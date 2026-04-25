# Contract: Meta / Delivery-Hygiene Spec Flag

**Feature**: `028-capstone-alignment`
**Scope**: applies to the closed set of meta specs defined in FR-020.

## Applicable specs

`003, 004, 007, 013, 016, 017, 024, 025, 026, 027, 028` (11 specs).

Capstone-critical-path (complement): `001, 005, 006, 008, 009, 010, 011, 012, 014, 015, 018, 019, 020, 021, 022, 023` (16 specs). Union = 27; partition disjoint and total.

## Required bullet

Each meta spec MUST include, inside its `## Out of Scope` section, exactly this declarative bullet (verbatim template, with `[list]` filled in):

```markdown
- This spec is delivery-hygiene / enabling infrastructure; capstone-outcome-critical-path ownership lives in specs [list].
```

Where `[list]` is the subset of capstone-critical-path specs this spec enables. For general-purpose hygiene specs (e.g., 003, 027), `[list]` MAY be "all capstone-critical-path specs".

## Validation rule

```text
For each spec in {003, 004, 007, 013, 016, 017, 024, 025, 026, 027, 028}:
  assert grep -c "^- This spec is delivery-hygiene" specs/NNN-*/spec.md == 1
```

## Rationale

Rubric evaluators need to separate capstone-value specs from delivery-hygiene specs in a single pass. See User Story 4, SC-008.
