"""Lifecycle sub-package — startup, heartbeat, kill-switch, autonomy dial, degraded mode.

Spec 032 (FR-A05/Q05). Re-exports legacy ``startup`` + the new modules required by
FR-AG02 (autonomy dial), FR-AG05 (kill-switch), FR-AG05a (governance), and the
existing degraded-mode evaluator.
"""

from __future__ import annotations

from common.startup import start_background_services, stop_background_services

from .autonomy_eval import (
    DEFAULT_AUTONOMY_BY_ENV,
    AutonomyDial,
    AutonomyEvaluator,
    AutonomyLevel,
)
from .heartbeat import emit_killswitch_lag_seconds
from .killswitch import (
    KillSwitchState,
    KillSwitchWatcher,
    is_engaged,
    register_subscriber,
)

__all__ = [
    "start_background_services",
    "stop_background_services",
    # Autonomy
    "AutonomyDial",
    "AutonomyLevel",
    "AutonomyEvaluator",
    "DEFAULT_AUTONOMY_BY_ENV",
    # Kill-switch
    "KillSwitchState",
    "KillSwitchWatcher",
    "is_engaged",
    "register_subscriber",
    # Heartbeat
    "emit_killswitch_lag_seconds",
]
