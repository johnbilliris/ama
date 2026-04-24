# Tasks: Capstone Specification Hardening

**Feature**: 027-spec-hardening
**Branch**: `027-spec-hardening`
**Input**: Design documents from `specs/027-spec-hardening/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Not applicable in the traditional runtime sense — this is a documentation-hardening feature. "Tests" here are markdown-lint + a PowerShell verification script that checks the markdown-level invariants from `data-model.md`. They are included because the feature's Success Criteria (SC-002, SC-005, SC-008, SC-009) are only testable by such a script.

**Organization**: Tasks are grouped by user story (US1, US2, US3 from `spec.md`). Each task names (a) the actor-specific agent(s) that must participate, (b) the tool set used to execute it, chosen from `execute`, `read`, `edit`, `search`, `web`, `agent`, `todo`, and (c) verifiable success criteria.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on other in-flight tasks).
- **[Story]**: Story label for traceability (US1 / US2 / US3).
- Every task names a file path.

## Legend

**Agents** reference the actor catalogue at `.github/agents/AGENTS.md`. **Tools** are drawn from `{execute, read, edit, search, web, agent, todo}`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare on-disk scaffolding so every subsequent task edits an existing file.

- [x] T001 Create the directory scaffolding for this feature's side-effect artefacts: `specs/shared/`, `specs/001-disaster-response-hub/evidence/`, and (if missing) `.github/`.
  - **Agent(s)**: `infrastructure-devops` (scaffolding owner), `product-owner-ba` (artefact-layout reviewer).
  - **Tools**: `execute`, `read`.
  - **Success**: Running `Get-ChildItem specs/shared, specs/001-disaster-response-hub/evidence, .github -Directory` returns three existing directories with exit code 0. No files are created yet.

- [x] T002 [P] Verify the repo's `markdownlint-cli2` configuration covers the paths this feature will touch; add entries to `.markdownlint.jsonc` if needed so table rows longer than 120 chars are permitted under `specs/` and `.github/CODEOWNERS` is excluded.
  - **Agent(s)**: `software-developer`, `principal-engineer` (reviewer).
  - **Tools**: `read`, `edit`, `execute`.
  - **Success**: `pnpm exec markdownlint-cli2 "specs/027-spec-hardening/**/*.md"` exits 0 on the files authored by Phase 0/1. No markdown rules are disabled globally.

- [x] T003 [P] Reserve the path `scripts/verify-spec-hardening.ps1` with a stub that prints `"not implemented"` and exits 0, so later tasks can wire it into CI without a chicken-and-egg failure.
  - **Agent(s)**: `software-developer`.
  - **Tools**: `edit`, `execute`.
  - **Success**: `pwsh -File scripts/verify-spec-hardening.ps1` exits 0 and prints exactly `not implemented`. File is under version control.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Seed the shared governance artefacts that every user story writes into. No user-story task may begin until this phase is green.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T004 Seed `specs/shared/gap-id-register.md` with a header + empty table that matches the column order in `specs/027-spec-hardening/contracts/gap-id-register-row.md`, then append one row per gap currently cited in `specs/027-spec-hardening/spec.md` (A-GAP-001..008, REQ-GAP-001..010, PER-GAP-001..007, HYP-GAP-001..006, SCP-GAP-001..009) with `status = Open` and `owning_feature = 001-disaster-response-hub`.
  - **Agent(s)**: `product-owner-ba` (owner), `observer-auditor` (register-integrity reviewer).
  - **Tools**: `read`, `edit`, `search`.
  - **Success**: File exists. Row count equals 40 (8 + 10 + 7 + 6 + 9). Every cited gap ID resolves to a row. `grep -oE '(A|REQ|PER|HYP|SCP)-GAP-[0-9]{3}' specs/027-spec-hardening/spec.md | sort -u | wc -l` equals the register row count.

- [x] T005 Create or amend `.github/CODEOWNERS` to add the line `specs/001-disaster-response-hub/ @johnbilliris/ama-spec-maintainers` per the template in `specs/027-spec-hardening/contracts/codeowners-entry.md`. If the team `@johnbilliris/ama-spec-maintainers` does not exist on GitHub, request creation with ≥ 2 members. If creation is declined or delayed, log an Open Delta row (`target_feature = 028-holistic-spec-hardening`, `blocking_phase = plan`) and nominate a named interim maintainer (individual GitHub handle) on the CODEOWNERS line so Phase 3+ can still proceed.
  - **Agent(s)**: `infrastructure-devops` (CODEOWNERS author), `security-engineer` (dual-control reviewer), `compliance-auditor` (audit trail reviewer).
  - **Tools**: `edit`, `web` (verify team exists via `gh api /orgs/johnbilliris/teams/ama-spec-maintainers`), `execute`.
  - **Success**: `.github/CODEOWNERS` contains an effective owner entry for `specs/001-disaster-response-hub/` (either the team or a named interim). `gh api /orgs/johnbilliris/teams/ama-spec-maintainers/members` returns ≥ 2 members OR an Open Delta row has been logged and the interim owner is named on the CODEOWNERS line.

- [x] T006 Add a `## Status-transition authority` subsection to `specs/001-disaster-response-hub/spec.md` that states the dual-control matrix from FR-034 (assumption owner + planner/privacy-reviewer countersign; test lead + planner countersign for hypotheses; UX lead + jurisdiction SME countersign for personas) and cites the CODEOWNERS entry created in T005 as the maintainer mechanism.
  - **Agent(s)**: `product-owner-ba`, `security-engineer` (countersign policy), `compliance-auditor` (audit-trail language).
  - **Tools**: `read`, `edit`.
  - **Success**: `specs/001-disaster-response-hub/spec.md` contains a `## Status-transition authority` section whose content resolves every row of the FR-034 matrix and names `.github/CODEOWNERS` explicitly.

