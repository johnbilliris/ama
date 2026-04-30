import asyncio
import logging
import os
import signal
from typing import Any

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

from apps.ingestion.pipeline_config import IngestionPipelineConfig

logger = logging.getLogger(__name__)


class PipelineWorker:
    """Lifecycle manager for ingestion pipeline instances (FR-001a).

    Runs as a long-lived background worker within Azure Container Apps.
    Manages multiple pipeline instances from configuration, supports
    graceful shutdown, and exposes health check state.
    """

    def __init__(self) -> None:
        self._pipelines: dict[str, Any] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._running = False
        self._healthy = True

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
        return self._running and self._healthy

    @property
    def is_ready(self) -> bool:
        return self._running and len(self._pipelines) > 0

    def get_status(self) -> dict[str, Any]:
        statuses = []
        for pid, pipeline in self._pipelines.items():
            statuses.append(
                {
                    "pipelineId": pid,
                    "circuitBreakerState": pipeline.circuit_breaker.state,
                    "metrics": pipeline._metrics.to_dict() if hasattr(pipeline, "_metrics") else {},
                }
            )
        return {
            "running": self._running,
            "pipelineCount": len(self._pipelines),
            "pipelines": statuses,
        }


# ---------------------------------------------------------------------------
# Lightweight health server – keeps the container alive and satisfies
# Container Apps ingress health probes on the configured targetPort.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    # configure_azure_monitor() (called at module level) may have already
    # added handlers to the root logger, which makes basicConfig() a no-op.
    # Explicitly add a StreamHandler so logs also reach stdout/stderr (and
    # thus Azure Container Apps console log stream).
    _fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    _console = logging.StreamHandler()
    _console.setFormatter(_fmt)
    root = logging.getLogger()
    root.addHandler(_console)
    root.setLevel(logging.INFO)

    # Suppress noisy INFO-level HTTP request/response logging from SDKs.
    # These log every request (including 4xx/5xx) at INFO, masking real issues.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
    logging.getLogger("azure.monitor.opentelemetry.exporter").setLevel(logging.WARNING)

    _PORT = int(os.environ.get("PORT", "8081"))
    _worker = PipelineWorker()

    class _HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status":"healthy"}')
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):  # noqa: A002
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
    from apps.api.app.services.ingestion.dedup_service import DedupService

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
                port=6380,
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

    def _factory(config):
        return create_pipeline(config, blob_storage=_blob_store, dedup_service=_dedup_service)

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
