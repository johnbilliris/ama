"use client";

import { CompanionDataTable } from "@/components/governance/a11y/CompanionDataTable";
import { Tooltip } from "@/components/governance/a11y/Tooltip";
import { generateChartAriaLabel } from "@/components/governance/a11y/ChartAriaLabel";

interface HealthScoreGaugeProps {
  /** Composite score 0-100 */
  score: number;
  /** Traffic light status */
  status: "green" | "amber" | "red";
  /** Dimension breakdown for companion table */
  dimensions?: Array<{
    dimension: string;
    score: number;
    weight: number;
    weighted_score: number;
    input_count?: number;
  }>;
}

const STATUS_COLOURS: Record<string, { ring: string; text: string; bg: string }> = {
  green: { ring: "text-green-500", text: "text-green-700", bg: "bg-green-50" },
  amber: { ring: "text-yellow-500", text: "text-yellow-700", bg: "bg-yellow-50" },
  red: { ring: "text-red-500", text: "text-red-700", bg: "bg-red-50" },
};

/** Per-dimension explanatory metadata used by the info-icon tooltips. */
const DIMENSION_META: Record<
  string,
  {
    label: string;
    description: string;
    formula: string;
    inputUnit: string;
  }
> = {
  constitutional_compliance: {
    label: "Constitutional Compliance",
    description:
      "Adherence to the 10 constitutional governance gates that protect public-safety, privacy, accountability, and AIIMS-aligned commitments. Compliant gates earn full credit; partially compliant gates earn half credit; gates still pending assessment are excluded from the denominator.",
    formula: "((compliant + partially_compliant × 0.5) ÷ assessed_gates) × 100",
    inputUnit: "constitutional gate",
  },
  operational_readiness: {
    label: "Operational Readiness",
    description:
      "Preparedness posture: how often required exercises are completed on schedule, how well key incident-management roles are covered, and how current the emergency plans are.",
    formula: "average(exercise_completion_rate, role_coverage_pct, plan_currency_pct)",
    inputUnit: "readiness metric",
  },
  data_source_governance: {
    label: "Data Source Governance",
    description:
      "Whether registered data sources meet the governance baseline (provenance, refresh cadence, classification, retention). Compliant sources earn full credit; partially compliant sources earn half credit.",
    formula: "((compliant + partially_compliant × 0.5) ÷ total_sources) × 100",
    inputUnit: "data source",
  },
  recovery_progress: {
    label: "Recovery Progress",
    description:
      "When an incident is in the recovery phase, the average completion across all recovery domains (people, environment, economy, infrastructure). When no recovery is active this scores 100% — there is nothing to recover from.",
    formula: "no active recovery → 100; otherwise mean(domain.completion_pct)",
    inputUnit: "recovery domain",
  },
};

const FALLBACK_META = {
  label: "Dimension",
  description: "Component dimension contributing to the composite governance health score.",
  formula: "score × weight",
  inputUnit: "input",
};

const formatPercent = (value: number) => `${(value * 100).toFixed(0)}%`;
const formatScore = (value: number) => value.toFixed(1);

const monoStyle = {
  fontFamily:
    "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
} as const;

const blockStyle = { display: "block" } as const;
const blockMutedStyle = { display: "block", color: "#d1d5db", marginTop: 4 } as const;
const blockMt1Style = { display: "block", marginTop: 4 } as const;

const interactiveScoreStyle = {
  textDecoration: "underline dotted #9ca3af",
  textUnderlineOffset: 2,
  cursor: "help",
} as const;

const infoIconStyle = {
  display: "inline-block",
  marginLeft: 4,
  width: 14,
  height: 14,
  color: "#6b7280",
  verticalAlign: "middle",
} as const;

/** Information (i) icon used as the tooltip trigger next to a dimension name. */
function InfoIcon() {
  return (
    <svg
      viewBox="0 0 20 20"
      aria-hidden="true"
      focusable="false"
      style={infoIconStyle}
    >
      <circle cx="10" cy="10" r="8.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="10" cy="6.25" r="1" fill="currentColor" />
      <path
        d="M10 9.25v5.25"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
      />
    </svg>
  );
}

/**
 * 0-100 gauge with traffic light status and companion data table for accessibility.
 */
