// Spec-038 evidence-harness TypeScript domain twins (T-S05, T-AMD-10).
//
// Hand-mirrored to the Pydantic models at
// `apps/api/app/services/evidence/models/`. Schema parity is asserted by
// the contract tests against `specs/040-success-criteria/contracts/openapi.evidence-harness.yaml`.

export type AiimsFunction =
  | "Control"
  | "Intelligence"
  | "Planning"
  | "Operations"
  | "Logistics"
  | "PublicInformation";

export type IncidentLevel = 1 | 2 | 3;
export type Provenance = "auto" | "manual";
export type IndicatorKind = "leading" | "lagging";
export type LifeSafetyTier = "life_safety" | "efficiency";
export type CapstoneScId =
  | "SC-CAP-015-001"
  | "SC-CAP-015-002"
  | "SC-CAP-015-003"
  | "SC-CAP-015-004"
  | "SC-CAP-015-005";

export interface ConfidenceBandRule {
  method?: "bootstrap_p2_5_p97_5" | "stddev_pm1";
  min_resamples?: number;
  fallback_label?: "small-sample";
}

/** FR-004 — 5×5 risk matrix (T-AMD-10). provenance/auditor_signoff_required added in Cycle 2. */
export interface RiskAdjustment {
  likelihood: number; // 1..5
  consequence: number; // 1..5
  provenance?: Provenance;
  auditor_signoff_required?: boolean;
}

export interface IndicatorDefinition {
  id: string;
  kpi_id: string;
  version: number;
  capstone_sc_id: CapstoneScId;
  name: string;
  kind: IndicatorKind;
  aiims_function: AiimsFunction;
  incident_level: IncidentLevel;
  life_safety_tier: LifeSafetyTier;
  formula: string;
  formula_version?: string;
  unit: string;
  owner_role: string;
  refresh_cadence: string;
  target_value: number;
  alert_threshold: number;
  baseline_source: string;
  calibration_reference?: string;
  provenance: Provenance;
  confidence_band_rule: ConfidenceBandRule;
  /** Required in Cycle 2 — defaults to (L=3,C=3) manual if not supplied (T-AMD-11). */
  risk_adjustment?: RiskAdjustment | null;
  publication_status?: "draft" | "published" | "superseded";
  created_at: string;
  created_by: string;
  superseded_by?: string | null;
}

export interface KpiLadderGroup {
  capstone_sc_id: CapstoneScId;
  leading: IndicatorDefinition[];
  lagging: IndicatorDefinition[];
}

export interface KpiLadderView {
  version: string;
  generated_at: string;
  groups: KpiLadderGroup[];
}

export interface MeasurementMethodDefinition {
  capstone_sc_id: string;
  kpi_id: string;
  name: string;
  definition_version: string;
  formula_version: string;
  formula: string;
  unit: string;
  delta_unit: string;
  target_measure: "absolute_delta" | "percent_delta";
  target_value: string;
  plain_language_definition: string;
  start_signal: string;
  end_signal: string;
  missing_timestamp_rule: string;
  calibration_method: string;
  calibration_reference: string;
  prototype_disclaimer: string;
  confidence_band_rule: ConfidenceBandRule;
}

export interface MeasurementMethod {
  version: string;
  generated_at: string;
  definitions: MeasurementMethodDefinition[];
  ama_advisory_only?: boolean;
}

export interface ReplayRequest {
  seed: string;
  run_pair_id: string;
  repetitions?: number;
  allow_degraded_mode?: boolean;
  baseline_simulation_id?: string | null;
  ama_assisted_simulation_id?: string | null;
}

export interface KpiDelta {
  kpi_id: string;
  definition_version: string;
  formula_version: string;
  formula: string;
  unit: string;
  delta_unit: string;
  calibration_reference: string;
  measurement_status?: "measured" | "no_signal";
  missing_modes?: ("baseline" | "ama_assisted")[];
  baseline_value: number | null;
  ama_assisted_value: number | null;
  absolute_delta: number | null;
  percent_delta: number | null;
  confidence_band_low: number | null;
  confidence_band_high: number | null;
  confidence_method: "bootstrap_p2_5_p97_5" | "stddev_pm1" | null;
  confidence_observation_count?: number;
  bootstrap_resamples?: number;
  imputed_observation_count?: number;
  meets_target: boolean;
  small_sample?: boolean;
  reduced_fidelity?: boolean;
  source_event_ids?: string[];
}

export interface DeterminismCheck {
  repetition_count: number;
  within_tolerance_count: number;
  diverged: boolean;
  reproduction_rate: number;
  tolerance_relative_pct?: number;
  tolerance_absolute_units?: number;
}

export interface RunProvenance {
  mode: "baseline" | "ama_assisted";
  source_run_id: string;
  scenario_version?: string | null;
  scenario_content_hash?: string | null;
  seed: string;
  source_event_ids?: string[];
  event_timestamps?: string[];
  confidence_values?: number[];
  signal_ids?: string[];
  model_output_ids?: string[];
  recommendation_ids?: string[];
  human_decision_ids?: string[];
  outcome_ids?: string[];
  component_versions?: string[];
  rejected_event_ids?: string[];
}

export interface DeltaScorecard {
  id: string;
  scenario_id: string;
  scenario_version?: string | null;
  scenario_content_hash?: string | null;
  seed: string;
  run_pair_id: string;
  idempotency_key: string;
  kpi_deltas: KpiDelta[];
  run_provenance?: RunProvenance[];
  determinism?: DeterminismCheck | null;
  imputation_share?: number;
  auditor_signoff_id?: string | null;
  auditor_id?: string | null;
  advisory_only?: boolean;
  reduced_fidelity?: boolean;
  publication_status?: "published";
  created_at: string;
  created_by?: string;
  correlation_id?: string;
}

