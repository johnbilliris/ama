# Template: Gap-ID register row

Satisfies FR-036 and Clarification 8. Copy into `specs/shared/gap-id-register.md`. The register is monorepo-wide, append-only, and monotonic.

## Column order

`gap_id | category | short_title | raised_by | raised_in_feature | status | owning_feature | evidence_link`

## Row template

```markdown
| <prefix-###> | <Assumption\|Requirement\|Persona\|Hypothesis\|Scope> | <short title ≤120 chars> | <Name, Role> | <feature directory, e.g. `027-spec-hardening`> | Open | unassigned | — |
```

## Category → prefix mapping (normative)

| Category | Prefix |
| --- | --- |
| Assumption | `A-GAP-` |
| Requirement | `REQ-GAP-` |
| Persona | `PER-GAP-` |
| Hypothesis | `HYP-GAP-` |
| Scope | `SCP-GAP-` |

Suffixes are zero-padded three digits (`001`, `002`, ..., `999`). The next allocated ID in a category is `max(existing_suffix) + 1`; no renumbering, no reuse, no withdrawn-ID recycling.

## Example

```markdown
| A-GAP-007 | Assumption | Controllers' acceptance of system recommendations unstated | J. Reviewer, Principal Architect | 027-spec-hardening | Resolved | 001-disaster-response-hub | [ASM-001](../001-disaster-response-hub/spec.md#asm-001) |
| HYP-GAP-004 | Hypothesis | Evacuation acceptance latency unmeasured | J. Reviewer, Principal Architect | 027-spec-hardening | In-progress | 001-disaster-response-hub | [HYP-003](../001-disaster-response-hub/evidence/HYP-003.md) |
```

## Validation rules

1. `gap_id` is unique across the whole register (not just within a category).
2. Within each category prefix, suffixes are strictly monotonic — a missing number fails validation.
3. Rows are never deleted. Status transitions are made in place.
4. A `status = Resolved` row MUST have non-empty `owning_feature` AND non-empty `evidence_link`.
5. Every Gap ID cited anywhere under `specs/` MUST appear here.
