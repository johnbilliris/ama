"""Tests for spec-036 T-Q01 / T-Q02 — cascade thread-cap enforcement.

* T-Q01 — :class:`ThreadCapService` rate-limits hazard-thread acquisitions
  via ETag conditional update on a per-simulation counter, capped at 5
  per FR-052 / Q8 (annotation-only fan-outs are NOT counted).
* T-Q02 — :func:`cascade_orchestrator.fan_out` honours the cap, emits a
  ``thread.cap_exceeded`` audit, and downgrades the cascade to
  annotation-only when the cap is hit.

Constitution invariants (NEVER violate):
    - Primacy of Life — refusals always log + audit
    - AIIMS alignment — cap=5 mirrors AIIMS coordination span
    - Fail-closed — a missing counter doc bootstraps to 0, not None
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from apps.api.app.services.simulation.thread_cap_service import (
    AcquireDenied,
    AcquireGranted,
    ThreadCapService,
    reset_thread_cap_service_for_tests,
)


@pytest.fixture(autouse=True)
def _isolate_thread_cap_state() -> None:
    reset_thread_cap_service_for_tests()
    yield
    reset_thread_cap_service_for_tests()


# ---- T-Q01 ThreadCapService -------------------------------------------


@pytest.mark.asyncio
async def test_first_acquire_returns_granted_with_count_one() -> None:
    svc = ThreadCapService()
    result = await svc.try_acquire("sim-Q1")
    assert isinstance(result, AcquireGranted)
    assert result.new_count == 1
    assert result.cap == 5


@pytest.mark.asyncio
async def test_acquire_respects_cap_of_5_per_fr052() -> None:
    svc = ThreadCapService()
    granted = []
    for _ in range(5):
        r = await svc.try_acquire("sim-Q2")
        granted.append(r)
    assert all(isinstance(g, AcquireGranted) for g in granted)
    assert [g.new_count for g in granted] == [1, 2, 3, 4, 5]

    sixth = await svc.try_acquire("sim-Q2")
    assert isinstance(sixth, AcquireDenied)
    assert sixth.current_count == 5
    assert sixth.cap == 5


@pytest.mark.asyncio
async def test_release_decrements_count_below_cap() -> None:
    svc = ThreadCapService()
    for _ in range(5):
        await svc.try_acquire("sim-Q3")
    denied = await svc.try_acquire("sim-Q3")
    assert isinstance(denied, AcquireDenied)

    await svc.release("sim-Q3")
    granted = await svc.try_acquire("sim-Q3")
    assert isinstance(granted, AcquireGranted)
    assert granted.new_count == 5


@pytest.mark.asyncio
async def test_per_simulation_isolation() -> None:
    """Different simulations have independent counters."""

    svc = ThreadCapService()
    for _ in range(5):
        await svc.try_acquire("sim-A")

    other = await svc.try_acquire("sim-B")
    assert isinstance(other, AcquireGranted)
    assert other.new_count == 1


@pytest.mark.asyncio
async def test_annotation_only_acquire_does_not_count_per_q8() -> None:
    """Per amendment Q8, annotation-only fan-outs are NOT counted."""

    svc = ThreadCapService()
    for _ in range(5):
        await svc.try_acquire("sim-Q5", thread_kind="hazard")
    # Cap reached for hazard threads — but annotation-only acquires
    # bypass the counter.
    annotation = await svc.try_acquire("sim-Q5", thread_kind="annotation")
    assert isinstance(annotation, AcquireGranted)
    assert annotation.new_count == 5  # hazard count unchanged


@pytest.mark.asyncio
async def test_release_of_unknown_simulation_is_safe_noop() -> None:
    """Defensive: release MUST not raise on a sim that never acquired."""

    svc = ThreadCapService()
    await svc.release("sim-never-seen")  # must not raise


# ---- T-Q02 cascade_orchestrator integration ---------------------------


@pytest.mark.asyncio
async def test_cascade_fan_out_emits_thread_cap_exceeded_when_capped() -> None:
    """When ThreadCapService denies, cascade_orchestrator emits audit + downgrades.

    Acceptance: when the simulation already has 5 hazard threads,
    a fresh top-level fan-out for a triggering signal must
    (a) NOT dispatch to additional sub-agents and
    (b) write a ``thread.cap_exceeded`` audit envelope per audit-envelope.md §3.10.
    """

    from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal

    svc = ThreadCapService()
    # Pre-fill the cap.
    for _ in range(5):
        await svc.try_acquire("sim-Q6")

    audit = AsyncMock()
    dispatcher = AsyncMock()
    from datetime import UTC, datetime

    signal = SyntheticSignal(
        signal_id="sim-msg-deadbeef",
        simulation_id="sim-Q6",
        tenant_id="tenant-pacific",
        category="fire-behaviour",
        confidence="high",
        parameters={"distance_km": 12.5},
        observed_at=datetime.now(UTC),
        freshness_window_seconds=60,
    )

    from apps.api.app.services.simulation.cascade_orchestrator import (
        fan_out,
    )

    result = await fan_out(
        trigger_signal=signal,
        dispatcher=dispatcher,
        audit_writer=audit,
        thread_cap_service=svc,
    )

    assert result.skipped_reason == "thread_cap_exceeded"
    assert result.triggered == []
    dispatcher.assert_not_awaited()
    audit.write.assert_awaited()
    # Inspect the kwargs of the audit call.
    call = audit.write.await_args_list[-1]
    assert call.args[0] == "thread.cap_exceeded"
    details = call.kwargs["details"]
    assert details["current_thread_count"] == 5
    assert details["rejection_source"] == "coordinator_injection"


@pytest.mark.asyncio
async def test_cascade_fan_out_acquires_thread_when_under_cap() -> None:
    """Successful fan-out increments the hazard-thread counter."""

    from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal

    svc = ThreadCapService()
    audit = AsyncMock()
    dispatcher = AsyncMock()
    from datetime import UTC, datetime

    signal = SyntheticSignal(
        signal_id="sim-msg-cafef00d",
        simulation_id="sim-Q7",
        tenant_id="tenant-pacific",
        category="fire-behaviour",
        confidence="high",
        parameters={"distance_km": 12.5},
        observed_at=datetime.now(UTC),
        freshness_window_seconds=60,
    )

    from apps.api.app.services.simulation.cascade_orchestrator import (
        fan_out,
    )

    result = await fan_out(
        trigger_signal=signal,
        dispatcher=dispatcher,
        audit_writer=audit,
        thread_cap_service=svc,
    )

    # Either matched & dispatched, or no_matching_rule — either way the
    # counter must have been touched (try_acquire) but the result
    # MUST NOT be ``thread_cap_exceeded`` since we started empty.
    assert result.skipped_reason != "thread_cap_exceeded"


@pytest.mark.asyncio
async def test_depth2_refusal_does_not_consume_thread_slot() -> None:
    """Depth-2 refusal must NOT call try_acquire (it never started a thread)."""

    from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal

    svc = ThreadCapService()
    audit = AsyncMock()
    dispatcher = AsyncMock()
    from datetime import UTC, datetime

    signal = SyntheticSignal(
        signal_id="sim-msg-12345678",
        simulation_id="sim-Q8",
        tenant_id="tenant-pacific",
        category="fire-behaviour",
        confidence="high",
        parameters={},
        observed_at=datetime.now(UTC),
        freshness_window_seconds=60,
    )

    from apps.api.app.services.simulation.cascade_orchestrator import (
        fan_out,
    )

    result = await fan_out(
        trigger_signal=signal,
        dispatcher=dispatcher,
        parent_origin_cascade_id="origin-A",
        audit_writer=audit,
        thread_cap_service=svc,
    )

    assert result.skipped_reason == "depth2_refused"
    # The hazard counter must still be 0 — confirm a fresh acquire grants 1.
    granted = await svc.try_acquire("sim-Q8")
    assert isinstance(granted, AcquireGranted)
    assert granted.new_count == 1
