# Multi-Jurisdiction Routing Checklist: Real Sub-Agent Invocation & Simulation Telemetry-Injection Agent

**Purpose**: Verify the spec satisfies Constitution **Principle III — AIIMS Alignment** and the
operational + sectors cohort guidance for **jurisdiction × hazard × agency** routing across all
eight Australian jurisdictions (NSW, VIC, QLD, SA, WA, TAS, NT, ACT) plus federal touchpoints
(BOM, GA, NEMA, ADF DACC, ABF, ASA, RFDS). Specifically: jurisdiction-routing tuple correctness
(Amendment M / FR-021), AIIMS function mapping per sub-agent (Amendment A / FR-061),
NT/Aboriginal locale coverage (Amendment L / FR-039), and the citation-tenant-isolation rule
(FR-007) that prevents cross-jurisdiction signal leakage.
**Created**: 2026-05-08
**Feature**: [spec.md](../spec.md) (Step 8 Amendment Log at top)
**Companions**: [requirements.md](./requirements.md), [amendment-pass.md](./amendment-pass.md),
[accessibility-and-cald.md](./accessibility-and-cald.md),
[integration-and-test-coverage.md](./integration-and-test-coverage.md).

## Jurisdiction × hazard × agency tuple routing — Amendment M / FR-021

- [ ] CHK001 spec.md FR-021 mandates routing via **jurisdiction × hazard × agency tuples**,
  not category-only lookup; coarse routing lists (e.g. matching on agency name alone or on
  hazard class alone) are PROHIBITED → FR-021, Amendment M
- [ ] CHK002 The deterministic 5-step inference ladder (explicit → single-jurisdiction sim →
  map viewport → ABS-SA boundary fallback → clarify) is preserved AND each step records
  `jurisdiction_inference_step: 1..5` in the routing-decision audit entry → FR-021
- [ ] CHK003 spec.md FR-021 names the canonical tuple fixtures: **WA — `dfes-wa` is the
  sole fire-and-emergency entry point** (no NSW-style split forced onto WA); SES is *not*
  an independent WA combat agency outside DFES → FR-021, sectors-cohort SA+WA+TAS+NT+ACT
- [ ] CHK004 spec.md FR-021 names **QLD — `qfd` (Queensland Fire Department, formerly QFES)**
  as the combined urban+rural fire combat agency; QFD is invocable as a secondary
  coordination input in SES-led QLD flood scenarios → FR-021, sectors NSW+VIC+QLD
- [ ] CHK005 spec.md FR-021 names **VIC — `frv` (declared metro/regional centre) vs.
  `cfa` (regional/peri-urban) split**; the CFA/FRV boundary is the highest-complexity
  routing decision; ambiguous peri-urban zones MUST reach the FR-021 step-5 clarify rather
  than be silently misrouted → FR-021, FR-020
- [ ] CHK006 spec.md FR-021 names **SA — `sacfs` (rural/regional) vs. `samfs` (metro)
  split**; location cues distinguish rural from metro routing → FR-021,
  sectors SA+WA+TAS+NT+ACT
- [ ] CHK007 spec.md FR-021 names **TAS — `tfs` (Tasmania Fire Service) as the single
  combined fire combat agency**; instantiating a fictitious "TAS Rural Fire" agent is
  PROHIBITED → FR-021, sectors SA+WA+TAS+NT+ACT
- [ ] CHK008 spec.md FR-021 names **NT — dual-fire** (`ntfrs` for structural fires,
  `bushfires-nt` for rural fires); both are independently routable; "Darwin structure
  fire" routes to NTFRS, "Katherine grass fire" routes to Bushfires NT → FR-021,
  sectors SA+WA+TAS+NT+ACT
- [ ] CHK009 spec.md FR-021 names **NT cyclone** (`ntes`) as a first-class scenario with
  TC-specific parameters (category 1–5, central pressure, destructive-wind radius,
  storm-surge height, track bearing) → FR-021, sectors SA+WA+TAS+NT+ACT
- [ ] CHK010 spec.md FR-021 names **ACT — `act-esa` (umbrella) is addressed for strategic
  coordination and fans out internally**; bypassing the ESA umbrella is PROHIBITED →
  FR-021, sectors SA+WA+TAS+NT+ACT
