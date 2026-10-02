from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.repositories.signal_repository import SignalRepository
from app.repositories.simulation_event_repository import SimulationEventRepository
from app.repositories.simulation_repository import SimulationRepository
from app.services.exercise_report_service import ExerciseReportService
from app.services.operational_store import OperationalStore
from app.services.state_store import reset_state

from packages.domain.src.domain.models.coordination_task import CoordinationTask
from packages.domain.src.domain.models.exercise_report import ExerciseReport, PerformanceMetrics
from packages.domain.src.domain.models.recommendation import Recommendation
from packages.domain.src.domain.models.simulation_event import SimulationEvent
from packages.domain.src.domain.models.simulation_tenant import SimulationParticipant, SimulationTenant

pytestmark = pytest.mark.spec007_isolation


@pytest.fixture(autouse=True)
def _reset_operational_state() -> None:
    reset_state()
    yield
    reset_state()


class _Blob:
    def __init__(self, container) -> None:  # noqa: ANN001
        self._container = container

    def get_container_client(self, name):  # noqa: ANN001, ANN201, ARG002
        return self._container


class _Container:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.rows: dict[str, bytes] = {}

    def upload_blob(self, name, data, overwrite):  # noqa: ANN001, ANN201
        assert overwrite is False
        if self.fail:
            raise ConnectionError("blob unavailable")
        self.rows[name] = data.encode("utf-8") if isinstance(data, str) else data

    def get_blob_client(self, name):  # noqa: ANN001, ANN201
        container = self

        class _Client:
            def download_blob(self):  # noqa: ANN201
                class _Download:
                    def readall(self):  # noqa: ANN201
                        return container.rows[name]

                return _Download()

        return _Client()


async def _tenant(
    repo: SimulationRepository,
    *,
    run_id: str = "12345678-1234-1234-1234-123456789012",
) -> SimulationTenant:
    tenant = SimulationTenant(
        tenant_id=f"sim-{run_id}",
        scenario_id=run_id,
        scenario_run_id=run_id,
        scenario_type="Flood",
        created_by="controller-1",
        participants=["controller-1"],
        participant_assignments=[
            SimulationParticipant(
                oid="controller-1",
                persona_id="persona-controller",
                organisation_id="ses-nsw",
                jurisdiction_id="nsw",
                role="coordinator",
            )
        ],
        status="Active",
    )
    return await repo.create(tenant)


@pytest.mark.asyncio
async def test_report_is_stable_truthful_and_retrievable_by_id() -> None:
    repo = SimulationRepository()
    tenant = await _tenant(repo)
    signals = SignalRepository()
    await signals.create_signal(
        tenant.tenant_id,
        {"signal_id": "sig-1", "category": "hydrology", "dataSourceId": "bom-gauge"},
    )
    store = OperationalStore(tenant.tenant_id)
    store.recommendations.put(
        "rec-1",
        Recommendation(
            recommendation_id="rec-1",
            incident_id="incident-1",
            type="coordination",
            summary="Coordinate response",
            explanation="Exercise",
            required_approval_level="incident_commander",
            status="approved",
        ),
    )
    store.tasks.put(
        "task-1",
        CoordinationTask(
            task_id="task-1",
            incident_id="incident-1",
            title="Blocked task",
            assigned_persona_id="persona-controller",
            assigned_organisation_id="ses-nsw",
            status="blocked",
            blocker_reason="awaiting resource",
        ),
    )
    events = SimulationEventRepository()
    events.append_event(
        SimulationEvent(
            tenant_id=tenant.tenant_id,
            event_seq=1,
            event_type="state_change",
            sim_time_offset=0,
            wall_clock_time=datetime.now(UTC),
        )
    )
    container = _Container()
    service = ExerciseReportService(repo, signals, events, _Blob(container))

    first = await service.generate_report(tenant.tenant_id)
    second = await service.get_report_by_id(first.report_id)

    assert second is not None
    assert second.report_id == first.report_id
    assert first.signal_summary.by_source == {"bom-gauge": 1}
    assert first.recommendation_summary.approved == 1
    assert first.participating_personas == ["persona-controller"]
    assert first.participating_organisations == ["ses-nsw"]
    assert first.coordination_gaps == ["task-1: awaiting resource"]
    assert len(first.exercise_timeline) == 1


