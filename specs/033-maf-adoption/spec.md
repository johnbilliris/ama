# Feature Specification: Microsoft Agent Framework (MAF) Adoption

**Feature Branch**: `033-maf-adoption`  
**Created**: 2026-04-30  
**Status**: Draft  
**Input**: Adopt Microsoft Agent Framework (MAF) across the AMA agent stack — (1) all five named agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication) become MAF ChatAgents; (2) the existing handoff graph between them becomes a MAF Workflow with checkpointing for crash recovery and HITL for the Communication Agent's approval gate (R8); (3) shared cross-cutting concerns become MAF middleware for content safety and audit logging, with MAF telemetry wired into the existing OpenTelemetry pipeline; (4) tools that live in separate processes (e.g., a routing service) are integrated via the Model Context Protocol (MCP).

## Clarifications

### Session 2026-04-30

- Q: Per incident, how many workflow runs can exist concurrently? → A: One active run per incident at a time; a closed/cancelled run can be superseded by a new run on incident re-escalation; all runs preserved for audit.
- Q: Which canonical operator-visible states must every workflow run be classifiable into? → A: 7-state model — Running, AwaitingApproval, NeedsOperatorDecision, Completed, Failed, Cancelled, Superseded.
- Q: How long must checkpoints and audit entries be retained online? → A: Checkpoints 30 days; audit entries 7 years online (different policies per artifact).
- Q: What is the authoritative source of approver identity and authorization for the new HITL gate? → A: Inherit spec 008 unchanged — the new HITL gate calls into the existing approval store/queue and records whatever identity that workflow already captures; no new identity model is introduced by this feature.
- Q: What is the canonical functional-equivalence rule for cutting a migrated agent over to the new abstraction? → A: ≥95% decision-equivalence on categorical fields plus 100% schema-equivalence on populated fields, evaluated against the agent's representative test corpus; free-text fields excluded from comparison.
- Q: What concurrent active workflow capacity must the platform support? → A: 25 concurrent active workflow runs sustained, 50 burst, without degrading SC-002 recovery rates or SC-007 latency-regression bar.
- Q: What is the contract-evolution policy for out-of-process (MCP) tools? → A: Semantic versioning; agent allow-list pins major version per tool; tool servers MUST stay backward-compatible within a major (additive only); a major bump is a separate allow-list entry that must be deliberately enabled per agent.
- Q: What is the default maximum elapsed duration of a single active workflow run before automatic transition to NeedsOperatorDecision? → A: 72 hours (default), configurable per environment.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Five Named Agents Built on a Common Agent Abstraction (Priority: P1)

As a platform engineer maintaining AMA's multi-agent system, I need each of the five named operational agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication) to share a single, well-defined agent abstraction with consistent inputs, outputs, lifecycle, and observability hooks, so that adding capabilities, changing prompts, and swapping LLM providers no longer requires bespoke per-agent plumbing and so that downstream orchestration can treat every agent uniformly.

**Why this priority**: Today each agent has bespoke pipeline, telemetry, retry, and LLM-invocation code. Without a shared agent abstraction, every later capability (workflow orchestration, middleware, HITL, MCP tools) must be added five times. This story is the foundation that makes Stories 2–4 economically feasible and unblocks all subsequent simplification.

**Independent Test**: For each of the five agents, submit a representative input through the new agent surface (not the legacy pipeline) and verify that (a) the structured output matches the legacy pipeline's output for the same input per the equivalence rule in FR-023, (b) the agent records the same audit trail as before, and (c) the agent can be invoked in isolation by a smoke test without spinning up the rest of the system.

**Acceptance Scenarios**:

