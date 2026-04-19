"use client";

import type { ComplianceMatrixEntry } from "@/lib/api/governance";
import { useState } from "react";

interface ComplianceMatrixProps {
  entries: ComplianceMatrixEntry[];
  totalCount: number;
  continuationToken: string | null;
  onFilter: (filters: { compliance_status?: string; category?: string }) => void;
  onSort: (sortBy: string, sortDir: string) => void;
  onPageNext: (token: string) => void;
  onRowClick: (dataSourceId: string) => void;
}

const STATUS_BADGE: Record<string, { bg: string; text: string; label: string }> = {
  compliant: { bg: "bg-green-100", text: "text-green-800", label: "Compliant" },
  non_compliant: { bg: "bg-red-100", text: "text-red-800", label: "Non-Compliant" },
  pending: { bg: "bg-gray-100", text: "text-gray-800", label: "Pending" },
  grace_period: { bg: "bg-orange-100", text: "text-orange-800", label: "Grace Period" },
};

/**
 * Sortable compliance matrix table with filter toolbar and pagination (US2).
 */
export function ComplianceMatrix({
  entries,
  totalCount,
  continuationToken,
  onFilter,
  onSort,
  onPageNext,
  onRowClick,
}: ComplianceMatrixProps) {
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [sortBy, setSortBy] = useState<string>("");
  const [sortDir, setSortDir] = useState<string>("asc");

  const handleSort = (column: string) => {
    const newDir = sortBy === column && sortDir === "asc" ? "desc" : "asc";
    setSortBy(column);
    setSortDir(newDir);
    onSort(column, newDir);
  };

  return (
    <div>
      {/* Filter toolbar */}
      <div className="mb-4 flex flex-wrap gap-3">
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            onFilter({ compliance_status: e.target.value || undefined, category: categoryFilter || undefined });
          }}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          aria-label="Filter by compliance status"
        >
          <option value="">All Statuses</option>
          <option value="compliant">Compliant</option>
          <option value="non_compliant">Non-Compliant</option>
          <option value="pending">Pending</option>
          <option value="grace_period">Grace Period</option>
        </select>
        <select
          value={categoryFilter}
          onChange={(e) => {
            setCategoryFilter(e.target.value);
            onFilter({ compliance_status: statusFilter || undefined, category: e.target.value || undefined });
          }}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          aria-label="Filter by category"
        >
          <option value="">All Categories</option>
          <option value="authoritative">Authoritative</option>
          <option value="sensor">Sensor</option>
          <option value="community">Community</option>
          <option value="derived">Derived</option>
        </select>
        <span className="self-center text-xs text-gray-500">
          {totalCount} source{totalCount !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b bg-gray-50">
              {[
                { key: "data_source_name", label: "Source Name" },
                { key: "compliance_status", label: "Status" },
                { key: "last_assessment_date", label: "Last Assessment" },
                { key: "next_assessment_due_date", label: "Next Due" },
                { key: "governance_gap_count", label: "Gaps" },
                { key: "grace_period_countdown_days", label: "Grace Period" },
              ].map(({ key, label }) => (
                <th
                  key={key}
                  className="cursor-pointer px-3 py-2 text-left font-medium text-gray-700 hover:text-blue-600"
                  onClick={() => handleSort(key)}
                  aria-sort={sortBy === key ? (sortDir === "asc" ? "ascending" : "descending") : "none"}
                >
                  {label}
                  {sortBy === key && (
                    <span className="ml-1">{sortDir === "asc" ? "↑" : "↓"}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => {
              const badge = STATUS_BADGE[entry.compliance_status] ?? STATUS_BADGE.pending;
              return (
                <tr
                  key={entry.data_source_id}
                  className="cursor-pointer border-b hover:bg-blue-50"
                  onClick={() => onRowClick(entry.data_source_id)}
                  role="button"
                  tabIndex={0}
                  aria-label={`View details for ${entry.data_source_name}`}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") onRowClick(entry.data_source_id);
                  }}
                >
                  <td className="px-3 py-2 font-medium">{entry.data_source_name}</td>
                  <td className="px-3 py-2">
                    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${badge.bg} ${badge.text}`}>
                      {badge.label}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-gray-600">
                    {entry.last_assessment_date
                      ? new Date(entry.last_assessment_date).toLocaleDateString()
                      : "—"}
                  </td>
                  <td className="px-3 py-2 text-gray-600">
                    {entry.next_assessment_due_date
                      ? new Date(entry.next_assessment_due_date).toLocaleDateString()
                      : "—"}
                  </td>
                  <td className="px-3 py-2 text-center">
                    {entry.governance_gap_count > 0 ? (
                      <span className="font-medium text-red-600">{entry.governance_gap_count}</span>
                    ) : (
                      <span className="text-gray-400">0</span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    {entry.grace_period_countdown_days != null ? (
                      <span className="text-orange-600">
                        {entry.grace_period_countdown_days}d remaining
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              );
            })}
            {entries.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-8 text-center text-gray-500">
                  No data sources match the current filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {continuationToken && (
        <div className="mt-4 flex justify-center">
          <button
            onClick={() => onPageNext(continuationToken)}
            className="rounded-md bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 hover:bg-blue-100"
          >
            Load more
          </button>
        </div>
      )}
    </div>
  );
}
