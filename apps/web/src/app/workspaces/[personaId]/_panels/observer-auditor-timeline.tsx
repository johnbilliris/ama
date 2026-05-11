/**
 * Observer / Auditor append-only timeline panel (T038, FR-003).
 *
 * Append-only UX. PATCH/DELETE attempts are intercepted client-side and
 * routed to a synthetic UI-rejection handler that emits an `outcome=denied`
 * audit row with the rationale and surfaces a non-silent error.
 */

"use client";

import * as React from "react";

interface AuditRow {
  audit_id: string;
  outcome: string;
  rationale?: string;
  timestamp: string;
  actor: string;
}

export interface ObserverAuditorTimelineProps {
  rows: AuditRow[];
  endpointBase?: string;
}

export function ObserverAuditorTimeline(
  props: ObserverAuditorTimelineProps,
): React.ReactElement {
  const { rows, endpointBase = "/api" } = props;
  const [denialError, setDenialError] = React.useState<string | null>(null);

  const handleEditAttempt = async (auditId: string, action: "edit" | "delete") => {
    const message =
      action === "edit"
        ? "Audit rows are append-only. Edit attempts are denied per FR-003."
        : "Audit rows are append-only. Delete attempts are denied per FR-003.";
    setDenialError(message);
    try {
      await fetch(`${endpointBase}/audit/denied-mutation`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          attempted_action: action,
          target_audit_id: auditId,
          rationale: "append-only-policy",
        }),
      });
    } catch {
      // Policy is server-enforced; the synthetic emit is best-effort.
    }
  };

  return (
    <section
      className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
      data-testid="observer-auditor-timeline"
    >
      <header className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Audit timeline (append-only)</h2>
        <span className="text-xs text-slate-500">FR-003</span>
      </header>
      {denialError ? (
        <p
          role="alert"
          aria-live="assertive"
          className="mb-3 rounded-md border border-rose-300 bg-rose-50 p-2 text-sm text-rose-900"
          data-testid="observer-auditor-denial"
        >
          {denialError}
        </p>
      ) : null}
      <ol className="space-y-2 text-sm">
        {rows.map((r) => (
          <li
            key={r.audit_id}
            className="rounded-md border border-slate-200 p-2"
          >
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs text-slate-500">
                {r.timestamp}
              </span>
              <span className="text-xs">{r.outcome}</span>
            </div>
            <p>{r.rationale ?? "—"}</p>
            <p className="text-xs text-slate-500">by {r.actor}</p>
            <div className="mt-1 flex gap-2 text-xs">
              <button
                type="button"
                className="text-rose-700 underline"
                onClick={() => handleEditAttempt(r.audit_id, "edit")}
              >
                Attempt edit (denied)
              </button>
              <button
                type="button"
                className="text-rose-700 underline"
                onClick={() => handleEditAttempt(r.audit_id, "delete")}
              >
                Attempt delete (denied)
              </button>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

export default ObserverAuditorTimeline;
