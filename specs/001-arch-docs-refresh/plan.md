# Implementation Plan: Comprehensive Architectural Documentation & Diagrams Refresh

**Branch**: `001-arch-docs-refresh` | **Date**: 2026-05-11 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/001-arch-docs-refresh/spec.md`

## Summary

Deliver a navigable, CI-validated architecture documentation set for the AMA platform covering all
persona clusters (Operational/Sector/Technical-Architecture/Build/Quality/Experience). The set
comprises 32 diagram pairs (`.drawio` + PNG, post-Amendment 1), ~35 Markdown pages organised under
`docs/architecture/` by view type, two Python lint scripts, and a new `docs-arch` CI job. Every
shipped spec (001–037, excluding confirmed archived/duplicate numbers) is cross-referenced from at
least one architecture page. Toolchain: Draw.io desktop + `drawio-mcp-diagramming` skill; staleness
detection via SHA256 hash manifest; CI link-checking via `lychee`; markdownlint via `npx`.

## Technical Context

**Language/Version**: Python 3.12 (lint scripts); Markdown/Draw.io XML (documentation artefacts)  
**Primary Dependencies**: Draw.io desktop ≥ 24.x; `drawio-mcp-diagramming` project skill (MCP);
  `markdownlint-cli2` (npx, no permanent devDependency); `lychee` (apt/binary in CI runner);
  `sha256sum` / PowerShell `Get-FileHash` (contributor toolchain)  
**Storage**: Git repository file system — `docs/architecture/` (Markdown + Draw.io XML + PNG)  
**Testing**: `docs-arch` CI job (markdownlint, lychee, find one-liners, sha256sum, Python scripts);
  manual navigation review against US1–US7 independent tests  
**Target Platform**: GitHub repository; GitHub Actions `ubuntu-latest`  
**Project Type**: Documentation-as-code (static Markdown + diagram source files)  
**Performance Goals**: `docs-arch` CI job completes within 10 minutes; new-joiner orientation
  question answerable within 60 minutes (SC-001)  
**Constraints**: Zero broken internal links (FR-021b); zero PNGs without sibling `.drawio` (FR-021a);
  zero un-cited spec numbers 001–037 (FR-021c); SHA256 manifest mismatch fails build (FR-021d);
  markdownlint zero violations against `.markdownlint.jsonc` (FR-022)  
**Scale/Scope**: 32 diagram pairs (post-Amendment 1); ~35 architecture pages; 37 spec cross-refs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

This feature is **documentation-only** — it produces no application code, no new APIs, no data
stores, and no changes to the production system. All constitution gates pass:

| Gate | Status | Notes |
|------|--------|-------|
| AU data residency | ✅ PASS | No data-plane changes; SEC-01 diagram documents the existing boundary |
| Human-in-the-loop | ✅ PASS | FR-009/FR-013 mandate marking human gates on actuation diagrams |
| Auditability | ✅ PASS | Hash manifest + known-gaps registry + spec cross-refs provide full provenance |
| Quality gates | ✅ PASS | `docs-arch` CI job enforces all mechanical checks; manual review for content |
| Complexity | ✅ PASS | No new projects, repositories, or architectural layers introduced |

**Post-design re-check (Amendment 1)**: Amendment adds 6 diagrams and 1 new view-type subdir
(`quality/`). Documentation-only; all gates continue to pass. No violations.

## Project Structure

### Specification artefacts

```text
specs/001-arch-docs-refresh/
├── plan.md           ← this file
├── research.md       ← Phase 0 output
├── data-model.md     ← Phase 1 output
├── quickstart.md     ← Phase 1 output (contributor guide)
├── contracts/
│   ├── diagram-manifest-format.md
│   ├── known-gaps-schema.md
│   └── lint-scripts.md
└── tasks.md          ← Phase 2 output (/speckit.tasks)
```

### Source artefacts (repository root)

```text
docs/architecture/
├── README.md                         ← top-level index (FR-001, FR-002)
├── .diagram-hashes                   ← SHA256 manifest (FR-021d)
├── known-gaps.md                     ← Known-gaps registry (FR-023)
│
├── c4/                               ← C4 Architecture views
│   ├── system.md + system.drawio + system.png          (C4-L1)
│   ├── container.md + container.drawio + container.png (C4-L2)
│   ├── component-api.md + *.drawio + *.png             (C4-L3-API)
│   ├── component-web.md + *.drawio + *.png             (C4-L3-Web)
│   ├── component-agents.md + *.drawio + *.png          (C4-L3-Agents)
│   ├── component-ingest.md + *.drawio + *.png          (C4-L3-Ingest)
│   └── agent-llm-gateway.md + *.drawio + *.png         (BUILD-01 — Amendment 1)
│
├── sequence/                         ← Sequence flow views
│   ├── monitoring-risk-comms.md      (pre-existing, front-matter updated)
│   ├── alert-approval-publication.*  (SEQ-01)
│   ├── cross-agency-recommendation.* (SEQ-02)
│   ├── evacuation-five-stage.*       (SEQ-03)
│   ├── recovery-transition.*         (SEQ-04)
│   ├── audit-trail-provenance.*      (SEQ-05)
│   └── graceful-degradation.*        (SEQ-06)
│
├── operational/                      ← AIIMS operational views
│   ├── aiims-system-context.*        (OPS-01)
│   ├── escalation-paths.*            (OPS-02)
│   ├── hazard-risk-register.*        (RISK-01 — Amendment 1)
│   └── pprr-phase-overlay.*          (OPS-03 — Amendment 1)
│
├── data/                             ← Data & sector views
│   ├── multi-jurisdiction-tenancy.*  (SECTOR-01)
│   ├── ingestion-data-flow.*         (SECTOR-02)
│   ├── integration-point-map.*       (SECTOR-03)
│   ├── jurisdiction-filter.*         (SECTOR-04)
│   └── cross-sector-touchpoints.*    (SECTOR-05 — Amendment 1)
│
├── security/                         ← Security & compliance views
│   ├── au-residency-data-classification.* (SEC-01)
│   ├── rbac-role-permission-matrix.*      (SEC-02)
│   ├── trust-boundary.*                   (SEC-03)
│   └── sli-slo-model.*                    (SEC-04)
│
├── deployment/                       ← Deployment & infrastructure views
│   ├── cicd-pipeline.*               (DEPLOY-01)
│   ├── azure-resource-topology.*     (DEPLOY-02)
│   └── cosmos-partitioning.*         (DEPLOY-03)
│
├── governance/                       ← Governance & WAF views
│   ├── waf-pillar-mapping.*          (GOV-01)
│   └── adr/README.md                 (ADR navigation index)
│
├── quality/                          ← Quality views (NEW — Amendment 1)
│   └── test-pyramid.*                (QUAL-01 — Amendment 1)
│
└── accessibility/                    ← Experience & accessibility views
    ├── wcag-coverage.md              (text-only; no diagram pair)
    └── ops-dashboard-user-journey.*  (EXP-01 — Amendment 1)

