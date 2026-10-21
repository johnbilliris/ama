# Tasks: Unambiguous LLM Deployment Configuration and Routing

**Implementation checkpoint, 2026-10-20 07:07 UTC, T053-T057:** T053-T055 are
complete within the approved implementation/Dev validation scope. T053 corrects
deployment-qualified routing across common sync/stream, MAF, controller and
dispatcher paths. The explicitly approved first-party existing-parent child
preserves all four observed capacities/states without changing pinned vendor
bytes; the approved RAI API representation retains complete filters and exact
`NONE` actions. Twelve strengthened infrastructure cases failed before the fix;
60 compiler/configuration cases pass, and explicit-Dev PSRule has 797 Pass /
zero Fail. ARM validation succeeds; the exact bounded What-If returns eight
NoChange resources and 45 Ignore, with no other changes, diagnostics or potential
changes. **53/57 tasks are checked**. T056 and original T027 remain blocked by
absent approved staging/production evidence/scope; T057 and original T030 remain
partial for all-target acceptance. Bicep and existing ARM artifacts were updated,
but no image build, deployment, inference, IAM/policy/secret or traffic change
occurred. See the latest checkpoint in `verification.md`; earlier checkpoints
below retain their historical scope.

**Current operational checkpoint, 2026-10-20 04:52 UTC:** the explicitly
approved dependency-remediation stage is deployed and accepted at zero traffic.
The corrected API image fixes Redis authentication and Search alias API
compatibility; actual API clients pass, as does the unchanged agents image's
configured retrieval metadata. The empty repository corpus schema/alias exists
without ingestion. Both apps are Healthy with four started/ready replicas,
zero restarts, exact pairing and preserved full configuration/protected
resources. Three additional app-identity tier requests pass; the original
maximum reserved budget is eight of nine, with only one simulation reservation
remaining. No new grants, secret-value operations, Foundry writes or promotion.
The corpus remains empty; grounded acceptance/ingestion and business promotion
are not claimed. Feature tasks remain **50/52**, with T027/T030 partial for
missing staging/production evidence. Prior checkpoints below are historical.

**Current operational checkpoint, 2026-10-20 03:53 UTC:** the separately
approved unheld zero-traffic Dev pair is Healthy; exact API-to-agents binding
and three bounded app-identity synthetic tier requests pass. Fixed preparation
to include observed required region; 64 focused tests pass. All Foundry resource
protections and full app state comparisons pass unchanged. No traffic promotion,
new grants or application secret operations. Broader business release is blocked
by missing Search corpus and the existing API Redis client's omitted Entra
authentication. Repairs need a new image/schema-provisioning scope; none was
silently performed under metadata-only authority. 50/52 feature tasks remain
complete, with T027/T030 still partial for other environments. Earlier checkpoint
paragraphs below retain their original stage boundaries.

**Latest resumed checkpoint, 2026-10-20:** 50/52 tasks complete; T027/T030
remain partial for missing staging/production evidence. The user approved
application-only Dev held-bootstrap staging and the narrowly scoped exact-PATCH
validation amendment in `contracts/rollout-and-preflight.md`. The vetted pair
is published and both ACR-scoped pull grants are verified. Both exact held
revisions are deployed with successful live startup probes, two Running
replicas each and zero candidate business traffic; writable-state preservation
and independent unchanged Foundry comparisons pass. No Foundry writes,
unheld startup, inference or business promotion are authorised by that stage.
Historical gate/status paragraphs below retain their original checkpoint
context; current proof is in `rollout-evidence.md` and the deployment plan.

**Input**: Approved `specs/041-llm-deployment-routing/{spec.md,plan.md,research.md,data-model.md,quickstart.md}`, three `contracts/*.md`, and `checklists/{requirements,routing-rollout}.md`.
**Prerequisites**: Human approval of this Tasks checkpoint; reviewer-owned requirements-quality gate below before implementation; additional external gates before IaC authoring or operational execution.
**Tests**: Required by SC-001–SC-007, plan and quickstart. Use hermetic fake SDK/HTTP transports, not Azure inference. Write focused regression tests first, demonstrate the expected failure, then implement and rerun.
**Organization**: Setup → foundation → US1 P1 → US2 P1 → US3 P1 → US4 P2 → cross-cutting verification. Phase numbers here are implementation phases, not fleet checkpoint numbers; this entire artifact is the fleet's Phase 5 Tasks output.

## Format and Path Conventions

- Checklist format: `- [ ] Tnnn [P?] [USn?] Description with exact repository-relative file paths`.
- `<!-- parallel-group: N -->` starts one bounded group of two or three independent `[P]` tasks; all group prerequisites must already be complete. Join the group before the next sequential task. `<!-- sequential -->` starts ordered work, not a fan-out.
- Paths below are relative to `C:\code\ama`. New test and evidence files are identified explicitly. Reuse existing implementations; do not add a routing service, SDK layer, dependency upgrade or platform rewrite.
- Every checkbox is pending. Task generation is not implementation, acceptance, checklist approval or operational authorisation.
- Do not commit as part of task execution unless separately instructed. Never rewrite stored historical audit records.

## Authority and External Gates (not automatic implementation tasks)

| Gate | Required evidence / decision | Blocks |
| --- | --- | --- |
| H0 — Tasks approval | Human approval of this artifact; no handoff or automatic implementation | All future task execution |
| H1 — requirements-quality review | Actual reviewer evaluation of CHK001–CHK036, source-referenced findings, remediation and reviewer acceptance; retain the separate built-in requirements checklist lifecycle | Implementation after T002; do not bypass the checklist gate |
| G0 — scoped evidence-collection authorisation | Recorded approver/target/operations/window/credentials: baseline/governance reads may precede G1/G2; explicit validation scope after G1–G3/local candidate review permits metadata reads, mandatory What-If and strict carve-out evidence collection for G4 | Any Azure read/validation lacking that explicit scope; grants no canary, activation, switch, promotion, provisioning or deletion authority |
| G1 — baseline approval | Authorised target-scoped read-only inventory; reconciled and approved names, model/version/format, SKU/capacity, RAI/effective filters, upgrade behaviour, access/network/auth, endpoint/residency, embedding and API/agents revision snapshots | Target-specific parameter values, IaC authoring under this plan, release and provisioning |
| G2 — governance clearance | Current feature-041 `04-governance-constraints.md` and `.json`, timestamped tenant/subscription/scope, inherited policy and Portal parity; applicable effects/property paths/required values | Bicep authoring/build and provisioning; historical specs do not clear this gate |
| G3 — AVM preservation compatibility | Published pinned consumable AVM composition, existing-parent support, exact baseline preservation and RAI/deployment operation serialization; scope decision if this needs an account rewrite | Bicep authoring/build; no silent raw-resource exemption |
| G4 — P1 release approval | Passing local acceptance, compatible readers, reviewed generated ARM/PSRule, G0-authorised mandatory What-If and strict carve-out results, verified target metadata, current exact matched API/agents image/config snapshots, safe rollback pair and human stage-specific approval | Canary inference, application/config activation, switch or promotion without the corresponding approval; does not block G0-authorised evidence collection needed to obtain G4 |
| G5a — optional P2 provisioning approval | Independently approved target-bound proposal/window, unchanged proposed model/protections, approved observation/retention criteria, current baseline/governance/What-If evidence and old+new coexistence quota/headroom in the actual pool | Replacement provisioning; does not require already-provisioned replacements and grants no inference or traffic-switch authority |
| G5b — optional P2 traffic-stage approval | Actual successful replacement provisioning, verified model/version/SKU/capacity/effective-policy/access parity and readiness, compatible candidate revisions, retained rollback pair and separately recorded stage-specific approval | Canary inference, traffic switch, forward/rollback rehearsal without the corresponding approval; provisioning approval alone does not satisfy this gate |
| G6 — separate retirement approval | Observation and rollback evidence; no active revision, worker, eval or rollback dependency; explicit deletion approval | Any old deployment retirement/deletion |

