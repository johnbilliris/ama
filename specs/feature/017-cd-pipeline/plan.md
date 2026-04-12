# Implementation Plan: CD Pipeline with Staging Environment

**Branch**: `feature/017-cd-pipeline` | **Date**: 2025-07-14 | **Spec**: [specs/017-cd-pipeline/spec.md](../../017-cd-pipeline/spec.md)
**Input**: Feature specification from `/specs/017-cd-pipeline/spec.md`

## Summary

Add a Continuous Deployment (CD) pipeline to the disaster response coordination hub that automates deployment to Azure with a staging environment, deployment gates, rollback automation, environment-specific configuration, and infrastructure drift detection. The pipeline is implemented as GitHub Actions workflows (YAML) using Azure Developer CLI (`azd`) for provisioning and deployment, Bicep IaC for infrastructure, and bash scripts for rollback automation. Authentication uses workload identity federation (OIDC) with no stored secrets.

## Technical Context

**Language/Version**: YAML (GitHub Actions workflows), Bash (rollback script), Bicep (IaC parameters), JSON (parameter files)
**Primary Dependencies**: GitHub Actions, Azure Developer CLI (`azd`), Azure CLI (`az`), `pip-audit`, `ruff`, `gh` CLI
**Storage**: N/A (pipeline orchestration — no application data storage)
**Testing**: Pipeline validation via dry-run / what-if; health check verification via HTTP probes
**Target Platform**: GitHub Actions `ubuntu-latest` runner → Azure (australiaeast)
**Project Type**: CI/CD pipeline (DevOps infrastructure-as-code)
**Performance Goals**: Staging deployment < 15 minutes end-to-end; rollback < 5 minutes; gate failure report < 2 minutes
**Constraints**: No CI regression; Australian regions only; OIDC auth only (no stored secrets); single concurrent deployment per environment
**Scale/Scope**: 4 services (api, agents, ingestion, web); 2 environments (staging, production); weekly drift detection

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Requirement | Status | Notes |
|---|-----------|-------------|--------|-------|
| 1 | I. Life Safety First | Rollback plan for any change impacting hazard predictions, evacuation routing, or alert generation | ✅ PASS | FR-004 mandates automated rollback on health failure; FR-012 halts on rollback failure. Rollback script (`scripts/rollback.sh`) is a deliverable. |
| 2 | II. Multi-Agent Coordination | Cross-agent handoffs must be explicit | ✅ PASS | Not directly applicable to pipeline, but deployment deploys all 4 services atomically (all-or-nothing rollback per FR-004, Edge Cases). |
| 3 | III. Data Trust & Provenance | Versioned and reproducible deployments | ✅ PASS | FR-011 records known-good revision; Git SHA tracked per deployment; concurrency groups prevent race conditions. |
| 4 | IV. Privacy & Security | Workload identity federation; no stored secrets; role-based access | ✅ PASS | FR-014 mandates OIDC only; FR-005 requires Key Vault per environment accessed via managed identity; manual approval gate (FR-003) for production. |
| 5 | V. Multilingual Communication | Alerts logged with audience, content, time, channel | ⬜ N/A | Pipeline does not generate public alerts. |
| 6 | VI. Cloud Platform | Azure only; Australian regions only | ✅ PASS | FR-009 mandates australiaeast primary, australiasoutheast failover; all IaC parameterized for location. |
| 7 | NFR: Resilience | Graceful degradation | ✅ PASS | Health check retries (FR-010); rollback on failure (FR-004); critical failure halt (FR-012). |
| 8 | NFR: Audit Trail | Append-only audit trail for safety-critical actions | ✅ PASS | GitHub Actions provides immutable run logs; deployment status recorded via commit status checks; drift findings as GitHub Issues. |
| 9 | NFR: WAF Compliance | Well-Architected Framework | ✅ PASS | Reliability (rollback, health checks), Security (OIDC, environment isolation), Operational Excellence (automated deployment, drift detection). |
| 10 | Quality Gates | Rollback plan, offline evaluation, documented change summary | ✅ PASS | Deployment gates (FR-002) enforce quality before promotion; rollback (FR-004) is automated; gate failure reports (SC-008) document findings. |

**Gate Result**: ✅ ALL PASS — No constitution violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/feature/017-cd-pipeline/
├── plan.md              # This file
├── research.md          # Phase 0: Research findings
├── data-model.md        # Phase 1: Entity model
├── quickstart.md        # Phase 1: Setup guide
├── contracts/           # Phase 1: Workflow interface contracts
│   ├── cd-workflow.md
│   ├── drift-detection-workflow.md
│   └── rollback-script.md
└── tasks.md             # Phase 2 output (not created by plan)
```

### Source Code (repository root)

```text
.github/
└── workflows/
    ├── ci.yml                          # EXISTING — not modified
    ├── cd.yml                          # NEW — CD pipeline workflow
    └── drift-detection.yml             # NEW — Weekly drift detection

scripts/
    ├── seed-database.sh                # EXISTING
    ├── seed-database.ps1               # EXISTING
    └── rollback.sh                     # NEW — Automated rollback script

infra/
    ├── main.bicep                      # EXISTING — not modified
    ├── main.parameters.json            # EXISTING — not modified
    ├── main.parameters.staging.json    # NEW — Staging env parameters
    └── main.parameters.production.json # NEW — Production env parameters
```

**Structure Decision**: This feature adds DevOps infrastructure files alongside existing codebase structure. No application source code changes. All new files are in `.github/workflows/`, `scripts/`, and `infra/` — all existing directories. The pattern follows the existing `ci.yml` workflow and `main.parameters.json` parameter file conventions.

## Complexity Tracking

> No constitution violations to justify. All deliverables align with existing project patterns.
