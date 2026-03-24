from datetime import datetime

from pydantic import BaseModel

from packages.domain.src.domain.models.handoff_chain import SignalCategory


class FunctionalDomainPrecedence(BaseModel):
    precedence_id: str
    hazard_type: SignalCategory
    jurisdiction_id: str | None = None
    primary_data_source_id: str
    rationale: str
    created_by: str
    created_at: datetime
