"use client";

/**
 * PprrPhaseIcon — Coloured badge for the four PPRR phases.
 *
 * Mirrors the IncidentTypeIcon pattern: a small coloured circle with a
 * unicode symbol for visual consistency across the Disaster Mapper
 * filter panel.
 */

export interface PprrPhaseIconProps {
  phase: string;
  size?: number;
  className?: string;
}

interface IconDef {
  bg: string;
  symbol: string;
}

const ICON_MAP: Record<string, IconDef> = {
  prevention:   { bg: "#2E7D32", symbol: "🛡️" },
  preparedness: { bg: "#0277BD", symbol: "📋" },
  response:     { bg: "#D84315", symbol: "🚒" },
  recovery:     { bg: "#6A1B9A", symbol: "🔄" },
};

const FALLBACK: IconDef = { bg: "#9E9E9E", symbol: "❓" };

export function PprrPhaseIcon({
  phase,
  size = 22,
  className,
}: PprrPhaseIconProps) {
  const def = ICON_MAP[phase] ?? FALLBACK;
  const fontSize = size * 0.52;

  return (
    <span
      className={`disaster-mapper-pprr-icon ${className ?? ""}`}
      role="img"
      aria-label={phase.replace(/_/g, " ")}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        width: size,
        height: size,
        minWidth: size,
        borderRadius: "50%",
        backgroundColor: def.bg,
        fontSize,
        lineHeight: 1,
      }}
    >
      {def.symbol}
    </span>
  );
}

export default PprrPhaseIcon;
