from datetime import UTC, datetime, timedelta

from app.services.dashboard_service import DashboardService
from app.services.operational_store import OperationalStore
from app.services.state_store import reset_state

from apps.ingestion.worker import PipelineWorker
from packages.domain.src.domain.models.incident import Incident
from packages.domain.src.domain.models.recommendation import Recommendation
from packages.domain.src.domain.models.signal import Signal


class _Breaker:
    def __init__(self, state: str, last_success_at: datetime | None):
        self.state = state
        self.last_success_at = last_success_at


class _Pipeline:
    def __init__(self, pipeline_id: str, state: str, last_success_at: datetime | None, expected_update_seconds: int):
        self.pipeline_id = pipeline_id
        self.circuit_breaker = _Breaker(state=state, last_success_at=last_success_at)
        self.expected_update_seconds = expected_update_seconds
        self._metrics = type("_M", (), {"to_dict": lambda self: {}})()


def test_aud009_worker_health_fresh_stale_boundary_and_repository_unavailable() -> None:
    worker = PipelineWorker()
    worker._running = True
    now = datetime.now(UTC)
    worker._pipelines = {
        "fresh": _Pipeline("fresh", "closed", now - timedelta(seconds=59), 60),
        "stale": _Pipeline("stale", "closed", now - timedelta(seconds=61), 60),
    }

    healthy, reasons = worker.evaluate_health()
    assert healthy is False
    assert any(reason.startswith("pipeline_stale:stale") for reason in reasons)

    worker.set_repository_status(False, "cosmos_unavailable")
    healthy_with_repo_failure, repo_reasons = worker.evaluate_health()
    assert healthy_with_repo_failure is False
    assert any(reason.startswith("repository_unavailable") for reason in repo_reasons)


def test_aud009_worker_health_partial_recovery() -> None:
    worker = PipelineWorker()
    worker._running = True
    now = datetime.now(UTC)
    stale_pipeline = _Pipeline("pipeline-a", "open", now - timedelta(seconds=120), 60)
    worker._pipelines = {"pipeline-a": stale_pipeline}

    unhealthy, _ = worker.evaluate_health()
    assert unhealthy is False

    stale_pipeline.circuit_breaker.state = "closed"
    stale_pipeline.circuit_breaker.last_success_at = datetime.now(UTC)
    worker.set_repository_status(True)
    healthy, reasons = worker.evaluate_health()
    assert healthy is True
    assert reasons == []


def test_aud009_incident_isolation_for_degraded_sources() -> None:
    reset_state()
    store = OperationalStore.current()
    now = datetime.now(UTC)

    store.incidents.put(
        "incident-a",
        Incident(
            incident_id="incident-a",
            title="Incident A",
            incident_type="flood",
            status="active",
            severity="warning",
            affected_jurisdiction_ids=["nsw"],
        ),
    )
    store.incidents.put(
        "incident-b",
        Incident(
            incident_id="incident-b",
            title="Incident B",
            incident_type="flood",
            status="active",
            severity="warning",
            affected_jurisdiction_ids=["nsw"],
        ),
    )

    store.signals.put(
        "sig-a",
        Signal(
            signal_id="sig-a",
            incident_id="incident-a",
            data_source_id="source-a",
            category="weather",
            occurred_at=now - timedelta(minutes=10),
            received_at=now - timedelta(minutes=10),
            jurisdiction_id="nsw",
            location={"type": "Point", "coordinates": [151.0, -33.0]},
            payload={},
            classification="official",
            retention_until=now + timedelta(days=30),
            confidence_score=0.8,
            freshness_score=0.3,
            validation_status="validated",
            provenance={"expectedUpdateSeconds": 60},
        ),
    )
    store.signals.put(
        "sig-b",
        Signal(
            signal_id="sig-b",
            incident_id="incident-b",
            data_source_id="source-b",
            category="weather",
            occurred_at=now,
            received_at=now,
            jurisdiction_id="nsw",
            location={"type": "Point", "coordinates": [151.1, -33.1]},
            payload={},
            classification="official",
            retention_until=now + timedelta(days=30),
            confidence_score=0.9,
            freshness_score=0.9,
            validation_status="validated",
            provenance={"expectedUpdateSeconds": 600},
        ),
    )

    store.recommendations.put(
        "rec-a",
        Recommendation(
            recommendation_id="rec-a",
            incident_id="incident-a",
            type="public_alert",
            summary="Alert A",
            explanation="A",
            supporting_signal_ids=["sig-a"],
            required_approval_level="incident_commander",
        ),
    )
    store.recommendations.put(
        "rec-b",
        Recommendation(
            recommendation_id="rec-b",
            incident_id="incident-b",
            type="public_alert",
            summary="Alert B",
            explanation="B",
            supporting_signal_ids=["sig-b"],
            required_approval_level="incident_commander",
        ),
    )

    dashboard_a = DashboardService().get_dashboard("incident-a", actor_roles=(), actor_persona_id=None)
    dashboard_b = DashboardService().get_dashboard("incident-b", actor_roles=(), actor_persona_id=None)

    assert len(dashboard_a["signalSummary"]["degradedSources"]) == 1
    assert len(dashboard_b["signalSummary"]["degradedSources"]) == 0
    assert dashboard_b["activeRecommendations"][0]["status"] == "proposed"
