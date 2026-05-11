"""Signal pipeline orchestrator — spec-036 Phase L (T-L01) / FR-009 / FR-015 / FR-051.

Owns the synthetic-signal write→publish→fan-out invariant per
plan-decision 20:

1. Persist a :class:`SyntheticSignal` durably via
   :class:`SyntheticSignalsRepository` (T-L03; partition by
   ``simulation_id``, idempotent upsert).
2. Publish a ``signal.persisted`` :class:`SignalPipelineEvent` to the
   tenant-scoped Event Hub via :class:`EventHubPublisher` (T-L04).
3. Resolve sub-agent subscribers via :func:`subscribers_for` (T-L05) — the
   closed-set registry per FR-051. Categories that don't map to a
   ``SignalKind`` (e.g. ``utility``, ``transport``, ``geohazard``) are a
   graceful no-op; only structural errors raise.
4. Publish a ``signal.fanned_out`` event per subscriber and write a
   ``synthetic-delivery`` audit envelope so AAR (FR-054) can stitch the
   timeline.

Cycle 2 / T-AA13 / Amendment A2-01 additions:

* **Per-subscriber correlation_id** — pass-1 Q4. Each subscriber gets a
  fresh ``uuid4()`` distinct from the injection-level ``correlation_id``.
  The mapping is surfaced via :attr:`DispatchResult.per_subscriber_correlations`
  so the route handler can populate ``TriggeredSubAgent.correlation_id``.

* **Hybrid OTel TraceContext propagation** — pass-2 Q3. The injection-level
  ``correlation_id`` (UUID) becomes the parent W3C ``trace_id`` (16-byte hex
  derived from ``uuid.UUID(corr).bytes``). Each per-subscriber
  ``correlation_id`` becomes the child ``span_id`` (8-byte hex derived from
  ``uuid.UUID(sub_corr).bytes[:8]``). Both also surface as
  ``customDimensions["injection_correlation_id"]`` and
  ``customDimensions["correlation_id"]`` so SLI KQL queries can join across
  the trace.

* **5 s per-edge timeout** — ``DISPATCH_ACK_TIMEOUT_SECONDS`` from
  :mod:`apps.api.app.services.simulation.dispatch_status` bounds each
  ``await self._publisher.publish(event)``. Timeouts surface as
  :class:`asyncio.TimeoutError` and are caught by the Wave B handler in
  ``simulations_036.py`` so the response body's per-subscriber
  ``dispatch_status`` is correctly set to ``timed_out``.

Constitution invariants honoured:

- **Primacy of Life** — hazard signals reach their subscribers in the
  same orchestrator turn (no silent drop). A subscriber registry miss
  short-circuits BEFORE any audit write so the operator sees the empty
  fan-out and can recover.
- **Synthetic-only egress** — every published event carries
  ``metadata={"synthetic": True}`` (FR-006). Downstream consumers MUST
  filter on this.
- **AIIMS alignment** — fan-out ordering follows the registry's
  PascalCase ``SubAgent`` enum order; the audit entry's
  ``aiims_function`` is auto-derived from the ``SubAgent`` -> AIIMS map
  in :mod:`packages.domain.src.domain.models.aiims_mapping`.

Tests live in ``tests/unit/test_signal_pipeline_orchestrator_036.py``.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from hashlib import sha256
from typing import TYPE_CHECKING, Final
from uuid import UUID, uuid4

from app.services.simulation.dispatch_status import (
    DISPATCH_ACK_TIMEOUT_SECONDS,
)
from app.services.simulation.event_hub_publisher import (
    SignalPipelineEvent,
)
from app.services.simulation.subscriber_registry import (
    SignalKind,
    subscribers_for,
)

from packages.domain.src.domain.models.aiims_mapping import (
    AGENT_TO_AIIMS,
    SubAgent,
)
from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal

if TYPE_CHECKING:  # pragma: no cover
    from app.repositories.synthetic_signals_repository import (
        SyntheticSignalsRepository,
    )
    from app.services.simulation.audit_writer import AuditWriter
    from app.services.simulation.event_hub_publisher import (
        EventHubPublisher,
    )

logger = logging.getLogger(__name__)


# ---- Category → SignalKind bridge --------------------------------------
#
# The synthetic-signal Pydantic enum (``SignalCategory``) is broader than
# the subscriber registry's :data:`SignalKind`; collapse hazard-bearing
# categories down to the three registry kinds. Categories not in this
# map produce an empty fan-out (graceful no-op).

_CATEGORY_TO_KIND: Final[dict[str, SignalKind]] = {
    "weather": "hazard",
    "fire-behaviour": "hazard",
    "hydrology": "hazard",
    "geohazard": "hazard",
    "evacuation": "hazard",
    "resource": "resource",
    "comms-channel-state": "channel-state",
}


def _trace_id_from_correlation_id(correlation_id: str) -> str:
    """Cycle 2 pass-2 Q3 — derive the 16-byte hex W3C ``trace_id``.

    The injection-level ``correlation_id`` is a UUID; its 16 raw bytes form
    the parent OTel ``trace_id``. ``correlation_id`` strings that are not
    UUIDs (e.g. test fixtures with stable strings) fall back to a hex digest
    of the encoded form so the function never raises.
    """

    try:
        return UUID(correlation_id).bytes.hex()
    except (TypeError, ValueError):
        digest = sha256(correlation_id.encode("utf-8")).digest()
        return digest[:16].hex()


def _span_id_from_correlation_id(correlation_id: UUID | str) -> str:
    """Cycle 2 pass-2 Q3 — derive the 8-byte hex W3C ``span_id``."""

    try:
        if isinstance(correlation_id, UUID):
            raw = correlation_id.bytes
        else:
            raw = UUID(str(correlation_id)).bytes
    except (TypeError, ValueError):
        raw = sha256(str(correlation_id).encode("utf-8")).digest()
    return raw[:8].hex()


# ---- Result type -------------------------------------------------------


@dataclass(frozen=True)
class SubscriberDispatchOutcome:
    """Cycle 2 / T-AA14 — per-subscriber dispatch result.

    Surfaced as one entry per attempted subscriber via
    :attr:`DispatchResult.subscriber_outcomes`. The route handler in
    ``simulations_036.py`` consumes this list to build the byte-equal
    ``triggered_sub_agents`` array on the HTTP 202 response body and
    on the ``signal_pipeline.dispatch_failed`` audit envelope.
    """

    sub_agent: SubAgent
    correlation_id: UUID
    dispatch_status: str  # acknowledged | failed | timed_out
    span_id: str = ""
    exception_class: str | None = None
    exception_message: str | None = None


@dataclass(frozen=True)
class DispatchResult:
    """Outcome of a single :meth:`SignalPipelineOrchestrator.dispatch`."""

    signal_id: str
    simulation_id: str
    tenant_id: str
    correlation_id: str
    fanned_out_to: tuple[SubAgent, ...] = field(default_factory=tuple)
    persisted: bool = True
    skipped_reason: str | None = None
    #: Cycle 2 / T-AA13 / pass-1 Q4 — per-subscriber correlation_id mapping.
    #: Each entry is a fresh UUID distinct from the parent
    #: ``correlation_id`` so the route handler can surface it as
    #: ``TriggeredSubAgent.correlation_id`` in the response body's array.
    per_subscriber_correlations: dict[SubAgent, UUID] = field(default_factory=dict)
    #: Cycle 2 / T-AA13 / pass-2 Q3 — hybrid OTel propagation.
    #: 16-byte hex W3C ``trace_id`` derived from the injection-level
    #: ``correlation_id``; surfaced as ``customDimensions["injection_correlation_id"]``.
    otel_trace_id: str = ""
    #: Per-subscriber 8-byte hex ``span_id`` derived from each
    #: ``per_subscriber_correlations[subscriber]``.
    otel_span_ids: dict[SubAgent, str] = field(default_factory=dict)
    #: Cycle 2 / T-AA14 / pass-2 Q1 — per-subscriber dispatch outcome
    #: (``acknowledged``, ``failed``, ``timed_out``). One entry per
    #: ATTEMPTED subscriber. The route handler uses this to populate the
    #: ``triggered_sub_agents`` array on both the HTTP 202 response body
    #: and the ``signal_pipeline.dispatch_failed`` audit envelope.
    subscriber_outcomes: tuple[SubscriberDispatchOutcome, ...] = field(default_factory=tuple)
    #: Cycle 2 / T-AA14 — convenience flag mirroring
    #: ``any(o.dispatch_status != "acknowledged" for o in subscriber_outcomes)``.
    degraded_dispatch: bool = False


# ---- Orchestrator ------------------------------------------------------


class SignalPipelineOrchestrator:
    """Wire :class:`SyntheticSignalsRepository`, :class:`EventHubPublisher`,
    :func:`subscribers_for`, and :class:`AuditWriter` together.

    The orchestrator is intentionally stateless beyond its dependencies — a
    single instance is safe to share across the FastAPI request lifecycle.
    """

    def __init__(
        self,
        *,
        signals_repository: SyntheticSignalsRepository,
        event_hub_publisher: EventHubPublisher,
        audit_writer: AuditWriter,
    ) -> None:
        self._signals = signals_repository
        self._publisher = event_hub_publisher
        self._audit = audit_writer

    @staticmethod
    def category_to_signal_kind(category: str) -> SignalKind | None:
        """Return the :data:`SignalKind` for *category* or ``None``."""

        return _CATEGORY_TO_KIND.get(category)

    async def dispatch(
        self,
        signal: SyntheticSignal,
        *,
        correlation_id: str | None = None,
    ) -> DispatchResult:
        """Persist + publish + fan-out a synthetic signal in one turn.

        Returns a :class:`DispatchResult` describing the outcome. The
        result is **non-failing** for the empty-fan-out case (an unknown
        category) — callers must inspect ``fanned_out_to`` if they need
        to gate UI behaviour on subscriber count.
        """

        corr = correlation_id or str(uuid4())
        # Cycle 2 / T-AA13 / pass-2 Q3 — derive the parent OTel trace_id
        # from the injection-level correlation_id so SLI KQL queries can
        # join requests/dependencies via customDimensions.
        otel_trace_id = _trace_id_from_correlation_id(corr)
        logger.debug(
            "signal_pipeline.dispatch.start signal=%s correlation_id=%s trace_id=%s",
            signal.signal_id,
            corr,
            otel_trace_id,
        )

        # Step 1 — persist (idempotent).
        await self._signals.persist(signal)

        # Step 2 — publish ``signal.persisted``.
        persisted_event = SignalPipelineEvent(
            tenant_id=signal.tenant_id,
            simulation_id=signal.simulation_id,
            signal_id=signal.signal_id,
            kind="signal.persisted",
            correlation_id=corr,
            metadata={
                "synthetic": True,
                "category": signal.category,
                "confidence": signal.confidence,
                "injection_correlation_id": corr,
                "otel_trace_id": otel_trace_id,
            },
        )
        await self._publisher.publish(persisted_event)

        # Step 3 — resolve subscribers.
        kind = self.category_to_signal_kind(signal.category)
        if kind is None:
            logger.info(
                "signal_pipeline.no_subscribers signal_id=%s category=%s",
                signal.signal_id,
                signal.category,
            )
            return DispatchResult(
                signal_id=signal.signal_id,
                simulation_id=signal.simulation_id,
                tenant_id=signal.tenant_id,
                correlation_id=corr,
                fanned_out_to=(),
                skipped_reason="no_subscribers_for_category",
                otel_trace_id=otel_trace_id,
            )

        subscribers = sorted(subscribers_for(kind))

        # Step 4 — publish + audit per subscriber.
        payload_hash = self._payload_hash(signal)
        per_subscriber_correlations: dict[SubAgent, UUID] = {}
        otel_span_ids: dict[SubAgent, str] = {}
        outcomes: list[SubscriberDispatchOutcome] = []
        acknowledged: list[SubAgent] = []

        for subscriber in subscribers:
            # Cycle 2 / T-AA13 / pass-1 Q4 — fresh per-subscriber
            # correlation_id distinct from parent.
            sub_corr = uuid4()
            per_subscriber_correlations[subscriber] = sub_corr
            sub_span_id = _span_id_from_correlation_id(sub_corr)
            otel_span_ids[subscriber] = sub_span_id

            event = SignalPipelineEvent(
                tenant_id=signal.tenant_id,
                simulation_id=signal.simulation_id,
                signal_id=signal.signal_id,
                kind="signal.fanned_out",
                correlation_id=corr,
                metadata={
                    "synthetic": True,
                    "subscriber": subscriber,
                    "category": signal.category,
                    "injection_correlation_id": corr,
                    "correlation_id": str(sub_corr),
                    "otel_trace_id": otel_trace_id,
                    "otel_span_id": sub_span_id,
                },
            )

            # Cycle 2 / T-AA14 / pass-2 Q1 — per-edge classification. Each
            # publish + ack is bounded by ``DISPATCH_ACK_TIMEOUT_SECONDS``
            # (5 s). On timeout we record ``timed_out``; on any other
            # exception we record ``failed``; on success we record
            # ``acknowledged`` and emit the synthetic-delivery audit. The
            # loop continues so the response body and dispatch_failed
            # envelope can carry one entry per ATTEMPTED subscriber
            # (audit-envelope.md §3.25 + spec.md L248-277 / pass-1 Q1).
            try:
                await asyncio.wait_for(
                    self._publisher.publish(event),
                    timeout=DISPATCH_ACK_TIMEOUT_SECONDS,
                )
            except TimeoutError as exc:
                logger.warning(
                    "signal_pipeline.subscriber.timeout signal=%s subscriber=%s",
                    signal.signal_id,
                    subscriber,
                )
                outcomes.append(
                    SubscriberDispatchOutcome(
                        sub_agent=subscriber,
                        correlation_id=sub_corr,
                        dispatch_status="timed_out",
                        span_id=sub_span_id,
                        exception_class=type(exc).__name__,
                        exception_message=str(exc)[:1000],
                    )
                )
                continue
            except Exception as exc:  # noqa: BLE001 — Cycle 2 per-subscriber
                logger.exception(
                    "signal_pipeline.subscriber.failed signal=%s subscriber=%s",
                    signal.signal_id,
                    subscriber,
                )
                outcomes.append(
                    SubscriberDispatchOutcome(
                        sub_agent=subscriber,
                        correlation_id=sub_corr,
                        dispatch_status="failed",
                        span_id=sub_span_id,
                        exception_class=type(exc).__name__,
                        exception_message=str(exc)[:1000],
                    )
                )
                continue

            # Acknowledged path — emit synthetic-delivery audit envelope.
            await self._emit_synthetic_delivery_audit(
                signal=signal,
                subscriber=subscriber,
                correlation_id=corr,
                payload_hash=payload_hash,
                subscriber_correlation_id=str(sub_corr),
                otel_trace_id=otel_trace_id,
                otel_span_id=sub_span_id,
            )
            outcomes.append(
                SubscriberDispatchOutcome(
                    sub_agent=subscriber,
                    correlation_id=sub_corr,
                    dispatch_status="acknowledged",
                    span_id=sub_span_id,
                )
            )
            acknowledged.append(subscriber)

        degraded = any(o.dispatch_status != "acknowledged" for o in outcomes)

        return DispatchResult(
            signal_id=signal.signal_id,
            simulation_id=signal.simulation_id,
            tenant_id=signal.tenant_id,
            correlation_id=corr,
            fanned_out_to=tuple(acknowledged),
            per_subscriber_correlations=per_subscriber_correlations,
            otel_trace_id=otel_trace_id,
            otel_span_ids=otel_span_ids,
            subscriber_outcomes=tuple(outcomes),
            degraded_dispatch=degraded,
        )

    async def _emit_synthetic_delivery_audit(
        self,
        *,
        signal: SyntheticSignal,
        subscriber: SubAgent,
        correlation_id: str,
        payload_hash: str,
        subscriber_correlation_id: str | None = None,
        otel_trace_id: str | None = None,
        otel_span_id: str | None = None,
    ) -> None:
        """Write a ``synthetic-delivery`` envelope per fan-out (FR-054)."""

        try:
            aiims = AGENT_TO_AIIMS.get(subscriber)
            await self._audit.write(
                "synthetic-delivery",
                simulation_id=signal.simulation_id,
                actor="signal_pipeline_orchestrator",
                correlation_id=subscriber_correlation_id or correlation_id,
                request_correlation_id=correlation_id,
                aiims_function=aiims,
                details={
                    "channel": "event-hub",
                    "audience": subscriber,
                    "message_id": f"sim-msg-{signal.signal_id.replace('-', '')[:16]}",
                    "sim_timestamp": signal.observed_at,
                    "block_reason": "simulation_tenant_egress_blocked",
                    "payload_hash": payload_hash,
                    "watermark_applied": True,
                },
            )
        except Exception:  # pragma: no cover - defensive
            logger.exception(
                "signal_pipeline.synthetic_delivery_audit_failed signal=%s subscriber=%s",
                signal.signal_id,
                subscriber,
            )

    @staticmethod
    def _payload_hash(signal: SyntheticSignal) -> str:
        """SHA-256 hex digest of the canonical JSON payload (FR-006)."""

        return sha256(signal.model_dump_json().encode("utf-8")).hexdigest()


__all__ = [
    "DispatchResult",
    "SignalPipelineOrchestrator",
    "SubscriberDispatchOutcome",
]
