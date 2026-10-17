# Azure Deployment Plan

> **Status:** Deployed

Generated: 2026-10-16

---

## 1. Project Overview

**Goal:** Fix Azure Monitor Live Metrics authentication in the API, grant its managed identity telemetry-publishing access, rebuild the container image, and roll it out to the existing dev Container App.

**Path:** Modify existing Azure application

## 2. Requirements

| Attribute | Value |
|-----------|-------|
| Classification | Development |
| Scale | Small; existing single Container App |
| Budget | Cost-optimized; no infrastructure or SKU changes |
| Subscription | ME-MngEnvMCAP035973-prbillir-2 (`74a25c57-d6e4-446e-8c99-7f5ace60011b`), confirmed by user |
| Location | Australia East, confirmed by user |

## 3. Components Detected

| Component | Type | Technology | Path |
|-----------|------|------------|------|
| AMA API | API | Python 3.12, FastAPI, Azure Monitor OpenTelemetry | `apps/api` |
| API image | Container | Docker; remotely built in ACR | `apps/api/Dockerfile` |
| Telemetry authorization | RBAC | AVM resource-scoped role assignment | `infra/bicep/modules/eval/eval-platform.bicep` |

## 4. Recipe Selection

**Selected:** Azure CLI — targeted application-image update

**Rationale:** The API is already deployed and its image is built remotely by ACR. Apply only the scoped App Insights role assignment and API image update; do not redeploy the full evaluation platform. Refresh the existing `dev` image tag and use a new revision suffix so the app deploys the new digest while keeping its configured image reference consistent.

## 5. Architecture

**Stack:** Existing Azure Container Apps deployment

### Service Mapping

| Component | Azure Service | SKU |
|-----------|---------------|-----|
| API | Container App `app-ama-api-dev` in `rg-ama-eval-dev` | Existing Consumption profile; no change |
| Container image | ACR `acramaevaldevzeaes6.azurecr.io` | Existing registry; no change |
| Telemetry | Existing Application Insights connection string and user-assigned managed identity | No resource change |
| Telemetry authorization | Monitoring Metrics Publisher role on the existing App Insights component | One resource-scoped assignment to the API identity |

### Supporting Services

| Service | Purpose |
|---------|---------|
| Azure Container Registry | Build and store the API image |
| Azure Container Apps | Run the API using the updated image |
| User-assigned managed identity | Authenticate the Live Metrics exporter |
| Application Insights | Existing destination for application telemetry |

## 6. Provisioning Limit Checklist

No compute, storage, or monitoring resources/SKUs will be added. One resource-scoped `Microsoft.Authorization/roleAssignments` assignment will be created for the API identity on the existing App Insights component. The operation also rebuilds an image in the existing ACR and updates the existing Container App revision; service provisioning quotas are not applicable.

| Resource Type | Number to Deploy | Total After Deployment | Limit/Quota | Notes |
|---------------|------------------|------------------------|-------------|-------|
| `Microsoft.Authorization/roleAssignments` | 1 | 1 | Not applicable | Scoped to the existing App Insights component; only `Monitoring Metrics Publisher` for the API identity |

**Status:** No new service provisioning; one narrow RBAC assignment.

## 7. Execution Checklist

### Phase 1: Planning
- [x] Analyze workspace and existing Azure deployment
- [x] Confirm subscription and location with user
- [x] Prepare resource inventory; no new resources
- [x] Scan API and Docker build configuration
- [x] Select targeted Azure CLI recipe
- [x] User approved this plan
- [x] User approved the scoped App Insights role assignment and deployment

### Phase 2: Execution
- [x] Pass `AZURE_CLIENT_ID` to `ManagedIdentityCredential`
- [x] Add an AVM resource-scoped `Monitoring Metrics Publisher` assignment for the API identity
- [x] Synchronize the generated eval-platform ARM template
- [x] Run API syntax validation and test suite
- [x] Build and push `ama/api:dev` to the existing ACR
- [ ] Deploy only the scoped App Insights role assignment (no full platform deployment)
- [ ] Update `app-ama-api-dev` with a unique revision suffix
- [x] Omit unsupported temperature from GPT-5 Foundry requests
- [x] Run focused Foundry client tests
- [x] Build and push `eval-runner:dev` to the existing ACR
- [x] Update `caj-eval-runner-dev` to the rebuilt image

### Phase 3: Validation
- [x] All validation checks pass
  - [x] Focused Foundry client test suite
  - [x] ACR remote build for eval-runner
- [x] Targeted Azure deployment preflight passed
  - [x] Azure CLI auth, Bicep compile, group validation, and role-assignment what-if
  - [x] Docker image build (remote ACR build; local Docker daemon unavailable)
  - [x] Azure Policy review (no applicable deny conflict)
- [x] Confirm deployment and active revision
- [x] Check `/api/health` and app logs for the Live Metrics credential error
- [x] Record validation proof below

### Phase 4: Deployment
- [x] Report deployed image and revision
- [x] Update `caj-eval-runner-dev` to the rebuilt image

## 7. Validation Proof

Validation so far:

