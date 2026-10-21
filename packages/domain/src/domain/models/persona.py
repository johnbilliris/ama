from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PersonaRole = Literal[
    "incident_commander",
    "operations_officer",
    "planning_officer",
    "liaison_officer",
    "logistics_officer",
    "public_information_officer",
    "field_coordinator",
    "resilience_planner",
    "observer_auditor",
    "executive_leader",
    "risk_manager",
]


class Persona(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    persona_id: str
    display_name: str
    organisation_id: str
    jurisdiction_id: str
    role: PersonaRole
    permissions: list[str] = Field(default_factory=list)
    decision_rights: list[str] = Field(default_factory=list)
    information_needs: list[str] = Field(default_factory=list)
    communication_pathways: list[str] = Field(default_factory=list)
    active_incident_ids: list[str] = Field(default_factory=list)
