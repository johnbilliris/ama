# Data Model: Governance Dashboard

**Feature**: 021-governance-dashboard
**Date**: 2025-07-18
**Depends on**: [research.md](./research.md)

---

## Overview

This document defines the data entities, relationships, validation rules, and state transitions for the Governance Dashboard feature. Models are split into three categories:

1. **New domain models** — added to `packages/domain/src/domain/models/`
2. **Extended domain models** — existing models that gain new fields or relationships
3. **View models** — API response shapes for dashboard-specific aggregations

All models use Pydantic 2.10 `BaseModel` with `Literal` types for enums (matching the existing codebase pattern in `packages/domain`).

---

## New Domain Models

### GovernanceHealthScore

**Location**: `packages/domain/src/domain/models/governance_health_score.py`
**Purpose**: Represents the calculated composite governance health score.

```python
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class DimensionScore(BaseModel):
    """Score for one of the four health score dimensions."""
    dimension: Literal[
        "constitutional_compliance",
        "operational_readiness",
        "data_source_governance",
        "recovery_progress"
    ]
    score: float = Field(ge=0.0, le=100.0, description="Dimension score 0-100")
    weight: float = Field(ge=0.0, le=1.0, description="Weight factor (must sum to 1.0)")
    weighted_score: float = Field(ge=0.0, le=100.0, description="score × weight")
    input_count: int = Field(ge=0, description="Number of inputs used for this dimension")
    stale: bool = Field(default=False, description="True if underlying data is older than cache TTL")

class GovernanceHealthScore(BaseModel):
    """Composite governance health score (0-100) with traffic light status."""
    id: str = Field(description="Unique score ID, format: health-score-{tenant_id}-{timestamp}")
    tenant_id: str = Field(description="Tenant context: 'live' or 'sim-{scenarioRunId}'")
    score: float = Field(ge=0.0, le=100.0, description="Composite score")
    status: Literal["green", "amber", "red"]
    dimensions: list[DimensionScore] = Field(min_length=4, max_length=4)
    calculated_at: datetime
    cache_ttl_s: int = Field(default=300, description="Cache time-to-live in seconds")
    has_active_incident: bool = Field(default=False)
```

**Validation Rules**:
- `score` must equal `sum(d.weighted_score for d in dimensions)` (± 0.01 for float precision)
- `status` derived: Green (≥80), Amber (50–79), Red (<50)
- `dimensions` weights must sum to 1.0
- All fields required except defaults

**Relationships**:
- References `ConstitutionalGateStatus` (for constitutional compliance dimension)
- References `DataSource` compliance data (for data source governance dimension)
- References PPRR/exercise/role data (for operational readiness dimension)
- References `RecoveryDomainProgress` (for recovery progress dimension)

---

### ConstitutionalGateStatus

**Location**: `packages/domain/src/domain/models/governance_health_score.py` (same file)
**Purpose**: Status of a single constitutional gate for dashboard display.

```python
class ConstitutionalGateStatus(BaseModel):
    """Compliance status for one of the 10 constitutional gates."""
    gate_number: int = Field(ge=1, le=10, description="Gate 1-10")
    gate_name: str = Field(description="Human-readable gate name")
    status: Literal["compliant", "non_compliant", "partially_compliant", "assessment_pending"]
    severity: Literal["info", "warning", "critical"] | None = Field(
        default=None,
        description="Severity indicator for non-compliant/partially-compliant gates"
    )
    last_assessment_date: datetime | None = Field(default=None)
    evidence_count: int = Field(ge=0, default=0, description="Number of evidence artefacts")
    detail_url: str = Field(description="Navigation URL to detailed compliance view")
```

**Constitutional Gates Reference**:

| Gate # | Name | Constitution Section |
|--------|------|---------------------|
| 1 | Primacy of Life | §I |
| 2 | National EM Principles | §II |
| 3 | Multi-Hazard Design | §III |
| 4 | Transparency & Auditability | §IV |
| 5 | Warning & Public Information | §V |
| 6 | Evacuation Framework | §VI |
| 7 | Recovery Support | §VII |
| 8 | Cloud Platform & Infrastructure | §VIII |
| 9 | PPRR Lifecycle | §PPRR |
| 10 | Governance & Quality Gates | §Quality Gates |

