# Feature Specification: Web Application Capstone Coverage Validation

**Feature Branch**: `034-webapp-capstone-coverage`
**Created**: 2026-05-02
**Status**: Draft
**Input**: User description: "Web Application Capstone Coverage Validation — a re-runnable, persona-driven Playwright validation suite that proves the AMA web application (locally `http://127.0.0.1:3000/`) is sufficiently built to meet the `capstone.md` objectives across all 10 operational personas + 58 Australian sector/jurisdiction personas, plus uplift work to close any gaps the suite reveals."

## Background & Motivation

The capstone (`capstone.md`) commits the AMA platform to five operational outcomes — save 1,000+ lives annually, 50% faster response, 24-hour-earlier evacuations, 30% logistics efficiency improvement, 30% economic-loss reduction — delivered through an autonomous, multi-agent disaster-response coordination hub. Today the web application at `http://127.0.0.1:3000/` exposes route trees for `/disasters`, `/incidents`, `/governance`, `/operations`, `/preparedness`, `/simulations`, `/workspaces`, and `/eval`, but **no executable specification proves** that the UI's behaviour, role visibility, and audit/COP guarantees actually meet (a) the capstone's five outcomes, (b) the eleven AEMA principles plus AIIMS / AWS / PPRR / 5-stage evacuation / 4-recovery-environment / data-sovereignty / human-in-the-loop / auditability obligations recorded in `.specify/memory/constitution.md`, and (c) the task lists synthesised by the operational and sector agent inputs ([`operational-input.md`](#cited-inputs), [`sector-eastern-input.md`](#cited-inputs), [`sector-southwest-input.md`](#cited-inputs), [`sector-tc-input.md`](#cited-inputs)).

Without a persona-driven, re-runnable validation suite, capstone alignment is asserted in prose, never empirically verified; gaps surface only through ad-hoc demos and grading risk. This feature delivers (1) the suite as the executable specification of "the web app meets the capstone for every persona", (2) the uplift work needed for the suite to pass, and (3) a traceability artefact mapping persona requirement → capstone outcome → FR → Playwright test ID → web-app route → audit evidence. It explicitly defers Asia (PH/JP/BD) coverage per `028-capstone-alignment` and the constitution's Asia-deferral hypothesis.

### Cited inputs

- Operational personas (10): `operational-input.md` — Incident Commander, Operations Officer, Planning Officer, Logistics Officer, Public Information Officer, Field Coordinator, Resilience Planner, Executive Leader, Observer/Auditor, Risk Manager.
- Eastern jurisdictions (15): `sector-eastern-input.md` — NSW (FRNSW, MRNSW, NSW Ambulance, NSW RFS, NSWPF, SES-NSW), VIC (AV, CFA-VIC, FRV, SES-VIC, VicPol), QLD (QAS, QFD, QPS, SES-QLD).
- Southern/Western jurisdictions (12): `sector-southwest-input.md` — SA (SAAS, SACFS, SES-SA, SAMFS, SAPOL), WA (DFES-WA, SJA-WA, WAPOL), TAS (AT, SES-TAS, TasPol, TFS).
- Territories, Commonwealth, Cross-Sector (31): `sector-tc-input.md` — ACT (act-ambulance, act-esa, act-fr, act-policing, act-rfs, afp, ses-act); NT (bushfires-nt, ntes, ntfrs, ntpf, sja-nt); Commonwealth (abf, adf, afp-commonwealth, arc, asa, bom-national, ga-national, nema, rfds, sja-national, surf-lifesaving); Cross-Sector (community-ngos, health, local-government, state-government, territory-government, transport, utility, volunteer).

Total persona scope: **10 operational + 58 sector/jurisdiction = 68 personas.**

## Constitution Alignment Baseline

This feature treats the following constitution clauses as **non-negotiable** assertions the suite MUST verify on every run:

| Constitution clause | Verified by suite as |
| ------------------- | -------------------- |
| I. Primacy of Life | Every safety-critical action gated by human-in-the-loop approval (FR-009) |
| II. AEMA 11 principles | Persona scenarios exercise comprehensive/collaborative/coordinated/risk-based/integrated behaviours (FR-001 + FR-014) |
| II-A. AIIMS Functional Alignment | RBAC by AIIMS function + COP across functions (FR-007, FR-008) |
| III. Multi-Hazard, Multi-Agency | Bushfire, flood, cyclone, earthquake/tsunami, storm, heat scenarios cross persona suites (FR-016) |
| IV. Transparency and Auditability | Append-only audit timeline with rationale, confidence, source, operator identity, ≤ 2 s latency (FR-010) |
| V-A. Australian Warning System (AWS) three-tier | Advice / Watch and Act / Emergency Warning, nested model, hazard icons, de-escalation, all-clear (FR-011) |
| V-B. Ten Warning Principles | Warning drafts assert life-saving, scaled, targeted, accessible, with call-to-action (FR-011 + FR-014) |
| V-C. Total Warning System | Six elements (situational awareness → community response) traceable in suite (FR-011) |
| VI-A. Five-Stage Evacuation | Decision → Warning → Withdrawal → Shelter → Return actionable for relevant personas (FR-012) |
| VI-B. Evacuation types & approaches | Total / partial / phased + shelter-in-place + directed/recommended/self-initiated (FR-012) |
| VI-C. Vulnerable Populations | ATSI, CALD, disability, children, older persons, homeless, tourists, institutional care prioritised in evacuation flows (FR-012) |
| VII-A/B/C. Recovery | Four recovery environments (Social, Built, Economic, Natural) tracked + managed handover (FR-013) |
| PPRR Lifecycle | Prevention, Preparedness, Response, Recovery actionable from UI (FR-006) |
| NCM / NJCOP integration | Cross-jurisdiction COP + national escalation visible (FR-015) |
| Non-Negotiable #1: Human-in-the-loop | All safety-critical actions blocked without explicit approver identity (FR-009) |
| Non-Negotiable #2: Data sovereignty | AU-region badge / banner; Foundry model carve-out compliance signalled (FR-018) |
| Non-Negotiable #5: Graceful degradation | Field offline mode + sync-on-reconnect (FR-017) |
| Quality Gate: Public outputs human-reviewed | No alert publishes without IC approval (FR-009 + FR-011) |

## Clarifications — Session 2026-05-02 (pass 1)

These clarifications resolve high-impact ambiguities surfaced during the first `/speckit.clarify`
pass. Recommended answers were derived directly from the constitution (`.specify/memory/constitution.md` v1.2.0),
prior specs (`001`, `017`, `027`, `028`, `029`), the ADR series under `docs/aidr/decisions/`, and the
persona-need syntheses (`operational-input.md`, `sector-eastern-input.md`, `sector-southwest-input.md`,
`sector-tc-input.md`).

- **Q1: Are the parenthetical "operationally:" budgets in SC-001..SC-005 the contractual targets the suite
  asserts pass/fail, or guidance for `speckit.plan`?**
  → **A: Contractual.** SC-001 (≤ 2 min in-app + community-language reach after IC approval), SC-002
  (≤ 5 / 15 / 30 min signal-to-action for AIIMS Level 1 / 2 / 3), SC-003 (≥ 24 h evacuation lead vs seed
  reference), SC-004 (≤ 7 clicks routine, ≤ 12 clicks mutual-aid lifecycle) and SC-005 (≥ 30 %
  projected loss-reduction proxy on the post-handover Economic environment view) are now contractual
  operator-visible thresholds the suite asserts. Plan phase may tighten, never relax.
  *Sources: constitution §II-A AIIMS Levels 1/2/3, §IV Auditability ≤ 2 s; FR-010, FR-023(d); ASM-010.*

- **Q2: Which specific community languages MUST be in scope for FR-014 / SC-001 vulnerable-population
  coverage on AU territory?**
  → **A:** Baseline is **Simplified Chinese** (v1 CALD language pack inherited from
  `specs/001-disaster-response-hub/spec.md` NFR-013 / ASM-004), **plus an Aboriginal & Torres Strait
  Islander language placeholder rendered on at least one warning per hazard category** (per
  constitution §VI-C and `operational-input.md` PIO must-do "Localise into relevant languages incl.
  Aboriginal and Torres Strait Islander languages where needed"). Canonical BCP-47 identifier selection
  for any additional CALD or ATSI variants is **deferred to plan-phase `research.md`** per the
  precedent set in `specs/028-capstone-alignment/spec.md` clarification Q ("Defer — canonical
  identifier selection resolved in each owning spec's `research.md`"). Non-AU language packs (PH/JP/BD)
  remain deferred per OOS-001 and spec-028.
  *Sources: spec-001 NFR-013, ASM-004; spec-028 FR-006; constitution §VI-C; `operational-input.md` PIO.*

- **Q3: Is FR-018's Foundry carve-out requirement display-only, or does it also enforce
  data-minimisation at the model gateway (constitution NN#2)?**
  → **A: Display + gateway enforcement + registry currency (all three).** The suite must (a) assert
  the AU-region badge / banner on every route processing regulated platform data, (b) submit a
  synthetic PSPF-marked or PII-bearing payload through the platform model gateway and assert it is
  denied or masked before reaching any non-AU model-hosting endpoint, and (c) read the named
  carve-out registry (`infra/parameters/foundry-carveout.yaml` or its successor) and assert
  `review_date` is current (within 90 days) and `approver_identities[]` is non-empty.
  *Sources: constitution NN#2 §3 ("data-minimisation controls at the platform's model gateway");
  `docs/aidr/decisions/adr-033-phi-shadow-boundary.md` Layer 2 (three-classifier filter,
  deny-by-default); `docs/aidr/decisions/adr-032-oidc-supersession.md` (deploy-time carve-out
  enforcement restored); `specs/029-progressive-delivery-pipeline/spec.md` FR-018.*

- **Q4: Does the suite carry a numeric upper bound for CI consumability (SC-011 / FR-022 / FR-023)?**
  → **A: Yes — ≤ 30 min wall-clock on a developer machine and ≤ 45 min wall-clock on the CI gate
  runner (`ubuntu-latest` shape).** Without a numeric ceiling, FR-023's "act as a CI quality gate"
  cannot be enforced deterministically. If exceeded, the plan phase shards the suite across runners.
  *Sources: `specs/029-progressive-delivery-pipeline/spec.md` line 6 ("PR gates within 10 minutes" for
  the lighter unit/contract path implies a longer but capped e2e budget); `specs/017-cd-pipeline/spec.md`
  runner shape.*

- **Q5: For the US5 / FR-024 iteration loop, what is the maximum number of iterations before the gate
  escalates, and the rollback policy when a fix breaks an unrelated persona?**
  → **A:** **Maximum 3 iteration cycles per gap before escalation to the project lead** (constitution
  §Governance: "The project lead has final authority on architectural decisions"); each cycle is one
  (objection → spec amendment → re-implement → re-run) round. **On regression detection** (any
  previously-passing persona now failing), the gate stays `Not Ready`, the offending change is reverted
  to the prior known-good revision (per `specs/017-cd-pipeline/spec.md` FR-004 and
  `specs/029-progressive-delivery-pipeline/spec.md` FR-008), the gap register row carries a
  `regression_detected` flag, the original gap returns to `Open`, and the iteration counter is reset
  for that gap. Rollback evidence is captured for grading. (Codified in updated FR-024 + new FR-027.)
  *Sources: constitution §Governance; spec-017 FR-004; spec-029 FR-008; ASM-006.*

### Additional ambiguities resolved without separate questions

- **FR-021 / OOS-007 — fixture RBAC drift**: Tightened in new ASM-011 — fixture-impersonated personas
  inherit RBAC strictly from `bootstrap_seed_data()`'s identity registry; no fixture-only identities
  are permitted, so test impersonation cannot drift from real RBAC.
- **ASM-006 — 85-agent review mechanics**: Tightened — orchestration is owned by the US5 iteration
  loop runner; "meritorious" is decided by ≥ 2/3 majority of the agent panel; ties and final sign-off
  rest with the project lead per constitution §Governance.
- **HYP-002 — 30 % gap-uplift threshold**: Clarified as a *falsification trigger that re-scopes* (per
  `specs/027-spec-hardening/spec.md` FR-018 hypothesis format), **not** a hard suite-fail; if the
  threshold is crossed the AU-validated cohort still ships, and the un-validated routes/features spawn
  a follow-on uplift feature.

## Clarifications — Session 2026-05-02 (pass 2)

These clarifications close the five follow-ups carried forward from pass 1 and resolve four further
ambiguities surfaced during the second `/speckit.clarify` pass. After this pass the spec carries zero
known open ambiguities. Recommended answers were derived directly from the constitution
(`.specify/memory/constitution.md` v1.2.0), prior specs (`001`, `015`, `017`, `027`, `028`, `029`),
the ADR series under `docs/aidr/decisions/` (031, 032, 033-*, 034, 035, 036), the actor agent files
under `.github/agents/operational/` and `.github/agents/sectors/`, and the persona-need syntheses
(`operational-input.md`, `sector-eastern-input.md`, `sector-southwest-input.md`,
`sector-tc-input.md`).

### Pass-1 follow-ups closed

- **Q6: For US5, codify Given/When/Then acceptance scenarios covering (a) the 4th-cycle escalation
  path (FR-024 max-3-cycles → escalate to project lead) and (b) the regression-rollback path
  (FR-027 revert to prior known-good revision; gap → Open; iteration counter reset).**
  → **A: Codified.** Two new acceptance scenarios appended to User Story 5 (Acceptance Scenarios
  #3 and #4 — see § User Scenarios & Testing / User Story 5). Scenario #3 binds FR-024's 4th-cycle
  escalation: gap stays `Not Ready`, the row is tagged `escalated:project-lead`, the iteration
  counter for that gap is halted (no further automated cycles), and the project lead's disposition
  (override / re-baseline / abandon) is recorded in the audit timeline before the gate may flip.
  Scenario #4 binds FR-027's regression-rollback: the gate stays `Not Ready`, the offending change
  is reverted to the prior known-good revision, the regressed gap returns to `Open`, the row is
  tagged `regression_detected`, the iteration counter is reset for that gap, and the rollback
  evidence (failing Test ID, reverted commit SHA, restored revision SHA) is captured for grading.
  *Sources: constitution §Governance ("The project lead has final authority on architectural
  decisions"); `specs/017-cd-pipeline/spec.md` FR-004 + FR-011 (known-good baseline + automated
  rollback); `specs/029-progressive-delivery-pipeline/spec.md` FR-008 + FR-021 (5-min auto-rollback
  to known-good revision; ≥ 3 retained known-good digests); FR-024 + FR-027 (this spec).*

- **Q7: Pin SC-005's "≥ 30 % projected loss-reduction proxy" — define the measurement window and
  the proxy formula, or codify a deferral.**
  → **A: Pinned, per-scenario evaluation, Sendai-aligned counterfactual.** SC-005 now asserts:
  at the response → recovery handover for every pre-warned hazard scenario in the seed data, the
  post-handover Economic-environment view MUST satisfy
  `(baseline_loss − projected_loss) / baseline_loss ≥ 0.30`, where:
  - `baseline_loss` = the seed-data scenario's pre-suite Economic baseline (recorded by
    `bootstrap_seed_data()` at scenario load), framed per Sendai Framework Indicator C
    ("direct economic loss attributed to disasters") and aligned with
    `specs/015-performance-benchmarks/spec.md` SC-CAP-015-005's "scenario-modelled counterfactual"
    measurement method;
  - `projected_loss` = the post-handover Economic-environment view's projected residual loss after
    the platform-recommended recovery actions are applied.
  - **Measurement window**: per-scenario, evaluated at the response → recovery transition (not
    annualised). The portfolio-level annualised "≥ 30 % economic-loss reduction" claim is owned by
    `specs/shared/capstone-metric-trace.md` row `ECONOMIC_LOSS_REDUCTION × AU-v1` (per
    `specs/028-capstone-alignment/spec.md` D-003 / FR-013); this suite's per-scenario assertion is
    the AU-v1 evidence stream that feeds that portfolio cell. The 5-year horizon implied by the
    capstone framing is honoured at portfolio level via spec-015 SC-CAP-015-005, not at per-scenario
    level in this spec.
  *Sources: constitution §VII-B (Four Recovery Environments — Economic);
  `specs/015-performance-benchmarks/spec.md` SC-CAP-015-005 ("Sendai indicator alignment");
  `specs/028-capstone-alignment/spec.md` FR-013 + D-003; Sendai Framework for Disaster Risk
  Reduction 2015–2030 Indicator C-1.*

- **Q8: Pin FR-016 multi-hazard cross-coverage — enumerate which two distinct hazard types are
  mandatory per outcome (#1..#5).**
  → **A: Enumerated with AU-canonical pairs per outcome.** FR-016 now binds each capstone outcome
  to two distinct AU-relevant hazard types drawn from constitution §III's hazard catalogue
  (bushfire, riverine flood, tropical cyclone, severe storm, extreme heat, earthquake/tsunami):
  - **Outcome #1 (1,000+ lives)** — `bushfire` AND `extreme heat` (the two highest-fatality
    natural hazards in AU per AIDR / NEMA disaster-fatality records).
  - **Outcome #2 (50 % faster response)** — `bushfire` AND `severe storm` (rapid-onset hazards
    that exercise signal-to-action latency at AIIMS Levels 1 / 2).
  - **Outcome #3 (24-h earlier evacuation)** — `tropical cyclone` AND `riverine flood` (the two
    pre-warned hazards with meaningful 24-h+ lead time per constitution §VI-B).
  - **Outcome #4 (30 % logistics efficiency)** — `bushfire` AND `tropical cyclone` (long-campaign
    and pre-positioning workloads that exercise the mutual-aid / DACC / COMDISPLAN lifecycle).
  - **Outcome #5 (30 % economic-loss reduction)** — `riverine flood` AND `severe storm` (the two
    top economic-loss contributors in AU per ICA insurance-loss data).
  - `earthquake/tsunami` remains in scope for AWS warning composition (FR-011) and ≥ 1 persona
    suite SHOULD exercise it (Geoscience Australia / BoM tsunami-warning relay), but it is NOT
    mandated as the second hazard for any specific capstone outcome — to keep the suite
    AU-realistic and bounded.
  *Sources: constitution §III (Multi-Hazard) and §VI-B (pre-warned vs immediate evacuations);
  `.github/agents/sectors/commonwealth/bom-national.agent.md`,
  `.github/agents/sectors/commonwealth/ga-national.agent.md` (hazard catalogue);
  `.github/agents/sectors/nt/ntes.agent.md` (tropical cyclone preparedness);
  `specs/001-disaster-response-hub/spec.md` § Edge Cases (multi-hazard scenarios).*

- **Q9: Pin FR-020 span-of-control scope — enumerate the command-side personas for which the
  warning fires.**
  → **A: Enumerated, command-side only.** The span-of-control warning fires for the AIIMS
  command-side personas who supervise direct reports per constitution §II-A and the AIIMS 3–7
  direct-reports guidance recorded in `.github/agents/operational/incident-commander.agent.md`
  § "Span of Control" and `.github/agents/operational/operations-officer.agent.md` § Responsibilities:
  - **Tier-1 (always evaluated)**: Incident Commander (`incident-commander`).
  - **Tier-2 AIIMS function leads (evaluated when supervising direct reports)**: Operations Officer
    (`operations-officer`) — for the field supervisors they manage; Logistics Officer
    (`logistics-officer`) — for the supply / transport / medical / welfare branch supervisors they
    manage.
  - **Warning is N/A (negative test asserts suppression)**: Planning Officer, Public Information
    Officer, Field Coordinator, Resilience Planner, Executive Leader, Observer/Auditor, Risk
    Manager, and all 58 sector / jurisdiction personas when they are not in an active AIIMS
    command chain. For these personas, FR-020 asserts the warning surface stays suppressed.
  *Sources: constitution §II-A (AIIMS Functions: Control, Operations, Logistics);
  `.github/agents/operational/incident-commander.agent.md` lines 44, 93–94 (3–7 direct reports);
  `.github/agents/operational/operations-officer.agent.md` line 33 (field-supervisor span-of-control);
  `operational-input.md` Operations Officer + Logistics Officer must-do lists.*

- **Q10: Pin FR-004 `coverage-trace.md` schema cardinality — one row per (persona × outcome),
  (persona × outcome × hazard), or (persona × outcome × scenario)?**
  → **A: One row per (persona × outcome × hazard).** Selected because:
  - **Constitution §IV (Transparency and Auditability)** requires every claim be traceable
    end-to-end; FR-016 (Q8) requires each outcome to hold across two named hazard types, so the
    hazard dimension MUST be visible in the trace or FR-016 is unverifiable.
  - **Capstone evaluator UX**: the canonical reviewer question is "for persona X, for outcome #N,
    which AU-hazard types have been empirically validated?" — answerable in O(1) lookup only when
    `Hazard` is a row key.
  - **Bounded row count**: at most 68 personas × 5 outcomes × 6 AU hazards ≈ 2,040 rows, bounded
    and grep-verifiable; (persona × outcome × scenario) would explode beyond this and duplicate
    hazard/outcome pairs.
  - **Aligned with spec-028 precedent**: `specs/shared/capstone-metric-trace.md` uses
    (metric × cohort) = 20 rows; this spec's coverage-trace is the AU-v1 evidence stream feeding
    spec-028's `*** × AU-v1` cells, one dimension finer-grained because the suite operates at
    persona + hazard precision the portfolio-level trace does not.
  - **Test ID cell**: when multiple Playwright scenarios assert the same
    (persona × outcome × hazard) tuple, their Test IDs are joined with `;` in the row's
    `Test ID` cell; rows are not duplicated. Schema columns therefore become:
    `Persona | Outcome (#1..#5) | Hazard | FR | Test ID | Route | Audit Evidence ID | Status`.
  *Sources: constitution §IV (auditability); FR-016 (multi-hazard cross-coverage);
  `specs/028-capstone-alignment/spec.md` D-003 / FR-013 / clarification Q (metric-trace schema);
  `specs/028-capstone-alignment/research.md` D-003.*

### Additional ambiguities surfaced and resolved during pass 2

- **Q11: What triggers the `In-Progress` status in the gap register (FR-005)? The
  Open / In-Progress / Closed enum is declared but transitions are not codified.**
  → **A: Status transitions are evidence-anchored, mirroring spec-028 metric-trace and spec-027
  evidence-stub semantics.** Transition rules (now codified in updated FR-005):
  - `Open` is set when a `GAP-*` flag is emitted (test failure, missing route, missing capability);
    `Owner` and `Closing Spec/PR` cells may be unfilled at this point.
  - `Open` → `In-Progress` on the first commit that fills the row's `Closing Spec/PR` cell with a
    real, in-flight spec amendment or PR reference (i.e., a closing artefact is identified and work
    has begun) AND the suite has been re-run at least once since the gap was first opened (so the
    gap is confirmed as not transient).
  - `In-Progress` → `Closed` only when the closing PR has merged AND the suite has been re-run on
    the merge commit AND the previously failing test now passes AND no regression has been detected
    per FR-027.
  - `In-Progress` → `Open` (re-open) when FR-027 fires and the gap's iteration counter is reset.
  - `Closed` → `Open` is permitted only via FR-027 regression handling; never by manual edit.
  - Every status change MUST append a row to the audit timeline (FR-010) with operator identity,
    rationale, and source PR / commit SHA, satisfying constitution §IV.
  *Sources: constitution §IV (auditability); `specs/027-spec-hardening/spec.md` FR-018 + FR-020
  (evidence-stub status transitions); `specs/028-capstone-alignment/spec.md` D-003 (Status enum
  semantics); FR-010, FR-024, FR-027 (this spec).*

- **Q12: What is the relationship between this spec's `coverage-trace.json` /
  `coverage-trace.md` and `028-capstone-alignment`'s `specs/shared/capstone-metric-trace.md`? Is one
  a subset of the other?**
  → **A: They live at different scopes and granularities; this spec's trace is the AU-v1 evidence
  stream that feeds spec-028's AU-v1 trace cells. Neither is a strict subset of the other.**
  - `specs/shared/capstone-metric-trace.md` (spec-028) is the **portfolio-level trace**:
    5 metrics × 4 cohorts = 20 rows; per-cohort `SC Owner` / `HYP Owner` cells point to spec IDs
    (e.g., `015:SC-CAP-015-005`).
  - `specs/034-webapp-capstone-coverage/coverage-trace.md` (this spec) is the **suite-level
    evidence trace** that empirically validates the AU-v1 cohort claim: one row per
    (persona × outcome × hazard) per Q10, with per-test passing evidence.
  - **Linkage rule**: every AU-v1 row in spec-028's trace whose owner cells cite an outcome covered
    by this suite MUST be re-citable to ≥ 1 passing row in spec-034's coverage-trace. If
    spec-034's coverage-trace shows a `Status = Failing` or `Open` row for a
    (persona × outcome × hazard) tuple supporting an AU-v1 claim, spec-028's matching cell MUST
    flip from `Validated` to `Unresolved` until the gap closes.
  - **No overlap of purpose**: spec-028 answers "which spec owns this metric for this cohort?"
    (portfolio governance); spec-034 answers "is the AU web app empirically delivering on this
    metric for this persona on this hazard?" (executable validation).
  - Codified in updated FR-004 and Cross-References § "Capstone metric trace".
  *Sources: `specs/028-capstone-alignment/spec.md` FR-013 + D-003;
  `specs/028-capstone-alignment/data-model.md` lines 79, 105;
  `specs/028-capstone-alignment/research.md` D-003.*

- **Q13: For the 85-agent review's three sub-panels (operational + sector + technical), are
  objections weighted equally, or does any panel hold a veto on its own domain?**
  → **A: Equal weighting by default, with a domain-veto guarantee for safety-critical clauses
  held by the operational panel.**
  - **Default**: an objection is meritorious when ≥ 2/3 of the relevant panel (the panel whose
    personas the objection touches — operational, sector, or technical) supports it. Cross-panel
    disputes are resolved by the project lead per constitution §Governance ("The project lead has
    final authority on architectural decisions").
  - **Domain-veto guarantee** (operational panel): any objection that ≥ 2/3 of the operational
    panel raises against a constitutional safety-critical clause — constitution §I (Primacy of
    Life), §IV (Transparency and Auditability), Non-Negotiable #1 (Human-in-the-loop),
    Non-Negotiable #2 (Data sovereignty), or the Quality Gate "Public outputs human-reviewed" —
    MUST be addressed before the suite gate may flip to `Capstone Ready`, regardless of sector or
    technical panel weighting. The project lead may adjudicate the remediation path but MAY NOT
    bypass the operational veto on these specific clauses.
  - Sector and technical panels do NOT carry an analogous unilateral veto; their objections fall
    under the default 2/3 weighting plus project-lead adjudication.
  - Codified in updated ASM-006.
  *Sources: constitution §I (Primacy of Life), §IV (Auditability), Non-Negotiables #1 and #2,
  Quality Gates ("Public-facing outputs … MUST be reviewed by a human operator"), §Governance
  (project-lead final authority); ASM-006.*

- **Q14: Does FR-014's WCAG 2.2 AA scope include the persona workspace routes
  (`/workspaces/[personaId]`) specifically, or only top-level dashboards?**
  → **A: Includes persona workspace routes explicitly, plus all P1 operator surfaces.** Per
  `specs/001-disaster-response-hub/spec.md` NFR-001 ("All operator and public surfaces MUST conform
  to WCAG 2.2 Level AA … screen-reader, keyboard-only, and high-contrast paths MUST complete every
  P1 user journey"), persona workspaces are operator surfaces and every persona's must-do flow is
  P1 (it is the platform's primary use case). FR-014 therefore asserts WCAG 2.2 AA conformance on:
  - Every `/workspaces/[personaId]` route (persona workspace landing pages — FR-019);
  - Every `/governance/dashboard/*` route (audit, compliance, readiness, recovery, risk);
  - Every warning-composition surface (`/incidents/[id]` warning panels, AWS draft composer);
  - Every simulation control surface (`/simulations/*`);
  - The audit timeline view.
  Asserted in `cross-cutting/accessibility-and-multilingual.spec.ts`. A persona workspace failing
  WCAG 2.2 AA emits `GAP-A11Y-WORKSPACE` and blocks the gate.
  *Sources: `specs/001-disaster-response-hub/spec.md` NFR-001 (WCAG 2.2 AA scope = all operator
  and public surfaces, every P1 flow); FR-019 (persona workspace routing); ASM-009 (WCAG
  achievable; failures are uplift not variance); constitution §V-B Principle 9 ("Warnings are
  readily accessible").*

## Clarifications — Session 2026-05-02 (pass 3 — review cycle 1)

These clarifications resolve material objections raised during the **first 85-agent
review cycle** (4 panels with material objections; 1 panel — sector eastern — endorsed
the implementation outright). All cited objections were validated against the actual
implementation on branch `034-webapp-capstone-coverage` commit `2b00330` before being
admitted as amendments. See `<session>/files/agent-review/consolidated-review.md` for the
audit trail of merit validation.

### Cycle 1 — material objections accepted

- **Q15: The operational panel objects that every persona scenario file is currently a stub
  (open workspace → seed scenario → assert audit emission), and many bail with
  `test.fail(true, "...")` when the underlying API endpoint is not wired (81 such bails
  detected by repository grep). Does FR-002 admit a "stub-with-gap" scenario as proof of
  capstone coverage, or does it require workflow-state assertions?**
  → **A: Workflow-state assertions are required.** FR-002 (and FR-009) are tightened in
  this pass to require **at least one workflow-state assertion** per persona scenario that
  proves the persona's actual capstone capability — not just route reachability and audit
  emission. A scenario that bails with `test.fail(true, "<API not wired>")` is **not** a
  passing scenario for FR-002; the underlying API gap MUST be closed (see Q16). The
  implementer's own "Known limitations" note in `quickstart.md` confirms the panel finding;
  this clarification removes the workaround.
  *Sources: operational-review.md cross-cutting objection lines 71–75; constitution §IV
  ("auditability is a non-negotiable behavioural assertion, not a route assertion"); spec
  028 capstone-alignment FR-002 (per-persona evidence rather than per-route presence).*

- **Q16: The operational panel objects that capstone outcome evaluator endpoints
  (`/api/outcomes/sc-{001..011}/evaluate`) and the audit-list endpoint (`/api/audit/list`)
  are not yet wired, forcing the suite to rely on `test.fail()` placeholders. Are these
  endpoints in scope for this feature, or do they belong to a follow-on spec?**
  → **A: In scope for this feature.** The capstone evaluator endpoints are required by FR-009
  / FR-010 / SC-001..SC-005 to actually run; without them the suite cannot prove the
  capstone outcomes it claims to assert. Adding them is route-only work against the existing
  Next.js + FastAPI baseline (no net-new Azure resource), so OOS-003 does not apply. They
  are added as FR-028 below.
  *Sources: implementer's `quickstart.md` Known limitations §1; constitution §V-A; SC-001
  through SC-005 contractual numerics.*

- **Q17: The sector southwest panel raises 6 persona-level coverage gaps (SA control-centre
  RBAC, SA multi-LGA long-distance evacuation, WA ATSI handoff with culturally safe
  messaging, WA iron-ore region critical-infrastructure protection, TAS island-isolation
  ferry/air medevac, TAS palawa multilingual at persona level). Are these inside the FR-002
  inventory or follow-on?**
  → **A: Inside FR-002.** All 6 are persona-level scenarios for personas already in the
  68-persona inventory (SAPOL, SACFS+SES-SA, DFES-WA, WAPOL, AT, SES-TAS+TasPol). They are
  net-new scenarios (not new personas), so they fit under the existing FR-002 +
  FR-016 hazard-pair commitment. Added as new scenario tags in FR-030.
  *Sources: sector-southwest-review.md lines 3–13; FR-016 hazard pair #4 (bushfire+cyclone)
  for WA cyclone+iron-ore; FR-016 hazard pair #5 (riverine-flood+severe-storm) for SA river
  Murray + TAS storm; constitution §VI-C (vulnerable populations including ATSI).*

- **Q18: The sector territories+Commonwealth panel raises 5 gaps: ACT national-capital
  security mechanics + emergency-declaration mechanics, NT ATSI multilingual at persona
  level, NT tropical disease + remote-area logistics, Commonwealth ABC/SBS AWS exercise at
  persona level, cross-sector insurance recovery + DACC/JATWC handoff + Built/Economic
  Recovery Environment assertions. Same disposition?**
  → **A: Yes — inside FR-002 + FR-013 + FR-015.** All five are scenarios on personas /
  agencies already in the 68-persona inventory (AFP for ACT national-capital, ses-act +
  territory-government for declarations, ntes + sja-nt for ATSI/multilingual, NEMA + ADF for
  DACC, BoM-national + GA-national for JATWC, utility + community-ngos for insurance/Built/
  Economic recovery). ABC and SBS are NOT in the canonical 11-Commonwealth roster (per
  spec §Cited inputs) — coverage of ABC/SBS-style public-warning relay personas is
  delegated to the existing **bom-national.cyclone-warning-relay** persona scenario
  augmented with the AWS multilingual variants required by FR-014 + FR-018, plus an audit
  assertion that `Source = ABC/SBS` is recorded when the relay propagates the warning.
  *Sources: sector-tc-review.md ACT/NT/Commonwealth/Cross-sector sections; constitution
  §VII-A/B/C (recovery environments); §V-A (AWS); §V-C (Total Warning System six elements);
  §III (multi-hazard).*

- **Q19: The technical panel raises a HIGH-severity defect: the test-support guard reads
  `AMA_TEST_SUPPORT` but CI exports `AMA_TEST_SUPPORT_ENABLED="true"`, so the endpoint stays
  off in CI. Does this need a spec amendment or is it an implementation defect?**
  → **A: Implementation defect, not a spec amendment.** The dual-guard contract in spec
  §FR-021 + persona-fixture.contract.md already names `AMA_TEST_SUPPORT_ENABLED=1` plus
  `ENVIRONMENT in {dev,test}` as the canonical activation. The code drifted from the
  contract. Defect to be fixed in plan/tasks/implement under cycle-2 budget; no FR change.
  Recorded here for traceability only.
  *Sources: technical-review.md Infrastructure/DevOps objection;
  `apps/api/app/middleware/test_support_guard.py:27`; `.github/workflows/ci.yml:147`.*

### Cycle 1 — what is NOT amended

- The sector eastern panel raised **0 material objections**. NSW/VIC/QLD coverage stands as
  implemented; no FR change.
- The 81 `test.fail(true, ...)` calls themselves are not directly amended — they are a
  consequence of Q15 + Q16. Once Q16's endpoints are wired and Q15's depth requirement is
  enforced, the bail-outs disappear; the gap register tracks any residual.
- OOS-001..OOS-010 are unchanged. No Asia personas, no IdP changes, no net-new infra
  beyond the already-approved `web-coverage-evidence` blob container.

### Pass 4 — cycle-1 ambiguity resolution

These five clarifications resolve under-specifications introduced by the cycle-1 amendments
themselves (FR-028 / FR-029 / FR-030 / SC-012); Q15..Q19 are not re-litigated. Recommended
answers were derived from the constitution (`.specify/memory/constitution.md` v1.2.0), the
existing pass-1/2/3 clarifications + FRs in this spec, the persona-fixture contract
(`contracts/persona-fixture.contract.md`), the data-model artefact
(`specs/034-webapp-capstone-coverage/data-model.md`), the persona-need syntheses
(`operational-input.md`, `sector-eastern-input.md`, `sector-southwest-input.md`,
`sector-tc-input.md`), and the ADR series under `docs/aidr/decisions/`.

- **Q20: What MUST each FR-029 depth-profile YAML carry, where do the files live, what
  schema validates them, and how does the spec generator behave when a persona has no
  depth profile?**
  → **A: Codify the contract here.**
  - **Location**: `tests/e2e/web-coverage/_lib/depth-profiles/{persona-id}.depth.yaml`
    (one per persona, 68 total).
  - **Schema**: `tests/e2e/web-coverage/_lib/depth-profiles/_schema.json` (JSON-Schema
    draft-07). Required keys: `persona_id` (kebab-case, MUST resolve in
    `bootstrap_seed_data().identities` per ASM-011); `workspace_route` (drawn from
    ASM-003's route tree); `safety_critical_workflow` (enum
    `approval | publish | allocate | decline | queue-sync | escalate | handover |
    declare | reopen | observe-tamper-resist | report-generate | export-evidence` —
    last three added per Q24 for read-only personas); `workflow_steps` (ordered
    `{action, target_selector, expected_response_status}` list); `assertion_targets`
    (`{ evaluator_endpoint?: "sc-001..sc-011"|null, ui_selector?: string,
    audit_correlation_id_source: "header"|"response_body" }`); `capstone_outcome`
    (1..5 per FR-016); `hazard` (constitution §III catalogue); optional
    `multilingual_variant` (BCP-47 tag per FR-014); optional `coverage_tags` (for the
    cross-jurisdiction rule in Q23).
  - **Generator behaviour**: refuses to emit a spec when a persona's profile is absent
    OR fails schema validation; CI fails at the depth-profile-validation step (binary
    gate per FR-029 final sentence). **Opt-out is not permitted** — every persona in
    the FR-002 inventory of 68 MUST have a profile; a missing or invalid profile emits
    `GAP-DEPTH-PROFILE-MISSING` per FR-005 and blocks `Capstone Ready` per FR-023.
  *Sources: FR-002 + FR-029 (depth contract); ASM-011 +
  contracts/persona-fixture.contract.md (seed-registry binding); ASM-003 (route tree);
  constitution §III (hazard catalogue) + §V-B (multilingual baseline); Q24 (read-only
  enum extension).*

- **Q21: What is the request/response schema for the FR-028 outcome evaluator
  (`POST /api/outcomes/sc-{001..011}/evaluate`), what idempotency applies, and what
  happens for unknown `scenario_id` or out-of-range `sc_id`?**
  → **A: Plan phase MUST publish `contracts/outcome-evaluator.contract.md` with these
  bindings:**
  - **Request body**: `{ scenario_id: string (kebab-case), persona_id: string
    (kebab-case, MUST resolve in seed registry per ASM-011), correlation_id: string
    (UUID v4), metric_inputs: { ...sc-specific shape, sourced from data-model.md
    HazardScenarioFixture.baseline } }`.
  - **Response 200**: matches FR-028 — `{ status: "pass"|"fail"|"gap", evidence_refs:
    string[], metric_value: number|null, threshold: number|null, audit_id: string }`.
  - **Idempotency**: keyed by `(sc_id, scenario_id, persona_id, correlation_id)`. A
    repeated request with the same key returns the same `audit_id` and verdict; a new
    `correlation_id` triggers fresh evaluation and a new audit-timeline row.
  - **Unknown `scenario_id`**: HTTP `404` with body `{ error: "scenario_not_found",
    scenario_id: "...", suggested_action: "register in bootstrap_seed_data() or update
    depth profile" }`. The suite MUST treat 404 as `GAP-EVALUATOR-SCENARIO-MISSING` per
    FR-005 — silent pass is forbidden.
  - **Out-of-range `sc_id`**: HTTP `400`; only `sc-001..sc-011` are routable.
  - **Activation**: dual-guard per FR-021 (`AMA_TEST_SUPPORT_ENABLED=1` AND
    `ENVIRONMENT in {dev,test}`); production registration is forbidden, mirroring the
    persona-fixture contract.
  *Sources: FR-021 + persona-fixture.contract.md (dual-guard activation); FR-028
  (response shape); ASM-011 (seed-registry binding); FR-005 (gap register);
  data-model.md HazardScenarioFixture.baseline; constitution §IV (audit identity +
  rationale).*

- **Q22: For the FR-028 audit-list endpoint, is the read-back current-cycle-only or
  all-time, what pagination is supported, and what retention semantics apply?**
  → **A: Current-cycle by default; opt-in for all-time; cursor-paginated; rows are
  append-only forever.**
  - **Request**: `GET /api/audit/list?correlation_id={uuid}&cycle={current|all}&limit={1..500}&cursor={opaque}`.
  - **Default `cycle=current`**: returns rows with `audit_timestamp >=
    bootstrap_seed_data().current_cycle_start` (a deterministic timestamp recorded at
    suite-run start; surfaced in the gap register's `cycle_start_ts` cell). Default
    chosen because pass-3 Q15 + Q16 motivated the endpoint to verify post-amendment
    scenario behaviour, not historical state.
  - **Opt-in `cycle=all`**: required for FR-005 status-transition reads (operator
    identity, rationale, source PR / commit SHA across cycles) and FR-027 regression
    evidence (failing Test ID + reverted commit SHA + restored revision).
  - **Pagination**: cursor-based; response includes `next_cursor: string|null`;
    `limit` defaults to 100 and is capped at 500 to bound CI runtime per SC-011.
  - **Retention**: rows are append-only and **never deleted** (constitution §IV +
    FR-010); the endpoint surface only filters and paginates, never truncates or
    rewrites the timeline. Tamper attempts are themselves audit events (per Q24).
  - **Response schema**: `{ count: number, items: AuditRow[], next_cursor: string|null,
    cycle: "current"|"all" }` where `AuditRow` matches FR-010's required fields
    (timestamp, rationale, confidence, source_refs, operator_identity, correlation_id).
  *Sources: FR-005 (cross-cycle audit reads); FR-010 (append-only timeline); FR-027
  (regression evidence); SC-011 (CI runtime budget); constitution §IV;
  persona-fixture.contract.md (X-Correlation-Id pattern).*

- **Q23: Some FR-030 scenarios reference cross-jurisdiction tags (`territory-government`,
  `state-government` for DACC/JATWC; ABC/SBS for the BoM relay). Do they live under
  `sectors/cross-sector/` or `sectors/commonwealth/`?**
  → **A: Folder placement pivots on the *owning persona*, not the union of
  cross-jurisdiction tags.** A scenario lives where its persona ID sits in §Suite Layout:
  - `nema.dacc-jatwc-cross-jurisdiction.spec.ts` → `sectors/commonwealth/` (NEMA is
    Commonwealth-canonical per §Cited inputs; FR-030 is amended below to move this entry
    out of the cross-sector bullet).
  - `bom-national.abc-sbs-warning-relay.spec.ts` → `sectors/commonwealth/` (BoM owns
    the relay path; already correctly placed).
  - `utility.insurance-recovery-handoff.spec.ts` → `sectors/cross-sector/` (`utility`
    is in the cross-sector roster of 8 per §Cited inputs and §Suite Layout).
  - All other FR-030 scenarios are unambiguous and stay in their named jurisdiction
    folder.
  Cross-jurisdiction reach is preserved via `coverage_tags` in the depth-profile YAML
  (Q20) and a per-tuple row in `coverage-trace.md` (FR-004), so traceability remains
  explicit while folder placement stays deterministic and the FR-001 file-naming
  convention remains persona-id-rooted.
  *Sources: §Cited inputs (Commonwealth roster of 11 includes NEMA + BoM-national;
  cross-sector roster of 8 includes utility); FR-001 (naming convention); FR-003
  (cross-jurisdiction per state/territory); FR-004 (per-tuple trace row); FR-015
  (NEMA / BoM / GA cross-jurisdiction integration); §Suite Layout.*

- **Q24: For personas whose canonical safety-critical workflow is read-only (Observer/
  Auditor, Executive Leader, plus any sector persona whose persona-need synthesis names
  no state-changing must-do), how is "state-changing transition" defined under
  FR-029(b)? Is a tamper-attempt + read-back sufficient?**
  → **A: Yes — and two audit-derivative state changes also qualify.** For audit-only /
  read-only personas, FR-029(b) is satisfied by ANY of:
  - **(a) Tamper-attempt + read-back** — the scenario submits a mutation request (e.g.,
    `PATCH /api/incidents/{id}` or `DELETE /api/audit/{id}`) using the persona's RBAC
    context, and asserts (i) the mutation is rejected with `403` or `409`, AND (ii)
    the post-attempt `/api/audit/list?cycle=current` read-back contains an entry
    recording the attempted mutation with `outcome: "denied"`,
    `operator_identity: {persona_id}`, and a non-empty `rationale` (per constitution
    §IV append-only auditability).
  - **(b) Audit-derivative report generation** — Observer/Auditor personas may instead
    exercise `/simulations/[tenantId]/playback` → `/simulations/reports/[reportId]` →
    export, with the suite asserting the report ID is persisted, retrievable, and
    audit-logged (this binds User Story 4 Acceptance Scenario #3).
  - **(c) Briefing-acknowledgement state change** — Executive Leader personas may pin /
    acknowledge a briefing item that is written to the audit timeline (operator
    identity + rationale + timestamp) and surfaced under
    `/governance/dashboard/readiness`.
  Any of (a), (b), or (c) qualifies as the FR-029(b) state-changing transition; the
  depth-profile YAML's `safety_critical_workflow` enum (Q20) is therefore extended with
  `observe-tamper-resist`, `report-generate`, and `export-evidence`. FR-002's existing
  example list ("an audit-list read-back that survives a tamper attempt") is consistent
  with this; this clarification makes the read-only baseline explicit so the generator
  does not flag read-only personas as depth-profile-missing.
  *Sources: FR-002 example list; FR-020 "Warning is N/A" cohort = the read-only cohort;
  FR-029(b); constitution §IV; User Story 4 Acceptance Scenario #3; §Cited inputs
  (Observer/Auditor + Executive Leader in the operational 10).*

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Capstone-outcome traceability per persona is provable from the UI (Priority: P1)

A capstone evaluator opens the suite report and, for each of the 68 personas, sees a passing Playwright scenario that demonstrates the web app enables that persona to perform their AIIMS / combat-agency / cross-sector role in a way that contributes to at least one of the five capstone outcomes (1,000+ lives, 50% faster, 24h earlier evacuations, 30% logistics, 30% economic-loss reduction). Each scenario asserts an outcome-proxy metric (warning latency, decision-to-action time, evacuation lead time, logistics-match efficiency, recovery-handover completeness) and writes its trace row to the traceability artefact.

**Why this priority**: This is the WHAT the feature exists to prove. Without persona-by-persona traceability into the five outcomes, the capstone claim is unsubstantiated and grading fails.

**Independent Test**: Open the suite report and `specs/034-webapp-capstone-coverage/coverage-trace.md`; for any persona ID drawn from the 68, locate the Playwright scenario, confirm it loaded the persona's workspace via `/workspaces/[personaId]`, performed the must-do actions from the cited input file, and asserted at least one outcome-proxy metric within the budget defined in SC-001..SC-005. Confirm the audit timeline received a corresponding entry within 2 seconds.

**Acceptance Scenarios**:

1. **Given** the operational persona `incident-commander` from `operational-input.md`, **When** the suite runs `tests/e2e/web-coverage/operational/incident-commander.approve-cross-agency-action.spec.ts`, **Then** the scenario approves a cross-agency action, asserts an audit entry with rationale/confidence/source/operator identity within 2 seconds, and writes a trace row tagged outcome **#1 (lives)** and **#2 (50% faster)**.
2. **Given** the NSW SES persona `ses-nsw` from `sector-eastern-input.md`, **When** the suite runs `tests/e2e/web-coverage/sectors/nsw/ses-nsw.watch-and-act-flood.spec.ts`, **Then** the scenario drafts a Watch and Act flood warning with hazard/location/action statement, sends it for IC approval, and asserts a 24-hour-earlier-evacuation lead-time proxy on the predictive risk → evacuation flow.
3. **Given** the Commonwealth persona `nema` from `sector-tc-input.md`, **When** the suite runs `tests/e2e/web-coverage/sectors/commonwealth/nema.activate-comdisplan.spec.ts`, **Then** the scenario activates COMDISPLAN, opens the NJCOP view, requests consequence metrics, and asserts a logistics-match-efficiency proxy linked to outcome **#4**.
4. **Given** any persona among the 68, **When** the suite completes, **Then** `coverage-trace.md` contains exactly one row per persona × outcome combination it claims to cover, with columns `Persona | Outcome | FR | Test ID | Route | Audit Evidence ID | Status`.
5. **Given** an operational persona whose workspace `/workspaces/[personaId]` does not yet resolve to a task-tailored landing page, **When** the suite runs, **Then** the persona scenario fails with a `GAP-WORKSPACE-MISSING` flag, and the failure is enumerated in the gap register so the implement phase addresses it.

---

### User Story 2 — Cross-cutting constitutional guarantees hold for every persona (Priority: P2)

A reviewer enabling the cross-cutting suite (`tests/e2e/web-coverage/cross-cutting/`) sees that, regardless of which persona is logged in, the web app enforces AIIMS-aligned RBAC, COP refresh ≤ 5 s, append-only audit ≤ 2 s, AWS-compliant warning composition, 5-stage evacuation flow, 4 recovery environments, span-of-control warnings beyond 7 direct reports, WCAG 2.2 AA accessibility, multilingual alert payloads, offline/degraded mode for field roles, and AU-region data-sovereignty signalling.

**Why this priority**: These cross-cutting guarantees are the constitutional baseline; if any fail, the persona suites cannot legitimately claim capstone alignment. They also represent the highest-leverage uplift work because a single fix benefits many personas.

**Independent Test**: Run only the `cross-cutting/` folder. Every spec file passes; the failure of any one spec blocks the suite gate. Each cross-cutting spec is parameterised over a sample of ≥ 3 personas drawn from at least 3 different jurisdictions, demonstrating that the guarantee holds regardless of role.

**Acceptance Scenarios**:

1. **Given** any safety-critical action drawn from the AWS warning, evacuation-order, or above-threshold resource-reallocation classes, **When** an unauthorised persona attempts execution, **Then** the action is denied and an audit entry records the denial; **When** the IC approves, **Then** the action proceeds and the audit entry records the approver identity, rationale, confidence, and source references within 2 seconds.
2. **Given** an Incident Commander with 8 active direct reports, **When** the COP refreshes, **Then** a span-of-control warning surfaces and the workspace prompts delegation.
3. **Given** an offline Field Coordinator capturing a GPS-tagged hazard report, **When** the device reconnects, **Then** the queued action syncs into the immutable audit trail with original timestamp and authorship preserved.
4. **Given** any dashboard route, **When** an automated accessibility scan executes, **Then** the page asserts WCAG 2.2 AA conformance for keyboard navigation, contrast, focus order, ARIA roles, and form labels with no critical violations.
5. **Given** any AWS warning draft, **When** the public-information persona submits it, **Then** the nested model (level + hazard/location + action statement), correct hazard icon, multilingual variants for at least one community language, and de-escalation/all-clear pathway are present, and publication is blocked until IC approval.

---

### User Story 3 — Cross-jurisdiction and cross-agency integration works end-to-end (Priority: P3)

A reviewer exercising the inter-jurisdiction scenarios sees combat-agency handoffs (e.g., NSW RFS → CFA when a bushfire crosses into Victoria; SES-QLD ↔ SES-NSW for tropical-cyclone flooding at the border; ADF DACC request lifecycle from a state controller through NEMA), with shared COP visibility, mutual-aid request lifecycle, COMDISPLAN / DACC / DRFA workflows, and NCM / NJCOP integration all visible in the UI and traceable in audit.

**Why this priority**: National-scale coordination is what differentiates the AMA platform from any single-agency tool, and is required by AEMA principles 3, 4, and 10 plus the NCM/NJCOP non-functional clause. Cross-jurisdiction failures show up only when ≥ 2 agencies are simulated together.

**Independent Test**: For every state/territory (NSW, VIC, QLD, SA, WA, TAS, ACT, NT) at least one cross-jurisdiction scenario passes under `tests/e2e/web-coverage/sectors/<jurisdiction>/`, plus at least one Commonwealth-bridge scenario under `sectors/commonwealth/` activates COMDISPLAN/DACC and shows mutual-aid + NJCOP views.

**Acceptance Scenarios**:

1. **Given** a bushfire incident initiated in NSW with predicted spread into Victoria, **When** the suite runs the NSW RFS + CFA cross-jurisdiction spec, **Then** both agencies see the same incident COP, AWS warning state, and audit history.
2. **Given** a state-controller request for ADF DACC support, **When** NEMA processes the request, **Then** the COMDISPLAN activation, DACC categorisation (A/B/C), asset arrival tracking, and mission-close report all appear in the audit timeline with consistent IDs.
3. **Given** any cross-border evacuation, **When** police agencies on each side update closures, **Then** the COP merges closure data within the ≤ 5 s refresh budget and both agency workspaces show the same evacuation polygon.

---

### User Story 4 — Simulation, playback, and lessons-management close the PPRR loop (Priority: P4)

A Resilience Planner / Observer-Auditor uses the simulation suite to rehearse a multi-hazard scenario, replay it via `/simulations/[tenantId]/playback`, generate a report at `/simulations/reports/[reportId]`, and flow the lessons identified back into preparedness controls — all without leaving the web app. The suite verifies tenant isolation, deterministic replay, and report exportability.

**Why this priority**: PPRR coverage and the constitution's Quality Gate "Lessons management" are required, but they are not on the critical path of an active incident; they enable the platform's continual-improvement principle (AEMA #11).

**Independent Test**: Run only `tests/e2e/web-coverage/cross-cutting/simulation-playback.spec.ts` and `tests/e2e/web-coverage/cross-cutting/lessons-management.spec.ts`. Both pass with deterministic seed data such that re-running yields identical playback timelines and report outputs.

**Acceptance Scenarios**:

1. **Given** a Resilience Planner creating a scenario via `/simulations/create`, **When** the simulation runs, **Then** decisions, agent actions, and timeline are captured deterministically from the bootstrap seed.
2. **Given** the same scenario re-played from `/simulations/[tenantId]/playback`, **When** the playback runs, **Then** the rendered timeline is byte-identical to the first run for the asserted properties.
3. **Given** a generated report at `/simulations/reports/[reportId]`, **When** the Observer-Auditor exports it, **Then** the export includes lessons identified, mapped to preparedness controls in `/preparedness`.

---

### User Story 5 — Suite acts as the executable quality gate and feeds the iteration loop (Priority: P5)

The 85-agent (operational + sector + technical) review consumes the latest suite report and the gap register; meritorious objections become spec amendments and re-implementation tasks; the suite is re-run and the gate goes green only when objections are resolved. The suite produces machine-readable artefacts (JUnit + JSON trace) suitable for CI gating without manual interpretation.

**Why this priority**: The iteration loop is what converts the suite from a one-time validation into an ongoing capstone-readiness signal. It is the lowest priority because Stories 1–4 must produce a credible first-pass report before the loop is meaningful.

**Independent Test**: After a spec amendment driven by an agent-review objection, re-run the suite; the gap register's row for that objection moves from `Open` to `Closed`, and the suite-level pass/fail signal updates accordingly.

**Acceptance Scenarios**:

1. **Given** an agent-review objection raised against a persona scenario, **When** the spec amendment merges, **Then** the corresponding test exists or is updated, and the gap register row references the spec/PR ID.
2. **Given** the suite report and gap register, **When** any meritorious objection remains `Open`, **Then** the suite-level signal is `Not Ready`; **When** all are `Closed`, **Then** the signal is `Capstone Ready`.
3. **Given** a single gap that has cycled through three (objection → spec amendment → re-implement → re-run) iterations without closure (FR-024), **When** a fourth iteration would otherwise begin, **Then** the gap register row is flagged `escalated:project-lead`, the iteration counter for that gap is halted (no further automated cycles), the suite-level signal stays `Not Ready`, and the gate may not flip until the project lead's disposition (override / re-baseline / abandon) is recorded in the audit timeline per constitution §Governance (per Clarifications Q6).
4. **Given** a fix that closed gap A is merged, **When** the next suite run shows that a previously-passing persona scenario for an unrelated gap B now fails (regression detected per FR-027), **Then** the gate stays `Not Ready`; the offending change is reverted to the prior known-good revision per `specs/017-cd-pipeline/spec.md` FR-004 and `specs/029-progressive-delivery-pipeline/spec.md` FR-008; gap B's row is tagged `regression_detected`, returned to `Open`, and its iteration counter is reset; rollback evidence (failing Test ID, reverted commit SHA, restored revision SHA) is appended to the audit timeline for grading (per Clarifications Q6).

### Edge Cases

- **Persona without an existing workspace route**: scenario fails fast with `GAP-WORKSPACE-MISSING`; the gap register flags the persona for uplift.
- **Persona whose combat-agency role overlaps with another jurisdiction's terminology** (e.g., SES-NSW vs SES-VIC iconography): suite asserts jurisdiction-specific iconography and combat-agency designation rather than a generic icon.
- **Cross-border incident with conflicting AWS warning levels**: suite asserts the higher-severity level wins on the shared COP and an audit entry records the reconciliation.
- **AWS warning de-escalation**: suite asserts an Emergency Warning may be downgraded to Watch and Act / Advice / All Clear, each transition logged.
- **Offline field coordinator submits a duplicate of an action that was synced earlier**: suite asserts idempotent dedupe by client-generated correlation ID, no double-counting.
- **AIIMS Level transition (Level 1 → 2 → 3)**: suite asserts the COP scope, escalation routes, and NCM integration adjust correctly.
- **Span-of-control breach**: 8th direct report assignment surfaces a warning before save; suite asserts the warning text and the option to delegate.
- **Vulnerable-population evacuation**: suite asserts ATSI / CALD / disability / institutional-care registers are filterable and that warnings render in at least one community language.
- **AU-region data-sovereignty banner absent on a route that processes regulated data**: suite fails the cross-cutting data-sovereignty spec and emits `GAP-DATA-SOV-BANNER`.
- **Foundry model-hosting carve-out present**: suite asserts the carve-out badge appears next to the affected feature and the carve-out list is reachable from `/governance/dashboard/compliance`.
- **Network partition during cross-jurisdiction sync**: suite asserts conservative defaults for stale data and a reconnect indicator on each affected workspace.
- **Audit timeline tampering attempt** (PUT/PATCH against an audit ID): suite asserts the API rejects with non-success and no row is mutated.

## Requirements *(mandatory)*

### Functional Requirements

#### Suite organisation, naming, and traceability

- **FR-001**: System MUST publish a Playwright suite under the fixed layout `tests/e2e/web-coverage/{operational,sectors/<jurisdiction>,cross-cutting,capstone}/` using the file-naming convention `<persona-id>.<scenario-slug>.spec.ts`, where `<persona-id>` is the kebab-case ID drawn verbatim from the cited input files (`operational-input.md`, `sector-eastern-input.md`, `sector-southwest-input.md`, `sector-tc-input.md`).
- **FR-002**: System MUST provide ≥ 1 passing Playwright scenario per persona for each of the 68 personas (10 operational + 58 sector/jurisdiction). Persona inventory: NSW (6), VIC (5), QLD (4), SA (5), WA (3), TAS (4), ACT (7), NT (5), Commonwealth (11), Cross-Sector (8), Operational (10). **A passing scenario MUST contain at least one workflow-state assertion** that proves the persona's safety-critical capstone capability (per Clarifications Q15) — examples: a state-changing approval that returns the new state, an AWS warning draft that completes the IC-approval-then-publish path with the published payload validated, an offline action that survives a reconnect-and-replay, an audit-list read-back that survives a tamper attempt, a logistics task that completes a match → allocation transition. **Route reachability + audit emission alone are NOT sufficient**; a scenario that bails with `test.fail(true, "<reason>")` because the underlying API is missing does NOT satisfy FR-002 — the missing capability MUST be added (see FR-028) and the scenario MUST then assert the workflow state.
- **FR-003**: System MUST provide ≥ 1 cross-jurisdiction integration scenario per Australian state/territory (NSW, VIC, QLD, SA, WA, TAS, ACT, NT) and ≥ 1 Commonwealth-bridge scenario invoking COMDISPLAN/DACC/NJCOP.
- **FR-004**: System MUST emit a traceability artefact `specs/034-webapp-capstone-coverage/coverage-trace.md` (and a machine-readable companion `coverage-trace.json`) with **one row per (persona × capstone-outcome × hazard) tuple** (per Clarifications Q10). Schema columns, in order: `Persona | Outcome (#1..#5) | Hazard | FR | Test ID | Route | Audit Evidence ID | Status`. Every row MUST resolve to a real persona ID, a real capstone outcome (#1..#5), a hazard drawn from the AU catalogue (`bushfire | riverine flood | tropical cyclone | severe storm | extreme heat | earthquake/tsunami`), a real spec ID, a real test ID, and a route present in the application's route tree. When multiple Playwright scenarios assert the same (persona × outcome × hazard) tuple, their Test IDs MUST be joined with `;` in the `Test ID` cell — rows are never duplicated on this key. The artefact is the AU-v1 evidence stream that feeds `specs/shared/capstone-metric-trace.md`'s AU-v1 cohort cells (per Clarifications Q12); spec-028's matching cell MUST flip from `Validated` to `Unresolved` whenever a row supporting it shows `Status = Failing` or `Open` here.
- **FR-005**: System MUST emit a gap register `specs/034-webapp-capstone-coverage/gap-register.md` recording every test failure or `GAP-*` flag with columns `Gap ID | Persona | Route | Constitution Clause | Owner | Status (Open|In-Progress|Closed) | Closing Spec/PR`. Status transitions (per Clarifications Q11) are evidence-anchored and one-way except via FR-027:
  - `Open` is set when a `GAP-*` flag is emitted (test failure, missing route, missing capability); `Owner` and `Closing Spec/PR` cells may be unfilled at this point.
  - `Open` → `In-Progress` requires (a) the `Closing Spec/PR` cell is filled with a real, in-flight spec amendment or PR reference, AND (b) the suite has been re-run at least once since the gap was first opened (so the gap is confirmed not transient).
  - `In-Progress` → `Closed` requires (a) the closing PR has merged, AND (b) the suite has been re-run on the merge commit, AND (c) the previously failing test now passes, AND (d) no regression has been detected per FR-027.
  - `In-Progress` → `Open` (re-open) only when FR-027 fires; the iteration counter is reset.
  - `Closed` → `Open` is permitted only via FR-027 regression handling; never by manual edit.
  - Every status change MUST append an entry to the audit timeline (FR-010) recording operator identity, rationale, and source PR / commit SHA, satisfying constitution §IV.
- **FR-006**: System MUST exercise all four PPRR phases (Prevention, Preparedness, Response, Recovery) across the suite by mapping each persona scenario to at least one phase tag in the trace artefact.

#### Capstone-outcome assertions (capstone/ subfolder)

- **FR-007**: System MUST enforce AIIMS-aligned RBAC by role and incident scope on every interactive route exercised by the suite, asserted by negative tests that confirm unauthorised personas are denied.
- **FR-008**: System MUST surface a Common Operating Picture (COP) shared across incidents, jurisdictions, and AIIMS functions with a refresh latency ≤ 5 s, asserted in `cross-cutting/cop-refresh-latency.spec.ts`.
- **FR-009**: System MUST require explicit human-in-the-loop approval for every safety-critical action (evacuation orders, public alerts, resource reallocation above the threshold defined in `operational-input.md`), asserted by both positive (approval succeeds, identity logged) and negative (no approval = no execution) tests.
- **FR-010**: System MUST write an append-only audit timeline entry within 2 s of a decision, including rationale, confidence, source references, and operator identity, asserted in `cross-cutting/audit-append-only.spec.ts`.
- **FR-011**: System MUST support AWS warnings in three states (Advice, Watch and Act, Emergency Warning) using the nested model (level + hazard/location + action statement), correct hazard iconography, de-escalation, and all-clear, asserted in `cross-cutting/aws-warning-compliance.spec.ts` and parameterised across hazard types (fire, flood, storm, cyclone, heat, other).
- **FR-012**: System MUST support the 5-stage evacuation flow (Decision → Warning → Withdrawal → Shelter → Return), evacuation types (total / partial / phased), approaches (directed / recommended / self-initiated) and shelter-in-place, with explicit prioritisation for vulnerable populations (Aboriginal & Torres Strait Islander, CALD, disability, children, older persons, homeless, tourists, institutional care), asserted in `cross-cutting/evacuation-five-stage.spec.ts`.
- **FR-013**: System MUST track all four recovery environments (Social, Built, Economic, Natural) and a managed handover from response to recovery, asserted in `cross-cutting/recovery-environments.spec.ts` and tied to outcome **#5** (30% economic-loss reduction).
- **FR-014**: System MUST support multilingual alert payloads for ≥ 1 community language per warning category, with the contractual baselines (per Clarifications Q2): (a) **Simplified Chinese** as the v1 CALD language pack inherited from `specs/001-disaster-response-hub/spec.md` NFR-013 / ASM-004, asserted on at least one warning per hazard category; (b) an **Aboriginal & Torres Strait Islander language placeholder** rendered on at least one warning per hazard category per constitution §VI-C and the Public Information Officer must-do in `operational-input.md`. Canonical BCP-47 identifier selection for any additional CALD or ATSI variants is **deferred to plan-phase `research.md`** per the `specs/028-capstone-alignment/spec.md` clarification precedent. Non-AU language packs (PH/JP/BD) remain deferred per OOS-001. The system MUST also pass automated WCAG 2.2 AA conformance scans on **every P1 operator surface** (per Clarifications Q14 and `specs/001-disaster-response-hub/spec.md` NFR-001), explicitly including (a) every `/workspaces/[personaId]` route (persona workspace landing pages — FR-019); (b) every `/governance/dashboard/*` route (audit, compliance, readiness, recovery, risk); (c) every warning-composition surface (`/incidents/[id]` warning panels and the AWS draft composer); (d) every simulation control surface under `/simulations/*`; and (e) the audit-timeline view. A persona workspace failing WCAG 2.2 AA emits `GAP-A11Y-WORKSPACE` (FR-005) and blocks the gate. Asserted in `cross-cutting/accessibility-and-multilingual.spec.ts`.
- **FR-015**: System MUST integrate the cross-jurisdiction handoff lifecycle (mutual aid, COMDISPLAN, DACC, NCM, NJCOP) such that the same incident COP is visible to the relevant neighbouring jurisdictions and the Commonwealth coordinator, asserted in `sectors/commonwealth/nema.*` and `sectors/<jurisdiction>/cross-jurisdiction-*.spec.ts`.
- **FR-016**: System MUST exercise multi-hazard scenarios across the persona suites such that each capstone-outcome assertion (#1..#5) holds for two **named** AU-relevant hazard types drawn from constitution §III's catalogue (per Clarifications Q8). Mandatory pairs:
  - **Outcome #1 (1,000+ lives)** — `bushfire` AND `extreme heat`.
  - **Outcome #2 (50 % faster response)** — `bushfire` AND `severe storm`.
  - **Outcome #3 (24-h earlier evacuation)** — `tropical cyclone` AND `riverine flood`.
  - **Outcome #4 (30 % logistics efficiency)** — `bushfire` AND `tropical cyclone`.
  - **Outcome #5 (30 % economic-loss reduction)** — `riverine flood` AND `severe storm`.
  - `earthquake/tsunami` remains in scope for AWS warning composition (FR-011) and ≥ 1 persona suite SHOULD exercise it (e.g., Geoscience Australia / BoM tsunami-warning relay), but it is NOT mandated as the second hazard for any specific outcome — to keep the suite AU-realistic and bounded.
  - Cross-trace verification: every (outcome × hazard) pair above MUST resolve to ≥ 1 passing row in `coverage-trace.md` (FR-004) before the gate may flip to `Capstone Ready`.
- **FR-017**: System MUST support offline / degraded-mode for field roles with queue-and-sync semantics, idempotent dedupe by client correlation ID, conservative life-safety defaults for stale data, and an offline-banner indicator, asserted in `cross-cutting/field-offline-mode.spec.ts`.
- **FR-018**: System MUST satisfy constitution Non-Negotiable #2 across **three contractual assertions** (per Clarifications Q3), all in `cross-cutting/data-sovereignty.spec.ts`: (a) **Display** — AU-region banner / badge present on every route processing regulated platform data, plus a discoverable Foundry-model carve-out list reachable from `/governance/dashboard/compliance`; (b) **Gateway enforcement** — a synthetic PSPF-marked or PII-bearing payload submitted through the platform model gateway is denied or masked before reaching any non-AU model-hosting endpoint, per constitution NN#2 §3 ("data-minimisation controls at the platform's model gateway") and the three-classifier deny-by-default filter described in `docs/aidr/decisions/adr-033-phi-shadow-boundary.md` Layer 2; (c) **Registry currency** — the named carve-out registry (`infra/parameters/foundry-carveout.yaml` or its successor, per `docs/aidr/decisions/adr-032-oidc-supersession.md` and `specs/029-progressive-delivery-pipeline/spec.md` FR-018) is read by the suite and asserted to have `review_date` within 90 days and a non-empty `approver_identities[]`.
- **FR-019**: System MUST resolve `/workspaces/[personaId]` to a task-tailored landing page for every persona ID in the 68-persona inventory; missing routes are flagged `GAP-WORKSPACE-MISSING` (FR-005) and uplifted before sign-off.
- **FR-020**: System MUST surface a span-of-control warning when a **command-side persona** has > 7 direct reports in an incident (per Clarifications Q9). Command-side personas in scope, drawn from constitution §II-A AIIMS Functions and the AIIMS 3–7-direct-reports guidance recorded in `.github/agents/operational/incident-commander.agent.md` and `.github/agents/operational/operations-officer.agent.md`:
  - **Tier-1 (always evaluated)**: Incident Commander (`incident-commander`).
  - **Tier-2 AIIMS function leads (evaluated when supervising direct reports)**: Operations Officer (`operations-officer`) — for the field supervisors they manage; Logistics Officer (`logistics-officer`) — for the supply / transport / medical / welfare branch supervisors they manage.
  - **Warning is N/A (negative test asserts the warning surface stays suppressed)**: Planning Officer, Public Information Officer, Field Coordinator, Resilience Planner, Executive Leader, Observer/Auditor, Risk Manager, and all 58 sector / jurisdiction personas when they are not in an active AIIMS command chain.
  - Asserted in `cross-cutting/span-of-control.spec.ts` with both positive (Tier-1 / Tier-2 with > 7 reports → warning fires) and negative (N/A personas → warning suppressed) coverage.

#### Determinism, evidence, and CI gate

- **FR-021**: System MUST run the suite against `http://127.0.0.1:3000/` using the existing deterministic seed-data path (`bootstrap_seed_data()` per the cited inputs) so that re-execution yields stable assertions; any non-determinism is a defect logged to the gap register. Test fixtures impersonating personas (per OOS-007) MUST inherit RBAC strictly from `bootstrap_seed_data()`'s identity registry — no fixture-only identities are permitted — so test impersonation cannot drift from real RBAC (see ASM-011).
- **FR-022**: System MUST emit machine-readable artefacts (JUnit XML + JSON trace + screenshot/video on failure) to a stable path under `tests/e2e/web-coverage/_artifacts/` so the CI gate, the iteration loop, and post-incident reviewers can consume them without manual interpretation.
- **FR-023**: System MUST act as a CI quality gate: a run is `Capstone Ready` only when (a) every persona has ≥ 1 passing scenario, (b) every cross-cutting spec passes, (c) every state/territory has ≥ 1 passing cross-jurisdiction scenario, (d) every capstone outcome (#1..#5) has ≥ 1 traceable passing assertion, and (e) the gap register has no `Open` entries.
- **FR-024**: System MUST support an iteration loop in which an agent-review objection becomes a spec amendment, the suite is updated, the gap register is updated, and the gate flips back to green when the objection is `Closed`. Per Clarifications Q5, the loop is bounded: **maximum 3 iteration cycles per gap before escalation to the project lead** (constitution §Governance). Each cycle is one (objection → spec amendment → re-implement → re-run) round. On the 4th unresolved cycle the gap register row is flagged `escalated:project-lead` and the gate stays `Not Ready` pending project-lead disposition.
- **FR-027** *(added during Clarifications Q5)*: System MUST detect regressions during the iteration loop. If any persona scenario that was passing in the prior suite run fails after a fix is merged for a different gap, the suite MUST (a) keep the gate at `Not Ready`, (b) revert the offending change to the prior known-good revision per `specs/017-cd-pipeline/spec.md` FR-004 and `specs/029-progressive-delivery-pipeline/spec.md` FR-008, (c) tag the relevant gap register row with `regression_detected`, return its status to `Open`, and reset its iteration counter, and (d) capture the rollback evidence (failing test, reverted commit SHA, restored revision) for grading.

#### Cycle-1 amendments (added during Clarifications pass 3)

- **FR-028** *(added during Clarifications Q16; refined during Pass 4 Q21 + Q22)*: System MUST expose capstone outcome evaluator endpoints `/api/outcomes/sc-{001..011}/evaluate` (one per success criterion) and an audit-list read-back endpoint `/api/audit/list` so the suite can drive workflow-state assertions (per FR-002, FR-009, FR-010, FR-029) without bailing on `test.fail(true, "<API not wired>")`. The evaluator endpoints accept a scenario ID + persona context and return a structured judgement (`status: pass|fail|gap`, `evidence_refs: []`, `metric_value: number|null`, `threshold: number|null`, `audit_id: string`); the audit-list endpoint accepts a correlation ID and returns the append-only timeline rows for that correlation. Both endpoints MUST be guarded by the dual-guard test-support contract in FR-021 + persona-fixture.contract.md (canonical activation: `AMA_TEST_SUPPORT_ENABLED=1` AND `ENVIRONMENT in {dev,test}`). They are route-only additions (no net-new Azure resource) so OOS-003 does not apply. The full evaluator request/response schema, idempotency rule (keyed by `(sc_id, scenario_id, persona_id, correlation_id)`), and error contract (`404` for unknown `scenario_id` → `GAP-EVALUATOR-SCENARIO-MISSING`; `400` for out-of-range `sc_id`) are codified in Pass 4 Q21 and the to-be-published `contracts/outcome-evaluator.contract.md` (plan phase). The audit-list endpoint's pagination (cursor-based, `limit` default 100, max 500), retention (append-only, never deleted), and `cycle={current|all}` semantics are codified in Pass 4 Q22.

- **FR-029** *(added during Clarifications Q15; refined during Pass 4 Q20 + Q24)*: System MUST conform to a **per-persona scenario depth contract** for every Playwright spec under `tests/e2e/web-coverage/{operational,sectors/<jurisdiction>}/`. The contract requires each scenario file to (a) load the persona's primary workspace, (b) drive the persona-specific safety-critical workflow at least to a state-changing transition (approval, publish, allocate, decline, queue+sync, escalate, handover, declare, reopen — extended for read-only personas per Pass 4 Q24 with `observe-tamper-resist`, `report-generate`, `export-evidence`), (c) assert the post-transition state via either the relevant capstone evaluator endpoint (FR-028) or a UI selector that reflects persisted state, and (d) read back the audit timeline via `/api/audit/list` to confirm the rationale, source, confidence, and operator identity were recorded. The persona spec generator under `scripts/web-coverage/_lib/` MUST consume a depth-profile YAML per persona (workflow steps + assertion targets) so generated specs are workflow-driven, not stubs. Depth-profile YAML location, JSON-Schema, required keys, and missing-profile gate behaviour are codified in Pass 4 Q20 (location: `tests/e2e/web-coverage/_lib/depth-profiles/{persona-id}.depth.yaml`; schema: `_schema.json`; missing or invalid profile emits `GAP-DEPTH-PROFILE-MISSING`). The read-only-persona variant of (b) — where Observer/Auditor, Executive Leader, and analogous personas use tamper-attempt + read-back, audit-derivative report generation, or briefing acknowledgement — is codified in Pass 4 Q24. Depth-profile coverage is a binary CI gate (FR-023): a persona scenario without a depth profile fails the gate.

- **FR-030** *(added during Clarifications Q17 + Q18)*: System MUST provide the following net-new persona-level scenarios required by the cycle-1 review, all on personas already in the 68-persona FR-002 inventory:
  - **SA**: `sapol.state-control-centre-rbac.spec.ts` (multi-LGA delegated authority + role separation); `ses-sa.long-distance-multi-lga-evacuation.spec.ts` (convoy staging + inter-LGA shelter routing under degraded comms).
  - **WA**: `dfes-wa.atsi-handoff-culturally-safe.spec.ts` (culturally safe messaging + audit trail to remote ATSI community); `dfes-wa.iron-ore-critical-infrastructure.spec.ts` (port/rail/power-corridor protection under cyclone + bushfire).
  - **TAS**: `at.island-isolation-aeromedical-disruption.spec.ts` (ferry/air medevac disruption + rescue-to-care handoff); `taspol.palawa-multilingual-warning.spec.ts` (palawa-language warning variant per FR-014 ATSI baseline).
  - **ACT**: `afp.national-capital-security-mechanics.spec.ts` (Parliament/Defence precincts + Commonwealth tenancy escalation); `ses-act.territory-emergency-declaration.spec.ts` (territory-government declaration mechanics).
  - **NT**: `ntes.atsi-multilingual-at-persona-level.spec.ts` (NT-specific palawa/Yolŋu/Kriol variants applied at persona scope, not just cross-cutting); `sja-nt.tropical-disease-remote-logistics.spec.ts` (tropical-disease surge + remote-area logistics chain).
  - **Commonwealth**: `bom-national.abc-sbs-warning-relay.spec.ts` (relay path with `Source = ABC/SBS` recorded in audit + multilingual variants per FR-014; also exercises FR-018 sovereignty triple at relay handoff); `nema.dacc-jatwc-cross-jurisdiction.spec.ts` (DACC + JATWC handoff via `state-government` and `territory-government` cross-jurisdiction tags; placed under `sectors/commonwealth/` per Pass 4 Q23 owning-persona rule, moved here from the cross-sector bullet).
  - **Cross-sector**: `utility.insurance-recovery-handoff.spec.ts` (insurance recovery handoff producing Built + Economic Recovery Environment assertions per FR-013).

  Each scenario MUST conform to FR-029's depth contract and emit at least one row in `coverage-trace.md` against the persona's primary capstone outcome (mapped per the cited input file's persona must-do list). Folder placement follows the Pass 4 Q23 owning-persona rule — multi-jurisdiction reach is recorded as `coverage_tags` in the depth-profile YAML (Q20), not used for folder placement.

#### Closed-loop coverage uplift (the WHAT, not the HOW)

- **FR-025**: System MUST close any web-app coverage gap surfaced by the suite as a precondition for the gate flipping to `Capstone Ready`. The plan phase decides which uplift is route-only, which requires net-new infra, and which is deferred (per Out of Scope).
- **FR-026**: System MUST capture, for every gap closed, a record linking the failing test, the spec/PR that closed it, and the post-fix passing test, so the iteration loop produces evidence for grading.

## Key Entities

- **Persona**: An operational or sector role identified by a kebab-case ID (e.g., `incident-commander`, `ses-nsw`, `nema`). Attributes drawn from the cited inputs: role 1-liner, must-do list, workspace routes, sector-specific scenarios, cross-jurisdiction integration tests, acceptance gates.
- **Capstone Outcome**: One of the five numbered outcomes (#1 lives, #2 50% faster, #3 24h evac, #4 30% logistics, #5 30% economic loss). Each has ≥ 1 outcome-proxy metric defined in Success Criteria.
- **Persona Scenario**: A Playwright test file under `tests/e2e/web-coverage/{operational|sectors/<jurisdiction>|cross-cutting|capstone}/` whose name follows FR-001's convention and whose body asserts at least one persona must-do, one constitution clause, and one capstone-outcome proxy.
- **Coverage Trace Row**: A row in `coverage-trace.md`/`.json` linking Persona × Outcome × FR × Test ID × Route × Audit Evidence ID × Status.
- **Gap Register Entry**: A row in `gap-register.md` representing a missing route, missing capability, or failing assertion; resolved when the underlying spec/PR merges and the suite re-passes.
- **Audit Timeline Entry**: An append-only record produced by the web app for each safety-critical action; contains operator identity, rationale, confidence, source references, timestamp.
- **AWS Warning Draft**: A composed warning following the nested model (level + hazard/location + action statement) with hazard icon, multilingual variants, and approval state.
- **Evacuation Stage State**: One of `decision | warning | withdrawal | shelter | return`, with type (`total | partial | phased | shelter-in-place`) and approach (`directed | recommended | self-initiated`).
- **Recovery Environment**: One of `social | built | economic | natural`, with handover state from response.
- **COP Snapshot**: A point-in-time projection of incidents, signals, organisations, risks, tasks, and recommendations available to a persona, with refresh latency stamp.

## Success Criteria *(mandatory)*

Outcome-proxy metrics below are technology-agnostic targets the Playwright suite asserts. They are deliberately framed as user/operator-visible behaviours, not implementation latencies.

### Measurable Outcomes

- **SC-001 (Outcome #1: Save 1,000+ lives annually)** *(contractual; per Clarifications Q1)*: For every published Emergency Warning in the suite, the warning passes IC approval, includes the AWS-compliant nested model, and reaches its target audience surfaces (in-app + at least one community-language variant — Simplified Chinese baseline plus an ATSI-language placeholder per Clarifications Q2) within **≤ 2 minutes** of approval. Vulnerable-population coverage filters (ATSI, CALD, disability, children, older persons, homeless, tourists, institutional care) are present and operable on at least one warning per hazard category.
- **SC-002 (Outcome #2: 50% faster response)** *(contractual; per Clarifications Q1)*: For every persona scenario, the time from signal ingestion to IC-approved coordinated action recorded in the audit timeline is **≤ 50 % of the persona's pre-suite baseline AND** absolutely **≤ 5 minutes for AIIMS Level 1, ≤ 15 minutes for Level 2, ≤ 30 minutes for Level 3** incidents in the seed data (whichever is stricter). Span-of-control breaches surface within one COP refresh (≤ 5 s per FR-008).
- **SC-003 (Outcome #3: 24-hour-earlier evacuations)**: For every pre-warned hazard scenario in the suite (flood, cyclone, bushfire), the predictive risk → 5-stage evacuation flow is actionable from the relevant persona workspace at least 24 hours earlier than the reference timestamp embedded in the seed-data scenario, with evidence captured in the audit timeline.
- **SC-004 (Outcome #4: 30% logistics efficiency)** *(contractual; per Clarifications Q1)*: For every Logistics Officer / mutual-aid / DACC scenario, the logistics-ledger task-to-resource match completes in **≤ 70 % of the persona's pre-suite baseline number of operator interactions AND** absolutely **≤ 7 clicks for routine allocations, ≤ 12 clicks for the mutual-aid lifecycle** (whichever is stricter), with no manual reconciliation outside the UI.
- **SC-005 (Outcome #5: 30% economic-loss reduction)** *(contractual; per Clarifications Q1 + Q7)*: For every recovery scenario, all four recovery environments (Social, Built, Economic, Natural) are visible and updatable from `/governance/dashboard/recovery`, and the response → recovery handover is a managed transition (not an abrupt switch). At the response → recovery handover for every pre-warned hazard scenario in the seed data, the post-handover Economic-environment view MUST satisfy **`(baseline_loss − projected_loss) / baseline_loss ≥ 0.30`** where `baseline_loss` is the seed-data scenario's pre-suite Economic baseline (recorded by `bootstrap_seed_data()` at scenario load, framed per Sendai Framework Indicator C "direct economic loss attributed to disasters" and aligned with `specs/015-performance-benchmarks/spec.md` SC-CAP-015-005's "scenario-modelled counterfactual"), and `projected_loss` is the post-handover Economic-environment view's projected residual loss after the platform-recommended recovery actions are applied. **Measurement window**: per-scenario, evaluated at the response → recovery transition (not annualised). Portfolio-level annualised "≥ 30 % economic-loss reduction" is owned by `specs/shared/capstone-metric-trace.md` row `ECONOMIC_LOSS_REDUCTION × AU-v1` per `specs/028-capstone-alignment/spec.md` D-003 / FR-013; the suite's per-scenario assertion is the AU-v1 evidence stream that feeds that portfolio cell.
- **SC-006 (Persona coverage)**: 100% (68 / 68) of the in-scope personas have ≥ 1 passing Playwright scenario.
- **SC-007 (Cross-jurisdiction coverage)**: 100% (8 / 8) of Australian states and territories have ≥ 1 passing cross-jurisdiction scenario plus ≥ 1 passing Commonwealth-bridge scenario.
- **SC-008 (Cross-cutting compliance)**: 100% of the cross-cutting specs (RBAC, COP latency, audit append-only, AWS, evacuation, recovery, accessibility, multilingual, offline mode, data sovereignty, span-of-control) pass on a clean run.
- **SC-009 (Iteration loop closure)**: 100% of meritorious objections raised in the 85-agent review are resolved before sign-off; the gap register has zero `Open` entries.
- **SC-010 (Determinism)**: The suite re-run (same seed) produces identical pass/fail signals on at least 3 consecutive executions (no flakes).
- **SC-011 (Re-runnable as quality gate)** *(contractual; per Clarifications Q4)*: The full suite completes within **≤ 30 minutes wall-clock on a developer machine** and **≤ 45 minutes wall-clock on the CI gate runner (`ubuntu-latest` shape)**, and produces JUnit + JSON artefacts (FR-022) that a CI gate can consume without human interpretation. If the budget is breached, plan-phase shards the suite across runners; the budget is never relaxed.
- **SC-012 (Review-cycle outcome closure)** *(added during Clarifications pass 3)*: For every iteration cycle (per FR-024 max 3), **≥ 80 % of merit-validated objections are closed within the next implement phase**, evidenced by (a) the gap register row flipping to `Closed` per FR-005, (b) the originally-failing scenario or generator-driven scenario producing a passing run on the post-amendment commit, and (c) the closing PR's diff containing the FR-029 depth-contract assertion that the panel's objection demanded. Objections that survive 3 cycles escalate to project lead per FR-024 and are excluded from the 80 % numerator + denominator.

## Assumptions

- **ASM-001**: The persona-need syntheses in `operational-input.md`, `sector-eastern-input.md`, `sector-southwest-input.md`, and `sector-tc-input.md` are authoritative for what each of the 68 personas must be able to do in the web app; suite content is derived from those files.
- **ASM-002**: The bootstrap seed-data path (`bootstrap_seed_data()`) provides deterministic baseline state across operational + sector personas; suite re-runs on the same seed produce identical outcome-proxy assertions.
- **ASM-003**: The current Next.js route tree (`/`, `/disasters`, `/incidents` (+`[id]`), `/governance` (+ `[dataSourceId]` + `assignments` + `compliance`), `/governance/dashboard` (+ `audit` / `compliance` / `readiness` / `recovery` / `risk`), `/operations` (+ `workflows`), `/preparedness`, `/simulations` (+ `[tenantId]` + `playback` + `create` + `reports` + `[reportId]`), `/workspaces` (+ `[personaId]`), `/eval` (+ `[runId]`)) is the in-scope route surface; routes a persona requires that are absent are uplift candidates for the implement phase, not blockers for the spec phase.
- **ASM-004**: The capstone-outcome proxy thresholds in SC-001..SC-005 are now **contractual** (per Clarifications Q1) — the suite asserts them pass/fail. The plan phase MAY tighten the numeric thresholds further per scenario from seed-data baselines and persona acceptance gates, but MUST NOT relax them.
- **ASM-005**: Asia (PH, JP, BD) personas, hazards, and language variants are deferred per `028-capstone-alignment` and constitution amendment 1.2.0 / spec 029; no Asia persona appears in the 68-persona inventory or the success criteria. AU-only scope is legitimised by this assumption.
- **ASM-006**: The 85-agent review (operational + sector + technical) is delivered as part of this feature's iteration loop and orchestrated by the User Story 5 runner. An objection is **"meritorious"** when it is supported by ≥ 2/3 majority of the relevant agent panel (panel = the personas whose scenarios the objection touches); ties and final sign-off rest with the **project lead** per constitution §Governance. Sub-panel weighting (per Clarifications Q13): sub-panels (operational / sector / technical) carry **equal default weight**, with cross-panel disputes adjudicated by the project lead. **Domain-veto guarantee**: if ≥ 2/3 of the **operational panel** raises an objection against a constitutional safety-critical clause — constitution §I (Primacy of Life), §IV (Transparency and Auditability), Non-Negotiable #1 (Human-in-the-loop), Non-Negotiable #2 (Data sovereignty), or the Quality Gate "Public outputs human-reviewed" — the objection MUST be addressed before the suite gate may flip to `Capstone Ready`, regardless of sector or technical panel weighting; the project lead may adjudicate the remediation path but MAY NOT bypass the operational veto on these specific clauses. Sector and technical panels do NOT carry an analogous unilateral veto. Meritorious objections become spec amendments and re-implementation per FR-024 (max 3 iteration cycles per gap). Non-meritorious objections are recorded but do not block the gate.
- **ASM-007**: Net-new Azure infrastructure is permitted only if essential for an identified gap and approved during plan phase by the technical agents; spec phase records intent, plan phase records design, implement phase records code.
- **ASM-008**: AWS warnings, evacuation flows, recovery environments, audit, RBAC, accessibility, span-of-control, offline mode, and data sovereignty are constitutional baselines, not optional behaviours; suite asserts them irrespective of persona.
- **ASM-009**: WCAG 2.2 AA, multilingual variants for ≥ 1 community language per warning category, and AU-region data-sovereignty banners are achievable under the existing platform; if not, the gap register flags them as uplift, not as acceptable variance.
- **ASM-010**: Performance budgets in SC-002 (≤ 5 / 15 / 30 min for L1/L2/L3), FR-008 (COP ≤ 5 s), FR-010 (audit ≤ 2 s) and SC-011 (suite wall-clock ≤ 30 min dev / ≤ 45 min CI) are **contractual operator-visible behaviour budgets the suite asserts pass/fail** (per Clarifications Q1 / Q4), not infrastructure SLOs; the plan phase translates them to tighter engineering targets if needed but never relaxes them.
- **ASM-011** *(added during Clarifications Q5)*: Test fixtures impersonating personas (per OOS-007) inherit RBAC strictly from `bootstrap_seed_data()`'s identity registry. No fixture-only identities are permitted. This guarantees that suite assertions about role-based denial / approval reflect the real RBAC contract, not a test-side simplification.

## Hypotheses

- **HYP-001**: We believe a persona-driven Playwright suite that asserts capstone-outcome proxies on every scenario will produce a credible, repeatable signal of capstone readiness for the AMA web application; we will know we are wrong if 3 consecutive clean runs disagree on pass/fail by > 0% (any flake), or if rubric evaluators dispute the validity of the outcome proxies during the 85-agent review.
- **HYP-002**: We believe AIIMS-aligned RBAC, COP refresh ≤ 5 s, audit append-only ≤ 2 s, AWS-compliant warnings, 5-stage evacuation, and 4 recovery environments are mostly already present in the web app such that gap-uplift work is bounded; we will know we are wrong if > 30% of the 68 personas require new routes or features that the existing route tree (ASM-003) does not cover. Per Clarifications, the 30 % threshold is a **falsification trigger that re-scopes** (per `specs/027-spec-hardening/spec.md` FR-018 hypothesis format), **not** a hard suite-fail: if crossed, the AU-validated cohort still ships and the un-validated routes/features spawn a follow-on uplift feature; the gate proceeds on the validated cohort.
- **HYP-003**: We believe deferring Asia (PH/JP/BD) coverage to a later spec is acceptable for the capstone graders given AMA's Australia-first framing in spec 028; we will know we are wrong if the rubric grading flags Asia coverage as a non-deferable critical-path criterion in the 85-agent review.

## Out of Scope

This feature explicitly defers / excludes the following so the spec, plan, and implement phases stay bounded:

- **OOS-001 — Asia (PH / JP / BD) personas, hazards, and language packs.** Deferred per `028-capstone-alignment` and constitution amendment 1.2.0; promotion preconditions live in spec 028's deferral register and are not re-litigated here.
- **OOS-002 — UI translation / localisation of dashboard chrome.** Only AWS warning payloads and at least one community-language variant per warning category are in scope (FR-014). Dashboard chrome stays English; rationale: the capstone is judged on warning effectiveness, not full UI translation.
- **OOS-003 — Net-new Azure infrastructure.** Allowed only if essential for an identified gap and approved by the technical agents during plan phase; the default uplift posture is route-only changes against the existing infrastructure baseline.
- **OOS-004 — Replacing or rewriting the existing simulation engine.** Suite uses the existing engine and `bootstrap_seed_data()`; engine changes are out of scope for this feature.
- **OOS-005 — Visual regression / pixel-perfect snapshot testing.** Suite asserts behaviour, accessibility, latency, and audit/coverage trace; pixel snapshots are not a capstone-grading criterion.
- **OOS-006 — Load / soak / chaos testing.** Performance budgets are asserted as operator-visible behaviour budgets (SC-002, FR-008, FR-010), not as infrastructure-scale benchmarks.
- **OOS-007 — Identity-provider integration changes.** Suite uses test fixtures impersonating personas under the existing RBAC model; IdP work is out of scope.
- **OOS-008 — Bicep / Terraform infrastructure refactors.** Any IaC change implied by an uplift is owned by the relevant infra spec(s), not this feature.
- **OOS-009 — Mobile-native field application.** Field offline mode is asserted in the web context only (FR-017); a separate native mobile app is not in scope.
- **OOS-010 — Public release / production deployment of the suite outputs.** Outputs are CI-internal artefacts feeding the gate and the iteration loop; no external publication is part of this feature.

## Suite Layout *(fixed by this spec)*

```text
tests/e2e/web-coverage/
  operational/                                   # 10 specs — one per AIIMS persona
    incident-commander.<scenario-slug>.spec.ts
    operations-officer.<scenario-slug>.spec.ts
    planning-officer.<scenario-slug>.spec.ts
    logistics-officer.<scenario-slug>.spec.ts
    public-information-officer.<scenario-slug>.spec.ts
    field-coordinator.<scenario-slug>.spec.ts
    resilience-planner.<scenario-slug>.spec.ts
    executive-leader.<scenario-slug>.spec.ts
    observer-auditor.<scenario-slug>.spec.ts
    risk-manager.<scenario-slug>.spec.ts
  sectors/
    nsw/                                         # 6 personas + cross-jurisdiction
    vic/                                         # 5 personas + cross-jurisdiction
    qld/                                         # 4 personas + cross-jurisdiction
    sa/                                          # 5 personas + cross-jurisdiction
    wa/                                          # 3 personas + cross-jurisdiction
    tas/                                         # 4 personas + cross-jurisdiction
    act/                                         # 7 personas + cross-jurisdiction
    nt/                                          # 5 personas + cross-jurisdiction
    commonwealth/                                # 11 personas + COMDISPLAN/DACC/NJCOP
    cross-sector/                                # 8 personas (community-ngos, health, local-government, state-government, territory-government, transport, utility, volunteer)
  cross-cutting/                                 # constitutional baselines exercised across personas
    rbac-aiims.spec.ts
    cop-refresh-latency.spec.ts
    audit-append-only.spec.ts
    aws-warning-compliance.spec.ts
    evacuation-five-stage.spec.ts
    recovery-environments.spec.ts
    accessibility-and-multilingual.spec.ts
    field-offline-mode.spec.ts
    data-sovereignty.spec.ts
    span-of-control.spec.ts
    simulation-playback.spec.ts
    lessons-management.spec.ts
  capstone/                                      # one spec per outcome, asserting traceability
    outcome-1-lives-saved.spec.ts
    outcome-2-50pct-faster.spec.ts
    outcome-3-24h-evacuation.spec.ts
    outcome-4-30pct-logistics.spec.ts
    outcome-5-30pct-economic-loss.spec.ts
  _artifacts/                                    # JUnit XML + JSON trace + screenshots/videos on failure
```

Naming convention reminder (FR-001): `<persona-id>.<scenario-slug>.spec.ts`. Persona IDs are kebab-case as listed in the cited inputs.

## Overlap & Authority Rules

- This feature is `authoritative for: persona-driven Playwright validation of capstone alignment in the web application`.
- This feature `defers-to: 028-capstone-alignment (Asia coverage and capstone metric trace schema)` for the deferral register and the metric-trace ownership table.
- This feature `defers-to: 027-spec-hardening (persona-profile contract and hypothesis format)` where any persona profile or hypothesis is reused.
- This feature `defers-to: 001-disaster-response-hub (canonical AIIMS / AWS / PPRR / 5-stage evacuation / 4-recovery-environment baseline)` for any underlying capability already specified there; this feature only validates the web-app expression of those capabilities.

## Cross-References

- Capstone brief: `capstone.md`
- Constitution: `.specify/memory/constitution.md` (v1.2.0)
- Persona-need syntheses: `operational-input.md`, `sector-eastern-input.md`, `sector-southwest-input.md`, `sector-tc-input.md` (per session-state path)
- Asia deferral: `specs/028-capstone-alignment/spec.md`
- Capstone metric trace (portfolio-level): `specs/shared/capstone-metric-trace.md` — this spec's `coverage-trace.md` is the AU-v1 evidence stream that feeds the AU-v1 cohort cells of that artefact (per Clarifications Q12).
- Persona-profile contract: `specs/027-spec-hardening/contracts/persona-profile.md`
- Foundry carve-out: constitution Non-Negotiable #2; `specs/029-progressive-delivery-pipeline/spec.md`; `docs/aidr/decisions/adr-032-oidc-supersession.md`; `docs/aidr/decisions/adr-033-phi-shadow-boundary.md`.
- Known-good baseline + auto-rollback: `specs/017-cd-pipeline/spec.md` FR-004 + FR-011; `specs/029-progressive-delivery-pipeline/spec.md` FR-008 + FR-021.
- Economic-loss baseline framing: `specs/015-performance-benchmarks/spec.md` SC-CAP-015-005 (Sendai indicator alignment, scenario-modelled counterfactual).
- AIIMS span-of-control source: `.github/agents/operational/incident-commander.agent.md` § "Span of Control"; `.github/agents/operational/operations-officer.agent.md` § Responsibilities.
