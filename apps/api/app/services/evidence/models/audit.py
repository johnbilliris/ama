"""Pillar F — Audit Entry + Trace (T-F04, FR-025 / FR-026 / FR-029)."""

from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field

AuRegion = Literal["australiaeast", "australiasoutheast"]

AuditKind = Literal[
    "signal_ingested",
    "scorecard_published",
    "ladder_version_published",
    "non_au_signal_refused",
    "manual_share_blocked",
    "auditor_signoff_recorded",
    "kpi_amendment_recorded",
    "degraded_mode_entered",
    "small_sample_labelled",
    "divergence_flagged",
]

CHAIN_STEPS = ("signal", "model_output", "recommendation", "human_decision", "outcome")


class AuditEntry(BaseModel):
    id: str
    audit_id: str
    value_id: str
    kind: AuditKind
    actor: str
    occurred_at: AwareDatetime
    references: dict[str, str] = Field(default_factory=dict)
    payload: dict = Field(default_factory=dict)
    correlation_id: str = ""
    region: AuRegion
    archived_to_blob: bool = False


class AuditTrace(BaseModel):
    value_id: str
    entries: list[AuditEntry] = Field(min_length=1)
    chain_complete: bool
    served_from_cold_archive: bool = False

    @classmethod
    def build(
        cls,
        value_id: str,
        entries: list[AuditEntry],
        *,
        served_from_cold_archive: bool = False,
    ) -> AuditTrace:
        keys: set[str] = set()
        for e in entries:
            keys.update(e.references.keys())
        chain_complete = all(step in keys for step in CHAIN_STEPS)
        return cls(
            value_id=value_id,
            entries=entries,
            chain_complete=chain_complete,
            served_from_cold_archive=served_from_cold_archive,
        )
