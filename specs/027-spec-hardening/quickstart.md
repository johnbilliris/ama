# Quickstart: Capstone Specification Hardening

**Feature**: 027-spec-hardening
**Audience**: Planner / test lead / UX lead reviewing whether the capstone specification is internally coherent and testable.

This quickstart walks through verifying success criteria SC-001 .. SC-010 by inspection only. Every step is a read-only action against files under `specs/` and `.github/`. No runtime deployment is required.

## Prerequisites

1. Clone the repo and check out branch `027-spec-hardening`.
2. Have `pnpm` installed (for `markdownlint-cli2`) and `pwsh` 7+ (for Spec-Kit scripts).
3. Have read access to the GitHub repo (so CODEOWNERS resolution can be verified).

## Walkthrough

### 1. Confirm Assumptions are registered and signed (SC-001, FR-001, FR-034)

1. Open `specs/001-disaster-response-hub/spec.md` and jump to `## Assumptions`.
2. Confirm every row has non-empty `basis`, `drafter`, `countersigner`, `status`, and `last_reviewed`.
3. Pick one row with `status = Validated`. Confirm `countersigner` names a member of the `specs/001-disaster-response-hub/` CODEOWNERS team (see `.github/CODEOWNERS`).
4. Confirm every `ASM-###` referenced from any FR in spec 001 has a matching row in `## Assumptions`.

### 2. Confirm NFRs carry targets, basis, and signed authority (SC-002, FR-004 .. FR-013, FR-035)

1. In spec 001, jump to `## NFRs`.
2. Confirm every row has non-empty `target`, `basis`, `drafter`, `sme_countersigner`, and `measurement_method`.
3. Confirm every row whose `category ∈ {Privacy, Security, Data-Residency}` has `privacy_reviewer ≠ "N/A"`.
4. Confirm every row whose `category ∈ {Interoperability, Accessibility}` has a `standard_reference` (e.g. CAP 1.2, EDXL-DE 2.0, WCAG 2.2 AA).

### 3. Confirm Personas cover AIIMS functions and vulnerable archetypes (SC-003, SC-004, FR-014 .. FR-017)

1. Open each persona profile (either inlined in spec 001 `## Personas` or filed under `specs/001-disaster-response-hub/personas/`).
2. Confirm at least one persona per AIIMS function (Control / Intelligence / Planning / Operations / Logistics / Public Information).
3. Confirm CALD, accessibility-impaired, and tourist archetypes are present.
4. Confirm every profile has `validated_by` with at least one SME or practitioner entry (proxy alone fails FR-016).

### 4. Confirm Hypotheses are falsifiable and have Evidence Pack stubs (SC-005, SC-006, FR-018 .. FR-021)

1. In spec 001 `## Hypotheses`, pick a row.
2. Confirm `statement`, `falsification_criterion`, and `method` are all non-empty.
3. Follow the row's `evidence_pack` link. Confirm the file exists on disk.
4. Open the file. Confirm it has the six required sections and that the front-matter `status` matches the row's `status`.
5. Repeat for a second row with a *different* status (e.g., one `Not tested` and one `Validated`).

### 5. Confirm Scope boundaries are explicit (SC-007, FR-022 .. FR-030)

1. In spec 001 `## Scope`, confirm the following subsections exist:
   - **v1 Primary Jurisdiction** (single named Australian state or territory).
   - **Deferred-Scope Register** (at least one row with `target_feature` filled).
   - **Autonomy Boundary Table** (every operational decision classified Human-in-the-loop / Advisory / Autonomous).
   - **Hazard List** (bushfire, flood, cyclone, severe storm with operational definitions and AIDR links).
   - **Citizen-Surface List** (what citizens see vs. not in v1).
   - **Upstream/Downstream Integrations** (BoM, State SES/RFS/VICSES, ABC Emergency, AWS, etc.).

### 6. Confirm Traceability Table is canonical in 027 and pointed to from 001 (SC-008, FR-031, Clarification 10)

1. Open `specs/027-spec-hardening/spec.md` and jump to `## Traceability Table`.
2. Confirm the row count equals the non-Withdrawn row count of `specs/shared/gap-id-register.md`.
3. Open `specs/001-disaster-response-hub/spec.md` `## Changelog`. Confirm it carries a pointer row to the 027 Traceability Table and does not duplicate the table itself.

### 7. Confirm Open Deltas block downstream plan-phase entry (SC-009, FR-032, Clarification 5)

1. Open spec 001 `## Open Deltas`.
2. For each row with `status ≠ Resolved`, note the `target_feature` value.
3. Confirm that none of those `target_feature` IDs correspond to features whose `plan.md` already exists (`ls specs/<target-feature>/plan.md`).
4. Confirm every Open Delta also appears in the 027 Traceability Table.

### 8. Confirm the Gap-ID register is monotonic and covers all cited gaps (SC-010, FR-036)

1. Open `specs/shared/gap-id-register.md`.
2. Confirm IDs are monotonic within each category prefix (no gaps, no reuse).
3. Run a grep for `A-GAP-|REQ-GAP-|PER-GAP-|HYP-GAP-|SCP-GAP-` across `specs/001-disaster-response-hub/` and `specs/027-spec-hardening/`. Confirm every unique hit appears in the register.

### 9. Confirm CODEOWNERS entry is in place (FR-034, Clarification 6)

1. Open `.github/CODEOWNERS`.
2. Confirm the line `specs/001-disaster-response-hub/ @<team-handle>` is present (team handle, not individual).
3. Confirm the team exists on GitHub by visiting the org-page URL from the handle.

### 10. Run the lint and verification gate

```pwsh
pnpm exec markdownlint-cli2 "specs/027-spec-hardening/**/*.md" "specs/001-disaster-response-hub/spec.md" "specs/shared/gap-id-register.md" ".github/CODEOWNERS"
```

Expect: zero errors. Warnings about line length in tables may be whitelisted in `.markdownlint.jsonc` if not already.

The companion verification script (authored in Phase 2) performs the automated equivalents of steps 1–8 and exits non-zero on any invariant breach. Run it via:

```pwsh
pwsh -File scripts/verify-spec-hardening.ps1
```

(Script path is a Phase 2 task; the plan only reserves the location.)

## Expected outcome

If steps 1–10 all pass, the capstone spec is certified as hardened against the A-GAP / REQ-GAP / PER-GAP / HYP-GAP / SCP-GAP review. Any failure surfaces as a Gap register row (Open) and, if it blocks a downstream feature, an Open Delta row with `blocking_phase = plan`.
