# Cycle 2 Cross-Artefact Analyze (Pass 1)

**Date**: 2026-05-09 · **Branch**: `036-sim-agent-extend` · **Mode**: pre-implement consistency check · **Scope**: Cycle 2 amendments (A2-01 → A2-08) + clarifications (Pass 1 Q1–Q5, Pass 2 Q1–Q5) ONLY (Cycle 1 content out-of-scope)

**Artefacts loaded**:

- `specs/036-sim-agent-extend/spec.md` (2,803 lines; Cycle 2 sections L86-685 + FR section L2619-2691 + SC section L2785-2797)
- `specs/036-sim-agent-extend/plan.md` (760 lines; §C2.1–§C2.6 at L528-756)
- `specs/036-sim-agent-extend/data-model.md` (1,091 lines; §11 at L905-1091)
- `specs/036-sim-agent-extend/tasks.md` (1,698 lines; §24 at L1342-1698)
- `specs/036-sim-agent-extend/contracts/audit-envelope.md` (entry-25 + Cycle 2 §3.2 update + closing-line counter)
- `specs/036-sim-agent-extend/contracts/error-responses.md` (§1 narrowing + new §7 allow-list)
- `specs/036-sim-agent-extend/contracts/sli-thresholds.md` (Z6 + Z7 + §7.3 staging gate)
- `specs/036-sim-agent-extend/checklists/quality.md` (CHK101–CHK156, all 56 items)
- `step-8i-synthesis.md` (Step 8i convergence + 9 merit-validated findings)
- `.specify/memory/constitution.md` (v1.2.0)

---

## A. Verdict (headline)

| Verdict | Reason |
|--------:|--------|
| 🟡 **YELLOW — proceed with explicit risk acceptance** | All 8 amendments have task coverage; all 10 clarification Q→A entries are reflected in spec/plan/contract/tasks; constitution invariants preserved; **but** 3 HIGH-severity doc-drift findings concentrated on a single root cause (the pre-Pass-1-Q1 "fully-failed dispatch ⇒ `triggered_sub_agents=[]`" wording was never re-aligned in spec.md FR-067 binding text, audit-envelope.md acceptance bullets, A2-01 acceptance criterion, or T-AA14 task body) WILL confuse implementers/reviewers in Step 8r unless harmonised before `/speckit.implement`. Implementation is technically unblocked — T-AA14 explicitly cites CHK109 ("Q1 byte-equality supersedes acknowledged-only wording") and audit-envelope.md §3.25 schema (the binding contract) says "ONE entry per attempted subscriber" — but the residual contradictory text creates a real risk a Step 8r reviewer will "fix" the implementation in the wrong direction. |

---

## B. Findings by severity

| Severity | Count |
|---------:|------:|
| 🔴 CRITICAL | **0** |
| 🟠 HIGH | **3** |
| 🟡 MEDIUM | **2** |
| 🟢 LOW | **2** |
| **Total** | **7** |

---

## C. Top 3 highest-severity findings (with `file:line` + remediation hint)

### 🟠 HIGH-01 — `triggered_sub_agents=[]` on fully-failed dispatch CONTRADICTS Pass-1 Q1 byte-equality + §3.25 schema "ONE entry per attempted subscriber"

- **Locations**:
  - `contracts/audit-envelope.md:667` (acceptance bullet) — *"…the response body still carries `degraded_dispatch=true` with `triggered_sub_agents=[]`"*
  - `contracts/audit-envelope.md:631` (§3.25 schema description) — *"Contains ONE entry per attempted subscriber"* (DIRECT contradiction with line 667 in the same document)
  - `spec.md:131` (A2-01 acceptance criterion) — same `triggered_sub_agents=[]` claim
  - `spec.md:2627-2628` (FR-067 binding text) — *"under degraded-dispatch, only `"acknowledged"` entries are listed in the response body"* (Pass-1 Q1 explicitly supersedes this at `spec.md:264-267` but FR-067 binding text was never re-worded; spec.md Cycle 2 is locked)
  - `tasks.md:1470` (T-AA14 description) — *"the body still carries `degraded_dispatch=true` with `triggered_sub_agents=[]` populated by failed/timed_out entries"* (internally contradictory: `[]` AND populated cannot both be true)
