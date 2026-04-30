"""Heartbeat / lag emitters used by the lifecycle subsystem.

Currently emits the kill-switch propagation lag; future entries can register
additional heartbeats here (e.g. agent liveness, autonomy snapshot freshness).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def emit_killswitch_lag_seconds(agent_id: str, lag_seconds: float) -> None:
    """Emit ``agent.killswitch.lag_seconds`` (histogram) for SLO-7.

    Telemetry is best-effort: if the App Insights metrics module isn't wired
    yet (Stream 5), the value is logged at INFO and the call returns silently.
    Never raises — call sites are time-sensitive.
    """
    try:
        from apps.api.app.observability.metrics import emit_histogram

        emit_histogram("agent.killswitch.lag_seconds", lag_seconds, {"agent_id": agent_id})
        return
    except Exception:  # noqa: BLE001
        logger.info(
            "agent.killswitch.lag_seconds agent=%s lag_seconds=%.3f (telemetry not wired)",
            agent_id,
            lag_seconds,
        )
