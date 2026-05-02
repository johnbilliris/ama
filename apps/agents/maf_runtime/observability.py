"""MAF observability bootstrap (T013).

Wires MAF's OpenTelemetry-first instrumentation through the existing
``azure-monitor-opentelemetry`` exporter (already initialised in
``apps/agents/monitoring/agent.py:15-25``) so every agent invocation, workflow
step, and tool call emits spans/metrics/logs into Application Insights without
per-agent setup code (FR-016, FR-017, SC-004).

Idempotent: calling ``setup_observability_once()`` more than once is a no-op.
Resilient: if Application Insights is unreachable, the agent runtime continues
(per spec edge case "Telemetry pipeline unavailable") — Azure Monitor's
exporter buffers/drops per its own retry policy.
"""

from __future__ import annotations

import logging
import os
from threading import Lock

logger = logging.getLogger(__name__)

_setup_done = False
_setup_lock = Lock()


def setup_observability_once(
    *,
    service_name: str = "ama-agents",
    enable_live_metrics: bool = True,
) -> bool:
    """Initialise OpenTelemetry tracing, metrics, and logging exactly once.

    Returns ``True`` if this call performed setup; ``False`` if a previous call
    already did. Safe to invoke from multiple module-level entry points.
    """
    global _setup_done

    with _setup_lock:
        if _setup_done:
            return False

        connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
        if not connection_string:
            logger.warning(
                "APPLICATIONINSIGHTS_CONNECTION_STRING not set; skipping observability setup. "
                "MAF spans will fall back to the default OTel no-op exporter."
            )
            _setup_done = True
            return True

        # Set the OTel resource attribute so all spans carry a stable service name.
        os.environ.setdefault("OTEL_SERVICE_NAME", service_name)

        try:
            # configure_azure_monitor wires OpenTelemetry's tracer/meter/logger providers
            # to the Azure Monitor exporter using managed identity in production.
            from azure.identity import ManagedIdentityCredential
            from azure.monitor.opentelemetry import configure_azure_monitor

            configure_azure_monitor(
                connection_string=connection_string,
                enable_live_metrics=enable_live_metrics,
                credential=ManagedIdentityCredential(),
            )
        except Exception:  # noqa: BLE001 - per-edge-case: telemetry failure must not crash agent
            # Per spec edge case "Telemetry pipeline (Application Insights) is unavailable":
            # agent execution proceeds; telemetry is buffered or dropped.
            logger.warning(
                "Failed to configure Azure Monitor observability; continuing without remote telemetry.",
                exc_info=True,
            )
            _setup_done = True
            return True

        # MAF's setup_observability hook is the recommended entry point as of SDK 1.2.x;
        # it registers the tracer/meter providers MAF needs to populate ai.agent.* span
        # attributes automatically. Hidden behind a try/except because some SDK builds
        # don't ship the helper and it's optional (Azure Monitor's auto-instrumentation
        # already covers the common cases).
        try:  # pragma: no cover - exercised at runtime only
            from agent_framework.observability import setup_observability  # type: ignore[import-not-found]

            setup_observability()
            logger.info("agent_framework.observability.setup_observability() registered")
        except ImportError:
            logger.info(
                "agent_framework.observability.setup_observability not available in this SDK build; "
                "Azure Monitor auto-instrumentation will cover MAF spans."
            )
        except Exception:  # noqa: BLE001
            logger.warning(
                "agent_framework.observability.setup_observability() raised; ignoring per edge case.",
                exc_info=True,
            )

        _setup_done = True
        return True


__all__ = ["setup_observability_once"]
