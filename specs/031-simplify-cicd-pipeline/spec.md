# Feature Specification: Simplify CI/CD with Branch-Based Deployment

**Feature Branch**: `031-simplify-cicd-pipeline`  
**Created**: 2026-04-30  
**Status**: Draft  
**Input**: User description: "The CI CD process is too complex. It needs to be simplified. Branch-based deployment (dev/staging/production), CI on push to main/dev/staging/production, CD on success of CI for the matching branch, all GitHub environments hold an `AZURE_CREDENTIALS` JSON object secret, drift detection limited to staging and production, and the spec-029 workflows are to be deleted. A decision-register entry is required to capture the temporary departure from the OIDC/federated-credential model toward a service-principal JSON secret used for MVP."

## Clarifications

### Session 2026-04-30

- Q: Should the spec-029 cleanup be limited to the three named files, or extended to the entire spec-029 progressive-delivery footprint? → A: Delete the entire spec-029 footprint — the 3 named workflows plus `_reusable/pr-gates.yml`, `_reusable/canary-stage.yml`, `change-freeze.yml`, `posture-exception-sweep.yml`, `evidence-pack.yml`, `dev-key-issue.yml`, `emergency-hotfix.yml`, and the now-unreferenced `tools/pipeline` package.
- Q: What Azure footprint does the new `dev` environment get? → A: Dedicated resource group `rg-drh-dev` with the same service composition as staging/production, provisioned from `infra/main.bicep` driven by a dev-specific Bicep parameter file (`infra/main.parameters.dev.json` per the existing `main.parameters.<env>.json` convention) that controls the SKUs (cheaper tiers for dev).
- Q: Which GitHub Actions trigger pattern wires CD to CI? → A: Keep two workflows — `ci.yml` runs on push to `main`/`dev`/`staging`/`production` (and on PRs to `main`); `cd.yml` is triggered by the `workflow_run` event for `ci` completion on the three environment branches and reads `workflow_run.head_branch` to select the target environment. (Generalises the current `cd.yml` pattern from `main`-only to all three environment branches.)
- Q: Does automated rollback on health-check failure apply to `dev`? → A: No — only `staging` and `production` run the rollback script and create a critical-failure issue if rollback itself fails. A failed `dev` deploy leaves the environment in the failed state and surfaces only as a workflow failure (no rollback, no auto-issue).
- Q: How are non-deploy Azure-touching workflows (`eval-pr-gate.yml`, `eval-publish-dataset.yml`) handled? → A: `eval-pr-gate.yml` is migrated to use `AZURE_CREDENTIALS` from the `dev` GitHub environment (PR evals run against dev infra). `eval-publish-dataset.yml` keeps its current structure but its commented-out Azure block is rewritten to use `AZURE_CREDENTIALS` so it is correct when uncommented later. Both workflows remain in the repository.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Predictable branch-based deployment to dev/staging/production (Priority: P1)

As a release engineer (or any committer), I push commits to a single environment branch — `dev`, `staging`, or `production` — and trust that the pipeline will build/validate the code and then deploy it to the matching Azure environment, with no manual workflow_dispatch, no approvals chain across environments inside one workflow, and no service-to-service plumbing required from me.

**Why this priority**: This is the entire point of the simplification. Without branch-based deployment, the pipeline remains opaque and high-friction, blocking every other improvement.

**Independent Test**: Push a trivial commit to the `dev` branch. Verify (a) the `ci` workflow runs against `dev`, (b) the `cd` workflow runs only after `ci` succeeds for the `dev` commit, and (c) the `cd` workflow deploys to the **dev** Azure environment only — staging and production are not touched. Repeat for `staging` and `production`. *Prerequisite for end-to-end runtime verification: User Story 2's operator setup (`AZURE_CREDENTIALS` per environment) must be complete; the User Story 1 workflow modifications are independently reviewable in the YAML files before that.*

**Acceptance Scenarios**:

