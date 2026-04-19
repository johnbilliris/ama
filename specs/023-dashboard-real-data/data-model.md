# Data Model: Governance Dashboard Real Data Integration

**Feature**: 023-dashboard-real-data
**Date**: 2025-07-18
**Prerequisite**: [research.md](./research.md) complete

## Entity Relationship Overview

```
┌──────────────────────┐     loads      ┌─────────────────────────┐
│    SeedService       │───────────────>│   bootstrap_seed_data() │
│  (lru_cache)         │                │   packages/domain/seed/ │
└──────────┬───────────┘                └─────────────────────────┘
           │ seed dict                         │
           ▼                                   │ returns dict with keys:
┌──────────────────────┐                       │  jurisdictions (9)
│ GovernanceDataService│<──────────────────────┘  frameworks (27)
│     (NEW)            │                          organisations (49)
│                      │                          data_sources (46)
│ - compute_gates()    │                          disasters
│ - compute_readiness()│                          framework_assignments (123)
│ - compute_recovery() │                          recovery_catalogue (5 domains) ← NEW
│ - compute_risk()     │
│ - compute_compliance()│
│ - query_audit()      │
└──────────┬───────────┘
           │ structured inputs
           ▼
┌──────────────────────────┐      delegates    ┌─────────────────────┐
│ DashboardAggregationSvc  │──────────────────>│ HealthScoreService  │
│  (existing, refactored)  │                   │ (existing, no change│
│                          │                   │  to algorithm)      │
│ 6 public view methods    │                   └─────────────────────┘
│ ~15 private helpers      │
│  → replaced with calls   │
│    to GovernanceDataSvc  │
└──────────┬───────────────┘
           │ response models
           ▼
┌──────────────────────────┐
│ 13 Route Endpoints       │
│ governance_dashboard.py  │
│ (inject SeedService via  │
│  FastAPI Depends)        │
└──────────────────────────┘
```

## Entities

### Existing Entities (No Schema Changes)

#### ConstitutionalAssessment
**Source**: `packages/domain/src/domain/models/constitutional_assessment.py`
**Storage**: Cosmos DB (when assessments are performed)

| Field | Type | Description |
|-------|------|-------------|
| assessment_id | str | Unique ID |
| data_source_id | str | Assessed data source |
| principle | ConstitutionalPrinciple | One of 6 enum values |
| compliance_status | AssessmentComplianceStatus | compliant/partially_compliant/non_compliant/not_applicable |
| explanation | str | Assessment rationale |
| conditions | list[str] | Conditions for compliance |
| gaps | list[str] | Identified gaps |
| assessor_id | str | Who performed assessment |
| assessed_at | datetime | When assessed |
| superseded_by | str \| None | ID of superseding assessment |
| is_current | bool | True if not superseded (FR-028 filter) |
| triggered_by | AssessmentTrigger | What triggered the assessment |

**Dashboard usage**: Constitutional compliance component (40% of health score), compliance matrix entries. Only `is_current=True` assessments are used (FR-028).

---

#### GovernanceAuditEntry
**Source**: `packages/domain/src/domain/models/governance_audit.py`
**Storage**: Cosmos DB (created by actual governance actions)

| Field | Type | Description |
|-------|------|-------------|
| audit_entry_id | str | Unique ID |
| data_source_id | str | Related data source |
| action | GovernanceAction | Action type (broad literal) |
| actor_id | str | Who performed the action |
| timestamp | datetime | When it occurred |
| details | str | Contextual details |
| related_entity_id | str \| None | Reference to related entity |
| tenant_id | str | Tenant scope |
| view_context | str \| None | Dashboard view context |
| session_id | str \| None | Session reference |

**Dashboard usage**: Audit trail view (FR-018–021). Empty when no actions have occurred — this is correct per spec clarification.

---

#### HazardAssessment
**Source**: `packages/domain/src/domain/models/hazard_assessment.py`
**Storage**: Cosmos DB (created by assessment processes)

| Field | Type | Description |
|-------|------|-------------|
| severity_level | Literal["low", "moderate", "high", "critical"] | Risk severity |
| confidence_score | float (0–1) | Assessment confidence |
| summary | str | Risk description |
| assessment_type | str | Type of assessment |
| status | str | Assessment status |
| tenant_id | str | Tenant scope |

**Dashboard usage**: Risk severity counts (FR-014), top risks list (FR-015). Returns zero counts when no assessments exist (FR-017).

