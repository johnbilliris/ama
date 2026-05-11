# Quality Checklist (Cycle 2 amendment): Real Sub-Agent Invocation & Simulation Telemetry-Injection Agent

**Purpose**: Validate Cycle 2 amendment quality (post Step 8i synthesis) before
proceeding to Step 8o (`speckit.plan`) → Step 8p (`speckit.tasks`) → Step 8r
(`speckit.implement`).
**Created**: 2026-05-09
**Feature**: [spec.md](../spec.md) (Cycle 2 Amendment Log at lines 86–234,
Cycle 2 pass-1 clarifications at 235–423, Cycle 2 pass-2 clarifications at
425–685).
**Cycle 1 reference (locked, NOT modified by this checklist)**:

- [requirements.md](./requirements.md) — Cycle 1 Specification Quality Checklist
- [amendment-pass.md](./amendment-pass.md) — Cycle 1 master amendment traceability (CHK001–CHK100)
- [accessibility-and-cald.md](./accessibility-and-cald.md)
- [audit-and-provenance.md](./audit-and-provenance.md)
- [graceful-degradation.md](./graceful-degradation.md)
- [multi-jurisdiction.md](./multi-jurisdiction.md)
- [safety-and-life-primacy.md](./safety-and-life-primacy.md)
- [integration-and-test-coverage.md](./integration-and-test-coverage.md)

> **Cycle 1 items must remain intact.** Any Cycle 1 checklist box (passing or
> failing) is out-of-scope for this file and must continue to be reviewed in
> its companion checklist.

---

## Cycle 2 Quality Checklist (post Step 8i amendments)

This section validates the **eight** Cycle 2 amendments (A2-01 → A2-08) and
the **ten** clarification Q→A entries (pass-1 Q1–Q5 + pass-2 Q1–Q5) that
resolved residual ambiguities. Each item carries a category tag in brackets
and a `file:line` evidence reference; gaps are tagged `[Gap]` and ambiguities
`[Ambiguity]`.

**Category legend**: Spec | Contract | Constitution | Test | Migration | Compatibility | Convergence

### 1. Spec-completeness — A2-XX evidence in spec.md

- [ ] CHK101 Cycle 2 Amendment Log table at `spec.md:106-118` enumerates all
  eight amendments (A2-01 … A2-08) with severity, cohort source, type, target,
  and one-line summary [Spec, Completeness, `spec.md:106-118`]
- [ ] CHK102 Each Cycle 2 amendment has a detail subsection (`spec.md:119-213`)
  with cohort source, file:line site evidence, type, what-changes prose, and
  acceptance criteria [Spec, Traceability, `spec.md:119-213`]
- [ ] CHK103 FR-067 (degraded_dispatch flag + `signal_pipeline.dispatch_failed`
  audit entry) is fully specified at `spec.md:2619-2647` with HTTP-status,
  body-shape, audit-envelope-shape, and silent-swallow prohibition
  [Spec, Completeness, `spec.md:2619-2647`]
- [ ] CHK104 FR-068 (cascade-rules canonical reconciliation invariant) is
  specified at `spec.md:2649-2665` with build-time-error / round-trip-test /
  byte-aligned-table assertions [Spec, Completeness, `spec.md:2649-2665`]
- [ ] CHK105 FR-069 (`triggered_sub_agents` array in `injection.success`
  envelope) is specified at `spec.md:2667-2677` with structural-identity and
  trigger_source enum requirements [Spec, Completeness, `spec.md:2667-2677`]
- [ ] CHK106 FR-070 (audit-envelope `sub_agent` enum alignment to 9-name
  PascalCase) is specified at `spec.md:2679-2691` with contract-test
  byte-equality requirement [Spec, Completeness, `spec.md:2679-2691`]
- [ ] CHK107 SC-013 (Z6 + Z7 staging-promotion gate) is specified at
  `spec.md:2785-2797` with named SLI thresholds, evidence-freshness window,
  and complementary (not replacing) FR-063 framing
  [Spec, Acceptance Criteria, `spec.md:2785-2797`]
- [ ] CHK108 The Step-8i synthesis severity convergence (2 HIGH + 8 MEDIUM
  → 0 reduced to 8 merit-validated items) is documented in the spec rationale
  preamble at `spec.md:86-104` [Spec, Traceability, `spec.md:86-104`]

### 2. Clarification-coverage — pass-1 + pass-2 Q→A in spec body

- [ ] CHK109 Pass-1 Q1 resolution (FR-067↔FR-069 byte-equality of HTTP body
  and audit envelope's `triggered_sub_agents` arrays, RFC 8785 JCS canonical)
  is recorded in spec body and supersedes FR-067's earlier
  `acknowledged`-only wording [Spec, Clarity, `spec.md:248-277`]
- [ ] CHK110 Pass-1 Q2 resolution (24 h trailing window for both Z6 and Z7
  staging-evidence freshness) is recorded; both SLIs share one
  `staging_run_window` parameter [Spec, Measurability, `spec.md:277-300`]
- [ ] CHK111 Pass-1 Q3 resolution (remove `cascade_rules.yaml`'s
  `fan_out_rules:` block; orchestrator imports `sim_cascade_matrix.py`
  directly; build-time fail-closed check; `evacuation` ↔ `evacuation-centre`
  alias) is recorded [Spec, Clarity, `spec.md:302-337`]
- [ ] CHK112 Pass-1 Q4 resolution (per-subscriber dispatch UUID NOT parent
  `injection_correlation_id`; lexicographic ordering by PascalCase
  `sub_agent` enum) is recorded [Spec, Clarity, `spec.md:339-374`]
- [ ] CHK113 Pass-1 Q5 resolution (`SPEC_036_PROBLEM_JSON_ROUTES:
  Final[frozenset[str]]` allow-list constant in
  `apps/api/app/middleware/error_handler.py`) is recorded
  [Spec, Clarity, `spec.md:376-412`]
- [ ] CHK114 Pass-2 Q1 resolution (3-value `dispatch_status` enum
  `{acknowledged, failed, timed_out}`; new
  `DISPATCH_ACK_TIMEOUT_SECONDS = 5.0`; rate-limit/circuit-open subsumed via
  `exception_class`) is recorded [Spec, Measurability, `spec.md:441-480`]
- [ ] CHK115 Pass-2 Q2 resolution (`degraded_dispatch: bool = False`
  ALWAYS-PRESENT on every HTTP 202 from inject-telemetry) is recorded with
  `TelemetryInjectionAck` Pydantic model implication
  [Spec, Compatibility, `spec.md:482-520`]
- [ ] CHK116 Pass-2 Q3 resolution (hybrid OTel TraceContext + Application
  Insights `customDimensions` correlation_id propagation; child span per
  subscriber) is recorded [Spec, Clarity, `spec.md:522-575`]
- [ ] CHK117 Pass-2 Q4 resolution (`MIN_SAMPLES_PER_SLI_24H: Final[int] = 30`
  for both Z6 and Z7; KQL queries emit `sample_count` column) is recorded
  [Spec, Measurability, `spec.md:577-623`]
- [ ] CHK118 Pass-2 Q5 resolution (allow-list gates BOTH 4xx AND 5xx;
  pre-existing 2xx `evidence-integrity-warning` carve-out preserved via
  `Warning` HTTP header) is recorded [Spec, Clarity, `spec.md:625-670`]

### 3. Contract-readiness — out-of-scope for spec amendment but ready for Step 8o

- [ ] CHK119 `contracts/audit-envelope.md` § 3.2 `injection.success` schema
  ready to add `triggered_sub_agents` to `required` (per FR-069) — current
  schema at `contracts/audit-envelope.md:132,142-149` already includes the
  array but NOT the `dispatch_status` field on each entry [Contract, Gap,
  `contracts/audit-envelope.md:142-149`]
- [ ] CHK120 `contracts/audit-envelope.md` ready to add a new entry-25
  schema for `signal_pipeline.dispatch_failed` (folded A2-08 +
  FR-067 typed envelope) with required fields
  `{partial_successful_subset[], failed_subscriber_list[], exception_class,
  prompt_hash, prompt_hash_source, injection_correlation_id}` [Contract, Gap]
- [ ] CHK121 `contracts/audit-envelope.md:149` `sub_agent` enum ready to be
  bumped from 7 kebab-case names to 9 PascalCase names per FR-070 + Pass-1
  Q4 ordering [Contract, Consistency, `contracts/audit-envelope.md:149`]
- [ ] CHK122 `contracts/error-responses.md:9` ready to be narrowed (per A2-05)
  from a platform-wide RFC 9457 claim to a spec-036 endpoint allow-list
  scoped to `SPEC_036_PROBLEM_JSON_ROUTES`; the 2xx
  `evidence-integrity-warning` carve-out at
  `contracts/error-responses.md:128-148` MUST remain unchanged
  [Contract, Consistency, `contracts/error-responses.md:9`]
- [ ] CHK123 `contracts/sli-thresholds.md` ready to add SLI-6 (Z6, P95
  sub-agent reply latency) and SLI-7 (Z7, map-overlay drift error budget)
  rows to the SLI summary table at `contracts/sli-thresholds.md:13-21`
  with `sc_refs` linking SC-001 (Z6) and SC-010 (Z7) [Contract, Completeness,
  `contracts/sli-thresholds.md:13-21`]
- [ ] CHK124 `infra/observability/sli-kql.json` ready to add Z6 + Z7 KQL
  queries that emit a `sample_count` column (per Pass-2 Q4) so the staging
  gate can assert both `sample_count >= 30` and the threshold predicate
  from a single query result [Contract, Test, Gap]

### 4. Constitution-invariant checks (Cycle 2 changes preserve all v1.2.0 invariants)

- [ ] CHK125 **Primacy of Life (Principle I)** — A2-02 / SC-013 explicitly
  cites primacy of life as the rationale for gating SC-001 + SC-010 by Z6 +
  Z7 with statistically meaningful evidence (Pass-2 Q4) [Constitution,
  `spec.md:296-298`, `spec.md:614-616`]
- [ ] CHK126 **AIIMS Functional Alignment (Principle II-A)** — A2-07 / FR-070
  bumps the audit `sub_agent` enum to the canonical 9-name PascalCase set
  matching `aiims_mapping.py`, preserving Cycle 1 Amendment A's AIIMS
  function-to-sub-agent mapping [Constitution, `spec.md:2679-2691`]
- [ ] CHK127 **AWS three-tier (Principle V-A)** — Cycle 2 introduces no new
  warning-tier vocabulary; Cycle 1 Amendment K's Advice/Watch-and-Act/
  Emergency-Warning palette remains the only AWS surface
  [Constitution, Compatibility, no new evidence required]
- [ ] CHK128 **AU residency** — Cycle 2 adds no new data-egress paths;
  Application Insights `customDimensions` (Pass-2 Q3) and Cosmos audit
  writes remain in Australia East / Australia Southeast regions
  [Constitution, `.specify/memory/constitution.md:242-243`]
- [ ] CHK129 **Human-in-the-loop (HITL)** — A2-01 / FR-067 degraded-dispatch
  is a graceful-degradation surface, not an autonomous-action authorisation;
  no Cycle 2 amendment introduces a new agent-initiated real-world action
  [Constitution, `.specify/memory/constitution.md:240-241`]
- [ ] CHK130 **AVM-first** — Cycle 2 introduces no new infrastructure
  primitives; Z6 + Z7 reuse the existing Application Insights workspace and
  Cosmos containers [Constitution, Compatibility]
- [ ] CHK131 **3-Container-App cap** — Pass-1 Q3's choice to remove
  `cascade_rules.yaml`'s `fan_out_rules:` block (rather than introduce a
  parallel config service) is explicitly rationalised against the
  3-Container-App cap [Constitution, `spec.md:329-330`]