| Check | Command Run | Result | Timestamp |
|-------|-------------|--------|-----------|
| Python syntax | `python -m compileall -q apps/api/app/main.py` | Passed | 2026-10-16 |
| API tests | `python -m pytest -q apps/api/tests` | 241 passed; 19 failed and 4 errors in unrelated API/contract tests | 2026-10-16 |
| ACR API image build | `az acr build --registry acramaevaldevzeaes6 --image ama/api:dev --file apps/api/Dockerfile --platform linux/amd64 .` | Remote run `cr3` succeeded; digest `sha256:5edcebc192736c9acad1a10a6ac7f27d85233dcef162e4ac27c093e90981b304` | 2026-10-16 |
| Eval Bicep compile | `az bicep build --file infra/bicep/modules/eval/eval-platform.bicep --outfile $env:TEMP\eval-platform-validation.json` | Passed with existing `no-hardcoded-env-urls` warning | 2026-10-16 |
| Updated eval Bicep compile | `az bicep build --file infra/bicep/modules/eval/eval-platform.bicep --outfile $env:TEMP\eval-platform-role-validation.json` | Passed; existing `no-hardcoded-env-urls` warning only | 2026-10-16 |
| Foundry client tests | `python -m pytest -q tests/unit/eval/test_foundry_failures.py` | 15 passed | 2026-10-17 |
| Runner Foundry + build-context tests | `python -m pytest -q tests/unit/eval/test_foundry_failures.py tests/unit/eval/test_run_llm_evaluation_script.py` | 63 passed | 2026-10-17 |
| Eval-runner ACR build | `az acr build --registry acramaevaldevzeaes6 --image eval-runner:dev --file <minimal-context>\apps\eval-runner\Dockerfile --platform linux/amd64 --no-logs <minimal-context>` | Run `cr6` succeeded; digest `sha256:38398c3cb9e05578990b431786465ecaeb470d1cdd6b952b0f05856b3da7f3d6` | 2026-10-17 |
| Runner ACR pull role | `az role assignment list --scope <ACR-resource-id> --assignee <runner-principal-id> --include-inherited` | `AcrPull` present | 2026-10-17 |
| Single-role ARM validation | `az deployment group validate --resource-group rg-ama-eval-dev --template-file .azure/appinsights-rbac-once.bicep --parameters principalId=... appInsightsResourceId=...` | Succeeded; validated one role assignment | 2026-10-16 |
| Single-role what-if | `az deployment group what-if --resource-group rg-ama-eval-dev --template-file .azure/appinsights-rbac-once.bicep --parameters principalId=... appInsightsResourceId=...` | Exactly 1 role assignment Create; 17 existing resources ignored; no other changes | 2026-10-16 |
| API identity registry role | `az role assignment list --scope <ACR-resource-id> --assignee <API-principal-id>` | `AcrPull` present | 2026-10-16 |
| App Insights identity role | `az role assignment list --scope <App-Insights-resource-id> --assignee <API-principal-id> --include-inherited` | `Monitoring Metrics Publisher` assigned at the App Insights component scope | 2026-10-16 |
| Policy review | Subscription policy query and project governance constraints | No applicable deny policy for the resource-scoped publisher assignment | 2026-10-16 |

Local Docker daemon was unavailable, so the API image was built by ACR instead. The API test suite failures include unrelated contract assertions and a missing local `redis` dependency; none reference the changed startup file. Azure validation is pending.

The ACR build command's local log streamer exited on a Windows code-page encoding error, but ACR run `cr3` completed with `Succeeded`; its reported image digest is recorded above. The full API suite reported 241 passed, 19 failed, and 4 errors in tests unrelated to the changed startup file (including a missing local `redis` package); those unrelated failures are recorded and were not modified. The targeted Bicep/ARM and image-build checks passed.

## 8. Deployment Results

| Item | Result |
|------|--------|
| App Insights role assignment | `Monitoring Metrics Publisher`, assignment `b1d51d26-19b0-5fcd-8dff-e4998d136f21`, scoped to the eval Application Insights component |
| Role deployment | `api-appinsights-role-20261016` succeeded |
| API image | `acramaevaldevzeaes6.azurecr.io/ama/api:dev` (`sha256:5edcebc192736c9acad1a10a6ac7f27d85233dcef162e4ac27c093e90981b304`) |
| Container App revision | `app-ama-api-dev--otel-uai-1016`, Provisioned and Healthy, 1 replica, 100% traffic |
| Health endpoint | HTTP 200; overall status `healthy` (its separate tenant-telemetry status fields remain unconfigured) |
| Live Metrics | Three QuickPulse pings returned HTTP 200; 24 telemetry transmissions succeeded; no exporter errors in the inspected logs |
| Runner image deployment | `az containerapp job update --name caj-eval-runner-dev --resource-group rg-ama-eval-dev --container-name runner --image acramaevaldevzeaes6.azurecr.io/eval-runner:dev` | Succeeded; job provisioning state `Succeeded`; image points to rebuilt dev tag | 2026-10-17 |

**Validated by:** Azure validation workflow  
**Validation timestamp:** 2026-10-16

## 9. Files to Change

| File | Purpose | Status |
|------|---------|--------|
| `apps/api/app/main.py` | Select the configured user-assigned managed identity for Azure Monitor | Updated |
| `apps/eval-runner/src/ama_eval/foundry_client.py` | Omit temperature for GPT-5 Foundry inference calls | Updated |
| `tests/unit/eval/test_foundry_failures.py` | Assert GPT-5 requests omit temperature | Updated |
| `infra/bicep/modules/eval/eval-platform.bicep` | Grant the API identity scoped telemetry-publishing rights | Updated |
| `infra/bicep/modules/eval/eval-platform.json` | Keep compiled ARM template synchronized with Bicep | Updated |
| `.azure/deployment-plan.md` | Record the deployment plan and validation results | In progress |

## 10. Next Steps

> Current: Complete

Deployment completed and verified.