---

#### EmergencyPlan
**Source**: `packages/domain/src/domain/models/emergency_plan.py`
**Storage**: Cosmos DB (created by plan management processes)

| Field | Type | Description |
|-------|------|-------------|
| plan_id | str | Unique ID |
| lifecycle_state | PlanLifecycleState | One of 7 states |
| region_id | str | Jurisdiction/region |
| hazard_types | list[IncidentType] | Hazards covered |
| next_review_date | date \| None | Review deadline |
| last_exercise_date | date \| None | Last exercise |

**Dashboard usage**: Emergency plan status distribution in operational readiness (FR-008). Falls back to seed-derived expectations when no plan records exist.

---

#### Organisation (Seed)
**Source**: `packages/domain/src/domain/seed/organisations_australia.json`
**Storage**: Seed file (46 entries loaded via bootstrap)

| Field | Type | Dashboard Usage |
|-------|------|----------------|
| organisation_id | str | Unique identifier |
| aiims_functions | list[AiimsFunction] | AIIMS role coverage (FR-007) |
| workforce_type | "paid" \| "volunteer" \| "mixed" | Volunteer readiness (FR-010) |
| primary_capabilities | list[str] | Capability gap analysis (FR-009) |
| jurisdiction_ids | list[str] | Jurisdiction distribution |
| category | str | Organisation classification |
| hazard_types | list[str] | Hazard coverage capability |

---

#### OperatingFramework (Seed)
**Source**: `packages/domain/src/domain/seed/frameworks_australia.json`
**Storage**: Seed file (27 entries loaded via bootstrap)

| Field | Type | Dashboard Usage |
|-------|------|----------------|
| framework_id | str | Join key for assignments |
| pprr_phases | list[PprrPhase] | PPRR phase distribution (FR-006) |
| hazard_types | list[IncidentType] | Capability gap derivation |
| applicable_jurisdiction_ids | list[str] | Jurisdiction coverage |

---

#### FrameworkAssignment (Seed)
**Source**: `packages/domain/src/domain/seed/framework_assignments_australia.json`
**Storage**: Seed file (123 entries loaded via bootstrap)

| Field | Type | Dashboard Usage |
|-------|------|----------------|
| assignment_id | str | Unique ID |
| framework_id | str | Join to framework for phases |
| jurisdiction_id | str | PPRR per jurisdiction (FR-006) |
| effective_from | datetime | Assignment validity |
| effective_to | datetime \| None | Assignment expiry |

---

#### DataSource (Seed)
**Source**: `packages/domain/src/domain/seed/data_sources_australia.json`
**Storage**: Seed file (46 entries loaded via bootstrap)

| Field | Type | Dashboard Usage |
|-------|------|----------------|
| data_source_id | str | Unique ID, join key for assessments |
| name | str | Display name |
| status | str | available/degraded/offline → governance score (FR-003) |
| trust_tier | TrustTier | AWS compliance derivation (FR-016) |
| compliance_status | str | Direct compliance status |

---

#### Recovery Catalogue Domain (Seed — NEW in bootstrap)
**Source**: `packages/domain/src/domain/seed/recovery-catalogue/{domain}.json`
**Storage**: Seed file (5 domain files loaded via extended bootstrap)

| Field | Type | Dashboard Usage |
|-------|------|----------------|
| domain | str | Domain identifier (overarching/social/economic/built/natural) |
| outcomes | list[Outcome] | Recovery outcome tracking (FR-011) |
| outcomes[].activities | list[Activity] | Activity counts per outcome |
| outcomes[].indicators | list[Indicator] | Indicator counts and targets (FR-012) |

**Outcome structure**:
```json
{
  "outcome_id": "built:1",
  "objective_type": "built_outcome",
  "title": "...",
  "description": "...",
  "activities": [{ "activity_id": "...", "title": "...", "description": "..." }],
  "indicators": [{ "indicator_id": "...", "title": "...", "description": "...", "data_collection_methodology": "...", "indicator_type": "..." }]
}
```

---

### New Service: GovernanceDataService

**File**: `apps/api/app/services/governance_data_service.py`
**Purpose**: Compute real dashboard metrics from seed data and stored records

