"use client";

import { useEffect, useState } from "react";

interface DataSourceEntry {
  data_source_id: string;
  name: string;
  kind: string;
  sub_category: string;
  provider: string;
  trust_tier: string;
  status: string;
  compliance_status: string;
  governance_status: string;
  geographic_coverage: string;
}

const KIND_OPTIONS = [
  "authoritative", "sensor", "iot", "field_report", "social", "community", "derived",
] as const;

const TRUST_TIER_LABELS: Record<string, string> = {
  tier_1_authoritative_government: "Tier 1 — Authoritative Government",
  tier_2_verified_institutional: "Tier 2 — Verified Institutional",
  tier_3_operational_sensor: "Tier 3 — Operational Sensor",
  tier_4_field_reports: "Tier 4 — Field Reports",
  tier_5_community_volunteer: "Tier 5 — Community/Volunteer",
  tier_6_social_unverified: "Tier 6 — Social/Unverified",
  tier_7_derived_computed: "Tier 7 — Derived/Computed",
};

interface DataSourceTableProps {
  apiBase?: string;
}

export function DataSourceTable({ apiBase = "/api/v1" }: DataSourceTableProps) {
  const [sources, setSources] = useState<DataSourceEntry[]>([]);
  const [kindFilter, setKindFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");

  useEffect(() => {
    const params = new URLSearchParams();
    if (kindFilter) params.set("kind", kindFilter);
    if (statusFilter) params.set("status", statusFilter);
    fetch(`${apiBase}/data-sources?${params}`)
      .then((r) => r.json())
      .then(setSources)
      .catch(() => setSources([]));
  }, [apiBase, kindFilter, statusFilter]);

  return (
    <div>
      <div className="mb-4 flex gap-4">
        <select
          value={kindFilter}
          onChange={(e) => setKindFilter(e.target.value)}
          className="rounded border px-2 py-1"
          aria-label="Filter by kind"
        >
          <option value="">All categories</option>
          {KIND_OPTIONS.map((k) => (
            <option key={k} value={k}>{k}</option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded border px-2 py-1"
          aria-label="Filter by status"
        >
          <option value="">All statuses</option>
          <option value="available">Available</option>
          <option value="degraded">Degraded</option>
          <option value="offline">Offline</option>
          <option value="deactivated">Deactivated</option>
        </select>
      </div>
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b font-medium">
            <th className="py-2">Name</th>
            <th>Kind</th>
            <th>Provider</th>
            <th>Trust Tier</th>
            <th>Coverage</th>
            <th>Status</th>
            <th>Compliance</th>
            <th>Governance</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((s) => (
            <tr key={s.data_source_id} className="border-b">
              <td className="py-1">
                <a href={`/governance/${s.data_source_id}/compliance`} className="text-blue-600 underline">
                  {s.name}
                </a>
              </td>
              <td>{s.kind}</td>
              <td>{s.provider}</td>
              <td>{TRUST_TIER_LABELS[s.trust_tier] ?? s.trust_tier}</td>
              <td>{s.geographic_coverage}</td>
              <td>{s.status}</td>
              <td>{s.compliance_status}</td>
              <td>{s.governance_status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
