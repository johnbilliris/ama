"use client";

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

const PRINCIPLE_LABELS: Record<string, string> = {
  life_safety_first: "I. Life Safety First",
  multi_agent_coordination: "II. Multi-Agent Coordination",
  data_trust_provenance_freshness: "III. Data Trust, Provenance & Freshness",
  privacy_security_regional_policy: "IV. Privacy, Security & Regional Policy",
  multilingual_accessible_actionable: "V. Multilingual, Accessible & Actionable",
  cloud_platform: "VI. Cloud Platform",
};

const STATUS_COLORS: Record<string, string> = {
  compliant: "bg-green-100 text-green-800",
  partially_compliant: "bg-yellow-100 text-yellow-800",
  non_compliant: "bg-red-100 text-red-800",
  not_applicable: "bg-gray-100 text-gray-600",
};

interface ComplianceCardProps {
  assessment: Assessment;
}

export function ComplianceCard({ assessment }: ComplianceCardProps) {
  const colorClass = STATUS_COLORS[assessment.compliance_status] ?? "bg-gray-100";

  return (
    <div className="rounded-lg border p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="font-semibold">{PRINCIPLE_LABELS[assessment.principle] ?? assessment.principle}</h3>
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${colorClass}`}>
          {assessment.compliance_status.replace(/_/g, " ")}
        </span>
      </div>
      <p className="mb-2 text-sm text-gray-700">{assessment.explanation}</p>
      {assessment.gaps.length > 0 && (
        <div className="mb-2">
          <span className="text-xs font-medium text-red-700">Gaps:</span>
          <ul className="ml-4 list-disc text-xs text-red-600">
            {assessment.gaps.map((g, i) => <li key={i}>{g}</li>)}
          </ul>
        </div>
      )}
      {assessment.conditions.length > 0 && (
        <div>
          <span className="text-xs font-medium text-yellow-700">Conditions:</span>
          <ul className="ml-4 list-disc text-xs text-yellow-600">
            {assessment.conditions.map((c, i) => <li key={i}>{c}</li>)}
          </ul>
        </div>
      )}
      <div className="mt-2 text-xs text-gray-400">
        Assessed by {assessment.assessor_id} on {new Date(assessment.assessed_at).toLocaleDateString()}
      </div>
    </div>
  );
}
