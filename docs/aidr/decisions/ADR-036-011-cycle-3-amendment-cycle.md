# ADR-036-011: Cycle 3 Amendment Cycle — KQL Canonicalisation Contract + Staging-Promotion Gate Enforcement

**Status**: Accepted (Cycle 5 Step 8au cohort re-review converged 🟢 GREEN PROCEED across all 3 cohorts — operational 10/10 ACCEPT, sectors 54 ACCEPT/4 carry-forward RESERVATIONS/0 OBJECT, technical 17/0/0 with infrastructure-devops keystone reservation closed; 0 OBJECT + 0 NEW merit-validated findings; per Cycle 5 clarify Pass 2 Q4 multi-cycle Status convergence rule)
**Deciders**: API Architect, Solution Architect, Observability Engineer, SRE Engineer, Infrastructure DevOps Engineer, Security Engineer, Compliance Auditor, Data Engineer, Operations Officer, Field Coordinator
**Date**: 2026-05-10
**Spec**: 036-sim-agent-extend (Cycle 3 amendments A3-01..A3-06)
**FR coverage**: FR-071 (workflow-gate enforcement), FR-072 (synthetic smoke-injection HTTP-POST contract), FR-073 (SLI KQL canonicalisation contract); SC-014 (staging-promotion gate refusal under synthetic canary)
**Constitution**: I (Primacy of Life — staging gates anchored on SC-001 / SC-010 require real telemetry to be enforceable), IV (Transparency and Auditability — single source of truth between contracts and implementation; least-privilege identity), V (Graceful Degradation — predictable failure with explicit non-zero workflow exit on threshold breach), NN-2 (Data sovereignty — `australiaeast` residency for `tnt-stg-smoke` and any token material)
**Related ADRs**: ADR-031 (`docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md`) — explicit non-application; ADR-036-007 (gap-free sequence allocator); ADR-036-008 (SLI thresholds rationale — pins `contracts/sli-thresholds.md` as canonical KQL surface); ADR-036-010 (`ADR-036-010-cycle-2-amendment-cycle.md`) — predecessor with stale citations being corrected by A3-03 / A3-04

> **Co-authored-by**: Copilot <223556219+Copilot@users.noreply.github.com>

---

## Context

Cycle 2 of spec-036 closed with eight amendments (A2-01..A2-08, ADR-036-010)
that introduced Z6 + Z7 SLIs, the `signal_pipeline.dispatch_failed` audit
envelope (entry-25), per-subscriber correlation IDs, and a staging-promotion
gate scaffold (`.github/workflows/staging-promotion.yml`,
`tests/staging_gates.py::assert_sli_thresholds`, synthetic smoke-injection
job).

The **Step 8s cohort sweep** (cross-cohort re-review of Cycle 2's *own*
deliverables — distinct from Cycles 1 / 2 which targeted the original spec /
implementation surface) surfaced **six merit-validated findings** spanning
the staging-promotion gate, the canonical SLI-Z6 / SLI-Z7 KQL implementations,
and the ADR-036-010 + CHANGELOG self-documentation. The user-agent
self-validated all six findings by direct `file:line` inspection before
Cycle 3 dispatch:

1. **A3-01 (HIGH, sre-engineer + Operations Officer + Field Coordinator)** —
   `staging-promotion.yml:67-113` heredoc only branches on `proc.returncode
   != 0`; on a successful `az` call it prints `latest=…` and unconditionally
   emits `"All 7 SLIs within threshold — promotion allowed."` regardless of
   actual values. SC-013 cannot be enforced at the workflow boundary even
   though `tests/staging_gates.py::assert_sli_thresholds` (line 98) is fully
   implemented and tested.
2. **A3-02 (HIGH, infrastructure-devops + Operations Officer + Field
   Coordinator)** — `staging-promotion.yml:142-185` smoke-injection step
   constructs `payload = {…}` per iteration but never invokes the
   inject-telemetry endpoint. `import subprocess` (line 147) is unused; no
   `requests.post`, `subprocess.run`, `curl`, or `az rest` call appears in
   the step body. The `≥ 40 synthetic signals` floor trivially passes (5 ×
   8 = 40 always) while no `customEvents` rows accumulate — defeating
   Cycle 2 Pass-2 Q4's `MIN_SAMPLES_PER_SLI_24H = 30` mitigation.
3. **A3-03 (MEDIUM, compliance-auditor)** — `ADR-036-010:87` and
   `CHANGELOG.md:20` cite `tests/staging_gates.py::_is_breach()` — a symbol
   that does not exist (`grep -n "_is_breach" tests/staging_gates.py`
   returns zero hits). Actual public entry-point is `assert_sli_thresholds()`
   (line 98); the helper carries inlined per-`(sub_agent, model_deployment)`
   Z6 and inverse-band Z7 branches.
4. **A3-04 (MEDIUM, compliance-auditor)** — `ADR-036-010:83-84` and
   `CHANGELOG.md:19` quote SLI-Z6 thresholds as gpt-4o `2 500 / 5 000 ms`
   and gpt-4o-mini `1 800 / 2 000 ms`; canonical values across
   `infra/observability/sli-kql.json:72-75`,
   `tests/staging_gates.py::assert_sli_thresholds()`,
   `infra/bicep/modules/observability-alerts.bicep`, and
   `contracts/sli-thresholds.md:218-228` are gpt-4o `4 000 / 5 000 ms` and
   gpt-4o-mini `1 500 / 2 000 ms`. Self-documentation drifts from the
   canonical contract.
5. **A3-05 (MEDIUM, data-engineer)** — `infra/observability/sli-kql.json:76`
   Z6 KQL drops `extend sub_agent`, drops `where env == "staging"`, and
   groups `by model_deployment` only — collapsing the 28-series cardinality
   (`sub_agent × model_deployment`) into ~2 (one row per model) AND mixing
   production traffic into the staging gate.
6. **A3-06 (MEDIUM, data-engineer)** — `infra/observability/sli-kql.json:87-91`
   Z7 reads a single `delivery_ms` customDimension instead of the spec's
   `client_received_ms − server_emit_ms` end-to-end clock-skew form;
   `warn_pct: 99.5` and `breach_pct: 99.5` are identical, contradicting
   `contracts/sli-thresholds.md:269-270` ("Warn ≥ 99.5 %; Breach < 99.0 %").

The combined Cycle 3 envelope (3 new FRs FR-071/072/073, 1 new SC SC-014,
1 new typed audit envelope `staging_promotion.refused` at
`audit-envelope.md` §3.26, 2 doc-fix amendments A3-03 / A3-04 against
ADR-036-010 and CHANGELOG) required a single cross-cutting ADR because
the changes interlock: the workflow-gate enforcement (A3-01 / FR-071), the
synthetic smoke-injection HTTP contract (A3-02 / FR-072), and the SLI KQL
canonicalisation contract (A3-05 + A3-06 / FR-073) each depend on the
others to satisfy SC-013 (Cycle 2 positive-side gate) AND the new SC-014
(negative-side refusal under synthetic canary), and the ADR-036-010
self-documentation fixes (A3-03 / A3-04) MUST be co-merged in Step 8x to
keep audit reviewers' references resolvable.

---

## Decision

Adopt the six Cycle 3 amendments en bloc. Land them across three sequential
work-items:

- **Step 8x** — `audit-envelope.md` §3.26 schema for
  `staging_promotion.refused` + counter increment 25 → 26 +
  `contracts/sli-thresholds.md` §"KQL canonicalisation contract"
  subsection + ADR-036-010 / CHANGELOG drift corrections (A3-03 + A3-04).
- **Step 8y** — this ADR + Cycle 3 plan-decision rows
  PD-C3-01..PD-C3-03 in `plan.md`.
- **Step 8z** — `tests/contract/_kql_canonicaliser.py` +
  `tests/contract/test_kql_canonicaliser_unit.py` +
  `tests/contract/test_sli_kql_canonical_match.py` (parametric over all 7
  SLIs, Z1-Z7) + workflow refactor (A3-01 + A3-02 implementation) +
  synthetic-canary integration test
  (`test_synthetic_canary_refused_red_sli_row`) + Z1-Z5 drift fixes if any
  surface (per PD-C3-02 co-merge unit).

The cross-cutting decisions recorded by this ADR are **three sub-decisions**
that bind the technical plan to the Pass-1 / Pass-2 clarifications resolved
in Cycle 3:

### Sub-decision (i): strict-string-after-normalisation over Kusto-AST equivalence

- **Decision**: The FR-073 SLI KQL canonicalisation contract uses
  **strict-string-after-normalisation** (a six-step pure-Python pipeline
  that strips comments, collapses whitespace, lowercases reserved keywords,
  sorts `by` and `summarize` clause column lists lexicographically, and
  strips redundant outer parentheses). Kusto-AST equivalence is explicitly
  rejected.
- **Rationale**: Three rejection points captured in PD-C3-01 of `plan.md`:
  cross-runtime fragility (.NET parser incompatibility with Linux runners),
  PR-diffability lost (binary match/no-match collapses surface differences
  reviewers MUST see), deterministic byte-equality is the simplest
  verifiable contract (reuses RFC 8785 JCS precedent from Cycle 1 Pass-1
  Q3 / Cycle 2 Pass-1 Q1).
- **Authoritative citation**: `spec.md:838-925` (Cycle 3 Pass-1 Q1).
  `plan.md` PD-C3-01.

