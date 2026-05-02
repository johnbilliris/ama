/**
 * PSPF classification label validator (T042).
 *
 * Asserts every visible classification banner / API response carries a
 * classification at or below the persona's clearance level. Used by the
 * cross-cutting `data-sovereignty.spec.ts` and `audit-trail.spec.ts`.
 */

export type Classification =
  | "UNOFFICIAL"
  | "OFFICIAL"
  | "OFFICIAL: Sensitive"
  | "PROTECTED"
  | "SECRET"
  | "TOP SECRET";

const ORDER: Classification[] = [
  "UNOFFICIAL",
  "OFFICIAL",
  "OFFICIAL: Sensitive",
  "PROTECTED",
  "SECRET",
  "TOP SECRET",
];

export function classificationLevel(label: string): number {
  const idx = ORDER.findIndex((c) => c.toLowerCase() === label.toLowerCase());
  if (idx === -1) {
    throw new Error(`Unknown PSPF classification: ${label}`);
  }
  return idx;
}

export interface PspfValidation {
  ok: boolean;
  reason?: string;
}

export function validatePspfClassification(
  visibleLabel: string,
  personaClearance: Classification,
): PspfValidation {
  try {
    const visible = classificationLevel(visibleLabel);
    const allowed = classificationLevel(personaClearance);
    if (visible > allowed) {
      return { ok: false, reason: `persona clearance '${personaClearance}' below visible '${visibleLabel}'` };
    }
    return { ok: true };
  } catch (err) {
    return { ok: false, reason: (err as Error).message };
  }
}