- [x] T007 [P] Add a `## Changelog` section (or append to an existing one) at the bottom of `specs/001-disaster-response-hub/spec.md` with a "Last reviewed" line dated today and a pointer row to the 027 Traceability Table in the form specified by `research.md` R-4. Do NOT duplicate the table.
  - **Agent(s)**: `product-owner-ba`.
  - **Tools**: `edit`.
  - **Success**: Section exists with a row whose target anchor resolves to `specs/027-spec-hardening/spec.md#traceability-table`. No table rows are copied from 027.

- [x] T008 [P] Add an `## Open Deltas` subsection placeholder to `specs/001-disaster-response-hub/spec.md` with the header row from `specs/027-spec-hardening/contracts/open-delta-row.md`. Body may be empty; later tasks add rows as contradictions are detected.
  - **Agent(s)**: `product-owner-ba`, `solution-architect`.
  - **Tools**: `edit`.
  - **Success**: Section exists with the exact column order from the contract template. Markdown-lint passes.

- [x] T009 [P] Add placeholder empty tables for `## Assumptions`, `## Non-Functional Requirements`, `## Personas`, `## Hypotheses`, and the six required Scope subsections (`### v1 Primary Jurisdiction`, `### Deferred-Scope Register`, `### Hazard List`, `### Autonomy Boundary Table`, `### Citizen-Surface List`, `### Upstream/Downstream Integrations`) to `specs/001-disaster-response-hub/spec.md`, using the column orders from the corresponding contract templates under `specs/027-spec-hardening/contracts/`.
  - **Agent(s)**: `product-owner-ba`, `solution-architect`.
  - **Tools**: `read`, `edit`.
  - **Success**: All listed headers exist with empty tables whose headers match the contract templates exactly. `markdownlint-cli2` passes.

**Checkpoint**: Foundation ready — user-story work can begin.

---

## Phase 3: User Story 1 — Capstone alignment is unambiguous to a new reviewer (Priority: P1) 🎯 MVP

**Goal**: A reviewer who has read only `capstone.md` can, after one pass of spec 001, correctly answer the four questions from US1 (v1 jurisdiction, rationale, un-validated Asia claims, extension preconditions).

**Independent Test**: Give the hardened spec to a reviewer who has not seen the Asia-Pacific annex; confirm by structured read-through that they answer the four questions without consulting any other document (quickstart step 1 + step 5).

### Implementation for User Story 1

- [x] T010 [US1] Author the `### v1 Primary Jurisdiction` subsection under `## Scope` in `specs/001-disaster-response-hub/spec.md`: name Australia, dated rationale (with citations to AIIMS, AIDR, BoM), and the preconditions under which a second jurisdiction may be promoted (FR-022). Create `SCP-###` boundary rows as needed.
  - **Agent(s)**: `product-owner-ba` (drafter), `solution-architect` (rationale review), `resilience-planner` (jurisdictional-fit SME), `incident-commander` (operational-fit SME).
  - **Tools**: `read`, `edit`, `agent` (solicit rationale inputs from resilience-planner and incident-commander).
  - **Success**: Subsection names exactly one Australian state/territory, dated ≤ 7 days ago, with ≥ 2 citations, and ≥ 3 named preconditions. `A-GAP-003` (or whichever gap covers v1 jurisdiction) is marked `In-progress` in `specs/shared/gap-id-register.md`.

- [x] T011 [US1] Author the `### Deferred-Scope Register` subsection rows for Philippines, Japan, and Bangladesh per FR-023, citing the existing extensibility evidence in `docs/disaster-response-hub/regional-adaptation-asia-pacific.md` and naming the `target_feature` as `unassigned` pending the next planning cycle. Also seed Deferred-Scope rows for every Principle III hazard not promoted into v1 (earthquake, tsunami, extreme heat, pandemic/biosecurity, CBRN, space weather, cyber-physical infrastructure attack) per FR-024 — reason, extensibility evidence (or `"none"`), and promotion preconditions.
  - **Agent(s)**: `product-owner-ba`, `resilience-planner` (jurisdictional review), `risk-manager` (hazard rationale), `compliance-auditor` (validation step definition).
  - **Tools**: `search` (grep for existing Asia seed content), `read`, `edit`, `agent`.
  - **Success**: Three jurisdiction `DEF-###` rows + seven hazard `DEF-###` rows exist (total ≥ 10), each with `reason_deferred`, `target_feature` (may be `unassigned`), and `re_evaluation_trigger` filled. Each jurisdiction row references at least one existing repo artefact as extensibility evidence. No Principle III hazard named in the constitution is absent from the register unless already listed in the In-Scope Hazard List.

- [x] T012 [US1] Seed the Assumptions table in `specs/001-disaster-response-hub/spec.md` with `ASM-001` stating that Australia is the v1 primary jurisdiction and Asia-region claims are deferred, citing the capstone-vs-solution divergence per FR-003, using the template at `specs/027-spec-hardening/contracts/assumption-row.md`.
  - **Agent(s)**: `product-owner-ba` (drafter), `solution-architect` (countersigner).
  - **Tools**: `read`, `edit`.
  - **Success**: Row validates against all rules in `contracts/assumption-row.md`; `drafter` and `countersigner` are non-empty; `A-GAP-003` register row is `Resolved` with `evidence_link` pointing at the new ASM anchor.

