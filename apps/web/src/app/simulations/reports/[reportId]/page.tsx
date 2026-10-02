"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useReportSimulationLifecycle } from "@/components/simulation-lifecycle";
import { getReportById, SimulationApiError, type ExerciseReportData } from "@/lib/api/simulations";

type ReportError = { status: number; message: string };

/**
 * AUD-021 — a deep link must say which of the three outcomes occurred:
 * denied (403), no such report (404), or generation still pending
 * (404/409 while the exercise has not produced one yet).
 */
function errorView({ status, message }: ReportError) {
  if (status === 403) {
    return {
      testId: "report-error-forbidden",
      title: "Not authorised for this exercise report",
      detail: "Your account is not a participant in the exercise that owns this report.",
    };
  }
  if (status === 409 || status === 202) {
    return {
      testId: "report-error-pending",
      title: "Exercise report not ready",
      detail: "The exercise is still running. The report is generated when it is archived.",
    };
  }
  if (status === 404) {
    return {
      testId: "report-error-not-found",
      title: "Exercise report not found",
      detail:
        "No report exists for this identifier. It may not have been generated yet, or the link is wrong.",
    };
  }
  return {
    testId: "report-error-unknown",
    title: "Could not load the exercise report",
    detail: message,
  };
}

export default function ExerciseReportPage() {
  const { reportId } = useParams<{ reportId: string }>();
  const [report, setReport] = useState<ExerciseReportData | null>(null);
  const [error, setError] = useState<ReportError | null>(null);

  useEffect(() => {
    if (!reportId) return;
    getReportById(reportId)
      .then(setReport)
      .catch((err) =>
        setError(
          err instanceof SimulationApiError
            ? { status: err.status, message: err.message }
            : { status: 0, message: err instanceof Error ? err.message : String(err) },
        ),
      );
  }, [reportId]);

  // AUD-018 — a generated exercise report is by definition a completed run;
  // publish it so the layout marker stops showing "Status pending".
  useReportSimulationLifecycle(report ? "Completed" : null);

  if (error) {
    const view = errorView(error);
    return (
      <div className="mx-auto max-w-2xl p-6" role="alert" data-testid={view.testId}>
        <h1 className="mb-2 text-2xl font-bold">{view.title}</h1>
        <p className="mb-2 text-sm text-gray-600">{view.detail}</p>
        <p className="text-xs text-gray-500">{error.message}</p>
      </div>
    );
  }
  if (!report) return <div className="p-6">Loading exercise report...</div>;

  return (
    <>
      <div className="mx-auto max-w-5xl p-6">
        <h1 className="mb-2 text-2xl font-bold">Exercise Report</h1>
        <p className="mb-6 text-sm text-gray-500">
          Report: {report.report_id} | Scenario: {report.scenario_type} | Generated:{" "}
          {new Date(report.generated_at).toLocaleString()}
        </p>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold">Participants</h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <h3 className="font-medium">Organisations</h3>
              <ul className="list-inside list-disc">
                {report.participating_organisations.length > 0
                  ? report.participating_organisations.map((o) => <li key={o}>{o}</li>)
                  : <li className="text-gray-400">None recorded</li>}
              </ul>
            </div>
            <div>
              <h3 className="font-medium">Personas</h3>
              <ul className="list-inside list-disc">
                {report.participating_personas.map((p) => <li key={p}>{p}</li>)}
              </ul>
            </div>
          </div>
        </section>

        <section className="mb-6 grid grid-cols-3 gap-4">
          <SummaryCard title="Signals" items={[
            ["Total", report.signal_summary.total],
            ...Object.entries(report.signal_summary.by_category),
          ]} />
          <SummaryCard title="Recommendations" testId="report-recommendation-summary" items={[
            ["Total", report.recommendation_summary.total],
            ["Approved", report.recommendation_summary.approved],
            ["Rejected", report.recommendation_summary.rejected],
            ["Escalated", report.recommendation_summary.escalated],
            ["Timed out", report.recommendation_summary.timed_out],
            ["Pending", report.recommendation_summary.pending],
          ]} />
          <SummaryCard title="Alerts" items={[
            ["Total", report.alert_summary.total],
            ["Published", report.alert_summary.published],
            ["Blocked (sim)", report.alert_summary.blocked_simulation],
          ]} />
        </section>

        {report.coordination_gaps.length > 0 && (
          <section className="mb-6">
            <h2 className="mb-2 text-lg font-semibold">Coordination Gaps</h2>
            <ul className="list-inside list-disc text-sm">
              {report.coordination_gaps.map((gap, i) => <li key={i}>{gap}</li>)}
            </ul>
          </section>
        )}

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold">Exercise Timeline</h2>
          {report.exercise_timeline.length === 0 ? (
            <p className="text-sm text-gray-500">No timeline events recorded.</p>
          ) : (
            <ol className="space-y-2 text-sm">
              {report.exercise_timeline.map((event, index) => (
                <li key={`${event.wall_clock_time}-${index}`} className="border-l-2 border-gray-300 pl-3">
                  <strong>{event.event_type.replaceAll("_", " ")}</strong>{" "}
                  <time>{new Date(event.wall_clock_time).toLocaleString()}</time>
                </li>
              ))}
            </ol>
          )}
        </section>

        <section className="mb-6" data-testid="report-benchmark-comparison">
          <h2 className="mb-2 text-lg font-semibold">Benchmark Comparison</h2>
          {report.benchmark_comparison.length === 0 ? (
            <p className="text-sm text-gray-500">No benchmark targets recorded for this exercise.</p>
          ) : (
            <table className="w-full table-auto border-collapse text-sm">
              <thead>
                <tr className="border-b text-left">
                  <th className="p-2">Metric</th>
                  <th className="p-2">Target</th>
                  <th className="p-2">Actual</th>
                  <th className="p-2">Prior</th>
                  <th className="p-2">Change</th>
                  <th className="p-2">Result</th>
                </tr>
              </thead>
              <tbody>
                {report.benchmark_comparison.map((b) => (
                  <tr key={b.metric} className="border-b">
                    <td className="p-2">{b.metric}</td>
                    <td className="p-2">{b.target}</td>
                    <td className="p-2">{b.actual ?? "—"}</td>
                    <td className="p-2">{b.prior_actual ?? "No prior exercise"}</td>
                    <td className="p-2">{b.delta_from_prior ?? "—"}</td>
                    <td className="p-2">{b.passed ? "✓ Pass" : "✗ Fail"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section>
          <h2 className="mb-2 text-lg font-semibold">Performance Metrics</h2>
          <dl className="grid grid-cols-3 gap-4 text-sm">
            <div className="rounded border p-3">
              <dt className="text-xs text-gray-500">Time to First Recommendation</dt>
              <dd className="text-lg font-bold">
                {report.performance_metrics.time_to_first_recommendation_s != null
                  ? `${report.performance_metrics.time_to_first_recommendation_s}s`
                  : "—"}
              </dd>
            </div>
            <div className="rounded border p-3">
              <dt className="text-xs text-gray-500">Time to Alert Publication</dt>
              <dd className="text-lg font-bold">
                {report.performance_metrics.time_to_alert_publication_s != null
                  ? `${report.performance_metrics.time_to_alert_publication_s}s`
                  : "—"}
              </dd>
            </div>
            <div className="rounded border p-3">
              <dt className="text-xs text-gray-500">Coordination Coverage</dt>
              <dd className="text-lg font-bold">
                {report.performance_metrics.coordination_coverage_pct != null
                  ? `${report.performance_metrics.coordination_coverage_pct}%`
                  : "—"}
              </dd>
            </div>
          </dl>
        </section>
      </div>
    </>
  );
}

function SummaryCard({
  title,
  items,
  testId,
}: {
  title: string;
  items: [string, number][];
  testId?: string;
}) {
  return (
    <div className="rounded border p-4" data-testid={testId}>
      <h3 className="mb-2 font-semibold">{title}</h3>
      <dl className="space-y-1 text-sm">
        {items.map(([label, value]) => (
          <div key={label} className="flex justify-between">
            <dt>{label}</dt>
            <dd className="font-medium">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
