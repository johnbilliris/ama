from datetime import datetime
from typing import Literal

from pydantic import BaseModel

AgentName = Literal[
    "monitoring", "risk_assessment", "evacuation", "resource_allocation", "communication"
]

AssignmentRole = Literal["primary", "secondary"]

AssignmentStatus = Literal["active", "revoked"]


class AgentGovernanceAssignment(BaseModel):
    assignment_id: str
    data_source_id: str
    agent_name: AgentName
    role: AssignmentRole
    scope_of_responsibility: str
    operational_conditions: list[str] = []
    assigned_by: str
    assigned_at: datetime
    status: AssignmentStatus = "active"
