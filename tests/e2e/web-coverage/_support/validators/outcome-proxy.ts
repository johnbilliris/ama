/**
 * Outcome-proxy validator (T040).
 *
 * The five capstone outcomes are abstract; the suite uses concrete observable
 * proxies. Given a coverage trace row, this validator confirms the row's
 * (outcome, hazard, fr_id, audit_type) tuple is consistent with the
 * outcome's expected proxy set declared in the per-outcome fixture data.
 */
import outcome1 from "../fixtures/data/outcome-1-bushfire-extreme-heat.fixture.json";
import outcome2 from "../fixtures/data/outcome-2-bushfire-severe-storm.fixture.json";
import outcome3 from "../fixtures/data/outcome-3-tropical-cyclone-flood.fixture.json";
import outcome4 from "../fixtures/data/outcome-4-bushfire-cyclone-logistics.fixture.json";
import outcome5 from "../fixtures/data/outcome-5-flood-storm-economic.fixture.json";
import type { CoverageTraceRow } from "../types/coverage";

interface OutcomeFixture {
  outcome: number;
  primary_hazards: string[];
  expected_routes: string[];
  fr_ids: string[];
  constitution_clauses: string[];
}

const FIXTURES: Record<number, OutcomeFixture> = {
  1: outcome1 as unknown as OutcomeFixture,
  2: outcome2 as unknown as OutcomeFixture,
  3: outcome3 as unknown as OutcomeFixture,
  4: outcome4 as unknown as OutcomeFixture,
  5: outcome5 as unknown as OutcomeFixture,
};

export interface ValidationFinding {
  ok: boolean;
  reasons: string[];
}

export function validateOutcomeProxy(row: CoverageTraceRow): ValidationFinding {
  const reasons: string[] = [];
  const fixture = FIXTURES[row.outcome];
  if (!fixture) {
    reasons.push(`Unknown outcome ${row.outcome}`);
    return { ok: false, reasons };
  }

  const hazardTokens = row.hazard.split("+");
  if (!hazardTokens.every((h) => fixture.primary_hazards.includes(h))) {
    reasons.push(
      `hazard '${row.hazard}' not declared in outcome-${row.outcome} fixture (got ${fixture.primary_hazards.join(", ")})`,
    );
  }
  if (!fixture.expected_routes.includes(row.route)) {
    reasons.push(
      `route '${row.route}' not declared in outcome-${row.outcome} fixture expected_routes`,
    );
  }
  if (!fixture.fr_ids.includes(row.fr_id)) {
    reasons.push(
      `fr_id '${row.fr_id}' not declared in outcome-${row.outcome} fixture fr_ids`,
    );
  }
  for (const clause of row.constitution_clauses) {
    if (!fixture.constitution_clauses.includes(clause)) {
      reasons.push(
        `clause '${clause}' not declared in outcome-${row.outcome} fixture constitution_clauses`,
      );
    }
  }

  return { ok: reasons.length === 0, reasons };
}
