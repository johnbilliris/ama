"""Pillar C — Replay orchestrator (T-C06)."""

from __future__ import annotations

import hashlib
from typing import Literal


def _seeded_pseudo(seed: str, kpi_id: str, mode: Literal["baseline", "ama_assisted"]) -> float:
    """Deterministic pseudo-random based on (seed, kpi_id, mode).

    Used in lieu of the full spec-026 warp-playback API for prototype dev.
    Returns a stable float per (seed, kpi_id, mode).
    """
    h = hashlib.sha256(f"{seed}|{kpi_id}|{mode}".encode()).digest()
    n = int.from_bytes(h[:8], "big") / 2**64
    return n


CAPSTONE_BASES = {
    "lives_saved_lagging": (50.0, 1.30),
    "response_time_p1": (600.0, 0.55),  # AMA reduces by 45%
    "evac_lead_lagging": (12.0, 2.10),
    "logistics_efficiency": (10.0, 1.40),
    "econ_loss_lagging": (10.0, 1.35),
}


def synthesise_pair(*, seed: str, scenario_id: str, kpi_id: str) -> tuple[float, float]:
    """Return (baseline_value, ama_assisted_value) for a single KPI.

    Deterministic per (seed, scenario_id, kpi_id) so re-runs reproduce.
    """
    base, ama_factor = CAPSTONE_BASES.get(kpi_id, (100.0, 1.10))
    jitter_b = _seeded_pseudo(seed, kpi_id + scenario_id, "baseline") * 0.005
    jitter_a = _seeded_pseudo(seed, kpi_id + scenario_id, "ama_assisted") * 0.005
    baseline = base * (1.0 + jitter_b)
    ama = base * ama_factor * (1.0 + jitter_a)
    return baseline, ama
