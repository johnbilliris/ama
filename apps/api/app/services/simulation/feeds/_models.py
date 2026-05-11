"""Spec-039 T019: Pydantic v2 models aligned with data-model.md.

Three models:

  * ``CanonicalRecord`` — the simulator NDJSON envelope (mirror of the
    JSON Schema in ``simulator_feed.schema.json``; the schema is the
    contract, this model is the runtime convenience).
  * ``FeedParams`` — chaos-engineering knobs per feed (drop_rate,
    latency_jitter_us, malform_rate). Bounded so that misconfiguration
    cannot accidentally produce wall-clock-shaped output.
  * ``ScenarioDefinition`` — a named scenario binding feeds to a default
    seed and start time.
"""

from __future__ import annotations

import re
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

KEBAB_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{1,127}$")
SHAPE_RE = re.compile(r"^[a-z0-9_.-]+\.v\d+$")
HEX32_RE = re.compile(r"^[0-9a-f]{32}$")
ISO_US_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$")


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CanonicalRecord(_Base):
    """Mirror of SimulatorRecord in simulator_feed.schema.json."""

    simulated: Literal[True]
    fictitious: Literal[True]
    residency: Literal["AU"]
    scenario_id: str
    seed: int = Field(ge=0, le=(1 << 64) - 1)
    source_shape: str
    timestamp: str
    feed_version: str
    correlation_id: str
    body: dict[str, Any]

    @field_validator("scenario_id")
    @classmethod
    def _kebab(cls, v: str) -> str:
        if not KEBAB_RE.match(v):
            raise ValueError(f"scenario_id must match {KEBAB_RE.pattern}")
        return v

    @field_validator("source_shape")
    @classmethod
    def _shape(cls, v: str) -> str:
        if not SHAPE_RE.match(v):
            raise ValueError(f"source_shape must match {SHAPE_RE.pattern}")
        return v

    @field_validator("feed_version")
    @classmethod
    def _feed_version(cls, v: str) -> str:
        if not re.match(r"^v\d+$", v):
            raise ValueError("feed_version must match ^v\\d+$")
        return v

    @field_validator("correlation_id")
    @classmethod
    def _cid(cls, v: str) -> str:
        if not HEX32_RE.match(v):
            raise ValueError("correlation_id must be 32 lowercase hex chars")
        return v

    @field_validator("timestamp")
    @classmethod
    def _ts(cls, v: str) -> str:
        if not ISO_US_RE.match(v):
            raise ValueError("timestamp must be ISO-8601 UTC with µs precision and Z suffix")
        return v


# Bounded chaos params — see plan §"chaos-engineer".
ProbabilityFloat = Annotated[float, Field(ge=0.0, le=1.0)]
LatencyMicros = Annotated[int, Field(ge=0, le=10_000_000)]


class FeedParams(_Base):
    """Per-feed chaos knobs."""

    drop_rate: ProbabilityFloat = 0.0
    latency_jitter_us: LatencyMicros = 0
    malform_rate: ProbabilityFloat = 0.0


class ScenarioDefinition(_Base):
    """Named scenario binding feeds to defaults."""

    scenario_id: str
    default_seed: int = Field(ge=0, le=(1 << 64) - 1)
    start_iso: str
    participating_feeds: tuple[str, ...]
    participating_personas: tuple[str, ...] = ()
    feed_params: dict[str, FeedParams] = Field(default_factory=dict)

    @field_validator("scenario_id")
    @classmethod
    def _kebab_sid(cls, v: str) -> str:
        if not KEBAB_RE.match(v):
            raise ValueError("scenario_id must be kebab-case")
        return v

    @field_validator("participating_feeds")
    @classmethod
    def _feeds_are_shapes(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        for f in v:
            if not SHAPE_RE.match(f):
                raise ValueError(f"participating feed {f!r} must match shape pattern")
        if not v:
            raise ValueError("participating_feeds must be non-empty")
        return v


__all__ = ["CanonicalRecord", "FeedParams", "ScenarioDefinition"]
