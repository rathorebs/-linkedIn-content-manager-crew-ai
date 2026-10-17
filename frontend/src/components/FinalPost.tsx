import { useState } from "react";

const LINKEDIN_MAX_CHARS = 3000;
// LinkedIn shows roughly the first 3 lines (~210 chars) before "…see more".
const FOLD_LINES = 3;

async function copyText(text: string) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    // Clipboard API unavailable (e.g. non-secure context): fall back to execCommand.
    const el = document.createElement("textarea");
    el.value = text;
    document.body.appendChild(el);
    el.select();
    document.execCommand("copy");
    el.remove();
  }
}

export function FinalPost({ post }: { post: string }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const lines = post.split("\n");
  const foldable = lines.length > FOLD_LINES;
  const shown = expanded || !foldable ? post : lines.slice(0, FOLD_LINES).join("\n");
  const words = post.split(/\s+/).filter(Boolean).length;
  const overLimit = post.length > LINKEDIN_MAX_CHARS;

  async function handleCopy() {
    await copyText(post);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="card final-post">
      <div className="final-head">
        <div>
          <p className="eyebrow">Ready to publish</p>
          <h3>Final post</h3>
        </div>
        <button className="primary" onClick={handleCopy}>
          {copied ? "Copied ✓" : "Copy post"}
        </button>
      </div>

      <article className="li-preview">
        <header>
          <span className="avatar" aria-hidden>
            You
          </span>
          <div>
            <div className="li-name">Your Name</div>
            <div className="muted li-sub">Now · 🌐</div>
          </div>
        </header>
        <div className="li-body">
          {shown}
          {foldable && !expanded && (
            <button className="link" onClick={() => setExpanded(true)}>
              …see more
            </button>
          )}
        </div>
        {foldable && expanded && (
          <button className="link" onClick={() => setExpanded(false)}>
            Show less
          </button>
        )}
      </article>

      <p className={`muted counts ${overLimit ? "over" : ""}`}>
        {words} words · {post.length.toLocaleString()} / {LINKEDIN_MAX_CHARS.toLocaleString()} characters
        {!expanded && foldable && " · the preview shows what appears above “see more”"}
      </p>
    </div>
  );
}
