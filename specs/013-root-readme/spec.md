# Feature Specification: Root README.md

**Feature Branch**: `013-root-readme`  
**Created**: 2026-03-26  
**Status**: Draft  
**Input**: User description: "Create a comprehensive root README.md for the Autonomous Disaster Response Agent Coordination Hub that serves as the primary entry point for all stakeholders — developers, operators, government agencies, and evaluators."

## Clarifications

### Session 2026-04-12

- Q: In what order should the 10 content areas appear in the README to serve all four audiences within the 2-minute comprehension target (SC-001)? → A: Universal-first ordering: Overview → Agents → AIIMS Personas → Architecture Diagram → Quickstart → Repository Structure → Technology Stack → Success Metrics → Contributing → Documentation Links. Universal context first, then developer-specific, then reference material.
- Q: How should the README manage document length vs. the 2-minute overview comprehension target (SC-001) when covering 10+ content sections? → A: Table of Contents after the overview for navigation; collapsible `<details>` blocks for verbose sections (repository structure tree, full prerequisite installation guides). Keeps the document scannable for quick-scan readers while preserving detail.
- Q: Should the quickstart work entirely without Azure credentials (local dev mode)? → A: Yes; quickstart uses local-only mode with no Azure credentials required. A separate "Deploy to Azure" subsection links to infrastructure docs under `infra/`. Clear separation between "getting started" and "deployment to Azure."
- Q: What format should the high-level architecture diagram use (FR-002)? → A: Mermaid inline code block. GitHub renders Mermaid natively (desktop and mobile), it is version-controlled as text with meaningful diffs, and requires no external tooling. The README diagram is a simplified summary; the full diagram lives in architecture.md.
- Q: Should the documentation links section (FR-006) include additional existing artifacts beyond the four listed? → A: Yes; organize links by audience — evaluators see rubric, capstone, and executive-deck; developers see architecture and quickstart; operators see runbooks and walkthrough. All existing `docs/disaster-response-hub/` artifacts should be linked.

### Session 2026-04-12 (Pass 2)

- Q: What reading level should "plain language" (FR-015) target? → A: Flesch-Kincaid Grade Level 8 or below for the overview and quickstart sections, consistent with Australian Government Digital Service Standard plain language guidance.
- Q: What is the maximum README length and how should comprehensiveness be balanced? → A: Target under 500 lines of Markdown. Use collapsible `<details>` blocks (FR-017) for verbose sections. Scannable in under 3 minutes for a developer, under 2 minutes for an evaluator.
- Q: Which sections should use collapsible `<details>` blocks and which should remain expanded? → A: Collapsible: detailed monorepo structure (file tree), full prerequisites list, detailed agent descriptions. Non-collapsible: project overview, architecture diagram, quickstart commands, links to docs.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand the Project at a Glance (Priority: P1)

A new stakeholder — developer, government evaluator, or agency operator — visits the repository for the first time and reads the root README.md to understand what the project is, who it serves, why it exists, and how it is structured. Within two minutes of reading, they can determine whether the project is relevant to them and where to go next.

**Why this priority**: The README is the single most visited file in any repository. If it fails to orient a first-time reader, all downstream engagement (contributions, evaluations, partnerships) is lost. This is the foundational information architecture for the entire project.

**Independent Test**: Can be fully tested by giving the README to a person unfamiliar with the project and verifying they can correctly answer: "What does this system do?", "Who is it for?", "How is it built?", and "Where do I go next?" within two minutes.

**Acceptance Scenarios**:

1. **Given** a first-time visitor opens the repository, **When** they read the README project overview section, **Then** they can describe in their own words that this is a multi-agent disaster response coordination system for Australian emergency management.
2. **Given** an evaluator reviewing the project for the Azure Master Architect program, **When** they read the README, **Then** they find direct links to the architecture documentation, evaluation rubric, constitution, and feature specifications.
3. **Given** a government agency representative, **When** they read the README, **Then** they understand that the system supports AIIMS incident management roles and that human incident commanders retain final authority over all safety-critical decisions.

---

### User Story 2 - Set Up a Local Development Environment (Priority: P1)

A developer wants to contribute to the project. They read the README quickstart section and follow the instructions to clone the repository, install prerequisites, and run the system locally. They can start all three runtimes and verify the system is operational.

**Why this priority**: Without a working quickstart, no developer can contribute. This is equally critical as the project overview because it gates all development activity.

**Independent Test**: Can be fully tested by following the quickstart instructions on a clean machine with only the listed prerequisites installed. Success is measured by the developer running all three runtimes locally and seeing a working response from each.