- [x] T013 [US1] Re-characterise any sentence in `specs/001-disaster-response-hub/spec.md` that treats the Asia-Pacific annex's "no code changes needed" claim as an architectural guarantee. Replace it with an explicit reference to the placeholder hypothesis id `HYP-006` (cross-jurisdictional framework portability). The `HYP-006` row and its evidence stub are authored in the **same commit** by T013b below, so no Open Delta is needed and invariant (b) is never in a failing state on disk.
  - **Agent(s)**: `product-owner-ba`, `principal-engineer` (language review), `solution-architect` (architectural-claim reviewer).
  - **Tools**: `search` (`grep -n "no code changes" specs/001-disaster-response-hub/spec.md`), `edit`.
  - **Success**: `grep` for "no code changes" returns either zero hits OR only hits inside fenced code blocks / quoted text. Every remaining mention of framework portability is adjacent to a `HYP-006` citation. No Open Delta is logged (citation is resolved in the same commit by T013b).

- [x] T013b [US1] In the **same commit** as T013, author the `HYP-006` (cross-jurisdictional framework portability to NDRRMC / Japan / Bangladesh) row in `specs/001-disaster-response-hub/spec.md § Hypotheses` using the template at `specs/027-spec-hardening/contracts/hypothesis-row.md`, and create `specs/001-disaster-response-hub/evidence/HYP-006.md` using the template at `specs/027-spec-hardening/contracts/evidence-pack-stub.md` (front-matter `status: Not tested`, single `## History` stub row). This keeps US1 fully self-contained — T042/T043 in Phase 5 author only HYP-001..005.
  - **Agent(s)**: `product-owner-ba`, `qa-test-engineer`, `public-information-officer`, `resilience-planner`, `solution-architect`, `observer-auditor`.
  - **Tools**: `read`, `edit`, `agent`, `execute`.
  - **Success**: `HYP-006` row exists in spec 001 § Hypotheses and conforms to the *"We believe X will produce Y for Z; wrong if W observed in window T"* form. `specs/001-disaster-response-hub/evidence/HYP-006.md` exists with matching `status`. Every `HYP-006` citation inserted by T013 resolves to a live anchor. `scripts/verify-spec-hardening.ps1` invariants (a) and (b) pass in the T013+T013b commit.

- [x] T014 [P] [US1] Scope every numeric success criterion in `specs/001-disaster-response-hub/spec.md § Success Criteria` to "the v1 Australian evaluation cohort" so Asia-wide claims are not implied (Acceptance Scenario 2).
  - **Agent(s)**: `product-owner-ba`, `qa-test-engineer` (evaluation-cohort wording), `observer-auditor`.
  - **Tools**: `read`, `edit`.
  - **Success**: Every SC in spec 001 carries an explicit cohort scope. A grep for SC identifiers without the word "Australian" or "v1" returns zero matches OR each such match is deliberate and commented.

- [x] T015 [US1] Append Traceability Table rows in `specs/027-spec-hardening/spec.md` for every gap resolved by T010–T014 (expected: A-GAP-002, A-GAP-003, SCP-GAP-001, SCP-GAP-002). Update matching rows in `specs/shared/gap-id-register.md` to `Resolved`.
  - **Agent(s)**: `product-owner-ba`, `observer-auditor` (register-integrity check).
  - **Tools**: `read`, `edit`.
  - **Success**: Traceability Table row count matches `In-progress`+`Resolved` count in the gap register. Every `Resolved` register row has non-empty `evidence_link`.

**Checkpoint**: SC-001 is testable — run Quickstart step 1 and step 5.

---

## Phase 4: User Story 2 — Planner, tester, legal reviewer, UX evaluator can proceed without clarifications (Priority: P1)

**Goal**: Each of the four downstream roles derives their first artefact (plan, test matrix, DPIA outline, evaluation protocol) from the hardened spec without raising a blocking clarification request in REQ-GAP / PER-GAP / SCP-GAP territory.

**Independent Test**: Per-role structured review against `specs/027-spec-hardening/checklists/requirements.md`; no role records a blocking item (quickstart steps 2, 3, 5).

### Implementation for User Story 2 — Assumptions hardening

- [x] T016 [P] [US2] Author Assumption rows `ASM-002` through `ASM-008` in `specs/001-disaster-response-hub/spec.md § Assumptions` covering: Asia-region data availability and quality, minimum connectivity floor, AI/agent quality floor, data residency and sovereignty, baseline-exercise availability, legal standing of AI-generated recommendations, target user device profiles (FR-002).
  - **Agent(s)**: `product-owner-ba`, `ai-ml-engineer` (quality-floor basis), `compliance-auditor` (legal standing), `data-engineer` (data residency), `ux-designer` (device profiles), `field-coordinator` (connectivity floor).
  - **Tools**: `read`, `edit`, `agent` (solicit numeric floors from each named agent), `web` (check AIDR / OAIC guidance).
  - **Success**: Seven new ASM rows present. Each row names its SME source. Matching `A-GAP-###` register rows transition to `Resolved`.

### Implementation for User Story 2 — NFR hardening

- [x] T017 [P] [US2] Draft and countersign the Accessibility NFR row (WCAG 2.2 AA on operator dashboard, public web dashboard, and public alerts) per FR-005 + FR-035, using the template at `specs/027-spec-hardening/contracts/nfr-row.md`.
  - **Agent(s)**: `accessibility-tester` (drafter), `ux-designer` (SME countersign), `public-information-officer` (public-alert surface validator).
  - **Tools**: `read`, `edit`, `agent`, `web` (WCAG 2.2 AA criteria reference).
  - **Success**: Row passes the three NFR validation rules; `standard_reference = "WCAG 2.2 AA"`; `measurement_method` names a production-observable mechanism.

