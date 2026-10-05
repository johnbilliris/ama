"""Composition root for the operational Evacuation Agent service."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from typing import Any

from evacuation.agent import EvacuationAgent, create_app, run_consumer
from evacuation.config import EvacuationConfig
from evacuation.road_network import RoadNetworkLoader
from evacuation.telemetry import configure_telemetry
from fastapi import FastAPI

from apps.console_logging import configure_console_logging, uvicorn_log_config

logger = logging.getLogger(__name__)

_REQUIRED_CONTAINERS = ("plans", "decisions", "assessments", "recommendations")
_PRODUCTION_ENVIRONMENTS = {"staging", "production"}


class ThreadedServiceBusConsumer:
    """Own the blocking Service Bus receive loop for the HTTP process lifetime."""

    def __init__(
        self,
        agent: EvacuationAgent,
        config: EvacuationConfig,
        *,
        target: Callable[..., None] = run_consumer,
    ) -> None:
        self._agent = agent
        self._config = config
        self._target = target
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        if not (self._config.azure_servicebus_connection or self._config.azure_servicebus_namespace):
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="evacuation-service-bus-consumer",
            daemon=True,
        )
        self._thread.start()

    def _run(self) -> None:
        update_health = getattr(self._agent, "update_queue_health", None)
        if callable(update_health):
            update_health(status="reconnecting")
        try:
            self._target(
                agent=self._agent,
                connection_string=self._config.azure_servicebus_connection or None,
                fully_qualified_namespace=self._config.azure_servicebus_namespace or None,
                queue_name=self._config.service_bus_queue_name,
                stop_event=self._stop_event,
            )
        finally:
            if callable(update_health):
                update_health(status="offline")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            if self._thread.is_alive():
                raise RuntimeError("Evacuation Service Bus consumer did not stop")
            self._thread = None


class ThreadedDependencyHealthMonitor:
    """Refresh dependency health outside HTTP request handling."""

    def __init__(
        self,
        agent: EvacuationAgent,
        *,
        interval_seconds: float = 30,
        probe_timeout_seconds: float = 0.5,
    ) -> None:
        self._agent = agent
        self._interval_seconds = interval_seconds
        self._probe_timeout_seconds = probe_timeout_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._probe_thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="evacuation-dependency-health",
            daemon=True,
        )
        self._thread.start()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self.probe_once()
            try:
                snapshot = self._agent.health_snapshot()
                self._agent.record_health_transition(
                    str(snapshot["status"]),
                    datetime.now(UTC),
                )
            except Exception:
                logger.exception("Dependency health transition audit failed")
            self._stop_event.wait(self._interval_seconds)

    def probe_once(self) -> None:
        if self._probe_thread is not None and self._probe_thread.is_alive():
            self._agent.update_llm_health(
                status="offline",
                checked_at=datetime.now(UTC),
                latency_ms=None,
            )
            return

        def probe() -> None:
            started = time.perf_counter()
            checked_at = datetime.now(UTC)

            def update_if_not_timed_out(**values: Any) -> None:
                with probe_update_lock:
                    if not probe_timed_out.is_set():
                        self._agent.update_llm_health(**values)

            try:
                self._agent._llm_client.generate_response(
                    purpose="reasoning",
                    prompt="health check ping",
                    max_output_tokens=5,
                    timeout_seconds=self._probe_timeout_seconds,
                )
            except Exception:
                update_if_not_timed_out(
                    status="offline",
                    checked_at=checked_at,
                    latency_ms=None,
                )
                return
            latency_ms = round((time.perf_counter() - started) * 1000)
            if latency_ms > self._probe_timeout_seconds * 1_000:
                update_if_not_timed_out(
                    status="offline",
                    checked_at=checked_at,
                    latency_ms=latency_ms,
                )
                return
            update_if_not_timed_out(
                status="healthy" if latency_ms < 5_000 else "degraded",
                checked_at=checked_at,
                latency_ms=latency_ms,
            )

        probe_update_lock = threading.Lock()
        probe_timed_out = threading.Event()
        self._probe_thread = threading.Thread(
            target=probe,
            name="evacuation-llm-health-probe",
            daemon=True,
        )
        self._probe_thread.start()
        self._probe_thread.join(timeout=self._probe_timeout_seconds)
        if self._probe_thread.is_alive():
            with probe_update_lock:
                probe_timed_out.set()
                self._agent.update_llm_health(
                    status="offline",
                    checked_at=datetime.now(UTC),
                    latency_ms=None,
                )

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            if self._thread.is_alive():
                raise RuntimeError("Dependency health monitor did not stop")
            self._thread = None


class _NoOpConsumer:
    def start(self) -> None:
        return

    def stop(self) -> None:
        return


class ThreadedPlanLifecycleSweeper:
    """Expire due proposal and paused plans until service shutdown."""

    def __init__(self, agent: EvacuationAgent, config: EvacuationConfig) -> None:
        self._agent = agent
        self._interval_seconds = config.plan_lifecycle_sweep_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="evacuation-plan-lifecycle-sweeper",
            daemon=True,
        )
        self._thread.start()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._agent.expire_all_due_plans()
            except Exception:
                logger.exception("Evacuation plan lifecycle sweep failed")
            self._stop_event.wait(self._interval_seconds)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            if self._thread.is_alive():
                raise RuntimeError("Evacuation lifecycle sweeper did not stop")
            self._thread = None


def build_application(
    config: EvacuationConfig | None = None,
    *,
    containers: dict[str, Any] | None = None,
    road_network: RoadNetworkLoader | None = None,
    reference_data: dict[str, Any] | None = None,
    consumer: Any = None,
    lifecycle_sweeper: Any = None,
    dependency_health_monitor: Any = None,
    principal_resolver: Any = None,
) -> FastAPI:
    """Compose the configured deterministic planner and its intake lifecycle."""
    configure_telemetry()
    runtime_config = config or EvacuationConfig()
    network = road_network or _load_road_network(runtime_config)
    data = reference_data if reference_data is not None else _load_reference_data(runtime_config)
    resolved_containers, cosmos_client = (
        (containers, None) if containers is not None else _resolve_containers(runtime_config)
    )
    resolved_containers = resolved_containers or {}
    _validate_runtime_dependencies(runtime_config, network, resolved_containers)

    agent = EvacuationAgent(
        config=runtime_config,
        road_network=network,
        cosmos_plans_container=resolved_containers.get("plans"),
        cosmos_decisions_container=resolved_containers.get("decisions"),
        cosmos_assessments_container=resolved_containers.get("assessments"),
        cosmos_recommendations_container=resolved_containers.get("recommendations"),
        population_data=(
            list(data["population_density"]) if isinstance(data.get("population_density"), list) else None
        ),
        facility_data=(list(data["facilities"]) if isinstance(data.get("facilities"), list) else None),
        reference_data_metadata=(data.get("metadata") if isinstance(data.get("metadata"), dict) else None),
    )
    intake = consumer
    if intake is None:
        intake = (
            ThreadedServiceBusConsumer(agent, runtime_config)
            if runtime_config.azure_servicebus_connection or runtime_config.azure_servicebus_namespace
            else _NoOpConsumer()
        )
    sweeper = lifecycle_sweeper
    if sweeper is None:
        sweeper = (
            ThreadedPlanLifecycleSweeper(agent, runtime_config)
            if resolved_containers.get("plans") is not None and hasattr(resolved_containers["plans"], "query_items")
            else _NoOpConsumer()
        )
    health_monitor = dependency_health_monitor or ThreadedDependencyHealthMonitor(agent)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        intake.start()
        sweeper.start()
        health_monitor.start()
        try:
            yield
        finally:
            health_monitor.stop()
            sweeper.stop()
            intake.stop()
            close = getattr(cosmos_client, "close", None)
            if callable(close):
                close()

    app = create_app(
        agent=agent,
        config=runtime_config,
        principal_resolver=principal_resolver,
        lifespan=lifespan,
    )
    app.state.runtime_config = runtime_config
    app.state.runtime_containers = resolved_containers
    app.state.runtime_consumer = intake
    app.state.lifecycle_sweeper = sweeper
    app.state.dependency_health_monitor = health_monitor
    app.state.reference_data = data
    return app


def _load_road_network(config: EvacuationConfig) -> RoadNetworkLoader:
    path = Path(config.road_network_file_path)
    network = RoadNetworkLoader(staleness_hours=config.road_data_staleness_hours)
    try:
        network.load(str(path))
        if network.node_count == 0 or network.edge_count == 0:
            raise RuntimeError("Road network did not produce a routable graph")
    except Exception:
        logger.exception("Road network unavailable; runtime will provide generic guidance")
    return network


def _load_reference_data(config: EvacuationConfig) -> dict[str, Any]:
    path = Path(config.population_data_file_path)
    try:
        if not path.is_file():
            raise FileNotFoundError(f"Population reference data is unavailable: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Population reference data must be a JSON object")
        for field in ("population_density", "facilities"):
            if not isinstance(data.get(field), list):
                raise ValueError(f"Population reference data requires a {field} list")
        return data
    except (OSError, ValueError) as exc:
        logger.exception("Population/facility reference data unavailable; needs remain unknown")
        return {
            "metadata": {"load_error": str(exc)},
            "population_density": None,
            "facilities": None,
        }


def _resolve_containers(
    config: EvacuationConfig,
) -> tuple[dict[str, Any], Any]:
    if not config.azure_cosmos_endpoint:
        return {}, None

    from azure.cosmos import CosmosClient
    from azure.identity import DefaultAzureCredential

    client_id = os.environ.get("AZURE_CLIENT_ID")
    credential = DefaultAzureCredential(managed_identity_client_id=client_id) if client_id else DefaultAzureCredential()
    client = CosmosClient(config.azure_cosmos_endpoint, credential=credential)
    database = client.get_database_client(config.cosmos_database_name)
    return (
        {
            "plans": database.get_container_client(config.plans_container_name),
            "decisions": database.get_container_client(config.decisions_container_name),
            "assessments": database.get_container_client(config.assessments_container_name),
            "recommendations": database.get_container_client(config.recommendations_container_name),
        },
        client,
    )


def _validate_runtime_dependencies(
    config: EvacuationConfig,
    network: RoadNetworkLoader,
    containers: dict[str, Any],
) -> None:
    if config.environment not in _PRODUCTION_ENVIRONMENTS:
        return
    missing = [name for name in _REQUIRED_CONTAINERS if containers.get(name) is None]
    if missing:
        raise RuntimeError(f"Evacuation runtime requires Cosmos containers: {', '.join(missing)}")
    if not (config.azure_servicebus_connection or config.azure_servicebus_namespace):
        raise RuntimeError("Evacuation runtime requires an Azure Service Bus namespace outside development")


def main() -> None:
    """Run the fully composed Evacuation Agent HTTP and intake service."""
    uvicorn = import_module("uvicorn")
    configure_console_logging()
    config = EvacuationConfig()
    port = int(os.environ.get("PORT", "8082"))
    logger.info("Evacuation Agent service starting on port %d", port)
    uvicorn.run(
        build_application(config),
        host="0.0.0.0",
        port=port,
        log_level="info",
        log_config=uvicorn_log_config(),
    )


__all__ = [
    "ThreadedDependencyHealthMonitor",
    "ThreadedPlanLifecycleSweeper",
    "ThreadedServiceBusConsumer",
    "build_application",
    "main",
]
