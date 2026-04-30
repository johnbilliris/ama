---
description: "Task list for spec 031 — Simplify CI/CD with branch-based deployment. Each task includes the responsible actor agent, tools to use, and explicit success criteria."
---

# Tasks: Simplify CI/CD with Branch-Based Deployment

**Input**: Design documents from `C:\code\ama\specs\031-simplify-cicd-pipeline\`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅
**Tests**: Not requested — there is no existing test framework for CI/CD workflows themselves. Validation is performed via `actionlint`/`grep` checks and the smoke tests in `quickstart.md`.
**Organization**: Tasks grouped by user story (US1–US5) per `spec.md`; each story is independently testable.

## Format

```text
- [ ] T### [P?] [USx?] Description with absolute file path
      🧑 Agent: <actor-agent-id from .github/agents/>
      🔧 Tools: <commands or actions used>
      ✅ Success: <explicit, verifiable criterion>
```

- **[P]** = task can run in parallel with other [P] tasks in the same phase (different files, no ordering dep)
- **[USx]** = user story tag (matches spec.md user stories)
- **Agent IDs** are drawn from `.github/agents/AGENTS.md` and `.github/agents/technical/`

## Path conventions

- All paths are absolute Windows paths under `C:\code\ama\`.
- Workflow files live in `.github\workflows\` (and `.github\workflows\_reusable\`).
- Custom composite actions in `.github\actions\`.
- IaC parameter files in `infra\`.
- Decision register entries in `docs\aidr\decisions\`.
- One-off operator scripts (already present) in `scripts\`.

---

## Phase 1: Setup (Shared artefacts)

**Purpose**: Create the new artefacts (Bicep parameter file for `dev`, ADR) that downstream workflow changes will reference. These are independent of any deletion or workflow modification and can run in parallel.

- [ ] T001 [P] Create the dev Bicep parameter file at `C:\code\ama\infra\main.parameters.dev.json` using the value table in `research.md` §R3 (`environmentName=drh-dev`, `location=australiaeast`, `principalType=ServicePrincipal`, `developerIpAddress=""`, `actionGroupEmail="dev-ops@example.com"`, `actionGroupWebhook=""`, `openAiDeploymentSku="GlobalStandard"`, `restrictNetworkAccess=false`).
      🧑 Agent: `infrastructure-devops`
      🔧 Tools: `create` tool; reference `infra\main.parameters.staging.json` for shape.
      ✅ Success: File exists, parses as valid JSON, all 7 parameters present and match `research.md` §R3 exactly. `Get-Content infra\main.parameters.dev.json | ConvertFrom-Json | Out-Null` returns no error.

- [ ] T002 [P] Create the decision-register entry at `C:\code\ama\docs\aidr\decisions\adr-031-azure-credentials-mvp.md` following the section structure defined in `data-model.md` §7 (Status=Accepted (time-bound); Context; Decision; Consequences a/b/c; Trade-offs accepted; Review trigger; Owner=`<TBD by maintainer>`; Links back to `specs/031-simplify-cicd-pipeline/spec.md` and forward to ADR-029-01).
      🧑 Agent: `compliance-auditor`
      🔧 Tools: `create`; reference `docs\aidr\decisions\adr-f02-async-bridge.md` for ADR style; cite Constitution NN-2 carve-out clause.
      ✅ Success: File exists; contains all 7 required sections from `data-model.md` §7; contains a literal link to `../../../specs/031-simplify-cicd-pipeline/spec.md`; contains the string "90 days" (rotation cadence per R10) and the string "Foundry-carve-out" (NN-2 regression note per R7).

**Checkpoint**: Both new artefacts exist; no workflow has been changed yet, so the existing pipeline still works.

---

## Phase 2: Foundational (Spec-029 footprint deletion)

**Purpose**: Delete the entire spec-029 footprint per the clarification answer to Q1. Must complete before US1/US2 verification (`grep` checks in T013/T024 and SC-002/SC-003 require zero remaining references). The deletions touch different paths so they parallelise within the phase.

**⚠️ CRITICAL**: No user story validation can pass until this phase is complete (the `ruff`/`actionlint` noise from leftover spec-029 files would create false negatives).

- [ ] T003 [P] Delete the three named spec-029 workflow files: `C:\code\ama\.github\workflows\spec029-ci.yml`, `C:\code\ama\.github\workflows\spec029-cd.yml`, `C:\code\ama\.github\workflows\spec029-drift-detection.yml`.
      🧑 Agent: `infrastructure-devops`
      🔧 Tools: `Remove-Item` (PowerShell) or `git rm`.
      ✅ Success: `Test-Path C:\code\ama\.github\workflows\spec029-*.yml` returns `$false` for all three.

- [ ] T004 [P] Delete the entire `_reusable` workflow folder: `C:\code\ama\.github\workflows\_reusable\` (contains `pr-gates.yml` and `canary-stage.yml`).
      🧑 Agent: `infrastructure-devops`
      🔧 Tools: `Remove-Item -Recurse`.
      ✅ Success: `Test-Path C:\code\ama\.github\workflows\_reusable` returns `$false`.

- [ ] T005 [P] Delete the five standalone spec-029 workflows: `C:\code\ama\.github\workflows\change-freeze.yml`, `posture-exception-sweep.yml`, `evidence-pack.yml`, `dev-key-issue.yml`, `emergency-hotfix.yml`.
      🧑 Agent: `infrastructure-devops`
      🔧 Tools: `Remove-Item` (one call per file or wildcard list).
      ✅ Success: All five files absent under `.github\workflows\`.

- [ ] T006 [P] Delete the three custom composite actions whose only consumers are now gone: `C:\code\ama\.github\actions\install-opa\`, `C:\code\ama\.github\actions\setup-cosign-syft\`, `C:\code\ama\.github\actions\setup-oidc-azure\`.
      🧑 Agent: `infrastructure-devops`
      🔧 Tools: `Remove-Item -Recurse`.
      ✅ Success: All three subdirectories absent. `Get-ChildItem C:\code\ama\.github\actions\` shows zero entries (or only entries unrelated to spec-029).

- [ ] T007 [P] Delete the freeze-state file: `C:\code\ama\.github\state\freeze.json`. If `.github\state\` becomes empty, delete the directory too.
      🧑 Agent: `infrastructure-devops`
      🔧 Tools: `Remove-Item`.
      ✅ Success: File absent; if directory was the only consumer, directory also absent.

- [ ] T008 [P] Delete the `tools/pipeline` Python package: `C:\code\ama\tools\pipeline\` (entire directory tree, including `src/pipeline_tools/`, `tests/`, `pyproject.toml`, `.ruff_cache`, etc.).
      🧑 Agent: `software-developer`
      🔧 Tools: `Remove-Item -Recurse -Force`.
      ✅ Success: `Test-Path C:\code\ama\tools\pipeline` returns `$false`. `pip show pipeline-tools` returns "Package not found" (it was an editable install only ever consumed by deleted workflows).

- [ ] T009 [P] Delete the spec-029 supporting infra: `C:\code\ama\infra\IDENTITY.md`, `C:\code\ama\infra\policy\posture-matrix.yaml`, `C:\code\ama\infra\policy\posture-exceptions.yaml`, `C:\code\ama\infra\policy\foundry-carveout.yaml`, and the entire `C:\code\ama\infra\policy\rego\` directory. (Keep `C:\code\ama\infra\bicep\modules\posture-policy-set.bicep` per `research.md` §R6 "Out of scope".)
      🧑 Agent: `infrastructure-devops`
      🔧 Tools: `Remove-Item`; cross-reference `research.md` §R6 deletion table; **do NOT** delete `posture-policy-set.bicep`.
      ✅ Success: Five named items absent; `posture-policy-set.bicep` still present. `Get-ChildItem C:\code\ama\infra\policy\rego -ErrorAction SilentlyContinue` returns nothing.

- [ ] T009a [P] Clean the dangling `IDENTITY.md` reference in `C:\code\ama\infra\main.bicep` (line ~55, comment on the `subscriptionId` parameter). Replace the existing description `'Spec 029 — Azure subscription ID this deployment targets. Validated by deployment workflows against infra/IDENTITY.md.'` with `'Azure subscription ID this deployment targets.'` (drops the spec-029 / IDENTITY.md sentence; the validation it referenced no longer exists once T009 lands).
      🧑 Agent: `infrastructure-devops`
      🔧 Tools: `edit` (single targeted change to the `@description(...)` decorator).
      ✅ Success: `grep -n "IDENTITY.md\|Spec 029" C:\code\ama\infra\main.bicep` returns zero matches. Bicep still parses (`az bicep build --file infra/main.bicep` succeeds).

- [ ] T010 [P] Delete the spec-029 bootstrap scripts: `C:\code\ama\scripts\spec029-bootstrap\` (entire directory).
      🧑 Agent: `infrastructure-devops`
      🔧 Tools: `Remove-Item -Recurse`.
      ✅ Success: `Test-Path C:\code\ama\scripts\spec029-bootstrap` returns `$false`. `C:\code\ama\scripts\rollback.sh` still present (untouched).

- [ ] T011 [P] Delete the legacy `infra\main.parameters.development.json` (replaced by `main.parameters.dev.json` per R3; the new branch is `dev`, not `development`).
      🧑 Agent: `infrastructure-devops`
      🔧 Tools: `Remove-Item`. Before deleting, `grep` for `main.parameters.development.json` across the repo to confirm zero remaining references.
      ✅ Success: File absent; `grep -r "main.parameters.development.json" .` returns zero matches.

- [ ] T011a [P] Prune the dead spec-029 entries from `C:\code\ama\.github\CODEOWNERS`. Specifically: delete the "Spec 029 — Progressive Delivery Pipeline" header block (lines 27-34, the comment block) and lines 35-39, 41-45 (rules pointing at `infra/policy/posture-matrix.yaml`, `infra/policy/posture-exceptions.yaml`, `infra/policy/foundry-carveout.yaml`, `infra/policy/rego/`, `infra/IDENTITY.md`, `change-freeze.yml`, `emergency-hotfix.yml`, `evidence-pack.yml`, `_reusable/`, `tools/pipeline/`). **Preserve line 40** (`.github/workflows/cd.yml @johnbilliris`) — that workflow survives the simplification and the ownership rule remains valid.
      🧑 Agent: `infrastructure-devops` (mechanics) + `security-engineer` (verifies no surviving Azure-touching workflow loses ownership)
      🔧 Tools: `view` lines 27-46 of CODEOWNERS; `edit` to remove the header block and the 10 dead rules while preserving the cd.yml rule.
      ✅ Success: `grep -nE "tools/pipeline|spec.?029|IDENTITY\\.md|posture-matrix|posture-exceptions|foundry-carveout|infra/policy/rego|change-freeze|emergency-hotfix|evidence-pack|_reusable" C:\code\ama\.github\CODEOWNERS` returns zero matches. Line `cd.yml @johnbilliris` still present. `gh api -X POST /repos/johnbilliris/ama/codeowners/errors` (or the equivalent UI check) reports zero CODEOWNERS errors.

- [ ] T012 Verify the spec-029 footprint is fully removed (no orphans, no dangling references). Run a repository-wide `grep` for the strings `spec029`, `spec-029`, `setup-oidc-azure`, `setup-cosign-syft`, `install-opa`, `pipeline_tools`, `tools/pipeline`, `posture-verifier`, `freeze-controller`, `evidence-packer`, `IDENTITY.md`, `posture-exceptions.yaml`, `posture-matrix.yaml`, `foundry-carveout.yaml`. The only surviving matches MUST be inside `specs/029-progressive-delivery-pipeline/` (historical), inside `specs/031-simplify-cicd-pipeline/` (this spec), or in `docs/aidr/decisions/adr-031-azure-credentials-mvp.md` (the ADR itself).
      🧑 Agent: `principal-engineer`
      🔧 Tools: `grep` (the built-in tool, not powershell); `git status` to confirm only deletions are staged.
      ✅ Success: No matches outside the three allowed locations. Document the surviving matches in the task tracker as expected.

- [ ] T012a Run a one-off `az deployment group what-if` against an empty/stub resource group using `infra/main.bicep` + the new `infra/main.parameters.dev.json`, to satisfy the Constitution Quality Gate ("Infrastructure changes MUST include a What-If / Plan review"). Capture the full output and attach it to the PR description. The expected output for a non-existent target RG is the full set of `Create` actions for every resource the Bicep template defines (no `Modify` / `Delete`); confirm there are zero validation errors and no surprise resources outside `australiaeast`.
      🧑 Agent: `infrastructure-devops` (executes) + `azure-principal-architect` (reviews the What-If output for unexpected drift / region escapes)
      🔧 Tools: `az group create --name rg-drh-dev-whatif --location australiaeast` (temporary), `az deployment group what-if --resource-group rg-drh-dev-whatif --template-file infra/main.bicep --parameters @infra/main.parameters.dev.json`, then `az group delete --name rg-drh-dev-whatif --yes --no-wait` to clean up. Operator may instead run against the real `rg-drh-dev` once it exists for an additive what-if.
      ✅ Success: What-If completes with exit code 0; output attached to PR description; reviewer confirms (a) zero validation errors, (b) all created resources have `location: australiaeast`, (c) no resources reference deleted spec-029 paths. Constitution Quality Gate satisfied for the dev IaC change.

**Checkpoint**: The spec-029 footprint is gone. From here, the four user stories can proceed in priority order (or in parallel for the two P1 stories if multiple developers are available).

---

## Phase 3: User Story 1 — Predictable branch-based deployment (Priority: P1) 🎯 MVP

**Goal**: Pushes to `dev`, `staging`, `production` trigger CI; on success, CD deploys to *exactly* the matching Azure environment, with no human intervention and no cross-environment leakage.

**Independent Test**: Push an empty commit to `dev` (after secret setup in US2). Confirm via the Actions UI: (1) one `ci` run starts and completes for the `dev` ref, (2) one `cd` run starts (triggered by `workflow_run`) and deploys to `rg-drh-dev` only, (3) no run is created against `rg-drh-staging` or `rg-drh-production`. Repeat for `staging` and `production`.

### Implementation for User Story 1

- [ ] T013 [US1] Modify `C:\code\ama\.github\workflows\ci.yml` per `contracts\ci-workflow.md`: replace the existing `on.push.branches` list (`main`, `001-disaster-response-hub`, `003-rubric-gap-closure`, `015-performance-benchmarks`) with exactly `[main, dev, staging, production]`; constrain `on.pull_request` to `branches: [main]`; keep all `quality` job steps unchanged.
      🧑 Agent: `infrastructure-devops`
      🔧 Tools: `edit` to replace the `on:` block in place. Validate with `actionlint .github/workflows/ci.yml` if available.
      ✅ Success: `grep -E "001-disaster-response-hub|003-rubric-gap-closure|015-performance-benchmarks" .github\workflows\ci.yml` returns zero matches. The file's `on.push.branches` list contains exactly the four canonical branches in that order. The `quality` job steps and order are byte-identical to the previous version.

- [ ] T014 [US1] Rewrite `C:\code\ama\.github\workflows\cd.yml` per `contracts\cd-workflow.md` (this is the single largest change). Specifically: (a) change `on.workflow_run.branches` from `[main]` to `[dev, staging, production]`; (b) remove the existing `deployment-gates` and `deploy-production` jobs (consolidated into a single dynamic `deploy` job); (c) the new `deploy` job has `environment: ${{ github.event.workflow_run.head_branch }}`, `concurrency.group: deploy-${{ github.event.workflow_run.head_branch }}`, `cancel-in-progress: false`; (d) job-level `if:` requires both `workflow_run.conclusion == 'success'` AND `workflow_run.event == 'push'`; (e) Step 1 checks out `ref: ${{ github.event.workflow_run.head_sha }}`; (f) Step 2 sets `TARGET_ENV=${{ github.event.workflow_run.head_branch }}` to `$GITHUB_ENV`; (g) all subsequent `rg-drh-staging`/`rg-drh-production` literals are replaced with `rg-drh-${TARGET_ENV}` and `drh-staging`/`drh-production` env names with `drh-${TARGET_ENV}`; (h) rollback step gains `&& env.TARGET_ENV != 'dev'` to its `if:` condition; (i) critical-failure issue step gains the same `&& env.TARGET_ENV != 'dev'` guard; (j) the deployment-status logic adds a `failed-no-rollback` case for the dev path. (Auth migration to `AZURE_CREDENTIALS` happens in T017 in US2; for now the existing `client-id`/`tenant-id`/`subscription-id` lines remain to keep the file syntactically valid until US2 lands.)
      🧑 Agent: `infrastructure-devops` (primary), with review by `sre-engineer` for rollback semantics
      🔧 Tools: `view` the current `cd.yml`; `edit` (multiple non-overlapping calls in one response) to apply each of (a)–(j); confirm the result against `contracts\cd-workflow.md`.
      ✅ Success: `grep -E "rg-drh-staging|rg-drh-production|drh-staging|drh-production" .github\workflows\cd.yml` returns zero matches (all replaced with `${TARGET_ENV}` patterns). The `on.workflow_run.branches` list is `[dev, staging, production]`. The `deployment-gates` and `deploy-production` job names no longer appear. The `if:` on the rollback and critical-failure steps both contain `env.TARGET_ENV != 'dev'`. The checkout step references `github.event.workflow_run.head_sha`. `actionlint .github/workflows/cd.yml` passes.

- [ ] T015 [US1] (Operator action — documented; not auto-executed by this PR) Create the three environment branches from `main` via `git push origin main:dev`, `main:staging`, `main:production` per `quickstart.md` §1.
      🧑 Agent: `infrastructure-devops` (operator-facing runbook step)
      🔧 Tools: `git push`; `gh api` (repository admin call); steps fully scripted in `quickstart.md` §1.
      ✅ Success: `git ls-remote --heads origin` returns refs for `main`, `dev`, `staging`, `production`. The PR description for spec 031 calls out this step as a prerequisite for the first deploy.

- [ ] T016 [US1] (Operator action — documented; recommended) Configure branch protection on `dev`, `staging`, `production`: require PR + 1 approving review + status check `ci / quality` per `quickstart.md` §1.
      🧑 Agent: `security-engineer` (governance) + `infrastructure-devops` (mechanics)
      🔧 Tools: `gh api -X PUT /repos/johnbilliris/ama/branches/<branch>/protection` or GitHub UI.
      ✅ Success: Each of the three branches shows "Protected" in the GitHub UI; pushes from a non-admin without an approved PR are rejected. (Operator confirms on a per-environment basis; not auto-validated.)

**Checkpoint**: US1 implementation complete in workflow files; end-to-end verification waits on US2 (secrets) before the first push to `dev` will succeed.

---

## Phase 4: User Story 2 — Single AZURE_CREDENTIALS auth (Priority: P1)

**Goal**: Every workflow that touches Azure authenticates via the single `AZURE_CREDENTIALS` JSON secret stored per GitHub Environment. No legacy `AZURE_CLIENT_ID`/`AZURE_TENANT_ID`/`AZURE_SUBSCRIPTION_ID` references remain.

**Independent Test**: Run `grep -rE "AZURE_CLIENT_ID|AZURE_TENANT_ID|AZURE_SUBSCRIPTION_ID" .github\workflows\` — expected output: zero matches across all active workflows. After operator setup (T021/T022), push an empty commit to `dev` and confirm `azure/login` succeeds at the first step that needs Azure access.

### Implementation for User Story 2

- [ ] T017 [US2] Update the `azure/login` invocation in `C:\code\ama\.github\workflows\cd.yml` to use the single secret. Replace the three-input form (`client-id`/`tenant-id`/`subscription-id` reading from `vars.*`) with `creds: ${{ secrets.AZURE_CREDENTIALS }}` per `contracts\cd-workflow.md`. Bump the action version to `azure/login@v3`. Remove the `permissions: id-token: write` line at workflow level (keep only `contents: read`, `issues: write`, `actions: read`).
      🧑 Agent: `infrastructure-devops` (primary) + `security-engineer` (verifies the credential is sourced from the env, not the org/repo level)
      🔧 Tools: `edit` (one targeted change to the `azure/login` step + one to the `permissions:` block).
      ✅ Success: `grep -E "vars\\.AZURE_(CLIENT|TENANT|SUBSCRIPTION)_ID|secrets\\.AZURE_(CLIENT|TENANT|SUBSCRIPTION)_ID|id-token: write" .github\workflows\cd.yml` returns zero matches. The single `azure/login@v3` step has exactly `creds: ${{ secrets.AZURE_CREDENTIALS }}`.

- [ ] T018 [US2] Update `C:\code\ama\.github\workflows\drift-detection.yml` per `contracts\drift-detection.contract.md`: bump `azure/login@v2` → `@v3`; replace the three-input form with `creds: ${{ secrets.AZURE_CREDENTIALS }}`; add `environment: ${{ matrix.environment }}` at job level (so the secret resolves from the matching GitHub Environment); remove `permissions: id-token: write`. Confirm matrix is already `[staging, production]` (it should be).
      🧑 Agent: `infrastructure-devops`
      🔧 Tools: `edit` (three targeted changes — login step, env binding, permissions block).
      ✅ Success: `azure/login@v3 with: creds:` is the sole auth path; the `environment:` key is set per matrix entry; no `id-token: write` line; matrix is exactly `[staging, production]`.

- [ ] T019 [US2] Update `C:\code\ama\.github\workflows\eval-pr-gate.yml` per the spec clarification (Q5). Replace the `azure/login@v2` block (which uses `secrets.AZURE_CLIENT_ID`/`TENANT_ID`/`SUBSCRIPTION_ID`) with `azure/login@v3 with: creds: ${{ secrets.AZURE_CREDENTIALS }}`. Add a job-level `environment: dev` so the secret resolves from the `dev` GitHub Environment. Remove `id-token: write` from `permissions:` (keep `contents: read`, `pull-requests: write`). Update the two `if:` guards on the trigger/poll steps from `${{ secrets.AZURE_CLIENT_ID != '' }}` to `${{ secrets.AZURE_CREDENTIALS != '' }}`.
      🧑 Agent: `infrastructure-devops` + `qa-test-engineer` (PR-eval flow correctness)
      🔧 Tools: `edit` (four targeted changes).
      ✅ Success: `grep -E "AZURE_CLIENT_ID|AZURE_TENANT_ID|AZURE_SUBSCRIPTION_ID" .github\workflows\eval-pr-gate.yml` returns zero matches. The `environment: dev` line is present at the job level. The `if:` guards reference `AZURE_CREDENTIALS`.

- [ ] T020 [US2] Rewrite the commented-out Azure-publish section in `C:\code\ama\.github\workflows\eval-publish-dataset.yml` so that when an operator uncomments it later, it uses `azure/login@v3 with: creds: ${{ secrets.AZURE_CREDENTIALS }}` instead of the current commented split-secret form. Add a note in the comment block stating which GitHub Environment the operator should activate the workflow under (recommend `dev` for dataset development; the operator picks the right environment when uncommenting).
      🧑 Agent: `data-engineer` (owns the eval-dataset flow) + `infrastructure-devops` (auth pattern)
      🔧 Tools: `edit` (single change to the commented block).
      ✅ Success: The commented block contains `creds: ${{ secrets.AZURE_CREDENTIALS }}` (still inside `#` comment markers); contains a `# NOTE:` line naming the environment-binding requirement; does not contain the legacy split-secret form.