1. **Given** a representative signal envelope, **When** it is submitted to the Monitoring agent through the new agent surface, **Then** the agent returns a triage decision (escalate / suppress / enrich) that matches the legacy pipeline output for the same input per the equivalence rule defined in FR-023.
2. **Given** the same input is submitted twice in succession, **When** processed by any of the five agents, **Then** the agent produces results that are functionally equivalent per FR-023 (free-text fields may differ; categorical decisions and populated schema fields must match) and emits audit events that are structurally identical.
3. **Given** an LLM provider outage, **When** any of the five agents is invoked, **Then** the agent surfaces a single, consistent failure mode (typed error + correlation id + audit entry) regardless of which agent was called.
4. **Given** a platform engineer needs to change a prompt or model tier for one agent, **When** they edit the agent's configuration, **Then** the change is contained to that agent's definition and requires no changes to retry, telemetry, or audit code.

---

### User Story 2 — Reliable Multi-Agent Workflow with Crash Recovery and Human-in-the-Loop Approval (Priority: P1)

As an emergency operations coordinator running an active incident, I need the chain of agent activity (signal → triage → risk → evacuation/resource → public alert) to behave as a single, durable workflow that survives process restarts and that always pauses for an authorised human to approve any public alert before publication, so that an in-flight incident is never lost to a transient fault and no public communication is ever issued without commander sign-off.

**Why this priority**: The existing point-to-point handoff graph has no shared run-state, no checkpointing, and only an ad-hoc approval queue. A single process restart mid-incident can lose context, and the absence of a first-class HITL pause is a direct compliance risk for life-safety communications (R8). Both gaps are P1 because they directly threaten incident continuity and public-safety governance.

**Independent Test**: Start an incident workflow, kill the orchestrating process partway through (after risk assessment, before public alert), restart it, and verify the workflow resumes from the last checkpoint without re-running completed steps and without losing any signal context. Separately, verify that no public alert is ever emitted without an explicit, recorded human approval action.

**Acceptance Scenarios**:

1. **Given** an incident workflow is running and has completed risk assessment, **When** the orchestrating process is forcibly terminated and restarted, **Then** the workflow resumes from the last checkpoint, does not re-execute the completed risk assessment step, and produces the same downstream outputs as if no crash had occurred.
2. **Given** the workflow reaches the Communication agent's draft-alert step, **When** the draft is produced, **Then** the workflow pauses, records a "pending approval" state, notifies the configured commander chain, and emits no public communication until an authorised approval action is recorded.
3. **Given** an alert is in "pending approval", **When** an authorised commander approves, modifies, or rejects the alert, **Then** the workflow resumes with the recorded decision, the decision (including approver identity, timestamp, and any modifications) is permanently auditable, and approval-pending time is measured.
4. **Given** an alert sits in "pending approval" beyond the configured timeout, **When** the timeout expires, **Then** the workflow escalates to the next commander in the chain (up to the configured maximum) and never auto-approves.
5. **Given** any node in the workflow fails transiently, **When** the workflow's resumption logic engages, **Then** retries occur within bounded attempts and elapsed time, failures beyond the bound move the run to a failed-with-context state rather than silently dropping it, and the operator can see exactly which step failed and why.

---

### User Story 3 — Cross-Cutting Safety, Audit, and Telemetry Without Per-Agent Boilerplate (Priority: P2)

As a risk and compliance owner for AMA, I need content safety screening and append-only audit logging to apply uniformly to every agent invocation, and I need every agent step to emit telemetry into the existing OpenTelemetry pipeline (traces, metrics, logs to Application Insights) without each agent re-implementing those concerns, so that audit completeness, safety enforcement, and operational visibility are guaranteed by construction rather than by reviewer diligence.

**Why this priority**: Compliance and observability are currently per-agent responsibilities, which means a new agent (or an edited one) can silently bypass content safety or stop emitting audit events. Centralising these as cross-cutting concerns eliminates a class of governance defects. Priority is P2 because Stories 1 and 2 must land first to provide the integration points.