G1–G3 are currently **unsatisfied**. Record missing evidence as blocked, never fill it with dev observations or guessed model choices. Local Python work can proceed after H0/H1 and foundation without clearing Azure gates. At a blocked IaC task, stop that lane; do not waive the gate or claim US2 release complete. No task below executes provisioning, traffic switching or deletion. G5/G6 execution is optional future operational work, outside this implementation checklist.

All target evidence requires the approved freshness/invalidation policy and
target/config/image/compiled-proposal bindings in `contracts/rollout-and-preflight.md`.
Missing/unapproved policy, stale/unbound evidence or unevaluated invalidation
fails closed; no universal TTL is selected here. G0 collection approval is
distinct from evidence approval and from G4/G5/G6 operational decisions.

G5 denotes the staged G5a/G5b migration approvals, not a single blanket
permission. G0-authorised post-provision metadata reads establish actual
replacement parity/readiness after G5a and before G5b; these checks do not
permit inference or switching. Each G5b approval records its permitted stages,
window and rollback scope. G6 retirement remains independent.

## Phase 1: Setup (Shared Preparation)

**Purpose**: Resolve review readiness, preserve baseline behaviour and bind acceptance to the approved scope. No project scaffolding or package upgrade is needed.

<!-- sequential -->
- [X] T001 Perform the actual requirements-quality review of CHK001–CHK036 in `specs/041-llm-deployment-routing/checklists/routing-rollout.md` against its cited sources; record per-item evidence, pass/gap/blocked disposition and reviewer ownership in new `specs/041-llm-deployment-routing/requirements-review.md`; inspect but do not reset `checklists/requirements.md`; this task is review, not marking all items complete.
- [X] T002 Resolve T001 findings in `specs/041-llm-deployment-routing/requirements-review.md`: propose narrowly scoped source-document corrections for approval where needed, obtain reviewer re-evaluation and H1 acceptance before implementation; only the owning reviewer may update satisfied markers in `checklists/routing-rollout.md`, and unresolved criteria remain unchecked and blocking; do not change approved scope or invent Q&A.
- [X] T003 Close the production SDK/caller inventory from `apps/agents/common/llm_client.py`, `apps/agents/common/foundry_chat_client.py`, `apps/agents/maf_runtime/chat_client.py`, `apps/agents/dispatcher/agent.py`, `apps/api/app/services/simulation/controller_service.py`, `apps/eval-runner/src/ama_eval/foundry_client.py`, `apps/ingest-runner/src/ama_ingest/embedder.py` and `apps/agents/common/foundry_query_embedder.py` in new `specs/041-llm-deployment-routing/verification.md`; enumerate sync/stream/MAF/controller requests and all six dispatcher roles, legacy and embedding consumers, concrete test nodes and the SC-001 denominator; preserve existing Help enablement.
- [X] T004 Capture existing quickstart regression results and historical fixture byte hashes in `specs/041-llm-deployment-routing/verification.md`, using the existing `tests/contract/test_foundry_chat_client_aoai.py`, `tests/contract/test_audit_record_shape.py`, `tests/contract/test_audit_replay_fidelity.py` and `tests/contract/test_simulation_api_contract.py`; identify first-write-wins assertions to replace, separate pre-existing failures, and record commands without presenting planning's ten passing tests as feature acceptance.

## Phase 2: Foundational (Blocking Local Prerequisites)

**Purpose**: Freeze test inputs and establish shared identity/evidence types before client or writer changes. H0/H1 and T003–T004 must be complete.

<!-- sequential -->
- [X] T005 Add hermetic fixtures in new `tests/fixtures/llm_deployment_routing.py` and synthetic old/new provenance examples in new `tests/fixtures/llm_deployment_provenance.json`: three distinct deployments sharing one synthetic model/version, all six orderings, raw duplicate CSVs, absent/blank/partial settings, old/new dispatcher payloads and request-submission spies; clear inherited AZURE_AI/AZURE_OPENAI settings per test and deny real network calls without changing global environments.
- [X] T006 Define frozen tier/model/routing/resolved identity types in `apps/agents/common/llm_config.py` using `data-model.md` §§1–6: closed chat enum "`reasoning`, `drafting`, `simulation`"; model_id and model_version "`non-empty string`", model_version "`Opaque provider version, never parsed from a name`", model_key "`model_id@model_version`"; deployment_name "`non-empty string`"; metadata_source "`configured`, `legacy_coordinate`, `unavailable`"; resolution_source "`explicit_tier`, `tier_alias`, `legacy_exact`, `legacy_base`"; retain configuration_revision and optional verification_reference, with no ARM lookup or new service.
- [X] T007 Snapshot endpoint, region, raw CSV, each tier's source presence, deployment, model metadata and compatibility key once in `apps/agents/common/llm_config.py`; implement the constraints "`An absent explicit setting is different from an explicitly empty one`", "`Partially supplied new metadata is invalid`", "`fully absent legacy identity may remain unavailable for auditing`", and "`A complete configured model identity must agree with a supplied compatibility coordinate`"; subsequent environment mutation must not affect the process snapshot; keep embedding lookup outside the chat enum.
  Bind any admitted legacy identity to the resolved destination/account using the validated same-destination coordinate mapping or target/config-bound verification reference; a unique coordinate-to-B cannot supply explicit A's metadata. Retain A and unavailable identity if association is unproven; preserve metadata_association_reference in the shared result.
- [X] T008 Define request-local attempt evidence alongside existing response/usage types in `apps/agents/common/foundry_chat_client.py`: call_id/correlation_id "`string`", resolved_identity "`ResolvedDeployment or absent`", inference_attempted "`boolean or null`", inference_outcome "`succeeded`, `failed`, `not_attempted`, `unknown` or null", error_code "`optional existing error code`" and output provenance "`existing usage/hash fields`"; default unavailable evidence to unknown, not success; do not enable new strict-schema producers yet.

**Checkpoint**: Local contracts/fixtures exist. US1 routing can be implemented and tested without live baselines. Types alone neither activate strict readers nor emit new provenance fields.

## Phase 3: User Story 1 — Correct Tier Routing (P1, Local MVP)

**Goal**: All production chat paths honour explicit tiers; simulation is isolated; conflicting maps fail before inference while embedding and unambiguous legacy use survive.
**Independent test**: With fake transports, exercise the complete T003 inventory across six orderings of shared-model configurations; assert actual SDK destinations, all six simulation role routes, errors with zero outbound calls, explicit precedence, immutable snapshots and preserved legacy/embedding behaviour.

### Tests first

<!-- parallel-group: 1 -->
- [X] T009 [P] [US1] Add resolver table tests in new `tests/unit/test_llm_deployment_routing.py` for six orderings, explicit-over-valid-map precedence, absent versus empty settings, partial/inconsistent metadata, unsupported tiers, absent endpoint/region, immutable snapshots, alias/exact/base precedence and simulation/live deployment collision; assert zero transport calls on invalid paths.
  Include explicit A with new identity absent and unique exact-coordinate-to-B (A plus unavailable identity), matching A association, missing association and wrong-account proof. Compare explicit simulation against effective live alias/exact/base destinations with both live explicit env settings absent, mixed explicit/legacy live tiers, distinct-destination controls and unresolved required isolation comparison.