**Acceptance Scenarios**:

1. **Given** a developer with the listed prerequisites installed, **When** they follow the quickstart instructions step by step, **Then** they can start the API, agent, and web runtimes locally without errors.
2. **Given** a developer has completed the quickstart, **When** they run the local test and lint commands documented in the README, **Then** all checks pass on a fresh clone of the default branch.
3. **Given** a developer is missing a prerequisite, **When** they read the prerequisites section, **Then** they find specific version requirements and installation guidance for each tool.

---

### User Story 3 - Navigate the Monorepo Structure (Priority: P2)

A developer or architect needs to find the right file, module, or documentation for a specific concern. They consult the README's repository structure section to understand the monorepo layout and locate the relevant directory.

**Why this priority**: Monorepos are notoriously difficult to navigate without a map. This section reduces onboarding friction and prevents developers from working in the wrong location.

**Independent Test**: Can be fully tested by asking a developer unfamiliar with the codebase to locate the evacuation agent code, the Bicep infrastructure templates, and the shared domain models using only the README's structure guide.

**Acceptance Scenarios**:

1. **Given** a developer looking for a specific agent's code, **When** they read the repository structure section, **Then** they can identify that agent code lives under `apps/agents/` with individual agent subdirectories.
2. **Given** an infrastructure engineer, **When** they consult the repository structure section, **Then** they can locate the Bicep templates under `infra/` and understand the deployment target.
3. **Given** a front-end developer, **When** they read the structure section, **Then** they can identify `apps/web/` as the Next.js application and `packages/ui/` as the shared design system.

---

### User Story 4 - Understand AIIMS Role Mapping and Human Authority (Priority: P2)

An incident commander, agency operator, or safety evaluator reads the README to understand how the system maps to Australian Interagency Incident Management System (AIIMS) roles and where human authority boundaries exist.

**Why this priority**: The constitution mandates that the platform aligns with AIIMS and that operational authority remains with designated incident management roles. The README must make this governance model immediately visible to build trust with emergency management stakeholders.

**Independent Test**: Can be fully tested by having an emergency management professional read the personas section and correctly identify which AIIMS roles map to which system capabilities, and confirm that the incident commander's final authority is explicitly stated.

**Acceptance Scenarios**:

1. **Given** an incident commander reading the README, **When** they review the personas section, **Then** they see that the IC role retains final decision authority over all safety-critical system outputs including evacuations, alerts, and resource dispatch.
2. **Given** a government evaluator, **When** they review the personas section, **Then** they find a clear mapping between AIIMS functional roles and the system's agent-assisted capabilities.
3. **Given** a safety auditor, **When** they review the README, **Then** they find a link to the project constitution that governs life-safety principles and human override requirements.

---

### User Story 5 - Evaluate Project Success Criteria and Maturity (Priority: P3)

An evaluator, sponsor, or senior stakeholder reads the README to understand the measurable goals the project aims to achieve, what technology underpins it, and where it is deployed.

**Why this priority**: Evaluators and sponsors need to quickly assess project ambition, feasibility, and alignment with program objectives. The success metrics and technology overview provide this context without requiring a deep dive into documentation.

**Independent Test**: Can be fully tested by having an evaluator locate the success metrics, technology stack, and deployment target within 60 seconds of opening the README.

**Acceptance Scenarios**:

1. **Given** a program evaluator, **When** they read the success metrics section, **Then** they find the capstone targets: 1,000+ lives saved annually, 50% response time reduction, 24-hour earlier evacuations, 30% resource efficiency improvement, and 30% economic loss reduction.
2. **Given** a technical reviewer, **When** they read the technology stack section, **Then** they can identify the three runtimes (FastAPI, Python agents, Next.js), the Azure deployment target (Azure regions within Australia, primary: Australia East), and the key Azure services used.
3. **Given** a contributor looking for context, **When** they read the README, **Then** they find links to the CI/CD pipeline configuration and instructions for running tests and linting locally.

---

### User Story 6 - Contribute to the Project (Priority: P3)

A developer wants to contribute code, documentation, or infrastructure changes. They read the contribution guidelines in the README to understand the development workflow, branching strategy, and quality expectations.

**Why this priority**: Contribution guidelines reduce friction for new contributors and ensure consistency across the codebase. Without them, contributions are inconsistent or discouraged entirely.

**Independent Test**: Can be fully tested by having a new contributor read the contribution section and successfully create a branch, make a change, run local quality checks, and understand the pull request process.

**Acceptance Scenarios**:

1. **Given** a new contributor, **When** they read the contribution guidelines, **Then** they understand the branching convention, commit expectations, and pull request workflow.
2. **Given** a contributor ready to submit changes, **When** they follow the documented local quality checks, **Then** they can run linting and tests for the relevant runtime before pushing.
3. **Given** a contributor looking at CI/CD, **When** they read the README, **Then** they find a reference to the CI pipeline configuration and understand what automated checks run on pull requests.

---

### Edge Cases

- What happens when a stakeholder has no technical background? The project overview and personas sections must be written in plain, non-technical language accessible to government and emergency management professionals (Flesch-Kincaid Grade Level 8 or below).
- What happens when the README is read on GitHub mobile? The document must render correctly in standard GitHub-flavoured Markdown without reliance on advanced rendering features. Collapsible `<details>` blocks must expand/collapse correctly on mobile; content inside must be valid Markdown when expanded.
- What happens when sections of the codebase referenced in the structure guide do not yet exist? The README must document the intended structure and note any sections that are planned but not yet implemented.
- What happens when prerequisite versions change? The prerequisites section must specify minimum versions and link to installation sources so that readers can verify compatibility.
- What happens when a collapsible `<details>` block contains a Mermaid diagram or code fence? Nested code fences inside `<details>` blocks must use correct GitHub-flavoured Markdown escaping. The architecture diagram MUST NOT be placed inside a collapsible block.
- What happens when the README is used by someone searching for human override guarantees? The project overview or personas section must contain a direct, standalone statement that the Incident Commander retains final authority over all safety-critical outputs, satisfying Constitution I (Life Safety First) at first-read depth.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The README MUST include a project overview section that explains the Autonomous Disaster Response Agent Coordination Hub as a multi-agent system for Australian emergency management coordination.
- **FR-002**: The README MUST include a high-level architecture diagram as an inline Mermaid code block showing the three-runtime structure (API/FastAPI, Agents/Python, Web/Next.js) and their relationships to Azure services. The Mermaid diagram MUST be a simplified summary; the full architecture detail lives in `docs/disaster-response-hub/architecture.md`.
- **FR-003**: The README MUST include a quickstart section with step-by-step instructions for cloning the repository, installing prerequisites, and running all three runtimes locally without requiring Azure credentials. A separate "Deploy to Azure" subsection MUST link to infrastructure documentation under `infra/` for cloud deployment.
- **FR-004**: The README MUST include a prerequisites section listing required tools with specific minimum version numbers (Python, Node.js, pnpm, uv, Docker, Azure CLI).
- **FR-005**: The README MUST include a personas section that maps AIIMS incident management roles to system capabilities, explicitly stating that the incident commander retains final authority over all safety-critical outputs.
- **FR-006**: The README MUST include a documentation links section organized by audience, referencing all major existing project artifacts: **For evaluators** — evaluation rubric (`AMA_Rubric_Asia.md`), capstone (`capstone.md`), executive deck (`docs/disaster-response-hub/demo/executive-deck.md`); **For developers** — architecture documentation (`docs/disaster-response-hub/architecture.md`), feature specifications (`specs/`), project constitution (`.specify/memory/constitution.md`); **For operators** — operator runbooks (`docs/disaster-response-hub/operator-runbooks.md`), demo walkthrough (`docs/disaster-response-hub/demo/walkthrough.md`).
- **FR-007**: The README MUST include a success metrics section listing the capstone targets: 1,000+ lives saved annually, 50% response time reduction, 24-hour earlier evacuations, 30% resource efficiency improvement, and 30% economic loss reduction.
- **FR-008**: The README MUST include a technology stack section listing the core technologies, Azure services, and the deployment target. The deployment region MUST state "Azure regions within Australia" (per Constitution VI), with Australia East as the primary region.
- **FR-009**: The README MUST include a repository structure section documenting the monorepo layout: `apps/` (api, agents, web, ingestion), `packages/` (domain, schemas, ui), `infra/`, `specs/`, `tests/`, `docs/`, and `scripts/`.
- **FR-010**: The README MUST include a contribution guidelines section documenting the development workflow, branching conventions, and local quality check commands.
- **FR-011**: The README MUST include a section referencing the CI/CD pipeline (`.github/workflows/ci.yml`) and documenting how to run tests and linting locally for each runtime.
- **FR-012**: The README MUST be written in GitHub-flavoured Markdown and render correctly on GitHub's web interface, including on mobile devices.
- **FR-013**: The README MUST link to the constitution (`.specify/memory/constitution.md`) and MUST contain a standalone, visible statement that the Incident Commander retains final human authority over all safety-critical outputs (evacuations, alerts, resource dispatch), satisfying Constitution I (Life Safety First). This statement MUST NOT be buried inside a collapsible block.
- **FR-014**: The README MUST describe the five specialised agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication) and their roles in the coordination system. The README MUST use the term "agent" (not "service") for these five AI components, and the term "runtime" for the three execution environments (API, Agents, Web).
- **FR-015**: The README MUST be accessible to non-technical stakeholders; the project overview, quickstart, and personas sections MUST use plain language at Flesch-Kincaid Grade Level 8 or below, consistent with Australian Government Digital Service Standard plain language guidance (per CHK016: union of FR-015 and NFR-003 scope). These sections MUST NOT require software engineering knowledge.
- **FR-016**: The README MUST present content areas in universal-first order: Project Overview → Agents → AIIMS Personas & Human Authority → Architecture Diagram → Quickstart → Repository Structure → Technology Stack → Success Metrics → Contributing → Documentation Links. Universal context sections appear before developer-specific sections to serve all four audiences within the 2-minute comprehension target.
- **FR-017**: The README MUST include a Table of Contents after the H1 title and one-sentence description for navigation. The following sections MUST use collapsible `<details>` blocks: detailed monorepo structure (file tree), full prerequisites list, and detailed agent descriptions. The following sections MUST remain non-collapsible (always visible): project overview, architecture diagram, quickstart commands, and documentation links.

