# Implementation Review Tasks: Azure OpenAI Integration

**Review date**: 2026-09-11  
**Reviewed revision**: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a` (confirmed HEAD)  
**Report home**: Primary specification folder, `specs/014-azure-openai-integration`.  
**Disposition**: Static review complete; implementation acceptance is not established.  
**Coverage**: 43 original tasks; 22 functional requirements; 10 success criteria; eight stories with
29 acceptance scenarios and eight independent tests; seven edge cases; 20 clarification items;
14 audit-indexed nonfunctional/contract obligations; 23 unchecked follow-ups.

## Scope and Evidence Boundary

This report independently reviews the primary specification together with its associated historical
task home. It contains the full task evidence and developer/tester instructions; no companion report
is required to interpret its findings. The [review contract](../001-spec-implementation-audit/README.md#L13)
is the only audit-control input. Other implementation audits were not consulted and no work was delegated.

All 12 feature-local documents were read in full:

| Input | Role |
| --- | --- |
| [spec.md](spec.md#L1) | Complete requirements, scenarios, clarifications, personas and hypothesis |
| [requirements.md](checklists/requirements.md#L1) | 16 checked specification-quality claims |
| [comprehensive-quality.md](checklists/comprehensive-quality.md#L1) | 92 unchecked requirements-quality questions |
| [tasks.md](../feature/014-azure-openai-integration/tasks.md#L1) | 43 original checked tasks, including T007b |
| [plan.md](../feature/014-azure-openai-integration/plan.md#L1) | Composition, nonfunctional targets and design-gate claims |
| [research.md](../feature/014-azure-openai-integration/research.md#L1) | R1 through R12 design decisions |
| [data-model.md](../feature/014-azure-openai-integration/data-model.md#L1) | Eight entities and configuration defaults |
| [quickstart.md](../feature/014-azure-openai-integration/quickstart.md#L1) | Operator/developer procedures and validation instructions |
| [llm-client.md](../feature/014-azure-openai-integration/contracts/llm-client.md#L1) | Authentication, routing, retry, metadata and logging contract |
| [llm-config.md](../feature/014-azure-openai-integration/contracts/llm-config.md#L1) | Five-agent defaults, validation, environment precedence and hashes |
| [bicep-module.md](../feature/014-azure-openai-integration/contracts/bicep-module.md#L1) | Infrastructure interface, roles, diagnostics and deployment outputs |
| [telemetry.md](../feature/014-azure-openai-integration/contracts/telemetry.md#L1) | Nine instruments, labels, histogram buckets and delivery target |

Applicable code-review, code-commenting and Bicep instructions, the Python fact-grounded review skill,
and Microsoft-docs skill were loaded. Review used static source and actual test assertions,
not imports or execution. No applications, tests, builds, benchmarks, cloud-resource queries,
deployments, branch creation, commits or original-file edits were performed. Only the two authorized
review reports are writable. All commands below are future instructions requiring separate authorization.

This isolated continuation read the complete pre-existing primary report, preserved its useful evidence
and stable AUD IDs, and independently checked the cited controlling paths. Additional associated inputs
include the [three risk entries](../../docs/risk-register/RISK-AOAI-001.md#L1),
[published risk records](../../docs/risk-register/risk-register.json#L1),
[carve-out registry](../../infra/parameters/foundry-carveout.yaml#L1),
[registry gate](../../scripts/verify-carveout.ps1#L1),
[persona contract](../027-spec-hardening/contracts/persona-profile.md#L1),
[hypothesis evidence contract](../028-capstone-alignment/contracts/evidence-stub.contract.md#L1),
and the explicitly linked [rubric baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L1).
The baseline is an authored portfolio-level structural assessment, not proof of HYP-012's per-feature
improvement or consultation. No other specification's implementation audit was consulted.

The [current constitution](../../.specify/memory/constitution.md#L1) and
[accepted Foundry cutover ADR](../../docs/decisions/036-foundry-rag-grounding/20-hard-cutover-foundry-foundation.md#L1)
were inspected as directly relevant replacement evidence. The ADR supersedes the original account/client
deployment arrangement, not all safety, confidence, cost or provenance obligations. The bounded
model-hosting carve-out does not itself approve arbitrary models, global processing or bypassed controls.
The original spec's constitution section numbers no longer describe the current constitution accurately.

Read-only [Microsoft deployment-type guidance](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/deployment-types)
states that Global Standard can process inference in any Azure region, while Standard is geography-scoped
and can use multiple regions within that geography. Neither a hostname nor an Australian account location
proves the original strict single-region inference promise. No live model availability or quota was queried.

### Evidence Statuses

| Status | Meaning in this review |
| --- | --- |
| IMPLEMENTED | Full scoped behavior or authored artifact is supported by inspected source; runtime success is not implied. |
| PARTIAL | A concrete part exists, but a required behavior, connection or assertion is absent or contradicted. |
| MISSING | Named artifact or behavior was not found in the explicitly searched scope after relocation checks. |
| CONFLICT | Original obligations, later decisions or current behavior disagree and require explicit resolution. |
| UNVERIFIED | Execution, performance, deployed state, approval or outcome cannot be established from admissible source. |
| SUPERSEDED | Explicit repository evidence records replacement; this does not automatically retire neighboring obligations. |

## Composition and Search Scope

| Path actually traced | Controlling evidence and consequence |
| --- | --- |
| Deployment to HTTP invocation | [azure.yaml](../../azure.yaml#L1) selects the agents [Dockerfile](../../apps/agents/Dockerfile#L1), which starts [dispatcher](../../apps/agents/dispatcher/__main__.py#L1). Its [handler](../../apps/agents/dispatcher/agent.py#L209) calls the SDK directly. The API [adapter](../../apps/api/app/services/simulation/sub_agents/_base.py#L34) consumes its summary and does not propagate a generation-method/review contract. |
| Legacy domain generation | [Risk](../../apps/agents/risk_assessment/agent.py#L57), [evacuation](../../apps/agents/evacuation/agent.py#L74), [resource allocation](../../apps/agents/resource_allocation/agent.py#L106) and the [translator](../../apps/agents/communication/translator.py#L25) construct the mixin without adapting their agent configs. Their call sites and downstream handoffs were read. |
| Monitoring | [Constructor and summary](../../apps/agents/monitoring/agent.py#L37) use an optional injected client; [classification](../../apps/agents/monitoring/agent.py#L126) calls it directly with reasoning purpose and no output-safety check. Default construction does not create a client. |
| Shared replacement transport | [LLMClient](../../apps/agents/common/llm_client.py#L90) selects [LiveFoundryChatClient](../../apps/agents/common/foundry_chat_client.py#L397) when configured. The legacy SDK and its fixed retry decorator remain a compatibility/test path. |
| Alternate MAF path | [Factory](../../apps/agents/maf_runtime/agents/_factory.py#L87) registers middleware and parses structured responses. The [safety middleware](../../apps/agents/maf_runtime/middleware/content_safety_middleware.py#L63) validates input before `call_next`, not generated output. Its parser is not the mixin's template-on-validation-failure path. |
| Relocated helpers | [Strategy chain](../../apps/agents/common/llm_strategies.py#L1) is explicitly additive. [External budget tracker](../../apps/agents/common/llm_budget_tracker.py#L1) exists, but searches found no production call to its factory or the strategy orchestrator. Neither proves the mixin's obligations are delivered. |
| Infrastructure | [Account](../../infra/main.bicep#L954), [module call and separated RBAC](../../infra/main.bicep#L1377), [module](../../infra/modules/azure-openai.bicep#L1), container environment arrays and both parameter-file families were inspected. RBAC moved out of the module call to break a dependency cycle; it is not missing. |

The standalone [risk health handler](../../apps/agents/risk_assessment/agent.py#L631) sends a prompt,
unlike dispatcher configuration-only readiness. The existing
[public-alert composer](../../apps/web/src/components/alerts/public-alert-composer.tsx#L15) invokes
the [approval service](../../apps/api/app/services/recommendation_service.py#L10), but displays fixed
alert copy and no recommendation confidence/source/reasoning bundle. These paths receive partial
credit; neither closes initialization or US6 review-context requirements.

Negative searches were bounded to tracked `apps/agents`, `apps/api/app`, the relevant domain models,
`apps/web/src/app` and `apps/web/src/components`, `tests/contract`, `tests/integration`, `tests/unit`,
`tests/benchmark`, `tests/simulation`, `apps/api/tests`, `infra/tests`, infrastructure parameters,
`docs/testing`, `docs/risk-register`, and the cited hypothesis evidence folder. Searches included
constructors, callbacks, structured validators, metric names and `.add`/`.record` consumers, budget
factories, quota parameters and API-key paths. No quota-parameter or mixin-budget assertions were found
in the searched test homes. Unrelated AU-ingestion tests were inspected and not credited as inference/IaC tests.

The continuation's tracked-file searches found only definitions/documentation for `build_budget_tracker`,
`run_chain` and `build_default_chain` in `apps/agents` and `apps/api/app`, and no `.add`/`.record` calls
on the nine named LLM instruments in those scopes. Searches for `azure-openai.bicep`, `reasoningTpmQuota`,
`draftingTpmQuota`, `_track_budget`, `_cumulative_cost_usd`, `llm.budget.exceeded` and
`LLM_MONTHLY_BUDGET_USD` in the named test homes returned no matches. The only tracked
`AZURE_OPENAI_API_KEY` match in `apps` and `infra` was a removal-history comment. Searches for MAF
`run_maf`/`_parse_response` overrides found only the shared factory. Web searches included snake-case
and camel-case human-review fields, approval helpers, component symbols and import paths; the existing
public-alert approval composer was followed rather than treated as missing.

The historical `prod.bicepparam` name was checked against the existing
[production.bicepparam](../../infra/parameters/production.bicepparam#L1) and
[production JSON parameters](../../infra/main.parameters.production.json#L1).
All three risk entries are in [one document](../../docs/risk-register/RISK-AOAI-001.md#L1), not missing
because separate RISK-AOAI-002/003 files do not exist. The referenced HYP-HYP-012 evidence stub was absent
from the [cited evidence folder](../028-capstone-alignment/evidence/) and targeted hypothesis searches;
neither the path search `specs/**/*HYP*012*` nor the identifier search across the two feature homes,
the cited evidence folder, the shared persona folder and `docs` found a relocated HYP-012 record.
The [referenced shared persona block](../001-disaster-response-hub/spec.md#L169) explicitly records
SME roles with concrete identities deferred to review; those role labels are not named, dated sign-offs.

## Prioritized Findings

P1 findings affect safety, residency, routing or outage behavior; P2 findings affect required controls
and evidence fidelity; P3 findings concern unverified outcomes and governance evidence.

| Priority | Finding | Controlling evidence | Follow-up |
| --- | --- | --- | --- |
| P1 | Deployed dispatcher returns unvalidated LLM summaries and unmarked degraded stubs; monitoring classification and MAF output also bypass the output validator. | [Dispatcher](../../apps/agents/dispatcher/agent.py#L209), [monitoring](../../apps/agents/monitoring/agent.py#L126), [middleware](../../apps/agents/maf_runtime/middleware/content_safety_middleware.py#L63) | AUD-014-001 |
| P1 | Global deployment defaults and fail-open endpoint/region checks do not establish the original AU/single-region promise or the bounded exception. | [SKU](../../infra/modules/azure-openai.bicep#L70), [URL check](../../apps/agents/common/llm_config.py#L76), [gateway](../../apps/agents/common/foundry_chat_client.py#L362) | AUD-014-002 |
| P1 | Successful calls are gated at fixed confidence 1.0; actual risk handoffs use 0.6 for evacuation and ignore the mixin review flag. | [Mixin](../../apps/agents/common/llm_mixin.py#L174), [handoff predicate](../../apps/agents/risk_assessment/agent.py#L491), [consumer](../../apps/agents/risk_assessment/pipeline.py#L509) | AUD-014-003 |
| P1 | Authentication/deployment readiness is not established at initialization; dispatcher health reports ready from object/config presence. | [Lazy client](../../apps/agents/common/foundry_chat_client.py#L324), [health](../../apps/agents/dispatcher/agent.py#L201) | AUD-014-004 |
| P1 | Declared per-agent tier, temperature and token settings do not control actual calls; resource allocation requests reasoning and the dispatcher selects one simulation deployment for every role. | [Allocation](../../apps/agents/resource_allocation/pipeline.py#L777), [dispatcher selection](../../apps/agents/dispatcher/agent.py#L108) | AUD-014-005 |
| P1 | Configured retries and end-to-end deadlines are not applied to the Foundry call; dispatcher defaults to a 60-second synchronous call inside an async route. | [Foundry call](../../apps/agents/common/foundry_chat_client.py#L397), [dispatcher](../../apps/agents/dispatcher/agent.py#L209) | AUD-014-006 |
| P2 | HALF_OPEN admits every concurrent caller, not one recovery probe. | [can_execute](../../apps/agents/common/circuit_breaker.py#L65) | AUD-014-007 |
| P2 | Structured validation is opt-in and not connected by the original generation callers; MAF parse failures are not translated here into template responses. | [Hook](../../apps/agents/common/llm_mixin.py#L136), [MAF parser](../../apps/agents/maf_runtime/agents/_factory.py#L281) | AUD-014-008 |
| P2 | Safety rejection reasons and review metadata are lost; the Azure validation branch returns before language validation. | [Validator](../../apps/agents/common/content_safety.py#L104), [mixin result](../../apps/agents/common/llm_mixin.py#L155) | AUD-014-009 |
| P2 | The authored 80%-character slice is not an enforced token bound and can leave short over-budget text unchanged. | [Trimming](../../apps/agents/common/llm_mixin.py#L124) | AUD-014-010 |
| P2 | Missing/zero provider usage becomes zero without the required warning; no explicit nonnegative normalization contract is enforced. | [Usage extraction](../../apps/agents/common/llm_client.py#L218) | AUD-014-011 |
| P2 | Foundry deployment metadata reports a model key/tier alias instead of the resolved deployment, and correlation is not passed into the Foundry call. | [Client](../../apps/agents/common/llm_client.py#L174), [response](../../apps/agents/common/foundry_chat_client.py#L460) | AUD-014-012 |
| P2 | Fallback responses/logs do not establish a linked audit event with actual retry count and timestamp. | [Fallback builder](../../apps/agents/common/llm_mixin.py#L202), [logging test](../../tests/contract/test_llm_logging.py#L6) | AUD-014-013 |
| P2 | Nine instruments are declared but not recorded by the generation path; histogram buckets and export proof are absent. | [Metrics](../../apps/agents/monitoring/telemetry.py#L56), [recorder-only emitter](../../apps/agents/common/otel_telemetry.py#L77) | AUD-014-014 |
| P2 | Monthly tracking logs instead of emitting the required warning metric, uses deployment-name price heuristics, and has no production $500 wiring. | [Budget](../../apps/agents/common/llm_mixin.py#L39), [container config](../../infra/main.bicep#L1144) | AUD-014-015 |
| P2 | Root deployment cannot pass TPM overrides; production retains module defaults 30/60 rather than 120/240. | [Root module parameters](../../infra/main.bicep#L1377), [production parameters](../../infra/parameters/production.bicepparam#L1) | AUD-014-016 |
| P2 | Manual AU Southeast redeployment described by the feature is blocked by the root's AU East-only parameter. | [Location restriction](../../infra/main.bicep#L79) | AUD-014-017 |
| P2 | Tests named for integration, telemetry and Bicep restrictions mainly inspect attributes, config or legacy mocks, not the actual required boundaries. | [Telemetry assertions](../../tests/contract/test_llm_telemetry.py#L9), [Bicep-named class](../../tests/contract/test_llm_managed_identity.py#L117) | AUD-014-018 |
| P2 | Retry counts, 404 handling, endpoints, models, quickstart entry points and document completion claims conflict. | [Research R8](../feature/014-azure-openai-integration/research.md#L131), [quickstart](../feature/014-azure-openai-integration/quickstart.md#L1) | AUD-014-019 |
| P2 | IC workspace supplies placeholder rationale, no sources and confidence zero instead of the flagged recommendation. | [Workspace binding](../../apps/web/src/components/workspaces/persona-workspace.tsx#L64) | AUD-014-020 |
| P2 | Risk treatments overstate controls, the quota probability combines disallowed categories, and implementer sign-off is not Risk Manager approval; review dates are overdue. | [Probability field](../../docs/risk-register/RISK-AOAI-001.md#L26), [published registry](../../docs/risk-register/risk-register.json#L14) | AUD-014-021 |
| P3 | Checked full-suite, clean-checkout, live latency, deployment and approval outcomes lack admissible execution proof. | [Original completion tasks](../feature/014-azure-openai-integration/tasks.md#L1), [instant-mock benchmark](../../tests/benchmark/test_llm_performance.py#L1) | AUD-014-022 |
| P3 | Persona validation labels and HYP-012 are not backed by local validation records; the named hypothesis stub is absent. | [Appendices](spec.md#L275), [persona contract](../027-spec-hardening/contracts/persona-profile.md#L1) | AUD-014-023 |

These are source-supported risks, not claims that unsafe public alerts were delivered or that data
actually left Australia. Simulation dispatch, domain handoff, and irreversible public delivery are
different boundaries. Independent human approval elsewhere does not satisfy FR-011's separate
requirement to block low-confidence automatic handoffs.

## Open Follow-up Tasks

All items remain unchecked. Owners and test locations below are existing unless explicitly marked
proposed. Validation command IDs refer to the complete future-only command section in this report.
Dependencies identify prerequisite decisions or collaborating repair tasks, not permission to execute
them during this review. Contract decisions in AUD-014-019 precede affected repairs; its final guide
refresh follows the resolved implementation. Regression authoring may accompany each repair, while
execution and sign-off require the separate prerequisites stated in the validation section.

### Runtime Safety and Availability

- [ ] **AUD-014-001 (P1): Enforce output safety and marked fallback at real entry points.**
  **Obligations**: FR-006, FR-007, SC-003, SC-005; US3, US4; T006, T021, T022, T037.
  **Dependencies**: AUD-014-005 for effective role settings; AUD-014-009 for the shared safety/result contract.
  **Expected/observed/impact**: Every consumed completion must pass validation; the [dispatcher](../../apps/agents/dispatcher/agent.py#L209) directly returns SDK text, its API [consumer](../../apps/api/app/services/simulation/sub_agents/_base.py#L109) treats a nonempty degraded stub as an ordinary reply, and monitoring classification/MAF output lack this gate. Internal consumers can use unvalidated output and lose degradation provenance.
  **Developer**: Own the dispatcher, adapter, monitoring classification and MAF post-response boundary. Reuse the current validator and canonical fallback result, preserve public response compatibility, and carry generation/review fields through adapters. Do not mistake input middleware or upstream content filtering for output validation; no new safety-service migration is required.
  **Tester positive**: All five original roles return a validated safe completion with unchanged required response fields. **Negative**: blocked text, validator failure and provider outage return approved templates and correct markers. **Edge**: empty completion, no choices, malformed reply and a nonempty degraded stub stay visibly degraded. **Fixtures**: real app factory, deterministic SDK transport, validator spy, HTTP adapter fake transport; do not replace the method being audited.
  **Future validation**: V01, V02, V04; extend existing integration tests and add `tests/contract/test_agent_dispatcher_llm.py` only if needed (proposed). **Complete when**: assertions follow handler-to-consumer execution and prove no generated text is consumed before validation.

- [ ] **AUD-014-002 (P1): Bind endpoint, deployment SKU and residency policy to verified configuration.**
  **Obligations**: FR-001, FR-005, FR-014, FR-017, SC-009; T004, T009, T010, T011; EDGE-06/07 and the constitution carve-out.
  **Dependencies**: AUD-014-019 policy reconciliation and explicit security/compliance approval of processing scope.
  **Expected/observed/impact**: Original AU-only/single-region inference is not established by [substring URL checks](../../apps/agents/common/llm_config.py#L76), [GlobalStandard](../../infra/modules/azure-openai.bicep#L70), or a [gateway](../../apps/agents/common/foundry_chat_client.py#L362) that passes through unknown regions/import failures. The dispatcher does not use that gateway. The [registry](../../infra/parameters/foundry-carveout.yaml#L20) names GPT-4o models while the module selects GPT-5.4; geography controls may be bypassed without approved scope.
  **Developer**: Own config parsing, Foundry/dispatcher transport policy, deployment parameters and registry/CD comparison. Parse scheme/host strictly, reject misleading suffix/query/userinfo URLs, bind region and processing scope to authoritative deployment configuration, and fail closed when required minimization is unavailable. Reconcile strict regional wording with documented service guarantees and approved carve-outs; do not relax Azure Policy or infer approval from a region string. Preserve AU storage/telemetry restrictions.
  **Gate detail**: The [CD invocation](../../.github/workflows/cd.yml#L211) omits the effective deployment artifact. The [gate](../../scripts/verify-carveout.ps1#L100) rejects only sufficiently old dates, and its [Strict branch](../../scripts/verify-carveout.ps1#L112) merely warns on near/past expiry. Its [what-if comparison](../../scripts/verify-carveout.ps1#L127) compares deployment names with model names. Bind approved model/version/region/SKU to effective deployment data and make the resolved expiry policy a failing gate; do not accept a registry-only pass as deployment compliance.
  **Tester positive**: approved model/version/SKU/region combinations and regional offline mode. **Negative**: unapproved model, non-AU endpoint without approval, `https://example.invalid/?next=openai.azure.com`, and missing required gateway. **Edge**: missing region, mixed-case hostname, global SKU on an AU account and expired approval. **Fixtures**: local deployment metadata and registry fixtures, gateway spy; no live credentials in unit tests.
  **Future validation**: V02, V06, V07 after policy-owner resolution. **Complete when**: transport and effective deployment are validated together, unsupported configurations fail before prompts leave the process, and actual processing-location proof remains a separate staging gate.

