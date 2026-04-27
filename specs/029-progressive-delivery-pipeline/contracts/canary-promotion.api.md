# Contract: Canary Promotion Control Surface

**Source**: spec.md FR-007, FR-008, FR-009, FR-010, FR-011, FR-024. This document pins the inputs, decision logic, and emitted events for the `canary_controller.py` tool that drives every production promotion.

## Inputs

- `service`: one of `api` | `agents` | `ingestion` | `web`
- `digest`: OCI digest of the artefact under promotion (must verify per FR-005 before any traffic shift)
- `environment`: `staging` | `production`
- `start_stage`: usually `5`; rollback resumes from `last_known_good`

## Per-stage observation windows (Q1)

| Stage | Window | Sample threshold |
|-------|--------|------------------|
| 5 %   | 10 min | per-service `min_sample_threshold` |
| 25 %  | 15 min | per-service `min_sample_threshold` |
| 50 %  | 30 min | per-service `min_sample_threshold` |
| 100 % | 60 min | per-service `min_sample_threshold` |

## Decision logic (per stage)

```
poll burn-rate every 60 s for window_minutes:
  if any SLO is in fast_burn (>= 5% budget in 1h):
      decision = rollback  → FR-008
      shift traffic to last_known_good
      emit audit event canary.rollback (outcome=success)
      open evidence pack outcome=rollback
      stop
  if any SLO is in slow_burn (>= 10% budget in 6h):
      decision = hold       → FR-009
      open tracked issue, emit audit canary.hold
      do NOT advance; do NOT rollback unless fast-burn later fires
  if telemetry insufficient (FR-024):
      decision = hold
      emit audit canary.hold (outcome=denied), reason=insufficient_data
      do NOT advance; await operator confirmation

after window_minutes elapsed with all SLOs healthy and samples >= threshold:
  decision = advance
  emit audit canary.advance (outcome=success)
  shift traffic to next stage entry %
```

## Freeze behaviour

If the singleton `Change Freeze` document in `pipeline_state` becomes `state=active` mid-stage, the controller:
- Holds traffic at the current stage % (no advance, no rollback unless fast-burn fires)
- Emits audit `canary.hold` with `correlation_id = <freeze incident id>`
- Resumes from the same stage when the freeze is deactivated (queue order preserved per FR-011)

## Rollback target — known-good selection (FR-008 / Q3)

```
SELECT artefact
FROM artefacts
WHERE service = $service
  AND last_known_good_at IS NOT NULL
  AND superseded_by IS NULL
  AND verification_status = 'verified'
ORDER BY last_known_good_at DESC
LIMIT 1
```

If no such row exists (e.g., very first deploy), the controller MUST FAIL CLOSED and escalate to a human (no traffic shift to an unverified target).

## Emitted events

For every decision the controller writes:
1. An `Audit Event` (see audit-event.schema.json) with `action ∈ {canary.advance, canary.hold, canary.rollback}`, `service`, `environment`, `stage_pct`, `digest`.
2. A `Canary Stage` row in `pipeline_state` with the burn-rate snapshot.
3. (On terminal stage success or rollback) Triggers `evidence-pack.yml` with the full per-stage history.
