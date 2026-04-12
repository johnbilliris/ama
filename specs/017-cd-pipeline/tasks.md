# Tasks: CD Pipeline with Staging Environment

**Input**: Design documents from `/specs/017-cd-pipeline/` and `/specs/feature/017-cd-pipeline/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Included — the user explicitly requested tests for workflows and scripts.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Workflows**: `.github/workflows/`
- **Scripts**: `scripts/`
- **Infrastructure parameters**: `infra/`
- **Tests**: `tests/devops/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — create directory structure and shared configuration files required by all user stories.

- [ ] T001 Create test directory structure at `tests/devops/` with `__init__.py` and `conftest.py` for pipeline test fixtures
- [ ] T002 [P] Create staging environment Bicep parameter file at `infra/main.parameters.staging.json` with `environmentName=drh-staging`, `location=australiaeast`, `principalType=ServicePrincipal`, empty `developerIpAddress`, and default action group values
- [ ] T003 [P] Create production environment Bicep parameter file at `infra/main.parameters.production.json` with `environmentName=drh-production`, `location=australiaeast`, `principalType=ServicePrincipal`, empty `developerIpAddress`, and production-appropriate `actionGroupEmail`/`actionGroupWebhook` values

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core rollback script that MUST be complete before the CD workflow can implement rollback logic (US1 depends on it for health-check-failure handling, US3 depends on it entirely).

**⚠️ CRITICAL**: The CD workflow references `scripts/rollback.sh` — it must exist before the workflow can function.

- [ ] T004 Create rollback script at `scripts/rollback.sh` implementing the full contract from `contracts/rollback-script.md`: argument parsing for `--environment`, `--resource-group`, `--revision-api`, `--revision-agents`, `--revision-ingestion`, `--revision-web`, and `--dry-run` flags
- [ ] T005 Implement input validation in `scripts/rollback.sh`: check `az` CLI availability (exit 3), validate `--environment` is `staging` or `production` (exit 2), validate `--resource-group` is non-empty (exit 2)
- [ ] T006 Implement revision discovery in `scripts/rollback.sh`: for Container Apps (`api`, `agents`, `ingestion`) use `az containerapp revision list` to find previous active revision; for App Service (`web`) use `az webapp deployment list` to find previous deployment
- [ ] T007 Implement rollback execution in `scripts/rollback.sh`: for Container Apps use `az containerapp revision activate` (previous) and `az containerapp revision deactivate` (current); for App Service use `az webapp deployment source config-zip` to redeploy previous artifact
- [ ] T008 Implement post-rollback health checks in `scripts/rollback.sh`: check all 4 services (`api` at `/api/health`, `agents` at `/health`, `ingestion` at `/health`, `web` at `/`) with 30s timeout, 3 retries, 10s intervals using `curl`; exit 0 on all pass, exit 4 on any failure
- [ ] T009 Implement `--dry-run` mode in `scripts/rollback.sh`: print all planned rollback actions with `[ROLLBACK] [DRY-RUN]` prefix without executing any Azure CLI commands
- [ ] T010 Implement structured output logging in `scripts/rollback.sh`: `[ROLLBACK]` prefixed stdout messages per contract format, `[ROLLBACK] ❌` prefixed stderr error messages, final summary line with ✅ or ❌ status
- [ ] T011 Make `scripts/rollback.sh` executable and add shellcheck-compliant shebang `#!/usr/bin/env bash` with `set -euo pipefail`

**Checkpoint**: Rollback script is complete, executable, and ready for integration with CD workflow

---

## Phase 3: User Story 1 — Automated Staging Deployment After CI (Priority: P1) 🎯 MVP + User Story 4 — Environment-Specific Configuration (Priority: P1) 🎯 MVP

**Goal**: Changes merged to main are automatically deployed to staging after CI passes. Each environment uses isolated configuration (resource groups, parameters).

**Independent Test**: Merge a change to main → CI passes → CD triggers → all 4 services deployed to staging → health endpoints return healthy responses.

**Why combined**: US1 (staging deployment) and US4 (environment config) are both P1 and tightly coupled — staging deployment cannot function without environment-specific parameters. They share the same deliverable file (`.github/workflows/cd.yml`).

