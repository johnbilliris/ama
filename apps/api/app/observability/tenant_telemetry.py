from __future__ import annotations

import logging
from typing import Any

from app.core.tenant_context import TenantContext, get_current_tenant

logger = logging.getLogger(__name__)

UNKNOWN_TENANT = "unknown"

_STATUS: dict[str, Any] = {
    "configured": False,
    "log_records": "unconfigured",
    "spans": "unconfigured",
    "errors": [],
}


def current_tenant_id(default: str = UNKNOWN_TENANT) -> str:
    """Resolve the ambient tenant.

    Background work without an explicit scope is reported as ``unknown``; only
    code that deliberately binds the live context is labelled ``live``.
    """
    try:
        return get_current_tenant().tenant_id
    except LookupError:
        return default


class TenantLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.tenant_id = current_tenant_id()
        return True


def _span_processor_base() -> type:
    try:
        from opentelemetry.sdk.trace import SpanProcessor
    except Exception:  # noqa: BLE001 - SDK is optional at runtime
        return object
    return SpanProcessor


class TenantSpanProcessor(_span_processor_base()):  # type: ignore[misc]
    """Stamps ``tenant_id`` on every span, including children of the request span."""

    sdk_backed = _span_processor_base() is not object

    def on_start(self, span: Any, parent_context: Any = None) -> None:  # noqa: ARG002
        try:
            span.set_attribute("tenant_id", current_tenant_id())
        except Exception:  # noqa: BLE001
            logger.debug("tenant span annotation failed", exc_info=True)

    def on_end(self, span: Any) -> None:  # noqa: ARG002
        return None

    def shutdown(self) -> None:
        return None

    def force_flush(self, timeout_millis: int = 30000) -> bool:  # noqa: ARG002
        return True


def annotate_current_span(context: TenantContext) -> None:
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span is not None and span.is_recording():
            span.set_attribute("tenant_id", context.tenant_id)
            span.set_attribute("tenant.mode", "simulation" if context.is_simulation else "live")
    except Exception:  # noqa: BLE001
        logger.debug("tenant span annotation skipped", exc_info=True)


def _install_log_record_factory() -> None:
    """Stamp every record at creation so late-registered exporters also carry the dimension."""
    factory = logging.getLogRecordFactory()
    if getattr(factory, "_ama_tenant_factory", False):
        return

    def tenant_record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = factory(*args, **kwargs)
        if not hasattr(record, "tenant_id"):
            record.tenant_id = current_tenant_id()
        return record

    tenant_record_factory._ama_tenant_factory = True  # type: ignore[attr-defined]
    logging.setLogRecordFactory(tenant_record_factory)


def telemetry_status() -> dict[str, Any]:
    return {key: (list(value) if isinstance(value, list) else value) for key, value in _STATUS.items()}


def configure_tenant_telemetry() -> dict[str, Any]:
    """Wire tenant dimensions into logs and spans, reporting failures instead of swallowing them."""
    errors: list[str] = []

    try:
        _install_log_record_factory()
        tenant_filter = TenantLogFilter()
        root = logging.getLogger()
        for handler in root.handlers:
            if not any(isinstance(existing, TenantLogFilter) for existing in handler.filters):
                handler.addFilter(tenant_filter)
        _STATUS["log_records"] = "healthy"
    except Exception as exc:  # noqa: BLE001
        logger.warning("tenant_log_telemetry_configuration_failed", exc_info=True)
        errors.append(f"log_records: {exc}")
        _STATUS["log_records"] = "unavailable"

    try:
        from opentelemetry import trace

        provider = trace.get_tracer_provider()
        add_processor = getattr(provider, "add_span_processor", None)
        if not callable(add_processor):
            _STATUS["spans"] = "unconfigured"
        else:
            add_processor(TenantSpanProcessor())
            _STATUS["spans"] = "healthy" if TenantSpanProcessor.sdk_backed else "degraded"
            if not TenantSpanProcessor.sdk_backed:
                message = "OpenTelemetry SDK unavailable; span processor is not SDK-backed"
                logger.warning("tenant_span_telemetry_degraded detail=%s", message)
                errors.append(f"spans: {message}")
    except Exception as exc:  # noqa: BLE001
        logger.warning("tenant_span_telemetry_configuration_failed", exc_info=True)
        errors.append(f"spans: {exc}")
        _STATUS["spans"] = "unavailable"

    _STATUS["errors"] = errors
    _STATUS["configured"] = True
    return telemetry_status()