- [X] T010 [P] [US1] Add cross-client acceptance tests in new `tests/contract/test_llm_deployment_routing.py` for common sync/stream and MAF request boundaries without CSV aliases, legacy/test injection seams and safe diagnostics; require actual request destinations rather than factory construction alone; synthetic explicit metadata must remain separate from misleading names.
  Assert that explicit A/legacy-to-B with absent new metadata sends to A but never labels the request/usage with B's model; association-matched legacy/embedding consumers remain compatible.
- [X] T011 [P] [US1] Add parser/embedding conformance tests in new `tests/contract/test_llm_deployment_map_compatibility.py` against common, eval and ingest parsers and `apps/agents/common/foundry_query_embedder.py`: duplicate-identical pairs, both conflict orders, whitespace, malformed/empty entries and multiple `=`, blank entire map on explicit chat, retained embedding key/deployment/dimensions, deliberate per-run eval mapping and non-simulation exact/base compatibility.

### Implementation

<!-- sequential -->
- [X] T012 [US1] Implement raw CSV validation and shared pure resolution in `apps/agents/common/llm_config.py` before dictionary creation: "`Keys and values are trimmed and non-empty`", "`Equal key/equal destination repeats are idempotent`", "`Equal key/different destinations is invalid in every ordering`"; validate injected maps too; explicit tier wins only over valid maps; reasoning/drafting may use absent-setting alias/exact/configured-base lookup; simulation requires explicit non-empty deployment and "`must be distinct from reasoning/drafting in the same account`"; preserve FoundryConfigurationError diagnostics and fail before retries/request submission.
  Resolve destination before legacy metadata association and compare simulation to effective live destinations after the same explicit/alias/exact/base precedence, not only supplied live env settings; fail the affected simulation path if a required comparison cannot resolve. No network lookup, inferred account distinction or borrowed identity.
- [X] T013 [US1] Replace existing first-write-wins expectations with strict actionable-conflict tests in `tests/contract/test_foundry_chat_client_aoai.py` and update only affected routing expectations in `tests/contract/test_llm_model_routing.py`; verify explicit tier settings need no duplicate legacy aliases and keep AOAI endpoint shaping, managed identity and test-only injection contracts.
- [X] T014 [US1] Route `apps/agents/common/foundry_chat_client.py` sync/stream and `apps/agents/common/llm_client.py` through one resolved snapshot result; retain `model_key=` for unambiguous legacy/test callers, cache/retry/deadline/token/gateway semantics and existing error types; no production fallback to AZURE_OPENAI test settings and no re-resolution from live env.

<!-- parallel-group: 2 -->
- [X] T015 [P] [US1] Update `apps/agents/maf_runtime/chat_client.py` to use the shared resolved deployment for reasoning/drafting without requiring CSV tier aliases; preserve public factory arguments, token provider/AAD scope and externally observed ValueError boundary with shared diagnostic as cause; exercise the request spy from T010.
- [X] T016 [P] [US1] Update every role in `apps/agents/dispatcher/agent.py` to request explicit simulation tier, remove model-key/reasoning fallback, and make unresolved readiness/configuration errors explicit through existing logging/degraded reply conventions; preserve all six role URLs, prompts, AIIMS tagging and safety controls.
- [X] T017 [P] [US1] Resolve explicit simulation configuration before any completion in `apps/api/app/services/simulation/controller_service.py`; remove shared/reasoning fallback while retaining direct AsyncAzureOpenAI streaming/tools transport and existing SSE `error` / `openai_unavailable` conventions naming `AZURE_AI_SIMULATION_DEPLOYMENT`; configuration failure sends zero requests.

<!-- parallel-group: 3 -->
- [X] T018 [P] [US1] Bring `apps/eval-runner/src/ama_eval/foundry_client.py` map parsing into T011 strict conformance without importing another app; preserve explicit unambiguous per-run model mapping, fail omitted ambiguous coordinates rather than guessing a tier, and do not redesign evaluations.
- [X] T019 [P] [US1] Bring `apps/ingest-runner/src/ama_ingest/embedder.py` map parsing into T011 strict conformance without cross-app imports; preserve embedding coordinate, deployment, dimensions, model and direct query embedding contract in `apps/agents/common/foundry_query_embedder.py` without unnecessary edits to the query embedder.

<!-- sequential -->
- [X] T020 [US1] Add hermetic end-to-end request-routing cases in new `tests/integration/test_llm_deployment_routing.py` using ASGI dispatcher and fake controller tool streaming: all six roles, common/MAF calls, shared model keys, no/blank simulation, isolation collisions and invalid-map zero-call assertions; retain public chat/SSE/tools/citations and unrelated-path degradation.
  Exercise mixed explicit/legacy live-tier isolation through alias, exact and base paths with no live explicit settings, and explicit A versus legacy-to-B metadata through real adapter request/provenance seams.
- [X] T021 [US1] Run T009–T011/T013/T020 and the routing/gateway/fallback/managed-identity/circuit-breaker regressions identified in `specs/041-llm-deployment-routing/quickstart.md`; record per-path results and complete SC-001–SC-003 denominator coverage in `specs/041-llm-deployment-routing/verification.md`; explicitly record that strict code is an inactive local candidate until coordinated US2 configuration/readers and G4 pass.

**Checkpoint**: US1 is independently verifiable locally. It is **not deployable alone** into old ambiguous maps. No permissive conflict bypass is allowed.

## Phase 4: User Story 2 — Safe Infrastructure Configuration (P1)

**Goal**: Independently express tier names/models/versions and truthful outputs while preserving every approved existing resource/property. Deliver preflight validation and a coordinated candidate contract, not a deployment.
**Independent test**: Synthetic compiled configuration and offline preflight fixtures demonstrate pass-through, clean CSV and zero baseline drift; an authorised target's approved baseline is required to claim target readiness.
**Gate**: T022–T023 and T028–T029 are local tests/tooling and may proceed without Azure access. T024–T027/T030 Bicep authoring/build require G1–G3; missing evidence means blocked, not guessed parameters.

### Tests first

<!-- parallel-group: 4 -->
- [X] T022 [P] [US2] Add configuration/output contract tests in new `tests/contract/test_llm_deployment_configuration.py` for nine explicit top-level selections, same model/version across three destinations, purpose/environment defaults only for new resources, explicit old names, complete API/agents identity env, collision-free aliases with omitted ambiguous model coordinates, retained embedding/unambiguous legacy outputs, child pass-through and unchanged protections using synthetic compiler/preflight fixtures.
- [X] T023 [P] [US2] Add offline preflight failure tests in new `tests/unit/test_llm_deployment_preflight.py` for scope mismatch, missing/unreadable deployment metadata, absent approvals, stale/unreconciled evidence, model/version/protection drift, simulation collision and mismatched image/config pairs; assert verification fails closed and no Azure calls or mutations occur.
  Cover missing/unapproved freshness policy/version, absent target/config/image/compiled-proposal bindings, policy-defined expiry, invalidating drift/revision changes without refresh, and valid current exact bindings; fixture windows are synthetic, not a production TTL.

### Gated infrastructure implementation

