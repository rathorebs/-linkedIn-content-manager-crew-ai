import type { ReportSummary } from "../types";
import { formatDate } from "../utils";

interface Props {
  reports: ReportSummary[];
  activeName: string | null;
  onOpen: (name: string) => void;
}

export function History({ reports, activeName, onOpen }: Props) {
  return (
    <div className="card history">
      <h3>Saved reports</h3>
      {reports.length === 0 ? (
        <p className="muted">Finished runs appear here.</p>
      ) : (
        <ul>
          {reports.map((r) => (
            <li key={r.name}>
              <button className={r.name === activeName ? "active" : ""} onClick={() => onOpen(r.name)}>
                <span className="history-topic">{r.topic}</span>
                <span className="muted">{formatDate(r.created_at)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
