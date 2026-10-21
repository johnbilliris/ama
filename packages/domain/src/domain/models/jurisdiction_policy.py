from pydantic import BaseModel, ConfigDict, Field, model_validator


class JurisdictionPolicy(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    policy_set_id: str
    data_residency_region: str
    allowed_location_precision_meters: int = Field(default=100)
    retention_days: int = Field(default=365, ge=1)
    retention_rules: list[str] = Field(default_factory=list)
    language_requirements: list[str] = Field(default_factory=list)
    cross_agency_sharing_rules: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_region(self) -> "JurisdictionPolicy":
        region = self.data_residency_region.strip().lower()
        if not region:
            raise ValueError("data_residency_region is required")
        if not region.startswith("australia"):
            raise ValueError("data_residency_region must be an Australian Azure region")
        if not self.retention_rules:
            raise ValueError("retention_rules must not be empty")
        return self
