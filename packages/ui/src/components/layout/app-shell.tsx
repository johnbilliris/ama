import type { PropsWithChildren } from "react";

export function AppShell({ children }: PropsWithChildren) {
  return (
    <div className="ama-app-shell">
      <main>{children}</main>
    </div>
  );
}
