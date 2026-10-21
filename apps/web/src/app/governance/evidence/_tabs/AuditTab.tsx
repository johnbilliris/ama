"use client";

import type { AuditTrace } from "@ama/domain";
import { useCallback, useEffect, useState } from "react";
import { EvidenceApiError, getAuditTrace } from "../../../../lib/api/evidence";

interface AuditTabProps {
  initialValueId?: string;
}

export default function AuditTab({ initialValueId = "" }: AuditTabProps) {
  const [valueId, setValueId] = useState(initialValueId || "demo");
  const [trace, setTrace] = useState<AuditTrace | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (initialValueId) setValueId(initialValueId);
  }, [initialValueId]);

  const load = useCallback(
    (signal?: AbortSignal) => {
      const requested = valueId.trim();
      if (!requested) {
        setTrace(null);
        setError("");
        return;
      }
      setLoading(true);
      setError("");
      void getAuditTrace(requested, signal)
        .then(setTrace)
        .catch((reason: unknown) => {
          if ((reason as Error).name === "AbortError") return;
          if (reason instanceof EvidenceApiError && reason.status === 404) {
            setTrace(null);
            setError("No audit entries exist for this value.");
            return;
          }
          setError(String(reason));
        })
        .finally(() => setLoading(false));
    },
    [valueId],
  );

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);

  return (
    <div data-testid="evidence-audit-tab">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          load();
        }}
      >
        <label>
          Evidence value ID{" "}
          <input
            value={valueId}
            onChange={(event) => setValueId(event.target.value)}
            required
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "Loading…" : "Load trace"}
        </button>
      </form>
      {error ? <p role="alert">{error}</p> : null}
      {trace ? (
        <div>
          <p>
            Chain: {trace.chain_complete ? "complete" : "incomplete"} · Source:{" "}
            {trace.served_from_cold_archive ? "cold archive" : "hot store"}
          </p>
          {!trace.chain_complete ? (
            <p role="status">
              reduced-fidelity · Missing: {(trace.missing_references ?? []).join(", ")}
            </p>
          ) : null}
          <ol aria-label="Audit timeline">
            {trace.entries.map((entry) => (
              <li key={entry.id}>
                <strong>{entry.kind}</strong> by {entry.actor} at{" "}
                <time dateTime={entry.occurred_at}>{entry.occurred_at}</time>
                {" "}({entry.storage_source ?? "hot"})
              </li>
            ))}
          </ol>
        </div>
      ) : null}
    </div>
  );
}
