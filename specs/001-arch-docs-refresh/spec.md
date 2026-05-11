# Feature Specification: Comprehensive Architectural Documentation & Diagrams Refresh

**Feature Branch**: `001-arch-docs-refresh`
**Created**: 2026-05-11
**Status**: Draft
**Motivated by**: New-joiner onboarding gap, compliance audit readiness, and the absence of navigable cross-persona architecture documentation across all 30+ shipped specs (001–037)

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — New Joiner Architecture Orientation (Priority: P1)

A new team member who already understands AIIMS and Azure cloud opens the repository and navigates to `docs/architecture/README.md`. Within 60 minutes they can answer: "What runs where, who talks to whom, where does the data live, and where does a human gate the loop?"

**Why this priority**: This is the single highest-value deliverable — without a navigable index, every other diagram is hard to discover. It also serves as the acceptance gate for every other story: if the index works and the diagrams answer these four questions, all other stories are implicitly satisfied.

**Independent Test**: Check out the branch and open `docs/architecture/README.md` with no other guidance. A person familiar with AIIMS and Azure should be able to navigate to a satisfying answer to each of the four questions within 60 minutes using only the linked pages and diagrams.

**Acceptance Scenarios**:

1. **Given** a fresh clone of the repo on the `001-arch-docs-refresh` branch, **When** a reader opens `docs/architecture/README.md`, **Then** every linked page and diagram loads without a 404, all diagram PNG files are present, and every PNG has a matching `.drawio` source file in the same directory.
2. **Given** the index page, **When** a reader selects their persona cluster (Operational / Sector / Technical — Architecture / Build / Quality / Experience), **Then** they reach a page with at least one diagram answering that cluster's primary architecture question within two navigation steps.
3. **Given** the system-context diagram, **When** a reader traces the human-in-the-loop path, **Then** they can identify every actuation diagram that highlights human approval checkpoints, confirmed by a visible legend or callout on each such diagram.

---

### User Story 2 — Operational Persona: Incident Commander Situational Awareness (Priority: P1)

An Incident Commander, using AIIMS Level 2 protocols, needs to understand the system's alert-authoring → human-approval → publication sequence, the escalation path from L1 to L3 incident levels, and the graceful-degradation behaviour when a subsystem is partially unavailable.

**Why this priority**: The operational persona set drives the core value proposition of the AMA platform; their documentation needs are highest-stakes and most likely to be evaluated by external reviewers or auditors.

**Independent Test**: Open the sequence diagram for alert authoring → approval → publication without opening any source code. The diagram should make all three stages and the human gate visible within one page.

**Acceptance Scenarios**:

1. **Given** the alert-authoring sequence diagram, **When** a reviewer traces the flow end-to-end, **Then** every human approval checkpoint is explicitly marked (e.g., a distinct shape, label, or swim-lane), and the publication step only appears after the approval step.
2. **Given** the escalation-paths diagram, **When** a reader follows the L1 → L2 → L3 path, **Then** each level transition shows the triggering condition, the responsible AIIMS role, and the resulting system action.
3. **Given** the graceful-degradation view, **When** a reader identifies a named subsystem as unavailable, **Then** the diagram shows which capabilities degrade, which remain operational, and which fallback paths are activated.
4. **Given** the AIIMS system-context diagram, **When** a reader maps Incident Commander, Operations, Planning, Logistics, Public Information, Field Coordinator, and Resilience Planner roles, **Then** each role is shown as a named actor with at least one interaction line to a system component.

---

### User Story 3 — Sector Persona: Multi-Jurisdiction Data Isolation (Priority: P2)

A NSW RFS officer and a VIC CFA officer both need to understand how their data is isolated from each other inside the platform, how lead-agency designation works per state, and how incoming CAP/EDXL/GeoJSON signals travel from ingestion through to agent processing.

**Why this priority**: Jurisdiction isolation and data sovereignty are primary concerns for real-world adoption by state agencies and are frequently audited during procurement. This story also validates the multi-tenancy design across all 50+ named agencies.

**Independent Test**: Open the multi-jurisdiction tenancy diagram and the data-flow ingestion diagram without opening source code. The tenant isolation boundary and the signal path from external source to processed agent output should each be traceable on a single diagram.

**Acceptance Scenarios**:

1. **Given** the multi-jurisdiction tenancy diagram, **When** a reader identifies the NSW and VIC tenants, **Then** the diagram shows the isolation boundary between them, the Cosmos DB partition key alignment, and the per-state lead-agency designation mechanism.
2. **Given** the ingestion data-flow diagram, **When** a reader traces a CAP alert from an external feed (e.g., BoM weather), **Then** they can follow the path through Event Hubs or Service Bus into Cosmos DB and confirm which agent receives it, all on one diagram.
3. **Given** the integration-point map, **When** a reader looks up a named external system (BoM, GA, NEMA), **Then** the diagram shows which data format that system uses, which ingestion endpoint receives it, and which agent(s) consume it.
4. **Given** the jurisdiction-filter behaviour diagram (based on spec 022), **When** a reader traces a cross-state hand-off (e.g., RFS suppresses → SES recovery → local-gov welfare), **Then** the filter rules and authority boundaries are shown at each transition.

---

### User Story 4 — Technical Persona: Architecture Cluster — Full C4 Model (Priority: P2)

A Solution Architect or Azure Principal Architect needs a complete C4 model (Levels 1–4) covering every container and the key components inside each application, an ADR index, and a mapping to Azure WAF pillars.

