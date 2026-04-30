"use client";

/**
 * SeverityIcon — Coloured badge for AWS severity tiers.
 *
 * Mirrors the IncidentTypeIcon pattern: a small coloured circle with a
 * unicode symbol for visual consistency across the Disaster Mapper
 * filter panel.
 */

export interface SeverityIconProps {
  tier: string;
  size?: number;
  className?: string;
}

interface IconDef {
  bg: string;
  symbol: string;
}

const ICON_MAP: Record<string, IconDef> = {
  Advice:               { bg: "#FBC02D", symbol: "ℹ️" },
  "Watch and Act":      { bg: "#F57C00", symbol: "⚠️" },
  "Emergency Warning":  { bg: "#C62828", symbol: "🚨" },
};

const FALLBACK: IconDef = { bg: "#9E9E9E", symbol: "❓" };

export function SeverityIcon({
  tier,
  size = 22,
  className,
}: SeverityIconProps) {
  const def = ICON_MAP[tier] ?? FALLBACK;
  const fontSize = size * 0.52;

  return (
    <span
      className={`disaster-mapper-severity-icon ${className ?? ""}`}
      role="img"
      aria-label={tier}
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

export default SeverityIcon;
