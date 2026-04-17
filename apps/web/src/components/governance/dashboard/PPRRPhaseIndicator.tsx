"use client";

import type { PPRRPhaseStatus } from "@/lib/api/governance";

interface PPRRPhaseIndicatorProps {
  phases: PPRRPhaseStatus[];
}

const PHASE_LABELS: Record<string, string> = {
  prevention: "Prevention",
  preparedness: "Preparedness",
  response: "Response",
  recovery: "Recovery",
};

const STATUS_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  active: { bg: "bg-blue-100", text: "text-blue-800", border: "border-blue-400" },
  elevated: { bg: "bg-red-100", text: "text-red-800", border: "border-red-400" },
  inactive: { bg: "bg-gray-100", text: "text-gray-600", border: "border-gray-300" },
};

/**
 * 4-phase horizontal PPRR indicator with active phase highlighted (US4).
 */
export function PPRRPhaseIndicator({ phases }: PPRRPhaseIndicatorProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <h3 className="mb-3 text-sm font-semibold text-gray-900">
        PPRR Lifecycle Phases
      </h3>
      <div className="flex gap-2">
        {phases.map((phase) => {
          const styles = STATUS_STYLES[phase.indicator_status] ?? STATUS_STYLES.inactive;
          const label = PHASE_LABELS[phase.phase] ?? phase.phase;

          return (
            <div
              key={phase.phase}
              className={`flex-1 rounded-lg border-2 p-3 text-center ${styles.bg} ${styles.border}`}
              role="status"
              aria-label={`${label}: ${phase.is_active ? "Active" : "Inactive"}${
                phase.indicator_status === "elevated" ? ", Elevated" : ""
              }`}
            >
              <p className={`text-sm font-semibold ${styles.text}`}>
                {label}
              </p>
              <p className={`text-xs ${styles.text}`}>
                {phase.is_active ? "● Active" : "○ Inactive"}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