export interface Assumption {
  id: string;
  text: string;
  resolved?: boolean;
  review_state?: "pending" | "validated" | "rejected";
  validation_method: string;
  evidence_required: string;
  owner_role: string;
  review_due_at?: string | null;
}

export interface ThreatToValidity {
  text: string;
  severity: "low" | "medium" | "high";
  mitigation: string;
}

export interface CausalChain {
  id: string;
  capability_id: string;
  capability_name: string;
  version: number;
  claim: string;
  kpis_moved: string[];
  magnitude_status: "source_grounded" | "hypothesis";
  expected_magnitude_value?: number | null;
  expected_magnitude_unit?: string | null;
  assumptions: Assumption[];
  threats_to_validity: ThreatToValidity[];
  originating_spec_path: string;
  originating_requirement: string;
  created_at: string;
  superseded_by?: string | null;
}

/** CitationRef — mandatory for non-manual benchmark rows (T-AMD-12). */
export interface CitationRef {
  organisation: string;
  document: string;
  year: number;
  url: string;
}

export interface BenchmarkEntry {
  id: string;
  kpi_id: string;
  jurisdiction: string;
  category: "fire" | "ambulance" | "ses" | "police" | "cross_sector";
  kind: "external_benchmark" | "prototype_baseline";
  source_name: string;
  source_citation?: CitationRef | null;
  provenance?: Provenance;
  benchmark_type:
    | "performance_target"
    | "operational_aim"
    | "trigger_window"
    | "metric_definition"
    | "prototype_measurement"
    | "unavailable";
  target_value?: number | null;
  target_unit: string;
  target_context: string;
  not_available?: boolean;
  created_at: string;
}

export type AuditKind =
  | "signal_ingested"
  | "model_output_recorded"
  | "recommendation_recorded"
  | "human_decision_recorded"
  | "outcome_recorded"
  | "scorecard_published"
  | "ladder_version_published"
  | "non_au_signal_refused"
  | "manual_share_blocked"
  | "auditor_signoff_recorded"
  | "kpi_amendment_recorded"
  | "degraded_mode_entered"
  | "small_sample_labelled"
  | "divergence_flagged"
  | "audit_mutation_attempted"
  | "language_fallback_used";

export interface AuditEntry {
  id: string;
  audit_id: string;
  value_id: string;
  kind: AuditKind;
  actor: string;
  occurred_at: string;
  references?: Record<string, string>;
  payload?: Record<string, unknown>;
  correlation_id?: string;
  region: "australiaeast" | "australiasoutheast";
  payload_sha256: string;
  storage_source?: "hot" | "cold" | "hot+cold";
  /** Populated on PI render replay rows when language fallback occurs (T-AMD-13). */
  language_fallback_used?: string | null;
}

export interface AuditTrace {
  value_id: string;
  entries: AuditEntry[];
  chain_complete: boolean;
  missing_references?: string[];
  served_from_cold_archive?: boolean;
}

export interface ConfidenceScore {
  value: number;
}

export interface CanonicalEventChain {
  call_received_at?: string | null;
  dispatched_at?: string | null;
  arrived_at?: string | null;
  controlled_at?: string | null;
  cleared_at?: string | null;
  imputed_fields?: string[];
}

export interface SignalIngressRequest {
  id: string;
  scenario_id: string;
  seed: string;
  mode: "baseline" | "ama_assisted";
  kpi_id:
    | "lives_saved_lagging"
    | "response_time_p1"
    | "evac_lead_lagging"
    | "logistics_efficiency"
    | "econ_loss_lagging";
  capability_id: string;
  capability_version: string;
  actor?: string | null;
  source: string;
  occurred_at: string;
  region?: string | null;
  chain: CanonicalEventChain;
  confidence: ConfidenceScore;
  reduced_fidelity?: boolean;
  advisory_only?: boolean;
  payload?: Record<string, unknown>;
  correlation_id?: string;
}

export interface Signal {
  id: string;
  scenario_id: string;
  seed: string;
  mode: "baseline" | "ama_assisted";
  kpi_id:
    | "lives_saved_lagging"
    | "response_time_p1"
    | "evac_lead_lagging"
    | "logistics_efficiency"
    | "econ_loss_lagging";
  capability_id: string;
  capability_version: string;
  actor: string;
  source: string;
  occurred_at: string;
  region: "australiaeast" | "australiasoutheast";
  chain: CanonicalEventChain;
  confidence: ConfidenceScore;
  reduced_fidelity?: boolean;
  advisory_only?: boolean;
  payload?: Record<string, unknown>;
  correlation_id?: string;
}

/** Public Information channel (T-AMD-14, FR-039). */
export interface PublicInformationChannel {
  language_code: string;
  body: string;
  fk_grade?: number | null;
  provenance?: Provenance;
  language_fallback_used?: string | null;
}

export interface AuslanAsset {
  captioned_image_url: string;
  transcript: string;
}

/** Public Information render response (T-AMD-14, FR-039). */
export interface PublicInformationRender {
  scenario_id: string;
  generated_at: string;
  channels: PublicInformationChannel[];
  advisory_only?: boolean;
  auslan?: AuslanAsset | null;
  auslan_asset_missing?: boolean;
}
