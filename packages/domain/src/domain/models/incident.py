from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

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
    incident_id: str
    title: str
    incident_type: IncidentType
    status: Literal["monitoring", "active", "stabilising", "recovery", "closed", "rehearsal"]
    severity: Literal["advisory", "watch", "warning", "emergency"]
    affected_jurisdiction_ids: list[str]
    participating_organisation_ids: list[str] = Field(default_factory=list)
    owning_framework_ids: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    pprr_phase: PprrPhase | None = None
    incident_level: IncidentLevel = 1
    location: dict[str, Any] | None = None
