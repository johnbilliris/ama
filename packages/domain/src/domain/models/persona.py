from typing import Literal

from pydantic import BaseModel, Field


class Persona(BaseModel):
    persona_id: str
    display_name: str
    organisation_id: str
    jurisdiction_id: str
    role: Literal[
        "incident_commander",
        "operations_officer",
        "planning_officer",
        "liaison_officer",
        "public_information_officer",
    ]
    permissions: list[str] = Field(default_factory=list)
    active_incident_ids: list[str] = Field(default_factory=list)
