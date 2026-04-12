# Data Model: Automated Demo Script

**Feature**: 016-automated-demo-script
**Date**: 2026-04-12

## Overview

The demo script introduces lightweight orchestration-layer models that wrap the existing domain models. These are **script-internal only** — they do not modify or extend the domain model layer in `packages/domain/`. All models are Python dataclasses or Pydantic `BaseModel` subclasses defined within `scripts/demo.py`.

## Entity Definitions

### DemoRun

A single execution of the demo script. Top-level container for all results.

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `str` | Unique run identifier, format: `demo-{YYYYMMDD}-{HHmmss}` |
| `scenario` | `str` | Scenario type: `bushfire`, `cyclone`, `flood` |
| `status` | `str` | Overall result: `pass` or `fail` |
| `started_at` | `datetime` | UTC timestamp when script started |
| `completed_at` | `datetime \| None` | UTC timestamp when script finished (None if interrupted) |
| `duration_seconds` | `float` | Wall-clock duration |
| `phases` | `list[PhaseResult]` | Ordered list of phase results |
| `audit_trail` | `list[DecisionRecord]` | Append-only list of all decisions |
| `handoffs` | `list[StageHandoff]` | All cross-agent handoff records |
| `alerts` | `AlertSummary` | Summary of alert generation results |

**Validation rules**:
- `run_id` must be non-empty and match `demo-\d{8}-\d{6}` pattern
- `scenario` must be one of `{"bushfire", "cyclone", "flood"}`
- `status` must be one of `{"pass", "fail"}`
- `phases` must contain exactly 7 entries on success, or 1..7 entries on failure (phases up to and including the failed phase)

**State transitions**: `status` starts as `None` (running), transitions to `pass` or `fail` once all phases complete or a failure is detected. No reverse transitions.

---

### PhaseResult

Result of a single pipeline phase execution.

| Field | Type | Description |
|-------|------|-------------|
| `phase` | `str` | Phase name: `setup`, `monitoring`, `risk_assessment`, `evacuation`, `resource_allocation`, `communication`, `summary` |
| `order` | `int` | Phase execution order (1-7) |
| `status` | `str` | Phase result: `pass`, `fail`, or `skipped` |
| `agent` | `str` | Responsible agent name or `orchestrator` for setup/summary |
| `duration_seconds` | `float` | Wall-clock duration of this phase |
| `summary` | `str` | Human-readable description of what happened |
| `details` | `dict[str, object]` | Phase-specific structured data (agent health status, response codes, etc.) |
| `error` | `str \| None` | Error message if status is `fail` |

**Validation rules**:
- `phase` must be one of the 7 defined phase names
- `order` must be 1-7, matching `phase`
- `status` must be one of `{"pass", "fail", "skipped"}`
- `error` must be set when `status == "fail"`, must be `None` when `status == "pass"`

**Phase-to-agent mapping**:

| Phase | Order | Agent |
|-------|-------|-------|
| `setup` | 1 | `orchestrator` |
| `monitoring` | 2 | `monitoring` |
| `risk_assessment` | 3 | `risk_assessment` |
| `evacuation` | 4 | `evacuation` |
| `resource_allocation` | 5 | `resource_allocation` |
| `communication` | 6 | `communication` |
| `summary` | 7 | `orchestrator` |

---

### SimulatedSignal

A seed disaster event injected into the monitoring agent. Wraps the existing `SignalEnvelope` schema.

| Field | Type | Description |
|-------|------|-------------|
| `signal_type` | `str` | Hazard category from scenario (e.g., `fire`, `weather`, `hydrology`) |
| `source_provenance` | `str` | Data source kind (e.g., `authoritative`, `sensor`) |
| `location` | `dict` | GeoJSON point: `{type, coordinates, precisionMeters}` |
| `severity` | `str` | Signal severity level |
| `timestamp` | `datetime` | Signal occurrence time |
| `confidence` | `float` | Confidence score (0.0-1.0) |
| `payload` | `dict` | Hazard-specific data payload |

**Validation rules**:
- `confidence` must be in range [0.0, 1.0]
- `location.type` must be `"Point"`
- `location.coordinates` must be `[longitude, latitude]` with valid ranges

**Relationship**: Converted to `SignalEnvelope` JSON for `POST /api/signals` request body.

---

### DecisionRecord

