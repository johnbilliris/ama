# Template: Assumption row

Satisfies FR-001, FR-002, FR-003, FR-034. Copy into the `## Assumptions` table of `specs/001-disaster-response-hub/spec.md`.

## Column order

`assumption_id | statement | basis | test | owner | drafter | countersigner | status | last_reviewed | linked_gaps`

## Row template

```markdown
| ASM-### | <single declarative sentence> | <citation, e.g. "AIIMS-5 §4.2" or "SME interview 2026-04-18"> | <how it would be invalidated> | <Name, Role> | <Name, Role> | <Name, Role — CODEOWNERS team member> | Proposed | YYYY-MM-DD | <comma-separated Gap IDs, or `—`> |
```

## Example

```markdown
| ASM-001 | Incident Controllers will accept system-generated evacuation recommendations when rationale and data provenance are surfaced inline. | AIDR Evacuation Planning Handbook (2023) §5.4; SME interview with NSW RFS Supt. 2026-04-18. | Two rehearsal runs in which Controllers reject ≥50% of recommendations despite inline rationale. | Program Owner | A. Chen, Product Lead | B. Okafor, Spec Maintainer | Proposed | 2026-04-24 | A-GAP-007 |
```

## Status lifecycle

```text
Proposed → Validated | Invalidated | Withdrawn
```

Any transition out of `Proposed` requires the `drafter` AND `countersigner` cells to be non-empty at the time of the PR merge. Transitions overwrite the previous status; prior status is visible via git history only.

## Validation rules (enforced by the verification script)

1. `assumption_id` is unique within spec 001 and monotonic (no gaps).
2. `basis`, `drafter`, `countersigner`, `status`, `last_reviewed` are non-empty.
3. `last_reviewed` is a valid ISO-8601 date (`YYYY-MM-DD`) no older than 12 months at the time of the verification run for any row with `status = Validated`.
4. Every `ASM-###` referenced from a functional requirement body in spec 001 has a matching row here.
