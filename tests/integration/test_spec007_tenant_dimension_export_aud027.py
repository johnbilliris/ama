"""AUD-027 — tenant_id on the exported telemetry pipeline, with no cross-request carry-over."""

from __future__ import annotations

import logging

import pytest
from app.core.tenant_context import TenantContext, reset_current_tenant, set_current_tenant
from app.middleware.tenant_middleware import add_tenant_middleware
from app.observability import simulation_metrics, tenant_telemetry
from app.observability.tenant_telemetry import (
    UNKNOWN_TENANT,
    TenantSpanProcessor,
    configure_tenant_telemetry,
    current_tenant_id,
    telemetry_status,
)
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from apps.ingestion import telemetry as ingestion_telemetry

pytestmark = pytest.mark.spec007_isolation

PROBE_LOGGER = "aud027.probe"


class _RecordingSpan:
    def __init__(self) -> None:
        self.attributes: dict[str, object] = {}

    def is_recording(self) -> bool:
        return True

    def set_attribute(self, key: str, value: object) -> None:
        self.attributes[key] = value


class _RecordingProvider:
    """In-memory stand-in for an exporting tracer provider."""

    def __init__(self) -> None:
        self.processors: list[object] = []
        self.exported: list[_RecordingSpan] = []

    def add_span_processor(self, processor: object) -> None:
        self.processors.append(processor)

    def export_span(self) -> _RecordingSpan:
        span = _RecordingSpan()
        for processor in self.processors:
            processor.on_start(span)  # type: ignore[attr-defined]
        self.exported.append(span)
        return span


class _CapturingHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class _StubTenant:
    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self.status = "Active"
        self.participants = ["user-1"]
        self.created_by = "user-1"


class _StubSimulationRepository:
    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id

    async def get_by_tenant_id(self, tenant_id: str):  # noqa: ANN201
        return _StubTenant(tenant_id) if tenant_id == self._tenant_id else None

    async def get_by_participant(self, _subject: str):  # noqa: ANN201
        return []

    async def touch_activity(self, _tenant_id: str) -> None:
        return None


class _ClaimsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # noqa: ANN001, ANN201
        request.state.claims = {
            "oid": "user-1",
            "roles": ["SimulationUser"],
            "agency_id": "nema",
            "jurisdiction_ids": ["nsw"],
        }
        return await call_next(request)


@pytest.fixture
def provider(monkeypatch: pytest.MonkeyPatch) -> _RecordingProvider:
    recorder = _RecordingProvider()
    monkeypatch.setattr("opentelemetry.trace.get_tracer_provider", lambda: recorder)
    configure_tenant_telemetry()
    return recorder


@pytest.fixture
def log_capture() -> _CapturingHandler:
    handler = _CapturingHandler()
    logger = logging.getLogger(PROBE_LOGGER)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    try:
        yield handler
    finally:
        logger.removeHandler(handler)


def _build_app(provider: _RecordingProvider, sim_tenant_id: str, request_spans: list[_RecordingSpan]) -> FastAPI:
    app = FastAPI()
    add_tenant_middleware(app, simulation_repository=_StubSimulationRepository(sim_tenant_id))
    app.add_middleware(_ClaimsMiddleware)

    @app.post("/api/simulations/{tenant_id}/probe")
    async def simulation_probe(tenant_id: str) -> dict[str, str]:  # noqa: ARG001
        request_spans.append(provider.export_span())
        logging.getLogger(PROBE_LOGGER).info("simulation probe")
        return {"ok": "true"}

    @app.post("/api/signals/probe")
    async def live_probe() -> dict[str, str]:
        request_spans.append(provider.export_span())
        logging.getLogger(PROBE_LOGGER).info("live probe")
        return {"ok": "true"}

    return app


