/**
 * Resilience handover PDF panel (T044, FR-007).
 *
 * Calls `POST /api/recovery/handover/sign`, downloads the SAS-protected PDF,
 * links the audit row. On a `422 signing_key_expired` envelope, surfaces a
 * non-silent banner naming the next-rotation ETA and links to the
 * App-Configuration-resolved key-rotation runbook URL.
 */

"use client";

import * as React from "react";

interface HandoverEnvelope {
  pdf_url: string;
  sas_expiry: string;
  audit_id: string;
  signed_at: string;
}

interface ErrorEnvelope {
  error_code: string;
  audit_id?: string;
  correlation_id?: string;
  detail?: string;
  retry_after_seconds?: number | null;
}

export interface ResilienceHandoverPdfProps {
  endpointBase?: string;
  payloadFactory: () => Record<string, unknown>;
  /**
   * App-Configuration resolved value for `recovery-handover:keyRotationRunbookUrl`.
   * Surfaced via NEXT_PUBLIC_RECOVERY_HANDOVER_RUNBOOK_URL or prop override.
   */
  rotationRunbookUrl?: string;
}

const DEFAULT_RUNBOOK_URL =
  typeof process !== "undefined" && process.env
    ? process.env.NEXT_PUBLIC_RECOVERY_HANDOVER_RUNBOOK_URL ?? ""
    : "";

export function ResilienceHandoverPdf(
  props: ResilienceHandoverPdfProps,
): React.ReactElement {
  const {
    endpointBase = "/api",
    payloadFactory,
    rotationRunbookUrl = DEFAULT_RUNBOOK_URL,
  } = props;
  const [pending, setPending] = React.useState(false);
  const [success, setSuccess] = React.useState<HandoverEnvelope | null>(null);
  const [signingKeyExpired, setSigningKeyExpired] =
    React.useState<{ rotationEta?: string; auditId?: string } | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const sign = async () => {
    setPending(true);
    setError(null);
    setSigningKeyExpired(null);
    try {
      const res = await fetch(`${endpointBase}/recovery/handover/sign`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payloadFactory()),
      });
      if (res.status === 422) {
        const env = (await res.json()) as ErrorEnvelope;
        if (
          env.error_code === "schema_invalid" &&
          typeof env.detail === "string" &&
          env.detail.startsWith("signing_key_expired")
        ) {
          const etaMatch = env.detail.match(/next_rotation_eta=([^\s;]+)/);
          setSigningKeyExpired({
            rotationEta: etaMatch?.[1],
            auditId: env.audit_id,
          });
          return;
        }
        setError(env.detail ?? `validation-failed:${env.error_code}`);
        return;
      }
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(
          (body as ErrorEnvelope | null)?.detail ?? `sign-failed:${res.status}`,
        );
      }
      const env = (await res.json()) as HandoverEnvelope;
      setSuccess(env);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setPending(false);
    }
  };

  return (
    <section
      className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
      data-testid="resilience-handover-pdf"
    >
      <header className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Resilience handover PDF</h2>
        <span className="text-xs text-slate-500">FR-007</span>
      </header>
      <button
        type="button"
        disabled={pending}
        onClick={sign}
        className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
      >
        {pending ? "Signing…" : "Sign handover & generate PDF"}
      </button>
      {success ? (
        <div className="mt-3 rounded-md border border-emerald-300 bg-emerald-50 p-2 text-sm">
          <p>
            Handover signed at{" "}
            <span className="font-mono">{success.signed_at}</span>.
          </p>
          <p>
            <a className="underline" href={success.pdf_url}>
              Download SAS-protected PDF
            </a>{" "}
            (expires {success.sas_expiry}). Audit:{" "}
            <a
              className="underline"
              href={`/governance/audit/${encodeURIComponent(success.audit_id)}`}
            >
              {success.audit_id}
            </a>
          </p>
        </div>
      ) : null}
      {signingKeyExpired ? (
        <div
          role="alert"
          aria-live="assertive"
          data-testid="signing-key-expired-banner"
          className="mt-3 rounded-md border border-rose-300 bg-rose-50 p-2 text-sm text-rose-900"
        >
          <p className="font-semibold">
            Signing key expired — re-issue blocked.
          </p>
          {signingKeyExpired.rotationEta ? (
            <p>
              Next rotation ETA:{" "}
              <span className="font-mono">{signingKeyExpired.rotationEta}</span>
            </p>
          ) : null}
          {rotationRunbookUrl ? (
            <p>
              Runbook:{" "}
              <a className="underline" href={rotationRunbookUrl}>
                key-rotation runbook
              </a>
            </p>
          ) : (
            <p className="text-xs">
              (Set
              <code className="mx-1">NEXT_PUBLIC_RECOVERY_HANDOVER_RUNBOOK_URL</code>
              to surface the runbook link.)
            </p>
          )}
          {signingKeyExpired.auditId ? (
            <p>
              Audit:{" "}
              <a
                className="underline"
                href={`/governance/audit/${encodeURIComponent(signingKeyExpired.auditId)}`}
              >
                {signingKeyExpired.auditId}
              </a>
            </p>
          ) : null}
        </div>
      ) : null}
      {error ? (
        <p role="alert" className="mt-2 text-sm text-rose-700">
          {error}
        </p>
      ) : null}
    </section>
  );
}

export default ResilienceHandoverPdf;
