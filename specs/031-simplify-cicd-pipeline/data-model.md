# Phase 1 — Data Model: Simplify CI/CD with Branch-Based Deployment

This feature has no application data model — it does not persist anything to Cosmos DB, the API store, or any other runtime data layer. The "data model" for a pipeline-config change is the set of **configuration entities** that the workflows, secrets, environments, and IaC parameter files form together. This document fixes their names, fields, and relationships so the contracts and tasks downstream are unambiguous.

## Entity overview

```text
GitHub Repository
└── Branch (4)               [main, dev, staging, production]
    ├── triggers → Workflow Run (CI)
    └── only env-branches trigger → Workflow Run (CD)

GitHub Environment (3)       [dev, staging, production]
├── holds → Secret AZURE_CREDENTIALS (1 per env)
└── targets → Azure Resource Group (1:1)

Azure Resource Group (3)     [rg-drh-dev, rg-drh-staging, rg-drh-production]
└── provisioned-by → Bicep template + parameter file

Bicep Parameter File (3)     [main.parameters.dev|staging|production.json]
└── consumed-by → infra/main.bicep

Decision Register Entry (1)  [docs/aidr/decisions/adr-031-azure-credentials-mvp.md]
└── governs → AZURE_CREDENTIALS deviation lifecycle
```

## Entities

### 1. Branch

| Attribute | Type | Values | Notes |
|---|---|---|---|
| `name` | string | `main` \| `dev` \| `staging` \| `production` | The four canonical branches; `main` is build/test only, the other three are deploy targets. |
| `protected` | boolean | recommended `true` for all four | Operator-set; out of scope for this PR. |
| `triggersCi` | boolean | `true` for all four | Per FR-001. |
| `triggersCd` | boolean | `false` for `main`; `true` for the other three | Per FR-003. |

**Identity**: `name` is unique within the repository.

**Lifecycle**: Branches are created once by the operator (see `quickstart.md`) and persist for the lifetime of the project. Force-pushes are allowed only for `main`; `dev`/`staging`/`production` should be linear via reviewed merge.

**Validation rules**:
- A push event on a branch not in this set MUST NOT trigger `cd`.
- A `workflow_run` whose `head_branch` is `main` MUST NOT cause `cd` to deploy (handled by the `branches:` filter on the `workflow_run` trigger).

### 2. GitHub Environment

| Attribute | Type | Values | Notes |
|---|---|---|---|
| `name` | string | `dev` \| `staging` \| `production` | Matches the deploy-target branch name. |
| `secrets` | map | `{ AZURE_CREDENTIALS: <JSON> }` | Exactly one secret required by this feature. |
| `protectionRules` | object | optional approvals / wait timer | Operator concern; preserved if already set. |

**Identity**: `name` is unique within the repository.

**Validation rules**:
- For all three environments, `secrets.AZURE_CREDENTIALS` MUST be present and parse as JSON conforming to `contracts/azure-credentials.schema.json`.
- An empty/missing/malformed `AZURE_CREDENTIALS` MUST cause the dependent `cd` (or `eval-pr-gate`) job to fail at the `azure/login` step with a clear error (per FR-016).

**Relationships**:
- 1:1 to Branch (by name).
- 1:1 to Azure Resource Group (by name → `rg-drh-<name>`).

### 3. AZURE_CREDENTIALS payload (the single secret)

The JSON object stored as `secrets.AZURE_CREDENTIALS`. Schema lives in `contracts/azure-credentials.schema.json` (Phase 1 contract artefact). Required fields:

| Field | Type | Required | Notes |
|---|---|---|---|
| `clientId` | string (UUID) | yes | Service-principal application (client) ID. |
| `clientSecret` | string | yes | The SP secret. **Long-lived; rotate every 90 days per ADR-031.** |
| `subscriptionId` | string (UUID) | yes | Azure subscription containing the resource group. |
| `tenantId` | string (UUID) | yes | Entra tenant. |
| `activeDirectoryEndpointUrl` | string (URL) | optional but recommended | Azure cloud endpoint constants. |
| `resourceManagerEndpointUrl` | string (URL) | optional but recommended | |
| `activeDirectoryGraphResourceId` | string (URL) | optional | Required only for legacy Graph scenarios. |
| `sqlManagementEndpointUrl` | string (URL) | optional | |
| `galleryEndpointUrl` | string (URL) | optional | |
| `managementEndpointUrl` | string (URL) | optional | |

**Validation rules**:
- `clientId`, `subscriptionId`, `tenantId` MUST match the UUID v4 pattern.
- `clientSecret` MUST be non-empty.
- The endpoint URLs, when present, MUST use `https`.

**Lifecycle**:
- **Create**: operator runs `az ad sp create-for-rbac --sdk-auth` once per environment, captures the JSON, pastes it into the GitHub Environment secret named `AZURE_CREDENTIALS`.
- **Rotate** (every 90 days): operator runs `az ad sp credential reset --id <clientId> --append`, captures the new JSON, replaces the secret. Detailed in `quickstart.md`.
- **Revoke** (incident response): operator runs `az ad sp credential delete --id <clientId> --key-id <kid>` and clears the GitHub secret.

### 4. Workflow

The five active workflow files, after this change.

