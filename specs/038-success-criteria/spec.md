# Feature Specification: Measurable Success-Criteria Evidence Harness

**Feature Branch**: `038-success-criteria`
**Created**: 2026-05-11
**Status**: Draft
**Input**: User description: "Demonstrate that the AMA prototype's success criteria are MEASURABLE — show HOW the system would measure success, not actual production proof — through six evidence pillars: (1) KPI modelling, (2) measurement framework, (3) simulation logic, (4) expected impact reasoning, (5) benchmark comparisons, (6) instrumentation design."

## Context & Scope Boundary *(mandatory)*

This specification adds a **Measurable Success-Criteria Evidence Harness** to the existing Autonomous Multi-Agency disaster-response coordination hub (AMA). It is a **prototype evidence harness**, not a production telemetry platform. Its purpose is to demonstrate, end-to-end and audit-traceably, that each capstone success criterion *can be measured* by the prototype — including the formula, signal source, instrumentation hook, baseline, benchmark, and replayable scenario logic. It does **not** prove production performance, and does **not** make any operational claim about the live system.

**Capstone success criteria in scope** (owned externally by spec 015 SC-CAP-015-001..005):

1. ≥1,000 modelled lives saved per year of equivalent operational tempo.
2. ≥50 % reduction in coordinated response time vs prototype baseline.
3. ≥24 hours earlier evacuation lead-time vs prototype baseline.
4. ≥30 % logistics efficiency uplift vs prototype baseline.
5. ≥30 % reduction in modelled economic loss vs prototype baseline.

**Capstone-criticality flag (constitution v1.2.0, AMA portfolio convention)**: This spec MUST be tagged in `specs/shared/capstone-metric-trace.md` as **non-capstone-critical-path / delivery-hygiene** in the same sense as spec 037 FR-020. It produces evidence that the *measurement harness* works against the prototype; it does **not** itself contribute a capstone-criterion metric value. Consequently it MUST be excluded from capstone-metric attribution roll-ups.

**Relationship to adjacent specs (no duplication)**:

- Spec 015 (Performance Benchmarks) — owns the five capstone SCs themselves; this spec consumes them, does not redefine them.
- Spec 028 (Capstone Alignment) — owns the cross-portfolio metric trace; this spec registers itself there but adds no new capstone metric.
- Spec 030 (LLM Eval Framework) — owns model-quality evaluation; this spec consumes its eval outputs as one signal class but does not re-implement them.
- Spec 026 (Sim Warp Playback) and spec 024 (Simulation Control Chat) — own scenario replay and operator interaction; this spec REUSES them for harness scenario runs.
- Spec 021 (Governance Dashboard) and spec 023 (Dashboard Real Data) — own the operator/governance UI shell; this spec REUSES the shell and adds a measurement-evidence view, with no new chart libraries or UI primitives.
- Spec 035 (Webapp Capstone Closure) and spec 037 (Capstone Evidence Pack) — own the evidence-pack delivery; this spec contributes its harness outputs to that pack rather than building a parallel pack.
- Specs 008–012 (agents), spec 036 (Foundry-RAG client), spec 036-sim-agent-extend (telemetry-injection agent) — produce the signals this harness consumes via the instrumentation contract defined here.

## Clarifications

### Session 2026-05-11

Resolved by referencing constitution v1.2.0, prior specs (015, 028, 030, 035, 037), and AIDR corpus (M&E Framework for Disaster Recovery v2, Outcomes Activities & Indicators 2020, Public Information & Warnings 2021). No questions paused for user input — answers selected per the priority sources of truth named in the clarification request.

- Q: FR-016 / SC-004 reference a "documented determinism tolerance" but never state a numeric bound. What is the tolerance? → A: **±2 % relative deviation OR ±1 absolute unit (whichever is greater) per per-KPI delta, evaluated across repeated same-seed runs; SC-004's "≥95 % of repetitions" applies to this bound.** Rationale: aligns with spec 015 SC-CAP-015-002/004 percentage-delta KPI grain (whole-number percent units) and is tight enough that any genuine non-determinism (e.g., async race in the simulation engine reused per FR-013) trips the divergence flag rather than averaging — satisfies constitution v1.2.0 "graceful degradation" + audit-traceability without over-constraining the prototype harness. Applied to: FR-016.
- Q: FR-009 / FR-010 require a confidence band on every KPI value but do not name the statistical method. Which method? → A: **Bootstrap 95 % confidence interval (P2.5–P97.5) over ≥1,000 resamples of the per-scenario event log; if resamples available < 1,000 the harness MUST fall back to ±1 standard deviation and label the value "small-sample".** Rationale: AIDR M&E Framework for Disaster Recovery v2 prescribes non-parametric bootstrap for outcome indicators where the underlying distribution is unknown (the case for all five capstone KPIs); ±1 SD fallback preserves a labelled answer in degraded-mode runs (FR-027 / FR-032) rather than failing. Applied to: FR-010.
- Q: FR-004 mandates a risk-adjusted variant per indicator using "likelihood × consequence" weighting but does not pin the matrix scale. What scale? → A: **5 × 5 matrix (likelihood 1–5 × consequence 1–5) per AS/NZS ISO 31000 + AIDR Emergency Planning 2020 risk-matrix convention; the risk-adjusted indicator value = unadjusted value × (likelihood × consequence) / 25, normalised to keep units identical to the unadjusted variant.** Rationale: matches the risk-manager-persona convention named in the clarification request and the matrix used by every Australian state hazard register cited in AIDR Emergency Planning 2020. Applied to: FR-004.
- Q: FR-007 requires a plain-language definition of "modelled lives saved" but the counterfactual computation is not specified. What is the canonical definition? → A: **Modelled lives saved = (modelled fatalities in baseline run) − (modelled fatalities in AMA-assisted run), summed per canonical scenario, then scaled to one year of equivalent operational tempo using the same Sendai-aligned scaling spec 015 SC-CAP-015-001 applies to economic loss; counts are scenario-counterfactual constructs only and carry the spec-015 disclaimer.** Rationale: spec 015 SC-CAP-015-001 already pins the ≥1,000 lives-saved-per-year denominator and cites Sendai indicator A-1 (mortality); reusing that scaling avoids redefinition (FR-013 reuse principle) and keeps the lives-saved KPI numerically commensurable with the economic-loss KPI in the same scorecard. Applied to: FR-007.
- Q: FR-025 mandates an append-only audit log but does not state a retention period. How long must records be retained? → A: **Minimum 7 years from record creation, persisted in an AU region (constitution v1.2.0 AU data sovereignty — Foundry carve-out does NOT apply because audit records are KPI-derived and never leave AU per FR-029); records older than 7 years MAY be archived to cold storage but MUST remain retrievable for auditor sign-off (per spec 037 FR-037 named-auditor precedent).** Rationale: AIDR Incident Management Handbook 2023 §6 (records management) recommends life-of-program retention for incident records; 7 years aligns with Australian Public Service / state emergency-services minimum record-keeping schedules and is the same horizon spec 037 implicitly assumes for capstone evidence. Applied to: FR-025.

#### Round 2 (deferred + residual ambiguities)

