# Capstone Deck — Claim Validation Audit

> Companion to `AMA_Capstone_Disaster_Response_Hub.pptx` (43 slides, generated 12 May 2026).
> **Method:** Every quantified or attributed claim in slide bodies, captions, and speaker notes was checked against (a) the workspace itself for internal counts, and (b) public sources (Wikipedia/Royal Commission/ABS/etc.) for external claims. Each entry below either passed validation, is flagged as overstated/unsupported, or is a complete fabrication that needs to be replaced.
>
> Verification trail (commands run today):
> ```
> Tests: 526 test_*.py + 5 e2e .spec.ts (not 231)
>   unit:173 contract:156 integration:134 simulation:25 benchmark:6 load:2 devops:10 pipeline:0 e2e:5
> Specs: 42 (matches "40+")
> Bicep modules: 32 (not 25)
> Operational personas: 10 (not 9)
> Sector personas (active, excl. _archive): 58 (not 14)
> Technical personas: 17 (not 8)
> Total active agents: 85 (or 100 incl. _archive); not 31
> Australian data sources seeded: 46 (not "50+")
> Governance dashboard endpoints: 13 — VERIFIED via spec 021 tasks.md T011/T031
> ```

## Validation outcome at a glance

| Verdict | Count |
|---|---|
| ✅ Verified — keep as written | 14 |
| ⚠️ Partially supported — edit recommended | 7 |
| ❌ Fabricated or unsupportable — must replace | 18 |

---

## 1. ❌ Items that must be replaced (fabricated or unsupportable)

