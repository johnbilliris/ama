"use client";

import { useEffect, useState } from "react";
import { ComplianceMatrix } from "@/components/governance/dashboard/ComplianceMatrix";
import { WidgetErrorBoundary } from "@/components/governance/dashboard/WidgetErrorBoundary";
import {
  getComplianceMatrix,
  getComplianceDetail,
  type ComplianceMatrixResponse,
  type ComplianceDetailResponse,
} from "@/lib/api/governance";

/**
 * Compliance matrix view page (US2).
 */
export default function CompliancePage() {
  const [data, setData] = useState<ComplianceMatrixResponse | null>(null);
  const [detail, setDetail] = useState<ComplianceDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<Record<string, string | undefined>>({});

  const fetchData = async (params?: Record<string, string | undefined>) => {
    try {
      setLoading(true);
      const cleanParams: Record<string, string> = {};
      if (params) {
        Object.entries(params).forEach(([k, v]) => {
          if (v) cleanParams[k] = v;
        });
      }
      const result = await getComplianceMatrix(cleanParams);
      setData(result);
    } catch {
      // Error handled by boundary
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleFilter = (newFilters: { compliance_status?: string; category?: string }) => {
    const merged = { ...filters, ...newFilters };
    setFilters(merged);
    fetchData(merged);
  };

  const handleSort = (sortBy: string, sortDir: string) => {
    fetchData({ ...filters, sort_by: sortBy, sort_dir: sortDir });
  };

  const handlePageNext = (token: string) => {
    fetchData({ ...filters, continuation_token: token });
  };

  const handleRowClick = async (dataSourceId: string) => {
    try {
      const d = await getComplianceDetail(dataSourceId);
      setDetail(d);
    } catch {
      // silently fail
    }
  };

  if (loading && !data) {
    return <div className="h-64 animate-pulse rounded-lg bg-gray-200" />;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-gray-900">Compliance Matrix</h2>

      <WidgetErrorBoundary widgetName="Compliance Matrix">
        {data && (
          <ComplianceMatrix
            entries={data.entries}
            totalCount={data.total_count}
            continuationToken={data.continuation_token}
            onFilter={handleFilter}
            onSort={handleSort}
            onPageNext={handlePageNext}
            onRowClick={handleRowClick}
          />
        )}
      </WidgetErrorBoundary>

      {/* Detail slide-out */}
      {detail && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900">
              {detail.data_source_name}
            </h3>
            <button
              onClick={() => setDetail(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          <p className="mt-2 text-sm text-gray-600">
            Status: {detail.compliance_status}
          </p>
          {detail.assessment_history.length > 0 && (
            <div className="mt-3">
              <h4 className="text-xs font-semibold text-gray-700">Assessment History</h4>
              <ul className="mt-1 list-inside list-disc text-xs text-gray-600">
                {detail.assessment_history.map((h, i) => (
                  <li key={i}>{JSON.stringify(h)}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
