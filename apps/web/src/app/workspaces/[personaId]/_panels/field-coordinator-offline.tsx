/**
 * Field Coordinator Offline panel (T041, FR-006).
 *
 * Degraded-mode banner, queue-depth gauge ≥ 80% utilisation warning (Q7),
 * reconnect-replay progress.
 */

"use client";

import * as React from "react";

import {
  createOfflineQueueStore,
  type OfflineQueueStore,
} from "../../../../lib/offline/queue-store";

export interface FieldCoordinatorOfflineProps {
  /**
   * Optional polling interval in ms for queue depth refresh.
   */
  pollIntervalMs?: number;
}

export function FieldCoordinatorOffline(
  props: FieldCoordinatorOfflineProps,
): React.ReactElement {
  const { pollIntervalMs = 1500 } = props;
  const [online, setOnline] = React.useState(true);
  const [size, setSize] = React.useState(0);
  const [cap, setCap] = React.useState(500);
  const [replay, setReplay] = React.useState<{
    active: boolean;
    drained: number;
    failed: number;
    needsReview: number;
  }>({ active: false, drained: 0, failed: 0, needsReview: 0 });
  const storeRef = React.useRef<OfflineQueueStore | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      const s = await createOfflineQueueStore();
      if (cancelled) {
        s.close();
        return;
      }
      storeRef.current = s;
      setCap(s.cap());
      setSize(await s.size());
    })();
    return () => {
      cancelled = true;
      storeRef.current?.close();
      storeRef.current = null;
    };
  }, []);

  React.useEffect(() => {
    if (typeof window === "undefined") return;
    setOnline(navigator.onLine);
    const goOnline = () => setOnline(true);
    const goOffline = () => setOnline(false);
    window.addEventListener("online", goOnline);
    window.addEventListener("offline", goOffline);
    return () => {
      window.removeEventListener("online", goOnline);
      window.removeEventListener("offline", goOffline);
    };
  }, []);

  React.useEffect(() => {
    const t = setInterval(async () => {
      const s = storeRef.current;
      if (!s) return;
      setSize(await s.size());
    }, pollIntervalMs);
    return () => clearInterval(t);
  }, [pollIntervalMs]);

  const utilisation = cap > 0 ? size / cap : 0;
  const utilisationPct = Math.round(utilisation * 100);
  const utilisationTone =
    utilisation >= 0.8
      ? "bg-rose-100 text-rose-900"
      : utilisation >= 0.5
        ? "bg-amber-100 text-amber-900"
        : "bg-emerald-100 text-emerald-900";

  const replayNow = React.useCallback(async () => {
    const s = storeRef.current;
    if (!s) return;
    setReplay({ active: true, drained: 0, failed: 0, needsReview: 0 });
    let drained = 0;
    let failed = 0;
    let needsReview = 0;
    let repeatedFailures = 0;

    const isManualReapprovalRoute = (route: string): boolean => {
      return /\/api\/alerts\/.+\/(publish|deliver)$/.test(route) || /\/api\/recommendations\/.+\/approvals$/.test(route);
    };

    const backoffMsFor = (attempts: number): number => {
      const exp = Math.min(5, Math.max(1, attempts + 1));
      return 1000 * 2 ** exp;
    };

    for (;;) {
      const batch = await s.leaseBatch(50, 30_000);
      if (batch.length === 0) break;
      for (const entry of batch) {
        if (isManualReapprovalRoute(entry.route)) {
          await s.nack(
            entry.actor_id,
            entry.client_correlation_id,
            "requires_explicit_reapproval",
            backoffMsFor(entry.attempts),
          );
          needsReview += 1;
          continue;
        }

        try {
          const res = await fetch(entry.route, {
            method: entry.method,
            headers: {
              "content-type": "application/json",
              "x-replay-captured-ts": entry.captured_ts,
              "x-correlation-id": entry.client_correlation_id,
              "x-offline-actor-id": entry.actor_id,
              "x-offline-tenant-id": entry.tenant_id,
              "x-offline-incident-id": entry.incident_id,
              "x-offline-mode": entry.mode,
              "x-replay-attempt": String(entry.attempts + 1),
            },
            body: JSON.stringify(entry.payload),
          });
          if (res.ok) {
            repeatedFailures = 0;
            drained += 1;
            await s.ack(entry.actor_id, entry.client_correlation_id);
          } else if ([401, 403, 409].includes(res.status)) {
            repeatedFailures = 0;
            needsReview += 1;
            await s.nack(
              entry.actor_id,
              entry.client_correlation_id,
              `operator_review_required_http_${res.status}`,
              backoffMsFor(entry.attempts),
            );
          } else {
            repeatedFailures += 1;
            failed += 1;
            await s.nack(
              entry.actor_id,
              entry.client_correlation_id,
              `retryable_http_${res.status}`,
              backoffMsFor(entry.attempts),
            );
          }
        } catch {
          repeatedFailures += 1;
          failed += 1;
          await s.nack(
            entry.actor_id,
            entry.client_correlation_id,
            "network_failure",
            backoffMsFor(entry.attempts),
          );
        }

        if (repeatedFailures >= 3) {
          break;
        }
      }
      setReplay({ active: true, drained, failed, needsReview });
      if (repeatedFailures >= 3) {
        break;
      }
    }
    setReplay({ active: false, drained, failed, needsReview });
    setSize(await s.size());
  }, []);

  return (
    <section
      className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
      data-testid="field-coordinator-offline"
    >
      <header className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Field coordinator (offline-aware)</h2>
        <span className="text-xs text-slate-500">FR-006</span>
      </header>
      {!online ? (
        <p
          role="status"
          aria-live="polite"
          className="mb-3 rounded-md border border-amber-300 bg-amber-50 p-2 text-sm text-amber-900"
          data-testid="degraded-mode-banner"
        >
          Degraded mode — operating offline. State-changing requests are being
          queued for replay.
        </p>
      ) : null}
      <div
        className={`rounded-md p-2 text-sm ${utilisationTone}`}
        data-testid="queue-depth-gauge"
      >
        Queue depth: {size}/{cap} ({utilisationPct}%)
        {utilisation >= 0.8 ? (
          <span className="ml-2 font-semibold">
            High utilisation — life-safety insertions will displace oldest routine.
          </span>
        ) : null}
      </div>
      <div className="mt-3 flex items-center gap-2">
        <button
          type="button"
          disabled={!online || replay.active || size === 0}
          onClick={replayNow}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {replay.active ? "Replaying…" : "Replay queued requests"}
        </button>
        {replay.drained || replay.failed || replay.needsReview ? (
          <span className="text-xs text-slate-700">
            drained {replay.drained}, failed {replay.failed}, review {replay.needsReview}
          </span>
        ) : null}
      </div>
    </section>
  );
}

export default FieldCoordinatorOffline;
