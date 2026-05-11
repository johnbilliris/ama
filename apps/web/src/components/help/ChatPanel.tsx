"use client";
/** spec-038 T-AA107 — Help ChatPanel: SSE consumer with refusal/deprecation/citation rendering. */
import { useRef, useState } from "react";
import { streamChatAsk, type ChatSseEvent } from "@/lib/help/sseClient";
import { CitationBadge } from "./CitationBadge";
import { RefusalCard } from "./RefusalCard";
import { RedactionNotice } from "./RedactionNotice";

interface Message {
  text: string;
  citations: { source_id: string; source_title: string; anchor: string }[];
  refusalReason?: string;
  redacted?: boolean;
}

export function ChatPanel({ persona }: { persona: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  async function send() {
    if (!input.trim() || busy) return;
    setBusy(true);
    const draft: Message = { text: "", citations: [] };
    setMessages((m) => [...m, draft]);
    abortRef.current = new AbortController();
    await streamChatAsk(
      { message: input, persona_id: persona },
      {
        onEvent: (e: ChatSseEvent) => {
          setMessages((m) => {
            const copy = [...m];
            const last = { ...copy[copy.length - 1] };
            if (e.kind === "meta") last.redacted = e.payload.redaction_notice;
            else if (e.kind === "delta") last.text += e.payload.text;
            else if (e.kind === "citation") last.citations = [...last.citations, e.payload];
            else if (e.kind === "refusal") last.refusalReason = e.payload.reason;
            copy[copy.length - 1] = last;
            return copy;
          });
        },
        onClose: () => setBusy(false),
        onError: () => setBusy(false),
      },
      { signal: abortRef.current.signal },
    );
    setInput("");
  }

  return (
    <section role="log" aria-live="polite" aria-label="Help chat" className="flex h-full flex-col">
      <ol className="flex-1 space-y-3 overflow-y-auto p-3">
        {messages.map((msg, i) => (
          <li key={i} className="rounded border p-2">
            {msg.redacted ? <RedactionNotice /> : null}
            {msg.refusalReason ? (
              <RefusalCard reason={msg.refusalReason} />
            ) : (
              <p>
                {msg.text}
                {msg.citations.map((c, j) => (
                  <CitationBadge key={j} index={j + 1} citation={c} />
                ))}
              </p>
            )}
          </li>
        ))}
      </ol>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
        className="flex gap-2 border-t p-2"
      >
        <input
          aria-label="Ask the help assistant"
          className="flex-1 rounded border px-2 py-1"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" disabled={busy}>{busy ? "…" : "Send"}</button>
      </form>
    </section>
  );
}