1. **Given** the `ci` workflow is configured to run on push to `main`, `dev`, `staging`, and `production`, **When** a commit is pushed to `dev`, **Then** `ci` runs on that commit and reports a single pass/fail status for the `dev` branch.
2. **Given** the `cd` workflow is configured to run after `ci` completes successfully on `dev`, `staging`, or `production`, **When** `ci` finishes successfully on a push to `staging`, **Then** `cd` runs and deploys only to the `staging` Azure environment.
3. **Given** `ci` fails on a push to `production`, **When** the workflow run completes, **Then** `cd` does not run and no production deployment is attempted.
4. **Given** a commit is pushed to `main` (or any non-environment branch), **When** `ci` succeeds, **Then** `cd` does **not** trigger an environment deployment from `main`.
5. **Given** `cd` is mid-deployment on `staging`, **When** another push to `staging` finishes `ci`, **Then** the new `cd` run queues behind the in-flight one (concurrency-safe; no parallel deploys to the same environment).

---

### User Story 2 - Single, uniform Azure authentication via `AZURE_CREDENTIALS` JSON secret (Priority: P1)

As an operator wiring a new GitHub environment (or rotating credentials), I configure exactly one secret per GitHub environment — `AZURE_CREDENTIALS`, a single JSON object — and every workflow in the repository authenticates to Azure consistently from that one secret. I do not maintain multiple split secrets/vars (`AZURE_CLIENT_ID` + `AZURE_TENANT_ID` + `AZURE_SUBSCRIPTION_ID`) per workflow.

**Why this priority**: A single, well-defined auth mechanism removes a major source of "works in one workflow, broken in another" pipeline failures and is the prerequisite for the branch-based CD flow to be reliable.

**Independent Test**: Place an `AZURE_CREDENTIALS` JSON object in the `dev` GitHub environment secret store. Push to `dev`. Verify `cd` authenticates to Azure successfully using only that secret and no other Azure credential variables/secrets are referenced in the active workflows.

**Acceptance Scenarios**:

1. **Given** each GitHub environment (`dev`, `staging`, `production`) holds a single `AZURE_CREDENTIALS` secret containing a JSON object with at least `clientId`, `clientSecret`, `subscriptionId`, and `tenantId`, **When** any workflow that needs Azure access runs in the context of that environment, **Then** it authenticates using only `AZURE_CREDENTIALS` and no other Azure-credential secret/variable.
2. **Given** the legacy split secrets/vars (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, OIDC `id-token` exchange) are no longer required by any active workflow, **When** the operator audits the repository's workflow definitions, **Then** no active workflow references those legacy values.
3. **Given** a workflow that previously used OIDC federated credentials, **When** it is rerun under the new model, **Then** it succeeds without an `id-token: write` permission (or the permission is retained only where strictly required by other actions, and that retention is intentional).
4. **Given** the `AZURE_CREDENTIALS` secret is missing or malformed in a GitHub environment, **When** a workflow targeting that environment runs, **Then** the workflow fails with a clear, actionable error pointing the operator at the missing/malformed secret.

---

### User Story 3 - Drift detection scoped to staging and production only (Priority: P2)

As an SRE, I want infrastructure drift checks to run only against environments that are stable and worth protecting — `staging` and `production` — and not waste runner minutes or generate noisy issues against `dev`, which changes constantly.

**Why this priority**: Cost and noise reduction. Drift detection on `dev` produces false signals because `dev` is allowed to deviate.

**Independent Test**: Trigger the drift-detection workflow on its schedule (or via `workflow_dispatch`). Verify the matrix iterates only over `staging` and `production`; no job is scheduled for `dev`.

**Acceptance Scenarios**:

1. **Given** the drift-detection workflow runs on its schedule, **When** the run starts, **Then** the environment matrix contains exactly `staging` and `production` (and nothing else).
2. **Given** an operator triggers drift detection manually via `workflow_dispatch`, **When** the run starts, **Then** the same staging/production-only scope applies (or the input choice list excludes `dev`).
3. **Given** drift is detected in `staging`, **When** the workflow finishes, **Then** an issue is opened against the repository scoped to staging (existing behaviour preserved).

