"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
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

  useEffect(() => {
    if (!params.dataSourceId) return;
    fetch(`/api/v1/data-sources/${params.dataSourceId}/compliance`)
      .then((r) => r.json())
      .then((data) => {
        setCurrent(data.current_assessments ?? []);
        setHistorical(data.historical_assessments ?? []);
      })
      .catch(() => {});
  }, [params.dataSourceId]);

  return (
    <div className="mx-auto max-w-4xl p-6">
      <h1 className="mb-6 text-2xl font-bold">Constitutional Compliance</h1>
      <h2 className="mb-4 text-lg font-semibold">Current Assessments</h2>
      <div className="mb-8 grid gap-4">
        {current.length === 0 && <p className="text-gray-500">No assessments recorded yet.</p>}
        {current.map((a) => (
          <ComplianceCard key={a.assessment_id} assessment={a} />
        ))}
      </div>
      {historical.length > 0 && (
        <>
          <h2 className="mb-4 text-lg font-semibold">Historical Assessments</h2>
          <div className="grid gap-4 opacity-60">
            {historical.map((a) => (
              <ComplianceCard key={a.assessment_id} assessment={a} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
