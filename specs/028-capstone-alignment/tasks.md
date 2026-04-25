# Tasks: Capstone Alignment Hardening Across AMA Specs

**Input**: Design documents from `C:\code\ama\specs\028-capstone-alignment\`
**Prerequisites**: `plan.md` (✅), `spec.md` (✅ clarified), `research.md` (✅), `data-model.md` (✅), `contracts/` (✅ 3 contracts), `quickstart.md` (✅)
**Feature type**: Documentation-only (Markdown edits under `specs/` and `specs/shared/`; no code, no infra, no tests).
**Tests**: No test tasks generated. Spec explicitly declares "documentation-only feature"; validation is grep-based per `quickstart.md`.

## Format: `[ID] [P?] [Story] Description`

- **[P]** — parallelizable (different files, no ordering dependency on incomplete tasks).
- **[Story]** — `[US1]..[US4]` map to User Stories 1–4 in `spec.md`. Setup / Foundational / Polish carry no story label.
- Every task cites absolute file paths and an **Actors** line (which `.github/agents/*.agent.md` actors to consult via the **agent** tool) and a **Tools** line (`execute|read|edit|search|web|agent|todo`).

## Path conventions

- Feature artefacts: `C:\code\ama\specs\028-capstone-alignment\`
- Target spec folders: `C:\code\ama\specs\001-*`..`C:\code\ama\specs\027-*`
- Shared artefacts: `C:\code\ama\specs\shared\`
- Rubric + skills: `C:\code\ama\AMA_Rubric_Asia.md`; `ama-rubric-grader` project skill.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish baselines and ID allocation plan before any spec is touched. Ensures FR-022 monotonicity and SC-009 measurable uplift.

- [ ] T001 Enumerate the current state of every `specs/NNN-*/spec.md` at `C:\code\ama\specs\` and produce a working inventory listing, for each of the 27 specs: (a) presence/absence of each required H2 section (`## Assumptions`, `## Personas`, `## Hypotheses`, `## Out of Scope`), (b) existing ASM/HYP/PER/SCP/REQ IDs used, (c) whether the spec is classified meta or capstone-critical-path per FR-020. Persist the inventory in the SQL session under a new table `spec_inventory` with one row per spec.
  - **Success criteria**: `SELECT count(*) FROM spec_inventory` = 27; every row has boolean columns for the four mandatory sections; capstone-critical vs meta classification matches `contracts/meta-spec-flag.contract.md`.
  - **Actors**: `product-owner-ba` (speckit conventions).
  - **Tools**: `read`, `search`, `sql`.

- [ ] T002 [P] Capture the pre-feature AMA rubric baseline snapshot by invoking the `ama-rubric-grader` project skill against `C:\code\ama\AMA_Rubric_Asia.md` with the current state of `C:\code\ama\specs\`. Persist the baseline scores for the five criteria tied to Assumptions / Requirements / Personas / Hypotheses / Scope into `C:\code\ama\specs\028-capstone-alignment\evidence\rubric-baseline.md`, including per-criterion scores, band, grader run ID, and ISO-8601 timestamp. This baseline is the frozen reference for SC-009's composite gate (Δmean ≥ +1 AND per-criterion Δ ≥ 0).
  - **Success criteria**: file exists; contains exactly the five target criteria as H2s; each criterion has an integer score and a quoted grader rationale; no criterion is missing.
  - **Actors**: `product-owner-ba` (grader invocation); `solution-architect` (confirms criteria mapping).
  - **Tools**: `agent` (invoke `ama-rubric-grader`), `edit`.

- [ ] T003 [P] Read `C:\code\ama\specs\shared\gap-id-register.md` and record the current high-watermark IDs for each family (ASM, HYP, PER, SCP, REQ) in a new SQL table `id_watermarks (family TEXT PRIMARY KEY, current_max INT, feature_028_next_start INT)`. Reserve a contiguous block of IDs for this feature by setting `feature_028_next_start = current_max + 1` per family. No register edits yet — only planning.
  - **Success criteria**: `SELECT family, current_max, feature_028_next_start FROM id_watermarks` returns five rows with `feature_028_next_start = current_max + 1` in every row; this query is the single source of truth for ID allocation in subsequent tasks.
  - **Actors**: `product-owner-ba`.
  - **Tools**: `read`, `sql`.

**Checkpoint**: Setup complete → inventory, rubric baseline, and ID watermarks recorded.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create skeletal shared artefacts and append-only register scaffolding. All user-story phases depend on these.

⚠️ **CRITICAL**: No user-story work may begin until Phase 2 is complete.

- [ ] T004 Create `C:\code\ama\specs\shared\capstone-metric-trace.md` conforming to `contracts/capstone-metric-trace.contract.md`: one H1 title, one paragraph intro, one Markdown table with the seven required columns in exact order, **20 rows** (5 metrics × 4 cohorts: AU-v1, PH, JP, BD). Each row's `Status` starts as `Unresolved`; `SC Owner`, `HYP Owner`, `Baseline`, `Measurement Method` cells carry the placeholder literal `TBD — see tasks T039..T043` and will be filled during US2. File header line must reference spec 028.
  - **Success criteria**: exactly 20 data rows; every `(Metric, Country Cohort)` pair from the full cross-product of the two closed enums appears once; no `NEEDS CLARIFICATION` marker.
  - **Actors**: `product-owner-ba`.
  - **Tools**: `read`, `edit`.

- [ ] T005 Append a new block `## Feature 028 Allocations` to `C:\code\ama\specs\shared\gap-id-register.md`, reserving monotonic ID blocks using the starts captured in T003. Document the allocation range per family (e.g., `ASM-### to ASM-###`, `HYP-### to HYP-###`, `PER-### to PER-###`, `SCP-### to SCP-###`). All subsequent tasks MUST consume IDs strictly inside these ranges. No existing ID is modified.
  - **Success criteria**: `git diff specs/shared/gap-id-register.md` shows only additions; every reserved range begins at `current_max + 1`; block header cites `specs/028-capstone-alignment/plan.md`.
  - **Actors**: `product-owner-ba`.
  - **Tools**: `read`, `edit`, `sql`.

