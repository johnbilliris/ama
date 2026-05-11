/**
 * Spec-038 KPI Ladder tab — live fetch + risk-adjusted side-by-side (T-AMD-15, T-AMD-16).
 *
 * Fetches from GET /api/v1/evidence/kpi-ladder on mount.
 * Renders Raw / Risk-adjusted (L×C) columns side-by-side per FR-041.
 * Shows provenance chip + ManualSignoffBadge when auditor_signoff_required=true.
 */
"use client";
import { useEffect, useState } from "react";
import PublicInformationChannels from "./PublicInformationChannels";

interface RiskAdjustment {
  likelihood: number;
  consequence: number;
  provenance: "auto" | "manual";
  auditor_signoff_required: boolean;
}

interface IndicatorDefinition {
  id: string;
  kpi_id: string;
  name: string;
  kind: "leading" | "lagging";
  target_value: number;
  unit: string;
  risk_adjustment: RiskAdjustment;
  provenance: string;
  life_safety_tier: string;
}

type Badge = "degraded" | "small-sample" | "manual" | "reduced-fidelity";

function StateBadge({ badge }: { badge: Badge }) {
  const styles: Record<Badge, string> = {
    degraded: "bg-orange-100 text-orange-800",
    "small-sample": "bg-yellow-100 text-yellow-800",
    manual: "bg-purple-100 text-purple-800",
    "reduced-fidelity": "bg-gray-200 text-gray-700",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${styles[badge]}`}
      role="status"
    >
      {badge}
    </span>
  );
}

function riskAdjusted(value: number, ra: RiskAdjustment): number {
  return value * ((ra.likelihood * ra.consequence) / 25);
}

export default function KpiLadderTab() {
  const [data, setData] = useState<{ groups: { leading: IndicatorDefinition[]; lagging: IndicatorDefinition[] }[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [degraded, setDegraded] = useState(false);

  useEffect(() => {
    fetch("/api/v1/evidence/kpi-ladder")
      .then((r) => {
        if (!r.ok) { setError(`HTTP ${r.status}`); return null; }
        if (r.headers.get("x-ama-degraded") === "true") setDegraded(true);
        return r.json();
      })
      .then((d) => d && setData(d))
      .catch((e) => setError(String(e)));
  }, []);

  const allIndicators: IndicatorDefinition[] = data
    ? data.groups.flatMap((g) => [...g.leading, ...g.lagging])
    : [];

  return (
    <div data-testid="evidence-kpi-ladder-tab">
      {degraded && <StateBadge badge="degraded" />}
      {error && <p role="alert" className="text-red-600">Failed to load: {error}</p>}
      {!data && !error && <p>Loading KPI Ladder…</p>}
      {data && (
        <table aria-label="KPI Ladder" className="w-full text-sm">
          <thead>
            <tr>
              <th>KPI</th><th>Kind</th><th>Unit</th>
              <th>Raw target</th>
              <th>Risk-adjusted (L×C)</th>
              <th>Provenance</th>
              <th>Life-safety tier</th>
            </tr>
          </thead>
          <tbody>
            {allIndicators.map((ind) => (
              <tr key={ind.id}>
                <td>{ind.name}</td>
                <td>{ind.kind}</td>
                <td>{ind.unit}</td>
                <td>{ind.target_value}</td>
                <td>
                  {riskAdjusted(ind.target_value, ind.risk_adjustment).toFixed(2)}
                  {" "}
                  <span className="text-xs text-gray-500">
                    (L={ind.risk_adjustment.likelihood}×C={ind.risk_adjustment.consequence})
                  </span>
                </td>
                <td>
                  {ind.risk_adjustment.provenance === "manual" && (
                    <StateBadge badge="manual" />
                  )}
                  {ind.risk_adjustment.auditor_signoff_required && (
                    <span className="ml-1 text-xs text-purple-700" aria-label="Manual signoff required">
                      ⚠ signoff required
                    </span>
                  )}
                </td>
                <td>{ind.life_safety_tier}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <PublicInformationChannels jurisdiction="AU" />
    </div>
  );
}

