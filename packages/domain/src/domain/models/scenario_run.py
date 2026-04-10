from datetime import UTC, datetime
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
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tenant_id: str | None = None
    exercise_report_uri: str | None = None
    archive_status: Literal["pending", "archived", "failed"] | None = None
    resource_consumption: dict[str, int] = Field(default_factory=dict)
    document_type: str = "scenario_run"
