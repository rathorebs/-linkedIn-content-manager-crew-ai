import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import type { Health, Report, ReportSummary, Run } from "./types";
import { TopicForm } from "./components/TopicForm";
import { RunView } from "./components/RunView";
import { ReportView } from "./components/ReportView";
import { History } from "./components/History";

const POLL_MS = 2000;

const isActive = (run: Run | null) => run?.status === "queued" || run?.status === "running";

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [run, setRun] = useState<Run | null>(null);
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  const refreshReports = useCallback(() => {
    api.listReports().then(setReports).catch(() => {});
  }, []);

  // Initial load: backend health, saved reports, and reattach to a run that is
  // still in progress (e.g. after a page refresh).
  useEffect(() => {
    api.health().then(setHealth).catch((e: Error) => setError(e.message));
    refreshReports();
    api
      .listRuns()
      .then((runs) => {
        const active = runs.find((r) => r.status === "queued" || r.status === "running");
        if (active) return api.getRun(active.id).then(setRun);
      })
      .catch(() => {});
  }, [refreshReports]);

  // Poll the active run until it finishes.
  const runId = run?.id;
  const active = isActive(run);
  useEffect(() => {
    if (!runId || !active) return;
    const timer = setInterval(async () => {
      try {
        const latest = await api.getRun(runId);
        setRun(latest);
        setError(null);
        if (latest.status === "completed") refreshReports();
      } catch (e) {
        setError((e as Error).message);
      }
    }, POLL_MS);
    return () => clearInterval(timer);
  }, [runId, active, refreshReports]);

  async function startRun(topic: string) {
    setStarting(true);
    setError(null);
    setReport(null);
    try {
      setRun(await api.startRun(topic));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setStarting(false);
    }
  }

  async function openReport(name: string) {
    try {
      setReport(await api.getReport(name));
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const missingKeys = health?.missing_keys ?? [];

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden>
            in
          </span>
          <div>
            <h1>LinkedIn Content Manager</h1>
            <p>Five AI agents: research, write, critique, optimize, schedule</p>
          </div>
        </div>
        {health && <span className="badge">{health.model}</span>}
      </header>

      {missingKeys.length > 0 && (
        <div className="alert warning">
          Missing API keys in <code>.env</code>: {missingKeys.join(", ")}. Add them and restart{" "}
          <code>python api.py</code>.
        </div>
      )}

      <main className="layout">
        <section className="main-col">
          {report ? (
            <ReportView report={report} onClose={() => setReport(null)} />
          ) : (
            <>
              <TopicForm
                disabled={active || starting || missingKeys.length > 0}
                busy={active || starting}
                onSubmit={startRun}
              />
              {error && <div className="alert error">{error}</div>}
              {run ? (
                <RunView run={run} />
              ) : (
                <div className="empty card">
                  <h2>How it works</h2>
                  <ol>
                    <li>Enter a topic or niche for your post.</li>
                    <li>The agents research trends, write a draft, critique it and rewrite it.</li>
                    <li>You get a copy-paste-ready post, a posting time and a first-hour engagement plan.</li>
                  </ol>
                  <p className="muted">A run usually takes 5–20 minutes depending on the model.</p>
                </div>
              )}
            </>
          )}
        </section>

        <aside className="side-col">
          <History reports={reports} activeName={report?.name ?? null} onOpen={openReport} />
        </aside>
      </main>
    </div>
  );
}
