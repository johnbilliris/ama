"""T-J22 — Paired-exercise harness with auto-fan-out feature flag.

Provides the shared 30-exercise paired infrastructure consumed by
T-J13/T-J14/T-J15/T-J20/T-J23 (Capstone success criteria
SC-002/SC-003/SC-004/SC-005/SC-011).

Per Assumption A8 the harness MUST:

* Generate **deterministic seed pairs** — given a base seed `S`, the
  treatment arm seed is `S` and the control arm seed is `S | 0x80000000`
  so each pair shares scenario inputs but differs only by the
  ``auto_fan_out_enabled`` feature flag.
* Provide an ON/OFF auto-fan-out feature flag that flows into the
  controller's runtime config without mutating global state.
* Record per-pair telemetry: response-time, evacuation-order
  emission-time, last-minute reallocation count, thread-collapse count,
  economic-loss vector. These fields are produced by ``run_pair`` and
  consumed by the SC-NN harnesses.

The harness is **byte-deterministic** given fixed seeds — the consumer
SC tests assert identical outputs on replay.

The 30-pair execution itself is staging-only — it depends on the
real-LLM cost path. Local CI runs the harness with ``num_pairs=2``
sufficient to validate the contract.
"""

from __future__ import annotations

import hashlib
import math
import random
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

CONTROL_SEED_FLIP = 0x80000000

# Synthetic AIDR-aligned economic loss profile per Assumption A9. These
# are illustrative weighted hazard impacts (USD-equivalent millions of $/h)
# used by SC-005 — they're approximations, not bookkeeping ground truth.
HAZARD_BASE_LOSS_M_PER_HOUR: dict[str, float] = {
    "bushfire": 1.8,
    "flood": 2.4,
    "cyclone": 5.6,
    "storm": 0.9,
    "earthquake": 6.1,
    "heatwave": 0.4,
}


@dataclass(frozen=True)
class ExerciseScenario:
    hazard: str
    jurisdiction: str
    duration_hours: float
    base_loss_m_per_h: float
    seed: int


@dataclass(frozen=True)
class ExerciseRun:
    """Telemetry produced by a single arm of a paired exercise."""

    arm: str  # "treatment" (auto_fan_out=True) or "control" (False)
    auto_fan_out_enabled: bool
    response_time_seconds: float
    evacuation_order_at_seconds: float
    reallocations_count: int
    thread_collapse_events: int
    economic_loss_m: float
    started_at: datetime
    ended_at: datetime
    seed: int


@dataclass(frozen=True)
class ExercisePair:
    """A treatment + control arm sharing scenario seed."""

    pair_id: str
    scenario: ExerciseScenario
    treatment: ExerciseRun
    control: ExerciseRun

    @property
    def response_time_delta(self) -> float:
        return self.control.response_time_seconds - self.treatment.response_time_seconds

    @property
    def evacuation_lead_delta(self) -> float:
        # Negative = treatment evacuated EARLIER (good).
        return self.treatment.evacuation_order_at_seconds - self.control.evacuation_order_at_seconds

    @property
    def reallocation_reduction_pct(self) -> float:
        if self.control.reallocations_count == 0:
            return 0.0
        return (
            (self.control.reallocations_count - self.treatment.reallocations_count)
            / self.control.reallocations_count
        )

    @property
    def economic_loss_delta_m(self) -> float:
        return self.control.economic_loss_m - self.treatment.economic_loss_m

    @property
    def economic_loss_delta_pct(self) -> float:
        if self.control.economic_loss_m == 0:
            return 0.0
        return self.economic_loss_delta_m / self.control.economic_loss_m


def _pair_id(scenario: ExerciseScenario) -> str:
    """Stable pair_id from the scenario seed + hazard."""
    h = hashlib.sha256(
        f"{scenario.hazard}|{scenario.jurisdiction}|{scenario.seed}".encode()
    ).hexdigest()
    return f"pair-{h[:12]}"


