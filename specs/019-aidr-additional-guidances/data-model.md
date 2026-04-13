# Data Model: AIDR Additional Guidance Integration

**Feature**: 019-aidr-additional-guidances  
**Date**: 2025-07-19  
**Depends on**: [research.md](./research.md) decisions R-001 through R-013

---

## Overview

This feature introduces **6 new domain models** and **1 extended model**. All models follow the existing Pydantic `BaseModel` convention in `packages/domain/src/domain/models/`. All use `Literal[...]` unions for constrained types (no `Enum` classes), string IDs, and `Field(default_factory=...)` for mutable defaults.

---

## Extended Models

### E-001: `RecoveryIndicator` (extend existing)

**File**: `packages/domain/src/domain/models/recovery_environment_tracker.py`  
**FRs**: FR-015, FR-030, FR-031  
**Research**: R-011

**Current fields** (preserved unchanged):
- `indicator_name: str`
- `environment: RecoveryEnvironment`
- `value: float | None`
- `unit: str`
- `baseline_value: float | None`
- `target_value: float | None`
- `last_updated_at: datetime | None`
- `update_source: IndicatorUpdateSource`
- `data_source_id: str | None`
- `population_coverage: int | None`
- `data_classification: DataClassification`
- `is_regressed: bool`
- `regression_cause: str | None`
- `linked_alert_id: str | None`

**New fields**:

| Field | Type | Default | FR | Description |
|-------|------|---------|-----|-------------|
| `catalogue_indicator_id` | `str \| None` | `None` | FR-015 | Hierarchical ID linking to AIDR catalogue counterpart (e.g., `aidr:social:community-health-levels:ind:1`). `None` for spec 018 indicators without catalogue link. |

**Validation rules**:
- All existing validators preserved unchanged (k-anonymity ≥10, regression_cause required when regressed).
- `catalogue_indicator_id`, when set, must match pattern `aidr:{domain}:{outcome-slug}:ind:{index}` (validated via regex).
- Backward compatible: existing code and tests unaffected by the new optional field.

---

## New Models

### N-001: `EmergencyPlan`

**File**: `packages/domain/src/domain/models/emergency_plan.py`  
**FRs**: FR-001–007, FR-007a  
**Research**: R-002, R-003, R-008

```python
# Type aliases
PlanLifecycleState = Literal[
    "draft", "in_consultation", "under_review", "endorsed",
    "activated", "post_event_review", "superseded",
]
PlanHierarchyLevel = Literal["national", "state", "regional", "local"]
SecurityRating = Literal["unclassified", "official", "official_sensitive", "protected"]
```

**Fields**:

| Field | Type | Default | FR | Description |
|-------|------|---------|-----|-------------|
| `plan_id` | `str` | — | — | Unique identifier (e.g., `ep-{uuid}`) |
| `title` | `str` | — | FR-002 | Plan title |
| `region_id` | `str` | — | FR-005 | Geographic region this plan covers (partition key) |
| `hazard_types` | `list[IncidentType]` | `[]` | FR-003 | Hazard types covered by this plan |
| `hierarchy_level` | `PlanHierarchyLevel` | — | FR-005 | Plan hierarchy position |
| `parent_plan_id` | `str \| None` | `None` | FR-005 | Parent plan in the hierarchy |
| `lifecycle_state` | `PlanLifecycleState` | `"draft"` | FR-006 | Current lifecycle state |
| `version` | `int` | `1` | FR-006 | Plan version number |
| `security_rating` | `SecurityRating` | `"official"` | FR-007a | Access control classification |
| `authority` | `str` | `""` | FR-002 | Issuing authority |
| `endorsed_by` | `str \| None` | `None` | FR-006 | Designated authority who endorsed |
| `endorsed_at` | `datetime \| None` | `None` | FR-006 | Endorsement timestamp |
| `next_review_date` | `datetime \| None` | `None` | FR-006 | Scheduled review date |
| `last_exercise_date` | `datetime \| None` | `None` | FR-006 | Last exercise completion date |
| `plan_sections` | `dict[str, PlanSection]` | `{}` | FR-002 | 27 required AIDR plan sections (keyed by section slug) |
| `planning_principles_checklist` | `dict[str, bool]` | `{}` | FR-004 | Eight AIDR planning principles compliance (keys: `risk_informed`, `reducing_unknowns`, `collaborative_inclusive`, `strategic`, `solutions_oriented`, `iterative`, `adaptive_capacity`, `shared_responsibility`) |
| `activation_records` | `list[PlanActivationRecord]` | `[]` | FR-007 | History of plan activations during incidents |
| `amendment_register` | `list[PlanAmendment]` | `[]` | FR-002 | Version history and change records |
| `distribution_list` | `list[str]` | `[]` | FR-002 | Entities that receive this plan |
| `created_at` | `datetime` | `now(UTC)` | — | Creation timestamp |
| `created_by` | `str` | `""` | FR-007a | Planning Officer who created the plan |
| `updated_at` | `datetime \| None` | `None` | — | Last modification timestamp |

