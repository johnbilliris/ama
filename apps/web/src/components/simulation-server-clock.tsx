"use client";

import { useEffect, useState } from "react";
import { getSimulationClock, type SimulationClockResponse } from "@/lib/api/simulations";

/**
 * Server-owned simulation clock display.
 *
 * Polls the backend `/clock` endpoint every `pollIntervalMs` (default 1000ms)
 * and shows:
 *   - current sim time (HH:MM:SS, optional wall elapsed hint)
 *   - current warp speed badge
 *   - paused indicator
 *   - delivery-lag warning banner when the scheduler is ≥10s behind
 */
export function SimulationServerClock({
  tenantId,
  pollIntervalMs = 1000,
  onClock,
}: {
  tenantId: string;
  pollIntervalMs?: number;
  onClock?: (c: SimulationClockResponse) => void;
}) {
  const [clock, setClock] = useState<SimulationClockResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const fetchOnce = () =>
      getSimulationClock(tenantId)
        .then((c) => {
          if (cancelled) return;
          setClock(c);
          setError(null);
          onClock?.(c);
        })
        .catch((err: Error) => {
          if (!cancelled) setError(err.message);
        });

    fetchOnce();
    const id = setInterval(fetchOnce, pollIntervalMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [tenantId, pollIntervalMs, onClock]);

  if (error) {
    return (
      <div className="sim-server-clock sim-server-clock--error" role="alert">
        Clock unavailable: {error}
      </div>
    );
  }
  if (!clock) {
    return (
      <div className="sim-server-clock sim-server-clock--loading">—</div>
    );
  }

  const fmt = (total: number) => {
    const t = Math.max(0, Math.floor(total));
    const h = String(Math.floor(t / 3600)).padStart(2, "0");
    const m = String(Math.floor((t % 3600) / 60)).padStart(2, "0");
    const s = String(t % 60).padStart(2, "0");
    return `${h}:${m}:${s}`;
  };

  const lag = clock.delivery_lag_seconds ?? 0;
  const lagging = lag >= 10;

  return (
    <div
      className="sim-server-clock"
      aria-label="Simulation server clock"
      style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.75rem", width: "100%" }}
    >
      <span
        className="sim-server-clock-left"
        style={{ display: "inline-flex", alignItems: "center", gap: "0.25rem" }}
      >
        <span className="sim-server-clock-icon">⏱</span>
        <span className="sim-server-clock-value">{fmt(clock.current_sim_seconds)}</span>
      </span>
      <span
        className="sim-server-clock-right"
        style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", marginLeft: "auto" }}
      >
        <span
          className="sim-server-clock-warp"
          title={`Current warp: ${clock.current_warp_speed}×`}
        >
          {clock.current_warp_speed}×
        </span>
        {clock.clock_paused && (
          <span className="sim-server-clock-paused" aria-label="Paused">
            ⏸ Paused
          </span>
        )}
        {lagging && (
          <span
            className="sim-server-clock-lag-warning"
            role="alert"
            title="Scheduler is behind schedule"
          >
            ⚠ Delivery lag {lag.toFixed(1)}s
          </span>
        )}
      </span>
    </div>
  );
}
