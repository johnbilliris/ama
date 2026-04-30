# ADR-033-02: Cosmos DB Backs the MAF Workflow `CheckpointStorage` (via SDK-Provided `agent_framework_azure_cosmos.CosmosCheckpointStorage`)

## Status

Accepted

## Context

Feature `033-maf-adoption` requires the multi-agent workflow runtime to **checkpoint at every agent-step boundary** (FR-006) and to **resume from the most recent checkpoint after a process restart with no re-execution** (FR-007 / SC-002 ≥99/100 fault-injection trials). It further requires that checkpoints be retained online for at least 30 days after the parent workflow run reaches a terminal state, and then automatically deleted (FR-012a).

The MAF Python SDK exposes:

- **`agent_framework.CheckpointStorage`** (abstract base)
- **`agent_framework.FileCheckpointStorage`** (reference implementation; not durable across process / container restarts)
- **`agent_framework.InMemoryCheckpointStorage`** (volatile)
- **`agent_framework_azure_cosmos.CosmosCheckpointStorage`** (sub-package of the official MAF SDK; first-class managed-identity support via `endpoint=...` + `credential=DefaultAzureCredential()`)

Earlier research (research.md §R4) called for a **custom `CosmosCheckpointStorage` subclass**, written in this repository. That decision was made before probing the SDK's actual capabilities; the SDK now ships the exact storage we need.

Constitution NN-2 (Data sovereignty) forbids storing platform data outside the Australian Azure regions; Cosmos placement is constrained to `australiaeast` (with `australiasoutheast` as a paired-region fallback).

## Decision

We adopt the **SDK-provided `agent_framework_azure_cosmos.CosmosCheckpointStorage`** as the workflow checkpoint backend. The repository wraps it in a thin factory that:

1. Constructs `CosmosCheckpointStorage(endpoint=<env_cosmos_endpoint>, database_name="platform", container_name="checkpoints", credential=DefaultAzureCredential())`.
2. Creates the `checkpoints` container via Bicep (`infra/bicep/modules/cosmos-workflow.bicep` — T008) with `partitionKey=/run_id` and `defaultTtl=2592000` (30 days). The TTL clock is gated by a small retention helper (`apps/agents/maf_runtime/checkpoint/retention.py` — T019) that re-stamps documents on terminal-state transition, so non-terminal runs are never auto-deleted while still active.
3. Wraps Cosmos client exceptions into the canonical `CheckpointStoreUnavailableError` (from `apps/agents/maf_runtime/errors.py` — T011b) so the workflow runtime can halt the affected run with a typed error rather than proceeding without durability (per spec edge case "Checkpoint store is unavailable").
4. Adds the `audit_entries` container (existing) to the deny-delete OPA policy (T010) so its 7-year online retention is enforced at deploy-time.

`agent_framework.FileCheckpointStorage` is **not** used in any environment — it does not survive a container restart and would defeat the SC-002 fault-injection guarantee.

## Consequences

- ✅ **No custom subclass code to maintain**. Behaviour, schema versioning, and bug fixes track the SDK's release cadence.
- ✅ **Single regulated store**: the new `checkpoints` container lives in the same `australiaeast` Cosmos account as `audit_entries` and `approval_decisions`, inheriting the existing managed-identity, RBAC, networking, and backup posture.
- ✅ **Schema evolution risk is borne by the SDK**, not by us. If MAF changes its checkpoint serialisation format, we adopt the SDK upgrade and its compatibility shims; no in-repo migration needed.
- ⚠️ **SDK version tracking**: a breaking change to the `CosmosCheckpointStorage` constructor or behaviour would require coordinated upgrade. Mitigation: the SDK is pinned (`agent-framework-azure-cosmos>=1.0.0b260429`); upgrades are PR-gated and run through the existing equivalence + load-test gates.
- ⚠️ **Container-TTL nuance**: the SDK writes documents with no TTL by default. The retention.py helper (T019) is the **only** path that sets `_ttl=2592000` on each checkpoint document for a run, and it runs exactly once when the parent workflow run reaches a terminal state. Non-terminal runs therefore never lose checkpoints to TTL; in-progress runs of >30 days (the 72h watchdog will normally have already moved them to `NeedsOperatorDecision` per FR-012c) remain durably checkpointed.
- ✅ **Constitution NN-2 preserved**: container is provisioned in `australiaeast` only.

## References

- `agent_framework_azure_cosmos.CosmosCheckpointStorage` constructor — supports `endpoint` + `credential` (managed-identity-compatible) and `cosmos_client` / `container_client` injection for testing.
- Spec 033 §FR-006, §FR-007, §FR-012a, §SC-002.
- Constitution v1.2.0 §Non-Negotiable #2.
- Edge case in spec 033: "Checkpoint store is unavailable when a workflow tries to persist".

## Related

- ADR-033-01 (`OpenAIChatClient` backing — client-side state captured by checkpoint).
- T008 (Bicep `cosmos-workflow.bicep`).
- T010 (OPA `deny_audit_delete.rego` — separate, applies to `audit_entries`).
- T018 (factory + error wrapping).
- T019 (terminal-state TTL stamp).
