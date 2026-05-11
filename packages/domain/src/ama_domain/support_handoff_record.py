"""spec-038 entity — SupportHandoffRecord. FR-023a / FR-023a-AMEND / FR-023b."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ChannelKind = Literal["email", "shared_mailbox", "on_call_rotation", "chat_link"]


class SupportHandoffRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    tenant_id: str
    channel_kind: ChannelKind
    address: str = Field(..., min_length=1)
    business_hours_window: str = "24x7"
    incident_mode_channel: "SupportHandoffRecord | None" = None
    auto_activate_on_nema_level3: bool = True
    manual_override_active: bool = False
    # FR-023b SLA defaults — 4 h routine, 5 min incident.
    sla_routine_business_hours: int = Field(default=4, ge=1)
    sla_incident_minutes: int = Field(default=5, ge=1)
    created_at: datetime
    updated_at: datetime


SupportHandoffRecord.model_rebuild()

__all__ = ["SupportHandoffRecord", "ChannelKind"]
