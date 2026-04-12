# Research: Automated Demo Script

**Feature**: 016-automated-demo-script
**Date**: 2026-04-12

## R-001: In-Process Agent Instantiation Pattern

### Question
How should the demo script instantiate all 5 agents in-process without TCP port binding?

### Research

The codebase already uses `TestClient(create_app())` extensively:

- **Benchmark fixtures** (`tests/benchmark/conftest.py:20-57`): Session-scoped `TestClient` for each agent via `create_app()` factory. Pattern: `from monitoring.agent import create_app as create_monitoring_app; TestClient(create_monitoring_app())`.
- **Quickstart rehearsals** (`tests/simulation/test_quickstart_rehearsals.py:29`): Platform API via `TestClient(create_app())` from `app.main`.
- **Unit tests**: Individual agent TestClients in `tests/unit/test_communication_endpoints.py`, `test_evacuation_endpoints.py`, `test_resource_allocation_endpoints.py`, `test_risk_assessment_endpoints.py`.

Each agent's `create_app()` accepts optional dependencies (agent instance, config, audit_writer, etc.) and defaults to `None`, creating minimal in-memory stubs:

| Agent | Factory location | Params |
|-------|-----------------|--------|
| Platform API | `app.main.create_app()` | None |
| Monitoring | `monitoring.agent.create_app(agent, audit_writer, freshness_tracker, config)` | All optional |
| Risk Assessment | `risk_assessment.agent.create_app(agent, audit_writer, pipeline, config, recommendation_store)` | All optional |
| Evacuation | `evacuation.agent.create_app(agent, config)` | All optional |
| Resource Allocation | `resource_allocation.agent.create_app(agent, config)` | All optional |
| Communication | `communication.agent.create_app(config, pipeline, approval_workflow, audit_writer)` | All optional |

### Decision
Use the same `TestClient(create_app())` pattern as benchmarks. Create 6 TestClients: one platform API client + one per agent. Each `create_app()` is called with default args (no external dependencies). This gives in-process ASGI transport without TCP binding.

### Rationale
- Proven pattern already in CI (benchmarks run this way)
- Zero-config: no ports, no process management, no startup/shutdown lifecycle
- Deterministic: same process, same memory space
- Fast: no network overhead

### Alternatives Considered
- **Subprocess per agent with TCP**: Rejected — adds process management complexity, port conflicts, startup delays, and violates the <60s CI constraint.
- **Direct function calls bypassing HTTP**: Rejected — loses the HTTP contract validation that the demo is supposed to exercise.

---

## R-002: Pipeline Phase Orchestration Strategy

### Question
How should the 7 pipeline phases be orchestrated, and what is the call sequence?

### Research

The existing quickstart rehearsal (`test_quickstart_rehearsals.py`) demonstrates the platform API flow:
1. `POST /api/signals` — ingest signal
2. `GET /api/incidents/{id}/dashboard` — verify situation picture
3. Seed recommendation + alert in state store
4. `POST /api/recommendations/{id}/approvals` — approve recommendation
5. `POST /api/alerts/{id}/publish` — publish alert
6. `POST /api/scenarios/replay` — run scenario replay

However, this only exercises the **platform API** — it does not drive the individual agent endpoints. The demo script needs to exercise all 5 agent-specific endpoints to demonstrate cross-agent coordination.

The agent-specific endpoints are:
- **Monitoring**: `GET /health`, `POST /associate`
- **Risk Assessment**: `GET /health`, `POST /override`
- **Evacuation**: `GET /health`, `POST /override`, `POST /replan`
- **Resource Allocation**: `GET /health`, `POST /override`
- **Communication**: `GET /health`, `POST /process-handoff`

