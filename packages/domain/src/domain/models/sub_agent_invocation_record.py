"""Sub-agent invocation record — per data-model.md §2 (feature 036, FR-060).

Captures every real sub-agent invocation: model deployment, prompt hash
(FR-060), latency, outcome. Lives in Cosmos container
``sub_agent_invocation_records`` partitioned by ``simulation_id``.

Spec-036 amendment-cycle T-T02 (FR-061 / Amendment A)
-----------------------------------------------------
Two AIIMS tagging fields are added per data-model.md §8.7:

* ``aiims_function`` — single primary AIIMS function for deterministic
  ordering by FR-054 lessons-capture.
* ``secondary_aiims_tags`` — up to TWO secondary tags (constitution v1.2.0
  cap, amendment Q→A Q4) describing the sub-agent's cross-functional
  liaisons.

Both are auto-populated from
:data:`packages.domain.src.domain.models.aiims_mapping.AGENT_TO_AIIMS`
when the caller does not supply them, via the :data:`LEGACY_ROLE_TO_SUB_AGENT`
bridge that maps the legacy 6-member kebab-case ``SubAgentRole`` Literal
onto the canonical 9-member PascalCase ``SubAgent`` Literal.
"""

from datetime import datetime
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt, model_validator

from .aiims_mapping import (
    AGENT_TO_AIIMS,
)
from .aiims_mapping import (
    secondary_aiims_tags as _canonical_secondary_tags,
)
from .aiims_role_assignment import AiimsFunction

SubAgentRole = Literal[
    "monitoring",
    "planning",
    "risk-assessment",
    "communication",
    "evacuation",
    "resource-allocation",
]

SubAgentOutcome = Literal[
    "success",
    "timeout",
    "degraded",
    "refused",
    "cancelled",
]


#: Bridge map from the legacy `SubAgentRole` (kebab-case, 6 members) to
#: the canonical spec-036 `SubAgent` Literal (PascalCase, 9 members).
#:
#: Mappings rationale:
#: * ``monitoring`` → ``Intel`` — situational awareness sits with the
#:   AIIMS Intelligence cell.
#: * ``planning`` → ``Planning`` — direct doctrinal mapping.
#: * ``risk-assessment`` → ``Risk`` — direct rename.
#: * ``communication`` → ``Comms`` — direct rename.
#: * ``evacuation`` → ``Evac`` — direct rename.
#: * ``resource-allocation`` → ``Resource`` — direct rename.
#:
#: The 9-member canonical set additionally includes ``Logistics``,
#: ``Health``, and ``Operations`` which have no legacy peer; spec-036
#: invocation records will surface those once the API surface adopts the
#: PascalCase identifiers (out of scope for Wave 2).
LEGACY_ROLE_TO_SUB_AGENT: Final[dict[str, str]] = {
    "monitoring": "Intel",
    "planning": "Planning",
    "risk-assessment": "Risk",
    "communication": "Comms",
    "evacuation": "Evac",
    "resource-allocation": "Resource",
}


class SubAgentInvocationRecord(BaseModel):
    """Append-only record of one sub-agent invocation (FR-002, FR-060)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    invocation_id: str
    simulation_id: str
    tenant_id: str
    agent_role: SubAgentRole
    prompt_hash: str = Field(
        min_length=64,
        max_length=64,
        pattern=r"^[a-f0-9]{64}$",
        description="sha256 hex over canonical LLM prompt (FR-060).",
    )
    model_deployment: str = Field(
        description="Observed deployment, or 'unknown' when unavailable.",
    )
    latency_ms: NonNegativeInt
    outcome: SubAgentOutcome
    started_at: datetime
    ended_at: datetime
    correlation_id: str | None = None
    triggering_signal_id: str | None = None
    origin_cascade_id: str | None = None
    error_code: str | None = None
    model_id: str | None = None
    model_version: str | None = None
    inference_attempted: bool | None = Field(default=None, strict=True)
    inference_outcome: Literal["succeeded", "failed", "not_attempted", "unknown"] | None = None

    # ---- AIIMS tagging (T-T02 / FR-061 / data-model.md §8.7) ---------------
    aiims_function: AiimsFunction | None = Field(
        default=None,
        description=(
            "Single primary AIIMS function (constitution v1.2.0). Auto-derived "
            "from ``agent_role`` via the canonical AGENT_TO_AIIMS table when "
            "not explicitly supplied."
        ),
    )
    secondary_aiims_tags: list[AiimsFunction] = Field(
        default_factory=list,
        max_length=2,
        description=(
            "Secondary AIIMS tags (≤2 per constitution v1.2.0). Auto-derived "
            "from the canonical mapping when not explicitly supplied. Must be "
            "disjoint from ``aiims_function``."
        ),
    )

    document_type: Literal["sub_agent_invocation_record"] = "sub_agent_invocation_record"

    # ----- Auto-population from agent_role -------------------------------------
    #
    # We use ``mode="before"`` so the auto-derived defaults flow through the
    # standard Pydantic validation pipeline (max_length=2, AiimsFunction
    # Literal containment, etc.) — and so frozen=True remains honoured at
    # the *post-validate* boundary.
    @model_validator(mode="before")
    @classmethod
    def _auto_populate_aiims_fields(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        agent_role = data.get("agent_role")
        if not isinstance(agent_role, str):
            return data
        canonical = LEGACY_ROLE_TO_SUB_AGENT.get(agent_role)
        if canonical is None:
            return data
        if data.get("aiims_function") in (None, ""):
            primary = AGENT_TO_AIIMS.get(canonical)
            if primary is not None:
                data["aiims_function"] = primary
        if "secondary_aiims_tags" not in data or data["secondary_aiims_tags"] is None:
            data["secondary_aiims_tags"] = _canonical_secondary_tags(canonical)
        return data

    @model_validator(mode="after")
    def _validate_aiims_disjointness(self) -> "SubAgentInvocationRecord":
        if self.aiims_function is not None and self.aiims_function in self.secondary_aiims_tags:
            raise ValueError(
                f"secondary_aiims_tags {self.secondary_aiims_tags!r} must not "
                f"include the primary aiims_function {self.aiims_function!r} "
                "(constitution v1.2.0 1+≤2 cap requires disjoint sets)."
            )
        return self

    @property
    def partition_key(self) -> str:
        return self.simulation_id


__all__ = [
    "LEGACY_ROLE_TO_SUB_AGENT",
    "SubAgentInvocationRecord",
    "SubAgentOutcome",
    "SubAgentRole",
]
