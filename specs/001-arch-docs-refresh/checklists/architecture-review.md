# Architecture Review Checklist: Comprehensive Architectural Documentation & Diagrams Refresh

**Purpose**: PR reviewer gate — validates requirement quality, completeness, and consistency of all architecture documentation deliverables before merge. Every item is a binary pass/fail check on the *requirements and their artefacts*, not on runtime behaviour.
**Created**: 2026-05-11
**Feature**: [`specs/001-arch-docs-refresh/spec.md`](../spec.md)
**Audience**: PR reviewers performing final architectural review before merge
**Granularity**: Per-deliverable (per diagram pair + per page) PLUS roll-up spec-level acceptance items

---

## 1 — Index & Navigation Completeness

- [ ] CHK001 — MUST confirm `docs/architecture/README.md` exists as the single top-level index from which every architecture page is reachable within ≤ 2 navigation steps. [Completeness, Spec §FR-001]
- [ ] CHK002 — MUST verify the index organises pages under all six named persona clusters: Operational, Sector, Technical-Architecture, Technical-Build, Technical-Quality, Technical-Experience. [Completeness, Spec §FR-002]
- [ ] CHK003 — MUST confirm the Technical-Experience cluster covers accessibility documentation, WCAG coverage map, and end-user interaction patterns (not left undefined). [Clarity, Spec §FR-002, Clarification Q1]
- [ ] CHK004 — MUST verify all six pre-existing architecture documents (`c4/system.md`, `c4/container.md`, `sequence/monitoring-risk-comms.md`, `capacity-model.md`, `cosmos-partitioning.md`, `spec-035-middleware-and-offline.md`) are linked or redirected from the index. [Completeness, Spec §FR-005]
- [ ] CHK005 — MUST confirm a redirect note appears in the index for each pre-existing document at its original path (not silently orphaned). [Completeness, Spec §FR-005]
- [ ] CHK006 — MUST verify zero broken internal links within `docs/architecture/README.md` itself (all relative `[text](path)` references resolve). [Consistency, Spec §FR-001]
- [ ] CHK007 — MUST confirm every persona cluster section in the index links to at least one page with a diagram answering that cluster's primary architecture question within one additional step. [Completeness, Spec §SC-002]
- [ ] CHK008 — MUST verify the ADR navigation index (`docs/architecture/adr/README.md`) exists as a cross-reference table — not a canonical ADR store — and that no existing ADRs have been moved from `docs/decisions/`. [Completeness, Spec §FR-004, Clarification Q2]

---

## 2 — Diagram Source-of-Truth Integrity

- [ ] CHK009 — MUST confirm every `.png` file under `docs/architecture/` has a sibling `.drawio` source file with the same base name in the same directory. [Completeness, Spec §FR-006, FR-007]
- [ ] CHK010 — MUST verify `docs/architecture/.diagram-hashes` exists and contains a SHA256 hash entry for every `.drawio` file in scope; no entry may be missing or stale. [Completeness, Spec §FR-021(d), Edge Case]
- [ ] CHK011 — MUST confirm PNG staleness detection uses the hash manifest (not file modification timestamps), ensuring git-clone reliability. [Clarity, Spec §FR-021(d), Clarification Q3]
- [ ] CHK012 — MUST verify all Azure service nodes across deployment, C4, and security diagrams use the official Azure Draw.io shape stencils (not generic shapes). [Completeness, Spec §FR-008]
- [ ] CHK013 — MUST confirm every actuation diagram carries a visually distinct human-in-the-loop checkpoint (labelled shape, dedicated colour, or explicit swim-lane boundary — not an inline comment). [Completeness, Spec §FR-009, SC-006]
- [ ] CHK014 — MUST verify all six sequence diagrams (SEQ-01 through SEQ-06) are present as diagram pairs and that every actuation diagram among them carries the required human-in-the-loop callout. [Completeness, Spec §FR-010, SC-006]
- [ ] CHK015 — MUST confirm the total distinct diagram pairs under `docs/architecture/` is ≥ 26, matching the named inventory in SC-007; any deferred or merged diagram is recorded in the known-gaps registry. [Completeness, Spec §SC-007]

---

