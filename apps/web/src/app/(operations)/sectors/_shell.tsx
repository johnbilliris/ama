/**
 * Shared sector-workspace shell (spec-035 T054..T060).
 *
 * Sector pages are net-new operational personas (T187..T199). Each page
 * composes the cultural-safety, infrastructure-overlay, and claims-velocity
 * subsystems plus the existing IC approval card / PIO composer / risk matrix
 * panels under one route. The shell normalises page chrome and keeps each
 * sector page focused on its FR-bound composition.
 */

"use client";

import * as React from "react";

export interface SectorWorkspaceShellProps {
  sectorCode: string;
  jurisdiction: string;
  title: string;
  fr: string;
  taskId: string;
  description: string;
  children: React.ReactNode;
}

export function SectorWorkspaceShell(
  props: SectorWorkspaceShellProps,
): React.ReactElement {
  const { sectorCode, jurisdiction, title, fr, taskId, description, children } = props;
  return (
    <div
      className="mx-auto max-w-7xl"
      data-testid={`sector-workspace-${sectorCode}`}
      data-task-id={taskId}
      data-jurisdiction={jurisdiction}
    >
      <header className="preparedness-header page-gutter-header">
        <p className="preparedness-kicker">
          {jurisdiction} · {taskId} · {fr}
        </p>
        <h1 className="preparedness-title">{title}</h1>
        <p className="preparedness-copy">{description}</p>
        <div
          data-testid="au-region-banner"
          role="note"
          aria-label="Data residency"
          className="mt-3 inline-flex items-center rounded border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-900"
        >
          Hosted in Australia · AU data residency
        </div>
      </header>
      <main className="p-6">
        <div className="grid gap-4 lg:grid-cols-2">{children}</div>
      </main>
    </div>
  );
}

export default SectorWorkspaceShell;
