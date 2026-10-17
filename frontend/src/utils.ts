/**
 * Pull the copy-paste-ready post out of the scheduler's publishing brief.
 * The brief puts it in the first fenced code block under a "Final Post"
 * heading; fall back to the first code block anywhere.
 */
export function extractFinalPost(markdown: string | null): string | null {
  if (!markdown) return null;
  const heading = markdown.search(/^#{1,6}[^\n]*final[^\n]*post/im);
  const searchFrom = heading >= 0 ? markdown.slice(heading) : markdown;
  const match = searchFrom.match(/```[^\n]*\n([\s\S]*?)```/) ?? markdown.match(/```[^\n]*\n([\s\S]*?)```/);
  return match ? match[1].trim() : null;
}

/** Return the body of one "## Stage: <name>" section from a saved report. */
export function reportSection(report: string, stage: string): string | null {
  const start = report.indexOf(`## Stage: ${stage}`);
  if (start < 0) return null;
  const rest = report.slice(start);
  const end = rest.indexOf("\n---\n");
  return end >= 0 ? rest.slice(0, end) : rest;
}

export function formatDuration(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return m > 0 ? `${m}m ${s.toString().padStart(2, "0")}s` : `${s}s`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function formatTokens(n: number): string {
  return n >= 1_000_000 ? `${(n / 1_000_000).toFixed(2)}M` : n >= 1000 ? `${(n / 1000).toFixed(1)}K` : `${n}`;
}
