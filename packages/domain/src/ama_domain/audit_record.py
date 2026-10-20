"""Spec 036 — AuditRecord (LLM-call) extended shape (T073).

Pydantic-v2 mirror of
``packages/schemas/spec_036/audit-record-llm-call.json`` (FR-RAG-AG-02,
FR-RAG-SIM-04, R-13). The pre-existing ``audit_records`` Cosmos container is
extended additively with the bold rows from data-model.md §AuditRecord;
this module exposes the canonical shape for both producers (the per-agent
audit writers and the simulation Controller) and consumers (the replay
harness, the KQL completeness check).

Invariants enforced here mirror the schema's ``allOf`` blocks:

* ``rag_used == True`` → ``retrieved_chunks`` non-empty AND ``corpus_build_sha``
  AND ``embedding_model_id`` AND ``citations`` populated.
* ``rag_used == False`` AND ``call_kind == "inference"`` → ``rag_optout_reason``
  AND ``adr_pointer``; ``retrieved_chunks`` empty.
* ``call_kind == "embedding"`` → no ``prompt_sha``, no ``retrieved_chunks``,
  ``rag_used == False``, ``embedding_model_id`` required.
* ``call_kind == "inference"`` → ``prompt_sha`` required.
* ``gateway_decision == "deny"`` → ``gateway_deny_reason`` required.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .citation import Citation
from .retrieval import Jurisdiction, LicenceMode

# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #


_CallKind = Literal["inference", "embedding"]
"""Discriminator (R-13). ``embedding`` calls have no prompt and no retrieved chunks."""


_AgentName = Literal[
    "MonitoringAgent",
    "RiskAssessmentAgent",
    "EvacuationAgent",
    "ResourceAllocationAgent",
    "DependencyNotifierAgent",
    "CommunicationAgent",
    "SimulationController",
    "ObserverAuditor",
]


_GatewayDecision = Literal["allow", "deny", "redact"]
"""Model gateway decision on the prompt + response (FR-RAG-CV-03)."""


_GatewayDenyReason = Literal[
    "pii",
    "pspf-marking",
    "sensitive-operational-content",
    "classification-above-official",
    "carveout-not-registered",
]


_RagOptoutReason = Literal[
    "structured-signal-pipeline",
    "bom-live-feed",
    "ga-live-feed",
    "planning-collection",
    "logistics-transactional",
    "scenario-execution",
    "classified-content",
    "lint-required-marker",
    "observer-auditor-replay",
]
"""Maps 1:1 to FR-RAG-NS-01..09."""


_OperatorAction = Literal["approve", "edit", "dismiss", "escalate"]


_ApprovalWorkflowState = Literal["pending", "approved", "rejected"]
"""F-A5 (Cluster A5; ADR-14) approval state machine values. Transitions:
``pending → approved | rejected`` (terminal). Source of truth:
``apps/api/app/services/approval_workflow.py``."""


_PrecedenceTiebreakTier = Literal["recency", "licence_mode", "embedding_model_id", "chunk_id"]
"""F-A5 (Cluster A3) deterministic tie-break tiers; order pinned by Pass 1
Q-P1-02. Recorded in audit emission via ``apps/agents/common/retrieval_client``."""


# --------------------------------------------------------------------------- #
# Sub-records
# --------------------------------------------------------------------------- #


class RetrievedChunkRef(BaseModel):
    """Compact projection of a ``RetrievedChunk`` for the audit record.

    Required iff ``rag_used == True``; matches the schema's
    ``retrieved_chunks[]`` item shape (without ``text`` / ``summary`` /
    ``rendered_url`` / ``source_url`` — those live on the Citation projection).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    chunk_id: str = Field(..., min_length=1)
    sha256_of_chunk: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    jurisdiction: Jurisdiction
    topic: str = Field(..., min_length=1)
    page: int = Field(..., ge=1)
    licence_mode: Literal[LicenceMode.FULL_TEXT, LicenceMode.METADATA_ONLY]
    confidence: float = Field(..., ge=0.0, le=1.0)