---

### RoleWidgetMapping

**Location**: `packages/domain/src/domain/models/dashboard_widget_config.py`
**Purpose**: Defines the default widget layout for each AIIMS role.

```python
from pydantic import BaseModel, Field
from typing import Literal

AIIMSRole = Literal[
    "incident_controller",
    "operations_officer",
    "planning_officer",
    "intelligence_officer",
    "logistics_officer",
    "public_information_officer",
    "executive_leader",
    "observer_auditor",
    "risk_manager",
    "resilience_planner"
]

class WidgetDefinition(BaseModel):
    """A single widget in a dashboard layout."""
    widget_id: str = Field(description="Unique widget identifier, e.g., 'health_score_gauge'")
    widget_type: Literal[
        "gauge", "grid", "table", "chart", "indicator",
        "search", "timeline", "progress_bar", "counter"
    ]
    display_name: str
    priority: int = Field(ge=1, description="Display order within the role's layout")
    data_endpoint: str = Field(description="API endpoint that provides data for this widget")
    refresh_group: Literal["active_incident", "steady_state", "manual_only"]

class RoleWidgetMapping(BaseModel):
    """Maps an AIIMS role to its default widget configuration."""
    role: AIIMSRole
    default_view: Literal[
        "executive_summary", "compliance", "audit_trail",
        "operational_readiness", "recovery", "risk_warning"
    ]
    widgets: list[WidgetDefinition] = Field(min_length=1)
    authority_rank: int = Field(
        ge=1, le=10,
        description="Rank for multi-role ordering: 1=highest authority"
    )
```

**Authority Hierarchy** (for multi-role resolution):

| Rank | Role |
|------|------|
| 1 | Incident Controller |
| 2 | Executive Leader |
| 3 | Operations Officer |
| 4 | Planning Officer |
| 5 | Intelligence Officer |
| 6 | Logistics Officer |
| 7 | Public Information Officer |
| 8 | Risk Manager |
| 9 | Resilience Planner |
| 10 | Observer/Auditor |

---

### AuditExportJob

**Location**: `packages/domain/src/domain/models/audit_export.py`
**Purpose**: Tracks the lifecycle of an asynchronous audit export operation.

```python
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

ExportFormat = Literal["pdf", "csv", "json"]

class AuditExportJob(BaseModel):
    """Tracks an asynchronous audit export operation."""
    id: str = Field(description="Unique job ID, format: export-{uuid}")
    tenant_id: str
    requested_by: str = Field(description="User identity who initiated the export")
    requested_at: datetime
    format: ExportFormat
    status: Literal["queued", "processing", "complete", "failed"]
    filter_params: dict = Field(
        default_factory=dict,
        description="The search/filter parameters used to select records"
    )
    record_count: int = Field(ge=0, default=0, description="Number of records in export")
    download_url: str | None = Field(
        default=None,
        description="Azure Blob Storage SAS URL, set when status='complete'"
    )
    download_expires_at: datetime | None = Field(default=None, description="SAS URL expiry (24h)")
    error_message: str | None = Field(default=None, description="Set when status='failed'")
    completed_at: datetime | None = Field(default=None)
```

**State Transitions**:
```
queued → processing → complete
                   → failed
```
- `queued`: Job created, waiting for background worker
- `processing`: Worker is generating the file
- `complete`: File available at `download_url` for 24 hours
- `failed`: Generation failed; `error_message` contains details

---

### DashboardInteractionAudit

**Location**: Extends `GovernanceAuditEntry` in `packages/domain/src/domain/models/governance_audit.py`
**Purpose**: Audit record for dashboard user interactions (FR-027).

