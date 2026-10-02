# Amendment Requirements-Quality Checklist (Cycle 2): 040-success-criteria

**Purpose**: Unit-test the *requirements* introduced by the Cycle 2 amendment block (AMD-01..AMD-13 → FR-038..FR-050, SC-014..SC-022) and the residual clarifications in Cycle 2 — Round 1 (Q1–Q5) and Cycle 2 — Round 2 (Q1–Q3) of `spec.md`. Each item asks whether the new requirement is *complete, clear, consistent, measurable, and traceable* — not whether the implementation works.
**Created**: 2026-05-11
**Feature**: [spec.md](../spec.md) (Amendments — Cycle 2 block; Clarifications — Cycle 2 R1 + R2)
**Continues from**: [`success-criteria.md`](./success-criteria.md) CHK001..CHK068 (pre-amendment FR-001..FR-037 / SC-001..SC-013). Items here begin at **CHK069** and cover *only* FR-038..FR-050, SC-014..SC-022, AMD-01..AMD-13.

> Markers: `[Gap]` = appears missing, `[Ambiguity]` = vague, `[Conflict]` = inconsistent, `[Assumption]` = needs validation, `[Traceability]` = back-link required, `[Completeness]` / `[Clarity]` / `[Consistency]` / `[Measurability]` = which quality dimension the item tests.

---

## Audit Cold-Archive Immutability — FR-038 / SC-014 (AMD-01)

- [ ] CHK069 Is the audit Blob immutability period quantified as **exactly 2,555 days (= 7 × 365)** and not "≈7 years" / "84 × 30 days" anywhere in the requirement text? [Clarity, Spec §FR-038]
- [ ] CHK070 Does FR-038 explicitly require the immutability policy `state` to be **`Locked` at deployment time** (operator follow-up to lock explicitly disallowed)? [Completeness, Spec §FR-038]
- [ ] CHK071 Does FR-038 specify the deployment-failure semantics if the produced policy is unlocked OR shorter than 2,555 days (i.e., not just "should be" but "MUST fail")? [Measurability, Spec §FR-038]
- [ ] CHK072 Does SC-014 name the **exact property values** (`state=Locked`, `immutabilityPeriodSinceCreationInDays=2555`) the automated check must assert, leaving no interpretation latitude? [Measurability, Spec §SC-014]

## Append-Only Persistence Boundary — FR-040 / SC-016 (AMD-03)