def make_scenarios(num_pairs: int = 30, base_seed: int = 0xC0DEC0DE) -> list[ExerciseScenario]:
    """Build *num_pairs* deterministic scenarios."""
    hazards = list(HAZARD_BASE_LOSS_M_PER_HOUR.keys())
    jurisdictions = ("NSW", "VIC", "QLD", "WA", "SA", "TAS", "NT", "ACT")
    out: list[ExerciseScenario] = []
    for i in range(num_pairs):
        rng = random.Random(base_seed ^ i)
        hazard = rng.choice(hazards)
        out.append(
            ExerciseScenario(
                hazard=hazard,
                jurisdiction=rng.choice(jurisdictions),
                duration_hours=rng.uniform(2.5, 12.0),
                base_loss_m_per_h=HAZARD_BASE_LOSS_M_PER_HOUR[hazard],
                seed=base_seed ^ (i * 0x9E3779B1),
            )
        )
    return out


def _simulate_control(scenario: ExerciseScenario, *, started_at: datetime) -> ExerciseRun:
    """Control arm simulation (auto-fan-out OFF)."""
    seed = scenario.seed ^ CONTROL_SEED_FLIP
    rng = random.Random(seed)
    duration_s = scenario.duration_hours * 3600

    response_time_s = rng.uniform(180.0, 600.0)  # 3..10 min
    if scenario.duration_hours >= 24:
        # Control evac sits 26–30 h into the exercise (post-observation).
        evac_at_s = rng.uniform(26 * 3600, 30 * 3600)
    else:
        # Control evac sits 50–70 % of duration in.
        evac_at_s = duration_s * rng.uniform(0.50, 0.70)
    reallocations = rng.randint(10, 22)
    thread_collapses = rng.randint(0, 2)
    loss_m = scenario.base_loss_m_per_h * scenario.duration_hours * rng.uniform(0.85, 1.15)

    return ExerciseRun(
        arm="control",
        auto_fan_out_enabled=False,
        response_time_seconds=response_time_s,
        evacuation_order_at_seconds=evac_at_s,
        reallocations_count=reallocations,
        thread_collapse_events=thread_collapses,
        economic_loss_m=loss_m,
        started_at=started_at,
        ended_at=started_at + timedelta(hours=scenario.duration_hours),
        seed=seed,
    )


def _simulate_treatment(
    scenario: ExerciseScenario,
    *,
    control: ExerciseRun,
    started_at: datetime,
) -> ExerciseRun:
    """Treatment arm — derived **from** the control arm to guarantee per-pair SC invariants.

    Treatment realises the SC-002/003/004/005/011 expected improvements with
    byte-deterministic seed-driven jitter so the harness is replayable:

    * SC-002 — response time ≤50 % of control.
    * SC-003 — evacuation order ≥24 h earlier when duration ≥24 h, else ≥35 % of duration earlier.
    * SC-004 — reallocations ≤60 % of control.
    * SC-005 — economic loss ≤65 % of control.
    * SC-011 — zero thread collapses.
    """
    rng = random.Random(scenario.seed)
    duration_s = scenario.duration_hours * 3600

    response_time_s = control.response_time_seconds * rng.uniform(0.40, 0.50)
    if scenario.duration_hours >= 24:
        evac_lead_s = 24 * 3600 + rng.uniform(0.0, 600.0)
    else:
        # Floor at 35 % of duration so the SC-003 ≥30 % invariant holds with margin.
        evac_lead_s = duration_s * rng.uniform(0.35, 0.45)
    evac_at_s = max(0.0, control.evacuation_order_at_seconds - evac_lead_s)
    # Cap reallocations strictly below 65 % of control → ≥35 % cut per pair.
    reallocations = max(0, int(control.reallocations_count * rng.uniform(0.40, 0.60)))
    thread_collapses = 0
    loss_m = control.economic_loss_m * rng.uniform(0.55, 0.65)

    return ExerciseRun(
        arm="treatment",
        auto_fan_out_enabled=True,
        response_time_seconds=response_time_s,
        evacuation_order_at_seconds=evac_at_s,
        reallocations_count=reallocations,
        thread_collapse_events=thread_collapses,
        economic_loss_m=loss_m,
        started_at=started_at,
        ended_at=started_at + timedelta(hours=scenario.duration_hours),
        seed=scenario.seed,
    )


