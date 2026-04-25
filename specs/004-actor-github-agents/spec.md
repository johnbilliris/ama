# Feature Specification: Actor-Specific GitHub Agents for Disaster Response Hub

**Feature Branch**: `004-actor-github-agents`  
**Created**: 2026-03-23  
**Status**: Draft  
**Input**: User description: "The autonomous disaster response co-ordination hub solution has a range of stakeholders and users across Commonwealth, state, territory, local government, utility, health, transport, community, and volunteer sectors. Furthermore, it has a range of technical personas ranging from solution architects, developers, infrastructure et al. We need to identify all these 'actors' and create custom GitHub agents for each and every one."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Use a domain-specific agent to accelerate role-aligned development (Priority: P1)

A developer working on a feature that affects a specific operational persona (e.g., incident commander, logistics officer, public information officer) invokes the corresponding GitHub agent in VS Code. The agent understands that persona's responsibilities, decision rights, information needs, vocabulary, and workflows within the Australian disaster response context. It provides contextually relevant guidance, code suggestions, and validation that aligns with the persona's operational reality and the AIIMS framework.

**Why this priority**: Operational persona agents directly improve the accuracy and speed of building the hub's core persona-specific workspaces, coordination workflows, and decision-support features. Without role-aware guidance, developers risk building generic interfaces that do not match real-world operational needs.

**Independent Test**: Can be fully tested by invoking a single operational persona agent (e.g., Incident Commander agent), asking it role-specific questions about coordination authority, AIIMS command structure, and multi-agency decision workflows, and verifying the responses are accurate, contextually grounded, and reference the correct frameworks and responsibilities.

**Acceptance Scenarios**:

1. **Given** a developer is building features for a specific operational persona, **When** they invoke that persona's GitHub agent, **Then** the agent responds with guidance grounded in that persona's responsibilities, decision rights, applicable frameworks, and inter-agency dependencies as defined in the hub's data model and the AIIMS framework.
2. **Given** a developer asks an operational persona agent about an action outside that persona's authority or scope, **When** the agent processes the request, **Then** it identifies the boundary, names the responsible persona or organisation, and explains the correct escalation or handoff pathway.
3. **Given** multiple persona agents exist, **When** a developer switches between agents during the same session, **Then** each agent maintains its distinct role perspective and does not bleed context from another persona's domain.

---

### User Story 2 - Use an organisation-sector agent to understand jurisdictional and sectoral context (Priority: P2)

A developer or analyst working on features for a specific sector (e.g., health, utilities, local government) invokes the corresponding sector agent. The agent understands how organisations in that sector participate in disaster response across Australian jurisdictions, their statutory obligations, coordination relationships with other sectors, and the frameworks that govern their operations. It helps the developer build features that correctly reflect real-world inter-agency dynamics.

**Why this priority**: Sector agents ensure the hub accurately represents how different types of organisations operate individually and collectively. Incorrect modelling of sectoral responsibilities, jurisdictional differences, or inter-agency coordination leads to features that misrepresent real-world operations.

**Independent Test**: Can be tested by invoking a sector agent (e.g., Health Sector agent), asking about the sector's disaster response role across different jurisdictions, and verifying that the agent accurately describes organisational responsibilities, coordination pathways, statutory obligations, and differences between states and territories.

**Acceptance Scenarios**:

1. **Given** a developer is working on features involving a specific sector, **When** they invoke that sector's agent, **Then** the agent provides accurate guidance about the sector's disaster response role, participating organisations, coordination obligations, and jurisdictional variations across Australian states and territories.
2. **Given** a sector agent is asked about inter-agency coordination, **When** the request involves dependencies with other sectors, **Then** the agent identifies the relevant counterpart sectors, describes the coordination mechanism, and references applicable frameworks.
3. **Given** a sector has different organisational structures or obligations across jurisdictions, **When** the developer asks about a specific state or territory, **Then** the agent explains the jurisdictional differences and their operational implications.

---

### User Story 3 - Use a technical persona agent for architecture-aligned development (Priority: P3)

