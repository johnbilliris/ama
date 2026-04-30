"""Recovery Environment Tracker — tracks post-disaster recovery across four environments.

Four environments: Social, Built, Economic, Natural with 21 AIDR-defined indicators.
Enforces k-anonymity ≥ 10 for sensitive social data (NFR-014).

FRs: FR-032–037 | SCs: SC-005 | Research: R-003, R-008, R-012
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

RecoveryEnvironment = Literal["social", "built", "economic", "natural"]
IndicatorUpdateSource = Literal["manual", "automated", "imported"]
DataClassification = Literal["public", "official", "sensitive"]
RecoveryPrinciple = Literal[
    "understand_context",
    "recognise_complexity",
    "community_led",
    "coordinate_activities",
    "communicate_effectively",
    "build_capacity",
]

# AIDR-defined indicators by environment (SC-005, 21 total)
AIDR_INDICATORS: dict[str, list[str]] = {
    "social": [
        "wealth",
        "employment",
        "amenity",
        "health",
        "social_issues",
        "social_belonging",
        "recreation_leisure",
    ],
    "built": [
        "essential_services",
        "community_infrastructure",
        "transport_networks",
        "property_housing",
        "planning_building_compliance",
    ],
    "economic": [
        "personal_income",
        "business_premises",
        "tourism",
        "workforce_availability",
        "productive_land",
    ],
    "natural": [
        "air_quality",
        "water_quality",
        "land_soil_health",
        "biodiversity",
    ],
}

ALL_INDICATOR_NAMES: list[str] = [name for names in AIDR_INDICATORS.values() for name in names]

# Indicators defaulting to sensitive classification
SENSITIVE_SOCIAL_INDICATORS: set[str] = {"health", "employment"}

ALL_RECOVERY_PRINCIPLES: list[str] = [
    "understand_context",
    "recognise_complexity",
    "community_led",
    "coordinate_activities",
    "communicate_effectively",
    "build_capacity",
]


class RecoveryIndicator(BaseModel):
    indicator_name: str
    environment: RecoveryEnvironment
    value: float | None = None
    unit: str = ""
    baseline_value: float | None = None
    target_value: float | None = None
    last_updated_at: datetime | None = None
    update_source: IndicatorUpdateSource = "manual"
    data_source_id: str | None = None
    population_coverage: int | None = None
    data_classification: DataClassification = "public"
    is_regressed: bool = False
    regression_cause: str | None = None
    linked_alert_id: str | None = None
    catalogue_indicator_id: str | None = None

    @model_validator(mode="after")
    def _validate_k_anonymity(self) -> "RecoveryIndicator":
        """Enforce k-anonymity ≥ 10 for sensitive social data (NFR-014, R-012)."""
        if (
            self.environment == "social"
            and self.data_classification == "sensitive"
            and self.population_coverage is not None
            and self.population_coverage < 10
        ):
            msg = (
                f"population_coverage must be ≥ 10 for sensitive social indicator "
                f"'{self.indicator_name}' (k-anonymity requirement NFR-014)"
            )
            raise ValueError(msg)
        if self.is_regressed and not self.regression_cause:
            msg = "regression_cause is required when is_regressed is True"
            raise ValueError(msg)
        if self.catalogue_indicator_id is not None:
            import re

            _pattern = r"^aidr:(overarching|social|economic|built|natural):[a-z0-9-]+:ind:\d+$"
            if not re.match(_pattern, self.catalogue_indicator_id):
                raise ValueError(
                    f"catalogue_indicator_id must match 'aidr:{{domain}}:{{outcome-slug}}:ind:{{index}}' pattern, "
                    f"got '{self.catalogue_indicator_id}'"
                )
        return self


class RecoveryEnvironmentTracker(BaseModel):
    tracker_id: str
    incident_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
    recovery_principles_applied: list[str] = Field(default_factory=list)
    community_input_summary: str = ""
    indicators: list[RecoveryIndicator] = Field(default_factory=list)
    status: Literal["active", "completed", "suspended"] = "active"

    @model_validator(mode="after")
    def _validate_principles(self) -> "RecoveryEnvironmentTracker":
        for p in self.recovery_principles_applied:
            if p not in ALL_RECOVERY_PRINCIPLES:
                msg = f"Invalid recovery principle: '{p}'. Must be one of {ALL_RECOVERY_PRINCIPLES}"
                raise ValueError(msg)
        return self
