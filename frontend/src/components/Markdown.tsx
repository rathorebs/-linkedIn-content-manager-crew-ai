import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/** Renders agent output (GitHub-flavoured markdown, incl. tables). */
export function Markdown({ children }: { children: string }) {
  return (
    <div className="markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  );
}
