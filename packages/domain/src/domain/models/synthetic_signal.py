"""Synthetic signal — per data-model.md §1 (feature 036, FR-001/FR-008/FR-013).

Pydantic v2 model representing a typed signal injected into a simulation realm
by the Telemetry-Injection Agent (or directly by a coordinator). Frozen and
strict per Constitution Audit-and-Provenance principles.
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt

# FR-008 nine canonical categories (see plan-decision #9 freshness windows).
SignalCategory = Literal[
    "weather",
    "fire-behaviour",
    "hydrology",
    "geohazard",
    "utility",
    "transport",
    "evacuation",
    "resource",
    "comms-channel-state",
]

SignalConfidence = Literal["high", "medium", "low"]


class GeoPoint(BaseModel):
    """Latitude/longitude pair for signal localisation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class SyntheticSignal(BaseModel):
    """Typed synthetic signal envelope (FR-001, FR-008).

    Lives in Cosmos container ``simulation_synthetic_signals`` partitioned by
    ``simulation_id``. ``synthetic_signal=True`` (FR-006) is set on every
    record to guarantee no synthetic signal is ever mistakenly treated as
    real-world telemetry by downstream consumers.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    signal_id: str
    simulation_id: str
    tenant_id: str
    category: SignalCategory
    parameters: dict[str, object] = Field(default_factory=dict)
    gps: GeoPoint | None = None
    jurisdiction_code: str | None = None
    observed_at: datetime
    written_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    freshness_window_seconds: NonNegativeInt
    confidence: SignalConfidence
    contradicts: str | None = Field(
        default=None,
        description="signal_id of a prior signal contradicted by this write (FR-013)",
    )
    injection_correlation_id: str | None = Field(
        default=None,
        description="Links to injection.success audit entry",
    )
    origin_cascade_id: str | None = Field(
        default=None,
        description="Links to the cascade that emitted this signal (FR-057). Not propagated transitively.",
    )
    synthetic_signal: Literal[True] = Field(
        default=True,
        description="FR-006: every injected event MUST carry this flag.",
    )
    document_type: Literal["synthetic_signal"] = "synthetic_signal"

    @property
    def partition_key(self) -> str:
        return self.simulation_id
