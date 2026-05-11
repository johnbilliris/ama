# ADR-036-006: Lessons-Capture Blob WORM with 7-Year Legal Hold

**Status**: Accepted
**Deciders**: Security Architect, Cloud Architect, Data Architect
**Date**: 2026-05-08
**Spec**: 036-sim-agent-extend
**FR coverage**: FR-054, FR-055
**Constitution**: AU Residency (NN-2), Audit-and-Provenance

## Context

The Australian Institute for Disaster Resilience (AIDR) post-exercise
artefacts are subject to **7-year retention** under the AFAC Doctrine
on Lessons Management. The simulation realm produces an
`ExerciseOutcomeRecord` (per `data-model.md §5`) at the end of every
simulation, regardless of `end_reason` (`completed | aborted |
timeout`). The record MUST be:

1. **Immutable** for at least 7 years (84 months).
2. **AU-resident** (Constitution NN-2) — Australia East primary,
   Australia Central secondary; cross-region replication MUST stay
   within the AU residency boundary.
3. **Idempotent** — `record_id == simulation_id` (FR-055) so a re-run
   yields the same blob and never duplicates.

## Decision

Persist the `ExerciseOutcomeRecord` JSON to a **dedicated Azure Storage
Blob container** (`exercise-outcome-records`) configured for:

- **Immutability policy**: time-based retention, 84 months, *unlocked*
  initially so deletes are reversible during the on-prem soak window
  (per AFAC Doctrine §6.4); the policy is automatically locked by the
  CI workflow `.github/workflows/foundry-carveout-review-6mo.yml`
  after the soak (T+30 days).
- **Legal hold tag**: `LegalHold=true` written at upload time, removed
  only by the `Simulation.RegulatoryAdmin` AAD role.
- **AU-resident region pair**: AU East (RA-GRS) primary, AU Central
  secondary. Cross-region replication is within the AU residency
  boundary per Constitution NN-2.
- **Tier**: Hot during the active-exercise window (≤30 days), then
  Cool, then Archive after 1 year. The lifecycle policy is encoded
  in `infra/bicep/modules/lessons-capture-storage.bicep`.

The Cosmos `exercise_outcome_index` container mirrors the blob URI +
metadata for low-latency lookups (no Blob list scan). PK is
`/simulationId`, document id == `record_id`. Idempotency is preserved
by both layers.

The post-exercise read API
(`GET /api/simulations/{simId}/outcome`) returns a **short-TTL signed
URL** (15 min default) so the blob is never exposed publicly.

## Consequences

- The 7-year retention overshoots the simulation realm's typical
  3-year archive window — but is required by AIDR alignment.
- A Blob WORM legal-hold removal requires the
  `Simulation.RegulatoryAdmin` role plus a documented disposition
  authority (per AFAC Doctrine §7).
- The `lessons_capture.generate()` callable accepts a `BlobUploader`
  parameter so unit tests exercise the same logic without an Azure
  storage account.

## Alternatives considered

- **Cosmos-only persistence (no Blob)** — rejected: Cosmos cost grows
  with retention; auditors and regulators expect immutable file
  artefacts, not database documents.
- **Confidential Ledger** — rejected: AU residency story incomplete at
  spec lock; revisit in a future ADR if Confidential Ledger gains GA
  in `australiaeast`.
- **Locked immutability from t=0** — rejected: would prevent fix-ups
  during the on-prem soak; AFAC permits unlocked policies for the
  first 30 days.

## Linked artefacts

- `apps/api/app/services/simulation/lessons_capture.py`
- `infra/bicep/modules/lessons-capture-storage.bicep`
- `data/governance/foundry_carveout_registry.json`
- `.github/workflows/foundry-carveout-review-6mo.yml`