**Why this priority**: The C4 model is the primary navigation artifact for technical reviewers, contract bidders, and architectural governance. Without it, the component-level and code-level diagrams have no structural home.

**Independent Test**: Navigate from the System Context (L1) to the Container view (L2), then to each application's Component view (L3) without leaving `docs/architecture/`. Confirm that every application listed in the Container view has a corresponding Component page.

**Acceptance Scenarios**:

1. **Given** the C4 System Context diagram (L1), **When** a reviewer counts external systems shown, **Then** all of the following appear: BoM weather feed, GA seismic feed, NEMA NCM, state agency CAP/EDXL sources, and the end-user browser/mobile client.
2. **Given** the C4 Container diagram (L2), **When** a reviewer lists containers, **Then** all deployed applications appear: API (FastAPI), Web (Next.js), Agents runtime (all 5 named agents), Ingest service, plus the backing services: Cosmos DB, Azure AI Search, Service Bus, Event Hubs, Application Insights, Key Vault, Azure OpenAI/Foundry.
3. **Given** the Component diagrams (L3) for each application container, **When** a reviewer traces a request from the Web UI through the API to an agent and back, **Then** internal components in each container are labelled and relationships are shown.
4. **Given** the ADR index page, **When** a reviewer searches for a decision by topic, **Then** each ADR entry shows: decision number, title, status, date, and the spec(s) that motivated it.
5. **Given** the WAF pillar mapping page, **When** a reviewer reads any one of the five pillars (Reliability, Security, Cost, Operational Excellence, Performance Efficiency), **Then** the relevant architecture components and design patterns addressing that pillar are listed and linked to diagrams or specs.

---

### User Story 5 — Technical Persona: Quality Cluster — Compliance & Security (Priority: P2)

A Compliance Auditor, Security Engineer, or SRE needs a single page that shows the AU-residency boundary, the Foundry carve-out for non-AU model hosting, and the model-gateway redaction enforcement in one view. They also need the RBAC role/permission matrix and the trust-boundary threat model.

**Why this priority**: AU data residency is a constitutional mandate (v1.2.0) and the Foundry carve-out is a non-obvious exception that must be documented clearly to pass sovereign data reviews. A single auditor-facing page for this reduces review time significantly.

**Independent Test**: Open the data-classification and AU-residency boundary diagram without opening source code. The AU boundary, the Foundry carve-out zone, and the redaction enforcement point should each be visible and labelled on a single diagram.

**Acceptance Scenarios**:

1. **Given** the AU-residency and data-classification diagram, **When** an auditor traces any data flow involving LLM inference, **Then** they can identify: (a) which data remains in AU regions, (b) which data crosses to non-AU regions for Foundry model inference, (c) where redaction is applied before data leaves the AU boundary.
2. **Given** the RBAC role/permission matrix, **When** a reviewer looks up any named AIIMS role, **Then** the matrix shows which platform permissions that role holds and which specs define those permission boundaries.
3. **Given** the trust-boundary and threat-model view, **When** a reviewer traces an ingestion path from an external agency, **Then** every trust-boundary crossing is labelled with the authentication/authorisation mechanism applied.
4. **Given** the SLI/SLO model page, **When** an SRE reads the error-budget section, **Then** they can identify the SLI definition, the SLO target, and the error-budget burn-rate alert thresholds for each key service.

---

### User Story 6 — Technical Persona: Build Cluster — Developer Orientation (Priority: P3)

A Software Developer or DevOps Engineer joining the project needs to understand the monorepo layout, CI/CD pipeline gates, Azure resource topology in `rg-ama`, Cosmos DB partitioning scheme, and the agent runtime + LLM model-gateway interaction, all without reading source code.

**Why this priority**: Build-cluster documentation accelerates contribution onboarding and reduces broken-pipeline incidents. It is lower priority than the compliance/operational views because it is more stable and partially covered by existing README files.

**Independent Test**: Open the CI/CD pipeline diagram and the Azure resource topology diagram. A DevOps engineer should be able to answer "which stages gate a deployment" and "which resource group contains the production containers" from those two diagrams alone.

**Acceptance Scenarios**:

1. **Given** the CI/CD pipeline diagram, **When** a developer reads the pipeline stages, **Then** the what-if/plan gates, manual approval steps, and deployment targets (Container Apps) are each visible and labelled.
2. **Given** the Azure resource topology diagram, **When** a reader locates `rg-ama`, **Then** all named resources appear: `ca-api`, `ca-agents`, `ca-ingest`, `cosmos-ama-zo6bb5`, `app-ama-zo6bb5`, plus Azure AI Search, Service Bus, Event Hubs, Application Insights, and Key Vault.
3. **Given** the Cosmos DB partitioning diagram, **When** a developer identifies the partition key strategy, **Then** they can trace how a disaster-event document is routed to a partition and confirm alignment with the multi-jurisdiction isolation model.
4. **Given** the Bicep module dependency graph, **When** a developer reads the dependency order, **Then** every Bicep module under `infra/bicep/` is represented and inter-module dependencies are shown as directed edges.

---

### User Story 7 — CI Validation: Documentation-as-Code (Priority: P3)

A pull-request reviewer or CI system needs to verify that every PNG diagram has a matching `.drawio` source file, all internal links in architecture pages resolve, and all 37 shipped specs (001–037) are cross-referenced from at least one architecture page.

**Why this priority**: Without CI enforcement, the documentation will drift from the codebase over time. This story is the mechanical quality gate that keeps all other stories honest.