### Sub-decision (ii): Z1-Z5 alignment audit co-merges with canonicaliser PR (single Step 8z PR)

- **Decision**: The Cycle 3 Step 8z PR landing
  `tests/contract/_kql_canonicaliser.py`,
  `tests/contract/test_kql_canonicaliser_unit.py`, and
  `tests/contract/test_sli_kql_canonical_match.py` (parametric over all 7
  SLIs) MUST also contain — in the same PR — any Z1-Z5 alignment fixes
  that the parametric test surfaces during PR review. The contract test
  MUST be green at PR-merge time. Sequential blocking (audit-first PR,
  then a follow-up contract-test PR) is explicitly rejected.
- **Three-outcome rubric** at PR review:
  - **(i) Green on first run** — all 5 SLIs (Z1-Z5)
    byte-equal-after-canonicalisation; the PR is the contract-test PR
    alone. Expected outcome (Pass-1 Q5 + Cycle 2 A2-02 Z1-Z5 alignment
    review).
  - **(ii) Drift fixed inline (preferred)** — drift surfaced; the same
    PR fixes the canonical or implementation form (per source-of-truth
    determination at PR review); PR description records the drift.
  - **(iii) Plan-touch fall-through (judged unlikely)** — drift requiring
    plan-level decision; PR opens a tracking issue, pins the contract
    test against the agreed canonical form before merge (test still
    green at merge); a thin Cycle 4 specify is dispatched OR the
    question is folded into a follow-on PR with a recorded
    `(plan-touch)` outcome. Outcome (iii) is judged unlikely (Pass-1 Q5
    + ADR-036-008 already pin `contracts/sli-thresholds.md` as canonical).
- **Authoritative citation**: `spec.md:1484-1606` (Cycle 3 Pass-2 Q3).
  `plan.md` PD-C3-02.

### Sub-decision (iii): Cycle 3 explicit non-application of ADR-031's `AZURE_CREDENTIALS` fallback to the staging-promotion smoke-injection job

- **Decision**: ADR-031's MVP-time-bound deviation to a long-lived
  `AZURE_CREDENTIALS` JSON secret does NOT apply to
  `.github/workflows/staging-promotion.yml`. The smoke-injection job
  (FR-072 / A3-02) acquires a short-lived OIDC-derived bearer access
  token at job start via `azure/login@v2` (federated credential, already
  wired at `staging-promotion.yml:31, 61-64, 135-140`) followed by
  `az account get-access-token --resource <staging-api-app-id-uri>`. No
  long-lived `SMOKE_TOKEN` secret is permitted. Rotation is "per workflow
  run" and automatic.
