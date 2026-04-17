"use client";

interface DataFreshnessIndicatorProps {
  /** ISO timestamp of the data freshness */
  timestamp: string | null;
  /** Label for the data source */
  label?: string;
}

/**
 * Staleness badge showing age of displayed data per widget (FR-030).
 * Displays time since last data update with colour coding:
 * - Green: < 1 minute
 * - Amber: 1-5 minutes
 * - Red: > 5 minutes
 */
export function DataFreshnessIndicator({
  timestamp,
  label = "Data",
}: DataFreshnessIndicatorProps) {
  if (!timestamp) {
    return (
      <span
        className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
        aria-label={`${label}: No data available`}
      >
        ⏳ No data
      </span>
    );
  }

  const now = new Date();
  const dataTime = new Date(timestamp);
  const ageMs = now.getTime() - dataTime.getTime();
  const ageMinutes = Math.floor(ageMs / 60000);

  let colorClass: string;
  let statusIcon: string;

  if (ageMinutes < 1) {
    colorClass = "bg-green-100 text-green-800";
    statusIcon = "🟢";
  } else if (ageMinutes <= 5) {
    colorClass = "bg-yellow-100 text-yellow-800";
    statusIcon = "🟡";
  } else {
    colorClass = "bg-red-100 text-red-800";
    statusIcon = "🔴";
  }

  const ageText =
    ageMinutes < 1
      ? "Just now"
      : ageMinutes === 1
        ? "1 min ago"
        : `${ageMinutes} min ago`;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs ${colorClass}`}
      aria-label={`${label}: Updated ${ageText}`}
    >
      {statusIcon} {ageText}
    </span>
  );
}
