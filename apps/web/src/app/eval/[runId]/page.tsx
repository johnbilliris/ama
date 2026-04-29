import { headers } from "next/headers";
import Link from "next/link";

interface MetricResult {
  metricId: string;
  mean: number;
  passRate?: number;
  n?: number;
  ci95Lower?: number;
  ci95Upper?: number;
  regression?: number;
  failureExemplars?: string[];
}

interface ScorecardWinner {
  perMetric: Record<string, string>;
  overall: string;
  tieBreakReason?: string;
}

interface Scorecard {
  runId: string;
  perModel: Record<string, Record<string, MetricResult>>;
  winner: ScorecardWinner;
  generatedAt: string;
}

async function fetchScorecard(runId: string): Promise<Scorecard | null> {
  const h = await headers();
  const proto = h.get("x-forwarded-proto") ?? "http";
  const host = h.get("host") ?? "localhost:3000";
  try {
    const res = await fetch(`${proto}://${host}/api/eval/runs/${runId}/scorecard`, {
      cache: "no-store",
      headers: { "x-eval-roles": "Eval.Viewer" },
    });
    if (!res.ok) return null;
    return (await res.json()) as Scorecard;
  } catch {
    return null;
  }
}

function formatPercent(v: number | undefined): string {
  if (v === undefined || v === null) return "—";
  return `${(v * 100).toFixed(1)}%`;
}

export default async function ScorecardPage({ params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  const sc = await fetchScorecard(runId);

  if (!sc) {
    return (
      <main className="p-8 max-w-5xl mx-auto">
        <Link className="text-blue-700 underline" href="/eval">← Back to runs</Link>
        <h1 className="text-2xl font-bold mt-4">Scorecard not found</h1>
        <p className="text-slate-600 mt-2">Run <code>{runId}</code> has no scorecard yet.</p>
      </main>
    );
  }

  const models = Object.keys(sc.perModel);
  const allMetrics = Array.from(
    new Set(models.flatMap((m) => Object.keys(sc.perModel[m]))),
  ).sort();

  return (
    <main className="p-8 max-w-7xl mx-auto">
      <Link className="text-blue-700 underline" href="/eval">← Back to runs</Link>
      <h1 className="text-2xl font-bold mt-4">Run {runId}</h1>
      <p className="text-sm text-slate-600 mt-1">
        Overall winner: <span className="font-semibold">{sc.winner.overall}</span>
      </p>

      <section className="mt-6">
        <h2 className="text-lg font-semibold mb-3">Per-metric scoreboard</h2>
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-2 text-left font-semibold">Metric</th>
                {models.map((m) => (
                  <th key={m} className="px-4 py-2 text-left font-semibold font-mono text-xs">{m}</th>
                ))}
                <th className="px-4 py-2 text-left font-semibold">Winner</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {allMetrics.map((metric) => (
                <tr key={metric}>
                  <td className="px-4 py-2 font-mono text-xs">{metric}</td>
                  {models.map((m) => {
                    const r = sc.perModel[m][metric];
                    const isWinner = sc.winner.perMetric[metric] === m;
                    return (
                      <td key={m} className={`px-4 py-2 ${isWinner ? "font-bold text-green-700" : ""}`}>
                        {r ? (
                          <>
                            {formatPercent(r.passRate ?? r.mean)}
                            {r.n ? <span className="text-xs text-slate-500"> (n={r.n})</span> : null}
                          </>
                        ) : "—"}
                      </td>
                    );
                  })}
                  <td className="px-4 py-2 font-mono text-xs">{sc.winner.perMetric[metric] ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-lg font-semibold mb-2">Tier-2 access</h2>
        <p className="text-sm text-slate-600">
          Sample traces and audit events require <code>Eval.AuditViewer</code> or{" "}
          <code>Eval.Operator</code> role and emit{" "}
          <code>scorecard.trace.read</code> audit events. Use{" "}
          <code>GET /api/eval/runs/{`{runId}`}/scorecard/traces/{`{caseId}`}</code> from a privileged
          session.
        </p>
      </section>

      <p className="mt-6 text-xs text-slate-500">
        Generated {new Date(sc.generatedAt).toLocaleString()}
      </p>
    </main>
  );
}
