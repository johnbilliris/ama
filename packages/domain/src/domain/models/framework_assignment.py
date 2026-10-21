from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FrameworkAssignment(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    assignment_id: str
    framework_id: str
    jurisdiction_id: str | None = None
    organisation_id: str | None = None
    effective_from: datetime = Field(default_factory=lambda: datetime.now(UTC))
    effective_to: datetime | None = None
    overrides: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_scope_and_window(self) -> "FrameworkAssignment":
        if not self.jurisdiction_id and not self.organisation_id:
            raise ValueError("Either jurisdiction_id or organisation_id must be provided")
        if self.effective_to is not None and self.effective_to <= self.effective_from:
            raise ValueError("effective_to must be after effective_from")
        return self


def is_effective(assignment: FrameworkAssignment, at: datetime) -> bool:
    reference = at.astimezone(UTC)
    start = assignment.effective_from.astimezone(UTC)
    end = assignment.effective_to.astimezone(UTC) if assignment.effective_to else None
    if start > reference:
        return False
    if end is not None and end <= reference:
        return False
    return True
