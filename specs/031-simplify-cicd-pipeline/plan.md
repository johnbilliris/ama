# Implementation Plan: Simplify CI/CD with Branch-Based Deployment

**Branch**: `031-simplify-cicd-pipeline` | **Date**: 2026-04-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/031-simplify-cicd-pipeline/spec.md`

## Summary

Replace the current opaque, multi-environment-in-one-workflow CI/CD pipeline with a strict **branch-equals-environment** model: pushes to `dev`, `staging`, or `production` trigger `ci.yml`; on success the existing `cd.yml` (re-wired via `workflow_run`) deploys to *exactly* the matching Azure resource group (`rg-drh-dev` / `rg-drh-staging` / `rg-drh-production`). All Azure auth is collapsed to a single `AZURE_CREDENTIALS` JSON secret stored per GitHub Environment (a documented temporary deviation from OIDC, recorded in a new ADR). The entire spec-029 progressive-delivery footprint is deleted (10 workflow files, 3 custom actions, the `tools/pipeline` Python package, and the supporting `infra/policy/` + `infra/IDENTITY.md` + `scripts/spec029-bootstrap/` artefacts that exist only to feed those workflows). Drift detection is scoped to `staging` and `production` only.

The change is **infrastructure / pipeline only** — no application source code (FastAPI, Next.js, agents) is modified. The three runtimes (Next.js web dashboard, FastAPI coordination API, Python autonomous agents) continue to be packaged and deployed by the existing `azd` flow inside `cd.yml`; we are simplifying *how* and *when* `cd.yml` runs, not *what* it deploys.

## Technical Context

**Language/Version**:
- GitHub Actions workflow YAML (schema v2)
- Bash 5 (workflow steps + `scripts/rollback.sh`)
- Bicep (Azure resource templates) — no version bump required
- Markdown (decision-register entry + spec docs)

**Primary Dependencies**:
- `azure/login@v3` (consumes `creds:` JSON for service-principal auth)
- `Azure/setup-azd@v2` (provisions/deploys via `azd provision` and `azd deploy`)
- Azure CLI 2.x (`az containerapp`, `az webapp`, `az group`, `az deployment group what-if`)
- `actions/checkout@v5`, `actions/setup-python@v6`, `actions/setup-node@v5`, `pnpm/action-setup@v5`
- GitHub CLI (`gh issue create`) for critical-failure issue path

**Storage**: N/A for the pipeline itself. Deployed runtimes (api, agents, ingestion, web) continue to use their existing Cosmos DB / Storage / Service Bus resources provisioned by `infra/main.bicep`.

**Testing**:
- Workflow validation: `actionlint` on the YAML files (run locally; not added as a gate in this change).
- End-to-end test: push a no-op commit to each environment branch and verify the matching `cd` run deploys to (and only to) the matching resource group.
- Existing `pytest tests/contract tests/integration` continues to gate `ci`; no new test framework introduced.

**Target Platform**:
- Runner: `ubuntu-latest` (GitHub-hosted)
- Azure target: Azure Container Apps (`api`, `agents`, `ingestion`) + App Service (`web`) in **Australia East** for staging/production. Dev: same composition, lower SKUs (set by `infra/main.parameters.dev.json`).

**Project Type**: Pipeline-only configuration change applied to a multi-runtime monorepo (Next.js web + FastAPI api + Python agents + Python ingestion). No new code projects; no source-tree restructure.

**Performance Goals**:
- `ci` total wall time on a clean push ≤ existing baseline (no regression).
- `cd` end-to-end (login → provision → deploy → health check) ≤ 20 minutes per environment (preserves existing `timeout-minutes: 20`).

**Constraints**:
- `AZURE_CREDENTIALS` is a long-lived secret — rotation is manual (called out in the ADR).
- `workflow_run` runs in the *default-branch* context — workflow MUST explicitly check out `github.event.workflow_run.head_sha` to deploy the correct commit.
- `cd` MUST NOT trigger from PR-driven `ci` runs (only from `push` events on the three environment branches).
- Concurrency: one in-flight `cd` per environment, queued (not cancelled) — `concurrency.group: deploy-<env>`, `cancel-in-progress: false`.
- Data sovereignty (Constitution NN-2): all deployment targets stay in Australia East. The CI/CD change does not introduce any non-AU resource.

**Scale/Scope**:
- 5 active workflows after the change: `ci.yml`, `cd.yml`, `drift-detection.yml`, `eval-pr-gate.yml`, `eval-publish-dataset.yml`.
- 10 spec-029 workflow files deleted, 3 custom composite actions deleted, 1 Python package removed, 1 ADR added, 1 Bicep parameter file added (`main.parameters.dev.json`), 1 Bicep parameter file aligned (`main.parameters.development.json` → renamed/replaced by `dev`).
- 3 GitHub branches created (`dev`, `staging`, `production`) — operator action.
- 3 GitHub environments configured with `AZURE_CREDENTIALS` (`dev`, `staging`, `production`) — operator action.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution governs the **disaster-response platform itself**, not the CI/CD machinery. Most principles (I–VII, evacuation, recovery, AWS) are non-applicable to a pipeline-config change. The relevant gates are:

| Constitution clause | Applicability | Result |
|---|---|---|
| **VIII. Cloud Platform** — "Azure", "IaC (Bicep preferred)", "Deployment via CI/CD (GitHub Actions)" | Direct | ✅ Pass — change keeps GitHub Actions + Bicep, single deploy path per environment. |
| **NN-2. Data sovereignty** — all platform data in AU; carve-out only for model-hosting endpoints | Indirect | ✅ Pass — the pipeline only deploys to existing AU-region resource groups (`australiaeast`). No new non-AU resource is introduced; the carve-out is unaffected. |
| **NN-2 carve-out machinery** — `infra/policy/foundry-carveout.yaml` was added by spec-029 to enforce the carve-out at deploy time | **Risk** | ⚠️ The deletion of `infra/policy/` files supporting spec-029 removes the *automated* carve-out enforcement (`policy/foundry-carveout.yaml`, posture-verifier sweep). The constitutional requirement itself remains; what we lose is the automated check. **Action:** explicitly call this out in the ADR as a known regression of automated enforcement and add it to the FR-020 recommendations queue. We do NOT delete the constitutional clause. |
| **NN-5. Graceful degradation** | Indirect | ✅ Pass — branch-based deployment isolates blast radius per environment; failed `dev` deploys cannot affect staging/production. |
| **Quality Gates** — every PR passes lint + unit + integration; infra changes need What-If review | Direct | ✅ Pass — `ci.yml` continues to run lint + tests on PRs; `drift-detection.yml` continues to run What-If on staging/production. |
| **Governance** — spec changes require PR with reviewer | Direct | ✅ Pass — this change is a PR. |

**Gate status: PASS with one documented regression** (loss of automated Foundry-carve-out enforcement when `infra/policy/foundry-carveout.yaml` is removed). The regression is captured in `research.md` §R-CON-1 and surfaced in the ADR as a follow-up item.

The constitution itself was amended in v1.2.0 to support spec-029. The amendment text remains valid — only the *enforcement automation* introduced by spec-029 is removed. **No constitutional amendment is proposed by this change.**

## Project Structure

### Documentation (this feature)

```text
specs/031-simplify-cicd-pipeline/
├── plan.md                    # This file
├── research.md                # Phase 0 — decisions on workflow_run pattern, secret format, dev SKUs, carve-out regression
├── data-model.md              # Phase 1 — entity model: branches, envs, secrets, workflows, parameter files
├── quickstart.md              # Phase 1 — operator runbook to wire env secrets and verify the pipeline end-to-end
├── contracts/
│   ├── ci-workflow.md         # Trigger contract for ci.yml (events, branches, jobs, outputs)
│   ├── cd-workflow.md         # Trigger contract for cd.yml (workflow_run, head_branch mapping, concurrency)
│   ├── azure-credentials.schema.json  # JSON Schema for the AZURE_CREDENTIALS secret payload
│   └── drift-detection.contract.md     # Matrix scope, schedule, outputs
└── checklists/
    └── requirements.md        # (already authored in /speckit.specify)