- [ ] T006 [P] Create the feature evidence folder `C:\code\ama\specs\028-capstone-alignment\evidence\` (parent directory must exist before any stub is written in later tasks). Additionally, pre-create per-agent evidence folders that will receive capstone-country HYP stubs in US2: `C:\code\ama\specs\008-communication-agent\evidence\`, `specs\009-evacuation-agent\evidence\`, `specs\010-monitoring-agent\evidence\`, `specs\011-resource-allocation-agent\evidence\`, `specs\012-risk-assessment-agent\evidence\`.
  - **Success criteria**: all six `evidence` folders exist; `Test-Path` returns `True` for each.
  - **Actors**: none (mechanical).
  - **Tools**: `execute`.

- [ ] T007 [P] Author a tiny reusable validator PowerShell snippet at `C:\code\ama\specs\028-capstone-alignment\scripts\validate-section-coverage.ps1` (create `scripts/` folder) that grep-checks every `specs/NNN-*/spec.md` (excluding `specs/shared/` and `specs/feature/`) for the four mandatory H2 headings and counts `NEEDS CLARIFICATION` markers. Output: CSV to stdout. This is used in Phase 7 polish and by reviewers per `quickstart.md`.
  - **Success criteria**: script runs with `pwsh -File` and exits 0; CSV columns `Spec,Assumptions,Personas,Hypotheses,OutOfScope,NeedsClarificationCount`.
  - **Actors**: `qa-test-engineer` (testability review).
  - **Tools**: `edit`, `execute`.

**Checkpoint**: Foundational complete → metric-trace skeleton, ID allocations, evidence folders, validator script. User-story phases may now run in parallel by story.

---

## Phase 3: User Story 1 — Reviewer audits every spec for capstone alignment (P1) 🎯 MVP

**Goal**: Every `specs/NNN-*/spec.md` (excluding `shared/` and `feature/`) contains the four mandatory H2 sections (`## Assumptions`, `## Personas`, `## Hypotheses`, `## Out of Scope`) populated per FR-001..FR-005, with content rules cross-referenced to spec-001 / spec-027 taxonomy.

**Independent Test**: Run T007's validator across the tree and inspect any 5 randomly-selected specs among 003..026 — every row shows `True` for all four H2 columns and content satisfies FR-001..FR-005 (≥3 assumptions tagged correctly, ≥2 personas or cross-refs, ≥1 FR-018-format hypothesis with linked stub, ≥3 scope items with ≥1 capstone-country deferral).

> **Execution note**: Tasks T008..T033 edit 26 different spec files (parallel-safe as `[P]`), plus spec 001 (T008) and spec 027 (T034) which are sequenced first because they are cross-referenced by everything else. Complete T008 + T034 before launching the parallel batch T009..T033.

### Authoritative cross-reference targets (must complete first)

- [ ] T008 [US1] Update `C:\code\ama\specs\001-disaster-response-hub\spec.md` to add/confirm the four mandatory H2 sections, then specifically: (a) add an Out-of-Scope item explicitly naming PH/JP/BD as deferred with the promotion preconditions from spec 001 DEF-001..003; (b) insert a cross-reference note under `## Assumptions` pointing any later spec to reuse its ASM IDs; (c) add an explicit `defers-to: 018` pointer at DEF-015 (recovery phase) per FR-018 / D-005; (d) do NOT renumber any existing ID. All additions consume IDs from the block reserved in T005.
  - **Success criteria**: four H2 headings present; new Out-of-Scope bullet cites PH/JP/BD explicitly; DEF-015 carries `defers-to: 018`; `git diff` shows no renumbered IDs; zero `NEEDS CLARIFICATION` introduced.
  - **Actors**: `incident-commander` (content rationale for coordination assumptions); `resilience-planner` (deferred-scope preconditions); `product-owner-ba` (taxonomy correctness).
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T009 [US1] Update `C:\code\ama\specs\027-spec-hardening\spec.md` to replace the stale `028-holistic-spec-hardening` reference on line 18 with `028-capstone-alignment` (this feature), add a scope note declaring cross-spec hardening is owned by spec 028, and reaffirm the four mandatory H2 sections are present (027 should already satisfy them; fill any gap). This task implements FR-019.
  - **Success criteria**: `grep -n "028-holistic-spec-hardening" specs/027-spec-hardening/spec.md` returns 0 matches; new pointer references `028-capstone-alignment`; all four H2 sections present.
  - **Actors**: `product-owner-ba`.
  - **Tools**: `read`, `edit`.

### Per-spec hardening — parallel batch (one task per spec, distinct file paths)

Every task below: (i) ensure the four mandatory H2 sections exist with FR-001..FR-005 content, (ii) add ≥1 Out-of-Scope bullet deferring at least one capstone country (PH/JP/BD) or hazard with explicit preconditions, (iii) if the spec's existing assumption/persona/hypothesis block uses a different format, add a taxonomy-mapping row rather than rewriting (FR-005), (iv) consume IDs strictly from the block reserved in T005, (v) introduce zero `NEEDS CLARIFICATION` markers, (vi) add the documented-tension `[RISK]` assumption about AU-only-residency vs capstone-sovereign-data (D-009) iff the spec touches PII or persona data.

- [ ] T010 [P] [US1] Harden `C:\code\ama\specs\003-rubric-gap-closure\spec.md` per the rules above. Spec is meta — see US4/T053 for the additional meta flag.
  - **Success criteria**: all four H2s present; ≥3 assumptions tagged; ≥2 personas or cross-refs; ≥1 FR-018 hypothesis; validator T007 reports `True` for all four columns.
  - **Actors**: `product-owner-ba`, `qa-test-engineer`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T011 [P] [US1] Harden `C:\code\ama\specs\004-actor-github-agents\spec.md` per the rules above. Out-of-Scope MUST explicitly name PH/JP/BD as non-applicable-today with promotion preconditions (per spec.md Edge Cases bullet 3). Spec is meta — see US4/T054.
  - **Actors**: `product-owner-ba`.
  - **Tools**: `read`, `edit`.

- [ ] T012 [P] [US1] Harden `C:\code\ama\specs\005-data-source-governance\spec.md` per the rules above, AND implement FR-007: add a per-country PII classification FR naming `Privacy Act 1988 (Cth) + APPs` (AU), `APPI 2017/2020` (JP), `RA 10173 DPA 2012 + NPC issuances` (PH), `ICT Act 2006 + draft DPA 2023` (BD); non-AU entries marked deferred with preconditions. Include the AU-only-residency tension `[RISK]` assumption (D-009).
  - **Success criteria**: new FR explicitly names all four regimes; three non-AU regimes tagged `deferred`; `[RISK]` assumption present and tagged `linked_gaps` to constitution NON-NEGOTIABLE #2.
  - **Actors**: `compliance-auditor`, `security-engineer`, `product-owner-ba`.
  - **Tools**: `read`, `edit`, `agent`, `web` (cite NPC / BD DPA 2023 draft URLs if needed).

