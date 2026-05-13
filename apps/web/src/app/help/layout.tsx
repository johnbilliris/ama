/** spec-038 T-AA099 — persistent help shell with chat right-rail.
 *
 * The chat lives in the layout (not the page) so it survives navigation
 * between `/help`, `/help/articles/[slug]`, `/help/playbooks`, etc.
 * Layout mirrors the simulation dashboard: full-viewport-height grid
 * with documentation occupying ~75% on the left and the grounded help
 * assistant pinned to the right ~25%.
 */
import type { ReactNode } from "react";
import { ChatPanel } from "@/components/help/ChatPanel";

export const metadata = { title: "Help · AMA Hub" };

export default function HelpLayout({ children }: { children: ReactNode }) {
  return (
    <section data-help-shell className="help-shell-page">
      <a href="#help-main" className="sr-only focus:not-sr-only">Skip to help content</a>
      <div className="help-shell-wrap">
        <div className="help-shell-layout">
          <main id="help-main" className="help-shell-content">
            {children}
          </main>

          {/* Persistent grounded help chat — preserved across help routes. */}
          <aside aria-labelledby="help-chat-heading" className="sim-right-panel">
            <header className="sim-right-header">
              <h2 id="help-chat-heading">Help Assistant</h2>
              <p>Grounded in approved Hub documentation. Cites sources, refuses out-of-scope questions.</p>
            </header>
            <div className="sim-right-chat">
              <ChatPanel persona="operational-default" />
            </div>
          </aside>
        </div>
      </div>
    </section>
  );
}
