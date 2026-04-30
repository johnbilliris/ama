# Phase 0 — Research: Simplify CI/CD with Branch-Based Deployment

This document resolves every open question raised by the spec, the clarification session, and the Technical Context section of `plan.md`. There are no remaining `NEEDS CLARIFICATION` markers in the plan; this file documents the *evidence* behind each decision so reviewers and Phase 1 (data-model + contracts) can rely on it.

## R1 — `workflow_run` event: branch context, head_sha checkout

**Decision**: `cd.yml` is triggered by `workflow_run` on `ci` completion, filtered to branches `dev`, `staging`, `production`. Inside `cd.yml`, jobs explicitly check out `github.event.workflow_run.head_sha` (NOT the default branch) and read `github.event.workflow_run.head_branch` to select the target environment.

**Rationale**: GitHub runs `workflow_run` workflows in the *default-branch* context by default — the `actions/checkout@v5` action without an explicit `ref` will check out `main`, not the commit that just passed CI. This is a well-known footgun that causes "we deployed an old commit" incidents. Explicitly passing `ref: ${{ github.event.workflow_run.head_sha }}` to checkout pins the deploy to the exact commit `ci` validated. We also gate the entire `cd` workflow on `github.event.workflow_run.event == 'push'` so that PR-driven CI runs (which run against the merge ref, not a target branch) do NOT cascade into a deployment.

**Alternatives considered**:
- **Inline deploy job in `ci.yml`** (rejected during clarification — Q3, Option B): would simplify branch context but lengthen every PR's runtime and mix gating with deployment in one file.
- **`repository_dispatch` from CI to CD**: equivalent end-state to `workflow_run` but adds a custom payload contract and a mandatory `secrets.GITHUB_TOKEN` for the dispatch call — more code for no behaviour gain.
- **`push`-trigger `cd.yml` directly with a status-API check**: would race against `ci` and require polling; rejected.

**References**:
- GitHub Actions docs — *Events that trigger workflows → workflow_run*: <https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_run>
- The current `cd.yml` already uses this pattern for `main` only — we generalise the `branches:` filter and the `head_branch` routing.

## R2 — `AZURE_CREDENTIALS` JSON shape & `azure/login@v3` consumption

**Decision**: Each GitHub Environment (`dev`, `staging`, `production`) holds a single secret named `AZURE_CREDENTIALS` containing the JSON object documented in the spec input (clientId, clientSecret, subscriptionId, tenantId, plus the Azure cloud-endpoint URLs). The action call is:

```yaml
- uses: azure/login@v3
  with:
    creds: ${{ secrets.AZURE_CREDENTIALS }}
```

**Rationale**: `azure/login` accepts the `creds:` input as the authoritative way to pass a service-principal JSON; this path does NOT require `permissions: id-token: write` on the job. The JSON shape we're given is the canonical output of `az ad sp create-for-rbac --sdk-auth` and is the format `azure/login` documented for non-OIDC use. Splitting the values back into individual `client-id` / `tenant-id` / `subscription-id` inputs (as the current `cd.yml` does) would defeat the "one secret per environment" goal.

**Alternatives considered**:
- **Per-key secrets (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, ...)** — current state; rejected because the spec explicitly mandates a single JSON secret (FR-007 / FR-008).
- **OIDC federated credential** — explicitly out of scope per the decision register (ADR-031).
- **Storing the JSON in `vars.*` instead of `secrets.*`** — rejected: `clientSecret` is a credential and MUST be a secret.

**References**:
- `azure/login` action README — `creds:` input — <https://github.com/Azure/login>
- Azure CLI `az ad sp create-for-rbac --sdk-auth` output schema (matches the JSON in the spec input).

## R3 — `dev` Bicep parameter file: naming and SKU choices

**Decision**: Create `infra/main.parameters.dev.json` (matches the new branch name `dev`). Delete `infra/main.parameters.development.json` after confirming no script references it. Set:

