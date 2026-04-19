"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  getSimulation,
  pauseSimulation,
  resumeSimulation,
  archiveSimulation,
  type SimulationDetail,
} from "@/lib/api/simulations";
import { SimulationBanner } from "@/components/simulation-banner";
import { SimulationChatPane } from "@/components/simulation-chat-pane";

export default function SimulationDashboardPage() {
  const { tenantId } = useParams<{ tenantId: string }>();
  const [tenant, setTenant] = useState<SimulationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [personaFilter, setPersonaFilter] = useState<string>("");

  useEffect(() => {
    if (!tenantId) return;
    getSimulation(tenantId)
      .then(setTenant)
      .catch((err) => setError(err.message));
  }, [tenantId]);

  if (error) return <div className="p-6 text-red-600">Error: {error}</div>;
  if (!tenant) return <div className="p-6">Loading simulation dashboard...</div>;

  return (
    <>
      <SimulationBanner />
      <div className="mx-auto max-w-6xl p-6" style={{ marginTop: "40px" }}>
        <h1 className="mb-2 text-2xl font-bold">Simulation Dashboard</h1>
        <p className="mb-6 text-sm text-gray-500">
          Tenant: {tenant.tenant_id} | Scenario: {tenant.scenario_type} | Status: {tenant.status}
        </p>

        <div className="mb-4 flex items-center gap-2">
          <label htmlFor="persona-filter" className="text-sm font-medium">Workspace scope:</label>
          <select
            id="persona-filter"
            value={personaFilter}
            onChange={(e) => setPersonaFilter(e.target.value)}
            className="rounded border px-2 py-1 text-sm"
          >
            <option value="">All participants</option>
            <option value="incident-commander">Incident Commander</option>
            <option value="operations-officer">Operations Officer</option>
            <option value="planning-officer">Planning Officer</option>
            <option value="logistics-officer">Logistics Officer</option>
            <option value="public-info-officer">Public Information Officer</option>
          </select>
        </div>

        <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
          <StatCard label="Signals" value={tenant.resource_consumption.signal_count} limit={tenant.resource_limits.max_signals} />
          <StatCard label="Recommendations" value={tenant.resource_consumption.recommendation_count} limit={tenant.resource_limits.max_recommendations} />
          <StatCard label="Storage" value={`${(tenant.resource_consumption.storage_bytes / 1024).toFixed(1)} KB`} />
          <StatCard label="Participants" value={tenant.participants.length} />
        </div>

        <div className="mb-6 rounded border p-4">
          <h2 className="mb-2 text-lg font-semibold">Tenant Details</h2>
          <dl className="grid grid-cols-2 gap-2 text-sm">
            <dt className="font-medium">Created by</dt>
            <dd>{tenant.created_by}</dd>
            <dt className="font-medium">Created at</dt>
            <dd>{new Date(tenant.created_at).toLocaleString()}</dd>
            <dt className="font-medium">Expires at</dt>
            <dd>{new Date(tenant.expires_at).toLocaleString()}</dd>
            <dt className="font-medium">TTL</dt>
            <dd>{tenant.ttl_hours}h</dd>
            <dt className="font-medium">Throttle mode</dt>
            <dd>{tenant.throttle_mode} ({tenant.throttle_quota_pct}%)</dd>
            <dt className="font-medium">Jurisdictions</dt>
            <dd>{tenant.jurisdictions.join(", ") || "—"}</dd>
          </dl>
        </div>

        <div className="rounded border p-4">
          <h2 className="mb-2 text-lg font-semibold">Participants ({tenant.participants.length})</h2>
          <ul className="list-inside list-disc text-sm">
            {tenant.participants.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        </div>

        <div className="mt-6 flex gap-2">
          <button
            type="button"
            className="rounded bg-amber-500 px-3 py-1 text-sm font-medium text-white disabled:opacity-40"
            disabled={tenant.status !== "active"}
            onClick={async () => {
              await pauseSimulation(tenant.tenant_id);
              setTenant({ ...tenant, status: "paused" });
            }}
          >
            Pause
          </button>
          <button
            type="button"
            className="rounded bg-emerald-600 px-3 py-1 text-sm font-medium text-white disabled:opacity-40"
            disabled={tenant.status !== "paused"}
            onClick={async () => {
              await resumeSimulation(tenant.tenant_id);
              setTenant({ ...tenant, status: "active" });
            }}
          >
            Resume
          </button>
          <button
            type="button"
            className="rounded bg-red-600 px-3 py-1 text-sm font-medium text-white disabled:opacity-40"
            disabled={!["active", "paused"].includes(tenant.status)}
            onClick={async () => {
              if (!window.confirm("Stop this simulation? This is terminal.")) return;
              await archiveSimulation(tenant.tenant_id);
              setTenant({ ...tenant, status: "archiving" });
            }}
          >
            Stop
          </button>
        </div>

        <div className="mt-6">
          <h2 className="mb-2 text-lg font-semibold">Simulation Controller</h2>
          <SimulationChatPane tenantId={tenant.tenant_id} />
        </div>
      </div>
    </>
  );
}

function StatCard({ label, value, limit }: { label: string; value: string | number; limit?: number }) {
  return (
    <div className="rounded border p-3">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-xl font-bold">
        {value}
        {limit !== undefined && <span className="text-sm font-normal text-gray-400"> / {limit}</span>}
      </p>
    </div>
  );
}
