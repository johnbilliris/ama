# Phase 0 Research — MAF Adoption

**Feature**: 033-maf-adoption  
**Date**: 2026-04-30  
**Status**: Complete — all research items resolved; no NEEDS CLARIFICATION remain

This research log resolves the architectural and integration choices that the spec deferred to planning. Each item follows the **Decision / Rationale / Alternatives Considered** format.

---

## R1 — Framework choice: Microsoft Agent Framework Python SDK

- **Decision**: Adopt `agent-framework` (Microsoft Agent Framework) Python SDK as the agent + workflow runtime.
- **Rationale**: Spec input names MAF directly. MAF combines AutoGen-style simple agent abstractions with Semantic Kernel-style enterprise features (typed agents, middleware, telemetry, MCP) and adds graph-based workflows with first-class checkpointing and HITL — i.e., it natively covers all four spec scope items (ChatAgent, Workflow + checkpoint + HITL, middleware + telemetry, MCP) in one package. MAF docs: <https://learn.microsoft.com/agent-framework/overview/>.
- **Alternatives Considered**:
  - **Semantic Kernel alone** — lacks first-class graph workflows, checkpointing, and `RequestPort` HITL primitive; would require building those.
  - **AutoGen** — Microsoft has positioned MAF as the go-forward consolidation of AutoGen + Semantic Kernel; the AutoGen → MAF migration guide is published, indicating AutoGen is no longer the recommended target.
  - **Custom orchestration** — already what we have today; this entire feature exists because that approach scales poorly.
  - **LangGraph / CrewAI / others** — non-Microsoft; introduces a new third-party dependency without Azure-native integrations and runs counter to Constitution VIII (Azure-native services preferred).

---

## R2 — Workflow shape: `WorkflowBuilder` with custom `Executor` subclasses wrapping each ChatAgent

- **Decision**: Use `WorkflowBuilder` to define the multi-agent flow as a directed graph of custom `Executor` subclasses; each executor wraps one MAF ChatAgent and is the unit of audit/checkpoint/telemetry boundary.
- **Rationale**: MAF's pre-baked `AgentExecutor` is convenient for trivial cases but does not give us a clean place to emit our exact audit fingerprint contract (FR-014) or to enforce the FR-011b state-transition rules at the boundary. Custom executors give us a single, uniform place to apply middleware in the order we need (content-safety → invoke ChatAgent → audit), to decide whether to dispatch to the legacy pipeline (FR-026 fallback) or to the MAF ChatAgent based on the per-agent feature flag, and to override `on_checkpoint_save` / `on_checkpoint_restore` with our own executor-state capture.
- **Alternatives Considered**:
  - **Five `AgentExecutor` instances only** — simpler but loses the per-step boundary control needed for FR-014 audit shape and FR-026 fallback dispatch.
  - **`GroupChat` orchestration** — wrong primitive: our flow is a deterministic graph (signal → triage → risk → evac/resource → comms), not an open-ended group chat.
  - **`Sequential` orchestration** — too rigid: evacuation and resource allocation can run in parallel for some categories.

---

## R3 — ChatClient: `AzureOpenAIChatClient` (managed identity), NOT `FoundryAgent`

- **Decision**: All five MAF ChatAgents back onto `AzureOpenAIChatClient` constructed with `azure_ad_token_provider=get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")`.
- **Rationale**: MAF documentation states (Agent Executor — Checkpointing): *"Checkpointing with agents that use server-side sessions (such as `FoundryAgent`) has limitations. Server-side session state is not captured in checkpoints and can be modified by subsequent runs."* Because FR-007 (resume from checkpoint without re-execution) and SC-002 (≥99/100 successful resumes) are P1 acceptance gates, we cannot use a ChatClient whose state is only partially captured by the checkpoint. `AzureOpenAIChatClient` keeps all conversational state client-side, where MAF's `AgentExecutor.on_checkpoint_save` already captures it. Managed-identity authentication satisfies FR-025 and Constitution NN-2.
- **Alternatives Considered**:
  - **`FoundryAgent`** — incompatible with reliable checkpointing (above).
  - **`OpenAIChatClient` (non-Azure)** — would require API-key auth (forbidden by FR-025) and break Australian data-sovereignty (NN-2).
  - **Anthropic / Ollama / other providers** — not on the AMA approved-models list; would require new compliance review.
- **Recorded as ADR-033-01.**

---

## R4 — Checkpoint backend: Custom `CosmosCheckpointStorage`

