"""PPRR Phase Context — non-incident PPRR phases for regions and scenarios.

Supports Prevention and Preparedness phases that apply without an active incident.
Links to an incident when the phase transitions to Response/Recovery.

FRs: FR-050 | Research: R-001
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class PprrPhaseContext(BaseModel):
    context_id: str
    context_type: Literal["region", "scenario"]
    context_reference_id: str
    pprr_phase: Literal["prevention", "preparedness"]
    activated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    activated_by: str
    deactivated_at: datetime | None = None
    transitioned_to_incident_id: str | None = None
    notes: str = ""

    @model_validator(mode="after")
    def _validate_transition(self) -> "PprrPhaseContext":
        if self.transitioned_to_incident_id is not None and self.deactivated_at is None:
            msg = "deactivated_at must be set when transitioned_to_incident_id is set"
            raise ValueError(msg)
        return self
