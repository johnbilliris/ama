import asyncio
import json
import logging
import os
import signal
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from apps.console_logging import configure_console_logging
from apps.ingestion.pipeline_config import IngestionPipelineConfig
from packages.domain.src.domain.repositories.signal_repository import SignalRepository

if os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    try:
        from azure.identity import ManagedIdentityCredential
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(
            enable_live_metrics=True,
            credential=ManagedIdentityCredential(),
        )
    except Exception:
        logging.getLogger(__name__).warning("Failed to configure Azure Monitor", exc_info=True)

configure_console_logging()

logger = logging.getLogger(__name__)

SIGNAL_ENVELOPE_V1_SCHEMA_ID = "https://example.gov.au/schemas/signal-envelope.schema.json"


def _build_signal_repository() -> tuple[SignalRepository, str | None]:
    endpoint = os.environ.get("COSMOS_ENDPOINT")
    environment = (os.environ.get("AMA_ENVIRONMENT") or os.environ.get("ENVIRONMENT") or "dev").lower()
    if not endpoint:
        if environment in {"production", "staging"}:
            raise RuntimeError("SignalRepository requires COSMOS_ENDPOINT in production/staging")
        return SignalRepository(), None

    try:
        from azure.cosmos.aio import CosmosClient
        from azure.identity.aio import DefaultAzureCredential

        client = CosmosClient(endpoint, credential=DefaultAzureCredential())
    except Exception as exc:
        return SignalRepository(), str(exc)
    return SignalRepository(cosmos_client=client), None


def _load_and_compile_schema(schema_path: Path) -> Draft202012Validator:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if schema.get("$id") != SIGNAL_ENVELOPE_V1_SCHEMA_ID:
        raise ValueError(f"Signal envelope schema must use v1 ID {SIGNAL_ENVELOPE_V1_SCHEMA_ID}")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


