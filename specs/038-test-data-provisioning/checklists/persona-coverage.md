# Persona Coverage Checklist: All Personas, Domain Demos, Multilingual

**Purpose**: Operational acceptance gate for full persona coverage — every operational and sector persona is exercisable, every domain group has an end-to-end demo scenario, and multilingual content (including outstanding A-10 deferred locales) is accounted for.
**Created**: 2026-05-11
**Feature**: [spec.md](../spec.md)
**Scope**: FR-033, FR-060..FR-062, FR-070, FR-071, SC-001, SC-008, SC-012, SC-013, SC-014, A-4, A-5, A-9, A-10.

## Operational Personas (10) — At Least One Named Test-Data Asset OR Demo Scenario

- [ ] CHK001 All 10 operational personas are enumerated in the persona-coverage report with the manifest entries serving each (FR-033, A-4).
- [ ] CHK002 Each of the 10 operational personas has ≥1 named manifest entry (seed entry, generator, mock, simulator-feed-shape, alert-template, or persona-binding) explicitly naming it in `persona_bindings` (FR-060, SC-001).
- [ ] CHK003 OR each of the 10 operational personas appears in ≥1 named demo scenario (FR-061).
- [ ] CHK004 Per-persona artefact volumes for the 10 operational personas meet or exceed the lower bound in each persona's volume guide (FR-062, SC-012, A-5).
- [ ] CHK005 The persona-coverage report shows zero "unbacked" operational personas (FR-033, SC-001).

## Sector Personas (58 total: 33 state/territory + 11 commonwealth + 8 cross-sector + 6 NSW)

- [ ] CHK006 All 33 state/territory sector personas are enumerated in the persona-coverage report with ≥1 manifest entry each (FR-060, SC-001, A-4).
- [ ] CHK007 All 11 commonwealth personas are enumerated in the persona-coverage report with ≥1 manifest entry each (FR-060, SC-001, A-4).
- [ ] CHK008 All 8 cross-sector personas are enumerated in the persona-coverage report with ≥1 manifest entry each (FR-060, SC-001, A-4).
- [ ] CHK009 All 6 NSW personas are enumerated in the persona-coverage report with ≥1 manifest entry each (FR-060, SC-001, A-4).
- [ ] CHK010 No sector persona resolves to zero entries in the persona-coverage report (FR-033, SC-001).
- [ ] CHK011 Per-persona artefact volumes for all 58 sector personas meet or exceed the lower bound in each persona's volume guide (FR-062, SC-012, A-5).

## Persona-Coverage Aggregate

- [ ] CHK012 100% of the 68 personas resolve to ≥1 named test-data artefact in the manifest (SC-001, FR-060, A-4).
- [ ] CHK013 The persona-coverage report is auto-derived from the manifest (not hand-maintained) (FR-033).
- [ ] CHK014 The persona-coverage CI check fails the build if any of the 68 personas has zero entries (FR-033, SC-001).
- [ ] CHK015 An automated volume-coverage check fails CI if any persona's lower-bound volume is unmet (FR-062, SC-012).
- [ ] CHK016 NT remote-response, surf life saving, and RFDS aeromedical retrieval personas (the user-flagged "silent gap" examples) are explicitly verified as covered (US4 motivation, SC-001).

## Domain-Group End-to-End Demo Scenarios (FR-061 — All 8 Groups)

- [ ] CHK017 The **operational** domain group has ≥1 named end-to-end demo scenario exercising ≥3 of its personas (FR-061, SC-008, US4 acceptance scenario 1).
- [ ] CHK018 The **fire** domain group has ≥1 named end-to-end demo scenario exercising ≥3 of its personas (FR-061, SC-008).
- [ ] CHK019 The **police** domain group has ≥1 named end-to-end demo scenario exercising ≥3 of its personas (FR-061, SC-008).
- [ ] CHK020 The **ambulance** domain group has ≥1 named end-to-end demo scenario exercising ≥3 of its personas (FR-061, SC-008).
- [ ] CHK021 The **SES** domain group has ≥1 named end-to-end demo scenario exercising ≥3 of its personas (FR-061, SC-008).
- [ ] CHK022 The **marine/aviation** domain group has ≥1 named end-to-end demo scenario exercising ≥3 of its personas (FR-061, SC-008).
- [ ] CHK023 The **commonwealth** domain group has ≥1 named end-to-end demo scenario exercising ≥3 of its personas (FR-061, SC-008).
- [ ] CHK024 The **cross-sector** domain group has ≥1 named end-to-end demo scenario exercising ≥3 of its personas (FR-061, SC-008).
- [ ] CHK025 Each domain demo scenario is end-to-end through the simulator + seeded reference data (not isolated to a single component) (FR-061).
- [ ] CHK026 Each domain demo scenario carries a `default_seed` so demos are reproducible without parameter passing (Key Entities — DemoScenario, FR-022).
- [ ] CHK027 Each domain demo scenario lists its `participating_personas` and `participating_feeds` in the manifest (Key Entities — DemoScenario, FR-031).
- [ ] CHK028 A fresh provisioned environment becomes demo-ready (seed loaded, simulator runnable for ≥1 named scenario per domain group) in a single automated `azd up` run with no manual data entry (SC-013).