```python
class GovernanceDataService:
    """Computes real governance metrics from seed data and stored records.
    
    Three-tier data resolution:
    1. Stored data (Cosmos DB) when available
    2. Seed-derived computation as fallback
    3. Zero-state baseline when seed also unavailable
    """
    
    def __init__(
        self,
        seed_data: dict[str, Any],
        governance_repo: object | None = None,  # Cosmos DB repo
    ) -> None:
        self._seed = seed_data
        self._repo = governance_repo
        # Pre-index seed data for fast lookup
        self._frameworks_by_id: dict[str, dict] = {
            f["framework_id"]: f for f in seed_data.get("frameworks", [])
        }
        self._orgs_by_id: dict[str, dict] = {
            o["organisation_id"]: o for o in seed_data.get("organisations", [])
        }
    
    # --- Constitutional Gates ---
    
    def compute_constitutional_gates(
        self, tenant_id: str
    ) -> list[ConstitutionalGateStatus]:
        """Build 10 constitutional gate statuses from stored assessments + seed inference.
        
        Returns exactly 10 gates. Uses stored ConstitutionalAssessment records
        where available (is_current=True only), infers remaining from seed data
        presence/coverage.
        """
        ...
    
    # --- Data Source Statistics ---
    
    def compute_data_source_stats(self, tenant_id: str) -> dict:
        """Compute data source governance stats from seed registry.
        
        Returns: {"total": int, "compliant": int, "partially_compliant": int}
        Mapping: status=available → compliant, degraded → partially_compliant,
                 offline → non_compliant
        """
        ...
    
    # --- Operational Readiness ---
    
    def compute_readiness_inputs(self, tenant_id: str) -> dict:
        """Compute operational readiness metrics from seed + stored data.
        
        Returns: {
            "exercise_completion_rate": float,  # from framework exercise metadata
            "role_coverage_pct": float,         # from org AIIMS functions
            "plan_currency_pct": float,         # from stored plans or 0.0
        }
        """
        ...
    
    def compute_pprr_distribution(self, tenant_id: str) -> list[PPRRPhaseStatus]:
        """Compute PPRR phase distribution from framework assignments.
        
        Joins 123 assignments to 27 frameworks to count phases.
        Returns exactly 4 PPRRPhaseStatus entries.
        """
        ...
    
    def compute_aiims_role_coverage(self, tenant_id: str) -> list[AIIMSRoleCoverage]:
        """Compute AIIMS role coverage from organisation function assignments.
        
        Aggregates aiims_functions across 49 organisations for all 6 AIIMS functions.
        """
        ...
    
    def compute_emergency_plan_summaries(self, tenant_id: str) -> list[EmergencyPlanSummary]:
        """Get plan counts by lifecycle state from stored records.
        
        Falls back to zero-count summaries when no plans exist.
        """
        ...
    
    def compute_volunteer_readiness(self, tenant_id: str) -> VolunteerReadiness:
        """Compute volunteer metrics from organisations with volunteer/mixed workforce.
        
        Counts organisations, jurisdiction distribution, capability coverage.
        """
        ...
    
    def compute_capability_gaps(self, tenant_id: str) -> list[CapabilityGap]:
        """Identify gaps between framework hazard requirements and org capabilities.
        
        Per jurisdiction: what hazard types do assigned frameworks require
        that no organisation in that jurisdiction can cover?
        """
        ...
    
    # --- Recovery Progress ---
    
    def compute_recovery_domains(
        self, tenant_id: str, incident_id: str | None = None
    ) -> list[RecoveryDomainProgress]:
        """Compute recovery domain progress from catalogue + active trackers.
        
        Returns up to 5 domains (overarching, social, economic, built, natural).
        When no trackers exist, returns 0% completion with catalogue structure.
        """
        ...
    
    def compute_recovery_domain_detail(
        self, domain: str, tenant_id: str
    ) -> RecoveryDomainDetail | None:
        """Get detailed recovery data for a specific domain from catalogue.
        
        Returns outcome targets, activity counts, indicator data.
        """
        ...
    
    def compute_recovery_inputs(self, tenant_id: str) -> dict:
        """Compute recovery data for health score input.
        
        Returns: {"has_active_recovery": bool, "domains": list[dict]}
        """
        ...
    
    # --- Risk & Warning ---
    
    def compute_risk_severity(self, tenant_id: str) -> RiskSeverityBreakdown:
        """Compute risk severity counts from stored hazard assessments.
        
        Returns zero counts when no assessments exist (FR-017).
        """
        ...
    
    def compute_top_risks(self, tenant_id: str) -> list[dict]:
        """Get top risks ranked by severity and confidence.
        
        From stored HazardAssessment records. Empty when none exist.
        """
        ...
    
    def compute_aws_compliance(self, tenant_id: str) -> list[AWSPrincipleCompliance]:
        """Compute AWS principle compliance from data source trust tier configs.
        
        Maps trust tier alignment to 10 warning principles.
        """
        ...
    
    # --- Compliance Matrix ---
    
    def compute_compliance_entries(
        self, tenant_id: str
    ) -> list[ComplianceMatrixEntry]:
        """Build compliance matrix from stored assessments + seed data sources.
        
        Uses real ConstitutionalAssessment records where available.
        Falls back to seed-derived baseline for unassessed sources.
        """
        ...
    
    # --- Audit Trail ---
    
    def query_audit_events(
        self,
        tenant_id: str,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        actor: str | None = None,
        action_type: str | None = None,
        affected_entity: str | None = None,
        keyword: str | None = None,
    ) -> list[AuditEventSummary]:
        """Query stored governance audit entries with filters.
        
        Returns actual stored records. Empty list when no entries exist.
        """
        ...
    
    def query_decision_chain(
        self, event_id: str, tenant_id: str
    ) -> AuditDecisionChainResponse | None:
        """Get the decision chain for a specific audit event.
        
        Returns actual linked events. None if event not found.
        """
        ...
```