| Parameter | dev value | rationale |
|---|---|---|
| `environmentName` | `drh-dev` | matches `azd env new drh-dev` and resource group `rg-drh-dev` |
| `location` | `australiaeast` | Constitution NN-2 (data sovereignty) |
| `principalType` | `ServicePrincipal` | `cd.yml` runs as the SPN from `AZURE_CREDENTIALS` |
| `developerIpAddress` | `""` | no developer-ip allow-list for dev |
| `actionGroupEmail` | `dev-ops@example.com` | placeholder; operator overrides post-deploy |
| `actionGroupWebhook` | `""` | no webhook in dev |
| `openAiDeploymentSku` | `GlobalStandard` | same as staging (cheapest available SKU that satisfies the agents' model needs; do NOT downgrade further or model calls will 429 in dev) |
| `restrictNetworkAccess` | `false` | dev is open by design |

**Rationale**: The existing `main.parameters.staging.json` is the closest functional analogue. Re-using its values *except for the env name* keeps the parameter surface consistent and avoids "dev was special so the bug only repros in staging" issues. Cost discipline for dev comes from container-app/app-service `min_replicas: 0` (already in `main.bicep` for non-prod) rather than from changing the OpenAI SKU, because cost there is per-call not per-deployment. The current `main.parameters.development.json` uses `${AZURE_ENV_NAME}` substitution, which is an `azd`-style template; it is not consumed by the simplified `cd.yml` (which uses literal-value `.json` parameter files like staging/production), so deleting it removes confusion.

**Alternatives considered**:
- **Reuse `main.parameters.development.json`** — rejected: branch is `dev`, not `development`; mismatched names mislead.
- **Lower-tier OpenAI SKU for dev** — rejected: would create dev-only failure modes.
- **Skip the Bicep parameter file and rely on `azd env set` CLI calls** — rejected: parameter files are version-controlled and reviewable; CLI `env set` calls hide deployment intent inside the workflow.

## R4 — `cd.yml` rollback scoping: dev vs staging/prod

**Decision**: The rollback step (`scripts/rollback.sh`) and the "create critical-failure issue" step run only when the resolved target environment is `staging` or `production`. For `dev`, both steps are skipped via an `if:` condition; a failed dev deploy surfaces only as a normal job failure.

**Rationale**: Per the spec clarification (Q4, Option B). Implementation: add `if: failure() && steps.health-check.outcome == 'failure' && env.TARGET_ENV != 'dev'` to the rollback step, and `if: failure() && steps.rollback.outcome == 'failure' && env.TARGET_ENV != 'dev'` to the critical-issue step. The TARGET_ENV is set at the top of the deploy job from `github.event.workflow_run.head_branch`.

**Alternatives considered**:
- **Per-environment branching jobs** (separate `deploy-dev` / `deploy-staging` / `deploy-production` jobs, each with its own rollback config) — rejected: triples the file size for marginal clarity gain; the matrix-of-one + `if:` is idiomatic GHA.
- **Deleting `scripts/rollback.sh` entirely** — rejected: staging/prod still need it.

## R5 — `drift-detection.yml` matrix: staging + production only

**Decision**: Change `strategy.matrix.environment: [staging, production]`. The schedule (`cron: "0 16 * * 6"`, Saturday 16:00 UTC = Sunday 02:00 AEST) is preserved. The `workflow_dispatch` trigger remains; we do NOT add a `choice` input restricting environments because the matrix already constrains scope and a dispatch-time override would invite accidental dev runs.

**Rationale**: Per the spec clarification implicit in FR-011. The current matrix is `[staging, production]` already (no change to that line in the existing file) — but the workflow's `azure/login@v2` block must be migrated from split secrets to `creds: ${{ secrets.AZURE_CREDENTIALS }}` (still inside the `environment: ${{ matrix.environment }}` matrix entry), and the `permissions: id-token: write` line dropped.

**Alternatives considered**:
- **Drift detection for `dev`** — rejected: `dev` is allowed to deviate; would produce noise.
- **Run drift detection on every push** — rejected: `azd what-if` is expensive (~5–15 minutes per env).

## R6 — Spec-029 footprint deletion: precise scope

**Decision**: The deletion list is the union of (a) the items the user named in the clarification answer and (b) the transitively orphaned files I confirmed via `grep` to have *no other consumers*:

| Path | Why deleted | Consumer (now gone) |
|---|---|---|
| `.github/workflows/spec029-ci.yml` | Named by user | — |
| `.github/workflows/spec029-cd.yml` | Named by user | — |
| `.github/workflows/spec029-drift-detection.yml` | Named by user | — |
| `.github/workflows/_reusable/pr-gates.yml` | Named by user | spec029-ci.yml |
| `.github/workflows/_reusable/canary-stage.yml` | Named by user | spec029-cd.yml |
| `.github/workflows/change-freeze.yml` | Named by user | — (manual workflow) |
| `.github/workflows/posture-exception-sweep.yml` | Named by user | scheduled |
| `.github/workflows/evidence-pack.yml` | Named by user | manual |
| `.github/workflows/dev-key-issue.yml` | Named by user | manual |
| `.github/workflows/emergency-hotfix.yml` | Named by user | manual |
| `.github/actions/install-opa/` | Transitively orphaned | `_reusable/pr-gates.yml` only |
| `.github/actions/setup-cosign-syft/` | Transitively orphaned | `spec029-ci.yml` only |
| `.github/actions/setup-oidc-azure/` | Transitively orphaned | `_reusable/pr-gates.yml`, `_reusable/canary-stage.yml` |
| `.github/state/freeze.json` | Managed by deleted change-freeze workflow | change-freeze.yml |
| `tools/pipeline/` (whole package) | Named by user | All deleted workflows `pip install -e ./tools/pipeline` |
| `infra/IDENTITY.md` | Topology trust-root for deleted setup-oidc-azure | setup-oidc-azure, identity_consistency.rego |
| `infra/policy/posture-matrix.yaml` | Posture sweep input | posture-exception-sweep.yml, posture-verifier |
| `infra/policy/posture-exceptions.yaml` | Posture sweep input | posture-exception-sweep.yml |
| `infra/policy/foundry-carveout.yaml` | Carve-out enforcement input (NN-2 carve-out) | posture-verifier (deleted) |
| `infra/policy/rego/` (whole dir) | OPA policy bundle | install-opa + posture-verifier |
| `scripts/spec029-bootstrap/` | One-off operator scripts for spec-029 SP/Entra setup | manual |

**Out of scope (NOT deleted by this change)**:
- `infra/bicep/modules/posture-policy-set.bicep` — declarative Azure Policy module that *may* be useful independently. Flagged for FR-020 review.
- `tests/pipeline/` — pytest fixtures for the deleted Rego/IDENTITY validation. Flagged for FR-020 review (dead tests).

**Rationale**: The user's instruction was to "delete the entire spec-029 footprint". The named workflow files plus their *only* consumers (composite actions, Rego policies, Python tooling) form a connected component in the dependency graph. Leaving any of them alive would mean dead code that confuses future maintainers and triggers `actionlint`/CI noise. The two items in "Out of scope" are *not* uniquely owned by spec-029 (the Bicep module could be reused; the pytest fixtures are test code that needs separate triage), so I am explicitly not deleting them in this change to avoid scope creep.

## R7 — Constitution Check regression: Foundry carve-out enforcement

**Decision**: Removing `infra/policy/foundry-carveout.yaml` and the posture-verifier removes the *automated* enforcement of Constitution NN-2's carve-out (which permits Foundry model-hosting endpoints in non-AU regions only when on a named, version-controlled list). The constitutional requirement itself is unchanged; the *control* downgrades from "automated CI gate" to "manual review at PR time".

**Mitigation** (not part of this PR, but tracked in the new ADR):
- The ADR (`adr-031`) lists carve-out enforcement re-introduction as a follow-up item with the same review trigger as the OIDC migration.
- Until then, any PR that introduces a Foundry model-hosting region MUST be reviewed by the security/compliance personas per Constitution NN-2 last paragraph (operator-driven, not pipeline-driven).
- This regression is surfaced as one of the three FR-020 recommendations to the maintainer (so they can accept/reject re-introduction explicitly).

**Alternatives considered**:
- **Keep `foundry-carveout.yaml` + a minimal evaluator workflow** — rejected: re-introduces the spec-029 surface area we are explicitly removing, and the evaluator would need its own SP/auth plumbing.
- **Move carve-out enforcement into `cd.yml`** — rejected: out of scope for the simplification PR; future work tracked by the ADR.

## R8 — Branch creation & protection (operator action, not in this PR)

**Decision**: This PR does NOT create the `dev`, `staging`, `production` branches or set their protection rules — that is an operator action documented in `quickstart.md`. The PR's CI changes only become *active* once the branches exist and are pushed to.

**Rationale**: GitHub branch creation requires repo-admin permissions and protection rules are a per-repo policy choice. The spec scopes branch protection to "out of scope" (Spec → Out of Scope, last bullet). However, the operator runbook (`quickstart.md`) calls out the recommended protections (require PR + 1 reviewer + status-check `ci`) so a careful operator does not enable a free-for-all on `production`.

**Alternatives considered**:
- **Auto-create branches via a one-off workflow** — rejected: requires elevated PAT, adds a single-use artefact to the repo.

## R9 — Concurrency, queueing, and same-environment serialisation

**Decision**: The deploy job in `cd.yml` declares:

```yaml
concurrency:
  group: deploy-${{ github.event.workflow_run.head_branch }}
  cancel-in-progress: false
```

This guarantees that two pushes landing on the same environment branch in quick succession will queue (not race), and that pushes to *different* environment branches can run in parallel.

**Rationale**: Spec FR-005. `cancel-in-progress: false` is the defensive choice — cancelling an in-flight `azd provision` mid-deploy can leave Azure resources in an inconsistent state.

**Alternatives considered**:
- `cancel-in-progress: true` — rejected; risk of partial provisioning.
- Single global lock (`group: deploy`) — rejected; serialises across environments unnecessarily.

## R10 — Secret rotation cadence (deferred to ADR)

**Decision**: The ADR (`adr-031`) documents a 90-day manual rotation cadence for `AZURE_CREDENTIALS.clientSecret` per environment, with the rotation procedure recorded in `quickstart.md` ("Rotating AZURE_CREDENTIALS"). No automated rotation is built in this PR.

**Rationale**: Manual rotation is the MVP-acceptable trade-off documented in the spec assumptions. The 90-day cadence aligns with common SP-secret expiry defaults; longer would weaken security posture.

**Alternatives considered**:
- **Key Vault-backed secret with rotation runbook** — rejected for MVP scope; deferred to the OIDC migration that supersedes this approach entirely.

---

## Summary table

| # | Topic | Decision | Status |
|---|---|---|---|
| R1 | `workflow_run` event handling | Two workflows; `head_branch` routes; explicit `head_sha` checkout | Resolved |
| R2 | `AZURE_CREDENTIALS` shape | Single JSON secret per env; `azure/login@v3 with: creds:` | Resolved |
| R3 | `dev` Bicep parameter file | Create `main.parameters.dev.json`; delete `.development.json` | Resolved |
| R4 | Rollback scoping | Staging/prod only; dev fails loudly | Resolved |
| R5 | Drift detection scope | `[staging, production]` matrix; preserve cron | Resolved |
| R6 | Spec-029 deletion list | Named items + transitively orphaned (table above) | Resolved |
| R7 | Carve-out automation regression | Documented in ADR + FR-020 recommendation | Resolved (with known trade-off) |
| R8 | Branch creation | Operator action via `quickstart.md`; not in PR | Resolved |
| R9 | Concurrency model | Per-env queue, no cancel-in-progress | Resolved |
| R10 | Secret rotation | 90-day manual cadence in ADR + quickstart | Resolved |

**No `NEEDS CLARIFICATION` markers remain.** Phase 1 (data-model, contracts, quickstart) can proceed.
