from typing import Literal

from pydantic import BaseModel, Field

from packages.domain.src.domain.models.aiims_role_assignment import AiimsFunction
from packages.domain.src.domain.models.incident import IncidentType

WorkforceType = Literal["paid", "volunteer", "mixed"]


class Organisation(BaseModel):
    organisation_id: str
    name: str
    abbreviation: str | None = None
    category: Literal[
        "commonwealth",
        "state",
        "territory",
        "local_government",
        "emergency_service",
        "health",
        "utility",
        "transport",
        "community",
        "volunteer",
        "other",
    ]
    jurisdiction_ids: list[str] = Field(default_factory=list)
    operating_role: str
    authority_level: str
    contact_channels: list[dict[str, str]] = Field(default_factory=list)
    participation_conditions: list[str] = Field(default_factory=list)
    status: Literal["active", "inactive", "planned"] = "active"

    # AIIMS alignment
    aiims_functions: list[AiimsFunction] = Field(default_factory=list)
    lead_agency_for: list[IncidentType] = Field(default_factory=list)

    # Capabilities
    primary_capabilities: list[str] = Field(default_factory=list)
    hazard_types: list[IncidentType] = Field(default_factory=list)
    workforce_type: WorkforceType | None = None

    # Legislation & governance
    legislative_basis: str | None = None

    # Coordination
    mutual_aid_partner_ids: list[str] = Field(default_factory=list)
    activation_triggers: list[str] = Field(default_factory=list)