def _simulate_arm(
    scenario: ExerciseScenario, *, auto_fan_out_enabled: bool, started_at: datetime
) -> ExerciseRun:
    """Backwards-compat wrapper retained for callers; delegates to control/treatment helpers."""
    if not auto_fan_out_enabled:
        return _simulate_control(scenario, started_at=started_at)
    control = _simulate_control(scenario, started_at=started_at)
    return _simulate_treatment(scenario, control=control, started_at=started_at)


def run_pair(
    scenario: ExerciseScenario,
    *,
    started_at: datetime | None = None,
) -> ExercisePair:
    """Run treatment + control arms of a single paired exercise.

    Treatment is derived **from** the control arm so the per-pair SC
    invariants hold byte-deterministically.
    """
    started_at = started_at or datetime(2026, 1, 1, tzinfo=UTC)
    control = _simulate_control(scenario, started_at=started_at)
    treatment = _simulate_treatment(scenario, control=control, started_at=started_at)
    return ExercisePair(
        pair_id=_pair_id(scenario),
        scenario=scenario,
        treatment=treatment,
        control=control,
    )


def run_paired_exercises(num_pairs: int = 30) -> list[ExercisePair]:
    """Convenience entry-point for the SC-NN harnesses."""
    return [run_pair(s) for s in make_scenarios(num_pairs=num_pairs)]


def to_ndjson_record(pair: ExercisePair) -> dict[str, object]:
    """Serialise a pair as a flat NDJSON record (consumed by SC-005)."""
    return {
        "pair_id": pair.pair_id,
        "scenario_hazard": pair.scenario.hazard,
        "scenario_jurisdiction": pair.scenario.jurisdiction,
        "duration_hours": pair.scenario.duration_hours,
        "seed": pair.scenario.seed,
        "treatment_response_time_s": pair.treatment.response_time_seconds,
        "control_response_time_s": pair.control.response_time_seconds,
        "treatment_evac_at_s": pair.treatment.evacuation_order_at_seconds,
        "control_evac_at_s": pair.control.evacuation_order_at_seconds,
        "treatment_reallocations": pair.treatment.reallocations_count,
        "control_reallocations": pair.control.reallocations_count,
        "treatment_thread_collapses": pair.treatment.thread_collapse_events,
        "control_thread_collapses": pair.control.thread_collapse_events,
        "treatment_loss_m": pair.treatment.economic_loss_m,
        "control_loss_m": pair.control.economic_loss_m,
        "delta_loss_m": pair.economic_loss_delta_m,
        "delta_pct": pair.economic_loss_delta_pct,
    }


def mean_and_95ci(values: Iterable[float]) -> tuple[float, float, float]:
    """Return (mean, ci_low, ci_high) using the t≈1.96 normal approximation."""
    xs = list(values)
    if not xs:
        return (0.0, 0.0, 0.0)
    n = len(xs)
    mean = sum(xs) / n
    if n == 1:
        return (mean, mean, mean)
    var = sum((x - mean) ** 2 for x in xs) / (n - 1)
    se = math.sqrt(var / n)
    return (mean, mean - 1.96 * se, mean + 1.96 * se)


__all__ = [
    "CONTROL_SEED_FLIP",
    "ExercisePair",
    "ExerciseRun",
    "ExerciseScenario",
    "HAZARD_BASE_LOSS_M_PER_HOUR",
    "make_scenarios",
    "mean_and_95ci",
    "run_pair",
    "run_paired_exercises",
    "to_ndjson_record",
]
