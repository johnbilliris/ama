/**
 * Spec-038 Impact Chains tab — live fetch (T-AMD-15).
 * Fetches from GET /api/v1/evidence/causal-chains/{capability_id} on mount.
 */
"use client";
import { useEffect, useState } from "react";

const DEFAULT_CAPABILITY = "spec-008";

export default function ImpactTab() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/v1/evidence/causal-chains/${DEFAULT_CAPABILITY}`)
      .then((r) => {
        if (!r.ok) { setError(`HTTP ${r.status}`); return null; }
        return r.json();
      })
      .then((d) => d && setData(d))
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div data-testid="evidence-impact-tab">
      {error && <p role="alert" className="text-red-600">Failed to load: {error}</p>}
      {!data && !error && <p>Loading Impact Chains…</p>}
      {data && (
        <div>
          <h3>{String(data.capability_name ?? data.capability_id ?? "")}</h3>
          {Array.isArray(data.assumptions) && data.assumptions.some((a: { resolved: boolean }) => !a.resolved) && (
            <span className="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800" role="status">
              unresolved assumptions
            </span>
          )}
          <pre className="whitespace-pre-wrap text-sm">{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