## 3 — C4 Coverage

- [ ] CHK016 — MUST confirm `C4-L1` (System Context) is present; MUST include all required external systems: BoM weather feed, GA seismic feed, NEMA NCM, state agency CAP/EDXL/GeoJSON sources, and end-user browser/mobile client. [Completeness, Spec §FR-004, US4 SC1]
- [ ] CHK017 — MUST confirm `C4-L2` (Container) is present; MUST show all deployed containers: API (FastAPI), Web (Next.js), Agents runtime (all 5 named agents), Ingest service, Cosmos DB, Azure AI Search, Service Bus, Event Hubs, Application Insights, Key Vault, Azure OpenAI/Foundry. [Completeness, Spec §FR-004, US4 SC2]
- [ ] CHK018 — MUST confirm `C4-L3-API` (Component: API) is present with internal components labelled and relationships to adjacent containers shown. [Completeness, Spec §FR-004, US4 SC3]
- [ ] CHK019 — MUST confirm `C4-L3-Web` (Component: Web) is present with internal components labelled. [Completeness, Spec §FR-004, US4 SC3]
- [ ] CHK020 — MUST confirm `C4-L3-Agents` (Component: Agents Runtime) is present, naming all 5 agents and their LLM/model-gateway interactions. [Completeness, Spec §FR-004, US4 SC3]
- [ ] CHK021 — MUST confirm `C4-L3-Ingest` (Component: Ingest Service) is present with ingestion paths and downstream routing shown. [Completeness, Spec §FR-004, US4 SC3]
- [ ] CHK022 — MUST verify a reader can trace L1 → L2 → L3 without leaving `docs/architecture/`; every container in L2 MUST have a corresponding Component page or a known-gap entry. [Completeness, Spec §US4 Test, FR-004]
- [ ] CHK023 — MUST confirm C4 L4 (Code) is either delivered or explicitly deferred with a known-gaps registry entry and follow-up task; silence on this level is not acceptable. [Completeness, Spec §FR-004, Assumption]

---

## 4 — Persona Coverage

- [ ] CHK024 — MUST confirm the Operational cluster has ≥ 1 diagram (`OPS-01` or equivalent) answering: "Which AIIMS roles interact with which system components, and how?" [Completeness, Spec §FR-002, SC-002]
- [ ] CHK025 — MUST confirm the Sector cluster has ≥ 1 diagram (`SECTOR-01` or equivalent) answering: "How are multi-jurisdiction tenants isolated, and which state is lead agency per event?" [Completeness, Spec §FR-002, SC-002]
- [ ] CHK026 — MUST confirm the Technical-Architecture cluster has ≥ 1 diagram (C4 model) answering: "What runs where and who talks to whom?" [Completeness, Spec §FR-002, SC-002]
- [ ] CHK027 — MUST confirm the Technical-Build cluster has ≥ 1 diagram (`DEPLOY-01` or equivalent) answering: "Which pipeline stages gate a deployment and what resources are in `rg-ama`?" [Completeness, Spec §FR-002, SC-002]
- [ ] CHK028 — MUST confirm the Technical-Quality cluster has ≥ 1 diagram (`SEC-01` or equivalent) answering: "Where is the AU boundary, where is the Foundry carve-out, and where is redaction applied?" [Completeness, Spec §FR-002, SC-002, SC-003]
- [ ] CHK029 — MUST confirm the Technical-Experience cluster has ≥ 1 diagram or page answering: "What WCAG coverage exists and what are the end-user interaction patterns?" [Completeness, Spec §FR-002]
- [ ] CHK030 — MUST verify all 10 AIIMS roles appear as named actors in at least one diagram: Incident Commander, Operations, Planning, Logistics, Public Information, Field Coordinator, Resilience Planner, Executive Leader, Observer/Auditor, Risk Manager. [Completeness, Spec §FR-013]
- [ ] CHK031 — MUST confirm the integration-point map (`SECTOR-03`) covers every named external system: BoM weather, GA seismic, NEMA NCM, and all CAP/EDXL/GeoJSON-producing agency systems, with data format and ingestion endpoint labelled. [Completeness, Spec §FR-014]

---

## 5 — Compliance & Security Coverage