def test_request_spans_and_logs_export_tenant_without_carry_over(
    provider: _RecordingProvider,
    log_capture: _CapturingHandler,
) -> None:
    sim_tenant_id = "sim-aud027-0001"
    request_spans: list[_RecordingSpan] = []
    client = TestClient(_build_app(provider, sim_tenant_id, request_spans))

    simulation = client.post(f"/api/simulations/{sim_tenant_id}/probe")
    live = client.post("/api/signals/probe")

    assert simulation.status_code == 200
    assert live.status_code == 200
    assert simulation.headers["X-Tenant-Id"] == sim_tenant_id
    assert live.headers["X-Tenant-Id"] == "live"

    assert [span.attributes["tenant_id"] for span in request_spans] == [sim_tenant_id, "live"]
    assert [record.tenant_id for record in log_capture.records] == [sim_tenant_id, "live"]


def test_span_processor_is_registered_and_reported(provider: _RecordingProvider) -> None:
    assert any(isinstance(processor, TenantSpanProcessor) for processor in provider.processors)
    status = telemetry_status()
    assert status["configured"] is True
    assert status["log_records"] == "healthy"
    assert status["spans"] in {"healthy", "degraded"}


def test_span_processor_subclasses_the_sdk_when_available() -> None:
    sdk_trace = pytest.importorskip("opentelemetry.sdk.trace")

    assert issubclass(TenantSpanProcessor, sdk_trace.SpanProcessor)
    assert TenantSpanProcessor.sdk_backed is True


def test_sdk_exporter_receives_tenant_dimension() -> None:
    sdk_trace = pytest.importorskip("opentelemetry.sdk.trace")
    export = pytest.importorskip("opentelemetry.sdk.trace.export")
    in_memory = pytest.importorskip("opentelemetry.sdk.trace.export.in_memory_span_exporter")

    exporter = in_memory.InMemorySpanExporter()
    sdk_provider = sdk_trace.TracerProvider()
    sdk_provider.add_span_processor(TenantSpanProcessor())
    sdk_provider.add_span_processor(export.SimpleSpanProcessor(exporter))
    tracer = sdk_provider.get_tracer("aud027")

    token = set_current_tenant(TenantContext("ses-nsw", ("nsw",), tenant_id="sim-export"))
    try:
        with tracer.start_as_current_span("simulation.request"):
            pass
    finally:
        reset_current_tenant(token)
    with tracer.start_as_current_span("live.request"):
        pass

    exported = {span.name: span.attributes.get("tenant_id") for span in exporter.get_finished_spans()}
    assert exported == {"simulation.request": "sim-export", "live.request": UNKNOWN_TENANT}


def test_configuration_failure_is_surfaced_not_swallowed(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fail(_factory):  # noqa: ANN001, ANN202
        raise RuntimeError("log factory locked")

    monkeypatch.setattr(logging, "setLogRecordFactory", _fail)
    monkeypatch.setattr(
        tenant_telemetry.logging,
        "getLogRecordFactory",
        lambda: logging.LogRecord,
    )

    status = configure_tenant_telemetry()

    assert status["log_records"] == "unavailable"
    assert any("log factory locked" in error for error in status["errors"])


def test_unscoped_background_work_is_unknown_not_live() -> None:
    assert current_tenant_id() == UNKNOWN_TENANT
    assert ingestion_telemetry.tenant_attributes({"pipeline.id": "bom"}) == {
        "pipeline.id": "bom",
        "tenant_id": UNKNOWN_TENANT,
    }
    assert simulation_metrics.tenant_attributes()["tenant_id"] == UNKNOWN_TENANT


def test_explicit_scope_keeps_system_ingestion_labelled_live() -> None:
    assert ingestion_telemetry.tenant_attributes({"pipeline.id": "bom"}, tenant_id="live") == {
        "pipeline.id": "bom",
        "tenant_id": "live",
    }
    assert ingestion_telemetry.tenant_attributes({}, tenant_id="sim-abc") == {"tenant_id": "sim-abc"}


def test_metric_helpers_carry_the_active_simulation_scope() -> None:
    token = set_current_tenant(TenantContext("ses-nsw", ("nsw",), tenant_id="sim-metrics"))
    try:
        assert simulation_metrics.tenant_attributes()["tenant_id"] == "sim-metrics"
        assert ingestion_telemetry.tenant_attributes()["tenant_id"] == "sim-metrics"
    finally:
        reset_current_tenant(token)

    assert simulation_metrics.tenant_attributes()["tenant_id"] == UNKNOWN_TENANT
