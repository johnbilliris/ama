/**
 * Trace-row helper (T035) — produces a CoverageTraceRow for a single test result.
 */
import type { CoverageTraceRow } from "../types/coverage";
import type { CoverageTags } from "./annotations";

export interface TraceRowInput {
  tags: CoverageTags;
  fr_id: string;
  test_id: string;
  route: string;
  audit_evidence_id: string | null;
  correlation_id: string;
  status: CoverageTraceRow["status"];
  duration_ms: number;
  aiims_function: CoverageTraceRow["aiims_function"];
}

export function buildTraceRow(input: TraceRowInput): CoverageTraceRow {
  return {
    persona_id: input.tags.persona,
    aiims_function: input.aiims_function,
    outcome: input.tags.outcome,
    hazard: input.tags.hazard,
    fr_id: input.fr_id,
    constitution_clauses: input.tags.clauses,
    test_ids: [input.test_id],
    route: input.route,
    audit_evidence_id: input.audit_evidence_id,
    correlation_id: input.correlation_id,
    status: input.status,
    duration_ms: input.duration_ms,
    emitted_at: new Date().toISOString(),
  };
}

/**
 * Sort rows for deterministic emission. Required by FR-006 trace replay.
 */
export function sortRowsDeterministic(rows: CoverageTraceRow[]): CoverageTraceRow[] {
  return rows.slice().sort((a, b) => {
    if (a.persona_id !== b.persona_id) return a.persona_id < b.persona_id ? -1 : 1;
    if (a.outcome !== b.outcome) return a.outcome - b.outcome;
    if (a.hazard !== b.hazard) return a.hazard < b.hazard ? -1 : 1;
    if (a.fr_id !== b.fr_id) return a.fr_id < b.fr_id ? -1 : 1;
    return 0;
  });
}
