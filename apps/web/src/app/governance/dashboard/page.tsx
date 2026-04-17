"use client";

import { useEffect, useState } from "react";
import { ConstitutionalGates } from "@/components/governance/dashboard/ConstitutionalGates";
import { DataFreshnessIndicator } from "@/components/governance/dashboard/DataFreshnessIndicator";
import { DegradedModeBanner } from "@/components/governance/dashboard/DegradedModeBanner";
import { RefreshControls } from "@/components/governance/dashboard/RefreshControls";
import { WidgetErrorBoundary } from "@/components/governance/dashboard/WidgetErrorBoundary";
import { HealthScoreGauge } from "@ama/ui/components/governance";
import {
  getExecutiveSummary,
  type ExecutiveSummaryResponse,
} from "@/lib/api/governance";

/**
 * Executive summary dashboard page (US1).
 * Displays health score gauge, 10 constitutional gates, active incidents,
 * resource utilisation, and risk summary.
 */
export default function ExecutiveSummaryPage() {
  const [data, setData] = useState<ExecutiveSummaryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [degradedSources, setDegradedSources] = useState<string[]>([]);

  const fetchData = async (bypassCache = false) => {
    try {
      setLoading(true);
      const result = await getExecutiveSummary(bypassCache);
      setData(result);
      setError(null);
      setDegradedSources([]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load data");
      setDegradedSources(["Executive summary service"]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    if (autoRefresh) {
      const interval = setInterval(() => fetchData(), 300000); // 5min default
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  if (loading && !data) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-32 animate-pulse rounded-lg bg-gray-200" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">Executive Summary</h2>
        <div className="flex items-center gap-3">
          {data && (
            <DataFreshnessIndicator
              timestamp={data.data_freshness}
              label="Dashboard data"
            />
          )}
          <RefreshControls
            pollIntervalMs={300000}
            autoRefresh={autoRefresh}
            onToggleAutoRefresh={() => setAutoRefresh((v) => !v)}
            onManualRefresh={() => fetchData(true)}
            refreshing={loading}
          />
        </div>
      </div>

      {/* Degraded mode banner */}
      <DegradedModeBanner degradedSources={degradedSources} />

      {error && !data && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      )}

      {data && (
        <>
          {/* Health Score + Key Metrics Row */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <WidgetErrorBoundary widgetName="Health Score">
              <HealthScoreGauge
                score={data.health_score.score}
                status={data.health_score.status}
                dimensions={data.health_score.dimensions}
              />
            </WidgetErrorBoundary>

            <WidgetErrorBoundary widgetName="Active Incidents">
              <div className="rounded-lg bg-blue-50 p-4">
                <h3 className="text-sm font-semibold text-gray-900">
                  Active Incidents
                </h3>
                <p className="mt-2 text-3xl font-bold text-blue-700">
                  {data.active_incident_count}
                </p>
              </div>
            </WidgetErrorBoundary>

            <WidgetErrorBoundary widgetName="Resource Utilisation">
              <div className="rounded-lg bg-purple-50 p-4">
                <h3 className="text-sm font-semibold text-gray-900">
                  Resource Utilisation
                </h3>
                <p className="mt-2 text-3xl font-bold text-purple-700">
                  {data.resource_utilisation_pct.toFixed(1)}%
                </p>
                <div className="mt-2 h-2 w-full rounded-full bg-gray-200">
                  <div
                    className="h-2 rounded-full bg-purple-500"
                    style={{ width: `${data.resource_utilisation_pct}%` }}
                  />
                </div>
              </div>
            </WidgetErrorBoundary>
          </div>

          {/* Constitutional Gates */}
          <WidgetErrorBoundary widgetName="Constitutional Gates">
            <ConstitutionalGates gates={data.constitutional_gates} />
          </WidgetErrorBoundary>

          {/* Risk Summary */}
          <WidgetErrorBoundary widgetName="Risk Summary">
            <div className="rounded-lg border border-gray-200 bg-white p-4">
              <h3 className="mb-3 text-sm font-semibold text-gray-900">
                Risk Summary by Severity
              </h3>
              <div className="grid grid-cols-4 gap-3">
                {Object.entries(data.risk_summary).map(([severity, count]) => (
                  <div
                    key={severity}
                    className={`rounded-lg p-3 text-center ${
                      severity === "extreme"
                        ? "bg-red-100 text-red-800"
                        : severity === "high"
                          ? "bg-orange-100 text-orange-800"
                          : severity === "medium"
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-green-100 text-green-800"
                    }`}
                  >
                    <p className="text-2xl font-bold">{count}</p>
                    <p className="text-xs font-medium capitalize">{severity}</p>
                  </div>
                ))}
              </div>
            </div>
          </WidgetErrorBoundary>
        </>
      )}
    </div>
  );
}