**Nested models**:

```python
class PlanSection(BaseModel):
    section_slug: str         # e.g., "authority", "aim_objectives", "response_arrangements"
    title: str                # Display title
    content: str              # Section content (Markdown)
    is_complete: bool = False # Completeness flag
    last_edited_at: datetime | None = None
    last_edited_by: str | None = None

class PlanActivationRecord(BaseModel):
    incident_id: str
    activated_at: datetime
    activated_by: str        # Incident Controller ID
    deactivated_at: datetime | None = None
    deactivation_reason: str | None = None

class PlanAmendment(BaseModel):
    amendment_number: int
    description: str
    amended_by: str
    amended_at: datetime
    sections_affected: list[str] = Field(default_factory=list)
```

**27 plan section slugs** (FR-002):
`contents_glossary`, `authority`, `security_rating`, `review_schedule`, `amendment_register`, `distribution_list`, `aim_objectives`, `legislative_context`, `plan_context`, `plan_scope`, `leadership_structures`, `roles_responsibilities`, `financial_management`, `communication_systems`, `information_management`, `resource_capability`, `prevention_mitigation`, `preparedness`, `public_education`, `plan_scheduling_activation`, `response_arrangements`, `emergency_control_facilities`, `public_information_warnings`, `evacuation_management`, `relief_arrangements`, `recovery_arrangements`, `exercise_schedule`

**Validation rules**:
- `lifecycle_state` transitions enforced via external state machine module (R-002), not in the model validator.
- `endorsed_by` and `endorsed_at` required when `lifecycle_state == "endorsed"` or any subsequent state.
- `hazard_types` must be non-empty.
- `planning_principles_checklist` keys must be from the defined set of 8 principles.

**State transitions** (FR-006):

| From | To | Authorization | Condition |
|------|----|--------------|-----------|
| `draft` | `in_consultation` | Planning Officer | — |
| `in_consultation` | `under_review` | Planning Officer | — |
| `in_consultation` | `draft` | Planning Officer | Major rework required |
| `under_review` | `endorsed` | Designated Authority | Per hierarchy level |
| `under_review` | `draft` | Designated Authority | Rejected — returns for revision |
| `endorsed` | `activated` | Incident Controller | Linked to live incident only |
| `activated` | `post_event_review` | IC or Planning Officer | After incident concludes |
| `post_event_review` | `draft` | Planning Officer | Creates new version; original → Superseded |
| Any non-terminal | `superseded` | System | When newer version reaches Endorsed |

**Cosmos container**: `emergency-plans`, partition key: `/region_id`

---

### N-002: `PlanningProcessRecord`

**File**: `packages/domain/src/domain/models/planning_process_record.py`  
**FRs**: FR-001  
**Research**: R-001

**Fields**:

| Field | Type | Default | FR | Description |
|-------|------|---------|-----|-------------|
| `record_id` | `str` | — | — | Unique identifier |
| `plan_id` | `str` | — | FR-001 | Associated emergency plan |
| `current_step` | `Literal[1, 2, 3, 4, 5, 6, 7, 8, 9]` | `1` | FR-001 | Current AIDR planning process step |
| `step_status` | `dict[int, StepCompletion]` | `{}` | FR-001 | Completion status for each step (keyed 1-9) |
| `project_team` | `list[TeamMember]` | `[]` | FR-001 | Step 2: project team membership |
| `stakeholder_engagement_log` | `list[EngagementEntry]` | `[]` | FR-001 | Step 3: consultation records |
| `risk_assessment_id` | `str \| None` | `None` | FR-003 | Link to risk assessment (step 4) |
| `endorsement_approvals` | `list[EndorsementApproval]` | `[]` | FR-006 | Step 7: endorsement records |
| `created_at` | `datetime` | `now(UTC)` | — | Creation timestamp |
| `updated_at` | `datetime \| None` | `None` | — | Last modification timestamp |

**Nested models**:

```python
class StepCompletion(BaseModel):
    step_number: int   # 1-9
    step_name: str     # e.g., "Establish project plan"
    is_complete: bool = False
    completed_at: datetime | None = None
    completed_by: str | None = None
    notes: str = ""

class TeamMember(BaseModel):
    name: str
    role: str
    organisation: str
    joined_at: datetime

class EngagementEntry(BaseModel):
    stakeholder: str
    method: Literal["workshop", "survey", "interview", "public_meeting", "written_submission", "other"]
    date: datetime
    summary: str
    attendee_count: int | None = None

class EndorsementApproval(BaseModel):
    authority_name: str
    authority_role: str
    approved: bool
    approved_at: datetime | None = None
    comments: str = ""
```

**Nine AIDR planning process steps** (FR-001):
1. Establish project plan
2. Establish project team
3. Communicate and consult
4. Understand risks and consequences
5. Develop strategies and arrangements
6. Document and trial
7. Endorse the plan
8. Implement and exercise
9. Monitor and review

**Cosmos container**: Embedded in `emergency-plans` container as a sub-document of the plan, or stored alongside with `plan_id` as a queryable field.

---

### N-003: `MEFramework`

**File**: `packages/domain/src/domain/models/me_framework.py`  
**FRs**: FR-008–014  
**Research**: R-005, R-009

```python
# Type aliases
EvaluationDomain = Literal[
    "governance", "community_engagement", "effectiveness",
    "efficiency", "implementation",
]
RecoveryDomain = Literal["overarching", "social", "economic", "built", "natural"]
ObjectiveType = Literal["sustainability", "resilience"]
```

**Fields**:

| Field | Type | Default | FR | Description |
|-------|------|---------|-----|-------------|
| `framework_id` | `str` | — | — | Unique identifier |
| `incident_id` | `str` | — | FR-008 | Associated recovery incident |
| `program_name` | `str` | — | FR-008 | Recovery program name |
| `affected_community_definition` | `str` | `""` | FR-008 | Description of the affected community |
| `selected_outcomes` | `list[SelectedOutcome]` | `[]` | FR-009 | Outcomes chosen from AIDR catalogue |
| `program_logic_id` | `str \| None` | `None` | FR-010 | Link to program logic model |
| `active_evaluation_domains` | `list[EvaluationDomain]` | all 5 | FR-011 | Active KEQ domains for this framework |
| `standards_of_success` | `list[SuccessStandard]` | `[]` | FR-012 | Thresholds for selected outcomes |
| `indicator_collection_schedule` | `list[CollectionSchedule]` | `[]` | FR-013 | Data collection plan |
| `evaluation_reports` | `list[str]` | `[]` | FR-014 | IDs of generated evaluation reports |
| `status` | `Literal["configuring", "active", "evaluation_complete", "closed"]` | `"configuring"` | — | Framework lifecycle status |
| `created_at` | `datetime` | `now(UTC)` | — | Creation timestamp |
| `created_by` | `str` | `""` | — | Recovery Coordinator ID |
| `updated_at` | `datetime \| None` | `None` | — | Last modification timestamp |