- [ ] CHK032 — MUST confirm `SEC-01` shows, on a single diagram: (a) AU data-residency boundary (`australiaeast` + `australiasoutheast` for all data-plane resources), (b) Foundry carve-out zone, (c) model-gateway redaction enforcement point — each visually labelled. [Completeness, Spec §FR-016, SC-003]
- [ ] CHK033 — MUST verify the Foundry carve-out zone in `SEC-01` is labelled exactly as "Permitted Non-AU Foundry Inference Zone (registry-gated)" with an annotation stating the current non-AU entry count (zero as of spec authoring). No specific non-AU region names are hard-coded. [Clarity, Spec §FR-016, Clarification Q4]
- [ ] CHK034 — MUST confirm `SEC-01` correctly identifies the AU boundary data-plane resources: Cosmos DB, Storage, Service Bus, Event Grid, Application Insights, Log Analytics, Key Vault, ACR, audit, and evidence stores. [Completeness, Spec §FR-016]
- [ ] CHK035 — MUST confirm `SEC-02` (RBAC matrix) maps every named AIIMS role to its platform permissions and cites the spec(s) that define those boundaries. [Completeness, Spec §FR-017]
- [ ] CHK036 — MUST confirm `SEC-03` (Trust-Boundary) labels every boundary crossing with the specific authentication or authorisation mechanism applied (not a generic "auth" label). [Clarity, Spec §FR-018]
- [ ] CHK037 — MUST confirm `SEC-04` (SLI/SLO Model) defines, per key service: the SLI metric, the SLO target percentage, and the error-budget burn-rate alert thresholds. [Completeness, Spec §FR-019]
- [ ] CHK038 — MUST confirm `SEQ-05` (Audit-Trail Provenance Flow) shows for every actuation: how it is logged, who can review the log, and what evidence is captured for compliance reporting. [Completeness, Spec §FR-020]
- [ ] CHK039 — MUST verify `SEC-03` traces at least one ingestion path from an external agency through every trust-boundary crossing to the agent consumer. [Coverage, Spec §FR-018, US5 SC3]
- [ ] CHK040 — MUST confirm the `SECTOR-01` (Multi-Jurisdiction Tenancy) diagram represents all eight state/territory jurisdictions (NSW, VIC, QLD, SA, WA, TAS, ACT, NT) plus Commonwealth agencies, with Cosmos DB partition-key alignment and per-state lead-agency designation shown. [Completeness, Spec §FR-015]

---

## 6 — Spec Cross-Reference Completeness (001–037)

- [ ] CHK041 — MUST confirm every spec number 001–037 is cited by at least one architecture page; verify this is the same set the CI `docs-arch` job checks. [Completeness, Spec §FR-011, SC-005]
- [ ] CHK042 — MUST confirm every architecture page cites the spec number(s) and/or ADR(s) that motivated its content (bidirectional: page → spec AND spec cited-by → page). [Completeness, Spec §FR-012]
- [ ] CHK043 — MUST verify spec numbers confirmed as archived or superseded are explicitly listed in the known-gaps registry — not silently excluded from CI counts. [Completeness, Spec §FR-011, Edge Case]
- [ ] CHK044 — MUST confirm the duplicate `036-*` directory situation is noted in the known-gaps registry and that it is counted as one shipped spec for cross-reference purposes. [Completeness, Spec §Assumption]
- [ ] CHK045 — MUST verify any spec with no natural architecture-page home has a known-gaps registry entry (with non-empty Follow-up Task Ref) rather than a forced spurious citation. [Completeness, Spec §Edge Case, FR-011]
- [ ] CHK046 — MUST confirm that citations are spec-number–specific (e.g., `spec-022`, not just "relevant specs"), enabling CI regex matching. [Clarity, Spec §FR-011, FR-021(c)]

---

## 7 — Documentation-as-Code CI Gates

