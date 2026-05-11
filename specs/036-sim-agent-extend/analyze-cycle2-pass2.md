# Cycle 2 Cross-Artefact Analyze (Pass 2)

**Date**: 2026-05-10 · **Branch**: `036-sim-agent-extend` · **Mode**: post-harmonisation re-verification · **Scope**: Cycle 2 amendments (A2-01 → A2-08) + clarifications (Pass 1 Q1–Q5, Pass 2 Q1–Q5) — closure check on the 3 HIGH findings raised by pass 1 and detection of any drift introduced by the harmonisation.

**Pass-1 baseline**: `specs/036-sim-agent-extend/analyze-cycle2-pass1.md` (verdict 🟡 YELLOW, 0 CRITICAL / 3 HIGH / 2 MEDIUM / 2 LOW).

**Artefacts loaded** (post-harmonisation, byte-pinned):

| Artefact | Bytes | Lines | SHA-256 (truncated) |
|----------|------:|------:|---------------------|
| `specs/036-sim-agent-extend/spec.md` | 246,336 | 2,809 | `BBF2B8F2…2C81` |
| `specs/036-sim-agent-extend/contracts/audit-envelope.md` | 46,203 | 741 | `6728AED8…61F8` |
| `specs/036-sim-agent-extend/tasks.md` | 151,154 | 1,698 | `4B511353…100A` |
| `specs/036-sim-agent-extend/plan.md` | (unchanged) | 760 | (unchanged from pass 1) |
| `specs/036-sim-agent-extend/data-model.md` | (unchanged) | 1,091 | (unchanged from pass 1) |
| `specs/036-sim-agent-extend/checklists/quality.md` | (unchanged) | (unchanged) | (unchanged from pass 1) |
| `specs/036-sim-agent-extend/contracts/error-responses.md` | (unchanged) | (unchanged) | (unchanged from pass 1) |
| `specs/036-sim-agent-extend/contracts/sli-thresholds.md` | (unchanged) | (unchanged) | (unchanged from pass 1) |

**Closing sentinels intact**:

- `spec.md:2809` — *“Cycle 2 clarify pass 2 complete. Ready for /speckit.checklist.”* ✅
- `audit-envelope.md:741` — Cycle 2 lock sentinel ✅
- `tasks.md:1698` — *“§24 Cycle 2 task block locked. Ready for /speckit.analyze.”* ✅

---

## a. Verdict (headline)

| Verdict | Reason |
|--------:|--------|
| 🟡 **YELLOW — proceed to `/speckit.implement`; residual issues are advisory-only** | All **3 pass-1 HIGH findings are CLOSED** at all 5–6 cited sites. The byte-equality invariant (Cycle 2 Pass-1 Q1) is now consistently expressed at every binding site (`spec.md:131` + `spec.md:134` blockquote + `spec.md:248-277` Q1 ruling + `spec.md:2625-2634` FR-067 binding bullet 1 + `audit-envelope.md:629-642` §3.25 schema + `audit-envelope.md:667` §3.25 acceptance bullet 3 + `tasks.md:1470` T-AA14 description). The `trigger_source` enum partition (4-value `injection.success` vs 2-value `signal_pipeline.dispatch_failed`) is consistently expressed in `audit-envelope.md:151` (§3.2 schema), `audit-envelope.md:637` (§3.25 schema), `audit-envelope.md:720` (§6.2 table — narrowed with explicit “`primary` does NOT appear in `injection.success`” caveat), and `data-model.md:1066-1072`. Coverage matrices remain 100 %; constitution invariants remain 100 %. **However**: the +2-line shift of the Pass-1 Q1 ruling (was `L246-275`, now `L248-277`) was not propagated to three back-reference sites (`spec.md:445`, `quality.md:71`, `tasks.md:1481`), and the pass-1 carry-overs (MED-01, MED-02, LOW-01) remain unchanged. None of these are substantive contradictions; they are advisory line-number staleness. Step 8r `/speckit.implement` may proceed; recommended cleanup is a 4-line micro-edit follow-up (or absorption into the first Step 8r-touching PR). |

---

## b. Findings by severity

| Severity | Count | Δ vs pass 1 |
|---------:|------:|------------:|
| 🔴 CRITICAL | **0** | — |
| 🟠 HIGH | **0** | **−3** ✅ |
| 🟡 MEDIUM | **2** | unchanged (carry-overs from pass 1: MED-01, MED-02) |
| 🟢 LOW | **4** | **+2** (3 new line-shift drifts; LOW-02 from pass 1 remained resolved; LOW-01 from pass 1 still carries) |
| **Total** | **6** | −1 |

---

## c. Top 3 highest-severity items (post-harmonisation)

> No HIGH or CRITICAL items remain. The three highest-severity items are MEDIUM × 2 (carried unchanged from pass 1) and LOW × 1 (highest-impact new finding from this pass). All listed items are non-blocking for `/speckit.implement`.

### 🟡 MED-01 (CARRY) — `plan.md` task-ID renumbering not retroactively reflected