### Tests for User Stories 1 & 4 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T012 [P] [US1] Create workflow syntax validation test at `tests/devops/test_cd_workflow_syntax.py` that validates `.github/workflows/cd.yml` is valid YAML with required top-level keys (`name`, `on`, `permissions`, `jobs`), correct `workflow_run` trigger referencing `["ci"]`, and `branches: [main]` filter
- [ ] T013 [P] [US1] Create deployment job structure test at `tests/devops/test_cd_workflow_jobs.py` that validates `deploy-staging` job exists with `environment: staging`, `concurrency` group `deploy-staging` with `cancel-in-progress: false`, and the `if` condition checking `github.event.workflow_run.conclusion == 'success'`
- [ ] T014 [P] [US4] Create parameter file validation test at `tests/devops/test_parameter_files.py` that validates both `infra/main.parameters.staging.json` and `infra/main.parameters.production.json` match the `$schema` from `infra/main.parameters.json`, contain all required parameters (`environmentName`, `location`, `principalType`, `developerIpAddress`), use distinct `environmentName` values, set `principalType` to `ServicePrincipal`, and assert `location` is one of `australiaeast` or `australiasoutheast` (FR-009 region compliance)
- [ ] T015 [P] [US4] Create environment isolation test at `tests/devops/test_environment_isolation.py` that validates staging and production parameter files have different `environmentName` values, both use `australiaeast` location, and neither references the other's resource group name pattern

### Implementation for User Stories 1 & 4

- [ ] T016 [US1] Create CD workflow file at `.github/workflows/cd.yml` with workflow name `cd`, `workflow_run` trigger on `["ci"]` completed on `main` branch, and top-level `permissions` block (`id-token: write`, `contents: read`, `issues: write`, `actions: read`)
- [ ] T017 [US1] Implement `deploy-staging` job in `.github/workflows/cd.yml`: `runs-on: ubuntu-latest`, `environment: staging`, `concurrency: { group: deploy-staging, cancel-in-progress: false }`, `if: ${{ github.event.workflow_run.conclusion == 'success' }}`
- [ ] T018 [US1] Add checkout and Azure authentication steps to `deploy-staging` job in `.github/workflows/cd.yml`: `actions/checkout@v4`, `azure/login@v2` with OIDC using `vars.AZURE_CLIENT_ID`, `vars.AZURE_TENANT_ID`, `vars.AZURE_SUBSCRIPTION_ID`
- [ ] T019 [US1] Add `azd` installation and environment configuration steps to `deploy-staging` job in `.github/workflows/cd.yml`: `Azure/setup-azd@v2`, resource group creation via `az group create --name rg-drh-staging --location australiaeast`, `azd env new drh-staging`, set `AZURE_ENV_NAME`, `AZURE_LOCATION`, `AZURE_SUBSCRIPTION_ID`
- [ ] T020 [US1] Add infrastructure provisioning and service deployment steps to `deploy-staging` job in `.github/workflows/cd.yml`: `azd provision --no-prompt` and `azd deploy --no-prompt`
- [ ] T021 [US1] Add parallel health check step to `deploy-staging` job in `.github/workflows/cd.yml`: bash script checking all 4 services in parallel (`api` at `/api/health`, `agents` at `/health`, `ingestion` at `/health`, `web` at `/`) with 30s timeout per service, 3 retries, 10s intervals, total window ≤2 minutes
- [ ] T022 [US1] Add known-good revision recording step to `deploy-staging` job in `.github/workflows/cd.yml`: on health check success, capture Container Apps revision names via `az containerapp show` and App Service deployment ID, set as job outputs (`revision-api`, `revision-agents`, `revision-ingestion`, `revision-web`, `deployment-status`)
- [ ] T023 [US1] Add rollback-on-failure step to `deploy-staging` job in `.github/workflows/cd.yml`: on health check failure, execute `scripts/rollback.sh --environment staging --resource-group rg-drh-staging`; on rollback failure (exit 4), create GitHub Issue with `critical` label via `gh issue create`. Acceptance: verify rollback step chains correctly: health check failure → rollback.sh → critical failure issue creation
- [ ] T024 [US1] Add `deployment-status` output to `deploy-staging` job in `.github/workflows/cd.yml` reporting `success`, `rolled-back`, or `critical-failure`

**Checkpoint**: Staging deployment pipeline is fully functional end-to-end. Merging to main triggers CI → CD → staging deploy → health checks → known-good recording or rollback.

---

## Phase 4: User Story 2 — Deployment Gates Between Staging and Production (Priority: P2)

**Goal**: Automated quality/security gates run after staging deployment; manual approval gate pauses before production deployment; production deployment mirrors staging with its own environment config.

