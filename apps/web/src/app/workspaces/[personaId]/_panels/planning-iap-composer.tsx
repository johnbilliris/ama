/**
 * Planning IAP Composer panel (T042, FR-005).
 *
 * Solicits the `planning-agent` for forecast + IAP draft inputs.
 */

"use client";

import * as React from "react";

interface PlanningDraft {
  iap_draft_markdown: string;
  forecast: {
    horizon_hours: number;
    confidence: number;
    bullets: string[];
  };
  span_of_control_warning?: { direct_reports: number; threshold: number };
}

export interface PlanningIapComposerProps {
  scenarioId: string;
  endpointBase?: string;
}

export function PlanningIapComposer(
  props: PlanningIapComposerProps,
): React.ReactElement {
  const { scenarioId, endpointBase = "/api" } = props;
  const [draft, setDraft] = React.useState<PlanningDraft | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [err, setErr] = React.useState<string | null>(null);

  const requestDraft = async () => {
    setLoading(true);
    setErr(null);
    try {
      const res = await fetch(
        `${endpointBase}/agents/planning/draft-iap?scenario_id=${encodeURIComponent(scenarioId)}`,
      );
      if (!res.ok) throw new Error(`planning-failed:${res.status}`);
      setDraft((await res.json()) as PlanningDraft);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section
      className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
      data-testid="planning-iap-composer"
    >
      <header className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Planning — IAP composer</h2>
        <span className="text-xs text-slate-500">FR-005</span>
      </header>
      <button
        type="button"
        disabled={loading}
        onClick={requestDraft}
        className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
      >
        {loading ? "Drafting…" : "Request IAP draft"}
      </button>
      {err ? (
        <p role="alert" className="mt-2 text-sm text-rose-700">
          {err}
        </p>
      ) : null}
      {draft ? (
        <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
          <article>
            <h3 className="text-sm font-semibold">Forecast</h3>
            <p className="text-xs text-slate-500">
              {draft.forecast.horizon_hours}h horizon · confidence{" "}
              {(draft.forecast.confidence * 100).toFixed(0)}%
            </p>
            <ul className="ml-5 list-disc text-sm">
              {draft.forecast.bullets.map((b, i) => (
                <li key={i}>{b}</li>
              ))}
            </ul>
          </article>
          <article>
            <h3 className="text-sm font-semibold">IAP draft</h3>
            <pre className="whitespace-pre-wrap rounded-md bg-slate-50 p-2 text-xs">
              {draft.iap_draft_markdown}
            </pre>
            {draft.span_of_control_warning ? (
              <p className="mt-2 text-sm text-amber-800">
                Span-of-control warning: {draft.span_of_control_warning.direct_reports}
                /{draft.span_of_control_warning.threshold} direct reports.
              </p>
            ) : null}
          </article>
        </div>
      ) : null}
    </section>
  );
}

export default PlanningIapComposer;
