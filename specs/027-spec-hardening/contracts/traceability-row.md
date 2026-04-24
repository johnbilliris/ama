# Template: Traceability Table row

Satisfies FR-031 and Clarification 10. Copy into the `## Traceability Table` of `specs/027-spec-hardening/spec.md`. This is the **canonical** location; `specs/001-disaster-response-hub/spec.md` carries only a pointer row in its `## Changelog`.

## Column order

`gap_id | short_title | category | resolved_by | evidence_pack | status`

## Row template

```markdown
| <Gap ID> | <short title ≤120 chars> | <Assumption\|Requirement\|Persona\|Hypothesis\|Scope> | <FR-### or NFR-### or § anchor in spec 001> | <relative link to Evidence Pack OR `—`> | <Open\|In-progress\|Resolved\|Withdrawn> |
```

## Example

```markdown
| HYP-GAP-004 | Evacuation acceptance latency unmeasured | Hypothesis | FR-018; [HYP-003](../001-disaster-response-hub/spec.md#hypotheses) | [evidence/HYP-003.md](../001-disaster-response-hub/evidence/HYP-003.md) | In-progress |
| A-GAP-007 | Controllers' acceptance of system recommendations unstated | Assumption | [ASM-001](../001-disaster-response-hub/spec.md#assumptions) | — | Resolved |
```

## Validation rules

1. Row count equals the non-Withdrawn row count of `specs/shared/gap-id-register.md`.
2. `status` matches the Gap register row for the same `gap_id` (cross-file invariant).
3. `category = Hypothesis` ⇒ `evidence_pack` is non-empty.
4. `resolved_by` must resolve to an existing anchor in spec 001.
5. This table must not be duplicated in spec 001; the changelog pointer row is the only spec-001-side reference.