```

### Source Code (repository root) — files this feature touches

```text
.github/workflows/                   # ─── Workflow files
├── ci.yml                           # MODIFY: add dev/staging/production to push branches
├── cd.yml                           # MODIFY: workflow_run for 3 branches, head_branch routing,
│                                   #         AZURE_CREDENTIALS, dev environment, dev rollback skip
├── drift-detection.yml              # MODIFY: matrix → [staging, production] only;
│                                   #         AZURE_CREDENTIALS auth
├── eval-pr-gate.yml                 # MODIFY: AZURE_CREDENTIALS from `dev` GitHub environment;
│                                   #         drop AZURE_CLIENT_ID / TENANT_ID / SUBSCRIPTION_ID
├── eval-publish-dataset.yml         # MODIFY: rewrite commented Azure block to use AZURE_CREDENTIALS
│
├── spec029-ci.yml                   # DELETE
├── spec029-cd.yml                   # DELETE
├── spec029-drift-detection.yml      # DELETE
├── change-freeze.yml                # DELETE
├── posture-exception-sweep.yml      # DELETE
├── evidence-pack.yml                # DELETE
├── dev-key-issue.yml                # DELETE
├── emergency-hotfix.yml             # DELETE
└── _reusable/
    ├── pr-gates.yml                 # DELETE (consumer spec029-ci.yml is gone)
    └── canary-stage.yml             # DELETE (consumer spec029-cd.yml is gone)