- [x] T018 [P] [US2] Draft the Privacy NFR cluster (PII classification, retention, right-to-erasure, in-region storage, cross-border transfer) per FR-006 + FR-035. Privacy reviewer countersign required.
  - **Agent(s)**: `compliance-auditor` (drafter), `security-engineer` (SME countersign), `data-engineer` (retention implementation check).
  - **Tools**: `read`, `edit`, `agent`, `web` (Privacy Act 1988 citations; OAIC APPs).
  - **Success**: Each row has `privacy_reviewer ≠ "N/A"`. Retention periods cite a statutory basis. Cross-border transfer row names APP 8 or an equivalent legal reference.

- [x] T019 [P] [US2] Draft the Security NFR cluster (AuthN strength with MFA, session management, key management, threat-model coverage: adversarial signal injection, coordinated misinformation, insider misuse, credential compromise) per FR-007 + FR-035.
  - **Agent(s)**: `security-engineer` (drafter), `sre-engineer` (SME countersign), `compliance-auditor` (privacy reviewer for identity/session).
  - **Tools**: `read`, `edit`, `agent`.
  - **Success**: Threat-model row enumerates all four named threats. Auth-strength row names an MFA standard.

- [x] T020 [P] [US2] Promote the Performance/Freshness NFRs currently embedded in `specs/001-disaster-response-hub/plan.md` (dashboard initial load, read-API p95, authoritative-hazard freshness) into `specs/001-disaster-response-hub/spec.md § NFRs` per FR-008 + FR-035. Leave the plan's values intact; add a pointer comment noting the spec is now authoritative.
  - **Agent(s)**: `sre-engineer` (drafter), `solution-architect` (SME countersign), `qa-test-engineer` (measurement-method review).
  - **Tools**: `read`, `edit`.
  - **Success**: Every performance target in `plan.md` is mirrored in `spec.md § NFRs` with identical numeric values. Plan carries a comment `<!-- NFR source moved to spec.md § NFRs -->` adjacent to each moved value.

- [x] T021 [P] [US2] Draft the Interoperability NFR cluster naming CAP 1.2 (public alerts), EDXL-DE (inter-agency exchange), and Sendai Framework indicators (M&E) per FR-009 + FR-035.
  - **Agent(s)**: `api-architect` (drafter), `solution-architect` (SME countersign), `nema` (Commonwealth coordination reviewer), `public-information-officer` (CAP surface validator).
  - **Tools**: `read`, `edit`, `agent`, `web` (OASIS CAP 1.2 and EDXL-DE 2.0 spec citations).
  - **Success**: Three rows present; each carries a non-empty `standard_reference`; each names a contract test or compliance mechanism.

- [x] T022 [P] [US2] Draft the Training & Change-Management NFR for SC-003 unassisted task completion per FR-010.
  - **Agent(s)**: `ux-designer` (drafter), `resilience-planner` (onboarding-target SME), `qa-test-engineer` (measurement).
  - **Tools**: `read`, `edit`, `agent`.
  - **Success**: NFR row names a numeric onboarding target (e.g. "≤ 30 min to first coordinated action") and cites the rehearsal basis.

- [x] T023 [P] [US2] Draft the Audit-Retention NFR covering retention duration, format, and recoverability SLO per FR-013 + FR-035.
  - **Agent(s)**: `observer-auditor` (drafter), `security-engineer` (SME countersign), `compliance-auditor` (privacy reviewer).
  - **Tools**: `read`, `edit`, `web` (AGRKMS / VERS retention guidance).
  - **Success**: Row states retention duration (years), immutable format, and recoverability SLO with a measurement mechanism.

- [x] T024 [US2] Author functional requirements or explicit out-of-scope declarations for medical triage, shelter allocation, utility isolation, and SAR tasking per FR-011. For every "out of scope" declaration, add a `DEF-###` row to the Deferred-Scope Register.
  - **Agent(s)**: `product-owner-ba`, `incident-commander`, `operations-officer`, `logistics-officer`, `health` (cross-sector), `utility` (cross-sector).
  - **Tools**: `read`, `edit`, `agent` (all six named agents must contribute scope statements).
  - **Success**: Each of the four capability areas is either (a) addressed by a specific FR in spec 001 with a named SME author or (b) listed as out-of-scope with `DEF-###` + rationale.

- [x] T025 [US2] Author the misinformation FR per FR-012, or declare it out of scope with rationale; if in scope, name the operator-visible evidence surface.
  - **Agent(s)**: `public-information-officer` (drafter), `ai-ml-engineer` (detection mechanism), `security-engineer` (threat-model link).
  - **Tools**: `read`, `edit`, `agent`.
  - **Success**: Either a FR exists naming detection method + evidence surface, or a Deferred-Scope row exists with rationale.

### Implementation for User Story 2 — Persona hardening

- [x] T026 [P] [US2] For each AIIMS operational role (Incident Controller, Operations Officer, Logistics Lead, PIO, Field Coordinator, Resilience Planner, Auditor) author a persona profile per `specs/027-spec-hardening/contracts/persona-profile.md`, validated for Australia (v1-primary) with SME countersign by the corresponding actor agent.
  - **Agent(s)**: `product-owner-ba` (drafter), `incident-commander`, `operations-officer`, `logistics-officer`, `public-information-officer`, `field-coordinator`, `resilience-planner`, `observer-auditor` (each countersigns their own persona).
  - **Tools**: `read`, `edit`, `agent` (solicit authority-scope and top-3 tasks from each operational agent).
  - **Success**: Seven persona files / blocks exist. Each has ≥ 1 `validated_by` entry with `role ∈ {SME, practitioner, documented-named-proxy}` per FR-016; proxy entries MUST additionally carry a non-empty `proxy_basis` field (e.g., "AIDR-accredited trainer", "published AIIMS course facilitator"). Each persona names one AIIMS function from the persona-profile enum.

