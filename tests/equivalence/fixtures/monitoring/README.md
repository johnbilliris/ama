# Monitoring agent equivalence fixtures (T036)

Each fixture file conforms to:

```json
{
  "case_id": "...",
  "input": { ... },
  "legacy_output": { ... },
  "maf_output": { ... }
}
```

The equivalence harness in `apps/agents/maf_runtime/equivalence/runner.py`
loads every `*.json` here, runs both outputs through `scorers.py`, and emits a
PASS/FAIL verdict per FR-023 (≥95% categorical decision match + 100% populated
schema match; free-text fields excluded).

Real fixtures captured from the per-agent shadow phase will be added during
the cutover playbook (`docs/aidr/runbooks/maf-cutover-playbook.md`, T069).
The single smoke fixture committed today (`smoke-fire-escalate.json`) proves
the harness wiring works end-to-end.