class PipelineWorker:
    """Lifecycle manager for ingestion pipeline instances (FR-001a).

    Runs as a long-lived background worker within Azure Container Apps.
    Manages multiple pipeline instances from configuration, supports
    graceful shutdown, and exposes health check state.
    """

    def __init__(self) -> None:
        self._pipelines: dict[str, Any] = {}
        self._tasks: dict[str, asyncio.Task[Any]] = {}
        self._running = False
        self._healthy = True
        self._repository_available = True
        self._repository_reason: str | None = None
        self._replica_id = os.environ.get("CONTAINER_APP_REPLICA_NAME", "local")

    async def start(self, configs: list[IngestionPipelineConfig], pipeline_factory: Any = None) -> None:
        self._running = True
        logger.info("Pipeline worker starting with %d pipeline configs", len(configs))

        for config in configs:
            if not config.enabled:
                logger.info("Pipeline %s disabled, skipping", config.pipeline_id)
                continue
            if pipeline_factory:
                pipeline = pipeline_factory(config)
            else:
                logger.warning("No pipeline factory — skipping %s", config.pipeline_id)
                continue
            self._pipelines[config.pipeline_id] = pipeline
            self._tasks[config.pipeline_id] = asyncio.create_task(pipeline.run(), name=f"pipeline-{config.pipeline_id}")
            logger.info("Started pipeline %s (interval=%ds)", config.pipeline_id, config.poll_interval_seconds)

        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))
            except NotImplementedError:
                pass

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        logger.info("Pipeline worker stopping — completing in-progress cycles")

        for pipeline_id, pipeline in self._pipelines.items():
            await pipeline.stop()
            logger.info("Pipeline %s stop requested", pipeline_id)

        for pipeline_id, task in self._tasks.items():
            try:
                await asyncio.wait_for(task, timeout=30)
            except TimeoutError:
                task.cancel()
                logger.warning("Pipeline %s forcibly cancelled after timeout", pipeline_id)
            except Exception:
                logger.exception("Pipeline %s error during shutdown", pipeline_id)

        logger.info("Pipeline worker stopped")

    @property
    def is_healthy(self) -> bool:
        healthy, _ = self.evaluate_health()
        return healthy

    @property
    def is_ready(self) -> bool:
        return self._running and len(self._pipelines) > 0

    def set_repository_status(self, available: bool, reason: str | None = None) -> None:
        self._repository_available = available
        self._repository_reason = reason

    def evaluate_health(self) -> tuple[bool, list[str]]:
        reasons: list[str] = []
        now = datetime.now(UTC)

        if not self._running:
            reasons.append("worker_not_running")

        if not self._healthy:
            reasons.append("worker_marked_degraded")

        if not self._repository_available:
            reasons.append(f"repository_unavailable:{self._repository_reason or 'unknown'}")

        for pipeline_id, pipeline in self._pipelines.items():
            breaker = getattr(pipeline, "circuit_breaker", None)
            expected_update_seconds = int(getattr(pipeline, "expected_update_seconds", 60))
            if breaker is None:
                continue

            if breaker.state == "open":
                reasons.append(f"pipeline_open:{pipeline_id}")

            last_success = getattr(breaker, "last_success_at", None)
            if last_success is None:
                reasons.append(f"pipeline_never_succeeded:{pipeline_id}")
                continue

            freshness_age = (now - last_success).total_seconds()
            if freshness_age > expected_update_seconds:
                reasons.append(
                    f"pipeline_stale:{pipeline_id}:age={int(freshness_age)}s:expected={expected_update_seconds}s"
                )

        return (len(reasons) == 0, reasons)

    def get_status(self) -> dict[str, Any]:
        statuses = []
        for pid, pipeline in self._pipelines.items():
            snapshotter = getattr(pipeline, "_pipeline_status_snapshot", None)
            if callable(snapshotter):
                snapshot = dict(snapshotter())
                health = dict(snapshot.get("health") or {})
                task = self._tasks.get(pid)
                if task is None or not task.done():
                    task_state = "running" if self._running else "stopped"
                elif task.cancelled():
                    task_state = "stopped"
                elif task.exception() is not None:
                    task_state = "failed"
                    health["state"] = "failed"
                    health["reason"] = str(task.exception())
                else:
                    task_state = "stopped"
                health["taskState"] = task_state
                if task_state == "stopped":
                    health["state"] = "stopped"
                snapshot["health"] = health
                snapshot["replicaId"] = self._replica_id
                statuses.append(snapshot)
                continue

            breaker = pipeline.circuit_breaker
            expected_update_seconds = int(getattr(pipeline, "expected_update_seconds", 60))
            last_success_at = breaker.last_success_at.isoformat() if breaker.last_success_at else None
            freshness_seconds = None
            freshness_status = "unknown"
            if breaker.last_success_at:
                freshness_seconds = int((datetime.now(UTC) - breaker.last_success_at).total_seconds())
                freshness_status = "stale" if freshness_seconds > expected_update_seconds else "fresh"
            statuses.append(
                {
                    "pipelineId": pid,
                    "circuitBreakerState": breaker.state,
                    "lastSuccessAt": last_success_at,
                    "expectedUpdateSeconds": expected_update_seconds,
                    "freshnessSeconds": freshness_seconds,
                    "freshnessStatus": freshness_status,
                    "metrics": pipeline._metrics.to_dict() if hasattr(pipeline, "_metrics") else {},
                }
            )
        healthy, reasons = self.evaluate_health()
        return {
            "running": self._running,
            "pipelineCount": len(self._pipelines),
            "pipelines": statuses,
            "repository": {
                "available": self._repository_available,
                "reason": self._repository_reason,
            },
            "health": {
                "healthy": healthy,
                "reasons": reasons,
            },
        }


