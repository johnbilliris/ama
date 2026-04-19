from typing import Any, Literal

from pydantic import BaseModel, Field

from packages.domain.src.domain.models.incident import IncidentType, PprrPhase


class OperatingFramework(BaseModel):
    framework_id: str
    name: str
    abbreviation: str | None = None
    description: str = ""
    framework_type: Literal[
        "aiims", "agency_specific", "jurisdictional_policy", "communications", "other"
    ]
    applicable_jurisdiction_ids: list[str] = Field(default_factory=list)
    custodian_organisation_id: str | None = None
    pprr_phases: list[PprrPhase] = Field(default_factory=list)
    hazard_types: list[IncidentType] = Field(default_factory=list)
    principles: list[str] = Field(default_factory=list)
    control_model: str = ""
    approval_rules: list[dict[str, Any]] = Field(default_factory=list)
    escalation_rules: list[dict[str, Any]] = Field(default_factory=list)
    span_of_control_guidance: str = ""
    activation_triggers: list[str] = Field(default_factory=list)
    legislative_basis: str | None = None
    version: str | None = None
    source_uri: str | None = None
    related_framework_ids: list[str] = Field(default_factory=list)
    status: Literal["active", "retired", "draft"] = "active"