- [ ] T013 [P] [US1] Harden `C:\code\ama\specs\006-data-ingestion-storage\spec.md` per the rules above, AND implement FR-009: add a deferred-scope FR enumerating at least one candidate feed per capstone country with validation preconditions — PH: PAGASA; JP: JMA (JAXA/QZSS for location); BD: BWDB / FFWC. Capture data-sovereignty tension `[RISK]`.
  - **Success criteria**: new deferred FR names all three feeds; preconditions list data-sharing MoU + schema validation + freshness SLO per feed.
  - **Actors**: `data-engineer`, `bom-national` (analog weather feed rationale for PAGASA), `ga-national` (analog for JMA earthquake/tsunami).
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T014 [P] [US1] Harden `C:\code\ama\specs\007-simulation-tenant-isolation\spec.md` per the rules above. Spec is meta — see US4/T055.
  - **Actors**: `security-engineer`, `product-owner-ba`.
  - **Tools**: `read`, `edit`.

- [ ] T015 [P] [US1] Harden `C:\code\ama\specs\008-communication-agent\spec.md` per the rules above, AND implement FR-006: add a language-pack plugin FR requiring ≥1 non-English language pack per capstone country (Philippines, Japan, Bangladesh) as a deferred capability; each entry has content-safety + back-translation preconditions. **Explicitly defer BCP-47 identifier selection to `specs/008-communication-agent/research.md`** per clarification Q2/D-004. Add a deferred FR for multilingual-misinformation-detection that inherits the spec-010 fallback rule. Also add an explicit `defers-to: 018` pointer for the warning-tier approval-timeout supersession per FR-017. Record the HYPs for this spec in US2/T035.
  - **Success criteria**: new language-pack FR mentions PH/JP/BD by name; text `"BCP-47 identifier selection is deferred to research.md"` present; `defers-to: 018` line present next to the escalation-timeout prose; no identifier (`fil-PH`/`ja-JP`/`bn-BD`) is hard-coded in spec.md.
  - **Actors**: `public-information-officer`, `accessibility-tester` (multilingual validation posture), `ai-ml-engineer` (misinformation detection).
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T016 [P] [US1] Harden `C:\code\ama\specs\009-evacuation-agent\spec.md` per the rules above. Hypotheses allocated in US2/T036.
  - **Actors**: `planning-officer`, `operations-officer`, `resilience-planner`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T017 [P] [US1] Harden `C:\code\ama\specs\010-monitoring-agent\spec.md` per the rules above. Hypotheses allocated in US2/T037.
  - **Actors**: `planning-officer`, `risk-manager`, `ai-ml-engineer`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T018 [P] [US1] Harden `C:\code\ama\specs\011-resource-allocation-agent\spec.md` per the rules above, AND add an explicit `defers-to: 018` pointer at the resource-recovery section per FR-018 / D-005. Hypotheses allocated in US2/T038.
  - **Success criteria**: `defers-to: 018` pointer present adjacent to any recovery-phase prose.
  - **Actors**: `logistics-officer`, `operations-officer`, `resilience-planner`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T019 [P] [US1] Harden `C:\code\ama\specs\012-risk-assessment-agent\spec.md` per the rules above. Confirm the hazard taxonomy owned here is extended (not replaced) to explicitly name typhoon (PH), earthquake (JP), riverine/cyclone-driven flood (BD) as deferred country-scoped instances of the existing AU hazard classes per P-004. Hypotheses allocated in US2/T039.
  - **Success criteria**: hazard table now includes PH/JP/BD rows tagged deferred; no existing AU hazard row modified.
  - **Actors**: `risk-manager`, `ga-national` (earthquake analog), `ntes` (tropical cyclone analog), `bom-national`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T020 [P] [US1] Harden `C:\code\ama\specs\013-root-readme\spec.md` per the rules above. Spec is meta — see US4/T056.
  - **Actors**: `product-owner-ba`.
  - **Tools**: `read`, `edit`.

- [ ] T021 [P] [US1] Harden `C:\code\ama\specs\014-azure-openai-integration\spec.md` per the rules above. Include the AU-only-residency tension `[RISK]` assumption (D-009) because the spec handles LLM traffic.
  - **Actors**: `ai-ml-engineer`, `azure-principal-architect`, `security-engineer`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T022 [P] [US1] Harden `C:\code\ama\specs\015-performance-benchmarks\spec.md` per the rules above, AND implement FR-012: add SC rows mapping at least one benchmark scenario to each of the five capstone success metrics (`LIVES_SAVED`, `RESPONSE_SPEED`, `EVAC_LEAD_TIME`, `LOGISTICS_EFFICIENCY`, `ECONOMIC_LOSS_REDUCTION`) with baseline and measurement method. SC cells here are the prime candidates for metric-trace SC-Owner citations in T039..T043.
  - **Success criteria**: five new SC rows each naming one capstone metric in enum form; each has baseline + measurement method; zero placeholder.
  - **Actors**: `qa-test-engineer`, `sre-engineer`, `product-owner-ba`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T023 [P] [US1] Harden `C:\code\ama\specs\016-automated-demo-script\spec.md` per the rules above. Spec is meta — see US4/T057.
  - **Actors**: `product-owner-ba`.
  - **Tools**: `read`, `edit`.

