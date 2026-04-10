from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class SignalSummary(BaseModel):
    total: int = 0
    by_category: dict[str, int] = Field(default_factory=dict)
    by_source: dict[str, int] = Field(default_factory=dict)


class RecommendationSummary(BaseModel):
    total: int = 0
    approved: int = 0
    rejected: int = 0
    pending: int = 0


class AlertSummary(BaseModel):
    total: int = 0
    published: int = 0
    blocked_simulation: int = 0


class PerformanceMetrics(BaseModel):
    time_to_first_recommendation_s: float | None = None
    time_to_alert_publication_s: float | None = None
    coordination_coverage_pct: float | None = None


class BenchmarkComparison(BaseModel):
    metric: str
    target: float
    actual: float | None = None
    passed: bool = False


class ExerciseReport(BaseModel):
    id: str = ""
    report_id: str
    tenant_id: str
    scenario_run_id: str
    scenario_type: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    exercise_timeline: list[dict[str, Any]] = Field(default_factory=list)
    participating_organisations: list[str] = Field(default_factory=list)
    participating_personas: list[str] = Field(default_factory=list)
    signal_summary: SignalSummary = Field(default_factory=SignalSummary)
    recommendation_summary: RecommendationSummary = Field(default_factory=RecommendationSummary)
    alert_summary: AlertSummary = Field(default_factory=AlertSummary)
    coordination_gaps: list[str] = Field(default_factory=list)
    performance_metrics: PerformanceMetrics = Field(default_factory=PerformanceMetrics)
    benchmark_comparison: list[BenchmarkComparison] = Field(default_factory=list)
    document_type: str = "exercise_report"

    def model_post_init(self, __context: object) -> None:
        if not self.id:
            self.id = self.report_id
