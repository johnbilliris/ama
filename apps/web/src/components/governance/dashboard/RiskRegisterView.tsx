"use client";

import { useState } from "react";
import type { RiskSeverityBreakdown } from "@/lib/api/governance";

const HAZARD_TYPES = [
  "All Hazards",
  "Bushfire",
  "Flood",
  "Storm",
  "Cyclone",
  "Earthquake",
  "Tsunami",
  "Heatwave",
  "Pandemic",
] as const;

interface RiskRegisterViewProps {
  severity: RiskSeverityBreakdown;
  treatmentClosureRatePct: number;
  topRisks: Array<{
    id: string;
    description: string;
    severity: string;
    treatment_due: string;
    responsible: string;
  }>;
  onRiskClick: (riskId: string) => void;
}

const SEVERITY_COLOURS: Record<string, { bg: string; text: string }> = {
  extreme: { bg: "bg-red-100", text: "text-red-800" },
  high: { bg: "bg-orange-100", text: "text-orange-800" },
  medium: { bg: "bg-yellow-100", text: "text-yellow-800" },
  low: { bg: "bg-green-100", text: "text-green-800" },
};

/**
 * Risk register with severity breakdown, treatment closure rate, and top risks table (US6).
 */
export function RiskRegisterView({
  severity,
  treatmentClosureRatePct,
  topRisks,
  onRiskClick,
}: RiskRegisterViewProps) {
  const [hazardType, setHazardType] = useState<string>("All Hazards");

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <h3 className="mb-3 text-sm font-semibold text-gray-900">
        Risk Register ({severity.total} active risks)
      </h3>

      {/* Hazard type filter */}
      <div className="mb-4">
        <label htmlFor="hazard-type-filter" className="block text-xs font-medium text-gray-700 mb-1">
          Hazard Type
        </label>
        <select
          id="hazard-type-filter"
          value={hazardType}
          onChange={(e) => setHazardType(e.target.value)}
          className="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          {HAZARD_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </div>

      {/* Severity breakdown cards */}
      <div className="mb-4 grid grid-cols-4 gap-2">
        {(["extreme", "high", "medium", "low"] as const).map((level) => {
          const colours = SEVERITY_COLOURS[level];
          return (
            <div key={level} className={`rounded-lg p-3 text-center ${colours.bg}`}>
              <p className={`text-2xl font-bold ${colours.text}`}>
                {severity[level]}
              </p>
              <p className={`text-xs font-medium capitalize ${colours.text}`}>
                {level}
              </p>
            </div>
          );
        })}
      </div>

      {/* Treatment closure rate */}
      <div className="mb-4 rounded-lg bg-gray-50 p-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-700">Treatment Closure Rate</span>
          <span className="text-lg font-bold text-gray-900">
            {treatmentClosureRatePct.toFixed(1)}%
          </span>
        </div>
        <div className="mt-2 h-2 w-full rounded-full bg-gray-200">
          <div
            className={`h-2 rounded-full ${
              treatmentClosureRatePct >= 80 ? "bg-green-500" : treatmentClosureRatePct >= 50 ? "bg-yellow-500" : "bg-red-500"
            }`}
            style={{ width: `${Math.min(100, treatmentClosureRatePct)}%` }}
          />
        </div>
      </div>

      {/* Top risks table */}
      <h4 className="mb-2 text-xs font-semibold text-gray-700">Top Risks</h4>
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b bg-gray-50">
            <th className="px-3 py-2 text-left font-medium text-gray-700">Description</th>
            <th className="px-3 py-2 text-left font-medium text-gray-700">Severity</th>
            <th className="px-3 py-2 text-left font-medium text-gray-700">Treatment Due</th>
            <th className="px-3 py-2 text-left font-medium text-gray-700">Responsible</th>
          </tr>
        </thead>
        <tbody>
          {topRisks.map((risk) => {
            const colours = SEVERITY_COLOURS[risk.severity] ?? SEVERITY_COLOURS.medium;
            return (
              <tr
                key={risk.id}
                className="cursor-pointer border-b hover:bg-blue-50"
                onClick={() => onRiskClick(risk.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") onRiskClick(risk.id);
                }}
              >
                <td className="px-3 py-2">{risk.description}</td>
                <td className="px-3 py-2">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${colours.bg} ${colours.text}`}>
                    {risk.severity}
                  </span>
                </td>
                <td className="px-3 py-2 text-gray-600">{risk.treatment_due}</td>
                <td className="px-3 py-2 text-gray-600">{risk.responsible}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
