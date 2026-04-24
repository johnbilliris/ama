"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listSimulations, pauseSimulation, resumeSimulation, archiveSimulation, deleteSimulation, type SimulationSummary } from "@/lib/api/simulations";

export default function SimulationListPage() {
  const [simulations, setSimulations] = useState<SimulationSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");

  const reload = () => {
    setLoading(true);
    listSimulations(statusFilter || undefined)
      .then((data) => {
        setSimulations(data.simulations);
        setTotal(data.total);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { reload(); }, [statusFilter]);

  if (loading) return <div className="p-6">Loading simulations...</div>;

  return (
    <div className="mx-auto max-w-6xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Simulation Exercises</h1>
        <Link
          href="/simulations/create"
          className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
        >
          Create Simulation
        </Link>
      </div>

      <div className="mb-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
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

      {simulations.length === 0 ? (
        <p className="text-gray-500">No simulation exercises found.</p>
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
                    <button onClick={() => pauseSimulation(sim.tenant_id).then(reload)} className="rounded bg-yellow-500 px-2 py-0.5 text-xs text-white">Pause</button>
                  )}
                  {sim.status === "Paused" && (
                    <button onClick={() => resumeSimulation(sim.tenant_id).then(reload)} className="rounded bg-green-500 px-2 py-0.5 text-xs text-white">Resume</button>
                  )}
                  {(sim.status === "Active" || sim.status === "Paused") && (
                    <button onClick={() => archiveSimulation(sim.tenant_id).then(reload)} className="rounded bg-orange-500 px-2 py-0.5 text-xs text-white">Archive</button>
                  )}
                  {sim.status === "Archived" && (
                    <button onClick={() => { if (confirm("Delete this simulation?")) deleteSimulation(sim.tenant_id).then(reload); }} className="rounded bg-red-500 px-2 py-0.5 text-xs text-white">Delete</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