- Q: US7 / Pillar A leaves the multilingual-coverage indicator's minimum language list unspecified (Round 1 deferred). What is the canonical minimum language set for the Public Information KPI render? → A: **English (rendered at plain-language Grade-8 reading level per AIDR Public Information & Warnings Handbook 2021 §2.2.4 "Clear language") PLUS the five top non-English community languages from ABS 2021 Census (Mandarin, Arabic, Vietnamese, Cantonese, Punjabi) PLUS Auslan (per AIDR PI&W 2021 accessibility guidance citing AUSLAN interpreters as non-optional) PLUS at least one jurisdiction-appropriate Aboriginal or Torres Strait Islander language drawn from the existing `apps/web/src/lib/i18n/language-packs.ts` catalogue (Kimberley/Pilbara languages, palawa kani, Yolŋu Matha, Pitjantjatjara, or Warlpiri — selected per scenario jurisdiction). Minimum total = 8 language channels per canonical scenario. Rendered views MUST meet WCAG 2.2 AA.** Rationale: AIDR PI&W 2021 §3 explicitly names Aboriginal & Torres Strait Islander communities and CALD audiences as required coverage; AWS Companion 2022 reinforces "English + key community languages"; ABS 2021 Census fixes the top-5 community-spoken non-English languages; the existing `language-packs.ts` already implements this exact catalogue, so the harness REUSES (FR-013 reuse principle, FR-034 no-new-primitives) instead of introducing new language assets. Applied to: US7, FR-002 (added multilingual-coverage indicator definition), and a new FR-037 (see Requirements).
- Q: FR-002 lists 8 attributes but Acceptance Scenario US1 and SC-001 require "all nine attributes" (the ninth being confidence-band rule). Which is canonical? → A: **Nine attributes is canonical: formula, unit, owner role, refresh cadence, target value, alert threshold, baseline source, provenance (auto vs manual), AND confidence-band rule (per FR-009/FR-010 default = bootstrap 95 % CI, P2.5–P97.5, ≥1,000 resamples).** Rationale: SC-001 and US1 Independent Test both pin nine; FR-009 makes the confidence-band rule mandatory per indicator; FR-002 is the omission. Applied to: FR-002 (corrected to nine attributes).
- Q: FR-008 says the Measurement Method MUST state "the rule for handling missing timestamps" but never gives the rule. What is the canonical missing-timestamp rule? → A: **Forward-impute the missing timestamp from the next-available adjacent event in the canonical chain (call → dispatch → arrival → control → clear), tag the affected row "missing-timestamp" + "reduced-fidelity" (per FR-027), and EXCLUDE imputed rows from the bootstrap CI computation (FR-010); if more than 10 % of rows in a per-scenario event log are imputed, the harness MUST label the entire scenario value "small-sample" and require named-auditor sign-off before the value is published (spec 037 FR-037 precedent).** Rationale: AIDR Monitoring & Evaluation Framework for Disaster Recovery v2 prescribes labelled imputation over deletion for missing outcome-indicator timestamps; the 10 % threshold mirrors the bootstrap small-sample fallback in Round 1 Q2; excluding imputed rows from the CI prevents fabricated narrowing of the band. Applied to: FR-008.
- Q: FR-024 mandates every emitted signal carry a "confidence score" but does not specify the numeric scale or banding. What scale? → A: **Float in [0.00, 1.00] with two-decimal precision; banding: ≥0.80 = "high", 0.50–0.79 = "medium", <0.50 = "low" (low-confidence signals MUST NOT contribute to a published KPI value unless flagged advisory-only per FR-030 and labelled reduced-fidelity per FR-027).** Rationale: matches the spec 030 LLM eval framework convention for model-output confidence scores (consumed by FR-036 as a signal class); the 0.80/0.50 cutoffs align with AIDR M&E Framework v2 outcome-indicator confidence categories and prevent silent inclusion of low-confidence signals in life-safety rollups (constitution v1.2.0 primacy of life). Applied to: FR-024.

#### Cycle 2 — Round 1

Scope: ambiguities discovered during the post-implementation amendment review (AMD-01..AMD-13 → FR-038..FR-050, SC-014..SC-022). Pre-amendment FR-001..FR-037 / SC-001..SC-013 were settled in R1+R2 above and are NOT re-clarified here. Answers selected per: constitution v1.2.0, AIDR corpus, prior specs (015, 028, 030, 035, 037, 026, 024, 008–012, 036), and the R1+R2 clarifications already on this spec. No user input paused for; decision rules in the clarification request applied verbatim.

Items already pinned by the amendment text and therefore NOT re-asked: FR-038 (2,555 days `Locked` at deploy), FR-042 (production fail-fast on missing AU credentials), FR-043 (Bicep reads bound resource `location` and asserts AU), FR-044 (audit row written durably before HTTP refusal; 503 + ProblemDetails on audit failure), FR-047 (`extra="forbid"` + 422), FR-048 (`language_fallback_used` + visible badge), FR-049 (≥32 jurisdictional rows + cross-sector rows; manual provenance when no citation), FR-050 (no stub tabs).

- Q: FR-045 distinguishes "any store unavailable → 503" from "non-critical stores degraded → 200 + degraded:true" but never enumerates which backing stores are critical vs non-critical. Which is which? → A: **Critical (failure → 503): every Cosmos container in the evidence database (`kpi_ladder`, `indicator_definition`, `measurement_method`, `scenario_run`, `delta_scorecard`, `causal_chain`, `benchmark`, `signal`, `evidence_audit`), the Blob immutable cold-archive container, and the Cosmos change-feed → Blob mirror processor (FR-040). Non-critical (failure → 200 + `degraded: true`): Application Insights ingestion endpoint and any read-only reporting/cache layer.** Rationale: the critical set sits on the FR-025 / FR-029 / FR-040 AU-sovereignty + append-only audit-invariant path, where the decision rule "production fail-fast preferred over silent degradation when AU-sovereignty / append-only invariants are at risk" applies; App Insights is observability-only and graceful degradation is the codified posture per FR-032 and constitution v1.2.0. Applied to: FR-045.
- Q: FR-040 says append-only mutations "MUST be rejected at the persistence boundary … and a contract test MUST verify rejection at HTTP layer" but does not name the HTTP status code SC-016 will assert. Which code? → A: **`409 Conflict` for both PATCH and DELETE against any existing `evidence_audit` document, with a `ProblemDetails` body whose `type` URI references FR-040 and `title` is `"audit-record-immutable"`. Each rejection MUST also append a tampering-attempt row to `evidence_audit` (per SC-016).** Rationale: RFC 9110 §15.5.10 defines 409 as "request could not be completed due to a conflict with the current state of the target resource" — exactly the semantics of attempting to mutate a record under a Locked Blob immutability policy (FR-038); a single status code keeps SC-016's contract test deterministic; ProblemDetails is the AMA portfolio convention for structured 4xx (spec 037 FR-037 precedent) and lets the auditor walk straight from the response back to FR-040. Applied to: FR-040.
- Q: FR-039 only names the cyclone, bushfire, and flood canonical scenarios for Auslan media + transcript coverage. What is the rule for the remaining four canonical scenarios (urban-fire, mass-casualty, hazmat, marine SAR)? → A: **Auslan media + transcript assets for those four scenarios are deferred-permitted in this cycle, but the rendered Public Information tab MUST display a visible `auslan-asset-missing` badge per FR-048 (silent omission is not permitted) AND each affected row MUST be tagged `provenance: manual` so it counts toward the FR-028 / SC-010 manual-cap arithmetic until the asset is supplied. The 8 text language channels from FR-037 remain mandatory for every canonical scenario.** Rationale: FR-037 already pins 8-channel text coverage per scenario; FR-039 elevates the three highest-frequency Australian hazard scenarios (matching AFAC / BoM warning-volume profiles cited in spec 015 SC-CAP-015-001) to also include Auslan media, while the no-silent-degradation decision rule + FR-048 surface the gap on the remaining four; tagging defaulted gaps `manual` keeps the FR-028 ≤50 % cap honest and prevents the harness from quietly publishing a partial render. Applied to: FR-039.
- Q: FR-041 mandates a default `(L=3, C=3)` neutral 5×5 weighting tagged `provenance: manual` + `auditor_signoff_required: true` when no risk-register row exists, but does not state whether those defaulted rows count toward the FR-028 / SC-010 ≤50 % per-artefact manual cap. Do they? → A: **Yes — defaulted-neutral `(3,3)` rows are `provenance: manual` per FR-041 itself and therefore count toward the FR-028 / SC-010 ≤50 % per-artefact manual cap. If the share of `provenance: manual` rows in the seeded KPI ladder exceeds 50 %, publication MUST be blocked until either (a) those rows are replaced by spec 037 risk-register-sourced weights, OR (b) a named auditor signs off per spec 037 FR-037 precedent.** Rationale: the decision-rule "Manual-row ≤50 % per artefact (>50 % → named-auditor sign-off)" is invariant across the spec; counting defaulted rows as manual (rather than treating them as system-generated) is the only interpretation that prevents the harness from publishing a ladder whose risk-adjusted variants are predominantly placeholder weights — directly matches R1-Q3 (5×5 matrix as authoritative) and the SC-010 publication-block contract. Applied to: FR-041.
- Q: FR-046 specifies "burn-rate alerts at 2 %/h and 5 %/h windows" and SLO targets but does not state the burn-rate evaluation window length, the SLO horizon, or how the action group is supplied. What are they? → A: **SLO horizon = rolling 30 days. Burn-rate evaluation window = rolling 1 hour for both 2 %/h and 5 %/h alerts (Google SRE Workbook Ch 5 fast-burn convention against a 30-day budget). Action group: the Bicep module MUST accept a required parameter `sloAlertActionGroupId` referencing the existing AMA SRE action group (e.g. `ag-ama-prod-sre`); deployment MUST fail when this parameter is empty in any non-test environment.** Rationale: 30-day horizon is the AMA portfolio default for availability SLOs (spec 035 / spec 037 evidence-pack convention) and matches the 99.5 % availability target's monthly-budget framing; 1-hour window is the standard fast-burn evaluation that yields actionable response time without false-positive noise; reusing an existing portfolio action group honours FR-034 (no new primitives) while the required-parameter + fail-fast posture mirrors FR-042 / FR-043 / SC-019 deployment-time enforcement and keeps SC-021's `what-if` assertion deterministic. Applied to: FR-046.

