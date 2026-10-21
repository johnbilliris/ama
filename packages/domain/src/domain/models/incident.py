from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

IncidentType = Literal[
    "biosecurity",
    "bushfire",
    "criminal",
    "cyclone",
    "earthquake",
    "environment",
    "flood",
    "health",
    "industrial",
    "landslide",
    "maritime_coastal",
    "storm",
    "tornado",
    "transport",
    "tsunami",
    "urban_fire",
    "extreme_heat",
    "pandemic",
    "other",
]

PprrPhase = Literal["prevention", "preparedness", "response", "recovery"]

IncidentLevel = Literal[1, 2, 3]


class Incident(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    incident_id: str
    title: str
    incident_type: IncidentType
    status: Literal["monitoring", "active", "stabilising", "recovery", "closed", "rehearsal"]
    severity: Literal["advisory", "watch", "warning", "emergency"]
    affected_jurisdiction_ids: list[str]
    participating_organisation_ids: list[str] = Field(default_factory=list)
    owning_framework_ids: list[str] = Field(default_factory=list)
    current_objectives: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ended_at: datetime | None = None
    pprr_phase: PprrPhase | None = None
    incident_level: IncidentLevel = 1
    location: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _validate_invariants(self) -> "Incident":
        if not self.affected_jurisdiction_ids:
            raise ValueError("affected_jurisdiction_ids must include at least one jurisdiction")
        if self.status not in {"recovery", "closed"} and self.ended_at is not None:
            raise ValueError("ended_at may only be set when status is recovery or closed")
        if self.ended_at is not None and self.ended_at <= self.started_at:
            raise ValueError("ended_at must be after started_at")
        return self
