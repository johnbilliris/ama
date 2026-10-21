# Static Implementation Audit: Disaster Response Coordination Hub

Review date: 2026-09-11. Source revision: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`.

## Scope and Limitations

This isolated, review-only audit applies the [Review Contract](../001-spec-implementation-audit/README.md#L13),
[review instructions](../../.github/instructions/code-review.instructions.md#L1), and
[constitution](../../.specify/memory/constitution.md#L1) to this feature.
The original [specification](spec.md#L1), [tasks](tasks.md#L1), and [plan](plan.md#L1) are the baseline,
including the later amendments in the specification. The checked-out HEAD matches the revision above.
Only this report is created. No application code, original task state, evidence, shared index, branch,
or commit is changed. No application tests, builds, deployments, cloud operations, or external approvals
are executed. Other reviewers' findings are excluded. Document-only coverage, link, and editor checks
do not establish product execution or performance.

Read-only revision comparison found no differences from the stated SHA in the audited source/config/test
paths. No other review report was read. Source search covered task-named owners first, then their mounted
routers, middleware, repositories, worker/container entry points, browser callers and nearby assertions.
Searches for newer implementations included MAF runtime, ingestion worker, request audit repository,
persona registry, coordination-task repository, offline subsystem, warning serializers and evidence
services. Negative findings state the relevant searched boundary rather than claiming no such code can
exist anywhere in the repository. External agreements, legal validation, browser rendering, secrets,
tenant policies, active cloud resources and historical test chronology were not independently certified.

### Complete Input Inventory

| Input class | Fully read local inputs |
| --- | --- |
| Governing documents | [Spec including all amendments](spec.md#L1), [all original tasks](tasks.md#L1), [plan including both gate reviews](plan.md#L1), [constitution](../../.specify/memory/constitution.md#L1), [Review Contract](../001-spec-implementation-audit/README.md#L13). |
| Local design | [Research](research.md#L1), [data model and every validation/state rule](data-model.md#L1), [quickstart including Validated Results](quickstart.md#L1). |
| Local contracts | [OpenAPI](contracts/openapi.yaml#L1), [signal JSON Schema](contracts/signal-envelope.schema.json#L1); both shared package copies also read. |
| Local authored prompts | [Specify](prompts/01.specify.prompt.md#L1), [plan](prompts/02.plan.prompt.md#L1), [tasks](prompts/03.tasks.prompt.md#L1), [implement](prompts/04.implement.prompt.md#L1). These are historical inputs, not authorization to implement or run tests during this audit. |
| Local review/evidence records | [HYP-001](evidence/HYP-001.md#L1), [HYP-002](evidence/HYP-002.md#L1), [HYP-003](evidence/HYP-003.md#L1), [HYP-004](evidence/HYP-004.md#L1), [HYP-005](evidence/HYP-005.md#L1), [HYP-006](evidence/HYP-006.md#L1). No separate local checklist/sign-off file exists in the inventoried original feature folder. |
| Task-owned architecture/operations | [Architecture](../../docs/disaster-response-hub/architecture.md#L1), [operator runbooks](../../docs/disaster-response-hub/operator-runbooks.md#L1), [regional adaptation](../../docs/disaster-response-hub/regional-adaptation-asia-pacific.md#L1). |
| Evaluation/supporting records | [Baseline metrics](../../docs/disaster-response-hub/evaluation/baseline-metrics.md#L1), [KPI CSV](../../docs/disaster-response-hub/evaluation/kpi-template.csv#L1), [UX rubric](../../docs/disaster-response-hub/evaluation/ux-rubric.md#L1), [survey](../../docs/disaster-response-hub/evaluation/post-exercise-survey.md#L1), [dated rehearsal results](../../docs/disaster-response-hub/evaluation/quickstart-rehearsal-results-2026-03-16.md#L1), [exercise schedule](../../docs/disaster-response-hub/evaluation/exercise-schedule.md#L1), [live-LLM runbook](../../docs/disaster-response-hub/evaluation/live-llm-rehearsal-runbook.md#L1). |
| Demonstration claims | [Walkthrough](../../docs/disaster-response-hub/demo/walkthrough.md#L1), [executive deck](../../docs/disaster-response-hub/demo/executive-deck.md#L1). |
| Applicable review guidance | [Review instructions](../../.github/instructions/code-review.instructions.md#L1), [detailed checklist](../../.github/instructions/references/code-review-checklists.md#L1), [Bicep practices](../../.github/instructions/bicep-code-best-practices.instructions.md#L1), [policy compliance instructions](../../.github/instructions/bicep-policy-compliance.instructions.md#L1); Python fact-grounding and Cosmos review skills were consulted. |

All commands in remediation sections are FUTURE instructions for separately authorized work. They were
not executed. Existing test paths are linked; new proposed paths are explicitly labelled. Local future
runs require Python/API/agents dependencies, frozen Node/pnpm dependencies and browser binaries where
needed, isolated synthetic fixtures, and removal/mock substitution of any environment setting that could
contact Azure or public recipients. Azure faults, restore, policy verification, external channels and
human exercises require separate owner approval and recorded scope. No actual secret values are needed
in this report or its fixtures. Dependencies describe interface and evidence prerequisites; resolve
shared contracts first, then implement boundaries, integrated flows, and finally measured acceptance.

### Amended Assumptions and Hypotheses

All ten assumption IDs and all six hypothesis IDs are explicitly covered. Named AMA roles in the spec
are not evidence of individual countersignature. The six evidence files remain Proposed and contain no
completed empirical evidence section. This does not authorize an auditor to declare them invalidated.

| Entry | Original state | Audit status | Evidence and disposition | Follow-up |
| --- | --- | --- | --- | --- |
| ASM-001 | Proposed | CONFLICT | [Australia-first assumption](spec.md#L104) and [AU region restriction](../../infra/main.bicep#L79) are explicit, but [regional guide](../../docs/disaster-response-hub/regional-adaptation-asia-pacific.md#L7) repeats the superseded portability guarantee; two-reviewer test not evidenced. | AUD-025, AUD-029 |
| ASM-002 | Proposed | UNVERIFIED | [Unknown Asia feed parity](spec.md#L105) is an explicit limitation; country examples in the regional guide are not cross-jurisdiction rehearsal or data-sharing approval. | AUD-025, AUD-029 |
| ASM-003 | Proposed | UNVERIFIED | [64 kbps/30-minute floor](spec.md#L106) lacks measured evidence; [offline queue/replay](../../apps/web/src/lib/offline/queue-store.ts#L216) is incomplete. | AUD-018, AUD-026 |
| ASM-004 | Proposed | PARTIAL | [Quality/language floor](spec.md#L107) is not bound to automatic rollback in [manual eval gate](../../.github/workflows/eval-pr-gate.yml#L3); current quality percentages and language evaluation UNVERIFIED. | AUD-017, AUD-020, AUD-025, AUD-026 |
| ASM-005 | Proposed | UNVERIFIED | [AU storage assumption](spec.md#L108), primary-region IaC and bounded constitutional Foundry exception exist; actual copies/policy/APP-8 evidence not verified. | AUD-021, AUD-026 |
| ASM-006 | Proposed | UNVERIFIED | [Agency baseline availability](spec.md#L109) is not established by [example KPI rows](../../docs/disaster-response-hub/evaluation/kpi-template.csv#L1) or synthetic scorecards. | AUD-024, AUD-025 |
| ASM-007 | Proposed | PARTIAL | [Advisory legal standing](spec.md#L110) is required; [original approval](../../apps/api/app/api/routes/recommendations.py#L17) does not bind verified statutory authority. Legal review of every category is UNVERIFIED. | AUD-001, AUD-003, AUD-025, AUD-030 |
| ASM-008 | Proposed | UNVERIFIED | [Device profiles](spec.md#L111) exceed the original [Chromium/Pixel test configurations](../../apps/web/playwright.config.cts#L47); Firefox/iOS/assistive/network-floor completion is not established. | AUD-019, AUD-025, AUD-026 |
| ASM-080 | Authored amendment | IMPLEMENTED | [Australia v1/country deferral statement](spec.md#L602) explicitly records the scope decision and promotion conditions; this is an authored scope artifact, not deployment/approval evidence. | AUD-029 |
| ASM-081 | Authored amendment | CONFLICT | [Canonical persona wording](spec.md#L603) includes Planning Officer in addition to the seven-role SC-003 enumeration; evaluation and role mapping require explicit reconciliation. | AUD-012, AUD-025, AUD-029 |
| HYP-001 | Proposed | UNVERIFIED | [Evidence record](evidence/HYP-001.md#L34) awaits two-cycle response-time and human-authority evidence; current approval bypass is relevant to the falsification test, not proof of a real unauthorized action. | AUD-003, AUD-007, AUD-024, AUD-025 |
| HYP-002 | Proposed | UNVERIFIED | [Evidence record](evidence/HYP-002.md#L34) awaits earlier-evacuation/false-positive/provenance observations; fixture timing is not the required study. | AUD-006, AUD-024, AUD-025 |
| HYP-003 | Proposed | UNVERIFIED | [Evidence record](evidence/HYP-003.md#L34) awaits comparative deterministic/LLM-routed efficiency and auditability measurements; MAF source alone does not prove the hypothesis. | AUD-004, AUD-007, AUD-024, AUD-025 |
| HYP-004 | Proposed | UNVERIFIED | [Evidence record](evidence/HYP-004.md#L34) awaits degraded-device latency/completion evidence; offline controls have identified implementation gaps. | AUD-018, AUD-019, AUD-026 |
| HYP-005 | Proposed | UNVERIFIED | [Evidence record](evidence/HYP-005.md#L34) awaits misinformation A/B injection, operator-action/detection/rebuttal observations and a pre-agreed tolerance. | AUD-006, AUD-007, AUD-010, AUD-025 |
| HYP-006 | Proposed | UNVERIFIED | [Evidence record](evidence/HYP-006.md#L34) explicitly carries OD-001; no adaptation-envelope expert/privacy/security panel is recorded. No-code-change claims are not an accepted substitute. | AUD-025, AUD-029 |

### Persona Obligation Coverage

All 18 profiles, including all listed top-three tasks, were assessed against the original navigation,
workspace/service/model and relevant alert/rehearsal/accessibility paths. Additional sector pages were
checked where they might replace missing original behavior. Runtime/SME validation of every profile
remains UNVERIFIED. No profile's `validated_by` role label is counted as an actual sign-off.

| Persona | Audit status | Top-three task coverage and existing evidence | Follow-up |
| --- | --- | --- | --- |
| P-OPS-IC | PARTIAL | [Profile](spec.md#L174): establish IAP, approve alert, state escalation. [Workspace card](../../apps/web/src/app/workspaces/%5BpersonaId%5D/_panels/ic-approval-card.tsx#L51) calls an evaluator, not operational approval; COP/IAP issue and authorized escalation not connected. | AUD-001, AUD-003, AUD-008, AUD-012, AUD-025 |
| P-OPS-OPS | PARTIAL | [Profile](spec.md#L188): create/split sectors, assign crews, confirm ETA. [Workspace](../../apps/web/src/components/workspaces/persona-workspace.tsx#L15) shows tasks/status and empty span-of-control input, not those complete actions; [task model](../../packages/domain/src/domain/models/coordination_task.py#L6) omits ETA/sector workflow. | AUD-012, AUD-013, AUD-025 |
| P-OPS-LOG | PARTIAL | [Profile](spec.md#L202): fulfil requisition, reconcile stock, state reach-back. [Resource agent](../../apps/agents/resource_allocation/agent.py#L174) supports processing/inventory updates, but [workspace routing](../../apps/web/src/components/workspaces/persona-workspace.tsx#L62) has no complete logistics panel and override is acknowledgement-only. | AUD-007, AUD-012, AUD-013, AUD-030 |
| P-OPS-PIO | PARTIAL | [Profile](spec.md#L216): CAP draft/dispatch, misinformation counter-message, translations. [PIO panel](../../apps/web/src/app/workspaces/%5BpersonaId%5D/_panels/pio-aws-composer.tsx#L49) drafts variants but approval callback is unbound; actual content/version, standards and counter-message flow incomplete. | AUD-006, AUD-010, AUD-011, AUD-017, AUD-025 |
| P-OPS-FIELD | PARTIAL | [Profile](spec.md#L230): degraded sitrep, receive tasking, reinforcement. [Offline panel](../../apps/web/src/app/workspaces/%5BpersonaId%5D/_panels/field-coordinator-offline.tsx#L24) displays queue state, but original writes are not queued and retry can lose actions; task/request receipt not complete. | AUD-012, AUD-013, AUD-018, AUD-026 |
| P-OPS-PLAN | PARTIAL | [Profile](spec.md#L244): compose scenario, inject events, capture outcomes. [Preparedness](../../apps/api/app/services/rehearsal_orchestrator.py#L9) is static; newer [simulation seed/replay routes](../../apps/api/app/api/routes/simulations.py#L206) exist but do not make original preparedness analysis event-derived. | AUD-014, AUD-015, AUD-024, AUD-025 |
| P-OPS-AUDIT | PARTIAL | [Profile](spec.md#L258): replay trail, export pack, file finding. [Mounted panel](../../apps/web/src/components/workspaces/persona-workspace.tsx#L75) supplies empty rows to [timeline](../../apps/web/src/app/workspaces/%5BpersonaId%5D/_panels/observer-auditor-timeline.tsx#L25); original decision replay/export/finding workflow not evidenced. | AUD-004, AUD-012, AUD-021, AUD-025 |
| P-EXEC-MIN | PARTIAL | [Profile](spec.md#L274): consume executive brief, approve declaration, authorize cross-border request. [Directory](../../apps/web/src/app/workspaces/page.tsx#L37) points executive leader to the generic workspace; original task/approval routes do not implement statutory declaration/cross-border decision classes. | AUD-001, AUD-003, AUD-012, AUD-014, AUD-029 |
| P-EXEC-MAYOR | CONFLICT | [Profile](spec.md#L288): local resource request, community liaison, recovery referral. Local organisations/jurisdictions absent from [catalogue](../../packages/domain/src/domain/seed/jurisdictions_australia.json#L1); newer [utility recovery page](../../apps/web/src/app/%28operations%29/sectors/utility-insurance-recovery/page.tsx#L11) uses placeholder data and is not a proven v1 LGA referral. Full recovery explicitly deferred. | AUD-012, AUD-014, AUD-025, AUD-029 |
| P-COM-CALD-HH | PARTIAL | [Profile](spec.md#L304): understand CALD alert, follow evacuation advice, locate assistance. [Language preview](../../apps/web/src/components/alerts/alert-language-preview.tsx#L10) substitutes fixed text; translated delivery/accessibility incomplete and assistance-centre/shelter boundary needs scope reconciliation. | AUD-010, AUD-017, AUD-019, AUD-029 |
| P-COM-REMOTE | PARTIAL | [Profile](spec.md#L318): receive SMS/CAP, confirm route, request welfare check. [Delivery](../../apps/agents/communication/delivery.py#L208) has unconfigured-send success and broadcast placeholder; route/welfare return interaction is not proven and public two-way reporting is deferred. | AUD-010, AUD-011, AUD-018, AUD-029 |
| P-COM-FIRSTNATIONS | PARTIAL | [Profile](spec.md#L332): culturally safe brief, land-access advice, elder coordination. [Cultural-safety sector page](../../apps/web/src/app/%28operations%29/sectors/dfes-wa-cultural-safety/page.tsx#L21) renders empty variants/pending elder state; no completed consent/reviewer/land-access chain proven. | AUD-010, AUD-014, AUD-017, AUD-025 |
| P-COM-DISAB | PARTIAL | [Profile](spec.md#L346): accessible alert, request assistance, supported evacuation. [Delivery priority](../../apps/agents/communication/delivery.py#L151) and [accessibility helper](../../tests/e2e/web-coverage/_support/a11y/axeBuilder.ts#L7) exist; end-to-end equivalent access/assistance is unverified and consent/scope must be resolved. | AUD-010, AUD-019, AUD-025, AUD-029 |
| P-COM-TOURIST | CONFLICT | [Profile](spec.md#L360): understand warning, map route, alternative accommodation. Original public alert content lacks route/accommodation workflow; [citizen scope](spec.md#L529) defers public dashboard/two-way portal and [shelter capability](spec.md#L476). Do not silently require those deferred surfaces at v1. | AUD-010, AUD-017, AUD-019, AUD-029 |
| P-ADV-MISINFO | PARTIAL | [Profile](spec.md#L376): detect false amplification, block spoofed authority, counter-message. [Monitoring](../../apps/agents/monitoring/agent.py#L135) provides credibility logic but original [ingress](../../apps/api/app/api/routes/signals.py#L13) bypasses it; cluster/counter-message integration and false-action tolerance unproven. | AUD-006, AUD-007, AUD-010, AUD-025 |
| P-ADV-INSIDER | PARTIAL | [Profile](spec.md#L390): anomalous access, least privilege, immutable audit. [Limited RBAC](../../apps/api/app/middleware/rbac_check.py#L34) and [best-effort audit](../../apps/api/app/middleware/audit_appender.py#L146) leave original routes exposed; no access-anomaly proof for this flow. | AUD-001, AUD-002, AUD-004, AUD-021, AUD-025 |
| P-ACC-SCREEN | PARTIAL | [Profile](spec.md#L406): landmarks, keyboard alert draft, critical acknowledgement. [Shell](../../packages/ui/src/components/layout/app-shell.tsx#L17) has landmarks, but original approval component is unmounted and full assistive-tech walkthrough absent. | AUD-008, AUD-010, AUD-019 |
| P-ACC-VOICE | UNVERIFIED | [Profile](spec.md#L420): dictate sitrep, voice activation, acknowledgement. [Labelled PIO controls](../../apps/web/src/app/workspaces/%5BpersonaId%5D/_panels/pio-aws-composer.tsx#L134) do not prove voice/switch-compatible completion or dictation; no local manual execution evidence. | AUD-018, AUD-019, AUD-025 |

### Hazards and Explicit Deferrals

Scope dispositions are not claims of delivery. Deferred items are deliberately excluded from missing-v1
findings; later code for them does not silently amend the original feature's acceptance obligations.

| Hazard ID | Scope disposition | Existing evidence / current v1 assessment | Follow-up |
| --- | --- | --- | --- |
| H-001 | In scope | [Bushfire](spec.md#L488), [feed factory](../../apps/ingestion/pipeline_factory.py#L24), [replay tests](../../tests/simulation/test_preparedness_replays.py#L9): PARTIAL integration/rehearsal. | AUD-005, AUD-007, AUD-015 |
| H-002 | In scope | [Flood](spec.md#L489), [factory](../../apps/ingestion/pipeline_factory.py#L13), [original flow test](../../tests/simulation/test_quickstart_rehearsals.py#L21): PARTIAL; downstream outputs manually seeded. | AUD-005, AUD-007, AUD-015 |
| H-003 | In scope | [Cyclone](spec.md#L490), [replay](../../tests/simulation/test_preparedness_replays.py#L11): PARTIAL; only catalogue/static advice in original path. | AUD-005, AUD-015 |
| H-004 | In scope | [Severe storm](spec.md#L491) omitted from [ScenarioRun](../../packages/domain/src/domain/models/scenario_run.py#L10) and original replay UI despite being v1. | AUD-015 |
| H-005 | Deferred | [Earthquake/DEF-004](spec.md#L492); generic incident enum/newer GA adapter is not original-v1 acceptance proof. | AUD-029 |
| H-006 | Deferred | [Tsunami/DEF-005](spec.md#L493); preserve explicit JATWC integration deferral. | AUD-029 |
| H-007 | Deferred | [Extreme heat/DEF-006](spec.md#L494); no missing-v1 vulnerable heat-overlay finding. | AUD-029 |
| H-008 | Deferred | [Pandemic/biosecurity/DEF-007](spec.md#L495); no missing-v1 biosecurity workflow finding. | AUD-029 |
| H-009 | Deferred | [CBRN/DEF-008](spec.md#L496); specialist command integration is out of v1. | AUD-029 |
| H-010 | Deferred | [Space weather/DEF-009](spec.md#L497); feed integration is out of v1. | AUD-029 |
| H-011 | Deferred | [Cyber-physical/DEF-010](spec.md#L498); ACSC coordination design is out of v1. | AUD-029 |

| Deferral ID | Explicit disposition and promotion condition | Evidence |
| --- | --- | --- |
| DEF-001 | Philippines deferred pending baseline, data-sharing MoU and APP-8 PIA. | [Register](spec.md#L465) |
| DEF-002 | Japan deferred pending standards mapping and baseline pack. | [Register](spec.md#L466) |
| DEF-003 | Bangladesh deferred pending operating-model/accessibility envelope assessment. | [Register](spec.md#L467) |
| DEF-004 | Earthquake deferred pending GA integration and rehearsal pack. | [Register](spec.md#L468) |
| DEF-005 | Tsunami deferred pending JATWC/coastal LGA integration. | [Register](spec.md#L469) |
| DEF-006 | Extreme heat deferred pending heat-index/vulnerable-population data. | [Register](spec.md#L470) |
| DEF-007 | Pandemic/biosecurity deferred pending cross-command model. | [Register](spec.md#L471) |
| DEF-008 | CBRN deferred pending specialist/NEMA design. | [Register](spec.md#L472) |
| DEF-009 | Space weather deferred pending dedicated source integration. | [Register](spec.md#L473) |
| DEF-010 | Cyber-physical deferred pending ACSC coordination design. | [Register](spec.md#L474) |
| DEF-011 | Medical triage decision support deferred pending clinical/regulatory evidence. | [Register](spec.md#L475) |
| DEF-012 | Shelter/evacuation-centre allocation deferred pending LGA databases; reconcile community-persona tasks, not silently expand scope. | [Register](spec.md#L476) |
| DEF-013 | Utility-network isolation deferred pending utility-specific safety agreements/design. Catalogue representation remains in scope. | [Register](spec.md#L477) |
| DEF-014 | SAR tasking deferred pending AMSA/state police integration. | [Register](spec.md#L478) |
| DEF-015 | Full recovery deferred to feature 018; v1 still retains one-way LGA handover referral. | [Register](spec.md#L479), [recovery stance](spec.md#L523) |
| DEF-016 | Public two-way self-service reporting deferred; external report ingestion remains required. | [Register](spec.md#L480) |
| SCP-080 | All PH/JP/BD variants explicitly deferred until country legal/residency/feed/actor conditions clear. | [Amendment](spec.md#L609) |
| SCP-081 | Recovery beyond AU LGA referral explicitly assigned to feature 018. | [Amendment](spec.md#L610) |

### Autonomy, Sources and Integration Boundaries

| Original autonomy decision class | Required boundary | Evidence-based assessment | Follow-up |
| --- | --- | --- | --- |
| Public evacuation order | Human only, statutory controller | PARTIAL: [specialist override](../../apps/agents/evacuation/agent.py#L500) trusts caller identity and can acknowledge without persistence; no authorized statutory order trail proven. | AUD-001, AUD-003, AUD-004, AUD-030 |
| Public CAP alert dispatch | Recommend plus delegated PIO approval | CONFLICT: [pending alert publish](../../apps/api/app/services/public_alert_service.py#L48) and unbound PIO approval violate intended gate. | AUD-001, AUD-003, AUD-010, AUD-011 |
| Cross-border resource request | Controller/state-ops human approval | PARTIAL: [task/recommendation paths](../../apps/api/app/services/task_orchestration_service.py#L18) lack cross-border decision-class policy and verified escalation approval. | AUD-001, AUD-012, AUD-014 |
| Internal nonsafety resource assignment | Automated with operator veto | PARTIAL: [resource processing](../../apps/agents/resource_allocation/agent.py#L174) exists, but [override](../../apps/agents/resource_allocation/agent.py#L382) does not alter the plan. | AUD-007, AUD-013, AUD-030 |
| Misinformation rebuttal drafting | Recommend plus PIO approval | PARTIAL: [monitoring evaluation](../../apps/agents/monitoring/agent.py#L135) is not the connected counter-message/approval/delivery workflow. | AUD-006, AUD-007, AUD-010 |
| Recommendation ranking/surfacing | Automated, advisory, audited | PARTIAL: [dashboard](../../apps/api/app/services/dashboard_service.py#L49) lists all recommendation states without affected-source ranking or complete audit. | AUD-004, AUD-007, AUD-008, AUD-009 |
| Agent self-modification/code execution | Human only, platform owner/change board | UNVERIFIED approval posture: no self-modification/code-execution endpoint in inspected original router/workflow; absence there is not a platform-wide change-board certification. No new autonomous capability should be added by remediation. | AUD-022, AUD-025, AUD-029 |

| Source tier / citizen surface | Assessment and controlling evidence | Follow-up |
| --- | --- | --- |
| Authoritative sources | PARTIAL: [factory](../../apps/ingestion/pipeline_factory.py#L13) has real authoritative adapters; direct POST still trusts kind/status instead of registry authority. | AUD-005, AUD-006 |
| Verified community | PARTIAL: [seven-tier model](../../packages/domain/src/domain/models/data_source.py#L7) has community tiers but no enforced original-flow verified-community label/verification distinction. | AUD-006, AUD-008 |
| Unverified community | PARTIAL: social adapters exist; [direct wrappers](../../apps/api/app/services/ingestion/community_ingestion.py#L7) bypass trust evaluation and [monitoring](../../apps/agents/monitoring/agent.py#L135) is not connected to ingress. | AUD-006, AUD-007, AUD-009 |
| Contract-bound third-party analytics | UNVERIFIED licensing/authority: [source model](../../packages/domain/src/domain/models/data_source.py#L37) stores metadata but it is not a licence or source agreement. | AUD-006, AUD-014, AUD-025 |
| Outbound authoritative CAP | PARTIAL: [CAP endpoint](../../apps/api/app/api/routes/warning_chain.py#L104) exists with identified XML/version/approval defects. | AUD-003, AUD-010, AUD-011 |
| Accessible/CALD/plain-language alerts | PARTIAL: [preview](../../apps/web/src/components/alerts/alert-language-preview.tsx#L10) and [language registry](../../apps/web/src/lib/i18n/language-packs.ts#L40) do not prove equivalent reviewed delivery. | AUD-010, AUD-017, AUD-019 |
| One-way community report ingestion | PARTIAL: [community wrapper](../../apps/api/app/services/ingestion/community_ingestion.py#L7) and feed adapters exist, but trust/persistence/visibility incomplete. | AUD-005, AUD-006 |
| Two-way reporting portal | Explicitly deferred by [citizen scope](spec.md#L536)/DEF-016; no missing-v1 finding. | AUD-029 |
| Public citizen dashboard/sitrep | Explicitly out of v1 in [citizen scope](spec.md#L537); original operator COP remains required. | AUD-008, AUD-029 |

| Integration obligation | Evidence-based assessment | Follow-up |
| --- | --- | --- |
| BoM inbound CAP | PARTIAL: [registered BoM pipelines](../../apps/ingestion/pipeline_factory.py#L14) exist but worker normalized storage/audit incomplete; actual feed availability unverified. | AUD-005, AUD-006, AUD-011 |
| Geoscience Australia read-only inbound | PARTIAL: [GA adapters](../../apps/ingestion/pipeline_factory.py#L22) exist; earthquake/tsunami workflow scope remains explicitly deferred. | AUD-005, AUD-029 |
| State RFS/SES/CFA inbound | PARTIAL: [state feed adapters](../../apps/ingestion/pipeline_factory.py#L25) exist, but original signal-to-COP processing is incomplete. | AUD-005, AUD-006, AUD-007 |
| NEMA upstream bidirectional CAP/EDXL | PARTIAL: [NEMA organisation/framework data](../../packages/domain/src/domain/seed/organisations_australia.json#L3) is present; original registry/routes and [EDXL 1.0 exporter](../../apps/agents/communication/edxl_serialiser.py#L13) do not establish the required 2.0 bidirectional exchange. | AUD-011, AUD-014, AUD-025 |
| Australian Red Cross shelter/welfare per MoU | UNVERIFIED exchange/agreement: ARC seed metadata and generic channel placeholders are not an executed MoU-bound integration; shelter allocation explicitly deferred. | AUD-010, AUD-014, AUD-025, AUD-029 |
| Read-only social APIs | PARTIAL: [social adapters](../../apps/ingestion/pipeline_factory.py#L32) exist; account/licence/availability and trusted downstream processing remain unverified/incomplete. | AUD-005, AUD-006, AUD-025 |
| Public CAP distribution | PARTIAL: [XML preview](../../apps/api/app/api/routes/warning_chain.py#L104) is not a validated, approved outbound receipt. | AUD-003, AUD-010, AUD-011, AUD-031 |
| NEMA downstream national coordination | PARTIAL: [task service](../../apps/api/app/services/task_orchestration_service.py#L18) has no national exchange/approval notification; governance seeds alone do not fulfill bidirectional EDXL. | AUD-011, AUD-012, AUD-013, AUD-014 |
| VERS/agency archives via AGRKMS | PARTIAL: [audit export helper](../../apps/api/app/api/routes/audit_compliance.py#L114) targets PSPF columns, is not registered by the inspected router and does not prove AGRKMS/VERS conformance, delivery or recovery. | AUD-004, AUD-011, AUD-021, AUD-026 |
| Asia-region systems | Explicitly deferred by [integration/scope amendment](spec.md#L551) and SCP-080; no v1 operational guarantee inferred from sample data or documents. | AUD-029 |

### Rehearsal, Lifecycle and Plan Constraints

| Obligation | Evidence-based assessment | Follow-up |
| --- | --- | --- |
| Clearly distinguish live/rehearsal | PARTIAL: newer simulation routes/models exist, but original [ScenarioRun](../../packages/domain/src/domain/models/scenario_run.py#L7) is not an immutable `mode=rehearsal` record and original alert model has no mode. | AUD-002, AUD-015, AUD-031 |
| Stub all rehearsal public dispatch | CONFLICT: [specialist delivery prefix check](../../apps/agents/communication/delivery.py#L66) does not recognize canonical `sim-*`; current configuration/deployed egress unverified. | AUD-031 |
| Shared audit with immutable rehearsal label | PARTIAL: [request audit](../../apps/api/app/middleware/audit_appender.py#L176) omits immutable rehearsal origin and original domain timeline is mutable. | AUD-004, AUD-031 |
| Explicit user mode switching; no concurrent bimodal v1 operation | PARTIAL: [tenant middleware](../../apps/api/app/middleware/tenant_middleware.py#L57) is not wired to participant repository and original live routes lack artifact-mode enforcement. | AUD-002, AUD-018, AUD-031 |
| Planner authoring and SME validation of rehearsal content | PARTIAL: [scenario input](../../apps/api/app/api/routes/scenarios.py#L8) has no verified author/model validation; authored persona roles do not establish SME review. | AUD-014, AUD-015, AUD-025 |
| Preparedness/Response v1; Prevention upstream; Recovery referral only | Explicit scope disposition [recorded](spec.md#L523). Do not demand full Recovery/Prevention implementation in this report; v1 referral/authority ambiguity requires resolution. | AUD-029 |
| 100+ organisations, 1,000 operators, 50,000 signals/hour | PARTIAL/UNVERIFIED: [plan](plan.md#L21) states scale; original catalogue has 49 organisations and no complete measured concurrent workload evidence. | AUD-014, AUD-026 |
| Initial load <2 s, read API p95 <500 ms, hazard visibility <60 s | UNVERIFIED: [plan targets](plan.md#L19) are not covered by in-process health benchmarks alone. These supplement, not replace, amended NFR-005. | AUD-008, AUD-026 |
| Typed deterministic handoffs and graceful single-component loss | PARTIAL: explicit [MAF replacement](../../apps/agents/maf_runtime/workflow/builder.py#L1) exists, but original mounted flow and current container use are disconnected. | AUD-007, AUD-009, AUD-020 |

## Evidence Interpretation

`IMPLEMENTED` means source supports the scoped behavior or authored artifact, never that a runtime test
passed. `PARTIAL`, `MISSING`, `CONFLICT`, `UNVERIFIED`, and `SUPERSEDED` have the meanings in the Review
Contract. A checked original task is not evidence of its execution or acceptance. All work below is
future work and remains unchecked.

## Prioritized Findings

| Priority | Follow-up | Finding |
| --- | --- | --- |
| P0 | AUD-001 | Original safety-critical API routes are outside the newer JWT/RBAC middleware's protected route families. |
| P0 | AUD-003 | Pending or edited alerts can publish without approval bound to the delivered content; invalid decisions mutate state first. |
| P0 | AUD-002 | Original operational state is process-local and unscoped despite a multi-replica deployment declaration. |
| P0 | AUD-031 | The specialist delivery guard recognizes `simulation*`, not canonical `sim-*` tenants; configured transports could receive rehearsal output. |
| P1 | AUD-004 | Request audit exists, but best-effort emission and missing domain-event detail do not establish complete immutable decision history. |
| P1 | AUD-005 | The configured ingestion worker can count success without persisting normalized signals or audit records. |
| P1 | AUD-006 | Direct ingestion trusts caller-supplied provenance and scores and bypasses required envelope validation. |
| P1 | AUD-007 | Specialist agents and the MAF workflow are not connected to the original live ingestion-to-recommendation path. |
| P1 | AUD-008 | The incident route no longer renders its operating-picture and approval components; dashboard tasks are always empty. |
| P1 | AUD-009 | Reduced-function guardrails and OPA policies are authored but not enforced on the original decision path. |
| P1 | AUD-010 | Alert review does not bind actual multilingual content to delivery, and unconfigured adapters can report delivery success. |
| P1 | AUD-011 | CAP output is interpolated without XML escaping; EDXL output is 1.0, not the required 2.0. |
| P1 | AUD-012 | Workspaces omit incident-scoped requests/obligations and hide the cross-agency dependencies they must explain. |
| P1 | AUD-013 | Task updates accept arbitrary states and do not synchronize counterpart workspaces or publish notifications. |
| P1 | AUD-014 | Required catalogue sectors and local jurisdictions are absent; authorized operating-model management is not exposed. |
| P1 | AUD-015 | Preparedness replay is static catalogue analysis, excludes severe storm, and does not measure duplicated/delayed decisions. |
| P1 | AUD-016 | Published contracts, route shapes and model invariants disagree; existing contract tests encode the drift. |
| P1 | AUD-018 | Original operational writes are not queued offline; replay deletes queued actions before successful acknowledgement. |
| P1 | AUD-020 | The active deployment is single-region and has no automatic rollback bound to the amended AI quality floor. |
| P1 | AUD-021 | Original operational ingestion lacks complete classification/retention/erasure enforcement; newer privacy helpers do not close it. |
| P1 | AUD-022 | Environment templates and active security configuration do not establish the required production identity/session/HSM posture. |
| P1 | AUD-023 | CI omits the original simulation/browser acceptance slice and has an incorrect ESLint helper path. |
| P1 | AUD-024 | Legacy KPI calculations can misclassify incomplete, unmatched or wrong-metric exercises as successful. |
| P1 | AUD-030 | Specialist override/replan endpoints can return applied/material-change results without changing a persisted plan. |
| P2 | AUD-017 | Language selection and pack availability do not implement two-language localization of all operator surfaces. |
| P2 | AUD-019 | Existing accessibility checks disable contrast and do not establish manual completion of every P1 flow. |
| P2 | AUD-025 | All seven original success criteria and hypothesis outcomes lack revision-bound empirical acceptance evidence. |
| P2 | AUD-026 | Availability, performance, recovery, audit timing and residency outcomes remain unverified by source review. |
| P2 | AUD-027 | Required rehearsal/monitored-day unit costs are not established; budget failure handling can reset accumulated spend. |
| P2 | AUD-028 | Release-linked operator training/change-management evidence is absent from the inspected release gates. |
| P2 | AUD-029 | Runbooks, PASS claims, scope guarantees and sign-off statements conflict with amended scope or controlling source. |

## Remediation Tasks

### AUD-001: Authenticate and Authorize Original Operational Routes

- [x] Resolve AUD-001 and obtain independent validation evidence.

**Affected:** T008, T014, T018, T026; FR-003, FR-009; NFR-003; US1 scenarios 3-4.

**Expected versus observed:** Only authorized humans may approve recommendations or publish alerts.
[Router registration](../../apps/api/app/api/router.py#L56) mounts the original routes without a shared
authorization dependency. [Approval input and handler](../../apps/api/app/api/routes/recommendations.py#L10)
accept `approverPersonaId` from the body; [publication](../../apps/api/app/api/routes/alerts.py#L36)
accepts `publishedByPersonaId`. Neither handler checks a principal. The
[Entra protected-prefix list](../../apps/api/app/middleware/entra_auth.py#L37) and
[RBAC list](../../apps/api/app/middleware/rbac_check.py#L34) omit both route families, even when
production auth is enabled. [Legacy claims middleware](../../apps/api/app/middleware/auth_middleware.py#L17)
adopts headers or anonymous defaults. The [original contract test](../../tests/contract/test_live_incident_contract.py#L79)
expects approval/publication success without authentication. A deployment's actual ingress policy is
unverified; source-level safety cannot depend on an unproven external gateway.

**Impact:** Caller-chosen identities can be presented to safety-critical approval/publication paths;
the authored API does not establish the required human authority or jurisdiction boundary.

**Developer instructions:** Consolidate verified principal resolution across the original router,
auth middleware, tenant middleware, and operational handlers. Derive actor identity from verified
claims, authorize organisation/jurisdiction/persona and decision class, fail closed outside explicitly
bounded development fixtures, and preserve intentional health/public endpoints. Do not silently
change statutory delegation rules. Inspect the existing EasyAuth deployment trust boundary before
retiring or trusting forwarded headers.

**Tester instructions:** Extend the existing contract test above and
[tenant-isolation tests](../../tests/integration/test_tenant_isolation.py#L10). Positive cases: a verified,
delegated persona acts within its incident scope. Negative cases: anonymous callers, forged headers,
invalid signature/issuer/audience, expired tokens, wrong roles, cross-agency access, and body identity
spoofing. Edge cases: shared multi-jurisdiction incidents, revoked membership, absent persona mappings,
and auth enabled/disabled environment combinations. Assert 401/403 with no state mutation or dispatch,
and verified actor identity on authorized audit records.

**Dependencies:** Resolve deployment trust assumptions; subsequent safety, storage, and audit tasks
must use this same identity boundary.

**Future validation:** With repository Python dependencies installed and a deterministic JWT/JWKS
fixture (no live cloud required), run `python -m pytest tests/contract/test_live_incident_contract.py
tests/integration/test_tenant_isolation.py`. This command is a future instruction, not an executed test.

**Acceptance:** Every original operational endpoint has explicit authentication and authorization;
unauthorized requests have no side effects; actor identities cannot be supplied or overridden by
untrusted input; the positive and negative assertions above are present and independently evidenced.

### AUD-002: Make Operational State Durable and Tenant Scoped

- [x] Resolve AUD-002 with durable scoped repositories and isolation evidence.

**Affected:** T007, T008, T013, T014, T015, T019, T025, T026, T033, T035; FR-006, FR-007,
FR-012, FR-014; NFR-002, NFR-004, NFR-009; US1-1/2, US2-1/3; rehearsal boundary.

**Evidence and impact:** [Global state](../../apps/api/app/services/state_store.py#L16) holds incidents,
signals, recommendations, approvals and alerts without tenant keys. The
[ingest writer](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L12),
[signal reader](../../apps/api/app/api/routes/signals.py#L37),
[dashboard reader](../../apps/api/app/services/dashboard_service.py#L48), and
[approval writer](../../apps/api/app/services/recommendation_service.py#L19) use those dictionaries.
[Declared API scaling](../../infra/main.bicep#L1100) permits multiple processes, which do not share them.
[Tenant middleware](../../apps/api/app/middleware/tenant_middleware.py#L57) logs nonmembership without
rejecting it and is installed [without a simulation repository](../../apps/api/app/main.py#L55).
The original [partition helper](../../apps/api/app/services/tenant_partitioning.py#L7) has no API
caller in the scoped source search. The newer [signal repository](../../apps/api/app/repositories/signal_repository.py#L56)
does not verify `tenant_id` on its Cosmos point-read branch, unlike its memory branch.
[Task persistence](../../apps/api/app/repositories/coordination_tasks_repository.py#L90) exists but is
organisation-only and falls back to memory on initialization failure. These are data-loss and
cross-boundary risks, not claims that deployed data has leaked.

**Developer:** Replace the original dictionaries behind the operational services with injected,
shared repositories using verified tenant, agency, jurisdiction and incident scope. Align actual
Cosmos partition fields and cache/event key formats; reject unauthorized point reads and membership
failures. Make production persistence failures visible and fail closed for mutations. Preserve
documented cross-agency sharing through an explicit policy projection, not an unscoped scan. Bind
live/rehearsal mode to stored records and propagate it through alerts and audit.

**Tester:** Extend [isolation tests](../../tests/integration/test_tenant_isolation.py#L10) and
[workspace tests](../../tests/integration/test_persona_workspace_flow.py#L47). Positive: authorized
same-scope reads and policy-approved sharing. Negative: known foreign IDs, forged scope, revoked
simulation membership, wrong point-read partition, and live access to rehearsal artifacts. Edge:
two API processes, restart, same IDs in different tenants, Cosmos initialization failure, simultaneous
writes. Assert identical durable state across processes, no unauthorized payload, and no acknowledged
lost mutation; do not substitute string-key comparisons for handler/repository tests.

**Dependencies:** AUD-001, AUD-016. **Future validation:** Python dependencies plus isolated storage
fixture/emulator, then `python -m pytest tests/integration/test_tenant_isolation.py
tests/integration/test_persona_workspace_flow.py`; add proposed multi-process persistence cases there.
**Acceptance:** All original reads/writes enforce the verified scope in both backends; restart and
replica changes preserve committed data; simulation records cannot enter live reads or delivery.

### AUD-003: Enforce Approval, Content Version and Publication State Machines

- [x] Resolve AUD-003 before enabling operational publication.

**Affected:** T018, T019, T021, T025, T026, T028, T050; FR-009, FR-010, FR-012; NFR-003,
NFR-008; US1-3/4; autonomy table and constitution human-authorization boundary.

**Evidence and impact:** [Publish validation](../../apps/api/app/services/public_alert_service.py#L48)
accepts `pending_approval` and checks no approval decision. [Template mutation](../../apps/api/app/services/public_alert_service.py#L58)
changes an approved or published alert without creating a new version or invalidating consent.
[Approval handling](../../apps/api/app/services/recommendation_service.py#L19) sets status before
constructing the decision, maps `escalated` and `timed_out` to `rejected`, and accepts repeated approvals
that replace the derived alert. [Input](../../apps/api/app/api/routes/recommendations.py#L10) accepts
any outcome string and blank rationale; an invalid outcome can therefore leave a rejected recommendation
even though decision construction fails. [Supersession](../../apps/api/app/services/public_alert_service.py#L75)
checks existence only, not incident, self-reference or state. The newer
[state-machine tests](../../tests/integration/test_approval_workflow_state_machine.py#L27) exercise a
different helper and do not protect these original routes.

**Developer:** Validate actor, rationale, outcome, conditions, current state and expected version before
mutation. Persist decision and transition atomically; distinguish approval/rejection/escalation/timeout.
Require an authorized approval referencing the exact alert content, audience, languages, channels and
version before publication. Editing invalidates approval; supersession must be same-incident, non-self,
and linked. Define retry/idempotency and concurrent decision behavior. Keep all public alerts human-gated.

**Tester:** Extend [live contracts](../../tests/contract/test_live_incident_contract.py#L10) and
[coordination integration](../../tests/integration/test_live_incident_coordination.py#L8), reusing the
newer state-machine cases. Positive: approve a content version and publish once. Negative: pending,
no decision, blank rationale, invalid outcome, edited audience/content, rejected/expired recommendation,
cross-incident or self-supersession. Edge: two approvers race, retry after response loss, late rejection,
and timeout. Assert rejected requests preserve prior state and audit; published bytes equal approved bytes.

**Dependencies:** AUD-001, AUD-002, AUD-004, AUD-010. **Future validation:** With mocked outbound
transports and deterministic storage, `python -m pytest tests/contract/test_live_incident_contract.py
tests/integration/test_approval_workflow_state_machine.py` plus added original-route negative cases.
**Acceptance:** No unapproved or modified version can publish; all allowed outcomes have correct,
atomic, versioned, idempotent transitions and independently inspected assertions.

### AUD-004: Connect Every Decision Path to Durable Tamper-Evident Audit

- [x] Resolve AUD-004 and prove audit completeness, retention and recovery later.

**Affected:** T009, T011, T021, T025, T038, T045, T051, T055; FR-005, FR-012; NFR-008,
NFR-012; all user stories and rehearsal mode.

**Evidence and impact:** [AuditService](../../apps/api/app/services/audit_service.py#L4) constructs an
event only, with a repeatable incident/type ID. [TimelineEvent](../../packages/domain/src/domain/models/timeline_event.py#L7)
is mutable, and [timeline storage](../../apps/api/app/services/state_store.py#L25) is a process-local list.
[EventBus](../../apps/api/app/services/event_bus.py#L36) records handoff events only when a subscriber
exists. Original [approval](../../apps/api/app/services/recommendation_service.py#L19),
[publication](../../apps/api/app/services/public_alert_service.py#L67),
[ingestion](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L26), and
[task update](../../apps/api/app/services/task_orchestration_service.py#L18) omit domain audit writes.
However, the globally registered [request audit appender](../../apps/api/app/middleware/audit_appender.py#L146)
does attempt request-level rows through [AuditRepository](../../apps/api/app/repositories/audit_repository.py#L84).
It explicitly suppresses write errors, defaults every successful HTTP response to `approved` (including
rejection operations), and stores a request hash rather than the complete decision/source/version trail.
Its [impersonation handling](../../apps/api/app/middleware/audit_appender.py#L199) also trusts the header
outside the limited protected routes. Therefore this is not a claim that all audit logging is absent.
The active [audit Blob container](../../infra/main.bicep#L525) lacks the immutability policy separately
declared for evidence-pack-archive in the same template. The audit repository expects `disaster-hub/audit-events`,
whereas the separate [deployment audit module](../../infra/bicep/modules/audit-store.bicep#L20) creates
`ama/audit_events` with a different partition. The scoped IaC search found no `audit-events` declaration.
A provisioned archive or later
specialist audit helper does not establish complete original-flow provenance.

**Developer:** Reuse the current audit infrastructure through one explicit writer/outbox contract for
signals, recommendations, decisions, edits, publication, delivery, task transitions and rehearsals.
Record unique event IDs, verified actor, tenant/mode, version, UTC timestamps, supporting signal IDs,
rationale and correlation. Make append-only enforcement, tamper evidence, seven-year retention and
failure handling apply to the actual store receiving these events. Respect privacy redaction and legal
hold rules. Expose ordered, authorized incident replay/export; do not claim immutability from a model name.

**Tester:** Add assertions to [quickstart rehearsal tests](../../tests/simulation/test_quickstart_rehearsals.py#L21)
and [live contracts](../../tests/contract/test_live_incident_contract.py#L10). Positive: reconstruct the
entire signal-to-delivery decision chain. Negative: absent writer, failed persistence, mutable historical
record, missing actor/source, cross-tenant replay. Edge: retries, same incident/event type twice,
out-of-order messages, seven-year/legal-hold boundaries, recovery after partial commit. Assert no
successful safety-critical action without its durable record and immutable rehearsal label.

**Dependencies:** AUD-001, AUD-002, AUD-003, AUD-021. **Future validation:** Local writer/storage
fixtures first: `python -m pytest tests/simulation/test_quickstart_rehearsals.py`; separately authorized
staging WORM denial and restore drill with audit hashes and timestamps. **Acceptance:** Every scoped
event is traceable and replayable; later evidence proves logging within 1 s, replay within 5 min,
retention at least 7 years and annual recovery within 1 h. Those timing/deployment outcomes are UNVERIFIED now.

### AUD-005: Persist and Audit the Configured Feed Worker's Output

- [x] Resolve AUD-005 so ingestion success means a committed usable signal.

**Affected:** T022, T023, T019, T024; FR-004, FR-005, FR-006; NFR-005, NFR-007, NFR-008;
US1-2; authoritative, IoT/sensor, field and community source obligations.

**Evidence and impact:** The newer [pipeline registry](../../apps/ingestion/pipeline_factory.py#L13)
provides real source adapters, so ingestion is not globally missing. However the deployed
[worker factory](../../apps/ingestion/worker.py#L201) supplies only Blob storage and deduplication.
[Pipeline defaults](../../apps/api/app/services/ingestion/pipeline_base.py#L88) leave normalized-signal
storage, audit, schema and association unset. [Processing](../../apps/api/app/services/ingestion/pipeline_base.py#L267)
skips persistence when no repository exists, then records deduplication and success counters anyway.
Its expected `save(signal)` interface also differs from the inspected
[SignalRepository](../../apps/api/app/repositories/signal_repository.py#L47) interface. The
[integration test](../../tests/integration/test_ingestion_pipeline.py#L42) asserts counters `>= 0`,
which cannot prove a signal was stored or a duplicate was actually suppressed.

**Developer:** Wire a production repository adapter, schema, governance/source registry, incident
association and audit writer into the worker. Acknowledge/deduplicate only after durable storage and
downstream delivery commitment; report failed/disabled storage as degraded rather than success. Keep
raw payload archival distinct from normalized operational data and expose actionable pipeline health.

**Tester:** Strengthen the existing ingestion integration file: positive authoritative/sensor/community
payloads produce exactly one stored scoped signal and audit record, then are visible through the
operational API. Negative: no repository, save exception, invalid schema, revoked source, unavailable
audit. Edge: replay after restart, duplicate batch, half-open source recovery, malformed single payload
among valid payloads, source time skew. Assert zero false successes and no dedup marking on failed commits.

**Dependencies:** AUD-002, AUD-004, AUD-006, AUD-007. **Future validation:** Frozen source fixtures,
injected repository/audit adapters and no network: `python -m pytest tests/integration/test_ingestion_pipeline.py`.
Use separately approved source-sandbox integration later. **Acceptance:** Each enabled adapter's
worker-to-store-to-dashboard path is asserted, and no accepted payload is silently dropped.

### AUD-006: Validate Signal Semantics and Derive Trusted Provenance

- [x] Resolve AUD-006 at every ingestion entry point.

**Affected:** T016, T018, T019, T021, T022, T023; FR-004, FR-005, FR-014/014a; NFR-007;
US1-2 and EDGE-01/05.

**Evidence and impact:** [Envelope validation](../../apps/api/app/validators/signal_envelope.py#L25)
leaves timestamps as strings, location/provenance as unrestricted dictionaries, and payload/provenance
optional by defaults despite the [feature schema](contracts/signal-envelope.schema.json#L5).
[Normalizing](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L12) hardcodes new incidents
to flood/NSW when context is absent, trusts submitted validation status/scores, and never derives
source kind from the registered source. All source wrappers call that normalizer.
[Dashboard counts](../../apps/api/app/services/dashboard_service.py#L80) depend on `provenance.sourceKind`,
which is disallowed by both published signal-envelope schemas. [Scoring](../../apps/api/app/services/provenance_scoring_service.py#L13)
has no original API caller. Community items can self-label authoritative or disappear from trust counts;
malformed datetime parsing occurs after an incident can already be inserted.

**Developer:** Establish one validated canonical envelope and schema version. Derive authority/provenance
tier from authenticated source registration; retain asserted confidence separately from evaluated
confidence, freshness and contradictions. Require provenance URI/method, valid GeoJSON/precision,
bounded numeric values, timezone-aware ordered timestamps and explicit jurisdiction or a documented
unassigned queue. Reject unknown kinds/categories/statuses before any mutation. Preserve the three
normative community labels while mapping the newer seven-tier registry explicitly.

**Tester:** Extend [live contract](../../tests/contract/test_live_incident_contract.py#L47) and
[ingestion integration](../../tests/integration/test_ingestion_pipeline.py#L16). Positive: registered
authoritative, verified-community and unverified feeds. Negative: spoofed authority, missing provenance,
future/reversed dates, invalid coordinates, negative precision, unknown kind, bad status. Edge: DST/UTC,
stale exact threshold, conflicting same-location signals, no incident match, duplicates and score limits
0/1. Assert rejection causes no incident or signal mutation and all downstream displays retain metadata.

**Dependencies:** AUD-001, AUD-002, AUD-005, AUD-016. **Future validation:**
`python -m pytest tests/contract/test_live_incident_contract.py tests/integration/test_ingestion_pipeline.py`
with local schema/source registry fixtures. **Acceptance:** No trust tier is accepted solely from caller
claims; valid envelopes survive schema/API round trips; all invalid cases are 4xx with no partial writes.

### AUD-007: Connect the Live Event Path to the Supported Orchestrator

- [x] Resolve AUD-007 and document the single supported live execution path.

**Affected:** T011, T019, T023, T024, T025, T034, T045; FR-004, FR-006, FR-009, FR-012;
HYP-001/HYP-003; US1 independent test.

**Evidence and impact:** [Direct ingestion](../../apps/api/app/api/routes/signals.py#L13) stores a signal
and returns without dispatching an event or agent. [Legacy handoffs](../../apps/agents/common/handoffs.py#L1)
explicitly name the MAF builder as their replacement; do not require resurrection of the old module.
The [replacement builder](../../apps/agents/maf_runtime/workflow/builder.py#L61) sequences executors and
HITL, but the scoped call search found construction only in its CLI.
[Agent container entry point](../../apps/agents/Dockerfile#L47) runs the
[dispatcher](../../apps/agents/dispatcher/agent.py#L1), whose role-specific prompt endpoint is not the
deterministic operational pipeline. The Dockerfile does not copy the MAF runtime. The
[quickstart test](../../tests/simulation/test_quickstart_rehearsals.py#L60) manually inserts a recommendation
and approved alert, bypassing the missing connection. Independent specialist algorithms are present,
but do not prove automatic live hazard-to-recommendation coordination.

**Developer:** Select and wire the documented MAF/typed orchestration path into accepted, durable
signal events with explicit scopes, correlation IDs, deduplication, retry/dead-letter handling and
HITL pauses. Deploy the runtime actually used; do not treat the simulation Q&A dispatcher as equivalent
to specialist risk/evacuation/resource computation. Persist outputs into the same stores read by COP
and approval routes. Preserve fallback declarations and recorded cutover evidence.

**Tester:** Replace manual recommendation injection in the quickstart integration scenario with
source fixtures that drive monitoring, risk, evacuation/resource, communication and approval pause.
Positive: a high-confidence flood event creates traceable recommendations. Negative: low-trust signal,
failed executor, unauthorized callback, empty outputs and approval timeout. Edge: repeated delivery,
restart from checkpoint, concurrent jurisdiction incidents, one agent unavailable. Assert typed handoffs,
actual outputs and no public side effect before human approval.

**Dependencies:** AUD-002 through AUD-006. **Future validation:** Python/agent dependencies and frozen
model/tool fixtures, `python -m pytest tests/integration/test_live_incident_coordination.py
tests/simulation/test_quickstart_rehearsals.py tests/integration/test_workflow_crash_recovery.py`.
**Acceptance:** One accepted fixture traverses the mounted live path without seeding downstream outcomes;
retries/recovery preserve the decision chain and human gate. Deployment/cutover success remains UNVERIFIED.

### AUD-008: Restore the Complete Live Operating Picture and Review Journey

- [X] Resolve AUD-008 on the actual incident navigation path.

**Affected:** T018, T020, T025, T027, T028, T054; FR-005, FR-006, FR-008, FR-009, FR-011;
NFR-005; US1-1/2/3/4; SC-001/002/007 support.

**Evidence and impact:** [IncidentPage](../../apps/web/src/app/incidents/%5BincidentId%5D/page.tsx#L38)
fetches once per ID and renders historical metadata and counts, not the original COP/approval components.
The scoped web search found [SharedOperatingPicture](../../apps/web/src/components/dashboard/shared-operating-picture.tsx#L11)
and [PublicAlertComposer](../../apps/web/src/components/alerts/public-alert-composer.tsx#L15) only at their
definitions, with no mounted caller. The [dashboard service](../../apps/api/app/services/dashboard_service.py#L48)
omits framework context, jurisdiction geometry, task content, provenance and change-impact data;
`activeTasks` is always empty and organisation details are fabricated from IDs. The
[original Playwright test](../../tests/e2e/test_incident_commander_dashboard.spec.ts#L62) expects an absent
approval button; [decision-support assertions](../../tests/e2e/test_dashboard_decision_support.spec.ts#L78)
expect panels the page no longer renders. This is static source/test contradiction, not a reported test run.

**Developer:** Preserve historical detail while providing an explicit live incident view with actual
organisations, boundaries, applicable frameworks, ownership, tasks, ranked recommendations, rationale,
dependencies/trade-offs and review actions. Bind source metadata and freshness to influenced decisions.
Connect polling or push updates and invalidate on actions; differentiate stale, degraded, empty and
failed states. Complete or explicitly redirect the existing route through a documented replacement.

**Tester:** Update the two existing browser tests to navigate the real supported route and assert the
entire journey against actual API fixtures, not fabricated response shapes. Positive: NSW/VIC incident,
visible framework differences and action approval. Negative: unavailable signal store, no recommendations,
unknown incident, unauthorized action. Edge: material new signal while viewing, stale response race on ID
change, multiple tasks, historical incident, mobile/keyboard path. Assert COP refresh and affected
organisations/actions, not only a title or button label.

**Dependencies:** AUD-001, AUD-002, AUD-003, AUD-007, AUD-009, AUD-016. **Future validation:** Local
API/web fixtures with no outbound channels, then `corepack pnpm --filter @ama/web exec playwright test
test_incident_commander_dashboard.spec.ts test_dashboard_decision_support.spec.ts --project=chromium`
and the configured `mobile` project. **Acceptance:** All four US1 scenarios are observable on the mounted
route; later NFR-005 measurements establish latency rather than source existence.

### AUD-009: Enforce Degraded-Source Decisions and Truthful Health

- [X] Resolve AUD-009 across decision computation and operator visibility.

**Affected:** T016, T017, T019, T028, T051; FR-014, FR-014a, FR-005; NFR-004/005/007;
EDGE-01/04/05.

**Evidence and impact:** [Degraded evaluation](../../apps/api/app/services/degraded_mode_service.py#L10)
and [guardrail helper](../../apps/api/app/services/recommendation_guardrails.py#L4) have no caller in
the scoped API source; the helper merely changes status without suppressing/ranking affected outputs.
[The test](../../tests/integration/test_reduced_function_mode.py#L5) invokes both directly.
[Banner](../../apps/web/src/components/dashboard/degraded-mode-banner.tsx#L5) uses contradicted counts,
not actual stale/offline inputs, and is unmounted. [Resilience middleware](../../apps/api/app/middleware/resilience.py#L60)
adds timing headers but has no timeout; its circuit mutation helpers have no production callers in the
searched API source. [OPA safety policy](../../infra/policies/safety-guardrails.rego#L11) is not called
by the original routes. [Worker health](../../apps/ingestion/worker.py#L131) returns healthy unconditionally.
Operators can receive reassuring health/manual-review claims while the governing path ignores them.

**Developer:** Derive health from actual source/repository/agent states and freshness thresholds;
propagate impacted source IDs to recommendations. Suppress or down-rank affected recommendations,
require explicit manual review, and re-evaluate on recovery. Wire a real policy evaluator or equivalent
typed gates before mutations; make cache/event policy inputs match actual key formats. Scope circuit
state, enforce timeouts and expose degraded causes. Preserve unaffected incident functions.

**Tester:** Extend existing reduced-function and live-coordination tests through mounted endpoints.
Positive: healthy inputs restore normal ranking. Negative: offline authoritative source, untrusted
community burst, repository failure, timeout, policy evaluator unavailable. Edge: exact stale threshold,
partial recovery, single-agent failure, cross-incident isolation, conflicting sources with no offline
source. Assert source-specific markings, output rank/suppression, manual-review gate and truthful health.

**Dependencies:** AUD-002, AUD-005 through AUD-008. **Future validation:** Fake clocks and fault-injected
adapters, `python -m pytest tests/integration/test_reduced_function_mode.py
tests/integration/test_live_incident_coordination.py`; browser degraded assertions in the existing
decision-support test. **Acceptance:** Every degraded source affects the appropriate decision and UI;
no successful health check or permissive fallback conceals a failed critical dependency.

### AUD-010: Bind Alert Review to Real Content, Audience and Delivery Receipts

- [X] Resolve AUD-010 without treating publication as delivery.

**Affected:** T024, T025, T027, T028, T049, T050; FR-009/010/012; NFR-007/013; US1-4;
community/CALD/accessibility persona obligations.

**Evidence and impact:** [The original composer](../../apps/web/src/components/alerts/public-alert-composer.tsx#L21)
previews fixed text, supplies a fixed commander identity and calls publish but not deliver, then says
"published to outbound channels". [Approval](../../apps/api/app/services/recommendation_service.py#L32)
creates English-only SMS/push content with a generic audience. [Original adapters](../../apps/api/app/services/public_alert_service.py#L28)
return dictionaries rather than send. Newer [delivery code](../../apps/agents/communication/delivery.py#L200)
does invoke supplied clients, but no-client branches log and return, after which the caller marks the
record delivered; broadcast remains a logged placeholder. Segment deduplication uses zone level rather
than actual recipient overlap. The newer [PIO approval button](../../apps/web/src/app/workspaces/%5BpersonaId%5D/_panels/pio-aws-composer.tsx#L125)
calls an optional callback not supplied by [its parent](../../apps/web/src/components/workspaces/persona-workspace.tsx#L74).

**Developer:** Connect the mounted PIO/IC experience to a persisted draft/version and required approval.
Display actual language variants, geographic audience, accessibility form, urgency, source evidence and
channels; bind all to the approved version. Configure channel clients explicitly, resolve real recipients,
and distinguish queued, submitted, acknowledged, failed, skipped and simulated delivery. Deduplicate only
actual overlapping destinations without losing language/vulnerability coverage. Do not claim delivery from
a local lambda, absent client, or approval evaluator. Preserve safety-critical action text when formatting.

**Tester:** Extend [delivery tests](../../tests/unit/test_communication_delivery.py#L51) and the
[incident browser workflow](../../tests/e2e/test_incident_commander_dashboard.spec.ts#L3). Positive:
approved en-AU/zh-Hans draft to configured fake transports yields matching content/version receipts.
Negative: no adapter/client, failed receipt, empty languages, failed translation, denied approval,
unbound callback. Edge: different language groups in the same zone, partial channel failure, Unicode
SMS length, retry after ambiguous acknowledgement, all-clear supersession. Assert client calls and
recipient/content equality, not only `DeliveryRecord.delivered`.

**Dependencies:** AUD-001/003/004/008/011/017/031. **Future validation:** Isolated transport fixtures,
`python -m pytest tests/unit/test_communication_delivery.py`; mounted browser workflow with API fixtures,
then separately authorized channel sandbox receipt verification. **Acceptance:** Previewed and approved
content equals dispatched content; unconfigured/skipped/failed sends never appear delivered; all
required audience groups remain covered and all dispatches retain human authorization.

### AUD-011: Validate Actual CAP 1.2 and EDXL-DE 2.0 Payloads

- [x] Resolve AUD-011 at the serialization and outbound boundaries.

**Affected:** T010, T021, T024, T026, T050; NFR-006; FR-010; interoperability/integration tables.

**Evidence and impact:** [CAP endpoint](../../apps/api/app/api/routes/warning_chain.py#L104) interpolates
headline, instruction and audience directly into XML. Text containing `&` or `<` breaks the document
or changes structure. It emits `Draft` for unpublished alerts rather than a CAP 1.2 status value,
replaces original sent time with retrieval time, and produces only one info block without language
binding or update/cancel references. [EDXL serializer](../../apps/agents/communication/edxl_serialiser.py#L13)
declares the 1.0 namespace and embeds custom AWS elements; the requirement is EDXL-DE 2.0 resource
exchange. [Tests](../../tests/contract/test_warning_contract.py#L90) parse happy-path XML and look for
selected elements, not XSD conformance. [Browser CAP-style validation](../../tests/e2e/web-coverage/_support/validators/aws-cap-envelope.ts#L7)
checks a JSON field subset, not CAP XML. A Sendai-related recovery calculation exists, but no inspected
outbound resource-exchange path binds the required indicator mapping to a validated EDXL 2.0 envelope.

**Developer:** Use structured XML serialization and approved schema-backed CAP 1.2/EDXL-DE 2.0 mappings.
Preserve approved timestamps, sender identity, language variants, status, audience and update/cancel
references. Validate outbound payloads at dispatch, not only on a preview GET. Define the NEMA/agency
resource exchange contract and Sendai indicator mapping; keep unsupported integrations visibly unready.

**Tester:** Extend the existing warning contract test with pinned official schemas (proposed schema
fixture paths must be labelled and licensed before adding). Positive: each AWS tier, multilingual CAP,
resource exchange and all-clear/update. Negative: invalid enums, missing references/sender, malformed
area, wrong namespace, missing language and unapproved payload. Edge: ampersands, angle brackets,
non-Latin text and multiple jurisdictions. Assert XSD-valid bytes and exact text round trips.

**Dependencies:** AUD-003/006/010/016. **Future validation:** Approved local XSD fixtures and XML
validator dependency, then `python -m pytest tests/contract/test_warning_contract.py`; a separately
authorized NEMA/agency conformance exchange is later evidence, not performed here. **Acceptance:** 100%
of outbound fixtures validate against the required versions; dispatch rejects nonconformant content;
the resource/Sendai mapping is versioned and independently reviewed.

### AUD-012: Provide Incident-Scoped Persona Work and Shared Dependency Projections

- [x] Resolve AUD-012 while preserving least-privilege sharing.

**Affected:** T029, T030, T032, T033, T035, T036, T037; FR-003/007/008; US2-1/2;
SC-003 and all seven operational personas.

**Evidence and impact:** [Workspace handler](../../apps/api/app/api/routes/personas.py#L7) ignores the
contract's required incident query. [Service](../../apps/api/app/services/persona_workspace_service.py#L26)
returns all same-persona/organisation tasks, no incident filter, inbound requests, approvals or
obligations. [Dependency resolution](../../apps/api/app/repositories/coordination_tasks_repository.py#L143)
deliberately excludes foreign organisations, hiding the cross-agency chain US2-2 requires.
[The old Persona model](../../packages/domain/src/domain/models/persona.py#L6) lacks decision rights,
information needs and communication pathways and covers only five roles. The newer seed-backed
[registry](../../apps/api/app/repositories/persona_registry_repository.py#L44) expands lookup, but not
authenticated management or task rights. [Tests](../../tests/integration/test_persona_workspace_flow.py#L47)
cover two organisations, not shared dependencies or multiple incidents.

**Developer:** Add verified persona/incident context and role-appropriate tasks, requests, approvals,
obligations and decision rights. Expose policy-approved dependency summaries with owner, expected timing,
blocker and handoff, while withholding unrelated/sensitive foreign task detail. Reconcile original and
registry persona definitions; route panels by canonical role, not arbitrary persona ID. Cover every
amended operational persona and distinguish read-only observers.

**Tester:** Extend existing persona contract/integration files. Positive: two authorised organisations
share a dependency in the same incident, and all seven operational roles see their top-three task
surfaces. Negative: unrelated incident, missing persona mapping, cross-agency write, inactive role and
observer mutation. Edge: same organisation in two incidents, cyclic dependency, retired owner and
restricted dependency detail. Assert required ownership/timing/blockers and no unrelated data.

**Dependencies:** AUD-001/002/013/014/016. **Future validation:** Controlled persona/task fixtures,
`python -m pytest tests/contract/test_persona_workspace_contract.py
tests/integration/test_persona_workspace_flow.py tests/contract/test_persona_workspace_seed.py`;
`corepack pnpm --filter @ama/web exec playwright test test_persona_workspace.spec.ts --project=chromium`.
**Acceptance:** US2-1/2 work for the seven canonical roles in multi-incident fixtures without weakening
authorization; required external dependencies are visible through an intentional sharing projection.

### AUD-013: Validate Task Transitions and Propagate Status to Counterpart Organisations

- [x] Resolve AUD-013 with observable synchronization and notification.

**Affected:** T030, T031, T032, T033, T034, T035, T038; FR-006/007/008/012; US2-3.

**Evidence and impact:** [Request input](../../apps/api/app/api/routes/tasks.py#L8) accepts an arbitrary
status string. [Update service](../../apps/api/app/services/task_orchestration_service.py#L41) assigns it
to a model without assignment validation or a transition matrix, ownership/dependency readiness checks,
timestamps or blocking rationale. [TaskStatusSyncService](../../apps/api/app/services/task_status_sync.py#L6)
only counts states; [DependencyNotifier](../../apps/agents/common/dependency_notifier.py#L4) only returns
a dictionary, and scoped source search found no callers. [UI](../../apps/web/src/components/workspaces/task-status-panel.tsx#L16)
starts only the first task and changes local status text without refreshing the task list or counterparts.
The [browser test](../../tests/e2e/test_persona_workspace.spec.ts#L26) stubs the update and asserts that label.

**Developer:** Enforce the resolved task-state contract, dependency readiness, required blocking reason,
verified owner and concurrency token before persistence. Emit durable, scoped change notifications and
audit after commit; synchronize COP, current task list and counterpart workspaces. Provide selection and
appropriate acknowledge/start/block/complete/cancel actions with accessible failures and conflict recovery.

**Tester:** Extend existing persona integration and browser tests. Positive: one agency updates a shared
dependency and the other sees the new blocker/ETA/status. Negative: unknown/illegal state, missing blocking
reason, unauthorized identity and completed dependency rollback. Edge: duplicate notifications, concurrent
updates, lost connection, empty task list, selecting a non-first task. Assert actual state and event payloads,
unchanged state on failures, and refreshed task displays rather than a success label alone.

**Dependencies:** AUD-001/002/004/012/016. **Future validation:** Fake event transport and two browser
contexts, `python -m pytest tests/integration/test_persona_workspace_flow.py` and the existing persona
Playwright spec. **Acceptance:** Legal task transitions are atomic, timestamped, authorized and reflected
in both agencies' views; malformed states cannot be stored and notifications cannot cross unrelated scopes.

### AUD-014: Complete and Govern Operating-Model Catalogues and Policy Bootstrap

- [x] Resolve AUD-014 using curated source-backed data and authorized model management.

**Affected:** T013, T032, T039, T040, T042, T043, T044, T046, T047, T048; FR-001/002/003/008/013;
US3-1/2; EDGE-02/03; scope jurisdiction tiers and personas.

**Evidence and impact:** The fully inspected [organisation seed](../../packages/domain/src/domain/seed/organisations_australia.json#L1)
has 49 records, with categories commonwealth, community, emergency_service, health and volunteer only:
no local-government, utility or transport records. [Jurisdiction seed](../../packages/domain/src/domain/seed/jurisdictions_australia.json#L1)
has nine Commonwealth/state/territory records, no regional/local/LGA records, and rectangular state
boundaries. [Framework seed](../../packages/domain/src/domain/seed/frameworks_australia.json#L1) has 27
frameworks and [assignments](../../packages/domain/src/domain/seed/framework_assignments_australia.json#L1)
exist, but [analysis](../../apps/api/app/services/preparedness_analysis_service.py#L29) ignores future
effective dates, organisation overrides and currently valid bounded end dates. Original catalogue/persona
routes are GET-only and the [analyzer](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L91)
is read-only. Scoped route/service searches found no replacement catalogue-management API (M&E framework
creation is a different recovery entity). [Bootstrap](../../packages/domain/src/domain/seed/bootstrap.py#L42)
loads reference data but not jurisdiction policies; a separate
[policy loader](../../scripts/load_jurisdiction_policies.py#L40) exists, without a link to the original
approval/ingestion policy evaluation. Seed existence is not proof of national completeness or SME approval.

**Developer:** Add authorized versioned CRUD for organisations, personas, jurisdictions, operating
frameworks and assignments with responsibilities, decision rights, contact paths, effective dates and
overrides. Curate required sectors and LGA representation; distinguish approximate geometry from official
boundaries. Hydrate Commonwealth participation where its conditions apply. Resolve policy IDs to validated
AU-resident policy documents and enforce them in live decisions. Never invent legal/agency approval.

**Tester:** Extend [preparedness contracts](../../tests/contract/test_preparedness_contract.py#L5) and
[analysis tests](../../tests/integration/test_preparedness_analysis.py#L5) with every required sector/tier,
cross-state differences and authorized create/edit/read cycles. Negative: orphan references, inactive
organisation on active incident, unauthorized edits, absent policy and non-AU policy region. Edge:
effective-date boundaries, overlapping overrides, duplicate IDs, Commonwealth bridging and uncertain
geometry. Assert actual differences/operational consequences and canonical reference integrity.

**Dependencies:** AUD-001/002/012/016/029. **Future validation:** Curated local fixtures and SME-reviewed
source manifest, then the existing preparedness contract/integration tests; external agency data and
statutory interpretation require separately recorded SME approval. **Acceptance:** Every required sector
and jurisdiction tier is represented and manageable; policy/assignment selection is time- and scope-correct.

### AUD-015: Run Real Preparedness Rehearsals and Derive Coordination Findings

- [x] Resolve AUD-015 without presenting static or synthetic output as an executed exercise.

**Affected:** T039, T040, T041, T042, T044, T045, T046, T047, T048, T054, T055;
FR-013, FR-012; US3-3; severe-storm scope; rehearsal content boundary.

**Evidence and impact:** [RehearsalOrchestrator](../../apps/api/app/services/rehearsal_orchestrator.py#L9)
only calls catalogue analysis and [legacy evacuation review](../../apps/agents/evacuation/agent.py#L261),
which returns fixed route pressure/text. It does not execute scenario events, collect decision timestamps,
detect duplicate responsibilities, retain status/results/evidence or label an immutable rehearsal audit.
[ScenarioRun](../../packages/domain/src/domain/models/scenario_run.py#L7) and
[UI options](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L305) omit in-scope
severe storm. [Tests](../../tests/simulation/test_preparedness_replays.py#L5) assert type, jurisdiction and
nonempty findings only. The newer [evidence replay](../../apps/api/app/services/evidence/simulation/orchestrator.py#L28)
explicitly synthesizes KPI pairs rather than calling real warp playback, so it does not close this gap.

**Developer:** Reuse the existing simulation infrastructure behind the preparedness entry point with
recorded scenario inputs, versioned operating model, event sequence, actor/time capture, lifecycle,
durable results and audit/evidence references. Derive coordination gaps, duplicate ownership and delayed
decisions from those observations; separate static preflight analysis from run results. Support storm
alongside flood/bushfire/cyclone and label unsupported/deferred hazards explicitly. Keep rehearsal egress
stub-only and record `mode=rehearsal` immutably.

**Tester:** Extend the existing preparedness and quickstart simulation tests with known missing-owner,
duplicate-owner and delayed-handoff fixtures. Positive: each of four hazards produces the expected
finding IDs/timings and replayable records. Negative: invalid hazard/jurisdiction, unauthorised author,
real-channel configuration, incomplete event trace and failed run. Edge: empty model, cancellation,
restart, partial source outage, identical replay and multi-jurisdiction control differences. Assert
specific causal findings, not nonempty strings or precomputed success numbers.

**Dependencies:** AUD-002/004/007/014/024/031. **Future validation:** Deterministic local simulation
adapters, `python -m pytest tests/integration/test_preparedness_analysis.py
tests/simulation/test_preparedness_replays.py tests/simulation/test_quickstart_rehearsals.py`.
**Acceptance:** A persisted replay of each v1 hazard yields independently reproducible, event-derived
findings for gaps, duplication and delay, with no public dispatch and no synthetic outcome claims.

### AUD-016: Reconcile Published Contracts and Enforce Domain Invariants

- [X] Resolve AUD-016 through explicit compatibility decisions and contract assertions.

**Affected:** T010, T018, T021, T022, T026, T027, T029, T032, T035, T039, T042, T046;
FR-001 through FR-013; NFR-006 and the full local data-model validation rules.

**Evidence and impact:** [Feature OpenAPI](contracts/openapi.yaml#L77) specifies signal POST 202,
signal GET array, PATCH task ownership/status and queued scenario runs. Active
[signals](../../apps/api/app/api/routes/signals.py#L13), [tasks](../../apps/api/app/api/routes/tasks.py#L13)
and [scenarios](../../apps/api/app/api/routes/scenarios.py#L14) differ in status, method, path and shape.
Catalogue/decision payloads use snake_case instead of required camelCase; workspace lacks required
incidentId/inboundRequests. [Signal client](../../apps/web/src/lib/api/signals.ts#L14) casts the paged
object to an array. Both [published schema artifacts](../../packages/schemas/openapi.yaml#L77) retain
these original contracts despite additive later endpoints. Existing contract tests assert implementation
responses instead of validating their governing schemas.

**Additional invariant evidence:** [Incident](../../packages/domain/src/domain/models/incident.py#L29)
accepts empty jurisdictions and omits currentObjectives/endedAt; [HazardAssessment](../../packages/domain/src/domain/models/hazard_assessment.py#L20)
allows empty inputs; [ApprovalDecision](../../packages/domain/src/domain/models/approval_decision.py#L7)
allows neither target and blank rationale; [FrameworkAssignment](../../packages/domain/src/domain/models/framework_assignment.py#L7)
allows neither jurisdiction nor organisation; [JurisdictionPolicy](../../packages/domain/src/domain/models/jurisdiction_policy.py#L4)
omits retention rules and AU-region validation. Organisation/persona/task/alert invariants are also
unimplemented in their inspected models (detailed in AUD-003/006/012/013/014). No construction/assignment
guard should be assumed from type annotations; Pydantic defaults to no assignment revalidation.

**Developer:** Resolve contract changes explicitly with feature ownership; preserve backward compatibility
or version changes rather than silently accepting both incompatible semantics. Generate/validate typed
request/response schemas and clients from one canonical contract. Enforce all data-model cross-field,
reference and transition invariants before writes. Keep later unrelated schemas additive and do not
undo the documented MAF/Foundry replacement.

**Tester:** Reuse all three original contract test files and add schema validation of real responses.
Positive: round-trip each endpoint/entity. Negative: each required field, bad enum, invalid reference,
unbound approval, empty geography, reversed date and illegal transition. Edge: optional nulls,
pagination, empty lists, legacy client/version compatibility and mutation after construction. Assert
contract statuses/methods and no state change on validation error. Proposed additional model-invariant
test file: `tests/unit/test_disaster_hub_domain_invariants.py` (not existing evidence).

**Dependencies:** Coordinate with AUD-001/003/006/012/014/015. **Future validation:** Installed local
schema tooling, `python -m pytest tests/contract/test_live_incident_contract.py
tests/contract/test_persona_workspace_contract.py tests/contract/test_preparedness_contract.py` plus
the proposed invariant suite; web client fixture tests afterward. **Acceptance:** Every original
contract endpoint and data-model validation rule is asserted or explicitly superseded by an approved,
versioned compatibility decision; no unchecked casts conceal wire mismatches.

### AUD-017: Localize All Operator Surfaces, Not Only Language Metadata

- [x] Resolve AUD-017 and obtain native-speaker review evidence.

**Affected:** T049, T050, T028, T037, T048; FR-010/011; NFR-013; ASM-004/008; EDGE-06.

**Evidence and impact:** [LanguageSwitcher](../../apps/web/src/components/accessibility/language-switcher.tsx#L25)
changes `lang`/`dir` but no strings, and scoped web search found no mounted caller. The
[root layout](../../apps/web/src/app/layout.tsx#L18) is English; original incident/workspace/preparedness
copy is hardcoded. [AlertLanguagePreview](../../apps/web/src/components/alerts/alert-language-preview.tsx#L10)
substitutes fixed translations, even for English, instead of translating the actual draft. The newer
[language registry](../../apps/web/src/lib/i18n/language-packs.ts#L40) supplies language metadata and
fallbacks, not a complete two-language operator catalogue. Availability checks cannot prove correct
localized content, formats or native-speaker approval.

**Developer:** Introduce/reuse an actual en-AU and zh-Hans message catalogue for every operator surface
and error/state, wire persistent locale selection, localize date/number formats and document RTL readiness.
Render actual reviewed alert variants and explicitly label unavailable translations; never substitute a
generic evacuation instruction for different approved content. Preserve community-review requirements.

**Tester:** Extend the existing [multilingual browser tests](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts#L16)
to traverse each original P1 flow in both languages. Positive: content/format parity and persistent locale.
Negative: missing key, untranslated error, stale translation, wrong content version. Edge: mixed scripts,
long text, Arabic direction preview, device refresh and unsupported locale. Record native-speaker review
against actual rendered strings and source versions, not a list of available pack IDs.

**Dependencies:** AUD-008/010/012/015/019. **Future validation:** Localized fixtures and browsers,
`corepack pnpm --filter @ama/web exec playwright test accessibility-and-multilingual.spec.ts
--project=web-coverage-chromium`, expanded to real flows, plus manual native-speaker review.
**Acceptance:** All operator surfaces are usable in both v1 languages with correct formats; 100% locale
conformance and language review are evidenced for the release. Current conformance is UNVERIFIED.

### AUD-018: Preserve Offline Actions Until Safe Reconciliation

- [x] Resolve AUD-018 before claiming degraded-connectivity completion.

**Affected:** T049, T038, T055; FR-014/014a; NFR-005; ASM-003/008; HYP-004; US2-3; EDGE-04.

**Evidence and impact:** [Original connectivity banner](../../apps/web/src/components/offline/connectivity-banner.tsx#L11)
is unmounted, assumes online initially and adds listeners during render without cleanup. Newer
[registration](../../apps/web/src/app/%28operations%29/_offline-bootstrap.tsx#L15) exists, but the
[service worker](../../apps/web/public/offline-sw.js#L8) is explicitly a no-op and the scoped source
search found no application caller of offline queue `enqueue`. Original task clients throw on failure.
[Queue drain](../../apps/web/src/lib/offline/queue-store.ts#L216) deletes entries before
[replay](../../apps/web/src/app/workspaces/%5BpersonaId%5D/_panels/field-coordinator-offline.tsx#L94)
sends them; failed requests are counted but not restored. Stored actions do not bind tenant/incident/mode
and a generic replay does not preserve original HTTP method or verified actor. Encrypted storage has a
plaintext fallback when crypto is unavailable. Connectivity display is not reliable offline operation.

**Developer:** Wire permitted mutations into a scoped durable queue and expose cached read freshness.
Lease/peek items, then acknowledge deletion only after validated server success; retain retryable
failures and surface conflicts/rejections for review. Bind actor/tenant/incident/mode/method and expiry,
reauthorize on reconnect, prevent duplicate dispatch, and never replay public warning authorization
automatically. Fail safely if encryption is required but unavailable. Register and clean listeners
within component lifecycle on the routes that actually need them.

**Tester:** Extend [queue tests](../../apps/web/tests/unit/spec_035/offline-queue-store.test.ts#L1),
[offline boundaries](../../tests/integration/test_field_coordinator_offline_boundaries.py#L28) and the
mounted field browser flow. Positive: queued routine action survives reload and reconciles once.
Negative: network failure after draining, 401/403/409/500, expired identity, cross-tenant replay and
unsafe public dispatch. Edge: crash after server commit, multiple tabs, queue at capacity, no crypto,
30-minute outage and 64 kbps reconnect. Assert no lost or duplicated action and truthful pending/error UI.

**Dependencies:** AUD-001/002/003/013/026/031. **Future validation:** Fake IndexedDB/transport fixtures,
`corepack pnpm --filter @ama/web exec vitest run tests/unit/spec_035/offline-queue-store.test.ts`, then
browser network-shaping with approved replay fixtures. **Acceptance:** No queued action is removed
before successful reconciliation; identity/mode remain isolated and every P1 task has an explicit
supported, queued or blocked degraded behavior. Connectivity/performance targets need later measurements.

### AUD-019: Verify Accessibility Across Complete P1 Journeys

- [x] Resolve AUD-019 with automated and manual accessibility evidence.

**Affected:** T012, T020, T028, T031, T037, T048, T049, T054, T055; NFR-001; FR-010/011;
P-ACC-SCREEN, P-ACC-VOICE, P-COM-DISAB; ASM-008.

**Evidence and impact:** [Shell](../../packages/ui/src/components/layout/app-shell.tsx#L17) supplies
landmarks and a labelled navigation toggle, so accessibility scaffolding exists. The
[newer axe tests](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts#L16)
visit three landing surfaces, not complete original incident approval/task/rehearsal journeys. Original
browser tests are mocked and do not inspect keyboard/screen-reader behavior. The
[PIO scan](../../apps/web/src/app/workspaces/%5BpersonaId%5D/_panels/pio-aws-composer.tsx#L84) runs only
older `wcag2a/wcag2aa` tags and labels results WCAG 2.1; this is not WCAG 2.2 AA evidence. No local
signed manual screen-reader/switch/high-contrast audit is present in the feature evidence directory.
The shared [axe builder](../../tests/e2e/web-coverage/_support/a11y/axeBuilder.ts#L7) does include WCAG 2.2
tags, but explicitly disables `color-contrast` and `region`; its green result would not prove full AA.

**Developer:** Restore required P1 actions first, then fix labels, focus order/return, status announcements,
keyboard affordances, touch targets, contrast and error recovery found on actual journeys. Ensure
language variants, long text and mobile layouts remain equivalent. Broaden accessibility test scope
and use the required WCAG 2.2 tags; do not market an in-page scanner as a full conformance certification.

**Tester:** Automated checks on every state of incident review/approval, persona task updates and
preparedness replay in both languages. Manual NVDA/JAWS or agreed supported screen reader, keyboard-only,
voice/switch, high-contrast and touch walkthroughs. Positive: all P1 actions complete. Negative:
validation errors, modal focus, unavailable/degraded data and disabled actions. Edge: zoom, 1366x768,
small mobile viewport, long translation and network interruption. Record issue IDs, tester identity,
device/browser/version and completion denominator.

**Dependencies:** AUD-008/010/012/015/017/018. **Future validation:** Installed axe/Playwright browsers,
expanded multilingual test above on Chromium/mobile, then Accessibility Insights and manual assistive
technology protocol. **Acceptance:** Zero WCAG 2.2 A/AA violations on all P1 flows and at least 95%
keyboard-only completion; full manual review signed for the release. These outcomes remain UNVERIFIED.

### AUD-020: Align Active Infrastructure and Rollback with Reliability Requirements

- [ ] Resolve AUD-020 through an approved reliability design and implementation.

Status note (2026-09-15): Non-Bicep automation for AUD-020 is complete in CI/CD workflows and devops workflow tests (PR trigger + reusable eval gate contract, fail-closed quality thresholds, and rollback on health-or-quality failure). The item remains open because required reliability topology remediation in active IaC/Bicep and external governance approval are blocked by unverified Azure Policy inheritance and unavailable Portal parity.

**Affected:** T007, T017, T051, T052; NFR-004/005/009; ASM-004/005; plan scale and graceful degradation.

**Evidence and impact:** [Deployment descriptor](../../azure.yaml#L8) selects the root template, whose
[Cosmos account](../../infra/main.bicep#L580) has one location, [Blob store](../../infra/main.bicep#L493)
uses LRS, and [web plan](../../infra/main.bicep#L1258) is Basic B1. The template does not wire paired-region
compute/failover despite [DR runbook claims](../../docs/operator-runbooks/dr-bcp.md#L58).
[Active monitoring](../../infra/modules/monitoring.bicep#L107) calls Maximum request duration "p99" and
does not cover the original NFR's p95/quality thresholds. [CD](../../.github/workflows/cd.yml#L1)
rolls back after health-check failure only; [eval gate](../../.github/workflows/eval-pr-gate.yml#L3)
is manually triggered and can skip unconfigured evaluation. No inspected active path binds <=2%
hallucinations or <=5% false positives to rollback within ten minutes. Separate old progressive-delivery
artifacts were explicitly retired in [CODEOWNERS](../../.github/CODEOWNERS#L28); do not resurrect them
merely because a historical task named them.

**Developer:** Wire a supported AU paired-region HA/recovery topology for state, API, agents and web;
align backup, compute, routing and state replication with RPO/RTO. Implement telemetry for the stated
AI quality floor and an auditable automatic rollback/manual-takeover path within ten minutes. Correct
percentile alerts and real dependency health. Reuse approved current modules; honor policy/AVM review
requirements and do not silently broaden the Foundry-only residency exception.

**Tester:** Inspect the expanded active deployment with approved parameter sets, then later test one
agent, service and AU region unavailable. Positive: healthy operation and restored primary. Negative:
stale replica, missing DR origin, quality breach, absent telemetry and rollback failure. Edge: quality
threshold equality, partial degradation, concurrent incidents and failback without duplicate actions.
Use disposable rehearsal data and capture actual state/traffic restoration rather than only CLI duration.

**Dependencies:** AUD-002/004/007/009/026. **Future validation:** Bicep toolchain, approved target
subscription policy snapshot and review permission; `bicep build infra/main.bicep` and a separately
approved What-If review, then the [DR drill workflow](../../.github/workflows/dr-drill.yml#L1) after
correcting its measurement scope. **Acceptance:** Active manifests supply the agreed HA/DR paths;
later evidence proves >=99.9% availability, RPO <=15 min, RTO <=1 h and AI rollback <=10 min.

### AUD-021: Enforce Privacy Classification, Retention, Erasure and Transit Rules

- [x] Resolve AUD-021 with privacy-owner-approved data lifecycle controls.

**Affected:** T007, T013, T021, T022, T023, T051; NFR-002/007/009/012; FR-004/005/012;
ASM-005; constitution privacy/data-minimization boundary.

**Evidence and impact:** [Original ingestion](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L26)
persists arbitrary payload/provenance without a classification or retention decision. The newer
[classifier](../../apps/api/app/middleware/classifier_gateway.py#L34) is opt-in and protects only five
newer route families. [Taxonomy](../../docs/safety/classification-taxonomy.md#L6) and
[model gateway](../../apps/agents/common/model_gateway.py#L191) exist, but source existence does not
prove every storage/transit call uses them; [dispatcher](../../apps/agents/dispatcher/agent.py#L238)
directly calls its model client. [SAR helper](../../apps/api/app/api/routes/audit_compliance.py#L80)
reports deletion unsupported, imports a repository factory absent from the inspected repository, and
converts errors into empty results; its router is not registered in the inspected main router. Scoped
API/domain/workflow search found no operational erasure request/SLA or full entity retention enforcement.
The [SAR tests](../../tests/contract/test_privacy_act_sar.py#L34) assert descriptive metadata, not those controls.
No actual cross-border leak or legal exemption is inferred here.

**Developer:** Inventory/classify every PII-carrying entity and wire collection, viewer, retention and
verified erasure rules into actual ingress/storage/replay paths. Implement <=30-day operational retention,
seven-year evidence/audit policy with legal-hold reconciliation, and <=30-day verified erasure SLA under
privacy counsel's resolved policy. Route every non-AU model call through the approved minimization and
carve-out registry checks; do not let a direct client bypass them. Distinguish failed SAR retrieval from
no records and require authenticated subject/role scoping. Preserve immutable audit of lifecycle actions.

**Tester:** Extend the existing SAR contract tests through the mounted API and add proposed lifecycle
cases in that file or `tests/integration/test_disaster_hub_privacy_lifecycle.py` (proposed). Positive:
classified data with permitted retention and verified erasure request. Negative: unclassified data,
forged subject, unauthorized export, non-AU unapproved transit, protected content and backend failure.
Edge: legal hold, backups/caches, expiry boundary, duplicate request and classifier failure. Assert real
data disposition and no outbound call on deny, not a notice string.

**Dependencies:** AUD-001/002/004/006/022. **Future validation:** Synthetic PII fixtures and fake clocks,
`python -m pytest tests/contract/test_privacy_act_sar.py tests/integration/test_carveout_enforcement.py`,
then approved retention/SAR/erasure evidence with privacy reviewer. **Acceptance:** 100% classification,
bounded retention and measured erasure SLA across all copies; unapproved sensitive non-AU transit denied.

### AUD-022: Make Environment and Identity Configuration Consistent and Fail Closed

- [x] Resolve AUD-022 and collect security-posture evidence.

**Affected:** T005, T006, T007, T008, T051; NFR-003; ASM-005; startup and production security assumptions.

**Evidence and impact:** All four task-named environment templates exist. A key-name-only inspection
found [API template](../../apps/api/.env.example#L1) uses `ENTRA_TENANT_ID`, `ENTRA_AUDIENCE`,
`ENVIRONMENT`, `COSMOS_DB_ENDPOINT`, while [middleware](../../apps/api/app/middleware/entra_auth.py#L88)
requires `AMA_ENTRA_TENANT_ID`, `AMA_ENTRA_AUDIENCE`, and production auth activation. Actual
[settings](../../apps/api/app/core/settings.py#L12) use `AMA_ENVIRONMENT`; repositories use `COSMOS_ENDPOINT`.
[Root template](../../.env.example#L1) and [agents template](../../apps/agents/.env.example#L1) mix further
deployment/runtime aliases. [Web template](../../apps/web/.env.local.example#L1) has a proxy key, but
[active web settings](../../infra/main.bicep#L1300) use `API_ENDPOINT` while
[rewrite config](../../apps/web/next.config.ts#L7) selects other names. The active API template does not
enable the required auth variables. MFA, session binding/lifetimes, accepted threat-model and HSM-backed
secret posture require tenant/config evidence; role names and optional signing modules do not prove them.
No secret values were copied or an exhaustive zero-secret certification claimed.

**Developer:** Define one documented deployment-to-runtime environment mapping, validated at startup.
Make production-required identity, scopes, persistent stores, secure proxy and secret references fail
closed when missing/malformed; isolate explicit test modes. Require phishing-resistant MFA and the
<=1 h access/<=24 h refresh policy through documented Entra controls. Inventory secrets and bind the
agreed managed HSM-backed store; obtain accepted STRIDE review rather than assuming a document title
means approval. Preserve canonical Foundry settings and documented compatibility aliases.

**Tester:** Add proposed configuration contract cases to existing auth/tenant tests. Positive: each
supported environment mapping resolves to intended endpoints and verified principal. Negative: wrong
alias, missing audience/tenant, malformed region list, expired/unbound token, production test principal
and browser proxy pointing to localhost. Edge: container versus repo cwd, secret rotation, DR endpoint
and disabled dev fixtures. Check sanitized diagnostics never disclose values.

**Dependencies:** AUD-001/002/020/021/029. **Future validation:** Disposable environment with synthetic
configuration, `python -m pytest tests/unit/test_management_auth.py tests/unit/test_tenant_context.py`
extended to original JWT startup; separately authorized Entra/session/HSM posture inspection.
**Acceptance:** Template-driven setup is coherent, production cannot start insecurely, and named security
reviewers provide revision-bound MFA/session/secret/threat-model evidence.

### AUD-023: Gate the Original Acceptance Slice and Correct Misleading Test Coverage

- [x] Resolve AUD-023 without retroactively claiming TDD chronology.

**Affected:** T004, T014, T016, T018, T019, T020, T029, T030, T031, T039, T040, T041, T054, T055;
constitution PR quality gates; all three independent story tests.

**Evidence and impact:** [CI Python test step](../../.github/workflows/ci.yml#L138) runs contract and
integration directories, not original simulation tests; its web shard targets `web-coverage-chromium`,
whose [configuration](../../apps/web/playwright.config.cts#L47) excludes the three original browser
tests by directory. No original Chromium/mobile acceptance run or web lint is present in that workflow.
[ESLint helper import](../../apps/web/eslint.config.mjs#L9) resolves to `apps/tests/...`, not the actual
root [rule](../../tests/e2e/web-coverage/_support/eslint-rules/no-waitfortimeout.cjs#L1).
Original integration tests often invoke helpers only, browser tests mock every relevant API response,
and the ingestion tests use non-discriminating `>= 0` assertions. The `.ts` Playwright filename is not
missing functionality: [the current `.cts` file](../../apps/web/playwright.config.cts#L1) is its replacement.

**Developer:** Correct config resolution and add the original three-story acceptance slice to required
CI checks alongside existing suites. Retain component mocks for focused tests but provide full API-backed
flow coverage, real schema assertions, scoped persistence and negative safety cases. Explicitly mark
external staging gates/skips; a skip, zero-case run or mocked downstream outcome must not count as acceptance.

**Tester:** Review each original test's assertions against the corresponding task/requirement. Positive:
valid three-story fixture flows. Negative: introduce representative schema/auth/dispatch/degraded
regressions and ensure the relevant assertion fails. Edge: empty collections, no collected tests,
skipped prerequisites, mobile flow, offline behavior and two-persona state changes. Record future
red/green evidence honestly; original "write failing tests first" chronology remains UNVERIFIED unless
historical revision/run evidence independently establishes it.

**Dependencies:** AUD-001 through AUD-019 as applicable. **Future validation:** Python 3.12+, approved
locked Node/pnpm toolchain and installed browsers; selected original contract/integration/simulation
files, then `corepack pnpm --filter @ama/web lint` and the three original browser files on Chromium/mobile.
All external environment variables must be isolated/mocked before a hermetic run. **Acceptance:** The
required CI workflow collects and enforces each original story's positive/negative assertions; no
critical requirement is represented solely by a filename, stub, zero-count assertion or unchecked skip.

### AUD-024: Compute Original Success Criteria from Comparable Complete Measurements

- [x] Resolve AUD-024 before using KPI results for acceptance or release claims.

**Affected:** T053, T054, T055; SC-001 through SC-007, especially SC-004/005/006/007; ASM-006;
HYP-001/002/003; evaluation baseline and UX method.

**Evidence and impact:** [ExerciseMetricsService](../../apps/api/app/services/exercise_metrics_service.py#L43)
does not require paired scenario/jurisdiction/roles/run types. SC-006 uses assignment time alone despite
the [specified three-component composite](../../docs/disaster-response-hub/evaluation/baseline-metrics.md#L51).
SC-007 uses means >=4, not the [required proportion of participants](../../docs/disaster-response-hub/evaluation/ux-rubric.md#L17).
Missing measures are omitted from `overall_pass`, allowing a partial set of successful results to pass.
The service is uncalled in the inspected production API. [Tests](../../tests/simulation/test_exercise_metrics.py#L6)
supply constants, do not assert overall failure for the 3.5-hour SC-005 shortfall, and omit mismatched
cohorts/missing metrics. Later [outcome evaluator](../../apps/api/app/services/outcome_evaluator_service.py#L65)
uses different spec-local SC meanings, and [new scorecards](../../apps/api/app/services/evidence/simulation/scorecard_builder.py#L53)
use synthetic pairs. Neither is evidence of original SC achievement.

**Developer:** Capture timestamped event/actor metrics from real rehearsals, namespace criterion IDs by
spec, and enforce matching scenario/version/jurisdiction/roles/controller rules across baseline and hub.
Validate ranges/timestamps and complete denominators. Implement the agreed normalized resource composite
and participant-level 85% rubric calculation. Missing or inapplicable measures must produce explicit
incomplete/provisional results, never an overall pass. Retain raw evidence and provenance to each result.

**Tester:** Extend the existing metric simulation test with exact 50%, 24 h, 30%, 85% boundaries,
slightly failing values, high mean with <85% favourable participants, worsened utilization/unfilled
requests despite faster assignments, mismatched scenario/roles, missing fields, duplicate IDs and
negative durations. Positive: complete comparable real-shaped pair. Assert independent recomputation,
all seven criterion statuses, and no pass from incomplete/synthetic data.

**Dependencies:** AUD-004/013/015/025. **Future validation:** Local timestamp/participant fixtures,
`python -m pytest tests/simulation/test_exercise_metrics.py`; later paired exercise capture after
instrumentation. **Acceptance:** Original criteria and all component denominators match their normative
definitions; every number is traceable to observed inputs and partial/invalid evidence cannot pass.

### AUD-025: Obtain Original Success-Criterion, Assumption and Hypothesis Evidence

- [x] Resolve AUD-025 automatable evidence-binding validation and CI gating; external exercise evidence remains open.

**Affected:** T053, T054, T055; SC-001/002/003/004/005/006/007; ASM-001/002/003/004/005/006/007/008,
ASM-080/081; HYP-001/002/003/004/005/006; all acceptance scenarios.

**Evidence and impact:** [Quickstart](quickstart.md#L57) claims automated success without a linked
revision-bound run bundle. The [dated rehearsal record](../../docs/disaster-response-hub/evaluation/quickstart-rehearsal-results-2026-03-16.md#L7)
is for feature 003, reports historical local results and explicitly skips live LLM validation; it does
not prove current-revision behavior or human-cohort outcomes. All six local HYP evidence packs still
contain placeholders and status Proposed. [KPI template](../../docs/disaster-response-hub/evaluation/kpi-template.csv#L1)
and test constants are not independent raw exercise observations. A test assertion, synthetic scorecard,
role label or checkbox does not establish timing, human approval, causal benefit or SME sign-off.

**Developer:** Finish instrumentation and provide deterministic fixture/version IDs, event export,
participant/role provenance and raw-to-score traceability for all criteria. Separate example data,
synthetic projections, current test runs, staging trials and actual cohort studies in UI/docs. Preserve
historical evidence rather than relabelling it. Maintain Proposed status until dual-control/privacy
signatures and hypothesis methods actually occur; invalidation must reopen linked decisions/SCs.

**Tester:** Recruit the required Australian cohort (>=3 tier-1 agencies for SC-001; >=3 organisation
types and >=5 operational personas for SC-007; all eight canonical roles in SC-003 coverage). Time identification
<5 min, first coordinated plan <10 min, >=90% unaided first-attempt priority completion, >=50% matched
response improvement, >=24 h earlier authorized evacuation, >=30% resource composite improvement, and
>=85% favourable rubric results. Negative/edge cases: failed cohort coverage, no baseline, changed
controller rules, compressed time, aided completion, missing raw data, failed safety boundary and
provisional/invalidated hypothesis. Run the six HYP methods with their stated cadence/two-cycle
conditions and agree HYP-005's currently unspecified tolerance before measurement.

**Dependencies:** AUD-001 through AUD-024 and AUD-029/031. **Future validation:** After fixes, run
`python -m pytest tests/simulation/test_quickstart_rehearsals.py tests/simulation/test_exercise_metrics.py`
and all three original browser flows, then execute the [survey](../../docs/disaster-response-hub/evaluation/post-exercise-survey.md#L1)
and [baseline protocol](../../docs/disaster-response-hub/evaluation/baseline-metrics.md#L1) with signed
observations. **Acceptance:** Each SC has raw evidence, correct denominator, revision, evaluator and
pass/fail/provisional result; each promoted ASM/HYP has named independent approval. No original historical
TDD or approval is invented. All current empirical outcomes remain UNVERIFIED in this audit.

### AUD-026: Measure NFR Outcomes with Real Network, Recovery and Residency Evidence

- [x] Resolve AUD-026 automatable harness and workflow scaffolding; authorized staging execution evidence remains open.

**Affected:** T007, T051, T054, T055; NFR-004/005/008/009/012; ASM-003/005/008; plan scale targets.

**Evidence and impact:** [Health benchmarks](../../tests/benchmark/test_api_performance.py#L1) explicitly
use in-process transport with no TCP; they do not measure situation refresh, alert visibility, operator
round trip or degraded mobile bandwidth. [DR workflow](../../.github/workflows/dr-drill.yml#L51)
times a failover command and asks someone to attach RPO evidence later. [Audit tests](../../tests/integration/test_audit_replay.py#L103)
reconstruct synthetic replay keys, not an actual one-month archive restore. [Audit immutability tests](../../tests/integration/test_audit_immutability.py#L19)
exercise evidence API denial, not storage-level seven-year WORM. Static AU locations do not prove all
replicas, backups, telemetry, secrets or cloud policy compliance. These are evidence limitations, not
claims of measured production failure.

**Developer:** Add instrumentation for end-to-end latency stages, immutable audit timing, restoration,
regional/copy inventory and quality-floor rollback. Expose degraded state and observation provenance;
prepare reproducible workload/configuration manifests for 1,000 operators and 50,000 signals/hour.
Extend the actual DR drill to time restored user workflows and compare committed writes, not CLI completion.

**Tester:** Positive: online and 64 kbps scenarios, controlled failure/recovery and retained audit replay.
Negative: lost replica, missing backups, out-of-region persistence, sampling gaps, source outage and
broken rollback. Edge: 30-minute disconnect, burst ingestion, percentile sample insufficiency,
duplicate/reordered events, leap-year retention and restore under load. Prerequisites: approved staging
scope, synthetic-only data, authorized fault-injection/restore window, client devices, independent
observer, policy inventory access and zero public recipients.

**Future validation:** Component baseline via existing benchmark tests is not sufficient; add
`tests/load/test_disaster_hub_slos.py` (proposed) and run with a recorded staging profile, plus the
corrected DR workflow and manual audit/residency attestation. **Dependencies:** AUD-002/004/005/008/018/020.
**Acceptance:** Measured p95 refresh <=3 s online/<=10 s at 64 kbps, alert visibility <=60 s, action
round trip <=2 s; plan initial load <2 s/read API p95 <500 ms measured separately; audit <=1 s and
replay <=5 min; availability >=99.9%, RPO <=15 min, RTO <=1 h, rollback <=10 min; 100% approved
AU storage/copies, seven-year audit and annual recoverability evidence. No measurements were run here.

### AUD-027: Establish Reliable Rehearsal and Monitored-Day Unit Costs

- [x] Resolve AUD-027 with finance-approved envelopes and reconciled telemetry.

**Affected:** T051, T053, T054; NFR-010; cost/scale assumptions in the plan.

**Evidence and impact:** [Cost reporting template](../../docs/operator-runbooks/cost-reporting.md#L1)
targets spend per recommendation and contains placeholders, not approved original-spec unit envelopes.
[BudgetTracker](../../apps/agents/common/llm_budget_tracker.py#L137) resets the stored total to one delta
on any read/replace exception, including conflicts; its no-container path instantiates a new memory
tracker per add. [Tests](../../tests/unit/test_spec032_llm_and_aiims.py#L85) exercise memory accumulation,
not the Cosmos failure path. The original rehearsal flow does not capture total per-run/per-24 h cost.
This can under-report spend; actual monetary variance is UNVERIFIED.

**Developer:** Define approved per-rehearsal and per-monitored-24 h denominators/envelopes and include
all platform resource costs, not only LLM tokens. Persist scoped period totals with safe concurrency,
distinguish not-found from transient failure, and never reset cumulative cost on conflicts. Reconcile
telemetry with cost exports and disclose incomplete attribution/failed export.

**Tester:** Extend the existing budget tests with injected Cosmos read/replace conflict/429/403 failures,
two concurrent increments, restart, month boundary, missing price, negative/duplicate costs and no
completed runs. Positive: known per-run/24 h totals reconcile exactly. Negative: absent approved budget
cannot pass; missing telemetry is incomplete. Edge: multi-tenant allocation and zero denominator.

**Dependencies:** AUD-002/015/024/026. **Future validation:** Synthetic cost/price fixtures,
`python -m pytest tests/unit/test_spec032_llm_and_aiims.py`, followed by finance-reviewed export
reconciliation in an authorized environment. **Acceptance:** No lost/reset spend increments; every run
and monitored day has traceable unit cost and approved envelope, with measured monthly variance <=20%
or explicit breach action. No cost queries were run in this audit.

### AUD-028: Bind Operator Training and Change Management to P1 Releases

- [x] Resolve AUD-028 automatable P1 inventory and release-gate enforcement; human training-delivery evidence remains open.

**Affected:** T052, T055; NFR-011; SC-003; all eight canonical operational personas.

**Evidence and impact:** [Operator runbooks](../../docs/disaster-response-hub/operator-runbooks.md#L1)
are authored, but [CI](../../.github/workflows/ci.yml#L1) and [CD](../../.github/workflows/cd.yml#L1)
contain no inspected gate linking each P1-changing release to a refreshed training pack and operator
release note. [Exercise schedule](../../docs/disaster-response-hub/evaluation/exercise-schedule.md#L1)
is a cadence, not proof of training delivery within five business days. Historical screenshots and
demo placeholders do not establish readiness of the amended seven-persona cohort.

**Developer:** Maintain a versioned P1-flow/change inventory and link every affected release to updated
runbooks, role task walkthroughs and operator notes. Add a release-evidence check for required artifacts,
owner, review and publication date. Keep training synchronized with the resolved live/rehearsal,
approval, offline and language behavior; reuse existing runbook/evaluation homes.

**Tester:** Positive: a P1-changing release has current material for all affected roles. Negative: missing,
stale or unsigned material blocks readiness; unaffected release is explicitly classified. Edge:
emergency release, rollback, public holidays and localization/accessibility changes. Have representative
operators perform top-priority tasks unaided using the released pack and record friction separately
from software execution metrics.

**Dependencies:** AUD-008/012/013/017/018/019/025/029. **Future validation:** Proposed
`tests/devops/test_p1_training_release_gate.py` verifies release-manifest fixtures; run it after authoring,
then perform the documented human walkthrough. **Acceptance:** 100% of P1-changing releases have a
reviewed training pack and operator note within five business days; release evidence proves the linkage.

### AUD-029: Reconcile Scope, Runbooks, Checkpoints and Formal Sign-Off Claims

- [x] Resolve AUD-029 automatable documentation/script contradiction checks without implying historical approvals occurred.

**Affected:** T052, T053, T055; plan gate claims, quickstart acceptance, ASM-001/080/081,
HYP-006, OD-001/002/003, SCP-080/081, status-transition authority and all local sign-off claims.

**Evidence and impact:** [Current spec](spec.md#L454) defers Asia and makes portability hypothetical,
but [regional adaptation guidance](../../docs/disaster-response-hub/regional-adaptation-asia-pacific.md#L7)
and architecture guarantee no code changes. The [quickstart](quickstart.md#L53) permits an alternate
approval mode contrary to [human-only/approved autonomy](spec.md#L500). Runbooks claim OPA enforcement,
cross-agency notification and complete audit not supported by the traced paths. [Plan PASS declarations](plan.md#L29)
are not current acceptance despite [OD-001's open plan blocker](spec.md#L583).
[ASM-081](spec.md#L603) aligns to the canonical eight-role wording now used by SC-003; external role-validation
sign-off remains open. Community top-three tasks include citizen requests/shelter capabilities that
[scope](spec.md#L529) defers. Clarify these obligations rather than silently claiming missing v1 scope.
[CODEOWNERS](../../.github/CODEOWNERS#L16) names the team but its claimed interim individual fallback is
commented out; actual team existence/PR approvals are UNVERIFIED. Role-labelled drafter/countersigner
cells and Proposed hypothesis files are not individual sign-off.

**Developer:** Align existing spec, plan, contracts, architecture, runbooks and training through an
explicit owner-reviewed reconciliation. Keep deferred country/recovery/citizen capabilities out of the
v1 completion denominator; reference their documented owners. Retire stale guarantees and alternate
autonomous public dispatch language. State which persona task surfaces are v1 and align evaluation.
Repair CODEOWNERS fallback if needed after verifying governance; do not fabricate approvals or close
Open Deltas without evidence. No new specification or branch is required by this audit task.

**Tester:** Positive: two independent reviewers can derive the same v1 jurisdiction, roles, hazards,
autonomy and release prerequisites from the reconciled documents. Negative: no-code-change guarantee,
unnamed approval, unresolved plan blocker, inconsistent scope or missing evidence must prevent sign-off.
Edge: intentional MAF/Foundry replacement, deferral promoted by later feature, absent maintainer team,
privacy third signature and invalidated hypothesis reopening linked decisions.

**Dependencies:** AUD-001 through AUD-028/030/031 findings inform reconciliation. **Future validation:**
`pwsh -File scripts/verify-spec-hardening.ps1` in a later authorized documentation-validation pass,
plus independent owner/SME/privacy review against actual PR records. **Acceptance:** No contradictory
current guarantee or unsubstantiated PASS remains; all scope decisions and status changes have their
required named reviewers, linked evidence and gap-register treatment. Shared audit index is not modified.

### AUD-030: Make Specialist Overrides and Replans Change the Actual Plan

- [x] Resolve AUD-030 before presenting specialist controls as operational.

**Affected:** T024, T034, T045; FR-009/012; US1-3; autonomy table and override requirement.

**Evidence and impact:** [Resource override](../../apps/agents/resource_allocation/agent.py#L382)
validates action/rationale and writes an audit record, but never loads or modifies the plan before
returning success. [Evacuation replan](../../apps/agents/evacuation/agent.py#L127) has no-op route,
transport, persistence and audit steps yet returns `material_change=True`; when supplied a plan it
compares it with itself. [Evacuation override](../../apps/agents/evacuation/agent.py#L500) skips storage
if unconfigured and reports an assumed transition. [Resource tests](../../tests/unit/test_resource_allocation_endpoints.py#L32)
and [evacuation tests](../../tests/unit/test_evacuation_endpoints.py#L76) assert response fields with no
persisted plan fixture. The current dispatcher does not make these fully deployed live endpoints;
this finding concerns claimed specialist implementation and the unsafe behavior if wired into operations.

**Developer:** Require a real scoped plan, verified authority, valid transition and concurrency token.
Persist resource reassignment/priority changes and route/transport/timeline recomputation as new versions;
retain old plan and approval lineage. Fail closed if persistence/replanning dependencies are unavailable.
Emit applied/material-change only after actual accepted plan differences, with audit tied to commit.

**Tester:** Extend the two existing endpoint suites with stored plans and real deterministic routing/
matching fixtures. Positive: approved override changes expected resource/route state and version.
Negative: unknown plan, missing backend, unauthorized actor, invalid transition or impossible route.
Edge: zero material change, blocked road creates shelter-in-place recommendation, concurrent override,
replan retry and partial failure. Assert before/after persistence and audit, not response text alone.

**Dependencies:** AUD-001/002/003/004/007. **Future validation:** Fake storage and fixed road/inventory
fixtures, `python -m pytest tests/unit/test_resource_allocation_endpoints.py
tests/unit/test_evacuation_endpoints.py`; mounted workflow integration after wiring.
**Acceptance:** Every successful control corresponds to a durable authorized plan change; failures and
no-change outcomes cannot masquerade as completed replanning or override.

### AUD-031: Make Rehearsal Egress Denial Independent of Tenant String Conventions

- [x] Resolve AUD-031 before configuring any public delivery transport.

**Affected:** T008, T014, T015, T024, T045, T049, T050, T055; FR-010/012/013;
rehearsal content boundary; constitution human authorization.

**Evidence and impact:** [Tenant semantics](../../apps/api/app/core/tenant_context.py#L12) treat every
non-`live` ID as simulation and the [partition helper](../../apps/api/app/repositories/cosmos_scope.py#L12)
generates `sim-...`. [Specialist delivery](../../apps/agents/communication/delivery.py#L66) blocks only
IDs beginning `simulation`; canonical `sim-...` takes the normal client path. Its
[test](../../tests/unit/test_communication_delivery.py#L169) uses `simulation-test` and no spy transport,
so it misses this bypass. Original [PublicAlert](../../packages/domain/src/domain/models/public_alert.py#L33)
has no immutable mode/tenant field, and [original delivery](../../apps/api/app/services/public_alert_service.py#L87)
uses current request context, not the artifact's origin. This is a demonstrated guard mismatch and a
conditional egress risk when a real client is configured, not a claim that a public message was sent.

**Developer:** Require an immutable stored live/rehearsal discriminator and matching verified scope
at all draft/export/approval/delivery boundaries. Fail closed on absent/unknown/mismatched mode, not
prefix-based allow-by-default. Route rehearsal to synthetic receipts only and keep visible rehearsal
watermarks; public CAP/export must not label rehearsal as Actual. Explicit switching must not relabel
old artifacts or permit concurrent live/rehearsal side effects.

**Tester:** Extend delivery/isolation tests with configured spy transports and tenant IDs `live`,
`sim-...`, `simulation-...`, unknown and missing. Positive: authorized approved live version reaches only
its intended fake recipient. Negative: every rehearsal/unknown/mismatched artifact produces zero public
client calls regardless of current operator mode. Edge: restart, queued replay after mode switch,
cross-tenant artifact ID, draft export, mixed-case IDs and repeated delivery. Assert immutable mode,
watermark and synthetic receipt, not merely a returned status.

**Dependencies:** AUD-001/002/003/004; prerequisite to AUD-007/010/015/018. **Future validation:**
`python -m pytest tests/unit/test_communication_delivery.py tests/integration/test_tenant_isolation.py`
with spy adapters only; separately approved network-denial proof later. **Acceptance:** Rehearsal
artifacts cannot invoke a public transport or become Actual/live at any boundary, including mode changes.

## Task Coverage

All 55 original tasks were independently traced; their original checkboxes are all checked. There are
145 distinct task-named paths: all exist except the renamed Playwright configuration, whose current
`.cts` replacement was read. Existence was followed by source and assertion review, not counted as
behavioral proof. Authored-test statuses below describe assertion adequacy, not execution or historical
red-before-green TDD. Those execution claims remain UNVERIFIED under AUD-025.

| Original task | Original state | Status | Concrete evidence / remaining obligation | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [x] | IMPLEMENTED | Monorepo skeleton supported by [API](../../apps/api/app/main.py#L25), [web](../../apps/web/package.json#L1), [agents](../../apps/agents/pyproject.toml#L5), [domain](../../packages/domain/src/domain/models/incident.py#L29), [schemas](../../packages/schemas/openapi.yaml#L1), [UI](../../packages/ui/package.json#L1), [IaC](../../infra/bicep/monitoring.bicep#L1), [policies](../../infra/policies/tenant-isolation.rego#L4), [tests](../../tests/conftest.py#L11). | - |
| T002 | [x] | IMPLEMENTED | [Root manifest](../../pyproject.toml#L1), [API manifest](../../apps/api/pyproject.toml#L1), [agent manifest](../../apps/agents/pyproject.toml#L1) define Python runtime/dependencies and package targets; no install/build was executed. | AUD-022 |
| T003 | [x] | IMPLEMENTED | [Root package](../../package.json#L1), [workspace](../../pnpm-workspace.yaml#L1), [web package](../../apps/web/package.json#L1), [UI package](../../packages/ui/package.json#L1) wire the shared web workspace. | - |
| T004 | [x] | PARTIAL | [CI](../../.github/workflows/ci.yml#L138), [ruff](../../ruff.toml#L1), [ESLint](../../apps/web/eslint.config.mjs#L9), [replacement Playwright config](../../apps/web/playwright.config.cts#L1): gates exist but original acceptance slice omitted and lint helper path wrong. | AUD-023 |
| T005 | [x] | PARTIAL | [Root](../../.env.example#L1), [API](../../apps/api/.env.example#L1), [agents](../../apps/agents/.env.example#L1), [web](../../apps/web/.env.local.example#L1) templates exist; key names do not consistently match [runtime auth](../../apps/api/app/middleware/entra_auth.py#L88) and [settings](../../apps/api/app/core/settings.py#L12). Values were not reproduced. | AUD-022 |
| T006 | [x] | IMPLEMENTED | [Application factory](../../apps/api/app/main.py#L25), [router assembly](../../apps/api/app/api/router.py#L56), [settings](../../apps/api/app/core/settings.py#L7) form the requested bootstrap; [contract source](../../tests/contract/test_live_incident_contract.py#L45) instantiates it. Runtime success unverified. | AUD-022, AUD-025 |
| T007 | [x] | PARTIAL | [Registry](../../apps/api/app/core/azure_clients.py#L8) holds empty client endpoints and only creates [region policy](../../apps/api/app/core/residency.py#L15); later [Cosmos client](../../apps/api/app/repositories/signal_repository.py#L8) exists separately without full residency/HA enforcement. | AUD-002, AUD-020, AUD-022, AUD-026 |
| T008 | [x] | PARTIAL | [Principal extraction](../../apps/api/app/core/auth.py#L16), [role checks](../../apps/api/app/api/dependencies/rbac.py#L6), [tenant context](../../apps/api/app/core/tenant_context.py#L6), [middleware](../../apps/api/app/middleware/tenant_middleware.py#L20) exist; original routes are outside [JWT/RBAC protection](../../apps/api/app/middleware/entra_auth.py#L37). | AUD-001, AUD-002, AUD-031 |
| T009 | [x] | PARTIAL | [Timeline](../../packages/domain/src/domain/models/timeline_event.py#L7), [provenance](../../packages/domain/src/domain/models/provenance.py#L6), [AuditService](../../apps/api/app/services/audit_service.py#L4) are mutable/build-only; [new request audit](../../apps/api/app/middleware/audit_appender.py#L146) is best-effort, not full incident history. | AUD-004 |
| T010 | [x] | IMPLEMENTED | [Shared OpenAPI](../../packages/schemas/openapi.yaml#L1) and [signal schema](../../packages/schemas/signal-envelope.schema.json#L1) contain the feature contracts with additive later fields/endpoints. Artifact publication is implemented; runtime conformance is separately contradicted. | AUD-016 |
| T011 | [x] | PARTIAL | [Event bus](../../apps/api/app/services/event_bus.py#L28) supports subscribers/dead letters, but no original ingestion publisher; [handoffs](../../apps/agents/common/handoffs.py#L1) explicitly superseded by [MAF builder](../../apps/agents/maf_runtime/workflow/builder.py#L61), whose live integration is incomplete. | AUD-004, AUD-007 |
| T012 | [x] | IMPLEMENTED | [Tokens](../../packages/ui/src/styles/tokens.css#L1), [shell](../../packages/ui/src/components/layout/app-shell.tsx#L17), [CSS import](../../apps/web/src/app/globals.css#L1), [layout usage](../../apps/web/src/app/layout.tsx#L18) establish the design foundation; accessibility/UX outcomes are not inferred. | AUD-019, AUD-025 |
| T013 | [x] | PARTIAL | [Bootstrap](../../packages/domain/src/domain/seed/bootstrap.py#L42) and [cached seed service](../../apps/api/app/services/seed_service.py#L8) load data; [policy model](../../packages/domain/src/domain/models/jurisdiction_policy.py#L4) lacks retention/AU checks; [separate loader](../../scripts/load_jurisdiction_policies.py#L40) is not the original decision-path bootstrap. | AUD-002, AUD-014, AUD-021 |
| T014 | [x] | PARTIAL | [Tests](../../tests/integration/test_tenant_isolation.py#L10) compare agency scope strings and memory simulation partitions; they do not prove authenticated original API cross-agency/region boundaries or Cosmos point-read parity. | AUD-001, AUD-002, AUD-023, AUD-031 |
| T015 | [x] | PARTIAL | [Partition coordinator](../../apps/api/app/services/tenant_partitioning.py#L7), [Cosmos keys](../../apps/api/app/repositories/cosmos_scope.py#L4), [cache](../../apps/api/app/services/cache_scope.py#L4), [events](../../apps/api/app/services/event_scope.py#L4) only build strings; [state store](../../apps/api/app/services/state_store.py#L16) bypasses them. | AUD-002, AUD-009 |
| T016 | [x] | PARTIAL | [Reduced-function test](../../tests/integration/test_reduced_function_mode.py#L5) directly calls helpers and checks manual-review fields, not mounted API/UI suppression or source outages. | AUD-009, AUD-023 |
| T017 | [x] | PARTIAL | [Evaluator](../../apps/api/app/services/degraded_mode_service.py#L10) and [guardrail](../../apps/api/app/services/recommendation_guardrails.py#L4) have no original API callers and do not rank/suppress affected recommendations. | AUD-009 |
| T018 | [x] | CONFLICT | [Live contract test](../../tests/contract/test_live_incident_contract.py#L47) asserts POST 200 and anonymous approval/publication, contrary to [OpenAPI](contracts/openapi.yaml#L77) and authority requirements; pre-seeds outcomes. | AUD-001, AUD-003, AUD-016, AUD-023 |
| T019 | [x] | PARTIAL | [Integration test](../../tests/integration/test_live_incident_coordination.py#L8) asserts scalar scoring and helper guardrails only, not fusion, approval-to-alert or COP propagation. | AUD-003, AUD-006, AUD-007, AUD-009, AUD-023 |
| T020 | [x] | CONFLICT | [Browser test](../../tests/e2e/test_incident_commander_dashboard.spec.ts#L62) requests an approval button absent from [current incident page](../../apps/web/src/app/incidents/%5BincidentId%5D/page.tsx#L38); all relevant API responses are mocked. | AUD-008, AUD-023 |
| T021 | [x] | PARTIAL | [Incident](../../packages/domain/src/domain/models/incident.py#L29), [source](../../packages/domain/src/domain/models/data_source.py#L37), [signal](../../packages/domain/src/domain/models/signal.py#L7), [assessment](../../packages/domain/src/domain/models/hazard_assessment.py#L20), [recommendation](../../packages/domain/src/domain/models/recommendation.py#L7), [decision](../../packages/domain/src/domain/models/approval_decision.py#L7), [alert](../../packages/domain/src/domain/models/public_alert.py#L33) exist but miss specified invariants. | AUD-003, AUD-006, AUD-016, AUD-031 |
| T022 | [x] | PARTIAL | [Envelope](../../apps/api/app/validators/signal_envelope.py#L25) validates only some fields; [scorer](../../apps/api/app/services/provenance_scoring_service.py#L13) is not called by original ingress. | AUD-005, AUD-006, AUD-016 |
| T023 | [x] | PARTIAL | [Authoritative](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L11), [IoT](../../apps/api/app/services/ingestion/iot_ingestion.py#L7), [community](../../apps/api/app/services/ingestion/community_ingestion.py#L7) share an untrusted memory normalizer; [new worker](../../apps/ingestion/worker.py#L201) omits normalized persistence/audit wiring. | AUD-002, AUD-005, AUD-006 |
| T024 | [x] | PARTIAL | [Monitoring](../../apps/agents/monitoring/agent.py#L37), [risk](../../apps/agents/risk_assessment/agent.py#L65), [communication](../../apps/agents/communication/agent.py#L111) contain specialist logic; [deployed dispatcher entry](../../apps/agents/Dockerfile#L47) and original ingress do not execute the complete typed operational chain. | AUD-007, AUD-010, AUD-030, AUD-031 |
| T025 | [x] | PARTIAL | [Dashboard](../../apps/api/app/services/dashboard_service.py#L49) hardcodes empty tasks; [approval](../../apps/api/app/services/recommendation_service.py#L19) mutates before validation; [publish](../../apps/api/app/services/public_alert_service.py#L48) permits pending approval. | AUD-002, AUD-003, AUD-004, AUD-008, AUD-010 |
| T026 | [x] | PARTIAL | Mounted [signals](../../apps/api/app/api/routes/signals.py#L13), [incidents](../../apps/api/app/api/routes/incidents.py#L12), [recommendations](../../apps/api/app/api/routes/recommendations.py#L17), [alerts](../../apps/api/app/api/routes/alerts.py#L36) lack original-route authority/scope gates and full contract parity. | AUD-001, AUD-002, AUD-003, AUD-016 |
| T027 | [x] | PARTIAL | [Dashboard](../../apps/web/src/lib/api/dashboard.ts#L44), [recommendation](../../apps/web/src/lib/api/recommendations.ts#L10), [alert](../../apps/web/src/lib/api/alerts.ts#L3) clients call current endpoints; [signals](../../apps/web/src/lib/api/signals.ts#L14) falsely casts paged object to array; no identity integration. | AUD-001, AUD-008, AUD-010, AUD-016 |
| T028 | [x] | CONFLICT | [Page](../../apps/web/src/app/incidents/%5BincidentId%5D/page.tsx#L38) omits [COP](../../apps/web/src/components/dashboard/shared-operating-picture.tsx#L11), [degraded banner](../../apps/web/src/components/dashboard/degraded-mode-banner.tsx#L5), [source panel](../../apps/web/src/components/dashboard/source-health-panel.tsx#L7) and [composer](../../apps/web/src/components/alerts/public-alert-composer.tsx#L15). | AUD-008, AUD-009, AUD-010 |
| T029 | [x] | CONFLICT | [Workspace contract test](../../tests/contract/test_persona_workspace_contract.py#L9) omits required incident scope and asserts POST status instead of specified PATCH ownership/status; no schema assertion. | AUD-012, AUD-013, AUD-016, AUD-023 |
| T030 | [x] | PARTIAL | [Workspace integration](../../tests/integration/test_persona_workspace_flow.py#L47) covers limited organisation filtering/403, not authenticated callers, shared dependency detail, multiple incidents or notifications. | AUD-001, AUD-012, AUD-013, AUD-023 |
| T031 | [x] | PARTIAL | [Workspace browser test](../../tests/e2e/test_persona_workspace.spec.ts#L3) mocks reads/writes and asserts a local status label; no counterpart update or seven-role workflow proof. | AUD-012, AUD-013, AUD-023 |
| T032 | [x] | PARTIAL | [Persona](../../packages/domain/src/domain/models/persona.py#L6) omits several canonical roles and decision-right fields; [task](../../packages/domain/src/domain/models/coordination_task.py#L6) omits due/blocker fields and differs from required status vocabulary. | AUD-012, AUD-013, AUD-016 |
| T033 | [x] | PARTIAL | [Workspace assembly](../../apps/api/app/services/persona_workspace_service.py#L26) and [task orchestration](../../apps/api/app/services/task_orchestration_service.py#L14) use [new repositories](../../apps/api/app/repositories/coordination_tasks_repository.py#L110), but omit incident scope, required requests/approvals and safe transitions. | AUD-002, AUD-012, AUD-013 |
| T034 | [x] | PARTIAL | [Resource agent](../../apps/agents/resource_allocation/agent.py#L106) builds a pipeline, but [override](../../apps/agents/resource_allocation/agent.py#L382) only acknowledges/audits; [notifier](../../apps/agents/common/dependency_notifier.py#L4) only summarizes and has no callers. | AUD-007, AUD-013, AUD-030 |
| T035 | [x] | CONFLICT | [Persona route](../../apps/api/app/api/routes/personas.py#L7) has no incident query/authorization; [task route](../../apps/api/app/api/routes/tasks.py#L13) uses a different path/method/body from the governing contract. | AUD-001, AUD-012, AUD-013, AUD-016 |
| T036 | [x] | IMPLEMENTED | [Persona client](../../apps/web/src/lib/api/personas.ts#L31) and [task client](../../apps/web/src/lib/api/tasks.ts#L3) implement transport/error handling for the current routes. Identity, incident scope and upstream contract corrections remain separate obligations. | AUD-001, AUD-012, AUD-016 |
| T037 | [x] | PARTIAL | [Workspace page](../../apps/web/src/app/workspaces/%5BpersonaId%5D/page.tsx#L16) mounts [persona workspace](../../apps/web/src/components/workspaces/persona-workspace.tsx#L15); role panels exist but requests/obligations/owner timing and complete operational actions are absent or evaluator-backed. | AUD-008, AUD-010, AUD-012, AUD-013 |
| T038 | [x] | PARTIAL | [Status service](../../apps/api/app/services/task_status_sync.py#L6) only counts states; [status UI](../../apps/web/src/components/workspaces/task-status-panel.tsx#L11) changes one local label and neither refreshes COP nor notifies counterpart organisations. | AUD-004, AUD-013 |
| T039 | [x] | CONFLICT | [Preparedness contract test](../../tests/contract/test_preparedness_contract.py#L5) asserts synchronous `/replay` and snake_case catalogue shapes instead of [feature contract](contracts/openapi.yaml#L221); no model-management or schema coverage. | AUD-014, AUD-015, AUD-016, AUD-023 |
| T040 | [x] | PARTIAL | [Preparedness integration](../../tests/integration/test_preparedness_analysis.py#L5) asserts framework presence and nonempty findings, not model edits, specific gaps, duplication or delay. | AUD-014, AUD-015, AUD-023 |
| T041 | [x] | PARTIAL | [Three-hazard tests](../../tests/simulation/test_preparedness_replays.py#L5) invoke static analysis and assert type/jurisdiction/nonempty text, not scenario execution or gap causality. | AUD-015, AUD-023 |
| T042 | [x] | PARTIAL | [Organisation](../../packages/domain/src/domain/models/organisation.py#L12), [jurisdiction](../../packages/domain/src/domain/models/jurisdiction.py#L6), [framework](../../packages/domain/src/domain/models/operating_framework.py#L9), [assignment](../../packages/domain/src/domain/models/framework_assignment.py#L7), [policy](../../packages/domain/src/domain/models/jurisdiction_policy.py#L4), [run](../../packages/domain/src/domain/models/scenario_run.py#L7) lack required invariants/lifecycle fields. | AUD-014, AUD-015, AUD-016 |
| T043 | [x] | PARTIAL | Fully read [49 organisations](../../packages/domain/src/domain/seed/organisations_australia.json#L1), [27 frameworks](../../packages/domain/src/domain/seed/frameworks_australia.json#L1), [9 jurisdictions](../../packages/domain/src/domain/seed/jurisdictions_australia.json#L1); sector/LGA gaps and approximate geometry prevent national catalogue completeness. | AUD-014, AUD-025 |
| T044 | [x] | PARTIAL | [Organisation intelligence](../../apps/api/app/services/organisation_intelligence_service.py#L14) filters static seed records; [analysis](../../apps/api/app/services/preparedness_analysis_service.py#L41) counts coverage without ownership duplication/delay or full effective-rule handling. | AUD-014, AUD-015 |
| T045 | [x] | PARTIAL | [Evacuation agent](../../apps/agents/evacuation/agent.py#L74) has planning logic but [legacy review](../../apps/agents/evacuation/agent.py#L261) is fixed text and [replan](../../apps/agents/evacuation/agent.py#L127) contains no-op stages; [rehearsal](../../apps/api/app/services/rehearsal_orchestrator.py#L9) calls only static analysis/review. | AUD-007, AUD-015, AUD-030 |
| T046 | [x] | PARTIAL | [Organisations](../../apps/api/app/api/routes/organisations.py#L19), [frameworks](../../apps/api/app/api/routes/frameworks.py#L19), [scenario route](../../apps/api/app/api/routes/scenarios.py#L14) are mounted; catalogue management/filter obligations and queued replay contract are not implemented. | AUD-001, AUD-014, AUD-015, AUD-016 |
| T047 | [x] | IMPLEMENTED | [Organisation](../../apps/web/src/lib/api/organisations.ts#L23), [framework](../../apps/web/src/lib/api/frameworks.ts#L26), [scenario](../../apps/web/src/lib/api/scenarios.ts#L14) clients implement current request/response transport, query selection and failures. Underlying feature behavior remains partial. | AUD-014, AUD-015, AUD-016 |
| T048 | [x] | PARTIAL | [Preparedness page](../../apps/web/src/app/preparedness/page.tsx#L9) mounts [client](../../apps/web/src/components/preparedness/preparedness-client.tsx#L17) and [analyzer](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L38); selectable read-only catalogue exists, not model CRUD or executed coordination analysis. | AUD-014, AUD-015 |
| T049 | [x] | PARTIAL | [Language switcher](../../apps/web/src/components/accessibility/language-switcher.tsx#L19), [connectivity banner](../../apps/web/src/components/offline/connectivity-banner.tsx#L11) unmounted; [alert preview](../../apps/web/src/components/alerts/alert-language-preview.tsx#L10) uses fixed translations; later offline queue is not wired to original writes. | AUD-017, AUD-018, AUD-019 |
| T050 | [x] | PARTIAL | [Alert service](../../apps/api/app/services/public_alert_service.py#L48), [routes](../../apps/api/app/api/routes/alerts.py#L36), [composer](../../apps/web/src/components/alerts/public-alert-composer.tsx#L15) implement only weak state checks/local adapters and fixed review; [new delivery](../../apps/agents/communication/delivery.py#L56) also has false-success/mode gaps. | AUD-003, AUD-010, AUD-011, AUD-031 |
| T051 | [x] | PARTIAL | [Original monitoring](../../infra/bicep/monitoring.bicep#L1) replaced in active deployment by [module](../../infra/modules/monitoring.bicep#L1); [safety](../../infra/policies/safety-guardrails.rego#L11), [isolation](../../infra/policies/tenant-isolation.rego#L11) policies lack decision-path wiring; [resilience](../../apps/api/app/middleware/resilience.py#L60) is header instrumentation, not enforced timeouts/HA/quality rollback. | AUD-002, AUD-004, AUD-009, AUD-020, AUD-021, AUD-026 |
| T052 | [x] | CONFLICT | [Architecture](../../docs/disaster-response-hub/architecture.md#L1) and [runbooks](../../docs/disaster-response-hub/operator-runbooks.md#L1) are authored but overstate auth, isolation, audit, notifications, live UI and portability relative to source/amended scope. | AUD-028, AUD-029 |
| T053 | [x] | PARTIAL | [Baseline](../../docs/disaster-response-hub/evaluation/baseline-metrics.md#L1), [CSV](../../docs/disaster-response-hub/evaluation/kpi-template.csv#L1), [rubric](../../docs/disaster-response-hub/evaluation/ux-rubric.md#L1), [survey](../../docs/disaster-response-hub/evaluation/post-exercise-survey.md#L1) define instruments; no revision-bound agency baseline/cohort proof, and comparator semantics disagree. | AUD-024, AUD-025 |
| T054 | [x] | PARTIAL | [Metric service](../../apps/api/app/services/exercise_metrics_service.py#L34) is uncalled and miscalculates/omits obligations; [metric tests](../../tests/simulation/test_exercise_metrics.py#L6) use constants; [decision-support browser test](../../tests/e2e/test_dashboard_decision_support.spec.ts#L78) expects unmounted controls. | AUD-008, AUD-023, AUD-024, AUD-025, AUD-026 |
| T055 | [x] | UNVERIFIED | [Quickstart results](quickstart.md#L57), [rehearsal assertions](../../tests/simulation/test_quickstart_rehearsals.py#L21), [historical results](../../docs/disaster-response-hub/evaluation/quickstart-rehearsal-results-2026-03-16.md#L7) do not establish current revision execution, real signal-to-agent flow, empirical SCs or approval. | AUD-007, AUD-015, AUD-023, AUD-025, AUD-029, AUD-031 |

## Requirement Coverage

The denominator is 35 normative requirement/outcome IDs: 15 FRs (including FR-014a), 13 NFRs, and 7 SCs.
All 35 are covered below. Acceptance scenarios and every amended assumption, hypothesis, persona and
scope obligation are assessed separately. PARTIAL controls do not imply their numerical outcomes pass.

| Requirement | Status | Evidence / remaining obligation | Follow-up |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | [Catalogue/service](../../apps/api/app/services/organisation_intelligence_service.py#L14) reads [49 organisations](../../packages/domain/src/domain/seed/organisations_australia.json#L1), but no local-government/utility/transport records; no authorized management. | AUD-014 |
| FR-002 | PARTIAL | [27 frameworks](../../packages/domain/src/domain/seed/frameworks_australia.json#L1) and [assignment filtering](../../apps/api/app/services/preparedness_analysis_service.py#L29) represent some rules, but ignore effective-start/overrides and do not govern original approvals. | AUD-001, AUD-014 |
| FR-003 | PARTIAL | [Persona registry](../../apps/api/app/repositories/persona_registry_repository.py#L44) and [workspace lookup](../../apps/api/app/services/persona_workspace_service.py#L26) exist; no authorized persona create/edit or complete decision-right/information-path model. | AUD-001, AUD-012, AUD-014 |
| FR-004 | PARTIAL | [Feed factory](../../apps/ingestion/pipeline_factory.py#L13) covers authoritative/sensor/community adapters; [worker construction](../../apps/ingestion/worker.py#L201) omits persistence/audit; [direct ingestion](../../apps/api/app/api/routes/signals.py#L13) only writes memory. | AUD-005, AUD-006, AUD-007 |
| FR-005 | PARTIAL | [Signal fields](../../packages/domain/src/domain/models/signal.py#L7) hold metadata, but [normalizer](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L26) trusts callers and [display](../../apps/web/src/app/incidents/%5BincidentId%5D/page.tsx#L188) shows counts, not complete influencing provenance/freshness/jurisdiction. | AUD-004, AUD-006, AUD-008 |
| FR-006 | PARTIAL | [Dashboard](../../apps/api/app/services/dashboard_service.py#L49) provides incident/counts, fabricates organisation summaries and has empty tasks; [page](../../apps/web/src/app/incidents/%5BincidentId%5D/page.tsx#L46) fetches once without live propagation/framework boundaries. | AUD-002, AUD-007, AUD-008, AUD-013 |
| FR-007 | PARTIAL | [Workspace](../../apps/api/app/services/persona_workspace_service.py#L26) shows some task/dependency data but not scoped requests, approvals, obligations or complete persona actions; [dependency filtering](../../apps/api/app/repositories/coordination_tasks_repository.py#L143) hides cross-agency chains. | AUD-001, AUD-012, AUD-013 |
| FR-008 | PARTIAL | [Catalogue UI](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L91) shows roles/partners; [workspace model](../../packages/domain/src/domain/models/coordination_task.py#L6) lacks due/blocker/owner handoff detail and runtime bottleneck analysis. | AUD-008, AUD-012, AUD-014, AUD-015 |
| FR-009 | PARTIAL | [Risk recommendation generation](../../apps/agents/risk_assessment/agent.py#L279) exists, but [approval service](../../apps/api/app/services/recommendation_service.py#L19) mishandles escalation and lacks verified authority/version checks; specialist controls can falsely acknowledge changes. | AUD-001, AUD-003, AUD-007, AUD-030 |
| FR-010 | PARTIAL | [Language metadata](../../apps/web/src/lib/i18n/language-packs.ts#L40), [PIO composer](../../apps/web/src/app/workspaces/%5BpersonaId%5D/_panels/pio-aws-composer.tsx#L49) and [delivery](../../apps/agents/communication/delivery.py#L56) exist but do not establish approved, accessible, community-tailored delivery. | AUD-003, AUD-010, AUD-011, AUD-017, AUD-019, AUD-031 |
| FR-011 | PARTIAL | [Design tokens](../../packages/ui/src/styles/tokens.css#L1) and [shell](../../packages/ui/src/components/layout/app-shell.tsx#L17) establish a visual system; required live decision controls are absent and [UX rubric](../../docs/disaster-response-hub/evaluation/ux-rubric.md#L1) has no current cohort results. | AUD-008, AUD-019, AUD-025 |
| FR-012 | PARTIAL | [Request audit appender](../../apps/api/app/middleware/audit_appender.py#L146) writes best-effort summaries; [original timeline](../../apps/api/app/services/state_store.py#L25) is mutable memory, with incomplete domain events/mode/version lineage. | AUD-004, AUD-021, AUD-026, AUD-031 |
| FR-013 | PARTIAL | [Preparedness analyzer](../../apps/api/app/services/preparedness_analysis_service.py#L41) detects a few static coverage gaps; [rehearsal](../../apps/api/app/services/rehearsal_orchestrator.py#L9) does not execute event-derived duplication/delay analysis or expose authorized model editing. | AUD-014, AUD-015, AUD-024 |
| FR-014 | PARTIAL | [Ingestion circuit breaker](../../apps/api/app/services/ingestion/pipeline_base.py#L28) is implemented, but original [degraded helper](../../apps/api/app/services/degraded_mode_service.py#L10) is disconnected from operational decisions and mounted incident UI. | AUD-005, AUD-009, AUD-018 |
| FR-014a | PARTIAL | [Guardrail](../../apps/api/app/services/recommendation_guardrails.py#L4) only adds manual-review/status fields; [banner](../../apps/web/src/components/dashboard/degraded-mode-banner.tsx#L5) uses contradicted counts and is unmounted, with no actual impacted-source ranking/suppression. | AUD-009 |
| NFR-001 | PARTIAL | [Axe builder](../../tests/e2e/web-coverage/_support/a11y/axeBuilder.ts#L7) uses WCAG 2.2 tags but disables contrast/regions; [test scope](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts#L16) is three landings, not every P1 journey. Zero A/AA violations and >=95% keyboard completion UNVERIFIED. | AUD-019, AUD-025 |
| NFR-002 | PARTIAL | [Original payload storage](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L26) lacks lifecycle classification; [SAR metadata](../../apps/api/app/api/routes/audit_compliance.py#L80) is not erasure or retention enforcement. 100% classification, 30-day operational retention/erasure and seven-year evidence policy not established. | AUD-021, AUD-026 |
| NFR-003 | PARTIAL | [JWT middleware](../../apps/api/app/middleware/entra_auth.py#L37) excludes original routes; [threat-model document](../../docs/aidr/threat-model.md#L1) is authored but quarterly acceptance, 100% phishing-resistant MFA, <=1 h access/<=24 h refresh, bound sessions, HSM and zero-secret posture UNVERIFIED. | AUD-001, AUD-022, AUD-029 |
| NFR-004 | PARTIAL | [Single Cosmos location](../../infra/main.bicep#L589), [Basic web plan](../../infra/main.bicep#L1258), [manual eval trigger](../../.github/workflows/eval-pr-gate.yml#L3), and health-only CD rollback do not provide the complete quality-bound regional HA design. Availability/RTO/RPO/rollback targets UNVERIFIED. | AUD-002, AUD-009, AUD-020, AUD-026 |
| NFR-005 | UNVERIFIED | [Health-only in-process benchmarks](../../tests/benchmark/test_api_performance.py#L1) do not measure p95 refresh 3 s/10 s, ingest-to-visible 60 s or action 2 s at the connectivity floor; [incident page](../../apps/web/src/app/incidents/%5BincidentId%5D/page.tsx#L46) lacks live refresh. | AUD-008, AUD-018, AUD-026 |
| NFR-006 | CONFLICT | [CAP renderer](../../apps/api/app/api/routes/warning_chain.py#L104) interpolates XML, emits Draft and lacks schema gate; [EDXL serializer](../../apps/agents/communication/edxl_serialiser.py#L13) targets 1.0, not 2.0. [Tests](../../tests/contract/test_warning_contract.py#L90) parse examples, not 100% XSD/resource/Sendai conformance. | AUD-011, AUD-016 |
| NFR-007 | PARTIAL | [Source trust tier model](../../packages/domain/src/domain/models/data_source.py#L7) exists, but [original normalizer](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L26) does not enforce authoritative/verified-community/unverified distinction and [COP](../../apps/web/src/components/dashboard/shared-operating-picture.tsx#L32) lacks every required metadata field. | AUD-006, AUD-008, AUD-010 |
| NFR-008 | PARTIAL | [Append repository](../../apps/api/app/repositories/audit_repository.py#L84) exists, but [appender](../../apps/api/app/middleware/audit_appender.py#L146) suppresses failures and loses decision semantics. One-second logging, append-only full chain and five-minute replay UNVERIFIED. | AUD-004, AUD-026 |
| NFR-009 | UNVERIFIED | [Primary-region allowlist](../../infra/main.bicep#L79) and [residency helper](../../apps/api/app/core/residency.py#L15) are authored; actual primary/replica/backup/telemetry inventory, 100% policy compliance and approved exceptions cannot be established without authorized evidence. | AUD-020, AUD-021, AUD-026 |
| NFR-010 | PARTIAL | [Budget tracker](../../apps/agents/common/llm_budget_tracker.py#L137) and [cost template](../../docs/operator-runbooks/cost-reporting.md#L1) do not establish per-rehearsal/per-monitored-day totals or approved <=20% variance; failure handling can reset spend. | AUD-027 |
| NFR-011 | PARTIAL | [Runbooks](../../docs/disaster-response-hub/operator-runbooks.md#L1) exist; [release pipeline](../../.github/workflows/cd.yml#L1) has no inspected P1 training-pack/update gate. 100% refreshed packs/operator notes within five business days UNVERIFIED. | AUD-028 |
| NFR-012 | PARTIAL | [Audit container](../../infra/main.bicep#L525) is not the separately protected evidence archive; [audit immutability tests](../../tests/integration/test_audit_immutability.py#L19) concern API refusal, not storage WORM. Seven-year tamper evidence and annual <=1 h restore UNVERIFIED. | AUD-004, AUD-021, AUD-026 |
| NFR-013 | PARTIAL | [Language switcher](../../apps/web/src/components/accessibility/language-switcher.tsx#L25) only changes attributes; [registry](../../apps/web/src/lib/i18n/language-packs.ts#L40) supplies metadata; original operator pages remain hardcoded English. Two-language/locale/RTL/native-review release compliance UNVERIFIED. | AUD-017, AUD-019 |
| SC-001 | UNVERIFIED | [Normative target](spec.md#L125) is <5 min with >=3 tier-1 AU agencies; [catalogue source](../../apps/api/app/services/organisation_intelligence_service.py#L14) and [survey template](../../docs/disaster-response-hub/evaluation/post-exercise-survey.md#L9) do not establish measured identification/cohort results. | AUD-014, AUD-025 |
| SC-002 | UNVERIFIED | [Target](spec.md#L126) is <10 min activation-to-first coordinated plan; [KPI sample](../../docs/disaster-response-hub/evaluation/kpi-template.csv#L3) and [fixture test](../../tests/simulation/test_exercise_metrics.py#L25) are not current observed activation-to-plan evidence. | AUD-007, AUD-008, AUD-024, AUD-025 |
| SC-003 | UNVERIFIED | [Target](spec.md#L127) is >=90% unaided first-attempt completion for the seven v1 roles; [workspace test](../../tests/e2e/test_persona_workspace.spec.ts#L3) mocks one operator and cannot prove this cohort outcome. | AUD-012, AUD-013, AUD-019, AUD-025, AUD-028 |
| SC-004 | UNVERIFIED | [Comparator](../../apps/api/app/services/exercise_metrics_service.py#L59) computes a response-time percentage, but [HYP evidence](evidence/HYP-001.md#L34) is a placeholder and no matched observed baseline/hub pair proves >=50% improvement. | AUD-024, AUD-025 |
| SC-005 | UNVERIFIED | [Comparator](../../apps/api/app/services/exercise_metrics_service.py#L77) supports hours earlier, but [fixture](../../tests/simulation/test_exercise_metrics.py#L56) shows only 3.5 h and [HYP evidence](evidence/HYP-002.md#L34) lacks a signed real pair. >=24 h under matching authority/risk rules unproven. | AUD-024, AUD-025 |
| SC-006 | UNVERIFIED | [Comparator](../../apps/api/app/services/exercise_metrics_service.py#L93) omits utilization/unfilled requests and [HYP evidence](evidence/HYP-003.md#L34) is empty; >=30% composite improvement within the AU cohort is unproven. | AUD-024, AUD-025 |
| SC-007 | UNVERIFIED | [Comparator](../../apps/api/app/services/exercise_metrics_service.py#L112) uses means instead of >=85% favourable participant scores; [rubric](../../docs/disaster-response-hub/evaluation/ux-rubric.md#L17) and [survey](../../docs/disaster-response-hub/evaluation/post-exercise-survey.md#L83) are instruments, not representative observed results. | AUD-017, AUD-019, AUD-024, AUD-025 |

## Acceptance Scenario and Edge Coverage

| Scenario | Status | Evidence / remaining obligation | Follow-up |
| --- | --- | --- | --- |
| US1-1 | PARTIAL | [Scenario](spec.md#L20): [dashboard](../../apps/api/app/services/dashboard_service.py#L49) omits real frameworks/boundaries/tasks/prioritization; [browser test](../../tests/e2e/test_incident_commander_dashboard.spec.ts#L3) supplies one mocked incident. | AUD-002, AUD-008, AUD-014 |
| US1-2 | PARTIAL | [Scenario](spec.md#L21): [ingestion](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L26) stores a signal but does not orchestrate or push its impact; [page](../../apps/web/src/app/incidents/%5BincidentId%5D/page.tsx#L46) fetches once; [integration](../../tests/integration/test_live_incident_coordination.py#L8) checks only helper scoring. | AUD-004, AUD-005, AUD-006, AUD-007, AUD-008, AUD-009 |
| US1-3 | PARTIAL | [Scenario](spec.md#L22): [approval service](../../apps/api/app/services/recommendation_service.py#L19) mishandles escalation and actor authority; UI does not show recommendation dependencies/trade-offs; [test](../../tests/contract/test_live_incident_contract.py#L79) exercises approval only. | AUD-001, AUD-003, AUD-004, AUD-008, AUD-030 |
| US1-4 | PARTIAL | [Scenario](spec.md#L23): [composer](../../apps/web/src/components/alerts/public-alert-composer.tsx#L21) previews fixed content, not actual audience/languages/channels; [publication](../../apps/api/app/services/public_alert_service.py#L48) allows pending approval; [mock test](../../tests/e2e/test_incident_commander_dashboard.spec.ts#L54) cannot prove delivery. | AUD-003, AUD-010, AUD-011, AUD-017, AUD-019, AUD-031 |
| US2-1 | PARTIAL | [Scenario](spec.md#L37): [workspace service](../../apps/api/app/services/persona_workspace_service.py#L26) resolves arbitrary persona IDs without verified principal/incident scope and lacks requests/obligations; [test](../../tests/contract/test_persona_workspace_contract.py#L9) lacks authentication. | AUD-001, AUD-002, AUD-012 |
| US2-2 | PARTIAL | [Scenario](spec.md#L38): [repository](../../apps/api/app/repositories/coordination_tasks_repository.py#L143) filters foreign dependencies and task model omits ETA/blocker; [integration](../../tests/integration/test_persona_workspace_flow.py#L47) does not assert authorized inter-agency chain visibility. | AUD-012, AUD-013 |
| US2-3 | PARTIAL | [Scenario](spec.md#L39): [update](../../apps/api/app/services/task_orchestration_service.py#L41) has no notification/event; [UI](../../apps/web/src/components/workspaces/task-status-panel.tsx#L16) changes local text only; [browser test](../../tests/e2e/test_persona_workspace.spec.ts#L33) validates that text, not counterpart state. | AUD-004, AUD-013, AUD-018 |
| US3-1 | MISSING | [Scenario](spec.md#L53): authorized add/edit is absent from the inspected original [catalogue routes](../../apps/api/app/api/routes/organisations.py#L19), [framework route](../../apps/api/app/api/routes/frameworks.py#L19), registry and [read-only analyzer](../../apps/web/src/components/preparedness/operating-model-analyzer.tsx#L91); scoped CRUD replacement search found only unrelated M&E framework creation. | AUD-001, AUD-014, AUD-016 |
| US3-2 | PARTIAL | [Scenario](spec.md#L54): [framework filtering](../../apps/api/app/services/preparedness_analysis_service.py#L29) supplies differing records but not effective overrides/operational consequence comparison; [test](../../tests/integration/test_preparedness_analysis.py#L5) asserts only a framework and nonempty finding. | AUD-014, AUD-015 |
| US3-3 | PARTIAL | [Scenario](spec.md#L55): [rehearsal](../../apps/api/app/services/rehearsal_orchestrator.py#L9) returns static gaps/fixed advice; [simulation tests](../../tests/simulation/test_preparedness_replays.py#L5) do not assert duplicated responsibilities or decision delays. | AUD-004, AUD-015, AUD-024, AUD-025 |
| EDGE-01 conflicting signals | PARTIAL | [Edge](spec.md#L59): [risk generation](../../apps/agents/risk_assessment/agent.py#L104) can lower confidence/add contradiction rationale, but original ingestion/dashboard/approval do not connect it; [degraded test](../../tests/integration/test_live_incident_coordination.py#L17) is helper-only. | AUD-006, AUD-007, AUD-009 |
| EDGE-02 cross-jurisdiction rules | PARTIAL | [Edge](spec.md#L60): [framework data](../../packages/domain/src/domain/seed/frameworks_australia.json#L1) has jurisdiction variants, but [approval route](../../apps/api/app/api/routes/recommendations.py#L17) and [partition tests](../../tests/integration/test_tenant_isolation.py#L10) do not prove their enforcement. | AUD-001, AUD-002, AUD-012, AUD-014 |
| EDGE-03 missing persona mappings | PARTIAL | [Edge](spec.md#L61): [workspace registry fallback](../../apps/api/app/services/persona_workspace_service.py#L26) returns 404 for unknown persona, but [approval](../../apps/api/app/api/routes/recommendations.py#L10) accepts an arbitrary persona ID; inconsistent fail-closed behavior. | AUD-001, AUD-012, AUD-014 |
| EDGE-04 degraded connectivity | PARTIAL | [Edge](spec.md#L62): [offline store](../../apps/web/src/lib/offline/queue-store.ts#L216) removes before acknowledgement; [worker](../../apps/web/public/offline-sw.js#L8) is no-op; [offline boundary test](../../tests/integration/test_field_coordinator_offline_boundaries.py#L28) checks helpers, not mounted field workflow. | AUD-018, AUD-026 |
| EDGE-05 misinformation/anomalous burst | PARTIAL | [Edge](spec.md#L63): [monitoring classification](../../apps/agents/monitoring/agent.py#L135) exists but original [ingress](../../apps/api/app/api/routes/signals.py#L13) bypasses it; quality, false-amplification detection, burst behavior and human actions on false content are not evidenced. | AUD-006, AUD-007, AUD-009, AUD-025, AUD-026 |
| EDGE-06 language/access/channel needs | PARTIAL | [Edge](spec.md#L64): [language registry](../../apps/web/src/lib/i18n/language-packs.ts#L40) and [delivery](../../apps/agents/communication/delivery.py#L56) provide foundations; fixed preview, skipped transport, zone-only dedup and incomplete AA coverage undermine tailored delivery. | AUD-010, AUD-017, AUD-019 |

## Review and Evidence Claims

The plan's pre-research/post-design PASS declarations are authored design claims, not verified reviews.
All seven SC outcomes, TDD chronology, external approvals, cloud residency, runtime availability,
performance, restore drills, and human UX/accessibility evaluations remain UNVERIFIED without
independent execution records. Every local supporting artifact and amendment was read. The following
assessments concern current implementation/readiness, not a retroactive denial that an older author
performed a design review. No original sign-off is edited.

| Local claim | Recorded state | Current evidence assessment | Follow-up |
| --- | --- | --- | --- |
| Plan pre-research: life safety | PASS | CONFLICT with [pending-approval publication](../../apps/api/app/services/public_alert_service.py#L48); actual human/owner approval unverified. | AUD-001, AUD-003, AUD-025 |
| Plan pre-research: clear multi-agent roles | PASS | PARTIAL: [specialists/MAF builder](../../apps/agents/maf_runtime/workflow/builder.py#L61) exist, not connected to original live ingress. | AUD-007 |
| Plan pre-research: trust/provenance/freshness | PASS | PARTIAL: [ingestion](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L26) accepts asserted trust without authoritative-first enforcement. | AUD-006, AUD-009 |
| Plan pre-research: privacy/security/isolation | PASS | CONFLICT with [limited auth](../../apps/api/app/middleware/entra_auth.py#L37) and unscoped original state; tenant/privacy approvals unverified. | AUD-001, AUD-002, AUD-021 |
| Plan pre-research: multilingual/accessibility | PASS | PARTIAL: [fixed preview](../../apps/web/src/components/alerts/alert-language-preview.tsx#L10) and unbound delivery/review; human accessibility evaluation unverified. | AUD-010, AUD-017, AUD-019 |
| Plan pre-research: Azure/AU cloud | PASS | UNVERIFIED deployment/residency; [active location parameter](../../infra/main.bicep#L79) supports AU intent but not actual all-copy compliance. | AUD-020, AUD-026 |
| Plan pre-research: TDD/readiness | PASS | UNVERIFIED historical test chronology and rehearsals; [CI](../../.github/workflows/ci.yml#L138) does not enforce the complete original acceptance slice. | AUD-023, AUD-025 |
| Plan post-design: safe domain state transitions | PASS | CONFLICT with [actual recommendation/alert transitions](../../apps/api/app/services/recommendation_service.py#L19), which do not enforce the declared state machine. | AUD-003, AUD-016 |
| Plan post-design: explicit typed handoffs | PASS | PARTIAL: [handoff replacement](../../apps/agents/common/handoffs.py#L1) is documented; active original ingress does not produce a complete chain. | AUD-007 |
| Plan post-design: trust/reproducibility fields | PASS | PARTIAL: [models](../../packages/domain/src/domain/models/signal.py#L7) have fields but not complete semantic validation or all-surface provenance. | AUD-006, AUD-008, AUD-016 |
| Plan post-design: policy/tenancy enforcement | PASS | CONFLICT: [key builders](../../apps/api/app/services/tenant_partitioning.py#L7) are not enforcement on original reads/writes. | AUD-001, AUD-002, AUD-014 |
| Plan post-design: accessible approved alert flow | PASS | CONFLICT/PARTIAL: [composer](../../apps/web/src/components/alerts/public-alert-composer.tsx#L15) is unmounted and cannot prove reviewed accessible delivery. | AUD-008, AUD-010, AUD-019 |
| Plan post-design: Azure component structure | PASS | IMPLEMENTED as authored structure; deployment/region/HA outcomes UNVERIFIED. [Descriptor](../../azure.yaml#L8) names real services and IaC. | AUD-020, AUD-026 |
| Plan post-design: replay/degraded operational readiness | PASS | PARTIAL: [replay tests](../../tests/simulation/test_preparedness_replays.py#L5) assert static output, [degraded test](../../tests/integration/test_reduced_function_mode.py#L5) checks helpers. | AUD-009, AUD-015, AUD-025 |
| Plan complexity: no constitution violations | No exceptions identified | Not a present implementation certification; current auth, human approval, audit and egress risks require resolution. | AUD-001, AUD-003, AUD-004, AUD-031 |
| Quickstart Python suite | 14 tests confirmed | UNVERIFIED at this revision; source assertions inspected, no test execution or linked revision-bound raw report. | AUD-023, AUD-025 |
| Quickstart Playwright suite | 3 tests confirmed | CONFLICT in current source/expected UI for two incident tests; actual result UNVERIFIED because tests were not run. | AUD-008, AUD-023, AUD-025 |
| Quickstart exercise metrics | SC-004/006/007 validated | UNVERIFIED empirical outcomes; [comparisons](../../apps/api/app/services/exercise_metrics_service.py#L93) do not implement all normative scoring rules. | AUD-024, AUD-025 |
| Quickstart complete multi-jurisdiction flow | Validated | [Test](../../tests/simulation/test_quickstart_rehearsals.py#L21) uses one NSW signal and manual downstream insertion, not the described three-source multi-jurisdiction workflow. | AUD-005, AUD-007, AUD-025 |
| Dated 2026-03-16 rehearsal record | 31 Python/6 browser passes; live LLM SKIP | Authored historical statement for feature 003, not current original-spec acceptance; skipped live environment explicitly preserved. | AUD-025, AUD-029 |
| Architecture/runbooks safety and full audit | Implemented wording | CONFLICT with actual OPA wiring, empty COP tasks, request-audit omissions, fake channel delivery and disconnected notifier. | AUD-003, AUD-004, AUD-008, AUD-009, AUD-010, AUD-013, AUD-029 |
| Architecture/Asia guide portability | No code changes needed | SUPERSEDED as a guarantee by [HYP-006/OD-001/SCP-080](spec.md#L583); stale wording remains and must be reconciled, not used to widen v1. | AUD-029 |
| Demo walkthrough/screens | Demonstrated/placeholder captions | Authored scripts/placeholders only; [walkthrough](../../docs/disaster-response-hub/demo/walkthrough.md#L1) does not supply current captured approval/UX evidence. | AUD-025, AUD-029 |
| HYP/ASM/persona validation | Proposed/role-labelled | UNVERIFIED named independent/SME/privacy signatures; no promotion inferred from `validated_by` labels. | AUD-025, AUD-029 |
| Local checklist/sign-off files | None in original feature inventory | No missing-file completion claim invented: plan gates, quickstart and six HYP records are the actual local review evidence assessed. Generic repository checklist is a template, not a signed review. | AUD-025, AUD-029 |

### Status Authority and Open Deltas

| Obligation | Assessment | Follow-up |
| --- | --- | --- |
| Drafting authority | [CODEOWNERS](../../.github/CODEOWNERS#L16) declares a team; current membership/actual reviewer authorization UNVERIFIED. | AUD-029 |
| Dual-control/three-way privacy signatures | [Spec rule](spec.md#L569) requires independent SME and privacy signatures; role names are not concrete signatures. | AUD-021, AUD-025, AUD-029 |
| Invalidated/Withdrawn dependencies | [Rule](spec.md#L570) must reopen affected decisions/SCs and Open Delta; none is changed by this audit and no hypothetical failure is declared a historical invalidation. | AUD-025, AUD-029 |
| Hypothesis invalidation | [Rule](spec.md#L571) requires linked SC/decision review in the same PR; later validation must test this workflow, not auto-close hypotheses on a score alone. | AUD-024, AUD-025, AUD-029 |
| Gap-register synchronization/dispute resolution | [Rules](spec.md#L572) require corresponding register/change records and maintainer resolution; actual enforcement/signatures UNVERIFIED. Shared register/index untouched. | AUD-029 |
| OD-001 | [Open plan blocker](spec.md#L583) remains Open; old plan PASS is not evidence it cleared. | AUD-025, AUD-029 |
| OD-002 | [Team fallback](spec.md#L584) remains Open; interim individual rule is commented out in CODEOWNERS. Team existence not queried. | AUD-029 |
| OD-003 | [Named individuals](spec.md#L585) remain deferred to PR review; no actual identities/signatures supplied by local role labels. | AUD-025, AUD-029 |

### Intentional Replacements and Non-Findings

| Historical instruction/artifact | Explicit replacement evidence | Audit treatment |
| --- | --- | --- |
| Playwright `.ts` config | [Current `.cts`](../../apps/web/playwright.config.cts#L1) contains the actual project/server configuration. | Not missing; T004 is partial for concrete gate/import issues, not filename change. |
| Legacy point-to-point handoffs | [Deprecation notice](../../apps/agents/common/handoffs.py#L1), [MAF builder](../../apps/agents/maf_runtime/workflow/builder.py#L1), [moved cutover playbook](../../docs/corpus/aidr/runbooks/maf-cutover-playbook.md#L1). | Legacy handoff instruction is SUPERSEDED; live integration still needs AUD-007. |
| Original monitoring file as active entry point | [Deployment descriptor](../../azure.yaml#L8) -> [root module reference](../../infra/main.bicep#L165) -> [current module](../../infra/modules/monitoring.bicep#L1). | Followed active replacement; did not infer absent monitoring from obsolete path. |
| Old progressive-delivery workflow footprint | [Explicit retirement comment](../../.github/CODEOWNERS#L28) names the single current CD entry. | SUPERSEDED architecture; assess current quality rollback instead of recreating retired pipelines. |
| Azure OpenAI compatibility environment path | [Foundry cutover declaration](../../infra/main.bicep#L937) removes old canonical endpoint convention. | Preserve current Foundry direction; update stale quickstart/env mappings under AUD-022/029. |
| Absolute no-non-AU-inference interpretation | [Constitution amendment](../../.specify/memory/constitution.md#L242) permits only named model-hosting carve-outs with minimization and no regulated persistence outside AU. | Apply bounded exception; not permission to move storage/audit/telemetry out of AU. Actual approvals UNVERIFIED. |
| Full Recovery/country/citizen portal scope | [DEF register](spec.md#L461), [SCP-080/081](spec.md#L609). | Explicitly deferred, not genuine missing-v1 behavior; v1 catalogue, alerts and LGA referral obligations remain. |

## Verification Handoff

Remediation order: resolve authority/contracts/mode and source-of-truth decisions first (AUD-001,
AUD-002, AUD-003, AUD-004, AUD-016, AUD-029, AUD-031); then integrate ingestion/orchestration/operator
flows and controls; finally collect independent test, cohort, security, cost and operational evidence.
Mutual dependency references identify shared interface decisions and later integration gates, not a
requirement to complete circular sign-offs before starting a narrowly authorized fix.

Developer work and tester/evidence work are separate in every AUD task. No original task checkbox is
retrospectively reopened, no earlier result is relabelled as current, and no named human approval is
invented. Before future commands, obtain separate authorization for remediation/testing and ensure
all public transports are replaced by spies or approved sandbox endpoints. Do not run broad `pytest
tests/` with inherited cloud credentials merely because the old quickstart recommends it.

Language-level support only: [Pydantic assignment validation documentation](https://pydantic.dev/docs/validation/latest/api/pydantic/config/#pydantic.config.ConfigDict.validate_assignment)
confirms default assignment revalidation is off. This public documentation check did not install a
package, import application code or establish the user's runtime package state.

## Document Validation

Document-only checks compare the original task IDs/checkbox states with the 55 explicit rows, the
35 normative FR/NFR/SC IDs with requirement rows, and the amended/scenario identifiers with their
separate tables. They verify that all 31 AUD IDs have unchecked remediation items, developer/tester
instructions, dependencies, future validation and acceptance criteria; all follow-up IDs resolve;
all local evidence targets exist and line anchors are in range; no audit-ledger placeholder remains;
the file has a final newline; and editor diagnostics are clear. These checks do not execute any product
test, build, deployment, source formatter, cloud query, remediation or approval workflow.

Coverage means reviewed and classified, not accepted or passed: **55/55 tasks, 35/35 normative
requirements/outcomes, 10/10 acceptance scenarios, 6/6 edge cases, 10/10 assumptions, 6/6 hypotheses,
18/18 personas, 11/11 hazards, 16/16 deferrals and both SCP amendments**. The report contains **31
unchecked remediation tasks**. The empirical/runtime/approval limitations stated above remain in force.