```python
# New GovernanceAction values to add to existing Literal type:
# "dashboard_view", "dashboard_filter", "dashboard_search",
# "dashboard_export", "dashboard_drill_down", "dashboard_navigate_to_crud"

class DashboardInteractionAudit(BaseModel):
    """Extended audit entry for dashboard-specific interactions."""
    id: str
    tenant_id: str
    timestamp: datetime
    actor_id: str = Field(description="User identity (required for Gate 4 provenance)")
    actor_role: AIIMSRole | str
    action: Literal[
        "dashboard_view", "dashboard_filter", "dashboard_search",
        "dashboard_export", "dashboard_drill_down", "dashboard_navigate_to_crud"
    ]
    view: str = Field(description="Dashboard view accessed, e.g., 'executive_summary'")
    parameters: dict = Field(
        default_factory=dict,
        description="Action-specific parameters: filters applied, search query, export format, etc."
    )
    result_count: int | None = Field(default=None, description="Number of results for search/filter")
    session_context: str = Field(description="Session correlation ID")
```

**Retention**: 90-day hot storage in Cosmos DB, then archived to Azure Storage cool tier (7-year total retention).

---

## Extended Domain Models

### DataSource (existing: `packages/domain/src/domain/models/data_source.py`)

**New Fields for Dashboard**:

```python
# Add to existing DataSource model:
next_assessment_due_date: datetime | None = Field(default=None)
governance_gap_count: int = Field(ge=0, default=0)
grace_period_expiry: datetime | None = Field(default=None)
grace_period_reason: str | None = Field(default=None)
```

These fields are already partially supported (grace period exists in the model). `governance_gap_count` and `next_assessment_due_date` are derived from the governance registry's `detect_governance_gaps()` and assessment history.

### GovernanceAuditEntry (existing: `packages/domain/src/domain/models/governance_audit.py`)

**Extended Action Types**:

```python
# Current GovernanceAction Literal values:
# "register", "assess", "assign", "reassess", "activate_grace_period",
# "extend_grace_period", "block_source", "define_handoff_chain",
# "set_precedence", "deactivate"

# New values to add for dashboard:
# "dashboard_view", "dashboard_filter", "dashboard_search",
# "dashboard_export", "dashboard_drill_down", "dashboard_navigate_to_crud"
```

**New Optional Fields**:

```python
# Add to existing GovernanceAuditEntry:
tenant_id: str = Field(default="live")
view_context: str | None = Field(default=None, description="Dashboard view name")
session_id: str | None = Field(default=None, description="Correlation ID for session tracking")
```

---

## View Models (API Response Shapes)

These are not persisted — they are constructed by the aggregation service for API responses.

### ExecutiveSummaryResponse

```python
class ExecutiveSummaryResponse(BaseModel):
    """Response for GET /governance/dashboard/summary"""
    health_score: GovernanceHealthScore
    constitutional_gates: list[ConstitutionalGateStatus] = Field(min_length=10, max_length=10)
    active_incident_count: int = Field(ge=0)
    resource_utilisation_pct: float = Field(ge=0.0, le=100.0)
    risk_summary: dict[str, int]  # {"extreme": 2, "high": 5, "medium": 12, "low": 8}
    data_freshness: datetime  # Timestamp of oldest data source
    tenant_id: str
```

### ComplianceMatrixResponse

```python
class ComplianceMatrixEntry(BaseModel):
    """A row in the compliance matrix."""
    data_source_id: str
    data_source_name: str
    compliance_status: Literal["compliant", "non_compliant", "pending", "grace_period"]
    last_assessment_date: datetime | None
    next_assessment_due_date: datetime | None
    governance_gap_count: int = Field(ge=0)
    grace_period_expiry: datetime | None
    grace_period_reason: str | None
    grace_period_countdown_days: int | None
    category: str | None

class ComplianceMatrixResponse(BaseModel):
    """Response for GET /governance/dashboard/compliance"""
    entries: list[ComplianceMatrixEntry]
    total_count: int
    filters_applied: dict
    continuation_token: str | None
    page_size: int = Field(default=50)
```