### Decision
Orchestrate 7 phases using a **dual-client strategy**:
1. **Phase 1 (Setup)**: Create all 6 TestClients (platform API + 5 agents). Health-check each via `GET /health`. Validate seed data files. Reset platform state via `reset_state()`.
2. **Phase 2 (Monitoring)**: Ingest bushfire signal via platform API `POST /api/signals`. Associate signals via monitoring agent `POST /associate`. Verify dashboard via `GET /api/incidents/{id}/dashboard`.
3. **Phase 3 (Risk Assessment)**: Seed a recommendation in state store (simulating agent output). Approve via risk agent `POST /override` with `action: "approve"`.
4. **Phase 4 (Evacuation)**: Trigger replan via evacuation agent `POST /replan` with bushfire scenario data. Override/approve the evacuation plan via `POST /override`.
5. **Phase 5 (Resource Allocation)**: Override/approve resource plan via `POST /override`.
6. **Phase 6 (Communication)**: Process handoff via communication agent `POST /process-handoff` with `AgentHandoffEvent`. Verify multilingual alert creation.
7. **Phase 7 (Summary)**: Collect all phase results, build audit trail, produce JSON summary.

### Rationale
- Exercises every agent's unique endpoint (not just the platform API)
- Demonstrates explicit cross-agent handoffs per Constitution §II
- Follows AIIMS workflow: activation → ingestion → analysis → recommendation → approval → alert publishing
- Fail-fast: each phase checks the previous phase's result before proceeding

### Alternatives Considered
- **Platform API only** (like quickstart rehearsal): Rejected — doesn't exercise agent-specific endpoints or demonstrate cross-agent handoffs.
- **Event-driven with message bus**: Rejected — adds infrastructure dependency; in-process calls are sufficient for demo.

---

## R-003: Seed Data Loading and Validation

### Question
How should seed data be loaded, what validation is needed, and what files are required?

### Research

Existing seed data in `data/`:

| Directory | Files | Schema |
|-----------|-------|--------|
| `data/alert-templates/` | `ar.json`, `el.json`, `en-AU.json`, `it.json`, `vi.json`, `zh-Hans.json` | Array of `{template_id, hazard_type, severity, alert_type, language_code, title_template, body_template, action_items_template}` |
| `data/population/` | `sample-population.json` | `{metadata, facilities[], population_density[]}` — facilities have coordinates, capacity, vulnerability |
| `data/road-networks/` | `far-north-qld-sample.json` | `{metadata, nodes[], edges[], assembly_areas[]}` — edges have distance, capacity, closure status |
| `data/resource-inventories/` | `sample-inventory.json` | `{resources[]}` — each with type, capabilities, location, status, capacity |

The existing `scripts/gen_sample_data.py` generates population and road network data. `scripts/seed_loader.py` loads seed data into Cosmos (not needed for demo).

### Decision
- Validate that all 10 required files exist on startup (6 alert templates + population + road network + resource inventory + at least one scenario match).
- Load JSON and validate top-level schema keys (not deep validation — just ensure files are parseable and contain expected top-level keys).
- For bushfire scenario: select templates where `hazard_type == "bushfire"`.
- Create a `SeedData` dataclass to hold loaded data for use across phases.
- Report specific errors for each missing/invalid file before starting any agents (per FR-014).

### Rationale
- Matches FR-014 (validate seed data completeness on startup)
- Reuses existing JSON files without modification
- Lightweight validation avoids blocking CI on schema changes

### Alternatives Considered
- **Deep Pydantic validation of all seed data**: Rejected — over-engineered for a demo script; JSON key checks are sufficient.
- **Generate seed data on the fly**: Rejected — existing data is realistic and reproducible; generation adds time.

---

## R-004: LLM-Free Operation via Template Fallback

### Question
How do agents operate without a live Azure OpenAI connection?

### Research

All agents use `LLMCallMixin._generate_with_fallback()` from `apps/agents/common/llm_mixin.py`:
1. Attempt LLM call via `LLMClient`
2. If circuit breaker is open, LLM times out, or response fails validation → fall back to template text
3. Fallback returns `generation_method="template_fallback"`, reduced confidence, `requires_human_review=True`

Each agent's `create_app()` defaults to no LLM client when no config is provided. The `LLMClientConfig` defaults pull from environment variables (`AZURE_OPENAI_ENDPOINT`, etc.) which will be absent in CI/demo.

