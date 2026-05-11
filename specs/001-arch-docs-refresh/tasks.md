# Tasks: Comprehensive Architectural Documentation & Diagrams Refresh

**Feature**: `001-arch-docs-refresh`  
**Input**: `specs/001-arch-docs-refresh/` — plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md  
**Generated**: 2026-05-11  
**Tests**: Not requested — documentation-only feature; acceptance validated by CI `docs-arch` job and manual navigation review (spec US1–US7 independent tests).

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Task can run in parallel with other `[P]` tasks in the same phase (distinct output files; no dependency on incomplete sibling tasks)
- **[Story]**: User story this task belongs to (US1–US7 from spec.md)
- **Diagram tasks**: Each covers `.drawio` authoring via `drawio-mcp-diagramming` skill + PNG export (150 DPI, white background) + SHA256 manifest entry update in `docs/architecture/.diagram-hashes`
- **[P] tasks listed first within each phase** to maximise parallel execution

---

## Phase 1: Setup

**Purpose**: Scaffold all new directories and prime the hash manifest before any authoring begins.

- [X] T001 Create new subdirectory scaffold: `docs/architecture/operational/`, `docs/architecture/data/`, `docs/architecture/security/`, `docs/architecture/deployment/`, `docs/architecture/governance/`, `docs/architecture/accessibility/`, `docs/architecture/adr/`, and `tools/lint/` (add `.gitkeep` in each empty dir so they track in git; per plan.md Project Structure)
- [X] T002 [P] Initialize `docs/architecture/.diagram-hashes` empty manifest file with a format comment header (`# sha256hex  relative/path/to/file.drawio`; two-space separator; entries will be sorted lexicographically by path; per `contracts/diagram-manifest-format.md`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish lint baseline, seed the known-gaps registry (escape valve for CI cross-ref check), and confirm the manifest is ready. **All user story diagram authoring is blocked until this phase completes.**

⚠️ **CRITICAL**: No diagram authoring can begin until T003 (lint pre-flight) exits 0 and T004 (known-gaps seed) is committed — the known-gaps exclusion list is read by `check_spec_cross_refs.py` at CI time.

- [X] T003 [P] Lint pre-flight — run `npx markdownlint-cli2 "docs/architecture/**/*.md"` against the six pre-existing `.md` files (`c4/system.md`, `c4/container.md`, `sequence/monitoring-risk-comms.md`, `capacity-model.md`, `cosmos-partitioning.md`, `spec-035-middleware-and-offline.md`) to confirm zero baseline violations before diagram authoring begins; fix any pre-existing rule violations before proceeding
- [X] T004 [P] Seed `docs/architecture/known-gaps.md` with the 11 initial registry entries below (Markdown table; columns: Area/Spec | Gap Description | Follow-up Task Ref | Date Identified | Status; **every row must have a non-TBD Follow-up Task Ref per FR-023**):

  | Area/Spec | Gap Description | Follow-up Task Ref | Date Identified | Status |
  |-----------|----------------|-------------------|----------------|--------|
  | BICEP-DEP-01 | Bicep module dependency graph deferred; requires auto-generation tooling from `infra/bicep/`; not hand-authored | https://github.com/johnbilliris/ama/issues/new?title=BICEP-DEP-01+Bicep+module+dependency+graph | 2026-05-11 | Open |
  | DUPE-036 | Two `036-*` spec directories observed; counted as one shipped spec for cross-ref purposes; deduplication handled by `check_spec_cross_refs.py` prefix logic | `tasks.md#T061` | 2026-05-11 | Open |
  | CAP-MIG-01 | `capacity-model.md` at repo root not yet migrated to `deployment/` or `governance/` subdir; kept in place with front-matter banner per FR-005 | `tasks.md#T067` | 2026-05-11 | Open |
  | COSM-MIG-01 | Root-level `cosmos-partitioning.md` not yet migrated; superseded by `deployment/cosmos-partitioning.md` (T060); root copy kept with redirect banner | `tasks.md#T068` | 2026-05-11 | Open |
  | MDW-MIG-01 | Root-level `spec-035-middleware-and-offline.md` not yet migrated to a named view-type subdir; kept with front-matter banner per FR-005 | `tasks.md#T069` | 2026-05-11 | Open |
  | FOUNDRY-REGION | Specific non-AU Foundry inference regions not hard-coded in SEC-01 diagram; mechanism-zone label used per FR-016 and constitution NN-2; registry at `infra/parameters/foundry-carveout.yaml` is authoritative | `tasks.md#T044` | 2026-05-11 | Open |
  | SPEC-037 | spec-037 has no confirmed architecture page home; to be mapped during implementation or formally archived if no matching component exists | `tasks.md#T064` | 2026-05-11 | Open |
  | C4-L4 | C4 Level 4 (Code) diagrams deferred; to be added only if L3 Component diagrams lack sufficient clarity for any container; per spec assumption | `tasks.md#T071` | 2026-05-11 | Open |
  | LYCHEE-CFG | `.lychee.toml` exclude patterns for spec deep-link anchor fragments not yet authored; RSK-03 mitigation pending; lychee may emit false positives on `specs/036-*/spec.md#fr-*` anchors | `tasks.md#T063` | 2026-05-11 | Open |
  | WCAG-AUDIT-FULL | WCAG coverage map limited to documenting already-implemented accessibility features; full independent audit deferred to a separate accessibility sprint per RQ-10 | `tasks.md#T054` | 2026-05-11 | Open |
  | SPEC-RANGE-VERIFY | Spec numbers 002–009, 011–014, 016, 018, 021, 023, 026–027, 031–034 require verified architecture citation homes; RSK-06 mitigation — if `check_spec_cross_refs.py` reports any missing after Phase 10, add individual known-gaps entries per spec | `tasks.md#T064` | 2026-05-11 | Open |

- [X] T005 Verify `docs/architecture/.diagram-hashes` readiness: confirm file exists and `sha256sum --check docs/architecture/.diagram-hashes` exits 0 with 0 entries; document baseline in commit message — this is the pre-diagram-authoring gate

**Checkpoint**: Directories scaffolded, known-gaps seeded, lint baseline clean, manifest initialized → diagram authoring may begin in parallel across all phases.

---

## Phase 3: User Story 1 — New Joiner Architecture Orientation (Priority: P1) 🎯 MVP

**Goal**: Deliver the top-level index and the two evacuation/recovery sequence diagrams so a new joiner can answer the four orientation questions within 60 minutes of opening `docs/architecture/README.md`.

**Independent Test**: Check out the branch; open `docs/architecture/README.md` in a browser. Every linked page and diagram must load without a 404. All PNGs must be present with matching `.drawio` siblings. No other guidance should be needed for a person familiar with AIIMS and Azure to identify the human-in-the-loop path.

**[P]-eligible tasks first:**

- [X] T006 [P] [US1] Author diagram pair SEQ-03 (Evacuation Five-Stage Flow): `docs/architecture/sequence/evacuation-five-stage.drawio` + `evacuation-five-stage.png` via `drawio-mcp-diagramming` skill — five evacuation stages; **FR-009 mandatory**: human approval gate marker (yellow swim-lane labelled "👤 Human Approval Gate" or equivalent distinct callout) on the actuation step; 150 DPI PNG, white `#FFFFFF` background; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T007 [P] [US1] Author diagram pair SEQ-04 (Recovery Transition): `docs/architecture/sequence/recovery-transition.drawio` + `recovery-transition.png` via `drawio-mcp-diagramming` skill — recovery phase transitions from response to recovery to normalisation; 150 DPI PNG, white background; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T008 [US1] Author markdown page `docs/architecture/sequence/evacuation-five-stage.md` using `quickstart.md` page template — purpose statement: answers "where does a human gate the loop during evacuation?"; persona clusters: Operational; spec refs: `spec-010`, `spec-019`; embeds `evacuation-five-stage.png`; FR-009, FR-010c; `[→ Architecture index](../README.md)` banner
- [X] T009 [US1] Author markdown page `docs/architecture/sequence/recovery-transition.md` — purpose statement; persona clusters: Operational; spec refs: `spec-010`, `spec-019`; embeds `recovery-transition.png`; FR-010d; index banner
- [X] T010 [US1] Author `docs/architecture/README.md` top-level index (FR-001, FR-002) — six persona cluster sections (Operational / Sector / Technical-Architecture / Technical-Build / Technical-Quality / Technical-Experience); a link to every one of the 26 diagram pages + `known-gaps.md` + `adr/README.md`; one-sentence purpose statement per section; `spec-cross-ref` HTML comment annotations covering spec-001 through spec-037 (ensures `check_spec_cross_refs.py` passes); sections may use placeholder `[forthcoming]` links for diagrams not yet authored in later phases — finalise all links in T071 lint post-flight

**Checkpoint**: `docs/architecture/README.md` loads; SEQ-03 and SEQ-04 diagrams and pages render; US1 acceptance tests 1 and 3 can be manually validated.

---

## Phase 4: User Story 2 — Operational Persona: Incident Commander Situational Awareness (Priority: P1)

**Goal**: Deliver the five operational diagrams (SEQ-01, SEQ-02, SEQ-06, OPS-01, OPS-02) and their pages so an Incident Commander can trace alert-authoring → approval → publication, the L1→L3 escalation path, and graceful-degradation behaviour from a single diagram each.

**Independent Test**: Open `docs/architecture/sequence/alert-approval-publication.md`. The human approval checkpoint must be explicitly marked on the diagram with no source code required. Every AIIMS role must appear as a named actor in the AIIMS system-context diagram.

**[P]-eligible tasks first:**

- [X] T011 [P] [US2] Author diagram pair SEQ-01 (Alert Authoring → Human Approval → Publication): `docs/architecture/sequence/alert-approval-publication.drawio` + `alert-approval-publication.png` via `drawio-mcp-diagramming` skill — three stages: authoring, human approval, publication; **FR-009 mandatory**: human approval step must be in a distinct swim-lane or use a red-bordered hexagon labelled "👤 Human Approval Gate"; publication step must appear only after approval step; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T012 [P] [US2] Author diagram pair SEQ-02 (Cross-Agency Recommendation → Approval → Execution): `docs/architecture/sequence/cross-agency-recommendation.drawio` + `cross-agency-recommendation.png` via `drawio-mcp-diagramming` skill — **FR-009 mandatory**: human approval gate before execution; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T013 [P] [US2] Author diagram pair SEQ-06 (Graceful-Degradation Behaviour): `docs/architecture/sequence/graceful-degradation.drawio` + `graceful-degradation.png` via `drawio-mcp-diagramming` skill — for each named subsystem shown as unavailable: which capabilities degrade, which remain operational, which fallback paths activate; FR-010f; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T014 [P] [US2] Author diagram pair OPS-01 (AIIMS System Context — 10 roles × system): `docs/architecture/operational/aiims-system-context.drawio` + `aiims-system-context.png` via `drawio-mcp-diagramming` skill — all 10 AIIMS functional roles as named actors (Incident Commander, Operations, Planning, Logistics, Public Information, Field Coordinator, Resilience Planner, Executive Leader, Observer/Auditor, Risk Manager); each role has ≥1 interaction line to a system component; FR-013; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T015 [P] [US2] Author diagram pair OPS-02 (Escalation Paths L1→L2→L3): `docs/architecture/operational/escalation-paths.drawio` + `escalation-paths.png` via `drawio-mcp-diagramming` skill — each level transition shows: triggering condition, responsible AIIMS role, resulting system action; FR-013; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T016 [US2] Author markdown page `docs/architecture/sequence/alert-approval-publication.md` — purpose: "answers the alert authoring → human approval → publication sequence end-to-end"; persona clusters: Operational; spec refs: `spec-010`; embeds `alert-approval-publication.png`; FR-009, FR-010a; index banner
- [X] T017 [US2] Author markdown page `docs/architecture/sequence/cross-agency-recommendation.md` — persona clusters: Operational; spec refs: `spec-010`, `spec-019`; embeds `cross-agency-recommendation.png`; FR-009, FR-010b; index banner
- [X] T018 [US2] Author markdown page `docs/architecture/sequence/graceful-degradation.md` — persona clusters: Operational; spec refs: `spec-010`; embeds `graceful-degradation.png`; FR-010f; index banner
- [X] T019 [US2] Author markdown page `docs/architecture/operational/aiims-system-context.md` — persona clusters: Operational; spec refs: `spec-019`; embeds `aiims-system-context.png`; FR-013; include named-role Key Elements list (all 10); index banner
- [X] T020 [US2] Author markdown page `docs/architecture/operational/escalation-paths.md` — persona clusters: Operational; spec refs: `spec-019`; embeds `escalation-paths.png`; FR-013; index banner

**Checkpoint**: All five operational diagrams and pages present; SEQ-01 human-gate visible; OPS-01 shows all 10 AIIMS roles; US2 acceptance tests 1–4 can be manually validated.

---

## Phase 5: User Story 3 — Sector Persona: Multi-Jurisdiction Data Isolation (Priority: P2)

**Goal**: Deliver the four data/sector diagrams (SECTOR-01 through SECTOR-04) and pages so a NSW RFS or VIC CFA officer can trace tenant isolation, data flow from ingestion to agent, and cross-state hand-off rules from single diagrams.

**Independent Test**: Open `docs/architecture/data/multi-jurisdiction-tenancy.md`. The NSW and VIC tenant isolation boundary, Cosmos DB partition key alignment, and lead-agency designation mechanism must each be visible on the single diagram without opening source code.

**[P]-eligible tasks first:**

- [X] T021 [P] [US3] Author diagram pair SECTOR-01 (Multi-Jurisdiction Tenancy): `docs/architecture/data/multi-jurisdiction-tenancy.drawio` + `multi-jurisdiction-tenancy.png` via `drawio-mcp-diagramming` skill — all 8 state/territory jurisdictions (NSW, VIC, QLD, SA, WA, TAS, ACT, NT) + Commonwealth; tenant isolation boundary per jurisdiction; Cosmos DB partition key alignment (Azure stencil for Cosmos DB); lead-agency designation mechanism; FR-015; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T022 [P] [US3] Author diagram pair SECTOR-02 (Ingestion Data-Flow): `docs/architecture/data/ingestion-data-flow.drawio` + `ingestion-data-flow.png` via `drawio-mcp-diagramming` skill — CAP/EDXL/GeoJSON signals from external feeds → Event Hubs or Service Bus → Cosmos DB → agent consumer; Azure stencils for Event Hubs, Service Bus, Cosmos DB; all traceable on one diagram; FR-014; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T023 [P] [US3] Author diagram pair SECTOR-03 (Integration-Point Map): `docs/architecture/data/integration-point-map.drawio` + `integration-point-map.png` via `drawio-mcp-diagramming` skill — every named external system: BoM weather (XML/CAP), GA seismic (GeoJSON), NEMA NCM (EDXL), agency CAP/EDXL sources; data format per system; ingestion endpoint receiving it; agent(s) that consume it; FR-014; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T024 [P] [US3] Author diagram pair SECTOR-04 (Jurisdiction-Filter Behaviour): `docs/architecture/data/jurisdiction-filter.drawio` + `jurisdiction-filter.png` via `drawio-mcp-diagramming` skill — cross-state hand-off example: RFS suppresses → SES recovery → local-gov welfare; filter rules and authority boundary at each transition; **must cite spec-022** (jurisdiction filter spec); FR-015; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T025 [US3] Author markdown page `docs/architecture/data/multi-jurisdiction-tenancy.md` — persona clusters: Sector; spec refs: `spec-015`, `spec-022`; embeds `multi-jurisdiction-tenancy.png`; FR-015; index banner
- [X] T026 [US3] Author markdown page `docs/architecture/data/ingestion-data-flow.md` — persona clusters: Sector, Technical-Architecture; spec refs: `spec-010`, `spec-014`; embeds `ingestion-data-flow.png`; FR-014; index banner
- [X] T027 [US3] Author markdown page `docs/architecture/data/integration-point-map.md` — persona clusters: Sector; spec refs: `spec-014`; embeds `integration-point-map.png`; FR-014; index banner
- [X] T028 [US3] Author markdown page `docs/architecture/data/jurisdiction-filter.md` — persona clusters: Sector; spec refs: `spec-022`; embeds `jurisdiction-filter.png`; FR-015; include `<!-- spec-cross-ref: spec-022 -->` annotation; index banner

**Checkpoint**: All four data/sector diagrams and pages present; SECTOR-01 shows 8+1 jurisdictions; SECTOR-04 cites spec-022; US3 acceptance tests 1–4 can be manually validated.

---

## Phase 6: User Story 4 — Technical Persona: Architecture Cluster — Full C4 Model (Priority: P2)

**Goal**: Deliver the complete 6-diagram C4 model (L1–L3 for all four containers), the WAF pillar mapping, and the ADR navigation index so a Solution Architect can navigate from System Context to any Component view without leaving `docs/architecture/`.

**Independent Test**: Navigate from `c4/system.md` (L1) → `c4/container.md` (L2) → each of the four component pages (L3) without leaving `docs/architecture/`. Every application listed in the Container view must have a corresponding Component page.

**[P]-eligible tasks first:**

- [X] T029 [P] [US4] Author diagram pair C4-L1 (System Context): `docs/architecture/c4/system.drawio` + `system.png` via `drawio-mcp-diagramming` skill — external systems visible: BoM weather feed, GA seismic feed, NEMA NCM, state agency CAP/EDXL sources, browser/mobile end-user client; Azure stencils for Azure services; FR-004; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T030 [P] [US4] Author diagram pair C4-L2 (Container): `docs/architecture/c4/container.drawio` + `container.png` via `drawio-mcp-diagramming` skill — all deployed containers: API (FastAPI), Web (Next.js), Agents Runtime (all 5 named agents), Ingest Service; all backing services: Cosmos DB, Azure AI Search, Service Bus, Event Hubs, Application Insights, Key Vault, Azure OpenAI/Foundry; Azure stencils; FR-004; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T031 [P] [US4] Author diagram pair C4-L3-API (Component: API FastAPI): `docs/architecture/c4/component-api.drawio` + `component-api.png` via `drawio-mcp-diagramming` skill — internal FastAPI components; request path from container boundary to internal handler; FR-004; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T032 [P] [US4] Author diagram pair C4-L3-Web (Component: Web Next.js): `docs/architecture/c4/component-web.drawio` + `component-web.png` via `drawio-mcp-diagramming` skill — Next.js frontend components; page/component hierarchy; FR-004; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T033 [P] [US4] Author diagram pair C4-L3-Agents (Component: Agents Runtime — 5 agents): `docs/architecture/c4/component-agents.drawio` + `component-agents.png` via `drawio-mcp-diagramming` skill — all 5 named agent types as labelled components; agent-to-service relationships; FR-004; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T034 [P] [US4] Author diagram pair C4-L3-Ingest (Component: Ingest Service): `docs/architecture/c4/component-ingest.drawio` + `component-ingest.png` via `drawio-mcp-diagramming` skill — Ingest service internal components; inbound adapter per format (CAP, EDXL, GeoJSON); FR-004; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T035 [P] [US4] Author diagram pair GOV-01 (WAF Pillar Mapping): `docs/architecture/governance/waf-pillar-mapping.drawio` + `waf-pillar-mapping.png` via `drawio-mcp-diagramming` skill — all 5 WAF pillars (Reliability, Security, Cost Optimisation, Operational Excellence, Performance Efficiency) × architecture components × spec citations; FR-004; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T036 [P] [US4] Author markdown page `docs/architecture/c4/component-api.md` — persona clusters: Technical-Architecture; spec refs: `spec-001`, `spec-010`; embeds `component-api.png`; FR-004; index banner; Related Pages links to `system.md`, `container.md`
- [X] T037 [P] [US4] Author markdown page `docs/architecture/c4/component-web.md` — persona clusters: Technical-Architecture, Technical-Experience; spec refs: `spec-020`; embeds `component-web.png`; FR-004; index banner
- [X] T038 [P] [US4] Author markdown page `docs/architecture/c4/component-agents.md` — persona clusters: Technical-Architecture; spec refs: `spec-024`, `spec-025`, `spec-030`; embeds `component-agents.png`; FR-004; index banner
- [X] T039 [P] [US4] Author markdown page `docs/architecture/c4/component-ingest.md` — persona clusters: Technical-Architecture; spec refs: `spec-035`; embeds `component-ingest.png`; FR-004; index banner
- [X] T040 [P] [US4] Author markdown page `docs/architecture/governance/waf-pillar-mapping.md` — persona clusters: Technical-Quality; spec refs: `spec-015`, `spec-028`; embeds `waf-pillar-mapping.png`; FR-004; WAF Pillar Notes section with one row per pillar; index banner
- [X] T041 [US4] Update `docs/architecture/c4/system.md` (pre-existing file, UPDATED per RQ-06) — add front-matter banner `[→ Architecture index](../README.md)`, persona clusters header, spec refs (`spec-001` through `spec-009`), and `## Diagram` section referencing the newly authored `system.drawio`/`system.png` siblings; do NOT move file; FR-005
- [X] T042 [US4] Update `docs/architecture/c4/container.md` (pre-existing file, UPDATED per RQ-06) — add front-matter index banner, persona clusters, spec refs (`spec-001` through `spec-009`), and `## Diagram` section referencing `container.drawio`/`container.png` siblings; do NOT move file; FR-005
- [X] T043 [US4] Author `docs/architecture/adr/README.md` ADR navigation index — Markdown table with columns: Decision Number | Title | Status (Proposed/Accepted/Deprecated/Superseded) | Date | Motivating Spec | Canonical Path; list all ADRs found under `docs/decisions/`; **canonical ADR files stay in `docs/decisions/`** — this page is a cross-reference only per RQ-07; `lychee` will validate all canonical paths

**Checkpoint**: All six C4 diagrams present; L1→L2→L3 navigation possible without 404s; WAF pillar mapping and ADR index present; US4 acceptance tests 1–5 can be manually validated.

---

## Phase 7: User Story 5 — Technical Persona: Quality Cluster — Compliance & Security (Priority: P2)

**Goal**: Deliver the four security diagrams (SEC-01 through SEC-04) plus the audit-provenance sequence (SEQ-05) and the WCAG coverage page so a Compliance Auditor can locate AU-residency boundary, Foundry carve-out, and RBAC matrix on single pages.

**Independent Test**: Open `docs/architecture/security/au-residency-data-classification.md`. The AU boundary zone, Foundry carve-out mechanism-zone label (exact text: `"Permitted Non-AU Foundry Inference Zone (registry-gated; zero active non-AU entries)"`), and model-gateway redaction enforcement point must each be visible and labelled on the single diagram.

**[P]-eligible tasks first:**

- [X] T044 [P] [US5] Author diagram pair SEC-01 (AU-Residency and Data-Classification): `docs/architecture/security/au-residency-data-classification.drawio` + `au-residency-data-classification.png` via `drawio-mcp-diagramming` skill — AU data-residency boundary zone covering `australiaeast` and `australiasoutheast` for all data-plane resources (Cosmos DB, Storage, Service Bus, Event Grid, App Insights, Log Analytics, Key Vault, ACR, audit/evidence stores); Foundry carve-out zone labelled **EXACTLY**: `"Permitted Non-AU Foundry Inference Zone (registry-gated; zero active non-AU entries)"` — **DO NOT hard-code non-AU region names**; model-gateway redaction enforcement point shown as a distinct shape before data exits AU boundary; Azure stencils; FR-016; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T045 [P] [US5] Author diagram pair SEC-02 (RBAC Role/Permission Matrix): `docs/architecture/security/rbac-matrix.drawio` + `rbac-matrix.png` via `drawio-mcp-diagramming` skill — all 10 AIIMS roles × platform permissions; spec citation column per permission boundary; FR-017; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T046 [P] [US5] Author diagram pair SEC-03 (Trust-Boundary Diagram): `docs/architecture/security/trust-boundary.drawio` + `trust-boundary.png` via `drawio-mcp-diagramming` skill — every trust-boundary crossing labelled with the authentication/authorisation mechanism applied (e.g., Managed Identity, API key, OAuth 2.0); ingestion path from external agency shown end-to-end; Azure stencils; FR-018; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T047 [P] [US5] Author diagram pair SEC-04 (SLI/SLO Model): `docs/architecture/security/sli-slo-model.drawio` + `sli-slo-model.png` via `drawio-mcp-diagramming` skill — SLI definition, SLO target, error-budget burn-rate alert thresholds per key service; FR-019; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T048 [P] [US5] Author diagram pair SEQ-05 (Audit-Trail Provenance Flow): `docs/architecture/sequence/audit-provenance.drawio` + `audit-provenance.png` via `drawio-mcp-diagramming` skill — **FR-009 mandatory**: human gate on actuation; how every actuation is logged; who can review the log; what evidence is captured for compliance reporting; FR-010e, FR-020; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T049 [P] [US5] Author text-only page `docs/architecture/accessibility/wcag-coverage.md` — WCAG 2.2 success-criteria coverage table mapping each criterion to implementation status per component (no diagram pair required per RQ-10 decision); spec refs: `spec-020`; persona clusters: Technical-Experience; index banner; note in page body that full independent audit is deferred (WCAG-AUDIT-FULL known-gaps entry)
- [X] T050 [US5] Author markdown page `docs/architecture/security/au-residency-data-classification.md` — persona clusters: Technical-Quality; spec refs: `spec-036`; embeds `au-residency-data-classification.png`; FR-016; include `<!-- spec-cross-ref: spec-036 -->` annotation; WAF Pillar Notes: Security pillar; index banner
- [X] T051 [US5] Author markdown page `docs/architecture/security/rbac-matrix.md` — persona clusters: Technical-Quality; spec refs: `spec-017`, `spec-019`; embeds `rbac-matrix.png`; FR-017; index banner
- [X] T052 [US5] Author markdown page `docs/architecture/security/trust-boundary.md` — persona clusters: Technical-Quality; spec refs: `spec-001`, `spec-017`; embeds `trust-boundary.png`; FR-018; index banner
- [X] T053 [US5] Author markdown page `docs/architecture/security/sli-slo-model.md` — persona clusters: Technical-Quality; spec refs: `spec-015`, `spec-017`; embeds `sli-slo-model.png`; FR-019; error-budget section with SLI/SLO definitions; index banner
- [X] T054 [US5] Author markdown page `docs/architecture/sequence/audit-provenance.md` — persona clusters: Technical-Quality; spec refs: `spec-020`, `spec-025`; embeds `audit-provenance.png`; FR-010e, FR-020; index banner

**Checkpoint**: All five security/compliance diagrams, audit-provenance sequence, and WCAG page present; SEC-01 Foundry carve-out label exact; US5 acceptance tests 1–4 can be manually validated.

---

## Phase 8: User Story 6 — Technical Persona: Build Cluster — Developer Orientation (Priority: P3)

**Goal**: Deliver the three deployment diagrams (DEPLOY-01 through DEPLOY-03) and pages so a DevOps engineer can answer "which stages gate a deployment" and "which resource group contains production containers" from the diagrams alone.

**Independent Test**: Open `docs/architecture/deployment/cicd-pipeline.md` and `docs/architecture/deployment/azure-resource-topology.md`. The what-if/plan gates, manual approvals, deployment targets, and all named `rg-ama` resources must be visible from those two diagrams without opening source code.

**[P]-eligible tasks first:**

- [X] T055 [P] [US6] Author diagram pair DEPLOY-01 (CI/CD Pipeline): `docs/architecture/deployment/cicd-pipeline.drawio` + `cicd-pipeline.png` via `drawio-mcp-diagramming` skill — pipeline stages: what-if/plan gates, manual approval steps, deployment targets (Container Apps); each stage labelled; Azure stencils; spec refs: `spec-017`, `spec-029`; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T056 [P] [US6] Author diagram pair DEPLOY-02 (Azure Resource Topology): `docs/architecture/deployment/azure-resource-topology.drawio` + `azure-resource-topology.png` via `drawio-mcp-diagramming` skill — `rg-ama` resource group containing all named resources: `ca-api`, `ca-agents`, `ca-ingest`, `cosmos-ama-zo6bb5`, `app-ama-zo6bb5`, Azure AI Search, Service Bus, Event Hubs, Application Insights, Key Vault; **Azure stencils mandatory for every resource**; spec refs: `spec-001`, `spec-017`; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T057 [P] [US6] Author diagram pair DEPLOY-03 (Cosmos DB Partitioning Scheme): `docs/architecture/deployment/cosmos-partitioning.drawio` + `cosmos-partitioning.png` via `drawio-mcp-diagramming` skill — partition key strategy; disaster-event document routing to partition; alignment with multi-jurisdiction isolation model (cross-reference SECTOR-01); Azure stencils for Cosmos DB; spec refs: `spec-001`, `spec-035`; 150 DPI PNG; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`
- [X] T058 [US6] Author markdown page `docs/architecture/deployment/cicd-pipeline.md` — persona clusters: Technical-Build; spec refs: `spec-017`, `spec-029`; embeds `cicd-pipeline.png`; index banner
- [X] T059 [US6] Author markdown page `docs/architecture/deployment/azure-resource-topology.md` — persona clusters: Technical-Build; spec refs: `spec-001`, `spec-017`; embeds `azure-resource-topology.png`; include Key Elements section listing all named `rg-ama` resources; index banner
- [X] T060 [US6] Author markdown page `docs/architecture/deployment/cosmos-partitioning.md` — **this is the new forward-authoritative page** superseding the root-level copy; include redirect note at top: "> **Note**: The root-level `../cosmos-partitioning.md` is a legacy copy; this page is authoritative. See known-gaps COSM-MIG-01."; persona clusters: Technical-Build; spec refs: `spec-001`, `spec-035`; embeds `cosmos-partitioning.png`; index banner

**Checkpoint**: All three deployment diagrams and pages present; DEPLOY-02 shows all `rg-ama` resources with Azure stencils; US6 acceptance tests 1–3 can be manually validated.

---

## Phase 9: User Story 7 — CI Validation: Documentation-as-Code (Priority: P3)

**Goal**: Deliver the two Python lint scripts and the `docs-arch` CI job so every PR automatically verifies diagram pairing, link integrity, spec cross-references, and known-gaps registry completeness.

**Independent Test**: Trigger the `docs-arch` CI job on the branch. It must report: (a) 0 PNGs without a `.drawio` sibling, (b) 0 broken internal links, (c) 0 un-cited spec numbers (001–037 excluding known-gaps exclusions).

**[P]-eligible tasks first:**

- [X] T061 [P] [US7] Author `tools/lint/check_spec_cross_refs.py` per `contracts/lint-scripts.md` §1 algorithm — stdlib only (`pathlib`, `re`, `sys`, `argparse`; Python 3.12); `--root REPO_ROOT` optional arg (default: `cwd`); exit 0 = all spec numbers cited, exit 1 = missing citations with structured report; deduplicate `036-*` directories by 3-digit prefix; read exclusion list from `docs/architecture/known-gaps.md` rows where `Status == 'Resolved'`
- [X] T062 [P] [US7] Author `tools/lint/check_known_gaps.py` per `contracts/lint-scripts.md` §2 — stdlib only; validates every row in `docs/architecture/known-gaps.md` has a non-empty, non-`TBD` Follow-up Task Ref; exit 0/1; `--root REPO_ROOT` optional arg; structured failure report on exit 1
- [X] T063 [US7] Wire `docs-arch` CI job into `.github/workflows/ci.yml` — insert the full job block from `contracts/lint-scripts.md` §4 verbatim: 7 steps (checkout, setup-python 3.12, setup-node 24, install lychee v0.15.1 pinned, markdownlint via `npx --yes markdownlint-cli2 "docs/architecture/**/*.md"`, link-check via lychee, png-drawio-pairing shell check, hash-manifest-check with `working-directory: docs/architecture`, spec-cross-ref-check, known-gaps-check); **NO `needs:` dependency** — runs parallel to `quality` job; `timeout-minutes: 10`; same triggers as `quality` job; no path filter; do NOT create a new workflow file
- [X] T064 [US7] Verify `check_spec_cross_refs.py` locally: `python tools/lint/check_spec_cross_refs.py` — expected output: "All N spec numbers cited." or a list of spec numbers now in known-gaps; investigate any unexpected missing spec numbers (especially spec-037 and SPEC-RANGE-VERIFY entries); add known-gaps rows for any spec confirmed as having no architecture home; exit must be 0
- [X] T065 [US7] Verify `check_known_gaps.py` locally: `python tools/lint/check_known_gaps.py` — expected: "All rows valid." confirming 11 (or more) rows and none with TBD Follow-up Task Ref; exit must be 0

**Checkpoint**: Both Python scripts exit 0 locally; `docs-arch` job defined in `ci.yml` with all 7 steps and no `needs:` dependency; US7 acceptance tests 1–3 ready for CI validation.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Front-matter updates on pre-existing docs, final manifest regeneration, lint post-flight, and the azd gate note.

**[P]-eligible tasks first:**

- [X] T066 [P] Update front-matter of `docs/architecture/sequence/monitoring-risk-comms.md` (pre-existing file, UPDATED per RQ-06) — add `[→ Architecture index](../README.md)` banner as first line after the title; add `persona clusters: Operational` and spec ref annotation; do NOT move file; FR-005; run markdownlint locally to confirm no violations after edit
- [X] T067 [P] Update front-matter of `docs/architecture/capacity-model.md` (pre-existing file at root, UPDATED per RQ-06) — add `[→ Architecture index](README.md)` banner; add migration note: "> **Migration**: This file is at the repository root of `docs/architecture/`. See known-gaps entry `CAP-MIG-01` for the follow-up migration to `deployment/` or `governance/`."; do NOT move file; FR-005
- [X] T068 [P] Update front-matter of `docs/architecture/cosmos-partitioning.md` (root-level legacy copy, UPDATED per RQ-06) — add index banner; add redirect note: "> **Redirect**: This is a legacy copy. The forward-authoritative page is [`deployment/cosmos-partitioning.md`](deployment/cosmos-partitioning.md). See known-gaps entry `COSM-MIG-01`."; do NOT move file; FR-005
- [X] T069 [P] Update front-matter of `docs/architecture/spec-035-middleware-and-offline.md` (pre-existing file at root, UPDATED per RQ-06) — add index banner; add migration note referencing `MDW-MIG-01` known-gaps entry; add spec ref annotation for `spec-035`; do NOT move file; FR-005
- [X] T070 Regenerate complete `docs/architecture/.diagram-hashes` manifest from all 26 `.drawio` files to ensure all diagram authoring is reflected — from `docs/architecture/` run: `find . -name '*.drawio' | sort | xargs sha256sum | sed 's|  \./|  |' > .diagram-hashes` (Linux/macOS) or PowerShell equivalent from `quickstart.md` Step 4 (Windows); verify all 26 entries present; run `sha256sum --check .diagram-hashes` — expected: 26 entries, all OK
- [X] T071 Finalise `docs/architecture/README.md` — replace all `[forthcoming]` placeholder links with real links to completed pages; verify every one of the 26 diagram pages is linked under the correct persona cluster section; add `<!-- spec-cross-ref: spec-NNN -->` comments for any spec numbers not yet inline-cited; run `npx markdownlint-cli2 docs/architecture/README.md` and confirm exit 0
- [X] T072 Lint post-flight — run the complete local CI check suite in order and confirm all five checks exit 0: (1) `npx markdownlint-cli2 "docs/architecture/**/*.md"`, (2) PNG↔drawio pairing shell check (per `contracts/lint-scripts.md` §3), (3) `cd docs/architecture && sha256sum --check .diagram-hashes && cd -`, (4) `python tools/lint/check_spec_cross_refs.py`, (5) `python tools/lint/check_known_gaps.py` — fix any remaining violations before raising the PR
- [X] T073 NOTE — `azd up` gate (expected no-op): This feature modifies **no application code, infrastructure templates, or environment variables**. Confirm scope: `git diff --name-only HEAD | grep -vE '^(docs/|tools/lint/|\.github/workflows/ci\.yml)'` must return empty output. `azd up` redeploy is NOT required and should NOT be triggered. If the grep returns unexpected paths, investigate before merging.

---

## Phase 11 — Amendment 1 (2026-05-11)

**Purpose**: Add 6 new diagram pairs and companion pages identified after T073 sign-off: RISK-01 (risk-register lifecycle), OPS-03 (PPRR phase overlay), SECTOR-05 (cross-sector touchpoints), BUILD-01 (agent-runtime LLM gateway), QUAL-01 (test pyramid), and EXP-01 (ops-dashboard user journey). Includes manifest regeneration from 26 → 32 entries and a full 5-check lint post-flight.

**Prerequisite**: All T001–T073 marked `[X]` (base feature complete). This amendment extends the diagram inventory from 26 → 32 diagrams.

**Fallback policy**: For each diagram task, attempt the `drawio-mcp-diagramming` skill first. If the MCP is unavailable or returns an error, fall back to hand-authored `.mxfile` XML (valid Draw.io XML with `<mxGraphModel>` root) and generate the PNG via Pillow (`PIL.Image` + `PIL.ImageDraw`) at 150 DPI on a white `#FFFFFF` background — the same approach used in the base feature. In either case, append the SHA256 manifest entry to `docs/architecture/.diagram-hashes` immediately after each PNG is confirmed. Add a `DRAWIO-FALLBACK-<ID>` row to `docs/architecture/known-gaps.md` for any diagram rendered via the fallback path; T086 removes the entry if the diagram is later re-rendered via the MCP, or keeps it `Open` if the fallback result is shipped as-is.

**[P]-eligible tasks first (diagram pairs):**

- [X] T074 [P] Author diagram pair RISK-01 (Risk Register Lifecycle): `docs/architecture/operational/risk-register-lifecycle.drawio` + `risk-register-lifecycle.png` via `drawio-mcp-diagramming` skill — lifecycle stages in sequence: risk identification → assessment (likelihood × impact) → treatment selection → monitoring → review/closure; AIIMS Risk Manager as primary actor per FR-013; escalation path to Incident Commander on high-residual-risk treatment; 150 DPI PNG, white `#FFFFFF` background; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`; if MCP unavailable fall back to hand-authored mxfile XML + Pillow-generated PNG and add `DRAWIO-FALLBACK-RISK-01` entry to `docs/architecture/known-gaps.md`
- [X] T075 [P] Author diagram pair OPS-03 (PPRR Phase Overlay): `docs/architecture/operational/pprr-phase-overlay.drawio` + `pprr-phase-overlay.png` via `drawio-mcp-diagramming` skill — four PPRR phases (Prevention, Preparedness, Response, Recovery) as horizontal swim-lanes; for each lane: system capabilities active, AIIMS roles engaged, key platform events; constitution §PPRR alignment note in diagram footer; FR-024; 150 DPI PNG, white background; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`; if MCP unavailable fall back to hand-authored mxfile XML + Pillow-generated PNG and add `DRAWIO-FALLBACK-OPS-03` entry to `docs/architecture/known-gaps.md`
- [X] T076 [P] Author diagram pair SECTOR-05 (Cross-Sector Touchpoints): `docs/architecture/data/cross-sector-touchpoints.drawio` + `cross-sector-touchpoints.png` via `drawio-mcp-diagramming` skill — touchpoints between emergency-management sectors (fire, flood/SES, health, transport, utilities); data exchange protocol label per touchpoint (CAP/EDXL/GeoJSON/REST); lead-agency designation rule shown at each sector boundary crossing; FR-015; 150 DPI PNG, white background; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`; if MCP unavailable fall back to hand-authored mxfile XML + Pillow-generated PNG and add `DRAWIO-FALLBACK-SECTOR-05` entry to `docs/architecture/known-gaps.md`
- [X] T077 [P] Author diagram pair BUILD-01 (Agent Runtime LLM Gateway): `docs/architecture/c4/agent-runtime-llm-gateway.drawio` + `agent-runtime-llm-gateway.png` via `drawio-mcp-diagramming` skill — internal path: 5 named agents → prompt-construction layer → model-gateway (redaction enforcement + routing) → Azure OpenAI / Foundry endpoint; rate-limit and circuit-breaker shown as distinct shapes; Azure stencil for Azure OpenAI; FR-014; 150 DPI PNG, white background; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`; if MCP unavailable fall back to hand-authored mxfile XML + Pillow-generated PNG and add `DRAWIO-FALLBACK-BUILD-01` entry to `docs/architecture/known-gaps.md`
- [X] T078 [P] Create directory `docs/architecture/quality/` with `.gitkeep` (add to git so directory tracks; only needed if not already present); then author diagram pair QUAL-01 (Test Pyramid): `docs/architecture/quality/test-pyramid.drawio` + `test-pyramid.png` via `drawio-mcp-diagramming` skill — 5-tier pyramid (bottom → top, widest → narrowest): Unit → Contract → Integration → Simulation → E2E; each tier labelled with relative volume descriptor (e.g., "~60 % of suite") and tooling (pytest / pact / pytest+testcontainers / simulation-harness / playwright); FR-025; 150 DPI PNG, white background; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`; if MCP unavailable fall back to hand-authored mxfile XML + Pillow-generated PNG and add `DRAWIO-FALLBACK-QUAL-01` entry to `docs/architecture/known-gaps.md`
- [X] T079 [P] Author diagram pair EXP-01 (Ops Dashboard User Journey): `docs/architecture/accessibility/ops-dashboard-user-journey.drawio` + `ops-dashboard-user-journey.png` via `drawio-mcp-diagramming` skill — step-by-step journey for Incident Commander through the ops dashboard: login → situational-awareness view → alert review → human approval gate (FR-009 marker required) → publication confirmation → audit receipt; WCAG 2.2 AA touchpoint annotation on each step (e.g., "SC 1.4.3 Contrast" on situational-awareness view); FR-026; 150 DPI PNG, white background; append SHA256 manifest entry to `docs/architecture/.diagram-hashes`; if MCP unavailable fall back to hand-authored mxfile XML + Pillow-generated PNG and add `DRAWIO-FALLBACK-EXP-01` entry to `docs/architecture/known-gaps.md`

**[P]-eligible tasks (markdown pages — each requires its respective diagram pair to be confirmed first; all six pages are independent of each other and may run in parallel):**

- [X] T080 [P] Author markdown page `docs/architecture/operational/risk-register-lifecycle.md` — purpose statement: "traces the end-to-end lifecycle of a risk record from identification through treatment to closure, showing the Risk Manager's decision points"; persona clusters: Operational (Risk Manager); spec refs: `spec-019`; embeds `risk-register-lifecycle.png`; FR-013; Key Elements section listing lifecycle stages and responsible AIIMS roles per stage; `<!-- spec-cross-ref: spec-019 -->` annotation; `[→ Architecture index](../README.md)` banner
- [X] T081 [P] Author markdown page `docs/architecture/operational/pprr-phase-overlay.md` — purpose statement: "maps platform capabilities and AIIMS roles to each PPRR phase so Resilience Planners can identify which system functions are active during Prevention, Preparedness, Response, and Recovery"; persona clusters: Operational (Resilience Planner); spec refs: `spec-019`; embeds `pprr-phase-overlay.png`; FR-024; note body: "Aligns with constitution §PPRR"; PPRR Phase Notes section (four rows: phase | active system capabilities | engaged AIIMS roles | key platform events); `[→ Architecture index](../README.md)` banner
- [X] T082 [P] Author markdown page `docs/architecture/data/cross-sector-touchpoints.md` — purpose statement: "documents the data exchange protocols and lead-agency designation rules at each cross-sector boundary for NSW RFS, VIC CFA, SES, Health, Transport, and Utilities personas"; persona clusters: Sector (Cross-Sector); spec refs: `spec-015`, `spec-022`; embeds `cross-sector-touchpoints.png`; FR-015; Touchpoint Reference table (columns: sector pair | data format | lead-agency rule | spec citation); `<!-- spec-cross-ref: spec-015 -->` annotation; `[→ Architecture index](../README.md)` banner
- [X] T083 [P] Author markdown page `docs/architecture/c4/agent-runtime-llm-gateway.md` — purpose statement: "traces the internal path from agent invocation through prompt construction, model-gateway redaction, and Foundry endpoint dispatch for AI/ML Engineers"; persona clusters: Technical-Build (AI/ML Engineer); spec refs: `spec-024`, `spec-025`, `spec-030`; embeds `agent-runtime-llm-gateway.png`; FR-014; Key Elements section: 5 named agents, prompt-construction layer, model-gateway redaction enforcement point, routing logic, circuit-breaker; Related Pages links to `component-agents.md`, `container.md`; `[→ Architecture index](../README.md)` banner
- [X] T084 [P] Author markdown page `docs/architecture/quality/test-pyramid.md` — purpose statement: "defines the five-tier test pyramid with relative volumes and tooling for the AMA platform so QA Engineers can scope test investment correctly"; persona clusters: Technical-Quality (QA Engineer); spec refs: any quality/testing spec present in `specs/`; embeds `test-pyramid.png`; FR-025; Test Tiers table (columns: tier | relative volume | tooling | example test target | notes) with one row per tier in order Unit → Contract → Integration → Simulation → E2E; `[→ Architecture index](../README.md)` banner
- [X] T085 [P] Author markdown page `docs/architecture/accessibility/ops-dashboard-user-journey.md` — purpose statement: "documents the Incident Commander's journey through the ops dashboard with WCAG 2.2 AA touchpoint annotations, enabling UX and PO review of accessibility obligations per step"; persona clusters: Technical-Experience (UX/PO); spec refs: `spec-020`; embeds `ops-dashboard-user-journey.png`; FR-026; Journey Steps table (columns: step | WCAG 2.2 criterion | AA requirement | implementation note); Related Pages link to `wcag-coverage.md`; `[→ Architecture index](../README.md)` banner

**Sequential finalization (depends on T074–T085 all complete):**

- [X] T086 Update `docs/architecture/README.md` index to add 6 new diagram page links in their correct persona-cluster sections: RISK-01 (`risk-register-lifecycle.md`) and OPS-03 (`pprr-phase-overlay.md`) under **Operational**, SECTOR-05 (`cross-sector-touchpoints.md`) under **Sector**, BUILD-01 (`agent-runtime-llm-gateway.md`) under **Technical-Build**, QUAL-01 (`test-pyramid.md`) under **Technical-Quality**, EXP-01 (`ops-dashboard-user-journey.md`) under **Technical-Experience**; then regenerate `docs/architecture/.diagram-hashes` manifest from scratch covering all 32 `.drawio` files (26 base + 6 amendment) — from `docs/architecture/` run: `find . -name '*.drawio' | sort | xargs sha256sum | sed 's|  \./|  |' > .diagram-hashes` (Linux/macOS) or PowerShell equivalent from `quickstart.md` Step 4 (Windows); verify exactly 32 entries are present; run all 5 lint checks in order and confirm each exits 0: (1) `npx markdownlint-cli2 "docs/architecture/**/*.md"`, (2) PNG↔drawio pairing shell check (per `contracts/lint-scripts.md` §3), (3) `cd docs/architecture && sha256sum --check .diagram-hashes && cd -`, (4) `python tools/lint/check_spec_cross_refs.py`, (5) `python tools/lint/check_known_gaps.py`; then update `docs/architecture/known-gaps.md`: for each of the 6 new diagrams, if it was rendered via the `drawio-mcp-diagramming` skill (MCP path), mark its `DRAWIO-FALLBACK-<ID>` entry as `Resolved` **or** remove the row if it was never added (MCP succeeded on first attempt); if the fallback path was used, keep the entry as `Open` — goal: zero `Open` DRAWIO-FALLBACK entries for any diagram successfully rendered by the MCP

**Checkpoint**: 32 `.drawio` + 32 `.png` files present; 6 new markdown pages reachable from `docs/architecture/README.md` with no 404s; `docs/architecture/.diagram-hashes` contains exactly 32 entries and `sha256sum --check` exits 0; all 5 lint checks exit 0; known-gaps `DRAWIO-FALLBACK-*` entries accurately reflect which diagrams used the fallback path.

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1: Setup                    → no dependencies; start immediately
Phase 2: Foundational             → depends on Phase 1 (directories must exist)
Phase 3: US1 (P1)                 → depends on Phase 2 (known-gaps seeded; lint baseline clean)
Phase 4: US2 (P1)                 → depends on Phase 2; independent of Phase 3
Phase 5: US3 (P2)                 → depends on Phase 2; independent of Phases 3–4
Phase 6: US4 (P2)                 → depends on Phase 2; independent of Phases 3–5
Phase 7: US5 (P2)                 → depends on Phase 2; independent of Phases 3–6
Phase 8: US6 (P3)                 → depends on Phase 2; independent of Phases 3–7
Phase 9: US7 (P3)                 → depends on Phase 2; lint scripts can draft in parallel with diagrams
Phase 10: Polish                  → depends on all diagram phases (3–9) being complete
Phase 11: Amendment 1             → depends on Phase 10 (T001–T073 all [X]); T074–T079 (diagrams) fully parallel;
                                     T080–T085 (pages) parallel with each other, each requires its diagram pair;
                                     T086 (manifest + lint + README) sequential after T074–T085
```

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 only — no dependency on US2–US7. Index (T010) should be started after T006–T009 so it can link to real pages.
- **US2 (P1)**: Depends on Phase 2 only — fully independent of US1. Can run in parallel with US1 if two contributors are available.
- **US3 (P2)**: Depends on Phase 2 only — independent of US1/US2. SECTOR-04 must cite spec-022.
- **US4 (P2)**: Depends on Phase 2 only — C4-L3 pages (T036–T039) benefit from C4-L2 diagram (T030) being complete for "Related Pages" links, but are otherwise independent.
- **US5 (P2)**: Depends on Phase 2 only — SEC-01 (T044) must use the exact Foundry carve-out label; no dependency on other US5 tasks.
- **US6 (P3)**: Depends on Phase 2 only — DEPLOY-03 markdown (T060) should cross-link to SECTOR-01 page from Phase 5 if that phase is already complete.
- **US7 (P3)**: Python scripts (T061, T062) can be drafted in parallel with any diagram phase. CI job wiring (T063) should be done after T061–T062 are verified locally (T064–T065).

### Within Each User Story

```text
[P] diagram-pair tasks → markdown page tasks → update README links
```

Diagram pairs and markdown pages for different diagrams within the same phase are fully independent (different files) and all marked `[P]`.

### Intra-Phase Ordering (where sequential execution is required)

- **Phase 3**: T006 and T007 (diagrams) before T008 and T009 (pages that embed them); T010 (index) after T008–T009
- **Phase 6**: T029–T035 (diagrams) before T041–T042 (updates to pre-existing files that add diagram references); T043 (ADR index) can run in parallel with all of Phase 6
- **Phase 10**: T070 (manifest regeneration) before T072 (lint post-flight hash check); T071 (finalise README) before T072

---

## Parallel Execution Examples

### US1 + US2 in parallel (two contributors, both P1)

```text
Contributor A (US1 — New Joiner):
  Parallel: T006 (SEQ-03 diagram) + T007 (SEQ-04 diagram)
  Sequential: T008 (SEQ-03 page) → T009 (SEQ-04 page) → T010 (README index)

Contributor B (US2 — Operational):
  Parallel: T011 (SEQ-01) + T012 (SEQ-02) + T013 (SEQ-06) + T014 (OPS-01) + T015 (OPS-02)
  Sequential: T016 → T017 → T018 → T019 → T020 (markdown pages)
```

### US3–US5 in parallel (three contributors, all P2)

```text
Contributor A (US3 — Sector): Parallel: T021 + T022 + T023 + T024; then T025–T028
Contributor B (US4 — Architecture): Parallel: T029–T035; then T036–T043
Contributor C (US5 — Security): Parallel: T044–T049; then T050–T054
```

### Phase 9 (US7) in parallel with diagram phases

```text
Contributor D (US7 — CI): T061 + T062 in parallel with any other phase;
  T063 after T061–T062 verified; T064–T065 after T063
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete **Phase 1** (Setup) — 5 minutes
2. Complete **Phase 2** (Foundational) — seed known-gaps, lint pre-flight baseline
3. Complete **Phase 3** (US1) — 2 diagrams + 2 pages + index
4. **STOP and VALIDATE**: Open `docs/architecture/README.md`; confirm SEQ-03 and SEQ-04 load; confirm index links resolve; confirm `npx markdownlint-cli2` and pairing check pass for Phase 3 output
5. Raise a draft PR to validate CI scaffold early (even before US7 CI job is wired)

### Incremental Delivery (Recommended)

```text
Phase 1+2 → Phase 3 (US1, P1) → Phase 4 (US2, P1)
         → demo/review: operational diagrams visible
         → Phase 5 (US3, P2) in parallel with Phase 6 (US4, P2)
         → Phase 7 (US5, P2) in parallel with above
         → Phase 8 (US6, P3) + Phase 9 (US7, P3)
         → Phase 10 (Polish + lint post-flight)
         → PR ready for merge
```

Each user story phase delivers independently reviewable documentation that adds value without breaking the prior phase.

### Parallel Team Strategy (4 contributors)

```text
After Phase 1+2:
  Dev A: Phase 3 (US1) + Phase 4 (US2) in sequence
  Dev B: Phase 5 (US3) + Phase 8 (US6)
  Dev C: Phase 6 (US4)
  Dev D: Phase 7 (US5) + Phase 9 (US7)
  All converge for Phase 10 (Polish)
```

---

## Task Summary

| Phase | Story | Priority | Task Range | Count | Key Deliverable |
|-------|-------|----------|------------|-------|-----------------|
| 1 — Setup | — | — | T001–T002 | 2 | Directory scaffold + manifest init |
| 2 — Foundational | — | — | T003–T005 | 3 | Lint baseline + known-gaps seed (11 entries) |
| 3 — US1 | US1 | P1 🎯 | T006–T010 | 5 | README index + SEQ-03 + SEQ-04 |
| 4 — US2 | US2 | P1 | T011–T020 | 10 | SEQ-01, SEQ-02, SEQ-06, OPS-01, OPS-02 |
| 5 — US3 | US3 | P2 | T021–T028 | 8 | SECTOR-01 through SECTOR-04 |
| 6 — US4 | US4 | P2 | T029–T043 | 15 | Full C4 model (L1–L3) + GOV-01 + ADR index |
| 7 — US5 | US5 | P2 | T044–T054 | 11 | SEC-01 through SEC-04 + SEQ-05 + WCAG page |
| 8 — US6 | US6 | P3 | T055–T060 | 6 | DEPLOY-01 through DEPLOY-03 |
| 9 — US7 | US7 | P3 | T061–T065 | 5 | Lint scripts + `docs-arch` CI job |
| 10 — Polish | — | — | T066–T073 | 8 | Front-matter × 4 + manifest regen + post-flight + azd note |
| 11 — Amendment 1 | — | — | T074–T086 | 13 | 6 new diagram pairs + 6 pages + manifest (32) + lint post-flight |
| **Total** | | | **T001–T086** | **86** | |

### Parallel Opportunities by Phase

| Phase | [P]-eligible tasks | Max parallel stream |
|-------|-------------------|---------------------|
| Phase 3 (US1) | T006, T007 | 2 diagrams simultaneously |
| Phase 4 (US2) | T011, T012, T013, T014, T015 | 5 diagrams simultaneously |
| Phase 5 (US3) | T021, T022, T023, T024 | 4 diagrams simultaneously |
| Phase 6 (US4) | T029, T030, T031, T032, T033, T034, T035, T036, T037, T038, T039, T040 | 12 tasks simultaneously |
| Phase 7 (US5) | T044, T045, T046, T047, T048, T049 | 6 tasks simultaneously |
| Phase 8 (US6) | T055, T056, T057 | 3 diagrams simultaneously |
| Phase 9 (US7) | T061, T062 | 2 scripts simultaneously |
| Phase 10 (Polish) | T066, T067, T068, T069 | 4 front-matter updates simultaneously |
| Phase 11 (Amendment 1) | T074–T079 (diagrams); T080–T085 (pages, after respective diagram) | 6 diagram pairs simultaneously; then 6 pages simultaneously |

### Diagram Inventory vs Tasks

| Diagram ID | File base | Phase | Task(s) |
|-----------|-----------|-------|---------|
| SEQ-03 | `sequence/evacuation-five-stage` | Phase 3 US1 | T006, T008 |
| SEQ-04 | `sequence/recovery-transition` | Phase 3 US1 | T007, T009 |
| SEQ-01 | `sequence/alert-approval-publication` | Phase 4 US2 | T011, T016 |
| SEQ-02 | `sequence/cross-agency-recommendation` | Phase 4 US2 | T012, T017 |
| SEQ-06 | `sequence/graceful-degradation` | Phase 4 US2 | T013, T018 |
| OPS-01 | `operational/aiims-system-context` | Phase 4 US2 | T014, T019 |
| OPS-02 | `operational/escalation-paths` | Phase 4 US2 | T015, T020 |
| SECTOR-01 | `data/multi-jurisdiction-tenancy` | Phase 5 US3 | T021, T025 |
| SECTOR-02 | `data/ingestion-data-flow` | Phase 5 US3 | T022, T026 |
| SECTOR-03 | `data/integration-point-map` | Phase 5 US3 | T023, T027 |
| SECTOR-04 | `data/jurisdiction-filter` | Phase 5 US3 | T024, T028 |
| C4-L1 | `c4/system` | Phase 6 US4 | T029, T041 |
| C4-L2 | `c4/container` | Phase 6 US4 | T030, T042 |
| C4-L3-API | `c4/component-api` | Phase 6 US4 | T031, T036 |
| C4-L3-Web | `c4/component-web` | Phase 6 US4 | T032, T037 |
| C4-L3-Agents | `c4/component-agents` | Phase 6 US4 | T033, T038 |
| C4-L3-Ingest | `c4/component-ingest` | Phase 6 US4 | T034, T039 |
| GOV-01 | `governance/waf-pillar-mapping` | Phase 6 US4 | T035, T040 |
| SEC-01 | `security/au-residency-data-classification` | Phase 7 US5 | T044, T050 |
| SEC-02 | `security/rbac-matrix` | Phase 7 US5 | T045, T051 |
| SEC-03 | `security/trust-boundary` | Phase 7 US5 | T046, T052 |
| SEC-04 | `security/sli-slo-model` | Phase 7 US5 | T047, T053 |
| SEQ-05 | `sequence/audit-provenance` | Phase 7 US5 | T048, T054 |
| DEPLOY-01 | `deployment/cicd-pipeline` | Phase 8 US6 | T055, T058 |
| DEPLOY-02 | `deployment/azure-resource-topology` | Phase 8 US6 | T056, T059 |
| DEPLOY-03 | `deployment/cosmos-partitioning` | Phase 8 US6 | T057, T060 |
| RISK-01 | `operational/risk-register-lifecycle` | Phase 11 Amend-1 | T074, T080 |
| OPS-03 | `operational/pprr-phase-overlay` | Phase 11 Amend-1 | T075, T081 |
| SECTOR-05 | `data/cross-sector-touchpoints` | Phase 11 Amend-1 | T076, T082 |
| BUILD-01 | `c4/agent-runtime-llm-gateway` | Phase 11 Amend-1 | T077, T083 |
| QUAL-01 | `quality/test-pyramid` | Phase 11 Amend-1 | T078, T084 |
| EXP-01 | `accessibility/ops-dashboard-user-journey` | Phase 11 Amend-1 | T079, T085 |

*All 32 diagram pairs are now covered (26 base + 6 Amendment 1). The deferred Bicep Module Dependency Graph is tracked as known-gaps entry `BICEP-DEP-01`.*

### Known-Gaps Registry — 11 Seed Entries (seeded in T004) + up to 6 Amendment 1 DRAWIO-FALLBACK entries (managed by T086)

| # | Entry ID | Seeded in | Status |
|---|----------|-----------|--------|
| 1 | BICEP-DEP-01 | T004 | Open |
| 2 | DUPE-036 | T004 | Open |
| 3 | CAP-MIG-01 | T004 | Open |
| 4 | COSM-MIG-01 | T004 | Open |
| 5 | MDW-MIG-01 | T004 | Open |
| 6 | FOUNDRY-REGION | T004 | Open |
| 7 | SPEC-037 | T004 | Open |
| 8 | C4-L4 | T004 | Open |
| 9 | LYCHEE-CFG | T004 | Open |
| 10 | WCAG-AUDIT-FULL | T004 | Open |
| 11 | SPEC-RANGE-VERIFY | T004 | Open |
| 12 | DRAWIO-FALLBACK-RISK-01 | T074 (conditional) | Added only if MCP unavailable for RISK-01; T086 resolves or removes |
| 13 | DRAWIO-FALLBACK-OPS-03 | T075 (conditional) | Added only if MCP unavailable for OPS-03; T086 resolves or removes |
| 14 | DRAWIO-FALLBACK-SECTOR-05 | T076 (conditional) | Added only if MCP unavailable for SECTOR-05; T086 resolves or removes |
| 15 | DRAWIO-FALLBACK-BUILD-01 | T077 (conditional) | Added only if MCP unavailable for BUILD-01; T086 resolves or removes |
| 16 | DRAWIO-FALLBACK-QUAL-01 | T078 (conditional) | Added only if MCP unavailable for QUAL-01; T086 resolves or removes |
| 17 | DRAWIO-FALLBACK-EXP-01 | T079 (conditional) | Added only if MCP unavailable for EXP-01; T086 resolves or removes |

---

## Notes

- `[P]` = different output files, no dependency on incomplete sibling tasks in the same phase — safe to execute simultaneously
- `[USN]` label maps each task to a specific user story for traceability to spec.md acceptance criteria
- Each user story phase is independently deployable: branch can be reviewed diagram-by-diagram
- Commit after each logical group (e.g., one diagram pair + its markdown page + manifest entry update)
- **Diagram authoring order within a phase does not matter** — all are independent `.drawio` + `.png` + `.md` triplets in different subdirectories
- **Manifest discipline**: After every PNG export, run Step 4 from `quickstart.md` to update `.diagram-hashes` before committing — CI will fail on a stale entry
- **FR-009 compliance**: SEQ-01, SEQ-02, SEQ-03, SEQ-05 are actuation diagrams and MUST have a visible human-in-the-loop gate marker — verify visually before committing each
- **Spec-022 citation**: Must appear in at least one page (`jurisdiction-filter.md` carries it; T028 includes the HTML comment annotation)
- **Spec-036 citation**: Must appear in at least one page (`au-residency-data-classification.md`; T050 includes the HTML comment annotation)
- **No new npm workspace devDependencies**: `npx --yes markdownlint-cli2` downloads on demand; lychee installed via curl in CI (per `contracts/lint-scripts.md`); no `package.json` changes required
- **No changes to `apps/` code**: this feature is documentation-as-code only; T073 confirms scope gate

### Amendment 1 Notes (2026-05-11)

- **Amendment scope**: T074–T086 add 6 diagram pairs and 6 pages; total diagram inventory grows from 26 → 32
- **New directory**: `docs/architecture/quality/` created in T078 — must be committed with `.gitkeep` before T084 (markdown page) is authored to avoid missing-parent errors
- **FR-009 in amendment**: EXP-01 (T079) includes the human approval gate step in the ops-dashboard user journey — the gate marker must be visible on the diagram per FR-009 before T085 embeds the PNG
- **Manifest discipline for amendment**: Append each new SHA256 entry to `.diagram-hashes` immediately after its PNG is exported (T074–T079), then do a complete regeneration in T086 to catch any ordering or duplicate issues — do NOT wait until T086 for the first write
- **DRAWIO-FALLBACK entries are conditional**: Rows 12–17 in the Known-Gaps Registry are only added if the `drawio-mcp-diagramming` skill is unavailable for that specific diagram; if all 6 render via MCP, the known-gaps table remains at 11 seed entries
- **FR-024 / constitution §PPRR**: OPS-03 (T075/T081) must cite FR-024 and reference the constitution §PPRR section in the diagram footer and page body — verify both before committing
- **`docs/architecture/quality/` lint scope**: T086 step (1) runs `npx markdownlint-cli2 "docs/architecture/**/*.md"` which will now include `quality/test-pyramid.md` — ensure the page passes before running T086