# ---------------------------------------------------------------------------
# Lightweight health server – keeps the container alive and satisfies
# Container Apps ingress health probes on the configured targetPort.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    # Suppress noisy INFO-level HTTP request/response logging from SDKs.
    # These log every request (including 4xx/5xx) at INFO, masking real issues.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
    logging.getLogger("azure.monitor.opentelemetry.exporter").setLevel(logging.WARNING)

    _PORT = int(os.environ.get("PORT", "8081"))
    _worker = PipelineWorker()

    class _HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/health":
                status = _worker.get_status()
                healthy = _worker.is_healthy
                body = {"status": "healthy" if healthy else "degraded", "worker": status}
                self.send_response(200 if healthy else 503)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(body).encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            pass  # suppress per-request logs

    # Start health server in a daemon thread so the main thread can run the
    # async worker event loop.
    _http = HTTPServer(("0.0.0.0", _PORT), _HealthHandler)
    _http_thread = threading.Thread(target=_http.serve_forever, daemon=True)
    _http_thread.start()
    logger.info("Ingestion health server listening on port %d", _PORT)

    # Load pipeline configs and run the worker on the main thread event loop.
    from apps.ingestion.pipeline_configs import PIPELINE_CONFIGS
    from apps.ingestion.pipeline_factory import create_pipeline

    # Build blob storage client when STORAGE_ACCOUNT_NAME is available (Azure)
    _blob_store = None
    _storage_account = os.environ.get("STORAGE_ACCOUNT_NAME")
    if _storage_account:
        try:
            from apps.ingestion.blob_store import RawPayloadBlobStore

            _blob_store = RawPayloadBlobStore(_storage_account)
            logger.info("Blob store initialised for account %s", _storage_account)
        except Exception:
            logger.warning("Failed to initialise blob store", exc_info=True)
    else:
        logger.info("STORAGE_ACCOUNT_NAME not set — raw payload archival disabled")

    # Build dedup service (uses Redis when available, falls back to local dict)
    from apps.api.app.services.ingestion.audit_writer import AuditWriter
    from apps.api.app.services.ingestion.dedup_service import DedupService
    from apps.api.app.services.ingestion.incident_association import IncidentAssociationService

    _redis_client = None
    _redis_host = os.environ.get("REDIS_HOST")
    if _redis_host:
        try:
            import redis as redis_lib
            from redis_entraid.cred_provider import create_from_managed_identity
            from redis_entraid.identity_provider import ManagedIdentityType

            credential_provider = create_from_managed_identity(
                identity_type=ManagedIdentityType.SYSTEM_ASSIGNED,
                resource="https://redis.azure.com/.default",
            )
            _redis_client = redis_lib.Redis(
                host=_redis_host,
                port=int(os.environ.get("REDIS_PORT", "10000")),
                ssl=True,
                decode_responses=True,
                credential_provider=credential_provider,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            _redis_client.ping()
            logger.info("Redis dedup backend connected at %s (Entra ID auth)", _redis_host)
        except Exception:
            logger.warning("Failed to connect Redis for dedup — using in-memory fallback", exc_info=True)
            _redis_client = None

    _dedup_service = DedupService(redis_client=_redis_client)
    logger.info("Dedup service initialised (redis=%s)", _redis_client is not None)
    _signal_repository, _signal_repository_error = _build_signal_repository()
    if _signal_repository_error:
        _worker._healthy = False
        _worker.set_repository_status(False, _signal_repository_error)
        logger.error("Signal repository degraded: %s", _signal_repository_error)
    logger.info("Signal repository initialised for ingestion persistence")

    _signal_schema: dict[str, Any] = {}
    _schema_path = Path("packages/schemas/signal-envelope.schema.json")
    try:
        _signal_schema = _load_and_compile_schema(_schema_path).schema
    except Exception:
        logger.warning("Failed to load signal schema for ingestion validation", exc_info=True)
    _audit_writer = AuditWriter(blob_storage=_blob_store)
    _incident_association = IncidentAssociationService()

    def _factory(config: IngestionPipelineConfig) -> Any:
        return create_pipeline(
            config,
            blob_storage=_blob_store,
            dedup_service=_dedup_service,
            signal_repository=_signal_repository,
            audit_writer=_audit_writer,
            incident_association=_incident_association,
            schema=_signal_schema or None,
        )

    async def _run() -> None:
        logger.info("Ingestion worker starting — %d pipeline configs loaded", len(PIPELINE_CONFIGS))
        await _worker.start(PIPELINE_CONFIGS, pipeline_factory=_factory)
        # Keep the loop alive until a termination signal arrives.
        stop_event = asyncio.Event()

        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, stop_event.set)
            except NotImplementedError:
                pass  # Windows — signals handled via KeyboardInterrupt

        try:
            await stop_event.wait()
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            logger.info("Shutdown signal received")
            await _worker.stop()
            _http.shutdown()

    asyncio.run(_run())
