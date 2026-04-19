from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

GovernanceAction = Literal[
    "registered",
    "updated",
    "deactivated",
    "assessment_created",
    "assessment_superseded",
    "approved",
    "conditionally_approved",
    "rejected",
    "agent_assigned",
    "agent_revoked",
    "handoff_defined",
    "handoff_updated",
    "handoff_deprecated",
    "rereview_triggered",
    "grace_period_started",
    "grace_period_extended",
    "grace_period_expired",
    "auto_blocked",
    "precedence_set",
    # Dashboard action types (021-governance-dashboard)
    "dashboard_view",
    "dashboard_filter",
    "dashboard_search",
    "dashboard_export",
    "dashboard_drill_down",
    "dashboard_navigate_to_crud",
]


class GovernanceAuditEntry(BaseModel):
    audit_entry_id: str
    data_source_id: str
    action: GovernanceAction
    actor_id: str
    timestamp: datetime
    details: dict[str, Any] = {}
    related_entity_id: str | None = None
    # Dashboard fields (021-governance-dashboard)
    tenant_id: str = "live"
    view_context: str | None = None
    session_id: str | None = None