- [ ] CHK047 — MUST confirm a `docs-arch` job exists in `.github/workflows/ci.yml` — not a new separate workflow file. [Completeness, Spec §FR-021, Assumption]
- [ ] CHK048 — MUST verify the `docs-arch` job runs on the same triggers as the `quality` job (push to `main`/`dev`/`staging`/`production`; PR to `main`) with no path filtering. [Completeness, Spec §Assumption, Clarification Q5]
- [ ] CHK049 — MUST confirm the `docs-arch` job invokes markdownlint via `npx markdownlint-cli2 "docs/architecture/**/*.md"` — no new workspace `devDependency` added. [Completeness, Spec §FR-022, Clarification Q3]
- [ ] CHK050 — MUST verify the `docs-arch` job fails the build when any `*.png` under `docs/architecture/` lacks a sibling `*.drawio` file. [Completeness, Spec §FR-021(a), SC-004]
- [ ] CHK051 — MUST confirm the `docs-arch` job reports zero broken internal links across all `.md` files under `docs/architecture/` and fails on any non-zero count. [Completeness, Spec §FR-021(b), SC-004]
- [ ] CHK052 — MUST verify the `docs-arch` job checks every spec number 001–037 (excluding CI-configured archived numbers) for ≥ 1 architecture citation and fails on any uncited number. [Completeness, Spec §FR-021(c), SC-004, SC-005]
- [ ] CHK053 — MUST confirm the `docs-arch` job computes the SHA256 hash of each `.drawio` file, compares it against `docs/architecture/.diagram-hashes`, and fails on any mismatch (indicating a stale PNG export). [Completeness, Spec §FR-021(d)]
- [ ] CHK054 — MUST verify the `docs-arch` job fails if any row in `docs/architecture/known-gaps.md` has an empty or "TBD" Follow-up Task Ref column. [Completeness, Spec §FR-023, SC-008]
- [ ] CHK055 — MUST confirm no additional `.markdownlint.jsonc` per-path exceptions were added for architecture pages; the existing relaxations (`line-length: false`, `MD033: false`, `MD024: siblings_only`) MUST be sufficient. [Consistency, Spec §FR-022, Clarification Q3]

---

## 8 — Known-Gaps Registry Hygiene

- [ ] CHK056 — MUST confirm `docs/architecture/known-gaps.md` exists at exactly that path. [Completeness, Spec §FR-023]
- [ ] CHK057 — MUST verify the registry uses a Markdown table with columns in this order: Area/Spec, Gap Description, Follow-up Task Ref, Date Identified, Status. [Clarity, Spec §FR-023, Clarification Q4]
- [ ] CHK058 — MUST confirm every row in the registry carries a non-empty, non-"TBD" Follow-up Task Ref (task ID, issue number, or equivalent concrete reference). [Completeness, Spec §FR-023, SC-008]
- [ ] CHK059 — MUST verify the three root-level pre-existing docs (`capacity-model.md`, `cosmos-partitioning.md`, `spec-035-middleware-and-offline.md`) each have a registry entry with a follow-up migration task. [Completeness, Spec §FR-005, Assumption]
- [ ] CHK060 — MUST confirm the Bicep Module Dependency Graph deferral (SC-007 Note) is recorded in the registry with a follow-up task referencing the tooling-generation approach. [Completeness, Spec §SC-007 Note]
- [ ] CHK061 — MUST verify any spec number with no natural architecture-page home has its own registry entry (not batched silently). [Completeness, Spec §FR-011, Edge Case]
- [ ] CHK062 — MUST confirm the duplicate `036-*` directory is documented in the registry. [Completeness, Spec §Assumption]
- [ ] CHK063 — MUST verify a registry entry exists for the Foundry carve-out non-AU region list if any uncertainty remains at merge time, citing `infra/parameters/foundry-carveout.yaml` as the source of truth. [Completeness, Spec §Edge Case, FR-016]

---

## 9 — Page Standard Compliance