#### Cycle 2 — Round 2

Scope: residual task-level ambiguities discovered after Cycle 2 — Round 1 against FR-038..FR-050 / SC-014..SC-022 / AMD-01..AMD-13. Three material items remained; the rest of the amendment block is pinned by the amendment text itself or by Cycle 2 — Round 1 above. Decision rules (constitution v1.2.0; AIDR corpus; prior specs 015/028/030/035/037/036/036-sim-agent-extend/008–012/024/026; existing R1+R2+Cycle-2-R1 clarifications) applied verbatim — no user input paused for.

- Q: FR-047 / SC-022(a) require the TS twin under `packages/domain/src/evidence/` to set `model_config = ConfigDict(extra="forbid")` and contract tests to assert 422 rejection, but the existing TS twin (`packages/domain/src/evidence/index.ts`) is plain TypeScript `type` / `interface` declarations with no runtime validator (no Zod, no class-validator) — matching the codebase convention used by `packages/domain/src/app-role.ts` (closed-set string union + `is*` type-guard, no runtime schema). What is the canonical TS-side enforcement? → A: **No TS-side runtime `extra=forbid` is required (and none is permitted to be added) because the TS twin is type-only per the existing `packages/domain/src/` convention (`app-role.ts:7-30`, `evidence/index.ts:1-30`). The FR-047 / SC-022(a) `extra=forbid` + 422 invariant is enforced exclusively at the FastAPI request boundary by the Pydantic v2 models in `apps/api/app/services/evidence/models/*.py`. Schema parity between the TS twin and the Pydantic models MUST be asserted by an OpenAPI-driven contract test against `specs/038-success-criteria/contracts/openapi.evidence-harness.yaml` (the parity contract is already declared in `packages/domain/src/evidence/index.ts:5` — "Schema parity is asserted by the contract tests against ... openapi.evidence-harness.yaml"). The TS twin MUST NOT introduce a new validator dependency (Zod or class-validator) — doing so would violate FR-034 ("no new chart libraries or UI primitives" — extended by precedent to no new domain-validation primitives where a portfolio convention already exists).** Rationale: the AMA TS-domain convention is type-only twins paired with OpenAPI contract tests (see `app-role.ts` precedent and the explicit parity comment in the existing evidence twin); enforcing `extra=forbid` at the API boundary already covers every wire-protocol entry point because the TS twin is consumed only by the Next.js client AFTER the FastAPI 422 has been raised; introducing Zod would duplicate validation, drift from the Python source of truth, and add a runtime dependency the rest of the portfolio does not use. Applied to: FR-047, SC-022(a).
- Q: FR-044 mandates the AU-region refusal-audit row "MUST be written **durably before** the HTTP refusal is returned" but never names the Cosmos consistency level or write-acknowledgement semantics; the AMA portfolio default for evidence Cosmos accounts is `Session` (per `infra/bicep/modules/eval/eval-platform.bicep:95` `defaultConsistencyLevel: 'Session'`), under which "write success" does not guarantee a quorum has acknowledged. What semantics must FR-044 use? → A: **The Cosmos client used by the AU-region refusal path (and only that path) MUST issue writes against the `evidence_audit` container at `Strong` consistency, requested per-operation via the SDK consistency override (`consistency_level=Strong` on the `create_item` call) — the account-level `defaultConsistencyLevel` MAY remain `Session` for all other containers (per the existing `eval-platform.bicep` portfolio default, FR-034 reuse). The FastAPI handler MUST `await` the write completion (HTTP 201 from Cosmos) before returning the AU-region refusal HTTP response. If the Cosmos write returns a transient error (HTTP 5xx or 429), the SDK MUST retry up to 3 attempts with exponential backoff (250 ms / 1 s / 4 s); if all retries fail, the handler MUST return `503 Service Unavailable` with a `ProblemDetails` body referencing FR-044 (NOT a swallowed exception followed by a 4xx refusal — already pinned by FR-044). The `evidence-harness.bicep` module MUST deploy the audit Cosmos account in a single AU region (`australiaeast`) — Strong consistency is permitted only because there is no cross-region replication on this account (FR-029 + FR-043).** Rationale: under `Session` consistency a write that returns success to the SDK is not guaranteed durable on a quorum, which would let an AU-refusal HTTP response race ahead of the audit row and break the FR-040 + FR-025 append-only invariant; `Strong` in a single AU region is the only level that pairs durability-on-write with FR-029 AU-sovereignty (multi-region Strong is forbidden by Cosmos so the "single AU region" constraint is mutually reinforcing); per-operation override (rather than account-level Strong) honours FR-034 reuse of the existing eval Cosmos account convention without forcing `Strong` on non-audit reads/writes; 3-retry exponential backoff matches the AMA portfolio Cosmos retry posture and bounds caller wait time below the FR-046 freshness SLO of 60 s. Applied to: FR-044, SC-020(a).
- Q: FR-046 requires "burn-rate alerts at 2 %/h and 5 %/h burn rates" routed to `sloAlertActionGroupId` (Cycle 2 — Round 1) but never assigns Azure Monitor `severity` to the two alert resources; severity drives whether the action group pages a human (Sev0/Sev1) or creates a ticket (Sev2/Sev3) and SC-021's `what-if` assertion needs a deterministic value. What severities? → A: **5 %/h fast-burn alert MUST set `severity: 1` (paging — fast budget consumption against a 30-day horizon is a near-term outage signal). 2 %/h slow-burn alert MUST set `severity: 2` (ticketing — sustained mid-rate burn warrants investigation but not paging). `severity: 0` MUST NOT be used (reserved for total-outage signals per `infra/bicep/modules/observability-alerts.bicep:164` precedent — out of scope for FR-046). Both alerts route to `sloAlertActionGroupId` per Cycle 2 — Round 1; the action group itself decides notification channels per severity. SC-021's `az deployment group what-if` assertion MUST verify both severities are present in the to-be-created resource set.** Rationale: matches the AMA portfolio severity convention — Sev1 for fast-burn / paging-required SLO alerts (`infra/bicep/monitoring.bicep:86`, `infra/bicep/modules/foundry-rag-cutover-alerts.bicep:58,97`, `infra/bicep/modules/maf-tool-alerts.bicep:29`, `infra/modules/monitoring.bicep:81`) and Sev2 for slow-burn / ticket-only budget consumption alerts (`infra/bicep/modules/observability-alerts.bicep:51,79,107`, `infra/modules/monitoring.bicep:112,145`); aligns with Google SRE Workbook Ch 5 fast-burn-vs-slow-burn paging guidance the burn rates themselves were drawn from in Cycle 2 — Round 1; reserving Sev0 for total-outage preserves the action group's noise budget. Applied to: FR-046, SC-021.



