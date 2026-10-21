from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl

Provenance = Literal["auto", "manual"]
CapstoneScId = Literal[
    "SC-CAP-015-001",
    "SC-CAP-015-002",
    "SC-CAP-015-003",
    "SC-CAP-015-004",
    "SC-CAP-015-005",
]


class EvidenceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConfidenceBandRule(EvidenceModel):
    method: Literal["bootstrap_p2_5_p97_5", "stddev_pm1"] = "bootstrap_p2_5_p97_5"
    min_resamples: int = 1000
    fallback_label: Literal["small-sample"] = "small-sample"


class RiskAdjustment(EvidenceModel):
    likelihood: int
    consequence: int
    provenance: Provenance = "auto"
    auditor_signoff_required: bool = False


class IndicatorDefinition(EvidenceModel):
    id: str
    kpi_id: str
    version: int
    capstone_sc_id: CapstoneScId
    name: str
    kind: Literal["leading", "lagging"]
    aiims_function: Literal[
        "Control",
        "Intelligence",
        "Planning",
        "Operations",
        "Logistics",
        "PublicInformation",
    ]
    incident_level: Literal[1, 2, 3]
    life_safety_tier: Literal["life_safety", "efficiency"]
    formula: str
    formula_version: str = "040.1"
    unit: str
    owner_role: str
    refresh_cadence: str
    target_value: Decimal
    alert_threshold: Decimal
    baseline_source: str
    calibration_reference: str = "prototype baseline paired by scenario version, content hash, and seed"
    provenance: Provenance
    confidence_band_rule: ConfidenceBandRule
    risk_adjustment: RiskAdjustment | None = None
    publication_status: Literal["draft", "published", "superseded"] = "published"
    created_at: AwareDatetime
    created_by: str
    superseded_by: str | None = None


class KpiLadderGroup(EvidenceModel):
    capstone_sc_id: CapstoneScId
    leading: list[IndicatorDefinition]
    lagging: list[IndicatorDefinition]


class KpiLadderView(EvidenceModel):
    version: str
    generated_at: datetime
    groups: list[KpiLadderGroup]


class RunProvenance(EvidenceModel):
    mode: Literal["baseline", "ama_assisted"]
    source_run_id: str
    scenario_version: str | None = None
    scenario_content_hash: str | None = None
    seed: str
    source_event_ids: list[str] = Field(default_factory=list)
    event_timestamps: list[AwareDatetime] = Field(default_factory=list)
    confidence_values: list[Decimal] = Field(default_factory=list)
    signal_ids: list[str] = Field(default_factory=list)
    model_output_ids: list[str] = Field(default_factory=list)
    recommendation_ids: list[str] = Field(default_factory=list)
    human_decision_ids: list[str] = Field(default_factory=list)
    outcome_ids: list[str] = Field(default_factory=list)
    component_versions: list[str] = Field(default_factory=list)
    rejected_event_ids: list[str] = Field(default_factory=list)


class KpiDelta(EvidenceModel):
    kpi_id: str
    definition_version: str
    formula_version: str
    formula: str
    unit: str
    delta_unit: str
    calibration_reference: str
    measurement_status: Literal["measured", "no_signal"] = "measured"
    missing_modes: list[Literal["baseline", "ama_assisted"]] = Field(default_factory=list)
    baseline_value: Decimal | None
    ama_assisted_value: Decimal | None
    absolute_delta: Decimal | None
    percent_delta: Decimal | None
    confidence_band_low: Decimal | None
    confidence_band_high: Decimal | None
    confidence_method: Literal["bootstrap_p2_5_p97_5", "stddev_pm1"] | None
    confidence_observation_count: int = 0
    bootstrap_resamples: int = 0
    imputed_observation_count: int = 0
    meets_target: bool
    small_sample: bool = False
    reduced_fidelity: bool = False
    source_event_ids: list[str] = Field(default_factory=list)


class DeterminismCheck(EvidenceModel):
    repetition_count: int
    within_tolerance_count: int
    diverged: bool
    tolerance_relative_pct: float = 2.0
    tolerance_absolute_units: float = 1.0


class DeltaScorecard(EvidenceModel):
    id: str
    scenario_id: str
    scenario_version: str | None = None
    scenario_content_hash: str | None = None
    seed: str
    run_pair_id: str
    idempotency_key: str
    kpi_deltas: list[KpiDelta]
    run_provenance: list[RunProvenance] = Field(default_factory=list)
    determinism: DeterminismCheck | None = None
    imputation_share: Decimal = Decimal("0")
    auditor_signoff_id: str | None = None
    auditor_id: str | None = None
    advisory_only: bool = True
    reduced_fidelity: bool = False
    publication_status: Literal["published"] = "published"
    created_at: AwareDatetime
    created_by: str = "system"
    correlation_id: str = ""


class Assumption(EvidenceModel):
    id: str
    text: str
    resolved: bool = False
    review_state: Literal["pending", "validated", "rejected"] = "pending"
    validation_method: str
    evidence_required: str
    owner_role: str
    review_due_at: AwareDatetime | None = None


class ThreatToValidity(EvidenceModel):
    text: str
    severity: Literal["low", "medium", "high"]
    mitigation: str


