# Research: CD Pipeline with Staging Environment

**Feature**: 017-cd-pipeline
**Date**: 2025-07-14
**Status**: Complete

---

## R-001: GitHub Actions `workflow_run` Trigger Pattern

**Question**: How should the CD pipeline trigger after CI completes on main?

**Decision**: Use `workflow_run` event with `types: [completed]` and `branches: [main]` filter, plus a job-level `if` condition checking `github.event.workflow_run.conclusion == 'success'`.

**Rationale**: This is the only GitHub Actions mechanism that chains workflows without modifying the upstream CI workflow. The `workflow_run` event fires on any conclusion (success, failure, cancelled), so the `if` guard is essential to prevent deploying after failed CI.

**Alternatives Considered**:
- `workflow_call` (reusable workflow): Rejected — would require modifying `ci.yml` to call the CD workflow, violating FR-008.
- Push trigger with path filters: Rejected — cannot guarantee CI has passed; would create a race condition.
- Repository dispatch: Rejected — adds unnecessary complexity; `workflow_run` is the native solution.

**Key Finding**: The existing CI workflow is named `ci` (line 1 of `.github/workflows/ci.yml`). The `workflow_run.workflows` filter must reference this exact name string `["ci"]`.

---

## R-002: Azure Developer CLI (`azd`) in GitHub Actions

**Question**: How should `azd` be used for provisioning and deployment in the CD pipeline?

**Decision**: Use `azd provision` for infrastructure and `azd deploy` for services, with environment-specific parameter files selected via `AZURE_ENV_NAME` environment variable.

**Rationale**: The existing `azure.yaml` already configures `azd` with Bicep provider and 4 service definitions. `azd` handles Container Apps revision management and App Service zip deploy natively based on host type.

**Alternatives Considered**:
- Direct `az` CLI commands for each service: Rejected — would duplicate logic already in `azure.yaml` and require manual Container Apps revision management.
- Terraform: Rejected — project already uses Bicep; switching would violate existing IaC investment.
- ARM template deployment: Rejected — Bicep is the higher-level abstraction already in use.

**Key Findings**:
- `azd` reads `infra/main.parameters.json` by default but can be directed to environment-specific files via `azd env set` and the `${AZURE_ENV_NAME}` variable substitution pattern.
- Environment-specific parameter files (`main.parameters.staging.json`, `main.parameters.production.json`) use the same `$schema` and variable-substitution pattern as the base file.
- `azd` in CI mode (`azd provision --no-prompt` / `azd deploy --no-prompt`) suppresses interactive prompts.
- Container image parameters (`apiImage`, `agentsImage`, `ingestionImage`) are set by `azd deploy` automatically — no manual override needed.
- The pipeline must create the resource group before `azd provision` since `main.bicep` uses `targetScope = 'resourceGroup'`.

---

## R-003: Workload Identity Federation (OIDC) for Azure Authentication

**Question**: How should the pipeline authenticate to Azure without stored secrets?

**Decision**: Use `azure/login@v2` action with workload identity federation (OIDC). Store only `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and `AZURE_SUBSCRIPTION_ID` as GitHub repository variables (not secrets). Require `permissions: id-token: write` on jobs.

**Rationale**: OIDC federation eliminates secret rotation burden and aligns with Constitution Principle IV (managed identity). GitHub Actions natively supports OIDC token generation.

**Alternatives Considered**:
- Service principal with client secret: Rejected — violates FR-014 and Constitution Principle IV; requires secret rotation.
- Azure CLI with device code flow: Rejected — not suitable for CI/CD automation.
- Managed identity on self-hosted runner: Rejected — project uses GitHub-hosted runners (`ubuntu-latest`).

**Key Findings**:
- Federated credential must be configured in Entra ID (Azure AD) with the GitHub issuer URL, organization, repository, and branch filter.
- Two separate federated credentials may be needed: one for `main` branch (CD), one for `environment:staging` and `environment:production` (if using GitHub environments).
- The `azure/login@v2` action handles the OIDC token exchange transparently.

---

## R-004: Health Check Strategy for 4 Services

**Question**: How should health checks be structured for the 4 services with different hosts?

**Decision**: Use `curl` with retry logic in bash. Check Container Apps services via their FQDN endpoints and App Service via its default domain. Run checks in parallel where possible, with serial fallback for timeout budget.

**Rationale**: All 4 services have confirmed health endpoints (verified in codebase): `api` → `/api/health`, `agents` → `/health`, `ingestion` → `/health`, `web` → `/` (HTTP 200). Using `curl` keeps the pipeline dependency-free.

**Alternatives Considered**:
- Azure Container Apps readiness probes only: Rejected — don't cover cross-service validation or App Service `web`.
- Custom health check action from marketplace: Rejected — unnecessary dependency; `curl` with retries is sufficient.
- `wget` or `httpie`: Rejected — `curl` is universally available on `ubuntu-latest`.

**Key Findings**:
- FR-010 arithmetic conflict: 4 services × 30s timeout × 3 retries × 10s intervals = worst case ~440s (7.3 min), but FR-010 caps total at 2 minutes. **Resolution**: Run health checks in parallel (all 4 simultaneously). Each service independently retries up to 3 times. Parallel execution means worst case is ~110s (30s + 10s + 30s + 10s + 30s) for a single service, well within the 2-minute window.
- Container Apps FQDN is available as `azd` deployment output or via `az containerapp show`.
- App Service URL follows pattern `https://{app-name}.azurewebsites.net`.

---