- [ ] CHK132 **Graceful Degradation (Principle V)** — A2-01 / FR-067 cites
  Principle V as the rationale for the degraded-dispatch flag (predictable
  failure with explicit machine-readable indicator); A2-05 cites Principle V
  for narrowing scope rather than expanding blast radius onto legacy
  surfaces [Constitution, `spec.md:227-229`, `spec.md:232-233`]

### 5. Test-pyramid readiness — every new FR/SC has unit + integration + contract targets identified

- [ ] CHK133 FR-067 has unit (degraded-dispatch response-shape serialiser),
  integration (orchestrator partial-failure scenario asserts HTTP 202 +
  `degraded_dispatch=true` + audit envelope), and contract
  (`signal_pipeline.dispatch_failed` schema) targets identified
  [Test, `spec.md:128-132`]
- [ ] CHK134 FR-068 has unit (`sim_cascade_matrix.evacuation` alias
  resolver), integration (live-orchestrator round-trip per cascade
  category), and contract (`tests/contract/test_cascade_yaml_no_fan_out_rules.py`
  build-time check) targets identified [Test, `spec.md:154-157`,
  `spec.md:322-324`]
- [ ] CHK135 FR-069 has unit (audit-details-dict builder), integration
  (byte-equality assertion between response body and audit envelope under
  RFC 8785 JCS), and contract (audit-envelope §3.2 schema regeneration)
  targets identified [Test, `spec.md:166-169`]
- [ ] CHK136 FR-070 has unit (no — pure schema/enum), integration (audit
  write-then-read round-trip with PascalCase names), and contract
  (`tests/contract/test_audit_envelope_sub_agent_enum.py` byte-equality
  vs `ALL_SUB_AGENTS`) targets identified [Test, `spec.md:2685-2687`]
- [ ] CHK137 SC-013 has unit (no — promotion gate), integration
  (`tests/staging_gates.py` `MIN_SAMPLES_PER_SLI_24H >= 30` + threshold
  assertion), and contract (sli-kql.json Z6 + Z7 emit `sample_count` and
  `sc_refs` columns) targets identified [Test, `spec.md:142-144`,
  `spec.md:597-602`]
- [ ] CHK138 Pass-1 Q5 / pass-2 Q5 RFC 9457 allow-list has a contract test
  (`tests/contract/test_spec_036_route_allow_list.py`) covering BOTH 4xx
  AND 5xx synthetic errors per Pass-2 Q5 option (b) [Test, `spec.md:394-398`,
  `spec.md:656-660`]

### 6. Backward-compatibility checks — Cycle 2 introduces explicit HTTP-API surface changes

- [ ] CHK139 **`TelemetryInjectionAck` response-shape change is breaking**:
  Pass-2 Q2 mandates `degraded_dispatch: bool = False` ALWAYS-PRESENT;
  pre-Cycle-2 clients that exhaustively-validate response keys (e.g.
  Pydantic `model_config = ConfigDict(extra="forbid")`) will reject the
  new field. This MUST be flagged in `CHANGELOG.md` and surfaced as a
  staging-promotion talking-point [Compatibility, **BREAKING**,
  `spec.md:482-520`]
- [ ] CHK140 **`triggered_sub_agents` entry-shape change is breaking**:
  FR-067 + FR-069 + Pass-1 Q4 mandate each entry now carries
  `dispatch_status` + per-subscriber `correlation_id` (NOT parent
  `injection_correlation_id`); pre-Cycle-2 audit-export consumers JOINing
  on `correlation_id` will silently mismatch. This MUST be flagged in
  audit-export consumer migration notes [Compatibility, **BREAKING**,
  `spec.md:340-348`]
- [ ] CHK141 **`sub_agent` enum change is breaking for new writes**: FR-070
  switches new audit writes from 7-name kebab-case to 9-name PascalCase;
  audit-export readers MUST handle BOTH historic and new forms during the
  transition window [Compatibility, **BREAKING for new writes**,
  `spec.md:2679-2691`]
- [ ] CHK142 **No new endpoints, methods, or path parameters** are
  introduced by Cycle 2 — the changes are confined to (a) response-body
  shape on the existing inject-telemetry endpoint, (b) audit-envelope
  shape, and (c) the legacy/spec-036 RFC 9457 surface split
  [Compatibility, Completeness]

### 7. Migration checks — operator runbooks and historic data

- [ ] CHK143 Operator runbooks referencing `apps/api/app/config/cascade_rules.yaml`'s
  `fan_out_rules:` block MUST be updated to reflect Pass-1 Q3's removal of
  that block; the YAML retains only `ladder:` and `cap:` keys
  [Migration, `spec.md:312-314`]
- [ ] CHK144 Existing audit rows with kebab-case `sub_agent` values
  (`monitoring`, `planning`, `resource-allocation`, `communication`,
  `evacuation`, `risk-assessment`, `simulation-telemetry-injection`) remain
  readable; FOI / lessons-capture export pathways MUST tolerate both
  kebab-case (historic) and PascalCase (post-Cycle-2) forms
  [Migration, `spec.md:2687-2691`]
- [ ] CHK145 Operator runbook for the staging-promotion gate MUST be updated
  to include the new Z6 + Z7 SLI checks and the
  `MIN_SAMPLES_PER_SLI_24H = 30` floor; staging environments with
  insufficient synthetic-injection traffic MUST schedule background load
  to satisfy the floor [Migration, `spec.md:606-608`]
- [ ] CHK146 The Cycle 1 Amendment N "Cascade matrix (canonical)" table at
  `spec.md:41` and the Python module `sim_cascade_matrix.py` MUST stay
  byte-aligned post-Cycle-2; FR-068 makes this an explicit invariant rather
  than an implicit one [Migration, Consistency, `spec.md:2663-2665`]

### 8. Convergence checks — 2 HIGH + 3 MEDIUM + 3 LOW from Step 8i synthesis

- [ ] CHK147 **HIGH A2-01** (Operations Officer + Field Coordinator +
  Observer-Auditor) — addressed via FR-067 + FR-009/FR-015 STRENGTHEN +
  folded A2-08 typed envelope [Convergence, `step-8i-synthesis.md` ll. 35-39]
- [ ] CHK148 **HIGH A2-02** (sre-engineer) — addressed via SC-013 +
  FR-063 STRENGTHEN naming Z1..Z7 [Convergence, `step-8i-synthesis.md`
  ll. 41-44]
- [ ] CHK149 **MEDIUM A2-03** (Logistics + Resilience Planner) — addressed
  via FR-068 + Pass-1 Q3 (YAML removal) + alias key
  [Convergence, `step-8i-synthesis.md` ll. 48-51]
- [ ] CHK150 **MEDIUM A2-04** (Observer-Auditor) — addressed via FR-069 +
  Pass-1 Q1 byte-equality + Pass-1 Q4 per-subscriber `correlation_id`
  semantics [Convergence, `step-8i-synthesis.md` ll. 53-56]
- [ ] CHK151 **MEDIUM A2-05** (api-architect) — addressed via contract
  narrowing + Pass-1 Q5 allow-list + Pass-2 Q5 4xx+5xx scope
  [Convergence, `step-8i-synthesis.md` ll. 58-61]
- [ ] CHK152 **LOW A2-06** (software-developer) — addressed via FR-048
  STRENGTHEN removing `sequence_number=1` placeholder
  [Convergence, `step-8i-synthesis.md` ll. 69-72]
- [ ] CHK153 **LOW A2-07** (sectors) — addressed via FR-070 +
  byte-equality contract test [Convergence, `step-8i-synthesis.md`
  ll. 74-77]
- [ ] CHK154 **LOW A2-08** (Observer-Auditor, folded) — addressed by FR-067
  typed `signal_pipeline.dispatch_failed` envelope without a duplicate FR
  [Convergence, `step-8i-synthesis.md` ll. 79-82]
- [ ] CHK155 **DEFERRED items** (sectors maritime/coastal/aviation; ACT
  branding; VIC fire ordering; KQL field-name verify; runtime-gate "no rows"
  sentinel; overlay summary visual diff; AAA contrast numeric; executive
  review calendar) are explicitly recorded as backlog at `spec.md:220-226`
  with FR-021 step-5 fallback rationale [Convergence, `spec.md:220-226`]
- [ ] CHK156 **Aggregate severity convergence** — Step 8i synthesis records
  CRITICAL 18→0, HIGH 39→2, MEDIUM 24→8, LOW 4→8 (doc-drift); Cycle 2
  closes the 2 HIGH + the 3 merit-validated MEDIUM + the 3 LOW that have
  merit, leaving only the explicitly-deferred items
  [Convergence, `step-8i-synthesis.md` ll. 22-27]

**Cycle 2 quality checklist locked. Ready for /speckit.plan.**

---

## Cycle 3 Quality Checklist (post Step 8s cohort re-review amendments)

This section validates the **six** Cycle 3 amendments (A3-01 → A3-06), the
**eight** clarification Q→A entries (Cycle 3 Pass-1 Q1–Q5 + Cycle 3 Pass-2
Q1–Q3), and the propagation queue assembled by Step 8x. Each item carries a
category tag in brackets and a `file:line` evidence reference; gaps are
tagged `[Gap]` and ambiguities `[Ambiguity]`. Cycle 1 (CHK001–CHK100) and
Cycle 2 (CHK101–CHK156) rows remain in force unchanged and are out-of-scope
for this section. Per the lock-zone constraint, no prior row is modified.

