# Feature Specification: CD Pipeline with Staging Environment

**Feature Branch**: `feature/017-cd-pipeline`  
**Created**: 2025-07-14  
**Status**: Draft  
**Input**: User description: "Add a Continuous Deployment (CD) pipeline to the disaster response coordination hub that provides safe, automated deployment to Azure with staging environment, deployment gates, rollback automation, environment-specific configuration, and infrastructure drift detection."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Automated Staging Deployment After CI (Priority: P1)

As a DevOps engineer, I want changes merged to the main branch to be automatically deployed to a staging environment after CI passes, so I can validate the full solution in an Azure environment that mirrors production before promoting to production.

**Why this priority**: Without a working staging deployment, none of the other gates, rollback, or drift-detection capabilities have an environment to operate against. This is the foundational capability upon which everything else depends.

**Independent Test**: Can be fully tested by merging a change to main, observing CI pass, and then confirming that all four azd services (`api`, `agents`, `ingestion`, `web` per `azure.yaml`) are running and reachable in the staging Azure environment.

**Acceptance Scenarios**:

1. **Given** a pull request is merged to `main` and CI completes successfully, **When** the CD workflow triggers, **Then** all services are deployed to the staging environment within 15 minutes.
2. **Given** the staging deployment completes, **When** a user accesses each service's health endpoint in staging, **Then** every service returns a healthy status.
3. **Given** the CD workflow triggers, **When** CI has not passed (tests, lint, typecheck, or build failed), **Then** no deployment occurs and the workflow reports the blocking failure.
4. **Given** a staging deployment is in progress, **When** a new commit is pushed to main, **Then** the in-progress deployment completes (or is cancelled gracefully) before the new deployment begins.

---

### User Story 2 — Deployment Gates Between Staging and Production (Priority: P2)

As a security engineer, I want automated gates that enforce quality and security checks after staging deployment before any production promotion, so that unsafe or non-compliant code never reaches production.

**Why this priority**: Gates are the safety mechanism that give teams confidence in automated deployment. Without them, staging is just a pre-production environment with no enforcement — defeating the purpose of a staged pipeline.

**Independent Test**: Can be tested by deploying a known-bad change (e.g., a failing test or a dependency with a known vulnerability) and confirming the gate blocks promotion.

**Acceptance Scenarios**:

1. **Given** a staging deployment succeeds, **When** all automated gates pass (test pass, security scan, health check), **Then** the pipeline proceeds to the production promotion step.
2. **Given** a staging deployment succeeds, **When** the security scan gate detects a code quality or dependency vulnerability issue, **Then** the pipeline halts and reports the specific findings.
3. **Given** all automated gates pass, **When** a manual approval gate is configured for production, **Then** the pipeline pauses and waits for an authorized approver before deploying to production.
4. **Given** any automated gate fails, **When** the pipeline evaluates promotion readiness, **Then** the pipeline stops, no production deployment occurs, and a notification is sent with failure details.

---

### User Story 3 — Automated Rollback on Staging Health Failure (Priority: P2)

As an SRE, I want the pipeline to automatically roll back a staging deployment if health checks fail after deployment, so that the staging environment always remains in a known-good state and failed deployments don't block the team.

**Why this priority**: Tied with US2 because rollback automation is what makes staging safe. Without it, a bad deployment could leave staging broken, requiring manual intervention and blocking all subsequent deployments.

**Independent Test**: Can be tested by deploying a version with a deliberately broken health endpoint and confirming the system reverts to the previous healthy revision.

**Acceptance Scenarios**:

1. **Given** a staging deployment completes, **When** one or more service health checks fail within the health-check window, **Then** the system reverts all services to their previous known-good revision.
2. **Given** a rollback is triggered, **When** the rollback completes, **Then** health checks pass on the restored revision and the pipeline reports which services were rolled back and why.
3. **Given** a staging deployment completes, **When** all health checks pass within the health-check window, **Then** no rollback occurs and the deployment is marked as the new known-good revision.
4. **Given** a rollback is triggered but the previous revision also fails health checks, **When** the rollback health check fails, **Then** the pipeline reports a critical failure requiring manual intervention.

---

### User Story 4 — Environment-Specific Configuration (Priority: P1)

As a platform operator, I want each environment (dev, staging, production) to have its own isolated Azure resource group, application configuration, and secrets, so that environments do not interfere with each other and sensitive production data is never exposed in lower environments.

