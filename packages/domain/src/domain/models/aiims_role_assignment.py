"""AIIMS Role Assignment model — maps agents to AIIMS functional roles per incident.

Supports six AIIMS functions: Control, Intelligence, Planning, Operations,
Logistics, and Public Information. Each agent holds exactly one function per
incident (enforced at service layer).

FRs: FR-013, FR-014, FR-049 | Research: R-005
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

AiimsFunction = Literal[
    "control",
    "intelligence",
    "planning",
    "operations",
    "logistics",
    "public_information",
]

ALL_AIIMS_FUNCTIONS: list[str] = [
    "control",
    "intelligence",
    "planning",
    "operations",
    "logistics",
    "public_information",
]


class AiimsRoleAssignment(BaseModel):
    assignment_id: str
    incident_id: str
    agent_identifier: str
    aiims_function: AiimsFunction
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    assigned_by: str
    unassigned_at: datetime | None = None
    is_active: bool = True
    delegation_source_id: str | None = None
    notes: str = ""

    @model_validator(mode="after")
    def _validate_active_state(self) -> "AiimsRoleAssignment":
        if self.is_active and self.unassigned_at is not None:
            msg = "is_active cannot be True when unassigned_at is set"
            raise ValueError(msg)
        return self