tools/lint/
├── check_spec_cross_refs.py          ← spec citation coverage (FR-021c)
└── check_known_gaps.py               ← known-gaps registry completeness (FR-023)

.github/workflows/ci.yml              ← docs-arch job added (FR-021, FR-022)
```

**Structure Decision**: View-type subdirectory layout extending the pre-existing `c4/` and
`sequence/` convention. Persona-cluster navigation expressed via `README.md` index, not directory
structure (spec clarification Q2 Session 2026-05-11). `quality/` added by Amendment 1.

## Diagram Inventory (32 pairs — post-Amendment 1)

| # | ID | Title | Subdir | FR(s) |
|---|----|----|---|---|
| 1 | C4-L1 | System Context | `c4/` | FR-004 |
| 2 | C4-L2 | Container | `c4/` | FR-004 |
| 3 | C4-L3-API | Component: API (FastAPI) | `c4/` | FR-004 |
| 4 | C4-L3-Web | Component: Web (Next.js) | `c4/` | FR-004 |
| 5 | C4-L3-Agents | Component: Agents Runtime | `c4/` | FR-004 |
| 6 | C4-L3-Ingest | Component: Ingest Service | `c4/` | FR-004 |
| 7 | SEQ-01 | Alert Authoring → Approval → Publication | `sequence/` | FR-009, FR-010(a) |
| 8 | SEQ-02 | Cross-Agency Recommendation → Approval | `sequence/` | FR-009, FR-010(b) |
| 9 | SEQ-03 | Evacuation Five-Stage Flow | `sequence/` | FR-009, FR-010(c) |
| 10 | SEQ-04 | Recovery Transition | `sequence/` | FR-010(d) |
| 11 | SEQ-05 | Audit-Trail Provenance Flow | `sequence/` | FR-010(e), FR-020 |
| 12 | SEQ-06 | Graceful-Degradation Behaviour | `sequence/` | FR-010(f) |
| 13 | OPS-01 | AIIMS System Context (all 10 roles) | `operational/` | FR-013 |
| 14 | OPS-02 | Escalation Paths (L1 → L2 → L3) | `operational/` | FR-013 |
| 15 | SECTOR-01 | Multi-Jurisdiction Tenancy | `data/` | FR-015 |
| 16 | SECTOR-02 | Ingestion Data-Flow | `data/` | FR-014 |
| 17 | SECTOR-03 | Integration-Point Map | `data/` | FR-014 |
| 18 | SECTOR-04 | Jurisdiction-Filter Behaviour | `data/` | FR-015 |
| 19 | SEC-01 | AU-Residency & Data-Classification | `security/` | FR-016 |
| 20 | SEC-02 | RBAC Role/Permission Matrix | `security/` | FR-017 |
| 21 | SEC-03 | Trust-Boundary Diagram | `security/` | FR-018 |
| 22 | SEC-04 | SLI/SLO Model | `security/` | FR-019 |
| 23 | DEPLOY-01 | CI/CD Pipeline | `deployment/` | US6 |
| 24 | DEPLOY-02 | Azure Resource Topology | `deployment/` | US6 |
| 25 | DEPLOY-03 | Cosmos DB Partitioning Scheme | `deployment/` | US6 |
| 26 | GOV-01 | WAF Pillar Mapping | `governance/` | FR-004 |
| 27 | RISK-01 | Hazard Taxonomy + Risk-Register Lifecycle | `operational/` | FR-013 (ext.) — **Amd 1** |
| 28 | OPS-03 | PPRR Phase-Overlay (agents × AIIMS roles) | `operational/` | FR-024 — **Amd 1** |
| 29 | SECTOR-05 | Cross-Sector Touch-Points & Partner Data Exchange | `data/` | FR-015 (ext.) — **Amd 1** |
| 30 | BUILD-01 | Agent Runtime + LLM Client + Model Gateway | `c4/` | FR-014 (ext.) — **Amd 1** |
| 31 | QUAL-01 | Test Pyramid (5-tier: unit/contract/integration/simulation/e2e) | `quality/` | FR-025 — **Amd 1** |
| 32 | EXP-01 | High-Pressure Ops Dashboard User-Journey | `accessibility/` | FR-026 — **Amd 1** |

## Complexity Tracking

No constitution violations. Table omitted per instruction ("Fill ONLY if Constitution Check has violations").

---

## Amendment 1 (2026-05-11)

**Source**: spec.md Amendment 1 (FR-024, FR-025, FR-026); spec clarification session 2026-05-11 (Amendment 1) Q1–Q3.  
**Nature**: Documentation-only addition of 6 diagram pairs across existing and one new persona cluster. No code changes. No new CI gates (Amendment 1 Q2 confirmed all 6 new FRs are mechanically covered by the existing `docs-arch` checks).

### New Diagrams

| ID | Title | Subdir | FR | Persona Cluster | Notes |
|----|-------|--------|----|----------------|-------|
| RISK-01 | Hazard Taxonomy + Risk-Register Lifecycle | `docs/architecture/operational/` | FR-013 extension | Operational — Risk Manager | Shows hazard classification taxonomy and risk-register state machine (Open → Mitigated → Closed); sits alongside OPS-01/OPS-02 in the `operational/` subdir |
| OPS-03 | PPRR Phase-Overlay | `docs/architecture/operational/` | FR-024 (new) | Operational — Resilience Planner | Sourced from constitution §PPRR Lifecycle; shows which platform agents and AIIMS roles activate in each PPRR phase (Prevention / Preparedness / Response / Recovery) including phase-overlap regions |
| SECTOR-05 | Cross-Sector Touch-Points & Partner Data Exchange | `docs/architecture/data/` | FR-015 extension | Sector — Cross-Sector | Extends the sector cluster alongside SECTOR-01–04 in `data/`; shows partner agency data exchange patterns across sector boundaries |
| BUILD-01 | Agent Runtime + LLM Client + Model Gateway | `docs/architecture/c4/` | FR-014 extension | Technical-Build — AI/ML | Integrated view of the 5-agent runtime, LLM client library, and model gateway; placed in `c4/` as a C4 component-layer view rather than creating a one-diagram `build/` subdir (minimum viable directory surface principle) |
| QUAL-01 | Test Pyramid (5-tier) | `docs/architecture/quality/` ← **NEW subdir** | FR-025 (new) | Technical-Quality — QA | Five tiers: unit (base, ~159 files) → contract → integration → simulation → e2e (apex); primary tooling per tier: pytest for unit/contract/integration/simulation/backend-e2e; Playwright for web e2e; simulation harness for simulation. Secondary tiers (benchmark, load, security, chaos) MAY appear as supplementary lanes. FR-025 corrected from "four-tier" to "five-tier" (Amendment 1 Q3) |
| EXP-01 | High-Pressure Ops Dashboard User-Journey | `docs/architecture/accessibility/` | FR-026 (new) | Technical-Experience — UX/PO | Traces one canonical user-journey through the dashboard during an active incident; callouts cover perception/comprehension/action steps and success-criteria → architecture component traceability at each step; placed in `accessibility/` per Technical-Experience = accessibility + WCAG + end-user interaction (spec clarification Q1 Session 2026-05-11) |

### New Subdirectory

`docs/architecture/quality/` — created for QUAL-01. No other diagrams currently planned for this subdir; `.gitkeep` added alongside the first committed diagram pair. `quality/` was anticipated by the "additional subdirectories as needed" clause in spec Assumptions.

### Tooling Reuse

All 6 new diagrams follow the **existing diagram-pair contract** (`contracts/diagram-manifest-format.md`):

- Authored via Draw.io desktop ≥ 24.x or `drawio-mcp-diagramming` skill (RQ-01)
- PNG exported at 150 DPI, white background, same base name, same subdir
- SHA256 hash manifest updated after each export (RQ-02 / quickstart.md Step 4)
- No new CI gates required (Amendment 1 Q2): all 6 diagrams are validated by the existing `docs-arch` checks (PNG/drawio pairing, hash manifest, markdownlint, lychee, spec cross-ref, known-gaps)
- No new contracts files: all 6 diagram pairs use the existing `contracts/diagram-manifest-format.md` contract without modification

### SC-007 Impact

SC-007 inventory updated from 26 to **32 diagrams** (as noted in spec.md Amendment 1). The `docs-arch` CI count gate checks the total against the named inventory. Any of the 6 new diagrams that cannot be completed must be added to `docs/architecture/known-gaps.md` with a non-TBD follow-up task reference.
