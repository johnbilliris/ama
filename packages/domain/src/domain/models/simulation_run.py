from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

VALID_TRANSITIONS: dict[str, set[str]] = {
    "configuring": {"running", "aborted"},
    "running": {"completed", "aborted"},
    "completed": set(),
    "aborted": set(),
}


class SimulationRun(BaseModel):
    run_id: str
    scenario_id: str
    status: Literal["configuring", "running", "completed", "aborted"] = "configuring"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    current_phase: str = ""
    signals_generated: dict[str, int] = Field(default_factory=dict)
    total_signals: int = 0
    time_compression_ratio: float = Field(default=1.0, gt=0)
    misinformation_ratio: float = Field(default=0.15, ge=0.0, le=1.0)
    created_by: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def transition_to(self, new_status: str) -> "SimulationRun":
        allowed = VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from '{self.status}' to '{new_status}'. "
                f"Allowed: {allowed or 'none (terminal state)'}"
            )
        updates: dict[str, object] = {"status": new_status}
        if new_status == "running":
            updates["started_at"] = datetime.now(UTC)
        elif new_status in ("completed", "aborted"):
            updates["completed_at"] = datetime.now(UTC)
        return self.model_copy(update=updates)

    @model_validator(mode="after")
    def validate_timestamps(self) -> "SimulationRun":
        if self.status == "running" and self.started_at is None:
            raise ValueError("started_at required when status is 'running'")
        if self.status in ("completed", "aborted") and self.completed_at is None:
            raise ValueError("completed_at required when status is terminal")
        return self
