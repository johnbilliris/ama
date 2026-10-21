# Spec 032 Static Implementation Audit

**Review date:** 2026-09-14. **Revision:** `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a` (read-only Git metadata verified).
**Scope:** Only the obligations of spec 032, traced into their implementation dependencies.
**Coverage denominators:** 152 original tasks (82 `[X]`, 70 without a checkbox), 89 FRs, 10 SCs,
30 numbered acceptance scenarios, 9 edge cases, and 91 local checklist items.
**Audit disposition:** Static review complete; 36 open remediation tasks. Runtime/deployment/approval outcomes remain unverified.

## Review Boundary

The full [Review Contract](../001-spec-implementation-audit/README.md#L11), read at lines 1-59, and
[code-review instructions](../../.github/instructions/code-review.instructions.md#L1) govern this review.
The detailed review checklist, Bicep/security instructions, constitution, rubric, Python fact-grounding and Cosmos review guidance were consulted.
The rubric-grader skill was read for evidence discipline; no independent score was generated because this is an implementation audit, not a regrade.
No existing report was present in this folder. Other implementation review reports are not inputs.
Only this report may be written. Original sources, configuration, specifications, checkboxes, evidence, and indexes remain unchanged.
No tests, builds, verification scripts, application imports, models, servers, browsers, deployments, installations, cloud operations,
external approvals, branches, or commits are executed or created. Static source assertions do not establish runtime or deployed outcomes.
Read-only metadata, text inventories, link checks, and report editor diagnostics are permitted.

## Original Inputs Read Completely

[Specification](spec.md#L1), [tasks](tasks.md#L1), [plan](plan.md#L1), [research](research.md#L1),
[data model](data-model.md#L1), [quickstart](quickstart.md#L1), [analysis](analysis.md#L1),
[traceability](traceability.md#L1), [coverage tracker](coverage-phase-tracker.md#L1),
[session record](SESSION-STATUS-2026-04-30.md#L1), [Stream 2 deferral](STREAM-2-DEFERRAL.md#L1),
[identity deletion note](T008-fr-i05-status.md#L1), [rubric checklist](checklists/rubric.md#L1),
[quality checklist](checklists/requirements.md#L1), [OpenAPI delta](contracts/openapi-delta.yaml#L1),
[OTel contract](contracts/otel-attributes.yaml#L1), [jurisdiction schema](contracts/jurisdiction-policy.schema.yaml#L1),
and [signing contract](contracts/cosign-signing.yaml#L1): all 18 original local files, including amendments and deferrals.

The five ADRs were located under the corpus tree rather than declared missing at their historical paths.
The [OIDC ADR](../../docs/corpus/aidr/decisions/adr-032-oidc-supersession.md#L3) remains Proposed.
The [partitioning document](../../docs/architecture/cosmos-partitioning.md#L16) explicitly redirects to
[its authoritative replacement](../../docs/architecture/deployment/cosmos-partitioning.md#L1).
The [Foundry cutover ADR](../../docs/decisions/036-foundry-rag-grounding/20-hard-cutover-foundry-foundation.md#L1)
changes the AOAI-to-Foundry migration, not every future model-version canary obligation.

## Prioritized Findings

**P0: release/life-safety blockers.** Production network isolation is not composed (AUD-032-002);
governed agent controls and push propagation are absent (004, 005); the audit chain cannot block publication (008);
central log redaction is absent (009); deployment validation is not bound to the resources being deployed (015);
offline replay deletes updates before acknowledgement (032).

**P1: required correctness/security gaps.** Nonblocking quality and coverage gates (001, 019), unbound CMKs (003),
unconsumed governance policy (006), incomplete provenance (007), broken/unconsumed resilience and budget adapters (011, 012),
grounding/shadow/structured-output/signing/eval gaps (013-018), disabled SAST and mutable supply-chain inputs (020),
incomplete telemetry/retention/SLO/security monitoring (021-023), unproven DR/chaos/performance gates (024-026),
unreconciled rubric/approval claims (030), staged-auth/delivery gaps (031), and language fallback gaps (033).

**P2: maintainability and reviewer-delivery gaps.** Incomplete module relocation (010), inaccurate DORA publication (027),
unusable reviewer/runbook links (028), and architecture/capacity drift (029). Exact source evidence follows;
the open-task section supplies separate developer/tester directions for every finding.

### Production Network And Encryption Claims Are Not Composed

The deployed-template entrypoint is [azure.yaml](../../azure.yaml#L8), which selects the root Bicep module.
That module retains the Azure-services wildcard in [Cosmos firewall rules](../../infra/main.bicep#L146),
enables public access on [Storage](../../infra/main.bicep#L493) and [Cosmos](../../infra/main.bicep#L580),
and passes empty private-network inputs with public access enabled to [Search](../../infra/main.bicep#L302).
The [Content Safety call](../../infra/main.bicep#L453) supplies neither private endpoint wiring nor caller RBAC.
The standalone [DNS helper](../../infra/modules/private-endpoints.bicep#L33) and
[CMK key module](../../infra/modules/cosmos-cmk.bicep#L33) do not establish an enforced production posture:
the root does not import them or bind a Cosmos/Storage encryption key.
These contradict the completion claims for T401-T406; deployed state is independently UNVERIFIED.

Continuous seven-day backup is actually authored in [the Cosmos account](../../infra/main.bicep#L594).
It does not prove region failover: the same account declares only the primary region at line 589.

### Runtime Helpers Do Not Establish End-To-End Delivery

The [active LLM mixin](../../apps/agents/common/llm_mixin.py#L26) constructs the legacy breaker and keeps
a process-local monthly counter. The [new strategy module](../../apps/agents/common/llm_strategies.py#L16)
expressly describes itself as additive. Tracked-source caller searches found no production consumers of the new
strategy chain, budget factory, typed AIIMS registry, autonomy evaluator, or kill-switch watcher.
The [kill-switch watcher](../../apps/agents/common/lifecycle/killswitch.py#L107) is an injected local poll hook,
not a Service Bus subscriber, change-feed publisher, or handoff drain. The
[spike](../../docs/spikes/T016-killswitch-propagation.md#L5) explicitly defers measurement.

The [budget adapter](../../apps/agents/common/llm_budget_tracker.py#L139) catches arbitrary read/replace failures
and upserts a fresh increment, risking counter loss after conflicts. Its disconnected fallback also recreates
an in-memory tracker on each add. The [governance repository](../../apps/api/app/repositories/jurisdiction_governance_policy_repository.py#L51)
retains Cosmos `id` when passing documents to an extra-forbidding model, then swallows resulting read failures.

The [recommendation model](../../packages/domain/src/domain/models/recommendation.py#L7) lacks the required
provenance/segment/shadow fields. The registered [API router](../../apps/api/app/api/router.py#L56) does not
connect the specified integrity, why-fired, or governed lifecycle endpoints. Relocated Foundry retrieval and
audit helpers were considered; they do not supply a per-recommendation hash-chain publication gate.

### Release And Measurement Claims Exceed The Evidence

[Prompt signing](../../.github/workflows/prompts-publish.yml#L7) is manual-only, depends on a previous-commit
diff from a default shallow checkout, and persists signatures only on `push`, which cannot trigger it.
CD contains no prompt verifier. The [eval gate](../../.github/workflows/eval-pr-gate.yml#L3) is also manual-only;
missing configuration and an unset terminal verdict do not fail it. [CodeQL](../../.github/workflows/codeql.yml#L3)
is explicitly disabled. [Nightly load](../../.github/workflows/nightly-load.yml#L44) suppresses pytest failure.

All 5,000 rows of [the relocated dataset](../../packages/eval-dataset/data/dataset-disaster-core-1.0.0/cases.jsonl#L1)
were parsed as text: 5,000 distinct IDs, all synthetic, all labelled approved, but all case approval-chain actions
are `draft` and none is a safety-reviewer approval. The [manifest](../../packages/eval-dataset/data/dataset-disaster-core-1.0.0/manifest.json#L1)
is a generator publication claim, not independent approval or a measured scorecard. The size is supported;
the approved-dataset and baseline-outcome claims are not.

The [telemetry wrapper](../../apps/agents/common/otel_telemetry.py#L78) only forwards to an in-memory recorder.
The [DR workflow](../../.github/workflows/dr-drill.yml#L58) times the failover command, not the runbook's
first successful secondary-region operator workflow or the last durable write. The
[DORA collector](../../scripts/dora_metrics_publish.py#L93) mixes incidents across environments and counts
incidents rather than unique failed deployments. None of these sources proves the required outcome windows.

### Strict Typing Is Not A Blocking Full-Scope Gate

FR-Q01 requires blocking strict checks over apps, packages, and tests. T105 is marked `[X]`, but
the `python-type-strict` step in [CI](../../.github/workflows/ci.yml#L116) invokes `mypy --strict apps packages`
and explicitly continues on error. A type error can therefore leave this step nonblocking; the test tree is outside its command scope.
The local pre-commit hook likewise restricts its file pattern to apps and packages in
[pre-commit configuration](../../.pre-commit-config.yaml#L26). This is source evidence, not a claim that CI was run.

## Open Remediation Tasks

All commands below are **future-only**, for a separately authorized implementation/validation effort. None was executed here.
Python commands require the project's supported interpreter, installed app/package/dev dependencies, and isolated synthetic fixtures;
web commands require the locked pnpm workspace dependencies. Tests that need real Azure resources require separately approved staging
resources and identities and must not be substituted with mocks to claim deployed success. Proposed test additions belong in the
named existing homes; a proposed new path is explicitly labelled and is never linked as current evidence.

- [ ] AUD-032-001 Enforce blocking full-scope engineering quality gates

**P1; original:** T001, T101-T106, T1001-T1003; FR-Q01-Q04, US7.1/2/4, SC-008.
**Expected/actual/impact:** strict apps/packages/tests checks must block; [CI](../../.github/workflows/ci.yml#L116)
continues on errors, and [mypy configuration](../../pyproject.toml#L90) suppresses test errors. Agent telemetry imports
the forbidden API package at [the budget emitter](../../apps/agents/common/llm_budget_tracker.py#L199).
**Developer:** use the existing pyproject configuration (not a second mypy file); remove grace and test suppression, fix scoped
typing, move shared metric ports out of API ownership, and align local hook scope/version/exit semantics. Retain strict import boundaries.
**Tester:** extend [devops YAML fixtures](../../tests/devops/conftest.py#L11) and existing scoped type tests with one invalid
type per root, a forbidden agent-to-API import, and an unformatted file; a valid shared-port import must pass. Check PRs to all supported targets.
**Future:** `mypy --strict apps packages tests`, `lint-imports`, `ruff format --check apps tests packages`, then
`pre-commit run --all-files`; negative fixtures must fail, corrected roots must pass. Do not run auto-fixing hooks during this audit.
**Complete when:** all specified roots are blocking in CI/local checks and the forbidden dependency is removed without widening exceptions.

- [ ] AUD-032-002 Compose private networking for every production data plane

**P0; original:** T401, T403-T406, T416, T601; FR-S01, FR-C05, FR-AI01/06, US2.1, SC-003.
**Expected/actual/impact:** private-only production plus working internal clients conflicts with [Cosmos/Storage](../../infra/main.bicep#L493),
[Search parameters](../../infra/main.bicep#L302), and [Foundry](../../infra/main.bicep#L954); Content Safety is disabled publicly but lacks a usable private path.
**Developer:** wire VNet/subnets, service private endpoints and DNS groups into the actual root deployment; remove the Cosmos wildcard,
bind runtime egress/DNS and Content Safety endpoint/RBAC, and document environment exceptions. Preserve AU residency and the existing resource identities;
adapt to discovered policy and AVM conventions rather than assuming isolated raw modules are deployed. Coordinate with 003, 022, and 031.
**Tester:** extend [parameter tests](../../tests/devops/test_parameter_files.py#L1) and [CD tests](../../tests/devops/test_cd_workflow.py#L1)
to inspect root-to-child production composition, all five data planes, empty subnet/DNS inputs, and dev exceptions. Proposed public-network-probe workflow
must distinguish authenticated network rejection from generic unauthenticated 403s and pair every external probe with a successful internal workflow.
**Future:** after dependencies and approved private staging runners exist, `pytest tests/devops/test_parameter_files.py tests/devops/test_cd_workflow.py -q`;
then the separately approved probe workflow must record 100% public refusal and internal success with resource IDs and timestamps.
**Complete when:** root-composed production settings and evidence cover every plane; merely creating DNS zones or observing a failed request is insufficient.

- [ ] AUD-032-003 Bind Cosmos and Storage CMKs with recoverable key management

**P1; original:** T402, T403; FR-S05, CHK003, E-03 retention dependency.
**Expected/actual/impact:** [the CMK module](../../infra/modules/cosmos-cmk.bicep#L28) creates a key in an existing vault;
[root Cosmos](../../infra/main.bicep#L580) and Storage do not consume its URI or declare the required encryption identity.
**Developer:** compose Premium/HSM vault, private access, managed identities, crypto permissions, rotation and encryption bindings for both services.
Define key recovery/rotation sequencing and prevent key deletion from making backup restores unreadable. Keep service IDs stable; coordinate migration with 002/024.
**Tester:** extend [parameter tests](../../tests/devops/test_parameter_files.py#L1): production without key URI/identity/RBAC must fail;
both encrypted resources and a rotated-version scenario must remain resolvable; reject placeholder key IDs and public vault exposure.
**Future:** `pytest tests/devops/test_parameter_files.py -q`, followed only under separate authorization by key-rotation and restore verification
from the private staging network. Expected: continued decryption with current and retained backup keys, no service-side public fallback.
**Complete when:** both account encryption bindings and rotation/recovery controls are root-composed and verified separately from module authorship.

- [ ] AUD-032-004 Implement governed kill-switch and autonomy control contracts

**P0; original:** T409, T410, T707, T708; FR-AG02/05a, NN-1, OpenAPI control operations.
**Expected/actual/impact:** [agent routes](../../apps/api/app/api/routes/agents.py#L24) contain draft bridges, not lifecycle controls;
[the contract](contracts/openapi-delta.yaml#L70) has no autonomy POST and conflates proposer acceptance with missing-approval rejection.
**Developer:** reconcile contract semantics first; register read/status/propose/approve operations with Entra session, required scopes and
IncidentCommander/ExecutiveLeader RoleAuthority, closed justification taxonomy, bounded reason, expiry and distinct-identity production approval.
Use an idempotent transactional outbox for Cosmos audit plus push; do not claim distributed Cosmos/Service Bus atomicity from sequential calls.
**Tester:** extend [approval state-machine tests](../../tests/integration/test_approval_workflow_state_machine.py#L1) and
[governance contract tests](../../tests/contract/test_governance_assignment.py#L1): valid dev toggle, pending prod proposal, distinct approval,
401/403, same-actor rejection, cross-tenant request, invalid taxonomy, replayed approval, expired proposal, and outbox failure with no effective toggle.
**Future:** `pytest tests/integration/test_approval_workflow_state_machine.py tests/contract/test_governance_assignment.py -q` with synthetic JWT/claims fixtures;
expected: exact 202/401/403/409 contract behavior and durable audit correlation. Depends on 005/006/008.
**Complete when:** both controls enforce the same fail-closed policy at registered request entrypoints and effects cannot precede valid production approval.

- [ ] AUD-032-005 Wire push-based kill-switch propagation and safe handoff drain

**P0; original:** T016, T203, T704-T706; FR-AG05, US5.3, EC-06, SLO-7.
**Expected/actual/impact:** [the watcher](../../apps/agents/common/lifecycle/killswitch.py#L107) has only `poll_once`;
[startup](../../apps/agents/common/startup.py#L14) starts only a dead-letter poller, and [the spike](../../docs/spikes/T016-killswitch-propagation.md#L5) has no measurement.
**Developer:** provision the tenant/environment-scoped config and lease containers, change-feed publisher, Service Bus topic/subscriptions,
watcher startup/shutdown and bounded in-flight drain. Enforce version/expiry ordering, deduplication, restart reconciliation and explicit degraded UI/header/guidance.
Measure from committed operator change through every process's completed drain, not merely message receipt. Do not replace the normal push design with polling.
**Tester:** extend [lifecycle tests](../../tests/unit/test_spec032_agent_subpackages.py#L124): all agents/replicas, duplicate and out-of-order toggles,
expired toggles, lost subscription, restart, 31-second lag, long-running handoff, and publisher crash after durable write; template output must retain AWS meaning.
**Future:** `pytest tests/unit/test_spec032_agent_subpackages.py -q`; with separately approved staging bus/Cosmos, replay 100 toggles and record
zero missed states, P99 <=30 seconds and post-drain heartbeat. Depends on 004/008/021; measured SLO remains UNVERIFIED until records exist.
**Complete when:** every running agent consumes authorized toggles and safely drains, with operational notices and trustworthy latency evidence.

- [ ] AUD-032-006 Connect jurisdiction policies and typed AIIMS decisions safely

**P1; original:** T208, T409, T701-T703, T708; FR-P05, FR-AG02, E-04/E-10.
**Expected/actual/impact:** [repository reads](../../apps/api/app/repositories/jurisdiction_governance_policy_repository.py#L51)
pass Cosmos `id` to an extra-forbidding model; exceptions become no policy. [Autonomy detection](../../apps/agents/common/lifecycle/autonomy_eval.py#L84)
defaults unknown environments to high-autonomy dev. Only NSW/VIC/Commonwealth YAMLs exist and the loader has no deploy caller.
**Developer:** strip known Cosmos envelope fields explicitly, distinguish absence from corrupt/unavailable policy, version-check writes/effective dates,
provision the actual renamed container, and wire deployment/runtime policy lookups to every decision and registry override. Use safe unknown-environment behavior;
do not import API repositories from agents. Cover all nine jurisdiction codes, preserve NN-1 at every level, and never waive prod dual approval at `high`.
**Tester:** extend [policy tests](../../tests/unit/test_spec032_jurisdiction_and_rag.py#L61) and
[registry tests](../../tests/unit/test_spec032_llm_and_aiims.py#L122) with real Cosmos-shaped `id/_etag` documents, stale versions,
future `effective_from`, invalid language/role keys, all environments/jurisdictions, failed reads, and actual decision-gate consumers.
**Future:** `pytest tests/unit/test_spec032_jurisdiction_and_rag.py tests/unit/test_spec032_llm_and_aiims.py -q`;
expected: validated round trips, monotonic activation, auditable overrides and safe failure. Depends on 001/004/005.
**Complete when:** deployed policy reaches each agent's decisions, not just an injected unit-test callback.

- [ ] AUD-032-007 Carry recommendation provenance through storage and the why-fired UI

**P1; original:** T301, T302, T307, T308, T310, T604, T714; FR-AI02, FR-AG03, US1.1, SC-002.
**Expected/actual/impact:** [Recommendation](../../packages/domain/src/domain/models/recommendation.py#L7) lacks prompt version,
model version, governance snapshots and segment linkage; [the mixin result](../../apps/agents/common/llm_mixin.py#L171) drops these fields.
Later [inference audit records](../../apps/agents/common/audit.py#L150) are not an equivalent per-recommendation why-fired endpoint.
**Developer:** carry E-01/E-02 provenance from actual inference/fallback through domain serialization, repository, API and a why-fired panel.
Include signal trust hashes, threshold, persona/jurisdiction, approval transitions and segment hash; distinguish template output without inventing model fields.
Preserve old records through an explicit schema version/compatibility reader, and enforce tenant/role filtering. Coordinate 008/013/016/017.
**Tester:** extend [audit shape tests](../../tests/contract/test_audit_record_shape.py#L1),
[risk audit tests](../../tests/unit/test_risk_assessment_audit.py#L1) and existing web component/e2e suites with 50-event timelines,
multiple prompt/model versions, fallback, rejected/escalated approvals, unavailable sources, and cross-tenant lookup denial.
**Future:** `pytest tests/contract/test_audit_record_shape.py tests/unit/test_risk_assessment_audit.py -q`; future web tests must assert
displayed values against persisted records, then a separately recorded reviewer timing must meet <30 seconds.
**Complete when:** every recommendation's visible explanation is reconstructible from its original evidence, not recomputed metadata or a UI placeholder.

- [ ] AUD-032-008 Enforce tamper-evident audit segments and publication blocking

**P0; original:** T303-T306; US1.1/2, E-03, EC-01, SLO-5, SC-002.
**Expected/actual/impact:** [append-only repository](../../apps/api/app/repositories/audit_repository.py#L85) is not a cryptographic chain;
[the inference writer](../../apps/agents/common/audit.py#L104) logs instead of persisting when its differently named Cosmos environment is absent.
No searched runtime source implements `AuditSegment`, `segment_hash`, the integrity endpoint/job, or a tamper-triggered publication hold.
**Developer:** implement tenant/incident-scoped canonical hashing, 100-event/60-second sealing, previous-hash linkage, scheduled/on-demand verification,
durable quarantined windows and a publication interlock with Observer-Auditor paging. Bind the real audit persistence variables/containers and archive retention;
do not rewrite old evidence or silently reseed broken chains. Define deterministic concurrent seal and restore/replay semantics.
**Tester:** extend [append-only tests](../../tests/integration/test_audit_append_only.py#L1) and
[replay tests](../../tests/integration/test_audit_replay.py#L1): first segment, window/full seal, reordered/removed/edited entries,
concurrent writers, chain fork, storage outage, interleaved tenants, and restore continuity. A tampered affected window must block publish and page once.
**Future:** `pytest tests/integration/test_audit_append_only.py tests/integration/test_audit_replay.py -q` with synthetic storage fixtures;
then separately authorized staging sealing/restore checks. Expected: canonical hashes, no false healthy status on unreadable storage, scoped blocks.
**Complete when:** integrity decisions are connected to publication and durable evidence, not just returned by a standalone hash helper.

- [ ] AUD-032-009 Apply central deny-by-default log redaction and a canary validator

**P0; original:** T202, T209, T309; FR-O05, US1.3, US3.4, EC-05, CHK003/052.
**Expected/actual/impact:** [the classifier](../../apps/agents/common/safety/classification.py#L192) defaults unspecified classes to allow;
[request masking](../../apps/api/app/middleware/classifier_gateway.py#L35) covers a few routes, not all structured logging sinks.
No bounded search found the required periodic log-canary scan. Raw errors/records can be logged before sanitization.
**Developer:** put an allowlisted recursive record sanitizer at every service's log/export boundary, hash unknown sensitive fields with managed salt,
cover messages/arguments/exceptions/nested objects, and avoid exporting raw records via fallback logging. Provide the periodic canary scanner,
alert routing and redaction failure policy. Preserve useful safe correlation dimensions; classifier availability must not permit unsanitized output.
**Tester:** extend [API scrubber tests](../../apps/api/tests/test_pii_scrubber.py#L1), lifecycle classifier tests and logging fixtures with nested
PII, unknown keys, structured exceptions, TFN/email/name/location, Unicode and overlapping patterns; assert originals never appear in captured sinks.
**Future:** `pytest apps/api/tests/test_pii_scrubber.py tests/unit/test_spec032_agent_subpackages.py -q`;
approved log-canary execution must detect planted synthetic PII and alert, with no production PII used as a fixture.
**Complete when:** all log-emitting services use the sanitizer and scanner failures cannot yield a false clean result. Depends on 021/022.

- [ ] AUD-032-010 Finish the common-module relocation with compatibility shims

**P2; original:** T201-T204; FR-A05, FR-Q05, US7 independent test.
**Expected/actual/impact:** [resilience](../../apps/agents/common/resilience/__init__.py#L14),
[safety](../../apps/agents/common/safety/__init__.py#L9), and [lifecycle](../../apps/agents/common/lifecycle/__init__.py#L10)
re-export implementations that remain flat; the full inventory finds 31 Python files directly under common.
**Developer:** move behavior to the appropriate subpackages in a behavior-preserving change, leave old imports as explicit compatibility shims,
fix package/distribution discovery, and update imports without coupling agents to API. Separate the behavioral changes in 011/012/014 from pure moves.
**Tester:** extend [subpackage tests](../../tests/unit/test_spec032_agent_subpackages.py#L1) to enumerate intended modules,
old/new symbol identity, import cycles and installed-package discovery; retain existing retry, dead-letter and content-safety assertions.
**Future:** `pytest tests/unit/test_spec032_agent_subpackages.py tests/integration/test_handoff_retry.py -q`, followed by the canonical unit/integration
suite after dependencies are installed. Expected: old and new imports expose identical behavior and actual implementations live in the new homes.
**Complete when:** the flat layer is compatibility-only and no behavior change is hidden in the relocation.

- [ ] AUD-032-011 Integrate strategy fallback and repair the maintained-breaker adapter

**P1; original:** T013, T205, T206; FR-P01/P03, EC-02, NN-5.
**Expected/actual/impact:** [mixin](../../apps/agents/common/llm_mixin.py#L26) never consumes the new strategy/breaker;
[adapter can_execute](../../apps/agents/common/resilience/pybreaker_adapter.py#L122) only reads state, so an open pybreaker
is not given its post-timeout trial call. Its only adapter test forces the library to be absent.
**Developer:** connect primary/secondary/template strategies to actual callers with one maintained breaker lifecycle, a bounded half-open trial and
correct success/failure accounting. Retain response shape, content checks, timeout limits and confidence reduction; prohibit production silent legacy fallback.
Keep the ADR truthful about the existing legacy half-open implementation. Coordinate 010/017 and shared telemetry in 021.
**Tester:** extend [breaker contracts](../../tests/contract/test_llm_circuit_breaker.py#L1) and
[strategy tests](../../tests/unit/test_spec032_llm_and_aiims.py#L25) with installed-library open/timeout/half-open/recovery,
concurrent trial, primary failure/secondary success, all-model failure/template, unsafe output and cancellation. Assert real caller selection.
**Future:** `pytest tests/contract/test_llm_circuit_breaker.py tests/unit/test_spec032_llm_and_aiims.py tests/contract/test_llm_fallback.py -q`;
expected: bounded recovery and retained AWS-safe template behavior, not only mock chain success.
**Complete when:** production callers use the strategies and recover through the maintained library without a permanent-open gate.

- [ ] AUD-032-012 Make budget accounting durable atomic and decision-enforcing

**P1; original:** T207, T511, T512, T812; FR-P02, FR-O03, US4.3, E-07, SLO-6.
**Expected/actual/impact:** [mixin accounting](../../apps/agents/common/llm_mixin.py#L35) resets on restart and only logs over budget;
[Cosmos add](../../apps/agents/common/llm_budget_tracker.py#L132) can reset totals on any exception and recreates fallback memory for each add.
**Developer:** connect a shared durable counter with atomic increments or bounded ETag retry, distinguish 404/409/412/429/transient failures,
provision its container and scope/period keys, and persist threshold events exactly once. Reconcile daily/monthly/incident budget units and currency;
implement 80% warning plus graceful degradation and a published hard-cap policy without bypassing life-safety templates. Never reset a counter on write failure.
**Tester:** extend [budget tests](../../tests/unit/test_spec032_llm_and_aiims.py#L77): 79.9/80/100%, concurrent adds, 412/429,
two instances/restart, UTC period rollover, negative input, missing store and repeated warning delivery; assert totals and unique durable events.
**Future:** `pytest tests/unit/test_spec032_llm_and_aiims.py -q`; separately approved Cosmos integration must show no lost increments/restart reset
and correct `llm.budget.warning`/cost customMetrics. Depends on 001/003/021.
**Complete when:** the production decision path resumes accurate durable totals and enforces its published thresholds.

- [ ] AUD-032-013 Complete licensed grounding and citations on actual inference entrypoints

**P1; original:** T015, T029, T302, T406, T601-T604; FR-AI01, US4.1, R-03, E-02, CHK006/042/058.
**Expected/actual/impact:** newer [hybrid retrieval](../../apps/agents/common/retrieval_client.py#L846) exists, but the deployed
[dispatcher](../../apps/agents/dispatcher/agent.py#L215) calls the SDK directly and returns empty citations. All nine AIDR sources are metadata-only;
[licence filtering](../../apps/ingest-runner/src/ama_ingest/licence_filter.py#L33) defaults a missing mode to full-text and does not verify sign-offs.
**Developer:** use the existing shared retrieval builder at every grounded entrypoint, enforce the authoritative per-handbook approval state at ingestion,
default absent/revoked rights to metadata/excluded, and persist source/page/chunk identifiers through recommendation rendering.
Preserve accepted 3072-dimensional Foundry corpus evolution; reconcile the older 1536/index-name contract explicitly rather than restoring obsolete clients.
Fix the [capacity alert](../../infra/modules/ai-search.bicep#L166), which compares SearchLatency with a percentage; wire a true storage-capacity alert.
**Tester:** extend [retrieval contracts](../../tests/contract/test_retrieval_service.py#L1),
[licence-mode integration](../../tests/integration/test_licence_mode_partition.py#L1) and citation UI tests: approved full-text, pending/unknown/revoked
licence, metadata-only, empty result, 503, exact quote/page/source, malformed score, actual dispatcher caller and capacity units.
**Future:** `pytest tests/contract/test_retrieval_service.py tests/integration/test_licence_mode_partition.py -q`;
after approved private staging setup, record retrieval P95 <=400 ms and verify citations against indexed approved source text.
**Complete when:** no caller or missing metadata can bypass the licence/network/grounding contract; authoring approval names is not sign-off. Depends on 002/007/021.

- [ ] AUD-032-014 Resolve and enforce the deny-by-default shadow-model boundary

**P1; original:** T012, T019, T209, T608; FR-AI03, US4.4, E-01/E-06, NN-2.
**Expected/actual/impact:** no runtime Phi shadow writer was found in the full apps/packages search;
[current registry](../../infra/parameters/foundry-carveout.yaml#L22) contains no Phi and the validator now permits only AU deployments.
[New gateway](../../apps/agents/common/model_gateway.py#L208) permits clean/unrecognised text and bypasses classification for AU regions;
the earlier taxonomy covers more content than its regex implementation. No explicit Phi retirement evidence was found.
**Developer:** obtain an explicit scope decision on Phi versus the newer AU-only policy, without broadening NN-2. If retained, implement
asynchronous shadow routing after classification and approved deployment lookup, deny ambiguous/sensitive payloads, do not fall through to another non-AU model,
store parent-linked `shadow=true` outputs in AU for seven years, and suppress them in every operator query/UI/export. Enforce override approval and expiry.
**Tester:** extend [classification tests](../../tests/unit/test_spec032_agent_subpackages.py#L33) and
[model gateway tests](../../tests/contract/test_no_openai_imports.py#L1) with PSPF variants, names/identifiers, cultural/operational data,
classifier failure, absent carve-out, expired override, benign prompt, divergent shadow result and UI suppression.
**Future:** `pytest tests/unit/test_spec032_agent_subpackages.py tests/contract/test_no_openai_imports.py -q` plus proposed shadow integration tests
under the existing integration tier; expected: zero forbidden calls and no user-facing dependency on shadow availability. Depends on 009/015/018.
**Complete when:** an explicit approved scope and connected fail-closed path exist, with durable comparison evidence rather than a shadow-labelled helper.

- [ ] AUD-032-015 Bind deployment carve-out validation to actual planned resources

**P0; original:** T017, T018, T412; FR-AI03a, NN-2, CHK066.
**Expected/actual/impact:** [CD](../../.github/workflows/cd.yml#L224) supplies only RegistryPath/Strict, never a planned resource inventory;
[validator](../../scripts/verify-carveout.ps1#L124) makes resource comparison optional, does not load the JSON schema/OPA, and compares deployment names
with model names. [Actual deployments](../../infra/modules/azure-openai.bicep#L178) use gpt-5.4 absent from the registry.
**Developer:** validate the schema, distinct real approvers, environment quorum, review expiry and prospective model/version/region coordinates before provisioning.
Use consistent ARM shape/model metadata and require a nonempty inventory; align the stricter AU policy with 014's explicit decision. Wire OPA or remove misleading claims
after documenting one authoritative validator. Fail closed on unavailable inventory, parse errors and unknown resources; no live mutation during review.
**Tester:** extend [carve-out security tests](../../tests/security/test_foundry_carveout.py#L1): empty planned inventory, unregistered model,
deployment alias different from model, duplicate approvers, yesterday/today expiry, missing fields, non-AU and malformed nested ARM records.
Replace the stale valid-case fixture expecting eastus/2030 success; inspect subprocess exit status, not just logged warnings.
**Future:** `pytest tests/security/test_foundry_carveout.py tests/devops/test_foundry_carveout_workflow.py -q` with synthetic plan JSON;
expected: a valid exact match passes and every invalid inventory fails before deployment. Depends on 014/031.
**Complete when:** the deployment entrypoint cannot provision a model merely because a different registry document is well formed.

- [ ] AUD-032-016 Publish consumable signed prompts and verify them before deployment

**P1; original:** T014, T028, T411, T605-T607; FR-AI05/09, E-09, signing contract.
**Expected/actual/impact:** [prompt library](../../packages/prompts/README.md#L7) is a layout/loader example only;
[signing workflow](../../.github/workflows/prompts-publish.yml#L7) is manual, shallow-diff dependent, and cannot persist signatures under its push-only condition.
[Manifest verification](../../packages/prompts/cosign.manifest.yaml#L17) is not called by CD and omits certificate/bundle arguments.
**Developer:** version actual templates and rendered-prompt hashes, pin ownership/review cadence, migrate callers from inline text, and sign immutable
release artifacts for the exact validated commit. Persist certificate/signature/bundle; verify exact producer identity, issuer, digest and revocation before deploy.
Do not treat the signing manifest itself as the prompt payload. Reconcile bypass approver roles across ADR/manifest/decision-rights, with one-shot audited expiry.
**Tester:** extend [CD tests](../../tests/devops/test_cd_workflow.py#L1) and existing LLM tests with unchanged prompts, multiple changed commits,
missing signature, altered bytes, wrong issuer/identity/branch, revoked identity, expired review and emergency bypass replay.
**Future:** `pytest tests/devops/test_cd_workflow.py tests/unit/test_spec032_llm_and_aiims.py -q`;
later isolated signing/verification with cosign installed must reject altered or unsigned artifacts and bind accepted prompts to the release SHA.
**Complete when:** runtime consumers load the signed/versioned artifacts and deployment cannot skip verification. Depends on 007/015/031.

- [ ] AUD-032-017 Require structured output across direct and forwarded fallback calls

**P1; original:** T609; FR-AI04, US4 independent test, CHK020.
**Expected/actual/impact:** all seven inspected production calls omit response_model: translator twice, risk agent three times,
[evacuation callback](../../apps/agents/evacuation/pipeline.py#L889), and [resource callback](../../apps/agents/resource_allocation/pipeline.py#L786).
The [mixin](../../apps/agents/common/llm_mixin.py#L134) only validates when a model is provided.
**Developer:** define response envelopes matching each actual operation, make production validation nonoptional, thread types through injected callbacks,
and preserve user-facing text and fallback semantics. Validate before accepting a response; handle malformed JSON, schema errors and token trimming safely.
Add a caller-aware gate including wrappers/aliases; do not waive free-text summary calls without an explicit requirement amendment.
**Tester:** extend [fallback contracts](../../tests/contract/test_llm_fallback.py#L1) and
[LLM integration](../../tests/integration/test_llm_integration.py#L1): valid envelope, malformed/empty JSON, wrong types, missing fields,
extra prohibited fields, truncation and no supplied schema; verify deterministic fallback and human-review flags.
**Future:** `pytest tests/contract/test_llm_fallback.py tests/integration/test_llm_integration.py -q`;
expected: every discovered production call supplies/enforces a schema and invalid responses cannot appear as accepted LLM output.
**Complete when:** direct and forwarded entrypoints are enforced, not merely found by a name-only scan. Depends on 011/016.

- [ ] AUD-032-018 Establish approved eval data and a fail-closed release scorecard

**P1; original:** T006, T610, T611, T909; FR-I01/02, FR-T09, SC-005, E-06, US4.2.
**Expected/actual/impact:** 5,000 stored unique cases exist but zero carry safety-reviewer approval; [manifest](../../packages/eval-dataset/data/dataset-disaster-core-1.0.0/manifest.json#L146)
credits cli-generator. [Runner](../../apps/eval-runner/src/ama_eval/runner.py#L157) returns success without gate evaluation;
[gate helper](../../apps/eval-runner/src/ama_eval/gate.py#L75) skips absent metrics; workflow can skip configuration or terminal verdict.
**Developer:** preserve existing published artifacts, publish corrections as a new governed version with authentic case/version approvals, resolve the
5,000-versus-subset and spec-030 English-only conflicts, bind scorecard to commit/dataset hash/model/metric versions, and evaluate mandatory metrics/baseline
before setting release success. Make PR/promotion triggers blocking, correlate the exact job execution, fail timeout/cancel/missing artifacts, and audit bounded eval bypass.
**Tester:** extend [gate tests](../../tests/unit/eval/test_phase5_6_modules.py#L142) and
[orchestrator tests](../../tests/unit/eval/test_orchestrator_e2e.py#L89), adding explicit IDs for all 14 spec-030 acceptance scenarios.
Fixtures: approved/unapproved cases, missing/NaN metrics, per-model regressions, stale baseline, all-failed/partial runs, cancel, timeout and replayed bypass.
**Future:** `pytest tests/unit/eval -q` plus dataset generator assertion homes under packages/eval-dataset/tests;
only later authorized full-model runs can establish the 5,000-case baseline outcome. Expected: no partial/unapproved/uncorrelated scorecard passes release.
**Complete when:** dataset governance, runner verdict and both release surfaces enforce one reproducible scorecard; a status label or fake Foundry test is insufficient.

- [ ] AUD-032-019 Implement all-tier branch-aware coverage ratcheting

**P1; original:** T107, T1004; FR-T01, US7.3, SC-008, coverage-phase tracker.
**Expected/actual/impact:** [CI](../../.github/workflows/ci.yml#L132) combines contract/integration, skips unit, and checks the combined XML as unit;
[ratchet](../../scripts/coverage-ratchet.ps1#L45) succeeds with no XML, starts Phase A at zero, accepts a 0.5-point regression and has no CI-restored prior artifact.
**Developer:** produce separate per-tier XML over apps/packages, fetch the previous successful run on the same branch and tier, persist baselines only on
success, reject missing/malformed metrics, and implement exact approved A/B/C activation. Bind one-PR incident bypass to two approvals and immutable audit.
Do not silently advance floors or retrofit reported historical measurements; preserve 63/40/49 and 80/60/50 intent until explicitly amended.
**Tester:** extend [devops fixture home](../../tests/devops/conftest.py#L11) with synthetic Cobertura and prior-run records:
equal/increased coverage, 0.1-point regression, wrong branch/tier, missing XML, first-ever branch, failed prior run, each floor boundary and reused bypass.
**Future:** proposed tests in tests/devops followed by `pytest tests/unit --cov=apps --cov=packages --cov-report=xml:coverage-unit.xml` and
equivalent integration/contract commands with the active phase's threshold; expected: each independent tier enforces the correct baseline.
**Complete when:** missing data cannot pass and all three branch-scoped ratchets are blocking, with activation evidence distinct from authored tracker entries.

- [ ] AUD-032-020 Restore SAST and immutable workflow and image inputs

**P1; original:** T005, T108-T110, T813; FR-S03, FR-T04, FR-C03, FR-D02, US2.3/4, SC-008.
**Expected/actual/impact:** [CodeQL](../../.github/workflows/codeql.yml#L3) is disabled/manual-only; 20 of 112 active action refs use tags;
all ten Dockerfile FROM instructions use mutable tags. [Dependabot](../../.github/dependabot.yml#L6) covers four Dockerfiles, not ingest-runner/web.
**Developer:** restore supported-language PR SAST with an explicitly documented Bicep/PowerShell scanner, preserve secret/PSRule/Trivy gates,
pin every active action to verified 40-hex commit and every deployed base image to digest, and add complete update coverage plus a no-new-tags gate.
If CodeQL entitlement is unavailable, record the blocker and seek a separately approved equivalent, not a green echo. Define security-bypass co-approval/expiry/audit.
**Tester:** extend [workflow tests](../../tests/devops/test_cd_workflow.py#L1) and [security tier](../../tests/security/test_foundry_carveout.py#L1)
with all 25 workflows/six Dockerfiles: new tag, local action, SHA, nested action, disabled scan, seeded secret, vulnerable fixture and bypass replay.
**Future:** `pytest tests/devops -q` plus future authorized scanner runs on deliberately vulnerable synthetic fixtures;
expected: real findings fail, supported clean fixtures pass, no entitlement gap is reported as successful analysis.
**Complete when:** complete inventories are pinned and updateable, SAST runs on PRs, and each security exception is bounded and evidenced.

- [ ] AUD-032-021 Export complete cross-service traces and reconcile every custom metric

**P1; original:** T026, T501-T504, T511, T512, T706; FR-O02/03/07, US3.1/4, OTel/E-07 contract.
**Expected/actual/impact:** API/MAF exporter setup exists, but [new retrieval/inference spans](../../apps/agents/common/otel_telemetry.py#L78)
never reach a real tracer; the [generic emitter](../../apps/api/app/observability/metrics.py#L46) is not a MetricDefinition registry.
The complete creation/emission inventory includes communication, monitoring, evacuation, resource, risk, ingestion, help/evidence and eval metrics absent from the catalogue.
**Developer:** use one shared telemetry port per service, real context extraction/injection across HTTP/bus/async hops, contract-required resource/span/LLM/handoff fields,
actual token/cost samples, and safe error/exporter fallback. Register metric kind/unit/dimensions/retention and bind aliases intentionally.
Include web and eval-runner startup; avoid API imports from agents, unbounded dimensions and sum-of-gauge ambiguity.
**Tester:** extend [OTel integration](../../tests/integration/test_otel_retrieval_span.py#L1) with an SDK in-memory exporter, not only OtelRecorder;
assert one trace parent tree across services, error/cancel/retry spans, model/prompt attributes, cost at 80%, no PII and no duplicate bootstraps.
**Future:** `pytest tests/integration/test_otel_retrieval_span.py -q` plus authored registry completeness tests;
later authorized exporter smoke must produce queryable traces/customMetrics without fabricated telemetry.
**Complete when:** complete metric inventory reconciles to the catalogue and real exported spans satisfy the contract. Depends on 001/009/012/022.

- [ ] AUD-032-022 Compose retention SLO alerts synthetics and complete Workbooks

**P1; original:** T025, T505-T510; FR-O01/04/06/08/09/10, SC-004/009, US3.2/3.
**Expected/actual/impact:** [monitoring](../../infra/modules/monitoring.bicep#L21) applies one 90-day retention and generic alerts;
the two [Workbook templates](../../infra/modules/workbooks/executive-governance.json#L4) are unbound and incomplete;
[synthetic locations](../../infra/modules/availability-tests.bicep#L28) include San Jose. Percentiles of `Sum/Count` do not establish event-level tail latency.
**Developer:** bind audit/eval 2555-day, security 365-day, operational 90-day policies; connect SLO burn calculations, P1-P5 routing/issue action,
both required endpoints and five approved AU/APAC locations, and executive/ingestion/agent-DLQ/LLM/operator-workflow tiles.
Reconcile rolling request-based versus time-based budgets, MTTD/MTTP clocks and zero-volume behavior; use correct weighted/sample latency semantics.
**Tester:** extend [monitoring Bicep tests](../../tests/devops/test_observability_alerts_bicep.py#L1): all root imports, retention fields,
geo list, 50% burn, zero samples, burst latency, issue+webhook routing, P1 integrity break, notification retry and missing tile sources.
**Future:** `pytest tests/devops/test_observability_alerts_bicep.py -q`; only later approved monitoring windows can demonstrate seven green days,
30-day 99.9/99.5% SLOs, detection <5 minutes and page <2 minutes after detection.
**Complete when:** configured data sources/alerts/retention support every tile and outcome records substantiate the SLOs; templates alone are PARTIAL.

- [ ] AUD-032-023 Integrate Defender Sentinel and required diagnostic feeds

**P1; original:** T407, T408; FR-S04, US2 security posture.
**Expected/actual/impact:** [Defender](../../infra/modules/defender.bicep#L6) and
[Sentinel](../../infra/modules/sentinel.bicep#L36) are standalone modules not invoked by the actual root/CD path;
two analytics queries do not supply diagnostic connectors, policy assignments or notification routing.
**Developer:** choose the correct subscription/resource-group composition, bind approved pricing/policy scopes, workspace connectors and required diagnostic
categories, then route KeyVaultAnomalousAccess/CosmosFirewallChange to the security responders. Validate rule IDs/types and retain least privilege,
AU telemetry residency and deployment idempotency. Treat unavailable cloud permission/entitlement as a blocker, not evidence of enablement.
**Tester:** extend [monitoring tests](../../tests/devops/test_observability_alerts_bicep.py#L1) with root reachability,
subscription-scope wiring, both query inputs, negative missing connectors and synthetic denied-key/firewall-change events.
**Future:** `pytest tests/devops/test_observability_alerts_bicep.py -q`; separately approved staging security-event injection must arrive at
the configured rule and responder with the source event ID. Depends on 002/003/022.
**Complete when:** the composed posture and data path exist; actual enabled state remains unverified until authoritative deployment evidence is supplied.

- [ ] AUD-032-024 Make DR and backup procedures match recoverable infrastructure

**P1; original:** T808-T810, T818; FR-D01/D04, SC-006, US6.3, EC-01.
**Expected/actual/impact:** seven-day backup is present, but [Cosmos](../../infra/main.bicep#L589) has one region;
[DR runbook](../../docs/operator-runbooks/dr-bcp.md#L56) assumes prewarmed secondary compute/front-door routing that is not composed.
[Drill](../../.github/workflows/dr-drill.yml#L58) times a CLI call, reuses the primary URL and never measures RPO; restore instructions reference a missing copy helper.
**Developer:** compose the secondary region/capacity/client routing, preserve audit continuity, and parameterize runbooks to real resource names.
Use authenticated operator transactions and timestamped durable sentinels for RTO/RPO. Bound drill targets to staging with explicit guards,
check native-command exits, verify fail-back and define restoration/reconciliation after partial failover. Do not widen Search residency.
**Tester:** extend [parameter tests](../../tests/devops/test_parameter_files.py#L1), [rollback tests](../../tests/devops/test_rollback_script.py#L1)
and replay tests: missing secondary, command failure, primary-only 200, delayed replica writes, >15-minute data loss, >60-minute operator recovery,
interrupted fail-back and duplicate ingestion. Confirm previously sealed audit segments remain valid.
**Future:** `pytest tests/devops/test_parameter_files.py tests/devops/test_rollback_script.py tests/integration/test_audit_replay.py -q`;
only a separately approved staging drill can prove RPO <=15 minutes/RTO <=60 minutes from defined clocks.
**Complete when:** runbook and composed recovery path agree and the drill records actual secondary workflow/data recovery rather than CLI elapsed time.

- [ ] AUD-032-025 Author fault-injection coverage and truthful exercise outcomes

**P1; original:** T030, T806, T807; FR-T03/R05/D05, SC-009/010, research R-14.
**Expected/actual/impact:** no tests/chaos tier was found; [experiment](../../infra/modules/chaos-studio.bicep#L91) restarts a target then
waits rather than throttling Cosmos, and is unbound. [Workflow](../../.github/workflows/chaos-quarterly.yml#L51) never fails a terminal Failed/Cancelled/timeout result.
Schedule prose conflicts across Apr/Oct, Jun/Dec, quarterly and monthly; day-of-month/day-of-week cron cannot be assumed to mean only first Sunday.
**Developer:** reconcile calendar/cancellation/ownership, add staged fault capability/RBAC and root wiring, implement the specified network/bus/Cosmos
faults, and make terminal status and SLO assertions authoritative. Create a proposed tests/chaos tier by reusing existing resilience fixtures,
not by relabelling an always-successful smoke. Publish raw time-series and lessons; never call a failed or unmeasured exercise completed.
**Tester:** reuse [retry integration](../../tests/integration/test_handoff_retry.py#L1) and
[breaker contracts](../../tests/contract/test_llm_circuit_breaker.py#L1): throttling, bus outage, failed/cancelled experiment, missing status URL,
timeout, missed toggle, audit failure and recovery. Assert stage-only boundaries and exact planned dates.
**Future:** after proposed tier exists, `pytest tests/chaos -q`; later separately approved rehearsals/drills must yield one full documented cycle,
including RPO/RTO and MTTD/MTTP records. Depends on 005/008/022/024.
**Complete when:** fault assertions are authored and scheduled execution produces genuine outcomes, with deferrals recorded and rescheduled within policy.

- [ ] AUD-032-026 Enforce benchmark regressions and run the real staging load harness

**P1; original:** T802, T803; FR-R01/R02, FR-T05, US6.1/2.
**Expected/actual/impact:** [benchmark session hook](../../tests/benchmark/conftest.py#L87) skips failure under CI;
[comparison](../../tests/benchmark/compare_benchmarks.py#L22) uses medians, not required per-test p95/memory.
[Nightly load](../../.github/workflows/nightly-load.yml#L44) suppresses pytest errors and never starts the Locust workload.
**Developer:** use environment-appropriate baselines with numeric p95 and memory limits, fail missing/incomparable results, and remove the CI bypass.
Run the actual staging load runner with explicit URL/auth, concurrency/duration and pass criteria, post measured latency/error/memory metrics,
and open regression issues on true verdicts. Reject production/arbitrary targets and do not report runner CPU as server resource use.
**Tester:** extend [benchmark helper tests](../../tests/benchmark/compare_benchmarks.py#L126) via the existing unit/devops homes and
[load threshold assertions](../../tests/load/assert_locust_thresholds.py#L1): below/equal/above p95+memory limits, missing baseline/output,
4xx/5xx, skipped tier, wrong target, telemetry unavailable, failed process and no traffic. Preserve real workload contracts.
**Future:** `pytest tests/benchmark -q --benchmark-json=.benchmarks/current.json` must fail a deliberate CI regression;
then a separately approved staging `locust -f tests/load/locustfile.py --headless` run with explicit load settings must produce asserted measurements.
**Complete when:** both benchmark and load verdicts fail closed and dashboards/issues consume measured results rather than an unconditional run counter.

- [ ] AUD-032-027 Correct environment-scoped DORA calculations and publish a dashboard

**P2; original:** T814, T816; FR-C04, US6.4, E-07.
**Expected/actual/impact:** [collector](../../scripts/dora_metrics_publish.py#L93) applies all incidents to each environment, can count several
failures for one deployment, and caps pagination at 500. [Workflow](../../.github/workflows/dora-metrics.yml#L7) is manual and the doc admits its Workbook is future work.
**Developer:** join immutable deployment identifiers/commits to environment-scoped incidents, count unique failed deployments, preserve complete pagination,
distinguish missing data from zero, and use correct gauge/histogram semantics. Restore the approved daily schedule and an actually bound four-metric dashboard;
handle API/export failure observably instead of publishing misleading zeros.
**Tester:** extend [DORA tests](../../tests/devops/test_dora_metrics_publish.py#L1): two environments, two incidents/one deployment,
one incident/multiple deployments, failed deployments, PR-labelled issues, >500 results, reopened/unresolved incidents and empty/error responses.
**Future:** `pytest tests/devops/test_dora_metrics_publish.py -q`; expected CFR stays in [0,1], MTTR never crosses environment boundaries,
and recorded daily metrics match fixtures; later dashboard evidence must show all four metrics for the requested month.
**Complete when:** calculation, scheduling, export and dashboard are connected and source provenance is visible.

- [ ] AUD-032-028 Complete reviewer navigation API docs and operational guides

**P2; original:** T002-T004, T010, T020, T811, T812, T817, T901-T908, T910, T1006;
FR-T02/06/08/10, FR-I03/04, FR-AG04, FR-AI07/08, FR-D03, FR-DOC01-DOC05, US8, SC-007.
**Expected/actual/impact:** [governance hub](../../docs/governance-hub/index.md#L9) has wrong relative links;
README has no video, canonical web API-docs route is absent, and [Playwright discovery](../../apps/web/playwright.config.cts#L4)
excludes the original operator spec, whose `<500` assertions accept 404. Contract-contributor guide and ingestion operations remain absent after relocation searches.
**Developer:** repair canonical nav/redirects without breaking existing hubs, link a real approved walkthrough, host the published OpenAPI at the
agreed route with compatible redirect, align live API schemas and hosted schema, correct Dependency Notifier path/count, and author usable contract/ingestion guides.
Update rollback/quota/cost docs to current model/metric surfaces; cross-link real survey outcomes (not blank templates). Reconcile local/CI test discovery.
**Tester:** extend [operator journey](../../apps/web/e2e/operator-journey.spec.ts#L9),
[Vitest home](../../apps/web/__tests__/smoke.test.tsx#L10) and existing web suites: actual nav clicks, 200 plus rendered API schema, no 404 pass,
keyboard/mobile/axe checks, five meaningful components, all runbook targets, stale redirects and author-owned links. Mark a proposed contributor guide as new.
**Future:** `pnpm --filter @ama/web test` and `pnpm --filter @ama/web exec playwright test --list` first prove discovery;
later authorized e2e/link checks plus a first-time reviewer timing must meet <60 seconds with zero broken links.
**Complete when:** every required reviewer/operator artifact works as authored; video availability and human time trials need actual records, not checklist assertions.

- [ ] AUD-032-029 Reconcile C4 capacity math scaling rules and all container budgets

**P2; original:** T021-T024, T804, T805; FR-A01-A04, FR-R03/R04, research R-12, architecture constraints.
**Expected/actual/impact:** C4 views and sequence exist but are not one configuration-generated model; [scale table](../../infra/main.bicep#L52)
claims per-agent rules absent from the shared [agents app](../../infra/main.bicep#L1180). Authoritative partitioning omits RU math;
legacy table totals/headroom and partition keys do not match active containers.
**Developer:** derive system/container/component and full-flow diagrams from a maintained model tied to actual root composition; label planned versus deployed
state. Inventory every root/imported/runtime-created Cosmos container and define workload/tenant/jurisdiction worst-case RU, caps and headroom with arithmetic.
Align CPU/HTTP/queue rules and service grouping without silently splitting containers or changing immutable partition keys; version any migration separately.
**Tester:** extend [parameter tests](../../tests/devops/test_parameter_files.py#L1) and architecture test homes with all container resources,
root/imported options, missing max caps, 9 simultaneous jurisdiction peaks, documented headroom formula, and diagram/model drift fixtures.
**Future:** `pytest tests/devops/test_parameter_files.py -q` plus proposed static model/inventory tests;
future benchmarks must verify capacity claims before these become operational sizing guarantees.
**Complete when:** all diagrams, budgets and actual scale rules agree, including dependent modules rather than only root examples.

- [ ] AUD-032-030 Reconcile scope traceability checklist and release evidence

**P1; original:** T006-T009, T801, T907-T909, T1005-T1010; FR-I01, FR-T07/09/10, SC-001/004-010, all review obligations.
**Expected/actual/impact:** 152 tasks/89 FRs exceed authored approximate counts; [rubric](../../AMA_Rubric_Asia.md#L55)
has 14 criterion rows but a 60-point scoring guide, while SC-001 claims 16/80. All 75 rubric-quality boxes remain open;
[traceability](traceability.md#L5) is a scaffold and complete-labelled stub tests are not completion. Spec 031 remains Draft.
**Developer:** reconcile binding versus deferred scope and rubric denominator with the owner, complete a real per-requirement/test/acceptance ledger for all
41 specification folders, and record every checklist disposition and design conflict. Preserve historical source/evidence; do not promote status, tag, claim approvals,
or inflate scores until criteria are satisfied. Attach verifiable commit/run/dataset/time-window evidence and human approvals where required.
**Tester/reviewer:** use this report's matrices as a closure checklist; inspect referenced assertions and discovery, reject guessed filenames, self-approved data,
empty suites and planned jobs. Validate each SC with its prescribed evidence window and persona, including independent regrade and review/deploy records.
**Future:** static ID/state/link validation of the final evidence package, then separately authorized canonical checks and independent human rubric review;
expected: no unmapped FR/task/scenario, no reused incident bypass, no unsupported Excellent claim, and traceable approvals before release.
**Complete when:** the approved denominator/scope and every closure claim are backed by genuine evidence; this task never authorizes retrospective checkbox edits.

- [ ] AUD-032-031 Complete staged OIDC and preserve model-version progressive delivery

**P1; original:** T007, T011, T413-T415, T801, T815, T819; FR-S02/S02a/S02b, FR-C01/02, FR-AI10, US2.2, EC-04.
**Expected/actual/impact:** [ADR-032](../../docs/corpus/aidr/decisions/adr-032-oidc-supersession.md#L5) is Proposed and allows temporary secret fallback;
[CD](../../.github/workflows/cd.yml#L81) still uses JSON credentials. No inspected seven-day prerequisite/rollout evidence exists.
[Delivery doc](../../docs/ci-cd/progressive-delivery.md#L19) lists gates not consumed by CD. Accepted Foundry hard cutover retires migration canaries only.
**Developer:** verify spec-031 merge/status/green-soak prerequisites, reconcile/approve ADR supersession with named approvers, then migrate dev/staging/prod
in order with distinct federated identities, actionable identity propagation preflight and no silent secret fallback. Preserve the simple pipeline and exact validated SHA.
Integrate immutable prompt/eval/candidate-model gates and rollback into that shape; do not revive the retired spec-029 footprint or treat index blue-green as model canary.
**Tester:** extend [CD tests](../../tests/devops/test_cd_workflow.py#L1) with missing subject/role, propagation error, wrong environment,
unapproved ADR, insufficient soak, missing signature/scorecard, regressing model and successful controlled canary. Inspect all auth workflows, not only CD.
**Future:** `pytest tests/devops/test_cd_workflow.py -q`; later approved isolated rollouts require seven-day dev and staging telemetry and
per-environment identity/rollback evidence. Depends on 015/016/018/020/022/030; external approval and soak are blockers, not tasks to execute in this audit.
**Complete when:** ordered migrations and model-version delivery gates are enforced and the prerequisite records support production readiness.

- [ ] AUD-032-032 Preserve offline updates until acknowledged replay succeeds

**P0; original:** EC-08, US5/US6 degraded-mode obligations, NN-5; cross-cutting work not given an original T ID.
**Expected/actual/impact:** [drainBatch](../../apps/web/src/lib/offline/queue-store.ts#L216) deletes entries before
[the field panel](../../apps/web/src/app/workspaces/[personaId]/_panels/field-coordinator-offline.tsx#L93) sends them; 4xx/5xx/network failure only increments a counter.
This loses field updates during the exact connectivity failure the spec must tolerate. Existing E2E tests call an evaluator, not the offline transport.
**Developer:** use peek/lease plus explicit acknowledgement or requeue semantics, preserve encrypted payload/persona/correlation/captured time,
implement bounded retry/conflict handling and cached COP behavior, and align the panel with the registered replay API and authorization.
Retain life-safety queue priority/capacity rules; do not clear user data or replace failed posts with successful local counters.
**Tester:** extend [queue-store tests](../../apps/web/tests/unit/spec_035/offline-queue-store.test.ts#L1) and
[offline replay contracts](../../apps/api/tests/contract/spec_035/test_offline_replay.py#L1): offline restart, interrupted batch, 401/409/429/500,
two tabs/personas, duplicate ACK, tampered payload, quota pressure and reconnect. Failed items must remain recoverable; one acknowledged event appears once.
**Future:** `pnpm --filter @ama/web exec vitest run tests/unit/spec_035/offline-queue-store.test.ts` and
`pytest apps/api/tests/contract/spec_035/test_offline_replay.py -q`; later browser tests must actually disconnect/reconnect with queued changes.
**Complete when:** no failed send destroys an unacknowledged update and the displayed COP/queue state is truthful. Depends on 004/008/028.

- [ ] AUD-032-033 Implement auditable jurisdiction-aware multilingual fallback

**P1; original:** EC-09, E-04 language priorities, US4 PIO/US5 cross-jurisdiction constraints; no dedicated original T ID.
**Expected/actual/impact:** [language resolver](../../apps/web/src/lib/i18n/language-packs.ts#L153) returns one available variant,
and all ATSI fallback chains end in English; [draft bridge](../../apps/api/app/api/routes/agents.py#L190) labels English carriers as pending translations.
That is not English plus the closest configured approved language with a PIO gap notice.
**Developer:** use ordered jurisdiction priorities and cultural-authority approvals to select a real permitted alternative, always retain English,
flag the unavailable requested asset and notify the PIO. Do not invent Indigenous translations or publish placeholder carrier text as translated content.
Define safe hold/escalation when no approved alternative exists and reconcile that edge with the binding publication requirement explicitly.
**Tester:** extend [language tests](../../apps/web/tests/unit/spec_035/language-packs.test.ts#L1) and existing communication fixtures:
requested approved asset, absent/unapproved asset, English+approved alternative, cross-jurisdiction priority, no alternative, mixed-script tags and duplicate languages.
Assert source/approval identity, AWS severity/action fidelity and PIO notice; never infer permission from a language label.
**Future:** `pnpm --filter @ama/web exec vitest run tests/unit/spec_035/language-packs.test.ts` plus communication contract tests;
later cultural/language reviewer acceptance must substantiate released content. Depends on 006/009/028/030.
**Complete when:** the operator and public outputs follow an approved, auditable bilingual fallback rather than silently substituting English.

- [ ] AUD-032-034 Materialize the Saga state model and distinct handoff timeouts

**P1; original:** T311, T709, T711; FR-P04, FR-AG06/08, US5 independent test.
**Expected/actual/impact:** [MAF workflow](../../apps/agents/maf_runtime/workflow/builder.py#L89) reaches a HITL pause but does not
generate the full state graph/recovery loops; [HandoffStep](../../packages/domain/src/domain/models/handoff_chain.py#L22) has no timeout.
The referenced Saga/Process Manager document and state renderer are absent after bounded replacement searches.
**Developer:** use one explicit state/transition configuration for approval, rejection, escalation, execution, timeout, dead-letter, recovery and lessons;
render stateDiagram-v2 and name the Saga/Process Manager pattern in a proposed Saga document. Propagate distinct recovery/lessons timeouts to real dispatchers,
preserve existing payload contracts and NN-1 approval pauses, and define retry/idempotency/compensation for each transition rather than diagram-only states.
**Tester:** extend [governance contracts](../../tests/contract/test_governance_assignment.py#L1),
[handoff chain integration](../../tests/integration/test_handoff_chain.py#L1) and [retry tests](../../tests/unit/test_async_handoff_retry.py#L1):
every valid transition, impossible transition, recovery versus lessons timeout, retry exhaustion, cancellation and graph/config drift.
**Future:** `pytest tests/contract/test_governance_assignment.py tests/integration/test_handoff_chain.py tests/unit/test_async_handoff_retry.py -q`;
expected: generated graph covers all configured transitions and distinct timeout values affect their actual callers. Depends on 005/008/010.
**Complete when:** runtime, generated graph and Saga document share one state model and every timeout/recovery transition is audited.

- [ ] AUD-032-035 Persist approval-outcome reflection as governed evaluation candidates

**P1; original:** T710; FR-AG07, US5 lifecycle, E-06, continual-improvement constraint.
**Expected/actual/impact:** [approval service](../../apps/api/app/services/recommendation_service.py#L11) only mutates status/creates an alert;
no searched caller forwards actual approval/helpfulness outcomes to a training/eval candidate store. Guardrail criticism is not this feedback loop.
**Developer:** link outcome, original recommendation/provenance, operator decision and later usefulness feedback into an idempotent AU-resident candidate
record. Sanitize before storage, retain consent/policy and approvals, and route candidates through the existing eval author/reviewer workflow; never
auto-promote rejection text or real operational data to approved training data. Preserve approvals even if downstream candidate export is retried.
**Tester:** extend [approval state-machine tests](../../tests/integration/test_approval_workflow_state_machine.py#L1) and
[eval sanitisation tests](../../tests/unit/eval/test_sanitise.py#L1): approved-helpful, approved-harmful, rejected, edited, duplicate/retried event,
missing consent, PII and unavailable candidate store; assert one candidate, original provenance and draft-only approval state.
**Future:** `pytest tests/integration/test_approval_workflow_state_machine.py tests/unit/eval/test_sanitise.py -q`;
expected: no lost approval and no unauthorized dataset promotion. Depends on 007/008/009/018.
**Complete when:** the real outcome path creates governed, traceable feedback candidates without implying model training was performed.

- [ ] AUD-032-036 Record cross-agent consensus and completion-time coordination gaps

**P1; original:** T712, T713; FR-AG09/10, US5.1/4, E-05.
**Expected/actual/impact:** [rehearsal orchestration](../../apps/api/app/services/rehearsal_orchestrator.py#L26) copies preparedness gaps;
there is no ConsensusEvent detector/store or ScenarioRun-completion summary of runtime handoff timeouts/DLQ cycles/agreements.
**Developer:** define domain-specific agreement on incident/corridor/conclusion, minimum distinct agents, bounded time window and normalized score;
persist tenant-scoped immutable events and link recommendations/cards. Generate an idempotent completion-time AAR containing timeout/DLQ/consensus IDs,
including empty and partial/cancelled runs; do not replace measured coordination events with static organisation-analysis findings.
**Tester:** extend [preparedness replay tests](../../tests/simulation/test_preparedness_replays.py#L1) and
[handoff chain tests](../../tests/integration/test_handoff_chain.py#L1): evacuation/resource same corridor, disagreeing conclusions,
same-agent duplicate, expired window, cross-tenant collision, cancelled run, repeated completion, empty run and recovery loop.
**Future:** `pytest tests/simulation/test_preparedness_replays.py tests/integration/test_handoff_chain.py -q`;
expected: exactly one valid consensus link and deterministic AAR from actual runtime events. Depends on 007/008/034.
**Complete when:** every ScenarioRun closure exposes trustworthy coordination evidence and the recommendation card surfaces genuine multi-agent agreement.

## Original Task Coverage

`[X]` is the exact original uppercase state; `none` means the original declaration has no checkbox.
No unchecked state is invented. IMPLEMENTED means source-supported behavior or the specified authored artifact, never execution.
PARTIAL means a concrete remaining obligation; CONFLICT means a requirement/source disagreement; MISSING follows the bounded searches
documented below; UNVERIFIED applies to outcomes/approvals without trustworthy records; SUPERSEDED requires an explicit repository decision.
All follow-up IDs below refer to the unchecked tasks above. Every original task has exactly one row, including four-digit IDs.

| Original task | Original state | Status | Concrete evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [X] | PARTIAL | [Hooks](../../.pre-commit-config.yaml#L26) omit tests from mypy and differ from blocking CI intent. | AUD-032-001 |
| T002 | [X] | PARTIAL | [Tier guide](../../tests/README.md#L8) exists; canonical CI command, E2E location and contributor/chaos links are stale. | AUD-032-028 |
| T003 | [X] | IMPLEMENTED | [Contributing guide](../../CONTRIBUTING.md#L14) authors branch conventions and spec workflow; correctness updates tracked separately. | AUD-032-028 |
| T004 | [X] | IMPLEMENTED | [Changelog](../../CHANGELOG.md#L91) includes an explicitly in-progress 032 section. | AUD-032-028 |
| T005 | [X] | PARTIAL | [Dependabot](../../.github/dependabot.yml#L6) covers four Docker locations, not all six. | AUD-032-020 |
| T006 | [X] | PARTIAL | [030 status](../030-llm-eval-framework/spec.md#L5) is Approved; no inspected PR-comment approval evidence supports the claimed promotion. | AUD-032-018, AUD-032-030 |
| T007 | [X] | CONFLICT | [031 status](../031-simplify-cicd-pipeline/spec.md#L5) remains Draft; [plan prerequisite](plan.md#L227) is not verified by a checked dependency entry/soak record. | AUD-032-030, AUD-032-031 |
| T008 | [X] | SUPERSEDED | [Deletion note](T008-fr-i05-status.md#L13) explicitly retires the named identity targets via 031; path inventory confirms absence. Future new identities remain constrained. | AUD-032-031 |
| T009 | [X] | PARTIAL | [Traceability scaffold](traceability.md#L5) exists only locally; full 41-spec inventory does not establish portfolio matrices. | AUD-032-030 |
| T010 | [X] | IMPLEMENTED | [README](../../README.md#L185) lists Dependency Notifier as first-class; its directory reference and five-agent summary need correction. | AUD-032-028 |
| T011 | [X] | PARTIAL | [Relocated ADR-032](../../docs/corpus/aidr/decisions/adr-032-oidc-supersession.md#L3) authors the migration but remains Proposed and permits a fallback needing resolution. | AUD-032-031 |
| T012 | [X] | IMPLEMENTED | [Relocated ADR-033](../../docs/corpus/aidr/decisions/adr-033-phi-shadow-boundary.md#L22) authors classification, transit and retention design; approval/implementation are separate. | AUD-032-014 |
| T013 | [X] | PARTIAL | [Relocated ADR-034](../../docs/corpus/aidr/decisions/adr-034-pybreaker-adoption.md#L13) inaccurately says the legacy breaker lacks half-open behavior. | AUD-032-011 |
| T014 | [X] | PARTIAL | [Relocated ADR-035](../../docs/corpus/aidr/decisions/adr-035-cosign-keyless-prompts.md#L45) authors verification but omits required certificate/bundle wiring. | AUD-032-016 |
| T015 | [X] | CONFLICT | [Relocated ADR-036](../../docs/corpus/aidr/decisions/adr-036-aisearch-rag.md#L20) lists a paired-region index despite its AU-East-only/no-replication statement. | AUD-032-013, AUD-032-030 |
| T016 | [X] | UNVERIFIED | [Spike status](../../docs/spikes/T016-killswitch-propagation.md#L5) explicitly defers prototype and measurements; budget estimates are not 100-toggle results. | AUD-032-005 |
| T017 | [X] | IMPLEMENTED | [Registry](../../infra/parameters/foundry-carveout.yaml#L14) and [schema](../../infra/parameters/foundry-carveout.schema.json#L1) are authored; approvals/deployment binding not established. | AUD-032-015 |
| T018 | [X] | PARTIAL | [CD hook](../../.github/workflows/cd.yml#L224) calls validator without prospective resource inventory; [optional comparison](../../scripts/verify-carveout.ps1#L124) can be skipped. | AUD-032-015 |
| T019 | [X] | IMPLEMENTED | [Taxonomy](../../docs/safety/classification-taxonomy.md#L1) documents PII/PSPF/operational classes, policies and governance; code coverage differs. | AUD-032-014 |
| T020 | [X] | PARTIAL | [Hub](../../docs/governance-hub/index.md#L9) is authored but wrong relative links prevent the promised navigation. | AUD-032-028 |
| T021 | [X] | IMPLEMENTED | [System](../../docs/architecture/c4/system.md#L34) and [container](../../docs/architecture/c4/container.md#L36) seed diagrams exist; not proof of actual topology or common generation. | AUD-032-029 |
| T022 | [X] | PARTIAL | [RU table](../../docs/architecture/cosmos-partitioning.md#L35) is a legacy copy; [authoritative redirect](../../docs/architecture/deployment/cosmos-partitioning.md#L24) lacks RU math. | AUD-032-029 |
| T023 | [X] | CONFLICT | [Header targets](../../infra/main.bicep#L52) do not match [actual shared agents scale](../../infra/main.bicep#L1180); no claimed per-agent queue rules. | AUD-032-029 |
| T024 | [X] | IMPLEMENTED | [Sequence](../../docs/architecture/sequence/monitoring-risk-comms.md#L16) authors retries, dead letters, approval and recovery; runtime claims remain separate. | AUD-032-029 |
| T025 | [X] | PARTIAL | [SLO catalogue](../../docs/observability/slo.md#L19) includes objectives and tiers; budget clocks/math and alert composition remain incomplete. | AUD-032-022 |
| T026 | [X] | PARTIAL | [Metric catalogue](../../docs/observability/metrics-catalogue.md#L7) omits many inventoried metrics and references nonexistent/unconsumed producers. | AUD-032-021 |
| T027 | [X] | PARTIAL | [Decision rights](../../docs/agents/decision-rights.md#L7) covers six named agents; new dispatcher planning role and runtime enforcement are not covered. | AUD-032-006, AUD-032-030 |
| T028 | [X] | PARTIAL | [Prompt README](../../packages/prompts/README.md#L7) and [manifest](../../packages/prompts/cosign.manifest.yaml#L17) exist; claimed consumer/verifier do not. | AUD-032-016 |
| T029 | [X] | IMPLEMENTED | [Licence note](../../docs/corpus/aidr/INDEXING-LICENCE-NOTE.md#L3) and [all nine rows](../../docs/corpus/aidr/LICENCE-INVENTORY.md#L16) explicitly preserve metadata-only pending approval. | AUD-032-013 |
| T030 | [X] | PARTIAL | [Schedule](../../docs/disaster-response-hub/evaluation/exercise-schedule.md#L9) publishes cadence but Apr/Oct and Jun/Dec contradict each other. | AUD-032-025 |
| T101 | [X] | PARTIAL | [pyproject mypy configuration](../../pyproject.toml#L90) is the replacement for absent mypy.ini, but test errors and strict options are suppressed. | AUD-032-001 |
| T102 | [X] | IMPLEMENTED | [Import contracts](../../pyproject.toml#L104) declare agents/API, ingestion/API and domain/apps boundaries. | AUD-032-001 |
| T103 | [X] | IMPLEMENTED | [CI format step](../../.github/workflows/ci.yml#L112) is blocking over apps/tests/packages. | - |
| T104 | none | UNVERIFIED | [Session record](SESSION-STATUS-2026-04-30.md#L55) records gates, not a reproducible complete format-run result for this revision. | AUD-032-001, AUD-032-030 |
| T105 | [X] | PARTIAL | [Mypy CI](../../.github/workflows/ci.yml#L116) excludes tests and continues on error. | AUD-032-001 |
| T106 | [X] | IMPLEMENTED | [CI import-linter](../../.github/workflows/ci.yml#L121) is a blocking step; actual forbidden imports need repair. | AUD-032-001 |
| T107 | [X] | PARTIAL | [Ratchet](../../scripts/coverage-ratchet.ps1#L45) skips missing XML, tolerates regression and has no CI baseline transport. | AUD-032-019 |
| T108 | [X] | CONFLICT | [CodeQL workflow](../../.github/workflows/codeql.yml#L3) disables analysis and has only manual dispatch. | AUD-032-020 |
| T109 | [X] | IMPLEMENTED | [Security workflow](../../.github/workflows/security-scan.yml#L9) authors PR/push gitleaks, PSRule and Trivy jobs; execution not inferred. | AUD-032-020 |
| T110 | [X] | PARTIAL | Full 25-workflow inventory finds 20 tagged refs, including [CI](../../.github/workflows/ci.yml#L417). | AUD-032-020 |
| T201 | [X] | PARTIAL | [Resilience facade](../../apps/agents/common/resilience/__init__.py#L14) re-exports flat implementations rather than moving them. | AUD-032-010 |
| T202 | [X] | PARTIAL | [Safety facade](../../apps/agents/common/safety/__init__.py#L9) adds classification but not all promised redaction/validation modules or relocation. | AUD-032-009, AUD-032-010 |
| T203 | [X] | PARTIAL | [Lifecycle facade](../../apps/agents/common/lifecycle/__init__.py#L10) exposes helpers; production startup/degraded evaluator is not integrated. | AUD-032-005, AUD-032-010 |
| T204 | none | PARTIAL | [Explicit retained originals](../../apps/agents/common/resilience/__init__.py#L7) and 31 flat files disprove completed move; test execution unverified. | AUD-032-010 |
| T205 | [X] | PARTIAL | [Strategy module](../../apps/agents/common/llm_strategies.py#L16) is explicitly additive; active mixin never calls it. | AUD-032-011 |
| T206 | [X] | PARTIAL | [Adapter](../../apps/agents/common/resilience/pybreaker_adapter.py#L110) is unconsumed and cannot initiate half-open trial through can_execute. | AUD-032-011 |
| T207 | [X] | PARTIAL | [Durable adapter](../../apps/agents/common/llm_budget_tracker.py#L132) is unconsumed and resets on failure; active mixin remains process-local. | AUD-032-012 |
| T208 | [X] | PARTIAL | [Typed registry](../../apps/agents/common/aiims_registry.py#L48) seeds from old constants; only tests use the override API. | AUD-032-006 |
| T209 | [X] | PARTIAL | [Classification](../../apps/agents/common/safety/classification.py#L192) is regex-based and unconsumed; newer gateway does not implement full deny-by-default taxonomy. | AUD-032-009, AUD-032-014 |
| T301 | none | MISSING | [Recommendation](../../packages/domain/src/domain/models/recommendation.py#L7) lacks E-01; bounded model/producer search found no RecommendationProvenance replacement. | AUD-032-007 |
| T302 | none | PARTIAL | [RagCitation](../../packages/domain/src/domain/models/rag_citation.py#L17) exists with quote/page validation but permits scores >1 and is not attached to Recommendation. | AUD-032-007, AUD-032-013 |
| T303 | none | MISSING | [Existing audit repository](../../apps/api/app/repositories/audit_repository.py#L85) appends rows but no AuditSegment model/repository/hash chain exists in searched runtime. | AUD-032-008 |
| T304 | none | MISSING | [Replay hash](../../apps/agents/common/audit.py#L52) hashes retrieval inputs, not previous-segment continuity/canonical events. | AUD-032-008 |
| T305 | none | MISSING | [Registered startup](../../apps/api/app/main.py#L25) and root jobs lack an integrity job; full job/infra search found none. | AUD-032-008 |
| T306 | none | MISSING | [API registration](../../apps/api/app/api/router.py#L56) has no audit-integrity operation matching [contract](contracts/openapi-delta.yaml#L15). | AUD-032-008 |
| T307 | none | MISSING | [Recommendation routes](../../apps/api/app/api/routes/recommendations.py#L7) expose approvals only; no why-fired handler found. | AUD-032-007 |
| T308 | none | PARTIAL | [LLM return](../../apps/agents/common/llm_client.py#L247) contains deployment/token data; new audit helper fields are not carried through the mixin/recommendation. | AUD-032-007 |
| T309 | none | PARTIAL | [Request classifier](../../apps/api/app/middleware/classifier_gateway.py#L35) is selective masking, not universal log allowlist/hash sanitizer/canary job. | AUD-032-009 |
| T310 | none | MISSING | [Existing recommendation card](../../apps/web/src/components/recommendations/recommendation-card.tsx#L40) is a citation scaffold, not the required why-fired page; no alternative route found. | AUD-032-007 |
| T311 | none | MISSING | [Decision-rights doc](../../docs/agents/decision-rights.md#L3) references a Saga document not found by saga/process-manager/state-graph searches. | AUD-032-034 |
| T401 | [X] | CONFLICT | [Root Cosmos](../../infra/main.bicep#L587) remains Enabled and [wildcard](../../infra/main.bicep#L147) persists. | AUD-032-002 |
| T402 | [X] | PARTIAL | [CMK module](../../infra/modules/cosmos-cmk.bicep#L33) authors HSM rotation/key RBAC but root account has no key binding. | AUD-032-003 |
| T403 | [X] | CONFLICT | [Actual Storage](../../infra/main.bicep#L493) has no CMK or PE and enables public network access; historical storage module is not the owner. | AUD-032-002, AUD-032-003 |
| T404 | [X] | CONFLICT | [Actual Foundry account](../../infra/main.bicep#L954) remains public; imported deployment module does not change network properties. | AUD-032-002 |
| T405 | [X] | PARTIAL | [PE-capable module](../../infra/modules/content-safety-pe.bicep#L53) exists but [root](../../infra/main.bicep#L453) uses a different module without PE/RBAC parameters. | AUD-032-002 |
| T406 | [X] | CONFLICT | [Root Search call](../../infra/main.bicep#L302) supplies empty subnet/DNS and public access true through the disabling flag set false. | AUD-032-002 |
| T407 | [X] | PARTIAL | [Defender pricing module](../../infra/modules/defender.bicep#L9) exists, unbound to root/CD/policy composition. | AUD-032-023 |
| T408 | [X] | PARTIAL | [Sentinel rules](../../infra/modules/sentinel.bicep#L36) are authored without composed connectors/actions. | AUD-032-023 |
| T409 | none | MISSING | No autonomy OPA policy in infra/policies or infra/policy; [local evaluator](../../apps/agents/common/lifecycle/autonomy_eval.py#L67) is not that authorization enforcement. | AUD-032-004, AUD-032-006 |
| T410 | none | MISSING | No kill-switch OPA policy found; [local state](../../apps/agents/common/lifecycle/killswitch.py#L71) has no role/dual-approval enforcement. | AUD-032-004 |
| T411 | none | MISSING | No prompt-signing OPA policy or CD verify consumer found; [manifest](../../packages/prompts/cosign.manifest.yaml#L17) is configuration only. | AUD-032-016 |
| T412 | none | PARTIAL | [Relocated OPA policy](../../infra/policy/rego/foundry_carveout.rego#L8) exists; CD's script does not invoke it or enforce its environment quorum. | AUD-032-015 |
| T413 | none | CONFLICT | [CD auth](../../.github/workflows/cd.yml#L81) is JSON-secret based; spec-031 approval/soak prerequisite is unmet in available evidence. | AUD-032-031 |
| T414 | none | UNVERIFIED | [ADR stage order](../../docs/corpus/aidr/decisions/adr-032-oidc-supersession.md#L30) is only a plan; no seven-day dev soak/staging migration record. | AUD-032-031 |
| T415 | none | UNVERIFIED | [ADR stage order](../../docs/corpus/aidr/decisions/adr-032-oidc-supersession.md#L30) has no staged production migration/soak evidence. | AUD-032-031 |
| T416 | none | MISSING | No public-network-probe workflow/script replacement in scoped inventory; [synthetics](../../infra/modules/availability-tests.bicep#L42) check only HTTP availability. | AUD-032-002 |
| T501 | [X] | IMPLEMENTED | All four app manifests declare the distro: [API](../../apps/api/pyproject.toml#L19), [agents](../../apps/agents/pyproject.toml#L13), [ingestion](../../apps/ingestion/pyproject.toml#L24), [eval](../../apps/eval-runner/pyproject.toml#L23). | - |
| T502 | [X] | PARTIAL | [API bootstrap](../../apps/api/app/observability/__init__.py#L18) plus API/MAF/worker startup exist; no complete contract resource attributes or eval/web bootstrap coverage. | AUD-032-021 |
| T503 | none | PARTIAL | [API stack](../../apps/api/app/main.py#L25) lacks general contract-attribute middleware; simulation-specific context does not cover every request. | AUD-032-021 |
| T504 | none | PARTIAL | [OTel recorder](../../apps/agents/common/otel_telemetry.py#L78) and [LLM return](../../apps/agents/common/llm_client.py#L247) do not export required LLM/handoff/audit attributes. | AUD-032-021 |
| T505 | none | PARTIAL | [Monitoring](../../infra/modules/monitoring.bicep#L21) defines 90 days, not separate audit/operational/security/eval retention. | AUD-032-022 |
| T506 | none | PARTIAL | [Action Group](../../infra/modules/monitoring.bicep#L50) is generic email/webhook, not P1-P5 routing and issue creation. | AUD-032-022 |
| T507 | [X] | CONFLICT | [Availability module](../../infra/modules/availability-tests.bicep#L28) includes US San Jose and is not root-composed. | AUD-032-022 |
| T508 | [X] | PARTIAL | [Executive Workbook](../../infra/modules/workbooks/executive-governance.json#L4) has four charts but lacks governance score/active incidents and bound data sources. | AUD-032-022 |
| T509 | [X] | IMPLEMENTED | [LLM-cost Workbook JSON](../../infra/modules/workbooks/llm-cost.json#L4) authors cost/warning/token charts; deployment/data production remain separate. | AUD-032-012, AUD-032-022 |
| T510 | none | MISSING | Workbook inventory has only executive/LLM-cost in the named module directory; [executive charts](../../infra/modules/workbooks/executive-governance.json#L4) do not cover agent-DLQ/operator workflows. | AUD-032-022 |
| T511 | none | PARTIAL | [Emitter](../../apps/api/app/observability/metrics.py#L46) accepts arbitrary names and caches instruments; no MetricDefinition registration/validation. | AUD-032-021 |
| T512 | none | PARTIAL | [Disconnected tracker emitter](../../apps/agents/common/llm_budget_tracker.py#L196) exists; [active budget path](../../apps/agents/common/llm_mixin.py#L47) logs only. | AUD-032-012, AUD-032-021 |
| T601 | none | PARTIAL | [Search module](../../infra/modules/ai-search.bicep#L27) supports SKU/replicas; root always supplies Standard and disables PE, not the specified env composition. | AUD-032-002, AUD-032-013 |
| T602 | none | PARTIAL | [Relocated ingest CLI](../../apps/ingest-runner/src/ama_ingest/__main__.py#L340) filters/embeds corpus but absent mode defaults full-text and sign-offs are not checked. | AUD-032-013 |
| T603 | [X] | PARTIAL | [Old service](../../apps/api/app/services/rag_service.py#L74) is lexical-only; [new client](../../apps/agents/common/retrieval_client.py#L846) implements hybrid but deployed dispatcher bypasses it. | AUD-032-013 |
| T604 | none | PARTIAL | [Citation card](../../apps/web/src/components/recommendations/recommendation-card.tsx#L76) exists without production imports; [dispatcher](../../apps/agents/dispatcher/agent.py#L269) returns empty citations. | AUD-032-007, AUD-032-013 |
| T605 | none | MISSING | Complete prompt-tree inventory is README+manifest only; [documented templates/loader](../../packages/prompts/README.md#L9) are examples, not shipped assets. | AUD-032-016 |
| T606 | [X] | PARTIAL | [Signing](../../.github/workflows/prompts-publish.yml#L32) can silently find no diff and never reaches its push-only commit step. | AUD-032-016 |
| T607 | none | MISSING | [CD provisioning/deploy](../../.github/workflows/cd.yml#L237) has no signature-verification gate; no hook replacement found. | AUD-032-016 |
| T608 | none | MISSING | No Phi shadow runner/store writer; [MAF shadow mode](../../apps/agents/maf_runtime/agents/_factory.py#L298) is runtime comparison, not the required Phi path. | AUD-032-014 |
| T609 | none | MISSING | [Translator](../../apps/agents/communication/translator.py#L143) and six other direct/forwarded calls omit schema; no caller-enforcement script/rule found. | AUD-032-017 |
| T610 | none | PARTIAL | [Eval workflow](../../.github/workflows/eval-pr-gate.yml#L3) is manual/skip-capable and [runner](../../apps/eval-runner/src/ama_eval/runner.py#L157) never invokes the gate. | AUD-032-018 |
| T611 | none | PARTIAL | [Manifest](../../packages/eval-dataset/data/dataset-disaster-core-1.0.0/manifest.json#L6) and full row count support 5,000; all approval chains are draft-only. | AUD-032-018 |
| T701 | [X] | PARTIAL | [Renamed repository](../../apps/api/app/repositories/jurisdiction_governance_policy_repository.py#L51) has invalid Cosmos read projection and no root-composed governance-policy container. | AUD-032-006 |
| T702 | [X] | PARTIAL | [Underscore-named loader](../../scripts/load_jurisdiction_policies.py#L34) exists; only three policy YAMLs and no deploy caller. | AUD-032-006 |
| T703 | [X] | PARTIAL | [Evaluator](../../apps/agents/common/lifecycle/autonomy_eval.py#L67) has only unit-test consumers and permissive unknown-env handling. | AUD-032-006 |
| T704 | [X] | MISSING | [Watcher design](../../apps/agents/common/lifecycle/killswitch.py#L1) claims a publisher/listener but no config/lease container, publisher job or kill-switch bus topic is composed. | AUD-032-005 |
| T705 | none | PARTIAL | [Injected poll hook](../../apps/agents/common/lifecycle/killswitch.py#L107) lacks subscription/drain/expiry enforcement. | AUD-032-005 |
| T706 | [X] | PARTIAL | [Heartbeat](../../apps/agents/common/lifecycle/heartbeat.py#L22) emits if called; apply only measures receipt, not all-process drain, and production has no watcher. | AUD-032-005, AUD-032-021 |
| T707 | none | MISSING | [Agent router](../../apps/api/app/api/routes/agents.py#L24) has no governed kill-switch mutation. | AUD-032-004 |
| T708 | none | MISSING | [Agent router](../../apps/api/app/api/routes/agents.py#L24) has no autonomy mutation; local OpenAPI also omits it. | AUD-032-004 |
| T709 | none | MISSING | [MAF graph code](../../apps/agents/maf_runtime/workflow/builder.py#L89) does not generate stateDiagram-v2; no renderer/replacement found. | AUD-032-034 |
| T710 | none | MISSING | [Approval service](../../apps/api/app/services/recommendation_service.py#L11) updates state/alert only, not an outcome-to-training feedback store. | AUD-032-035 |
| T711 | none | PARTIAL | [Handoff model](../../packages/domain/src/domain/models/handoff_chain.py#L22) lacks per-handoff timeout; legacy retry hardcodes two seconds and MAF lacks recovery/lessons split. | AUD-032-034 |
| T712 | none | MISSING | [Recommendation model](../../packages/domain/src/domain/models/recommendation.py#L7) and full consensus search contain no consensus event/detector/store. | AUD-032-036 |
| T713 | none | PARTIAL | [Rehearsal summary](../../apps/api/app/services/rehearsal_orchestrator.py#L26) copies static organisation-analysis gaps, not runtime timeouts/DLQ/consensus for every completion. | AUD-032-036 |
| T714 | none | PARTIAL | [Recommendation](../../packages/domain/src/domain/models/recommendation.py#L13) has signal IDs/confidence but no threshold/persona/policy why-fired artifact or endpoint. | AUD-032-007 |
| T801 | none | CONFLICT | [Spec 031](../031-simplify-cicd-pipeline/spec.md#L5) remains Draft; simplified CD authorship is not all prerequisite approvals/soak. | AUD-032-030, AUD-032-031 |
| T802 | none | PARTIAL | [CI benchmark](../../.github/workflows/ci.yml#L147) is blocking, but [session hook](../../tests/benchmark/conftest.py#L87) exempts CI from comparison failure and uses medians. | AUD-032-026 |
| T803 | [X] | PARTIAL | [Nightly load](../../.github/workflows/nightly-load.yml#L44) swallows failure and does not drive Locust/staging assertions. | AUD-032-026 |
| T804 | [X] | PARTIAL | [Capacity model](../../docs/architecture/capacity-model.md#L24) authors throughput but baseline SKUs/caps/rules and 30% headroom are not source-aligned. | AUD-032-029 |
| T805 | none | PARTIAL | Root containers have caps, but [imported workflow containers](../../infra/bicep/modules/cosmos-workflow.bicep#L34) have no throughput options. | AUD-032-029 |
| T806 | [X] | PARTIAL | [Chaos module](../../infra/modules/chaos-studio.bicep#L91) waits instead of a Cosmos fault and is not composed with capability/RBAC. | AUD-032-025 |
| T807 | [X] | PARTIAL | [Quarterly workflow](../../.github/workflows/chaos-quarterly.yml#L51) breaks on failure without failing the job; outcome/SLO verification is absent. | AUD-032-025 |
| T808 | none | IMPLEMENTED | [Root backup policy](../../infra/main.bicep#L594) explicitly enables Continuous7Days despite no original checkbox. | - |
| T809 | [X] | PARTIAL | [DR runbook](../../docs/operator-runbooks/dr-bcp.md#L19) defines RPO/RTO but relies on unprovisioned secondary compute/routing and missing integrity check. | AUD-032-024 |
| T810 | [X] | PARTIAL | [Restore runbook](../../docs/operator-runbooks/cosmos-backup-restore.md#L32) references missing copy helper and unavailable integrity operation. | AUD-032-024 |
| T811 | [X] | PARTIAL | [Model rollback](../../docs/operator-runbooks/model-rollback.md#L16) uses old aliases/model versions rather than active Foundry coordinates and unavailable verification endpoints. | AUD-032-028, AUD-032-031 |
| T812 | [X] | IMPLEMENTED | [Cost template](../../docs/operator-runbooks/cost-reporting.md#L5) authors source fields/report sections; actual budget/metric linkage remains 012/021. | AUD-032-012 |
| T813 | none | PARTIAL | [Agents base](../../apps/agents/Dockerfile#L1) and all other FROM rows are tag-only; Dependabot omits ingest-runner/web Docker. | AUD-032-020 |
| T814 | [X] | PARTIAL | [DORA workflow](../../.github/workflows/dora-metrics.yml#L7) is manual; [collector](../../scripts/dora_metrics_publish.py#L93) misattributes incidents and overcounts CFR. | AUD-032-027 |
| T815 | [X] | CONFLICT | [Gate matrix](../../docs/ci-cd/progressive-delivery.md#L19) claims PR eval/CodeQL/cosign/soak gates absent from effective workflow composition. | AUD-032-031 |
| T816 | [X] | PARTIAL | [DORA doc](../../docs/ci-cd/dora-metrics.md#L17) claims daily publication and defers the actual Workbook. | AUD-032-027 |
| T817 | [X] | PARTIAL | [Quota guide](../../docs/operator-runbooks/aoai-quota.md#L7) exists but old deployment/TPM claims mismatch current model module; service-response promises lack evidence. | AUD-032-028 |
| T818 | [X] | PARTIAL | [DR workflow](../../.github/workflows/dr-drill.yml#L58) authors failover commands but not actual secondary/RPO measurements or strict staging guard. | AUD-032-024 |
| T819 | none | MISSING | [CD](../../.github/workflows/cd.yml#L237) has no new-model canary gate; [ADR-20](../../docs/decisions/036-foundry-rag-grounding/20-hard-cutover-foundry-foundation.md#L5) retires only migration canaries. | AUD-032-031 |
| T901 | none | MISSING | [README evaluator links](../../README.md#L275) provide deck/walkthrough text, no 60-second video link. | AUD-032-028 |
| T902 | none | PARTIAL | [FastAPI docs](../../apps/api/app/main.py#L30) exist at /api/docs from runtime schema, not a web /api-docs route rendering published YAML. | AUD-032-028 |
| T903 | none | PARTIAL | [Hub](../../docs/governance-hub/index.md#L9) has incorrect relative links and is not the single discoverable README/web navigation. | AUD-032-028 |
| T904 | [X] | PARTIAL | [Vitest config](../../apps/web/vitest.config.ts#L20) discovers tests, but original [smoke](../../apps/web/__tests__/smoke.test.tsx#L10) has two tests and CI does not run the full tier. | AUD-032-028 |
| T905 | [X] | PARTIAL | [Operator spec](../../apps/web/e2e/operator-journey.spec.ts#L9) only smokes pages, accepts 404 and is outside configured discovery. | AUD-032-028 |
| T906 | none | MISSING | [Tier guide](../../tests/README.md#L36) points to a nonexistent contract contributor guide; bounded docs/tests search found no replacement. | AUD-032-028 |
| T907 | none | PARTIAL | [032 matrix](traceability.md#L16) remains scaffold/pending/complete-stub, lacks parent FR-S02 and usable acceptance IDs; portfolio mapping incomplete. | AUD-032-030 |
| T908 | none | MISSING | [Survey](../../docs/disaster-response-hub/evaluation/post-exercise-survey.md#L23) is blank and has no outcome-to-test links. | AUD-032-028, AUD-032-030 |
| T909 | none | PARTIAL | [Eval tests](../../tests/unit/eval/test_orchestrator_e2e.py#L89) assert fake-run behavior but no concrete per-acceptance 030 ID inventory was found. | AUD-032-018 |
| T910 | none | MISSING | [Relocated operator guide](../../docs/disaster-response-hub/operator-runbooks.md#L1) covers five operational workflows, not ingestion start/stop/observability/dead-letter recovery. | AUD-032-028 |
| T1001 | none | UNVERIFIED | [Session deferred work](SESSION-STATUS-2026-04-30.md#L78) and current hook scope do not prove a full pre-commit pass at this SHA. | AUD-032-001, AUD-032-030 |
| T1002 | none | UNVERIFIED | [Historical lint claim](SESSION-STATUS-2026-04-30.md#L115) has no complete revision-bound execution record inspected here. | AUD-032-030 |
| T1003 | none | UNVERIFIED | [Nonblocking CI](../../.github/workflows/ci.yml#L116) cannot substantiate successful strict validation. | AUD-032-001, AUD-032-030 |
| T1004 | none | UNVERIFIED | [Current CI test selection](../../.github/workflows/ci.yml#L132) differs from the required command and no trustworthy full coverage run is supplied. | AUD-032-019, AUD-032-030 |
| T1005 | none | PARTIAL | [Traceability polish gate](traceability.md#L106) is authored, but pending/scaffold/unsupported complete rows remain. | AUD-032-030 |
| T1006 | none | PARTIAL | [032 changelog entry](../../CHANGELOG.md#L91) lists foundations only, not a verified complete release slice. | AUD-032-028, AUD-032-030 |
| T1007 | none | UNVERIFIED | [Step-8 deferral](SESSION-STATUS-2026-04-30.md#L95) explicitly postpones all-agent review; analysis is not implementation-review execution. | AUD-032-030 |
| T1008 | none | UNVERIFIED | [Step-9 deferral](SESSION-STATUS-2026-04-30.md#L96) lacks deployment evidence; this audit executed no Azure command. | AUD-032-030 |
| T1009 | none | UNVERIFIED | No local v032-rubric-improvements tag in read-only metadata; [release task](tasks.md#L205) is not proof of remote tag/merge. | AUD-032-030 |
| T1010 | none | CONFLICT | [032 status](spec.md#L5) remains Draft; no status-promotion execution is inferred. | AUD-032-030 |

## Requirement Coverage

All 89 FR declarations are represented, including the parent FR-S02 and suffix requirements FR-AI03a, FR-AG05a,
FR-S02a and FR-S02b. Overlaps retain separate rows. There are no numbered NFR declarations in this spec;
the unnumbered nonfunctional, persona, assumption and design obligations have their own table below.

| Requirement | Status | Controlling evidence and remaining obligation | Follow-up |
| --- | --- | --- | --- |
| FR-A01 | PARTIAL | [C4 system](../../docs/architecture/c4/system.md#L34) and container views exist; no single source generating all three levels and README navigation to that model. | AUD-032-029 |
| FR-A02 | PARTIAL | [Legacy RU math](../../docs/architecture/cosmos-partitioning.md#L35) conflicts with [authoritative model](../../docs/architecture/deployment/cosmos-partitioning.md#L24) and actual keys/caps. | AUD-032-029 |
| FR-A03 | CONFLICT | [Header targets](../../infra/main.bicep#L52) differ from shared agents/API scaling; comments are not enforced per-agent queue rules. | AUD-032-029 |
| FR-A04 | IMPLEMENTED | [Authored sequence](../../docs/architecture/sequence/monitoring-risk-comms.md#L16) includes retry, dead-letter, recovery and approval flows; execution is not implied. | AUD-032-029 |
| FR-A05 | PARTIAL | [Compatibility facade](../../apps/agents/common/resilience/__init__.py#L7) retains original implementations; 31 flat Python files remain. | AUD-032-010 |
| FR-P01 | PARTIAL | [Strategy chain](../../apps/agents/common/llm_strategies.py#L16) explicitly awaits migration; active mixin does not call it. | AUD-032-011 |
| FR-P02 | PARTIAL | [Active counter](../../apps/agents/common/llm_mixin.py#L35) is in-memory; durable adapter is unconsumed and unsafe on conflicts. | AUD-032-012 |
| FR-P03 | PARTIAL | [Adapter](../../apps/agents/common/resilience/pybreaker_adapter.py#L110) and ADR exist but callers remain legacy and open-state recovery is defective. | AUD-032-011 |
| FR-P04 | MISSING | [Decision-rights reference](../../docs/agents/decision-rights.md#L3) points to absent Saga document; MAF workflow is not the required named process-manager artifact. | AUD-032-034 |
| FR-P05 | PARTIAL | [Registry](../../apps/agents/common/aiims_registry.py#L48) supports local overrides, not declarative runtime consumption. | AUD-032-006 |
| FR-Q01 | PARTIAL | [CI](../../.github/workflows/ci.yml#L116) continues on strict errors and omits tests; configuration suppresses test errors. | AUD-032-001 |
| FR-Q02 | IMPLEMENTED | [Forbidden import contract](../../pyproject.toml#L108) and blocking lint-imports step exist; illegal imports are a separate repair obligation. | AUD-032-001 |
| FR-Q03 | IMPLEMENTED | [Format check](../../.github/workflows/ci.yml#L112) blocks apps/tests/packages changes on configured CI triggers. | - |
| FR-Q04 | PARTIAL | [Hooks](../../.pre-commit-config.yaml#L26) do not mirror required strict scope and all CI checks. | AUD-032-001 |
| FR-Q05 | PARTIAL | [Facades](../../apps/agents/common/lifecycle/__init__.py#L10) do not reduce the flat implementation layout. | AUD-032-010 |
| FR-I01 | PARTIAL | [030 Approved](../030-llm-eval-framework/spec.md#L5), [031 Draft](../031-simplify-cicd-pipeline/spec.md#L5); approval/closure records absent. | AUD-032-030, AUD-032-031 |
| FR-I02 | PARTIAL | [5,000-case artifact](../../packages/eval-dataset/data/dataset-disaster-core-1.0.0/manifest.json#L6) exists under packages; complete row inspection finds zero safety approvals. | AUD-032-018 |
| FR-I03 | PARTIAL | [Operator spec](../../apps/web/e2e/operator-journey.spec.ts#L9) is a weak smoke outside actual discovery, not a critical journey. | AUD-032-028 |
| FR-I04 | MISSING | [Relocated runbook](../../docs/disaster-response-hub/operator-runbooks.md#L1) has no ingestion start/stop/dead-letter recovery procedure. | AUD-032-028 |
| FR-I05 | SUPERSEDED | [Explicit deletion decision](T008-fr-i05-status.md#L13) retires the three old placeholder-bearing targets; new identity guardrails remain binding. | AUD-032-031 |
| FR-T01 | PARTIAL | [Coverage ratchet](../../scripts/coverage-ratchet.ps1#L45) fails open with missing evidence and lacks same-branch successful-run/all-tier comparison. | AUD-032-019 |
| FR-T02 | PARTIAL | [Vitest config](../../apps/web/vitest.config.ts#L20) includes the tier; selected CI filters do not run the full web unit-test tier. | AUD-032-028 |
| FR-T03 | MISSING | No tests/chaos tier; [Chaos Studio workflow](../../.github/workflows/chaos-quarterly.yml#L51) is not resilience test assertions. | AUD-032-025 |
| FR-T04 | PARTIAL | [Supplementary scanners](../../.github/workflows/security-scan.yml#L9) exist; [SAST](../../.github/workflows/codeql.yml#L3) is disabled. | AUD-032-020 |
| FR-T05 | PARTIAL | [Scheduled workflow](../../.github/workflows/nightly-load.yml#L9) swallows failures and runs pytest smoke rather than actual staged load. | AUD-032-026 |
| FR-T06 | PARTIAL | [Tier guide](../../tests/README.md#L8) lists purpose/commands/runtime, but several paths and canonical CI claims are false. | AUD-032-028 |
| FR-T07 | PARTIAL | [032 matrix](traceability.md#L16) is incomplete; full 41-spec inventory below finds missing/partial and linked external candidate matrices. | AUD-032-030 |
| FR-T08 | MISSING | [Contributor-guide link](../../tests/README.md#L36) has no target or located replacement. | AUD-032-028 |
| FR-T09 | PARTIAL | [Eval unit assertions](../../tests/unit/eval/test_phase5_6_modules.py#L142) exist without all spec-030 acceptance IDs or a connected release gate. | AUD-032-018 |
| FR-T10 | MISSING | [Survey](../../docs/disaster-response-hub/evaluation/post-exercise-survey.md#L23) is a blank form, not outcomes linked to tests. | AUD-032-028, AUD-032-030 |
| FR-O01 | PARTIAL | [Monitoring retention](../../infra/modules/monitoring.bicep#L21) is uniformly 90 days, not four signal classes. | AUD-032-022 |
| FR-O02 | PARTIAL | [Catalogue](../../docs/observability/metrics-catalogue.md#L7) is not exhaustive against all inventoried instrument names/units/dimensions. | AUD-032-021 |
| FR-O03 | PARTIAL | [Mixin](../../apps/agents/common/llm_mixin.py#L47) logs warning only; disconnected tracker emits differing metric/dimension names. | AUD-032-012, AUD-032-021 |
| FR-O04 | PARTIAL | [Executive](../../infra/modules/workbooks/executive-governance.json#L4) and [cost](../../infra/modules/workbooks/llm-cost.json#L4) JSON exist; missing tiles, ingestion/agent-flow and root composition. | AUD-032-022 |
| FR-O05 | PARTIAL | [Classifier middleware](../../apps/api/app/middleware/classifier_gateway.py#L35) is route-specific masking, not deny-by-default structured log hashing. | AUD-032-009 |
| FR-O06 | PARTIAL | [SLO definitions](../../docs/observability/slo.md#L19) exist; independent dead-letter objective and sound window/budget calculations are incomplete. | AUD-032-022 |
| FR-O07 | PARTIAL | [API exporter](../../apps/api/app/main.py#L12) exists, but [custom spans](../../apps/agents/common/otel_telemetry.py#L78) stay in memory and contract attributes/trace continuation are incomplete. | AUD-032-021 |
| FR-O08 | MISSING | [Two available Workbooks](../../infra/modules/workbooks/executive-governance.json#L4) do not author incident activation, recommendation-publication and degraded-mode operator views. | AUD-032-022 |
| FR-O09 | PARTIAL | [SLO tiers](../../docs/observability/slo.md#L7) are prose; [generic Action Group](../../infra/modules/monitoring.bicep#L50) has no P1-P5 routing/issue action. | AUD-032-022 |
| FR-O10 | CONFLICT | [Five locations](../../infra/modules/availability-tests.bicep#L28) include a US location; tests are not composed into main. | AUD-032-022 |
| FR-AI01 | PARTIAL | [Hybrid implementation](../../apps/agents/common/retrieval_client.py#L846) and nine metadata-only records exist; active dispatcher bypasses retrieval, licence defaults and capacity alert are wrong. | AUD-032-002, AUD-032-013 |
| FR-AI02 | PARTIAL | [Inference audit builder](../../apps/agents/common/audit.py#L150) carries some model fields, not prompt-version/full persisted recommendation provenance. | AUD-032-007 |
| FR-AI03 | CONFLICT | [Phi ADR](../../docs/corpus/aidr/decisions/adr-033-phi-shadow-boundary.md#L22) requires non-AU carve-out but newer registry validator is AU-only; no explicit Phi retirement or connected shadow store. | AUD-032-014 |
| FR-AI03a | PARTIAL | [Registry validator](../../scripts/verify-carveout.ps1#L124) optionally checks resource inventory, but CD omits it and OPA/schema are not executed. | AUD-032-015 |
| FR-AI04 | MISSING | [Optional validation](../../apps/agents/common/llm_mixin.py#L134) and all seven schema-less production call sites do not enforce the universal requirement. | AUD-032-017 |
| FR-AI05 | PARTIAL | [Prompt README](../../packages/prompts/README.md#L54) authors cadence/owner/version rules; no actual templates/loader/history exist in that library. | AUD-032-016 |
| FR-AI06 | CONFLICT | [Foundry public account](../../infra/main.bicep#L954), public Search and unconnected Content Safety PE do not establish all three private data planes. | AUD-032-002 |
| FR-AI07 | PARTIAL | [Rollback runbook](../../docs/operator-runbooks/model-rollback.md#L16) exists but references old aliases and unavailable provenance/validation paths. | AUD-032-028, AUD-032-031 |
| FR-AI08 | PARTIAL | [Quota guide](../../docs/operator-runbooks/aoai-quota.md#L7) documents paths but stale quotas/aliases and unsupported guaranteed response times require correction. | AUD-032-028 |
| FR-AI09 | PARTIAL | [Signing workflow](../../.github/workflows/prompts-publish.yml#L32) does not persist usable release signatures and CD does not verify. | AUD-032-016 |
| FR-AI10 | MISSING | [CD](../../.github/workflows/cd.yml#L237) lacks candidate model-version canary; [accepted cutover ADR](../../docs/decisions/036-foundry-rag-grounding/20-hard-cutover-foundry-foundation.md#L5) does not retire future model-version safety gates. | AUD-032-031 |
| FR-AG01 | PARTIAL | [Decision rights](../../docs/agents/decision-rights.md#L7) covers six original agents but not all current runtime roles or measurable delegated thresholds. | AUD-032-006, AUD-032-030 |
| FR-AG02 | PARTIAL | [Evaluator](../../apps/agents/common/lifecycle/autonomy_eval.py#L67) is unconsumed; repository/loader/env defaults are unsafe/incomplete. | AUD-032-004, AUD-032-006 |
| FR-AG03 | PARTIAL | [Recommendation](../../packages/domain/src/domain/models/recommendation.py#L13) has signals/confidence but lacks decision threshold/context trace and query UI. | AUD-032-007 |
| FR-AG04 | IMPLEMENTED | [README entry](../../README.md#L185) names Dependency Notifier as first-class; path/count corrections remain documentation debt. | AUD-032-028 |
| FR-AG05 | PARTIAL | [Local watcher](../../apps/agents/common/lifecycle/killswitch.py#L107) lacks push/drain/expiry and [spike](../../docs/spikes/T016-killswitch-propagation.md#L5) defers P99 validation. | AUD-032-005 |
| FR-AG05a | MISSING | [Registered agent router](../../apps/api/app/api/routes/agents.py#L24) has neither governed control; contract scopes alone do not authenticate or approve. | AUD-032-004 |
| FR-AG06 | MISSING | [MAF workflow](../../apps/agents/maf_runtime/workflow/builder.py#L89) is not a configuration-generated full-flow stateDiagram-v2. | AUD-032-034 |
| FR-AG07 | MISSING | [Approval service](../../apps/api/app/services/recommendation_service.py#L11) has no outcome-to-eval feedback writer. | AUD-032-035 |
| FR-AG08 | PARTIAL | [HandoffStep](../../packages/domain/src/domain/models/handoff_chain.py#L22) has no timeout and legacy helper uses uniform two-second attempts. | AUD-032-034 |
| FR-AG09 | MISSING | [Recommendation model](../../packages/domain/src/domain/models/recommendation.py#L7) has no consensus ID and no matching detector/store found. | AUD-032-036 |
| FR-AG10 | PARTIAL | [Preparedness gaps](../../apps/api/app/services/rehearsal_orchestrator.py#L26) are not every run's actual timeouts/dead-letter/consensus summary. | AUD-032-036 |
| FR-S01 | CONFLICT | [Cosmos account](../../infra/main.bicep#L587) is public with Azure-services wildcard despite production restriction flag. | AUD-032-002 |
| FR-S02 | PARTIAL | [Proposed staged ADR](../../docs/corpus/aidr/decisions/adr-032-oidc-supersession.md#L22) exists; main auth remains JSON. | AUD-032-031 |
| FR-S02a | PARTIAL | [ADR status](../../docs/corpus/aidr/decisions/adr-032-oidc-supersession.md#L5) is Proposed, not approved supersession with approver identities. | AUD-032-031 |
| FR-S02b | UNVERIFIED | [CD auth](../../.github/workflows/cd.yml#L81) is not migrated; no seven-day prerequisite or sequential environment soak/approval records establish rollout. | AUD-032-031 |
| FR-S03 | CONFLICT | [CodeQL](../../.github/workflows/codeql.yml#L3) is disabled and manual-only, despite Python/JS matrix; unsupported language coverage needs explicit alternative. | AUD-032-020 |
| FR-S04 | PARTIAL | [Defender](../../infra/modules/defender.bicep#L9)/[Sentinel](../../infra/modules/sentinel.bicep#L36) are uncomposed and lack connected diagnostic/action policy feeds. | AUD-032-023 |
| FR-S05 | PARTIAL | [Cosmos key](../../infra/modules/cosmos-cmk.bicep#L33) is authored; root Cosmos/Storage are not CMK-bound. | AUD-032-003 |
| FR-R01 | PARTIAL | [CI benchmark](../../.github/workflows/ci.yml#L147) no longer continues on error, but [hook](../../tests/benchmark/conftest.py#L87) suppresses regression failure in CI and lacks p95/memory gating. | AUD-032-026 |
| FR-R02 | PARTIAL | [Nightly runner](../../.github/workflows/nightly-load.yml#L44) swallows load-test failure and does not measure target workload; same obligation as FR-T05. | AUD-032-026 |
| FR-R03 | PARTIAL | [Capacity model](../../docs/architecture/capacity-model.md#L24) is authored but source-inconsistent and missing evidence-backed per-agent incident budget. | AUD-032-029 |
| FR-R04 | PARTIAL | Root caps exist; [imported MAF containers](../../infra/bicep/modules/cosmos-workflow.bicep#L34) have no caps, and several promised runtime containers are unprovisioned. | AUD-032-029 |
| FR-R05 | PARTIAL | [Chaos module](../../infra/modules/chaos-studio.bicep#L91)/schedule exist; no composed fault/RBAC/SLO exercise and terminal failures are not enforced. | AUD-032-025 |
| FR-C01 | PARTIAL | [Simplified CD](../../.github/workflows/cd.yml#L19) and legacy deletion are present; 031 remains Draft. [Staging SLI gate](../../.github/workflows/staging-promotion.yml#L9) explicitly is not a deployer, and CD does not require its result. | AUD-032-030, AUD-032-031 |
| FR-C02 | CONFLICT | [Progressive delivery matrix](../../docs/ci-cd/progressive-delivery.md#L19) lists gates/soaks absent from actual CD. | AUD-032-031 |
| FR-C03 | PARTIAL | Full workflow inventory: 20/112 active refs use tags, e.g. [CI](../../.github/workflows/ci.yml#L417). | AUD-032-020 |
| FR-C04 | PARTIAL | [DORA collector](../../scripts/dora_metrics_publish.py#L93) is mis-scoped; manual-only publication and no dedicated bound dashboard. | AUD-032-027 |
| FR-C05 | CONFLICT | [0.0.0.0 rule](../../infra/main.bicep#L147) remains; same concrete violation as FR-S01. | AUD-032-002 |
| FR-D01 | PARTIAL | [DR runbook](../../docs/operator-runbooks/dr-bcp.md#L19) authors correct clocks/targets, but actual secondary workload/RPO is not exercised. | AUD-032-024 |
| FR-D02 | PARTIAL | [Docker inputs](../../apps/agents/Dockerfile#L1) and all other bases are tag-only; [root images](../../infra/main.bicep#L91) default to latest, update inventory incomplete. | AUD-032-020 |
| FR-D03 | PARTIAL | [Cost template](../../docs/operator-runbooks/cost-reporting.md#L5) exists; active budget path never produces its required durable AUD metrics. | AUD-032-012, AUD-032-028 |
| FR-D04 | PARTIAL | [Continuous backup](../../infra/main.bicep#L594) is implemented; [restore instructions](../../docs/operator-runbooks/cosmos-backup-restore.md#L32) contain an unavailable helper/check. | AUD-032-024 |
| FR-D05 | PARTIAL | [Cadence](../../docs/disaster-response-hub/evaluation/exercise-schedule.md#L9) is authored with conflicting dates; full-cycle outcomes unverified. | AUD-032-025 |
| FR-DOC01 | MISSING | [README](../../README.md#L275) has no video link after media/link inventory. | AUD-032-028 |
| FR-DOC02 | PARTIAL | [API Swagger](../../apps/api/app/main.py#L30) exists; no web /api-docs publisher of the committed OpenAPI YAML. | AUD-032-028 |
| FR-DOC03 | PARTIAL | [Hub](../../docs/governance-hub/index.md#L9) is present but broken and not a single canonical top-level navigation. | AUD-032-028 |
| FR-DOC04 | IMPLEMENTED | [Contributor document](../../CONTRIBUTING.md#L14) authors branch and spec workflow; technical gate claims need updating. | AUD-032-028 |
| FR-DOC05 | IMPLEMENTED | [Changelog](../../CHANGELOG.md#L91) records 032 as in-progress; not a claim of completed implementation. | AUD-032-028 |

### Success Criteria

| Criterion | Status | Evidence and required outcome distinction | Follow-up |
| --- | --- | --- | --- |
| SC-001 | CONFLICT | [Rubric](../../AMA_Rubric_Asia.md#L55) says 60 total while its 14 criteria imply 70; spec claims 16 dimensions/80. No independent evidence-backed regrade. No score is assigned by this audit. | AUD-032-030 |
| SC-002 | UNVERIFIED | [Recommendation model](../../packages/domain/src/domain/models/recommendation.py#L7) and missing why-fired endpoint/panel cannot establish complete provenance or <30-second reviewer timing. | AUD-032-007, AUD-032-008 |
| SC-003 | UNVERIFIED | [Root public settings](../../infra/main.bicep#L587) contradict desired posture; no trustworthy paired external/internal probe records. | AUD-032-002 |
| SC-004 | UNVERIFIED | [SLO catalogue](../../docs/observability/slo.md#L31) names 99.5/99.9% but no complete rolling 30-day metric window exists in inspected evidence. | AUD-032-021, AUD-032-022 |
| SC-005 | UNVERIFIED | [Dataset manifest](../../packages/eval-dataset/data/dataset-disaster-core-1.0.0/manifest.json#L1) and mocked eval tests are not approved 5,000-case measured model scorecards. | AUD-032-018 |
| SC-006 | UNVERIFIED | [Drill](../../.github/workflows/dr-drill.yml#L58) lacks end-to-end RPO/RTO measurement; no staged failover record meeting both targets. | AUD-032-024 |
| SC-007 | UNVERIFIED | [Hub links](../../docs/governance-hub/index.md#L9) are broken, video/web API-docs incomplete, and no first-time reviewer timing record. | AUD-032-028 |
| SC-008 | PARTIAL | [Format gate](../../.github/workflows/ci.yml#L112)/secret scan exist; strict/coverage/CodeQL/pin guard gaps permit unsupported green states. | AUD-032-001, AUD-032-019, AUD-032-020 |
| SC-009 | UNVERIFIED | [Generic alerts](../../infra/modules/monitoring.bicep#L76) do not enforce all required burn/page clocks, and no timed detect/page evidence is supplied. | AUD-032-022, AUD-032-025 |
| SC-010 | UNVERIFIED | [Schedule](../../docs/disaster-response-hub/evaluation/exercise-schedule.md#L19) is not a completed full cycle of published rehearsal/chaos outcomes. | AUD-032-025, AUD-032-030 |

## Acceptance Scenario Coverage

Every numbered Given/When/Then scenario in the eight user stories is covered separately. USn.m is an audit label for
the original story/scenario ordinal, not a newly invented source requirement. Scenario results refer to source support, not executed tests.

| Scenario | Status | Expected behavior versus controlling source/test evidence | Follow-up |
| --- | --- | --- | --- |
| US1.1 | PARTIAL | >=50-event why-fired panel must show full provenance and hash; [Recommendation](../../packages/domain/src/domain/models/recommendation.py#L7) only has partial inputs/confidence and no panel/segment link. | AUD-032-007, AUD-032-008 |
| US1.2 | MISSING | Tamper must block publication and page auditor; [audit append](../../apps/api/app/repositories/audit_repository.py#L85) does not verify a chain or quarantine publication. | AUD-032-008 |
| US1.3 | PARTIAL | All emitted PII must be hash-redacted; [request masker](../../apps/api/app/middleware/classifier_gateway.py#L35) is not the log sink. | AUD-032-009 |
| US2.1 | CONFLICT | Public production data-plane requests must be rejected/logged; [Cosmos/Storage](../../infra/main.bicep#L493) remain public and Content Safety lacks internal PE path. | AUD-032-002 |
| US2.2 | CONFLICT | CD must use OIDC with ADR in summary and no JSON secret; [CD login](../../.github/workflows/cd.yml#L95) uses credentials JSON. | AUD-032-031 |
| US2.3 | PARTIAL | Zero tag refs required; 20 active tag refs remain, including [CI](../../.github/workflows/ci.yml#L417). | AUD-032-020 |
| US2.4 | CONFLICT | Push SAST/PR summary required; [CodeQL](../../.github/workflows/codeql.yml#L35) only echoes unavailability and Bicep uses a separate scanner. | AUD-032-020 |
| US3.1 | PARTIAL | A single traceId must span web/API/ingestion/agents/LLM; [recorder-only spans](../../apps/agents/common/otel_telemetry.py#L78) do not provide distributed trace export. | AUD-032-021 |
| US3.2 | PARTIAL | 50% monthly burn must open issue and notify webhook; [generic alerts](../../infra/modules/monitoring.bicep#L76) do neither burn-specific computation nor issue creation. | AUD-032-022 |
| US3.3 | PARTIAL | Six live tiles required; [executive template](../../infra/modules/workbooks/executive-governance.json#L4) lacks ingestion/governance/active-incident coverage and root binding. | AUD-032-022 |
| US3.4 | PARTIAL | Log redaction plus real cost customMetrics required; [active budget](../../apps/agents/common/llm_mixin.py#L47) warns only. | AUD-032-009, AUD-032-012, AUD-032-021 |
| US4.1 | PARTIAL | Retrieved AIDR chunks/citations required; [shared retrieval](../../apps/agents/common/retrieval_client.py#L846) exists but [dispatcher](../../apps/agents/dispatcher/agent.py#L215) bypasses it. | AUD-032-013 |
| US4.2 | UNVERIFIED | Completed approved-v1 baseline scorecards required; [fake Foundry test](../../tests/unit/eval/test_orchestrator_e2e.py#L89) is not that outcome. | AUD-032-018 |
| US4.3 | PARTIAL | At 80% daily budget persist warning and degrade; [tracker](../../apps/agents/common/llm_budget_tracker.py#L196) is unconsumed/monthly and no active degradation gate exists. | AUD-032-012 |
| US4.4 | MISSING | Phi side-by-side record and comparison metric required; [MAF shadow](../../apps/agents/maf_runtime/agents/_factory.py#L298) is different runtime comparison, not a Phi record. | AUD-032-014 |
| US5.1 | MISSING | Two agents on same corridor must emit/surface consensus_event; [Recommendation](../../packages/domain/src/domain/models/recommendation.py#L7) has no consensus path. | AUD-032-036 |
| US5.2 | PARTIAL | Low autonomy requires life-safety approval and audited policy; [dial](../../apps/agents/common/lifecycle/autonomy_eval.py#L49) disallows autonomous life safety locally but is not connected to decisions. | AUD-032-004, AUD-032-006 |
| US5.3 | PARTIAL | Engaged kill-switch must select templates/header/badge; [local state](../../apps/agents/common/lifecycle/killswitch.py#L55) is never consumed by actual dispatcher gates. | AUD-032-005 |
| US5.4 | PARTIAL | AAR needs timeouts, DLQ cycles and consensus; [preparedness summary](../../apps/api/app/services/rehearsal_orchestrator.py#L26) contains organisation-analysis gaps instead. | AUD-032-036 |
| US6.1 | PARTIAL | Regression must fail pipeline; [benchmark hook](../../tests/benchmark/conftest.py#L87) explicitly skips regression failure in CI. | AUD-032-026 |
| US6.2 | PARTIAL | Nightly load results/regression issue required; [runner](../../.github/workflows/nightly-load.yml#L44) suppresses failures and only emits completed counter. | AUD-032-026 |
| US6.3 | UNVERIFIED | Actual AU Southeast traffic recovery within RTO/logged; [drill](../../.github/workflows/dr-drill.yml#L75) checks the same URL and lacks regional transaction proof. | AUD-032-024 |
| US6.4 | PARTIAL | Four monthly DORA stats visible; [doc](../../docs/ci-cd/dora-metrics.md#L30) defers Workbook and [collector](../../scripts/dora_metrics_publish.py#L93) mixes incidents. | AUD-032-027 |
| US7.1 | IMPLEMENTED | [Forbidden import contract](../../pyproject.toml#L108) and [blocking CI step](../../.github/workflows/ci.yml#L121) implement the gate; no actual gate run is claimed. | AUD-032-001 |
| US7.2 | IMPLEMENTED | [Blocking format command](../../.github/workflows/ci.yml#L112) checks all required source roots. | - |
| US7.3 | PARTIAL | [Combined coverage](../../.github/workflows/ci.yml#L132) is mislabeled as unit and missing baseline paths can pass. | AUD-032-019 |
| US7.4 | PARTIAL | [Pre-commit mypy](../../.pre-commit-config.yaml#L26) omits tests and does not mirror complete CI. | AUD-032-001 |
| US8.1 | MISSING | [README](../../README.md#L275) has no required 60-second video link. | AUD-032-028 |
| US8.2 | CONFLICT | Original scenario requests /api/docs; later SC-007/task T902 requests /api-docs; [FastAPI](../../apps/api/app/main.py#L30) renders runtime JSON, not live committed YAML in the web app. | AUD-032-028, AUD-032-030 |
| US8.3 | PARTIAL | [Consolidated nav](../../docs/governance-hub/index.md#L9) exists but broken links and separate entrypoints defeat single-hub discovery. | AUD-032-028 |

### Independent Story Tests

| Story obligation | Status | Source/test evidence limits | Follow-up |
| --- | --- | --- | --- |
| US1-I | PARTIAL | [Audit test](../../tests/integration/test_human_approval_preserved.py#L36) manually supplies approval fields; no stored ScenarioRun proof of provenance and chain. | AUD-032-007, AUD-032-008 |
| US2-I | UNVERIFIED | [Root settings](../../infra/main.bicep#L587) contradict private posture; no public/internal probe execution or CMK/OIDC deployed proof. | AUD-032-002, AUD-032-003, AUD-032-031 |
| US3-I | UNVERIFIED | [Synthetic definitions](../../infra/modules/availability-tests.bicep#L42) are unbound; no one-minute dashboard/seven-day availability/full-trace/error-budget evidence. | AUD-032-021, AUD-032-022 |
| US4-I | PARTIAL | Full dataset exists but [approval chains](../../packages/eval-dataset/data/dataset-disaster-core-1.0.0/cases.jsonl#L1), [schemas](../../apps/agents/common/llm_mixin.py#L134) and restart budget fail required proof. | AUD-032-012, AUD-032-017, AUD-032-018 |
| US5-I | PARTIAL | [MAF flow](../../apps/agents/maf_runtime/workflow/builder.py#L89) is not a complete state-generated Saga; kill-switch and every transition audit absent. | AUD-032-005, AUD-032-034, AUD-032-036 |
| US6-I | UNVERIFIED | [031 Draft](../031-simplify-cicd-pipeline/spec.md#L5) and unmeasured [drill](../../.github/workflows/dr-drill.yml#L58) block the full independent-test claim. | AUD-032-024, AUD-032-026, AUD-032-031 |
| US7-I | PARTIAL | [Strict grace](../../.github/workflows/ci.yml#L116), missing coverage baseline and retained flat modules defeat deliberate-violation/move verification. | AUD-032-001, AUD-032-010, AUD-032-019 |
| US8-I | UNVERIFIED | [README entrypoints](../../README.md#L275) and [hub](../../docs/governance-hub/index.md#L9) lack the complete seven-artifact navigation; no timed reviewer evidence. | AUD-032-028 |

### Edge Cases

| Edge case | Status | Expected behavior and controlling evidence | Follow-up |
| --- | --- | --- | --- |
| EC-01 Regional failover during incident | PARTIAL | PITR exists, but [single Cosmos region](../../infra/main.bicep#L589) and absent audit chain cannot establish continuity plus idempotent reconstruction. | AUD-032-008, AUD-032-024 |
| EC-02 OpenAI private endpoint outage | PARTIAL | [Fallback contract](../../tests/contract/test_llm_fallback.py#L4) only checks generation_method; no all-agent AWS level/action fidelity assertion under private endpoint outage. | AUD-032-011, AUD-032-017 |
| EC-03 Eval blocks mid-incident | MISSING | [Eval gate](../../.github/workflows/eval-pr-gate.yml#L3) lacks one-time incident bypass with authenticated executive approval/audit; a bypass mention is not enforcement. | AUD-032-018 |
| EC-04 OIDC propagation lag | MISSING | [JSON-secret login](../../.github/workflows/cd.yml#L95) has no federated identity preflight; ADR fallback conflicts with no silent fallback. | AUD-032-031 |
| EC-05 Redaction false negatives | MISSING | [Taxonomy](../../docs/safety/classification-taxonomy.md#L13) describes redaction; no periodic canary log validator/job/alert found. | AUD-032-009 |
| EC-06 High-severity kill-switch | PARTIAL | [Watcher](../../apps/agents/common/lifecycle/killswitch.py#L107) has no production gate, explicit operator badge/notice or alternate workflow. | AUD-032-005 |
| EC-07 Emergency CodeQL false positive | MISSING | [CodeQL](../../.github/workflows/codeql.yml#L3) is disabled; no bounded security-bypass label with Principal/Security co-approval and audit found. | AUD-032-020 |
| EC-08 Connectivity-degraded field | PARTIAL | [Queue drain](../../apps/web/src/lib/offline/queue-store.ts#L216) deletes before [HTTP acknowledgement](../../apps/web/src/app/workspaces/[personaId]/_panels/field-coordinator-offline.tsx#L93); cached COP/replay is not guaranteed. | AUD-032-032 |
| EC-09 Cross-jurisdiction language fallback | PARTIAL | [Resolver](../../apps/web/src/lib/i18n/language-packs.ts#L150) returns one English fallback, not English plus approved configured alternative with PIO gap notice. | AUD-032-033 |

## Review And Checklist Evidence

These are assessments of the original review questions/claims, not edits or retrospective check-offs. All 75 rubric checklist
states remain `[ ]`; the 16 unnamed quality items retain `[x]` and receive audit labels Q01-Q16 in source order.
IMPLEMENTED in this section can mean an explicitly authored answer to a requirements-quality question; it does not certify the runtime.

### Rubric Checklist

| Item | Original state | Status | Inspected answer, gap or evidence limitation | Follow-up |
| --- | --- | --- | --- | --- |
| CHK001 | [ ] | PARTIAL | [Decision rights](../../docs/agents/decision-rights.md#L7) covers six agents, not all current roles or every measurable delegated limit. | AUD-032-006, AUD-032-030 |
| CHK002 | [ ] | PARTIAL | [Kill-switch contract](contracts/openapi-delta.yaml#L87) names P99/metric but [spike](../../docs/spikes/T016-killswitch-propagation.md#L5) lacks all-process measurements/identity inventory. | AUD-032-005 |
| CHK003 | [ ] | PARTIAL | [Key module](../../infra/modules/cosmos-cmk.bicep#L44) defines rotation, not composed vault network/recovery/access policy. | AUD-032-003 |
| CHK004 | [ ] | IMPLEMENTED | [OTel contract](contracts/otel-attributes.yaml#L5) enumerates resource/span/LLM attributes; actual export is independently partial. | AUD-032-021 |
| CHK005 | [ ] | IMPLEMENTED | [Catalogue convention](../../docs/observability/metrics-catalogue.md#L5) quantifies audit/eval 2555, operations 90 and security 365 days; Bicep does not enforce them. | AUD-032-022 |
| CHK006 | [ ] | PARTIAL | [Citation model](../../packages/domain/src/domain/models/rag_citation.py#L17) defines fields/quote limit but no full source-confidence/no-result contract or <=1 score bound. | AUD-032-013 |
| CHK007 | [ ] | PARTIAL | [Spec edge cases](spec.md#L164) call for notice/badge/guidance without a connected kill-switch UX. | AUD-032-005 |
| CHK008 | [ ] | IMPLEMENTED | [Import contracts](../../pyproject.toml#L104) enumerate agents/API, ingestion/API and domain/apps constraints. | AUD-032-001 |
| CHK009 | [ ] | IMPLEMENTED | [Prompt review rules](../../packages/prompts/README.md#L54) specify quarterly review and maximum six-month due date. | AUD-032-016 |
| CHK010 | [ ] | IMPLEMENTED | [DORA definitions](../../docs/ci-cd/dora-metrics.md#L7) identify workflow runs, commits and incidents; incorrect calculation tracked separately. | AUD-032-027 |
| CHK011 | [ ] | MISSING | [Degraded-mode requirement](spec.md#L164) gives no RTT/packet-loss operating envelope for the field path. | AUD-032-032, AUD-032-030 |
| CHK012 | [ ] | PARTIAL | [SLO-2](../../docs/observability/slo.md#L31) gives depth >=100 but no per-queue age threshold/objective. | AUD-032-022 |
| CHK013 | [ ] | PARTIAL | [E-05](data-model.md#L73) names >=2 agents, score and window fields, but no operational agreement/window thresholds or detector. | AUD-032-036 |
| CHK014 | [ ] | PARTIAL | [SLO window](../../docs/observability/slo.md#L31) says 30 days, but composed alert evaluation and denominator do not implement it. | AUD-032-022 |
| CHK015 | [ ] | MISSING | [Rehearsal summary](../../apps/api/app/services/rehearsal_orchestrator.py#L26) is string gaps, not a schema for runtime timeouts/DLQ/consensus. | AUD-032-036 |
| CHK016 | [ ] | CONFLICT | [Research R-10](research.md#L87) names AU/NZ/Singapore/Tokyo while [Bicep](../../infra/modules/availability-tests.bicep#L28) includes San Jose. | AUD-032-022 |
| CHK017 | [ ] | PARTIAL | [Decision rights](../../docs/agents/decision-rights.md#L68) names executive/engineer co-approval, but no authenticated eval-bypass mechanism. | AUD-032-018 |
| CHK018 | [ ] | PARTIAL | [Ratchet tracker](coverage-phase-tracker.md#L5) names three tiers; CI merges two, omits unit and does not document ancillary-tier measurement treatment accurately. | AUD-032-019 |
| CHK019 | [ ] | PARTIAL | [ADR-032](../../docs/corpus/aidr/decisions/adr-032-oidc-supersession.md#L3) links the old ADR but remains Proposed with no recorded approval/superseded status workflow. | AUD-032-031 |
| CHK020 | [ ] | PARTIAL | [Mixin validation failure](../../apps/agents/common/llm_mixin.py#L134) falls back, but only when optional response_model is supplied. | AUD-032-017 |
| CHK021 | [ ] | IMPLEMENTED | [T803](tasks.md#L164) owns nightly load once for FR-T05/FR-R02; separate FR rows preserved here. | AUD-032-026 |
| CHK022 | [ ] | IMPLEMENTED | [T401](tasks.md#L88) owns Cosmos network replacement once for FR-S01/FR-C05. | AUD-032-002 |
| CHK023 | [ ] | IMPLEMENTED | [Autonomy defaults](../../apps/agents/common/lifecycle/autonomy_eval.py#L31) and [disengaged switch](../../apps/agents/common/lifecycle/killswitch.py#L55) are individually stated; production wiring remains incomplete. | AUD-032-005, AUD-032-006 |
| CHK024 | [ ] | IMPLEMENTED | [Task sequencing](tasks.md#L53) makes SHA pinning independent of OIDC stage; current pins are incomplete. | AUD-032-020 |
| CHK025 | [ ] | IMPLEMENTED | [Shadow/cost catalogue retention](../../docs/observability/metrics-catalogue.md#L46) matches authored seven-year eval retention; not deployed proof. | AUD-032-014, AUD-032-022 |
| CHK026 | [ ] | CONFLICT | [ADR-036 table](../../docs/corpus/aidr/decisions/adr-036-aisearch-rag.md#L20) permits paired read-only index failover, conflicting with its own no-replication clause/spec. | AUD-032-013, AUD-032-030 |
| CHK027 | [ ] | CONFLICT | [Rubric guide](../../AMA_Rubric_Asia.md#L55) and SC-001 have incompatible totals/categories; no inspected independent 80/80 assessment. | AUD-032-030 |
| CHK028 | [ ] | PARTIAL | [Phi boundary ADR](../../docs/corpus/aidr/decisions/adr-033-phi-shadow-boundary.md#L11) distinguishes endpoint carve-out, but newer AU-only validator conflicts with intended Phi path. | AUD-032-014, AUD-032-015 |
| CHK029 | [ ] | PARTIAL | [CodeQL languages](../../.github/workflows/codeql.yml#L26) name Python/JS; analysis disabled, Bicep/PowerShell scanner responsibilities not coherently declared. | AUD-032-020 |
| CHK030 | [ ] | PARTIAL | [Workbook tasks](tasks.md#L115) distinguish executive/cost/flow, but no full operator-runbook view ownership/content is implemented. | AUD-032-022 |
| CHK031 | [ ] | PARTIAL | [SC-002](spec.md#L326) gives <30 seconds but no implemented panel or reproducible start/stop reviewer protocol. | AUD-032-007, AUD-032-030 |
| CHK032 | [ ] | PARTIAL | [SLO-10](../../docs/observability/slo.md#L112) defines 24 hours, not full probe population/source identity/internal success control. | AUD-032-002, AUD-032-022 |
| CHK033 | [ ] | PARTIAL | [SLO catalogue](../../docs/observability/slo.md#L31) names metrics, but current producers/alerts differ and no complete metric-ID binding exists. | AUD-032-021, AUD-032-022 |
| CHK034 | [ ] | PARTIAL | [GateThresholds](../../apps/eval-runner/src/ama_eval/gate.py#L17) is numeric but missing metrics pass and the specified complete baseline families are not enforced. | AUD-032-018 |
| CHK035 | [ ] | PARTIAL | [Reviewer smoke](../../apps/web/e2e/operator-journey.spec.ts#L18) accepts 404 and never proves navigation/time-to-artifact. | AUD-032-028 |
| CHK036 | [ ] | PARTIAL | [SC-009](spec.md#L333) defines detection/page targets, but no authoritative event clocks or all-SLI measured fixture chain. | AUD-032-022 |
| CHK037 | [ ] | IMPLEMENTED | [US1 scenarios](spec.md#L45) are externally observable panel/tamper/redaction requirements; no execution evidence implied. | AUD-032-007, AUD-032-008, AUD-032-009 |
| CHK038 | [ ] | PARTIAL | [SLO-10](../../docs/observability/slo.md#L112) adds a window, but US2 probe count/credentials/location sampling is unresolved. | AUD-032-002 |
| CHK039 | [ ] | PARTIAL | [E-05](data-model.md#L73) is an authored event shape only; no audit-timeline consensus linkage. | AUD-032-036 |
| CHK040 | [ ] | PARTIAL | [Runbook clocks](../../docs/operator-runbooks/dr-bcp.md#L19) are clear; workflow emits neither a complete RPO/RTO record nor monthly DORA join evidence. | AUD-032-024, AUD-032-027 |
| CHK041 | [ ] | CONFLICT | [ADR fallback](../../docs/corpus/aidr/decisions/adr-032-oidc-supersession.md#L37) retains secrets during soak while edge case prohibits silent fallback. | AUD-032-031 |
| CHK042 | [ ] | PARTIAL | [Retrieval failure](../../apps/agents/common/retrieval_client.py#L796) returns no hits; actual dispatcher/degraded header/template fidelity is not end-to-end. | AUD-032-013 |
| CHK043 | [ ] | PARTIAL | [Signing manifest](../../packages/prompts/cosign.manifest.yaml#L24) declares block/page; CD has no verifier and bypass roles differ among docs. | AUD-032-016 |
| CHK044 | [ ] | MISSING | [Capacity model](../../docs/architecture/capacity-model.md#L24) targets operators, not concurrent Workbook query/tile loads. | AUD-032-022, AUD-032-029 |
| CHK045 | [ ] | PARTIAL | [Fail-back procedure](../../docs/operator-runbooks/dr-bcp.md#L92) exists but assumes unavailable topology and lacks interrupted-recovery reconciliation. | AUD-032-024 |
| CHK046 | [ ] | PARTIAL | [Availability retries](../../infra/modules/availability-tests.bicep#L57) exist; suppression/page routing is uncomposed. | AUD-032-022 |
| CHK047 | [ ] | PARTIAL | [Unknown environment handling](../../apps/agents/common/lifecycle/autonomy_eval.py#L84) falls back to dev/high instead of safe failure. | AUD-032-006 |
| CHK048 | [ ] | PARTIAL | [Spike risks](../../docs/spikes/T016-killswitch-propagation.md#L43) propose fallback/widening but no implemented lag recovery or authorized SLO change. | AUD-032-005 |
| CHK049 | [ ] | PARTIAL | [E-03](data-model.md#L34) requires publish-block/page; implementation is absent. | AUD-032-008 |
| CHK050 | [ ] | PARTIAL | [Shadow divergence metric](../../docs/observability/metrics-catalogue.md#L55) is listed, but there is no thresholded Phi comparison path. | AUD-032-014 |
| CHK051 | [ ] | PARTIAL | [Policy schema](contracts/jurisdiction-policy.schema.yaml#L20) declares ordered language priorities; runtime returns only one fallback. | AUD-032-006, AUD-032-033 |
| CHK052 | [ ] | MISSING | [Kill-switch state](../../apps/agents/common/lifecycle/killswitch.py#L35) lacks explicit high-severity incident audit tags/operator notification. | AUD-032-005 |
| CHK053 | [ ] | MISSING | [Disabled SAST](../../.github/workflows/codeql.yml#L3) has no security-bypass expiry/revocation mechanism. | AUD-032-020 |
| CHK054 | [ ] | PARTIAL | [SLO-3](../../docs/observability/slo.md#L41) defines publish latency but no enforced outage/fallback link to that SLI. | AUD-032-011, AUD-032-022 |
| CHK055 | [ ] | MISSING | [Spec edge cases](spec.md#L164) do not define degraded response-time guarantees relative to normal mode. | AUD-032-022, AUD-032-030 |
| CHK056 | [ ] | PARTIAL | [Plan accessibility position](plan.md#L60) mentions WCAG 2.2; no complete Workbook/API-docs AA assertions/evidence. | AUD-032-022, AUD-032-028 |
| CHK057 | [ ] | MISSING | [Governance hub](../../docs/governance-hub/index.md#L1) has no en-AU/CALD/ATSI localisation contract or corpus of translations. | AUD-032-028, AUD-032-033 |
| CHK058 | [ ] | PARTIAL | [SLO-8](../../docs/observability/slo.md#L92) defines <=400 ms retrieval, but end-to-end added latency and export are not verified. | AUD-032-013, AUD-032-021 |
| CHK059 | [ ] | PARTIAL | [Prompt ownership](../../packages/prompts/README.md#L31) is an example; no actual signed template/consumer or enforced editor/signer/deployer policy. | AUD-032-016 |
| CHK060 | [ ] | MISSING | [SLO catalogue](../../docs/observability/slo.md#L19) lacks independent Workbook/metrics-pipeline availability objectives. | AUD-032-022 |
| CHK061 | [ ] | PARTIAL | [Quota guide](../../docs/operator-runbooks/aoai-quota.md#L7) covers stale model quotas, not confirmed Search/Chaos/Sentinel capacity prerequisites. | AUD-032-023, AUD-032-025, AUD-032-029 |
| CHK062 | [ ] | PARTIAL | [Research R-17](research.md#L115) offers Loom/Storage fallback, not an approved service/licence or published video. | AUD-032-028 |
| CHK063 | [ ] | PARTIAL | [030 status](../030-llm-eval-framework/spec.md#L5) is a promotion label; concrete framework/test/dataset prerequisites remain incomplete. | AUD-032-018 |
| CHK064 | [ ] | IMPLEMENTED | [Cross-stream prerequisite](plan.md#L227) explicitly gates OIDC on 031 merge, approval and green soak; actual satisfaction is unverified. | AUD-032-031 |
| CHK065 | [ ] | PARTIAL | [Identity note](T008-fr-i05-status.md#L21) specifies env/Bicep resolution but supplies no current provider identity/approval evidence. | AUD-032-031 |
| CHK066 | [ ] | CONFLICT | [Phi ADR](../../docs/corpus/aidr/decisions/adr-033-phi-shadow-boundary.md#L22) and [AU-only policy](../../infra/policy/rego/foundry_carveout.rego#L11) disagree without explicit Phi retirement. | AUD-032-014, AUD-032-015 |
| CHK067 | [ ] | PARTIAL | [Catalogue](../../docs/observability/metrics-catalogue.md#L3) claims runtime-registry ownership, but generic emitters/dynamic metrics are not reconciled to it. | AUD-032-021 |
| CHK068 | [ ] | PARTIAL | [Executive Workbook](../../infra/modules/workbooks/executive-governance.json#L4) lacks the named governance-health tile and source binding. | AUD-032-022 |
| CHK069 | [ ] | IMPLEMENTED | [Research R-19](research.md#L125) chooses a single nav with redirects preserving old hubs; actual links remain partial. | AUD-032-028 |
| CHK070 | [ ] | IMPLEMENTED | [Dev dependencies](../../pyproject.toml#L27) plus [contracts](../../pyproject.toml#L104) include import-linter as both tool and boundary specification. | AUD-032-001 |
| CHK071 | [ ] | CONFLICT | [Rubric](../../AMA_Rubric_Asia.md#L1), 1.1-17.5 labels, 75-item claim and 89 actual FRs are not one-to-one. | AUD-032-030 |
| CHK072 | [ ] | PARTIAL | [Traceability](traceability.md#L16) uses undeclared US-Arch/US-Impl and general US labels, not per-acceptance mapping for every FR. | AUD-032-030 |
| CHK073 | [ ] | PARTIAL | [Analysis SC mapping](analysis.md#L178) maps task surfaces, not complete FR/outcome evidence; rubric SC remains conflicted. | AUD-032-030 |
| CHK074 | [ ] | PARTIAL | [032 matrix](traceability.md#L5) exists but is scaffold/pending/complete-stub rather than complete requirement/test evidence. | AUD-032-030 |
| CHK075 | [ ] | IMPLEMENTED | [Foundation tasks/dependency graph](tasks.md#L24) lists ADRs and gating relations; no execution implied. | AUD-032-031, AUD-032-034 |

### Specification Quality Checklist

| Item | Original state | Status | Original claim and evidence assessment | Follow-up |
| --- | --- | --- | --- | --- |
| Q01 | [x] | IMPLEMENTED | Tool-specific constraints in [requirements](spec.md#L181) are explicitly rubric-mandated, consistent with the checklist's stated exception. | - |
| Q02 | [x] | IMPLEMENTED | [Eight user stories](spec.md#L34) lead with auditor/operator/executive/engineer/reviewer value. | - |
| Q03 | [x] | PARTIAL | Persona narratives are accessible, but [contracts/requirements](contracts/openapi-delta.yaml#L1) carry substantial implementation-specific detail. | AUD-032-030 |
| Q04 | [x] | IMPLEMENTED | [Spec](spec.md#L1) has scenarios, requirements, measurable outcomes and assumptions. | - |
| Q05 | [x] | IMPLEMENTED | [Both clarification passes](spec.md#L13) contain answers; no outstanding literal NEEDS CLARIFICATION marker is treated as a blocker. | - |
| Q06 | [x] | CONFLICT | [Rubric checklist](checklists/rubric.md#L11) still contains 75 unresolved questions and scope/contracts disagree. | AUD-032-030 |
| Q07 | [x] | PARTIAL | [SCs](spec.md#L325) provide numeric goals, but rubric denominator and timing/probe definitions are incomplete. | AUD-032-030 |
| Q08 | [x] | PARTIAL | Most SCs are outcomes; [SC-003/005/008](spec.md#L327) specify service/tool-specific gates and unresolved evidence protocols. | AUD-032-030 |
| Q09 | [x] | IMPLEMENTED | All eight stories have numbered acceptance scenarios; this report accounts for all 30. [Scenarios](spec.md#L34). | - |
| Q10 | [x] | IMPLEMENTED | [Edge-case section](spec.md#L164) explicitly lists all nine exceptional flows, though implementation is partial/missing. | - |
| Q11 | [x] | CONFLICT | 75 items/16 groups/~115 tasks disagree with actual 89 FRs/152 tasks and [rubric](../../AMA_Rubric_Asia.md#L55). | AUD-032-030 |
| Q12 | [x] | IMPLEMENTED | [Plan dependencies](plan.md#L227) explicitly name 031, PE-first, licence, carve-out and spike constraints. | - |
| Q13 | [x] | PARTIAL | [FR matrix](traceability.md#L16) has generic/undefined story labels rather than precise acceptance criteria for every FR. | AUD-032-030 |
| Q14 | [x] | IMPLEMENTED | [Stories](spec.md#L34) cover audit, security, observability, AI, coordination, delivery, hygiene and docs at requirements level. | - |
| Q15 | [x] | UNVERIFIED | Claim that feature meets SC outcomes has no independent score/SLO/drill/reviewer evidence; [session](SESSION-STATUS-2026-04-30.md#L106) defers review/deploy. | AUD-032-030 |
| Q16 | [x] | IMPLEMENTED | Same explicit rubric-tool exception as Q01 in [quality checklist](checklists/requirements.md#L30); not implementation proof. | - |

### Prior Analysis Claims

| Review item | Status | Fresh disposition | Follow-up |
| --- | --- | --- | --- |
| H1 | IMPLEMENTED | [Analysis](analysis.md#L28) correctly identifies separate S02a/S02b task labels; label correctness does not approve migration. | AUD-032-031 |
| H2 | IMPLEMENTED | [Analysis](analysis.md#L32) correctly maps AI03a to T017/T018/T412; actual deployment comparison remains partial. | AUD-032-015 |
| H3 | CONFLICT | [OpenAPI](contracts/openapi-delta.yaml#L70) only defines kill-switch, not autonomy POST, and atomicity/proposal semantics are unresolved. | AUD-032-004 |
| M1 | IMPLEMENTED | Nightly-load duplicate FRs are deliberately tracked by T803 in [tasks](tasks.md#L164). | AUD-032-026 |
| M2 | IMPLEMENTED | Private-Cosmos duplicate FRs are deliberately tracked by T401 in [tasks](tasks.md#L88). | AUD-032-002 |
| M3 | PARTIAL | Push mechanism is textually aligned, but [spike](../../docs/spikes/T016-killswitch-propagation.md#L5) defers measurement and local watcher is not a subscriber. | AUD-032-005 |
| M4 | PARTIAL | [Inventory](../../docs/corpus/aidr/LICENCE-INVENTORY.md#L16) is metadata-only; [ingest filter](../../apps/ingest-runner/src/ama_ingest/licence_filter.py#L33) defaults missing mode to full-text. | AUD-032-013 |
| M5 | PARTIAL | [WhyFired schema](contracts/openapi-delta.yaml#L215) names fields but omits required signal/threshold/trust data and prompt_version from required list. | AUD-032-007 |
| L1 | IMPLEMENTED | Video naming is a nonblocking prose issue; [README](../../README.md#L275) still lacks the actual video. | AUD-032-028 |
| L2 | PARTIAL | [Quickstart](quickstart.md#L62) is smoke guidance, not one-minute Workbook assertions. | AUD-032-022 |
| L3 | IMPLEMENTED | T020 stub then T903 consolidation is intentional in [tasks](tasks.md#L190); broken navigation still needs repair. | AUD-032-028 |
| L4 | PARTIAL | [README](../../README.md#L185) does add Dependency Notifier, but its directory/count is stale and later tasks do not prove correction. | AUD-032-028 |
| Analysis coverage conclusion | CONFLICT | [100% mapping claim](analysis.md#L176) includes planned filenames rather than tests and omits parent FR-S02; source-supported implementation is not 100%. | AUD-032-030 |
| Constitution pre/post gates | UNVERIFIED | [Plan gate](plan.md#L49) is a self-assessment; root public networks, missing control approval and absent chain contradict claimed enforcement. | AUD-032-002, AUD-032-004, AUD-032-008 |
| Session execution claims | UNVERIFIED | [Session summary](SESSION-STATUS-2026-04-30.md#L113) claims commits/lint/builds without immutable logs tied to the requested SHA; no reruns permitted. | AUD-032-030 |
| Stream-2 deferral | PARTIAL | [Explicit deferral](STREAM-2-DEFERRAL.md#L1) preserves future scope, not supersession; later helpers/tests do not complete the runtime migration. | AUD-032-010, AUD-032-011, AUD-032-012 |
| T008 deletion note | SUPERSEDED | [Explicit deletion](T008-fr-i05-status.md#L13) plus current path inventory retires named old files, not future identity validation. | AUD-032-031 |

## Design And Unnumbered Obligations

The labels in this section identify source sections, not new original requirement IDs. They account for the nonfunctional
constraints and embedded decisions that would otherwise be lost by reviewing only the 89 FR bullet labels.

### Clarifications And Scope Changes

| Source obligation | Status | Binding content and evidence disposition | Follow-up |
| --- | --- | --- | --- |
| Pass1-Q1 | PARTIAL | Two-stage OIDC, 031 first, then approved ADR-032; [ADR remains Proposed](../../docs/corpus/aidr/decisions/adr-032-oidc-supersession.md#L5), with no soak/approver records. | AUD-032-031 |
| Pass1-Q2 | CONFLICT | Binding 5,000 approved v1 cases conflicts with [Top-5 subset deferral](plan.md#L239); 5,000 authored labels do not supply safety approval. | AUD-032-018, AUD-032-030 |
| Pass1-Q3 | UNVERIFIED | RPO <=15 minutes/RTO <=60 minutes, Executive sign-off and drills: [runbook clocks](../../docs/operator-runbooks/dr-bcp.md#L19) authored, actual recovery/sign-off absent. | AUD-032-024 |
| Pass1-Q4 | MISSING | Phi shadow must persist seven years, queryable but hidden from operators; [current Recommendation](../../packages/domain/src/domain/models/recommendation.py#L7) has no shadow/parent fields. | AUD-032-014 |
| Pass1-Q5 | PARTIAL | 80/60/50 binding floors amended into documented A/B/C ratchet; [active A](coverage-phase-tracker.md#L7) is authored, actual cross-run/no-regression enforcement absent. | AUD-032-019 |
| Pass2-Q1 | PARTIAL | AIDR licence note, citation page and AU-East-only index; [pending nine-handbook inventory](../../docs/corpus/aidr/LICENCE-INVENTORY.md#L16) correctly withholds full-text approval. | AUD-032-013 |
| Pass2-Q2 | PARTIAL | Keyless cosign/Fulcio verification supersedes any ambiguous long-lived-key option; [manifest](../../packages/prompts/cosign.manifest.yaml#L6) is not a running verifier. | AUD-032-016 |
| Pass2-Q3 | CONFLICT | S1 1x1 prod/Basic dev, 1536-dim selection and 70% capacity alert: [new module](../../infra/modules/ai-search.bicep#L55) records 3072 evolution, while current alert uses SearchLatency. | AUD-032-013, AUD-032-030 |
| Pass2-Q4 | PARTIAL | dev/rehearsal high, staging/prod standard, jurisdiction overrides and restricted low: [evaluator](../../apps/agents/common/lifecycle/autonomy_eval.py#L31) not consumed; unknown env falls to dev. | AUD-032-006 |
| Pass2-Q5 | UNVERIFIED | All-process <=30-second kill-switch P99 including drain; [spike](../../docs/spikes/T016-killswitch-propagation.md#L5) explicitly defers prototype/results. | AUD-032-005 |
| Licence amendment | PARTIAL | Positive dual-signoff required per handbook; all current AIDR records metadata-only, but [missing-mode default](../../apps/ingest-runner/src/ama_ingest/licence_filter.py#L33) violates fail-closed future ingest. | AUD-032-013 |
| Phi/classification amendment | CONFLICT | PII+PSPF+sensitive-operational deny before non-AU transit conflicts with newer AU-only registry; no explicit retirement of original Phi outcome. [Policy](../../infra/policy/rego/foundry_carveout.rego#L11). | AUD-032-014, AUD-032-015 |
| Control-auth amendment | MISSING | Entra/RoleAuthority/taxonomy/dual approval/linked audit for both controls; [OpenAPI](contracts/openapi-delta.yaml#L70) omits autonomy and implementation is missing. | AUD-032-004 |
| PE-first dependency | CONFLICT | No Search ingest/retrieval even in dev before PE; [root Search](../../infra/main.bicep#L302) is explicitly public with empty private inputs. | AUD-032-002 |
| Kill-switch spike dependency | CONFLICT | Spike must validate before downstream SLO commitment; [status](../../docs/spikes/T016-killswitch-propagation.md#L5) defers it to downstream tasks. | AUD-032-005, AUD-032-030 |
| Top5-1 Dataset split | CONFLICT | [Plan](plan.md#L239) allows subset now/5,000 later; does not amend binding approved-v1 outcome to completion. | AUD-032-018, AUD-032-030 |
| Top5-2 OIDC split | UNVERIFIED | Dev must-land and staging/prod evidence later are schedules, not source-backed migration. [CD](../../.github/workflows/cd.yml#L95). | AUD-032-031 |
| Top5-3 Observability split | PARTIAL | One workbook/availability subset cannot close full metrics/Workbooks/five-AU-APAC/30-day requirements. [Templates](../../infra/modules/workbooks/executive-governance.json#L4). | AUD-032-021, AUD-032-022 |
| Top5-4 DR split | PARTIAL | PITR authored, but paired-read and actual drill remain obligations; [root](../../infra/main.bicep#L589) has one region. | AUD-032-024 |
| Top5-5 Security split | PARTIAL | Two priority Sentinel rules authored, but [unbound module](../../infra/modules/sentinel.bicep#L36) does not meet must-land enablement/action routing. | AUD-032-023 |
| Coverage tracker activation | UNVERIFIED | B requires seven green baseline runs, C three green target runs; [tracker](coverage-phase-tracker.md#L5) leaves both pending. No activation or bypass approval execution inferred. | AUD-032-019 |
| Stream-2 five-PR deferral | PARTIAL | [Deferral](STREAM-2-DEFERRAL.md#L19) requires behavior-preserving moves, breaker benchmarks, Cosmos integration and classifier tests, not present-day completion. | AUD-032-010, AUD-032-011, AUD-032-012, AUD-032-014 |

### Persona And Nonfunctional Constraints

| Obligation | Status | Coverage and explicit limitation | Follow-up |
| --- | --- | --- | --- |
| OBL-01 Operational persona consultation | UNVERIFIED | [Spec consultation note](spec.md#L8) lists IC, Operations, Planning, Logistics, PIO, Field Coordinator, Resilience Planner, Executive, Observer-Auditor and Risk Manager; authored note is not independent human consultation/sign-off. | AUD-032-030 |
| OBL-02 Sector persona consultation | UNVERIFIED | Same note covers NSW/VIC/QLD/SA/WA/TAS/ACT/NT, Commonwealth and cross-sector; no consultation records establish consent/approval or all-jurisdiction runtime reach. | AUD-032-006, AUD-032-030 |
| OBL-03 Technical persona consultation | UNVERIFIED | [Plan note](plan.md#L6) claims all 17 technical personas consulted (architecture, security/compliance, AI, API, infrastructure/container, data, SRE, QA/accessibility, chaos, software, UX, PO/BA); no independent review records. | AUD-032-030 |
| OBL-04 Primacy of life and NN-1 | PARTIAL | [MAF HITL pause](../../apps/agents/maf_runtime/workflow/builder.py#L159) is supported; absent control approval, audit interlock and incorrect policy default prevent a universal guarantee. | AUD-032-004, AUD-032-006, AUD-032-008 |
| OBL-05 AIIMS COP and NERAG/ISO 31000 | PARTIAL | [Typed role helper](../../apps/agents/common/aiims_registry.py#L48) and existing risk models do not connect policy overrides/full why-fired trace; preserve these semantics during fixes. | AUD-032-006, AUD-032-007, AUD-032-029 |
| OBL-06 CALD/ATSI accessibility | PARTIAL | [Language registry](../../apps/web/src/lib/i18n/language-packs.ts#L35) includes cultural approval, but English-only fallback and missing API-doc/Workbook WCAG evidence remain. | AUD-032-028, AUD-032-033 |
| OBL-07 Degraded connectivity and warning fidelity | PARTIAL | [Offline drain](../../apps/web/src/lib/offline/queue-store.ts#L216) loses failures; legacy fallback tests do not assert full AWS level/hazard/action equivalence. | AUD-032-011, AUD-032-032 |
| OBL-08 Multi-jurisdiction/NEMA-state semantics | PARTIAL | Nine jurisdiction policy codes are modelled, only three deployment YAMLs exist, and no policy consumers enforce all-state/Commonwealth overrides. [Model](../../packages/domain/src/domain/models/jurisdiction_governance_policy.py#L29). | AUD-032-006, AUD-032-036 |
| OBL-09 Append-only traceability and privacy | PARTIAL | [Audit appends](../../apps/api/app/repositories/audit_repository.py#L85) and hash helpers exist; no chain-wide quarantine, complete retention or central redaction. | AUD-032-008, AUD-032-009, AUD-032-022 |
| OBL-10 Azure-only AU data residency | PARTIAL | [Root primary region](../../infra/main.bicep#L79) is constrained; proposed APAC synthetics include US and model carve-out rules conflict. Actual deployed location is unverified. | AUD-032-002, AUD-032-014, AUD-032-022 |
| OBL-11 Performance envelope | UNVERIFIED | [Plan performance goals](plan.md#L43) specify ingestion P95 <=60s, handoff >=99.5%, publish P95 <=90s, dashboard >=99.9%, kill-switch P99 <=30s, RAG P95 <=400ms; no measurement record proves these together. | AUD-032-005, AUD-032-013, AUD-032-022, AUD-032-026 |
| OBL-12 DR envelope | UNVERIFIED | RPO/RTO, paired-read capacity, audit continuity, quarterly drills require genuine records; [runbook](../../docs/operator-runbooks/dr-bcp.md#L19) is instructions only. | AUD-032-024 |
| OBL-13 Nine-step workflow and two clarifications | PARTIAL | [Both clarify sections](spec.md#L13) authored; all 75 rubric questions remain open and [review/deploy](SESSION-STATUS-2026-04-30.md#L106) explicitly deferred. | AUD-032-030 |
| OBL-14 Scoping and overlap rules | CONFLICT | [Plan summary](plan.md#L23) says 75/16/nine streams but lists streams 0-9; task source has 152 not ~115. FR duplicates are intentional, not license to omit matrix rows. | AUD-032-030 |
| OBL-15 Baseline/approval escape valves | MISSING | [Decision-rights bypass list](../../docs/agents/decision-rights.md#L68) is prose; no one-time incident coverage/eval/security approval token, expiry/replay guard or immutable approval proof. | AUD-032-016, AUD-032-018, AUD-032-019, AUD-032-020 |
| OBL-16 Backward compatibility | PARTIAL | [Facades](../../apps/agents/common/resilience/__init__.py#L7) preserve existing imports but do not complete relocation; contract/schema/partition changes must remain versioned. | AUD-032-007, AUD-032-010, AUD-032-017, AUD-032-029 |
| OBL-17 Portfolio obligations | PARTIAL | Full static inventories cover all 41 spec folders, 25 workflows, six Dockerfiles and root-imported Cosmos containers; summary counts are below, not sampled as representative proof. | AUD-032-020, AUD-032-021, AUD-032-029, AUD-032-030 |
| OBL-18 Quickstart smoke contract | CONFLICT | [Quickstart](quickstart.md#L14) omits tests from mypy, combines coverage at 80, calls missing endpoints, supplies invalid control reason/no auth, and uses signing/eval commands inconsistent with actual CLI. Never executed here. | AUD-032-004, AUD-032-016, AUD-032-018, AUD-032-028 |

### Research Decisions

| Decision | Status | Static enforcement or discrepancy | Follow-up |
| --- | --- | --- | --- |
| R-01 | PARTIAL | [pybreaker adapter](../../apps/agents/common/resilience/pybreaker_adapter.py#L110) is unconsumed and has no half-open trial from can_execute. | AUD-032-011 |
| R-02 | PARTIAL | [Azure Monitor bootstrap](../../apps/api/app/main.py#L12) exists; recorder-only spans and missing contract fields do not establish OTLP end-to-end transport. | AUD-032-021 |
| R-03 | CONFLICT | [Search configuration](../../infra/main.bicep#L302) uses broader 3072-dim corpus with public access; [capacity metric](../../infra/modules/ai-search.bicep#L166) is not a capacity percent. | AUD-032-002, AUD-032-013 |
| R-04 | UNVERIFIED | [OIDC stages](../../docs/corpus/aidr/decisions/adr-032-oidc-supersession.md#L24) lack prerequisite approval and seven-day soak evidence. | AUD-032-031 |
| R-05 | PARTIAL | [Signing manifest](../../packages/prompts/cosign.manifest.yaml#L17) is not consumed by deployment; certificates/bundles not wired. | AUD-032-016 |
| R-06 | PARTIAL | [HSM key](../../infra/modules/cosmos-cmk.bicep#L33) does not bind Cosmos/Storage/workspace CMKs; log-analytics-key is a shared-key helper, not a vault pattern. | AUD-032-003 |
| R-07 | MISSING | No Phi AU-side shadow recommendation persistence/7-year filter path; [MAF shadow](../../apps/agents/maf_runtime/agents/_factory.py#L298) is not equivalent. | AUD-032-014 |
| R-08 | PARTIAL | [Vitest config](../../apps/web/vitest.config.ts#L1) exists, but full-tier CI and five meaningful original tests remain incomplete. | AUD-032-028 |
| R-09 | PARTIAL | [CI coverage](../../.github/workflows/ci.yml#L132) does not implement separate tiers/baseline transport/PR comparison claimed by research. | AUD-032-019 |
| R-10 | CONFLICT | [Availability module](../../infra/modules/availability-tests.bicep#L28) uses standard URL checks, different POPs and US fallback, not stated four-endpoint multi-step set. | AUD-032-022 |
| R-11 | PARTIAL | [Continuous7Days](../../infra/main.bicep#L594) present; paired-region read and recovery/client behavior absent in root. | AUD-032-024 |
| R-12 | CONFLICT | [Math doc](../../docs/architecture/cosmos-partitioning.md#L35) budgets/keys differ from root and authoritative successor has no arithmetic. | AUD-032-029 |
| R-13 | PARTIAL | [Sentinel](../../infra/modules/sentinel.bicep#L36) has two of five proposed rules but no composed connectors/actions/Defender policies. | AUD-032-023 |
| R-14 | PARTIAL | [Chaos experiment](../../infra/modules/chaos-studio.bicep#L91) does not implement the four faults, outcomes/metrics or stage-only root composition. | AUD-032-025 |
| R-15 | PARTIAL | [DORA aggregation](../../scripts/dora_metrics_publish.py#L93) uses GitHub sources but not correct per-environment deployment attribution/daily publication. | AUD-032-027 |
| R-16 | PARTIAL | [Pre-commit](../../.pre-commit-config.yaml#L26)/[contribution guide](../../CONTRIBUTING.md#L26) exist with incomplete gate parity/workflow details. | AUD-032-001, AUD-032-028 |
| R-17 | MISSING | [README](../../README.md#L275) has no Loom/MP4 walkthrough; no approval of alternate hosting is inferred. | AUD-032-028 |
| R-18 | PARTIAL | [FastAPI docs](../../apps/api/app/main.py#L30) are runtime-generated; no Next.js /api-docs/Redoc consumer of YAML. | AUD-032-028 |
| R-19 | PARTIAL | [Governance hub](../../docs/governance-hub/index.md#L9) chooses nav approach but has broken relative paths and no single top-nav route. | AUD-032-028 |
| R-20 | PARTIAL | [Base-image example](../../apps/agents/Dockerfile#L1) and all nine remaining FROM rows lack digests; update coverage is incomplete. | AUD-032-020 |

### Entity Contracts

| Entity | Status | Field/invariant coverage | Follow-up |
| --- | --- | --- | --- |
| E-01 Recommendation | PARTIAL | [Domain model](../../packages/domain/src/domain/models/recommendation.py#L7) has status/signals/model deployment only; no prompt SHA/version, model ID/version, alias, citations, consensus, autonomy/switch snapshot, shadow/parent or segment linkage. Existing approvals collapse non-approved outcomes to rejected. | AUD-032-007, AUD-032-008, AUD-032-014, AUD-032-034 |
| E-02 RagCitation | PARTIAL | [Model](../../packages/domain/src/domain/models/rag_citation.py#L17) has handbook/chapter/page/chunk/score/500-char quote, but no score <=1; no durable Recommendation attachment. | AUD-032-007, AUD-032-013 |
| E-03 AuditSegment | MISSING | No segment UUID/tenant/incident/window/event/seal/hash-chain repository; [replay hash](../../apps/agents/common/audit.py#L52) is a different invariant. Canonical formula/concurrency/order must be settled before implementation. | AUD-032-008 |
| E-04 JurisdictionPolicy | PARTIAL | [Renamed governance model](../../packages/domain/src/domain/models/jurisdiction_governance_policy.py#L40) preserves fields/codes but repository keeps `id`, no effective/version monotonic enforcement, only three YAMLs, no consumers. | AUD-032-006 |
| E-05 ConsensusEvent | MISSING | [Preparedness analysis](../../apps/api/app/services/rehearsal_orchestrator.py#L26) provides no >=2-agent incident/window/score event entity. | AUD-032-036 |
| E-06 EvalCase/Scorecard | PARTIAL | [Stored case](../../packages/eval-dataset/data/dataset-disaster-core-1.0.0/cases.jsonl#L1) has generated approval label, not safety approval; [gate](../../apps/eval-runner/src/ama_eval/gate.py#L75) skips missing mandatory metrics. | AUD-032-018 |
| E-07 MetricDefinition | PARTIAL | [Emitter](../../apps/api/app/observability/metrics.py#L46) has no typed registry, retention/SLO/dimension validation; metric names/types diverge from the full inventory. | AUD-032-021 |
| E-08 SLO | PARTIAL | [Document](../../docs/observability/slo.md#L19) provides metric/objective/budget/tier fields, but no registered API, correct complete burn math or deployed all-SLI alerts. | AUD-032-022 |
| E-09 PromptArtifact | MISSING | [README example](../../packages/prompts/README.md#L31) is not a signed/versioned artifact with sha/owner/review_due/templates/certificate identity. | AUD-032-016 |
| E-10 AutonomyDial | PARTIAL | [Dataclass](../../apps/agents/common/lifecycle/autonomy_eval.py#L40) has snapshot fields, but runtime defaults/lookup consumers and immutable recommendation decision snapshot are absent. | AUD-032-006, AUD-032-007 |
| E-11 KillSwitch | PARTIAL | [State](../../apps/agents/common/lifecycle/killswitch.py#L35) holds reason/identity/expiry, but expiry/order/governance/persistence/tenant-scoped propagation are not enforced. | AUD-032-004, AUD-032-005 |

### OpenAPI And Telemetry Contracts

| Contract operation/invariant | Status | Implementation trace and gap | Follow-up |
| --- | --- | --- | --- |
| API-01 GET health/audit-integrity | MISSING | [Router registrations](../../apps/api/app/api/router.py#L56) contain no matching integrity endpoint; report fields/empty-ledger semantics unimplemented. | AUD-032-008 |
| API-02 GET recommendations/id/why-fired | MISSING | [Recommendation router](../../apps/api/app/api/routes/recommendations.py#L7) only exposes approval POST; WhyFired required fields also omit signals/trust/threshold. | AUD-032-007 |
| API-03 GET observability/slos | MISSING | [API router](../../apps/api/app/api/router.py#L56) has no catalogue handler; authored SLO Markdown is not that API. | AUD-032-021, AUD-032-022 |
| API-04 GET observability/metrics-catalogue | MISSING | [Metrics wrapper](../../apps/api/app/observability/metrics.py#L46) is not a registry/API. | AUD-032-021 |
| API-05 GET agents/id/killswitch | MISSING | [Agent router](../../apps/api/app/api/routes/agents.py#L24) has no read control or agent.killswitch.read enforcement. | AUD-032-004 |
| API-06 POST agents/id/killswitch | MISSING | No registered scope/role/taxonomy/reason/proposer/approver/expiry path; [contract](contracts/openapi-delta.yaml#L87) cannot itself implement atomic audit/push. | AUD-032-004, AUD-032-005 |
| API-07 GET agents/id/status | MISSING | [Dispatcher health](../../apps/agents/dispatcher/agent.py#L207) is not per-agent switch/autonomy/heartbeat status. | AUD-032-004, AUD-032-005 |
| API-08 GET jurisdictions/code/policy | MISSING | [Governance repo](../../apps/api/app/repositories/jurisdiction_governance_policy_repository.py#L24) has no route caller matching the declared policy contract. | AUD-032-006 |
| API-09 POST rag/search | MISSING | [RagService](../../apps/api/app/services/rag_service.py#L27) has only tests as callers; no registered q/top_k/citation operation. Internal shared retrieval still exists separately. | AUD-032-013 |
| API-10 Autonomy control omitted | CONFLICT | [Declared scope](contracts/openapi-delta.yaml#L204) has no path or proposal/approval contract despite FR-AG05a requiring both controls. | AUD-032-004 |
| API auth/errors/atomicity | PARTIAL | [OAuth declaration](contracts/openapi-delta.yaml#L193) uses a tenant placeholder and scopes, not deployed validation; production proposal/409 semantics and cross-resource atomicity need explicit outbox design. | AUD-032-004 |
| OTel resource attributes | PARTIAL | [Contract](contracts/otel-attributes.yaml#L5): service.name, service.version, deployment.environment, cloud.provider/region/account.id; [bootstrap](../../apps/api/app/observability/__init__.py#L40) supplies only a subset. | AUD-032-021 |
| OTel common span attributes | PARTIAL | [Contract](contracts/otel-attributes.yaml#L13): tenant, jurisdiction, incident, agent, recommendation, autonomy, switch, shadow; no universal context-injection middleware. | AUD-032-021 |
| OTel LLM attributes | PARTIAL | [Contract](contracts/otel-attributes.yaml#L40): model/version/alias/prompt SHA/version/tokens/cost, optional budget/fallback/RAG/validation; [recorder](../../apps/agents/common/otel_telemetry.py#L128) exports none. | AUD-032-007, AUD-032-021 |
| OTel handoff/audit attributes | PARTIAL | [Contract](contracts/otel-attributes.yaml#L55) specifies source/target/attempt/dead-letter/timeout and segment/event-count/integrity; legacy logging/MAF helpers do not implement all fields or segments. | AUD-032-008, AUD-032-021, AUD-032-034 |
| OTel named events | MISSING | [Five required events](contracts/otel-attributes.yaml#L67): ama.killswitch.toggled, ama.consensus.event, ama.audit.integrity_failure, ama.budget.warning, ama.shadow.divergence_detected lack a connected common export path. | AUD-032-005, AUD-032-008, AUD-032-012, AUD-032-014, AUD-032-036 |
| Signing contract | PARTIAL | [Identity/issuer/bundle/revocation/2555-day contract](contracts/cosign-signing.yaml#L9) lacks deployment consumer, certificate flags and revocation enforcement. | AUD-032-016 |
| Jurisdiction schema | PARTIAL | [YAML schema](contracts/jurisdiction-policy.schema.yaml#L7) defines nine codes, ordered BCP-47 languages, overrides, version/effective/approver; loader validates model but does not apply policy monotonically or at deploy. | AUD-032-006 |

### Spec-030 Acceptance ID Obligation

FR-T09/T909 require concrete pytest IDs for the dependent framework's acceptance scenarios. The scoped review read those 14
scenarios and inspected current eval tests; no 030 acceptance-ID binding was found in the complete eval test inventory.
The rows below credit related assertions without claiming those scenarios passed or expanding this into a second spec audit.

| Dependent scenario | Status | Existing assertion/evidence and remaining ID coverage | Follow-up |
| --- | --- | --- | --- |
| 030-US1.1 | PARTIAL | [Fake multi-model comparison](../../tests/unit/eval/test_orchestrator_e2e.py#L89) checks some metrics/winner; no all-metric acceptance ID/live scorecard. | AUD-032-018 |
| 030-US1.2 | UNVERIFIED | [Runner](../../apps/eval-runner/src/ama_eval/runner.py#L29) does not establish live progress/cancellation cleanup via an acceptance test ID. | AUD-032-018 |
| 030-US1.3 | PARTIAL | [Scorecard save](../../apps/eval-runner/src/ama_eval/runner.py#L163) and fake traces exist; export reproducibility not bound to an acceptance ID. | AUD-032-018 |
| 030-US2.1 | PARTIAL | [All stored approval chains](../../packages/eval-dataset/data/dataset-disaster-core-1.0.0/cases.jsonl#L1) are draft-only despite approved labels; safety-reviewer publication not asserted for the artifact. | AUD-032-018 |
| 030-US2.2 | UNVERIFIED | [Manifest](../../packages/eval-dataset/data/dataset-disaster-core-1.0.0/manifest.json#L1) labels published; no acceptance-ID proof of immutability/new-version writes inspected. | AUD-032-018 |
| 030-US2.3 | PARTIAL | [Runner max-cases](../../apps/eval-runner/src/ama_eval/runner.py#L114) slices rows, not complete hazard/jurisdiction/severity selection with reported subset identity. | AUD-032-018 |
| 030-US3.1 | PARTIAL | [Provisioner test](../../tests/unit/eval/test_phase5_6_modules.py#L58) injects CLI, not linked full provision/run/teardown evidence or acceptance ID. | AUD-032-018 |
| 030-US3.2 | PARTIAL | [Reconciler test](../../tests/unit/eval/test_phase5_6_modules.py#L88) checks fake orphan cleanup, not full failed-run lifecycle ID coverage. | AUD-032-018 |
| 030-US3.3 | PARTIAL | [Cost tests](../../tests/unit/eval/test_phase5_6_modules.py#L126) compute local numbers; no complete lifecycle/cost artifact acceptance ID. | AUD-032-018 |
| 030-US4.1 | PARTIAL | [Gate tests](../../tests/unit/eval/test_phase5_6_modules.py#L142) check thresholds/deltas, but runner/workflow do not enforce the result. | AUD-032-018 |
| 030-US4.2 | MISSING | [Workflow](../../.github/workflows/eval-pr-gate.yml#L109) has no immutable authorized override plus safety notification acceptance binding. | AUD-032-018 |
| 030-US5.1 | UNVERIFIED | [Trace upload](../../apps/eval-runner/src/ama_eval/runner.py#L202) is optional/best-effort; no historical full-chain acceptance ID/proof. | AUD-032-018 |
| 030-US5.2 | UNVERIFIED | [Fake sample traces](../../tests/unit/eval/test_orchestrator_e2e.py#L126) do not establish original historical rationale retrieval without recomputation. | AUD-032-018 |
| 030-US6.1 | PARTIAL | [Sanitisation test home](../../tests/unit/eval/test_sanitise.py#L1) is useful, but no real-case consent/safety-review publication acceptance ID is mapped. | AUD-032-018 |

## Full Static Inventories

Inventories below are scoped extensions explicitly required by spec 032's portfolio-wide obligations, not implementation audits
of the other specifications. Other implementation-review-tasks reports were neither read nor used. Tracked-path inventories were
cross-checked against the filesystem; ignored virtual environments, node_modules, compiled outputs and runtime/cloud state are excluded.

### Action References

All 25 workflow YAML files were scanned for every active `uses:` instruction, including nested job steps. No composite-action files
remain under .github/actions. There are **112 active references: 92 SHA-shaped and 20 tag-shaped**. SHA shape does not verify the
remote commit's publisher/version; no network lookup was performed. Commented CodeQL action lines are not active references.

| Workflow | Active refs | Tag refs | Evidence |
| --- | ---: | ---: | --- |
| amend-loop-coupling | 1 | 1 | [Checkout](../../.github/workflows/amend-loop-coupling.yml#L23) |
| cd | 6 | 0 | [Validated checkout](../../.github/workflows/cd.yml#L64) |
| chaos-quarterly | 3 | 0 | [Checkout](../../.github/workflows/chaos-quarterly.yml#L29) |
| ci | 33 | 2 | [Unpinned evidence job](../../.github/workflows/ci.yml#L417) |
| codeql | 1 | 0 | [Checkout; analysis disabled](../../.github/workflows/codeql.yml#L30) |
| corpus-ingest | 5 | 0 | [Checkout](../../.github/workflows/corpus-ingest.yml#L58) |
| dora-metrics | 2 | 0 | [Checkout](../../.github/workflows/dora-metrics.yml#L22) |
| dr-drill | 3 | 0 | [Checkout](../../.github/workflows/dr-drill.yml#L30) |
| drift-detection | 2 | 0 | [Checkout](../../.github/workflows/drift-detection.yml#L34) |
| eval-pr-gate | 4 | 0 | [Checkout](../../.github/workflows/eval-pr-gate.yml#L23) |
| eval-publish-dataset | 3 | 0 | [Checkout](../../.github/workflows/eval-publish-dataset.yml#L24) |
| foundry-carveout-review-6mo | 1 | 1 | [Checkout](../../.github/workflows/foundry-carveout-review-6mo.yml#L22) |
| foundry-carveout-review | 5 | 5 | [First tagged actions](../../.github/workflows/foundry-carveout-review.yml#L11); further refs at 55, 60, 91 |
| help-gates | 2 | 2 | [Tagged actions](../../.github/workflows/help-gates.yml#L10) |
| help-snapshot | 4 | 4 | [Tagged publish actions](../../.github/workflows/help-snapshot.yml#L29); rollback actions at 51, 52 |
| nightly-load | 4 | 0 | [Checkout](../../.github/workflows/nightly-load.yml#L31) |
| prompts-publish | 3 | 0 | [Checkout](../../.github/workflows/prompts-publish.yml#L19) |
| security-scan | 6 | 0 | [Checkout](../../.github/workflows/security-scan.yml#L24) |
| simulation-load-test | 3 | 3 | [Tagged actions](../../.github/workflows/simulation-load-test.yml#L31); further refs at 34, 60 |
| simulation-stub-sweep | 2 | 2 | [Tagged actions](../../.github/workflows/simulation-stub-sweep.yml#L10) |
| spec-035-gate | 4 | 0 | [Checkout](../../.github/workflows/spec-035-gate.yml#L14) |
| spec-036-50-agent-load | 3 | 0 | [Checkout](../../.github/workflows/spec-036-50-agent-load.yml#L38) |
| spec-036-blue-green-e2e | 2 | 0 | [Checkout](../../.github/workflows/spec-036-blue-green-e2e.yml#L37) |
| staging-promotion | 7 | 0 | [Checkout](../../.github/workflows/staging-promotion.yml#L52) |
| web-coverage-iteration | 3 | 0 | [Checkout](../../.github/workflows/web-coverage-iteration.yml#L37) |

### Base Images

Every tracked Dockerfile was inspected for base-image instructions. **Six files, ten FROM instructions, zero digest pins.**
Root default service images and the ingest-runner tag additionally use latest; a Dockerfile-only sweep would miss them.

| Surface | All base instructions | Update coverage |
| --- | --- | --- |
| Agents | [Builder](../../apps/agents/Dockerfile#L1), [runtime](../../apps/agents/Dockerfile#L21): python:3.12-slim | Weekly Docker update declared |
| API | [Builder](../../apps/api/Dockerfile#L1), [runtime](../../apps/api/Dockerfile#L11): python:3.12-slim | Weekly Docker update declared |
| Eval runner | [Base](../../apps/eval-runner/Dockerfile#L2): python:3.12-slim | Weekly Docker update declared |
| Ingest runner | [Base](../../apps/ingest-runner/Dockerfile#L14): python:3.13-slim | No Docker entry in Dependabot |
| Ingestion | [Builder](../../apps/ingestion/Dockerfile#L1), [runtime](../../apps/ingestion/Dockerfile#L15): python:3.12-slim | Weekly Docker update declared |
| Web | [Builder](../../apps/web/Dockerfile#L1), [runtime](../../apps/web/Dockerfile#L11): node:20-alpine | npm entry is not Docker base-image update coverage |
| Root service images | [Defaults](../../infra/main.bicep#L91): api/agents/ingestion helloworld:latest; [ingest tag](../../infra/main.bicep#L248): latest | Must validate rendered deployment image inputs, not just FROM |

### All Specification Folders

FR-T07 inventory: **41 actual specification folders** containing spec.md, not a sample of the already reviewed specs. The scan read
every original Markdown file under specs for inline FR/SC-to-test rows and references to matrix/traceability/CSV artifacts; it also
searched docs/tests/app-test paths for replacements. Task-to-FR lists, gap-to-FR tables, persona-to-task matrices and a guessed test
filename do not count as complete requirement-to-test coverage. This inventory evaluates artifact coverage only, not the other specs' code.

| Specification folder | Traceability status | Located source/artifact and limit |
| --- | --- | --- |
| 001-arch-docs-refresh | MISSING | [Spec](../001-arch-docs-refresh/spec.md#L1); no requirement-to-test closure matrix located in the bounded inventory. |
| 001-disaster-response-hub | MISSING | [Spec](../001-disaster-response-hub/spec.md#L1); 027 gap pointer is not its per-requirement test matrix. |
| 003-rubric-gap-closure | MISSING | [Spec](../003-rubric-gap-closure/spec.md#L1); no per-FR test matrix located. |
| 004-actor-github-agents | MISSING | [Spec](../004-actor-github-agents/spec.md#L1); no per-FR test matrix located. |
| 005-data-source-governance | MISSING | [Spec](../005-data-source-governance/spec.md#L1); no per-FR test matrix located. |
| 006-data-ingestion-storage | MISSING | [Spec](../006-data-ingestion-storage/spec.md#L1); no per-FR test matrix located. |
| 007-simulation-tenant-isolation | MISSING | [Spec](../007-simulation-tenant-isolation/spec.md#L1); no per-FR test matrix located. |
| 008-communication-agent | MISSING | [Spec](../008-communication-agent/spec.md#L1); no per-FR test matrix located. |
| 009-evacuation-agent | MISSING | [Spec](../009-evacuation-agent/spec.md#L1); no per-FR test matrix located. |
| 010-monitoring-agent | MISSING | [Spec](../010-monitoring-agent/spec.md#L1); no per-FR test matrix located. |
| 011-resource-allocation-agent | MISSING | [Spec](../011-resource-allocation-agent/spec.md#L1); no per-FR test matrix located. |
| 012-risk-assessment-agent | MISSING | [Spec](../012-risk-assessment-agent/spec.md#L1); no per-FR test matrix located. |
| 013-root-readme | MISSING | [Spec](../013-root-readme/spec.md#L1); docs-only checks still need explicit validation/disposition, not an assumed exemption. |
| 014-azure-openai-integration | MISSING | [Spec](../014-azure-openai-integration/spec.md#L1); no per-FR test matrix located. |
| 015-performance-benchmarks | MISSING | [Spec](../015-performance-benchmarks/spec.md#L1); benchmark files alone are not a requirement mapping. |
| 016-automated-demo-script | MISSING | [Spec](../016-automated-demo-script/spec.md#L1); no per-FR test matrix located. |
| 017-cd-pipeline | MISSING | [Spec](../017-cd-pipeline/spec.md#L1); no per-FR test matrix located. |
| 018-aidr-guidance-integration | MISSING | [Spec](../018-aidr-guidance-integration/spec.md#L1); no per-FR test matrix located. |
| 019-aidr-additional-guidances | MISSING | [Spec](../019-aidr-additional-guidances/spec.md#L1); no per-FR test matrix located. |
| 020-disaster-mapper-ui | MISSING | [Spec](../020-disaster-mapper-ui/spec.md#L1); no per-FR test matrix located. |
| 021-governance-dashboard | MISSING | [Spec](../021-governance-dashboard/spec.md#L1); no per-FR test matrix located. |
| 022-multi-jurisdiction-filter | MISSING | [Spec](../022-multi-jurisdiction-filter/spec.md#L1); no per-FR test matrix located. |
| 023-dashboard-real-data | MISSING | [Spec](../023-dashboard-real-data/spec.md#L1); no per-FR test matrix located. |
| 024-simulation-control-chat | MISSING | [Spec](../024-simulation-control-chat/spec.md#L1); no per-FR test matrix located. |
| 025-agent-spec-compliance | MISSING | [Spec](../025-agent-spec-compliance/spec.md#L1); no per-FR test matrix located. |
| 026-sim-warp-playback | MISSING | [Spec](../026-sim-warp-playback/spec.md#L1); task descriptions name tests but no per-FR matrix located. |
| 027-spec-hardening | PARTIAL | [R-4](../027-spec-hardening/research.md#L62) explicitly defines a gap-to-FR table, not complete FR-to-test closure; NFR-row contract is only a schema example. |
| 028-capstone-alignment | MISSING | [Spec](../028-capstone-alignment/spec.md#L1); no per-FR test matrix located. |
| 029-progressive-delivery-pipeline | MISSING | [Spec](../029-progressive-delivery-pipeline/spec.md#L1); no per-FR test matrix located; retirement still needs explicit disposition rows. |
| 030-llm-eval-framework | MISSING | [Spec](../030-llm-eval-framework/spec.md#L1); tests are not mapped to its 14 acceptance scenarios. |
| 031-simplify-cicd-pipeline | MISSING | [Spec](../031-simplify-cicd-pipeline/spec.md#L1); no per-FR test closure matrix located. |
| 032-rubric-improvements | PARTIAL | [Traceability](traceability.md#L16) has 88 FR rows, including placeholders; parent FR-S02 absent. This audit is not a retroactive original-matrix edit. |
| 033-maf-adoption | MISSING | [Spec](../033-maf-adoption/spec.md#L1); no complete per-FR test matrix located. |
| 034-webapp-capstone-coverage | PARTIAL | [Analysis mapping](../034-webapp-capstone-coverage/analysis.md#L57) covers constitution/selected FR test surfaces; not every FR/acceptance mapping. |
| 035-webapp-capstone-closure | PARTIAL | [Quickstart matrix](../035-webapp-capstone-closure/quickstart.md#L185) maps SCs to artifacts, not a complete FR-to-test matrix. |
| 036-foundry-rag-grounding | PARTIAL | [Persona traceability](../036-foundry-rag-grounding/persona-traceability.md#L1) maps concerns to tasks; plan/task tests are not complete per-FR closure rows. |
| 036-sim-agent-extend | PARTIAL | [FR matrix](../036-sim-agent-extend/fr-coverage-matrix.md#L7) groups IDs and stops at 066; [SC matrix](../036-sim-agent-extend/sc-measurement-matrix.md#L6) uses PASS including staging-gated claims. Later amendments need reconciliation. |
| 037-capstone-evidence-pack | PARTIAL | [Linked CSV](../../tests/contract/spec_037/_traceability.csv#L1) and [API copy](../../apps/api/tests/contract/spec_037/_traceability.csv#L1) cover FR/SC labels, but many rows are manual/artifacts/deferred rather than concrete tests. |
| 038-help-docs-chat | PARTIAL | [Verification status](../038-help-docs-chat/verification-status.md#L51) supplies selected SC/source evidence, not complete requirement/test closure. |
| 039-test-data-provisioning | PARTIAL | [Verification matrix](../039-test-data-provisioning/verification.md#L68) is substantive but mixes artifacts/lints/manual claims and omits later FR-036/SC-016 amendment coverage. |
| 040-success-criteria | MISSING | [Spec](../040-success-criteria/spec.md#L1); no complete per-FR test matrix located despite many named task test homes. |

### Cosmos Throughput Composition

Full recursive root composition was inspected, including conditional modules. There are **25 declared Cosmos container resources**
in main and its imported container modules when the Help flag is enabled: **22 with explicit caps, three without**.
That is not the same as all runtime-needed containers being provisioned. No independent second infrastructure entrypoint was
silently counted as deployed by azure.yaml. Future-only resource/provider validation remains required.

| Root-composed owner | Complete container set | Caps and source |
| --- | --- | --- |
| Main | signals; simulation; seed; sim-chat; governance; coordination_tasks; evidence_pack_artefact_cache | [Signals](../../infra/main.bicep#L609): 4000; other six: 1000 each |
| Recovery/lessons | recovery; lessons; aiims-assignments; evacuation-stages; pprr-contexts | [Imported module](../../infra/modules/recovery-lessons.bicep#L19): 1000 each |
| Emergency planning | emergency-plans; recovery-programmes; recovery-catalogue | [Imported module](../../infra/modules/emergency-planning.bicep#L19): 1000 each |
| MAF workflow | workflow_runs; checkpoints; tool_registrations | [Imported module](../../infra/bicep/modules/cosmos-workflow.bicep#L34): no throughput options on any of the three |
| Help, conditional | help_articles; screenshot_registry; chat_sessions; chat_audit_log; snapshot_records; support_handoff_config; content_review_backlog | [Imported module](../../infra/bicep/modules/cosmos-help-containers.bicep#L28): default cap 4000 each |
| Spec-032 runtime requirements | llm_budgets; jurisdiction_governance_policies; agent_killswitches/lease; audit_segments; consensus_events | Referenced by [budget](../../apps/agents/common/llm_budget_tracker.py#L106), [policy repo](../../apps/api/app/repositories/jurisdiction_governance_policy_repository.py#L24) and design; no matching root-composed containers |

[Legacy RU table](../../docs/architecture/cosmos-partitioning.md#L35) adds to 7100 baseline RU/s, not its labelled ~7300.
Its 46000 maximum versus 41400 nine-jurisdiction peak leaves 4600, or about 11.1% above the peak, not 30% peak headroom.
The definition of headroom and the authoritative successor need reconciliation rather than treating either number as a measured capacity guarantee.

### Metric And Caller Inventories

FR-O02: all **1164 tracked .py/.ts/.tsx/.js/.mjs/.cjs source files** under apps/packages/scripts/tools were text-scanned for
instrument creation and emission families. This found **137 distinct literal names in 13 producer files, 129 absent from the catalogue**.
This is a full lexical inventory, not runtime enumeration: dynamic-name emitters, declarative dictionaries, workflow heredocs,
optional exporters and no-op recorders are assessed separately rather than silently assumed covered by literal-name counts.

| All literal-name producer files | Catalogue result / required reconciliation |
| --- | --- |
| [Lifecycle heartbeat](../../apps/agents/common/lifecycle/heartbeat.py#L22) | kill-switch metric named; runtime watcher/drain not connected |
| [Budget tracker](../../apps/agents/common/llm_budget_tracker.py#L196) | cost/warning names listed, but unconsumed and warning suffix/scope differ from original contract |
| [Strategy chain](../../apps/agents/common/llm_strategies.py#L202) | fallback-step listed; chain unconsumed |
| [Breaker adapter](../../apps/agents/common/resilience/pybreaker_adapter.py#L25) | two breaker instruments listed; dependency boundary and caller wiring missing |
| [Communication telemetry](../../apps/agents/communication/telemetry.py#L124) | `communication.*` plus shared `llm.*` names absent from catalogue, including latency, safety, approval and delivery |
| [Evacuation telemetry](../../apps/agents/evacuation/telemetry.py#L119) | `evacuation.*` and shared `llm.*` names absent; per-plan/route/shelter/replan dimensions need registration |
| [Monitoring telemetry](../../apps/agents/monitoring/telemetry.py#L57) | shared `llm.*` and `me.framework`/indicator/outcome names absent |
| [Resource telemetry](../../apps/agents/resource_allocation/telemetry.py#L99) | `resource_allocation.*` and shared `llm.*` names absent |
| [Risk telemetry](../../apps/agents/risk_assessment/telemetry.py#L93) | `risk_assessment.*` and shared `llm.*` names absent |
| [Reconciliation metric](../../apps/api/app/api/routes/admin/reconciliation.py#L65) | reconciliation.gap absent |
| [Evidence ratio metric](../../apps/api/app/services/governance/manual_row_ratio.py#L51) | evidence_pack.manual_row_ratio absent |
| [RagService emitter](../../apps/api/app/services/rag_service.py#L100) | two names listed, but hit_count kind differs and service is unconsumed |
| [Ingestion telemetry](../../apps/ingestion/telemetry.py#L18) | `ingestion.*` and `simulation.*` literal names absent; proposed `signal.ingestion.*` is not an alias implementation |
| [Dynamic metric wrapper](../../apps/api/app/observability/metrics.py#L46) | accepts any name; no registry enforcing type/unit/dimensions/retention |
| [Dynamic DORA emitter](../../scripts/dora_metrics_publish.py#L140) | four documented DORA names, but sums snapshot values as counters and publication can silently fail |
| [Recorded-span metrics](../../apps/agents/common/otel_telemetry.py#L78) | retrieval/inference/ingest dictionaries are recorder-only; not real exported customMetrics |
| [Workflow load counter](../../.github/workflows/nightly-load.yml#L55) | loadtest.run_total is not load latency/error/memory results |

FR-AI04: complete actual production invocation inventory for _generate_with_fallback and its forwarded bound method:

| Call | Owning entry/caller | response_model |
| --- | --- | --- |
| Draft/translate | [Translator](../../apps/agents/communication/translator.py#L143) | absent |
| Back-translation | [Translator](../../apps/agents/communication/translator.py#L251) | absent |
| Hazard assessment | [Risk agent](../../apps/agents/risk_assessment/agent.py#L127) | absent |
| Recommendation explanation | [Risk agent](../../apps/agents/risk_assessment/agent.py#L336) | absent |
| Public alert recommendation | [Risk agent](../../apps/agents/risk_assessment/agent.py#L425) | absent |
| Evacuation summary | [Pipeline callback](../../apps/agents/evacuation/pipeline.py#L889), bound by agent constructor | absent |
| Resource summary | [Pipeline callback](../../apps/agents/resource_allocation/pipeline.py#L786), bound by agent constructor | absent |

Other inference entrypoints were also inspected: the deployed dispatcher calls the SDK directly, MAF parses an output schema,
and the Simulation controller has its own Foundry/retrieval path. They are not falsely counted as mixin call sites or as proof
that the seven required calls validate. Common subpackage/strategy/budget/registry/watchers were searched across all apps/packages/scripts:
test-only and docstring references were distinguished from real imports and function calls.

## Bounded Negative Searches And Evidence Limits

MISSING rows use the following bounded searches, not failure to open one historical filename. Source-controlled text was searched
with filename inventories and symbol/path variants; external metadata and deployed resources were deliberately not queried.

| Search scope | Variants/controlling surfaces inspected | Negative or replacement conclusion |
| --- | --- | --- |
| All original files in this spec | 18-file recursive inventory, all contents including contracts/checklists/status/deferral | No prior implementation report or additional local amendments/evidence files before this report |
| apps + packages + tests + infra | AuditSegment, prev-hash/segment-hash, audit_integrity, why-fired/why_fired and recommendation fields; actual API registration/writers | No requested segment integrity job/endpoint/UI/publication gate; generic audit append/replay found and assessed separately |
| apps + packages + scripts + infra + tests | killswitch/kill_switch, autonomy, policy repository, bus topic/lease/publisher and OPA filename variants; dispatcher/startup/root imports | Local state/lookup helpers found; no governed control API or push/drain deployment chain |
| apps + packages + scripts + docs + tests | saga/process manager, stateDiagram-v2/render-state, consensus/agreement, reflection feedback, coordination gap/AAR | MAF replacement and preparedness summary found; no required Saga document/generated graph/feedback/consensus/completion AAR |
| apps + packages + scripts + .github | prompt loaders/registry, signing manifest consumers, cosign sign/verify, all library assets and CD/azd hooks | Only prompt README+manifest in library; no versioned template consumer/CD signature verifier |
| apps + packages + tests + infra | Phi/shadow, classification gateways, parent recommendation/shadow fields, retention store | MAF runtime shadow found, not Phi shadow; no explicit repository retirement of FR-AI03 |
| infra + .github + scripts + tools | private-endpoint/CMK/Storage encryption, public-network probes, monitoring/Workbooks, OPA autonomy/killswitch/signing | Standalone security modules found but not root composition; no probe or three requested OPA policies |
| .github + scripts + tools + app middleware | pii canary/log validator, security/eval/coverage bypass names and callbacks | Mentions/helper masking found, not periodic log scan or authenticated one-time exception workflow |
| docs + apps/web + tests + README | video/Loom/MP4 links; API-docs/Redoc/Swagger; contract contributor-guide variants; ingestion operational guide | Native API docs and relocated operator guide found; no requested video link/web schema host/contract guide/ingestion procedure |
| Entire specs + linked docs/tests/app tests | FR/SC-to-test table rows; traceability/matrix filenames and explicit CSV/shared-matrix references; excludes all other implementation-review-tasks reports | Full 41-folder matrix above distinguishes missing, partial, gap-only, persona-only and linked CSV artifacts |
| .github/workflows + .github/actions + all Dockerfiles | Every active uses and FROM instruction; also rendered image defaults and Dependabot locations | 20 active tag refs, ten unpinned FROM rows; no remaining composite actions |
| Root Bicep recursively composed container modules | Resource containers, partition keys, throughput options and dependent runtime client names | 25 declared containers, three uncapped, several 032 runtime containers unprovisioned |
| All source metric producers/consumers | Literal and dynamic instrument families plus logging-only/recorder-only wrappers and workflow heredocs | Catalogue is materially incomplete; lexical counts do not prove runtime/export success |
| Git metadata only | HEAD, initial/final worktree status, local v032 tag inventory | Requested SHA verified; no local v032 tag, no remote tag/PR/branch-protection or deployment state inferred |

**Authorship is not execution.** Five relocated Proposed ADRs, the design-only spike, manual/deferred CSV rows, blank surveys,
generator approval labels, release notes, module compilation claims and authored rubric grades are not signatures or trustworthy
run records. Existing private-network intentions do not prove external probes. SLO/benchmark targets do not prove measured latency.
The report does not assign an independent rubric score or infer Azure resources/entitlements from available text.

**Static blockers to closure:** network/CMK composition; control/audit safety gates; approved eval data and fail-closed release gates;
real telemetry and private staging paths; explicit policy/scope decisions; genuine persona/legal/security approvals; and the required
seven-day/30-day/full-cycle measurements. These block implementation-complete claims, not completion of this static audit.

**Future validation prerequisites:** use an approved isolated implementation effort, supported toolchains and installed dependencies,
known synthetic fixture data, configured non-production resources where a task calls for live validation, and explicit human approval
for deployments, exercises, data licences, identity rollout and release. Preserve prior evidence and bind every new record to commit,
dataset/prompt/model version, environment, timestamps, command and unedited result. No future commands or approvals were executed here.

## Final Static Validation

- Source task comparison: 152/152 unique rows; exact original states preserved (82 `[X]`, 70 `none`).
- Task dispositions: 17 IMPLEMENTED, 82 PARTIAL, 28 MISSING, 13 CONFLICT, 11 UNVERIFIED, one SUPERSEDED.
- Requirement comparison: 89/89 FRs and 10/10 SCs, including parent and suffix IDs, without duplicates.
- Scenario accounting: all 30 original numbered scenarios, eight independent story tests, nine edge cases, and the 14 dependent spec-030 acceptance-ID obligations.
- Local checklist comparison: 75/75 rubric IDs with original `[ ]`, 16/16 quality items with original `[x]`; all local analysis findings, 20 research decisions, 11 entities and ten clarification answers accounted for.
- Remediation format: 36 unique AUD-032 IDs, all exact unchecked checkbox lines; all referenced follow-ups resolve.
- Evidence links: 866 occurrences / 490 unique local links checked for existing workspace targets and valid exact line bounds; no links to other implementation review reports.
- Portfolio inventories: 41 spec folders, 25 workflows/112 active action refs, six Dockerfiles/ten base instructions, all root-composed Cosmos container modules, and every tracked source file in the metric-producer search scope.
- Validation consisted of metadata/text/JSON inventory and report editor diagnostics only. No product test, repository verification script, import, build, model, server, browser, cloud operation or approval was executed.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 032 only. Three parallel technical reviews examined full-scope
quality gates, production posture/provenance, and rubric/evidence claims. The source-completable CI defect was corrected:
the `python-type-strict` step no longer has `continue-on-error`, so `mypy --strict apps packages` is a blocking gate.

Validation: `python -m pytest tests/devops/test_ci_workflow_structure.py -q` returned `10 passed`.

Remaining open work includes private production networking/CMK, governed agent controls, append-only audit/publication
blocking, redaction, deployment-bound validation, resilience/budget adapters, RAG/eval/signing, SAST/supply chain,
telemetry/retention/SLOs, DR/chaos/performance, staged auth, language fallback, and human/cloud evidence.
