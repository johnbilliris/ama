# Phase 1 Data Model: Capstone Specification Hardening

**Feature**: 027-spec-hardening
**Date**: 2026-04-24

This feature has no runtime entities. The "data model" for a documentation-hardening feature is the set of **state-bearing markdown rows** that its deliverables produce or update. Each section below specifies one entity: its purpose, fields, status lifecycle, and the FR(s) it satisfies. Every row is rendered as a markdown table cell in the target artefact; field order below is the canonical column order.

A row is valid if and only if every `required` field is non-empty and every enum field contains an allowed value. The `## Validation` subsection on each entity states the machine-checkable invariants the Phase 2 verification script must enforce.

---

## E-1. Gap (row in `specs/shared/gap-id-register.md`)

**Purpose**: Single source of truth for every gap raised during spec reviews across the monorepo.

**Satisfies**: FR-036, FR-031, Clarification 8.

**Fields**:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `gap_id` | enum prefix + 3-digit suffix | Y | `A-GAP-###`, `REQ-GAP-###`, `PER-GAP-###`, `HYP-GAP-###`, `SCP-GAP-###`. Monotonic across the monorepo; never reused. |
| `category` | enum | Y | Assumption / Requirement / Persona / Hypothesis / Scope. |
| `short_title` | string | Y | ≤ 120 chars. |
| `raised_by` | string | Y | Name, role. |
| `raised_in_feature` | string | Y | Feature directory name (e.g. `027-spec-hardening`). |
| `status` | enum | Y | Open / In-progress / Resolved / Withdrawn. |
| `owning_feature` | string | Y | Feature directory name that resolves the gap; `"unassigned"` while Open. |
| `evidence_link` | relative URL | N | Link to Evidence Pack or resolving PR. |

**Status lifecycle**:

```text
Open → In-progress → Resolved
Open → Withdrawn
In-progress → Withdrawn
```

A *Withdrawn* row is retained; the ID is never reused. A *Resolved* row's `evidence_link` must be non-empty.

**Validation**:

1. `gap_id` is unique across the register.
2. The numeric suffix within a category is monotonic (no gaps permitted).
3. Every gap cited in any `specs/*/spec.md` appears here.
4. A row with `status = Resolved` has non-empty `evidence_link` and non-empty `owning_feature`.

---

## E-2. Assumption (row in `specs/001-disaster-response-hub/spec.md § Assumptions`)

**Purpose**: Named, testable claim about the domain / environment / user behaviour that the design depends on.

**Satisfies**: FR-001, FR-002, FR-003, FR-034.

**Fields**:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `assumption_id` | `ASM-###` | Y | Monotonic within spec 001. |
| `statement` | string | Y | Single declarative sentence. |
| `basis` | citation | Y | AIIMS / AIDR reference, published study, or internal SME record. |
| `test` | string | Y | How the assumption would be invalidated. |
| `owner` | string | Y | Name, role. |
| `drafter` | string | Y | Name, role (FR-034). |
| `countersigner` | string | Y | Name, role — CODEOWNERS team member (FR-034). |
| `status` | enum | Y | Proposed / Validated / Invalidated / Withdrawn. |
| `last_reviewed` | ISO-8601 date | Y | |
| `linked_gaps` | list of Gap IDs | N | |

**Status lifecycle**: `Proposed → Validated | Invalidated | Withdrawn`. Any transition requires both `drafter` and `countersigner` signatures to be set in the row *at the time of the transition*; the fields are overwritten (not appended) on subsequent transitions.

**Validation**:

1. Every `ASM-###` cited elsewhere in spec 001 or spec 027 appears here.
2. No status transition without non-empty `drafter` and `countersigner`.

---

## E-3. NFR (row in `specs/001-disaster-response-hub/spec.md § NFRs`)

**Purpose**: Non-functional requirement with a citable target and signed accountability chain.

**Satisfies**: FR-004 .. FR-013, FR-035.

**Fields**:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `nfr_id` | `NFR-###` | Y | Monotonic within spec 001. |
| `category` | enum | Y | Performance / Reliability / Security / Privacy / Accessibility / Interoperability / Observability / Data-Residency / Cost. |
| `statement` | string | Y | |
| `target` | string | Y | Numeric or enumerated value with units. |
| `basis` | citation | Y | Standard, benchmark, regulatory text, or SME judgement. |
| `drafter` | string | Y | Name, role. |
| `sme_countersigner` | string | Y | Name, role. |
| `privacy_reviewer` | string | Y | Name + role, OR `"N/A"` if category ∉ {Privacy, Security, Data-Residency}. |
| `standard_reference` | string | N | E.g. CAP 1.2, EDXL-DE 2.0, ISO 27001, WCAG 2.2 AA, Sendai B-2. Required when category = Interoperability or Accessibility. |
| `measurement_method` | string | Y | How target compliance is measured in the runtime. |

