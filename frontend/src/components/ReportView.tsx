import type { Report } from "../types";
import { extractFinalPost, reportSection } from "../utils";
import { FinalPost } from "./FinalPost";
import { Markdown } from "./Markdown";

export function ReportView({ report, onClose }: { report: Report; onClose: () => void }) {
  const title = report.content.split("\n", 1)[0].replace(/^# LinkedIn Content Report:\s*/, "");
  const finalPost =
    extractFinalPost(reportSection(report.content, "Scheduling")) ??
    reportSection(report.content, "Optimization");

  return (
    <div className="run">
      <div className="card report-head">
        <div>
          <p className="eyebrow">Saved report</p>
          <h2>{title}</h2>
          <p className="muted">
            <code>outputs/{report.name}</code>
          </p>
        </div>
        <button onClick={onClose}>← New post</button>
      </div>
      {finalPost && <FinalPost post={finalPost} />}
      <details className="card section">
        <summary>Full report (all 5 stages)</summary>
        <Markdown>{report.content}</Markdown>
      </details>
    </div>
  );
}
