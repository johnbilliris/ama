from datetime import datetime
from typing import Literal

from pydantic import BaseModel, model_validator

TrustTier = Literal[
    "tier_1_authoritative_government",
    "tier_2_verified_institutional",
    "tier_3_operational_sensor",
    "tier_4_field_reports",
    "tier_5_community_volunteer",
    "tier_6_social_unverified",
    "tier_7_derived_computed",
]

TRUST_TIER_TO_RANK: dict[str, int] = {
    "tier_1_authoritative_government": 1,
    "tier_2_verified_institutional": 2,
    "tier_3_operational_sensor": 3,
    "tier_4_field_reports": 4,
    "tier_5_community_volunteer": 5,
    "tier_6_social_unverified": 6,
    "tier_7_derived_computed": 7,
}

DataSourceKind = Literal[
    "authoritative", "sensor", "iot", "field_report", "social", "community", "derived"
]

ComplianceStatus = Literal[
    "unassessed", "compliant", "partially_compliant", "non_compliant", "compliance_lapsed"
]

GovernanceStatus = Literal["unassigned", "assigned", "fully_governed"]

DataSourceStatus = Literal["available", "degraded", "offline", "deactivated"]


class DataSource(BaseModel):
    data_source_id: str
    name: str
    kind: DataSourceKind
    sub_category: str = ""
    provider: str = ""
    collection_method: str = ""
    data_type: str = ""
    update_frequency: str = ""
    geographic_coverage: str = ""
    trust_tier: TrustTier = "tier_7_derived_computed"
    authority_rank: int = 0
    status: DataSourceStatus = "available"
    compliance_status: ComplianceStatus = "unassessed"
    governance_status: GovernanceStatus = "unassigned"
    grace_period_start: datetime | None = None
    grace_period_end: datetime | None = None
    deactivated_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def sync_authority_rank(self) -> "DataSource":
        self.authority_rank = TRUST_TIER_TO_RANK.get(self.trust_tier, 0)
        return self
