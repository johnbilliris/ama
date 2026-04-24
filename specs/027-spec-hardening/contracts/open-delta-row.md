# Template: Open Delta row

Satisfies FR-032 and Clarification 5. Copy into the `## Open Deltas` table of `specs/001-disaster-response-hub/spec.md`.

## Column order

`delta_id | description | source_section | target_feature | blocking_phase | status | resolution_link`

## Row template

```markdown
| DELTA-### | <one-sentence description of the contradiction or dependency> | <§ anchor in spec 001> | <feature ID, e.g. `028-holistic-spec-hardening`> | plan | Open | — |
```

## Allowed `blocking_phase` values

`plan`, `tasks`, `implementation`. Default = `plan` per Clarification 5.

## Allowed `status` values

`Open`, `Accepted`, `Resolved`, `Withdrawn`.

## Examples

```markdown
| DELTA-002 | Public alert retention conflicts between FR-013 (7 years) and §Privacy (Privacy Act default 5 years for personal identifiers). | §NFRs NFR-006 | 028-holistic-spec-hardening | plan | Open | — |
| DELTA-005 | Evacuation routing currently classified Autonomous in FR-025 but HITL in constitution Non-Negotiable #1. | §Scope/Autonomy Boundary Table | 001-disaster-response-hub | plan | Resolved | [PR #4312](https://example.com/pr/4312) |
```

## Validation rules

1. `/speckit.plan` for a feature whose ID equals `target_feature` MUST refuse to proceed while any row with that `target_feature` has `blocking_phase = plan` AND `status ≠ Resolved`.
2. Rows with `status = Resolved` MUST have a non-empty `resolution_link` (PR URL or commit SHA).
3. Every Open Delta row MUST also have a matching Traceability Table row in `specs/027-spec-hardening/spec.md`.
4. `target_feature` MUST resolve to a directory under `specs/` OR carry the literal value `unassigned` (which itself blocks `plan` phase of any feature that later claims ownership).