<!-- sequential -->
- [X] T024 [US2] After G1–G3 evidence is supplied, implement the bounded approved deployment composition in `infra/modules/azure-openai.bicep`; use the verified pinned AVM when compatible or stop for scope approval; make model/version explicit for direct child use, preserve operation serialization and baseline fields "`capacity | positive integer`", "`sku | string | Approved existing value, no default substitution`", "`version_upgrade_option | string or unavailable`", account_resource_id "`Environment-specific approved parent`", region "`Approved existing endpoint placement`", RAI "`Preserve attachment and effective filters`", and access_controls "`Preserve managed identities, roles, network and local-auth posture`"; no resource migration or account rewrite.
- [X] T025 [US2] After T024, expose `reasoningDeploymentName/reasoningModelName/reasoningModelVersion`, drafting equivalents and simulation equivalents in `infra/main.bicep`, pass all nine unchanged to the child, and publish separate `_DEPLOYMENT/_MODEL_ID/_MODEL_VERSION/_MODEL_KEY` to both API and agents; new-only name defaults are `reasoning-${environmentName}`, `drafting-${environmentName}`, `simulation-${environmentName}`; reject unrelated-name collisions, preserve compatible old outputs and all model/protection selections without global GPT defaults.
- [X] T026 [US2] After T025, generate collision-free compatibility CSV in `infra/modules/azure-openai.bicep` and wire its single source to both services in `infra/main.bicep`: include tier aliases, include exact/base legacy coordinates only when uniquely configured to one destination, omit ambiguous shared chat coordinates, preserve existing embedding model/version/deployment and direct embedding env; do not change resources or independently activate env against old clients.
- [ ] T027 [US2] After G1 approval for each individual target, supply explicit approved existing names, models and versions in `infra/parameters/dev.bicepparam`, `infra/parameters/staging.bicepparam` and `infra/parameters/production.bicepparam`; compare SKU/capacity/RAI/access/residency/upgrade behaviour and embedding against each target baseline, add only a narrow preservation override if necessary, and stop on missing values or drift rather than copying dev observations or provisioning.

### Local preflight and candidate contract

<!-- sequential -->
**2026-10-20 policy amendment:** the project lead explicitly waived additional
approvers for **all environments through 2030-11-20 UTC**. The registry retains
normal quorum settings and records the expiring exception; the Dev `gpt-5.4`
row records only the genuine `johnbilliris` approval. Model review remains due
2027-04-08. Strict offline replay of the captured Dev preview and actual OPA
evaluation pass; expiry restores normal quorum. This does not complete
T027/T030 or waive preservation, freshness, paired rollback or release gates.
Evidence: `evidence/dev-preparation/single-approver-waiver-replay.json`.

- [X] T028 [US2] Implement a local read-only evidence comparison CLI in new `scripts/verify-llm-deployment-preflight.py`, driven by T023 fixtures and `contracts/rollout-and-preflight.md`; accept already authorised inventory/baseline/output/candidate files, verify account/scope/approvals and per-tier properties plus exact raw CSV through the shared validator, compare full protection/embedding invariants, and return nonzero for missing/unverified/mismatched evidence; no ARM request path, approval fabrication, provisioning or configuration writes.
  Require approved freshness/invalidation policy/version, collection authority, target and applicable config/image/compiled-proposal bindings or explicit baseline-to-candidate reconciliation; evaluate supplied policy windows/invalidation events and fail nonzero on absent policy/binding or stale/invalidated evidence. Do not choose a universal TTL or silently refresh.
- [X] T029 [US2] Document evidence inputs and P1 activation/rollback sequence in new `specs/041-llm-deployment-routing/rollout-evidence.md`: baseline states "`uncollected -> observed -> reconciled -> approved`", environment/subscription/account/scope/timestamp/approver, three deployment identities plus embedding and current API/agents pairs, reader-first provenance, cleaned immutable env plus strict images as one activation unit, explicit per-run eval map where needed, post-switch drift checks and verified corrected rollback pair; unsafe pre-P1 simulation stays unavailable, never falls back to live tiers.
  Separate G0 read/validation scope from later G4 stage approvals, preserve mandatory What-If, and record approved freshness/invalidation policy/version, exact target/revision bindings and refresh/reapproval decisions; absent policy remains blocked. Report local verification, target P1 readiness and real P2 acceptance independently.
- [ ] T030 [US2] Only after G1–G3 and T024–T027, run approved local Bicep lint/build to regenerate `infra/main.json` and `infra/modules/azure-openai.json`, run T022–T023/T028 acceptance and existing local PSRule checks, and record compiled per-target comparisons in `specs/041-llm-deployment-routing/verification.md`; require zero P1 deployment creates/renames/replacements/deletions or model/version/SKU/capacity/RAI/access/residency changes; record G4 What-If/carve-out/live metadata checks as externally pending, not executed or passed.

**2026-10-19 bounded Dev preparation:** T024–T026 are locally implemented and
actual-compiler tested under the user's preservation/pinned-child/preparation
approval. T027 is **PARTIAL: Dev only** (explicit existing names/models/versions,
capacity/SKU/upgrade preservation); staging and production have no approved
baseline and remain untouched. T030 is **PARTIAL: Dev local build/lint/contracts
and explicit-Dev PSRule completed**, not its all-target acceptance. The full
`infra/` PSRule scan stops on unapproved/unpopulated parameter files; these were
not guessed. No What-If, cloud write, registry publication or activation occurred.
See `verification.md` current preparation addendum and
`evidence/dev-preparation/` for actual outputs. Neither partial task is ticked.

**Checkpoint**: Local US2 tooling is independently testable; target IaC remains blocked until G1–G3. Nothing here authorises deployment. Exact reader/image/config compatibility is rechecked after US3 before G4.

## Phase 5: User Story 3 — Trustworthy Inference Records (P1)

**Goal**: Separate model/version/deployment from actual attempt/outcome on successful, failed, uncertain and no-call paths without historical rewrites.
**Independent test**: Compare strict old/new schemas, stored-fixture bytes and fake request-boundary evidence across all producers, remote response loss, tool rounds and degraded/safety outcomes; no fabricated inference rows or obsolete labels.
**Dependencies**: Foundation and the US1 adapter seams. US2 target gates do not prevent this local story. Reader/schema tasks precede producer activation in implementation and deployment.

All producer/adapter tasks T037–T042 apply the normative per-surface admission
matrix in `contracts/inference-provenance.md`: only proved true submission
admits new inference/model-call projections (including unknown completion);
false or unknown submission uses existing event/invocation envelopes only.
HTTP correlation is not proof, configured targets are not invoked identities,
and new-write admission does not invalidate historical uncertain records.

### Tests first

<!-- parallel-group: 5 -->
- [X] T031 [P] [US3] Add old/new Pydantic and strict JSON-schema compatibility tests in new `tests/contract/test_llm_deployment_provenance_schema.py` using T005 fixtures: required string identities and `unknown`, optional nullable attempt/outcome, absence as unknown, legacy dispatcher payloads, required invocation model_deployment `unknown`, unchanged additionalProperties restrictions, replay/export compatibility and byte-identical historical fixtures.
- [X] T032 [P] [US3] Add submission-boundary unit tests in new `tests/unit/test_llm_inference_attempt_evidence.py`: config/credential/client/local SDK/gateway failure before submission is false/not_attempted; mere method/middleware entry is not evidence; unavailable submission is null/unknown; submitted timeout/4xx/5xx, partial stream/cancel, empty completion and safety fallback retain truthful evidence and actual usage.
  Prove the request-bound outbound SDK transport handoff signal with call ID/destination; distinguish locally observed submitted timeout (true/failed), correlated remote submission without terminal evidence (true/unknown completion), and unknown whether submission occurred (null/unknown).
