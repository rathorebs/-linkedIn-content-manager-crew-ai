#!/usr/bin/env python3
"""
Autonomous LinkedIn Content Manager
===================================

A five-agent CrewAI pipeline that turns a topic/niche into a publish-ready
LinkedIn post with a scheduling brief:

    Research  ->  Writing  ->  Critique  ->  Optimization  ->  Scheduling

Usage:
    python linkedin_content_manager.py                     # prompts for a topic
    python linkedin_content_manager.py "AI in healthcare"  # topic as argument

Required environment variables (loaded from .env):
    ANTHROPIC_API_KEY - Anthropic (Claude) key used by every agent
    SERPER_API_KEY    - Serper.dev key used by the researcher's web-search tool

Optional:
    CLAUDE_MODEL      - defaults to "claude-opus-5-5" (e.g. "claude-sonnet-5-5", "claude-haiku-5-5")
    MAX_RETRIES       - retries for transient API failures, defaults to 2

Crew memory embeddings run locally (ONNX MiniLM, downloaded on first run), so
no OpenAI key is needed. Anthropic does not offer an embeddings API.
"""

from __future__ import annotations

import os
import re
import sys
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Environment loading
# ---------------------------------------------------------------------------
# Load .env before importing CrewAI so the library sees the keys at import time.
from dotenv import load_dotenv

load_dotenv()

REQUIRED_ENV_VARS = {
    "ANTHROPIC_API_KEY": "https://console.anthropic.com/settings/keys",
    "SERPER_API_KEY": "https://serper.dev (free tier available)",
}

DEFAULT_MODEL = "claude-opus-5-5"
MAX_OUTPUT_TOKENS = 16000
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"

# Stage names, in pipeline order. Used for console separators and the report.
STAGES = ["Research", "Writing", "Critique", "Optimization", "Scheduling"]

SEPARATOR = "=" * 80
SUB_SEPARATOR = "-" * 80


# ---------------------------------------------------------------------------
# Console helpers
# ---------------------------------------------------------------------------
def banner(title: str, char: str = "=") -> None:
    """Print a full-width section banner."""
    line = char * 80
    print(f"\n{line}\n{title.center(80)}\n{line}\n", flush=True)


class PipelineError(Exception):
    """A pipeline failure with a user-facing message and an optional fix hint."""

    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


def fail(message: str, hint: str | None = None, code: int = 1) -> None:
    """Print an error (and optional hint) to stderr and exit."""
    print(f"\n[ERROR] {message}", file=sys.stderr)
    if hint:
        print(f"        {hint}", file=sys.stderr)
    sys.exit(code)


# ---------------------------------------------------------------------------
# Pre-flight validation
# ---------------------------------------------------------------------------
def missing_env_vars() -> list[str]:
    """Return the required API keys that are unset or still placeholders."""
    return [
        name
        for name in REQUIRED_ENV_VARS
        if not os.getenv(name) or os.getenv(name, "").startswith("your_")
    ]


def validate_topic(topic: str) -> str:
    """Return the stripped topic, or raise PipelineError if it is unusable."""
    topic = topic.strip()
    if len(topic) < 3:
        raise PipelineError("Topic must be at least 3 characters long.", 'Example: "AI agents for B2B sales"')
    if len(topic) > 200:
        raise PipelineError("Topic is too long (max 200 characters). Keep it to a focused niche.")
    return topic


def validate_environment() -> None:
    """Fail fast with a clear message if any required API key is missing."""
    missing = missing_env_vars()
    if missing:
        details = "\n".join(f"  - {name}: get one at {REQUIRED_ENV_VARS[name]}" for name in missing)
        fail(
            f"Missing required environment variable(s): {', '.join(missing)}",
            f"Copy .env.example to .env and fill in:\n{details}",
        )


def get_topic() -> str:
    """Read the topic from argv, or prompt for it interactively."""
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:]).strip()
    else:
        try:
            topic = input("Enter the topic/niche for your LinkedIn post: ").strip()
        except (EOFError, KeyboardInterrupt):
            fail("No topic provided.")

    try:
        return validate_topic(topic)
    except PipelineError as exc:
        fail(exc.message, exc.hint)


