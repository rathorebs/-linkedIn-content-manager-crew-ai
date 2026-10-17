import { useEffect, useState } from "react";
import type { Run, Stage } from "../types";
import { extractFinalPost, formatDuration, formatTokens } from "../utils";
import { FinalPost } from "./FinalPost";
import { Markdown } from "./Markdown";

const STAGE_INFO = [
  { agent: "Trend Researcher", working: "Searching the web for trends, hashtags and hooks" },
  { agent: "Content Writer", working: "Drafting the post from the research" },
  { agent: "Content Critic", working: "Scoring the draft and listing fixes" },
  { agent: "Post Optimizer", working: "Rewriting with the critic's feedback" },
  { agent: "Publishing Strategist", working: "Choosing the posting time and final format" },
];

/** Re-render every second while `active`, for live elapsed timers. */
function useNow(active: boolean) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!active) return;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [active]);
  return now;
}

export function RunView({ run }: { run: Run }) {
  const active = run.status === "queued" || run.status === "running";
  const now = useNow(active);
  const end = run.finished_at ? Date.parse(run.finished_at) : now;
  const elapsed = formatDuration(end - Date.parse(run.created_at));

  // Prefer the scheduler's copy-paste block; fall back to the optimizer's rewrite.
  const finalPost =
    run.status === "completed" ? extractFinalPost(run.result) ?? run.stages[3]?.output ?? null : null;

  return (
    <div className="run">
      <div className="card">
        <div className="run-head">
          <div>
            <p className="eyebrow">{statusLabel(run.status)}</p>
            <h2>{run.topic}</h2>
          </div>
          <div className="run-meta">
            <span>{elapsed}</span>
            <span className="muted">{run.model}</span>
          </div>
        </div>

        <ol className="stepper">
          {run.stages.map((stage, i) => (
            <StepItem key={stage.name} index={i} stage={stage} now={now} />
          ))}
        </ol>

        {run.notice && <div className="alert warning">{run.notice}</div>}
        {run.error && (
          <div className="alert error">
            <strong>{run.error.message}</strong>
            {run.error.hint && <div>{run.error.hint}</div>}
          </div>
        )}
      </div>

      {finalPost && <FinalPost post={finalPost} />}

      {run.status === "completed" && run.result && (
        <details className="card section" open>
          <summary>Publishing brief</summary>
          <Markdown>{run.result}</Markdown>
          {run.token_usage && (
            <p className="muted usage">
              {formatTokens(run.token_usage.total_tokens)} tokens · {run.token_usage.successful_requests} API
              requests
              {run.report_file && (
                <>
                  {" "}
                  · saved as <code>outputs/{run.report_file}</code>
                </>
              )}
            </p>
          )}
        </details>
      )}

      {run.stages.some((s) => s.output) && (
        <div className="card section">
          <h3>Stage outputs</h3>
          {run.stages.map((stage, i) =>
            stage.output ? (
              <details key={stage.name} className="stage-output">
                <summary>
                  {i + 1}. {stage.name} <span className="muted">· {STAGE_INFO[i]?.agent}</span>
                </summary>
                <Markdown>{stage.output}</Markdown>
              </details>
            ) : null,
          )}
        </div>
      )}
    </div>
  );
}

function StepItem({ index, stage, now }: { index: number; stage: Stage; now: number }) {
  const info = STAGE_INFO[index];
  let detail = "Waiting";
  if (stage.status === "running" && stage.started_at) {
    detail = `${info?.working ?? "Working"} · ${formatDuration(now - Date.parse(stage.started_at))}`;
  } else if (stage.status === "completed" && stage.started_at && stage.finished_at) {
    detail = `Done in ${formatDuration(Date.parse(stage.finished_at) - Date.parse(stage.started_at))}`;
  } else if (stage.status === "failed") {
    detail = "Failed";
  }

  return (
    <li className={`step ${stage.status}`}>
      <span className="step-dot" aria-hidden>
        {stage.status === "completed" ? "✓" : stage.status === "failed" ? "!" : index + 1}
      </span>
      <div>
        <div className="step-name">
          {stage.name} <span className="muted">· {info?.agent}</span>
        </div>
        <div className="step-detail">{detail}</div>
      </div>
    </li>
  );
}

function statusLabel(status: Run["status"]) {
  return { queued: "Starting", running: "In progress", completed: "Completed", failed: "Failed" }[status];
}
