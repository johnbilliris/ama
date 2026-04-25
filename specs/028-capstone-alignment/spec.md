# Feature Specification: Capstone Alignment Hardening Across AMA Specs

**Feature Branch**: `028-capstone-alignment`  
**Created**: 2026-04-24  
**Status**: Draft  
**Input**: User description: "Capstone alignment hardening across AMA specs — add Assumptions, Requirements, Personas, Hypotheses, and Out-of-Scope sections to every spec so the portfolio meets the Asia-framed capstone brief."

## Clarifications

### Session 2026-04-24

- Q: Which spec is the authoritative owner of the recovery phase (resolving the split across 001 DEF-015 / 018 recovery indicators / 011 resource aspects)? → A: Spec 018 (aidr-guidance-integration) is authoritative; specs 001 and 011 carry `defers-to: 018` pointers.
- Q: Should this feature lock canonical BCP-47 language codes for PH/JP/BD language packs, or defer naming to each spec? → A: Defer — this feature only mandates "≥1 non-English language per capstone country" as a deferred capability; canonical identifier selection (Filipino vs Tagalog, Bengali variant, dialect coverage) is resolved in each owning spec's `research.md`.
- Q: What is the schema of `specs/shared/capstone-metric-trace.md`? → A: A single Markdown table with fixed columns `Metric | Country Cohort | SC Owner | HYP Owner | Baseline | Measurement Method | Status`; one row per (metric × cohort) = 5 metrics × 4 cohorts (AU-v1, PH, JP, BD) = 20 rows; `Status ∈ {Validated, Deferred, Unresolved}`.
- Q: Which specs must self-flag as delivery-hygiene / non-capstone-critical-path under FR-020? → A: `003, 004, 007, 013, 016, 017, 024, 025, 026, 027, 028` — expanded to include all infrastructure/tooling/simulation/demo specs with no direct line to the five capstone outcome metrics.
- Q: What is the minimum content of each new `evidence/HYP-*.md` stub? → A: Fixed H2 headings with minimum content — `## Hypothesis` (restates the spec-027 FR-018 format), `## Preconditions` (≥2 bullets), `## Measurement Window` (named capstone season, e.g., "PH typhoon season Jun–Nov"), `## Falsification Criterion` (≥1 quantified threshold), `## Status` (= `Not tested`), `## Linked` (spec/SC/ASM refs).
- Q: What is the quantified "measurable uplift" threshold for SC-009 against the AMA rubric? → A: Composite gate — for the 5 rubric criteria tied to Assumptions / Requirements / Personas / Hypotheses / Scope, (i) mean score increases by ≥1 point versus the pre-feature baseline snapshot, AND (ii) no individual criterion regresses (delta ≥ 0 for each).

### Session 2026-04-25 — `/speckit.analyze` remediation

- Q: US1 Independent Test previously referenced "five mandatory sections" including Requirements; FR-001..FR-004 only mandate four new H2 sections (Assumptions, Personas, Hypotheses, Out of Scope) — which is authoritative? → A: Four H2 sections is authoritative. US1 Independent Test corrected to list four; the pre-existing `## Requirements` section in each spec is unchanged by this feature (handled by FR-005a below for AU-only legitimisation).
- Q: US1 Acceptance Scenario 5 ("AU-only scope legitimised by explicit assumption") is not codified by any FR — promote or drop? → A: Promote. Added **FR-005a** requiring every AU-only FR to carry an inline `[AU-only — see ASM-###]` citation pointing to an assumption ID.
- Q: FR-023 (non-AU personas tagged `placeholder`) had no task coverage in `tasks.md` — add validator? → A: Yes, added polish task **T062a** greps every newly added non-AU persona for `status: placeholder` + non-empty preconditions.
- Q: SC-003 requires an external reviewer user test (≥3 reviewers × ≥5 specs each, ≤ 10 min per spec) that no task schedules — defer or schedule? → A: Defer validation to post-merge. SC-003 annotated as `validation: deferred-to-post-merge`; post-merge evidence path fixed at `specs/028-capstone-alignment/evidence/reviewer-timings.md`. Added non-blocking task **T063a** describing the post-merge activity.
- Q: FR-012 / SC-002 say each metric MUST have "at least one SC owner and at least one HYP owner anywhere in the portfolio" but the metric-trace schema allows `Deferred — preconditions: …` cells — is `Deferred` satisfactory? → A: Clarified. SC-002's "at least one owner" is satisfied **per metric aggregated across cohorts**: an AU-v1 row citing concrete SC/HYP IDs satisfies SC-002 even when PH/JP/BD cohort rows for the same metric are `Deferred`. No metric may be `Deferred` in every cohort.
- Q: Overlap-rule phrasing drifts across FR-017, FR-018 and US3 acceptance scenarios ("declares authoritative and defers", "scope rule", "authoritative for recovery-phase indicators") — adopt canonical template? → A: Adopted. Canonical phrasing is `authoritative for: <capability>` on the owning spec and `defers-to: <spec> (<capability>)` on the deferring spec. All new overlap rules use this template verbatim; see new paragraph under `## Overlap phrasing template` below.