# ---------------------------------------------------------------------------
# Imports that depend on installed packages
# ---------------------------------------------------------------------------
# Imported after validation helpers are defined so an install problem produces
# a readable error instead of a bare traceback.
try:
    from crewai import LLM, Agent, Crew, Process, Task
    from crewai.tasks.task_output import TaskOutput
    from crewai_tools import ScrapeWebsiteTool, SerperDevTool
except ImportError as exc:  # pragma: no cover - environment problem
    fail(
        f"Required package not installed: {exc.name or exc}",
        "Run: pip install -r requirements.txt  (Python 3.10-3.13)",
    )


# ---------------------------------------------------------------------------
# LLM configuration
# ---------------------------------------------------------------------------
def build_llm() -> LLM:
    """
    Return the Claude LLM shared by all agents.

    No temperature is set: current Claude models (Opus 5.5, Sonnet 5.5) reject
    sampling parameters, and adaptive thinking is on by default. max_tokens is
    capped explicitly because CrewAI otherwise requests the model maximum
    (128K), which the Anthropic SDK refuses for non-streaming calls.
    """
    model = os.getenv("CLAUDE_MODEL", DEFAULT_MODEL)
    return LLM(
        model=f"anthropic/{model}",
        max_tokens=MAX_OUTPUT_TOKENS,
        timeout=300,
        max_retries=2,
    )


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------
def build_agents(llm: LLM) -> dict[str, Agent]:
    """Create the five specialised agents."""

    # 1. Trend Researcher - the only agent with tools (web search + scraping).
    researcher = Agent(
        role="LinkedIn Trend Researcher",
        goal="Research latest trending topics, hashtags, and content themes for a given niche",
        backstory=(
            "You are an expert social media researcher who monitors LinkedIn trends, "
            "viral posts, and industry news every day. You know exactly what drives "
            "engagement on LinkedIn: which topics spark debate, which formats get saved "
            "and shared, and which hashtags actually have reach. You always ground your "
            "findings in current, verifiable sources."
        ),
        tools=[SerperDevTool(), ScrapeWebsiteTool()],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )

    # 2. Content Writer - LLM only.
    writer = Agent(
        role="LinkedIn Content Writer",
        goal="Write engaging, high-quality LinkedIn posts based on research provided",
        backstory=(
            "You are a seasoned LinkedIn ghostwriter for industry leaders and founders. "
            "You understand the LinkedIn algorithm deeply: dwell time, the 'see more' "
            "fold, comment velocity. You are a master of hook writing, storytelling, "
            "and natural CTA placement, and you write in a conversational yet "
            "professional tone that sounds human, never corporate."
        ),
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # 3. Content Critic - LLM only.
    critic = Agent(
        role="Content Quality Critic",
        goal=(
            "Review LinkedIn posts and provide detailed constructive feedback on engagement "
            "potential, tone, structure, clarity, hook strength, and CTA effectiveness"
        ),
        backstory=(
            "You are a harsh but fair editor who has reviewed thousands of LinkedIn posts. "
            "You can instantly tell the difference between a post that gets 10 likes and "
            "one that earns 10k+ impressions. You never give vague praise; every piece of "
            "feedback you deliver is specific, actionable, and tied to engagement outcomes."
        ),
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # 4. Content Optimizer - LLM only.
    optimizer = Agent(
        role="LinkedIn Post Optimizer",
        goal="Rewrite posts incorporating critic feedback to maximize LinkedIn engagement",
        backstory=(
            "You are a LinkedIn growth expert and conversion copywriter. You are a master "
            "of LinkedIn formatting: short punchy lines, strategic white space, tasteful "
            "emoji usage, hashtag optimization, proven hook patterns, and mobile-first "
            "readability. You take good drafts and make them impossible to scroll past."
        ),
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # 5. Scheduling / Publishing Strategist - LLM only.
    scheduler = Agent(
        role="LinkedIn Publishing Strategist",
        goal=(
            "Determine optimal posting time, finalize formatting with hashtags, and create "
            "publishing-ready output with scheduling recommendations"
        ),
        backstory=(
            "You are a LinkedIn analytics expert who has studied posting performance across "
            "industries for years. You understand optimal posting times by industry, "
            "audience timezone, and day of week, and you know exactly what a creator should "
            "do in the critical first hour after publishing to maximize reach."
        ),
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    return {
        "researcher": researcher,
        "writer": writer,
        "critic": critic,
        "optimizer": optimizer,
        "scheduler": scheduler,
    }


# ---------------------------------------------------------------------------
# Stage-completion callback
# ---------------------------------------------------------------------------
# Progress listeners let other front ends (e.g. the web API) follow a run.
# Each listener is called as listener(event, **data) with event one of
# "stage_started" (stage), "stage_completed" (stage, output) or
# "retrying" (attempt, wait_seconds, error).
_progress_listeners: list[Callable[..., None]] = []


def add_progress_listener(listener: Callable[..., None]) -> None:
    _progress_listeners.append(listener)


def remove_progress_listener(listener: Callable[..., None]) -> None:
    if listener in _progress_listeners:
        _progress_listeners.remove(listener)


def _emit(event: str, **data: Any) -> None:
    for listener in list(_progress_listeners):
        try:
            listener(event, **data)
        except Exception as exc:  # noqa: BLE001 - a broken listener must not kill the run
            print(f"[WARN] Progress listener failed: {exc}", file=sys.stderr)


# Maps each agent role to its pipeline stage index. The callback must be a
# module-level function (not a closure) so CrewAI can serialize it for checkpointing.
ROLE_TO_STAGE = {
    "LinkedIn Trend Researcher": 0,
    "LinkedIn Content Writer": 1,
    "Content Quality Critic": 2,
    "LinkedIn Post Optimizer": 3,
    "LinkedIn Publishing Strategist": 4,
}


def on_stage_complete(output: TaskOutput) -> None:
    """Task callback: print a separator when a stage finishes and announce the next one."""
    stage_index = ROLE_TO_STAGE.get(output.agent.strip())
    if stage_index is None:
        return
    banner(f"STAGE {stage_index + 1}/{len(STAGES)} COMPLETE: {STAGES[stage_index].upper()}")
    _emit("stage_completed", stage=stage_index, output=output.raw)
    if stage_index + 1 < len(STAGES):
        nxt = STAGES[stage_index + 1]
        banner(f"STAGE {stage_index + 2}/{len(STAGES)}: {nxt.upper()}", char="-")
        _emit("stage_started", stage=stage_index + 1)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------
def build_tasks(agents: dict[str, Agent]) -> list[Task]:
    """
    Create the five sequential tasks. `{topic}` placeholders are interpolated
    by CrewAI from the inputs passed to `crew.kickoff()`.

    In a sequential process each task automatically receives the previous
    task's output; `context=` is set explicitly where a task needs output from
    more than just the immediately preceding step.
    """

    research_task = Task(
        description=(
            "Research the latest trends, viral content patterns, and hot topics on LinkedIn "
            "for the niche: {topic}.\n\n"
            "Use web search to find recent (last 30-90 days) news, discussions, and "
            "high-performing LinkedIn content in this niche. Scrape a few of the most "
            "relevant pages if snippets are not enough.\n\n"
            "Identify 3-5 trending angles, relevant hashtags, and content hooks currently "
            "performing well. Note the target audience (roles, industries, likely timezones)."
        ),
        expected_output=(
            "A structured research brief in markdown with these sections:\n"
            "1. Trending Topics (3-5, each with a one-line why-it-matters and a source)\n"
            "2. Suggested Angles (3-5 distinct post angles)\n"
            "3. Top-Performing Hashtags (8-12, mix of broad and niche)\n"
            "4. Content Hook Ideas (5 opening lines)\n"
            "5. Target Audience Profile (roles, industries, primary regions/timezones)"
        ),
        agent=agents["researcher"],
        callback=on_stage_complete,
    )

    writing_task = Task(
        description=(
            "Using the research brief, write a compelling LinkedIn post about {topic}.\n\n"
            "Requirements:\n"
            "- A strong hook in the first 2 lines (this is what shows above 'see more')\n"
            "- A storytelling or value-driven body\n"
            "- A clear call-to-action that invites comments\n"
            "- 150-300 words\n"
            "- Use the trending angles and hooks from the research"
        ),
        expected_output=(
            "A complete LinkedIn post draft with a hook, body, and CTA, followed by a "
            "line of suggested hashtags and a word count."
        ),
        agent=agents["writer"],
        context=[research_task],
        callback=on_stage_complete,
    )

    critique_task = Task(
        description=(
            "Critically review the LinkedIn post draft about {topic}.\n\n"
            "Evaluate each of the following and score it out of 10:\n"
            "- Hook strength (will people click 'see more'?)\n"
            "- Storytelling quality\n"
            "- Engagement potential\n"
            "- CTA effectiveness\n"
            "- Tone consistency\n"
            "- LinkedIn formatting\n"
            "- Viral potential\n\n"
            "Give an overall score out of 10 and specific, actionable improvement "
            "suggestions (quote the exact lines that should change)."
        ),
        expected_output=(
            "A detailed critique in markdown containing: a score table (each criterion /10 "
            "plus overall /10), strengths, weaknesses, and a numbered list of specific "
            "actionable improvements."
        ),
        agent=agents["critic"],
        context=[writing_task],
        callback=on_stage_complete,
    )

    optimization_task = Task(
        description=(
            "Take the original LinkedIn post and the critic's feedback. Rewrite the post "
            "about {topic} incorporating ALL of the feedback.\n\n"
            "- Improve the hook\n"
            "- Tighten the copy (keep it 150-300 words)\n"
            "- Optimize formatting: short lines, line breaks, strategic emoji (not excessive)\n"
            "- Strengthen the CTA\n"
            "- Optimize hashtags (3-5 at the end)\n\n"
            "Produce the final publish-ready version."
        ),
        expected_output=(
            "The final, polished, publish-ready LinkedIn post with optimized formatting, "
            "hashtags, and CTA, followed by a short bullet list of what changed and why."
        ),
        agent=agents["optimizer"],
        context=[writing_task, critique_task],
        callback=on_stage_complete,
    )

    scheduling_task = Task(
        description=(
            "Analyze the final post content and the target audience for {topic}.\n\n"
            "- Recommend the best day and time to publish, with timezone, plus a backup slot\n"
            "- Provide the final formatted post ready for LinkedIn copy-paste "
            "(plain text, no markdown syntax such as ** or #headers)\n"
            "- Include a hashtag strategy brief\n"
            "- Include first-hour engagement tips"
        ),
        expected_output=(
            "A complete publishing brief in markdown with these sections:\n"
            "1. Recommended Posting Time (day, time, timezone, rationale, backup slot)\n"
            "2. Final Post (inside a fenced code block, ready for copy-paste)\n"
            "3. Hashtag Strategy (list of hashtags with the role of each)\n"
            "4. First-Hour Engagement Strategy (5-7 concrete actions)"
        ),
        agent=agents["scheduler"],
        context=[research_task, optimization_task],
        callback=on_stage_complete,
    )

    return [research_task, writing_task, critique_task, optimization_task, scheduling_task]


# ---------------------------------------------------------------------------
# Crew
# ---------------------------------------------------------------------------
def build_crew() -> Crew:
    """Assemble agents and tasks into a sequential, verbose, memory-enabled crew."""
    agents = build_agents(build_llm())
    tasks = build_tasks(agents)

    return Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,  # research -> write -> critique -> optimize -> schedule
        verbose=True,
        memory=True,  # unified crew memory; analysis runs on the agents' Claude LLM
        # Anthropic has no embeddings API, so embed memories locally with ONNX
        # (all-MiniLM-L6-v2, ~80 MB download on first run, no API key needed).
        embedder={"provider": "onnx"},
    )


# ---------------------------------------------------------------------------
# Error classification and retry
# ---------------------------------------------------------------------------
# CrewAI calls Claude through the Anthropic SDK; matching on exception class
# name (rather than importing the classes) keeps this robust across versions.
FATAL_ERRORS = {
    "AuthenticationError": (
        "Authentication failed.",
        "Check ANTHROPIC_API_KEY / SERPER_API_KEY in your .env file.",
    ),
    "PermissionDeniedError": (
        "Permission denied by the API.",
        "Your key may not have access to this model. Try CLAUDE_MODEL=claude-sonnet-5-5.",
    ),
    "NotFoundError": (
        "Model not found.",
        "Check CLAUDE_MODEL in your .env file.",
    ),
    "BadRequestError": (
        "The API rejected the request.",
        "This is usually a model/parameter mismatch. See the details above.",
    ),
}
TRANSIENT_ERRORS = {
    "RateLimitError",
    "APIConnectionError",
    "APITimeoutError",
    "Timeout",
    "InternalServerError",
    "OverloadedError",
    "ServiceUnavailableError",
    "ConnectionError",
}


def classify_error(exc: BaseException) -> str:
    """Return 'fatal', 'transient' or 'unknown' by walking the exception chain."""
    current: BaseException | None = exc
    while current is not None:
        name = type(current).__name__
        if name in FATAL_ERRORS:
            return "fatal"
        if name in TRANSIENT_ERRORS:
            return "transient"
        text = str(current).lower()
        if "credit balance is too low" in text:
            return "fatal"
        if "rate limit" in text or "timed out" in text:
            return "transient"
        current = current.__cause__ or current.__context__
    return "unknown"


def fatal_message(exc: BaseException) -> tuple[str, str]:
    """Find a user-friendly message for a fatal error."""
    current: BaseException | None = exc
    while current is not None:
        if type(current).__name__ in FATAL_ERRORS:
            return FATAL_ERRORS[type(current).__name__]
        if "credit balance is too low" in str(current).lower():
            return (
                "Anthropic credit balance is too low.",
                "Add credit at https://console.anthropic.com/settings/billing.",
            )
        current = current.__cause__ or current.__context__
    return ("Unrecoverable API error.", "See the details above.")


def run_crew(topic: str):
    """
    Run the crew, retrying transient failures with exponential backoff.

    Raises PipelineError on failure (KeyboardInterrupt propagates unchanged).
    """
    max_retries = int(os.getenv("MAX_RETRIES", "2"))

    for attempt in range(max_retries + 1):
        try:
            crew = build_crew()  # fresh crew per attempt so no half-finished state leaks
            banner(f"STAGE 1/{len(STAGES)}: {STAGES[0].upper()}", char="-")
            _emit("stage_started", stage=0)
            return crew.kickoff(inputs={"topic": topic})
        except KeyboardInterrupt:
            raise
        except Exception as exc:  # noqa: BLE001 - classified below
            kind = classify_error(exc)
            print(f"\n[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)

            if kind == "fatal":
                raise PipelineError(*fatal_message(exc)) from exc

            if attempt < max_retries and kind == "transient":
                wait = 10 * (2**attempt)
                print(
                    f"[RETRY] Transient API error. Retrying in {wait}s "
                    f"(attempt {attempt + 2}/{max_retries + 1})...",
                    file=sys.stderr,
                )
                _emit("retrying", attempt=attempt + 2, wait_seconds=wait, error=str(exc))
                time.sleep(wait)
                continue

            raise PipelineError(
                "The crew failed to complete.",
                "If this persists, check your network connection and API status pages.",
            ) from exc
    raise PipelineError("The crew failed to complete.")  # unreachable


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def save_report(topic: str, result) -> Path:
    """Write every stage's output plus the final brief to outputs/<timestamp>_<slug>.md."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:50] or "post"
    path = OUTPUT_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{slug}.md"

    parts = [f"# LinkedIn Content Report: {topic}", f"_Generated {datetime.now():%Y-%m-%d %H:%M}_\n"]
    for stage, task_output in zip(STAGES, result.tasks_output):
        parts.append(f"\n---\n\n## Stage: {stage}\n\n{task_output.raw}\n")

    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def main() -> None:
    banner("AUTONOMOUS LINKEDIN CONTENT MANAGER")
    validate_environment()
    topic = get_topic()

    print(f"Topic:    {topic}")
    print(f"Model:    {os.getenv('CLAUDE_MODEL', DEFAULT_MODEL)}")
    print(f"Pipeline: {' -> '.join(STAGES)}")

    try:
        result = run_crew(topic)
    except KeyboardInterrupt:
        fail("Interrupted by user.", code=130)
    except PipelineError as exc:
        fail(exc.message, exc.hint)

    banner("FINAL PUBLISHING BRIEF")
    print(result.raw)

    try:
        report = save_report(topic, result)
        print(f"\n{SUB_SEPARATOR}\nFull report (all 5 stages) saved to: {report}\n{SUB_SEPARATOR}")
    except OSError as exc:
        print(f"\n[WARN] Could not save report: {exc}", file=sys.stderr)

    if result.token_usage:
        print(f"Token usage: {result.token_usage}")


if __name__ == "__main__":
    main()
