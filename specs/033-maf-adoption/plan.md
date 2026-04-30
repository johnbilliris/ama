# Implementation Plan: Microsoft Agent Framework (MAF) Adoption

**Branch**: `033-maf-adoption` | **Date**: 2026-04-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/033-maf-adoption/spec.md`

## Summary

Replace the current bespoke per-agent pipeline + ad-hoc handoff graph with a single Microsoft Agent Framework (MAF) runtime that hosts the five named operational agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication) as MAF **ChatAgents**, orchestrates them through a MAF **Workflow** with **Cosmos DB-backed checkpointing** for crash recovery, gates the Communication agent's public-alert step with a MAF **HITL `RequestPort`** that delegates approver identity to spec 008's existing approval store/queue, applies content safety and audit logging as MAF **agent middleware** (so a sixth agent inherits both for free), wires MAF telemetry through the existing `azure-monitor-opentelemetry` exporter into Application Insights, and exposes the routing service to agents through a MAF **`MCPStreamableHTTPTool`** with semver-pinned major versions per agent allow-list. Per-agent cutover is gated on a 95%-decision / 100%-schema **equivalence harness** (FR-023) and runs incrementally under the spec 029 progressive-delivery feature-flag mechanism.

Technical approach: keep the three runtimes (Next.js 16 web, FastAPI API, Python autonomous agents); install `agent-framework` Python SDK in `apps/agents`; introduce `apps/agents/maf_runtime/` as the new MAF host (ChatAgents, Executors, Workflow, middleware, MCP tools, Cosmos `CheckpointStorage`); reuse existing `AzureOpenAIChatClient` with `DefaultAzureCredential` (managed identity, no API keys, FR-025); add three new Cosmos containers (`workflow_runs`, `checkpoints` with 30-day TTL, `tool_registrations`) sharing the existing audit Cosmos account; reuse the existing `audit_entries` container (no TTL, 7-year retention via deny-delete policy) for the centralised middleware-emitted audit; reuse spec 008's existing Service Bus `commander-approval-queue` and Cosmos approval store for the HITL `RequestInfoEvent` round trip; add operator endpoints under `apps/api/app/api/routes/workflow_runs.py` (list/get/states/checkpoint history) and a new `apps/web/src/app/operations/workflows/` page with state filters; route the existing routing service behind `MCPStreamableHTTPTool`; per-environment cutover wrapped in `FEATURE_MAF_RUNTIME_*` flags consumed via the spec 029 mechanism.

## Technical Context

**Language/Version**:
- Agent runtime: Python 3.12 (matches `apps/agents`, `apps/api`)
- API: FastAPI / Python 3.12
- Web: Next.js 16.2 / TypeScript 5.x (Node 20 LTS) for new operator dashboard tab only
- Workflow definitions: Python 3.12 using `agent-framework` SDK (`WorkflowBuilder`, `Executor`, `AgentExecutor`, `RequestPort`)

**Primary Dependencies**:
- `agent-framework` (Microsoft Agent Framework Python SDK) — ChatAgents, Workflows, AgentExecutor, RequestPort, AgentMiddleware, FunctionMiddleware, MCP tool classes
- `agent-framework[azure-ai]` extra — `AzureOpenAIChatClient` with `azure_ad_token_provider` (managed identity)
- Existing `azure-monitor-opentelemetry` (already wired in `apps/agents/monitoring/agent.py:15-25`) — receives MAF traces/metrics/logs
- Existing `azure-cosmos` async SDK — backs `CosmosCheckpointStorage` (custom subclass of MAF `CheckpointStorage`) and `WorkflowRunRepository`
- Existing `azure-servicebus` SDK — receives HITL approval requests on `commander-approval-queue` (spec 008 unchanged)
- `mcp` (Model Context Protocol Python SDK) — peer dependency surfaced by `agent-framework`'s MCP tool classes; used by routing-service MCP server in `tools/routing_mcp_server/`
- Existing `pydantic` v2 — output schemas (FR-003), MAF agent_framework integrates natively

**Storage**:
- Workflow run records: Azure Cosmos DB container `workflow_runs` in the existing `ama-platform` account (`australiaeast`); partition key `/incident_id`; uniqueness on `incident_id + is_active=true` enforced in repository (FR-011a)
- Checkpoints: Azure Cosmos DB container `checkpoints` in same account; partition key `/run_id`; **container TTL = 2,592,000 s (30 days)** counting from `terminal_at` (FR-012a)
- Audit entries: existing `audit_entries` container (deny-delete via Cosmos role policy + Azure Policy initiative; effective 7-year online retention per FR-012a)
- Tool registrations: `tool_registrations` container in same account; partition key `/tool_name`; entry holds `address`, `pinned_major_version`, `bound_agents[]` (FR-019, FR-019a)
- HITL approval queue: existing Service Bus `commander-approval-queue` (spec 008 — no schema change; the new `RequestInfoEvent` payload is wrapped into the existing `ApprovalRequest` envelope)
- HITL approval store: existing Cosmos `approval_decisions` container (spec 008 — no schema change)
- Telemetry: Application Insights resource `appi-ama-{env}` (existing) — receives MAF spans, metrics, logs via `setup_observability(...)` at runtime startup

**Testing**:
- pytest for the new MAF runtime (`tests/unit/test_maf_runtime.py`, `tests/integration/test_workflow_resume.py`, `tests/contract/test_workflow_run_api.py`)
- New equivalence harness `tests/equivalence/` (FR-023): per-agent fixture-driven runner that scores 95% decision-equivalence and 100% schema-equivalence, gates per-agent cutover
- Synthetic crash-injection harness `tests/integration/test_workflow_crash_recovery.py` for SC-002 (≥99/100 successful resumes)
- Synthetic load test `tests/load/test_workflow_capacity.py` validating FR-012b (25 sustained / 50 burst) on a per-environment basis
- Existing repo test suite (~2,255 unit/integration/contract tests, ~6.5 min) continues to gate every PR

**Target Platform**:
- Agent runtime: Azure Container Apps `ca-agents-drh-{env}` (existing) — internal-only, managed identity, scales 0–N, in `rg-drh-{env}`
- Tools: Azure Container Apps for the routing-service MCP server (new internal-only container app) — managed identity, in same RG
- API: Azure Container Apps `ca-api-drh-{env}` (existing) — exposes `/api/workflow_runs/*` operator endpoints (managed identity to Cosmos)
- Web: Azure App Service `app-drh-{env}-*` (existing) — adds the workflows dashboard page; managed identity to API

**Project Type**: Web application monorepo (apps/web + apps/api + apps/agents already in place). This feature primarily evolves `apps/agents/` by introducing `maf_runtime/`, adds operator endpoints to `apps/api/`, adds a dashboard page to `apps/web/`, adds three Cosmos containers via `infra/bicep/modules/`, and adds `tools/routing_mcp_server/` as the first out-of-process MCP tool.

**Performance Goals**:
- End-to-end incident workflow latency ≤ 110% of legacy at 25 concurrent active runs (SC-007 + FR-012b)
- ≥ 99/100 successful workflow resume after fault injection (SC-002)
- 100% audit/telemetry coverage of agent invocations (SC-004) — automated daily reconciliation between invocation count, audit-entry count, and OTel-span count
- HITL pause-state visibility ≤ 10 seconds from `RequestInfoEvent` emit to operator dashboard surfacing (per SC-008's day-one latency clause)
- 0 public alerts emitted without recorded human approval (SC-003) — measured continuously in production

**Constraints**:
- All workloads, telemetry, audit, checkpoint storage MUST remain in `australiaeast` / `australiasoutheast` (Constitution NN-2). Sole exception: Foundry / Azure OpenAI model-hosting endpoints on the named carve-out from spec 029 (constitution v1.2.0).
- Managed identity only for Azure OpenAI, Cosmos DB, Service Bus, Application Insights, MCP tool servers (FR-025, NN-2 derived).
- HITL approval surface MUST delegate identity/authorization to spec 008's existing approval workflow (FR-009 clarification + Assumption); no parallel identity model.
- ChatClient choice: `AzureOpenAIChatClient` (no server-side session) — **`FoundryAgent` server-side sessions are excluded** because MAF documentation explicitly warns that server-side session state is not captured in checkpoints (research §R3); this is required to make FR-007 / SC-002 hold.
- Per-agent cutover gated on equivalence harness pass (FR-023).
- Workflow runs MUST be classifiable into the 7-state model (FR-011b) at all times; no transitive/intermediate states leaked to operators.
- Workflow run uniqueness MUST be enforced in the repository layer (Cosmos transactional batch on `incident_id` + `is_active=true`) — FR-011a.

**Scale/Scope**:
- 5 named agents migrated to MAF (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication)
- 1 multi-agent workflow definition replacing the existing handoff graph
- 1 first MCP tool server (routing-service) — additional tools follow same pattern
- 25 sustained / 50 burst concurrent active workflow runs supported (FR-012b)
- Per workflow run: ~7 agent steps (typical) → ~7 checkpoints → ~7 audit entries → ~7+ OTel spans
- Daily steady-state estimate: ~50–200 incidents/day across federation → ~350–1,400 audit entries/day from agent steps; ~2× that with tool calls
- Audit container 7-year retention: ~1M–3M audit entries/year sustained ≈ ~10M–30M total at horizon → well within Cosmos partition limits given `/incident_id` partitioning
- Checkpoint container with 30-day TTL post-terminal: typically < 100k live items at any time

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle / Non-Negotiable | Status | Evidence |
|---|----------------------------|--------|----------|
| 1 | I. Primacy of Life and Harm Reduction | ✅ PASS | HITL `RequestPort` (FR-008/009) blocks any public alert without recorded human approval; SC-003 = 0 auto-published alerts; checkpointing (FR-006/007) prevents incident-context loss mid-event. |
| 2 | II. National Emergency Management Principles | ✅ PASS | Continual-improvement principle realised via centralised audit (FR-014/015) and operator-visible run-state model (FR-011b); coordinated/integrated principles realised by single workflow definition replacing the 5-pipeline graph. |
| 3 | II-A. AIIMS Functional Alignment | ✅ PASS | Communication agent's HITL surface delegates to the existing AIIMS commander chain in spec 008 (FR-009 clarification) — no parallel identity model. |
| 4 | III. Multi-Hazard, Multi-Agency Design | ✅ PASS | Migration is hazard-agnostic; touches no hazard-specific decision logic (Out-of-Scope: "Adding new agent capabilities"). |
| 5 | IV. Transparency and Auditability | ✅ PASS | FR-013/014/015 (centralised middleware-emitted audit); FR-016/017 (full OTel coverage); SC-004 (100% reconciled coverage); audit entries 7-year online retention (FR-012a). |
| 6 | V. Warning and Public Information | ✅ PASS | Communication agent's prompt/output schema unchanged; AWS-tier and 10-warning-principle compliance carried forward via the existing Communication agent definition; HITL gate adds enforcement, does not weaken existing checks. |
| 7 | VI. Evacuation Framework | ✅ PASS | Evacuation agent's behaviour unchanged; only its hosting (ChatAgent abstraction) changes. Equivalence harness FR-023 verifies behavioural parity. |
| 8 | VII. Recovery Support | ✅ PASS | Recovery handoffs (`build_recovery_handoff`, `build_lessons_capture_handoff` in `apps/agents/common/handoffs.py`) are preserved as workflow edges; PPRR coverage unchanged. |
| 9 | VIII. Cloud Platform and Infrastructure | ✅ PASS | Azure Container Apps + Cosmos DB + Service Bus + App Insights + Azure OpenAI; Bicep IaC (3 new container definitions); Microsoft Agent Framework is Microsoft-first SDK. |
| NN-1 | Human-in-the-loop | ✅ PASS | FR-008 mandates HITL pause for every public-alert step; SC-003 = 0 auto-publish; spec 008's commander chain is the authority. |
| NN-2 | Data sovereignty (AU regions) | ✅ PASS | All new Cosmos containers, Service Bus, App Insights, Container Apps remain in `australiaeast`. Azure OpenAI deployments retain existing carve-out under constitution v1.2.0 (no new endpoints introduced by this feature). |
| NN-3 | Privacy by design | ✅ PASS | Audit fingerprints are SHA-256 hashes of inputs/outputs (not raw PII); content-safety middleware (Azure AI Content Safety) wraps every invocation; existing `data-minimisation at the model gateway` policy from spec 029 §carve-out continues to apply. |
| NN-4 | Interoperability | ✅ PASS | MAF Workflows expose typed contracts (Pydantic schemas in `apps/agents/common/handoff_payloads.py`); MCP is an open standard; OpenAPI for the new `/workflow_runs/*` endpoints; CAP/EDXL outputs of the Communication agent are unchanged. |
| NN-5 | Graceful degradation | ✅ PASS | FR-026 fallback flag (per-agent revert to legacy pipeline); checkpoint store unavailability halts the affected run with a typed error rather than proceeding without durability (Edge Cases); telemetry pipeline outage does not impact agent correctness (Edge Cases); MCP tool failure surfaces typed error rather than fabricating a result (FR-021). |
| QG | Quality Gates | ✅ PASS | Existing CI continues; equivalence harness (FR-023) is a per-agent cutover gate; load test (FR-012b) is a per-environment cutover gate; OPA/conftest gates from spec 029 continue to validate Bicep changes. |

### Recorded architecture decisions affecting this plan

- **ADR-033-01 — `AzureOpenAIChatClient`, not `FoundryAgent`, for ChatAgent backing** (research.md §R3). MAF documentation states that checkpointing with agents that use server-side sessions (e.g., `FoundryAgent`) has reliability limitations because server-side state is not captured in checkpoints. Because FR-007 / SC-002 require deterministic resume from checkpoint, all five MAF ChatAgents back onto `AzureOpenAIChatClient` with managed identity (`DefaultAzureCredential` → `get_bearer_token_provider("https://cognitiveservices.azure.com/.default")`). **Constitution impact: NN-1, NN-2, QG all PASS** under this choice.
- **ADR-033-02 — Cosmos DB backs the MAF `CheckpointStorage`** (research.md §R4). MAF ships a `FileCheckpointStorage` reference implementation; we implement `CosmosCheckpointStorage` that subclasses MAF's `CheckpointStorage` interface and reads/writes a partitioned `checkpoints` container in the existing audit account. This keeps every durable artefact in one regulated store, reuses the deny-delete + AU-residency policies, and avoids introducing a new persistence backend. **Constitution impact: NN-2 PASSES** because the new container is created in `australiaeast` by a new Bicep module `infra/bicep/modules/cosmos-workflow.bicep` (T008) targeting the existing Cosmos account.
- **ADR-033-03 — HITL `RequestPort` payload routes through spec 008's existing approval store/queue** (research.md §R5). The MAF workflow's `RequestInfoEvent` payload is wrapped into the existing `ApprovalRequest` envelope and emitted onto `commander-approval-queue` (existing Service Bus). On commander action, the existing approval-decision Cosmos write triggers an existing handler that calls `Workflow.send_response(...)` to resume the run. **Constitution impact: NN-1 PASSES** with the existing AIIMS chain semantics; this feature introduces no parallel identity or escalation model.
- **ADR-033-04 — `MCPStreamableHTTPTool` for the routing service** (research.md §R6). The routing service is a long-lived containerised process; HTTP-streamable MCP is the right transport (vs. stdio, which suits per-process spawn, or websockets, which add operational complexity in Azure Container Apps). The agent's tool allow-list pins major version per FR-019a; the MCP server advertises its semver via the protocol's `serverInfo` block. **Constitution impact: NN-2, NN-4 PASS** — the MCP server runs in the same RG/region, exposes managed-identity-bound endpoints, and uses an open standard.

**Initial gate result: PASS — no violations to justify.** Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/033-maf-adoption/
├── spec.md              # Feature specification (clarified, 8/10 questions answered)
├── plan.md              # This file
├── research.md          # Phase 0 — research decisions (R1–R10)
├── data-model.md        # Phase 1 — entity model + state transitions
├── quickstart.md        # Phase 1 — operator/developer quickstart
├── contracts/           # Phase 1 — interface contracts
│   ├── agent-definition.schema.yaml          # Per-agent declarative definition (FR-002)
│   ├── workflow-run.schema.json              # Persisted workflow_run document (FR-011, FR-011a, FR-011b)
│   ├── checkpoint.schema.json                # Persisted checkpoint document (FR-006, FR-007)
│   ├── audit-entry.schema.json               # Centralised middleware-emitted audit (FR-014)
│   ├── tool-registration.schema.json         # MCP tool allow-list entry (FR-019, FR-019a)
│   ├── workflow-runs.api.md                  # Operator REST API (list/get/state-filter/checkpoint history)
│   └── hitl-request.envelope.md              # Spec-008-compatible wrapping of MAF RequestInfoEvent
├── checklists/
│   └── requirements.md  # Spec quality checklist (existing)
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root — files this feature evolves)

```text
apps/agents/
├── pyproject.toml                              # EVOLVE — adds `agent-framework`, `agent-framework[azure-ai]`, `mcp`
├── maf_runtime/                                # NEW — MAF host package (the new agent abstraction surface)
│   ├── __init__.py
│   ├── chat_client.py                          # Shared AzureOpenAIChatClient factory (managed identity, ADR-033-01)
│   ├── agents/                                 # NEW — five ChatAgent definitions (FR-001, FR-002)
│   │   ├── monitoring_agent.py
│   │   ├── risk_assessment_agent.py
│   │   ├── evacuation_agent.py
│   │   ├── resource_allocation_agent.py
│   │   └── communication_agent.py
│   ├── workflow/                               # NEW — single multi-agent workflow definition (FR-006)
│   │   ├── builder.py                          # WorkflowBuilder wiring; replaces apps/agents/common/handoffs.py edges
│   │   ├── executors/                          # AgentExecutor wrappers + custom Executors per agent step
│   │   │   ├── _base.py                        # NEW — shared base: validate_output (FR-011b schema check), with_retry_budget (FR-012)
│   │   │   ├── monitoring_executor.py
│   │   │   ├── risk_executor.py
│   │   │   ├── evacuation_executor.py
│   │   │   ├── resource_executor.py
│   │   │   └── communication_executor.py
│   │   ├── hitl_request_port.py                # RequestPort that wraps spec-008 ApprovalRequest envelope (ADR-033-03)
│   │   ├── run_state.py                        # 7-state enum + transition rules (FR-011b)
│   │   └── duration_watchdog.py                # FR-012c — 72h cap → NeedsOperatorDecision transition
│   ├── checkpoint/                             # NEW — Cosmos-backed CheckpointStorage (ADR-033-02)
│   │   ├── cosmos_checkpoint_storage.py        # subclass MAF CheckpointStorage; partition key /run_id
│   │   └── retention.py                        # 30-day TTL helper aligned with FR-012a
│   ├── middleware/                             # NEW — cross-cutting agent + function middleware (FR-013, FR-014, FR-015, FR-016)
│   │   ├── content_safety_middleware.py        # Wraps existing ContentSafetyValidator (apps/agents/common/content_safety.py)
│   │   ├── audit_middleware.py                 # Emits to existing audit_entries container; SHA-256 fingerprints
│   │   └── otel_middleware.py                  # Adds agent-step span attributes (agent name, model, tokens, run_id link)
│   ├── mcp/                                    # NEW — MCP tool client wrappers (FR-018, FR-019, FR-019a)
│   │   ├── routing_tool.py                     # MCPStreamableHTTPTool bound to routing service; major-version-pinned
│   │   └── allow_list.py                       # Per-agent tool allow-list loader; refuses non-allow-listed calls
│   ├── repositories/                           # NEW — Cosmos repos for workflow_runs, tool_registrations
│   │   ├── workflow_run_repository.py          # Enforces FR-011a uniqueness via Cosmos transactional batch
│   │   └── tool_registration_repository.py     # Backs FR-019a major-version match
│   ├── equivalence/                            # NEW — equivalence harness (FR-023)
│   │   ├── runner.py                           # Loads spec-025 fixtures + existing test fixtures
│   │   ├── scorers.py                          # 95% categorical decision + 100% schema scoring
│   │   └── reports/                            # Per-agent equivalence report artefact (Markdown + JSON)
│   ├── feature_flags.py                        # Per-agent FEATURE_MAF_RUNTIME_<AGENT> + retry overrides FEATURE_MAF_RUNTIME_RETRY_* (FR-026; consumes spec 029 mechanism)
│   ├── errors.py                               # NEW — canonical typed error hierarchy required by FR-004 (T011b)
│   └── observability.py                        # Calls setup_observability with the existing Azure Monitor exporter
├── monitoring/                                 # KEEP — legacy pipeline retained behind FR-026 fallback flag during cutover
├── risk_assessment/                            # KEEP — legacy pipeline retained behind FR-026 fallback flag during cutover
├── evacuation/                                 # KEEP — legacy pipeline retained behind FR-026 fallback flag during cutover
├── resource_allocation/                        # KEEP — legacy pipeline retained behind FR-026 fallback flag during cutover
├── communication/                              # KEEP — legacy pipeline retained behind FR-026 fallback flag during cutover
└── common/
    ├── content_safety.py                       # KEEP — wrapped by content_safety_middleware
    ├── handoffs.py                             # DEPRECATE post-cutover — superseded by workflow/builder.py + executors
    └── handoff_payloads.py                     # KEEP — typed payloads reused as workflow edge data

apps/api/
└── app/api/routes/
    └── workflow_runs.py                        # NEW — operator REST API (list, get, filter-by-state, checkpoint history)

apps/web/
└── src/
    ├── app/operations/workflows/page.tsx       # NEW — workflows dashboard with state-filter tabs (FR-011, SC-008)
    ├── components/workflow/
    │   ├── WorkflowRunList.tsx                 # Lists runs grouped by 7 canonical states
    │   ├── WorkflowRunDetail.tsx               # Step-by-step view + checkpoint timeline + HITL pause indicator
    │   └── ApprovalGateMetrics.tsx             # MTTA / escalation rate / timeout rate (SC-008)
    └── lib/api/workflow-runs.ts                # Typed client (native fetch, cache: "no-store" per repo convention)

tools/                                          # NEW — out-of-process tool servers (first MCP server)
└── routing_mcp_server/
    ├── pyproject.toml                          # `mcp` SDK; FastAPI optional but mcp lib serves Streamable HTTP natively
    ├── server.py                               # Wraps existing routing logic; advertises serverInfo with semver
    └── README.md                               # How to run locally; how the agent allow-list pins its major version

infra/
├── bicep/
│   └── modules/
│       └── cosmos-workflow.bicep               # NEW — adds workflow_runs, checkpoints (TTL=30d), tool_registrations containers in existing account
└── policy/                                     # EVOLVE (additive) — extend deny-delete policy to cover audit_entries permanently
    └── deny_audit_delete.rego                  # NEW — supports FR-012a 7-year online retention; consumed by spec 029 OPA gate

tests/
├── unit/
│   ├── test_maf_runtime_chat_client.py         # NEW
│   ├── test_run_state_transitions.py           # NEW — covers all 7 states + invalid-transition rejection (FR-011b)
│   ├── test_duration_watchdog.py               # NEW — FR-012c 72h cap behaviour
│   ├── test_audit_middleware.py                # NEW — FR-014 fingerprint + immutability
│   ├── test_content_safety_middleware.py       # NEW — FR-013 centralisation; bypass test = fail
│   ├── test_otel_middleware.py                 # NEW — FR-016 span attributes
│   ├── test_tool_allow_list.py                 # NEW — FR-019, FR-019a major-version mismatch test
│   └── test_workflow_run_uniqueness.py         # NEW — FR-011a enforcement
├── integration/
│   ├── test_workflow_resume.py                 # NEW — SC-002 fault-injection (≥99/100 trials)
│   ├── test_hitl_round_trip.py                 # NEW — RequestPort → spec-008 queue → resume
│   └── test_mcp_routing_tool.py                # NEW — US4 acceptance scenarios (typed result, typed error, version mismatch)
├── contract/
│   ├── test_workflow_run_api.py                # NEW — exercises contracts/workflow-runs.api.md
│   ├── test_audit_entry_schema.py              # NEW — contracts/audit-entry.schema.json
│   └── test_agent_definition_schema.py         # NEW — contracts/agent-definition.schema.yaml
├── equivalence/                                # NEW — per-agent harness (FR-023)
│   ├── test_monitoring_equivalence.py
│   ├── test_risk_assessment_equivalence.py
│   ├── test_evacuation_equivalence.py
│   ├── test_resource_allocation_equivalence.py
│   ├── test_communication_equivalence.py
│   └── fixtures/                               # Symlinks/refs into spec-025 audit fixtures + existing per-agent fixtures
└── load/
    └── test_workflow_capacity.py               # NEW — FR-012b 25 sustained / 50 burst validation

docs/
└── aidr/
    └── decisions/
        ├── adr-033-01-azure-openai-chat-client.md  # NEW
        ├── adr-033-02-cosmos-checkpoint-storage.md # NEW
        ├── adr-033-03-hitl-spec-008-delegation.md  # NEW
        └── adr-033-04-mcp-streamable-http.md       # NEW
```

**Structure Decision**: Web application monorepo (apps/web + apps/api + apps/agents already in place). This feature primarily evolves `apps/agents/` by introducing a new sub-package `maf_runtime/` (the new MAF host) while keeping the five legacy per-agent packages (`monitoring/`, `risk_assessment/`, `evacuation/`, `resource_allocation/`, `communication/`) intact behind the FR-026 fallback flag during the per-agent cutover window. Three Cosmos containers are added via a new Bicep module reusing the existing audit account. New operator-facing REST endpoints land in `apps/api/app/api/routes/workflow_runs.py` and a new dashboard page at `apps/web/src/app/operations/workflows/page.tsx`. The first out-of-process MCP tool server lives at `tools/routing_mcp_server/`. New test directories `tests/equivalence/` and `tests/load/` join the existing `tests/{unit,integration,contract,load}/` layout.

## Complexity Tracking

> No constitutional violations to justify; section intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Phase 0 — Research

See [research.md](./research.md) for the resolved research log. Summary of decisions:

- **R1: MAF Python SDK is the right framework** — `pip install agent-framework` provides ChatAgent, Workflow (graph-based), AgentExecutor, RequestPort/RequestInfoEvent (HITL), AgentMiddleware/FunctionMiddleware, MCP tool classes, OpenTelemetry-first observability — i.e., everything the spec asks for in one place.
- **R2: Workflow shape — `WorkflowBuilder` with custom `Executor` subclasses wrapping each ChatAgent** (rather than five `AgentExecutor`s only). Custom executors give us per-agent step boundaries we control for checkpointing and let us emit our exact audit fingerprint at the boundary.
- **R3: ChatClient choice — `AzureOpenAIChatClient`, NOT `FoundryAgent`** (ADR-033-01) — server-side sessions break checkpoint reliability per MAF docs.
- **R4: Checkpoint backend — Custom `CosmosCheckpointStorage`** (ADR-033-02) subclassing MAF's `CheckpointStorage` interface (`save_checkpoint`, `load_checkpoint`, `list_checkpoints`); MAF's reference `FileCheckpointStorage` is for samples only.
- **R5: HITL approver delegation — wrap `RequestInfoEvent` into spec 008's `ApprovalRequest` envelope** (ADR-033-03) — no new identity model; existing escalation timer and AIIMS chain are reused unchanged.
- **R6: MCP transport — `MCPStreamableHTTPTool`** (ADR-033-04) — long-lived container apps can't be `stdio`; `MCPWebsocketTool` adds operational complexity without benefit; HTTP-Streamable matches the routing service's existing FastAPI-style deployment shape.
- **R7: Telemetry wiring — call `setup_observability(...)` once at runtime startup** (`apps/agents/maf_runtime/observability.py`) so MAF's built-in OpenTelemetry instrumentation auto-emits spans/metrics/logs through the existing `azure-monitor-opentelemetry` exporter (already configured in `apps/agents/monitoring/agent.py`); add custom span attributes via `otel_middleware.py` for run_id linkage.
- **R8: Audit immutability — Cosmos `audit_entries` container with deny-delete role policy + Azure Policy initiative** — meets FR-014 immutability and FR-012a 7-year online retention without introducing a separate ledger product.
- **R9: Equivalence harness shape — fixture-driven runner that replays the spec-025 audit fixtures + existing test fixtures through both legacy pipeline and MAF agent, scores 95% decision-equivalence + 100% schema-equivalence per FR-023, emits per-agent Markdown + JSON report attached to the cutover PR**.
- **R10: Per-agent feature-flag cutover — `FEATURE_MAF_RUNTIME_<AGENT>` env-var per environment** (consumed via spec 029's flag mechanism); the workflow runtime can route a step to the legacy pipeline or the MAF ChatAgent at dispatch time, satisfying FR-022 (mixed migration) and FR-026 (per-agent fallback).

## Phase 1 — Design & Contracts

Outputs:
- [data-model.md](./data-model.md) — entity definitions, relationships, state transitions for the 7-state model (FR-011b)
- [contracts/](./contracts/) — schemas and interface contracts (agent definition, workflow run, checkpoint, audit entry, tool registration, operator REST API, HITL envelope)
- [quickstart.md](./quickstart.md) — operator and developer quickstart (run a workflow locally, inspect a paused HITL run, reissue checkpoint, register an MCP tool, run the equivalence harness for one agent)
- Agent context update — run `update-agent-context.ps1 -AgentType copilot`

### Re-evaluated Constitution Check (post-design)

Same matrix as the initial gate. The Phase 1 artefacts (workflow-run schema with the 7-state enum and the `prior_run_id` linkage; audit-entry schema with SHA-256 fingerprints rather than raw payloads; HITL envelope that strictly wraps spec 008 — no new identity fields; tool-registration schema with `pinned_major_version`; OpenAPI for `/workflow_runs/*` operator endpoints) all reinforce — and do not weaken — any constitutional obligation. Specifically:

- **NN-1 (HITL)** is strengthened by `hitl-request.envelope.md` proving the wrapping is non-bypassable (no direct `Workflow.send_response(...)` path that does not flow through spec 008's commander queue).
- **NN-2 (data sovereignty)** is preserved by the new Bicep module placing all three containers in the existing `australiaeast` account; no new region introduced.
- **NN-3 (privacy by design)** is reinforced by `audit-entry.schema.json` mandating SHA-256 fingerprints rather than raw input/output bodies in the audit store.
- **NN-4 (interoperability)** is reinforced by `agent-definition.schema.yaml` (declarative, version-controlled, language-agnostic) and by MCP being an open standard for tool integration.
- **NN-5 (graceful degradation)** is reinforced by `workflow-run.schema.json` requiring the `prior_run_id` link, and by `tool-registration.schema.json` typed version-mismatch error contract.

**Post-design gate result: PASS.**

---

**Phase 2 (tasks)** is produced by `/speckit.tasks`, not by this command.
