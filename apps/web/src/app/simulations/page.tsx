"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { listSimulations, pauseSimulation, resumeSimulation, archiveSimulation, deleteSimulation, type SimulationSummary } from "@/lib/api/simulations";

const PAGE_SIZE = 20;

export default function SimulationListPage() {
  const [simulations, setSimulations] = useState<SimulationSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const reload = useCallback(() => {
    setLoading(true);
    setError(null);
    listSimulations(statusFilter || undefined, PAGE_SIZE, offset)
      .then((data) => {
        setSimulations(data.simulations);
        setTotal(data.total);
      })
      .catch((err: Error) => {
        setSimulations([]);
        setTotal(0);
        setError(err.message);
      })
      .finally(() => setLoading(false));
  }, [statusFilter, offset]);

  useEffect(() => { reload(); }, [reload]);

  const runAction = (action: Promise<unknown>) => {
    setActionError(null);
    action.then(reload).catch((err: Error) => setActionError(err.message));
  };

  const onFilterChange = (value: string) => {
    setOffset(0);
    setStatusFilter(value);
  };

  const rangeStart = total === 0 ? 0 : offset + 1;
  const rangeEnd = offset + simulations.length;
  const hasPrev = offset > 0;
  const hasNext = offset + PAGE_SIZE < total;

  return (
    <div className="mx-auto max-w-6xl p-6">
      <header className="preparedness-header mb-5">
        <p className="preparedness-kicker">Simulations</p>
        <h1 className="preparedness-title">Simulation Dashboard</h1>
        <p className="preparedness-copy">
          Create, control, and review simulation exercises across tenants —
          manage warp speeds, pause or archive runs, and inspect historical
          scenario activity.
        </p>
      </header>

      <div className="mb-4 flex items-center justify-between">
        <div>
          <select
            value={statusFilter}
            onChange={(e) => onFilterChange(e.target.value)}
            className="rounded border px-3 py-1"
            aria-label="Filter by status"
          >
            <option value="">All statuses</option>
            <option value="Active">Active</option>
            <option value="Paused">Paused</option>
            <option value="Archived">Archived</option>
          </select>
          <span className="ml-2 text-sm text-gray-500">{total} total</span>
        </div>
        <Link
          href="/simulations/create"
          className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
        >
          Create Simulation
        </Link>
      </div>

      {error && (
        <div role="alert" data-testid="sim-list-error" className="mb-4 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800">
          <p className="font-semibold">Could not load simulations.</p>
          <p className="mt-1 break-words">{error}</p>
          <button type="button" onClick={reload} className="mt-2 rounded bg-red-600 px-3 py-1 text-xs text-white">
            Retry
          </button>
        </div>
      )}

      {actionError && (
        <div role="alert" data-testid="sim-action-error" className="mb-4 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800">
          {actionError}
        </div>
      )}

      {loading ? (
        <p data-testid="sim-list-loading">Loading simulations…</p>
      ) : simulations.length === 0 ? (
        !error && <p className="text-gray-500">No simulation exercises found.</p>
      ) : (
        <table className="w-full table-auto border-collapse text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="p-2">Tenant ID</th>
              <th className="p-2">Scenario</th>
              <th className="p-2">Warp</th>
              <th className="p-2">Status</th>
              <th className="p-2">Created</th>
              <th className="p-2">Participants</th>
              <th className="p-2">Signals</th>
              <th className="p-2">Storage</th>
              <th className="p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {simulations.map((sim) => (
              <tr key={sim.tenant_id} className="border-b hover:bg-gray-50">
                <td className="p-2">
                  <Link href={`/simulations/${sim.tenant_id}`} className="text-blue-600 hover:underline">
                    {sim.tenant_id.slice(0, 12)}…
                  </Link>
                </td>
                <td className="p-2">{sim.scenario_type}</td>
                <td className="p-2">
                  <span className="rounded bg-indigo-100 px-2 py-0.5 text-xs font-semibold text-indigo-800">
                    {sim.current_warp_speed ?? 1}×
                  </span>
                </td>
                <td className="p-2">
                  <span className={`rounded px-2 py-0.5 text-xs font-medium ${
                    sim.status === "Active" ? "bg-green-100 text-green-800" :
                    sim.status === "Paused" ? "bg-yellow-100 text-yellow-800" :
                    "bg-gray-100 text-gray-800"
                  }`}>
                    {sim.status}
                  </span>
                </td>
                <td className="p-2">{new Date(sim.created_at).toLocaleDateString()}</td>
                <td className="p-2">{sim.participant_count}</td>
                <td className="p-2">{sim.signal_count}</td>
                <td className="p-2">{(sim.storage_bytes / 1024).toFixed(1)} KB</td>
                <td className="p-2 space-x-1">
                  {sim.status === "Active" && (
                    <button onClick={() => runAction(pauseSimulation(sim.tenant_id))} className="rounded bg-yellow-500 px-2 py-0.5 text-xs text-white">Pause</button>
                  )}
                  {sim.status === "Paused" && (
                    <button onClick={() => runAction(resumeSimulation(sim.tenant_id))} className="rounded bg-green-500 px-2 py-0.5 text-xs text-white">Resume</button>
                  )}
                  {(sim.status === "Active" || sim.status === "Paused") && (
                    <button onClick={() => runAction(archiveSimulation(sim.tenant_id))} className="rounded bg-orange-500 px-2 py-0.5 text-xs text-white">Archive</button>
                  )}
                  {sim.status === "Archived" && (
                    <button onClick={() => { if (confirm("Delete this simulation?")) runAction(deleteSimulation(sim.tenant_id)); }} className="rounded bg-red-500 px-2 py-0.5 text-xs text-white">Delete</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <nav className="mt-4 flex items-center gap-3 text-sm" aria-label="Simulation list pagination">
        <button
          type="button"
          data-testid="sim-page-prev"
          onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}
          disabled={!hasPrev || loading}
          className="rounded border px-3 py-1 disabled:opacity-40"
        >
          Previous
        </button>
        <span data-testid="sim-page-range">
          {rangeStart}–{rangeEnd} of {total}
        </span>
        <button
          type="button"
          data-testid="sim-page-next"
          onClick={() => setOffset((o) => o + PAGE_SIZE)}
          disabled={!hasNext || loading}
          className="rounded border px-3 py-1 disabled:opacity-40"
        >
          Next
        </button>
      </nav>
    </div>
  );
}
