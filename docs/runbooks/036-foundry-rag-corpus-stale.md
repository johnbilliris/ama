# Runbook — Corpus Stale Alert (Spec 036 Phase F-A8)

> **Trigger**: `corpus_stale` Service Bus event + on-call PagerDuty page.
>
> **Severity**: `yellow` for `corpus_age_days ∈ [14, 17)`, `red` for
> `corpus_age_days >= 17`. (UI freshness indicator goes yellow at 7 days
> and red at 14 days — that's a separate signal.)
>
> **SLO**: corpus freshness restored within **24 hours** of red alert per
> FR-RAG-FRESH-02.

This runbook covers the four common stale causes per Plan §F-A8.5:

1. [Corpus repo stalled](#cause-1-corpus-repo-stalled)
2. [Ingest pipeline failing](#cause-2-ingest-pipeline-failing)
3. [Cron misconfigured](#cause-3-cron-misconfigured)
4. [Parity gate blocking](#cause-4-parity-gate-blocking)

## When the page fires

You are on-call. PagerDuty has paged you with the payload from
`staleness_alert.schema.json`. The payload includes:

- `corpus_build_sha` — points at the manifest currently aliased.
- `corpus_age_days` + `last_ingest_run_age_hours` — drives severity.
- `feature_flag_state` — confirms whether `feature.corpus_freshness_alert.enabled`
  is enabled (red flag if it's been disabled by an actor you don't recognise).

## Pre-flight diagnostics

1. **Verify the alert** — query the latest `corpus_freshness_state` audit
   event in the Eval workspace. Confirm `is_stale: true`. If false, the
   alert was a transient and PagerDuty can be acknowledged.
2. **Check feature flag** — confirm
   `feature.corpus_freshness_alert.enabled = true` in the audit log. If it
   was recently disabled by an unknown actor, escalate to security ops
   immediately AND treat the staleness as real.
3. **Pull the manifest** —
   ```
   az search index show --service-name srch-ama --name corpus-current
   ```
   Note the alias target (`corpus-v{N}`) for use below.

## Cause 1 — corpus repo stalled

**Symptoms**: ingest cron last ran within 48h (`last_ingest_run_age_hours < 48`)
but the manifest age has grown past 14 days. Ingest is succeeding but no new
chunks are being committed.

**Diagnosis**:
- Check `docs/corpus/source.json` for new entries since the last successful
  manifest. If the repo is stalled, every recent run will report
  `no_drift_detected`.
- Cross-reference with `docs/corpus/aidr/decisions/` — has a fresh ADR
  authored a chunk-schema change that hasn't yet landed?

**Remediation**:
1. Open a tracking issue with the corpus owner and AFAC liaison.
2. Manually rebuild the corpus from a known-good state:
   ```pwsh
   pwsh -ExecutionPolicy Bypass -File infra/scripts/blue-green-flip.ps1 `
     -NewIndexName "corpus-v$(Get-Date -Format yyMMddHHmm)" -DryRun
   ```
3. If dry-run is OK, drop `-DryRun` and execute. Confirm the manifest age
   resets and the alert clears within ~10 minutes.

## Cause 2 — ingest pipeline failing

**Symptoms**: `last_ingest_run_age_hours >= 48`. Recent ingest cron runs
are red in `.github/workflows/corpus-ingest.yml`.

**Diagnosis**:
- Pull the most recent ingest workflow run; look for failures in the
  embedder, chunker, or Cosmos sink steps.
- Common failures:
  - **Foundry quota exhausted** — see `docs/runbooks/036-foundry-rag-gameday.md`.
  - **`validate_chunk_metadata` rejected a chunk** — Phase F lint refuses
    the build if `agency`/`agency_role`/`authority_level`/`cultural_*`
    invariants fail. Check the build artefact for `chunk_*` errors.
  - **AI Search 503** — transient; retry with exponential back-off; see
    `docs/runbooks/036-foundry-rag-blue-green-rollback.md`.

**Remediation**:
1. Fix the upstream cause.
2. Re-run `Re-run failed jobs` on the workflow.
3. Confirm `last_ingest_run_at` updates and the alert clears.

## Cause 3 — cron misconfigured

**Symptoms**: cron schedule no longer matches `"0 14 * * *"` (UTC) /
`0100 AEST`. `last_ingest_run_age_hours` grows >24h despite the corpus
being healthy.

**Diagnosis**:
- Inspect `.github/workflows/corpus-ingest.yml` — was the cron expression
  recently edited?
- Check the GitHub Actions cron last-run timestamp.

**Remediation**:
1. Restore the cron to `"0 14 * * *"`.
2. Manually trigger one nightly run to break the staleness window.
3. Re-confirm by reviewing the next cron firing (~24h later).

## Cause 4 — parity gate blocking

**Symptoms**: ingest succeeds and writes to a new `corpus-v{N+1}`, but the
alias is NOT flipped because the parity-replay gate (T222) reported <95%
byte-identical replay. The old alias remains pinned to the stale index.

**Diagnosis**:
- Check `tests/e2e/test_blue_green_alias_flip.py` parity-replay output in
  the most recent CI run.
- Compare top-N retrieval results from old vs new index using
  `tests/fixtures/golden-set-v1.json`.
- A common cause: an embedding model upgrade changes ranking enough to
  drop replay below 95%. This is intentional fail-safe behaviour.

**Remediation**:
- If the drop is INTENTIONAL (e.g., deliberate model upgrade), authorise
  the alias flip out-of-band per `docs/runbooks/036-foundry-rag-blue-green-rollback.md`.
- If the drop is UNINTENTIONAL, halt the rollout, restore the previous
  manifest, and escalate to the corpus owner.

## Post-remediation

1. Confirm via `corpus_freshness_state` audit that `is_stale: false`.
2. Acknowledge PagerDuty; close the incident.
3. If the cause was a process gap, file a `lessons` entry per spec 029
   progressive-delivery review cadence.
4. If the cause was a tool defect (e.g., cron mis-config that snuck through
   review), open a CI guardrail issue.

## Related runbooks

- `docs/runbooks/036-foundry-rag-gameday.md` — game-day chaos drill.
- `docs/runbooks/036-foundry-rag-blue-green-rollback.md` — alias-flip
  rollback inside the 5-minute SLO.

## Change log

| Date       | Change                                              | Author             |
|------------|-----------------------------------------------------|--------------------|
| 2026-XX-XX | Initial draft (T217 / Plan §F-A8.5)                  | Implementation     |
