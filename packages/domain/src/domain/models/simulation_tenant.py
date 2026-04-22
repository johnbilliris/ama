import re
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from packages.domain.src.domain.models.warp_constants import (
    DEFAULT_WARP_SPEED,
    validate_warp_speed,
)
from packages.domain.src.domain.models.warp_speed_change import WarpSpeedChange

TENANT_ID_PATTERN = re.compile(r"^sim-[a-z0-9-]{36}$")

VALID_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "Provisioning": {"Active"},
    "Active": {"Paused", "Archiving"},
    "Paused": {"Active", "Archiving"},
    "Archiving": {"Archived"},
    "Archived": {"Deleted"},
}


class ResourceLimits(BaseModel):
    max_signals: int = 10_000
    max_recommendations: int = 500
    max_duration_hours: int = 48


class ResourceConsumption(BaseModel):
    signal_count: int = 0
    recommendation_count: int = 0
    storage_bytes: int = 0
    cache_keys: int = 0


class SimulationTenant(BaseModel):
    id: str = ""
    tenant_id: str
    scenario_id: str
    scenario_run_id: str
    scenario_type: Literal[
        "Bushfire",
        "Flood",
        "Cyclone",
        "Severe Storm",
        "Heatwave",
        "Earthquake",
        "Tsunami",
        "Pandemic",
        "Other",
        "Cross-jurisdiction",
    ]
    scenario_template_id: str | None = None
    status: Literal[
        "Provisioning", "Active", "Paused", "Archiving", "Archived", "Deleted"
    ] = "Provisioning"
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ttl_hours: int = 72
    expires_at: datetime | None = None
    participants: list[str] = Field(default_factory=list)
    jurisdictions: list[str] = Field(default_factory=list)
    resource_limits: ResourceLimits = Field(default_factory=ResourceLimits)
    resource_consumption: ResourceConsumption = Field(default_factory=ResourceConsumption)
    throttle_mode: Literal["normal", "throttled", "incident-throttled"] = "normal"
    throttle_quota_pct: int = 100
    exercise_report_uri: str | None = None
    archive_uri: str | None = None
    document_type: str = "simulation_tenant"

    # Deprecated: legacy client-managed elapsed time. Retained for
    # backward compatibility with pre-feature-026 clients. The API now
    # mirrors ``accumulated_sim_seconds`` into this field on responses.
    elapsed_seconds: float = 0.0

    # Feature 026: server-owned canonical simulation clock.
    current_warp_speed: float = Field(default=DEFAULT_WARP_SPEED)
    accumulated_sim_seconds: float = 0.0
    last_resumed_at: datetime | None = None
    clock_paused: bool = True
    playback_status: Literal["full", "partial", "none"] = "none"
    warp_speed_history: list[WarpSpeedChange] = Field(default_factory=list)

    @field_validator("current_warp_speed")
    @classmethod
    def _validate_warp_speed(cls, v: float) -> float:
        return validate_warp_speed(v)

    @property
    def current_sim_seconds(self) -> float:
        """Live simulated time. When running, extrapolates from ``last_resumed_at``."""
        if self.clock_paused or self.last_resumed_at is None:
            return self.accumulated_sim_seconds
        delta = (datetime.now(UTC) - self.last_resumed_at).total_seconds()
        return self.accumulated_sim_seconds + max(delta, 0.0) * self.current_warp_speed

    def model_post_init(self, __context: object) -> None:
        if not self.id:
            self.id = self.tenant_id
        if self.expires_at is None:
            from datetime import timedelta

            self.expires_at = self.created_at + timedelta(hours=self.ttl_hours)

    @field_validator("tenant_id")
    @classmethod
    def validate_tenant_id(cls, v: str) -> str:
        if not TENANT_ID_PATTERN.match(v):
            raise ValueError(f"tenant_id must match {TENANT_ID_PATTERN.pattern}, got '{v}'")
        return v

    @field_validator("participants")
    @classmethod
    def validate_participants_non_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("participants must contain at least one entry (the creator)")
        return v

    @field_validator("jurisdictions")
    @classmethod
    def uppercase_jurisdictions(cls, v: list[str]) -> list[str]:
        return [j.upper() for j in v]

    def can_transition_to(self, new_status: str) -> bool:
        allowed = VALID_STATUS_TRANSITIONS.get(self.status, set())
        return new_status in allowed

    def transition_to(
        self, new_status: str, *, elapsed_seconds: float | None = None
    ) -> "SimulationTenant":
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from '{self.status}' to '{new_status}'. "
                f"Allowed: {VALID_STATUS_TRANSITIONS.get(self.status, set())}"
            )
        updates: dict = {"status": new_status}
        if elapsed_seconds is not None:
            updates["elapsed_seconds"] = elapsed_seconds
        return self.model_copy(update=updates)
