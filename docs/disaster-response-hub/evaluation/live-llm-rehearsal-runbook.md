# Live LLM Rehearsal Runbook

This runbook validates the real Azure OpenAI-backed quickstart flow for rubric task T052.

## Prerequisites

Set these environment variables in the shell where tests are executed:

- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_REASONING_DEPLOYMENT`
- `AZURE_OPENAI_DRAFTING_DEPLOYMENT`

Optional (recommended):

- `AZURE_OPENAI_API_VERSION`

## Execute

From the repository root:

```powershell
python -m pytest tests/simulation/test_quickstart_live_llm_rehearsal.py -q
```

## Expected outcome

- Test passes with `generation_method == "llm"` for both risk recommendation and communication draft.
- Response metadata includes deployment id and token usage.

## Troubleshooting

- If test is skipped, one or more required environment variables are missing.
- If test fails with authorization/404, verify deployment names and API key scope.
- If test falls back to simulation, verify endpoint and deployment values are correct and reachable.
