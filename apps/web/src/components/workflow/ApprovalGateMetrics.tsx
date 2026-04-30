"use client";

import { useEffect, useState } from "react";

import {
  type ApprovalGateMetrics,
  type ApprovalGateWindow,
  getApprovalGateMetrics,
} from "@/lib/api/workflow-runs";

/**
 * ApprovalGateMetricsPanel (T056b — day-one version moved into US2).
 *
 * Default window 24h; T059 (US3) extends with selectable windows.
 * Mounted as a sibling of WorkflowRunDetail in the workflows page so an
 * operator viewing a paused run sees both detail and metrics without
 * navigation.
 */

const DEFAULT_WINDOW: ApprovalGateWindow = "24h";
const WINDOWS: ApprovalGateWindow[] = ["1h", "24h", "7d", "30d"];

export function ApprovalGateMetricsPanel() {
  const [window, setWindow] = useState<ApprovalGateWindow>(DEFAULT_WINDOW);
  const [data, setData] = useState<ApprovalGateMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    getApprovalGateMetrics(window)
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [window]);

  return (
    <section aria-labelledby="approval-gate-h2" className="rounded border p-4">
      <h2 id="approval-gate-h2" className="text-base font-semibold">
        Approval-gate metrics (SC-008)
      </h2>
      <div className="mt-2 flex gap-1" role="tablist" aria-label="Window">
        {WINDOWS.map((w) => (
          <button
            type="button"
            key={w}
            role="tab"
            aria-selected={window === w}
            onClick={() => setWindow(w)}
            className={
              window === w
                ? "rounded bg-indigo-600 px-2 py-1 text-xs text-white"
                : "rounded border px-2 py-1 text-xs text-slate-600"
            }
          >
            {w}
          </button>
        ))}
      </div>
      {error ? (
        <p role="alert" className="mt-2 text-sm text-red-600">
          {error}
        </p>
      ) : data ? (
        <dl className="mt-3 grid grid-cols-3 gap-3 text-sm">
          <div>
            <dt className="text-xs text-slate-500">MTTA (s)</dt>
            <dd className="font-mono text-base">{data.mtta_seconds}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Approvals</dt>
            <dd className="font-mono text-base">{data.approvals}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Modifications</dt>
            <dd className="font-mono text-base">{data.modifications}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Rejections</dt>
            <dd className="font-mono text-base">{data.rejections}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Escalations</dt>
            <dd className="font-mono text-base">{data.escalations}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Timeouts</dt>
            <dd className="font-mono text-base">{data.timeouts}</dd>
          </div>
        </dl>
      ) : (
        <p className="mt-2 text-sm text-slate-500">Loading…</p>
      )}
    </section>
  );
}
