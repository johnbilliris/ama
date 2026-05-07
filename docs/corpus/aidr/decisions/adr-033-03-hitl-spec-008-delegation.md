# ADR-033-03: HITL via Custom `HitlGateExecutor` + Spec-008 Approval Envelope (No `RequestPort`)

## Status

Accepted (revised from research.md §R5 to reflect SDK reality)

## Context

Feature `033-maf-adoption` mandates that the Communication agent's public-alert step **always pauses** for an authorised human approval (FR-008, FR-009, FR-010, FR-024a, Constitution NN-1). Research item R5 originally proposed using MAF's documented HITL pattern: a `RequestPort` emits a `RequestInfoEvent`; the workflow runtime persists the pending request as part of a checkpoint; an external handler eventually calls `Workflow.send_response(request_id, decision)` to resume.

Implementation probing of `agent-framework` Python SDK 1.2.2 revealed:

- The names `RequestPort`, `RequestInfoEvent`, and `Workflow.send_response` are **not present** in the public Python API surface at this version. They appear in the cross-language documentation but the corresponding Python implementation is either preview, C#-only, or not yet shipped in the GA-track 1.2.x release.
- The closest public types are `SubWorkflowRequestMessage` / `SubWorkflowResponseMessage`, which are designed for sub-workflow inter-process messaging, not for HITL pause-and-resume.
- The `Workflow` class supports **checkpoint-and-exit** plus **resume-from-checkpoint** as first-class operations through `WorkflowBuilder` + `CosmosCheckpointStorage`.

Spec 008 (Communication Agent) **already provides**:

- A Service Bus queue `commander-approval-queue` for outbound `ApprovalRequest` messages.
- A Service Bus queue `commander-approval-decisions-queue` for inbound `ApprovalDecision` messages.
- A Cosmos container `approval_decisions` recording approver identity, decision (approve / modify / reject), modifications, and timestamp.
- An AIIMS-aligned escalation timer + dual-control rules.

These pieces give us everything the `RequestPort` pattern would have provided — we just need to glue them together using public MAF APIs.

## Decision

We implement HITL as a **custom `HitlGateExecutor`** placed at the Communication agent's public-alert boundary, paired with a **decision-listener** that resumes the workflow when a commander acts.

### Pause path

1. The Communication-agent step's draft alert is delivered as input to `HitlGateExecutor.run(...)`.
2. `HitlGateExecutor`:
   1. Wraps the draft into spec 008's `ApprovalRequest` envelope (mapping in `contracts/hitl-request.envelope.md`).
   2. Sets `alert.payload.metadata.maf_run_id`, `alert.payload.metadata.maf_source_executor`, and `alert.payload.metadata.correlation_id` so spec 008's existing audit trail can correlate back.
   3. Publishes the envelope to `commander-approval-queue` via the existing `azure-servicebus` client.
   4. Updates the workflow run document: `status = AwaitingApproval`, `pending_request_id = <request_id>`.
   5. Triggers a final checkpoint via the workflow runtime's checkpoint hook and returns a `WorkflowEvent` indicating the run is parked.
3. The workflow runtime's outer loop sees the parked event, persists the final checkpoint, and exits the run process with status `AwaitingApproval`.

### Resume path

1. A Container Apps job (`apps/agents/maf_runtime/workflow/hitl_decision_listener.py`) subscribes to spec 008's `commander-approval-decisions-queue`.
2. On receipt of an `ApprovalDecision` message:
   1. Look up the workflow run by `pending_request_id` (from the run document).
   2. Idempotency check: if the same decision has already been applied (run is no longer in `AwaitingApproval`), acknowledge and exit.
   3. Load the workflow's last checkpoint via `CosmosCheckpointStorage`.
   4. Apply the decision into the workflow context (`approve` / `modify` / `reject` + any modifications + approver identity).
   5. Run the workflow forward from the next step. For `approve` / `modify`: alert is published. For `reject`: workflow transitions to `Cancelled` (terminal), no alert is published.

This pattern is **non-bypassable** by construction:

- `HitlGateExecutor` is the **only** code path that emits a public alert.
- `hitl_decision_listener.py` is the **only** code path that resumes a run from `AwaitingApproval`.
- Both invariants are enforced by the static-analysis test T047.

### Crash safety

If the agents process is killed mid-pause (after the envelope is published but before the run document is checkpointed, or anywhere else in the pause/resume path), the resume path is idempotent:

- On restart, the decision listener compares the `pending_request_id` against `approval_decisions` for an already-recorded decision. If found, it auto-resumes without re-publishing to the commander queue (T048).
- The pause path is also idempotent: re-running `HitlGateExecutor` against the same draft generates the same `request_id` (deterministic from incident_id + workflow_run_id + step_index), so spec 008's commander-queue de-duplication catches double-publishes.

## Consequences

- ✅ **Built on public APIs only**. No reliance on a preview / language-mismatched SDK surface.
- ✅ **Spec 008 unchanged**. Identity, escalation, dual-control, and audit semantics remain authoritative.
- ✅ **FR-024 (no contract regression)** trivially satisfied: the wire envelope is exactly the existing `ApprovalRequest`/`ApprovalDecision`.
- ✅ **Constitution NN-1 (HITL non-bypassable)**: enforced by the single-code-path constraint and verified by T047 static analysis at every PR.
- ⚠️ **Operational complexity**: introduces a second long-lived Container Apps process (`hitl_decision_listener`) co-resident with the agents app. Mitigation: deploy as the same container image with a different startup command; share managed identity; share telemetry; SLO covered by the existing Container Apps health checks.
- ⚠️ **Determinism of `request_id`**: must be generated deterministically (UUIDv5 from `incident_id + run_id + step_index`) so a crash mid-publish doesn't generate a second pending request. Test T046 enforces this.
- ✅ **Forward-compat**: when the Python SDK ships `RequestPort`/`RequestInfoEvent`, we can revisit. The current shape is intentionally close to that future API so the migration would be small.

## References

- Microsoft Learn — *Agent Framework Workflows — Human-in-the-loop (HITL)* (cross-language doc page; the `RequestPort` Python implementation is not yet GA in 1.2.x): <https://learn.microsoft.com/agent-framework/workflows/human-in-the-loop>
- Probing of `agent-framework` 1.2.2 Python public API: no `RequestPort`, `RequestInfoEvent`, or `Workflow.send_response` exists at this version.
- Spec 008 — Communication Agent (existing approval queue + store).
- Spec 033 §FR-008, §FR-009, §FR-010, §FR-024a, §SC-003.
- `contracts/hitl-request.envelope.md` — exact field mapping.
- Constitution v1.2.0 §Non-Negotiable #1.

## Related

- ADR-033-01 (chat client backing — `OpenAIChatClient`).
- ADR-033-02 (Cosmos checkpoint — preserves the pause across process restarts).
- T046 (HitlGateExecutor + decision listener implementation).
- T047 (static-analysis non-bypassability gate).
- T048 (idempotency on resume).
- T056 (audit invariant: no orphan publishes).
