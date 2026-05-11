# Spec 038 — Evidence Harness chaos-drill runbook (T-G06)

> Validates FR-027 / FR-032 graceful degradation across three failure
> modes. **Dev / staging only — never run against production.**

## Pre-conditions

- Local Cosmos emulator + Azurite running (see
  `specs/040-success-criteria/quickstart.md` §1).
- `evidence-harness-slo` workbook importable in App Insights.
- 2 %/h burn-rate alerts enabled (informational); 5 %/h alerts armed (page-out).

## Experiment 1 — Cosmos 429 throttle on `kpi_signals`

```powershell
python -m apps.api.scripts.chaos_evidence --experiment cosmos_429 --container kpi_signals --duration 120
```

**Expected**: `degraded_mode_entered` audit rows accumulate; 2 %/h informational
alert fires within 5 min; 5 %/h does NOT fire; replay endpoint continues to
serve scorecards with `reduced_fidelity=true`.

**Rollback**: stop the script; throttle clears within 60s; verify
`evidence_audit` no longer accrues degraded entries.

## Experiment 2 — AOAI timeout during Measurement-Method summarisation

```powershell
python -m apps.api.scripts.chaos_evidence --experiment aoai_timeout --duration 60
```

**Expected**: `GET /api/v1/evidence/measurement-method` still returns
deterministic markdown (FR-027 — `summary unavailable` reduced-fidelity tag).

**Rollback**: stop the script; LLM summariser resumes on next request.

## Experiment 3 — App Insights ingestion lag

```powershell
python -m apps.api.scripts.chaos_evidence --experiment appi_lag --duration 90
```

**Expected**: `evidence-harness-slo` workbook surfaces metric-freshness
breach alert; no evidence dropped; `degraded_mode_entered` audit rows emitted.

**Rollback**: stop the script; ingestion catches up; freshness alert clears.

## Drill cadence

- Quarterly in dev; monthly in staging during SRE on-call rotation.
- Outcomes recorded in the spec-037 evidence pack via T-Z04.