- [ ] T021 [US2] (Operator action — documented) Create three Azure service principals (one per environment) using `az ad sp create-for-rbac --name "sp-drh-<env>-cicd" --role Contributor --scopes /subscriptions/<sub> --sdk-auth` per `quickstart.md` §2. Capture the three JSON outputs to local files temporarily.
      🧑 Agent: `security-engineer` (SP creation + scope review) + `infrastructure-devops` (mechanics)
      🔧 Tools: `az` CLI (`az login`, `az ad sp create-for-rbac --sdk-auth`); secret JSON files MUST be deleted after T022.
      ✅ Success: Three SPNs exist in Entra (`sp-drh-dev-cicd`, `sp-drh-staging-cicd`, `sp-drh-production-cicd`); each has Contributor scope on the target subscription; each JSON output validates against `contracts/azure-credentials.schema.json`.

- [ ] T022 [US2] (Operator action — documented) Create the three GitHub Environments (`dev`, `staging`, `production`) and populate `AZURE_CREDENTIALS` in each via `gh secret set AZURE_CREDENTIALS --env <env> --body "$(cat azure-credentials-<env>.json)"` per `quickstart.md` §3. Then delete the three local JSON files.
      🧑 Agent: `infrastructure-devops` (mechanics) + `security-engineer` (verifies secrets are env-scoped, not repo-scoped, and that local files are deleted)
      🔧 Tools: `gh api -X PUT /repos/.../environments/<env>`, `gh secret set --env`, `Remove-Item` for the local JSON files.
      ✅ Success: `gh secret list --env dev` (and likewise for staging/production) shows `AZURE_CREDENTIALS` and only `AZURE_CREDENTIALS` for Azure auth. No local `azure-credentials-*.json` files exist on the operator workstation.

