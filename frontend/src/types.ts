// Shapes returned by the FastAPI backend (api.py).

export type RunStatus = "queued" | "running" | "completed" | "failed";
export type StageStatus = "pending" | "running" | "completed" | "failed";

export interface Stage {
  name: string;
  status: StageStatus;
  output: string | null;
  started_at: string | null;
  finished_at: string | null;
}

export interface TokenUsage {
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  cached_prompt_tokens?: number;
  successful_requests: number;
}

export interface Run {
  id: string;
  topic: string;
  model: string;
  status: RunStatus;
  created_at: string;
  finished_at: string | null;
  current_stage: number | null;
  stages: Stage[];
  notice: string | null;
  result: string | null;
  report_file: string | null;
  token_usage: TokenUsage | null;
  error: { message: string; hint: string | null } | null;
}

export interface RunSummary {
  id: string;
  topic: string;
  model: string;
  status: RunStatus;
  created_at: string;
  finished_at: string | null;
  report_file: string | null;
}

export interface Health {
  ok: boolean;
  model: string;
  missing_keys: string[];
  stages: string[];
}

export interface ReportSummary {
  name: string;
  topic: string;
  created_at: string;
}

export interface Report {
  name: string;
  content: string;
}