A technical contributor (solution architect, developer, infrastructure engineer, data engineer, security engineer, QA engineer, UX designer, or product owner) invokes their technical persona agent to receive guidance aligned with the project's architecture, conventions, quality gates, and technology stack. The agent understands the project's constitution, non-functional requirements, Azure-specific constraints, and the contributor's area of expertise.

**Why this priority**: Technical persona agents reduce onboarding friction and enforce project conventions consistently. They are valuable but depend on the operational and sector agents being defined first to provide the domain context that technical agents reference.

**Independent Test**: Can be tested by invoking a technical persona agent (e.g., Solution Architect agent), asking about design decisions, technology constraints, or non-functional requirements, and verifying that the agent's guidance aligns with the project constitution, Azure AU-region constraints, and established architectural patterns.

**Acceptance Scenarios**:

1. **Given** a technical contributor needs guidance on a design or implementation decision, **When** they invoke their technical persona agent, **Then** the agent provides advice consistent with the project's constitution, non-functional requirements, established patterns, and Azure-specific constraints.
2. **Given** a technical contributor asks about cross-cutting concerns (security, performance, accessibility), **When** the agent processes the request, **Then** it references the relevant constitutional principles, quality gates, and project conventions.
3. **Given** a new contributor onboards to the project, **When** they invoke their technical persona agent, **Then** the agent can explain the project structure, key conventions, testing requirements, and deployment patterns relevant to that contributor's role.

---

### User Story 4 - Maintain and evolve the agent catalogue as the hub grows (Priority: P4)

A project lead or senior developer updates the agent catalogue when new organisations, personas, or technical roles are added to the hub. They can verify that all agents remain consistent with the current data model, constitution, and operational frameworks. The agent catalogue serves as a living reference of all actors in the system.

**Why this priority**: The agent catalogue must stay current as the hub evolves. Stale or inconsistent agents erode trust and provide incorrect guidance. This story depends on the initial catalogue being established first.

**Independent Test**: Can be tested by adding a new organisation or persona to the hub's data model, then verifying that a corresponding agent can be created following the established conventions, and that the agent catalogue accurately reflects the current state of all actors.

**Acceptance Scenarios**:

1. **Given** a new organisation or persona is added to the hub's data model, **When** the project lead follows the agent creation conventions, **Then** a new agent definition can be created that is consistent with the existing catalogue structure and conventions.
2. **Given** the hub's data model or constitution is updated, **When** the project lead reviews the agent catalogue, **Then** any affected agents are identifiable and can be updated to reflect the changes.

### Edge Cases

- A persona exists in the data model but has no clearly differentiated responsibilities from another persona (e.g., planner vs. planning officer), requiring the agents to have distinct but complementary scopes.
- An organisation participates in disaster response only under specific conditions (e.g., Defence involvement only during declared national emergencies), and the agent must accurately represent these participation boundaries.
- A developer invokes an agent for a persona or sector they do not have deep knowledge of, and the agent must provide self-contained, accurate context without requiring prior domain expertise.
- A jurisdiction introduces a new framework or restructures its emergency management arrangements, requiring updates to multiple sector and persona agents simultaneously.
- Two agents provide conflicting guidance because their source frameworks have overlapping but inconsistent coordination rules across jurisdictions.

## Requirements *(mandatory)*

### Functional Requirements

#### Actor Identification

- **FR-001**: The project MUST maintain a comprehensive, documented catalogue of all actors in the disaster response hub, organised into three tiers: operational personas, organisation sectors, and technical personas.
- **FR-002**: The operational persona catalogue MUST include the following roles derived from the AIIMS framework and the hub's data model: Incident Commander, Operations Officer, Planning Officer, Logistics Officer, Public Information Officer, Field Coordinator, Resilience Planner, Executive/Senior Leader, and Observer/Auditor.
- **FR-003**: The organisation sector catalogue MUST include the following sectors: Commonwealth Government, State Government, Territory Government, Local Government, Fire Services, Police, Ambulance/Paramedic, State Emergency Service (SES), Meteorology (Bureau of Meteorology), Health, Utility, Transport, Community (NGOs and non-government organisations), and Volunteer organisations.
- **FR-004**: The technical persona catalogue MUST include the following roles: Solution Architect, Software Developer, Infrastructure/DevOps Engineer, Data Engineer, Security Engineer, QA/Test Engineer, UX Designer, Product Owner/Business Analyst, Azure Principal Architect, API Architect, Principal Software Engineer, and SRE Engineer.