- [ ] T023 [US2] Repository-wide verification: `grep` confirms zero references to legacy split-secret patterns across all *active* workflows. Run `grep -rE "secrets\\.AZURE_(CLIENT|TENANT|SUBSCRIPTION)_ID|vars\\.AZURE_(CLIENT|TENANT|SUBSCRIPTION)_ID" C:\code\ama\.github\workflows\` and assert empty output. Also `grep -rn "permissions:" .github\workflows\` and assert that any `id-token: write` line that survives is intentional and documented in a comment immediately above it.
      🧑 Agent: `principal-engineer` (final gatekeeper)
      🔧 Tools: `grep` (built-in).
      ✅ Success: Zero matches for the legacy pattern; every surviving `id-token: write` (if any) is preceded by a `# RATIONALE:` comment.

**Checkpoint**: All Azure-touching workflows authenticate via `AZURE_CREDENTIALS`. With T015/T016/T021/T022 complete, push to `dev` should now exercise the full US1+US2 path end-to-end.

---

## Phase 5: User Story 3 — Drift detection scoped to staging/production (Priority: P2)

**Goal**: The drift-detection workflow runs only against `staging` and `production`, never against `dev`.

**Independent Test**: Trigger `drift-detection` via `workflow_dispatch`. Confirm the Actions UI shows exactly two matrix jobs (`staging`, `production`) and zero `dev` jobs.

