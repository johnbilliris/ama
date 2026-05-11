/**
 * spec-038 T-AA098 — degraded-mode detector.
 *
 * Surfaces a degraded state when any of the following are true:
 *   - navigator.onLine is false
 *   - service-worker reports offline event
 *   - /help/chat/ask has returned a recent 503
 */

import { useEffect, useState } from "react";

export interface DegradedState {
  offline: boolean;
  chatUnavailable: boolean;
  trigger: "offline" | "chat-503" | null;
}

export function useDegradedMode(): DegradedState {
  const [state, setState] = useState<DegradedState>({
    offline: typeof navigator !== "undefined" ? !navigator.onLine : false,
    chatUnavailable: false,
    trigger: null,
  });

  useEffect(() => {
    if (typeof window === "undefined") return;
    const on = () => setState((s) => ({ ...s, offline: false, trigger: s.chatUnavailable ? "chat-503" : null }));
    const off = () => setState((s) => ({ ...s, offline: true, trigger: "offline" }));
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    const onChat503 = () => setState((s) => ({ ...s, chatUnavailable: true, trigger: "chat-503" }));
    window.addEventListener("help.chat.503" as keyof WindowEventMap, onChat503);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
      window.removeEventListener("help.chat.503" as keyof WindowEventMap, onChat503);
    };
  }, []);

  return state;
}

export function emitChatUnavailable(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event("help.chat.503"));
}
