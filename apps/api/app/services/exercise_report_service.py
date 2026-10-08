import hashlib
import json
import logging
import os
from datetime import UTC, datetime
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from app.core.async_io import run_blocking
from app.repositories.signal_repository import SignalRepository
from app.repositories.simulation_repository import SimulationRepository
from app.services.operational_store import OperationalStore

from packages.domain.src.domain.models.exercise_report import (
    AlertSummary,
    BenchmarkComparison,
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
        event_repository: Any = None,
        blob_service_client: Any = None,
        audit_writer: Any = None,
    ):
        self._sim_repo = simulation_repository
        self._signal_repo = signal_repository
        self._event_repo = event_repository
        self._blob = blob_service_client
        self._audit_writer = audit_writer
        self._memory: dict[str, ExerciseReport] = {}
        self._archive_memory: dict[str, dict[str, Any]] = {}
        environment = (os.environ.get("AMA_ENVIRONMENT") or os.environ.get("ENVIRONMENT") or "dev").lower()
        if self._blob is None and environment in {"production", "staging"}:
            raise RuntimeError("ExerciseReportService requires Blob storage in production/staging")

    async def generate_report(self, tenant_id: str) -> ExerciseReport:
        tenant = await self._sim_repo.get_by_tenant_id(tenant_id)
        if tenant is None:
            raise ValueError(f"Simulation tenant '{tenant_id}' not found")

        existing = await self.get_report(tenant_id)
        if existing is not None:
            return existing

        signals: list[dict[str, Any]] = []
        offset = 0
        page_size = 1000
        max_signals = tenant.resource_limits.max_signals
        while offset < max_signals:
            page, total = await self._signal_repo.list_by_tenant(
                tenant_id,
                limit=min(page_size, max_signals - offset),
                offset=offset,
            )
            signals.extend(page)
            offset += len(page)
            if not page or offset >= total:
                break
        signal_count = len(signals)

        by_category: dict[str, int] = {}
        by_source: dict[str, int] = {}
        for sig in signals:
            cat = sig.get("category", "unknown")
            by_category[cat] = by_category.get(cat, 0) + 1
            src = sig.get("dataSourceId") or sig.get("data_source_id") or "unknown"
            by_source[src] = by_source.get(src, 0) + 1

        store = OperationalStore(tenant_id)
        recommendations = store.recommendations.values()
        alerts = store.alerts.values()
        tasks = store.tasks.values()
        timeline = (
            await run_blocking(self._event_repo.list_events, tenant_id, limit=10_000)
            if self._event_repo is not None
            else []
        )
        report_id = f"rpt-{uuid5(NAMESPACE_URL, f'{tenant_id}:{tenant.scenario_run_id}:report').hex[:16]}"
        recommendation_statuses = {
            status: 0 for status in ("approved", "rejected", "escalated", "timed_out", "pending")
        }
        for recommendation in recommendations:
            if recommendation.status == "approved":
                recommendation_statuses["approved"] += 1
            elif recommendation.status == "rejected":
                recommendation_statuses["rejected"] += 1
            elif recommendation.status == "escalated":
                recommendation_statuses["escalated"] += 1
            elif recommendation.status in {"expired"}:
                recommendation_statuses["timed_out"] += 1
            else:
                recommendation_statuses["pending"] += 1

        completed_tasks = sum(1 for task in tasks if task.status == "completed")
        coordination_coverage = (completed_tasks / len(tasks) * 100.0) if tasks else None
        first_recommendation = _first_timeline_timestamp(timeline, {"recommendation"})
        first_publication = _first_timeline_timestamp(timeline, {"publication"})
        seed_context = await self._sim_repo.get_document(
            document_type="simulation_seed_template",
            document_id=f"{tenant_id}:template",
        )
        targets = seed_context.get("benchmark_targets", {}) if seed_context else {}
        metrics = PerformanceMetrics(
            time_to_first_recommendation_s=_seconds_since(tenant.created_at, first_recommendation),
            time_to_alert_publication_s=_seconds_since(tenant.created_at, first_publication),
            coordination_coverage_pct=coordination_coverage,
        )
        prior_report = await self._find_prior_report(tenant_id, tenant.scenario_type)

        report = ExerciseReport(
            report_id=report_id,
            tenant_id=tenant_id,
            scenario_run_id=tenant.scenario_run_id,
            scenario_type=tenant.scenario_type,
            generated_at=datetime.now(UTC),
            participating_organisations=sorted(
                {
                    assignment.organisation_id
                    for assignment in tenant.participant_assignments
                    if assignment.organisation_id
                }
            ),
            participating_personas=sorted(
                {assignment.persona_id or assignment.oid for assignment in tenant.participant_assignments}
            ),
            exercise_timeline=[event.model_dump(mode="json") for event in timeline],
            signal_summary=SignalSummary(
                total=signal_count,
                by_category=by_category,
                by_source=by_source,
            ),
            recommendation_summary=RecommendationSummary(
                total=len(recommendations),
                approved=recommendation_statuses["approved"],
                rejected=recommendation_statuses["rejected"],
                escalated=recommendation_statuses["escalated"],
                timed_out=recommendation_statuses["timed_out"],
                pending=recommendation_statuses["pending"],
            ),
            alert_summary=AlertSummary(
                total=len(alerts),
                published=sum(1 for alert in alerts if alert.status == "published"),
                blocked_simulation=sum(
                    1 for alert in alerts if "simulationDeliveryCorrelationId" in alert.content_blocks
                ),
            ),
            performance_metrics=metrics,
            coordination_gaps=[
                f"{task.task_id}: {task.blocker_reason or 'blocked'}" for task in tasks if task.status == "blocked"
            ],
            benchmark_comparison=_benchmark_comparison(
                targets,
                metrics,
                prior_report.performance_metrics if prior_report is not None else None,
            ),
        )

        await self._persist_report(tenant_id, report)

        tenant_update = tenant.model_copy(
            update={
                "exercise_report_id": report_id,
                "exercise_report_uri": f"simulation/{tenant_id}/reports/{report_id}.json",
            }
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
                data = await run_blocking(lambda: blob.download_blob().readall())
                return ExerciseReport.model_validate_json(data)
            except Exception as exc:
                if exc.__class__.__name__ in {"ResourceNotFoundError", "BlobNotFoundError"}:
                    return None
                raise RuntimeError(f"Exercise report storage unavailable for {tenant_id}") from exc

        return self._memory.get(tenant_id)

    async def get_report_by_id(self, report_id: str) -> ExerciseReport | None:
        tenant = await self._sim_repo.get_by_report_id(report_id)
        if tenant is None:
            return None
        return await self.get_report(tenant.tenant_id)

    async def _find_prior_report(self, tenant_id: str, scenario_type: str) -> ExerciseReport | None:
        archived, _ = await self._sim_repo.list_by_status(status="Archived", limit=1000)
        candidates = [
            tenant
            for tenant in archived
            if tenant.tenant_id != tenant_id and tenant.scenario_type == scenario_type and tenant.exercise_report_uri
        ]
        candidates.sort(key=lambda candidate: candidate.archived_at or candidate.created_at, reverse=True)
        for candidate in candidates:
            report = await self.get_report(candidate.tenant_id)
            if report is not None:
                return report
        return None

    async def _persist_report(self, tenant_id: str, report: ExerciseReport) -> None:
        blob_path = f"{tenant_id}/reports/{report.report_id}.json"
        if self._blob:
            container = self._blob.get_container_client("simulation")
            try:
                await run_blocking(
                    container.upload_blob,
                    blob_path,
                    json.dumps(report.model_dump(mode="json"), default=str),
                    overwrite=False,
                )
            except Exception as exc:
                if exc.__class__.__name__ != "ResourceExistsError":
                    raise RuntimeError(f"Exercise report persistence failed for {tenant_id}") from exc
            return
        self._memory[tenant_id] = report

    async def persist_archive_manifest(
        self,
        tenant_id: str,
        report: ExerciseReport,
        audit_writer: Any = None,
    ) -> str:
        documents = await self._sim_repo.list_tenant_documents(tenant_id)
        snapshot_digest = await run_blocking(_snapshot_digest, documents)
        writer = audit_writer if audit_writer is not None else self._audit_writer
        audit_events = await writer.read_tenant_events(tenant_id) if writer is not None else []
        audit_entries = await run_blocking(_audit_entries, audit_events)
        manifest = {
            "tenantId": tenant_id,
            "reportId": report.report_id,
            "reportUri": f"simulation/{tenant_id}/reports/{report.report_id}.json",
            "auditPrefix": writer.audit_prefix(tenant_id) if writer is not None else f"audit/{tenant_id}/",
            "auditEventCount": len(audit_entries),
            "auditEvents": audit_entries,
            "auditSnapshotSha256": await run_blocking(_snapshot_digest, audit_events),
            "seedDocumentCount": len(documents),
            "seedSnapshotSha256": snapshot_digest,
            "seedDocuments": documents,
            "createdAt": datetime.now(UTC).isoformat(),
        }
        blob_path = f"{tenant_id}/archive/manifest.json"
        if self._blob:
            container = self._blob.get_container_client("simulation")
            try:
                await run_blocking(
                    container.upload_blob,
                    blob_path,
                    json.dumps(manifest, default=str, sort_keys=True),
                    overwrite=False,
                )
            except Exception as exc:
                if exc.__class__.__name__ != "ResourceExistsError":
                    raise RuntimeError(f"Simulation archive manifest persistence failed for {tenant_id}") from exc
        else:
            self._archive_memory[tenant_id] = manifest
        return f"simulation/{blob_path}"

    async def get_archive_manifest(self, tenant_id: str) -> dict[str, Any] | None:
        if self._blob:
            container = self._blob.get_container_client("simulation")
            blob = container.get_blob_client(f"{tenant_id}/archive/manifest.json")
            try:
                data = await run_blocking(lambda: blob.download_blob().readall())
            except Exception as exc:
                if exc.__class__.__name__ in {"ResourceNotFoundError", "BlobNotFoundError"}:
                    return None
                raise RuntimeError(f"Simulation archive manifest unavailable for {tenant_id}") from exc
            return json.loads(data)
        return self._archive_memory.get(tenant_id)

    async def delete_archive(self, tenant_id: str, report_uri: str | None, archive_uri: str | None) -> None:
        """Destroy report/manifest evidence.

        Deprecated for the retention-governed delete path (AUD-022): operational
        deletion must retain immutable report/manifest evidence. Retained only for
        explicit, separately authorized evidence-destruction workflows.
        """
        if self._blob:
            container = self._blob.get_container_client("simulation")
            for uri in (report_uri, archive_uri):
                if not uri:
                    continue
                blob_name = uri.replace("simulation/", "", 1)
                try:
                    await run_blocking(container.delete_blob, blob_name)
                except Exception as exc:
                    if exc.__class__.__name__ not in {"ResourceNotFoundError", "BlobNotFoundError"}:
                        raise RuntimeError(f"Simulation archive deletion failed for {tenant_id}") from exc
        self._memory.pop(tenant_id, None)
        self._archive_memory.pop(tenant_id, None)


def _snapshot_digest(documents: list[dict[str, Any]]) -> str:
    snapshot = json.dumps(documents, default=str, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(snapshot.encode("utf-8")).hexdigest()


def _audit_entries(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per-record identity and checksum so the manifest can be verified item by item."""
    entries: list[dict[str, Any]] = []
    for event in events:
        payload = json.dumps(event, default=str, sort_keys=True, separators=(",", ":"))
        entries.append(
            {
                "eventId": event.get("event_id"),
                "action": event.get("action"),
                "timestamp": event.get("timestamp"),
                "blobName": event.get("_blob_name"),
                "sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            }
        )
    return entries


def _first_timeline_timestamp(events: list[Any], event_types: set[str]) -> datetime | None:
    values = [event.wall_clock_time for event in events if event.event_type in event_types]
    return min(values) if values else None


def _seconds_since(start: datetime, end: datetime | None) -> float | None:
    if end is None:
        return None
    return max(0.0, (end - start).total_seconds())


def _benchmark_comparison(
    targets: dict[str, Any],
    metrics: PerformanceMetrics,
    prior_metrics: PerformanceMetrics | None = None,
) -> list[BenchmarkComparison]:
    rows = [
        (
            "time_to_first_recommendation_s",
            targets.get("time_to_first_recommendation_s"),
            metrics.time_to_first_recommendation_s,
            "max",
        ),
        ("time_to_alert_s", targets.get("time_to_alert_s"), metrics.time_to_alert_publication_s, "max"),
        (
            "coordination_coverage_pct",
            targets.get("coordination_coverage_pct"),
            metrics.coordination_coverage_pct,
            "min",
        ),
    ]
    return [
        BenchmarkComparison(
            metric=name,
            target=float(target),
            actual=actual,
            passed=actual is not None and (actual <= float(target) if direction == "max" else actual >= float(target)),
            prior_actual=getattr(prior_metrics, _prior_metric_name(name), None) if prior_metrics is not None else None,
            delta_from_prior=_delta_from_prior(
                actual,
                getattr(prior_metrics, _prior_metric_name(name), None) if prior_metrics is not None else None,
            ),
        )
        for name, target, actual, direction in rows
        if target is not None
    ]


def _prior_metric_name(metric: str) -> str:
    return "time_to_alert_publication_s" if metric == "time_to_alert_s" else metric


def _delta_from_prior(actual: float | None, prior: float | None) -> float | None:
    if actual is None or prior is None:
        return None
    return actual - prior