**Category legend**: Spec | Contract | Constitution | Test | Workflow | Docs | Anti-pattern | Convergence

### 9. Cycle 3 amendment evidence in `spec.md` (A3-01 → A3-06)

- [ ] CHK157 **HIGH A3-01 / FR-071** — staging-promotion gate workflow MUST
  invoke `tests.staging_gates.assert_sli_thresholds()` (or the equivalent
  `pytest tests/integration/test_assert_sli_thresholds_z6_z7.py -q`) on every
  gate run and exit non-zero on any breach or sample-floor underage; the
  acceptance criteria explicitly prohibit the unconditional success message
  `"All 7 SLIs within threshold — promotion allowed."` and prohibit branching
  only on `proc.returncode != 0` from the upstream `az` call
  [Spec, Acceptance Criteria, `spec.md:285-288` + `spec.md:3625-3641`]
- [ ] CHK158 **HIGH A3-02 / FR-072** — synthetic smoke-injection job MUST
  invoke `requests.post(f"{STAGING_API_BASE}/api/simulations/{sim_id}/inject-telemetry", …)`
  for every constructed payload, assert HTTP 202 + `degraded_dispatch=false`,
  and source `STAGING_API_BASE` from the GitHub `staging` environment
  (NOT a repository-level secret); print-only stub bodies are explicitly
  rejected [Spec, Acceptance Criteria, `spec.md:297-301` + `spec.md:3643-3658`]
- [ ] CHK159 **MEDIUM A3-03** — `docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md:87`
  and `CHANGELOG.md:20` MUST cite the actual public symbol
  `tests/staging_gates.py::assert_sli_thresholds()` (NOT the non-existent
  `_is_breach()`) [Spec, Acceptance Criteria, `spec.md:303-313`]
- [ ] CHK160 **MEDIUM A3-04** — ADR-036-010 (`:83-84`) and `CHANGELOG.md:19`
  MUST quote the canonical SLI-Z6 thresholds gpt-4o `warn=4000 / breach=5000`
  ms and gpt-4o-mini `warn=1500 / breach=2000` ms (NOT the drifted
  `warn=2500 / breach=5000` and `warn=1800 / breach=2000`)
  [Spec, Acceptance Criteria, `spec.md:315-325`]
- [ ] CHK161 **MEDIUM A3-05 / FR-073** — Z6 implementation KQL at
  `infra/observability/sli-kql.json:67-81` MUST extend `sub_agent` and
  `env` from `customDimensions`, filter `where env == "staging"`, and
  `summarize … by sub_agent, model_deployment` (28-series cardinality)
  matching `contracts/sli-thresholds.md:230-244` byte-for-byte after
  canonicalisation [Spec, Acceptance Criteria, `spec.md:327-337` +
  `spec.md:3660-3677`]
- [ ] CHK162 **MEDIUM A3-06 (folded into FR-073)** — Z7 KQL at
  `infra/observability/sli-kql.json:82-96` MUST compute
  `drift_ms = client_received_ms − server_emit_ms`, filter
  `where env == "staging"`, and set `breach_pct: 99.0` (NOT the drifted
  `99.5` that makes warn and breach indistinguishable) per
  `contracts/sli-thresholds.md:269-270, 276-289`
  [Spec, Acceptance Criteria, `spec.md:339-351`]
- [ ] CHK163 Cycle 3 Amendment Log summary table at `spec.md:267-274`
  enumerates all six amendments (A3-01 … A3-06) with severity, cohort
  source, type, target, and one-line summary [Spec, Completeness,
  `spec.md:267-274`]
- [ ] CHK164 **SC-014** (Cycle 3 staging-promotion gate refusal under
  synthetic canary) is specified at `spec.md:3784-3794` with non-zero exit,
  no `promote/{build_label}` git tag created, and no downstream production
  deploy invariants; SC-014 explicitly *complements* (does not replace)
  SC-013 [Spec, Acceptance Criteria, `spec.md:3784-3794`]

### 10. Cycle 3 Pass-1 + Pass-2 clarification Q→A coverage

- [ ] CHK165 **Pass-1 Q1** (KQL canonicalisation algorithm) — resolution
  pins **strict-string-after-normalisation** with a deterministic six-step
  pipeline (strip comments → collapse whitespace + preserve newline before
  `|` → lowercase Kusto reserved keywords → sort `by` columns
  lexicographically → sort `summarize` aggregate aliases → strip redundant
  outer parentheses); Kusto-AST equivalence is **explicitly rejected**
  [Spec, Clarity, `spec.md:838-925`]
- [ ] CHK166 **Pass-1 Q2** (smoke-token rotation + tenant isolation) —
  resolution pins **NO long-lived `SMOKE_TOKEN` secret**; bearer is
  short-lived OIDC-derived via `azure/login@v2` + `az account get-access-token`
  (per workflow run, automatic), and `tnt-stg-smoke` carries five named
  isolation guarantees: data residency (australiaeast), sole-tenant scope,
  posture parity (private endpoint + CMK + soft-delete 7d), Z6/Z7 KQL
  filtering (`| where tenant_id == "tnt-stg-smoke"`), and least-privilege
  `Simulation.Coordinator` test identity scoped exclusively to
  `tnt-stg-smoke` [Spec, Clarity, `spec.md:926-1014`]
- [ ] CHK167 **Pass-1 Q3** (concurrent gate refusals) — resolution pins
  **two distinct `staging_promotion.refused` audit envelope rows** for
  two concurrently-failing gate runs, each with a fresh
  `staging_promotion_correlation_id` (UUID4); coalescing or deduplication
  at the audit-write boundary is rejected; envelope MUST be written by the
  gate-helper BEFORE the `StagingPromotionRefused` exception propagates
  [Spec, Clarity, `spec.md:1016-1098`]
- [ ] CHK168 **Pass-1 Q4** (SC-014 synthetic-canary input mechanism) —
  resolution pins **option (b): CI-level Python fixture** consumed via
  `assert_sli_thresholds(sli_results=red_fixture)`; live-KQL injection
  (option a) and dedicated `tnt-stg-canary` tenant (option c) are both
  **explicitly rejected**; the canary fixture set MUST cover four red
  shapes (Z6 P95 latency breach, Z7 drift breach, Z6 sample starvation,
  Z7 sample starvation), each asserting four invariants (raises
  `StagingPromotionRefused` + non-zero subprocess exit + no
  `promote/{build_label}` git tag + envelope written exactly once)
  [Spec, Clarity, `spec.md:1099-1182`]
- [ ] CHK169 **Pass-1 Q5** (FR-073 retroactive scope) — resolution pins
  **all seven SLIs (Z1–Z7)** as the canonicalisation contract surface;
  Z6+Z7 are the cohort-finding-driven minimum, but the contract surface
  is universal; the one-time Z1-Z5 alignment audit folds into the same
  Step 8z PR that lands the contract test [Spec, Clarity,
  `spec.md:1183-1250`]
- [ ] CHK170 **Pass-2 Q1** (`audit-envelope.md` slot + counter increment) —
  resolution pins **§3.26** as the natural slot for the new
  `staging_promotion.refused` typed envelope (immediately after Cycle 2's
  §3.25 `signal_pipeline.dispatch_failed`; the §3.20–§3.24 gap is
  **preserved**, NOT back-filled); the typed-entry counter increments
  **25 → 26** at `contracts/audit-envelope.md:689` and `:703`
  [Spec, Clarity, `spec.md:1308-1387`]
- [ ] CHK171 **Pass-2 Q2** (canonicaliser Python public surface) —
  resolution pins the public `tests/contract/_kql_canonicaliser.py`
  surface to **two free public functions plus one private helper**:
  `canonicalise_kql(text: str) -> str`, `canonical_kql_for_sli(sli_id: str,
  *, thresholds_path: Path | None = None) -> str`, and private
  `_canonicalise_kql_string(raw: str) -> str`; module-level
  `_THRESHOLDS_PATH = Path(__file__).resolve().parents[2] / "specs" /
  "036-sim-agent-extend" / "contracts" / "sli-thresholds.md"`;
  `__all__ = ["canonicalise_kql", "canonical_kql_for_sli"]`;
  `KeyError` for unknown sli_id, `ValueError` for malformed contracts
  file [Spec, Clarity, `spec.md:1388-1483`]
- [ ] CHK172 **Pass-2 Q3** (Z1-Z5 alignment audit landing pattern) —
  resolution pins **CO-MERGE in a single Cycle 3 Step 8z PR** for
  `_kql_canonicaliser.py` + `test_kql_canonicaliser_unit.py` +
  `test_sli_kql_canonical_match.py` + any Z1-Z5 drift fixes; sequential
  audit-first-then-test-first is **explicitly rejected**; Step 8x
  (contracts subsection + §3.26 envelope schema) MUST land before Step 8z
  opens by artefact dependency [Spec, Clarity, `spec.md:1484-1605`]

### 11. Audit-envelope §3.26 `staging_promotion.refused` schema readiness

- [ ] CHK173 `contracts/audit-envelope.md` §3.26 schema MUST declare the
  eight-field `details` set pinned by Pass-1 Q3:
  `staging_promotion_correlation_id` (UUID4), `build_label` (str from
  `workflow_dispatch.inputs.build_label`), `triggering_workflow_run_id`
  (int from `github.run_id`), `triggering_actor` (str from `github.actor`),
  `breached_slis` (`list[str]`), `sample_floor_underages`
  (`list[{sli_id, observed_samples, required_samples}]`), `refused_at`
  (ISO-8601 timestamp), and `gate_helper_version` (sha-256 of
  `tests/staging_gates.py`) [Contract, Completeness, `spec.md:1029-1039` +
  `spec.md:1336-1346`]
- [ ] CHK174 §3.26 schema MUST declare an `entry_type` const discriminator —
  `{ "type": "string", "const": "staging_promotion.refused" }` — for
  typed-envelope discriminator parity with §3.25
  `signal_pipeline.dispatch_failed` (Cycle 2 Amendment A2-01)
  [Contract, Consistency, `spec.md:1340-1342` + `spec.md:1365-1369`]
- [ ] CHK175 §3.26 schema MUST include a top-level `correlation_id` field
  whose value equals the `details.staging_promotion_correlation_id` so
  the established single-stream JOIN-by-`correlation_id` invariant from
  Cycle 2 Pass-1 Q4 keeps working at the workflow-run granularity
  [Contract, Consistency, `spec.md:1342-1346` + `contracts/audit-envelope.md:735-736`]
