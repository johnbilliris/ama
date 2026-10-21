"""Structured scenario card produced by the Controller for user confirmation."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class GeoPoint(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: list[float]


class SimScenarioLocation(BaseModel):
    name: str
    geojson_point: GeoPoint | None = None
    resolver: Literal["azure-maps", "user-provided", "unresolved"] = "unresolved"


class SimScenarioCard(BaseModel):
    id: str
    tenant_id: str
    simulation_id: str
    hazard: Literal[
        "bushfire",
        "flood",
        "cyclone",
        "storm",
        "heat",
        "earthquake",
        "tsunami",
        "pandemic",
        "other",
    ]
    location: SimScenarioLocation
    start_at: datetime
    aws_default_level: Literal["advice", "watch_and_act", "emergency_warning"] = "advice"
    parameters: dict[str, object] = Field(default_factory=dict)
    confirmed: bool = False
    confirmed_by_oid: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    document_type: str = "sim_scenario_card"