### Key Entities

- **README Sections**: Discrete content blocks (overview, architecture, quickstart, personas, documentation links, success metrics, technology stack, repository structure, contribution guidelines, CI/CD) that together form the complete document.
- **Stakeholder Personas**: The four primary audiences (developers, operators, government agencies, evaluators) whose information needs the README must satisfy.
- **AIIMS Role Mapping**: The correspondence between Australian Interagency Incident Management System functional roles and the system's agent-assisted capabilities.

### Terminology

- **Agent**: One of the five specialised AI components (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication). Do NOT use "service" to refer to these components.
- **Runtime**: One of the three execution environments (API/FastAPI, Agents/Python, Web/Next.js). The architecture documentation may use "API Service" for the FastAPI component; the README MUST use "API runtime" for consistency.
- **Incident Commander (IC)**: The AIIMS role that retains final human authority over all safety-critical decisions. Do NOT abbreviate on first use.

### Non-Functional Requirements

- **NFR-001**: The README MUST NOT exceed 500 lines of Markdown source (excluding blank lines within collapsible `<details>` blocks that are collapsed by default).
- **NFR-002**: The README MUST be scannable in under 3 minutes for a developer audience and under 2 minutes for an evaluator audience, achieved through the Table of Contents, collapsible sections, and universal-first content ordering.
- **NFR-003**: The project overview, quickstart, and personas sections MUST score Flesch-Kincaid Grade Level 8 or below when validated with a readability analysis tool (per CHK016: union scope aligned with FR-015).
- **NFR-004**: All collapsible `<details>` blocks MUST include a meaningful `<summary>` label and MUST render correctly on GitHub desktop and mobile. Content inside collapsible blocks MUST be valid GitHub-flavoured Markdown when expanded.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time reader with no prior project knowledge can correctly describe the system's purpose, audience, and structure after reading the README for no more than two minutes (evaluator) or three minutes (developer seeking setup context).
- **SC-002**: A developer can complete local development setup by following the quickstart instructions in under 15 minutes on a machine with prerequisites already installed.
- **SC-003**: An evaluator can locate all five key documentation links (architecture, constitution, specs, rubric, capstone) within 30 seconds of opening the README.
- **SC-004**: A government stakeholder can identify the AIIMS role mapping and confirm human authority over safety-critical decisions within 60 seconds of reading the personas section. The Incident Commander's final authority MUST be stated in a standalone sentence, not buried in a list.
- **SC-005**: The README contains all 10 content areas specified in the feature description: project overview, architecture diagram, quickstart, AIIMS role mapping, documentation links, success metrics, technology stack, monorepo structure, contribution guidelines, and CI/CD reference.
- **SC-006**: The README renders correctly in GitHub-flavoured Markdown with no broken links, no rendering artefacts, and readable formatting on both desktop and mobile GitHub views. All collapsible `<details>` blocks expand and collapse correctly.
- **SC-007**: All internal links in the README resolve to existing files or directories in the repository at the time of merge.
- **SC-008**: The README source does not exceed 500 lines of Markdown (measured by `wc -l README.md` or equivalent).
- **SC-009**: The project overview and quickstart sections score Flesch-Kincaid Grade Level 8 or below when analysed with a readability tool (e.g., `textstat` Python library, Hemingway Editor, or equivalent).
- **SC-010**: The README uses the term "agent" (not "service") for all references to the five AI components, and "runtime" for all references to the three execution environments. No terminology inconsistencies exist.