**Independent Test**: Trigger the `docs-arch` CI job on the branch. It should report: (a) count of PNGs without a `.drawio` sibling (must be 0), (b) count of broken internal links (must be 0), (c) count of spec numbers 001–037 with no architecture cross-reference (must be 0, excluding confirmed archived/duplicate numbers).

**Acceptance Scenarios**:

1. **Given** the `docs-arch` CI job definition, **When** it runs on the branch, **Then** it checks every `*.png` file under `docs/architecture/` for a sibling `*.drawio` file and fails the build if any is missing.
2. **Given** the link-checker step in `docs-arch`, **When** it scans all `.md` files under `docs/architecture/`, **Then** it reports zero broken internal links (relative `[text](path)` references that resolve to non-existent files).
3. **Given** the spec cross-reference check, **When** it scans all architecture `.md` pages, **Then** every spec number from 001 to 037 appears as a citation in at least one page (spec numbers confirmed as archived or superseded are excluded and documented in a known-gaps registry).

---

### Edge Cases

- **Archived / duplicate spec numbers**: Spec numbers that are confirmed duplicates or archived (e.g., two `036-*` directories exist) must be explicitly listed in a known-gaps registry rather than silently omitted from cross-reference counts.
- **Diagram source vs PNG mismatch**: If a `.drawio` file is updated but the exported PNG is not regenerated, the CI job MUST detect the staleness via a SHA256 hash manifest (`docs/architecture/.diagram-hashes`). File modification timestamps MUST NOT be used — they are unreliable after `git clone` (all files share the clone timestamp) — and a hash manifest provides git-stable, auditable provenance for every diagram version. The manifest is updated as part of the diagram-export step; a hash mismatch between the manifest entry and the current `.drawio` file fails the build.
- **Existing sparse docs conflict**: The six pre-existing architecture documents (`c4/system.md`, `c4/container.md`, `sequence/monitoring-risk-comms.md`, `capacity-model.md`, `cosmos-partitioning.md`, `spec-035-middleware-and-offline.md`) must be either incorporated into the new structure with updated front-matter or explicitly superseded and linked from the new index — not silently orphaned.
- **Cross-reference gap where no page covers a spec**: When a spec has no natural home in any architecture view, a gap entry is created in the known-gaps registry with a follow-up task, rather than forcing a spurious mention.
- **Foundry carve-out accuracy**: The AU-residency diagram must accurately reflect which Azure OpenAI/Foundry model-hosting regions are non-AU; if this is unknown at spec time, it is flagged as a known gap with a follow-up task.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Documentation Structure

- **FR-001**: The documentation set MUST include a single top-level index at `docs/architecture/README.md` from which every architecture page is reachable within two navigation steps.
- **FR-002**: The index MUST organise pages by persona cluster: Operational (AIIMS roles), Sector (jurisdictions), Technical — Architecture, Technical — Build, Technical — Quality, Technical — Experience (accessibility documentation, WCAG coverage map, and end-user interaction patterns).
- **FR-003**: Every architecture page MUST open with a one-sentence purpose statement, list its target persona clusters, embed at least one diagram, and link to the spec(s) and/or ADRs that motivated it.
- **FR-004**: The documentation MUST be structured around the C4 model (System Context L1, Container L2, Component L3, optional Code L4) plus auxiliary views: data, security/trust, deployment, sequence, capacity, governance, accessibility.
- **FR-005**: Pre-existing architecture documents MUST be kept in their current locations; their front-matter MUST be updated to include a link to `docs/architecture/README.md` (the new index), and the index MUST include a redirect note pointing to each pre-existing document's current path. Documents that cannot be incorporated by reference (e.g., those at the root of `docs/architecture/` with no clear view-type subdir home) MUST be explicitly listed in the known-gaps registry with a follow-up task for physical migration during the planning phase. They MUST NOT be silently orphaned.

#### Diagram Requirements

- **FR-006**: Every diagram MUST be authored as a Draw.io `.drawio` source file checked into the repository under `docs/architecture/`.
- **FR-007**: Every `.drawio` source file MUST have a sibling PNG export file with the same base name in the same directory.
- **FR-008**: Draw.io diagrams MUST use the Azure shape stencils where depicting Azure services.
- **FR-009**: Every actuation diagram (any diagram showing a system taking an action with real-world consequence) MUST highlight human-in-the-loop checkpoints with a distinct visual treatment (labelled shape, colour, or swim-lane boundary).
- **FR-010**: Sequence diagrams MUST be provided for each of these flows: (a) alert authoring → human approval → publication; (b) cross-agency action recommendation → approval → execution; (c) evacuation five-stage flow; (d) recovery transition; (e) audit-trail provenance flow; (f) graceful-degradation behaviour during partial outages.

#### Coverage Requirements

- **FR-011**: All shipped spec numbers 001 through 037 MUST be cited from at least one architecture page; spec numbers confirmed as archived or superseded MUST be listed in a known-gaps registry.
- **FR-012**: Conversely, every architecture page MUST cite the spec number(s) that motivated its content.
- **FR-013**: Every AIIMS functional role listed in the constitution (Incident Commander, Operations, Planning, Logistics, Public Information, Field Coordinator, Resilience Planner, Executive Leader, Observer/Auditor, Risk Manager) MUST appear as a named actor in at least one diagram.
- **FR-014**: The integration-point map MUST cover every named external system: BoM weather, GA seismic, NEMA NCM, and all CAP/EDXL/GeoJSON-producing agency systems.
- **FR-015**: The multi-jurisdiction view MUST represent all eight state/territory jurisdictions (NSW, VIC, QLD, SA, WA, TAS, ACT, NT) plus Commonwealth agencies, showing tenant isolation and lead-agency designation.

