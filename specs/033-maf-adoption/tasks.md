---
description: "Task list for feature 033 — Microsoft Agent Framework (MAF) Adoption"
---

# Tasks: Microsoft Agent Framework (MAF) Adoption

**Input**: Design documents from `C:\code\ama\specs\033-maf-adoption\`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Tests are INCLUDED in this plan because (a) the spec defines explicit measurable success criteria gated by automated checks (SC-002 fault-injection, SC-003 zero-auto-publish, SC-004 reconciliation, SC-007 latency, SC-010 sixth-agent worked example), (b) FR-023 mandates an automated equivalence harness as the per-agent cutover gate, and (c) the existing AMA test suite already covers every other production code path under `tests/{unit,integration,contract,load}/`.

**Organization**: Tasks are grouped by user story (US1..US4). Each task carries the actor-specific agent(s) that must contribute and the tools required to execute it.

## Format

Every task line follows the strict checklist format:

```text
- [ ] T### [P?] [USx?] Imperative single-outcome action with absolute repo-relative file path
  - **Agents**: comma-separated agent-id values from .github/agents/AGENTS.md
  - **Tools**: subset of {execute, read, edit, search, web, agent, todo}
  - **Success**: verifiable, single-line acceptance criterion
```

Tool legend: `execute` = run a shell/PowerShell command (build, test, deploy, az CLI); `read` = view files; `edit` = modify or create files; `search` = grep / glob; `web` = fetch external docs (e.g., MAF Learn pages); `agent` = consult an actor agent for input; `todo` = update the SQL todo state.

## Path Conventions

Monorepo (per `plan.md → Project Structure`):

- Agent runtime: `apps/agents/maf_runtime/`
- API: `apps/api/app/api/routes/`
- Web: `apps/web/src/{app,components,lib}/`
- Infra: `infra/bicep/modules/`, `infra/policy/`
- Tools: `tools/routing_mcp_server/`
- Tests: `tests/{unit,integration,contract,equivalence,load}/`
- ADRs: `docs/aidr/decisions/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialisation — install MAF SDK, scaffold the new package, register ADRs.

- [X] T001 Add `agent-framework`, `agent-framework[azure-ai]`, and `mcp` dependencies to `apps/agents/pyproject.toml`
  - **Agents**: software-developer, ai-ml-engineer
  - **Tools**: edit, execute
  - **Success**: `pip install -e apps/agents` succeeds in `.venv` and `python -c "from agent_framework import ChatAgent, WorkflowBuilder, AzureOpenAIChatClient; print('OK')"` prints `OK`.

- [X] T002 [P] Create the `apps/agents/maf_runtime/` package skeleton with `__init__.py` files for all sub-package directories: `agents/`, `workflow/`, `workflow/executors/` (nested), `checkpoint/`, `middleware/`, `mcp/`, `repositories/`, `equivalence/`, `equivalence/reports/` (nested) — 9 directories total (7 top-level, 2 nested)
  - **Agents**: software-developer
  - **Tools**: edit
  - **Success**: `python -c "import apps.agents.maf_runtime"` succeeds; `Get-ChildItem apps\agents\maf_runtime -Recurse -Directory` lists the 9 directories.

- [X] T003 [P] Author ADR `docs/aidr/decisions/adr-033-01-azure-openai-chat-client.md` recording R3 (no `FoundryAgent` due to checkpoint reliability)
  - **Agents**: solution-architect, ai-ml-engineer, principal-engineer
  - **Tools**: edit, read, web
  - **Success**: ADR follows the existing `adr-031-*` template (Status, Context, Decision, Consequences, References) and cites the MAF docs URL from `research.md §R3`.

- [X] T004 [P] Author ADR `docs/aidr/decisions/adr-033-02-cosmos-checkpoint-storage.md` recording R4 (custom CosmosCheckpointStorage)
  - **Agents**: solution-architect, data-engineer, infrastructure-devops
  - **Tools**: edit, read
  - **Success**: ADR includes the partition-key choice (`/run_id`), the 30-day TTL, and the deny-delete posture for the audit container.

- [X] T005 [P] Author ADR `docs/aidr/decisions/adr-033-03-hitl-spec-008-delegation.md` recording R5 (HITL wraps spec 008)
  - **Agents**: solution-architect, security-engineer, public-information-officer, incident-commander
  - **Tools**: edit, read
  - **Success**: ADR enumerates the field-mapping table from `contracts/hitl-request.envelope.md` and references FR-009 + Q4 clarification.

- [X] T006 [P] Author ADR `docs/aidr/decisions/adr-033-04-mcp-streamable-http.md` recording R6 (MCPStreamableHTTPTool transport)
  - **Agents**: solution-architect, api-architect, infrastructure-devops
  - **Tools**: edit, read
  - **Success**: ADR explains the rejection of stdio / WebSockets / HostedMCPTool with the rationale from `research.md §R6`.

- [X] T007 Configure `apps/agents/pyproject.toml` ruff + mypy include paths to cover the new `maf_runtime/` package
  - **Agents**: software-developer
  - **Tools**: edit, execute
  - **Success**: `ruff check apps tests packages` and `mypy apps/agents/maf_runtime` both pass against the empty package skeleton.

**Checkpoint**: SDK installed, package skeleton committed, all four ADRs in `docs/aidr/decisions/`. Lint and import smoke tests pass.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that EVERY user story depends on. No US1–US4 work may start until this phase is complete.

### Infrastructure (Cosmos containers + immutability policy)

- [X] T008 Add `infra/bicep/modules/cosmos-workflow.bicep` defining three new Cosmos SQL containers in the existing `ama-platform` account: `workflow_runs` (partition `/incident_id`, no TTL), `checkpoints` (partition `/run_id`, defaultTtl=2592000), `tool_registrations` (partition `/tool_name`, no TTL)
  - **Agents**: infrastructure-devops, data-engineer, azure-principal-architect
  - **Tools**: edit, read
  - **Success**: `az bicep build --file infra/bicep/modules/cosmos-workflow.bicep` succeeds with no errors.

- [X] T009 Wire the new `cosmos-workflow.bicep` module into `infra/main.bicep`, exposing container names as outputs and adding `australiaeast` as the only allowed location parameter
  - **Agents**: infrastructure-devops, security-engineer
  - **Tools**: edit, read
  - **Success**: `az deployment group what-if --resource-group rg-drh-dev --template-file infra/main.bicep --parameters @infra/main.parameters.dev.json` reports the three new containers as `Create` and no other deltas (regression check for FR-024).

- [X] T009b Implement `tests/contract/test_audit_telemetry_fields_no_regression.py` proving FR-024 — a field-level snapshot test that captures the pre-MAF field set of (a) every operator-facing REST response in `apps/api/app/api/routes/`, (b) every `audit_entries` Cosmos document shape produced today, and (c) every OTel span attribute referenced by an existing dashboard query under `infra/bicep/modules/dashboards/`; the test FAILS the build if any field is removed or renamed by MAF code paths
  - **Agents**: qa-test-engineer, observer-auditor, sre-engineer
  - **Tools**: read, edit, execute, search
  - **Success**: A deliberate field rename in a draft PR causes `pytest tests/contract/test_audit_telemetry_fields_no_regression.py` to fail; reverting passes; the snapshot file is committed under `tests/contract/snapshots/audit_telemetry_fields.json`.

- [X] T010 Add `infra/policy/deny_audit_delete.rego` Rego rule that denies any role assignment granting `Microsoft.DocumentDB/.../items/delete` on the `audit_entries` container, satisfying R8 + FR-012a 7-year online retention
  - **Agents**: security-engineer, compliance-auditor, infrastructure-devops
  - **Tools**: edit, execute
  - **Success**: `conftest test infra/bicep/modules/cosmos-workflow.bicep --policy infra/policy` blocks a deliberately added `delete` action in a fixture and passes the canonical posture matrix.