.github/actions/                     # ─── Custom composite actions (transitively orphaned)
├── install-opa/                     # DELETE — only consumer was _reusable/pr-gates.yml
├── setup-cosign-syft/               # DELETE — only consumer was spec029-ci.yml
└── setup-oidc-azure/                # DELETE — only consumers were the two _reusable/ files

.github/state/freeze.json            # DELETE (managed by deleted change-freeze workflow)

infra/                               # ─── IaC
├── main.bicep                       # UNCHANGED (already supports parameter-driven SKUs)
├── main.parameters.dev.json         # CREATE (cheaper SKUs; environmentName=drh-dev)
├── main.parameters.development.json # DELETE (replaced by .dev.json — naming aligns with branch)
├── main.parameters.staging.json     # UNCHANGED
├── main.parameters.production.json  # UNCHANGED
│
├── IDENTITY.md                      # DELETE — only referenced by deleted setup-oidc-azure action
├── policy/
│   ├── posture-matrix.yaml          # DELETE — consumed by deleted posture-exception-sweep
│   ├── posture-exceptions.yaml      # DELETE
│   ├── foundry-carveout.yaml        # DELETE — see Constitution Check note (regression)
│   └── rego/                        # DELETE — consumed by deleted install-opa + posture-verifier
└── bicep/modules/posture-policy-set.bicep  # KEEP (declarative Azure Policy module —
                                            #  out of scope; future cleanup if unused)

tools/pipeline/                      # DELETE — Python package consumed only by deleted workflows

scripts/
├── rollback.sh                      # UNCHANGED (still invoked by cd.yml for staging/prod)
└── spec029-bootstrap/               # DELETE — operator scripts for deleted spec-029 SP/Entra setup

docs/aidr/decisions/
└── adr-031-azure-credentials-mvp.md # CREATE — the decision-register entry (FR-017)
```

**Structure Decision**: Pipeline-only change applied to the existing monorepo. No new application code projects; no source-tree restructure. The deletion list is intentionally aggressive per the clarification answer (Q1 of `/speckit.clarify`), but **does not touch any of the three runtime applications** (Next.js `apps/web`, FastAPI `apps/api`, Python `apps/agents`, `apps/ingestion`). Azure resource deployment for those runtimes continues unchanged through `infra/main.bicep` + `azd`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Loss of automated Foundry-carve-out enforcement at deploy time (deletion of `infra/policy/foundry-carveout.yaml` + posture-verifier) | Spec-029 was the *only* consumer of that automation; keeping the policy file alive without the workflow that evaluates it would be dead code that misleads operators into thinking enforcement is active. | Keeping `foundry-carveout.yaml` plus a stub workflow to evaluate it would re-introduce the spec-029 surface area we are explicitly removing. The constitutional requirement remains documented; manual review of any new model-hosting region is the interim control until the carve-out automation is re-introduced (post-MVP). |
| Long-lived service-principal `clientSecret` instead of OIDC federated credentials | OIDC requires per-environment federated-credential setup in Entra plus the `setup-oidc-azure` composite (which we are deleting). For MVP delivery the operator burden of OIDC was the blocker. | Re-implementing OIDC inside the simplified pipeline would re-introduce the very plumbing we are removing. The deviation is explicitly time-bound by the new ADR (`adr-031`). |
