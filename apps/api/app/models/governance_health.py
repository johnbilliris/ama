"""API response models for the governance dashboard.

View models constructed by the aggregation service — not persisted to Cosmos DB.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from packages.domain.src.domain.models.dashboard_widget_config import WidgetDefinition
from packages.domain.src.domain.models.governance_health_score import (
    ConstitutionalGateStatus,
    GovernanceHealthScore,
)

# --- Executive Summary ---


class ExecutiveSummaryResponse(BaseModel):
    """Response for GET /governance/dashboard/summary."""

    health_score: GovernanceHealthScore
    constitutional_gates: list[ConstitutionalGateStatus] = Field(min_length=10, max_length=10)
    active_incident_count: int = Field(ge=0)
    resource_utilisation_pct: float = Field(ge=0.0, le=100.0)
    risk_summary: dict[str, int]
    data_freshness: datetime
    tenant_id: str


# --- Compliance Matrix ---


class ComplianceMatrixEntry(BaseModel):
    """A row in the compliance matrix."""

    data_source_id: str
    data_source_name: str
    compliance_status: Literal["compliant", "non_compliant", "pending", "grace_period"]
    last_assessment_date: datetime | None = None
    next_assessment_due_date: datetime | None = None
    governance_gap_count: int = Field(ge=0)
    grace_period_expiry: datetime | None = None
    grace_period_reason: str | None = None
    grace_period_countdown_days: int | None = None
    category: str | None = None
    data_source_type: str | None = None
    degraded: bool = False


class ComplianceMatrixResponse(BaseModel):
    """Response for GET /governance/dashboard/compliance."""

    entries: list[ComplianceMatrixEntry]
    total_count: int
    filters_applied: dict
    continuation_token: str | None = None
    page_size: int = Field(default=50)


class ComplianceDetailResponse(BaseModel):
    """Response for GET /governance/dashboard/compliance/{dataSourceId}."""

    data_source_id: str
    data_source_name: str
    compliance_status: str
    assessment_history: list[dict]
    remediation_actions: list[dict]
    related_audit_urls: list[str] = Field(default_factory=list)


# --- Audit Trail ---


class AuditEventSummary(BaseModel):
    """Summary row in the audit trail list."""

    id: str
    timestamp: datetime
    actor: str
    action_type: str
    affected_entity: str
    outcome: str
    provenance_reference: str | None = None
    has_decision_chain: bool = False


class DecisionChainStep(BaseModel):
    """A step in a decision chain."""

    step_order: int
    event_type: Literal["trigger", "approval", "action", "notification"]
    actor: str
    timestamp: datetime
    description: str
    rationale: str | None = None
    evidence_integrity: Literal["verified", "unverified", "pending"]


class AuditDecisionChainResponse(BaseModel):
    """Response for GET /governance/dashboard/audit/{event_id}/chain."""

    event_id: str
    chain: list[DecisionChainStep]
    chain_complete: bool = Field(description="True if chain has trigger + final action")


class AuditTrailResponse(BaseModel):
    """Response for GET /governance/dashboard/audit."""

    events: list[AuditEventSummary]
    total_count: int
    filters_applied: dict
    continuation_token: str | None = None
    page_size: int = Field(default=50)


# --- Operational Readiness ---


class PPRRPhaseStatus(BaseModel):
    """Status of a single PPRR phase."""

    phase: Literal["prevention", "preparedness", "response", "recovery"]
    is_active: bool
    indicator_status: Literal["active", "inactive", "elevated"]


class EmergencyPlanSummary(BaseModel):
    """Emergency plan counts by lifecycle status."""

    lifecycle_state: Literal[
        "Draft",
        "InConsultation",
        "UnderReview",
        "Endorsed",
        "Activated",
        "PostEventReview",
        "Superseded",
    ]
    count: int = Field(ge=0)
    overdue_count: int = Field(ge=0, description="Plans in this state with expired review date")


class AIIMSRoleCoverage(BaseModel):
    """Coverage status for a single AIIMS role."""

    role: str
    assigned_count: int = Field(ge=0)
    required_count: int = Field(ge=1)
    is_staffed: bool
    coverage_pct: float = Field(ge=0.0, le=100.0)


class VolunteerReadiness(BaseModel):
    """Volunteer workforce readiness metrics."""

    total_registered: int = Field(ge=0)
    currently_available: int = Field(ge=0)
    active_deployed: int = Field(ge=0)
    availability_rate_pct: float = Field(ge=0.0, le=100.0)
    welfare_check_compliance_pct: float = Field(ge=0.0, le=100.0)


class CapabilityGap(BaseModel):
    """A single identified capability gap."""

    gap_type: str
    description: str
    severity: Literal["critical", "high", "medium", "low"]
    affected_roles: list[str] = Field(default_factory=list)


class OperationalReadinessResponse(BaseModel):
    """Response for GET /governance/dashboard/readiness."""

    pprr_phases: list[PPRRPhaseStatus] = Field(min_length=4, max_length=4)
    emergency_plans: list[EmergencyPlanSummary]
    total_plans: int
    overdue_plans_total: int
    exercise_completion_rate_pct: float = Field(ge=0.0, le=100.0)
    exercise_breakdown: list[dict]
    overall_readiness_score: float = Field(ge=0.0, le=100.0)
    aiims_role_coverage: list[AIIMSRoleCoverage]
    overall_role_coverage_pct: float = Field(ge=0.0, le=100.0)
    capability_gap_count: int = Field(ge=0)
    capability_gaps: list[CapabilityGap] = Field(default_factory=list)
    volunteer_readiness: VolunteerReadiness | None = None


# --- Recovery Progress ---


class RecoveryDomainProgress(BaseModel):
    """Progress tracking for one recovery domain."""

    domain: Literal["overarching", "social", "economic", "built", "natural"]
    display_name: str
    completion_pct: float = Field(ge=0.0, le=100.0)
    trend: Literal["improving", "stable", "declining"]
    target_pct: float = Field(ge=0.0, le=100.0)
    variance_from_target: float = Field(description="Positive = ahead, negative = behind")
    is_below_target: bool
    is_cross_cutting: bool = Field(default=False, description="True for overarching domain")
    incident_id: str


class RecoveryDomainDetail(BaseModel):
    """Detail panel for a recovery domain."""

    domain: str
    outcome_targets: list[dict]
    activity_completion_rates: list[dict]
    community_indicators: list[dict]
    me_evaluation_results: list[dict]


class RecoveryProgressResponse(BaseModel):
    """Response for GET /governance/dashboard/recovery."""

    domains: list[RecoveryDomainProgress] = Field(min_length=0, max_length=5)
    active_incident_id: str | None = None
    available_incidents: list[dict]
    has_active_recovery: bool


# --- Risk & Warning ---


class RiskSeverityBreakdown(BaseModel):
    """Risk counts by severity level."""

    extreme: int = Field(ge=0)
    high: int = Field(ge=0)
    medium: int = Field(ge=0)
    low: int = Field(ge=0)
    total: int = Field(ge=0)


class AWSPrincipleCompliance(BaseModel):
    """Compliance rate for one of the 10 AWS warning principles."""

    principle: Literal[
        "life_saving",
        "empowering",
        "trusted",
        "risk_scaled",
        "timely_targeted",
        "impact_conveying",
        "action_calling",
        "clearly_communicated",
        "accessible",
        "bigger_picture",
    ]
    display_name: str
    compliant_count: int = Field(ge=0)
    total_count: int = Field(ge=0)
    compliance_rate_pct: float = Field(ge=0.0, le=100.0)
    non_compliant_warning_ids: list[str] = Field(default_factory=list)


class AlertComplianceMetrics(BaseModel):
    """Alert and warning compliance metrics."""

    avg_approval_latency_s: float = Field(ge=0.0)
    acceptable_threshold_s: float
    exceeds_threshold: bool
    alerts_exceeding_threshold: list[dict]
    aws_tier_usage: dict[str, int]
    broadcast_reach_pct: float = Field(ge=0.0, le=100.0)
    principle_compliance: list[AWSPrincipleCompliance] = Field(min_length=10, max_length=10)
    overall_principle_compliance_pct: float = Field(ge=0.0, le=100.0)


class RiskWarningResponse(BaseModel):
    """Response for GET /governance/dashboard/risk."""

    risk_severity: RiskSeverityBreakdown
    treatment_closure_rate_pct: float = Field(ge=0.0, le=100.0)
    alert_compliance: AlertComplianceMetrics
    top_risks: list[dict]


class RiskDetailResponse(BaseModel):
    """Response for GET /governance/dashboard/risk/{riskId}."""

    risk_id: str
    description: str
    severity: str
    likelihood: str
    consequence: str
    treatments: list[dict]
    treatment_history: list[dict]
    related_audit_urls: list[str] = Field(default_factory=list)


# --- Dashboard Config ---


class DashboardConfigResponse(BaseModel):
    """Response for GET /governance/dashboard/config."""

    user_roles: list[str]
    primary_role: str | None = Field(default=None, description="Highest-authority role")
    widget_layout: list[WidgetDefinition]
    default_view: str
    poll_interval_ms: int = Field(description="Current polling interval in milliseconds")
    has_active_incident: bool
    cache_ttl_s: int = Field(default=300)
    tenant_id: str
    tenant_display_name: str
    is_simulation: bool