## Background & Motivation

The AMA capstone (`capstone.md` §"Regional Specificity", lines 38–41) is explicitly Asia-framed — typhoons in the Philippines, earthquakes in Japan, floods in Bangladesh, multilingual alerts across regional languages and dialects, varying government response protocols, and strict location-data privacy laws. The 27-spec portfolio under `specs/` is, with the exception of `001-disaster-response-hub`, entirely Australia-first and largely silent on Asia. Spec 001 formalises this misalignment (DEF-001/002/003 at lines 465–467 defer PH/JP/BD; HYP-006 line 446 downgrades Asia portability to an unvalidated hypothesis). The existing `027-spec-hardening` is scoped **only** to spec 001 (line 18 references a non-existent `028-holistic-spec-hardening`). This feature closes that gap across the remaining 26 specs and the solution-as-a-whole so the capstone's Asia-specific success metrics, personas, and constraints become testable, falsifiable, and owned.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reviewer audits every spec for capstone alignment (Priority: P1)

A spec-portfolio reviewer opens any spec under `specs/NNN-*/` and can, without reading other specs, determine: (a) what assumptions that spec is betting on, (b) which personas it serves including any deferred Asia personas, (c) what testable hypotheses back its value claim, (d) what is explicitly out of scope, and (e) how its requirements map to the capstone's Asia context and five success metrics.

**Why this priority**: Without this, the capstone brief's Asia context is invisible at the spec level, which is the lens rubric evaluators use. This unlocks every downstream hardening outcome.

**Independent Test**: Open any 5 randomly-selected specs among 003–026 and confirm each contains the four mandatory H2 sections (Assumptions, Personas, Hypotheses, Out of Scope) with the content rules in FR-001..FR-004 satisfied, that the pre-existing `## Requirements` section complies with FR-005a (every AU-only FR carries an `[AU-only — see ASM-###]` citation), and that the five capstone-alignment questions can be answered in under 10 minutes per spec without external context.

**Acceptance Scenarios**:

1. **Given** any spec under `specs/NNN-*/spec.md` (excluding `specs/shared/` and `specs/feature/`), **When** a reviewer inspects it, **Then** an H2 `## Assumptions` section exists with ≥3 entries tagged `[TESTABLE|DECISION|RISK]` and cross-referenced to spec 001 or a new ID in `specs/shared/gap-id-register.md`.
2. **Given** any such spec, **When** a reviewer inspects it, **Then** an H2 `## Personas` section exists with ≥2 personas OR ≥2 explicit cross-references to spec 001 personas, formatted per the existing `specs/027-spec-hardening/contracts/persona-profile.md` contract.
3. **Given** any such spec, **When** a reviewer inspects it, **Then** an H2 `## Hypotheses` section exists with ≥1 testable hypothesis in the spec-027 FR-018 format (`"We believe {capability} will produce {outcome} for {persona}; we will know we are wrong if {leading indicator} is observed in {measurement window}"`) plus an `evidence/HYP-*.md` stub.
4. **Given** any such spec, **When** a reviewer inspects it, **Then** an H2 `## Out of Scope` section exists with ≥3 items, at least one of which explicitly defers a capstone country (PH/JP/BD) or a capstone hazard (typhoon/earthquake/riverine flood) with promotion preconditions.
5. **Given** any such spec, **When** a reviewer inspects it, **Then** every FR in the pre-existing `## Requirements` section whose scope is Australia-only carries an inline `[AU-only — see ASM-###]` citation pointing to an assumption ID (per FR-005a); AU-only scope is legitimised by an explicit assumption, never by silence.

