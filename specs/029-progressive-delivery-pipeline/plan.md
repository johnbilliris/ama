# Implementation Plan: Trunk-Based Progressive Delivery Pipeline

**Branch**: `029-progressive-delivery-pipeline` | **Date**: 2026-04-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/029-progressive-delivery-pipeline/spec.md`

## Summary

Evolve the existing `ci.yml` / `cd.yml` / `drift-detection.yml` workflows into a trunk-based, progressive-delivery pipeline that promotes a single signed artefact through `dev` → `staging` → production canary (5/25/50/100 %) under SLO burn-rate auto-promotion / auto-rollback, with a 10-minute median PR gate budget, an immutable evidence pack per production promotion, an Incident-Mode Change Freeze with a 2-person emergency-hotfix lane, and an environment-tiered Azure infrastructure posture (relaxed `dev`, locked-down `staging`/`production`) enforced mechanically through a single canonical posture matrix at `infra/policy/posture-matrix.yaml`.

Technical approach: keep the three runtimes (Next.js 16 web, FastAPI API, Python autonomous agents) build-once / deploy-many; consume Bicep What-If + OPA conftest at PR time; use OIDC-federated Entra ID workload identities exclusively; write evidence packs to immutability-policy Blob Storage in `australiaeast`; persist deployment audit events into the existing platform append-only audit store using the same `actor / timestamp / action / rationale / outcome` schema as incident events; isolate environments via one resource group per environment (`rg-ama-{env}-{region}`) with RG-scoped Azure Policy assignments generated from the posture matrix; permit Microsoft Foundry model-hosting endpoints in non-AU regions under a named carve-out file; rely on Microsoft Defender for Cloud + Entra ID Protection (no bespoke heuristics) for `dev` data-plane anomaly detection.

## Technical Context

**Language/Version**:
- Pipeline orchestration: GitHub Actions YAML (no language version), reusable workflows in `.github/workflows/`
- Pipeline-side scripts and posture verifier: Python 3.12 (matches `apps/api`, `apps/agents`)
- Web runtime under deployment: Next.js 16.2 / TypeScript 5.x (Node 20 LTS)
- API runtime under deployment: FastAPI / Python 3.12 (uvicorn)
- Autonomous agents runtime under deployment: Python 3.12

**Primary Dependencies**:
- GitHub Actions, GitHub OIDC → Entra ID federated workload identities
- Azure CLI / `azd`, Bicep CLI, `az deployment group what-if`
- OPA / `conftest` for IaC policy-as-code; Rego rules under `infra/policy/`
- Azure Resource Graph (cross-env reference detection FR-029, posture sweep FR-031)
- Azure Container Apps revision-based traffic-splitting (services); Azure App Service deployment slots (web)
- Azure Monitor / Application Insights for SLO burn-rate (availability, p95 API latency, p95 dashboard load, signal freshness, recommendation correctness)
- Cosign (image signing), Syft (SBOM), SLSA-3 GitHub provenance attestation
- Microsoft Defender for Cloud + Entra ID Protection (FR-026 anomaly detection)
- Microsoft Entra Privileged Identity Management (PIM) for staging/prod jump-host JIT access
- Azure Bastion + hardened jump-host VM per non-prod / prod VNet

**Storage**:
- Evidence pack store: Azure Blob Storage (immutable, time-based retention 7 years, legal hold) in `australiaeast`
- Deployment audit events: existing platform append-only Cosmos DB audit store (shared schema with incident/operator events; partition key includes `actor` + day bucket)
- Pipeline state (canary stage cursor, freeze flag, known-good index): GitHub Deployments API + a small Cosmos container `pipeline_state` reusing the existing audit Cosmos account
- Image artefact store: Azure Container Registry in `australiaeast` with retention ≥ 3 known-good digests per service (FR-021)
- Posture matrix and exception register: version-controlled YAML at `infra/policy/posture-matrix.yaml` and `infra/policy/posture-exceptions.yaml`

**Testing**:
- pytest for pipeline-side Python (posture verifier, evidence-pack assembler, audit emitter)
- Conftest unit tests (`*.rego` + fixture JSON) for IaC policy gate
- Bash / pwsh smoke tests for workflow dispatch flows (`dev-key-issue.yml`, freeze toggle)
- Synthetic canary harness (deliberate latency injection) for FR-008 auto-rollback validation
- Existing repo test suite (~2255 unit/integration/contract tests, ~6.5 min) continues to gate every PR

**Target Platform**:
- Pipeline: GitHub-hosted Linux runners (`ubuntu-22.04`); self-hosted runners explicitly out of scope to keep runner identity = OIDC subject
- Workloads: Azure Container Apps (`api`, `agents`, `ingestion`) + Azure App Service (`web`), all in `rg-ama-{env}-australiaeast`
- Foundry model-hosting endpoints: any Azure region per the named carve-out list (FR-018)

**Project Type**: Web application (Next.js frontend + FastAPI backend + Python agents) — pipeline feature operates across the existing monorepo, not a new app

**Performance Goals**:
- PR gate median < 10 min wall-clock (FR-002, SC-002); p95 < 15 min
- Build-once: single image build per merge to `main`, no rebuilds downstream
- Auto-rollback: traffic restored to known-good revision within 5 min of fast-burn breach (FR-008, SC-004)
- Lead time merge → 100 % production traffic < 60 min for non-safety-critical changes (SC-001)
- Evidence pack written within 5 min of promotion completion (FR-013, SC-005)

**Constraints**:
- All workloads, telemetry, audit, evidence storage MUST remain in `australiaeast` / `australiasoutheast` (Constitution NON-NEGOTIABLE #2). Sole exception: Foundry model-hosting endpoints on the named carve-out (FR-018; constitution v1.2.0 carve-out).
- OIDC-only identity, zero long-lived cloud secrets (FR-016, SC-007)
- Append-only audit, 7-year retention with legal hold (FR-014, FR-015)
- Posture matrix is the SOLE source of truth; ad-hoc Azure Policy edits in the portal are prohibited and surfaced as drift
- Emergency-hotfix lane MUST keep all correctness/safety/supply-chain/policy gates mandatory; only long-running gates may be deferred (FR-012)
- Posture-matrix gate is non-skippable in the emergency-hotfix lane (FR-028)
- `dev` posture relaxation is conditional on no real PII / PSPF-marked content in `dev`

**Scale/Scope**:
- 4 deployable services (`api`, `agents`, `ingestion`, `web`) × 3 environments = 12 deployment targets
- ~10–30 PRs/week → ~10–30 production promotions/week → equivalent evidence-pack writes
- Posture matrix coverage: ~15 Azure resource types across the platform (Cosmos DB, Storage, Key Vault, Service Bus, Event Grid, ACR, Container Apps, App Service, Application Insights, Log Analytics, AKS where relevant, Foundry, IoT Hub, Maps, Communication Services)
- ~10 developer Entra IDs concurrently issuing dev API keys via `dev-key-issue.yml`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle / Non-Negotiable | Status | Evidence |
|---|----------------------------|--------|----------|
| 1 | I. Primacy of Life and Harm Reduction | ✅ PASS | Incident-Mode Change Freeze (US6, FR-011, FR-012) suspends auto-promotion during SEV-1; SC-001 explicitly suspended during freeze; emergency lane keeps all safety/correctness gates mandatory |
| 2 | II. National Emergency Management Principles | ✅ PASS | Continual-improvement principle realised via SC-003 (CFR), SC-004 (MTTR), SC-011 (drift closure SLA); coordinated/integrated principles realised via shared audit-store schema (FR-015) |
| 3 | III. Multi-Hazard, Multi-Agency Design | ✅ PASS | Pipeline is hazard-agnostic; touches no hazard-specific logic |
| 4 | IV. Transparency and Auditability | ✅ PASS | FR-013/014/015 mandate evidence pack + append-only audit; SC-005/SC-012 measure pack completeness and auditor-retrieval time; drift findings flow into the same audit store (FR-019) |
| 5 | V. Warning and Public Information | ✅ PASS (org mode) / ⚠️ PASS-WITH-MITIGATION (user-owned mode) | Pipeline does not emit warnings; CODEOWNERS gate (FR-003) ensures warning-pathway changes get persona review. Under user-owned mode (current — see ADR-029-01), persona review collapses to a single individual (`@johnbilliris`); mitigated by branch-protection "require 2 approving reviews" + the second-collaborator prerequisite (T000a) + ADR reversibility on org migration. |
| 6 | VI. Evacuation Framework | ✅ PASS | Not applicable — infrastructure feature |
| 7 | VII. Recovery Support | ✅ PASS | Not applicable — infrastructure feature |
| 8 | VIII. Cloud Platform and Infrastructure | ✅ PASS | Azure-only; Bicep IaC; GitHub Actions CD; Azure-native services across the board |
| NN-1 | Human-in-the-loop | ✅ PASS | Emergency-hotfix lane requires 2 distinct authorised humans (FR-011a, FR-012); CODEOWNERS gate (FR-003) for safety-critical paths; freeze invocation requires Entra group membership (FR-011) |
| NN-2 | Data sovereignty (AU regions) | ✅ PASS with carve-out | FR-018 + Constitution v1.2.0 carve-out: Foundry model-hosting endpoints permitted outside AU on named, version-controlled list; all data-persisting services remain AU-only; data-minimisation at model gateway; carve-out is auditable |
| NN-3 | Privacy by design | ✅ PASS | `dev` posture relaxation conditional on no real PII in `dev` (Assumption + Constraint sections of spec); leakage treated as high-severity incident; Defender + Entra ID Protection cover dev anomalies (FR-026) |
| NN-4 | Interoperability | ✅ PASS | Pipeline consumes GitHub-native APIs and Azure-native APIs; no proprietary protocols introduced |
| NN-5 | Graceful degradation | ✅ PASS | FR-024 (refuse to advance canary on missing telemetry), Edge Cases cover SLO unavailability, evidence-store outage, CODEOWNERS unavailability |
| QG | Quality Gates | ✅ PASS | FR-001 (full PR gate set), FR-003 (CODEOWNERS for safety-critical), FR-006 (staging gate set), FR-007 (canary burn-rate), FR-019 (drift); evidence pack (FR-013) is the lessons-management input for deploy events |

### Recorded architecture decisions affecting this plan

- **ADR-029-01 — CODEOWNERS reviewer identities under user-owned repository** (research.md §R17). The repository is currently user-owned (`johnbilliris/ama`), which means GitHub team handles (`@org/<team>`) cannot be created or referenced. CODEOWNERS entries that would otherwise resolve to teams resolve to the individual handle `@johnbilliris` instead, and the dual-approver requirement (FR-033) is enforced via branch protection's "require N approving reviews" rather than via team membership. The decision is reversible by text substitution once the repository migrates into a GitHub organisation; the canonical future-state team mapping table lives in research.md §R17. **Constitution impact: NN-1 still PASSES** because the Entra-group-backed authority paths (FR-011, FR-011a) are independent of GitHub teams and remain authoritative for freeze invocation and emergency-hotfix approval.
- **R16 — Dual Azure subscription topology** (research.md §R16). The pipeline supports either Topology A (one subscription per environment) or Topology B (single subscription, one RG per environment); the choice is recorded in `infra/IDENTITY.md`. Bicep at the root accepts a `subscriptionTopology` parameter that switches Azure Policy assignment scope between subscription-level and RG-level. **Constitution impact: NN-2 (data sovereignty), QG (Quality Gates), and the FR-025–FR-029 isolation requirements all PASS under both topologies**, because the IaC policy gate (FR-029) enforces cross-environment-scope blocks regardless of whether "scope" resolves to a subscription or a resource group.

**Initial gate result: PASS — no violations to justify.** Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/029-progressive-delivery-pipeline/
├── spec.md              # Feature specification (clarified, 10/10 questions answered)
├── plan.md              # This file
├── research.md          # Phase 0 — research decisions
├── data-model.md        # Phase 1 — entity model
├── quickstart.md        # Phase 1 — operator quickstart
├── contracts/           # Phase 1 — interface contracts
│   ├── posture-matrix.schema.yaml
│   ├── posture-exceptions.schema.yaml
│   ├── evidence-pack.schema.json
│   ├── audit-event.schema.json
│   ├── dev-key-issue.workflow.yaml
│   └── canary-promotion.api.md
├── checklists/
│   └── requirements.md  # Spec quality checklist (existing)
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root — files this feature evolves)

```text
.github/
├── workflows/
│   ├── ci.yml                      # EVOLVE — PR gate set, sharded, 10-min budget (FR-001, FR-002)
│   ├── cd.yml                      # EVOLVE — build-once + canary 5/25/50/100 (FR-004, FR-005, FR-007)
│   ├── drift-detection.yml         # EVOLVE — adds posture-violation labelling (FR-019, FR-029, FR-031 nightly sweep)
│   ├── dev-key-issue.yml           # NEW — pipeline-managed dev API key issuance (FR-030)
│   ├── change-freeze.yml           # NEW — freeze toggle dispatch (FR-011)
│   ├── emergency-hotfix.yml        # NEW — 2-person approval lane (FR-011a, FR-012)
│   ├── evidence-pack.yml           # NEW — reusable workflow assembling evidence (FR-013, FR-014)
│   ├── posture-exception-sweep.yml # NEW — daily auto-removal of expired exceptions (FR-033)
│   └── _shared/
│       ├── pr-gates.yml            # Reusable PR gate composite
│       ├── canary-stage.yml        # Reusable canary-stage with burn-rate poll
│       └── posture-verify.yml      # Reusable post-deploy verifier (FR-031)
├── CODEOWNERS                      # EVOLVE — security + compliance + SRE + infrastructure + incident-domain personas on safety-critical paths. Handle mode (team vs. user) is governed by ADR-029-01 in research.md §R17 (currently user-owned: `@johnbilliris` placeholder until org migration)

