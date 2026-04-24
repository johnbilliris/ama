"""Unit tests for :class:`SimulationEventRecorder` (feature 026)."""

from __future__ import annotations

import pytest
from app.repositories.simulation_event_repository import SimulationEventRepository
from app.services.simulation_event_recorder import SimulationEventRecorder


@pytest.fixture
def tenant_id() -> str:
    return "sim-" + "a" * 36


@pytest.fixture
def recorder() -> tuple[SimulationEventRecorder, SimulationEventRepository]:
    repo = SimulationEventRepository()
    return SimulationEventRecorder(repo), repo


def test_record_event_creates_sequential_events(recorder, tenant_id) -> None:
    rec, repo = recorder
    rec.record_signal_delivered(
        tenant_id,
        0.0,
        signal_id="sig-1",
        data_source_id="ds-1",
        category="bushfire",
        offset_seconds=0.0,
    )
    rec.record_signal_delivered(
        tenant_id,
        5.0,
        signal_id="sig-2",
        data_source_id="ds-1",
        category="bushfire",
        offset_seconds=5.0,
    )
    events = repo.list_events(tenant_id)
    assert [e.event_seq for e in events] == [1, 2]
    assert events[0].event_type == "signal_delivered"
    assert events[0].payload["signal_id"] == "sig-1"


def test_record_chat_turn_preview_trimmed(recorder, tenant_id) -> None:
    rec, repo = recorder
    msg = "x" * 500
    rec.record_chat_turn(
        tenant_id,
        1.0,
        turn_sequence=1,
        role="user",
        message_preview=msg,
    )
    [event] = repo.list_events(tenant_id)
    assert event.event_type == "chat_turn_user"
    assert len(event.payload["message_preview"]) == 200


def test_record_tool_invocation_payload(recorder, tenant_id) -> None:
    rec, repo = recorder
    rec.record_tool_invocation(
        tenant_id,
        2.0,
        tool_name="deploy_resources",
        outcome="success",
        latency_ms=42,
    )
    [event] = repo.list_events(tenant_id)
    assert event.payload == {
        "tool_name": "deploy_resources",
        "outcome": "success",
        "latency_ms": 42,
    }


def test_state_change_and_warp_change_events(recorder, tenant_id) -> None:
    rec, repo = recorder
    rec.record_state_change(
        tenant_id, 0.0, from_status="Provisioning", to_status="Active", trigger="start"
    )
    rec.record_warp_speed_change(tenant_id, 1.0, old_speed=1.0, new_speed=10.0)
    events = repo.list_events(tenant_id)
    assert [e.event_type for e in events] == ["state_change", "warp_speed_change"]


def test_record_event_graceful_failure_marks_unhealthy(recorder, tenant_id) -> None:
    rec, repo = recorder

    def _boom(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("simulated cosmos outage")

    repo.append_event = _boom  # type: ignore[assignment]
    for _ in range(3):
        result = rec.record_event(tenant_id, "signal_delivered", 0.0, {})
        assert result is None
    assert rec.is_healthy(tenant_id) is False


def test_snapshot_created_every_100_events(recorder, tenant_id) -> None:
    rec, repo = recorder
    for i in range(100):
        rec.record_event(tenant_id, "signal_delivered", float(i), {"i": i})
    snapshots = repo.list_snapshots(tenant_id)
    # A snapshot triggers at seq==100 via count, and at sim_time>=300 via time;
    # only the count trigger has fired here since time max is 99.
    assert len(snapshots) == 1
    assert snapshots[0].event_seq == 100


def test_snapshot_created_on_time_boundary(recorder, tenant_id) -> None:
    rec, repo = recorder
    rec.record_event(tenant_id, "signal_delivered", 0.0, {})
    rec.record_event(tenant_id, "signal_delivered", 350.0, {})
    snapshots = repo.list_snapshots(tenant_id)
    assert len(snapshots) == 1
    assert snapshots[0].sim_time_offset == 350.0
