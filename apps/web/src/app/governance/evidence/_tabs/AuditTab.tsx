/**
 * Spec-038 Audit Trace tab — live fetch (T-AMD-15).
 * Fetches from GET /api/v1/evidence/audit/{value_id} on mount.
 */
"use client";
import { useEffect, useState } from "react";

const DEFAULT_VALUE_ID = "demo";

export default function AuditTab() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/v1/evidence/audit/${DEFAULT_VALUE_ID}`)
      .then((r) => {
        if (r.status === 404) { setError("No audit entries for this value"); return null; }
        if (!r.ok) { setError(`HTTP ${r.status}`); return null; }
        return r.json();
      })
      .then((d) => d && setData(d))
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div data-testid="evidence-audit-tab">
      {error && <p role="alert" className="text-gray-500 text-sm">{error}</p>}
      {!data && !error && <p>Loading Audit Trace…</p>}
      {data && (
        <div>
          {!(data.chain_complete as boolean) && (
            <span className="inline-flex items-center rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-800" role="status">
              reduced-fidelity
            </span>
          )}
          <pre className="whitespace-pre-wrap text-sm mt-2">{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