The monitoring agent has a separate fallback path in `summarize_signal()` that returns rule-based summaries when LLM is unavailable.

The communication agent's pipeline has hardcoded emergency text fallback when the `TemplateLoader` is `None`.

### Decision
No special configuration needed. The default `create_app()` call (with no args) naturally triggers template fallback because:
1. No Azure OpenAI environment variables → `LLMClient` will fail on first call
2. Circuit breaker opens after first failure → all subsequent calls use template fallback
3. Template fallback produces valid, deterministic output with reduced confidence

The demo script should set `generation_method` assertions to expect `"template_fallback"` in the output.

### Rationale
- Zero-config: the fallback mechanism is already built into every agent
- Deterministic: template output is the same every run
- Aligns with spec assumption: "Template-based fallback responses are adequate for the demo"

### Alternatives Considered
- **Mock the LLM client**: Rejected — unnecessary; the fallback path is the real code path we want to exercise.
- **Set environment variables to a mock server**: Rejected — adds complexity and fragility.

---

## R-005: Output Format and Summary Structure

### Question
What JSON structure should the summary output use?

### Research

The spec requires (FR-006):
- All 7 phases covered
- Per-phase: pass/fail status, inputs consumed, outputs produced
- Overall pass/fail
- Audit trail (FR-011): agent, decision, data references, timestamps, governance policy
- Handoffs (FR-012): source agent, destination agent, data transferred, confidence

The existing `ExerciseReport` model (`packages/domain/src/domain/models/exercise_report.py`) provides a pattern for structured exercise output with `SignalSummary`, `RecommendationSummary`, `AlertSummary`, `PerformanceMetrics`, and `BenchmarkComparison`.

### Decision
Use a summary-only JSON structure (key metrics, not full model dumps) per the user's instruction:

```json
{
  "run_id": "demo-20260412-143022",
  "scenario": "bushfire",
  "status": "pass",
  "started_at": "2026-04-12T14:30:22Z",
  "completed_at": "2026-04-12T14:30:28Z",
  "duration_seconds": 6.2,
  "phases": [
    {
      "phase": "setup",
      "order": 1,
      "status": "pass",
      "agent": "orchestrator",
      "duration_seconds": 0.8,
      "summary": "All 5 agents healthy, seed data validated",
      "details": {
        "agents_healthy": 5,
        "seed_files_validated": 10
      }
    }
  ],
  "audit_trail": [
    {
      "timestamp": "2026-04-12T14:30:24Z",
      "decision_type": "evacuation_approval",
      "agent": "evacuation",
      "approver_role": "incident_commander",
      "policy": "AIIMS_escalation",
      "outcome": "auto_approved",
      "supporting_data": ["signal-001", "assessment-001"]
    }
  ],
  "handoffs": [
    {
      "timestamp": "2026-04-12T14:30:25Z",
      "source_agent": "risk_assessment",
      "target_agent": "evacuation",
      "confidence": 0.72,
      "payload_summary": "Bushfire risk assessment with evacuation recommendation"
    }
  ],
  "alerts": {
    "total": 1,
    "languages": ["en-AU", "zh-Hans", "ar", "vi", "el", "it"],
    "safety_validated": true
  }
}
```

### Rationale
- Summary-only keeps output scannable for CI logs and live demos
- Matches all FR requirements (phases, audit, handoffs, alerts)
- JSON is machine-parseable for CI gate assertions
- Lightweight compared to dumping full Pydantic models

### Alternatives Considered
- **Full model dumps**: Rejected — too verbose, not useful for CI or demo narration.
- **YAML or plain text**: Rejected — JSON is the standard for CI tooling and is explicitly required by FR-006.
- **Separate detailed log file**: Rejected — adds complexity; verbose mode provides detail via stderr narration.

---

## R-006: CI vs Verbose Mode Behaviour

### Question
How should CI mode and verbose mode differ in behaviour?

### Research

