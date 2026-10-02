from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CoordinationTaskStatus = Literal["queued", "in_progress", "blocked", "completed"]


class CoordinationTask(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    task_id: str
    incident_id: str
    title: str
    assigned_persona_id: str
    assigned_organisation_id: str
    jurisdiction_id: str | None = None
    status: CoordinationTaskStatus = "queued"
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    dependency_task_ids: list[str] = Field(default_factory=list)
    approval_requirement: str | None = None
    blocker_reason: str | None = None
    expected_completion: datetime | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    version: int = 1
