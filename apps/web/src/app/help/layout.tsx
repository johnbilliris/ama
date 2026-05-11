/** spec-038 T-AA099 — persistent help shell with telemetry mount. */
import type { ReactNode } from "react";

export const metadata = { title: "Help · AMA Hub" };

export default function HelpLayout({ children }: { children: ReactNode }) {
  return (
    <section data-help-shell className="min-h-screen">
      <a href="#help-main" className="sr-only focus:not-sr-only">Skip to help content</a>
      <main id="help-main">{children}</main>
    </section>
  );
}
