# Research: Measurable Success-Criteria Evidence Harness (spec 040 (originally Spec 038))

**Branch**: `040-success-criteria` | **Date**: 2026-05-11
**Input**: `specs/040-success-criteria/spec.md`

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
    OpenAPI in `specs/040-success-criteria/contracts/`. Maps to
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
  `specs/040-success-criteria/` as
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

---

## Cycle 2 Decisions

The following decisions cover AMD-01..AMD-13 and the Cycle 2 R1+R2
clarifications. Numbering continues from D14. None of D1..D14 are
re-opened.

### D15. Audit cold-archive immutability period and lock state (AMD-01 / FR-038 / SC-014)

- **Decision**: Bicep deploys the cold-archive Blob immutability
  policy with `immutabilityPeriodSinceCreationInDays = 2555` (= 7 ×
  365) AND `state = 'Locked'` at deployment time. Operator follow-up
  to lock is forbidden. Any deploy producing an unlocked or shorter
  policy fails the `az deployment group what-if` gate.
- **Rationale**: Removes the post-deploy "unlocked window" that would
  otherwise let an operator weaken the FR-025 append-only invariant.
  2,555 d is the exact arithmetic of the spec's ≥7-year requirement,
  not "≈84 months", which would silently round.
- **Alternatives considered**: 30-day-multiple periods (rejected — not
  the constitutional requirement); deploy-then-lock workflow (rejected
  — leaves a tampering window).

### D16. Audit-mutation rejection contract: `409 Conflict` + ProblemDetails (AMD-03 / FR-040 / SC-016)

- **Decision**: PATCH and DELETE against `evidence_audit` documents
  are rejected at the persistence boundary (Cosmos server-side
  stored procedure or change-feed processor invariant). HTTP layer
  surfaces `409 Conflict` with a `ProblemDetails` body whose `type`
  URI references FR-040 and whose `title` is exactly
  `"audit-record-immutable"`. Each rejection appends a tampering-
  attempt audit row of `kind="audit_mutation_attempted"` in the same
  transaction.
- **Rationale**: RFC 9110 §15.5.10 is the closest semantic fit
  ("conflict with the current state of the target resource" — the
  locked immutability policy IS the target state). `403` would
  mis-signal an authorisation issue; `405` would imply the verb is
  globally unsupported.
- **Alternatives considered**: `403 Forbidden` (rejected — not an
  authorisation failure); `405 Method Not Allowed` (rejected —
  PATCH/DELETE ARE supported on other endpoints, just not on locked
  audit rows).

### D17. Auslan deferred-permitted with visible badge (AMD-02 / FR-039 / R1-Q3)

- **Decision**: Auslan media + transcript are mandatory only for
  cyclone, bushfire, and flood scenarios in this cycle. The other
  four scenarios (urban_fire, mass_casualty, hazmat, marine_sar) are
  deferred-permitted but MUST render a visible
  `auslan-asset-missing` badge AND tag the row `provenance: manual`
  so it counts toward the FR-028 / SC-010 ≤50 % manual-row cap.
- **Rationale**: Aligns with constitution V-A (AWS hazard-icon
  expectation strongest for the three highest-frequency hazards)
  while avoiding silent omission, which would breach the Ten Warning
  Principles #3 and #8 (trusted, clearly communicated).
- **Alternatives considered**: Mandatory Auslan for all 7 (rejected
  this cycle — production-grade Auslan asset pipeline not yet in
  scope); silent omission (rejected — violates V-B principle 3).

### D18. Defaulted `(L=3, C=3)` weights count toward FR-028 manual cap (AMD-04 / FR-041 / R1-Q4)

- **Decision**: When the spec-037 risk register has no matching row
  the `risk_adjustment` field defaults to `(L=3, C=3)` AND the row's
  `provenance` is set to `manual`. These rows count toward the
  FR-028 / SC-010 ≤50 % per-artefact manual-row cap. Publication is
  blocked when the cap is breached; unblocking paths are (a) replace
  with risk-register-sourced weights or (b) named-auditor sign-off
  per spec 037 FR-037.
