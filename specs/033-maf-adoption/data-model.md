# Phase 1 Data Model — MAF Adoption

**Feature**: 033-maf-adoption  
**Date**: 2026-04-30  
**Source**: derived from `spec.md` Key Entities + Functional Requirements + clarifications

This document defines the persistent and in-memory entities introduced by this feature, their fields, relationships, validation rules, and (where applicable) state transitions. Storage decisions (which Cosmos container, partition key, TTL) are recorded in `plan.md → Storage`.

---

## 1. Agent Definition

**Purpose**: Declarative description of one of the five named agents. Read at runtime startup; not mutated at runtime.

**Storage**: Version-controlled YAML files in the repo at `apps/agents/maf_runtime/agents/<agent>.yaml` (loaded by the corresponding Python module). Not persisted in Cosmos — code-as-source-of-truth.

**Fields**:

| Field | Type | Notes |
|---|---|---|
| `name` | string (enum) | One of `monitoring`, `risk_assessment`, `evacuation`, `resource_allocation`, `communication`. |
| `display_name` | string | Operator-visible label. |
| `prompt` | string | The system/instruction prompt for the ChatAgent. |
| `model_tier` | string (enum) | `reasoning` or `drafting` — selects the Azure OpenAI deployment per existing `LLMClientConfig`. |
| `output_schema` | reference | Pydantic model class path, e.g. `domain.models.MonitoringTriageDecision`. |
| `tool_allow_list` | array of `{tool_name, pinned_major_version}` | Per FR-019, FR-019a. |
| `middleware_bindings` | array of strings | Names of agent middleware to apply (default: `[content_safety, audit, otel]`). |

**Validation rules (FR-001, FR-002, FR-003)**:
- `name` MUST be unique across the five definitions.
- `output_schema` reference MUST resolve to a Pydantic v2 BaseModel.
- Each `tool_allow_list` entry's `pinned_major_version` MUST be a non-negative integer.
- `middleware_bindings` MUST contain `content_safety` and `audit` (refusal to omit; FR-013, FR-014, FR-015).

**Relationships**:
- Referenced by every `Workflow Run` (one Agent Definition per agent step in the run).

---

## 2. Workflow Run

**Purpose**: A durable execution instance of the multi-agent flow tied to one incident.

**Storage**: Cosmos DB container `workflow_runs`, partition key `/incident_id`. No TTL.

**Fields**:

| Field | Type | Notes |
|---|---|---|
| `id` | string (UUID v4) | Primary key inside the partition. |
| `run_id` | string | Alias of `id`; used in API paths. |
| `incident_id` | string | Partition key; FK to incident record. |
| `status` | string (enum) | One of the **7 canonical states** (see §2.1). |
| `is_active` | bool | Computed: `status in {Running, AwaitingApproval}`. Indexed. Used by FR-011a uniqueness check. |
| `current_step` | string | Name of the agent step currently executing or paused at. |
| `last_checkpoint_id` | string \| null | FK to `checkpoints.id`. |
| `prior_run_id` | string \| null | FK to a previously terminated run for the same incident; enables FR-011a supersession audit linkage. |
| `pending_request_id` | string \| null | When `status = AwaitingApproval`, the MAF `RequestInfoEvent.request_id` awaiting commander action. |
| `failure_reason` | string \| null | When `status = Failed`, structured reason + last-completed step. |
| `terminal_at` | datetime \| null | Set on first transition to a terminal state; drives the 30-day checkpoint TTL clock (FR-012a). |
| `started_at` | datetime | Set on creation. |
| `last_step_at` | datetime | Updated on every step boundary; drives the FR-012c 72h watchdog. |
| `created_by` | string | The actor that initiated the run (operator, ingestion service, etc.). |
| `tenant_id` | string | Multi-tenant isolation (existing repo convention). |

**Validation rules**:
- **FR-011a (uniqueness)**: A Cosmos transactional batch MUST atomically check that no other document for the same `incident_id` has `is_active = true` before inserting a new run.
- `status` transitions MUST follow §2.1.
- `terminal_at` MUST be set on the same write that flips `status` to a terminal value.
- `prior_run_id` MUST be set on creation iff a prior run for the same incident exists in any terminal state.

### 2.1 — Workflow Run state model (FR-011b)

