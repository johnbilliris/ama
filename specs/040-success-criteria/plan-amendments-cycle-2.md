# Implementation Plan — Amendments Cycle 2: 040-success-criteria

**Branch**: `040-success-criteria` | **Date**: 2026-05-11
**Scope**: AMD-01..AMD-13 → FR-038..FR-050 / SC-014..SC-022 only.
**Continues from**: [`plan.md`](./plan.md) (FR-001..FR-037 / SC-001..SC-013 — UNCHANGED).
**Driving inputs**: spec.md *Amendments — Cycle 2* block, *Clarifications — Cycle 2 R1+R2*, [`checklists/amendments-cycle-2.md`](./checklists/amendments-cycle-2.md) CHK069..CHK152.

> This is a **delta**. The base plan (Phase 0/1 design, container layout,
> reuse posture, six-pillar module structure, capstone-trace tagging step)
> remains authoritative. Anything not amended below stands as written.

---

## Summary of the delta

Cycle 2 hardens four cross-cutting invariants without changing the
six-pillar module shape, the seven-Cosmos-container layout, or the route
structure under `apps/web/src/app/governance/evidence/`:

1. **Audit immutability** — Blob lock pinned to `state=Locked` /
   `2,555 days`; PATCH/DELETE on `evidence_audit` returns
   `409 Conflict + ProblemDetails(title="audit-record-immutable")` and
   appends a tampering-attempt audit row in the same transaction
   (FR-038, FR-040, SC-014, SC-016).
2. **AU-residency hardening** — Bicep deploy-time `existing.location`
   assertion against `{australiaeast, australiasoutheast}`; production
   fail-fast on missing AU credentials guarded by `AMA_TEST_MODE=1`
   sentinel; per-operation `Strong` consistency on the AU-refusal audit
   write with bounded 3-retry exponential backoff and `503` on
   exhaustion (FR-042, FR-043, FR-044, SC-018, SC-019, SC-020(a)).
3. **Operability** — `/healthz/evidence` partitioned into critical
   (Cosmos containers + Blob immutable archive + change-feed mirror →
   `503` when down) vs non-critical (App Insights + read-only cache →
   `200 + degraded:true`); SLO horizon = rolling 30 d, burn windows =
   rolling 1 h, severities pinned (5 %/h ⇒ Sev 1, 2 %/h ⇒ Sev 2),
   `sloAlertActionGroupId` mandatory in non-test environments
   (FR-045, FR-046, SC-020(b), SC-021).
4. **Schema rigour & live UX** — Pydantic v2 `extra="forbid"` on every
   evidence model (`422` on unknown fields); TS twin remains type-only,
   asserted by an OpenAPI-driven contract test (no Zod, no
   class-validator); `language_fallback_used: "<from>→<to>"` field on
   PI render responses with paired UI badge; jurisdictional benchmark
   seed ≥32 + cross-sector ≥5 with mandatory `source_citation`; all
   seven governance/evidence tabs fetch live data on mount with the
   four state badges (`degraded`, `small-sample`, `manual`,
   `reduced-fidelity`) explicitly surfaced (FR-047, FR-048, FR-049,
   FR-050, SC-022(a)..(d)).

Pillar A also gains a non-optional 5×5 risk-adjustment matrix with
`(L=3, C=3)` graceful default and `provenance: manual` tag that counts
toward the FR-028 / SC-010 ≤50 % manual-row cap (FR-041, SC-017).

---

## Reuse audit (REUSE-ONLY constraint re-verified)