- [X] T011 [P] Add the `audit_entries` permanent-retention rule to the spec-029 posture matrix (`infra/policy/posture-matrix.yaml`) so the OPA gate enforces it on every PR
  - **Agents**: security-engineer, compliance-auditor
  - **Tools**: edit
  - **Success**: PR diff shows a single additive rule under `cosmosdb.containers.audit_entries`; existing posture-matrix tests pass.

- [X] T011b Implement `apps/agents/maf_runtime/errors.py` exposing the canonical typed error hierarchy required by FR-004: `MafRuntimeError` (base) and subclasses `LlmFailure` (with sub-distinguished `LlmRateLimitError`, `LlmTimeoutError`, `LlmContentFilterError`, `LlmQuotaError`, `LlmServerError` to drive per-class retry policy in T042c), `ToolFailure` (with subclasses `ToolVersionMismatchError`, `ToolUnreachableError`, `ToolTimeoutError`, `ToolMalformedResponseError`), `ValidationFailure`, `OutputSchemaMismatchError`, `PolicyFailure`, `InvalidStateTransitionError`, `ActiveRunAlreadyExistsError`, `CheckpointStoreUnavailableError`, `DuplicateDecisionConflictError`. Every error MUST carry a `correlation_id`, an optional `run_id`, and a stable `error_code` string. The static-analysis check (no locally-defined error classes within `apps/agents/maf_runtime/`) MUST be split out into a separate polish-phase task (T074b) so it runs only after all downstream tasks have been completed
  - **Agents**: principal-engineer, software-developer, api-architect
  - **Tools**: read, edit
  - **Success**: A new test `tests/unit/test_maf_runtime_errors.py` asserts every error subclass carries the required fields. The cross-module import-discipline check is delegated to T074b (Polish phase) so it does not falsely fail mid-phase before downstream tasks have wired up their imports.

### Shared MAF runtime building blocks

- [X] T012 Implement `apps/agents/maf_runtime/chat_client.py` exposing `build_azure_openai_chat_client(model_tier)` factory that uses `DefaultAzureCredential` + `get_bearer_token_provider("https://cognitiveservices.azure.com/.default")` and reads endpoint + deployment names from existing `LLMClientConfig` (mirrors `apps/agents/common/llm_client.py:18-39`)
  - **Agents**: ai-ml-engineer, security-engineer, software-developer
  - **Tools**: read, edit, execute
  - **Success**: A new unit test `tests/unit/test_maf_runtime_chat_client.py` constructs the client with both `reasoning` and `drafting` tiers without making any network call (deployment names verified, no API key referenced anywhere).

- [X] T013 Implement `apps/agents/maf_runtime/observability.py::setup_observability_once()` that registers MAF's OpenTelemetry hooks via `agent_framework.setup_observability(...)` and routes spans/metrics/logs through the existing `azure-monitor-opentelemetry` exporter (already initialised in `apps/agents/monitoring/agent.py:15-25`)
  - **Agents**: sre-engineer, ai-ml-engineer, software-developer
  - **Tools**: read, edit, web
  - **Success**: Calling `setup_observability_once()` twice is idempotent (no duplicate handlers), and a smoke test asserts that a synthetic span carries the `service.name=ama-agents` resource attribute.

- [X] T014 [P] Implement `apps/agents/maf_runtime/workflow/run_state.py` exposing the 7-state `WorkflowRunStatus` Enum and a `validate_transition(from_state, to_state) -> None` function that raises `InvalidStateTransitionError` for any move not enumerated in `data-model.md §2.1`
  - **Agents**: software-developer, principal-engineer
  - **Tools**: read, edit
  - **Success**: New `tests/unit/test_run_state_transitions.py` exhaustively asserts every allowed transition is accepted and a representative set of illegal transitions is rejected with `InvalidStateTransitionError`.

- [X] T015 [P] Implement `apps/agents/maf_runtime/feature_flags.py::get_agent_mode(agent_name) -> Literal['legacy','maf','shadow']` reading env var `FEATURE_MAF_RUNTIME_<AGENT>` (default `legacy`) and integrating with the spec-029 progressive-delivery flag mechanism. ALL feature flags introduced by this feature MUST share the `FEATURE_MAF_RUNTIME_*` prefix (e.g., the retry-budget overrides in T042c use `FEATURE_MAF_RUNTIME_RETRY_*`)
  - **Agents**: software-developer, infrastructure-devops
  - **Tools**: read, edit
  - **Success**: Unit test parameterises the env var across `legacy`/`maf`/`shadow`/unset for all five agent names; default is `legacy`; invalid values raise `ValueError` (so a typo cannot silently route to MAF).

- [X] T016 Implement `apps/agents/maf_runtime/repositories/workflow_run_repository.py` with `create(...)`, `get(run_id)`, `list(filters)`, `update_status(run_id, new_status)` methods. `create(...)` MUST execute a Cosmos transactional batch that asserts no document for the same `incident_id` has `is_active=true` (FR-011a)
  - **Agents**: data-engineer, software-developer
  - **Tools**: read, edit
  - **Success**: `tests/unit/test_workflow_run_uniqueness.py` proves a second concurrent `create(...)` for the same incident raises a typed `ActiveRunAlreadyExistsError`; transactional batch verified with a fake Cosmos client.

- [X] T017 [P] Implement `apps/agents/maf_runtime/repositories/tool_registration_repository.py` with `register(tool_name, major_version, address, bound_agents)`, `get_for_agent(agent_name) -> list[ToolRegistration]`. `register(...)` MUST refuse in-place updates of an existing `(tool_name, major_version)` and instead require a NEW composite id per FR-019a + `contracts/tool-registration.schema.json`
  - **Agents**: data-engineer, api-architect
  - **Tools**: read, edit
  - **Success**: Unit test confirms a re-register attempt with same `(tool_name, major_version)` is rejected; a major-version bump succeeds and the prior version remains queryable.

- [X] T018 Implement `apps/agents/maf_runtime/checkpoint/cosmos_checkpoint_storage.py` as a subclass of MAF's `CheckpointStorage` interface with `save_checkpoint(run_id, sequence, executor_states, pending_requests)`, `load_latest_checkpoint(run_id)`, `list_checkpoints(run_id)` — all writing to the `checkpoints` Cosmos container with partition key `/run_id`
  - **Agents**: ai-ml-engineer, data-engineer
  - **Tools**: read, edit, web
  - **Success**: Round-trip unit test in `tests/unit/test_cosmos_checkpoint_storage.py` saves an opaque `executor_states` dict and one `pending_requests` entry, then `load_latest_checkpoint` returns byte-equal payloads; AND a separate test simulates a Cosmos write failure and asserts the call surfaces as `CheckpointStoreUnavailableError` (from `errors.py`, T011b), the workflow refuses to proceed without durability, and an operator-visible alert is emitted (covers spec edge case "Checkpoint store is unavailable when a workflow tries to persist").

- [X] T019 Implement `apps/agents/maf_runtime/checkpoint/retention.py::stamp_terminal(run_id)` that re-saves each checkpoint document for the run with `_ttl=2592000` after the parent run reaches a terminal state, ensuring the 30-day countdown starts at terminality (FR-012a)
  - **Agents**: data-engineer, software-developer
  - **Tools**: read, edit
  - **Success**: Unit test simulates terminal transition and asserts every checkpoint document for the run now has `_ttl=2592000`; non-terminal runs leave checkpoints with no TTL.

### Cross-cutting middleware (foundational because all agents bind to it)

- [X] T020 Implement `apps/agents/maf_runtime/middleware/audit_middleware.py` as a MAF `AgentMiddleware` that, around every agent invocation, computes SHA-256 fingerprints of canonicalised input and output JSON and writes one `audit-entry.schema.json`-compliant document to the existing `audit_entries` Cosmos container
  - **Agents**: security-engineer, compliance-auditor, data-engineer, observer-auditor
  - **Tools**: read, edit
  - **Success**: `tests/unit/test_audit_middleware.py` confirms (a) fingerprints are deterministic across map iteration order, (b) raw payloads are never written, (c) `outcome=blocked_by_content_safety` and `tool_failure` paths each emit an entry with `failure_reason`.

