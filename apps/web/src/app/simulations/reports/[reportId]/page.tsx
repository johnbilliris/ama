"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { SimulationBanner } from "@/components/simulation-banner";

interface ExerciseReportData {
  report_id: string;
  tenant_id: string;
  scenario_type: string;
  generated_at: string;
  participating_organisations: string[];
  participating_personas: string[];
  signal_summary: { total: number; by_category: Record<string, number>; by_source: Record<string, number> };
  recommendation_summary: { total: number; approved: number; rejected: number; pending: number };
  alert_summary: { total: number; published: number; blocked_simulation: number };
  coordination_gaps: string[];
  performance_metrics: { time_to_first_recommendation_s: number | null; time_to_alert_publication_s: number | null; coordination_coverage_pct: number | null };
  benchmark_comparison: { metric: string; target: number; actual: number | null; passed: boolean }[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export default function ExerciseReportPage() {
  const { reportId } = useParams<{ reportId: string }>();
  const [report, setReport] = useState<ExerciseReportData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!reportId) return;
    fetch(`${API_BASE_URL}/simulations/${reportId}/report`)
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status}`);
        return r.json();
      })
      .then(setReport)
      .catch((err) => setError(err.message));
  }, [reportId]);

  if (error) return <div className="p-6 text-red-600">Error: {error}</div>;
  if (!report) return <div className="p-6">Loading exercise report...</div>;

  return (
    <>
      <SimulationBanner />
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
          <SummaryCard title="Recommendations" items={[
            ["Total", report.recommendation_summary.total],
            ["Approved", report.recommendation_summary.approved],
            ["Rejected", report.recommendation_summary.rejected],
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

        {report.benchmark_comparison.length > 0 && (
          <section className="mb-6">
            <h2 className="mb-2 text-lg font-semibold">Benchmark Comparison</h2>
            <table className="w-full table-auto border-collapse text-sm">
              <thead>
                <tr className="border-b text-left">
                  <th className="p-2">Metric</th>
                  <th className="p-2">Target</th>
                  <th className="p-2">Actual</th>
                  <th className="p-2">Result</th>
                </tr>
              </thead>
              <tbody>
                {report.benchmark_comparison.map((b) => (
                  <tr key={b.metric} className="border-b">
                    <td className="p-2">{b.metric}</td>
                    <td className="p-2">{b.target}</td>
                    <td className="p-2">{b.actual ?? "—"}</td>
                    <td className="p-2">{b.passed ? "✓ Pass" : "✗ Fail"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}

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

function SummaryCard({ title, items }: { title: string; items: [string, number][] }) {
  return (
    <div className="rounded border p-4">
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
