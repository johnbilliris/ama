"""Pydantic v2 model for Spec-037 TradeoffRow (T030).

Citations: FR-032, FR-036.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ._common import Provenance

_ADR_ID_RE = re.compile(r"^ADR-\d{3}.*$")
_SPEC_ID_RE = re.compile(r"^\d{3}-[a-z0-9-]+$")


class TradeoffRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    adr_id: str
    adr_path: str
    bounding_features: list[str] = Field(min_length=1)
    alternatives_considered: list[str] = Field(min_length=1)
    rationale: str = Field(min_length=1)
    synthesised_tension: Literal[
        "speed-vs-legality",
        "automation-vs-command",
        "local-vs-cross-jurisdiction",
        "visibility-vs-privacy",
        "none",
    ]
    provenance: Provenance

    @field_validator("adr_id")
    @classmethod
    def _adr_id_pattern(cls, v: str) -> str:
        if not _ADR_ID_RE.match(v):
            raise ValueError(f"adr_id must match ADR-NNN-...; got {v!r}")
        return v

    @field_validator("bounding_features")
    @classmethod
    def _features_pattern(cls, v: list[str]) -> list[str]:
        for f in v:
            if not _SPEC_ID_RE.match(f):
                raise ValueError(f"bounding_features entry {f!r} must match NNN-<slug>")
        return v
