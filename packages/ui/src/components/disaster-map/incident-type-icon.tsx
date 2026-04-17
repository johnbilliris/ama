"use client";

/**
 * IncidentTypeIcon — SVG icon for each disaster/incident type.
 *
 * Inspired by the AIDR Knowledge Hub (knowledge.aidr.org.au/disasters/)
 * pin icons. Each type gets a distinct colour and symbol rendered as an
 * inline SVG so there are zero external image dependencies.
 */

export interface IncidentTypeIconProps {
  type: string;
  size?: number;
  className?: string;
}

interface IconDef {
  /** Fill colour for the circle background */
  bg: string;
  /** Emoji / unicode symbol rendered in the centre */
  symbol: string;
}

const ICON_MAP: Record<string, IconDef> = {
  biosecurity:      { bg: "#6A1B9A", symbol: "🧬" },
  bushfire:         { bg: "#D84315", symbol: "🔥" },
  criminal:         { bg: "#37474F", symbol: "🚨" },
  cyclone:          { bg: "#0277BD", symbol: "🌀" },
  earthquake:       { bg: "#795548", symbol: "💥" },
  environment:      { bg: "#2E7D32", symbol: "🌿" },
  extreme_heat:     { bg: "#E65100", symbol: "🌡️" },
  flood:            { bg: "#1565C0", symbol: "🌊" },
  health:           { bg: "#C62828", symbol: "🏥" },
  industrial:       { bg: "#455A64", symbol: "🏭" },
  landslide:        { bg: "#8D6E63", symbol: "⛰️" },
  maritime_coastal: { bg: "#00838F", symbol: "⚓" },
  other:            { bg: "#757575", symbol: "⚠️" },
  pandemic:         { bg: "#AD1457", symbol: "🦠" },
  storm:            { bg: "#4527A0", symbol: "⛈️" },
  tornado:          { bg: "#283593", symbol: "🌪️" },
  transport:        { bg: "#EF6C00", symbol: "🚗" },
  tsunami:          { bg: "#006064", symbol: "🌊" },
  urban_fire:       { bg: "#BF360C", symbol: "🏠" },
};

const FALLBACK: IconDef = { bg: "#9E9E9E", symbol: "❓" };

export function IncidentTypeIcon({
  type,
  size = 22,
  className,
}: IncidentTypeIconProps) {
  const def = ICON_MAP[type] ?? FALLBACK;
  const fontSize = size * 0.52;

  return (
    <span
      className={`disaster-mapper-type-icon ${className ?? ""}`}
      role="img"
      aria-label={type.replace(/_/g, " ")}
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

export default IncidentTypeIcon;
