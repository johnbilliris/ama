# Tasks: Root README.md

**Input**: Design documents from `/specs/013-root-readme/` and `/specs/feature/013-root-readme/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅, checklists/comprehensive.md ✅

**Tests**: Not requested — this is a documentation-only feature. Validation tasks are included as quality gates.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Since all tasks target a single file (`README.md`), parallelism is limited — but content drafting for independent sections can proceed in parallel before assembly.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (independent content, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single deliverable**: `README.md` at repository root
- **Spec sources**: `specs/013-root-readme/spec.md`, `specs/feature/013-root-readme/plan.md`
- **Reference docs**: `docs/disaster-response-hub/architecture.md`, `.specify/memory/constitution.md`, `capstone.md`

---

## Phase 1: Setup (Document Skeleton)

**Purpose**: Create the README.md file with the FR-016 section ordering skeleton and Table of Contents

- [X] T001 Create README.md at repository root with H1 title "Autonomous Disaster Response Agent Coordination Hub" and one-sentence project description per FR-001 in README.md
- [X] T002 Add Table of Contents section with anchor links to all 10 content sections per FR-016 ordering (Overview → Agents → AIIMS Personas → Architecture → Quickstart → Repository Structure → Technology Stack → Success Metrics → Contributing → Documentation) per FR-017 in README.md
- [X] T003 Add all 10 H2 section headings as empty placeholders in FR-016 order per data-model.md section instances in README.md

---

## Phase 2: Foundational (FK-Validated Sections & Key Constraints)

**Purpose**: Write the three readability-constrained sections first (FK Grade ≤ 8.0) because they are the hardest to get right and block US1 and US4 validation

**⚠️ CRITICAL**: These sections have NFR-003/FR-015 readability constraints — write them before other content so FK scores can be validated in isolation

- [X] T004 Write the Project Overview section (FR-001) using plain language at FK Grade ≤ 8.0: describe the multi-agent disaster response system, Australian emergency management context, four stakeholder audiences, and link to constitution at .specify/memory/constitution.md per FR-015/NFR-003 in README.md
- [X] T005 Write the AIIMS Personas & Human Authority section (FR-005): include AIIMS role mapping table (IC, Operations, Planning, Logistics, Public Information), add standalone IC authority blockquote per CHK018 resolution and SC-004, link to constitution, and maintain FK Grade ≤ 8.0 per FR-015 in README.md
- [X] T006 Write the Quickstart section shell (FR-003/FR-004): add clone/install/run commands for all 3 runtimes (API, Agent, Web) — commands always visible, no Azure credentials required — and add "Deploy to Azure" subsection linking to infra/ per FR-003, maintaining FK Grade ≤ 8.0 per NFR-003 in README.md
- [X] T007 Add collapsible prerequisites subsections inside Quickstart: "Prerequisites for Local Development" (Python ≥3.12, Node.js ≥22, pnpm 10.6.3, uv, Docker, Git) and "Prerequisites for Azure Deployment" (Azure CLI ≥2.60, Azure subscription, azd) per CHK017 resolution and FR-004 in README.md
- [X] T008 Validate FK Grade Level ≤ 8.0 for Overview, Quickstart, and Personas sections using textstat.flesch_kincaid_grade() per RT-003 resolution — revise any section scoring above 8.0

**Checkpoint**: Three FK-constrained sections complete and validated — foundational readability gate passed

---

## Phase 3: User Story 1 — Understand the Project at a Glance (Priority: P1) 🎯 MVP

**Goal**: A first-time visitor can determine what the project is, who it serves, how it is built, and where to go next within 2 minutes (SC-001)

**Independent Test**: Give the README to a person unfamiliar with the project — they can answer "What does this system do?", "Who is it for?", "How is it built?", and "Where do I go next?" within 2 minutes

### Implementation for User Story 1

- [X] T009 [US1] Write the Agents section (FR-014): describe all 5 agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication) with summary lines always visible and detailed descriptions in collapsible `<details>` blocks per FR-017; use "agent" terminology (never "service") per FR-014 in README.md
- [X] T010 [US1] Create the Mermaid architecture diagram (FR-002): simplified `graph TD` showing 3 runtimes (Web/Next.js → API/FastAPI → Agent/Python), 5 agents, and Azure services (Cosmos DB, Redis, Blob Storage) — ≤30 lines, NOT inside `<details>`, use "runtime" not "service" in labels per RT-001 in README.md
- [X] T011 [US1] Write brief architecture context paragraph below the Mermaid diagram linking to full architecture at docs/disaster-response-hub/architecture.md per FR-002 in README.md
- [X] T012 [US1] Write the Documentation Links section (FR-006) organized by audience: Evaluators (AMA_Rubric_Asia.md, capstone.md, docs/disaster-response-hub/demo/executive-deck.md), Developers (docs/disaster-response-hub/architecture.md, specs/, .specify/memory/constitution.md), Operators (docs/disaster-response-hub/operator-runbooks.md, docs/disaster-response-hub/demo/walkthrough.md) per FR-006 in README.md
- [X] T013 [US1] Add IC authority cross-reference sentence in the Documentation Links section per CHK018 resolution: "See the Project Constitution for complete life-safety principles, including the Incident Commander's final authority over all safety-critical decisions" per FR-013 in README.md

**Checkpoint**: User Story 1 complete — first-time visitor can understand the project, see the architecture, find all key links, and identify all agents within 2 minutes

---

## Phase 4: User Story 2 — Set Up a Local Development Environment (Priority: P1)

**Goal**: A developer can clone, install, and run all 3 runtimes locally by following the quickstart (SC-002: under 15 minutes)

**Independent Test**: Follow the quickstart instructions on a clean machine with prerequisites installed — all three runtimes start without errors

### Implementation for User Story 2

- [X] T014 [US2] Refine the Quickstart run commands (FR-003): verify and document exact clone, dependency install, and startup commands for API runtime (FastAPI), Agent runtime (Python), and Web runtime (Next.js) — ensure commands work on a fresh clone per FR-003 in README.md
- [X] T015 [US2] Write the Contributing section (FR-010): document branching conventions, PR workflow, commit expectations, and local quality check commands (lint + test per runtime) per FR-010 in README.md
- [X] T016 [US2] Add CI/CD pipeline reference (FR-011): reference .github/workflows/ci.yml, document how to run tests and linting locally for each runtime, and describe what automated checks run on pull requests per FR-011 in README.md

**Checkpoint**: User Story 2 complete — developer can set up local dev environment, run quality checks, and understand the contribution workflow

---

## Phase 5: User Story 3 — Navigate the Monorepo Structure (Priority: P2)

**Goal**: A developer can locate any module, agent, or documentation directory within the monorepo using the README's structure guide

**Independent Test**: Ask a developer unfamiliar with the codebase to locate the evacuation agent code, Bicep templates, and shared domain models using only the README

### Implementation for User Story 3

- [X] T017 [US3] Write the Repository Structure section (FR-009): document monorepo layout inside a collapsible `<details>` block with descriptive `<summary>` label — include apps/ (api, agents/5 subdirs, web, ingestion), packages/ (domain, schemas, ui), infra/, specs/, tests/, docs/, scripts/ per FR-009/FR-017 in README.md
- [X] T018 [US3] Write the Technology Stack section (FR-008): list core technologies (FastAPI, Python, Next.js), Azure services (Container Apps, App Service, Cosmos DB, Redis, Blob Storage), and deployment target ("Azure regions within Australia", primary: Australia East) per FR-008 in README.md

**Checkpoint**: User Story 3 complete — developer or architect can navigate the monorepo and understand the technology stack

---

## Phase 6: User Story 4 — Understand AIIMS Role Mapping and Human Authority (Priority: P2)

**Goal**: An incident commander or safety evaluator can identify AIIMS role mappings and confirm human authority over safety-critical decisions within 60 seconds (SC-004)

**Independent Test**: Have an emergency management professional read the personas section and correctly identify AIIMS role-to-capability mappings and confirm IC final authority

### Implementation for User Story 4

- [X] T019 [US4] Review and refine the AIIMS Personas section (written in T005): verify the role mapping table covers IC, Operations Officer, Planning Officer, Logistics Officer, and Public Information Officer with corresponding system capabilities; verify IC authority blockquote is standalone, visible, NOT in `<details>`, and NOT buried in a list per SC-004/FR-013 in README.md
- [X] T020 [US4] Verify constitution link in Personas section resolves to .specify/memory/constitution.md and cross-reference sentence in Documentation section (T013) aligns with the primary IC authority statement per CHK018 in README.md

**Checkpoint**: User Story 4 complete — AIIMS role mapping is clear, IC authority is prominent and standalone

---

## Phase 7: User Story 5 — Evaluate Project Success Criteria and Maturity (Priority: P3)

**Goal**: An evaluator can locate success metrics, technology stack, and deployment target within 60 seconds of opening the README

**Independent Test**: Have an evaluator find all 5 capstone targets, the deployment region, and the key Azure services within 60 seconds

### Implementation for User Story 5

- [X] T021 [US5] Write the Success Metrics section (FR-007): list all 5 capstone targets (1,000+ lives saved annually, 50% response time reduction, 24-hour earlier evacuations, 30% resource efficiency improvement, 30% economic loss reduction) and link to capstone.md per FR-007 in README.md

**Checkpoint**: User Story 5 complete — evaluators can quickly assess project ambition and measurable goals

---

## Phase 8: User Story 6 — Contribute to the Project (Priority: P3)

**Goal**: A new contributor can understand branching conventions, run local quality checks, and follow the PR workflow

**Independent Test**: Have a new contributor read the contribution section, create a branch, run local quality checks, and describe the PR process

### Implementation for User Story 6

- [X] T022 [US6] Review and refine the Contributing section (written in T015/T016): ensure branching conventions, PR workflow, local lint/test commands per runtime, and CI pipeline reference are complete and actionable per FR-010/FR-011 in README.md

**Checkpoint**: User Story 6 complete — new contributors have a clear path to contribution

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Document-wide quality validation, constraint enforcement, and cross-cutting consistency checks

- [X] T023 Enforce `<details>` block formatting: verify all collapsible blocks have descriptive `<summary>` labels (NFR-004), blank line after `<summary>`, blank line before `</details>` per RT-002 best practices in README.md
- [X] T024 Enforce terminology consistency (SC-010): search for "service" used for agents and "agent" used for runtimes — use "agent" for 5 AI components, "runtime" for 3 execution environments per FR-014/RT-007 terminology mapping in README.md
- [X] T025 Validate all internal links resolve (SC-007): extract all relative `[text](path)` links and verify each target file/directory exists — reference RT-006 confirmed list: architecture.md, constitution.md, ci.yml, AMA_Rubric_Asia.md, capstone.md, executive-deck.md, operator-runbooks.md, walkthrough.md, specs/, infra/ in README.md
- [X] T026 Validate line count ≤ 500 (NFR-001/SC-008): run `(Get-Content README.md).Count` and adjust content or add `<details>` blocks if over budget — target ~420–480 lines per RT-008 line budget in README.md
- [X] T027 Re-validate FK Grade Level ≤ 8.0 for Overview, Quickstart, and Personas sections using textstat after all edits — revise if any section exceeds threshold per NFR-003/SC-009 in README.md
- [X] T028 Validate Table of Contents anchors (V-008): verify all 10 ToC links resolve to actual H2 headings in the document per FR-017 in README.md
- [X] T029 Verify Mermaid diagram is NOT inside a `<details>` block (V-007) and renders correctly on GitHub per FR-002/FR-017 in README.md
- [X] T030 Verify GitHub rendering: confirm README.md renders correctly on GitHub desktop and mobile — all `<details>` blocks expand/collapse, Mermaid diagram renders, tables are formatted per FR-012/SC-006 in README.md
- [X] T031 Final review: confirm all 10 FR-016 content sections are present in specified order, all 17 functional requirements (FR-001–FR-017) are addressed, and all 10 success criteria (SC-001–SC-010) are satisfiable per spec.md in README.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (skeleton must exist) — BLOCKS all user stories because FK-validated sections are shared across US1, US2, and US4
- **User Story 1 (Phase 3)**: Depends on Phase 2 — adds agents, architecture, and documentation links
- **User Story 2 (Phase 4)**: Depends on Phase 2 — refines quickstart and adds contributing section
- **User Story 3 (Phase 5)**: Depends on Phase 2 — adds repository structure and technology stack
- **User Story 4 (Phase 6)**: Depends on Phase 2 (specifically T005) — reviews and refines personas
- **User Story 5 (Phase 7)**: Depends on Phase 1 — adds success metrics (independent of other stories)
- **User Story 6 (Phase 8)**: Depends on Phase 4 (specifically T015/T016) — reviews contributing section
- **Polish (Phase 9)**: Depends on ALL user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P1)**: Depends on Foundational (Phase 2) — no dependencies on other stories
- **User Story 3 (P2)**: Depends on Phase 1 skeleton only — can start after Phase 1 if needed
- **User Story 4 (P2)**: Depends on T005 (personas section from Phase 2)
- **User Story 5 (P3)**: Depends on Phase 1 skeleton only — fully independent
- **User Story 6 (P3)**: Depends on US2 (T015/T016 must exist before review)

### Within Each User Story

- Content sections that share a file must be written sequentially (single-file constraint)
- FK-validated sections must be written and validated before dependent stories begin
- Collapsible block formatting must follow RT-002 pattern on every `<details>` block
- Terminology must be checked after each section is written

### Parallel Opportunities

- **Phase 2**: T004, T005, T006 can be drafted in parallel (different sections, same file — merge sequentially)
- **Phase 3–7**: US1, US2, US3, US5 can be drafted in parallel after Phase 2 (independent content areas)
- **Phase 9**: T023–T025 (formatting, terminology, link validation) can run in parallel as validation checks

---

## Parallel Example: Phase 2 (Foundational)

```text
# Draft FK-validated sections in parallel (merge into README.md sequentially):
Task T004: "Write Project Overview section (FK8)" → draft overview text
Task T005: "Write AIIMS Personas section (FK8)" → draft personas text
Task T006: "Write Quickstart section shell (FK8)" → draft quickstart text

