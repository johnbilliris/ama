# Phase 1 Data Model: Capstone Alignment Hardening

**Feature**: `028-capstone-alignment`
**Date**: 2026-04-24
**Note**: This is a documentation-only feature. "Entities" are Markdown artefacts, not database rows. No runtime schemas are introduced.

## Entity Inventory

### E-001: Spec

- **Location**: `specs/NNN-<short-name>/spec.md` plus sibling artefacts (`research.md`, `tasks.md`, `evidence/`, `checklists/`, `contracts/`).
- **Identity**: three-digit zero-padded number `NNN` + kebab-case short name. Immutable under FR-022.
- **Required fields after this feature**:
  - `## Assumptions` (≥3 entries, each tagged `[TESTABLE|DECISION|RISK]`)
  - `## Personas` (≥2 personas OR ≥2 x-refs to spec-001 personas)
  - `## Hypotheses` (≥1 hypothesis in spec-027 FR-018 format)
  - `## Out of Scope` (≥3 items, ≥1 deferring a capstone country or hazard)
- **Classification**: `{capstone-critical-path | delivery-hygiene}` — closed partition defined in FR-020 (D-008).
- **Relationships**:
  - references → `specs/shared/gap-id-register.md` (for ASM/HYP/PER/SCP/REQ IDs)
  - may declare `supersedes: <spec>:<section>` or `defers-to: <spec>` pointers

### E-002: Assumption (ASM)

- **ID family**: `ASM-###`, globally monotonic in `specs/shared/gap-id-register.md`.
- **Fields**:
  - `id`: `ASM-###`
  - `tag`: `TESTABLE | DECISION | RISK`
  - `statement`: ≤ 2 sentences
  - `drafter`: role/persona (per spec-001 taxonomy)
  - `countersigner`: different role (per spec-001 taxonomy)
  - `status`: `open | accepted | retired`
  - `linked_gaps`: list of related IDs
  - `country_cohorts`: subset of `{AU-v1, PH, JP, BD}` — default `{AU-v1}`; non-AU entries default to `deferred`
- **Validation**: every new ASM must cite at least one capstone metric, hazard, country cohort, or privacy regime it affects (or explicitly `n/a` with justification).

### E-003: Hypothesis (HYP)

- **ID family**: `HYP-###`, globally monotonic.
- **Statement format** (spec-027 FR-018): *"We believe {capability} will produce {outcome} for {persona}; we will know we are wrong if {leading indicator} is observed in {measurement window}"*.
- **Fields**:
  - `id`: `HYP-###`
  - `owning_spec`: `NNN`
  - `country_cohort`: one of `{AU-v1, PH, JP, BD}` (required)
  - `capstone_metric`: optional link to one of five capstone metrics
  - `evidence_stub`: relative path to `evidence/HYP-<id>.md` (required, D-006)
  - `status`: must be `Not tested` at creation
- **State transitions**: `Not tested → In evaluation → Validated | Falsified | Retired`. Only `Not tested` is introduced by this feature.

### E-004: Persona (PER)

- **ID family**: `PER-###`, globally monotonic.
- **Contract**: YAML front-matter schema defined in `specs/027-spec-hardening/contracts/persona-profile.md` (reused, not redefined).
- **Validation status**: `validated | placeholder` (FR-023). Every non-AU persona added by this feature MUST carry `status: placeholder` with explicit promotion preconditions.
- **Relationship**: a Persona may be referenced by multiple Specs via cross-reference rather than duplication.

### E-005: Out-of-Scope Item (SCP)

- **ID family**: `SCP-###`, globally monotonic.
- **Fields**:
  - `id`: `SCP-###`
  - `statement`: what is explicitly not in scope
  - `country_scope`: subset of `{AU-v1, PH, JP, BD}` (default: all)
  - `promotion_preconditions`: list of conditions that must be met before this item re-enters scope (required when `country_scope` includes non-AU cohorts)

### E-006: Requirement (REQ)

