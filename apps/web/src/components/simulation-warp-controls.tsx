"use client";

import { useState } from "react";
import { ALLOWED_WARP_SPEEDS, changeWarpSpeed } from "@/lib/api/simulations";

/**
 * Warp-speed control selector. Shows current warp, allows mid-run changes (US2),
 * and surfaces errors inline. Accessible via arrow keys and screen readers.
 */
export function SimulationWarpControls({
  tenantId,
  currentWarpSpeed,
  disabled = false,
  onChanged,
}: {
  tenantId: string;
  currentWarpSpeed: number;
  disabled?: boolean;
  onChanged?: (newSpeed: number) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const select = async (speed: number) => {
    if (speed === currentWarpSpeed || busy || disabled) return;
    setBusy(true);
    setError(null);
    try {
      const result = await changeWarpSpeed(tenantId, speed);
      onChanged?.(result.current_warp_speed);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="sim-warp-controls" aria-label="Time warp speed">
      <div
        className="sim-warp-buttons"
        role="radiogroup"
        aria-label="Warp speed selector"
      >
        {ALLOWED_WARP_SPEEDS.map((s) => {
          const active = Math.abs(s - currentWarpSpeed) < 1e-9;
          return (
            <button
              key={s}
              type="button"
              role="radio"
              aria-checked={active}
              onClick={() => select(s)}
              disabled={busy || disabled}
              className={
                "sim-warp-btn " + (active ? "sim-warp-btn--active" : "")
              }
              title={`${s}× warp`}
            >
              {s}×
            </button>
          );
        })}
      </div>
      {error && (
        <p role="alert" className="sim-warp-error">
          {error}
        </p>
      )}
    </div>
  );
}
