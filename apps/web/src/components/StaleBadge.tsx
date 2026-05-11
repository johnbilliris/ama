/**
 * Spec-036 T-I02 — stale-data indicator badge.
 *
 * Surfaced by the map and chat panes when an overlay or signal has crossed
 * its FR-030 freshness window. Carries an `aria-label` so screen-readers
 * announce the staleness independently of colour cues.
 */
import type { CSSProperties } from "react";

interface StaleBadgeProps {
  /** Age in seconds since the data point's `valid_from` timestamp. */
  ageSeconds: number;
  /** Threshold in seconds — defaults to 300 (5 min). */
  thresholdSeconds?: number;
  className?: string;
  style?: CSSProperties;
}

export function StaleBadge({
  ageSeconds,
  thresholdSeconds = 300,
  className,
  style,
}: StaleBadgeProps) {
  if (ageSeconds <= thresholdSeconds) return null;
  const minutes = Math.floor(ageSeconds / 60);
  return (
    <span
      role="status"
      aria-label={`Stale data — ${minutes} minutes old, exceeds ${Math.floor(
        thresholdSeconds / 60,
      )} minute freshness window`}
      className={`inline-flex items-center gap-1 rounded-sm bg-amber-50 px-1.5 py-0.5 text-[10px] font-medium text-amber-800 ring-1 ring-amber-200 ${className ?? ""}`}
      style={style}
      data-testid="stale-badge"
      title={`Data is ${minutes} min old`}
    >
      <span aria-hidden="true">⏱</span>
      <span>STALE · {minutes}m</span>
    </span>
  );
}

export default StaleBadge;