```
                     ┌────────────────────────────┐
                     │           Running          │
                     │   (executing agent step)   │
                     └──────────┬─────────────────┘
                                │
        ┌───────────────────────┼─────────────────────────────┬────────────────────────┐
        │                       │                             │                        │
        ▼                       ▼                             ▼                        ▼
┌────────────────┐   ┌──────────────────────┐     ┌────────────────────────┐   ┌──────────────┐
│ AwaitingApproval│  │ NeedsOperatorDecision│     │     Completed          │   │  Cancelled   │
│ (HITL pause —   │  │ (cannot make progress │     │ (terminal — success)  │   │ (terminal —  │
│  Communication  │  │  without operator —   │     └────────────────────────┘   │  operator    │
│  agent)         │  │  schema mismatch /    │                                  │  initiated)  │
└──────────┬──────┘  │  retries exhausted /  │                                  └──────────────┘
           │         │  72h cap)             │
           │         └──────────┬────────────┘
           │                    │
           ▼                    ▼
┌──────────────────┐   ┌────────────────────────┐
│  Running         │   │       Failed           │
│  (resumed by    │    │ (terminal — failed-   │
│  commander      │    │  with-context after   │
│  decision)      │    │  retries exhausted)   │
└──────────────────┘   └────────────────────────┘

Plus terminal state:
┌──────────────┐
│  Superseded  │   ← set on the prior run when a new run for the same incident_id starts
└──────────────┘
   (only entered from Running, AwaitingApproval, or NeedsOperatorDecision when an
    operator explicitly closes the prior run as part of starting a new one)
```

**Allowed transitions** (enforced by `apps/agents/maf_runtime/workflow/run_state.py`):

| From | To | Trigger |
|---|---|---|
| _(none)_ | Running | Run created |
| Running | AwaitingApproval | Communication agent step emits HITL `RequestInfoEvent` |
| Running | NeedsOperatorDecision | Schema mismatch, retries exhausted with ambiguous outcome, or 72h watchdog (FR-012c) |
| Running | Completed | Final agent step succeeds |
| Running | Failed | Retries exhausted with deterministic failure |
| Running | Cancelled | Operator initiates cancel |
| AwaitingApproval | Running | Commander approves or modifies (decision recorded by spec 008) |
| AwaitingApproval | Cancelled | Commander rejects, OR operator initiates cancel |
| AwaitingApproval | NeedsOperatorDecision | 72h watchdog (FR-012c) |
| NeedsOperatorDecision | Running | Operator resolves (e.g., bumps schema, retries) |
| NeedsOperatorDecision | Cancelled | Operator initiates cancel |
| NeedsOperatorDecision | Failed | Operator declines to resolve and closes the run as failed |
| Running, AwaitingApproval, NeedsOperatorDecision | Superseded | Operator explicitly starts a new run for the same incident |
| Completed, Failed, Cancelled, Superseded | _(none)_ | Terminal |

Any other transition MUST be rejected by the repository write path with a typed `InvalidStateTransitionError` and audited.

---

## 3. Checkpoint

**Purpose**: A persisted snapshot of MAF Workflow state taken at agent-step boundaries, sufficient to resume execution after a process restart.

**Storage**: Cosmos DB container `checkpoints`, partition key `/run_id`. Container TTL = 2,592,000 s (30 days). The TTL clock starts only after the parent run reaches a terminal state, implemented by a small retention helper that re-stamps the document's `_ts`-equivalent control field on terminal transition.

**Fields**:

| Field | Type | Notes |
|---|---|---|
| `id` | string (UUID v4) | Primary key inside the partition. |
| `run_id` | string | Partition key; FK to `workflow_runs.id`. |
| `sequence` | int | Monotonically increasing per run; starts at 0. |
| `step_name` | string | The agent step boundary at which the checkpoint was taken. |
| `executor_states` | object | `{<executor_id>: <serialised state>}` — the dict returned by each executor's `on_checkpoint_save`. |
| `pending_requests` | array | MAF-emitted pending `RequestInfoEvent` records (per MAF docs, captured automatically). |
| `taken_at` | datetime | |

**Validation rules (FR-006, FR-007)**:
- `sequence` MUST be unique per `run_id` (Cosmos transactional batch).
- A checkpoint MAY only be taken at agent-step boundaries, not mid-step.
- On restore, the workflow runtime MUST re-emit pending `RequestInfoEvent`s rather than auto-resolving them (per MAF docs and spec edge case "mid-workflow crash during a paused HITL step").

---

## 4. Approval Decision

**Purpose**: A recorded human action against a pending public-alert step. **This entity already exists in spec 008's `approval_decisions` Cosmos container; this feature does NOT introduce a new entity.** Documented here for completeness.

**Storage**: Existing Cosmos container `approval_decisions` (spec 008). No schema change.

**Fields used by this feature**:

| Field | Notes |
|---|---|
| `request_id` | The wrapped MAF `RequestInfoEvent.request_id`. |
| `approver_identity` | Whatever spec 008 records (carried through unchanged per FR-009 + Q4 clarification). |
| `decision` | `approve` / `modify` / `reject`. |
| `modifications` | Free-form (existing schema). |
| `decided_at` | datetime. |

**Integration**:
- This feature reads `approval_decisions` only as a side effect of spec 008's existing handler calling `Workflow.send_response(request_id, decision)`.

---

## 5. Audit Entry

**Purpose**: An immutable record of one agent invocation, captured by the centralised middleware.