- **Locations**: `plan.md:676-712` (§C2.4) cites **T-AA01 … T-AA12** (12 tasks); `tasks.md:1342-1698` (§24) instantiates **T-AA07 … T-AA22** (16 tasks).
- **Why MEDIUM (not HIGH)**: documented and reconciled by the `tasks.md:1346-1366` §24.1 mapping table; binding ID set is `T-AA07 … T-AA22` per §24 lock at `tasks.md:1698`. Carried unchanged from pass 1 (RECOMMENDED, not MANDATORY).
- **Remediation hint** (deferred): add a 2-line annotation footer to `plan.md` §C2.4 pointing at `tasks.md:1346-1366`; do NOT renumber (§24 is byte-locked).

### 🟡 MED-02 (CARRY) — `cascade_rules.yaml` `fan_out_rules:` line range varies between artefacts

- **Locations**: `spec.md:152` cites lines **32-53**; `tasks.md:1537` (T-AA20 Files) cites lines **17-55**; `spec.md:338` (Pass-1 Q3 evidence pointer) cites lines **22-55**; `plan.md:570` (verified earlier) cites lines **17-55**. Direct inspection of `apps/api/app/config/cascade_rules.yaml:22` confirms `fan_out_rules:` starts at line **22** (`ladder:` at L8, `cap: 5` at L15, blank L16-21, `fan_out_rules:` at L22).
- **Why MEDIUM (not HIGH)**: T-AA20's wider range (17-55) is a safe over-removal that includes blank lines either side; the implementer can grep `fan_out_rules:` to find the exact start (line 22). No risk of partial removal.
- **Remediation hint** (deferred): pin all three references to **22-55** during Step 8r when the `fan_out_rules:` block is removed; spec.md:152 is narrative evidence, can stay at 32-53 (the meaningful payload).

### 🟢 LOW-PASS2-01 (NEW) — Pass-1 Q1 line-number back-references not updated post-harmonisation shift

- **Root cause**: the L134 blockquote insertion shifted the Pass-1 Q1 ruling from `L246-275` → `L248-277` (+2 lines). Three back-reference sites still cite `L246-275`.
- **Locations**:
  - `spec.md:445` — *“…and pass-1 Q1 (spec.md:246-275) collectively define a 3-value `dispatch_status` enum…”* (inside Pass-2 Q1 question text)
  - `checklists/quality.md:71` — *“[Spec, Clarity, `spec.md:246-275`]”* (CHK109 evidence pointer)
  - `tasks.md:1481` — *“pass-1 Q1 byte-equality (lines 246-275)”* (T-AA15 Acceptance bullet)
- **Why LOW**: line-number drift of −2 lines. Implementer following the citation lands on `spec.md:246` (which is mid-paragraph in the Pass-1 clarification preamble) and the **Q1 ruling header** at `spec.md:248` is one scroll-stop away. The binding semantics are unaffected — Q1 is unique and unmistakable. No substantive risk.
- **Remediation hint**: 3-site sed-replace `246-275` → `248-277`. Doc-only, can land in the same Step 8r PR or as a separate 3-line micro-PR.

---

## d. Coverage matrix (re-stated; identical to pass 1)

| Amendment | Severity | Spec FR/SC | Plan §C2.x | Data-model §11.x | Contract | Quality CHK | Cycle 2 Task(s) | Coverage % |
|-----------|---------:|------------|-----------|-------------------|----------|-------------|-----------------|-----------:|
| **A2-01** | HIGH | FR-067 (L2621-2654 *post-harmonisation; was L2619-2647 pre*) + FR-009/FR-015 STRENGTHEN | §C2.1 A2-01 (L540-551) + §C2.5 risk #3 | §11.1, §11.2, §11.3, §11.6 | audit-envelope.md §3.25 + §1 enum bump + closing 25 | CHK103, CHK109, CHK114, CHK129, CHK132, CHK139, CHK140, CHK141, CHK147 | T-AA07, T-AA08, T-AA12, T-AA13, T-AA14, T-AA22 (6) | **100 %** |
| **A2-02** | HIGH | SC-013 (L2791-2803 *post +6 shift; was L2785-2797 pre*) + FR-063 STRENGTHEN | §C2.1 A2-02 (L553-565) | n/a | sli-thresholds.md §1 rows 6-7 + §6a/§6b + §7.3 + §7.4 | CHK107, CHK110, CHK117, CHK123, CHK124, CHK130, CHK137, CHK143, CHK145, CHK148 | T-AA16, T-AA17, T-AA18, T-AA19 (4) | **100 %** |
| **A2-03** | MEDIUM | FR-068 (L2655-2671) | §C2.1 A2-03 | n/a | n/a (canonical matrix in `sim_cascade_matrix.py`) | CHK104, CHK111, CHK131, CHK134, CHK143, CHK146, CHK149 | T-AA20 (1) | **100 %** |
| **A2-04** | MEDIUM | FR-069 (L2673-2683) | §C2.1 A2-04 | §11.2, §11.3 | audit-envelope.md §3.2 (`triggered_sub_agents` required) | CHK105, CHK109, CHK119, CHK135, CHK140, CHK150 | T-AA09, T-AA15 (2) | **100 %** |
| **A2-05** | MEDIUM | RECONCILE (no new FR) | §C2.1 A2-05 | n/a | error-responses.md §1 + §4 + §6 + §7 | CHK113, CHK118, CHK122, CHK132, CHK138, CHK151 | T-AA11 (1) | **100 %** |
| **A2-06** | LOW | FR-048 STRENGTHEN | §C2.1 A2-06 | §11.4 | audit-envelope.md §3.9 | CHK152 | T-AA21 (1) | **100 %** |
| **A2-07** | LOW | FR-070 (L2685-2697) | §C2.1 A2-07 | §11.2 (PascalCase Literal) | audit-envelope.md §3.2 line 150 enum + §3.25 line 636 enum + §6.2 row 722 | CHK106, CHK121, CHK126, CHK136, CHK141, CHK144, CHK153 | T-AA10 (1) | **100 %** |
| **A2-08** | LOW | folded into FR-067 | §C2.1 A2-08 | §11.3 (`signal_pipeline.dispatch_failed`) | audit-envelope.md §3.25 (NEW) | CHK120, CHK154 | folded into T-AA14 | **100 %** |