---

### User Story 2 - Solution-as-a-whole demonstrably covers the five capstone success metrics (Priority: P1)

A rubric evaluator opens a single traceability artefact and can see which spec owns the success criterion (SC) and hypothesis (HYP) for each of the five capstone metrics (save 1,000+ lives/yr, 50% faster response, 24 h earlier evacuation, 30% logistics efficiency, 30% economic loss reduction), for each of Australia-v1 and capstone-country cohorts (PH, JP, BD).

**Why this priority**: The capstone is judged on these five metrics. Today only three of them (50%, 24h, 30% logistics) bind to spec 001 SC-004/005/006 for AU only; "1,000 lives" and "30% economic loss" have no SC or HYP owner in any spec.

**Independent Test**: Open `specs/shared/capstone-metric-trace.md` and verify every row has at least one SC owner and one HYP owner spec, with a separate column per country cohort. Following each cited SC/HYP back into the referenced spec confirms it exists as written.

**Acceptance Scenarios**:

1. **Given** the capstone's five success metrics, **When** the evaluator opens `specs/shared/capstone-metric-trace.md`, **Then** every metric has a named SC owner spec, HYP owner spec, baseline, and measurement method.
2. **Given** any capstone country (PH, JP, BD), **When** the evaluator filters the trace for that country, **Then** the cell shows either a validated row OR a `Deferred — preconditions: …` row (never silent).
3. **Given** a referenced SC or HYP ID, **When** the evaluator opens the cited spec, **Then** the ID exists in that spec at the referenced section.

---

### User Story 3 - Cross-spec overlaps and ownership gaps are explicit (Priority: P2)

A reader determining which spec owns a capability does not need to read Session notes or infer from prose; every overlap or supersession is declared with a `supersedes` / `defers-to` rule in the affected spec.

