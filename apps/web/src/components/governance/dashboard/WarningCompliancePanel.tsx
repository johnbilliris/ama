"use client";

import { useState } from "react";
import type { AWSPrincipleCompliance, AlertComplianceMetrics } from "@/lib/api/governance";

const ISSUING_AUTHORITIES = [
  "All Authorities",
  "Bureau of Meteorology",
  "Geoscience Australia",
  "State/Territory Lead Agency",
] as const;

interface WarningCompliancePanelProps {
  alertCompliance: AlertComplianceMetrics;
}

/**
 * AWS 10-principle warning compliance panel with tier usage and broadcast reach (US6).
 * Uses AWS severity colour tokens per FR-033A.
 */
export function WarningCompliancePanel({
  alertCompliance,
}: WarningCompliancePanelProps) {
  const [issuingAuthority, setIssuingAuthority] = useState<string>("All Authorities");

  const {
    avg_approval_latency_s,
    acceptable_threshold_s,
    exceeds_threshold,
    aws_tier_usage,
    broadcast_reach_pct,
    principle_compliance,
    overall_principle_compliance_pct,
  } = alertCompliance;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <h3 className="mb-3 text-sm font-semibold text-gray-900">
        Warning Compliance
      </h3>

      {/* Issuing Authority filter */}
      <div className="mb-4">
        <label htmlFor="issuing-authority-filter" className="block text-xs font-medium text-gray-700 mb-1">
          Issuing Authority
        </label>
        <select
          id="issuing-authority-filter"
          value={issuingAuthority}
          onChange={(e) => setIssuingAuthority(e.target.value)}
          className="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          {ISSUING_AUTHORITIES.map((authority) => (
            <option key={authority} value={authority}>
              {authority}
            </option>
          ))}
        </select>
      </div>

      {/* Key metrics row */}
      <div className="mb-4 grid grid-cols-3 gap-3">
        {/* Approval latency */}
        <div className={`rounded-lg p-3 ${exceeds_threshold ? "bg-red-50" : "bg-green-50"}`}>
          <p className="text-xs text-gray-600">Avg Approval Latency</p>
          <p className={`text-lg font-bold ${exceeds_threshold ? "text-red-700" : "text-green-700"}`}>
            {avg_approval_latency_s.toFixed(0)}s
          </p>
          {exceeds_threshold && (
            <p className="text-[10px] text-red-600">
              ⚠ Exceeds {acceptable_threshold_s}s threshold
            </p>
          )}
        </div>

        {/* Broadcast reach */}
        <div className="rounded-lg bg-blue-50 p-3">
          <p className="text-xs text-gray-600">Broadcast Reach</p>
          <p className="text-lg font-bold text-blue-700">
            {broadcast_reach_pct.toFixed(1)}%
          </p>
        </div>

        {/* Overall compliance */}
        <div className="rounded-lg bg-purple-50 p-3">
          <p className="text-xs text-gray-600">Principle Compliance</p>
          <p className="text-lg font-bold text-purple-700">
            {overall_principle_compliance_pct.toFixed(1)}%
          </p>
        </div>
      </div>

      {/* AWS tier usage */}
      <div className="mb-4">
        <h4 className="mb-2 text-xs font-semibold text-gray-700">
          AWS Warning Tier Usage
        </h4>
        <div className="flex gap-3">
          <div
            className="flex-1 rounded-lg p-2 text-center"
            style={{
              backgroundColor: "var(--ama-aws-advice, #fef3c7)",
              color: "var(--ama-aws-advice-text, #92400e)",
            }}
          >
            <p className="text-lg font-bold">{aws_tier_usage.advice ?? 0}</p>
            <p className="text-xs font-medium">Advice</p>
          </div>
          <div
            className="flex-1 rounded-lg p-2 text-center"
            style={{
              backgroundColor: "var(--ama-aws-watch, #fed7aa)",
              color: "var(--ama-aws-watch-text, #9a3412)",
            }}
          >
            <p className="text-lg font-bold">{aws_tier_usage.watch_and_act ?? 0}</p>
            <p className="text-xs font-medium">Watch & Act</p>
          </div>
          <div
            className="flex-1 rounded-lg p-2 text-center"
            style={{
              backgroundColor: "var(--ama-aws-emergency, #fecaca)",
              color: "var(--ama-aws-emergency-text, #991b1b)",
            }}
          >
            <p className="text-lg font-bold">{aws_tier_usage.emergency_warning ?? 0}</p>
            <p className="text-xs font-medium">Emergency</p>
          </div>
        </div>
      </div>

      {/* 10 AWS principles grid */}
      <h4 className="mb-2 text-xs font-semibold text-gray-700">
        10 AWS Warning Principles
      </h4>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
        {principle_compliance.map((p) => (
          <div
            key={p.principle}
            className={`rounded-lg border p-2 text-center ${
              p.compliance_rate_pct >= 80
                ? "border-green-200 bg-green-50"
                : p.compliance_rate_pct >= 50
                  ? "border-yellow-200 bg-yellow-50"
                  : "border-red-200 bg-red-50"
            }`}
          >
            <p className="text-lg font-bold">
              {p.compliance_rate_pct.toFixed(0)}%
            </p>
            <p className="truncate text-[10px] font-medium text-gray-700">
              {p.display_name}
            </p>
            <p className="text-[10px] text-gray-500">
              {p.compliant_count}/{p.total_count}
            </p>
          </div>
        ))}
      </div>

      {/* Multilingual Coverage */}
      <div className="mt-4">
        <h4 className="mb-2 text-xs font-semibold text-gray-700">
          Multilingual Coverage
        </h4>
        <div
          className="rounded-lg p-3"
          style={{
            backgroundColor: "var(--ama-aws-advice, #fef3c7)",
            color: "var(--ama-aws-advice-text, #92400e)",
          }}
        >
          <p className="text-xs text-gray-600">Warnings with multilingual versions</p>
          <p className="text-2xl font-bold">0%</p>
          <p className="text-[10px] text-gray-500">0 of 0 warnings have multilingual translations</p>
        </div>
      </div>

      {/* Accessibility Compliance */}
      <div className="mt-4">
        <h4 className="mb-2 text-xs font-semibold text-gray-700">
          Accessibility Compliance
        </h4>
        <div
          className="rounded-lg p-3"
          style={{
            backgroundColor: "var(--ama-aws-watch, #fed7aa)",
            color: "var(--ama-aws-watch-text, #9a3412)",
          }}
        >
          <p className="text-xs text-gray-600">WCAG compliance rate for public communications</p>
          <p className="text-2xl font-bold">0%</p>
          <p className="text-[10px] text-gray-500">0 of 0 communications meet WCAG 2.1 AA standards</p>
        </div>
      </div>
    </div>
  );
}