**Why this priority**: Tied with US1 because staging deployment cannot function without environment-specific configuration. Resource isolation is a prerequisite for any multi-environment deployment.

**Independent Test**: Can be tested by provisioning the staging environment and confirming its resources are in a separate resource group with distinct configuration values from production.

**Acceptance Scenarios**:

1. **Given** the pipeline deploys to staging, **When** the deployment resolves configuration, **Then** it uses staging-specific values (resource group, connection strings, feature flags) distinct from production.
2. **Given** a new environment variable or secret is added, **When** it is configured for staging only, **Then** it is not visible or accessible from the production environment.
3. **Given** the pipeline deploys to production, **When** the deployment resolves configuration, **Then** it uses production-specific values and connects only to production resources in the designated Azure Australia regions.

---

### User Story 5 — Infrastructure Drift Detection (Priority: P3)

As a platform operator, I want a scheduled check that compares the actual Azure infrastructure state against the declared IaC definitions, so I can catch unauthorized or accidental manual changes before they cause incidents.

**Why this priority**: Drift detection is a governance capability that operates independently of the deployment pipeline. While valuable, it does not block deployments and can be added after the core pipeline is operational.

**Independent Test**: Can be tested by manually modifying an Azure resource property outside of IaC and confirming the drift-detection report identifies the change.

**Acceptance Scenarios**:

1. **Given** the scheduled drift-detection workflow runs, **When** all Azure resources match the IaC definitions, **Then** the report indicates no drift and no alert is raised.
2. **Given** the scheduled drift-detection workflow runs, **When** one or more resources have drifted from IaC definitions, **Then** the report lists each drifted resource with the specific property differences.
3. **Given** drift is detected, **When** the report is generated, **Then** a GitHub Issue is created with the label `infrastructure-drift`, containing a summary of drifted resources and property-level differences.

---

### Edge Cases