- [x] T027 [P] [US2] Author executive persona profiles for Minister/Premier-equivalent and Mayor/local-government-equivalent per FR-015(b), validated by an executive-leader SME.
  - **Agent(s)**: `product-owner-ba`, `executive-leader`, `state-government` (cross-sector), `local-government` (cross-sector).
  - **Tools**: `read`, `edit`, `agent`.
  - **Success**: Two persona profiles exist, each with executive authority scope, `aiims_function = Non-AIIMS-Governance` (per the persona-profile contract enum), and a named SME validator.

- [x] T028 [P] [US2] Author affected-community persona profiles: native-language speaker, limited-literacy resident, low-vision resident, hard-of-hearing resident, tourist/non-resident per FR-015(c).
  - **Agent(s)**: `ux-designer`, `accessibility-tester`, `community-ngos` (cross-sector), `arc` (Australian Red Cross).
  - **Tools**: `read`, `edit`, `agent`, `web` (CALD guidance from SBS / DSS).
  - **Success**: Five persona profiles exist; accessibility-impaired archetypes carry specific assistive-technology fields.

- [x] T029 [P] [US2] Author adversarial persona profiles: misinformation actor, insider threat per FR-015(d).
  - **Agent(s)**: `security-engineer`, `chaos-engineer`, `afp` (Australian Federal Police).
  - **Tools**: `read`, `edit`, `agent`.
  - **Success**: Two adversarial persona profiles exist; each names the FR that mitigates the threat (link to T019 or T025 output).

- [x] T030 [P] [US2] Author accessibility-specific operator persona profiles: low-vision operator, hard-of-hearing field worker per FR-015(e).
  - **Agent(s)**: `accessibility-tester`, `ux-designer`, `field-coordinator`.
  - **Tools**: `read`, `edit`, `agent`.
  - **Success**: Two operator-accessibility persona profiles exist with WCAG-aligned accommodation notes.

- [x] T031 [US2] Update Success Criterion SC-003 in `specs/001-disaster-response-hub/spec.md` to reference the validated v1 persona set by name per FR-017.
  - **Agent(s)**: `product-owner-ba`, `qa-test-engineer`.
  - **Tools**: `read`, `edit`.
  - **Success**: SC-003 names at least the seven operational personas and carries an explicit unassisted-task-completion definition testable by inspection.

### Implementation for User Story 2 — Scope hardening

- [x] T032 [P] [US2] Populate `### Hazard List` in spec 001 § Scope with rows for bushfire, flood, cyclone, severe storm (in-scope with AIDR handbook links) AND explicit out-of-scope rows for every Principle III hazard not promoted into v1: earthquake, tsunami, extreme heat, pandemic/biosecurity, CBRN, space weather, cyber-physical infrastructure attack — each with rationale. Every out-of-scope hazard MUST also appear in the Deferred-Scope Register (T011/T024 may need to add the rows) so FR-024's "silent exclusion is forbidden" invariant holds.
  - **Agent(s)**: `resilience-planner`, `incident-commander`, `risk-manager`, `bom-national`, `ga-national`.
  - **Tools**: `read`, `edit`, `agent`, `web` (AIDR handbook citations).
  - **Success**: Eleven hazard rows present (4 in-scope + 7 out-of-scope); every in-scope hazard carries an AIDR reference URL; every out-of-scope hazard has a matching row in the Deferred-Scope Register. `verify-spec-hardening.ps1` invariant (d) passes.

