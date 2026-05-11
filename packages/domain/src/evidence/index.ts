// Spec-038 evidence-harness TypeScript domain twins (T-S05).
//
// Hand-mirrored to the Pydantic models at
// `apps/api/app/services/evidence/models/`. Schema parity is asserted by
// the contract tests against `specs/038-success-criteria/contracts/openapi.evidence-harness.yaml`.

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
  method: "bootstrap_p2_5_p97_5" | "stddev_pm1";
  min_resamples: number;
  fallback_label?: "small-sample";
}

export interface RiskAdjustment {
  likelihood: number; // 1..5
  consequence: number; // 1..5
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
  unit: string;
  owner_role: string;
  refresh_cadence: string;
  target_value: number;
  alert_threshold: number;
  baseline_source: string;
  provenance: Provenance;
  confidence_band_rule: ConfidenceBandRule;
  risk_adjustment?: RiskAdjustment | null;
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

export interface KpiDelta {
  kpi_id: string;
  baseline_value: number;
  ama_assisted_value: number;
  absolute_delta: number;
  percent_delta: number;
  confidence_band_low: number;
  confidence_band_high: number;
  confidence_method: "bootstrap_p2_5_p97_5" | "stddev_pm1";
  meets_target: boolean;
  small_sample?: boolean;
  reduced_fidelity?: boolean;
}

export interface DeterminismCheck {
  repetition_count: number;
  within_tolerance_count: number;
  diverged: boolean;
  reproduction_rate?: number;
  tolerance_relative_pct?: number;
  tolerance_absolute_units?: number;
}

export interface DeltaScorecard {
  id: string;
  scenario_id: string;
  seed: string;
  run_pair_id: string;
  kpi_deltas: KpiDelta[];
  determinism?: DeterminismCheck | null;
  advisory_only?: boolean;
  reduced_fidelity?: boolean;
  created_at: string;
}

export interface Assumption {
  text: string;
  resolved: boolean;
}

export interface ThreatToValidity {
  text: string;
  severity: "low" | "medium" | "high";
}

export interface CausalChain {
  id: string;
  capability_id: string;
  capability_name: string;
  version: number;
  kpis_moved: string[];
  expected_magnitude_value: number;
  expected_magnitude_unit: string;
  assumptions: Assumption[];
  threats_to_validity: ThreatToValidity[];
  originating_spec_path: string;
}

export interface BenchmarkEntry {
  id: string;
  kpi_id: string;
  jurisdiction: string;
  kind: "external_benchmark" | "prototype_baseline";
  source_name: string;
  source_citation: string;
  target_value?: number | null;
  target_unit: string;
  not_available?: boolean;
}

export type AuditKind =
  | "signal_ingested"
  | "scorecard_published"
  | "ladder_version_published"
  | "non_au_signal_refused"
  | "manual_share_blocked"
  | "auditor_signoff_recorded"
  | "kpi_amendment_recorded"
  | "degraded_mode_entered"
  | "small_sample_labelled"
  | "divergence_flagged";

export interface AuditEntry {
  id: string;
  audit_id: string;
  value_id: string;
  kind: AuditKind;
  actor: string;
  occurred_at: string;
  references: Record<string, string>;
  payload?: Record<string, unknown>;
  correlation_id?: string;
  region: "australiaeast" | "australiasoutheast";
  archived_to_blob?: boolean;
}

export interface AuditTrace {
  value_id: string;
  entries: AuditEntry[];
  chain_complete: boolean;
  served_from_cold_archive?: boolean;
}