- [X] T033 [P] [US3] Add producer/consumer contract cases in new `tests/contract/test_llm_deployment_provenance.py` for common usage/telemetry, MAF, dispatcher/API and controller no-RAG/multi-round failure; distinguish HTTP invocation from inference, misleading alias from model, and configured metadata from response-reported identity; assert no inference row for no-call outcomes and no new obsolete GPT-4o labels.
  Assert the provenance per-surface admission matrix at the owning writer: audit-enabled eligible single-call counts true/succeeded=1, true/failed=1, true/unknown completion=1, false/not_attempted=0, null/unknown submission=0. Preserve uncertain event/invocation envelopes and no model-call projection for unknown submission; do not retroactively reject historical uncertain rows.

### Readers and schemas before producers

<!-- parallel-group: 6 -->
- [X] T034 [P] [US3] Extend `packages/domain/src/ama_domain/audit_record.py` and `packages/schemas/spec_036/audit-record-llm-call.json` with optional nullable inference_attempted/inference_outcome using exactly "`succeeded`, `failed`, `not_attempted`, `unknown` or null"; "`retains required string model_id, model_version, deployment_alias`" and "`Keep call_kind as inference/embedding`"; keep strict extra-field rejection, accept historical absence as unavailable and update affected replay/export reader projections discovered by T003 without backfill.
- [X] T035 [P] [US3] Extend `packages/domain/src/domain/models/sub_agent_invocation_record.py`, `apps/api/app/services/simulation/sub_agent_invoker.py` and `apps/api/app/services/simulation/sub_agents/_base.py` readers additively: "`required string model_deployment uses unknown when unavailable`", "`SubAgentReply retains nullable model_deployment`", optional model_id/model_version/attempt/outcome/error provenance, historical/old-dispatcher absence unknown; preserve invocation_id, roles, citations, prompt_hash and AIIMS without enabling new response producers yet.

<!-- sequential -->
- [X] T036 [US3] Update `apps/agents/common/audit.py` writer after T031/T034/T035 reader tests pass: reuse the request's resolved identity, use "`unknown`" only for unavailable required string identity on actual inference, carry nullable evidence, and emit no make_inference_record row for known no-call outcomes; preserve RAG/opt-out, hash, gateway, tenant partition, correlation, sequence/durability and append-only rules; never modify old records.
  Enforce new inference-row admission only for true proved submission, including true/unknown completion; false and null/unknown submission emit zero inference rows. Retain uncertainty in existing agent/simulation/event envelopes, never invent invocation. One eligible row per distinct proved call ID at its owning writer; retain opt-out/deduplication and historical read compatibility.

### Producers and adapters

<!-- parallel-group: 7 -->
- [X] T037 [P] [US3] Instrument `apps/agents/common/foundry_chat_client.py` and propagate through `apps/agents/common/llm_client.py` with narrow existing transport/request hooks after gateway/local validation; preserve typed resolved identity across translated failures, actual submission and response usage for sync/stream/empty/partial outcomes, and unknown when submission cannot be proved; SDK method entry is insufficient and provider execution success is not inferred.
  Use the contract's exact outbound transport handoff boundary and matrix; proved submission with unavailable terminal evidence is true/unknown, whereas unknown submission is null/unknown and must not admit a model-call row/projection.
- [X] T038 [P] [US3] Update `apps/agents/common/llm_mixin.py` and `apps/agents/common/otel_telemetry.py` to propagate request evidence separately from generation method: no-call template degradation is not inference, post-call safety fallback retains real attempt/usage, model_id is underlying metadata and deployment is separate, with no alias parsing, obsolete default labels or sensitive prompt/PII logging.
- [X] T039 [P] [US3] Connect actual chat-adapter request evidence in `apps/agents/maf_runtime/chat_client.py` to `apps/agents/maf_runtime/middleware/audit_middleware.py` and `apps/agents/maf_runtime/middleware/otel_middleware.py`; agent `call_next()`/tool/policy execution alone cannot prove inference, no-call failures use existing event envelopes, and agent-level outcomes, safety and correlation remain intact.

<!-- parallel-group: 8 -->
- [X] T040 [P] [US3] Correct controller provenance in `apps/api/app/services/simulation/controller_service.py` using the same resolved simulation identity and per-submission evidence: distinct call IDs for each tool round under turn correlation, audit actual requests on no-RAG and failure paths, retain earlier rounds on later failure, and do not attribute aggregated/template output or fabricated usage to a completion; preserve SSE/tools/citations and opt-out behaviour.
- [X] T041 [P] [US3] Emit optional provenance from `apps/agents/dispatcher/agent.py` only after readers are ready: use FoundryResponse.deployment_id and resolved model metadata rather than raw deployment guesses, preserve nullable wire identity and truthful attempted/failed/unknown/degraded states for every role; HTTP invocation_id remains agent correlation, not proof of inference.
- [X] T042 [P] [US3] Remove `MODEL_DEPLOYMENT_BY_ROLE` identity fallback in `apps/api/app/services/simulation/sub_agent_invoker.py` and `apps/api/app/services/simulation/sub_agents/_base.py`; consume dispatcher evidence, keep the six-role set independent of model labels, retain null on nullable replies and unknown on required persisted fields, and classify lost HTTP responses as unknown rather than false/no-call or success.

<!-- sequential -->
- [X] T043 [US3] Add hermetic multi-service acceptance in new `tests/integration/test_llm_deployment_provenance.py` for submitted versus local failures, each controller tool-round request, no-RAG, gateway denial, empty/safety fallback, all dispatcher roles, old payloads, remote timeout/lost response and safe API/agents reader/writer combinations; assert exact model/version/deployment and no-call audit-row count at the actual transport boundary.
  Verify all five single-call admission counts from T033 across writer surfaces; first controller round proved/second unknown submission totals 1, both proved totals 2. A lost dispatcher response retains API null/unknown event evidence, not a duplicate/fabricated inference row; correlated true/unknown completion remains an actual attempt.
- [X] T044 [US3] Run T031–T033/T043 and existing audit shape/replay/export/telemetry, fallback and simulation contracts from `specs/041-llm-deployment-routing/quickstart.md`; record SC-004/SC-007 populations, pre/post historical fixture hashes and reader-before-producer activation evidence in `specs/041-llm-deployment-routing/verification.md`; preserve historical bytes and stop on unsupported strict readers rather than relaxing all schemas.

**Checkpoint**: New provenance is locally compatible and truthful. Deploy compatible readers first; do not enable producer fields on an unverified old strict consumer. Target release still needs US2 evidence and G4.

## Phase 6: User Story 4 — Controlled Naming Migration Procedure (P2)

**Goal**: Deliver the opt-in procedure and local failure/rollback rehearsal, not execute resource migration.
**Independent test**: Rehearse a synthetic approved-baseline scenario: replacements remain model/protection-equivalent, readiness precedes switch, failure restores the old corrected pair, and no retirement can occur without a distinct decision.
**Dependencies**: US1/US3 local verification and the US2 rollout/preflight contract T028–T029. Local rehearsal may use synthetic evidence while target G1–G4 remain blocked; no claim of real environment readiness.

### Tests first

