"""Dashboard widget configuration and AIIMS role mapping models.

New domain models for governance dashboard role-based personalisation (021).
"""

from typing import Literal

from pydantic import BaseModel, Field

AIIMSRole = Literal[
    "incident_controller",
    "operations_officer",
    "planning_officer",
    "intelligence_officer",
    "logistics_officer",
    "public_information_officer",
    "executive_leader",
    "observer_auditor",
    "risk_manager",
    "resilience_planner",
    "field_coordinator",
]

AIIMS_AUTHORITY_RANKS: dict[str, int] = {
    "incident_controller": 1,
    "operations_officer": 3,
    "planning_officer": 4,
    "intelligence_officer": 5,
    "logistics_officer": 6,
    "public_information_officer": 7,
    "executive_leader": 2,
    "observer_auditor": 10,
    "risk_manager": 8,
    "resilience_planner": 9,
    "field_coordinator": 11,
}


class WidgetDefinition(BaseModel):
    """A single widget in a dashboard layout."""

    widget_id: str = Field(description="Unique widget identifier, e.g., 'health_score_gauge'")
    widget_type: Literal[
        "gauge",
        "grid",
        "table",
        "chart",
        "indicator",
        "search",
        "timeline",
        "progress_bar",
        "counter",
    ]
    display_name: str
    priority: int = Field(ge=1, description="Display order within the role's layout")
    data_endpoint: str = Field(description="API endpoint that provides data for this widget")
    refresh_group: Literal["active_incident", "steady_state", "manual_only"]


class RoleWidgetMapping(BaseModel):
    """Maps an AIIMS role to its default widget configuration."""

    role: AIIMSRole
    default_view: Literal[
        "executive_summary",
        "compliance",
        "audit_trail",
        "operational_readiness",
        "recovery",
        "risk_warning",
    ]
    widgets: list[WidgetDefinition] = Field(min_length=1)
    authority_rank: int = Field(
        ge=1,
        le=11,
        description="Rank for multi-role ordering: 1=highest authority",
    )
