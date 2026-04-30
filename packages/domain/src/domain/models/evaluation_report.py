"""Evaluation Report — structured evaluation across 5 KEQ domains.

Supports both manual and AI-assisted report generation with
content safety validation requirement for AI-assisted content.

FRs: FR-014, SC-009 | Research: R-009
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

EvaluationDomain = Literal[
    "governance",
    "community_engagement",
    "effectiveness",
    "efficiency",
    "implementation",
]
RecoveryDomain = Literal["overarching", "social", "economic", "built", "natural"]


class Finding(BaseModel):
    """A single finding within an evaluation domain."""

    finding_text: str
    evidence_summary: str
    severity: Literal["positive", "neutral", "concern", "critical"]
    related_indicator_ids: list[str] = Field(default_factory=list)


class DomainFinding(BaseModel):
    """Findings for a single evaluation domain (KEQ)."""

    evaluation_domain: EvaluationDomain
    questions_addressed: list[str] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    """An actionable recommendation from the evaluation report."""

    text: str
    priority: Literal["high", "medium", "low"]
    target_domain: RecoveryDomain | None = None
    suggested_activity_ids: list[str] = Field(default_factory=list)


class DisseminationRecord(BaseModel):
    """Record of report dissemination to stakeholders."""

    recipient: str
    recipient_type: Literal["government", "community", "ngo", "research"]
    disseminated_at: datetime
    format: Literal["pdf", "json", "presentation"]


class EvaluationReport(BaseModel):
    """Structured evaluation report across 5 KEQ domains.

    FRs: FR-014, SC-009 | Research: R-009
    """

    report_id: str
    framework_id: str
    incident_id: str
    evaluation_period_start: datetime
    evaluation_period_end: datetime
    domain_findings: dict[str, DomainFinding] = Field(default_factory=dict)
    summary: str = ""
    recommendations: list[Recommendation] = Field(default_factory=list)
    dissemination_records: list[DisseminationRecord] = Field(default_factory=list)
    generated_by: Literal["manual", "ai_assisted"] = "manual"
    content_safety_result: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str = ""

    @model_validator(mode="after")
    def _validate_report(self) -> "EvaluationReport":
        if self.evaluation_period_end <= self.evaluation_period_start:
            raise ValueError("evaluation_period_end must be after evaluation_period_start")
        if self.generated_by == "ai_assisted" and not self.content_safety_result:
            raise ValueError("content_safety_result required when generated_by is 'ai_assisted'")
        valid_domains = {"governance", "community_engagement", "effectiveness", "efficiency", "implementation"}
        for key in self.domain_findings:
            if key not in valid_domains:
                raise ValueError(f"Invalid domain_findings key: '{key}'. Must be one of {valid_domains}")
        return self