- **Why HIGH**: Pass-1 Q1 (`spec.md:246-275`) is the **deciding-authority resolution** that the body and audit are byte-equal with "ONE entry per attempted subscriber with `dispatch_status` ∈ `{acknowledged, failed, timed_out}`". A reviewer reading any of the four contradictory lines above without consulting Pass-1 Q1 will reach the wrong conclusion (filter body to `acknowledged`-only OR set body=`[]` on full failure). T-AA14 then asserts `json.dumps(body, sort_keys=True) == json.dumps(audit['details']['triggered_sub_agents'], sort_keys=True)` (`tasks.md:1473`) — the test will fail in the wrong direction depending on which paragraph the implementer follows.
- **Remediation hint** *(Step 8r pre-implement; non-spec-amendment; targeted text fixes only)*:
  1. Edit `contracts/audit-envelope.md:667` → *"…the response body carries `degraded_dispatch=true` and `triggered_sub_agents` populated with **ONE entry per attempted subscriber** (each `dispatch_status` ∈ {`failed`, `timed_out`} on a fully-failed dispatch)."*
  2. Edit `tasks.md:1470` (T-AA14 description) → remove `triggered_sub_agents=[]`; replace with *"the body still carries `degraded_dispatch=true` with `triggered_sub_agents` populated by ONE entry per attempted subscriber (`dispatch_status` ∈ {`failed`, `timed_out`} on a fully-failed dispatch)."*
  3. spec.md:131 + spec.md:2627-2628 are inside the locked Cycle 2 amendment scope — leave the text as-is BUT add a one-line "Superseded by Pass-1 Q1" inline note immediately after each instance, OR open a Cycle 3 micro-amendment to re-word in place. The first option is preferred to avoid re-opening the spec.

### 🟠 HIGH-02 — Pass-1 Q1 supersedure of FR-067 wording recorded in clarification but never propagated into FR-067 binding text or task descriptions

- **Locations**:
  - `spec.md:127` (FR-067 narrative) — *"each entry tagged `dispatch_status: \"acknowledged\"`"*
  - `spec.md:2619-2647` (FR-067 binding section) — line 2627 still says *"under degraded-dispatch, only `\"acknowledged\"` entries are listed in the response body"*
  - `spec.md:264-267` (Pass-1 Q1 resolution) — explicitly states *"FR-067's line-127 wording … is **superseded by this resolution** and will be re-worded in Step 8o"*
  - `spec.md:414` (Pass-1 resolution rollup) — *"Q1 → updates FR-067 wording"* (BUT the wording update never landed)
  - **No Cycle 2 task** in `tasks.md:1342-1698` re-words FR-067 (T-AA22 is ADR + CHANGELOG only; no spec.md edits)
- **Why HIGH**: A binding FR (FR-067) contains text that the same document declares "superseded" 23 sections earlier. Whether the supersedure is acceptable depends on policy: speckit.clarify treats clarifications as authoritative-by-recency, but a Step 8r reviewer reading FR-067 line-by-line is not guaranteed to scroll back to Pass-1 Q1 — the spec is 2,803 lines.
- **Remediation hint**: Either (a) accept the locked-spec convention and add a 1-line cross-reference at `spec.md:127` and `spec.md:2627-2628` ("⚠ Superseded by Pass-1 Q1 — see L246-275"), OR (b) open a Cycle 3 micro-amendment (Cycle 2 spec is currently locked at L2799 sentinel) to re-word in place. Option (a) is lighter-weight and preserves Cycle 2 lock invariants.

### 🟠 HIGH-03 — `trigger_source` enum drift between audit-envelope.md §3.2 and data-model.md §11.5

