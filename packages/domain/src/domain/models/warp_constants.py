"""Shared constants and validation for simulation warp speeds.

Feature 026-sim-warp-playback: the simulation clock advances at a
configurable multiplier of wall-clock time. Only a fixed set of
multipliers is allowed so UI controls, scheduler maths and audit
records share an enumerated contract.
"""

from __future__ import annotations

ALLOWED_WARP_SPEEDS: tuple[float, ...] = (1.0, 2.0, 5.0, 10.0, 24.0, 60.0)
PLAYBACK_SPEEDS: tuple[float, ...] = (1.0, 2.0, 5.0, 10.0)
DEFAULT_WARP_SPEED: float = 1.0
DELIVERY_LAG_WARNING_SECONDS: float = 10.0


def validate_warp_speed(speed: float) -> float:
    """Return ``speed`` if it matches one of ``ALLOWED_WARP_SPEEDS``.

    Accepts any numeric type comparable to the allowed set; raises
    ``ValueError`` with a helpful message otherwise.
    """

    try:
        value = float(speed)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"warp_speed must be numeric, got {speed!r}") from exc
    for allowed in ALLOWED_WARP_SPEEDS:
        if abs(value - allowed) < 1e-9:
            return allowed
    raise ValueError(
        f"Invalid warp speed {speed!r}. Allowed values: "
        f"{', '.join(str(int(s)) for s in ALLOWED_WARP_SPEEDS)}"
    )


def validate_playback_speed(speed: float) -> float:
    """Return ``speed`` if it matches one of ``PLAYBACK_SPEEDS``."""

    try:
        value = float(speed)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"playback_speed must be numeric, got {speed!r}") from exc
    for allowed in PLAYBACK_SPEEDS:
        if abs(value - allowed) < 1e-9:
            return allowed
    raise ValueError(
        f"Invalid playback speed {speed!r}. Allowed values: "
        f"{', '.join(str(int(s)) for s in PLAYBACK_SPEEDS)}"
    )