#### Compliance & Security Requirements

- **FR-016**: A dedicated AU-residency and data-classification page MUST show in one diagram: the AU data-residency boundary, the Foundry carve-out zone for non-AU model hosting, and the model-gateway redaction enforcement point. The carve-out zone MUST be labelled as a mechanism zone — "Permitted Non-AU Foundry Inference Zone (registry-gated)" — with an annotation stating the current number of active non-AU entries from `infra/parameters/foundry-carveout.yaml` (as of spec authoring: zero non-AU entries; all three production deployments are in `australiaeast`). Specific non-AU region names MUST NOT be hard-coded in the diagram; the registry at `infra/parameters/foundry-carveout.yaml` is the single source of truth for permitted regions. The AU boundary zone covers `australiaeast` and `australiasoutheast` for all data-plane resources (Cosmos DB, Storage, Service Bus, Event Grid, Application Insights, Log Analytics, Key Vault, ACR, audit, evidence stores).
- **FR-017**: An RBAC role/permission matrix MUST map every named AIIMS role to its platform permissions and cite the spec(s) that define those boundaries.
- **FR-018**: A trust-boundary diagram MUST label every boundary crossing with the authentication or authorisation mechanism applied.
- **FR-019**: An SLI/SLO model page MUST define the SLI, the SLO target, and the error-budget alert thresholds for each key service.
- **FR-020**: The audit-trail provenance flow diagram MUST show how every actuation is logged, who can review the log, and what evidence is captured for compliance reporting.

#### Documentation-as-Code Requirements

- **FR-021**: A CI job named `docs-arch` MUST verify: (a) every PNG under `docs/architecture/` has a sibling `.drawio` source; (b) zero broken internal links in all `.md` files under `docs/architecture/`; (c) every spec number 001–037 (excluding documented archived numbers) appears in at least one architecture page; (d) every `.drawio` file's SHA256 hash matches its entry in `docs/architecture/.diagram-hashes` — a mismatch signals a stale PNG export and fails the build.
- **FR-022**: All architecture markdown MUST pass `markdownlint` with the project's existing ruleset (`.markdownlint.jsonc` at repo root) without exceptions specific to this feature. The `docs-arch` CI job MUST invoke `markdownlint-cli2` via `npx markdownlint-cli2 "docs/architecture/**/*.md"` — no new workspace devDependency is required. The existing ruleset relaxations (`line-length: false`, `MD033: false`, `MD024: siblings_only`) already cover diagram-heavy pages with long image paths and HTML comment annotations; no additional per-path exceptions are needed for architecture pages.
- **FR-023**: A known-gaps registry MUST be maintained at `docs/architecture/known-gaps.md`; entries MUST use a Markdown table with columns: Area/Spec, Gap Description, Follow-up Task Ref, Date Identified, Status. Every row MUST carry a non-empty Follow-up Task Ref — the CI job (`docs-arch`) MUST fail if any row's Follow-up Task Ref column is empty or contains only a placeholder such as "TBD".

### Amendment 1 (2026-05-11) — persona-cluster review additions

- **FR-024**: A PPRR phase-overlay diagram (`OPS-03`) MUST show, for each of the four PPRR phases (Prevention, Preparedness, Response, Recovery), which platform agents and which AIIMS roles are active in that phase, including phase-overlap regions. Sourced from constitution §PPRR Lifecycle.
- **FR-025**: A test-pyramid diagram (`QUAL-01`) MUST visualise the five-tier test taxonomy used in the project (unit, contract, integration, simulation, end-to-end), showing relative volume per tier and the primary tooling for each (pytest for unit/contract/integration/simulation/backend-e2e; Playwright for web e2e; simulation harness for simulation). Unit MUST appear as the base-of-pyramid tier with the highest relative volume (~159 files). Secondary tiers (benchmark, load, security, chaos) MAY be shown as supplementary lanes but are not required for diagram completeness. Required by the QA cluster. *Corrected by Session 2026-05-11 (Amendment 1) Q3 — original "four-tier" omitted unit, the largest tier and constitutionally mandated tier (§Quality Gates).*
- **FR-026**: A high-pressure ops dashboard user-journey diagram (`EXP-01`) MUST trace one canonical user-journey through the dashboard during an active incident, calling out perception/comprehension/action steps and the success-criteria → architecture component traceability used at each step. Required by the UX/PO cluster.

### Key Entities