- [x] T033 [P] [US2] Populate `### Autonomy Boundary Table` in spec 001 § Scope classifying every category in FR-025 — public alert publication, evacuation routing, resource pre-positioning, SMS/voice alert drafting, recommendation re-prioritisation, field-task assignment, de-escalation/closure — into one of {advisory-only, human-approved (HITL), auto-executable with operator override window}.
  - **Agent(s)**: `security-engineer` (drafter), `incident-commander` (SME countersign), `public-information-officer` (alert categories), `operations-officer` (tasking categories), `ai-ml-engineer` (autonomy-class feasibility).
  - **Tools**: `read`, `edit`, `agent`.
  - **Success**: Seven rows exist; 100% classified. Public-alert row is `human-approved`; evacuation-routing row is `human-approved` (constitution Non-Negotiable #1).

- [x] T034 [P] [US2] Enumerate in-scope community-signal/social-media sources for v1 per FR-026 with platform, licensing basis, moderation obligation. List exclusions.
  - **Agent(s)**: `data-engineer`, `compliance-auditor`, `public-information-officer`, `security-engineer`.
  - **Tools**: `read`, `edit`, `agent`, `web` (platform ToS).
  - **Success**: Each in-scope row names a licensing instrument; out-of-scope list is non-empty.

- [x] T035 [P] [US2] State the Recovery (PPRR) stance per FR-027: if out of scope, describe the hand-off contract; if in scope, list the recovery surfaces.
  - **Agent(s)**: `resilience-planner`, `arc`, `local-government`.
  - **Tools**: `read`, `edit`, `agent`.
  - **Success**: `### Recovery` subsection exists with an explicit binary stance and the corresponding detail (hand-off contract or surface list).

- [x] T036 [P] [US2] Populate `### Citizen-Surface List` per FR-028 classifying each of public web dashboard, push-notification mobile app, two-way SMS, voice IVR as in- or out-of-scope.
  - **Agent(s)**: `ux-designer`, `public-information-officer`, `accessibility-tester`.
  - **Tools**: `read`, `edit`, `agent`.
  - **Success**: Four rows present. Each out-of-scope row has a rationale ≥ 1 sentence.

- [x] T037 [P] [US2] Populate `### Upstream/Downstream Integrations` per FR-029: CAD, EOC, GIS/mapping, utilities SCADA, telco cell-broadcast, meteorology authority feed, etc.
  - **Agent(s)**: `api-architect`, `solution-architect`, `bom-national`, `transport` (cross-sector), `utility` (cross-sector).
  - **Tools**: `read`, `edit`, `agent`.
  - **Success**: Each row names direction (up/down), protocol/standard, and owning agent handle.

- [x] T038 [US2] State the rehearsal/simulation content boundary per FR-030 (shipped with v1 / imported / user-authored) in `### Rehearsal Content Boundary`.
  - **Agent(s)**: `qa-test-engineer`, `resilience-planner`.
  - **Tools**: `read`, `edit`, `agent`.
  - **Success**: Subsection exists and fixes exactly one boundary value.

- [x] T039 [US2] Append Traceability Table rows in `specs/027-spec-hardening/spec.md` for every gap resolved by T016–T038 and update `specs/shared/gap-id-register.md` statuses accordingly.
  - **Agent(s)**: `product-owner-ba`, `observer-auditor`.
  - **Tools**: `read`, `edit`.
  - **Success**: Post-merge row count in Traceability Table equals the non-Open count in the gap register. No gap cited in spec 001 is missing a register row.

**Checkpoint**: SC-002, SC-003, SC-004, SC-007, SC-009 become testable — run Quickstart steps 2, 3, 5, 7.

---

## Phase 5: User Story 3 — Claims about the solution are falsifiable (Priority: P2)

**Goal**: Each major design claim is backed by a falsifiable hypothesis with leading indicator, measurement window, and Evidence Pack stub.

**Independent Test**: Enumerate the six required hypothesis themes; confirm each is present with the mandated form and has a stub file on disk (quickstart step 4, step 8).

### Implementation for User Story 3

- [x] T040 [US3] Author Hypothesis rows `HYP-001` (safety-autonomy) and `HYP-002` (signal trust) in `specs/001-disaster-response-hub/spec.md § Hypotheses` using the template at `specs/027-spec-hardening/contracts/hypothesis-row.md`. Link each to the FR / NFR it underpins (autonomy-boundary table from T033; signal trust fields from spec 001).
  - **Agent(s)**: `qa-test-engineer` (drafter), `security-engineer` (safety-autonomy SME), `data-engineer` (signal-trust SME).
  - **Tools**: `read`, `edit`, `agent`.
  - **Success**: Two rows present; each conforms to the *"We believe X will produce Y for Z; wrong if W observed in window T"* form.

- [x] T041 [US3] Author Hypothesis rows `HYP-003` (orchestration: deterministic vs LLM-routed) and `HYP-004` (mobile delivery under degraded connectivity).
  - **Agent(s)**: `qa-test-engineer`, `ai-ml-engineer`, `api-architect`, `ux-designer`, `field-coordinator`.
  - **Tools**: `read`, `edit`, `agent`.
  - **Success**: Two rows present; `linked_decision` for HYP-004 resolves to the Performance/Freshness NFRs authored in T020.

- [x] T042 [US3] Author the Hypothesis row `HYP-005` (misinformation resilience). `HYP-006` is authored in Phase 3 by T013b; do NOT re-author it here.
  - **Agent(s)**: `qa-test-engineer`, `public-information-officer`.
  - **Tools**: `read`, `edit`, `agent`.
  - **Success**: `HYP-005` row present and conforms to the *"We believe X will produce Y for Z; wrong if W observed in window T"* form. No duplicate `HYP-006` row is introduced.

- [x] T043 [P] [US3] For every hypothesis authored in T040–T042 (`HYP-001`..`HYP-005`), create `specs/001-disaster-response-hub/evidence/HYP-###.md` using the template at `specs/027-spec-hardening/contracts/evidence-pack-stub.md` with front-matter `status: Not tested` and a stub `## History` row (FR-020, Clarification 9). `HYP-006`'s stub is already on disk from T013b.
  - **Agent(s)**: `qa-test-engineer`, `observer-auditor`.
  - **Tools**: `read`, `edit`, `execute`.
  - **Success**: Five files (`HYP-001..005`) exist on disk at row-creation time; together with `HYP-006.md` (from T013b) the total is six. Each front-matter `status` matches its hypothesis row. Each `## History` has exactly one row (stub creation).

- [x] T044 [US3] Cross-reference existing Success Criteria that embed causal claims (SC-004, SC-005, SC-006 of spec 001) from at least one hypothesis so an invalidated hypothesis forces reconsideration per FR-021.
  - **Agent(s)**: `product-owner-ba`, `qa-test-engineer`.
  - **Tools**: `read`, `edit`.
  - **Success**: Each of SC-004, SC-005, SC-006 carries a parenthetical citing the specific `HYP-###` whose invalidation would reopen it.

- [x] T045 [US3] Append Traceability Table rows for HYP-GAP-001..006 and update the register to `Resolved`.
  - **Agent(s)**: `product-owner-ba`, `observer-auditor`.
  - **Tools**: `read`, `edit`.
  - **Success**: Six Traceability rows exist with non-empty `evidence_pack` column; the 6 HYP-GAP rows in the register are `Resolved`.

**Checkpoint**: SC-005, SC-006 are testable — run Quickstart step 4.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Build the verification gate, lint, detect contradictions against the rest of spec 001's downstream artefacts, and deliver the full traceability table.

- [x] T046 [P] Expand the placeholder at `scripts/verify-spec-hardening.ps1` (from T003) to enforce the five cross-entity invariants in `data-model.md`: (a) gap-closure symmetry, (b) hypothesis-evidence lockstep, (c) signature presence on status transitions, (d) scope consistency (Deferred ↔ Boundary), (e) plan-phase ordering for Open Deltas.
  - **Agent(s)**: `software-developer` (author), `qa-test-engineer` (invariants review), `principal-engineer` (code review).
  - **Tools**: `read`, `edit`, `execute`.
  - **Success**: Running `pwsh -File scripts/verify-spec-hardening.ps1` on the current branch exits 0; introducing a synthetic breach of each invariant causes exit 1 with a clear message.

- [x] T047 Inspect `specs/001-disaster-response-hub/plan.md`, `data-model.md`, `contracts/`, `quickstart.md`, `tasks.md` for contradictions against the hardened spec per FR-032. Every contradiction is either fixed in this branch OR recorded as an Open Delta row with `target_feature` and `blocking_phase = plan`.
  - **Agent(s)**: `speckit.analyze` (consistency sweep), `product-owner-ba`, `solution-architect`, `security-engineer`, `compliance-auditor`, `principal-engineer`.
  - **Tools**: `agent` (delegate consistency sweep to `speckit.analyze`), `read`, `edit`.
  - **Success**: `speckit.analyze` reports zero unreconciled contradictions OR every remaining contradiction has a matching Open Delta row. Every Open Delta appears in the 027 Traceability Table.

- [x] T048 Populate `## Traceability Table` in `specs/027-spec-hardening/spec.md` with the full 40-row set, one row per gap ID, cross-linked to the FR / NFR / § anchor that resolved it and to the Evidence Pack where applicable (FR-031).
  - **Agent(s)**: `product-owner-ba`, `observer-auditor` (row-count audit), `speckit.analyze`.
  - **Tools**: `read`, `edit`, `agent`.
  - **Success**: Row count equals 40. Every row has non-empty `resolved_by`. Every category = Hypothesis row has non-empty `evidence_pack`. Status of every row matches the gap register.

- [x] T049 [P] Run `pnpm exec markdownlint-cli2` over every file authored / amended by this feature; resolve any violations without disabling lint rules globally.
  - **Agent(s)**: `software-developer`, `principal-engineer`.
  - **Tools**: `execute`, `edit`.
  - **Success**: `pnpm exec markdownlint-cli2 "specs/027-spec-hardening/**/*.md" "specs/001-disaster-response-hub/**/*.md" "specs/shared/**/*.md" ".github/CODEOWNERS"` exits 0.

- [x] T050 [P] Run `markdown-link-check` (relative links only) on the same file set; fix broken relative links.
  - **Agent(s)**: `software-developer`.
  - **Tools**: `execute`, `edit`.
  - **Success**: Zero failing relative links reported.

- [x] T051 Run the Quickstart walkthrough (`specs/027-spec-hardening/quickstart.md` steps 1–10) end-to-end against the branch HEAD. Record any step that fails as an Open Delta.
  - **Agent(s)**: `observer-auditor` (independent reviewer), `qa-test-engineer`, `speckit.checklist` (generate the reviewer checklist if not already present).
  - **Tools**: `agent`, `execute`, `read`.
  - **Success**: Every quickstart step passes. No new Open Delta rows are introduced by the walkthrough.

- [x] T052 [P] Update `specs/027-spec-hardening/plan.md` Phase status markers from "complete" to a final "sealed on `YYYY-MM-DD`" note and bump the "Last reviewed" date in spec 001's changelog.
  - **Agent(s)**: `product-owner-ba`.
  - **Tools**: `edit`.
  - **Success**: Both files reflect the merge date; no placeholder dates remain.

- [x] T053 Open a single PR to merge branch `027-spec-hardening`, ensuring CODEOWNERS review is requested from `@johnbilliris/ama-spec-maintainers` and that the PR description lists every gap ID whose status changed.
  - **Agent(s)**: `product-owner-ba`, `principal-engineer`, `security-engineer`.
  - **Tools**: `execute` (`gh pr create`), `read`.
  - **Success**: PR exists; CODEOWNERS review requested; description contains a table mapping the 40 gap IDs to new status. CI (lint + verify-spec-hardening.ps1) is green.

- [x] T054 [P] Author `specs/027-spec-hardening/checklists/requirements.md` — the reviewer checklist referenced by spec §Evaluation Method — using `speckit.checklist` to generate the initial set from `spec.md` FRs + SCs, then curate to one checkbox per FR/SC/Open-Delta item. This replaces T051's conditional side-effect with a deterministic artefact.
  - **Agent(s)**: `speckit.checklist` (generator), `product-owner-ba`, `qa-test-engineer`, `observer-auditor` (reviewer).
  - **Tools**: `agent`, `read`, `edit`.
  - **Success**: File exists. Contains at minimum one checkbox per FR (36) + one per SC (10) + one per Open Delta. Referenced from spec 027 § Evaluation Method with a relative link.

- [x] T055 Wire `scripts/verify-spec-hardening.ps1` into the Spec-Kit plan-phase gate so FR-032's "Open Deltas MUST block `/speckit.plan`" invariant is mechanically enforced. Approach: invoke the script from `.specify/scripts/powershell/check-prerequisites.ps1 -RequirePlan` (guarded by a repo-root marker so it is a no-op outside this monorepo) OR add a preamble check to `.github/prompts/ama.3-plan.prompt.md`. Document the chosen integration point in `scripts/verify-spec-hardening.ps1` header.
  - **Agent(s)**: `software-developer`, `principal-engineer` (review), `compliance-auditor` (audit-trail review).
  - **Tools**: `read`, `edit`, `execute`.
  - **Success**: Running `/speckit.plan` on a feature with a matching Open Delta row exits non-zero with a message naming the blocking delta; running it on a feature with no blocking delta is unaffected. Integration point is documented and discoverable by grep.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup (T001–T003). Blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational. No dependency on US2 or US3.
- **User Story 2 (Phase 4)**: Depends on Foundational. Independent of US1 and US3 but will benefit from US1's v1-jurisdiction decision being sealed first.
- **User Story 3 (Phase 5)**: Depends on Foundational. Independent of US1 and US2. `HYP-004` references NFR artefacts produced in US2; `HYP-006` is authored in US1 (T013b) rather than here — T042/T043 in this phase author only `HYP-001..005`.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1) 🎯 MVP**: Fully independent — self-contained PR. Ships the v1 jurisdiction declaration, the re-characterisation of the Asia-extensibility claim, and the `HYP-006` row + evidence stub that closes that re-characterisation in the same commit.
- **US2 (P1)**: Independent — assumption / NFR / persona / scope hardening. Pairs naturally with US1 for the MVP PR but can be shipped in a follow-up PR if needed.
- **US3 (P2)**: Independent once the first NFRs exist (T017–T023) so hypotheses can reference them. Can be shipped as a third PR.