**Storage**: Existing Cosmos container `audit_entries`. No TTL (7-year online retention enforced by deny-delete policy per R8). Partition key `/incident_id` (existing convention).

**Fields**:

| Field | Type | Notes |
|---|---|---|
| `id` | string (UUID v4) | |
| `incident_id` | string | Partition key. |
| `run_id` | string | FK to `workflow_runs.id`. |
| `agent_name` | string | One of the five canonical names. |
| `step_name` | string | |
| `model_tier` | string | E.g., `reasoning`, `drafting`. |
| `input_fingerprint` | string | SHA-256 hex of canonicalised input JSON. **Not the raw input** (NN-3). |
| `output_fingerprint` | string \| null | SHA-256 hex of canonicalised output JSON, when produced. |
| `correlation_id` | string | The OTel trace_id (FR-016 linkage). |
| `started_at` | datetime | |
| `ended_at` | datetime | |
| `outcome` | string (enum) | `success` \| `failed` \| `blocked_by_content_safety` \| `tool_failure` \| `version_mismatch` (FR-019a). |
| `failure_reason` | string \| null | When `outcome != success`. |
| `tool_invocations` | array of `{tool_name, version, outcome, latency_ms}` | When the agent step called MCP tools (FR-020). |

**Validation rules (FR-014, FR-015)**:
- Audit entry MUST be written by the centralised middleware, NOT by agent code (test gate: a "no-op" agent that does nothing still produces an audit entry — SC-004).
- Fingerprints MUST be SHA-256 hex of canonicalised JSON (sorted keys, no whitespace) so that re-running the same input produces a comparable fingerprint regardless of map iteration order.
- The container's effective immutability (deny-delete role + Azure Policy) MUST be in place before any cutover (covered by Phase 0 R8).

---

## 6. Tool Registration

**Purpose**: Binds an out-of-process MCP tool to one or more agents' allow-lists.

**Storage**: Cosmos DB container `tool_registrations`, partition key `/tool_name`. No TTL.

**Fields**:

| Field | Type | Notes |
|---|---|---|
| `id` | string | Composite: `<tool_name>:v<major>`. |
| `tool_name` | string | Partition key. |
| `address` | string | URL of the MCP server (HTTP-Streamable; FR-018 + ADR-033-04). |
| `pinned_major_version` | int | Per FR-019a. |
| `bound_agents` | array of strings | Subset of the five canonical agent names. |
| `capability_description` | string | Human-readable summary. |
| `registered_at` | datetime | |
| `registered_by` | string | Operator identity. |

**Validation rules (FR-019, FR-019a)**:
- The agent runtime MUST refuse to invoke a tool whose advertised major version (per the MCP `serverInfo` block) does not match the registered `pinned_major_version`; this MUST surface as `outcome = version_mismatch` in the audit entry and emit an operator-visible alert.
- A new major version is a NEW registration document with a NEW composite id, NOT an in-place update; this preserves the audit trail per FR-014.

---

## 7. Telemetry Span

**Purpose**: An OpenTelemetry span emitted for each agent step or tool invocation.

**Storage**: Application Insights (`appi-ama-{env}`) — emitted via the existing `azure-monitor-opentelemetry` exporter; not persisted in Cosmos.

**Span attributes**:

| Attribute | Notes |
|---|---|
| `ai.agent.name` | MAF convention. |
| `ai.agent.model` | MAF convention; populated to the Azure OpenAI deployment name. |
| `ai.tokens.input` / `ai.tokens.output` | MAF convention. |
| `workflow.run_id` | Custom — links span to `workflow_runs.id` (FR-016 linkage). |
| `workflow.step` | Custom — `step_name`. |
| `workflow.parent_trace_id` | Custom — top-level run trace id, so a child span can roll up. |
| `tool.name` / `tool.version` | When the span covers an MCP tool invocation (FR-020). |

**Validation rules (FR-016, FR-017, SC-004)**:
- Every agent invocation MUST produce at least one span (covered by `otel_middleware.py`).
- Daily reconciliation job MUST compare invocation count, audit-entry count, and span count and assert zero gap.
- Existing dashboards MUST continue to render without per-agent gaps after each cutover (verified manually as part of the per-agent cutover gate).

---

## Entity Relationships

```
Incident (existing)
   │
   │ 1
   ▼
WorkflowRun ─────────► (prior_run_id) ────► WorkflowRun (terminal)
   │ 1                                          (Superseded)
   │
   │ N
   ▼
Checkpoint
   │
   │ N (pending_requests)
   ▼
ApprovalRequest envelope (spec 008)
   │
   │ 1
   ▼
ApprovalDecision (spec 008)

WorkflowRun ────► AgentDefinition (one per step, by name)
   │
   │ 1..N
   ▼
AuditEntry ────► TelemetrySpan (correlation_id == trace_id)
   │
   │ 0..N
   ▼
ToolInvocation ────► ToolRegistration (by tool_name + pinned_major_version)
```
