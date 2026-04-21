from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class BenchmarkTargets(BaseModel):
    time_to_first_recommendation_s: int = Field(default=300, gt=0)
    time_to_alert_s: int = Field(default=600, gt=0)
    coordination_coverage_pct: float = Field(default=80.0, gt=0)


class SignalTimelineEntry(BaseModel):
    offset_seconds: int
    signal_envelope: dict[str, Any]

    @field_validator("offset_seconds")
    @classmethod
    def non_negative_offset(cls, v: int) -> int:
        if v < 0:
            raise ValueError("offset_seconds must be non-negative")
        return v


class SeedOrganisation(BaseModel):
    org_id: str
    name: str
    type: str
    jurisdiction_ids: list[str] = Field(default_factory=list)


class ScenarioTemplate(BaseModel):
    id: str = ""
    template_id: str
    kind: str = "scenario_template"
    scenario_type: Literal[
        "Bushfire", "Flood", "Cyclone", "Severe Storm", "Heatwave",
        "Earthquake", "Tsunami", "Pandemic", "Other", "Cross-jurisdiction",
    ]
    name: str
    description: str = ""
    seed_organisations: list[SeedOrganisation] = Field(default_factory=list)
    seed_jurisdictions: list[str] = Field(default_factory=list)
    seed_framework_ids: list[str] = Field(default_factory=list)
    signal_timeline: list[SignalTimelineEntry] = Field(default_factory=list)
    benchmark_targets: BenchmarkTargets = Field(default_factory=BenchmarkTargets)
    document_type: str = "scenario_template"

    def model_post_init(self, __context: object) -> None:
        if not self.id:
            self.id = self.template_id

    @field_validator("signal_timeline")
    @classmethod
    def timeline_sorted_ascending(cls, v: list[SignalTimelineEntry]) -> list[SignalTimelineEntry]:
        for i in range(1, len(v)):
            if v[i].offset_seconds < v[i - 1].offset_seconds:
                raise ValueError("signal_timeline must be sorted ascending by offset_seconds")
        return v

    @field_validator("benchmark_targets")
    @classmethod
    def positive_benchmarks(cls, v: BenchmarkTargets) -> BenchmarkTargets:
        if v.time_to_first_recommendation_s <= 0:
            raise ValueError("time_to_first_recommendation_s must be positive")
        if v.time_to_alert_s <= 0:
            raise ValueError("time_to_alert_s must be positive")
        if v.coordination_coverage_pct <= 0:
            raise ValueError("coordination_coverage_pct must be positive")
        return v