### User Story 1 - Risk Manager builds a risk-adjusted KPI ladder (Priority: P1)

A Risk Manager opens the harness, selects each of the five capstone success criteria, and assembles a versioned KPI ladder mapping each criterion to at least one leading and at least one lagging indicator. For every indicator the Risk Manager records the formula, unit, owner role, refresh cadence, target value, alert threshold, baseline source, and provenance (auto vs manual). For each indicator the Risk Manager produces both a risk-adjusted variant (likelihood × consequence weighting) and an unadjusted variant, and decomposes the indicators across AIIMS functions (Control, Intelligence, Planning, Operations, Logistics, Public Information) and incident levels (1, 2, 3).

**Why this priority**: Without a documented KPI ladder no other measurement activity is meaningful — every downstream pillar references it. It is the foundational artefact a reviewer asks for first.

**Independent Test**: Can be fully tested by having a reviewer open the published KPI ladder, pick any one of the five capstone criteria at random, and verify that ≥1 leading + ≥1 lagging indicator exist with all nine attributes populated, both risk-adjusted and unadjusted variants, AIIMS-function decomposition, and incident-level decomposition.

**Acceptance Scenarios**:

1. **Given** the harness is open and the KPI ladder is at version `v1`, **When** the Risk Manager selects capstone criterion "≥50 % response-time reduction", **Then** the ladder shows ≥1 leading indicator (e.g., dispatch-decision latency) and ≥1 lagging indicator (e.g., end-to-end call-to-clear duration), each with formula, unit, owner role, cadence, target, threshold, baseline, provenance, risk-adjusted twin, AIIMS-function tag, and incident-level tag.
2. **Given** the KPI ladder is published, **When** any indicator definition changes, **Then** the ladder version increments and the prior version remains retrievable for audit.
3. **Given** an indicator's provenance is "manual", **When** the manual share for that artefact exceeds 50 %, **Then** the harness blocks publication until a named auditor signs off (per spec 037 FR-037 precedent).

---

### User Story 2 - Executive Leader reads a single Measurement Method document (Priority: P1)

An Executive Leader opens a single Measurement Method document and finds, for each of the five capstone criteria, an unambiguous definition of "what counts" in the prototype: what counts as a modelled life saved, what counts as response time (which timestamps mark the start and end), what counts as evacuation lead time, what counts as logistics efficiency, and what counts as modelled economic loss avoided. The document also names the calibration method and the confidence band each KPI value carries.

**Why this priority**: Executive readers cannot accept claims against the criteria unless the definitions are pinned down. This is the second-most-asked-for artefact.

**Independent Test**: Can be fully tested by an executive reading the document end-to-end and confirming that for each capstone criterion the definition, the start/end signals, the unit, the calibration method, and the confidence-band rule are stated in plain language without referring to any other document.

**Acceptance Scenarios**:

1. **Given** the Measurement Method document is published, **When** the Executive Leader searches for "response time", **Then** they find a single canonical definition naming the start signal (call received) and end signal (incident controlled) plus the rule for handling missing timestamps.
2. **Given** a KPI value is reported, **When** the Executive Leader inspects it, **Then** a confidence band and calibration-method reference are attached.

---

### User Story 3 - Resilience Planner runs a canonical scenario replay (Priority: P1)

A Resilience Planner picks one of the canonical scenarios (bushfire, flood, cyclone, urban-fire, mass-casualty, hazmat, marine SAR), runs it twice — once as **baseline (no AMA)** and once as **AMA-assisted** — and reads a per-KPI delta scorecard for the five capstone criteria. The replay reuses the existing simulation capability (specs 007, 024, 026) with deterministic seed control and is compatible with warp playback so an auditor can step through the same run later.

**Why this priority**: This is the headline demonstration — without a replayable baseline-vs-AMA delta scorecard there is no evidence of measurability beyond paper definitions.

**Independent Test**: Can be fully tested by selecting one canonical scenario, running both modes with the same seed, and verifying that the scorecard reports a per-KPI delta with confidence bands and that a second run with the same seed reproduces the deltas within the stated tolerance.

**Acceptance Scenarios**:

1. **Given** the bushfire canonical scenario and seed `S1`, **When** the Planner runs baseline then AMA-assisted, **Then** the scorecard shows for each capstone KPI: baseline value, AMA-assisted value, absolute delta, percent delta, confidence band, and a "meets target?" flag.
2. **Given** the same scenario and seed, **When** the run is repeated, **Then** the deltas reproduce within the harness's documented determinism tolerance.
3. **Given** any single signal source is unavailable, **When** the scenario runs in degraded mode, **Then** the scorecard still reports values for every KPI with reduced-fidelity flags rather than failing.

---

### User Story 4 - Observer-Auditor traces any KPI value back to source signals and human approvals (Priority: P1)

An Observer-Auditor selects any reported KPI value in the scorecard and follows a single audit trail from the value back through: the formula version, the input signals with timestamps and provenance, the model/recommendation that generated each signal, the human decision that approved or rejected the recommendation, and the resulting modelled outcome. The audit trail is append-only and survives degraded-mode runs.

**Why this priority**: Without end-to-end traceability the harness cannot satisfy the audit/governance requirement and the evidence claim collapses.

**Independent Test**: Can be fully tested by an auditor picking any one KPI value at random and walking the full chain (signal → model → recommendation → human decision → outcome) without leaving the audit view, and verifying append-only history.

**Acceptance Scenarios**:

1. **Given** a published KPI value, **When** the auditor opens its trace, **Then** every contributing signal lists provenance, confidence score, and the recommendation it fed plus the human decision applied to that recommendation.
2. **Given** a prior KPI value, **When** any contributing record is amended, **Then** the original record is preserved and the amendment is recorded as a new append-only entry.

---

### User Story 5 - Solution Architect / Principal Engineer reviews Expected Impact reasoning (Priority: P2)

A Solution Architect or Principal Engineer reviews the Expected Impact document and, for each AMA capability (each of the agents in specs 008–012, the Foundry-RAG client from spec 036, and the simulation telemetry-injection agent from spec 036-sim-agent-extend), validates the causal chain: capability → KPI(s) it should move → expected magnitude → assumptions that must hold → threats to validity. Each chain is traceable back to the originating spec.

**Why this priority**: This is essential for engineering-leadership sign-off but is downstream of the ladder, the method, and the replay (the P1s). It is gated by them rather than gating them.

**Independent Test**: Can be fully tested by an engineer picking any one capability and confirming that its causal chain names ≥1 KPI moved, an expected magnitude with units, ≥1 assumption, ≥1 threat to validity, and a citation back to the originating spec.

**Acceptance Scenarios**:

1. **Given** the Expected Impact document is published, **When** the engineer opens the chain for the Resource Allocation Agent (spec 011), **Then** the chain names the logistics-efficiency KPI(s) it moves, the expected magnitude, the assumptions, the threats to validity, and a back-link to spec 011.
2. **Given** any chain has an unresolved assumption, **When** the chain is read, **Then** the assumption is visibly flagged as unresolved.

---

### User Story 6 - Sector-specific KPI render for a chosen jurisdiction (Priority: P3)

A sector reader (e.g., NSW Ambulance) picks their jurisdiction and reads a render of the response-time KPI calibrated to the recognised local benchmark — for example, NSW Ambulance Priority-1 response-time targets vs the prototype delta from the canonical mass-casualty scenario.

**Why this priority**: Useful for sector buy-in but not on the critical path for the harness itself.

**Independent Test**: Can be fully tested by selecting a jurisdiction, reading the sector view, and confirming both the named external benchmark and the prototype-baseline comparison are present and labelled distinctly.

