import type { Health, Report, ReportSummary, Run, RunSummary } from "./types";

/** Fetch JSON from the backend, turning FastAPI error bodies into readable Errors. */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new Error("Can't reach the backend. Is `python api.py` running?");
  }
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // Non-JSON error body; keep the status text.
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>("/api/health"),
  startRun: (topic: string) =>
    request<Run>("/api/runs", { method: "POST", body: JSON.stringify({ topic }) }),
  listRuns: () => request<RunSummary[]>("/api/runs"),
  getRun: (id: string) => request<Run>(`/api/runs/${id}`),
  listReports: () => request<ReportSummary[]>("/api/reports"),
  getReport: (name: string) => request<Report>(`/api/reports/${encodeURIComponent(name)}`),
};
