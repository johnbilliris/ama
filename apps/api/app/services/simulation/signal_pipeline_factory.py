"""Spec-036 Wave 4 — Signal pipeline orchestrator factory (T-L02 / T-L06).

Wires the orchestrator's three repository / publisher / writer
dependencies together for FastAPI dependency-injection. Tests can
override any single piece via :func:`set_signal_pipeline_orchestrator_for_tests`.
"""

from __future__ import annotations

from app.repositories.synthetic_signals_repository import (
    SyntheticSignalsRepository,
    get_synthetic_signals_repository,
)
from app.services.simulation.audit_writer import (
    AuditWriter,
    get_audit_writer,
)
from app.services.simulation.event_hub_publisher import (
    EventHubPublisher,
    get_event_hub_publisher,
)
from app.services.simulation.signal_pipeline_orchestrator import (
    SignalPipelineOrchestrator,
)

_default_orchestrator: SignalPipelineOrchestrator | None = None


def build_signal_pipeline_orchestrator(
    *,
    signals_repository: SyntheticSignalsRepository | None = None,
    event_hub_publisher: EventHubPublisher | None = None,
    audit_writer: AuditWriter | None = None,
) -> SignalPipelineOrchestrator:
    """Construct a :class:`SignalPipelineOrchestrator` from ambient singletons."""

    return SignalPipelineOrchestrator(
        signals_repository=signals_repository or get_synthetic_signals_repository(),
        event_hub_publisher=event_hub_publisher or get_event_hub_publisher(),
        audit_writer=audit_writer or get_audit_writer(),
    )


def get_signal_pipeline_orchestrator() -> SignalPipelineOrchestrator:
    """Return the process-wide orchestrator (lazy, T-L02)."""

    global _default_orchestrator
    if _default_orchestrator is None:
        _default_orchestrator = build_signal_pipeline_orchestrator()
    return _default_orchestrator


def set_signal_pipeline_orchestrator_for_tests(
    orchestrator: SignalPipelineOrchestrator | None,
) -> None:
    """Inject (or reset) the process-wide orchestrator — tests only."""

    global _default_orchestrator
    _default_orchestrator = orchestrator


def reset_signal_pipeline_orchestrator_for_tests() -> None:
    """Reset the process-wide orchestrator — tests only."""

    global _default_orchestrator
    _default_orchestrator = None


__all__ = [
    "build_signal_pipeline_orchestrator",
    "get_signal_pipeline_orchestrator",
    "reset_signal_pipeline_orchestrator_for_tests",
    "set_signal_pipeline_orchestrator_for_tests",
]
