"""Pillar C — Delta Scorecard + Determinism Check (T-C05, FR-015 / FR-016)."""

from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field, condecimal, model_validator

DEFAULT_TOL_REL_PCT = 2.0
DEFAULT_TOL_ABS_UNIT = 1.0


class KpiDelta(BaseModel):
    kpi_id: str
    baseline_value: condecimal(max_digits=18, decimal_places=4)
    ama_assisted_value: condecimal(max_digits=18, decimal_places=4)
    absolute_delta: condecimal(max_digits=18, decimal_places=4)
    percent_delta: condecimal(max_digits=8, decimal_places=4)
    confidence_band_low: condecimal(max_digits=18, decimal_places=4)
    confidence_band_high: condecimal(max_digits=18, decimal_places=4)
    confidence_method: Literal["bootstrap_p2_5_p97_5", "stddev_pm1"]
    meets_target: bool
    small_sample: bool = False
    reduced_fidelity: bool = False


class DeterminismCheck(BaseModel):
    repetition_count: int = Field(ge=1)
    within_tolerance_count: int = Field(ge=0)
    diverged: bool
    tolerance_relative_pct: float = DEFAULT_TOL_REL_PCT
    tolerance_absolute_units: float = DEFAULT_TOL_ABS_UNIT

    @property
    def reproduction_rate(self) -> float:
        if self.repetition_count == 0:
            return 0.0
        return self.within_tolerance_count / self.repetition_count


class DeltaScorecard(BaseModel):
    id: str
    scenario_id: str
    seed: str
    run_pair_id: str
    kpi_deltas: list[KpiDelta] = Field(min_length=5, max_length=5)
    determinism: DeterminismCheck | None = None
    advisory_only: bool = True
    reduced_fidelity: bool = False
    created_at: AwareDatetime
    created_by: str = "system"
    correlation_id: str = ""

    @model_validator(mode="after")
    def _propagate_reduced_fidelity(self) -> DeltaScorecard:
        if any(d.reduced_fidelity for d in self.kpi_deltas):
            self.reduced_fidelity = True
        return self