- [ ] CHK011 spec.md FR-021 disambiguates **ACT policing — `afp` (federal/CT) vs.
  `act-policing` (territory EM)**; intent cues distinguish (e.g., counter-terrorism →
  AFP; routine emergency-management → ACT Policing) → FR-021, FR-023,
  sectors SA+WA+TAS+NT+ACT
- [ ] CHK012 spec.md FR-021 mandates **medical service brand per jurisdiction** as a
  closed set (SAAS, SJA-WA, SJA-NT, AT, ACT-Ambulance, NSW Ambulance, Vic Ambulance,
  QAS); a generic ambulance agent is PROHIBITED → FR-024, FR-021
- [ ] CHK013 spec.md FR-021 mandates that **SES is the lead flood/storm combat agency in
  NSW + VIC + QLD**; the simulation MUST maintain dual combat-agency threads (e.g.
  fire + flood) without collapsing them under the FR-052 5-thread cap → FR-052, FR-057,
  sectors NSW+VIC+QLD
- [ ] CHK014 An integration test sweeps each jurisdiction × hazard × agency tuple with
  one positive case (correct route) and one negative case (mis-jurisdiction OR
  mis-hazard reaches the FR-021 step-5 clarify with `routing.jurisdiction_ambiguous`
  audit entry) → FR-021, FR-020

## AIIMS function mapping per jurisdiction — Amendment A / FR-061

- [ ] CHK015 spec.md FR-061 mandates that the **same primary `aiims_function`** mapping
  applies across all eight jurisdictions (Communication agent → primary
  `Public Information` everywhere; Resource Allocation → primary `Logistics` everywhere;
  etc.); jurisdiction-specific AIIMS variants ("Sit-cell" in some AU jurisdictions vs.
  "Intelligence" elsewhere) are noted in the FR-061 table but do NOT change the canonical
  primary value → FR-061
- [ ] CHK016 spec.md FR-061 mandates that **routing logic MUST NOT blend AIIMS functions
  across sub-agents** in any jurisdiction (e.g., a Logistics intent in QLD MUST NOT
  silently invoke a QLD Planning sub-agent; cross-function fan-out requires one
  invocation per AIIMS function under the FR-052 cap) → FR-061
- [ ] CHK017 The lessons-capture writer surfaces the resolved primary `aiims_function`
  alongside the jurisdiction-specific sub-agent name (e.g. "FR-V (Operations)",
  "QFD (Operations)", "DFES-WA (Operations)") in §3 sub-agent responses and §4 IC
  decisions → FR-054, FR-061

## NT/remote Aboriginal locale coverage — Amendment L / FR-039

- [ ] CHK018 spec.md FR-039 includes **NT/remote Aboriginal languages** —
  **Yolŋu Matha**, **Warlpiri**, **Pitjantjatjara**, **Arrernte** — in the watermark
  text-translation table AND audio-prefix table → FR-039, Amendment L
- [ ] CHK019 spec.md FR-039 includes **Kriol** and **Torres Strait Creole** in both
  watermark tables → FR-039, Amendment L
- [ ] CHK020 spec.md FR-039 mandates **jurisdiction language profiles** linking each
  jurisdiction (NSW, VIC, QLD, SA, WA, TAS, **NT**, ACT) to its priority locales — the
  NT profile MUST list at least one of Yolŋu Matha, Warlpiri, Pitjantjatjara, Arrernte,
  Kriol → FR-039, Amendment L
- [ ] CHK021 The locale-resolution 3-step fallback `request_locale →
  jurisdiction_priority_locale → en_AU` (shared between FR-058 audio-prefix and FR-064
  live-log per pass-2 Q6) MUST honour the jurisdiction language profile so an NT
  simulation defaults to a remote Aboriginal language locale for screen-readers + audio
  on a CALD-listener pathway → FR-058, FR-064, FR-039, pass-2 Q6
- [ ] CHK022 An integration test asserts that the `jurisdiction_priority_locale` step is
  consulted (not bypassed) for at least one simulation in each of the eight jurisdictions
  → FR-039
