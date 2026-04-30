import {
  type WorkflowRun,
  listAudit,
  listCheckpoints,
  listRuns,
} from "@/lib/api/workflow-runs";
import { ApprovalGateMetricsPanel } from "@/components/workflow/ApprovalGateMetrics";
import { WorkflowRunDetail } from "@/components/workflow/WorkflowRunDetail";
import { WorkflowRunList } from "@/components/workflow/WorkflowRunList";

/**
 * Workflows operator dashboard (T055).
 *
 * Server component composing:
 *  - WorkflowRunList (T053)        — runs grouped by 7 canonical states
 *  - WorkflowRunDetail (T054)       — selected run's checkpoints + audit
 *  - ApprovalGateMetricsPanel (T056b) — day-one approval-gate metrics
 *
 * SC-008 invariant: this page is on the "available on day one of cutover"
 * critical path; ApprovalGateMetricsPanel ships in US2 (T056b), not US3.
 */

export default async function WorkflowsPage({
  searchParams,
}: {
  searchParams?: { run?: string; state?: string };
}) {
  const { items } = await listRuns({ limit: 100 });
  const selectedId = searchParams?.run;
  const selected: WorkflowRun | undefined =
    items.find((r) => r.id === selectedId) ?? items[0];

  let checkpoints: Awaited<ReturnType<typeof listCheckpoints>> = [];
  let audit: Awaited<ReturnType<typeof listAudit>> = [];
  if (selected) {
    [checkpoints, audit] = await Promise.all([
      listCheckpoints(selected.id),
      listAudit(selected.id),
    ]);
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-4">
      <div>
        <WorkflowRunList runs={items} />
        <div className="mt-6">
          <ApprovalGateMetricsPanel />
        </div>
      </div>
      <div>
        {selected ? (
          <WorkflowRunDetail
            run={selected}
            checkpoints={checkpoints}
            audit={audit}
          />
        ) : (
          <p className="text-slate-500">No workflow runs yet.</p>
        )}
      </div>
    </div>
  );
}