### AuditTrailResponse

```python
class AuditEventSummary(BaseModel):
    """Summary row in the audit trail list."""
    id: str
    timestamp: datetime
    actor: str
    action_type: str
    affected_entity: str
    outcome: str
    provenance_reference: str | None
    has_decision_chain: bool

class DecisionChainStep(BaseModel):
    """A step in a decision chain."""
    step_order: int
    event_type: Literal["trigger", "approval", "action", "notification"]
    actor: str
    timestamp: datetime
    description: str
    rationale: str | None
    evidence_integrity: Literal["verified", "unverified", "pending"]

class AuditDecisionChainResponse(BaseModel):
    """Response for GET /governance/dashboard/audit/{event_id}/chain"""
    event_id: str
    chain: list[DecisionChainStep]
    chain_complete: bool = Field(description="True if chain has trigger + final action")

class AuditTrailResponse(BaseModel):
    """Response for GET /governance/dashboard/audit"""
    events: list[AuditEventSummary]
    total_count: int
    filters_applied: dict
    continuation_token: str | None
    page_size: int = Field(default=50)
```

### OperationalReadinessResponse

```python
class PPRRPhaseStatus(BaseModel):
    """Status of a single PPRR phase."""
    phase: Literal["prevention", "preparedness", "response", "recovery"]
    is_active: bool
    indicator_status: Literal["active", "inactive", "elevated"]

class EmergencyPlanSummary(BaseModel):
    """Emergency plan counts by lifecycle status."""
    lifecycle_state: Literal[
        "Draft", "InConsultation", "UnderReview", "Endorsed",
        "Activated", "PostEventReview", "Superseded"
    ]
    count: int = Field(ge=0)
    overdue_count: int = Field(ge=0, description="Plans in this state with expired review date")

class AIIMSRoleCoverage(BaseModel):
    """Coverage status for a single AIIMS role."""
    role: AIIMSRole
    assigned_count: int = Field(ge=0)
    required_count: int = Field(ge=1)
    is_staffed: bool
    coverage_pct: float = Field(ge=0.0, le=100.0)

class OperationalReadinessResponse(BaseModel):
    """Response for GET /governance/dashboard/readiness"""
    pprr_phases: list[PPRRPhaseStatus] = Field(min_length=4, max_length=4)
    emergency_plans: list[EmergencyPlanSummary]
    total_plans: int
    overdue_plans_total: int
    exercise_completion_rate_pct: float = Field(ge=0.0, le=100.0)
    exercise_breakdown: list[dict]  # [{type, rate, last_date}]
    overall_readiness_score: float = Field(ge=0.0, le=100.0)
    aiims_role_coverage: list[AIIMSRoleCoverage]
    overall_role_coverage_pct: float = Field(ge=0.0, le=100.0)
    capability_gap_count: int = Field(ge=0)
```

### RecoveryProgressResponse

```python
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
    outcome_targets: list[dict]  # [{target_name, target_value, current_value}]
    activity_completion_rates: list[dict]  # [{activity, rate_pct}]
    community_indicators: list[dict]  # [{indicator, value, type: "quantitative"|"qualitative"}]
    me_evaluation_results: list[dict]  # [{outcome, rating, evidence_count}]

class RecoveryProgressResponse(BaseModel):
    """Response for GET /governance/dashboard/recovery"""
    domains: list[RecoveryDomainProgress] = Field(min_length=5, max_length=5)
    active_incident_id: str | None
    available_incidents: list[dict]  # [{incident_id, name, start_date}]
    has_active_recovery: bool
```

### RiskWarningResponse