From the spec clarifications:
- **CI mode** (default): Silent, auto-approve, <60s, exit code 0/non-zero
- **Verbose mode** (`--verbose`): Narrated output, auto-approve with narration, <5min
- No interactive prompts in either mode

### Decision

| Aspect | CI Mode (default) | Verbose Mode (`--verbose`) |
|--------|-------------------|---------------------------|
| Stdout | JSON summary only | JSON summary only |
| Stderr | Silent (errors only) | Rich narration per phase |
| Approvals | Auto-approve silently | Auto-approve with narration ("Incident Commander reviewing evacuation plan... APPROVED") |
| Timing | <60s target | <5min target |
| Exit code | 0 = success, 1 = failure | Same |
| Delays | None | Optional narration pauses (configurable) |

The narration goes to stderr so JSON output on stdout remains machine-parseable. Verbose mode adds `time.sleep()` pauses between narration lines (default 0.5s) to pace the live demo.

### Rationale
- Separation of concerns: JSON on stdout, narration on stderr
- CI can capture stdout for assertions, ignore stderr
- Verbose mode paces naturally for live demos without blocking

### Alternatives Considered
- **Interleave narration in JSON**: Rejected — breaks JSON parsing.
- **Separate log file for narration**: Rejected — unnecessary; stderr is the right channel.
- **Interactive mode with actual prompts**: Rejected per spec clarification.

---

## R-007: Error Handling and Fail-Fast Strategy

### Question
How should the script handle errors at each phase?

### Research

From spec: "Fail-fast. Stop at first stage failure, report which agent/stage failed, exit non-zero."

The existing agent health checks return structured responses with per-dependency status. An unhealthy agent returns `status: "unhealthy"` when critical dependencies (like message queue) are offline.

### Decision
- Each phase function returns a `PhaseResult` dataclass with `status`, `duration`, `summary`, `details`, and optional `error`.
- The orchestrator checks `PhaseResult.status == "pass"` after each phase.
- On failure: skip remaining phases, set overall status to `"fail"`, add the failed phase to the summary, and exit with code 1.
- The JSON summary always includes all attempted phases (passed and failed) plus which phases were skipped.
- Health checks: `status` in `["healthy", "degraded"]` = pass. `"unhealthy"` = fail.
- Ctrl+C: Catch `KeyboardInterrupt`, output partial summary, exit 130.

### Rationale
- Aligns with spec requirement for fail-fast + CI gate semantics
- Partial summary on failure aids debugging
- `degraded` is acceptable (agents can operate with template fallback)

### Alternatives Considered
- **Continue on failure**: Rejected per spec.
- **Retry failed phases**: Rejected — adds complexity and violates fail-fast.

---

## R-008: Scenario Configuration

### Question
How should the `--scenario` flag work, and what changes per scenario?

### Research

The ingestion simulation system (`apps/ingestion/simulation/scenario_templates.py`) defines templates for bushfire, flood, cyclone, and severe_storm scenarios. Each template specifies phases, active data sources, and signal generation parameters.

Seed data is currently bushfire/generic. Road networks and population data are location-based (Far North QLD), not scenario-specific. Alert templates include bushfire, cyclone, and flood variants for all 6 languages.

### Decision
- `--scenario` accepts `bushfire` (default), `cyclone`, `flood`.
- Scenario affects: signal type/category, alert template selection (`hazard_type` filter), and narration text.
- Scenario does NOT affect: road network data, population data, resource inventory (these are location-based, not hazard-based).
- Implement as a `ScenarioConfig` dataclass mapping scenario type to signal parameters, template filters, and narration text.
- Bushfire is the only fully-tested scenario initially; cyclone and flood are stretch goals.

### Rationale
- Aligns with spec FR-016 and constitution's scenario-based testing requirement
- Minimal per-scenario variation keeps the script maintainable
- Alert templates already support all three hazard types

### Alternatives Considered
- **Full simulation runner integration**: Rejected — too heavy for a demo; simulation runner is designed for extended exercises.
- **Scenario-specific seed data files**: Rejected — existing data is generic enough; hazard-type filtering in templates is sufficient.
