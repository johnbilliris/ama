/**
 * spec-038 — TypeScript twins for the 13 Help domain entities.
 *
 * These are byte-identical-shape aliases of the Pydantic v2 source-of-truth
 * models in ``packages/domain/src/ama_domain/`` (see data-model.md §1–§13).
 * The CI sync test (T-AA047) verifies field cardinality at build time.
 */

export type ArticleKind = "article" | "playbook" | "faq" | "glossary" | "persona";
export type ArticleStatus = "draft" | "published" | "withdrawn";
export type ArticleDomain =
  | "getting-started"
  | "persona-workflow"
  | "screen-by-screen"
  | "simulation-playbook"
  | "agent-playbook"
  | "audit-observer"
  | "accessibility"
  | "troubleshooting"
  | "glossary";

export interface HelpArticle {
  id: string;
  tenant_id: string;
  kind: ArticleKind;
  title: string;
  slug: string;
  persona_tags: string[];
  sector_tags: string[];
  surface_tags: string[];
  jurisdiction_tags: string[];
  domain: ArticleDomain;
  body_uri: string;
  screenshot_ids: string[];
  snapshot_id: string;
  version: number;
  status: ArticleStatus;
  staleness_flag_id: string | null;
  last_reviewed_at: string;
  created_at: string;
  updated_at: string;
  etag: string | null;
  glossary_term_links: string[];
}

export interface Callout {
  number: number;
  anchor_dom_path: string;
  alt_text: string;
  keyboard_steps: string[];
}

export interface AnnotatedScreenshot {
  id: string;
  tenant_id: string;
  screen_id: string;
  route_id: string;
  previous_route_id: string | null;
  screen_id_hash: string;
  light_blob_uri: string;
  dark_blob_uri: string;
  alt_text_blob_uri: string;
  callouts: Callout[];
  captured_at: string;
  captured_by: string;
  article_ids: string[];
  staleness_flag_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface GlossaryTerm {
  id: string;
  tenant_id: string;
  term: string;
  definition: string;
  domain: "aiims" | "aidr" | "jurisdictional" | "hub";
  aliases: string[];
  related_article_ids: string[];
  lang: string;
  cultural_authority_ref: string | null;
  created_at: string;
  updated_at: string;
}

export interface PersonaHelpProfile {
  id: string;
  tenant_id: string;
  persona_kind: "operational" | "sector";
  authority_rank: number;
  landing_tile_ids: string[];
  recommended_workflow_article_ids: string[];
  decision_rights_summary: string;
  handoff_destinations: string[];
  chat_starter_prompts: string[];
  created_at: string;
  updated_at: string;
}

export interface KnowledgeCorpusSource {
  id: string;
  snapshot_id: string;
  source_kind: "help_article" | "docs_corpus" | "docs_aidr" | "spec";
  source_path: string;
  spec_id: string | null;
  spec_version: string | null;
  spec_status: "Active" | "Implemented" | null;
  content_hash: string;
  classification: "OFFICIAL" | "OFFICIAL: SENSITIVE";
  scope: "tenant" | "global";
  indexed_at: string;
}

export type RefusalReason =
  | "out_of_scope"
  | "cross_tenant"
  | "no_corpus_match"
  | "pii_blocked"
  | "above_official_classification"
  | "deprecated_no_replacement";

export interface ChatTurn {
  turn_index: number;
  user_input_redacted: string;
  redaction_occurred: boolean;
  answer_text: string;
  citations: string[];
  refusal_reason: RefusalReason | null;
  pattern_id: string;
  feedback_id: string | null;
  audit_entry_id: string;
  created_at: string;
}

export interface ChatSession {
  id: string;
  tenant_id: string;
  user_id: string;
  persona_id: string;
  persona_source: "idp_default" | "user_override";
  jurisdiction_codes: string[];
  snapshot_id_at_open: string;
  turns: ChatTurn[];
  started_at: string;
  last_turn_at: string;
  ttl_seconds: number;
}

export interface HelpFeedback {
  id: string;
  tenant_id: string;
  target_kind: "article" | "chat_turn";
  target_id: string;
  rating: "helpful" | "not_helpful";
  comment: string | null;
  submitted_by: string;
  pattern_id: string | null;
  created_at: string;
}

export interface StalenessFlag {
  id: string;
  tenant_id: string;
  target_kind: "screenshot" | "article";
  target_id: string;
  raised_reason: "screen_id_hash_mismatch" | "route_renamed" | "manual";
  raised_at: string;
  grace_release_id: string;
  cleared_at: string | null;
  cleared_by: string | null;
  bulk_baseline_id: string | null;
}

export interface Approver {
  identity: string;
  role: "help_content_owner" | "safety_lead" | "governance_lead";
  approved_at: string;
}

export interface SnapshotRecord {
  id: string;
  tenant_id: string;
  sources: KnowledgeCorpusSource[];
  ai_search_index_name: string;
  approvers: Approver[];
  published_at: string;
  published_by: string;
  rollback_of: string | null;
}

export type ChannelKind = "email" | "shared_mailbox" | "on_call_rotation" | "chat_link";

export interface SupportHandoffRecord {
  id: string;
  tenant_id: string;
  channel_kind: ChannelKind;
  address: string;
  business_hours_window: string;
  incident_mode_channel: SupportHandoffRecord | null;
  auto_activate_on_nema_level3: boolean;
  manual_override_active: boolean;
  sla_routine_business_hours: number;
  sla_incident_minutes: number;
  created_at: string;
  updated_at: string;
}

export interface ContentReviewBacklogItem {
  id: string;
  tenant_id: string;
  target_kind: "article" | "chat_pattern";
  target_id: string;
  feedback_ids: string[];
  negative_count_30d: number;
  status: "new" | "needs_review" | "in_review" | "resolved" | "wont_change";
  auto_promoted_at: string | null;
  resolved_by: string | null;
  resolved_snapshot_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatAuditEntry {
  id: string;
  tenant_id: string;
  chat_session_id: string;
  turn_index: number;
  user_id: string;
  persona_id: string;
  persona_source: "idp_default" | "user_override";
  jurisdiction_codes: string[];
  snapshot_id: string;
  foundry_agent_name: "help_assistant";
  user_input_redacted: string;
  redaction_occurred: boolean;
  retrieved_citation_ids: string[];
  response_text: string;
  refusal_reason: string | null;
  pattern_id: string;
  gateway_decision: "allow" | "deny" | "redact";
  created_at: string;
}

/** Re-exported from spec-036 — citation envelope shape (do not redefine). */
export interface Citation {
  jurisdiction: string;
  topic: string;
  page: number;
  source_url: string;
  rendered_url: string;
  sha256_of_chunk: string;
  licence_mode: "full-text" | "metadata-only";
  confidence: number;
  snippet?: string;
}