- **Rationale**: Treating defaulted neutrals as "auto" would let a
  ladder ship 100 % placeholder weights and defeat the manual-cap
  invariant. Tagging them `manual` makes the placeholder visible in
  the audit trail and the UI.
- **Alternatives considered**: Tag as `auto` with a side-channel
  flag (rejected — fragments the manual-cap arithmetic across two
  fields); refuse to publish any ladder with defaulted rows
  (rejected — too brittle for the prototype tier and not what the
  spec requires).

### D19. `AMA_TEST_MODE=1` sentinel for in-memory client fallback (AMD-05 / FR-042 / SC-018)

- **Decision**: The in-memory client registry in
  `apps/api/app/services/evidence/_clients.py` activates **only**
  when `AMA_TEST_MODE=1` (or a pytest-detected equivalent) is set in
  the environment. In any other environment, missing Azure
  credentials cause the FastAPI app to fail fast on startup with an
  error message that names BOTH FR-029 (AU sovereignty) and FR-042
  (production-mode requirement).
- **Rationale**: A startup-time failure is the cheapest and most
  observable enforcement point; lazy / first-request failure would
  let pods enter the rotation in a permanently broken state and
  silently violate FR-029.
- **Alternatives considered**: Health-check probe failure (rejected —
  too late, already in rotation); pytest-only env var (rejected —
  doesn't cover dev-loop reproduction outside pytest).

### D20. Bicep `existing.location` deploy-time AU assertion (AMD-06 / FR-043 / SC-019)

- **Decision**: `infra/bicep/modules/evidence-harness.bicep` reads
  the `location` of every bound existing Cosmos / Storage /
  Application Insights / Log Analytics resource via `existing` and
  asserts `location ∈ {'australiaeast', 'australiasoutheast'}`.
  `@allowed` parameter constraints alone are NOT sufficient — they
  constrain what the operator may pass, not what is actually bound.
- **Rationale**: Deploy-time assertion against the real bound
  resource closes the gap where an operator wires a non-AU resource
  into an AU-allowed parameter slot and the deploy succeeds. Mirrors
  the precedent in existing portfolio modules.
- **Alternatives considered**: Azure Policy at subscription scope
  (rejected — not a module-level guarantee, may be missing in dev
  subscriptions); post-deploy validation script (rejected —
  validates after the breach).

### D21. Per-operation `Strong` consistency + bounded 3-retry backoff (AMD-07 / FR-044 / R2-Q2)

- **Decision**: The audit write that precedes every AU-refusal HTTP
  response uses Cosmos SDK request-options override
  `consistency_level=Strong` on `create_item` (per-operation; the
  account-level default `Session` remains for non-audit containers
  per `eval-platform.bicep` precedent). Transient 5xx / 429 are
  retried 3 times with 250 ms / 1 s / 4 s exponential backoff. On
  retry exhaustion the API returns HTTP `503` with a `ProblemDetails`
  body referencing FR-044. The audit Cosmos account is single-region
  (`australiaeast`) so per-op `Strong` is compatible (multi-region
  Strong is forbidden by Cosmos).
- **Rationale**: Per-op Strong gives the durable-before-respond
  guarantee the spec requires while preserving Session consistency
  for the rest of the harness (FR-034 reuse invariant). The retry
  budget (~5.25 s worst case) is bounded well below the FR-046 ≤60 s
  freshness SLO so the retry policy cannot independently breach the
  SLO budget (CHK107).
- **Alternatives considered**: Account-level Strong (rejected —
  breaks portfolio-wide Session default and forbids the
  australiasoutheast paired DR); silent retry forever (rejected —
  unbounded blocking); fail-fast with no retry (rejected — too
  brittle for transient 429).

### D22. `/healthz/evidence` critical vs non-critical banding (AMD-08 / FR-045 / SC-020(b) / R1-Q1)

- **Decision**: The probe partitions stores into:
  - **Critical (failure ⇒ 503)**: every Cosmos container in the
    evidence DB (`kpi_ladder`, `indicator_definition`,
    `measurement_method`, `scenario_run`, `delta_scorecard`,
    `causal_chain`, `benchmark`, `signal`, `evidence_audit`), the
    Blob immutable cold-archive container, and the Cosmos
    change-feed → Blob mirror processor (FR-040).
  - **Non-critical (failure ⇒ 200 + `degraded:true`)**: Application
    Insights ingestion endpoint and any read-only reporting/cache
    layer.
  The hardcoded `evidence-audit-cold=True` shortcut is removed.
- **Rationale**: Critical stores sit on the FR-025 / FR-029 / FR-040
  AU-sovereignty + append-only audit invariant path, where silent
  degradation is forbidden. App Insights is observability-only and
  graceful degradation is acceptable per FR-032.
- **Alternatives considered**: Single threshold "any failure ⇒ 503"
  (rejected — would page on App Insights blip and violate FR-032);
  no banding (rejected — would let an audit-store outage hide behind
  a `200 + degraded:true` and breach FR-025).

### D23. SLO horizon = 30 d, burn windows = 1 h, action group mandatory (AMD-09 / FR-046 / R1-Q5)

- **Decision**: Bicep deploys the `evidence-harness-slo` workbook
  with availability ≥99.5 %, replay success ≥98 %, and freshness
  ≤60 s SLO targets evaluated against a **rolling 30-day** SLO
  horizon. Burn-rate alerts at 2 %/h and 5 %/h are evaluated over a
  rolling **1-hour** window (Google SRE Workbook Ch 5 fast-burn
  convention). The Bicep module accepts a required parameter
  `sloAlertActionGroupId`; deployment fails when this is empty in any
  non-test environment (FR-042 fail-fast precedent). None of the
  workbook, SLO targets, burn-rate alerts, or action-group binding
  may be deferred to "operator follow-up".
- **Rationale**: 1 h is the smallest window that yields statistically
  meaningful burn against a 30-day budget while still firing within
  an actionable response time. Mandating the action-group ID at
  deploy time prevents the common failure mode of alerts that fire
  into a void.
- **Alternatives considered**: 6 h / 24 h burn windows (rejected —
  too slow to fire against a 30-d budget); optional action group
  (rejected — observed to ship as default-empty).

### D24. Sev1 / Sev2 burn-rate alert routing (R2-Q3 / FR-046)

- **Decision**: 5 %/h fast-burn alert ⇒ `severity: 1` (paging tier).
  2 %/h slow-burn alert ⇒ `severity: 2` (ticketing tier).
  `severity: 0` is forbidden for these alerts (reserved for total-
  outage signals per `observability-alerts.bicep` precedent).
- **Rationale**: Mirrors the existing AMA SRE severity ladder; Sev0
  reservation prevents the workbook from clashing with the
  total-outage rule set.
- **Alternatives considered**: Both at Sev1 (rejected — paging
  fatigue on slow burn); both at Sev2 (rejected — fast-burn would
  miss the 24×7 page).

### D25. TS twin parity asserted by OpenAPI contract test, no Zod (AMD-10 / FR-047 / SC-022(a) / R2-Q1)

- **Decision**: Pydantic v2 models under
  `apps/api/app/services/evidence/models/*.py` set
  `model_config = ConfigDict(extra="forbid")`; unknown fields are
  rejected with HTTP `422`. The TS twin under
  `packages/domain/src/evidence/*.ts` remains type-only — no Zod, no
  class-validator, no runtime `extra=forbid`. Schema parity is
  asserted by an OpenAPI-driven contract test against
  `specs/040-success-criteria/contracts/openapi.evidence-harness.yaml`,
  not by ad-hoc TS unit tests. Convention precedent:
  `packages/domain/src/app-role.ts`.
- **Rationale**: Adding Zod/class-validator would violate the FR-034
  "no new domain-validation primitives" invariant. The OpenAPI is
  already the source of truth for the API boundary, so the contract
  test is the natural parity check.
- **Alternatives considered**: Zod runtime validation in the TS twin
  (rejected — new primitive, violates FR-034); duplicated TS unit
  tests (rejected — drifts from the OpenAPI source of truth).

### D26. PI render `language_fallback_used` response field (AMD-11 / FR-048 / SC-022(b))

- **Decision**: The Public Information render endpoint
  (`GET /api/v1/evidence/public-information/{scenario_id}`) returns
  a `language_fallback_used: "<from_code>→<to_code>"` field on each
  channel render where the language-pack lookup chain fell back. The
  separator is the U+2192 RIGHTWARDS ARROW (`→`), not `->`. The
  field is **omitted** entirely when no fallback occurred so
  consumers can distinguish positive vs negative cases. The UI
  renders a visible "fallback used" badge near the affected content;
  silent downgrade is forbidden.
- **Rationale**: A nullable field would force consumers to
  distinguish `null` from "absent" inconsistently across language
  channels; field-omit is the cleaner contract. The U+2192 arrow
  matches the human-readable rendering and avoids ASCII collision
  with the `->` operator commonly seen in logs.
- **Alternatives considered**: Boolean `fallback_used` (rejected —
  loses the `<from>→<to>` provenance); global toast (rejected —
  CHK132 requires a per-content badge).

### D27. Per-jurisdiction benchmark seed coverage ≥32 + cross-sector ≥5 (AMD-12 / FR-049 / SC-022(c))

- **Decision**: The seeded `benchmark_register` MUST contain ≥32
  jurisdictional rows (8 jurisdictions × ≥4 categories: primary
  fire, ambulance, SES, police) PLUS ≥5 cross-sector rows (BoM
  warning lead-time per warning class, NEMA COMDISPLAN
  activation-to-deployment, ICAO ARFF response targets via
  Airservices Australia, SAIDI/SAIFI for utilities, AIIMS span-of-
  control 3–7). Each row carries a structured `source_citation`
  4-tuple (organisation + document + year + URL). Unsourced rows
  are tagged `provenance: manual` and counted toward the FR-028
  ≤50 % per-artefact manual-row cap. Citations only — external
  benchmark data is not republished (Assumption #7).
- **Rationale**: An aggregate floor would let one heavily-seeded
  jurisdiction satisfy SC-022(c) while leaving others empty. The
  split assertion (≥32 + ≥5) makes each leg independently
  verifiable.
- **Alternatives considered**: Single aggregate ≥37 (rejected —
  hides per-jurisdiction gaps); free-text citations (rejected —
  precludes machine-checkable provenance).

### D28. Governance/evidence tabs fetch live data on mount (AMD-13 / FR-050 / SC-022(d))

- **Decision**: Each tab in `apps/web/src/app/governance/evidence/`
  (KPI Ladder, Measurement Method, Replay Scorecard, Causal Chains,
  Benchmarks, Audit Trace, Public Information) MUST fetch live data
  from its corresponding `/api/v1/evidence/*` endpoint **on mount**
  (not lazy / manual-refresh / deferred-until-tab-focus). Tabs MUST
  surface all four state badges — `degraded`, `small-sample`,
  `manual`, `reduced-fidelity` — explicitly. Stub or placeholder
  content (e.g., "populated by Phase 4") is forbidden in any merged
  build.
- **Rationale**: On-mount fetch is the user-observable contract that
  matches the SC-005 audit-walk and SC-002 measurement-method
  lookup latency targets. Explicit state badges are the operator's
  only signal that a value is not at full fidelity (FR-027 / FR-032
  / FR-028 invariants).
- **Alternatives considered**: Lazy fetch on first interaction
  (rejected — defeats the "live data on mount" contract);
  conditional badge rendering only when a state is set (already the
  behaviour — but absence MUST also be testable, hence the
  explicit-surfacing requirement).
