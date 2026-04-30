"""Record of an outbound message that was blocked because it originated in a simulation."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class SimSyntheticDelivery(BaseModel):
    id: str
    tenant_id: str
    simulation_id: str
    channel: Literal["sms", "email", "broadcast", "social", "cap_push", "http"]
    audience: str
    payload_hash: str
    block_reason: Literal["sim-egress-blocked", "publication-gate", "http-wrapper-gate"]
    intended_url: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    document_type: str = "sim_synthetic_delivery"
