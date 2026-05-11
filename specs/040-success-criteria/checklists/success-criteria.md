# Success Criteria & Evidence Harness Checklist: 040-success-criteria

**Purpose**: Unit-test the *requirements* in `spec.md` (and downstream artefacts) for the success-criteria-evidence harness — does the spec define a complete, clear, consistent, measurable, AU-sovereign, constitution-aligned KPI/measurement/simulation/instrumentation framework that demonstrably evidences capstone outcomes (spec 015 SC-CAP-015-001..005) without re-building shared platform capabilities?
**Created**: 2026-05-11
**Feature**: [spec.md](../spec.md)
**Scope discipline reference**: [`specs/shared/capstone-metric-trace.md`](../../shared/capstone-metric-trace.md), spec 037 FR-020 / FR-037 precedents.

> Each item asks whether a *requirement is well-written* (complete / clear / consistent / measurable / traceable). Markers: `[Gap]` = appears missing, `[Ambiguity]` = vague, `[Conflict]` = inconsistent, `[Assumption]` = needs validation, `[Traceability]` = back-link required.

---

## KPI Ladder Completeness (Capstone Coverage)

- [ ] CHK001 Are leading-indicator KPIs explicitly defined (≥1 each) for all five capstone outcomes SC-CAP-015-001 (lives saved), -002 (response time), -003 (evac lead time), -004 (logistics efficiency), -005 (economic loss reduction)? [Completeness, Spec §FR/§SuccessCriteria → Spec 015]
- [ ] CHK002 Are lagging-indicator KPIs explicitly defined (≥1 each) for the same five SC-CAP-015-001..005 outcomes? [Completeness]
- [ ] CHK003 Does the spec require every KPI entry (leading and lagging) to carry all nine attributes — formula, unit, owner-role, refresh cadence, target, alert threshold, baseline source, provenance, confidence-band rule — with no optional attribute? [Completeness, Clarity]
- [ ] CHK004 Is the *formula* attribute required to be expressed as a deterministic, reproducible expression (variables + arithmetic) rather than narrative prose? [Clarity, Measurability]
- [ ] CHK005 Is the *unit* attribute constrained to SI / domain-standard units with explicit dimensional consistency between leading and lagging pairs? [Consistency]
- [ ] CHK006 Is the *owner-role* attribute defined against named roles in the governance shell (spec 035) rather than free-text job titles? [Traceability, Consistency]
- [ ] CHK007 Are *refresh cadence* values constrained to an enumerated set (e.g., real-time / hourly / daily / per-incident / post-event) rather than ad-hoc strings? [Clarity]
- [ ] CHK008 Are *target* and *alert threshold* required to be numeric with explicit comparator (≤ / ≥ / band) and to share the KPI's unit? [Measurability]
- [ ] CHK009 Is the *baseline source* required to cite either (a) a recognised AU external benchmark or (b) the prototype-baseline simulation run, with both options enumerated? [Traceability]
- [ ] CHK010 Is the *provenance* attribute required to chain to instrumentation lineage (signal → model → recommendation → human-decision → outcome)? [Traceability]
- [ ] CHK011 Is the *confidence-band rule* required to specify the statistical method (bootstrap-95%-CI default, SD fallback) per KPI? [Clarity, Measurability]

## Measurement Framework Integrity

- [ ] CHK012 Does the spec define each capstone metric (lives saved, response time, evac lead time, logistics efficiency, economic loss reduction) with a single canonical written definition usable by an Executive Leader (US2)? [Completeness, Spec §US2]
- [ ] CHK013 Is the bootstrap-95%-CI rule specified with a minimum resample count and deterministic seeding policy? [Clarity, Measurability]
- [ ] CHK014 Is the SD-fallback rule specified with the exact trigger condition (e.g., n < threshold, non-bootable distribution) and the substitute calculation? [Clarity]
- [ ] CHK015 Is the missing-timestamp imputation rule specified as forward-impute, with a tagging requirement on every imputed row? [Completeness]
- [ ] CHK016 Does the spec require imputed rows to be excluded from confidence-interval computation? [Consistency]
- [ ] CHK017 Is the >10% imputed-share threshold specified as triggering both a small-sample flag *and* named-auditor sign-off (cross-referenced to spec 037 FR-037 precedent)? [Completeness, Traceability]
- [ ] CHK018 Are unit-of-measure and time-zone normalisation rules defined for all input signals feeding capstone metrics? [Gap]
- [ ] CHK019 Is the rounding/precision policy specified per KPI to prevent display-vs-storage drift? [Gap, Clarity]

## Simulation Harness — Replay & Scenario Coverage