**Nested models**:

```python
class SelectedOutcome(BaseModel):
    catalogue_outcome_id: str       # e.g., "aidr:social:community-health-levels"
    domain: RecoveryDomain
    objective_type: ObjectiveType
    community_restatement: str | None = None  # FR-022: community-specific restatement
    is_active: bool = True

class SuccessStandard(BaseModel):
    catalogue_outcome_id: str
    indicator_id: str               # catalogue_indicator_id
    threshold_value: float
    threshold_operator: Literal["gte", "lte", "eq", "between"]
    threshold_upper: float | None = None  # For "between" operator
    stakeholder_label: str = "primary"    # FR edge case: multiple stakeholder standards
    notes: str = ""

class CollectionSchedule(BaseModel):
    indicator_id: str
    frequency: Literal["weekly", "fortnightly", "monthly", "quarterly", "annually"]
    next_due_date: datetime
    last_collected_at: datetime | None = None
    is_overdue: bool = False
```

**Validation rules**:
- `active_evaluation_domains` must be a subset of the 5 defined KEQ domains.
- `selected_outcomes` must reference valid catalogue outcome IDs (validated at service layer, not model layer, since it requires Cosmos lookup).
- `standards_of_success` must reference outcomes in `selected_outcomes`.

**Cosmos container**: `recovery-programmes`, partition key: `/incident_id`

---

### N-004: `ProgramLogicModel`

**File**: `packages/domain/src/domain/models/program_logic_model.py`  
**FRs**: FR-010  
**Research**: R-005

**Fields**:

| Field | Type | Default | FR | Description |
|-------|------|---------|-----|-------------|
| `model_id` | `str` | — | — | Unique identifier |
| `framework_id` | `str` | — | FR-010 | Associated M&E framework |
| `model_type` | `Literal["ex_ante", "ex_post"]` | `"ex_ante"` | FR-010 | Planning-stage or evaluation-stage |
| `resources_inputs` | `list[LogicElement]` | `[]` | FR-010 | What the program invests |
| `activities` | `list[LogicElement]` | `[]` | FR-010 | What the program does |
| `outputs` | `list[LogicElement]` | `[]` | FR-010 | Direct products of activities |
| `intermediate_outcomes` | `list[LogicElement]` | `[]` | FR-010 | Short-to-medium term changes |
| `final_outcomes` | `list[FinalOutcome]` | `[]` | FR-010 | Long-term sustainability and resilience outcomes |
| `outcome_chain_links` | `list[OutcomeChainLink]` | `[]` | FR-010 | Relationships between elements |
| `timeline_months` | `int \| None` | `None` | FR-010 | Projected program timeline |
| `created_at` | `datetime` | `now(UTC)` | — | Creation timestamp |
| `updated_at` | `datetime \| None` | `None` | — | Last modification timestamp |

**Nested models**:

```python
class LogicElement(BaseModel):
    element_id: str
    description: str
    catalogue_activity_id: str | None = None  # Link to AIDR catalogue activity
    domain: RecoveryDomain | None = None

class FinalOutcome(BaseModel):
    element_id: str
    description: str
    catalogue_outcome_id: str | None = None
    objective_type: ObjectiveType  # sustainability or resilience
    domain: RecoveryDomain

class OutcomeChainLink(BaseModel):
    from_element_id: str
    to_element_id: str
    link_type: Literal["produces", "contributes_to", "enables", "depends_on"]
```

**Validation rules**:
- `final_outcomes` must distinguish sustainability and resilience objectives (FR-023).
- `outcome_chain_links` must reference valid `element_id` values from the model's elements.

