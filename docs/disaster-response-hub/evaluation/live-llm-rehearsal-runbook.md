# Live LLM Rehearsal Runbook

This runbook validates the real Foundry-backed quickstart flow for rubric task T052.

## Prerequisites

Set these environment variables in the shell where tests are executed:

- `AMA_LIVE_REHEARSAL=1` (explicit opt-in; without this the test intentionally skips)
- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_AI_PROJECT_DEPLOYMENTS`
- `AZURE_AI_REASONING_DEPLOYMENT`
- `AZURE_AI_DRAFTING_DEPLOYMENT`

Optional (recommended):

- `AZURE_AI_PROJECT_REGION`

Authentication:

- Use Microsoft Entra ID / managed identity (DefaultAzureCredential).
- Do not provide an API key for this rehearsal path.

## Execute

From the repository root:

```powershell
python -m pytest tests/simulation/test_quickstart_live_llm_rehearsal.py -q
```

## Expected outcome

- Test passes with `generation_method == "llm"` for both risk recommendation and communication draft.
- Communication draft includes all six languages (`en-AU`, `zh-Hans`, `ar`, `vi`, `el`, `it`).
- No template fallback modes are accepted in this rehearsal.
- End-to-end rehearsal completes in under 30 seconds.

## Troubleshooting

- If test is skipped, `AMA_LIVE_REHEARSAL` is not set to `1`.
- If `AMA_LIVE_REHEARSAL=1` and prerequisites are missing, the test fails by design.
- If test fails with authorization/404, verify Entra identity access and Foundry deployment names.
- If fallback modes appear, verify Foundry endpoint/deployment map reachability and model health.
