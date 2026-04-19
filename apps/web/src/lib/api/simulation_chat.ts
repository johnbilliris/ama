/**
 * Client for the Simulation Controller SSE chat endpoint.
 *
 * Parses the event stream produced by `POST /api/simulations/{tenantId}/chat`
 * according to the contract in `specs/024-simulation-control-chat/contracts/simulation-chat-api.md`.
 *
 * No external deps — uses the browser fetch + ReadableStream with a tiny SSE parser.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export type ChatEventName =
  | "turn.start"
  | "turn.delta"
  | "tool.call"
  | "tool.result"
  | "card.scenario"
  | "banner.throttle"
  | "turn.end"
  | "error";

export interface ChatEvent {
  event: ChatEventName;
  data: Record<string, unknown>;
}

export async function* streamChat(
  tenantId: string,
  message: string,
  signal?: AbortSignal,
): AsyncGenerator<ChatEvent> {
  const res = await fetch(
    `${API_BASE_URL}/simulations/${encodeURIComponent(tenantId)}/chat`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({ message }),
      signal,
    },
  );
  if (!res.ok || !res.body) {
    throw new Error(`chat ${res.status}: ${await res.text()}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx;
    // Events are separated by blank lines per the SSE spec.
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const raw = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const parsed = parseEvent(raw);
      if (parsed) yield parsed;
    }
  }
}

function parseEvent(raw: string): ChatEvent | null {
  let event: string | null = null;
  const dataLines: string[] = [];
  for (const line of raw.split(/\r?\n/)) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (!event || dataLines.length === 0) return null;
  try {
    return { event: event as ChatEventName, data: JSON.parse(dataLines.join("\n")) };
  } catch {
    return null;
  }
}
