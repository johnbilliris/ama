"use client";
/**
 * spec-038 T-AA107 — Help ChatPanel.
 *
 * Visual language mirrors `simulation-chat-pane.tsx`: header bar, scrollable
 * iMessage-style bubbles (operator right/blue, assistant left/grey), quick
 * actions row, multi-line textarea with Enter-to-send + Cancel/Send buttons.
 * Help-specific affordances (citations, refusal cards, redaction notices)
 * are layered into assistant bubbles instead of replacing them.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { streamChatAsk, type ChatSseEvent } from "@/lib/help/sseClient";
import { CitationBadge } from "./CitationBadge";
import { RefusalCard } from "./RefusalCard";
import { RedactionNotice } from "./RedactionNotice";

type Role = "user" | "assistant";

interface Citation {
  source_id: string;
  source_title: string;
  anchor: string;
  snippet?: string;
}

interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  citations?: Citation[];
  refusalReason?: string;
  redacted?: boolean;
}

const QUICK_ACTIONS = [
  { label: "🚦 Get started", prompt: "How do I get started with the AMA Hub for my persona?" },
  { label: "🗺 Map basics", prompt: "How do I read and filter the Disaster Map?" },
  { label: "📋 Audit", prompt: "How do I review the audit trail and constitutional gates?" },
  { label: "🛟 Offline", prompt: "What happens if I lose connectivity in the field?" },
  { label: "🔁 Simulation", prompt: "How do I run and replay a simulation exercise?" },
];

export function ChatPanel({ persona }: { persona: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll on new content, mirroring sim chat behaviour.
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, isStreaming]);

  const send = useCallback(async () => {
    if (!input.trim() || isStreaming) return;
    const prompt = input.trim();
    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", content: prompt };
    const assistantId = crypto.randomUUID();
    setMessages((prev) => [
      ...prev,
      userMsg,
      { id: assistantId, role: "assistant", content: "", citations: [] },
    ]);
    setInput("");
    setStreaming(true);
    setError(null);

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      await streamChatAsk(
        { message: prompt, persona_id: persona },
        {
          onEvent: (e: ChatSseEvent) => {
            setMessages((prev) =>
              prev.map((m) => {
                if (m.id !== assistantId) return m;
                if (e.kind === "meta") return { ...m, redacted: e.payload.redaction_notice };
                if (e.kind === "delta") return { ...m, content: m.content + e.payload.text };
                if (e.kind === "citation")
                  return { ...m, citations: [...(m.citations ?? []), e.payload] };
                if (e.kind === "refusal") return { ...m, refusalReason: e.payload.reason };
                return m;
              }),
            );
          },
          onClose: () => setStreaming(false),
          onError: (err) => {
            setError(err.message);
            setStreaming(false);
          },
        },
        { signal: ctrl.signal },
      );
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  }, [input, isStreaming, persona]);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const injectQuickAction = useCallback((prompt: string) => {
    setInput(prompt);
  }, []);

  return (
    <div
      role="log"
      aria-live="polite"
      aria-label="Help chat"
      className="grid h-full min-h-0 overflow-hidden rounded border"
      style={{ gridTemplateRows: "auto minmax(0, 1fr) auto auto" }}
    >
      <header className="sim-chat-header border-b bg-blue-50 px-3 py-2 text-xs font-medium text-blue-900">
        <span>HELP ASSISTANT · Grounded in approved Hub documentation</span>
      </header>

      <div ref={scrollRef} className="min-h-0 space-y-3 overflow-y-auto p-3 text-sm">
        {messages.length === 0 && (
          <p className="text-gray-500">
            Ask anything about using the Hub. Example:{" "}
            <em>&ldquo;How do I escalate a cross-border bushfire to NEMA?&rdquo;</em>
          </p>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        {error && (
          <p role="alert" className="rounded bg-red-50 px-2 py-1 text-xs text-red-700">
            {error}
          </p>
        )}
      </div>

      <div className="sim-quick-actions border-t">
        {QUICK_ACTIONS.map((qa) => (
          <button
            key={qa.label}
            type="button"
            className="sim-quick-btn"
            onClick={() => injectQuickAction(qa.prompt)}
            disabled={isStreaming}
            title={qa.prompt}
          >
            {qa.label}
          </button>
        ))}
      </div>

      <footer className="flex gap-2 border-t bg-white p-2">
        <textarea
          aria-label="Ask the help assistant"
          className="flex-1 resize-none rounded border px-2 py-1 text-sm"
          rows={2}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void send();
            }
          }}
          placeholder="Ask the help assistant…"
          disabled={isStreaming}
        />
        {isStreaming ? (
          <button
            type="button"
            onClick={cancel}
            className="rounded bg-red-600 px-3 py-1 text-sm font-medium text-white"
          >
            Cancel
          </button>
        ) : (
          <button
            type="button"
            onClick={() => void send()}
            disabled={!input.trim()}
            className="rounded bg-blue-600 px-3 py-1 text-sm font-medium text-white disabled:opacity-40"
          >
            Send
          </button>
        )}
      </footer>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const alignClass = isUser ? "text-right" : "text-left";
  const alignStyle: React.CSSProperties = { textAlign: isUser ? "right" : "left" };
  const bubbleClass =
    "inline-block max-w-[85%] rounded-lg px-3 py-2 text-left " +
    (isUser
      ? "whitespace-pre-wrap bg-blue-600 text-white"
      : message.refusalReason
        ? "bg-amber-100 text-amber-900"
        : "sim-chat-markdown bg-gray-100 text-gray-900");

  return (
    <div className={alignClass} style={alignStyle}>
      <div className={bubbleClass} style={{ textAlign: "left" }}>
        {message.redacted ? <RedactionNotice /> : null}
        {message.refusalReason ? (
          <RefusalCard reason={message.refusalReason} />
        ) : message.content ? (
          <p className="whitespace-pre-wrap">
            {message.content}
            {(message.citations ?? []).map((c, j) => (
              <CitationBadge key={`${c.source_id}-${j}`} index={j + 1} citation={c} />
            ))}
          </p>
        ) : (
          <span className="text-gray-400">…</span>
        )}
      </div>
    </div>
  );
}
