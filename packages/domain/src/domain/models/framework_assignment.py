from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class FrameworkAssignment(BaseModel):
    assignment_id: str
    framework_id: str
    jurisdiction_id: str | None = None
    organisation_id: str | None = None
    effective_from: datetime = Field(default_factory=lambda: datetime.now(UTC))
    effective_to: datetime | None = None
    overrides: dict[str, Any] = Field(default_factory=dict)