- **Decision**: Implement `apps/agents/maf_runtime/checkpoint/cosmos_checkpoint_storage.py` as a subclass of MAF's `CheckpointStorage` interface, backed by a new Cosmos DB container `checkpoints` (partition key `/run_id`, container TTL = 30 days from `terminal_at`) in the existing `ama-platform` Cosmos account.
- **Rationale**: MAF ships `FileCheckpointStorage` for samples; production MAF deployments are expected to plug their own implementation. Cosmos is already the system's durable, AU-resident, managed-identity-bound store; reusing it for checkpoints gives us one consistent backup/DR posture and avoids introducing a new persistence backend (Constitution VIII — Azure-native). The 30-day TTL is enforced at container level and matches FR-012a.
- **Alternatives Considered**:
  - **`FileCheckpointStorage`** — does not survive container restarts; defeats the entire crash-recovery purpose.
  - **Azure Blob Storage** — workable but lacks Cosmos's transactional batch and per-document TTL semantics needed for the FR-011a uniqueness check and FR-012a retention.
  - **Azure Table Storage** — older API surface; lacks per-row TTL; would force a custom retention sweep job.
  - **Azure SQL** — operational overhead (DBA, schema migrations) we don't otherwise need; relational shape is wrong for blob-of-state checkpoints.
- **Recorded as ADR-033-02.**

---

## R5 — HITL: wrap `RequestInfoEvent` into spec 008's existing `ApprovalRequest` envelope

- **Decision**: The MAF Workflow's HITL pause uses MAF's `RequestPort` primitive; the emitted `RequestInfoEvent` payload is wrapped into spec 008's existing `ApprovalRequest` envelope and emitted onto Service Bus `commander-approval-queue`. On commander action, the existing approval-decision Cosmos write triggers an existing handler that calls `Workflow.send_response(request_id, decision)` to resume the run.
- **Rationale**: The Q4 clarification pinned identity, authorization, and chain semantics to spec 008 unchanged. Wrapping `RequestInfoEvent` rather than introducing a parallel approval store/queue means: (a) the AIIMS commander chain, escalation timer, dual-control rules, and audit trail are already in production and this feature inherits them for free; (b) operator UX (CLI / approval app) does not change for commanders; (c) FR-024 (no regression in existing public API/audit/telemetry contracts) is trivially satisfied because the envelope IS the existing contract; (d) MAF checkpoints save pending requests as part of checkpoint state per the docs, so a crash mid-approval is recoverable without losing the pending decision.
- **Alternatives Considered**:
  - **Bespoke MAF-native approval store** — duplicates spec 008 work, breaks Q4 clarification, fails FR-024.
  - **Direct Workflow.send_response invocation from a synchronous HTTP endpoint** — bypasses the commander queue and the AIIMS escalation timer; violates FR-009 and Constitution NN-1.
- **Recorded as ADR-033-03.**

---

## R6 — MCP transport: `MCPStreamableHTTPTool` for the routing service

- **Decision**: Use `agent_framework.MCPStreamableHTTPTool` (HTTP-Streamable MCP transport) to bind the routing service to agents. The routing service runs as a long-lived Azure Container App that exposes an MCP server endpoint internally.
- **Rationale**: MAF supports three MCP transports: `MCPStdio` (per-process spawn), `MCPStreamableHTTPTool` (HTTP), `MCPWebsocketTool` (WebSocket). The routing service is already a long-lived container with stable HTTP endpoints; spawning it per agent invocation (`stdio`) would defeat the point of having a separately-deployable service. Websockets add LB/ingress complexity in Azure Container Apps without delivering anything HTTP-Streamable doesn't already give us. HTTP-Streamable also matches our existing managed-identity-bound HTTP auth pattern between container apps. The MCP server advertises its semver via the protocol's `serverInfo` block, which the agent's allow-list validates per FR-019a.
- **Alternatives Considered**:
  - **`MCPStdio`** — wrong topology for a containerised long-lived tool.
  - **`MCPWebsocketTool`** — operational complexity with no benefit.
  - **`HostedMCPTool`** (Azure-hosted MAF managed MCP) — currently in preview and adds a managed dependency we don't need; revisit when GA.
- **Recorded as ADR-033-04.**

---

## R7 — Telemetry: call `setup_observability(...)` once at runtime startup

- **Decision**: At agent runtime startup (`apps/agents/maf_runtime/observability.py`) call MAF's `setup_observability(...)` to register OpenTelemetry tracing/metrics/logging hooks; route them through the existing `azure-monitor-opentelemetry` exporter (already initialised with `ManagedIdentityCredential` in `apps/agents/monitoring/agent.py:15-25`). Add custom span attributes (run_id, agent_name, model_tier, token_usage) via a small `otel_middleware.py` MAF middleware.
- **Rationale**: MAF is OpenTelemetry-first; calling `setup_observability` populates spans/metrics/logs automatically for every ChatAgent invocation and Workflow step. Routing through the **existing** Azure Monitor exporter means: (a) every existing operator dashboard and KQL alert continues to work without a parallel telemetry stack (FR-017, SC-009); (b) Application Insights is already authenticated via managed identity in AU-region; no new auth or region work; (c) the run_id custom attribute satisfies the FR-016 trace-id linkage to the parent workflow run.
- **Alternatives Considered**:
  - **Roll our own OTel instrumentation per agent** — what we have today; explicit anti-goal of this feature (SC-005).
  - **Stand up a parallel OTel collector** — violates Out-of-Scope ("Re-platforming the audit store or the telemetry backend").

---

## R8 — Audit immutability mechanism

