/**
 * Spec-036 T-I03 — telemetry injection confirmation card.
 *
 * Rendered after a successful injection (FR-008 happy path). Shows a
 * concise summary of the synthetic signal that was accepted: hazard class,
 * jurisdiction, severity, dispatcher routing decision, and the audit-id
 * link controllers can paste into After-Action Review notes.
 */

import { SimBadge } from "./SimBadge";

export interface InjectionConfirmCardProps {
  signalId: string;
  hazardClass: string;
  jurisdiction: string;
  severity: "low" | "moderate" | "high" | "extreme";
  routedTo: string;
  auditEntryId: string;
  /** ISO-8601 UTC timestamp shown in the card. */
  acceptedAt: string;
  /** Click handler for the audit-link button. */
  onOpenAudit?: (auditEntryId: string) => void;
}

export function InjectionConfirmCard({
  signalId,
  hazardClass,
  jurisdiction,
  severity,
  routedTo,
  auditEntryId,
  acceptedAt,
  onOpenAudit,
}: InjectionConfirmCardProps) {
  return (
    <article
      role="status"
      aria-label="Synthetic signal injection accepted"
      className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900"
      data-testid="injection-confirm-card"
    >
      <header className="mb-1 flex items-center gap-2">
        <SimBadge size="sm" />
        <strong className="font-semibold">Telemetry injection accepted</strong>
      </header>
      <dl className="grid grid-cols-[max-content_1fr] gap-x-3 gap-y-0.5 text-[12px]">
        <dt className="text-emerald-700">Signal</dt>
        <dd className="font-mono">{signalId}</dd>
        <dt className="text-emerald-700">Hazard</dt>
        <dd>
          {hazardClass} · {jurisdiction.toUpperCase()} · {severity}
        </dd>
        <dt className="text-emerald-700">Routed to</dt>
        <dd className="font-mono">{routedTo}</dd>
        <dt className="text-emerald-700">Accepted</dt>
        <dd>
          <time dateTime={acceptedAt}>{acceptedAt}</time>
        </dd>
      </dl>
      <footer className="mt-2 flex items-center gap-2">
        <button
          type="button"
          className="rounded bg-emerald-600 px-2 py-0.5 text-[11px] font-medium text-white hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:ring-offset-1"
          onClick={() => onOpenAudit?.(auditEntryId)}
          aria-label={`Open audit envelope ${auditEntryId}`}
        >
          🔗 Audit envelope
        </button>
        <span className="font-mono text-[10px] text-emerald-700">
          {auditEntryId}
        </span>
      </footer>
    </article>
  );
}

export default InjectionConfirmCard;