An audit entry for a human-in-the-loop or automated decision during the demo.

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `datetime` | UTC time of decision |
| `decision_type` | `str` | Type: `evacuation_approval`, `resource_approval`, `alert_approval`, `risk_override`, `policy_escalation` |
| `agent` | `str` | Agent that owns the decision |
| `approver_role` | `str` | Role of the simulated approver (e.g., `incident_commander`) |
| `policy` | `str` | Governance policy applied (e.g., `AIIMS_escalation`, `resource_threshold_policy`) |
| `outcome` | `str` | Decision result: `auto_approved`, `auto_rejected` |
| `supporting_data` | `list[str]` | IDs of supporting signals, assessments, or plans |

**Validation rules**:
- `outcome` must be one of `{"auto_approved", "auto_rejected"}`
- `supporting_data` must be non-empty
- `agent` must be one of the 5 agent names

**Relationship**: Appended to `DemoRun.audit_trail`. Maps to the `ApprovalDecision` domain model concept.

---

### StageHandoff

A data transfer record between two agents during the pipeline.

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `datetime` | UTC time of handoff |
| `source_agent` | `str` | Agent sending data |
| `target_agent` | `str` | Agent receiving data |
| `confidence` | `float` | Confidence level of the data being transferred |
| `payload_summary` | `str` | Human-readable description of data transferred |
| `handoff_id` | `str` | Unique handoff identifier |

**Validation rules**:
- `source_agent != target_agent`
- `confidence` in range [0.0, 1.0]
- `handoff_id` must be non-empty

**Relationship**: Wraps `AgentHandoffEvent` from `apps/agents/common/handoffs.py`. Appended to `DemoRun.handoffs`.

---

### AlertSummary

Summary of multilingual alert generation results.

| Field | Type | Description |
|-------|------|-------------|
| `total` | `int` | Number of alerts generated |
| `languages` | `list[str]` | Language codes of generated alerts |
| `safety_validated` | `bool` | Whether content safety validation passed |
| `channel_targets` | `list[str]` | Target delivery channels |

**Validation rules**:
- `total >= 0`
- `languages` should contain 6 entries on success: `["en-AU", "zh-Hans", "ar", "vi", "el", "it"]`

---

### ScenarioConfig

Configuration for a specific disaster scenario. Determines signal parameters and template selection.

| Field | Type | Description |
|-------|------|-------------|
| `scenario_type` | `str` | `bushfire`, `cyclone`, `flood` |
| `signal_category` | `str` | Signal category to inject (e.g., `fire`, `weather`, `hydrology`) |
| `hazard_type` | `str` | Alert template filter (e.g., `bushfire`, `cyclone`, `flood`) |
| `default_severity` | `str` | Default severity level for signals |
| `default_location` | `dict` | Default GeoJSON point for the scenario |
| `narration_prefix` | `str` | Human-readable scenario description for verbose mode |

**Validation rules**:
- `scenario_type` must be one of `{"bushfire", "cyclone", "flood"}`

**Predefined configurations**:

| Scenario | Category | Hazard Type | Default Location |
|----------|----------|-------------|-----------------|
| `bushfire` | `fire` | `bushfire` | `[149.13, -35.28]` (ACT region) |
| `cyclone` | `weather` | `cyclone` | `[145.77, -16.92]` (Far North QLD) |
| `flood` | `hydrology` | `flood` | `[151.2, -33.8]` (Sydney region) |

---

### SeedData

Container for all loaded seed data, passed to phase functions.

| Field | Type | Description |
|-------|------|-------------|
| `alert_templates` | `dict[str, list[dict]]` | Templates keyed by language code |
| `population` | `dict` | Parsed `sample-population.json` |
| `road_network` | `dict` | Parsed `far-north-qld-sample.json` |
| `resource_inventory` | `dict` | Parsed `sample-inventory.json` |
| `scenario_templates` | `list[dict]` | Filtered templates matching scenario hazard type |

**Validation rules**:
- All fields must be non-None after loading
- `alert_templates` must have entries for all 6 required language codes
- `scenario_templates` must have at least one matching template

## Entity Relationship Diagram

```text
DemoRun
├── phases: PhaseResult[]         (1:7 — ordered, one per pipeline phase)
├── audit_trail: DecisionRecord[] (1:N — append-only during execution)
├── handoffs: StageHandoff[]      (1:N — one per cross-agent transfer)
└── alerts: AlertSummary          (1:1 — aggregated from communication phase)

ScenarioConfig ──uses──► SimulatedSignal (1:N — config drives signal generation)

SeedData ──loaded-by──► DemoRun.setup phase
         ──consumed-by──► all subsequent phases

SimulatedSignal ──injected-into──► PhaseResult[monitoring]
DecisionRecord  ──created-by──► PhaseResult[risk|evacuation|resource|communication]
StageHandoff    ──created-by──► PhaseResult[risk|evacuation|resource|communication]
AlertSummary    ──created-by──► PhaseResult[communication]
```
