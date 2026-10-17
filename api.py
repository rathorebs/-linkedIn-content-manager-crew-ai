#!/usr/bin/env python3
"""
Web API for the Autonomous LinkedIn Content Manager
===================================================

Wraps the CrewAI pipeline in linkedin_content_manager.py with a small REST API
for the React frontend in ./frontend.

Endpoints:
    GET  /api/health              - model in use and any missing API keys
    POST /api/runs                - start a run: {"topic": "..."} (one at a time)
    GET  /api/runs                - runs since the server started, newest first
    GET  /api/runs/{run_id}       - live status of one run, incl. stage outputs
    GET  /api/reports             - saved reports in ./outputs, newest first
    GET  /api/reports/{name}      - markdown content of one saved report

Usage:
    python api.py                 # serves on http://127.0.0.1:8000

If ./frontend/dist exists (after `npm run build`), the built frontend is served
at / as well, so a single process runs the whole app.
"""

from __future__ import annotations

import os
import threading
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import linkedin_content_manager as pipeline

FRONTEND_DIST = Path(__file__).resolve().parent / "frontend" / "dist"

app = FastAPI(title="LinkedIn Content Manager API")


# ---------------------------------------------------------------------------
# Run state
# ---------------------------------------------------------------------------
# Runs live in memory; finished runs are also persisted as reports in ./outputs
# by pipeline.save_report. A single lock guards all run state because the crew
# executes in a worker thread while request handlers read it.
_lock = threading.Lock()
_runs: dict[str, dict[str, Any]] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_stages() -> list[dict[str, Any]]:
    return [
        {"name": name, "status": "pending", "output": None, "started_at": None, "finished_at": None}
        for name in pipeline.STAGES
    ]


def _active_run() -> dict[str, Any] | None:
    return next((r for r in _runs.values() if r["status"] in ("queued", "running")), None)


def _make_listener(run_id: str):
    """Build a progress listener that records pipeline events on one run."""

    def listener(event: str, **data: Any) -> None:
        with _lock:
            run = _runs[run_id]
            if event == "stage_started":
                stage = run["stages"][data["stage"]]
                stage.update(status="running", started_at=_now())
                run["current_stage"] = data["stage"]
                run["notice"] = None
            elif event == "stage_completed":
                stage = run["stages"][data["stage"]]
                stage.update(status="completed", output=data["output"], finished_at=_now())
            elif event == "retrying":
                # The crew restarts from scratch on retry, so reset stage progress.
                run["stages"] = _new_stages()
                run["current_stage"] = None
                run["notice"] = (
                    f"Temporary API error. Retrying in {data['wait_seconds']}s "
                    f"(attempt {data['attempt']})..."
                )

    return listener


def _execute(run_id: str, topic: str) -> None:
    """Worker thread: run the crew and record the outcome."""
    listener = _make_listener(run_id)
    pipeline.add_progress_listener(listener)
    with _lock:
        _runs[run_id]["status"] = "running"
    try:
        result = pipeline.run_crew(topic)
        try:
            report_file = pipeline.save_report(topic, result).name
        except OSError as exc:
            print(f"[WARN] Could not save report: {exc}")
            report_file = None
        usage = result.token_usage.model_dump() if result.token_usage else None
        with _lock:
            _runs[run_id].update(
                status="completed",
                result=result.raw,
                report_file=report_file,
                token_usage=usage,
                finished_at=_now(),
                current_stage=None,
            )
    except pipeline.PipelineError as exc:
        _fail_run(run_id, exc.message, exc.hint)
    except Exception as exc:  # noqa: BLE001 - surface anything else to the UI
        traceback.print_exc()
        _fail_run(run_id, f"Unexpected error: {type(exc).__name__}: {exc}", None)
    finally:
        pipeline.remove_progress_listener(listener)


def _fail_run(run_id: str, message: str, hint: str | None) -> None:
    with _lock:
        run = _runs[run_id]
        for stage in run["stages"]:
            if stage["status"] == "running":
                stage["status"] = "failed"
        run.update(status="failed", error={"message": message, "hint": hint}, finished_at=_now())


def _summary(run: dict[str, Any]) -> dict[str, Any]:
    keys = ("id", "topic", "model", "status", "created_at", "finished_at", "report_file")
    return {k: run[k] for k in keys}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
class RunRequest(BaseModel):
    topic: str


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "model": os.getenv("CLAUDE_MODEL", pipeline.DEFAULT_MODEL),
        "missing_keys": pipeline.missing_env_vars(),
        "stages": pipeline.STAGES,
    }


@app.post("/api/runs", status_code=201)
def create_run(req: RunRequest) -> dict[str, Any]:
    missing = pipeline.missing_env_vars()
    if missing:
        raise HTTPException(400, f"Missing API keys in .env: {', '.join(missing)}")
    try:
        topic = pipeline.validate_topic(req.topic)
    except pipeline.PipelineError as exc:
        raise HTTPException(422, exc.message) from exc

    with _lock:
        # One run at a time: runs are long, cost real money, and share crew memory.
        active = _active_run()
        if active:
            raise HTTPException(409, f'A run is already in progress: "{active["topic"]}"')
        run_id = uuid.uuid4().hex[:12]
        run = {
            "id": run_id,
            "topic": topic,
            "model": os.getenv("CLAUDE_MODEL", pipeline.DEFAULT_MODEL),
            "status": "queued",
            "created_at": _now(),
            "finished_at": None,
            "current_stage": None,
            "stages": _new_stages(),
            "notice": None,
            "result": None,
            "report_file": None,
            "token_usage": None,
            "error": None,
        }
        _runs[run_id] = run

    threading.Thread(target=_execute, args=(run_id, topic), daemon=True, name=f"run-{run_id}").start()
    with _lock:
        return dict(_runs[run_id])


@app.get("/api/runs")
def list_runs() -> list[dict[str, Any]]:
    with _lock:
        return [_summary(r) for r in sorted(_runs.values(), key=lambda r: r["created_at"], reverse=True)]


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    with _lock:
        run = _runs.get(run_id)
        if not run:
            raise HTTPException(404, "Run not found")
        return {**run, "stages": [dict(s) for s in run["stages"]]}


@app.get("/api/reports")
def list_reports() -> list[dict[str, Any]]:
    if not pipeline.OUTPUT_DIR.exists():
        return []
    reports = []
    for path in sorted(pipeline.OUTPUT_DIR.glob("*.md"), reverse=True):
        with path.open(encoding="utf-8") as fh:
            first_line = fh.readline().strip()
        topic = first_line.removeprefix("# LinkedIn Content Report:").strip() or path.stem
        reports.append(
            {
                "name": path.name,
                "topic": topic,
                "created_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            }
        )
    return reports


@app.get("/api/reports/{name}")
def get_report(name: str) -> dict[str, str]:
    path = (pipeline.OUTPUT_DIR / name).resolve()
    # Only plain .md files directly inside ./outputs (blocks path traversal).
    if path.parent != pipeline.OUTPUT_DIR.resolve() or path.suffix != ".md" or not path.is_file():
        raise HTTPException(404, "Report not found")
    return {"name": path.name, "content": path.read_text(encoding="utf-8")}


# Serve the built frontend last so /api routes take precedence.
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    # No auto-reload: a reload would kill an in-progress run's worker thread.
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("PORT", "8000")))
