"use client";

/**
 * StatusIcon — SVG/emoji icon for each operational status.
 *
 * Mirrors the IncidentTypeIcon pattern: each status is rendered as a
 * small coloured circle with a unicode symbol so there are zero external
 * image dependencies.
 */

export interface StatusIconProps {
  status: string;
  size?: number;
  className?: string;
}

interface IconDef {
  bg: string;
  symbol: string;
}

const ICON_MAP: Record<string, IconDef> = {
  monitoring:  { bg: "#1565C0", symbol: "👁️" },
  active:      { bg: "#D84315", symbol: "🚨" },
  stabilising: { bg: "#F9A825", symbol: "🛠️" },
  recovery:    { bg: "#2E7D32", symbol: "🌱" },
  closed:      { bg: "#546E7A", symbol: "✅" },
};

const FALLBACK: IconDef = { bg: "#9E9E9E", symbol: "❓" };

export function StatusIcon({
  status,
  size = 22,
  className,
}: StatusIconProps) {
  const def = ICON_MAP[status] ?? FALLBACK;
  const fontSize = size * 0.52;

  return (
    <span
      className={`disaster-mapper-status-icon ${className ?? ""}`}
      role="img"
      aria-label={status.replace(/_/g, " ")}
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

export default StatusIcon;
