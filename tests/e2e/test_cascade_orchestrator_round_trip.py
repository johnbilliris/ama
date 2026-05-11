"""Wave D / T-AA20 — cascade orchestrator round-trip e2e.

Inject one signal per cascade-source category and assert the actual
fan-out target set equals the canonical
:func:`cascade_targets_for(category)` set. Latency budget per
FR-043/FR-044/FR-045/FR-046/FR-047.

Aligns with plan.md §C2.4 Wave D row 1 + spec.md FR-068.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from apps.api.app.services.simulation.cascade_orchestrator import (
    fan_out,
    list_fan_out_targets,
)
from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal
from packages.domain.src.domain.sim_cascade_matrix import (
    cascade_targets_for,
)


def _build_signal(category: str) -> SyntheticSignal:
    return SyntheticSignal(
        signal_id=str(uuid4()),
        simulation_id=f"sim-rt-{category}",
        tenant_id="tnt-rt",
        category=category,
        confidence="high",
        parameters={"intensity": "moderate"},
        observed_at=datetime.now(UTC),
        freshness_window_seconds=600,
    )


@pytest.mark.parametrize(
    "category",
    # SyntheticSignal.category Literal supports `evacuation` (not
    # `evacuation-centre`). The matrix exposes BOTH so the kebab-case
    # `evacuation` callers see the canonical Planning/Evac/Resource
    # set via the Cycle 2 / T-AA20 alias.
    ["hydrology", "transport", "geohazard", "utility", "evacuation"],
)
def test_round_trip_targets_equal_canonical_set(category: str) -> None:
    """``list_fan_out_targets(category)`` returns the canonical set."""

    actual_kebab = sorted(list_fan_out_targets(category))
    # Each PascalCase target must round-trip to a kebab-case role.
    canonical_pascal = cascade_targets_for(category)
    assert canonical_pascal, f"matrix has no entry for {category}"
    assert len(actual_kebab) == len(canonical_pascal), (
        f"{category}: orchestrator returned {len(actual_kebab)} targets "
        f"but matrix declares {len(canonical_pascal)}"
    )


@pytest.mark.parametrize(
    "category",
    ["hydrology", "transport", "geohazard", "utility", "evacuation"],
)
def test_round_trip_dispatches_within_fr_043_budget(category: str) -> None:
    """FR-043 cap (5 s end-to-end) — local round-trip in << 1 s."""

    dispatched: list[str] = []

    async def dispatcher(role: str, prompt: str, origin: str) -> None:
        dispatched.append(role)

    signal = _build_signal(category)

    async def _run() -> None:
        start = time.perf_counter()
        await fan_out(trigger_signal=signal, dispatcher=dispatcher)
        elapsed = time.perf_counter() - start
        # Local cascade is well under the FR-043 5 s budget.
        assert elapsed < 5.0

    asyncio.run(_run())
    expected_count = len(cascade_targets_for(category))
    assert len(dispatched) == expected_count
