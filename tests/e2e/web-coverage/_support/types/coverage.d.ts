/**
 * Coverage trace row type — matches contracts/coverage-trace-row.schema.json.
 * Emitted by the custom Playwright reporter (T033) per (persona × outcome × hazard × FR) tuple.
 */
export interface CoverageTraceRow {
  persona_id: string;
  aiims_function: "control" | "operations" | "planning" | "logistics" | "public-information";
  outcome: 1 | 2 | 3 | 4 | 5;
  hazard: string;
  fr_id: string; // FR-NNN[a]
  constitution_clauses: string[];
  test_ids: string[];
  route: string;
  audit_evidence_id: string | null;
  correlation_id: string;
  status: "passed" | "failing" | "flake-known" | "skipped";
  duration_ms: number;
  emitted_at: string; // ISO 8601
}

/**
 * Aggregate written to coverage-trace.json. Ordering of `rows` is deterministic
 * (sorted by persona_id, outcome, hazard, fr_id) so trace replay is byte-stable.
 */
export interface CoverageTrace {
  generated_at: string;
  spec: "034-webapp-capstone-coverage";
  schema_version: 1;
  rows: CoverageTraceRow[];
}
