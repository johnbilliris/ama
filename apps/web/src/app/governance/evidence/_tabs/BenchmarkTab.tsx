"use client";

import type { BenchmarkEntry } from "@ama/domain";
import { useCallback, useEffect, useState } from "react";
import { getBenchmarks } from "../../../../lib/api/evidence";

const KPI_OPTIONS = [
  ["response_time_p1", "Priority response time"],
  ["fire_structural_response", "Structure fire response"],
  ["ses_flood_response", "SES flood response"],
  ["police_evacuation_clearance", "Police evacuation clearance"],
  ["airservices_arff_response", "Airservices ARFF response"],
  ["saidi", "SAIDI"],
  ["saifi", "SAIFI"],
] as const;
const JURISDICTIONS = ["ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA", "AU"];

export default function BenchmarkTab() {
  const [kpiId, setKpiId] = useState(KPI_OPTIONS[0][0]);
  const [jurisdiction, setJurisdiction] = useState("NSW");
  const [rows, setRows] = useState<BenchmarkEntry[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(
    (signal?: AbortSignal) => {
      setLoading(true);
      setError("");
      void getBenchmarks(kpiId, jurisdiction, signal)
        .then(setRows)
        .catch((reason: unknown) => {
          if ((reason as Error).name !== "AbortError") setError(String(reason));
        })
        .finally(() => setLoading(false));
    },
    [jurisdiction, kpiId],
  );

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);

  return (
    <div data-testid="evidence-benchmarks-tab">
      <div className="mb-4 flex flex-wrap gap-4">
        <label>
          Metric{" "}
          <select value={kpiId} onChange={(event) => setKpiId(event.target.value as typeof kpiId)}>
            {KPI_OPTIONS.map(([id, label]) => (
              <option key={id} value={id}>{label}</option>
            ))}
          </select>
        </label>
        <label>
          Jurisdiction{" "}
          <select value={jurisdiction} onChange={(event) => setJurisdiction(event.target.value)}>
            {JURISDICTIONS.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
      </div>
      {loading ? <p role="status">Loading benchmarks…</p> : null}
      {error ? (
        <div role="alert">
          <p>Failed to load benchmarks: {error}</p>
          <button type="button" onClick={() => load()}>Retry</button>
        </div>
      ) : null}
      {!loading && !error && rows.length === 0 ? (
        <p>No external benchmark is published for this selection.</p>
      ) : null}
      {rows.length > 0 ? (
        <table className="w-full text-sm" aria-label="Benchmark comparison">
          <thead>
            <tr>
              <th>Source</th>
              <th>Comparison</th>
              <th>Value</th>
              <th>Context</th>
              <th>Provenance</th>
              <th>Citation</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                <td>{row.source_name}</td>
                <td>{row.kind === "external_benchmark" ? "External" : "Prototype baseline"}</td>
                <td>{row.not_available ? "Not available" : `${row.target_value} ${row.target_unit}`}</td>
                <td>{row.target_context}</td>
                <td>{row.provenance === "manual" ? <span role="status">manual</span> : "automatic"}</td>
                <td>
                  {row.source_citation ? (
                    <a href={row.source_citation.url} rel="noreferrer">
                      {row.source_citation.organisation}, {row.source_citation.year}
                    </a>
                  ) : "Internal prototype"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </div>
  );
}