- [ ] CHK020 Is determinism quantified as ±2% relative *and* ±1 absolute-unit per KPI on identical-seed replay, with both bounds applied (whichever is tighter/looser explicitly stated)? [Clarity, Measurability]
- [ ] CHK021 Is warp-playback compatibility (spec 026) required, and are the supported warp factors / state-snapshot semantics referenced rather than redefined? [Reuse, Traceability]
- [ ] CHK022 Are all seven canonical scenarios — bushfire, flood, cyclone, urban-fire, mass-casualty, hazmat, marine SAR — each required to have at least one executable replay artefact? [Coverage, Spec §US3]
- [ ] CHK023 For each canonical scenario, is the baseline-vs-AMA-assisted comparison required to emit a per-KPI delta scorecard (one row per KPI, signed delta + CI)? [Completeness]
- [ ] CHK024 Does the spec define what constitutes the "baseline" run (e.g., AMA assistance disabled, human-only) unambiguously enough to reproduce? [Clarity, Ambiguity]
- [ ] CHK025 Are scenario-input fixtures required to be version-pinned and content-hashed for replay determinism? [Measurability, Gap]
- [ ] CHK026 Is the failure mode defined for when a scenario replay drifts outside the ±2% / ±1-unit determinism bound (e.g., quarantine, auditor sign-off)? [Edge Case, Gap]

## Expected-Impact Reasoning (Capability → KPI Causal Chains)

- [ ] CHK027 Is each capability→KPI causal chain required to enumerate named assumptions (not anonymous bullets)? [Completeness, Spec §US5]
- [ ] CHK028 Is each causal chain required to enumerate threats-to-validity (confounders, selection bias, scenario-coverage gaps)? [Completeness]
- [ ] CHK029 Is each causal chain required to back-cite the originating capability spec (spec ID + section)? [Traceability]
- [ ] CHK030 Are assumptions required to carry a falsifiability criterion (what observation would invalidate them)? [Measurability, Gap]
- [ ] CHK031 Is conflict resolution defined for cases where two capabilities claim the same KPI delta (no double-counting)? [Conflict, Gap]

## Benchmark Register

- [ ] CHK032 Does every KPI cite a recognised AU external benchmark — drawn from at minimum AFAC FDI/FFDI, BoM lead-time, agency response targets, ICAO ARFF, SAIDI/SAIFI, or AIIMS span-of-control 3–7 — appropriate to its domain? [Completeness, Traceability]
- [ ] CHK033 Does every KPI additionally cite a prototype-baseline comparison value (from the simulation harness baseline run)? [Completeness]
- [ ] CHK034 Are benchmark citations required to include source identifier, publication/version date, and URL or document reference? [Traceability, Clarity]
- [ ] CHK035 Is the AIIMS span-of-control benchmark applied as the 3–7 band (not a single point) wherever organisational-structure KPIs are defined? [Consistency]
- [ ] CHK036 Is benchmark applicability checked per jurisdiction (US6) so that, e.g., ARFF only applies to aviation contexts? [Consistency, Coverage]

## Instrumentation, Audit & Traceability

- [ ] CHK037 Is the full traceability chain — signal → model → recommendation → human-decision → outcome — required for every KPI value, with each link uniquely identifiable? [Completeness, Spec §US4]
- [ ] CHK038 Is the audit log required to be append-only with cryptographic or equivalent tamper-evidence? [Completeness, Gap]
- [ ] CHK039 Is the AU retention period specified as ≥7 years with the source legislation/standard cited? [Traceability, Clarity]
- [ ] CHK040 Are degraded-mode events (missing signals, model fallback, manual override) required to be captured with the same traceability schema as nominal events? [Coverage, Edge Case]
- [ ] CHK041 Is the manual-row tag required on every artefact and KPI rollup with a ≤50% manual share, exceeding which mandates named-auditor sign-off (spec 037 FR-037 precedent)? [Completeness, Traceability]
- [ ] CHK042 Is the manual-share computation rule (numerator/denominator definition, scope per artefact vs. per KPI) unambiguously specified? [Clarity]

## Constitution Non-Negotiables

- [ ] CHK043 Is "primacy of life" required to be the top-ranked KPI dimension whenever KPIs are sorted, ranked, or trade-off-weighted? [Consistency]
- [ ] CHK044 Are AU-sovereignty constraints required for KPI data, scenario fixtures, and audit logs (data-residency + processing-locality, not just storage)? [Completeness]
- [ ] CHK045 Is human-in-the-loop required as advisory-only — i.e., AMA outputs are recommendations, never autonomous actions affecting the physical world? [Consistency]
- [ ] CHK046 Is interoperability required against CAP, EDXL, GeoJSON, and OpenAPI with explicit version constraints rather than "compatible with"? [Clarity, Ambiguity]
- [ ] CHK047 Is graceful degradation required for every KPI — i.e., a defined behaviour when an upstream signal is unavailable (degraded value + flag, not silent failure)? [Coverage, Edge Case]

