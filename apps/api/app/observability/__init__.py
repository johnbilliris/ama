"""Observability sub-package for the API.

Provides:
  - ``otel.bootstrap()`` — wires the Azure Monitor OpenTelemetry Distro so
    traces, metrics, and logs flow to Application Insights. Idempotent.
  - ``metrics.emit_*`` — thin instrument wrappers used by call sites.

Spec 032 FR-O07 + FR-O02 + FR-O03.
"""

from __future__ import annotations

from .metrics import emit_counter, emit_gauge, emit_histogram

__all__ = ["emit_counter", "emit_gauge", "emit_histogram", "bootstrap"]


def bootstrap(*, service_name: str = "apps.api", connection_string: str | None = None) -> None:
    """Initialise the Azure Monitor OpenTelemetry Distro.

    Reads ``APPLICATIONINSIGHTS_CONNECTION_STRING`` from the environment when
    ``connection_string`` is None. Safe to call multiple times — subsequent
    calls are no-ops.

    The distro auto-instruments FastAPI, requests, httpx, Azure SDKs.
    """
    import logging
    import os

    logger = logging.getLogger(__name__)

    cs = connection_string or os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not cs:
        logger.info("APPLICATIONINSIGHTS_CONNECTION_STRING not set; OTel bootstrap skipped")
        return

    try:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(
            connection_string=cs,
            disable_offline_storage=False,
            resource_attributes={
                "service.name": service_name,
                "service.namespace": "ama-disaster-response-hub",
                "deployment.environment": os.getenv("AMA_ENVIRONMENT", "dev"),
                "cloud.provider": "azure",
                "cloud.region": os.getenv("AZURE_REGION", "australiaeast"),
            },
        )
        logger.info("Azure Monitor OpenTelemetry Distro initialised for %s", service_name)
    except ImportError:
        logger.warning("azure-monitor-opentelemetry not installed; OTel bootstrap skipped")
    except Exception:  # noqa: BLE001
        logger.exception("OTel bootstrap failed; continuing without telemetry")
