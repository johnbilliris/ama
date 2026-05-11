"""Feature flag registry for the simulation realm (spec 036).

`SIM_CONTROLLER_MODE`:
  - ``stub``       — default. Uses ``default_invoker()`` stub adapters from
                      ``apps/api/app/services/simulation/sub_agent_invoker.py``.
  - ``production`` — uses the real adapters in
                      ``apps/api/app/services/simulation/sub_agents/`` (FR-002).

The flag is read at app startup; per the FR-002 migration plan the stub
adapters are eventually deleted (T-B14) and this module's flag is removed.
"""

from __future__ import annotations

import os
from typing import Final, Literal

ControllerMode = Literal["stub", "production"]

ENV_VAR: Final[str] = "SIM_CONTROLLER_MODE"
DEFAULT_MODE: Final[ControllerMode] = "stub"


def controller_mode() -> ControllerMode:
    """Return the current ``SIM_CONTROLLER_MODE`` value, defaulting to ``stub``.

    Raises ``ValueError`` if the env var holds an unrecognised value so a
    misconfigured deployment fails fast.
    """

    raw = os.environ.get(ENV_VAR, DEFAULT_MODE).strip().lower()
    if raw not in ("stub", "production"):
        raise ValueError(
            f"{ENV_VAR}={raw!r} must be 'stub' or 'production'."
        )
    return raw  # type: ignore[return-value]


def is_production() -> bool:
    return controller_mode() == "production"


__all__ = [
    "DEFAULT_MODE",
    "ENV_VAR",
    "ControllerMode",
    "controller_mode",
    "is_production",
]