---

### User Story 4 - Retire the spec-029 progressive-delivery workflows (Priority: P2)

As a maintainer, I want the in-flight spec-029 workflows (`spec029-ci.yml`, `spec029-cd.yml`, `spec029-drift-detection.yml`) removed from the repository so contributors are not confused about which pipeline is authoritative, and so that the simplified pipeline is the single source of truth.

**Why this priority**: Removing the parallel/abandoned pipeline is essential to "simplification" — leaving it in place defeats the purpose. It is independent of the deployment flow itself.

**Independent Test**: After the change, list `.github/workflows/`. Verify the three `spec029-*.yml` files no longer exist and no remaining workflow references them (e.g., via `workflow_run`, `uses:`, or documentation).

**Acceptance Scenarios**:

1. **Given** the simplification is implemented, **When** an operator inspects `.github/workflows/`, **Then** `spec029-ci.yml`, `spec029-cd.yml`, and `spec029-drift-detection.yml` are absent.
2. **Given** the spec-029 workflows are deleted, **When** any remaining workflow runs, **Then** it does not depend on (or `workflow_run` from) any spec-029 workflow name.

---

### User Story 5 - Documented, time-bound credential decision-register entry (Priority: P3)

As an auditor or future maintainer, I can read a single decision-register entry that explains *why* the repository is using a service-principal `clientSecret` JSON object instead of OIDC federated credentials, *what* the security trade-off is, *who* decided, and *when* it must be revisited.

**Why this priority**: Important for governance and to ensure the deviation is paid down, but does not block the pipeline working end-to-end.

**Independent Test**: Open the new decision-register entry. Verify it identifies the deviation (long-lived client secret instead of OIDC), the rationale (MVP delivery), the risk (secret leakage / rotation burden), and a follow-up action item with an owner.

**Acceptance Scenarios**:

1. **Given** the decision-register entry exists, **When** a reviewer reads it, **Then** they can identify (a) the previous standard (OIDC federated credentials per-workflow), (b) the new MVP approach (`AZURE_CREDENTIALS` JSON in each GitHub environment), (c) the security trade-off, and (d) a follow-up action to migrate back to OIDC.
2. **Given** the decision is filed, **When** the simplification is reviewed at the next governance checkpoint, **Then** the entry can be located via the repository's existing decision/ADR conventions.

---

### Edge Cases

- A push lands on **two** environment branches in quick succession (e.g., a fast-forward merge from `dev` → `staging`): both `ci` runs must complete; the corresponding `cd` runs must serialize per-environment, never deploy `dev` artefacts to `staging` (and vice versa).
- The `production` branch receives a force-push or non-fast-forward push: `ci` and `cd` should still trigger on the resulting head commit; rollback must remain possible. Whether force-pushes are *allowed* on protected branches is a branch-protection concern outside this spec.
- `AZURE_CREDENTIALS` JSON is present but contains an expired `clientSecret`: deployment fails with an authentication error from Azure; the failure message must clearly indicate credential rotation is needed (we do not silently retry).
- A scheduled drift-detection run starts while a `cd` deployment to `staging` is in progress: the two must not interfere. Drift detection should produce a no-op or expected-pending state rather than flagging the in-flight deployment as drift.
- The `cd` workflow is triggered by `workflow_run` after `ci` succeeds, but the `ci` run was triggered by a `pull_request` (not a `push`): `cd` must **not** deploy on PR-driven CI runs, only on push-driven ones to the four named branches.
- Non-deploy workflows that touch Azure (`eval-pr-gate.yml`, the dormant Azure-publish block in `eval-publish-dataset.yml`) authenticate via `AZURE_CREDENTIALS` from the `dev` GitHub Environment per FR-019a / FR-019b — they are in scope of this simplification, not out of scope.

## Requirements *(mandatory)*

### Functional Requirements

**Branch-based triggers**