- **ID family**: `REQ-###`, globally monotonic. (Note: each spec keeps local `FR-###` numbering for readability; REQ-### is used only when allocating a new canonical cross-portfolio requirement in the gap-id register.)
- **Relationship**: every FR introduced by this feature that adds cross-spec behaviour is mirrored by a REQ-### allocation.

### E-007: Capstone Metric

- **Closed enum**:
  - `LIVES_SAVED` — 1,000+ lives/yr
  - `RESPONSE_SPEED` — 50% faster response
  - `EVAC_LEAD_TIME` — 24 h earlier evacuation
  - `LOGISTICS_EFFICIENCY` — 30% logistics efficiency
  - `ECONOMIC_LOSS_REDUCTION` — 30% economic loss reduction
- **Relationship**: every metric has ≥1 SC-owner spec and ≥1 HYP-owner spec in `specs/shared/capstone-metric-trace.md` (SC-002).

### E-008: Country Cohort

- **Closed enum**: `AU-v1 | PH | JP | BD`.
- **Default scope**: `AU-v1`.
- **Deferred cohorts** (PH/JP/BD) carry promotion preconditions documented in the owning Assumption or Out-of-Scope Item.

### E-009: Capstone Hazard

- **Closed enum**: `typhoon (PH) | earthquake (JP) | riverine/cyclone-driven flood (BD)` layered over constitution-defined AU hazards (bushfire, cyclone, flood, earthquake, tsunami, storm, extreme heat, pandemic).
- **Owner**: spec 012 (risk assessment) holds the hazard taxonomy; downstream agent specs declare applicability per cohort.

### E-010: Privacy-Law Regime

- **Closed enum**: `AU_PRIVACY_ACT_1988 | JP_APPI | PH_RA10173_DPA2012 | BD_ICT2006_DRAFT_DPA2023` (plus regional: `SG_PDPA_2012`, `MY_PDPA_2010`, for reference only).
- **Owner**: spec 005 (data source governance) under FR-007.
- **Non-AU entries**: all marked deferred with promotion preconditions.

### E-011: Cross-Agency Protocol

- **Placeholder enum**: `AU_AIIMS (spec 018) | PH_NDRRMC_NDRP | JP_CABINET_DM_PLAN | BD_SOD_2019 | ASEAN_AHA_SASOP`.
- **Owner**: spec 018 for AIIMS; others are reference placeholders only.

### E-012: Capstone Metric Trace Row

- **Container**: `specs/shared/capstone-metric-trace.md` (single Markdown table).
- **Primary key**: (Metric, Country Cohort). Exactly 5 × 4 = 20 rows.
- **Columns**: `Metric | Country Cohort | SC Owner | HYP Owner | Baseline | Measurement Method | Status`.
- **Status**: `Validated | Deferred | Unresolved` — `Unresolved` MUST reach zero before feature closeout.

### E-013: Gap-ID Register Entry

- **Container**: `specs/shared/gap-id-register.md`.
- **Invariant**: monotonic append-only. Every new ASM/HYP/PER/SCP/REQ ID MUST be strictly greater than the prior max in its family. SC-007 verifies this by diff against pre-feature HEAD.

---

## Relationships (summary)

```text
Spec (1) ─── owns ──▶ (0..*) Assumption / Hypothesis / Persona / Scope / Requirement
Hypothesis (1) ─── has ──▶ (1) Evidence Stub
Hypothesis (0..*) ─── references ──▶ (0..1) Capstone Metric
Assumption/Hypothesis/Scope (0..*) ─── scoped to ──▶ (1..*) Country Cohort
Country Cohort (1) ─── aligns with ──▶ (0..*) Capstone Hazard / Privacy Regime / Cross-Agency Protocol
Capstone Metric Trace Row ◀── (5×4) ─── Capstone Metric × Country Cohort
Gap-ID Register ─── allocates ──▶ (1) unique ID per Assumption / Hypothesis / Persona / Scope / Requirement
```

## Validation rules summary

| Rule | Source | Mechanism |
| --- | --- | --- |
| Every spec has 4 mandatory H2 sections | FR-001–004, SC-001 | Grep |
| Evidence stub has 6 fixed H2 headings | D-006, FR-015 | Grep + structural check |
| Every capstone metric × cohort has a trace row | FR-013, SC-002 | Row-count check (=20) + Owner cell regex |
| No existing ID renumbered | FR-022, SC-007 | `git diff` against baseline |
| Non-AU personas tagged `placeholder` | FR-023 | YAML front-matter regex |
| SC-009 composite gate | D-007 | `ama-rubric-grader` skill vs baseline snapshot |
