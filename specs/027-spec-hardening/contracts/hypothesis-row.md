# Template: Hypothesis row

Satisfies FR-018 .. FR-021. Copy into the `## Hypotheses` table of `specs/001-disaster-response-hub/spec.md`.

## Column order

`hypothesis_id | statement | falsification_criterion | method | linked_decision | owner | status | evidence_pack`

## Row template

```markdown
| HYP-### | If X then Y because Z | <observable condition that would invalidate the statement> | rehearsal \| telemetry \| A/B \| expert-review | <FR-### or NFR-### or § anchor> | <Name, Role> | Not tested | [evidence/HYP-###.md](./evidence/HYP-###.md) |
```

## Example

```markdown
| HYP-003 | If evacuation recommendations are surfaced with provenance-weighted confidence intervals, then Incident Controllers will accept them within 3 minutes of activation because uncertainty is made legible rather than hidden. | ≥2 rehearsals with median acceptance time > 6 minutes, or <40% acceptance at first presentation. | rehearsal | FR-011; NFR-004 | A. Chen, Product Lead | Not tested | [evidence/HYP-003.md](./evidence/HYP-003.md) |
```

## Allowed `status` values

`Not tested`, `Under validation`, `Validated`, `Invalidated`, `Withdrawn`.

## Validation rules

1. The file at the `evidence_pack` path **exists** at the moment the row is merged (FR-020, Clarification 9).
2. The Evidence Pack front-matter `status` equals the row `status`.
3. `falsification_criterion` is an observable condition — untestable aspirations (e.g., "users love it") fail validation.
4. `method` is a bounded enum; free-form methods fail validation.
5. `linked_decision` resolves to a defined FR / NFR ID within spec 001.
