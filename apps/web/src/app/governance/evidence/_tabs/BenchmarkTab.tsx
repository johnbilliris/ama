/**
 * Spec-038 Benchmarks tab — live fetch (T-AMD-15).
 * Fetches from GET /api/v1/evidence/benchmarks/{kpi_id}?jurisdiction=NSW on mount.
 */
"use client";
import { useEffect, useState } from "react";

const DEFAULT_KPI = "response_time_p1";
const DEFAULT_JURISDICTION = "NSW";

interface BenchmarkRow {
  id: string;
  kind: "external_benchmark" | "prototype_baseline";
  source_name: string;
  target_value: number | null;
  target_unit: string;
  not_available: boolean;
  provenance: "auto" | "manual";
}

export default function BenchmarkTab() {
  const [rows, setRows] = useState<BenchmarkRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [jurisdiction, setJurisdiction] = useState(DEFAULT_JURISDICTION);

  useEffect(() => {
    fetch(`/api/v1/evidence/benchmarks/${DEFAULT_KPI}?jurisdiction=${jurisdiction}`)
      .then((r) => {
        if (!r.ok) { setError(`HTTP ${r.status}`); return null; }
        return r.json();
      })
      .then((d) => d && setRows(Array.isArray(d) ? d : d.entries ?? []))
      .catch((e) => setError(String(e)));
  }, [jurisdiction]);

  return (
    <div data-testid="evidence-benchmarks-tab">
      <label className="mr-2 text-sm font-medium">Jurisdiction:
        <select className="ml-1 border rounded px-1" value={jurisdiction} onChange={(e) => setJurisdiction(e.target.value)}>
          {["NSW","VIC","QLD","SA","WA","ACT","NT","TAS","AU"].map((j) => (
            <option key={j} value={j}>{j}</option>
          ))}
        </select>
      </label>
      {error && <p role="alert" className="text-red-600">Failed to load: {error}</p>}
      {rows.length === 0 && !error && <p>Loading Benchmarks…</p>}
      {rows.length > 0 && (
        <table className="w-full text-sm" aria-label="Benchmarks">
          <thead>
            <tr><th>Source</th><th>Kind</th><th>Target</th><th>Unit</th><th>Status</th></tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className={r.kind === "external_benchmark" ? "" : "bg-gray-50"}>
                <td>{r.source_name}</td>
                <td>{r.kind === "external_benchmark" ? "External" : "Prototype baseline"}</td>
                <td>{r.not_available ? "—" : String(r.target_value ?? "—")}</td>
                <td>{r.target_unit}</td>
                <td>
                  {r.not_available && <span className="text-gray-500 text-xs">not available</span>}
                  {r.provenance === "manual" && (
                    <span className="ml-1 inline-flex items-center rounded-full bg-purple-100 px-1.5 py-0.5 text-xs font-medium text-purple-800">manual</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
