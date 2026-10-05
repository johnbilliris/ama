from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ScenarioRunType = Literal[
    "bushfire",
    "flood",
    "cyclone",
    "severe_storm",
    "heatwave",
    "earthquake",
    "tsunami",
    "pandemic",
    "other",
    "cross_jurisdiction",
]


class ScenarioEvent(BaseModel):
    event_id: str
    offset_seconds: int
    actor: str
    decided_at: datetime
    source: str


class ScenarioRun(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    scenario_run_id: str
    scenario_name: str
    scenario_type: ScenarioRunType
    jurisdiction_ids: list[str] = Field(default_factory=list)
    organisation_ids: list[str] = Field(default_factory=list)
    framework_ids: list[str] = Field(default_factory=list)
    mode: Literal["rehearsal", "live"] = "rehearsal"
    status: Literal["queued", "running", "completed", "failed", "cancelled"] = "completed"
    model_version: str = "deterministic-v1"
    event_trace: list[ScenarioEvent] = Field(default_factory=list)
    coordination_gap_summary: list[str] = Field(default_factory=list)
    generated_findings: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    preflight_catalogue: dict[str, object] = Field(default_factory=dict)
    tenant_id: str
    exercise_report_uri: str | None = None
    archive_status: Literal["pending", "archived", "failed"] | None = None
    resource_consumption: dict[str, int] = Field(default_factory=dict)
    document_type: str = "scenario_run"
