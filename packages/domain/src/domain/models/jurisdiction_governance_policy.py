"""JurisdictionGovernancePolicy domain model (spec-032 FR-AG02, data-model.md E-04).

Distinct from the existing ``JurisdictionPolicy`` (which captures data-residency +
location-precision + cross-agency sharing rules under a ``policy_set_id``). This
model captures the **governance** controls added by spec-032:
  - autonomy_level (low|standard|high) per FR-AG02
  - kill_switch_overrides per agent (FR-AG05)
  - language_priorities for outbound public messaging (FR-V references)
  - aiims_role_overrides (per-jurisdiction agent reassignment, FR-P05)

Stored in Cosmos container ``jurisdiction_governance_policies`` (PK ``/jurisdiction_code``).
Loaded at deploy time from ``infra/parameters/jurisdiction-policies/<code>.yaml``.

Consumers:
  - AutonomyEvaluator (apps/agents/common/lifecycle/autonomy_eval.py)
  - KillSwitchWatcher (per-agent overrides)
  - AiimsRegistry (per-jurisdiction role overrides)
  - Communication agent (language_priorities)
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

JurisdictionCode = Literal[
    "act", "nsw", "vic", "qld", "sa", "wa", "tas", "nt", "commonwealth"
]
GovernanceAutonomyLevel = Literal["low", "standard", "high"]
GovernanceAiimsFunction = Literal[
    "control",
    "intelligence",
    "planning",
    "operations",
    "logistics",
    "public_information",
]


class JurisdictionGovernancePolicy(BaseModel):
    """Declarative governance controls per Australian jurisdiction (spec-032)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    jurisdiction_code: JurisdictionCode
    autonomy_level: GovernanceAutonomyLevel = "standard"
    kill_switch_overrides: dict[str, bool] = Field(default_factory=dict)
    language_priorities: list[str] = Field(default_factory=lambda: ["en-AU"])
    aiims_role_overrides: dict[GovernanceAiimsFunction, str] = Field(default_factory=dict)
    version: int = Field(default=1, ge=1)
    effective_from: datetime
    approved_by: str = Field(min_length=3)

    @field_validator("language_priorities")
    @classmethod
    def _validate_languages(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("language_priorities must contain at least one BCP-47 tag")
        import re

        bcp47 = re.compile(r"^[a-z]{2,3}(-[A-Z][a-zA-Z]{1,7})*(-[A-Z]{2})?$")
        for tag in v:
            if not bcp47.match(tag):
                raise ValueError(f"invalid BCP-47 tag: {tag!r}")
        return v

    def language_for(self, requested: str | None = None) -> str:
        """Best-match language: requested if present, else first priority."""
        if requested and requested in self.language_priorities:
            return requested
        return self.language_priorities[0]

    def kill_switch_engaged_for(self, agent_id: str) -> bool | None:
        """Return per-agent kill-switch override (None = not overridden)."""
        return self.kill_switch_overrides.get(agent_id)
