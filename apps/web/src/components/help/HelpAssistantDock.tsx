"use client";
/**
 * Global Help Assistant launcher + slide-over.
 *
 * Mounted once at the root layout so the conversation persists across every
 * route navigation. Hides itself on `/help/*` routes because the help shell
 * already pins ChatPanel into its right rail (state is shared via
 * `useHelpChat`, so opening the global dock from a non-help page and then
 * navigating to `/help` shows the same conversation in the rail).
 */
import { usePathname } from "next/navigation";
import { useEffect } from "react";

import { ChatPanel } from "@/components/help/ChatPanel";
import { useHelpChat } from "@/lib/help/chatStore";

export function HelpAssistantDock({ persona = "operational-default" }: { persona?: string }) {
  const pathname = usePathname() ?? "/";
  const { isOpen, setOpen, toggleOpen, messages } = useHelpChat();
  const hidden = pathname === "/help" || pathname.startsWith("/help/");

  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isOpen, setOpen]);

  if (hidden) return null;

  return (
    <>
      <button
        type="button"
        onClick={toggleOpen}
        aria-label={isOpen ? "Close Help Assistant" : "Open Help Assistant"}
        aria-expanded={isOpen}
        aria-controls="help-assistant-dock-panel"
        className="help-dock-launcher"
      >
        <span aria-hidden="true">💬</span>
        <span className="help-dock-launcher-label">Help</span>
        {messages.length > 0 ? (
          <span className="help-dock-launcher-badge" aria-label={`${messages.length} messages`}>
            {messages.length}
          </span>
        ) : null}
      </button>

      {isOpen ? (
        <aside
          id="help-assistant-dock-panel"
          role="complementary"
          aria-label="Help Assistant"
          className="help-dock-panel"
        >
          <div className="help-dock-panel-header">
            <div>
              <p className="help-dock-panel-kicker">Help Assistant</p>
              <p className="help-dock-panel-sub">Grounded in approved Hub documentation.</p>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close Help Assistant"
              className="help-dock-panel-close"
            >
              ×
            </button>
          </div>
          <div className="help-dock-panel-body">
            <ChatPanel persona={persona} />
          </div>
        </aside>
      ) : null}
    </>
  );
}
