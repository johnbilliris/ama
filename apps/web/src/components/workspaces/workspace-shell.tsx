"use client";

import type { ReactNode } from "react";

interface WorkspaceShellProps {
  ariaLabel?: string;
  kicker: string;
  title: string;
  subtitle: string;
  children: ReactNode;
  footer?: ReactNode;
}

export function WorkspaceShell({
  ariaLabel,
  kicker,
  title,
  subtitle,
  children,
  footer,
}: WorkspaceShellProps) {
  return (
    <section className="workspace-shell" aria-label={ariaLabel}>
      <header className="workspace-header">
        <p className="workspace-kicker">{kicker}</p>
        <h1 className="workspace-title">{title}</h1>
        <p className="workspace-org">{subtitle}</p>
      </header>
      {children}
      {footer}
    </section>
  );
}