**Acceptance Scenarios**:

1. **Given** the jurisdiction "NSW Ambulance" and the mass-casualty scenario, **When** the sector view loads, **Then** it shows the NSW Pri-1 benchmark, the prototype baseline, and the AMA-assisted value, each labelled distinctly.

---

### User Story 7 - Public Information Officer KPI render (Priority: P3)

A Public Information Officer reads a KPI render covering alert reach, behavioural-impact proxy, and multilingual coverage (including CALD and remote-community proxies), so the public-information function is represented in the ladder rather than being an afterthought.

**Why this priority**: Communications is consistently under-instrumented; including it raises evidence completeness but is not blocking.

**Independent Test**: Can be fully tested by opening the Public Information view and confirming reach, behavioural-impact proxy, and multilingual-coverage indicators all have formula, unit, baseline, and provenance fields populated.

**Acceptance Scenarios**:

1. **Given** the Public Information view, **When** the PIO opens it for the cyclone canonical scenario, **Then** alert-reach, behavioural-impact-proxy, and multilingual-coverage indicators are each rendered with formula, unit, baseline, and provenance, and the multilingual-coverage indicator shows ≥8 language channels per FR-037 (English plain-language + Mandarin + Arabic + Vietnamese + Cantonese + Punjabi + Auslan + ≥1 jurisdiction-appropriate First-Nations language) with WCAG 2.2 AA compliance.

---

### Edge Cases

- A canonical scenario emits no events for a given function (e.g., Logistics) — the harness MUST still render that function's KPIs as "no signal" with a reduced-fidelity flag rather than omitting them.
- A required external benchmark is unavailable for a jurisdiction — the harness MUST surface the prototype-baseline comparison and label the external benchmark as "not available".
- A KPI's provenance flips from auto to manual mid-run (e.g., a feed drops) — the harness MUST tag the affected rows manual and apply the per-artefact ≤50 % manual cap rule.
- Two replays of the same seed diverge beyond the documented determinism tolerance — the harness MUST flag the divergence rather than silently averaging.
- The risk-adjusted variant of a KPI is requested but no likelihood × consequence weighting exists — the harness MUST refuse to render the risk-adjusted value and prompt the Risk Manager to supply the weighting.
- A signal source is in a non-AU region — the harness MUST refuse to persist the value and record the refusal in the audit log.
- Human approval is missing for a recommendation that contributed to a KPI value — the harness MUST tag the value as "advisory only" and exclude it from any rollup that requires approved decisions.

## Requirements *(mandatory)*

### Functional Requirements

**Pillar A — KPI Model**

- **FR-001**: System MUST publish a versioned KPI ladder that maps each of the five capstone success criteria (spec 015 SC-CAP-015-001..005) to at least one leading and at least one lagging indicator.
- **FR-002**: For every indicator the ladder MUST record nine attributes: formula, unit, owner role, refresh cadence, target value, alert threshold, baseline source, provenance (auto vs manual), AND confidence-band rule (per FR-009/FR-010, default = bootstrap 95 % CI over ≥1,000 resamples).
- **FR-003**: The ladder MUST decompose indicators by AIIMS function (Control, Intelligence, Planning, Operations, Logistics, Public Information) and by incident level (1, 2, 3).
- **FR-004**: The ladder MUST publish both a risk-adjusted variant and an unadjusted variant of each indicator. The risk-adjusted variant MUST use a 5 × 5 likelihood-by-consequence matrix (likelihood 1–5 × consequence 1–5, per AS/NZS ISO 31000 and AIDR Emergency Planning 2020) with risk-adjusted value = unadjusted × (likelihood × consequence) / 25, normalised so units match the unadjusted variant.
- **FR-005**: The ladder MUST be versioned; prior versions MUST remain retrievable.
- **FR-006**: The ladder MUST rank life-safety indicators above efficiency indicators in any rollup, in line with constitution v1.2.0 "primacy of life".

**Pillar B — Measurement Framework**

- **FR-007**: System MUST publish a single Measurement Method document that defines, in plain language, what counts as: a modelled life saved, response time, evacuation lead time, logistics efficiency, modelled economic loss avoided. The "modelled life saved" definition MUST use the scenario-counterfactual formula: (modelled fatalities in baseline run) − (modelled fatalities in AMA-assisted run), summed per canonical scenario and scaled to one year of equivalent operational tempo using the spec 015 SC-CAP-015-001 Sendai-aligned scaling, with the spec-015 disclaimer attached.
- **FR-008**: The Measurement Method MUST name the start and end signals (call → dispatch → arrival → control → clear) for each timestamp-based KPI and the rule for handling missing timestamps. The missing-timestamp rule is: forward-impute from the next-available adjacent event in the canonical chain, tag the row "missing-timestamp" + "reduced-fidelity" (per FR-027), and EXCLUDE imputed rows from the bootstrap CI computation (FR-010). If >10 % of rows in a per-scenario event log are imputed, the harness MUST label the entire scenario value "small-sample" and require named-auditor sign-off before publication (spec 037 FR-037 precedent).
- **FR-009**: Every reported KPI value MUST carry a confidence band and a reference to the calibration method used.
- **FR-010**: The Measurement Method MUST specify how confidence bands are computed and how calibration is performed against the prototype baseline. The default confidence band MUST be a non-parametric bootstrap 95 % CI (P2.5–P97.5) over ≥1,000 resamples of the per-scenario event log (per AIDR M&E Framework for Disaster Recovery v2); when fewer than 1,000 resamples are available, the harness MUST fall back to ±1 standard deviation and label the value "small-sample".

**Pillar C — Simulation Logic**

- **FR-011**: System MUST provide a canonical scenario set covering at minimum: bushfire, flood, cyclone, urban-fire, mass-casualty, hazmat, marine SAR.
- **FR-012**: Each scenario MUST be runnable in two modes: baseline (no AMA) and AMA-assisted.
- **FR-013**: The harness MUST reuse existing simulation capabilities (specs 007, 024, 026) and MUST NOT introduce a new simulation engine.
- **FR-014**: Scenario runs MUST be deterministic given a seed and MUST be compatible with warp playback (spec 026) so an auditor can step through the same run later.
- **FR-015**: After a baseline + AMA-assisted run, the harness MUST output a per-KPI delta scorecard with: baseline value, AMA-assisted value, absolute delta, percent delta, confidence band, and a "meets target?" flag.
- **FR-016**: The harness MUST document a determinism tolerance and MUST flag (not hide) any divergence between repeated runs of the same seed beyond that tolerance. The tolerance is **±2 % relative deviation OR ±1 absolute unit (whichever is greater) per per-KPI delta**; SC-004's "≥95 % of repetitions" reproduction target applies against this bound.

**Pillar D — Expected Impact Reasoning**

- **FR-017**: System MUST publish an Expected Impact document containing one causal chain per AMA capability: each agent in specs 008–012, the Foundry-RAG client (spec 036), and the simulation telemetry-injection agent (spec 036-sim-agent-extend).
- **FR-018**: Each causal chain MUST name: the capability, the KPI(s) it should move, the expected magnitude with units, the assumptions that must hold, the threats to validity, and a citation back to the originating spec.
- **FR-019**: Unresolved assumptions MUST be visibly flagged in the published chain.

**Pillar E — Benchmark Comparisons**

- **FR-020**: System MUST publish a benchmark register that, for each KPI, names the recognised external Australian benchmark (including but not limited to: AFAC FDI/FFDI bands, BoM hazard warning lead-time targets, state ambulance Pri-1 response-time KPIs across NSW/VIC/QLD/SA/WA/ACT/NT/TAS, FRNSW/FRV/SAMFS structural-fire turnout standards, SES flood-rescue and sandbag throughput norms, police evacuation-clearance objectives, ICAO ARFF response targets for Airservices, SAIDI/SAIFI for utilities, AIIMS span-of-control 3–7).
- **FR-021**: The register MUST distinguish "prototype-baseline" comparison from "external-benchmark" comparison and label each value accordingly.
- **FR-022**: Where an external benchmark is unavailable for a jurisdiction, the register MUST mark it "not available" and still surface the prototype-baseline comparison.

