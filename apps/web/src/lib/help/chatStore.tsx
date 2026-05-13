"use client";
/**
 * Persistent help-chat store.
 *
 * The provider is mounted once at the root layout, so navigating between
 * any two routes (e.g. `/governance/dashboard` → `/help/articles/foo`) does
 * not unmount it and the conversation, current draft input, in-flight
 * stream, and dock open/close state all survive intact.
 *
 * State is also mirrored to `sessionStorage` so a hard reload within the
 * same browser tab restores the conversation.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { streamChatAsk, type ChatSseEvent } from "@/lib/help/sseClient";

export interface HelpCitation {
  source_id: string;
  source_title: string;
  anchor: string;
  snippet?: string;
}

export interface HelpChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: HelpCitation[];
  refusalReason?: string;
  redacted?: boolean;
}

interface HelpChatState {
  messages: HelpChatMessage[];
  input: string;
  isStreaming: boolean;
  error: string | null;
  isOpen: boolean;
  setInput: (value: string) => void;
  send: (persona: string) => Promise<void>;
  cancel: () => void;
  reset: () => void;
  setOpen: (open: boolean) => void;
  toggleOpen: () => void;
}

const STORAGE_KEY = "ama:help-chat:v1";

const HelpChatContext = createContext<HelpChatState | null>(null);

interface PersistedShape {
  messages: HelpChatMessage[];
  input: string;
  isOpen: boolean;
}

function loadPersisted(): PersistedShape | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<PersistedShape>;
    return {
      messages: Array.isArray(parsed.messages) ? parsed.messages : [],
      input: typeof parsed.input === "string" ? parsed.input : "",
      isOpen: Boolean(parsed.isOpen),
    };
  } catch {
    return null;
  }
}

export function HelpChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<HelpChatMessage[]>([]);
  const [input, setInputState] = useState("");
  const [isStreaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setOpen] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  // One-shot hydration from sessionStorage on mount (client-only).
  useEffect(() => {
    const persisted = loadPersisted();
    if (persisted) {
      setMessages(persisted.messages);
      setInputState(persisted.input);
      setOpen(persisted.isOpen);
    }
    setHydrated(true);
  }, []);

  // Persist on relevant state changes (after hydration to avoid clobber).
  useEffect(() => {
    if (!hydrated || typeof window === "undefined") return;
    try {
      window.sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ messages, input, isOpen } satisfies PersistedShape),
      );
    } catch {
      // SessionStorage may be unavailable (private mode quotas) — ignore.
    }
  }, [messages, input, isOpen, hydrated]);

  const setInput = useCallback((value: string) => setInputState(value), []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setStreaming(false);
  }, []);

  const send = useCallback(
    async (persona: string) => {
      const prompt = input.trim();
      if (!prompt || isStreaming) return;

      const userMsg: HelpChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: prompt,
      };
      const assistantId = crypto.randomUUID();
      setMessages((prev) => [
        ...prev,
        userMsg,
        { id: assistantId, role: "assistant", content: "", citations: [] },
      ]);
      setInputState("");
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
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (abortRef.current === ctrl) abortRef.current = null;
        setStreaming(false);
      }
    },
    [input, isStreaming],
  );

  const reset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setMessages([]);
    setInputState("");
    setError(null);
    setStreaming(false);
  }, []);

  const toggleOpen = useCallback(() => setOpen((v) => !v), []);

  const value = useMemo<HelpChatState>(
    () => ({
      messages,
      input,
      isStreaming,
      error,
      isOpen,
      setInput,
      send,
      cancel,
      reset,
      setOpen,
      toggleOpen,
    }),
    [messages, input, isStreaming, error, isOpen, setInput, send, cancel, reset, toggleOpen],
  );

  return <HelpChatContext.Provider value={value}>{children}</HelpChatContext.Provider>;
}

export function useHelpChat(): HelpChatState {
  const ctx = useContext(HelpChatContext);
  if (!ctx) {
    throw new Error("useHelpChat must be used within <HelpChatProvider/>");
  }
  return ctx;
}
