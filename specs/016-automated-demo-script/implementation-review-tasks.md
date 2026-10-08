# Spec 016 Implementation Review and Remediation Tasks

## Scope and Verdict

- Review date: **2026-09-11**.
- Reviewed revision: **5b44c249f00e0e4a13ea2579c8c33d06e2471d7a**. Read-only Git metadata confirmed HEAD and no tracked differences in the inspected implementation scope before this report was written.
- Authority: the complete [Review Contract](../001-spec-implementation-audit/README.md#L14).
- Overall implementation status: **PARTIAL**, with material **CONFLICT** and **UNVERIFIED** obligations. The current summary is not reliable evidence of a working end-to-end disaster-response pipeline.
- Original task coverage: **39/39**, preserving **39 `[X]`** states. Those states are author claims, not this review's acceptance decisions.
- Requirement coverage: **17 FRs and 8 SCs**. The specification has **no numbered NFRs**; the plan's two named NFR obligations are assessed separately below, as are the comprehensive checklist's nonfunctional concerns.
- Scenario coverage: **15 acceptance scenarios and 5 edge cases**. Also covered: five clarification decisions, three personas, one hypothesis, four scope amendments, the canonical meta-spec declaration, six assumptions, eight research decisions, eight implementation models, 14 plan-gate claims, 16 quality-checklist items, and 109 comprehensive-checklist items.
- Remediation: **21 unchecked tasks**, AUD-016-001 through AUD-016-021. Their instructions are for a separately authorized implementation effort.
- Isolation: no other implementation-audit reports were inputs; no delegation occurred. No branch, commit, index, application, original spec/task/checklist, or existing evidence changes were made.
- Execution boundary: **no tests, Python imports, demo runs, builds, deployments, cloud-resource queries, benchmarks, or human sign-offs** were performed. Source describes reachable behavior; runtime and environmental outcomes remain unverified.

### Evidence Statuses

| Status | Meaning in this report |
| --- | --- |
| IMPLEMENTED | The scoped behavior or authored artifact is supported by inspected source; not a runtime pass. |
| PARTIAL | Some behavior exists, but a stated obligation is absent or contradicted. |
| MISSING | The named artifact or behavior was not found in the explicitly stated search scope. |
| CONFLICT | Requirements, task instructions, or implementation disagree and need an explicit resolution. |
| UNVERIFIED | Source cannot establish execution, measurement, approval, or deployed state. |
| SUPERSEDED | Explicit repository evidence documents replacement; not inferred from age or a renamed file. |

### Inputs and Search Boundaries

Read in full: [spec.md](spec.md), including its clarification and later persona/hypothesis/scope additions; [tasks.md](tasks.md); [plan.md](plan.md); [research.md](research.md); [data-model.md](data-model.md); [quickstart.md](quickstart.md); [contracts/cli-interface.md](contracts/cli-interface.md); [contracts/output-schema.md](contracts/output-schema.md); [checklists/requirements.md](checklists/requirements.md); and [checklists/comprehensive.md](checklists/comprehensive.md). The local packet contained exactly those ten files and no separate review or execution-evidence record before this report.

Associated references inspected include the full [manual walkthrough](../../docs/disaster-response-hub/demo/walkthrough.md), [constitution](../../.specify/memory/constitution.md), [persona-profile contract](../027-spec-hardening/contracts/persona-profile.md), [hypothesis-evidence contract](../028-capstone-alignment/contracts/evidence-stub.contract.md), [meta-spec contract](../028-capstone-alignment/contracts/meta-spec-flag.contract.md), and feature-028 [baseline](../028-capstone-alignment/evidence/rubric-baseline.md), [postfeature snapshot](../028-capstone-alignment/evidence/rubric-postfeature.md), and [decision record](../028-capstone-alignment/evidence/decision-record.md). The [feature-value-ledger row](../shared/feature-value-ledger.md#L30) was checked for the scope of its exclusion claim.

Implementation tracing started at the complete [scripts/demo.py](../../scripts/demo.py#L1) and complete [demo test module](../../tests/simulation/test_demo_script.py#L1), then followed the six app factories, called handlers, platform ingestion/state/middleware/repository paths, and nearby processing pipelines and test assertions. The [review instructions](../../.github/instructions/code-review.instructions.md) and Python fact-grounded-coding skill were applied within the static-only boundary. No interpreter, installed-package, Pylance-type, or runtime-success claim is made.

Negative and replacement searches used these bounded scopes:

| Search | Scope and result |
| --- | --- |
| Demo implementation relocation | Searched demo-related filenames and references in scripts, tests, documentation, workflows, and the local packet. The existing entrypoint is [scripts/demo.py:1103](../../scripts/demo.py#L1103). Existing risk, evacuation, resource, and communication pipelines are cited below; they are not globally missing. |
| Newer orchestration | [Legacy handoffs:1](../../apps/agents/common/handoffs.py#L1) explicitly identifies [the MAF workflow builder:1](../../apps/agents/maf_runtime/workflow/builder.py#L1) as its replacement while retaining fallback support. That builder has a separate CLI and awaits approval. The demo's [factory wiring:295](../../scripts/demo.py#L295) and [phase dispatch:1130](../../scripts/demo.py#L1130) do not call it. The legacy primitive's replacement is SUPERSEDED evidence, not retirement of Spec 016 or proof of demo completion. |
| CI gate | Searched all workflow text for the demo entrypoint/test name and simulation/pytest invocations. [CI:131](../../.github/workflows/ci.yml#L131) selects contract/integration tests, [CI:148](../../.github/workflows/ci.yml#L148) benchmarks, and [Windows CI:196](../../.github/workflows/ci.yml#L196) contract/integration tests. No selection of this demo module or command was found. Other simulation/load workflows are not this seven-phase demo. |
| Documentation entry | Searched the root README and documentation tree for the automated command, test name, feature slug, and automated-demo wording. [README:281](../../README.md#L281) links the [manual walkthrough:1](../../docs/disaster-response-hub/demo/walkthrough.md#L1), not the automated command or Spec 016 quickstart. No replacement onboarding reference satisfying T039 was found. |
| Hypothesis and acceptance evidence | Enumerated the complete local packet; searched hypothesis-014 filenames across the workspace, feature-028 evidence, shared traceability, and documentation attestations for HYP-014 or this demo. The doubled-prefix stub named at [spec:161](spec.md#L161) was not found, nor a relocated matching stub. The three located feature-028 records are portfolio documents, not a Spec 016 experiment or demo run receipt. |
| Seed evidence | All six named language-template files exist. Inspected the [English template definitions:23](../../data/alert-templates/en-AU.json#L23) and structural metadata/records in [population:1](../../data/population/sample-population.json#L1), [roads:1](../../data/road-networks/far-north-qld-sample.json#L1), and [inventory:1](../../data/resource-inventories/sample-inventory.json#L1). This is not a full semantic-data audit, multilingual linguistic approval, or privacy certification. |

## Prioritized Findings

P1 findings block relying on this demo as a correctness/safety smoke gate. P2 findings concern material completeness, reproducibility, observability, and evidence. Shared-handler findings below are limited to their use by this demo, not a new audit of the owning agent specifications.

| Priority / status | Finding, evidence, and impact | Follow-up |
| --- | --- | --- |
| P1 / PARTIAL | Offline operation is not enforced before imports. [Factory imports:304](../../scripts/demo.py#L304) reach [telemetry setup:12](../../apps/api/app/main.py#L12) and [router imports:38](../../apps/api/app/api/router.py#L38), then [module-level repositories:28](../../apps/api/app/api/routes/simulations.py#L28). [SignalRepository:26](../../apps/api/app/repositories/signal_repository.py#L26) selects an environment-configured Cosmos client. In-process HTTP does not isolate these external dependencies. | [AUD-016-001](#aud-016-001) |
| P1 / PARTIAL | Setup clears unrelated process-global platform data via [demo:345](../../scripts/demo.py#L345) and [reset_state:33](../../apps/api/app/services/state_store.py#L33). There is no ownership-scoped cleanup, client context management, or finalizer in [run_pipeline:1103](../../scripts/demo.py#L1103). Embedded/repeated invocations can destroy prior state and retain demo state. | [AUD-016-002](#aud-016-002) |
| P1 / CONFLICT | [Setup:356](../../scripts/demo.py#L356) accepts every HTTP-200 health status, including unhealthy/unknown, and increments the healthy count for them. It omits the platform health check. This contradicts [T009](tasks.md#L60), [FR-002](spec.md#L100), and the [research health policy](research.md#L294). | [AUD-016-003](#aud-016-003) |
| P1 / PARTIAL | [Monitoring:480](../../scripts/demo.py#L480) ignores association failures, coerces zero associations to one, and ignores failed dashboards. [Evacuation:676](../../scripts/demo.py#L676) treats 503 as a triggered plan and ignores override responses. [Communication:939](../../scripts/demo.py#L939) converts errors/discards into invented success. The orchestrator only sees these passing results. | [AUD-016-004](#aud-016-004) |
| P1 / CONFLICT | [Risk phase:548](../../scripts/demo.py#L548) authors a fixed recommendation instead of running assessment; its approval endpoint has [no recommendation store:604](../../apps/agents/risk_assessment/agent.py#L604), so the [conditional update:749](../../apps/agents/risk_assessment/agent.py#L749) is bypassed. T011 intentionally specifies seeding, while the spec promises a propagated analysis result. | [AUD-016-005](#aud-016-005) |
| P1 / PARTIAL | Evacuation is constructed without an agent, so [replan:619](../../apps/agents/evacuation/agent.py#L619) returns 503. [The demo phase:650](../../scripts/demo.py#L650) produces no route, zone, or transport plan and never supplies its loaded road/population data to the real [processing implementation:110](../../apps/agents/evacuation/pipeline.py#L110). | [AUD-016-006](#aud-016-006) |
| P1 / PARTIAL | [Resource phase:784](../../scripts/demo.py#L784) approves a hard-coded nonexistent plan. [The endpoint:381](../../apps/agents/resource_allocation/agent.py#L381) only writes an override audit and returns success; it does not retrieve, create, allocate, or mutate a plan. Demand matching and quantities in [the real pipeline:91](../../apps/agents/resource_allocation/pipeline.py#L91) are not exercised. | [AUD-016-007](#aud-016-007) |
| P1 / PARTIAL | Communication is created with no pipeline, so [process-handoff:185](../../apps/agents/communication/agent.py#L185) returns 503. Nevertheless [demo:954](../../scripts/demo.py#L954) reports template filenames as languages, one alert, and `safety_validated=True`. No bodies, interpolation, or safety validation occur in this fallback. | [AUD-016-008](#aud-016-008) |
| P1 / PARTIAL | [Alert approval narration:964](../../scripts/demo.py#L964) is not an approval transition or publication operation. Risk approval is disconnected from the seeded store; evacuation approval results are ignored; resource approval is an acknowledgement. Public-facing governance claims are not backed by approved entities or dry-run delivery receipts. | [AUD-016-009](#aud-016-009) |
| P1 / PARTIAL | [Ingestion:24](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L24) generates a `sig-...` identifier, but [risk evidence:548](../../scripts/demo.py#L548) and [audit:600](../../scripts/demo.py#L600) cite `signal-demo-001`. Handoffs are mostly handwritten records rather than delivered payloads; confidence and timestamps are not tied to actual transfer results. | [AUD-016-010](#aud-016-010) |
| P1 / PARTIAL | [Seed/client startup:1119](../../scripts/demo.py#L1119) occurs before the run record, [phase dispatch:1192](../../scripts/demo.py#L1192) has no exception conversion, and [SIGINT:1251](../../scripts/demo.py#L1251) exits immediately. Failed startup, exceptions, and interrupts lose the required structured partial summary and stage identity. | [AUD-016-011](#aud-016-011) |
| P2 / PARTIAL | [Escalation:727](../../scripts/demo.py#L727) uses total facility capacity greater than 100, not affected population; [resource escalation:841](../../scripts/demo.py#L841) uses inventory length greater than five, not assigned quantities. Neither threshold is configurable; escalation reason/threshold are absent from JSON. T022's >1000 example is not itself a mandated default. | [AUD-016-012](#aud-016-012) |
| P2 / PARTIAL | [Seed loading:225](../../scripts/demo.py#L225) checks file existence and parses JSON but does not check required top-level keys, usable contents, or a nonempty scenario match. Missing all languages can still yield a passing fabricated alert. [Seed tests:354](../../tests/simulation/test_demo_script.py#L354) inspect committed keys, not rejection behavior. | [AUD-016-013](#aud-016-013) |
| P2 / PARTIAL | [Scenario defaults:146](../../scripts/demo.py#L146) combine ACT/Sydney/FNQ events with FNQ roads/population and Sydney resources. [Signal payload:424](../../scripts/demo.py#L424) always says NSW, while [ingestion:15](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L15) creates every incident as flood/warning. The scenario test asserts labels, not semantic consistency. | [AUD-016-014](#aud-016-014) |
| P2 / PARTIAL | [Models:49](../../scripts/demo.py#L49) lack the enums, bounds, cross-field checks, and phase cardinality required by [data-model:12](data-model.md#L12). Per-phase inputs/outputs and draft content from FR-006/Key Entities are not represented adequately. [Serializer tests:395](../../tests/simulation/test_demo_script.py#L395) deliberately serialize invalid `demo-test` run IDs with no phases. | [AUD-016-015](#aud-016-015) |
| P2 / PARTIAL | [Narrator:181](../../scripts/demo.py#L181) has a fixed delay on every print, no pacing configuration or encoding fallback. It narrates unverified outcomes, displays no alert bodies, and [summary:1039](../../scripts/demo.py#L1039) prints elapsed time before summary narration/final serialization. | [AUD-016-016](#aud-016-016) |
| P2 / PARTIAL | The [22 demo tests:54](../../tests/simulation/test_demo_script.py#L54) primarily assert generated labels/counts. Their sole injected phase failure is HTTP 500 during setup; they do not establish real plan/draft generation, semantic failures, egress isolation, cleanup, interruption, or a cold CLI launch. | [AUD-016-017](#aud-016-017) |
| P2 / MISSING | No CI selection of this demo was found in the workflow search. [CI:131](../../.github/workflows/ci.yml#L131) and [Windows CI:196](../../.github/workflows/ci.yml#L196) exclude its simulation test directory. A runnable helper is not an installed CI gate. | [AUD-016-018](#aud-016-018) |
| P2 / CONFLICT | Current [FR-014](spec.md#L112) allows missing-language degradation, while [SC-005](spec.md#L143) requires six languages on every success. Tasks/research/model examples disagree over validation, default factories, phase output, file counts, and pacing. [T039](tasks.md#L140) is checked but its external documentation entry is missing. | [AUD-016-019](#aud-016-019) |
| P2 / UNVERIFIED | Checked [T038](tasks.md#L139), [performance assertion:322](../../tests/simulation/test_demo_script.py#L322), and quickstart example output are not evidence that the commands ran successfully or that cold CI/live-demonstration budgets were met at this revision. | [AUD-016-020](#aud-016-020) |
| P2 / UNVERIFIED | [HYP-014 and persona validation labels](spec.md#L153) lack Spec 016-scoped supporting records in the searched evidence. The named hypothesis stub is MISSING. Portfolio [rubric claims](../028-capstone-alignment/evidence/rubric-postfeature.md#L24) do not establish SC-007's Application Demo grade or HYP-014's per-spec experiment. | [AUD-016-021](#aud-016-021) |

## Controlling Execution Trace

| Phase | Actual source path and boundary | Audit conclusion |
| --- | --- | --- |
| Activation / setup | [run_pipeline:1119](../../scripts/demo.py#L1119) loads seeds, constructs six clients, then [setup:334](../../scripts/demo.py#L334) clears shared state and checks five HTTP endpoints. Monitoring/risk/evacuation have no agent; communication has no pipeline. | Client existence is not agent readiness. There is no platform health gate or explicit lifespan/close handling. |
| Ingestion / monitoring | [demo:408](../../scripts/demo.py#L408) calls [signals route:14](../../apps/api/app/api/routes/signals.py#L14), [authoritative ingestion:12](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L12), then [monitoring association:344](../../apps/agents/monitoring/agent.py#L344). | The first writes a platform signal; the latter rejects a missing agent. The summary overwrites that distinction. The successful ingestion creates an in-memory incident, so the dashboard's Cosmos fallback is not claimed as the ordinary successful path. |
| Risk analysis | [demo:527](../../scripts/demo.py#L527) inserts a recommendation into a platform dictionary, then calls [risk override:713](../../apps/agents/risk_assessment/agent.py#L713). | No assessment pipeline or shared approval store is connected. A response can say approved without changing the inserted recommendation. |
| Evacuation routing | [demo:650](../../scripts/demo.py#L650) calls [replan:619](../../apps/agents/evacuation/agent.py#L619) with no agent and then [override:499](../../apps/agents/evacuation/agent.py#L499). | A 503 is treated as success; no road-backed plan is created. Override has conditional store mutation only when a configured agent/store exists. |
| Resource allocation | [demo:784](../../scripts/demo.py#L784) calls [resource override:381](../../apps/agents/resource_allocation/agent.py#L381). The constructed agent loads inventory but its [process_handoff:174](../../apps/agents/resource_allocation/agent.py#L174) is never called. | An audit acknowledgement is reported as an allocation; no assignments or quantities are inspected. |
| Alert drafting | [demo:897](../../scripts/demo.py#L897) calls an unconfigured [communication pipeline handler:185](../../apps/agents/communication/agent.py#L185), then invents language/safety/approval outcomes. | Actual [draft/safety processing:91](../../apps/agents/communication/pipeline.py#L91) and [approval:217](../../apps/agents/communication/agent.py#L217) exist but are disconnected. |
| Audit summary | [summary:1026](../../scripts/demo.py#L1026) counts local lists; [serialize_output:1074](../../scripts/demo.py#L1074) writes JSON. | Aggregation and serialization exist, but do not validate the reality or completeness of their inputs. |

The resource agent constructs an environment-sensitive [LLM client via the mixin:26](../../apps/agents/common/llm_mixin.py#L26). However, its demo health path is optimistic and its override path does not invoke generation. This audit does **not** claim an observed live LLM call. Conversely, [platform import-time telemetry](../../apps/api/app/main.py#L12) and [environment-driven repository construction](../../apps/api/app/repositories/signal_repository.py#L26) are real reachable branches. A [resource audit write:43](../../apps/agents/resource_allocation/audit.py#L43) normally buffers in memory without Cosmos, but configured buffer exhaustion can spill locally. These distinctions must remain in future isolation tests.

## Open Remediation Tasks

All tasks remain unchecked. P1/P2 is priority, not an implementation status. Each tester subsection is separate from developer work. **V1-V6** refer to the future-only validation recipes below; their offline prerequisites are mandatory even for unit-test commands. Existing test homes are cited; proposed test cases are not existing evidence.

<a id="aud-016-001"></a>

- [ ] **AUD-016-001 [P1] Establish an explicit offline dependency boundary before app imports.**

  **Trace / expected vs observed:** [FR-003](spec.md#L101), [SC-008](spec.md#L146), [T005](tasks.md#L43), CHK074/CHK076 and R-001/R-004 require zero external services. [create_clients:295](../../scripts/demo.py#L295) uses ambient configuration, reaching the telemetry and repository branches identified above. Impact: a presenter or CI worker with configured endpoints can initiate unintended external work or fail before the demo starts.

  **Developer:** Own the demo factory boundary and narrowly scoped injection points in [platform startup](../../apps/api/app/main.py#L25), [router dependencies](../../apps/api/app/api/routes/simulations.py#L28), and [agent construction](../../apps/agents/resource_allocation/agent.py#L112). Supply explicit in-memory repositories, no-export telemetry, local audit sinks, deterministic template-generation dependencies, and no-send delivery. Establish the boundary before importing modules with side effects. Do not globally weaken production authentication, silently remove the user's settings, or depend on a failed network request to activate fallback. Treat configured Foundry/OpenAI, Cosmos, telemetry, and auth paths as separate dependencies.

  **Tester:** Extend [TestFullPipeline](../../tests/simulation/test_demo_script.py#L54) with a pre-import egress-denial fixture. Positive: a fresh process with no service settings completes actual processing locally. Negative: sentinel Cosmos/Foundry/OpenAI/telemetry configurations must cause zero credential, socket, HTTP, exporter, or cloud-constructor attempts, not merely zero successful calls. Edge: modules already imported and a pre-existing client must not bypass isolation; local audit spill must stay in owned scratch or be disabled. Use V1/V3 only after guard construction; do not contact real endpoints. Assert unchanged caller configuration and no external files beyond authorized output.

  **Dependencies / completion:** Coordinate with AUD-016-002 and AUD-016-019. Complete when dependency selection is demonstrably explicit before imports and adversarial environment tests prove no external I/O, without changing production defaults.

<a id="aud-016-002"></a>

- [ ] **AUD-016-002 [P1] Scope state and resource lifetime to one demo run.**

  **Trace / expected vs observed:** [Edge case 4](spec.md#L92), [T005](tasks.md#L43), [T008](tasks.md#L46), [T009](tasks.md#L60), and plan storage/isolation assumptions require clean local operation. [reset_state:33](../../apps/api/app/services/state_store.py#L33) clears all tenants' dictionaries; [run_pipeline:1103](../../scripts/demo.py#L1103) neither closes clients nor cleans demo-owned data. The request [tenant middleware:47](../../apps/api/app/middleware/tenant_middleware.py#L47) defaults ordinary API requests to live; a handwritten `tenant_id="demo"` in a later handoff does not scope the earlier store.

  **Developer:** Own [run_pipeline](../../scripts/demo.py#L1103), [create_clients](../../scripts/demo.py#L295), and the needed state adapters. Replace blanket reset with isolated per-run stores or a safe, documented ownership mechanism. Manage every successfully created client and enabled lifespan in a finally/context boundary, including partial construction failure. Clean only this run's state, pending approvals, audit buffers and owned files. Preserve the caller's SIGINT handler and avoid leaving global configuration changes. Do not assert that six clients imply six spawned processes; the source starts none.

  **Tester:** In [TestFailurePaths](../../tests/simulation/test_demo_script.py#L189), seed sentinel unrelated incident/signal/recommendation/approval/task data. Positive: sequential runs leave those sentinels unchanged and do not reuse prior demo entities. Negative: fail each factory and phase and assert already-created clients close once, no later clients/steps start, and only owned state is removed. Edge: interruption during setup and overlapping run contexts cannot cross-delete data. Use V1; use a disposable process for signal cases. Completion asserts restored handlers and no owned resources retained after success, failure, or interruption.

  **Dependencies / completion:** AUD-016-001 and AUD-016-011. Resolve whether shared-process concurrency is supported under AUD-016-019; do not claim it without tests. Original T009's reset instruction needs an authorized compatibility decision rather than destructive literal reuse.

<a id="aud-016-003"></a>

- [ ] **AUD-016-003 [P1] Gate all six services on real offline readiness.**

  **Trace / expected vs observed:** [FR-002](spec.md#L100), [US1-AS2](spec.md#L31), [T009](tasks.md#L60) and [R-007](research.md#L294) require healthy/degraded acceptance and unhealthy rejection. [setup:334](../../scripts/demo.py#L334) accepts unknown/unhealthy bodies and never checks the platform. [Monitoring health:273](../../apps/agents/monitoring/agent.py#L273) and [evacuation health:379](../../apps/agents/evacuation/agent.py#L379) expose genuinely missing dependencies, not proof that usable fallback processing exists.

  **Developer:** Own setup and demo-local app dependencies. Initialize actual offline agents/pipelines and check the platform's real health route as well as each agent. Define which explicitly described degradations remain operational. Reject unknown/malformed responses, unavailable processing, missing road/inventory data, non-success HTTP, and bounded timeouts. Keep healthy and degraded counts disjoint and include service names and dependency results. Do not fix by relabelling every unhealthy dependency as healthy.

  **Tester:** Extend [health failure test:202](../../tests/simulation/test_demo_script.py#L202). Positive: six checks complete before ingestion; supported degraded mode is accurately counted. Negative: parameterize HTTP 500, 200/unhealthy, unknown/missing status, malformed JSON, missing core dependency, and platform failure. Edge: a slow check times out under the agreed budget and starts no later phase. Use V1 with no-network clients; assert one failing setup record, named dependency, six skipped downstream entries and exit 1.

  **Dependencies / completion:** AUD-016-001, AUD-016-002, AUD-016-005, AUD-016-006, AUD-016-007, AUD-016-008; health/time-budget contract decision in AUD-016-019. Complete only when reported readiness corresponds to the processing objects actually used.

<a id="aud-016-004"></a>

- [ ] **AUD-016-004 [P1] Stop converting endpoint and business failures into passing phases.**

  **Trace / expected vs observed:** [FR-005](spec.md#L103), [FR-007](spec.md#L105), [edge case 1](spec.md#L89), [T007](tasks.md#L45), [T010](tasks.md#L61), [T012](tasks.md#L63), [T014](tasks.md#L65), [T016](tasks.md#L67), [T035](tasks.md#L136). The fabricated association count, 503 replan success, ignored override/dashboard failures, and error/discard alert fallback make unrelated failures indistinguishable from a healthy pipeline.

  **Developer:** Own [monitoring phase:408](../../scripts/demo.py#L408), [evacuation:650](../../scripts/demo.py#L650), [communication:897](../../scripts/demo.py#L897), and the common phase-result contract. Validate both HTTP status and the response's required business outcome. Reject zero association where association is the claimed action; verify dashboard incident/signal visibility; require actual plan/draft identifiers and accepted transitions. Treat unavailable services, rejected/discarded handoffs, negative acknowledgement bodies, and invalid payloads as failures, except the explicitly bounded missing-language policy. Never manufacture counters to make a phase pass.

  **Tester:** Use V1 in [TestFailurePaths](../../tests/simulation/test_demo_script.py#L189). Positive: inspect actual per-service results. Negative: inject 503/404/429/500, 200 with `success=False`, discarded handoffs, zero associations, and missing dashboard signal. Edge: a valid no-replan decision must have an explicitly agreed status rather than an unconditional "plan triggered" summary. Assert the precise failing phase/agent, unmodified observed counts, no approval/alert invented afterward, and no later handler calls.

  **Dependencies / completion:** AUD-016-003 and AUD-016-011; integrate with processing tasks. Complete when changing any required endpoint outcome to failure reliably changes both JSON and exit code without later phase execution.

<a id="aud-016-005"></a>

- [ ] **AUD-016-005 [P1] Connect risk analysis and approval to the ingested signal and a real local store.**

  **Trace / expected vs observed:** [FR-005](spec.md#L103), [FR-009](spec.md#L107), [FR-011](spec.md#L109), [US1-AS3](spec.md#L32), [US2-AS2](spec.md#L48), [T011](tasks.md#L62), [T017](tasks.md#L83). The fixed [seeded recommendation:548](../../scripts/demo.py#L548) is not an assessment result, and a store-less [override handler:749](../../apps/agents/risk_assessment/agent.py#L749) cannot approve it. T011/R-002's seeding shortcut conflicts with the feature's promised analysis, rather than proving the analysis implementation is missing everywhere.

  **Developer:** Own the demo risk phase and its dependencies on [AssessmentProcessingPipeline:45](../../apps/agents/risk_assessment/pipeline.py#L45). Feed the actual platform signal and its provenance into deterministic local assessment; connect recommendation creation and override to the same local store. Report real assessment/recommendation IDs, rationale, confidence, and resulting approval status. Use supported processing or a narrowly scoped adapter consistent with the documented newer workflow; do not silently migrate the full platform or disguise a fixed fixture as computation. Obtain the contract resolution in AUD-016-019 before changing T011's intended scope.

  **Tester:** Reuse patterns in [risk pipeline tests:13](../../tests/unit/test_risk_assessment_pipeline.py#L13), strengthening their conditional/weak assertions, and add demo assertions under [TestFullPipeline](../../tests/simulation/test_demo_script.py#L54). Positive: a changed input signal changes the assessment and stored recommendation while preserving actual IDs. Negative: missing signal/store, rejected override, or failed assessment produces no approval claim. Edge: below-threshold confidence produces a conservative explicit result; simulation output cannot escalate live. Use V1/V2. Assert the stored proposed-to-approved transition, not just HTTP 200.

  **Dependencies / completion:** AUD-016-001, AUD-016-002, AUD-016-004, AUD-016-010, AUD-016-019. Complete when one trace links ingestion, analysis, recommendation, and accepted local approval.

<a id="aud-016-006"></a>

- [ ] **AUD-016-006 [P1] Produce and verify a seed-backed evacuation plan.**

  **Trace / expected vs observed:** [FR-004](spec.md#L102), [FR-005](spec.md#L103), [US1-AS3](spec.md#L32), [T012](tasks.md#L63), [T018](tasks.md#L84). The [demo replan request:663](../../scripts/demo.py#L663) supplies neither affected-area geometry nor population data, loads no road network into an evacuation agent, and accepts an uninitialized-agent error as a plan.

  **Developer:** Own demo evacuation construction and phase wiring. Reuse [EvacuationProcessingPipeline:65](../../apps/agents/evacuation/pipeline.py#L65) and its local road/population/facility inputs to create an initial plan before testing replanning. Pass the actual assessment, affected area and corresponding seed snapshot. Validate routes, safe alternatives, transport demands, and plan identity; approve the resulting plan in an isolated store. Preserve safety restrictions and make a no-route/shelter outcome explicit rather than claiming a computed route that does not exist.

  **Tester:** Extend [evacuation pipeline fixture:48](../../tests/unit/test_evacuation_pipeline.py#L48) and [demo full-pipeline tests](../../tests/simulation/test_demo_script.py#L54). Positive: known graph nodes and population yield inspectable zones/routes and supporting IDs. Negative: unloaded roads, disconnected graph, failed replan, denied override, or nonexistent plan cannot report routing success. Edge: closure changes the route or reports shelter/no-safe-route with the correct approval requirement. Use V1/V2 with copied seed fixtures and no Cosmos/LLM. Assert route edges are in the graph and assigned transport/clearance outputs belong to this incident.

  **Dependencies / completion:** AUD-016-001, AUD-016-002, AUD-016-004, AUD-016-005, AUD-016-013, AUD-016-014. Complete when the observable routing result comes from computation, not a request receipt.

<a id="aud-016-007"></a>

- [ ] **AUD-016-007 [P1] Demonstrate actual resource assignments, criteria, and quantities.**

  **Trace / expected vs observed:** [FR-005](spec.md#L103), [FR-009](spec.md#L107), [US3-AS2](spec.md#L65), [T013](tasks.md#L64), [T019](tasks.md#L85). [Demo:800](../../scripts/demo.py#L800) sends an override for a fixed plan ID; [resource override:400](../../apps/agents/resource_allocation/agent.py#L400) only audits it. Neither assignments nor resource status changes establish allocation.

  **Developer:** Own demo resource phase and a local plan-store/approval adapter around [AllocationProcessingPipeline:91](../../apps/agents/resource_allocation/pipeline.py#L91). Feed real recommendation and transport demands, run inventory eligibility/matching, retain the resulting plan, then approve that plan. Report quantities, matched resource IDs, selection criteria, policy and shortfalls. Scope inventory reservations to the run, and preserve existing production interfaces while correcting any shared override integration needed by the demo.

  **Tester:** Reuse [resource pipeline fixtures:28](../../tests/unit/test_resource_allocation_pipeline.py#L28) and the existing demo module. Positive: a known demand gets the expected eligible resource and quantity. Negative: nonexistent plan, unavailable resource, no demands, or negative override acknowledgement cannot claim allocation. Edge: demand above inventory produces a quantified shortfall and escalation, without over-allocation or double reservation. Use V1/V2. Strengthen the existing conditional timelines assertion to require assignments for a fixture deliberately containing a match; assert inventory and plan transitions, not only nonempty summaries.

  **Dependencies / completion:** AUD-016-001, AUD-016-002, AUD-016-004, AUD-016-005; coordinate transport with AUD-016-006. Complete when output quantities reconcile to plan assignments and isolated inventory changes.

<a id="aud-016-008"></a>

- [ ] **AUD-016-008 [P1] Generate real multilingual drafts and propagate actual safety results.**

  **Trace / expected vs observed:** [FR-010](spec.md#L108), [SC-005](spec.md#L143), [US2-AS3](spec.md#L49), [T014](tasks.md#L65), [T020](tasks.md#L86), [T027](tasks.md#L106). [Demo:954](../../scripts/demo.py#L954) substitutes loaded language keys for content and sets safety true after a pipeline 503. This falsely represents a validated public warning.

  **Developer:** Own communication dependency construction and [run_communication_phase](../../scripts/demo.py#L897). Connect a real local [CommunicationProcessingPipeline:57](../../apps/agents/communication/pipeline.py#L57), template loader, no-network translator, and safety validator. Select matching hazard/severity/type templates and interpolate actual scenario values. Retain each produced title/body/action and validation state; derive language coverage, channels and count from those drafts. Fail or explicitly degrade on unusable content according to the resolved missing-language policy. Do not substitute `safety_validated=True` for the validator's result, and do not send real notifications.

  **Tester:** Use [communication pipeline tests:36](../../tests/unit/test_communication_pipeline.py#L36) as a component home, but do not reuse its one-language mocked translator as six-language evidence. In the demo tests, positive cases assert six nonempty locale-appropriate template-derived drafts and zero unresolved interpolation fields. Negative: 503/discard, unsafe result, missing content, or zero usable languages cannot produce a safe alert. Edge: one missing locale reports the exact omission while preserving valid drafts according to AUD-016-019. Use V1/V2; inject sentinel text into copied templates to prove content is consumed, and assert no outbound delivery calls.

  **Dependencies / completion:** AUD-016-001, AUD-016-004, AUD-016-005, AUD-016-007, AUD-016-013, AUD-016-019. Complete when every reported language and safety flag has a corresponding inspected draft and validation result.

<a id="aud-016-009"></a>

- [ ] **AUD-016-009 [P1] Make simulated approvals and dry-run publication real state transitions.**

  **Trace / expected vs observed:** [FR-009](spec.md#L107), [FR-017](spec.md#L115), [US3-AS1](spec.md#L64), [T017](tasks.md#L83), [T018](tasks.md#L84), [T019](tasks.md#L85), [T020](tasks.md#L86), [T026](tasks.md#L105). [Approval narration:964](../../scripts/demo.py#L964) records approval without calling the existing approval workflow or publishing even to a local sink.

  **Developer:** Own orchestration of proposed/approved/draft/published-demo states. Connect the existing [communication approval handler:217](../../apps/agents/communication/agent.py#L217) and corresponding risk/plan approval adapters to actual locally produced entities. Use explicitly simulated authorized personas; record approver, policy, input ID, outcome and transition time after successful mutation. Demonstrate publication only through a no-send in-memory sink with observable channel receipts, or obtain an explicit drafting-only scope resolution. Preserve automatic, noninteractive behavior and never bypass production human-authorization rules.

  **Tester:** Reuse [pending-alert fixture:23](../../tests/unit/test_communication_endpoints.py#L23) and [approval success/not-found assertions:78](../../tests/unit/test_communication_endpoints.py#L78). The [manual rehearsal test:59](../../tests/simulation/test_quickstart_rehearsals.py#L59) provides a publication assertion but seeds state; it is not full-agent evidence. Positive: approvals precede simulated publication and receipts name actual alert/plan IDs. Negative: denial, unknown entity, insufficient role, and unsafe draft produce no downstream publication. Edge: duplicate approval does not duplicate the receipt. Use V1/V2; assert no actual SMS/push/broadcast transport and no prompt input.

  **Dependencies / completion:** AUD-016-001, AUD-016-005, AUD-016-006, AUD-016-007, AUD-016-008, AUD-016-019. Complete when every claimed approval/publication has a verified local transition and visibly simulated provenance.

<a id="aud-016-010"></a>

- [ ] **AUD-016-010 [P1] Preserve real provenance and record handoffs at actual transfers.**

  **Trace / expected vs observed:** [FR-011](spec.md#L109), [FR-012](spec.md#L110), [SC-006](spec.md#L144), [T017](tasks.md#L83), [T018](tasks.md#L84), [T019](tasks.md#L85), [T020](tasks.md#L86), [T021](tasks.md#L87), [T023](tasks.md#L89). The ingested signal ID is captured only in one phase; later evidence is fixed. Four appended summaries are not evidence of four delivered payloads.

  **Developer:** Own per-run context and handoff/audit assembly in [demo:600](../../scripts/demo.py#L600), [demo:750](../../scripts/demo.py#L750), [demo:864](../../scripts/demo.py#L864), and [demo:990](../../scripts/demo.py#L990). Carry actual signal, assessment, recommendation, plan and alert IDs forward. Capture accepted source/destination, payload summary or reference, confidence and send/accept time at the transfer boundary. Record failed/rejected decisions separately; do not claim a delivered handoff after rejection. Align existing camelCase payload consumers, such as [communication retrieval:234](../../apps/agents/communication/pipeline.py#L234), with the producer; the current `recommendation_id` payload does not supply `recommendationId`. Use collision-resistant run/entity identities compatible with the approved output contract.

  **Tester:** Extend [audit assertions:95](../../tests/simulation/test_demo_script.py#L95) and [handoff assertions:115](../../tests/simulation/test_demo_script.py#L115). Positive: every supporting ID resolves within this run, and every delivered record matches the receiving payload and confidence. Negative: fabricated IDs, wrong tenant/incident/target, missing timestamp, rejected transfer, and mismatched casing fail validation. Edge: two runs within one second and a duplicated handoff preserve distinct run ownership and no false delivery. Use V1/V2; compare actual observed transfer events to records one-for-one rather than `len >= 4`.

  **Dependencies / completion:** AUD-016-002 and processing/approval tasks; AUD-016-015 resolves schema identity constraints. Complete when 100% of required decisions and handoffs are traceable without fixed placeholder IDs.

<a id="aud-016-011"></a>

- [ ] **AUD-016-011 [P1] Preserve structured failure and interruption output from startup through finalization.**

  **Trace / expected vs observed:** [FR-006](spec.md#L104), [FR-007](spec.md#L105), [edge case 4](spec.md#L92), [T006](tasks.md#L44), [T007](tasks.md#L45), [T008](tasks.md#L46), [T016](tasks.md#L67). [run_pipeline:1119](../../scripts/demo.py#L1119) cannot serialize a startup failure; [main:1251](../../scripts/demo.py#L1251) exits on SIGINT without access to partial results. Exceptions during any phase also bypass phase attribution.

  **Developer:** Own [run_pipeline](../../scripts/demo.py#L1103), [main](../../scripts/demo.py#L1243), and [serialize_output](../../scripts/demo.py#L1074). Create a run record before seed loading/client creation. Convert phase exceptions and interruption into a consistent final result with completed, failed/interrupted and skipped phases under the resolved schema. Preserve agent/phase/error context and exit codes 1, 2 and 130; argparse help remains a successful non-run path. Finalize once, clean up through AUD-016-002, and restore the original signal handler. Define truthful behavior when the requested output destination itself is unwritable; do not claim a successful file write or lose all actionable diagnostics.

  **Tester:** Extend [TestFailurePaths](../../tests/simulation/test_demo_script.py#L189) and [TestSerializeOutput](../../tests/simulation/test_demo_script.py#L392). Positive: completed records survive a later failure. Negative: missing/corrupt seed, client-construction error, request exception, malformed response, denied output path, and broken pipe return the agreed exit/diagnostic behavior. Edge: interrupt during seed load, phase work, narration, and finalization emits at most one complete JSON object when the destination is usable; completed_at and skipped phases match the interruption contract. Use V1/V3/V4 in disposable processes with platform-appropriate signal handling. Assert exit 130, cleanup and no orphaned resources, not only stderr text.

  **Dependencies / completion:** AUD-016-002, AUD-016-004, AUD-016-015, AUD-016-019. Complete when every reachable failure boundary has deterministic machine-readable reporting where the output channel remains usable.

<a id="aud-016-012"></a>

- [ ] **AUD-016-012 [P2] Base escalation on configured policy and actual affected/allocated quantities.**

  **Trace / expected vs observed:** [US3-AS2](spec.md#L65), [US3-AS4](spec.md#L67), [FR-009](spec.md#L107), [FR-011](spec.md#L109), [T022](tasks.md#L88). [Facility-capacity sum:727](../../scripts/demo.py#L727) and [inventory count:841](../../scripts/demo.py#L841) are not evacuation impact or allocations; the escalation JSON has neither reason nor measured threshold.

  **Developer:** Own demo policy configuration and decision serialization. Define an approved example threshold and units; T022's >1000 people is an example, not permission to invent a production policy. Evaluate actual affected population and assigned resources from the generated plans. Record measured quantity, threshold, comparison, reason, required authority and simulated approval separately. Do not conflate available inventory with mobilized resources or facility capacity with all threatened residents.

  **Tester:** In the existing demo module use small fixture populations and inventories with deliberately different available versus assigned quantities. Positive: an above-threshold decision creates the correct escalation. Negative: below-threshold assignments and a large unused inventory do not. Edge: exercise exactly threshold minus one, threshold, and threshold plus one, including empty/unknown quantity. Use V1; assert policy/units/reason/authority in JSON and narration and matching total_escalations.

  **Dependencies / completion:** AUD-016-006, AUD-016-007, AUD-016-010, AUD-016-015, AUD-016-019. Complete when escalation is explainable from measured plan data and approved configuration.

<a id="aud-016-013"></a>

- [ ] **AUD-016-013 [P2] Validate usable seed data before constructing any agents.**

  **Trace / expected vs observed:** [FR-004](spec.md#L102), [FR-014](spec.md#L112), [edge case 2](spec.md#L90), [edge case 5](spec.md#L93), [T004](tasks.md#L42), [T033](tasks.md#L125). [load_seed_data:225](../../scripts/demo.py#L225) parses JSON but accepts empty/wrong-key structural dictionaries and empty scenario matches; malformed JSON lacks the required file-specific structured startup record.

  **Developer:** Own seed preflight and its data contract. Validate required top-level types/keys, minimally usable records, required template fields, language-code/file agreement, and at least a usable matching scenario template under the resolved policy. Apply semantic checks needed by the consumers, including nonnegative quantities and usable geometry/references. Keep missing structural files fatal and missing individual language files explicitly degradable. Return or raise structured path-specific errors/warnings into the run record; do not call `sys.exit` from the loader or defer validation to a partially constructed agent. Reuse existing model/loader validation where compatible rather than duplicating a complete data framework.

  **Tester:** Extend [TestSeedDataLoading:341](../../tests/simulation/test_demo_script.py#L341) and the [missing-seed test:192](../../tests/simulation/test_demo_script.py#L192), using tmp_path copies and a create_clients spy. Positive: all nine named physical files and minimal valid records work. Negative: each structural file missing, invalid JSON, wrong root type, missing keys, negative quantities, invalid references, and no scenario match produce file-specific errors before any agent construction. Edge: one locale missing, all locales missing, empty locale arrays and inaccessible directory follow the separately agreed degradation policy. Use V1; assert exact warnings/skipped languages, not just a nonempty dictionary.

  **Dependencies / completion:** AUD-016-011 and AUD-016-019; integrate with AUD-016-008. Complete when preflight prevents invalid inputs reaching processing and the reported validated-file count is real.

<a id="aud-016-014"></a>

- [ ] **AUD-016-014 [P2] Keep scenario, incident, jurisdiction, and seed geography consistent.**

  **Trace / expected vs observed:** [FR-015](spec.md#L113), [FR-016](spec.md#L114), [US4-AS1](spec.md#L81), [US4-AS2](spec.md#L82), [T030](tasks.md#L122), [T031](tasks.md#L123), [T032](tasks.md#L124). Configuration changes category/location, but [demo payload:424](../../scripts/demo.py#L424) fixes NSW and [incident construction:15](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L15) fixes flood/warning. Structural seed geography does not align with all three declared defaults.

  **Developer:** Own scenario configuration and the demo-local incident seeding/ingestion adapter. Select a coherent geographic fixture set or explicitly approved coordinate adaptation, without changing committed seed data as an accidental side effect. Ensure incident type/severity/jurisdiction, signal location, affected zones, roads, population and resource reachability agree. Make cyclone/flood deliverables versus stretch-goal language explicit. Preserve the default bushfire command and do not introduce PH/JP/BD variants that remain deferred.

  **Tester:** Strengthen [scenario tests:247](../../tests/simulation/test_demo_script.py#L247) to capture actual ingested category, hazard, severity, coordinates, jurisdiction, incident dashboard and selected template content for all three scenarios. Positive: each scenario yields coherent outputs. Negative: a cyclone named only in the root JSON but processed as flood fails; out-of-area routing data must be rejected or clearly handled. Edge: changing hazard on the same local geography changes content while retaining valid graph/resource references. Use V1/V3. Assert payload semantics and different hazard-appropriate outputs, not only `scenario == ...`.

  **Dependencies / completion:** AUD-016-005, AUD-016-006, AUD-016-007, AUD-016-008, AUD-016-013, AUD-016-019. Complete when both JSON and narration describe the same physically coherent scenario.

<a id="aud-016-015"></a>

- [ ] **AUD-016-015 [P2] Enforce the run/output models and observable phase contracts.**

  **Trace / expected vs observed:** [FR-006](spec.md#L104), [Key Entities](spec.md#L117), [SC-004](spec.md#L142), [T003](tasks.md#L32), [T006](tasks.md#L44), [T034](tasks.md#L135). [Demo models:49](../../scripts/demo.py#L49) are permissive containers, not the validators required in [data-model.md](data-model.md). Details often contain only an acknowledgement or invented flag instead of input/output evidence.

  **Developer:** Own all eight models, finalization validation, and an authorized output-contract update. Enforce known phases/scenarios/statuses/agents, order-to-phase agreement, bounded confidence and coordinates, nonnegative counts/durations, nonempty supporting IDs, distinct source/target and valid run IDs. Validate seven ordered unique phases on success and the agreed failure/interruption representation. Include compact input/output references and real draft/safety/approval detail without dumping sensitive/full upstream objects. Define whether run-ID uniqueness extends beyond the current second-resolution pattern; do not silently break consumers. Preserve stable existing JSON keys unless the contract change explicitly versions them.

  **Tester:** Extend [schema-key test:73](../../tests/simulation/test_demo_script.py#L73) and [serializer tests:392](../../tests/simulation/test_demo_script.py#L392). Positive: validate complete success/failure/interruption objects, types and semantic links. Negative: unknown enum, order 0/8, swapped or duplicate phase, negative duration/count, confidence outside [0,1], invalid coordinates, empty support list, same-agent handoff, invalid run ID and safe status with no drafts are rejected. Edge: zero alerts is valid only for the agreed failed/degraded cases; timestamps are UTC and ordered. Use V1; replace `demo-test` fixtures with contract-valid IDs except in explicit rejection tests.

  **Dependencies / completion:** AUD-016-010, AUD-016-011, AUD-016-019. Complete when model and serialized-output checks agree with both contracts and the spec's observable inputs/outputs.

<a id="aud-016-016"></a>

- [ ] **AUD-016-016 [P2] Make narration accurate, configurable, portable, and honestly timed.**

  **Trace / expected vs observed:** [FR-008](spec.md#L106), [SC-002](spec.md#L140), [US2-AS1](spec.md#L47), [US2-AS2](spec.md#L48), [US2-AS3](spec.md#L49), [T024](tasks.md#L103), [T025](tasks.md#L104), [T026](tasks.md#L105), [T027](tasks.md#L106), [T028](tasks.md#L107), [T029](tasks.md#L108), [T032](tasks.md#L124). The [narrator:181](../../scripts/demo.py#L181) works on stderr but lacks configurable pacing and an unsupported-encoding fallback; [summary:1039](../../scripts/demo.py#L1039) prints an incomplete elapsed duration.

  **Developer:** Render narration from validated phase/decision/draft results, including actual inputs, recommendation support, approved plan quantities, draft bodies and channel targets. Keep the simulated-review label explicit. Use configurable bounded pacing with no CI delay, preserving the existing CLI unless an additional option is approved. Handle supported Windows/redirected stream encodings without compromising JSON. Measure an explicitly defined end-to-end wall-clock interval, including startup, narration and output, and avoid claiming the pre-summary duration is the final total.

  **Tester:** Extend [TestNarrator:363](../../tests/simulation/test_demo_script.py#L363) and [verbose test:271](../../tests/simulation/test_demo_script.py#L271). Positive: seven ordered phase labels, inputs/outputs, support IDs, real decisions and six draft bodies appear on stderr while stdout remains one JSON object. Negative: unavailable/failed processing never prints success, and a restricted-encoding stream is handled as documented. Edge: no TTY, verbose plus output file, zero pacing, maximum supported pacing and interrupted narration. Use V1/V3; stub delays for content tests and use V5 separately for real timing.

  **Dependencies / completion:** AUD-016-004, AUD-016-008, AUD-016-009, AUD-016-010, AUD-016-011, AUD-016-019. Complete when narration is a faithful projection of validated outcomes and timing claims are measured consistently.

<a id="aud-016-017"></a>

- [ ] **AUD-016-017 [P2] Strengthen tests from summary self-checks to behavior assertions.**

  **Trace / expected vs observed:** [T034](tasks.md#L135), [T035](tasks.md#L136), [T036](tasks.md#L137), [T037](tasks.md#L138), [SC-001](spec.md#L139), [SC-004](spec.md#L142), [SC-005](spec.md#L143), [SC-006](spec.md#L144). The exact assertions reviewed are summarized in the test-evidence section below. All-positive labels generated by the script can satisfy them despite absent processing.

  **Developer:** Keep [the existing demo module](../../tests/simulation/test_demo_script.py#L1) as the primary home. Add reusable run-context, copied-seed, egress-denial, fake-clock, transport-spy and fault-injection fixtures, with reliable teardown and no live services. Exercise the CLI boundary as well as direct orchestration. Retain inexpensive model/unit tests, but separate deliberately mocked handler behavior from an offline real-processing integration case. Do not relax expected outcomes to accommodate missing agents, and do not introduce a suite that only reasserts new hard-coded fields.

  **Tester:** Positive: validate one complete observable chain and all scenario payloads. Negative: parameterize each required handler's failure and business-negative response, validate phase identity/skipping/no later calls, and prove replacing real plans/drafts with empty objects fails tests. Edge: concurrent identity collisions, repeated runs, corrupt seeds, partial languages, interruption, output errors and redirected streams. Use V1/V2/V4 after isolation fixes. Require timestamp/payload/support-ID/confidence/quantity/content assertions; existing names such as "signal type" must actually check that property.

  **Dependencies / completion:** AUD-016-001 through AUD-016-016 as applicable. Complete when each behavior defect has a discriminating regression assertion in an existing suitable test home and product execution results are recorded separately, not inferred from test source.

<a id="aud-016-018"></a>

- [ ] **AUD-016-018 [P2] Install the demo as an explicit bounded CI smoke gate.**

  **Trace / expected vs observed:** [US1](spec.md#L20), [FR-007](spec.md#L105), [FR-013](spec.md#L111), [SC-003](spec.md#L141), [plan Quality Gates](plan.md#L36), and [T034](tasks.md#L135)/[T037](tasks.md#L138). No matching workflow selection was found; the [current CI selections](../../.github/workflows/ci.yml#L131) cannot run this simulation test merely because it exists.

  **Developer:** Own a narrowly scoped CI change after the offline harness is trustworthy. Explicitly invoke the selected demo test/CLI contract, provision only declared local dependencies, apply a bounded job timeout, preserve the command exit code, and retain JSON/diagnostic evidence on failure. Do not turn on cloud credentials or use continue-on-error to make a smoke check green. Align the Python/OS matrix and trigger scope with the documented CI contract and existing required-check administration; do not claim branch-protection enforcement from workflow YAML alone.

  **Tester:** Positive: in a future authorized CI run, prove the demo command is selected and its artifact belongs to the same revision. Negative: inject a demo phase failure and confirm the check fails, retains the failed-stage JSON, and cannot be masked by piping/conditional commands. Edge: timeout and artifact-write failure remain non-green. Use V1/V3/V5; inspect the workflow and actual run/check status separately. No CI run was launched in this audit.

  **Dependencies / completion:** AUD-016-001, AUD-016-011, AUD-016-017, AUD-016-019. Complete when explicit selection and failing-gate behavior are evidenced; runtime branch-protection/sign-off remains UNVERIFIED until separately supplied.

<a id="aud-016-019"></a>

- [ ] **AUD-016-019 [P2] Resolve contract conflicts and correct onboarding/review documentation.**

  **Trace / expected vs observed:** [FR-014](spec.md#L112) versus [SC-005](spec.md#L143); [FR-005](spec.md#L103) versus [T011](tasks.md#L62)/[R-002](research.md#L69); [T004](tasks.md#L42), [T005](tasks.md#L43), [T009](tasks.md#L60), [T029](tasks.md#L108), [T039](tasks.md#L140), and all unresolved checklist rows. The [quickstart prerequisite](quickstart.md#L6) offers root installation even though [root dependencies:10](../../pyproject.toml#L10) do not declare the API/agent dependency set; [API](../../apps/api/pyproject.toml#L10) and [agents](../../apps/agents/pyproject.toml#L10) do.

  **Developer:** Product owner and demo maintainer must explicitly settle: genuine processing versus endpoint-rehearsal scope; drafting versus safe simulated publication; healthy/degraded acceptance; default versus reduced-language success including zero usable locales; scenario stretch-goal status; nine actual files versus ten-file examples; failure/interruption cardinality; phase inputs/outputs; pacing configuration; output overwrite/errors; time-budget measurement; and unsupported concurrency/SIGTERM/size/memory expectations. Preserve approved historical evidence and task checkboxes. In a separately authorized change, align specification/plan/research/contracts/quickstart with the decision, fix the root developer-documentation entry linking the command and quickstart, and reference correct subproject installation prerequisites. Correct the [first-failure circuit-breaker claim](research.md#L145): [the current default threshold is three](../../apps/agents/common/llm_config.py#L57), and this demo does not exercise the asserted generator fallback chain. Reconcile plan principle labels with the current constitution without amending it.

  **Tester:** Positive: walk every CLI example against agreed semantics and verify both documentation links resolve. Negative: contrast missing-one-language, absent pipeline, unknown health, and no-safe-route cases so documented degradation cannot mask actual failure. Edge: verify help/invalid arguments, combined flags, existing/non-writable destinations and declared unsupported behavior. Review every CHK/SQ/plan row in this report, recording a decision or explicit bounded deferral rather than silently requiring new product scope. Use V3/V4/V6 only in a future authorized phase. Review evidence must include named reviewer/date, not just checked boxes.

  **Dependencies / completion:** Contract decisions precede affected implementation tasks; final documentation follows their verified behavior. Complete when contradictions have explicit authority-approved resolutions, T039 has a real external entry, and checklist closure has its own evidence.

<a id="aud-016-020"></a>

- [ ] **AUD-016-020 [P2] Obtain revision-bound quickstart and performance evidence.**

  **Trace / expected vs observed:** [T038](tasks.md#L139), [FR-013](spec.md#L111), [SC-001](spec.md#L139), [SC-002](spec.md#L140), [SC-003](spec.md#L141), [SC-005](spec.md#L143), [SC-008](spec.md#L146). Example durations and a checked task are not execution receipts. [The existing timing test:322](../../tests/simulation/test_demo_script.py#L322) measures a direct call after module import and may encounter warmed process state; it does not prove cold CLI or verbose performance.

  **Developer:** Provide a future repeatable offline validation recipe that captures revision, interpreter/dependency versions, OS/hardware, clean versus warm state, command, start/end wall-clock interval, exit code, stdout/stderr and phase/draft evidence. Include default, verbose, output-to-file, cyclone and flood commands. Time through final output, including imports and narration for cold CLI evidence. Retain failures honestly and distinguish proposed evidence locations from existing artifacts. Do not retroactively mark original tasks or manufactured examples as executed.

  **Tester:** Positive: run the agreed commands in fresh isolated processes and capture semantic success plus elapsed <60 seconds for CI and <300 seconds for verbose. Negative: a deliberately delayed/failing phase must not produce a passing performance/evidence record. Edge: exactly 60/300 seconds is not "under" the threshold; output serialization and missing-template degradation must be accounted for. Use V1/V3/V5; record repeated-run method and do not convert any finite sample into proof of success on every possible run. No live infrastructure is required or authorized by this task.

  **Dependencies / completion:** AUD-016-001 through AUD-016-019 as applicable. Complete when independently readable, revision-bound receipts establish the agreed outcomes, with failures and any remaining limitations retained.

<a id="aud-016-021"></a>

- [ ] **AUD-016-021 [P2] Repair amendment evidence linkage without inventing validation or promoting deferred scope.**

  **Trace / expected vs observed:** [PER-040](spec.md#L153), [PER-041](spec.md#L154), [PER-042](spec.md#L155), [HYP-014](spec.md#L161), [SC-007](spec.md#L145), [SCP-044](spec.md#L169), [SCP-045](spec.md#L170), [SCP-046](spec.md#L171), [SCP-047](spec.md#L172). No matching HYP-014 stub or per-spec consultation/grade record was found in the search scope. The located portfolio snapshots measure different criteria/population from the Application Demo outcome.

  **Developer:** Own an authorized documentation/evidence follow-up with the product owner, not demo runtime. Correct the doubled-prefix hypothesis pointer to an approved canonical existing/new stub; any new path is **proposed**, not present evidence. Follow the [six-section stub contract](../028-capstone-alignment/contracts/evidence-stub.contract.md#L11), begin with Not tested, preserve frozen baselines, and identify a per-spec measurement window/falsification method and consultation record. Resolve validated persona references to attributable SME/practitioner records or explicitly retain UNVERIFIED status. Record an independent Application Demo assessment against the appropriate rubric criterion; do not reuse the portfolio mean as that grade. Retain the canonical meta declaration and all country/authority deferrals.

  **Tester / reviewer:** Positive: verify hypothesis ID, filename, six ordered sections, two preconditions, quantified falsification and owning-spec link; confirm evidence names the reviewer, date, revision and exact criterion. Negative: reject fabricated consultations, a score inferred from source, a missing/doubled-prefix link, or a portfolio-only score presented as Spec 016 evidence. Edge: a deferred country persona remains a placeholder after documentation repair; only authorized gates can promote it. Use V6; a future rubric assessment should apply the applicable grader skill and independently distinguish HYP-014 from SC-007. No delegation or assessment was performed here.

  **Dependencies / completion:** AUD-016-019 for scope decisions and AUD-016-020 for runtime material used by a later assessment. Evidence-stub repair may proceed independently under its change-control rules. Complete only with valid links and honest evidence state; authoring a stub does not validate the hypothesis.

## Requirement Coverage

### Functional Requirements and Success Criteria

| Original requirement | Status | Expected versus inspected evidence | Follow-up |
| --- | --- | --- | --- |
| [FR-001](spec.md#L99) | IMPLEMENTED | Root script entrypoint and all three flags exist at [parser:1216](../../scripts/demo.py#L1216) and [main:1243](../../scripts/demo.py#L1243). Clean-environment execution is not proven. | [AUD-016-017](#aud-016-017), [AUD-016-019](#aud-016-019), [AUD-016-020](#aud-016-020) |
| [FR-002](spec.md#L100) | PARTIAL | Six clients are constructed, but core processing dependencies and the platform health check are missing; [factories/setup:295](../../scripts/demo.py#L295). | [AUD-016-001](#aud-016-001), [AUD-016-003](#aud-016-003) |
| [FR-003](spec.md#L101) | PARTIAL | ASGI calls are local, but [import-time repository construction](../../apps/api/app/api/routes/simulations.py#L28) and [telemetry configuration](../../apps/api/app/main.py#L12) remain environment-sensitive. | [AUD-016-001](#aud-016-001), [AUD-016-002](#aud-016-002) |
| [FR-004](spec.md#L102) | IMPLEMENTED | [Loader:225](../../scripts/demo.py#L225) reads all four required data categories. Their meaningful consumption is a separate pipeline gap. | [AUD-016-006](#aud-016-006), [AUD-016-008](#aud-016-008), [AUD-016-013](#aud-016-013) |
| [FR-005](spec.md#L103) | PARTIAL | Platform signal ingestion exists, but [association:480](../../scripts/demo.py#L480) fails and subsequent processing is disconnected/fabricated. | [AUD-016-004](#aud-016-004), [AUD-016-005](#aud-016-005), [AUD-016-006](#aud-016-006), [AUD-016-007](#aud-016-007), [AUD-016-008](#aud-016-008) |
| [FR-006](spec.md#L104) | PARTIAL | [Seven phase dispatch entries:1092](../../scripts/demo.py#L1092) and JSON serialization exist; input/output evidence and exception/interrupt summaries do not satisfy the full contract. | [AUD-016-010](#aud-016-010), [AUD-016-011](#aud-016-011), [AUD-016-015](#aud-016-015) |
| [FR-007](spec.md#L105) | PARTIAL | [Orchestrator:1192](../../scripts/demo.py#L1192) responds to explicit failed results, but individual phases mask failures and errors can bypass reporting. | [AUD-016-004](#aud-016-004), [AUD-016-011](#aud-016-011), [AUD-016-018](#aud-016-018) |
| [FR-008](spec.md#L106) | PARTIAL | [Narrator:181](../../scripts/demo.py#L181) uses stderr without prompts, but narrates invented outcomes and lacks expected concrete draft/input detail. | [AUD-016-009](#aud-016-009), [AUD-016-016](#aud-016-016) |
| [FR-009](spec.md#L107) | PARTIAL | Four auto-approval records are appended, but [risk store conditional:749](../../apps/agents/risk_assessment/agent.py#L749) and [alert narration:964](../../scripts/demo.py#L964) do not establish actual transitions. | [AUD-016-005](#aud-016-005), [AUD-016-009](#aud-016-009), [AUD-016-012](#aud-016-012) |
| [FR-010](spec.md#L108) | PARTIAL | [Communication fallback:954](../../scripts/demo.py#L954) lists six existing template files, not generated multilingual drafts. | [AUD-016-008](#aud-016-008), [AUD-016-013](#aud-016-013) |
| [FR-011](spec.md#L109) | PARTIAL | [DecisionRecord:74](../../scripts/demo.py#L74) has basic fields, but supporting signal IDs, actual decisions and escalation reasons are incomplete or incorrect. | [AUD-016-009](#aud-016-009), [AUD-016-010](#aud-016-010), [AUD-016-012](#aud-016-012) |
| [FR-012](spec.md#L110) | PARTIAL | [StageHandoff:86](../../scripts/demo.py#L86) has fields; [appended handoffs:614](../../scripts/demo.py#L614) do not prove transfers of real processing outputs. | [AUD-016-010](#aud-016-010) |
| [FR-013](spec.md#L111) | UNVERIFIED | [TestPerformance:322](../../tests/simulation/test_demo_script.py#L322) contains an elapsed <60 assertion; no result or cold-process measurement was obtained. | [AUD-016-016](#aud-016-016), [AUD-016-018](#aud-016-018), [AUD-016-020](#aud-016-020) |
| [FR-014](spec.md#L112) | PARTIAL | [Loader:236](../../scripts/demo.py#L236) rejects missing structural files and warns on missing locales, but usable schema/scenario contents and zero-locale semantics are not validated. | [AUD-016-011](#aud-016-011), [AUD-016-013](#aud-016-013), [AUD-016-019](#aud-016-019) |
| [FR-015](spec.md#L113) | PARTIAL | [Bushfire default:146](../../scripts/demo.py#L146) exists, but [new incidents:15](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L15) say flood and seed geography conflicts. | [AUD-016-014](#aud-016-014) |
| [FR-016](spec.md#L114) | PARTIAL | Three flags/configurations work in source, but [scenario tests:247](../../tests/simulation/test_demo_script.py#L247) establish labels only; hazard-consistent processing is absent. | [AUD-016-014](#aud-016-014), [AUD-016-017](#aud-016-017), [AUD-016-019](#aud-016-019) |
| [FR-017](spec.md#L115) | PARTIAL | Phase labels approximate the workflow, but [communication:964](../../scripts/demo.py#L964) neither performs its narrated approval nor demonstrates publication. | [AUD-016-005](#aud-016-005), [AUD-016-009](#aud-016-009), [AUD-016-019](#aud-016-019) |
| [SC-001](spec.md#L139) | PARTIAL | [All-pass test:57](../../tests/simulation/test_demo_script.py#L57) asserts the script's flags, which mask missing actual phases. Repeatable runtime success remains unverified. | [AUD-016-004](#aud-016-004), [AUD-016-017](#aud-016-017), [AUD-016-020](#aud-016-020) |
| [SC-002](spec.md#L140) | UNVERIFIED | No verbose elapsed assertion; [narration test:271](../../tests/simulation/test_demo_script.py#L271) checks only banner/Phase text and JSON. | [AUD-016-016](#aud-016-016), [AUD-016-020](#aud-016-020) |
| [SC-003](spec.md#L141) | UNVERIFIED | [Timing assertion:322](../../tests/simulation/test_demo_script.py#L322) is authored, not executed here, and does not time interpreter/module startup. | [AUD-016-018](#aud-016-018), [AUD-016-020](#aud-016-020) |
| [SC-004](spec.md#L142) | PARTIAL | Seven results appear on explicit phase-result paths, but [phase pass fabrication:676](../../scripts/demo.py#L676) and exception loss undermine verifiable status. | [AUD-016-004](#aud-016-004), [AUD-016-011](#aud-016-011), [AUD-016-015](#aud-016-015) |
| [SC-005](spec.md#L143) | CONFLICT | Six drafts on every success conflicts with FR-014's successful partial-language behavior; independently, [fallback:954](../../scripts/demo.py#L954) generates no content. | [AUD-016-008](#aud-016-008), [AUD-016-013](#aud-016-013), [AUD-016-019](#aud-016-019) |
| [SC-006](spec.md#L144) | PARTIAL | [Audit/handoff tests:95](../../tests/simulation/test_demo_script.py#L95) check counts/key presence rather than actual decision/transfer completeness and valid support IDs. | [AUD-016-009](#aud-016-009), [AUD-016-010](#aud-016-010), [AUD-016-017](#aud-016-017) |
| [SC-007](spec.md#L145) | UNVERIFIED | No Spec 016 Application Demo grading record found; [portfolio snapshot:1](../028-capstone-alignment/evidence/rubric-postfeature.md#L1) uses different criteria. | [AUD-016-021](#aud-016-021) |
| [SC-008](spec.md#L146) | PARTIAL | Local transport exists but [external dependency branches](../../apps/api/app/repositories/signal_repository.py#L26) remain reachable; zero-egress execution is unverified. | [AUD-016-001](#aud-016-001), [AUD-016-020](#aud-016-020) |

### Named Plan NFRs

These labels come from the plan, not invented numbered requirements.

| Obligation | Status | Evidence / gap | Follow-up |
| --- | --- | --- | --- |
| [NFR: Audit Trail](plan.md#L34) | PARTIAL | Local records and [summary counts](../../scripts/demo.py#L1026) exist, but their support IDs/decisions are not reliable. | [AUD-016-009](#aud-016-009), [AUD-016-010](#aud-016-010), [AUD-016-012](#aud-016-012) |
| [NFR: Scenario Testing](plan.md#L35) | PARTIAL | [Scenario tests](../../tests/simulation/test_demo_script.py#L244) exist, but cyclone/flood labels are not payload/route/draft assertions or execution evidence. | [AUD-016-014](#aud-016-014), [AUD-016-017](#aud-016-017), [AUD-016-020](#aud-016-020) |

### Acceptance Scenarios

USn-ASn identifiers below are report-local references to the original numbered acceptance scenarios, not added requirements.

| Scenario | Status | Expected versus observed / FR and SC trace | Follow-up |
| --- | --- | --- | --- |
| [US1-AS1](spec.md#L30) | PARTIAL | No-credential single-command full chain: FR-001/002/003/005/007, SC-001/008. [Default test](../../tests/simulation/test_demo_script.py#L57) checks fabricated phase statuses. | [AUD-016-001](#aud-016-001), [AUD-016-003](#aud-016-003), [AUD-016-004](#aud-016-004), [AUD-016-017](#aud-016-017) |
| [US1-AS2](spec.md#L31) | CONFLICT | Readiness before progress: FR-002, SC-001. [Setup](../../scripts/demo.py#L334) accepts unhealthy/unknown and skips platform readiness. | [AUD-016-003](#aud-016-003) |
| [US1-AS3](spec.md#L32) | PARTIAL | Real results for ingestion/risk/route/resource/draft: FR-005/006, SC-001/004. [Phase dispatch](../../scripts/demo.py#L1130) calls mostly acknowledgements or synthetic summaries. | [AUD-016-005](#aud-016-005), [AUD-016-006](#aud-016-006), [AUD-016-007](#aud-016-007), [AUD-016-008](#aud-016-008) |
| [US1-AS4](spec.md#L33) | PARTIAL | Identify failed agent/stage and exit nonzero: FR-007, SC-004. [500 setup test](../../tests/simulation/test_demo_script.py#L202) covers one failure form only. | [AUD-016-003](#aud-016-003), [AUD-016-004](#aud-016-004), [AUD-016-011](#aud-016-011) |
| [US2-AS1](spec.md#L47) | PARTIAL | Narrate inputs/decisions/outputs: FR-008, SC-002/004. [Narrator](../../scripts/demo.py#L181) prints labels but many outcomes are invented or omitted. | [AUD-016-016](#aud-016-016) |
| [US2-AS2](spec.md#L48) | PARTIAL | Show recommendation support and simulated review: FR-009/011, SC-006. [Risk narration](../../scripts/demo.py#L568) has fixed assessment text and incorrect supporting evidence. | [AUD-016-005](#aud-016-005), [AUD-016-009](#aud-016-009), [AUD-016-010](#aud-016-010), [AUD-016-016](#aud-016-016) |
| [US2-AS3](spec.md#L49) | PARTIAL | Six draft bodies plus targets: FR-010, SC-005. [Display loop](../../scripts/demo.py#L958) prints only locale codes and hard-coded channels. | [AUD-016-008](#aud-016-008), [AUD-016-016](#aud-016-016) |
| [US2-AS4](spec.md#L50) | UNVERIFIED | Complete in <5 minutes: FR-008, SC-002. [Verbose test](../../tests/simulation/test_demo_script.py#L271) has no time assertion/result. | [AUD-016-016](#aud-016-016), [AUD-016-020](#aud-016-020) |
| [US3-AS1](spec.md#L64) | PARTIAL | Safety-critical approval, outcome and role: FR-009/011, SC-006. [Evacuation approval](../../scripts/demo.py#L697) ignores the actual response before recording approval. | [AUD-016-009](#aud-016-009) |
| [US3-AS2](spec.md#L65) | PARTIAL | Allocation criteria/policy/quantities: FR-009/011, SC-006. [Resource result](../../scripts/demo.py#L784) contains only override_action and no allocations. | [AUD-016-007](#aud-016-007), [AUD-016-012](#aud-016-012) |
| [US3-AS3](spec.md#L66) | PARTIAL | All transfer metadata with real payloads: FR-012, SC-006. [Handoff tests](../../tests/simulation/test_demo_script.py#L115) omit timestamp/payload and actual delivery checks. | [AUD-016-010](#aud-016-010), [AUD-016-017](#aud-016-017) |
| [US3-AS4](spec.md#L67) | PARTIAL | Configured threshold and explicit reason/authority: FR-009/011, SC-006. [Escalations](../../scripts/demo.py#L727) use fixed unrelated totals and omit reason from JSON. | [AUD-016-012](#aud-016-012) |
| [US4-AS1](spec.md#L81) | PARTIAL | Default bushfire uses seed inputs: FR-004/014/015, SC-001/005. [Loader](../../scripts/demo.py#L225) loads them, but roads/templates are not used for real outputs. | [AUD-016-006](#aud-016-006), [AUD-016-008](#aud-016-008), [AUD-016-014](#aud-016-014) |
| [US4-AS2](spec.md#L82) | PARTIAL | Alternate hazard changes outputs consistently: FR-016, SC-001/005. [Cyclone test](../../tests/simulation/test_demo_script.py#L247) checks scenario label and monitoring pass only. | [AUD-016-014](#aud-016-014), [AUD-016-017](#aud-016-017), [AUD-016-019](#aud-016-019) |
| [US4-AS3](spec.md#L83) | IMPLEMENTED | Missing required structural file aborts before clients: FR-014, SC-004's failure context. [Loader exit](../../scripts/demo.py#L262) precedes [client creation](../../scripts/demo.py#L1122). Test lacks diagnostic/no-client assertions; structured reporting remains separate. | [AUD-016-011](#aud-016-011), [AUD-016-013](#aud-016-013), [AUD-016-017](#aud-016-017) |

### Edge Cases

| Edge | Status | Evidence and requirement trace | Follow-up |
| --- | --- | --- | --- |
| [EC-1: mid-pipeline failure](spec.md#L89) | PARTIAL | FR-007/SC-004: explicit failed PhaseResult skips later work, but [phase code](../../scripts/demo.py#L676) masks failures and exceptions bypass result collection. | [AUD-016-004](#aud-016-004), [AUD-016-011](#aud-016-011) |
| [EC-2: corrupt/invalid seed data](spec.md#L90) | PARTIAL | FR-014: [loader](../../scripts/demo.py#L225) parses JSON but does not enforce required usable schema or file-specific partial output. | [AUD-016-013](#aud-016-013), [AUD-016-011](#aud-016-011) |
| [EC-3: CI without TTY](spec.md#L91) | PARTIAL | FR-006/008: normal output is JSON with no input prompts; [main errors](../../scripts/demo.py#L1271) and interruption can produce no JSON. No fresh redirected CLI test. | [AUD-016-011](#aud-016-011), [AUD-016-016](#aud-016-016), [AUD-016-017](#aud-016-017) |
| [EC-4: Ctrl+C cleanup](spec.md#L92) | PARTIAL | [SIGINT handler](../../scripts/demo.py#L1251) supplies exit 130 only, without partial summary, client close, state cleanup or handler restoration. | [AUD-016-002](#aud-016-002), [AUD-016-011](#aud-016-011) |
| [EC-5: missing locale templates](spec.md#L93) | CONFLICT | [Loader warnings](../../scripts/demo.py#L251) exist, but no real partial drafts/skipped-language JSON; SC-005 still says six drafts on every successful run. | [AUD-016-008](#aud-016-008), [AUD-016-013](#aud-016-013), [AUD-016-019](#aud-016-019) |

## Original Task Coverage

Every original task has exactly one row. Checkbox state is copied verbatim; none was edited. IMPLEMENTED rows concern their bounded authored behavior, not acceptance of the full feature or execution claims.

| Original task | Original state | Status | Concrete implementation / test evidence and gap | Follow-up |
| --- | --- | --- | --- | --- |
| [T001](tasks.md#L30) | [X] | IMPLEMENTED | [Script/module:1](../../scripts/demo.py#L1), lazy dependency imports and [entrypoint:1276](../../scripts/demo.py#L1276) exist. Import placement differences are not a missing script. | [AUD-016-020](#aud-016-020) |
| [T002](tasks.md#L31) | [X] | IMPLEMENTED | [build_parser:1216](../../scripts/demo.py#L1216) defines the requested choices/defaults/flags. No actual CLI invocation in the demo tests. | [AUD-016-017](#aud-016-017) |
| [T003](tasks.md#L32) | [X] | PARTIAL | [Eight models:49](../../scripts/demo.py#L49) exist, but required enums/bounds/invariants are absent; [serializer fixture:395](../../tests/simulation/test_demo_script.py#L395) uses an invalid ID. | [AUD-016-015](#aud-016-015) |
| [T004](tasks.md#L42) | [X] | PARTIAL | [load_seed_data:225](../../scripts/demo.py#L225) loads nine files and filters hazard; no required top-level-key or nonempty-match validation. | [AUD-016-013](#aud-016-013), [AUD-016-019](#aud-016-019) |
| [T005](tasks.md#L43) | [X] | CONFLICT | [create_clients:295](../../scripts/demo.py#L295) creates six clients and an explicit resource agent; default factories for other agents do not initialize processing or guarantee offline operation as R-001 claims. | [AUD-016-001](#aud-016-001), [AUD-016-002](#aud-016-002), [AUD-016-003](#aud-016-003), [AUD-016-019](#aud-016-019) |
| [T006](tasks.md#L44) | [X] | PARTIAL | [serialize_output:1074](../../scripts/demo.py#L1074) uses model_dump JSON/ISO timestamps and correct destination, but accepts nonconforming models and lacks controlled output-error behavior. | [AUD-016-011](#aud-016-011), [AUD-016-015](#aud-016-015) |
| [T007](tasks.md#L45) | [X] | PARTIAL | [Loop:1174](../../scripts/demo.py#L1174) skips after explicit failed results; exceptions and false-positive phase results violate fail-fast/output guarantees. | [AUD-016-004](#aud-016-004), [AUD-016-011](#aud-016-011) |
| [T008](tasks.md#L46) | [X] | PARTIAL | [main:1248](../../scripts/demo.py#L1248) handles SIGINT/KeyboardInterrupt with code 130 only; partial DemoRun and cleanup are absent. | [AUD-016-002](#aud-016-002), [AUD-016-011](#aud-016-011) |
| [T009](tasks.md#L60) | [X] | CONFLICT | [Setup:334](../../scripts/demo.py#L334) counts unhealthy/unknown as healthy and globally resets state, contrary to the task's unhealthy rejection and full spec readiness. | [AUD-016-002](#aud-016-002), [AUD-016-003](#aud-016-003), [AUD-016-019](#aud-016-019) |
| [T010](tasks.md#L61) | [X] | PARTIAL | [Monitoring:408](../../scripts/demo.py#L408) posts a dict rather than validated SimulatedSignal, ignores association/dashboard failure, and forces positive association count. | [AUD-016-004](#aud-016-004), [AUD-016-010](#aud-016-010), [AUD-016-014](#aud-016-014), [AUD-016-015](#aud-016-015) |
| [T011](tasks.md#L62) | [X] | CONFLICT | [Risk:527](../../scripts/demo.py#L527) implements the seeding shortcut but not genuine analysis or mutation of the seeded recommendation via the independent store-less override. | [AUD-016-005](#aud-016-005), [AUD-016-019](#aud-016-019) |
| [T012](tasks.md#L63) | [X] | PARTIAL | [Evacuation:650](../../scripts/demo.py#L650) omits geometry/population input, treats 503 as plan creation, and ignores override status. | [AUD-016-004](#aud-016-004), [AUD-016-006](#aud-016-006) |
| [T013](tasks.md#L64) | [X] | PARTIAL | [Resource phase:784](../../scripts/demo.py#L784) invokes override, but [handler:381](../../apps/agents/resource_allocation/agent.py#L381) only audits a fixed ID and does not approve an actual allocation plan. | [AUD-016-007](#aud-016-007), [AUD-016-009](#aud-016-009) |
| [T014](tasks.md#L65) | [X] | PARTIAL | [Communication:897](../../scripts/demo.py#L897) posts a handoff but has no pipeline; reports fallback language keys and safety true without drafts. | [AUD-016-004](#aud-016-004), [AUD-016-008](#aud-016-008) |
| [T015](tasks.md#L66) | [X] | IMPLEMENTED | [Summary:1026](../../scripts/demo.py#L1026) counts decisions, handoffs and languages in the supplied run. Counting does not prove underlying correctness. | [AUD-016-010](#aud-016-010) |
| [T016](tasks.md#L67) | [X] | PARTIAL | [Dispatch:1130](../../scripts/demo.py#L1130) wires seven functions in order and passes data; failure exceptions and disconnected inner work prevent full end-to-end orchestration. | [AUD-016-004](#aud-016-004), [AUD-016-011](#aud-016-011) |
| [T017](tasks.md#L83) | [X] | PARTIAL | [Risk decision:600](../../scripts/demo.py#L600) has required labels but cites a signal that ingestion did not create and no verified store approval. | [AUD-016-005](#aud-016-005), [AUD-016-009](#aud-016-009), [AUD-016-010](#aud-016-010) |
| [T018](tasks.md#L84) | [X] | PARTIAL | [Evacuation decision:714](../../scripts/demo.py#L714) is appended after an unchecked override for an uncreated plan. | [AUD-016-006](#aud-016-006), [AUD-016-009](#aud-016-009) |
| [T019](tasks.md#L85) | [X] | PARTIAL | [Resource decision:828](../../scripts/demo.py#L828) records a policy and approval without real assignments or a plan transition. | [AUD-016-007](#aud-016-007), [AUD-016-009](#aud-016-009) |
| [T020](tasks.md#L86) | [X] | PARTIAL | [Alert decision:976](../../scripts/demo.py#L976) records approval of a fabricated alert ID after failed generation. | [AUD-016-008](#aud-016-008), [AUD-016-009](#aud-016-009), [AUD-016-010](#aud-016-010) |
| [T021](tasks.md#L87) | [X] | PARTIAL | [First handoff:614](../../scripts/demo.py#L614) and three later records use fixed IDs/confidences, not observed accepted transfers. | [AUD-016-010](#aud-016-010) |
| [T022](tasks.md#L88) | [X] | PARTIAL | [Evacuation threshold:727](../../scripts/demo.py#L727) and [resource threshold:841](../../scripts/demo.py#L841) are hard-coded proxies; JSON lacks reason/threshold. | [AUD-016-012](#aud-016-012) |
| [T023](tasks.md#L89) | [X] | IMPLEMENTED | [Summary:1033](../../scripts/demo.py#L1033) includes total_decisions, total_handoffs and total_escalations before serialization. Source lists remain semantically unreliable. | [AUD-016-010](#aud-016-010), [AUD-016-012](#aud-016-012) |
| [T024](tasks.md#L103) | [X] | IMPLEMENTED | [Narrator:181](../../scripts/demo.py#L181) implements headers, phase/detail/success/warning methods with stderr/no-op mode; [helper tests:363](../../tests/simulation/test_demo_script.py#L363) inspect text. | [AUD-016-016](#aud-016-016) |
| [T025](tasks.md#L104) | [X] | PARTIAL | Narration exists in [setup:334](../../scripts/demo.py#L334), [monitoring:408](../../scripts/demo.py#L408) and [risk:527](../../scripts/demo.py#L527), but it represents unavailable processing as healthy/generated. | [AUD-016-003](#aud-016-003), [AUD-016-016](#aud-016-016) |
| [T026](tasks.md#L105) | [X] | PARTIAL | [Risk gate text:570](../../scripts/demo.py#L570) and other gates exist, but narration lacks reliable support/transition evidence. | [AUD-016-009](#aud-016-009), [AUD-016-010](#aud-016-010), [AUD-016-016](#aud-016-016) |
| [T027](tasks.md#L106) | [X] | PARTIAL | [Display:958](../../scripts/demo.py#L958) lists language/channel names, not the draft alerts required by US2-AS3. | [AUD-016-008](#aud-016-008), [AUD-016-016](#aud-016-016) |
| [T028](tasks.md#L107) | [X] | PARTIAL | [Banner:1039](../../scripts/demo.py#L1039) prints counters but unconditional all-pass wording and a pre-final duration, not a verified complete-run summary. | [AUD-016-010](#aud-016-010), [AUD-016-016](#aud-016-016) |
| [T029](tasks.md#L108) | [X] | PARTIAL | [Narrator:187](../../scripts/demo.py#L187) sleeps 0.3 seconds only when verbose, but pacing is not configurable and the <5-minute bound is unmeasured. | [AUD-016-016](#aud-016-016), [AUD-016-020](#aud-016-020) |
| [T030](tasks.md#L122) | [X] | IMPLEMENTED | [SCENARIO_CONFIGS:146](../../scripts/demo.py#L146) contains all requested types/categories/locations/severity/prefix fields. Their geographic inconsistency is a separate requirement defect. | [AUD-016-014](#aud-016-014) |
| [T031](tasks.md#L123) | [X] | IMPLEMENTED | [run_pipeline:1113](../../scripts/demo.py#L1113) resolves scenario and passes it to loading/monitoring; [signal payload:424](../../scripts/demo.py#L424) uses category/location/severity. | [AUD-016-014](#aud-016-014), [AUD-016-017](#aud-016-017) |
| [T032](tasks.md#L124) | [X] | PARTIAL | Header/hazard wording changes, and the prefix enters the payload, but [monitoring narration:416](../../scripts/demo.py#L416) never narrates that prefix or coherent downstream scenario evidence. | [AUD-016-014](#aud-016-014), [AUD-016-016](#aud-016-016) |
| [T033](tasks.md#L125) | [X] | IMPLEMENTED | [Structural missing-file check:236](../../scripts/demo.py#L236) names paths and aborts before clients. Missing language files follow amended FR-014 rather than becoming structural failures. | [AUD-016-011](#aud-016-011), [AUD-016-013](#aud-016-013) |
| [T034](tasks.md#L135) | [X] | PARTIAL | [TestFullPipeline:54](../../tests/simulation/test_demo_script.py#L54) covers requested root keys/counts/statuses, but not complete output-schema semantics or actual processing. | [AUD-016-015](#aud-016-015), [AUD-016-017](#aud-016-017) |
| [T035](tasks.md#L136) | [X] | PARTIAL | [Failure tests:189](../../tests/simulation/test_demo_script.py#L189) cover missing directory/SystemExit and HTTP-500 setup, but not specific missing-file text, no-client construction, semantic health, or later-stage failures. | [AUD-016-003](#aud-016-003), [AUD-016-004](#aud-016-004), [AUD-016-011](#aud-016-011), [AUD-016-017](#aud-016-017) |
| [T036](tasks.md#L137) | [X] | PARTIAL | [Scenario/mode tests:244](../../tests/simulation/test_demo_script.py#L244) cover labels, banner/Phase text and file output, but the cyclone test does not assert the signal type or CLI flag parsing. | [AUD-016-014](#aud-016-014), [AUD-016-016](#aud-016-016), [AUD-016-017](#aud-016-017) |
| [T037](tasks.md#L138) | [X] | IMPLEMENTED | [Timing test:322](../../tests/simulation/test_demo_script.py#L322) asserts exit 0 and elapsed <60 for run_pipeline. Authored assertion only; no result or cold-start proof. | [AUD-016-020](#aud-016-020) |
| [T038](tasks.md#L139) | [X] | UNVERIFIED | [Quickstart commands:15](quickstart.md#L15) and examples exist, but no local revision-bound execution receipt was located. | [AUD-016-020](#aud-016-020) |
| [T039](tasks.md#L140) | [X] | MISSING | Scoped README/docs search found only [manual walkthrough link:286](../../README.md#L286); no automated command plus Spec 016 quickstart entry. | [AUD-016-019](#aud-016-019) |

## Amendments, Assumptions, and Models

### Clarifications and Later Additions

| Item | Status | Evidence / disposition | Follow-up |
| --- | --- | --- | --- |
| [CL-01: seven phases](spec.md#L12) | IMPLEMENTED | [PHASES:1092](../../scripts/demo.py#L1092) has seven orchestration stages, five agent names and two orchestrator stages. Semantic completion remains separate. | [AUD-016-015](#aud-016-015) |
| [CL-02: JSON stdout or output file](spec.md#L13) | PARTIAL | [Serializer:1074](../../scripts/demo.py#L1074) implements normal destinations but error/interrupt paths bypass it. | [AUD-016-011](#aud-016-011) |
| [CL-03: only CI/verbose, no prompts](spec.md#L14) | IMPLEMENTED | [Parser:1216](../../scripts/demo.py#L1216) and [Narrator:181](../../scripts/demo.py#L181) expose the two modes; no interactive input in the script. Budgets and valid approvals are separate gaps. | [AUD-016-009](#aud-016-009), [AUD-016-016](#aud-016-016) |
| [CL-04: Python CLI location/flags](spec.md#L15) | IMPLEMENTED | [Entrypoint:1243](../../scripts/demo.py#L1243) and flag definitions match; clean-install execution unverified. | [AUD-016-017](#aud-016-017), [AUD-016-019](#aud-016-019) |
| [CL-05: fail-fast](spec.md#L16) | PARTIAL | [Loop:1192](../../scripts/demo.py#L1192) responds only to returned results, several of which hide failures. | [AUD-016-004](#aud-016-004), [AUD-016-011](#aud-016-011) |
| [PER-040](spec.md#L153) | UNVERIFIED | Authored AU persona cross-reference says validated but supplies no Spec 016-scoped validator identity/date/scenario receipt; [persona contract](../027-spec-hardening/contracts/persona-profile.md#L5) requires attributable evidence. This is not a claim that upstream profiles do not exist. | [AUD-016-021](#aud-016-021) |
| [PER-041](spec.md#L154) | UNVERIFIED | Technical-actor catalogue cross-reference is authored, but actor consultation/validation for this demo is not evidenced by the label. No delegation was undertaken to create retrospective evidence. | [AUD-016-021](#aud-016-021) |
| [PER-042](spec.md#L155) | IMPLEMENTED | Explicit PH/JP/BD placeholder and preconditions are authored; [D-009 decision](../028-capstone-alignment/evidence/decision-record.md#L12) retains deferral. No country validation is claimed. | [AUD-016-021](#aud-016-021) preserves deferral |
| [HYP-014](spec.md#L161) | PARTIAL | Hypothesis/falsification text exists. Named doubled-prefix stub is MISSING after the scoped search; per-spec consultation and measured uplift are UNVERIFIED. [Portfolio comparator](../028-capstone-alignment/evidence/rubric-postfeature.md#L24) was found under its actual name, not mistaken for missing evidence. | [AUD-016-021](#aud-016-021) |
| [SCP-044](spec.md#L169) | IMPLEMENTED | Country variants remain explicitly deferred behind D-009, data-sharing and responsible-owner gates. No request here authorizes implementing those variants. | [AUD-016-021](#aud-016-021) preserves boundary |
| [SCP-045](spec.md#L170) | IMPLEMENTED | Spec does not amend constitutional non-negotiables. Current offline/approval defects must be addressed without relaxing them; [constitution](../../.specify/memory/constitution.md#L253) remains authoritative. | [AUD-016-001](#aud-016-001), [AUD-016-009](#aud-016-009), [AUD-016-019](#aud-016-019) |
| [SCP-046](spec.md#L171) | IMPLEMENTED | Explicit deferrals to recovery/warning authorities are present. Fixing demo wiring is not permission to claim ownership of those capabilities. | [AUD-016-019](#aud-016-019), [AUD-016-021](#aud-016-021) |
| [SCP-047](spec.md#L172) | IMPLEMENTED | Meta marker is present and points to the canonical declaration; awkward historical wording is not absence of the required bullet. | [AUD-016-019](#aud-016-019) |
| [Canonical meta declaration](spec.md#L165) | IMPLEMENTED | Exactly one declaration names enabled specs; satisfies [meta contract:12](../028-capstone-alignment/contracts/meta-spec-flag.contract.md#L12). [Ledger exclusion](../shared/feature-value-ledger.md#L30) is not demo retirement or a runtime pass. | None |

### Original Assumptions

| Assumption | Status | Assessment | Follow-up |
| --- | --- | --- | --- |
| [A1: in-process factories](spec.md#L128) | PARTIAL | ASGI factories exist, but defaults do not populate monitoring/evacuation/communication processing; [factory wiring](../../scripts/demo.py#L295). | [AUD-016-001](#aud-016-001), [AUD-016-003](#aud-016-003) |
| [A2: template fallback adequate/no live LLM](spec.md#L129) | PARTIAL | Real fallback machinery exists, but fixed demo results do not execute it and ambient dependencies are not isolated; [LLM mixin](../../apps/agents/common/llm_mixin.py#L65). | [AUD-016-001](#aud-016-001), [AUD-016-005](#aud-016-005), [AUD-016-008](#aud-016-008) |
| [A3: six templates, consistent schema](spec.md#L130) | PARTIAL | Six files exist and sampled English definitions have fields; [loader](../../scripts/demo.py#L225) does not validate per-language schema/usable content. Linguistic approval not established. | [AUD-016-008](#aud-016-008), [AUD-016-013](#aud-016-013) |
| [A4: seed data sufficient for bushfire](spec.md#L131) | PARTIAL | Source data exists but ACT/FNQ/Sydney mismatch and disconnected consumers prevent a sufficiency conclusion. | [AUD-016-006](#aud-016-006), [AUD-016-007](#aud-016-007), [AUD-016-014](#aud-016-014) |
| [A5: deterministic simulated approvals](spec.md#L132) | PARTIAL | No prompts and auto-approval labels exist, but actual entity transitions are not verified. | [AUD-016-009](#aud-016-009), [AUD-016-010](#aud-016-010) |
| [A6: cyclone/flood stretch goals](spec.md#L133) | CONFLICT | Stretch-goal language disagrees with [FR-016](spec.md#L114), closed CLI choices and checked scenario tasks. | [AUD-016-014](#aud-016-014), [AUD-016-019](#aud-016-019) |

### Model and Entity Obligations

The spec's six entities and the data-model's two additional containers are covered together; similar names are not mistaken for missing files.

| Model / entity | Status | Evidence / gap | Follow-up |
| --- | --- | --- | --- |
| [DemoRun](data-model.md#L12) | PARTIAL | [Model:127](../../scripts/demo.py#L127) starts as pass and permits empty phases/invalid ID/scenario; lacks required terminal invariants and partial-startup representation. | [AUD-016-011](#aud-016-011), [AUD-016-015](#aud-016-015) |
| [PhaseResult / Pipeline Stage](data-model.md#L39) | PARTIAL | [Model:49](../../scripts/demo.py#L49) has fields but no phase/order/error relation or explicit consumed/produced evidence contract. | [AUD-016-015](#aud-016-015) |
| [SimulatedSignal](data-model.md#L74) | PARTIAL | [Model:62](../../scripts/demo.py#L62) is defined but unused in monitoring; confidence/GeoJSON constraints absent. | [AUD-016-013](#aud-016-013), [AUD-016-015](#aud-016-015) |
| [DecisionRecord](data-model.md#L97) | PARTIAL | [Model:74](../../scripts/demo.py#L74) lacks outcome/agent/support constraints and structured escalation explanation. | [AUD-016-010](#aud-016-010), [AUD-016-012](#aud-016-012), [AUD-016-015](#aud-016-015) |
| [StageHandoff](data-model.md#L120) | PARTIAL | [Model:86](../../scripts/demo.py#L86) lacks confidence/distinct-agent/ID constraints and is not built from actual transfer receipts. | [AUD-016-010](#aud-016-010), [AUD-016-015](#aud-016-015) |
| [AlertSummary / Alert Draft](data-model.md#L142) | PARTIAL | [Model:97](../../scripts/demo.py#L97) is an aggregate, not the content/body/approval-mode evidence required by [Alert Draft entity](spec.md#L123). | [AUD-016-008](#aud-016-008), [AUD-016-015](#aud-016-015) |
| [ScenarioConfig](data-model.md#L159) | PARTIAL | [Model:106](../../scripts/demo.py#L106) has fields/configs but no scenario enum or geometry validation. | [AUD-016-014](#aud-016-014), [AUD-016-015](#aud-016-015) |
| [SeedData](data-model.md#L185) | PARTIAL | [Model:117](../../scripts/demo.py#L117) permits empty structures and zero template matches. The all-six model rule also conflicts with amended degradation. | [AUD-016-013](#aud-016-013), [AUD-016-019](#aud-016-019) |

## Research and Review Evidence

### Research Decisions

| Decision | Status | Source assessment | Follow-up |
| --- | --- | --- | --- |
| [R-001](research.md#L6) | CONFLICT | Existing [benchmark factories](../../tests/benchmark/conftest.py#L27) prove local HTTP instantiation, not default-agent processing or absence of import-time I/O. | [AUD-016-001](#aud-016-001), [AUD-016-003](#aud-016-003), [AUD-016-019](#aud-016-019) |
| [R-002](research.md#L45) | CONFLICT | Dual-client phases are wired, but deliberate recommendation seeding/override acknowledgements disagree with actual analysis/routing/allocation/publication promises. | [AUD-016-005](#aud-016-005), [AUD-016-006](#aud-016-006), [AUD-016-007](#aud-016-007), [AUD-016-009](#aud-016-009), [AUD-016-019](#aud-016-019) |
| [R-003](research.md#L91) | CONFLICT | Calls nine physical files plus a scenario match "10 files"; says top-level validation/all required locales, unlike [loader](../../scripts/demo.py#L225) and amended FR-014. | [AUD-016-013](#aud-016-013), [AUD-016-019](#aud-016-019) |
| [R-004](research.md#L127) | CONFLICT | First-failure circuit opening is inconsistent with [default threshold three](../../apps/agents/common/llm_config.py#L57). Missing pipelines do not execute real template fallback, and current configuration also includes Foundry. | [AUD-016-001](#aud-016-001), [AUD-016-008](#aud-016-008), [AUD-016-019](#aud-016-019) |
| [R-005](research.md#L164) | PARTIAL | Summary-only JSON exists, but counts/flags do not fulfill verifiable consumed-input/produced-output and alert-content obligations. | [AUD-016-010](#aud-016-010), [AUD-016-015](#aud-016-015), [AUD-016-019](#aud-016-019) |
| [R-006](research.md#L246) | PARTIAL | Normal stdout/stderr separation and no prompts exist. Research default 0.5-second pacing differs from the task/code's fixed 0.3; limits are unmeasured. | [AUD-016-016](#aud-016-016), [AUD-016-019](#aud-016-019), [AUD-016-020](#aud-016-020) |
| [R-007](research.md#L283) | PARTIAL | Explicit-result skipping exists; unhealthy acceptance, ignored errors and no partial interrupt record violate the chosen policy. | [AUD-016-003](#aud-016-003), [AUD-016-004](#aud-016-004), [AUD-016-011](#aud-016-011) |
| [R-008](research.md#L313) | PARTIAL | Hazard flags/filtering exist; matching templates are unused and geography/incident semantics disagree. Stretch-goal scope unresolved. | [AUD-016-014](#aud-016-014), [AUD-016-019](#aud-016-019) |

### Plan Gate Claims

All 14 entries below are authored **PASS** claims. They do not prove a review ran, a human signed off, a benchmark passed, or a deployment exists. The two overall ALL PASS banners inherit the unresolved rows. The current constitution's principle names/numbering differ from historical plan shorthand; the constitution is not rewritten by this review.

| Gate claim | Status | Evidence / limitation | Follow-up |
| --- | --- | --- | --- |
| [PG-01: initial Life Safety First](plan.md#L28) | PARTIAL | Error masking and invented approval/safety results contradict the explanation. | [AUD-016-004](#aud-016-004), [AUD-016-008](#aud-016-008), [AUD-016-009](#aud-016-009) |
| [PG-02: initial Multi-Agent Coordination](plan.md#L29) | PARTIAL | Five clients/labels are not five connected processing agents or delivered handoffs. | [AUD-016-003](#aud-016-003), [AUD-016-010](#aud-016-010) |
| [PG-03: initial Data Trust and Provenance](plan.md#L30) | PARTIAL | Simulation provenance is authored in the envelope, but support IDs and validation are incomplete. | [AUD-016-010](#aud-016-010), [AUD-016-013](#aud-016-013) |
| [PG-04: initial Privacy and Security](plan.md#L31) | UNVERIFIED | Synthetic intent is documented; no exhaustive PII validation or no-egress proof. Ambient telemetry/repositories defeat an unconditional in-memory assertion. | [AUD-016-001](#aud-016-001), [AUD-016-002](#aud-016-002), [AUD-016-020](#aud-016-020) |
| [PG-05: initial Multilingual Communication](plan.md#L32) | PARTIAL | Six filenames are not generated/validated drafts. | [AUD-016-008](#aud-016-008) |
| [PG-06: initial Cloud Platform](plan.md#L33) | PARTIAL | Local intent is bounded appropriately, but zero external dependencies is not enforced. No cloud deployment claim is evaluated. | [AUD-016-001](#aud-016-001) |
| [PG-07: initial NFR Audit Trail](plan.md#L34) | PARTIAL | Records are appended but not reliably linked to actual decisions/transfers. | [AUD-016-009](#aud-016-009), [AUD-016-010](#aud-016-010) |
| [PG-08: initial NFR Scenario Testing](plan.md#L35) | PARTIAL | Test source exists with scenario labels but no complete semantic/measurement evidence. | [AUD-016-014](#aud-016-014), [AUD-016-017](#aud-016-017), [AUD-016-020](#aud-016-020) |
| [PG-09: initial Quality Gates](plan.md#L36) | PARTIAL | No explicit CI selection of the demo; phase pass flags are unreliable. | [AUD-016-004](#aud-016-004), [AUD-016-018](#aud-016-018) |
| [PG-10: post-design Life Safety First](plan.md#L44) | PARTIAL | Named ApprovalGate behavior is represented by DecisionRecord/narration, not a validated state transition. Renaming alone is not the defect. | [AUD-016-009](#aud-016-009), [AUD-016-019](#aud-016-019) |
| [PG-11: post-design Coordination](plan.md#L45) | PARTIAL | StageHandoff container exists but does not establish transfer completeness. | [AUD-016-010](#aud-016-010) |
| [PG-12: post-design Provenance](plan.md#L46) | PARTIAL | SimulatedSignal is unused and loader lacks promised SeedValidator-equivalent schema checks. | [AUD-016-010](#aud-016-010), [AUD-016-013](#aud-016-013), [AUD-016-015](#aud-016-015) |
| [PG-13: post-design Multilingual](plan.md#L47) | PARTIAL | AlertSummary is present but does not retain draft content, actual safety status or approval mode. | [AUD-016-008](#aud-016-008), [AUD-016-015](#aud-016-015) |
| [PG-14: post-design Audit Trail](plan.md#L48) | PARTIAL | Ordered append operations exist, but model lists are mutable and entries lack verified decision provenance. | [AUD-016-009](#aud-016-009), [AUD-016-010](#aud-016-010), [AUD-016-015](#aud-016-015) |

### Specification Quality Checklist

SQ labels identify the 16 original unnumbered entries by exact line. Every original state is `[x]`; states remain unchanged. Status assesses the statement, not whether a checklist review actually happened.

| Checklist item | Original state | Status | Evidence / disposition | Follow-up |
| --- | --- | --- | --- | --- |
| [SQ-01: no implementation details](checklists/requirements.md#L9) | [x] | CONFLICT | [FR-001/002](spec.md#L99) explicitly name Python, argparse, app path and TestClients. | [AUD-016-019](#aud-016-019) |
| [SQ-02: user/business value](checklists/requirements.md#L10) | [x] | IMPLEMENTED | [Four user stories](spec.md#L18) identify developer/presenter/governance/tester value. | None |
| [SQ-03: nontechnical stakeholders](checklists/requirements.md#L11) | [x] | PARTIAL | Stories are accessible; implementation-specific FRs/CLI terms remain. | [AUD-016-019](#aud-016-019) |
| [SQ-04: mandatory sections](checklists/requirements.md#L12) | [x] | IMPLEMENTED | User Scenarios, Requirements and Success Criteria are present in the full spec. | None |
| [SQ-05: no clarification markers](checklists/requirements.md#L16) | [x] | IMPLEMENTED | No unresolved clarification marker is present in the spec; that does not imply absence of conflicts. | [AUD-016-019](#aud-016-019) |
| [SQ-06: testable/unambiguous](checklists/requirements.md#L17) | [x] | PARTIAL | Thresholds, full-pipeline meaning and degraded success need explicit decisions. | [AUD-016-012](#aud-016-012), [AUD-016-019](#aud-016-019) |
| [SQ-07: measurable SCs](checklists/requirements.md#L18) | [x] | PARTIAL | Time/count/grade targets exist; measurement baseline, cold timing and per-run scope are incomplete. | [AUD-016-020](#aud-016-020), [AUD-016-021](#aud-016-021) |
| [SQ-08: technology-agnostic SCs](checklists/requirements.md#L19) | [x] | CONFLICT | [SC-008](spec.md#L146) explicitly names Azure credentials and network/database dependencies. | [AUD-016-019](#aud-016-019) |
| [SQ-09: acceptance scenarios defined](checklists/requirements.md#L20) | [x] | IMPLEMENTED | All 15 original numbered scenarios are authored; their implementation statuses differ. | None |
| [SQ-10: edge cases identified](checklists/requirements.md#L21) | [x] | IMPLEMENTED | Five explicit edge cases are authored at [spec:87](spec.md#L87). | None |
| [SQ-11: clearly bounded scope](checklists/requirements.md#L22) | [x] | PARTIAL | Later scope deferrals are clear, but stretch scenarios and drafting/publication remain inconsistent. | [AUD-016-019](#aud-016-019) |
| [SQ-12: dependencies/assumptions](checklists/requirements.md#L23) | [x] | PARTIAL | Six assumptions and design dependencies exist, but current default factories and package requirements contradict parts. | [AUD-016-001](#aud-016-001), [AUD-016-019](#aud-016-019) |
| [SQ-13: all FR acceptance criteria clear](checklists/requirements.md#L27) | [x] | PARTIAL | No complete phase-output/readiness/degradation policy; this report supplies traceability, not new accepted requirements. | [AUD-016-015](#aud-016-015), [AUD-016-019](#aud-016-019) |
| [SQ-14: primary flows covered](checklists/requirements.md#L28) | [x] | IMPLEMENTED | The four stories cover smoke, presentation, governance and scenario configuration. | None |
| [SQ-15: measurable outcomes met](checklists/requirements.md#L29) | [x] | UNVERIFIED | Authored tests/examples/checks do not prove SC execution or grade outcomes; source also shows contradictions. | [AUD-016-020](#aud-016-020), [AUD-016-021](#aud-016-021) |
| [SQ-16: no implementation details leak](checklists/requirements.md#L30) | [x] | CONFLICT | Same direct counterexample as SQ-01; the checklist's closing "all pass" is not current proof. | [AUD-016-019](#aud-016-019) |

### Comprehensive Checklist Coverage

All **109 original checkboxes remain `[ ]`**. These are questions about requirement quality, not 109 extra implemented product features. IMPLEMENTED means the requested definition is found in the packet/source cited; it does not close the original checkbox or prove review execution. Undefined optional concerns require an explicit scope decision under AUD-016-019, not unilateral expansion of the feature.

| Original item | Original state | Status | Definition/evidence assessment | Follow-up |
| --- | --- | --- | --- | --- |
| [CHK001](checklists/comprehensive.md#L13) | [ ] | PARTIAL | [Tasks:60](tasks.md#L60) name phase actions, but real processing entry/exit success criteria remain incomplete. | [AUD-016-004](#aud-016-004), [AUD-016-015](#aud-016-015) |
| [CHK002](checklists/comprehensive.md#L14) | [ ] | PARTIAL | [Factory:295](../../scripts/demo.py#L295) has a sequence but no specified dependency/readiness contract. | [AUD-016-003](#aud-016-003), [AUD-016-019](#aud-016-019) |
| [CHK003](checklists/comprehensive.md#L15) | [ ] | PARTIAL | [R-007:294](research.md#L294) defines health statuses but not bounded checks; code contradicts rejection. | [AUD-016-003](#aud-016-003) |
| [CHK004](checklists/comprehensive.md#L16) | [ ] | IMPLEMENTED | [CLI exit-code table](contracts/cli-interface.md#L20) defines 0/1/2/130. | [AUD-016-011](#aud-016-011) for behavior |
| [CHK005](checklists/comprehensive.md#L17) | [ ] | IMPLEMENTED | [Output contract:198](contracts/output-schema.md#L198) supplies field/type tables and examples. | [AUD-016-015](#aud-016-015) for enforcement |
| [CHK006](checklists/comprehensive.md#L18) | [ ] | IMPLEMENTED | [Decision schema:230](contracts/output-schema.md#L230) supplies exact fields. | [AUD-016-010](#aud-016-010) |
| [CHK007](checklists/comprehensive.md#L19) | [ ] | PARTIAL | [T021](tasks.md#L87) enumerates four summaries/confidences, not full per-transfer payload or consumer mappings. | [AUD-016-010](#aud-016-010), [AUD-016-015](#aud-016-015) |
| [CHK008](checklists/comprehensive.md#L20) | [ ] | PARTIAL | [T009](tasks.md#L60) omits platform readiness and initialization dependencies required by FR-002. | [AUD-016-003](#aud-016-003), [AUD-016-019](#aud-016-019) |
| [CHK009](checklists/comprehensive.md#L21) | [ ] | IMPLEMENTED | [T015](tasks.md#L66) and [T023](tasks.md#L89) define aggregation counts. | [AUD-016-010](#aud-016-010) for truthfulness |
| [CHK010](checklists/comprehensive.md#L22) | [ ] | IMPLEMENTED | [CLI narration contract:62](contracts/cli-interface.md#L62) defines labelled/timestamped layout. | [AUD-016-016](#aud-016-016) |
| [CHK011](checklists/comprehensive.md#L23) | [ ] | PARTIAL | [Argparse parser:1216](../../scripts/demo.py#L1216) supplies help, but explicit help acceptance behavior is not documented/tested. | [AUD-016-017](#aud-016-017), [AUD-016-019](#aud-016-019) |
| [CHK012](checklists/comprehensive.md#L24) | [ ] | PARTIAL | Argparse error/code 2 is specified; required diagnostic/stream assertions are not. | [AUD-016-011](#aud-016-011), [AUD-016-019](#aud-016-019) |
| [CHK013](checklists/comprehensive.md#L25) | [ ] | IMPLEMENTED | [SimulatedSignal definition:74](data-model.md#L74) specifies envelope fields and validation rules. | [AUD-016-015](#aud-016-015) |
| [CHK014](checklists/comprehensive.md#L26) | [ ] | IMPLEMENTED | [FR-005](spec.md#L103) explicitly chooses a minimum of one; an additional fixed count is not necessary. | [AUD-016-004](#aud-016-004) |
| [CHK015](checklists/comprehensive.md#L27) | [ ] | IMPLEMENTED | [T004](tasks.md#L42) enumerates nine physical files; research's ten-file count still needs correction. | [AUD-016-019](#aud-016-019) |
| [CHK016](checklists/comprehensive.md#L28) | [ ] | IMPLEMENTED | [T027](tasks.md#L106) and [output example](contracts/output-schema.md#L6) name sms/push/broadcast. | [AUD-016-008](#aud-016-008), [AUD-016-009](#aud-016-009) |
| [CHK017](checklists/comprehensive.md#L29) | [ ] | PARTIAL | [R-001 factory table](research.md#L11) documents interface assumptions that are not current processing guarantees. | [AUD-016-001](#aud-016-001), [AUD-016-019](#aud-016-019) |
| [CHK018](checklists/comprehensive.md#L33) | [ ] | IMPLEMENTED | [Quickstart technical section](quickstart.md#L61) defines in-process ASGI/TestClient, not subprocess servers. | [AUD-016-002](#aud-016-002) for lifecycle |
| [CHK019](checklists/comprehensive.md#L34) | [ ] | CONFLICT | [R-007 health policy](research.md#L294) disagrees with [setup's permissive branch](../../scripts/demo.py#L356). | [AUD-016-003](#aud-016-003), [AUD-016-019](#aud-016-019) |
| [CHK020](checklists/comprehensive.md#L35) | [ ] | PARTIAL | [Scenario locations](data-model.md#L159) are given, but realism has no coherent geographic acceptance fixture. | [AUD-016-014](#aud-016-014), [AUD-016-019](#aud-016-019) |
| [CHK021](checklists/comprehensive.md#L36) | [ ] | IMPLEMENTED | [US2-AS1/2/3](spec.md#L47) and [narration contract](contracts/cli-interface.md#L62) specify content. | [AUD-016-016](#aud-016-016) |
| [CHK022](checklists/comprehensive.md#L37) | [ ] | PARTIAL | [Approval assumption](spec.md#L132) defines auto-approve intent, but actual state/role verification and publication boundaries are incomplete. | [AUD-016-009](#aud-016-009), [AUD-016-019](#aud-016-019) |
| [CHK023](checklists/comprehensive.md#L38) | [ ] | IMPLEMENTED | [StageHandoff definition](data-model.md#L120) bounds confidence to [0,1]. | [AUD-016-015](#aud-016-015) |
| [CHK024](checklists/comprehensive.md#L39) | [ ] | PARTIAL | [FR-009](spec.md#L107) gives examples and T017-T020 name four gates, but threshold/publication semantics remain incomplete. | [AUD-016-009](#aud-016-009), [AUD-016-012](#aud-016-012), [AUD-016-019](#aud-016-019) |
| [CHK025](checklists/comprehensive.md#L40) | [ ] | PARTIAL | [T022](tasks.md#L88) gives an example, not a configured resource-allocation threshold. | [AUD-016-012](#aud-016-012) |
| [CHK026](checklists/comprehensive.md#L41) | [ ] | PARTIAL | [Hard-coded branches](../../scripts/demo.py#L727) have no policy configuration format/default contract. | [AUD-016-012](#aud-016-012), [AUD-016-019](#aud-016-019) |
| [CHK027](checklists/comprehensive.md#L42) | [ ] | PARTIAL | >1000 affected people is an example in [T022](tasks.md#L88); code measures facility capacity >100 instead. | [AUD-016-012](#aud-016-012) |
| [CHK028](checklists/comprehensive.md#L43) | [ ] | IMPLEMENTED | [DecisionRecord definition](data-model.md#L97) specifies supporting entity IDs. | [AUD-016-010](#aud-016-010) |
| [CHK029](checklists/comprehensive.md#L44) | [ ] | PARTIAL | Policy-name strings/examples exist, but [decision model](data-model.md#L97) lacks authority/version/threshold reference semantics. | [AUD-016-012](#aud-016-012), [AUD-016-019](#aud-016-019) |
| [CHK030](checklists/comprehensive.md#L45) | [ ] | PARTIAL | [R-008](research.md#L324) defines category/hazard/narration variations, not consistent downstream fixture outcomes. | [AUD-016-014](#aud-016-014) |
| [CHK031](checklists/comprehensive.md#L46) | [ ] | IMPLEMENTED | [CLI channels](contracts/cli-interface.md#L29) require JSON stdout in both modes. | [AUD-016-011](#aud-016-011), [AUD-016-016](#aud-016-016) |
| [CHK032](checklists/comprehensive.md#L47) | [ ] | PARTIAL | [Interrupt edge](spec.md#L92) names cleanup but not ownership; [run_pipeline](../../scripts/demo.py#L1103) has none. | [AUD-016-002](#aud-016-002), [AUD-016-019](#aud-016-019) |
| [CHK033](checklists/comprehensive.md#L51) | [ ] | IMPLEMENTED | [Clarification:12](spec.md#L12) reconciles five inner agents with seven orchestration phases. | None |
| [CHK034](checklists/comprehensive.md#L52) | [ ] | IMPLEMENTED | [FR-006](spec.md#L104), [Pipeline Stage entity](spec.md#L120), and clarification consistently enumerate seven conceptual phases. | [AUD-016-015](#aud-016-015) for enforced mapping |
| [CHK035](checklists/comprehensive.md#L53) | [ ] | CONFLICT | [FR-017](spec.md#L115) ends in publishing, while phase six/task design ends at drafting and summary. | [AUD-016-009](#aud-016-009), [AUD-016-019](#aud-016-019) |
| [CHK036](checklists/comprehensive.md#L54) | [ ] | PARTIAL | US2-AS4 and SC-002 agree on <5 minutes; [timing implementation](../../scripts/demo.py#L1174) does not define a complete measurement receipt. | [AUD-016-016](#aud-016-016), [AUD-016-020](#aud-016-020) |
| [CHK037](checklists/comprehensive.md#L55) | [ ] | IMPLEMENTED | [FR-013](spec.md#L111) and [SC-003](spec.md#L141) state the same <60-second wall-clock target. | [AUD-016-020](#aud-016-020) |
| [CHK038](checklists/comprehensive.md#L56) | [ ] | PARTIAL | Safety gates and escalation overlap coherently in intent, but [T022](tasks.md#L88) leaves actual resource thresholds open. | [AUD-016-009](#aud-016-009), [AUD-016-012](#aud-016-012) |
| [CHK039](checklists/comprehensive.md#L57) | [ ] | CONFLICT | Lists agree on six target languages, but [SC-005](spec.md#L143) conflicts with degraded success allowed by FR-014. | [AUD-016-019](#aud-016-019) |
| [CHK040](checklists/comprehensive.md#L58) | [ ] | IMPLEMENTED | [Quickstart:6](quickstart.md#L6) requires committed local data; no requirement authorizes template fetching. | [AUD-016-001](#aud-016-001) for enforcing no egress |
| [CHK041](checklists/comprehensive.md#L59) | [ ] | PARTIAL | [Amended FR-014](spec.md#L112) explicitly treats missing individual locales as degradable, resolving that exception to fail-fast; zero locales and SC-005 remain unresolved. | [AUD-016-013](#aud-016-013), [AUD-016-019](#aud-016-019) |
| [CHK042](checklists/comprehensive.md#L63) | [ ] | PARTIAL | [T009-T016 actions](tasks.md#L60) lack complete observable processing success criteria and accept acknowledgements. | [AUD-016-004](#aud-016-004), [AUD-016-015](#aud-016-015) |
| [CHK043](checklists/comprehensive.md#L64) | [ ] | IMPLEMENTED | [US2-AS1](spec.md#L47) names stage, inputs, decision and output as observable elements. | [AUD-016-016](#aud-016-016) |
| [CHK044](checklists/comprehensive.md#L65) | [ ] | IMPLEMENTED | [Handoff schema](contracts/output-schema.md#L242) supplies source/target/time/confidence/payload fields. | [AUD-016-010](#aud-016-010) |
| [CHK045](checklists/comprehensive.md#L66) | [ ] | UNVERIFIED | [SC-007](spec.md#L145) explicitly requires external rubric assessment, not self-scoring by the demo. | [AUD-016-021](#aud-016-021) |
| [CHK046](checklists/comprehensive.md#L67) | [ ] | PARTIAL | [T021](tasks.md#L87) names four expected routes; observed/failed/extra processing handoffs are not reconciled. | [AUD-016-010](#aud-016-010), [AUD-016-017](#aud-016-017) |
| [CHK047](checklists/comprehensive.md#L68) | [ ] | PARTIAL | [Scenario test](../../tests/simulation/test_demo_script.py#L247) does not define or verify hazard-specific outputs. | [AUD-016-014](#aud-016-014) |
| [CHK048](checklists/comprehensive.md#L69) | [ ] | CONFLICT | [SC-001](spec.md#L139) says every run, while scenarios are also described as stretch goals and partial language success is allowed. | [AUD-016-019](#aud-016-019), [AUD-016-020](#aud-016-020) |
| [CHK049](checklists/comprehensive.md#L73) | [ ] | PARTIAL | [Serializer](../../scripts/demo.py#L1074) overwrites existing files; this policy is not explicit in the CLI contract. | [AUD-016-011](#aud-016-011), [AUD-016-019](#aud-016-019) |
| [CHK050](checklists/comprehensive.md#L74) | [ ] | PARTIAL | Parent directories are created; non-writable output behavior and retained failure evidence are unspecified/unhandled structurally. | [AUD-016-011](#aud-016-011), [AUD-016-019](#aud-016-019) |
| [CHK051](checklists/comprehensive.md#L75) | [ ] | IMPLEMENTED | [CLI channel contract](contracts/cli-interface.md#L29) implies stderr narration independent of file destination; implementation keeps that split. | [AUD-016-017](#aud-016-017) for combined-flags test |
| [CHK052](checklists/comprehensive.md#L76) | [ ] | IMPLEMENTED | [CLI exit 2](contracts/cli-interface.md#L20) and [argparse choices](../../scripts/demo.py#L1229) reject unknown scenarios. | [AUD-016-017](#aud-016-017) |
| [CHK053](checklists/comprehensive.md#L77) | [ ] | IMPLEMENTED | [Argument table](contracts/cli-interface.md#L12) gives a closed three-value enumeration. | None |
| [CHK054](checklists/comprehensive.md#L78) | [ ] | IMPLEMENTED | [Output channels](contracts/cli-interface.md#L29) specify JSON-only stdout. | [AUD-016-011](#aud-016-011) for error paths |
| [CHK055](checklists/comprehensive.md#L79) | [ ] | PARTIAL | Concurrent runs/shared process/output locking are not specified; global reset and second-resolution IDs create risk. | [AUD-016-002](#aud-016-002), [AUD-016-010](#aud-016-010), [AUD-016-019](#aud-016-019) |
| [CHK056](checklists/comprehensive.md#L83) | [ ] | PARTIAL | [Fail-fast research](research.md#L294) defines skipping, not ownership-scoped rollback/cleanup of earlier state. | [AUD-016-002](#aud-016-002), [AUD-016-011](#aud-016-011) |
| [CHK057](checklists/comprehensive.md#L84) | [ ] | PARTIAL | No per-check timeout is defined in [T009](tasks.md#L60) or enforced by setup. | [AUD-016-003](#aud-016-003), [AUD-016-019](#aud-016-019) |
| [CHK058](checklists/comprehensive.md#L85) | [ ] | IMPLEMENTED | [Failure schema](contracts/output-schema.md#L262) identifies phase/agent/error with common exit 1; separate numeric codes are not necessary. | [AUD-016-011](#aud-016-011) |
| [CHK059](checklists/comprehensive.md#L86) | [ ] | PARTIAL | [Loader](../../scripts/demo.py#L236) aggregates missing structural paths, but parse/type errors abort differently without a unified policy. | [AUD-016-013](#aud-016-013), [AUD-016-019](#aud-016-019) |
| [CHK060](checklists/comprehensive.md#L87) | [ ] | PARTIAL | Only Ctrl+C/SIGINT is contracted at [CLI:20](contracts/cli-interface.md#L20); SIGTERM needs an explicit support/defer decision, not assumed implementation. | [AUD-016-011](#aud-016-011), [AUD-016-019](#aud-016-019) |
| [CHK061](checklists/comprehensive.md#L88) | [ ] | PARTIAL | Missing directory is covered by missing structural files, but inaccessible directory/read errors lack consistent structured reporting. | [AUD-016-011](#aud-016-011), [AUD-016-013](#aud-016-013) |
| [CHK062](checklists/comprehensive.md#L89) | [ ] | PARTIAL | [In-process design](quickstart.md#L61) starts no agent subprocesses; client/lifespan/global-state cleanup remains undefined. | [AUD-016-002](#aud-016-002), [AUD-016-019](#aud-016-019) |
| [CHK063](checklists/comprehensive.md#L93) | [ ] | IMPLEMENTED | [FR-013](spec.md#L111) and [test assertion](../../tests/simulation/test_demo_script.py#L322) both use strictly <60. | [AUD-016-020](#aud-016-020) |
| [CHK064](checklists/comprehensive.md#L94) | [ ] | PARTIAL | [SC-002](spec.md#L140) says <300 seconds; exceeding-target exit/report policy is not explicit. | [AUD-016-016](#aud-016-016), [AUD-016-019](#aud-016-019), [AUD-016-020](#aud-016-020) |
| [CHK065](checklists/comprehensive.md#L95) | [ ] | PARTIAL | [Seed model](data-model.md#L185) says nonempty match, but empty structural-record acceptance is not defined/enforced. | [AUD-016-013](#aud-016-013), [AUD-016-019](#aud-016-019) |
| [CHK066](checklists/comprehensive.md#L96) | [ ] | CONFLICT | No-usable-language success is unresolved between [FR-014](spec.md#L112) and [SC-005](spec.md#L143); code reports one safe alert even with zero languages. | [AUD-016-008](#aud-016-008), [AUD-016-013](#aud-016-013), [AUD-016-019](#aud-016-019) |
| [CHK067](checklists/comprehensive.md#L97) | [ ] | PARTIAL | [R-003](research.md#L109) expressly chooses top-level checks; semantic quantities/coordinates/cross-file validity needed by real consumers are not bounded. | [AUD-016-013](#aud-016-013), [AUD-016-019](#aud-016-019) |
| [CHK068](checklists/comprehensive.md#L98) | [ ] | PARTIAL | Named files are defined; minimal usable record set is not. | [AUD-016-013](#aud-016-013), [AUD-016-019](#aud-016-019) |
| [CHK069](checklists/comprehensive.md#L99) | [ ] | PARTIAL | No maximum seed size/scale expectation beyond [plan scope](plan.md#L20); obtain a bounded fixture/scope decision. | [AUD-016-019](#aud-016-019), [AUD-016-020](#aud-016-020) |
| [CHK070](checklists/comprehensive.md#L103) | [ ] | PARTIAL | Wall-clock target exists, but cold/warm/hardware/dependency measurement methodology is absent. | [AUD-016-020](#aud-016-020) |
| [CHK071](checklists/comprehensive.md#L104) | [ ] | PARTIAL | [PhaseResult](data-model.md#L39) records durations but defines no per-stage targets; do not invent them as original obligations. | [AUD-016-003](#aud-016-003), [AUD-016-019](#aud-016-019) |
| [CHK072](checklists/comprehensive.md#L105) | [ ] | PARTIAL | Seed loading is included in overall direct-call timing, but no distinct budget is defined. | [AUD-016-019](#aud-016-019), [AUD-016-020](#aud-016-020) |
| [CHK073](checklists/comprehensive.md#L106) | [ ] | PARTIAL | [Plan technical context](plan.md#L10) contains no memory ceiling; future scope/measurement decision required. | [AUD-016-002](#aud-016-002), [AUD-016-019](#aud-016-019) |
| [CHK074](checklists/comprehensive.md#L110) | [ ] | PARTIAL | Zero dependencies is required but ambient production settings are not blocked before [imports](../../scripts/demo.py#L304). | [AUD-016-001](#aud-016-001) |
| [CHK075](checklists/comprehensive.md#L111) | [ ] | UNVERIFIED | [Plan synthetic-data claim](plan.md#L31) is not an exhaustive privacy review of all seed fields/logs. | [AUD-016-019](#aud-016-019), [AUD-016-020](#aud-016-020) |
| [CHK076](checklists/comprehensive.md#L112) | [ ] | PARTIAL | [FR-003](spec.md#L101) states the outcome but not enforcement; current code has no explicit egress boundary. | [AUD-016-001](#aud-016-001), [AUD-016-019](#aud-016-019) |
| [CHK077](checklists/comprehensive.md#L116) | [ ] | IMPLEMENTED | [Quickstart](quickstart.md#L6) and [root metadata](../../pyproject.toml#L9) require Python 3.12+. | [AUD-016-020](#aud-016-020) for actual environment evidence |
| [CHK078](checklists/comprehensive.md#L117) | [ ] | IMPLEMENTED | [Plan:16](plan.md#L16) names Linux CI and local Windows/macOS. | [AUD-016-016](#aud-016-016), [AUD-016-020](#aud-016-020) |
| [CHK079](checklists/comprehensive.md#L118) | [ ] | IMPLEMENTED | [Plan:16](plan.md#L16) names GitHub Actions. Workflow gate selection is separately missing. | [AUD-016-018](#aud-016-018) |
| [CHK080](checklists/comprehensive.md#L119) | [ ] | CONFLICT | [Quickstart root install](quickstart.md#L10) does not declare the [API/agent dependency sets](../../apps/api/pyproject.toml#L10) needed by the command. | [AUD-016-019](#aud-016-019), [AUD-016-020](#aud-016-020) |
| [CHK081](checklists/comprehensive.md#L123) | [ ] | PARTIAL | [CLI channels](contracts/cli-interface.md#L29) define narration/errors, not agent logger/exporter levels or separation. | [AUD-016-001](#aud-016-001), [AUD-016-016](#aud-016-016), [AUD-016-019](#aud-016-019) |
| [CHK082](checklists/comprehensive.md#L124) | [ ] | PARTIAL | [Narrator](../../scripts/demo.py#L181) and [audit warnings](../../apps/agents/resource_allocation/audit.py#L83) have no unified distinction/quiet-mode contract. | [AUD-016-016](#aud-016-016), [AUD-016-019](#aud-016-019) |
| [CHK083](checklists/comprehensive.md#L128) | [ ] | PARTIAL | [DecisionRecord](data-model.md#L97) gives role examples, not a closed or validated authority set. | [AUD-016-009](#aud-016-009), [AUD-016-019](#aud-016-019), [AUD-016-021](#aud-016-021) |
| [CHK084](checklists/comprehensive.md#L129) | [ ] | PARTIAL | [T017-T020](tasks.md#L83) give policy strings, not a registry/version/threshold link. | [AUD-016-012](#aud-016-012), [AUD-016-019](#aud-016-019) |
| [CHK085](checklists/comprehensive.md#L130) | [ ] | PARTIAL | [FR-017](spec.md#L115) gives an order; historical plan principle mapping and actual publication proof are incomplete. | [AUD-016-009](#aud-016-009), [AUD-016-019](#aud-016-019) |
| [CHK086](checklists/comprehensive.md#L131) | [ ] | IMPLEMENTED | [R-005](research.md#L180) chooses an in-run JSON audit array and rejects separate detailed log artifacts for the demo. | [AUD-016-002](#aud-016-002), [AUD-016-010](#aud-016-010) |
| [CHK087](checklists/comprehensive.md#L132) | [ ] | PARTIAL | [SC-006](spec.md#L144) requires completeness; [tests](../../tests/simulation/test_demo_script.py#L95) check count/key presence only. | [AUD-016-010](#aud-016-010), [AUD-016-017](#aud-016-017) |
| [CHK088](checklists/comprehensive.md#L133) | [ ] | PARTIAL | [Clarification:16](spec.md#L16) links fail-fast to safe behavior, but returned-success bypasses undermine it. | [AUD-016-004](#aud-016-004), [AUD-016-019](#aud-016-019) |
| [CHK089](checklists/comprehensive.md#L137) | [ ] | IMPLEMENTED | [T004](tasks.md#L42) and [loader DATA_DIR](../../scripts/demo.py#L222) explicitly identify repository-local locations. | None |
| [CHK090](checklists/comprehensive.md#L138) | [ ] | PARTIAL | [R-003 table](research.md#L96) describes top-level structures, not a full required usable-input contract. | [AUD-016-013](#aud-016-013), [AUD-016-019](#aud-016-019) |
| [CHK091](checklists/comprehensive.md#L139) | [ ] | PARTIAL | [T004](tasks.md#L42) requires key checks, but [loader](../../scripts/demo.py#L225) does not implement them; ranges/references are unspecified. | [AUD-016-013](#aud-016-013), [AUD-016-019](#aud-016-019) |
| [CHK092](checklists/comprehensive.md#L140) | [ ] | IMPLEMENTED | [R-008](research.md#L324) explicitly reuses structural files and varies hazard/template filters. Geographic suitability remains separate. | [AUD-016-014](#aud-016-014) |
| [CHK093](checklists/comprehensive.md#L141) | [ ] | CONFLICT | [Assumption A6](spec.md#L133) calls cyclone/flood stretch goals while FR-016 and checked tasks require them. | [AUD-016-019](#aud-016-019) |
| [CHK094](checklists/comprehensive.md#L142) | [ ] | IMPLEMENTED | [R-003 schema description](research.md#L96) and [template definitions](../../data/alert-templates/en-AU.json#L23) enumerate fields. Runtime validation/linguistic approval is not established. | [AUD-016-013](#aud-016-013) |
| [CHK095](checklists/comprehensive.md#L146) | [ ] | PARTIAL | [FR-010](spec.md#L108) names locales, not formatting/linguistic review rules; local templates alone are not locale approval. | [AUD-016-008](#aud-016-008), [AUD-016-019](#aud-016-019) |
| [CHK096](checklists/comprehensive.md#L147) | [ ] | CONFLICT | [Alert Draft entity](spec.md#L123) requires body/approval attributes; [output AlertSummary](contracts/output-schema.md#L253) only defines an aggregate. | [AUD-016-008](#aud-016-008), [AUD-016-015](#aud-016-015), [AUD-016-019](#aud-016-019) |
| [CHK097](checklists/comprehensive.md#L148) | [ ] | PARTIAL | [Output schema](contracts/output-schema.md#L253) has a safety boolean without specifying its evidence; the [real safety stage](../../apps/agents/communication/pipeline.py#L126) is not wired into the demo. | [AUD-016-008](#aud-016-008), [AUD-016-019](#aud-016-019) |
| [CHK098](checklists/comprehensive.md#L149) | [ ] | PARTIAL | [FR-014](spec.md#L112) explicitly allows missing individual languages, but all-missing outcome and SC-005 reconciliation remain open. | [AUD-016-013](#aud-016-013), [AUD-016-019](#aud-016-019) |
| [CHK099](checklists/comprehensive.md#L150) | [ ] | IMPLEMENTED | [T027](tasks.md#L106) and [AlertSummary schema](contracts/output-schema.md#L253) make channel_targets explicit. | [AUD-016-008](#aud-016-008), [AUD-016-009](#aud-016-009) |
| [CHK100](checklists/comprehensive.md#L151) | [ ] | PARTIAL | [Auto-approval assumption](spec.md#L132) exists, but draft approval-mode/state representation is absent from the aggregate schema. | [AUD-016-009](#aud-016-009), [AUD-016-015](#aud-016-015) |
| [CHK101](checklists/comprehensive.md#L155) | [ ] | CONFLICT | [Benchmark factory references](research.md#L11) establish instantiation, not initialized agents or no-I/O processing. Current handlers reject missing dependencies. | [AUD-016-001](#aud-016-001), [AUD-016-003](#aud-016-003), [AUD-016-019](#aud-016-019) |
| [CHK102](checklists/comprehensive.md#L156) | [ ] | PARTIAL | [Template adequacy assumption](spec.md#L129) lacks content/safety acceptance detail, and the demo does not execute fallback generation. | [AUD-016-008](#aud-016-008), [AUD-016-019](#aud-016-019) |
| [CHK103](checklists/comprehensive.md#L157) | [ ] | PARTIAL | [Data inventory](research.md#L96) exists; realistic sufficiency remains unverified because consumers/geography are disconnected. | [AUD-016-013](#aud-016-013), [AUD-016-014](#aud-016-014) |
| [CHK104](checklists/comprehensive.md#L158) | [ ] | PARTIAL | [R-001](research.md#L11) cites rehearsals/benchmarks, but no versioned compatibility/ready-processing contract follows from them. | [AUD-016-017](#aud-016-017), [AUD-016-019](#aud-016-019) |
| [CHK105](checklists/comprehensive.md#L159) | [ ] | PARTIAL | [Tasks](tasks.md#L60) name endpoint payloads, but no coupling/version-change strategy; existing code already drifts from assumptions. | [AUD-016-010](#aud-016-010), [AUD-016-017](#aud-016-017), [AUD-016-019](#aud-016-019) |
| [CHK106](checklists/comprehensive.md#L163) | [ ] | PARTIAL | FR/SC/T IDs exist; original scenarios/edges have numbers/bullets but no explicit complete crosswalk. Report-local aliases do not edit the originals. | [AUD-016-019](#aud-016-019) |
| [CHK107](checklists/comprehensive.md#L164) | [ ] | PARTIAL | This report supplies all 15 scenario-to-FR/SC mappings; the original packet does not have a complete explicit mapping. | [AUD-016-019](#aud-016-019) |
| [CHK108](checklists/comprehensive.md#L165) | [ ] | PARTIAL | [FR-014](spec.md#L112) links missing-language behavior, while the other edge-to-requirement mappings remain implicit in the packet. | [AUD-016-019](#aud-016-019) |
| [CHK109](checklists/comprehensive.md#L166) | [ ] | UNVERIFIED | [SC-007](spec.md#L145) is a rubric outcome without a located demo-specific grade/evidence record; portfolio grades cannot substitute. | [AUD-016-021](#aud-016-021) |

## Test Assertions and Evidence Limits

All tests below were **read, not run**. No pytest collection or import was performed.

| Existing test group | Test count | Actual assertions and limitations |
| --- | --- | --- |
| [TestFullPipeline](../../tests/simulation/test_demo_script.py#L54) | 9 | Checks exit 0, scenario, seven pass flags, root-key subset, at least four decisions/handoffs, key presence, distinct handoff agents, six language labels, true safety flag, nonempty channels, run-ID prefix regex, and sequential orders. Does not prove real pipeline calls, content, plans, approval mutation, reference integrity, exact handoff set, timestamp/payload validity, or semantic health. |
| [TestFailurePaths](../../tests/simulation/test_demo_script.py#L189) | 2 | Calls loader against a nonexistent directory and asserts SystemExit(1). Separately supplies one MagicMock client whose GET returns 500 and checks fail/skipped statuses. Does not assert file-specific error text, no factory calls, unhealthy HTTP-200 bodies, later failures, output errors or cleanup. |
| [TestScenarioAndMode](../../tests/simulation/test_demo_script.py#L244) | 4 | Checks cyclone/flood root labels and passing status, verbose banner/Phase strings plus JSON, and output-file JSON/stdout emptiness. Does not check cyclone signal type despite the test name, actual CLI parsing, coherent geography, bodies/approval detail or combined flags. |
| [TestPerformance](../../tests/simulation/test_demo_script.py#L319) | 1 | Measures run_pipeline with perf_counter and asserts exit 0 plus <60 seconds. It is a valid authored direct-call assertion, not measured cold-CLI, verbose, hardware-baselined or repeated-run evidence. |
| [TestSeedDataLoading](../../tests/simulation/test_demo_script.py#L341) | 2 | Checks committed data nonempty, six language files, some bushfire templates, and permissive key alternatives such as facilities OR metadata. Does not test rejection of malformed/empty/semantically invalid fixtures or locale loss. |
| [TestNarrator](../../tests/simulation/test_demo_script.py#L363) | 2 | Checks no output when disabled and banner/message when enabled. No content completeness, encoding, pacing or timing assertions. |
| [TestSerializeOutput](../../tests/simulation/test_demo_script.py#L392) | 2 | Checks JSON serialization and run_id equality for `demo-test`, which violates the stated pattern; no nested schema validation or destination-failure coverage. |

Reusable component tests were also inspected: [risk pipeline assertions](../../tests/unit/test_risk_assessment_pipeline.py#L119) allow recommendation_count >=0 and a conditional type assertion; [evacuation tests](../../tests/unit/test_evacuation_pipeline.py#L67) assert a real plan, zones and traceability but not this demo's wiring; [resource tests](../../tests/unit/test_resource_allocation_pipeline.py#L129) assert demands/traceability but allow conditional assignment checks; [communication tests](../../tests/unit/test_communication_pipeline.py#L84) mock a translator and only construct an English content block; [approval endpoint tests](../../tests/unit/test_communication_endpoints.py#L78) do verify a seeded pending-alert approval and a missing-alert 404. These are suitable homes/patterns, not substitute proof of an offline six-language end-to-end demo.

The [quickstart rehearsal](../../tests/simulation/test_quickstart_rehearsals.py#L21) does assert platform approval/publication, but manually seeds recommendation/alert state. The [benchmark fixtures](../../tests/benchmark/conftest.py#L27) instantiate empty agent apps. Neither validates the research claim that every default factory supplies functional processing.

Authored evidence versus execution/sign-off:

- The local checklists, plan PASS banners, checked tasks and quickstart JSON are authored artifacts. Their existence is IMPLEMENTED; the claimed execution/approval is UNVERIFIED unless separately evidenced.
- Feature-028's [postfeature snapshot](../028-capstone-alignment/evidence/rubric-postfeature.md#L24) reports a portfolio structural mean. It neither grades Spec 016's Application Demo criterion nor tests HYP-014 on this spec. The [decision record](../028-capstone-alignment/evidence/decision-record.md#L35) describes authoring/validation and says optional critique was not blocking; it is not a transcript of all required actor consultations.
- The [feature-value ledger](../shared/feature-value-ledger.md#L30) excludes this delivery-hygiene spec from that pack's outcome attribution. This does not supersede the demo requirements, verify a run, or close its follow-ups.
- No new runtime evidence or human sign-off was produced here. No statement that every successful run is safe/reproducible, no privacy certification, and no rubric grade follows from this static review.

## Future-Only Validation Recipes

**Do not run these as part of this audit.** They are instructions for a separately authorized developer/tester after the indicated remediation. Obtain a selected Python 3.12+ environment with the required API/agent packages and test dependencies installed from their manifests, committed seed fixtures available, and disposable scratch space. Root metadata alone is not a complete runtime installation recipe. Resolve current dependency installation constraints before claiming a clean setup succeeded.

Establish AUD-016-001's no-egress fixture/isolated process **before any product import**. No Azure credentials, production endpoint access, deployments or live message delivery are necessary. In adversarial environment tests, use sentinels under a deny-all transport guard, not real service coordinates. Keep writes inside temporary test state/output and retain failure diagnostics. A future test run must record its own revision and result; these commands are not a record of execution.

| Recipe | Future command / procedure | Prerequisites and expected assertions |
| --- | --- | --- |
| V1: demo regressions | `python -m pytest tests/simulation/test_demo_script.py -q` | Isolated dependencies and stronger cases from AUD-016-017. Require actual processing, full schema/reference/content checks, failure attribution/skipping, no egress, no unrelated-state mutation and reliable cleanup. Narrow runs may select the existing TestFullPipeline, TestFailurePaths, TestScenarioAndMode, TestSeedDataLoading, TestNarrator and TestSerializeOutput classes. |
| V2: component assertions | `python -m pytest tests/unit/test_risk_assessment_pipeline.py tests/unit/test_evacuation_pipeline.py tests/unit/test_resource_allocation_pipeline.py tests/unit/test_communication_pipeline.py tests/unit/test_communication_endpoints.py -q` | Guard imports and inject local dependencies; strengthen existing mocks/conditional assertions as described. A component pass does not close demo integration tasks. |
| V3: quickstart matrix | `python scripts/demo.py`; `python scripts/demo.py --verbose`; `python scripts/demo.py --scenario cyclone`; `python scripts/demo.py --scenario flood`; `python scripts/demo.py --output results/demo-summary.json`; `python scripts/demo.py --verbose --output results/demo-summary.json` | Future disposable checkout/scratch, correct package setup, no-egress guard and resolved output/degradation policy. These are separate invocations. Check one valid JSON object or the requested file, correct stdout/stderr, all real stage outputs, expected scenario data and zero outbound notifications. Also rehearse the quickstart's verbose cyclone/flood combinations. |
| V4: CLI/fault matrix | `python scripts/demo.py --help`; `python scripts/demo.py --scenario earthquake`; future fault-injection cases in V1 | Help exits 0 without running a pipeline; invalid choice exits 2 with usage on stderr. Isolated child-process fault/signal cases assert code 1 or 130, precise failed phase, preserved partial JSON where writable, skipped later work and cleanup. Use platform-appropriate SIGINT handling; SIGTERM behavior requires an explicit decision. |
| V5: measured runs | `python -m pytest tests/simulation/test_demo_script.py::TestPerformance -q`, plus externally timed fresh-process V3 commands | Record cold/warm definition, revision, OS/hardware, interpreter/dependencies, seed identity, total wall-clock through final output, JSON and exit. Require <60 seconds CI and <300 seconds verbose for the agreed scenarios; exact thresholds are failures of the "under" criterion. Keep artificial delay/malformed-run negative controls separate from measured happy paths. |
| V6: documentation/evidence review | Static packet/link/checkbox/schema review; independently authorized persona/hypothesis/rubric assessment | Reconcile every CHK/SQ/plan obligation with the accepted contract. Verify the hypothesis stub structure and real sign-off identities/dates. Grade Application Demo separately from portfolio structural uplift using the applicable rubric skill. Do not mark a hypothesis validated merely because its stub exists. |

Suggested dependency order: settle blocking contract decisions in AUD-016-019; establish offline isolation, owned state and failure reporting; connect actual processing and approvals; repair provenance/policy/output/narration; strengthen tests; install the CI gate; then obtain runtime and independent assessment evidence. Documentary evidence repair may proceed independently where its owner authorizes it. None of these future tasks authorizes changes during this review.

## Report Integrity Validation

Only report-text validation is authorized here: compare original task IDs and exact checkbox states; check complete FR/SC/scenario/edge/amendment/checklist/model/research/gate enumerations; verify every remediation task remains unchecked and every follow-up resolves; verify existing Markdown targets and cited line bounds; and request editor diagnostics for this report only. No product execution is part of that validation. The post-write validation receipt is reported separately; any repair must affect only this report.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 016 only. Three parallel technical reviews examined offline
boundary/failure handling, phase correctness, and evidence/CI claims. A local source correction tightened the setup
health gate: `healthy` and explicit `degraded` are accepted, while `unhealthy` or unknown statuses now fail fast
instead of being counted as operational.

Validation was attempted with `python -m pytest tests/simulation/test_demo_script.py -q`; the prior application-import
blocker from the missing `IngestionProcessingResult` contract has since been repaired. Demo tests still require a fresh
focused rerun. Clean-startup, no-egress, real phase processing, CI selection, timing, human review, and hypothesis
evidence remain unverified.

### 2026-09-19 Continuation Validation

The demo composition was improved without weakening health checks: an initialized MonitoringAgent is supplied for
rule-based degraded fallback, the committed sample road network is loaded into EvacuationAgent, and the platform
governance registry is seeded with the committed BoM source catalogue. Setup now passes all five agent checks, with three
explicit degraded dependencies, and monitoring/risk phases pass.

The focused demo initially failed at evacuation because `/replan` correctly enforced an authenticated commander principal
and the demo request used the old request contract. The demo now supplies an explicit local commander principal and full
replan payload, while preserving route authorization and degraded repository handling.

Validation: `python -m pytest tests/simulation/test_demo_script.py -q` returned `22 passed, 2 warnings`.

Remaining open work is clean-startup portability, real phase/provider composition outside local fallbacks, CI selection,
timing under representative workloads, no-egress evidence, and human/hypothesis evidence.

## Continuation Boundary

The local demo path is validated through all seven phases; external deployment and human evidence remain open.
No cloud deployment or human approval was performed in this continuation.