## State Transitions

### Data Source Resolution State Machine

```
┌──────────────┐
│  Request     │
│  Received    │
└──────┬───────┘
       │
       ▼
┌──────────────┐    records found    ┌──────────────┐
│ Check Stored │───────────────────>│ Use Stored   │
│ Records      │                    │ Data         │
└──────┬───────┘                    │ indicator:   │
       │ no records                 │  "live"      │
       ▼                            └──────────────┘
┌──────────────┐    seed loaded     ┌──────────────┐
│ Check Seed   │───────────────────>│ Use Seed     │
│ Data         │                    │ Computed     │
└──────┬───────┘                    │ indicator:   │
       │ seed missing/failed        │ "seed_fallback"│
       ▼                            └──────────────┘
┌──────────────┐
│ Zero State   │
│ Baseline     │
│ indicator:   │
│  "unavailable"│
└──────────────┘
```

### Emergency Plan Lifecycle States (Existing)

```
Draft → InConsultation → UnderReview → Endorsed → Activated → PostEventReview → Superseded
```

7 states. Plan counts per state are computed from stored `EmergencyPlan` records.

## Validation Rules

| Rule | Source | Enforcement |
|------|--------|-------------|
| Exactly 10 constitutional gates | `CONSTITUTIONAL_GATES` constant | `ConstitutionalGateStatus` list validated in `GovernanceDataService` |
| Exactly 4 PPRR phases | PprrPhase enum | `PPRRPhaseStatus` list len=4 in response model |
| Health score weights sum to 1.0 | `GovernanceHealthScore` validator | Pydantic validator `± 0.01` tolerance |
| `is_current=True` filter on assessments | FR-028 | Query filter in `GovernanceDataService` |
| Recovery domains ∈ {overarching, social, economic, built, natural} | Literal type | Pydantic model + route validation |
| Risk severity ∈ {low, moderate, high, critical} | `HazardAssessment` model | Literal type constraint |
| Compliance status ∈ {compliant, non_compliant, pending, grace_period} | `ComplianceMatrixEntry` | Literal type constraint |
| Superseded assessments excluded | FR-028 | `is_current` boolean filter |

## Additive Response Model Changes

### New Optional Fields (backward-compatible)

```python
# No structural changes to existing response models.
# The data_source_indicator metadata will be carried through 
# the existing dict fields where applicable (e.g., risk_summary, 
# available_incidents) rather than adding new top-level fields.
#
# This avoids any response model changes while still communicating
# data provenance through existing flexible dict/list fields.
```

**Decision**: After analysis, no new response model fields are needed for MVP. The seed fallback information is observable through:
1. Zero counts in risk severity → clearly no stored assessments
2. Empty audit trail → clearly no actions taken
3. Catalogue structure with 0% completion → clearly no active trackers
4. Log-level metadata for operators via Application Insights

Frontend indicator updates (showing "seed baseline" labels) can be implemented as a follow-up based on the presence of zero/baseline values, without new API fields.
