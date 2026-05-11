"""Dispatch-status primitives for spec-036 Cycle 2 (T-AA08 / A2-01 / FR-067).

Owns the shared types and constants used by the inject-telemetry route layer
(`apps/api/app/api/routes/simulations_036.py`) and the signal-pipeline
orchestrator (`apps/api/app/services/simulation/signal_pipeline_orchestrator.py`)
to surface degraded-dispatch outcomes per pass-2 Q1 (3-value enum) and
pass-2 Q2 (always-present `degraded_dispatch` flag).

Cycle 2 invariants honoured here:

- ``DispatchStatus`` is a closed three-value Literal — ``acknowledged`` |
  ``failed`` | ``timed_out`` (pass-2 Q1). Rate-limit and circuit-open
  conditions are subsumed into ``failed`` with the ``exception_class`` field
  on the ``signal_pipeline.dispatch_failed`` audit envelope carrying the
  granularity (audit-envelope.md §3.25).
- ``DISPATCH_ACK_TIMEOUT_SECONDS`` is the per-subscriber transport budget
  (Event-Hubs publish + subscriber ack); 5.0 s aligns with ADR-036-007's
  ``Retry-After: 5`` cadence (contracts/error-responses.md:162) and is
  2.5× SLI-Z1's 2000 ms breach threshold.
- ``TriggerSource`` here is the **narrow two-value** enum used exclusively
  by the new ``signal_pipeline.dispatch_failed`` envelope (pass-1 Q4 +
  data-model §11.5). The four-value Cycle 1 enum
  ``{subscriber, controller_intent, cascade, lifecycle}`` continues to apply
  to ``injection.success`` / ``SubAgentInvocationRecord`` etc.
- ``TriggeredSubAgent`` is the canonical Pydantic shape for each entry in
  the ``triggered_sub_agents`` array — used in BOTH the HTTP 202 response
  body (``TelemetryInjectionAck``) and the ``signal_pipeline.dispatch_failed``
  audit envelope's array, with byte-equality enforced by RFC 8785 JCS
  canonicalisation (pass-1 Q1 + CHK135).
- ``model_config = ConfigDict(extra="forbid")`` prevents silent field
  addition that would break the byte-equality invariant.

Tests live under ``tests/unit/test_dispatch_status_enum.py``,
``tests/unit/test_dispatch_ack_timeout_constant.py``, and
``tests/unit/test_triggered_sub_agent_pydantic.py``.
"""

from __future__ import annotations

from typing import Final, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from packages.domain.src.domain.models.aiims_mapping import SubAgent

#: Per-subscriber dispatch acknowledgement timeout (Cycle 2 pass-2 Q1).
#:
#: Measured from the orchestrator's ``await self._publisher.publish(event)``
#: call to the subscriber's ack arrival. Anything exceeding this window is
#: classified ``timed_out``; an explicit raise during publish or pre-ack
#: receipt is ``failed``. This is **distinct** from FR-006's 120 s sub-agent
#: reply timeout — different concerns (transport vs compute).
DISPATCH_ACK_TIMEOUT_SECONDS: Final[float] = 5.0


#: Three-value transport-layer outcome enum (Cycle 2 pass-2 Q1).
#:
#: - ``acknowledged`` — subscriber acked within ``DISPATCH_ACK_TIMEOUT_SECONDS``.
#: - ``failed`` — orchestrator raised before/at publish; rate-limit and
#:   circuit-open conditions are subsumed here, with ``exception_class``
#:   on the dispatch-failed envelope carrying granularity.
#: - ``timed_out`` — no ack within ``DISPATCH_ACK_TIMEOUT_SECONDS``.
DispatchStatus = Literal["acknowledged", "failed", "timed_out"]


#: Tuple form for iteration / contract tests.
ALL_DISPATCH_STATUSES: Final[tuple[str, ...]] = (
    "acknowledged",
    "failed",
    "timed_out",
)


#: Narrowed two-value trigger-source for the NEW ``signal_pipeline.dispatch_failed``
#: envelope (Cycle 2 pass-1 Q4 + data-model §11.5).
#:
#: - ``primary`` — direct subscriber fan-out from the inject-telemetry path.
#: - ``cascade`` — depth-1 cascade fan-out (per FR-057).
#:
#: The wider four-value enum
#: ``{subscriber, controller_intent, cascade, lifecycle}`` continues to apply
#: to the Cycle 1 ``injection.success`` envelope and ``SubAgentInvocationRecord``;
#: ``primary`` does NOT appear in those surfaces.
TriggerSource = Literal["primary", "cascade"]


#: Tuple form for iteration / contract tests.
ALL_TRIGGER_SOURCES: Final[tuple[str, ...]] = ("primary", "cascade")


class TriggeredSubAgent(BaseModel):
    """Canonical Pydantic shape for one ``triggered_sub_agents`` entry.

    Used in BOTH the HTTP 202 response body (``TelemetryInjectionAck``) and
    the ``signal_pipeline.dispatch_failed`` audit envelope's array. The
    ``extra="forbid"`` model config is critical for the Cycle 2 pass-1 Q1
    byte-equality invariant (CHK135) — silent field addition would break the
    one-line `json.dumps(body, sort_keys=True) == json.dumps(audit, ...)`
    assertion in ``tests/contract/test_dispatch_failed_body_audit_byte_equality.py``.

    Field semantics:

    * ``sub_agent`` — PascalCase 9-name ``SubAgent`` Literal (per Cycle 2
      Amendment A2-07 / FR-070, audit-envelope.md §3.2 line 150).
    * ``trigger_source`` — narrow two-value enum (``primary`` | ``cascade``)
      per pass-1 Q4 + data-model §11.5.
    * ``correlation_id`` — **per-subscriber** dispatch UUID (one fresh UUID
      per fan-out edge, distinct from the parent ``injection_correlation_id``)
      per pass-1 Q4. Reused as the ``correlation_id`` field on subsequent
      ``sub_agent.timeout`` / ``sub_agent.cancel`` / ``sub_agent.degraded``
      envelopes raised against the same fan-out edge so a single-stream JOIN
      reconstructs the per-subscriber timeline.
    * ``dispatch_status`` — three-value transport-layer outcome
      (``acknowledged`` | ``failed`` | ``timed_out``) per pass-2 Q1.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    sub_agent: SubAgent = Field(
        description=("Canonical 9-member PascalCase SubAgent Literal (Cycle 2 A2-07 / FR-070)."),
    )
    trigger_source: TriggerSource = Field(
        description=(
            "Narrow two-value enum exclusive to the dispatch-failed surface (Cycle 2 pass-1 Q4 + data-model §11.5)."
        ),
    )
    correlation_id: UUID = Field(
        description=(
            "Per-subscriber dispatch UUID (one fresh UUID per fan-out edge). "
            "DISTINCT from the parent injection_correlation_id (pass-1 Q4)."
        ),
    )
    dispatch_status: DispatchStatus = Field(
        description=("Three-value transport outcome — acknowledged within 5.0 s, failed, or timed_out (pass-2 Q1)."),
    )


__all__ = [
    "ALL_DISPATCH_STATUSES",
    "ALL_TRIGGER_SOURCES",
    "DISPATCH_ACK_TIMEOUT_SECONDS",
    "DispatchStatus",
    "TriggerSource",
    "TriggeredSubAgent",
]
