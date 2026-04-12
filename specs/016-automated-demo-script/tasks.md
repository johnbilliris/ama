# Tasks: Automated Demo Script

**Input**: Design documents from `/specs/016-automated-demo-script/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Included — plan.md explicitly specifies `tests/simulation/test_demo_script.py` as a deliverable.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Script**: `scripts/demo.py` (new — single-file CLI tool, ~600-800 LOC)
- **Tests**: `tests/simulation/test_demo_script.py` (new — pytest with `simulation` marker)
- **Seed data**: `data/alert-templates/`, `data/population/`, `data/road-networks/`, `data/resource-inventories/`
- **Agents**: `apps/agents/{monitoring,risk_assessment,evacuation,resource_allocation,communication}/agent.py`
- **Platform API**: `apps/api/app/main.py`

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Create the script file, CLI entrypoint, and all Pydantic data models

- [X] T001 Create `scripts/demo.py` with module docstring, `__future__` annotations, standard library imports (`argparse`, `datetime`, `json`, `sys`, `signal`, `time`, `pathlib`), third-party imports (`httpx`, `pydantic`, `fastapi.testclient`), and `if __name__ == "__main__"` entrypoint stub
- [X] T002 Implement `argparse` CLI parser in `scripts/demo.py` with `--verbose` (flag, default `False`), `--scenario` (choices: `bushfire`, `cyclone`, `flood`, default `bushfire`), and `--output` (path, optional) per `contracts/cli-interface.md`
- [X] T003 Define all Pydantic `BaseModel` classes in `scripts/demo.py` per `data-model.md`: `PhaseResult`, `SimulatedSignal`, `DecisionRecord`, `StageHandoff`, `AlertSummary`, `ScenarioConfig`, `SeedData`, and `DemoRun` with validation rules and field constraints

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `load_seed_data(scenario: str) -> SeedData` function in `scripts/demo.py` that loads and validates all 9 required seed files: 6 alert template JSONs from `data/alert-templates/{en-AU,zh-Hans,ar,vi,el,it}.json`, population data from `data/population/sample-population.json`, road network from `data/road-networks/far-north-qld-sample.json`, and resource inventory from `data/resource-inventories/sample-inventory.json`; validates top-level schema keys exist; filters `scenario_templates` by `hazard_type`; reports specific errors for missing/invalid files per FR-014
- [X] T005 Implement `create_clients() -> dict[str, TestClient]` function in `scripts/demo.py` that instantiates 6 in-process ASGI TestClients using the `create_app()` factory pattern from `tests/benchmark/conftest.py`: platform API via `app.main.create_app()`, monitoring via `monitoring.agent.create_app()`, risk assessment via `risk_assessment.agent.create_app()`, evacuation via `evacuation.agent.create_app()`, resource allocation via `resource_allocation.agent.create_app()`, communication via `communication.agent.create_app()` — all with default args (no external dependencies) per R-001
- [X] T006 Implement `serialize_output(run: DemoRun, output_path: str | None)` function in `scripts/demo.py` that serialises `DemoRun` to JSON matching `contracts/output-schema.md` schema; writes to stdout by default or to `--output` file path; uses `model_dump(mode="json")` with ISO 8601 datetime formatting
- [X] T007 Implement `run_pipeline(args) -> int` orchestrator function in `scripts/demo.py` that iterates through all 7 phases in order, calls each phase function, checks `PhaseResult.status == "pass"` after each phase, stops on first failure (fail-fast per R-007), marks remaining phases as `skipped`, assembles `DemoRun`, calls `serialize_output()`, and returns exit code (0=success, 1=failure); wire to `main()` entrypoint with `sys.exit()`
- [X] T008 Implement `KeyboardInterrupt` and `SIGINT` handler in `scripts/demo.py` that catches interrupts, outputs partial `DemoRun` summary with phases completed so far, and exits with code 130 per `contracts/cli-interface.md`

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — End-to-End Pipeline Smoke Test (Priority: P1) 🎯 MVP

**Goal**: A single command (`python scripts/demo.py`) exercises the full 5-agent disaster response pipeline, exits with code 0 on success, and produces a JSON summary covering all 7 phases

**Independent Test**: Run `python scripts/demo.py` in an environment with no Azure credentials and verify exit code 0 plus JSON output with 7 phases all showing `"status": "pass"`

### Implementation for User Story 1

- [X] T009 [US1] Implement `run_setup_phase(clients, seed_data) -> PhaseResult` in `scripts/demo.py`: health-check all 5 agents via `GET /health` on each agent TestClient, accept `"healthy"` or `"degraded"` status as pass, fail on `"unhealthy"`; call `reset_state()` from `app.services.state_store`; count validated seed files; return `PhaseResult(phase="setup", order=1, agent="orchestrator")` with `details` dict containing `agents_healthy`, `agents_degraded`, `seed_files_validated` counts
- [X] T010 [US1] Implement `run_monitoring_phase(clients, seed_data, scenario_config) -> PhaseResult` in `scripts/demo.py`: build a `SimulatedSignal` from `ScenarioConfig` defaults; POST signal payload to platform API `POST /api/signals` as a `SignalEnvelope` JSON (matching the format in `tests/simulation/test_quickstart_rehearsals.py:32-50`); POST to monitoring agent `POST /associate` to associate signal to incident; verify dashboard via `GET /api/incidents/{incident_id}/dashboard`; return `PhaseResult(phase="monitoring", order=2, agent="monitoring")` with `details` containing `signal_id`, `incident_id`, `signals_associated`
- [X] T011 [US1] Implement `run_risk_assessment_phase(clients, seed_data) -> PhaseResult` in `scripts/demo.py`: seed a `Recommendation` object into `state_store.RECOMMENDATIONS` dict (simulating agent output with `generation_method="template_fallback"` and `confidence=0.72`); POST to risk assessment agent `POST /override` with `action: "approve"` to approve the recommendation; return `PhaseResult(phase="risk_assessment", order=3, agent="risk_assessment")` with `details` containing `recommendation_id`, `generation_method`, `override_action`, `confidence`
- [X] T012 [US1] Implement `run_evacuation_phase(clients, seed_data) -> PhaseResult` in `scripts/demo.py`: POST to evacuation agent `POST /replan` with bushfire scenario data (affected area coordinates, population data); POST to evacuation agent `POST /override` with `action: "approve"` to approve the evacuation plan; return `PhaseResult(phase="evacuation", order=4, agent="evacuation")` with `details` containing `plan_triggered`, `override_action`
- [X] T013 [US1] Implement `run_resource_allocation_phase(clients, seed_data) -> PhaseResult` in `scripts/demo.py`: POST to resource allocation agent `POST /override` with `action: "approve"` to approve the resource allocation plan; return `PhaseResult(phase="resource_allocation", order=5, agent="resource_allocation")` with `details` containing `override_action`
- [X] T014 [US1] Implement `run_communication_phase(clients, seed_data, scenario_config) -> PhaseResult` in `scripts/demo.py`: build an `AgentHandoffEvent` payload (matching `apps/agents/common/handoffs.py` schema) with source `resource_allocation`, target `communication`, and scenario-appropriate alert content; POST to communication agent `POST /process-handoff`; verify response includes multilingual alert drafts in 6 languages (en-AU, zh-Hans, ar, vi, el, it); return `PhaseResult(phase="communication", order=6, agent="communication")` with `details` containing `alert_id`, `languages` list, `safety_validated`, `confidence`; populate `AlertSummary` with results
- [X] T015 [US1] Implement `run_summary_phase(demo_run) -> PhaseResult` in `scripts/demo.py`: aggregate statistics from all previous phases — count total decisions, total handoffs, total languages; return `PhaseResult(phase="summary", order=7, agent="orchestrator")` with `details` containing `total_decisions`, `total_handoffs`, `total_languages`
- [X] T016 [US1] Wire all 7 phase functions into `run_pipeline()` in `scripts/demo.py`: call phases in sequence (setup → monitoring → risk_assessment → evacuation → resource_allocation → communication → summary), pass TestClients and SeedData through, assemble `DemoRun` with ordered `phases` list, compute `duration_seconds` and `status`, call `serialize_output()`

**Checkpoint**: At this point, `python scripts/demo.py` should complete all 7 phases, exit with code 0, and produce valid JSON output — the core smoke test works

---

## Phase 4: User Story 3 — Governance and Auditability Demonstration (Priority: P2)

**Goal**: Enrich pipeline with formal decision records, stage handoff tracking, policy references, and audit trail so the JSON output demonstrates governance controls

**Independent Test**: Run `python scripts/demo.py` and verify the JSON output contains `audit_trail` with 4 decision records (risk, evacuation, resource, alert) each with `approver_role`, `policy`, and `outcome`; and `handoffs` with 4 entries each with `source_agent`, `target_agent`, `confidence`, and `timestamp`

> **Note**: US3 is implemented before US2 because the audit data must exist before verbose mode can narrate it.

### Implementation for User Story 3

- [X] T017 [US3] Add `DecisionRecord` creation to `run_risk_assessment_phase()` in `scripts/demo.py`: after approval, create a `DecisionRecord` with `decision_type="risk_override"`, `agent="risk_assessment"`, `approver_role="incident_commander"`, `policy="AIIMS_escalation"`, `outcome="auto_approved"`, `supporting_data=[signal_id]`; append to `DemoRun.audit_trail`
- [X] T018 [P] [US3] Add `DecisionRecord` creation to `run_evacuation_phase()` in `scripts/demo.py`: create record with `decision_type="evacuation_approval"`, `agent="evacuation"`, `approver_role="incident_commander"`, `policy="AIIMS_escalation"`, `outcome="auto_approved"`, `supporting_data=[recommendation_id]`; append to `DemoRun.audit_trail`
- [X] T019 [P] [US3] Add `DecisionRecord` creation to `run_resource_allocation_phase()` in `scripts/demo.py`: create record with `decision_type="resource_approval"`, `agent="resource_allocation"`, `approver_role="incident_commander"`, `policy="resource_threshold_policy"`, `outcome="auto_approved"`, `supporting_data=[recommendation_id]`; append to `DemoRun.audit_trail`
- [X] T020 [P] [US3] Add `DecisionRecord` creation to `run_communication_phase()` in `scripts/demo.py`: create record with `decision_type="alert_approval"`, `agent="communication"`, `approver_role="incident_commander"`, `policy="AIIMS_alert_publication"`, `outcome="auto_approved"`, `supporting_data=[recommendation_id, alert_id]`; append to `DemoRun.audit_trail`
- [X] T021 [US3] Implement `StageHandoff` recording in `scripts/demo.py`: create 4 handoff records at each cross-agent transfer — monitoring→risk_assessment (signal data, confidence 0.92), risk_assessment→evacuation (evacuation recommendation, confidence 0.72), risk_assessment→resource_allocation (resource mobilisation, confidence 0.72), resource_allocation→communication (alert request, confidence 0.65); append each to `DemoRun.handoffs` with unique `handoff_id`, `timestamp`, and `payload_summary`
- [X] T022 [US3] Implement policy escalation detection in `scripts/demo.py`: when a decision exceeds a configured threshold (e.g., large-scale evacuation affecting >1000 people), create an additional `DecisionRecord` with `decision_type="policy_escalation"` including escalation reason and authority level required; integrate into `run_evacuation_phase()` and `run_resource_allocation_phase()`
- [X] T023 [US3] Update `run_summary_phase()` in `scripts/demo.py` to include audit trail and handoff statistics in phase `details`: `total_decisions`, `total_handoffs`, `total_escalations`; ensure `DemoRun.audit_trail` and `DemoRun.handoffs` are fully populated before serialisation

**Checkpoint**: JSON output now contains complete governance evidence — audit trail, handoff log, and policy escalation records

---

## Phase 5: User Story 2 — Live Demonstration for Stakeholders (Priority: P2)

**Goal**: Verbose mode (`--verbose`) prints human-readable, narrated descriptions of each pipeline stage to stderr, suitable for live demonstrations completing in under 5 minutes

**Independent Test**: Run `python scripts/demo.py --verbose` and confirm stderr output includes labelled phase headers with timestamps, approval gate narration, multilingual alert details in 6 languages, and a final summary banner — all completing in under 5 minutes

### Implementation for User Story 2

- [X] T024 [US2] Implement `Narrator` class in `scripts/demo.py` with methods: `header(scenario)` prints the demo title banner to stderr, `phase_start(phase_name, order, description)` prints phase header with timestamp and order (e.g., `[14:30:22] ▶ Phase 1/7: SETUP — ...`), `phase_end(duration)` prints completion indicator, `detail(message)` prints indented detail line with `→` prefix, `success(message)` prints `✓` prefixed line, `warning(message)` prints `⚠` prefixed line; all output goes to `sys.stderr`; all methods are no-ops when `verbose=False`
- [X] T025 [US2] Add verbose narration calls to each phase function in `scripts/demo.py`: `run_setup_phase()` narrates each agent health check result with agent name and status; `run_monitoring_phase()` narrates signal injection with signal ID, confidence, and category; `run_risk_assessment_phase()` narrates hazard assessment and recommendation
- [X] T026 [US2] Add approval gate narration to `run_risk_assessment_phase()`, `run_evacuation_phase()`, `run_resource_allocation_phase()`, and `run_communication_phase()` in `scripts/demo.py`: print `⚠ APPROVAL GATE: [Role] reviewing [action]...` followed by `✓ AUTO-APPROVED (simulated human review)` and `→ Decision recorded in audit trail`; shows recommendation details, supporting signal IDs, and simulated human approval per US2 acceptance scenario 2
- [X] T027 [US2] Add multilingual alert display to `run_communication_phase()` verbose output in `scripts/demo.py`: print each language code with channel distribution targets (sms, push, broadcast) per US2 acceptance scenario 3
- [X] T028 [US2] Add final summary banner to verbose output in `scripts/demo.py`: print bordered summary block showing total phases passed, agents exercised, approval gates passed, cross-agent handoffs recorded, alert languages, and total duration per `contracts/cli-interface.md` narration format
- [X] T029 [US2] Add configurable pacing delays between narration lines in `scripts/demo.py`: `time.sleep(0.3)` between detail lines in verbose mode (no delays in CI mode); ensure total verbose run stays under 5 minutes per SC-002

**Checkpoint**: `python scripts/demo.py --verbose` produces a presenter-ready narrated walkthrough on stderr while still outputting valid JSON on stdout

---

## Phase 6: User Story 4 — Seed Data and Scenario Configuration (Priority: P3)

**Goal**: The demo loads realistic seed data from `data/` and supports `--scenario bushfire|cyclone|flood` to adapt demonstrations for different disaster types

**Independent Test**: Run `python scripts/demo.py --scenario bushfire` and verify bushfire-specific outputs; re-run with `--scenario cyclone` and confirm outputs change to cyclone-specific signals and alert templates

### Implementation for User Story 4

- [X] T030 [US4] Implement `SCENARIO_CONFIGS` dictionary in `scripts/demo.py` with 3 predefined `ScenarioConfig` entries per `data-model.md`: bushfire (signal_category=`fire`, location=`[149.13, -35.28]`, hazard_type=`bushfire`), cyclone (signal_category=`weather`, location=`[145.77, -16.92]`, hazard_type=`cyclone`), flood (signal_category=`hydrology`, location=`[151.2, -33.8]`, hazard_type=`flood`); each with appropriate `default_severity` and `narration_prefix`
- [X] T031 [US4] Wire `--scenario` argument to `ScenarioConfig` selection in `scripts/demo.py`: resolve the selected scenario config in `main()`, pass to `load_seed_data()` for template filtering by `hazard_type`, pass to `run_monitoring_phase()` for signal generation with scenario-specific `signal_type`, `location`, and `severity`
- [X] T032 [US4] Add scenario-specific narration to verbose mode in `scripts/demo.py`: update `Narrator.header()` to display the active scenario name in the title banner; update `run_monitoring_phase()` narration to use `ScenarioConfig.narration_prefix` for scenario context; update signal descriptions to reflect scenario-specific hazard type
- [X] T033 [US4] Add seed data missing-file validation to `load_seed_data()` in `scripts/demo.py`: if any required file is missing, report the specific file path and exit with code 1 before starting any agents per FR-014 and US4 acceptance scenario 3

**Checkpoint**: Demo supports all 3 disaster scenarios with appropriate seed data and outputs

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Test coverage, documentation validation, and quality hardening

- [X] T034 Create `tests/simulation/test_demo_script.py` with pytest `simulation` marker: test that `run_pipeline()` completes all 7 phases with `status="pass"` using default bushfire scenario; test that JSON output matches `contracts/output-schema.md` root schema keys; test that `audit_trail` contains ≥4 decision records; test that `handoffs` contains ≥4 entries; test that `alerts.languages` contains all 6 language codes; test that exit code is 0 on success
- [X] T035 [P] Add failure-path tests to `tests/simulation/test_demo_script.py`: test that a simulated agent health-check failure produces exit code 1 and `status="fail"` with the failed phase identified and remaining phases marked `skipped`; test that missing seed data file produces a specific error message and exit code 1 before any agents start
- [X] T036 [P] Add scenario and mode tests to `tests/simulation/test_demo_script.py`: test that `--scenario cyclone` produces cyclone-specific signal type in output; test that `--verbose` produces narration on stderr while JSON remains valid on stdout; test that `--output <path>` writes JSON to file instead of stdout
- [X] T037 [P] Add performance assertion to `tests/simulation/test_demo_script.py`: test that full pipeline completes in under 60 seconds wall-clock time per SC-003
- [X] T038 Run `specs/016-automated-demo-script/quickstart.md` validation: execute every command documented in the quickstart (CI mode, verbose mode, output-to-file, cyclone scenario) and verify each produces expected results
- [X] T039 Add `demo` script entry to repo documentation: update `README.md` or `docs/` with a reference to the new `scripts/demo.py` command and link to `specs/016-automated-demo-script/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — core pipeline, BLOCKS US3 and US2
- **US3 (Phase 4)**: Depends on US1 — adds audit/governance data layer
- **US2 (Phase 5)**: Depends on US1 — adds verbose presentation layer (benefits from US3 data)
- **US4 (Phase 6)**: Depends on US1 — adds scenario flexibility (independent of US2/US3)
- **Polish (Phase 7)**: Depends on US1 at minimum; ideally after all stories complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 3 (P2)**: Depends on US1 — enriches pipeline with governance data that US2 narrates
- **User Story 2 (P2)**: Depends on US1 — can start in parallel with US3 but benefits from US3 completing first
- **User Story 4 (P3)**: Depends on US1 — independent of US2 and US3; can run in parallel with either

