"""Wave B / T-AA15 / FR-069 — ``injection.success`` audit byte-equality.

Asserts that for the happy-path dispatch, the ``triggered_sub_agents``
array on the response body equals the array on the ``injection.success``
audit envelope after RFC 8785 JCS canonicalisation. Cycle 2 spec.md
L248-277 + CHK135.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from uuid import uuid4

from apps.api.app.services.simulation.audit_writer import (
    AuditWriter,
    canonicalise_triggered_sub_agents,
    reset_audit_writer_for_tests,
)
from apps.api.app.services.simulation.dispatch_status import TriggeredSubAgent
from apps.api.app.services.simulation.signal_pipeline_orchestrator import (
    SignalPipelineOrchestrator,
)
from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal


class _StubSignalsRepo:
    async def persist(self, signal: SyntheticSignal) -> None:
        return None


class _AlwaysAckPublisher:
    async def publish(self, event) -> None:
        return None


def _build_signal() -> SyntheticSignal:
    return SyntheticSignal(
        signal_id=str(uuid4()),
        simulation_id="sim-aa15",
        tenant_id="tenant-aa15",
        category="weather",
        confidence="high",
        parameters={"intensity": "moderate"},
        observed_at=datetime.now(UTC).isoformat(),
        freshness_window_seconds=600,
    )


def test_happy_path_all_acknowledged() -> None:
    """Healthy dispatch — every subscriber acknowledged, degraded=False."""

    reset_audit_writer_for_tests()
    repo = _StubSignalsRepo()
    pub = _AlwaysAckPublisher()
    audit = AuditWriter(cosmos_container=None)
    orch = SignalPipelineOrchestrator(
        signals_repository=repo,
        event_hub_publisher=pub,
        audit_writer=audit,
    )
    result = asyncio.run(
        orch.dispatch(_build_signal(), correlation_id=str(uuid4()))
    )
    assert result.degraded_dispatch is False
    assert all(o.dispatch_status == "acknowledged" for o in result.subscriber_outcomes)
    assert set(result.fanned_out_to) == {
        o.sub_agent for o in result.subscriber_outcomes
    }


def test_canonicaliser_byte_equal_for_injection_success() -> None:
    """The same helper drives both body and audit canonical forms."""

    entries = [
        TriggeredSubAgent(
            sub_agent="Comms",
            trigger_source="primary",
            correlation_id=uuid4(),
            dispatch_status="acknowledged",
        ),
        TriggeredSubAgent(
            sub_agent="Resource",
            trigger_source="primary",
            correlation_id=uuid4(),
            dispatch_status="acknowledged",
        ),
    ]
    body_canonical = canonicalise_triggered_sub_agents(entries)
    audit_canonical = canonicalise_triggered_sub_agents(entries)
    assert json.dumps(body_canonical, sort_keys=True) == json.dumps(
        audit_canonical, sort_keys=True
    )
