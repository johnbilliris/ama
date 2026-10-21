"use client";

import type { IndicatorDefinition, KpiLadderView } from "@ama/domain";
import { useCallback, useEffect, useState } from "react";
import { getKpiLadder } from "../../../../lib/api/evidence";

const CAPSTONE_OPTIONS = [
  ["", "All capstone criteria"],
  ["SC-CAP-015-001", "Lives saved"],
  ["SC-CAP-015-002", "Response time"],
  ["SC-CAP-015-003", "Evacuation lead time"],
  ["SC-CAP-015-004", "Logistics efficiency"],
  ["SC-CAP-015-005", "Economic loss reduction"],
] as const;

function riskAdjusted(value: number, indicator: IndicatorDefinition): number {
  const risk = indicator.risk_adjustment;
  if (!risk) return value;
  const { likelihood, consequence } = risk;
  return value * ((likelihood * consequence) / 25);
}

export default function KpiLadderTab() {
  const [data, setData] = useState<KpiLadderView | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [includeRiskAdjusted, setIncludeRiskAdjusted] = useState(true);
  const [capstoneScId, setCapstoneScId] = useState("");

  const load = useCallback(
    (signal?: AbortSignal) => {
      setLoading(true);
      setError("");
      void getKpiLadder(
        includeRiskAdjusted,
        capstoneScId || null,
        signal,
      )
        .then(setData)
        .catch((reason: unknown) => {
          if ((reason as Error).name !== "AbortError") setError(String(reason));
        })
        .finally(() => setLoading(false));
    },
    [capstoneScId, includeRiskAdjusted],
  );

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const indicators = data?.groups.flatMap((group) => [
    ...group.leading,
    ...group.lagging,
  ]) ?? [];

  return (
    <div data-testid="evidence-kpi-ladder-tab">
      <div className="mb-4 flex flex-wrap gap-4">
        <label>
          Criterion{" "}
          <select
            value={capstoneScId}
            onChange={(event) => setCapstoneScId(event.target.value)}
          >
            {CAPSTONE_OPTIONS.map(([value, label]) => (
              <option key={value || "all"} value={value}>{label}</option>
            ))}
          </select>
        </label>
        <label>
          <input
            type="checkbox"
            checked={includeRiskAdjusted}
            onChange={(event) => setIncludeRiskAdjusted(event.target.checked)}
          />{" "}
          Show risk-adjusted values
        </label>
      </div>
      {loading ? <p role="status">Loading KPI ladder…</p> : null}
      {error ? (
        <div role="alert">
          <p>Failed to load the KPI ladder: {error}</p>
          <button type="button" onClick={() => load()}>Retry</button>
        </div>
      ) : null}
      {!loading && !error && indicators.length === 0 ? (
        <p>No published indicators match this criterion.</p>
      ) : null}
      {indicators.length > 0 ? (
        <div className="overflow-x-auto">
          <table aria-label="KPI ladder" className="w-full text-sm">
            <thead>
              <tr>
                <th>KPI</th>
                <th>Kind</th>
                <th>Formula</th>
                <th>Unit</th>
                <th>Owner</th>
                <th>Cadence</th>
                <th>Target</th>
                <th>Alert</th>
                <th>Baseline</th>
                <th>Provenance</th>
                <th>Confidence rule</th>
                <th>Risk-adjusted target</th>
              </tr>
            </thead>
            <tbody>
              {indicators.map((indicator) => {
                const target = Number(indicator.target_value);
                return (
                  <tr key={indicator.id}>
                    <td>{indicator.name}</td>
                    <td>{indicator.kind}</td>
                    <td>{indicator.formula}</td>
                    <td>{indicator.unit}</td>
                    <td>{indicator.owner_role}</td>
                    <td>{indicator.refresh_cadence}</td>
                    <td>{target}</td>
                    <td>{Number(indicator.alert_threshold)}</td>
                    <td>{indicator.baseline_source}</td>
                    <td>
                      {indicator.provenance}
                      {indicator.risk_adjustment?.provenance === "manual" ? (
                        <span role="status" className="ml-1">manual</span>
                      ) : null}
                    </td>
                    <td>
                      {indicator.confidence_band_rule.method} ·{" "}
                      {indicator.confidence_band_rule.min_resamples}
                    </td>
                    <td>
                      {includeRiskAdjusted
                        ? riskAdjusted(target, indicator).toFixed(2)
                        : "Hidden"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