- [ ] CHK064 — MUST confirm every architecture page (new and updated) opens with a one-sentence purpose statement as its first substantive paragraph. [Completeness, Spec §FR-003]
- [ ] CHK065 — MUST verify every architecture page explicitly lists its target persona clusters (not implied — listed). [Completeness, Spec §FR-003]
- [ ] CHK066 — MUST confirm every architecture page embeds at least one diagram (inline image reference to a `.png` in the same repository). [Completeness, Spec §FR-003]
- [ ] CHK067 — MUST verify every architecture page cites at least one spec number or ADR in its source-links section. [Completeness, Spec §FR-003, FR-012]
- [ ] CHK068 — MUST confirm every architecture page is discoverable from `docs/architecture/README.md` within two navigation steps. [Completeness, Spec §FR-001, FR-003]
- [ ] CHK069 — MUST verify all six pre-existing documents have updated front-matter containing a link back to `docs/architecture/README.md` (not just a hope that readers find it). [Completeness, Spec §FR-005]
- [ ] CHK070 — MUST confirm the ADR index page (`docs/architecture/adr/README.md`) is a cross-reference table showing, for each ADR: decision number, title, status, date, and motivating spec(s). [Completeness, Spec §US4 SC4, FR-004]

---

## 10 — Constitutional Alignment

- [ ] CHK071 — MUST confirm the AIIMS functional view (`OPS-01`) shows all 10 AIIMS roles as named actors, each with ≥ 1 interaction line to a system component. [Completeness, Spec §FR-013, US2 SC4]
- [ ] CHK072 — MUST verify the container/component C4 views reflect the Azure three-tier pattern (presentation, application, data tiers) consistent with the project constitution. [Consistency, Spec §FR-004]
- [ ] CHK073 — MUST confirm all four PPRR phases (Prevention, Preparedness, Response, Recovery) are visible across the operational views — either in `OPS-01`, `OPS-02`, or annotated sequence diagrams. [Coverage, Spec §FR-013, Constitution]
- [ ] CHK074 — MUST verify `SEQ-03` (Evacuation Five-Stage Flow) shows all five evacuation stages as distinct steps or swim-lane segments, none collapsed or omitted. [Completeness, Spec §FR-010(c), SC-007 SEQ-03]
- [ ] CHK075 — MUST confirm `SEQ-04` (Recovery Transition) shows all six recovery principles and all four environments, labelled explicitly — not referenced by number only. [Completeness, Spec §FR-010(d), SC-007 SEQ-04]
- [ ] CHK076 — MUST verify NCM/NJCOP integration with NEMA is shown in `SECTOR-03` (Integration-Point Map) or `OPS-01`, with the data exchange format labelled. [Completeness, Spec §FR-014, US3 SC3]
- [ ] CHK077 — MUST confirm `GOV-01` (WAF Pillar Mapping) covers all five Azure WAF pillars (Reliability, Security, Cost Optimisation, Operational Excellence, Performance Efficiency), linking each to relevant architecture components and spec citations. [Completeness, Spec §FR-004, US4 SC5, SC-007 GOV-01]

---

## 11 — Per-Diagram Inventory Checks (SC-007 Named Diagrams)

*Apply each line independently. For each diagram: `.drawio` source MUST exist; sibling `.png` MUST exist; entry MUST be present in `.diagram-hashes`; ≥ 1 architecture page MUST reference the diagram; persona-cluster applicability MUST be tagged on the referencing page.*