**Amendment coverage**: **8 / 8 = 100 %** (unchanged from pass 1).

### Pass-1 + Pass-2 clarification coverage

| Q | Topic | Spec | Plan | Data-model | Contract | Task(s) | CHK |
|---|-------|------|------|------------|----------|---------|-----|
| **P1-Q1** | Body↔audit byte-equality (RFC 8785 JCS) | spec.md:**248-277** *(post-harmonisation; was 246-275)* | §C2.1 A2-01 + §C2.5 risk #1 | §11.1, §11.2 | audit-envelope.md §3.2 + §3.25 + §6.3 + acceptance bullet 3 (L667) | T-AA14 (`test_dispatch_failed_body_audit_byte_equality.py`), T-AA15 | CHK109 |
| **P1-Q2** | 24 h staging-evidence freshness | spec.md:**279-302** *(was 277-300)* | §C2.1 A2-02 | n/a | sli-thresholds.md §6a + §6b + §7.3 | T-AA16, T-AA17 | CHK110 |
| **P1-Q3** | Remove YAML `fan_out_rules:` + alias | spec.md:**304-339** *(was 302-337)* | §C2.1 A2-03 | n/a | (canonical matrix in `sim_cascade_matrix.py`) | T-AA20 | CHK111, CHK131, CHK134, CHK143, CHK146 |
| **P1-Q4** | Per-subscriber `correlation_id` + lex order | spec.md:**341-376** *(was 339-374)* | §C2.1 A2-01 + A2-04 | §11.2 | audit-envelope.md §3.2 + §3.25 + §6.3 | T-AA13, T-AA14 | CHK112, CHK140 |
| **P1-Q5** | `SPEC_036_PROBLEM_JSON_ROUTES` allow-list | spec.md:**378-414** *(was 376-412)* | §C2.1 A2-05 | n/a | error-responses.md §7 | T-AA11 | CHK113, CHK122, CHK138 |
| **P2-Q1** | 3-value `dispatch_status` + 5 s timeout | spec.md:**443-482** *(was 441-480)* | §C2.1 A2-01 | §11.1, §11.2, §11.3 | audit-envelope.md §3.2 line 153 + §3.25 line 639 + line 656 | T-AA08, T-AA13, T-AA14 | CHK114 |
| **P2-Q2** | Always-present `degraded_dispatch: bool = False` | spec.md:**484-522** *(was 482-520)* | §C2.1 A2-01 | §11.1, §11.3 | audit-envelope.md §3.25 line 655 (`const true` invariant) | T-AA07, T-AA08 | CHK115, CHK139 |
| **P2-Q3** | Hybrid OTel TraceContext + customDimensions | spec.md:**524-577** *(was 522-575)* | §C2.1 A2-01 | §11.3 | audit-envelope.md §6.3 | T-AA13 | CHK116 |
| **P2-Q4** | `MIN_SAMPLES_PER_SLI_24H = 30` | spec.md:**579-625** *(was 577-623)* | §C2.1 A2-02 + §C2.5 risk #2 | n/a | sli-thresholds.md §6a + §6b + §7.3 | T-AA17, T-AA19 | CHK117, CHK137, CHK145 |
| **P2-Q5** | Allow-list gates 4xx + 5xx | spec.md:**627-672** *(was 625-670)* | §C2.1 A2-05 | n/a | error-responses.md §4 + §7 | T-AA11 | CHK118, CHK138 |

**Clarification coverage**: **10 / 10 = 100 %**. Line-number columns updated for the +2 shift after the L134 blockquote (Q1) and the +6 cumulative shift after the FR-067 binding expansion (everything past current L2625).

### Quality checklist coverage (CHK101–CHK156)

