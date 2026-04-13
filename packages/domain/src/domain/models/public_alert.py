from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

WarningTier = Literal["advice", "watch_and_act", "emergency_warning"]
ColourCode = Literal["yellow", "orange", "red"]
HazardIcon = Literal["cyclone", "fire", "flood", "heat", "storm", "other"]

TIER_COLOUR_MAP: dict[str, str] = {
    "advice": "yellow",
    "watch_and_act": "orange",
    "emergency_warning": "red",
}

WARNING_PRINCIPLE_KEYS: list[str] = [
    "life_saving", "empowering", "trusted", "risk_scaled", "timely_targeted",
    "impact_conveying", "action_calling", "clearly_communicated", "accessible",
    "bigger_picture",
]


class PublicAlert(BaseModel):
    alert_id: str
    incident_id: str
    status: Literal[
        "draft", "pending_approval", "approved", "published", "superseded", "cancelled"
    ] = "draft"
    approval_mode: Literal["human_approved", "autonomous", "escalated"] = "human_approved"
    audience_segments: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    accessibility_attributes: list[str] = Field(default_factory=list)
    channel_set: list[str] = Field(default_factory=list)
    content_blocks: dict[str, str] = Field(default_factory=dict)
    published_at: datetime | None = None
    generation_method: Literal[
        "llm", "template", "template_fallback", "safety_fallback"
    ] = "template"
    model_deployment_id: str | None = None
    content_safety_result: Literal["passed", "failed_with_fallback", "not_checked"] = "not_checked"

    # AWS warning fields (FR-001–005, FR-048)
    warning_tier: WarningTier | None = None
    colour_code: ColourCode | None = None
    hazard_icon: HazardIcon | None = None
    action_statement: str | None = None
    superseded_warning_id: str | None = None
    tier_skip_justification: str | None = None
    is_all_clear: bool = False
    warning_principles_checklist: dict[str, bool] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_warning_fields(self) -> "PublicAlert":
        if self.warning_tier is not None:
            expected = TIER_COLOUR_MAP[self.warning_tier]
            if self.colour_code is not None and self.colour_code != expected:
                msg = f"colour_code must be '{expected}' for tier '{self.warning_tier}'"
                raise ValueError(msg)
            # Auto-derive colour from tier
            object.__setattr__(self, "colour_code", expected)
            if not self.action_statement:
                msg = "action_statement is required when warning_tier is set"
                raise ValueError(msg)
        if self.is_all_clear and self.warning_tier is not None:
            msg = "warning_tier must be None for all-clear notifications"
            raise ValueError(msg)
        if self.warning_principles_checklist:
            if set(self.warning_principles_checklist.keys()) != set(WARNING_PRINCIPLE_KEYS):
                msg = f"warning_principles_checklist must have exactly these keys: {WARNING_PRINCIPLE_KEYS}"
                raise ValueError(msg)
        return self
