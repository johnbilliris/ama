/**
 * spec-038 T-AA096 — typed SSE consumer for /help/chat/ask.
 *
 * Provides reconnect + cancel; surfaces typed events for ChatPanel.
 */

export type ChatSseEvent =
  | { kind: "meta"; payload: { session_id: string; snapshot_id: string; persona_id: string; redaction_notice: boolean } }
  | { kind: "delta"; payload: { text: string } }
  | { kind: "citation"; payload: { source_id: string; source_title: string; anchor: string; snippet?: string } }
  | { kind: "refusal"; payload: { reason: string } }
  | { kind: "done"; payload: { audit_entry_id: string; pattern_id: string; turn_index: number; refusal_reason: string | null } };

export interface ChatStreamHandler {
  onEvent: (event: ChatSseEvent) => void;
  onError?: (error: Error) => void;
  onClose?: () => void;
}

export async function streamChatAsk(
  body: { message: string; session_id?: string; persona_id?: string; surface_id?: string; jurisdiction_codes?: string[] },
  handler: ChatStreamHandler,
  init?: { url?: string; headers?: HeadersInit; signal?: AbortSignal },
): Promise<void> {
  const url = init?.url ?? "/api/help/chat/ask";
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream", ...init?.headers },
    body: JSON.stringify(body),
    signal: init?.signal,
  });
  if (!resp.ok || !resp.body) {
    handler.onError?.(new Error(`chat/ask failed ${resp.status}`));
    return;
  }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buf.indexOf("\n\n")) >= 0) {
      const frame = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      const event = parseFrame(frame);
      if (event) handler.onEvent(event);
    }
  }
  handler.onClose?.();
}

function parseFrame(frame: string): ChatSseEvent | null {
  let eventName = "";
  let dataLine = "";
  for (const line of frame.split("\n")) {
    if (line.startsWith("event: ")) eventName = line.slice(7).trim();
    else if (line.startsWith("data: ")) dataLine += line.slice(6);
  }
  if (!eventName || !dataLine) return null;
  try {
    const payload = JSON.parse(dataLine);
    return { kind: eventName as ChatSseEvent["kind"], payload } as ChatSseEvent;
  } catch {
    return null;
  }
}
