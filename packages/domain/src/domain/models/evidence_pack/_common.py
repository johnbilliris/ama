"""Common sub-models for Spec-037 evidence-pack rows."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BackCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["spec", "adr", "governance_hub", "telemetry_sink", "agent_md"]
    ref: str = Field(min_length=1)
    section: str | None = None


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tag: Literal["automated", "manual"]
    source: str
    owner: str | None = None
    review_cadence: Literal["quarterly", "monthly", "post-incident"] | None = None
    automation_target: str | None = None
    evidence_status: Literal["Validated", "Deferred", "Unresolved"]

    @model_validator(mode="after")
    def _manual_requires_owner(self) -> Provenance:
        if self.tag == "manual":
            missing = [f for f in ("owner", "review_cadence", "automation_target") if getattr(self, f) is None]
            if missing:
                raise ValueError(f"manual provenance requires {missing}; see FR-037")
        return self
