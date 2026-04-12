import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.repositories.signal_repository import SignalRepository
from app.repositories.simulation_repository import SimulationRepository

from packages.domain.src.domain.models.exercise_report import (
    AlertSummary,
    ExerciseReport,
    PerformanceMetrics,
    RecommendationSummary,
    SignalSummary,
)

logger = logging.getLogger(__name__)


class ExerciseReportService:
    def __init__(
        self,
        simulation_repository: SimulationRepository,
        signal_repository: SignalRepository,
        blob_service_client: Any = None,
    ):
        self._sim_repo = simulation_repository
        self._signal_repo = signal_repository
        self._blob = blob_service_client

    async def generate_report(self, tenant_id: str) -> ExerciseReport:
        tenant = await self._sim_repo.get_by_tenant_id(tenant_id)
        if tenant is None:
            raise ValueError(f"Simulation tenant '{tenant_id}' not found")

        signals, signal_count = await self._signal_repo.list_by_tenant(tenant_id, limit=10_000)

        by_category: dict[str, int] = {}
        by_source: dict[str, int] = {}
        for sig in signals:
            cat = sig.get("category", "unknown")
            by_category[cat] = by_category.get(cat, 0) + 1
            src = sig.get("source_context", "unknown")
            by_source[src] = by_source.get(src, 0) + 1

        report_id = f"rpt-{uuid4().hex[:12]}"

        report = ExerciseReport(
            report_id=report_id,
            tenant_id=tenant_id,
            scenario_run_id=tenant.scenario_run_id,
            scenario_type=tenant.scenario_type,
            generated_at=datetime.now(UTC),
            participating_organisations=[],
            participating_personas=tenant.participants,
            signal_summary=SignalSummary(
                total=signal_count,
                by_category=by_category,
                by_source=by_source,
            ),
            recommendation_summary=RecommendationSummary(
                total=tenant.resource_consumption.recommendation_count,
            ),
            alert_summary=AlertSummary(),
            performance_metrics=PerformanceMetrics(),
            coordination_gaps=[],
            benchmark_comparison=[],
        )

        await self._persist_report(tenant_id, report)

        tenant_update = tenant.model_copy(
            update={"exercise_report_uri": f"simulation/{tenant_id}/reports/{report_id}.json"}
        )
        await self._sim_repo.update(tenant_update)

        logger.info("exercise_report_generated tenant_id=%s report_id=%s", tenant_id, report_id)
        return report

    async def get_report(self, tenant_id: str) -> ExerciseReport | None:
        tenant = await self._sim_repo.get_by_tenant_id(tenant_id)
        if tenant is None or not tenant.exercise_report_uri:
            return None

        if self._blob:
            try:
                container = self._blob.get_container_client("simulation")
                blob = container.get_blob_client(tenant.exercise_report_uri.replace("simulation/", "", 1))
                data = blob.download_blob().readall()
                return ExerciseReport.model_validate_json(data)
            except Exception:
                logger.warning("report_load_failed tenant_id=%s", tenant_id, exc_info=True)

        return None

    async def _persist_report(self, tenant_id: str, report: ExerciseReport) -> None:
        blob_path = f"{tenant_id}/reports/{report.report_id}.json"
        if self._blob:
            try:
                container = self._blob.get_container_client("simulation")
                container.upload_blob(
                    blob_path,
                    json.dumps(report.model_dump(mode="json"), default=str),
                    overwrite=True,
                )
            except Exception:
                logger.warning("report_persist_failed tenant_id=%s", tenant_id, exc_info=True)