# Then merge all three into README.md and validate:
Task T008: "Validate FK Grade Level ≤ 8.0 for all three sections"
```

## Parallel Example: User Stories 1, 2, 3, 5

```text
# After Phase 2, draft independent story content in parallel:
Task T009: [US1] "Write Agents section"
Task T014: [US2] "Refine Quickstart run commands"
Task T017: [US3] "Write Repository Structure section"
Task T021: [US5] "Write Success Metrics section"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003) — create file skeleton
2. Complete Phase 2: Foundational (T004–T008) — write and validate FK-constrained sections
3. Complete Phase 3: User Story 1 (T009–T013) — add agents, architecture, documentation links
4. **STOP and VALIDATE**: The README should orient any first-time visitor within 2 minutes
5. Share for early feedback

### Incremental Delivery

1. Setup + Foundational → Document skeleton with core readability-validated sections
2. Add User Story 1 → Full project orientation (MVP!)
3. Add User Story 2 → Developer quickstart and contribution guidelines
4. Add User Stories 3 + 4 → Monorepo navigation and AIIMS governance
5. Add User Stories 5 + 6 → Success metrics and contribution refinement
6. Polish (Phase 9) → Full validation pass across all constraints

### Single-Author Strategy (Recommended)

Since this is a single-file deliverable, the optimal approach is:

1. Write the skeleton (Phase 1) — 5 minutes
2. Write FK-constrained sections first (Phase 2) — these are hardest to revise later
3. Fill remaining sections top-to-bottom in FR-016 order (Phases 3–8)
4. Run all validation checks (Phase 9)
5. Commit the complete README.md

---

## Requirement Coverage Matrix

| Requirement | Task(s) | Phase |
|-------------|---------|-------|
| FR-001 | T001, T004 | 1, 2 |
| FR-002 | T010, T011, T029 | 3, 9 |
| FR-003 | T006, T014 | 2, 4 |
| FR-004 | T007 | 2 |
| FR-005 | T005, T019 | 2, 6 |
| FR-006 | T012 | 3 |
| FR-007 | T021 | 7 |
| FR-008 | T018 | 5 |
| FR-009 | T017 | 5 |
| FR-010 | T015, T022 | 4, 8 |
| FR-011 | T016, T022 | 4, 8 |
| FR-012 | T030 | 9 |
| FR-013 | T005, T013, T020 | 2, 3, 6 |
| FR-014 | T009, T024 | 3, 9 |
| FR-015 | T004, T005, T006, T008, T027 | 2, 9 |
| FR-016 | T002, T003 | 1 |
| FR-017 | T002, T007, T009, T017, T023, T028, T029 | 1, 2, 3, 5, 9 |
| NFR-001 | T026 | 9 |
| NFR-002 | T002, T003 | 1 |
| NFR-003 | T004, T006, T008, T027 | 2, 9 |
| NFR-004 | T023, T030 | 9 |
| SC-001–SC-010 | T031 (final check) | 9 |

---

## Notes

- This is a **documentation-only** feature — the single deliverable is `README.md` at the repository root
- **No tests** are generated because none were requested in the spec
- **Single-file constraint**: All tasks target `README.md`, limiting true parallelism — but content can be drafted independently and merged sequentially
- **FK Grade 8 sections** (Overview, Quickstart, Personas) should be written first because they are hardest to adjust after surrounding content is in place
- **Terminology discipline** is critical: "agent" for 5 AI components, "runtime" for 3 execution environments — never "service" for either
- **`<details>` blocks** must follow the blank-line pattern from RT-002 to render correctly on GitHub
- Commit after each phase or logical group of tasks
- Reference the quickstart.md in specs/feature/013-root-readme/ for step-by-step implementation guidance
