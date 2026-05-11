# Research: Measurable Success-Criteria Evidence Harness (spec 038)

**Branch**: `038-success-criteria` | **Date**: 2026-05-11
**Input**: `specs/038-success-criteria/spec.md`

All clarifications inside the spec (`Session 2026-05-11` Round 1 + Round 2) were
resolved against constitution v1.2.0 and the AIDR / ABS / AS-NZS source corpus.
This research file records the **technical** decisions that follow from those
clarifications — i.e. how the existing AMA stack will host the six-pillar
evidence harness without inventing new languages, frameworks, chart libraries,
or UI primitives.

No item below is left as `NEEDS CLARIFICATION`. Every decision cites the
spec FR / SC and the prior code/spec it reuses.

---

## D1. Backend service shape

- **Decision**: Implement the harness as a single backend module
  `apps/api/app/services/evidence/` exposed under FastAPI router prefix
  `/api/v1/evidence`. Six sub-modules — `kpi_ladder/`, `measurement/`,
  `simulation/` (replay orchestration), `impact/` (causal chains),
  `benchmarks/`, `instrumentation/` (audit + signal ingest) — one per
  spec pillar (FR-001..FR-028).
- **Rationale**: Mirrors the existing pillar-per-module pattern in
  `apps/api/app/services/eval`, `governance`, `ingestion`, `simulation`.
  Keeps deployment footprint inside the existing `ca-api-ama` Container
  App; no new container or function. Satisfies the user input
  *"Reuse the technology stack — do NOT invent new..."* and FR-013/FR-034.
- **Alternatives considered**:
  - Six separate microservices (one per pillar) — rejected: violates
    delivery-hygiene scope (FR-033) and requires six new Container Apps
    plus six independent deploys; no operational value at prototype tier.
  - Embed inside `apps/agents/*` — rejected: pillars are deterministic
    orchestration with no agent reasoning loop; LLM use is summarisation
    only (D6).

## D2. Persistence — Cosmos DB containers (AU-only)

- **Decision**: Add six new Cosmos DB SQL-API containers in the existing
  AU Cosmos account, declared via Bicep:
  | Container             | Partition key      | TTL / retention | Spec FR / SC anchor |
  | --------------------- | ------------------ | --------------- | ------------------- |
  | `kpi_ladder`          | `/kpi_id`          | none (versioned) | FR-001..FR-005     |
  | `kpi_signals`         | `/scenario_id`     | 90d hot, then cold-archive (D3) | FR-023..FR-024 |
  | `delta_scorecards`    | `/scenario_id`     | none            | FR-015, SC-003/004 |
  | `causal_chains`       | `/capability_id`   | none            | FR-017..FR-019     |
  | `benchmark_register`  | `/kpi_id`          | none            | FR-020..FR-022     |
  | `evidence_audit`      | `/audit_id`        | append-only ≥7y (D3) | FR-025..FR-026 |
  | `evidence_audit_dlq`  | `/audit_id`        | 30d             | FR-025 fault path  |
- **Rationale**: AU Cosmos region (`australiaeast` primary,
  `australiasoutheast` paired DR) satisfies FR-029 / SC-009. Per-entity
  partition keys keep query fan-out single-partition for the published
  endpoints (KPI ladder by `kpi_id`, replay scorecards by `scenario_id`,
  chains by `capability_id`). Append-only behaviour for `evidence_audit`
  is enforced at write-time by the service layer (no PATCH/DELETE) and
  surfaced to cold storage by Cosmos change-feed (D3).
- **Alternatives considered**:
  - Postgres / Azure SQL — rejected: AMA prototype already standardises
    on Cosmos for governance + simulation telemetry; no relational
    queries are required by any FR.
  - Single Cosmos container with `entity_type` discriminator — rejected:
    cross-entity hot-key risk on `scenario_id`, blunts partition-pruning
    for the per-pillar endpoints.

## D3. Long-term audit retention (FR-025, ≥7 years)

