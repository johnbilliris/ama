from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


ResolutionState = Literal["pending", "replayed", "discarded", "escalated"]
EntryType = Literal["handoff_failure", "ingestion_failure", "event_delivery_failure"]


class DeadLetterEntry(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True,
        populate_by_name=True,
        alias_generator=_to_camel,
    )

    entry_id: str
    entry_type: EntryType
    correlation_id: str
    original_payload: dict[str, object] = Field(default_factory=dict)
    failure_reason: str = Field(min_length=1)
    failure_code: str = Field(min_length=1)
    attempt_count: int = Field(default=1, ge=1, le=3)
    retry_count: int = Field(default=0, ge=0, le=2)
    source_service: str
    target_service: str
    incident_id: str | None = None
    tenant_scope_key: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reviewed_at: datetime | None = None
    reviewed_by: str | None = None
    resolution: ResolutionState = "pending"

    @model_validator(mode="after")
    def _validate_invariants(self) -> "DeadLetterEntry":
        if not self.original_payload:
            raise ValueError("original_payload must not be empty")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if self.reviewed_at is not None and self.reviewed_at.tzinfo is None:
            raise ValueError("reviewed_at must be timezone-aware")
        if self.attempt_count != self.retry_count + 1:
            raise ValueError("attempt_count must equal retry_count + 1")
        if self.resolution != "pending" and not self.reviewed_by:
            raise ValueError("reviewed_by is required when resolution is not pending")
        return self

    def _assert_resolution_transition(self, next_resolution: ResolutionState) -> None:
        if self.resolution == "pending" and next_resolution in {"replayed", "discarded", "escalated"}:
            return
        if self.resolution == next_resolution:
            return
        raise ValueError(f"invalid resolution transition: {self.resolution} -> {next_resolution}")

    def resolve(
        self,
        *,
        resolution: ResolutionState,
        reviewed_by: str,
        reviewed_at: datetime | None = None,
        notes: str | None = None,
    ) -> None:
        self._assert_resolution_transition(resolution)
        self.reviewed_by = reviewed_by
        self.reviewed_at = reviewed_at or datetime.now(UTC)
        self.resolution = resolution
        if notes:
            self.original_payload["resolution_notes"] = notes

    def __setattr__(self, name: str, value: object) -> None:
        if name == "resolution" and "resolution" in self.__dict__:
            self._assert_resolution_transition(value)  # type: ignore[arg-type]
        super().__setattr__(name, value)
