"""Recovery Outcome — AIDR catalogue models for outcomes, activities, and indicators.

Hierarchical ID scheme: aidr:{domain}:{outcome-slug}[:act|:ind:{index}]
Immutable reference data seeded at deployment (~561 documents total).

FRs: FR-015–024 | Research: R-004
"""

import re
from typing import Literal

from pydantic import BaseModel, Field, model_validator

RecoveryDomain = Literal["overarching", "social", "economic", "built", "natural"]
ObjectiveType = Literal["sustainability", "resilience"]

CATALOGUE_OUTCOME_ID_PATTERN = re.compile(r"^aidr:(overarching|social|economic|built|natural):[a-z0-9-]+$")
CATALOGUE_ACTIVITY_ID_PATTERN = re.compile(r"^aidr:(overarching|social|economic|built|natural):[a-z0-9-]+:act:\d+$")
CATALOGUE_INDICATOR_ID_PATTERN = re.compile(r"^aidr:(overarching|social|economic|built|natural):[a-z0-9-]+:ind:\d+$")


class RecoveryOutcome(BaseModel):
    """An AIDR nationally-agreed recovery outcome.

    FRs: FR-015–019 | Research: R-004
    """
    outcome_id: str
    domain: RecoveryDomain
    objective_type: ObjectiveType
    title: str
    description: str = ""
    activity_ids: list[str] = Field(default_factory=list)
    indicator_ids: list[str] = Field(default_factory=list)
    has_developed_activities: bool = True

    @model_validator(mode="after")
    def _validate_ids(self) -> "RecoveryOutcome":
        if not CATALOGUE_OUTCOME_ID_PATTERN.match(self.outcome_id):
            raise ValueError(f"outcome_id must match 'aidr:{{domain}}:{{slug}}', got '{self.outcome_id}'")
        return self


class CatalogueActivity(BaseModel):
    """An AIDR catalogue activity associated with a recovery outcome.

    FRs: FR-020 | Research: R-004
    """
    activity_id: str
    outcome_id: str
    domain: RecoveryDomain
    title: str
    description: str = ""

    @model_validator(mode="after")
    def _validate_ids(self) -> "CatalogueActivity":
        if not CATALOGUE_ACTIVITY_ID_PATTERN.match(self.activity_id):
            raise ValueError(f"activity_id must match 'aidr:{{domain}}:{{slug}}:act:{{n}}', got '{self.activity_id}'")
        return self


class CatalogueIndicator(BaseModel):
    """An AIDR catalogue indicator for measuring outcome progress.

    FRs: FR-021 | Research: R-004
    """
    indicator_id: str
    outcome_id: str
    domain: RecoveryDomain
    title: str
    description: str = ""
    data_collection_methodology: str | None = None
    indicator_type: Literal["quantitative", "qualitative", "both"] = "quantitative"

    @model_validator(mode="after")
    def _validate_ids(self) -> "CatalogueIndicator":
        if not CATALOGUE_INDICATOR_ID_PATTERN.match(self.indicator_id):
            raise ValueError(f"indicator_id must match 'aidr:{{domain}}:{{slug}}:ind:{{n}}', got '{self.indicator_id}'")
        return self