**Independent Test**: Add a synthetic "no-op" agent to the system that performs no safety, audit, or telemetry work of its own. Run any input through it. Verify that (a) content safety still ran and recorded a verdict, (b) an audit entry is present in the audit store with the same shape as for the five real agents, and (c) traces, metrics, and logs for that invocation appear in Application Insights with the expected correlation ids — purely because the cross-cutting layer is applied centrally.

**Acceptance Scenarios**:

1. **Given** any agent invocation regardless of which agent, **When** the invocation completes (success or failure), **Then** an immutable audit entry exists containing input fingerprint, output fingerprint, agent identity, model/tier identifier, correlation id, timestamps, and outcome.
2. **Given** an input that triggers content safety rejection, **When** any agent attempts to process it, **Then** the request is blocked at the cross-cutting layer with a categorised rejection reason, the rejection is audited, and the agent's own logic is not invoked.
3. **Given** the content safety service is unavailable, **When** an agent is invoked, **Then** the cross-cutting layer applies the documented degraded-mode behaviour (per existing circuit-breaker contract) consistently across all agents.
4. **Given** any agent step executes, **When** the step starts and completes, **Then** the OpenTelemetry pipeline receives a span with the agent name, step name, model identifier, token usage where applicable, latency, and a trace id that links to the parent workflow run.
5. **Given** an operator opens the existing Application Insights dashboards, **When** they filter by agent or by workflow run, **Then** they see complete traces and metrics for every agent step in that run with no per-agent gaps.

---

### User Story 4 — Out-of-Process Tools Integrated via a Standard Protocol (Priority: P3)

As an agent developer, I need agents to call tools that live in separate processes (such as the routing service) through a single, standard protocol rather than through bespoke HTTP clients per tool, so that adding, replacing, or sandboxing a tool does not require changes inside the agents and so that tools can be developed, deployed, and versioned independently of the agent runtime.

**Why this priority**: Out-of-process tool integration today is ad-hoc per service, which couples agent code to each tool's transport, auth, and error model. Moving to a standard protocol removes that coupling and lets new tools be added without modifying agent code. This is P3 because it improves extensibility but does not block incident-handling correctness or compliance.

**Independent Test**: Stand up a tool server (e.g., the routing service) behind the standard protocol, register it with one agent, and verify that the agent can discover the tool, invoke it, receive a typed result, and surface tool-side errors — all without any tool-specific client code inside the agent.

**Acceptance Scenarios**:

1. **Given** a tool server is reachable and registered, **When** an agent invokes the tool, **Then** the agent receives a structured result and the call is captured in the same telemetry and audit trail as the rest of the agent's work.
2. **Given** a tool server is unreachable, **When** an agent attempts to invoke it, **Then** the agent receives a typed error within a bounded timeout, the failure is audited, and the agent's own retry/fallback policy is applied uniformly with other tool failures.
3. **Given** a new tool is added or an existing tool changes its inputs/outputs, **When** the change is deployed to the tool server only, **Then** the agent picks up the new capability through protocol-level discovery without code changes inside the agent runtime, subject to the agent's configured allow-list.

---

### Edge Cases

- **Mid-workflow crash during a paused HITL step**: workflow resumes in the same paused state; no auto-approval; pending-approval timer is reconciled rather than reset.
- **Two commanders approve the same alert simultaneously**: workflow accepts the first decision, surfaces a documented conflict to the second, and audits both attempts.
- **Checkpoint store is unavailable when a workflow tries to persist**: the workflow halts the affected run with a typed error rather than proceeding without durability; operator is alerted.
- **Telemetry pipeline (Application Insights) is unavailable**: agent execution proceeds; telemetry is buffered or dropped per the existing OpenTelemetry exporter policy; agent correctness is unaffected.
- **A registered MCP tool starts returning malformed responses**: invocations fail closed with a typed error; the agent does not fabricate a result; the failure is audited.
- **Content safety rejection at the middleware layer for an alert that is already in "pending approval"**: the alert is moved to a rejected state with reason and the commander is notified.
- **A long-running incident workflow exceeds the configured maximum run duration (default 72 hours, per FR-012c)**: the run is moved to a "needs operator decision" state rather than being silently abandoned.
- **An agent's output schema changes**: the workflow detects the schema mismatch at the orchestration boundary and fails the step with a clear contract-violation error rather than passing malformed data downstream.