**Validation**:

1. No row with `category ∈ {Privacy, Security, Data-Residency}` may carry `privacy_reviewer = "N/A"`.
2. `category ∈ {Interoperability, Accessibility}` requires a non-empty `standard_reference`.
3. `target` is a well-formed number-with-units OR a bounded enum value — never prose.

---

## E-4. Persona (profile file in `specs/001-disaster-response-hub/personas/<persona-id>.md` OR single-row block in spec 001 § Personas)

**Purpose**: Named operator / community archetype with validated authority, AIIMS function, and representative evidence.

**Satisfies**: FR-014, FR-015, FR-016, FR-017.

**Fields** (required in every persona profile, regardless of whether the profile is inlined or filed):

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `persona_id` | `PER-###` | Y | |
| `display_name` | string | Y | |
| `aiims_function` | enum | Y | Control / Intelligence / Planning / Operations / Logistics / Public Information / Non-AIIMS-Community / Non-AIIMS-Governance. |
| `role_basis` | citation | Y | AIIMS-5, AIDR handbook, or community-archetype study. |
| `jurisdiction_scope` | string | Y | `v1-primary` / `deferred` / `national`. |
| `authority_scope` | string | Y | What the persona may authorise unilaterally vs. what requires countersign. |
| `validated_by` | list | Y | Each entry = name + role + validation date (SME, practitioner, or proxy) (FR-016). |
| `representative_scenarios` | list | Y | ≥ 1 link to a scenario in spec 001 or the rehearsal library. |
| `accessibility_needs` | string | Y | Or `"Not applicable — operator persona"`. |

**Validation**:

1. At least one persona per AIIMS function exists (SC-004).
2. `validated_by` has ≥ 1 entry where `role ∈ {SME, practitioner}` (proxy alone is insufficient per FR-016).
3. Persona roster includes the CALD, accessibility-impaired, and tourist archetypes required by FR-015(c)(d)(e).

---

## E-5. Hypothesis (row in `specs/001-disaster-response-hub/spec.md § Hypotheses`)

**Purpose**: Falsifiable claim whose validation underpins a design decision or success metric.

**Satisfies**: FR-018, FR-019, FR-020, FR-021.

**Fields**:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `hypothesis_id` | `HYP-###` | Y | |
| `statement` | string | Y | Declarative sentence in the form "If X then Y because Z". |
| `falsification_criterion` | string | Y | Observable condition that would invalidate the statement. |
| `method` | string | Y | How the hypothesis is to be tested (rehearsal / telemetry / A/B / expert review). |
| `linked_decision` | string | Y | FR, NFR, or design decision that the hypothesis underpins. |
| `owner` | string | Y | Name, role. |
| `status` | enum | Y | Not tested / Under validation / Validated / Invalidated / Withdrawn. |
| `evidence_pack` | relative URL | Y | Must point at `evidence/<HYP-ID>.md` — file exists at creation time. |

**Status lifecycle**: `Not tested → Under validation → Validated | Invalidated | Withdrawn`. Every transition updates both the row `status` and the Evidence Pack file's `status` field in lock-step.

**Validation**:

1. `evidence_pack` resolves to an existing file on disk at row creation (FR-020, Clarification 9).
2. For every row with `status = Validated`, the evidence pack's `## Evidence` section is non-empty.
3. `linked_decision` resolves to a defined FR / NFR ID within the same spec.

---

## E-6. Evidence Pack (file at `specs/<owning-feature>/evidence/<HYP-ID>.md`)

**Purpose**: Durable audit artefact backing a hypothesis status.

**Satisfies**: FR-020, Clarification 9.

**File front-matter (YAML)**:

```yaml
---
hypothesis_id: HYP-###
owning_feature: 001-disaster-response-hub
status: Not tested | Under validation | Validated | Invalidated | Withdrawn
last_reviewed: YYYY-MM-DD
drafter: "Name, Role"
countersigner: "Name, Role"
---
```

**Required markdown sections**:

1. `## Statement` — restates the hypothesis verbatim.
2. `## Falsification Criteria` — restates the falsification criterion verbatim.
3. `## Method` — names the test (rehearsal / telemetry / A/B / expert review).
4. `## Evidence` — body of evidence; may be empty when `status = Not tested`.
5. `## Decision` — one paragraph describing the conclusion and any follow-on action.
6. `## History` — append-only log of prior statuses with date, transition, and PR link.

**Validation**:

1. File exists for every `HYP-###` cited in spec 001 from the moment the hypothesis row is merged.
2. Front-matter `status` equals the row status in spec 001.
3. `## History` grows monotonically (entries appended, never deleted).

---

