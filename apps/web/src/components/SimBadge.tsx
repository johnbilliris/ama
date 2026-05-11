/**
 * Spec-036 T-I02 — `[SIMULATION]` badge.
 *
 * Renders the FR-058 visual watermark required on every simulation surface.
 * Always rendered with role="status" + aria-label so screen-readers announce
 * the exercise mode unambiguously.
 */
import type { CSSProperties } from "react";

interface SimBadgeProps {
  /** Visual size — defaults to small inline pill. */
  size?: "sm" | "md";
  /** Optional explicit className for compositional layouts. */
  className?: string;
  style?: CSSProperties;
}

export function SimBadge({ size = "sm", className, style }: SimBadgeProps) {
  const sizeClass =
    size === "md"
      ? "px-2 py-1 text-[11px] font-bold"
      : "px-1.5 py-0.5 text-[10px] font-bold";
  return (
    <span
      role="status"
      aria-label="Simulation exercise mode"
      className={`inline-flex items-center rounded-sm bg-amber-100 text-amber-900 ring-1 ring-amber-300 ${sizeClass} ${className ?? ""}`}
      style={style}
      data-testid="sim-badge"
    >
      [SIMULATION]
    </span>
  );
}

export default SimBadge;
