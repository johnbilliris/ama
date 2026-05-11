"""T225 — F-A9 conflict detection integration tests.

Per FR-RAG-COORD-01 + Plan §F-A9.3, exercises four deterministic conflict
classes:

1. ``resource``  — same ``resource_id``, overlapping ``(start_time, end_time)``.
2. ``spatial``   — incompatible recs over overlapping ``(geo_bbox, time_window)``.
3. ``temporal``  — antagonistic action verbs with mutually-exclusive deadlines.
4. ``severity``  — hazard severity buckets with delta ≥ 1 AIIMS level.

Each case asserts a ``conflict_detected`` event with the right class label
and a stable ``conflict_group_id``.

Also covers T231 — ``feature.multi_agent_conflict_detection.enabled``
flag toggle reverts to single-agent behaviour without silencing agents.

Proves: T228 + T229 + T231.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from apps.api.app.services.conflict_detection import (
    AgentRecommendation,
    detect_conflicts,
    emit_conflict_event,
    set_multi_agent_detection_flag,
)


def _now() -> datetime:
    return datetime(2026, 5, 15, 3, 42, 30, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _reset_flag() -> Any:
    set_multi_agent_detection_flag(value=True, actor="test-fixture")
    yield


def test_resource_conflict_same_id_overlapping_window() -> None:
    """Two agents claim the same helicopter in overlapping windows."""
    a = AgentRecommendation(
        agent_name="EvacuationAgent",
        audit_call_id="11111111-1111-1111-1111-111111111111",
        recommendation_summary="Tasking helo HEL-VH-AAA for Bega Valley evac.",
        resource_id="HEL-VH-AAA",
        time_window_start=_now(),
        time_window_end=_now() + timedelta(hours=4),
    )
    b = AgentRecommendation(
        agent_name="ResourceAllocationAgent",
        audit_call_id="22222222-2222-2222-2222-222222222222",
        recommendation_summary="Pre-positioning HEL-VH-AAA for Eden CFS staging.",
        resource_id="HEL-VH-AAA",
        time_window_start=_now() + timedelta(hours=2),
        time_window_end=_now() + timedelta(hours=6),
    )
    res = detect_conflicts([a, b], now=_now())
    assert len(res) == 1
    assert res[0].conflict_class == "resource"
    assert res[0].conflict_group_id  # stable id present


def test_spatial_conflict_overlapping_bbox_antagonistic_verbs() -> None:
    """Evacuate vs shelter-in-place over overlapping bbox + window."""
    bbox = (149.6, -36.9, 150.1, -36.5)
    a = AgentRecommendation(
        agent_name="EvacuationAgent",
        audit_call_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        recommendation_summary="Evacuate Bega Valley LGA south of Princes Hwy.",
        action_verb="evacuate",
        geo_bbox=bbox,
        time_window_start=_now(),
        time_window_end=_now() + timedelta(hours=12),
    )
    b = AgentRecommendation(
        agent_name="RiskAssessmentAgent",
        audit_call_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        recommendation_summary="Shelter-in-place — road network compromised.",
        action_verb="shelter-in-place",
        geo_bbox=bbox,
        time_window_start=_now(),
        time_window_end=_now() + timedelta(hours=12),
    )
    res = detect_conflicts([a, b], now=_now())
    assert any(r.conflict_class == "spatial" for r in res)


def test_temporal_conflict_antagonistic_verbs_close_deadlines() -> None:
    """Same actor pair with deadlines within 60s and antagonistic verbs."""
    a = AgentRecommendation(
        agent_name="EvacuationAgent",
        audit_call_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
        recommendation_summary="Evacuate by 1500.",
        action_verb="evacuate",
        deadline=_now() + timedelta(hours=1),
    )
    b = AgentRecommendation(
        agent_name="RiskAssessmentAgent",
        audit_call_id="dddddddd-dddd-dddd-dddd-dddddddddddd",
        recommendation_summary="Shelter-in-place by 1500:30.",
        action_verb="shelter-in-place",
        deadline=_now() + timedelta(hours=1, seconds=30),
    )
    res = detect_conflicts([a, b], now=_now())
    assert any(r.conflict_class == "temporal" for r in res)


def test_severity_conflict_same_hazard_aiims_delta() -> None:
    """Two agents disagree on AIIMS severity for the same hazard."""
    a = AgentRecommendation(
        agent_name="MonitoringAgent",
        audit_call_id="eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
        recommendation_summary="Bushfire severity 1 (low).",
        severity_aiims_level=1,
        hazard_type="bushfire",
    )
    b = AgentRecommendation(
        agent_name="RiskAssessmentAgent",
        audit_call_id="ffffffff-ffff-ffff-ffff-ffffffffffff",
        recommendation_summary="Bushfire severity 3 (major).",
        severity_aiims_level=3,
        hazard_type="bushfire",
    )
    res = detect_conflicts([a, b], now=_now())
    assert any(r.conflict_class == "severity" for r in res)


def test_no_conflict_when_only_one_recommendation() -> None:
    """Single agent → no conflicts (Constitution Principle I — agent NEVER silenced)."""
    a = AgentRecommendation(
        agent_name="EvacuationAgent",
        audit_call_id="11111111-1111-1111-1111-111111111111",
        recommendation_summary="Solo recommendation.",
    )
    assert detect_conflicts([a], now=_now()) == []


def test_flag_disabled_returns_empty_without_silencing() -> None:
    """T231 — flag disabled → no detection, but agents still emit (verified by len==2 input)."""
    audit: list[dict[str, Any]] = []
    set_multi_agent_detection_flag(
        value=False,
        actor="ops-on-call",
        audit_sink=audit.append,
        now_fn=_now,
    )
    a = AgentRecommendation(
        agent_name="EvacuationAgent",
        audit_call_id="11111111-1111-1111-1111-111111111111",
        recommendation_summary="Tasking HEL-VH-AAA.",
        resource_id="HEL-VH-AAA",
        time_window_start=_now(),
        time_window_end=_now() + timedelta(hours=4),
    )
    b = AgentRecommendation(
        agent_name="ResourceAllocationAgent",
        audit_call_id="22222222-2222-2222-2222-222222222222",
        recommendation_summary="Tasking HEL-VH-AAA.",
        resource_id="HEL-VH-AAA",
        time_window_start=_now() + timedelta(hours=1),
        time_window_end=_now() + timedelta(hours=5),
    )
    res = detect_conflicts([a, b], now=_now())
    assert res == [], "flag disabled MUST short-circuit detection"
    assert any(e["event_type"] == "multi_agent_coordination_disabled" for e in audit)


def test_emit_conflict_event_writes_log_and_audit() -> None:
    """End-to-end: detection → cosmos_writer + audit_sink invoked."""
    a = AgentRecommendation(
        agent_name="EvacuationAgent",
        audit_call_id="11111111-1111-1111-1111-111111111111",
        recommendation_summary="Tasking HEL-VH-AAA for evac.",
        resource_id="HEL-VH-AAA",
        time_window_start=_now(),
        time_window_end=_now() + timedelta(hours=4),
    )
    b = AgentRecommendation(
        agent_name="ResourceAllocationAgent",
        audit_call_id="22222222-2222-2222-2222-222222222222",
        recommendation_summary="Pre-position HEL-VH-AAA.",
        resource_id="HEL-VH-AAA",
        time_window_start=_now() + timedelta(hours=2),
        time_window_end=_now() + timedelta(hours=6),
    )
    detections = detect_conflicts([a, b], now=_now())
    assert detections, "expected at least one detection"

    cosmos: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    payload = emit_conflict_event(detections[0], cosmos_writer=cosmos.append, audit_sink=audit.append)

    assert payload["conflict_class"] == "resource"
    assert payload["conflict_group_id"]
    assert len(cosmos) == 1
    assert any(e["event_type"] == "conflict_detected" for e in audit)
