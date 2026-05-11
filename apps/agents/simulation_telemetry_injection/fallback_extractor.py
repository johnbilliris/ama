"""Deterministic fallback regex extractor (T-C05 / FR-016)."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal

DEFAULT_FRESHNESS_BY_CATEGORY: dict[str, int] = {
    "weather": 300,
    "fire-behaviour": 300,
    "hydrology": 600,
    "geohazard": 300,
    "utility": 900,
    "transport": 900,
    "evacuation": 600,
    # T-AA04 / I3 / FR-013 — resource freshness tightened from 1800s
    # (30 minutes) to 600s (10 minutes); cohort review flagged that
    # half-hour-stale resource signals were too coarse for tactical
    # decisions in fast-moving incidents.
    "resource": 600,
    "comms-channel-state": 600,
}

_KEYWORD_TO_CATEGORY: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(temp|temperature|hot|heat|fire weather)\b", re.I), "weather"),
    (re.compile(r"\b(rain|wind|storm|cyclone|hail|forecast)\b", re.I), "weather"),
    (re.compile(r"\b(spotting|flame height|ember|fire (front|spread))\b", re.I), "fire-behaviour"),
    (re.compile(r"\b(river|flood|gauge|water level|catchment)\b", re.I), "hydrology"),
    (re.compile(r"\b(earthquake|seismic|landslide|magnitude)\b", re.I), "geohazard"),
    (re.compile(r"\b(power|outage|blackout|grid|substation)\b", re.I), "utility"),
    (re.compile(r"\b(road closed|highway|traffic|rail)\b", re.I), "transport"),
    (re.compile(r"\b(evacuat\w*|shelter\w*|relocate\w*)\b", re.I), "evacuation"),
    (re.compile(r"\b(crew|tanker|engine|asset|deploy|resource)\b", re.I), "resource"),
    (re.compile(r"\b(comms|radio|repeater|channel)\b", re.I), "comms-channel-state"),
]


def extract(*, prompt: str, simulation_id: str, tenant_id: str) -> SyntheticSignal | None:
    """Map *prompt* to a :class:`SyntheticSignal` or ``None`` if no rule fires."""
    if not prompt or not prompt.strip():
        return None
    for pattern, category in _KEYWORD_TO_CATEGORY:
        if pattern.search(prompt):
            return SyntheticSignal(
                signal_id=str(uuid4()),
                simulation_id=simulation_id,
                tenant_id=tenant_id,
                category=category,  # type: ignore[arg-type]
                parameters={"raw_text": prompt[:500], "extracted_via": "fallback_regex"},
                observed_at=datetime.now(UTC),
                freshness_window_seconds=DEFAULT_FRESHNESS_BY_CATEGORY[category],
                confidence="low",
            )
    return None