- **Decision**: 0–90 days hot in `evidence_audit` Cosmos container; from
  90 days, mirror via Cosmos change-feed → an Azure Storage Blob
  container (`evidence-audit-cold/`, **Cool** access tier, immutability
  policy with 7-year retention lock). Records remain retrievable via the
  `GET /api/v1/evidence/audit/{value_id}` endpoint, which falls through
  to the blob index when a record is older than 90 days.
- **Rationale**: Matches the user input ("Optional Azure Storage Blob
  (cool tier) for ≥7-year audit cold-archive (Q5 of clarifications)")
  and the spec Round 1 Q5 answer. Immutability lock satisfies the
  "append-only" intent of FR-025 against future tampering. AU region
  enforced by storage-account location pinning to `australiaeast`.
- **Alternatives considered**:
  - All-Cosmos retention — rejected: 7-year hot-tier RU cost is
    disproportionate for a prototype harness.
  - Archive tier — rejected: rehydrate latency (hours) breaks the
    SC-005 "<3 minutes audit walk" target for older records.

## D4. Simulation reuse for replay (FR-013, FR-014)

- **Decision**: The `evidence/simulation/` sub-module is an **orchestrator**
  over the existing simulation engine (specs 007/024/026); it does NOT
  embed a new engine. It calls the spec-026 warp-playback API with a
  fixed seed pair (baseline / AMA-assisted), captures emitted signals
  into `kpi_signals`, and computes the per-KPI delta scorecard via the
  bootstrap CI helper (D5). Determinism tolerance per FR-016 is
  evaluated at scorecard write-time (±2 % rel OR ±1 abs unit, whichever
  is greater).
- **Rationale**: FR-013 explicitly forbids a new engine. The orchestrator
  is the smallest unit needed to bind seeded runs to scorecards.
- **Alternatives considered**:
  - Re-use spec-024 chat orchestration end-to-end — rejected: chat
    introduces non-deterministic LLM turns, breaks SC-004 reproducibility.

## D5. Confidence-band computation (FR-009, FR-010)

- **Decision**: Implement bootstrap-95 % CI helper at
  `apps/api/app/services/evidence/measurement/confidence.py` using
  NumPy resampling (already a transitive dep of the simulation stack).
  Reuses the bootstrap pattern previously established for the spec-030
  LLM eval framework (`apps/agents/eval/confidence.py` — verify path at
  implementation time; if absent, port pattern from spec 030 plan/research).
  Default ≥1,000 resamples; <1,000 → fall back to ±1 SD with
  `small-sample` label per spec Round 1 Q2.
- **Rationale**: Aligns with spec Round 1 Q2 answer and FR-010 default;
  reuses existing dependency surface (no new wheels).
- **Alternatives considered**:
  - SciPy `bootstrap` — rejected: SciPy not currently in
    `apps/api/pyproject.toml`; adding it for a single helper violates
    the "reuse" constraint.
  - Parametric (normal-approx) CI — rejected: AIDR M&E Framework v2
    explicitly prescribes non-parametric for outcome indicators.

## D6. LLM use is summarisation-only (FR-036, advisory-only FR-030)

- **Decision**: LLM access is limited to plain-language summarisation
  inside `evidence/measurement/` (Measurement Method document
  rendering) and `evidence/impact/` (causal-chain narrative). All
  routing, scoring, and KPI math is deterministic Python. LLM client
  is the existing `apps/agents/common/llm_client.py`; retrieval (when
  used to ground summaries against AIDR / spec corpus) goes through the
  existing `apps/agents/common/retrieval_client.py`.
- **Rationale**: Matches user input *"deterministic orchestration only —
  no LLM-decided routing"* and FR-030 advisory-only constraint.
  Foundry carve-out is N/A because no KPI / scenario / audit data is
  persisted outside AU (spec Assumption #5).
- **Alternatives considered**:
  - LLM-driven KPI classification — rejected: violates FR-030 and SC-009
    (would route data through non-AU regions if Foundry was used).

## D7. Frontend route + reuse posture

- **Decision**: New top-level governance route at
  `apps/web/src/app/governance/evidence/` (sibling to the existing
  `executive`, `dashboard`, and `data-sources` routes). Page composes
  the existing `PersonaWorkspace` shell with six tabs aligned to the
  six pillars: KPI Ladder, Measurement Method, Replay Scorecard, Impact
  Chains, Benchmarks, Audit Trace. Display states for degraded-mode,
  small-sample (>10 % imputed rows), manual rows, and reduced-fidelity
  reuse the badge/banner primitives already present in
  `apps/web/src/app/governance/executive` (verified during planning;
  if a needed primitive is missing, the implementing PR MUST extend an
  existing component, not introduce a new chart library — FR-034).
- **Rationale**: Matches user input *"Reuse the `PersonaWorkspace`
  shell — NO new chart libraries, NO new UI primitives"* and FR-034.
- **Alternatives considered**:
  - Embed under `governance/executive/` — rejected: would couple two
    independent personas (Risk Manager + Auditor here vs Executive
    Leader in spec 037) and dilute SC-005 audit-walk timing.
  - New top-level `app/evidence/` route — rejected: harness is a
    governance artefact; siblings already live under `/governance`.

## D8. Multilingual + accessibility (FR-037, SC-013)

- **Decision**: Reuse `apps/web/src/lib/i18n/language-packs.ts` (existing
  catalogue). The Public Information KPI render iterates over the
  eight required channels (English plain-language + Mandarin + Arabic
  + Vietnamese + Cantonese + Punjabi + Auslan + ≥1 jurisdiction-
  appropriate First-Nations language). WCAG 2.2 AA conformance is
  validated by Playwright + axe-core (D11).
- **Rationale**: FR-037 explicitly mandates reuse of the existing
  `language-packs.ts`; introducing new language assets would violate
  FR-013 and FR-034.
- **Alternatives considered**: none — FR-037 pins the source.

## D9. API contract style (Service → Manager → Resilience)

- **Decision**: Each endpoint follows the AMA api-architect
  Service → Manager → Resilience pattern: a thin FastAPI router
  function (Service) calls a domain Manager (in `services/evidence/...`)
  that delegates Cosmos / Blob I/O to a Resilience-wrapped client
  (retry + circuit-breaker via the shared resilience helpers already
  used by `services/governance`). Every endpoint emits RED metrics
  (Rate, Errors, Duration) plus a correlation-ID header
  (`x-ama-correlation-id`) propagated to App Insights.
- **Rationale**: Consistent with the existing AMA api-architect contract
  pattern; correlation IDs are required by the AMA telemetry
  conventions (Application Insights + Log Analytics).
- **Alternatives considered**:
  - Direct Cosmos calls from router — rejected: bypasses retry policy
    and breaks the chaos-experiment expectations in D12.

## D10. Bicep IaC

- **Decision**: New Bicep module
  `infra/bicep/modules/evidence-harness.bicep` declares: 6 Cosmos
  containers (D2) + 1 cold-archive Blob container with 7-year
  immutability policy (D3) + 1 App Insights workbook
  (`evidence-harness-slo`) for SLO/RED dashboards. Wired into
  `infra/bicep/main.bicep` behind a feature flag parameter
  `enableEvidenceHarness` defaulting to `true` for non-prod. AVM
  modules are used where available (`avm/res/storage/storage-account`
  for the cold archive); inline resources only where no AVM module
  exists. Region pinned to `australiaeast` / paired DR
  `australiasoutheast` per FR-029.
- **Rationale**: Follows
  `.github/instructions/bicep-code-best-practices.instructions.md`
  AVM-first policy and the existing modular pattern under
  `infra/bicep/modules/`. Terraform parity will be added under
  `infra/terraform/` in the same PR if and only if the spec-035 / 037
  Terraform mirrors landed for governance modules (verify at
  implementation time; if not present, defer Terraform parity to a
  follow-up issue and record in the constitution-check section of
  `plan.md`).
- **Alternatives considered**:
  - Reuse `audit-store.bicep` — rejected: existing module is sized for
    the spec-037 evidence pack and does not declare `kpi_signals` or
    cold-archive tier.

## D11. Testing strategy

- **Decision**: Test pyramid:
  - **Contract tests** (`tests/contract/test_evidence_*.py`) — one per
    endpoint (D9), validates request/response schemas against the
    OpenAPI in `specs/038-success-criteria/contracts/`. Maps to
    SC-001..SC-013.
  - **Integration tests** (`tests/integration/`):
    - `test_replay_determinism.py` — SC-004 (±2 %/±1 unit tolerance,
      ≥95 % reproduction across N repeats).
    - `test_baseline_vs_ama_delta.py` — SC-003 (per-KPI delta scorecard
      for all 7 canonical scenarios × 5 KPIs).
    - `test_imputation_rule.py` — FR-008 (forward-impute, label,
      exclude from CI; >10 % → small-sample + auditor sign-off gate).
    - `test_au_region_refusal.py` — FR-029 / SC-009 (non-AU signal
      refused + audit-logged).
    - `test_audit_append_only.py` — FR-025 (PATCH/DELETE rejected;
      amendment recorded as new entry).
  - **E2E (Playwright + axe-core)**
    `apps/web/tests/playwright/governance/evidence.spec.ts` — WCAG 2.2
    AA for all six tabs and the eight-language Public Information render
    (SC-013).
- **Rationale**: Matches user input testing block; reuses the
  `tests/contract` and `tests/integration` conventions already used by
  spec 037.
- **Alternatives considered**: none material.

## D12. SRE / SLO / chaos

- **Decision**:
  - SLOs: evidence-endpoint availability ≥99.5 %; replay job success
    rate ≥98 %; metric freshness ≤60 s.
  - Burn-rate alerts at 2 %/h and 5 %/h, defined in the
    `evidence-harness-slo` workbook.
  - Three staged chaos experiments:
    1. Cosmos rate-limit on `kpi_signals` — verify replay retries +
       degraded-mode flag.
    2. AOAI timeout during Measurement Method summarisation — verify
       Measurement Method document still renders deterministic content
       with a "summary unavailable" reduced-fidelity tag.
    3. App Insights ingestion lag — verify SLO dashboard surfaces
       freshness breach alert without dropping evidence.
- **Rationale**: Matches user input. All three exercises validate the
  FR-027 / FR-032 graceful-degradation requirements end-to-end.
- **Alternatives considered**: none material.

## D13. Container + health

- **Decision**: No new container image. Reuse
  `apps/api/Dockerfile`. Add `/healthz/evidence` liveness/readiness
  endpoint that pings the six Cosmos containers (HEAD-only RU cost) and
  verifies the cold-archive Blob container is reachable.
- **Rationale**: User input explicitly directs container reuse.
  Pinned base image stays unchanged.
- **Alternatives considered**: separate evidence container — rejected
  (delivery-hygiene scope, FR-033).

## D14. Capstone-trace tagging (FR-033)

- **Decision**: Append a row to
  `specs/shared/capstone-metric-trace.md` under the
  *"Spec-level capstone-criticality flags"* table, tagging
  `specs/038-success-criteria/` as
  **non-capstone-critical-path / delivery-hygiene** with rationale
  citing FR-033 and the spec-037 FR-020 precedent. This is performed
  during `/speckit.implement`, not by `/speckit.plan` itself, but the
  plan records the row text verbatim (see plan.md §"Capstone-trace
  tagging step") so the implementing PR can apply it as a single-line
  insert.
- **Rationale**: Mirrors the existing spec-037 row already present at
  the bottom of `capstone-metric-trace.md`.
- **Alternatives considered**: none — FR-033 pins the requirement.

---

## Open questions

None. All clarifications resolved in spec; all technical decisions
above cite either the spec, the constitution, or a concrete reuse
target in the existing codebase.