- **Locations**:
  - `contracts/audit-envelope.md:151` (§3.2 `injection.success` schema) — `"enum": ["primary", "cascade", "subscriber", "controller_intent", "lifecycle"]` (5-value)
  - `contracts/audit-envelope.md:720` (§6.2 amendment table) — *"enum `subscriber | controller_intent | cascade | lifecycle | primary`"* (5-value)
  - `data-model.md:1066-1070` (§11.5) — explicitly states *"The Cycle 1 four-value `trigger_source` enum (`subscriber | controller_intent | cascade | lifecycle`) is **retained unchanged** for `SubAgentInvocationRecord.trigger_source` (FR-026 dedup) and for the `injection.success` audit envelope's `triggered_sub_agents[].trigger_source`."* — i.e. `injection.success` is 4-value, NOT 5-value
  - `data-model.md:1066-1070` then says *"Cycle 2 introduces a **narrowed two-value enum** (`primary | cascade`) for the NEW `signal_pipeline.dispatch_failed` envelope's `triggered_sub_agents[].trigger_source`"* — confirms `primary` belongs only to `signal_pipeline.dispatch_failed`, NOT to `injection.success`
  - `contracts/audit-envelope.md:637` (§3.25 schema) — `"enum": ["primary", "cascade"]` for `signal_pipeline.dispatch_failed` ✅ matches data-model
- **Why HIGH**: The contract (audit-envelope.md §3.2) admits `primary` to `injection.success` but the data-model (§11.5) forbids it. Whichever document the contract test (`test_audit_envelope_schema_2020_12.py` per T-AA12) is generated from will be authoritative, and the other will be silently in drift. Forensic-replay JOINs across `injection.success` and `signal_pipeline.dispatch_failed` envelopes that key off `trigger_source` will misbehave at the boundary.
- **Remediation hint**: Pick ONE of:
  - **(a) Narrow audit-envelope.md §3.2** to 4-value `["subscriber", "controller_intent", "cascade", "lifecycle"]` (matches data-model §11.5; preserves Cycle 1 compatibility on `injection.success`); update §6.2 line 720 row accordingly.
  - **(b) Widen data-model.md §11.5** to allow `primary` on both envelopes (consistent 5-value union); requires tasks.md T-AA08 + T-AA09 to accept `primary` on `injection.success` writes too.
  - Option (a) is the conservative choice — Cycle 1 `injection.success` writes never used `primary`, and the new dispatch envelope is the natural home for `primary | cascade`.

---

## D. MEDIUM and LOW findings

### 🟡 MED-01 — Plan-to-tasks ID renumbering (T-AA01..T-AA12 → T-AA07..T-AA22)

- `plan.md:676-712` (§C2.4) refers to **T-AA01..T-AA12 (12 tasks)** but `tasks.md:1342-1698` (§24) instantiates **T-AA07..T-AA22 (16 tasks)**. The renumbering is documented in `tasks.md:1346-1366` (§24.1 mapping table), but plan.md was not retroactively updated.
- **Why MEDIUM (not HIGH)**: Documented and resolved in §24.1; `T-AA07..T-AA22` is the binding ID set per `tasks.md:1698` "Cycle 2 task block locked" sentinel. The 4 net-new tasks (T-AA12 Schemathesis, T-AA19 smoke-injection, T-AA22 ADR) are all justified expansions, not silent additions.
- **Remediation hint**: Add a 2-line annotation to plan.md §C2.4 footer pointing to `tasks.md` §24.1 for the canonical task IDs; do NOT rename because §24 is locked.

### 🟡 MED-02 — `cascade_rules.yaml` `fan_out_rules:` block line range varies between artefacts

