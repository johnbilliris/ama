/**
 * ARIA label generator for chart/gauge widgets (FR-032).
 *
 * Generates descriptive ARIA labels for data visualisations so screen readers
 * can convey the meaning without visual cues.
 */

export interface ChartAriaLabelOptions {
  /** Type of visualisation */
  type: "gauge" | "chart" | "indicator" | "progress_bar";
  /** Main label */
  label: string;
  /** Current value */
  value: number | string;
  /** Maximum value (for gauges) */
  max?: number;
  /** Unit of measurement */
  unit?: string;
  /** Status text (e.g., "Green", "Amber", "Red") */
  status?: string;
  /** Additional context */
  context?: string;
}

/**
 * Generate an accessible ARIA label for chart/gauge widgets.
 *
 * @example
 * generateChartAriaLabel({
 *   type: "gauge",
 *   label: "Governance health score",
 *   value: 78,
 *   max: 100,
 *   status: "Amber",
 * })
 * // Returns: "Governance health score: 78 out of 100, Amber status"
 */
export function generateChartAriaLabel({
  type,
  label,
  value,
  max,
  unit,
  status,
  context,
}: ChartAriaLabelOptions): string {
  const parts: string[] = [label];

  if (type === "gauge" && max !== undefined) {
    parts.push(`${value} out of ${max}`);
  } else if (unit) {
    parts.push(`${value}${unit}`);
  } else {
    parts.push(String(value));
  }

  if (status) {
    parts.push(`${status} status`);
  }

  if (context) {
    parts.push(context);
  }

  return parts.join(": ").replace(/: /, ": ").replace(/:(\s*:)+/g, ":");
}

/**
 * React component wrapper for chart ARIA labels.
 */
export function ChartAriaLabel(props: ChartAriaLabelOptions) {
  const label = generateChartAriaLabel(props);
  return <span className="sr-only">{label}</span>;
}
