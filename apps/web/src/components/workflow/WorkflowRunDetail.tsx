"use client";

import type {
  AuditEntrySummary,
  CheckpointSummary,
  WorkflowRun,
} from "@/lib/api/workflow-runs";

/**
 * WorkflowRunDetail (T054).
 *
 * Step-by-step progress, checkpoint timeline, "AwaitingApproval" banner,
 * and a deep-link to the OTel trace in App Insights.
 */

interface Props {
  run: WorkflowRun;
  checkpoints: CheckpointSummary[];
  audit: AuditEntrySummary[];
  appInsightsTraceUrl?: (correlationId: string) => string;
}

export function WorkflowRunDetail({
  run,
  checkpoints,
  audit,
  appInsightsTraceUrl,
}: Props) {
  const correlation = audit[0]?.id ?? null;
  const traceUrl =
    correlation && appInsightsTraceUrl ? appInsightsTraceUrl(correlation) : null;

  return (
    <article aria-label={`Workflow run ${run.id}`} className="space-y-4">
      {run.status === "AwaitingApproval" ? (
        <div role="status" className="border-l-4 border-amber-500 bg-amber-50 p-3 text-sm">
          <strong>Awaiting commander approval.</strong>{" "}
          Pending request: <code className="font-mono">{run.pending_request_id}</code>
        </div>
      ) : null}
      {run.status === "Failed" && run.failure_reason ? (
        <div role="alert" className="border-l-4 border-red-500 bg-red-50 p-3 text-sm">
          <strong>Failed</strong> at step{" "}
          {String((run.failure_reason as Record<string, unknown>).last_completed_step)}:{" "}
          {String((run.failure_reason as Record<string, unknown>).reason_code)}
        </div>
      ) : null}

      <header className="space-y-1">
        <h1 className="text-lg font-semibold">{run.incident_id}</h1>
        <p className="text-sm text-slate-600">
          run <span className="font-mono">{run.id}</span> · status{" "}
          <strong>{run.status}</strong> · current step <em>{run.current_step}</em>
        </p>
        {traceUrl ? (
          <a
            className="text-sm text-indigo-600 underline"
            href={traceUrl}
            target="_blank"
            rel="noopener"
          >
            View OTel trace in Application Insights
          </a>
        ) : null}
      </header>

      <section aria-labelledby="checkpoints-h2">
        <h2 id="checkpoints-h2" className="text-base font-semibold">
          Checkpoint timeline ({checkpoints.length})
        </h2>
        <ol className="border-l-2 pl-4 space-y-1 text-sm">
          {checkpoints.map((c) => (
            <li key={c.id}>
              <span className="font-mono text-xs text-slate-500">{c.taken_at}</span>{" "}
              · #{c.sequence} {c.step_name}
            </li>
          ))}
          {checkpoints.length === 0 ? (
            <li className="text-slate-500">No checkpoints yet.</li>
          ) : null}
        </ol>
      </section>

      <section aria-labelledby="audit-h2">
        <h2 id="audit-h2" className="text-base font-semibold">
          Audit ({audit.length})
        </h2>
        <table className="text-sm w-full">
          <thead>
            <tr className="text-left text-slate-500">
              <th>Agent</th>
              <th>Step</th>
              <th>Outcome</th>
              <th>When</th>
            </tr>
          </thead>
          <tbody>
            {audit.map((a) => (
              <tr key={a.id} className="border-t">
                <td>{a.agent_name}</td>
                <td>{a.step_name}</td>
                <td>{a.outcome}</td>
                <td className="font-mono text-xs">{a.ended_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </article>
  );
}
