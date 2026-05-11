"""T-A03: SyntheticDeliveryReceipt unit tests (FR-019)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from domain.models.synthetic_delivery_receipt import SyntheticDeliveryReceipt
from pydantic import ValidationError


def _kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "delivery_id": str(uuid4()),
        "simulation_id": str(uuid4()),
        "tenant_id": "sim-tenant-a",
        "channel": "sms",
        "receipt_status": "delivered",
        "latency_ms": 120,
    }
    base.update(overrides)
    return base


def test_synthetic_delivery_receipt_happy() -> None:
    r = SyntheticDeliveryReceipt(**_kwargs())
    assert r.partition_key == r.simulation_id


def test_synthetic_delivery_receipt_channel_constrained() -> None:
    with pytest.raises(ValidationError):
        SyntheticDeliveryReceipt(**_kwargs(channel="passenger-pigeon"))


def test_synthetic_delivery_receipt_status_constrained() -> None:
    with pytest.raises(ValidationError):
        SyntheticDeliveryReceipt(**_kwargs(receipt_status="exploded"))
