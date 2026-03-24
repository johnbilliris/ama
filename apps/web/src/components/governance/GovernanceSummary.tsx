"use client";

interface DashboardSummary {
  total_sources: number;
  compliant: number;
  partially_compliant: number;
  non_compliant: number;
  unassessed: number;
  compliance_lapsed: number;
  assigned: number;
  unassigned: number;
  fully_governed: number;
  rereview_pending: number;
}

interface GovernanceSummaryProps {
  summary: DashboardSummary;
}

const STAT_CARDS: { key: keyof DashboardSummary; label: string; color: string }[] = [
  { key: "total_sources", label: "Total Sources", color: "bg-blue-50 text-blue-800" },
  { key: "compliant", label: "Compliant", color: "bg-green-50 text-green-800" },
  { key: "partially_compliant", label: "Partially Compliant", color: "bg-yellow-50 text-yellow-800" },
  { key: "non_compliant", label: "Non-Compliant", color: "bg-red-50 text-red-800" },
  { key: "unassessed", label: "Unassessed", color: "bg-gray-50 text-gray-800" },
  { key: "compliance_lapsed", label: "Compliance Lapsed", color: "bg-orange-50 text-orange-800" },
  { key: "fully_governed", label: "Fully Governed", color: "bg-emerald-50 text-emerald-800" },
  { key: "unassigned", label: "Unassigned", color: "bg-rose-50 text-rose-800" },
];

export function GovernanceSummary({ summary }: GovernanceSummaryProps) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {STAT_CARDS.map(({ key, label, color }) => (
        <div key={key} className={`rounded-lg p-4 ${color}`}>
          <div className="text-2xl font-bold">{summary[key]}</div>
          <div className="text-xs font-medium">{label}</div>
        </div>
      ))}
    </div>
  );
}
