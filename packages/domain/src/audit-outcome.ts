/**
 * Closed-set audit outcome enum (spec-035).
 *
 * Source: specs/035-webapp-capstone-closure/data-model.md § 4 AuditTimelineEntry → "Outcome enum (closed set)".
 * MUST contain exactly 20 values. The Python mirror at
 * apps/api/app/domain/audit_outcome.py is the contract counterpart and MUST stay
 * cardinality-identical (a contract test in apps/api/tests/contract/spec_035 enforces this).
 */
export const AUDIT_OUTCOMES = [
  "approved",
  "denied",
  "published",
  "allocate",
  "admin_override",
  "classifier_deny",
  "classifier_mask",
  "classifier_failed",
  "queue_overflow",
  "queue_displaced",
  "activation_mutex_violation",
  "rate_limited",
  "auth_unauthorized",
  "auth_forbidden",
  "sovereignty_denied",
  "schema_invalid",
  "seed_not_ready",
  "evaluator_not_routable",
  "cultural_safety_timeout_override",
  "cultural_safety_held",
] as const;

export type AuditOutcome = (typeof AUDIT_OUTCOMES)[number];

const AUDIT_OUTCOME_SET: ReadonlySet<string> = new Set(AUDIT_OUTCOMES);

export function isAuditOutcome(value: unknown): value is AuditOutcome {
  return typeof value === "string" && AUDIT_OUTCOME_SET.has(value);
}

export const AUDIT_OUTCOME_COUNT: 20 = 20;
