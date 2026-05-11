/**
 * Classifier-mask banner (T046, FR-027 / Q6).
 *
 * Renders the **"this content was masked before processing"** message with:
 * - the masked-field count,
 * - a link to the audit-row detail (`/governance/audit/{auditId}`),
 *
 * when `outcome === "classifier_mask"`. Suppressed otherwise.
 *
 * See [`classifier-gateway.contract.md`](../../../../specs/035-webapp-capstone-closure/contracts/classifier-gateway.contract.md).
 */

import * as React from "react";

export type ClassifierOutcome =
  | "classifier_mask"
  | "classifier_deny"
  | "classifier_failed"
  | "clean";

export interface ClassifierBannerProps {
  outcome: ClassifierOutcome;
  maskedFieldCount?: number;
  auditId?: string;
  /**
   * Override the audit-row URL. Defaults to `/governance/audit/{auditId}`.
   */
  auditUrlBase?: string;
}

export function ClassifierBanner(props: ClassifierBannerProps): React.ReactElement | null {
  const { outcome, maskedFieldCount, auditId, auditUrlBase } = props;
  if (outcome !== "classifier_mask") return null;
  const base = auditUrlBase ?? "/governance/audit";
  const auditHref = auditId ? `${base}/${encodeURIComponent(auditId)}` : null;
  const count = maskedFieldCount ?? 0;
  return (
    <div
      role="status"
      aria-live="polite"
      data-testid="classifier-mask-banner"
      className="rounded-md border border-amber-300 bg-amber-50 p-3 text-amber-900"
    >
      <p className="font-medium">
        This content was masked before processing.
      </p>
      <p className="text-sm">
        <span data-testid="classifier-mask-count">
          {count} field{count === 1 ? "" : "s"}
        </span>{" "}
        masked.
        {auditHref ? (
          <>
            {" "}
            <a
              data-testid="classifier-mask-audit-link"
              href={auditHref}
              className="underline"
            >
              View audit record
            </a>
            .
          </>
        ) : null}
      </p>
    </div>
  );
}

export default ClassifierBanner;
