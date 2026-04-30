"use client";

import Link from "next/link";

import type { WorkflowRun, WorkflowRunStatus } from "@/lib/api/workflow-runs";

/**
 * WorkflowRunList (T053).
 *
 * Lists runs grouped into the 7 canonical state tabs (FR-011b) with badge
 * counts. Every tab is keyboard-navigable; tab order matches the lifecycle.
 */

const STATE_ORDER: WorkflowRunStatus[] = [
  "Running",
  "AwaitingApproval",
  "NeedsOperatorDecision",
  "Completed",
  "Failed",
  "Cancelled",
  "Superseded",
];

interface Props {
  runs: WorkflowRun[];
  selectedStatus?: WorkflowRunStatus;
}

export function WorkflowRunList({ runs, selectedStatus }: Props) {
  const grouped = STATE_ORDER.reduce<Record<WorkflowRunStatus, WorkflowRun[]>>(
    (acc, s) => ({ ...acc, [s]: [] }),
    {} as Record<WorkflowRunStatus, WorkflowRun[]>,
  );
  for (const r of runs) {
    grouped[r.status]?.push(r);
  }
  const active = selectedStatus ?? STATE_ORDER.find((s) => grouped[s].length > 0) ?? "Running";

  return (
    <div className="space-y-4">
      <nav aria-label="Workflow run states" className="flex flex-wrap gap-2 border-b">
        {STATE_ORDER.map((s) => {
          const count = grouped[s].length;
          const isActive = s === active;
          return (
            <Link
              key={s}
              href={{ pathname: "/operations/workflows", query: { state: s } }}
              role="tab"
              aria-selected={isActive}
              className={
                isActive
                  ? "border-b-2 border-indigo-600 px-3 py-2 text-sm font-semibold"
                  : "px-3 py-2 text-sm text-slate-600"
              }
            >
              {s}{" "}
              <span aria-label={`${count} runs`} className="ml-1 rounded bg-slate-100 px-2 text-xs">
                {count}
              </span>
            </Link>
          );
        })}
      </nav>

      <ul className="divide-y" aria-label={`Workflow runs in ${active}`}>
        {grouped[active].map((r) => (
          <li key={r.id} className="py-2 text-sm">
            <Link
              href={{ pathname: "/operations/workflows", query: { run: r.id } }}
              className="text-indigo-600 hover:underline"
            >
              {r.incident_id}
            </Link>{" "}
            <span className="font-mono text-xs text-slate-500">{r.id.slice(0, 8)}</span>{" "}
            · step <em>{r.current_step}</em>
          </li>
        ))}
        {grouped[active].length === 0 ? <li className="py-2 text-sm text-slate-500">None.</li> : null}
      </ul>
    </div>
  );
}
