# Data Model: AIDR Guidance Integration

**Feature**: 018-aidr-guidance-integration  
**Date**: 2025-07-20  
**Depends on**: [research.md](./research.md) decisions R-001 through R-013

---

## Overview

This feature introduces **4 new domain models**, **1 new context model**, and **3 extended domain models**. All models follow the existing Pydantic `BaseModel` convention in `packages/domain/src/domain/models/`. All use `Literal[...]` unions for constrained types (no `Enum` classes), string IDs, and `Field(default_factory=...)` for mutable defaults.

---

## Extended Models

### E-001: `Incident` (extend existing)

**File**: `packages/domain/src/domain/models/incident.py`  
**FRs**: FR-050 (pprr_phase), FR-051 (incident_type), FR-015 (incident_level), R-011

**Current fields** (preserved unchanged):
- `incident_id: str`
- `title: str`
- `incident_type: Literal["bushfire", "flood", "cyclone", "storm", "earthquake", "other"]`
- `status: Literal["monitoring", "active", "stabilising", "recovery", "closed", "rehearsal"]`
- `severity: Literal["advisory", "watch", "warning", "emergency"]`
- `affected_jurisdiction_ids: list[str]`
- `participating_organisation_ids: list[str]`
- `owning_framework_ids: list[str]`
- `started_at: datetime`

**New fields**:

| Field | Type | Default | FR | Description |
|-------|------|---------|-----|-------------|
| `pprr_phase` | `Literal["prevention", "preparedness", "response", "recovery"] \| None` | `None` | FR-050 | Current PPRR lifecycle phase. Independent of `status`. `None` for incidents created before AIDR integration. |
| `incident_level` | `Literal[1, 2, 3]` | `1` | FR-015, R-011 | AIIMS incident level. Level 1 = local/single-agency. Level 2 = multi-agency/shared COP. Level 3 = major/state-wide/NCM. |

**Extended `incident_type`**:
```python
Literal[
    "bushfire", "flood", "cyclone", "storm", "earthquake",
    "tsunami", "extreme_heat", "pandemic", "other"  # ← 3 new values per FR-051
]
```

**Validation rules**:
- `pprr_phase` is optional to maintain backward compatibility with existing incidents.
- `incident_level` defaults to 1 for all new incidents.
- No automatic mapping between `severity`, `pprr_phase`, and `incident_level` — they are independent axes (spec clarification Pass 2).

**State transitions**:
- `pprr_phase` transitions are recorded as `TimelineEvent` entries (FR-053).
- `incident_level` changes are recorded as `TimelineEvent` entries.
- Level 2+ closure triggers lessons capture (FR-038).

---

### E-002: `PublicAlert` (extend existing)

**File**: `packages/domain/src/domain/models/public_alert.py`  
**FRs**: FR-048, FR-001–005

**Current fields** (preserved unchanged):
- `alert_id`, `incident_id`, `status`, `approval_mode`, `audience_segments`, `languages`, `accessibility_attributes`, `channel_set`, `content_blocks`, `published_at`, `generation_method`, `model_deployment_id`, `content_safety_result`

**New fields**:

| Field | Type | Default | FR | Description |
|-------|------|---------|-----|-------------|
| `warning_tier` | `Literal["advice", "watch_and_act", "emergency_warning"] \| None` | `None` | FR-001, FR-048 | AWS three-tier level. `None` for non-AWS alerts and all-clear notifications. |
| `colour_code` | `Literal["yellow", "orange", "red"] \| None` | `None` | FR-001, FR-048 | AWS tier visual colour. Derived from `warning_tier`. |
| `hazard_icon` | `Literal["cyclone", "fire", "flood", "heat", "storm", "other"] \| None` | `None` | FR-003, FR-048 | Hazard icon type for graphical output. |
| `action_statement` | `str \| None` | `None` | FR-002, FR-048 | AWS nested-model action statement. Call-to-action text for the public. |
| `superseded_warning_id` | `str \| None` | `None` | FR-004, FR-048, R-004 | `alert_id` of the warning this alert supersedes. Forms a singly-linked warning chain. |
| `tier_skip_justification` | `str \| None` | `None` | Edge case | If the warning skipped tiers (e.g., straight to Emergency Warning for earthquake), the justification. |
| `is_all_clear` | `bool` | `False` | FR-005 | Whether this alert is an all-clear notification closing a warning chain. |
| `warning_principles_checklist` | `dict[str, bool]` | `{}` | FR-006, SC-006 | Map of the 10 warning principles to pass/fail status. Keys: `life_saving`, `empowering`, `trusted`, `risk_scaled`, `timely_targeted`, `impact_conveying`, `action_calling`, `clearly_communicated`, `accessible`, `bigger_picture`. |

