# Spec 036 F-A4 — Amend-Loop Coupling Constraint

**Status**: Active (Phase F merge train).
**FR**: FR-RAG-CV-01 (extended).
**Source**: Pass 2 Q-P2-03; Plan §F-A4.2 + §Updated phase ordering.
**Owner**: amend-loop merge captain (rotating; current: johnbilliris).

## Constraint

Any pull request that mutates **`infra/policy/rego/foundry_carveout.rego`**
(the OPA carve-out gate) MUST also mutate either:

1. `specs/036-foundry-rag-grounding/tasks.md` (Phase F entries T151–T251), or
2. another file in the Phase F implementation set (any of the F-A1..F-A12
   directories below).

Symmetrically, any PR mutating Phase F tasks/files MUST also mutate the rego
within the same merge train. Bifurcating the rego patch from the Phase F
implementation creates a window where the production OPA gate would refuse
existing 2-approver prod rows without the matching schema migration in place.

The CI guard at `.github/workflows/amend-loop-coupling.yml` enforces this
constraint at PR-check time.

## Rationale

The R3 architecture finding F-ARCH-05 (BLOCKER) identified the rego at
line 29 as enforcing `< 2` for every row, irrespective of `environment`.
FR-RAG-CV-01 requires 3 approvers for production deployments.

Closing the gap means:

- **Patching the rego**: introduce an `input.environment` discriminator
  (`prod` → `< 3`, `dev`/`staging` → `< 2`). See T152.
- **Patching the registry schema** (`foundry-carveout.schema.json`): add the
  `min_approvers_prod` / `min_approvers_dev` registry-root keys and the
  per-row `environment` enum. See T153.
- **Patching the spec contract mirror**: see T154 (already mirrored at
  `specs/036-foundry-rag-grounding/contracts/foundry-cv.schema.json`).

These three changes MUST land together. If only the rego is patched, the
existing 2-approver prod rows in `infra/parameters/foundry-carveout.yaml`
break. If only the schema is patched, the gate still passes a 2-approver
prod row. If only the spec contract is patched, the runtime gate is unchanged.

## Phase F coupling

The F-A4 cluster (T151–T155) is the FIRST sub-phase in Phase F. Per the plan,
all subsequent F-A5..F-A12 work piggybacks on the same merge train. The
coupling constraint guarantees that the rego fix lands in the same PR as the
broader amend-loop work, eliminating the bifurcated rollout window.

## Phase F implementation set (informational)

Files / directories that count as Phase F mutations for the CI guard:

- `specs/036-foundry-rag-grounding/tasks.md`
- `specs/036-foundry-rag-grounding/checklists/`
- `infra/policy/rego/foundry_carveout.rego`
- `infra/policy/rego/cultural_authority_flag.rego`
- `infra/parameters/foundry-carveout.schema.json`
- `infra/modules/cosmos-cultural-authority.bicep`
- `infra/modules/cosmos-conflict-detection.bicep`
- `infra/scripts/migrate-audit-record-036.ps1`
- `apps/agents/common/cultural_authority_registry.py`
- `apps/agents/common/retrieval_service.py`
- `apps/api/app/services/approval_workflow.py`
- `apps/api/app/services/conflict_detection.py`
- `apps/api/app/services/index_rollback.py`
- `packages/domain/src/ama_domain/audit_record.py`
- `packages/schemas/spec_036/`
- `tests/contract/test_foundry_carveout.py`
- `tests/integration/test_*` (any F-A* test added)
- `docs/decisions/036-foundry-rag-grounding/12-` ... `19-*.md`
- `docs/runbooks/036-foundry-rag-*.md`
- `docs/compliance/ISM-2024-mapping.md`

The CI guard's regex check (see workflow) covers the canonical paths; the
`tasks.md` mutation is the broadest catch-all for novel files.

## Override (emergency)

Emergency rollback PRs that revert ONLY the rego change MAY include a single
trailer in the PR body:

```text
amend-loop-coupling-override: "<release-manager-handle>: <one-line reason>"
```

The CI guard recognises this trailer and waives the coupling check. The
override is recorded in `docs/runbooks/036-foundry-rag-blue-green-rollback.md`
for post-incident review (see T172).
