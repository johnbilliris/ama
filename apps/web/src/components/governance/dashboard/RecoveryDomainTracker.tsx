"use client";

import { CompanionDataTable } from "@/components/governance/a11y/CompanionDataTable";
import type { RecoveryDomainProgress } from "@/lib/api/governance";

interface RecoveryDomainTrackerProps {
  domains: RecoveryDomainProgress[];
  onDomainClick: (domain: string) => void;
}

const TREND_ICONS: Record<string, { icon: string; label: string; colour: string }> = {
  improving: { icon: "↑", label: "Improving", colour: "text-green-600" },
  stable: { icon: "→", label: "Stable", colour: "text-gray-600" },
  declining: { icon: "↓", label: "Declining", colour: "text-red-600" },
};

/**
 * 5-domain recovery progress display with trend indicators and target variance (US5).
 */
export function RecoveryDomainTracker({
  domains,
  onDomainClick,
}: RecoveryDomainTrackerProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <h3 className="mb-3 text-sm font-semibold text-gray-900">
        Recovery Domain Progress
      </h3>

      <div className="space-y-3">
        {domains.map((domain) => {
          const trend = TREND_ICONS[domain.trend] ?? TREND_ICONS.stable;
          return (
            <button
              key={domain.domain}
              onClick={() => onDomainClick(domain.domain)}
              className={`w-full rounded-lg border p-3 text-left transition-colors hover:border-blue-300 hover:bg-blue-50 ${
                domain.is_cross_cutting
                  ? "border-gray-300 bg-gray-50"
                  : "border-gray-200"
              }`}
              aria-label={`${domain.display_name}: ${domain.completion_pct}% complete, ${trend.label}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-900">
                    {domain.display_name}
                  </span>
                  {domain.is_cross_cutting && (
                    <span className="rounded bg-gray-200 px-1.5 py-0.5 text-[10px] text-gray-600">
                      Cross-cutting
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-semibold ${trend.colour}`}>
                    {trend.icon} {trend.label}
                  </span>
                  <span className="text-sm font-bold text-gray-900">
                    {domain.completion_pct.toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Progress bar */}
              <div className="mt-2 h-2 w-full rounded-full bg-gray-200">
                <div
                  className={`h-2 rounded-full ${
                    domain.is_below_target ? "bg-red-500" : "bg-green-500"
                  }`}
                  style={{ width: `${Math.min(100, domain.completion_pct)}%` }}
                />
              </div>

              {/* Target info */}
              <div className="mt-1 flex justify-between text-xs text-gray-500">
                <span>Target: {domain.target_pct.toFixed(1)}%</span>
                <span
                  className={
                    domain.variance_from_target >= 0
                      ? "text-green-600"
                      : "text-red-600"
                  }
                >
                  {domain.variance_from_target >= 0 ? "+" : ""}
                  {domain.variance_from_target.toFixed(1)}%
                  {domain.is_below_target && " ⚠ Below target"}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Companion data table */}
      {domains.length > 0 && (
        <CompanionDataTable
          caption="Recovery domain progress breakdown"
          headers={["Domain", "Completion %", "Target %", "Variance", "Trend"]}
          rows={domains.map((d) => [
            d.display_name,
            d.completion_pct.toFixed(1),
            d.target_pct.toFixed(1),
            `${d.variance_from_target >= 0 ? "+" : ""}${d.variance_from_target.toFixed(1)}%`,
            d.trend,
          ])}
        />
      )}
    </div>
  );
}