**Independent Test**: Deploy a change to staging → gates run (ruff check, pip-audit, health verification) → if gates pass, pipeline pauses for manual approval → on approval, production deploys.

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T025 [P] [US2] Create deployment gates job structure test at `tests/devops/test_cd_gates.py` that validates `deployment-gates` job exists in `.github/workflows/cd.yml` with `needs: deploy-staging`, condition checking `deployment-status == 'success'`, and steps for `ruff check` and `pip-audit`
- [ ] T026 [P] [US2] Create production job structure test at `tests/devops/test_cd_production.py` that validates `deploy-production` job exists in `.github/workflows/cd.yml` with `needs: deployment-gates`, `environment: production`, `concurrency: { group: deploy-production, cancel-in-progress: false }`, and condition checking `gates-passed == 'true'`

### Implementation for User Story 2

- [ ] T027 [US2] Implement `deployment-gates` job in `.github/workflows/cd.yml`: `runs-on: ubuntu-latest`, `needs: deploy-staging`, `if: needs.deploy-staging.outputs.deployment-status == 'success'`
- [ ] T028 [US2] Add checkout, Python setup, and security scan steps to `deployment-gates` job in `.github/workflows/cd.yml`: `actions/checkout@v4`, `actions/setup-python@v5` with Python 3.12, `ruff check apps tests packages`, `pip install -e . && pip install pip-audit && pip-audit` (install project deps first so pip-audit scans the full dependency tree)
- [ ] T029 [US2] Add gate summary reporting step to `deployment-gates` job in `.github/workflows/cd.yml`: generate job summary with gate pass/fail results, set `gates-passed` and `gate-failures` as job outputs
- [ ] T030 [US2] Implement `deploy-production` job in `.github/workflows/cd.yml`: `runs-on: ubuntu-latest`, `environment: production`, `needs: deployment-gates`, `if: needs.deployment-gates.outputs.gates-passed == 'true'`, `concurrency: { group: deploy-production, cancel-in-progress: false }`
- [ ] T031 [US2] Add checkout, Azure login, `azd` setup, resource group creation, and environment configuration steps to `deploy-production` job in `.github/workflows/cd.yml`: same pattern as staging but with `rg-drh-production`, `AZURE_ENV_NAME=drh-production`, `australiaeast`
- [ ] T032 [US2] Add infrastructure provisioning, service deployment, and health check steps to `deploy-production` job in `.github/workflows/cd.yml`: `azd provision --no-prompt`, `azd deploy --no-prompt`, same parallel health check pattern as staging
- [ ] T033 [US2] Add known-good revision recording step to `deploy-production` job in `.github/workflows/cd.yml`: capture and record revision IDs on health check success, same pattern as staging

**Checkpoint**: Full pipeline flow works: staging deploy → automated gates → manual approval → production deploy. Gate failures block production.

---

## Phase 5: User Story 3 — Automated Rollback on Staging Health Failure (Priority: P2)

**Goal**: The pipeline automatically rolls back all services to the previous known-good revision when any health check fails after staging deployment. This phase validates rollback integration (the rollback script itself was built in Phase 2).

**Independent Test**: Deploy a version with a deliberately broken health endpoint → health checks fail → rollback triggers → previous revision restored → health checks pass on restored revision.

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T034 [P] [US3] Create rollback script unit tests at `tests/devops/test_rollback_script.py`: validate argument parsing (all flags recognized, invalid args return exit code 2), `--dry-run` produces output without Azure CLI calls, invalid `--environment` value returns exit code 2, missing `--resource-group` returns exit code 2
- [ ] T035 [P] [US3] Create rollback integration test at `tests/devops/test_rollback_integration.py`: validate rollback step in `.github/workflows/cd.yml` is conditional on health check failure (`if: failure()`), invokes `scripts/rollback.sh` with correct `--environment` and `--resource-group` arguments, and critical failure step creates a GitHub Issue on rollback exit code 4

### Implementation for User Story 3

- [ ] T036 [US3] Add first-run bootstrap handling to rollback script: when no previous revision exists (first deployment), skip rollback with informational message and exit code 0; add test case for this scenario in `tests/devops/test_rollback_script.py`
- [ ] T037 [US3] Add rollback notification step to `deploy-staging` job in `.github/workflows/cd.yml`: on successful rollback (exit 0), add job summary reporting which services were rolled back and to which revision, set `deployment-status` to `rolled-back`
- [ ] T038 [US3] Add critical failure notification step to `deploy-staging` job in `.github/workflows/cd.yml`: on rollback failure (exit 4), create GitHub Issue via `gh issue create --title "CRITICAL: Rollback failed in staging" --body "..." --label critical` with details of failing services and manual intervention guidance

