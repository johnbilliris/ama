# Verification checkpoint — T003 and T004 only

## Current T053-T057 checkpoint - Dev preservation verified, 2026-10-20 07:07 UTC

**Disposition:** T053-T055 complete within the approved scope; T056 blocked and
T057 partial/blocked for staging/production. **53/57 tasks are checked**, with
original T027/T030 and new T056/T057 still unchecked. This supersedes the
pre-approval stop conditions below, not historical deployment receipts.
No changed application image or infrastructure was deployed in this pass.

### Explicit composition and validation authority

The user selected **`approve raw bicep`**, approved Dev metadata collection and
bounded ARM validation/What-If, and explicitly left staging/production blocked.
The precise decision, target, exclusions and conservative 10:00 UTC authority
end are retained in
`evidence/dev-preparation/convergence-implementation-approval.json`.
The exception covers only a first-party deployment child referencing the
existing account and the RAI API/representation needed for full preservation.
It does not permit vendor edits, account-root rewrites, deployment, inference,
image publication, IAM/policy/secret operations or traffic changes.

Fresh baseline collection at **06:57:02-06:57:19 UTC** matched all deployments,
SKUs, RAI definitions, diagnostics, account controls, identity/tags, all **11**
effective assignment property sets (including the three SystemHidden entries)
and **50** inherited access assignments. The selected **27** initiative/definition
enforcement snapshots match. Parameter metadata is excluded exactly at that
comparison boundary; full fresh values are retained. The initial discrepancy
was added `parameters.effect.metadata` display text, not a rule/default/binding
change. This is not rediscovery of all 329 definitions, a new Portal observation
or a live compliance verdict. See `convergence-preservation-baseline.json`;
the earlier `convergence-preservation-refresh.json` is an intermediate observation,
not the reconciled acceptance baseline.

### Implemented preservation boundary

- `infra/modules/cognitive-services-deployment-preservation.bicep` is explicitly
  first-party. Its only writable resource is a deployment at `2026-05-01`; the
  parent is existing. Required typed `deploymentOperatingStates` pass through
  root/wrapper/Dev parameters to reasoning, drafting, simulation and embedding.
  Current capacity is independent of SKU capacity; Running/Paused is explicit
  and never silently defaulted. Models/versions, names, SKU/capacity, upgrade
  behavior and policy attachments retain the observed values.
- The three RAI resources use the approved `2026-05-01` representation and
  preserve **exact wire action `NONE`** in both observed filters. No
  `NONE`/`None` equivalence or omission default is assumed. Blocking mode,
  Microsoft.DefaultV2 base, High Violence thresholds and enabled/blocking/source
  fields are unchanged. System-managed policies are referenced, not rewritten.
- The complete serialized chain remains reasoning RAI/deployment, drafting
  RAI/deployment, simulation RAI/deployment, then embedding. The existing
  diagnostic snapshot and empty principal list remain intact.
- Pinned 0.18.0 source/license hashes pass unchanged. Published 0.19.x's missing
  inputs were not bypassed by editing vendor or deploying its account root.
  The narrow exact-API BCP081 suppressions acknowledge the installed type
  bundle's absence; actual ARM validation/What-If supplies the target check.
  See the current approved exception in `avm-compatibility.md`.

### Actual local and target checks

Twelve strengthened compiler cases failed before the infrastructure fix:
missing current capacity/state, eight independent operating-state cases and
complete action comparisons for all three policies. The revised comparisons
exclude only known non-input deployment observations (`capabilities`,
`provisioningState`, `rateLimits`) and policy classification `type`; they no
longer whitelist a reduced mutable set or strip filter actions. Unexpected
other baseline properties therefore fail comparison.

Actual final command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\contract\test_llm_deployment_compiled.py tests\contract\test_llm_deployment_configuration.py -q -p no:cacheprovider --tb=short
```

**60 passed in 40.85s**, using session `t054-t055-final` basetemp. Cases include
Paused/zero and independent Running/capacity propagation for all four
deployments, complete baseline comparisons, exact operation dependencies,
all nine selections, both service environments, compatibility CSV variants,
unchanged vendor bytes and checked-in ARM/compiler equality. Type imports
produce ARM languageVersion 2.0 symbolic resources/references; the evaluator
resolves actual symbol/resource identities rather than substring proxies.
An intermediate six-case failure exposed old test-helper assumptions about
resource-ID dependency strings; no production dependency was removed to satisfy it.

Root/wrapper Bicep builds and Dev build-params exit 0; existing ARM files were
compiler-regenerated, never hand-edited. Existing unrelated unused/security
warnings remain; no new unsuppressed warning remains in the new child.
Ruff check and format check pass the changed compiler test.
Existing PSRule 2.9.0 / Rules.Azure 1.47.0 / **Azure.Default** against only
`infra/parameters/dev.bicepparam` reports **797 Pass / zero Fail**, using the
installed Bicep path and unchanged `ps-rule.yaml`/suppressions/60-second timeout.
Existing no-matching-rule warnings are not claimed as coverage.

Actual ARM validation **07:07:08-07:07:14 UTC** exits 0 with no error.
Actual bounded What-If **07:07:14-07:07:37 UTC** exits 0, status **Succeeded**:
**8 NoChange / 45 Ignore / zero other changes**. The eight exact resources are
all four deployments, all three custom policies and existing diagnostics.
Their complete before/after payloads are equal; every delta is empty, with no
unsupported reasons, diagnostics or potential changes. The parent and
unrelated RG resources are Ignore, not approved root-template changes.
Baseline age at both operations is about ten minutes, within the 3600-second
limit and current authority window.

Exact proposal/source/baseline/approval hashes and actual receipts:
`convergence-candidate-binding.json`,
`convergence-deployments.template.json`,
`convergence-deployments.parameters.json`,
`convergence-validate.json`, `convergence-what-if.json` and
`convergence-preservation-review.json`, all under `evidence/dev-preparation/`.

### Remaining boundaries

T056 cannot populate staging/production from absent approved evidence.
Consequently T057, T027 and T030 cannot claim all-target acceptance or a full
infra scan. Existing unrelated root-template drift remains isolated; only the
bounded wrapper was submitted for validation/preview. No new registry/release,
residency, inference-budget or traffic authority is inferred. GlobalStandard
is preserved, not relabeled AU-only inference. Existing zero-business-traffic
application revisions and ARM64-local/remote-only-AMD64 policy are untouched.
The optional after-implementation verify hook is reported separately, not
represented as executed.

## Historical pre-approval T053-T057 checkpoint - 2026-10-20

**Disposition:** T053 complete locally; T054-T057 blocked, not implemented or
accepted. Including the original T027/T030 partial tasks, 51/57 tasks are
checked. This section supersedes earlier local routing-completeness claims
only for the demonstrated deployment-qualified endpoint defect. Existing Dev
images/revisions have not been rebuilt or redeployed.

### T053 correction and actual request evidence

The new tests first reproduced all 31 new cases as failures. A configured
`/openai/deployments/synthetic-live-r` path overrode the common client's
resolved simulation/drafting destination. Installed OpenAI transports also
exposed duplicated deployment/account paths in MAF and the controller.

`apps/agents/common/llm_config.py` now validates the captured HTTPS endpoint
before affected-path resolution and normalizes a supported deployment-qualified
AOAI URL to its account endpoint. Invalid URI/operation paths, embedded
credentials, query strings and fragments fail with the existing configuration
error without echoing credentials. Native Foundry project paths are retained.
The common client's `_endpoint_for` uses the same normalization, then appends
the selected deployment and caches by effective URL; AOAI classification uses
the actual hostname rather than a substring anywhere in the URI.

No MAF/controller transport replacement was needed: both already consume the
shared resolved endpoint. MAF retains its account-level Responses URL and model
selection; the controller's installed OpenAI streaming client now uses the
simulation deployment URL. All six dispatcher roles retain simulation-only
requests and proved attempt evidence. Tests also cover matching-qualified
endpoints, both AOAI host families, immutable snapshots, repeated calls/client
caches, credential/gateway failures, unknown/failed outcomes and owning-writer
admission rather than asserting SDK construction alone.

**Actual validation commands and results:**

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$routingSelectors = @(
  'tests\unit\test_llm_inference_attempt_evidence.py'
  'tests\contract\test_llm_deployment_routing.py'
  'tests\integration\test_llm_deployment_provenance.py'
  'tests\integration\test_llm_deployment_routing.py'
  'tests\unit\test_llm_adapter_snapshots.py'
  'tests\unit\test_llm_shared_resolver.py'
  'tests\unit\test_llm_deployment_routing.py'
  'tests\unit\test_llm_foundation_contracts.py'
  'tests\contract\test_foundry_chat_client_aoai.py'
  'tests\contract\test_foundry_chat_client.py'
  'tests\contract\test_foundry_gateway_fail_closed.py'
  'tests\contract\test_llm_model_routing.py'
  'tests\contract\test_llm_deployment_provenance.py'
  'tests\unit\test_llm_provenance_admission.py'
  'tests\contract\test_llm_deployment_map_compatibility.py'
)
.\.venv\Scripts\python.exe -m pytest @routingSelectors -q -p no:cacheprovider --tb=short
.\.venv\Scripts\python.exe -m pytest tests\unit\test_llm_deployment_preflight.py tests\contract\test_llm_deployment_configuration.py -q -p no:cacheprovider --tb=short
```

The first command passed **683 cases in 13.14s**; the second passed **171 cases
in 69.83s**. Actual runs additionally used distinct `--basetemp` directories in
the session workspace (`t053-green` and `t053-preflight`). Before the fix, the
three changed test modules selected with
`-k 'qualified_endpoint or invalid_endpoint'` failed **31 cases**. These are
offline synthetic SDK/HTTP transports with the existing network guard, not
Azure inference or live preservation acceptance.

Ruff check and format check pass all five changed Python files:
`apps/agents/common/{llm_config,foundry_chat_client}.py`,
`tests/unit/test_llm_inference_attempt_evidence.py`,
`tests/contract/test_llm_deployment_routing.py` and
`tests/integration/test_llm_deployment_provenance.py`.
Configured mypy passes the two source modules. Existing adjacent audit
example/type-count failures from the preceding assessment were not included
in these focused selectors, hidden, repaired or claimed as passing.

### T054-T057 stop conditions and public-source review

| Task | Current evidence and remaining gate |
| --- | --- |
| T054 | Pinned child 0.18.0 omits `currentCapacity`/`deploymentState`. The public registry lists 0.19.0 and 0.19.1; reviewed tagged child source still lacks both inputs. Exact-API documentation exposes them and does not prove safe omission. Stop for a compatible verified composition or explicit narrow alternative-composition approval and applicable fresh baseline/governance evidence; do not edit pinned vendor bytes or deploy the account root. |
| T055 | The exact newer RAI input documents action `None`; retained observed filters contain `NONE`. Documentation does not establish omission/casing/default equivalence. An explicitly approved supported representation/API change or authoritative approved equivalence is required. The existing compiler test's action-stripping comparison is not full protection acceptance. |
| T056 | All retained baseline/governance/collection approvals are Dev-specific. Staging/production parameter files have no nine approved selections and no corresponding approved baseline/collection bundle. Do not infer their subscription/account identities or copy Dev settings. |
| T057 | Depends on T054-T056 and each target's gates. No target-bound complete preservation acceptance, Bicep regeneration or full PSRule success is claimed. Earlier unrelated root-template drift remains an explicit stop, not work to apply opportunistically. |

Public references checked without Azure resource operations:

