from typing import Literal

from pydantic import BaseModel, Field


class CoordinationTask(BaseModel):
    task_id: str
    incident_id: str
    title: str
    assigned_persona_id: str
    assigned_organisation_id: str
    status: Literal["queued", "in_progress", "blocked", "completed"] = "queued"
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    dependency_task_ids: list[str] = Field(default_factory=list)
    approval_requirement: str | None = None
