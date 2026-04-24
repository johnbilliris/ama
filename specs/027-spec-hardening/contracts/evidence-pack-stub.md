# Template: Evidence Pack stub

Satisfies FR-020 and Clarification 9. Copy to `specs/<owning-feature>/evidence/<HYP-ID>.md` at the moment the hypothesis row is created. The stub is overwritten in place on every status transition; prior content moves into `## History`.

## File template

```markdown
---
hypothesis_id: HYP-###
owning_feature: 001-disaster-response-hub
status: Not tested
last_reviewed: YYYY-MM-DD
drafter: "<Name, Role>"
countersigner: "<Name, Role — CODEOWNERS team member>"
---

# Evidence Pack: HYP-###

## Statement

<Verbatim copy of the hypothesis statement from spec.md>

## Falsification Criteria

<Verbatim copy of the falsification criterion from spec.md>

## Method

<One sentence: rehearsal / telemetry / A/B / expert-review — specify the concrete instrument.>

## Evidence

<Empty for `status = Not tested`. Populated with links to rehearsal transcripts, telemetry exports, A/B analyses, or expert-review memos as the hypothesis is tested.>

## Decision

<Empty until status transitions out of `Not tested`. When populated: one paragraph stating the conclusion and any follow-on action.>

## History

| Date | From → To | PR | Drafter | Countersigner | Note |
| --- | --- | --- | --- | --- | --- |
| YYYY-MM-DD | — → Not tested | <PR link> | <Name, Role> | <Name, Role> | Stub created. |
```

## Validation rules

1. File exists on disk at hypothesis-row merge time (FR-020, Clarification 9).
2. Front-matter `status` equals the hypothesis row's `status` at all times.
3. `## History` is strictly append-only; existing rows must not be deleted or rewritten.
4. Status transitions into `Validated` or `Invalidated` require non-empty `## Evidence` and non-empty `## Decision`.
5. Status transitions into any state other than `Not tested` require both `drafter` and `countersigner` to be non-empty (FR-034).