## Requirements *(mandatory)*

### Functional Requirements

**Agent abstraction (US1)**

- **FR-001**: System MUST expose each of the five named operational agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication) through a single shared agent abstraction with a uniform invocation interface, lifecycle, and error contract.
- **FR-002**: Each agent's behaviour MUST be defined by configuration (prompt, model tier, tool allow-list, output schema) such that a behaviour change for one agent does not require code changes in another.
- **FR-003**: The agent abstraction MUST produce typed, schema-validated outputs; downstream consumers MUST be able to reject malformed outputs at the abstraction boundary.
- **FR-004**: The agent abstraction MUST surface a single, consistent typed error model (including correlation id) for LLM, tool, validation, and policy failures.
- **FR-005**: Each agent MUST be invocable in isolation (without the workflow runtime) for unit-level smoke tests.

**Workflow orchestration, checkpointing, HITL (US2)**

- **FR-006**: System MUST orchestrate the multi-agent flow as a single durable workflow whose state is checkpointed at agent-step boundaries.
- **FR-007**: A workflow run interrupted by a process restart MUST resume from the most recent checkpoint without re-executing completed agent steps and without losing in-flight signal context.
- **FR-008**: The Communication agent's public-alert step MUST always pause the workflow for human approval and MUST NOT publish a public communication without a recorded human approval decision.
- **FR-009**: The HITL approval surface MUST capture approver identity, decision (approve / modify / reject), timestamp, and any modifications, and MUST persist these as part of the workflow's audit trail. The HITL gate MUST delegate **identity, authorization, and approval-chain semantics to the existing Communication-agent approval workflow defined by spec 008** rather than introducing a parallel identity model; this feature integrates with that workflow's existing approval store/queue and surfaces whatever approver identity it already records.
- **FR-010**: A pending approval that exceeds the configured timeout MUST escalate to the next commander in the configured chain, up to the configured maximum, and MUST never auto-approve.
- **FR-011**: Workflow runs MUST be addressable, listable, and inspectable by operators (current step, last checkpoint, failure reason where applicable).
- **FR-011a**: System MUST enforce **at most one active workflow run per incident** at any time; any attempt to start a second concurrent active run for the same incident MUST be rejected. A new run for the same incident MAY only be started after the prior run has reached a terminal state (`Completed`, `Failed`, `Cancelled`, or `Superseded`), and MUST link to the prior run's identifier for audit continuity.
- **FR-011b**: Every workflow run MUST be classifiable at any time into exactly one of seven canonical states: **Running** (executing an agent step), **AwaitingApproval** (HITL-paused at the Communication agent's public-alert step, healthy), **NeedsOperatorDecision** (cannot make progress without explicit operator input — e.g., schema mismatch, exhausted retries with ambiguous outcome, run-duration cap exceeded), **Completed** (terminal — successful end-to-end), **Failed** (terminal — failed-with-context after retries exhausted), **Cancelled** (terminal — operator-initiated stop), **Superseded** (terminal — closed because a new run for the same incident has started). State transitions MUST be append-only and auditable. Operator dashboards MUST be able to filter and group runs by these states.
- **FR-012**: Transient agent or tool failures within a workflow MUST be retried within bounded attempts and bounded elapsed time; exhausted retries MUST move the run to a failed-with-context state rather than dropping it. **Default bounds**: at most 3 attempts and at most 30 seconds total elapsed per agent step (per-environment overrides permitted; specific tunings recorded in `research.md` and validated by tests in `tests/unit/`).
- **FR-012a**: **Checkpoints** MUST be retained online for at least **30 days** after the owning workflow run reaches a terminal state, then MAY be deleted. **Audit entries** (per FR-014) MUST be retained online and queryable for at least **7 years** from creation; they MUST NOT be deleted within that window. Retention policies for the two artifact types are independent and MUST be enforced automatically rather than by manual cleanup.
- **FR-012b**: System MUST sustain **at least 25 concurrent active workflow runs** at steady state and **at least 50 concurrent active workflow runs** at burst (defined as a 60-minute window) without violating SC-002 (≥99/100 successful resumes after fault injection) or SC-007 (≤10% end-to-end latency regression versus legacy). Capacity targets MUST be validated by an automated load test that is part of the per-environment cutover gate.
- **FR-012c**: A single active workflow run that has been in a non-terminal state (`Running` or `AwaitingApproval`) continuously for longer than **72 hours** (default; configurable per environment) MUST be automatically transitioned to **NeedsOperatorDecision** and surfaced to operators with the elapsed duration and last-completed step. The system MUST NOT silently abandon, auto-cancel, or auto-complete a run that exceeds this duration.

**Cross-cutting middleware and telemetry (US3)**

- **FR-013**: Content safety screening MUST be applied to every agent invocation through a centralised mechanism such that bypass requires a deliberate, documented exception rather than agent-side omission.
- **FR-014**: Every agent invocation (success or failure) MUST produce an immutable audit entry containing input fingerprint, output fingerprint, agent identity, model/tier identifier, correlation id, timestamps, and outcome.
- **FR-015**: Audit and content-safety behaviour MUST be uniform across all agents; a new or modified agent MUST inherit both without per-agent implementation work.
- **FR-016**: Every agent step MUST emit traces, metrics, and logs into the existing OpenTelemetry pipeline (Application Insights), tagged with agent name, step name, model identifier, token usage **for every LLM-backed step (omitted for tool-only or middleware-only spans)**, latency, and a trace id linking to the parent workflow run.
- **FR-017**: Existing operator dashboards MUST continue to function; no per-agent telemetry gaps may exist for any of the five named agents after migration.

**Out-of-process tools (US4)**

- **FR-018**: Tools that run in separate processes MUST be exposed to agents through a single standard protocol; agents MUST NOT contain bespoke per-tool transport or auth code.
- **FR-019**: Each agent MUST have a configurable allow-list of tools it may invoke; the system MUST refuse calls to tools outside the allow-list.
- **FR-019a**: Out-of-process tool servers MUST publish a **semantic version** for their interface. Each entry in an agent's allow-list (FR-019) MUST pin a specific **major version** for the bound tool. Tool servers MUST remain **backward-compatible within a major version** (additive changes only — no field renames, no removed capabilities, no narrowed types, no breaking semantic changes); a breaking change MUST be released as a major-version bump, which constitutes a separate allow-list entry that an agent's configuration MUST opt into deliberately. The system MUST refuse to invoke a tool whose advertised major version does not match the allow-list entry, MUST surface this as a typed version-mismatch error, and MUST emit an operator-visible alert.
- **FR-020**: Tool invocations MUST appear in the same audit trail and telemetry pipeline as agent steps, including correlation id linkage.
- **FR-021**: A tool's failure (unreachable, timeout, malformed response) MUST surface as a typed error to the calling agent within a bounded timeout and MUST NOT cause the agent to fabricate a result.

**Migration, compatibility, governance**

- **FR-022**: Migration MUST be incremental — each of the five agents MUST be cuttable over to the new abstraction independently, with the workflow orchestration able to mix migrated and not-yet-migrated agents during the transition.
- **FR-023**: For every migrated agent, the system MUST provide a documented equivalence test demonstrating that the new agent produces functionally equivalent outputs to the legacy pipeline for a representative input set. **Functional equivalence** is defined as: (a) **≥95% decision-equivalence on categorical output fields** (e.g., escalate/suppress/enrich, hazard severity bucket, evacuation stage, alert approval-required flag) — i.e., the new agent must produce the same categorical decision as the legacy pipeline on at least 95% of corpus inputs; and (b) **100% schema-equivalence** — every output must be schema-valid and contain the same set of populated fields as the legacy output for the same input. **Free-text fields** (rationales, summaries, narrative explanations) are explicitly excluded from the equivalence comparison. The representative input set MUST be drawn from the existing unit, integration, and contract test fixtures plus the spec-025 (Agent Specification Compliance) audit fixtures. Per-agent cutover is gated on passing this test.
- **FR-024**: The migration MUST NOT regress any existing public API contract, audit field, or telemetry field already consumed by external dashboards or downstream services. Compliance MUST be verified by an automated **field-level snapshot test** that compares the pre-MAF and post-MAF field sets of (a) every operator-facing REST response, (b) every `audit_entries` document, and (c) every OTel span attribute referenced by an existing dashboard query; any removed or renamed field fails the test.
- **FR-024a**: The Communication agent's prompt and output schema MUST NOT change as part of this migration. Specifically, the prompt string loaded from `communication.yaml` MUST be byte-equal to the legacy prompt constant in `apps/agents/communication/agent.py`, and the populated output-field set MUST be unchanged. This invariant exists because Constitution V (Warnings) compliance for the Australian Warning System tiers and the ten warning principles is encoded in the existing prompt; behavioural drift would silently weaken life-safety communications.
- **FR-025**: Authentication to all platform services (LLM, telemetry, audit store, checkpoint store, tool servers) MUST continue to use managed identity; introduction of API-key authentication is forbidden.
- **FR-026**: Operators MUST be able to disable the new workflow runtime and revert to the legacy pipeline per agent during the migration window.

### Key Entities *(include if feature involves data)*

- **Agent Definition**: The declarative description of one of the five named agents — its name, prompt(s), model tier, output schema, tool allow-list, and middleware bindings.
- **Workflow Run**: A durable execution instance of the multi-agent flow tied to an incident, with current step, checkpoint history, pending-approval state, and final outcome. **At most one active run per incident at a time**; a closed or cancelled run may be superseded by a new run (e.g., on incident re-escalation), with the prior run retained for audit and linked to its successor. Every run is classifiable at any time into exactly one of seven canonical states: **Running**, **AwaitingApproval**, **NeedsOperatorDecision**, **Completed**, **Failed**, **Cancelled**, or **Superseded** (the last four are terminal).
- **Checkpoint**: A persisted snapshot of workflow state taken at agent-step boundaries, sufficient to resume execution after a process restart.
- **Approval Decision**: A recorded human action against a pending public-alert step — approver identity, decision (approve / modify / reject), timestamp, and any modifications.
- **Audit Entry**: An immutable record of one agent invocation, captured by the centralised middleware and including input/output fingerprints, identities, model/tier, correlation id, timestamps, and outcome.
- **Tool Registration**: A record that binds an out-of-process tool to one or more agents' allow-lists, including the tool's address, capability description, and **pinned major semantic version per FR-019a**.
- **Telemetry Span**: An OpenTelemetry span emitted for each agent step or tool invocation, carrying agent name, step name, model identifier, token usage where applicable, latency, and trace correlation back to the parent workflow run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the five named operational agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication) are running on the shared agent abstraction at end-of-feature; legacy per-agent pipeline code paths are removed or behind a documented fallback flag.
- **SC-002**: After a forced restart of the workflow runtime mid-incident, the affected workflow run resumes and completes successfully without re-executing already-completed agent steps in at least 99 of 100 fault-injection trials.
- **SC-003**: 0 public alerts are ever emitted by the system without a recorded human approval decision (measured continuously in production and during all test runs); any such occurrence is treated as a P1 defect.
- **SC-004**: 100% of agent invocations produce an audit entry and a corresponding telemetry trace; an automated daily reconciliation between invocation counts and audit/telemetry counts shows zero gap.
- **SC-005**: Mean time to add a new cross-cutting policy (e.g., a new content-safety category, a new audit field) drops to a single change applied centrally rather than five per-agent changes — verified by a worked example during the feature.
- **SC-006**: At least one out-of-process tool (the routing service) is consumed by at least one agent through the standard protocol with no tool-specific client code inside the agent runtime.
- **SC-007**: End-to-end incident workflow latency (signal received → public alert ready for approval) does not regress versus the legacy pipeline by more than 10% on a representative benchmark **at the FR-012b sustained capacity target (25 concurrent active runs)**; any regression beyond 10% blocks the cutover.
- **SC-008**: Approval-gate metrics (mean time-to-approval, escalation rate, timeout rate) become first-class operator dashboards available on day one of cutover; an operator viewing the workflows dashboard sees the `AwaitingApproval` state for a paused run within **10 seconds** of `RequestInfoEvent` emission.
- **SC-009**: Every existing operator dashboard continues to render with no field-level gaps for the five named agents after each agent's cutover.
- **SC-010**: Onboarding a sixth named agent (proof-of-concept) requires only an Agent Definition, prompt, and tool allow-list — no new middleware, telemetry, audit, or workflow-runtime code — demonstrated by a worked example.

