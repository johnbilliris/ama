"""Pydantic v2 model for Spec-037 AdoptionWave (T027).

Citations: FR-015, FR-016, FR-017, FR-018.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ._common import BackCitation, Provenance

_WAVE_ID_RE = re.compile(r"^WAVE-\d{2}$")
_JURISDICTIONS = {"NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT", "Commonwealth"}


class TrainingExerciseCadence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    frequency: Literal["monthly", "quarterly", "biannual", "annual", "per-wave"]
    cite: list[BackCitation] = Field(min_length=1)


class AdoptionWave(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wave_id: str
    cohort: Literal[
        "state-lead", "local-government", "utilities", "transport", "volunteer-ngo", "commonwealth"
    ]
    jurisdictions: list[str] = Field(min_length=1)
    lead_agency: dict[str, str]
    readiness_gates: list[str] = Field(min_length=1)
    training_exercise_cadence: TrainingExerciseCadence
    change_management_artefacts: list[str] = Field(min_length=1)
    decommission_rollback_criteria: list[str] = Field(min_length=1)
    back_citations: list[BackCitation] = Field(min_length=1)
    provenance: Provenance

    @field_validator("wave_id")
    @classmethod
    def _wave_id_pattern(cls, v: str) -> str:
        if not _WAVE_ID_RE.match(v):
            raise ValueError(f"wave_id must match WAVE-NN; got {v!r}")
        return v

    @field_validator("jurisdictions")
    @classmethod
    def _jurisdictions_enum(cls, v: list[str]) -> list[str]:
        for j in v:
            if j not in _JURISDICTIONS:
                raise ValueError(f"unknown jurisdiction {j!r}")
        if len(set(v)) != len(v):
            raise ValueError("jurisdictions must be unique within a wave")
        return v
