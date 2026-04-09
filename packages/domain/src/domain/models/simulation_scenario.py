from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class EventPhase(BaseModel):
    phase_name: str
    phase_order: int = Field(ge=1)
    duration_minutes: int = Field(ge=1)
    data_sources_active: list[str] = Field(default_factory=list)
    escalation_triggers: list[str] = Field(default_factory=list)
    signal_generation_params: dict[str, Any] = Field(default_factory=dict)


class SimulationScenario(BaseModel):
    scenario_id: str
    name: str
    scenario_type: Literal["bushfire", "flood", "cyclone", "severe_storm"]
    target_region: dict[str, Any]
    target_jurisdiction_ids: list[str] = Field(min_length=1)
    activated_data_source_ids: list[str] = Field(min_length=1)
    time_compression_ratio: float = Field(default=1.0, gt=0)
    event_phases: list[EventPhase] = Field(min_length=1)
    misinformation_ratio: float = Field(default=0.15, ge=0.0, le=1.0)
    historical_overlay_path: str | None = None
    created_by: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