- What happens when a deployment is already in progress and a new commit triggers the pipeline? GitHub Actions concurrency groups (`concurrency: group: deploy-{environment}`) ensure one deployment per environment at a time. A second deployment queues until the first completes.
- What happens when the staging environment's Azure resource group does not exist yet? The pipeline must provision it before deploying (first-run bootstrapping).
- What happens when health checks time out rather than returning an error? The pipeline treats a timeout as a failure and initiates rollback.
- What happens when rollback also fails? The pipeline alerts the operations team with a critical severity notification and stops further automated action.
- What happens when the drift-detection workflow cannot authenticate to Azure? The workflow fails gracefully with an authentication error report rather than silently passing.
- What happens when only some services fail health checks after deployment? The pipeline rolls back all services to maintain version consistency, not just the failing ones.
- What happens when OIDC token exchange to Azure AD fails (e.g., federated credential misconfigured or Azure AD outage)? The pipeline fails immediately at the authentication step with a clear error. No partial deployment occurs.
- What happens when a queued deployment waits indefinitely because the in-progress deployment hangs? GitHub Actions enforces a 6-hour job timeout; after that, the stuck job is cancelled and the queued deployment proceeds.
- What happens when infrastructure provisioning (`azd provision`) fails but service deployment has not started? The pipeline stops before any service deployment. No rollback is needed since no services were updated.
- What happens when the `web` App Service returns HTTP 200 at root but is serving an error page (e.g., Next.js build error)? The pipeline treats any HTTP 200 response as healthy. Content-level validation is out of scope for deployment health checks.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST deploy all four azd services (`api`, `agents`, `ingestion`, `web`) as defined in `azure.yaml` to the staging environment automatically after CI passes on the main branch.
- **FR-002**: System MUST execute deployment gates between staging and production in the following order: test pass verification, security scan (ruff for code linting and `pip-audit` for dependency vulnerability scanning), staging health check validation.
- **FR-003**: System MUST enforce a manual approval gate before production deployment that pauses the pipeline until an authorized team member approves. The approval gate MUST auto-reject after 72 hours if no action is taken. Staging deployments MUST NOT require manual approval.
- **FR-004**: System MUST automatically roll back all staging services to their previous known-good revision when any service's health check fails after deployment. The rollback logic MUST be implemented in `scripts/rollback.sh` (bash, for GitHub Actions `ubuntu-latest` runner compatibility).
- **FR-005**: System MUST maintain environment-specific configuration (resource groups, application settings, secrets) for at least two environments: staging and production. Environment-specific Bicep parameters MUST be defined in `infra/main.parameters.staging.json` and `infra/main.parameters.production.json` (extending the base `infra/main.parameters.json` variable-substitution pattern). Secrets MUST be stored in a dedicated Azure Key Vault per environment, accessed by the pipeline via workload identity federation and by application services via managed identity.
- **FR-006**: System MUST run a weekly infrastructure drift-detection check (Sunday 02:00 AEST / Saturday 16:00 UTC) via a dedicated workflow at `.github/workflows/drift-detection.yml` that compares live Azure resources against the IaC definitions and produces a report of differences. Drift findings MUST be posted as a GitHub Issue with the label `infrastructure-drift`.
- **FR-007**: System MUST report deployment failures, gate failures, rollback events, and drift detection findings using GitHub Actions native notification mechanisms only (commit status checks, deployment status, GitHub Issues). No external notification service (Slack, Teams, etc.) is required.
- **FR-008**: System MUST NOT modify or interfere with the existing CI workflow (`ci.yml`). The CD pipeline MUST be implemented as a separate workflow at `.github/workflows/cd.yml`, triggered by a `workflow_run` event when the `ci` workflow completes successfully on the `main` branch.
- **FR-009**: System MUST deploy all Azure resources to Australian regions (australiaeast as primary, australiasoutheast as failover) to comply with data sovereignty requirements. Parameter files MUST be validated (via test) to contain only Australian region values.
- **FR-010**: System MUST verify all 4 service health endpoints **in parallel** after staging deployment before marking the deployment as successful: `api` at `GET /api/health` (port 8000), `agents` at `GET /health` (port 8080), `ingestion` at `GET /health` (port 8081), and `web` at `GET /` (App Service root, HTTP 200). Each service health check MUST timeout after 30 seconds, with 3 retries at 10-second sleep between retry attempts. Total health-check window MUST NOT exceed 2 minutes across all services (achieved via parallel execution).
- **FR-011**: System MUST record the current deployment revision as the known-good baseline when all health checks pass, so future rollbacks have a target revision.
- **FR-012**: System MUST halt the pipeline and report a critical failure when a rollback itself fails health checks, requiring manual intervention.
- **FR-013**: System MUST support deploying from IaC definitions (`infra/main.bicep`, `targetScope = 'resourceGroup'`) so that infrastructure is provisioned or updated as part of the deployment pipeline. The pipeline MUST create the target resource group (via `az group create`) before invoking `azd provision` since the Bicep template is resource-group scoped.
- **FR-014**: System MUST authenticate to Azure using workload identity federation (GitHub OIDC → Azure AD federated credential). No long-lived credentials or service principal secrets MUST be stored in GitHub Actions secrets. Only OIDC federation configuration values (tenant ID, subscription ID, client ID) are permitted in GitHub repository settings.
- **FR-015**: System MUST enforce single concurrent deployment per environment using GitHub Actions concurrency groups (`concurrency: group: deploy-{environment}, cancel-in-progress: false`). A queued deployment MUST wait until the in-progress deployment completes before starting. If the in-progress deployment exceeds the GitHub Actions job timeout (6 hours default), it is cancelled by the platform and the queued deployment proceeds.

### Key Entities

- **Environment**: A deployment target (staging, production) with its own resource group, configuration, and secrets. Key attributes: name, Azure region, resource group identifier, configuration source.
- **Deployment Revision**: A versioned snapshot of all deployed services. Key attributes: revision identifier, deployment timestamp, health status, designation as known-good or rolled-back.
- **Deployment Gate**: An automated check that must pass before promotion to the next stage. Key attributes: gate name, gate type (test/security/health/manual), pass/fail status, failure details.
- **Drift Report**: A comparison of actual Azure infrastructure state against IaC definitions. Key attributes: report timestamp, list of drifted resources, property-level differences, severity.
- **Health Check Result**: The outcome of a health endpoint probe against a deployed service. Key attributes: service name, endpoint, response status, response time, pass/fail evaluation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Changes merged to main are deployed to the staging environment within 15 minutes of CI completion, with zero manual steps required.
- **SC-002**: 100% of deployments to production pass all automated gates (test, security scan, health check) — no ungated production deployments occur.
- **SC-003**: Failed staging deployments are automatically rolled back within 5 minutes of health-check failure detection.
- **SC-004**: Staging and production environments use completely isolated configuration — no shared resource groups, secrets, or connection strings between environments.
- **SC-005**: Infrastructure drift is detected and reported within 7 days of the change occurring, based on the weekly scheduled check (Sunday 02:00 AEST / Saturday 16:00 UTC). Drift findings are posted as GitHub Issues with the label `infrastructure-drift`.
- **SC-006**: The existing CI pipeline continues to function identically — no regressions in test, lint, typecheck, or build steps after CD pipeline is added.
- **SC-007**: All Azure resources remain deployed exclusively in Australian regions (australiaeast / australiasoutheast) across all environments.
- **SC-008**: Deployment gate failures produce actionable reports that identify the specific failing check, the affected service, and the remediation guidance within 2 minutes of the gate completing.
- **SC-009**: The platform supports at least 2 isolated environments (staging and production) with the ability to add more (e.g., dev) without pipeline redesign.
- **SC-010**: Rollback success rate is 95% or higher — meaning 95% of automated rollbacks restore all services to a healthy state without manual intervention.

