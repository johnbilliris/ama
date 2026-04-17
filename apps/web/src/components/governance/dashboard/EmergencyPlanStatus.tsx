"use client";

import type { EmergencyPlanSummary } from "@/lib/api/governance";

interface EmergencyPlanStatusProps {
  plans: EmergencyPlanSummary[];
  totalPlans: number;
  overdueTotal: number;
}

const STATE_COLOURS: Record<string, string> = {
  Draft: "bg-gray-100 text-gray-800",
  InConsultation: "bg-blue-100 text-blue-800",
  UnderReview: "bg-yellow-100 text-yellow-800",
  Endorsed: "bg-green-100 text-green-800",
  Activated: "bg-purple-100 text-purple-800",
  PostEventReview: "bg-orange-100 text-orange-800",
  Superseded: "bg-gray-200 text-gray-600",
};

/**
 * Emergency plan lifecycle breakdown with overdue flags (US4, R-012).
 * "Expired" is a display-level overlay, not a lifecycle state.
 */
export function EmergencyPlanStatus({
  plans,
  totalPlans,
  overdueTotal,
}: EmergencyPlanStatusProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">
          Emergency Plans ({totalPlans})
        </h3>
        {overdueTotal > 0 && (
          <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">
            ⚠ {overdueTotal} overdue
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7">
        {plans.map((plan) => {
          const colour = STATE_COLOURS[plan.lifecycle_state] ?? "bg-gray-100 text-gray-800";
          return (
            <div
              key={plan.lifecycle_state}
              className={`relative rounded-lg p-3 ${colour}`}
            >
              <p className="text-lg font-bold">{plan.count}</p>
              <p className="text-xs font-medium">
                {plan.lifecycle_state.replace(/([A-Z])/g, " $1").trim()}
              </p>
              {plan.overdue_count > 0 && (
                <span className="absolute -right-1 -top-1 rounded-full bg-red-500 px-1.5 py-0.5 text-[10px] font-bold text-white">
                  ⚠ {plan.overdue_count}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