- [ ] CHK023 Backlog locales (Yolŋu Matha, Warlpiri, Pitjantjatjara, Arrernte, Kriol,
  Torres Strait Creole) are tracked with explicit
  `staging_promotion_blocker: true|false` flags so the Constitution-aligned spec target
  is not silently degraded by an empty backlog → FR-039, Amendment L

## Citation tenant-isolation across jurisdictions — FR-007

- [ ] CHK024 spec.md FR-007 mandates that **no sub-agent citation may resolve to a
  live-tenant resource** in any jurisdiction; a citation that resolves cross-jurisdiction
  to live data is treated as a tenant-isolation violation → FR-007
- [ ] CHK025 The citation-validation guard rejects cross-jurisdiction live-tenant
  citations on every sub-agent reply, marks the reply `degraded`, and writes a typed
  audit entry with the offending jurisdiction + resource name → FR-007, FR-016
- [ ] CHK026 An integration test simulates a sub-agent reply citing a live-tenant
  resource for each of the eight jurisdictions and asserts the citation is rejected with
  the typed audit → FR-007

## Federal / cross-jurisdiction touchpoints

- [ ] CHK027 BOM, GA, NEMA COMDISPLAN, ADF DACC, ABF, ASA, RFDS, ARC, SLSA, SJA — all
  federal/national touchpoints are wired as **sandboxed sources** (BOM weather injection,
  GA geohazard polygons, etc.) and never as live-tenant data sources → FR-007, FR-042,
  cohort table cross-jurisdiction
- [ ] CHK028 spec.md FR-042 mandates **hard refusal** of any free-text injection that
  attempts to dispatch a real-world ADF DACC, BOM warning, or NEMA COMDISPLAN action;
  the refusal produces a typed audit entry naming the requested federal touchpoint →
  FR-042, Edge Cases ("Free-text injects a real-world action")
- [ ] CHK029 An MRNSW maritime scenario (NSW state but with no declared BOM handoff in
  the persona file) MUST inject BOM weather as a sandboxed source without relying on a
  declared `mrnsw → BOM` path → cohort table NSW+VIC+QLD, FR-007

## Concurrent multi-jurisdiction scenarios

- [ ] CHK030 spec.md A10 + FR-052 + FR-057 mandate that concurrent multi-hazard +
  multi-jurisdiction sims (up to 5 hazard threads per A10) MUST run as **parallel
  sub-agent threads** with map overlays coexisting and chat replies attributed to the
  correct agency per jurisdiction → FR-052, FR-057, A10
- [ ] CHK031 An integration test reproduces a concurrent NSW bushfire + QLD flood +
  VIC medical + ACT evacuation scenario and asserts: (a) 4 concurrent hazard threads
  active; (b) each thread attributed to the correct jurisdiction × agency tuple;
  (c) FR-061 primary `aiims_function` correctly resolved per sub-agent invocation;
  (d) zero combat-agency thread collapse (SC-011) → FR-052, FR-057, FR-061, SC-011

## Notes

**What this checklist covers**: the cohort-cited multi-jurisdiction surface area of
spec 036 — specifically, that jurisdiction routing uses tuple-based fixtures (not
category-only lookup) for all eight Australian jurisdictions plus federal touchpoints;
that the FR-061 AIIMS function mapping is jurisdiction-invariant on the primary value;
that the FR-039 watermark table covers NT/remote Aboriginal locales; and that
cross-jurisdiction tenant-isolation is preserved on every citation pathway.

**What this checklist does NOT cover**:

- Constitution-I (Primacy of Life) safety guarantees — covered by
  `safety-and-life-primacy.md`.
- CALD watermark rendering completeness for the 30+ locale set generally — covered by
  `accessibility-and-cald.md` (this checklist covers only the NT/Aboriginal expansion).
- Audit-record completeness and provenance — covered by `audit-and-provenance.md`.
- Failure-mode behaviour and recovery — covered by `graceful-degradation.md`.
- General test-matrix enumerability — covered by `integration-and-test-coverage.md`.
- The full Step-8 amendment scope detail — covered by `amendment-pass.md`.

**Relation to `requirements.md`**: that checklist verifies the spec is *well-written*.
This checklist verifies the spec **routes correctly across all eight Australian
jurisdictions** and that no jurisdiction is silently aliased to a coarser routing
category that would lose a combat-agency tuple, an AIIMS-function mapping, or a
priority locale.
