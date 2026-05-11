"""Pydantic v2 envelope for Spec-037 EvidencePackArtefact (T032).

Citations: FR-001, FR-005.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .publication_gate_metadata import PublicationGateMetadata


class EvidencePackArtefact(BaseModel):
    """Cross-artefact envelope.

    Per-artefact row contents validated by the artefact-specific Pydantic models
    (RiskRow, AdoptionWave, KpiRow, RaiRow, FeatureValueRow + TradeoffRow). The
    envelope itself only requires a non-empty `rows` array; consumers downcast
    based on `artefact_id`.
    """

    model_config = ConfigDict(extra="forbid")

    artefact_id: Literal[
        "risk_register",
        "adoption_roadmap",
        "executive_kpi_surface",
        "rai_register",
        "feature_value_ledger",
    ]
    schema_version: str
    publication_id: str  # UUID
    published_at_utc: str
    published_by: str
    metadata: PublicationGateMetadata
    rows: list[dict[str, Any]] = Field(min_length=1)
    superseded_surfaces: list[str] | None = None
    # feature_value_ledger only
    tradeoffs: list[dict[str, Any]] | None = None