```python
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
        "life_saving", "empowering", "trusted", "risk_scaled",
        "timely_targeted", "impact_conveying", "action_calling",
        "clearly_communicated", "accessible", "bigger_picture"
    ]
    display_name: str
    compliant_count: int = Field(ge=0)
    total_count: int = Field(ge=0)
    compliance_rate_pct: float = Field(ge=0.0, le=100.0)
    non_compliant_warning_ids: list[str] = Field(
        default_factory=list,
        description="IDs of warnings failing this principle (for drill-down)"
    )

class AlertComplianceMetrics(BaseModel):
    """Alert and warning compliance metrics."""
    avg_approval_latency_s: float = Field(ge=0.0)
    acceptable_threshold_s: float
    exceeds_threshold: bool
    alerts_exceeding_threshold: list[dict]  # [{alert_id, actual_latency_s, approved_at}]
    aws_tier_usage: dict[str, int]  # {"advice": N, "watch_and_act": N, "emergency_warning": N}
    broadcast_reach_pct: float = Field(ge=0.0, le=100.0)
    principle_compliance: list[AWSPrincipleCompliance] = Field(min_length=10, max_length=10)
    overall_principle_compliance_pct: float = Field(ge=0.0, le=100.0)

class RiskWarningResponse(BaseModel):
    """Response for GET /governance/dashboard/risk"""
    risk_severity: RiskSeverityBreakdown
    treatment_closure_rate_pct: float = Field(ge=0.0, le=100.0)
    alert_compliance: AlertComplianceMetrics
    top_risks: list[dict]  # [{id, description, severity, treatment_due, responsible}]
```

### DashboardConfigResponse

```python
class DashboardConfigResponse(BaseModel):
    """Response for GET /governance/dashboard/config"""
    user_roles: list[AIIMSRole]
    primary_role: AIIMSRole | None = Field(description="Highest-authority role")
    widget_layout: list[WidgetDefinition]
    default_view: str
    poll_interval_ms: int = Field(description="Current polling interval in milliseconds")
    has_active_incident: bool
    cache_ttl_s: int = Field(default=300)
    tenant_id: str
    tenant_display_name: str  # "Live" or "SIMULATION — {scenario name}"
    is_simulation: bool
```

---

## Entity Relationship Diagram

```
┌─────────────────────────┐     ┌──────────────────────────────┐
│ GovernanceHealthScore   │────▶│ ConstitutionalGateStatus (10)│
│ - score, status, dims   │     │ - gate_number, status        │
│ - calculated_at         │     │ - severity, evidence_count   │
└─────────────┬───────────┘     └──────────────────────────────┘
              │
    ┌─────────┼─────────────────────────────┐
    │         │                             │
    ▼         ▼                             ▼
┌────────┐ ┌──────────┐  ┌─────────┐ ┌───────────────────┐
│DataSrc │ │ PPRR/    │  │Recovery │ │ RoleWidgetMapping │
│(exist) │ │ Plans/   │  │Domain   │ │ - role, widgets   │
│+gaps   │ │ Exercises│  │Progress │ │ - authority_rank  │
└────────┘ └──────────┘  └─────────┘ └───────────────────┘

┌─────────────────────────┐     ┌──────────────────────────┐
│ GovernanceAuditEntry    │     │ AuditExportJob           │
│ (EXTENDED)              │────▶│ - format, status         │
│ + tenant_id             │     │ - download_url           │
│ + dashboard actions     │     │ - filter_params          │
└─────────────────────────┘     └──────────────────────────┘
```

---

## Cosmos DB Container Strategy

All new entities use the existing governance containers with `type` discriminator:

| Entity | Container | Partition Key | Type Discriminator |
|--------|-----------|---------------|-------------------|
| GovernanceHealthScore | governance | `tenant_id` | `health_score` |
| ConstitutionalGateStatus | governance | `tenant_id` | `gate_status` |
| RoleWidgetMapping | governance | `_config` | `role_widget_mapping` |
| AuditExportJob | governance_audit | `tenant_id` | `export_job` |
| DashboardInteractionAudit | governance_audit | `tenant_id` | `dashboard_interaction` |
| RecoveryDomainProgress | governance | `incident_id` | `recovery_progress` |

**New Composite Indexes**:
- `governance_audit` container: `(tenant_id, timestamp DESC, action_type, actor)`
- `governance` container: `(tenant_id, type, compliance_status)`
