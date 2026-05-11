/**
 * Spec-038 Replay Scorecard tab — live fetch (T-AMD-15).
 * Fetches replays from POST /api/v1/evidence/scenarios/{scenario_id}/replay on mount.
 */
"use client";
import { useEffect, useState } from "react";

const DEFAULT_SCENARIO = "bushfire";

export default function ReplayTab() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [degraded, setDegraded] = useState(false);
  const [smallSample, setSmallSample] = useState(false);

  useEffect(() => {
    fetch(`/api/v1/evidence/scenarios/${DEFAULT_SCENARIO}/replay`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ seed: "default", run_pair_id: "init", repetitions: 2, allow_degraded_mode: true }),
    })
      .then((r) => {
        if (!r.ok) { setError(`HTTP ${r.status}`); return null; }
        return r.json();
      })
      .then((d) => {
        if (!d) return;
        setData(d);
        if (d.reduced_fidelity) setDegraded(true);
        if (Array.isArray(d.kpi_deltas) && d.kpi_deltas.some((k: { small_sample?: boolean }) => k.small_sample)) setSmallSample(true);
      })
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div data-testid="evidence-replay-tab">
      {degraded && <span className="inline-flex items-center rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-800" role="status">degraded</span>}
      {smallSample && <span className="ml-1 inline-flex items-center rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-800" role="status">small-sample</span>}
      {error && <p role="alert" className="text-red-600">Failed to load: {error}</p>}
      {!data && !error && <p>Loading Replay Scorecard…</p>}
      {data && <pre className="whitespace-pre-wrap text-sm">{JSON.stringify(data, null, 2)}</pre>}
    </div>
  );
}
