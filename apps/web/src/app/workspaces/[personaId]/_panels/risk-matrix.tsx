/**
 * Risk Matrix panel (T039, FR-004).
 *
 * Solicits the `risk-assessment-agent` for the live recommendation matrix.
 * Renders a 5x5 likelihood-by-consequence grid with current scenario placement.
 */

"use client";

import * as React from "react";

const LIKELIHOOD = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"] as const;
const CONSEQUENCE = ["Insignificant", "Minor", "Moderate", "Major", "Catastrophic"] as const;

type Likelihood = (typeof LIKELIHOOD)[number];
type Consequence = (typeof CONSEQUENCE)[number];

interface RiskRecommendation {
  scenario_id: string;
  likelihood: Likelihood;
  consequence: Consequence;
  rationale: string;
  recommended_controls: string[];
}

export interface RiskMatrixProps {
  scenarioId: string;
  endpointBase?: string;
}

const TONE: Record<string, string> = {
  low: "bg-emerald-100 text-emerald-900",
  moderate: "bg-amber-100 text-amber-900",
  high: "bg-orange-200 text-orange-900",
  extreme: "bg-rose-200 text-rose-900",
};

function classify(l: Likelihood, c: Consequence): keyof typeof TONE {
  const li = LIKELIHOOD.indexOf(l);
  const ci = CONSEQUENCE.indexOf(c);
  const score = li + ci;
  if (score <= 2) return "low";
  if (score <= 4) return "moderate";
  if (score <= 6) return "high";
  return "extreme";
}

export function RiskMatrix(props: RiskMatrixProps): React.ReactElement {
  const { scenarioId, endpointBase = "/api" } = props;
  const [rec, setRec] = React.useState<RiskRecommendation | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [err, setErr] = React.useState<string | null>(null);

  React.useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    fetch(
      `${endpointBase}/agents/risk-assessment/recommend?scenario_id=${encodeURIComponent(scenarioId)}`,
      { signal: ctrl.signal },
    )
      .then((r) => {
        if (!r.ok) throw new Error(`risk-fetch-failed:${r.status}`);
        return r.json();
      })
      .then((j: RiskRecommendation) => setRec(j))
      .catch((e) => {
        if ((e as { name?: string }).name !== "AbortError") {
          setErr(e instanceof Error ? e.message : String(e));
        }
      })
      .finally(() => setLoading(false));
    return () => ctrl.abort();
  }, [scenarioId, endpointBase]);

  return (
    <section
      className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
      data-testid="risk-matrix"
    >
      <header className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Risk matrix</h2>
        <span className="text-xs text-slate-500">FR-004</span>
      </header>
      {loading ? <p>Loading recommendation…</p> : null}
      {err ? <p role="alert" className="text-rose-700">{err}</p> : null}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr>
              <th className="border border-slate-200 p-1"></th>
              {CONSEQUENCE.map((c) => (
                <th key={c} className="border border-slate-200 p-1">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {LIKELIHOOD.map((l) => (
              <tr key={l}>
                <th className="border border-slate-200 p-1 text-left">{l}</th>
                {CONSEQUENCE.map((c) => {
                  const here = rec?.likelihood === l && rec?.consequence === c;
                  const tone = TONE[classify(l, c)];
                  return (
                    <td
                      key={c}
                      className={`border border-slate-200 p-1 text-center ${tone}`}
                    >
                      {here ? (
                        <span data-testid="risk-matrix-current">●</span>
                      ) : (
                        ""
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rec ? (
        <div className="mt-3 text-sm">
          <p>{rec.rationale}</p>
          <ul className="ml-5 list-disc">
            {rec.recommended_controls.map((ctl, i) => (
              <li key={i}>{ctl}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

export default RiskMatrix;