**Validation rules**:
- If `warning_tier` is set, `colour_code` MUST match: advice→yellow, watch_and_act→orange, emergency_warning→red.
- If `warning_tier` is set, `action_statement` MUST be non-empty.
- If `is_all_clear` is True, `warning_tier` MUST be None (all-clear is not a tiered warning).
- `superseded_warning_id`, if set, MUST reference an existing published alert.
- `warning_principles_checklist`, if non-empty, MUST have exactly 10 keys matching the defined principle names.

**Warning chain semantics** (R-004):
- Chains are singly-linked via `superseded_warning_id`.
- De-escalation: new lower-tier warning supersedes higher-tier warning.
- All-clear: `is_all_clear = True` warning supersedes last active warning in chain.
- Multi-hazard: independent chains per hazard type (same incident may have multiple active chains).

---

### E-003: `HandoffChainDefinition` (extend existing)

**File**: `packages/domain/src/domain/models/handoff_chain.py`  
**FRs**: FR-054

**Extended `SignalCategory`**:
```python
SignalCategory = Literal[
    "weather", "hydrology", "fire", "geohazard",
    "infrastructure", "community_report", "social_report", "resource_status",
    "recovery_assessment", "lessons_capture"  # ← 2 new values per FR-054
]
```

**New handoff chain patterns** (FR-054):
1. **Recovery-phase handoff**: Risk Assessment → recovery-configured agents. Uses `category_filter = ["recovery_assessment"]`.
2. **Lessons-capture handoff**: Incident closure (Level 2+) → lessons service trigger. Uses `category_filter = ["lessons_capture"]`.

---

## New Models

### N-001: `AiimsRoleAssignment`

**File**: `packages/domain/src/domain/models/aiims_role_assignment.py`  
**FRs**: FR-013, FR-014, FR-049, R-005

```python
AiimsFunction = Literal[
    "control", "intelligence", "planning",
    "operations", "logistics", "public_information"
]

class AiimsRoleAssignment(BaseModel):
    assignment_id: str
    incident_id: str
    agent_identifier: str          # e.g., "monitoring", "risk_assessment", "evacuation"
    aiims_function: AiimsFunction
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    assigned_by: str               # user or system identifier
    unassigned_at: datetime | None = None
    is_active: bool = True
    delegation_source_id: str | None = None  # if this is a delegated role
    notes: str = ""
```

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `assignment_id` | `str` | Unique identifier (format: `aiims-{uuid}`) |
| `incident_id` | `str` | The incident this assignment applies to |
| `agent_identifier` | `str` | The agent assigned to this AIIMS function |
| `aiims_function` | `AiimsFunction` | One of the six AIIMS functions |
| `assigned_at` | `datetime` | When the assignment was made |
| `assigned_by` | `str` | Who made the assignment (user ID or "system") |
| `unassigned_at` | `datetime \| None` | When the assignment ended (None = still active) |
| `is_active` | `bool` | Whether this assignment is currently active |
| `delegation_source_id` | `str \| None` | If delegated, the `assignment_id` of the original assignment |
| `notes` | `str` | Free-text notes for audit |

**Validation rules**:
- Each agent may hold exactly one `aiims_function` per incident (FR-013). Enforced at service layer, not model layer (requires cross-record check).
- All six AIIMS functions MUST have at least one active assignment for Level 3 incidents. Advisory for Level 1-2. Enforced at service layer.
- `is_active = True` requires `unassigned_at is None`.

**Relationships**:
- References `Incident.incident_id`.
- Complements `OperatingFramework` (framework definition) and `FrameworkAssignment` (framework-to-org mapping).
- Queried by the COP display (FR-014) to show current AIIMS structure.

---

### N-002: `EvacuationStage`

**File**: `packages/domain/src/domain/models/evacuation_stage.py`  
**FRs**: FR-018–025, R-010