- All **56** items remain cited in at least one of: (a) Cycle 2 task acceptance bullet, (b) plan.md §C2.5/§C2.6, (c) spec.md amendment narrative.
- CHK109 wording re-verified post-harmonisation: *“Pass-1 Q1 resolution (FR-067↔FR-069 byte-equality of HTTP body and audit envelope's `triggered_sub_agents` arrays, RFC 8785 JCS canonical) is recorded in spec body and supersedes FR-067's earlier `acknowledged`-only wording”* — **aligns with the post-harmonisation T-AA14 wording at `tasks.md:1470`** ✅. The CHK109 evidence pointer cites a stale line range (see LOW-PASS2-02 below) but the binding text matches.
- CHK135 wording re-verified: *“FR-069 has unit (audit-details-dict builder), integration (byte-equality assertion between response body and audit envelope under RFC 8785 JCS), and contract (audit-envelope §3.2 schema regeneration) targets identified”* — **aligns with T-AA15 at `tasks.md:1480` (which says `injection.success` audit envelope's array is byte-equal to the HTTP 202 response body's array after RFC 8785 JCS canonicalisation)** ✅.
- **Quality CHK coverage**: **56 / 56 = 100 %** (unchanged from pass 1).

---

## e. Closure verification of pass-1 HIGH-01 / HIGH-02 / HIGH-03 *(NEW for pass 2)*

### ✅ HIGH-01 CLOSED — `triggered_sub_agents` shape on fully-failed dispatch

| Site | Pre (pass-1 quote) | Post (pass-2 verified) | Closed? |
|------|--------------------|------------------------|--------|
| `spec.md:131` | *“…`triggered_sub_agents=[]`…”* | *“…`triggered_sub_agents` populated with **one entry per attempted subscriber** (all `dispatch_status` ∈ `{"failed", "timed_out"}` on full failure). *(Updated by Cycle 2 Pass-1 Q1 — see ‘Clarifications (Cycle 2 — Pass 1) → Q1’ at L248-277 below; supersedes the original ‘`triggered_sub_agents=[]`’ wording.)*”* | ✅ |
| `spec.md:2625-2634` (FR-067 binding bullet 1) | *“partial-successful subset (each entry tagged `dispatch_status: \"acknowledged\"`)”* | *“`triggered_sub_agents` populated with **one entry per attempted subscriber**. Each entry MUST carry `dispatch_status` ∈ `{"acknowledged", "failed", "timed_out"}`. *(Updated by Cycle 2 Pass-1 Q1 at L248-277: the response body's `triggered_sub_agents` array MUST be byte-equal — after RFC 8785 JCS canonicalisation — to the `signal_pipeline.dispatch_failed` audit envelope's array; this supersedes the original FR-067 wording…)*”* | ✅ |
| `audit-envelope.md:667` (§3.25 acceptance bullet 3) | *“…with `triggered_sub_agents=[]`”* | *“…with `triggered_sub_agents` populated with **one entry per attempted subscriber** (all `dispatch_status` ∈ `{failed, timed_out}`), per the §3.25 schema and Cycle 2 Pass-1 Q1 byte-equality with the audit envelope's array”* | ✅ |
| `audit-envelope.md:629-642` (§3.25 schema lock zone) | *“Contains ONE entry per attempted subscriber”* | *“Contains ONE entry per attempted subscriber”* (byte-identical pre/post — preserved by Wave-1 instructions) | ✅ (preserved) |
| `tasks.md:1470` (T-AA14 Description) | *“the body still carries `degraded_dispatch=true` with `triggered_sub_agents=[]` populated by failed/timed_out entries”* (internally contradictory) | *“populate `triggered_sub_agents` with the **full** attempted-subscriber set — **one entry per attempted subscriber** (lexicographically ordered by PascalCase `sub_agent` per pass-1 Q4) — including failed and timed-out entries; … write exactly one `signal_pipeline.dispatch_failed` envelope per `injection_correlation_id` with the byte-equal array (per Cycle 2 pass-1 Q1, spec.md L248-277); … On a fully-failed dispatch (zero acknowledged subscribers), `injection.success` is **NOT** emitted; only `signal_pipeline.dispatch_failed` is written and the body still carries `degraded_dispatch=true` with `triggered_sub_agents` populated by one entry per attempted subscriber (all `dispatch_status` ∈ `{"failed", "timed_out"}` on full failure).”* | ✅ |
| `spec.md:248-277` (Pass-1 Q1 ruling, byte-equality decision) | *“Body and audit are structurally identical (FR-069 prevails)…ONE entry per attempted subscriber with `dispatch_status` ∈ `{"acknowledged", "failed", "timed_out"}`; the `signal_pipeline.dispatch_failed` audit envelope's `triggered_sub_agents` array MUST be byte-equal (after RFC 8785 JCS canonicalisation)…”* | unchanged content; shifted +2 lines (was L246-275) | ✅ (preserved) |

**HIGH-01 closure verdict**: **CLOSED** ✅. All 6 cited sites now consistently say “one entry per attempted subscriber” (or, for the canonical schema sites, “ONE entry per attempted subscriber”). The pre-harmonisation `triggered_sub_agents=[]` wording is gone from every binding site; where the legacy `[]` reference is retained (e.g. the silent-swallow paragraph at `spec.md:2646-2648`), it is correctly framed as the **PROHIBITED** silent-swallow behaviour, not the binding shape.

### ✅ HIGH-02 CLOSED — FR-067 binding text now points at Pass-1 Q1

| Site | Closure evidence |
|------|------------------|
| `spec.md:2625-2634` (FR-067 binding bullet 1) | Inline parenthetical at L2628-2632: *“(Updated by Cycle 2 Pass-1 Q1 at L248-277: the response body's `triggered_sub_agents` array MUST be byte-equal — after RFC 8785 JCS canonicalisation — to the `signal_pipeline.dispatch_failed` audit envelope's array; this supersedes the original FR-067 wording that listed only `\"acknowledged\"` entries in the body.)”* — ✅ explicit pass-1 Q1 supersedure citation + RFC 8785 JCS reference. |
| `spec.md:134` (new Markdown blockquote) | *“**Cycle 2 Pass-1 Q1 supersedure**: the body-vs-audit shape of `triggered_sub_agents` is determined by Cycle 2 Pass-1 Q1 (L248-277), which mandates byte-equality between the HTTP 202 body and the `signal_pipeline.dispatch_failed` audit envelope. Any \"acknowledged-only\" wording above is interpreted as the partial-successful **derivable view** — the binding shape is \"one entry per attempted subscriber\".”* — ✅ forward-reference covers the entire A2-01 narrative (L121-L132), including the L127 narrative paragraph that retains legacy “acknowledged” wording. |
| `spec.md:127` (FR-067 narrative — locked Cycle 2 spec) | Narrative still reads *“each entry tagged `dispatch_status: \"acknowledged\"`”* but is **explicitly covered** by the L134 blockquote (which says *“Any 'acknowledged-only' wording above is interpreted as the partial-successful **derivable view**”*). The blockquote is positioned between A2-01 and A2-02 so that the “above” reference unambiguously scopes the entire A2-01 subsection. ✅ Pass-1 finding HIGH-02's residual concern (FR-067 narrative L127 not re-worded) is mitigated by the forward-reference rather than by re-writing the locked spec — which is the exact remediation pass-1 recommended (option a). |

**HIGH-02 closure verdict**: **CLOSED** ✅. The FR-067 binding text at `spec.md:2625-2634` now explicitly cites Pass-1 Q1 with line-number anchor + RFC 8785 JCS canonicalisation rationale; the L134 blockquote forward-reference closes the gap to the L127 narrative “acknowledged” wording without re-opening the locked spec. The `spec.md:414` Pass-1 resolution rollup line (*“Q1 → updates FR-067 wording”*) now resolves to a real edit at L2628.

### ✅ HIGH-03 CLOSED — `trigger_source` enum partition

| Site | Pre (pass-1 quote) | Post (pass-2 verified) | Closed? |
|------|--------------------|------------------------|--------|
| `audit-envelope.md:151` (§3.2 `injection.success` schema) | 5-value `["primary", "cascade", "subscriber", "controller_intent", "lifecycle"]` | 4-value `["subscriber", "controller_intent", "cascade", "lifecycle"]` (NO `primary`); description: *“This is the `injection.success` 4-value enum (Cycle 1 invariant retained). The Cycle 2 narrower pair `{primary, cascade}` is **exclusive to** the new §3.25 `signal_pipeline.dispatch_failed` envelope (see line 637) per data-model.md §11.5; `primary` does NOT appear in `injection.success`.”* | ✅ |
| `audit-envelope.md:637` (§3.25 schema) | 2-value `["primary", "cascade"]` | 2-value `["primary", "cascade"]` (UNCHANGED — exclusive home of `primary`) | ✅ (preserved) |
| `audit-envelope.md:720` (§6.2 field-additions table) | 5-value `subscriber \| controller_intent \| cascade \| lifecycle \| primary` | 4-value `subscriber \| controller_intent \| cascade \| lifecycle` with annotation *“(Cycle 2 pass-1 Q4 narrows the `{primary, cascade}` pair to §3.25 `signal_pipeline.dispatch_failed` only — see line 637 — so `primary` does NOT appear in `injection.success`)”* | ✅ |
| `data-model.md:1066-1072` (§11.5) | 4-value retained for `injection.success`; 2-value for `signal_pipeline.dispatch_failed` | unchanged (already correct in pass 1) | ✅ (preserved) |

**HIGH-03 closure verdict**: **CLOSED** ✅. The contract↔data-model drift is resolved: `audit-envelope.md` §3.2 narrowed to 4-value, §3.25 retained at 2-value, §6.2 narrowed with explicit cross-reference to §3.25 line 637 as the exclusive home of `primary`. All four sites now agree, and the contract test (`tests/contract/test_audit_envelope_schema_2020_12.py` per T-AA12) will validate the partition correctly.

---

## f. New findings introduced by harmonisation *(NEW for pass 2)*

### 🟢 LOW-PASS2-01 (NEW) — Stale `L246-275` back-reference at `spec.md:445`

- **Where**: inside the Pass-2 Q1 question text (the question itself, not a binding clause): *“…and pass-1 Q1 (spec.md:246-275) collectively define a 3-value `dispatch_status` enum…”*
- **Severity**: 🟢 LOW. The Pass-1 Q1 ruling shifted from `L246-275` → `L248-277` after the L134 blockquote insertion. A reader following the citation lands on `spec.md:246` (mid-paragraph in the “Clarifications (Cycle 2 — Pass 1)” preamble) and the **Q1 header** is one scroll-stop away at L248. No substantive risk; semantics unaffected.
- **Remediation**: 1 sed-replace in `spec.md:445` from `246-275` → `248-277`.
- **Note**: this is a NEW drift introduced by harmonisation (the L134 blockquote shifted Q1 by +2).

### 🟢 LOW-PASS2-02 (NEW) — Stale `spec.md:246-275` back-reference at `quality.md:71`

- **Where**: CHK109 evidence pointer: *“[Spec, Clarity, `spec.md:246-275`]”*.
- **Severity**: 🟢 LOW. Same root cause as LOW-PASS2-01. CHK109's binding wording (the body-↔-audit byte-equality assertion) is correct; only the cited line range is off by 2.
- **Remediation**: 1 sed-replace in `quality.md:71` from `246-275` → `248-277`.

### 🟢 LOW-PASS2-03 (NEW) — Stale `lines 246-275` back-reference at `tasks.md:1481`

- **Where**: T-AA15 Acceptance bullet: *“…+ pass-1 Q1 byte-equality (lines 246-275)”*.
- **Severity**: 🟢 LOW. Same root cause. T-AA15's binding semantics (byte-equality + RFC 8785 JCS at the audit-write path) are correct; only the cited line range is stale.
- **Remediation**: 1 sed-replace in `tasks.md:1481` from `lines 246-275` → `lines 248-277`. Note: T-AA14 at `tasks.md:1470` correctly cites `spec.md L248-277` post-harmonisation, so the new wording at T-AA14 is not affected; only T-AA15's pre-existing reference needs updating.

### 🟢 LOW-PASS2-CARRY (carried from pass-1 LOW-01) — `plan.md:531` finding count drift

- **Where**: `plan.md:531` says *“**2 HIGH + 4 MEDIUM + 3 LOW** merit-validated findings”*; spec.md / tasks.md / quality.md / synthesis all say **2 HIGH + 3 MEDIUM + 3 LOW**.
- **Severity**: 🟢 LOW (cosmetic count drift; unchanged from pass 1).
- **Status**: NOT addressed by Wave-1 harmonisation (pass-1 classified as RECOMMENDED, not MANDATORY).
- **Remediation**: 1 edit in `plan.md:531` from `4 MEDIUM` → `3 MEDIUM`, OR add parenthetical *“(plus 1 deferred MEDIUM A2-S1 — maritime/coastal/aviation outside spec-036 hazard set)”*.

### Cross-checks for byte-equality invariant consistency *(no new findings)*

The Cycle 2 Pass-1 Q1 byte-equality invariant relies on consistent expression at four sites. Verified post-harmonisation:

| Site | Wording check | Status |
|------|--------------|--------|
| `spec.md:248-277` (Pass-1 Q1 ruling) | *“The HTTP 202 response body's `triggered_sub_agents` array MUST contain ONE entry per attempted subscriber with `dispatch_status` ∈ `{"acknowledged", "failed", "timed_out"}`; the `signal_pipeline.dispatch_failed` audit envelope's `triggered_sub_agents` array MUST be byte-equal (after RFC 8785 JCS canonicalisation, consistent with Cycle 1 pass-1 Q3 idempotency body-hashing) to the response body's array.”* | ✅ |
| `audit-envelope.md:629-642` (§3.25 schema description) | *“Cycle 2 pass-1 Q1 — byte-equal (after RFC 8785 JCS canonicalisation) to the HTTP 202 response body's `triggered_sub_agents` array. Ordered lexicographically by `sub_agent` PascalCase enum value (Cycle 2 pass-1 Q4). Contains ONE entry per attempted subscriber.”* | ✅ |
| `audit-envelope.md:667` (§3.25 acceptance bullet 3) | *“…the response body still carries `degraded_dispatch=true` with `triggered_sub_agents` populated with **one entry per attempted subscriber** (all `dispatch_status` ∈ `{failed, timed_out}`), per the §3.25 schema and Cycle 2 Pass-1 Q1 byte-equality with the audit envelope's array.”* | ✅ |
| `tasks.md:1470` (T-AA14 Description) | *“…write exactly one `signal_pipeline.dispatch_failed` envelope per `injection_correlation_id` with the byte-equal array (per Cycle 2 pass-1 Q1, spec.md L248-277)…”* | ✅ |

**Byte-equality invariant consistency**: ✅ all four sites agree.

### T-AA14 ↔ T-AA15 internal-consistency check *(no new findings)*

- `tasks.md:1470` (T-AA14) commits the orchestrator + route handler to populate the array with “one entry per attempted subscriber” + emit exactly one `signal_pipeline.dispatch_failed` envelope per `injection_correlation_id` with a byte-equal array.
- `tasks.md:1480` (T-AA15) asserts byte-equality between `injection.success` audit envelope's array and the HTTP 202 response body's array after RFC 8785 JCS canonicalisation. *(Note: T-AA15 covers the **success** path; T-AA14 covers the **dispatch-failed** path. Both paths are gated by the same byte-equality invariant.)*

The T-AA14 wording does NOT contradict T-AA15: T-AA14's array is the dispatch-failed envelope's array (byte-equal to the body); T-AA15's array is the `injection.success` envelope's array (byte-equal to the same body — which means by transitivity both audit arrays are byte-equal to each other ON THE INTERSECTION of cases where both envelopes write, which is empty per FR-067 acceptance bullet 3 “the `injection.success` envelope is NOT emitted on a fully-failed dispatch”). The two tasks are mutually consistent. ✅

### Audit-envelope §3.2 ↔ §3.25 enum-partition consistency *(no new findings)*

- `audit-envelope.md:151` description explicitly cross-references §3.25 line 637 as the exclusive home of `primary`.
- `audit-envelope.md:637` description does not over-claim — it scopes the 2-value enum to “Cycle 2 dispatch entries” only.
- `audit-envelope.md:720` (§6.2 row) annotates the partition correctly.
- No third site references both enums simultaneously without the partition annotation. ✅

### Quality CHK109 + CHK135 ↔ tasks.md L1470 + L1480 alignment *(no new findings)*

- CHK109 (`quality.md:68-71`): *“Pass-1 Q1 resolution (FR-067↔FR-069 byte-equality of HTTP body and audit envelope's `triggered_sub_agents` arrays, RFC 8785 JCS canonical) is recorded in spec body and supersedes FR-067's earlier `acknowledged`-only wording”* — aligns with the new T-AA14 wording at `tasks.md:1470` ✅. (Evidence pointer at `quality.md:71` is stale per LOW-PASS2-02 but the binding text is correct.)
- CHK135 (`quality.md:182-185`): *“FR-069 has unit (audit-details-dict builder), integration (byte-equality assertion between response body and audit envelope under RFC 8785 JCS), and contract (audit-envelope §3.2 schema regeneration) targets identified”* — aligns with T-AA15 at `tasks.md:1480` ✅.

---

## g. Constitution invariant matrix (12 invariants — re-verified)

| Invariant | Cycle 2 status | Pass-2 verification |
|-----------|---------------|---------------------|
| **I. Primacy of Life** | ✅ PASS | A2-01 honours via predictable-failure surface; A2-02 gates SC-001 + SC-010 on Z6/Z7 with ≥30-sample CLT floor. Harmonisation did not alter life-safety surfaces; the byte-equality fix actually **improves** forensic-recoverability (single-stream JOIN). |
| **II-A. AIIMS alignment** | ✅ PASS | FR-070 9-name PascalCase enum still aligns with `aiims_mapping.py`. Harmonisation did not touch AIIMS surfaces. |
| **III. Multi-hazard / multi-agency** | ✅ PASS | Cycle 2 changes remain agency-agnostic. Unchanged. |
| **IV. Transparency / Auditability** | ✅ PASS | A2-01 + A2-04 are direct improvements; the post-harmonisation byte-equality wording at all 4 sites strengthens this further (single-stream forensic reconstruction is now unambiguous in the contract). |
| **V (Graceful Degradation)** + **V-A (AWS three-tier)** | ✅ PASS | A2-01 remains the canonical Constitution V example; AWS palette unchanged. |
| **AU residency** | ✅ PASS | Z6/Z7 KQL queries still target staging Application Insights (`env == "staging"`); audit writes still land in `simulation_audit_entries` (australiaeast). Unchanged. |
| **HITL (NN-1)** | ✅ PASS | Coordinator surface (HTTP 202 with `degraded_dispatch=true`) preserves partial situational awareness — and now the surface ALSO includes failed/timed-out entries (richer SA), which is a strict improvement over the pre-harmonisation `[]`-shape. |
| **AVM-first (NN-4 / VIII)** | ✅ PASS | T-AA10 + T-AA18 reuse existing AVM modules. Unchanged. |
| **3-Container-App cap (NN-4 / VIII)** | ✅ PASS | No new container apps. Unchanged. |
| **Interoperability (NN-4)** | ✅ PASS | OpenAPI v0.3.0 BREAKING bump still documented. The post-harmonisation `trigger_source` enum partition (4-value `injection.success` + 2-value `signal_pipeline.dispatch_failed`) is now consistently expressed in the contract (closes pass-1 HIGH-03). |
| **Privacy by design (NN-3)** | ✅ PASS | `exception_message` field still PII-scrubbed with `maxLength: 1000`. Unchanged. |
| **Graceful degradation (NN-5)** | ✅ PASS | Canonical Constitution V example. Unchanged. |

**Constitution check**: ✅ **PASS** (12 / 12 = 100 %, unchanged from pass 1).

---

## h. Caller next-step recommendation

🟡 **YELLOW — proceed to `/speckit.implement` (Step 8r)**.

### Rationale

1. All 3 pass-1 HIGH findings are **closed** at every cited binding site. The byte-equality invariant (Pass-1 Q1) is now consistently expressed at 4 / 4 sites. The `trigger_source` enum partition is correctly expressed at 4 / 4 sites.
2. Coverage matrices remain 100 % (8 / 8 amendments, 10 / 10 clarifications, 56 / 56 quality checks).
3. Constitution invariants remain 100 % (12 / 12).
4. No HIGH or MEDIUM regressions or new HIGH/MEDIUM/CRITICAL items introduced by the harmonisation.
5. Three NEW LOWs are stale line-number references (`L246-275` → should be `L248-277`) at non-binding citation sites; one carry-over LOW (plan.md:531 finding count) and two carry-over MEDIUMs (plan.md task IDs, cascade YAML line range) are pre-existing and were never classified as MANDATORY in pass 1.

### Recommended Step 8r entry path

- **Path A (recommended)**: Proceed directly to `/speckit.implement`. Address the 4 LOWs as part of the first Step 8r-touching PR (single sed-replace `246-275` → `248-277` at the 3 stale sites + 1 plan.md count fix = 4 lines of churn). No re-analyze required after path-A cleanup.
- **Path B (optional)**: Run a tiny Cycle 3 micro-cleanup pass to fix the 4 LOWs first, then re-run `/speckit.analyze` for a 🟢 GREEN. Adds one round-trip but produces a cleaner pre-implementation baseline.
- **Path C (do nothing)**: Accept the 4 LOWs as advisory line-number staleness; the binding semantics at every cited line range are correct. Implementation proceeds; documentation will be cleaned up organically as Step 8s re-review touches the sites.

Path A is preferred: minimum incremental work, retains the Step 8r → Step 8s → Step 9 cadence, and folds doc cleanup into the natural Step 8r commit boundary.

### Step 8r entry preconditions (re-stated for clarity)

The Step 8r implementer SHOULD treat the following as the binding contract (priority order):

1. **(authoritative)** `spec.md:248-277` — Pass-1 Q1 ruling: body+audit byte-equal, ONE entry per attempted subscriber.
2. **(authoritative schema)** `audit-envelope.md:629-642` — §3.25 schema, lock zone preserved.
3. **(authoritative success path)** `audit-envelope.md:142-153` — §3.2 schema with 4-value `trigger_source` enum (no `primary`).
4. **(authoritative task)** `tasks.md:1470` — T-AA14 description with “full attempted-subscriber set” language.
5. **(authoritative test contract)** `tests/contract/test_dispatch_failed_body_audit_byte_equality.py` (T-AA14) + `tests/integration/test_injection_success_audit_triggered_sub_agents.py` (T-AA15) — byte-equality assertions.
6. **(authoritative quality gate)** `quality.md` CHK109 + CHK135 — byte-equality + JCS canonicalisation gates.

The 3 stale `L246-275` line-number references at `spec.md:445`, `quality.md:71`, and `tasks.md:1481` are advisory pointers to the same binding content (Pass-1 Q1 ruling, now at L248-277). The implementer is reminded that the binding content is the Q1 ruling itself, not the line-number pointer.

---

## Metrics summary

| Metric | Pass 1 | Pass 2 | Δ |
|--------|-------:|-------:|--:|
| CRITICAL findings | 0 | 0 | 0 |
| HIGH findings | 3 | **0** | **−3** ✅ |
| MEDIUM findings | 2 | 2 | 0 (carry) |
| LOW findings | 2 | 4 | +2 (3 new line-shift + 1 carry; LOW-02 from pass-1 stays resolved) |
| Total findings | 7 | 6 | −1 |
| Amendment coverage | 100 % | 100 % | 0 |
| Clarification Q→A coverage | 100 % | 100 % | 0 |
| Quality CHK coverage | 100 % | 100 % | 0 |
| Constitution invariant pass | 100 % | 100 % | 0 |
| Byte-equality consistent at 4 sites | n/a (was contradicted) | **✅** | **closed** |
| `trigger_source` enum partition consistent | n/a (was contradicted) | **✅** | **closed** |
| FR-067 binding text supersedure recorded | ❌ | **✅** | **closed** |

---

**Cycle 2 analyze pass 2 complete — verdict: 🟡 YELLOW.**

*Pass-1 HIGH-01, HIGH-02, HIGH-03 all CLOSED. Residual issues are 4 LOWs (3 new line-number-shift drifts at advisory citation sites + 1 pass-1 carry-over count drift) and 2 carry-over MEDIUMs (plan.md task IDs and cascade YAML line range) — none block `/speckit.implement`. Recommended next step: proceed to Step 8r (Path A — fold the 4-line cleanup into the first Step 8r-touching PR).*
