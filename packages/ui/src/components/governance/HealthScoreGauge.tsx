"use client";

import { CompanionDataTable } from "@/components/governance/a11y/CompanionDataTable";
import { generateChartAriaLabel } from "@/components/governance/a11y/ChartAriaLabel";

interface HealthScoreGaugeProps {
  /** Composite score 0-100 */
  score: number;
  /** Traffic light status */
  status: "green" | "amber" | "red";
  /** Dimension breakdown for companion table */
  dimensions?: Array<{
    dimension: string;
    score: number;
    weight: number;
    weighted_score: number;
  }>;
}

const STATUS_COLOURS: Record<string, { ring: string; text: string; bg: string }> = {
  green: { ring: "text-green-500", text: "text-green-700", bg: "bg-green-50" },
  amber: { ring: "text-yellow-500", text: "text-yellow-700", bg: "bg-yellow-50" },
  red: { ring: "text-red-500", text: "text-red-700", bg: "bg-red-50" },
};

/**
 * 0-100 gauge with traffic light status and companion data table for accessibility.
 */
export function HealthScoreGauge({
  score,
  status,
  dimensions = [],
}: HealthScoreGaugeProps) {
  const colours = STATUS_COLOURS[status] ?? STATUS_COLOURS.amber;
  const percentage = Math.min(100, Math.max(0, score));
  const circumference = 2 * Math.PI * 40;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const ariaLabel = generateChartAriaLabel({
    type: "gauge",
    label: "Governance health score",
    value: Math.round(score),
    max: 100,
    status: status.charAt(0).toUpperCase() + status.slice(1),
  });

  return (
    <div className={`rounded-lg p-4 ${colours.bg}`}>
      <div className="flex items-center gap-4">
        {/* SVG Gauge */}
        <div className="relative h-24 w-24" aria-hidden="true">
          <svg className="h-24 w-24 -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="currentColor"
              strokeWidth="8"
              className="text-gray-200"
            />
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="currentColor"
              strokeWidth="8"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              className={colours.ring}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`text-2xl font-bold ${colours.text}`}>
              {Math.round(score)}
            </span>
          </div>
        </div>

        {/* Labels */}
        <div>
          <h3 className="text-sm font-semibold text-gray-900">
            Governance Health
          </h3>
          <p className={`text-lg font-bold ${colours.text}`} aria-label={ariaLabel}>
            {Math.round(score)}/100
          </p>
          <span
            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${colours.bg} ${colours.text}`}
          >
            {status === "green" && "✓ Good"}
            {status === "amber" && "⚠ Warning"}
            {status === "red" && "✗ Critical"}
          </span>
        </div>
      </div>

      {/* Companion data table for screen readers */}
      {dimensions.length > 0 && (
        <CompanionDataTable
          caption="Health score dimension breakdown"
          headers={["Dimension", "Score", "Weight", "Weighted Score"]}
          rows={dimensions.map((d) => [
            d.dimension.replace(/_/g, " "),
            d.score.toFixed(1),
            (d.weight * 100).toFixed(0) + "%",
            d.weighted_score.toFixed(1),
          ])}
        />
      )}
    </div>
  );
}
