"use client";

import { useCallback, useRef, useState } from "react";
import {
  streamChat,
  type ChatEvent,
} from "@/lib/api/simulation_chat";

type Role = "user" | "assistant";

interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  toolCalls?: { name: string; arguments: Record<string, unknown> }[];
  card?: Record<string, unknown>;
  refused?: boolean;
}

export function SimulationChatPane({ tenantId }: { tenantId: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const send = useCallback(async () => {
    if (!input.trim() || isStreaming) return;
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: input.trim(),
    };
    const assistantId = crypto.randomUUID();
    setMessages((prev) => [
      ...prev,
      userMsg,
      { id: assistantId, role: "assistant", content: "" },
    ]);
    setInput("");
    setStreaming(true);
    setError(null);

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      for await (const ev of streamChat(tenantId, userMsg.content, ctrl.signal)) {
        applyEvent(assistantId, ev, setMessages);
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setError((err as Error).message);
      }
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  }, [input, isStreaming, tenantId]);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return (
    <div className="flex h-[520px] flex-col rounded border">
      <header className="border-b bg-amber-50 px-3 py-2 text-xs font-medium text-amber-900">
        SIMULATION CONTROLLER · Exercise scope only · No real-world dispatch
      </header>
      <div className="flex-1 space-y-3 overflow-y-auto p-3 text-sm">
        {messages.length === 0 && (
          <p className="text-gray-500">
            Describe a scenario to begin. Example: <em>&ldquo;Bushfire near Katoomba, 39&nbsp;°C,
            NW winds 55&nbsp;km/h, start 14:00 AEST&rdquo;</em>
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
      <footer className="flex gap-2 border-t p-2">
        <textarea
          aria-label="Simulation chat input"
          className="flex-1 resize-none rounded border px-2 py-1 text-sm"
          rows={2}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          placeholder="Ask the Simulation Controller…"
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
            onClick={send}
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
  return (
    <div className={isUser ? "text-right" : "text-left"}>
      <div
        className={
          "inline-block max-w-[85%] whitespace-pre-wrap rounded-lg px-3 py-2 " +
          (isUser
            ? "bg-blue-600 text-white"
            : message.refused
              ? "bg-amber-100 text-amber-900"
              : "bg-gray-100 text-gray-900")
        }
      >
        {message.content || <span className="text-gray-400">…</span>}
      </div>
      {message.toolCalls?.map((t, i) => (
        <div key={i} className="mt-1 text-xs text-gray-500">
          → tool <code className="rounded bg-gray-100 px-1">{t.name}</code>
          {t.arguments.sub_agent ? ` (${String(t.arguments.sub_agent)})` : ""}
        </div>
      ))}
      {message.card && (
        <div className="mt-2 rounded border bg-white p-3 text-left text-xs shadow-sm">
          <p className="mb-1 font-semibold">Scenario card (review &amp; confirm)</p>
          <pre className="overflow-x-auto whitespace-pre-wrap text-[11px]">
            {JSON.stringify(message.card, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

function applyEvent(
  assistantId: string,
  ev: ChatEvent,
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>,
) {
  if (ev.event === "turn.delta") {
    const delta = String(ev.data.delta ?? "");
    setMessages((prev) =>
      prev.map((m) =>
        m.id === assistantId ? { ...m, content: m.content + delta } : m,
      ),
    );
  } else if (ev.event === "tool.call") {
    const name = String(ev.data.name ?? "");
    const args = (ev.data.arguments as Record<string, unknown>) ?? {};
    setMessages((prev) =>
      prev.map((m) =>
        m.id === assistantId
          ? { ...m, toolCalls: [...(m.toolCalls ?? []), { name, arguments: args }] }
          : m,
      ),
    );
  } else if (ev.event === "card.scenario") {
    setMessages((prev) =>
      prev.map((m) => (m.id === assistantId ? { ...m, card: ev.data } : m)),
    );
  } else if (ev.event === "turn.end") {
    if (ev.data.refused) {
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, refused: true } : m)),
      );
    }
  } else if (ev.event === "error") {
    const code = String(ev.data.code ?? "error");
    const msg = String(ev.data.message ?? "chat error");
    setMessages((prev) =>
      prev.map((m) =>
        m.id === assistantId ? { ...m, content: `(${code}) ${msg}`, refused: true } : m,
      ),
    );
  }
}