class CausalChain(EvidenceModel):
    id: str
    capability_id: str
    capability_name: str
    version: int
    claim: str
    kpis_moved: list[str]
    magnitude_status: Literal["source_grounded", "hypothesis"]
    expected_magnitude_value: Decimal | None = None
    expected_magnitude_unit: str | None = None
    assumptions: list[Assumption]
    threats_to_validity: list[ThreatToValidity]
    originating_spec_path: str
    originating_requirement: str
    created_at: AwareDatetime
    superseded_by: str | None = None


class CitationRef(EvidenceModel):
    organisation: str
    document: str
    year: int
    url: HttpUrl


class BenchmarkEntry(EvidenceModel):
    id: str
    kpi_id: str
    jurisdiction: str
    category: Literal["fire", "ambulance", "ses", "police", "cross_sector"]
    kind: Literal["external_benchmark", "prototype_baseline"]
    source_name: str
    source_citation: CitationRef | None = None
    provenance: Provenance = "auto"
    benchmark_type: Literal[
        "performance_target",
        "operational_aim",
        "trigger_window",
        "metric_definition",
        "prototype_measurement",
        "unavailable",
    ]
    target_value: Decimal | None = None
    target_unit: str
    target_context: str
    not_available: bool = False
    created_at: AwareDatetime


class AuditEntry(EvidenceModel):
    id: str
    audit_id: str
    value_id: str
    kind: str
    actor: str
    occurred_at: AwareDatetime
    references: dict[str, str] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str = ""
    region: Literal["australiaeast", "australiasoutheast"]
    payload_sha256: str
    language_fallback_used: str | None = None
    storage_source: Literal["hot", "cold", "hot+cold"] = "hot"


class AuditTrace(EvidenceModel):
    value_id: str
    entries: list[AuditEntry]
    chain_complete: bool
    missing_references: list[str] = Field(default_factory=list)
    served_from_cold_archive: bool = False


class PublicInformationChannel(EvidenceModel):
    language_code: str
    body: str
    fk_grade: float | None = None
    provenance: Provenance = "auto"
    language_fallback_used: str | None = None


class AuslanAsset(EvidenceModel):
    captioned_image_url: str
    transcript: str


class PublicInformationRender(EvidenceModel):
    scenario_id: str
    generated_at: AwareDatetime
    channels: list[PublicInformationChannel]
    auslan: AuslanAsset | None = None
    auslan_asset_missing: bool = False
    advisory_only: bool = True


class CanonicalEventChain(EvidenceModel):
    call_received_at: AwareDatetime | None = None
    dispatched_at: AwareDatetime | None = None
    arrived_at: AwareDatetime | None = None
    controlled_at: AwareDatetime | None = None
    cleared_at: AwareDatetime | None = None
    imputed_fields: list[str] = Field(default_factory=list)


class ConfidenceScore(EvidenceModel):
    value: Decimal


class SignalIngressRequest(EvidenceModel):
    id: str
    scenario_id: str
    seed: str
    mode: Literal["baseline", "ama_assisted"]
    kpi_id: str
    capability_id: str
    capability_version: str
    actor: str | None = None
    source: str
    occurred_at: AwareDatetime
    region: str | None = None
    chain: CanonicalEventChain
    confidence: ConfidenceScore
    reduced_fidelity: bool = False
    advisory_only: bool = False
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str = ""


class Signal(SignalIngressRequest):
    actor: str
    region: Literal["australiaeast", "australiasoutheast"]


class ReplayRequest(EvidenceModel):
    seed: str
    run_pair_id: str
    repetitions: int = 1
    allow_degraded_mode: bool = True
    baseline_simulation_id: str | None = None
    ama_assisted_simulation_id: str | None = None


class MeasurementMethodDefinition(EvidenceModel):
    capstone_sc_id: str
    kpi_id: str
    name: str
    definition_version: str
    formula_version: str
    formula: str
    unit: str
    delta_unit: str
    target_measure: Literal["absolute_delta", "percent_delta"]
    target_value: str
    plain_language_definition: str
    start_signal: str
    end_signal: str
    missing_timestamp_rule: str
    calibration_method: str
    calibration_reference: str
    prototype_disclaimer: str
    confidence_band_rule: ConfidenceBandRule


class MeasurementMethod(EvidenceModel):
    version: str
    generated_at: AwareDatetime
    definitions: list[MeasurementMethodDefinition]
    ama_advisory_only: bool = True


__all__ = [
    "Assumption",
    "AuditEntry",
    "AuditTrace",
    "AuslanAsset",
    "BenchmarkEntry",
    "CanonicalEventChain",
    "CausalChain",
    "CitationRef",
    "ConfidenceBandRule",
    "ConfidenceScore",
    "DeltaScorecard",
    "DeterminismCheck",
    "IndicatorDefinition",
    "KpiDelta",
    "KpiLadderGroup",
    "KpiLadderView",
    "MeasurementMethod",
    "MeasurementMethodDefinition",
    "PublicInformationChannel",
    "PublicInformationRender",
    "ReplayRequest",
    "RiskAdjustment",
    "RunProvenance",
    "Signal",
    "SignalIngressRequest",
    "ThreatToValidity",
]