**Pillar F — Instrumentation Design**

- **FR-023**: Every AMA component (agents in specs 008–012, Foundry-RAG client spec 036, telemetry-injection agent spec 036-sim-agent-extend) MUST emit, via documented event hooks, the signal types the KPI framework consumes.
- **FR-024**: Every emitted signal MUST carry provenance fields (source, time, actor, capability version) and a confidence score expressed as a float in [0.00, 1.00] with two-decimal precision. Banding: ≥0.80 = "high", 0.50–0.79 = "medium", <0.50 = "low". Low-confidence signals MUST NOT contribute to a published KPI value unless flagged advisory-only (FR-030) AND labelled reduced-fidelity (FR-027). Aligns with spec 030 LLM eval framework convention consumed via FR-036.
- **FR-025**: The audit log MUST be append-only; amendments MUST be recorded as new entries that preserve the original. Records MUST be retained for a minimum of 7 years from creation, persisted in an AU region (constitution v1.2.0 AU data sovereignty; Foundry carve-out does NOT apply per FR-029); records may be archived to cold storage after 7 years but MUST remain retrievable for named-auditor sign-off (spec 037 FR-037 precedent).
- **FR-026**: The instrumentation MUST provide end-to-end traceability from signal → model → recommendation → human decision → outcome for any KPI value.
- **FR-027**: Instrumentation MUST capture signals in degraded mode (offline / cached) and label the resulting KPI values reduced-fidelity.
- **FR-028**: Where automation is incomplete, manual rows MUST be tagged manual; per-artefact manual share MUST NOT exceed 50 %; >50 % MUST require named-auditor sign-off (spec 037 FR-037 precedent).

**Cross-cutting non-negotiables (constitution v1.2.0)**

- **FR-029**: All KPI values, scenario configurations, and audit data MUST be persisted in AU regions; signals from non-AU regions MUST be refused and the refusal logged.
- **FR-030**: KPI values that drive operator-visible recommendations MUST remain advisory; the harness MUST NOT trigger any autonomous operational action.
- **FR-031**: KPI exports MUST use standards-based formats compatible with CAP, EDXL, GeoJSON, and OpenAPI where applicable.
- **FR-032**: The KPI framework MUST continue to compute (with reduced fidelity flags) when any single signal source is unavailable.
- **FR-033**: This spec MUST be registered in `specs/shared/capstone-metric-trace.md` as **non-capstone-critical-path / delivery-hygiene** and MUST be excluded from capstone-metric attribution rollups (spec 028 FR-020 / spec 037 FR-020 precedent).

**Reuse / no-duplication constraints**

- **FR-034**: System MUST reuse the governance dashboard shell (specs 021, 023, 035) and MUST NOT introduce new chart libraries or UI primitives.
- **FR-035**: System MUST contribute its outputs to the capstone evidence pack (spec 037) rather than building a parallel pack.
- **FR-036**: System MUST consume LLM evaluation outputs from spec 030 as one signal class; MUST NOT re-implement model-quality evaluation.
- **FR-037**: The Public Information KPI render (US7) MUST cover at minimum eight language channels per canonical scenario: English (rendered at plain-language Grade-8 reading level per AIDR PI&W Handbook 2021 §2.2.4), the five top non-English ABS 2021 Census community languages (Mandarin, Arabic, Vietnamese, Cantonese, Punjabi), Auslan (per AIDR PI&W 2021 accessibility guidance), and at least one jurisdiction-appropriate Aboriginal or Torres Strait Islander language drawn from the existing `apps/web/src/lib/i18n/language-packs.ts` catalogue (Kimberley/Pilbara, palawa kani, Yolŋu Matha, Pitjantjatjara, or Warlpiri). All rendered evidence views MUST meet WCAG 2.2 AA. The harness MUST REUSE the existing language-packs catalogue and MUST NOT introduce new language assets (per FR-013, FR-034).

### Key Entities

- **KPI Ladder**: Versioned mapping from each capstone success criterion to its leading + lagging indicators, decomposed by AIIMS function and incident level, with risk-adjusted and unadjusted variants.
- **Indicator Definition**: A single KPI with formula, unit, owner role, refresh cadence, target, alert threshold, baseline source, provenance, and confidence-band rule.
- **Measurement Method**: Plain-language definitions of what each capstone metric counts and how it is computed from event-log timestamps and counts.
- **Canonical Scenario**: A named, seedable scenario (bushfire, flood, cyclone, urban-fire, mass-casualty, hazmat, marine SAR) runnable in baseline and AMA-assisted modes.
- **Delta Scorecard**: Per-KPI baseline value, AMA-assisted value, deltas, confidence band, and target-met flag for a single scenario run pair.
- **Causal Chain**: Capability → KPI(s) moved → expected magnitude → assumptions → threats to validity → originating-spec citation.
- **Benchmark Register**: Per-KPI list of recognised external Australian benchmarks plus prototype-baseline reference, distinctly labelled.
- **Signal**: Instrumentation event carrying provenance, confidence score, source, time, actor, and capability version.
- **Audit Trail**: Append-only chain from signal → model → recommendation → human decision → outcome for any KPI value.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For each of the five capstone success criteria, the published KPI ladder contains at least one leading and at least one lagging indicator with all nine attributes (formula, unit, owner, cadence, target, threshold, baseline, provenance, confidence-band rule) populated — verifiable by inspection of the ladder.
- **SC-002**: A reviewer can locate the canonical definition of each capstone metric in the Measurement Method document in under two minutes without consulting another document.
- **SC-003**: For each of the seven canonical scenarios a baseline + AMA-assisted run pair produces a per-KPI delta scorecard for all five capstone KPIs.
- **SC-004**: Repeated runs of the same scenario and seed reproduce the per-KPI deltas within the harness's documented determinism tolerance in at least 95 % of repetitions.
- **SC-005**: An auditor can trace any published KPI value back to its source signals, model output, recommendation, human decision, and outcome within a single audit view, in under three minutes.
- **SC-006**: 100 % of AMA capabilities (agents in specs 008–012, Foundry-RAG client spec 036, telemetry-injection agent spec 036-sim-agent-extend) have a published causal chain with named KPI(s) moved, expected magnitude, assumptions, threats to validity, and originating-spec citation.
- **SC-007**: For every KPI in the ladder, the benchmark register names either a recognised external Australian benchmark or an explicit "not available" with a prototype-baseline value present.
- **SC-008**: When any single signal source is removed, the harness still produces values for 100 % of KPIs, each correctly labelled reduced-fidelity.
- **SC-009**: 100 % of KPI values, scenario configurations, and audit records are persisted in AU regions; non-AU signal sources are refused and logged.
- **SC-010**: Per-artefact manual provenance share does not exceed 50 % unless a named auditor sign-off is recorded; the harness blocks publication otherwise.
- **SC-011**: This spec is listed in `specs/shared/capstone-metric-trace.md` under the spec-criticality table as **non-capstone-critical-path / delivery-hygiene** and is excluded from capstone-metric attribution rollups.
- **SC-012**: Zero net-new chart libraries or UI primitives are introduced; all rendering reuses the governance shell delivered by specs 021, 023, and 035 — verifiable by dependency inspection.
- **SC-013**: The Public Information KPI render covers ≥8 language channels per canonical scenario (English plain-language Grade-8 + Mandarin + Arabic + Vietnamese + Cantonese + Punjabi + Auslan + ≥1 jurisdiction-appropriate First-Nations language drawn from `apps/web/src/lib/i18n/language-packs.ts`) and rendered views pass automated WCAG 2.2 AA conformance checks — verifiable by inspection of FR-037 against the rendered view and an automated accessibility scan.

## Assumptions