### Implementation for User Story 3

- [ ] T024 [US3] Verify (no functional change required — the matrix is already `[staging, production]`) that `C:\code\ama\.github\workflows\drift-detection.yml` matrix scope is `environment: [staging, production]` and **add** the FR-011 annotation comment `# Per spec 031 / FR-011: dev is intentionally excluded from drift detection.` immediately above the `strategy.matrix` block so a reader of just the YAML understands the constraint.
      🧑 Agent: `sre-engineer` (drift detection is an SRE responsibility)
      🔧 Tools: `view` to confirm current matrix; `edit` to add the annotation comment.
      ✅ Success: Matrix is exactly `[staging, production]` (verified by `grep -A1 'matrix:' .github\workflows\drift-detection.yml`); the FR-011 annotation comment is present immediately above the `strategy.matrix` block.

**Checkpoint**: Drift detection scope is locked and documented.

---

## Phase 6: User Story 4 — Spec-029 footprint retired (Priority: P2)

**Goal**: The repository contains no live spec-029 progressive-delivery artefacts.

**Independent Test**: Run the verification commands in `quickstart.md` §"Smoke tests" row "Spec-029 footprint deleted". All paths return absent / empty.

### Implementation for User Story 4

(Implementation done in Phase 2 — T003–T011. This phase is verification-only.)

