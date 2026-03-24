"use client";

import { useEffect, useState } from "react";
import { GovernanceSummary } from "@/components/governance/GovernanceSummary";
import { DataSourceTable } from "@/components/governance/DataSourceTable";

interface DashboardData {
  summary: {
    total_sources: number;
    compliant: number;
    partially_compliant: number;
    non_compliant: number;
    unassessed: number;
    compliance_lapsed: number;
    assigned: number;
    unassigned: number;
    fully_governed: number;
    rereview_pending: number;
  };
}

export default function GovernanceDashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);

  useEffect(() => {
    fetch("/api/v1/governance/dashboard")
      .then((r) => r.json())
      .then(setDashboard)
      .catch(() => {});
  }, []);

  if (!dashboard) return <div className="p-6">Loading governance dashboard...</div>;

  const hasGaps = dashboard.summary.unassessed > 0 || dashboard.summary.unassigned > 0;

  return (
    <div className="mx-auto max-w-6xl p-6">
      <h1 className="mb-6 text-2xl font-bold">Data Source Governance Dashboard</h1>

      <GovernanceSummary summary={dashboard.summary} />

      {hasGaps && (
        <div className="mt-4 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800">
          Governance gaps detected: {dashboard.summary.unassessed} source(s) without assessments,{" "}
          {dashboard.summary.unassigned} source(s) without agent assignments.
        </div>
      )}

      {dashboard.summary.compliance_lapsed > 0 && (
        <div className="mt-2 rounded-lg border border-orange-300 bg-orange-50 p-3 text-sm text-orange-800">
          {dashboard.summary.compliance_lapsed} source(s) in compliance-lapsed state with active grace period.
        </div>
      )}

      <div className="mt-6">
        <h2 className="mb-4 text-lg font-semibold">Data Sources</h2>
        <DataSourceTable />
      </div>
    </div>
  );
}
