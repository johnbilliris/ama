/**
 * IC Approval Card panel (T036, FR-001).
 *
 * Renders rationale, source references, confidence pill, approver identity.
 * Calls `POST /api/outcomes/sc-{N}/evaluate` then re-fetches via
 * `/api/audit/list?correlation_id=...` to surface the resulting audit row.
 */

"use client";

import * as React from "react";

import { ClassifierBanner } from "../../../../lib/classifier/banner";

interface SourceRef {
  doc_id: string;
  excerpt: string;
  href?: string;
}

export interface IcApprovalCardProps {
  scenarioId: string;
  rationale: string;
  sources: SourceRef[];
  confidence: number;
  approverIdentity: string;
  endpointBase?: string;
}

interface AuditRow {
  audit_id: string;
  outcome: string;
  classifier_outcome?: string;
  masked_field_count?: number;
  timestamp: string;
}

export function IcApprovalCard(props: IcApprovalCardProps): React.ReactElement {
  const {
    scenarioId,
    rationale,
    sources,
    confidence,
    approverIdentity,
    endpointBase = "/api",
  } = props;

  const [submitting, setSubmitting] = React.useState(false);
  const [audit, setAudit] = React.useState<AuditRow | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const submit = React.useCallback(async () => {
    setSubmitting(true);
    setError(null);
    const correlationId = crypto.randomUUID();
    try {
      const evalRes = await fetch(
        `${endpointBase}/outcomes/sc-${encodeURIComponent(scenarioId)}/evaluate`,
        {
          method: "POST",
          headers: {
            "content-type": "application/json",
            "x-correlation-id": correlationId,
          },
          body: JSON.stringify({
            rationale,
            sources,
            confidence,
            approver_identity: approverIdentity,
          }),
        },
      );
      if (!evalRes.ok) {
        const body = await evalRes.json().catch(() => null);
        throw new Error(body?.detail ?? `evaluate-failed:${evalRes.status}`);
      }
      const auditRes = await fetch(
        `${endpointBase}/audit/list?correlation_id=${encodeURIComponent(correlationId)}`,
      );
      if (!auditRes.ok) throw new Error("audit-fetch-failed");
      const list = (await auditRes.json()) as { rows: AuditRow[] };
      setAudit(list.rows[0] ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }, [scenarioId, rationale, sources, confidence, approverIdentity, endpointBase]);

  const confidenceTone =
    confidence >= 0.85
      ? "bg-emerald-100 text-emerald-900"
      : confidence >= 0.6
        ? "bg-amber-100 text-amber-900"
        : "bg-rose-100 text-rose-900";

  return (
    <section
      className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
      data-testid="ic-approval-card"
    >
      <header className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">IC Approval (sc-{scenarioId})</h2>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${confidenceTone}`}
        >
          confidence {(confidence * 100).toFixed(0)}%
        </span>
      </header>
      <p className="mb-3 text-sm text-slate-800">{rationale}</p>
      <details className="mb-3">
        <summary className="cursor-pointer text-sm text-slate-600">
          Source references ({sources.length})
        </summary>
        <ul className="mt-2 space-y-1 text-sm">
          {sources.map((s) => (
            <li key={s.doc_id}>
              <span className="font-mono text-xs text-slate-500">
                {s.doc_id}
              </span>{" "}
              — {s.excerpt}
              {s.href ? (
                <>
                  {" "}
                  <a className="underline" href={s.href}>
                    open
                  </a>
                </>
              ) : null}
            </li>
          ))}
        </ul>
      </details>
      <p className="text-xs text-slate-500">
        Approver: <span className="font-mono">{approverIdentity}</span>
      </p>
      {audit ? (
        <ClassifierBanner
          outcome={(audit.classifier_outcome as never) ?? "clean"}
          maskedFieldCount={audit.masked_field_count}
          auditId={audit.audit_id}
        />
      ) : null}
      {error ? (
        <p role="alert" className="mt-2 text-sm text-rose-700">
          {error}
        </p>
      ) : null}
      <button
        type="button"
        disabled={submitting}
        onClick={submit}
        className="mt-3 rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? "Submitting…" : "Approve & emit audit"}
      </button>
    </section>
  );
}

export default IcApprovalCard;
