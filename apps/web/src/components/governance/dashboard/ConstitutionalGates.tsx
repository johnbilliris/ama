"use client";

import type { ConstitutionalGateStatus } from "@/lib/api/governance";

interface ConstitutionalGatesProps {
  gates: ConstitutionalGateStatus[];
}

const STATUS_BADGE: Record<
  string,
  { bg: string; text: string; icon: string; label: string }
> = {
  compliant: {
    bg: "bg-green-100",
    text: "text-green-800",
    icon: "✓",
    label: "Compliant",
  },
  non_compliant: {
    bg: "bg-red-100",
    text: "text-red-800",
    icon: "✗",
    label: "Non-Compliant",
  },
  partially_compliant: {
    bg: "bg-yellow-100",
    text: "text-yellow-800",
    icon: "⚠",
    label: "Partial",
  },
  assessment_pending: {
    bg: "bg-gray-100",
    text: "text-gray-600",
    icon: "⏳",
    label: "Pending",
  },
};

const SEVERITY_INDICATOR: Record<string, string> = {
  critical: "🔴",
  warning: "🟡",
  info: "🔵",
};

/**
 * 10-gate constitutional compliance grid with colour-coded status badges (FR-002).
 */
export function ConstitutionalGates({ gates }: ConstitutionalGatesProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <h3 className="mb-3 text-sm font-semibold text-gray-900">
        Constitutional Gates ({gates.length})
      </h3>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
        {gates.map((gate) => {
          const badge = STATUS_BADGE[gate.status] ?? STATUS_BADGE.assessment_pending;
          const severity = gate.severity
            ? SEVERITY_INDICATOR[gate.severity]
            : null;

          return (
            <a
              key={gate.gate_number}
              href={gate.detail_url}
              className="group rounded-lg border border-gray-100 p-2 transition-colors hover:border-blue-300 hover:bg-blue-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
              aria-label={`Gate ${gate.gate_number}: ${gate.gate_name} — ${badge.label}${
                gate.severity ? `, ${gate.severity} severity` : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-500">
                  Gate {gate.gate_number}
                </span>
                {severity && (
                  <span aria-hidden="true" className="text-xs">
                    {severity}
                  </span>
                )}
              </div>
              <p className="mt-1 truncate text-xs font-medium text-gray-800 group-hover:text-blue-800">
                {gate.gate_name}
              </p>
              <span
                className={`mt-1 inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-medium ${badge.bg} ${badge.text}`}
              >
                <span aria-hidden="true">{badge.icon}</span>
                {badge.label}
              </span>
            </a>
          );
        })}
      </div>
    </div>
  );
}