```python
EvacStageName = Literal[
    "decision", "warning", "withdrawal", "shelter",
    "return", "shelter_in_place", "completed"
]

EvacuationType = Literal["pre_warned", "immediate"]
EvacuationApproach = Literal["directed", "recommended", "self_initiated"]
EvacuationScope = Literal["total", "partial", "phased"]

class EvacuationStage(BaseModel):
    stage_id: str
    incident_id: str
    evacuation_plan_id: str        # links to existing EvacuationPlan
    current_stage: EvacStageName
    previous_stage: EvacStageName | None = None
    stage_started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    stage_ended_at: datetime | None = None
    re_entry_count: int = 0

    # Decision stage fields (FR-019)
    decision_authority: str | None = None
    decision_rationale: str | None = None
    evacuation_type: EvacuationType | None = None
    evacuation_approach: EvacuationApproach | None = None
    evacuation_scope: EvacuationScope | None = None

    # Warning stage fields (FR-020)
    warning_alert_ids: list[str] = Field(default_factory=list)
    evacuation_timeframe_minutes: int | None = None

    # Withdrawal stage fields (FR-021)
    population_total: int | None = None
    population_moved: int | None = None
    vulnerable_population_status: dict[str, str] = Field(default_factory=dict)

    # Shelter stage fields (FR-022)
    active_shelter_ids: list[str] = Field(default_factory=list)
    total_shelter_capacity: int | None = None
    current_shelter_occupancy: int | None = None

    # Return stage fields (FR-023)
    safety_conditions_met: bool = False
    safety_certifier: str | None = None
    return_completion_rate: float | None = None

    # Shelter-in-place fields (FR-024)
    shelter_in_place_rationale: str | None = None
    shelter_in_place_monitoring_interval_minutes: int | None = None

    # Audit
    authorized_by: str | None = None
    transition_rationale: str | None = None
```

**Valid state transitions** (R-010):
```
decision → warning → withdrawal → shelter → return → completed
decision → shelter_in_place → decision (re-evaluation)
withdrawal → decision (route impassable re-entry)
shelter → decision (conditions change re-entry)
warning → decision (new hazard data re-entry)
```

**Validation rules**:
- Forward transitions follow the defined sequence.
- Re-entry transitions increment `re_entry_count`.
- Decision stage requires `decision_authority` and `decision_rationale` (FR-019).
- Shelter-in-place requires `shelter_in_place_rationale` (FR-024).
- Every transition creates a `TimelineEvent`.

**Relationships**:
- References `Incident.incident_id`.
- References existing `EvacuationPlan.plan_id` from `apps/agents/evacuation/models.py`.
- `warning_alert_ids` reference `PublicAlert.alert_id` records.
- `vulnerable_population_status` keys are population group names from Constitution §VI-C.

---

### N-003: `RecoveryEnvironmentTracker`

**File**: `packages/domain/src/domain/models/recovery_environment_tracker.py`  
**FRs**: FR-032–037, SC-005, R-003, R-008, R-012

```python
RecoveryEnvironment = Literal["social", "built", "economic", "natural"]
IndicatorUpdateSource = Literal["manual", "automated", "imported"]
DataClassification = Literal["public", "official", "sensitive"]

class RecoveryIndicator(BaseModel):
    indicator_name: str
    environment: RecoveryEnvironment
    value: float | None = None
    unit: str = ""
    baseline_value: float | None = None
    target_value: float | None = None
    last_updated_at: datetime | None = None
    update_source: IndicatorUpdateSource = "manual"
    data_source_id: str | None = None    # for future automated collection
    population_coverage: int | None = None  # k-anonymity enforcement for social
    data_classification: DataClassification = "public"
    is_regressed: bool = False
    regression_cause: str | None = None
    linked_alert_id: str | None = None   # for community-response feedback loop (FR-012)

class RecoveryEnvironmentTracker(BaseModel):
    tracker_id: str
    incident_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
    recovery_principles_applied: list[str] = Field(default_factory=list)
    community_input_summary: str = ""
    indicators: list[RecoveryIndicator] = Field(default_factory=list)
    status: Literal["active", "completed", "suspended"] = "active"
```

**AIDR-defined indicators** (SC-005, 21 total):

