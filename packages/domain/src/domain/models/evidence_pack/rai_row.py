"""Pydantic v2 model for Spec-037 RaiRow (T029).

Citations: FR-024, FR-025, FR-026, FR-027, PD-037-05.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ._common import BackCitation, Provenance


class RaiCell(BaseModel):
    model_config = ConfigDict(extra="forbid")

    posture: Literal["compliant", "partial", "not-applicable"]
    summary: str = Field(min_length=1)
    na_justification: str | None = None
    evidence: list[BackCitation] = Field(min_length=1)

    @model_validator(mode="after")
    def _na_requires_justification(self) -> "RaiCell":
        if self.posture == "not-applicable" and not self.na_justification:
            raise ValueError("not-applicable cells require na_justification (FR-027)")
        return self


class NistRmfCells(BaseModel):
    model_config = ConfigDict(extra="forbid")

    govern: RaiCell
    map: RaiCell
    measure: RaiCell
    manage: RaiCell


class Frameworks(BaseModel):
    model_config = ConfigDict(extra="forbid")

    au_ai_ethics_8_principles: RaiCell
    iso_42001: RaiCell
    iso_23894: RaiCell
    nist_ai_rmf: NistRmfCells


class Principles(BaseModel):
    model_config = ConfigDict(extra="forbid")

    human_oversight: RaiCell
    fairness: RaiCell
    accountability: RaiCell
    transparency: RaiCell
    privacy: RaiCell
    safety: RaiCell
    contestability: RaiCell
    reliability: RaiCell


class RaiRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component_id: str = Field(min_length=1)
    component_kind: Literal["sub-agent", "simulation-agent", "evaluation-framework", "rag-client"]
    spec_refs: list[BackCitation] = Field(min_length=1)
    frameworks: Frameworks
    principles: Principles
    eval_evidence_refs: list[BackCitation] = Field(min_length=1)
    provenance: Provenance
