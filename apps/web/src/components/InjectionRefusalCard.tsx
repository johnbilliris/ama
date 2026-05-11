/**
 * Spec-036 T-I03 — telemetry injection refusal card.
 *
 * Rendered when the controller's injection request is refused. Renders a
 * full RFC 7807 problem-detail (FR-010) so the operator immediately sees
 * the machine-readable code, the human reason, and a link to the audit
 * envelope that captured the refusal.
 */

import { SimBadge } from "./SimBadge";

/**
 * RFC 7807 application/problem+json shape — minimal subset used by the
 * simulation backend. Extra fields (`audit_entry_id`, `correlation_id`)
 * are spec-036 extensions — kept under additional properties so any
 * future RFC-7807 problem can be rendered as-is.
 */
export interface RfcProblemDetail {
  type: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  audit_entry_id?: string;
  correlation_id?: string;
  /** Allow callers to include additional reason-codes / error fields. */
  [extra: string]: unknown;
}

export interface InjectionRefusalCardProps {
  problem: RfcProblemDetail;
  /** Click handler for the audit-link button. */
  onOpenAudit?: (auditEntryId: string) => void;
  /** Click handler for the "retry" button (advisory). */
  onRetry?: () => void;
}

export function InjectionRefusalCard({
  problem,
  onOpenAudit,
  onRetry,
}: InjectionRefusalCardProps) {
  const code = problem.type.split("/").pop() || problem.type;
  return (
    <article
      role="alert"
      aria-live="polite"
      aria-label="Synthetic signal injection refused"
      className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900"
      data-testid="injection-refusal-card"
    >
      <header className="mb-1 flex items-center gap-2">
        <SimBadge size="sm" />
        <strong className="font-semibold">Injection refused</strong>
        <span
          className="rounded bg-amber-200 px-1.5 py-0.5 font-mono text-[10px] text-amber-900"
          data-testid="refusal-code"
        >
          {code}
        </span>
        <span className="ml-auto text-[10px] text-amber-700">
          HTTP {problem.status}
        </span>
      </header>
      <h3 className="mb-1 text-[13px] font-semibold">{problem.title}</h3>
      {problem.detail && (
        <p className="text-[12px] leading-snug">{problem.detail}</p>
      )}
      <footer className="mt-2 flex flex-wrap items-center gap-2">
        {problem.audit_entry_id && (
          <button
            type="button"
            className="rounded bg-amber-700 px-2 py-0.5 text-[11px] font-medium text-white hover:bg-amber-800 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-1"
            onClick={() => onOpenAudit?.(problem.audit_entry_id!)}
            aria-label={`Open audit envelope ${problem.audit_entry_id}`}
          >
            🔗 Audit envelope
          </button>
        )}
        {onRetry && (
          <button
            type="button"
            className="rounded border border-amber-400 bg-white px-2 py-0.5 text-[11px] font-medium text-amber-900 hover:bg-amber-50 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-1"
            onClick={onRetry}
          >
            Retry
          </button>
        )}
        {problem.correlation_id && (
          <span className="font-mono text-[10px] text-amber-700">
            cid: {problem.correlation_id}
          </span>
        )}
      </footer>
    </article>
  );
}

export default InjectionRefusalCard;
