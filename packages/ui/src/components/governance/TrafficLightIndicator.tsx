interface TrafficLightIndicatorProps {
  /** Current status */
  status: "green" | "amber" | "red" | string;
  /** Optional label text */
  label?: string;
  /** Size variant */
  size?: "sm" | "md" | "lg";
}

const STATUS_CONFIG: Record<string, { bg: string; text: string; icon: string; label: string }> = {
  green: {
    bg: "bg-green-100",
    text: "text-green-800",
    icon: "✓",
    label: "Good",
  },
  amber: {
    bg: "bg-yellow-100",
    text: "text-yellow-800",
    icon: "⚠",
    label: "Warning",
  },
  red: {
    bg: "bg-red-100",
    text: "text-red-800",
    icon: "✗",
    label: "Critical",
  },
};

const SIZE_CLASSES = {
  sm: "px-2 py-0.5 text-xs",
  md: "px-3 py-1 text-sm",
  lg: "px-4 py-1.5 text-base",
};

/**
 * Green/Amber/Red status indicator with icon + text label.
 * Colour is never the sole means of conveying information (WCAG).
 */
export function TrafficLightIndicator({
  status,
  label,
  size = "md",
}: TrafficLightIndicatorProps) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.amber;
  const displayLabel = label ?? config.label;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-medium ${config.bg} ${config.text} ${SIZE_CLASSES[size]}`}
      role="status"
      aria-label={`Status: ${displayLabel}`}
    >
      <span aria-hidden="true">{config.icon}</span>
      {displayLabel}
    </span>
  );
}