#### Agent Definition

- **FR-005**: Each identified actor MUST have a corresponding GitHub agent definition file that follows the project's established agent file conventions, including YAML frontmatter with description, and structured instruction content.
- **FR-006**: Each operational persona agent MUST encode that persona's responsibilities, decision rights, information needs, escalation pathways, and applicable AIIMS command functions as defined in the hub's data model and operating frameworks.
- **FR-007**: Each organisation sector agent MUST encode the sector's disaster response role, typical participating organisations, statutory obligations, coordination relationships with other sectors, and jurisdictional variations across Australian states and territories.
- **FR-008**: Each technical persona agent MUST encode the project's constitution, relevant non-functional requirements, technology stack constraints (Azure AU-region, cloud-native), architectural patterns, and the conventions and quality gates applicable to that technical role.
- **FR-009**: Each agent definition MUST include contextual references to relevant project artefacts such as the data model, constitution, operating frameworks, and spec documents so the agent can ground its responses in authoritative project sources. Tier-specific mandatory references are defined in `contracts/agent-file-contract.md`.
- **FR-010**: Agent definitions MUST NOT contain hard-coded incident data, user credentials, API keys, or any sensitive operational information.

#### Agent Organisation

- **FR-011**: Agents MUST be organised under `.github/agents/` in tier subdirectories — `operational/`, `sectors/`, and `technical/` — keeping existing speckit workflow agents in the `.github/agents/` root.
- **FR-012**: The agent catalogue MUST include a registry or index document that lists all agents, their tier (operational, sector, technical), a brief description, and the file path to each agent definition.
- **FR-013**: Each agent MUST declare handoff relationships where applicable, identifying which other agents a user should consult for questions outside the current agent's scope.

#### Agent Consistency

- **FR-014**: All agents MUST be consistent with the hub's current data model, constitution, and AIIMS framework alignment.
- **FR-015**: Agents whose scope overlaps (e.g., a Health sector agent and a Logistics persona agent discussing medical supply coordination) MUST provide complementary rather than contradictory guidance, with clear delineation of which agent owns which aspect.

### Key Entities

- **Actor**: A person, role, or organisational representative that interacts with or contributes to the disaster response hub; classified into operational personas, organisation sectors, or technical personas.
- **Agent Definition**: A GitHub agent configuration file (`.agent.md`) that encodes an actor's domain knowledge, responsibilities, scope boundaries, handoff relationships, and references to authoritative project artefacts.
- **Agent Catalogue**: The complete registry of all agent definitions, organised by tier, with metadata describing each agent's purpose, scope, and relationships to other agents.
- **Agent Tier**: A classification level for agents — operational (AIIMS-aligned roles), sector (organisation types), or technical (project contributor roles).
- **Handoff Relationship**: A declared link between two agents indicating that questions outside one agent's scope should be directed to another specific agent.

### Assumptions

- GitHub Copilot agent definitions (`.agent.md` files) are the delivery format, consistent with the project's existing agent infrastructure in `.github/agents/`.
- Every identified actor receives a dedicated standalone `.agent.md` file (35+ files total). Shared context (constitution, data model, AIIMS framework references) is referenced from each agent rather than duplicated inline, keeping agents maintainable while providing clear, unambiguous invocation per actor.
- Actor agents are organised under `.github/agents/` in tier subdirectories (`operational/`, `sectors/`, `technical/`), keeping existing speckit workflow agents in the `.github/agents/` root.
- The AIIMS framework and the hub's existing data model are the authoritative sources for operational persona definitions and responsibilities.
- Sector-specific knowledge will be sourced from publicly available Australian emergency management documentation and frameworks (e.g., COMDISPLAN, state emergency management acts, sector-specific guidelines).
- Technical persona agents will reference the project's constitution, existing specs, and documented architectural decisions as their primary knowledge sources.
- Agents are development-time tools used by contributors in VS Code; they are not runtime components of the deployed hub.
- The initial agent definitions represent a starting point; they will be refined as the project matures and real users provide feedback on accuracy and usefulness.