- [X] T020b Add `tests/unit/test_audit_writer_uniqueness.py` enforcing Constitution NN-3 (Privacy by design): a static-analysis check that scans `apps/agents/maf_runtime/` and asserts the ONLY module that opens a Cosmos client against the `audit_entries` container is `apps/agents/maf_runtime/middleware/audit_middleware.py`. Any other module attempting to write raw payloads to `audit_entries` MUST fail the test
  - **Agents**: security-engineer, principal-engineer, observer-auditor
  - **Tools**: read, edit, search
  - **Success**: Adding a deliberate second writer in a draft PR causes the test to fail; reverting passes.

- [X] T021 Implement `apps/agents/maf_runtime/middleware/content_safety_middleware.py` wrapping the existing `ContentSafetyValidator` (`apps/agents/common/content_safety.py`) and the existing `ContentSafetyCircuitBreaker`, refusing to invoke the wrapped agent when verdict = block
  - **Agents**: security-engineer, ai-ml-engineer, public-information-officer
  - **Tools**: read, edit
  - **Success**: `tests/unit/test_content_safety_middleware.py` proves (a) blocked inputs short-circuit the agent, the rejection is audited (`outcome=blocked_by_content_safety`), (b) a degraded-mode fallback (circuit open) follows the existing FR-007/FR-008 contract from spec 025, AND (c) a content-safety rejection on the resumed Communication-agent step (i.e., a run already in `AwaitingApproval`) transitions the run to `Cancelled` with `failure_reason="content_safety_rejected"` and publishes a notification onto the existing commander queue (covers spec edge case "Content safety rejection at the middleware layer for an alert that is already in 'pending approval'").

- [X] T022 [P] Implement `apps/agents/maf_runtime/middleware/otel_middleware.py` that adds `workflow.run_id`, `workflow.step`, `workflow.parent_trace_id` custom attributes to the MAF-emitted span for each agent step (per `data-model.md §7`)
  - **Agents**: sre-engineer, ai-ml-engineer
  - **Tools**: read, edit
  - **Success**: `tests/unit/test_otel_middleware.py` captures spans via an in-memory exporter and asserts (a) all three custom attributes are populated on every agent-step span, AND (b) when the exporter raises (simulating Application Insights unavailability per spec edge case "Telemetry pipeline unavailable"), the agent invocation completes successfully and the exception is swallowed.

### Equivalence harness scaffold

- [X] T023 Implement `apps/agents/maf_runtime/equivalence/scorers.py::score(legacy_outputs, maf_outputs, agent_name) -> EquivalenceReport` implementing the FR-023 rule: ≥95% decision-equivalence on enumerated categorical fields + 100% schema-equivalence on populated fields, free-text fields excluded
  - **Agents**: qa-test-engineer, ai-ml-engineer, principal-engineer
  - **Tools**: read, edit
  - **Success**: `tests/unit/test_equivalence_scorers.py` covers (a) a corpus that satisfies both thresholds (PASS), (b) one categorical disagreement above the 5% budget (FAIL), (c) one missing populated field (FAIL), (d) free-text divergence only (PASS).

- [X] T024 Implement `apps/agents/maf_runtime/equivalence/runner.py` CLI: loads per-agent fixtures from `tests/equivalence/fixtures/<agent>/` (which symlinks into existing per-agent fixtures + spec-025 audit fixtures), replays each through both legacy pipeline and MAF agent, scores with T023, emits `apps/agents/maf_runtime/equivalence/reports/<agent>-<UTC-timestamp>.{md,json}`. ALL error types raised by the equivalence harness MUST be imported from `apps/agents/maf_runtime/errors.py` (T011b) — no locally-defined error classes
  - **Agents**: qa-test-engineer, ai-ml-engineer
  - **Tools**: read, edit, execute
  - **Success**: `python -m apps.agents.maf_runtime.equivalence.runner --agent monitoring --dry-run` succeeds against an empty fixtures directory and produces a valid report with zero items (used to wire the CI gate before fixtures are populated).

### Dashboard regression baseline (must be captured BEFORE any per-agent cutover)

- [X] T024b **Capture the existing-dashboard field snapshot** by running a one-time job that walks every workbook query under `infra/bicep/modules/dashboards/`, extracts every referenced field name (KQL columns, Application Insights span attributes, Cosmos query projections), and writes the canonical snapshot to `tests/contract/snapshots/existing_dashboard_fields.json`. This snapshot is the input that T060b's regression test asserts against AFTER cutover. MUST run in Foundational phase so the snapshot reflects pre-MAF state regardless of when individual agent cutovers occur in US1
  - **Agents**: sre-engineer, qa-test-engineer, observer-auditor
  - **Tools**: read, edit, execute, search
  - **Success**: `tests/contract/snapshots/existing_dashboard_fields.json` is committed; running the snapshot-capture script a second time against unchanged dashboards produces a byte-equal file (deterministic).

### API surface foundation

- [X] T025 [P] Add `apps/api/app/api/routes/workflow_runs.py` skeleton with the **six** endpoints from `contracts/workflow-runs.api.md` (list, get, checkpoints, audit, cancel, approval-gate metrics) returning 501 Not Implemented placeholders, and register the router in `apps/api/app/api/router.py`
  - **Agents**: api-architect, software-developer
  - **Tools**: read, edit
  - **Success**: `curl -X GET http://localhost:8000/api/workflow_runs` returns 501; OpenAPI document at `/openapi.json` lists all six endpoints under the `workflow_runs` tag.

**Checkpoint**: Cosmos containers, immutability policy, MAF chat-client, OTel bootstrap, run-state enum, feature flags, repositories, checkpoint storage + retention, three middleware modules, equivalence scorer + runner skeleton, and the API router skeleton are all in place. User story phases can begin.

---

## Phase 3: User Story 1 — Five Named Agents on a Common Agent Abstraction (Priority: P1) 🎯 MVP

**Goal**: Each of the five named agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication) runs as a MAF ChatAgent, produces typed schema-validated output, inherits the three foundational middleware bindings, and passes its FR-023 equivalence test against the legacy pipeline.

**Independent Test**: For each agent, `python -m apps.agents.maf_runtime.agents.<agent> --input <fixture>.json` returns a schema-valid output; the equivalence harness reports ≥95% categorical / 100% schema PASS against the existing fixture corpus; an audit entry exists in `audit_entries` for the invocation.

### Per-agent definition + ChatAgent + equivalence (5 agents in parallel)

- [X] T026 [P] [US1] Author agent definition `apps/agents/maf_runtime/agents/monitoring.yaml` conforming to `contracts/agent-definition.schema.yaml` (model_tier=`reasoning`, output_schema = existing Pydantic model under `domain.models`, middleware = [content_safety, audit, otel], empty tool_allow_list)
  - **Agents**: ai-ml-engineer, software-developer, observer-auditor
  - **Tools**: read, edit
  - **Success**: `python -m jsonschema --instance apps/agents/maf_runtime/agents/monitoring.yaml --schema specs/033-maf-adoption/contracts/agent-definition.schema.yaml` validates.

- [X] T027 [P] [US1] Implement `apps/agents/maf_runtime/agents/monitoring_agent.py` — loads `monitoring.yaml`, builds a MAF `ChatAgent` backed by T012's chat client, binds the three foundational middleware, exposes `async run(input: SignalEnvelope) -> MonitoringTriageDecision`, and a `__main__` block that consumes a JSON fixture from stdin
  - **Agents**: ai-ml-engineer, software-developer
  - **Tools**: read, edit, search
  - **Success**: Smoke test `python -m apps.agents.maf_runtime.agents.monitoring_agent` against `tests/fixtures/monitoring/sample_signal.json` returns a `MonitoringTriageDecision` JSON document; a fresh audit entry appears via the audit middleware.

- [X] T028 [P] [US1] Author agent definition `apps/agents/maf_runtime/agents/risk_assessment.yaml`
  - **Agents**: ai-ml-engineer, risk-manager, software-developer
  - **Tools**: read, edit
  - **Success**: Schema validation as in T026.

