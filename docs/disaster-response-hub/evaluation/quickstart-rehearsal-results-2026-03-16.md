# Quickstart Rehearsal Results — 2026-03-16

## Scope

- Feature: `003-rubric-gap-closure`
- Objective: Execute quickstart rehearsal flow and record validation outcomes for implementation review.
- Evidence status: historical rehearsal snapshot only; not a complete current-revision acceptance bundle.

## Executed Validation

1. Python full suite
   - Command: `./.venv/Scripts/python.exe -m pytest tests -q`
   - Result: **PASS** (31 passed)
   - Qualification: historical and incomplete denominator for the current test corpus; cannot be used as a blanket SC pass claim.
2. Playwright E2E suite
   - Command: `corepack pnpm --filter ./apps/web exec playwright test --workers=1 --timeout=60000`
   - Result: **PASS** (6 passed)
3. Quickstart rehearsal simulation
   - Command: `./.venv/Scripts/python.exe -m pytest tests/simulation/test_quickstart_rehearsals.py -q`
   - Result: **PASS**
4. Live Foundry rehearsal gate
   - Command: `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; .\\apps\\agents\\.venv\\Scripts\\python.exe -m pytest tests/simulation/test_quickstart_live_llm_rehearsal.py -q`
   - Result: **SKIP** (required Foundry environment variables not set)

## Notes

- Local environment has no production Foundry credentials configured, so rehearsal evidence is based on simulation and fallback-safe pathways validated by contract/integration tests.
- Live rehearsal command and runbook are prepared in `docs/disaster-response-hub/evaluation/live-llm-rehearsal-runbook.md` for immediate execution once credentials are provisioned.
- Playwright required serial execution (`--workers=1`) to avoid local dev-server contention and navigation timeouts.
- This report must be paired with `specs/003-rubric-gap-closure/evidence-manifest.json` for per-SC status (`PASS`, `UNVERIFIED`, `SKIP`) and attributable revision-bound evidence.

## Outcome

- Quickstart rehearsal evidence is recorded for local implementation verification.
- Remaining external-environment activity: provision real Foundry test credentials and rerun live LLM rehearsal for full production-equivalent validation.