**Checkpoint**: Rollback automation is fully integrated. Health check failures trigger automatic rollback, and rollback failures trigger critical alerts.

---

## Phase 6: User Story 5 — Infrastructure Drift Detection (Priority: P3)

**Goal**: A weekly scheduled workflow compares live Azure infrastructure against IaC definitions and reports drift as GitHub Issues.

**Independent Test**: Manually modify an Azure resource property outside IaC → trigger drift-detection workflow → GitHub Issue created with `infrastructure-drift` label listing the drifted property.

### Tests for User Story 5 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T039 [P] [US5] Create drift detection workflow syntax test at `tests/devops/test_drift_workflow_syntax.py` that validates `.github/workflows/drift-detection.yml` is valid YAML with correct `schedule` cron (`0 16 * * 6`), `workflow_dispatch` trigger, and required `permissions` (`id-token: write`, `contents: read`, `issues: write`)
- [ ] T040 [P] [US5] Create drift detection job structure test at `tests/devops/test_drift_workflow_jobs.py` that validates `detect-drift` job uses matrix strategy over `[staging, production]`, includes `az deployment group what-if` command with `--result-format FullResourcePayloads`, and conditionally creates GitHub Issues via `gh issue create`

### Implementation for User Story 5

- [ ] T041 [US5] Create drift detection workflow file at `.github/workflows/drift-detection.yml` with workflow name `drift-detection`, `schedule` trigger (`cron: "0 16 * * 6"` = Saturday 16:00 UTC / Sunday 02:00 AEST), `workflow_dispatch` for manual runs, and `permissions` block (`id-token: write`, `contents: read`, `issues: write`)
- [ ] T042 [US5] Implement `detect-drift` job in `.github/workflows/drift-detection.yml`: `runs-on: ubuntu-latest`, matrix strategy over `[staging, production]`, checkout, Azure login via OIDC (same auth pattern as CD workflow)
- [ ] T043 [US5] Add `az deployment group what-if` step to `detect-drift` job in `.github/workflows/drift-detection.yml`: execute against `rg-drh-${{ matrix.environment }}` with `infra/main.bicep` and `infra/main.parameters.${{ matrix.environment }}.json`, use `--result-format FullResourcePayloads --no-pretty-print -o json`
- [ ] T044 [US5] Add drift result parsing step to `detect-drift` job in `.github/workflows/drift-detection.yml`: filter out false-positive properties (`provisioningState`, `etag`, `identity.principalId`, timestamps, `uniqueId`, `systemData`, `hostNames`, `defaultHostName`, `outboundIpAddresses`) using `jq`, classify remaining changes as `Create`, `Delete`, or `Modify`
- [ ] T045 [US5] Add drift report generation step to `detect-drift` job in `.github/workflows/drift-detection.yml`: format drift findings into markdown table per contract (Resource, Type, Change, Property, Expected, Actual), include summary metrics (resources with drift, properties modified, resources to create/delete)
- [ ] T046 [US5] Add conditional GitHub Issue creation step to `detect-drift` job in `.github/workflows/drift-detection.yml`: if drift detected, create issue via `gh issue create --title "Infrastructure drift detected: ${{ matrix.environment }} ($(date +%Y-%m-%d))" --body "${DRIFT_REPORT}" --label "infrastructure-drift"`; if no drift, log clean status in job summary
- [ ] T047 [US5] Add error handling to `detect-drift` job in `.github/workflows/drift-detection.yml`: handle Azure login failure (fail with auth error, no false clean report), resource group not found (report environment not provisioned), `what-if` command failure (surface error in summary), GitHub Issue API rate limit (fail with drift in logs)

**Checkpoint**: Drift detection runs on schedule and on-demand. Drift findings appear as labeled GitHub Issues with property-level details.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories — validation, documentation, and hardening.

