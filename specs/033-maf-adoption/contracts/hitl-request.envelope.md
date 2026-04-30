# HITL Request Envelope (MAF ↔ spec 008 wrapping contract)

**Purpose**: Define exactly how a MAF `RequestInfoEvent` emitted by the Communication agent's HITL `RequestPort` is wrapped into the existing spec 008 `ApprovalRequest` envelope (Service Bus + Cosmos), and how the commander's decision is routed back into `Workflow.send_response(...)` to resume the run.

**Backs**: FR-008, FR-009 (HITL identity delegated to spec 008), FR-024 (no API regression), Constitution NN-1.  
**Recorded as**: ADR-033-03.

---

## 1. MAF emits

When the Communication agent reaches the public-alert step, the workflow emits:

```python
RequestInfoEvent(
    request_id="<uuid>",
    source_executor_id="communication_executor",
    payload=ToolApprovalRequestContent(  # MAF's built-in HITL payload type
        tool_name="publish_public_alert",
        arguments={
            "alert_text": "...",
            "aws_tier": "Watch and Act",
            "channels": ["sms", "app_push", "broadcast"],
            "target_languages": ["en-AU", "..."],
            ...
        }
    ),
)
```

The workflow runtime serialises this event and pauses; the workflow's persisted state moves to `status = AwaitingApproval` and `pending_request_id = <uuid>` (per `workflow-run.schema.json`).

---

## 2. Wrapping into spec 008's `ApprovalRequest`

`apps/agents/maf_runtime/workflow/hitl_request_port.py` MUST translate the `RequestInfoEvent` into an `ApprovalRequest` Service Bus message exactly as spec 008 already expects. **No spec 008 schema change is permitted** by this feature.

Mapping:

| MAF field | spec 008 `ApprovalRequest` field | Notes |
|---|---|---|
| `request_id` | `request_id` | Reused verbatim. |
| `payload.arguments.alert_text` | `alert.payload.message` | |
| `payload.arguments.aws_tier` | `alert.payload.aws_tier` | |
| `payload.arguments.channels` | `alert.payload.channels` | |
| `payload.arguments.target_languages` | `alert.payload.target_languages` | |
| (workflow context) `incident_id` | `alert.incident_id` | |
| (workflow context) `run_id` | `alert.payload.metadata.maf_run_id` | New metadata key; spec 008 ignores unknown metadata. |
| (workflow context) `correlation_id` | `alert.payload.metadata.correlation_id` | OTel trace id linkage. |
| `source_executor_id` | `alert.payload.metadata.maf_source_executor` | New metadata key. |

The wrapped envelope is published onto the existing Service Bus `commander-approval-queue`. Spec 008's existing escalation timer, AIIMS chain semantics, and dual-control rules apply unchanged.

---

## 3. Commander decision routes back

When the commander acts via the existing approval UI / API (spec 008), spec 008:

1. Records the decision in the existing `approval_decisions` Cosmos container (existing schema; capturing approver identity, decision, modifications, timestamp).
2. Publishes a `ApprovalDecision` message onto the existing `commander-approval-decisions-queue`.

This feature adds a single new subscriber to that decision queue: `apps/agents/maf_runtime/workflow/hitl_request_port.py::on_decision_received`. The handler:

1. Looks up `workflow_runs` by `pending_request_id == decision.request_id`.
2. Calls:

   ```python
   await workflow_runtime.send_response(
       request_id=decision.request_id,
       response=HITLDecisionResponse(
           decision=decision.decision,            # "approve" | "modify" | "reject"
           modifications=decision.modifications,  # if any
           approver_identity=decision.approver_identity,
       ),
   )
   ```

3. Per MAF semantics, `Workflow.send_response(...)` resumes the workflow. The run transitions per the rules in `data-model.md §2.1`:
   - `approve` or `modify` → `Running`, then publishes the (possibly modified) alert.
   - `reject` → `Cancelled` (terminal), no public alert is published.

---

## 4. Crash-safety

Per MAF docs:

> *"When a checkpoint is created, pending requests are also saved as part of the checkpoint state. When you restore from a checkpoint, any pending requests will be re-emitted as `RequestInfoEvent` objects, allowing you to capture and respond to them."*

This means a crash mid-approval is automatically recovered:

1. Process restarts; the workflow's last checkpoint is loaded.
2. The pending `RequestInfoEvent` is re-emitted.
3. `hitl_request_port.py::on_request_emitted` checks the existing `approval_decisions` container for an already-recorded decision matching this `request_id` (idempotency check).
   - If found, immediately calls `send_response(...)` with the recorded decision.
   - If not found, publishes a fresh wrapped `ApprovalRequest` to the queue (deduplicated by `request_id` on spec 008's side) and waits.

This satisfies the spec edge case *"Mid-workflow crash during a paused HITL step: workflow resumes in the same paused state; no auto-approval; pending-approval timer is reconciled rather than reset."*

---

## 5. Constraints (non-bypassable)

- The MAF Workflow MUST NOT call `Workflow.send_response(...)` from any path other than `hitl_request_port.py::on_decision_received`. Test gate: a static check ensures no other module imports `Workflow.send_response`.
- `hitl_request_port.py` MUST NOT have a code path that resolves a request without an `ApprovalDecision` from spec 008. Test gate: a unit test verifies that calling the request-port handler with a synthetic decision that did NOT come from spec 008's queue is rejected.
- The wrapped `ApprovalRequest` MUST set `alert.payload.metadata.maf_run_id` so that spec 008's existing audit trail can be correlated back to the MAF workflow run.

These constraints make NN-1 (Human-in-the-loop) non-bypassable by construction.