## Assumptions

- The existing managed-identity authentication model for Azure OpenAI, Cosmos DB, Service Bus, and Application Insights remains in force; no API-key fallback will be introduced.
- Cosmos DB is the system's existing durable store and is the natural home for workflow checkpoints and audit entries (final placement is a planning decision, but durability and auditability are required).
- The existing AIIMS-aligned commander approval chain (per spec 008-communication-agent) defines who may approve **and how their identity is established**; this feature carries those rules forward by integrating with spec 008's existing approval store/queue rather than introducing a parallel identity or authorization model.
- The existing OpenTelemetry pipeline to Application Insights is the target for all new agent and workflow telemetry; introducing a parallel telemetry stack is out of scope.
- Migration proceeds agent-by-agent under a feature flag; the workflow runtime can orchestrate a mix of migrated and not-yet-migrated agents during the transition window.
- Functional equivalence between legacy and migrated agents is measured **per FR-023** against a representative test corpus drawn from existing unit/integration/contract tests and the spec-025 audit fixtures.
- The "routing service" is taken as the first out-of-process tool because it is the most complete separately-deployable tool today; additional tools may follow but are not required for this feature's success criteria.

## Out of Scope

- Adding new agent capabilities (new prompts, new output fields, new decisions). This feature changes the runtime, abstraction, and orchestration; it does not change what each agent decides.
- Replacing the LLM provider or changing model tiers. The migration must accept current model selections.
- Changes to the AIIMS approval chain semantics (who may approve, escalation levels, timeout values) beyond surfacing them through the new HITL gate.
- Re-platforming the audit store or the telemetry backend.
- A user-facing workflow designer or low-code authoring surface for agents.
- Migration of incident-management, planning, or any non-named agent code paths — they may consume the new abstractions later but are not part of this feature.

## Dependencies

- **Spec 008 — Communication Agent**: defines the AIIMS approval chain and timeout/escalation rules that the HITL gate must honour.
- **Spec 025 — Agent Specification Compliance**: provides the equivalence-test fixtures used to verify migrated agents match legacy behaviour.
- **Spec 029 — Progressive Delivery Pipeline**: provides the feature-flag and per-environment rollout mechanism used for incremental agent cutover.
- **Existing OpenTelemetry → Application Insights pipeline**: target for all new telemetry; must be reachable from the new workflow runtime.
- **Existing managed-identity (Entra ID) configuration** for Azure OpenAI, Cosmos DB, Service Bus, and Application Insights.
- **Existing Cosmos DB account** is assumed available as the durable store for new workflow checkpoints and audit entries (final placement determined in planning).