## Assumptions

- The existing CI workflow (`ci.yml`) on GitHub Actions will remain the source of truth for test, lint, typecheck, and build validation. The CD pipeline triggers after CI succeeds rather than duplicating CI checks.
- Each Container Apps service exposes a health endpoint: `api` at `GET /api/health` (port 8000), `agents` at `GET /health` (port 8080), `ingestion` at `GET /health` (port 8081). The `web` service (App Service, Next.js) has no dedicated health endpoint; the CD pipeline will use `GET /` (HTTP 200) as its health check.
- Azure Developer CLI (`azd`) will be used for provisioning and deployment, leveraging `azure.yaml` (services: `api`, `agents`, `ingestion`, `web`) with environment-specific Bicep parameter files (`infra/main.parameters.staging.json`, `infra/main.parameters.production.json`).
- Bicep IaC in the `infra/` directory defines all infrastructure. The drift-detection workflow compares this IaC against the live Azure state.
- The manual approval gate for production will use the native environment protection rules mechanism provided by the CI/CD platform (GitHub Actions environments with required reviewers).
- Notifications for failures and alerts use GitHub Actions native mechanisms only: commit status checks, deployment status, and GitHub Issues. No external notification services (Slack, Teams, etc.) are in scope.
- The pipeline uses a single deployment strategy: rolling revision update for Container Apps services (`api`, `agents`, `ingestion`) and zip deploy for App Service (`web`). Rollback targets the previous known-good revision for each service type.
- The `dev` environment is considered optional for initial implementation. The pipeline must support staging and production, with the architecture allowing a `dev` environment to be added later.
- Pipeline authentication to Azure uses workload identity federation (GitHub OIDC → Azure AD federated credential), consistent with the project constitution's Principle IV managed identity requirement. No long-lived secrets are stored in GitHub.
- Security scans in the deployment gate use ruff for code linting and `pip-audit` for dependency vulnerability scanning. No additional SAST tool is required.

## Dependencies

- **Existing CI pipeline**: The CD pipeline depends on CI passing. Any CI workflow changes could affect CD triggering.
- **Azure subscription and permissions**: Deployment authenticates via workload identity federation (GitHub OIDC → Azure AD federated credential). No stored secrets in GitHub except OIDC federation configuration (tenant ID, subscription ID, client ID). Azure role assignments must grant the federated identity appropriate permissions for each environment.
- **Health endpoints**: Services must expose functioning health endpoints at their documented paths: `api` → `/api/health` (port 8000), `agents` → `/health` (port 8080), `ingestion` → `/health` (port 8081), `web` → `/` (App Service root, HTTP 200). If any health endpoint is broken or missing, the pipeline cannot validate deployments.
- **IaC definitions**: The Bicep template (`infra/main.bicep`, `targetScope = 'resourceGroup'`) already supports parameterized environments via `environmentName` and `location` parameters. Environment-specific parameter files (`infra/main.parameters.staging.json`, `infra/main.parameters.production.json`) must be created to provide staging- and production-specific values.
- **azure.yaml**: The Azure Developer CLI configuration defines four services (`api`, `agents`, `ingestion`, `web`) with Bicep-based infrastructure in `infra/`. Environment-specific overrides are provided via Bicep parameter files and `azd env` settings. Note: the `agents` service deploys a single Container App running the monitoring agent by default (`CMD ["python", "-m", "monitoring.agent"]`); all five agent modules (monitoring, risk_assessment, evacuation, resource_allocation, communication) share this container image.