| Environment | Indicators | Count |
|---|---|---|
| Social | wealth, employment, amenity, health, social_issues, social_belonging, recreation_leisure | 7 |
| Built | essential_services, community_infrastructure, transport_networks, property_housing, planning_building_compliance | 5 |
| Economic | personal_income, business_premises, tourism, workforce_availability, productive_land | 5 |
| Natural | air_quality, water_quality, land_soil_health, biodiversity | 4 |

**Validation rules**:
- Social environment indicators with `data_classification = "sensitive"` MUST have `population_coverage ≥ 10` (NFR-014, R-012).
- `recovery_principles_applied` values MUST be from: `understand_context`, `recognise_complexity`, `community_led`, `coordinate_activities`, `communicate_effectively`, `build_capacity`.
- Regression detection: if `value < baseline_value` (or direction-specific comparison), `is_regressed` is set to `True` and `regression_cause` is required.

**Relationships**:
- References `Incident.incident_id`.
- `linked_alert_id` on indicators references `PublicAlert.alert_id` for Total Warning System feedback loop.
- `data_source_id` references `DataSource.source_id` for future automated collection.

---

### N-004: `Lesson`

**File**: `packages/domain/src/domain/models/lesson.py`  
**FRs**: FR-038–042, FR-052, R-007

```python
LessonStatus = Literal["identified", "in_progress", "resolved", "rejected"]
LessonSeverity = Literal["low", "medium", "high", "critical"]

class Lesson(BaseModel):
    lesson_id: str
    incident_id: str | None = None
    scenario_run_id: str | None = None     # for exercise-originated lessons (FR-052)
    title: str
    description: str
    aiims_function: Literal[
        "control", "intelligence", "planning",
        "operations", "logistics", "public_information"
    ] | None = None                        # FR-039 categorisation
    pprr_phase: Literal[
        "prevention", "preparedness", "response", "recovery"
    ] | None = None                        # FR-039 categorisation
    severity: LessonSeverity = "medium"    # FR-039 categorisation
    status: LessonStatus = "identified"
    assigned_to: str | None = None         # FR-041
    target_resolution_date: datetime | None = None  # FR-041
    resolved_at: datetime | None = None
    resolution_reference: str | None = None  # PR URL, config change ref, etc.
    resolution_notes: str = ""
    originating_event_id: str | None = None  # TimelineEvent or ExerciseReport id
    is_contradictory: bool = False           # Edge case: contradicts existing config
    contradicts_config_ref: str | None = None
    escalation_approved_by: str | None = None  # For contradictory lessons
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str = ""
    tags: list[str] = Field(default_factory=list)
```

**Validation rules**:
- At least one of `incident_id` or `scenario_run_id` MUST be set (a lesson must originate from something).
- If `status = "resolved"`, `resolved_at` and `resolution_reference` MUST be non-None.
- If `is_contradictory = True`, `status` cannot transition to `resolved` without `escalation_approved_by` being set (edge case: contradictory lesson requires escalated review).
- `target_resolution_date`, if set, is tracked for SC-007 (90% closure within 90 days).

**Relationships**:
- `incident_id` references `Incident.incident_id`.
- `scenario_run_id` references `ExerciseReport.scenario_run_id` (FR-052).
- `resolution_reference` is a free-text reference (typically a PR URL or config path).
- `originating_event_id` references `TimelineEvent.event_id`.

---

### N-005: `PprrPhaseContext`

**File**: `packages/domain/src/domain/models/pprr_phase_context.py`  
**FRs**: FR-050 (non-incident PPRR), R-001

```python
class PprrPhaseContext(BaseModel):
    context_id: str
    context_type: Literal["region", "scenario"]
    context_reference_id: str      # jurisdiction_id or scenario_template_id
    pprr_phase: Literal["prevention", "preparedness"]
    activated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    activated_by: str
    deactivated_at: datetime | None = None
    transitioned_to_incident_id: str | None = None  # when phase moves to an actual incident
    notes: str = ""
```

**Validation rules**:
- `pprr_phase` is restricted to `"prevention"` or `"preparedness"` — Response and Recovery require an active `Incident`.
- When `transitioned_to_incident_id` is set, `deactivated_at` MUST also be set.
- `context_reference_id` MUST reference a valid `Jurisdiction.jurisdiction_id` (when `context_type = "region"`) or `ScenarioTemplate.template_id` (when `context_type = "scenario"`).