infra/
├── main.bicep                      # EVOLVE — env-parameterised; Azure Policy assignment scope switches on `subscriptionTopology` parameter (`'A'` = sub-scope, `'B'` = RG-scope) per research.md §R16
├── main.parameters.development.json
├── main.parameters.staging.json
├── main.parameters.production.json
├── modules/
│   ├── pipeline-identity.bicep     # NEW — Entra workload identities + federated credentials per env
│   ├── evidence-store.bicep        # NEW — Blob Storage with immutability + legal hold (AU)
│   ├── audit-store.bicep           # EVOLVE — schema-compatible deployment audit container
│   ├── jump-host.bicep             # NEW — Bastion + hardened VM per staging/prod VNet
│   ├── defender-baseline.bicep     # NEW — Defender for Cloud plans + Entra ID Protection wiring (dev)
│   └── posture-policy-set.bicep    # NEW — generated Azure Policy initiative from posture-matrix.yaml
└── policy/                         # NEW — single canonical home for policy artefacts (FR-025)
    ├── posture-matrix.yaml         # NEW — sole source of truth (env × resource-type rules)
    ├── posture-exceptions.yaml     # NEW — named, dual-approved, expiring exceptions (FR-033)
    ├── foundry-carveout.yaml       # NEW — named non-AU Foundry deployment list (FR-018)
    └── rego/                       # NEW — OPA / conftest rules consuming posture-matrix.yaml
        ├── posture.rego
        ├── cross_env.rego
        ├── secret_hygiene.rego
        └── au_region.rego