- **Architecture Page**: A markdown document under `docs/architecture/` with a purpose statement, persona audience, at least one embedded diagram, and citations to specs and/or ADRs.
- **Diagram Pair**: A `.drawio` source file and its PNG sibling export; treated as an atomic unit for CI validation.
- **Known-Gaps Registry**: A Markdown table at `docs/architecture/known-gaps.md` with columns: Area/Spec, Gap Description, Follow-up Task Ref, Date Identified, Status. Every row must carry a non-empty Follow-up Task Ref; this format enables CI parsing (FR-021/FR-023) and GitHub UI review without additional tooling.
- **ADR (Architectural Decision Record)**: A short record capturing a significant architectural decision, its context, options considered, and the outcome. **Canonical home**: `docs/decisions/{spec-id}/{id}-{slug}.md` (e.g., `docs/decisions/036-foundry-rag-grounding/01-rag-optout-dependency-notifier.md`). The file `docs/architecture/adr/README.md` is a *navigation index* — a Markdown table cross-referencing all ADRs in `docs/decisions/` by decision number, title, status, date, and motivating spec(s) — and is NOT a canonical store for ADR files. No existing ADRs are moved.
- **Spec Cross-Reference**: An explicit citation of a spec number (e.g., `spec-022`) within an architecture page, confirming traceability between the shipped feature and its documentation.
- **Human-in-the-Loop Checkpoint**: A visually distinct marker on an actuation diagram indicating a point where a human must approve an action before the system proceeds.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new joiner familiar with AIIMS and Azure can answer the four orientation questions ("what runs where, who talks to whom, where does the data live, where does a human gate the loop?") within 60 minutes of opening `docs/architecture/README.md`, using only the linked pages and diagrams.
- **SC-002**: Every operational, sector, and technical persona cluster has at least one diagram answering its primary architecture question, reachable in two navigation steps from the index.
- **SC-003**: A compliance reviewer can locate the AU-residency boundary, the Foundry carve-out, and the model-gateway redaction enforcement on a single page without opening source code.
- **SC-004**: The `docs-arch` CI job reports zero broken internal links, zero PNGs without a matching `.drawio` source, and zero un-cited spec numbers (001–037, excluding documented archived numbers).
- **SC-005**: 100% of shipped specs (001–037, excluding confirmed archived/duplicate numbers) are cross-referenced from at least one architecture page, verified by the CI job.
- **SC-006**: Every actuation sequence diagram contains at least one human-in-the-loop checkpoint marker, verified by manual review against FR-009.
- **SC-007**: The documentation set contains a minimum of 20 distinct diagram pairs (`.drawio` + PNG) spanning all four C4 levels, auxiliary views (data, security, deployment, sequence, capacity, governance, accessibility), and persona-specific views. The named inventory below is the authoritative target list (32 diagrams as of Amendment 1, 2026-05-11); the CI count gate checks the total against this list. Any diagram deferred or merged must be recorded in the known-gaps registry with a follow-up task reference.

  **Named Diagram Inventory** (26 target diagrams):

  | # | ID | Title | View Type | Primary FR(s) |
  |---|-----|-------|-----------|---------------|
  | 1 | C4-L1 | System Context | C4 / Architecture | FR-004, US4 |
  | 2 | C4-L2 | Container | C4 / Architecture | FR-004, US4 |
  | 3 | C4-L3-API | Component: API (FastAPI) | C4 / Architecture | FR-004, US4 |
  | 4 | C4-L3-Web | Component: Web (Next.js) | C4 / Architecture | FR-004, US4 |
  | 5 | C4-L3-Agents | Component: Agents Runtime (5 agents) | C4 / Architecture | FR-004, US4 |
  | 6 | C4-L3-Ingest | Component: Ingest Service | C4 / Architecture | FR-004, US4 |
  | 7 | SEQ-01 | Alert Authoring → Human Approval → Publication | Sequence | FR-009, FR-010(a), US2 |
  | 8 | SEQ-02 | Cross-Agency Recommendation → Approval → Execution | Sequence | FR-009, FR-010(b), US2 |
  | 9 | SEQ-03 | Evacuation Five-Stage Flow | Sequence | FR-009, FR-010(c), US1 |
  | 10 | SEQ-04 | Recovery Transition | Sequence | FR-010(d), US1 |
  | 11 | SEQ-05 | Audit-Trail Provenance Flow | Sequence | FR-010(e), FR-020, US5 |
  | 12 | SEQ-06 | Graceful-Degradation Behaviour | Sequence | FR-010(f), US2 |
  | 13 | OPS-01 | AIIMS System Context (all 10 AIIMS roles × system interactions) | Operational | FR-013, US2 |
  | 14 | OPS-02 | Escalation Paths (L1 → L2 → L3) | Operational | FR-013, US2 |
  | 15 | SECTOR-01 | Multi-Jurisdiction Tenancy (8 jurisdictions + Commonwealth, lead-agency) | Sector | FR-015, US3 |
  | 16 | SECTOR-02 | Ingestion Data-Flow (CAP/EDXL/GeoJSON → Event Hubs → Cosmos → agents) | Data | FR-014, US3 |
  | 17 | SECTOR-03 | Integration-Point Map (BoM, GA, NEMA, agency systems) | Data | FR-014, US3 |
  | 18 | SECTOR-04 | Jurisdiction-Filter Behaviour (cross-state hand-off rules) | Sector | FR-015, US3 |
  | 19 | SEC-01 | AU-Residency and Data-Classification (incl. Foundry carve-out zone) | Security | FR-016, US5 |
  | 20 | SEC-02 | RBAC Role/Permission Matrix | Security | FR-017, US5 |
  | 21 | SEC-03 | Trust-Boundary Diagram | Security | FR-018, US5 |
  | 22 | SEC-04 | SLI/SLO Model | Security / Governance | FR-019, US5 |
  | 23 | DEPLOY-01 | CI/CD Pipeline (gates, approvals, deployment targets) | Deployment | US6 |
  | 24 | DEPLOY-02 | Azure Resource Topology (`rg-ama`, all named resources) | Deployment | US6 |
  | 25 | DEPLOY-03 | Cosmos DB Partitioning Scheme | Deployment / Data | US6 |
  | 26 | GOV-01 | WAF Pillar Mapping (5 pillars × components × specs) | Governance | FR-004, US4 |
  | 27 | RISK-01 | Hazard taxonomy + risk-register lifecycle | Operational (Risk Manager) | FR-013 (extension), US2 |
  | 28 | OPS-03 | PPRR phase-overlay (which agents activate in each phase) | Operational (Resilience Planner) | FR-024 (new), US2 |
  | 29 | SECTOR-05 | Cross-sector touch-points & partner data exchange | Sector (Cross-Sector) | FR-015 (extension), US3 |
  | 30 | BUILD-01 | Agent runtime + LLM client + model gateway integrated view | Technical-Build (AI/ML) | FR-014 (extension), US6 |
  | 31 | QUAL-01 | Test pyramid (unit / contract / integration / simulation / e2e) | Technical-Quality (QA) | FR-025 (new), US5 |
  | 32 | EXP-01 | High-pressure ops dashboard user-journey | Technical-Experience (UX) | FR-026 (new), US1 |

  *Note: Bicep Module Dependency Graph (mentioned in US6 scenario 4) is deferred to planning — it requires tooling to generate from `infra/bicep/` and may be autogenerated rather than hand-authored. A known-gap entry is created for it if not delivered.*