- [X] T029 [P] [US1] Implement `apps/agents/maf_runtime/agents/risk_assessment_agent.py` mirroring T027 (loads YAML, ChatAgent, middleware, `__main__`)
  - **Agents**: ai-ml-engineer, risk-manager, software-developer
  - **Tools**: read, edit
  - **Success**: Smoke test with a representative fixture returns a schema-valid `HazardAssessment` and produces an audit entry.

- [X] T030 [P] [US1] Author agent definition `apps/agents/maf_runtime/agents/evacuation.yaml`
  - **Agents**: ai-ml-engineer, software-developer, ses-nsw, nswpf
  - **Tools**: read, edit
  - **Success**: Schema validation.

- [X] T031 [P] [US1] Implement `apps/agents/maf_runtime/agents/evacuation_agent.py` mirroring T027
  - **Agents**: ai-ml-engineer, software-developer
  - **Tools**: read, edit
  - **Success**: Smoke test returns a schema-valid `EvacuationPlan`.

- [X] T032 [P] [US1] Author agent definition `apps/agents/maf_runtime/agents/resource_allocation.yaml`
  - **Agents**: ai-ml-engineer, logistics-officer, software-developer
  - **Tools**: read, edit
  - **Success**: Schema validation.

- [X] T033 [P] [US1] Implement `apps/agents/maf_runtime/agents/resource_allocation_agent.py` mirroring T027
  - **Agents**: ai-ml-engineer, logistics-officer, software-developer
  - **Tools**: read, edit
  - **Success**: Smoke test returns a schema-valid `ResourceAllocationPlan`.

- [X] T034 [P] [US1] Author agent definition `apps/agents/maf_runtime/agents/communication.yaml`
  - **Agents**: ai-ml-engineer, public-information-officer, accessibility-tester, software-developer
  - **Tools**: read, edit
  - **Success**: Schema validation.

- [X] T035 [P] [US1] Implement `apps/agents/maf_runtime/agents/communication_agent.py` mirroring T027 — but include a clearly-marked TODO that the public-alert step still needs the HITL request port (delivered in US2/T046); for now the agent returns a draft alert without publishing
  - **Agents**: ai-ml-engineer, public-information-officer, software-developer
  - **Tools**: read, edit
  - **Success**: Smoke test returns a schema-valid `AlertDraft`; no public-channel side effects occur (verified by mocking `delivery.py`).

### Per-agent equivalence harness (FR-023) — 5 in parallel

- [X] T036 [P] [US1] Populate `tests/equivalence/fixtures/monitoring/` (Python symlinks/refs into the existing `tests/{unit,integration,contract}/fixtures/monitoring/` and the spec-025 audit fixtures) and add `tests/equivalence/test_monitoring_equivalence.py` that runs T024 against the corpus and asserts ≥95% / 100%
  - **Agents**: qa-test-engineer, ai-ml-engineer
  - **Tools**: read, edit, execute, search
  - **Success**: `pytest tests/equivalence/test_monitoring_equivalence.py -q` PASSES; the latest report is committed under `apps/agents/maf_runtime/equivalence/reports/monitoring-*.md`.

- [X] T037 [P] [US1] Repeat T036 for Risk Assessment: `tests/equivalence/fixtures/risk_assessment/` + `tests/equivalence/test_risk_assessment_equivalence.py`
  - **Agents**: qa-test-engineer, risk-manager
  - **Tools**: read, edit, execute
  - **Success**: PASS; report committed.

- [X] T038 [P] [US1] Repeat T036 for Evacuation
  - **Agents**: qa-test-engineer, ses-nsw
  - **Tools**: read, edit, execute
  - **Success**: PASS; report committed.

- [X] T039 [P] [US1] Repeat T036 for Resource Allocation
  - **Agents**: qa-test-engineer, logistics-officer
  - **Tools**: read, edit, execute
  - **Success**: PASS; report committed.

