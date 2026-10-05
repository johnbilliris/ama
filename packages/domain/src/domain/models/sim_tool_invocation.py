"""Record of a Simulation Controller tool invocation (allow-list enforced)."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

ALLOW_LISTED_TOOLS = (
    "seed_scenario",
    "query_sub_agent",
    "draft_warning_sim",
    "summarise_state",
    "pause",
    "resume",
    "stop",
    "list_participants",
)

SubAgent = Literal[
    "monitoring",
    "planning",
    "resource_allocation",
    "communication",
    "evacuation",
    "risk_assessment",
]


class SimToolInvocation(BaseModel):
    id: str
    tenant_id: str
    simulation_id: str
    turn_id: str
    tool_name: Literal[
        "seed_scenario",
        "query_sub_agent",
        "draft_warning_sim",
        "summarise_state",
        "pause",
        "resume",
        "stop",
        "list_participants",
    ]
    arguments: dict[str, object] = Field(default_factory=dict)
    result: dict[str, object] | None = None
    outcome: Literal["ok", "refused", "error", "cancelled-by-stop"]
    sub_agent: SubAgent | None = None
    latency_ms: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    document_type: str = "sim_tool_invocation"