## Assumptions

- The project already has the monorepo structure in place (`apps/`, `packages/`, `infra/`, `specs/`, `tests/`, `docs/`, `scripts/`) and these directories will exist at the time the README is merged.
- The CI pipeline is defined in `.github/workflows/ci.yml` and will remain at that path.
- The architecture documentation at `docs/disaster-response-hub/architecture.md` is the authoritative source for technical architecture details; the README provides a summary and links to it.
- The constitution at `.specify/memory/constitution.md` is the authoritative source for governance principles; the README references but does not duplicate it.
- Prerequisites include Python 3.12+, Node.js 22+, pnpm 10.6+, uv (Python package manager), and Docker, based on the existing `pyproject.toml` and `package.json` configurations.
- The evaluation rubric at `AMA_Rubric_Asia.md` is the current rubric and will remain at the repository root.
- The AIIMS framework is the applicable Australian incident management standard for this project, as specified in the constitution.
- The five agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication) represent the current agent roster as defined in the capstone and architecture documentation.
- Azure CLI is required for deployment to Azure but is NOT required for the local development quickstart. The quickstart MUST work with only Python, Node.js, pnpm, uv, and Docker installed.

## Dependencies

- **Architecture documentation** (`docs/disaster-response-hub/architecture.md`): Must be current and accurate for the README architecture summary to reference.
- **Constitution** (`.specify/memory/constitution.md`): Must be ratified for the README to reference life-safety and governance principles.
- **CI pipeline** (`.github/workflows/ci.yml`): Must exist for the README to document CI/CD references and local equivalents.
- **Evaluation rubric** (`AMA_Rubric_Asia.md`): Must be present at the repository root for the documentation links section.

## Out of Scope

- This spec is delivery-hygiene / enabling infrastructure; capstone-outcome-critical-path ownership lives in specs all capstone-critical-path specs (001, 005, 006, 008, 009, 010, 011, 012, 014, 015, 018, 019, 020, 021, 022, 023).

- Detailed API documentation or endpoint references (covered by architecture docs and OpenAPI specs).
- Deployment runbooks or production operations guides (covered by `docs/disaster-response-hub/operator-runbooks.md`).
- Detailed agent behaviour descriptions or agent interaction protocols (covered by individual feature specs under `specs/`).
- Azure resource provisioning instructions (covered by infrastructure documentation under `infra/`).
- Automated README generation or synchronisation tooling.
- Badges or status indicators (can be added as a follow-up enhancement).


## Personas

Authored against the `specs/027-spec-hardening/contracts/persona-profile.md` schema. AU-v1 personas are validated; PH / JP / BD entries are explicit placeholders pending capstone-reinterpretation (D-009) and SME validation per FR-023.

- **PER-031**: cross-ref to `specs/001-disaster-response-hub/spec.md` AIIMS personas (Incident Commander / Planning Officer / Operations Officer / Logistics Officer / Public Information Officer) per `specs/027-spec-hardening/contracts/persona-profile.md`. `status:` validated. `preconditions:` none.
- **PER-032**: cross-ref to `specs/004-actor-github-agents/spec.md` actor catalogue covering all `.github/agents/technical/*.agent.md` actors. `status:` validated. `preconditions:` none.
- **PER-033** [non-AU placeholder]: capstone-country operator personas for PH (NDRRMC), JP (Cabinet Office DRR / FDMA), BD (DDM / CPP volunteers). `status:` placeholder. `preconditions:` capstone-reinterpretation decision per D-009; SME validation via `ama-rubric-grader`-vetted SME interviews.

## Hypotheses

Hypotheses use the FR-018 statement format (`If <condition> then <observable>`) and link to a structured evidence stub conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. Capstone-country hypotheses for this spec's agent ownership (where applicable) are allocated in feature 028 / US2.

- **HYP-011**: If the actors named in `specs/004-actor-github-agents/spec.md` consult on every change to this spec via the `agent` tool, then the AMA rubric criterion mean (Assumptions / Requirements / Personas / Hypotheses / Scope) for this spec rises by at least +1 band relative to the baseline captured in `specs/028-capstone-alignment/evidence/rubric-baseline.md`. **Falsification**: post-feature rubric snapshot shows a regression in any of those five criteria for this spec. **Evidence stub**: `specs/028-capstone-alignment/evidence/HYP-HYP-011.md` (created in feature 028 polish).

