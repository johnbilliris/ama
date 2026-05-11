"""Unit tests for spec-036 T-L04 — Event Hubs publisher for tenant-scoped
signal pipeline.

Per tasks.md §5 (Phase L) and FR-051:

* AAD-authenticated; uses Managed Identity / DefaultAzureCredential.
* Event Hub name is tenant-scoped (``synthetic-signals-{tenant_id}``).
* Emits ``signal.persisted`` and ``signal.fanned_out`` events with a
  parent ``correlation_id``.
* Supports batch publish.

Tests run against the in-memory fallback (no ``azure.eventhub`` package
required) — production deployments wire up the real
:class:`azure.eventhub.EventHubProducerClient` via Managed Identity.
"""

from __future__ import annotations

import pytest

from apps.api.app.services.simulation.event_hub_publisher import (
    EventHubPublisher,
    SignalPipelineEvent,
)


def _event(
    *,
    tenant_id: str = "tenant-a",
    simulation_id: str = "sim-1",
    signal_id: str = "sig-1",
    kind: str = "signal.persisted",
    correlation_id: str = "corr-abc",
) -> SignalPipelineEvent:
    return SignalPipelineEvent(
        tenant_id=tenant_id,
        simulation_id=simulation_id,
        signal_id=signal_id,
        kind=kind,  # type: ignore[arg-type]
        correlation_id=correlation_id,
    )


@pytest.mark.asyncio
async def test_publish_records_event_in_memory() -> None:
    publisher = EventHubPublisher()
    evt = _event()

    await publisher.publish(evt)

    captured = publisher.captured_events_for("tenant-a")
    assert len(captured) == 1
    assert captured[0].signal_id == "sig-1"


@pytest.mark.asyncio
async def test_publish_routes_per_tenant_event_hub() -> None:
    """Tenant scoping per FR-051 — events are isolated per tenant."""

    publisher = EventHubPublisher()
    await publisher.publish(_event(tenant_id="tenant-a", signal_id="a1"))
    await publisher.publish(_event(tenant_id="tenant-b", signal_id="b1"))

    a = publisher.captured_events_for("tenant-a")
    b = publisher.captured_events_for("tenant-b")
    assert {e.signal_id for e in a} == {"a1"}
    assert {e.signal_id for e in b} == {"b1"}


@pytest.mark.asyncio
async def test_publish_batch_writes_all_events() -> None:
    publisher = EventHubPublisher()
    batch = [_event(signal_id=f"s{i}") for i in range(5)]

    await publisher.publish_batch(batch)

    captured = publisher.captured_events_for("tenant-a")
    assert {e.signal_id for e in captured} == {"s0", "s1", "s2", "s3", "s4"}


@pytest.mark.asyncio
async def test_publish_batch_validates_single_tenant_per_call() -> None:
    """An Event Hubs batch is single-partition; mixed tenants are rejected."""

    publisher = EventHubPublisher()
    batch = [
        _event(tenant_id="tenant-a", signal_id="a1"),
        _event(tenant_id="tenant-b", signal_id="b1"),
    ]
    with pytest.raises(ValueError):
        await publisher.publish_batch(batch)


@pytest.mark.asyncio
async def test_event_kind_must_be_canonical() -> None:
    """Only ``signal.persisted`` and ``signal.fanned_out`` are valid kinds."""

    with pytest.raises(ValueError):
        _event(kind="signal.unknown")


@pytest.mark.asyncio
async def test_event_hub_name_is_tenant_scoped() -> None:
    publisher = EventHubPublisher()

    assert publisher.hub_name_for("tenant-a") == "synthetic-signals-tenant-a"


@pytest.mark.asyncio
async def test_correlation_id_propagates_into_event_payload() -> None:
    publisher = EventHubPublisher()
    evt = _event(correlation_id="corr-xyz")

    await publisher.publish(evt)

    captured = publisher.captured_events_for("tenant-a")
    assert captured[0].correlation_id == "corr-xyz"


@pytest.mark.asyncio
async def test_publisher_falls_back_when_azure_eventhub_unavailable() -> None:
    """When ``azure.eventhub`` is not installed, publisher uses in-memory mode."""

    publisher = EventHubPublisher(namespace="missing.servicebus.windows.net")
    # We don't actually have az sdk; publisher still operates against memory.
    assert publisher._producer is None or publisher._producer.__class__.__name__ in (
        "_InMemoryProducer",
        "object",
    )
