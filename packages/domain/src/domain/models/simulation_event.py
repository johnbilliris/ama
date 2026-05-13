"""Domain models for recorded simulation events, snapshots and scheduler state.

Feature 026-sim-warp-playback introduces a dedicated Cosmos container
``sim-events`` that stores a monotonic event stream per simulation, plus
periodic playback snapshots. The signal scheduler cursor lives alongside
the ``simulation`` container documents.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

SimulationEventType = Literal[
    "signal_delivered",
    "chat_turn_user",
    "chat_turn_assistant",
    "tool_invocation",
    "state_change",
    "warp_speed_change",
    "annotation",
    "ui_log",
]


class SimulationEvent(BaseModel):
    """A single recorded event in the canonical simulation timeline."""

    id: str = Field(default_factory=lambda: f"evt-{uuid4()}")
    tenant_id: str
    event_seq: int = Field(ge=1)
    event_type: SimulationEventType
    sim_time_offset: float = Field(ge=0.0)
    wall_clock_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = Field(default_factory=dict)
    schema_version: int = 1
    document_type: str = "simulation_event"


class PlaybackSnapshot(BaseModel):
    """Periodic state snapshot used to accelerate playback scrub."""

    id: str = Field(default_factory=lambda: f"snap-{uuid4()}")
    tenant_id: str
    event_seq: int = Field(ge=1)
    sim_time_offset: float = Field(ge=0.0)
    state: dict[str, Any] = Field(default_factory=dict)
    wall_clock_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    document_type: str = "playback_snapshot"


class SignalSchedulerState(BaseModel):
    """Durable cursor tracking which signal the warp scheduler delivers next."""

    id: str
    tenant_id: str
    next_signal_index: int = 0
    last_delivered_signal_id: str | None = None
    last_delivery_sim_time: float = 0.0
    scheduler_owner: str | None = None
    heartbeat_at: datetime | None = None
    delivery_lag_seconds: float = 0.0
    document_type: str = "signal_scheduler_state"