## E-7. Scope Boundary Entry (row in `specs/001-disaster-response-hub/spec.md § Scope`)

**Purpose**: Named scope statement making v1 reach explicit.

**Satisfies**: FR-022, FR-024, FR-025, FR-027, FR-028, FR-029.

**Fields**:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `boundary_id` | `SCP-###` | Y | |
| `boundary_type` | enum | Y | Jurisdiction / Hazard / Citizen-Surface / Autonomy-Classification / Integration-Upstream / Integration-Downstream / Recovery. |
| `in_scope_v1` | boolean | Y | |
| `statement` | string | Y | |
| `rationale` | string | Y | Why in or out. |
| `target_feature` | string | N | Required when `in_scope_v1 = false` AND `boundary_type ∈ {Jurisdiction, Hazard, Citizen-Surface, Recovery}`. |

**Validation**:

1. Every boundary with `in_scope_v1 = false` and a jurisdiction / hazard / citizen-surface / recovery type has a `target_feature`.
2. At least one `boundary_type = Jurisdiction` row exists with `in_scope_v1 = true`.
3. At least one `boundary_type = Hazard` row exists per capstone hazard (bushfire, flood, cyclone, severe storm) with `in_scope_v1 = true`.

---

## E-8. Deferred-Scope Entry (row in spec 001 § Scope / Deferred-Scope Register)

**Purpose**: Authoritative list of out-of-scope items with re-evaluation triggers.

**Satisfies**: FR-023, FR-028, Clarification 5.

**Fields**:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `deferred_id` | `DEF-###` | Y | |
| `kind` | enum | Y | One of `Jurisdiction`, `Hazard`, `Capability`, `Surface`, `Integration` (FR-023). |
| `item` | string | Y | Jurisdiction, hazard, capability, surface, or integration name. |
| `reason_deferred` | string | Y | |
| `target_feature` | string | Y | Feature ID that will address it (may be `"unassigned"`). |
| `re_evaluation_trigger` | string | Y | Condition that forces re-evaluation. |

**Validation**:

1. Every Deferred-Scope Entry appears in the Gap-ID register with category = Scope.
2. No Deferred-Scope Entry contradicts a Scope Boundary Entry (i.e., no row appears as both in-scope and deferred).

---

## E-9. Open Delta (row in `specs/001-disaster-response-hub/spec.md § Open Deltas`)

**Purpose**: Contradiction or unresolved dependency that must be settled before a downstream plan phase.

**Satisfies**: FR-032, Clarification 5.

**Fields**:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `delta_id` | `DELTA-###` | Y | |
| `description` | string | Y | |
| `source_section` | string | Y | Section of spec 001 where contradiction was found. |
| `target_feature` | string | Y | Feature that must resolve it. |
| `blocking_phase` | enum | Y | plan / tasks / implementation. Per Clarification 5, default = `plan`. |
| `status` | enum | Y | Open / Accepted / Resolved / Withdrawn. |
| `resolution_link` | relative URL | N | Required when `status = Resolved`. |

**Validation**:

1. When `blocking_phase = plan` and `status ≠ Resolved`, `/speckit.plan` on the `target_feature` must refuse to proceed.
2. Every Open Delta is also referenced in the 027 Traceability Table.

---

## E-10. Traceability Link (row in `specs/027-spec-hardening/spec.md § Traceability Table`)

**Purpose**: Canonical mapping from every gap to the requirement or section that resolves it.

**Satisfies**: FR-031, Clarification 10.

**Fields**:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `gap_id` | Gap ID | Y | |
| `short_title` | string | Y | |
| `category` | enum | Y | Same enum as Gap. |
| `resolved_by` | string | Y | FR-### / NFR-### / § anchor in spec 001. |
| `evidence_pack` | relative URL | N | Required when `category = Hypothesis`. |
| `status` | enum | Y | Must match the row in `specs/shared/gap-id-register.md`. |

**Validation**:

1. Row count equals the number of non-Withdrawn rows in the Gap-ID register.
2. Status matches the gap register row (cross-file invariant).
3. Every `resolved_by` value resolves to an existing anchor in spec 001.

---

## Cross-entity invariants (verification-script responsibilities)

1. **Gap closure symmetry** — every Gap register row with `status = Resolved` has exactly one Traceability Table row.
2. **Hypothesis-Evidence lockstep** — a hypothesis row's status equals its Evidence Pack front-matter status.
3. **Signature presence** — no Assumption / Hypothesis / Persona status transition is merged without non-empty drafter + countersigner fields.
4. **Scope consistency** — no Deferred-Scope Entry contradicts a Scope Boundary Entry.
5. **Plan-phase ordering** — no `/speckit.plan` run for a feature whose ID appears in an unresolved Open Delta with `blocking_phase = plan`.