- **SC-008**: The known-gaps registry identifies any spec or architectural area not yet fully documented and assigns a follow-up task reference; the registry itself contains zero items with no follow-up reference.

---

## Assumptions

- The six pre-existing architecture documents are treated as inputs to be incorporated, not authoritative sources; they may contain stale information that this feature corrects.
- Spec numbers with duplicate directory entries (e.g., two `036-*` directories observed) will be treated as one shipped spec for cross-reference counting purposes; the duplication is noted in the known-gaps registry.
- The Foundry carve-out region list: inspection of `infra/parameters/foundry-carveout.yaml` (spec 036 FR-RAG-CV-01) confirms that all three current production deployments (`gpt-4o-mini`, `gpt-4o`, `text-embedding-3-large`) are in `australiaeast`; there are zero active non-AU entries. The constitution's NN-2 Amendment 1.2.0 carve-out is a registry-driven mechanism permitting any non-AU region when declared with proper justification and ≥3 approver identities (prod); no specific non-AU regions are pre-approved. The FR-016 compliance diagram labels the carve-out as a mechanism zone ("zero active non-AU entries") rather than naming specific regions, so auditors see accurate current state.
- Draw.io diagram generation may be assisted by the `drawio-mcp-diagramming` skill; all generated diagrams must be reviewed for accuracy before being committed.
- The `docs-arch` CI job is a new job added to the **existing `ci.yml` workflow** (`.github/workflows/ci.yml`); it does not create a new workflow file and does not replace or modify existing CI jobs. It runs on the same triggers as the `quality` job (push to `main`/`dev`/`staging`/`production`; PR to `main`) without path filtering, ensuring spec cross-reference correctness is checked on every PR regardless of whether the changed files are under `docs/architecture/`.
- Accessibility documentation (WCAG coverage map) scope is limited to documenting what is already implemented per existing specs; this feature does not introduce new accessibility requirements.
- The "Code" level (C4 L4) is optional and will only be produced where it adds material clarity beyond the Component level (C4 L3); the planning phase will determine which, if any, components warrant L4 diagrams.
- The `docs/architecture/` directory MUST be organised by view type, extending the pre-existing `c4/` and `sequence/` subdirectory convention with additional subdirectories as needed: `data/`, `security/`, `deployment/`, `governance/`, `accessibility/`, `operational/`, `quality/`. Persona-cluster navigation is expressed through the index page (`README.md`), not through the physical directory layout. Amendment 1 diagram placement (resolved by Session 2026-05-11 (Amendment 1) Q1): RISK-01 and OPS-03 → `operational/`; SECTOR-05 → `data/`; BUILD-01 → `c4/`; QUAL-01 → `quality/`; EXP-01 → `accessibility/`.
- Pre-existing architecture documents (`c4/system.md`, `c4/container.md`, `sequence/monitoring-risk-comms.md`, `capacity-model.md`, `cosmos-partitioning.md`, `spec-035-middleware-and-offline.md`) are kept in their current locations during this feature; their front-matter is updated to link to the new index. Documents at the root of `docs/architecture/` (i.e., `capacity-model.md`, `cosmos-partitioning.md`, `spec-035-middleware-and-offline.md`) do not currently fit a named view-type subdirectory and are listed in the known-gaps registry with follow-up tasks for optional physical migration in a subsequent iteration.

---

## Clarifications

### Session 2026-05-11

- **Q1 — Technical-Experience persona scope**: What does the "Technical — Experience" persona cluster cover? FR-002 listed it without a definition, and no user story addressed it. → **A**: Accessibility documentation, WCAG coverage map, and end-user interaction patterns. *Rationale: The Assumptions section already scoped "Accessibility documentation (WCAG coverage map)" as part of this feature; constitution §VI-C mandates priority consideration of vulnerable populations, reinforcing accessibility as a first-class concern. Adopted answer: max auditability + constitution alignment.*

- **Q2 — Directory structure for `docs/architecture/`**: Should pages be organised by persona cluster, by C4 level, or by view type? FR-002 implies persona-cluster organisation; pre-existing docs already use view-type subdirs (`c4/`, `sequence/`). → **A**: View-type subdirectory structure (extending `c4/` and `sequence/` with `data/`, `security/`, `deployment/`, `governance/`, `accessibility/`); persona-cluster navigation is expressed through the index, not the directory layout. *Rationale: Prior-spec convention (3 of 6 existing docs already in view-type subdirs); avoids breaking paths; index provides the persona-cluster lens per FR-001/FR-002.*