- [ ] T048 [P] Add `timeout-minutes: 20` to `deploy-staging` and `deploy-production` jobs in `.github/workflows/cd.yml` to enforce the 15-minute deployment target (SC-001) with buffer
- [ ] T049 [P] Add `timeout-minutes: 30` to `detect-drift` job in `.github/workflows/drift-detection.yml` for what-if analysis timeout
- [ ] T050 [P] Add workflow-level notification step to `.github/workflows/cd.yml` that creates a GitHub deployment status (`success`/`failure`) for staging and production jobs for commit status tracking (FR-007)
- [ ] T051 Run `shellcheck scripts/rollback.sh` and fix all warnings/errors for shell script quality
- [ ] T052 Validate all parameter files against `infra/main.bicep` by running `az bicep build --file infra/main.bicep` and `az deployment group validate` with each parameter file (dry-run)
- [ ] T053 Run `quickstart.md` verification: execute the verification steps from `specs/feature/017-cd-pipeline/quickstart.md` to confirm pipeline flow, health check format, rollback dry-run, and drift detection manual trigger all work
- [ ] T054 [P] Run all tests in `tests/devops/` and confirm they pass against the implemented workflows and scripts

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (parameter files must exist for rollback context) — BLOCKS US1/US3
- **US1+US4 (Phase 3)**: Depends on Phase 2 (rollback script must exist) — this is the MVP
- **US2 (Phase 4)**: Depends on Phase 3 (staging deployment must exist for gates and production to extend)
- **US3 (Phase 5)**: Depends on Phase 3 (rollback integration validates what Phase 2 built + Phase 3 wired)
- **US5 (Phase 6)**: Depends on Phase 1 only (parameter files) — can start in parallel with Phase 3
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1+US4 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **US2 (P2)**: Depends on US1+US4 — gates and production job extend the CD workflow created in US1
- **US3 (P2)**: Depends on US1+US4 — validates rollback integration within the staging deployment job
- **US5 (P3)**: Independent — can start after Phase 1 (parameter files); separate workflow file

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Workflow structure before step implementation
- Core steps before error handling steps
- Story complete before moving to next priority

### Parallel Opportunities

- T002 and T003 can run in parallel (different parameter files)
- T012, T013, T014, T015 can run in parallel (different test files)
- T025 and T026 can run in parallel (different test files)
- T034 and T035 can run in parallel (different test files)
- T039 and T040 can run in parallel (different test files)
- **US5 (Phase 6) can run in parallel with Phases 3–5** (separate workflow file, no shared state)
- T048, T049, T050, T054 can run in parallel (different files or independent operations)

---

## Parallel Example: User Story 1+4 (Phase 3)

```bash
# Launch all tests for US1+US4 together (4 parallel test files):
Task: T012 "Workflow syntax validation test in tests/devops/test_cd_workflow_syntax.py"
Task: T013 "Deployment job structure test in tests/devops/test_cd_workflow_jobs.py"
Task: T014 "Parameter file validation test in tests/devops/test_parameter_files.py"
Task: T015 "Environment isolation test in tests/devops/test_environment_isolation.py"

# Then implement sequentially (each step builds on previous):
Task: T016 → T017 → T018 → T019 → T020 → T021 → T022 → T023 → T024
```

## Parallel Example: US5 alongside US2/US3

```bash
# US5 is a separate workflow file — can be developed in parallel with US2/US3:
Developer A: Phase 4 (US2 gates + production) — works on .github/workflows/cd.yml
Developer B: Phase 6 (US5 drift detection) — works on .github/workflows/drift-detection.yml
# No file conflicts between these two streams
```

---

## Implementation Strategy

### MVP First (User Stories 1+4 Only)

1. Complete Phase 1: Setup (parameter files)
2. Complete Phase 2: Foundational (rollback script)
3. Complete Phase 3: User Stories 1+4 (staging deployment + environment config)
4. **STOP and VALIDATE**: Merge to main → CI → CD → staging deployed with health checks
5. Deploy/demo if ready — staging environment is operational

### Incremental Delivery

1. Complete Setup + Foundational → Rollback script ready, parameter files ready
2. Add US1+US4 → Test staging deployment end-to-end → Deploy (MVP!)
3. Add US2 → Gates + production deployment → Full pipeline
4. Add US3 → Rollback integration validation → Resilient pipeline
5. Add US5 → Drift detection → Governance layer
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1+US4 (staging deploy + env config) → then US2 (gates + production)
   - Developer B: US5 (drift detection — independent workflow)
3. After US1+US4 merges: Developer A → US3 (rollback integration)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- CI workflow (`ci.yml`) is NEVER modified — CD is additive only (FR-008)
- All Azure resources in Australian regions only (FR-009)
- No stored secrets — OIDC federation only (FR-014)