## R-005: Rollback Strategy for Container Apps and App Service

**Question**: How should rollback work for the two different hosting types?

**Decision**: Implement `scripts/rollback.sh` that:
1. For Container Apps (api, agents, ingestion): Reactivate the previous revision via `az containerapp revision activate` and deactivate the current one.
2. For App Service (web): Redeploy the previous known-good deployment via `az webapp deployment source config-zip` or slot swap if available.

**Rationale**: Container Apps natively supports multi-revision mode, making rollback a revision activation. App Service requires redeployment from the last known-good artifact.

**Alternatives Considered**:
- `azd` rollback (not available): `azd` has no native rollback command.
- Full re-provision from previous commit: Rejected — too slow for the 5-minute rollback target (SC-003).
- Blue/green with deployment slots: Rejected — adds complexity; Container Apps revisions and simple redeployment are sufficient for the staging environment.

**Key Findings**:
- Known-good revision tracking: Store the revision name/ID as a GitHub Actions artifact or environment variable after successful deployment. The rollback script reads this to know the target.
- The rollback script should accept parameters: `--environment`, `--resource-group`, `--services` (all or specific).
- After rollback, re-run health checks to verify the restored revision is healthy.
- If rollback itself fails health checks → halt and report critical failure (FR-012).

---

## R-006: Infrastructure Drift Detection via `az deployment group what-if`

**Question**: How should drift detection compare live Azure state against IaC?

**Decision**: Use `az deployment group what-if` with `--result-format FullResourcePayloads` and `-o json` to get machine-parseable output. Filter out known false-positive fields (system-managed properties). Report findings as a GitHub Issue with the `infrastructure-drift` label.

**Rationale**: `what-if` is the native ARM/Bicep mechanism for comparing desired vs. actual state. It runs server-side and handles all resource types defined in the Bicep template.

**Alternatives Considered**:
- Azure Resource Graph queries: Rejected — requires building comparison logic from scratch; doesn't understand Bicep template intent.
- `azd provision --preview`: Rejected — less granular output than `what-if`; designed for preview, not drift detection.
- Third-party tools (Checkov, Bridgecrew): Rejected — adds external dependency; `what-if` is sufficient for property-level drift.

**Key Findings**:
- False positive mitigation: Filter out `provisioningState`, `etag`, `identity.principalId` (system-assigned), timestamps, `uniqueId`, and other runtime-generated properties.
- Schedule: `cron: "0 16 * * 6"` (Saturday 16:00 UTC = Sunday 02:00 AEST). Note: cron doesn't account for daylight saving; AEDT would be Sunday 03:00 local, which is acceptable.
- GitHub Issue format: Title includes environment and date; body has summary table of drifted resources with property-level differences.
- The workflow needs the same OIDC authentication as the CD pipeline.

---

## R-007: Environment-Specific Parameter Files

**Question**: How should staging and production parameter files differ from the base?

**Decision**: Create `infra/main.parameters.staging.json` and `infra/main.parameters.production.json` following the same `$schema` and variable-substitution pattern as `main.parameters.json`. Each file provides environment-specific values for `environmentName`, `location`, and operational parameters.

**Rationale**: The existing `main.parameters.json` uses `${AZURE_ENV_NAME}` substitution — the environment-specific files follow the same pattern but with distinct env names (e.g., `drh-staging`, `drh-production`).

**Key Findings**:
- Both files must provide all parameters that `main.bicep` expects (or rely on defaults).
- Staging uses smaller/cheaper SKUs where applicable (cost optimization per CHK066).
- Production adds `actionGroupEmail` and `actionGroupWebhook` with real values.
- `principalType` changes to `ServicePrincipal` for pipeline-deployed environments (vs. `User` for local dev).
- `developerIpAddress` is empty for pipeline environments (no developer IP needed).

---

## R-008: Concurrency Control and Queue Behavior

**Question**: How should concurrent deployments be handled?

**Decision**: Use GitHub Actions `concurrency` groups with `cancel-in-progress: false` per environment. Pattern: `concurrency: { group: deploy-staging, cancel-in-progress: false }`.

**Rationale**: `cancel-in-progress: false` ensures a running deployment completes before the next one starts. This prevents partial deployments and maintains environment consistency.

**Key Findings**:
- GitHub Actions enforces a 6-hour job timeout by default, preventing indefinite queue blocks.
- Each environment (staging, production) should have its own concurrency group to allow independent deployment cadences.
- Rapid successive merges will queue but not cancel in-flight deployments.

---

## R-009: Deployment Gates Between Staging and Production

**Question**: What specific checks constitute the deployment gates?

**Decision**: Three automated gates executed sequentially after staging deployment: (1) CI pass verification (already guaranteed by `workflow_run` trigger), (2) security scan (`ruff check` + `pip-audit`), (3) staging health check validation. Plus one manual gate: GitHub Environment protection rule with required reviewers for production.

**Rationale**: FR-002 specifies gate order. CI pass is already guaranteed by the trigger mechanism. Security scan re-runs ensure the deployed code matches the checked code. Health checks validate the live staging environment.

**Key Findings**:
- `ruff check` is already configured in the project (used in CI). Run against `apps/ tests/ packages/`.
- `pip-audit` scans installed Python packages for known vulnerabilities. Install and run in the pipeline.
- Manual approval gate uses GitHub Actions `environment` with required reviewers configured in repository settings (not in YAML).
- 72-hour auto-reject: GitHub environment protection rules support wait timers but auto-reject requires a custom timeout mechanism or workflow-level `timeout-minutes`.