- **Q3 — PNG staleness detection method**: The edge-case bullet offered "file modification timestamps or a hash manifest" without deciding; FR-021 was silent on the mechanism. → **A**: SHA256 hash manifest at `docs/architecture/.diagram-hashes`; timestamps are not used. *Rationale: Constitution §IV (full provenance and auditability); timestamps are unreliable after `git clone`; hash manifest is git-stable and cache-friendly. Adopted answer: maximises auditability.*

- **Q4 — Known-gaps registry format**: FR-023 mandated the registry but did not specify a format, making the CI "no empty follow-up ref" check (SC-008) un-implementable. → **A**: Markdown table with columns Area/Spec, Gap Description, Follow-up Task Ref, Date Identified, Status; every row must have a non-empty Follow-up Task Ref. *Rationale: Human-readable in GitHub UI, CI-parseable by regex, consistent with prior-spec matrix conventions; requires no extra tooling beyond markdownlint.*

- **Q5 — Pre-existing docs physical handling**: Should the 6 pre-existing architecture documents be physically moved to view-type subdirectories, or kept in place? → **A**: Keep in place; update their front-matter to link to the new index; the new index emits redirect notes to their current paths. The 3 root-level docs (`capacity-model.md`, `cosmos-partitioning.md`, `spec-035-middleware-and-offline.md`) are listed in the known-gaps registry with follow-up migration tasks. *Rationale: Moving files risks breaking external references and CI paths; prior-spec convention favours backward compatibility; physical migration deferred to planning phase per individual document assessment.*

### Session 2026-05-11 (Pass 2)

- **Q1 — Named diagram inventory (SC-007)**: SC-007 stated "minimum of 20 distinct diagram pairs" without naming them, making task decomposition ambiguous and the CI count gate unverifiable. Should the named inventory be enumerated in the spec now, or deferred to planning with a written deferral note? → **A**: Enumerate named inventory in the spec now (26 diagrams listed in SC-007 table). *Rationale: All 26 diagrams are directly derivable from FR-004, FR-010, FR-013–020, and the User Stories — the enumeration is not a planning-phase discovery but a spec-level obligation. Naming them here allows CI gate validation, task-level assignment in tasks.md, and prevents "which 20?" ambiguity during implementation. Constitution §IV (auditability): a concrete inventory is auditable; a floor count alone is not. Chosen to maximise auditability and reduce downstream rework risk.*

- **Q2 — ADR canonical home vs `docs/architecture/adr/README.md`**: The Key Entities section defined the ADR index as `docs/architecture/adr/README.md` but `docs/decisions/036-foundry-rag-grounding/` already exists as the active ADR store with 20 files (confirmed by directory listing). Should `docs/decisions/` remain canonical with `docs/architecture/adr/README.md` as a navigation cross-reference, or should ADRs migrate to `docs/architecture/adr/`? → **A**: `docs/decisions/{spec-id}/{id}-{slug}.md` is the canonical path pattern; `docs/architecture/adr/README.md` is a navigation index only — a cross-reference table, not a file store. No existing ADRs are moved. *Rationale: Moving 20 existing spec-036 ADRs would break the CI `rag-optout-binding-lint` step (which resolves paths in `docs/decisions/036-foundry-rag-grounding/`), all spec-036 ADR cross-references, and the constitution's footnote pattern. Prior-spec convention (Pass 1 Q5) favours backward compatibility. Key Entities updated accordingly.*

- **Q3 — Markdownlint CI invocation**: `.markdownlint.jsonc` exists at repo root but is absent from all existing `ci.yml` steps. FR-022 mandates markdownlint for architecture markdown. Should `docs-arch` invoke it via `npx markdownlint-cli2` (no new devDependency) or add a permanent workspace devDependency? → **A**: `npx markdownlint-cli2 "docs/architecture/**/*.md"` in the `docs-arch` job; no new permanent devDependency. No additional rule exceptions are needed for diagram-heavy pages — the existing `.markdownlint.jsonc` (`line-length: false`, `MD033: false`, `MD024: siblings_only`) already covers long image paths and HTML comment annotations. *Rationale: Leanest path; avoids polluting the monorepo dependency tree for a docs-only tool; satisfies FR-022's "existing ruleset without exceptions specific to this feature". FR-022 updated to specify the `npx markdownlint-cli2` invocation.*

- **Q4 — FR-016 Foundry carve-out zone labelling**: The `foundry-carveout.yaml` registry contains zero non-AU entries — all three current production Foundry deployments (`gpt-4o-mini`, `gpt-4o`, `text-embedding-3-large`) are in `australiaeast`. FR-016 requires the compliance diagram to show "the Foundry carve-out zone for non-AU model hosting." Should the diagram label specific non-AU regions (e.g., `eastus`, `swedencentral`) or label it as a registry-gated mechanism zone with current entry count? → **A**: Mechanism zone label — "Permitted Non-AU Foundry Inference Zone (registry-gated; zero active non-AU entries)" — with no specific region names hard-coded. *Rationale: The constitution's NN-2 Amendment 1.2.0 carve-out grants a mechanism (any region, when declared on the registry with proper approvals), not a pre-approved region list. Hard-coding `eastus` or `swedencentral` would be factually incorrect and misleading to auditors since those regions are not in the registry. The annotation "zero active non-AU entries" shows auditors the current operational state. FR-016 and the Foundry carve-out Assumption updated accordingly.*

