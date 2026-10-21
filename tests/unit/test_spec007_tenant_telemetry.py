from __future__ import annotations

import logging

import pytest
from app.core.tenant_context import TenantContext, reset_current_tenant, set_current_tenant
from app.observability.tenant_telemetry import TenantLogFilter, TenantSpanProcessor, annotate_current_span

pytestmark = pytest.mark.spec007_isolation


class _Span:
    def __init__(self) -> None:
        self.attributes = {}

    def is_recording(self) -> bool:
        return True

    def set_attribute(self, name, value):  # noqa: ANN001, ANN201
        self.attributes[name] = value


def test_log_filter_stamps_current_tenant() -> None:
    token = set_current_tenant(TenantContext("ses-nsw", ("nsw",), tenant_id="sim-drill"))
    try:
        record = logging.LogRecord("test", logging.INFO, __file__, 1, "message", (), None)
        assert TenantLogFilter().filter(record) is True
        assert record.tenant_id == "sim-drill"
    finally:
        reset_current_tenant(token)


def test_span_processor_stamps_current_tenant() -> None:
    token = set_current_tenant(TenantContext("ses-nsw", ("nsw",), tenant_id="sim-drill"))
    try:
        span = _Span()
        TenantSpanProcessor().on_start(span)
        assert span.attributes["tenant_id"] == "sim-drill"
    finally:
        reset_current_tenant(token)


def test_request_annotation_includes_mode(monkeypatch) -> None:
    span = _Span()
    monkeypatch.setattr("opentelemetry.trace.get_current_span", lambda: span)

    annotate_current_span(TenantContext("ses-nsw", ("nsw",), tenant_id="sim-drill"))

    assert span.attributes == {"tenant_id": "sim-drill", "tenant.mode": "simulation"}