- [ ] **AUD-014-003 (P1): Gate actual domain confidence and fallback-adjusted handoffs.**
  **Obligations**: FR-011, FR-012, SC-007; all US6 scenarios; T007, T026, T027; R4.
  **Dependencies**: AUD-014-005 for effective confidence settings and AUD-014-009 for preserved safety review metadata.
  **Expected/observed/impact**: The [mixin](../../apps/agents/common/llm_mixin.py#L174) evaluates successful output at 1.0. [Risk escalation](../../apps/agents/risk_assessment/pipeline.py#L509) calls the [evacuation predicate](../../apps/agents/risk_assessment/agent.py#L491), which permits a high-severity evacuation recommendation at 0.65 under the [0.6 default](../../apps/agents/risk_assessment/config.py#L56). The [recommendation model](../../packages/domain/src/domain/models/recommendation.py#L7) does not carry the mixin review flag. Domain fallback factors remain 0.8 rather than the configured LLM factor 0.5. Low-confidence or fallback-derived work can be handed off contrary to this feature.
  **Developer**: Own mixin confidence input/result, domain recommendation/plan construction and handoff predicates. Carry real confidence and review provenance, apply the configured reduction exactly once at the appropriate generation step, and enforce the review gate before constructing/sending safety-critical handoffs. Preserve independent severity, tenant and human-approval constraints; do not remove stronger domain gates.
  **Tester positive**: confidence 0.70 and 0.85 proceed when other gates pass. **Negative**: 0.55 and 0.65 produce no handoff; a recommendation-generation fallback after a successful assessment still requires review. **Edge**: exact threshold, configured factor 0/1, safety fallback and preexisting review flags. **Fixtures**: existing risk recommendation factory, fake handoff sink and mixed success/failure completions.
  **Future validation**: V03 and V04, extending [confidence tests](../../tests/contract/test_llm_confidence.py#L17) and [real handoff tests](../../tests/contract/test_risk_assessment_escalation.py#L29). **Complete when**: generation-to-persistence-to-handoff tests, not helper-only calls, enforce the resolved threshold contract.

- [ ] **AUD-014-004 (P1): Make configured authentication and deployment readiness honest.**
  **Obligations**: FR-004, FR-005; US1-AS2/3; EDGE-02; T004, T008, T037, T038.
  **Dependencies**: AUD-014-002 for endpoint policy and AUD-014-006 for a bounded preflight deadline.
  **Expected/observed/impact**: Configured identity failures should surface during bounded initialization. [Foundry SDK construction](../../apps/agents/common/foundry_chat_client.py#L324) is deferred until inference; [legacy initialization](../../apps/agents/common/llm_client.py#L107) catches initialization failures. [Dispatcher health](../../apps/agents/dispatcher/agent.py#L201) infers readiness from objects and names; [resource health](../../apps/agents/resource_allocation/agent.py#L315) is explicitly optimistic. Operators can receive false readiness and discover bad identity/deployment configuration during an incident.
  **Existing credit**: The [risk health handler](../../apps/agents/risk_assessment/agent.py#L631) does call `generate_response`, but does not establish startup readiness for all roles or return the required deployment/region metadata. Reuse that genuine probe behavior where suitable rather than assuming every health path is a stub.
  **Developer**: Own startup/readiness composition and the client. Distinguish intentional no-endpoint template mode from configured-but-invalid identity, endpoint or deployment. Add a bounded preflight, meaningful health metadata including resolved deployment and region, and safe recovery for delayed RBAC propagation. Keep AAD-only auth and never introduce key fallback.
  **Tester positive**: token acquisition and a nonempty deployment health response yield ready metadata. **Negative**: unavailable credential, wrong scope, forbidden role and nonexistent deployment yield descriptive non-ready state. **Edge**: absent endpoint remains usable offline; initialization timeout is bounded; credential refresh and eventual role propagation recover. **Fixtures**: credential/token-provider fakes and transport responses, not only constructor-kwarg assertions.
  **Future validation**: V01, V02, V04; V08 only after explicit staging authorization. **Complete when**: all five operational contexts have truthful startup/health checks and documented offline behavior.

- [ ] **AUD-014-005 (P1): Connect per-agent configuration to model calls.**
  **Obligations**: FR-002, FR-003, FR-010, FR-020, SC-004; T002, T005, T012, T013, T014, T015, T016, T017.
  **Dependencies**: AUD-014-019 decisions on approved models, effective defaults and configuration precedence.
  **Expected/observed/impact**: All five configs declare fields, but [risk](../../apps/agents/risk_assessment/agent.py#L61), [evacuation](../../apps/agents/evacuation/agent.py#L90), [allocation](../../apps/agents/resource_allocation/agent.py#L121) and [translation](../../apps/agents/communication/translator.py#L33) do not adapt them into the mixin. Allocation requests reasoning; monitoring classification also requests reasoning; drafting calls omit temperature and therefore use the method's 0.0 default. Dispatcher uses one deployment for every role. Model cost/quality and reproducibility differ from operator intent.
  **Developer**: Own agent constructors, callback generation calls, shared config and dispatcher role resolution. Resolve the approved model-version change explicitly, preserve role-specific defaults in a cohosted process, pass tier/temperature/token/timeout settings and test actual effective configuration. Validate monthly budgets and retry/circuit settings as finite positive values where required; do not claim a hash proves those values were used.
  **Tester positive**: capture actual transport parameters for each original role and custom config overrides. **Negative**: unknown tier/purpose, invalid temperature/token limit, nonpositive/NaN budget and invalid retry/timeout values fail descriptively. **Edge**: only selecting reasoning must yield its documented defaults; environment changes after construction must not silently mutate frozen behavior. **Fixtures**: per-role config matrix and transport spy with distinct deployment IDs.
  **Future validation**: V01, V02, V03, V04. **Complete when**: all five entry-point tests observe the configured values at the real transport boundary and metadata reflects the chosen deployment.

- [ ] **AUD-014-006 (P1): Apply a bounded retry and total-deadline policy.**
  **Obligations**: FR-008, SC-001, SC-003; US3-AS1/2/3; EDGE-01/05; T005, T018, T020.
  **Dependencies**: AUD-014-019 decisions on attempts versus retries, 404 handling and the total timeout boundary.
  **Expected/observed/impact**: The [legacy decorator](../../apps/agents/common/llm_client.py#L263) fixes three total attempts, ignoring config retry fields. Three total attempts have two intervening sleeps, not three sleeps of 1/2/4 seconds. [Foundry](../../apps/agents/common/foundry_chat_client.py#L397) accepts `timeout_s` but does not pass it to `client.complete`; explicit retry behavior is left to the SDK and wrapped errors lose status attributes. Dispatcher defaults to 60 seconds and blocks its async handler. The source does not enforce the 15-second fallback bound or independent concurrent progress.
  **Developer**: Resolve attempts-versus-retries and 404 policy with AUD-014-019, then own one config-driven retry boundary with preserved categories and an overall deadline including credential acquisition, waits and transport. Bound or disable nested SDK retries, propagate timeouts, and keep synchronous calls off shared event-loop execution. Do not implement automatic regional failover.
  **Tester positive**: transient error followed by success uses exactly the resolved attempts/waits. **Negative**: perpetual 429/503, unreachable host and stalled credential/transport return marked fallback within the total budget. **Edge**: nontransient 400/401/403/404 follow the approved policy, a slow call does not block another agent, cancellation leaves no uncontrolled retry work. **Fixtures**: fake clock, sleep recorder and deterministic transport; later a controlled stalled endpoint for wall-clock measurement.
  **Future validation**: V01, V02, V04 and authorized V08. **Complete when**: exact retry counts, wait sequence, error categories and worst-case completion time are asserted through production composition.

### Shared Processing and Observability

- [ ] **AUD-014-007 (P2): Permit one HALF_OPEN recovery probe.**
  **Obligations**: T003, T006, T018, T019; R3; data-model entity 2 and outage recovery.
  **Dependencies**: None; coordinate the transport-facing regression with AUD-014-006 and AUD-014-018.
  **Expected/observed/impact**: [can_execute](../../apps/agents/common/circuit_breaker.py#L65) returns true for every caller in HALF_OPEN. The lock protects state mutation but does not reserve a probe, so concurrent recovery calls can recreate the retry storm the breaker is meant to prevent.
  **Developer**: Own the circuit-breaker state machine and mixin integration. Reserve/release a single probe atomically, handle cancellation/exception completion, and keep state per agent instance. Preserve injectable time and existing CLOSED/OPEN semantics.
  **Tester positive**: one successful probe closes the breaker. **Negative**: a failed probe reopens it and all concurrent contenders skip transport. **Edge**: exact recovery boundary, cancelled probe, simultaneous late success/failure and independent agent breakers. **Fixtures**: fake monotonic clock, thread barrier and transport call counter in the [existing breaker tests](../../tests/contract/test_llm_circuit_breaker.py#L19).
  **Future validation**: V01 and V04. **Complete when**: concurrency assertions prove at most one in-flight HALF_OPEN call and deterministic recovery without deadlock.

- [ ] **AUD-014-008 (P2): Validate structured results at their actual consumption boundary.**
  **Obligations**: FR-018; T007b, T037; R7; structured-output edge cases.
  **Dependencies**: AUD-014-001 and AUD-014-009 for consistent post-response validation and fallback metadata.
  **Expected/observed/impact**: The [mixin hook](../../apps/agents/common/llm_mixin.py#L136) is authored, but inspected original callers request prose and do not supply a response model. [MAF structured parsing](../../apps/agents/maf_runtime/agents/_factory.py#L281) validates a model but has no local template transition on validation failure. Existence of a hook is not proof of the required structured fallback chain.
  **Developer**: Classify actual prose versus structured call sites, connect the appropriate existing domain model only where structured output is consumed, and carry schema failure into canonical template fallback with confidence reduction and charged-token provenance. Do not force prose summaries into unrelated JSON schemas or replace domain semantic logic. Validate the fallback representation too.
  **Tester positive**: valid agent-specific JSON reaches the domain object. **Negative**: invalid JSON, missing required fields, invalid enums and out-of-range confidence yield valid template objects. **Edge**: syntactically valid but wrong-schema JSON, fenced JSON, truncation and a malformed template. **Fixtures**: existing Recommendation/EvacuationPlan models and lower-level transport fakes; the simulation telemetry parser is a different boundary.
  **Future validation**: V04 with schema cases added to [integration tests](../../tests/integration/test_llm_integration.py#L39). **Complete when**: every identified structured caller has positive and negative model assertions and no validation exception escapes its required fallback boundary.

- [ ] **AUD-014-009 (P2): Preserve content-safety decisions, reasons and language checks.**
  **Obligations**: FR-006, FR-007; US4-AS1/2/3/4; T021, T022.
  **Dependencies**: None; preserve existing validator/result consumers while extending the shared contract.
  **Expected/observed/impact**: [Validator results](../../apps/agents/common/content_safety.py#L104) separate generic result from detailed reason. The [mixin](../../apps/agents/common/llm_mixin.py#L155) retains only the generic result; the [translator](../../apps/agents/communication/translator.py#L158) reuses it as the failure reason. The Azure branch skips language checks; Foundry filter metadata is not retained by the shared client. Operators lose the stated intervention reason and equivalent safety behavior across modes.
  **Developer**: Own result normalization and validator/client/translator adapters. Preserve backward-compatible result plus explicit reason, validation method and review requirements; apply the required language check regardless of primary/fallback validator mode. Honor provider filtering independently of nonempty text and avoid exposing raw sensitive content in diagnostics.
  **Tester positive**: safe output passes with accurate metadata in keyword and Azure-backed modes. **Negative**: blocked keyword, overlength, empty text, language mismatch and a filtered provider response produce the correct reason and safe template. **Edge**: keyword-only service degradation and unsupported-language policy. **Fixtures**: [existing validator tests](../../tests/unit/test_content_safety_pipeline.py#L77), fake Azure safety response and real mixin/translator adapters.
  **Future validation**: V01, V02, V04. **Complete when**: the same rejection reason survives validation, domain output and audit inspection.

- [ ] **AUD-014-010 (P2): Resolve and enforce the output-token limit contract.**
  **Obligations**: FR-010; US5-AS2; T005, T025; R5.
  **Dependencies**: AUD-014-005 for effective limits and the AUD-014-019 decision on the character-slice conflict.
  **Expected/observed/impact**: The [requested legacy slice](../../apps/agents/common/llm_mixin.py#L124) is implemented exactly, so T025 receives artifact credit. Retaining 80% of characters with a minimum slice of 80 does not ensure a token ceiling and may not shorten a short response. Effective per-agent limits are also disconnected. This is a spec/design-contract conflict, not a missing slice.
  **Developer**: Own request-limit propagation and post-response enforcement. Reconcile R5 with the actual maximum guarantee, use a model-appropriate bounded strategy or safe fallback, preserve required alert meaning, and do not deliver truncated invalid structured data. Keep actual usage separate from delivered-text size.
  **Tester positive**: under-limit and exactly-at-limit responses remain intact. **Negative**: heavily over-limit and short high-token-density responses are bounded or safely replaced. **Edge**: Unicode, structured JSON, tiny configured budgets and provider length finish reason. **Fixtures**: known token/response pairs and validator spies, not character length as a proxy assertion.
  **Future validation**: V01 and V04 after the contract decision. **Complete when**: tests assert the resolved token-bound guarantee and required warning with actual/maximum counts.

- [ ] **AUD-014-011 (P2): Make token-accounting metadata best-effort and explicit.**
  **Obligations**: FR-009; US5-AS1; EDGE-04; T005, T023.
  **Dependencies**: None; expose the normalized contract for AUD-014-014 and AUD-014-015 to consume.
  **Expected/observed/impact**: [Usage extraction](../../apps/agents/common/llm_client.py#L218) substitutes zeros without the required warning; conversions do not explicitly enforce nonnegative counts. Missing accounting can look like free inference, and malformed usage can affect otherwise valid generation.
  **Developer**: Own response normalization before mixin budget/metric consumption. Normalize missing/zero usage to documented nonnegative integers, emit a bounded warning/availability indicator, preserve successful content, and prevent malformed accounting alone from crashing the agent. Do not invent token usage or silently charge zero as measured usage.
  **Tester positive**: real positive integer usage is preserved. **Negative**: null, missing, negative and malformed usage produces the documented warning and safe numeric metadata. **Edge**: zero/zero health replies and partial usage fields do not block operation. **Fixtures**: both SDK response shapes and caplog/metric recorder at the actual client boundary.
  **Future validation**: V01, V02, V04. **Complete when**: valid output survives unavailable usage, missing measurements are distinguishable, and no negative counters are emitted.

- [ ] **AUD-014-012 (P2): Preserve actual deployment identity and end-to-end correlation.**
  **Obligations**: FR-003, FR-009, FR-015, FR-016, SC-004; US1-AS3, US2, US8-AS2; T005, T037.
  **Dependencies**: AUD-014-005 for effective role/deployment resolution; coordinate compatible response fields with AUD-014-009.
  **Expected/observed/impact**: [LLMClient](../../apps/agents/common/llm_client.py#L193) reads a `deployment_id` attribute absent from the real FoundryResponse and falls back to a model key or `reasoning`/`drafting` alias. The [real response](../../apps/agents/common/foundry_chat_client.py#L460) stores the resolved deployment in `raw`. The client omits correlation when invoking Foundry, and the mixin returns the supplied nullable ID instead of its client's generated ID. Routing/cost evidence cannot be reliably tied to the originating pipeline.
  **Developer**: Own the response contract and adapters. Expose the resolved deployment and region explicitly, generate a correlation ID once at the pipeline boundary, and propagate it through provider request/span, mixin response, domain artifact and adapter. Preserve compatible legacy response consumers; never use a configured model key as proof of the deployment used.
  **Tester positive**: distinct model key/deployment name returns the actual deployment and one caller correlation ID everywhere. **Negative**: missing deployment metadata is not silently fabricated. **Edge**: repeated CSV keys, tier aliases, caller-omitted ID, fallback and concurrent calls. **Fixtures**: real frozen FoundryResponse objects, request/header/span spies and distinct per-role mappings.
  **Future validation**: V02, V04, V05. **Complete when**: assertions compare the transport's resolved deployment and correlation to every downstream record.

- [ ] **AUD-014-013 (P2): Record a complete fallback audit event.**
  **Obligations**: FR-007, FR-015, FR-016; US3-AS4, US8-AS3; T018, T020.
  **Dependencies**: AUD-014-006 for actual attempt counts, AUD-014-009 for rejection reasons, and AUD-014-012 for correlation/deployment identity.
  **Expected/observed/impact**: The [fallback builder](../../apps/agents/common/llm_mixin.py#L202) has reason and nullable correlation but no timestamp or actual attempt count. Outer domain audit records do not establish a linked per-call retry history. The [logging test](../../tests/contract/test_llm_logging.py#L6) emits its expected log from the fake itself, so it does not verify production logging.
  **Developer**: Own client retry-result metadata and the mixin/domain audit writer boundary. Emit one structured, append-only-compatible event with safe reason code, UTC time, originating correlation, attempts, fallback type and circuit state. Count zero network attempts for an open circuit or offline mode; keep provider-attempt counts distinct from handoff-delivery retries.
  **Tester positive**: successful retry history and final fallback are accurately linked. **Negative**: auth, 429/503 exhaustion, safety rejection and schema failure carry distinct safe reasons. **Edge**: open circuit, missing endpoint and audit-sink degradation do not invent attempts or duplicate events. **Fixtures**: fake clock/transport and existing audit-writer interfaces; capture the real log/event, not a fake-emitted string.
  **Future validation**: V01, V04, V05. **Complete when**: persisted/event assertions establish all required fields and reconstruct one originating invocation without raw prompt leakage.

- [ ] **AUD-014-014 (P2): Record and export the nine required LLM instruments.**
  **Obligations**: FR-009, FR-016, SC-006; US8; T030, T031, T032, T033, T034, T035, T036.
  **Dependencies**: AUD-014-007, AUD-014-011, AUD-014-012 and AUD-014-013 for truthful transition, usage, identity and outcome inputs.
  **Expected/observed/impact**: Instruments exist in all five telemetry modules, but the [mixin](../../apps/agents/common/llm_mixin.py#L64) never records them. [Foundry telemetry](../../apps/agents/common/otel_telemetry.py#L77) only records into an optional in-memory recorder; no exporter call follows its comment. The [tests](../../tests/contract/test_llm_telemetry.py#L9) assert attributes and call a few instruments themselves. Operators cannot rely on the required breakdown or 60-second availability.
  **Developer**: Own generation instrumentation, per-agent registries and deployed exporter initialization. Record calls, latency, input/output tokens, fallback, categorized errors, breaker transitions, budget breaches and confidence gates with bounded labels. Configure the contracted histogram buckets `[100,250,500,1000,2500,5000,10000,15000]`. Reconcile contract-specific label subsets with FR-016's blanket deployment label. Preserve optional no-op operation without conflating it with production observability.
  **Tester positive**: real generation emits exact instrument values/types/buckets and role/deployment labels. **Negative**: each failure category and fallback emits once, with no false success. **Edge**: no OTel package/provider, exporter failure and concurrent agents preserve behavior and metric attribution. **Fixtures**: actual OTel in-memory metric reader/exporter and transport fakes; do not call instruments directly as the behavior under test.
  **Future validation**: V01, V02, V04; V08 measures later export availability. **Complete when**: all nine instruments are asserted at production call boundaries and a separately authorized measurement proves the delivery target.

- [ ] **AUD-014-015 (P2): Deliver per-agent monthly USD budget warning behavior.**
  **Obligations**: FR-021; US5; T023, T024, T029; R10.
  **Dependencies**: AUD-014-005, AUD-014-011 and AUD-014-014; approved model/version pricing inputs are an external prerequisite.
  **Expected/observed/impact**: [Tracking](../../apps/agents/common/llm_mixin.py#L39) logs an over-budget warning but never emits `llm.budget.exceeded`. It selects old pricing by whether the deployment name contains `mini`; actual model identity has changed. The [alternate tracker](../../apps/agents/common/llm_budget_tracker.py#L189) is disconnected and uses a different currency/metric contract. Production receives no $500 override. Cost monitoring is incomplete even though requests are not blocked.
  **Developer**: Own the mixin tracker, validated config, telemetry emission and deployment budget values. Use approved model/version pricing inputs and USD semantics, key monthly state by year/month and agent, count billed safety/schema-fallback calls, and emit the specified warning without blocking requests. The historical in-memory/process-restart limitation is explicitly allowed; do not introduce mandatory persistence just to satisfy this feature.
  **Tester positive**: below-budget accumulation and monthly reset. **Negative**: threshold breach emits the warning metric while generation continues; invalid budget/pricing configuration is descriptive. **Edge**: exact threshold, year rollover, same month in a later year, concurrent calls, two agents and provider usage unavailable. **Fixtures**: fixed prices, fake calendar, per-agent metric reader and charged-token replies.
  **Future validation**: V01 and V04 with real tracker assertions added. **Complete when**: per-agent cost totals, dev/prod defaults, reset semantics and warning emission are observed without request enforcement.

### Infrastructure, Tests and Governance

- [ ] **AUD-014-016 (P2): Expose effective environment-specific model and quota settings.**
  **Obligations**: FR-002, FR-013, FR-022; US7-AS1/4; T010, T011, T028, T029.
  **Dependencies**: AUD-014-002 processing-policy resolution and AUD-014-019 approved model/environment contract.
  **Expected/observed/impact**: [Module parameters](../../infra/modules/azure-openai.bicep#L47) permit quotas, but the [root call](../../infra/main.bicep#L1377) does not pass them or expose matching root parameters. [Dev](../../infra/parameters/dev.bicepparam#L1) and [production](../../infra/parameters/production.bicepparam#L1) files lack the promised values; production also inherits default environment tier/SKU on that path. The JSON production file sets Standard but still not 120/240 TPM. Operator overrides and environment guarantees are not delivered by the actual entry point.
  **Developer**: Own root/module parameters and both supported parameter families. Establish one approved model/version/naming mapping, forward environment-aware 30/60 versus 120/240 values and budgets, preserve stable account/deployment identity during quota-only changes, and retain the separated RBAC assignments that avoid cycles. Verify effective parameters rather than comments or filenames.
  **Tester positive**: render dev and prod effective templates with correct tiers, quotas, SKU, names, roles and diagnostics. **Negative**: zero/negative quotas and unsupported environment/model combinations fail. **Edge**: operator override, custom environment prefix and quota-only update retain resource identity. **Fixtures**: locally rendered templates and approved before/after deployment snapshots.
  **Future validation**: V06 and V07; live update behavior remains V08. **Complete when**: every supported deployment entry point forwards the intended values and a quota-only change has no unintended replacement.

- [ ] **AUD-014-017 (P2): Reconcile the manual AU Southeast failover procedure.**
  **Obligations**: FR-001, FR-014, FR-017; EDGE-06/07; T010, T011, T028, T040; clarification 3 and three-tier degradation amendment.
  **Dependencies**: AUD-014-002, AUD-014-016 and AUD-014-019, plus explicit architecture/policy approval of the model-hosting failover path.
  **Expected/observed/impact**: The [module](../../infra/modules/azure-openai.bicep#L18) accepts both AU regions, but it references an existing account and does not change that account's location. The [root](../../infra/main.bicep#L79) permits only AU East. The documented failover parameter action cannot accomplish the promised recovery path.
  **Developer**: Own the supported infrastructure entry point and operator runbook. Obtain an explicit architecture/policy resolution for a model-hosting failover path without loosening residency of data services or implementing automatic failover. Explain resource replacement/data continuity, endpoint/config updates and fallback while both regions lack capacity; do not simply remove a policy restriction.
  **Tester positive**: a separately approved AU Southeast model-hosting configuration renders and points agents at its actual endpoint. **Negative**: nonapproved regions and absent regional capacity leave agents safely template-only. **Edge**: partial outage, return to primary and mismatched account/config region. **Fixtures**: AU East/AU Southeast local deployment plans and deterministic outage transports.
  **Future validation**: V06, V07 and separately authorized V08. **Complete when**: the supported runbook and effective templates implement the resolved manual degradation chain with no automatic cross-region inference switch.

- [ ] **AUD-014-018 (P2): Replace misleading assertion coverage with boundary-level regressions.**
  **Obligations**: T008, T009, T012, T018, T019, T021, T023, T026, T030, T037, T038; all success-criterion verification methods.
  **Dependencies**: Author alongside each repair; final coverage depends on AUD-014-001 through AUD-014-017 and AUD-014-020. No test execution is authorized in this review.
  **Expected/observed/impact**: [Bicep-named tests](../../tests/contract/test_llm_managed_identity.py#L117) exercise Python URLs, [routing tests](../../tests/contract/test_llm_model_routing.py#L17) mostly read config, and [integration tests](../../tests/integration/test_llm_integration.py#L24) inject the legacy `_client`. They omit actual handoff blocking, recovery chain, budget warnings and deadlines. [Communication coverage](../../tests/contract/test_communication_llm.py#L4) is unconditionally skipped; the [live rehearsal](../../tests/simulation/test_quickstart_live_llm_rehearsal.py#L5) gates on legacy variables and only invokes risk assessment. Passing these sources would not establish the checked tasks' full scope.
  **Developer**: Own the existing named test files and their fixtures. Patch at transport/credential/audit boundaries, exercise actual constructors/callbacks/handlers, isolate both legacy and Foundry environment variables, and add assertions for all five agents. Keep useful validator, state-machine and legacy-compatibility tests; do not replace them with name scans.
  **Tester positive**: demonstrate assertions on each required real path. **Negative**: deliberately bypass a gate, misroute a tier, remove a metric or exceed a deadline and verify the corresponding regression would fail. **Edge**: missing SDK/provider, accidental ambient Foundry environment and skipped live tests cannot count as passes. **Fixtures**: shared deterministic transports, actual response dataclasses, fake clock, metric reader, handoff sink and compiled-template fixtures.
  **Future validation**: V01 through V08 as separately authorized. **Complete when**: coverage maps to concrete assertions, skip counts are visible, and no claimed proof comes solely from a fake's own output or log.

- [ ] **AUD-014-019 (P2): Reconcile original contracts and refresh the supported quickstart.**
  **Obligations**: FR-005, FR-008, FR-010, FR-016, FR-020; T004, T005, T018, T025, T027, T040; both clarification sessions and quality checklists.
  **Dependencies**: None for decisions; obtain accountable requirement-owner agreement before dependent repairs. Final guide content must match their resolved source; execution evidence belongs to AUD-014-022.
  **Expected/observed/impact**: Three attempts versus three retries/three sleeps, retrying 404 versus [R8](../feature/014-azure-openai-integration/research.md#L131), 30-second per-call defaults versus a 15-second total bound, URL-region matching versus custom domains, and old GPT-4o/SDK instructions versus accepted Foundry replacement disagree. The [quickstart](../feature/014-azure-openai-integration/quickstart.md#L1) still uses legacy env/output names and `risk_assessment.main`, which was not found in the scoped agent files. Its unconditional startup-health claim is not true of current composition.
  **Developer**: Own feature contracts/quickstart and explicit architecture decision records in a later authorized change. Record the resolved policy per obligation, current executable entry point, working-directory/import prerequisites and supported environment setup. Correct the 19-versus-22 FR count and stale scope/constitution references without rewriting historical completion or inventing stakeholder approval.
  **Tester positive**: each documented example resolves to an existing entry point and effective configuration. **Negative**: incompatible model names, invalid endpoint, absent credentials and missing deployment produce the documented outcome. **Edge**: offline mode, Windows versus shell syntax and caller-supplied overrides. **Fixtures**: clean authorized checkout and fake/offline configuration before any live rehearsal.
  **Future validation**: V01, V06, V09; authoring consistency can be reviewed without executing product code. **Complete when**: one unambiguous contract governs every conflicting point and a future clean-checkout rehearsal is recorded honestly.

- [ ] **AUD-014-020 (P2): Bind the human-review interface to the actual flagged output.**
  **Obligations**: FR-011; US6-AS3; T026, T027.
  **Dependencies**: AUD-014-003 for review/confidence state and AUD-014-012 for the originating artifact's identity/provenance.
  **Expected/observed/impact**: [IcApprovalCard](../../apps/web/src/app/workspaces/[personaId]/_panels/ic-approval-card.tsx#L21) can display confidence/sources/rationale, but the [workspace](../../apps/web/src/components/workspaces/persona-workspace.tsx#L64) supplies placeholder rationale, empty sources and zero confidence. The card posts to a scenario-outcome evaluator rather than the flagged recommendation. The [recommendation model](../../packages/domain/src/domain/models/recommendation.py#L7) lacks the integration review flag. A relocated [public-alert composer](../../apps/web/src/components/alerts/public-alert-composer.tsx#L15) does call the existing [recommendation approval route](../../apps/api/app/api/routes/recommendations.py#L16), but displays fixed alert content and lacks the required confidence/source/reasoning bundle. The [citation card](../../apps/web/src/components/recommendations/recommendation-card.tsx#L25) likewise has no confidence/review fields. Approval primitives exist; the flagged-output review experience is incomplete.
  **Developer**: Own the recommendation/plan review payload, persisted review state, API-to-workspace binding and approval consumer. Reuse the existing approval route and [service](../../apps/api/app/services/recommendation_service.py#L10). Bind actual adjusted confidence, contributing source records, reasoning and fallback cause to the selected versioned recommendation, preserving tenant/role/approval boundaries and existing independent human-authorization requirements.
  **Tester positive**: a known low-confidence recommendation renders its exact score, source IDs and rationale and records the user's decision against that recommendation. **Negative**: missing or cross-tenant evidence cannot appear as complete review context. **Edge**: template fallback, updated recommendation version, no sources and concurrent approval. **Fixtures**: real serialized domain output, mocked API transport and the existing [web unit test home](../../apps/web/tests/unit/).
  **Future validation**: V03, V04, V10; add a focused component test if no suitable file exists (proposed). **Complete when**: a generated review flag reaches a meaningful human queue/view and the decision updates the corresponding versioned artifact.

- [ ] **AUD-014-021 (P2): Reassess risk treatments and obtain real Risk Manager approval.**
  **Obligations**: FR-019, SC-010; T039; structured-risk amendment.
  **Dependencies**: AUD-014-002, AUD-014-003, AUD-014-004, AUD-014-006, AUD-014-015, AUD-014-016 and AUD-014-017 treatment evidence; independent Risk Manager participation is required.
  **Expected/observed/impact**: [All three risk entries](../../docs/risk-register/RISK-AOAI-001.md#L1) are authored, but treatments assert controls this review found incomplete. The quota-risk [probability](../../docs/risk-register/RISK-AOAI-001.md#L26) combines Low and Medium rather than one of the required categories. Its Markdown cadence is monthly while the published provenance says quarterly. The [published registry](../../docs/risk-register/risk-register.json#L14) records an implementer sign-off rather than Risk Manager acceptance; its three relevant next-review dates precede 2026-09-11. Artifact existence therefore merits partial format credit, not full FR-019 compliance or operational approval.
  **Developer**: Own those three entries and their published representations. Update treatment status and model/cost/failover assumptions after implementation decisions. Select a permitted probability category with a coherent percentage range, reconcile monthly quota review across formats, and obtain identifiable Risk Manager acceptance with date and evidence. Preserve historical records and never backdate approval.
  **Tester positive**: each required risk has all structured fields, current treatment evidence and accountable review. **Negative**: missing approver, stale treatment proof or overdue review is reported as unverified, not accepted. **Edge**: all three entries remain discoverable in one document and monthly quota reviews agree across formats. **Fixtures**: dated source records and a fixed review date.
  **Future validation**: V11 documentary review, followed by authorized governance sign-off. **Complete when**: risk ratings and treatments reflect demonstrated controls and approval is distinguishable from publication metadata.

- [ ] **AUD-014-022 (P3): Supply execution and deployment acceptance evidence prospectively.**
  **Obligations**: T041, T042; SC-001, SC-003, SC-006, SC-008, SC-009, SC-010 and all deployment/performance independent tests.
  **Dependencies**: Resolve or explicitly accept AUD-014-001 through AUD-014-021, then obtain separate execution, staging-cost and governance authorization. A source repair or authored test is not execution evidence.
  **Expected/observed/impact**: Checked tasks and design checkpoints are not test/build/deployment records. The [benchmark](../../tests/benchmark/test_llm_performance.py#L1) deliberately uses instant mocked responses; it cannot prove live latency. No admissible feature-local full-suite, clean-checkout, five-agent staging or Risk Manager approval record establishes these outcomes.
  **Developer**: After fixing/resolving the relevant follow-ups and obtaining execution approval, retain immutable run IDs, exact revision/environment/configuration, actual and skipped test counts, timings, deployment identity/location/SKU and human approvals. Keep authored artifacts separate from measured results; do not retroactively mark original tasks as verified.
  **Tester positive**: all five live contexts satisfy latency, safe outage recovery and telemetry visibility under documented conditions; infrastructure and roles match the approved plan. **Negative**: skipped/no-endpoint runs, mock-only results, wrong revision and incomplete role coverage fail acceptance. **Edge**: cold startup, quota saturation, token refresh and approved failover exercise. **Fixtures**: staging-only authorized identities/resources and retained sanitized measurements.
  **Future validation**: V08, V09, V11 only with their prerequisites. **Complete when**: every execution-dependent claim has independently inspectable evidence and exceptions are explicitly accepted by the responsible owner.

- [ ] **AUD-014-023 (P3): Resolve appended persona and hypothesis evidence gaps.**
  **Obligations**: PER-034, PER-035, PER-036, HYP-012 in [the appended sections](spec.md#L275).
  **Dependencies**: Authentic named SME/practitioner records and any applicable D-009/country approvals; no additional agents, interviews or grading are authorized by this audit.
  **Expected/observed/impact**: Validation labels do not include the [required named SME/practitioner record](../027-spec-hardening/contracts/persona-profile.md#L7); the [cross-referenced AU profiles](../001-disaster-response-hub/spec.md#L169) provide role-only labels with identities deferred. The non-AU persona is intentionally a gated placeholder. The referenced `specs/028-capstone-alignment/evidence/HYP-HYP-012.md` was not found after targeted relocation checks and its doubled prefix conflicts with the [evidence filename contract](../028-capstone-alignment/contracts/evidence-stub.contract.md#L1). The [linked baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L1) is a portfolio-level structural assessment, not a Spec-014 consultation or before/after result. A one-band improvement cannot be inferred from those labels.
  **Developer**: Own these feature appendices and their explicitly linked evidence, in a separately authorized documentation change. Qualify cross-spec FR references, link authentic profile-validation records, preserve the non-AU activation preconditions and supply the actual hypothesis evidence or correct its reference. Do not create an unrequested new audit, delegate work, manufacture interviews or treat the placeholder as validated.
  **Tester positive**: references resolve to the correct persona/hypothesis and identify validation roles, date, conditions and outcome. **Negative**: proxy-only validation, missing stub and absent before/after evidence remain unverified. **Edge**: deferred country preconditions are unmet and must stay deferred. **Fixtures**: approved documentary records, fixed revision/date and local link checker.
  **Future validation**: V11; any interviews or grading require separate authorization. **Complete when**: every label is backed by appropriately scoped evidence or explicitly remains deferred/unverified.

## Functional Requirement Coverage

Every defined FR appears once. There is no separately numbered NFR block in this spec; nonfunctional
targets are covered by all ten SC rows and the plan-obligation table below. FR-023 in the persona prose
is a cross-reference ambiguity, not an additional defined requirement of feature 014.

| Requirement | Status | Concrete evidence and gap | Follow-up |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | [Account](../../infra/main.bicep#L954) is AU East; [root location](../../infra/main.bicep#L79) prevents the promised AU Southeast provisioning path; literal OpenAI account kind is superseded by the accepted ADR. | AUD-014-002, AUD-014-017 |
| FR-002 | CONFLICT | [Deployments](../../infra/modules/azure-openai.bicep#L28) default both tiers to GPT-5.4 rather than GPT-4o/GPT-4o-mini; no local amendment reconciles those exact promises. | AUD-014-005, AUD-014-016, AUD-014-019 |
| FR-003 | PARTIAL | [Routing config](../../apps/agents/common/llm_config.py#L103) exists; [allocation](../../apps/agents/resource_allocation/pipeline.py#L786) and dispatcher ignore the intended per-role tier. | AUD-014-005, AUD-014-012 |
| FR-004 | IMPLEMENTED | [Dispatcher AAD provider](../../apps/agents/dispatcher/agent.py#L154), [Foundry credential](../../apps/agents/common/foundry_chat_client.py#L324), [disableLocalAuth](../../infra/main.bicep#L954) and separated RBAC support keyless inference; actual role propagation is unverified. | AUD-014-004, AUD-014-022 |
| FR-005 | PARTIAL | [Config](../../apps/agents/common/llm_config.py#L76) checks substrings, not actual host/region; Foundry region metadata is not validated against the endpoint. | AUD-014-002, AUD-014-004 |
| FR-006 | PARTIAL | [Mixin gate](../../apps/agents/common/llm_mixin.py#L155) exists, but [dispatcher](../../apps/agents/dispatcher/agent.py#L209), monitoring classification and MAF output bypass it. | AUD-014-001, AUD-014-009 |
| FR-007 | PARTIAL | [Mixin fallback](../../apps/agents/common/llm_mixin.py#L202) returns required markers; [dispatcher/adapter](../../apps/api/app/services/simulation/sub_agents/_base.py#L109) does not carry them. | AUD-014-001, AUD-014-009, AUD-014-013 |
| FR-008 | PARTIAL | [Legacy retry](../../apps/agents/common/llm_client.py#L263) is fixed; [Foundry](../../apps/agents/common/foundry_chat_client.py#L397) does not implement the config-driven contract. | AUD-014-006, AUD-014-019 |
| FR-009 | PARTIAL | [Client usage](../../apps/agents/common/llm_client.py#L218) and [integration assertions](../../tests/integration/test_llm_integration.py#L109) exist; production metrics and missing-usage warning do not. | AUD-014-011, AUD-014-014 |
| FR-010 | PARTIAL | [Slice and warning](../../apps/agents/common/llm_mixin.py#L124) exist; actual per-agent settings and a strict post-response token bound are not established. | AUD-014-005, AUD-014-010 |
| FR-011 | PARTIAL | [Helper](../../apps/agents/common/llm_mixin.py#L226) works on supplied values but [actual escalation](../../apps/agents/risk_assessment/pipeline.py#L509) does not enforce the configured integration review gate. | AUD-014-003, AUD-014-020 |
| FR-012 | PARTIAL | Helper multiplies by configured 0.5, but [risk generation](../../apps/agents/risk_assessment/agent.py#L144) and [evacuation](../../apps/agents/evacuation/pipeline.py#L924) use older domain factors; recommendation-only fallback can retain prior confidence. | AUD-014-003, AUD-014-005 |
| FR-013 | IMPLEMENTED | [Root account/module/RBAC](../../infra/main.bicep#L1377) and [diagnostics/deployments](../../infra/modules/azure-openai.bicep#L174) implement the authored composition on the replacement account. Deployment success remains unverified. | AUD-014-016, AUD-014-022 |
| FR-014 | IMPLEMENTED | [Root restriction](../../infra/main.bicep#L79) and [module allowed list](../../infra/modules/azure-openai.bicep#L18) reject non-AU parameter values in source. This is not inference-location proof or an executed compiler test. | AUD-014-002, AUD-014-018 |
| FR-015 | PARTIAL | [Client](../../apps/agents/common/llm_client.py#L169) generates/logs an ID, but callers omit pipeline IDs and Foundry/mixin do not propagate it end to end. | AUD-014-012, AUD-014-013 |
| FR-016 | PARTIAL | [Nine instruments](../../apps/agents/monitoring/telemetry.py#L56) are authored; call recording, contracted buckets and exporter wiring are not established. | AUD-014-014 |
| FR-017 | CONFLICT | [GlobalStandard default](../../infra/modules/azure-openai.bicep#L70) contradicts strict regional inference; the current bounded carve-out and published geography guarantees need explicit reconciliation. | AUD-014-002, AUD-014-017, AUD-014-019 |
| FR-018 | PARTIAL | [Optional validation hook](../../apps/agents/common/llm_mixin.py#L136) and [MAF parser](../../apps/agents/maf_runtime/agents/_factory.py#L281) exist but do not establish the full structured-output-to-template contract for consuming callers. | AUD-014-008 |
| FR-019 | PARTIAL | [One risk document](../../docs/risk-register/RISK-AOAI-001.md#L1) contains all three risks, but the [quota probability category](../../docs/risk-register/RISK-AOAI-001.md#L26) does not follow the required Low/Medium/High format. Treatment truth, cadence consistency and human review also remain unresolved. | AUD-014-021 |
| FR-020 | PARTIAL | [Agent defaults](../../apps/agents/communication/config.py#L88) are frozen and declared; [drafting calls](../../apps/agents/communication/translator.py#L143) omit configured temperature. | AUD-014-005 |
| FR-021 | PARTIAL | [In-memory cost calculation](../../apps/agents/common/llm_mixin.py#L47) exists but no required warning metric or production $500 environment setting is wired. | AUD-014-015, AUD-014-016 |
| FR-022 | PARTIAL | [30/60 module defaults](../../infra/modules/azure-openai.bicep#L47) have minimum validators; root/production overrides for 120/240 are absent. | AUD-014-016 |

## Success Criterion Coverage

| Criterion | Status | Concrete evidence and limitation | Follow-up |
| --- | --- | --- | --- |
| SC-001 | UNVERIFIED | [Live rehearsal](../../tests/simulation/test_quickstart_live_llm_rehearsal.py#L12) covers one agent without a latency assertion; [benchmark](../../tests/benchmark/test_llm_performance.py#L1) uses instant mocks. Five live responses under 10 seconds were not measured. | AUD-014-004, AUD-014-005, AUD-014-006, AUD-014-022 |
| SC-002 | IMPLEMENTED | Keyless inference is supported by [client construction](../../apps/agents/dispatcher/agent.py#L154) and [resource auth](../../infra/main.bicep#L954); scoped searches found no executable OpenAI API-key path. Unrelated service credentials and live environment values are not certified by this review. | AUD-014-022 |
| SC-003 | PARTIAL | [Fallback](../../apps/agents/common/llm_mixin.py#L202) exists, but [transport](../../apps/agents/common/foundry_chat_client.py#L397) and dispatcher do not enforce the 15-second total bound; no zero-unhandled-exception observation window was run. | AUD-014-001, AUD-014-006, AUD-014-022 |
| SC-004 | CONFLICT | [Current models](../../infra/modules/azure-openai.bicep#L28), actual role routing and [reported deployment identity](../../apps/agents/common/llm_client.py#L193) disagree with the named GPT-4o tier promise. | AUD-014-005, AUD-014-012, AUD-014-016 |
| SC-005 | PARTIAL | [Validator tests](../../tests/unit/test_content_safety_pipeline.py#L77) support local rejection behavior, not universal output gating; dispatcher/classifier/MAF counter-paths are present. | AUD-014-001, AUD-014-009, AUD-014-018 |
| SC-006 | PARTIAL | [Instrument definitions](../../apps/agents/monitoring/telemetry.py#L56) do not establish emitted metrics or availability within 60 seconds; replacement span emission is recorder-only. | AUD-014-014, AUD-014-022 |
| SC-007 | PARTIAL | [Handoff code](../../apps/agents/risk_assessment/pipeline.py#L509) permits the conflicting evacuation confidence interval; [helper tests](../../tests/contract/test_llm_confidence.py#L17) cannot prove 100% blocking. | AUD-014-003, AUD-014-020 |
| SC-008 | UNVERIFIED | [IaC composition](../../infra/main.bicep#L1377) is authored; no single-deployment execution or update outcome was verified. | AUD-014-016, AUD-014-022 |
| SC-009 | UNVERIFIED | [AU account declaration](../../infra/main.bicep#L954) is source evidence only; live resource metadata and inference residency were not queried. | AUD-014-002, AUD-014-022 |
| SC-010 | UNVERIFIED | [Risk artifacts](../../docs/risk-register/RISK-AOAI-001.md#L1) exist; [implementer sign-off](../../docs/risk-register/risk-register.json#L14) is not evidence of the required Risk Manager review. | AUD-014-021, AUD-014-022 |

## Acceptance Scenario Coverage

IDs below preserve story number and original scenario order. Each of the 29 original scenarios has
one row; independent-test descriptions are additionally covered by the validation-command section.

| Scenario | Original expected outcome | Status | Evidence and remaining work | Follow-up |
| --- | --- | --- | --- | --- |
| US1-AS1 | AU East resource with reasoning/drafting GPT-4o deployments | CONFLICT | [Account](../../infra/main.bicep#L954) is Foundry and [model defaults](../../infra/modules/azure-openai.bicep#L28) are GPT-5.4; account migration is documented but literal models need resolution. | AUD-014-005, AUD-014-016, AUD-014-019 |
| US1-AS2 | Managed identity initialization without keys | PARTIAL | [AAD construction](../../apps/agents/dispatcher/agent.py#L154) is keyless, but initialization does not acquire/validate a token or establish readiness. | AUD-014-004, AUD-014-022 |
| US1-AS3 | Operational health prompt with deployment and region metadata | PARTIAL | [Dispatcher health](../../apps/agents/dispatcher/agent.py#L201) checks object presence; [shared response](../../apps/agents/common/llm_client.py#L239) lacks region and misreports Foundry deployment. | AUD-014-004, AUD-014-012 |
| US1-AS4 | Non-Australian deployment parameter rejected clearly | IMPLEMENTED | [Allowed location](../../infra/main.bicep#L79) is restrictive; the [named test](../../tests/contract/test_llm_managed_identity.py#L117) does not compile/validate Bicep. | AUD-014-018, AUD-014-022 |
| US2-AS1 | Risk reasoning call reaches GPT-4o and confirms deployment | PARTIAL | [Risk call](../../apps/agents/risk_assessment/agent.py#L127) requests reasoning, but model mapping changed and returned identity is not the resolved deployment. | AUD-014-005, AUD-014-012 |
| US2-AS2 | Monitoring classification reaches GPT-4o-mini | CONFLICT | [Classification](../../apps/agents/monitoring/agent.py#L126) requests reasoning; [its assertion](../../tests/contract/test_monitoring_escalation.py#L221) expects that conflicting behavior. | AUD-014-005, AUD-014-018 |
| US2-AS3 | Missing deployment produces descriptive failure and template | PARTIAL | [Foundry resolver](../../apps/agents/common/foundry_chat_client.py#L276) raises a descriptive error; shared fallback exists but dispatcher degradation lacks the canonical marker. | AUD-014-001, AUD-014-004, AUD-014-006 |
| US3-AS1 | Unreachable endpoint returns exact template within timeout | PARTIAL | [Integration fallback](../../tests/integration/test_llm_integration.py#L42) asserts text/marker, not elapsed bound; current Foundry timeout argument is unused. | AUD-014-006, AUD-014-018 |
| US3-AS2 | 503 retries with the stated 1/2/4-second pattern | CONFLICT | [Fixed three-attempt decorator](../../apps/agents/common/llm_client.py#L263) and the three-retry prose disagree; Foundry does not use that decorator. | AUD-014-006, AUD-014-019 |
| US3-AS3 | 429 uses the same retry/fallback pattern | PARTIAL | [Legacy classification](../../apps/agents/common/llm_client.py#L253) recognizes 429; production retry/total time and all-agent fallback markers are not established. | AUD-014-001, AUD-014-006 |
| US3-AS4 | Audit carries reason, timestamp, correlation and retry count | PARTIAL | [Fallback result](../../apps/agents/common/llm_mixin.py#L202) omits actual attempts/time; nullable correlation is not stitched to originating work. | AUD-014-012, AUD-014-013 |
| US4-AS1 | Blocked keyword rejection and safety template marker | PARTIAL | [Unit reason assertion](../../tests/unit/test_content_safety_pipeline.py#L95) and [mixin substitution test](../../tests/integration/test_llm_integration.py#L137) exist; end-to-end reason and universal gate do not. | AUD-014-001, AUD-014-009 |
| US4-AS2 | Excessive length rejected as length_exceeded | IMPLEMENTED | [Validator guard](../../apps/agents/common/content_safety.py#L115) and [actual assertion](../../tests/unit/test_content_safety_pipeline.py#L90) support the local behavior, not dispatcher enforcement. | AUD-014-001, AUD-014-009 |
| US4-AS3 | Empty output rejected as empty_output | IMPLEMENTED | [Validator guard](../../apps/agents/common/content_safety.py#L112) and [assertion](../../tests/unit/test_content_safety_pipeline.py#L85) support rejection. | AUD-014-001, AUD-014-009 |
| US4-AS4 | Passed output retained with passed result | IMPLEMENTED | [Mixin success](../../apps/agents/common/llm_mixin.py#L174) and [safe-response assertion](../../tests/integration/test_llm_integration.py#L112) support the scoped behavior. | AUD-014-001, AUD-014-018 |
| US5-AS1 | Nonnegative integer input/output token metadata | PARTIAL | [Usage extraction](../../apps/agents/common/llm_client.py#L218) supports normal replies; normalization/warnings and consistent all-agent propagation remain gaps. | AUD-014-011, AUD-014-012 |
| US5-AS2 | Over-budget text trimmed and warning includes actual/maximum | PARTIAL | [Exact legacy slice/log](../../apps/agents/common/llm_mixin.py#L124) is authored, but text shorter than 80 characters can remain unchanged even when reported tokens exceed the configured maximum. T025 retains credit for its explicitly requested algorithm. | AUD-014-010, AUD-014-018 |
| US5-AS3 | Concurrent usage metrics tagged by agent and deployment | PARTIAL | [Metrics](../../apps/agents/monitoring/telemetry.py#L56) are declared but not recorded by actual calls. | AUD-014-014, AUD-014-015 |
| US6-AS1 | Below-threshold output flagged and no automatic handoff | PARTIAL | [Risk consumer](../../apps/agents/risk_assessment/pipeline.py#L509) does not apply the mixin review flag or 0.7 evacuation threshold. | AUD-014-003 |
| US6-AS2 | At/above threshold normal handoff proceeds | PARTIAL | [Existing handoff tests](../../tests/contract/test_risk_assessment_escalation.py#L31) cover high values but not integration-level flag/threshold composition or exact 0.7 boundary. | AUD-014-003, AUD-014-018 |
| US6-AS3 | IC sees score, contributing data and reasoning | PARTIAL | [Card](../../apps/web/src/app/workspaces/[personaId]/_panels/ic-approval-card.tsx#L21) supports fields; [binding](../../apps/web/src/components/workspaces/persona-workspace.tsx#L64) supplies placeholders. | AUD-014-020 |
| US6-AS4 | Template output gets configured reduction and review flag | PARTIAL | [Mixin](../../apps/agents/common/llm_mixin.py#L202) supplies factor/flag; domain consumers use older factors and omit that review state. | AUD-014-003, AUD-014-005 |
| US7-AS1 | Dev GPT-4o tiers at 30K/60K TPM in AU region | CONFLICT | [Module](../../infra/modules/azure-openai.bicep#L28) retains quota numbers but changes models and defaults SKU to GlobalStandard. | AUD-014-002, AUD-014-016 |
| US7-AS2 | Specified identity receives OpenAI User role | IMPLEMENTED | [Module role loop](../../infra/modules/azure-openai.bicep#L255) and [root identities](../../infra/main.bicep#L1392) are authored; actual assignment propagation is unverified. | AUD-014-004, AUD-014-022 |
| US7-AS3 | Diagnostic logs/metrics route to shared workspace | IMPLEMENTED | [Diagnostic settings](../../infra/modules/azure-openai.bicep#L282) target the passed workspace with RequestResponse, Audit and AllMetrics; deployed flow was not measured. | AUD-014-022 |
| US7-AS4 | Quota parameter update avoids resource recreation | PARTIAL | Stable deployment names exist, but [root](../../infra/main.bicep#L1377) does not expose/forward quotas and update execution is unverified. | AUD-014-016, AUD-014-022 |
| US8-AS1 | Calls, latency, tokens, fallback and categorized errors available | PARTIAL | [Definitions](../../apps/agents/risk_assessment/telemetry.py#L192) exist; [mixin](../../apps/agents/common/llm_mixin.py#L64) does not record them. | AUD-014-014 |
| US8-AS2 | Successful event includes correlation, deployment, latency and usage | PARTIAL | [Client INFO log](../../apps/agents/common/llm_client.py#L230) has fields, but Foundry identity/correlation and actual telemetry recording are incomplete. | AUD-014-012, AUD-014-014 |
| US8-AS3 | Fallback event includes type and applicable error reason | PARTIAL | [Fallback dictionary](../../apps/agents/common/llm_mixin.py#L202) and warning exist, not the required linked telemetry/audit event on all paths. | AUD-014-009, AUD-014-013, AUD-014-014 |

### Independent Tests

These eight rows cover the separate **Independent Test** paragraphs, not additional original task IDs.
No listed test or deployment was executed in this review.

| Independent test | Status | Source and outstanding assertions | Follow-up / future validation |
| --- | --- | --- | --- |
| US1-IT | UNVERIFIED | [Health implementations](../../apps/agents/dispatcher/agent.py#L201) and [single-agent rehearsal](../../tests/simulation/test_quickstart_live_llm_rehearsal.py#L12) do not establish deployed reachability, identity and deployment/region metadata from all five contexts. | AUD-014-004, AUD-014-022; V08 |
| US2-IT | PARTIAL | [Routing tests](../../tests/contract/test_llm_model_routing.py#L17) check configuration rather than all five requests at transport. | AUD-014-005, AUD-014-012, AUD-014-018; V01, V02, V04 |
| US3-IT | PARTIAL | [Fallback assertions](../../tests/integration/test_llm_integration.py#L42) cover text/markers, not an unreachable production transport within the total deadline. | AUD-014-001, AUD-014-006, AUD-014-018; V04, V08 |
| US4-IT | PARTIAL | [Validator cases](../../tests/unit/test_content_safety_pipeline.py#L77) cover local rejection reasons; Azure-backed language behavior and end-to-end substitution/reason propagation remain gaps. | AUD-014-001, AUD-014-009; V02, V04 |
| US5-IT | PARTIAL | [Positive usage assertion](../../tests/integration/test_llm_integration.py#L158) does not cover over-limit text or emitted usage/budget metrics. | AUD-014-010, AUD-014-011, AUD-014-014, AUD-014-015; V01, V04 |
| US6-IT | PARTIAL | [Helper tests](../../tests/contract/test_llm_confidence.py#L17) and [handoff tests](../../tests/contract/test_risk_assessment_escalation.py#L29) are separate and do not exercise generated review state through the safety-critical consumer. | AUD-014-003, AUD-014-020; V03, V04, V10 |
| US7-IT | UNVERIFIED | [IaC source](../../infra/modules/azure-openai.bicep#L174) is authored; no test-subscription provision/update result establishes parameter, role and diagnostic outcomes. | AUD-014-016, AUD-014-017, AUD-014-022; V06, V08 |
| US8-IT | PARTIAL | [Instrument-attribute tests](../../tests/contract/test_llm_telemetry.py#L9) are not call-to-export/backend assertions. | AUD-014-014, AUD-014-018, AUD-014-022; V01, V04, V08 |

## Edge Case Coverage

| Edge | Original obligation | Status | Evidence and gap | Follow-up |
| --- | --- | --- | --- | --- |
| EDGE-01 | Deleted/renamed deployment retries then templates | CONFLICT | [R8](../feature/014-azure-openai-integration/research.md#L131) and client contract prohibit retrying 404; resolver/fallback behavior exists but conflicts with this edge's wording. | AUD-014-006, AUD-014-019 |
| EDGE-02 | Identity token failure fails fast at initialization | PARTIAL | [Lazy credential acquisition](../../apps/agents/common/foundry_chat_client.py#L324) does not establish initialization failure; health is optimistic. | AUD-014-004 |
| EDGE-03 | Semantic inconsistency belongs to domain logic, not transport | IMPLEMENTED | [Risk confidence/severity processing](../../apps/agents/risk_assessment/agent.py#L94) and [domain factual validator tests](../../tests/unit/test_content_safety_pipeline.py#L119) support the separation. Semantic correctness itself was not certified; this audit does not request new agent decision logic. | None for transport scope |
| EDGE-04 | Missing/zero token usage warns and does not block operation | PARTIAL | [Client](../../apps/agents/common/llm_client.py#L218) defaults to zero but does not warn; malformed accounting handling is not established. | AUD-014-011 |
| EDGE-05 | Concurrent agent retries/rate limits remain independent | PARTIAL | Breaker instances are separate, but [dispatcher](../../apps/agents/dispatcher/agent.py#L209) blocks an async route with synchronous SDK work and HALF_OPEN lacks a probe lease. | AUD-014-006, AUD-014-007 |
| EDGE-06 | Operator manually redeploys model to AU Southeast | CONFLICT | [Root region restriction](../../infra/main.bicep#L79) blocks this procedure; the existing-account child module cannot relocate the account. | AUD-014-017, AUD-014-019 |
| EDGE-07 | AU East, manual AU Southeast, automatic template degradation | PARTIAL | Runtime templates exist; supported regional operator transition and behavior when neither region has capacity are not delivered by the current entry point/runbook. | AUD-014-001, AUD-014-006, AUD-014-017 |

## Clarification and Amendment Coverage

CL IDs are audit-local indexes in original order: five initial clarifications, five first-session answers,
and ten second-pass answer/verification/fix bullets. They do not invent new original requirement IDs.

| Item | Original clarification | Status | Evidence/disposition | Follow-up |
| --- | --- | --- | --- | --- |
| CL-01 | Remove API-key authentication; use identity | IMPLEMENTED | [AAD transport](../../apps/agents/dispatcher/agent.py#L154), keyless resource and scoped negative search support code intent. | AUD-014-004, AUD-014-022 |
| CL-02 | Two named GPT-4o model tiers and five-agent mapping | CONFLICT | [Module models](../../infra/modules/azure-openai.bicep#L28) and actual per-agent purposes differ. | AUD-014-005, AUD-014-016 |
| CL-03 | AU East primary, AU Southeast manual failover; no cross-region inference | CONFLICT | Root AU East-only restriction, global processing default and bounded later carve-out need reconciliation. | AUD-014-002, AUD-014-017 |
| CL-04 | Canonical mixin plus real-deployment fallback verification | PARTIAL | [Mixin](../../apps/agents/common/llm_mixin.py#L64) exists but is bypassed; live all-agent verification absent. | AUD-014-001, AUD-014-022 |
| CL-05 | Existing validator sufficient; safety-service migration excluded | SUPERSEDED | [Current validator](../../apps/agents/common/content_safety.py#L1) explicitly documents a later Azure/keyword/domain pipeline. Reuse it; original universal output-gating obligation is not retired. | AUD-014-001, AUD-014-009 |
| CL-06 | Output tokens 4000 reasoning / 2000 drafting, configurable | PARTIAL | [Config defaults](../../apps/agents/common/llm_config.py#L47) and agent fields exist but effective callers hard-code smaller limits. | AUD-014-005, AUD-014-010 |
| CL-07 | Default confidence threshold 0.7 | PARTIAL | [Helper](../../apps/agents/common/llm_mixin.py#L226) uses it; actual safety-critical handoff path does not consistently enforce it. | AUD-014-003 |
| CL-08 | Temperature 0.0 reasoning / 0.3 drafting | PARTIAL | Declared in agent configs, not passed by drafting callers. | AUD-014-005 |
| CL-09 | Deployment names gpt-4o-{env} / gpt-4o-mini-{env} | CONFLICT | [Current deployment names](../../infra/modules/azure-openai.bicep#L174) are GPT-5.4-based. | AUD-014-016, AUD-014-019 |
| CL-10 | $50 dev / $500 prod per agent; tracking only | PARTIAL | Default $50/logging exists; prod override and warning metric are absent. | AUD-014-015, AUD-014-016 |
| CL-11 | Dev TPM 30K/60K, prod 120K/240K | PARTIAL | Module defaults/minimums exist; root and production forwarding do not. | AUD-014-016 |
| CL-12 | Model routing and temperature consistency verified | CONFLICT | [Monitoring classification assertion](../../tests/contract/test_monitoring_escalation.py#L221) expects reasoning; config-only verification does not establish consistency. | AUD-014-005, AUD-014-018 |
| CL-13 | Retry strategy consistency verified | CONFLICT | Three attempts, three retries and three waits cannot all describe the same schedule; Foundry path differs. | AUD-014-006, AUD-014-019 |
| CL-14 | Confidence threshold consistency verified | PARTIAL | Prose uses 0.7; [domain evacuation threshold](../../apps/agents/risk_assessment/config.py#L56) remains 0.6. | AUD-014-003 |
| CL-15 | All LLM outputs explicitly require safety validation | PARTIAL | [Dispatcher](../../apps/agents/dispatcher/agent.py#L209), monitoring classifier and MAF post-call path disconfirm universal enforcement. | AUD-014-001 |
| CL-16 | Token defaults are within model output limits | UNVERIFIED | Historical 16,384-limit statement concerns old models; current model/version availability and constraints were not queried or executed. | AUD-014-010, AUD-014-016, AUD-014-022 |
| CL-17 | Add explicit three-tier degradation chain | PARTIAL | Edge narrative is authored; root failover and runtime deadline gaps remain. | AUD-014-006, AUD-014-017 |
| CL-18 | Strengthen Bicep module dependency references | IMPLEMENTED | [Root roles/diagnostics](../../infra/main.bicep#L1377) and [module](../../infra/modules/azure-openai.bicep#L255) preserve the relevant design intent despite relocated RBAC. | AUD-014-019 |
| CL-19 | Make structured risk-entry format explicit | PARTIAL | [Three risk entries](../../docs/risk-register/RISK-AOAI-001.md#L1) have the fields, but the [quota probability](../../docs/risk-register/RISK-AOAI-001.md#L26) combines categories outside the stated format; accuracy and approval also remain unresolved. | AUD-014-021 |
| CL-20 | Add FR-022 with environment-aware TPM quota defaults | PARTIAL | The requirement is present in the amended spec; [module defaults](../../infra/modules/azure-openai.bicep#L47) remain 30/60 and [root forwarding](../../infra/main.bicep#L1377) does not supply production 120/240 overrides. | AUD-014-016 |

| Appended/later item | Status | Evidence and scope resolution | Follow-up |
| --- | --- | --- | --- |
| Constitution v1.2.0 carve-out | CONFLICT | [Amended non-negotiable residency rule](../../.specify/memory/constitution.md#L249) is bounded by named approvals and minimization; original absolute wording and current global SKU cannot be silently equated. | AUD-014-002, AUD-014-019 |
| ADR-20 Foundry hard cutover | SUPERSEDED | [Accepted decision](../../docs/decisions/036-foundry-rag-grounding/20-hard-cutover-foundry-foundation.md#L1) and root AIServices/config wiring replace the original OpenAI account/legacy env path. Approval prose is authored evidence, not a new verified deployment. | AUD-014-019, AUD-014-022 |
| PER-034 | UNVERIFIED | [Declared validated AU reference](spec.md#L279) leads to [shared profiles](../001-disaster-response-hub/spec.md#L169) that record SME roles and defer concrete identities; a named, dated validation record is not established. | AUD-014-023 |
| PER-035 | UNVERIFIED | [Technical actor catalogue reference](spec.md#L280) is not proof those actors reviewed this implementation or validated the persona fields. | AUD-014-023 |
| PER-036 | UNVERIFIED | [Non-AU placeholder](spec.md#L281) explicitly depends on a separate decision and SME validation; it must not be counted as activated/validated coverage. | AUD-014-023 |
| HYP-012 | MISSING | [Hypothesis statement](spec.md#L287) references an absent HYP-HYP-012 stub; consultation and grade improvement remain UNVERIFIED, not falsified by this static audit. | AUD-014-023 |

## Plan, Research and Contract Assessment

| Obligation group | Status | Source-supported disposition | Follow-up |
| --- | --- | --- | --- |
| R1 identity migration | PARTIAL | AAD clients and scope are authored; initialization/refresh outcomes and local-vs-managed credential selection are not verified. | AUD-014-004, AUD-014-022 |
| R2 frozen environment configuration | PARTIAL | Frozen fields and hashes exist; config-to-transport binding and complete validation are missing. | AUD-014-005 |
| R3 per-agent recovery circuit | PARTIAL | State transitions and lock exist; single HALF_OPEN probe and full-path recovery assertions do not. | AUD-014-007, AUD-014-018 |
| R4 fallback factor 0.5 | PARTIAL | Helper supports it; domain paths retain 0.8 factors or prior confidence. | AUD-014-003 |
| R5 80%-character trim | IMPLEMENTED | Exact requested slice is present; it does not establish FR-010's stronger token-bound reading. | AUD-014-010, AUD-014-019 |
| R6 endpoint substring implies AU | CONFLICT | Current client relaxed to generic URL substrings; neither historical nor current substring approach proves region. | AUD-014-002, AUD-014-019 |
| R7 Pydantic validation hook | PARTIAL | Hook and separate MAF parser exist; required consuming/fallback chain is not established. | AUD-014-008 |
| R8 only 429/503 transient | CONFLICT | Conflicts with deployment-not-found edge and is not the controlled production retry policy. | AUD-014-006, AUD-014-019 |
| R9 existing account plus child module | IMPLEMENTED | Composition remains with the accepted account-kind change; RBAC moved to root for actual principals. | AUD-014-016, AUD-014-022 |
| R10 monthly in-memory tracking/no blocking | PARTIAL | In-memory arithmetic and continued calls exist; required metric/currency/model identity/defaults incomplete. Restart reset is an accepted limitation, not a new missing-persistence finding. | AUD-014-015 |
| R11 AU model availability claim | UNVERIFIED | Historical assertion has no current deployment/quota measurement in this review; no capacity or model-availability query was made. | AUD-014-016, AUD-014-022 |
| R12 fully offline developer operation | PARTIAL | Mixin produces templates with missing endpoint; quickstart entry point, dispatcher markers and all-agent integration assumptions are stale. | AUD-014-001, AUD-014-019 |
| Data-model entity 1: LLMClientConfig | PARTIAL | Fields exist; tier-dependent effective defaults, region validation and consuming config are not fully delivered. | AUD-014-002, AUD-014-005 |
| Data-model entity 2: CircuitBreakerState | PARTIAL | Lock/clock/state machine exist; single-probe semantics fail under concurrent admission. | AUD-014-007 |
| Data-model entity 3: LLMResponse | PARTIAL | Legacy shape exists; Foundry resolved deployment and upstream correlation are lost. | AUD-014-011, AUD-014-012 |
| Data-model entity 4: FallbackResponse | PARTIAL | Canonical fields exist in mixin, not dispatcher/adapter; complete audit metadata absent. | AUD-014-001, AUD-014-013 |
| Data-model entity 5: Agent-tier mapping | CONFLICT | Declared defaults differ from actual classification/allocation/dispatcher calls and deployed model versions. | AUD-014-005, AUD-014-016 |
| Data-model entity 6: Resource/deployments | PARTIAL | Account, deployments, roles and diagnostics authored; overrides, supported failover and literal model defaults differ. | AUD-014-016, AUD-014-017 |
| Data-model entity 7: Risk entries | PARTIAL | Three entries are authored together; the quota probability category conflicts with the required format, and review/treatment outcome is not proved. | AUD-014-021 |
| Data-model entity 8: Telemetry | PARTIAL | Nine instruments authored; producer calls, labels/buckets/export and measurements incomplete. | AUD-014-014 |
| Client contract | PARTIAL | Public generate signature and AAD shape remain; sole-entry-point, retry, startup and metadata guarantees do not. | AUD-014-001, AUD-014-004, AUD-014-006, AUD-014-012 |
| Configuration contract | PARTIAL | Five configs/hash fields are authored; actual settings and effective environment precedence are not demonstrated by consumers. | AUD-014-005, AUD-014-016 |
| Infrastructure contract | PARTIAL | Module/root composition exists; account kind is superseded, names/models changed, root overrides/failover conflict. | AUD-014-016, AUD-014-017, AUD-014-019 |
| Telemetry contract | PARTIAL | Exact instrument names present, but required recording, bucket/label policy and exporter proof absent. | AUD-014-014 |
| Plan NFR: under 10s live / under 15s outage | PARTIAL | No measured outcomes; configured limits/retry composition do not enforce these bounds. | AUD-014-006, AUD-014-022 |
| Plan NFR: metrics available within 60s | PARTIAL | Export interval assertion in prose is not an ingestion-latency guarantee; producer/exporter gaps precede measurement. | AUD-014-014, AUD-014-022 |
| Plan NFR: AU, zero keys, safe degradation, audit and human override | PARTIAL | Keyless source is supported, but residency, fallback marking, linked audit and handoff review controls have the findings above. | AUD-014-001, AUD-014-002, AUD-014-003, AUD-014-013 |
| Plan NFR: five agents, two environments, concurrent load | PARTIAL | All configs exist; role-aware runtime settings, prod quotas/budgets and independent concurrent progress are not established. | AUD-014-005, AUD-014-006, AUD-014-015, AUD-014-016 |

### Unnumbered Nonfunctional Obligations

The spec has no original NFR IDs. NFR-A01 through NFR-A14 are audit-local indexes of explicit plan,
client/configuration/telemetry contract and constitutional obligations. Checklist questions do not
introduce new percentile, availability or capacity targets.

| Audit index | Obligation | Status | Evidence and limitation | Follow-up |
| --- | --- | --- | --- | --- |
| NFR-A01 | Five live agents respond within 10 seconds | UNVERIFIED | [Mock benchmark](../../tests/benchmark/test_llm_performance.py#L1) and [one-role rehearsal](../../tests/simulation/test_quickstart_live_llm_rehearsal.py#L12) cannot prove SC-001. | AUD-014-004, AUD-014-006, AUD-014-022 |
| NFR-A02 | Outage fallback within 15 seconds including retries | PARTIAL | [Foundry transport](../../apps/agents/common/foundry_chat_client.py#L397) ignores its timeout argument; [dispatcher](../../apps/agents/dispatcher/agent.py#L209) defaults to 60 seconds. | AUD-014-001, AUD-014-006 |
| NFR-A03 | Metrics available within 60 seconds | PARTIAL | [Definitions](../../apps/agents/monitoring/telemetry.py#L56) and [recorder](../../apps/agents/common/otel_telemetry.py#L77) do not establish producer/export/backend delivery. | AUD-014-014, AUD-014-022 |
| NFR-A04 | AU processing/privacy with only the bounded approved exception | CONFLICT | [Constitution](../../.specify/memory/constitution.md#L249), [global SKU](../../infra/modules/azure-openai.bicep#L70) and [fail-open gateway](../../apps/agents/common/foundry_chat_client.py#L362) do not establish the original absolute residency promise. | AUD-014-002, AUD-014-017, AUD-014-019 |
| NFR-A05 | Keyless OpenAI identity authentication and credential lifecycle | PARTIAL | [AAD construction](../../apps/agents/dispatcher/agent.py#L154) supports the keyless source requirement; actual token acquisition, refresh and role propagation are unverified. | AUD-014-004, AUD-014-022 |
| NFR-A06 | Per-agent outage recovery without blocking other agents | PARTIAL | [Breaker](../../apps/agents/common/circuit_breaker.py#L65) permits multiple recovery probes; dispatcher synchronous work runs inside an async handler. | AUD-014-006, AUD-014-007 |
| NFR-A07 | Append-only-compatible audit with full call provenance and rationale | PARTIAL | [Domain audit calls](../../apps/agents/risk_assessment/pipeline.py#L473) exist, but [fallback metadata](../../apps/agents/common/llm_mixin.py#L202) lacks a linked per-call timestamp/attempt history. | AUD-014-012, AUD-014-013 |
| NFR-A08 | Human override and inspectable confidence, sources and reasoning | PARTIAL | [Approval service](../../apps/api/app/services/recommendation_service.py#L10) exists; [workspace inputs](../../apps/web/src/components/workspaces/persona-workspace.tsx#L64) are placeholders and domain review flags are not preserved. | AUD-014-003, AUD-014-020 |
| NFR-A09 | Language-appropriate validated public output | PARTIAL | [Azure validator branch](../../apps/agents/common/content_safety.py#L119) returns before language checks, and direct output paths bypass validation. | AUD-014-001, AUD-014-009 |
| NFR-A10 | Frozen configuration resolved at construction with effective overrides | PARTIAL | [Frozen config](../../apps/agents/common/llm_config.py#L21) exists, but [Foundry model-key resolution](../../apps/agents/common/llm_config.py#L134) rereads environment and callers ignore agent settings. | AUD-014-005, AUD-014-019 |
| NFR-A11 | Preserve existing client/mixin consumers through migration | PARTIAL | [Client signature](../../apps/agents/common/llm_client.py#L144) and legacy compatibility remain; metadata identity and actual defaults no longer satisfy the original contract. | AUD-014-005, AUD-014-012, AUD-014-019 |
| NFR-A12 | Optional OTel/no-op behavior without errors or behavioral changes | PARTIAL | [No-op stubs](../../apps/agents/monitoring/telemetry.py#L27) are authored; the [test](../../tests/contract/test_llm_telemetry.py#L76) does not force package absence. Literal zero-overhead and full-path behavioral equivalence are unmeasured. | AUD-014-014, AUD-014-018, AUD-014-022 |
| NFR-A13 | Five roles, dev/prod environments, concurrent disaster load | PARTIAL | [Role dispatcher](../../apps/agents/dispatcher/agent.py#L108) selects one deployment; [production parameters](../../infra/parameters/production.bicepparam#L1) omit quotas/budgets and concurrency guarantees are not demonstrated. | AUD-014-005, AUD-014-006, AUD-014-015, AUD-014-016 |
| NFR-A14 | Well-Architected/design gate and prospective quality gates | UNVERIFIED | [Plan ALL PASS](../feature/014-azure-openai-integration/plan.md#L24) is an authored design assertion; no run/approval evidence establishes its claimed operational controls. | AUD-014-018, AUD-014-019, AUD-014-021, AUD-014-022 |

## Original Task Coverage

Exactly 43 rows follow, preserving every original `[x]` state. Status is this review's disposition,
not a replacement checkbox. Task descriptions are summarized individually; no IDs are collapsed into ranges.

| Original task | Original state | Status | Obligation and concrete implementation/test evidence | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [x] | IMPLEMENTED | Identity is declared in [root dependencies](../../pyproject.toml#L9); openai, tenacity and OTel SDK/distribution are in [agent dependencies](../../apps/agents/pyproject.toml#L9), which the Dockerfile installs. Installed/resolved environment not verified. | AUD-014-022 |
| T002 | [x] | PARTIAL | [Shared config](../../apps/agents/common/llm_config.py#L21) contains frozen fields and validators; required region proof, tier-derived defaults and effective per-agent binding are incomplete. | AUD-014-002, AUD-014-005 |
| T003 | [x] | PARTIAL | [Circuit state machine](../../apps/agents/common/circuit_breaker.py#L26) has lock and clock, but HALF_OPEN is not single-probe. | AUD-014-007 |
| T004 | [x] | PARTIAL | [Legacy AAD migration](../../apps/agents/common/llm_client.py#L107) and replacement Foundry path exist; AU validation and initialization failure contract are not implemented as required. | AUD-014-002, AUD-014-004, AUD-014-019 |
| T005 | [x] | PARTIAL | [generate_response](../../apps/agents/common/llm_client.py#L144) accepts temperature and returns metadata, but retry config is ignored and Foundry deployment/correlation fields are wrong. | AUD-014-005, AUD-014-006, AUD-014-011, AUD-014-012 |
| T006 | [x] | PARTIAL | [Mixin breaker/fallback](../../apps/agents/common/llm_mixin.py#L64) is connected locally, not universally in deployed composition; recovery admission is incomplete. | AUD-014-001, AUD-014-007 |
| T007 | [x] | PARTIAL | [Confidence helper](../../apps/agents/common/llm_mixin.py#L226) calculates a factor/flag, but actual success uses 1.0 and downstream handoffs ignore the intended gate. | AUD-014-003 |
| T007b | [x] | PARTIAL | [Pydantic hook](../../apps/agents/common/llm_mixin.py#L136) exists; original callers do not supply models and separate MAF parser failures do not establish canonical template fallback. | AUD-014-008 |
| T008 | [x] | PARTIAL | [Auth tests](../../tests/contract/test_llm_managed_identity.py#L20) assert absence of api_key field/kwargs and a token-provider call; they do not prove AU region, startup authentication or the active Foundry path. | AUD-014-002, AUD-014-004, AUD-014-018 |
| T009 | [x] | MISSING | Required Bicep region assertion was not found in the scoped test homes. [TestBicepRegionRestriction](../../tests/contract/test_llm_managed_identity.py#L117) only constructs Python URL config; [AU ingestion tests](../../tests/integration/test_au_region_refusal.py#L1) concern a different boundary. | AUD-014-018 |
| T010 | [x] | PARTIAL | [Module](../../infra/modules/azure-openai.bicep#L1) contains deployments, RBAC and diagnostics, but model/naming/SKU defaults differ from its original contract; account-kind change has explicit ADR support. | AUD-014-002, AUD-014-016, AUD-014-017, AUD-014-019 |
| T011 | [x] | PARTIAL | [Root](../../infra/main.bicep#L954) disables local auth and wires Foundry names; [actual roles](../../infra/main.bicep#L1392) exist outside the module call. Required quotas, prod budget and failover configuration are not forwarded. | AUD-014-016, AUD-014-017 |
| T012 | [x] | PARTIAL | [Routing tests](../../tests/contract/test_llm_model_routing.py#L17) assert deployment_for and config defaults, not the parameters sent by each actual agent or dispatcher. | AUD-014-005, AUD-014-018 |
| T013 | [x] | PARTIAL | [Risk config](../../apps/agents/risk_assessment/config.py#L74) has six fields/validation/hash; [constructor/calls](../../apps/agents/risk_assessment/agent.py#L61) leave them disconnected from LLM config and actual confidence. | AUD-014-003, AUD-014-005 |
| T014 | [x] | PARTIAL | [Evacuation config](../../apps/agents/evacuation/config.py#L95) has fields/hash; [constructor](../../apps/agents/evacuation/agent.py#L90) and [summary callback](../../apps/agents/evacuation/pipeline.py#L886) use separate config/defaults. | AUD-014-003, AUD-014-005 |
| T015 | [x] | PARTIAL | [Monitoring config](../../apps/agents/monitoring/config.py#L66) has drafting defaults/hash; [classification](../../apps/agents/monitoring/agent.py#L126) requests reasoning and default constructor has no client. | AUD-014-001, AUD-014-005 |
| T016 | [x] | PARTIAL | [Communication config](../../apps/agents/communication/config.py#L88) has fields/hash; [translator](../../apps/agents/communication/translator.py#L143) uses alert_max_tokens and omits configured temperature. | AUD-014-005 |
| T017 | [x] | PARTIAL | [Allocation config](../../apps/agents/resource_allocation/config.py#L111) has drafting fields/hash; [actual summary call](../../apps/agents/resource_allocation/pipeline.py#L786) uses reasoning, 300 tokens and a hard-coded timeout. | AUD-014-005 |
| T018 | [x] | PARTIAL | [Named fallback file](../../tests/contract/test_llm_fallback.py#L1) has only two marker assertions. [Integration tests](../../tests/integration/test_llm_integration.py#L39) add breaker-open/text checks, not full recovery, 15s timing or complete audit fields. | AUD-014-006, AUD-014-007, AUD-014-013, AUD-014-018 |
| T019 | [x] | PARTIAL | [Breaker tests](../../tests/contract/test_llm_circuit_breaker.py#L19) assert transitions, injectable time and concurrent failure counting; no concurrent HALF_OPEN admission assertion. | AUD-014-007, AUD-014-018 |
| T020 | [x] | PARTIAL | [Fallback warnings/result](../../apps/agents/common/llm_mixin.py#L186) contain some fields; actual attempts, linked timestamped audit and generated-correlation propagation are absent. | AUD-014-012, AUD-014-013 |
| T021 | [x] | PARTIAL | [Fallback marker test](../../tests/contract/test_llm_fallback.py#L16), [relocated validator reasons](../../tests/unit/test_content_safety_pipeline.py#L77) and safe/blocked integration tests cover useful local behavior, not universal gate/reason propagation. | AUD-014-001, AUD-014-009, AUD-014-018 |
| T022 | [x] | PARTIAL | [Mixin validator](../../apps/agents/common/llm_mixin.py#L155) substitutes templates, but all-output verification fails on dispatcher/classifier/MAF paths and detailed reason propagation is lost. | AUD-014-001, AUD-014-009 |
| T023 | [x] | PARTIAL | [Telemetry tests](../../tests/contract/test_llm_telemetry.py#L9) do not assert token trimming or budget breaches; [integration usage assertion](../../tests/integration/test_llm_integration.py#L158) covers positive counts only. No relocated mixin-budget assertions found. | AUD-014-010, AUD-014-011, AUD-014-015, AUD-014-018 |
| T024 | [x] | PARTIAL | [Monthly tracker](../../apps/agents/common/llm_mixin.py#L47) implements arithmetic/reset/logging but not required metric emission or correct effective model/config attribution. | AUD-014-015 |
| T025 | [x] | IMPLEMENTED | [Exact requested character slice and warning](../../apps/agents/common/llm_mixin.py#L124) exist. This credits authored logic, not execution or a strict token bound. | AUD-014-010, AUD-014-018 |
| T026 | [x] | PARTIAL | [Confidence tests](../../tests/contract/test_llm_confidence.py#L17) exercise helper arithmetic and flags only; they do not assert no handoff or populated review UI. | AUD-014-003, AUD-014-018, AUD-014-020 |
| T027 | [x] | PARTIAL | [Mixin fallback factor](../../apps/agents/common/llm_mixin.py#L202) exists, but [domain handoffs](../../apps/agents/risk_assessment/pipeline.py#L509) and UI do not consume the intended review/confidence fields. | AUD-014-003, AUD-014-020 |
| T028 | [x] | PARTIAL | [Quota parameters](../../infra/modules/azure-openai.bicep#L47) have minimums; [root forwarding](../../infra/main.bicep#L1377) and production 120/240 values are absent. No redeployment outcome was verified. | AUD-014-016, AUD-014-022 |
| T029 | [x] | PARTIAL | [Dev file](../../infra/parameters/dev.bicepparam#L1) and renamed [production file](../../infra/parameters/production.bicepparam#L1) exist, but neither sets required TPM/budget values; JSON production sets SKU only. | AUD-014-015, AUD-014-016 |
| T030 | [x] | PARTIAL | [Instrument tests](../../tests/contract/test_llm_telemetry.py#L9) use hasattr and manual instrument calls, not instrument names/types/buckets/labels on actual generation events. | AUD-014-014, AUD-014-018 |
| T031 | [x] | PARTIAL | [Risk metrics](../../apps/agents/risk_assessment/telemetry.py#L192) define nine instruments and no-op fields; contracted buckets and production recording are not connected. | AUD-014-014 |
| T032 | [x] | PARTIAL | [Evacuation metrics](../../apps/agents/evacuation/telemetry.py#L287) define nine instruments via guarded factories; bucket/recording obligations remain. | AUD-014-014 |
| T033 | [x] | PARTIAL | [Monitoring metrics](../../apps/agents/monitoring/telemetry.py#L56) define nine instruments with no-op support; bucket/recording obligations remain. | AUD-014-014 |
| T034 | [x] | PARTIAL | [Communication metrics](../../apps/agents/communication/telemetry.py#L238) define nine instruments/namespace; generation does not record them or configure the contracted buckets. | AUD-014-014 |
| T035 | [x] | PARTIAL | [Allocation metrics](../../apps/agents/resource_allocation/telemetry.py#L235) define nine instruments/no-op attributes, not their required runtime recording/buckets. | AUD-014-014 |
| T036 | [x] | MISSING | Required recording is absent in [mixin](../../apps/agents/common/llm_mixin.py#L64); scoped production searches found no `.add`/`.record` consumers for these instruments. [Replacement emitter](../../apps/agents/common/otel_telemetry.py#L77) is not an OTel export implementation. | AUD-014-014 |
| T037 | [x] | PARTIAL | [Integration suite](../../tests/integration/test_llm_integration.py#L1) tests legacy mocks/basic fallback; it does not prove config-to-Foundry composition, recovery chain, multi-call budget tracking or no-handoff behavior. | AUD-014-003, AUD-014-006, AUD-014-008, AUD-014-018 |
| T038 | [x] | PARTIAL | [Rehearsal](../../tests/simulation/test_quickstart_live_llm_rehearsal.py#L1) removes API-key requirements but checks legacy env vars, one risk call and no latency. Current Foundry-only environments can skip it. | AUD-014-018, AUD-014-022 |
| T039 | [x] | PARTIAL | [Risk document](../../docs/risk-register/RISK-AOAI-001.md#L1) contains all three named entries, but the [quota probability category](../../docs/risk-register/RISK-AOAI-001.md#L26) conflicts with FR-019's stated format. Approval, freshness and treatment truth are not credited. | AUD-014-021 |
| T040 | [x] | PARTIAL | [Quickstart](../feature/014-azure-openai-integration/quickstart.md#L1) is authored but references old env/output names, absent main module and unsupported readiness/failover assumptions. | AUD-014-019 |
| T041 | [x] | UNVERIFIED | Original full-suite and Bicep-build completion claim has no admissible execution record establishing success at the reviewed revision. Neither command was run by this audit. | AUD-014-022 |
| T042 | [x] | UNVERIFIED | Clean-checkout end-to-end quickstart validation is claimed by the checkbox; [current guide](../feature/014-azure-openai-integration/quickstart.md#L1) is stale and no such rehearsal was performed here. | AUD-014-019, AUD-014-022 |

## Review and Checklist Evidence Assessment

The basic checklist remains **16/16 originally checked**; the comprehensive checklist remains
**0/92 originally checked**. These are authored quality-review states, not implementation or execution
results. The basic checklist still says 19 FRs and eight exclusions, whereas the spec defines 22 FRs
and includes additional exclusions. Its no-implementation-detail claims are also inconsistent with
the explicitly technical contract text. Neither checklist was edited or retroactively completed.

The full comprehensive checklist was considered by topic as follows; its questions are not silently
converted into new product requirements, and unresolved policy questions need AUD-014-019 resolution.

| Original checklist section | Original items | Evidence assessment | Follow-up |
| --- | --- | --- | --- |
| Infrastructure completeness | CHK001, CHK002, CHK003, CHK004, CHK005, CHK006, CHK007, CHK008 | Regions/models/names/TPM/diagnostics are authored; neither-region capacity, networking/retention policy and effective failover remain incomplete or conflicting. | AUD-014-002, AUD-014-016, AUD-014-017, AUD-014-019 |
| Authentication/security | CHK009, CHK010, CHK011, CHK012, CHK013 | Identity/RBAC/keyless code exists; refresh/lifecycle/readiness outcomes are unverified and SDK delegation is not an execution record. | AUD-014-004, AUD-014-022 |
| Routing/configuration | CHK014, CHK015, CHK016, CHK017, CHK018 | Frozen defaults/hash and partial validation exist; real routing/temperature/config application disagrees. | AUD-014-005 |
| Resilience/fallback | CHK019, CHK020, CHK021, CHK022, CHK023, CHK024 | Fallback/circuit artifacts exist; template validity, markers, single-probe recovery and manual chain need work. | AUD-014-001, AUD-014-006, AUD-014-007, AUD-014-008, AUD-014-017 |
| Safety/confidence | CHK025, CHK026, CHK027, CHK028, CHK029, CHK030 | Domain confidence and validator exist; all-output gate, safety-critical gate scope and populated review UI are not established. | AUD-014-001, AUD-014-003, AUD-014-009, AUD-014-020 |
| Telemetry/cost | CHK031, CHK032, CHK033, CHK034, CHK035, CHK036 | Names/labels/buckets/prices are documented; emitting/exporting metrics, actual rates and dashboard/retention ownership are not proved. Warning metrics are distinct from out-of-scope enforcement. | AUD-014-014, AUD-014-015, AUD-014-019 |
| Requirement clarity | CHK037, CHK038, CHK039, CHK040, CHK041, CHK042, CHK043, CHK044 | Valid response/load/deadline/init bounds require explicit definitions; trim, region and 404 policies conflict. | AUD-014-004, AUD-014-006, AUD-014-008, AUD-014-010, AUD-014-019 |
| Consistency | CHK045, CHK046, CHK047, CHK048, CHK049, CHK050, CHK051, CHK052 | Retry math, effective defaults, 19/22 count and live model versions disconfirm blanket consistency; tracking-only scope is retained. | AUD-014-005, AUD-014-015, AUD-014-016, AUD-014-019 |
| Acceptance quality | CHK053, CHK054, CHK055, CHK056, CHK057, CHK058, CHK059, CHK060, CHK061, CHK062 | Measurement methodology, originating correlation, inference geography and named human approval cannot be replaced by mocks/checkmarks. | AUD-014-002, AUD-014-012, AUD-014-018, AUD-014-021, AUD-014-022 |
| Scenario coverage | CHK063, CHK064, CHK065, CHK066, CHK067, CHK068, CHK069 | All five contexts, concurrency, first-run/readiness and malformed output require boundary tests; frozen config intentionally excludes hot reload. | AUD-014-004, AUD-014-005, AUD-014-006, AUD-014-008, AUD-014-018 |
| Additional edges | CHK070, CHK071, CHK072, CHK073, CHK074, CHK075 | Partial replies, missing usage, API retirement, credential expiry, quota contention and name mismatch need explicit behavior/evidence. | AUD-014-004, AUD-014-006, AUD-014-011, AUD-014-016, AUD-014-019 |
| NFR questions | CHK076, CHK077, CHK078, CHK079, CHK080, CHK081 | No new percentile/availability target is invented; original latency, privacy, concurrency and compatibility claims need resolved definitions and measured evidence. | AUD-014-002, AUD-014-006, AUD-014-013, AUD-014-019, AUD-014-022 |
| Dependencies/assumptions | CHK082, CHK083, CHK084, CHK085, CHK086, CHK087 | Existing mixin/validator/templates/IaC were traced, including replacements; availability, export capacity and version support remain unverified. | AUD-014-001, AUD-014-008, AUD-014-014, AUD-014-016, AUD-014-022 |
| Traceability/governance | CHK088, CHK089, CHK090, CHK091, CHK092 | This report supplies FR/SC/scenario/task mapping; stale constitution references and stakeholder validation claims still need authentic evidence. | AUD-014-019, AUD-014-021, AUD-014-023 |

| Authored artifact or claim | What was actually established |
| --- | --- |
| Plan constitution gate marked ALL PASS | A design assertion only; controlling source has counterexamples for output safety, review gating, provenance and observability. |
| Historical task checkpoints and all 43 checked tasks | Authored completion claims; not evidence of test-first failures, successful builds, live deployment, timing or approval. |
| Risk Markdown plus published JSON | Three risks and publication metadata exist. The JSON sign-off identifies an implementer; relevant next-review dates are 2026-06-11 or 2026-08-11, before this review. |
| Foundry ADR and carve-out registry | Accepted-decision/approval fields are authored records. Current effective models, SKU and gateway enforcement still need validation; approval identities were not independently authenticated. |
| Test source | Local assertions were inspected, including useful validator/state transitions and deficient mocks/skips. No passing run is claimed. |
| Live rehearsal and benchmark source | One legacy-env-gated risk call and instant-mock overhead measurement, respectively; neither establishes five-agent deployed performance. |
| Persona/hypothesis labels and linked baseline | Shared profiles contain role-only validation labels. The authored portfolio baseline does not establish a Spec-014 before/after result or consultation; the specifically named hypothesis stub was not found and its doubled prefix conflicts with the evidence contract. |

## Future-Only Validation Commands

**None of these commands was run.** These are instructions for later authorized developers/testers.
Run from repository root unless stated otherwise. Before V01-V05, use an explicitly selected Python
3.12+ environment containing root development and agent dependencies. Clear ambient live Foundry,
legacy OpenAI and Content Safety endpoints; tests must install deterministic transport/credential
fakes before client construction. The existing conftest adds import paths but does not isolate those
environment variables. Use fake time for retries; do not call cloud services from contract tests.

| ID | Future command/procedure | Additional prerequisite | Required result, beyond exit code |
| --- | --- | --- | --- |
| V01 | `pytest tests/contract/test_llm_managed_identity.py tests/contract/test_llm_model_routing.py tests/contract/test_llm_fallback.py tests/contract/test_llm_confidence.py tests/contract/test_llm_circuit_breaker.py tests/contract/test_llm_telemetry.py -v -rA` | Add the missing boundary assertions described by the linked AUD tasks first. | AAD-only config, actual routing/settings, fallback/review gates, one recovery probe, token limits and real metric emissions are asserted; skips are not accepted as completed coverage. |
| V02 | `pytest tests/contract/test_foundry_chat_client.py tests/contract/test_foundry_chat_client_aoai.py tests/unit/test_content_safety_pipeline.py -v -rA` | Use actual FoundryResponse shape and fake SDK transport; extend beyond protocol/URL shape tests. | Resolved deployment, correlation, timeout/retry propagation, gateway refusal and safety reason/language cases are observed. |
| V03 | `pytest tests/contract/test_risk_assessment_escalation.py tests/contract/test_monitoring_escalation.py tests/contract/test_llm_confidence.py -v -rA` | Generation fixtures and fake downstream sink must exercise the whole decision path. | No safety-critical handoff below the resolved threshold, including 0.65; exact-threshold behavior and fallback adjustments are verified. |
| V04 | `pytest tests/integration/test_llm_integration.py -v -rA` | Expand the current legacy-mock suite to actual application composition and all five roles; proposed dispatcher test must be run additionally when created. | Config-to-transport-to-safety-to-domain-to-audit assertions, malformed structured output, concurrency, recovery and budget behavior. |
| V05 | `pytest tests/contract/test_llm_logging.py -v -rA` | Remove the fake's self-emitted expected log and capture actual client/mixin/audit output. | Originating correlation, actual deployment, categorized reason, UTC timestamp and real attempt count survive the full path. |
| V06 | `bicep build infra/main.bicep --stdout`; `bicep build infra/modules/azure-openai.bicep --stdout`; `bicep build-params infra/parameters/dev.bicepparam --stdout`; `bicep build-params infra/parameters/production.bicepparam --stdout` | Installed supported Bicep CLI and separately approved effective configuration; these builds may require module availability. | No compile failures/cycles; inspected output has intended model/version/SKU, region bounds, 30/60 or 120/240 quotas, stable resource names, keyless roles and diagnostics. Compilation is not deployment proof. |
| V07 | `pwsh -NoProfile -File scripts/verify-carveout.ps1 -RegistryPath infra/parameters/foundry-carveout.yaml -WhatIfPath <approved-local-what-if.json> -Strict` | Replace placeholder with an independently approved local plan artifact; script prerequisites include Python/PyYAML. Resolve deployment-name versus model-name comparison before treating the gate as complete. | Effective model/version/region/SKU matches approvals; negative fixtures are refused. Current CD omits WhatIfPath, so registry-only success is insufficient. No cloud query is authorized by this command listing. |
| V08 | `pytest tests/simulation/test_quickstart_live_llm_rehearsal.py -v -rA` plus the resolved staged outage/telemetry procedure | Explicit authorization for staging identities/resources and costs; update the rehearsal to Foundry and all five roles first; define load and measurement start/end points. | Five non-skipped live calls under 10s, controlled outage fallback within 15s, metrics visible within 60s, observed deployment/region/SKU and safe recovery. Save sanitized measured results with revision/configuration. |
| V09 | `pytest tests/contract/ tests/integration/ -v -rA` and the corrected quickstart on an authorized clean checkout | Full dependency set and explicit approval for broader execution; perform V01-V07 first and do not run stale guide commands blindly. | Retained full run/skips/failures, compiled IaC and reproducible offline/live guide results satisfy T041/T042 prospectively, not retroactively. |
| V10 | `pnpm --filter @ama/web test` | Existing web dependencies and focused review-binding tests in the existing unit test home; no app build is necessary for the unit slice. | Actual recommendation confidence, sources, rationale and review state render; decision binds to the correct tenant/version, with missing-context and stale-version cases. |
| V11 | Documentary comparison and local link/schema checks on the authorized future evidence changes | Named Risk Manager/SME records, dated approvals and original evidence preserved; no new grading/delegation assumed. | Current treatment evidence, genuine approval role/date, resolved persona references and hypothesis evidence or explicit deferral; authored labels alone cannot pass. |

The report-only checks performed in this audit are text-level task/checkbox coverage and local path/line
link validation plus editor diagnostics on the authored Markdown. Those checks do not import product
code, execute tests, certify infrastructure, authenticate approvers or establish runtime acceptance.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 014 only. Three parallel technical reviews examined runtime
safety, infrastructure/model alignment, and telemetry/evidence. No behavior-changing source edit was applied because
the active contract is not yet coherent: the repository's Foundry cutover supersedes the legacy Azure OpenAI
transport, while retry/404 semantics, model/version/SKU/region policy, telemetry inventory, confidence thresholds,
and offline-versus-configured readiness remain contradictory or incomplete.

| Area | Result | Evidence / remaining limitation |
| --- | --- | --- |
| Foundry supersession boundary | Clarified for this review. | Legacy account/client/API-key deployment assumptions are superseded by the Foundry cutover; managed identity, safety/fallback, confidence gates, per-agent settings, audit/correlation, AU persistence/telemetry, and approved carve-out controls remain active obligations. |
| AUD-014-001–013 | Contract-blocked source work. | Output safety bypasses, confidence propagation, readiness, per-agent settings, retry/deadline, circuit-breaker, token, metadata, and fallback-audit repairs require the AUD-014-019 policy decisions first. |
| AUD-014-014–023 | Partial/evidence-gated. | Telemetry/budget wiring and documentation corrections may be source work after contract approval; live latency, exporter visibility, residency/SKU deployment, Risk Manager approval, SME validation, and HYP-012 evidence remain unverified. |

No model calls, staging outage, Bicep what-if, deployment, quota query, human approval, or performance evidence was
created. The report remains open pending explicit contract resolution and authorized Foundry validation.
