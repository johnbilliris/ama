"""Tenant-scoped Event Hubs publisher — spec-036 Phase L (T-L04) / FR-051.

Publishes signal-pipeline events (``signal.persisted`` and
``signal.fanned_out``) onto the tenant-scoped Event Hub
``synthetic-signals-{tenant_id}``. Authentication is AAD-only via
:class:`azure.identity.DefaultAzureCredential` (Managed Identity in
production, developer credentials locally).

Auto-connect pattern
--------------------
* If :mod:`azure.eventhub` is installed and the publisher is constructed
  with a ``namespace`` (e.g. ``my-ns.servicebus.windows.net``), the
  publisher binds a real
  :class:`azure.eventhub.aio.EventHubProducerClient` per tenant.
* Otherwise the publisher falls back to an in-process queue so that
  unit / contract tests can exercise the round-trip without
  infrastructure. The captured events are observable via
  :meth:`captured_events_for` for assertion.
"""

from __future__ import annotations

import logging
import os
from collections import defaultdict
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Final, Literal

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from azure.eventhub.aio import EventHubProducerClient

logger = logging.getLogger(__name__)

EventKind = Literal["signal.persisted", "signal.fanned_out"]


class SignalPipelineEvent(BaseModel):
    """Wire payload for a signal-pipeline event.

    Tenant + simulation IDs route the event; ``correlation_id`` ties the
    event back to the originating ``audit.injection.success`` envelope so
    AAR (FR-054) can stitch the timeline.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    tenant_id: str
    simulation_id: str
    signal_id: str
    kind: EventKind
    correlation_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


_TENANT_HUB_PREFIX: Final[str] = "synthetic-signals-"


class _InMemoryProducer:
    """Test-time stand-in for :class:`EventHubProducerClient`."""

    def __init__(self) -> None:
        self._events: dict[str, list[SignalPipelineEvent]] = defaultdict(list)

    async def send(self, hub_name: str, event: SignalPipelineEvent) -> None:
        self._events[hub_name].append(event)

    async def send_batch(self, hub_name: str, events: list[SignalPipelineEvent]) -> None:
        self._events[hub_name].extend(events)

    def events_for(self, hub_name: str) -> list[SignalPipelineEvent]:
        return list(self._events[hub_name])


class EventHubPublisher:
    """AAD-authenticated, tenant-scoped Event Hubs publisher."""

    def __init__(self, namespace: str | None = None) -> None:
        self._namespace = namespace
        self._producer: _InMemoryProducer | None
        self._producer_factory: Callable[[str], EventHubProducerClient] | None = None
        if namespace is None:
            self._producer = _InMemoryProducer()
            return

        try:
            # Lazy import: azure-eventhub is an optional dependency. When
            # absent, fall back to in-memory mode so unit tests still run.
            from azure.eventhub.aio import (
                EventHubProducerClient,
            )
            from azure.identity.aio import DefaultAzureCredential

            credential = DefaultAzureCredential()
            self._producer_factory = lambda hub: EventHubProducerClient(
                fully_qualified_namespace=namespace,
                eventhub_name=hub,
                credential=credential,
            )
            self._producer = None  # connections are per-hub, lazily opened
        except ImportError:
            logger.warning(
                "EventHubPublisher: azure-eventhub not installed; falling back to in-memory producer for namespace=%s",
                namespace,
            )
            self._producer = _InMemoryProducer()

    @staticmethod
    def hub_name_for(tenant_id: str) -> str:
        """Return the tenant-scoped Event Hub name (FR-051)."""

        return f"{_TENANT_HUB_PREFIX}{tenant_id}"

    async def publish(self, event: SignalPipelineEvent) -> None:
        """Publish a single event to its tenant Event Hub."""

        hub = self.hub_name_for(event.tenant_id)
        if isinstance(self._producer, _InMemoryProducer):
            await self._producer.send(hub, event)
            return

        # Real-Azure path — wraps the SDK call.
        producer_factory = self._producer_factory
        if producer_factory is None:
            raise RuntimeError("Event Hub producer factory is not configured")
        producer = producer_factory(hub)
        try:
            from azure.eventhub import EventData

            event_data = EventData(event.model_dump_json())
            await producer.send_event(event_data)
        finally:
            await producer.close()

    async def publish_batch(self, events: list[SignalPipelineEvent]) -> None:
        """Publish a batch of events. All events MUST share the same tenant."""

        if not events:
            return

        tenants = {e.tenant_id for e in events}
        if len(tenants) > 1:
            raise ValueError(
                "EventHubPublisher.publish_batch requires a single tenant per "
                f"call; got {sorted(tenants)!r}. Split the batch by tenant."
            )

        hub = self.hub_name_for(events[0].tenant_id)
        if isinstance(self._producer, _InMemoryProducer):
            await self._producer.send_batch(hub, events)
            return

        producer_factory = self._producer_factory
        if producer_factory is None:
            raise RuntimeError("Event Hub producer factory is not configured")
        producer = producer_factory(hub)
        try:
            from azure.eventhub import EventData

            batch = await producer.create_batch()
            for event in events:
                batch.add(EventData(event.model_dump_json()))
            await producer.send_batch(batch)
        finally:
            await producer.close()

    def captured_events_for(self, tenant_id: str) -> list[SignalPipelineEvent]:
        """Return events captured by the in-memory producer (test helper)."""

        if not isinstance(self._producer, _InMemoryProducer):
            raise RuntimeError(
                "captured_events_for is only available when running against "
                "the in-memory fallback (no Event Hubs namespace bound)."
            )
        return self._producer.events_for(self.hub_name_for(tenant_id))


__all__ = [
    "EventHubPublisher",
    "EventKind",
    "SignalPipelineEvent",
    "build_event_hub_publisher",
    "get_event_hub_publisher",
    "reset_event_hub_publisher_for_tests",
]


_default_publisher: EventHubPublisher | None = None


def build_event_hub_publisher() -> EventHubPublisher:
    """Build a tenant-scoped publisher honouring environment configuration.

    T-L06 — production wiring is selected via the
    ``SIM036_EVENT_HUB_NAMESPACE`` env var. When unset the publisher
    falls back to the in-memory producer (FR-051 unit/contract tests).
    """

    namespace = os.environ.get("SIM036_EVENT_HUB_NAMESPACE")
    if namespace:
        logger.info(
            "EventHubPublisher: binding production producer for namespace=%s",
            namespace,
        )
        return EventHubPublisher(namespace=namespace)
    logger.info("EventHubPublisher: SIM036_EVENT_HUB_NAMESPACE unset — using in-memory producer")
    return EventHubPublisher()


def get_event_hub_publisher() -> EventHubPublisher:
    """Return the process-wide :class:`EventHubPublisher` (lazy, T-L06)."""

    global _default_publisher
    if _default_publisher is None:
        _default_publisher = build_event_hub_publisher()
    return _default_publisher


def reset_event_hub_publisher_for_tests() -> None:
    """Reset the process-wide singleton — tests only."""

    global _default_publisher
    _default_publisher = None