| # | Slide | Existing quote / claim | Why it fails | Supportable substitute |
|---|---|---|---|---|
| 1 | **Slide 3 (3-cols, col 1)** | "**3,500+ homes destroyed**" (Black Summer) | Wikipedia (cited from Royal Commission tables): 2,779 homes destroyed nationally in the season tables; full dataset rounds to "**3,000+ buildings destroyed**". 3,500+ is overstated. | "**3,000+ buildings destroyed**" (source: Royal Commission into National Natural Disaster Arrangements 2020, NEMA Black Summer fact sheet). |
| 2 | **Slide 3 (col 1)** | "Black Summer 2019–20 burned **24 million hectares** across the eastern seaboard" | Hectares figure is correct nationally (24M ha), but **"eastern seaboard"** is misleading — ~6.8M of those hectares were in the Northern Territory, mostly scrub/grassland fires. | "Black Summer 2019–20 burned **~24 million hectares nationally** — including ~5.2 million hectares in NSW alone — and remains Australia's costliest natural disaster" (source: Wikipedia citing Cook et al. 2021 / Read & Denniss 2020). |
| 3 | **Slide 3 (col 3)** | "**Insurance Council of Australia estimates climate-amplified disaster losses will exceed $35B per year by 2050**" | I cannot locate this specific ICA statement. There are real ICA reports projecting rising disaster costs but I do not have evidence of the "$35B/yr by 2050" figure. | Replace with verifiable claim: "**Australia's normal-year insured natural-disaster losses already exceeded A$2B every year from 2019–2023, peaking at A$7.2B in 2022** (source: Insurance Council of Australia, *Insurance Catastrophe Resilience Report*)." If you want a 2050 projection, cite the **Climate Council 2022 *Uninsurable Nation*** report's projected one-in-25 properties uninsurable by 2030 instead. |
| 4 | **Slide 3 — speaker notes** | "Royal Commission into National Natural Disaster Arrangements named coordination… as the primary improvement opportunity in **31 of its 80 recommendations**" | Royal Commission has 80 recommendations (verified) but I have no evidence "31" relate to coordination specifically. Both the count and the framing are fabricated. | "The Royal Commission delivered **80 recommendations** (28 October 2020). Multiple recommendations — including the establishment of NEMA — explicitly addressed coordination across jurisdictions." (Source: Royal Commission report, royalcommission.gov.au.) |
| 5 | **Slide 3 — speaker notes** | "Productivity Commission's 2024 finding that disaster spend is **97% reactive, 3% pre-emptive**" | I cannot verify this attribution. The Productivity Commission has commented on the response/mitigation balance historically, but the 97/3 split as a "2024 finding" is not something I can substantiate. | "Successive reviews (Productivity Commission 2014 *Natural Disaster Funding*; Royal Commission 2020) have found Australia's disaster spend skewed strongly toward post-event recovery rather than mitigation." Drop the "97% / 3%" precision unless you can cite the specific source. |
| 6 | **Slide 4 (body)** | "**537 local councils**" | Approximate — the Australian Local Government Association reports ~537 LGAs. *Acceptable*, but flag as approximate. Defensible. | Reword: "**~537 local councils** (per Australian Local Government Association)". Borderline OK as-is; minor risk. |
| 7 | **Slide 4 (body)** | "**AFAC projects a 25–35% increase in days of catastrophic fire danger by 2040**" | I cannot verify this specific AFAC projection. AFAC does publish seasonal outlooks but I have no source for the "25–35% by 2040" range. | "**CSIRO and the Bureau of Meteorology's *State of the Climate 2024* report finds dangerous fire weather days in southern and eastern Australia have increased significantly since the 1950s, with further increases projected**" (source: BoM/CSIRO biennial *State of the Climate* report — verifiable). |
| 8 | **Slide 5 — body & speaker notes** | "Catalogued **31 personas across nine operational roles, fourteen sector agencies, and eight executive/technical roles**" | Verified counts in repo: **10 operational + 58 active sector + 17 technical = 85** (or 100 incl. archived). 31 / 9 / 14 / 8 are wrong. | "**Catalogued 85+ personas across 10 operational roles, 58 sector agents (across Commonwealth + 8 state/territory jurisdictions + cross-sector), and 17 technical roles** — all checked into `.github/agents/`." |
| 9 | **Slide 5 (col 2)** | "Fire (RFS/CFA/QFES), Police, SES, Ambulance, Hospitals, Utilities, Transport, Telecommunications, Local Government, Environment, Indigenous Relations, Wildlife, Weather, Research. **14 sector agents**, governed by jurisdiction policy." | Same as #8 — actual count is 58 active, organised by jurisdiction sub-folder (commonwealth/act/nsw/nt/qld/sa/tas/vic/wa/cross-sector). | "**58 active sector agents** organised by jurisdiction (Commonwealth, all states/territories, cross-sector) — fire, police, SES, ambulance, hospitals, utilities, transport, telco, local gov, environment, Indigenous relations, wildlife, weather, research." |
| 10 | **Slide 6 (col 1)** | "BoM, GA, eight state services, 537 councils, utilities, satellite feeds, social media — **50+ authoritative sources**" | Workspace has **46** seeded data sources. "50+" overstates. | "**~46 seeded Australian sources at launch** — extensible via 30 lines of YAML + a Bicep module." |
| 11 | **Slide 6 (col 2)** | "An average level-2 incident generates **~600 source signals per hour**. Today these are fused by human duty officers… **Industry timing studies show 4–6 hours elapsed** before an Incident Action Plan converges." | Both numbers are fabricated. No "industry timing study" cited; "600 signals/hour" not benchmarked anywhere in the repo or in any AIDR document. | "Today, signal fusion is largely manual — duty officers swivel-chair across multiple authoritative systems. **AIDR Incident Management Handbook 2023 §3 acknowledges that converging on an Incident Action Plan in a multi-agency response can take hours under load** — exact latency varies by jurisdiction and is not publicly benchmarked. *(Spec 040 establishes the prototype baseline.)*" |
| 12 | **Slide 7 (body)** | "Today's **median coordination latency for a level-2 incident is 4.2 hours (range 1.5–9.0)**" + speaker-notes "based on After Action Reviews from 2018–2024" | **Already conceded as fabricated** in earlier exchange. No source. | "**There is no published canonical baseline for coordination latency in Australian level-2 incidents — and that absence is itself the problem we attack.** Spec 040 (*Measurable Success-Criteria Evidence Harness*) establishes a prototype baseline against which AMA-assisted runs are scored, with bootstrap 95% confidence intervals." |
| 13 | **Slide 7 (body)** | "We modelled the response timeline for **five canonical Australian scenarios** — bushfire, riverine flood, tropical cyclone, urban-fire mass-casualty, **and pandemic surge**." | Spec 040 actually defines **seven** canonical scenarios: bushfire, flood, cyclone, urban-fire, mass-casualty, hazmat, marine SAR. **Pandemic surge is NOT one of them.** | "**Spec 040 defines seven canonical Australian scenarios — bushfire, flood, cyclone, urban-fire, mass-casualty, hazmat, marine SAR — each replayable baseline-vs-AMA-assisted with deterministic seed control.**" *(Already correctly stated on slide 27 — slide 7 should match.)* |
| 14 | **Slide 22 (col 1 — demo recap)** | "**Signal-to-recommendation: ~22s in this run.** … **Baseline run took 47 minutes for the same outcome — a 31× compression.**" + notes "**31× compression is the mean of three deterministic seed runs**" | These are fabricated demo measurements. No actual run produced these numbers. | "**Designed targets (per spec 040 SLOs):** signal-to-recommendation P95 <30s; recommendation-to-approval-request P95 <5s; end-to-end signal-to-alert-published P95 <90s. Baseline-vs-AMA-assisted compression to be reported per scenario in the Evidence Harness scorecard." |
| 15 | **Slide 22 (col 2)** | "~**45,000 simulated Lithgow & surrounds residents** addressable via Emergency Alert + ABC broadcast feed." | Lithgow urban population (2021 Census): **11,197**; the broader City of Lithgow LGA: **~20,000** (2020 estimate). 45,000 is overstated by ~2×. | "~**20,000 City of Lithgow LGA residents** addressable via Emergency Alert + ABC broadcast feed (Lithgow urban centre: 11,197 at 2021 Census)." |
| 16 | **Slide 28 (col 1, 2, 3) and Slide 43** | All AUD pricing: pilot **~$8,500/month**, state **~$45,000/month**, national **~$220,000/month**, plus all line-item prices on slide 43 (Foundry $2,800, Cosmos $1,200, etc.) | No Azure pricing calculator output, no `azd estimate` run, no FinOps workspace evidence in repo. These are guesses presented as "May 2026 Azure list prices in AUD" — they are not. | Either (a) **run the Azure Pricing Calculator** with the actual SKU list and reference its export in the slide; or (b) reframe the slide as an illustrative cost-shape, e.g. "**Indicative cost ladder — to be validated via Azure Pricing Calculator before pilot kickoff**" with order-of-magnitude bands rather than precise dollars. |
| 17 | **Slide 28 (col 3) + speaker notes** | "Productivity Commission's 2024 estimate of **$38B/yr nominal disaster spend**" + "the cost of *one* level-3 bushfire averages **$850M in direct loss**" | Neither figure is verified. The $38B/yr aggregate disaster spend figure is not something I can attribute. The "$850M average level-3 bushfire" is not a standard published statistic. | Replace with verified anchor: "**Black Summer 2019–20 alone cost an estimated A$100 billion** (Read & Denniss, *The Conversation*, Jan 2020 — the costliest natural disaster in Australian history). The platform's national-scale operating cost is a vanishingly small percentage of that loss curve." |
| 18 | **Slide 43 — ROI scenario** | "**One prevented level-3 escalation = ~$850M direct loss avoidance vs ~$2.6M annualised pilot+state operating cost**" | Both numbers are unsupported (see #16, #17). | Reframe as ratio rather than precise dollars: "**Black Summer 2019–20 = ~A$100B in losses. State-scale annualised operating cost is in the low single-digit millions. Even a fractional-percent reduction in the loss curve dwarfs platform TCO over a multi-year horizon.**" |

---

## 2. ⚠️ Items that are partially supported — recommend tightening

| # | Slide | Existing quote / claim | Issue | Recommended tighter wording |
|---|---|---|---|---|
| 19 | **Slide 3 (col 3)** | "$103B economic cost" | Actual published estimates cluster around **A$100B** (Read & Denniss, Jan 2020); $103B is slightly overstated and not a single canonical figure. | "**~A$100B economic cost** (Read & Denniss, *The Conversation*, 17 Jan 2020 — Australia's costliest natural disaster on record)." |
| 20 | **Slide 3 (col 2)** | "The 2022 Northern Rivers floods displaced 60,000 people" | I cannot verify "60,000 displaced" specifically. Wikipedia notes 27 deaths, 1,400 rapid-damage assessments in Lismore (900 uninhabitable), 3,000+ Lismore homes affected, and ~5,000 ADF deployed. Across both QLD+NSW the affected population was very large but the specific "60,000 displaced" number is not verified. | "**The 2022 eastern Australia floods (QLD + NSW) — Australia's fourth most costly global disaster of 2022 (~A$9.6B) — included Lismore's worst flood in recorded history; 3,000+ Lismore homes were affected and 900+ Lismore properties were declared uninhabitable**" (sources: AFR/Wikipedia). |
| 21 | **Slide 3 (col 2)** | "Twelve hours earlier would have changed the outcome." | Editorial opinion stated as fact. Has no source. | "**The 2022 NSW Independent Flood Inquiry concluded that warning, evacuation and inter-agency coordination failures contributed materially to the casualty count** — earlier, better-coordinated evacuation was a primary recommendation." (Source: NSW Government 2022 Flood Inquiry final report.) |
| 22 | **Slide 6 (col 3)** | "The Australian Warning System defines **3 levels and 10 principles**" | Verified but incomplete — Constitution (which is the source of truth) actually identifies **3 AWS levels + 10 Warning Principles + 6 elements of the Total Warning System**. The "3 levels and 10 principles" is correct as far as it goes. | OK as-is, or extend to "**3 AWS levels, 10 Warning Principles, and 6 elements of the Total Warning System**" (per AIDR Public Information & Warnings Handbook 2021 + AWS Companion 2022). |
| 23 | **Slide 9 (body)** | "MONITORING AGENT — ingests **50+ Australian sources**" | Same as #10 — actual is 46. | "ingests **~46 seeded Australian sources** (extensible)". |
| 24 | **Slide 14 (notes)** | "We seeded **~50** Australian data sources at launch" | Same — actual 46. | "We seeded **46** Australian data sources at launch — across 7 trust tiers." |
| 25 | **Slide 41 (notes)** | "**231 test files: 110 unit, 53 contract, 26 integration, 19 simulation, 10 benchmark, 6 devops, 2 e2e, 2 load, 2 pipeline**" | Outdated — current actual: **526 test_*.py + 5 e2e .spec.ts = 531 total**. Breakdown: 173 unit, 156 contract, 134 integration, 25 simulation, 6 benchmark, 10 devops, 0 pipeline, 5 e2e, 2 load. | "**531 test files: 173 unit, 156 contract, 134 integration, 25 simulation, 10 devops, 6 benchmark, 5 e2e, 2 load** (workspace at deck-build time). Branch-based dev/staging/prod per spec 031." |

---

## 3. ✅ Verified — no change needed

| # | Slide | Claim | Source |
|---|---|---|---|
| 26 | Slide 3 (col 1) | "**33 lives lost**" (Black Summer direct deaths) | Wikipedia / Royal Commission / NEMA — 33 direct + 417 indirect (smoke). |
| 27 | Slide 4 | "Six states, two territories" | Constitutional fact. |
| 28 | Slide 18 | "Mandarin, Arabic, Vietnamese, Cantonese, Punjabi (top-5 ABS Census non-English)" | ABS 2021 Census Cultural Diversity release: Mandarin 2.7%, Arabic 1.4%, Vietnamese 1.3%, Cantonese 1.2%, Punjabi 0.9%. |
| 29 | Slide 18 | "WCAG 2.2 AA on every render" | Spec 040 FR-037 commitment. |
| 30 | Slide 24 (notes) | "Governance Dashboard… **13 endpoints documented in spec 021**" | spec 021 tasks.md T011 / T031 explicitly list 13 endpoints. |
| 31 | Slide 24 (notes) | "Append-only audit container, Cosmos at Strong consistency, single AU region, **7-year Locked Blob immutability**. Tampering attempts return **409 Conflict** and write a tampering-attempt audit row." | Spec 040 FR-038, FR-040, FR-044, Cycle 2 Round 2 Q2. |
| 32 | Slide 24 (notes) | Rego policies: "au_region, cross_env, identity_consistency, posture, secret_hygiene, safety-guardrails, tenant-isolation" | Verified in workspace memory. |
| 33 | Slides 17, 22, 38 | "Typed AgentHandoffEvent. **3 retries within a 300s window.** Failed handoffs land in dead-letter container." | Codebase (`apps/agents/common/handoffs.py`). |
| 34 | Slide 26 | All five capstone KPIs (≥1,000 lives, ≥50% response time, ≥24h evac lead, ≥30% logistics, ≥30% econ loss) | spec 015 SC-CAP-015-001..005 + spec 040 owned criteria. |
| 35 | Slide 26 | "Per-KPI determinism tolerance **±2% / ±1 absolute**" | spec 040 Round 1 Q1. |
| 36 | Slide 26 | "Risk-adjusted variant computed via **5×5 likelihood × consequence matrix per AS/NZS ISO 31000**" | spec 040 Round 1 Q3. |
| 37 | Slides 26, 27, 32 | "Bootstrap **95% CI** over **≥1,000 resamples**; ±1 SD fallback labelled small-sample" | spec 040 Round 1 Q2. |
| 38 | Slide 32 | "Burn-rate alerts at **2%/h and 5%/h**, **30-day SLO horizon**, Sev1 (5%/h pages) and Sev2 (2%/h tickets)" | spec 040 Cycle 2 Round 1 + Round 2 Q3. |
| 39 | Slide 33 | "We wrote **40+ specifications**" | Verified: 42 spec dirs (matches "40+"). |

---

## 4. Patch plan (recommended)

If you want, I can apply the following changes in one pass to both `scripts/build_capstone_presentation.py` and `docs/ama-presentation/AMA_Capstone_QnA.md`:

1. **Slide 3** — replace fabricated stats (Lives ✓, homes 3,500→3,000+, $103B→~A$100B), drop the "$35B/yr by 2050" claim, fix Royal Commission "31 of 80" attribution.
2. **Slide 4** — drop the AFAC "25–35% by 2040" projection unless I can find a real source.
3. **Slide 5** — fix persona counts (10 / 58 / 17 / 85+).
4. **Slide 6** — drop "600 signals/hour" and "industry timing studies show 4–6 hours" fabrications.
5. **Slide 7** — replace the "4.2 hours" fabrication with the spec-040 baseline-harness framing; correct "five canonical scenarios" → "seven canonical scenarios".
6. **Slide 9, 14** — change "50+ Australian sources" to "~46".
7. **Slide 22** — replace fabricated demo numbers with design SLOs; fix Lithgow population.
8. **Slide 28, 43** — re-baseline cost ladder either by running Azure Pricing Calculator or by reframing as illustrative bands; replace "$38B/yr disaster spend" and "$850M level-3" anchors with the verified A$100B Black Summer figure.
9. **Slide 41** — update test counts to 531 with correct breakdown.
10. **Q&A document** — same fixes mirrored in answers A1, A2, A10, B13.

Just say the word and I will regenerate the deck and Q&A doc with the substitutions above. The ones I can't repair without external sources (#3 ICA, #5 Productivity Commission, #7 AFAC, #16 Azure pricing) I'll either drop, mark "indicative", or leave as TODOs depending on your preference.
