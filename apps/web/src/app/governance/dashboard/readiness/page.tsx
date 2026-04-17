"use client";

import { useEffect, useState } from "react";
import { PPRRPhaseIndicator } from "@/components/governance/dashboard/PPRRPhaseIndicator";
import { EmergencyPlanStatus } from "@/components/governance/dashboard/EmergencyPlanStatus";
import { WidgetErrorBoundary } from "@/components/governance/dashboard/WidgetErrorBoundary";
import {
  getOperationalReadiness,
  type OperationalReadinessResponse,
} from "@/lib/api/governance";

/**
 * Operational readiness view page (US4).
 * PPRR phases, emergency plans, exercises, capability gaps, role coverage.
 */
export default function ReadinessPage() {
  const [data, setData] = useState<OperationalReadinessResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOperationalReadiness()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="h-64 animate-pulse rounded-lg bg-gray-200" />;
  }

  if (!data) {
    return <p className="text-gray-500">Failed to load readiness data.</p>;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-gray-900">Operational Readiness</h2>

      {/* PPRR Phases */}
      <WidgetErrorBoundary widgetName="PPRR Phases">
        <PPRRPhaseIndicator phases={data.pprr_phases} />
      </WidgetErrorBoundary>

      {/* Emergency Plans */}
      <WidgetErrorBoundary widgetName="Emergency Plans">
        <EmergencyPlanStatus
          plans={data.emergency_plans}
          totalPlans={data.total_plans}
          overdueTotal={data.overdue_plans_total}
        />
      </WidgetErrorBoundary>

      {/* Exercise Completion & Capability Gaps */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <WidgetErrorBoundary widgetName="Exercise Completion">
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-900">
              Exercise Completion Rate
            </h3>
            <p className="text-3xl font-bold text-blue-700">
              {data.exercise_completion_rate_pct.toFixed(1)}%
            </p>
            <div className="mt-3 space-y-2">
              {data.exercise_breakdown.map((ex: Record<string, unknown>, i: number) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 capitalize">{String(ex.type)}</span>
                  <span className="font-medium">{String(ex.rate)}%</span>
                </div>
              ))}
            </div>
          </div>
        </WidgetErrorBoundary>

        <WidgetErrorBoundary widgetName="Capability Gaps">
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-900">
              Capability Gaps
            </h3>
            <p className={`text-3xl font-bold ${data.capability_gap_count > 0 ? "text-red-700" : "text-green-700"}`}>
              {data.capability_gap_count}
            </p>
            <p className="mt-1 text-xs text-gray-500">
              {data.capability_gap_count === 0
                ? "No capability gaps identified"
                : `${data.capability_gap_count} gap${data.capability_gap_count !== 1 ? "s" : ""} require attention`}
            </p>
            {data.capability_gaps && data.capability_gaps.length > 0 && (
              <table className="mt-3 min-w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="px-2 py-1.5 text-left font-medium text-gray-700">Type</th>
                    <th className="px-2 py-1.5 text-left font-medium text-gray-700">Description</th>
                    <th className="px-2 py-1.5 text-left font-medium text-gray-700">Severity</th>
                    <th className="px-2 py-1.5 text-left font-medium text-gray-700">Affected Roles</th>
                  </tr>
                </thead>
                <tbody>
                  {data.capability_gaps.map((gap: { gap_type: string; description: string; severity: string; affected_roles: string[] }, i: number) => (
                    <tr key={i} className="border-b">
                      <td className="px-2 py-1.5 capitalize">{gap.gap_type}</td>
                      <td className="px-2 py-1.5">{gap.description}</td>
                      <td className="px-2 py-1.5">
                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${
                          gap.severity === "critical" ? "bg-red-100 text-red-800"
                            : gap.severity === "high" ? "bg-orange-100 text-orange-800"
                              : gap.severity === "medium" ? "bg-yellow-100 text-yellow-800"
                                : "bg-green-100 text-green-800"
                        }`}>
                          {gap.severity}
                        </span>
                      </td>
                      <td className="px-2 py-1.5 text-gray-600">
                        {gap.affected_roles.map((r: string) => r.replace(/_/g, " ")).join(", ")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </WidgetErrorBoundary>
      </div>

      {/* AIIMS Role Coverage */}
      <WidgetErrorBoundary widgetName="Role Coverage">
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900">
              AIIMS Role Coverage
            </h3>
            <span className="text-sm font-bold text-gray-700">
              Overall: {data.overall_role_coverage_pct.toFixed(1)}%
            </span>
          </div>
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="px-3 py-2 text-left font-medium text-gray-700">Role</th>
                <th className="px-3 py-2 text-center font-medium text-gray-700">Assigned</th>
                <th className="px-3 py-2 text-center font-medium text-gray-700">Required</th>
                <th className="px-3 py-2 text-center font-medium text-gray-700">Coverage</th>
              </tr>
            </thead>
            <tbody>
              {data.aiims_role_coverage.map((role) => (
                <tr key={role.role} className="border-b">
                  <td className="px-3 py-2 capitalize">
                    {role.role.replace(/_/g, " ")}
                  </td>
                  <td className="px-3 py-2 text-center">{role.assigned_count}</td>
                  <td className="px-3 py-2 text-center">{role.required_count}</td>
                  <td className="px-3 py-2 text-center">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        role.is_staffed
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {role.coverage_pct.toFixed(0)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </WidgetErrorBoundary>

      {/* Volunteer Workforce Readiness */}
      {data.volunteer_readiness && (
        <WidgetErrorBoundary widgetName="Volunteer Readiness">
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <h3 className="mb-3 text-sm font-semibold text-gray-900">
              Volunteer Workforce Readiness
            </h3>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
              <div className="rounded-lg bg-blue-50 p-3 text-center">
                <p className="text-2xl font-bold text-blue-700">
                  {data.volunteer_readiness.total_registered}
                </p>
                <p className="text-xs text-gray-600">Registered</p>
              </div>
              <div className="rounded-lg bg-green-50 p-3 text-center">
                <p className="text-2xl font-bold text-green-700">
                  {data.volunteer_readiness.currently_available}
                </p>
                <p className="text-xs text-gray-600">Available</p>
              </div>
              <div className="rounded-lg bg-orange-50 p-3 text-center">
                <p className="text-2xl font-bold text-orange-700">
                  {data.volunteer_readiness.active_deployed}
                </p>
                <p className="text-xs text-gray-600">Deployed</p>
              </div>
              <div className="rounded-lg bg-purple-50 p-3 text-center">
                <p className="text-2xl font-bold text-purple-700">
                  {data.volunteer_readiness.availability_rate_pct.toFixed(1)}%
                </p>
                <p className="text-xs text-gray-600">Availability Rate</p>
              </div>
              <div className="rounded-lg bg-gray-50 p-3 text-center">
                <p className="text-2xl font-bold text-gray-700">
                  {data.volunteer_readiness.welfare_check_compliance_pct.toFixed(1)}%
                </p>
                <p className="text-xs text-gray-600">Welfare Compliance</p>
              </div>
            </div>
          </div>
        </WidgetErrorBoundary>
      )}
    </div>
  );
}
