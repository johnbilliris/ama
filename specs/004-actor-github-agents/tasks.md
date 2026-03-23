# Tasks: Actor-Specific GitHub Agents for Disaster Response Hub

**Input**: Design documents from `/specs/004-actor-github-agents/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and registry scaffold

- [X] T001 Create tier subdirectories under `.github/agents/`: `operational/`, `sectors/`, `technical/`
- [X] T002 Create agent registry scaffold in `.github/agents/AGENTS.md` with tier section headers, column definitions, and empty tables per the registry entry contract in `specs/004-actor-github-agents/contracts/agent-file-contract.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create reference agents — one per tier — that establish the pattern all subsequent agents follow

**⚠️ CRITICAL**: All subsequent agents in Phases 3–5 must follow the structure established by these reference agents

- [X] T003 Create reference operational agent in `.github/agents/operational/incident-commander.agent.md` with YAML frontmatter (description, handoffs to operations-officer and planning-officer), and body sections: Role Overview (AIIMS Incident Controller function), Responsibilities & Decision Rights (from data model `incident_commander` roleType: overall coordination authority, multi-agency decision approval, public alert authorisation, escalation to executive), Scope Boundaries (not tactical operations — handoff to operations-officer; not logistics — handoff to logistics-officer), Key Relationships (all AIIMS functions, sector leads), Contextual References (constitution, data-model.md, spec.md), Guidance Notes (AIIMS command structure, span of control, multi-jurisdiction coordination)
- [X] T004 Create reference sector agent in `.github/agents/sectors/fire-services.agent.md` with YAML frontmatter (description, handoffs to police, ses, incident-commander), and body sections: Role Overview (fire response lead agency for bushfire), Responsibilities & Decision Rights (fire suppression, controlled burns, evacuation recommendations in fire zones), Scope Boundaries (not law enforcement — handoff to police; not flood/storm — handoff to ses), Key Relationships (police for evacuation enforcement, ambulance for casualties, meteorology-bom for weather intelligence), Contextual References (constitution, data-model.md, spec.md), Guidance Notes (jurisdictional variations: CFA/RFS/DFES/MFS across states, bushfire vs structural fire, Total Fire Ban authorities)
- [X] T005 Create reference technical agent in `.github/agents/technical/solution-architect.agent.md` with YAML frontmatter (description, handoffs to software-developer, infrastructure-devops, security-engineer), and body sections: Role Overview (system design and architectural governance), Responsibilities & Decision Rights (architecture decisions, NFR enforcement, technology selection within Azure AU constraints), Scope Boundaries (not code-level patterns — handoff to software-developer; not infrastructure provisioning — handoff to infrastructure-devops), Key Relationships (all technical personas, product-owner-ba for requirements), Contextual References (constitution, architecture.md, data-model.md, plan.md files), Guidance Notes (Azure AU-region constraint, AIIMS alignment, multi-agent coordination patterns, Cosmos DB for state, event-driven architecture)
- [X] T006 Register the three reference agents in `.github/agents/AGENTS.md` with agent name, file path, tier, description, and key handoffs columns populated

**Checkpoint**: Three reference agents exist, registry has entries, pattern is established for remaining agents

---

## Phase 3: User Story 1 — Operational Persona Agents (Priority: P1) 🎯 MVP

**Goal**: Create all 9 operational persona agents so developers building persona-specific features have AIIMS-aligned domain guidance

**Independent Test**: Invoke the Incident Commander agent, ask 5 role-specific questions about AIIMS authority, multi-agency coordination, and escalation pathways; verify at least 4/5 responses are accurate per SC-003

### Implementation for User Story 1

