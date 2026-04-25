# Contract: `evidence/HYP-*.md` stub

**Feature**: `028-capstone-alignment`
**Producers**: any feature introducing a new `HYP-###`.
**Consumers**: rubber-duck reviewers; SC-005 / FR-015 automated checks; downstream features promoting `Not tested` → `Validated`.

## File location

`specs/NNN-<short-name>/evidence/HYP-<id>.md` — co-located with the owning spec.

## Required structure (six H2 headings, in this order)

```markdown
# HYP-### — <short title>

## Hypothesis
<Restates the hypothesis in the spec-027 FR-018 format:
"We believe {capability} will produce {outcome} for {persona};
we will know we are wrong if {leading indicator} is observed in {measurement window}.">

## Preconditions
- <precondition 1>
- <precondition 2>
<!-- ≥ 2 bullets required -->

## Measurement Window
<A named capstone season or bounded window. Examples:
"PH typhoon season Jun–Nov"; "JP continuous; quarterly review"; "BD monsoon Apr–Sep".>

## Falsification Criterion
- <quantified threshold — if observed, hypothesis is falsified>
<!-- ≥ 1 quantified threshold required -->

## Status
Not tested

## Linked
- Spec: `specs/NNN-<short-name>/spec.md`
- SC: <optional>
- ASM: <optional>
- Other HYP: <optional>
```

## Validation rules

1. All six H2 headings present exactly as named (case-sensitive).
2. `## Preconditions` has ≥2 bullet items.
3. `## Falsification Criterion` has ≥1 bullet with a numeric threshold or explicit boolean test.
4. `## Status` body contains exactly `Not tested` (case-sensitive) at creation time.
5. `## Linked` cites at least the owning spec.
6. Filename matches `HYP-\d{3}.md` and aligns with the HYP ID in the register.

## Minimal example (skeletal but compliant)

```markdown
# HYP-042 — PH fil-PH language-pack misinformation detection

## Hypothesis
We believe that adding a fil-PH language pack to the Communication Agent will produce a ≥85% true-positive detection rate on known misinformation samples for Filipino-speaking communities during a PH typhoon landfall event; we will know we are wrong if true-positive rate < 70% is observed across any validation sample during PH typhoon season Jun–Nov.

## Preconditions
- PH NDRRMC data-sharing MoU signed.
- fil-PH training corpus reviewed by ≥1 native-speaker content-safety reviewer.

## Measurement Window
PH typhoon season Jun–Nov.

## Falsification Criterion
- True-positive rate < 70% on the labelled fil-PH validation corpus.

## Status
Not tested

## Linked
- Spec: `specs/008-communication-agent/spec.md`
- ASM: `specs/005-data-source-governance/spec.md` ASM-0XX (PH DPA 2012 compliance)
```

## Change control

- Only the owning spec's feature branch may modify the stub while `Status = Not tested`.
- Transition to `Validated | Falsified | Retired` requires a separate spec-numbered feature and must update this file plus the gap-id register.