- **FR-001**: The `ci` workflow MUST trigger on `push` to each of the branches `main`, `dev`, `staging`, and `production`.
- **FR-002**: The `ci` workflow MUST also continue to trigger on pull requests targeting `main` (to keep PR gating intact).
- **FR-003**: The `cd` workflow MUST be a separate workflow file from `ci` and MUST be triggered by the `workflow_run` event on the `ci` workflow with `types: [completed]` filtered to the branches `dev`, `staging`, and `production`. CD MUST run only when the upstream `ci` run's `conclusion == 'success'` AND its `event == 'push'` (PR-driven CI runs MUST NOT cause `cd` to run; `main` is build-and-test only and does not deploy).
- **FR-003a**: The `cd` workflow MUST determine its target environment by reading `github.event.workflow_run.head_branch` and mapping `dev` → dev, `staging` → staging, `production` → production. The workflow MUST explicitly check out `github.event.workflow_run.head_sha` (not the default branch) to ensure the correct commit is deployed.
- **FR-004**: The `cd` workflow MUST deploy to **exactly one** Azure environment per run, determined by the source branch: `dev` → dev (resource group `rg-drh-dev`), `staging` → staging (resource group `rg-drh-staging`), `production` → production (resource group `rg-drh-production`). Cross-environment deployment within a single `cd` run MUST NOT occur.
- **FR-004a**: The `dev` Azure environment MUST be provisioned from the same `infra/main.bicep` template as staging and production, parameterised by a dev-specific Bicep parameter file (`infra/main.parameters.dev.json`, following the existing `main.parameters.<env>.json` convention) that selects cheaper/lower-tier SKUs appropriate for a non-production environment.
- **FR-005**: The `cd` workflow MUST use GitHub Actions concurrency controls so that only one `cd` run per target environment is active at any time, with newer runs queued (not cancelled) behind in-flight runs.
- **FR-006**: A `ci` run triggered by a `pull_request` event MUST NOT cause `cd` to run.

**Authentication & secrets**

