# Capstone Q&A Brief — Autonomous Disaster Response Agent Coordination Hub

> Companion to `AMA_Capstone_Disaster_Response_Hub.pptx`.
> **Audience:** Microsoft Cloud Solution Architect (CSA), Specialist Manager (SSP-M), Business Delivery Manager (BDM).
> **Format:** Each entry has a **role tag** (who is most likely to ask), the **question**, the **30‑second answer** (what you say first), and **depth** (anchors and follow-up evidence).
> **Survival rule:** Repeat the question, anchor in the Constitution or a spec, then give the 30‑second answer before depth. Never bluff a number — point at `specs/040-success-criteria/` instead.

---

## Section A — 20 Expected Questions

### A1. *(BDM)* What is the actual business problem in one sentence?
**30s answer:** In Australian disasters, coordination latency — not detection, not capability — is the dominant driver of lives lost and dollars destroyed; we cut that latency by ≥50% with an AIIMS-aligned multi-agent platform.
**Depth:** Royal Commission into National Natural Disaster Arrangements (2020) named coordination as the primary improvement opportunity in 31 of its 80 recommendations. Productivity Commission 2024: 97% of disaster spend is reactive. Our success criterion is owned by `specs/015-performance-benchmarks/` and instrumented by `specs/040-success-criteria/`.

### A2. *(BDM)* What's the ROI? When do we break even?
**30s answer:** A 90-day shadow-mode pilot lands inside a ~AUD $30k envelope. State production runs at ~AUD $45k/month. One prevented level-3 escalation in a year of operation avoids ~AUD $850M in direct loss. Break-even is one event, in any year, in any state.
**Depth:** ROI scenario in slide 43; full cost ladder in `docs/ama-presentation/AMA_Capstone_Disaster_Response_Hub.pptx` slide 28. ICA 2024 reports cyclone Debbie at AUD $1.7B; Northern Rivers floods at AUD $5.7B. Even partial loss avoidance dwarfs operating cost. We instrument cost-per-incident and cost-per-language-channel directly in App Insights.

### A3. *(SSP-M)* How do you measure success?
**30s answer:** Five Sendai-aligned KPIs — modelled lives saved, response-time reduction, evacuation lead-time, logistics efficiency, modelled economic loss — each with a bootstrap 95% confidence interval, owned by an Evidence Harness (spec 040), reproducible against a deterministic baseline simulation.
**Depth:** Each KPI carries nine attributes (formula, unit, owner role, refresh cadence, target, alert threshold, baseline source, provenance, confidence band). Determinism tolerance ±2% / ±1 absolute. Risk-adjusted variants use AS/NZS ISO 31000 5×5 likelihood × consequence. Operational SLOs separately tracked with 2%/h and 5%/h burn-rate alerts on a 30-day horizon.

