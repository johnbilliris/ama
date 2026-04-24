"""Immutable record of a warp-speed transition during a simulation."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class WarpSpeedChange(BaseModel):
    """Embedded value object appended to ``SimulationTenant.warp_speed_history``."""

    model_config = ConfigDict(frozen=True)

    sim_time_offset: float = Field(ge=0.0)
    old_speed: float
    new_speed: float
    changed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