- [ ] CHK078 — **C4-L1** (System Context): `.drawio` + `.png` present; hash entry present; ≥ 1 referencing page; all required external systems visible; FR-004, FR-002 persona tags present. [Spec §SC-007 #1]
- [ ] CHK079 — **C4-L2** (Container): `.drawio` + `.png` present; hash entry present; ≥ 1 referencing page; all 11 containers/backing services labelled. [Spec §SC-007 #2]
- [ ] CHK080 — **C4-L3-API** (Component: API — FastAPI): `.drawio` + `.png` present; hash entry present; ≥ 1 referencing page; internal components labelled; FR-004 cite on page. [Spec §SC-007 #3]
- [ ] CHK081 — **C4-L3-Web** (Component: Web — Next.js): `.drawio` + `.png` present; hash entry present; ≥ 1 referencing page; internal components labelled. [Spec §SC-007 #4]
- [ ] CHK082 — **C4-L3-Agents** (Component: Agents Runtime — 5 agents): `.drawio` + `.png` present; hash entry present; all 5 agents named; model-gateway interaction shown; ≥ 1 referencing page. [Spec §SC-007 #5]
- [ ] CHK083 — **C4-L3-Ingest** (Component: Ingest Service): `.drawio` + `.png` present; hash entry present; ≥ 1 referencing page; downstream routing to Event Hubs/Cosmos shown. [Spec §SC-007 #6]
- [ ] CHK084 — **SEQ-01** (Alert Authoring → Human Approval → Publication): `.drawio` + `.png` present; hash entry present; human-in-the-loop checkpoint visually distinct; publication step appears only after approval; ≥ 1 referencing page. [Spec §SC-007 #7, FR-009, FR-010(a)]
- [ ] CHK085 — **SEQ-02** (Cross-Agency Recommendation → Approval → Execution): `.drawio` + `.png` present; hash entry present; human-in-the-loop checkpoint visually distinct; ≥ 1 referencing page. [Spec §SC-007 #8, FR-009, FR-010(b)]
- [ ] CHK086 — **SEQ-03** (Evacuation Five-Stage Flow): `.drawio` + `.png` present; hash entry present; all 5 stages explicitly shown; human gate marked; ≥ 1 referencing page. [Spec §SC-007 #9, FR-009, FR-010(c)]
- [ ] CHK087 — **SEQ-04** (Recovery Transition): `.drawio` + `.png` present; hash entry present; 6 recovery principles + 4 environments labelled; ≥ 1 referencing page. [Spec §SC-007 #10, FR-010(d)]
- [ ] CHK088 — **SEQ-05** (Audit-Trail Provenance Flow): `.drawio` + `.png` present; hash entry present; every actuation shows logging, review access, and evidence capture; actuation callout present; ≥ 1 referencing page. [Spec §SC-007 #11, FR-010(e), FR-020]
- [ ] CHK089 — **SEQ-06** (Graceful-Degradation Behaviour): `.drawio` + `.png` present; hash entry present; degraded capabilities, operational capabilities, and fallback paths each labelled; ≥ 1 referencing page. [Spec §SC-007 #12, FR-010(f)]
- [ ] CHK090 — **OPS-01** (AIIMS System Context): `.drawio` + `.png` present; hash entry present; all 10 AIIMS roles visible as named actors; each role has ≥ 1 interaction line; ≥ 1 referencing page. [Spec §SC-007 #13, FR-013]
- [ ] CHK091 — **OPS-02** (Escalation Paths — L1 → L2 → L3): `.drawio` + `.png` present; hash entry present; each level transition shows triggering condition, responsible AIIMS role, and resulting system action; ≥ 1 referencing page. [Spec §SC-007 #14, FR-013]
- [ ] CHK092 — **SECTOR-01** (Multi-Jurisdiction Tenancy): `.drawio` + `.png` present; hash entry present; all 8 jurisdictions + Commonwealth shown; isolation boundary, Cosmos DB partition key alignment, and lead-agency designation labelled; ≥ 1 referencing page. [Spec §SC-007 #15, FR-015]
- [ ] CHK093 — **SECTOR-02** (Ingestion Data-Flow): `.drawio` + `.png` present; hash entry present; CAP/EDXL/GeoJSON path from external feed through Event Hubs to Cosmos DB to consuming agent visible end-to-end on one diagram; ≥ 1 referencing page. [Spec §SC-007 #16, FR-014]
- [ ] CHK094 — **SECTOR-03** (Integration-Point Map): `.drawio` + `.png` present; hash entry present; BoM, GA, NEMA, and all named agency systems shown with data format and ingestion endpoint labelled; NCM/NJCOP integration labelled; ≥ 1 referencing page. [Spec §SC-007 #17, FR-014]
- [ ] CHK095 — **SECTOR-04** (Jurisdiction-Filter Behaviour): `.drawio` + `.png` present; hash entry present; cross-state hand-off rules (RFS → SES → local-gov example) and authority boundaries shown at each transition; ≥ 1 referencing page. [Spec §SC-007 #18, FR-015]
- [ ] CHK096 — **SEC-01** (AU-Residency and Data-Classification): `.drawio` + `.png` present; hash entry present; AU boundary, "Permitted Non-AU Foundry Inference Zone (registry-gated)" label, and model-gateway redaction point each visible and labelled; zero hard-coded non-AU region names; ≥ 1 referencing page. [Spec §SC-007 #19, FR-016]
- [ ] CHK097 — **SEC-02** (RBAC Role/Permission Matrix): `.drawio` + `.png` present; hash entry present; every named AIIMS role mapped to platform permissions; spec citations present per role row; ≥ 1 referencing page. [Spec §SC-007 #20, FR-017]
- [ ] CHK098 — **SEC-03** (Trust-Boundary Diagram): `.drawio` + `.png` present; hash entry present; every boundary crossing labelled with the specific auth/authz mechanism; external ingestion path traced; ≥ 1 referencing page. [Spec §SC-007 #21, FR-018]
- [ ] CHK099 — **SEC-04** (SLI/SLO Model): `.drawio` + `.png` present; hash entry present; SLI definition, SLO target %, and error-budget burn-rate alert thresholds specified per key service; ≥ 1 referencing page. [Spec §SC-007 #22, FR-019]
- [ ] CHK100 — **DEPLOY-01** (CI/CD Pipeline): `.drawio` + `.png` present; hash entry present; what-if/plan gates, manual approval steps, and deployment targets (Container Apps) each visible and labelled; ≥ 1 referencing page. [Spec §SC-007 #23, US6 SC1]
- [ ] CHK101 — **DEPLOY-02** (Azure Resource Topology — `rg-ama`): `.drawio` + `.png` present; hash entry present; all named resources present: `ca-api`, `ca-agents`, `ca-ingest`, `cosmos-ama-zo6bb5`, `app-ama-zo6bb5`, Azure AI Search, Service Bus, Event Hubs, Application Insights, Key Vault; Azure stencils used; ≥ 1 referencing page. [Spec §SC-007 #24, US6 SC2]
- [ ] CHK102 — **DEPLOY-03** (Cosmos DB Partitioning Scheme): `.drawio` + `.png` present; hash entry present; partition key strategy traceable for a disaster-event document; alignment with multi-jurisdiction isolation model shown; ≥ 1 referencing page. [Spec §SC-007 #25, US6 SC3]
- [ ] CHK103 — **GOV-01** (WAF Pillar Mapping): `.drawio` + `.png` present; hash entry present; all five Azure WAF pillars (Reliability, Security, Cost Optimisation, Operational Excellence, Performance Efficiency) represented; each pillar linked to relevant architecture components and specs; ≥ 1 referencing page. [Spec §SC-007 #26, FR-004]

---

## 12 — Per-Page Standard Compliance

*Apply to every new or updated architecture markdown page. Each line is a binary gate.*

- [ ] CHK104 — **Index** (`docs/architecture/README.md`): passes `markdownlint-cli2` clean against existing ruleset; all internal links valid; persona-cluster sections present; no 404 PNG paths. [Completeness, Spec §FR-001, FR-022]
- [ ] CHK105 — **C4 Architecture pages** (`c4/system.md`, `c4/container.md`, new C4-L3-* pages): each passes `markdownlint-cli2` clean; all embedded image refs valid; purpose sentence + persona clusters listed; spec/ADR citations present. [Completeness, Spec §FR-003, FR-022]
- [ ] CHK106 — **Sequence diagram pages** (pages hosting SEQ-01 through SEQ-06): each passes `markdownlint-cli2` clean; all embedded image refs valid; human-in-the-loop callout described in prose where applicable; spec citations present. [Completeness, Spec §FR-003, FR-010, FR-022]
- [ ] CHK107 — **Operational pages** (pages hosting OPS-01, OPS-02): each passes `markdownlint-cli2` clean; all embedded image refs valid; AIIMS roles enumerated in page prose; spec citations present. [Completeness, Spec §FR-003, FR-013, FR-022]
- [ ] CHK108 — **Sector pages** (pages hosting SECTOR-01 through SECTOR-04): each passes `markdownlint-cli2` clean; all embedded image refs valid; jurisdiction list or integration system list confirmed in prose; spec citations present. [Completeness, Spec §FR-003, FR-014, FR-015, FR-022]
- [ ] CHK109 — **Security/compliance pages** (pages hosting SEC-01 through SEC-04): each passes `markdownlint-cli2` clean; all embedded image refs valid; AU residency and/or RBAC/trust-boundary scope described in prose; FR-016 through FR-020 citations present. [Completeness, Spec §FR-003, FR-016–020, FR-022]
- [ ] CHK110 — **Deployment pages** (pages hosting DEPLOY-01 through DEPLOY-03): each passes `markdownlint-cli2` clean; all embedded image refs valid; `rg-ama` resource list and/or pipeline-gate description in prose; spec citations present. [Completeness, Spec §FR-003, FR-022]
- [ ] CHK111 — **Governance page** (page hosting GOV-01): passes `markdownlint-cli2` clean; all embedded image refs valid; all five WAF pillars named in prose; ADR cross-references present; spec citations present. [Completeness, Spec §FR-003, FR-004, FR-022]
- [ ] CHK112 — **ADR navigation index** (`docs/architecture/adr/README.md`): passes `markdownlint-cli2` clean; cross-reference table present with columns (decision #, title, status, date, motivating spec); no ADR files physically relocated from `docs/decisions/`. [Completeness, Spec §FR-004, Clarification Q2]
- [ ] CHK113 — **Known-gaps registry** (`docs/architecture/known-gaps.md`): passes `markdownlint-cli2` clean; Markdown table present with correct columns; zero rows with empty or "TBD" Follow-up Task Ref. [Completeness, Spec §FR-023, SC-008]
- [ ] CHK114 — **Pre-existing docs front-matter** (all 6 pre-existing architecture documents): each contains updated front-matter with a link to `docs/architecture/README.md`; no pre-existing document has been moved from its original path. [Completeness, Spec §FR-005]
- [ ] CHK115 — **Accessibility page** (Technical-Experience cluster page): passes `markdownlint-cli2` clean; WCAG coverage map scoped to existing implementations only (no new requirements introduced); end-user interaction patterns described; spec citations present. [Completeness, Spec §FR-002, Assumption]

---

## Roll-Up Acceptance Gates

*Final merge blockers — ALL must pass.*

- [ ] CHK116 — MUST confirm `docs-arch` CI job exits 0 on this PR (zero PNG-without-drawio, zero broken links, zero uncited spec 001–037, zero stale hashes, zero empty gap-registry refs). [SC-004, Spec §FR-021–FR-023]
- [ ] CHK117 — MUST confirm total distinct `.drawio`/`.png` diagram pairs ≥ 26 matching the SC-007 named inventory; any shortfall is blocking unless paired with a known-gap entry and a follow-up task. [SC-007, Spec §SC-007]
- [ ] CHK118 — MUST confirm a new joiner familiar with AIIMS and Azure can reach a diagram answering each of the four orientation questions ("what runs where / who talks to whom / where does data live / where does a human gate the loop") in ≤ 2 navigation steps from `docs/architecture/README.md`. [SC-001, Spec §SC-001]
- [ ] CHK119 — MUST confirm a compliance reviewer can locate the AU-residency boundary, the Foundry carve-out zone label, and the model-gateway redaction enforcement point on `SEC-01` without opening any source file. [SC-003, Spec §SC-003]
- [ ] CHK120 — MUST confirm 100% of specs 001–037 (excluding CI-registered archived numbers) are cited; all exclusions are documented in `docs/architecture/known-gaps.md` with non-empty Follow-up Task Refs. [SC-005, Spec §SC-005]
- [ ] CHK121 — MUST confirm every actuation sequence diagram (SEQ-01, SEQ-02, SEQ-03, SEQ-05 at minimum) contains ≥ 1 visually distinct human-in-the-loop checkpoint marker confirmed by manual review, not CI alone. [SC-006, Spec §SC-006, FR-009]

---

## Notes

- Mark items `[x]` when confirmed passing; add inline comment with evidence (e.g., link to CI run, diagram path, or specific line reference).
- Items marked `[Gap]` in their tag indicate a requirement that may not yet be written in the spec; confirm the gap is intentional or file a follow-up.
- If a blocking item cannot be resolved before merge, open a tracked issue and add a known-gaps registry entry — silence is not acceptable.
- Each `/speckit.checklist` run creates a new file; this file (`architecture-review.md`) is the canonical PR gate checklist for `001-arch-docs-refresh`.
