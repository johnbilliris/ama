/**
 * Gap register entry — matches contracts/gap-register-entry.schema.json.
 * Persisted as both gap-register.md (source of truth) and audit JSONL shadow.
 */
export interface RegressionEvidence {
  failing_test_id: string;
  reverted_commit_sha: string;
  restored_revision_sha: string;
  detected_at: string;
}

export interface GapRegisterEntry {
  gap_id: string; // GAP-...
  affected_personas: string[];
  affected_routes: string[];
  fr_ids: string[];
  constitution_clauses: string[];
  owner: string;
  status: "Open" | "In-Progress" | "Closed" | "Reopened" | "Escalated";
  closing_pr_url: string | null;
  merge_sha: string | null;
  iteration_count: number; // 0..4
  regression_evidence: RegressionEvidence | null;
  tribunal_notes: string;
  updated_at: string;
}