- **Q5 — docs-arch CI job: within `ci.yml` vs new workflow file**: The Assumptions section said "new job added to the existing GitHub Actions workflow" without specifying `ci.yml` explicitly. Confirmed: the `docs-arch` job is a new job added to `.github/workflows/ci.yml` — not a new separate workflow file — running on the same triggers as the `quality` job with no path filtering. → **A**: New `docs-arch` job in `.github/workflows/ci.yml`. *Rationale: The stated Assumption is preserved; a separate workflow file would allow docs changes to bypass required PR checks and would diverge from the single-file CI convention established across all 37 shipped specs. Running without path filtering ensures spec cross-reference correctness is checked whenever any code change might affect architecture citations. Assumption updated to name `ci.yml` explicitly.*

### Session 2026-05-11 (Amendment 1)

- **Q1 — View-type subdirectory placement for Amendment 1 diagrams**: The amendment added 6 diagrams (RISK-01, OPS-03, SECTOR-05, BUILD-01, QUAL-01, EXP-01) but did not specify which view-type subdirectory each lives in under `docs/architecture/`. → **A**: RISK-01 → `operational/`; OPS-03 → `operational/`; SECTOR-05 → `data/`; BUILD-01 → `c4/`; QUAL-01 → new `quality/`; EXP-01 → `accessibility/`. *Rationale: View-type organisation principle (Assumptions Q2 Session 2026-05-11 + constitution §IV). RISK-01/OPS-03 are Operational-view diagrams consistent with OPS-01/OPS-02 already in `operational/`. SECTOR-05 ("cross-sector touch-points & partner data exchange") is a data-exchange flow diagram consistent with SECTOR-02/SECTOR-03/SECTOR-04 in `data/`. BUILD-01 is an AI/ML integrated component view that fits the C4 component layer in `c4/`; creating a `build/` subdirectory for a single diagram violates the "minimum viable directory surface" convention. QUAL-01 requires a new `quality/` subdirectory — test pyramid visualisations are QA-persona artefacts distinct from all existing view types; `quality/` already anticipated by "additional subdirectories as needed" phrasing in Assumptions. EXP-01 goes in `accessibility/` — per Session 2026-05-11 Q1, Technical-Experience = accessibility docs, WCAG coverage map, and end-user interaction patterns; `accessibility/` already holds wcag-coverage.md. Assumptions section updated to add `operational/` (retroactively named) and `quality/` (new) to the subdirectory list with explicit Amendment 1 placement mapping.*

- **Q2 — Additional CI gates for FR-024, FR-025, FR-026**: Do the three new Amendment 1 FRs require CI steps beyond the existing 6 `docs-arch` checks (markdownlint, spec-cross-ref, known-gaps-check, PNG/drawio pairing, hash-staleness, internal-link-check)? → **A**: No additional CI gates. All mechanically verifiable constraints on FR-024, FR-025, FR-026 are already covered by the existing `docs-arch` job: diagram-pair existence (FR-021a), PNG staleness via hash manifest (FR-021d), broken-link detection (FR-021b), spec citation presence (FR-021c/FR-011), known-gaps completeness (FR-023/SC-008), and markdownlint (FR-022). Content-level correctness — PPRR phase/agent alignment for OPS-03, test tier visual accuracy for QUAL-01, user-journey traceability for EXP-01 — is verified by human reviewers during PR review; these checks require semantic understanding of diagram content and cannot be reliably automated via Draw.io XML parsing without brittle, high-maintenance tooling. *Rationale: Constitution §Quality Gates does not mandate diagram-content parsing; adding a fragile XML-parse step would increase CI flakiness risk without proportionate auditability gain; the PR description for diagrams should explicitly reference the relevant spec section (e.g., constitution §PPRR Lifecycle for OPS-03, tests/README.md for QUAL-01) to satisfy the auditability requirement.*

- **Q3 — FR-025 QUAL-01 test pyramid tier alignment vs actual `tests/` structure**: FR-025 specified "four-tier test taxonomy (contract, integration, simulation, end-to-end)" but `tests/README.md` documents 13 test tiers; the canonical CI command (`pytest tests/unit tests/integration tests/contract`) explicitly includes `unit`; the constitution §Quality Gates mandates "unit tests and integration tests before merge"; `tests/unit/` is the largest tier (~159 files) and is entirely absent from the original FR-025 tier list. → **A**: FR-025 corrected to "five-tier test taxonomy (unit, contract, integration, simulation, end-to-end)." QUAL-01 MUST visualise unit as the base-of-pyramid tier with the highest relative volume (~159 files). Secondary tiers (benchmark, load, security, chaos) MAY be shown as supplementary lanes. *Rationale: Constitution v1.2.0 §Quality Gates explicitly requires "unit tests...before merge" — omitting `unit` from the test pyramid diagram contradicts the constitution and misrepresents the project's quality posture to auditors. `tests/unit/` is the single largest directory with 159 files; a test pyramid with its base as `contract` (118 files) would be topologically wrong. Canonical CI command confirmed in tests/README.md: unit + integration + contract. The "four-tier" claim also conflates two e2e variants (web Playwright in `apps/web/e2e/` and backend pytest in `tests/e2e/`) as one tier — collapsing them into one apex tier is acceptable for diagram clarity. FR-025 updated accordingly.*
