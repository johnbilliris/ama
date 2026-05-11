"""Degraded-mode signal handlers (T-C13 / FR-053 / Constitution NN-5)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal

DegradedMode = Literal["comms-blackout", "sub-agent-unavailable", "network-partition"]


def make_degraded_mode_signal(
    *,
    mode: DegradedMode,
    simulation_id: str,
    tenant_id: str,
    affected_resource: str,
) -> SyntheticSignal:
    """Build a typed degraded-mode signal.

    The signal's ``category`` is always ``comms-channel-state`` (the only
    spec-008 category broad enough to encode all three degraded modes); the
    ``parameters.mode`` discriminator carries the actual degraded type so
    downstream handlers can dispatch.
    """
    return SyntheticSignal(
        signal_id=str(uuid4()),
        simulation_id=simulation_id,
        tenant_id=tenant_id,
        category="comms-channel-state",
        parameters={
            "mode": mode,
            "affected_resource": affected_resource,
            "is_degraded_mode_signal": True,
        },
        observed_at=datetime.now(UTC),
        freshness_window_seconds=600,
        confidence="high",
    )
