from __future__ import annotations

import pytest
from app.repositories.coordination_tasks_repository import (
    get_coordination_tasks_repository,
    reset_coordination_tasks_repository,
)
from app.services.audit_service import AuditService
from app.services.governance_registry import GovernanceRegistryService
from app.services.ingestion.authoritative_ingestion import AuthoritativeIngestionService
from app.services.recommendation_service import RecommendationService
from app.services.state_store import PERSONAS, RECOMMENDATIONS, TIMELINE_EVENTS, reset_state
from app.services.task_orchestration_service import TaskOrchestrationService
from app.validators.signal_envelope import SignalEnvelope

from packages.domain.src.domain.models.coordination_task import CoordinationTask
from packages.domain.src.domain.models.data_source import DataSource
from packages.domain.src.domain.models.persona import Persona
from packages.domain.src.domain.models.recommendation import Recommendation


def _seed_recommendation() -> None:
    RECOMMENDATIONS["rec-aud4"] = Recommendation(
        recommendation_id="rec-aud4",
        incident_id="incident-aud4",
        type="public_alert",
        summary="Issue an evacuation warning",
        explanation="Flood depth exceeded threshold",
        supporting_signal_ids=["sig-1"],
        required_approval_level="incident_commander",
    )


def test_recommendation_mutation_fails_closed_when_audit_write_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_state()
    _seed_recommendation()

    def _raise(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("audit down")

    monkeypatch.setattr(AuditService, "record_event", _raise)

    with pytest.raises(RuntimeError, match="audit down"):
        RecommendationService().record_approval(
            recommendation_id="rec-aud4",
            approver_persona_id="persona-incident-commander",
            outcome="approved",
            rationale="meets threshold",
        )

    assert RECOMMENDATIONS["rec-aud4"].status == "proposed"


def test_duplicate_approval_returns_stable_idempotent_decision() -> None:
    reset_state()
    _seed_recommendation()

    first = RecommendationService().record_approval(
        recommendation_id="rec-aud4",
        approver_persona_id="persona-incident-commander",
        outcome="rejected",
        rationale="insufficient certainty",
    )
    second = RecommendationService().record_approval(
        recommendation_id="rec-aud4",
        approver_persona_id="persona-incident-commander",
        outcome="rejected",
        rationale="insufficient certainty",
    )

    assert second.approval_decision_id == first.approval_decision_id


def test_rejected_and_timed_out_map_to_distinct_recommendation_states() -> None:
    reset_state()
    RECOMMENDATIONS["rec-rejected"] = Recommendation(
        recommendation_id="rec-rejected",
        incident_id="incident-aud4",
        type="coordination",
        summary="Coordinate sandbag logistics",
        explanation="Escalating forecast",
        supporting_signal_ids=[],
        required_approval_level="operations_officer",
    )
    RECOMMENDATIONS["rec-timeout"] = Recommendation(
        recommendation_id="rec-timeout",
        incident_id="incident-aud4",
        type="coordination",
        summary="Confirm staging coverage",
        explanation="Awaiting acknowledgement",
        supporting_signal_ids=[],
        required_approval_level="operations_officer",
    )

    RecommendationService().record_approval(
        recommendation_id="rec-rejected",
        approver_persona_id="persona-ops",
        outcome="rejected",
        rationale="Conflicts with current plan",
    )
    RecommendationService().record_approval(
        recommendation_id="rec-timeout",
        approver_persona_id="persona-ops",
        outcome="timed_out",
        rationale="No response within SLA",
    )

    assert RECOMMENDATIONS["rec-rejected"].status == "rejected"
    assert RECOMMENDATIONS["rec-timeout"].status == "expired"


def test_task_status_mutation_fails_closed_when_audit_write_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_state()
    reset_coordination_tasks_repository()

    PERSONAS["persona-ops"] = Persona(
        persona_id="persona-ops",
        display_name="Ops",
        organisation_id="ses-nsw",
        jurisdiction_id="nsw",
        role="operations_officer",
    )

    task = CoordinationTask(
        task_id="task-aud4",
        incident_id="incident-aud4",
        title="Open staging area",
        assigned_persona_id="persona-ops",
        assigned_organisation_id="ses-nsw",
        status="queued",
    )
    TaskOrchestrationService().upsert_task(task)

    def _raise(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("audit down")

    monkeypatch.setattr(AuditService, "record_event", _raise)

    with pytest.raises(RuntimeError, match="audit down"):
        TaskOrchestrationService().update_task_status("task-aud4", "persona-ops", "in_progress")

    task_after = get_coordination_tasks_repository().get("task-aud4", "ses-nsw")
    assert task_after is not None
    assert task_after.status == "queued"


def test_authoritative_ingestion_writes_domain_audit_event() -> None:
    reset_state()

    source = GovernanceRegistryService().register_source(
        DataSource(
            data_source_id="bom-feed",
            name="BoM",
            kind="authoritative",
            trust_tier="tier_1_authoritative_government",
        ),
        actor_id="test-suite",
    )

    envelope = SignalEnvelope.model_validate(
        {
            "source": {"dataSourceId": "bom-feed", "name": "BoM", "kind": "authoritative"},
            "incidentId": "incident-aud4",
            "category": "weather",
            "occurredAt": "2026-09-15T01:00:00Z",
            "receivedAt": "2026-09-15T01:00:15Z",
            "jurisdictionId": "nsw",
            "location": {"type": "Point", "coordinates": [151.2, -33.8], "precisionMeters": 100},
            "payload": {"warning": "storm"},
            "confidenceScore": 0.9,
            "freshnessScore": 0.9,
            "validationStatus": "validated",
            "provenance": {
                "sourceUri": "https://example.gov.au/bom",
                "collectionMethod": "api",
            },
        }
    )

    AuthoritativeIngestionService().ingest(envelope, source=source)

    tenant_events = TIMELINE_EVENTS.bucket_for("live")
    incident_events = tenant_events.get("incident-aud4")
    assert incident_events is not None
    assert any(event.event_type == "ingestion" for event in incident_events)
