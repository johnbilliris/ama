"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { HandoffChainEditor } from "@/components/governance/HandoffChainEditor";

interface Assignment {
  assignment_id: string;
  agent_name: string;
  role: string;
  scope_of_responsibility: string;
  status: string;
}

interface Chain {
  chain_id: string;
  steps: { step_order: number; source_agent: string; target_agent: string; confidence_threshold: number | null }[];
  status: string;
}

export default function AssignmentsPage() {
  const params = useParams<{ dataSourceId: string }>();
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [chain, setChain] = useState<Chain | null>(null);

  const load = () => {
    if (!params.dataSourceId) return;
    fetch(`/api/v1/data-sources/${params.dataSourceId}/governance`)
      .then((r) => r.json())
      .then((data) => {
        setAssignments(data.assignments ?? []);
        setChain(data.handoff_chain ?? null);
      })
      .catch(() => {});
  };

  useEffect(load, [params.dataSourceId]);

  return (
    <div className="mx-auto max-w-4xl p-6">
      <h1 className="mb-6 text-2xl font-bold">Agent Governance</h1>

      <h2 className="mb-4 text-lg font-semibold">Assignments</h2>
      {assignments.length === 0 && <p className="mb-4 text-gray-500">No agents assigned yet.</p>}
      <div className="mb-8 space-y-2">
        {assignments.map((a) => (
          <div key={a.assignment_id} className="flex items-center gap-3 rounded border p-3">
            <span className="font-medium">{a.agent_name}</span>
            <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-800">{a.role}</span>
            <span className="text-sm text-gray-600">{a.scope_of_responsibility}</span>
          </div>
        ))}
      </div>

      <h2 className="mb-4 text-lg font-semibold">Handoff Chain</h2>
      {chain && (
        <div className="mb-4 rounded border p-3">
          <div className="flex items-center gap-2 text-sm">
            {chain.steps.map((s, i) => (
              <span key={i}>
                <span className="font-medium">{s.source_agent}</span>
                <span className="mx-1 text-gray-400">&rarr;</span>
                <span className="font-medium">{s.target_agent}</span>
                {s.confidence_threshold != null && (
                  <span className="ml-1 text-xs text-gray-500">(&ge;{s.confidence_threshold})</span>
                )}
                {i < chain.steps.length - 1 && <span className="mx-2 text-gray-300">|</span>}
              </span>
            ))}
          </div>
        </div>
      )}

      <HandoffChainEditor dataSourceId={params.dataSourceId ?? ""} onSaved={load} />
    </div>
  );
}
