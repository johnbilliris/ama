# Spec-035 — Technical Panel Input Brief

**To**: All 17 agents in `.github/agents/technical/`.
**From**: Spec author.
**Subject**: We need user requirements and clarifications for spec-035 — Web Application Capstone Closure.

## Why you are being asked

Spec-034's job was validation; spec-035's job is **building the workflows** the validation suite asserts against. The operational + sector panels have surfaced sizeable UI gaps (see `operational-brief.md`, `sector-southwest-brief.md`, `sector-tc-brief.md`). Closing those gaps requires architecture, infrastructure, identity, AI, observability, security, and accessibility decisions that only your panel can underwrite. Constitution v1.2.0 binds; spec-034 OOS clauses bind; AVM-first binds.

## Architectural questions to answer

### Solution Architect / Azure Principal Architect / Principal Engineer

1. Should the new persona-depth UI be implemented as **Server Components + RSC streaming** (current Next.js 16 pattern) or shift any specific persona to **client-side state machines** (e.g. XState) for workflow correctness — for example IC approval, PIO publish flow, Field-Coordinator offline?
2. The PIO multilingual AWS composer needs Microsoft Foundry for translation drafts. Foundry resource model: shared multi-tenant project at `cog-ama-zo6bb5` or per-jurisdiction project? AU sovereignty constraints (constitution §V-C, NN-1) must hold.
3. Offline + degraded-comms (Field Coordinator + WA Kimberley + TAS islands + NT remote): Service Worker + IndexedDB + Background Sync vs. native PWA install vs. Azure Front Door + edge-cached fallback. Pick one.
4. RBAC for SA control-centre, AFP for ACT national-capital, ATSI / palawa elder approval — all via Microsoft Entra ID app roles? Spec-034 OOS-007 said no IdP changes; spec-035 may need to revisit.
5. Append-only audit + tamper-resist UX: how do we surface immutability in the UI without leaking implementation? Cosmos analytical store + append-only patterns are already in use; the UI surface is the gap.

### Software Developer / API Architect

6. The capstone evaluator endpoints `/api/outcomes/sc-{001..005}/evaluate` are currently dual-guarded for dev/test only (Q25/Q29). Spec-035 must extend them to production with appropriate auth (Entra ID app role) and rate-limit. Surface the contract changes needed.
7. `/api/audit/list` pagination contract: sort key, max page size, cursor format. Spec-034 cycle-1 wired the route — what production-grade contract do we promote?
8. The 13 net-new persona scenarios (T187..T199) each need a backend surface (RBAC view, multi-LGA evac, ATSI messaging, JATWC handoff, etc.). Each needs an API contract — name them and propose the shape.

### Data Engineer

9. Recovery handover artefact (Resilience Planner) must be downloadable, signed, and immutably referenced. Cosmos + Storage immutable container vs. signed-blob shelf — recommend.
10. Insurance recovery + economic recovery surfaces will need new domain entities (claims, grants, recovery KPIs). Where do they live in `packages/domain`? Are they part of the existing seed-data shape (must be additive only per spec-035 brief) or a new partition?
11. ATSI / palawa language packs: where are they stored? Cosmos `language_pack` partition? Static blob? Configurable per-jurisdiction?

### Security Engineer / Compliance Auditor

12. AU sovereignty + Foundry carve-out surfacing in the UI: where does the model-source label live, who can see it, and how is it audited? Constitutional anchor: NN-1.
13. Tamper-attempt UX (Observer-Auditor): when a user clicks "edit audit", what is the correct UX? Hard 4xx vs. allow-then-rollback vs. simulation-only sandbox? Recommend.
14. ABF / AFP / ASA roles bring classified-overlay constraints (OFFICIAL: Sensitive). Are we ready to surface PROTECTED-or-higher data? If not, spec-035 must explicitly defer.
15. Capstone evaluator extending to production: what is the auth model? Entra ID role + rate-limit + per-route audit?

### QA / Test Engineer / Accessibility Tester

16. The spec-034 web-coverage suite is read-only for spec-035. If a depth-profile assertion is wrong, we amend the YAML, not the implementation. Confirm.
17. Accessibility for AWS composer: WCAG 2.2 AA. Constitution NN-3. The composer needs alt-text validation, language-tag attributes, keyboard navigation, screen-reader announcement. Spec out the testable contract.
18. Multilingual fallback chain: en → community-language → en. The PIO test asserts both. UI must visibly fall back without silent translation drop.

### SRE Engineer / Chaos Engineer / DevOps

19. Offline-first PWA + Background Sync: SLO for sync-on-reconnect (e.g. ≤ 30 s for queued events of size N to land in audit). Define.
20. Capstone evaluator production rollout: feature-flag (App Configuration), canary in `dev` → `staging` → `production` per ADR-031. Confirm the rollout mechanism.
21. Chaos targets: which new surfaces should we deliberately fail in chaos days (offline replay, evaluator timeout, ATSI elder-approval fan-out)? Recommend a minimal chaos plan.

### AI/ML Engineer

22. AWS warning composer translation via Foundry: model selection (`gpt-5.4-ama`?), temperature, prompt-template registry, fallback to human-only when model output low-confidence. Recommend a contract.
23. JATWC handoff: BoM tsunami warning → AI summary → human approve → publish. AI is advisory only; gating must be explicit. Constitutional anchor: NN-2.
24. Cultural-safety guardrails for ATSI / palawa templates: how does the AI avoid disrespectful output? Foundry content-safety policy + reviewer in loop. Recommend.

### Docker & Container Engineer / UX Designer / Product Owner

25. Front-end build size will grow (multilingual packs, new components). Confirm Next.js 16 standalone build still fits the App Service plan, or recommend a switch to Container Apps for the web tier.
26. UX for offline + degraded mode: degraded-mode banner, pending-sync indicator, error-state recovery affordances. Spec out the design system extension.
27. Product backlog ordering: out of the operational + sector + technical gaps, which should ship first? Recommend a P0 / P1 / P2 split aligned to capstone severity.

## Asks of you

For each numbered question above, please return:
1. The recommended technical decision
2. Constitution / ADR / spec-034 anchor that justifies it
3. Acceptance criteria for the implementation
4. Risks (especially anything that would force a NN- or QG- exception)
5. Net-new Azure resources required (if any), per AVM-first policy
6. Test approach — what spec-034 web-coverage tests will exercise this; what new unit / integration / contract tests are needed
