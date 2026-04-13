"""Program Logic Model — structured resource→activity→output→outcome chains.

Supports both ex ante (planning-stage) and ex post (evaluation-stage) models
with AIDR catalogue linking for activities and outcomes.

FRs: FR-010 | Research: R-005
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

RecoveryDomain = Literal["overarching", "social", "economic", "built", "natural"]
ObjectiveType = Literal["sustainability", "resilience"]


class LogicElement(BaseModel):
    """A single element in the program logic chain."""
    element_id: str
    description: str
    catalogue_activity_id: str | None = None
    domain: RecoveryDomain | None = None


class FinalOutcome(BaseModel):
    """A final outcome distinguishing sustainability vs resilience."""
    element_id: str
    description: str
    catalogue_outcome_id: str | None = None
    objective_type: ObjectiveType
    domain: RecoveryDomain


class OutcomeChainLink(BaseModel):
    """A directed link between two elements in the logic chain."""
    from_element_id: str
    to_element_id: str
    link_type: Literal["produces", "contributes_to", "enables", "depends_on"]


class ProgramLogicModel(BaseModel):
    """Program Logic Model mapping resources → activities → outputs → outcomes.

    FRs: FR-010 | Research: R-005
    """
    model_id: str
    framework_id: str
    model_type: Literal["ex_ante", "ex_post"] = "ex_ante"
    resources_inputs: list[LogicElement] = Field(default_factory=list)
    activities: list[LogicElement] = Field(default_factory=list)
    outputs: list[LogicElement] = Field(default_factory=list)
    intermediate_outcomes: list[LogicElement] = Field(default_factory=list)
    final_outcomes: list[FinalOutcome] = Field(default_factory=list)
    outcome_chain_links: list[OutcomeChainLink] = Field(default_factory=list)
    timeline_months: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def _validate_chain_links(self) -> "ProgramLogicModel":
        all_ids = set()
        for el in self.resources_inputs + self.activities + self.outputs + self.intermediate_outcomes:
            all_ids.add(el.element_id)
        for fo in self.final_outcomes:
            all_ids.add(fo.element_id)
        for link in self.outcome_chain_links:
            if link.from_element_id not in all_ids:
                raise ValueError(f"outcome_chain_links references unknown from_element_id: '{link.from_element_id}'")
            if link.to_element_id not in all_ids:
                raise ValueError(f"outcome_chain_links references unknown to_element_id: '{link.to_element_id}'")
        return self