export function HealthScoreGauge({
  score,
  status,
  dimensions = [],
}: HealthScoreGaugeProps) {
  const colours = STATUS_COLOURS[status] ?? STATUS_COLOURS.amber;
  const percentage = Math.min(100, Math.max(0, score));
  const circumference = 2 * Math.PI * 40;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const ariaLabel = generateChartAriaLabel({
    type: "gauge",
    label: "Governance health score",
    value: Math.round(score),
    max: 100,
    status: status.charAt(0).toUpperCase() + status.slice(1),
  });

  return (
    <div className={`rounded-lg p-4 ${colours.bg}`}>
      <div className="flex items-center gap-4">
        {/* SVG Gauge */}
        <div className="relative h-24 w-24" aria-hidden="true">
          <svg className="h-24 w-24 -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="currentColor"
              strokeWidth="8"
              className="text-gray-200"
            />
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="currentColor"
              strokeWidth="8"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              className={colours.ring}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`text-2xl font-bold ${colours.text}`}>
              {Math.round(score)}
            </span>
          </div>
        </div>

        {/* Labels */}
        <div>
          <h3 className="text-sm font-semibold text-gray-900">
            Governance Health
          </h3>
          <p className="mt-1 text-xs text-gray-600">
            Composite score across the constitutional governance dimensions.
          </p>
          <p className={`mt-2 text-lg font-bold ${colours.text}`} aria-label={ariaLabel}>
            {Math.round(score)}/100
          </p>
          <span
            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${colours.bg} ${colours.text}`}
          >
            {status === "green" && "✓ Good"}
            {status === "amber" && "⚠ Warning"}
            {status === "red" && "✗ Critical"}
          </span>
        </div>
      </div>

      {/* Companion data table for screen readers */}
      {dimensions.length > 0 && (
        <CompanionDataTable
          caption="Health score dimension breakdown"
          headers={["Dimension", "Score", "Weight", "Weighted Score"]}
          rows={dimensions.map((d) => {
            const meta = DIMENSION_META[d.dimension] ?? FALLBACK_META;
            const inputCount = d.input_count ?? 0;
            const inputLabel = `${inputCount} ${meta.inputUnit}${inputCount === 1 ? "" : "s"}`;
            const weightPct = formatPercent(d.weight);
            const scoreText = formatScore(d.score);
            const weightedText = formatScore(d.weighted_score);

            const dimensionExplanation = (
              <span>
                <span style={{ ...blockStyle, fontWeight: 600 }}>{meta.label}</span>
                <span style={blockMt1Style}>{meta.description}</span>
                <span style={blockMutedStyle}>
                  Formula: <span style={monoStyle}>{meta.formula}</span>
                </span>
                <span style={blockMutedStyle}>
                  Weight in composite: {weightPct}
                </span>
              </span>
            );

            const calculationExplanation = (
              <span>
                <span style={{ ...blockStyle, fontWeight: 600 }}>
                  How {meta.label} = {scoreText}
                </span>
                <span style={blockMt1Style}>Inputs: {inputLabel}.</span>
                <span style={blockMt1Style}>
                  Formula: <span style={monoStyle}>{meta.formula}</span>
                </span>
                <span style={blockMt1Style}>
                  Result: <span style={monoStyle}>{scoreText} / 100</span>
                </span>
                <span style={blockMutedStyle}>
                  Weighted contribution:{" "}
                  <span style={monoStyle}>
                    {scoreText} × {weightPct} = {weightedText}
                  </span>
                </span>
              </span>
            );

            return [
              <span
                key="dim"
                style={{ display: "inline-flex", alignItems: "center" }}
              >
                <span>{d.dimension.replace(/_/g, " ")}</span>
                <Tooltip content={dimensionExplanation} side="top" widthPx={300}>
                  <span
                    role="img"
                    aria-label={`About ${meta.label}`}
                    style={{ display: "inline-flex", alignItems: "center" }}
                  >
                    <InfoIcon />
                  </span>
                </Tooltip>
              </span>,
              <Tooltip
                key="score"
                content={calculationExplanation}
                side="top"
                widthPx={300}
              >
                <span style={interactiveScoreStyle}>{scoreText}</span>
              </Tooltip>,
              weightPct,
              <Tooltip
                key="weighted"
                content={calculationExplanation}
                side="top"
                widthPx={300}
              >
                <span style={interactiveScoreStyle}>{weightedText}</span>
              </Tooltip>,
            ];
          })}
        />
      )}
    </div>
  );
}
