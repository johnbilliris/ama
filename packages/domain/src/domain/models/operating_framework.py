from typing import Any, Literal

from pydantic import BaseModel, Field


class OperatingFramework(BaseModel):
    framework_id: str
    name: str
    framework_type: Literal["aiims", "agency_specific", "jurisdictional_policy", "communications", "other"]
    principles: list[str] = Field(default_factory=list)
    control_model: str
    approval_rules: list[dict[str, Any]] = Field(default_factory=list)
    escalation_rules: list[dict[str, Any]] = Field(default_factory=list)
    span_of_control_guidance: str
    status: Literal["active", "retired", "draft"] = "active"
