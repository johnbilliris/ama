from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class ScenarioRun(BaseModel):
    scenario_run_id: str
    scenario_name: str
    scenario_type: Literal["bushfire", "flood", "cyclone"]
    jurisdiction_ids: list[str] = Field(default_factory=list)
    organisation_ids: list[str] = Field(default_factory=list)
    framework_ids: list[str] = Field(default_factory=list)
    coordination_gap_summary: list[str] = Field(default_factory=list)
    generated_findings: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
