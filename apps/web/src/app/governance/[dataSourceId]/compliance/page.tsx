"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AssessmentForm } from "@/components/governance/AssessmentForm";
import { ComplianceCard } from "@/components/governance/ComplianceCard";

interface Assessment {
  assessment_id: string;
  principle: string;
  compliance_status: string;
  explanation: string;
  conditions: string[];
  gaps: string[];
  assessor_id: string;
  assessed_at: string;
  is_current: boolean;
}

export default function CompliancePage() {
  const params = useParams<{ dataSourceId: string }>();
  const [current, setCurrent] = useState<Assessment[]>([]);
  const [historical, setHistorical] = useState<Assessment[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!params.dataSourceId) return;
    try {
      const response = await fetch(
        `/api/data-sources/${encodeURIComponent(params.dataSourceId)}/compliance`,
      );
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        throw new Error(detail.detail || `Failed to load assessments: ${response.status}`);
      }
      const data = await response.json();
      setCurrent(data.current_assessments ?? []);
      setHistorical(data.historical_assessments ?? []);
      setLoadError(null);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Failed to load assessments.");
    }
  }, [params.dataSourceId]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="mx-auto max-w-4xl space-y-8 p-6">
      <div>
        <h1 className="text-2xl font-bold">Constitutional Compliance</h1>
        <p className="mt-1 text-sm text-gray-600">
          Data source: <span className="font-mono">{params.dataSourceId}</span>
        </p>
      </div>

      {params.dataSourceId && (
        <AssessmentForm dataSourceId={params.dataSourceId} onCreated={load} />
      )}

      <section>
        <h2 className="mb-4 text-lg font-semibold">Current Assessments</h2>
        {loadError && (
          <div role="alert" className="mb-4 rounded border border-red-200 bg-red-50 p-2 text-sm text-red-800">
            {loadError}
          </div>
        )}
        <div className="grid gap-4">
          {current.length === 0 && !loadError && (
            <p className="text-gray-500">No assessments recorded yet.</p>
          )}
          {current.map((a) => (
            <ComplianceCard key={a.assessment_id} assessment={a} />
          ))}
        </div>
      </section>

      {historical.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-semibold">Historical Assessments</h2>
          <div className="grid gap-4 opacity-60">
            {historical.map((a) => (
              <ComplianceCard key={a.assessment_id} assessment={a} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