- [X] T007 [P] [US1] Create operations-officer agent in `.github/agents/operational/operations-officer.agent.md` — AIIMS Operations function, tactical coordination, field deployment, handoffs to incident-commander (escalation) and field-coordinator (ground ops)
- [X] T008 [P] [US1] Create planning-officer agent in `.github/agents/operational/planning-officer.agent.md` — AIIMS Planning function, situation assessment, resource forecasting, handoffs to incident-commander (strategic decisions) and logistics-officer (resource needs)
- [X] T009 [P] [US1] Create logistics-officer agent in `.github/agents/operational/logistics-officer.agent.md` — AIIMS Logistics function, supply chain, transport coordination, medical supplies, handoffs to planning-officer (demand forecasting) and health sector (medical logistics)
- [X] T010 [P] [US1] Create public-information-officer agent in `.github/agents/operational/public-information-officer.agent.md` — AIIMS Public Information function, media liaison, community alerts, multilingual obligations per Constitution V, handoffs to incident-commander (alert approval) and community-ngos (community channels)
- [X] T011 [P] [US1] Create field-coordinator agent in `.github/agents/operational/field-coordinator.agent.md` — field operations, ground-level coordination, connectivity-degraded scenarios, handoffs to operations-officer (tactical direction) and logistics-officer (supply requests)
- [X] T012 [P] [US1] Create resilience-planner agent in `.github/agents/operational/resilience-planner.agent.md` — preparedness analysis, scenario rehearsal, gap identification, framework modelling, handoffs to planning-officer (active incident planning) and executive-leader (policy decisions)
- [X] T013 [P] [US1] Create executive-leader agent in `.github/agents/operational/executive-leader.agent.md` — executive oversight, strategic decisions, policy escalation, inter-government liaison, handoffs to incident-commander (operational authority) and commonwealth-government (national coordination)
- [X] T014 [P] [US1] Create observer-auditor agent in `.github/agents/operational/observer-auditor.agent.md` — read-only participation, audit trail review, post-incident analysis, compliance verification, handoffs to resilience-planner (lessons learned) and planning-officer (timeline review)
- [X] T015 [US1] Update `.github/agents/AGENTS.md` registry with all 9 operational persona agents (incident-commander already registered in T006, add remaining 8)

**Checkpoint**: All 9 operational persona agents exist with AIIMS-aligned content, registered in catalogue, independently testable via structured questions

---

## Phase 4: User Story 2 — Organisation Sector Agents (Priority: P2)

**Goal**: Create all 14 organisation sector agents so developers building cross-agency features have accurate jurisdictional and sectoral context

**Independent Test**: Invoke the Health sector agent, ask 5 sector-specific questions about disaster response role, jurisdictional variations, and inter-agency coordination; verify at least 4/5 responses are accurate per SC-004

### Implementation for User Story 2