## Constraints

- **Data sovereignty**: All Azure resources must reside in Australian regions (australiaeast primary, australiasoutheast failover) per the project constitution's Principle VI.
- **No CI regression**: The existing CI workflow must not be modified. The CD pipeline is additive only.
- **GitHub Actions**: The pipeline must be implemented using GitHub Actions, consistent with the existing CI setup.
- **Azure-only**: The solution must use Azure services exclusively. No multi-cloud or third-party deployment platforms.
- **No stored secrets for pipeline authentication**: Pipeline authentication MUST use workload identity federation (GitHub OIDC → Azure AD federated credential). No long-lived credentials or service principal secrets are permitted in GitHub Actions secrets.
- **Production rollback out of scope**: Automated rollback is implemented for staging only (FR-004). Production rollback requires manual intervention — the staging rollback demonstrates the pattern and the `scripts/rollback.sh` script can be invoked manually for production recovery. Full production automated rollback is deferred to a future iteration.

## Clarifications

### Session 2026-04-13

- Q: How should the pipeline authenticate to Azure? → A: Workload identity federation (GitHub OIDC → Azure AD federated credential). No stored secrets. Aligns with Constitution Principle IV managed identity requirement.
- Q: What are the specific health check timeout values for FR-010? → A: 30 seconds per service, 3 retries with 10s interval. Total timeout 2 minutes for all 6 services (5 agents + platform API).
- Q: Which security scan tool for dependency vulnerability scanning? → A: `pip-audit` (not `safety` which is commercial). Ruff handles linting. No additional SAST tool.
- Q: How are application secrets managed across environments? → A: Azure Key Vault per environment. Pipeline accesses via workload identity federation. Application services access via managed identity. No secrets stored in GitHub except OIDC federation config (tenant ID, subscription ID, client ID).
- Q: What notification mechanism for deployment and drift events? → A: GitHub Actions native notifications only (commit status checks, deployment status, GitHub Issues). No external notification service (Slack, Teams, etc.) — out of scope.
- Q: How are concurrent deployments handled? → A: GitHub Actions concurrency groups — one deployment per environment at a time. Second deployment queues until first completes. Pattern: `concurrency: group: deploy-{environment}`.
- Q: What is the drift detection schedule? → A: Weekly, Sunday 02:00 AEST (Saturday 16:00 UTC). Results posted as GitHub Issue with label `infrastructure-drift`.
- Q: What is the manual approval timeout and which environments require it? → A: 72 hours before auto-reject for production gate. Staging has no manual approval gate.

### Session 2026-04-13 — Pass 2 (Codebase Cross-Reference)

- Q: What services does `azure.yaml` actually define? → A: Four services: `api`, `agents`, `ingestion`, `web`. The spec originally referenced "5 agents + platform API" (6 services) but agents are deployed as a single Container App. Updated FR-001, FR-010, and all health check references to match the actual 4-service architecture.
- Q: What are the actual health endpoint paths per service? → A: `api` → `GET /api/health` (port 8000, mounted under `/api` prefix), `agents` → `GET /health` (port 8080), `ingestion` → `GET /health` (port 8081), `web` → `GET /` (App Service root, no dedicated health endpoint). Updated FR-010, Assumptions, and Dependencies.
- Q: Where should CD-related workflow and script files live? → A: CD workflow at `.github/workflows/cd.yml`, drift detection at `.github/workflows/drift-detection.yml`, rollback script at `scripts/rollback.sh` (bash). Updated FR-004, FR-006, FR-008.
- Q: How should the CD workflow trigger after CI? → A: Via `workflow_run` event on the `ci` workflow (name from `ci.yml`) completing on `main`. Updated FR-008.
- Q: What is the Bicep parameter file strategy for multi-environment? → A: Environment-specific files `infra/main.parameters.staging.json` and `infra/main.parameters.production.json` extending the existing `infra/main.parameters.json` variable-substitution pattern. Updated FR-005, FR-013, Assumptions, and Dependencies.
- Q: How does FR-015 handle a hung deployment blocking the concurrency group? → A: GitHub Actions 6-hour job timeout cancels stuck jobs automatically. Updated FR-015 and added edge case.
- Q: What is the Bicep `targetScope` and what does it imply for the pipeline? → A: `targetScope = 'resourceGroup'` — the pipeline must create the target resource group before invoking `azd provision`. Updated FR-013 and added edge case.