- **Decision**: Store audit entries in the existing Cosmos `audit_entries` container (`australiaeast`); enforce immutability via (a) a Cosmos role assignment that grants the agent runtime managed identity only `Cosmos DB Built-in Data Contributor` minus `Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/delete` actions (custom role), and (b) an Azure Policy initiative that denies any role assignment that would re-grant delete on the `audit_entries` container. 7-year online retention is a property of NOT setting a TTL on the container (no auto-purge); the deny-delete policy prevents manual purge.
- **Rationale**: Meets FR-014 (immutable) and FR-012a (7-year online) without introducing a new product (Azure Confidential Ledger, Append-Blob, etc.) — Out-of-Scope explicitly forbids re-platforming the audit store. Cosmos role-based action filtering is a documented capability and integrates with existing managed-identity authentication. The Azure Policy deny is enforced at deploy-time by the OPA/conftest gate from spec 029.
- **Alternatives Considered**:
  - **Azure Confidential Ledger** — strongest immutability guarantee, but new product, new region, and a separate query surface from the rest of platform audit.
  - **Append-only Blob with time-based immutability** — works but mismatched with the existing query patterns operators use against `audit_entries` (Cosmos KQL-like queries through the platform API).
  - **Application-side immutability only** — relies on application correctness, not an enforced control; weaker than role-based action denial.

---

## R9 — Equivalence harness shape (FR-023)

- **Decision**: `apps/agents/maf_runtime/equivalence/runner.py` is a fixture-driven harness. For each migrated agent it loads (a) the existing per-agent test fixtures from `tests/{unit,integration,contract}/fixtures/<agent>/` and (b) the spec-025 (Agent Specification Compliance) audit fixtures, then replays each fixture through both the legacy pipeline and the MAF ChatAgent, scores the outputs with `scorers.py` against the FR-023 rule (≥95% decision-equivalence on enumerated categorical fields + 100% schema-equivalence on populated fields; free-text fields excluded), and emits a per-agent Markdown + JSON report into `apps/agents/maf_runtime/equivalence/reports/<agent>-<timestamp>.{md,json}`. The cutover PR for each agent attaches the latest report as evidence; CI gate refuses to merge a cutover PR whose report does not pass the FR-023 thresholds.
- **Rationale**: Pinning the input corpus to existing fixtures (a) avoids inventing test data of unknown coverage, (b) directly leverages spec 025's already-curated representative fixtures, (c) makes the gate auditable per FR-023, and (d) keeps the harness deterministic on the legacy side (no extra LLM calls) while accepting LLM non-determinism on the MAF side via the threshold rather than via byte-equality.
- **Alternatives Considered**:
  - **Human spot-check only** — non-objective; cannot block CI.
  - **Byte-equality** — rejected by Q5 clarification (LLM non-determinism makes this brittle).
  - **Synthetic fuzz inputs** — would require curation effort that the existing fixture corpora already paid.

---

## R10 — Per-agent feature-flag cutover mechanism

- **Decision**: Each of the five agents has a per-environment env-var feature flag `FEATURE_MAF_RUNTIME_<AGENT>` (values: `legacy` | `maf` | `shadow`). The workflow runtime reads the flag at step-dispatch time inside each custom Executor: `legacy` → invoke the existing pipeline function; `maf` → invoke the MAF ChatAgent; `shadow` → invoke the MAF ChatAgent in the background, return the legacy output, and feed both into the equivalence harness for live monitoring (does not affect production output). Flags are managed through the spec 029 progressive-delivery flag mechanism and per-environment Bicep parameters.
- **Rationale**: Satisfies FR-022 (incremental, mixed-state migration), FR-026 (per-agent revert during the migration window), and gives us a low-risk live-shadow phase before each cutover. Reusing spec 029's mechanism avoids inventing a parallel flag system.
- **Alternatives Considered**:
  - **Big-bang cutover for all five agents** — explicitly rejected by FR-022.
  - **Branch deployments per agent** — operationally heavier; spec 029 progressive delivery already provides per-environment flag flips with audit.
  - **In-app DB-backed flags** — adds a runtime read-path dependency and a new audit surface; env-var via spec 029 is simpler and already audited.

---

## Open items deliberately left to implementation

These are not NEEDS CLARIFICATION — they are design refinements that surface naturally during implementation and have a documented default:

- **Exact retry budget per Executor** (FR-012). Default: 3 attempts with exponential backoff, total elapsed cap 30 s per step. Refine per agent during integration tests.
- **Exact OTel span attribute names**. Default to MAF conventions (`ai.agent.name`, `ai.agent.model`, `ai.tokens.input`, `ai.tokens.output`) plus our `workflow.run_id`, `workflow.step` extensions; reconcile with existing dashboards during cutover.
- **Operator dashboard layout for the 7-state filter**. Defer to UX iteration during the cutover of the first agent (Monitoring); design proposal lives in `apps/web/src/components/workflow/WorkflowRunList.tsx`.
- **Tool allow-list change governance** (Outstanding from clarification round 2). Default: PR-based change to `tool_registrations` seed file under spec-029 CODEOWNERS; revisit when a second tool is added.
