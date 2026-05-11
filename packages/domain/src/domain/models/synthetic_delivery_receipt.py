"""Synthetic delivery receipt — per data-model.md §3 (feature 036, FR-019).

Captures synthetic-delivery acks from blocked outbound communications.
Distinct from ``sim_synthetic_delivery`` (the spec-024 record): this is the
receipt-side artefact emitted on the simulated transport channel.
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt

DeliveryChannel = Literal[
    "sms",
    "email",
    "broadcast",
    "social",
    "cap_push",
    "http",
    "voice",
]

ReceiptStatus = Literal[
    "delivered",
    "queued",
    "failed",
    "blocked",
    "deferred",
]


class SyntheticDeliveryReceipt(BaseModel):
    """Receipt confirming a synthetic delivery (FR-019)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    delivery_id: str
    signal_id: str | None = Field(
        default=None,
        description="Optional link back to the signal that triggered the warning.",
    )
    simulation_id: str
    tenant_id: str
    channel: DeliveryChannel
    receipt_status: ReceiptStatus
    latency_ms: NonNegativeInt
    received_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    audience: str | None = None
    error_code: str | None = None
    payload_hash: str | None = Field(
        default=None,
        pattern=r"^[a-f0-9]{64}$",
    )
    document_type: Literal["synthetic_delivery_receipt"] = "synthetic_delivery_receipt"

    @property
    def partition_key(self) -> str:
        return self.simulation_id