- [X] T016 [P] [US2] Create commonwealth-government agent in `.github/agents/sectors/commonwealth-government.agent.md` — COMDISPLAN, Emergency Management Australia, national coordination, Defence engagement conditions, handoffs to state-government (state-level ops) and meteorology-bom (national weather intelligence)
- [X] T017 [P] [US2] Create state-government agent in `.github/agents/sectors/state-government.agent.md` — state emergency management acts, state coordination centres, lead agency designation, handoffs to commonwealth-government (national escalation) and local-government (local coordination)
- [X] T018 [P] [US2] Create territory-government agent in `.github/agents/sectors/territory-government.agent.md` — territory emergency management ordinances, differences from state arrangements (ACT, NT), handoffs to commonwealth-government (Commonwealth support) and local-government (local service delivery)
- [X] T019 [P] [US2] Create local-government agent in `.github/agents/sectors/local-government.agent.md` — municipal emergency management plans, local coordination, community recovery, council responsibilities, handoffs to state-government (escalation) and community-ngos (community support)
- [X] T020 [P] [US2] Create police agent in `.github/agents/sectors/police.agent.md` — evacuation enforcement, traffic management, coronial engagement, search and rescue coordination, handoffs to fire-services (fire zones) and ses (flood/storm)
- [X] T021 [P] [US2] Create ambulance-paramedic agent in `.github/agents/sectors/ambulance-paramedic.agent.md` — patient triage, medical evacuation, mass casualty management, handoffs to health (hospital surge) and logistics-officer (medical supply)
- [X] T022 [P] [US2] Create ses agent in `.github/agents/sectors/ses.agent.md` — flood/storm lead agency, rescue operations, SES volunteer coordination, sandbagging, handoffs to police (evacuation support) and meteorology-bom (flood warnings)
- [X] T023 [P] [US2] Create meteorology-bom agent in `.github/agents/sectors/meteorology-bom.agent.md` — Bureau of Meteorology, authoritative weather warnings, Meteorology Act 1955, forecast products, severe weather thresholds, handoffs to fire-services (fire weather) and ses (flood watches)
- [X] T024 [P] [US2] Create health agent in `.github/agents/sectors/health.agent.md` — public health emergencies, hospital surge, environmental health, mental health response, handoffs to ambulance-paramedic (pre-hospital care) and logistics-officer (medical supply chain)
- [X] T025 [P] [US2] Create utility agent in `.github/agents/sectors/utility.agent.md` — energy, water, telecommunications, essential services restoration, handoffs to transport (infrastructure access) and local-government (community impact)
- [X] T026 [P] [US2] Create transport agent in `.github/agents/sectors/transport.agent.md` — road/rail closure authorities, evacuation transport, freight coordination, handoffs to police (traffic management) and logistics-officer (transport assets)
- [X] T027 [P] [US2] Create community-ngos agent in `.github/agents/sectors/community-ngos.agent.md` — Red Cross, Salvation Army, community recovery organisations, evacuation centre management, handoffs to local-government (local coordination) and volunteer (volunteer management)
- [X] T028 [P] [US2] Create volunteer agent in `.github/agents/sectors/volunteer.agent.md` — spontaneous volunteer management, volunteer protection legislation, credentialing, handoffs to ses (SES volunteers) and community-ngos (organised volunteering)
- [X] T029 [US2] Update `.github/agents/AGENTS.md` registry with all 14 sector agents (fire-services already registered in T006, add remaining 13)

**Checkpoint**: All 14 sector agents exist with jurisdictional context, registered in catalogue, independently testable via structured questions

---

## Phase 5: User Story 3 — Technical Persona Agents (Priority: P3)

**Goal**: Create all 8 technical persona agents so project contributors have architecture-aligned guidance for their role

**Independent Test**: Invoke the Software Developer agent, ask about code conventions, testing frameworks, and Azure constraints; verify responses align with the constitution and copilot-instructions.md

### Implementation for User Story 3

- [X] T030 [P] [US3] Create software-developer agent in `.github/agents/technical/software-developer.agent.md` — Python 3.12/TypeScript 5.6 conventions, FastAPI/Next.js patterns, ruff/eslint, PR workflow, handoffs to solution-architect (design decisions) and security-engineer (auth patterns)
- [X] T031 [P] [US3] Create infrastructure-devops agent in `.github/agents/technical/infrastructure-devops.agent.md` — Azure AU infra, Bicep templates, Container Apps, CI/CD pipelines, monitoring, handoffs to solution-architect (architecture) and security-engineer (RBAC/identity)
- [X] T032 [P] [US3] Create data-engineer agent in `.github/agents/technical/data-engineer.agent.md` — Cosmos DB, signal ingestion pipelines, Event Hubs/Service Bus, data model conventions, handoffs to solution-architect (data architecture) and security-engineer (data privacy)
- [X] T033 [P] [US3] Create security-engineer agent in `.github/agents/technical/security-engineer.agent.md` — Constitution IV compliance, tenant isolation, RBAC, content safety, privacy obligations, Australian data residency, handoffs to infrastructure-devops (infrastructure security) and software-developer (secure coding)
- [X] T034 [P] [US3] Create qa-test-engineer agent in `.github/agents/technical/qa-test-engineer.agent.md` — pytest, Playwright, contract/integration/simulation/e2e testing strategy, test file conventions, handoffs to software-developer (unit testing) and ux-designer (accessibility testing)
- [X] T035 [P] [US3] Create ux-designer agent in `.github/agents/technical/ux-designer.agent.md` — dashboard design for high-pressure ops, SC-007 rubric, accessibility per Constitution V, Tailwind CSS patterns, handoffs to software-developer (component implementation) and product-owner-ba (user research)
- [X] T036 [P] [US3] Create product-owner-ba agent in `.github/agents/technical/product-owner-ba.agent.md` — requirements methodology, acceptance criteria writing, success metrics, stakeholder management, speckit workflow, handoffs to solution-architect (feasibility) and ux-designer (UX requirements)
- [X] T037 [US3] Update `.github/agents/AGENTS.md` registry with all 8 technical persona agents (solution-architect already registered in T006, add remaining 7)