- [X] T040 [P] [US1] Repeat T036 for Communication (note: equivalence runs against the legacy pipeline's pre-publication draft; HITL is not exercised here)
  - **Agents**: qa-test-engineer, public-information-officer
  - **Tools**: read, edit, execute
  - **Success**: PASS; report committed.

- [X] T040b [US1] Add `tests/unit/test_communication_prompt_invariant.py` enforcing FR-024a: the prompt string loaded from `apps/agents/maf_runtime/agents/communication.yaml` MUST be byte-equal to the legacy prompt constant in `apps/agents/communication/agent.py` (or a documented superset where the YAML adds machine-readable scaffolding around an unchanged human-readable prompt body); the populated output-field set MUST be unchanged. Backs Constitution V (Warnings — AWS, 10 principles) by preventing silent prompt drift
  - **Agents**: ai-ml-engineer, public-information-officer, security-engineer, accessibility-tester
  - **Tools**: read, edit, search
  - **Success**: A deliberate single-character edit to the YAML prompt body causes the test to fail; reverting passes; populated-field comparison runs against the spec-025 fixture corpus and reports zero deltas.

### CI integration of the equivalence gate

- [X] T041 [US1] Add a CI step `equivalence-gate` to `.github/workflows/ci.yml` that runs `pytest tests/equivalence/ -q` and refuses to merge a per-agent cutover PR (detected by file changes touching `apps/agents/maf_runtime/agents/<agent>.yaml`) whose corresponding equivalence test fails
  - **Agents**: infrastructure-devops, qa-test-engineer
  - **Tools**: read, edit, execute
  - **Success**: A deliberately-broken fixture in a draft PR causes the gate to fail; reverting passes the gate.

**Checkpoint US1**: All five agents are invocable in isolation through the new ChatAgent surface, every invocation produces schema-valid output and an audit entry, and each agent has an automated equivalence report. The MVP increment is deployable in `shadow` mode behind FR-026 fallback flags.

---

## Phase 4: User Story 2 — Reliable Multi-Agent Workflow with Crash Recovery and HITL (Priority: P1)

**Goal**: A single MAF Workflow orchestrates the five ChatAgents, persists checkpoints to Cosmos, resumes from checkpoint after a process restart with no re-execution, and pauses for HITL at the Communication agent's public-alert step — delegating identity to spec 008's existing approval store/queue.

**Independent Test**: Start an incident workflow against a fixture; kill the process after Risk Assessment; restart; verify the workflow resumes without re-running Risk Assessment and that it pauses at AwaitingApproval. Then approve via the existing spec-008 commander API; verify the alert publishes and the run reaches Completed. Verify SC-003 by attempting (and failing) to publish an alert without a recorded approval.

### Workflow + executors

- [X] T042 [US2] Implement five custom MAF `Executor` subclasses in `apps/agents/maf_runtime/workflow/executors/{monitoring,risk,evacuation,resource,communication}_executor.py`, each one reading `feature_flags.get_agent_mode(<agent>)` to dispatch to the legacy pipeline (`apps/agents/<agent>/agent.py`), the new ChatAgent from US1, or both (shadow); each executor MUST override `on_checkpoint_save` / `on_checkpoint_restore`
  - **Agents**: ai-ml-engineer, software-developer, principal-engineer
  - **Tools**: read, edit, search
  - **Success**: Unit test per executor proves all three modes (`legacy`, `maf`, `shadow`) dispatch correctly and `on_checkpoint_save` round-trips through `on_checkpoint_restore` byte-equal.

- [X] T042b [US2] Implement an output-schema validator inside every executor — placed in a shared base module `apps/agents/maf_runtime/workflow/executors/_base.py::validate_output(agent_definition, output)` that, after each step's agent invocation, deserialises the output through the Pydantic class declared by `agent_definition.output_schema`; on a `ValidationError`, the executor MUST raise `OutputSchemaMismatchError` (imported from `apps/agents/maf_runtime/errors.py`, T011b) and the workflow MUST transition the run to `NeedsOperatorDecision` per FR-011b and the spec edge case "An agent's output schema changes"
  - **Agents**: ai-ml-engineer, software-developer, principal-engineer
  - **Tools**: read, edit
  - **Success**: `tests/integration/test_output_schema_mismatch.py` injects a deliberately-malformed agent output, asserts `OutputSchemaMismatchError` is raised, asserts the run transitions to `NeedsOperatorDecision`, and asserts the audit entry has `outcome=failed` with `failure_reason` referencing the schema field that failed.

- [X] T042c [US2] Implement a per-executor retry budget in the shared `apps/agents/maf_runtime/workflow/executors/_base.py::with_retry_budget` decorator/context manager defaulting to **3 attempts** and **30 seconds total elapsed per step** per FR-012; on exhausted retries the executor MUST surface a typed error (from `apps/agents/maf_runtime/errors.py`, T011b) and the workflow MUST transition the run to `Failed` (failed-with-context) rather than dropping it. Retry bounds MUST be configurable per environment via `FEATURE_MAF_RUNTIME_RETRY_*` env vars (matches the FEATURE_MAF_RUNTIME_* prefix convention from T015). Per-error-class retry policy: `LlmRateLimitError` and `LlmServerError` are retryable; `LlmContentFilterError`, `LlmQuotaError`, `OutputSchemaMismatchError`, `ValidationFailure`, `ToolVersionMismatchError` are NOT retryable
  - **Agents**: sre-engineer, software-developer, principal-engineer
  - **Tools**: read, edit
  - **Success**: `tests/unit/test_executor_retry_budget.py` proves (a) a flaky-then-success step succeeds within budget, (b) a permanently-failing step exhausts the 3-attempt budget within 30 s and routes the run to `Failed`, (c) per-environment overrides via `FEATURE_MAF_RUNTIME_RETRY_*` are honoured, (d) non-retryable error classes fail fast on the first attempt without consuming the retry budget.

- [X] T043 [US2] Implement `apps/agents/maf_runtime/workflow/builder.py::build_workflow()` using `WorkflowBuilder` to wire the 5 executors as a directed graph (Monitoring → Risk Assessment → {Evacuation || Resource Allocation} → Communication), bind the T018 `CosmosCheckpointStorage`, and register the T046 HITL request port
  - **Agents**: ai-ml-engineer, software-developer, solution-architect
  - **Tools**: read, edit, web
  - **Success**: `python -m apps.agents.maf_runtime.workflow.builder --incident-fixture tests/fixtures/incidents/flood_level2.json --shadow` runs the full happy path end-to-end, persists ≥6 checkpoints, and exits cleanly with a `Completed` run document.

- [X] T044 [US2] Implement `apps/agents/maf_runtime/workflow/duration_watchdog.py` as a Container-Apps-compatible periodic task (5-minute interval) that scans `workflow_runs` for documents with `is_active=true AND now() - last_step_at > 72h`, transitions them to `NeedsOperatorDecision`, and writes an operator-visible alert (FR-012c)
  - **Agents**: sre-engineer, software-developer, observer-auditor
  - **Tools**: read, edit
  - **Success**: `tests/unit/test_duration_watchdog.py` proves a fake clock at +72h-epsilon does NOT transition; +72h+1s DOES transition and emits an alert; configurable threshold honoured.

### HITL — wraps spec 008

- [X] T045 [US2] Audit spec 008's existing approval queue and store: read `apps/agents/communication/approval.py`, the existing `ApprovalRequest` schema, and the existing `commander-approval-queue` Service Bus configuration. Document the discovered envelope in a new code comment block at the top of `apps/agents/maf_runtime/workflow/hitl_request_port.py`
  - **Agents**: software-developer, security-engineer, public-information-officer
  - **Tools**: read, search, agent
  - **Success**: The discovered fields exactly match the mapping in `contracts/hitl-request.envelope.md`; any drift triggers an update to the contract before T046 begins.

- [X] T046 [US2] Implement `apps/agents/maf_runtime/workflow/hitl_request_port.py` with two functions: `wrap_request_info_event(event) -> ApprovalRequest` (publishes to the existing `commander-approval-queue`, never to a new queue) and `on_decision_received(decision)` (subscribes to the existing `commander-approval-decisions-queue`, looks up the run by `pending_request_id`, calls `Workflow.send_response`)
  - **Agents**: ai-ml-engineer, security-engineer, public-information-officer
  - **Tools**: read, edit, search
  - **Success**: `tests/integration/test_hitl_round_trip.py` runs the full Communication step with a stubbed Service Bus, verifies that `ApprovalRequest.alert.payload.metadata.maf_run_id` is populated, and that `on_decision_received("approve")` resumes the workflow and produces a published alert.

- [X] T047 [US2] Add a static-analysis test `tests/unit/test_send_response_call_sites.py` that scans the entire repo and asserts the ONLY module that imports/calls `Workflow.send_response` is `apps/agents/maf_runtime/workflow/hitl_request_port.py` (Constitution NN-1 non-bypassability — see `contracts/hitl-request.envelope.md §5`)
  - **Agents**: security-engineer, principal-engineer, observer-auditor
  - **Tools**: read, edit, search
  - **Success**: A deliberately-added second call site causes the test to fail; reverting passes.

- [X] T048 [US2] Add an idempotency check inside `hitl_request_port.py::on_request_emitted` so that on workflow restore, if `approval_decisions` already has a recorded decision for the re-emitted `request_id`, the workflow auto-resolves rather than re-publishing to the commander queue (covers spec edge case "mid-workflow crash during a paused HITL step")
  - **Agents**: software-developer, sre-engineer
  - **Tools**: read, edit
  - **Success**: `tests/integration/test_hitl_resume.py` simulates crash mid-approval, verifies that re-launching does NOT cause a duplicate commander notification, and that an already-approved request resumes immediately.

- [X] T048b [US2] Add `tests/integration/test_hitl_concurrent_approval.py` proving the spec edge case "Two commanders approve the same alert simultaneously": fire two `on_decision_received` events for the same `request_id` from two distinct approver identities within milliseconds; assert exactly one decision wins, the workflow resumes once, the losing decision returns a typed `DuplicateDecisionConflictError`, and BOTH attempts are present in the `approval_decisions` audit trail
  - **Agents**: qa-test-engineer, security-engineer, public-information-officer
  - **Tools**: read, edit, execute
  - **Success**: Test PASSES; deliberately removing the conflict guard fails the test by causing a duplicate `Workflow.send_response` invocation (caught by T047's static check at runtime).

- [X] T048c [US2] Add `tests/integration/test_hitl_escalation_timeout.py` proving FR-010 still works through the wrapped envelope: simulate a pending approval that exceeds the configured spec-008 timeout; assert the spec-008 escalation message is delivered to the next commander in the chain; assert the workflow remains in `AwaitingApproval` (not `Cancelled` or `Failed`) until either an approve/reject/modify decision arrives or the configured maximum escalation level is exhausted (in which case the run transitions to `NeedsOperatorDecision`); the test MUST never auto-approve
  - **Agents**: qa-test-engineer, security-engineer, incident-commander, public-information-officer
  - **Tools**: read, edit, execute
  - **Success**: Test PASSES; mutation testing — flipping the auto-approve guard to true causes the test to fail (proving the FR-010 invariant is enforced).

### Crash recovery and capacity

- [X] T049 [US2] Implement `tests/integration/test_workflow_crash_recovery.py` — fault-injection harness that runs 100 trials per fixture: starts a workflow, kills the process at a randomised step boundary, restarts from checkpoint, asserts the re-launched run completes successfully without re-executing already-completed steps. Asserts ≥99/100 trials succeed (SC-002)
  - **Agents**: chaos-engineer, sre-engineer, qa-test-engineer
  - **Tools**: read, edit, execute
  - **Success**: `pytest tests/integration/test_workflow_crash_recovery.py -q` reports ≥99/100 successes; failures emit per-trial diagnostics; the test runs in <10 minutes wall-clock locally.

- [X] T050 [US2] Implement `tests/load/test_workflow_capacity.py` — Locust-style load harness validating FR-012b: 25 sustained concurrent active runs for 30 minutes + 50 burst for 60 minutes; asserts SC-007 (≤10% latency regression vs the legacy baseline captured in `tests/load/baselines/legacy_baseline.json`)
  - **Agents**: sre-engineer, qa-test-engineer, chaos-engineer
  - **Tools**: read, edit, execute
  - **Success**: Test produces a `tests/load/results/maf-<timestamp>.json` artefact with `p95_latency_ms <= 1.10 * baseline_p95_latency_ms` and zero workflow failures across the load window.

### Operator REST API + dashboard

- [X] T051 [US2] Replace the 501 stubs in `apps/api/app/api/routes/workflow_runs.py` with full implementations of all six endpoints from `contracts/workflow-runs.api.md` (list with status filter, get, checkpoints, audit, cancel, approval-gate metrics) backed by `WorkflowRunRepository`, the `audit_entries` container, and Application Insights for the metrics endpoint
  - **Agents**: api-architect, software-developer
  - **Tools**: read, edit, execute
  - **Success**: `tests/contract/test_workflow_run_api.py` exercises the documented schema for each endpoint; tenancy enforcement verified; cancel returns 409 on already-terminal runs.

- [X] T052 [P] [US2] Implement `apps/web/src/lib/api/workflow-runs.ts` — typed fetch client with `cache: "no-store"` per repo convention, exposing `listRuns(filters)`, `getRun(id)`, `listCheckpoints(id)`, `listAudit(id)`, `cancelRun(id, reason)`, `getApprovalGateMetrics(window)`
  - **Agents**: software-developer, api-architect
  - **Tools**: read, edit
  - **Success**: TypeScript types compile under `tsc --noEmit`; client maps cleanly to the OpenAPI types of T051.

- [X] T053 [P] [US2] Implement `apps/web/src/components/workflow/WorkflowRunList.tsx` rendering runs grouped into the 7 canonical state tabs (Running / AwaitingApproval / NeedsOperatorDecision / Completed / Failed / Cancelled / Superseded) with badge counts
  - **Agents**: ux-designer, software-developer, accessibility-tester
  - **Tools**: read, edit
  - **Success**: Component renders against fixture data; all 7 tabs are keyboard-navigable; meets WCAG 2.2 AA on the new component (verified via the existing axe test harness).

- [X] T054 [P] [US2] Implement `apps/web/src/components/workflow/WorkflowRunDetail.tsx` showing step-by-step progress, checkpoint timeline, an "AwaitingApproval — pending commander action" banner when applicable, and a deep-link to the OTel trace in Application Insights
  - **Agents**: ux-designer, software-developer
  - **Tools**: read, edit
  - **Success**: Storybook entry renders all four notable states (Running mid-step, AwaitingApproval, NeedsOperatorDecision, Failed-with-context); checkpoint timeline scrolls correctly with 50+ entries.

- [X] T055 [P] [US2] Implement `apps/web/src/app/operations/workflows/page.tsx` server component that composes T053 + T054 and is mounted under the existing `operations/` segment
  - **Agents**: software-developer, ux-designer
  - **Tools**: read, edit
  - **Success**: `next build` succeeds; the page renders against a mocked API client with no client-side fetch errors.

- [X] T056 [US2] Add `tests/contract/test_hitl_audit_invariant.py` proving SC-003: scan the last N production-style traces in a fixture and assert that every `alert.published` event has a corresponding `approval_decisions` document AND vice versa (no orphan publishes)
  - **Agents**: qa-test-engineer, observer-auditor, security-engineer
  - **Tools**: read, edit, execute
  - **Success**: Test PASSES against a clean fixture and FAILS when one decision is removed (proving the invariant detects gaps).

- [X] T056b [US2] Implement `apps/web/src/components/workflow/ApprovalGateMetrics.tsx` (initial day-one version) rendering MTTA / approvals / modifications / rejections / escalations / timeouts from `getApprovalGateMetrics(window)` with a default 24h window — moved into US2 from the original US3 placement so SC-008's "available on day one of cutover" invariant is satisfied at MVP cutover. Component is a **sibling** of `WorkflowRunDetail.tsx` (per `plan.md` project tree) and is composed alongside it in `apps/web/src/app/operations/workflows/page.tsx` so both paused-run context and approval-gate metrics surface on the same workflows page. T059 in US3 extends this component with selectable windows (1h / 7d / 30d)
  - **Agents**: ux-designer, software-developer
  - **Tools**: read, edit
  - **Success**: Component renders against fixture metrics with the 24h window only; numbers match the API response from T051; mounted as a sibling in the workflows page so an operator viewing a paused run sees both detail and approval-gate metrics without navigation.

**Checkpoint US2**: A real workflow runs, checkpoints durably, recovers from crashes ≥99/100 trials, pauses for HITL via spec 008, resumes correctly, and is fully visible/manageable through the operator API + dashboard. SC-002 + SC-003 + SC-007 + SC-008 are demonstrably met.

---

## Phase 5: User Story 3 — Cross-Cutting Safety, Audit, and Telemetry Without Per-Agent Boilerplate (Priority: P2)

**Goal**: Audit, content safety, and OTel telemetry are uniformly applied to every agent invocation by the foundational middleware (already shipped in Phase 2). This phase delivers the **verification artefacts** that prove uniformity, the daily reconciliation job, and the dashboard parity check that are required to claim SC-004, SC-005, SC-009, SC-010.

**Independent Test**: Add a synthetic "no-op" agent (T057) that contains no safety, audit, or telemetry code of its own; run it; verify (a) a content-safety verdict was recorded, (b) an audit entry exists with the same shape as the five real agents, (c) traces/metrics/logs appear in App Insights with the expected correlation ids — purely from the centralised middleware. Then verify the daily reconciliation job reports zero gap.

- [X] T057 [US3] Add a "no-op" agent under `tests/integration/no_op_agent/` consisting only of an Agent Definition YAML and a 10-line ChatAgent module with empty business logic; bind it to the three foundational middleware. This agent exists only as a worked example for SC-005 and SC-010
  - **Agents**: qa-test-engineer, principal-engineer, ai-ml-engineer
  - **Tools**: read, edit
  - **Success**: Invoking the no-op agent produces an audit entry, a content-safety verdict, and an OTel span with `workflow.run_id` populated — without writing any agent-side audit/safety/OTel code.

- [X] T058 [US3] Implement `apps/api/app/api/routes/admin/reconciliation.py::run_daily_reconciliation()` (also exposed as a scheduled Container Apps job) that for the previous 24h compares (invocation count from OTel) vs (audit-entry count) vs (workflow-step count), writes a `reconciliation_reports` Cosmos document, and emits a `reconciliation.gap` metric to App Insights for SC-004 alerting
  - **Agents**: sre-engineer, observer-auditor, data-engineer
  - **Tools**: read, edit
  - **Success**: Synthetic test injects a deliberate audit-emission failure; reconciliation reports the gap and emits the metric; alert rule fires within 5 minutes in dev.

- [X] T059 [P] [US3] **Extend** `apps/web/src/components/workflow/ApprovalGateMetrics.tsx` (the day-one version landed in T056b) with selectable windows (1h / 7d / 30d) added alongside the default 24h, and a richer historical view satisfying SC-008's "first-class operator dashboard" beyond the minimum cutover requirement
  - **Agents**: ux-designer, software-developer
  - **Tools**: read, edit
  - **Success**: Window switcher updates without a full reload; all four windows render correctly; numbers match the API response.

- [X] T060 [US3] Update the existing Application Insights workbook(s) under `infra/bicep/modules/dashboards/` to add an "Agent runs" panel keyed by `ai.agent.name` and a "Workflow runs by state" panel keyed by `workflow.run.state`, satisfying SC-009 (no per-agent dashboard gaps)
  - **Agents**: sre-engineer, ux-designer, infrastructure-devops
  - **Tools**: read, edit
  - **Success**: `az bicep build` succeeds; deploying to dev shows the two new panels populated by traffic from the no-op agent (T057).

- [X] T060b [US3] Add `tests/contract/test_existing_dashboards_no_regression.py` proving FR-017 + SC-009: read the pre-cutover snapshot from `tests/contract/snapshots/existing_dashboard_fields.json` (captured in Foundational phase by T024b), then assert every snapshotted field is still populated by at least one MAF-emitted span/metric/log for each of the five agents. Covers the "no per-agent telemetry gaps" guarantee
  - **Agents**: qa-test-engineer, sre-engineer, observer-auditor
  - **Tools**: read, edit, execute, search
  - **Success**: Test PASSES against the snapshot from T024b; deliberately removing one OTel attribute from `otel_middleware.py` causes the test to fail by reporting which dashboard query lost coverage.

- [X] T061 [US3] Document the worked example for SC-005 in `apps/agents/maf_runtime/middleware/README.md`: "How to add a new content-safety category in one place and have it apply to all five agents" — including a concrete diff that touches only `content_safety_middleware.py`
  - **Agents**: principal-engineer, security-engineer, software-developer
  - **Tools**: read, edit
  - **Success**: README's worked-example diff is a single-file change; rerunning the per-agent equivalence harness still PASSES (proves no agent-side code change required).

**Checkpoint US3**: Cross-cutting concerns demonstrably uniform; reconciliation job catches gaps within 24h; SC-004 / SC-005 / SC-008 / SC-009 / SC-010 all instrumented.

---

## Phase 6: User Story 4 — Out-of-Process Tools via MCP (Priority: P3)

**Goal**: The existing routing service is exposed to the Evacuation agent through `MCPStreamableHTTPTool`, with the agent allow-list pinning a major version per FR-019a. The agent calls the tool, receives a typed result, and version-mismatch / unreachable / timeout failures surface as typed errors rather than fabricated agent outputs.

**Independent Test**: Stand up the routing-service MCP server in dev; register it for the Evacuation agent at `pinned_major_version=1`; invoke the agent against a fixture that requires routing; verify a successful tool invocation appears in `audit_entries.tool_invocations`. Then deploy a v2 server without registering it; verify the next invocation fails with `outcome=version_mismatch` and an operator-visible alert is emitted.

- [X] T062 [P] [US4] Scaffold `tools/routing_mcp_server/` with `pyproject.toml` (dependency on `mcp`), `server.py` exposing the existing routing logic as MCP tools, and a `serverInfo` block advertising semantic version `1.0.0`
  - **Agents**: api-architect, software-developer, transport
  - **Tools**: read, edit, web
  - **Success**: `python -m tools.routing_mcp_server.server --port 9000` starts; `curl http://localhost:9000/mcp` returns a valid MCP `initialize` response with `serverInfo.version="1.0.0"`.

- [X] T063 [US4] Implement `apps/agents/maf_runtime/mcp/routing_tool.py` wrapping `MCPStreamableHTTPTool` against the registered routing-service address; reads `pinned_major_version` from `tool_registrations` and validates it against the server's advertised major; raises typed `ToolVersionMismatchError` on mismatch
  - **Agents**: ai-ml-engineer, security-engineer, software-developer
  - **Tools**: read, edit, web
  - **Success**: `tests/integration/test_mcp_routing_tool.py` covers (a) successful invocation, (b) `ToolVersionMismatchError` when the server advertises v2 but allow-list pins v1, (c) typed `ToolTimeoutError` when the server is slow, (d) typed `ToolUnreachableError` when the server is down, AND (e) typed `ToolMalformedResponseError` when the server returns invalid JSON or violates the MCP envelope schema (covers spec edge case "A registered MCP tool starts returning malformed responses"); all five errors imported from `apps/agents/maf_runtime/errors.py` (T011b).

- [X] T064 [P] [US4] Implement `apps/agents/maf_runtime/mcp/allow_list.py::resolve_allowed_tools(agent_name) -> list[ToolBinding]` that loads from `tool_registrations` via T017's repository and refuses any tool not on the agent's allow-list
  - **Agents**: security-engineer, software-developer
  - **Tools**: read, edit
  - **Success**: Unit test proves an agent attempting to invoke a non-allow-listed tool is rejected before any MCP call is made; the rejection is audited.

- [X] T065 [US4] Wire the routing tool into the Evacuation agent (T031) via `tool_allow_list` in `evacuation.yaml`, and update `evacuation_executor.py` to surface tool failures into the run's `failure_reason` rather than treating them as the agent's own failure
  - **Agents**: ai-ml-engineer, software-developer, ses-nsw, transport
  - **Tools**: read, edit
  - **Success**: A fixture incident that requires routing produces an `EvacuationPlan` whose audit entry includes the `tool_invocations` array with `tool_name=routing_service`, `version=1`.

- [X] T066 [US4] Add a deployment for the `routing-mcp-server` Container App in `infra/bicep/modules/`: internal-only ingress, managed identity, restricted to the same RG as `ca-agents-drh-{env}`
  - **Agents**: infrastructure-devops, security-engineer, docker-container-engineer
  - **Tools**: read, edit, execute
  - **Success**: `az deployment group what-if` against dev reports a single new container app `ca-routing-mcp-drh-dev` with internal ingress only and no public endpoint.

- [X] T067 [US4] Seed the initial tool registration via `scripts/register_mcp_tool.py --tool-name routing_service --address https://routing-mcp-drh-dev.<region>.azurecontainerapps.io/mcp --pinned-major-version 1 --bind-agents evacuation`
  - **Agents**: infrastructure-devops, software-developer
  - **Tools**: edit, execute
  - **Success**: A row appears in the `tool_registrations` container with composite id `routing_service:v1`; `resolve_allowed_tools("evacuation")` returns it.

- [X] T068 [US4] Add an Application Insights alert rule (Bicep) firing when `tool.outcome="version_mismatch"` count > 0 over 5 minutes (operator-visible alert per FR-019a)
  - **Agents**: sre-engineer, infrastructure-devops
  - **Tools**: read, edit, execute
  - **Success**: A synthetic mismatch in dev triggers the alert within 5 minutes; alert routes to the existing on-call email distribution list.

**Checkpoint US4**: Routing service is consumed by the Evacuation agent through a standard protocol with no tool-specific client code inside the agent runtime; SC-006 met; version-mismatch behaviour validated end-to-end.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Per-agent cutover playbook, legacy retirement, performance benchmark, quickstart validation.

- [ ] T069 [P] Author `docs/aidr/runbooks/maf-cutover-playbook.md`: per-agent cutover steps (shadow → maf → rollback) using the FEATURE_MAF_RUNTIME_<AGENT> env var, including the equivalence-report attachment requirement and the per-environment FR-012b load-test prerequisite
  - **Agents**: sre-engineer, infrastructure-devops, principal-engineer
  - **Tools**: read, edit
  - **Success**: A dry-run by a separate engineer (verified by a comment on the cutover PR template) successfully promotes the no-op agent from `legacy` to `maf` in dev using only the playbook.

- [ ] T070 [P] Author `docs/aidr/runbooks/maf-rollback.md` for the FR-026 fallback: how to flip a single agent back to legacy mid-incident; expected operator-visible signals during rollback
  - **Agents**: sre-engineer, incident-commander, observer-auditor
  - **Tools**: read, edit
  - **Success**: A dry-run rollback in dev completes within 5 minutes wall-clock and the next workflow run for that agent dispatches to the legacy code path.

- [ ] T071 Capture the legacy-pipeline performance baseline into `tests/load/baselines/legacy_baseline.json` (used by T050 to check the SC-007 ≤10% regression bar) by running the existing legacy pipeline against the same load profile for 60 minutes
  - **Agents**: sre-engineer, qa-test-engineer
  - **Tools**: execute, edit
  - **Success**: Baseline JSON contains `p50_latency_ms`, `p95_latency_ms`, `p99_latency_ms`, `error_rate`, `throughput_rps`; committed under git LFS if >100KB.

- [ ] T072 [P] Update `apps/agents/common/handoffs.py` with a deprecation banner pointing to `apps/agents/maf_runtime/workflow/builder.py` and the per-agent cutover playbook; do NOT remove the file (FR-026 fallback still needs it)
  - **Agents**: software-developer, principal-engineer
  - **Tools**: read, edit
  - **Success**: Module docstring carries a clear `DEPRECATED — superseded by maf_runtime/workflow/builder.py post-cutover` notice; existing imports still work.

- [ ] T073 Run the entire `quickstart.md` end-to-end in dev as written and capture results; fix any drift between the document and reality in a single follow-up PR
  - **Agents**: qa-test-engineer, software-developer
  - **Tools**: execute, read, edit
  - **Success**: All 9 sections of `quickstart.md` execute without manual intervention beyond the documented commands; the resulting report is appended as a new section "Last Validated: <date>".

- [ ] T074 [P] Update `apps/agents/maf_runtime/equivalence/reports/.gitkeep` and add `.gitignore` entry for `apps/agents/maf_runtime/equivalence/reports/*.json` (keep `.md` reports in repo as cutover evidence; keep raw JSON out of repo to control size)
  - **Agents**: software-developer
  - **Tools**: edit
  - **Success**: `git status` after a fresh equivalence run shows the new `.md` report as tracked and the `.json` as ignored.

- [ ] T074b Add `tests/unit/test_maf_runtime_error_imports.py` enforcing FR-004 import discipline: a static-analysis test that scans every Python module under `apps/agents/maf_runtime/` (excluding `errors.py` itself) and asserts no locally-defined `Exception` subclass exists. Every error type used inside the package MUST be imported from `apps/agents/maf_runtime/errors.py` (T011b). Runs in Polish phase so all downstream modules (T012, T016, T017, T018, T020, T021, T042b, T042c, T046, T048b, T063, T064) have had their chance to wire imports before the gate runs
  - **Agents**: principal-engineer, security-engineer, software-developer
  - **Tools**: read, edit, search, execute
  - **Success**: A deliberately-added local `class FakeError(Exception): pass` inside any `maf_runtime/` module fails the test; reverting passes; CI runs this gate as part of the Polish phase smoke-tests.

- [ ] T075 Run the full repo lint + test suite and the new `tests/equivalence/` + `tests/load/test_workflow_capacity.py` (capacity test in dev only) to assert no regression
  - **Agents**: qa-test-engineer
  - **Tools**: execute
  - **Success**: `ruff check apps tests packages` is clean; `python -m pytest tests/unit tests/integration tests/contract tests/equivalence -q --tb=line` passes; `pytest tests/load/test_workflow_capacity.py -q` PASSES against dev.

- [ ] T076 Run `/speckit.analyze` to cross-check spec ↔ plan ↔ tasks consistency and address any findings before merging
  - **Agents**: speckit.analyze, principal-engineer
  - **Tools**: agent, read, edit
  - **Success**: Analyze report has zero High-severity findings; any Medium findings are either resolved or explicitly accepted with a recorded justification in this `tasks.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories.
- **User Stories (Phases 3–6)**: All depend on Foundational completion.
  - **US1** is independent and is the MVP increment.
  - **US2** depends on US1's ChatAgent implementations (T026–T035) because the workflow executors dispatch to them when `mode=maf`. US2 also requires foundational HITL infrastructure assumptions about spec 008 to be true — verified in T045.
  - **US3** is largely independent because the foundational middleware is already in place; US3 adds the verification artefacts and reconciliation job.
  - **US4** depends on US1's Evacuation agent (T031) being implementable but does NOT need US2 to be complete; the routing tool can be exercised against the isolated Evacuation agent first.
- **Polish (Phase 7)**: Depends on US1+US2+US3 minimum (US4 is P3 and may follow polish for the first three stories).

### User Story Dependencies — quick reference

- US1 → independent, MVP candidate.
- US2 → depends on US1 ChatAgents (T026–T035).
- US3 → independent of US2 (uses no-op agent T057 as proof); can start in parallel with US2 once foundational middleware is in place.
- US4 → depends on US1 Evacuation (T031); independent of US2 and US3.

### Parallel Opportunities

- T002, T003, T004, T005, T006 in Phase 1 (different files).
- T010, T011 in Phase 2 (policy edits).
- T014, T015, T017, T022 in Phase 2 (different modules, no shared mutable state).
- All 5 agent definitions (T026, T028, T030, T032, T034) in parallel.
- All 5 ChatAgent modules (T027, T029, T031, T033, T035) in parallel.
- All 5 equivalence harness instances (T036–T040) in parallel.
- T052, T053, T054, T055, T059 in US2/US3 (different web files).
- T062, T064 in US4.
- T069, T070, T072, T074 in Polish.

### Within Each User Story

- Definitions (`*.yaml`) before ChatAgent modules (`*_agent.py`).
- ChatAgent modules before equivalence tests.
- Equivalence tests before per-agent cutover.
- Workflow builder (T043) after all 5 executors (T042) and after `CosmosCheckpointStorage` (T018).
- HITL request port (T046) after spec-008 audit (T045).
- Operator dashboard (T053–T055) after API endpoints (T051).
- MCP routing tool (T063) after routing-service MCP server (T062) and allow-list (T064).

---

## Parallel Example: User Story 1

```bash
# Launch the 5 agent-definition tasks together (different YAML files):
Task: T026 [P] Author monitoring.yaml
Task: T028 [P] Author risk_assessment.yaml
Task: T030 [P] Author evacuation.yaml
Task: T032 [P] Author resource_allocation.yaml
Task: T034 [P] Author communication.yaml

# Then launch the 5 ChatAgent modules in parallel (different .py files):
Task: T027 [P] Implement monitoring_agent.py
Task: T029 [P] Implement risk_assessment_agent.py
Task: T031 [P] Implement evacuation_agent.py
Task: T033 [P] Implement resource_allocation_agent.py
Task: T035 [P] Implement communication_agent.py

# Then run the 5 equivalence harnesses in parallel:
Task: T036 [P] Equivalence: monitoring
Task: T037 [P] Equivalence: risk_assessment
Task: T038 [P] Equivalence: evacuation
Task: T039 [P] Equivalence: resource_allocation
Task: T040 [P] Equivalence: communication
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1 (Setup) — install MAF SDK, scaffold package, write ADRs.
2. Complete Phase 2 (Foundational) — Cosmos containers, middleware, repositories, equivalence scorer.
3. Complete Phase 3 (US1) — five ChatAgents + per-agent equivalence reports.
4. **STOP and VALIDATE**: invoke each of the five agents in isolation; equivalence reports PASS; audit entries land.
5. Cut the first agent over to `shadow` mode in dev for 24 hours; review live reconciliation; promote to `maf` if clean.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. US1 → MVP; per-agent shadow → maf cutover in dev (one agent at a time, easiest first — Monitoring is recommended).
3. US2 → workflow + checkpointing + HITL; cutover the multi-agent flow once all five agents are at `maf` in dev.
4. US3 → reconciliation + dashboards + worked example; SC-005 and SC-010 demonstrably met.
5. US4 → MCP routing tool; demonstrate the SC-006 evidence.
6. Polish → playbooks, baseline, quickstart validation, `/speckit.analyze`.

### Parallel Team Strategy

With multiple developers after Phase 2 completes:

- Developer A (ai-ml-engineer): owns US1 (T026–T040) + handoff to US4.
- Developer B (software-developer + sre-engineer): owns US2 (T042–T056).
- Developer C (security-engineer + observer-auditor): owns US3 (T057–T061) and the Constitution NN-1 invariants (T047, T056).
- Developer D (infrastructure-devops): owns US4 infra (T062, T066, T068) and Polish runbooks (T069, T070).

---

## Notes

- [P] tasks = different files, no incomplete dependency on a non-[P] task in the same phase.
- [Story] label maps each task to a user story in `spec.md` for traceability.
- Each user story is independently completable and testable per its **Independent Test** clause above.
- The HITL contract (`contracts/hitl-request.envelope.md`) is **non-bypassable by construction** — enforced by the static-analysis test T047.
- Audit + telemetry coverage is **enforced by reconciliation** — T058 fails CI if the gap is non-zero.
- The 7-state model is **enforced at the repository write boundary** — T014 + T016 reject illegal transitions and concurrent active runs.
- Constitution NN-1, NN-2, NN-3 are testable regression-protected: T047 (NN-1), T009 + T011 (NN-2), T020 (NN-3 via fingerprints not raw payloads).
