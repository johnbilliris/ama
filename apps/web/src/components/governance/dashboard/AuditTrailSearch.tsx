"use client";

import type { AuditEventSummary } from "@/lib/api/governance";
import { useState } from "react";

interface AuditTrailSearchProps {
  events: AuditEventSummary[];
  totalCount: number;
  continuationToken: string | null;
  onSearch: (filters: Record<string, string>) => void;
  onPageNext: (token: string) => void;
  onEventClick: (eventId: string) => void;
  onExport: (selectedIds: string[]) => void;
}

/**
 * Audit trail search form with result table and row selection for export (US3).
 */
export function AuditTrailSearch({
  events,
  totalCount,
  continuationToken,
  onSearch,
  onPageNext,
  onEventClick,
  onExport,
}: AuditTrailSearchProps) {
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [actor, setActor] = useState("");
  const [actionType, setActionType] = useState("");
  const [keyword, setKeyword] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const handleSearch = () => {
    onSearch({
      ...(dateFrom ? { date_from: dateFrom } : {}),
      ...(dateTo ? { date_to: dateTo } : {}),
      ...(actor ? { actor } : {}),
      ...(actionType ? { action_type: actionType } : {}),
      ...(keyword ? { keyword } : {}),
    });
  };

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div>
      {/* Search form */}
      <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          aria-label="From date"
          placeholder="From"
        />
        <input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          aria-label="To date"
          placeholder="To"
        />
        <input
          type="text"
          value={actor}
          onChange={(e) => setActor(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          aria-label="Actor"
          placeholder="Actor"
        />
        <select
          value={actionType}
          onChange={(e) => setActionType(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          aria-label="Action type"
        >
          <option value="">All Actions</option>
          <option value="registered">Registered</option>
          <option value="assessment_created">Assessment</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="dashboard_view">Dashboard View</option>
          <option value="dashboard_export">Dashboard Export</option>
        </select>
        <input
          type="text"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          aria-label="Keyword search"
          placeholder="Keyword"
        />
        <button
          onClick={handleSearch}
          className="rounded-md bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
        >
          Search
        </button>
      </div>

      {/* Export button */}
      {selectedIds.size > 0 && (
        <div className="mb-3">
          <button
            onClick={() => onExport(Array.from(selectedIds))}
            className="rounded-md bg-green-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-green-700"
          >
            Export {selectedIds.size} selected
          </button>
        </div>
      )}

      {/* Results count */}
      <p className="mb-2 text-xs text-gray-500">{totalCount} result{totalCount !== 1 ? "s" : ""}</p>

      {/* Results table */}
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b bg-gray-50">
              <th className="px-2 py-2 text-left">
                <span className="sr-only">Select</span>
              </th>
              <th className="px-3 py-2 text-left font-medium text-gray-700">Timestamp</th>
              <th className="px-3 py-2 text-left font-medium text-gray-700">Actor</th>
              <th className="px-3 py-2 text-left font-medium text-gray-700">Action</th>
              <th className="px-3 py-2 text-left font-medium text-gray-700">Entity</th>
              <th className="px-3 py-2 text-left font-medium text-gray-700">Outcome</th>
              <th className="px-3 py-2 text-left font-medium text-gray-700">Chain</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event) => (
              <tr
                key={event.id}
                className="border-b hover:bg-blue-50"
              >
                <td className="px-2 py-2">
                  <input
                    type="checkbox"
                    checked={selectedIds.has(event.id)}
                    onChange={() => toggleSelect(event.id)}
                    aria-label={`Select event ${event.id}`}
                  />
                </td>
                <td className="px-3 py-2 text-gray-600 whitespace-nowrap">
                  {new Date(event.timestamp).toLocaleString()}
                </td>
                <td className="px-3 py-2">{event.actor}</td>
                <td className="px-3 py-2">
                  <span className="rounded bg-gray-100 px-2 py-0.5 text-xs">{event.action_type}</span>
                </td>
                <td className="px-3 py-2">{event.affected_entity}</td>
                <td className="px-3 py-2">{event.outcome}</td>
                <td className="px-3 py-2">
                  {event.has_decision_chain ? (
                    <button
                      onClick={() => onEventClick(event.id)}
                      className="text-blue-600 underline hover:text-blue-800 text-xs"
                    >
                      View chain
                    </button>
                  ) : (
                    <span className="text-gray-400 text-xs">—</span>
                  )}
                </td>
              </tr>
            ))}
            {events.length === 0 && (
              <tr>
                <td colSpan={7} className="px-3 py-8 text-center text-gray-500">
                  No audit events match the current search criteria.
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