**Checkpoint**: All 8 technical persona agents exist with project-convention-aligned content, registered in catalogue, independently testable

---

## Phase 6: User Story 4 — Polish & Cross-Cutting Concerns

**Goal**: Ensure cross-agent consistency, validate handoff relationships, and finalize the catalogue for maintainability

**Independent Test**: Add a hypothetical new actor following documented conventions and verify it can be created in under 30 minutes per SC-006

- [X] T038 Validate all handoff relationships across the 31 agents — verify every `handoffs[].agent` reference in YAML frontmatter points to an existing agent file, verify every agent declares at least one handoff per FR-013, fix any broken or missing references
- [X] T039 Review scope boundary consistency across all cross-tier overlapping agents — verify every sector-to-operational and sector-to-sector boundary provides complementary (not contradictory) guidance per FR-015, including but not limited to: Health + Logistics (medical supplies), Fire Services + Police (evacuation enforcement), Meteorology + all sectors (weather intelligence), Ambulance + Health (pre-hospital vs hospital), SES + Police (flood evacuation), Commonwealth + State (national escalation), Community-NGOs + Volunteer (volunteer management)
- [X] T040 Verify all contextual reference file paths in every agent body point to files that exist in the repository — fix any broken paths
- [X] T041 Final review of `.github/agents/AGENTS.md` registry — confirm all 31 agents listed with correct file paths, tier assignments, descriptions, and key handoffs
- [X] T042 Verify no agent file contains hard-coded incident data, credentials, API keys, or PII per FR-010

**Checkpoint**: Complete catalogue of 31 agents, all validated, all registered, all cross-referenced — ready for contributor use

---

## Dependencies

```
T001 ──► T002 ──► T003, T004, T005 (parallel) ──► T006
                                                      │
         ┌────────────────────────────────────────────┘
         ▼
    T007–T014 (all parallel) ──► T015
    T016–T028 (all parallel) ──► T029
    T030–T036 (all parallel) ──► T037
                                   │
         ┌─────────────────────────┘
         ▼
    T038 ──► T039 ──► T040 ──► T041 ──► T042
```

## Parallel Execution Examples

**Within User Story 1 (Phase 3)**: T007–T014 can all run in parallel — each creates a separate `.agent.md` file with no dependencies on other agents being complete. T015 (registry update) must wait for all to finish.

**Within User Story 2 (Phase 4)**: T016–T028 can all run in parallel — same rationale. T029 waits for completion.

**Within User Story 3 (Phase 5)**: T030–T036 can all run in parallel. T037 waits for completion.

**Cross-story**: Phase 4 can begin before Phase 3 is fully complete (the reference agents from Phase 2 establish the pattern). However, Phase 6 validation requires all three story phases to be done.

## Implementation Strategy

**MVP**: Phase 1 + Phase 2 + Phase 3 (setup + reference agents + operational personas) = User Story 1 delivers 9 AIIMS-aligned agents immediately usable by developers building the hub's core persona features.

**Incremental delivery**:
1. MVP: 9 operational agents (highest life-safety impact alignment)
2. Increment 2: 14 sector agents (cross-agency coverage)
3. Increment 3: 8 technical agents (contributor onboarding)
4. Final: Cross-cutting validation and polish

**Total tasks**: 42
**Tasks per user story**: US1: 9 agents + registry = 10 tasks | US2: 13 agents + registry = 14 tasks | US3: 7 agents + registry = 8 tasks | US4: 5 validation tasks
**Parallel opportunities**: 28 of 42 tasks are parallelizable (marked [P])
