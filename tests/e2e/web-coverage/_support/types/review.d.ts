/**
 * Review tribunal vote types — match contracts/review-vote.schema.json
 * and contracts/agent-objection.schema.json.
 */

export type AgentPanel = "operational" | "sector" | "technical";
export type Vote = "approve" | "object" | "abstain";
export type Disposition = "meritorious" | "rejected" | "veto" | "override" | "pending";

export interface ReviewVote {
  agent_id: string;
  panel: AgentPanel;
  cycle: number;
  gap_id: string;
  touched_personas: string[];
  touched_frs: string[];
  touched_clauses: string[];
  vote: Vote;
  rationale: string;
  disposition: Disposition;
  recorded_at: string;
}

export interface AgentObjectionEvidence {
  type: "test-failure" | "trace-row" | "audit-event" | "spec-ref" | "external-reference";
  pointer: string;
}

export interface AgentObjection {
  agent_id: string;
  panel: AgentPanel;
  cycle: number;
  gap_id?: string;
  touched_personas: string[];
  touched_frs: string[];
  touched_clauses: string[];
  rationale: string;
  evidence: AgentObjectionEvidence[];
  proposed_remediation: string;
}