<!-- sequential -->
- [X] T045 [US4] Add offline migration preflight cases in new `tests/unit/test_llm_deployment_migration_preflight.py` against `scripts/verify-llm-deployment-preflight.py`: independent P2 approval, unchanged model/protections, correct old+new quota pool/headroom evidence, observation/retention decisions, verified old corrected pair and separate retirement decision; missing evidence must block the relevant step without invoking Azure.

### Procedure and rehearsal

<!-- sequential -->
- [X] T046 [US4] Write new `specs/041-llm-deployment-routing/naming-migration.md` with G5/G6 boundaries and migration states "`proposed -> approved -> replacements_ready -> switched -> verified -> retained`", failure "`rolled_back`" and "`retained -> retirement_approved -> retired`"; specify environment/approval/old-new identities, unchanged model/protection comparisons, governance/quota evidence, readiness, paired revisions, verification, rollback, observation/retention and separate retirement reference; no automatic transition, rename, model choice or operational execution.
  Distinguish G5a proposal-based provisioning approval from G0-authorised actual post-provision parity/readiness checks and later stage-specific G5b canary/switch/forward/rollback approval. Missing actual replacement evidence blocks G5b, not otherwise approved G5a provisioning; G6 is independent.
  Separate synthetic procedure verification from target P1 release readiness and real G5 P2 acceptance; bind operational evidence to target/revisions and approved freshness/invalidation policy. SC-006 requires actual authorised readiness/switch/forward/rollback checks, not a tabletop.
- [X] T047 [US4] Extend only offline checks in `scripts/verify-llm-deployment-preflight.py` to satisfy T045 and document safe forward/failed-forward/rollback/no-approval tabletop results in new `specs/041-llm-deployment-routing/migration-rehearsal.md`; retain old resources and corrected image/config pair, require actual pool headroom rather than assume quota, and label synthetic outcomes distinctly from external G5 provisioning/switch and G6 deletion.
- [X] T048 [US4] Run T045 and the local tabletop in `specs/041-llm-deployment-routing/migration-rehearsal.md`, cross-check every FR-016 step in `specs/041-llm-deployment-routing/naming-migration.md`, and record SC-006 local procedure coverage in `specs/041-llm-deployment-routing/verification.md`; real replacement readiness, canary/switch/rollback and retirement remain separately pending approval, not passed by documentation tests.
  Label this as local implementation/procedure verification only; mark SC-006 operational acceptance pending/not executed until separately approved real target readiness, traffic switch and forward/rollback evidence exist. Neither this task nor synthetic success grants G4/G5/G6 authority.

**Checkpoint**: P2 procedure delivered independently of optional execution. P1 can retain existing explicit names indefinitely.

## Phase 7: Polish & Cross-Cutting Verification

**Purpose**: Consolidate only introduced/fixed behaviour, evidence and safe handover; do not broaden the feature.

<!-- parallel-group: 9 -->
- [X] T049 [P] Update `specs/041-llm-deployment-routing/quickstart.md` with exact new test/preflight commands, actual outcomes, fixture-only boundaries and blocked target gates; retain local-versus-authorised-Azure distinctions and explicitly prohibit strict-reader activation against old ambiguous maps or env-only updates to incompatible dispatchers.
- [X] T050 [P] Re-evaluate requirement-quality findings and task acceptance links in `specs/041-llm-deployment-routing/requirements-review.md` against CHK001–CHK036 after implementation; request reviewer remediation/acceptance where needed, never auto-check `checklists/routing-rollout.md` or alter the built-in `checklists/requirements.md` lifecycle, and distinguish quality approval from test/release evidence.

<!-- sequential -->
- [X] T051 Run focused routing/provenance/preflight/migration tests plus identified existing chat/SSE/simulation/embedding/eval/audit regressions and repository lint on touched files; consolidate FR-001–FR-016/SC-001–SC-007 evidence in `specs/041-llm-deployment-routing/verification.md`, marking any G1–G6-dependent acceptance as blocked/not executed and retaining zero historical modifications, no model change and zero unauthorised resource-operation assertions.
  Report local implementation/procedure verification, target P1 release readiness and real P2 operational migration acceptance separately; never turn synthetic SC-006 procedure coverage into an operational pass. G0/G4 authority and freshness/revision validity remain explicit external gates.
- [X] T052 Assemble the human review handover in `specs/041-llm-deployment-routing/rollout-evidence.md`: exact matched API/agents image and cleaned config references, reader/writer compatibility, safe rollback, outstanding G1–G6 approvals and stage-specific stop conditions; require independent target metadata/What-If/carve-out reviews and human release approval, and stop without deploying, switching, deleting or committing.
  Include G0 collection versus G4 release scopes, evidence policy/version and target/revision bindings, and the three separate acceptance levels with real P2/SC-006 pending where unexecuted. No handover claim changes operational authority.

## Dependencies & Execution Order

### Local task graph

```text
H0
 └─ T001 → T002 / H1 → T003 → T004 → T005 → T006 → T007 → T008
      ├─ US1: group 1 → T012 → T013 → T014 → group 2 → group 3 → T020 → T021
      ├─ US2: group 4
      │       ├─ T023 + T012 → T028 → T029 (offline lane)
      │       └─ G1+G2+G3 → T024 → T025 → T026 → T027 (gated IaC lane)
      │       Both lanes + T022 → T030
      └─ US3 (after US1): group 5 → group 6 → T036 → group 7 → group 8 → T043 → T044
US1 + US3 + US2 local T028/T029 → US4: T045 → T046 → T047 → T048
All selected local story work → group 9 → T051 → T052 → human review
US2 target evidence + US1 + US3 + G4 → separately authorised P1 release (not a task)
P1 + G5 → optional operational migration; G6 separately → optional retirement (neither a task)
```

- Phase 1 and foundation block all implementation stories. T002 must genuinely resolve H1; generating review tasks does not satisfy it.
- **US1** has no local dependency on target IaC and is the suggested local MVP.
- **US2** tests and offline preflight may proceed after foundation. T028 requires T023 plus US1's shared validator T012, **not** T024–T027; T029 follows T028. This offline lane need not wait for blocked Azure evidence. T030 requires T022–T029, G1–G3 and compiler-ready outputs. Its target comparison cannot pass with synthetic fixtures alone.
- **US3** uses completed US1 adapter seams. It can proceed while US2's gated authoring is blocked. T034/T035 readers and passing schema checks precede all new producers; each parallel group joins before the next group.
- **US4** documents/rehearses only after the local P1 contracts are available. Actual P1 release or optional migration readiness is not inferred from that rehearsal.
- **Final phase** follows all selected implementation/procedure tasks; a blocked US2 lane must stay explicitly blocked in final evidence rather than be ticked complete.
- Different stories are not blanket-parallel: shared source and evidence paths require scheduling. For a single fleet stream, use the numbered groups in order; only the explicitly independent US2 offline lane may be interleaved, with exclusive access to shared evidence files.

### Activation ordering (separate from local implementation)

1. Clear human review; obtain G0 scoped baseline/governance collection authority,
   reconcile G1–G3, then obtain explicit G0 target-validation scope to collect
   mandatory What-If/carve-out/metadata evidence for G4. Apply approved
   freshness/invalidation policy and exact target/revision bindings throughout.
2. Deploy compatible provenance readers before enabling optional producer fields.
3. Prepare cleaned output with old approved resource names, complete model metadata, embedding and unambiguous legacy/eval mappings.
4. Validate strict application images and exact cleaned env together in matched inactive API/agents candidates; neither strict-code-only nor env-only activation is safe.
5. Only G4 permits separately authorised canary/switch/post-switch verification. On failure retain the prior safe pair; never feed old conflicting CSV to strict code or restore known simulation-to-live misrouting.
6. G5 optional naming migration and G6 retirement remain independent later decisions. No application task authorises deployment resource operations.