**Cosmos container**: `recovery-programmes`, partition key: `/incident_id` (via framework's incident_id)

---

### N-005: Recovery Catalogue Models (`RecoveryOutcome`, `CatalogueActivity`, `CatalogueIndicator`)

**File**: `packages/domain/src/domain/models/recovery_outcome.py`  
**FRs**: FR-015–024  
**Research**: R-004

```python
RecoveryDomain = Literal["overarching", "social", "economic", "built", "natural"]
ObjectiveType = Literal["sustainability", "resilience"]
```

#### `RecoveryOutcome`

| Field | Type | Default | FR | Description |
|-------|------|---------|-----|-------------|
| `outcome_id` | `str` | — | FR-015 | Hierarchical ID: `aidr:{domain}:{outcome-slug}` |
| `domain` | `RecoveryDomain` | — | FR-015 | Recovery domain |
| `objective_type` | `ObjectiveType` | — | FR-023 | Sustainability or resilience |
| `title` | `str` | — | FR-015 | Outcome title |
| `description` | `str` | `""` | FR-015 | Detailed description |
| `activity_ids` | `list[str]` | `[]` | FR-020 | Associated catalogue activity IDs |
| `indicator_ids` | `list[str]` | `[]` | FR-021 | Associated catalogue indicator IDs |
| `has_developed_activities` | `bool` | `True` | Assumptions | False when "no activities or indicators were developed" per source |

#### `CatalogueActivity`

| Field | Type | Default | FR | Description |
|-------|------|---------|-----|-------------|
| `activity_id` | `str` | — | FR-020 | Hierarchical ID: `aidr:{domain}:{outcome-slug}:act:{index}` |
| `outcome_id` | `str` | — | FR-020 | Parent outcome ID |
| `domain` | `RecoveryDomain` | — | FR-020 | Recovery domain |
| `title` | `str` | — | FR-020 | Activity title |
| `description` | `str` | `""` | FR-020 | Detailed description |

#### `CatalogueIndicator`

| Field | Type | Default | FR | Description |
|-------|------|---------|-----|-------------|
| `indicator_id` | `str` | — | FR-021 | Hierarchical ID: `aidr:{domain}:{outcome-slug}:ind:{index}` |
| `outcome_id` | `str` | — | FR-021 | Parent outcome ID |
| `domain` | `RecoveryDomain` | — | FR-021 | Recovery domain |
| `title` | `str` | — | FR-021 | Indicator title |
| `description` | `str` | `""` | FR-021 | Detailed description |
| `data_collection_methodology` | `str \| None` | `None` | FR-021 | Methodology guidance where available |
| `indicator_type` | `Literal["quantitative", "qualitative", "both"]` | `"quantitative"` | FR-021 | Indicator measurement type |

**Catalogue scale** (from spec):
- ~7 overarching outcomes
- ~24 social outcomes
- ~19 economic outcomes
- ~5 built outcomes
- ~6 natural outcomes
- ~200 activities total
- ~300 indicators total

**ID scheme examples**:
- Outcome: `aidr:social:community-health-levels`
- Activity: `aidr:social:community-health-levels:act:1`
- Indicator: `aidr:social:community-health-levels:ind:1`

**Cosmos container**: `recovery-catalogue`, partition key: `/domain`

**Note**: All catalogue entries are **immutable reference data** seeded at deployment. User-defined extensions are stored as separate documents with a `custom:` prefix in their IDs (e.g., `custom:social:local-wellbeing-index`).

---

### N-006: `EvaluationReport`

**File**: `packages/domain/src/domain/models/evaluation_report.py`  
**FRs**: FR-014, SC-009  
**Research**: R-009

**Fields**:

| Field | Type | Default | FR | Description |
|-------|------|---------|-----|-------------|
| `report_id` | `str` | — | — | Unique identifier |
| `framework_id` | `str` | — | FR-014 | Associated M&E framework |
| `incident_id` | `str` | — | — | Incident ID (for partition key) |
| `evaluation_period_start` | `datetime` | — | FR-014 | Evaluation period start |
| `evaluation_period_end` | `datetime` | — | FR-014 | Evaluation period end |
| `domain_findings` | `dict[str, DomainFinding]` | `{}` | FR-011, SC-009 | Findings keyed by evaluation domain |
| `summary` | `str` | `""` | FR-027 | Natural-language executive summary |
| `recommendations` | `list[Recommendation]` | `[]` | FR-014 | Actionable recommendations |
| `dissemination_records` | `list[DisseminationRecord]` | `[]` | FR-014 | Who received this report |
| `generated_by` | `Literal["manual", "ai_assisted"]` | `"manual"` | FR-025 | How the report was generated |
| `content_safety_result` | `str \| None` | `None` | FR-028 | Content safety validation outcome |
| `created_at` | `datetime` | `now(UTC)` | — | Creation timestamp |
| `created_by` | `str` | `""` | — | Creator ID |

**Nested models**:

```python
class DomainFinding(BaseModel):
    evaluation_domain: EvaluationDomain
    questions_addressed: list[str]   # Standard KEQ questions
    findings: list[Finding]
    evidence_references: list[str]

class Finding(BaseModel):
    finding_text: str
    evidence_summary: str
    severity: Literal["positive", "neutral", "concern", "critical"]
    related_indicator_ids: list[str] = Field(default_factory=list)

class Recommendation(BaseModel):
    text: str
    priority: Literal["high", "medium", "low"]
    target_domain: RecoveryDomain | None = None
    suggested_activity_ids: list[str] = Field(default_factory=list)  # From AIDR catalogue

class DisseminationRecord(BaseModel):
    recipient: str
    recipient_type: Literal["government", "community", "ngo", "research"]
    disseminated_at: datetime
    format: Literal["pdf", "json", "presentation"]
```

**Validation rules**:
- `domain_findings` keys must be valid `EvaluationDomain` values.
- If `generated_by == "ai_assisted"`, `content_safety_result` must be set.
- `evaluation_period_end` must be after `evaluation_period_start`.

**Cosmos container**: `recovery-programmes`, partition key: `/incident_id`

---

## Cosmos DB Container Summary

| Container | Partition Key | Models Stored | Autoscale Max RU/s | Composite Indexes |
|-----------|--------------|---------------|--------------------|--------------------|
| `emergency-plans` (NEW) | `/region_id` | EmergencyPlan, PlanningProcessRecord | 1000 | `lifecycle_state` + `updated_at`, `hierarchy_level` + `lifecycle_state` |
| `recovery-programmes` (NEW) | `/incident_id` | MEFramework, ProgramLogicModel, EvaluationReport | 1000 | `status` + `created_at`, `incident_id` + `status` |
| `recovery-catalogue` (NEW) | `/domain` | RecoveryOutcome, CatalogueActivity, CatalogueIndicator | 1000 | `domain` + `objective_type` |
| `recovery` (EXISTING) | `/incident_id` | RecoveryEnvironmentTracker, RecoveryIndicator (extended) | 1000 | (unchanged) |

---

## Configurable Parameters

| Parameter | Environment Variable | Default | Unit | Description |
|-----------|---------------------|---------|------|-------------|
| Plan generation timeout | `PLAN_GENERATION_TIMEOUT_SECONDS` | `15` | seconds | NFR-001 max time for plan assembly |
| AI analysis timeout | `AI_ANALYSIS_TIMEOUT_SECONDS` | `30` | seconds | NFR-004 max time for cross-domain analysis |
| Plan review reminder days | `PLAN_REVIEW_REMINDER_DAYS` | `365` | days | Default interval for plan review reminders |
| Indicator staleness threshold | `INDICATOR_STALENESS_DAYS` | `7` | days | Days before an indicator shows staleness warning |
| Max concurrent plans | `MAX_CONCURRENT_PLANS` | `20` | count | NFR-005 concurrent active emergency plans |
| Max concurrent ME frameworks | `MAX_CONCURRENT_ME_FRAMEWORKS` | `10` | count | NFR-006 concurrent M&E frameworks |
| Catalogue cache TTL | `CATALOGUE_CACHE_TTL_SECONDS` | `3600` | seconds | Cache TTL for immutable catalogue data |
| K-anonymity minimum | `K_ANONYMITY_MINIMUM` | `10` | count | NFR-009 minimum population for sensitive social data |