### Within Each User Story

- Models and data structures before functions that use them
- Infrastructure functions before phase functions
- Phase functions before orchestrator wiring
- Core implementation before verbose/narration enrichment

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel after T001 creates the file
- **Phase 4 (US3)**: T018, T019, T020 can run in parallel (different phase functions, same pattern)
- **Phase 5 vs Phase 6**: US2 and US4 can be implemented in parallel by different developers
- **Phase 7**: T035–T037 can run in parallel after T034 creates the test file; T039 is independent

---

## Parallel Example: User Story 3

```
# Launch all DecisionRecord tasks in parallel (different phase functions):
Task T018: "Add DecisionRecord to run_evacuation_phase() in scripts/demo.py"
Task T019: "Add DecisionRecord to run_resource_allocation_phase() in scripts/demo.py"
Task T020: "Add DecisionRecord to run_communication_phase() in scripts/demo.py"
```

## Parallel Example: Polish Phase

```
# T034 must complete first (creates the file), then T035–T037 can run in parallel:
Task T034: "Create test_demo_script.py with success-path tests"  (FIRST)
Task T035: "Add failure-path tests to test_demo_script.py"       (after T034)
Task T036: "Add scenario and mode tests to test_demo_script.py"  (after T034)
Task T037: "Add performance assertion to test_demo_script.py"    (after T034)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T008)
3. Complete Phase 3: User Story 1 (T009–T016)
4. **STOP and VALIDATE**: Run `python scripts/demo.py` — verify exit code 0 and valid JSON output
5. This alone satisfies SC-001, SC-003, SC-004, SC-005, SC-008 — a working CI smoke test

### Incremental Delivery

1. Setup + Foundational → Script skeleton ready
2. **Add US1** → Test with `python scripts/demo.py` → **MVP complete** (CI smoke test works)
3. **Add US3** → Verify `audit_trail` and `handoffs` in JSON output → Governance evidence complete
4. **Add US2** → Test with `python scripts/demo.py --verbose` → Live demo ready
5. **Add US4** → Test with `--scenario cyclone` → Scenario flexibility added
6. **Polish** → Run tests, validate quickstart → Production-ready

### Parallel Team Strategy

With multiple developers after US1 is complete:

1. All complete Setup + Foundational + US1 together
2. Once US1 is done:
   - Developer A: US3 (governance/audit enrichment)
   - Developer B: US2 (verbose narration) — can start immediately, integrate US3 data when available
   - Developer C: US4 (scenario configuration)
3. All stories integrate cleanly because they extend different aspects of the same pipeline

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 39 |
| **Phase 1 (Setup)** | 3 tasks |
| **Phase 2 (Foundational)** | 5 tasks |
| **Phase 3 (US1 — Smoke Test)** | 8 tasks |
| **Phase 4 (US3 — Governance)** | 7 tasks |
| **Phase 5 (US2 — Live Demo)** | 6 tasks |
| **Phase 6 (US4 — Scenarios)** | 4 tasks |
| **Phase 7 (Polish)** | 6 tasks |
| **Parallel opportunities** | 7 tasks marked [P] + US2/US4 phases can run in parallel |
| **MVP scope** | Phases 1–3 (16 tasks) |
| **Files created** | `scripts/demo.py`, `tests/simulation/test_demo_script.py` |

## Notes

- [P] tasks = different files or independent functions, no dependencies
- [Story] label maps task to specific user story for traceability
- All 7 pipeline phases (setup, monitoring, risk_assessment, evacuation, resource_allocation, communication, summary) map to the AIIMS-aligned workflow per Constitution §II
- US3 (governance) is ordered before US2 (verbose) despite both being P2 because audit data must exist before narration can display it
- The demo script uses the proven `TestClient(create_app())` pattern from `tests/benchmark/conftest.py` — no new infrastructure required
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
