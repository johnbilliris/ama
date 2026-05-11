# Spec-037 quickstart rehearsal results

**Status**: `deferred-to-step-9`

The spec-037 implementation orchestrator has explicitly deferred the
end-to-end quickstart rehearsal (`specs/037-capstone-evidence-pack/quickstart.md`
workflows 1–4) to **Step 9 (`azd up` redeploy)**. This file is the canonical
record of that deferral per T067 acceptance.

## What runs in Step 9

The four quickstart workflows are:

1. **Add a new risk row** (Workflow 1) — verified end-to-end against the live
   `evidence-pack-publication-gate` job by raising a small docs-only PR.
2. **Publish an artefact** (Workflow 2) — verified against the deployed
   `ca-api-ama` Container App and the new
   `evidence_pack_artefact_cache` Cosmos child container after `azd up` lands
   the spec-037 Bicep delta.
3. **Obtain auditor sign-off** (Workflow 3) — verified by intentionally
   exceeding the cap on a fixture artefact and recording the sign-off block.
4. **Verify the executive page** (Workflow 4) — verified by browsing
   `/governance/executive` on the deployed App Service.

## Why deferred

The first three workflows require:

- a live `evidence_pack_artefact_cache` Cosmos container (lands via `azd up`)
- a live `evidence-pack-archive` Blob container with immutability policy
  (lands via `azd up`)
- the `evidence-pack-publication-gate` CI job to be running on `main` after
  the spec-037 PR merges (gate is added by T046 in the same PR)

Workflow 4 additionally requires the new `/governance/executive` route to be
deployed to the `app-ama-zo6bb5` App Service — also covered by `azd up`.

## Local pre-flight (PASS — recorded 2026-05-11)

The following local pre-flight checks PASSED on the spec-037 implementation
branch (commit shipped in this PR):

- `python -m evidence_pack_gate` → `PASS — 5 artefact(s)`
- `pytest --basetemp=C:\tmp\pytest037 tests/contract/spec_037/` → 20 passed
- `pytest --basetemp=C:\tmp\pytest037 apps/api/tests/contract/spec_037/` → 4 passed
- `pytest --basetemp=C:\tmp\pytest037 tests/integration/spec_037/` → 2 passed

Citations: T067, FR-035, FR-038, SC-011.