class OperatorAction(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    action: _OperatorAction
    actor_id: str
    timestamp_utc: datetime
    reason: str | None = None


# --------------------------------------------------------------------------- #
# AuditRecord
# --------------------------------------------------------------------------- #


class AuditRecord(BaseModel):
    """Append-only audit record emitted on every LLM call.

    Source of truth for retrieval+inference equivalence replay (SC-011) and
    for FR-RAG-NS-01..09 carve-out enforcement (R-13).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    call_id: str = Field(..., min_length=1)  # UUID; primary key (Cosmos /id)
    timestamp_utc: datetime
    agent_name: _AgentName
    chat_turn_index: int | None = None
    call_kind: _CallKind
    prompt_sha: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    model_id: str = Field(..., min_length=1)
    model_version: str = Field(..., min_length=1)
    deployment_alias: str = Field(..., min_length=1)
    inference_attempted: bool | None = Field(default=None, strict=True)
    inference_outcome: Literal["succeeded", "failed", "not_attempted", "unknown"] | None = None
    embedding_model_id: str | None = None
    corpus_build_sha: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    retrieved_chunks: list[RetrievedChunkRef] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    rag_used: bool
    rag_optout_reason: _RagOptoutReason | None = None
    adr_pointer: str | None = Field(
        default=None,
        pattern=r"^docs/decisions/036-foundry-rag-grounding/0[1-9]-rag-optout-[a-z-]+\.md$",
    )
    gateway_decision: _GatewayDecision
    gateway_deny_reason: _GatewayDenyReason | None = None
    hallucinated_citation_count: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    output_text_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    operator_actions: list[OperatorAction] = Field(default_factory=list)
    tenant_id: str = Field(..., min_length=1)
    correlation_id: str = Field(..., min_length=1)

    # ------------------------------------------------------------------ #
    # F-A5 (Cluster A5; ADR-14) — additive-nullable extension fields.
    # All fields default to None for legacy rows + non-applicable paths.
    # ------------------------------------------------------------------ #
    operator_override_rationale: str | None = Field(default=None, min_length=1, max_length=2048)
    approval_workflow_state: _ApprovalWorkflowState | None = None
    approval_authority: str | None = Field(default=None, min_length=3, max_length=256)
    downgrade_justification: str | None = Field(default=None, min_length=1, max_length=2048)
    retrieval_index_name: str | None = Field(
        default=None,
        pattern=r"^corpus-(v[0-9]+|test-[a-z0-9-]+)$",
    )
    field_coordinator_offline_decision: str | None = Field(default=None, min_length=1, max_length=1024)
    conflict_group_id: str | None = Field(default=None, min_length=1)
    precedence_tiebreak_applied: list[_PrecedenceTiebreakTier] = Field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Invariants (mirror the schema's allOf blocks)
    # ------------------------------------------------------------------ #

    @model_validator(mode="after")
    def _enforce_invariants(self) -> AuditRecord:
        # 1: rag_used == true → retrieved_chunks non-empty AND corpus_build_sha
        #    AND embedding_model_id AND citations.
        if self.rag_used:
            if not self.retrieved_chunks:
                raise ValueError("rag_used=true requires retrieved_chunks[] to be non-empty")
            if not self.corpus_build_sha:
                raise ValueError("rag_used=true requires corpus_build_sha")
            if not self.embedding_model_id:
                raise ValueError("rag_used=true requires embedding_model_id")
            if not self.citations:
                raise ValueError("rag_used=true requires citations[]")
        # 2: rag_used == false AND call_kind == inference →
        #    rag_optout_reason AND adr_pointer required; retrieved_chunks empty.
        if not self.rag_used and self.call_kind == "inference":
            if not self.rag_optout_reason:
                raise ValueError("rag_used=false requires rag_optout_reason for inference calls")
            if not self.adr_pointer:
                raise ValueError("rag_used=false requires adr_pointer for inference calls")
            if self.retrieved_chunks:
                raise ValueError("rag_used=false MUST have empty retrieved_chunks[]")
        # 3: call_kind == embedding → no prompt_sha, no retrieved_chunks,
        #    rag_used=false, embedding_model_id required.
        if self.call_kind == "embedding":
            if self.prompt_sha is not None:
                raise ValueError("call_kind=embedding MUST NOT carry prompt_sha")
            if self.rag_used:
                raise ValueError("call_kind=embedding implies rag_used=false")
            if self.retrieved_chunks:
                raise ValueError("call_kind=embedding MUST have empty retrieved_chunks[]")
            if not self.embedding_model_id:
                raise ValueError("call_kind=embedding requires embedding_model_id")
        # 4: call_kind == inference → prompt_sha required.
        if self.call_kind == "inference" and self.prompt_sha is None:
            raise ValueError("call_kind=inference requires prompt_sha")
        # 5: gateway_decision == deny → gateway_deny_reason required.
        if self.gateway_decision == "deny" and self.gateway_deny_reason is None:
            raise ValueError("gateway_decision=deny requires gateway_deny_reason")
        # 6 (F-A5; ADR-16): rag_used == true → retrieval_index_name required.
        if self.rag_used and not self.retrieval_index_name:
            raise ValueError("rag_used=true requires retrieval_index_name (ADR-16 alias-pinning protocol)")
        # 7 (F-A5; ADR-14): approval_workflow_state ∈ {approved, rejected} →
        # approval_authority required.
        if self.approval_workflow_state in {"approved", "rejected"} and not self.approval_authority:
            raise ValueError("approval_workflow_state in {approved, rejected} requires approval_authority")
        return self


__all__ = [
    "AuditRecord",
    "OperatorAction",
    "RetrievedChunkRef",
]