- [ ] CHK073 Are the rejected HTTP verbs (`PATCH` and `DELETE`) exhaustively enumerated for `evidence_audit` mutation attempts (not "any mutation" / "write attempts")? [Completeness, Spec §FR-040]
- [ ] CHK074 Is the rejection HTTP status code **fixed at `409 Conflict`** (not the looser "4xx") with the rationale tied to RFC 9110 §15.5.10? [Clarity, Spec §FR-040, R1-Q2]
- [ ] CHK075 Does FR-040 require a `ProblemDetails` body whose `type` URI references FR-040 and whose `title` is **`"audit-record-immutable"`**? [Completeness, Spec §FR-040]
- [ ] CHK076 Is SC-016's "returns 4xx" wording reconciled with FR-040's pinned `409 Conflict` so a reviewer cannot satisfy SC-016 with a `400` or `403`? [Consistency, Spec §SC-016 vs §FR-040]
- [ ] CHK077 Does FR-040 require **each rejection to also append a tampering-attempt row** to `evidence_audit` (so SC-016's "recorded as a tampering attempt audit row" is unambiguously sourced)? [Completeness, Spec §FR-040, §SC-016]
- [ ] CHK078 Is the persistence-boundary enforcement mechanism (server-side stored procedure OR change-feed processor invariant) named — rather than left to implementer choice that could omit one? [Clarity, Spec §FR-040]
- [ ] CHK079 Does FR-040 require the change-feed → immutable Blob mirror to be **activated by the same Bicep deployment** (i.e., not a separate manual step)? [Clarity, Spec §FR-040]

## Public Information Accessibility — FR-039 / SC-015 (AMD-02 + R1-Q3)

- [ ] CHK080 Does FR-039 enumerate **all 7 canonical scenarios** and partition them into "Auslan-mandatory" (cyclone, bushfire, flood) vs "Auslan-deferred-permitted" (urban-fire, mass-casualty, hazmat, marine SAR)? [Completeness, Spec §FR-039]
- [ ] CHK081 Is the **`auslan-asset-missing` badge** requirement explicit for every deferred-permitted row (silent omission explicitly forbidden)? [Clarity, Spec §FR-039, R1-Q3]
- [ ] CHK082 Does FR-039 require deferred-Auslan rows to be tagged `provenance: manual` AND counted toward the FR-028 / SC-010 ≤50 % per-artefact manual cap? [Consistency, Spec §FR-039 vs §FR-028 / §SC-010]
- [ ] CHK083 Is the readability requirement quantified as **Flesch-Kincaid grade ≤ 8** with the assertion mechanism (Playwright readability check) named — rather than a vague "plain language"? [Measurability, Spec §FR-039]
- [ ] CHK084 Does FR-039 require **zero `serious` or `critical` axe-core violations** (rather than "WCAG-clean" / "no major issues") with the asserting tool named? [Measurability, Spec §FR-039]
- [ ] CHK085 Does FR-039 retain the FR-037 invariant that **all 8 text language channels** remain mandatory for **every** canonical scenario (i.e., the deferred-permitted relaxation applies only to Auslan media + transcript)? [Consistency, Spec §FR-039 vs §FR-037]
- [ ] CHK086 Does SC-015's pass criteria (axe-core zero serious/critical + FK ≤ 8 via Playwright) match the tools and thresholds named in FR-039 (no drift)? [Consistency, Spec §SC-015 vs §FR-039]

## Risk-Adjusted KPI Weighting — FR-041 / SC-017 (AMD-04 + R1-Q4)

- [ ] CHK087 Is the 5×5 weighting domain (`L`, `C` ∈ 1..5) and formula (`weight = (L*C)/25`) explicitly specified in FR-041 (not left to "standard 5×5 matrix")? [Clarity, Spec §FR-041]
- [ ] CHK088 Does FR-041 name the authoritative source of weights (spec 037 `docs/risk-register/`) AND the graceful-degradation default `(L=3, C=3)` when no matching row exists? [Completeness, Spec §FR-041]
- [ ] CHK089 Does FR-041 explicitly state defaulted-neutral `(3,3)` rows are tagged `provenance: manual` AND **count toward the FR-028 / SC-010 ≤50 % manual cap** (not treated as system-generated)? [Consistency, Spec §FR-041 vs §FR-028 / §SC-010, R1-Q4]
- [ ] CHK090 Is the publication-blocking behaviour defined when the manual-row share exceeds 50 %, with both unblocking paths enumerated ((a) replace with risk-register-sourced weights OR (b) named-auditor sign-off per spec 037 FR-037)? [Completeness, Spec §FR-041]
- [ ] CHK091 Does FR-041 require the **adjusted and unadjusted values to be rendered side-by-side** (not just "both available")? [Clarity, Spec §FR-041]
- [ ] CHK092 Does SC-017 require BOTH (a) every KPI in the seeded ladder has a non-null 5×5 weight AND (b) side-by-side adjusted/unadjusted render for **every** row (not a sampled subset)? [Measurability, Spec §SC-017]

## Production Fail-Fast on Missing AU Credentials — FR-042 / SC-018 (AMD-05)

- [ ] CHK093 Is the test-mode sentinel **exactly named** (`AMA_TEST_MODE=1` or pytest-detected equivalent) and scoped only to in-memory client activation? [Clarity, Spec §FR-042]
- [ ] CHK094 Does FR-042 require **startup failure** (not lazy / first-request / runtime failure) when production credentials are absent? [Measurability, Spec §FR-042]
- [ ] CHK095 Does the required startup-error message reference **both** FR-029 (AU sovereignty) and FR-042 (production-mode requirement) so the failure is self-documenting? [Traceability, Spec §FR-042]
- [ ] CHK096 Does SC-018 require a unit test that asserts the startup error **references FR-042 by name** (not merely "an error is raised")? [Measurability, Spec §SC-018]

## Bicep AU-Region Assertion — FR-043 / SC-019 (AMD-06)

- [ ] CHK097 Does FR-043 enumerate the **resource categories** whose `location` must be read at deploy-time (Cosmos, Storage, Application Insights, Log Analytics) — not a generic "bound resources"? [Completeness, Spec §FR-043]
- [ ] CHK098 Is the AU-allowed location set fixed to **`{australiaeast, australiasoutheast}`** (no other AU geos accepted)? [Clarity, Spec §FR-043]
- [ ] CHK099 Does FR-043 explicitly state that documented `@allowed` parameters alone are **NOT sufficient** (deploy-time assertion against the actual bound resource is required)? [Clarity, Spec §FR-043]
- [ ] CHK100 Does SC-019 require the `what-if` failure to surface a **clear AU-residency violation message** (not merely "deployment fails"), so a reviewer can mechanically verify intent? [Measurability, Spec §SC-019]

## AU-Refusal Audit Durability — FR-044 / SC-020(a) (AMD-07 + R2-Q2)

- [ ] CHK101 Does FR-044 retain account-level `Session`, explicitly prohibit an impossible Strong-per-request upgrade, and require both create-only Cosmos and locked-Blob acknowledgements before refusal? [Clarity, Spec §FR-044, 2026-09-24 resolution]
- [ ] CHK102 Is the **await-before-respond ordering** (durable Cosmos write 201 completes before the AU-refusal HTTP response is returned) explicit in FR-044? [Completeness, Spec §FR-044, R2-Q2]
- [ ] CHK103 Does FR-044 quantify the retry policy — **3 attempts with 250 ms / 1 s / 4 s exponential backoff** — for transient HTTP 5xx / 429 from Cosmos? [Clarity, Spec §FR-044, R2-Q2]
- [ ] CHK104 Does FR-044 require **`503 Service Unavailable` + `ProblemDetails` referencing FR-044** on retry exhaustion (explicitly NOT a swallowed exception followed by a 4xx refusal)? [Completeness, Spec §FR-044]
- [ ] CHK105 Does R2-Q2 preserve the approved Session-consistency AU two-region topology and prohibit adding a non-AU region to obtain stronger quorum semantics? [Consistency, Spec §FR-044 vs §FR-029, §FR-043]
- [ ] CHK106 Does R2-Q2 confirm the account-level `defaultConsistencyLevel: 'Session'` (per `eval-platform.bicep` portfolio default) MAY remain unchanged for non-audit containers (so FR-034 reuse invariant holds)? [Consistency, Spec §R2-Q2 vs §FR-034]
- [ ] CHK107 Is the 3-retry × backoff total bounded **below the FR-046 freshness SLO (≤ 60 s)** so the retry policy cannot independently breach the SLO budget? [Consistency, Spec §FR-044 vs §FR-046]
- [ ] CHK108 Does SC-020(a) require an integration test that asserts **`503` specifically when the audit write fails** (not a generic write-failure path)? [Measurability, Spec §SC-020]

## `/healthz/evidence` Probe Banding — FR-045 / SC-020(b) (AMD-08 + R1-Q1)

- [ ] CHK109 Does FR-045 enumerate the **critical** stores by exact container/resource name — every Cosmos container (`kpi_ladder`, `indicator_definition`, `measurement_method`, `scenario_run`, `delta_scorecard`, `causal_chain`, `benchmark`, `signal`, `evidence_audit`), the Blob immutable cold-archive container, and the Cosmos change-feed → Blob mirror processor? [Completeness, Spec §FR-045, R1-Q1]
- [ ] CHK110 Does FR-045 enumerate the **non-critical** stores (Application Insights ingestion endpoint + any read-only reporting/cache layer) and pin their failure posture to `200 + degraded:true`? [Completeness, Spec §FR-045, R1-Q1]
- [ ] CHK111 Does FR-045 explicitly require **removal of the hardcoded `evidence-audit-cold=True` shortcut** (not "audit shortcut should be reviewed")? [Clarity, Spec §FR-045]
- [ ] CHK112 Are the three response contract states — `503` (any critical down), `200 + degraded:true` (one+ non-critical degraded), `200 + degraded:false` (all healthy) — **mutually exclusive and exhaustive** (no undefined fourth state)? [Consistency, Spec §FR-045]
- [ ] CHK113 Is the rationale for the critical/non-critical partition tied back to FR-025 / FR-029 / FR-040 (AU-sovereignty + append-only invariants) vs FR-032 (graceful observability degradation), so the partition is principle-driven not arbitrary? [Traceability, Spec §FR-045 vs §FR-025 / §FR-029 / §FR-032 / §FR-040]
- [ ] CHK114 Does SC-020(b) require taking a backing store **actually offline** (not a mocked failure injected via test double) to assert `503`? [Measurability, Spec §SC-020]

## SLO Horizon, Burn Window & Action Group — FR-046 / SC-021 (AMD-09 + R1-Q5)

- [ ] CHK115 Does FR-046 quantify the SLO horizon as **rolling 30 days** (not "monthly" / "per-month")? [Clarity, Spec §FR-046, R1-Q5]
- [ ] CHK116 Does FR-046 quantify the burn-rate evaluation window as **rolling 1 hour for both 2 %/h and 5 %/h alerts** (not just "burn-rate alerts")? [Clarity, Spec §FR-046, R1-Q5]
- [ ] CHK117 Are the SLO targets — availability ≥ 99.5 %, replay success ≥ 98 %, freshness ≤ 60 s — each numeric with explicit comparator and unit? [Measurability, Spec §FR-046]
- [ ] CHK118 Does FR-046 mandate the Bicep parameter **`sloAlertActionGroupId`** as required, with deployment failing when empty in any non-test environment (mirroring FR-042 fail-fast posture)? [Completeness, Spec §FR-046, R1-Q5]
- [ ] CHK119 Does FR-046 explicitly **prohibit deferral** of any of (a) workbook, (b) SLO targets, (c) burn-rate alerts, (d) action-group binding to "operator follow-up"? [Clarity, Spec §FR-046]

## Burn-Rate Alert Severity — FR-046 / SC-021 (R2-Q3)

- [ ] CHK120 Does FR-046 assign **exactly `severity: 1`** to the 5 %/h fast-burn alert (paging tier)? [Clarity, Spec §FR-046, R2-Q3]
- [ ] CHK121 Does FR-046 assign **exactly `severity: 2`** to the 2 %/h slow-burn alert (ticketing tier)? [Clarity, Spec §FR-046, R2-Q3]
- [ ] CHK122 Does FR-046 explicitly **forbid `severity: 0`** for these alerts (reserved for total-outage signals per `observability-alerts.bicep` precedent)? [Clarity, Spec §FR-046, R2-Q3]
- [ ] CHK123 Is the severity assignment justified by named portfolio precedent files (so future reviewers can audit consistency) rather than by free-text rationale? [Traceability, Spec §R2-Q3]
- [ ] CHK124 Does SC-021 require `az deployment group what-if` to verify **both severities are present** in the to-be-created resource set (not just the existence of two alerts)? [Measurability, Spec §SC-021, R2-Q3]

## Pydantic `extra=forbid` + TS Twin Parity — FR-047 / SC-022(a) (AMD-10 + R2-Q1)

- [ ] CHK125 Does FR-047 require `model_config = ConfigDict(extra="forbid")` on **every** Pydantic v2 model under `apps/api/app/services/evidence/models/*.py` (not "the public-facing models")? [Completeness, Spec §FR-047]
- [ ] CHK126 Is the API rejection status fixed at **`422`** for unknown fields (not "4xx" / "400")? [Clarity, Spec §FR-047]
- [ ] CHK127 Does R2-Q1 explicitly state the TS twin under `packages/domain/src/evidence/` MUST remain **type-only** (no Zod, no class-validator) AND MUST NOT add a runtime `extra=forbid`? [Clarity, Spec §R2-Q1]
- [ ] CHK128 Does R2-Q1 require **schema parity** to be asserted by an OpenAPI-driven contract test against `specs/040-success-criteria/contracts/openapi.evidence-harness.yaml` (rather than by ad-hoc TS unit tests)? [Traceability, Spec §R2-Q1]
- [ ] CHK129 Does R2-Q1 cite the existing portfolio convention precedent (`packages/domain/src/app-role.ts`) so the "type-only twin" decision is anchored, not discretionary? [Traceability, Spec §R2-Q1]
- [ ] CHK130 Is SC-022(a)'s contract assertion (rejects unknown fields with 422) scoped to the **API boundary** consistent with R2-Q1 (no test attempts to assert TS-side runtime rejection)? [Consistency, Spec §SC-022 vs §R2-Q1]

## Language Fallback Disclosure — FR-048 / SC-022(b) (AMD-11)

- [ ] CHK131 Does FR-048 specify the **exact API field name and format** — `language_fallback_used: "<from_code>→<to_code>"` (with the `→` separator, not "->" or arbitrary)? [Clarity, Spec §FR-048]
- [ ] CHK132 Does FR-048 require a **UI badge near the affected content** (not a global toast, footer, or hidden log entry)? [Completeness, Spec §FR-048]
- [ ] CHK133 Does FR-048 explicitly **forbid silent downgrade** (so a future implementer cannot satisfy the requirement by logging only)? [Clarity, Spec §FR-048]
- [ ] CHK134 Does SC-022(b) require contract assertion that the field appears **whenever fallback occurs** (i.e., positive case asserted) AND is absent when no fallback occurs (negative case asserted)? [Measurability, Spec §SC-022]

## Benchmark Seed Coverage — FR-049 / SC-022(c) (AMD-12)

- [ ] CHK135 Does FR-049 quantify the minimum jurisdictional seed as **≥32 rows** (8 jurisdictions × ≥4 categories: primary fire, ambulance, SES, police) — derivable arithmetically? [Measurability, Spec §FR-049]
- [ ] CHK136 Does FR-049 enumerate the **cross-sector benchmark categories** (BoM warning lead-time per warning class, NEMA COMDISPLAN activation-to-deployment, ICAO ARFF response targets via Airservices Australia, SAIDI/SAIFI for utilities, AIIMS span-of-control 3–7) — not "and similar"? [Completeness, Spec §FR-049]
- [ ] CHK137 Does FR-049 mandate `source_citation` containing **organisation + document + year + URL** for every row (all four sub-fields, not "a citation")? [Clarity, Spec §FR-049]
- [ ] CHK138 Does FR-049 require unsourced rows to be tagged `provenance: manual` AND respect the FR-028 ≤50 % per-artefact manual cap? [Consistency, Spec §FR-049 vs §FR-028]
- [ ] CHK139 Does the amendment scope note confirm FR-049 does **not republish** external benchmark data (citations only — assumption #7)? [Consistency, Spec §Amendment Scope Notes]
- [ ] CHK140 Does SC-022(c) numerically split the assertion into **≥32 jurisdictional rows + ≥5 cross-sector rows** (not a single aggregate count) so each leg is independently verifiable? [Measurability, Spec §SC-022]

## Live Tab Data Wiring — FR-050 / SC-022(d) (AMD-13)

- [ ] CHK141 Does FR-050 enumerate **every** governance/evidence tab — KPI Ladder, Measurement Method, Replay Scorecard, Causal Chains, Benchmarks, Audit Trace, Public Information — with no "etc."? [Completeness, Spec §FR-050]
- [ ] CHK142 Does FR-050 specify each tab MUST **fetch live data from its corresponding `/api/v1/evidence/*` endpoint on mount** (not lazy / manual-refresh / deferred-until-tab-focus)? [Clarity, Spec §FR-050]
- [ ] CHK143 Does FR-050 require **explicit surfacing of all four state badges** — `degraded`, `small-sample`, `manual`, `reduced-fidelity` — per Round 2 Q3/Q4? [Completeness, Spec §FR-050]
- [ ] CHK144 Does FR-050 explicitly **forbid stub or placeholder content** (e.g., "populated by Phase 4") in any merged build? [Clarity, Spec §FR-050]
- [ ] CHK145 Does SC-022(d) require contract assertion that **every** governance/evidence tab fetches live data on mount (not a sampled subset)? [Measurability, Spec §SC-022]

## Cross-Cutting Amendment Quality

- [ ] CHK146 Are all 13 amendments (AMD-01..AMD-13) traceable **1:1 to at least one new functional requirement** (FR-038..FR-050) in the amendment table? [Traceability, Spec §Amendment Drivers vs §Functional Requirements (Amended / New)]
- [ ] CHK147 Are SC-014..SC-022 collectively consistent with FR-038..FR-050 such that **no new FR lacks at least one corresponding SC clause**? [Consistency, Spec §FR-038..FR-050 vs §SC-014..SC-022]
- [ ] CHK148 Does the amendment block preserve the spec 037 FR-037 **manual-row ≤50 % cap** across every newly introduced manual-tagging path (FR-039 deferred Auslan, FR-041 defaulted `(3,3)` weights, FR-049 unsourced citations)? [Consistency, Spec §Amendment Scope Notes vs §FR-039 / §FR-041 / §FR-049]
- [ ] CHK149 Are all amendment-introduced HTTP status codes (`409 Conflict`, `422 Unprocessable Entity`, `503 Service Unavailable`) and their associated `ProblemDetails` envelopes **consistent across FR-040, FR-044, FR-045, FR-047** (no contradictory status-code reuse)? [Consistency, Spec §FR-040, §FR-044, §FR-045, §FR-047]
- [ ] CHK150 Does the amendment block confirm the FR-034 invariant — **no new chart libraries, UI primitives, sim engines, or domain-validation primitives** are introduced (with R2-Q1 explicitly extending the invariant to forbid Zod/class-validator)? [Consistency, Spec §Amendment Scope Notes vs §R2-Q1]
- [ ] CHK151 Does the amendment block explicitly affirm **no change to the spec's capstone-criticality flag** and **no extension of any prior spec's scope** (so the amendments cannot be read as scope creep)? [Consistency, Spec §Amendment Scope Notes]
- [ ] CHK152 Does each Cycle 2 R1/R2 clarification carry an explicit **"Applied to: FR-xxx"** line so the resolved ambiguity is unambiguously bound to the amended requirement? [Traceability, Spec §Clarifications Cycle 2 R1+R2]

## Notes

- Check items off as completed: `[x]`
- Items CHK001..CHK068 cover the pre-amendment surface and live in [`success-criteria.md`](./success-criteria.md). Do NOT renumber.
- Each item asks whether the *requirement is well-written* — if you find yourself reaching for the implementation to answer, re-read the item against the cited spec section instead.
- Markers `[Gap]` / `[Ambiguity]` / `[Conflict]` / `[Assumption]` annotate the failure mode you would record on a "no" answer.