### Out of Scope

- Runtime AI agents or chatbots deployed within the hub application itself.
- Authentication, authorisation, or access control for agent invocation (VS Code Copilot handles this natively).
- Automated testing of agent response quality (may be addressed in a future feature).
- Training or fine-tuning of underlying language models.
- Agent definitions for international disaster response frameworks or non-Australian jurisdictions.

## Clarifications

### Session 2026-03-23

- Q: Should every actor get a dedicated standalone agent, or should some be grouped into shared/parameterised agents? → A: Every actor gets a dedicated standalone `.agent.md` file (31+ files after subsequent clarifications), with shared context referenced rather than duplicated.
- Q: Should Emergency Services be one combined sector agent or split into sub-sector agents? → A: Split into 4 sub-sector agents (Fire Services, Police, Ambulance/Paramedic, SES) because they have fundamentally different command structures, legislation, and coordination obligations. Sector count increases from 10 to 13.
- Q: Where should the new actor agents be placed in the directory structure? → A: Nested under `.github/agents/` with tier subdirectories: `operational/`, `sectors/`, `technical/`. Existing speckit workflow agents remain in `.github/agents/` root.
- Q: Should Meteorology/BoM be added as a sector agent? → A: Yes, add Meteorology/Bureau of Meteorology as a 14th sector agent. BoM has a unique role as the authoritative source of weather warnings and hazard intelligence with distinct coordination obligations to all other sectors. Sector count increases from 13 to 14.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A comprehensive actor catalogue is produced that identifies at least 35 distinct actors (9 operational personas + 14 organisation sectors + 12 technical personas) with documented responsibilities and scope boundaries.
- **SC-002**: Each identified actor has a corresponding GitHub agent definition file that passes structural validation against the project's agent file conventions (YAML frontmatter, description, structured content).
- **SC-003**: In a structured evaluation, at least 80% of role-specific questions posed to an operational persona agent receive responses that accurately reflect the persona's responsibilities, decision rights, and AIIMS-aligned command functions as verified against the hub's data model documentation.
- **SC-004**: In a structured evaluation, at least 80% of sector-specific questions posed to an organisation sector agent receive responses that accurately describe the sector's disaster response role and jurisdictional variations as verified against publicly available Australian emergency management documentation.
- **SC-005**: At least 85% of contributors onboarding to the project report that their technical persona agent helped them understand the project's conventions, architecture, and quality gates, measured via a post-onboarding survey.
- **SC-006**: The complete agent catalogue can be reviewed and a new agent created by a project contributor in under 30 minutes by following the documented conventions and registry.

## Assumptions

Scoped to this spec's domain (actor / GitHub agent catalogue and registry). Tagging follows `specs/027-spec-hardening` taxonomy: `[RISK]` (open externally-driven risk), `[DECISION]` (deliberate scoping decision), bare bullet (operating assumption).

- **ASM-004**: The AU-v1 deployment context defined in `specs/001-disaster-response-hub/spec.md` is the operational baseline for this spec; capstone-country variants (PH / JP / BD) are deferred. `linked_gaps:` `specs/shared/gap-id-register.md` A-GAP-001..003. `status:` Open.
- **ASM-005** [DECISION]: This spec's deliverables (actor / GitHub agent catalogue and registry) integrate with the actor catalogue (`specs/004-actor-github-agents/spec.md`); responsible technical agents - product-owner-ba - are consulted via the `agent` tool during authoring and review.
- **ASM-006**: Speckit conventions (FR/SC numbering, ASM/HYP/PER/SCP families) and the persona-profile YAML schema (`specs/027-spec-hardening/contracts/persona-profile.md`) are authoritative; this spec defers to those rather than redefining them.

