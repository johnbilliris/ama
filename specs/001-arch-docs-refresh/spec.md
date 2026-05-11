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
- **Diagram source vs PNG mismatch**: If a `.drawio` file is updated but the exported PNG is not regenerated, the CI job must detect the staleness (by comparing file modification timestamps or a hash manifest).
- **Existing sparse docs conflict**: The six pre-existing architecture documents (`c4/system.md`, `c4/container.md`, `sequence/monitoring-risk-comms.md`, `capacity-model.md`, `cosmos-partitioning.md`, `spec-035-middleware-and-offline.md`) must be either incorporated into the new structure with updated front-matter or explicitly superseded and linked from the new index — not silently orphaned.
- **Cross-reference gap where no page covers a spec**: When a spec has no natural home in any architecture view, a gap entry is created in the known-gaps registry with a follow-up task, rather than forcing a spurious mention.
- **Foundry carve-out accuracy**: The AU-residency diagram must accurately reflect which Azure OpenAI/Foundry model-hosting regions are non-AU; if this is unknown at spec time, it is flagged as a known gap with a follow-up task.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Documentation Structure

- **FR-001**: The documentation set MUST include a single top-level index at `docs/architecture/README.md` from which every architecture page is reachable within two navigation steps.
- **FR-002**: The index MUST organise pages by persona cluster: Operational (AIIMS roles), Sector (jurisdictions), Technical — Architecture, Technical — Build, Technical — Quality, Technical — Experience.
- **FR-003**: Every architecture page MUST open with a one-sentence purpose statement, list its target persona clusters, embed at least one diagram, and link to the spec(s) and/or ADRs that motivated it.
- **FR-004**: The documentation MUST be structured around the C4 model (System Context L1, Container L2, Component L3, optional Code L4) plus auxiliary views: data, security/trust, deployment, sequence, capacity, governance, accessibility.
- **FR-005**: Pre-existing architecture documents MUST be incorporated into the new structure (with updated front-matter linking to the index) or explicitly superseded with a redirect note — they MUST NOT be silently orphaned.

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

- **FR-016**: A dedicated AU-residency and data-classification page MUST show in one diagram: the AU data-residency boundary, the Foundry carve-out zone for non-AU model hosting, and the model-gateway redaction enforcement point.
- **FR-017**: An RBAC role/permission matrix MUST map every named AIIMS role to its platform permissions and cite the spec(s) that define those boundaries.
- **FR-018**: A trust-boundary diagram MUST label every boundary crossing with the authentication or authorisation mechanism applied.
- **FR-019**: An SLI/SLO model page MUST define the SLI, the SLO target, and the error-budget alert thresholds for each key service.
- **FR-020**: The audit-trail provenance flow diagram MUST show how every actuation is logged, who can review the log, and what evidence is captured for compliance reporting.

#### Documentation-as-Code Requirements

- **FR-021**: A CI job named `docs-arch` MUST verify: (a) every PNG under `docs/architecture/` has a sibling `.drawio` source; (b) zero broken internal links in all `.md` files under `docs/architecture/`; (c) every spec number 001–037 (excluding documented archived numbers) appears in at least one architecture page.
- **FR-022**: All architecture markdown MUST pass `markdownlint` with the project's existing ruleset without exceptions specific to this feature.
- **FR-023**: A known-gaps registry MUST be maintained listing any spec or architectural area where documentation is identified as missing or stale, with a brief description and a follow-up task reference.

### Key Entities

- **Architecture Page**: A markdown document under `docs/architecture/` with a purpose statement, persona audience, at least one embedded diagram, and citations to specs and/or ADRs.
- **Diagram Pair**: A `.drawio` source file and its PNG sibling export; treated as an atomic unit for CI validation.
- **Known-Gaps Registry**: A structured list of documentation gaps (missing coverage, stale content) with follow-up task references; lives at `docs/architecture/known-gaps.md`.
- **ADR (Architectural Decision Record)**: A short record capturing a significant architectural decision, its context, options considered, and the outcome; indexed from `docs/architecture/adr/README.md`.
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
- **SC-007**: The documentation set contains a minimum of 20 distinct diagram pairs (`.drawio` + PNG) spanning all four C4 levels, auxiliary views (data, security, deployment, sequence, capacity, governance, accessibility), and persona-specific views.
- **SC-008**: The known-gaps registry identifies any spec or architectural area not yet fully documented and assigns a follow-up task reference; the registry itself contains zero items with no follow-up reference.

---

## Assumptions

- The six pre-existing architecture documents are treated as inputs to be incorporated, not authoritative sources; they may contain stale information that this feature corrects.
- Spec numbers with duplicate directory entries (e.g., two `036-*` directories observed) will be treated as one shipped spec for cross-reference counting purposes; the duplication is noted in the known-gaps registry.
- The Foundry carve-out region list (which Azure OpenAI/Foundry regions are non-AU) will be drawn from the constitution v1.2.0 and the `infra/bicep` configuration; if the exact regions cannot be confirmed from these sources, a placeholder is used and a known-gap entry is created.
- Draw.io diagram generation may be assisted by the `drawio-mcp-diagramming` skill; all generated diagrams must be reviewed for accuracy before being committed.
- The `docs-arch` CI job is a new job added to the existing GitHub Actions workflow; it does not replace or modify existing CI jobs.
- Accessibility documentation (WCAG coverage map) scope is limited to documenting what is already implemented per existing specs; this feature does not introduce new accessibility requirements.
- The "Code" level (C4 L4) is optional and will only be produced where it adds material clarity beyond the Component level (C4 L3); the planning phase will determine which, if any, components warrant L4 diagrams.
