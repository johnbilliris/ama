from datetime import datetime
from typing import Literal

from pydantic import BaseModel

SignalCategory = Literal[
    "weather",
    "hydrology",
    "fire",
    "geohazard",
    "infrastructure",
    "community_report",
    "social_report",
    "resource_status",
    "recovery_assessment",
    "lessons_capture",
]

ChainStatus = Literal["active", "draft", "deprecated"]


class HandoffStep(BaseModel):
    step_order: int
    source_agent: str
    target_agent: str
    confidence_threshold: float | None = None
    category_filter: list[SignalCategory] = []
    payload_contract_ref: str | None = None


class HandoffChainDefinition(BaseModel):
    chain_id: str
    data_source_id: str
    steps: list[HandoffStep]
    created_by: str
    created_at: datetime
    updated_at: datetime | None = None
    status: ChainStatus = "active"