tools/
└── pipeline/                       # NEW — pipeline-side Python utilities
    ├── posture_verifier.py         # FR-031 full-sweep verifier (Resource Graph join)
    ├── cross_env_check.py          # FR-029 deploy-time Resource Graph check
    ├── evidence_pack_builder.py    # FR-013 assembly; writes to evidence store
    ├── audit_emitter.py            # FR-015 append-only schema-compatible writer
    ├── canary_controller.py        # FR-007 burn-rate poll + traffic shifts
    ├── known_good_index.py         # FR-008 last_known_good_at maintenance
    └── tests/                      # pytest suite for the above

tests/
└── pipeline/                       # NEW — pipeline integration tests (synthetic canary, freeze flow)
    ├── test_canary_rollback.py
    ├── test_evidence_pack.py
    ├── test_posture_verifier.py
    ├── test_cross_env_check.py
    ├── test_dev_key_issue_flow.py
    └── fixtures/                   # Bicep what-if JSON, Resource Graph mocks

apps/                               # NO source-code changes in apps/web, apps/api, apps/agents from this feature
```

**Structure Decision**: Web application monorepo (apps/web + apps/api + apps/agents already in place). This feature evolves cross-cutting infra/CI directories: `.github/workflows/` (gains 5 new + 3 reusable workflows; evolves 3 existing), `infra/` (gains `policy/`, gains 5 new Bicep modules, evolves `main.bicep` and parameter files for env-parameterised RG-scoped policy assignments), and adds two new top-level directories `tools/pipeline/` (Python pipeline utilities, pytest-tested) and `tests/pipeline/` (integration tests for canary/freeze/dev-key flows). The three runtime apps (Next.js web, FastAPI API, Python agents) are unchanged in source — they are *consumers* of the pipeline, not modified by it.

## Complexity Tracking

> No constitutional violations to justify; section intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Phase 0 — Research

See [research.md](./research.md) for the resolved research log. Summary of decisions:

- **OPA + conftest** chosen over Checkov / pure Azure-Policy for the PR-time IaC gate — single Rego ruleset can consume `posture-matrix.yaml` directly and run in < 30 s in CI
- **Cosign + Syft + SLSA-3 GitHub provenance** for build-once / sign / SBOM (FR-004, FR-005)
- **Azure Container Apps revision traffic-split** for service canary; **App Service deployment slots** for web canary (already configured per Assumption)
- **Azure Resource Graph** for both cross-env detection (FR-029 layer 2) and post-deploy posture sweep (FR-031) — single API surface, low rate-limit pressure
- **Microsoft Defender for Cloud + Entra ID Protection** for `dev` anomaly detection (FR-026) — no custom thresholds
- **Cosmos DB `pipeline_state` container** in the existing audit account for canary cursor + freeze flag + known-good index — reuses identity, region, retention configuration
- **Azure Blob Storage with time-based immutability + legal hold** in `australiaeast` for evidence packs — meets 7-year retention with deny-modify (FR-014)
- **Bastion + jump-host + Entra PIM** for staging/prod developer JIT access — no point-to-site VPN, no public endpoints

## Phase 1 — Design & Contracts

Outputs:
- [data-model.md](./data-model.md) — entity definitions, relationships, state transitions
- [contracts/](./contracts/) — schemas and interface contracts (posture matrix, posture exceptions, evidence pack, audit event, `dev-key-issue` workflow inputs/outputs, canary promotion control surface)
- [quickstart.md](./quickstart.md) — operator/developer quickstart (issue a dev key, invoke a freeze, retrieve an evidence pack, add a posture exception)
- Agent context update — run `update-agent-context.ps1 -AgentType copilot`

### Re-evaluated Constitution Check (post-design)

Same matrix as the initial gate. Designed artefacts (posture matrix schema, evidence-pack schema, audit-event schema, dev-key-issue workflow contract) reinforce — and do not weaken — any constitutional obligation. **Post-design gate result: PASS.**

---

**Phase 2 (tasks)** is produced by `/speckit.tasks`, not by this command.
