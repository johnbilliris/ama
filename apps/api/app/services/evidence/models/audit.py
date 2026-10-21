from __future__ import annotations

from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

AuRegion = Literal["australiaeast", "australiasoutheast"]
StorageSource = Literal["hot", "cold", "hot+cold"]

AuditKind = Literal[
    "signal_ingested",
    "model_output_recorded",
    "recommendation_recorded",
    "human_decision_recorded",
    "outcome_recorded",
    "scorecard_published",
    "ladder_version_published",
    "non_au_signal_refused",
    "manual_share_blocked",
    "auditor_signoff_recorded",
    "kpi_amendment_recorded",
    "degraded_mode_entered",
    "small_sample_labelled",
    "divergence_flagged",
    "audit_mutation_attempted",
    "language_fallback_used",
]

CHAIN_REFERENCE_KEYS = (
    "signal_id",
    "model_output_id",
    "recommendation_id",
    "human_decision_id",
    "outcome_id",
)


class AuditEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    audit_id: str = Field(min_length=1, max_length=128)
    value_id: str = Field(min_length=1, max_length=128)
    kind: AuditKind
    actor: str = Field(min_length=1, max_length=256)
    occurred_at: AwareDatetime
    references: dict[str, str] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str = Field(default="", max_length=128)
    region: AuRegion
    payload_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    language_fallback_used: str | None = Field(
        default=None,
        pattern=r"^[A-Za-z_-]+→[A-Za-z-]+$",
    )
    storage_source: StorageSource = "hot"


class AuditTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value_id: str
    entries: list[AuditEntry] = Field(min_length=1)
    chain_complete: bool
    missing_references: list[str] = Field(default_factory=list)
    served_from_cold_archive: bool = False

    @classmethod
    def build(
        cls,
        value_id: str,
        entries: list[AuditEntry],
        *,
        served_from_cold_archive: bool = False,
    ) -> AuditTrace:
        referenced: dict[str, str] = {}
        resolvable_ids = {entry.id for entry in entries} | {entry.value_id for entry in entries}
        for entry in entries:
            referenced.update(entry.references)
        missing = [
            key for key in CHAIN_REFERENCE_KEYS if not referenced.get(key) or referenced[key] not in resolvable_ids
        ]
        return cls(
            value_id=value_id,
            entries=entries,
            chain_complete=not missing,
            missing_references=missing,
            served_from_cold_archive=served_from_cold_archive,
        )
