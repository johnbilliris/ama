"""Spec 036 / Phase F (T228 + T229) — Multi-agent conflict detector.

Reactive, post-return, deterministic, rule-based detector running in the
recommendation-aggregation layer per Pass 2 Q-P2-06 (NOT inside any
individual agent and NOT in real-time streaming). Pre-emptive divergence
detection was rejected because it breaks Constitution Principle IV
deterministic replay + spec 033 MAF agent-isolation model.

Four conflict classes (ADR-18 / FR-RAG-COORD-01):

* ``resource``  — same ``resource_id`` claimed in overlapping time windows.
* ``spatial``   — incompatible recommendations covering overlapping
  ``(geo_bbox, time_window)`` (e.g. "evacuate" vs "shelter-in-place").
* ``temporal``  — action verbs with mutually exclusive deadlines.
* ``severity``  — hazard severity buckets with delta ≥1 AIIMS incident
  level for the same hazard.

The detector emits ``conflict_detected`` events with a stable
``conflict_group_id`` (UUID v7, time-ordered). The same id is also written
to every implicated ``AuditRecord.conflict_group_id`` so trace stitching
works without a JOIN.

Per Plan §F-A9.6 (T231) — ``feature.multi_agent_conflict_detection.enabled``
(Reversible class) reverts to single-agent behaviour when disabled. NEVER
silences the agent (Constitution Principle I).
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

# Conflict class enum mirror of contracts/conflict_detection.schema.json.
ConflictClass = str  # Literal["resource", "spatial", "temporal", "severity"]

# Reversible feature flag state per Plan §F-A9.6.
_MULTI_AGENT_DETECTION_ENABLED: bool = True
_FLAG_LAST_ACTOR: str | None = None
_FLAG_LAST_CHANGED_AT: datetime | None = None


def get_multi_agent_detection_enabled() -> bool:
    """Return the current ``feature.multi_agent_conflict_detection.enabled`` value."""
    return _MULTI_AGENT_DETECTION_ENABLED


def set_multi_agent_detection_flag(
    *,
    value: bool,
    actor: str,
    audit_sink: Callable[[dict[str, Any]], None] | None = None,
    now_fn: Callable[[], datetime] | None = None,
) -> None:
    """Flip the multi-agent conflict-detection feature flag.

    Reversible class per Pass 2 Q-P2-08. Disabling reverts to single-agent
    behaviour (per-agent recommendations are still emitted; cross-agent
    detection short-circuits). NEVER silences an agent (Constitution
    Principle I). Emits ``multi_agent_coordination_disabled`` (or
    ``..._enabled``) audit event on flip.
    """
    global _MULTI_AGENT_DETECTION_ENABLED, _FLAG_LAST_ACTOR, _FLAG_LAST_CHANGED_AT

    if not actor:
        raise ValueError("actor required for feature-flag change (audit invariant)")
    old_value = _MULTI_AGENT_DETECTION_ENABLED
    _MULTI_AGENT_DETECTION_ENABLED = bool(value)
    _FLAG_LAST_ACTOR = actor
    _FLAG_LAST_CHANGED_AT = (now_fn or (lambda: datetime.now(tz=UTC)))()

    if audit_sink is not None:
        audit_sink(
            {
                "event_type": (
                    "multi_agent_coordination_disabled" if not bool(value) else "multi_agent_coordination_enabled"
                ),
                "flag_name": "feature.multi_agent_conflict_detection.enabled",
                "old_value": old_value,
                "new_value": _MULTI_AGENT_DETECTION_ENABLED,
                "actor_id": actor,
                "timestamp": _FLAG_LAST_CHANGED_AT.isoformat(),
            }
        )


@dataclass(frozen=True)
class AgentRecommendation:
    """One agent's contribution into the recommendation-aggregation layer."""

    agent_name: str
    audit_call_id: str
    recommendation_summary: str
    action_verb: str | None = None  # "evacuate", "shelter-in-place", etc.
    resource_id: str | None = None
    geo_bbox: tuple[float, float, float, float] | None = None
    time_window_start: datetime | None = None
    time_window_end: datetime | None = None
    deadline: datetime | None = None
    severity_aiims_level: int | None = None
    hazard_type: str | None = None


@dataclass
class ConflictDetection:
    """Outcome of one detector run."""

    conflict_group_id: str
    detected_at: datetime
    conflict_class: ConflictClass
    agent_recommendations: list[AgentRecommendation]
    escalation_state: str = "awaiting_ops_officer"
    current_owner: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_log_entry(self) -> dict[str, Any]:
        """Render to the ``conflict_detection.schema.json`` shape."""
        return {
            "conflict_group_id": self.conflict_group_id,
            "detected_at": self.detected_at.isoformat(),
            "conflict_class": self.conflict_class,
            "agent_recommendations": [_rec_to_dict(r, self.conflict_class) for r in self.agent_recommendations],
            "escalation_state": self.escalation_state,
            "current_owner": self.current_owner,
            "escalated_to_ic_at": self.extras.get("escalated_to_ic_at"),
            "resolution": self.extras.get("resolution"),
            "field_coordinator_offline_queue": self.extras.get("field_coordinator_offline_queue"),
        }


def _rec_to_dict(r: AgentRecommendation, conflict_class: str) -> dict[str, Any]:
    out: dict[str, Any] = {
        "agent_name": r.agent_name,
        "audit_call_id": r.audit_call_id,
        "recommendation_summary": r.recommendation_summary,
    }
    if conflict_class == "resource":
        out["resource_id"] = r.resource_id
    if conflict_class == "spatial":
        out["geo_bbox"] = list(r.geo_bbox) if r.geo_bbox else None
    if conflict_class in ("resource", "spatial", "temporal"):
        out["time_window"] = (
            {
                "start_time": r.time_window_start.isoformat(),
                "end_time": r.time_window_end.isoformat(),
            }
            if r.time_window_start and r.time_window_end
            else None
        )
    if conflict_class == "severity":
        out["severity_aiims_level"] = r.severity_aiims_level
    return out