## Parallel Execution Examples

All groups contain different write paths and at most three tasks. Tests may initially fail; join and evaluate that expected failure before implementation. Shared fixture T005 is complete before test fan-out.

| Group | Tasks | Prerequisite / independent outputs |
| --- | --- | --- |
| 1 — US1 tests | T009, T010, T011 | Foundation; unit resolver, client contract, map compatibility files |
| 2 — US1 adapters | T015, T016, T017 | T014; MAF factory, dispatcher, controller |
| 3 — US1 legacy consumers | T018, T019 | Group 2; eval parser versus ingest parser |
| 4 — US2 tests | T022, T023 | Foundation; compiled-output contract versus offline preflight cases |
| 5 — US3 tests | T031, T032, T033 | US1; schema, submission evidence, producer contract files |
| 6 — US3 readers | T034, T035 | Group 5; strict audit readers/schema versus invocation/reply readers |
| 7 — US3 producers | T037, T038, T039 | T036 and reader tests; common transport, mixin/telemetry, MAF middleware |
| 8 — US3 simulation provenance | T040, T041, T042 | Group 7; controller, dispatcher, API reply consumers |
| 9 — cross-cutting docs | T049, T050 | Selected story completion; quickstart versus requirements-review evidence |

**Per-story examples**:

- US1: launch T009/T010/T011 together; after sequential shared implementation, launch T015/T016/T017 together. Join before integration.
- US2: launch T022/T023 together; keep child → main → CSV → target parameters → generated ARM sequential and externally gated.
- US3: launch T031/T032/T033 together; join, prepare readers in group 6, then writer and bounded producer groups. Never overlap edits to factory/controller/dispatcher with their US1 tasks.
- US4: **no parallel tasks**; T045 → T046 → T047 → T048 is intentionally sequential because procedure, checker and rehearsal evidence depend on one another. Do not invent fan-out by splitting the same runbook.

## Requirement and Checklist Coverage

| Requirement / success criterion | Principal tasks and evidence |
| --- | --- |
| FR-001 / FR-002 | T006–T007, T009–T010, T022, T024–T027, T031–T044 |
| FR-003 / FR-005 | T022, T024–T027, T030; existing names retained, new-only purpose defaults |
| FR-004 / SC-005 | T023–T030, T051–T052; G1–G4 remain mandatory external evidence |
| FR-006 / FR-008 / SC-001 | T003, T009–T010, T012–T015, T020–T021; complete inventory, six permutations, request-boundary assertions |
| FR-007 / SC-002 | T009, T012, T016–T017, T020–T021; every simulation role, no live fallback |
| FR-009 / FR-010 / FR-011 / SC-003 | T009–T023, T026, T028–T030; raw conflicts, precedence, unambiguous legacy/embedding/eval and zero requests |
| FR-012 | T022–T030 plus G1/G4 live-property agreement; offline checks do not replace live evidence |
| FR-013 / FR-014 / FR-015 / SC-004 | T008, T031–T044; unknown/no-call/attempted/failed distinctions and reader-first compatibility |
| FR-016 / SC-006 | T045–T048 verify procedure/local branches only; SC-006 real migration acceptance needs separately approved actual target readiness/switch/forward/rollback evidence under G5; G6 retirement remains separate |
| SC-007 | T004, T020–T021, T031–T044, T051; chat/SSE/simulation contracts and byte-identical historical fixtures |
| CHK001–CHK014 | Actual T001/T002 review, T006–T019, T022–T044, reviewer re-evaluation T050 |
| CHK015–CHK028 | Inventory/evidence T003–T004, focused tests T009–T011/T020/T022–T023/T031–T033/T043/T045, T048/T051 |
| CHK029–CHK036 | T001/T002/T050, no-behaviour-drift tasks, T024–T030/T046–T052 and explicit H/G gates |

This mapping provides review/implementation coverage, not approval of any checklist item. All 36 existing risk-review items remain unchanged by Tasks generation. Review-discovered requirement changes require approval before implementation.

## Implementation Strategy

### MVP First — Local US1 Only

1. Obtain Tasks approval, complete actual requirements review/remediation and foundation.
2. Implement/test US1 locally with synthetic settings; preserve legacy and embedding consumers.
3. Stop and show routing/zero-call evidence. This is a local MVP, **not permission to release strict conflict rejection**.
4. A releasable P1 increment additionally needs US2 coordinated producer/config preparation, US3 compatible readers/provenance and all G4 approvals.

### Incremental Delivery

1. Complete review and shared contracts without dependency/model upgrades.
2. Prove routing locally; develop offline US2 tests/checker while external evidence is pending.
3. Prepare compatible US3 readers before producer changes; verify old and new surfaces together.
4. Once G1–G3 are cleared, implement only approved-baseline-preserving IaC and regenerate ARM. If blocked, report the lane as blocked, not completed.
5. Complete P2 documentation and synthetic rehearsal independently of optional resource migration.
6. Consolidate focused evidence, outstanding gates and rollback constraints; stop for human review. Any authorised release/migration is a separate operational session.

## Task Inventory and Completion Boundary

- **52 tasks**: setup 4; foundation 4; US1 13; US2 9; US3 14; US4 4; polish 4.
- **23 parallel-marked tasks** in **9 explicit groups**, maximum concurrency 3; **29 sequential tasks**. US4 is intentionally sequential.
- No missing design clarification is asserted. Current blockers are reviewer acceptance and execution evidence/approval gates, not requests to invent models, baselines or governance.
- Refinement preserves all 52 task IDs, 9 parallel groups and existing dependencies. Completion reporting separates local verification, target P1 readiness and real P2 migration acceptance; synthetic rehearsal does not satisfy SC-006.
- Generated now: this `tasks.md` only. Every future evidence/test/source path above is planned work, not a claim that it exists or has passed.

## Phase 8: Convergence

**Assessment scope**: Current implementation against all 52 original tasks, 16 functional requirements, 19 acceptance scenarios, six buildable success criteria, nine edge cases, four local-build obligations, the plan and applicable constitutional constraints. SC-006 real migration acceptance remains separately gated operational work. Existing task text and completion markers above are retained, not accepted as proof of implementation.

**Ordering and authority**: T053 is an offline routing correction. T054 and T055 require the applicable G1-G3 preservation/scope approvals before infrastructure authoring or compilation; the application-only Dev exception does not authorise Foundry writes. T056 requires genuine approval for each target. T057 depends on T054-T056 and their applicable gates. No task authorises deployment, traffic promotion, migration, inference-budget renewal, additional approver fabrication or a local AMD64 build.