| File | Trigger | Environment binding | Azure auth |
|---|---|---|---|
| `.github/workflows/ci.yml` | `push: [main, dev, staging, production]`, `pull_request:` | none (no Azure access) | none |
| `.github/workflows/cd.yml` | `workflow_run` on `ci`, branches `[dev, staging, production]`, `types: [completed]` | dynamic — `${{ github.event.workflow_run.head_branch }}` | `AZURE_CREDENTIALS` |
| `.github/workflows/drift-detection.yml` | `schedule: "0 16 * * 6"`, `workflow_dispatch` | matrix `[staging, production]` | `AZURE_CREDENTIALS` |
| `.github/workflows/eval-pr-gate.yml` | `pull_request: [main]` (path-filtered) | `dev` | `AZURE_CREDENTIALS` |
| `.github/workflows/eval-publish-dataset.yml` | `push: [dataset/*]`, `workflow_dispatch` | none until commented Azure block is activated | (commented) `AZURE_CREDENTIALS` |

**Validation rules**:
- Every workflow that references Azure CLI / `azure/login` MUST authenticate via `creds: ${{ secrets.AZURE_CREDENTIALS }}` and MUST run inside an `environment:` block.
- No workflow MUST reference `secrets.AZURE_CLIENT_ID`, `secrets.AZURE_TENANT_ID`, `secrets.AZURE_SUBSCRIPTION_ID`, `vars.AZURE_CLIENT_ID`, `vars.AZURE_TENANT_ID`, or `vars.AZURE_SUBSCRIPTION_ID` after the change.
- No workflow MUST request `permissions: id-token: write` unless explicitly justified.

### 5. Azure Resource Group

| Attribute | Type | Values |
|---|---|---|
| `name` | string | `rg-drh-dev` \| `rg-drh-staging` \| `rg-drh-production` |
| `location` | string | `australiaeast` (Constitution NN-2) |
| `provisionedFrom` | path | `infra/main.bicep` + `infra/main.parameters.<env>.json` |

### 6. Bicep parameter file

| Attribute | Type | Values |
|---|---|---|
| `path` | string | `infra/main.parameters.{dev,staging,production}.json` |
| `parameters.environmentName` | string | `drh-{dev,staging,production}` |
| `parameters.location` | string | `australiaeast` |
| `parameters.principalType` | string | `ServicePrincipal` |
| `parameters.openAiDeploymentSku` | string | `GlobalStandard` |
| `parameters.restrictNetworkAccess` | bool | `false` for dev; existing values preserved for staging/production |

**Validation rules**:
- One parameter file per environment, named `main.parameters.<env>.json` where `<env>` matches the branch name exactly (`dev` not `development`).
- The legacy file `main.parameters.development.json` MUST be deleted in this change (no consumer remains).

### 7. Decision Register Entry (`adr-031`)

A markdown document at `docs/aidr/decisions/adr-031-azure-credentials-mvp.md`. Required sections (matching the existing `adr-f02-async-bridge.md` pattern):

| Section | Content |
|---|---|
| Status | `Accepted (time-bound)` |
| Context | The OIDC standard previously enforced via `setup-oidc-azure` is being removed for MVP delivery velocity. |
| Decision | Use `AZURE_CREDENTIALS` JSON secret per environment; document deviation here. |
| Consequences | (a) Long-lived `clientSecret` requires manual 90-day rotation. (b) Loss of automated Foundry-carve-out enforcement (separate item). (c) Easier operator onboarding. |
| Trade-offs accepted | Increased secret-leakage blast radius; manual rotation burden; loss of identity-topology validation. |
| Review trigger | Before public GA, OR at the next governance checkpoint, OR upon any production-secret leakage incident. |
| Owner | (filled by operator at PR time) |
| Links | This spec (`specs/031-simplify-cicd-pipeline/spec.md`); the deleted ADR-029-01 reference if any. |

**Validation rules**:
- File exists.
- Links back to `specs/031-simplify-cicd-pipeline/spec.md`.
- Names a single owner.
- Names at least one review trigger condition.

## Relationships (entity diagram)

```text
                    ┌─────────────┐
                    │   Branch    │
                    │  (main)     │ → triggers CI only (no deploy)
                    └─────────────┘

  ┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐
  │   Branch    │ →   │   Workflow Run   │ →   │   Workflow Run   │
  │   (dev)     │     │     (ci.yml)     │     │     (cd.yml)     │
  └─────────────┘     └──────────────────┘     └──────────────────┘
         │                                              │
         │                                              ▼
         │                                   ┌─────────────────────┐
         │                                   │   GitHub Env (dev)  │
         │                                   │  + AZURE_CREDENTIALS│
         │                                   └─────────────────────┘
         │                                              │
         │                                              ▼
         │                                   ┌─────────────────────┐
         └─────────────  1 : 1  ────────────►│  rg-drh-dev (Azure) │
                                             │  ← main.bicep +     │
                                             │    parameters.dev   │
                                             └─────────────────────┘

(Same shape repeats for staging and production.)
```

## State transitions

The only entity with non-trivial state transitions is **Workflow Run (cd)**:

```text
queued ──► in-progress ──► success
                       └─► failure ──┬─► (env=dev)        ──► no further action
                                     └─► (env=staging|prod) ──► rollback ──┬─► success    ──► (issue NOT created)
                                                                            └─► failure   ──► critical-failure issue created
```

This transition is enforced by the `if:` conditions on the rollback and critical-issue steps in `cd.yml` (per R4 in `research.md`).

## What this feature does **not** model

- Application domain entities (incidents, alerts, evacuations, etc.) — unchanged.
- Cosmos DB containers, partition keys, repositories — unchanged.
- Eval framework data shapes — unchanged.
- API contracts — unchanged.

This file exists to anchor the contracts (`contracts/`) and tasks (`tasks.md`) on a single, agreed-upon set of names and fields for the configuration surface this PR touches.