**Relationships**:
- `context_reference_id` references `Jurisdiction` or `ScenarioTemplate`.
- `transitioned_to_incident_id` references `Incident.incident_id` when a preparedness context becomes a real incident.

---

## Extended `TimelineEvent` Payload Schemas

**File**: `packages/domain/src/domain/models/timeline_event.py`  
**FR**: FR-053

The `TimelineEvent` model itself is not changed. The `payload: dict[str, object]` field accommodates new event types via structured payload schemas:

### PPRR Phase Transition Payload (FR-053)

```python
# event_type = "system"
# payload structure:
{
    "action": "pprr_phase_transition",
    "source_phase": "response",        # Literal PPRR phase
    "target_phase": "recovery",        # Literal PPRR phase
    "transition_rationale": "Flood waters receded...",
    "authorising_user": "user-id-123",
    "overlap_active": True,            # Are both phases active simultaneously?
    "overlap_end_expected_at": "2025-08-01T00:00:00Z"  # optional
}
```

### Incident Level Change Payload

```python
# event_type = "system"
# payload structure:
{
    "action": "incident_level_change",
    "previous_level": 1,
    "new_level": 2,
    "rationale": "Multi-agency involvement required...",
    "authorising_user": "user-id-123"
}
```

### Evacuation Stage Transition Payload

```python
# event_type = "system"
# payload structure:
{
    "action": "evacuation_stage_transition",
    "evacuation_plan_id": "ep-...",
    "previous_stage": "withdrawal",
    "new_stage": "decision",        # re-entry
    "is_re_entry": True,
    "re_entry_count": 1,
    "rationale": "Route Alpha impassable due to flooding",
    "authorising_user": "user-id-123"
}
```

### Lessons Capture Trigger Payload

```python
# event_type = "system"
# payload structure:
{
    "action": "lessons_capture_triggered",
    "trigger_source": "incident_closure",  # or "exercise_completion"
    "incident_level": 2,
    "incident_id": "inc-...",
    "scenario_run_id": null               # set for exercises
}
```

---

## Entity Relationship Diagram (textual)

```
Incident (extended)
├── incident_level: 1|2|3
├── pprr_phase: prevention|preparedness|response|recovery
├── incident_type: +tsunami, +extreme_heat, +pandemic
│
├── 1:N → AiimsRoleAssignment (per-incident agent-to-function mapping)
├── 1:N → EvacuationStage (five-stage lifecycle per evacuation)
├── 1:N → RecoveryEnvironmentTracker (21 indicators across 4 environments)
├── 1:N → Lesson (lessons captured from this incident)
├── 1:N → PublicAlert (extended with AWS warning fields)
│           ├── warning_tier, colour_code, hazard_icon
│           ├── action_statement, superseded_warning_id
│           └── warning_principles_checklist
└── 1:N → TimelineEvent (extended payload schemas for PPRR/AIIMS/evacuation)

PprrPhaseContext (non-incident PPRR phases)
├── context_type: region|scenario
├── pprr_phase: prevention|preparedness only
└── transitioned_to_incident_id → Incident (when phase becomes real incident)

HandoffChainDefinition (extended)
└── SignalCategory: +recovery_assessment, +lessons_capture

EvacuationStage
├── evacuation_plan_id → EvacuationPlan (existing, in evacuation agent)
├── warning_alert_ids → PublicAlert[] (evacuation warnings)
└── vulnerable_population_status: dict per group

RecoveryEnvironmentTracker
├── indicators[].linked_alert_id → PublicAlert (feedback loop)
└── indicators[].data_source_id → DataSource (future automation)

Lesson
├── incident_id → Incident (or null for exercise-only)
├── scenario_run_id → ExerciseReport (exercise linkage per FR-052)
└── originating_event_id → TimelineEvent
```

---

## Model Registration

All new models must be exported from `packages/domain/src/domain/models/__init__.py` (or equivalent module re-export file). The existing pattern exports models directly from the models package.

New exports:
- `AiimsRoleAssignment`, `AiimsFunction`
- `EvacuationStage`, `EvacStageName`, `EvacuationType`, `EvacuationApproach`, `EvacuationScope`
- `RecoveryEnvironmentTracker`, `RecoveryIndicator`, `RecoveryEnvironment`
- `Lesson`, `LessonStatus`, `LessonSeverity`
- `PprrPhaseContext`
