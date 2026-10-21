"use client";
/**
 * spec-038 T-AA107 — Help ChatPanel.
 *
 * View component for the grounded help assistant. State (messages, input,
 * in-flight stream) is owned by `HelpChatProvider` so multiple ChatPanel
 * mount points (help layout right rail, /help/chat page, global dock)
 * share one conversation that survives cross-route navigation.
 */
import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { useHelpChat, type HelpChatMessage } from "@/lib/help/chatStore";

import { CitationBadge } from "./CitationBadge";
import { RedactionNotice } from "./RedactionNotice";
import { RefusalCard } from "./RefusalCard";

const QUICK_ACTIONS = [
  { label: "🚦 Get started", prompt: "How do I get started with the AMA Hub for my persona?" },
  { label: "🗺 Map basics", prompt: "How do I read and filter the Disaster Map?" },
  { label: "📋 Audit", prompt: "How do I review the audit trail and constitutional gates?" },
  { label: "🛟 Offline", prompt: "What happens if I lose connectivity in the field?" },
  { label: "🔁 Simulation", prompt: "How do I run and replay a simulation exercise?" },
];

export function ChatPanel({ persona }: { persona: string }) {
  const { messages, input, isStreaming, error, setInput, send, cancel } = useHelpChat();
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, isStreaming]);

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
            onClick={() => setInput(qa.prompt)}
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
              void send(persona);
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
            onClick={() => void send(persona)}
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

function MessageBubble({ message }: { message: HelpChatMessage }) {
  const isUser = message.role === "user";
  const alignClass = isUser ? "text-right" : "text-left";
  const alignStyle: React.CSSProperties = { textAlign: isUser ? "right" : "left" };
  const bubbleClass =
    "inline-block max-w-[85%] rounded-lg px-3 py-2 text-left " +
    (isUser
      ? "whitespace-pre-wrap bg-blue-600 text-white"
      : message.refusalReason
        ? "bg-amber-100 text-amber-900"
        : "bg-gray-100 text-gray-900");

  return (
    <div className={alignClass} style={alignStyle}>
      <div className={bubbleClass} style={{ textAlign: "left" }}>
        {message.redacted ? <RedactionNotice /> : null}
        {message.refusalReason ? (
          <RefusalCard reason={message.refusalReason} />
        ) : message.content ? (
          isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="sim-chat-markdown">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
          )
        ) : (
          <span className="text-gray-400">…</span>
        )}
        {!isUser && message.citations && message.citations.length > 0 ? (
          <section aria-label="Sources" className="mt-2 border-t border-gray-300 pt-2">
            <h3 className="mb-1 text-xs font-semibold text-gray-700">Sources</h3>
            <ol className="list-decimal space-y-1 pl-5">
              {message.citations.map((citation, index) => (
                <li key={`${citation.source_id}-${citation.anchor}-${index}`} className="text-xs">
                  <CitationBadge index={index + 1} citation={citation} />
                  <span className="ml-1 text-gray-700">{citation.source_title}</span>
                </li>
              ))}
            </ol>
          </section>
        ) : null}
      </div>
    </div>
  );
}