- [ ] T025 [US4] Run the explicit FR-013/FR-014 acceptance check: enumerate every entry in the `research.md` §R6 deletion table and assert each path is absent. Then run `grep -rln "workflow_run.workflows.*spec029|uses:.*\\(install-opa\\|setup-cosign-syft\\|setup-oidc-azure\\|_reusable\\)|pipeline_tools|tools/pipeline" .github\ infra\ scripts\` and assert zero matches.
      🧑 Agent: `principal-engineer`
      🔧 Tools: `Test-Path` (PowerShell loop over the deletion table); `grep` (multi-pattern).
      ✅ Success: All 21 paths in the §R6 deletion table return `False` to `Test-Path`; the cross-reference `grep` returns zero matches; `git status` shows the deletions are staged/committed.

**Checkpoint**: Spec-029 surface area is verified gone.

---

## Phase 7: User Story 5 — Decision-register entry filed (Priority: P3)

**Goal**: A documented, time-bound, owned ADR exists explaining the temporary departure from OIDC.

**Independent Test**: Open `docs\aidr\decisions\adr-031-azure-credentials-mvp.md`. Confirm the seven required sections from `data-model.md` §7 are present, the link back to this spec resolves, and a single owner is named.

### Implementation for User Story 5

(File created in T002 in Phase 1. This phase is operator-driven completion + verification.)

- [ ] T026 [US5] (Operator action) The maintainer fills in the `Owner:` field in `C:\code\ama\docs\aidr\decisions\adr-031-azure-credentials-mvp.md` with their own name/handle and a contact method. The maintainer also confirms the "Review trigger" wording matches their governance cadence (the default is "before public GA, OR at the next governance checkpoint, OR upon any production-secret leakage incident").
      🧑 Agent: `compliance-auditor` (drives the maintainer to fill the field) + `principal-engineer` (final reviewer)
      🔧 Tools: `edit` (single field substitution).
      ✅ Success: The literal string `<TBD by maintainer>` no longer appears in the ADR; an owner is named; the ADR is committed alongside the rest of the PR.

**Checkpoint**: All five user stories implemented and verified.

---

## Phase 8: Polish & Cross-Cutting Concerns (FR-019/020 review + smoke tests)

**Purpose**: Workflow review, three FR-020 recommendations, and end-to-end smoke validation per `quickstart.md`.

- [ ] T027 [P] Review every remaining workflow under `C:\code\ama\.github\workflows\` (after Phase 2 deletions) to confirm: (a) it uses `AZURE_CREDENTIALS` if it touches Azure (per T023); (b) it is still relevant to the simplified pipeline; (c) action versions are pinned to a current major (`@v5`/`@v6` for `actions/*`, `@v3` for `azure/login`). Produce a one-paragraph review note per workflow file (`ci.yml`, `cd.yml`, `drift-detection.yml`, `eval-pr-gate.yml`, `eval-publish-dataset.yml`).
      🧑 Agent: `principal-engineer` (chairs the review) + `infrastructure-devops` + `sre-engineer`
      🔧 Tools: `view` each workflow; `actionlint` if available; reference the contracts in `specs/031-simplify-cicd-pipeline/contracts/`.
      ✅ Success: A review note exists for each of the five surviving workflows; each note states "RELEVANT" or "DEPRECATE" and lists any version-pin discrepancies found.

- [ ] T028 [P] Produce the three FR-020 recommendations. Each recommendation MUST follow this structure: **(1) Proposed change**, **(2) Reason**, **(3) Trade-off / cost**. The three recommendations are seeded from `research.md` and the FR-019 review:
      - **Rec A**: Re-introduce automated NN-2 Foundry-carve-out enforcement (regression noted in Constitution Check).
      - **Rec B**: Plan the OIDC migration that supersedes the long-lived `clientSecret` (referenced in ADR-031 review trigger).
      - **Rec C**: One additional recommendation chosen from T027's review notes (likely candidates: consolidate the two `eval-*` workflows; add `actionlint` as a CI gate; pin `Azure/setup-azd` action by SHA).
      Then present each recommendation to the maintainer one at a time and request individual feedback (accept / reject / modify). Record the responses next to each recommendation.
      🧑 Agent: `principal-engineer` (chairs the conversation) + `solution-architect` (Rec B sign-off) + `compliance-auditor` (Rec A sign-off)
      🔧 Tools: `ask_user` (one call per recommendation); record outcomes in the PR description or in `docs\aidr\decisions\` follow-up entries.
      ✅ Success: Three recommendations are presented in three separate `ask_user` calls; each response is captured in the PR description with a clear accept/reject/modify outcome and (for accepted/modified) a follow-up issue number or owner.

- [ ] T029 Run the eight smoke tests in `C:\code\ama\specs\031-simplify-cicd-pipeline\quickstart.md` §"Smoke tests (verify spec success criteria)". Each smoke test maps to a Success Criterion (SC-001 through SC-008). Document the pass/fail of each in the PR description. **Additionally, run an explicit FR-016 smoke test**: temporarily clear (or rename) the `AZURE_CREDENTIALS` secret in the `dev` GitHub Environment, push an empty commit to `dev`, and confirm the resulting `cd` run fails fast at the `azure/login` step with an error message that **names both the secret (`AZURE_CREDENTIALS`) and the environment (`dev`)**. Restore the secret afterwards. Record the observed error message verbatim in the PR description.
      🧑 Agent: `qa-test-engineer` + `infrastructure-devops`
      🔧 Tools: `git push` for the dev/staging push tests; `gh secret list --env <env>` for SC-002/005; `Get-ChildItem`/`Test-Path` for SC-003; `gh workflow run drift-detection.yml` for SC-004; `cat` for SC-006; pipeline duration comparison for SC-007; review the recorded responses from T028 for SC-008; `gh secret delete AZURE_CREDENTIALS --env dev` then `gh secret set AZURE_CREDENTIALS --env dev --body "$(cat azure-credentials-dev.json)"` for the FR-016 test.
      ✅ Success: All eight smoke tests pass; one row per test is recorded in the PR description with the literal command run, the observed output, and a green/red status. The FR-016 smoke test confirms the failure message contains both `AZURE_CREDENTIALS` and `dev`; the secret is restored after the test.

- [ ] T030 Update the repository `README.md` (and any other developer-facing onboarding docs) to point at `specs\031-simplify-cicd-pipeline\quickstart.md` as the authoritative CI/CD onboarding runbook. Remove or update any references to the deleted spec-029 workflows (`change-freeze`, `evidence-pack`, `dev-key-issue`, `emergency-hotfix`, `posture-exception-sweep`, the `_reusable/` workflows, `tools/pipeline`).
      🧑 Agent: `product-owner-ba` (docs ownership) + `infrastructure-devops` (technical accuracy)
      🔧 Tools: `grep -rln "spec029\\|change-freeze\\|evidence-pack\\|dev-key-issue\\|emergency-hotfix\\|posture-exception\\|_reusable\\|tools/pipeline" *.md docs/` to find references; `edit` to update.
      ✅ Success: `grep` for the same patterns across `*.md` and `docs/` returns zero matches outside `specs/029-*` and `specs/031-*`. README links to `specs/031-simplify-cicd-pipeline/quickstart.md`.

---

## Dependencies & Execution Order

### Phase dependencies (top-down)

```text
Phase 1 (Setup)
    ↓
Phase 2 (Foundational — spec-029 deletion) ⚠️ BLOCKS the verification tasks in US1/US2/US4
    ↓
Phase 3 (US1)  ┐
Phase 4 (US2)  ├─ Two P1 stories — workflow modifications can interleave (different files
Phase 5 (US3)  │  for T013/T018; T014 and T017 both touch cd.yml so serialise those two)
Phase 6 (US4)  │  ↓
Phase 7 (US5)  ┘
    ↓
Phase 8 (Polish — review + recommendations + smoke tests)
```

### Specific intra-phase orderings

- **T009 → T009a** (T009a edits a comment that names files T009 deletes; sequencing is cosmetic but T009a should commit alongside or just after T009 to keep the tree consistent).
- **T011 → T011a** are mutually independent — both are housekeeping items in Phase 2 that touch different files (`infra\` vs `.github\CODEOWNERS`); both must complete before T012's verification grep.
- **T012a depends on T001** (the dev parameter file must exist before What-If can be run against it). T012a should also follow T009 (so the Bicep template is free of references to deleted IDENTITY.md).
- **T014 → T017** (both edit `cd.yml`; T014 changes structure first, T017 swaps auth on the now-correct file). Cannot be parallelised.
- **T013, T018, T019, T020 are mutually independent** (different files) and can all be done in parallel by one or more developers.
- **T015, T016, T021, T022 are operator actions**; they can be done in any order *after* T013–T020 are merged, but `cd` will not succeed end-to-end until all four are complete.
- **T024 (US3 verification) requires T018 to be done** (since T018 also touches `drift-detection.yml`).
- **T025 (US4 verification) requires Phase 2 fully done.**
- **T026 (US5 fill-in) requires T002 done.**
- **T029 (smoke tests) requires every preceding task done** — it is the final acceptance gate. The FR-016 sub-test additionally requires T022 (secret exists to be temporarily cleared).

### User-story dependency matrix

| Story | Depends on | Independently testable? | Notes |
|---|---|---|---|
| US1 | Phase 2 (deletion) for clean grep; **US2 operator setup** for end-to-end run | ⚠️ Implementation independent; runtime test requires US2 secrets | Workflow YAML can be merged before US2 secrets are set |
| US2 | Phase 2 (deletion); US1 cd.yml structure (for T017's edits to land cleanly) | ⚠️ Implementation independent; runtime test requires US1 branches | — |
| US3 | T018 (touches drift-detection.yml) | ✅ Yes | Single verification + comment annotation |
| US4 | Phase 2 deletions | ✅ Yes | Verification-only |
| US5 | T002 (ADR file created in Phase 1) | ✅ Yes | Single field fill-in |

### Parallel opportunities

- **Phase 1**: T001 ‖ T002 (different files).
- **Phase 2**: T003 ‖ T004 ‖ T005 ‖ T006 ‖ T007 ‖ T008 ‖ T009 ‖ T010 ‖ T011 (all different paths). T012 must wait for all.
- **Phase 3 / Phase 4**: T013, T018, T019, T020 can all be done in parallel (different workflow files); T014 and T017 must serialise on `cd.yml`.
- **Operator actions** (T015, T016, T021, T022) parallelise across operators with the right access.
- **Phase 8**: T027 ‖ T028 (different artefacts: review notes vs recommendations).

---

## Parallel example: Phase 2 (single developer or single agent)

```bash
# All 9 deletion tasks can be batched into one PowerShell session:
Remove-Item C:\code\ama\.github\workflows\spec029-*.yml -Force                       # T003
Remove-Item C:\code\ama\.github\workflows\_reusable -Recurse -Force                  # T004
Remove-Item C:\code\ama\.github\workflows\change-freeze.yml,                         `
            C:\code\ama\.github\workflows\posture-exception-sweep.yml,               `
            C:\code\ama\.github\workflows\evidence-pack.yml,                         `
            C:\code\ama\.github\workflows\dev-key-issue.yml,                         `
            C:\code\ama\.github\workflows\emergency-hotfix.yml -Force                # T005
Remove-Item C:\code\ama\.github\actions\install-opa,                                 `
            C:\code\ama\.github\actions\setup-cosign-syft,                           `
            C:\code\ama\.github\actions\setup-oidc-azure -Recurse -Force             # T006
Remove-Item C:\code\ama\.github\state\freeze.json -Force                             # T007
Remove-Item C:\code\ama\tools\pipeline -Recurse -Force                               # T008
Remove-Item C:\code\ama\infra\IDENTITY.md,                                           `
            C:\code\ama\infra\policy\posture-matrix.yaml,                            `
            C:\code\ama\infra\policy\posture-exceptions.yaml,                        `
            C:\code\ama\infra\policy\foundry-carveout.yaml -Force                    # T009 (1/2)
Remove-Item C:\code\ama\infra\policy\rego -Recurse -Force                            # T009 (2/2)
Remove-Item C:\code\ama\scripts\spec029-bootstrap -Recurse -Force                    # T010
Remove-Item C:\code\ama\infra\main.parameters.development.json -Force                # T011
git add -A && git commit -m "chore(spec-031): delete spec-029 footprint"
```

T012 then runs the verification grep to close the foundational phase.

---

## Implementation strategy

### MVP first (US1 + US2 — both P1)

Both P1 stories are required for any deployment to succeed. The minimum shippable increment is:

1. Phase 1 (T001, T002).
2. Phase 2 (T003–T012) — the deletion baseline.
3. Phase 3 + Phase 4 implementation tasks (T013, T014, T017–T020) — workflow modifications.
4. Operator setup (T015, T016, T021, T022) — branches, protection, SPNs, secrets.
5. Smoke test the dev → staging → production push sequence.

At this point the simplified pipeline is live. US3, US4, US5 (P2/P3) and the FR-019/020 review can land in a follow-up PR if time-pressed; however, since US3/US4/US5 are mostly verification + a single edit each, they should land in the same PR.

### Incremental delivery

If a multi-PR strategy is preferred:

- **PR 1** (foundational): Phase 1 + Phase 2 + ADR commit. Pipeline still works exactly as today (we only deleted abandoned spec-029 surface).
- **PR 2** (US1 + US2): Workflow modifications + operator setup. Pipeline now branch-based.
- **PR 3** (US3 + US4 + US5 + Polish): Verification, review, recommendations.

### Parallel team strategy

With 2–3 developers:

- **Dev A** (devops lead): T001, T013, T014, T017, T018, T024.
- **Dev B** (devops + data): T019, T020, T027.
- **Dev C** (security + compliance): T002, T021, T022, T026, T028 (Rec A/B sign-off).
- All collaborate on Phase 2 deletions (T003–T011) — easy to split across the 9 tasks.
- T012, T023, T025, T029 are gating verification tasks held by `principal-engineer`.

---

## Notes

- **Tests not generated**: there is no existing CI/CD-workflow test framework in this repo (no `tests/workflows/` or equivalent). All verification is done via `grep`, `actionlint`, `Test-Path`, and the runtime smoke tests in `quickstart.md`.
- **`[P]` semantics**: tasks marked `[P]` touch different files and have no ordering dep within the phase. T014 and T017 both touch `cd.yml` and are intentionally NOT marked `[P]`.
- **Operator actions** (T015, T016, T021, T022, T026) are documented as operator-facing in `quickstart.md`; they are listed here so the task tracker captures the full delivery scope, but they execute outside the PR.
- **Constitution Check**: re-validated after Phase 1 design. Single documented regression (loss of automated Foundry-carve-out enforcement) is captured in the ADR (T002) and surfaced as Rec A in T028.
- **Commit cadence**: commit after each task or after each phase boundary. Phase 2 may be one commit (`chore(spec-031): delete spec-029 footprint`); Phase 3/4 should be one commit per workflow file modified.
- **PR description checklist**: include the eight smoke-test results from T029 and the three recommendation responses from T028.