@pytest.mark.asyncio
async def test_report_storage_failure_does_not_publish_uri() -> None:
    repo = SimulationRepository()
    tenant = await _tenant(repo)
    service = ExerciseReportService(repo, SignalRepository(), SimulationEventRepository(), _Blob(_Container(fail=True)))

    with pytest.raises(RuntimeError, match="persistence failed"):
        await service.generate_report(tenant.tenant_id)

    persisted = await repo.get_by_tenant_id(tenant.tenant_id)
    assert persisted is not None
    assert persisted.exercise_report_uri is None
    assert persisted.exercise_report_id is None


@pytest.mark.asyncio
async def test_recommendation_outcomes_are_counted_exactly_once() -> None:
    repo = SimulationRepository()
    tenant = await _tenant(repo)
    store = OperationalStore(tenant.tenant_id)
    for status in ("approved", "rejected", "escalated", "expired", "under_review"):
        store.recommendations.put(
            f"rec-{status}",
            Recommendation(
                recommendation_id=f"rec-{status}",
                incident_id="incident-1",
                type="coordination",
                summary=status,
                explanation="Exercise",
                required_approval_level="incident_commander",
                status=status,
            ),
        )
    service = ExerciseReportService(repo, SignalRepository(), SimulationEventRepository())

    report = await service.generate_report(tenant.tenant_id)
    summary = report.recommendation_summary

    assert summary.model_dump() == {
        "total": 5,
        "approved": 1,
        "rejected": 1,
        "escalated": 1,
        "timed_out": 1,
        "pending": 1,
    }


@pytest.mark.asyncio
async def test_report_compares_metrics_with_prior_archived_same_scenario() -> None:
    repo = SimulationRepository()
    prior = await _tenant(repo, run_id="11111111-1111-1111-1111-111111111111")
    current = await _tenant(repo, run_id="22222222-2222-2222-2222-222222222222")
    prior_report = ExerciseReport(
        report_id="rpt-prior",
        tenant_id=prior.tenant_id,
        scenario_run_id=prior.scenario_run_id,
        scenario_type="Flood",
        performance_metrics=PerformanceMetrics(
            time_to_first_recommendation_s=120,
            time_to_alert_publication_s=240,
            coordination_coverage_pct=80,
        ),
    )
    prior_archived = (
        prior.transition_to("Archiving")
        .transition_to("Archived")
        .model_copy(
            update={
                "exercise_report_id": prior_report.report_id,
                "exercise_report_uri": f"simulation/{prior.tenant_id}/reports/{prior_report.report_id}.json",
                "archive_job_state": "completed",
            }
        )
    )
    await repo.update(prior_archived)
    await repo.upsert_document(
        {
            "id": f"{current.tenant_id}:template",
            "tenant_id": current.tenant_id,
            "scenario_id": current.scenario_id,
            "document_type": "simulation_seed_template",
            "benchmark_targets": {
                "time_to_first_recommendation_s": 300,
                "time_to_alert_s": 600,
                "coordination_coverage_pct": 75,
            },
        }
    )
    service = ExerciseReportService(repo, SignalRepository(), SimulationEventRepository())
    service._memory[prior.tenant_id] = prior_report

    report = await service.generate_report(current.tenant_id)

    comparisons = {row.metric: row for row in report.benchmark_comparison}
    assert comparisons["time_to_first_recommendation_s"].prior_actual == 120
    assert comparisons["time_to_alert_s"].prior_actual == 240
    assert comparisons["coordination_coverage_pct"].prior_actual == 80
    assert all(row.delta_from_prior is None for row in comparisons.values())