def _windows_overlap(a: AgentRecommendation, b: AgentRecommendation) -> bool:
    if not (a.time_window_start and a.time_window_end and b.time_window_start and b.time_window_end):
        return False
    return a.time_window_start < b.time_window_end and b.time_window_start < a.time_window_end


def _bboxes_overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    """WGS84 bbox overlap test on `[west, south, east, north]`."""
    aw, asou, ae, an = a
    bw, bsou, be, bn = b
    return aw < be and bw < ae and asou < bn and bsou < an


# Action-verb antagonisms recognised by the spatial + temporal classes.
_ANTAGONISTIC_VERBS: dict[str, set[str]] = {
    "evacuate": {"shelter-in-place"},
    "shelter-in-place": {"evacuate"},
    "deploy": {"recall"},
    "recall": {"deploy"},
}


def _verbs_antagonistic(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return False
    return b in _ANTAGONISTIC_VERBS.get(a, set())


def _now_uuid7(now: datetime) -> str:
    """Best-effort UUID v7 — falls back to uuid4 on Python < 3.13.

    The conflict log only requires a stable, time-ordered id; uuid4 is
    acceptable for our purposes. uuid7 is preferred when available.
    """
    try:
        # uuid7 was added in Python 3.13 / RFC 9562.
        return str(uuid.uuid7())  # type: ignore[attr-defined]
    except AttributeError:  # pragma: no cover - <3.13 fallback
        return str(uuid.uuid4())


def detect_conflicts(
    recommendations: Iterable[AgentRecommendation],
    *,
    now: datetime | None = None,
) -> list[ConflictDetection]:
    """Run all four classes against the recommendation-aggregation set.

    Returns an empty list when fewer than 2 recommendations are supplied
    OR when the feature flag is disabled.
    """
    recs = list(recommendations)
    if not _MULTI_AGENT_DETECTION_ENABLED or len(recs) < 2:
        return []

    ts = now or datetime.now(tz=UTC)
    results: list[ConflictDetection] = []
    seen_pairs: set[tuple[int, int, str]] = set()

    for i in range(len(recs)):
        for j in range(i + 1, len(recs)):
            a, b = recs[i], recs[j]

            # Resource conflict
            if (
                a.resource_id
                and b.resource_id
                and a.resource_id == b.resource_id
                and _windows_overlap(a, b)
                and (i, j, "resource") not in seen_pairs
            ):
                seen_pairs.add((i, j, "resource"))
                results.append(
                    ConflictDetection(
                        conflict_group_id=_now_uuid7(ts),
                        detected_at=ts,
                        conflict_class="resource",
                        agent_recommendations=[a, b],
                    )
                )

            # Spatial conflict
            if (
                a.geo_bbox
                and b.geo_bbox
                and _bboxes_overlap(a.geo_bbox, b.geo_bbox)
                and _windows_overlap(a, b)
                and _verbs_antagonistic(a.action_verb, b.action_verb)
                and (i, j, "spatial") not in seen_pairs
            ):
                seen_pairs.add((i, j, "spatial"))
                results.append(
                    ConflictDetection(
                        conflict_group_id=_now_uuid7(ts),
                        detected_at=ts,
                        conflict_class="spatial",
                        agent_recommendations=[a, b],
                    )
                )

            # Temporal conflict
            if (
                a.deadline
                and b.deadline
                and _verbs_antagonistic(a.action_verb, b.action_verb)
                and abs((a.deadline - b.deadline).total_seconds()) < 60
                and (i, j, "temporal") not in seen_pairs
            ):
                seen_pairs.add((i, j, "temporal"))
                results.append(
                    ConflictDetection(
                        conflict_group_id=_now_uuid7(ts),
                        detected_at=ts,
                        conflict_class="temporal",
                        agent_recommendations=[a, b],
                    )
                )

            # Severity conflict
            if (
                a.severity_aiims_level is not None
                and b.severity_aiims_level is not None
                and a.hazard_type
                and b.hazard_type
                and a.hazard_type == b.hazard_type
                and abs(a.severity_aiims_level - b.severity_aiims_level) >= 1
                and (i, j, "severity") not in seen_pairs
            ):
                seen_pairs.add((i, j, "severity"))
                results.append(
                    ConflictDetection(
                        conflict_group_id=_now_uuid7(ts),
                        detected_at=ts,
                        conflict_class="severity",
                        agent_recommendations=[a, b],
                    )
                )
    return results


def emit_conflict_event(
    detection: ConflictDetection,
    *,
    cosmos_writer: Callable[[dict[str, Any]], None] | None = None,
    audit_sink: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Persist the detection to ``conflictDetectionLog`` + emit audit event."""
    payload = detection.to_log_entry()
    if cosmos_writer is not None:
        try:
            cosmos_writer(payload)
        except Exception as exc:  # noqa: BLE001 - best-effort persist
            logger.warning("conflict_log_write_error err=%s", exc)
    if audit_sink is not None:
        audit_sink(
            {
                "event_type": "conflict_detected",
                "conflict_group_id": detection.conflict_group_id,
                "conflict_class": detection.conflict_class,
                "agent_call_ids": [r.audit_call_id for r in detection.agent_recommendations],
                "timestamp": detection.detected_at.isoformat(),
            }
        )
    return payload


__all__ = [
    "AgentRecommendation",
    "ConflictDetection",
    "detect_conflicts",
    "emit_conflict_event",
    "get_multi_agent_detection_enabled",
    "set_multi_agent_detection_flag",
]