| Concern                                    | Reuses                                                                                                                                  | Net-new dep? |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| Pydantic v2 `extra="forbid"` (FR-047)      | Pydantic already in `apps/api/pyproject.toml`; `ConfigDict(extra="forbid")` is built-in.                                                | No           |
| TS twin parity (R2-Q1)                     | Reuses portfolio convention `packages/domain/src/app-role.ts` (type-only); contract test reuses existing `pytest`/OpenAPI test pattern. | No           |
| axe-core + Flesch-Kincaid (FR-039)         | Reuses Playwright + axe-core deps already installed by tasks T-A09/T-A10. FK readability = `textstat` (verify; if absent, use a 60-LOC Pyte-style helper inside the existing Playwright spec — no Python pkg). | **Action** — confirm `textstat` already transitive via existing dev deps; otherwise inline JS Flesch-Kincaid (no new dep, ≈40 LOC). |
| Cosmos change-feed → Blob mirror (FR-040)  | Container Apps **job** (`Microsoft.App/jobs@2024-03-01`) — pattern already used in `infra/bicep/modules/eval/eval-platform.bicep:390`. Storage change-feed already enabled on prior modules (`infra/bicep/modules/evidence-store.bicep:38`). | No           |
| Per-op Strong consistency (FR-044 / D21)   | Cosmos SDK request-options override `consistency_level=Strong` on `create_item`. No new SDK or wrapper.                                 | No           |
| 3-retry exp backoff (D21)                  | Reuses the resilience helper already wrapping Cosmos clients in `services/governance` (D9 in base research).                            | No           |
| SLO workbook + burn-rate alerts (FR-046)   | `Microsoft.Insights/scheduledQueryRules` + workbook resources — pattern used in existing `observability-alerts.bicep` precedent.        | No           |
| Healthz banding (FR-045)                   | Existing `/healthz/*` aiohttp pattern in `apps/api/app`; only re-partitions checks, no new dep.                                         | No           |
| Live tab fetch on mount (FR-050)           | Existing Next.js `useEffect`/SWR pattern already used by sibling `governance/executive` tabs; no new chart libs / primitives.           | No           |
| Benchmark seed ≥32 + ≥5 (FR-049)           | Static seed JSON loaded by existing `services/evidence/benchmarks/` Manager; citations are text fields — no external fetch.             | No           |
| PI render `language_fallback_used`         | Adds a field to the existing PI render response (new endpoint `GET /api/v1/evidence/public-information/{scenario_id}` defined under §Contract delta below) — reuses `apps/web/src/lib/i18n/language-packs.ts` lookup chain only. | No           |

**Net-new runtime dependencies introduced by Cycle 2**: **zero**.
**Net-new dev dependencies introduced by Cycle 2**: **conditional** —
only if `textstat` (or equivalent) is not already transitively
available; mitigated by a ~40 LOC inline Flesch-Kincaid implementation
(no package add). To be verified by the first Phase 4 task.

---

## Constitution Check (re-evaluated against the 11 gates)

Constitution version: **v1.2.0** (`.specify/memory/constitution.md`).
Same 11-row table as base plan, re-checked against the Cycle 2 delta:

| # | Principle / Gate                                     | Cycle 2 amendment touchpoint                                                                                                                                            | Pass? |
| - | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| 1 | I. Primacy of Life and Harm Reduction                | FR-041 `(L,C)` weighting still ranks below `life_safety_tier` ordering invariant (base data-model §Cross-entity invariants). Risk-adjusted view is a **rendering** add-on, not a re-rank of life-safety vs efficiency. | ✅ |
| 2 | II. National Emergency Management Principles (AEMA) | FR-049 benchmark seed encodes BoM warning lead-time per warning class (Watch / Warning / Severe / Emergency), NEMA COMDISPLAN, AIIMS span-of-control 3–7 — strengthens AEMA alignment. | ✅ |
| 3 | II-A. AIIMS Functional Alignment                     | Unchanged — AIIMS function tagging still required at ladder write-time.                                                                                                  | ✅ |
| 4 | III. Multi-Hazard, Multi-Agency Design               | FR-039 retains all 7 canonical scenarios; deferred-permitted Auslan scope (urban-fire, mass-casualty, hazmat, marine SAR) is **rendering** only — coverage matrix preserved with `auslan-asset-missing` badge. | ✅ |
| 5 | IV. Transparency and Auditability                    | FR-038 hardens immutability (`Locked` + 2555 d); FR-040 server-side rejection + tampering-attempt row; FR-044 durable-before-respond + 503 on audit-write failure; FR-045 critical/non-critical banding makes audit-store outage observable. **Strengthens** transparency. | ✅ |
| 6 | V. Warning and Public Information                    | FR-039 adds axe-core zero `serious`/`critical` and FK ≤ 8 thresholds; FR-048 forbids silent language downgrade. Aligns with Ten Warning Principles #3 (trusted, verifiable) and #8 (clearly communicated). | ✅ |
| 7 | AU Sovereignty (Non-Negotiable #2)                  | FR-042 production fail-fast; FR-043 deploy-time `existing.location` assertion against `{australiaeast, australiasoutheast}`; FR-044 single-region `australiaeast` for audit Cosmos to permit per-op `Strong`. **Strengthens** sovereignty. | ✅ |
| 8 | Advisory-only / human-in-the-loop                    | Unchanged — all amended endpoints remain advisory-only; `ProblemDetails.ama_advisory_only=true` invariant preserved.                                                    | ✅ |
| 9 | Graceful degradation                                 | FR-045 critical vs non-critical banding **codifies** what may degrade gracefully (App Insights, read-only cache) vs what must fail loudly (audit + AU-sovereignty path). FR-050 surfaces all 4 state badges to the operator. | ✅ |
|10 | Reuse-only / no new primitives                       | See §Reuse audit — zero new runtime deps; R2-Q1 explicitly forbids Zod/class-validator on the TS twin. FR-049 citations are static text — no scraping, no republishing of external benchmark data. | ✅ |
|11 | Capstone exclusion                                   | Unchanged — base plan §"Capstone-trace tagging step" still authoritative; Cycle 2 introduces no capstone-attribution change.                                            | ✅ |

**Result**: All 11 gates still pass post-amendment. **No violations** →
no entries added to base plan §Complexity Tracking.

---

## Contract / data-model / research delta — pointers

| Artefact                                     | Change                                                                                                                                                                                                                          |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`data-model.md`](./data-model.md)           | `IndicatorDefinition.risk_adjustment` made **required** with `(L=3, C=3)` graceful default + `manual` provenance contagion; `BenchmarkEntry.source_citation` typed as `CitationRef` (org+doc+year+url, all 4 mandatory); `AuditEntry.language_fallback_used` added (optional, only set on PI render replay rows). New §"Cycle 2 amendments" appended. |
| [`contracts/openapi.evidence-harness.yaml`](./contracts/openapi.evidence-harness.yaml) | `422` response added on every endpoint (Pydantic `extra=forbid`); `409` added on a new `evidence_audit` PATCH/DELETE pair (explicit reject endpoints) referencing FR-040; `503` added on every endpoint hitting the audit-write path **and** on `/healthz/evidence` when any critical store is down; new `language_fallback_used` field on the PI render schema; new `GET /api/v1/evidence/public-information/{scenario_id}` endpoint (was previously implicit via the `governance/evidence` PI tab). |
| [`research.md`](./research.md)               | Append `## Cycle 2 Decisions` block with D15..D28 (one decision per AMD plus the four cross-cutting clarifications). No prior D1..D14 row is mutated.                                                                            |
| [`checklists/amendments-cycle-2.md`](./checklists/amendments-cycle-2.md) | No change — already authoritative for CHK069..CHK152.                                                                                                                                                                            |
| [`tasks.md`](./tasks.md)                     | Out of scope of `/speckit.plan`; Cycle 2 tasks (T-A10..T-A14, T-AMD-*) are already enumerated and marked. This plan-amendment file provides the design rationale they cite.                                                     |

---

## Phase ordering for Cycle 2 work

Cycle 2 amendments are intentionally orthogonal to the base
six-pillar module structure, so they slot into the existing phase
ladder without re-ordering:

- **Phase 0 (Research delta)** — D15..D28 appended to `research.md`. No
  `NEEDS CLARIFICATION` items remain. (Performed by this command.)
- **Phase 1 (Design delta)** — `data-model.md` + `contracts/openapi.*`
  edits described above. (Performed by this command.)
- **Phase 2 (Tasks)** — Already exists in `tasks.md`; the Cycle 2 task
  block (T-AMD-01..T-AMD-13) maps 1:1 to AMD-01..AMD-13. No
  regeneration of `tasks.md` by `/speckit.plan`.
- **Phase 3 (Implementation)** — Driven by `/speckit.implement`. The
  REUSE audit table above is the contract.
- **Phase 4 (Validation)** — Driven by the existing T-Z* batch:
  contract tests over the amended OpenAPI; integration tests for
  `Strong`-consistency audit write under chaos; Playwright + axe-core +
  FK readability for FR-039; `az deployment group what-if` for
  FR-043 / FR-046 deploy-time assertions.

---

## Stop conditions

Per `/speckit.plan` contract this command stops after Phase 1 design
delta. `tasks.md` is not regenerated. The base plan file
[`plan.md`](./plan.md) is **not** rewritten — its FR-001..FR-037 design
remains the single source of truth, and this delta is read alongside
it.
