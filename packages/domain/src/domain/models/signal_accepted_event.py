from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SignalAcceptedEvent(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    event_type: Literal["SignalAccepted"] = "SignalAccepted"
    tenant_id: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    signal_id: str = Field(min_length=1)
    data_source_id: str = Field(min_length=1)
    jurisdiction_id: str | None = None
    correlation_id: str = Field(min_length=1)
    incident_id: str | None = None
    derived_source_kind: Literal["authoritative", "sensor", "iot", "field_report", "social", "community", "derived"]
    derived_trust_tier: Literal[
        "tier_1_authoritative_government",
        "tier_2_verified_institutional",
        "tier_3_operational_sensor",
        "tier_4_field_reports",
        "tier_5_community_volunteer",
        "tier_6_social_unverified",
        "tier_7_derived_computed",
    ]
    validation_status: Literal["pending", "validated", "contradicted", "rejected", "escalated"]
    evaluated_confidence_score: float = Field(ge=0.0, le=1.0)