- `spec.md:152` cites `apps/api/app/config/cascade_rules.yaml:32-53`
- `tasks.md:1537` (T-AA20) cites `cascade_rules.yaml` `fan_out_rules:` block at `lines 17-55`
- `plan.md:570` cites `lines 17-55`
- **Why MEDIUM**: Discrepant line ranges (32-53 vs 17-55) for the same YAML block. The implementation task references the wider range; spec uses the narrower. Could cause a partial-removal in Step 8r if the implementer trusts spec.md's narrower range.
- **Remediation hint**: Verify the actual YAML by `view`-ing `apps/api/app/config/cascade_rules.yaml` and pin the correct range in T-AA20; spec.md L152 evidence pin can stay (it's narrative, not binding).

### 🟢 LOW-01 — plan.md merit-validated finding count drifts from spec.md / tasks.md / synthesis

- `plan.md:531` — *"**2 HIGH + 4 MEDIUM + 3 LOW** merit-validated findings"*
- `spec.md:91-94`, `spec.md:97-104`, `tasks.md:1379-1386` (§24.2 severity legend), `quality.md:249-284` (CHK147–CHK156), `step-8i-synthesis.md:33-82` — all consistent with **2 HIGH + 3 MEDIUM + 3 LOW** (8 amendments — A2-01 HIGH, A2-02 HIGH, A2-03 MED, A2-04 MED, A2-05 MED, A2-06 LOW, A2-07 LOW, A2-08 LOW folded)
- **Why LOW**: plan.md likely counted the deferred sectors finding A2-S1 (maritime/coastal) — `step-8i-synthesis.md:63-65` records as "MEDIUM ❌ DEFERRED". Cosmetic count drift; no impact on amendment scope, task coverage, or constitution checks.
- **Remediation hint**: Edit `plan.md:531` to **"2 HIGH + 3 MEDIUM + 3 LOW"** OR add a parenthetical *"(plus 1 deferred MEDIUM A2-S1 — maritime/coastal/aviation outside spec-036 hazard set)"*.

### 🟢 LOW-02 — quality.md CHK156 wording "MEDIUM 24→8" matches Step-8i synthesis (`step-8i-synthesis.md:26`) but Cycle 2 only addresses 3 (A2-03/04/05); other 5 MEDIUMs are explicitly deferred at `spec.md:220-226` and CHK155

- **Why LOW**: Documented and reconciled — CHK155 captures the deferral. Verified consistent.

---

## E. Coverage matrix (amendments × artefacts × tasks)

| Amendment | Severity | Spec FR/SC | Plan §C2.x | Data-model §11.x | Contract | Quality CHK | Cycle 2 Task(s) | Coverage % |
|-----------|---------:|------------|-----------|-------------------|----------|-------------|-----------------|-----------:|
| **A2-01** | HIGH | FR-067 (L2619-2647) + FR-009/FR-015 STRENGTHEN | §C2.1 A2-01 (L540-551) + §C2.5 risk #3 (L722) | §11.1, §11.2, §11.3, §11.6 | audit-envelope.md §3.25 + §1 enum bump + closing 25 | CHK103, CHK109, CHK114, CHK129, CHK132, CHK139, CHK140, CHK141, CHK147 | T-AA07, T-AA08, T-AA12, T-AA13, T-AA14, T-AA22 (6) | **100 %** |
| **A2-02** | HIGH | SC-013 (L2785-2797) + FR-063 STRENGTHEN | §C2.1 A2-02 (L553-565) + §C2.5 risk #2 (L721) | n/a (no entity change) | sli-thresholds.md §1 rows 6-7 + §6a + §6b + §7.3 + §7.4 | CHK107, CHK110, CHK117, CHK123, CHK124, CHK130, CHK137, CHK143, CHK145, CHK148 | T-AA16, T-AA17, T-AA18, T-AA19 (4) | **100 %** |
| **A2-03** | MEDIUM | FR-068 (L2649-2665) | §C2.1 A2-03 (L567-576) | n/a (matrix is in `sim_cascade_matrix.py` already) | n/a (canonical matrix is already a contract via Cycle 1) | CHK104, CHK111, CHK131, CHK134, CHK143, CHK146, CHK149 | T-AA20 (1) | **100 %** |
| **A2-04** | MEDIUM | FR-069 (L2667-2677) | §C2.1 A2-04 (L578-587) | §11.2, §11.3 | audit-envelope.md §3.2 (`triggered_sub_agents` required) | CHK105, CHK109, CHK119, CHK135, CHK140, CHK150 | T-AA09, T-AA15 (2) | **100 %** |
| **A2-05** | MEDIUM | RECONCILE (no new FR; spec.md:171-181) | §C2.1 A2-05 (L589-598) | n/a | error-responses.md §1 line 9 + §4 + §6 + §7 (NEW allow-list) | CHK113, CHK118, CHK122, CHK132, CHK138, CHK151 | T-AA11 (1) | **100 %** |
| **A2-06** | LOW | FR-048 STRENGTHEN (no new FR text in §FR section — strengthened in narrative) | §C2.1 A2-06 (L600-608) | §11.4 | audit-envelope.md §3.9 (schema unchanged) | CHK152 | T-AA21 (1) | **100 %** |
| **A2-07** | LOW | FR-070 (L2679-2691) | §C2.1 A2-07 (L610-620) | §11.2 (PascalCase Literal) | audit-envelope.md §3.2 line 150 enum + §3.25 line 636 enum + §6.2 row 722 | CHK106, CHK121, CHK126, CHK136, CHK141, CHK144, CHK153 | T-AA10 (1) | **100 %** |
| **A2-08** | LOW | folded into FR-067 | §C2.1 A2-08 (L622-624) | §11.3 (`signal_pipeline.dispatch_failed`) | audit-envelope.md §3.25 (NEW) | CHK120, CHK154 | folded into T-AA14 | **100 %** |

**Amendment coverage**: **8 / 8 = 100 %**.

### Pass-1 + Pass-2 clarification coverage

| Q | Topic | Spec | Plan | Data-model | Contract | Task(s) | CHK |
|---|-------|------|------|------------|----------|---------|-----|
| **P1-Q1** | Body↔audit byte-equality (RFC 8785 JCS) | spec.md:246-275 | §C2.1 A2-01 + §C2.5 risk #1 | §11.1, §11.2 | audit-envelope.md §3.2 + §3.25 + §6.3 | T-AA14 (`test_dispatch_failed_body_audit_byte_equality.py`), T-AA15 | CHK109 |
| **P1-Q2** | 24 h staging-evidence freshness | spec.md:277-300 | §C2.1 A2-02 | n/a | sli-thresholds.md §6a + §6b + §7.3 | T-AA16, T-AA17 | CHK110 |
| **P1-Q3** | Remove YAML `fan_out_rules:` + alias | spec.md:302-337 | §C2.1 A2-03 | n/a | (canonical matrix in `sim_cascade_matrix.py`) | T-AA20 | CHK111, CHK131, CHK134, CHK143, CHK146 |
| **P1-Q4** | Per-subscriber `correlation_id` + lex order | spec.md:339-374 | §C2.1 A2-01 + A2-04 | §11.2 | audit-envelope.md §3.2 + §3.25 + §6.3 | T-AA13, T-AA14 | CHK112, CHK140 |
| **P1-Q5** | `SPEC_036_PROBLEM_JSON_ROUTES` allow-list | spec.md:376-412 | §C2.1 A2-05 | n/a | error-responses.md §7 | T-AA11 | CHK113, CHK122, CHK138 |
| **P2-Q1** | 3-value `dispatch_status` + 5 s timeout | spec.md:441-480 | §C2.1 A2-01 | §11.1, §11.2, §11.3 | audit-envelope.md §3.2 line 153 + §3.25 line 639 + line 656 | T-AA08, T-AA13, T-AA14 | CHK114 |
| **P2-Q2** | Always-present `degraded_dispatch: bool = False` | spec.md:482-520 | §C2.1 A2-01 | §11.1, §11.3 | audit-envelope.md §3.25 line 655 (`const true` invariant) | T-AA07, T-AA08 | CHK115, CHK139 |
| **P2-Q3** | Hybrid OTel TraceContext + customDimensions | spec.md:522-575 | §C2.1 A2-01 | §11.3 | audit-envelope.md §6.3 | T-AA13 | CHK116 |
| **P2-Q4** | `MIN_SAMPLES_PER_SLI_24H = 30` | spec.md:577-623 | §C2.1 A2-02 + §C2.5 risk #2 | n/a | sli-thresholds.md §6a + §6b + §7.3 | T-AA17, T-AA19 | CHK117, CHK137, CHK145 |
| **P2-Q5** | Allow-list gates 4xx + 5xx | spec.md:625-670 | §C2.1 A2-05 | n/a | error-responses.md §4 + §7 (4xx + 5xx scope) | T-AA11 | CHK118, CHK138 |

**Clarification coverage**: **10 / 10 = 100 %**.

### Quality checklist coverage (CHK101–CHK156)

- All **56** items are cited in at least one of: (a) Cycle 2 task acceptance bullet (`tasks.md:1379-1681`), (b) plan.md §C2.5/§C2.6, (c) the spec.md amendment narrative.
- Per `tasks.md:1681` ("**≥ 60 unique evidence anchors**") and §24.10 ("✅ Every Acceptance bullet cites at least one of: plan.md §C2.x, spec.md FR-067..070 / SC-013 / pass-1 Q1–Q5 / pass-2 Q1–Q5, contract delta, data-model.md §11.x, quality.md CHK1xx").
- **Quality CHK coverage**: **56 / 56 = 100 %**.

---

## F. Constitution invariant matrix (per plan.md §C2.6 + this analyze)

| Invariant | Cycle 2 status | Independent verification |
|-----------|---------------|-------------------------|
| **I. Primacy of Life** | ✅ A2-01 honours via predictable-failure surface (NOT silent-swallow); A2-02 gates SC-001 + SC-010 (life-safety) on Z6 + Z7 with ≥30-sample CLT floor | Verified — `degraded_dispatch=true` is an explicit machine-readable indicator (Constitution V example honoured per `spec.md:227-229`); no Cycle 2 amendment elevates dispatch-success reporting above life-safety messaging. Pass-1 Q1 + Q4 actually IMPROVE life-safety forensic-recoverability (single-stream JOIN, no parent→child correlation). |
| **II-A. AIIMS alignment** | ✅ FR-070 9-name PascalCase enum aligns with `aiims_mapping.py` canonical Literal | Verified — 9 names (`Risk`, `Evac`, `Resource`, `Logistics`, `Comms`, `Planning`, `Health`, `Operations`, `Intel`) are a **richer breakdown** of the 6 constitutional AIIMS functions, not a violation. `aiims_mapping.py:67-95` documents the mapping (e.g. *"Health → Operations (strike-team within Ops)"*, *"Risk → Planning (situation analysis)"*, *"Resource → Logistics"*). The user prompt referenced "Other" — verified `Other` is **NOT** in the 9-name list, so no AIIMS violation. |
| **III. Multi-hazard / multi-agency** | ✅ Cycle 2 changes are agency-agnostic; canonical cascade matrix covers all 5 cascade-source categories | Verified |
| **IV. Transparency / Auditability** | ✅ A2-01 + A2-04 are **direct improvements** (typed audit replaces silent-swallow; body↔audit byte-equality enables single-stream forensic reconstruction); A2-05 is a documentation correction (legacy envelope was always in use outside spec-036, contract overstated the surface). | Verified — see `plan.md:738` for the explicit ⚠ → ✅ rationale on A2-05. |
| **V (Graceful Degradation)** + **V-A (AWS three-tier)** | ✅ A2-01 is the canonical Constitution V example. Cycle 2 introduces **NO** new map markers — Z7 is a drift-budget SLI (latency, not warning-tier). AWS Advice/Watch-and-Act/Emergency-Warning palette unchanged. | Verified — `quality.md` CHK127 confirms no new AWS surface; `sli-thresholds.md` §6b Z7 measures `drift_ms` not warning tier. |
| **AU residency** | ✅ Z6/Z7 KQL queries target staging Application Insights (`env == "staging"`); audit writes land in `simulation_audit_entries` (australiaeast); no new model deployments | Verified — `sli-thresholds.md:237-238` filters `env == "staging"` and assumes staging App Insights is in australiaeast. Recommend `quality.md` CHK128 also assert AU-region staging workspace. |
| **HITL (NN-1)** | ✅ Coordinator surface (HTTP 202 with `degraded_dispatch=true`) preserves partial situational awareness; auto-degradation has clear notification path via the explicit boolean | Verified — `plan.md:742` explicitly cites NN-1 preservation. |
| **AVM-first (NN-4 / VIII)** | ✅ T-AA10 + T-AA18 reuse existing `avm/res/insights/action-group` modules; no new container apps; no new Cosmos containers | Verified — `tasks.md:1513-1518` (T-AA18) cites AVM module reuse; `data-model.md:1087` confirms no new Cosmos containers. |
| **3-Container-App cap (NN-4 / VIII)** | ✅ Cycle 2 introduces no new container apps (3 cap preserved: ca-api, ca-agents, ca-ingest); Pass-1 Q3 explicitly rationalises YAML removal against the 3-app cap (`spec.md:329-330`) | Verified |
| **Interoperability (NN-4)** | ✅ OpenAPI v0.3.0 BREAKING bump documented (data-model §11.6 + ADR-036-010 in T-AA22); RFC 9457 surface explicitly enumerated | Verified |
| **Privacy by design (NN-3)** | ✅ `exception_message` field on `signal_pipeline.dispatch_failed` is PII-scrubbed (`audit-envelope.md:628` `maxLength: 1000`); KQL queries surface no PII | Verified |
| **Graceful degradation (NN-5)** | ✅ Canonical Constitution V example (A2-01) | Verified |

**Constitution check**: ✅ **PASS** (consistent with `plan.md:750`).

---

## G. Convergence verdict + Step 8r preconditions

🟡 **YELLOW — proceed to /speckit.implement with explicit risk acceptance**

### Risks accepted for Step 8r

1. **HIGH-01 + HIGH-02 + HIGH-03 doc-drift** — Step 8r implementer MUST treat the following as the binding contract (in priority order):
   - **(1)** spec.md Pass-1 Q1 resolution (`spec.md:246-275`) — body+audit byte-equal, ONE entry per attempted subscriber
   - **(2)** audit-envelope.md §3.25 schema (the JSON-Schema contract, lines 611-661) — `triggered_sub_agents` "Contains ONE entry per attempted subscriber"
   - **(3)** quality.md CHK109 — *"Q1 byte-equality supersedes acknowledged-only wording"*
   - **(4)** data-model.md §11.5 — `injection.success` 4-value `trigger_source` enum vs `signal_pipeline.dispatch_failed` 2-value enum
   - The contradictory text in `spec.md:131`, `spec.md:2627-2628`, `audit-envelope.md:667`, `tasks.md:1470`, `audit-envelope.md:151` is **superseded** and MUST NOT be followed by the implementation.

### Step 8r preconditions (recommended micro-edits before `/speckit.implement`)

1. **(MANDATORY)** Edit `audit-envelope.md:667` to remove `triggered_sub_agents=[]` claim → replace with "ONE entry per attempted subscriber" wording aligned to §3.25 schema.
2. **(MANDATORY)** Edit `tasks.md:1470` (T-AA14 description) to remove the internally contradictory `[]`+populated wording.
3. **(MANDATORY)** Pick option (a) or (b) for HIGH-03 `trigger_source` enum drift; preferred = narrow audit-envelope.md §3.2 line 151 + §6.2 row 720 to 4-value to match data-model §11.5.
4. **(RECOMMENDED)** Add inline supersedure footnote at `spec.md:127` and `spec.md:2627-2628` pointing to Pass-1 Q1 (preserves Cycle 2 lock).
5. **(RECOMMENDED)** Fix `plan.md:531` count from "4 MEDIUM" → "3 MEDIUM" (LOW-01).
6. **(RECOMMENDED)** Verify `cascade_rules.yaml` actual line range and reconcile spec.md:152 / tasks.md:1537 / plan.md:570 (MED-02).

These 3 mandatory edits are **doc-only, no spec amendment, no code changes**, and should land in the same PR as the Cycle 2 implementation wave (or as a tiny precursor PR).

---

## H. Metrics summary

| Metric | Value |
|--------|------:|
| Cycle 2 amendments | 8 (A2-01 → A2-08) |
| Cycle 2 new FRs | 4 (FR-067, FR-068, FR-069, FR-070) |
| Cycle 2 new SCs | 1 (SC-013) |
| Cycle 2 strengthened FRs | 3 (FR-009/FR-015, FR-048, FR-063) |
| Cycle 2 reconciled contracts | 1 (error-responses.md A2-05) |
| Cycle 2 clarifications | 10 (Pass-1 Q1–Q5 + Pass-2 Q1–Q5) |
| Cycle 2 tasks | 16 (T-AA07..T-AA22; 10 [P]) |
| Cycle 2 NEW tests | 39 (9 unit + 12 integration + 9 contract + 4 e2e + 1 migration + 4 docs/devops) |
| Cycle 2 BREAKING-flagged tasks | 5 (T-AA07, T-AA08, T-AA14, T-AA20, T-AA22) |
| Cycle 2 ADRs added | 1 (ADR-036-010 via T-AA22) |
| Amendment coverage | **100 %** (8 / 8) |
| Clarification Q→A coverage | **100 %** (10 / 10) |
| Quality checklist coverage | **100 %** (56 / 56) |
| Constitution invariant pass | **100 %** (12 / 12) |
| Coverage matrix completeness | **100 %** |
| Findings (CRITICAL / HIGH / MEDIUM / LOW) | 0 / 3 / 2 / 2 |

---

**Cycle 2 analyze pass 1 complete — verdict: 🟡 YELLOW.**