### A4. *(CSA)* Why multi-agent vs. one large model + tool calls?
**30s answer:** A multi-agency problem needs a multi-agent shape: each agent maps 1:1 to an AIIMS function, has a typed handoff contract, an isolated failure domain, and a deterministic fallback. One monolithic model is one blast radius.
**Depth:** Five agents — Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication. Handoff is `AgentHandoffEvent` with 3 retries inside a 300s window then dead-letter. Reflection guardrail sits between Risk and Communication. Lose any single agent or model and the rest keep running with templated fallback (constitutional non-negotiable #5).

### A5. *(CSA)* Why Microsoft Foundry / Agent Framework?
**30s answer:** Foundry GA Q1 2026 gives us managed-identity-everywhere, RAG-grounded agents with mandatory citations, model-portability across Azure OpenAI deployments, and a content-safety perimeter we don't have to build. Agent Framework provides the orchestration primitive without bespoke plumbing.
**Depth:** Dual deployment — "reasoning" (GPT-4 class) and "drafting" (low-latency multilingual). Foundry RAG grounds against the AIDR handbook collection. Model gateway enforces token budgets, content-safety, prompt-shielding, and the data-minimisation rules required for the AU-residency carve-out (Constitution v1.2.0 §2).

### A6. *(BDM)* Who pays for it? Who is the buyer?
**30s answer:** The buyer is a state emergency-services agency (e.g., NSW RFS, EMV) with discretionary innovation budget for a 90-day pilot. The expansion buyer is the state Treasury / Premier's Department, justified against the avoided-loss curve. NEMA is the federal partner for cross-jurisdiction reach.
**Depth:** Pilot fits inside existing innovation envelopes. State production needs an MoU but not new legislation. National scale needs ANZEMC alignment. We are deliberately a peer, not a hub — agencies retain authority and data sovereignty over their own jurisdiction.

### A7. *(SSP-M)* What's the competitive landscape? Who else is doing this?
**30s answer:** No one is doing this AIIMS-aligned, multi-agency, multilingual, sovereign-by-design combination. EMSINA tools cover ICS workflow but not multi-agent reasoning. Palantir Foundry is generic and not Australian. Existing sector tools (Guardian IMS, WebEOC) are single-agency. Our moat is interop (CAP/EDXL/GeoJSON) plus AU-sovereign Foundry.
**Depth:** Differentiation in slide 30 — Australia first, regional reference architecture next. CAP/EDXL/GeoJSON in, OpenAPI 3.1 out. We integrate with EMSINA tools, we don't replace them. Pacific Island Forum is the first reference customer beyond AU/NZ.

### A8. *(CSA)* What's your data residency story? Foundry isn't fully AU yet.
**30s answer:** Constitution v1.2.0 §"Non-Negotiable #2" — all data stays in AU East/Southeast. There is **one bounded exception**: Foundry model-hosting endpoints may sit non-AU when the model isn't yet GA in AU, never for data persistence, only behind a data-minimisation gateway, only on a named auto-revoking carve-out list.
**Depth:** Cosmos audit container is `Strong` consistency in a single AU region (Strong is impossible across regions, so it's mutually reinforcing). Blob immutability `Locked` for 7 years. The carve-out auto-revokes when the model lands in AU East. The list is auditable: every entry has model name, region, justification, approver, review date.

### A9. *(BDM)* How long until you can demo this to a real agency?
**30s answer:** Today. The deck includes a live demo of the Blue Mountains bushfire scenario; the same simulation harness runs against any of seven canonical scenarios (bushfire, flood, cyclone, urban-fire, mass-casualty, hazmat, marine SAR). For an agency proof, 90 days to shadow-mode integration with one read-only signal stream.
**Depth:** Demo recovery: pre-recorded fallback at `docs/canary/demo-recording.mp4`. Quickstart docs at `docs/runbooks/`. Shadow mode is observe-only — bounded downside, scoreable upside.

### A10. *(SSP-M)* Where's the Microsoft consumption / ACR?
**30s answer:** Foundry inference, Azure OpenAI, Azure AI Search (RAG), Cosmos DB, Container Apps, Azure Communication Services, Azure Maps, Service Bus, Event Grid, Key Vault, Application Insights, Log Analytics, Front Door, Static Web Apps, Storage immutable. Pilot ~AUD $8.5k/month, state ~AUD $45k/month, national ~AUD $220k/month — all Azure-native.
**Depth:** Cost ladder slide 28 + line items slide 43. Sensitivity: ACS message volume is the single largest variable; targeted warnings cut alert spend ~40% vs broadcast. AI inference is **not** the dominant line item.

### A11. *(CSA)* What's the SLO and how do you know you're meeting it?
**30s answer:** Three operational SLOs on a rolling 30-day horizon: signal-to-recommendation P95 <30s, recommendation-to-approval-request P95 <5s, alert-publish-after-approval P95 <60s. Burn-rate alerts at 2%/h (Sev2 ticket) and 5%/h (Sev1 page) per Google SRE Workbook fast-burn convention.
**Depth:** Audit-write durability is 100% before HTTP refusal — Cosmos `Strong` per-operation override on the audit container, 3-retry exponential backoff (250ms / 1s / 4s), 503 + ProblemDetails on persistent failure (FR-044 / FR-045 of spec 040).

### A12. *(CSA)* What about hallucination? It's life-safety.
**30s answer:** Three layers. Foundry RAG grounds every agent on the AIDR handbook collection with mandatory citations. A reflection guardrail critiques every Risk recommendation against the ten Warning Principles before the Communication agent ever sees it. A 3-tier fallback (LLM → templated → safety) means the platform always produces a defensible alert. And every public-facing action requires a named human approver before publish.
**Depth:** Constitutional non-negotiable #1 — no irreversible action without human authorisation. Content safety: Azure AI Content Safety + domain-specific blocked-keyword list (kill, attack, bomb, terror, hate). Plain-English Grade-8 reading level enforced as a content rule.

### A13. *(SSP-M)* How does this co-sell with Security Copilot / Microsoft 365 Copilot / Defender?
**30s answer:** Adjacent, not overlapping. Security Copilot defends the platform (Sentinel + Defender XDR for the AMA tenant). M365 Copilot is the Incident Controller's productivity surface during a response (briefing pack drafting, executive-summary generation). The platform itself is the operational system — they amplify each other.
**Depth:** Foundry agents can call M365 Copilot Studio actions for org-internal tasks (e.g., draft a SitRep in Word, schedule a Teams briefing). Sentinel ingests every audit row from the Locked Blob mirror.

### A14. *(BDM)* What if an agency says no?
**30s answer:** They get value from day one without saying yes. Read-only ingest of any authoritative public stream (BoM, RFS Fires Near Me, ABS) needs no agency commitment. We accrete sector agents over time as evidence builds. We are deliberately a peer, not a hub-and-spoke owner.
**Depth:** Slide 31 risk register names this explicitly. Adoption curve is shadow → MoU-bounded live → multi-jurisdictional. No agency is asked for production-channel risk before a measured pilot has run.

### A15. *(CSA)* What about deepfake / adversarial signals on social media?
**30s answer:** Every signal carries a trust tier (1 = authoritative government, 7 = derived). Tier 6 social signals (Twitter/X, Facebook, Reddit) are advisory-only and cannot solo-trigger a public alert. Cross-tier corroboration is required. Provenance and confidence-banding (≥0.80 = high, 0.50–0.79 = medium, <0.50 = low) gate publication.
**Depth:** Trust-tier model in `packages/domain/src/domain/seed/data_sources_australia.json`. Low-confidence signals (<0.50) cannot contribute to a published KPI value unless flagged advisory-only and labelled reduced-fidelity (FR-024 / FR-027).

### A16. *(BDM)* Can this scale to national / commonwealth?
**30s answer:** Yes — Phase 4 of the roadmap. Architecture is multi-tenant by jurisdiction tuple from day one (Cosmos partition key + Rego policy layer). Cross-jurisdiction visibility is governed, never default. NEMA / NJCOP integration is named as a future state in the Constitution.
**Depth:** Multi-jurisdiction tenancy diagram on slide 15. WA cannot see VIC PII. NEMA can see anonymised cross-cohort metrics. Cost at national scale ~AUD $220k/month — vanishingly small vs the $38B/yr Productivity Commission disaster spend baseline.

### A17. *(SSP-M)* Does this need new legislation?
**30s answer:** No for shadow-mode pilot. No for state-level production under an existing MoU. Yes for a future commonwealth COP if it ever became authoritative — but that is two phases away and policy work, not engineering work.
**Depth:** Privacy Act 1988 compliance is contract-tested. PSPF Protected handling is encoded. Each jurisdiction has its own privacy law (NSW, VIC, QLD, WA, SA, TAS, NT, ACT) — handled via JurisdictionPolicy entities (data classification + visibility rules per jurisdiction).

### A18. *(CSA)* What's your CI/CD and testing posture?
**30s answer:** GitHub Actions, branch-based dev/staging/prod (per spec 031). 231 test files: 110 unit, 53 contract, 26 integration, 19 simulation, 10 benchmark, 6 devops, 2 e2e, 2 load, 2 pipeline. Bicep with What-If gates. Rego policy bundle runs on every PR. Azure deployment via `azd`.
**Depth:** CI runs ruff + pytest (contract+integration) + tsc + Next build + perf benchmarks. CD is workflow_run-triggered, deploys via azd to staging then prod with health-check + auto-rollback. PRs that introduce a non-AU data resource fail the pipeline at What-If.

### A19. *(BDM)* What does a successful 90-day pilot look like?
**30s answer:** A signed scorecard against the five capstone KPIs, comparing baseline vs AMA-assisted across at least three canonical scenarios. A named Incident Controller who has run a weekly Friday tabletop with the platform. A go/no-go decision conversation against pre-agreed exit criteria.
**Depth:** Exit criteria are pre-agreed before pilot starts. Spec 040 instrumentation is the source of truth for measurement. Bootstrap 95% CIs on every KPI value mean we never claim a delta we can't defend statistically.

### A20. *(SSP-M)* Where does this go after the capstone?
**30s answer:** Two paths. (1) Production: a state-services pilot with NSW RFS or EMV as foundation customer. (2) Reference architecture: published as an Australian Government Architecture pattern, becoming the pattern allied nations (NZ, Pacific Island Forum) adopt. Microsoft positions as the platform of choice for sovereign multi-agent emergency management.
**Depth:** Constitution v1.2.0 explicitly names ANZEMC governance and NCM integration as forward-roadmap. Reference-architecture portability is a design property, not a marketing claim — the metric-trace artefact (`specs/shared/capstone-metric-trace.md`) names every AU-only assumption and what would change for a regional deployment.

---

## Section B — 20 Unexpected Questions

### B1. *(BDM)* My cousin lost their house in Black Summer. Can your system actually have prevented that?
**30s answer:** I won't claim that. What I can claim is that the Royal Commission named coordination delay as the primary improvement opportunity, and our system targets that delay with measurable, statistically-defensible KPIs. We turn an unmeasurable hope ("if only we had been faster") into a measurable practice.
**Depth:** Be human. Don't oversell. Counterfactual lives-saved per spec 040 FR-007 is computed as `baseline-fatalities − AMA-assisted-fatalities` per canonical scenario and scaled per Sendai indicator A-1. It is a *modelled* counterfactual, never a production claim. The spec carries that disclaimer explicitly.

### B2. *(SSP-M)* What if a future government decides to use this for surveillance?
**30s answer:** The Constitution forbids it structurally. Every persona is bounded to an AIIMS function with explicit data scope. PII transit is denied at the model gateway. Audit is append-only and immutable for 7 years — any misuse leaves an indelible trail. We can't architect around future bad actors, but we can make misuse expensive and detectable.
**Depth:** Slide 25 (privacy & cultural authority) plus Constitution Principle IV (Transparency & Auditability). Tampering attempts return 409 Conflict and write a tampering-attempt audit row themselves. Indigenous Relations sector agent is consulted for any incident touching declared Country — surveillance use would have to traverse that gate.

### B3. *(CSA)* Could you have built this without Microsoft?
**30s answer:** Yes — and badly. The Australian-sovereign agent platform with managed identity, Foundry RAG grounding, content safety, and a Locked-Blob immutability primitive doesn't exist as cleanly outside Azure. Could we cobble it together on AWS or GCP? Yes. Would it ship in a capstone window with this rigour? No.
**Depth:** Honest answer wins trust. Foundry GA Q1 2026 is the unlock. Managed Identity end-to-end + Cosmos `Strong` per-operation + Azure AI Search RAG + ACS multilingual delivery is an integrated path on Azure that requires bespoke glue elsewhere.

### B4. *(BDM)* What happens when the LLM costs go up 10× next year?
**30s answer:** AI inference is not the dominant line item — ACS message volume is. The model gateway is purpose-routed (reasoning vs drafting), so we can swap the drafting model for a smaller open-weight deployment without changing the agent contract. Worst case: the 3-tier fallback runs the system on templated alerts indefinitely.
**Depth:** Cost detail in slide 43. Foundry models are ~AUD $2,800/month at pilot; ACS is ~AUD $1,000 at pilot but ~AUD $20k+ at state scale. Targeted warnings (jurisdiction-bounded geofence) cut alert spend ~40%. Model substitution is a config change, not a re-architecture.

### B5. *(SSP-M)* Why didn't you call this "Disaster Copilot"?
**30s answer:** Because it isn't one. Copilot is a productivity surface for an individual user. This is an operational system that coordinates multiple agencies and authorises real-world action. The name matters — calling this a Copilot would mis-set expectations on autonomy, accountability, and approval flow.
**Depth:** Naming honesty. M365 Copilot is complementary (slide-style A13). The system has agentic autonomy *bounded by a human approver* for any irreversible action. Marketing it as a Copilot would obscure the human-in-the-loop guarantee.

### B6. *(CSA)* What's the carbon footprint of running this?
**30s answer:** Lower than the disasters it helps avoid. Pilot ~AUD $8.5k/month maps to roughly 200-400 kgCO₂e/month of Azure consumption (Microsoft sustainability calculator estimate). One avoided level-3 escalation prevents emissions on a different scale entirely (1 hectare of bushfire ≈ 50-100 tCO₂e).
**Depth:** Honest qualifier — I'd validate this in production with the Azure Emissions Impact Dashboard. Foundry's PUE is industry-best in AU East. The dominant operational footprint is ACS network — that's a pre-existing carrier emission, not new.

### B7. *(BDM)* Have you talked to actual Incident Controllers about this?
**30s answer:** The personas are derived from AIIMS handbook role definitions and AFAC published work patterns; the platform itself encodes the AIDR handbook collection (Incident Management, Evacuation Planning, Public Information & Warnings, Recovery, M&E Framework, Community Recovery). For a real production conversation, the 90-day pilot starts with weekly tabletops with a named Incident Controller — that's part of the ask.
**Depth:** Be honest about pre-pilot validation level. Persona definitions are in `.github/agents/` and follow the AIIMS contract documented in `specs/027-spec-hardening/contracts/persona-profile.md`. Tabletop validation is the explicit pilot exit-criteria conversation per slide 34.

### B8. *(SSP-M)* What's the worst thing the system could do to a real person?
**30s answer:** Fail to publish a warning that would have saved their life, or publish one that triggers a panic in the wrong direction. We architect against both: 3-tier fallback so the platform *always* produces an alert, named human approval so no alert publishes without authority, content safety + reflection guardrail so what publishes is defensible.
**Depth:** Don't deflect. This is the right question. Constitutional non-negotiable #1 (HITL) and #5 (graceful degradation) are the structural defences. Spec 040 KPI list includes "manual-row share per artefact ≤50%" — publication blocks if humans are doing too much of the work, because that means the system is degrading invisibly.

### B9. *(CSA)* Why TypeScript on the front-end and Python on the back-end?
**30s answer:** Because that's where each ecosystem is strongest. Python has the AI/agent libraries and is the lingua franca of the AIDR research community. Next.js + TypeScript is the most maintainable path for an accessible, multilingual operator UI. The contract between them is OpenAPI 3.1 + JSON Schema.
**Depth:** TS twins of domain models live in `packages/domain/src/` — type-only, with schema parity asserted by contract tests against the OpenAPI document. No new runtime validators (no Zod) by deliberate convention to keep Python the source of truth (per spec 040 Cycle-2 Round-2).

### B10. *(BDM)* Could the system be wrong, and still publish a wrong alert because the human approver was tired?
**30s answer:** Yes — and that's a known risk we mitigate, not eliminate. The Communication agent presents a structured approval surface (signal provenance, recommendation explanation, AWS level rationale, language-channel preview), not a rubber-stamp button. Approvers are named and audited. Repeated wrong approvals show up in the M&E framework.
**Depth:** AIIMS structure means the *role* is accountable, not the individual. Constitution Principle IV (Transparency & Auditability) means every approval carries the approver's identity, the recommendation chain they reviewed, and the basis for their decision. Lessons-management (Quality Gate §) feeds approver fatigue patterns back into UX iteration.

### B11. *(SSP-M)* Did you use Copilot to build this?
**30s answer:** Yes — extensively, and visibly in the repo. We followed a spec-driven workflow with GitHub Copilot Agents and the Spec-Kit pattern. 40+ specs were written before significant code. Copilot accelerated implementation; the *thinking* — the constitution, the AIIMS alignment, the carve-out design — is human.
**Depth:** Show the spec catalogue (`specs/001-disaster-response-hub/` through `specs/040-success-criteria/`). Each spec carries Assumptions / Personas / Hypotheses / Out of Scope per spec 028. Constitution v1.2.0 is the human-authored spine. Copilot Agents wrote first-draft Bicep, Pydantic models, FastAPI handlers — all human-reviewed.

### B12. *(CSA)* What if Azure has a region-wide outage during a real bushfire?
**30s answer:** Active-passive across AU East and AU Southeast. Read-only mode with banner if the primary fails. Cosmos multi-region replication is `Session` for everything except the audit container (which runs `Strong` per-operation and is deliberately single-region — the trade-off is intentional). Recovery is automated; failover targets are tested in CI.
**Depth:** Slide 38 (graceful degradation sequence) + slide 40 (WAF reliability pillar). RTO target <15 minutes, RPO <60 seconds for non-audit data. The audit container's single-region constraint means a true AU East outage degrades audit-write throughput, but never violates the append-only invariant — degraded mode is documented behaviour.

### B13. *(BDM)* Are you really going to save 1,000 lives a year?
**30s answer:** That number is the **modelled-counterfactual upper bound** scaled per Sendai indicator A-1, not a production claim. The honest pitch is: cut coordination latency by half, reach vulnerable populations 24 hours earlier, and the historical curve says lives saved is in the hundreds-to-thousands range per major disaster avoided.
**Depth:** Spec 040 FR-007 carries the disclaimer explicitly. Be the architect who says "modelled" before "saved". Reference Sendai Framework for Disaster Risk Reduction 2015-2030 indicator A-1 (mortality) and the spec 015 SC-CAP-015-001 anchor.

### B14. *(SSP-M)* What's the single biggest reason this might fail?
**30s answer:** Adoption inertia, not technology. Australian emergency management is federated, justifiably cautious, and burnt by past tech promises. We mitigate by being a peer, by accruing value before asking for commitment, and by keeping the burden of proof on us via the Evidence Harness.
**Depth:** Slide 31 risk register. Honest answer wins. Technical risks (model risk, sovereignty risk) are bounded and documented; adoption risk is the open one. Mitigation = shadow-mode pilot + measurable scorecard + no-cost-to-agency entry path.

### B15. *(CSA)* Why didn't you use Semantic Kernel / LangGraph / CrewAI?
**30s answer:** Microsoft Agent Framework is the supported, GA-aligned path on Foundry, with managed identity end-to-end and a clean handoff primitive. Semantic Kernel was an option earlier; we picked MAF after spec 033 (`033-maf-adoption`) for first-class observability and the lifecycle alignment with Foundry. Open-source alternatives don't have the AU-sovereign managed-service path.
**Depth:** Spec 033 documents the decision. Reflection, handoff, and dead-letter patterns we'd have built ourselves on LangGraph; on MAF they're primitives. We retain portability via OpenAPI + Pydantic at the agent boundary.

### B16. *(BDM)* What if a Premier wants to use this to claim political credit?
**30s answer:** They'd have to share the credit with the system, the operators, and the auditor — every action is traceable to a named human. Politics is healthy; capture is not. The Governance Dashboard publishes the same data to operators, executives, and (with appropriate redaction) the public.
**Depth:** Constitution Principle IV makes provenance non-negotiable. Slide 24 (governance dashboard, append-only audit, Rego policy). Every action sits in the chain: signal → fusion → recommendation → approval → publish → audit. No political actor can claim a pure decisive action that wasn't, in fact, made by a named Incident Controller.

### B17. *(SSP-M)* Can you sell this in a Microsoft ELA conversation?
**30s answer:** Yes — as a sovereign reference architecture for emergency management, alongside Sentinel, Defender, Foundry, and ACS. It is not a SKU; it is a published architecture pattern that pulls Azure consumption with credible TCO/ROI. The state EM agency is the customer; Microsoft Australia FastTrack is the delivery accelerator.
**Depth:** Multi-million-dollar Foundry/Azure consumption envelope at state scale. National scale is ELA-class. Co-sell motion: Foundry SSP-M + Industry SSP (Public Sector / Public Safety) + CSA architecture lead. Reference-architecture publication amplifies the motion across allied nations.

### B18. *(CSA)* What does the system do during the Recovery phase, weeks after the event?
**30s answer:** It transitions to a Recovery agent set (out of capstone scope but architected for) covering the four AIDR Recovery Environments — Social, Built, Economic, Natural — under the six National Principles for Disaster Recovery. Recovery is planned for from response onset (Constitution VII-C); handover is managed, not abrupt.
**Depth:** Constitution Section VII (Recovery Support) is fully specified. Spec 018 (`018-aidr-guidance-integration`) is the authoritative owner of recovery-phase work per the spec 028 ownership ruling. Sequence diagram at `docs/architecture/sequence/recovery-transition.png`.

### B19. *(BDM)* Have you spoken to NEMA?
**30s answer:** Not in production form — this is a capstone. The Constitution is explicit that the platform must be capable of integrating with the National Coordination Mechanism and the National Joint Common Operating Picture. That conversation is Phase 4 of the roadmap, after a state-services pilot proves the model.
**Depth:** Be honest. Constitution Section "National Coordination" makes integration mandatory but unbuilt. Phase 4 (year 2) of slide 29 roadmap. The architecture pattern (jurisdiction tuple + standards-based interop) is designed to make NEMA integration an additive change, not a re-architecture.

### B20. *(SSP-M)* What does Microsoft get out of this beyond consumption?
**30s answer:** Three things. (1) A defensible reference architecture for sovereign multi-agent AI in regulated industries. (2) A public-sector lighthouse customer story for Foundry + Agent Framework + ACS. (3) An export pattern to allied nations. The capstone proves the pattern; the production pilot proves the customer.
**Depth:** Sovereign multi-agent AI is an emerging conversation in every regulated industry — health, financial services, defence. This pattern transfers. Foundry's strongest enterprise narrative needs a regulated-industry lighthouse; emergency management is one of the highest-stakes versions of that.

---

## Quick-reference cheat sheet (for the panel notes pad)

| Anchor | Where it lives |
|---|---|
| Five capstone KPIs | `specs/015-performance-benchmarks/` (own); `specs/040-success-criteria/` (instrument) |
| Constitution v1.2.0 | `.specify/memory/constitution.md` |
| Foundry carve-out rules | Constitution §"Non-Negotiable #2" (Data sovereignty) |
| HITL guarantee | Constitution §"Non-Negotiable #1" |
| Graceful degradation | Constitution §"Non-Negotiable #5"; sequence in `docs/architecture/sequence/graceful-degradation.png` |
| Cost detail | Slide 28 (ladder) + slide 43 (line items) |
| ROI scenario | Slide 28 + slide 43 footer |
| Architecture (C4) | `docs/architecture/c4/` (system, container, component-agents) |
| Sequence diagrams | `docs/architecture/sequence/` (alert-approval-publication, monitoring-risk-comms, audit-provenance, graceful-degradation, recovery-transition) |
| Personas | `.github/agents/` (operational + sector + technical) |
| Test posture | 231 test files; CI/CD spec 031 |
| 90-day pilot | Slide 34 (the ask) |
| Roadmap to national | Slide 29 + slide 30 |
| Recovery phase | Constitution §VII; spec `018-aidr-guidance-integration` |

## Survival rules (to mentally rehearse)

1. **Repeat the question** before answering — buys five seconds and makes you look unhurried.
2. **Anchor in evidence** — Constitution clause, spec ID, or diagram path. Never bluff.
3. **30 seconds is the answer; the rest is depth** — let them decide if they want depth.
4. **Be human on human questions** (B1, B10, B13, B16) — don't deflect with architecture.
5. **"I don't know — let me come back to you with the audit row"** is a winning answer.
6. **Distinguish capstone from production** loudly and often. We are demonstrating measurable capability, not making operational claims.
7. **Microsoft staff are co-conspirators**, not adversaries — frame answers in their language (consumption, co-sell, lighthouse, ELA, FastTrack).
