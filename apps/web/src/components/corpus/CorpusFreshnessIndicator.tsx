"use client";

/**
 * Spec 036 / Phase F (T214) — Corpus freshness indicator
 *
 * Per FR-RAG-FRESH-01 + Plan §F-A8.2 — surfaces "Corpus last updated:
 * <timestamp>" derived from `corpus_build_sha.generated_at` on every
 * citation card and the simulation chat surface. Colour bands per Plan
 * §F-A8.2:
 *
 *   - green  : age <= 7 days
 *   - yellow : age in (7, 14] days
 *   - red    : age > 14 days
 *
 * NOTE: this is the IN-UI signal. The on-call alert (FR-RAG-FRESH-02) is
 * the separate Service Bus + PagerDuty path; this component only shades
 * the badge.
 */

interface CorpusFreshnessIndicatorProps {
  /** ISO timestamp of `corpus_build_sha.generated_at`. */
  generatedAt: string | null;
  /** Optional override for the comparison "now" (for SSR / tests). */
  now?: Date;
  /** Compact mode — drops the "Corpus last updated:" prefix. */
  compact?: boolean;
}

const YELLOW_AGE_DAYS = 7;
const RED_AGE_DAYS = 14;
const HOURS_PER_DAY = 24;
const SECONDS_PER_HOUR = 3600;
const MS_PER_SECOND = 1000;

function ageInDays(generatedAt: string, now: Date): number {
  const generated = new Date(generatedAt).getTime();
  const ms = now.getTime() - generated;
  return ms / (MS_PER_SECOND * SECONDS_PER_HOUR * HOURS_PER_DAY);
}

function severityFor(ageDays: number): "green" | "yellow" | "red" {
  if (ageDays > RED_AGE_DAYS) return "red";
  if (ageDays > YELLOW_AGE_DAYS) return "yellow";
  return "green";
}

const SEVERITY_CLASSES: Record<"green" | "yellow" | "red", string> = {
  green:
    "inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-xs text-emerald-800",
  yellow:
    "inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-900",
  red: "inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-800",
};

const SEVERITY_ICONS: Record<"green" | "yellow" | "red", string> = {
  green: "✓",
  yellow: "⚠",
  red: "✗",
};

const SEVERITY_LABELS: Record<"green" | "yellow" | "red", string> = {
  green: "fresh",
  yellow: "stale",
  red: "very stale",
};

export function CorpusFreshnessIndicator({
  generatedAt,
  now,
  compact = false,
}: CorpusFreshnessIndicatorProps) {
  if (!generatedAt) {
    return (
      <span
        className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
        role="status"
        aria-label="Corpus freshness unknown"
        data-testid="corpus-freshness-indicator"
        data-severity="unknown"
      >
        ⏳ Corpus age unknown
      </span>
    );
  }

  const days = ageInDays(generatedAt, now ?? new Date());
  const severity = severityFor(days);
  const labelDate = new Date(generatedAt).toISOString().slice(0, 10);
  const ariaLabel = `Corpus ${SEVERITY_LABELS[severity]}; last updated ${labelDate}; ${Math.floor(days)} days old.`;

  return (
    <span
      className={SEVERITY_CLASSES[severity]}
      role="status"
      aria-label={ariaLabel}
      data-testid="corpus-freshness-indicator"
      data-severity={severity}
      data-age-days={days.toFixed(1)}
    >
      <span aria-hidden="true">{SEVERITY_ICONS[severity]}</span>
      <span className="ml-1">
        {compact ? labelDate : `Corpus last updated: ${labelDate}`}
      </span>
    </span>
  );
}