## Multilingual Coverage (FR-070)

- [ ] CHK029 Multilingual alert templates exist for `en-AU` (FR-070).
- [ ] CHK030 Multilingual alert templates exist for `ar` (Arabic) (FR-070).
- [ ] CHK031 Multilingual alert templates exist for `el` (Greek) (FR-070).
- [ ] CHK032 Multilingual alert templates exist for `it` (Italian) (FR-070).
- [ ] CHK033 Multilingual alert templates exist for `vi` (Vietnamese) (FR-070).
- [ ] CHK034 Multilingual alert templates exist for `zh-Hans` (Simplified Chinese) (FR-070).
- [ ] CHK035 ≥5 alert variants exist per supported language (FR-062, FR-070).
- [ ] CHK036 ≥1 Indigenous-language placeholder slot is present and carries `placeholder=true` plus a "needs cultural-authority review" manifest note (FR-070, A-10, SC-014).
- [ ] CHK037 ≥1 Auslan-transcript placeholder is present and carries `placeholder=true` plus a "needs cultural-authority review" manifest note (FR-070, SC-014).
- [ ] CHK038 Every multilingual alert template entry resolves to either a translated body or an explicitly-flagged `placeholder=true` entry (SC-014).
- [ ] CHK039 The loader accepts placeholder entries (does not reject them) and labels them with `placeholder=true` (Edge Case "Multilingual content for low-resource locales").
- [ ] CHK040 Manifest filter for `placeholder=true` entries returns the full set of outstanding placeholder locales (SC-014).

## Outstanding A-10 Deferred Locales (Cultural-Authority Review Pending)

- [ ] CHK041 Every entry whose locale is an Indigenous language carries `cultural_review_required=true` in the manifest (A-10, A-18, FR-044, SC-015).
- [ ] CHK042 Indigenous-language placeholders use anonymised regional zones (e.g. "NT Central Desert regional zone — placeholder") rather than real community names (FR-044, A-10).
- [ ] CHK043 The list of A-10 deferred locales (Pitjantjatjara, Auslan transcripts, and any other low-resource locale called out by the cultural-authority custodians) is enumerated in the manifest as a tracked backlog (FR-070, A-10).
- [ ] CHK044 No real Traditional Owner names, sacred-site coordinates, or community names appear in any multilingual placeholder entry (FR-044, A-10).
- [ ] CHK045 The denylist lint at `tools/lint/check_indigenous_placeholders.py` runs against multilingual alert template files (FR-044, A-18).

## Accessibility (FR-071)

- [ ] CHK046 Every alert template's rendered surface complies with WCAG 2.1 AA (FR-071).
- [ ] CHK047 Every alert template uses plain-language wording suitable for the target audience (FR-071).
- [ ] CHK048 Audio descriptions are provided for any rendered surface that requires them (FR-071).

## Persona Naming Compliance (Reinforces FR-041)

- [ ] CHK049 Every persona-bound test record uses a synthetic person name (`John Doe`-style or `[FICTITIOUS]`-prefixed) (FR-041, A-9).

## How to Use

This checklist is an **operational gate**:
- **At end of `/speckit.plan`**: confirm the plan addresses CHK013–CHK015 (auto-derived report + CI checks), CHK017–CHK028 (8 demo scenarios), CHK029–CHK037 (multilingual baseline + placeholders).
- **At end of `/speckit.implement`**: confirm CHK001–CHK016 (per-persona coverage), CHK038–CHK045 (multilingual + Indigenous handling), CHK046–CHK049 (accessibility + naming) all pass before merge.
- **Before every demo or evaluation campaign**: re-run CHK012 (68/68 coverage), CHK017–CHK024 (all 8 domain demos), CHK028 (`azd up` demo-ready). Any unchecked item blocks the demo.
- **Each time the persona universe changes** (A-4 add/rename): re-run CHK001–CHK016 and CHK043 to surface new gaps.
