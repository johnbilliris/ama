from typing import Literal

from pydantic import BaseModel, Field


class Organisation(BaseModel):
    organisation_id: str
    name: str
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
