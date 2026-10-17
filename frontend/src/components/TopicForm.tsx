import { useState, type FormEvent } from "react";

const EXAMPLES = [
  "AI agents for B2B sales",
  "Building a personal brand as a software engineer",
  "Remote team leadership",
  "Sustainable supply chains",
];

interface Props {
  disabled: boolean;
  busy: boolean;
  onSubmit: (topic: string) => void;
}

export function TopicForm({ disabled, busy, onSubmit }: Props) {
  const [topic, setTopic] = useState("");
  const trimmed = topic.trim();
  const valid = trimmed.length >= 3 && trimmed.length <= 200;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (valid && !disabled) onSubmit(trimmed);
  }

  return (
    <form className="card topic-form" onSubmit={handleSubmit}>
      <label htmlFor="topic">Topic or niche</label>
      <div className="topic-row">
        <input
          id="topic"
          type="text"
          value={topic}
          maxLength={200}
          placeholder='e.g. "AI agents for B2B sales"'
          onChange={(e) => setTopic(e.target.value)}
          disabled={disabled}
          autoComplete="off"
        />
        <button type="submit" className="primary" disabled={disabled || !valid}>
          {busy ? "Running…" : "Generate post"}
        </button>
      </div>
      <div className="examples">
        <span className="muted">Try:</span>
        {EXAMPLES.map((ex) => (
          <button type="button" key={ex} className="chip" disabled={disabled} onClick={() => setTopic(ex)}>
            {ex}
          </button>
        ))}
      </div>
    </form>
  );
}