### Within Each User Story

- Shared-register writes (gap register, CODEOWNERS, traceability table) happen at the *end* of each user story to avoid merge conflicts.
- Persona profiles (T026–T030) are pure inserts and fully parallelisable.
- NFR rows (T017–T023) are pure inserts and fully parallelisable.
- Evidence Pack stubs (T043) must be created in the same commit as the corresponding hypothesis row to satisfy FR-020's "stub at creation" rule.

### Parallel Opportunities

- Setup: T002 and T003 in parallel.
- Foundational: T007, T008, T009 in parallel after T004–T006 complete.
- US1: T014 can run in parallel with T010–T013.
- US2: T016–T023 (assumption + NFR inserts) fully parallel. T026–T030 (persona inserts) fully parallel. T032–T037 (scope inserts) fully parallel.
- US3: T043 parallel across the five evidence files (`HYP-001..005`); `HYP-006.md` was already created in US1 by T013b.
- Polish: T049, T050, T052 in parallel.

---

## Parallel Example: User Story 2 NFR cluster

```text
# Launch the seven NFR tasks together — each writes a different row:
T017 [P] [US2] Accessibility NFR → accessibility-tester + ux-designer
T018 [P] [US2] Privacy NFR cluster → compliance-auditor + security-engineer
T019 [P] [US2] Security NFR cluster → security-engineer + sre-engineer
T020 [P] [US2] Promote performance NFRs → sre-engineer + solution-architect
T021 [P] [US2] Interoperability NFRs → api-architect + nema
T022 [P] [US2] Training NFR → ux-designer + resilience-planner
T023 [P] [US2] Audit-retention NFR → observer-auditor + security-engineer
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003).
2. Complete Phase 2: Foundational (T004–T009).
3. Complete Phase 3: US1 (T010–T015).
4. Run Quickstart steps 1 and 5 with `observer-auditor`.
5. Open PR with CODEOWNERS review — demonstrable resolution of the capstone-vs-solution scoping defect.

### Incremental Delivery

1. Setup + Foundational → Foundation ready.
2. Add US1 → test via Quickstart step 1/5 → PR #1 (MVP).
3. Add US2 (assumptions, NFRs, personas, scope) → test via Quickstart 2/3/7 → PR #2.
4. Add US3 (hypotheses + evidence stubs) → test via Quickstart 4/8 → PR #3.
5. Polish phase as PR #4 (traceability complete, verification script, full quickstart run).

### Parallel Team Strategy

With multiple reviewers:

1. Team completes Setup + Foundational together.
2. Once Foundational is done:
   - Lane A (product-owner-ba + resilience-planner): US1.
   - Lane B (NFR authors named in T017–T023 with compliance-auditor coordination): US2 NFR cluster.
   - Lane C (ux-designer + accessibility-tester + operational agents): US2 Persona cluster.
   - Lane D (qa-test-engineer + ai-ml-engineer): US3 hypotheses.
3. Lanes converge in Polish (T047 `speckit.analyze` sweep, T048 Traceability Table seal).

---

## Actor-agent coverage summary

| Agent category | Named agents in this tasks file | Minimum tasks |
| --- | --- | --- |
| Operational personas | incident-commander, operations-officer, logistics-officer, public-information-officer, field-coordinator, resilience-planner, observer-auditor, executive-leader, risk-manager | 15 |
| Commonwealth / sector | nema, bom-national, ga-national, afp, arc, community-ngos, state-government, local-government, transport, utility, health | 10 |
| Technical personas | solution-architect, software-developer, infrastructure-devops, data-engineer, security-engineer, qa-test-engineer, ux-designer, product-owner-ba, api-architect, principal-engineer, sre-engineer, ai-ml-engineer, accessibility-tester, chaos-engineer, compliance-auditor | 40+ |
| Speckit workflow | speckit.analyze, speckit.checklist | 2 |

Every task in this file names ≥ 1 primary actor agent, ≥ 1 countersigning or reviewing agent where the artefact is status-bearing, and a tool set constrained to `{execute, read, edit, search, web, agent, todo}`.

---

## Notes

- `[P]` = different files, no dependencies on in-flight tasks.
- `[Story]` label maps each task to its user story; setup, foundational, and polish tasks carry no story label.
- No runtime code is produced by this feature. All tasks operate on markdown, YAML front-matter, PowerShell, and GitHub configuration.
- Every status-bearing row (Assumption, NFR, Hypothesis, Persona, Open Delta, Traceability Link) requires drafter + countersigner signatures at row-creation time per FR-034.
- Verify `scripts/verify-spec-hardening.ps1` exits 0 before merging any task's output.
- Stop at any checkpoint (end of a Phase) to validate the current increment independently; do not batch checkpoints.
- Avoid: vague "update the spec" tasks, cross-story dependencies that break Independent Test guarantees, and edits that widen scope beyond `specs/001-disaster-response-hub/`, `specs/027-spec-hardening/`, `specs/shared/`, and `.github/`.