- The five capstone success criteria are owned by spec 015 and are stable for the duration of this harness; this spec does not redefine them.
- The simulation engine, warp playback, and operator chat (specs 007, 024, 026) are available and stable enough to host deterministic, seed-controlled replay.
- The governance dashboard shell (specs 021, 023, 035) exposes extension points sufficient to host the Measurement Evidence view without new chart libraries.
- LLM evaluation outputs from spec 030 are available as a consumable signal class.
- The Foundry-RAG carve-out does not affect this harness because no KPI evaluator persists data outside AU regions.
- "Modelled lives saved" and "modelled economic loss avoided" are scenario-counterfactual constructs (Sendai-aligned for economic loss, per spec 015), not claims about real-world casualties or losses.
- External Australian benchmarks (AFAC, BoM, state ambulances, FRNSW/FRV/SAMFS, SES, ICAO ARFF, SAIDI/SAIFI, AIIMS span-of-control) are referenced by their published targets and not republished by this harness.
- The "≤50 % manual share per artefact / >50 % requires named-auditor sign-off" rule is inherited from spec 037 FR-037 and applied verbatim here.

## Out of Scope (Explicit Exclusions)

- Production-grade SLA monitoring of the live AMA system (this harness is prototype evidence only).
- Net-new operational dashboards beyond the governance shell delivered by specs 035 and 037.
- Net-new chart libraries or UI primitives.
- Real customer or patient PII of any kind.
- Demo scripting (owned by spec 016) and FinOps cost dashboards (per spec 037 exclusion precedent).
- Any autonomous operational action; KPI values are advisory only (constitution v1.2.0 human-in-the-loop).
- Re-implementation of model-quality evaluation (owned by spec 030) or the simulation engine (owned by specs 007, 024, 026).
- New capstone success criteria — the five from spec 015 SC-CAP-015-001..005 are the only ones in scope.

## Amendments — Cycle 2 (Session 2026-05-11)

This block records merit-bearing review feedback from the post-implementation all-personas review (operational + 58 sectors + 17 technical = 95 personas). Each amendment encodes a new functional requirement (FR-038..FR-050), an extended success criterion (SC-014..SC-022), or both, and is wired into the existing pillars without changing scope boundaries (still non-capstone-critical-path / delivery-hygiene per spec 037 FR-020).

### Amendment Drivers (validated for merit)

| ID | Reviewer (persona) | Severity | Rationale for accepting |
|----|--------------------|----------|-------------------------|
| AMD-01 | Logistics Officer + Infra/DevOps + Compliance Auditor | Critical | "84 × 30 days" ≈ 6.9 yr falls short of the 7-yr clarification (Round 1 Q5); also unlocked default. |
| AMD-02 | Public Information Officer + Accessibility Tester | Critical | FR-037 / SC-013 require demonstrable WCAG 2.2 AA + Auslan media + Grade-8 plain language; current render is labels only. |
| AMD-03 | Observer-Auditor + Data Engineer + Security Engineer | High | Append-only enforcement is helper-code only; storage-boundary enforcement is required for FR-025 credibility. |
| AMD-04 | Risk Manager | High | FR-004 mandates a risk-adjusted variant but no 5×5 matrix is seeded, so the variant is unproducible. |
| AMD-05 | Software Developer + Security + Compliance | High | Memory-client fallback must not run in production paths (silent data-residency / append-only bypass). |
| AMD-06 | Solution Architect + Azure Principal Architect | High | Bicep `@allowed` only constrains module params, not the bound existing accounts' actual location. |
| AMD-07 | Security Engineer | High | AU-region refusal audit currently swallows write exceptions, leaving no durable trace. |
| AMD-08 | API Architect | High | `/healthz/evidence` does not actually probe the backing stores; the 503 contract is unenforceable. |
| AMD-09 | SRE Engineer | High | SLO + 2 %/h + 5 %/h burn-rate alerts are documented in tasks but not wired into Bicep. |
| AMD-10 | Software Developer | High | Codebase convention `model_config = ConfigDict(extra="forbid")` (per `RetrievedChunk` precedent) is missing on every evidence model. |
| AMD-11 | UX Designer | Medium | Language-pack fallback chain silently downgrades to English without operator-visible disclosure. |
| AMD-12 | All 10 jurisdiction reviews + Commonwealth + Cross-sector | High | Benchmark seed is generic (single AU-wide ambulance/BoM proxy); spec FR-020 demands recognised AU benchmarks per agency/sector. |
| AMD-13 | Principal Engineer | Medium | Frontend tabs are stubs; SC-001..SC-013 cannot be visually verified end-to-end without live data wiring. |

### Functional Requirements (Amended / New)

**Pillar F — Instrumentation (audit retention hardening)**

- **FR-038** (AMD-01): The audit cold-archive Blob immutability period MUST be set to **2,555 days (= 7 × 365)** with the immutability policy **state set to `Locked` at deployment time**. Operator follow-up to lock is NOT permitted. Any deployment producing an unlocked or shorter policy MUST fail.
- **FR-040** (AMD-03): The `evidence_audit` Cosmos container MUST be backed by a **Cosmos change-feed → immutable Blob mirror** activated by the same Bicep deployment. Any direct PUT/PATCH/DELETE attempt against an existing audit document MUST be rejected at the persistence boundary (server-side stored procedure or change-feed processor invariant), and a contract test MUST verify rejection at HTTP layer. The HTTP rejection status MUST be **`409 Conflict`** for both PATCH and DELETE (RFC 9110 §15.5.10 — "the request could not be completed due to a conflict with the current state of the target resource", i.e. the locked immutability policy), with a `ProblemDetails` body whose `type` URI references FR-040 and whose `title` is `"audit-record-immutable"`. Each rejection MUST also append a tampering-attempt row to `evidence_audit` (per SC-016).
- **FR-044** (AMD-07): When AU-region refusal occurs, the refusal-audit row MUST be written **durably before** the HTTP refusal is returned to the caller. If the audit write itself fails, the response MUST be `503 Service Unavailable` with a `ProblemDetails` body, NOT a swallowed exception followed by a 4xx refusal.
- **FR-045** (AMD-08): `/healthz/evidence` MUST query each required backing store (every Cosmos container plus Blob immutable archive plus Application Insights ingestion) and MUST return `503` when any **critical** store is unavailable, `200` with `degraded: true` when one or more **non-critical** stores are degraded, and `200` with `degraded: false` only when all are healthy. The hardcoded `evidence-audit-cold=True` shortcut MUST be removed. **Critical stores (failure → 503):** every Cosmos container in the evidence database (`kpi_ladder`, `indicator_definition`, `measurement_method`, `scenario_run`, `delta_scorecard`, `causal_chain`, `benchmark`, `signal`, `evidence_audit`), the Blob immutable cold-archive container, and the Cosmos change-feed → Blob mirror processor (FR-040). **Non-critical stores (failure → 200 + `degraded: true`):** Application Insights ingestion endpoint and any read-only reporting/cache layer. Rationale: critical stores sit on the FR-025 / FR-029 / FR-040 AU-sovereignty + append-only audit invariant path, where silent degradation is forbidden (production fail-fast decision rule); App Insights is observability-only and graceful degradation is acceptable per FR-032.

**Pillar A — KPI Model (risk-adjusted variant + extra="forbid")**

- **FR-041** (AMD-04): Every KPI in the seeded ladder MUST receive a 5×5 likelihood × consequence weighting (`L`, `C` ∈ 1..5; `weight = (L*C)/25`), drawn from the systematic risk register seeded by spec 037 (`docs/risk-register/`) where a matching risk row exists, otherwise defaulted to `(L=3, C=3)` "neutral, not yet assessed" with `provenance: manual` and `auditor_signoff_required: true` per spec 037 FR-037 precedent. The KPI ladder render MUST display the adjusted and unadjusted values **side-by-side**. Defaulted-neutral `(3,3)` rows **count toward the per-artefact ≤50 % manual-row cap** defined in FR-028: if the share of KPI-ladder rows whose `provenance` is `manual` (whether from defaulted weights or other manual entries) exceeds 50 % of the ladder, publication MUST be blocked until either (a) those rows are replaced by spec 037 risk-register-sourced weights, OR (b) a named auditor signs off per spec 037 FR-037 precedent. This preserves the manual-cap invariant codified in FR-028 / SC-010 and prevents publication of a ladder whose risk-adjusted variants are predominantly placeholder.
- **FR-047** (AMD-10): All Pydantic v2 models in `apps/api/app/services/evidence/models/*.py` (and the TS twin under `packages/domain/src/evidence/`) MUST set `model_config = ConfigDict(extra="forbid")`. Contract tests MUST verify rejection of unknown fields with a 422 response.

