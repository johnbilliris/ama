from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PublicAlert(BaseModel):
    alert_id: str
    incident_id: str
    status: Literal["draft", "pending_approval", "approved", "published", "superseded", "cancelled"] = "draft"
    approval_mode: Literal["human_approved", "autonomous", "escalated"] = "human_approved"
    audience_segments: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    accessibility_attributes: list[str] = Field(default_factory=list)
    channel_set: list[str] = Field(default_factory=list)
    content_blocks: dict[str, str] = Field(default_factory=dict)
    published_at: datetime | None = None
    generation_method: Literal["llm", "template", "template_fallback", "safety_fallback"] = "template"
    model_deployment_id: str | None = None
    content_safety_result: Literal["passed", "failed_with_fallback", "not_checked"] = "not_checked"