- [X] T053 [US1] CRITICAL - Correct deployment-qualified AOAI endpoint shaping in `apps/agents/common/foundry_chat_client.py` so sync and streaming request URLs honour the frozen resolved tier rather than a conflicting deployment already embedded in the configured endpoint, per FR-006/FR-007, US1/AC1-US1/AC2, SC-001/SC-002 and T010/T013/T014 (contradicts).
  Evidence: `_endpoint_for` preserves any existing `/openai/deployments/` path. An installed-SDK reproduction with the existing synthetic transport and blocked network resolved/body-selected `synthetic-exercise-s` but submitted to `/openai/deployments/synthetic-live-r/chat/completions`; request evidence correctly remained unknown rather than proving the intended destination.
  Acceptance: Extend `tests/contract/test_llm_deployment_routing.py` and `tests/unit/test_llm_inference_attempt_evidence.py` to inspect actual sync/stream transport URLs for distinct reasoning, drafting and simulation tiers with deployment-qualified endpoints. Preserve matching-qualified and native Foundry endpoints, per-effective-endpoint caching, managed identity, gateway/retry semantics and truthful request-bound provenance; reject invalid required endpoint configuration before submission. Check the shared endpoint's MAF/controller boundaries for the same inconsistency and correct any demonstrated mismatch without changing their transports.
  Implementation, 2026-10-20: COMPLETE locally. Shared pure endpoint normalization in `apps/agents/common/llm_config.py` supplies the account endpoint to all resolved adapters; the common client builds/caches the selected per-deployment URL. Real SDK/HTTP transports cover all tiers, both AOAI host families, sync/stream, MAF, controller owning-writer admission and all six dispatcher roles; invalid endpoint configuration fails before client construction. Source, results and limits are recorded in `verification.md`. No image rebuild or deployment is claimed.

- [X] T054 [US2] HIGH - Resolve preservation of observed deployment `currentCapacity` and `deploymentState` through the approved composition in `infra/modules/azure-openai.bicep` and strengthen `tests/contract/test_llm_deployment_compiled.py`, per FR-004, US2/AC1/US2/AC3, SC-005, T024/T030 and plan: baseline-preserving AVM composition (partial).
  Evidence: `infra/modules/vendor/avm-cognitive-services-deployment-0.18.0/main.bicep` emits only model, RAI attachment and upgrade properties; the compiler test asserts that reduced set. `evidence/dev-preparation/corrected-validation-review.json` retains unresolved capacity/state omissions for all four deployments and does not establish that these exact-API inputs are read-only.
  Acceptance: Establish explicit supported preservation or documented, approved exact-API omission/default equivalence against the target baseline, including embedding. Use a verified compatible published AVM when available; otherwise stop for explicit scope approval rather than editing pinned vendor bytes or introducing an unauthorised resource/account rewrite. Compiler comparisons must expose unexplained baseline-field loss instead of accepting a reduced allowlist. Any later target metadata/What-If validation needs its own current G0 scope; no Foundry mutation is authorised.
  Historical pre-approval status, 2026-10-20: BLOCKED. Public registry tags include 0.19.1, but the reviewed 0.19.0/0.19.1 tagged deployment-child interfaces still expose neither field. Exact `2026-05-01` documentation does not prove safe omission.
  Implementation after explicit approval: COMPLETE for the approved Dev preservation scope. `infra/modules/cognitive-services-deployment-preservation.bicep` is first-party, not a modified/relabeled AVM. Required typed operating-state inputs pass through root/wrapper/Dev parameters to all four deployments independently of SKU. Complete mutable-property comparisons reject unexplained loss; Paused/zero and independent Running/capacity cases pass. Fresh baseline/governance/access comparison, actual ARM validation and all-four NoChange preview pass. Vendor hashes remain unchanged; no account write, deployment or other-target acceptance is claimed. See `convergence-preservation-review.json` and `verification.md`.

- [X] T055 [US2] HIGH - Resolve effective RAI `contentFilters.action` preservation in `infra/modules/azure-openai.bicep` and replace the action-stripping comparison in `tests/contract/test_llm_deployment_compiled.py`, per FR-004, US2/AC3, SC-005, T024/T030 and plan: unchanged protection baseline (partial).
  Evidence: The wrapper's `2024-10-01` RAI input shape omits the observed action field; the compiler test removes that field before comparing filters. `evidence/dev-preparation/corrected-validation-review.json` explicitly leaves the observed `NONE` versus newer-input `None` casing/default equivalence unresolved.
  Acceptance: Demonstrate and record approved exact-API effective-policy equivalence or implement a supported, explicitly scope-approved representation preserving complete filter semantics, base policy, mode, attachment and operation serialization. Tests must compare the complete approved semantics and fail on unexplained action loss or change; do not silently weaken filters, assume casing/default equivalence, upgrade resource APIs beyond approval or infer cloud-write authority.
  Historical pre-approval status, 2026-10-20: BLOCKED. Official `2026-05-01` input documentation exposes action `None`, while retained observations contain `NONE`; no omission/casing equivalence or approved API/representation change had been supplied.
  Implementation after explicit approval: COMPLETE for the approved Dev preservation scope. The narrow RAI representation uses `2026-05-01` and retains exact observed `NONE`, not a guessed `None` conversion. Complete policy/filter comparisons retain all action/source/severity/enabled/blocking fields, base and mode; exact compiled dependencies preserve the full operation chain. ARM validation succeeds and all three policy before/after payloads are identical NoChange with no unsupported/potential changes. System-managed base policies are not written. This is preview acceptance, not an executed policy update or release approval.

- [ ] T056 [US2] HIGH - Complete the remaining target-specific T027 parameters in `infra/parameters/staging.bicepparam` and `infra/parameters/production.bicepparam` only from each target's genuinely approved reconciled baseline and governance evidence, per FR-003/FR-004/FR-012, US2/AC2-US2/AC4, SC-005 and T027 (partial).
  Evidence: Both files still contain topology/environment/location/subscription/tags without the nine explicit tier deployment/model/version selections; existing T027 evidence is Dev-only.
  Acceptance: Bind all nine selections per target, compare SKU/capacity/state, upgrade behaviour, complete RAI/access/residency protections and embedding, and add only approved narrow preservation overrides if necessary. Missing G0 collection authority or G1-G3 evidence remains an explicit blocker; never copy Dev observations, invent approvals/models, replace existing deployments or provision resources to satisfy the checklist.
  Execution status, 2026-10-20: BLOCKED. The latest explicit decision says staging/production evidence is not supplied and both remain blocked. Neither has an approved baseline/governance bundle or scoped collection authority. Their parameter files remain untouched rather than filled with Dev selections.

- [ ] T057 [US2] HIGH - Complete T030 compiled per-target preservation and PSRule acceptance after T054-T056 and applicable target approvals, per FR-003/FR-004/FR-012, US2/AC1-US2/AC4, SC-005, T022/T023/T028/T030 and plan: target-bound validation evidence (partial).
  Evidence: T030 records Dev local build/contracts and explicit-Dev PSRule only; staging/production lack approved populated parameters, the full infrastructure scan remains blocked, and the retained Foundry preview still has unresolved preservation differences.
  Acceptance: Regenerate `infra/main.json` and `infra/modules/azure-openai.json` from approved Bicep, run the existing local compiler/preflight/PSRule checks against every approved target, and record exact target/proposal bindings and complete baseline comparisons in `specs/041-llm-deployment-routing/verification.md`. Require zero unexplained creates/renames/replacements/deletions or identity/SKU/capacity/state/RAI/access/residency/embedding changes; isolate and escalate unrelated root-template drift instead of applying it. Keep absent target approvals and G4 What-If/carve-out/live-metadata or release authority explicitly pending, never inferred from offline passes.
  Execution status, 2026-10-20: PARTIAL / BLOCKED by T056 and other-target approvals. The Dev portion now has regenerated root/wrapper ARM, exact artifact/compiler parity, 60 passing compiler/configuration cases, 797 PSRule passes with zero failures, fresh reconciled evidence and eight exact NoChange preview resources. T054/T055 preservation omissions are resolved for this candidate. Staging/production and full-infra/all-target acceptance remain unclaimed; unrelated root drift was not submitted. No release was executed.
