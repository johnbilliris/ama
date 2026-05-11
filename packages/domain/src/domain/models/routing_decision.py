"""Routing decision — 5-step jurisdiction ladder result (feature 036, FR-021).

Records every jurisdiction-inference decision so audit replay can reconstruct
the ladder steps deterministically. Cosmos container ``routing_decisions``
partitioned by ``simulation_id``.
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LadderStep = Literal[
    "explicit_payload",
    "operator_asserted",
    "viewport_hint_revalidated",
    "strtree_polygon",
    "abs_sa4_fallback",
]

Confidence = Literal["high", "medium", "ambiguous"]


class RoutingDecision(BaseModel):
    """Outcome of one jurisdiction-routing pass (FR-021)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    decision_id: str
    simulation_id: str
    tenant_id: str
    chat_turn_id: str | None = None
    steps_attempted: list[LadderStep]
    final_jurisdiction_code: str | None
    confidence: Confidence
    viewport_hint_used: bool = False
    viewport_hint_match: bool | None = None
    viewport_centroid_lat: float | None = None
    viewport_centroid_lng: float | None = None
    jurisdiction_dataset_version: str | None = None
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    document_type: Literal["routing_decision"] = "routing_decision"

    @property
    def partition_key(self) -> str:
        return self.simulation_id