## Reuse & Scope Discipline

- [ ] CHK048 Does the spec explicitly state that the governance shell (spec 035) is reused and not re-implemented? [Reuse, Traceability]
- [ ] CHK049 Does the spec explicitly reuse warp playback (spec 026) for replay UI, with no new playback primitive? [Reuse]
- [ ] CHK050 Does the spec explicitly reuse the evaluation framework (spec 030) for KPI computation/aggregation, with no parallel eval engine? [Reuse]
- [ ] CHK051 Does the spec explicitly reuse the simulation chat (spec 024) for scenario interaction, with no new chat surface? [Reuse]
- [ ] CHK052 Does the spec explicitly prohibit introducing new chart libraries, new UI primitives, or a new simulation engine? [Out-of-Scope, Spec §OutOfScope]
- [ ] CHK053 Is this feature tagged in `specs/shared/capstone-metric-trace.md` as non-capstone-critical-path / delivery-hygiene per spec 037 FR-020 precedent? [Traceability]

## Multilingual & Accessibility (US7)

- [ ] CHK054 Is language coverage required to include English, the top-5 ABS community languages (named explicitly), Auslan, and ≥1 jurisdiction-appropriate First-Nations language? [Completeness, Spec §US7]
- [ ] CHK055 Is the rule for selecting the "jurisdiction-appropriate First-Nations language" specified (e.g., from a maintained registry per jurisdiction) rather than left to authoring discretion? [Clarity, Ambiguity]
- [ ] CHK056 Is WCAG 2.2 AA conformance required for every public-information KPI render, with the exact success criteria scope (perceivable / operable / understandable / robust) referenced? [Completeness]
- [ ] CHK057 Is plain-language Grade-8 readability required, with the measurement method (e.g., Flesch-Kincaid grade ≤ 8) and tooling specified? [Measurability]
- [ ] CHK058 Are Auslan deliverables required to be video (not text gloss) with caption and transcript pairing? [Clarity, Gap]

## Risk-Adjusted KPIs

- [ ] CHK059 Is the 5×5 likelihood × consequence matrix specified with each cell's L and C value enumerated (1..5 each)? [Completeness]
- [ ] CHK060 Is the risk-adjusted formula `risk_adjusted = unadjusted × (L × C) / 25` stated verbatim, with worked example? [Clarity, Measurability]
- [ ] CHK061 Is the requirement that units are preserved by the risk-adjustment (i.e., (L×C)/25 is dimensionless) stated and asserted in test fixtures? [Consistency]
- [ ] CHK062 Are the L and C scoring rubrics (what does L=3 mean? what does C=5 mean?) defined or cited from a recognised AU risk standard (e.g., AS ISO 31000)? [Completeness, Traceability]
- [ ] CHK063 Is the policy defined for displaying both unadjusted and risk-adjusted KPI values side-by-side (no silent substitution)? [Clarity, Gap]

## Cross-Cutting Ambiguities, Conflicts & Edge Cases

- [ ] CHK064 Are there any conflicting refresh cadences between a leading KPI and its paired lagging KPI that would prevent honest delta computation? [Conflict]
- [ ] CHK065 Is the behaviour defined when the prototype baseline run itself is unavailable (e.g., new scenario added) — does the KPI render with "no baseline" state? [Edge Case, Gap]
- [ ] CHK066 Is the policy defined for KPIs whose recognised external benchmark is contested or jurisdiction-variant (e.g., differing state response targets)? [Edge Case, Ambiguity]
- [ ] CHK067 Is a unique, stable identifier scheme established for every KPI, scenario, and audit record (to support back-citation across spec 015/030/035/037)? [Traceability]
- [ ] CHK068 Are the acceptance criteria for "harness complete" objectively measurable (i.e., a reviewer can mechanically verify pass/fail without authorial intent)? [Measurability]

---

## Notes

- Mark items `[x]` when the spec (or named downstream artefact) demonstrably satisfies the question.
- Where an item is `[Gap]`, the resolution is normally an additional FR or clarification round — not a code change.
- Spec 037 precedents cited: FR-020 (delivery-hygiene tagging), FR-037 (>50% manual-share auditor sign-off).
- Capstone outcomes referenced: spec 015 SC-CAP-015-001 (lives saved), -002 (response time), -003 (evac lead time), -004 (logistics efficiency), -005 (economic loss reduction).
- Reused artefacts: spec 024 (sim chat), spec 026 (warp playback), spec 030 (eval framework), spec 035 (governance shell).