- **FR-007**: Each of the GitHub environments `dev`, `staging`, and `production` MUST hold a single secret named `AZURE_CREDENTIALS` containing a JSON object with (at minimum) the keys `clientId`, `clientSecret`, `subscriptionId`, and `tenantId` in the format documented in the input.
- **FR-008**: Every active workflow that authenticates to Azure MUST authenticate using `AZURE_CREDENTIALS` (passed via the `creds:` input of `azure/login@v3`), and MUST NOT reference the legacy split values `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, or `AZURE_SUBSCRIPTION_ID` — whether sourced from `secrets.*` or `vars.*`.
- **FR-009**: Workflows MUST drop the `id-token: write` permission unless it is required by another action in the same job; the new auth path does not need OIDC token exchange.
- **FR-010**: Workflows that need Azure access from a scheduled or manual context MUST run inside a GitHub `environment:` block (or matrix entry that maps to one) so that `AZURE_CREDENTIALS` resolves correctly.

**Drift detection**

- **FR-011**: The drift-detection workflow MUST limit its environment matrix to exactly `staging` and `production`. It MUST NOT run against `dev`.
- **FR-012**: The drift-detection workflow MUST continue to support manual `workflow_dispatch` invocation, scoped to the same staging/production-only set.

**Workflow housekeeping**

- **FR-013**: The entire spec-029 progressive-delivery footprint MUST be deleted from the repository. This includes:
  - `.github/workflows/spec029-ci.yml`
  - `.github/workflows/spec029-cd.yml`
  - `.github/workflows/spec029-drift-detection.yml`
  - `.github/workflows/_reusable/pr-gates.yml` (orphaned once `spec029-ci.yml` is removed)
  - `.github/workflows/_reusable/canary-stage.yml` (orphaned once `spec029-cd.yml` is removed)
  - `.github/workflows/change-freeze.yml`
  - `.github/workflows/posture-exception-sweep.yml`
  - `.github/workflows/evidence-pack.yml`
  - `.github/workflows/dev-key-issue.yml`
  - `.github/workflows/emergency-hotfix.yml`
  - The `tools/pipeline` Python package.
  - All source artefacts whose only consumers are the workflows above. The full enumeration (transitively orphaned custom composite actions, IaC policy files, IDENTITY topology trust-root, freeze-state file, bootstrap scripts) is fixed in `research.md` §R6 — that table is the binding deletion list for this requirement.
- **FR-014**: After the spec-029 footprint is deleted, no remaining workflow MUST reference any of the deleted files (no `workflow_run.workflows` entry, no `uses:` reference, no `pip install -e ./tools/pipeline`, no `.github/CODEOWNERS` rule pointing at a deleted path, no `infra/main.bicep` comment naming a deleted file, no documentation that points to them as live).

**Failure & visibility**

- **FR-015**: When `cd` fails (provisioning, deploy, or post-deploy health check), the failing run MUST surface a clear summary in the GitHub Actions UI identifying the target environment, the failing step, and (where applicable) the rollback outcome.
- **FR-015a**: For `staging` and `production` only, on health-check failure the `cd` workflow MUST execute the rollback procedure (`scripts/rollback.sh` or equivalent) and, if the rollback itself fails, MUST create a GitHub issue labelled `critical` describing the environment, the failing step, and the manual remediation required.
- **FR-015b**: For `dev`, the `cd` workflow MUST NOT attempt automated rollback and MUST NOT auto-create critical-failure issues; a failed deploy leaves the dev environment in its failed state and surfaces only as a normal workflow failure.
- **FR-016**: When `AZURE_CREDENTIALS` is missing or unparseable for the target environment, the workflow MUST fail fast at the login step with a message that names the secret and the environment.

**Governance**

- **FR-017**: A decision-register entry MUST be added (under the repository's existing decision/ADR convention, e.g., `docs/aidr/decisions/`) that records the temporary use of a long-lived service-principal client secret JSON in lieu of OIDC federated credentials, including: rationale (MVP delivery), risk (secret leakage and manual rotation), expiry/review trigger (next governance checkpoint or before GA), and an owner.
- **FR-018**: The decision-register entry MUST link back to this specification (`specs/031-simplify-cicd-pipeline/spec.md`).

**Review of remaining workflows**

- **FR-019**: After the simplification is implemented, every remaining workflow under `.github/workflows/` MUST be reviewed to confirm it (a) uses `AZURE_CREDENTIALS` if it touches Azure, and (b) is still relevant to the simplified pipeline.
- **FR-019a**: `.github/workflows/eval-pr-gate.yml` MUST be migrated to authenticate via `AZURE_CREDENTIALS` sourced from the `dev` GitHub environment (PR evaluations run against dev infrastructure). Its existing references to `secrets.AZURE_CLIENT_ID`, `secrets.AZURE_TENANT_ID`, and `secrets.AZURE_SUBSCRIPTION_ID` MUST be removed.
- **FR-019b**: `.github/workflows/eval-publish-dataset.yml` MUST retain its current structure, but the commented-out Azure-publish section MUST be rewritten to use `AZURE_CREDENTIALS` (still commented) so the block is correct when an operator activates it later.
- **FR-020**: The reviewer MUST present three concrete recommendations for further simplification or hardening of the remaining workflows after the changes in FR-001 through FR-019b are applied, and MUST request individual feedback (accept / reject / modify) on each one before action is taken.

### Key Entities

- **Environment branch**: One of `dev`, `staging`, or `production`. A push to this branch is the only sanctioned trigger for a deployment to the matching Azure environment. `main` is the integration branch and is built/tested by `ci` but never deployed by `cd`.
- **GitHub Environment**: Named `dev`, `staging`, or `production`. Holds the `AZURE_CREDENTIALS` secret and any environment-scoped variables. May have its own approval/protection rules (existing behaviour preserved).
- **Azure resource group per environment**: `rg-drh-dev`, `rg-drh-staging`, `rg-drh-production`. Each is provisioned from the shared `infra/main.bicep` template using its corresponding `infra/main.parameters.<env>.json` parameter file; the dev parameter file uses lower-tier SKUs to control cost.
- **`AZURE_CREDENTIALS` secret**: A JSON object stored as a single GitHub Actions secret per environment. Contains the service-principal credentials used to authenticate with Azure. Treated as a long-lived secret with rotation responsibility documented in the decision register.
- **Decision-register entry**: A new markdown document under the repository's existing decisions/ADR location that records the deviation from the OIDC standard and the path back to it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A push to any of `dev`, `staging`, or `production` triggers `ci`, and on success triggers `cd`, deploying only to the matching environment, with no human intervention required between the two workflows.
- **SC-002**: 100% of active workflows (counted as files under `.github/workflows/` excluding archived/reusable templates) that touch Azure authenticate via the single `AZURE_CREDENTIALS` JSON secret. Zero references to the legacy `AZURE_CLIENT_ID` / `AZURE_TENANT_ID` / `AZURE_SUBSCRIPTION_ID` triplet remain in active workflows.
- **SC-003**: The repository contains zero files matching `.github/workflows/spec029-*.yml`, zero files under `.github/workflows/_reusable/`, zero of the standalone spec-029 workflows (`change-freeze`, `posture-exception-sweep`, `evidence-pack`, `dev-key-issue`, `emergency-hotfix`), and no `tools/pipeline` package.
- **SC-004**: The drift-detection workflow's matrix evaluates to exactly two entries (`staging`, `production`) in any run; zero drift-detection runs are recorded against `dev`.
- **SC-005**: A new contributor can deploy to `dev` by creating one secret (`AZURE_CREDENTIALS`) in the `dev` GitHub environment and pushing to the `dev` branch — no other workflow editing or secret configuration is required.
- **SC-006**: The decision-register entry recording the service-principal-secret deviation exists, is linked from this spec, and identifies a named owner and a review trigger.
- **SC-007**: After implementation, the time from "push to `dev`" to "deployment complete in dev" is no greater than the equivalent end-to-end time observed on the previous pipeline (i.e., simplification does not regress deployment latency).
- **SC-008**: Three concrete follow-up recommendations are presented to the maintainer for individual review, with each recommendation including the change proposed, the reason, and the trade-off.

## Assumptions

- The repository's existing branch-protection rules will be updated by an operator (out of scope of this spec) so that `dev`, `staging`, and `production` are protected and only updated via reviewed PRs or controlled merges. The simplification does not require any specific protection rule, but absence of one would let any contributor deploy.
- The `AZURE_CREDENTIALS` JSON object is created and populated by an operator out of band (Azure-side service principal creation is not in scope of this spec).
- The Azure resource groups and target services already exist or will be provisioned by the existing `azd provision` step inside `cd` (we do not redesign provisioning).
- Workflows that are not strictly part of the deploy flow but still reach Azure (specifically `eval-pr-gate.yml` and the commented section of `eval-publish-dataset.yml`) will be migrated to `AZURE_CREDENTIALS` in the same change for consistency. `eval-pr-gate.yml` will source the secret from the `dev` GitHub environment.
- The decision-register location follows the existing convention in `docs/aidr/decisions/` (or the equivalent location used by other ADRs in the repo at implementation time).
- The `main` branch remains the integration branch; merging to `main` runs `ci` only and is not a deploy trigger.

## Out of Scope

- Re-introducing OIDC federated credentials (this is a planned future migration tracked by the decision-register entry, not part of this change).
- Adding new deployment topologies (canary, blue/green, ring-based) — these were part of the spec-029 design that is being explicitly retired here.
- Changing the Azure resource layout (resource groups, naming, regions).
- Re-architecting health checks, rollback, or evidence-pack generation **beyond the per-environment scoping in FR-015a / FR-015b** (existing behaviour in `cd.yml` is otherwise preserved).
- Branch-protection / required-reviewer policy changes on `dev`, `staging`, `production` (operator concern).
- Secret rotation tooling for `AZURE_CREDENTIALS` (manual rotation is acceptable for MVP and is called out in the decision-register entry).