- [Registry tags](https://mcr.microsoft.com/v2/bicep/avm/res/cognitive-services/account/tags/list).
- [0.19.0 tagged deployment child](https://github.com/Azure/bicep-registry-modules/blob/55c62d45eaf6675c09bf663616c3e7fdd8c4560f/avm/res/cognitive-services/account/deployment/main.bicep).
- [0.19.1 tagged deployment child](https://github.com/Azure/bicep-registry-modules/blob/f1f4ba28698437d9a683d68bf181341ad3547e48/avm/res/cognitive-services/account/deployment/main.bicep).
- [Exact deployment input API](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/2026-05-01/accounts/deployments).
- [Exact newer RAI input API](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/2026-05-01/accounts/raipolicies).

These interface checks are not verification of a replacement OCI source archive
or adoption of a new pin. No Bicep/vendor/generated ARM or target parameter
file was changed. No Azure read/write, What-If, inference, image build/push,
traffic change, permission/secret operation or commit was executed. The local
ARM64-only rule and remote-only AMD64 deployment rule remain unchanged.

## Current Dev dependency verification - 2026-10-20 04:52 UTC

The separately approved bounded dependency stage is accepted at zero business
traffic. Corrected suffix `llm041-deps-20261020t044249` is Healthy in both apps,
with four started/ready replicas and zero restarts. Exact API-to-agents binding,
complete expected application hashes, existing pull roles and unchanged
Foundry/account/RAI/diagnostic/Search-service protection comparisons pass.

The actual API pipeline-status Redis client authenticates through its refreshing
Entra provider. The actual API retrieval factory resolves the configured corpus;
the unchanged agents image's configured retrieval metadata also succeeds.
The repository-defined empty index and alias exist; zero documents were
uploaded. Earlier runtime failures exposed and fixed the MSAL resource/scope
distinction and API Search alias-version incompatibility before inference.
76 focused regressions, Ruff, Redis mypy, the explicit amd64 build, source-byte
checks, isolated held startup and runtime dependency closure pass.

Three actual additional tier calls pass within the original budget: eight
maximum aggregate reservations consumed, including uncertain historical
attempts. Only one simulation reservation remains. No new grants, secret-value
operations, Foundry resource writes, business invocations or promotion.
An empty corpus is not grounded business acceptance; ingestion and business
rollout still require their own authority/evidence. T027/T030 remain partial
for other environments. See `dependency-final-acceptance.json` and
`rollout-evidence.md`; prior checkpoint sections below retain historical scope.

## Current unheld Dev verification - 2026-10-20 03:53 UTC

The later explicit unheld/inference approval supersedes only the relevant
held-stage restrictions below. Corrected revision suffix
`llm041-val-20261020t033002` is Healthy in both apps. All four observed
replicas started and became ready with zero restarts. Exact API-adapter to
internal agents-revision connectivity passes; candidate traffic is zero.
All complete writable-state hashes and independently compared Foundry
deployments, controls, RAI and diagnostics match expected preserved state.

Three app-identity synthetic requests actually succeeded, one per tier:
128-token caps, four generated tokens each, no business data/tools and zero
SDK retries. Actual provider identity is `gpt-5.4-2026-03-05`. Conservative
reservations, including two earlier failed handshakes, total at most five of
nine permitted requests. The shared adapter's request-local evidence reports
attempted/succeeded rather than inferring success from configuration.

64 focused tests and Ruff pass. A regression now resolves complete prepared
routing through the real shared resolver; missing/foreign observed region fails
closed. Startup and TCP readiness are not comprehensive business readiness:
Search has no corpus index, and the existing API Redis client omits Entra
authentication despite a successful same-identity authenticated PING.
Cosmos and actual Blob container authorization pass after targeted follow-up.
Business release remains blocked; no new image/schema provisioning or traffic
promotion was authorized by this stage. T027/T030 remain partial across
environments. See `unheld-final-acceptance.json` and `rollout-evidence.md`.

## Latest resumed Dev checkpoint — 2026-10-20

The historical sections below retain their original checkpoint boundaries.
Current application-only work adds held startup/readiness, private complete
configuration comparison and exact secret-preserving JSON Merge PATCH
preparation. 57 focused tests pass; Ruff and four-module mypy pass.
Both normal Docker entrypoints pass isolated-network held initialization and
graceful shutdown. These are packaging/containment checks, not live model calls.

The exact vetted pair is published to Dev ACR and authoritative manifest/config
digests are verified. The two approved app principals have AcrPull at that ACR
only. All four Foundry deployments and captured protections remain unchanged.
The user explicitly approved held application staging and PATCH-specific
validation. Both resulting revisions are now provisioned with two Running,
successfully started replicas each, zero restarts and intentional held readiness
false. Full expected writable-state hashes match after probe-type ordering
normalization; all Foundry protections remain unchanged. Old named revisions
retain 100% traffic and the held candidates receive zero business traffic.
No secret-value operation or Foundry write occurred. Unheld startup, inference
and business promotion are not approved.
See `rollout-evidence.md` and `.azure/deployment-plan.md` for current operational
scope/proof. T027/T030 remain partial for missing staging/production evidence;
do not convert Dev observations into another environment's acceptance.

## Authority, environment and result

- Date: 2026-10-18. Authorisation: **“Resume — T003–T004 only, then checkpoint”**.
- Repository root: `C:\code\ama`. Paths below are repository-relative to that absolute root.
- Actual branch: `model-upgrade-chat-sumlation`, retained. The prerequisite script's feature association is not a branch-switch instruction.
- Prerequisites: `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks` returned `C:\code\ama\specs\041-llm-deployment-routing` and research, data model, contracts, quickstart and tasks.
- Read-only gates: `checklists/requirements.md` **16/16 checked**, `checklists/routing-rollout.md` **36/36 checked**; zero unchecked. H1 acceptance and the historical T002 stop are retained, not rewritten.
- T003: **complete — inventory/evidence only**. T004: **complete — existing baseline and byte fingerprints only**.
- Existing baseline: **94 passed, 0 failed, 0 errors, 0 skipped, 0 deselected**, one dependency warning, 3.79 seconds. This is not feature-041 acceptance.
- **STOP before T005.** No new fixtures, acceptance tests, application/IaC/configuration/model changes, package installation, Azure operations, inference, branch changes or commits.
- `.gitignore` and `.dockerignore` already cover the Python/Node build, cache, environment and secret patterns needed here. No setup/ignore changes are required or authorised for this documentation-only checkpoint.
- No coverage percentage is claimed. The constitution supplies no numeric coverage threshold.

## T003 — closed request and caller inventory

### Search boundary and counting rules

Read the eight T003 seed files and traced their callers under `apps` and `packages`, including lazy SDK imports, injected callables, factory construction and actual request submission sites. The seven production SDK request surfaces are:

| Surface | Exact boundary | Current selection / retained boundary |
| --- | --- | --- |
| Common synchronous chat | `apps/agents/common/foundry_chat_client.py:437` `LiveFoundryChatClient.chat_complete` → `client.complete(**kwargs)` at 481 | `_resolve(model_key)`; map precedes live tier env, then base key. AOAI per-deployment endpoint and `model=deployment`; AAD, gateway, retries/cache/deadline retained. |
| Common asynchronous streaming chat | Same file, `chat_complete_stream` at 520 → async `client.complete` at 561 | Same destination resolver; `stream=True`, per-request timeout and streamed chunks. No in-repository production caller of this method was found; it is an existing supported adapter, not evidence of an enabled flow. |
| MAF chat | `apps/agents/maf_runtime/chat_client.py:80` `build_azure_openai_chat_client` → `OpenAIChatClient(model=deployment, ...)`; `apps/agents/maf_runtime/agents/_factory.py:265` `run_maf` → `await agent.run(body)` at 277 | Endpoint/map via `_resolve_endpoint_and_deployment`. The request occurs inside the external MAF adapter, not at factory construction. Preserve public factory args, shared credential/token provider, AAD scope and ValueError boundary. |
| Controller chat | `apps/api/app/services/simulation/controller_service.py:518` `_stream_from_azure` → `AsyncAzureOpenAI.chat.completions.create` at 690 | Explicit simulation env wins; currently falls back to simulation/reasoning model key CSV. Three-round tool loop, `stream=True`, tools and `tool_choice="auto"`. Every emitted round is a separate request. |
| Evaluation chat | `apps/eval-runner/src/ama_eval/foundry_client.py` `FoundryClient.complete` → `ChatCompletionsClient.complete` | Per-call `deployment=` or exact `model_id@version`, then base key. Independent package/parser (currently last-write-wins). `runner.py` constructs the client and its `_foundry_call` supplies registry version/parameters to the orchestrator. Not a chat-tier selector. |
| Ingest embeddings | `apps/ingest-runner/src/ama_ingest/embedder.py` `FoundryEmbedder` → `AzureOpenAI.embeddings.create` at 296 | Actual code uses AzureOpenAI, despite older EmbeddingsClient docstrings. Exact/default `text-embedding-3-large@1`, then base lookup; 3072 dimensions, AAD, injected embed seam and batching/retry semantics retained. Independent ingest package/parser. |
| Query embeddings | `apps/agents/common/foundry_query_embedder.py:130` `_embed_sync` → `AzureOpenAI.embeddings.create` at 132; `embed_query` bridges to a thread | Direct `EMBEDDING_DEPLOYMENT_NAME`, default `text-embedding-3-large-ama`, 3072 dimensions. Not routed through the chat-tier enum or CSV. |

`apps/agents/common/llm_client.py` constructs the common sync seam and passes `purpose` through `foundry_model_key_for`. Its `_call_llm_with_retry` also retains a direct AzureOpenAI SDK branch at line 311 **for hermetic legacy tests only** when the Foundry endpoint/seam is absent. That is an eighth, test-compatibility boundary, not an additional production SDK surface and not permission to restore production `AZURE_OPENAI_*` fallback.

### Production caller closure and SC-001 population

The following **23 concrete production caller/role entries** reach the tiered transports when their existing enablement/configuration permits. A disabled optional caller is still inventoried; this checkpoint does not enable it.

| ID | Caller / method / route | Designated tier and downstream boundary |
| --- | --- | --- |
| C01 | `apps/agents/risk_assessment/agent.py:165`, `RiskAssessmentAgent.generate_assessment` | reasoning → mixin → LLMClient → common sync |
| C02 | Same file:439, `_generate_recommendation` | reasoning → same chain |
| C03 | Same file:545, `recommend_public_alert` | reasoning → same chain |
| C04 | Same file:781, `create_app.health` LLM probe | reasoning → LLMClient → common sync; keep optional health behaviour |
| C05 | `apps/agents/monitoring/agent.py:109`, `MonitoringAgent.summarize_signal` | drafting → injected LLMClient → common sync |
| C06 | Same file:282, `evaluate_escalated_signal` | reasoning → `asyncio.to_thread(generate_response, ...)` → common sync, **not** common streaming |
| C07 | `apps/agents/monitoring/indicator_analysis.py:95`, `analyse_cross_domain_correlations` | drafting → LLMClient → common sync |
| C08 | `apps/agents/communication/translator.py:187`, `MultilingualTranslator._generate_content` | drafting → mixin → LLMClient → common sync |
| C09 | Same file:308, `back_translate_and_score` | drafting → same chain, preserve template-skipping/embedding-score behaviour |
| C10 | `apps/agents/evacuation/pipeline.py:1801`, `EvacuationProcessingPipeline._stage_8_plan_summary` | reasoning → `_llm_generate_fn` injected from `evacuation/agent.py` → mixin/common sync |
| C11 | `apps/agents/evacuation/runtime.py:145`, `ThreadedDependencyHealthMonitor.probe_once` nested probe | reasoning → agent's LLMClient → common sync; preserve bounded health probe |
| C12 | `apps/agents/resource_allocation/pipeline.py:845`, `AllocationProcessingPipeline._generate_summary` | **reasoning**, despite the agent config's drafting default; injected by `resource_allocation/agent.py` → mixin/common sync. Inventory is based on actual call args, not labels. |
| C13 | `apps/agents/maf_runtime/agents/monitoring_agent.py` → inherited `MafAgentFacade.run_maf` | YAML `monitoring.yaml` currently reasoning → factory → actual MAF chat request |
| C14 | `apps/agents/maf_runtime/agents/risk_assessment_agent.py` → inherited `run_maf` | YAML `risk_assessment.yaml` currently reasoning → same request chain |
| C15 | `apps/agents/maf_runtime/agents/communication_agent.py` → inherited `run_maf` | YAML `communication.yaml` currently reasoning → same request chain |
| C16 | `apps/agents/maf_runtime/agents/resource_allocation_agent.py` → inherited `run_maf` | YAML `resource_allocation.yaml` currently reasoning → same request chain |
| C17 | `apps/api/app/services/simulation/controller_service.py`, `stream_turn` → `_stream_from_azure` | simulation → direct async OpenAI streaming; every initial/tool-followup request |
| C18 | `apps/agents/dispatcher/agent.py:146`, `POST /monitoring/invoke` | simulation → common sync |
| C19 | Same handler, `POST /planning/invoke` | simulation → common sync |
| C20 | Same handler, `POST /risk-assessment/invoke` | simulation → common sync |
| C21 | Same handler, `POST /communication/invoke` | simulation → common sync |
| C22 | Same handler, `POST /evacuation/invoke` | simulation → common sync |
| C23 | Same handler, `POST /resource-allocation/invoke` | simulation → common sync |

Dispatcher currently chooses `AZURE_AI_SIMULATION_MODEL_KEY or AZURE_AI_REASONING_MODEL_KEY or "simulation"` at startup, then calls `chat_complete` at line 161. These six role entries are separate acceptance paths even though their handler is shared. Their API chain is `production_invoker` in `apps/api/app/services/simulation/sub_agent_invoker.py` → the six files `sub_agents/{monitoring,planning,risk_assessment,communication,evacuation,resource_allocation}_adapter.py` → `sub_agents/_base.py:call_agent` → the matching kebab-case URL. Preserve all URLs, role prompts, citations, tenant header, invocation IDs and AIIMS mappings.

`apps/agents/maf_runtime/agents/evacuation_agent.py` overrides **both** `run_maf` and `run_legacy` with `_run_deterministic`/the operational evacuation pipeline. Its YAML also says reasoning, but counting it as a fifth independent generic MAF inference would be false. Any optional summary/probe calls are C10/C11. MAF legacy/shadow branches of the other facades reuse the already listed common callers; shadow does not establish a new routing rule.

To avoid omitting supported but currently uncalled adapter paths, acceptance also includes these **five capability entries**:

| ID | Entry to exercise with a fake request transport | Tier |
| --- | --- | --- |
| A01 | Direct common `chat_complete(model_key="simulation")`, separately from role entry wiring | simulation |
| A02 | Direct common `chat_complete_stream(model_key="reasoning")` | reasoning |
| A03 | Direct common `chat_complete_stream(model_key="drafting")` | drafting |
| A04 | Direct common `chat_complete_stream(model_key="simulation")` | simulation |
| A05 | MAF factory **and actual adapter request**, with `model_tier="drafting"` | drafting |

**Precise SC-001 acceptance denominator: 28 named paths (C01–C23 + A01–A05) × 6 CSV orderings = 168 path/order cells.** This deliberately retains separate caller-wiring checks even when they share a transport; one direct adapter test cannot stand in for all callers. Six orderings are R-D-S, R-S-D, D-R-S, D-S-R, S-R-D and S-D-R, with three distinct destinations and one shared model/version. Repeated requests/tool rounds must all select the same designated tier within their cell; one wrong request fails that cell. Do not multiply cells by token chunks, retries, tool rounds or shadow invocations, or omit callers on the basis of shared code.

For adapter review, the same inventory projects onto **15 tier/transport/role combinations**: common sync R/D/S (3), common stream R/D/S (3), MAF R/D (2), controller S (1), dispatcher roles S (6). This is a useful secondary matrix, **not a smaller replacement denominator**. Map each C/A ID to request-boundary evidence in T010/T020/T021. Factory/resolver success alone is insufficient; observe SDK request `model` and AOAI deployment URL where applicable.

**Feature acceptance now: not executed; 0/168 cells demonstrated by feature-specific tests.** This is an evidence-completeness count, not a measured routing failure rate. No fake-transport coverage was implemented by writing this inventory. T009–T011/T020 must add the tests; T021 records their actual outcomes. Invalid maps, zero-call failures, metadata association and simulation/live isolation are additional SC-002/SC-003/SC-004 obligations, not ways to reduce SC-001's denominator.

### Supported compatibility consumers and exclusions

- Eval: `apps/eval-runner/src/ama_eval/runner.py` → `FoundryClient.complete`; explicit per-run deployment or unambiguous exact/base coordinate remains supported. The tier-permutation denominator does not assert a tier for eval; ambiguous omitted coordinates must be rejected, while deliberate per-run mappings remain valid. T011/T018 cover its independent parser without importing another app.
- Ingest: `apps/ingest-runner/src/ama_ingest/__main__.py` constructs `FoundryEmbedder`, then the pipeline embeds chunks. Keep default key/model, dimensions and exact/base entry; T011/T019 cover parser conformance without cross-app imports.
- Retrieval: `apps/agents/common/retrieval_client.py` → `build_query_embedder` → `FoundryQueryEmbedder`; controller default retrieval also uses that builder. `apps/ingest-runner/src/help_snapshot/embedder.py:_embed` uses the same builder via `run_async`; dry-run/absent-client zero vectors are existing behaviour, not chat or proof of inference. `communication/translator.py:_embed` consumes an injected embedding function, not another SDK routing implementation.
- Legacy common/test injection: `LLMClient(chat_complete=...)`, `LLMClientConfig`, direct Foundry `deployments=`/credential seams, exact `model@version` and base keys remain supported where unambiguous. Preserve gateway, managed identity, error types, timeouts and no production fallback to test-only settings.
- `apps/agents/common/llm_strategies.py` accepts generic supplied callables; it has no SDK construction or new production tier choice. `planning` is deterministic outside the simulation dispatcher.
- **Help is not enabled**: `apps/api/app/api/routes/help_chat.py` captures `HELP_FOUNDRY_LIVE` (default 0). `apps/agents/help_assistant/agent.py:run_chat_turn` raises `NotImplementedError`; the existing grounded/offline paths do not invoke an LLM. Preserve this gate/stub; do not invent a live Help acceptance path.
- **Telemetry injection is an optional callable, not a discovered common SDK caller**: `apps/api/app/api/routes/simulations_036.py` reads `app.state.telemetry_injection_llm_call`; the repository has no assignment wiring it to a production SDK. `apps/agents/simulation_telemetry_injection/{handler,llm_client}.py` consume the injected callable or deterministic fallback. This corrects the plan's provisional “inherit common routing” assumption with factual inventory evidence only. Keep the seam disabled/unwired; cassette/optional staging tests are not production routing acceptance.

### Concrete existing test nodes and remaining gaps

All nodes below exist. Only the ten-module population in T004 was executed here; other nodes are inventory pointers for later authorised regression work, not passing claims.

| Area | Existing concrete node(s) | What it does not prove |
| --- | --- | --- |
| Common sync/error | `tests/contract/test_foundry_chat_client.py::test_chat_complete_timeout_maps_to_transport_error` | No complete tier/order matrix |
| Common stream | Same module `::test_fake_implements_protocol` and `::test_foundry_stream_chunk_is_frozen_dataclass` | Fake/protocol shape is not LiveFoundry async destination coverage |
| Wrapper | `tests/contract/test_llm_logging.py::test_llm_logging_with_real_wrapper_and_transport_double`; `::test_llm_wrapper_fails_when_foundry_response_lacks_deployment_id` | No per-caller closure or immutable snapshot proof |
| Old tier behaviour | `tests/contract/test_llm_model_routing.py::TestModelRouting::test_reasoning_purpose_routes_to_reasoning_deployment`; `::test_drafting_purpose_routes_to_drafting_deployment` | Config lookup is not SDK request routing |
| Endpoint/alias | `tests/contract/test_foundry_chat_client_aoai.py::test_endpoint_for_appends_openai_deployments_path_on_aoai`; `::test_resolve_honours_simulation_tier_env_var`; `::test_resolve_falls_back_to_csv_when_tier_env_var_unset` | Resolver-only, no isolation/permutations |
| Gateway | `tests/contract/test_foundry_gateway_fail_closed.py::test_gateway_deny_fails_closed_for_any_supported_message_text` | Not submitted-request evidence |
| Fallback/deadline | `tests/contract/test_llm_fallback.py::test_deadline_expiry_uses_template_fallback_without_outbound_call`; `::test_safety_fallback_when_content_flagged` | Not new provenance admission counts |
| Managed identity | `tests/contract/test_llm_managed_identity.py::TestManagedIdentityAuth::test_client_init_uses_token_provider_not_api_key` | Inventory only, not run here |
| Circuit breaker | `tests/contract/test_llm_circuit_breaker.py::TestCircuitBreakerTransitions::test_closed_to_open_after_threshold` | Inventory only, not run here |
| Monitoring callers | `tests/unit/test_monitoring_pipeline.py::TestPipelineSummarisation::test_llm_summary_with_content_safety_pass`; `tests/contract/test_monitoring_escalation.py::TestMisinformationClassificationOutcomes::test_llm_timeout_holds_for_review`; `tests/unit/test_indicator_analysis.py::TestLLMEnrichment::test_llm_enrichment_with_content_safety_pass` | Injected caller behaviour, not shared-model destinations |
| Communication callers | `tests/unit/test_communication_translator.py::TestDraftingPrompt::test_prompt_contains_bounded_source_context_and_configured_budget`; `::TestBackTranslateAndScore::test_semantic_embedding_score_uses_back_translation` | Not feature routing/embedding compatibility |
| Evacuation probe | `tests/unit/test_evacuation_runtime.py::TestDependencyHealthMonitor::test_slow_probe_is_bounded_and_updates_cached_offline_state` | Not a new live or MAF request |
| Dispatcher | `tests/unit/test_aud021_privacy_classification_and_dispatcher.py::test_dispatcher_non_au_gateway_denial_has_no_outbound` | Its fake increments `chat_complete` once and raises gateway denial; despite its name it does not observe an outbound SDK transport or cover six roles |
| Controller | `apps/api/tests/test_simulation_chat_controller_wiring.py::test_simulation_chat_controller_has_all_sub_agents_wired`; `tests/unit/test_simulation_controller_safety.py::test_controller_refuses_jailbreaks` | Wiring/safety, not direct SDK/tool-round routing |
| Eval | `tests/unit/eval/test_foundry_failures.py::test_parse_deployment_map_handles_csv`; `::test_foundry_client_uses_deployment_for_known_model`; `::test_foundry_client_uses_model_inference_endpoint`; `::test_foundry_client_uses_max_completion_tokens_for_gpt5` | No strict conflicting-map conformance |
| MAF / embedding gap | No existing tests directly exercising `build_azure_openai_chat_client`, `FoundryEmbedder` or `FoundryQueryEmbedder` request routing were located in the searched test population | T010/T011/T020 must add real fake-SDK boundary coverage; do not count unrelated tests as coverage |
| Historical audit/schema | `tests/contract/test_audit_record_shape.py::test_examples_validate_against_schema[grounded_inference]`; `tests/contract/test_audit_record_amend_loop_fields.py::test_spec_and_mirror_byte_equal` | Old shape only |
| Historical replay | `tests/contract/test_audit_replay_fidelity.py::test_sampled_byte_replay_meets_95_percent_over_one_month_window`; `::test_replay_key_is_deterministic_under_repeated_construction[1]`; `tests/integration/test_audit_replay.py::test_replay_key_derives_byte_identical_inputs` | Synthetic replay keys, not stored Azure record recovery |
| Invocation/export | `packages/domain/tests/test_sub_agent_invocation_record.py::test_sub_agent_invocation_record_happy`; `apps/api/tests/test_lessons_capture_and_export.py::test_audit_export_produces_ndjson_gzip_and_sha256` | No new provenance compatibility yet |

### F3 disposition — exact T034/T035 reader/projection write sets

This closes the **inventory** warning, not the future reader implementation or deployment gate. The following are bounded reader-first changes, to be made only during separately authorised T034/T035. No file in these sets was edited now.

| Task | Exact future reader/projection file | Boundary and dependency |
| --- | --- | --- |
| T034 | `packages/domain/src/ama_domain/audit_record.py` | Strict Pydantic AuditRecord; add optional nullable attempt/outcome, retain required string identity and historical absence. T031 schema tests first. |
| T034 | `packages/schemas/spec_036/audit-record-llm-call.json` | Strict JSON Schema counterpart; same optional fields/enum without relaxing extra fields. |
| T034 | `specs/036-foundry-rag-grounding/contracts/audit-record-llm-call.json` | Existing byte-equal schema source/mirror paired with the preceding file by `test_spec_and_mirror_byte_equal`; update in lockstep, not historical audit data. |
| T035 | `packages/domain/src/domain/models/sub_agent_invocation_record.py` | Strict frozen invocation reader; additive identity/nullable attempt/outcome; required deployment string remains string, new unavailable writes use `unknown`. Preserve roles/AIIMS/invocation ID. T031/T033 old/new tests first. |
| T035 | `apps/api/app/services/simulation/sub_agent_invoker.py` | `SubAgentReply` dataclass/old payload boundary; nullable provenance and unknown remote evidence without assuming submission. Do not enable producers. |
| T035 | `apps/api/app/services/simulation/sub_agents/_base.py` | HTTP JSON→reply projection; parse optional fields without losing them. Preserve old response absence. Removal of obsolete role identity fallback is T042, not a claim made by this inventory. |
| T035 | `packages/domain/src/domain/models/telemetry_injection_audit_entry.py` | Existing strict per-entry details readers (`SubAgentTimeoutDetails`, `SubAgentDegradedDetails` and related existing event detail types carrying call uncertainty); add optional provenance only where the existing event carries it, retain all discriminators/extra-field rejection. `simulation/audit_writer.py` calls `validate_details` before persistence, so these readers must precede event producers. No new event kind. |
| T035 | `apps/api/app/services/simulation/lessons_capture.py` | `_build_sub_agent_responses` explicitly projects `SubAgentInvocationRecord` to report rows and currently keeps only `model_deployment`; carry the additive provenance without fabricating historical status. `_build_timeline` remains an agent-event timeline, not a model-call admission signal. |

**Write-set totals: T034 three files; T035 five files; eight distinct files, disjoint between the two tasks.** These are discovered dependencies of the existing reader tasks, not execution now or added tasks. Keep the schema-source byte-equality test and existing event-detail tests; do not enable new producers until both reader tasks and their tests pass.

Reviewed adjacent reader/replay/export boundaries that **do not need a T034/T035 edit**:

- `apps/agents/common/audit.py:replay_key`: consumes corpus SHA, prompt SHA, model version and ordered chunk SHAs only. Leave the key algorithm/historical missing-field handling unchanged; writer admission belongs to T036.
- `apps/agents/common/offline_cache.py:AuditSpool`: stores/drains whole JSON dicts, not a provenance allowlist. Preserve.
- `apps/api/app/services/simulation/audit_export.py:_to_export_dict`: serialises the full envelope/details; no field-loss projection to extend. Preserve existing carve-out review behaviour; model-name heuristics are not proof of region and are not expanded here.
- `apps/api/app/services/audit_export_service.py`: JSON serialises whole dictionaries, CSV uses incoming keys; no strict AuditRecord/sub-agent provenance whitelist. Mixed CSV row shapes remain an existing constraint, not grounds for unrelated export redesign.
- `apps/api/app/services/playback_service.py`, `apps/api/app/api/routes/{simulation_playback,audit_compliance}.py`: generic event/export pass-through, not new typed provenance filters.
- `apps/api/app/services/simulation/replay/{ndjson_reader,ndjson_writer,digest,engine}.py`: signal NDJSON/digest replay, not LLM audit rows. Leave canonical history and signal metadata projection unchanged.
- `apps/api/app/services/simulation/sse_sub_agent_events.py` projects completed/degraded events; public SSE vocabulary stays unchanged. Any later producer propagation is coordinated with T040/T042 after readers pass, not a new T035 response producer.
- `apps/api/app/services/signal_accepted_workflow.py:_emit_llm_call_timeline_events` currently keys model-call projections off `generation_method`; this is **not** proof of submission. It is a later provenance/admission integration risk, not a T034/T035 reader edit or authority to expand tasks now. Until eligible evidence is propagated, retain the designed unknown/no-inference-projection fallback and fail later acceptance rather than claim the inventory fixed it.
- Repository search found no web TypeScript/TSX or additional package JSON schema projection of `model_deployment`/`deployment_alias` requiring another T034/T035 write. No new audit/dispatcher schema mirror is invented.

F1 (optional splitting of future large tasks) remains deferred. F2 (request-bound submission hook proof or unknown fallback) remains **unproven**: SDK method entry, MAF `call_next` and HTTP invocation do not prove submission. F4 (per-target G1 parameter approvals) remains unsatisfied. F3 is dispositioned as **inventory complete, execution/compatibility pending**, without changing `review.md` or historical review artifacts.

## T004 — exact existing baseline

Executed from `C:\code\ama`, using the existing virtual environment and dependencies. No manifest/environment installation or global configuration change:

```powershell
$env:PYTHONPATH='apps\agents;apps\api;packages\domain\src'
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python.exe -m pytest tests/contract/test_foundry_chat_client_aoai.py tests/contract/test_foundry_chat_client.py tests/contract/test_foundry_gateway_fail_closed.py tests/contract/test_llm_model_routing.py tests/contract/test_llm_fallback.py tests/contract/test_llm_logging.py tests/contract/test_audit_record_shape.py tests/contract/test_audit_record_amend_loop_fields.py tests/contract/test_simulation_api_contract.py tests/contract/test_audit_replay_fidelity.py -q -p no:cacheprovider -m 'not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging and not azure_blob_worm_staging and not measurement_staging' --tb=short
```

This is the smallest module union of **quickstart §1's nine modules plus T004's replay-fidelity module**. No focused future tests from quickstart §2, staging, optional live inference or broad suite was run. Pytest returned exit code 0. A separate read-only `--collect-only -q -p no:cacheprovider` with the same ten paths confirmed the population is 94 nodes (1.69 seconds).

| `tests/contract/` module | Collected | Passed | Failed/errors |
| --- | ---: | ---: | ---: |
| `test_foundry_chat_client_aoai.py` | 10 | 10 | 0 |
| `test_foundry_chat_client.py` | 9 | 9 | 0 |
| `test_foundry_gateway_fail_closed.py` | 3 | 3 | 0 |
| `test_llm_model_routing.py` | 9 | 9 | 0 |
| `test_llm_fallback.py` | 5 | 5 | 0 |
| `test_llm_logging.py` | 2 | 2 | 0 |
| `test_audit_record_shape.py` | 10 | 10 | 0 |
| `test_audit_record_amend_loop_fields.py` | 22 | 22 | 0 |
| `test_simulation_api_contract.py` | 15 | 15 | 0 |
| `test_audit_replay_fidelity.py` | 9 | 9 | 0 |
| **Total** | **94** | **94** | **0** |

Pre-existing failures in this exact population: **none observed**. Introduced failures: **none observed**; no source was changed. The single pre-existing `StarletteDeprecationWarning` comes from `.venv/Lib/site-packages/fastapi/testclient.py:1` (“Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead”). It appears during collection as well. Do not install anything or change dependencies to address it within this checkpoint.

### First-write-wins expectations to replace later

- Exact obsolete node: `tests/contract/test_foundry_chat_client_aoai.py::test_parse_deployment_map_first_write_wins` (lines 105–115). Its comment says the first shared key **must** win; it asserts the first of three distinct chat destinations and separately asserts the embedding entry. T013 replaces the ambiguous-chat assertion with actionable strict conflict rejection in all orders, while retaining the embedding assertion.
- Same module's introductory first-write-wins explanation is part of that obsolete expectation; update it with T013, not now.
- `apps/agents/common/llm_config.py:foundry_deployment_map` and common `_parse_deployment_map` implement first-write-wins with `setdefault`; the controller CSV resolver returns the first match. Eval/ingest parsers instead overwrite the prior value. These are existing defects/behaviour, **not baseline test failures**.
- `test_resolve_falls_back_to_csv_when_tier_env_var_unset` is an unambiguous non-simulation exact-coordinate case, not a licence for simulation fallback; preserve legitimate legacy compatibility. `test_llm_model_routing.py` is config-only and needs only affected expectations updated in T013.
- The 10 AOAI tests passing in planning and again now are old behaviour, including the obsolete passing assertion. Neither 10 nor 94 passing tests constitute feature acceptance.

## Historical bytes — actual fixture provenance and SHA-256 baseline

Algorithm: **SHA-256 over each file's raw bytes**, including original newline/encoding bytes; no JSON reserialisation, newline normalisation or invented historical records. Fingerprints were captured before the documentation edit and checked again at checkpoint.

The audit shape/replay tests **do not load a committed historical audit-record JSON file**. Their old-format fixtures are inline:

- `test_audit_record_shape.py`: `_grounded_inference_example`, `_optout_example`, `_embedding_example`.
- `test_audit_replay_fidelity.py`: `_build_record` / seeded `_generate_window` (2,500 synthetic records, sample 250; seeds 1/7/23/101 for determinism). KQL files below are query assets actually read by that module, not history rows.
- `test_audit_replay.py`: inline `_build_record`, including a synthetic 1,000-record window.
- `test_persona_dpe_inspector_audit_replay.py`: inline records constructed through the existing writer.
- Invocation model tests: `_good` is generated with current UTC/UUID, so hashing a newly serialised sample would falsely imply stable stored historical bytes.
- Existing export tests: `_seed_audit` generates in-memory envelopes; gzip output is generated at runtime, not a committed historical bundle.

Accordingly the **six original fixture-bearing source files** are fingerprinted as the authoritative existing fixture definitions, plus the **two actually consumed KQL assets**. This proves unchanged source bytes, not the existence of archived production history. Only the two contract fixture-source modules and KQL assets participated in the 94-test run; the other source hashes are preservation anchors for the enumerated future replay/reader/export regressions.

| Existing fixture source / consumed asset | SHA-256 |
| --- | --- |
| `tests/contract/test_audit_record_shape.py` | `e4fdfe606884f3ce2fdc095a64e82af646cc7854cef72fbb4f051f7c84c2bd68` |
| `tests/contract/test_audit_replay_fidelity.py` | `cc0eea5f71f2262b752cd6c15c26a4577b2af141d5ca3d496f2f169ad1507152` |
| `tests/integration/test_audit_replay.py` | `3caa5bf2347de1608e732da10f56ae4dc28d612a480b83c2e5a91445aed9acb4` |
| `tests/integration/test_persona_dpe_inspector_audit_replay.py` | `803ea688a428ca934854262c7fb64a347279f53bfb458e31a9d702f8b32a9010` |
| `packages/domain/tests/test_sub_agent_invocation_record.py` | `90ac06ba6c46d117c815f4419427cf231ff6f542f6201986861cfc3b792c8d0d` |
| `apps/api/tests/test_lessons_capture_and_export.py` | `ef60f64f55c417193b5634c2903f04878befaef7fbf53cc1928840edd5aa74c1` |
| `tests/audit/audit_replay_fidelity.kql` | `175880927accf9ff2e58ade6bfcd9b4742a8394b82ed924f16a9533f0f9cedce` |
| `tests/audit/audit_trail_completeness.kql` | `423982d4b94704fc4341638341e7cfd14f25b35437a26cf7ae56b21c28f8bbec` |

There **are** real pre-existing committed signal-replay files. `tests/integration/test_replay_digest_sidecar_regression.py::test_committed_replay_matches_sidecar` consumes all 21 below; `tests/contract/spec039/test_demo_replay_byte_identical.py::test_demo_replay_matches_committed_sidecar` uses the eight demo files. These are signal history, **not LLM provenance rows**; fingerprint them without pretending they supply missing historical LLM records. No replay generators or fixture-writing commands were run.

Every filename in the next table is under the exact directory `fixtures/sim_replays/`; its sidecar is the exact same path plus `.sha256`. All **21/21 recorded sidecar digest values matched** the raw NDJSON SHA-256. The sidecar's own raw byte hash is separately retained, so the protected population is **42 actual files**, not just 21 digest strings.

| Existing NDJSON filename | NDJSON SHA-256 | `.sha256` file SHA-256 |
| --- | --- | --- |
| `ambulance_cad_vic.ndjson` | `a605952ef88d4e59040d37a5469bc90e75d60752566e1f5866d230a6e14ecab7` | `2e411fcb1067beb08a70a74bc567ac38328164ac1e1cdee88ea0b749a114683c` |
| `bom_cyclone_track_qld.ndjson` | `459c77dc1bf2afb6b6a27553af0676e660b5b89d376d6a1b2256a84697b3c96a` | `0e64811fd68c78e86f993119126525871b4b30d3f4b139b33d23df27bc4f0157` |
| `bom_fire_weather_fdi_vic.ndjson` | `0784b3338c2441ce4c56f6bf7e8e59e2189ebbac7982909fbdbf6887116c8933` | `219b1a68c4cc8f65b2214b05f395e470f9f7464ed469275b34754fb30941a1d4` |
| `bom_flood_gauge_nsw.ndjson` | `733f05d357e5b0e80183f0dac12e093c6dadda546a6be82a35f7573c64451127` | `7a7c6edb63f6ac9e0eb81f35752a20e420bafb4ac76ca4c81bec49733f56e485` |
| `bom_severe_weather_warning_nsw.ndjson` | `0ea0e81002acac2499eab5bb1b09b589588b5ff135a2f81d97e2e2eb73911a80` | `afe2175c7c59251db17e390d41a210e2f95819a2059c385d0be5deb583bd4539` |
| `demo_ambulance_v1.ndjson` | `c355d82a79d691ac39659de602b19d09baa024383efcd73d9dae349d4ca20eca` | `7395386111cb8dec972e9f7b89013a8d83572913ac33e43876b2ed5594ce2f20` |
| `demo_commonwealth_v1.ndjson` | `40d6b7000600afdbc14e1a1af5f750399ea08dbeb479e361f0852015a499dcf6` | `de5db435d56809056b940bfe9483b043b9f7538da345139e621999a0f64bad3f` |
| `demo_cross_sector_v1.ndjson` | `a4638851c199135b6c8c2210d8c488cdb104c0cc6775c88203eeaaa2eb9188d0` | `b53051c8031f19ce7f20d5d9e971c9611f5e7f9b375c4a639f7e11b719e71fe2` |
| `demo_fire_v1.ndjson` | `e409308e647ee99d1369a4c5f389129f173a4ad84d88a09a5cec839405ba8359` | `5c87e65ad5cabbaac39f34e1f19073493835cc6d65ba65c6c5089c1e713f7b33` |
| `demo_marine_aviation_v1.ndjson` | `e7327c0384f321939eef449396f2364176de8bbc3b7054307d6711a3f6bf1c5a` | `3a097351b79634034c63df38e6310a76a821b0659b01da662497f3a7cc32db44` |
| `demo_operational_v1.ndjson` | `0857b8ed919bca721689db90433e024b18f3e5fe8f3fe652c1f9cd618e924244` | `e38f9c66362b416a49ec6b3bb0a504fb388ea021cd11569df10779fcce791a9e` |
| `demo_police_v1.ndjson` | `ddca1a4b8ea6a08cfe30d696f8dbf917d22c70fd888b62ba79420fb1500372f4` | `91e518998fd7d417bea1d96e37f5353e52481b02acf00068bcc405cfa40f5a54` |
| `demo_ses_v1.ndjson` | `fb8a36364994eca7a67bd7d2345df31b6ce792de075b00eda8c821b67de0ab35` | `f675db4892c4360988cd310d84edb4b505e9da7371dd81cd838ec9b76cef27f6` |
| `epa_pm25_vic.ndjson` | `33623e47ce2d9347f1228a3e28a026bed5d66b88d243d14cb084a038b4784584` | `3ec392aaed29f9cb8ac01cb76e2aacc295e794dc39e84d5eb9a4a5221ccd6260` |
| `ga_earthquake_event_wa.ndjson` | `bfc04e414668480df3d214db6729a22c4c401d011eeb9dad4be56ca4d4949257` | `002a95cf57cc478f5367df05d80af307810bfa03696386164f8806c2fff860b7` |
| `ga_tsunami_threat_nsw.ndjson` | `0aff474690c7d4cfcf5ad7a68e7eb87f52761218bed788470a0b8f33a7e92744` | `94ddfd056072e80b4cf93e3cb689e776a27098e468a1c9c1e3da2d2657cf744a` |
| `sensor_telemetry_nt.ndjson` | `98e0bf317ed88b2400d0cbb902acbd9029590e62de57e29ea2bc8ffa1bfe51cb` | `d346907fbd44ec2981bc1a5951e31b92e0f670cb2777f8038292db83c3aea24b` |
| `social_chatter_au.ndjson` | `7f11794ccaf580da3ef27e2186f7c466608b073981e0267b2dc515485cf3ae1f` | `efc8c0faa19f4ff9a4a37ec7b4dbbfb9fe1c5431dd4e5c8b4027ed1fceafd980` |
| `synthetic_fallback_au.ndjson` | `17f235fb6211106f69c10780f0fbcdc433a1156ea30c070c40cab9dd4504e95f` | `0585980c597c9c2da9106a4c07f9c935f71046191a1e119f3126f56133d1e255` |
| `traffic_road_closure_nsw.ndjson` | `3c5ce7c3d8ce480ec45ef9bf7adde854e8e2ad451ba0b0caee5ff7bdced8c4ed` | `509abd374cfa91b8e85e13adcc22e619361a5bc830f48d5d757a5f907c88493f` |
| `utility_outage_qld.ndjson` | `e27c94a8a60548e436dce2b62ddeb968e547b1a4def160f81b8d9c2429b3f7d7` | `fd819a775cef69e78e1b8c59fafad444ebe6c708c23c0ee362370d751c43f097` |

Reproduce a raw-byte fingerprint without generating or modifying a fixture:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath C:\code\ama\tests\contract\test_audit_replay_fidelity.py
Get-ChildItem -LiteralPath C:\code\ama\fixtures\sim_replays -File |
    Where-Object { $_.Name -like '*.ndjson' -or $_.Name -like '*.ndjson.sha256' } |
    Get-FileHash -Algorithm SHA256
```

**Hash coverage: 50 unchanged files** = 6 inline-fixture source files + 2 consumed KQL assets + 21 committed NDJSON fixtures + 21 sidecars. Hash equality is a preservation check, not a replay-regression execution claim. Archived production LLM-record byte coverage remains unavailable because these tests have no such on-disk input; future T031/T044 must preserve the original inline fixtures and test old/new readers, not fabricate a past dataset.

## Checkpoint integrity and remaining gates

- Only `specs/041-llm-deployment-routing/verification.md` is created and only the T003/T004 checkbox bytes in `specs/041-llm-deployment-routing/tasks.md` are changed.
- The other **14 feature files** retain aggregate SHA-256 `8fb7d76135d786f763143572acc258dec882ef58259d048990945c0cce704834`, calculated over sorted `relative/path + space + raw-file-SHA256` entries joined by LF with no trailing LF; `tasks.md` and this file are excluded.
- Original `tasks.md` raw SHA-256: `1392f590def676ae116271cc001d310fcc66afb1652c0c04431ee6cade04755c`. Reversing only T003/T004 `[X]` markers reproduces that value; no other task state or task wording changes.
- Existing tracked worktree remains clean. The feature directory was already untracked and remains untracked; no add/stage/commit operation occurred.
- No T003/T004 blocker remains. Later feature acceptance is pending, F2 proof is outstanding, and the identified live model-call projection must not manufacture submission evidence. G1–G3 and later target release/migration approvals remain unsatisfied, not waived by local inventory or tests.
- Pre-hook declaration: no `before_implement` hooks registered. Post-hook: `verify` / `speckit.verify.run` is **optional** and is offered, not dispatched; the orchestrator requested no delegation/handoff and only this checkpoint.
- **T005 and all subsequent task states remain unchanged and unexecuted. Return to the orchestrator; do not auto-forward.**

## T005–T008 foundation checkpoint — 2026-10-18

**Authority:** explicit approval “execute T005–T008 only, then checkpoint”.
This section supersedes the prior checkpoint's final pending-T005 statement;
it does not change that checkpoint's historical evidence. Actual branch
`model-upgrade-chat-sumlation` retained. No T009/T010 acceptance matrix,
T012+ routing implementation, client rewiring, schema producer, IaC, Azure
operation, agent/workflow/hook invocation, staging, commit or installation.

### Foundation contracts delivered

- **T005:** `tests/fixtures/llm_deployment_routing.py` contains three synthetic
  deployments sharing one opaque model/version, six alias orderings, six raw
  conflicting-coordinate orderings, an identical duplicate CSV, absent/blank/
  partial/complete settings, and distinct method-entry/submission spy ledgers
  (sync and async submission seams). The opt-in fixture/context clears inherited
  `AZURE_AI_*` / `AZURE_OPENAI_*` sources and denies DNS/socket networking only
  during its lifetime; restoration is tested. No global/autouse patch was added.
  `tests/fixtures/llm_deployment_provenance.json` adds synthetic historical,
  completed, known-no-call and unknown dispatcher examples, not stored history.
- **T006:** `common.llm_config` adds frozen `ModelIdentity`,
  `DeploymentIdentity`, `TierConfiguration`, `LegacyRoutingEntry`,
  `RoutingConfiguration`, `LegacyMetadataAssociation` and `ResolvedDeployment`;
  closed `OperationalTier`, `MetadataSource` and `ResolutionSource` enums.
  Model version is non-empty opaque text, model key is derived, deployment
  identity remains independent, and revision/verification references are
  retained. No model, transport API version or approved baseline is invented.
- **T007:** opt-in `RoutingConfiguration.from_environment(...)` copies the
  supplied mapping/environment once. `None` retains absence; supplied blanks
  in tier settings and partial new metadata are invalid. Complete new identity
  must agree with a supplied compatibility key. Endpoint/region/raw CSV and
  all tier settings are frozen; raw CSV is deliberately **not parsed** here.
  Optional `legacy_entries` is reserved for the later validated parser.
  `ResolvedDeployment.with_legacy_metadata(...)` admits only an association
  matching endpoint/account scope, destination and configuration revision;
  mismatched/missing proof retains the destination and unavailable identity.
  The result preserves `metadata_association_reference`; base-key evidence
  may supply model ID without inventing a version. Evidence creation/validation
  remains the later resolver/preflight's responsibility, not an ARM lookup or
  destination guess. Embedding is not a chat tier.
- **T008:** frozen `InferenceAttemptEvidence` carries call/correlation IDs,
  optional resolved identity, nullable attempt, outcome, existing error-code
  text, actual optional prompt/completion usage, latency and output hash.
  Default is `None / unknown`, never success or synthetic zero usage.
  Terminal outcomes require true submission status. Response/chunk containers
  have an optional evidence slot defaulting to absent; no existing client
  method populates it and no writer/schema is activated.

**Preserved-behaviour boundary:** existing `LLMClientConfig` methods,
first-write-wins compatibility parsers, live environment selection, transport
submission, client caching, retry, gateway, audit and telemetry behaviour remain
unchanged pending their later tasks and matched configuration rollout.
The new snapshot is opt-in: constructing an existing client does not activate
new metadata validation or strict-map parsing. An association/reference or
SDK-method-entry spy is **not** evidence that Azure executed or even received
a request. Production submission instrumentation remains outstanding.

### Gates and setup

- Prerequisite script returned
  `FEATURE_DIR=C:\code\ama\specs\041-llm-deployment-routing` and
  `AVAILABLE_DOCS=[research.md,data-model.md,contracts/,quickstart.md,tasks.md]`.
  Requirements checklist **16/16** and routing-rollout checklist **36/36**:
  read-only PASS; no checklist marker changes.
- Read governing commenting/review instructions, constitution, feature
  specification/plan/research/data model, three contracts and quickstart.
  Existing `.gitignore`, `.dockerignore`, `.terraformignore` and web flat ESLint
  ignores cover the applicable setup; private workspace is not npm-published.
  No missing critical ignore patterns or setup changes were needed.
- `.specify/extensions.yml` parsed successfully. No before-implement hook;
  after-implement verification is optional and not dispatched, respecting this
  bounded checkpoint. No mandatory hook was registered.

### Actual scoped validation

Commands run from `C:\code\ama` using the existing virtual environment:

```powershell
$env:PYTHONPATH='apps\agents;apps\api;packages\domain\src'
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python.exe -m pytest tests\unit\test_llm_foundation_contracts.py -q -p no:cacheprovider --tb=short
```

- **RED before implementation:** exit 2, expected collection ImportError for
  missing `InferenceAttemptEvidence`.
- **Final focused run:** **12 passed**, 0 failed/errors/skips, **0.40 s**.
  Intermediate Ruff import-order/fixture-import findings were corrected.

The unchanged ten-module T004 union separately returned **94 passed**,
0 failed/errors/skips, **2.67 s**, one existing Starlette/httpx warning.
Final same-process run placed the foundation fixtures before that union,
also checking they do not contaminate existing regressions:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_llm_foundation_contracts.py tests\contract\test_foundry_chat_client_aoai.py tests\contract\test_foundry_chat_client.py tests\contract\test_foundry_gateway_fail_closed.py tests\contract\test_llm_model_routing.py tests\contract\test_llm_fallback.py tests\contract\test_llm_logging.py tests\contract\test_audit_record_shape.py tests\contract\test_audit_record_amend_loop_fields.py tests\contract\test_simulation_api_contract.py tests\contract\test_audit_replay_fidelity.py -q -p no:cacheprovider -m 'not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging and not azure_blob_worm_staging and not measurement_staging' --tb=short
```

**106 passed**, 0 failed/errors/skips, **2.64 s**. Sole warning:
existing `StarletteDeprecationWarning` in FastAPI's test client recommending
`httpx2`; no dependency change was made.

```powershell
.\.venv\Scripts\python.exe -m ruff check apps\agents\common\llm_config.py apps\agents\common\foundry_chat_client.py tests\fixtures\llm_deployment_routing.py tests\unit\test_llm_foundation_contracts.py
.\.venv\Scripts\python.exe -m ruff format --check apps\agents\common\llm_config.py apps\agents\common\foundry_chat_client.py tests\fixtures\llm_deployment_routing.py tests\unit\test_llm_foundation_contracts.py
$env:MYPYPATH='apps\agents;apps\api;packages\domain\src'
.\.venv\Scripts\python.exe -m mypy --follow-imports=silent apps\agents\common\llm_config.py apps\agents\common\foundry_chat_client.py
git -c core.whitespace=cr-at-eol --no-pager diff --check
```

All exit 0: Ruff lint clean, **4 files already formatted**, strict configured
mypy **no issues in 2 source files** (dependencies followed silently, not a
whole-repository typing claim). Plain `git diff --check` flags existing
CRLF-style added lines as trailing whitespace; the one-command `cr-at-eol`
check passes. `git ls-files --eol` confirms both touched source files retain
their original index/worktree CRLF. No Git configuration was changed.

### Preservation and checkpoint result

Read-only Python SHA-256 comparison against the tables above checked all
**50 files**, including the separate NDJSON sidecar byte hashes:
**0 mismatches**. Other 14 feature artifacts retain the prior root-relative
aggregate `8fb7d76135d786f763143572acc258dec882ef58259d048990945c0cce704834`.
Pre-foundation `tasks.md` SHA-256 was
`2a4f77f2163c6f1d7fd5f8db0176c7e35b08263c10ee84d1a0e5da6f32444c60`;
the final read-only marker-reversal check reproduced it exactly. Final Git
status showed only the two scoped source modifications and untracked new
fixtures/test plus the already-untracked feature directory. Branch remained
`model-upgrade-chat-sumlation`; T009 and T012 were explicitly confirmed unchecked.

**4/4 authorised tasks complete:** only T005–T008 newly marked `[X]`.
No unresolved foundation test/type/lint failure. This is **foundation
verification only**, not feature acceptance, SC-001's future 168 routing cells,
production submission proof, target P1 release readiness or real P2 acceptance.
All external baseline/governance/AVM/release/operational gates remain closed.
**STOP before T009. Return to the orchestrator with no handoff or auto-forward.**

## T009–T011 tests-first checkpoint — 2026-10-18

**Authority:** “Approve — execute T009–T011 tests first, then checkpoint.”
Only these three test-authoring tasks are complete. T012 and all later task
markers remain untouched. Branch remains `model-upgrade-chat-sumlation`.
No production routing, parsers, clients, foundation, schemas, configuration,
IaC or historical inputs were edited for this checkpoint. No agents, hooks,
workflows, installations, Azure calls, inference or commits were invoked.

Prerequisites resolved the existing absolute feature directory and documents.
Read-only checklist gates remain PASS: requirements **16/16**, routing-rollout
**36/36**. Existing ignore coverage needed no change. No requirements/design
clarification blocker was found; assertions use executable existing resolver,
client and SDK seams, plus the actual foundation `attempt_evidence` slot.
There are no conditional imports, compatibility shims, xfails or skips.

### Test files and boundaries

- **T009:** `tests/unit/test_llm_deployment_routing.py` — **81 cases**.
  Explicit precedence for all three tiers in all six alias orderings; all six
  raw conflict orderings; absent/empty settings; partial/inconsistent metadata;
  missing endpoint/region; unsupported chat tier; alias/exact/configured-base
  selection; captured endpoint/tier behaviour. Explicit A is retained with
  coordinate-to-B, matching A or missing association; wrong-account proof is
  rejected through the foundation's existing association admission API.
  Simulation isolation covers comparison against **both** live tiers through
  explicit/alias/exact/base routes, mixed explicit/legacy configurations,
  absent live explicit settings, distinct controls, and an unresolved required
  drafting comparison while reasoning remains callable. Invalid-path tests
  assert no fake SDK submissions, not merely a factory result.
- **T010:** `tests/contract/test_llm_deployment_routing.py` — **121 cases**.
  Common sync/stream requests cover all six configuration insertion orderings,
  all three chat tiers and native/AOAI endpoint shapes without CSV chat aliases.
  Assertions inspect the SDK `complete(...)` model, shaped endpoint, timeout,
  token parameters, messages and AAD scope. Request/usage identity tests cover
  explicit A versus legacy B, matching/absent association, and a misleading
  deployment name with separate configured synthetic model/version.
  Raw invalid maps, injected-map validation, safe diagnostics, common-wrapper
  snapshot behaviour, legacy exact/base injection and no production fallback
  to `AZURE_OPENAI_*` are independently exercised.
  MAF calls run the actual public factory, actual `OpenAIChatClient` and OpenAI
  SDK serialization with an injected `httpx.MockTransport`; assertions inspect
  the submitted HTTP URL and JSON model. This installed MAF client uses the
  **Responses API** (`/openai/responses`), not Chat Completions. Its two legacy
  test-seam controls actually complete requests. No routing function or
  deployment choice is mocked. Missing explicit-route support and the
  `ValueError`/shared-cause contract remain intentionally red.
- **T011:** `tests/contract/test_llm_deployment_map_compatibility.py` —
  **88 cases**. Independent common/config/eval/ingest parser tables cover
  duplicate-identical entries, both conflict orders, whitespace, absent/blank
  maps, missing/empty entries and keys/values, and multiple equals signs.
  All six alias orderings preserve the embedding coordinate, deployment and
  3072 dimensions. Ingest and direct-query embedding execute fake SDK request
  boundaries; direct query rejects mismatched dimensions. Deliberately selected
  per-run eval mappings execute requests, whereas an omitted shared coordinate
  cannot select any tier and submits zero requests. Non-tier exact-over-base
  compatibility remains green.

Network/environment isolation reuses T005's `routing_environment` context.
The two async-capable test modules enter that context from a function-scoped
async fixture **after** Windows initializes its event-loop socketpair.
The fixture restores all patches on teardown; no global network exception or
environment mutation was added. Initial authoring runs exposed and corrected
test-only loop initialization, MAF message/response shape, embedding method
name and evidence-slot name mistakes. These are not remaining product defects
or accepted red reasons.

### Actual final commands and counts

Run from `C:\code\ama`, existing virtual environment, no dependency changes:

```powershell
$env:PYTHONPATH='apps\agents;apps\api;packages\domain\src'
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python.exe -m pytest tests\unit\test_llm_deployment_routing.py tests\contract\test_llm_deployment_routing.py tests\contract\test_llm_deployment_map_compatibility.py --collect-only -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest tests\unit\test_llm_deployment_routing.py tests\contract\test_llm_deployment_routing.py tests\contract\test_llm_deployment_map_compatibility.py -q -p no:cacheprovider --tb=no -rN
```

**290 collected**, no collection errors (**2.58 s**).
Focused execution: **150 failed, 140 passed**, **4.54 s**, pytest exit **1**
as expected; **0 errors/skips/xfails**, no warnings.

| New module | Total | Passed | Expected red |
| --- | ---: | ---: | ---: |
| Unit resolver tables (T009) | 81 | 23 | 58 |
| Client request boundaries (T010) | 121 | 77 | 44 |
| Parser/embedding compatibility (T011) | 88 | 40 | 48 |
| Total | 290 | 140 | 150 |

Expected failures grouped by missing contract behaviour:

| Missing behaviour | Red cases | Observed reason |
| --- | ---: | --- |
| Raw CSV conflict/malformed rejection | 66 | Existing parsers accept conflicts/malformed entries; explicit common calls still submit on conflicting maps (6 unit + 12 client + 48 parser cases) |
| Injected-map non-empty destination validation | 2 | Empty/whitespace destinations reach the fake SDK; the empty-key control already fails closed |
| Explicit-over-alias precedence / live-tier exact/base fallback | 22 | 18 explicit tier/ordering cases choose aliases instead; 4 configured exact/base cases report no tier mapping |
| Empty explicit settings, invalid metadata, simulation explicit requirement and actionable invalid-Foundry diagnostic | 10 | 2 empty settings + 4 invalid metadata + 3 simulation fallback cases fail zero-submission assertions; 1 wrapper error names the legacy coordinate rather than the empty explicit setting |
| Common client/wrapper immutable selection | 3 | 1 direct client + 2 wrapper cases choose post-construction mutated deployments |
| Request-local resolved identity | 10 | Existing `attempt_evidence` remains absent: 3 resolver association + 6 sync/stream association + 1 configured misleading-name case |
| Simulation isolation / required comparison | 17 | 16 collision cases and 1 unresolved comparison still submit simulation requests |
| MAF explicit routing without CSV aliases | 12 | Factory raises `ValueError` for missing CSV tier mapping before request submission |
| MAF shared diagnostic cause | 6 | Existing factory `ValueError` has no shared `FoundryConfigurationError` cause |
| MAF captured explicit selection | 2 | Existing factory still requires CSV tier mapping; snapshot request cannot yet execute |
| Total | 150 | Intentional regression red, not feature acceptance |

Zero-submission assertions intentionally expose the wrongly submitted fake
requests on invalid paths. Those submissions are in-memory witnesses, not real
network/model execution. Diagnostic assertions remain in place beyond the
currently failing rejection gates; green rejection alone will not bypass them.
No final failure is an import, fixture/setup, SDK fake-shape or dependency error.

The unchanged foundation/baseline command was rerun separately:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_llm_foundation_contracts.py tests\contract\test_foundry_chat_client_aoai.py tests\contract\test_foundry_chat_client.py tests\contract\test_foundry_gateway_fail_closed.py tests\contract\test_llm_model_routing.py tests\contract\test_llm_fallback.py tests\contract\test_llm_logging.py tests\contract\test_audit_record_shape.py tests\contract\test_audit_record_amend_loop_fields.py tests\contract\test_simulation_api_contract.py tests\contract\test_audit_replay_fidelity.py -q -p no:cacheprovider -m 'not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging and not azure_blob_worm_staging and not measurement_staging' --tb=short
```

**106 passed** = **12 foundation + 94 unchanged baseline**, **3.71 s**,
exit 0. The old first-write-wins assertion remains unchanged and passing;
replacing it is T013, not authorised here.

A same-process run placed all new tests **before** that foundation/baseline
union, demonstrating fixture restoration even after expected red failures:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_llm_deployment_routing.py tests\contract\test_llm_deployment_routing.py tests\contract\test_llm_deployment_map_compatibility.py tests\unit\test_llm_foundation_contracts.py tests\contract\test_foundry_chat_client_aoai.py tests\contract\test_foundry_chat_client.py tests\contract\test_foundry_gateway_fail_closed.py tests\contract\test_llm_model_routing.py tests\contract\test_llm_fallback.py tests\contract\test_llm_logging.py tests\contract\test_audit_record_shape.py tests\contract\test_audit_record_amend_loop_fields.py tests\contract\test_simulation_api_contract.py tests\contract\test_audit_replay_fidelity.py -q -p no:cacheprovider --tb=no -rN -m 'not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging and not azure_blob_worm_staging and not measurement_staging'
```

The command was executed via `pytest.main` with the identical argument list
and a reporting-only plugin counting outcomes by module. Result:
**150 expected failed, 246 passed**, **7.01 s**, exit 1; no errors/skips.
All **106** pre-existing/foundation cases still pass after the new fixtures.
Both baseline runs have only the existing Starlette/httpx deprecation warning.
No new-test environment/network fixture contaminates the following modules.

```powershell
.\.venv\Scripts\python.exe -m ruff check tests\unit\test_llm_deployment_routing.py tests\contract\test_llm_deployment_routing.py tests\contract\test_llm_deployment_map_compatibility.py
.\.venv\Scripts\python.exe -m ruff format --check tests\unit\test_llm_deployment_routing.py tests\contract\test_llm_deployment_routing.py tests\contract\test_llm_deployment_map_compatibility.py
git -c core.whitespace=cr-at-eol --no-pager diff --check
```

Lint **PASS**; format **3 files already formatted**; whitespace check PASS.
No production typing claim is added for this tests-only checkpoint.

### Preservation, hooks and stop

Read-only Python `hashlib.sha256(path.read_bytes())` compared the original
tables in this document: **50 checked, 0 mismatches**, including sidecar bytes.
The other **14 feature artifacts** still reproduce aggregate
`8fb7d76135d786f763143572acc258dec882ef58259d048990945c0cce704834`.
Pre-test-authoring `tasks.md` SHA-256:
`da338b45a74372dd58f9584ed8fcb8abed9ea501f23d55153d83c0a81abe8089`;
the final read-only reversal of only this checkpoint's three markers
**reproduced that value exactly**. A final raw-byte comparison also confirmed
the five prior source/foundation files retained their pre-marker fingerprints.
Prior source and foundation fixture files were not edited. Scope is exactly
the three new test files, this appended evidence and T009–T011 markers.

`.specify/extensions.yml` was read again: no before-implement hook is
registered; after-implement `verify / speckit.verify.run` is optional.
It was not invoked, respecting the explicit no-hooks checkpoint boundary.
No mandatory hook is registered.

**3/3 authorised test-authoring tasks complete; 11/52 total task markers now
complete.** The red regressions are the successful deliverable of T009–T011,
not a claim that the feature works. SC-001's 28 paths × 6 orderings = 168 future
acceptance cells are **not** acceptance-passed by these 290 test cases.
Dispatcher/controller integration, all six dispatcher roles, production fixes
and later acceptance remain assigned to their unchanged future tasks.
No unexpected final failures or unresolved contract-design blockers remain.
All external governance/baseline/release/operational gates remain closed.
**STOP before T012. Return to the orchestrator; no handoff or auto-forward.**

## T012–T013 shared resolver checkpoint — 2026-10-18

**Authority:** “Approve — execute T012–T013 only, then checkpoint.”
Only these two markers are newly complete: **13/52 overall**. Actual branch
`model-upgrade-chat-sumlation` retained. T014 and all later markers remain
unchanged. No client adoption, dispatcher/controller/MAF/eval/ingest changes,
SDK transport or audit-producer changes, IaC/model/cloud operations, installs,
hooks, workflows, delegation, handoffs or commits.

Prerequisites again returned the existing absolute feature directory and its
five available document entries. Read-only checklist status: requirements
**16/16**, routing-rollout **36/36**, both PASS. Read the exact tasks, approved
routing contract, data model, plan/research/quickstart, constitution, applicable
commenting/review guidance, foundation APIs and existing regression tests.
Existing ignore coverage requires no setup change.

### Shared API and exact scope

- `apps/agents/common/llm_config.py`: `parse_deployment_entries(raw)` validates
  before a dictionary exists; `parse_deployment_map(raw)` creates the lookup
  only from those validated entries. Absent/blank whole CSV is allowed;
  non-empty malformed entries fail, whitespace is trimmed, identical repeats
  are idempotent, conflicting destinations name the key and both destinations.
  Diagnostics do not dump malformed raw input, prompts, credentials or env.
- Frozen `DeploymentResolver(configuration, deployments=...)` validates raw
  CSV even when a map is injected, validates/copies injected entries including
  trim-induced conflicts, and retains immutable entries. Its
  `from_environment(..., configuration_revision=...)` copies once; no later
  environment/network reads. Invalid tier settings are retained as immutable
  `RoutingConfiguration.tier_errors` and rejected on affected use rather than
  converted into a valid fallback. Reconstructing a resolver from that snapshot
  preserves these errors. The original foundation snapshot constructor retains
  its eager ValueError contract.
- `resolve(tier, metadata_association=...)` returns one `ResolvedDeployment`.
  Explicit tier precedes valid alias/exact/configured-base lookup; blank
  supplied fields are errors, not absence. Simulation requires explicit
  deployment and compares both effective live destinations under the same
  snapshot precedence; unresolved or equal live comparisons fail closed.
  Other resolvable paths remain usable, including when simulation or another
  tier has invalid metadata. No inferred account differences or default models.
- Destination is chosen before metadata. Complete configured identity remains
  independent of deployment spelling. Legacy identity is admitted only from
  a same-destination validated map or target/account/revision-bound association;
  explicit A never borrows coordinate-to-B's identity/version. Base-only
  association does not invent a version. `resolve_legacy(model_key)` preserves
  exact-before-base and embedding lookup outside chat tiers; chat aliases
  cannot bypass simulation rules through this method.
- `LLMClientConfig.foundry_deployment_map()` now delegates to the shared raw
  validator. No new parser/resolver is added outside the shared mechanism.
  `foundry_chat_client.py` only imports/re-exports the existing public
  `FoundryConfigurationError` from configuration to avoid a circular dependency.
  It remains a RuntimeError, with the same public client import; SDK methods,
  legacy client parser, caches, retries, gateway and evidence slots are untouched.
- T013 replaces the obsolete first-write-wins assertion with two actionable
  conflict-order assertions and a separate identical-duplicate/embedding
  preservation assertion. The model-routing module adds only affected config
  conflict and explicit-tier/no-duplicate-alias checks. Existing AOAI shapes,
  test-only injection and tier/default checks remain. Its config import uses
  the canonical `common` package for the shared exception boundary.
- `tests/unit/test_llm_shared_resolver.py` adds just **six direct-API tests**,
  reusing existing conflict fixtures. These test the new seam without replacing
  or mocking the routing in T009–T011. No assertion there was weakened, skipped
  or xfailed. T013's two client-parser rejection cases remain expected-red
  until T014 adopts validation; test-authoring completion is not a claim that
  this old consumer is strict already.

### Exact commands and results

From `C:\code\ama`, existing virtual environment:

```powershell
$env:PYTHONPATH='apps\agents;apps\api;packages\domain\src'
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python.exe -m pytest tests\unit\test_llm_shared_resolver.py -q -p no:cacheprovider --tb=short
```

**RED:** 6 failed, 0 collection/setup errors, **0.48 s**, exit 1, because
`DeploymentResolver` did not exist. After implementation, direct plus foundation
returned **18 passed**, **0.42 s**, exit 0. Subsequent focused commands:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_llm_shared_resolver.py tests\unit\test_llm_foundation_contracts.py tests\contract\test_llm_model_routing.py -q -p no:cacheprovider --tb=short
.\.venv\Scripts\python.exe -m pytest tests\contract\test_llm_deployment_map_compatibility.py -k config -q -p no:cacheprovider --tb=short
```

**32 passed** (**2.04 s**) and **17 passed / 71 deselected** (**0.55 s**),
both exit 0. Direct tests also cover path-local invalid simulation/live metadata,
immutable error retention, bound/wrong-account proof, explicit A versus B,
configured opaque identity, effective isolation and missing connection settings.

Final same-process union (new tests first, preserving fixture-restoration check):

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_llm_shared_resolver.py tests\unit\test_llm_deployment_routing.py tests\contract\test_llm_deployment_routing.py tests\contract\test_llm_deployment_map_compatibility.py tests\unit\test_llm_foundation_contracts.py tests\contract\test_foundry_chat_client_aoai.py tests\contract\test_foundry_chat_client.py tests\contract\test_foundry_gateway_fail_closed.py tests\contract\test_llm_model_routing.py tests\contract\test_llm_fallback.py tests\contract\test_llm_logging.py tests\contract\test_audit_record_shape.py tests\contract\test_audit_record_amend_loop_fields.py tests\contract\test_simulation_api_contract.py tests\contract\test_audit_replay_fidelity.py -q -p no:cacheprovider --tb=no -rN -m 'not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging and not azure_blob_worm_staging and not measurement_staging'
```

**409 executed: 269 passed / 140 expected failed**, **6.55 s**, exit 1;
**0 errors/skips/xfails**. Only the existing Starlette/httpx deprecation warning.
An earlier identical-argument run through `pytest.main` with a reporting-only
plugin counted module/function outcomes (**269/140**, **10.05 s**):

| Population | Passed | Expected red |
| --- | ---: | ---: |
| Six direct shared-API checks | 6 | 0 |
| T009 unit client-bound tables | 23 | 58 |
| T010 request-boundary tests | 77 | 44 |
| T011 parser/embedding compatibility | 52 | 36 |
| Foundation plus updated baseline union | 111 | 2 |
| Total | 269 | 140 |

T009–T011 alone move from **140 pass / 150 red** to **152 pass / 138 red**:
**12 config-parser cases genuinely red-to-green**. The 17 config-parser
cases all pass. No shared resolver failure remains in direct-API checks.
Remaining failures are real consumer assertions, not import/fixture failures:

| Owning later task | Red | Exact grouping |
| --- | ---: | --- |
| T014 common client/wrapper/parser adoption | 96 | T009 58 (18 explicit precedence, 6 raw conflicts, 2 blank settings, 4 metadata, 4 exact/base, 1 snapshot, 3 association, 3 required simulation, 16 isolation, 1 unresolved comparison); T010 common 24 (12 raw-map, 2 injected-map, 2 snapshot, 1 diagnostic, 7 identity); T011 common parser 12; T013 replacement parser tests 2 |
| T015 MAF adoption | 20 | 12 explicit/no-alias requests, 6 shared diagnostic causes, 2 captured selection |
| T018 eval parser | 12 | 2 conflict orders, 10 malformed maps |
| T019 ingest parser | 12 | 2 conflict orders, 10 malformed maps |

The shared resolver already implements the underlying rejection/selection rules;
these consumers still do not use it. Do not make the 140 cases green by changing
their assertions or implementing T014+ inside this checkpoint.

```powershell
.\.venv\Scripts\python.exe -m ruff check apps\agents\common\llm_config.py apps\agents\common\foundry_chat_client.py tests\unit\test_llm_shared_resolver.py tests\contract\test_foundry_chat_client_aoai.py tests\contract\test_llm_model_routing.py
.\.venv\Scripts\python.exe -m ruff format --check apps\agents\common\llm_config.py apps\agents\common\foundry_chat_client.py tests\unit\test_llm_shared_resolver.py tests\contract\test_foundry_chat_client_aoai.py tests\contract\test_llm_model_routing.py
$env:MYPYPATH='apps\agents;apps\api;packages\domain\src'
.\.venv\Scripts\python.exe -m mypy --follow-imports=silent apps\agents\common\llm_config.py apps\agents\common\foundry_chat_client.py
.\.venv\Scripts\python.exe -m mypy --follow-imports=silent tests\unit\test_llm_shared_resolver.py tests\contract\test_foundry_chat_client_aoai.py
git -c core.whitespace=cr-at-eol --no-pager diff --check
```

Final results: lint PASS; **5 already formatted**; configured strict mypy
**2 source files PASS**, **2 test files PASS**; whitespace PASS.
An additional attempted all-five-file mypy command (same arguments, with all
five Python paths above) and a test-only `--explicit-package-bases` attempt
both stop at existing mixed imports: `apps/agents/communication/config.py`
is found as both `apps.agents.communication.config` and `communication.config`
through the legacy model-routing test's unchanged agent-config imports.
This extended test-module typing limitation is recorded, not suppressed with
ignores, altered configuration, skipped imports or unrelated import rewrites.
The established scoped source typing gate is green.

### Preservation, hooks and stop

Read-only raw-byte SHA-256 comparison against the original tables above:
**50 checked / 0 mismatches**, including all 21 sidecar byte hashes.
The other **14 feature artifacts** retain root-relative aggregate
`8fb7d76135d786f763143572acc258dec882ef58259d048990945c0cce704834`.
UTF-8-decoded `git show HEAD:<path>` versus current AST confirms the entire
`LiveFoundryChatClient` class unchanged, and `LLMClientConfig` unchanged except
its authorised shared-parser delegation. Thus old transport/retry/cache/
gateway and audit behaviour was not rewired to satisfy future red tests.
Existing source CRLF is retained. Pre-marker task SHA-256:
`d7d7a9a7fca41e041c1709063321bdb50640122be53b1d2b540e636d72f2eb78`;
reversing only T012/T013 markers reproduces that value.

`.specify/extensions.yml` has no before-implement hook; its only
after-implement hook is optional `verify / speckit.verify.run`, offered but
not invoked under the explicit no-hooks boundary. No mandatory hook exists.

**2/2 authorised tasks complete; 13/52 overall.** No unresolved shared-resolver
implementation blocker. Extended legacy-test typing has the limitation above;
adapter/parser acceptance remains intentionally red. This is an inactive local
candidate, not SC-001's future **168-cell acceptance**, target readiness or
permission to deploy strict readers against the old ambiguous CSV.
All baseline/governance/collection/AVM/release/migration/retirement gates stay
closed. **STOP before T014. Return to the orchestrator; no handoff.**

## T014–T017 adapter adoption checkpoint — 2026-10-18

**Authority:** explicit approval “Approve — execute T014–T017 only, then
checkpoint”. This supersedes the preceding pending-T014 stop statement, not
any later-task or operational gate. One agent executed T014, then T015, T016,
T017 sequentially. No agent, workflow, hook command, Azure read/provisioning,
real-model call, IaC/model-choice change, install, stage or commit was performed.
Branch `model-upgrade-chat-sumlation` and all pre-existing changes are retained.

### Gates and implementation

Prerequisites:

```powershell
& .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
```

Returned `C:\code\ama\specs\041-llm-deployment-routing` and
`["research.md","data-model.md","contracts/","quickstart.md","tasks.md"]`.
Read-only checklist gate: requirements **16/16**, routing-rollout **36/36**;
both PASS, no checklist edits. Existing Python `.gitignore` / `.dockerignore`
already cover the affected build/cache/environment artifacts; no ignore-file
or package/configuration changes were needed.

| Task | Adoption and preserved boundaries |
| --- | --- |
| T014 | `LLMClientConfig` captures tier source presence, endpoint, region and raw map once. Its resolver factory reads only that frozen snapshot. `foundry_model_key_for` selects purpose, not a guessed model coordinate/default. `LiveFoundryChatClient` delegates parsing and resolution to the existing shared resolver; injected dictionaries cannot conceal conflicting raw environment CSV. Each sync/stream request uses one resolved deployment and exposes its associated identity in optional evidence, with `inference_attempted=null` / outcome `unknown`. No new strict audit fields or submission instrumentation are emitted. Endpoint shaping, per-URL SDK caches, AAD scope, gateway, token parameters, retries/deadlines/timeouts, tools, response/usage shape and unambiguous legacy exact/base lookup remain. |
| T015 | MAF consumes the same config snapshot/resolver, including explicit deployments without CSV aliases or legacy per-tier fields. Its actual SDK request `model` is checked by the existing HTTP mock transport, not a factory-only proxy. Shared credential/token-provider caches, cognitive-services scope, middleware and factory signature are unchanged. Shared configuration errors cross the existing public `ValueError` boundary with their actionable `FoundryConfigurationError` cause. |
| T016 | Dispatcher construction validates explicit simulation and effective live isolation before readiness can be ready. Every role passes the constant simulation purpose, never simulation/reasoning model keys. A frozen validated resolver is given to the common client. Configuration errors use narrow handling, diagnostic logging, degraded readiness and a marked `[configuration-error]` degraded reply with no invoked deployment; transport/gateway boundaries, six role routes and prompts are retained. Successful responses use typed `deployment_id`, not optional raw metadata. |
| T017 | Controller retains one immutable resolver snapshot plus frozen endpoint/region/API-version/backend settings. One resolved simulation result supplies the direct `AsyncAzureOpenAI` destination and endpoint for every completion round. Invalid raw maps, missing/blank simulation, live collisions and unresolved isolation emit existing SSE `error` / `openai_unavailable` before SDK/credential construction. Missing simulation diagnostics name `AZURE_AI_SIMULATION_DEPLOYMENT`. Configured-but-broken Foundry routing does not silently become a successful offline turn. Genuine unconfigured offline mode, safety/refusal order, user history, tools, gateway and existing audit behavior remain unchanged. |

Two compatibility details were addressed during adoption, without altering
the foundation resolver's parser, precedence or identity-association algorithms:

- The old wrapper swallowed Foundry initialization exceptions; missing/blank
  endpoint with other Foundry settings could also select the legacy transport.
  Captured `foundry_configured` source presence now keeps those paths on
  Foundry and propagates the shared error. New tests include absent, empty and
  whitespace endpoint with valid legacy test settings and assert zero legacy
  constructors/SDK submissions in both wrapper and MAF.
- MAF's supported hermetic legacy test seam must remain executable. Only when
  **no Foundry routing is configured**, the config's already-captured test
  endpoint/per-tier deployment values can be adapted into the same resolver.
  This cannot override invalid/present Foundry settings. No production
  `AZURE_OPENAI_*` fallback is introduced.

Test changes are restricted to focused behavioral gaps and obsolete private
resolver assumptions:

- `tests/contract/test_foundry_chat_client_aoai.py` and
  `tests/contract/test_llm_model_routing.py`: private resolver probes now supply
  the endpoint/region context required by shared resolution; no weakened
  routing/conflict assertions.
- `tests/contract/test_llm_deployment_map_compatibility.py`: the non-tier
  exact/base private probe similarly supplies endpoint/region. Eval/ingest
  assertions and implementation remain untouched.
- `tests/contract/test_llm_deployment_routing.py`: assert identity-only
  evidence remains unknown, raw response gains no strict fields, and broken
  Foundry endpoint cannot select legacy test transport.
- New `tests/unit/test_llm_adapter_snapshots.py`: **14 focused tests**:
  dispatcher six-role SDK requests from one frozen app, five invalid-config
  cases, controller six invalid-snapshot cases, missing-endpoint/no-offline
  fallback, and two tool rounds retaining the same destination. Direct route
  coroutine/unit seams are used; the later T020 ASGI/integration acceptance
  suite was not authored or run. The two-round case asserts existing SSE
  order, tool schemas, streaming and AAD transport arguments.

### Execution and scoped development checks

All commands below use the existing `.venv`, no installs or SDK upgrades.

T014 development command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_llm_deployment_routing.py tests/contract/test_llm_deployment_routing.py tests/contract/test_llm_deployment_map_compatibility.py tests/unit/test_llm_foundation_contracts.py tests/unit/test_llm_shared_resolver.py tests/contract/test_llm_model_routing.py tests/contract/test_foundry_chat_client_aoai.py tests/contract/test_foundry_chat_client.py -q -p no:cacheprovider --tb=short
```

Initial adoption result: **292 passed / 51 failed**. Those failures were
20 not-yet-adopted MAF tests, 24 intentionally later eval/ingest tests, and
seven old private probes missing newly required connection context. After
fixing only that probe context, the same command with
`-k 'not maf and not eval and not ingest'` passed **280 / 63 deselected**
(exit 0). The later full union below includes every originally failing probe;
deselection is not used to report the full union green.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/contract/test_llm_deployment_routing.py -k maf -q -p no:cacheprovider --tb=short
```

First T015 adoption run: **20 passed / 2 failed**, exposing the supported
hermetic legacy seam described above. After the fix: **22 passed /
99 deselected**, exit 0. No acceptance assertion was removed.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_llm_adapter_snapshots.py tests/unit/test_aud021_privacy_classification_and_dispatcher.py -q -p no:cacheprovider --tb=short
.\.venv\Scripts\python.exe -m pytest tests/unit/test_llm_adapter_snapshots.py tests/unit/test_aud021_privacy_classification_and_dispatcher.py tests/unit/test_simulation_controller_safety.py apps/api/tests/test_simulation_chat_controller_wiring.py -q -p no:cacheprovider --tb=short
.\.venv\Scripts\python.exe -m pytest tests/unit/test_llm_adapter_snapshots.py tests/unit/test_aud021_privacy_classification_and_dispatcher.py tests/unit/test_simulation_controller_safety.py apps/api/tests/test_simulation_chat_controller_wiring.py tests/contract/test_llm_deployment_routing.py -q -p no:cacheprovider --tb=short
```

Dispatcher checkpoint: **9 passed**. The first expanded controller run had
**26 passed / 1 failed** because the new test incorrectly expected a
`citations` event with retrieval disabled; the test now asserts the actual
preserved no-retrieval event order. No production SSE change was made to
satisfy that assertion. Final combined adapter/common/MAF check: **152 passed**,
exit 0, **4.44 s**.

### Final established regression union

The established T012/T013 union plus the four bounded adapter/safety/wiring
modules, with the existing staging exclusions:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_llm_shared_resolver.py tests/unit/test_llm_deployment_routing.py tests/contract/test_llm_deployment_routing.py tests/contract/test_llm_deployment_map_compatibility.py tests/unit/test_llm_foundation_contracts.py tests/contract/test_foundry_chat_client_aoai.py tests/contract/test_foundry_chat_client.py tests/contract/test_foundry_gateway_fail_closed.py tests/contract/test_llm_model_routing.py tests/contract/test_llm_fallback.py tests/contract/test_llm_logging.py tests/contract/test_audit_record_shape.py tests/contract/test_audit_record_amend_loop_fields.py tests/contract/test_simulation_api_contract.py tests/contract/test_audit_replay_fidelity.py tests/unit/test_llm_adapter_snapshots.py tests/unit/test_aud021_privacy_classification_and_dispatcher.py tests/unit/test_simulation_controller_safety.py apps/api/tests/test_simulation_chat_controller_wiring.py -q -p no:cacheprovider --tb=no -rN -m 'not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging and not azure_blob_worm_staging and not measurement_staging'
```

Final result: **416 passed / 24 failed**, **440 collected**, **6.79 s**,
pytest exit **1**. No collection errors, xfails, skips or hidden expected-red
markers. One existing Starlette/httpx TestClient deprecation warning;
no dependency change is made for it. An earlier full-union run with
`--tb=short` (before the four extra connection gap cases) was
**412 passed / 24 failed**, **6.91 s**, and identified all remaining nodes.
The final source refinements were followed by the final full union above.

All remaining failures are in
`tests/contract/test_llm_deployment_map_compatibility.py`:

| Later task | Exact node families / parameters | Failures |
| --- | --- | ---: |
| T018 eval | `test_conflicting_pair_orders_fail_with_actionable_diagnostics[destinations0-eval]`, `[destinations1-eval]`; `test_nonempty_maps_never_silently_discard_malformed_entries[<raw>-eval]` for each raw value below | 12 |
| T019 ingest | Same conflict nodes with `-ingest`; same malformed nodes with `-ingest` | 12 |

The ten exact malformed raw parameters are `missing-equals`, `=destination`,
`key=`, `key=  ` (two trailing spaces), ` =destination`,
`key=destination=extra`, `key=destination,`, `,key=destination`,
`key=destination,,other=target`, `key=destination,  ,other=target`.
Each failure is **DID NOT RAISE** the existing package-specific configuration
exception. These are ordinary failing assertions, not pytest xfails. T018/T019
source is deliberately unchanged. All 96 former common/wrapper/parser reds
and all 20 former MAF reds are resolved; no authorized-scope failure remains.

### Lint, formatting, type checks and preservation

Exact final commands:

```powershell
.\.venv\Scripts\python.exe -m ruff check apps/agents/common/llm_config.py apps/agents/common/foundry_chat_client.py apps/agents/common/llm_client.py apps/agents/maf_runtime/chat_client.py apps/agents/dispatcher/agent.py apps/api/app/services/simulation/controller_service.py tests/contract/test_foundry_chat_client_aoai.py tests/contract/test_llm_model_routing.py tests/contract/test_llm_deployment_map_compatibility.py tests/contract/test_llm_deployment_routing.py tests/unit/test_llm_adapter_snapshots.py
.\.venv\Scripts\python.exe -m ruff format --check apps/agents/common/llm_config.py apps/agents/common/foundry_chat_client.py apps/agents/common/llm_client.py apps/agents/maf_runtime/chat_client.py apps/agents/dispatcher/agent.py apps/api/app/services/simulation/controller_service.py tests/contract/test_foundry_chat_client_aoai.py tests/contract/test_llm_model_routing.py tests/contract/test_llm_deployment_map_compatibility.py tests/contract/test_llm_deployment_routing.py tests/unit/test_llm_adapter_snapshots.py
.\.venv\Scripts\python.exe -m mypy --follow-imports=silent apps/agents/common/llm_config.py apps/agents/common/foundry_chat_client.py apps/agents/common/llm_client.py apps/agents/maf_runtime/chat_client.py apps/agents/dispatcher/agent.py apps/api/app/services/simulation/controller_service.py
.\.venv\Scripts\python.exe -m mypy --follow-imports=silent tests/unit/test_llm_adapter_snapshots.py tests/contract/test_llm_deployment_map_compatibility.py tests/contract/test_llm_deployment_routing.py tests/contract/test_foundry_chat_client_aoai.py
git -c core.whitespace=cr-at-eol diff --check
```

Ruff **PASS**, **11 already formatted**; configured strict mypy **6 source
files PASS**, **4 test files PASS** (existing repository test overrides apply).
The pre-existing mixed-import identity issue for
`tests/contract/test_llm_model_routing.py` remains the already documented
limitation; it is included in pytest/Ruff but not combined into this mypy
invocation. No import-layout change, casts or new type ignores were added.
Initial Ruff findings (import order/line wrapping) were corrected; the
formatter was used only on touched files. A plain `git diff --check` reports
retained CRLF as trailing whitespace under this repository's configuration;
the established CRLF-aware command above passes without line-ending churn.

Read-only historical comparison command (no fixture writes):

```powershell
@'
import hashlib
import re
from pathlib import Path
text = Path('specs/041-llm-deployment-routing/verification.md').read_text(encoding='utf-8').split('## Checkpoint integrity and remaining gates')[0]
anchors = dict(re.findall(r'\| `((?:tests/|packages/|apps/)[^`]+)` \| `([a-f0-9]{64})` \|', text))
for name, data_hash, sidecar_hash in re.findall(r'\| `([^`]+\.ndjson)` \| `([a-f0-9]{64})` \| `([a-f0-9]{64})` \|', text):
    anchors[f'fixtures/sim_replays/{name}'] = data_hash
    anchors[f'fixtures/sim_replays/{name}.sha256'] = sidecar_hash
assert len(anchors) == 50, len(anchors)
mismatches = [path for path, expected in anchors.items() if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected]
assert not mismatches, mismatches
print('Historical fingerprint verification: 50/50 unchanged')
'@ | .\.venv\Scripts\python.exe -
```

Result: **50/50 unchanged**, including all 21 NDJSON and 21 sidecar raw
byte hashes. No historical fixture source, audit schema/writer/reader or
KQL asset changed. Pre-marker tasks SHA-256:
`c85e4669ec73b7131a247036e46aa3353ffe767ea99ed8125adb5d98557647ee`;
only T014–T017 markers change at this checkpoint.

### Hooks, changed paths and stop

`.specify/extensions.yml` was read and parsed with the existing PyYAML:
no `before_implement` hooks; sole enabled/unconditional `after_implement`
hook is optional `verify / speckit.verify.run`, offered but **not invoked**
under the explicit no-hooks boundary. No mandatory hook exists.

Changed at this checkpoint:

- Source: `apps/agents/common/{llm_config,foundry_chat_client,llm_client}.py`,
  `apps/agents/maf_runtime/chat_client.py`, `apps/agents/dispatcher/agent.py`,
  `apps/api/app/services/simulation/controller_service.py`.
- Tests: `tests/contract/{test_foundry_chat_client_aoai,test_llm_model_routing,test_llm_deployment_map_compatibility,test_llm_deployment_routing}.py`,
  new `tests/unit/test_llm_adapter_snapshots.py`.
- Tracking: this `verification.md` append and only T014–T017 checkboxes in
  `tasks.md`. Existing earlier uncommitted source/fixtures/feature artifacts
  remain in place.

**4/4 authorized tasks complete; 17/52 overall, 35 unchecked.** T018 and
every later task remain unchecked. No unresolved implementation concern
within T014–T017; the 24 later-task reds, pre-existing test-import typing
limitation and TestClient warning are explicitly retained. Strict submission
evidence/audit activation, T020/T021 integration and acceptance, and the
**28 paths × 6 orders = 168 future cells** remain unclaimed. This is an
inactive local candidate; no deployment/readiness or coverage-completion
claim is made for the full feature. All external baseline/governance/AVM/
collection/release/migration/retirement gates remain closed.
**STOP before T018. Return to the orchestrator; no handoff.**

## Checkpoint — T018–T019 only (2026-10-18)

### Authority, scope and compatibility

- Authorisation: **“Approve — execute T018–T019 only, then checkpoint”**.
  Repository `C:\code\ama`; actual branch `model-upgrade-chat-sumlation`
  retained. No handoff, delegation, workflow, hook execution or commit.
- Prerequisite script returned this absolute feature directory and the
  expected research/data-model/contracts/quickstart/tasks documents.
  Read-only checklist gate: requirements **16/16**, routing-rollout **36/36**;
  no unchecked items and no checklist edits.
- Read the task plan, routing contract (including adapter/package boundaries),
  design context, constitution, applicable commenting/review instructions,
  existing parser/eval/embedding tests and preceding verification commands.
  Existing Python/Docker ignore patterns suffice; no setup changes.
- **T018 complete**: eval uses package-local strict CSV/pair validation and
  retains exact model/version before base-model lookup and explicit per-run
  mapping. Omitted shared coordinates still fail rather than infer a tier.
- **T019 complete**: ingest uses the same validation semantics locally,
  without importing agent/common or eval code. Default
  `text-embedding-3-large@1`, exact-before-base lookup, deployment and 3072
  dimensions remain unchanged. Embeddings do not adopt chat tiers.
- Both parsers trim surrounding whitespace, accept absent/empty/whitespace-only
  entire input and identical duplicate pairs, and reject malformed nonempty
  entries (including empty CSV segments, empty keys/values and multiple `=`).
  Conflicting keys fail before an overwrite and identify the setting, key
  and both destinations. Grammar errors identify setting and entry position.
- Constructors validate configured raw CSV even when a map or callable is
  injected. Injected maps require nonempty string keys/values, are trimmed
  and checked for normalized-key conflicts, and are copied. A valid deliberate
  per-run injected map still overrides a valid configured mapping.
- Request code, version handling, parameters, endpoint/client/auth injection,
  retry/rate-limit/timeout behaviour, batching and query embedding code are
  untouched. No model identity is inferred from names; no stored data rewritten.
  No manifest/dependency/package-layout changes or installations.

### Red → green evidence

Exact reproduction/rerun command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/contract/test_llm_deployment_map_compatibility.py -k '(eval or ingest) and (conflicting_pair_orders or nonempty_maps)' -q -p no:cacheprovider --tb=no -rN
```

Before source changes: **24 failed / 64 deselected**, **0.44 s**, exit **1**:
the existing 12 eval and 12 ingest conflict/malformed assertions, all ordinary
failures. After implementation, the same selection (with `--tb=short` instead
of `--tb=no`) produced **24 passed / 82 deselected**, **0.43 s**, exit **0**.
The 18 extra deselections are the new bounded edge cases below.

Four focused test functions were appended to the existing compatibility
module (18 parametrized cases): injected seams cannot conceal invalid raw
CSV; injected keys/values must be nonempty strings; normalized duplicates
and copied-map stability with deliberate override of valid configured maps;
ingest exact/base embedding lookup. No assertion was weakened or skipped.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/contract/test_llm_deployment_map_compatibility.py -k 'compatibility_inject or ingest_embedding_exact' -q -p no:cacheprovider --tb=short -rN
```

Before source changes: **16 failed / 2 passed / 88 deselected**, **0.49 s**,
exit **1**. After implementation: **18 passed / 88 deselected**, **0.43 s**,
exit **0**. The final combined run also includes the added assertion that
a valid configured map does not prevent deliberate injected mapping override.
Fixtures clear inherited routing settings and block real network access.

### Final combined regression

The preceding checkpoint's complete 19-module union, the complete updated
compatibility module and the 15 existing eval failure/transport/orchestrator
baselines ran in one command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_llm_shared_resolver.py tests/unit/test_llm_deployment_routing.py tests/contract/test_llm_deployment_routing.py tests/contract/test_llm_deployment_map_compatibility.py tests/unit/test_llm_foundation_contracts.py tests/contract/test_foundry_chat_client_aoai.py tests/contract/test_foundry_chat_client.py tests/contract/test_foundry_gateway_fail_closed.py tests/contract/test_llm_model_routing.py tests/contract/test_llm_fallback.py tests/contract/test_llm_logging.py tests/contract/test_audit_record_shape.py tests/contract/test_audit_record_amend_loop_fields.py tests/contract/test_simulation_api_contract.py tests/contract/test_audit_replay_fidelity.py tests/unit/test_llm_adapter_snapshots.py tests/unit/test_aud021_privacy_classification_and_dispatcher.py tests/unit/test_simulation_controller_safety.py apps/api/tests/test_simulation_chat_controller_wiring.py tests/unit/eval/test_foundry_failures.py -q -p no:cacheprovider --tb=short -rN -m 'not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging and not azure_blob_worm_staging and not measurement_staging'
```

Result: **473 passed, 0 failed/errors/skipped/xfail**, **11.65 s**, exit **0**.
One pre-existing Starlette/httpx TestClient deprecation warning remains; no
package upgrade was attempted. Count reconciles as prior 440 + 18 added
edge cases + 15 existing eval cases. All 106 compatibility assertions pass.
Tests use injected fakes; no real inference/embedding or Azure operation.
This is bounded regression validation, **not execution of T020/T021** or a
claim of complete 168-cell production-caller acceptance. No coverage
percentage is claimed.

### Lint, formatting and typing

Exact final commands (preceding scope plus the two source modules):

```powershell
.\.venv\Scripts\python.exe -m ruff check apps/agents/common/llm_config.py apps/agents/common/foundry_chat_client.py apps/agents/common/llm_client.py apps/agents/maf_runtime/chat_client.py apps/agents/dispatcher/agent.py apps/api/app/services/simulation/controller_service.py apps/eval-runner/src/ama_eval/foundry_client.py apps/ingest-runner/src/ama_ingest/embedder.py tests/contract/test_foundry_chat_client_aoai.py tests/contract/test_llm_model_routing.py tests/contract/test_llm_deployment_map_compatibility.py tests/contract/test_llm_deployment_routing.py tests/unit/test_llm_adapter_snapshots.py
.\.venv\Scripts\python.exe -m ruff format --check apps/agents/common/llm_config.py apps/agents/common/foundry_chat_client.py apps/agents/common/llm_client.py apps/agents/maf_runtime/chat_client.py apps/agents/dispatcher/agent.py apps/api/app/services/simulation/controller_service.py apps/eval-runner/src/ama_eval/foundry_client.py apps/ingest-runner/src/ama_ingest/embedder.py tests/contract/test_foundry_chat_client_aoai.py tests/contract/test_llm_model_routing.py tests/contract/test_llm_deployment_map_compatibility.py tests/contract/test_llm_deployment_routing.py tests/unit/test_llm_adapter_snapshots.py
.\.venv\Scripts\python.exe -m mypy --follow-imports=silent apps/agents/common/llm_config.py apps/agents/common/foundry_chat_client.py apps/agents/common/llm_client.py apps/agents/maf_runtime/chat_client.py apps/agents/dispatcher/agent.py apps/api/app/services/simulation/controller_service.py apps/eval-runner/src/ama_eval/foundry_client.py apps/ingest-runner/src/ama_ingest/embedder.py
.\.venv\Scripts\python.exe -m mypy --follow-imports=silent tests/unit/test_llm_adapter_snapshots.py tests/contract/test_llm_deployment_map_compatibility.py tests/contract/test_llm_deployment_routing.py tests/contract/test_foundry_chat_client_aoai.py
git -c core.whitespace=cr-at-eol diff --check
```

All final commands **PASS**: Ruff **13 files**, formatting **13 already
formatted**, configured strict mypy **8 source modules** and **4 test modules**
(existing test overrides apply), CRLF-aware whitespace check. Initial scoped
Ruff/format found one 121-character line in ingest; corrected manually before
the final checks. No casts/new type ignores or unrelated formatting changes.
The known mixed-import mypy identity issue for
`tests/contract/test_llm_model_routing.py` remains separate and unchanged;
that module remains in pytest/Ruff, not the mypy population.

### Historical preservation and checkpoint

Read-only comparison against the original 50 stored hashes:

```powershell
@'
import hashlib
import re
from pathlib import Path
text = Path('specs/041-llm-deployment-routing/verification.md').read_text(encoding='utf-8').split('## Checkpoint integrity and remaining gates')[0]
anchors = dict(re.findall(r'\| `((?:tests/|packages/|apps/)[^`]+)` \| `([a-f0-9]{64})` \|', text))
for name, data_hash, sidecar_hash in re.findall(r'\| `([^`]+\.ndjson)` \| `([a-f0-9]{64})` \| `([a-f0-9]{64})` \|', text):
    anchors[f'fixtures/sim_replays/{name}'] = data_hash
    anchors[f'fixtures/sim_replays/{name}.sha256'] = sidecar_hash
assert len(anchors) == 50, len(anchors)
mismatches = [path for path, expected in anchors.items() if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected]
assert not mismatches, mismatches
print('Historical fingerprint verification: 50/50 unchanged')
'@ | .\.venv\Scripts\python.exe -
```

Result: **50/50 unchanged**, exit **0**. No historical fixture, schema,
audit writer/reader, KQL or query embedder changed.

Only these five paths changed in this checkpoint:

- `apps/eval-runner/src/ama_eval/foundry_client.py`
- `apps/ingest-runner/src/ama_ingest/embedder.py`
- `tests/contract/test_llm_deployment_map_compatibility.py` (append only)
- `specs/041-llm-deployment-routing/verification.md` (this append)
- `specs/041-llm-deployment-routing/tasks.md` (only T018/T019 markers)

Pre-marker tasks SHA-256:
`9f25081a3236bf3e7515cd22b463c80bac71915d5ba01d8b3361657baf8147ec`.
Existing earlier uncommitted work is retained. `.specify/extensions.yml`
was parsed with existing PyYAML before and after implementation: no pre-hook;
the only enabled unconditional post-hook is optional
`verify / speckit.verify.run`, offered but not invoked under the no-hooks
boundary. No mandatory hook exists.

**2/2 authorised tasks complete; 19/52 overall, 33 unchecked.**
No blocker remains within T018/T019. The known test typing-import limitation
and TestClient warning are unrelated and explicitly retained. T020/T021
remain unchecked and unexecuted; no integration acceptance file was added.
The future **28 paths × 6 orders = 168 cells** acceptance sweep is not claimed.
Strict provenance writers/transport-attempt instrumentation remain inactive.
G0/G1/G2/G3/G4/G5a/G5b/G6 remain independent and closed; this is an inactive
local candidate, not deployment readiness. No Azure operations, real calls,
IaC/model changes, resource operations, activation or commits.
**STOP before T020. Return to the orchestrator; no handoff.**

## T020–T021 checkpoint — complete LOCAL US1 request-routing acceptance

### Authority, scope and result

- Authorisation: **“Approve — execute T020–T021 only, then checkpoint”**.
  Retained `model-upgrade-chat-sumlation`; no branch operation or commit.
- Prerequisites again resolve to `C:\code\ama\specs\041-llm-deployment-routing`.
  Read-only checklist gates remain requirements **16/16**, routing-rollout
  **36/36**, zero unchecked; no reviewer markers changed. Read the exact tasks,
  routing contract, quickstart, design context, caller inventory and applicable
  commenting/review guidance. Existing ignore files suffice; no setup changes.
- **T020 complete**: added only
  `tests/integration/test_llm_deployment_routing.py` (189 parametrized cases).
  No production source correction, dependency installation or refactoring.
- **T021 complete LOCAL**: **168/168 SC-001 cells**, SC-002/SC-003 routing
  cases below and the established regression union pass. Final union:
  **681 passed, 0 failed/errors/skipped/xfail**, one existing warning, **9.15 s**.
  This is routing acceptance, not provenance or target release acceptance.
- Prior uncommitted work is retained. Initial new-test runs exposed only
  synthetic fixture/assertion mistakes: stream identity lives on
  `attempt_evidence.resolved_identity`, risk assessments require a signal,
  and PublicAlert requires its `ca-` ID and tenant-consistent rehearsal mode.
  Initial results were 30 failed/159 passed, then 6 failed/183 passed;
  corrections produced 189 passed in 4.88 s without production changes.
- First combined run: 677 passed/4 failed in 10.01 s. Earlier controller
  regressions had consumed the process-shared rate limiter for the same
  synthetic tenant/user, masking configuration errors with `rate_limited`.
  Isolated the new fixture using a fresh **real** `RateLimiter` per controller,
  retaining defaults and checks, not bypassing them. The same union then
  passed all 681. No production routing defect was uncovered.

### Closed SC-001 matrix — concrete collected and passing nodes

Every suffix in this table is a complete executable pytest node when appended
to the common prefix
`tests/integration/test_llm_deployment_routing.py::test_inventory_request_routing`.
**Every listed node was collected and passed in the final union.**
RDS/RSD/DRS/DSR/SRD/SDR name actual `ALIAS_CSV_ORDERINGS` permutations, not
environment insertion order. Each has three distinct alias destinations with
all three configured model coordinates equal to the synthetic shared MODEL_KEY.
The ambiguous shared coordinate is correctly omitted from valid CSVs;
six conflicting shared-coordinate permutations are tested separately.
No denominator adjustment: **C01–C23 + A01–A05 = 28 paths × 6 = 168 cells**.

| Path | Real caller/capability exercised | Tier | Six collected/passing node suffixes |
| --- | --- | --- | --- |
| C01 | RiskAssessmentAgent.generate_assessment → mixin/wrapper | R | `[C01-RDS]`, `[C01-RSD]`, `[C01-DRS]`, `[C01-DSR]`, `[C01-SRD]`, `[C01-SDR]` |
| C02 | RiskAssessmentAgent._generate_recommendation (coordination) → mixin/wrapper | R | `[C02-RDS]`, `[C02-RSD]`, `[C02-DRS]`, `[C02-DSR]`, `[C02-SRD]`, `[C02-SDR]` |
| C03 | RiskAssessmentAgent.recommend_public_alert → mixin/wrapper | R | `[C03-RDS]`, `[C03-RSD]`, `[C03-DRS]`, `[C03-DSR]`, `[C03-SRD]`, `[C03-SDR]` |
| C04 | Risk create_app /health via ASGI → wrapper probe | R | `[C04-RDS]`, `[C04-RSD]`, `[C04-DRS]`, `[C04-DSR]`, `[C04-SRD]`, `[C04-SDR]` |
| C05 | MonitoringAgent.summarize_signal → wrapper | D | `[C05-RDS]`, `[C05-RSD]`, `[C05-DRS]`, `[C05-DSR]`, `[C05-SRD]`, `[C05-SDR]` |
| C06 | MonitoringAgent.evaluate_escalated_signal → to_thread(wrapper), not streaming | R | `[C06-RDS]`, `[C06-RSD]`, `[C06-DRS]`, `[C06-DSR]`, `[C06-SRD]`, `[C06-SDR]` |
| C07 | IndicatorAnalysisService.analyse_cross_domain_correlations → wrapper | D | `[C07-RDS]`, `[C07-RSD]`, `[C07-DRS]`, `[C07-DSR]`, `[C07-SRD]`, `[C07-SDR]` |
| C08 | MultilingualTranslator._generate_content → mixin/wrapper | D | `[C08-RDS]`, `[C08-RSD]`, `[C08-DRS]`, `[C08-DSR]`, `[C08-SRD]`, `[C08-SDR]` |
| C09 | MultilingualTranslator.back_translate_and_score → mixin/wrapper; injected embedding vectors | D | `[C09-RDS]`, `[C09-RSD]`, `[C09-DRS]`, `[C09-DSR]`, `[C09-SRD]`, `[C09-SDR]` |
| C10 | EvacuationAgent's constructor-wired pipeline._stage_8_plan_summary → mixin/wrapper | R | `[C10-RDS]`, `[C10-RSD]`, `[C10-DRS]`, `[C10-DSR]`, `[C10-SRD]`, `[C10-SDR]` |
| C11 | ThreadedDependencyHealthMonitor.probe_once on actual EvacuationAgent → wrapper | R | `[C11-RDS]`, `[C11-RSD]`, `[C11-DRS]`, `[C11-DSR]`, `[C11-SRD]`, `[C11-SDR]` |
| C12 | ResourceAllocationAgent's constructor-wired pipeline._generate_summary → mixin/wrapper | R | `[C12-RDS]`, `[C12-RSD]`, `[C12-DRS]`, `[C12-DSR]`, `[C12-SRD]`, `[C12-SDR]` |
| C13 | MonitoringMafAgent.run_maf → YAML/factory → real Agent.run → SDK HTTP | R | `[C13-RDS]`, `[C13-RSD]`, `[C13-DRS]`, `[C13-DSR]`, `[C13-SRD]`, `[C13-SDR]` |
| C14 | RiskAssessmentMafAgent.run_maf → YAML/factory → real Agent.run → SDK HTTP | R | `[C14-RDS]`, `[C14-RSD]`, `[C14-DRS]`, `[C14-DSR]`, `[C14-SRD]`, `[C14-SDR]` |
| C15 | CommunicationMafAgent.run_maf → YAML/factory → real Agent.run → SDK HTTP | R | `[C15-RDS]`, `[C15-RSD]`, `[C15-DRS]`, `[C15-DSR]`, `[C15-SRD]`, `[C15-SDR]` |
| C16 | ResourceAllocationMafAgent.run_maf → YAML/factory → real Agent.run → SDK HTTP | R | `[C16-RDS]`, `[C16-RSD]`, `[C16-DRS]`, `[C16-DSR]`, `[C16-SRD]`, `[C16-SDR]` |
| C17 | Controller.stream_turn → first completion + reassembled-tool follow-up completion | S | `[C17-RDS]`, `[C17-RSD]`, `[C17-DRS]`, `[C17-DSR]`, `[C17-SRD]`, `[C17-SDR]` |
| C18 | Dispatcher POST /monitoring/invoke via ASGI | S | `[C18-RDS]`, `[C18-RSD]`, `[C18-DRS]`, `[C18-DSR]`, `[C18-SRD]`, `[C18-SDR]` |
| C19 | Dispatcher POST /planning/invoke via ASGI | S | `[C19-RDS]`, `[C19-RSD]`, `[C19-DRS]`, `[C19-DSR]`, `[C19-SRD]`, `[C19-SDR]` |
| C20 | Dispatcher POST /risk-assessment/invoke via ASGI | S | `[C20-RDS]`, `[C20-RSD]`, `[C20-DRS]`, `[C20-DSR]`, `[C20-SRD]`, `[C20-SDR]` |
| C21 | Dispatcher POST /communication/invoke via ASGI | S | `[C21-RDS]`, `[C21-RSD]`, `[C21-DRS]`, `[C21-DSR]`, `[C21-SRD]`, `[C21-SDR]` |
| C22 | Dispatcher POST /evacuation/invoke via ASGI | S | `[C22-RDS]`, `[C22-RSD]`, `[C22-DRS]`, `[C22-DSR]`, `[C22-SRD]`, `[C22-SDR]` |
| C23 | Dispatcher POST /resource-allocation/invoke via ASGI | S | `[C23-RDS]`, `[C23-RSD]`, `[C23-DRS]`, `[C23-DSR]`, `[C23-SRD]`, `[C23-SDR]` |
| A01 | Direct LiveFoundryChatClient.chat_complete(simulation) | S | `[A01-RDS]`, `[A01-RSD]`, `[A01-DRS]`, `[A01-DSR]`, `[A01-SRD]`, `[A01-SDR]` |
| A02 | Direct LiveFoundryChatClient.chat_complete_stream(reasoning) | R | `[A02-RDS]`, `[A02-RSD]`, `[A02-DRS]`, `[A02-DSR]`, `[A02-SRD]`, `[A02-SDR]` |
| A03 | Direct LiveFoundryChatClient.chat_complete_stream(drafting) | D | `[A03-RDS]`, `[A03-RSD]`, `[A03-DRS]`, `[A03-DSR]`, `[A03-SRD]`, `[A03-SDR]` |
| A04 | Direct LiveFoundryChatClient.chat_complete_stream(simulation) | S | `[A04-RDS]`, `[A04-RSD]`, `[A04-DRS]`, `[A04-DSR]`, `[A04-SRD]`, `[A04-SDR]` |
| A05 | MAF drafting factory → real OpenAIChatClient.get_response → SDK HTTP | D | `[A05-RDS]`, `[A05-RSD]`, `[A05-DRS]`, `[A05-DSR]`, `[A05-SRD]`, `[A05-SDR]` |

Proof boundaries:

- **132 common SDK cells** assert exactly one downstream
  `azure.ai.inference[.aio].ChatCompletionsClient.complete(model=destination)`
  and the AOAI `/openai/deployments/{destination}` endpoint. Actual callers,
  mixins and wrapper selection run; no resolver is replaced. Defaults remain
  unchanged outside each fixture. Stream identity is also checked on the
  existing optional evidence seam, with no attempted/succeeded claim.
- **30 MAF cells** execute real adapter/OpenAI request serialization into
  `httpx.MockTransport`, asserting JSON `model` and `/openai/responses` URL.
  Four real facades load their YAMLs, construct the real Agent/middleware and
  validate the synthetic response against their actual output schemas.
  Only HTTP/auth and audit persistence are doubled; audit contents are not
  provenance acceptance. A05 uses the supported direct drafting adapter.
- **6 controller cells**, **12 requests**, assert `model` on **both** actual
  `chat.completions.create` entries, endpoint, `stream`, tools, `tool_choice`,
  assembled tool-call ID and tool-result history. The fake tool stream sends
  fragmented `{`/`}` arguments; the real controller reassembles and executes
  its injected tool seam, then emits start/call/result/delta/end events.
  Mid-loop environment mutation cannot change the captured destination.
- ASGI dispatcher cases preserve HTTP response shape, citations list,
  prompt hash, invocation ID, role-specific system prompt and returned
  deployment. C04 also uses real ASGI health routing; C10/C12 use the actual
  agents' constructor-wired callbacks, not manually substituted generators.
- Total **174 synthetic downstream request observations**, not a denominator
  of 174: extra controller rounds do not create extra path/order cells.
  Tier cells: reasoning **78**, drafting **36**, simulation **54**.
  Network denial covers DNS and outbound sockets within each opt-in fixture;
  credentials, inference/embedding and external persistence never go live.
  Token counting uses the existing local heuristic, avoiding tokenizer fetches.
  A collection-time Cartesian-set check independently confirmed all 28 IDs,
  all six order IDs, **168 unique nodes**, six per path and 28 per order.

### SC-002 / SC-003 and supported compatibility evidence

The following populations all pass in the final union. These are additional
acceptance obligations, **not replacements for the 168-cell denominator**.
Function names are executable selectors in the indicated modules.

| Local obligation | Concrete executed evidence / population |
| --- | --- |
| SC-002 successful controller + all six roles | Matrix C17–C23: **42/42 path/order cells**, 48 downstream requests, all explicit simulation. A01/A04 add 12 simulation adapter cells separately. |
| Absent versus explicit-empty/whitespace simulation, even with aliases/shared model keys present | New integration `::test_simulation_required_on_every_public_role_and_controller`: **3/3 nodes**, each exercises six ASGI roles + controller (**21 invalid path visits**); actionable setting error/degraded evidence, zero requests/no live fallback. A reasoning call afterwards succeeds, proving path-local degradation. |
| Conflicting shared-model raw CSV, every ordering | New integration `::test_conflicts_reach_no_adapter_request`: **6/6 nodes**; all six roles, controller, common sync/stream for all tiers, C01–C12 callers/wrappers, all four actual MAF facades and drafting factory have zero downstream requests; diagnostic names conflicting MODEL_KEY. Earlier contract conflict nodes assert both destinations and safe diagnostics; parser pair-order cases also pass. |
| Effective-live isolation with no explicit live deployments or mixed explicit/legacy live tiers | New integration `::test_effective_legacy_isolation_at_public_requests`: **12/12 nodes** = alias/exact/base × both-legacy/mixed × distinct/collision. Each exercises all six roles and controller; **42 colliding path visits** fail before request, **42 distinct-control visits** succeed (48 control requests). Comparison is against effective drafting destination; existing unit cases additionally cover both live tiers/unresolved comparisons. |
| Missing endpoint/region, unsupported key, partial/inconsistent metadata, invalid injected maps, alias/exact/base precedence | Existing `tests/unit/test_llm_deployment_routing.py::{test_missing_required_connection_setting_fails_before_transport,test_unsupported_chat_tier_does_not_become_an_arbitrary_map_alias,test_invalid_identity_fails_before_transport,test_absent_explicit_allows_alias_but_empty_is_invalid,test_live_tier_alias_exact_base_precedence,test_unresolved_required_live_comparison_fails_only_simulation}` plus full shared-resolver/contract populations; invalid cases assert errors and zero requests. No language-constant-only test was added. |
| Explicit A versus unique coordinate-to-B, matching A and absent association | `tests/contract/test_llm_deployment_routing.py::test_request_identity_is_not_borrowed_from_another_destination`: **6/6 nodes**, sync/stream × three associations, actual SDK model A plus existing response/chunk resolved identity seam. B/absent cannot supply model metadata; matching A can. Wrong-account proof remains covered by `tests/unit/test_llm_deployment_routing.py::test_wrong_account_proof_cannot_supply_explicit_destination_identity`. This is metadata association, **not SC-004 production audit provenance**. |
| Snapshot immutability / no aliases needed / misleading names / error boundaries | Entire existing common/MAF contract and adapter-snapshot modules pass, including captured wrapper/MAF/dispatcher/controller settings, no-alias SDK calls, independent configured identity, MAF ValueError/cause, safe diagnostics and no production fallback to test-only Azure OpenAI settings. |
| Legacy common exact/base and deliberate eval per-run mapping | `tests/contract/test_llm_deployment_routing.py::test_common_legacy_model_key_injection_remains_executable` (2 SDK nodes) and `::test_maf_legacy_test_configuration_still_submits_a_request` (2 HTTP nodes); compatibility module `::test_eval_deliberate_per_run_exact_mapping_remains_supported` (2 SDK nodes), `::test_eval_omitted_shared_coordinate_never_guesses_a_tier` (3 zero-request nodes), plus retained eval baseline. |
| Embedding coordinate/destination/dimensions retained, no chat-tier adoption | Compatibility module `::test_ingest_embedding_request_preserves_model_destination_and_dimensions` (2 SDK nodes), `::test_direct_query_embedding_retains_env_destination_and_rejects_dimension_mismatch` (2 SDK nodes), six alias-order embedding lookup cases, exact/base and parser conformance cases; full **106-case** module passes. No real embeddings. |

SC-003 is **LOCAL PASS for the complete enumerated invalid-case acceptance
population**: no failures/skips, errors precede inference; diagnostics name
the missing/invalid setting or unsupported/conflicting key and destinations.
No claim of deployment-time configuration admission, arbitrary fuzz coverage,
target Azure validation or later audit writer admission is made.

### Reproduction commands and final results

Exact matrix collection, standalone module execution and final regression union:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/integration/test_llm_deployment_routing.py::test_inventory_request_routing --collect-only -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest tests/integration/test_llm_deployment_routing.py -q -p no:cacheprovider --tb=short -rN
.\.venv\Scripts\python.exe -m pytest tests/unit/test_llm_shared_resolver.py tests/unit/test_llm_deployment_routing.py tests/contract/test_llm_deployment_routing.py tests/contract/test_llm_deployment_map_compatibility.py tests/unit/test_llm_foundation_contracts.py tests/contract/test_foundry_chat_client_aoai.py tests/contract/test_foundry_chat_client.py tests/contract/test_foundry_gateway_fail_closed.py tests/contract/test_llm_model_routing.py tests/contract/test_llm_fallback.py tests/contract/test_llm_logging.py tests/contract/test_audit_record_shape.py tests/contract/test_audit_record_amend_loop_fields.py tests/contract/test_simulation_api_contract.py tests/contract/test_audit_replay_fidelity.py tests/unit/test_llm_adapter_snapshots.py tests/unit/test_aud021_privacy_classification_and_dispatcher.py tests/unit/test_simulation_controller_safety.py apps/api/tests/test_simulation_chat_controller_wiring.py tests/unit/eval/test_foundry_failures.py tests/contract/test_llm_managed_identity.py tests/contract/test_llm_circuit_breaker.py tests/integration/test_llm_deployment_routing.py -q -p no:cacheprovider --tb=short -rN -m 'not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging and not azure_blob_worm_staging and not measurement_staging'
```

- Collection: **168 unique matrix nodes**, **3.27 s**, exit 0; verbose node
  list is in the session output. Independent collection set/count check passed.
- Standalone integration before the limiter-isolation fix: **189 passed**,
  **4.88 s**, exit 0. The final union reruns every node after that fix.
- Final union: **681 passed**, **9.15 s**, exit 0. Count reconciles as
  preceding **473** + **19** required managed-identity/circuit-breaker cases
  + **189** new integration cases. No unrelated suite expansion.
- One pre-existing Starlette/httpx TestClient deprecation warning remains;
  no installation or upgrade. No numeric coverage threshold is specified by
  the constitution; no line/branch coverage percentage is claimed.

Quality commands (same preceding 13-file scope plus the one new test):

```powershell
$files = @('apps/agents/common/llm_config.py','apps/agents/common/foundry_chat_client.py','apps/agents/common/llm_client.py','apps/agents/maf_runtime/chat_client.py','apps/agents/dispatcher/agent.py','apps/api/app/services/simulation/controller_service.py','apps/eval-runner/src/ama_eval/foundry_client.py','apps/ingest-runner/src/ama_ingest/embedder.py','tests/contract/test_foundry_chat_client_aoai.py','tests/contract/test_llm_model_routing.py','tests/contract/test_llm_deployment_map_compatibility.py','tests/contract/test_llm_deployment_routing.py','tests/unit/test_llm_adapter_snapshots.py','tests/integration/test_llm_deployment_routing.py')
.\.venv\Scripts\python.exe -m ruff check @files
.\.venv\Scripts\python.exe -m ruff format --check @files
.\.venv\Scripts\python.exe -m mypy --follow-imports=silent @($files[0..7])
.\.venv\Scripts\python.exe -m mypy --follow-imports=silent tests/unit/test_llm_adapter_snapshots.py tests/contract/test_llm_deployment_map_compatibility.py tests/contract/test_llm_deployment_routing.py tests/contract/test_foundry_chat_client_aoai.py tests/integration/test_llm_deployment_routing.py
git -c core.whitespace=cr-at-eol diff --check
```

All pass: Ruff **14 files**, formatting **14 already formatted**,
configured mypy **8 source + 5 test modules** (existing test overrides apply).
The new file was rechecked after the fixture fix: lint/format/mypy all pass.
The unrelated legacy routing-test duplicate-import mypy limitation is unchanged;
that module remains in pytest/Ruff, not the mypy population. No new cast/ignore.

The exact read-only **50-hash comparison script in the preceding checkpoint**
was rerun against its original anchors before
`## Checkpoint integrity and remaining gates`: **50/50 unchanged**, exit 0.
No historical schema/fixture/NDJSON/sidecar is edited. Post-evidence integrity
and whitespace checks are repeated before returning this checkpoint.

### Checkpoint limits and changed paths

Only these three paths change in T020/T021:

- `tests/integration/test_llm_deployment_routing.py` (new).
- `specs/041-llm-deployment-routing/verification.md` (this append).
- `specs/041-llm-deployment-routing/tasks.md` (T020/T021 markers only).

Pre-marker tasks SHA-256:
`cd77e382c811f1c7e63dbac1bd1a6604e215afab5a596f1b2a07de80aafb9c67`.
**2/2 authorised tasks complete; 21/52 overall, 31 unchecked.**
No local routing blocker remains. No T022 or later task was started.

SC-001/002/003 here are **LOCAL routing acceptance only**. The strict code is
an **inactive local candidate**, not deployable alone against old ambiguous
CSV. A cleaned configuration/revision pairing, compatible readers,
coordinated US2 release evidence and G4 approval remain external requirements.
Target release, Azure baseline parity, optional real migration acceptance
and audit provenance are **not executed/not accepted** here. SC-004 strict
production schemas/writers and transport-submission instrumentation remain
unstarted; optional attempt evidence still defaults to unknown. No emission
or transport-observation claim is inferred from a successful mock request.
Help stays disabled/stubbed and telemetry injection stays an optional seam.

No Azure reads/writes, real model/embedding inference, IaC/model choice,
resource operation, hook execution, workflow, delegation, handoff or commit.
Extension configuration was read only; no mandatory implementation hook exists;
the optional verify hook is not invoked under the explicit no-hooks scope.
G0/G1/G2/G3/G4/G5a/G5b/G6 remain independently closed.
**STOP before T022. Return to the orchestrator and stop.**

## T022/T023/T028/T029 — approved offline US2 checkpoint

### Authority, scope and delivered paths

Authorisation: **“Approve — execute T022–T023 and T028–T029 only, then
checkpoint”**. Actual branch `model-upgrade-chat-sumlation` retained.
Prerequisite script returned this absolute feature directory and the established
available documents. Requirements checklist **16/16** and routing-rollout
checklist **36/36** checked; both were read-only gates, not implementation
markers. Read the scoped tasks, spec/plan/data model, routing/rollout contracts,
research/quickstart, constitution and governing code instructions.

Only these six paths are delivered/updated by this lane:

- `tests/contract/test_llm_deployment_configuration.py` — new synthetic
  compiled/preflight contract fixtures and executable CLI assertions.
- `tests/unit/test_llm_deployment_preflight.py` — new local failure/policy/
  reconciliation tests, subprocess exit/stdout/stderr boundaries, file
  immutability and a child audit hook prohibiting network/subprocess/writes.
- `scripts/verify-llm-deployment-preflight.py` — new local read-only comparison
  tool, stdlib plus existing shared routing validation; no dependency changes.
- `specs/041-llm-deployment-routing/rollout-evidence.md` — exact input contract,
  executable synthetic example and future approval-gated rollout/rollback.
- `specs/041-llm-deployment-routing/tasks.md` — only T022/T023/T028/T029 markers.
- `specs/041-llm-deployment-routing/verification.md` — this append.

Existing source/test work is preserved. Setup verification found existing
Git/Docker ignore files covering the Python/Node/tool outputs and secrets;
the existing web flat ESLint config covers node_modules/dist/build/coverage/
minified files. The root package is private, so no publishing ignore is
required; no Prettier config, Terraform or Helm change applies to this lane.
No setup or lockfile edits were needed.

### Tool contract and acceptance boundary

```powershell
.\.venv\Scripts\python.exe scripts/verify-llm-deployment-preflight.py --inventory C:\evidence\inventory.json --baseline C:\evidence\baseline.json --outputs C:\evidence\outputs.json --candidate C:\evidence\candidate.json
```

These are **already supplied/authorised local files**, not collection commands.
Common envelopes require exact target tenant/subscription/resource group/account/
environment/endpoint/region, observation/source revisions, current approvals,
approved freshness policy ID/version, explicit invalidation evaluation and
exact candidate configuration/image/compiled-proposal bindings. Baseline
additionally supplies approved state/policy, with explicit reconciliation if
pre-candidate bindings differ. Supplied G0 scope/window must cover baseline and
inventory collection. The tool compares full supplied model/name/version/
format/SKU/capacity/RAI/effective-filter/upgrade, access/RBAC/managed identity/
network/auth/diagnostics/AU-residency and embedding snapshots.

Outputs must preserve baseline resource/protection properties, pass all nine
top-level selections unchanged to child selections, and describe exactly the
candidate API/agents image/revision/env pairs. Their actual configuration digest
is computed, not accepted as an unrelated string. Complete per-tier identities,
endpoint/region, direct embedding env and actual raw CSV are checked for both
services through the shared validator/resolver. Ambiguous model coordinates
are omitted, aliases and embedding retained, unambiguous configured legacy
keys preserved, and simulation remains isolated. Historical conflicting CSV
may be observed as current evidence but cannot be replayed as candidate env.

Exit 0 emits only local-comparison status with **target_readiness:
not established**. Exit 1 has actionable location/rule stderr and empty stdout;
usage errors exit 2. Malformed/duplicate/non-finite/over-nested JSON, unreadable
files/properties, wrong types and incomplete/stale/unbound/unapproved evidence
fail closed without payload/secret echo. No refresh, ARM/network request,
configuration mutation or authority inference exists.

`--at` overrides use time **only if all four files are labelled synthetic**.
The fixture's 2040 timestamps and two-hour age window are test policy values,
not a production TTL. The tool does not authenticate the supplied declarations
or validate external governance/AVM/What-If/rollback artifacts. Reviewers must
authenticate completeness and authority separately. `rollout-evidence.md`
records those limits and their freshness/reapproval obligations.

**T022 is synthetic compiled/preflight contract acceptance only.** It tests
independent selections and actual CLI rejection of changed child/top-level
selections, changed existing names, metadata/CSV/protection drift and pair
mismatch. It accepts already-established purpose-named baselines, but rejects
applying new-resource purpose defaults over approved old identities. It does
not prove actual Bicep defaulting/pass-through or real target resource diffs:
T024–T027/T030 remain blocked and unchecked.

### Test-first execution and final regression commands

Initial test-first command, before adding the CLI:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/contract/test_llm_deployment_configuration.py tests/unit/test_llm_deployment_preflight.py -q -p no:cacheprovider --tb=no -rN
```

Result: **148 failed**, **16.64 s**, exit 1, because the CLI did not yet
exist. Initial implementation yielded **144 passed/4 failed**; the four
failures required the missing-reconciliation diagnostic to explicitly explain
changed bindings. The diagnostic was corrected, not assertions weakened.
Additional bounded cases cover actual policy/parser/output/read-only boundaries;
there are now **171 new tests**. No skip/xfail or combinatorial routing expansion.

Final consolidated execution uses exactly the preceding established 681-test
union plus the two new modules:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/contract/test_llm_deployment_configuration.py tests/unit/test_llm_deployment_preflight.py tests/unit/test_llm_shared_resolver.py tests/unit/test_llm_deployment_routing.py tests/contract/test_llm_deployment_routing.py tests/contract/test_llm_deployment_map_compatibility.py tests/unit/test_llm_foundation_contracts.py tests/contract/test_foundry_chat_client_aoai.py tests/contract/test_foundry_chat_client.py tests/contract/test_foundry_gateway_fail_closed.py tests/contract/test_llm_model_routing.py tests/contract/test_llm_fallback.py tests/contract/test_llm_logging.py tests/contract/test_audit_record_shape.py tests/contract/test_audit_record_amend_loop_fields.py tests/contract/test_simulation_api_contract.py tests/contract/test_audit_replay_fidelity.py tests/unit/test_llm_adapter_snapshots.py tests/unit/test_aud021_privacy_classification_and_dispatcher.py tests/unit/test_simulation_controller_safety.py apps/api/tests/test_simulation_chat_controller_wiring.py tests/unit/eval/test_foundry_failures.py tests/contract/test_llm_managed_identity.py tests/contract/test_llm_circuit_breaker.py tests/integration/test_llm_deployment_routing.py -q -p no:cacheprovider --tb=short -rN -m 'not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging and not azure_blob_worm_staging and not measurement_staging'
```

Final after formatting and cross-platform file-write audit-mask correction:
**852 passed (171 + 681)**, **40.70 s**, exit 0, no failures/errors/skips/xfails.
One unchanged Starlette/httpx TestClient deprecation warning remains;
no upgrade/install was performed. Earlier consolidated runs passed 845
(before seven added boundary cases) and 852; the final run supersedes them.
No numeric coverage percentage/threshold is claimed.

The established US1 inventory collection was repeated with a uniqueness/count
assertion (all those cells also ran in the final passing union):

```powershell
@'
import subprocess, sys
args = [sys.executable, '-m', 'pytest', 'tests/integration/test_llm_deployment_routing.py::test_inventory_request_routing', '--collect-only', '-q', '-p', 'no:cacheprovider']
p = subprocess.run(args, text=True, capture_output=True, check=False)
nodes = [line for line in p.stdout.splitlines() if line.startswith('tests/integration/test_llm_deployment_routing.py::test_inventory_request_routing[')]
assert p.returncode == 0, p.stderr
assert len(nodes) == len(set(nodes)) == 168, (len(nodes), p.stdout)
print('US1 request routing inventory: 168 unique cells collected; all included in passing regression union')
'@ | .\.venv\Scripts\python.exe -
```

Result: **168 unique cells**, exit 0. No previous routing source, request
seam, test cell or evidence inventory was changed.

### Lint, format, strict types and historical preservation

```powershell
$files = @('apps/agents/common/llm_config.py','apps/agents/common/foundry_chat_client.py','apps/agents/common/llm_client.py','apps/agents/maf_runtime/chat_client.py','apps/agents/dispatcher/agent.py','apps/api/app/services/simulation/controller_service.py','apps/eval-runner/src/ama_eval/foundry_client.py','apps/ingest-runner/src/ama_ingest/embedder.py','tests/contract/test_foundry_chat_client_aoai.py','tests/contract/test_llm_model_routing.py','tests/contract/test_llm_deployment_map_compatibility.py','tests/contract/test_llm_deployment_routing.py','tests/unit/test_llm_adapter_snapshots.py','tests/integration/test_llm_deployment_routing.py','scripts/verify-llm-deployment-preflight.py','tests/contract/test_llm_deployment_configuration.py','tests/unit/test_llm_deployment_preflight.py')
.\.venv\Scripts\python.exe -m ruff check @files
.\.venv\Scripts\python.exe -m ruff format --check @files
.\.venv\Scripts\python.exe -m mypy --follow-imports=silent @($files[0..7])
.\.venv\Scripts\python.exe -m mypy --follow-imports=silent tests/unit/test_llm_adapter_snapshots.py tests/contract/test_llm_deployment_map_compatibility.py tests/contract/test_llm_deployment_routing.py tests/contract/test_foundry_chat_client_aoai.py tests/integration/test_llm_deployment_routing.py
.\.venv\Scripts\python.exe -m mypy --config-file= --strict --ignore-missing-imports --explicit-package-bases --follow-imports=silent @($files[14..16])
git -c core.whitespace=cr-at-eol diff --check
```

Final: Ruff **PASS**, **17 already formatted**; established configured mypy
**8 source + 5 test modules PASS**, and **all 3 new Python files PASS under
strict mypy with empty config**, deliberately bypassing the repository's
`tests.* ignore_errors` override. Initial truly strict execution exposed six
inference/narrowing issues; explicit runtime narrowing and fixture annotations
fixed them without casts/ignores. An intermediate format check reported two
files; they were formatted, then the final tests and checks above reran.
The established unrelated duplicate-import mypy limitation is unchanged.
These are scoped checks, not a repository-wide type/coverage claim.

The exact original read-only 50-hash script in the preceding checkpoint was
rerun against the anchors before `## Checkpoint integrity and remaining gates`:
**50/50 unchanged**, exit 0. Historical fixtures/NDJSON/sidecars/KQL/schema
anchors were not regenerated, reserialised or updated. Post-document/marker
integrity and whitespace checks are repeated before return.

Pre-marker `tasks.md` raw SHA-256:
`d03f8db5d679fd2d9c6aae3c1d520c37bed82cbbc21142f7fd805f869ea4d2ed`.
Reversing only the four selected markers must reproduce it.

### Remaining gates and stop

**4/4 authorised tasks complete; 25/52 overall, 27 unchecked.**
Only T022/T023/T028/T029 were marked `[X]`.

- **T024–T027/T030 BLOCKED and unchecked**: no approved target baseline/G0
  collection scope, current inherited governance or pinned AVM evidence;
  no Bicep/ARM/parameter authoring, acquisition, compile/lint or discovery.
- **US3/T031–T044 pending/unstarted**: reader-first provenance compatibility,
  schemas, strict production writers and actual submission observation remain
  future tasks. Existing optional attempt evidence is not promoted to proof.
- T045–T052 remain pending; no automatic continuation/handoff.
- **Target P1 readiness BLOCKED**: actual approved baseline, policy/version/
  revisions, G1–G3, compatible readers/candidate pairs, actual compiled
  acceptance, mandatory reviewed What-If/carve-out/live metadata and G4
  stage-scoped release authority are absent. Local exit 0 is not this gate.
- **Real P2 acceptance BLOCKED**: G5a/headroom/proposal/provisioning,
  post-provision actual readiness, G5b traffic/switch/forward/rollback evidence
  remain unsupplied; G6 retirement is independent. Synthetic evidence cannot
  supply SC-006 operational acceptance.

No Azure reads/writes, real model/embedding calls, hook/workflow/delegation,
dependency changes or commits occurred. Extension configuration was read
before/after; there are no mandatory implementation hooks. The optional verify
hook was not invoked under the explicit no-hooks scope.

**STOP before US3/T031. Return this checkpoint to the orchestrator and stop.**

Final read-only checkpoint checks confirmed **50/50 original fingerprints**,
the exact pre-marker task SHA after reversing only the four approved markers,
**25/52 complete with exactly T024–T027/T030/T031–T052 pending**, and clean
`git diff --check`. The executable synthetic example in `rollout-evidence.md`
was run exactly as documented using a new temporary directory: exit **0**,
the documented local-only status JSON, empty stderr. No historical fixture
was regenerated. Final extension inspection found only the optional verify
implementation hook; its notice was surfaced, not invoked. No continuation.

## T031–T033 tests-first authoring checkpoint — 2026-10-19

**Authority:** “Approve — execute T031–T033 tests first, then checkpoint”.
Branch `model-upgrade-chat-sumlation` retained. This section supersedes only the
preceding pending-T031 stop, not its historical evidence. Prerequisites returned
this absolute feature directory; read-only checklist gates remain **16/16**
and **36/36**, with zero unchecked. No checklist marker was edited.

### Authored tests and observed results

| New module | Collected | Passed | Expected behavioural red |
| --- | ---: | ---: | ---: |
| `tests/contract/test_llm_deployment_provenance_schema.py` (T031) | 38 | 17 | 21 |
| `tests/unit/test_llm_inference_attempt_evidence.py` (T032) | 15 | 1 | 14 |
| `tests/contract/test_llm_deployment_provenance.py` (T033) | 25 | 0 | 25 |
| **Total** | **78** | **18** | **60** |

T031 reuses the T005 synthetic dispatcher examples and unchanged historical
audit fixture helpers. It exercises both strict readers concurrently, independently
optional/nullable fields, required string identities/`unknown`, existing extra-field
and call-kind rejection, historical uncertain-read compatibility, replay inputs,
invocation AIIMS/partition/deployment and the actual lessons export projection.
Historical fixture-source/replay/sidecar bytes remain protected by the original
50 fingerprints; no archived production LLM dataset is invented.

T032 executes the **installed azure-ai-inference sync/async SDKs**, real JSON/SSE
serialization, authentication policies and pipeline into fake
`HttpTransport.send` / `AsyncHttpTransport.send`. The request ledger observes
SDK `x-ms-client-request-id`, serialized deployment and AOAI destination URL;
future evidence must bind that actual handoff, not a separately fabricated spy ID.
Credential rejection demonstrably enters the real pipeline but reaches zero
transport sends; local unserialisable content fails inside the real SDK before
handoff. Submitted timeout/403/500, empty/filtered completions and streamed partial
failure/cancel/missing terminal completion all reach the fake outbound boundary.
The supported opaque injection control has **no observable transport** and remains
null/unknown; its method-entry ledger is deliberately not submission evidence.
No expected provenance object is injected into the instrumented common path.

T033 runs the actual common wrapper/mixin/telemetry, dispatcher ASGI endpoint,
API production invoker/parser, MAF chat adapter/middleware and controller.
MAF and controller use real OpenAI SDKs with `httpx.MockTransport`; only the
explicit unavailable-observation controls return ordinary uninstrumented output.
The no-RAG controller has an enabled in-memory owning writer and checks the
five admission counts **1/1/1/0/0**, including event/turn retention for false and
unknown submission. Distinct two-round expectations are **2** for both success,
**2** for later submitted failure, and **1** for later unknown submission.
Remote true/unknown-completion and null/unknown-submission are distinct consumer
inputs. API HTTP envelopes must never add a duplicate dispatcher model row.

These are **completed test-authoring tasks**, not passing US3 implementation,
SC-004/SC-007 acceptance, reader compatibility or release readiness.

### Expected red mapped to future implementation tasks

Counts below assign each failure once; coupled prerequisites are stated explicitly.
All failures are runtime behaviour/validation assertions, not collection errors.

| Future task | Red nodes | Observed reason / retained assertion |
| --- | ---: | --- |
| T034 | 18 | Pydantic and JSON readers reject the additive attempt/outcome fields, including independently supplied and nullable fields. Valid `unknown` support must precede the invalid-enum assertion. Keep both schema mirrors strict; never reclassify historical false/null rows as invalid new writes. |
| T035 | 3 | Invocation reader rejects additive model/attempt fields before the lessons projection can retain them. Existing old payload, required `model_deployment` string and extra rejection pass. The seven API consumer nodes below also depend on T035 reply fields. |
| T036 / T040 | 8 | Owning controller writer emits **0** rows for all three proved single-call states and all three two-round cases. The two zero-row cases pass admission but lose false/unknown evidence in existing event/turn envelopes. T036 supplies evidence-aware builder/admission; T040 connects each actual request, no-RAG opt-out and failure path without aggregate/template usage. |
| T037 | 15 | Fourteen transport nodes: submitted success/empty remain null/unknown; translated failures and local failures lack request evidence; partial/cancel failures lose evidence; a submitted stream without terminal completion remains null instead of true/unknown. The real SDK exposes `CompletionsFinishReason.CONTENT_FILTERED`, so the current string comparison also loses the safety flag. The additional wrapper node drops request identity/evidence. Actual request/usage observations precede these assertions. |
| T038 | 3 | Telemetry labels deployment alias as model; deadline fallback omits false/not_attempted; post-call safety fallback changes observed completion usage **2** to heuristic **3**, rather than retaining actual usage separately. |
| T039 | 2 | Tool failure writes an agent envelope without no-call evidence; real MAF HTTP request produces no eligible model-call row at either existing injected writer seam. Middleware entry alone is never proof. |
| T041 | 4 | Dispatcher omits attempt/outcome/model/error/degraded provenance for success, empty, configuration failure and submitted timeout; an HTTP invocation ID does not supply those fields. Underlying request evidence also depends on T037. |
| T042 | 7 | API parser/reply drops new provenance and old/lost-response uncertainty; omitted deployment fabricates `gpt-4o-mini-australiaeast`. Keep null on nullable replies, preserve remote degraded/error evidence, and do not create an outer HTTP inference row. Depends on T035 additive readers. |

No unresolved normative contract ambiguity was found. All missing behaviour above
remains **unimplemented**; no production schema, reader, audit writer, transport,
instrumentation, source adapter, IaC, configuration or model was changed.

### Executed commands and consolidated leakage check

Standalone final run (with a reporting-only pytest plugin counting modules):

```powershell
$new = @('tests/contract/test_llm_deployment_provenance_schema.py','tests/unit/test_llm_inference_attempt_evidence.py','tests/contract/test_llm_deployment_provenance.py')
.\.venv\Scripts\python.exe -m pytest @new -q -p no:cacheprovider --tb=no --show-capture=no -rN
```

**78 collected; 60 failed, 18 passed; 5.41 s; exit 1** (expected red).
The reporting plugin changes no fixtures, selection or results.

The consolidated run put **all three new modules first**, followed by the exact
preceding checkpoint's final **852-test selector union**, then these directly
relevant existing provenance regressions:

```powershell
$extra = @('packages/domain/tests/test_sub_agent_invocation_record.py','tests/integration/test_audit_replay.py','tests/integration/test_persona_dpe_inspector_audit_replay.py','apps/api/tests/test_lessons_capture_and_export.py','tests/contract/test_llm_telemetry.py','tests/integration/test_otel_retrieval_span.py')
# $baseline is the unchanged selector list in the preceding final 852-test command.
.\.venv\Scripts\python.exe -m pytest @new @baseline @extra -q -p no:cacheprovider --tb=no --show-capture=no -rN -m 'not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging and not azure_blob_worm_staging and not measurement_staging'
```

**959 collected; 60 failed, 899 passed; 56.38 s; exit 1** solely for the same
60 new expected reds. Reporting-plugin groups: **baseline 852/852 passed**,
**extra 29/29 passed**, new **18 passed/60 failed**. Zero collection errors,
setup/teardown errors, skips or xfails. One inherited Starlette/httpx deprecation
warning; no package installation/upgrade. No numeric coverage claim is made.
The existing replay/export regressions passed without fixture/history rebaseline.

All new executable tests use fixture-lifetime DNS/socket denial and fake transports;
schema references resolve locally. Sync/async clients are closed and monkeypatches,
environment and the common recorder are restored. **No unstubbed outbound/model
call occurred.** The same-process old regression population remained entirely
green after the new tests, including their failure/cancellation paths.

### Quality, preservation and stop

```powershell
.\.venv\Scripts\python.exe -m ruff check @new
.\.venv\Scripts\python.exe -m ruff format --check @new
.\.venv\Scripts\python.exe -m mypy --follow-imports=silent @new
.\.venv\Scripts\python.exe -m mypy --config-file= --strict --ignore-missing-imports --explicit-package-bases --follow-imports=silent @new
.\.venv\Scripts\python.exe -m mypy --config-file= --strict --ignore-missing-imports --explicit-package-bases --follow-imports=silent --disable-error-code=no-untyped-call @new
git -c core.whitespace=cr-at-eol diff --check
```

Ruff/format **PASS, 3 files**. Established configured mypy **PASS, 3 files**
(repository `tests.* ignore_errors` override applies). The extra empty-config
strict probe has **six inherited helper-call typing errors only**: two
`configure_tiers` calls and two calls each to `build_controller` /
`controller_events`, whose reused existing definitions are untyped.
The same probe with only `no-untyped-call` disabled **PASS, 3 files**;
this is not an unqualified strict-mypy pass. No helper/import/production edits,
casts or in-file ignores were added to conceal that inherited limitation.

Original-anchor raw SHA-256 comparison: **50/50 unchanged**, including the six
fixture-bearing source files, two KQL assets and 42 replay/sidecar files.
Existing ignore files already cover this test-only scope; none changed.
Pre-marker `tasks.md` SHA-256:
`8d71a237597cb8521273d545dc2d966204944e98ceb7914dcc538e4d61767e43`;
reversing exactly T031/T032/T033 must reproduce it.

Changed paths are only the three new modules above and this append plus the
three selected markers in `tasks.md`. **3/3 authorised authoring tasks complete;
28/52 overall, 24 unchecked.** T024–T027/T030 remain **blocked**, not skipped or
passed. T034–T052 remain unchecked/unstarted in this execution.

Extension YAML was parsed before return: no pre-implementation or mandatory
implementation hook; the optional verify hook is not invoked under the explicit
no-hooks scope. No agents/workflows/handoffs, Azure operations, real inference,
dependency/model/config changes, history rewrites, staging or commits.
Target P1 readiness and real P2/SC-006 acceptance remain blocked on the previously
recorded external evidence and separate authority; synthetic tests supply neither.

**STOP before T034. Return this tests-first checkpoint to the orchestrator; no continuation.**

## Resumed US3 local implementation checkpoint — T034–T044

### Authority, recovery and reader-first ordering

This checkpoint supersedes the preceding **stop before T034** only for the
explicitly authorised local US3 lane, **T034–T044 inclusive**. The branch remains
`model-upgrade-chat-sumlation`; pre-existing dirty US1/US2 work is preserved.
No T024–T027/T030 or T045–T052 work is performed here.
The prerequisite script identified
`C:\code\ama\specs\041-llm-deployment-routing`; the read-only checklist gates
remain **requirements 16/16** and **routing-rollout 36/36**.

Recovery confirmed the T031–T033 checkpoint, including **18 passed / 60 expected
red**, rather than treating interrupted terminal output as partial implementation.
The provenance contract, data model, implementation plan, quickstart, governance
constraints and T003 reader/projection inventory were read before edits.
T034/T035 strict reader/schema/export validation passed **before** T036
admission was enabled. The five-case T036 admission test then passed **before**
the T037–T042 producer changes. These were ordered local edits and validation
steps, not a deployment or a claim about deployed reader versions.

### Implementation and precise projection boundaries

- **T034/T035:** additive nullable attempt/outcome fields in strict audit readers,
  both spec-036 JSON schema mirrors, invocation/reply/detail readers and lessons
  export projection. Historical absence remains unavailable. Required persisted
  identity strings remain required, with `unknown` where unavailable; nullable
  wire identity remains null. Extra fields and invalid status values still fail
  strict validation. No historical payload is rewritten.
- **T036:** `make_observed_inference_record` admits only request evidence with
  `inference_attempted is True`, reuses its frozen identity and request IDs, and
  validates the resulting strict record. Legacy historical/replay construction
  remains compatible. The five-state eligible-owning-writer matrix is exactly
  **1/1/1/0/0** for true/succeeded, true/failed, true/unknown,
  false/not_attempted and null/unknown.
- **T037/T038:** `common/inference_observation.py` observes installed Azure SDK
  transport `send` and installed OpenAI/httpx async transport handoff. Matching
  requires the request ID, account, serialized model and, where present, the
  AOAI URL deployment segment. SDK entry, policy/middleware entry and a prepared
  request are not proof. Context-local binding prevents shared-client leakage.
  A mismatched handoff followed by a decoding/type error remains unknown, not a
  fabricated known no-call. Known pre-call validation/authentication failures
  remain false/not_attempted; opaque observation remains null/unknown.
  Sync/stream exceptions, cancellation, empty/safety output and partial streams
  preserve evidence and actual observed usage. The installed
  `CONTENT_FILTERED` finish enum is handled. A final usage-only stream frame is
  retained even with no text delta. Mixin/template degradation does not replace
  provider usage with a retained-text heuristic or erase a real attempt.
  Proved-only logical inference telemetry separates underlying model metadata
  from deployment alias.
- **T039:** MAF resolves once for routing and evidence, observes its real
  Responses API transport, and separates agent/tool outcomes from model-call
  completion. Streaming pull/transform/cleanup hooks preserve request context
  and cancellation evidence. Queued/in-progress responses do not imply completed
  inference. Strict rows require actual explicit grounding/opt-out eligibility;
  missing RAG audit context does **not** invent a role-based carve-out. Actual
  observed calls remain in the existing agent envelope and telemetry when a
  strict grounding record is ineligible.
- **T040:** the controller records each proved tool-round request independently,
  with distinct call IDs and shared turn correlation, actual round usage/output
  hash and the existing grounded or scenario-execution opt-out context.
  No-RAG requests and proved failures are audited; earlier rows survive a later
  failure or unobserved request. Two proved rounds yield two rows; proved then
  submission-unknown yields one. Aggregate/template output is not assigned to a
  model-call row. Persisted aggregate turn model is null when a round lacks
  submission proof. Tool reply projection preserves remote invocation correlation
  and attempt/completion/degradation evidence without creating duplicate rows.
- **T041/T042:** dispatcher responses carry nullable invoked identity and actual
  attempt/outcome/degraded/error evidence for all six roles. API consumers remove
  `MODEL_DEPLOYMENT_BY_ROLE`, retain old-payload absence as unavailable, classify
  a lost HTTP response as unknown and never treat HTTP invocation correlation as
  inference proof. Nullable replies and required persisted `unknown` strings
  retain their different contracts.

Two additional concrete inventory findings were handled narrowly, not by
relaxing readers:

1. `specs/033-maf-adoption/contracts/audit-entry.schema.json` is also a strict
   reader of the MAF agent envelope. It now explicitly accepts additive nullable
   attempt/outcome and `model_calls`; `additionalProperties: false` and invalid
   enum rejection remain tested.
2. `signal_accepted_workflow._emit_llm_call_timeline_events` previously projected
   model calls from `generation_method` alone. It now requires explicit true
   submission evidence. Existing output DTOs without that evidence retain the
   designed **no new model-call projection** fallback, not a manufactured call.
   No public DTO expansion, endpoint or SSE event-name change was needed.

Older SDK-entry-only routing spies were corrected to expect nullable invoked
identity/unknown status while retaining their real destination/request assertions.
They were not upgraded into fake transport proof. The MAF strict-writer fixture
now supplies explicit synthetic **grounded monitoring** context rather than
manufacturing an opt-out. Real installed SDK fake-transport tests independently
cover proved submission.

### T043/T044 acceptance populations and commands

The **SC-004 local acceptance population** is the asserted reader/provenance
fixtures and actual-transport samples in these five modules, **112 cases**:

| Module | Cases | Final |
|---|---:|---|
| `tests/contract/test_llm_deployment_provenance_schema.py` | 38 | PASS |
| `tests/unit/test_llm_inference_attempt_evidence.py` | 15 | PASS |
| `tests/contract/test_llm_deployment_provenance.py` | 25 | PASS |
| `tests/unit/test_llm_provenance_admission.py` | 5 | PASS |
| `tests/integration/test_llm_deployment_provenance.py` | 29 | PASS |

These include successful/failed/completion-unknown submitted requests,
known no-call and submission-unknown results, safety/empty/partial/cancelled
streams, final usage-only frames, exact request identity binding, per-round
controller admission, all dispatcher roles, old/new reader combinations, remote
timeout/lost responses, strict mirrors and unchanged history.
All asserted samples pass their identity/absence and zero-fabricated-row checks.
**112 is a test-case count, not a count of production records** or a measured
production provenance percentage; no live sample is claimed.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/contract/test_llm_deployment_provenance_schema.py tests/unit/test_llm_inference_attempt_evidence.py tests/contract/test_llm_deployment_provenance.py tests/unit/test_llm_provenance_admission.py tests/integration/test_llm_deployment_provenance.py -q -p no:cacheprovider --tb=short
```

Focused command: **112 passed, 5.97 s** before the final handoff-mismatch
strengthening; the complete final-source consolidated run below again passes
all **112/112**, including that strengthening.

The **SC-007 required regression population** preserves the original
**852-case / 25-selector** baseline and **29-case / 6-selector**
audit/replay/export/telemetry extension, with the new tests first:

```powershell
$text = Get-Content specs/041-llm-deployment-routing/verification.md
$line = $text | Where-Object { $_.Contains('python.exe -m pytest tests/contract/test_llm_deployment_configuration.py tests/unit/test_llm_deployment_preflight.py tests/unit/test_llm_shared_resolver.py') } | Select-Object -First 1
$baseline = [regex]::Matches($line, '(?:tests|apps)/[^ ]+\.py').Value
$new = @('tests/contract/test_llm_deployment_provenance_schema.py','tests/unit/test_llm_inference_attempt_evidence.py','tests/contract/test_llm_deployment_provenance.py','tests/unit/test_llm_provenance_admission.py','tests/integration/test_llm_deployment_provenance.py')
$extra = @('packages/domain/tests/test_sub_agent_invocation_record.py','tests/integration/test_audit_replay.py','tests/integration/test_persona_dpe_inspector_audit_replay.py','apps/api/tests/test_lessons_capture_and_export.py','tests/contract/test_llm_telemetry.py','tests/integration/test_otel_retrieval_span.py')
$local = 'not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging and not azure_blob_worm_staging and not measurement_staging'
.\.venv\Scripts\python.exe -m pytest @new @baseline @extra -q -p no:cacheprovider --tb=short -m $local
```

Executed with the identical extracted selector arrays via inline `pytest.main`:
**993 passed, 52.93 s, exit 0**, one inherited Starlette/httpx deprecation warning.
The final-source expanded run reconfirms the same **993/993** population.
This includes corrected routing/error/provenance outcomes, existing chat,
simulation/SSE/tools/safety/fallback contracts, strict shape, audit replay,
lessons export and telemetry regressions. No whole-repository or numerical code
coverage claim is made.

An additional **122-case** adjacent regression population was also run:

```powershell
$adjacent = @('tests/contract/test_audit_telemetry_fields_no_regression.py','tests/unit/test_audit_writer_uniqueness.py','apps/api/tests/test_sub_agent_invoker.py','apps/api/tests/test_audit_schemas_19_types.py','tests/unit/test_audit_envelope_amendment_036.py','tests/unit/test_sub_agent_invocation_record_aiims_036.py','tests/contract/test_token_budget.py','tests/contract/test_llm_confidence.py','tests/integration/test_replay_digest_sidecar_regression.py','tests/contract/spec039/test_demo_replay_byte_identical.py')
.\.venv\Scripts\python.exe -m pytest @new @baseline @extra @adjacent -q -p no:cacheprovider --tb=short -m $local
```

The final-source consolidated invocation used these exact arrays with a
reporting-only in-memory pytest plugin grouping call outcomes by selector.
**1,115 collected: 1,111 passed, 4 failed; 69.75 s; exit 1**:

| Population | Passed | Failed |
|---|---:|---:|
| Focused provenance | 112 | 0 |
| Original baseline | 852 | 0 |
| Existing replay/export/telemetry extension | 29 | 0 |
| Additional adjacent regressions | 118 | 4 |

The four failures are exclusively the unchanged
`apps/api/tests/test_audit_schemas_19_types.py` expectations:
`test_all_entry_types_have_examples`, the two dispatch examples for
`signal_pipeline.dispatch_failed` / `staging_promotion.refused`, and
`test_24_audit_entry_types_locked`. That test file is **byte-identical to HEAD**;
AST comparison confirms `ALL_ENTRY_TYPES` is **exactly HEAD's 26-element tuple**.
The test still expects 24 and lacks those two exemplars. Neither this unrelated
test nor the enum was changed to hide its stale oracle.

An initial **adjacent-only** run was **117 passed / 5 failed, 15.76 s**.
Its additional snapshot failure was diagnosed: route imports fail on the existing
production startup guard (`AMA_ENABLE_PRODUCTION_AUTH must be enabled`), and
the snapshot helper silently skips those failed imports. No corresponding API
field was removed. In the recorded consolidated acceptance process, with the
established test bootstrap/import context, that snapshot passes. No snapshot
regeneration, production-auth weakening or persistent configuration edit was
used. The isolated collector/bootstrap limitation remains visible rather than
being misreported as an unconditional standalone pass.

### Quality and preservation

The scoped Python quality set is exactly these **23 files**:

```powershell
$quality = @('apps/agents/common/inference_observation.py','apps/agents/common/audit.py','apps/agents/common/foundry_chat_client.py','apps/agents/common/llm_client.py','apps/agents/common/llm_mixin.py','apps/agents/common/otel_telemetry.py','apps/agents/maf_runtime/chat_client.py','apps/agents/maf_runtime/middleware/audit_middleware.py','apps/agents/maf_runtime/middleware/otel_middleware.py','apps/agents/dispatcher/agent.py','apps/api/app/services/simulation/controller_service.py','apps/api/app/services/simulation/sub_agent_invoker.py','apps/api/app/services/simulation/sub_agents/_base.py','apps/api/app/services/simulation/lessons_capture.py','apps/api/app/services/signal_accepted_workflow.py','packages/domain/src/ama_domain/audit_record.py','packages/domain/src/domain/models/sub_agent_invocation_record.py','packages/domain/src/domain/models/telemetry_injection_audit_entry.py','tests/unit/test_llm_provenance_admission.py','tests/integration/test_llm_deployment_provenance.py','tests/contract/test_llm_deployment_provenance.py','tests/unit/test_llm_adapter_snapshots.py','tests/integration/test_llm_deployment_routing.py')
.\.venv\Scripts\python.exe -m ruff check @quality
.\.venv\Scripts\python.exe -m ruff format --check @quality
.\.venv\Scripts\python.exe -m mypy --follow-imports=silent @quality
git -c core.whitespace=cr-at-eol diff --check
```

Ruff, formatting and configured scoped mypy **PASS**. The repository's
`tests.* ignore_errors` override applies to the five test modules; this is not
an unqualified empty-config strict-mypy claim. Production code remains checked
under the configured strict rules. The two late handoff-binding edits also
passed Ruff/format and the final consolidated acceptance population.

Original-anchor raw SHA-256 comparison: **50/50 unchanged before and after**.
The expected/before SHA-256 values remain the original T003 anchors above;
the post values match every one of those same raw-byte digests, not a regenerated
baseline. Both schema and integration tests call the original-anchor helper.
The two spec-036 audit JSON schema mirrors are byte-identical after their
additive changes. Historical replay/sidecar regressions pass without rewriting
records, fixtures, snapshots or replay keys. Ignore files already cover this
local scope and were not changed.

### Status and stop

**11/11 authorised implementation tasks T034–T044 are complete and marked [X];
39/52 feature tasks are complete, 13 unchecked.** T024–T027/T030 remain blocked
by absent G1 approved target baseline, G2 current governance and G3 pinned AVM
compatibility evidence. T045–T052 remain unchecked and outside this execution.
The unrelated stale audit-type tests and isolated snapshot bootstrap limitation
above remain explicit local validation limitations.

After the task/evidence edits, the final 23-file Ruff/format/configured-mypy and
CRLF-aware whitespace checks passed again. Re-running the strict schema/history
and integration modules passed **67/67, 6.40 s**, reconfirming all 50 original
fingerprints. A raw-byte check reversing only T031–T044 markers reproduces the
original pre-T031 `tasks.md` SHA-256
`8d71a237597cb8521273d545dc2d966204944e98ceb7914dcc538e4d61767e43`;
no task wording or out-of-scope marker changed.

There were no agents, handoffs, workflows, hook executions, commits/staging,
Azure reads/writes, real inference, dependency changes, infrastructure edits or
persisted model/configuration changes. All inference acceptance uses installed
SDKs against hermetic fake transport seams; it supplies no target readiness.
The extension YAML was parsed again: no pre-implementation or mandatory
implementation hooks; optional `speckit.verify.run` was surfaced but not invoked
under the explicit no-hooks scope.
G0/G1/G2/G3/G4/G5a/G5b/G6 remain independent external release/migration gates.
Local US3 acceptance does **not** approve deployment, real P1 readiness,
P2/SC-006 switch/rollback acceptance or retirement.

**STOP after T044. Return this local implementation/evidence checkpoint to the
orchestrator; do not continue or auto-forward.**

## T045–T048 checkpoint — offline P2 procedure only (2026-10-19)

This checkpoint follows the explicit approval **“Approve — continue local
migration procedure T045–T048”**. It supersedes only the preceding stop for
these four tasks, not its evidence or external gates. Actual branch
`model-upgrade-chat-sumlation` and existing dirty work were retained.

Prerequisites again returned absolute feature directory
`C:\code\ama\specs\041-llm-deployment-routing` and available research/data-model/
contracts/quickstart/tasks documents. Checklist gates were read-only:
requirements **16/16**, routing-rollout **36/36**, zero unchecked.
Existing Python/Docker ignore rules cover required build/cache/env patterns;
the root package is private, so no publishing ignore file was introduced.
No dependencies were installed or changed.

### Exact task/file changes

| Task | File | Delivered change |
| --- | --- | --- |
| T045 | `tests/unit/test_llm_deployment_migration_preflight.py` (new) | Tests-first synthetic migration suite, expanded to 144 cases; stage approvals, old/new parity, actual-pool shaped quota, old corrected rollback pair, freshness/invalidation/bindings, G0 readiness scope, G6 and no-socket/no-input-write checks |
| T046 | `specs/041-llm-deployment-routing/naming-migration.md` (new) | Controlled states, eight-step FR-016/contract crosswalk, separate G5a/G0/G5b/G6 boundaries, failure/rollback/retention and offline evidence contract |
| T047 | `scripts/verify-llm-deployment-preflight.py` (existing local file extended) | Optional paired `--migration`/`--stage` comparison after unchanged P1 checks; no action execution; existing four-file output/exit semantics preserved |
| T047–T048 | `specs/041-llm-deployment-routing/migration-rehearsal.md` (new) | Executable temporary-input tabletop, expected forward/failed-forward/rollback/no-approval outcomes, remaining operational gates |
| T048 | `specs/041-llm-deployment-routing/verification.md` | This appended local evidence/limits; no prior evidence rewritten |
| Progress | `specs/041-llm-deployment-routing/tasks.md` | Only T045–T048 changed from `[ ]` to `[X]` in this checkpoint |

The migration evidence is bound to both exact old corrected/new API and agents
image/config/revision pairs, compiled-proposal revisions, proposal digest and
window/decision digest. It must use the supplied approved policy/version,
explicit per-kind windows/invalidation and exact target. Missing/unreadable/
expired/invalidated evidence fails the affected stage without default values.

G5a compares proposal parity, governance/What-If records, pool quota and
retained corrected rollback compatibility **without requiring uncreated
replacement readiness**. Later stages require actual post-provision shaped
readiness, scoped G0 metadata authority and independent stage approval.
Readiness observation follows G5a approval; traffic approval follows readiness
approval. G5a is not substituted for G5b. G6 is independent of traffic approval.
The checker cannot authenticate supplied approvals or prove real observations:
all success reports still say target readiness is **not established** and
operational authority is **not granted**.

Quota comparisons group old/new allocations by actual subscription, region,
model and SKU, aggregate shared-model tiers in one pool, include other
allocations plus explicit margin and reject insufficient headroom. They do not
assume a new deployment creates quota. Per-tier model/version/format/SKU/
capacity/RAI/filter/upgrade settings, embedding and access/residency controls
remain unchanged. The old corrected pair and old resources remain retained;
ambiguous pre-P1 configuration is not a permitted rollback substitution.

### Tests-first and final local validation

Initial T045 command, before extending the CLI:

```powershell
uv run --no-sync pytest tests/unit/test_llm_deployment_migration_preflight.py -q --tb=line
```

Result: **102 failed, 1 passed, 26.97 s**. Failures were the intended unsupported
`--migration`/`--stage` interface (exit 2), not Azure/dependency failures.
Subsequent development checks caught formatting/type issues and a transient
test comprehension syntax error; these were fixed locally before final checks.

Final focused regression:

```powershell
uv run --no-sync pytest tests/unit/test_llm_deployment_migration_preflight.py tests/unit/test_llm_deployment_preflight.py tests/contract/test_llm_deployment_configuration.py -q --tb=line
```

Result: **315 passed, 69.86 s**, exit **0**. This includes **144 migration
cases** and **171 existing preflight/configuration cases**. The migration
count was independently confirmed with `--collect-only -q`: 144 collected.
Seven stage cases execute comparisons with socket creation replaced by a
failing guard and observe zero calls. Subprocess cases compare input bytes and
temporary-directory contents before/after: no checker writes.

Scoped quality commands:

```powershell
uv run --no-sync ruff check scripts/verify-llm-deployment-preflight.py tests/unit/test_llm_deployment_migration_preflight.py
uv run --no-sync ruff format --check scripts/verify-llm-deployment-preflight.py tests/unit/test_llm_deployment_migration_preflight.py
uv run --no-sync mypy scripts/verify-llm-deployment-preflight.py tests/unit/test_llm_deployment_migration_preflight.py --follow-imports=silent
```

Final results: Ruff **passed**; format **2 files already formatted**; configured
mypy **no issues in 2 source files**, all exit **0**. Repository mypy settings
ignore test-body errors; the checker itself is checked under configured strict
settings. CRLF-aware trailing-whitespace validation passed for all scoped code/
document files. No standalone Markdown lint executable was available in the
existing root `node_modules/.bin`; none was installed. No overall coverage
percentage or new full-suite pass is claimed. The previously recorded four
stale audit-type assertions and isolated snapshot bootstrap limitation remain
unrelated and were not changed.

### T048 tabletop and FR-016 cross-check

Executed the **exact Python block** in `migration-rehearsal.md`, extracted
read-only and compiled/executed via `uv run --no-sync python -`.
All **15/15 named outcomes** matched:

| Actual local case | Exit/result |
| --- | --- |
| Supplied provision/canary/switch/forward/rollback/retain/retire | 0 each; local comparison only |
| Uncreated replacement readiness omitted at G5a | 0 at provision |
| Same absent readiness at G5b | 1, `migration.records.readiness` missing |
| Failed forward/streaming evidence | 1, `migration.verification.outcome` mismatch |
| Same failed-forward evidence with independent approved rollback | 0, rollback comparison only |
| Missing provision/switch/rollback/retire approval | 1 each, exact `migration.approvals.<stage>` diagnostic |

The runbook's eight FR-016 rows were cross-checked against the complete P2
contract: independent proposal/target identity; actual-pool coexistence;
proposed protection/governance/What-If and G5a; provisioning followed by
G0-authorised actual readiness; paired candidates/retained corrected rollback;
individual G5b traffic stages plus post-switch/failed-forward rollback
verification; explicit observation/retention and rollback rehearsal; independent
G6 with no remaining active revision/worker/eval/rollback dependencies.
States include `proposed -> approved -> replacements_ready -> switched ->
verified -> retained`, failure `rolled_back`, and `retained ->
retirement_approved -> retired`. No state transition is executed by a test.

**SC-006: local procedure coverage demonstrated; real operational acceptance
pending / not executed.** Synthetic flags and reference strings do not supply
real provisioning, quota clearance, readiness, traffic switching, verification,
rollback or retirement evidence.

### Preservation and remaining gates

The existing read-only 50-hash helper reproduced **50/50 original fingerprints
unchanged**, including all original replay NDJSON and sidecar bytes. Reversing
only the T031–T048 completion markers in raw `tasks.md` reproduced the original
pre-T031 task-file SHA-256:
`8d71a237597cb8521273d545dc2d966204944e98ceb7914dcc538e4d61767e43`.
Thus this checkpoint changes only T045–T048 markers, not task wording or earlier
completion state. The final post-evidence check repeats both checks.

Extension YAML parsed successfully: no pre-implementation hooks and no
mandatory implementation hooks. The optional `speckit.verify.run` hook was
surfaced, not invoked; no hooks/workflows/agents/handoffs were executed.
No staging/commits, Azure operations, real inference, target configuration/model
changes or infrastructure authoring/build/collection occurred.

T024–T027/T030 remain blocked on approved G1 target baseline, G2 current
inherited governance and G3 pinned AVM compatibility. G0 collection authority
and G4 release-stage decisions remain independent. G5a actual proposal approval
and provisioning, G0 actual replacement readiness, individual G5b canary/switch/
forward/rollback authority and execution, real observation/retention and G6
retirement remain external gates. T049–T052 are future checkpoint work.

**STOP after T048. Return this local checkpoint to the orchestrator; no
follow-up handoff or automatic continuation.**

<a id="final-local-cross-cutting-checkpoint--t049t052"></a>

## Final local cross-cutting checkpoint — T049–T052

### Authority, scope and exact local result

Date: **2026-10-19**. Authority: **“Approve — finish local cross-cutting tasks
T049–T052”**. This supersedes the preceding local stop only for those four
tasks. Branch `model-upgrade-chat-sumlation` retained. No delegation,
handoffs, hooks/workflows, staging/commits, Azure operations, real inference,
infrastructure authoring/build, target model/configuration edits or external
gate approvals occurred.

Only these five feature documents change at this checkpoint:
`quickstart.md`, `requirements-review.md`, `verification.md`,
`rollout-evidence.md`, and the T049–T052 markers in `tasks.md`.
Pre-existing dirty source/schema/test work is preserved, not reverted,
reformatted or extended. No dependencies or tools were installed.

**Final local union: 1,259 collected; 1,255 passed, 4 failed; one inherited
Starlette/httpx deprecation warning; 98.17 seconds; exit 1.**
No collection/setup errors, skips or xfails were reported.
This is not an entirely green suite, a full-repository result, numerical
code coverage, target P1 readiness or real P2/SC-006 acceptance.

### Exact final relevant selector union

Executed once, with the existing 25-selector baseline extracted from its
original T028 record rather than silently replacing regression selectors:

```powershell
@'
from pathlib import Path
import re
import pytest
text = Path('specs/041-llm-deployment-routing/verification.md').read_text(encoding='utf-8')
line = next(line for line in text.splitlines() if 'python.exe -m pytest tests/contract/test_llm_deployment_configuration.py tests/unit/test_llm_deployment_preflight.py tests/unit/test_llm_shared_resolver.py' in line)
baseline = re.findall(r'(?:tests|apps)/[^ ]+\.py', line)
new = ['tests/contract/test_llm_deployment_provenance_schema.py','tests/unit/test_llm_inference_attempt_evidence.py','tests/contract/test_llm_deployment_provenance.py','tests/unit/test_llm_provenance_admission.py','tests/integration/test_llm_deployment_provenance.py']
extra = ['packages/domain/tests/test_sub_agent_invocation_record.py','tests/integration/test_audit_replay.py','tests/integration/test_persona_dpe_inspector_audit_replay.py','apps/api/tests/test_lessons_capture_and_export.py','tests/contract/test_llm_telemetry.py','tests/integration/test_otel_retrieval_span.py']
adjacent = ['tests/contract/test_audit_telemetry_fields_no_regression.py','tests/unit/test_audit_writer_uniqueness.py','apps/api/tests/test_sub_agent_invoker.py','apps/api/tests/test_audit_schemas_19_types.py','tests/unit/test_audit_envelope_amendment_036.py','tests/unit/test_sub_agent_invocation_record_aiims_036.py','tests/contract/test_token_budget.py','tests/contract/test_llm_confidence.py','tests/integration/test_replay_digest_sidecar_regression.py','tests/contract/spec039/test_demo_replay_byte_identical.py']
migration = ['tests/unit/test_llm_deployment_migration_preflight.py']
selectors = list(dict.fromkeys(new + baseline + extra + adjacent + migration))
assert len(baseline) == 25 and len(selectors) == 47
print('FINAL SELECTORS', len(selectors), flush=True)
local = 'not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging and not azure_blob_worm_staging and not measurement_staging'
raise SystemExit(pytest.main(selectors + ['-q','-p','no:cacheprovider','--tb=short','-m',local,'--basetemp=C:\\code\\ama\\.feature041-checks']))
'@ | .\.venv\Scripts\python.exe -
```

The inherited selector spelling is retained inside Python strings; pytest
scratch inputs were explicitly confined to `C:\code\ama\.feature041-checks`,
not an OS temporary directory. That owned directory is removed after checks.
Feature tests use fixture-only fake SDK/HTTP transports and network guards;
the migration CLI subprocesses compare only synthetic local files. The
checker never performs the operation named by its stage.

| Union component | Selectors | Cases / final outcome |
| --- | ---: | --- |
| T031–T044 focused provenance | 5 | 112 passed |
| Original T028 baseline, including routing/configuration/preflight, chat/SSE/simulation, safety/gateway/fallback/MI/circuit, embedding/eval and history contracts | 25 | 852 passed |
| Existing audit/replay/export/telemetry extension | 6 | 29 passed |
| T045–T048 migration | 1 | 144 passed |
| Adjacent audit/invocation/token/confidence/replay checks | 10 | 118 passed, 4 failed |
| **Total** | **47** | **1,255 passed, 4 failed** |

The required local population is **1,137/1,137 passing**; four failures belong
only to the additional adjacent population. Counts above are the unchanged
recorded populations plus migration, with all four final failures identified
below. The final union does not shrink/skip the failing population.

Exact unchanged failures, all in `apps\api\tests\test_audit_schemas_19_types.py`:

- `test_all_entry_types_have_examples`: missing `signal_pipeline.dispatch_failed`
  and `staging_promotion.refused`.
- `test_entry_type_validates_against_dispatch[signal_pipeline.dispatch_failed]`:
  missing example key.
- `test_entry_type_validates_against_dispatch[staging_promotion.refused]`:
  missing example key.
- `test_24_audit_entry_types_locked`: HEAD's 26 types versus 24 expected.

That test remains HEAD-equivalent; the read-only current comparison normalised
line endings, and the preceding US3 AST comparison established the unchanged
26-element tuple. No enum, exemplar, unrelated test, snapshot or auth guard
was changed. The isolated snapshot helper's production-auth route-import
limitation remains; its snapshot passes in this final consolidated bootstrap.
No standalone unconditional snapshot-pass claim is made.

### Exact scoped lint and configured type checks

Executed against every touched/untracked Python file in the preserved feature
worktree, **40 unique files**, using existing installed tools:

```powershell
$tracked = @(git --no-pager diff --name-only -- '*.py')
$new = @(git ls-files --others --exclude-standard -- '*.py')
$quality = @($tracked + $new | Sort-Object -Unique)
.\.venv\Scripts\python.exe -m ruff check @quality
.\.venv\Scripts\python.exe -m ruff format --check @quality
$types = @($quality | Where-Object { $_ -ne 'tests/contract/test_llm_model_routing.py' -and $_ -ne 'tests/fixtures/llm_deployment_routing.py' })
.\.venv\Scripts\python.exe -m mypy --follow-imports=silent @types
.\.venv\Scripts\python.exe -m mypy --follow-imports=silent tests\fixtures\llm_deployment_routing.py
git -c core.whitespace=cr-at-eol diff --check
```

Results: Ruff **all checks passed**; format **40 files already formatted**;
configured mypy **no issues in 38 files**, and the fixture **one file** checked
separately passes; all quality commands exit **0**.
The fixture is separate to avoid duplicate module identity when supplied
alongside its importing modules. The known legacy mixed-import
`test_llm_model_routing.py` remains in pytest/Ruff but is not a mypy target.
Repository test overrides apply (`tests.* ignore_errors`); no new ignores,
casts or unqualified strict-mypy claim. No source formatter write was run.

No Markdown lint executable exists in the root `node_modules\.bin`, and root
`package.json` defines no Markdown lint script. No package install/download
was attempted. Feature-document local links and CRLF-aware whitespace are
checked directly; this is not a claim that a missing Markdown linter ran.

### Original bytes and preservation

The initial direct import of the schema test helper outside pytest failed
with `ModuleNotFoundError: ama_domain` because its package bootstrap was
absent. No dependency was installed or test changed. The established
read-only original-anchor parser was then used successfully:

```powershell
@'
import hashlib
import re
from pathlib import Path
text = Path('specs/041-llm-deployment-routing/verification.md').read_text(encoding='utf-8').split('## Checkpoint integrity and remaining gates')[0]
anchors = dict(re.findall(r'\| `((?:tests/|packages/|apps/)[^`]+)` \| `([a-f0-9]{64})` \|', text))
for name, data_hash, sidecar_hash in re.findall(r'\| `([^`]+\.ndjson)` \| `([a-f0-9]{64})` \| `([a-f0-9]{64})` \|', text):
    anchors[f'fixtures/sim_replays/{name}'] = data_hash
    anchors[f'fixtures/sim_replays/{name}.sha256'] = sidecar_hash
assert len(anchors) == 50, len(anchors)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == expected for p, expected in anchors.items())
print('HISTORICAL_FINGERPRINTS: 50/50 unchanged')
'@ | .\.venv\Scripts\python.exe -
```

Result: **50/50 original raw-byte SHA-256 anchors unchanged**, also exercised
in the passing schema/integration population. No anchor was regenerated.
Both reviewer checklists retain their entry hashes, **16/16 and 36/36**
markers and original lifecycle; exact hashes are in requirements-review.md.

Entry preservation digest for all **44 dirty paths outside feature 041**,
sorted by path, hashing each UTF-8 path + NUL + raw file bytes + NUL:
`b90f233989a7897843d3ff0f6c8bf91290c0dea072373b665832d75a3824255a`.
The final preservation check reproduced this same value, not a new
baseline. This includes all pre-existing dirty source/test/schema work.
Reversing only T031–T052 completion markers reproduced the original
pre-T031 tasks SHA-256
`8d71a237597cb8521273d545dc2d966204944e98ceb7914dcc538e4d61767e43`.

### FR-001–FR-016 evidence consolidation

| Requirement | Actual local evidence | Remaining external acceptance / limitation |
| --- | --- | --- |
| FR-001 | Frozen tier/model/deployment types, separate provenance fields; T006–T008/T037–T042 and passing routing/provenance cases | Real target model association not verified |
| FR-002 | Three distinct destinations sharing one synthetic model/version; six orderings and immutable resolution pass | Actual independent per-tier IaC selections blocked |
| FR-003 | T023/T028 synthetic nine-selection top-level/child/output comparisons pass | **BLOCKED / not executed:** T024–T027/T030 actual Bicep pass-through/compiled evidence, G1–G3 |
| FR-004 | Synthetic baseline drift/protection/embedding/access/binding/freshness rejection passes | **BLOCKED / not executed:** approved per-target parity and mandatory reviewed What-If; zero real diff is not asserted |
| FR-005 | Explicit old names supported locally; purpose-name fixture contract/procedure covered | **BLOCKED / not executed:** actual new-only IaC defaulting and approved target parameter sets |
| FR-006 | Common clients and adapters use immutable explicit-tier resolution; 168 caller/order cells retained | Deployed paired image/config compatibility remains unverified |
| FR-007 | Controller and six dispatcher roles require explicit isolated simulation; invalid configuration yields zero requests | No authorised real simulation inference/canary |
| FR-008 | MAF/common/controller/dispatcher actual fake-request boundaries pass shared-model resolution | Real transport/deployed version review remains external |
| FR-009 | Strict pre-dictionary CSV validation rejects all conflict orders, admits equal duplicates; safe diagnostics | Clean real candidate CSV not supplied |
| FR-010 | Explicit precedence, destination-bound metadata and unambiguous legacy/eval/embedding conformance pass | Real cleaned compatibility map and deliberate eval maps require review |
| FR-011 | Missing/blank/unsupported/partial/ambiguous required settings fail before affected requests; graceful degradation preserved | No target readiness inferred from local exceptions |
| FR-012 | Synthetic outputs/candidate/baseline metadata equality and account/endpoint binding fail closed | **BLOCKED / not executed:** actual infrastructure outputs and G0-authorised Azure deployment metadata verification |
| FR-013 | 112-case provenance population separates model/version/deployment and actual usage, distinct per-round requests | Local samples only; no production-record percentage |
| FR-014 | Proved transport handoff versus no-call/unknown evidence; owning-writer matrix 1/1/1/0/0, failed/lost/partial/cancel/safety cases pass | Actual provider execution is not inferred merely from submission; deployed-reader review pending |
| FR-015 | Obsolete label fallback removed; replay/export readers preserve unavailable identity; 50 original hashes unchanged | No historical production dataset invented or rewritten |
| FR-016 | T045–T048 controlled runbook, 144 migration cases, 15/15 synthetic tabletop outcomes, T052 stage-specific handover | **Not executed:** G5a provisioning, G0 actual readiness, G5b traffic/forward/rollback, observation and G6 retirement |

### SC-001–SC-007 evidence consolidation

| Criterion | Exact acceptance population / result | Level and remaining gate |
| --- | --- | --- |
| SC-001 | C01–C23/A01–A05 × six orders = **168/168** actual caller/request cells pass within the original routing population | Local hermetic acceptance only; no invented additional production caller |
| SC-002 | Controller and every one of six role routes, including tool rounds; explicit simulation only, missing/blank/collision configuration yields zero requests | Local cases pass; no real canary/activation authority |
| SC-003 | Resolver, conformance, adapter and preflight invalid-required-config cases pass with safe actionable errors and zero affected requests | Local acceptance; compiled/target input readiness still blocked |
| SC-004 | **112/112** focused provenance/schema/admission/integration cases pass; all asserted records preserve identity/absence and no fabricated inference rows | Test-case population, not a production sample or provider-execution claim |
| SC-005 | Synthetic unchanged-baseline comparisons and negative drift cases pass; zero resources were operated on | **BLOCKED / not executed** for every real target; approved G1–G3, compiled comparisons and reviewed metadata/What-If/carve-out absent |
| SC-006 | **144** migration cases and earlier **15/15** synthetic tabletop outcomes verify procedure branches | **Real operational acceptance pending / not executed**; separate G5a/G5b actual readiness/switch/forward/rollback plus G6 retention boundary |
| SC-007 | Required **1,137/1,137** local routing/provenance/preflight/migration/original regression cases pass; **50/50** original raw-byte history anchors unchanged | Adjacent run still has **4 unchanged stale failures**; isolated collector limitation retained. No unqualified full-suite/release acceptance |

### T049–T052 outputs and final boundary

- **T049:** quickstart now documents real existing commands, final results,
  synthetic-only boundaries, missing target gates and explicit prohibitions
  on old-map strict-reader activation or incompatible env-only rollout.
  The project-local synthetic CLI example was executed: **exit 0**, exact
  `target_readiness: "not established"` JSON; its directory was removed.
  `--help` confirmed the four required inputs and optional paired
  `--migration`/`--stage`; a stage name grants no operational authority.
- **T050:** CHK001–CHK036 were re-evaluated with task/evidence links and
  local-versus-blocked dispositions. Independent owner re-evaluation of
  post-implementation evidence is requested, not issued; F4 and target
  gates remain open. No checklist marker/lifecycle changed.
- **T051:** the exact final regression union and scoped lint/type/preservation
  evidence above are complete, with all failures and FR/SC limits disclosed.
- **T052:** rollout-evidence.md supplies the human review handover, exact
  required API/agents candidate/rollback/config reference locations marked
  **NOT SUPPLIED**, compatibility/safe rollback rules and G0–G6 stage stops.
  Missing real references block release, not delivery of the local handover.
  Independent metadata/What-If/carve-out reviews and human release approval
  remain required; none are granted.

**4/4 authorised cross-cutting tasks complete; 47/52 tasks recorded complete.
Exactly T024–T027/T030 remain unchecked and externally blocked by G1 approved
target baseline, G2 current inherited governance and G3 pinned AVM compatibility.**
G0 collection/validation, G4 release-stage approval, G5a provisioning,
G5b actual-ready traffic/forward/rollback and G6 retirement remain independent
and unexecuted. No models, target configurations, resources or history were
changed at this checkpoint. No claim that the feature is complete or ready
to deploy.

Final post-edit integrity validation: **44/44 pre-existing dirty paths
byte-identical**, both reviewer checklists byte-identical, **50/50 original
fingerprints unchanged**, all **30 local document references/fragments valid**,
all **36 T050 CHK rows present**, original task wording/other markers verified
by the reversal hash, and only the five expected external tasks unchecked.
`git -c core.whitespace=cr-at-eol diff --check` exits **0**. This Git check
covers tracked differences; the feature directory is untracked and its five
edited documents also receive a direct CRLF-aware trailing-whitespace check
(existing two-space Markdown hard breaks allowed). The owned
`.feature041-checks` and `.feature041-example` directories are removed.
The branch and all pre-existing dirty work remain intact.

**STOP after T052. Return exact local results/blockers to the orchestrator;
no follow-up handoff, automatic execution, deployment or commit.**

<a id="e1e2-provenance-remediation-2026-10-19"></a>

## E1/E2 provenance remediation — 2026-10-19

Authority: **“Approve — fix both provenance findings and re-verify”**.
This corrective checkpoint changes implementation and its focused regressions;
it supersedes neither the historical checkpoint record above nor any external
gate. Branch remains `model-upgrade-chat-sumlation`. No delegation, hooks,
workflows, commit/staging, dependency installation, Azure operation, live model
inference, infrastructure authoring/build or target model/configuration change.

### Tests first and exact corrective scope

Before production edits:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\contract\test_llm_deployment_provenance.py tests\integration\test_llm_deployment_provenance.py -k 'mixin_generation_method or workflow_request_evidence' -q --tb=short
```

**7 failed, 2 passed, 52 deselected; exit 1.** E1 safety/budget-processing
exceptions lost actual usage; E2 three proved-submission cases emitted zero
events, and false/unknown cases exposed unproved generated model/alias values.
After the first bridge, the additional common-adapter workflow regression was
run before adding its collector forwarding:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\integration\test_llm_deployment_provenance.py -k 'workflow_request_evidence and common-success' -q --tb=short
```

**1 failed, 34 deselected; exit 1**, zero events instead of two. The test's
expected reasoning alias was corrected to the existing fixture's
`synthetic-live-r`, not a changed production setting or weakened assertion.

Implementation files modified in this checkpoint:

- `apps\agents\common\llm_mixin.py`: capture the response's evidence before
  downstream processing; reuse it on local failure, preserving model outcome,
  original call ID, identity and actual usage. The local error still returns
  a review-required template fallback. Exceptions before a response retain
  attached request evidence, otherwise unknown; no response means no invented
  success. Forward captured evidence to an active workflow collector.
- `apps\agents\common\inference_observation.py`: request-local collector scope;
  no inference write or ownership change.
- `apps\agents\maf_runtime\middleware\audit_middleware.py`: propagate the
  collected request evidence to an enclosing scope after restoring ContextVars;
  existing strict model/agent audit ownership and admission remain unchanged.
- `apps\agents\maf_runtime\workflow\builder.py`: collect risk/communication
  request evidence separately from generated JSON and checkpoint payloads.
- `apps\api\app\services\signal_accepted_workflow.py`: builders retain typed
  evidence in private internal Recommendation/PublicAlert subclasses, without
  changing domain models or public schemas. Timeline emits one event per
  distinct proved call ID, including failed/unknown completion. It records
  request-derived alias, model/version and observed usage; generated flags or
  labels cannot assert inference. False/unknown submission emits zero.

Two existing test files changed:
`tests\contract\test_llm_deployment_provenance.py` and
`tests\integration\test_llm_deployment_provenance.py`. Added eight cases:
two post-completion processing exceptions and six workflow cases. The latter
execute installed SDKs with fake transports, nested MAF audit scopes, actual
`AmaWorkflow`, API builders and the timeline writer. They cover MAF success,
submitted failure, lost completion, local no-call, opaque submission, and
common-mixin success: event counts **2/2/2/0/0/2**. Positive flags and misleading
identity in generated output are deliberately ignored; no second strict audit
owner or fabricated RAG opt-out is introduced. Private evidence is absent from
public model dumps. No original test assertion or strict reader was relaxed.

Final focused command:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\contract\test_llm_deployment_provenance.py tests\integration\test_llm_deployment_provenance.py -q --tb=short
```

**62 passed in 5.35 seconds; exit 0.** Includes ordinary safety fallback,
deadline/no-call, transport/translation failures, request binding, writer
admission, MAF/common/dispatcher/API provenance and historical fingerprints.

### Expanded relevant regression command and result

The previous 47-selector union was retained, not narrowed to hide failures.
Nine relevant existing workflow/translation selector files added 50 cases.
Together with the eight new cases, the union collected **1,317 cases**:
**1,313 passed, 4 failed, 1 inherited deprecation warning**, **102.00 seconds**,
exit **1**; no skips, xfails or collection/setup errors.

```powershell
@'
from pathlib import Path
import re
import pytest
text = Path(r'specs\041-llm-deployment-routing\verification.md').read_text(encoding='utf-8')
line = next(line for line in text.splitlines() if 'python.exe -m pytest tests/contract/test_llm_deployment_configuration.py tests/unit/test_llm_deployment_preflight.py tests/unit/test_llm_shared_resolver.py' in line)
baseline = re.findall(r'(?:tests|apps)/[^ ]+\.py', line)
new = ['tests/contract/test_llm_deployment_provenance_schema.py','tests/unit/test_llm_inference_attempt_evidence.py','tests/contract/test_llm_deployment_provenance.py','tests/unit/test_llm_provenance_admission.py','tests/integration/test_llm_deployment_provenance.py']
extra = ['packages/domain/tests/test_sub_agent_invocation_record.py','tests/integration/test_audit_replay.py','tests/integration/test_persona_dpe_inspector_audit_replay.py','apps/api/tests/test_lessons_capture_and_export.py','tests/contract/test_llm_telemetry.py','tests/integration/test_otel_retrieval_span.py']
adjacent = ['tests/contract/test_audit_telemetry_fields_no_regression.py','tests/unit/test_audit_writer_uniqueness.py','apps/api/tests/test_sub_agent_invoker.py','apps/api/tests/test_audit_schemas_19_types.py','tests/unit/test_audit_envelope_amendment_036.py','tests/unit/test_sub_agent_invocation_record_aiims_036.py','tests/contract/test_token_budget.py','tests/contract/test_llm_confidence.py','tests/integration/test_replay_digest_sidecar_regression.py','tests/contract/spec039/test_demo_replay_byte_identical.py']
migration = ['tests/unit/test_llm_deployment_migration_preflight.py']
workflow = ['tests/integration/test_aud007_signal_accepted_workflow.py','tests/integration/test_workflow_crash_recovery.py','tests/unit/test_executor_base.py','tests/integration/no_op_agent/test_no_op_inherits_middleware.py','tests/contract/test_risk_assessment_llm.py','tests/contract/test_communication_llm.py','tests/unit/test_communication_translator.py','tests/contract/test_workflow_run_api.py','tests/unit/test_workflow_run_uniqueness.py']
selectors = list(dict.fromkeys(new + baseline + extra + adjacent + migration + workflow))
assert len(baseline) == 25 and len(selectors) == 56, (len(baseline), len(selectors))
print('REMEDIATION SELECTORS', len(selectors), flush=True)
local = 'not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging and not azure_blob_worm_staging and not measurement_staging'
raise SystemExit(pytest.main([p.replace('/', chr(92)) for p in selectors] + ['-q','-p','no:cacheprovider','--tb=short','-m',local,r'--basetemp=C:\code\ama\.feature041-remediation-checks']))
'@ | .\.venv\Scripts\python.exe -
```

The same four failures remain solely in
`apps\api\tests\test_audit_schemas_19_types.py`:
`test_all_entry_types_have_examples`, the two
`test_entry_type_validates_against_dispatch` cases for
`signal_pipeline.dispatch_failed` and `staging_promotion.refused`, and
`test_24_audit_entry_types_locked` (26 actual versus 24 expected). No audit
type/fixture/test change was made. The inherited warning is Starlette's httpx
TestClient deprecation. This is not an unqualified full-suite green result.

### Quality, bytes, handover and independent stop

After implementation, all dirty/untracked Python files were checked:

```powershell
$tracked = @(git --no-pager diff --name-only -- '*.py')
$new = @(git ls-files --others --exclude-standard -- '*.py')
$quality = @($tracked + $new | Sort-Object -Unique)
.\.venv\Scripts\python.exe -m ruff check @quality
.\.venv\Scripts\python.exe -m ruff format --check @quality
$types = @($quality | Where-Object { $_ -ne 'tests/contract/test_llm_model_routing.py' -and $_ -ne 'tests/fixtures/llm_deployment_routing.py' })
.\.venv\Scripts\python.exe -m mypy --follow-imports=silent @types
.\.venv\Scripts\python.exe -m mypy --follow-imports=silent tests\fixtures\llm_deployment_routing.py
git -c core.whitespace=cr-at-eol diff --check
```

Ruff **all checks passed**, format **41 files already formatted**, configured
mypy **39 files plus the separate fixture pass**, all exit **0**. The extra
file versus the previous scope is the workflow builder. The same repository
test overrides and mixed-import exclusion apply; no new ignore, cast, tool
installation or source formatter write. Before the expanded checks, the seven
directly changed Python files also passed Ruff/format/configured mypy.

The original-anchor parser in the preceding checkpoint was rerun without
regenerating anchors: **50/50 raw-byte SHA-256 matches**, also checked by
passing provenance tests. `tasks.md` is unchanged:
`34d0ce71f7de60cab29a21bff164d97095c45d26c6e41e6c4f7516cca4387060`.
Both reviewer checklist hashes still match the prior T050 record:
requirements `70ba36dd52686feb8d6f3f6e888451f1e64ed332f5a9c0a63868daf2af61ea06`;
routing-rollout `ffe16873f2a7ba33a1c7a269ba62c3c64a54d96b5c9f7d8c3f33c5603ad6a4b4`.
No historical content, task marker or reviewer item was edited.
The owned project-local `.feature041-remediation-checks` directory was removed.

This checkpoint also appends the E1/E2 disposition to `remediation.md` and
updates the declared T052 handover in `rollout-evidence.md`. Earlier
byte-identical-dirty-work claims describe their historical checkpoint; these
seven explicitly approved Python files are now intentionally extended, not
represented as unchanged. Other existing dirty work is left intact.

Local tasks remain **47/52 complete**; only **T024–T027/T030** are externally
blocked on approved target baseline, current inherited governance and pinned
AVM compatibility. G0 collection/validation, G4 release, G5a provisioning,
G5b actual-readiness/traffic/forward/rollback and G6 retirement decisions and
execution remain pending. No target P1 or real P2/SC-005/SC-006 acceptance.

**STOP: return the exact local results and blockers to the orchestrator for
independent read-only E1/E2 re-verification. No auto-forward, hook/workflow,
deployment, commit or further operation.**

Final persisted-artifact integrity check: **47/52 task markers** with exactly
T024–T027/T030 pending; task and both reviewer checklist hashes match the values
above; **50/50** original anchors still match; **5/5** local links/fragments in
the three edited evidence documents resolve; their direct whitespace checks
and CRLF-aware Git diff check pass. The stale audit test is HEAD-equivalent
after line-ending normalisation. Owned scratch remains absent.

Raw-byte SHA-256 of the exact seven corrected Python artifacts supplied for
independent read-only re-verification (not replacement historical anchors):

| File | SHA-256 |
| --- | --- |
| `apps\agents\common\llm_mixin.py` | `dc619e20dce0bc5d40ef417eae239bbc6f4a8b6d34af46df1b4f0367fe77fcfa` |
| `apps\agents\common\inference_observation.py` | `8fe6b6e9472a36573e0c70e1a3cc937d6f21bc8401a52a235cfb824ba34275f1` |
| `apps\agents\maf_runtime\middleware\audit_middleware.py` | `5011cee20c2ebc67a560549e1a84107be7b67cf10952887e8bd2a3e465183f6c` |
| `apps\agents\maf_runtime\workflow\builder.py` | `8b1f89d3cdcf34f7da1bae868afcc3b192fefc9c7133ea12e2a7d8239bbd3291` |
| `apps\api\app\services\signal_accepted_workflow.py` | `80923b009e3d96062a6c269b8aaf95f8c0b0473cbf9c0365a8577352a367d2a7` |
| `tests\contract\test_llm_deployment_provenance.py` | `39d1d64f3901b25c764b3e667fd67510dd087fb500feba6d6e12c7335dc86a3f` |
| `tests\integration\test_llm_deployment_provenance.py` | `23a3384811ed5a127cb1bcbe29060dbee58810d00a8f3d20d0a6cd6594441570` |
# Current addendum — approved Dev preservation preparation (2026-10-19)

This addendum supersedes **authoring/build blocked** statements below only for
the explicitly approved existing Dev target. It does not supersede any release,
healthy rollback, staging/production, What-If or activation gate. Authority is
the current user's **“Approve — preserve live baseline; use a verifiably pinned
AVM child if compatible; prepare immutable application candidates”**, expressly
limited to **PREPARATION ONLY**. No new approval timestamp or TTL is fabricated.

## Current gates and observation binding

- **G0:** actual UTC checked before live reads; collection used the existing
  credential with explicit subscription `74a25c57-d6e4-446e-8c99-7f5ace60011b`,
  inside the approved `2026-10-19T09:15:34Z–17:15:34Z` read window.
- **G1:** the supplied acceptance is for bounded **preservation authoring**,
  not unhealthy-app readiness. `evidence/dev-preparation/refresh.json` refreshes
  account/auth/network/identity, all four deployments, RAI, diagnostics,
  inherited access, policy assignment metadata and current API/agents revision
  configuration from **2026-10-19T13:13:17.862389Z**. Model, SKU, capacity,
  upgrade, RAI, account and revision/image invariants matched. Full original
  versus refreshed checks in `protection-comparison.json` additionally match
  all **50** direct/inherited RBAC assignments (including conditions), all
  **11** policy assignment bindings (definitions/parameters/enforcement/scope/
  exclusions/selectors/overrides), and diagnostic workspace/categories/
  retention. Observation timestamps are not renewed by compiling or testing.
  A supplementary `policy-definition-refresh.json` at approximately **13:52Z**
  matches all **27** selected definition semantics: all seven assigned
  initiatives, every deny-initiative member and the target-relevant rules.
  Rules, effect defaults, allowed values and member bindings are unchanged.
  An initial comparison discrepancy was only descriptive parameter metadata
  omitted from the original sanitized capture; investigation is retained.
  This is not a new claim to have refetched all 329 definitions or live policy
  compliance states. The original 334 effect evaluations remain preserved.
- **Freshness:** the user's approved **one-hour maximum observation age** applies
  at use. Refresh before What-If and activation. Any changed candidate binding
  requires reconciliation and explicit reapproval. The G0 end is not an
  invented approval-expiry time for the baseline or application candidate.
- **G2:** complete discovery retains all **3 subscription + 8 inherited**
  assignments and 334 effect evaluations. Portal-visible eight plus proven
  three SystemHidden assignments is reconciled coverage, not raw-count parity.
  Current preparation uses these constraints without a governance waiver.
- **G3:** the approved unchanged child from parent AVM publication **0.18.0** is
  vendored with complete MIT notice and provenance. Its bytes/hash match both
  published archive and pinned commit. No invented standalone child registry
  address or full account AVM was introduced. Target GET API `2026-05-01`
  succeeded; local compile succeeds. This is not evidence of write semantics.
- **G4:** **NOT APPROVED / NOT RUN**. No What-If, deployment, inference, registry
  push, remote build, permissions/auth/network change, secret request, traffic
  change, commit, hook or workflow was performed.

## Implemented and compiled scope

T024–T026 are implemented. All nine top-level tier name/model/version selections
pass unchanged to the wrapper; model/version have no global GPT defaults.
Names default to purpose/environment only for new resources. Dev explicitly
supplies **`gpt-5.4-dev`, `gpt-5.4-mini-dev`, `gpt-5.4-sim-dev`**; all three
actually use **`gpt-5.4@2026-03-05`**, capacities **30/60/20**, **GlobalStandard**,
their original custom RAI attachments, and
**`OnceNewDefaultVersionAvailable`**. Per-tier SKU/capacity/upgrade bindings
prevent an AVM default substitution. Embedding remains
**`text-embedding-3-large-dev` / `text-embedding-3-large@1` / Standard / 60 /
Microsoft.DefaultV2 / OnceNewDefaultVersionAvailable**.

The child has an existing-only parent; its sole writable resource is a model
deployment. The wrapper retains the original RAI definitions and diagnostics,
with no RBAC writes when its original empty principal list is used. Its compiled
barriers preserve the complete reasoning RAI → deployment → drafting RAI →
deployment → simulation RAI → deployment → embedding chain.

Both API and agents receive the same complete tier `_DEPLOYMENT`, `_MODEL_ID`,
`_MODEL_VERSION`, `_MODEL_KEY`, region, direct embedding deployment and single
clean CSV. Shared chat model coordinates are omitted, not first-wins collapsed:

```text
reasoning=gpt-5.4-dev,drafting=gpt-5.4-mini-dev,simulation=gpt-5.4-sim-dev,text-embedding-3-large=text-embedding-3-large-dev,text-embedding-3-large@1=text-embedding-3-large-dev
```

Actual compiler-output contracts evaluate the generated pure ARM expressions
and run the shared runtime validator, including distinct/exact/base/shared
coordinate cases and rejection of unrelated alias collisions. Collision
rejection is a mandatory local preflight/runtime validation, not a claim that
the ARM deployment engine validates CSV routing semantics.

**T027 remains PARTIAL and unchecked:** only Dev parameters were verified and
updated; staging/production were not inferred, copied or compiled as approved.
**T030 remains PARTIAL and unchecked:** Dev local verification is complete,
but its T027/all-target prerequisite is not. This is not 52/52 completion.

## Actual local validation

- Bicep **0.46.1**: `build` and `lint` for `infra/main.bicep` and
  `infra/modules/azure-openai.bicep`: **exit 0**. Both adjacent ARM JSON files
  were compiler-generated, never hand-authored. Explicit Dev main and bounded
  wrapper `build-params`: **exit 0**.
- Actual-compiled contracts plus configuration/map/routing/provenance/schema
  and preflight contracts: **618 passed**. The new compiler tests are not the
  older synthetic CLI acceptance tests. Additional mocked unit/integration
  routing/provenance checks: **357 passed**, with no live inference.
- Ruff on new Python helpers/contracts: **passed**.
- Existing PSRule **2.9.0 / Rules.Azure 1.47.0 / Azure.Default**, existing
  `ps-rule.yaml`, explicit Dev parameter file: **797 Pass, zero Fail**.
  Existing suppressions were retained, not expanded. The initial invocation
  lacked a Bicep path; rerunning with the installed CLI explicitly configured
  resolved that tool issue. The full `infra/` invocation then **stopped** on the
  old `validation-1816801545.bicepparam` missing newly required model/upgrade
  parameters. Unapproved targets/placeholder validation inputs were not filled
  with guessed selections. Full-repository PSRule is therefore **not passed**.
- Retained Bicep warnings: wrapper `location`/`tags` compatibility parameters
  are unused because it cannot rewrite the existing account; unrelated existing
  help-storage unused tags, IoT secure-input warning and unused evidence-harness
  existing resource remain. Upstream's BCP081 suppression is unchanged.
- Local Docker builds use the existing repository-root API/agents contexts,
  preserving source and Dockerfiles. Build logs, the filtered source SHA256
  manifest and observed immutable base digest are under `evidence/dev-preparation/`.
  The paired local image/config bindings and network-isolated resolver smoke
  results were recorded by the successful `prepare.py` run at approximately
  **2026-10-19T14:09:17.762034Z** in `candidate-bindings.json`. A local Docker image ID is **not** a verified ACR manifest
  digest; no publishable ACR digest is invented.
  The API build succeeded and its immutable local ID is
  `sha256:5bbd6497c7c74c0aa8e11a67326c8bfffc1f68ca4c894b30344e4e8dbd6474cb`;
  its isolated resolver smoke passed against the exact source hash. The first
  agents build failed fetching a public package dependency after timeout/DNS
  failures. Signed public-package redirect query strings were redacted from
  persisted logs. Independent host/container DNS probes then succeeded; one
  unchanged-Dockerfile retry **succeeded, exit 0**, producing agents image
  `sha256:2bee5de4feeb4794253f62d4769799c05a83debb0798120fab0b3bc8ffd3cd1f`.
  Both images passed network-isolated packaged-source hash and three-tier
  resolver smoke checks. `candidate-bindings.json` records
  `paired_application_candidate_complete=true`, exact local immutable IDs,
  identical LLM environment, preserved nonsecret environment/secretRefs and
  compiler/parameter/source hashes. No older or placeholder image was substituted.
  Package versions are captured for both real images. This proves local
  preparation, not application health, registry publication, rollback readiness
  or release approval.

## Inventory and release stop

`main-inventory-review.json` records actual regenerated full-main inventory
versus the historical checked-in ARM: **76 → 78 root entries**, including
pre-existing source/ARM differences involving web name expressions, `entra-auth`,
`sim-events`, storage and unrelated module bodies. The account's generated body
is unchanged from historical ARM; no full-account refactor was performed.
These differences are **not live What-If findings**, and are not authorised
changes. Do **not** run full `azd up` or deploy regenerated `main.json`.

The reviewable bounded model composition is
`evidence/dev-preparation/deployments.template.json` with
`deployments.parameters.json`, compiled from the reused wrapper and explicit
existing Dev account. It has zero account writes, four exact existing model
identities, three retained RAI definitions, retained diagnostics and zero RBAC
writes. Evaluated fields match the refreshed baseline; actual create/replace/
delete/no-op classification still requires separately approved fresh What-If.
Existing `SecurityControl=Ignore` was observed, not added/copied to any new
resource. No audit finding was used to change public access, local auth,
network, identities, roles, diagnostics, embedding or existing GlobalStandard
placement; GlobalStandard is not an AU-only inference guarantee. MFA write
authorization is not established by these GETs or local scans.

API `ca-api-dev--n6l54uy` and agents `ca-agents-dev--pm412va` remain unhealthy,
ActivationFailed, 100% active mutable hello-world placeholders. No healthy
rollback pair or immutable live image was discovered or fabricated. Candidate
source/config/image binding approval, publication to an approved registry,
healthy paired rollback/readiness evidence, a narrowly scoped fresh What-If
review and later activation permission are still separate release gates.

## Bounded preview and local diagnostic remediation - 2026-10-19

The user separately approved bounded Dev metadata/ARM validation/What-If and
renewed the expired window for two hours. `validation-approval.json` records the
conservative permitted interval; all files below are under `evidence/dev-preparation`.
The 21:51 UTC metadata matches original target, account controls, identity/tags,
four deployments, RAI, diagnostics, all 11 policy assignments, RBAC and application
revision/configuration evidence. All 27 relevant policy/initiative semantics match.

ARM validation and actual What-If operations passed, but preservation review is
**BLOCKED**, not release-ready. Machine JSON reports **eight Modify, 45 Ignore,
zero resource Create/Delete**. The helper console counts nested property lines,
not resources; its printed 23 Modify / 21 Delete is not a resource inventory.
The real strict carve-out invocation with actual JSON failed, exit 4, for all
four exact Dev deployment names. No gpt-5.4 registry approval exists.
The complete deltas and raw evidence hashes are in `validation-review.json`.

The user then selected **"Continue local remediation only; keep deployment blocked"**.
No later Azure requests or cloud mutations occurred. The existing compiler test
was strengthened from enabled-category-set equality to full diagnostic snapshot
equality and reproduced missing retention plus three disabled log categories.
An optional root/module diagnostic snapshot now preserves these exact Dev values
in both parameter surfaces without altering defaults for other environments.
Three focused cases cover absent versus explicitly empty log/metric arrays.

Actual validation after the local correction:

- `pytest tests\contract\test_llm_deployment_compiled.py tests\contract\test_llm_deployment_configuration.py -q`:
  **48 passed**. The first strengthened-test run failed on the actual omission.
- Actual root/module Bicep build/lint: exit 0; checked-in ARM regenerated by Bicep.
- Focused Ruff check and test-file formatter check: passed.
- Actual explicit-Dev PSRule Azure.Default: **797 Pass / zero Fail**.
  Initial process-local tool discovery/timeout failures were resolved by pointing
  PSRule to the existing Bicep binary and explicitly retaining the repository's
  60-second timeout. No install, rule change or exemption was added.
- Application source-manifest hashes and LLM CSV still match original local
  candidates; both immutable local image IDs remain available.

The new compiled proposal is separately bound in
`diagnostics-remediation-bindings.json`; the original approved template and real
preview remain unchanged. The old preview cannot clear the corrected proposal:
new bindings require fresh approval/What-If. No new release readiness is claimed.
RAI `action=NONE` and returned deployment field omissions remain unresolved,
not declared false positives. Registry approval, immutable published manifests,
configuration/healthy rollback evidence and G4 remain missing. T027/T030 remain
partial; no staging/production acceptance or new independent full verification
is inferred from these focused local results. No commit was made.

## Corrected real preview after renewed Dev request - 2026-10-19 22:40 UTC

The user requested Dev deployment, then approved fresh validation of the corrected
bounded candidate while retaining release gates. Approval reference: not supplied.
`corrected-validation-approval.json` binds the exact corrected template/parameters
and retains the existing 23:43:19 UTC G0 cutoff.

New capture files preserve all old evidence hashes. Fresh metadata at 22:35 UTC
matches target, controls, identity/tags, all model/protection settings, effective
policy assignments, RBAC and the still-unhealthy application revisions. All 27
relevant definition/initiative semantic comparisons pass. Focused capture-script
Ruff and compilation checks passed after adding distinct output-path arguments.

ARM validation: PASS. Real corrected What-If: **7 Modify / 1 NoChange / 45 Ignore,
zero resource Create/Delete**. Diagnostics: **NoChange**, verifying the fix live.
The existing strict carve-out against the actual corrected JSON still fails,
exit 4, on all four existing Dev names. No required approval was fabricated.

The exact 2026-05-01 deployment input reference includes currentCapacity and
deploymentState, which controls Running/Paused inference availability. Thus the
remaining omissions are not established read-only false positives. The unchanged
pinned AVM child has no corresponding inputs. No speculative action/API/property
changes were made to clear them; three RAI action omissions also remain unresolved.
Operational G3 preservation and G4 stay blocked. Full details and hashed evidence:
`evidence/dev-preparation/corrected-validation-review.json`.

No image publication, resource deployment, inference, traffic/permission change,
or commit occurred. No successful deployment or operational acceptance is claimed.

## Carve-out validator model identity correction

The registry check now uses proposed `after.properties.model.name`, not the
deployment resource-name alias. It rejects absent/empty proposed model metadata
without falling back to an approved alias or `before` model, ignores resources
not being deployed (Ignore/Delete), and checks proposed as well as root location.
The registry and schema documentation now explicitly identify underlying models;
no approval entry, reviewer, date or security requirement was changed.

Ten regression cases cover Create/Modify/NoChange aliases, both What-If result
wrappers, an approved-looking alias hiding an unregistered model, missing proposed
identity despite approved alias/before state, Ignore/Delete, and non-AU locations.
Before correction: **9 failed / 1 passed**. After correction: **all 10 pass**.
Combined enforcement/security/schema run: **27 passed / one unchanged pre-existing
failure**. The baseline before changes was **17 passed / that same failure**:
`tests/security/test_foundry_carveout.py::test_valid_deployment_passes` incorrectly
expects eastus and a 2030 review date to pass current AU/date rules. It was not
modified. Focused Ruff check/format and PowerShell parser checks passed.

Offline replay of the unchanged real corrected Dev What-If now accepts the
registered embedding model. Exit 4 remains solely for underlying gpt-5.4 across
the three chat aliases; the prior all-four-alias false-rejection explanation is
historical. Evidence: `evidence/dev-preparation/model-identity-carveout-replay.json`
and separate stdout/stderr logs. No existing evidence hashes were rewritten.
This proves the matching fix, not a new model approval or successful release.
No Azure operation, image publication, inference, deployment or commit occurred.

## Explicit quorum waiver and model registration — 2026-10-20

The project lead explicitly authorised skipping additional approvers and selected
**All environments / 2030-11-20**. The registry records a distinct `quorum_waiver`
with sole authoriser `johnbilliris`, exact instruction reference and inclusive UTC
expiry. The normal floors are retained; expiry/removal restores them. No second
approval is represented. A `gpt-5.4` Dev row now records the genuine sole approver
and model review deadline **2027-04-08**, on the existing registry review cycle.
The waiver does not waive the separate maximum twelve-month model review window.

Both schemas, PowerShell and OPA apply the explicit approval-count exception.
The focused enforcement/schema/OPA/security run reports **64 passed / one
unchanged baseline failure** (`test_valid_deployment_passes`, eastus / 2030 model
review). New cases exercise every environment, normal quorum restoration,
missing/invalid/expired waiver evidence, and retained non-AU/placeholder/no-
approver/data-flag/model-review rejection. Real OPA 0.70.0 compiled and evaluated
the policy; its tests did not rely on the Python fallback. Ruff check/format,
PowerShell parsing and diff whitespace checks pass.

Strict offline replay of the unchanged corrected live Dev preview now returns
**0**, and real OPA evaluation of the actual registry has no denials. With OPA's
clock set to **2030-11-21 UTC**, the policy rejects the expired exception and the
one-approver row. Bound inputs, source hashes, scope, expiry and limitations are
in `evidence/dev-preparation/single-approver-waiver-replay.json`, with separate
stdout/stderr logs. Old captured evidence/hashes were not rewritten.

This clears the carve-out blocker under the authorised exception, not the
capacity/state/RAI preservation, fresh live evidence, publication/config/rollback
or stage-release gates. No Azure call, deployment, image push or commit occurred.
