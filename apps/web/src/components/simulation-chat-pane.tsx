"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  getChatHistory,
  streamChat,
  type ChatEvent,
  type SimChatTurn,
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

export function SimulationChatPane({
  tenantId,
  onScenarioCard,
  onEvent,
}: {
  tenantId: string;
  onScenarioCard?: (card: Record<string, unknown>) => void;
  onEvent?: (text: string) => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isHydrating, setHydrating] = useState(true);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  // Stable ref so the hydrate effect doesn't refire when the parent's inline
  // onScenarioCard callback identity changes on every render.
  const onScenarioCardRef = useRef(onScenarioCard);
  onScenarioCardRef.current = onScenarioCard;

  // Auto-scroll to the newest message whenever the list or streamed content
  // grows. Keeps the active reply + input visible without the user chasing it.
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, isStreaming]);

  useEffect(() => {
    // Hydrate the pane with prior turns so controllers returning to an
    // ongoing exercise see the full conversation, not an empty canvas.
    let cancelled = false;
    (async () => {
      try {
        const turns = await getChatHistory(tenantId);
        if (cancelled) return;
        const seeded: ChatMessage[] = turns
          .filter((t) => t.role === "user" || t.role === "assistant")
          .map((t) => ({
            id: t.id,
            role: t.role as Role,
            content: t.content,
          }));
        setMessages(seeded);

        // Replay the most recent persisted scenario card (stored as role="tool"
        // content) so the map pin + chip reappear when a controller returns to
        // an already-seeded exercise. Without this, scenarioCard is only ever
        // set live during streaming, so a page refresh loses the Katoomba pin
        // and the map falls back to generic jurisdiction centroids.
        const latestCard = extractLatestScenarioCard(turns);
        if (latestCard) onScenarioCardRef.current?.(latestCard);
      } finally {
        if (!cancelled) setHydrating(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [tenantId]);

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
        if (ev.event === "card.scenario" && onScenarioCard) {
          onScenarioCard(ev.data as Record<string, unknown>);
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setError((err as Error).message);
      }
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  }, [input, isStreaming, tenantId, onScenarioCard]);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const exportTranscript = useCallback(() => {
    const lines = messages.map((m) => {
      const role = m.role === "user" ? "OPERATOR" : "CONTROLLER";
      return `[${role}]\n${m.content}\n`;
    });
    const blob = new Blob(
      [`# Simulation Exercise Transcript\n# Tenant: ${tenantId}\n# Exported: ${new Date().toISOString()}\n\n${lines.join("\n")}`],
      { type: "text/markdown" },
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sim-transcript-${tenantId.slice(0, 12)}-${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }, [messages, tenantId]);

  const QUICK_ACTIONS = [
    { label: "📋 SITREP", prompt: "Provide a situation report for the current simulation state." },
    { label: "🚒 Deploy", prompt: "Deploy available resources to the staging area nearest the incident." },
    { label: "📢 Alert", prompt: "Draft a public alert message for the affected area." },
    { label: "⬆ Escalate", prompt: "Escalate the current situation to executive leadership with a risk summary." },
    { label: "⚠ Risk", prompt: "Provide a risk assessment for the current scenario including hazard severity and consequences." },
  ];

  const injectQuickAction = useCallback((prompt: string) => {
    setInput(prompt);
  }, []);

  return (
    <div
      className="grid h-full min-h-0 overflow-hidden rounded border"
      style={{ gridTemplateRows: "auto minmax(0, 1fr) auto auto" }}
    >
      <header className="sim-chat-header border-b bg-amber-50 px-3 py-2 text-xs font-medium text-amber-900">
        <span>SIMULATION CONTROLLER · Exercise scope only</span>
        {messages.length > 0 && (
          <button
            type="button"
            onClick={exportTranscript}
            className="sim-export-btn"
            title="Export chat transcript for post-exercise review"
          >
            ⬇ Export
          </button>
        )}
      </header>
      <div
        ref={scrollRef}
        className="min-h-0 space-y-3 overflow-y-auto p-3 text-sm"
      >
        {isHydrating && (
          <p className="text-xs text-gray-400">Loading prior conversation…</p>
        )}
        {!isHydrating && messages.length === 0 && (
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
      {/* Quick-action buttons for common operational commands */}
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
  // iMessage-style alignment: the operator's own messages hug the RIGHT
  // edge (outgoing blue bubbles), assistant replies hug the LEFT edge
  // (incoming grey bubbles). We set text-align both via utility class AND
  // inline style because this project ships a hand-authored utility set
  // and the inline style guarantees correct alignment regardless.
  const alignClass = isUser ? "text-right" : "text-left";
  const alignStyle: React.CSSProperties = {
    textAlign: isUser ? "right" : "left",
  };
  // Derive a concise human-readable card summary (hazard · location · level)
  // from the scenario payload so we never expose raw IDs / JSON to operators.
  const cardSummary = message.card ? summariseScenarioCard(message.card) : null;
  const bubbleClass =
    "inline-block max-w-[85%] rounded-lg px-3 py-2 text-left " +
    (isUser
      ? "whitespace-pre-wrap bg-blue-600 text-white"
      : message.refused
        ? "whitespace-pre-wrap bg-amber-100 text-amber-900"
        : "sim-chat-markdown bg-gray-100 text-gray-900");
  return (
    <div className={alignClass} style={alignStyle}>
      <div className={bubbleClass} style={{ textAlign: "left" }}>
        {message.content ? (
          isUser ? (
            message.content
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          )
        ) : (
          <span className="text-gray-400">…</span>
        )}
      </div>
      {message.toolCalls?.map((t, i) => (
        <div key={i} className="mt-1 text-xs text-gray-500">
          → tool <code className="rounded bg-gray-100 px-1">{t.name}</code>
          {t.arguments.sub_agent ? ` (${String(t.arguments.sub_agent)})` : ""}
        </div>
      ))}
      {cardSummary && (
        <div
          className="mt-2 inline-flex max-w-[85%] items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-left text-[11px] text-emerald-900"
          style={{ textAlign: "left" }}
        >
          <span aria-hidden="true">📍</span>
          <span>
            <strong className="font-semibold">Scenario seeded</strong> — {cardSummary}
          </span>
        </div>
      )}
    </div>
  );
}

function summariseScenarioCard(card: Record<string, unknown>): string {
  const hazard =
    typeof card.hazard === "string" && card.hazard ? card.hazard : "scenario";
  const locObj = (card.location as Record<string, unknown>) || {};
  const locName =
    typeof locObj.name === "string" && locObj.name ? locObj.name : "unspecified";
  const levelRaw =
    typeof card.aws_default_level === "string" ? card.aws_default_level : "";
  const level = levelRaw ? levelRaw.replace(/_/g, " ") : "";
  return level ? `${hazard} near ${locName} · ${level}` : `${hazard} near ${locName}`;
}

// Walk tool turns newest-first and return the first payload that looks like a
// scenario card (produced by `seed_scenario` on the backend). Tool turns store
// the card as a JSON string in `content`; anything that fails to parse or lacks
// the hazard+location shape is ignored so other tool results can't masquerade
// as a card.
function extractLatestScenarioCard(
  turns: SimChatTurn[],
): Record<string, unknown> | null {
  for (let i = turns.length - 1; i >= 0; i--) {
    const t = turns[i];
    if (t.role !== "tool" || !t.content) continue;
    try {
      const parsed = JSON.parse(t.content) as Record<string, unknown>;
      if (
        parsed &&
        typeof parsed === "object" &&
        typeof parsed.hazard === "string" &&
        parsed.location &&
        typeof parsed.location === "object"
      ) {
        return parsed;
      }
    } catch {
      // Non-JSON tool result (e.g. summarise_state) — skip.
    }
  }
  return null;
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
    const technicalMessage = String(ev.data.message ?? "chat error");
    const displayMessage = formatChatErrorForDisplay(code, technicalMessage);
    setMessages((prev) =>
      prev.map((m) =>
        m.id === assistantId
          ? { ...m, content: displayMessage, refused: true }
          : m,
      ),
    );
  }
}

// Friendly copy shown to coordinators in staging/production. The raw technical
// payload (Azure OpenAI JSON, stack traces) is only useful while developing and
// leaks implementation detail — including internal error codes and filter
// categories — that non-technical users don't need.
const FRIENDLY_CHAT_ERROR: Record<string, string> = {
  content_filter:
    "Your message included wording that the AI safety filter blocked. " +
    "Please rephrase — for example, describe the operational action directly " +
    "(\u201cupgrade the Blackheath warning to Watch and Act; fire behaviour is worsening\u201d) " +
    "rather than framing it as escalation or intensification.",
  openai_unavailable:
    "The AI assistant is temporarily unavailable. Please try again in a moment. " +
    "If the issue persists, contact your administrator.",
};

const FRIENDLY_CHAT_ERROR_FALLBACK =
  "Something went wrong while processing your message. Please try again.";

function formatChatErrorForDisplay(code: string, technicalMessage: string): string {
  // Raw technical payloads are useful while developing but must never reach
  // coordinators in staging/production. NEXT_PUBLIC_ENVIRONMENT is baked in at
  // build time and defaults to a safe (friendly-only) surface when unset.
  const env = (process.env.NEXT_PUBLIC_ENVIRONMENT ?? "").toLowerCase();
  const isDev = env === "local" || env === "development";
  const friendly = FRIENDLY_CHAT_ERROR[code] ?? FRIENDLY_CHAT_ERROR_FALLBACK;
  if (isDev) {
    return `${friendly}\n\n[dev ${code}] ${technicalMessage}`;
  }
  return friendly;
}
