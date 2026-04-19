"use client";

import { useEffect, useState } from "react";
import { RiskRegisterView } from "@/components/governance/dashboard/RiskRegisterView";
import { WarningCompliancePanel } from "@/components/governance/dashboard/WarningCompliancePanel";
import { WidgetErrorBoundary } from "@/components/governance/dashboard/WidgetErrorBoundary";
import {
  getRiskAndWarning,
  getRiskDetail,
  type RiskWarningResponse,
  type RiskDetailResponse,
} from "@/lib/api/governance";

/**
 * Risk & warning view page (US6).
 * Risk register, treatment closure, alert compliance, AWS principles.
 */
export default function RiskPage() {
  const [data, setData] = useState<RiskWarningResponse | null>(null);
  const [detail, setDetail] = useState<RiskDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getRiskAndWarning()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleRiskClick = async (riskId: string) => {
    try {
      const d = await getRiskDetail(riskId);
      setDetail(d);
    } catch {
      // silently fail
    }
  };

  if (loading) {
    return <div className="h-64 animate-pulse rounded-lg bg-gray-200" />;
  }

  if (!data) {
    return <p className="text-gray-500">Failed to load risk data.</p>;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-gray-900">Risk & Warning</h2>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Risk Register */}
        <WidgetErrorBoundary widgetName="Risk Register">
          <RiskRegisterView
            severity={data.risk_severity}
            treatmentClosureRatePct={data.treatment_closure_rate_pct}
            topRisks={data.top_risks as Array<{
              id: string;
              description: string;
              severity: string;
              treatment_due: string;
              responsible: string;
            }>}
            onRiskClick={handleRiskClick}
          />
        </WidgetErrorBoundary>

        {/* Warning Compliance */}
        <WidgetErrorBoundary widgetName="Warning Compliance">
          <WarningCompliancePanel alertCompliance={data.alert_compliance} />
        </WidgetErrorBoundary>
      </div>

      {/* Risk detail slide-out */}
      {detail && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900">
              {detail.risk_id}: {detail.description}
            </h3>
            <button
              onClick={() => setDetail(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          <div className="mt-2 grid grid-cols-3 gap-3 text-sm">
            <div>
              <span className="text-xs text-gray-500">Severity:</span>
              <p className="font-medium capitalize">{detail.severity}</p>
            </div>
            <div>
              <span className="text-xs text-gray-500">Likelihood:</span>
              <p className="font-medium capitalize">{detail.likelihood}</p>
            </div>
            <div>
              <span className="text-xs text-gray-500">Consequence:</span>
              <p className="font-medium capitalize">{detail.consequence}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