## Personas

Authored against the `specs/027-spec-hardening/contracts/persona-profile.md` schema. AU-v1 personas are validated; PH / JP / BD entries are explicit placeholders pending capstone-reinterpretation (D-009) and SME validation per FR-023.

- **PER-004**: cross-ref to `specs/001-disaster-response-hub/spec.md` AIIMS personas (Incident Commander / Planning Officer / Operations Officer / Logistics Officer / Public Information Officer) per `specs/027-spec-hardening/contracts/persona-profile.md`. `status:` validated. `preconditions:` none.
- **PER-005**: cross-ref to `specs/004-actor-github-agents/spec.md` actor catalogue covering all `.github/agents/technical/*.agent.md` actors. `status:` validated. `preconditions:` none.
- **PER-006** [non-AU placeholder]: capstone-country operator personas for PH (NDRRMC), JP (Cabinet Office DRR / FDMA), BD (DDM / CPP volunteers). `status:` placeholder. `preconditions:` capstone-reinterpretation decision per D-009; SME validation via `ama-rubric-grader`-vetted SME interviews.

## Hypotheses

Hypotheses use the FR-018 statement format (`If <condition> then <observable>`) and link to a structured evidence stub conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. Capstone-country hypotheses for this spec's agent ownership (where applicable) are allocated in feature 028 / US2.

- **HYP-002**: If the actors named in `specs/004-actor-github-agents/spec.md` consult on every change to this spec via the `agent` tool, then the AMA rubric criterion mean (Assumptions / Requirements / Personas / Hypotheses / Scope) for this spec rises by at least +1 band relative to the baseline captured in `specs/028-capstone-alignment/evidence/rubric-baseline.md`. **Falsification**: post-feature rubric snapshot shows a regression in any of those five criteria for this spec. **Evidence stub**: `specs/028-capstone-alignment/evidence/HYP-HYP-002.md` (created in feature 028 polish).

## Out of Scope

- This spec is delivery-hygiene / enabling infrastructure; capstone-outcome-critical-path ownership lives in specs all capstone-critical-path specs (001, 005, 006, 008, 009, 010, 011, 012, 014, 015, 018, 019, 020, 021, 022, 023).

Items explicitly deferred from this spec; promotion to in-scope requires the named preconditions to clear. Cross-references to other specs use the canonical overlap phrasing (`authoritative for: <capability>` / `defers-to: <NNN> (<capability>)`).

- **SCP-005** [DEFERRED]: Capstone-country variants (PH typhoon, JP earthquake, BD flood) of this spec's capabilities are out of scope until: (i) capstone-reinterpretation decision per D-009; (ii) per-country regulatory + data-sharing preconditions documented in `specs/005-data-source-governance/spec.md` clear; (iii) responsible technical agents (product-owner-ba) sign off on country-specific calibration.
- **SCP-006**: Constitutional-level changes (NON-NEGOTIABLE #1..#5) are not modified by this spec; any tension is documented as `[RISK]` in Assumptions, never resolved here.
- **SCP-007**: Cross-spec authority disputes are arbitrated via `product-owner-ba` and the speckit governance flow; this spec does not unilaterally claim ownership of capabilities owned elsewhere. `defers-to:` 018 (recovery-phase indicators, triggers, phase-exit criteria); 008 (warning-tier authoring, multilingual delivery, misinformation defence) where applicable.
- **SCP-008** [META]: This spec is delivery-hygiene / enabling infrastructure; capstone-outcome-critical-path ownership lives in specs (canonical list — see the verbatim bullet inserted by feature 028 / US4 elsewhere in this section). (See `specs/028-capstone-alignment/contracts/meta-spec-flag.contract.md`; the verbatim canonical bullet is added in US4.)