**Pillar E — Benchmark Comparisons (per-agency seed)**

- **FR-049** (AMD-12): The benchmark register seed MUST include, at minimum, **one row per state/territory primary fire agency, ambulance agency, SES, and police agency** (8 jurisdictions × ≥4 categories = ≥32 rows), plus separate rows for: BoM warning lead-time per warning class (Watch / Warning / Severe / Emergency), NEMA COMDISPLAN activation-to-deployment, ICAO ARFF response targets (Airservices Australia), SAIDI / SAIFI for utilities, AIIMS span-of-control 3–7. Each row MUST carry `source_citation` (organisation + document + year + URL). When a citation cannot be sourced from a published Australian standard, the row MUST be tagged `provenance: manual` (≤50 % per artefact per FR-028).

**Pillar B — Measurement Framework (already covered by FR-007..FR-010)** — no amendment required; the 5×5 matrix integration falls under FR-041 in Pillar A.

**Pillar C — Simulation Logic** — no amendment required; AMD-09 and AMD-13 apply at infra/UI layers.

**Pillar D — Expected Impact** — no amendment required.

**Constitution Non-Negotiables (existing FR-029..FR-033 hardening)**

- **FR-039** (AMD-02): The Public Information KPI render MUST satisfy ALL of: (a) text content rendered in all 8 language channels named in FR-037 for **every** canonical scenario; (b) plain-language readability **Flesch-Kincaid grade ≤ 8** for the English variant, asserted by an automated readability check in the Playwright suite; (c) Auslan placeholder asset (video URL OR captioned-image with sign-language description) plus full transcript provided for at least the cyclone, bushfire, and flood canonical scenarios; (d) automated `axe-core` scan on the rendered Public Information tab MUST report **zero `serious` or `critical` violations**. For the remaining four canonical scenarios (urban-fire, mass-casualty, hazmat, marine SAR) the Auslan media + transcript assets are **deferred-permitted** in this cycle, but the rendered tab MUST display a visible **`auslan-asset-missing`** badge per FR-048 (silent omission is not permitted) AND the row MUST be tagged `provenance: manual` so it counts toward the FR-028 / SC-010 manual-cap arithmetic until the asset is supplied. Any other failing variant MUST surface a clear "fallback used" or "asset missing" badge per FR-048.
- **FR-042** (AMD-05): The in-memory client registry in `apps/api/app/services/evidence/_clients.py` MUST be active **only** when the environment variable `AMA_TEST_MODE=1` (or equivalent pytest-detected sentinel) is set. In any other environment, the absence of configured Azure Cosmos / Blob / Application Insights credentials MUST cause the FastAPI app to **fail fast on startup** with a clear error referring to FR-029 (AU sovereignty) and FR-042 (production-mode requirement).
- **FR-043** (AMD-06): The `evidence-harness.bicep` module MUST, at deployment time, read the `location` of each bound existing Cosmos and Storage account (and any Application Insights / Log Analytics resource it wires) and assert that the value ∈ {`australiaeast`, `australiasoutheast`}. If any bound resource is outside AU, deployment MUST fail with a clear policy-violation message; documented `@allowed` parameters alone are NOT sufficient.
- **FR-046** (AMD-09): The Bicep module MUST deploy: (a) the Application Insights workbook for `evidence-harness-slo`, (b) availability ≥ 99.5 %, replay success ≥ 98 %, freshness ≤ 60 s SLO targets evaluated against a **rolling 30-day SLO horizon**, and (c) burn-rate alerts at **2 %/h and 5 %/h burn rates evaluated over a rolling 1-hour window** (Google SRE Workbook Ch 5 fast-burn convention; 1 h is the smallest window that yields statistically meaningful burn against a 30-day budget while still firing within an actionable response time). The Bicep module MUST accept a required parameter `sloAlertActionGroupId` (the existing AMA SRE action group, e.g. `ag-ama-prod-sre`); deployment MUST fail when this parameter is empty in any non-test environment (FR-042 production fail-fast precedent). None of these may be deferred to "operator follow-up".

**UI / UX**

- **FR-048** (AMD-11): When the language-pack lookup chain falls back from a requested language to a default, the API response MUST include `language_fallback_used: "<from_code>→<to_code>"` and the UI MUST render a visible "fallback used" badge near the affected content. Silent downgrade is not permitted.
- **FR-050** (AMD-13): Each tab in `apps/web/src/app/governance/evidence/` (KPI Ladder, Measurement Method, Replay Scorecard, Causal Chains, Benchmarks, Audit Trace, Public Information) MUST fetch live data from its corresponding `/api/v1/evidence/*` endpoint on mount and surface the `degraded`, `small-sample`, `manual`, and `reduced-fidelity` states explicitly per Round 2 Q3/Q4. Stub or placeholder content (e.g., "populated by Phase 4") is not permitted in any merged build.

### Success Criteria (Amended / New)

- **SC-014** (AMD-01): An automated check confirms the deployed audit Blob immutability policy is `state=Locked` and `immutabilityPeriodSinceCreationInDays=2555`.
- **SC-015** (AMD-02): The Public Information tab passes `axe-core` with zero `serious` / `critical` violations and the English variant scores Flesch-Kincaid ≤ 8 (asserted via Playwright).
- **SC-016** (AMD-03): A contract test confirms an HTTP `PATCH` and `DELETE` against any document in `evidence_audit` returns 4xx and is recorded as a tampering attempt audit row.
- **SC-017** (AMD-04): Every KPI in the seeded ladder has a non-null 5×5 weight; the KPI Ladder tab renders adjusted + unadjusted values side-by-side for every row.
- **SC-018** (AMD-05): A unit test verifies that constructing the FastAPI app without `AMA_TEST_MODE=1` and without Azure credentials raises a startup error referencing FR-042.
- **SC-019** (AMD-06): Bicep what-if against a deliberately mis-located bound resource fails with a clear AU-residency violation message.
- **SC-020** (AMD-07 + AMD-08): Integration tests verify (a) AU-refusal returns 503 when the audit write fails, and (b) `/healthz/evidence` returns 503 when any backing store is taken offline.
- **SC-021** (AMD-09): `az deployment group what-if` against the Bicep module shows the SLO workbook + both burn-rate alerts in the to-be-created resource set.
- **SC-022** (AMD-10 + AMD-11 + AMD-12 + AMD-13): Contract tests confirm (a) every evidence Pydantic model rejects unknown fields with 422; (b) the `language_fallback_used` field appears whenever fallback occurs; (c) the benchmark register contains ≥32 jurisdictional rows + ≥5 cross-sector rows; (d) every governance/evidence tab fetches live data on mount.

### Amendment Scope Notes

- All 13 amendments are infrastructure / instrumentation / data-seed hardening — they do NOT change the spec's capstone-criticality flag, do NOT extend any prior spec's scope, and do NOT introduce new chart libraries / UI primitives / sim engines.
- AMD-04 introduces a one-way dependency on spec 037's `docs/risk-register/` if present; if absent, the default `(L=3, C=3)` neutral weighting + manual-row tagging applies, preserving graceful degradation (FR-027/FR-032).
- AMD-12 does NOT republish external benchmark data; it stores citations only (per existing assumption #7).
- The amendments preserve the spec 037 FR-037 manual-row ≤50 % cap (>50 % requires named-auditor sign-off).

