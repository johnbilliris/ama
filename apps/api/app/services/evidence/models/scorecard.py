# Delta scorecard models with explicit measurement and event provenance.

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, computed_field, model_validator

DEFAULT_TOL_REL_PCT = 2.0
DEFAULT_TOL_ABS_UNIT = 1.0
Decimal4 = Annotated[Decimal, Field(max_digits=24, decimal_places=4)]
Percent4 = Annotated[Decimal, Field(max_digits=12, decimal_places=4)]
Confidence4 = Annotated[Decimal, Field(ge=0, le=1, max_digits=5, decimal_places=4)]
Share4 = Annotated[Decimal, Field(ge=0, le=1, max_digits=5, decimal_places=4)]
EXPECTED_CAPSTONE_KPI_IDS = frozenset(
    {
        "lives_saved_lagging",
        "response_time_p1",
        "evac_lead_lagging",
        "logistics_efficiency",
        "econ_loss_lagging",
    }
)


class RunProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["baseline", "ama_assisted"]
    source_run_id: str
    scenario_version: str | None = None
    scenario_content_hash: str | None = None
    seed: str
    source_event_ids: list[str] = Field(default_factory=list)
    event_timestamps: list[AwareDatetime] = Field(default_factory=list)
    confidence_values: list[Confidence4] = Field(default_factory=list)
    signal_ids: list[str] = Field(default_factory=list)
    model_output_ids: list[str] = Field(default_factory=list)
    recommendation_ids: list[str] = Field(default_factory=list)
    human_decision_ids: list[str] = Field(default_factory=list)
    outcome_ids: list[str] = Field(default_factory=list)
    component_versions: list[str] = Field(default_factory=list)
    rejected_event_ids: list[str] = Field(default_factory=list)


class KpiDelta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kpi_id: str
    definition_version: str
    formula_version: str
    formula: str
    unit: str
    delta_unit: str
    calibration_reference: str
    measurement_status: Literal["measured", "no_signal"] = "measured"
    missing_modes: list[Literal["baseline", "ama_assisted"]] = Field(default_factory=list)
    baseline_value: Decimal4 | None
    ama_assisted_value: Decimal4 | None
    absolute_delta: Decimal4 | None
    percent_delta: Percent4 | None
    confidence_band_low: Decimal4 | None
    confidence_band_high: Decimal4 | None
    confidence_method: Literal["bootstrap_p2_5_p97_5", "stddev_pm1"] | None
    confidence_observation_count: int = Field(default=0, ge=0)
    bootstrap_resamples: int = Field(default=0, ge=0)
    imputed_observation_count: int = Field(default=0, ge=0)
    meets_target: bool
    small_sample: bool = False
    reduced_fidelity: bool = False
    source_event_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _no_signal_is_explicit(self) -> KpiDelta:
        if self.measurement_status == "no_signal":
            self.reduced_fidelity = True
            self.meets_target = False
            self.absolute_delta = None
            self.percent_delta = None
            self.confidence_band_low = None
            self.confidence_band_high = None
            self.confidence_method = None
            return self
        required = (
            self.baseline_value,
            self.ama_assisted_value,
            self.absolute_delta,
            self.confidence_band_low,
            self.confidence_band_high,
            self.confidence_method,
        )
        if any(value is None for value in required):
            raise ValueError("measured KPI deltas require values and a confidence band")
        return self


class DeterminismCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repetition_count: int = Field(ge=1)
    within_tolerance_count: int = Field(ge=0)
    diverged: bool
    tolerance_relative_pct: float = DEFAULT_TOL_REL_PCT
    tolerance_absolute_units: float = DEFAULT_TOL_ABS_UNIT

    @computed_field  # type: ignore[prop-decorator]
    @property
    def reproduction_rate(self) -> float:
        return self.within_tolerance_count / self.repetition_count


class DeltaScorecard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    scenario_id: str
    scenario_version: str | None = None
    scenario_content_hash: str | None = None
    seed: str
    run_pair_id: str
    idempotency_key: str
    kpi_deltas: list[KpiDelta] = Field(min_length=5, max_length=5)
    run_provenance: list[RunProvenance] = Field(default_factory=list, max_length=2)
    determinism: DeterminismCheck | None = None
    imputation_share: Share4 = Decimal("0")
    auditor_signoff_id: str | None = None
    auditor_id: str | None = None
    advisory_only: bool = True
    reduced_fidelity: bool = False
    publication_status: Literal["published"] = "published"
    created_at: AwareDatetime
    created_by: str = "system"
    correlation_id: str = ""

    @model_validator(mode="after")
    def _validate_scorecard(self) -> DeltaScorecard:
        kpi_ids = [delta.kpi_id for delta in self.kpi_deltas]
        if len(set(kpi_ids)) != len(kpi_ids) or set(kpi_ids) != EXPECTED_CAPSTONE_KPI_IDS:
            raise ValueError("scorecard must contain each canonical capstone KPI exactly once")
        if any(delta.reduced_fidelity for delta in self.kpi_deltas):
            self.reduced_fidelity = True
        measured = [delta for delta in self.kpi_deltas if delta.measurement_status == "measured"]
        if measured and (not self.scenario_version or not self.scenario_content_hash):
            raise ValueError("measured scorecards require scenario version and content hash")
        return self
