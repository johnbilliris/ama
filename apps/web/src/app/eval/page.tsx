import { headers } from "next/headers";
import Link from "next/link";

interface RunSummary {
  runId: string;
  status: string;
  mode: string;
  datasetId: string;
  datasetVersion: string;
  createdAt: string;
  createdBy: string;
  completedAt?: string;
  exitCode?: number;
}

async function fetchRuns(): Promise<RunSummary[]> {
  const h = await headers();
  const proto = h.get("x-forwarded-proto") ?? "http";
  const host = h.get("host") ?? "localhost:3000";
  try {
    const res = await fetch(`${proto}://${host}/api/eval/runs?limit=50`, {
      cache: "no-store",
      headers: { "x-eval-roles": "Eval.Viewer" },
    });
    if (!res.ok) return [];
    return (await res.json()) as RunSummary[];
  } catch {
    return [];
  }
}

function StatusPill({ status }: { status: string }) {
  const cls = {
    succeeded: "bg-green-100 text-green-800",
    running: "bg-blue-100 text-blue-800",
    queued: "bg-amber-100 text-amber-800",
    cancelling: "bg-orange-100 text-orange-800",
    cancelled: "bg-slate-200 text-slate-800",
    failed: "bg-red-100 text-red-800",
    provisioning: "bg-violet-100 text-violet-800",
  }[status] ?? "bg-slate-100 text-slate-700";
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${cls}`}>
      {status}
    </span>
  );
}

export default async function EvalRunsPage() {
  const runs = await fetchRuns();
  return (
    <main className="p-8 max-w-7xl mx-auto">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">LLM Evaluation Runs</h1>
        <p className="text-sm text-slate-600 mt-1">
          Cross-model scorecards for the Disaster Response Coordination Hub. Tier-2 traces require
          auditor or operator role.
        </p>
      </header>

      <div className="overflow-x-auto rounded-lg border border-slate-200">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-slate-700">
            <tr>
              <th className="px-4 py-2 text-left font-semibold">Run ID</th>
              <th className="px-4 py-2 text-left font-semibold">Status</th>
              <th className="px-4 py-2 text-left font-semibold">Mode</th>
              <th className="px-4 py-2 text-left font-semibold">Dataset</th>
              <th className="px-4 py-2 text-left font-semibold">Created</th>
              <th className="px-4 py-2 text-left font-semibold">By</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {runs.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                  No runs found. Trigger one via <code>POST /api/eval/runs</code> or{" "}
                  <code>az containerapp job start</code>.
                </td>
              </tr>
            )}
            {runs.map((r) => (
              <tr key={r.runId} className="hover:bg-slate-50">
                <td className="px-4 py-2 font-mono text-xs">
                  <Link className="text-blue-700 underline" href={`/eval/${r.runId}`}>
                    {r.runId}
                  </Link>
                </td>
                <td className="px-4 py-2"><StatusPill status={r.status} /></td>
                <td className="px-4 py-2">{r.mode}</td>
                <td className="px-4 py-2">
                  <span className="font-mono text-xs">{r.datasetId}@{r.datasetVersion}</span>
                </td>
                <td className="px-4 py-2 text-slate-600">{new Date(r.createdAt).toLocaleString()}</td>
                <td className="px-4 py-2">{r.createdBy}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
