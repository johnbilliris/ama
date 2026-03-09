from pydantic import BaseModel, Field


class JurisdictionPolicy(BaseModel):
    policy_set_id: str
    data_residency_region: str
    allowed_location_precision_meters: int = Field(default=100)
    language_requirements: list[str] = Field(default_factory=list)
    cross_agency_sharing_rules: list[str] = Field(default_factory=list)
