/**
 * Annotation tag helpers (T034).
 *
 * Each test in tests/e2e/web-coverage/** must declare exactly one tag from each
 * axis required by R-017:
 *   @persona:<id>  @outcome:<1..5>  @hazard:<...>  @fr:FR-NNN  @clause:<...>  @p1|@p2|@p3
 *
 * These helpers compose the tag string and surface mismatches at runtime so
 * the custom reporter can refuse to emit malformed rows.
 */

export type Priority = "p1" | "p2" | "p3";
export type ConstitutionClause =
  | "I"
  | "II"
  | "II-A"
  | "III"
  | "IV"
  | "V"
  | "V-A"
  | "V-B"
  | "V-C"
  | "VI"
  | "VII"
  | "VIII"
  | "NN-1"
  | "NN-2"
  | "NN-3"
  | "NN-4"
  | "NN-5"
  | "QG-1"
  | "QG-2"
  | "QG-3";

export interface CoverageTags {
  persona: string;
  outcome: 1 | 2 | 3 | 4 | 5;
  hazard: string;
  frs: string[]; // FR-NNN[a]
  clauses: ConstitutionClause[];
  priority: Priority;
}

const FR_PATTERN = /^FR-\d{3}[a-z]?$/;
const HAZARD_PATTERN = /^[a-z][a-z-]*(\+[a-z][a-z-]*)?$/;

export function buildTagString(tags: CoverageTags): string {
  if (!FR_PATTERN.test(tags.frs[0] ?? "")) {
    throw new Error(`buildTagString: invalid FR id '${tags.frs[0]}'`);
  }
  if (!HAZARD_PATTERN.test(tags.hazard)) {
    throw new Error(`buildTagString: invalid hazard '${tags.hazard}' (expected lowercase + hyphens, optional + pair)`);
  }
  const parts = [
    `@persona:${tags.persona}`,
    `@outcome:${tags.outcome}`,
    `@hazard:${tags.hazard}`,
    ...tags.frs.map((fr) => `@fr:${fr}`),
    ...tags.clauses.map((c) => `@clause:${c}`),
    `@${tags.priority}`,
  ];
  return parts.join(" ");
}

export function parseTagString(annotation: string): CoverageTags | null {
  const persona = /@persona:([a-z0-9-]+)/.exec(annotation)?.[1];
  const outcome = /@outcome:([1-5])/.exec(annotation)?.[1];
  const hazard = /@hazard:([a-z+-]+)/.exec(annotation)?.[1];
  const frs = Array.from(annotation.matchAll(/@fr:(FR-\d{3}[a-z]?)/g)).map((m) => m[1]);
  const clauses = Array.from(annotation.matchAll(/@clause:([A-Z\-0-9]+)/g)).map(
    (m) => m[1] as ConstitutionClause,
  );
  const priority = /@(p[123])\b/.exec(annotation)?.[1] as Priority | undefined;

  if (!persona || !outcome || !hazard || frs.length === 0 || clauses.length === 0 || !priority) {
    return null;
  }
  return {
    persona,
    outcome: Number(outcome) as CoverageTags["outcome"],
    hazard,
    frs,
    clauses,
    priority,
  };
}