- **Five `tnt-stg-smoke` isolation guarantees** (codified, all enforced
  by automated contract tests): (1) data residency in `australiaeast`;
  (2) sole-tenant scope (forbidden-literal list); (3) posture parity with
  production (private endpoint + customer-managed key on `tnt-stg-smoke`
  storage, soft-delete with 7-day retention); (4) KQL filtering
  (`where tenant_id == "tnt-stg-smoke"` on canonical Z6 / Z7 KQL bodies);
  (5) least-privilege test identity. The `Simulation.Coordinator` role
  assignment is **database-level** (`scope: '${account.id}/dbs/${databaseName}'`)
  because the Cosmos data-plane RBAC API 2024-08-15 does not yet expose a
  `partitionKey` selector; the database-level scope is therefore a
  **compensating defence-in-depth control** rather than a partition-level
  guarantee. The smoke-injection runtime tenant filter
  (`where tenant_id == "tnt-stg-smoke"`) at the KQL contract surface, the
  `customDimensions["tenant_id"]` envelope discriminator, and the Pass-1 Q2
  isolation guarantees (i)–(v) jointly enforce tenant isolation. A backlog
  issue (#84) tracks the partition-scope upgrade once
  the Cosmos data-plane RBAC API exposes `partitionKey`. (See the Cycle 4
  amendment sub-section at L478+ for the full A4-02 narrative; see
  `spec.md:3896-3915` and `spec.md:961-966` for the spec-side anchors.)
- **Why ADR-031 fallback does NOT apply**: (a) the workflow already uses
  OIDC; (b) ADR-031 was scoped to the `azd` deploy path (the MVP cd
  workflow), not the staging-promotion gate; (c) introducing a
  long-lived `SMOKE_TOKEN` in 2026 — when federated identity already
  works — would regress on Constitution Principle IV (least-privilege
  identity, single-tenant scoping) and clause NN-2 (data sovereignty for
  any token material); (d) per Cycle 3 Pass-1 Q2, the FR-072
  `SMOKE_TOKEN` shorthand is being corrected to OIDC bearer wording in
  Step 8x.
- **Authoritative citation**: `spec.md:926-1015` (Cycle 3 Pass-1 Q2).
  `plan.md` PD-C3-03.

---

## Alternatives Considered

### A-1: Kusto-AST equivalence for the FR-073 contract

- **Rejected**: cross-runtime fragility (.NET parser incompatible with
  Linux runners; `kustopreview` Windows-only), PR-diffability lost
  (binary match/no-match), AST equivalence buys nothing for the
  cohort-validated surface-form defect surface (A3-05 / A3-06 are all
  surface-form deltas). See PD-C3-01 in `plan.md`.

### A-2: Sequential PR pair for canonicaliser (audit-first, then contract-test)

- **Rejected**: leaves SLI-Z1-Z5 unaudited under the new contract until
  the second PR landed (a partial-enforcement window, exactly what
  Pass-1 Q5 explicitly rejected). Cycle 2 A2-02 set the co-merge
  precedent for Z6 + Z7 introduction. See PD-C3-02 in `plan.md`.

### A-3: Long-lived `SMOKE_TOKEN` GitHub secret (citing ADR-031)

- **Rejected**: ADR-031 was scoped to the `azd` deploy path; the
  staging-promotion gate already uses OIDC at
  `staging-promotion.yml:31, 61-64, 135-140`; introducing a new
  long-lived secret in 2026 would regress on Constitution Principle IV
  and NN-2. See PD-C3-03 in `plan.md`.

### A-4: Live-KQL canary for SC-014 (instead of CI-level Python fixture)

- **Rejected**: would inject deliberately-malformed telemetry into the
  same Application Insights workspace the production gate consumes,
  contaminating the gate's own evidence stream and risking
  false-positive refusals on genuine staging telemetry. CI-level
  Python fixture meets SC-014's literal requirement, runs in <100 ms
  per case, and has zero infrastructure cost. See `spec.md:1099-1218`
  (Cycle 3 Pass-1 Q4).

### A-5: Dedicated `tnt-stg-canary` tenant for SC-014

- **Rejected as premature complexity**: the fixture-driven option
  (option (b) — Pass-1 Q4) meets SC-014's literal requirement without
  requiring a second isolated tenant beyond `tnt-stg-smoke`. See
  `spec.md:1099-1218`.

### A-6: Coalesce concurrent `StagingPromotionRefused` raises into one DLQ row

- **Rejected**: violates the gap-free invariant SLI-Z2 P99 ≤ 1 gap
  per 10 000 envelopes is built to enforce; loses
  attribution-by-`triggering_workflow_run_id` for forensic review. Each
  refused gate run writes its own `staging_promotion.refused` envelope
  with a fresh per-run UUID `staging_promotion_correlation_id`. See
  `spec.md:1016-1098` (Cycle 3 Pass-1 Q3).

### A-7: Back-fill the `audit-envelope.md` §3.20–§3.24 gap for the new envelope slot

- **Rejected**: would obscure the temporal ordering of envelope
  additions across cycles and break tooling that has indexed the
  §3.25 anchor. §3.26 is the natural sequential slot, immediately
  after the Cycle 2 envelope, mirroring the "append at the end of §3"
  pattern Cycle 2 itself followed. See `spec.md:1308-1387` (Cycle 3
  Pass-2 Q1).

### A-8: Action Finding 9 (`TriggerSource` cardinality OpenAPI(5) vs Pydantic(2))

- **NOT actioned (by-design)**: the `TriggerSource` cardinality
  divergence between the OpenAPI surface (5 trigger sources) and the
  Pydantic envelope (2 trigger sources) is by-design forward-compat
  posture per `data-model.md` §11.5 and ADR-036-010 § Consequences.
  The Cycle 2 ADR explicitly accepts the divergence as forward-compat
  for new trigger sources to be added without a BREAKING bump on the
  envelope side. Cycle 3 leaves this unchanged.

---

## Consequences

### Positive

- **Workflow-gate enforcement restored** — `assert_sli_thresholds()` is
  invoked on every gate run, threshold breaches and sample-floor
  underages produce non-zero workflow exits, the unconditional success
  message is removed. SC-013 (Cycle 2 positive-side gate) becomes
  enforceable at the workflow boundary AND SC-014 (Cycle 3
  negative-side refusal under synthetic canary) becomes exercisable.
- **Synthetic smoke-injection emits real telemetry** — `requests.post`
  to the staging inject-telemetry endpoint accumulates `customEvents`
  rows in the staging Application Insights workspace, satisfying the
  `MIN_SAMPLES_PER_SLI_24H = 30` floor (Cycle 2 Pass-2 Q4) in
  low-traffic staging environments. Smoke traffic is provably scoped
  to `tnt-stg-smoke` (five isolation guarantees, all contract-test-
  enforced).
- **Parametric contract test over all 7 SLIs (Z1-Z7)** — the FR-073
  KQL canonicalisation contract test is parametric over the full SLI
  set, preventing future drift across all declared SLIs (NOT just
  Z6 / Z7). Strict-string canonicalisation gives PR-diffable output
  for human review.
- **New audit-envelope entry §3.26** (`staging_promotion.refused`)
  brings the typed-envelope total to **26** (counter increments
  `25 → 26` in `audit-envelope.md:689` and `:703`); two concurrent
  gate refusals produce two distinct envelope rows with two distinct
  `staging_promotion_correlation_id` values, preserving forensic
  attribution.
- **Workflow-level `concurrency:` block** queues common-path
  `workflow_dispatch` runs at the GitHub Actions layer; coalescing
  is impossible because each run gets its own envelope on the
  `assert_sli_thresholds()` raise path before queueing
  short-circuits. No coalescing of refusals.
- **Self-documentation aligned with code** — ADR-036-010 and
  CHANGELOG.md cite `assert_sli_thresholds()` (the actual public
  symbol) and quote the canonical Z6 thresholds (gpt-4o
  `4 000 / 5 000 ms`, gpt-4o-mini `1 500 / 2 000 ms`). A new docs
  regression test under `tests/docs/` parses ADR / CHANGELOG and
  asserts every cited Python symbol resolves via `importlib` AND
  every quoted threshold is byte-equal to the corresponding SLI-Z6
  field in `infra/observability/sli-kql.json`.

### Negative

- **Staging-promotion gate becomes more selective** — gate runs that
  previously printed "All 7 SLIs within threshold — promotion
  allowed." regardless of actual values will now genuinely refuse on
  threshold breach or sample-floor underages. Operators MUST plan for
  refusals in the days immediately following Step 8z merge as the
  smoke-injection floor accumulates evidence.
- **Smoke-injection job consumes a small staging-API budget** — each
  gate run posts `5 categories × 8 events = 40 synthetic signals`;
  at peak frequency this is bounded but non-zero (estimated ≤ 200
  inject-telemetry calls per day in low-traffic staging environments).
- **Build minor regression risk** on the canonicaliser PR — the
  parametric contract test is hard-pinned to byte-equality post-
  canonicalisation; any future drift on a single SLI fails the entire
  parametric test. Mitigated by the three-outcome rubric (drift fixed
  inline is preferred and expected for routine cases).
- **`_KEBAB_TO_PASCAL` shim retains** — the Cycle 2 read-only shim
  remains in place for the full Cycle 1 evidence-retention window
  (12 months under FR-048 retention). Cycle 3 does not retire it.

### Neutral

- **Forward-compat `TriggerSource` divergence preserved** — the
  OpenAPI(5) vs Pydantic(2) cardinality divergence (Step 8s Finding
  9, NOT actioned) remains by-design per `data-model.md` §11.5 and
  ADR-036-010 § Consequences. Cycle 3 does not change this.
- **§3.20–§3.24 audit-envelope gap preserved** — back-filling would
  obscure temporal ordering. Cycle 3 appends at §3.26 (next
  sequential after Cycle 2's §3.25), keeping the gap visible.
- **No SMOKE_TOKEN secret introduced** — the existing OIDC plumbing
  is the only authentication path; ADR-031's MVP fallback is
  explicitly NOT applied. No GitHub secret named `SMOKE_TOKEN` exists
  or will exist on this repository as a result of Cycle 3.

---

## Migration Recipe (cross-reference)

Cycle 3 is a corrective cycle on Cycle 2 deliverables — there is **no
SDK-consumer migration recipe** beyond what Cycle 2 already shipped via
`contracts/openapi-changelog.md` v0.3.0. SDK consumers see no schema
change. Internal migration steps (workflow / contract / test artefacts)
are sequenced as:

1. **Step 8x lands first** — `audit-envelope.md` §3.26
   `staging_promotion.refused` schema + counter increment 25 → 26 +
   `contracts/sli-thresholds.md` §"KQL canonicalisation contract"
   subsection + ADR-036-010 / CHANGELOG drift corrections (A3-03 +
   A3-04) + new docs regression test under `tests/docs/`.
2. **Step 8y lands second** — this ADR + plan-decision rows
   PD-C3-01..PD-C3-03 in `plan.md` (no code change).
3. **Step 8z lands third (single co-merge unit)** — workflow refactor
   (A3-01 + A3-02 implementation) + canonicaliser
   (`_kql_canonicaliser.py`) + parametric contract test
   (`test_sli_kql_canonical_match.py`) + canonicaliser unit test
   (`test_kql_canonicaliser_unit.py`) + synthetic-canary integration
   test (`test_synthetic_canary_refused_red_sli_row`) + smoke-tenant
   isolation contract test (`test_smoke_tenant_isolation.py`) + Z1-Z5
   drift fixes if any surface (per PD-C3-02 co-merge unit) +
   `assert_sli_thresholds()` extension to write
   `staging_promotion.refused` envelopes on its raise path +
   workflow-level `concurrency:` block + concurrency integration test
   (`test_staging_promotion_concurrency.py`).

Step 8x → Step 8z is sequential by artefact dependency (the Step 8z
contract test asserts the §3.26 envelope schema and the
canonicalisation-contract subsection both exist). Step 8y is
non-blocking on either Step 8x or Step 8z — this ADR + the plan
delta can land in parallel with Step 8x and before Step 8z opens.

---

## Test Obligations

- Contract: `tests/contract/_kql_canonicaliser.py` (canonicalisation
  helper — public API: `canonicalise_kql(text: str) -> str`,
  `canonical_kql_for_sli(sli_id: str, *, thresholds_path: Path | None =
  None) -> str`; private `_canonicalise_kql_string(raw: str) -> str`;
  `KeyError` on unknown sli_id; `ValueError` on malformed contracts
  file; `__all__` declared).
- Contract: `tests/contract/test_kql_canonicaliser_unit.py`
  (deterministic input/output fixtures for each of the six
  normalisation steps; idempotence assertion
  `canonicalise_kql(canonicalise_kql(x)) == canonicalise_kql(x)`;
  determinism assertion (10× re-runs produce byte-equal output)).
- Contract: `tests/contract/test_sli_kql_canonical_match.py`
  (parametric over all 7 SLIs Z1-Z7; asserts
  `canonicalise_kql(impl) == canonicalise_kql(canonical)` for every
  declared SLI).
- Contract: `tests/contract/test_smoke_tenant_isolation.py` (asserts
  the `Simulation.Coordinator` role assignment list emitted by
  `infra/bicep/modules/cosmos-simulation-containers.bicep` is scoped
  exclusively to `tnt-stg-smoke`; no production-tenant role
  assignment exists for this identity).
- Integration:
  `tests/integration/test_smoke_injection_no_prod_pollution.py`
  (forbidden-literal list + dedicated-tenant assertion; production
  tenant identifiers — `"tnt-prod"`, `"tnt-au-"` — fail the build if
  they appear in workflow YAML).
- Integration:
  `tests/integration/test_staging_promotion_concurrency.py` (invoke
  `assert_sli_thresholds()` twice concurrently against shared
  red-fixture data; assert two distinct envelope rows + two distinct
  `staging_promotion_correlation_id` values + two non-zero exits — no
  coalescing).
- Integration: `tests/integration/test_assert_sli_thresholds_z6_z7.py`
  (extended for canonicalisation-contract live-KQL test path; pre-
  existing Cycle 2 entry, refreshed for Cycle 3).
- E2E:
  `tests/e2e/test_staging_promotion_gates.py::test_synthetic_canary_refused_red_sli_row`
  (CI-level Python fixture per Pass-1 Q4; constructs deterministic
  red `sli_results` dict; asserts (i) `pytest.raises(StagingPromotionRefused)`,
  (ii) workflow non-zero exit, (iii) no `promote/{build_label}` git
  tag created, (iv) `staging_promotion.refused` envelope written
  exactly once with expected `breached_slis` content).
- E2E: `tests/e2e/test_staging_smoke_injection_floor.py` (Cycle 2
  precedent; refreshed for Cycle 3 to assert HTTP-POST is exercised
  per request, NOT just declarative payload construction).
- Docs: `tests/docs/test_adr_036_010_symbol_citations.py` (parses
  ADR-036-010 + CHANGELOG.md; asserts every cited Python symbol
  resolves via `importlib`).
- Docs: `tests/docs/test_adr_036_010_threshold_drift.py` (parses
  ADR-036-010's threshold table; asserts every quoted value is
  byte-equal to the corresponding SLI-Z6 field in
  `infra/observability/sli-kql.json`).

---

## References

- Spec FR-071 (`spec.md:3625-3641`), FR-072 (`spec.md:3643-3658`),
  FR-073 (`spec.md:3660-3677`), SC-014 (`spec.md:3784-3795`).
- `specs/036-sim-agent-extend/spec.md` §§ Cycle 3 amendments
  A3-01..A3-06 (lines 237-358), Cycle 3 clarifications Pass-1 Q1..Q5
  (lines 812-1278), Pass-2 Q1..Q3 (lines 1280-1605).
- `specs/036-sim-agent-extend/plan.md` §§ PD-C3-01, PD-C3-02,
  PD-C3-03 (Cycle 3 plan-decisions appended Step 8y).
- `specs/036-sim-agent-extend/data-model.md` § 11 (Cycle 2 entities;
  TriggerSource cardinality forward-compat divergence in §11.5
  unchanged in Cycle 3).
- `specs/036-sim-agent-extend/checklists/quality.md` (CHK157..CHK196,
  Cycle 3 quality rows added Step 8x).
- `specs/036-sim-agent-extend/contracts/audit-envelope.md` §3.26
  (`staging_promotion.refused` envelope; counter `25 → 26`; will be
  added Step 8x).
- `specs/036-sim-agent-extend/contracts/sli-thresholds.md`
  §"KQL canonicalisation contract" (will be added Step 8x); tables
  Z6 + Z7 (Cycle 2 source).
- ADR-031 (`docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md`)
  — explicit non-application to staging-promotion smoke-injection
  job per Sub-decision (iii).
- ADR-036-007 (gap-free sequence allocator —
  `staging_promotion.refused` envelope inherits the writer-only
  invariant).
- ADR-036-008 (SLI thresholds rationale — pins
  `contracts/sli-thresholds.md` as canonical KQL surface;
  canonicalisation is the contract-test mechanism that binds it to
  `infra/observability/sli-kql.json`).
- ADR-036-010 (Cycle 2 amendment cycle — predecessor; A3-03 and
  A3-04 correct stale citations in this document at lines 83-84
  and 87).
- RFC 8785 — JSON Canonicalisation Scheme (JCS) — surface-form
  byte-equality precedent reused by FR-073:
  <https://www.rfc-editor.org/rfc/rfc8785>.
- W3C TraceContext — `<https://www.w3.org/TR/trace-context/>`
  (Cycle 2 hybrid OTel propagation context for the
  `staging_promotion.refused` correlation ID lineage).
- RFC 9457 — Problem Details for HTTP APIs:
  <https://www.rfc-editor.org/rfc/rfc9457> (Cycle 2 SPEC_036
  problem+json route allow-list; staging-promotion gate refusals
  surface as workflow-level non-zero exits, NOT HTTP responses, so
  RFC 9457 does not apply directly).

---

## Cycle 4 amendment (2026-05-11)

> **Scope of this sub-section**: This sub-section is appended in place per
> Cycle 4 Pass 1 Q5 binding decision (`spec.md:4288-4351`). All Cycle 3
> prior content above (lines 1-474) is preserved verbatim; the only edit
> made *outside* this sub-section is the L172-173 in-place rewrite of the
> A-2 / Sub-decision (iii) wording for the `Simulation.Coordinator` RBAC
> scope claim, per A4-02 (`spec.md:3896-3915`). This sub-section was added
> by `/speckit.plan` Step 8ad plan landing; the actual L172-173 wording
> rewrite + smoke-tenant-isolation contract test extension + spec mirror
> correction land at Step 8ae per the dependency-edge note in
> `plan.md` § "Step 8ad / 8ae dependency-edge note (Cycle 4)".

### Cycle 4 trigger

The **Step 8ac cohort sweep** (cross-cohort re-review of Cycle 3's *own*
deliverables — distinct from Cycle 3 which targeted Cycle 2's deliverables)
surfaced **two merit-validated findings**:

1. **F-OPS-3-01 / data-engineer technical OBJECT (HIGH)** — the SLI-Z7
   KQL at `infra/observability/sli-kql.json:91` (Cycle 3 A3-06 / T-AA34
   amended body) groups `by model_deployment` and projects
   `model_deployment` without first introducing it via `extend
   model_deployment = tostring(customDimensions["model_deployment"])`.
   The byte-equality contract test
   (`tests/contract/test_sli_kql_canonical_match.py`, Cycle 3 Step 8z)
   missed the defect because BOTH `sli-kql.json` AND
   `contracts/sli-thresholds.md` §6b drifted symmetrically — the JSON
   and the contract are byte-identical-after-canonicalisation, just
   both wrong. At AppInsights query-time the KQL emits
   `SemanticError: Failed to resolve column reference
   'model_deployment'`; the staging-promotion workflow's
   `proc.returncode != 0` branch fires before
   `assert_sli_thresholds()` is invoked, so no
   `staging_promotion.refused` envelope is written, breaking the
   Cycle 3 Pass 1 Q3 always-write-envelope-on-refusal invariant and
   rendering SC-010 unenforceable on this code path
   (`spec.md:3875-3895` for full A4-01 detail). Cohort source:
   data-engineer (HIGH technical OBJECT verdict — `step-8ac-rereview-technical.md`
   § "data-engineer — Finding — HIGH: Z7 KQL groups by `model_deployment`
   without first extending it from `customDimensions`"); Operations
   Officer + Field Coordinator (HIGH operational F-OPS-3-01 — `step-8ac-rereview-operational.md`
   § "F-OPS-3-01"). Codified as Cycle 4 amendment **A4-01**.
2. **Cross-finding (4-persona MEDIUM)** — ADR-036-011 lines 172-173
   (Sub-decision (iii) point (5)) AND the Cycle 3 Pass 1 Q2 item (v)
   wording at `spec.md:961-966` both state the `Simulation.Coordinator`
   role assignment is *"scoped exclusively to `tnt-stg-smoke`"*. The
   actual Bicep at `infra/bicep/modules/cosmos-simulation-containers.bicep:316`
   declares `scope: '${account.id}/dbs/${databaseName}'` (database-
   level — the narrowest scope supported by Cosmos data-plane RBAC API
   version 2024-08-15 in `az rest` deploys); the Bicep author's
   comment block at L305-315 documents this honestly, identifying the
   query-time `where tenant_id == "tnt-stg-smoke"` filter on the Z6 /
   Z7 KQL bodies (per FR-073) as the actual compensating defence-in-
   depth control. The defect is a wording / spec misrepresentation
   only; no Bicep change is required (`spec.md:3896-3915` for full
   A4-02 detail). Cohort source: api-architect + azure-principal-
   architect + infrastructure-devops + security-engineer (cross-
   finding, all four MEDIUM — `step-8ac-rereview-technical.md`
   § "Cross-finding — RBAC scope wording misrepresents Bicep reality
   (4 personas)"). Codified as Cycle 4 amendment **A4-02**.

Both ground-truth re-review reports are held in the session workspace
`C:\Users\prbillir\.copilot\session-state\ddfe017a-c801-4ecd-b4ba-986fe32d7afd\files\`
per `spec.md:3837`. Cycle 4 is **narrower in scope than Cycle 3**
(`spec.md:3838-3841`): 0 new FRs, 0 new SCs, 1 FR strengthened in place
(FR-073), 1 self-documentation supersession (Cycle 3 Pass 1 Q2 item (v)
wording superseded by A4-02's binding wording at `spec.md:3906`). Five
Pass 1 Q→A and four Pass 2 Q→A clarifications resolved second- and
third-order ambiguities (`spec.md:3969-4385` and `spec.md:4387-4866`).

### A4-01 effects on the Cycle 3 narrative

Cycle 3 § "Decision" / Sub-decision (i) at L110-125 introduced the
**strict-string-after-normalisation** canonicalisation algorithm and the
parametric byte-equality contract test
(`tests/contract/test_sli_kql_canonical_match.py`). Cycle 4 A4-01
strengthens this contract surface with a **complementary**
runtime-validity contract test (`tests/contract/test_sli_kql_runtime_validity.py`,
new at Step 8ad) that closes the **symmetric-drift gap**: byte-equality
is necessary but **not sufficient** when both source-of-truth files drift
in lock-step. The new test enforces an author-time KQL column-resolution
discipline (a)–(c) over Z1–Z7 and is the binding mechanism for the
FR-073 strengthening recorded in the Cycle 4 amendment log at
`spec.md:3886, 3922-3934`.

The runtime-validity walker is a **lightweight regex/lexer** consuming
canonical KQL via the existing `tests/contract/_kql_canonicaliser.py`
public surface (`canonicalise_kql(text)` at L274 and
`canonical_kql_for_sli(...)` at L290). A full Kusto AST parser
dependency is **explicitly rejected** for the same three reasons
Cycle 3 PD-C3-01 / Sub-decision (i) above rejected AST equivalence at
the canonicaliser layer (cross-runtime fragility, supply-chain
expansion, surface-form sufficiency for the cohort-validated defect
surface) — see `spec.md:3997-4081` (Pass 1 Q1) for the full per-(a)/(b)/(c)
reasoning. The walker tracks `let` / `extend` / `summarize`-aggregate-
LHS symbols top-down (Pass 1 Q4, `spec.md:4219-4286`); `union`
cross-table resolutions are explicitly out-of-scope for Cycle 4 with
a fail-fast error message verbatim *"union is not yet supported by the
runtime validity walker — extend test_sli_kql_runtime_validity.py to
support multi-table column resolution"* (`spec.md:4274-4277`).

The symmetric Z7 KQL fix is applied to **both**
`infra/observability/sli-kql.json:91` AND
`specs/036-sim-agent-extend/contracts/sli-thresholds.md:280-296` (§6b
Z7 block), inserting `extend model_deployment =
tostring(customDimensions["model_deployment"])` after the existing
`extend tenant_id` line and before `where env == "staging"` — ordering
and quoting byte-identical to the corresponding Z6 line at
`sli-kql.json:75`. After the fix, `test_sli_kql_canonical_match.py`
continues to pass byte-equality across all seven SLIs; the new
`test_sli_kql_runtime_validity.py` parametric matrix is structurally
guaranteed by mirroring `test_sli_kql_canonical_match.py:37-40`'s
`@pytest.mark.parametrize("sli_id", [s["id"] for s in
_SLI_DOC["slis"]])` decorator (Pass 2 Q1, `spec.md:4496-4501`). Test
count delta: +7 parametric ids (one per SLI Z1–Z7) → 3391 baseline
becomes 3398 after Step 8ad merge (Pass 2 Q1, `spec.md:4429-4450`).
The full post-Cycle-4-implement total of **3399** (minimal posture) or
**3400** (full posture) is recorded under "Test count convergence"
below.

### A4-02 effects on the Cycle 3 narrative — RBAC scope wording correction

#### Old wording (lines 172-173, Sub-decision (iii) point (5))

> *"(5) least-privilege test identity (`Simulation.Coordinator` role
> assignment scoped exclusively to `tnt-stg-smoke`)."*

This wording misrepresents the actual Bicep scope at
`infra/bicep/modules/cosmos-simulation-containers.bicep:316`, which
declares `scope: '${account.id}/dbs/${databaseName}'` — database-
level, NOT partition-level. The Bicep is correct as-is: Cosmos data-
plane RBAC API version 2024-08-15 does not officially support
per-partition-key-value scoping in `az rest` deploys, so database-
level is the narrowest scope supported by the API at the time of this
amendment. The Bicep author's comment block at L305-315 already
documents this trade-off honestly, identifying the query-time `where
tenant_id == "tnt-stg-smoke"` filter on the Z6 / Z7 KQL bodies (per
FR-073) as the actual compensating defence-in-depth control.

#### New corrected wording (binding for Cycle 4 onward)

> *"(5) least-privilege test identity — the `Simulation.Coordinator`
> test identity is provisioned as an Entra ID enterprise app with a
> Cosmos data-plane RBAC role assignment scoped at the **database
> level** (`'${account.id}/dbs/${databaseName}'`) — this is the
> narrowest scope supported by Cosmos data-plane RBAC API version
> 2024-08-15 in `az rest` deploys. Tenant isolation onto
> `tnt-stg-smoke` is achieved via a query-time **compensating defence-
> in-depth control**: every SLI-Z6 / SLI-Z7 KQL body (per FR-073)
> carries an explicit `where tenant_id == "tnt-stg-smoke"` filter, and
> `tests/contract/test_smoke_tenant_isolation.py` asserts (i) exactly
> one role assignment exists for the `Simulation.Coordinator`
> principal across the entire Bicep emission, scoped at
> `'${account.id}/dbs/${databaseName}'`, and (ii) zero production-
> tenant role assignments reference the same principal. Strengthening
> to true partition-level RBAC isolation is deferred to a backlog
> issue ([backlog issue: TBD]; the placeholder is replaced atomically
> when the issue is filed at Step 8ae): Cosmos data-plane RBAC API
> version 2024-08-15 does not officially support per-partition-key-
> value scope in `az rest` deploys, and uptake of either (a) a custom
> role definition with conditional access policies or (b) a separate
> Cosmos database for the smoke tenant — Alternative #6 above,
> previously rejected — is gated on that API uplift."*

The corrected wording uses **both** phrasings in combination — they
are not mutually exclusive (Cycle 4 Pass 1 Q2, `spec.md:4083-4157`):
the security-pattern name *"compensating defence-in-depth control"*
(NIST SP 800-160 / OWASP / PCI-DSS lineage) AND the inline backlog-
issue citation. The single-token *"documented mitigation with
deferred remediation"* phrasing was considered and **rejected**: it
elides the technical security-pattern name and is weaker than
"compensating control" in PCI-DSS / SOC 2 audit contexts where the
latter is a term of art with bounded meaning.

#### Bicep is unchanged

`infra/bicep/modules/cosmos-simulation-containers.bicep` requires
**no edit** (`spec.md:3907`). The role-assignment resource at L316
is correctly declared with `scope:
'${account.id}/dbs/${databaseName}'`, and the comment block at
L305-315 already documents the actual scope and the compensating
defence-in-depth control honestly — the Bicep author's prior naming
choice is repository-internal precedent for the corrected wording's
*"compensating"* language. Step 8ae **MAY** (OPTIONAL) rewrite the
comment block to use the canonical phrase from the corrected wording
above AND insert the backlog issue id citation; this rewrite is not
mandatory and is gated on whether the Pass 2 Q4 optional assertion
(h) `test_bicep_comment_block_documents_compensating_control` is
taken in `tests/contract/test_smoke_tenant_isolation.py` extension
(`spec.md:4720-4742, 4796-4803`).

#### Smoke-tenant-isolation contract test extension

`tests/contract/test_smoke_tenant_isolation.py` is extended in
Step 8ae with **one required** new `def test_*` function and **one
optional** new `def test_*` function (Cycle 4 Pass 2 Q4,
`spec.md:4679-4814`):

- **REQUIRED**: `def test_smoke_role_assignment_scope_is_database_level`
  asserts the Bicep text contains
  `scope: '${account.id}/dbs/${databaseName}'` literally on the
  `smokeCoordinatorRoleAssignment` resource (regex:
  `scope:\s*'\$\{account\.id\}/dbs/\$\{databaseName\}'` within the
  `sqlRoleAssignments` resource block) AND that no narrower
  `pks/${...}` (per-partition-key) suffix nor broader account-level
  scope (`scope: '\$\{account\.id\}'` with no `/dbs/...` suffix)
  appears. Failure message verbatim: *"A4-02 invariant: role
  assignment scope MUST be database-level
  `'${account.id}/dbs/${databaseName}'` per the corrected
  ADR-036-011 wording — got <observed scope>; see `spec.md:3906`
  for the binding wording"* (`spec.md:4707-4719`).
- **OPTIONAL**: `def test_bicep_comment_block_documents_compensating_control`
  asserts the comment block at
  `infra/bicep/modules/cosmos-simulation-containers.bicep:305-315`
  contains both (h-i) the literal phrase `compensating defence-in-
  depth control` (or the existing semantic equivalent at L309-310
  if the comment block is not rewritten) AND (h-ii) the GitHub
  backlog issue URL or id (placeholder `[backlog issue: TBD]`
  accepted with a `# TODO(Step 8ae close): replace TBD with actual
  issue id` comment until the issue is filed —
  `spec.md:4720-4736`).

The test file gains 1 (required) or 2 (full) new `def test_*`
functions; the existing six functions
(`test_smoke_role_assignment_resource_present`,
`test_smoke_role_assignment_is_conditional_on_coordinator_principal`,
`test_smoke_tenant_id_defaults_to_contract_value`,
`test_smoke_role_assignment_name_uses_smoke_tenant_id_in_guid`,
`test_smoke_role_uses_builtin_data_contributor_role`,
`test_no_production_tenant_role_assignment_for_coordinator`) remain
unchanged. The module-level docstring header at L1-30 is updated
symmetrically by Step 8ae to list the new assertion(s).

#### Spec-body re-render of the superseded Cycle 3 wording

The Cycle 3 Pass 1 Q2 item (v) narrative wording at
`spec.md:961-966` is **explicitly superseded** by the binding
corrected wording recorded at `spec.md:3906` (per the Cycle 2 Q1
supersession precedent at `spec.md:389-392`). The original Cycle 3
narrative is preserved verbatim per the within-cycle immutability
discipline at `spec.md:3905, 3947-3950`; Step 8ae re-renders the
corrected wording in the spec body alongside the original
(preserved verbatim) and links to the A4-02 anchor at
`spec.md:3896-3915` (Pass 1 Q2 propagation `spec.md:4140-4145`).

### GitHub backlog issue (Pass 1 Q3)

The deferred Cosmos data-plane RBAC partition-key-scope strengthening
is tracked as a **GitHub issue only** — no `docs/backlog/` markdown
entry (Cycle 4 Pass 1 Q3 binding decision at `spec.md:4159-4217`).
A repository scan during Pass 1 confirmed neither convention is
currently established (no `.github/ISSUE_TEMPLATE/` directory, no
`docs/backlog/` directory at the time of Cycle 4 close —
`spec.md:4163-4166`).

- **Title prefix**: `[backlog]` — e.g. *"[backlog] Cosmos data-plane
  RBAC: per-partition-key scope (blocked on API ≥ 2024-08-15+)"*.
- **Body**: cites A4-02 acceptance criterion (`spec.md:3912`); Bicep
  site (`infra/bicep/modules/cosmos-simulation-containers.bicep:316`);
  Cosmos data-plane RBAC API version 2024-08-15 constraint as the
  explicit blocker; the two strengthening alternatives — (a) custom
  role definition with conditional access policies, (b) separate
  Cosmos database for the smoke tenant (Alternative #6 above,
  previously rejected) — both deferred until the API uplift.
- **Label**: `backlog` IF the repo's labels inventory already
  contains it; otherwise no label (do NOT create a new label as a
  side-effect — `spec.md:4181-4183`).
- **Inline references**: the issue URL is referenced from (1) the
  corrected L172-173 wording above (replacing the
  `[backlog issue: TBD]` placeholder atomically); (2) Alternative #6
  row in § "Alternatives Considered" above (replacing any
  placeholder); (3) the optional forward-reference comment in
  `cosmos-simulation-containers.bicep:305-315` if Pass 2 Q4 optional
  assertion (h) is taken at Step 8ae.
- **`docs/backlog/` deferral**: forward-compatible — if a future
  cycle introduces a `docs/backlog/index.md` convention, a one-line
  entry referencing the GitHub issue can be added at that point;
  this is NOT a Cycle 4 work-item.

Placeholder discipline: until the issue id is known at Step 8ae
implementation time, every site that cites the issue uses the literal
substring `[backlog issue: TBD]` and (where applicable) carries a
`# TODO(Step 8ae close): replace TBD with actual issue id` comment.
The placeholder is replaced **atomically** in a single commit when
the issue is filed.

### Multi-cycle Status convergence rule (Pass 2 Q3)

The Status field of this ADR (currently `Proposed` per the document
header at line 3) follows a deterministic multi-cycle convergence
rule (Cycle 4 Pass 2 Q3 binding decision, `spec.md:4595-4677`):

1. During Cycle 4 implement (Step 8ae), this Cycle 4 amendment
   sub-section is appended to ADR-036-011 with the Status field
   **unchanged** (remains `Proposed` from the Cycle 3 close).
2. At Step 8al cohort re-review, **if all three cohorts (sectors /
   operational / technical) return 0 OBJECT votes AND 0 NEW
   merit-validated findings against ADR-036-011** (matching the
   user's standing convergence rule cited at `spec.md:90-91`), the
   Status field flips `Proposed` → `Accepted` in that same Step-8al-
   close commit, AND this Cycle 4 amendment sub-section gains a
   closing line *"Cycle 4 cohort re-review verdict: 0 OBJECT, 0 NEW
   findings — Status moved Proposed → Accepted on YYYY-MM-DD per
   `spec.md:4595-4677` (Pass 2 Q3 convergence rule)"*.
3. If Step 8al surfaces ≥1 OBJECT vote OR ≥1 NEW merit-validated
   finding against ADR-036-011, Status remains `Proposed` and the
   next cycle (Cycle 5) opens — the Status flip is deferred to
   Cycle 5+'s Step-8X re-review under the same rule recursively.
4. There is **no time-bound auto-flip**: Status MUST NOT flip to
   `Accepted` after N days absent a clean cohort re-review verdict.
   The flip is gated solely on the verdict, not on calendar time.
5. The rule applies recursively across Cycle 5 / Cycle 6 / ...:
   Status flips `Proposed → Accepted` only on the **first** clean
   cohort re-review verdict, and **never reverts** once Accepted.
   Subsequent cycles MAY append additional amendment sub-sections,
   but those amendments target the Accepted ADR rather than
   re-opening its Status — the immutability discipline at
   `spec.md:3947-3950` applies recursively.

This rule is recorded inline within this Cycle 4 amendment sub-section
so future maintainers reading ADR-036-011 in isolation see the
convergence rule alongside the Status field and do not flip
prematurely (Pass 2 Q3 propagation requirement at
`spec.md:4633-4637`).

### CHANGELOG.md format (Pass 2 Q2)

The Cycle 4 close emits a CHANGELOG.md grouped block under the
existing `## [Unreleased]` heading at `CHANGELOG.md:5`, mirroring
the **Cycle 2 precedent** at `CHANGELOG.md:7-31` (Cycle 4 Pass 2
Q2 binding decision, `spec.md:4507-4593`). The orchestrator-suggested
single-bullet `- A4-XX <one-sentence-summary>` format has **zero
in-repo precedent** (verified via `Select-String -Path 'CHANGELOG.md'
-Pattern '^- A\d+-\d+'` → no matches) and is **explicitly rejected**.

The Cycle 4 grouped block contains **at minimum two** sub-sections
(no `### Breaking changes` because A4-01 is an FR strengthening with
backward-compatible KQL surface and A4-02 is documents-only):

- **`### Added (spec 036 — Cycle 4 amendment cycle)`**:
  - One bullet for the new
    `tests/contract/test_sli_kql_runtime_validity.py` (citing
    `(A4-01 / FR-073)` inline).
  - One bullet for the new GitHub backlog issue URL once filed
    (citing `(A4-02)` inline).
- **`### Changed (spec 036 — Cycle 4 amendment cycle)`**:
  - One bullet for the FR-073 column-resolution sub-bullet
    strengthening (citing `(A4-01 / FR-073)` inline).
  - One bullet for the symmetric Z7 KQL `extend model_deployment`
    fix in `infra/observability/sli-kql.json` and
    `contracts/sli-thresholds.md` (citing `(A4-01 / FR-073)`
    inline).
  - One bullet for the `tests/contract/test_smoke_tenant_isolation.py`
    extension (citing `(A4-02)` inline; Pass 2 Q4 extension scope —
    REQUIRED scope-string assertion, OPTIONAL comment-block
    assertion).
  - One bullet for the ADR-036-011 wording correction with the
    *"compensating defence-in-depth control"* phrase + backlog-
    issue citation (citing `(A4-02)` inline).

The post-Cycle-4-implement test count delta (3391 → 3399 / 3400) MAY
appear as a short closing line within the `### Added` or `### Changed`
block, NOT as its own sub-section. Each bullet is a verbose paragraph
citing file:line evidence and inline `(AN-XX / FR-YYY)` provenance
tags consistent with the Cycle 2 precedent at `CHANGELOG.md:8`.

Pass 2 Q2 also requires a **retroactive Cycle 3 grouped block**
(`spec.md:4576-4584`) — Cycle 3 implement is complete per the Cycle 3
sentinel at `spec.md:3829` but the CHANGELOG block was not yet
written at that close (deferred to the cohort-re-review-clean state).
Step 8ad MAY write the Cycle 3 grouped block retroactively if it has
not yet been written by Step 8ab; verify-first.

### Test count convergence

The Cycle 3 baseline is **3391 tests pass / 0 fail** (`spec.md:3829`).
Cycle 4 introduces a multi-stage test-count math which has been
superseded twice within the cycle:

- **Pass 1 Q1** (`spec.md:3893, 4381`) initially recorded *"3392
  tests pass / 0 fail expected post-Cycle-4-implement"* on the
  implicit assumption that `test_sli_kql_runtime_validity.py`
  contributes 1 test.
- **Pass 2 Q1** (`spec.md:4427-4505`) **superseded** the 3392 figure
  with **3398** based on live pytest verification — the new test is
  parametric over Z1–Z7 and pytest collects 7 distinct ids per
  parametric `def test_*` function (verified via `pytest tests/contract/test_sli_kql_canonical_match.py
  --collect-only -q` reporting *"7 tests collected"*). 3391 + 7 =
  **3398**.
- **Pass 2 Q4** (`spec.md:4679-4814`) **further superseded** the
  3398 figure with **3399** (REQUIRED scope-string assertion only)
  or **3400** (REQUIRED scope-string + OPTIONAL comment-block
  assertion both taken). The choice between 3399 and 3400 is
  recorded at Step 8ae implementation time in `tasks.md` per
  Pass 2 Q4 propagation at `spec.md:4791-4795`.

The **binding** post-Cycle-4-implement total cited by this ADR is
**3399** (minimal Step 8ae posture) or **3400** (full Step 8ae
posture). The Pass 1 lines at `spec.md:3893` and `spec.md:4381` and
the Pass 2 Q1 line at `spec.md:4429-4452` remain in the spec
verbatim per the within-cycle immutability discipline; this Cycle 4
amendment sub-section is the canonical authority for the binding
total. Step 8ad's CI gate / Step 8ae's `tasks.md` acceptance MUST
cite **3399** or **3400** — never 3392 or 3398.

### References (Cycle 4)

- Spec FR-073 strengthening (Cycle 4 — A4-01): `spec.md:3886, 3922-3934`
  (the (a)–(c) author-time column-resolution discipline).
- `specs/036-sim-agent-extend/spec.md` § "Cycle 4 Amendment Log
  (post Step 8ac cohort re-review, 2026-05-11)" (`spec.md:3830-3967`).
- `specs/036-sim-agent-extend/spec.md` § "Clarifications (Cycle 4 —
  Pass 1)" Q1..Q5 (`spec.md:3969-4385`).
- `specs/036-sim-agent-extend/spec.md` § "Clarifications (Cycle 4 —
  Pass 2)" Q1..Q4 (`spec.md:4387-4866`).
- `specs/036-sim-agent-extend/plan.md` § "Cycle 4 Plan Decisions
  (Step 8ad / 8ae, 2026-05-11)" PD-C4-01 + PD-C4-02 (Cycle 4 plan-
  decisions appended Step 8ad).
- `specs/036-sim-agent-extend/checklists/quality.md` (CHK197..CHK230,
  Cycle 4 quality rows added Step 8ad).
- `infra/observability/sli-kql.json:91` (Z7 KQL — site of the A4-01
  symmetric fix).
- `specs/036-sim-agent-extend/contracts/sli-thresholds.md:280-296`
  (Z7 KQL §6b — site of the symmetric fix on the contract side).
- `infra/bicep/modules/cosmos-simulation-containers.bicep:305-315`
  (comment block — already-correct documentation of the database-
  level scope and compensating defence-in-depth control); L316
  (role-assignment resource — correct as-is, no change).
- `tests/contract/_kql_canonicaliser.py` (re-used; Cycle 3 Step 8z
  contract surface; no edit in Cycle 4).
- `tests/contract/test_sli_kql_canonical_match.py` (verify-only;
  must continue to pass byte-equality across Z1–Z7 after the
  symmetric Z7 fix).
- `tests/contract/test_sli_kql_runtime_validity.py` (NEW; Step 8ad
  parametric-over-Z1–Z7 author-time column-resolution contract test).
- `tests/contract/test_smoke_tenant_isolation.py` (Step 8ae extension
  — REQUIRED scope-string assertion + OPTIONAL comment-block
  assertion).
- NIST SP 800-160 Vol. 1 §3 ("Defense-in-Depth"); OWASP defence-in-
  depth taxonomy; PCI-DSS v4.0 §"Compensating Controls" definition
  — linguistic anchors for the *"compensating defence-in-depth
  control"* phrase in the corrected L172-173 wording.

---

*Cycle 4 amendment sub-section appended 2026-05-11 by `/speckit.plan`
(Step 8ad plan landing). Status remains `Proposed` per Pass 2 Q3
multi-cycle convergence rule above; flip to `Accepted` is gated on
Step 8al's clean cohort verdict. The L172-173 in-place rewrite of the
A-2 / Sub-decision (iii) point (5) wording lands at Step 8ae per the
dependency-edge note in `plan.md` § "Step 8ad / 8ae dependency-edge
note (Cycle 4)". No new ADR-036-012 is created.*

---

## Cycle 5 amendment (2026-05-11)

> **Scope of this sub-section**: Appended per the Cycle 4 Pass 1 Q5
> in-place ADR revision pathway (`spec.md:4288-4351`) applied recursively
> per Cycle 5 Pass 2 Q4 verbatim restatement (`spec.md:5863-5897`). All
> Cycle 3 / Cycle 4 content above (lines 1-941) is preserved verbatim.
> The L172-184 binding wording (the three-clause acknowledgement landed
> by A4-02 at Cycle 4 close) is **NOT re-amended** (out-of-scope per
> `spec.md:4979`). Added by `/speckit.plan` Step 8aq plan landing; the
> actual Bicep comment-block rewrite + test docstring/header-comment
> update + two new `.lower()` + `in` absence assertions land at Step 8at
> (Cycle 5 implement) per the dependency-edge note in `plan.md` §
> "Step 8aq / 8ar / 8at dependency-edge note (Cycle 5)".

### Cycle 5 trigger

The **Step 8al cohort re-review** (cross-cohort re-review of Cycle 4's
*own* deliverables — distinct from Step 8ac which targeted Cycle 3's
deliverables) returned **Operational 🟢 GREEN PROCEED** (10 ACCEPT / 0
RESERVATIONS / 0 OBJECT; 0 NEW findings), **Sectors 🟢 GREEN PROCEED**
(54 ACCEPT / 4 carry-forward RESERVATIONS / 0 OBJECT; 0 NEW findings),
and **Technical 🟡 YELLOW** (16 ACCEPT / 1 RESERVATION / 0 OBJECT;
**1 NEW MEDIUM** — F-TECH-4-01 from infrastructure-devops). The Cycle 3
data-engineer OBJECT verdict on the Z7 KQL `extend model_deployment`
defect is **closed** by direct file inspection of
`infra/observability/sli-kql.json:91` and
`specs/036-sim-agent-extend/contracts/sli-thresholds.md:288-290`
(`spec.md:4908-4915`); the keystone is removed. One residual defect
remains:

- **F-TECH-4-01** (MEDIUM, infrastructure-devops cohort, technical
  triple) —
  `infra/bicep/modules/cosmos-simulation-containers.bicep:305-309`
  retain a verbatim pre-Cycle-4 preamble leading at L305 with *"Scope
  the assignment to the smoke-tenant partition path"* and at L306-308
  with an illustrative resolution
  `/subscriptions/<sub>/resourceGroups/<rg>/.../dbs/<db>/colls/<container>/pks/<tenant_id>`.
  These phrasings contradict the actual database-level scope at L328
  (`scope: '${account.id}/dbs/${databaseName}'` — unchanged by
  Cycle 4 and confirmed correct at the Step 8al
  azure-principal-architect ACCEPT verdict citing L328 verbatim), the
  corrected ADR-036-011 wording at :172-184, and the spec.md A4-02
  binding wording at :3907-3925. The Cycle 4 A4-02 amendment ADDED the
  correct wording at L317-327 of the same Bicep module but did NOT
  REMOVE the OLD pre-Cycle-4 preamble at L305-315 — the two blocks
  contradict each other within a single contiguous comment block
  (L305-327). The defect is **documentation-only**: the compiled Bicep
  `scope:` expression is correct and unchanged; runtime RBAC behaviour
  is identical. Codified as Cycle 5 amendment **A5-01**
  (`spec.md:4943, 4947-4992`).

Ground-truth report `step-8al-rereview-technical.md` § "NEW findings"
row + § "infrastructure-devops — RESERVATIONS" is held in the session
workspace
`C:\Users\prbillir\.copilot\session-state\ddfe017a-c801-4ecd-b4ba-986fe32d7afd\files\`
(`spec.md:4892-4895`). Cycle 5 is **narrower in scope** than Cycle 4
(`spec.md:4896-4901`): 0 new FRs, 0 new SCs, 0 FR strengthenings
(pure DOC-FIX, narrower than Cycle 4's A4-01 FR-073 sub-bullet
strengthening), 0 new self-documentation supersessions, 1
OPTIONAL→REQUIRED prose promotion (Pass 2 Q1 — `spec.md:5498-5614`).
Three Pass 1 Q→A and four Pass 2 Q→A clarifications resolved seven
Q→A entries between them (`spec.md:5037-5453` Pass 1;
`spec.md:5455-5994` Pass 2).

### A5-01 resolution scope (documentation-only — no runtime/RBAC change)

A5-01 is **purely documentation**: the L305-315 Bicep preamble is
rewritten in place (Step 8at) to consolidate with the existing Cycle 4
A4-02 sub-block at L317-327 into a single coherent comment block. The
actual `scope:` expression at L328 is **byte-identical** to the
Cycle 4 baseline (`scope: '${account.id}/dbs/${databaseName}'`) and
**MUST NOT be modified** — any change is a Cycle 5 scope-creep
violation (`spec.md:4980`). Pass 1 Q1 (`spec.md:5067-5096`) pins the
consolidated block's top-down ordering: (1) database-level scope
statement citing the Cosmos data-plane RBAC API 2024-08-15
constraint; (2) compensating defence-in-depth control phrasing;
(3) joint enforcement clauses (SLI-Z6 / SLI-Z7 query-time
`where tenant_id == "tnt-stg-smoke"` filter +
`customDimensions["tenant_id"]` envelope discriminator);
(4) `[backlog issue: #84]` citation. The ordering is byte-identical
in sequence to (a) the ADR-036-011:172-184 binding narrative,
(b) the existing Cycle 4 A4-02 sub-block at
`cosmos-simulation-containers.bicep:317-327`, and (c) the
F-TECH-4-01 recommended remediation in
`step-8al-rereview-technical.md` § "NEW findings". Runtime RBAC
behaviour is unchanged: no compiled scope change, no role-assignment
count change, no role-definition-id change, no principal-id change.
Strengthening to true partition-level isolation continues to be
deferred to backlog issue **#84** (filed at Cycle 4 implement close
per `spec.md:4886`); #84 remains open at Cycle 5 close and is cited
verbatim in the rewritten preamble (quality.md CHK241).

### A5-01 test surface extension

`test_bicep_comment_block_documents_compensating_control` at
`tests/contract/test_smoke_tenant_isolation.py:250-297` (introduced
Cycle 4 Step 8ae per the function's docstring at L253) is **extended
in place** with two new `assert ... not in role_block.lower()`
statements per Pass 1 Q2 + Pass 2 Q2 (`spec.md:5175-5240, 5648-5754`):
**(i)** `assert "pks/<tenant_id>" not in role_block.lower(), (...)`
— guards the exact resolution-string example F-TECH-4-01 identifies
at L306-308 of the current Bicep;
**(ii)** `assert "partition path" not in role_block.lower(), (...)`
— guards the false claim at L305 of the current Bicep (*"Scope the
assignment to the smoke-tenant partition path"*). Both assertions
consume `_extract_role_assignment_block(bicep_text)` at L220-247
(canonical scope-narrowing primitive — same helper as the two
existing presence assertions, per Pass 1 Q3 at
`spec.md:5299-5418`). The `.lower()` + plain `in` substring check is
the binding case-folding primitive (Pass 2 Q2); the
`re.compile(..., re.IGNORECASE)` and `str.casefold()` alternatives
offered in Pass 1 Q2 are **explicitly rejected** for simplicity,
no-regex-metacharacters, and within-file symmetry with the existing
`tnt-prod` absence check at L166. The two existing presence
assertions (`compensating_re.search(role_block)` at L271-282 and
`backlog_re.search(role_block)` at L286-297) remain
**byte-identical** — the two new option-(b) assertions are additive,
not replacements (quality.md CHK235). No `pytest.mark.skip`,
`pytest.mark.xfail`, `pytest.mark.skipif`, or conditional decorator
is added (quality.md CHK243 anti-pattern guard).

### T-AA52 OPTIONAL → REQUIRED prose promotion (Pass 2 Q1)

The Cycle 4 Pass 2 Q4 minimal-3399 / FULL-3400 posture split
(`spec.md:4795-4801`) is **retired** by Cycle 5 Pass 2 Q1
(`spec.md:5498-5614`). The promotion is **prose-only**: pytest
already collects
`test_bicep_comment_block_documents_compensating_control`
unconditionally (no `pytest.mark.*` decorator, no skipif gate, no
env-var fixture); the OPTIONAL label was purely the docstring at
`tests/contract/test_smoke_tenant_isolation.py:253` plus the header
comment at L173. F-TECH-4-01 was missed precisely because the test
was labelled OPTIONAL — the wording-residue defect lives inside the
same comment block T-AA52 already inspects, but the existing
assertions assert **presence** of correct phrasing, not **absence**
of incorrect phrasing, and the OPTIONAL label signalled the
assertion-block was non-binding. Step 8at updates the docstring at
L253 and the header comment at L173 to record the REQUIRED
disposition (verbatim text pinned at `spec.md:5568-5586`); no
`pytest.mark.*` decorator is added or removed (runtime disposition
is unchanged — the test was already collected unconditionally at
Cycle 4 close per `tasks.md:2527`).

### Test count convergence (Cycle 5)

Pre-Cycle-5: **3400 tests pass / 0 fail (FULL posture)** per the
Cycle 4 implement close sentinel at `spec.md:4886`. Post-Cycle-5:
**3400 tests pass / 0 fail (single posture, no minimal/FULL split)**
— the numerical count is unchanged; the material change is
dispositional (Pass 2 Q3 at `spec.md:5774-5859`). The Cycle 4 Pass 2
Q4 minimal-3399 escape hatch at `spec.md:4795-4801` is **retired**
by the Pass 2 Q1 REQUIRED promotion. Cycle 5 implement delta is
**+0** (test extended in place; no new `def test_*` function, no
parametrize axis widening, no new test file). Step 8at's
`python -m pytest -q` gate MUST return returncode 0 AND
collected-node count exactly **3400** with zero
`skipped` / `xfailed` / `xpassed` qualifier for T-AA52
(quality.md CHK236, CHK242).

### Multi-cycle Status convergence rule (Pass 2 Q4 restatement)

The Cycle 4 Pass 2 Q3 rule at `spec.md:4636-4684` (recorded in this
ADR at the Cycle 4 amendment sub-section above) applies
**recursively** to Cycle 5 close. Cycle 5 Pass 2 Q4
(`spec.md:5863-5897`) restates the rule verbatim. The Status field
of this ADR (currently `Proposed` per the document header at line 3)
**remains `Proposed`** through this Cycle 5 sub-section append
(Step 8aq) and through Step 8at (Cycle 5 implement); the Status flip
is gated **solely** on the Step 8au cohort re-review verdict:

1. IF Step 8au returns `0 OBJECT votes AND 0 NEW merit-validated
   findings against ADR-036-011` from **all three cohorts**
   (operational, sectors, technical), THEN in the same Step 8au
   close commit (a) flip ADR-036-011 Status from `Proposed` to
   `Accepted`; (b) record the flip in the Cycle 5 close-block
   sentinel; (c) the ADR is locked from further revision under the
   *"no revert once Accepted"* clause. Step 9 (`azd up` staging
   deploy) unlocks on the `Accepted` Status (quality.md CHK244).
2. IF Step 8au surfaces ≥1 OBJECT vote OR ≥1 NEW merit-validated
   finding against ADR-036-011, Status remains `Proposed`; Cycle 6
   opens under the same recursive rule. The Cycle 5 → Cycle 6
   surface is expected to narrow further (A5-01 is a single MEDIUM
   doc-fix; a hypothetical Cycle 6 surface would be at most LOW or
   empty per `spec.md:5023-5025`).
3. The rule applies **recursively** across all future cycles; no
   time-bound auto-flip; no revert once Accepted. Cycle 4 close did
   not flip the Status because Step 8al surfaced F-TECH-4-01 as a
   NEW merit-validated finding; Cycle 5 close has the next
   opportunity.

### CHANGELOG.md format (Pass 2 Q1 propagation)

The Cycle 5 close (Step 8at) emits a CHANGELOG.md grouped block
under the existing `## [Unreleased]` heading at `CHANGELOG.md:5`,
mirroring the Cycle 4 grouped-sub-section format precedent
established at Cycle 4 Pass 2 Q2 (`spec.md:4507-4593`) and recorded
at `CHANGELOG.md:7-15` (quality.md CHK240). At minimum one
sub-section (no `### Added` because no new file lands; no
`### Breaking changes` because A5-01 is documents-and-test-only and
non-breaking):

- **`### Changed (spec 036 — Cycle 5 amendment cycle)`**:
  - One bullet for the consolidated Bicep comment block rewrite at
    `infra/bicep/modules/cosmos-simulation-containers.bicep:305-315`
    (citing `(A5-01)` inline).
  - One bullet for the two new option-(b) absence assertions
    appended to
    `test_bicep_comment_block_documents_compensating_control` at
    `tests/contract/test_smoke_tenant_isolation.py:250-297` (citing
    `(A5-01 / F-TECH-4-01)` inline).
  - One bullet for the T-AA52 OPTIONAL → REQUIRED prose promotion
    (docstring at L253 + header comment at L173 rewrite; citing
    `(A5-01 / Cycle 5 Pass 2 Q1)` inline).
  - One bullet for the dispositional collapse (Cycle 4 Pass 2 Q4
    minimal-3399 escape hatch retired; single 3400 posture binding
    going forward; citing `(A5-01 / Cycle 5 Pass 2 Q3)` inline).

The single-bullet `- A5-XX <one-sentence-summary>` format is
**explicitly rejected** per the Cycle 4 Pass 2 Q2 ruling (zero
in-repo precedent — `spec.md:4513-4516`).

### References (Cycle 5)

- `specs/036-sim-agent-extend/spec.md` § "Cycle 5 Amendment Log
  (post Step 8al cohort re-review, 2026-05-11)"
  (`spec.md:4888-5035`).
- `specs/036-sim-agent-extend/spec.md` § "Clarifications (Cycle 5
  — Pass 1)" Q1..Q3 (`spec.md:5037-5453`).
- `specs/036-sim-agent-extend/spec.md` § "Clarifications (Cycle 5
  — Pass 2)" Q1..Q4 (`spec.md:5455-5994`).
- `specs/036-sim-agent-extend/plan.md` § "Cycle 5 Plan Addendum
  (post Step 8al cohort re-review amendments)" PD-C5-01 (appended
  Step 8aq in the same plan landing as this sub-section).
- `specs/036-sim-agent-extend/checklists/quality.md`
  (CHK231..CHK244, Cycle 5 quality rows added Step 8ap).
- `infra/bicep/modules/cosmos-simulation-containers.bicep:305-315`
  (A5-01 rewrite site at Step 8at); L317-327 (existing Cycle 4
  A4-02 sub-block — preserved in place; consolidation happens
  *around* it, not *through* it); L328 (actual `scope:` expression
  — byte-identical to the Cycle 4 baseline; **MUST NOT be
  modified**).
- `tests/contract/test_smoke_tenant_isolation.py:250-297` (the
  `test_bicep_comment_block_documents_compensating_control`
  function extended by A5-01); L220-247
  (`_extract_role_assignment_block` helper — re-used, no edit);
  L173 (header comment — rewritten to record T-AA52 REQUIRED
  promotion); L253 (docstring — rewritten to record T-AA52
  REQUIRED promotion); L166 (the `tnt-prod` absence-check
  precedent that the two new option-(b) assertions inherit
  byte-symmetrically).
- F-TECH-4-01 ground-truth: `step-8al-rereview-technical.md`
  § "NEW findings" row + § "infrastructure-devops —
  RESERVATIONS" (session workspace
  `C:\Users\prbillir\.copilot\session-state\ddfe017a-c801-4ecd-b4ba-986fe32d7afd\files\`).
- Cycle 4 Pass 2 Q3 multi-cycle Proposed→Accepted convergence rule
  at `spec.md:4636-4684` (recorded in this ADR at the Cycle 4
  amendment sub-section above) — applied recursively to Cycle 5
  close per the Cycle 5 Pass 2 Q4 verbatim restatement at
  `spec.md:5863-5897`.
- Backlog issue **#84** (Cosmos RBAC partition-scope upgrade,
  filed at Cycle 4 implement close per `spec.md:4886`) — remains
  open at Cycle 5 close; cited verbatim as `[backlog issue: #84]`
  in the rewritten Bicep preamble (Pass 1 Q1 ordering element (4))
  and in this Cycle 5 sub-section.

---

*Cycle 5 amendment sub-section appended 2026-05-11 by
`/speckit.plan` (Step 8aq plan landing). Status remains `Proposed`
per the recursive Cycle 4 Pass 2 Q3 convergence rule (Cycle 5
Pass 2 Q4 verbatim restatement at `spec.md:5863-5897`); flip to
`Accepted` is gated **solely** on Step 8au's clean cohort re-review
verdict (0 OBJECT votes AND 0 NEW merit-validated findings against
ADR-036-011 from operational + sectors + technical cohorts). The
actual Bicep comment-block rewrite + test docstring/header-comment
update + two new `.lower()` + `in` absence assertions land at
Step 8at (Cycle 5 implement) per the dependency-edge note in
`plan.md` § "Step 8aq / 8ar / 8at dependency-edge note (Cycle 5)".
No new ADR-036-012 is created (Cycle 5 follows the Cycle 4 Pass 1
Q5 in-place revision pathway recursively).*