- [ ] T024 [P] [US1] Harden `C:\code\ama\specs\017-cd-pipeline\spec.md` per the rules above, AND implement FR-010: add a deferred FR declaring that the pipeline supports region-per-country topology; today deploys to `australiaeast` / `australiasoutheast` only; reversal of the AU-only default is explicitly a capstone-reinterpretation decision owned outside this feature (reference constitution NON-NEGOTIABLE #2 and D-009). Spec is meta — see US4/T058.
  - **Actors**: `infrastructure-devops`, `azure-principal-architect`, `security-engineer`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T025 [P] [US1] Harden `C:\code\ama\specs\018-aidr-guidance-integration\spec.md` per the rules above, AND add an authoritative scope rule: "Spec 018 is the authoritative owner of recovery-phase indicators, triggers, and phase-exit criteria across the portfolio" per FR-018 / D-005. Also add the reciprocal scope rule making 018 authoritative for warning-tier approval-timeout escalation (FR-017).
  - **Success criteria**: scope rule mentioning "authoritative for recovery-phase" present; escalation-timeout authority statement present; no existing section renamed or deleted.
  - **Actors**: `incident-commander`, `resilience-planner`, `planning-officer`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T026 [P] [US1] Harden `C:\code\ama\specs\019-aidr-additional-guidances\spec.md` per the rules above.
  - **Actors**: `resilience-planner`, `product-owner-ba`.
  - **Tools**: `read`, `edit`.

- [ ] T027 [P] [US1] Harden `C:\code\ama\specs\020-disaster-mapper-ui\spec.md` per the rules above.
  - **Actors**: `ux-designer`, `accessibility-tester`, `operations-officer`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T028 [P] [US1] Harden `C:\code\ama\specs\021-governance-dashboard\spec.md` per the rules above.
  - **Actors**: `ux-designer`, `observer-auditor`, `compliance-auditor`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T029 [P] [US1] Harden `C:\code\ama\specs\022-multi-jurisdiction-filter\spec.md` per the rules above, AND implement FR-008: add a country-dimension FR supporting a nested `country → state/region` hierarchy; PH/JP/BD nodes MUST be present as placeholders with preconditions; the existing 9-AU-jurisdiction UI is preserved unchanged (ASM reaffirms preservation).
  - **Success criteria**: hierarchy block shows `AU → {NSW, VIC, QLD, SA, WA, TAS, ACT, NT, Commonwealth}` unchanged; new nodes `PH → {placeholder}`, `JP → {placeholder}`, `BD → {placeholder}` present with preconditions.
  - **Actors**: `ux-designer`, `solution-architect`, `state-government`, `local-government`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T030 [P] [US1] Harden `C:\code\ama\specs\023-dashboard-real-data\spec.md` per the rules above.
  - **Actors**: `ux-designer`, `data-engineer`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T031 [P] [US1] Harden `C:\code\ama\specs\024-simulation-control-chat\spec.md` per the rules above. Spec is meta — see US4/T059.
  - **Actors**: `ai-ml-engineer`, `ux-designer`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T032 [P] [US1] Harden `C:\code\ama\specs\025-agent-spec-compliance\spec.md` per the rules above. Spec is meta — see US4/T060.
  - **Actors**: `qa-test-engineer`, `product-owner-ba`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T033 [P] [US1] Harden `C:\code\ama\specs\026-sim-warp-playback\spec.md` per the rules above. Spec is meta — see US4/T061.
  - **Actors**: `qa-test-engineer`, `ux-designer`.
  - **Tools**: `read`, `edit`, `agent`.

**Checkpoint**: US1 complete → run `pwsh -File specs/028-capstone-alignment/scripts/validate-section-coverage.ps1`; every row reports `True` for all four H2 columns and `NeedsClarificationCount = 0`. MVP is shippable after this phase.

---

## Phase 4: User Story 2 — Solution-as-a-whole demonstrably covers the five capstone success metrics (P1)

**Goal**: The five capstone metrics each have named SC and HYP owners per country cohort, captured in `specs/shared/capstone-metric-trace.md` and backed by `evidence/HYP-*.md` stubs.

**Independent Test**: Open `specs/shared/capstone-metric-trace.md`, confirm 20 rows, and follow every cited `<spec>:<ID>` reference back to its source spec — each ID exists. Grep all `HYP-*.md` evidence stubs — each contains the six required H2 headings per `contracts/evidence-stub.contract.md`.

### Capstone-country hypotheses (≥3 per agent spec × 5 agent specs = ≥15 HYPs)

Each task below allocates monotonic HYP IDs from T005's reserved block, edits the owning spec's `## Hypotheses` section to add ≥3 hypotheses (one per capstone country: PH, JP, BD) using the spec-027 FR-018 statement format, and creates one `evidence/HYP-<id>.md` stub per new hypothesis conforming to `contracts/evidence-stub.contract.md`.

- [ ] T034 [P] [US2] Add 3 capstone-country hypotheses (PH/JP/BD) and matching evidence stubs for spec 008 (Communication Agent) at `C:\code\ama\specs\008-communication-agent\spec.md` and `C:\code\ama\specs\008-communication-agent\evidence\HYP-<id>.md` (×3). Hypotheses target multilingual alert delivery and misinformation detection per capstone country; measurement windows: PH typhoon season Jun–Nov; JP continuous with quarterly review; BD monsoon Apr–Sep.
  - **Success criteria**: 3 new HYPs present, each using the FR-018 format; 3 stubs created, each with the six mandatory H2 headings; `## Status` body = `Not tested`.
  - **Actors**: `public-information-officer`, `accessibility-tester`, `ai-ml-engineer`.
  - **Tools**: `read`, `edit`, `agent`, `sql` (allocate HYP IDs).

- [ ] T035 [P] [US2] Add 3 capstone-country hypotheses and stubs for spec 009 (Evacuation Agent) at `C:\code\ama\specs\009-evacuation-agent\spec.md` + `evidence\HYP-<id>.md`. Hypotheses target pre-warned vs immediate evacuation lead-time per capstone hazard (typhoon pre-warned PH; earthquake immediate JP; flood pre-warned BD).
  - **Actors**: `planning-officer`, `operations-officer`, `resilience-planner`, `transport`.
  - **Tools**: `read`, `edit`, `agent`, `sql`.

- [ ] T036 [P] [US2] Add 3 capstone-country hypotheses and stubs for spec 010 (Monitoring Agent) at `C:\code\ama\specs\010-monitoring-agent\spec.md` + `evidence\HYP-<id>.md`. Target hypotheses: PH PAGASA feed detection, JP JMA earthquake alert latency, BD BWDB/FFWC flood signal ingestion.
  - **Actors**: `ai-ml-engineer`, `data-engineer`, `bom-national`, `ga-national`.
  - **Tools**: `read`, `edit`, `agent`, `sql`.

- [ ] T037 [P] [US2] Add 3 capstone-country hypotheses and stubs for spec 011 (Resource Allocation Agent) at `C:\code\ama\specs\011-resource-allocation-agent\spec.md` + `evidence\HYP-<id>.md`. Target hypotheses: capstone-country logistics efficiency (30% target) per country, accounting for road/rail topology differences (BD deltaic; JP urban-dense; PH archipelagic).
  - **Actors**: `logistics-officer`, `operations-officer`, `transport`, `adf`.
  - **Tools**: `read`, `edit`, `agent`, `sql`.

- [ ] T038 [P] [US2] Add 3 capstone-country hypotheses and stubs for spec 012 (Risk Assessment Agent) at `C:\code\ama\specs\012-risk-assessment-agent\spec.md` + `evidence\HYP-<id>.md`. Target hypotheses: country-scoped risk-index calibration for typhoon (PH), earthquake (JP), riverine flood (BD); falsification when calibration error exceeds a quantified threshold during the named measurement window.
  - **Actors**: `risk-manager`, `ga-national`, `ntes`, `bom-national`.
  - **Tools**: `read`, `edit`, `agent`, `sql`.

### Metric-trace population (fill the 20 rows created in T004)

- [ ] T039 [P] [US2] Populate the 4 rows for metric `LIVES_SAVED` in `C:\code\ama\specs\shared\capstone-metric-trace.md`. For AU-v1 cohort: assign SC/HYP owners from spec 001 or spec 015 (selected in T022); if no existing SC maps directly to 1,000+ lives/yr, this task adds a new SC in spec 001 that does — allocating a new ID from T005's block. For PH/JP/BD rows: set `Status = Deferred` with explicit preconditions per D-003 / P-003. Update row `Status` accordingly (`Validated` iff both owners point to real IDs, else `Deferred`).
  - **Success criteria**: all 4 `LIVES_SAVED` rows have both owner cells filled; AU-v1 row Status = Validated; PH/JP/BD rows Status = Deferred with non-empty preconditions.
  - **Actors**: `qa-test-engineer`, `incident-commander`, `nema`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T040 [P] [US2] Populate the 4 rows for metric `RESPONSE_SPEED` (50% faster response) in `C:\code\ama\specs\shared\capstone-metric-trace.md`. AU-v1 candidate owner: spec 001 SC-004 (50% response) and an AU-v1 HYP. PH/JP/BD rows: Deferred with preconditions naming country feed + agent deployment.
  - **Actors**: `qa-test-engineer`, `operations-officer`, `sre-engineer`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T041 [P] [US2] Populate the 4 rows for metric `EVAC_LEAD_TIME` (24 h earlier evacuation) in `C:\code\ama\specs\shared\capstone-metric-trace.md`. AU-v1 candidate owner: spec 001 SC-005 or spec 009 SC (see T022). PH/JP/BD rows: Deferred with preconditions citing the 3 HYPs created in T035.
  - **Actors**: `planning-officer`, `resilience-planner`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T042 [P] [US2] Populate the 4 rows for metric `LOGISTICS_EFFICIENCY` (30% efficiency) in `C:\code\ama\specs\shared\capstone-metric-trace.md`. AU-v1 owner: spec 001 SC-006 or spec 011 SC; PH/JP/BD: Deferred citing T037 HYPs.
  - **Actors**: `logistics-officer`, `qa-test-engineer`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T043 [P] [US2] Populate the 4 rows for metric `ECONOMIC_LOSS_REDUCTION` (30% economic loss reduction) in `C:\code\ama\specs\shared\capstone-metric-trace.md`. If no existing SC or HYP maps to this metric, allocate new IDs from T005's block and add SC in spec 015 and HYP in spec 012 (referencing the T038 stubs); otherwise cite existing IDs. PH/JP/BD: Deferred with preconditions.
  - **Success criteria**: zero rows remain with `Status = Unresolved`; `grep -c Unresolved specs/shared/capstone-metric-trace.md` returns 0.
  - **Actors**: `risk-manager`, `executive-leader`, `compliance-auditor`.
  - **Tools**: `read`, `edit`, `agent`.

**Checkpoint**: US2 complete → `specs/shared/capstone-metric-trace.md` has 20 fully populated rows, zero `Unresolved`; ≥15 new capstone-country HYPs exist with matching evidence stubs; every HYP stub passes the `contracts/evidence-stub.contract.md` validator (6 H2 headings, `Status = Not tested`).

---

## Phase 5: User Story 3 — Cross-spec overlaps and ownership gaps are explicit (P2)

**Goal**: Every observed overlap (spec 006 FR-024 / spec 008; spec 018 escalation timeout / spec 008; recovery across 001/018/011) carries explicit `supersedes` / `defers-to` / `authoritative for` rules in both directions.

**Independent Test**: `grep -rn "supersedes\|defers-to\|authoritative for" specs/*/spec.md` returns matching rules on both sides of every declared overlap; no overlap referenced in spec-028 FR-016..019 is silent.

- [ ] T044 [US3] Resolve the spec 006 FR-024 overlap: open `C:\code\ama\specs\006-data-ingestion-storage\spec.md`, either (A) relocate FR-024 content to spec 008, or (B) reframe FR-024 in spec 006 as a contract assumption with an explicit `defers-to: 008` pointer and a `supersedes: spec-006 FR-024` note in spec 008. Choose (B) by default to preserve FR-022 append-only. Add the reciprocal `supersedes` rule in `C:\code\ama\specs\008-communication-agent\spec.md`.
  - **Success criteria**: `grep "defers-to: 008" specs/006-data-ingestion-storage/spec.md` returns ≥1 match; `grep "supersedes: specs/006" specs/008-communication-agent/spec.md` returns ≥1 match; original FR-024 number retained (FR-022).
  - **Actors**: `api-architect`, `solution-architect`, `public-information-officer`, `data-engineer`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T045 [US3] Resolve the spec 018 escalation-timeout supersession of spec 008's warning-tier approval timeout. Edit `C:\code\ama\specs\008-communication-agent\spec.md` adding `defers-to: 018 (warning-tier approval timeout)`. Edit `C:\code\ama\specs\018-aidr-guidance-integration\spec.md` adding `authoritative for: warning-tier approval timeout across portfolio`. (T025 may have added the 018 side already — make this task idempotent.)
  - **Success criteria**: both sides present; IDs unchanged; `grep -c "defers-to: 018"` in 008 ≥ 1.
  - **Actors**: `incident-commander`, `public-information-officer`, `api-architect`.
  - **Tools**: `read`, `edit`, `agent`.

- [ ] T046 [US3] Resolve recovery-phase ownership across specs 001, 018, 011 per FR-018 / D-005. Verify that: `specs/001-disaster-response-hub/spec.md` DEF-015 has `defers-to: 018` (from T008); `specs/011-resource-allocation-agent/spec.md` recovery section has `defers-to: 018` (from T018); `specs/018-aidr-guidance-integration/spec.md` has `authoritative for: recovery-phase indicators, triggers, phase-exit criteria` (from T025). If any pointer missing, add it. Exactly one spec (018) must be authoritative.
  - **Success criteria**: `grep -c "authoritative for: recovery-phase" specs/018-*/spec.md` = 1; every other spec mentioning recovery has `defers-to: 018`.
  - **Actors**: `resilience-planner`, `incident-commander`, `logistics-officer`, `solution-architect`.
  - **Tools**: `read`, `edit`, `search`, `agent`.

**Checkpoint**: US3 complete → every overlap named in FR-016..019 has reciprocal pointers.

---

## Phase 6: User Story 4 — Meta / delivery-hygiene specs flagged as non-capstone-critical-path (P3)

**Goal**: All 11 meta specs (`003, 004, 007, 013, 016, 017, 024, 025, 026, 027, 028`) carry the verbatim meta-flag bullet from `contracts/meta-spec-flag.contract.md` inside their `## Out of Scope` section.

**Independent Test**: `grep -l "^- This spec is delivery-hygiene" specs/*/spec.md` returns exactly 11 files matching the meta set.

**Canonical bullet (verbatim template — per `contracts/meta-spec-flag.contract.md`)**:

```markdown
- This spec is delivery-hygiene / enabling infrastructure; capstone-outcome-critical-path ownership lives in specs [list].
```

Replace `[list]` with the subset of capstone-critical-path specs this spec enables (for general hygiene specs, `[list]` MAY be the literal string "all capstone-critical-path specs"). Every task T047..T057 below MUST satisfy the following per-task success criterion:

- **Success criteria (applies to every meta-flag task)**: after edit, `Select-String -Path <spec path> -Pattern "^- This spec is delivery-hygiene / enabling infrastructure; capstone-outcome-critical-path ownership lives in specs " -SimpleMatch | Measure-Object` returns exactly 1; the bullet appears inside an `## Out of Scope` section; the `[list]` placeholder has been substituted with a concrete list (no literal `[list]` remains).

- [ ] T047 [P] [US4] Add the meta-flag bullet to `C:\code\ama\specs\003-rubric-gap-closure\spec.md`.
  - **Actors**: `product-owner-ba`.
  - **Tools**: `read`, `edit`.
- [ ] T048 [P] [US4] Add the meta-flag bullet to `C:\code\ama\specs\004-actor-github-agents\spec.md`.
  - **Actors**: `product-owner-ba`.
  - **Tools**: `read`, `edit`.
- [ ] T049 [P] [US4] Add the meta-flag bullet to `C:\code\ama\specs\007-simulation-tenant-isolation\spec.md`.
  - **Actors**: `product-owner-ba`, `security-engineer`.
  - **Tools**: `read`, `edit`.
- [ ] T050 [P] [US4] Add the meta-flag bullet to `C:\code\ama\specs\013-root-readme\spec.md`.
  - **Actors**: `product-owner-ba`.
  - **Tools**: `read`, `edit`.
- [ ] T051 [P] [US4] Add the meta-flag bullet to `C:\code\ama\specs\016-automated-demo-script\spec.md`.
  - **Actors**: `product-owner-ba`, `qa-test-engineer`.
  - **Tools**: `read`, `edit`.
- [ ] T052 [P] [US4] Add the meta-flag bullet to `C:\code\ama\specs\017-cd-pipeline\spec.md`.
  - **Actors**: `infrastructure-devops`, `product-owner-ba`.
  - **Tools**: `read`, `edit`.
- [ ] T053 [P] [US4] Add the meta-flag bullet to `C:\code\ama\specs\024-simulation-control-chat\spec.md`.
  - **Actors**: `product-owner-ba`.
  - **Tools**: `read`, `edit`.
- [ ] T054 [P] [US4] Add the meta-flag bullet to `C:\code\ama\specs\025-agent-spec-compliance\spec.md`.
  - **Actors**: `qa-test-engineer`, `product-owner-ba`.
  - **Tools**: `read`, `edit`.
- [ ] T055 [P] [US4] Add the meta-flag bullet to `C:\code\ama\specs\026-sim-warp-playback\spec.md`.
  - **Actors**: `qa-test-engineer`, `ux-designer`.
  - **Tools**: `read`, `edit`.
- [ ] T056 [P] [US4] Add the meta-flag bullet to `C:\code\ama\specs\027-spec-hardening\spec.md`.
  - **Actors**: `product-owner-ba`.
  - **Tools**: `read`, `edit`.
- [ ] T057 [P] [US4] Add the meta-flag bullet to `C:\code\ama\specs\028-capstone-alignment\spec.md`. For this self-reference, the `[list]` is "all capstone-critical-path specs: 001, 005, 006, 008, 009, 010, 011, 012, 014, 015, 018, 019, 020, 021, 022, 023".
  - **Actors**: `product-owner-ba`.
  - **Tools**: `read`, `edit`.

**Checkpoint**: US4 complete → `grep -l "^- This spec is delivery-hygiene" specs/*/spec.md | Measure-Object` returns exactly 11.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Verify every SC and FR from spec 028 is satisfied, refresh shared artefacts, and lock in SC-009.

- [ ] T058 [P] Run the validator script `C:\code\ama\specs\028-capstone-alignment\scripts\validate-section-coverage.ps1` against the repo and store the CSV output in `C:\code\ama\specs\028-capstone-alignment\evidence\validator-run-post-feature.csv`. Assert: every non-meta spec row shows `True,True,True,True` for the four H2 columns; every row shows `NeedsClarificationCount = 0`.
  - **Success criteria**: CSV exists; zero rows with `NeedsClarificationCount > 0`; zero rows with any H2 column = `False`.
  - **Actors**: `qa-test-engineer`.
  - **Tools**: `execute`, `edit`.

- [ ] T059 [P] Grep the portfolio to prove every overlap rule exists on both sides: run `Select-String -Path specs\*\spec.md -Pattern "supersedes|defers-to|authoritative for"` and export to `C:\code\ama\specs\028-capstone-alignment\evidence\overlap-rules-audit.txt`. Cross-check against FR-016..019.
  - **Success criteria**: every overlap pair has at least two hits (one per spec side); audit file enumerates them with line numbers.
  - **Actors**: `product-owner-ba`, `solution-architect`.
  - **Tools**: `search`, `edit`.

- [ ] T060 Produce a monotonicity diff of `specs/shared/gap-id-register.md` by running `git --no-pager diff <pre-feature-sha> -- specs/shared/gap-id-register.md` and storing the result at `C:\code\ama\specs\028-capstone-alignment\evidence\gap-id-monotonic-diff.txt`. Verify: zero deletions (every hunk is `+` only); every new ID is strictly greater than the prior family max recorded in T003.
  - **Success criteria**: diff contains only `+` additions; highest new ID per family ≥ pre-feature max + 1; no existing ID removed or renumbered.
  - **Actors**: `product-owner-ba`.
  - **Tools**: `execute`, `edit`, `sql`.

- [ ] T061 Validate `specs/shared/capstone-metric-trace.md` structurally: row count = 20, `Status` column contains only values from `{Validated, Deferred}` (zero `Unresolved`), every `Validated` row's Owner cells match `^[0-9]{3}:(SC|HYP)-[0-9]{3}$`, every `Deferred` row's Owner cells begin `Deferred — preconditions: `. Follow every Validated Owner reference and confirm the cited ID exists in the referenced spec.
  - **Success criteria**: all five structural assertions pass; evidence saved at `C:\code\ama\specs\028-capstone-alignment\evidence\metric-trace-audit.md`.
  - **Actors**: `qa-test-engineer`, `product-owner-ba`.
  - **Tools**: `read`, `search`, `edit`.

- [ ] T062 Validate every `evidence/HYP-*.md` stub created in US2 against `contracts/evidence-stub.contract.md`: six H2 headings in order, `## Preconditions` ≥ 2 bullets, `## Falsification Criterion` ≥ 1 quantified threshold, `## Status` body = `Not tested`. Record per-stub pass/fail at `C:\code\ama\specs\028-capstone-alignment\evidence\stub-audit.md`.
  - **Success criteria**: ≥15 stubs audited; zero fails.
  - **Actors**: `qa-test-engineer`.
  - **Tools**: `read`, `search`, `edit`.

- [ ] T062a [P] Validate FR-023 (non-AU persona placeholder tagging). For every persona block authored or cross-referenced by this feature targeting a non-AU jurisdiction (PH, JP, BD, or any other non-AU node), grep-assert the persona carries `status: placeholder` in its front-matter (per `specs/027-spec-hardening/contracts/persona-profile.md` schema) **and** a non-empty `preconditions:` list (≥1 bullet). Fail if any non-AU persona is tagged `validated` or lacks preconditions. Persist per-persona pass/fail audit at `C:\code\ama\specs\028-capstone-alignment\evidence\persona-placeholder-audit.md`.
  - **Success criteria**: audit file exists; zero non-AU personas marked `status: validated`; every non-AU persona has `preconditions:` with ≥1 bullet; `grep -rn "status: validated" specs/*/spec.md | grep -Ei "philippines|japan|bangladesh|PH\b|JP\b|BD\b"` returns 0 matches.
  - **Actors**: `compliance-auditor`, `product-owner-ba`.
  - **Tools**: `search`, `read`, `edit`.

- [ ] T063 Capture the post-feature AMA rubric snapshot by re-invoking the `ama-rubric-grader` skill against `C:\code\ama\AMA_Rubric_Asia.md` with the now-hardened `specs/` tree. Persist at `C:\code\ama\specs\028-capstone-alignment\evidence\rubric-post-feature.md` with the same criterion layout as T002. Then compute the SC-009 composite gate: (i) Δmean across the 5 target criteria ≥ +1; (ii) per-criterion Δ ≥ 0. Record pass/fail per criterion in the same file.
  - **Success criteria**: post-feature file exists; gate table shows `Δmean` and per-criterion Δ; both SC-009 conditions hold (otherwise this task fails and the feature MUST iterate).
  - **Actors**: `product-owner-ba`, `solution-architect`.
  - **Tools**: `agent` (invoke `ama-rubric-grader`), `edit`.

- [ ] T063a [Post-merge, non-blocking] Schedule and run the SC-003 reviewer user test. Recruit ≥3 independent reviewers (preferably not the feature author); assign each reviewer ≥5 randomly-selected specs from `specs/NNN-*/` (excluding `specs/shared/` and `specs/feature/`); time each reviewer answering the five capstone-alignment questions per spec (assumptions / personas / hypotheses / out-of-scope / AU-vs-capstone scope) without external context. Persist timings and per-reviewer pass/fail at `C:\code\ama\specs\028-capstone-alignment\evidence\reviewer-timings.md` with columns `Reviewer | Spec | Minutes | Five-Qs-Answered? | Notes`. This task is **deferred-to-post-merge** (per clarification 2026-04-25) and does NOT block `/speckit.implement` or feature merge; it gates SC-003's Validated status only.
  - **Success criteria**: evidence file exists with ≥15 rows (3 reviewers × ≥5 specs); `Minutes ≤ 10` in ≥80% of rows; every row has `Five-Qs-Answered? = Yes` OR a recorded reason for No.
  - **Actors**: `product-owner-ba`, `qa-test-engineer`, plus ≥3 external reviewers (any combination of `solution-architect`, `principal-engineer`, `compliance-auditor`, `incident-commander`, `resilience-planner`, `risk-manager`, `ux-designer`).
  - **Tools**: `agent`, `execute`, `edit`.

- [ ] T064 [P] Consult `rubber-duck` for a final critique pass on the whole feature: provide it `spec.md`, `plan.md`, `research.md`, the validator outputs from T058..T063, and ask for blind-spot findings on (a) residual vague adjectives (FR-021/SC-004), (b) append-only violations (FR-022/SC-007), (c) reciprocal overlap-rule coverage (FR-016..019), (d) the AU-residency tension framing (D-009), (e) meta-spec list completeness (FR-020/SC-008), (f) capstone-country coverage in hypotheses (SC-005). Record findings and responses at `C:\code\ama\specs\028-capstone-alignment\evidence\rubber-duck-review.md`; adopt any finding that prevents bugs and note any set-aside finding with justification.
  - **Success criteria**: review file exists; every finding has a disposition (`adopted` / `set-aside with rationale`); no `adopted` finding is left unimplemented.
  - **Actors**: `rubber-duck` (sync task-tool agent).
  - **Tools**: `agent`.

- [ ] T065 Record a clarification-follow-up decision for `C:\code\ama\specs\028-capstone-alignment\spec.md`. **Always emit** an evidence file `C:\code\ama\specs\028-capstone-alignment\evidence\t065-decision.md` containing one of two verbatim decisions: (A) `Decision: no-op — T064 surfaced no new ambiguity that alters the feature.` with a bulleted list of the T064 findings considered; OR (B) `Decision: applied — T064 surfaced a new ambiguity.` with (i) the Q/A bullet appended to `spec.md` under a new `### Session <YYYY-MM-DD>` subheading of `## Clarifications`, (ii) the exact driving edit (diff hunk), (iii) justification. Do NOT retroactively rewrite existing `Clarifications` bullets for style.
  - **Success criteria**: `Test-Path specs/028-capstone-alignment/evidence/t065-decision.md` = True; file's first non-blank line begins with `Decision: no-op` or `Decision: applied`; if `applied`, `git log -- specs/028-capstone-alignment/spec.md` shows exactly one new commit since T064, and that commit touches only the `## Clarifications` section.
  - **Actors**: `product-owner-ba`.
  - **Tools**: `read`, `edit`, `execute`.

- [ ] T066 Run `/speckit.analyze` against `specs/028-capstone-alignment/` (the `speckit.analyze` agent) for cross-artefact consistency across `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `contracts/`, and the shared artefacts edited by this feature. Capture output to `C:\code\ama\specs\028-capstone-alignment\evidence\speckit-analyze-report.md`. Resolve any inconsistency flagged (typically small drift between `tasks.md` Success Criteria and `spec.md` SCs).
  - **Success criteria**: analyze report produced; zero `HIGH` or `CRITICAL` findings open; all `LOW`/`MEDIUM` findings triaged with disposition.
  - **Actors**: `speckit.analyze`.
  - **Tools**: `agent`, `edit`.

**Checkpoint**: Feature 028 complete and provably aligned to the capstone brief. All nine SCs in `spec.md` are grep-verifiable. `quickstart.md` walkthrough produces green across the board.

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 Setup** — start immediately.
- **Phase 2 Foundational** — depends on Phase 1 (needs inventory, rubric baseline, ID watermarks).
- **Phase 3–6 User Stories** — depend on Phase 2. US1 (Phase 3) is the MVP; US2–US4 can run in parallel with US1 once Phase 2 closes, but the MVP checkpoint recommends completing Phase 3 first for an early deploy/demo.
- **Phase 7 Polish** — depends on every in-scope user-story phase being complete.

### User-story dependencies

- **US1 (P1)** — no dependency on other stories; produces the MVP.
- **US2 (P1)** — independent of US1 content-wise, but T034..T038 *touch* the same spec files that US1 tasks T015..T019 edit. Sequence rule: for any given agent spec (008/009/010/011/012), complete the US1 task before the US2 task on that file.
- **US3 (P2)** — independent of US2. T044..T046 may race with US1 tasks on specs 006/008/011/018/001; sequence rule: complete the US1 task on each affected spec before the US3 task on that spec.
- **US4 (P3)** — may run in parallel with US1..US3 for the 11 meta specs; sequence rule: for each meta spec, complete its US1 task before adding the meta-flag bullet.

### Within each user story

- Models / sections (e.g., `## Assumptions`) are added before contract-level additions (e.g., FR-006 language-pack plugin) in the same file.
- Shared-artefact tasks (T004, T005, T039..T043) must see their producers complete before the artefact is populated.
- Cross-references precede the pointer rules: add sections first (US1), then add `defers-to` / `supersedes` rules (US3).

### Parallel opportunities

- Setup: T002 ∥ T003.
- Foundational: T006 ∥ T007.
- US1 per-spec hardening: T010..T033 are 24 independent file edits (after T008 + T009).
- US2 HYP authoring: T034..T038 independent (different agent spec files).
- US2 metric-trace rows: T039..T043 independent (different row groups in one file — use `edit` on non-overlapping rows; sequence if needed).
- US4 meta-flag: T047..T057 are 11 independent bullet insertions.
- Polish: T058 ∥ T059 ∥ T062 ∥ T064.

---

## Parallel example — US1 per-spec hardening (after T008, T009)

Launch the 24 independent spec-edit tasks in parallel:

```text
T010  specs/003-rubric-gap-closure/spec.md
T011  specs/004-actor-github-agents/spec.md
T012  specs/005-data-source-governance/spec.md
T013  specs/006-data-ingestion-storage/spec.md
T014  specs/007-simulation-tenant-isolation/spec.md
T015  specs/008-communication-agent/spec.md
T016  specs/009-evacuation-agent/spec.md
T017  specs/010-monitoring-agent/spec.md
T018  specs/011-resource-allocation-agent/spec.md
T019  specs/012-risk-assessment-agent/spec.md
T020  specs/013-root-readme/spec.md
T021  specs/014-azure-openai-integration/spec.md
T022  specs/015-performance-benchmarks/spec.md
T023  specs/016-automated-demo-script/spec.md
T024  specs/017-cd-pipeline/spec.md
T025  specs/018-aidr-guidance-integration/spec.md
T026  specs/019-aidr-additional-guidances/spec.md
T027  specs/020-disaster-mapper-ui/spec.md
T028  specs/021-governance-dashboard/spec.md
T029  specs/022-multi-jurisdiction-filter/spec.md
T030  specs/023-dashboard-real-data/spec.md
T031  specs/024-simulation-control-chat/spec.md
T032  specs/025-agent-spec-compliance/spec.md
T033  specs/026-sim-warp-playback/spec.md
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1: Setup (T001–T003).
2. Complete Phase 2: Foundational (T004–T007).
3. Complete Phase 3: US1 (T008, T009, then parallel T010–T033).
4. **STOP and VALIDATE**: run T058 early. If every row reports `True,True,True,True` and zero `NEEDS CLARIFICATION`, MVP is shippable.
5. Open PR for US1-only scope; merge after ≥1 reviewer approval (constitution §Governance).

### Incremental delivery

1. Setup + Foundational → foundation ready.
2. Add US1 → validator T058 passes → PR / merge → **MVP shipped**.
3. Add US2 → metric-trace populated, HYP evidence stubs land → PR / merge.
4. Add US3 → overlap rules reciprocal → PR / merge.
5. Add US4 → meta-flag bullets land → PR / merge.
6. Polish → T058..T066 close the feature; T063 (post-rubric snapshot) gates SC-009.

### Parallel team strategy

With multiple contributors:

1. Contributor A (spec-domain-lead + `product-owner-ba`): Phase 1, Phase 2, then T008–T009.
2. Contributor B (ops-SME + `incident-commander` / `planning-officer`): US1 operational agent specs (008..012) and US2 hypotheses.
3. Contributor C (infra-SME + `infrastructure-devops` / `security-engineer` / `compliance-auditor`): specs 005, 014, 017 and the AU-residency `[RISK]` propagation.
4. Contributor D (UX-SME + `ux-designer` / `accessibility-tester`): specs 020..023.
5. All converge on Phase 7 polish.

---

## Notes

- **[P]** tasks edit different files; they are parallel-safe. Non-[P] tasks either touch a shared file or must see a prior task's output first.
- Every task includes absolute Windows paths (FR-022 append-only; no path ambiguity).
- No test tasks are generated — this is a documentation-only feature per `plan.md` D-001. Validation is grep/regex via `quickstart.md` and T058..T063.
- ID allocation is driven by the SQL `id_watermarks` table created in T003; every task that allocates IDs MUST `UPDATE id_watermarks SET current_max = current_max + <n>` after claiming IDs. This guarantees FR-022 monotonicity across parallel contributors.
- The `[RISK]` assumption for the AU-only-residency vs capstone-sovereign-data tension (D-009) is explicitly REQUIRED to be added in T012 (spec 005 data governance/PII), T013 (spec 006 ingestion/feeds), T017 (spec 010 monitoring/feeds carrying geolocation PII), T021 (spec 014 Azure OpenAI/LLM traffic), T024 (spec 017 CD pipeline/region topology) — every spec that reads, stores, displays, or moves PII/persona/location data — not an optional extra. T014 (spec 007 simulation tenant isolation) SHOULD add it iff the simulated data includes PII; otherwise may omit.
- Commit after each task or tight logical group (US1 per-spec = one commit per spec acceptable).
- When in doubt, consult `rubber-duck` (T064 invokes it explicitly); `product-owner-ba` owns the speckit taxonomy disputes.