**Why this priority**: Observed overlaps today (spec 006 FR-024 defining Communication Agent behaviour duplicating spec 008; spec 018 superseding spec 008's escalation timeout only in prose; recovery ownership between 001/018/011 unresolved) cause reviewer confusion and duplicated effort.

**Independent Test**: Grep for the strings `supersedes`, `defers-to`, and `authoritative for` across `specs/*/spec.md`; each overlap listed in this spec's Assumptions has at least one matching rule in the affected spec.

**Acceptance Scenarios**:

1. **Given** spec 006 FR-024, **When** a reader inspects spec 006, **Then** FR-024 is either relocated to spec 008 or reframed as a contract assumption with an explicit `defers-to: 008` pointer.
2. **Given** spec 018's escalation-timeout supersession, **When** a reader inspects both 008 and 018, **Then** each carries a scope rule declaring 018 authoritative and 008 deferring.
3. **Given** recovery-phase work across 001, 018, and 011, **When** a reader inspects these specs, **Then** exactly one is declared authoritative for recovery ownership and the other two carry `defers-to` rules.

---

### User Story 4 - Meta/delivery-hygiene specs are flagged as non-capstone-critical-path (Priority: P3)

A reader of the 27-spec portfolio can trivially separate capstone-value specs from delivery-hygiene specs (`003, 004, 007, 013, 016, 017, 024, 025, 026, 027, 028`).

**Why this priority**: Reduces cognitive load for rubric evaluators; prevents misreading meta work as capstone drift.

**Independent Test**: Each meta spec carries an H2 `## Out of Scope` block with the line "This spec is delivery-hygiene; capstone-outcome-critical-path ownership lives in specs [list]."

**Acceptance Scenarios**:

1. **Given** spec 027, **When** a reader opens it, **Then** the stale `028-holistic-spec-hardening` reference (line 18) is replaced by a pointer to this feature (028-capstone-alignment).
2. **Given** spec 013/016/025/026, **When** a reader opens each, **Then** each declares itself delivery-hygiene with pointers to the capstone-critical-path specs it supports.

---

### Edge Cases

- A spec already has a `## Personas` section inherited from spec 001 only (e.g., spec 022): this is sufficient IFF the cross-reference format matches the persona-profile contract and the persona's applicability to this spec's country cohort is explicit.
- A spec has zero data-model involvement (e.g., `017-cd-pipeline`): the `## Hypotheses` section must still contain ≥1 hypothesis about operator behaviour, pipeline reliability, or region-topology portability — not omitted.
- A spec is genuinely not capstone-country-relevant today (e.g., `004-actor-github-agents`): Out-of-Scope must explicitly name PH/JP/BD as non-applicable-today with preconditions for future applicability, not silently omit them.
- A spec's existing `Assumptions` block uses a different taxonomy (e.g., spec 010 line 215): this is addressed by adding a taxonomy-mapping row pointing to spec 001's `[drafter | countersigner | status | linked_gaps]` format, not by rewriting the existing block.
- Two specs end up claiming authoritative ownership of the same capability: the hardening work MUST resolve to exactly one authoritative owner before the feature is considered complete.
- The `specs/feature/` folder contains stale duplicates of 013/014/015/017: these are flagged as out-of-scope for this feature and a separate removal proposal is authored, not merged in.

## Requirements *(mandatory)*

### Functional Requirements

#### Section coverage (every spec must have)

- **FR-001**: Every spec under `specs/NNN-*/spec.md` (excluding `specs/shared/` and `specs/feature/`) MUST contain an H2 `## Assumptions` section with ≥3 entries, each tagged `[TESTABLE|DECISION|RISK]`, each cross-referenced to either an existing spec-001 ASM-* or a newly allocated ASM-ID in `specs/shared/gap-id-register.md`.
- **FR-002**: Every such spec MUST contain an H2 `## Out of Scope` section with ≥3 items, at least one of which explicitly defers a capstone country (Philippines, Japan, or Bangladesh) or a capstone hazard (typhoon, earthquake, riverine flood, cyclone-driven monsoon flood) with explicit promotion preconditions.
- **FR-003**: Every such spec MUST contain an H2 `## Personas` section with ≥2 personas or ≥2 explicit cross-references to personas defined in spec 001, following the YAML front-matter contract at `specs/027-spec-hardening/contracts/persona-profile.md`.
- **FR-004**: Every such spec MUST contain an H2 `## Hypotheses` section with ≥1 testable hypothesis in the spec-027 FR-018 format and an accompanying `evidence/HYP-*.md` stub per spec-027 FR-020.
- **FR-005**: Any spec that currently has an Assumptions, Personas, Hypotheses, or Out-of-Scope block in a different form MAY retain the existing form, but MUST add a taxonomy-mapping row cross-referencing spec 001's format.
- **FR-005a**: Any FR inside a spec's pre-existing `## Requirements` section whose effective scope is Australia-only MUST carry an inline `[AU-only — see ASM-###]` citation whose target is an existing or newly-allocated assumption ID explaining the AU-only scoping. Grep-verifiable: for every `spec.md` outside `specs/shared/` and `specs/feature/`, `grep -nE "\\[AU-only — see ASM-[0-9]{3}\\]" specs/NNN-*/spec.md` MUST return at least one match iff that spec contains any FR tagged AU-only, and every cited ASM-### MUST exist in the same spec's `## Assumptions` section or in `specs/shared/gap-id-register.md`. Silence (AU-only scope with no citation) is a defect.

#### Capstone-country coverage (selected specs)

- **FR-006**: Spec 008 (Communication Agent) MUST add a language-pack plugin FR requiring **≥1 non-English language pack per capstone country (Philippines, Japan, Bangladesh)** as a deferred capability, each with content-safety and back-translation preconditions. Canonical BCP-47 identifier selection (e.g., Filipino vs Tagalog, Bengali locale variant, dialect coverage) is **deferred to the owning spec's `research.md`** and is not decided in this feature. Spec 008 MUST also add a multilingual-misinformation-detection deferred FR that inherits the spec-010 fallback rule.
- **FR-007**: Spec 005 (Data Source Governance) MUST add a per-country PII classification FR naming Australia's `Privacy Act 1988 (Cth) + APPs`, Japan's `APPI (2017/2020)`, the Philippines' `Republic Act 10173 (DPA 2012)` + NPC issuances, and Bangladesh's `ICT Act 2006 + draft DPA 2023`, with each non-AU entry marked deferred.
- **FR-008**: Spec 022 (Multi-Jurisdiction Filter) MUST add a country-dimension FR supporting a nested `country→state/region` hierarchy; PH/JP/BD nodes MUST be present as placeholders with preconditions.
- **FR-009**: Spec 006 (Data Ingestion & Storage) MUST add a deferred-scope FR enumerating at least one candidate feed per capstone country (e.g., PAGASA, JMA/QZSS, BWDB/FFWC) with validation preconditions.
- **FR-010**: Spec 017 (CD Pipeline) MUST add a deferred FR: pipeline supports region-per-country topology; today deploys to `australiaeast`/`australiasoutheast` only; reversal of this default is a capstone-reinterpretation decision owned outside this feature.
- **FR-011**: Specs 008, 009, 010, 011, 012 (the five agent specs other than 001 roll-up) MUST each add ≥1 capstone-country-scoped hypothesis per capstone country (PH, JP, BD), each marked `Not tested` with explicit preconditions for promotion.
- **FR-012**: Spec 015 (Performance Benchmarks) MUST add SC rows mapping at least one benchmark scenario to each of the five capstone success metrics (1,000 lives, 50% response, 24h earlier, 30% logistics, 30% economic loss) with baseline and measurement method; each metric MUST have at least one SC owner and at least one HYP owner anywhere in the portfolio. **Aggregation rule (per FR-013/SC-002 clarification 2026-04-25)**: "at least one owner" is satisfied *per metric aggregated across cohorts* — an AU-v1 row citing concrete SC/HYP IDs satisfies this requirement even when PH/JP/BD cohort rows for the same metric carry `Deferred — preconditions: …`. A metric whose rows are `Deferred` in **all four** cohorts does NOT satisfy SC-002 and is a defect.

#### Traceability and registry

- **FR-013**: A new artefact `specs/shared/capstone-metric-trace.md` MUST exist as a single Markdown table with fixed columns `Metric | Country Cohort | SC Owner | HYP Owner | Baseline | Measurement Method | Status`, containing exactly one row per (capstone metric × country cohort) combination — 5 metrics × 4 cohorts (AU-v1, PH, JP, BD) = 20 rows. `Status` MUST be one of `Validated`, `Deferred`, `Unresolved`. `SC Owner` and `HYP Owner` cells MUST cite spec-number + ID (e.g., `001:SC-004`) or state `Deferred — preconditions: …`.
- **FR-014**: `specs/shared/gap-id-register.md` MUST be updated to allocate new ASM/HYP/PER/SCP/REQ IDs for every new entry created by this feature, preserving monotonicity (no renumbering of existing IDs).
- **FR-015**: Every new hypothesis introduced by this feature MUST have a corresponding `evidence/HYP-<id>.md` stub in the owning spec's folder containing exactly these H2 headings with the minimum content shown:
  - `## Hypothesis` — restates the hypothesis in the spec-027 FR-018 format.
  - `## Preconditions` — ≥2 bullets naming what must be true before the hypothesis can be tested (e.g., "PH PAGASA feed contract signed"; "fil-PH language pack templates approved").
  - `## Measurement Window` — a named capstone season or bounded window (e.g., "PH typhoon season Jun–Nov"; "JP continuous; quarterly review"; "BD monsoon Apr–Sep").
  - `## Falsification Criterion` — ≥1 quantified threshold that, if observed, falsifies the hypothesis.
  - `## Status` — literal value `Not tested`.
  - `## Linked` — references to the owning spec + any SC, ASM, or other HYP IDs.

#### Overlap and authority resolution

- **FR-016**: Spec 006 FR-024 (Communication Agent behaviour defined inside the ingestion spec) MUST be either relocated to spec 008 or reframed as a contract assumption with an explicit `defers-to: 008` pointer.
- **FR-017**: Spec 018's supersession of spec 008's warning-tier approval timeout MUST be reflected by explicit scope rules in both specs: 018 declares authoritative ownership; 008 declares `defers-to: 018`.
- **FR-018**: Recovery-phase ownership is **authoritatively owned by spec 018 (`aidr-guidance-integration`)**. Spec 001 DEF-015 and spec 011 resource-recovery behaviour MUST each carry a `defers-to: 018` pointer; spec 018 MUST carry a scope rule declaring itself authoritative for recovery-phase indicators, triggers, and phase-exit criteria across the portfolio.
- **FR-019**: Spec 027's stale reference to the non-existent `028-holistic-spec-hardening` (line 18) MUST be replaced with a pointer to this feature (`028-capstone-alignment`), and spec 027's scope note clarifying that cross-spec hardening is owned by this feature MUST be retained.

#### Overlap phrasing template *(canonical; applies to FR-016..019)*

Every overlap rule introduced by this feature MUST use exactly this verbatim template on both sides of the pair:

- On the **owning** spec, inside the section the rule governs, add one line:
  - `authoritative for: <capability>` (e.g., `authoritative for: recovery-phase indicators, triggers, phase-exit criteria`).
- On the **deferring** spec, inside the section the rule governs, add one line:
  - `defers-to: <NNN> (<capability>)` (e.g., `defers-to: 018 (warning-tier approval timeout)`).

Both sides MUST appear; a unilateral rule is a defect. Grep-verifiable: for every overlap declared by FR-016..019, `grep -rn "authoritative for: <capability>"` returns exactly one spec and `grep -rn "defers-to: <NNN>"` returns at least one match in every deferring spec.

#### Meta-spec flagging

- **FR-020**: Meta / delivery-hygiene specs — `003, 004, 007, 013, 016, 017, 024, 025, 026, 027, 028` — MUST each declare in Out-of-Scope: "This spec is delivery-hygiene / enabling infrastructure; capstone-outcome-critical-path ownership lives in specs [list]." The capstone-critical-path set is the complement: `001, 005, 006, 008, 009, 010, 011, 012, 014, 015, 018, 019, 020, 021, 022, 023`.

#### Quality gates

- **FR-021**: After this feature completes, zero `NEEDS CLARIFICATION` markers MAY remain in any `spec.md`, `research.md`, or `tasks.md` (baseline: 0 today; must stay 0). Markers in `checklists/` files are permitted.
- **FR-022**: No existing spec number or filename is renamed; no existing ASM/HYP/PER/SCP/REQ ID is renumbered. All additions are append-only.
- **FR-023**: Every new persona added by this feature for a non-AU jurisdiction MUST be tagged `placeholder` (not `validated`) with explicit preconditions for promotion to validated status.

### Key Entities *(documentation entities; no code)*

- **Spec**: An artefact at `specs/NNN-<name>/spec.md` plus sibling `research.md`, `tasks.md`, optional `evidence/`, `checklists/`, `contracts/`. Unit of change for this feature.
- **Capstone Metric**: One of five outcome targets from `capstone.md` lines 32–36. Each must have at least one SC owner spec and one HYP owner spec.
- **Capstone Country Cohort**: AU-v1 (baseline), PH, JP, BD. Every assumption/hypothesis/persona may be scoped to one or more cohorts; non-AU cohorts default to `deferred` with preconditions.
- **Capstone Hazard**: Typhoon (PH), earthquake (JP), riverine/cyclone-driven flood (BD), plus existing AU hazards (bushfire, cyclone, flood). Each hazard must be owned by spec 012 (risk assessment), and downstream agent specs must declare applicability.
- **Privacy-Law Regime**: AU Privacy Act 1988 + APPs; JP APPI; PH RA 10173 (DPA 2012) + NPC issuances; BD ICT Act 2006 + draft DPA 2023; regional regimes noted where relevant (SG PDPA 2012, MY PDPA 2010).
- **Cross-Agency Protocol**: AIIMS (AU, covered in spec 018); NDRRMC NDRP (PH); Cabinet Office Disaster Management Plan + ICS-JP (JP); SOD 2019 + CPP/CDMP (BD); ASEAN-AHA SASOP (regional). Placeholder-level references only.
- **Gap-ID Register**: `specs/shared/gap-id-register.md`, the monotonically-increasing source of truth for ASM/HYP/PER/SCP/REQ IDs used across the spec portfolio.
- **Capstone Metric Trace**: New `specs/shared/capstone-metric-trace.md` mapping each capstone metric to SC+HYP owners per country cohort.

## Assumptions

- The capstone brief (`capstone.md`) is the authoritative scoping document. Where the solution portfolio diverges (AU-first), the divergence must be legitimised by an explicit assumption + hypothesis in the owning spec, not by silence. `[DECISION]`
- The `027-spec-hardening` spec-001-only work is accepted as-is; this feature extends the same taxonomy (ASM/HYP/PER/SCP/REQ gap IDs, role countersign rule, monorepo-monotonic register) to the remaining 26 specs. `[DECISION]`
- Non-AU persona validation cannot complete in v1; new personas added by this feature for PH/JP/BD are `placeholder` with explicit promotion preconditions, not validated personas. `[RISK]`
- All new cross-references to capstone-country hazards, languages, privacy regimes, and cross-agency protocols are documentation-only at this stage; no functional code, data, or infrastructure change is implied. `[TESTABLE]`
- `specs/shared/gap-id-register.md` is the single source of truth for ID allocation; this feature appends, never renumbers. `[TESTABLE]`
- Existing `checklists/requirements.md` files that carry `NEEDS CLARIFICATION` markers are triaged by this feature (listed in tasks) but not rewritten as part of this feature. `[DECISION]`
- Spec 022's existing 9-AU-jurisdiction UI is preserved; the country dimension added by FR-008 is additive. `[DECISION]`
- Spec 027's "Evidence Pack must exist at hypothesis creation" rule (FR-020) applies to every new hypothesis added by this feature. `[TESTABLE]`
- The `specs/feature/` folder (stale duplicates of 013/014/015/017) is out-of-scope for edits; a separate removal proposal is authored but not merged here. `[RISK]`
- The contradiction between spec 001 ASM-005 (AU-only residency) and capstone sovereign-data requirements for PH/JP/BD is acknowledged but not resolved by this feature; resolution requires a capstone-reinterpretation decision owned elsewhere. A new assumption explicitly captures this unresolved contradiction in each affected spec. `[RISK]`

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of specs under `specs/NNN-*/spec.md` (excluding `specs/shared/` and `specs/feature/`) carry all four mandatory H2 sections (`## Assumptions`, `## Personas`, `## Hypotheses`, `## Out of Scope`) with the content rules in FR-001..FR-004 satisfied — measured by automated grep over the spec tree.
- **SC-002**: Each of the five capstone success metrics (1,000+ lives/yr; 50% faster response; 24 h earlier evacuation; 30% logistics efficiency; 30% economic loss reduction) has at least one SC owner spec and at least one HYP owner spec in `specs/shared/capstone-metric-trace.md`, verifiable by opening the trace and following each reference.
- **SC-003**: A reviewer new to the portfolio can, in under 10 minutes per spec, answer the five capstone-alignment questions for any randomly-selected spec (assumptions, personas, hypotheses, out-of-scope, AU-vs-capstone scope), measured by a user test with ≥3 independent reviewers on ≥5 specs each. **Validation**: deferred-to-post-merge — this SC is not gated by `/speckit.implement`. Evidence persists at `specs/028-capstone-alignment/evidence/reviewer-timings.md` when the post-merge user test is run (see `tasks.md` T063a). Failure to run the post-merge test does not block the feature from shipping; it blocks the SC from being marked Validated.
- **SC-004**: Zero `NEEDS CLARIFICATION` markers remain in any `spec.md`, `research.md`, or `tasks.md` file (baseline: 0 today) after this feature lands; markers in `checklists/` are permitted.
- **SC-005**: At least 15 capstone-country-scoped hypotheses (5 agent specs × 3 countries) are added and each has a corresponding `evidence/HYP-*.md` stub with `Status: Not tested` and declared preconditions.
- **SC-006**: Every overlap enumerated in FR-016..FR-019 (spec 006↔008, spec 018↔008, recovery across 001/018/011, spec 027 stale reference) is reconciled with an explicit `supersedes` / `defers-to` rule, verifiable by grep and by opening the referenced sections.
- **SC-007**: `specs/shared/gap-id-register.md` monotonicity is preserved — no existing ID is renumbered; every new ID is strictly greater than the prior highest ID in its family, verifiable by diff against the pre-feature baseline.
- **SC-008**: 100% of meta/delivery-hygiene specs (`003, 004, 007, 013, 016, 017, 024, 025, 026, 027, 028`) carry the declarative Out-of-Scope line required by FR-020.
- **SC-009**: Post-feature AMA rubric snapshot (graded via the `ama-rubric-grader` skill against `AMA_Rubric_Asia.md`) satisfies BOTH of the following versus the pre-feature baseline snapshot of the same spec set, across the 5 rubric criteria tied to Assumptions, Requirements clarity, Personas, Hypotheses, and Scope boundaries: (i) mean score across these 5 criteria increases by ≥1 point; AND (ii) no single criterion regresses (per-criterion delta ≥ 0).

## Out of Scope

- This spec is delivery-hygiene / enabling infrastructure; capstone-outcome-critical-path ownership lives in specs all capstone-critical-path specs (001, 005, 006, 008, 009, 010, 011, 012, 014, 015, 018, 019, 020, 021, 022, 023).

- Rewriting working code in `apps/`, `packages/`, `infra/`, or `scripts/`.
- Re-architecting agents, adding/removing agents, or changing agent port assignments (spec 008 line 20).
- Re-numbering or renaming existing specs, or editing existing ASM/HYP/PER/SCP/REQ IDs.
- Reversing the v1-Australia-primary decision recorded in spec 001 ASM-001 and spec 027 FR-022 — any such reversal is an explicit capstone-reinterpretation decision owned outside this feature.
- Creating the phantom `028-holistic-spec-hardening` referenced in spec 027 line 18; instead this feature **is** that work under the allocated feature number 028.
- Implementing Asia-region feeds, language packs, or legal mappings — this feature documents them as first-class deferred scope with preconditions only.
- Editing `capstone.md` or `AMA_Rubric_Asia.md` (authoritative inputs).
- Altering content under `specs/feature/` (stale duplicates of 013/014/015/017); flag out-of-scope and propose removal separately.
- Validating newly-added non-AU personas with real SMEs (promotion from `placeholder` to `validated` is deferred).
- Resolving the AU-only-residency vs capstone-sovereign-data contradiction; this feature documents the unresolved contradiction, it does not resolve it.
- Rewriting `checklists/requirements.md` files that carry `NEEDS CLARIFICATION` markers (triage only; rewrite is a separate feature).

## Dependencies

- Depends on `027-spec-hardening` existing taxonomy, gap-id register, and persona-profile contract.
- Depends on `specs/shared/gap-id-register.md` being writable and monotonic.
- Depends on `capstone.md` and `AMA_Rubric_Asia.md` remaining authoritative during this feature's lifecycle.

## References

- `capstone.md` (authoritative brief; Asia-framed success metrics, lines 32–41)
- `AMA_Rubric_Asia.md` (evaluator lens)
- `specs/001-disaster-response-hub/spec.md` (canonical taxonomy for Assumptions/Personas/Hypotheses/Scope and Deferred-Scope Register lines 463–481)
- `specs/027-spec-hardening/spec.md` (scope note line 18; FR-018 HYP format; FR-020 evidence-pack rule; contracts/persona-profile.md)
- `specs/shared/gap-id-register.md` (ID register; referenced by 027 FR-Uniqueness line 31)


## Personas

> Authored against `specs/027-spec-hardening/contracts/persona-profile.md`. AU-v1 personas validated; capstone-country personas explicit placeholders pending D-009 resolution per FR-023.

- **PER-074**: cross-ref to `specs/001-disaster-response-hub/spec.md` § Personas — Incident Commander, Planning Officer, Operations Officer, Logistics Officer, Public Information Officer, Field Coordinator, Resilience Planner, Observer / Auditor. `status:` validated. `preconditions:` none.
- **PER-075**: cross-ref to `specs/004-actor-github-agents/spec.md` actor catalogue — `product-owner-ba`, `solution-architect`, `azure-principal-architect`, `infrastructure-devops`, `security-engineer`, `compliance-auditor`, `data-engineer`, `ai-ml-engineer`, `qa-test-engineer`, `sre-engineer`, `ux-designer`, `accessibility-tester`. `status:` validated. `preconditions:` none.
- **PER-076** [non-AU placeholder]: capstone-country operator personas — Philippines (NDRRMC), Japan (Cabinet Office DRR / FDMA / JMA liaison), Bangladesh (DDM / CPP volunteers). `status:` placeholder. `preconditions:` D-009 capstone-reinterpretation decision; SME validation per FR-023.

## Hypotheses

- **HYP-026**: If feature `028-capstone-alignment` lands the four mandatory H2 sections, the meta-flag bullets, the metric trace, and the overlap reciprocal pointers across all 27 specs, then the AMA rubric mean for the five hardened criteria (Assumptions / Requirements / Personas / Hypotheses / Scope) rises from the **1.8/5** baseline at `specs/028-capstone-alignment/evidence/rubric-baseline.md` to **>= 2.8/5** post-feature with no per-criterion regression. **Falsification**: post-feature rubric snapshot shows mean < 2.8 or any criterion regresses. **Evidence stub**: `specs/028-capstone-alignment/evidence/HYP-026.md` (created in T038 of polish phase).