- [ ] CHK176 Typed-entry counter increment MUST land in **two** places:
  the `entry_type` enumeration list at `contracts/audit-envelope.md:689`
  ("any of the **25** typed entries above" → "any of the **26** typed
  entries above") AND the §6.1 heading at `contracts/audit-envelope.md:703`
  ("5 added in Cycle 1, 1 added in Cycle 2 — total 19 → 25" → "5 added
  in Cycle 1, 1 added in Cycle 2, 1 added in Cycle 3 — total 19 → 26")
  with a new §6.1 table row referencing Cycle 3 Amendment A3-01 / FR-071
  and Cosmos container `simulation_audit_entries`
  [Contract, Completeness, `spec.md:1310-1318` + `spec.md:1370-1378`]
- [ ] CHK177 The §3.20–§3.24 envelope-section gap MUST be **preserved**
  (not back-filled by §3.26); back-filling the gap obscures temporal
  ordering of envelope additions across cycles and breaks tooling indexed
  on the §3.25 anchor [Contract, Consistency, `spec.md:1325-1330`]
- [ ] CHK178 `gap-free sequence_number` MUST be allocated by the audit
  writer (NOT a literal in the schema), inheriting the Cycle 2 Amendment
  A2-06 `cascade.depth2_refused` precedent at
  `contracts/audit-envelope.md:726`; the §3.26 schema MUST NOT carry a
  placeholder `sequence_number = 1` [Contract, Consistency,
  `spec.md:1330-1336`]

### 12. Anti-pattern rejection rows (PR review gates)

- [ ] CHK179 **Anti-pattern: `pytest.mark.xfail` on canonicaliser PR** —
  any PR that lands `tests/contract/test_sli_kql_canonical_match.py`
  with a `pytest.mark.xfail`, `pytest.mark.skip`, or any conditional skip
  decorator on the parametrised test MUST be rejected at code review;
  the contract test MUST be **green at PR-merge time** for every declared
  SLI [Anti-pattern, `spec.md:1494-1496` + `spec.md:1569-1572`]
- [ ] CHK180 **Anti-pattern: hard-coded SLI subset on canonicaliser PR** —
  any PR that hard-codes a subset of SLIs (e.g. `["SLI-Z6", "SLI-Z7"]`)
  in the parametrise expression rather than iterating over every entry
  in `sli_doc["slis"]` MUST be rejected; the test MUST use
  `@pytest.mark.parametrize("sli_id", [s["id"] for s in sli_doc["slis"]])`
  so any SLI added to `sli-kql.json` after Cycle 3 automatically
  participates in canonicalisation enforcement
  [Anti-pattern, `spec.md:1213-1217` + `spec.md:1474-1477`]
- [ ] CHK181 **Anti-pattern: incomplete canary fixture coverage** —
  any PR that lands `test_synthetic_canary_refused_red_sli_row` with
  fewer than the four required red shapes (Z6 P95 latency breach + Z7
  drift breach + Z6 sample starvation + Z7 sample starvation) or with
  fewer than the four invariants per shape (raises
  `StagingPromotionRefused` + non-zero subprocess exit + no
  `promote/{build_label}` git tag + envelope written exactly once) MUST
  be rejected at code review [Anti-pattern, `spec.md:1138-1148` +
  `spec.md:1172-1174`]

### 13. Docs-drift regression-test rows

- [ ] CHK182 New regression test `tests/docs/test_adr_036_010_threshold_drift.py`
  MUST parse `docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md`'s
  threshold table (and the `CHANGELOG.md:19` quote) and assert every
  numeric value is byte-equal to the corresponding SLI-Z6 field in
  `infra/observability/sli-kql.json`; this prevents recurrence of the
  A3-04 numeric drift class (gpt-4o `warn=2500 / 5000` vs canonical
  `4000 / 5000`; gpt-4o-mini `warn=1800 / 2000` vs canonical
  `1500 / 2000`) [Test, Docs, `spec.md:325` (acceptance criterion)]
- [ ] CHK183 New regression test `tests/docs/test_adr_036_010_symbol_citations.py`
  (or equivalent under `tests/docs/`) MUST parse ADR-036-010 + `CHANGELOG.md`
  and assert every cited Python symbol resolves via `importlib`; this
  prevents recurrence of the A3-03 dead-reference class (the cited
  `tests/staging_gates.py::_is_breach()` does not exist) [Test, Docs,
  `spec.md:313` (acceptance criterion)]

### 14. Step-8z artefact + Step-8x propagation readiness

- [ ] CHK184 New `tests/contract/_kql_canonicaliser.py` MUST implement the
  Pass-2 Q2 public surface — `canonicalise_kql`, `canonical_kql_for_sli`,
  private `_canonicalise_kql_string`, module-level `_THRESHOLDS_PATH`
  constant, `__all__` declaration — with the canonicalisation pipeline
  asserted **deterministic**, **idempotent**
  (`canonicalise_kql(canonicalise_kql(x)) == canonicalise_kql(x)` for
  every input), and stable across CPython 3.12+ runtimes
  [Test, Contract, `spec.md:885-889` + `spec.md:1463-1468`]
- [ ] CHK185 New `tests/contract/test_kql_canonicaliser_unit.py` MUST
  golden-fixture-test each of the six normalisation steps in isolation
  AND assert idempotence + determinism + 10× re-run byte-equality on
  the private `_canonicalise_kql_string` surface [Test, Contract,
  `spec.md:1469-1472`]
- [ ] CHK186 New `tests/integration/test_staging_promotion_concurrency.py`
  MUST invoke `assert_sli_thresholds()` twice concurrently against
  shared red-fixture data and assert two distinct envelope rows + two
  distinct `staging_promotion_correlation_id` values + two non-zero
  process exits — never a coalesced single envelope [Test, Workflow,
  `spec.md:1094-1097`]
- [ ] CHK187 New `tests/contract/test_smoke_tenant_isolation.py` MUST
  assert the role-assignment list emitted by
  `infra/bicep/modules/cosmos-simulation-containers.bicep` contains
  exactly one entry referencing `Simulation.Coordinator`, and that entry
  is scoped exclusively to `tnt-stg-smoke` (no production-tenant
  scope present) [Test, Contract, `spec.md:966-970` + `spec.md:1004-1007`]
- [ ] CHK188 `.github/workflows/staging-promotion.yml` MUST be amended at
  Step 8z to add a workflow-level `concurrency: { group:
  staging-promotion-${{ github.workflow }}-${{ github.ref }},
  cancel-in-progress: false }` block so concurrent dispatches queue at
  the GitHub Actions layer rather than racing the gate-helper boundary
  [Workflow, `spec.md:1090-1093`]
- [ ] CHK189 `tests/staging_gates.py:98-130` `assert_sli_thresholds()`
  MUST be extended to instantiate the audit-envelope writer and emit a
  `staging_promotion.refused` envelope **before** each
  `StagingPromotionRefused` raise — the workflow YAML is the propagation
  surface, NOT the binding contract surface [Test, Workflow,
  `spec.md:1041-1045` + `spec.md:1086-1089`]
- [ ] CHK190 `contracts/sli-thresholds.md:230-244` (Z6) and `:276-289`
  (Z7) canonical KQL bodies MUST be amended at Step 8x to add
  `| where tenant_id == "tnt-stg-smoke"` (per Pass-1 Q2 isolation
  guarantee iv) so smoke-injected events are visible to the gate but
  provably never contaminate production-tenant SLI evaluation
  [Contract, `spec.md:954-960` + `spec.md:995-998`]
- [ ] CHK191 `contracts/sli-thresholds.md` MUST gain a new
  §"KQL canonicalisation contract" subsection at Step 8x documenting
  the public surface from Pass-2 Q2 (function names, signatures, return
  types, error contracts, `_THRESHOLDS_PATH` resolution) so consumers
  rely on the contract without spelunking the implementation
  [Contract, Docs, `spec.md:1478-1482`]
- [ ] CHK192 New `docs/aidr/decisions/ADR-036-NN-cycle-3-amendment-cycle.md`
  MUST be authored at Step 8x recording (a) the Cycle 3 explicit
  **non-application** of ADR-031's `AZURE_CREDENTIALS` long-lived-secret
  fallback to `staging-promotion.yml` and (b) the **co-merge decision**
  for the Step 8z PR with the three-outcome rubric: (i) all 7 SLIs
  byte-equal-after-canonicalisation on first run / (ii) drift surfaced
  on Z1-Z5 and fixed inline / (iii) drift requires plan-level decision
  (`(plan-touch)` fall-through) [Docs, `spec.md:1012-1014` +
  `spec.md:1573-1577` + `spec.md:1519-1532`]
- [ ] CHK193 In-place spec-text propagations MUST land at Step 8x:
  (a) FR-072 at `spec.md:3651-3653` replaces the `"$SMOKE_TOKEN"`
  shorthand with OIDC-bearer wording per Pass-1 Q2; (b) FR-071 at
  `spec.md:3625-3641` appends a sentence mandating the
  `staging_promotion.refused` envelope at §3.26 with fresh
  `staging_promotion_correlation_id`; (c) SC-014 at `spec.md:3784-3794`
  appends "fixture-driven, no live-KQL injection" sentence per Pass-1
  Q4; (d) FR-073 at `spec.md:3675-3677` re-words "covers both Z6 and
  Z7" → "covers all seven SLIs (Z1–Z7); Z6+Z7 are the cohort-finding
  minimum but the contract surface is universal" per Pass-1 Q5
  [Spec, Workflow, `spec.md:991-994` + `spec.md:1075-1081` +
  `spec.md:1166-1171` + `spec.md:1234-1240`]
- [ ] CHK194 The Step 8z `tasks.md` task MUST be a **single co-merge
  unit** encompassing `_kql_canonicaliser.py` +
  `test_kql_canonicaliser_unit.py` + `test_sli_kql_canonical_match.py`
  + any Z1-Z5 drift fixes, with an explicit dependency edge to Step 8x
  (contracts subsection + §3.26 envelope schema MUST land first because
  the Step 8z contract test asserts those surfaces' existence)
  [Workflow, `spec.md:1559-1568`]

### 15. Convergence — Cycle 3 closure

- [ ] CHK195 **Cycle 3 amendment scope** — six findings (2 HIGH + 4
  MEDIUM) close via three new FRs (FR-071, FR-072, FR-073), one new
  success criterion (SC-014), zero existing-FR strengthenings, and zero
  contract-scope reconciliations; Cycle 1 amendments A–S and Cycle 2
  amendments A2-01 → A2-08 remain in force unchanged
  [Convergence, `spec.md:252-256`]
- [ ] CHK196 **Cycle 3 sentinel chain** at end of `spec.md` records the
  five sequential gate states (L3796 Cycle 2 amendment scope locked →
  L3798 Cycle 2 clarify pass 1 complete → L3800 Cycle 2 clarify pass 2
  complete → L3802 Cycle 3 amendment specify complete → L3804 Cycle 3
  clarify pass 1 complete → L3806 Cycle 3 clarify pass 2 complete);
  the next sentinel ("Cycle 3 checklist complete") is appended by Step
  8x [Convergence, `spec.md:3796-3806`]

**Cycle 3 quality checklist locked. Ready for /speckit.plan.**

---

## Cycle 4 Quality Checklist (post Step 8ac cohort re-review amendments)

This section validates the **two** Cycle 4 amendments (A4-01 + A4-02), the
**nine** clarification Q→A entries (Cycle 4 Pass-1 Q1–Q5 + Cycle 4 Pass-2
Q1–Q4), and the propagation queue assembled by Steps 8ad / 8ae. Each item
carries a category tag in brackets and a `file:line` evidence reference;
gaps are tagged `[Gap]` and ambiguities `[Ambiguity]`. Cycle 1
(CHK001–CHK100), Cycle 2 (CHK101–CHK156), and Cycle 3 (CHK157–CHK196) rows
remain in force unchanged and are out-of-scope for this section. Per the
lock-zone constraint, no prior row is modified. Cycle 4 is **narrower in
scope** than Cycle 3: zero new FRs, zero new SCs, one FR strengthening
(FR-073 author-time column-resolution sub-bullet via A4-01), and one
self-documentation supersession (Cycle 3 Pass 1 Q2 item (v) at
`spec.md:961-966` superseded by A4-02's binding corrected wording).

**Category legend**: Spec | Contract | Constitution | Test | Workflow | Docs | Anti-pattern | Convergence

### 16. Cycle 4 amendment evidence in `spec.md` (A4-01 → A4-02)

- [ ] CHK197 **HIGH A4-01 / FR-073 (KQL fix — JSON site)** —
  `infra/observability/sli-kql.json:91` (Z7 `kql` value) MUST contain
  `| extend model_deployment = tostring(customDimensions["model_deployment"])`
  inserted between the existing `extend tenant_id = ...` segment and the
  `where env == "staging"` segment; the new clause MUST be byte-identical
  in ordering and quoting to the corresponding Z6 line at
  `infra/observability/sli-kql.json:76` (the working asymmetric comparator)
  [Spec, Acceptance Criteria, `spec.md:3884` + `spec.md:3889`]
- [ ] CHK198 **HIGH A4-01 / FR-073 (KQL fix — contract symmetric site)** —
  `specs/036-sim-agent-extend/contracts/sli-thresholds.md:280-296` §6b Z7
  KQL block MUST gain the same `extend model_deployment` line in the
  symmetric position (after `extend tenant_id`, before
  `where env == "staging"`) so the contract block remains
  byte-equal-after-canonicalisation to the JSON
  [Contract, Acceptance Criteria, `spec.md:3885` + `spec.md:3890`]
- [ ] CHK199 **HIGH A4-01 / byte-equality preservation** — the Cycle 3
  parametric test `tests/contract/test_sli_kql_canonical_match.py` MUST
  continue to pass byte-equality across all seven SLIs (Z1–Z7) after the
  symmetric Z7 fix is applied to both `sli-kql.json` and
  `contracts/sli-thresholds.md`; the canonicaliser-driven byte-equality
  contract surface from Cycle 3 Pass-1 Q1 / Pass-2 Q2 is preserved
  [Test, Convergence, `spec.md:3891` + `spec.md:1494-1496`]
- [ ] CHK200 **Cycle 4 Amendment Log table** at `spec.md:3866-3871`
  enumerates both amendments (A4-01 + A4-02) with severity, cohort
  source, type, target, and one-line summary; the FR-073 strengthening
  is recorded at `spec.md:3922-3934` and will be folded into FR-073's
  acceptance text in Step 8ad [Spec, Completeness, `spec.md:3866-3871`
  + `spec.md:3922-3934`]
- [ ] CHK201 **MEDIUM A4-02 / ADR-036-011 in-place revision** —
  `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md` MUST gain
  a new "Cycle 4 amendment" sub-section near the end of the document
  capturing A4-01 (FR-073 column-resolution sub-bullet) + A4-02 (RBAC
  scope wording correction) effects with explicit cross-references to
  the two `[CLARIFIED Cycle 4 Pass 1 Qn]` markers at `spec.md:3894` and
  `spec.md:3914` and to the binding corrected wording at `spec.md:3906`
  [Docs, Acceptance Criteria, `spec.md:4300-4307` + `spec.md:4338-4344`]
- [ ] CHK202 **MEDIUM A4-02 / immutability discipline** — the Cycle 4
  amendment sub-section appended to ADR-036-011 MUST preserve all
  Cycle 3 prior content **verbatim** (no rewriting of pre-Cycle-4
  paragraphs); corrections are appended as sub-sections, not folded
  silently into prior prose, per the immutability discipline at
  `spec.md:3947-3950` and the Cycle 2 Q1 supersession precedent at
  `spec.md:389-392` [Docs, Consistency, `spec.md:4307-4309` +
  `spec.md:3905`]
- [ ] CHK203 **MEDIUM A4-02 / corrected wording (dual phrasing +
  backlog citation)** — `ADR-036-011-cycle-3-amendment-cycle.md:172-173`
  MUST be rewritten to the three-clause acknowledgement at
  `spec.md:3904-3906`: (a) actual Bicep scope is database-level
  (`'${account.id}/dbs/${databaseName}'`); (b) tenant isolation is a
  query-time **"compensating defence-in-depth control"** via
  `where tenant_id == "tnt-stg-smoke"` on Z6/Z7 KQL bodies (FR-073);
  (c) inline citation of the deferred-remediation backlog issue id (or
  `[backlog issue: TBD]` placeholder until the issue is filed). The
  *"scoped exclusively to `tnt-stg-smoke`"* phrasing is **explicitly
  rejected** [Docs, Acceptance Criteria, `spec.md:3901` + `spec.md:3904-3906`
  + `spec.md:4083-4115`]
- [ ] CHK204 **MEDIUM A4-02 / ADR Status convergence** — ADR-036-011
  Status field remains `Proposed` at Step 8ae close; the
  `Proposed → Accepted` flip occurs only on a clean Step 8al cohort
  re-review verdict (0 OBJECT votes AND 0 NEW merit-validated findings
  against ADR-036-011); there is **no time-bound auto-flip**, the rule
  is recorded inline within the Cycle 4 amendment sub-section, and it
  applies recursively across Cycle 5+ until first clean verdict
  [Docs, Convergence, `spec.md:4309-4311` + `spec.md:4595-4637`]
- [ ] CHK205 **MEDIUM A4-02 / spec mirror correction** —
  `spec.md:961-966` (Cycle 3 Pass 1 Q2 item (v) "Least-privilege test
  identity" narrative) is **explicitly superseded** by A4-02's binding
  corrected wording at `spec.md:3906` per the Cycle 2 Q1 supersession
  precedent at `spec.md:389-392`; the original Cycle 3 wording is
  preserved verbatim per immutability; Step 8ae re-renders the
  corrected wording in the spec body. Any FR-072 mirror at
  `spec.md:3651-3653` (or other propagation sites) using the
  superseded wording MUST be reconciled in the same Step 8ae pass
  [Spec, Consistency, `spec.md:3899-3906` + `spec.md:3944-3950`]
- [ ] CHK206 **MEDIUM A4-02 / GitHub backlog issue filed** — a single
  GitHub issue MUST be filed with title prefix `[backlog]` (e.g.
  `[backlog] Cosmos data-plane RBAC: per-partition-key scope (blocked
  on API ≥ 2024-08-15+)`); body cites A4-02 acceptance at
  `spec.md:3912`, the Bicep site at
  `infra/bicep/modules/cosmos-simulation-containers.bicep:316`, the
  Cosmos data-plane RBAC API version 2024-08-15 partition-key-scope
  constraint as the explicit blocker, and ADR-036-011 Alternative #6
  (separate Cosmos database, previously rejected); label `backlog` is
  applied **only if** the repo's labels inventory already contains it
  (no new label is created as a side-effect) [Docs, Acceptance Criteria,
  `spec.md:3912` + `spec.md:4159-4204`]

### 17. Cycle 4 new test surface — `test_sli_kql_runtime_validity.py` + `test_smoke_tenant_isolation.py` extension

- [ ] CHK207 New file `tests/contract/test_sli_kql_runtime_validity.py`
  MUST exist with a parametric pytest test over Z1–Z7 mirroring the
  shape at `tests/contract/test_sli_kql_canonical_match.py:37-40`
  (`@pytest.mark.parametrize("sli_id", [s["id"] for s in _SLI_DOC["slis"]])`)
  so the 7-id collection is structurally guaranteed and any future
  Z8/Z9 SLI added to `infra/observability/sli-kql.json` automatically
  participates [Test, Contract, `spec.md:3887` + `spec.md:4496-4501`]
- [ ] CHK208 The new test MUST consume canonical KQL strings via the
  already-landed `tests/contract/_kql_canonicaliser.py` public surface
  (`canonicalise_kql(text: str) -> str` and
  `canonical_kql_for_sli(sli_id: str, *, thresholds_path: Path | None = None) -> str`)
  — there is **no second canonicalisation surface**; the runtime-validity
  test inherits from the same source of truth as the byte-equality
  test [Test, Contract, `spec.md:3887` + `spec.md:4020-4023`]
- [ ] CHK209 The new test MUST maintain a **module-level static**
  base-table-column allowlist as a `dict` keyed by table name
  (`requests`, `customEvents`, `customMetrics`, `traces`) with **inline
  comments** identifying each column's origin under the Application
  Insights schema; the allowlist MUST NOT perform a remote schema
  lookup at test time (auditable, deterministic, no network dependency)
  [Test, Contract, `spec.md:4023-4026`]
- [ ] CHK210 The new test's walker MUST be top-down and stateful: it
  advances line-by-line through canonicalised KQL, populating an
  in-scope set with (i) every `let <name> = <expr>;` LHS, (ii) every
  `extend <name> = <expr>` LHS (one or more per `extend` clause), and
  (iii) every `summarize <agg>=... by <col>` aggregate-LHS where the
  LHS is a fresh symbol introduced by the `summarize`; bare column
  references in `where` / `project` / `summarize ... by` / `extend`
  RHS / `let` RHS resolve against the static allowlist, the in-scope
  set populated up to that line, or a `customDimensions["..."]` lookup
  [Test, Contract, `spec.md:4221-4240`]
- [ ] CHK211 The new test's failure messages MUST cite, in the failure
  body: (i) the SLI id (Z1–Z7), (ii) the unresolved column name, (iii)
  the line number within the canonicalised KQL, and (iv) the full
  canonicalised KQL string (for postmortem / forensic correlation
  under Constitution IV); the headline message MUST be the literal
  form `KQL Zn references undefined column '<name>' at line N — must
  extend from customDimensions first` [Test, Contract, `spec.md:3887`
  + `spec.md:4031-4042`]
- [ ] CHK212 The new test MUST **hard-fail** (NOT `pytest.skip`,
  `pytest.xfail`, or any `mark.skipif`) when a `union` cross-table
  clause is encountered in any SLI's KQL body, with the exact
  message *"union is not yet supported by the runtime validity walker
  — extend test_sli_kql_runtime_validity.py to support multi-table
  column resolution"*; treating `union` as an open-ended pass-through
  is **explicitly rejected** because it would re-introduce the
  symmetric-drift defect class A4-01 was filed to close
  [Test, Contract, Anti-pattern, `spec.md:4240-4255` +
  `spec.md:4272-4277`]
- [ ] CHK213 `tests/contract/test_smoke_tenant_isolation.py` extension
  MUST add the **REQUIRED** new function
  `test_smoke_role_assignment_scope_is_database_level` that asserts
  the `smokeCoordinatorRoleAssignment` resource block in
  `infra/bicep/modules/cosmos-simulation-containers.bicep` contains
  the literal scope-string `scope: '${account.id}/dbs/${databaseName}'`
  AND that no narrower `pks/${...}` per-partition-key suffix nor
  broader account-level scope appears; failure message cites
  `spec.md:3906` as the binding wording authority
  [Test, Acceptance Criteria, `spec.md:3911` + `spec.md:4707-4719`]
- [ ] CHK214 `tests/contract/test_smoke_tenant_isolation.py` extension
  MAY add the **OPTIONAL** new function
  `test_bicep_comment_block_documents_compensating_control` asserting
  the comment block at
  `infra/bicep/modules/cosmos-simulation-containers.bicep:305-315`
  contains the literal phrase `compensating defence-in-depth control`
  AND the GitHub backlog issue id citation (the placeholder substring
  `[backlog issue: TBD]` is permitted until the issue is filed and
  replaced atomically); whether assertion is taken is recorded at
  Step 8ae implementation time and drives the 3399 (REQUIRED only) vs
  3400 (REQUIRED + OPTIONAL) post-implement test count
  [Test, Acceptance Criteria, `spec.md:4720-4736` + `spec.md:4783-4795`]

### 18. Cycle 4 Pass-1 + Pass-2 clarification Q→A coverage

- [ ] CHK215 **Pass-1 Q1** (KQL parser scope) — resolution pins
  **lightweight regex/lexer** consuming canonical KQL via the existing
  `_kql_canonicaliser.py` helpers; a full Kusto AST parser dependency
  (`pykusto`, `kusto-parser-py`, shelling to `kustopreview`,
  `Microsoft.Azure.Kusto.Language` .NET bridge) is **explicitly
  rejected** for the same reasons Cycle 3 Pass-1 Q1 rejected AST
  equivalence: cross-runtime fragility, supply-chain attack surface,
  Linux GitHub-hosted runner posture, and the lean `pyproject.toml`
  test-surface convention [Spec, Clarity, `spec.md:3997-4062`]
- [ ] CHK216 **Pass-1 Q2 + Q5** (corrected-wording terminology + ADR
  pathway) — resolution pins **both** *"compensating defence-in-depth
  control"* AND inline backlog-issue citation as the binding A4-02
  wording (per NIST SP 800-160 + OWASP defence-in-depth taxonomy +
  PCI-DSS compensating-control lineage; the existing Bicep comment
  block at L305-315 already uses "compensating" language as
  in-repository precedent) AND pins **revise ADR-036-011 in place**
  with a "Cycle 4 amendment" sub-section (NOT a new ADR-036-012); the
  in-place revision is the binding pathway because Cycle 4 is a
  correction-of-Cycle-3-deliverables, not a new architectural decision
  [Spec, Clarity, `spec.md:4083-4157` + `spec.md:4288-4351`]
- [ ] CHK217 **Pass-1 Q3 + Q4** (backlog mechanism + walker discipline)
  — resolution pins **GitHub issue only** (no `docs/backlog/` markdown
  entry; no `.github/ISSUE_TEMPLATE/` directory) as the deferred
  Cosmos-RBAC-partition-scope tracking artefact AND pins the
  runtime-validity walker's `let`/`extend`/`summarize`-aggregate-LHS
  top-down in-scope tracking with `union` deferred via fail-fast
  message; an audit during Pass 1 confirmed zero `union` occurrences
  across Z1–Z7 in `infra/observability/sli-kql.json` so the deferral
  is risk-free for the Cycle 4 cohort [Spec, Clarity,
  `spec.md:4159-4218` + `spec.md:4219-4286`]
- [ ] CHK218 **Pass-2 Q1 + Q4** (test count math supersession chain) —
  resolution pins **3398** (3391 + 7 parametric ids) as the corrected
  count superseding Pass-1 Q1's **3392** figure, then Q4 **further
  supersedes** Q1's 3398 with **3399** (REQUIRED scope-string assertion
  only — minimal Step 8ae posture) or **3400** (REQUIRED + OPTIONAL
  comment-block assertion — full Step 8ae posture); live verification
  via `pytest --collect-only` confirmed 7-id parametric collection on
  the existing `test_sli_kql_canonical_match.py` template; Step 8ae
  records the chosen value (3399 or 3400) in `tasks.md`
  [Spec, Clarity, `spec.md:4427-4505` + `spec.md:4781-4795`]
- [ ] CHK219 **Pass-2 Q2** (CHANGELOG.md format precedent) —
  resolution pins **grouped sub-sections** under `## [Unreleased]`
  mirroring the Cycle 2 precedent at `CHANGELOG.md:7-31`: at minimum
  `### Added (spec 036 — Cycle 4 amendment cycle)` and
  `### Changed (spec 036 — Cycle 4 amendment cycle)` (no
  `### Breaking changes` because A4-01 + A4-02 are non-breaking); each
  bullet cites file:line evidence + inline `(A4-XX / FR-YYY)`
  provenance tags; the orchestrator-suggested single-bullet
  `- A4-XX <summary>` format is **rejected** as having zero in-repo
  precedent (verified: zero matches for `^- A\d+-\d+ ` pattern in
  `CHANGELOG.md`) [Spec, Clarity, `spec.md:4507-4593`]
- [ ] CHK220 **Pass-2 Q3** (multi-cycle ADR Status convergence rule) —
  resolution pins ADR-036-011 Status field stays `Proposed` until the
  *first* cohort re-review (Step 8al or any subsequent re-review) that
  returns `0 OBJECT votes AND 0 NEW merit-validated findings against
  ADR-036-011`; **no time-bound auto-flip**; rule is recorded inline
  within the Cycle 4 amendment sub-section per (i)–(v); recursive
  across Cycle 5 / Cycle 6 / ...; once `Accepted`, the Status never
  reverts (subsequent cycles append amendment sub-sections to an
  Accepted ADR rather than re-opening Status)
  [Spec, Clarity, Convergence, `spec.md:4595-4677`]

### 19. Anti-pattern rejection rows (Cycle 4 PR review gates)

- [ ] CHK221 **Anti-pattern: Kusto AST parser dependency** — any PR
  that lands `tests/contract/test_sli_kql_runtime_validity.py` with a
  Kusto AST / parser dependency (e.g. `pykusto`, `kusto-parser-py`,
  shelling to `kustopreview`, a managed-runtime bridge to
  `Microsoft.Azure.Kusto.Language`, or any third-party Kusto-aware
  package) added to `pyproject.toml`, `tests/contract/`, or any other
  test-surface MUST be rejected at code review; the binding
  pure-Python regex/lexer discipline from Pass-1 Q1 is mandatory and
  preserves the Cycle 3 Pass-1 Q1 "no Kusto runtime dependency"
  precedent [Anti-pattern, `spec.md:3894` + `spec.md:4002-4015`]
- [ ] CHK222 **Anti-pattern: skip on runtime-validity test** — any PR
  that lands `test_sli_kql_runtime_validity.py` with a
  `pytest.mark.xfail`, `pytest.mark.skip`, `pytest.mark.skipif`, or
  any conditional skip decorator on the parametric Z1–Z7 test (whole
  test or any individual SLI id) MUST be rejected at code review;
  the test MUST be **green at PR-merge time** for every declared SLI
  per Cycle 3 Pass-1 Q5 universal-scope contract surface
  [Anti-pattern, `spec.md:3892` + `spec.md:1185-1230`]
- [ ] CHK223 **Anti-pattern: ADR-036-012 created** — any PR that
  introduces a new file `docs/aidr/decisions/ADR-036-012-*.md` (or
  any `ADR-036-012` filename pattern) to record Cycle 4 amendments
  MUST be rejected; Cycle 4 is a correction-of-Cycle-3-deliverables
  per Pass-1 Q5 and MUST be folded into ADR-036-011 in place via a
  "Cycle 4 amendment" sub-section. The directory listing of
  `docs/aidr/decisions/` MUST show **no** ADR-036-012 file post-Cycle-4
  [Anti-pattern, `spec.md:4288-4351` + `spec.md:4349-4351`]
- [ ] CHK224 **Anti-pattern: docs/backlog/ or speculative ISSUE_TEMPLATE**
  — any PR that creates `docs/backlog/index.md`, `docs/backlog/`
  directory, `.github/ISSUE_TEMPLATE/` directory, or any backlog
  surface other than the GitHub issue mandated by Pass-1 Q3 MUST be
  rejected; the convention is **GitHub issues only** (verified absent
  in repo at Pass-1 time); a future cycle may introduce a
  `docs/backlog/` convention but doing so as a Cycle 4 side-effect
  breaches the Cycle 4 narrowness discipline at `spec.md:3838-3841`
  [Anti-pattern, `spec.md:4161-4192`]
- [ ] CHK225 **Anti-pattern: speculative backlog label creation** —
  any PR that creates a new GitHub label such as
  `backlog:cosmos-rbac-partition-scope` (or any label not pre-existing
  in the repo's labels inventory at Cycle 4 implement time) as a
  side-effect of filing the deferred-remediation issue MUST be
  rejected; Pass-1 Q3 binding wording specifies *"label `backlog` IF
  the repo's labels inventory already contains it, otherwise no
  label (don't create a new label as a side-effect of this filing)"*
  [Anti-pattern, `spec.md:4181-4183`]
- [ ] CHK226 **Anti-pattern: Cycle 4 amendment-log mutation post-specify**
  — any PR that modifies the Cycle 4 Amendment Log lines
  `spec.md:3830-3967` after the Cycle 4 specify pass closed at L3967
  MUST be rejected (within-cycle immutability discipline analogous to
  Cycle 2 Q1 supersession at `spec.md:389-392` and the Cycle 4
  immutability discipline at `spec.md:3947-3950`); the **only**
  permitted in-place mutation is updating the two `[NEEDS
  CLARIFICATION]` markers at L3894 (Q1) and L3914 (Q2) to
  `[CLARIFIED Cycle 4 Pass 1 Qn]` markers — already performed at the
  L4385 Pass 1 close — no further mutation of L3830-L3967 is
  permitted in Cycle 4 [Anti-pattern, `spec.md:3941-3942` +
  `spec.md:3894, 3914` + `spec.md:3947-3950`]

### 20. Constitution alignment + prior-cycle traceability + audit-envelope reference

- [ ] CHK227 **Constitution alignment** — A4-01 honours **Principle I**
  (Primacy of Life — SC-010 overlay-drift gate enforceability is
  restored on this code path because the runtime-validity test
  prevents the gate from being silenced by an undefined-column error)
  and **Principle V** (Graceful Degradation — predictable failure with
  explicit machine-readable indicator: an author-time KQL semantic
  error is surfaced at contract-test time, not at AppInsights query
  time during a live gate run). A4-02 honours **Principle IV**
  (Transparency and Auditability — self-documentation aligns with
  binding implementation; the corrected wording removes the
  misrepresentation, names the actual compensating defence-in-depth
  control, and acknowledges the API-version constraint as the
  explicit blocker for the deferred remediation)
  [Constitution, `spec.md:3955-3965`]
- [ ] CHK228 **Prior-cycle preservation + supersession ledger** —
  Cycle 1 amendments A–S, Cycle 2 amendments A2-01 → A2-08, and
  Cycle 3 amendments A3-01 → A3-06 remain in force unchanged; A4-02
  records the **single explicit supersession** of Cycle 3 Pass-1 Q2
  item (v) "Least-privilege test identity" wording at
  `spec.md:961-966` per the Cycle 2 Q1 supersession precedent at
  `spec.md:389-392`, with the original Cycle 3 wording preserved
  verbatim. The Cycle 3 baseline of **3391 tests pass / 0 fail** at
  `spec.md:3829` is preserved; the binding post-Cycle-4-implement
  total is **3399** (REQUIRED scope-string assertion only — minimal
  Step 8ae posture) or **3400** (REQUIRED + OPTIONAL comment-block
  assertion — full Step 8ae posture); 3392 / 3398 figures from
  Pass-1 Q1 / Pass-2 Q1 are superseded
  [Convergence, `spec.md:3853-3855` + `spec.md:3943-3950` +
  `spec.md:4783-4795`]
- [ ] CHK229 **§3.26 envelope schema unchanged + reachability restored**
  — the Cycle 3 §3.26 `staging_promotion.refused` audit-envelope
  schema in `contracts/audit-envelope.md` is **unchanged by Cycle 4**
  (Cycle 4 strengthens the gate that writes the envelope but does
  not modify the envelope schema, the typed-entry counter, or the
  §3.20–§3.24 gap-preservation invariant). A4-01's Z7 KQL fix
  ensures the gate-evaluation success path is reachable so the
  §3.26 envelope is written on REFUSED outcomes — this **closes
  the Pass-1 Q3 invariant gap** at `spec.md:3882`
  (*"`assert_sli_thresholds()` is never invoked → no
  `staging_promotion.refused` envelope is written → Pass-1 Q3
  invariant is broken"*) [Contract, Convergence, `spec.md:3882` +
  `spec.md:1029-1039`]

### 21. Convergence — Cycle 4 closure

- [ ] CHK230 **Cycle 4 sentinel chain** at end of `spec.md` records
  the four sequential gate states added in Cycle 4 (L3829 Cycle 3
  implement complete → L3967 Cycle 4 amendment specify complete →
  L4385 Cycle 4 clarify pass 1 complete → L4866 Cycle 4 clarify pass 2
  complete (CONVERGED)); the next sentinel ("Cycle 4 checklist
  complete (NN rows appended). Ready for /speckit.plan (Cycle 4).")
  is appended by this Step 8 checklist pass immediately after L4866,
  unblocking `/speckit.plan` (Cycle 4)
  [Convergence, `spec.md:3829, 3967, 4385, 4866`]

**Cycle 4 quality checklist locked. Ready for /speckit.plan (Cycle 4).**

## Cycle 5 Quality Checklist (post Step 8al cohort re-review amendments)

This section validates the **single** Cycle 5 amendment (A5-01), the
**seven** clarification Q→A entries (Cycle 5 Pass-1 Q1–Q3 + Cycle 5 Pass-2
Q1–Q4), and the propagation queue assembled by Steps 8aq / 8ar / 8at. Each
item carries a category tag in brackets and a `file:line` evidence
reference; gaps are tagged `[Gap]` and ambiguities `[Ambiguity]`. Cycle 1
(CHK001–CHK100), Cycle 2 (CHK101–CHK156), Cycle 3 (CHK157–CHK196), and
Cycle 4 (CHK197–CHK230) rows remain in force unchanged and are
out-of-scope for this section. Per the lock-zone constraint, no prior row
is modified. Cycle 5 is **narrower in scope** than Cycle 4: zero new FRs,
zero new SCs, zero FR strengthenings (pure DOC-FIX — Bicep comment-block
rewrite + one test-assertion extension + one OPTIONAL→REQUIRED prose
promotion); the F-TECH-4-01 defect surfaced by the Step 8al cohort
re-review (operational/sectors/technical triple) is closed by A5-01.

**Category legend**: Spec | Contract | Constitution | Test | Workflow | Docs | Bicep | Anti-pattern | Convergence

### 22. Cycle 5 amendment evidence in `spec.md` (A5-01)

- [ ] CHK231 **A5-01 Bicep preamble residue removal** — the consolidated
  comment block at `infra/bicep/modules/cosmos-simulation-containers.bicep:305-315`
  (consolidated with the Cycle 4 A4-02 sub-block at L317-327 per the
  Pass-1 Q1 binding ordering) MUST NOT contain the case-insensitive
  substrings `partition path`, `pks/<tenant_id>`, or
  `/colls/<container>/pks/`; the actual `scope:` expression at L328 MUST
  remain byte-identical to the Cycle 4 baseline
  `scope: '${account.id}/dbs/${databaseName}'` — A5-01 is
  documentation-only (no Bicep `scope:` change, no compiled-RBAC-behaviour
  change, no `pyproject.toml` change)
  [Bicep, Acceptance Criteria, `spec.md:4943` + `spec.md:4965-4968` +
  `spec.md:5117-5124`]
- [ ] CHK232 **Pass-1 Q1 ordering symmetry** — the rewritten preamble's
  top-down reading sequence MUST be (1) database-level scope statement
  citing `${account.id}/dbs/${databaseName}` as the narrowest scope
  supported by Cosmos data-plane RBAC API 2024-08-15; (2) compensating
  defence-in-depth control phrasing; (3) joint enforcement clauses
  naming the SLI-Z6/Z7 query-time `where tenant_id == "tnt-stg-smoke"`
  filter and the `customDimensions["tenant_id"]` envelope discriminator;
  (4) the `[backlog issue: #84]` citation. Symmetry is byte-identical
  in ordering to the three precedent anchors — ADR-036-011:172-184, the
  Cycle 4 A4-02 sub-block at `cosmos-simulation-containers.bicep:317-327`,
  and the F-TECH-4-01 recommended remediation — and is qualitatively
  verified by the Step 8au cohort re-review (not test-automatable)
  [Bicep, Spec, Pass-1 Q1, `spec.md:4969` + `spec.md:5067-5096`]

### 23. Cycle 5 test surface — `test_smoke_tenant_isolation.py` assertion extension + T-AA52 prose promotion

- [ ] CHK233 **Pass-2 Q1 OPTIONAL→REQUIRED prose promotion** — the
  docstring at `tests/contract/test_smoke_tenant_isolation.py:253` MUST
  be rewritten to record REQUIRED disposition (from the Cycle 4 text
  *"T-AA52 — OPTIONAL A4-02 evidence: Bicep comment block (L305-315).
  Cycle 4 FULL posture per Pass-2 Q4..."* to *"T-AA52 — REQUIRED A4-02
  evidence (promoted Cycle 5 Pass 2): Bicep comment block (L305-315).
  Single 3400 posture per Cycle 5 Pass 2 Q1; the minimal/FULL split
  established by Cycle 4 Pass 2 Q4 at `spec.md:4795-4801` is
  collapsed..."*), AND the header comment at
  `tests/contract/test_smoke_tenant_isolation.py:173` MUST be rewritten
  from `# Cycle 4 / T-AA51 (REQUIRED) + T-AA52 (OPTIONAL) — A4-02
  evidence tests` to `# Cycle 4 / T-AA51 (REQUIRED) + T-AA52 (REQUIRED
  — promoted Cycle 5 Pass 2 per spec.md A5-01) — A4-02 evidence tests`.
  No `pytest.mark.*` decorator is added or removed (runtime disposition
  is unchanged — the test was already collected unconditionally at
  Cycle 4 close per `tasks.md:2527`)
  [Test, Pass-2 Q1, `spec.md:5498-5586` + `spec.md:5616-5623`]
- [ ] CHK234 **Pass-2 Q2 case-folding primitive** — the two new absence
  assertions appended to
  `test_bicep_comment_block_documents_compensating_control` at
  `tests/contract/test_smoke_tenant_isolation.py:250-297` MUST be
  encoded **byte-identically** as
  `assert "pks/<tenant_id>" not in role_block.lower(), (...)` AND
  `assert "partition path" not in role_block.lower(), (...)` per the
  verbatim Python shown at `spec.md:5656-5673`. The
  `re.compile(..., re.IGNORECASE)` + `.search` alternative offered in
  Pass 1 Q2 at `spec.md:5184-5191` and the `str.casefold()` alternative
  are **explicitly rejected**; the `.lower()` + plain `in` shape is
  symmetric with the existing `tnt-prod` absence precedent at
  `tests/contract/test_smoke_tenant_isolation.py:166`
  [Test, Anti-pattern, Pass-2 Q2, `spec.md:5650-5754` +
  `spec.md:5656-5673`]
- [ ] CHK235 **Pass-1 Q2 pre-existing presence assertions preserved**
  — the two existing presence assertions in
  `test_bicep_comment_block_documents_compensating_control` —
  (i) the `compensating defence-in-depth` phrase presence assertion at
  `tests/contract/test_smoke_tenant_isolation.py:271-282` and (ii) the
  backlog-issue identifier presence assertion at
  `tests/contract/test_smoke_tenant_isolation.py:286-297` — MUST remain
  byte-identical (no modification to the existing
  `assert compensating_re.search(role_block)` / `assert
  backlog_re.search(role_block)` calls); the two new option-(b) absence
  assertions per Pass-1 Q2 + Pass-2 Q2 are **additive**, NOT
  replacements, and both consume the same
  `_extract_role_assignment_block(bicep_text)` helper per Pass-1 Q3
  [Test, Pass-1 Q2 + Q3, `spec.md:5234-5239` + `spec.md:5289-5292` +
  `spec.md:5301-5418`]

### 24. Cycle 5 Pass-2 Q3 test-count posture + Step 8at pytest gate

- [ ] CHK236 **Pass-2 Q3 single 3400 posture binding** — the
  post-Cycle-5-implement binding test count MUST be exactly **3400
  tests pass / 0 fail (single posture)**; the Cycle 4 Pass 2 Q4
  minimal-3399 / FULL-3400 split established at `spec.md:4795-4801` is
  **retired** by the Pass-2 Q1 REQUIRED promotion (the
  minimal-posture escape hatch is eliminated); Cycle 5 implement delta
  is **+0** (test extended in place with two new `assert ... not in
  role_block.lower()` statements; NO new `def test_*` function, NO
  parametrize-axis widening, NO new test file); Step 8at's
  `python -m pytest -q` gate MUST return returncode 0 AND
  collected-node count exactly **3400** with zero `skipped` / `xfailed`
  / `xpassed` qualifier for
  `test_bicep_comment_block_documents_compensating_control`
  [Test, Pass-2 Q3, `spec.md:5440-5444` + `spec.md:5776-5815`]

### 25. Cycle 5 propagation discipline — sentinels, ADR in-place revision, mirror immutability, CHANGELOG, backlog issue, ruff

- [ ] CHK237 **Spec sentinel chain preserved verbatim** — the twelve
  prior sentinel anchors at `spec.md:3829` (Cycle 3 implement
  complete), `spec.md:3967` (Cycle 4 amendment specify complete),
  `spec.md:4385` (Cycle 4 clarify Pass 1 complete), `spec.md:4866`
  (Cycle 4 clarify Pass 2 close), `spec.md:4868`, `spec.md:4870`,
  `spec.md:4871`, `spec.md:4873` (Cycle 4 Pass 2 supersession-ladder
  internal anchors), `spec.md:4886` (Cycle 4 implement complete — 3400
  FULL posture; backlog issue #84 filed), `spec.md:5035` (Cycle 5
  amendment log complete), `spec.md:5453` (Cycle 5 clarify Pass 1
  complete), and `spec.md:5994` (Cycle 5 clarify Pass 2 complete —
  CONVERGED) MUST remain byte-identical post-Cycle-5; only the Cycle 5
  checklist + plan + tasks + analyze + implement close sentinels are
  appended **after** L5994
  [Convergence, `spec.md:3829, 3967, 4385, 4866, 4868, 4870, 4871,
  4873, 4886, 5035, 5453, 5994`]
- [ ] CHK238 **ADR-036-011 in-place revision (no new ADR file)** —
  `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md`
  acquires a **Cycle 5 amendment sub-section** appended at Step 8aq
  (Cycle 5 plan), consistent with the Cycle 4 sub-section at L478+ per
  the Cycle 4 Pass-1 Q2/Q5 in-place revision pathway. The Cycle 5
  sub-section records: (a) the Bicep comment-block consolidation
  (Pass-1 Q1); (b) the assertion extension (Pass-1 Q2 + Q3 +
  Pass-2 Q2); (c) the T-AA52 OPTIONAL→REQUIRED promotion
  (Pass-2 Q1); (d) the dispositional collapse to single 3400 posture
  (Pass-2 Q3); (e) the convergence-rule restatement (Pass-2 Q4). The
  ADR-036-011 binding wording at :172-184 is **NOT re-amended**
  (out-of-scope per `spec.md:4979`); the ADR Status field remains
  `Proposed` post-Step-8aq and is flipped to `Accepted` only by the
  Step 8au close commit on clean cohort re-review. Creating a new ADR
  file (`docs/aidr/decisions/ADR-036-012-*.md`) is rejected — Cycle 5
  is a correction-of-Cycle-4-deliverables, not a new architectural
  decision
  [Docs, Convergence, Anti-pattern, `spec.md:4976` +
  `spec.md:5631-5641` + `spec.md:5863-5897`]
- [ ] CHK239 **LOW-1 within-cycle mirror immutability** — the four
  Cycle 4 sibling-artefact stale-mirror lines at `plan.md:682`,
  `tasks.md:1929`, `quality.md:367`, and `quality.md:528` MUST **NOT**
  be edited in Cycle 5 (those mirrors were already annotated as
  *"known-stale per A4-02 supersession"* via the Cycle 4 strikethrough
  block at `spec.md:961-970` under the LOW-1 within-cycle immutability
  discipline); any re-rendering of those four lines as a Cycle 5
  side-effect is rejected as a scope-creep violation against the
  Cycle 5 narrowness discipline
  [Convergence, Anti-pattern, `spec.md:4933-4937` + `spec.md:4982`]
- [ ] CHK240 **CHANGELOG.md Cycle 5 close-block format** — the
  `CHANGELOG.md` Cycle 5 close block (appended at Step 8at close) MUST
  mirror the Cycle 4 Pass 2 Q2 grouped-sub-section format precedent
  recorded at `CHANGELOG.md:7-15`: at minimum
  `### Added (spec 036 — Cycle 5 amendment cycle)` and
  `### Changed (spec 036 — Cycle 5 amendment cycle)` sub-sections
  under the existing `## [Unreleased]` heading (no
  `### Breaking changes` because A5-01 is non-breaking); each bullet
  cites `file:line` evidence + inline `(A5-01)` provenance tag. The
  single-bullet `- A5-01 <summary>` format remains rejected per the
  Cycle 4 Pass 2 Q2 ruling
  [Docs, Pass-2 Q1 propagation, `spec.md:5642-5646` +
  `spec.md:5848-5853`]
- [ ] CHK241 **Backlog issue #84 remains open and cited** — GitHub
  backlog issue **#84** (`Cosmos RBAC partition-scope upgrade`) filed
  at Cycle 4 implement close per `spec.md:4886` MUST remain **open**
  at Cycle 5 close and MUST be cited verbatim in (a) the rewritten
  Bicep preamble at `cosmos-simulation-containers.bicep:305-315` per
  Pass-1 Q1 ordering element (4) — `[backlog issue: #84]`; and (b) the
  ADR-036-011 Cycle 5 sub-section appended at Step 8aq. No new backlog
  issue is filed for Cycle 5 (A5-01 **closes** the F-TECH-4-01 defect
  rather than deferring it); the `backlog` label policy from Cycle 4
  Pass-1 Q3 is unchanged
  [Docs, `spec.md:4886` + `spec.md:4943` + `spec.md:4968-4969`]
- [ ] CHK242 **Ruff cleanliness post-Cycle-5** — after Step 8at
  (Cycle 5 implement), `python -m ruff check apps tests packages` MUST
  exit with returncode 0 and zero findings, preserving the Cycle 4
  post-implement clean state certified at `spec.md:4886`. The two new
  `assert ... not in role_block.lower()` lines, the docstring +
  header-comment prose rewrites at `test_smoke_tenant_isolation.py:173,
  253`, and the Bicep comment-block rewrite at
  `cosmos-simulation-containers.bicep:305-315` MUST NOT introduce any
  ruff rule violation (line-length E501, line-continuation, unused
  import, etc.)
  [Test, Workflow, `spec.md:4886`]

### 26. Anti-pattern rejection rows (Cycle 5 PR review gates)

- [ ] CHK243 **Anti-pattern: skip/xfail/skipif on T-AA52** — any PR
  that lands the Cycle 5 T-AA52 prose promotion at
  `tests/contract/test_smoke_tenant_isolation.py:173, 253` AND
  introduces a `pytest.mark.skip`, `pytest.mark.xfail`,
  `pytest.mark.skipif`, or any conditional skip decorator on
  `test_bicep_comment_block_documents_compensating_control` MUST be
  rejected at code review — the Pass-2 Q1 REQUIRED promotion is
  prose-only (the test was already collected unconditionally at
  Cycle 4); introducing a runtime gate would contradict the REQUIRED
  label and would re-introduce the OPTIONAL signal-disposition gap
  F-TECH-4-01 demonstrated as inadequate, defeating the Cycle 5
  remediation intent
  [Anti-pattern, Test, `spec.md:5513-5523` + `spec.md:5546-5550`]

### 27. Convergence — Cycle 5 closure

- [ ] CHK244 **Cycle 5 sentinel chain + multi-cycle ADR Status
  convergence rule** — the Cycle 5 sentinel chain at end of `spec.md`
  records the three sequential gate states added in Cycle 5: L5035
  (Cycle 5 amendment log complete → Pass 1 unblocked) → L5453 (Cycle 5
  clarify Pass 1 complete → Pass 2 unblocked) → L5994 (Cycle 5 clarify
  Pass 2 complete — CONVERGED → checklist unblocked); the next
  sentinel — *"Cycle 5 checklist complete. Ready for /speckit.plan
  (Cycle 5)."* — is appended by this Step 8ap checklist pass
  immediately after L5994, unblocking `/speckit.plan` (Cycle 5). The
  Cycle 4 Pass 2 Q3 multi-cycle ADR-036-011 `Proposed → Accepted`
  convergence rule restated verbatim at Cycle 5 Pass 2 Q4
  (`spec.md:5863-5897`) MUST be applied by the Step 8au cohort
  re-review with substitutions `Step 8al → Step 8au` and
  `Cycle 4 → Cycle 5`: on Step 8au verdict of `0 OBJECT votes AND
  0 NEW merit-validated findings against ADR-036-011`, the ADR Status
  flips `Proposed → Accepted` in the same close commit and Step 9
  deploy unlocks; otherwise Cycle 6 opens
  [Convergence, Pass-2 Q4, `spec.md:5035, 5453, 5994` +
  `spec.md:5863-5897`]

**Cycle 5 quality checklist complete. Ready for /speckit.plan (Cycle 5).**
