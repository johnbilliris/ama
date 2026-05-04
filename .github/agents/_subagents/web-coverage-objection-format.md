# Web-coverage objection format (spec 034)

> Authoritative format for sub-agent objections under
> `.github/agents/_subagents/`. Mirrors
> `specs/034-webapp-capstone-coverage/contracts/agent-objection.schema.json`.
> Copy `scripts/web-coverage/agent-objection-template.json` next to your
> `{agent-id}.agent.md` to file an objection in the next tribunal cycle.

## Required fields

| Field              | Type                                   | Notes                                                                                       |
| ------------------ | -------------------------------------- | ------------------------------------------------------------------------------------------- |
| `agent_id`         | string (kebab-case)                    | Must match the `{agent-id}.agent.md` filename stem.                                         |
| `panel`            | `operational \| sector \| technical`   | The panel this agent belongs to (Q13).                                                      |
| `cycle`            | integer 0..4                           | Iteration cycle being voted on (FR-024 cap is 3).                                           |
| `gap_id`           | string `GAP-...`                       | Must reference an existing row in `gap-register.json`.                                       |
| `vote`             | `approve \| object \| abstain`         | Only `object` requires a non-empty `rationale`.                                             |
| `rationale`        | string                                 | One sentence citing the FR / clause being violated.                                         |
| `touched_personas` | array of persona ids                   | Personas the gap impacts; must intersect the gap's `affected_personas`.                     |
| `touched_frs`      | array of FR ids (`FR-001`..`FR-027`)   | Must intersect the gap's `fr_ids`.                                                          |
| `touched_clauses`  | array of clause ids (`I`..`X`, `NN-*`) | Must intersect the gap's `constitution_clauses`.                                            |
| `evidence_uris`    | array of URIs (>= 1)                   | CI run links, PR diffs, or audit-log permalinks supporting the rationale.                   |
| `recorded_at`      | ISO-8601 UTC                           | Generated automatically by `review-log.py vote`; can be omitted in the human-authored form. |

## Workflow

1. Sub-agent emits a `{agent_id}.objection.json` next to its agent card.
2. `review-log.py vote` validates the JSON against the contract schema and
   appends the row to `review-log.json`.
3. `review-log.py panel` resolves all objections for one panel x cycle:
   - **Meritorious** if >= 2/3 of the relevant panel approves.
   - **Operational-panel veto** on any objection touching safety-critical
     clauses {I, IV, NN-1, NN-2, QG-1}.
   - **Override** if >= 50% + 1 of all 85 agents sustain a veto.
4. Resolutions emit `specs/034-.../diffs/cycle-{N}/{gap_id}.md` PR stubs that
   `web-coverage-iteration.yml` opens as a single follow-up PR per night.

## Anti-patterns

- Filing an objection without `evidence_uris` — the panel resolver treats it
  as `pending` until evidence is provided.
- Citing FRs/clauses that are *not* on the gap row — the schema's
  intersection rule rejects the JSON.
- Voting `object` with an empty `rationale` — the contract requires a
  one-sentence cite.
