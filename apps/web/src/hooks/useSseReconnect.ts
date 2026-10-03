/**
 * Spec-036 T-I05 — `useSseReconnect` hook.
 *
 * Manages an `EventSource` connection with:
 *   - exponential back-off (1s → 2s → 4s → 8s, capped at 30s)
 *   - `Last-Event-ID` resume across reconnects
 *   - `AbortController`-equivalent cleanup on unmount
 *
 * EventSource itself sends `Last-Event-ID` automatically when it sees
 * an `id:` field in the SSE stream, so this hook just tracks it for
 * debug surfacing and for tests.
 */
import { useEffect, useRef, useState } from "react";

interface UseSseReconnectOptions {
  /** Fully-qualified SSE URL. */
  url: string;
  /** Called once per parsed event. */
  onEvent?: (event: MessageEvent) => void;
  /** Called when the connection transitions to open. */
  onOpen?: () => void;
  /** Called on each error (before back-off retry). */
  onError?: (event: Event, attempt: number) => void;
  /** Disable when false — used to defer connection until ready. */
  enabled?: boolean;
  /** Custom EventSource factory — primarily for tests with FakeEventSource. */
  eventSourceFactory?: (url: string) => EventSourceLike;
  /** Initial back-off in ms (default 1000). */
  initialBackoffMs?: number;
  /** Cap on back-off in ms (default 30000). */
  maxBackoffMs?: number;
}

export interface EventSourceLike {
  addEventListener(
    type: string,
    listener: (event: Event) => void,
  ): void;
  removeEventListener(
    type: string,
    listener: (event: Event) => void,
  ): void;
  close(): void;
  readonly readyState: number;
}

interface UseSseReconnectState {
  status: "idle" | "connecting" | "open" | "retrying" | "closed";
  lastEventId: string | null;
  attempt: number;
}

export function useSseReconnect({
  url,
  onEvent,
  onOpen,
  onError,
  enabled = true,
  eventSourceFactory,
  initialBackoffMs = 1000,
  maxBackoffMs = 30000,
}: UseSseReconnectOptions): UseSseReconnectState {
  const [status, setStatus] = useState<UseSseReconnectState["status"]>("idle");
  const [lastEventId, setLastEventId] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const onEventRef = useRef(onEvent);
  const onOpenRef = useRef(onOpen);
  const onErrorRef = useRef(onError);
  onEventRef.current = onEvent;
  onOpenRef.current = onOpen;
  onErrorRef.current = onError;

  useEffect(() => {
    if (!enabled) {
      setStatus("idle");
      return;
    }
    let cancelled = false;
    let currentSource: EventSourceLike | null = null;
    let backoffTimer: ReturnType<typeof setTimeout> | null = null;
    let localAttempt = 0;

    const connect = () => {
      if (cancelled) return;
      setStatus(localAttempt === 0 ? "connecting" : "retrying");
      const factory =
        eventSourceFactory ??
        ((u: string) => new EventSource(u, { withCredentials: false }));
      const es = factory(url);
      currentSource = es;

      const handleOpen = () => {
        if (cancelled) return;
        localAttempt = 0;
        setAttempt(0);
        setStatus("open");
        onOpenRef.current?.();
      };

      const handleMessage = (raw: Event) => {
        if (cancelled) return;
        const message = raw as MessageEvent;
        if (typeof message.lastEventId === "string" && message.lastEventId) {
          setLastEventId(message.lastEventId);
        }
        onEventRef.current?.(message);
      };

      const handleError = (raw: Event) => {
        if (cancelled) return;
        onErrorRef.current?.(raw, localAttempt);
        es.close();
        currentSource = null;
        // Exponential back-off — 1s, 2s, 4s, … capped at maxBackoffMs.
        const delay = Math.min(
          initialBackoffMs * Math.pow(2, localAttempt),
          maxBackoffMs,
        );
        localAttempt += 1;
        setAttempt(localAttempt);
        setStatus("retrying");
        backoffTimer = setTimeout(connect, delay);
      };

      es.addEventListener("open", handleOpen);
      es.addEventListener("message", handleMessage);
      es.addEventListener("error", handleError);
    };

    connect();

    return () => {
      cancelled = true;
      if (backoffTimer) clearTimeout(backoffTimer);
      if (currentSource) currentSource.close();
      setStatus("closed");
    };
    // The `*Ref` mirrors above let us depend only on URL/enabled/factory
    // without forcing a reconnect on every parent render.
     
  }, [url, enabled, eventSourceFactory, initialBackoffMs, maxBackoffMs]);

  return { status, lastEventId, attempt };
}

export default useSseReconnect;
