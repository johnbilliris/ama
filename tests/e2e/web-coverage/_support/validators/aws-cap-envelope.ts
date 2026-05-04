/**
 * AWS CAP envelope validator (T041).
 *
 * Asserts a public warning payload conforms to the Australian Warning System
 * CAP-style envelope: required fields, level (advice|watch-and-act|emergency-warning),
 * issuer hierarchy, and multi-language array.
 */

const REQUIRED_FIELDS = [
  "warning_id",
  "issued_at",
  "level",
  "hazard_type",
  "headline",
  "instruction",
  "affected_areas",
  "languages",
];

const VALID_LEVELS = new Set(["advice", "watch-and-act", "emergency-warning"]);

export interface AwsCapValidation {
  ok: boolean;
  errors: string[];
}

export function validateAwsCapEnvelope(payload: Record<string, unknown>): AwsCapValidation {
  const errors: string[] = [];
  for (const field of REQUIRED_FIELDS) {
    if (payload[field] === undefined || payload[field] === null) {
      errors.push(`missing required field: ${field}`);
    }
  }
  const level = payload.level;
  if (typeof level !== "string" || !VALID_LEVELS.has(level)) {
    errors.push(`invalid level: ${String(level)}; expected one of ${[...VALID_LEVELS].join(", ")}`);
  }
  const languages = payload.languages;
  if (!Array.isArray(languages) || languages.length === 0) {
    errors.push("languages must be a non-empty array of BCP-47 codes");
  } else if (!languages.includes("en")) {
    errors.push("languages MUST include 'en' (Australia primary)");
  }
  const issued = payload.issued_at;
  if (typeof issued !== "string" || Number.isNaN(Date.parse(issued))) {
    errors.push("issued_at must be ISO 8601 timestamp");
  }
  return { ok: errors.length === 0, errors };
}
