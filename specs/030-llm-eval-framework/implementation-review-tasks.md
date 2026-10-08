# Spec 030 Implementation Review Tasks

## Review Metadata

- Review date: 2026-09-14.
- Expected and read-only verified HEAD: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`.
- Scope: spec 030 only, with implementation dependencies inspected to establish its behavior.
- Authority: [Review Contract](../001-spec-implementation-audit/README.md#L11) and
  [code-review instructions](../../.github/instructions/code-review.instructions.md#L1).
- Sole writable artifact: this report. No prior report existed in this directory.
- Static source, configuration, test-assertion, fixture, and recorded-artifact review only.
  No evaluations, tests, builds, verification scripts, imports, model calls, servers, browsers,
  cloud queries, deployments, installations, or external approvals were executed.
- Original task states are retained as evidence of authored tracking, not proof of delivery.
  Runtime outcomes and human approvals remain UNVERIFIED unless attributable records establish them.
- Fresh stand-alone review; three authorised read-only reviewers were consulted without nested
  delegation. Their assertions were reconciled against source, not accepted as completion evidence.
  No other specification's implementation-review-tasks report was read.
- Coverage: 98 original tasks (all `[X]`, including T031a, T046a and T067a), 32 functional
  requirement IDs, 12 SCs, 14 acceptance scenarios, eight edge cases, and 18 open follow-ups.
  The plan/research's older "29 FRs" summary does not override the actual source ID set.
- No original NFR IDs exist. The NF, AS, EC, CQ, OP, RV and other ledger IDs below are review-local
  accounting labels, not new requirements or changes to source tasks.

### Inputs and Search Boundaries

All eight local inputs were read completely: [specification](spec.md#L1), [tasks](tasks.md#L1),
[plan](plan.md#L1), [research D1-D10](research.md#L1), [data model](data-model.md#L1),
[API contract](contracts/api.md#L1), [quickstart](quickstart.md#L1), and
[quality checklist](checklists/requirements.md#L1). There are no separate local review/evidence/amendment
files. The embedded amendment is FR-022a and tasks Phase 10. The six user-story personas, ten clarification
decisions, assumptions and scope exclusions are included below; no additional local persona/hypothesis
amendment was found or imported from another specification.

Relevant guidance read: code-review instructions and their detailed checklist, code-commenting guidance,
both Bicep instructions, Python fact-grounded-coding and Cosmos DB best-practices skills. Runtime steps
suggested by those materials were not executed. This report does not certify cloud policy compliance,
installed dependencies, branch protection, current deployment state or Microsoft model availability.

| Boundary | Complete controlling surface inspected and negative-search limits |
| --- | --- |
| S-RUN | [Manual CLI](../../scripts/run_llm_evaluation.py#L1) -> [run routes](../../apps/api/app/api/routes/eval/runs.py#L35) -> [job invoker](../../apps/api/app/services/eval_job_trigger.py#L40) -> [runner](../../apps/eval-runner/src/ama_eval/runner.py#L26) -> [orchestrator](../../apps/eval-runner/src/ama_eval/orchestrator.py#L73). All default evaluator modules, client, scorecard, gate, cost, provisioner, reconciler and evidence modules were read. Completed runner-source searches found judge factories/definitions but no production registration call, registry-file loader or EVAL_JOB_ROLE dispatcher. Broad searches that timed out were not treated as absence evidence. |
| S-API | All five modules registered by [router.py](../../apps/api/app/api/routes/eval/router.py#L40), their repository implementation, shared models, schemas, audit vocabulary, policy evaluator and upstream auth middleware. Gate/override, progress, export, dataset-family list and metric/judge activation writers are absent from this registered surface. Renamed nested scorecard/trace routes were credited. |
| S-DATA | Entire eval-dataset file inventory, package CLI/generator/templates/distribution/manifest/README/tests, the complete 5,000-record JSONL and manifest, sanitisation helper/tests, both eval workflows and CODEOWNERS. The README explicitly identifies the old cases path as legacy; replacement package/data paths were inspected before absence claims. No committed 50-case smoke artifact, operational Presidio publish step, or owned enforced minimum-share rule was found in these paths. |
| S-TEST | All eight tests/unit/eval files; eval-core model/policy tests and eval-dataset generator tests; scoped contract/integration searches for ama_eval, eval-runner, /api/eval and disaster-core-v1. Hits outside unit/package tests are other-feature fixtures/allowlists/per-agent gates, not the missing 030 contract/publish/projection/override assertions. Existing UI smoke assertions and eval page object were inspected, not ignored because their filenames differ. |
| S-CI | Both renamed eval workflows, [CI](../../.github/workflows/ci.yml#L1), [CD](../../.github/workflows/cd.yml#L1), [staging promotion](../../.github/workflows/staging-promotion.yml#L1), eval promotion policy, descriptive required-check configuration and Playwright config. Completed workflow searches found no /api/eval/gate consumer. |
| S-INFRA | All three eval Bicep modules, all three environment parameter files, provisioning policy, worker Dockerfile/build context and package dependencies. No eval job dispatcher, private-endpoint/network wiring, audit-projection implementation or active call to the standalone eval-rbac module was found in the inspected deployment chain. Compilation and deployment were not attempted. |
| S-UI | Both actual eval pages, typed client, proxy rewrite, Playwright discovery, interface-coverage smoke and eval page object. No comparison/progress/trace/gate/dataset-version journey assertion or dedicated dataset/gate/trace view was found in these scoped paths. Other features' outcome-evaluator tests are not LLM evaluation evidence. |
| S-EVIDENCE | All eight .eval-out CLI logs read completely; all six scorecards parsed completely; all members of all three archives read in memory without extraction. Manual guide, package READMEs, related risk-register entries, RAI register prose and the relevant recorded UI test result were inspected. Local artifacts lack source-SHA/signature/provider-trace attribution; their existence is not current-HEAD acceptance. No dedicated eval compliance mapping/SLO/WAF/security/a11y review record was found in local inputs or the scoped docs inventory/search. |

Explicit supersession is narrow: [CODEOWNERS](../../.github/CODEOWNERS#L28) records removal of the old
spec-029 progressive-delivery footprint, and eval workflow comments record the spec-031 credential
migration. This does not supersede spec-030's safety, approval, single-change scorecard or runtime limits.
Other renamed helpers/pages are credited as implementation evidence, not labelled SUPERSEDED without
an explicit retirement record. Original spec/tasks/checklists, index and evidence remain unchanged.

### Prioritised Findings

The following findings are ordered by impact; detailed follow-ups retain their stable IDs below.

| Priority | Finding and concrete source evidence | Follow-up |
| --- | --- | --- |
| Critical | [Unverified JWT claims](../../apps/api/app/middleware/eval_role_guard.py#L57) are trusted, and [upstream protected prefixes](../../apps/api/app/middleware/entra_auth.py#L36) exclude eval. | AUD-030-004 |
| Critical | [Viewer case-body access](../../apps/api/app/api/routes/eval/datasets.py#L71) and [unscoped anonymous trace access](../../apps/api/app/api/routes/eval/traces.py#L20) bypass the required content boundary. | AUD-030-005 |
| High | [Judge registration](../../apps/eval-runner/src/ama_eval/evaluators/judge.py#L95) is uncalled; required semantic/secondary scoring, exact attribution and complete denominators are missing. | AUD-030-002 |
| High | [Missing metrics are skipped](../../apps/eval-runner/src/ama_eval/gate.py#L76); [manual workflow](../../.github/workflows/eval-pr-gate.yml#L3) does not evaluate a changed prompt or enforce a scorecard gate. | AUD-030-010 |
| High | [All work is dispatched without cancellation polling](../../apps/eval-runner/src/ama_eval/orchestrator.py#L97), and [success precedes trace persistence](../../apps/eval-runner/src/ama_eval/runner.py#L150). | AUD-030-003 |
| High | [Provisioning constructs records only](../../apps/eval-runner/src/ama_eval/provisioner.py#L46); [reconciliation ignores expired nonterminal runs](../../apps/eval-runner/src/ama_eval/reconciler.py#L35). | AUD-030-012 |
| High | [All job roles share one entrypoint and incomplete settings](../../infra/bicep/modules/eval/eval-platform.bicep#L389); runner cannot write traces with the declared Blob Reader role. | AUD-030-013 |
| High | [Publication trusts manifests](../../apps/api/app/api/routes/eval/datasets.py#L24); [generator approval](../../packages/eval-dataset/src/ama_eval_dataset/generator.py#L147) is not safety review. | AUD-030-006 |
| High | [Corpus](../../packages/eval-dataset/data/dataset-disaster-core-1.0.0/cases.jsonl#L1) has contradictory prompt/action assignments, 1,997 out-of-scope v1 language codes and no recorded safety approvals. | AUD-030-007 |
| High | [Run snapshots lose subsets](../../apps/api/app/api/routes/eval/runs.py#L117); exact dataset bytes/metric/judge/policy state are not resolved or pinned. | AUD-030-008 |
| High | [Case-only trace keys](../../apps/eval-runner/src/ama_eval/runner.py#L198) cannot address every model/version; errors or missing settings are silently tolerated. | AUD-030-001 |
| High | [Caller-owned estimates](../../apps/api/app/api/routes/eval/runs.py#L42) and [unknown-model free prices](../../apps/eval-runner/src/ama_eval/cost.py#L38) do not enforce real cost/deployment caps. | AUD-030-009 |
| High | [Archive CLI inserts empty evidence categories](../../apps/eval-runner/src/ama_eval/evidence.py#L203), drops the detached signature and returns success on incomplete fetches. | AUD-030-011 |
| High | [Parameter binding](../../apps/eval-runner/src/ama_eval/runner.py#L124), [hard-coded model list](../../scripts/run_llm_evaluation.py#L100) and [absent modelVerdicts consumer](../../scripts/run_llm_evaluation.py#L1284) undermine comparison and operator success messages. | AUD-030-014 |
| High | [Exception logging](../../apps/eval-runner/src/ama_eval/orchestrator.py#L103) has no eval content scrubber or required per-case SLO instrumentation. | AUD-030-017 |
| High evidence gate | [Recorded succeeded run](../../.eval-out/execute.log#L15) has [empty metrics](../../.eval-out/01P2RF55BY7T0NQD6PKM4THG6P/scorecard.json#L5); approvals and representative full-run outcomes remain UNVERIFIED. | AUD-030-018 |
| Important | [Dashboard winner shape](../../apps/web/src/app/eval/[runId]/page.tsx#L94) differs from the API; expected views, identity propagation and live progress are incomplete. | AUD-030-015 |
| Important | [CI discovery](../../.github/workflows/ci.yml#L141) excludes the principal eval suites; tests lack required contract/integration assertions and leak fake evidence to a shared output path. | AUD-030-016 |

### Recorded Artifact Assessment

Static corpus inventory: 5,000 unique case IDs; 338 unique prompt texts; 312 prompt texts with multiple
expected actions; all records synthetic and labelled approved, with zero safety-reviewer approval entries.
There are 500 retrieval-scope cases and 500 injection-labelled cases. Language counts: en-AU 3,003;
en-NZ 501; vi-VN 500; zh-Hans-CN 497; ar-SA 499. These are text/JSON inventory results, not model scores.

| Hazard | Cases | Share |
| --- | --- | --- |
| structure-fire | 425 | 8.5% |
| bushfire | 400 | 8.0% |
| flood | 475 | 9.5% |
| storm | 375 | 7.5% |
| building-collapse | 325 | 6.5% |
| hazmat | 325 | 6.5% |
| mass-casualty | 350 | 7.0% |
| missing-person | 350 | 7.0% |
| fatality-report | 350 | 7.0% |
| remains-recovery | 275 | 5.5% |
| evacuation-order | 375 | 7.5% |
| public-info | 475 | 9.5% |
| crisis-distress | 500 | 10.0% |

The [manifest](../../packages/eval-dataset/data/dataset-disaster-core-1.0.0/manifest.json#L5) declares hash
`sha256:3e8046676110c3b44be06ac0a5ac12fb2499b7a2c8d2e102477c8585b4eff08b` over the generator's canonical
JSON array. The committed raw JSONL SHA-256 is
`027055d372130e092e41c46c26f6c4d9084b920b2ce902d7bc8b3c7342af3ce6`. Different algorithms explain this
difference; it is a contract mismatch, not by itself evidence of tampering. The manifest's file URI and
author-generated approval do not prove an immutable remote publication.

| Record inspected | What it supports | What it does not establish |
| --- | --- | --- |
| [provision.log](../../.eval-out/provision.log#L1), [provision2.log](../../.eval-out/provision2.log#L1) | Timestamped local non-dry-run CLI narratives for platform provision/image build and health probes. Both accept latest ACR run status after wrapper errors. | No source SHA/image digest linkage, complete ARM evidence, per-run lifecycle, cleanup window or current deployment guarantee. |
| [publish.log](../../.eval-out/publish.log#L23), [publish2.log](../../.eval-out/publish2.log#L23), [publish3.log](../../.eval-out/publish3.log#L23) | Existing-blob warnings, two API registration 500s, then recorded 201 with anonymous mode detected. | No retrieved-byte/hash comparison, independent safety approval, required publication pipeline, or immutable-storage lock proof. |
| [execute.log](../../.eval-out/execute.log#L11) with [01P2 scorecard](../../.eval-out/01P2RF55BY7T0NQD6PKM4THG6P/scorecard.json#L1) | A run ID, queued/succeeded polling and a saved one-model scorecard with empty metrics; the CLI logs an empty model-verdict list. | No attributable successful model response, grade suite, full workload, cost, safety gate or valid comparison. |
| [01GKK scorecard](../../.eval-out/01GKK252J837Q5HVWQTZ9HCFWA/scorecard.json#L1), [01XH scorecard](../../.eval-out/01XHMBGN440NZ70NV6BQ3Y24HJ/scorecard.json#L1) | Three-model and one-model maps respectively, both with no metric cells. | Not a passing multi-model evaluation; no original output/judge/performance provenance. |
| [01S8 scorecard](../../.eval-out/01S8FV6FXGRP9RPMWHPB7HVWGP/scorecard.json#L1) | Seven model keys, nine rule metric IDs, 63 aggregate cells; base sample count five, retrieval count two; 42 failing aggregate cells. | No 5,000-case run, primary/secondary judge, cost/baseline, provider traces or independently verified model availability. |
| [01FB scorecard](../../.eval-out/01FB3PRZY147VMN6K0HKN3G1TT/scorecard.json#L1) | Seven model keys, nine rule metric IDs, 63 aggregate cells; base sample count 25, retrieval count three; 42 failing aggregate cells. | No full-run/week/p95 evidence; latency-budget mean 1.0 is not raw latency or proof of provider success. |
| [r-1 scorecard](../../.eval-out/r-1/scorecard.json#L1) | Mock-shaped `modelVerdicts: []`, directly produced by the [CLI auth test fixture](../../tests/unit/eval/test_run_llm_evaluation_script.py#L758). | Not a Foundry run, gate pass, approval or acceptance record. |
| [archive.log](../../.eval-out/archive.log#L21), [archive2.log](../../.eval-out/archive2.log#L9) | First archive upload reports missing file; second records bundle creation and an upload success message. | Successful upload does not prove signature, correct target environment, data completeness or retention. |
| Three local evidence.tar files under runs 01FB, 01GKK and 01P2 above | Every archive contains run.json, scorecard.json and a hash manifest, but audit-events.json is `[]` and dataset-manifest/metric-set/judge-set/model-registry are `{}`. No signature, original traces or standalone lifecycle record member exists. | No signed reproducible evidence chain, independent historic replay or trustworthy approvals. Member inventory was read in memory; no extraction or product code ran. |
| [UI JUnit record](../../tests/e2e/web-coverage/_artifacts/junit/web-coverage.xml#L143) | The named eval route-smoke testcase is recorded as skipped. [Source assertion](../../tests/e2e/interface-coverage.spec.ts#L623) checks an h1, not comparison correctness. | No T040 comparison/SSE/role test pass or WCAG 2.2 AA audit. |
| [Responsible AI register](../../docs/governance-hub/rai-register/responsible-ai-register.md#L18), [risk 004](../../docs/risk-register/RISK-NEW-004.md#L9), [risk 006](../../docs/risk-register/RISK-NEW-006.md#L9) | Authored posture/treatment references to spec 030. The register declares manual-row ratio 1.00 and an author sign-off label. | Not actual run-level evidence, safety-reviewer approval or proof that the grounding gate/quarterly recalibration operated. |

The records above are historical local artifacts, not assumed to be committed at the reviewed HEAD.
They were not rerun. In particular, an old succeeded/empty scorecard does not disprove the newer source's
all-cases-raise safeguard; it demonstrates why status strings alone are insufficient evidence.

## Findings and Remediation

### Trace Persistence Does Not Distinguish Models

- [ ] AUD-030-001 Preserve each model's traces without overwrite or silent loss

**Affected obligations:** T029, T034, T073; FR-004, FR-015, FR-021, FR-026; SC-006, SC-012.

**Expected versus observed:** A comparison must retain independently addressable traces for every
case/model pair. The [runner](../../apps/eval-runner/src/ama_eval/runner.py#L198) uploads to
`runs/{run_id}/traces/{caseId}.json` with `overwrite=True`; the path does not distinguish models.
The upload also returns without persistence when its container setting is absent and logs storage
failures without failing the completed run. Multi-model persistence and historical evidence cannot
be inferred from a successful scorecard.

**Developer:** Reconcile the trace writer and trace consumers around a run/case/model/version identity.
Preserve existing readable artifacts, prevent overwriting another model's output, and surface artifact
persistence failures in the durable run outcome. The [reader](../../apps/api/app/api/routes/eval/traces.py#L20)
also lacks model/version selection and pagination. Persist blob version IDs when versioned storage is used;
do not infer that physical historical versions were deleted. An overwrite-enabled store changes the current
case-only object; a protected store can reject the write, which the current code merely logs. Both prevent
reliable model-qualified retrieval. Use safe identifiers for catalog names containing slashes and preserve
legacy read compatibility. Dependencies: AUD-030-003, AUD-030-005, AUD-030-008, AUD-030-011, AUD-030-013.

**Tester:** Extend [test_orchestrator_e2e.py](../../tests/unit/eval/test_orchestrator_e2e.py#L91) and
[test_api_dev_integration.py](../../tests/unit/eval/test_api_dev_integration.py#L1) with fake persistent
storage/read adapters. Contrast two models and two versions of one model on the same case, slash-containing
catalog IDs, retry of identical/different bytes, a protected blob, missing configuration and a failed upload.
Assert independent retrievable outputs/rationales, idempotent same-content writes and truthful durable status.

**Future validation:** After storage/identity repair and with transport-only fakes, run
`pytest tests/unit/eval/test_orchestrator_e2e.py tests/unit/eval/test_api_dev_integration.py -q`.
**Complete when:** the production writer/reader preserve every case/model/version trace and persistence
failures cannot be reported as complete evidence. No upload or test execution was performed in this audit.

### Scoring Does Not Bind the Required Judge and Metric Versions

- [ ] AUD-030-002 Execute and record the complete versioned metric and judge plan

**Affected obligations:** T009, T010, T019, T029, T030, T031, T031a, T032, T033, T034;
FR-001, FR-002, FR-003, FR-003a, FR-003b, FR-004, FR-025, FR-026; SC-001, SC-006.

**Expected versus observed:** The production [orchestrator](../../apps/eval-runner/src/ama_eval/orchestrator.py#L89)
uses the import-time evaluator registry. Importing [judge.py](../../apps/eval-runner/src/ama_eval/evaluators/judge.py#L94)
does not invoke its registration function. The runner never calls that function or binds a judge.
The [scorecard builder](../../apps/eval-runner/src/ama_eval/scorecard.py#L74) emits empty disagreement and
regression diagnostics. A metric-set version string is not evidence that the version's evaluators ran.
The [result type](../../apps/eval-runner/src/ama_eval/evaluators/base.py#L36) has no metric version, tier,
or judge identity fields. Retrieval scoring is token overlap rather than the specified ranked retrieval
metrics; rank/k/nDCG and exact ground-truth/structured-output/escalation checks are not implemented.
Empty answers can pass rule refusal correctness when an answer was expected. A negated forbidden phrase
is still a substring violation; output classification ignores its expected-action argument and classifies
empty filtered output differently from the refusal evaluator. The model call receives a constant system
prompt and one user prompt, not the case conversation or retrieved context. Missing evaluator results
shrink denominators while scorecard pass/fail uses a hard-coded 95% rather than versioned metric policy.

**Developer:** Bind an immutable, active metric plan and primary/secondary judge versions before execution;
fail closed on unavailable required evaluators; preserve applicability, scoring scales, thresholds,
judge attribution and sampling configuration through aggregation and traces. Do not silently substitute
keyword checks for the authored semantic metrics. Keep deterministic checks where sufficient. Owning
files: the existing orchestrator, evaluator modules and scorecard builder cited above, plus shared metric
models. Dependencies: AUD-030-007/008 for coherent rubrics/active snapshots and AUD-030-014 for effective
judge/model invocation. Keep old result readers compatible while versioning the enriched trace schema.

**Tester:** Extend [test_orchestrator_e2e.py](../../tests/unit/eval/test_orchestrator_e2e.py#L91) and
[test_foundry_failures.py](../../tests/unit/eval/test_foundry_failures.py#L157) with instrumented fake judges,
missing registrations, disagreement samples, malformed judge JSON, empty output and ranked-context fixtures.
Add missing conversations/context, negated prohibitions, uncertainty/referral answers, malformed structured
output, unlabeled injection and reversed retrieval ranks. Assert invoked metric/version sets, attribution,
denominator completeness, semantic/rule tier proportions, independent sampling and explicit failures.

**Validation and completion:** Future-only `pytest tests/unit/eval/test_orchestrator_e2e.py
tests/unit/eval/test_foundry_failures.py -q`, after dependency/bootstrap repair and with external calls
replaced at the transport boundary. Passing requires all required metrics and attribution to be present;
actual model quality and performance still require separately attributable executions.

### Run Completion Can Hide Failures and Ignore Cancellation

- [ ] AUD-030-003 Make run lifecycle, cancellation and partial-result state truthful

**Affected obligations:** T028, T029, T035, T041, T053, T054, T056, T057, T060, T085;
FR-017, FR-018, FR-019, FR-028, FR-029; SC-002, SC-003, SC-011.

**Expected versus observed:** The [cancel route](../../apps/api/app/api/routes/eval/runs.py#L209) saves
`cancelling`, but the [orchestrator](../../apps/eval-runner/src/ama_eval/orchestrator.py#L97) submits every
case without polling the repository. It catches case/evaluator failures and continues; only a model with
zero successful cases raises. The [runner](../../apps/eval-runner/src/ama_eval/runner.py#L150) saves
`succeeded` before best-effort trace upload. Its main path has no unconditional provisioner teardown,
no durable per-case checkpoint and no cancelled/orphan exit-code branch.

**Developer:** Make the run controller own start/progress/cancel/failure/partial/terminal transitions,
bounded dispatch, durable checkpoints, timeout enforcement and unconditional owned-resource teardown.
Persist all partial traces before terminal state; distinguish inference failures from rubric failures.
Handle retries without losing prior checkpoints or overwriting a newer cancellation state. Owners:
runner/orchestrator, existing run routes/repository and job invoker; persist job-start failure instead of
leaving a silently stuck queue entry. Dependencies: AUD-030-001, AUD-030-008, AUD-030-009, AUD-030-012,
AUD-030-013. Preserve existing run IDs and terminal records; do not mutate a completed run into a new attempt.

**Tester:** Extend the existing orchestrator and failure tests cited above, using fake transport,
repository, clock and resource adapters. Exercise one failure among successes, all transport errors,
evaluator failure, cancellation before dispatch and mid-batch, deadline expiry and teardown failure.
Assert processed/failed/remaining counters, preserved traces, audited transitions and exit codes 0/1/2/3.

**Validation and completion:** Future-only
`pytest tests/unit/eval/test_orchestrator_e2e.py tests/unit/eval/test_foundry_failures.py tests/unit/eval/test_api_dev_integration.py -q`
after the listed repairs, with isolated dependencies and fake external transports. All failure/cancel
branches must preserve attributable partial results and reconcile only owned resources. Runtime cleanup
guarantees remain UNVERIFIED until a later approved live exercise.

### Evaluation Authentication Does Not Verify the Bearer Token

- [ ] AUD-030-004 Verify evaluation principals at a fail-closed authentication boundary

**Priority:** Critical. **Affected obligations:** T020, T036, T065, T070, T073, T074, T086,
T091, T092; FR-021, FR-022, FR-022a, FR-024; SC-009, SC-012.

**Expected versus observed:** [The evaluation guard](../../apps/api/app/middleware/eval_role_guard.py#L57)
base64-decodes caller-supplied JWT claims and trusts their roles. The
[general auth middleware](../../apps/api/app/middleware/auth_middleware.py#L18) only populates claims;
the [Entra verifier's protected prefixes](../../apps/api/app/middleware/entra_auth.py#L36) exclude eval.
The current source therefore does not establish the signature/issuer/audience/expiry validation claimed
by the eval guard. Dev bearer-token permission is also based on a truthy environment variable, not a
dev-only environment check. Live ingress configuration remains unverified.

**Developer:** Reuse verified Entra principal state or an explicitly enforced, non-bypassable gateway
contract. Validate signature, issuer, audience, expiry and principal; map the contract's evaluator,
safety and governance roles without granting publishing/override powers to a generic operator.
Restrict legacy dev tokens to dev and reject unsafe startup configuration outside dev. Owner is
eval_role_guard.py with main.py/Entra middleware and eval deployment configuration. Coordinate with
AUD-030-005/013; shared authentication changes must preserve unrelated API routes' established contracts.

**Tester:** Extend [test_eval_role_guard_anonymous.py](../../tests/unit/eval/test_eval_role_guard_anonymous.py#L1)
and [test_api_dev_integration.py](../../tests/unit/eval/test_api_dev_integration.py#L1). Use fake identity
transport with valid signed claims, altered payload/signature, expiry, wrong issuer/audience, roleless staff,
wrong privileged role, `EVAL_ALLOW_DEV_TOKENS=0`, and staging/prod dev-token attempts. Assert 401/403 before
any mutation; keep the explicit anonymous-dev flow available only within its content boundary.

**Validation and completion:** Future-only
`pytest tests/unit/eval/test_eval_role_guard_anonymous.py tests/unit/eval/test_api_dev_integration.py -q`
after identity dependencies are available, without network calls. Complete when direct API ingress cannot
grant roles from unverified claims and the configuration/role contract agrees at every environment boundary.

### Dataset and Anonymous Access Bypass the Content Tier

- [ ] AUD-030-005 Enforce content-aware access and audit every sensitive read

**Priority:** Critical. **Affected obligations:** T020, T036, T049, T070, T072, T073, T074,
T083, T091, T093, T095; FR-012, FR-021, FR-022, FR-022a, FR-023; SC-009, SC-012.

**Expected versus observed:** [Case enumeration](../../apps/api/app/api/routes/eval/datasets.py#L71)
uses the summary-viewer dependency yet returns full case inputs. Anonymous scope checks only the
dataset identifier, not provenance or labels. [Trace reads](../../apps/api/app/api/routes/eval/traces.py#L20)
do not check the run's dataset/content eligibility, and their audit metadata omits anonymous environment
tagging. Anonymous roles include the trace reader role, so the dataset-name allow-list is insufficient.

**Developer:** Apply Tier-2 protection to case bodies and trace/evidence access; keep safe summaries
available to authenticated staff. Resolve actual immutable dataset/run content before granting anonymous
access, fail closed if eligibility is unknown, and reject real-derived or disallowed sensitivity labels.
Apply the same checks to list, cancel, winner, audit and export surfaces. Preserve principal, environment,
run, case and model in access events without putting sensitive content into summary channels. Owners:
existing dataset/run/scorecard/trace routes and role guard; dependencies AUD-030-004/006/008/011. Keep
Tier-1 summary schemas usable without adding raw case content as a workaround for missing detail views.

**Tester:** Extend the existing API/anonymous tests cited above with one allowed synthetic dataset name
containing a real-derived case, a graphic-label sentinel, an allowed dev fixture and a different dataset.
Exercise every reader and mutator as anonymous, viewer, evaluator, safety reviewer and governance reviewer;
assert denial before data exposure, correct audit metadata and zero sentinels in Tier-1 JSON/HTML.

**Validation and completion:** Future-only
`pytest tests/unit/eval/test_eval_role_guard_anonymous.py tests/unit/eval/test_api_dev_integration.py -q`
after AUD-030-004 and content fixtures are in place, with fake stores/identity. Require explicit positive
and negative role/content matrices, not just dataset-name tests. Never interpret a local synthetic principal
or an authored approval string as an authenticated human approval.

### Publication Trusts Authored Metadata Instead of Reviewed Content

- [ ] AUD-030-006 Enforce reviewed, immutable and PII-screened publication

**Priority:** High. **Affected originals:** T018, T042, T043, T047, T048, T049, T050, T052,
T078, T079, T080, T081; FR-007, FR-008, FR-009, FR-011, FR-012, FR-021, FR-023; AS-2.1,
AS-2.2, AS-6.1; SC-005, SC-009.

**Expected/actual/impact:** The [publish route](../../apps/api/app/api/routes/eval/datasets.py#L24)
accepts a caller's complete manifest and operator role without loading cases, checking actual approvals,
scanning PII, enforcing the hazard floor, or writing immutable blobs. Its read-then-upsert check is not
atomic. [Repository saves](../../apps/api/app/repositories/eval/repositories.py#L140) can replace published
versions and cases directly. [Manifest construction](../../packages/eval-dataset/src/ama_eval_dataset/manifest.py#L49)
sets published state and creates an author approval itself. The
[replacement publish workflow](../../.github/workflows/eval-publish-dataset.yml#L3) is manual-only; its
Azure upload/register block is commented out. [CODEOWNERS](../../.github/CODEOWNERS#L16) has no eval
dataset owners. [Sanitisation](../../apps/eval-runner/src/ama_eval/sanitise.py#L16) is a regex helper,
not a Presidio-backed candidate/publication workflow. This permits unreviewed or inadequately redacted
data to be labelled published; the source cannot establish APP consent/policy clearance.

**Developer:** Put approval verification and actual content validation in one publication service used by
API and CI. Require authenticated safety-reviewer approval bound to the content hash, and independent
governance approval plus consent/policy clearance for sanitised-real content. Run a second PII screen at
publication; preserve a non-sensitive, schema-compatible sanitisation log. Use conditional create/version
checks, immutable content writes and compensating audit events. Verify the exact remote bytes before
treating an existing blob or HTTP 409 as success. Retain the current JSONL layout; preserve old published
versions. Dependencies: AUD-030-004, AUD-030-005, AUD-030-008, AUD-030-011. Do not weaken approval rules
to accept the current generated corpus.

**Tester:** Extend [test_api_dev_integration.py](../../tests/unit/eval/test_api_dev_integration.py#L35),
[test_generator.py](../../packages/eval-dataset/tests/test_generator.py#L17), and
[test_sanitise.py](../../tests/unit/eval/test_sanitise.py#L18). Positive: approved synthetic cases and
properly de-identified real cases with distinct reviewers. Negative/edge: spoofed approval strings,
draft case, wrong reviewer, residual name/DOB/address/phone in conversation or context, absent consent,
empty sanitisation log, same-version concurrent publishes, different remote hash, storage failure and
partial publish. Assert rejection before publication, immutable prior bytes, correct content hash and
complete audit events. Existing tests that accept five unapproved cases must not define the production rule.

**Future validation:** With configured Python dependencies and transport-only fakes, run
`pytest tests/unit/eval/test_api_dev_integration.py tests/unit/eval/test_sanitise.py packages/eval-dataset/tests -q`.
Expected: the positive/negative matrix above passes without real interactions or cloud calls.
**Complete when:** no API/CI path bypasses review, PII screening, distribution validation or immutable publication;
actual reviewer decisions are separately attributable and never fabricated by the generator.

### Corpus Quantity Masks Rubric and Language Conflicts

- [ ] AUD-030-007 Curate a coherent English-only v1 corpus and enforce coverage floors

**Priority:** High. **Affected originals:** T026, T042, T044, T045, T046, T052, T089;
FR-006, FR-007, FR-008, FR-010, FR-011, FR-025; SC-001, SC-005, SC-009; research D7/D8.

**Expected/actual/impact:** Read-only parsing of the entire
[committed corpus](../../packages/eval-dataset/data/dataset-disaster-core-1.0.0/cases.jsonl#L1)
found 5,000 unique IDs, 338 distinct prompt texts and 312 prompt texts assigned multiple expected actions.
The [generator](../../packages/eval-dataset/src/ama_eval_dataset/generator.py#L111) allocates actions
independently of the selected template's suggested action. It marks cases approved but supplies only a
draft approval entry. All 5,000 are synthetic, with zero safety-reviewer approval entries. The
[distribution](../../packages/eval-dataset/src/ama_eval_dataset/distribution.py#L23) targets five languages;
only 3,003 records are en-AU, and 1,997 are outside v1's en/en-AU restriction. The distribution helper
computes statistics, not an enforced safety-reviewer-owned minimum-share floor. Repeating prompt text
with contradictory rubrics can reward/refute identical model behavior arbitrarily.

**Developer:** Couple each case's scenario, expected action, language, jurisdiction and rubric; preserve
uncertainty/referral cases without inventing a single factual answer. Resolve the deterministic-template
versus Foundry-generation D8 conflict explicitly with the spec owner; do not call template output a model
generation result. Produce drafts for independent SME/safety review, enforce all 13 hazards and an owned,
versioned minimum share, and create a reproducible 50-case smoke fixture spanning at least three hazards
and two actions. Keep multilingual schema capacity for later versions but enforce English-only v1.
Add version input to the generator rather than changing only its output directory. Dependencies:
AUD-030-002, AUD-030-006, AUD-030-008. Never overwrite the existing published-labelled v1 artifact.

**Tester:** Extend [test_generator.py](../../packages/eval-dataset/tests/test_generator.py#L38).
Test each hazard/action archetype, a missing hazard, the exact minimum-share boundary, 4,999/5,000 and
10,001 cases, same/different seed, duplicate IDs, duplicate prompts with contradictory actions,
English-only v1 and multilingual later versions, realistic jurisdiction referrals and injection cases.
Assert draft state, no synthesized human approval, consistent rubric/action pairs and version/hash changes.

**Future validation:** After dependencies and an approved coverage policy exist, run
`pytest packages/eval-dataset/tests -q`; then, only in a later authorised authoring phase, generate a new
version and obtain SME/safety review. Expected: coherent coverage, not a higher filename/row count alone.
**Complete when:** a genuinely approved, content-addressed v1 meets the coverage/language rules, the smoke
fixture is usable, and any broader language/generation strategy has explicit scoped supersession evidence.

### Run Contracts, Subsets and Reproduction Snapshots Diverge

- [ ] AUD-030-008 Preserve authoritative run inputs and reconcile schema and API contracts

**Priority:** High. **Affected originals:** T009, T010, T013, T024, T027, T028, T029, T034,
T035, T037, T047, T049, T063, T073, T089, T090; FR-002, FR-004, FR-008, FR-009, FR-010,
FR-014, FR-021, FR-026, FR-027; SC-004, SC-006, SC-012.

**Expected/actual/impact:** [CreateRunRequest](../../apps/api/app/api/routes/eval/runs.py#L35) accepts
flat dataset/model fields and returns 201, unlike the nested refs and 202 in the
[contract](contracts/api.md#L89). The constructor drops `datasetSubset`; only its `maxCases` is passed
transiently to the job. The [loader](../../apps/eval-runner/src/ama_eval/runner.py#L101) reads repository
cases first, otherwise a constructed blob path, never verifies the manifest hash, and uses prefix slicing
instead of filtering/stratification. No published-dataset or active-metric check occurs at enqueue.
[Models](../../packages/eval-core/src/ama_eval_core/models.py#L317) omit required definition text,
judge-version bindings and strict immutable run snapshots. The
[run schema](../../packages/eval-core/src/ama_eval_core/schemas/run.schema.json#L40) requires semver for
`metricSetVersion`, while the CLI uses `disaster-core-v1`. JSON schemas omit case cross-field conditions
and reject optional nulls emitted by corpus serialization. The hash algorithm is a canonical JSON array,
not the specified canonical JSONL bytes. Historical replay cannot recover the exact chosen inputs.

**Developer:** Resolve the API/schema contract under explicit versioning, retaining compatibility for
existing flat clients and saved artifacts. Resolve published dataset, immutable bytes/hash, exact subset
criteria plus selected IDs/seed, active metric/judge definitions, model deployment/version/parameters,
policy and baseline at enqueue and persist them. Verify all references before creating resources. Apply
all five subset dimensions and deterministic stratification consistently across modes; handle empty
subsets explicitly. Align all entity schemas/nullability and enforce cross-entity invariants in services,
not only Pydantic. Add optimistic concurrency and stable idempotency for the approved change/mode contract
without deduplicating independent ad-hoc runs. Dependencies: AUD-030-002, AUD-030-006, AUD-030-009, AUD-030-010.

**Tester:** Extend [test_models.py](../../packages/eval-core/tests/test_models.py#L62),
[test_api_dev_integration.py](../../tests/unit/eval/test_api_dev_integration.py#L65), and the existing
orchestrator tests. Cover every entity/schema, real corpus serialization including nulls, missing/draft
versions, inactive/mutated judges, tampered bytes, same semantic data with different canonical bytes,
every filter and intersections, empty/one-case subsets, retry and concurrent independent runs. Assert exact
selected IDs and snapshots survive a fresh repository instance; no silent defaults or dropped fields.

**Future validation:** With local fakes and all eval packages available, run
`pytest packages/eval-core/tests/test_models.py tests/unit/eval/test_api_dev_integration.py tests/unit/eval/test_orchestrator_e2e.py -q`.
Expected: API and persisted artifacts satisfy one versioned contract and replay uses the recorded subset.
**Complete when:** all model/schema invariants and API response shapes are assertion-covered and an independent
reviewer can select the exact original inputs without consulting mutable configuration.

### Cost and Deployment Limits Are Not Authoritative

- [ ] AUD-030-009 Derive and enforce run budgets before allocating resources

**Priority:** High. **Affected originals:** T007, T012, T013, T028, T055, T058, T059,
T060, T067a, T082, T088; FR-001(i), FR-018, FR-019, FR-020; SC-002, SC-008.

**Expected/actual/impact:** The [actual policy file](../../infra/policy/eval/provisioning-policy.dev.yaml#L10)
exists, but the [API](../../apps/api/app/api/routes/eval/runs.py#L78) uses a hard-coded dev policy in every
environment. [Policy evaluation](../../packages/eval-core/src/ama_eval_core/policy.py#L90) permits omitted
region/SKU and counts in-flight runs rather than all deployments. It trusts submitted cost/duration;
the [CLI](../../scripts/run_llm_evaluation.py#L1194) submits AUD 0 and 60 minutes. The
[cost helper](../../apps/eval-runner/src/ama_eval/cost.py#L31) is disconnected from the run, defaults unknown
models to free and omits judge/storage/provision costs. A seven-model request can pass the API's six-deployment
cap; PR-fast mode's default estimate is rejected rather than selecting a bounded fast subset.

**Developer:** Load a versioned environment-specific policy and trusted prices keyed by model/version,
region and SKU; resolve omitted deployment fields before validation. Estimate complete MUT/judge/sample,
storage and provisioning usage, reserve deployment capacity atomically across runs, fail closed on unknown
prices/invalid numeric inputs, and enforce an end-to-end deadline. Keep independent requests independent
while sharing only explicitly safe leases. Record estimates, actuals/availability, currency, breakdown
and cap decisions on the run and scorecard. Distinguish data-region policy from approved model-host carve-outs.
Dependencies: AUD-030-008, AUD-030-012, AUD-030-013; do not trust user estimates as a cost control.

**Tester:** Extend [test_policy.py](../../packages/eval-core/tests/test_policy.py#L35) and
[test_phase5_6_modules.py](../../tests/unit/eval/test_phase5_6_modules.py#L126). Cases: exact/below/above
cost and duration caps, missing price, seven models versus six slots, concurrent reservations, missing
region/SKU, non-AU data region, allowed model exception, invalid/negative estimates and judge sampling cost.
Assert zero resource calls on rejection, stable snapshot, explicit unavailable actuals and consistent totals.

**Future validation:** With deterministic price/clock/resource fixtures, run
`pytest packages/eval-core/tests/test_policy.py tests/unit/eval/test_phase5_6_modules.py -q`.
Expected: hard pre-provision policy rejection and truthful cost reporting. **Complete when:** no request
can bypass budgets by omitting metadata or declaring zero cost; live cost/performance guarantees remain
subject to the later representative-window evidence task AUD-030-018.

### Release Gating Is Disconnected and Can Accept Incomplete Scores

- [ ] AUD-030-010 Bind fail-closed release gates to the evaluated change and baseline

**Priority:** High. **Affected originals:** T028, T034, T061, T062, T063, T064, T065,
T066, T067, T068, T069; FR-004, FR-024, FR-027; AS-4.1, AS-4.2; SC-007.

**Expected/actual/impact:** [Gate evaluation](../../apps/eval-runner/src/ama_eval/gate.py#L39) skips missing
metrics; a non-empty model map containing an empty metric map can pass. It reads `baseline.metrics`,
not the emitted `perModel` scorecard or stored baseline pointer. The
[router](../../apps/api/app/api/routes/eval/router.py#L40) has no gate/check/override or baseline-designation
writer. The [replacement PR workflow](../../.github/workflows/eval-pr-gate.yml#L3) is manual-only; it
starts a job without a persisted run/dataset identity, polls the latest execution, and fails only on an
explicit Failed status. Missing config/timeouts can finish without a failing gate. It never calls the
metric gate. The CLI checks absent `modelVerdicts`, while the
[orchestrator prompt](../../apps/eval-runner/src/ama_eval/orchestrator.py#L153) ignores the changed prompt/RAG
configuration. The old 029 integration target is explicitly removed in
[CODEOWNERS](../../.github/CODEOWNERS#L28); current [CD](../../.github/workflows/cd.yml#L18) has no eval
consumer. Descriptive [required checks](../../.github/branch-protection.json#L2) omit eval. No actual merge
protection or override approval is established by this audit.

**Developer:** Pin candidate source SHA/prompt/retrieval/model configuration and baseline scope; evaluate
the candidate, not a constant assistant prompt. Add the documented check/override surface and baseline
designation/supersession audit. Require all applicable metrics, sample floors, complete execution,
compatible metric versions and baseline; reject pending/missing/stale/error states. Produce sample-level
diagnostics privately, preserve one authoritative change evidence record with clear fast/full coverage,
and resolve the contract's `(changeRef, mode)` versus single-scorecard ambiguity explicitly. Wire path-scoped
PR triggers and the approved replacement promotion surface; do not silently recreate retired 029 machinery.
Overrides require authenticated governance identity, >=50-character justification, approvers, record link,
immutable audit and safety notification. Dependencies: AUD-030-002, AUD-030-003, AUD-030-004, AUD-030-008,
AUD-030-011. Preserve the explicitly documented credential migration separately from gate semantics.

**Tester:** Extend [test_phase5_6_modules.py](../../tests/unit/eval/test_phase5_6_modules.py#L142) and API tests;
use actual emitted scorecard/baseline shapes, not a hand-shaped alternate baseline. Contrast unchanged
candidate and degraded prompt, missing metric/model/baseline, disjoint subsets, timed-out/failed jobs,
two concurrent job executions, same change retry, different modes/users, and short/unauthorised overrides.
Assert fail-closed decisions, correct change/run linkage, sample IDs, audit and notification exactly once.

**Future validation:** Offline fakes first:
`pytest tests/unit/eval/test_phase5_6_modules.py tests/unit/eval/test_api_dev_integration.py -q`.
Later authorised PR/promotion trials must demonstrate rejection on first attempt and inspect the installed
required check. **Complete when:** both active delivery surfaces consume attributable gate evidence and
cannot pass using a successful job status, empty result, wrong execution or undocumented override.

### Archived Evidence Is Empty, Unsigned and Not Durably Projected

- [ ] AUD-030-011 Seal complete evidence and retain append-only audit records

**Priority:** High. **Affected originals:** T011, T014, T017, T018, T021, T070, T071,
T072, T073, T075, T076, T077, T081, T093; FR-003, FR-014, FR-021, FR-022, FR-026;
SC-004, SC-006, SC-009, SC-012.

**Expected/actual/impact:** The [bundle builder](../../apps/eval-runner/src/ama_eval/evidence.py#L43)
uses current timestamps in a tar.gz rather than a deterministic signed zip; its signature is returned
separately and signing failure yields an unsigned bundle regardless of environment. Its
[CLI](../../apps/eval-runner/src/ama_eval/evidence.py#L173) supplies empty audit/dataset/metric/judge/model
manifests, substitutes empty payloads on HTTP errors, and writes only bundle bytes. All three inspected
local archives confirm those five empty members and no signature member. The archive driver does not
propagate the resolved API URL/token/vault URI and ignores the bundler's exit code. The run path never
automatically builds a bundle. Repository mutators do not all emit audit events, and the daily projection
job has no implementation. [Retention](../../infra/bicep/modules/eval/eval-platform.bicep#L186) is 2,555
days since blob creation, not at least seven calendar years after run completion; dev disables it,
staging/production are initially unlocked, and selecting Locked does not execute a lock operation.

**Developer:** Assemble evidence from immutable run snapshots, every model trace, actual approvals and
all lifecycle/cost/audit records. Fail closed on missing required members, signature failure or unresolved
references outside an explicitly labelled non-production diagnostic mode. Use the approved signer and
include signature, key version/algorithm and trust material with deterministic member serialization.
Pass the selected environment explicitly, implement authenticated JSON/HTML/bundle exports, daily
idempotent Cosmos-to-immutable-Blob projection with durable watermarks, and repository-level mutation
audits. Use compensating events, never destructive correction. Retain artifacts through at least seven
calendar years after completion and record the independent lock/approval state. Dependencies:
AUD-030-001, AUD-030-004, AUD-030-005, AUD-030-008, AUD-030-013.

**Tester:** Extend [test_phase2_foundations.py](../../tests/unit/eval/test_phase2_foundations.py#L126)
and CLI tests. Test byte-identical repeated assembly with fixed metadata, all required members, missing
trace, tampered hash/signature, wrong run/version/key, Key Vault denial, HTTP 401/404/500, wrong environment,
projection restart/duplicate/late event and leap-year retention. Assert no unsigned production success,
all events projected within 24 hours, and no raw content in Tier-1 exports.

**Future validation:** With fake repository/blob/signer adapters and no cloud credentials, run
`pytest tests/unit/eval/test_phase2_foundations.py tests/unit/eval/test_run_llm_evaluation_script.py -q`.
A later authorised reviewer must verify a historical bundle and replay from its recorded inputs.
**Complete when:** archive contents, signatures, storage retention and retrieval agree; a hash of empty
objects, an upload log or a signer configuration string is never treated as a complete evidence chain.

### Provisioner and Reconciler Do Not Implement the Resource Lifecycle

- [ ] AUD-030-012 Implement owned-resource provisioning, leases and bounded reconciliation

**Priority:** High. **Affected originals:** T015, T016, T029, T053, T054, T055, T056,
T057, T060, T085, T086; FR-016, FR-017, FR-018, FR-019, FR-029; AS-3.1, AS-3.2, AS-3.3;
SC-002, SC-003, SC-008, SC-011.

**Expected/actual/impact:** [provision_models](../../apps/eval-runner/src/ama_eval/provisioner.py#L46)
returns deployment records and emits provisioned events without calling its resource adapter. It has no
What-If, RG creation, lease acquisition or Bicep invocation. Deletion supplies the deployment name as the
account name and swallows errors. [Reconciliation](../../apps/eval-runner/src/ama_eval/reconciler.py#L35)
requires a terminal run, so a crashed nonterminal run is not an orphan; it expects `eval-runId` tags while
the [deployment module](../../infra/bicep/modules/eval/foundry-deployments.bicep#L38) defines `runId`.
Both emit subject type `deployment`, rejected by the strict audit subject model. The real
[platform](../../infra/bicep/modules/eval/eval-platform.bicep#L290) instead creates seven persistent model
deployments. These source facts do not establish automatic teardown of any real per-run resource.

**Developer:** Connect a real resource adapter to the run controller, persist owned IDs before/after
provision operations, perform bounded What-If and policy checks before mutation, and create isolated
run-scoped resources only where authorised. Resolve the impossible assumption that RG-scoped Contributor
can create sibling RGs: choose a properly authorised lifecycle boundary without broadening permissions
implicitly. Lease pre-existing deployments with pinned versions and reference counting; never delete
shared platform resources. Align ownership tags, resource IDs, audit vocabulary and clock/deadline rules.
Reconcile expired nonterminal runs independently of the failed process and finish cleanup within 60
minutes after the recorded max duration. Dependencies: AUD-030-003, AUD-030-009, AUD-030-011, AUD-030-013.

**Tester:** Extend [test_phase5_6_modules.py](../../tests/unit/eval/test_phase5_6_modules.py#L60).
Positive: missing model creates and deletes only owned resources; lease reuse releases without deletion.
Negative/edge: What-If outside scope, second provision fails, cancellation during create, expired running
state, missing/malformed ownership tags, unknown creation time, concurrent lease users, failed delete,
audit validation error and exact timeout boundary. Assert actual adapter calls/IDs/order, no false
provisioned event, explicit orphan state and bounded repeated cleanup.

**Future validation:** Offline adapter/clock tests:
`pytest tests/unit/eval/test_phase5_6_modules.py tests/unit/eval/test_foundry_failures.py -q`.
Only after separate approval, run a tagged dev lifecycle/kill exercise and inspect its recorded inventory.
**Complete when:** success/failure/cancel/crash paths preserve data, remove owned resources and preserve
shared leases, with attributable lifecycle events rather than constructed deployment records alone.

### Job Dispatch, Storage Permissions and Private Connectivity Are Incomplete

- [ ] AUD-030-013 Wire deployable job roles, least privilege and private data access

**Priority:** High. **Affected originals:** T002, T006, T014, T015, T016, T017, T021,
T028, T029, T057, T067a, T071, T075, T082, T087, T092; FR-016, FR-018, FR-019, FR-021,
FR-022a, FR-027; SC-002, SC-003, SC-012.

**Expected/actual/impact:** All four [jobs](../../infra/bicep/modules/eval/eval-platform.bicep#L389)
use the [Docker entrypoint](../../apps/eval-runner/Dockerfile#L31) `ama_eval.runner`; `EVAL_JOB_ROLE` has
no reader/dispatcher. Scheduled jobs lack required run/dataset arguments; scheduler and audit-projection
implementations are absent. The runner is given `EVAL_BLOB_ACCOUNT` and Blob Reader, but trace writing
requires `EVAL_STORAGE_ACCOUNT`, `EVAL_TRACES_CONTAINER` and write permission. The alternative
[RBAC module](../../infra/bicep/modules/eval/eval-rbac.bicep#L51) is not invoked and assigns several roles
at RG scope instead of its named resource IDs; it does not create the stated Entra roles or ephemeral
Contributor grant. Staging/production disable public data access without VNet/private endpoint/DNS
wiring. Raw resource templates do not demonstrate the mandatory AVM discovery/approval process.

**Developer:** Give runner/reconciler/scheduler/projection jobs explicit entrypoints and required settings;
preserve job environment/resources when starting an execution. Scheduler must load the production baseline
configuration and submit a policy-checked scheduled run. Projection must implement AUD-030-011. Proposed
new modules, if needed: `apps/eval-runner/src/ama_eval/scheduler.py` and
`apps/eval-runner/src/ama_eval/audit_projection.py` (not existing evidence). Wire the actual resource-scoped
MI permissions, signing-key permissions and private network path; fail deployment/readiness on missing
configuration. Resolve Python 3.13 plan versus 3.12 image/CI explicitly. Keep anonymous flag dev-only;
retain an accurate environment value outside dev rather than removing it to satisfy T092's conflicting
wording. Dependencies: AUD-030-004, AUD-030-011, AUD-030-012. No live policy exceptions are authorised here.

**Tester:** Extend [test_run_llm_evaluation_script.py](../../tests/unit/eval/test_run_llm_evaluation_script.py#L182)
and [test_api_dev_integration.py](../../tests/unit/eval/test_api_dev_integration.py#L141). Check each job's
actual command/config contract and scoped permissions, not string presence alone. Fixtures: all three
environments, missing storage/write/sign settings, scheduler retry, projection restart, private DNS failure,
wrong role discriminator and build context missing a repository/package. Assert no job can report ready
while its work is a no-op or argument error.

**Future validation:** Offline pytest for those homes; later compile the three eval Bicep modules and
validate each environment with an approved identity and discovered governance constraints. Build/run a
smoke image only in that later phase. **Complete when:** every provisioned job can perform its assigned
work through its intended identity/network, with executable assertions and deployment evidence.

### Manual CLI and Model Configuration Can Misreport Success

- [ ] AUD-030-014 Align operator commands, model configuration and exit behavior

**Priority:** High. **Affected originals:** T019, T026, T046a, T058, T069, T077, T089,
T093, T094, T095; FR-013, FR-014, FR-020, FR-024, FR-026; SC-001, SC-008, SC-010.

**Expected/actual/impact:** [Model parameters](../../packages/eval-core/src/ama_eval_core/models.py#L356)
serialize `maxTokens`/`topP`/penalty names, but the
[client](../../apps/eval-runner/src/ama_eval/foundry_client.py#L116) accepts `max_tokens` and none of
those extra names; the orchestrator forwards them unchanged. `timeout_seconds` is not forwarded to the
SDK; actual raw responses are discarded. The [v1 registry](../../packages/eval-core/src/ama_eval_core/registries/models-v1.json#L1)
is not loaded; CLI and Bicep duplicate a different seven-model list. Appending registry JSON cannot
deploy/register a fourth model. The [runner adapter](../../apps/eval-runner/src/ama_eval/runner.py#L125)
resolves version using the first matching modelId, so two versions of one model invoke the first version
while their traces claim different versions. [CLI gate checking](../../scripts/run_llm_evaluation.py#L1284) reads an
absent field and treats it as an empty verdict list. `--stage all` stops on error before cleanup, archive
ignores subprocess failure, and existing-blob/409 paths do not prove matching content. The
[manual guide](../../docs/llm-evaluation/manual-evaluation-guide.md#L110) documents unsupported smoke,
runner, gate and validator commands, a nonexistent approval route and a 12-hour full mode.

**Developer:** Use a single validated configuration registry for model and judge deployments; translate
parameters explicitly, reject unsupported fields, pin/record effective version/endpoint parameters and
enforce transport deadlines. Keep inference adapters configurable without code changes. Bind CLI gate
status to the same strict decision as AUD-030-010, always enter safe cleanup after failures, and propagate
environment/auth/signing context to archive. Update existing operator docs to the approved contract and
supported flags; label bounded smoke versus full runs clearly. Preserve safe old-client compatibility;
never turn a missing field, missing file or failed subprocess into a success message.

**Tester:** Extend [test_foundry_failures.py](../../tests/unit/eval/test_foundry_failures.py#L125) and
[test_run_llm_evaluation_script.py](../../tests/unit/eval/test_run_llm_evaluation_script.py#L729).
Use real client-argument binding with fake transport: maxTokens/topP/penalties, unknown model/version,
deadline, 429/filter/empty/malformed responses, fourth JSON model, 409 mismatched bytes, alternate API URL,
signer denial and each stage failure. Assert exact effective args, nonzero failures, cleanup and correct
anonymous/header branching through publish/execute/archive, not only a mock `modelVerdicts` shape.

**Future validation:** `pytest tests/unit/eval/test_foundry_failures.py tests/unit/eval/test_run_llm_evaluation_script.py -q`
with all CLI transport/subprocess calls faked. After dependent fixes, a separately approved operator can
repeat the documented quickstart. **Complete when:** documentation and CLI use one contract, a registry-only
model addition is effective, and every printed success is backed by checked stage results.

### Dashboard Shape Drift and Missing Operator Views

- [ ] AUD-030-015 Deliver authenticated comparison, progress, dataset and trace views

**Priority:** Important. **Affected originals:** T005, T037, T038, T039, T040, T051,
T059, T068, T074, T084; FR-005, FR-010, FR-020, FR-022, FR-028; AS-1.1, AS-1.2, AS-1.3,
AS-2.3, AS-3.3, AS-5.1, AS-5.2; SC-001, SC-009, SC-012.

**Expected/actual/impact:** Replacement pages are [runs list](../../apps/web/src/app/eval/page.tsx#L15)
and [/eval/[runId]](../../apps/web/src/app/eval/[runId]/page.tsx#L27), not the planned directory. Both send
`x-eval-roles` rather than verified identity, catch fetch failures as empty/not-found, and have no live
progress/cancel controls. The detail page reads `winner.perMetric` and `generatedAt`; the actual model
emits `byMetric` and `createdAt`, causing an undefined-property access for nonempty metrics. It treats
arbitrary mean scales as percentages. The unused [typed client](../../apps/web/src/lib/api/eval.ts#L43)
expects an envelope for the bare run list and calls the nonexistent `/scorecards/{id}` route. Dataset,
gate and role-gated paged trace views and cost/lifecycle rendering were not found in the scoped UI search.

**Developer:** Reuse a single generated/validated API contract with server-verified session identity,
explicit authorization/not-found/loading/error states, correct per-metric scales/verdicts/winners,
model set and timestamps. Preserve links to the existing detail URL or add compatibility routing. Add
progress/cancel, cost/lifecycle, dataset/version/filter, gate diagnostics/override history and paged
Tier-2 traces with server-side rechecks and sensitivity controls. Do not expose raw content in SSR props
before authorization. Dependencies: AUD-030-003, AUD-030-004, AUD-030-005, AUD-030-008, AUD-030-010, AUD-030-011.

**Tester:** Use the existing [Playwright discovery root](../../apps/web/playwright.config.cts#L4),
not the undiscovered historical apps/web/e2e path. Proposed new test: `tests/e2e/eval-comparison.spec.ts`.
Feed actual API-shaped 0/1/many-model scorecards, tied/no winner, a Likert metric, missing baseline,
401/403/404/500, progressive events/cancel, graphics sentinel and narrow/mobile layout. Assert meaningful
error states, no undefined access, correct scales/identity/role blocking and zero Tier-1 sentinel exposure;
cover keyboard/focus/live announcements with WCAG 2.2 AA checks.

**Future validation:** After UI/API and test-discovery repair, run
`pnpm --filter @ama/web exec playwright test eval-comparison.spec.ts --project=chromium --project=mobile`.
Prerequisites: approved local-only API fakes, configured test servers/browsers; none started in this audit.
**Complete when:** operator journeys work through all expected states and an attributable accessibility
review confirms the tested routes, not merely that pages compile or exist.

### Regression Tests Are Narrow and Their CI Discovery Is Incomplete

- [ ] AUD-030-016 Make specification tests discoverable, isolated and behavior-discriminating

**Priority:** Important. **Affected originals:** T001, T002, T003, T004, T005, T008,
T013, T023, T024, T025, T040, T041, T042, T043, T053, T054, T061, T062, T070, T071,
T078, T083, T084, T090; every story's test-first/independent-delivery obligation.

**Expected/actual/impact:** Renamed tests exist and are credited, but
[general CI](../../.github/workflows/ci.yml#L141) runs contract/integration directories, not the eight
eval unit files or eval package tests; eval-specific workflows are manual-only. No equivalent contract
assertions were found for the documented eval API, evidence/leak sentinel, publication/PII flow, projection
or override. [Playwright](../../apps/web/playwright.config.cts#L4) discovers tests/e2e, not apps/web/e2e.
[API dependencies](../../apps/api/pyproject.toml#L10) omit ama-eval-core, and
[router registration](../../apps/api/app/api/router.py#L46) silently drops eval on any import failure.
Several tests mutate environment/sys.path at module import, bypass real dependency composition, and the
[CLI auth tests](../../tests/unit/eval/test_run_llm_evaluation_script.py#L729) write the shared `.eval-out/r-1`
path. These conditions can conceal missing production wiring and contaminate evidence.

**Developer:** Include all owned package/runner/API dependencies in the build and explicit PR test lanes;
make eval startup failure observable, not optional without a documented feature flag. Isolate unit tests
from environment, filesystem and cloud access with fixtures/tmp paths; separate fake outputs from retained
evaluation evidence. Reuse existing test homes; add only the missing contract/integration cases required
by the findings. Do not redefine a test as integration solely because it invokes a helper end-to-end.
Dependencies: implementation tasks above; historical TDD ordering cannot be retroactively proven.

**Tester:** Assert registered route/OpenAPI shapes, true API -> worker -> persistence -> reader composition,
metric coverage, sensitivity sentinel, audit/projection, leases and gates using fakes only at external
boundaries. Verify collect-only discovery in clean Linux/Windows environments, no network when credentials
are absent, no shared artifact writes, and failure when a required evaluator/route/job configuration is removed.
Do not call filenames, fake logs or broad `isinstance` assertions proof of acceptance.

**Future validation:** With intended packages installed in an isolated environment, first run
`pytest --collect-only packages/eval-core/tests packages/eval-dataset/tests tests/unit/eval -q`, then the
focused suites listed in each remediation. Confirm the added contract/e2e tests are in required CI jobs.
**Complete when:** discovery and discriminating assertions cover every specified behavior; CI run IDs,
counts and source SHA are retained separately under AUD-030-018.

### Observability Does Not Establish Redaction or End-to-End SLOs

- [ ] AUD-030-017 Instrument safe evaluation telemetry and define measurable SLOs

**Priority:** High. **Affected originals:** T082, T083, T084, T085, T086, T087, T088;
FR-001(i), FR-018, FR-021, FR-022, FR-023; SC-002, SC-008, SC-009, SC-011; plan performance goals.

**Expected/actual/impact:** [API-wide Azure Monitor setup](../../apps/api/app/main.py#L12) exists, but
the runner only initializes logging and no per-case/evaluator/provisioning spans or sentinel scrubber
were found. [Exceptions](../../apps/eval-runner/src/ama_eval/orchestrator.py#L103) and judge/provider errors
are logged verbatim without an eval-specific content filter. The
[latency rule](../../apps/eval-runner/src/ama_eval/evaluators/rule_based.py#L150) measures only model-call
latency, not per-sample wall time including judges. There is no eval SLO document/dashboard matching
the required API p95, queue/start, full/fast run budgets. This is a source-level exposure/measurement gap,
not a claim that sensitive text was observed in live telemetry.

**Developer:** Use the established telemetry stack with an allow-list of run/case/model/metric/judge/tier
IDs and numeric measures. Scrub provider exceptions and exporter payloads before logging; never export
raw inputs/outputs/rationales as attributes. Measure queue-to-start and total case/run latency, judge
calls, costs, partials, timeouts and orphan lag. Define versioned SLOs and dashboards/alerts over actual
emitted metrics. Proposed documents/artifacts: `docs/sre/eval-slos.md` and
`infra/observability/eval-dashboards.bicep`. Dependencies: AUD-030-002, AUD-030-003, AUD-030-009, AUD-030-013.

**Tester:** Extend existing Foundry-failure/orchestrator tests using an in-memory span/log exporter and
fake clock. Inject a unique synthetic sensitive sentinel into success, filter error, judge parse error,
SDK exception and cancellation. Assert zero occurrences in logs/exporter/summary, retained gated trace
content, complete ID linkage, and duration inclusive of judges/queueing. Check absent data does not make
an SLO green. Later accessibility and chaos exercises need separate evidence, not unit-test inference.

**Future validation:** `pytest tests/unit/eval/test_foundry_failures.py tests/unit/eval/test_orchestrator_e2e.py -q`
with deterministic exporters/clocks; later perform an approved full/fast workload measurement.
**Complete when:** telemetry is safely attributable and each SLO has an executable query, owned threshold
and representative recorded measurement rather than a configured timeout or mock latency value.

### Claimed Completion Is Not an Attributable Acceptance Record

- [ ] AUD-030-018 Capture independent acceptance, performance and approval evidence after remediation

**Priority:** High evidence gate; execution explicitly deferred. **Affected originals:** T008, T023,
T041, T046, T052, T060, T069, T076, T077, T081, T083, T084, T085, T086, T087, T088,
T089, T090, T095; all SC-001 through SC-012 and review/quickstart obligations.

**Expected/actual/impact:** All 98 source tasks are checked, but the
[quality checklist](checklists/requirements.md#L29) and approved specification status are authored
assertions. Local logs show dev CLI attempts, two publication 500s followed by a recorded 201, one empty
metric run marked succeeded, and archive attempts. Seven-model scorecards cover only 5 or 25 cases and
contain 42 failing aggregate metric cells each, with no costs/baselines/judges. The three archives omit
five evidence categories and signatures. No inspected record establishes a representative validation
week, full 5,000-case three-model run, human approval, independent 30-day replay, live-fire blocked PR,
24-hour cleanup exercise, WCAG audit, security/WAF sign-off or performance p95 at this HEAD.

**Developer/evidence owner:** After code/test repairs, create a run-linked evidence index identifying
source SHA, immutable dataset/metric/judge/model versions, effective config, invocation, timestamps,
provider request/token/latency records, exit/status, artifact hashes, test command/results and actual human
review identity/decision. Proposed mapping: `docs/compliance/eval-mapping.md`, generated from actual metric
and policy data, covering ISO/IEC 42001 clauses 6.1.4, 6.2, 8.3, 9.1, A.6, A.7; NIST Govern/Map/Measure/Manage
subcategories; APP 6/11. Retain failures and explicit unresolved items. Do not manufacture approval chains,
claim current HEAD attribution for historical local artifacts, or retrospectively recheck source tasks.

**Tester/reviewers:** First collect isolated suite results after AUD-030-016. Then authorised evaluation,
safety, governance, security, SRE and accessibility reviewers must exercise full/fast runs, different
model tiers, configuration-only model addition, rejected budgets, degraded candidate gate, override,
cancel/crash/quota/network/corrupt-trace faults, seven-year retention, and independent historical replay.
Compare negative cases as well as happy paths, across the representative week and 24-hour cleanup window;
record sample-level diagnostics privately. Repeat the dev anonymous flow and reject restricted content.

**Future validation:** After all prerequisites, explicit cloud/cost and human-review approval, and working
publication/provision/cleanup controls, use the repaired existing driver, for example
`python scripts/run_llm_evaluation.py --stage execute --env dev --max-cases 0 --models $ApprovedThreeModelRefs`.
`$ApprovedThreeModelRefs` must identify three approved, configured model/version pairs; this is not an
authorisation to execute now. Run each documented focused suite and the corrected quickstart, retaining
exact commands and results. **Complete when:** independent reviewers can verify all SCs and approvals from
attributable artifacts; source-only or unauthenticated results remain UNVERIFIED rather than passing.

## Original Task Coverage

Source: [complete task list](tasks.md#L42). Every original state is exactly `[X]`; none was modified.
IMPLEMENTED means the entire scoped authored artifact/behavior is supported statically, not that its
execution passed. PARTIAL/CONFLICT identify concrete source deficiencies; UNVERIFIED is used for
execution/review obligations. S-* boundaries above apply to each negative conclusion.

| Original Task | Source State | Status | Inspected Evidence and Limitation | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [X] | PARTIAL | [Package metadata](../../packages/eval-core/pyproject.toml#L5), models/README/tests exist; Python floor is 3.12, not a pinned 3.13 workspace; [pnpm workspace](../../pnpm-workspace.yaml#L1) does not register eval packages. | AUD-030-013, AUD-030-016 |
| T002 | [X] | PARTIAL | [Worker package](../../apps/eval-runner/pyproject.toml#L5) and [non-root Dockerfile](../../apps/eval-runner/Dockerfile#L2) exist, but image uses 3.12 and lacks a job-role dispatch contract. | AUD-030-013, AUD-030-016 |
| T003 | [X] | PARTIAL | [Package](../../packages/eval-dataset/pyproject.toml#L5) and [replacement layout](../../packages/eval-dataset/README.md#L5) exist; documented author/review workflow contradicts generator/publisher behavior. | AUD-030-006, AUD-030-007 |
| T004 | [X] | IMPLEMENTED | [Eval feature registration](../../apps/api/app/api/routes/eval/router.py#L16) and separate API/model/service/repository feature surfaces exist; subsequent wiring is assessed under T018/T022. | none |
| T005 | [X] | PARTIAL | [Typed client](../../apps/web/src/lib/api/eval.ts#L1) and feature pages replace the stub; its nominal contract types diverge from actual API/contract. | AUD-030-008, AUD-030-015 |
| T006 | [X] | IMPLEMENTED | [Platform](../../infra/bicep/modules/eval/eval-platform.bicep#L21), [deployment module](../../infra/bicep/modules/eval/foundry-deployments.bicep#L12), [RBAC](../../infra/bicep/modules/eval/eval-rbac.bicep#L6) and three parameter files are authored beyond skeleton stage; no build implied. | none |
| T007 | [X] | IMPLEMENTED | [Policy](../../infra/policy/eval/provisioning-policy.dev.yaml#L10) and [promotion-gate definition](../../infra/policy/eval/promotion-gates/eval-gate.yaml#L8) contain the requested scaffold fields. Their actual consumers are assessed separately. | none |
| T008 | [X] | PARTIAL | [Ruff scope](../../ruff.toml#L1) covers apps/packages/tests; [root pytest configuration](../../pyproject.toml#L42) exists, but [CI](../../.github/workflows/ci.yml#L141) omits principal eval suites. Collection/lint execution not attributable. | AUD-030-016, AUD-030-018 |
| T009 | [X] | PARTIAL | All eight [case](../../packages/eval-core/src/ama_eval_core/schemas/case.schema.json#L7)/manifest/metric/judge/run/scorecard/audit/policy schemas exist; cross-field rules, nullability and data-model fields do not fully align. | AUD-030-002, AUD-030-008 |
| T010 | [X] | PARTIAL | [Models](../../packages/eval-core/src/ama_eval_core/models.py#L203) enforce selected case invariants, but not publication/reference immutability, active judge binding, snapshots or partial-run invariants. | AUD-030-002, AUD-030-008 |
| T011 | [X] | PARTIAL | [Enum/protocol/memory emitter](../../packages/eval-core/src/ama_eval_core/audit.py#L22) exists; vocabulary differs from contract and real lifecycle callers use invalid subject type deployment. | AUD-030-008, AUD-030-011, AUD-030-012 |
| T012 | [X] | PARTIAL | [Pure policy helper](../../packages/eval-core/src/ama_eval_core/policy.py#L90) checks supplied values, but optional placement fields and run-count concurrency leave required limits unproven. | AUD-030-009 |
| T013 | [X] | PARTIAL | Renamed [model tests](../../packages/eval-core/tests/test_models.py#L62) round-trip case/manifest only; [policy tests](../../packages/eval-core/tests/test_policy.py#L35) cover individual checks, not exhaustive entity/policy/invariant matrices. | AUD-030-008, AUD-030-009, AUD-030-016 |
| T014 | [X] | PARTIAL | [Platform IaC](../../infra/bicep/modules/eval/eval-platform.bicep#L85) declares real data/jobs/telemetry resources, but retention, networking, RBAC, dispatch and AVM/process obligations remain incomplete; no compile claim. | AUD-030-011, AUD-030-013, AUD-030-018 |
| T015 | [X] | PARTIAL | [Deployment module](../../infra/bicep/modules/eval/foundry-deployments.bicep#L46) pins version/tags but fixes OpenAI format, only echoes region and is not called by the provisioner. | AUD-030-012, AUD-030-014 |
| T016 | [X] | PARTIAL | [RBAC module](../../infra/bicep/modules/eval/eval-rbac.bicep#L39) exists but is disconnected; grants RG-wide roles, omits Entra app roles and actual ephemeral Contributor assignment. | AUD-030-004, AUD-030-012, AUD-030-013 |
| T017 | [X] | PARTIAL | [Dev](../../infra/bicep/parameters/eval-platform.dev.json#L4), [staging](../../infra/bicep/parameters/eval-platform.staging.json#L4), [production](../../infra/bicep/parameters/eval-platform.production.json#L4) author Disabled/Unlocked/Unlocked initial choices; required lock follow-through is undocumented/unverified. | AUD-030-011, AUD-030-013 |
| T018 | [X] | PARTIAL | Consolidated [repositories](../../apps/api/app/repositories/eval/repositories.py#L110) implement Cosmos/memory persistence; per-instance memory stores are not shared across routes/workers, mutators do not emit audit, and upserts permit replacement. | AUD-030-003, AUD-030-006, AUD-030-011, AUD-030-016 |
| T019 | [X] | PARTIAL | [Inference wrapper](../../apps/eval-runner/src/ama_eval/foundry_client.py#L59) uses managed credentials and configuration errors, but not the stipulated Projects/judge contract; params, version attribution, errors and timeout are incomplete. | AUD-030-002, AUD-030-014 |
| T020 | [X] | CONFLICT | [Role guard](../../apps/api/app/middleware/eval_role_guard.py#L32) trusts unverified claims, differs from contract roles and does not emit per-access audit itself; endpoint-specific coverage is incomplete. | AUD-030-004, AUD-030-005 |
| T021 | [X] | PARTIAL | [Builder](../../apps/eval-runner/src/ama_eval/evidence.py#L43) hashes tar members; timestamps break determinism, signing is optional/fail-open and no persisted complete signed chain is produced. | AUD-030-011 |
| T022 | [X] | IMPLEMENTED | [Health and registration](../../apps/api/app/api/routes/eval/router.py#L19) plus [API inclusion](../../apps/api/app/api/router.py#L132) exist. Optional-import disappearance is separately tracked. | AUD-030-016 |
| T023 | [X] | UNVERIFIED | [Foundation assertions](../../tests/unit/eval/test_phase2_foundations.py#L74) exist; no attributable requested pytest/ruff results or foundational review at this HEAD. | AUD-030-016, AUD-030-018 |
| T024 | [X] | MISSING | S-TEST found no run/scorecard OpenAPI contract assertions or retrieval-schema contract gate; [run models](../../apps/api/app/api/routes/eval/runs.py#L35) contradict the contract. | AUD-030-008, AUD-030-016 |
| T025 | [X] | PARTIAL | [Renamed orchestrator test](../../tests/unit/eval/test_orchestrator_e2e.py#L91) checks five cases/two fake models/rules/winner/ten in-memory traces, not queued API -> worker -> durable scorecard lifecycle. | AUD-030-001, AUD-030-003, AUD-030-016 |
| T026 | [X] | PARTIAL | [Generator size option](../../packages/eval-dataset/src/ama_eval_dataset/cli.py#L90) and five-case test exist; no committed/regenerable specified 50-case smoke fixture after S-DATA/S-TEST search. | AUD-030-007 |
| T027 | [X] | CONFLICT | [Inline run models](../../apps/api/app/api/routes/eval/runs.py#L35) replace planned files but differ in request refs, summary fields/status and contract validation. | AUD-030-008 |
| T028 | [X] | PARTIAL | [Queue route](../../apps/api/app/api/routes/eval/runs.py#L69) persists and invokes a job; no authoritative dataset/metric/policy resolution, change idempotency, polling or durable cancel lifecycle. | AUD-030-003, AUD-030-008, AUD-030-009, AUD-030-010 |
| T029 | [X] | PARTIAL | [Worker](../../apps/eval-runner/src/ama_eval/runner.py#L73) loads run/cases and saves a scorecard; incomplete evaluators, trace write failures, lifecycle exits, snapshots and teardown remain. | AUD-030-001, AUD-030-002, AUD-030-003, AUD-030-008, AUD-030-012 |
| T030 | [X] | PARTIAL | [Rule evaluators](../../apps/eval-runner/src/ama_eval/evaluators/rule_based.py#L40) implement token/refusal/authority/tone/latency checks, not exact factuality, structured shape, escalation correctness or required score attribution. | AUD-030-002 |
| T031 | [X] | PARTIAL | [Judge factory](../../apps/eval-runner/src/ama_eval/evaluators/judge.py#L45) exists but is not registered by production; no Microsoft built-in suite/custom complete bindings or recorded judge versions. | AUD-030-002 |
| T031a | [X] | PARTIAL | [Retrieval helper](../../apps/eval-runner/src/ama_eval/evaluators/retrieval.py#L16) and scope filter exist; lexical overlap/citation heuristics are not recall@k/precision@k/nDCG or semantic groundedness. | AUD-030-002 |
| T032 | [X] | MISSING | [Unused sampling field](../../apps/eval-runner/src/ama_eval/orchestrator.py#L46) and [empty disagreements](../../apps/eval-runner/src/ama_eval/scorecard.py#L80) are not a sampled independent judge executor; S-RUN searched. | AUD-030-002 |
| T033 | [X] | PARTIAL | [Classifier](../../apps/eval-runner/src/ama_eval/orchestrator.py#L63) distinguishes text/empty/refusal but ignores expected action and disagrees with filtered-empty/refusal scoring; no canonical positive/negative matrix. | AUD-030-002, AUD-030-003 |
| T034 | [X] | PARTIAL | [Scorecard builder](../../apps/eval-runner/src/ama_eval/scorecard.py#L17) provides means/distribution/winners; no wired baseline deltas, metric-policy verdicts, complete denominator, persisted HTML or sample diagnostics. | AUD-030-002, AUD-030-008, AUD-030-010, AUD-030-011 |
| T035 | [X] | PARTIAL | [Run routes](../../apps/api/app/api/routes/eval/runs.py#L160) supply list/detail/cancel; SSE and dataset/since/changeRef filters are absent, status_filter differs and cancel does not reach execution. | AUD-030-003, AUD-030-008 |
| T036 | [X] | PARTIAL | [Nested summary endpoint](../../apps/api/app/api/routes/eval/scorecards.py#L17) returns aggregate data; it is not the contract path/role boundary and does not enforce anonymous content scope. | AUD-030-004, AUD-030-005, AUD-030-008 |
| T037 | [X] | CONFLICT | [Typed client](../../apps/web/src/lib/api/eval.ts#L43) expects wrong list envelope/scorecard route and has no identity propagation; actual pages bypass it. | AUD-030-008, AUD-030-015 |
| T038 | [X] | PARTIAL | [List page](../../apps/web/src/app/eval/page.tsx#L47) has table/status/detail links, but omits model set/verdict and masks authentication/fetch failure as empty data. | AUD-030-015 |
| T039 | [X] | CONFLICT | [Renamed detail page](../../apps/web/src/app/eval/[runId]/page.tsx#L94) dereferences wrong winner property; no live progress or complete verdict/baseline presentation. | AUD-030-003, AUD-030-015 |
| T040 | [X] | PARTIAL | [Interface smoke](../../tests/e2e/interface-coverage.spec.ts#L623) and [page object](../../tests/e2e/web-coverage/_support/pages/eval.po.ts#L6) exist, but do not assert comparison/SSE/trace roles; recorded route testcase is skipped. | AUD-030-015, AUD-030-016 |
| T041 | [X] | UNVERIFIED | Authored [fake-client test](../../tests/unit/eval/test_orchestrator_e2e.py#L91) and UI smoke are not requested test execution or orchestrator/evaluator review evidence. | AUD-030-016, AUD-030-018 |
| T042 | [X] | PARTIAL | [Generator tests](../../packages/eval-dataset/tests/test_generator.py#L71) cover generated labels/Pydantic; [CLI validate](../../packages/eval-dataset/src/ama_eval_dataset/cli.py#L40) does not run JSON Schema/Presidio against the committed corpus. | AUD-030-006, AUD-030-007, AUD-030-008, AUD-030-016 |
| T043 | [X] | PARTIAL | [API dataset tests](../../tests/unit/eval/test_api_dev_integration.py#L65) check memory registration and hash conflict, not generation -> reviewed content -> immutable upload -> version retrieval. | AUD-030-006, AUD-030-016 |
| T044 | [X] | CONFLICT | [Replacement generator](../../packages/eval-dataset/src/ama_eval_dataset/generator.py#L111) is deterministic template sampling with approved output; D8 requires frontier generation and drafts. | AUD-030-006, AUD-030-007 |
| T045 | [X] | PARTIAL | [Distribution constants/helper](../../packages/eval-dataset/src/ama_eval_dataset/distribution.py#L7) replace JSON/CLI filenames but compute counts without enforcing a safety-owned minimum hazard share. | AUD-030-007 |
| T046 | [X] | PARTIAL | [5,000-case artifact](../../packages/eval-dataset/data/dataset-disaster-core-1.0.0/manifest.json#L6) exists; schema/language/rubric/approval conflicts remain and specified generation/validation execution is not attributable. | AUD-030-006, AUD-030-007, AUD-030-018 |
| T046a | [X] | PARTIAL | [Three-model/two-judge JSON](../../packages/eval-core/src/ama_eval_core/registries/models-v1.json#L1) is authored; no production loader, AU preference, effective deployment/version binding or JSON-only fourth-model proof. | AUD-030-002, AUD-030-014 |
| T047 | [X] | CONFLICT | [Publish route input](../../apps/api/app/api/routes/eval/datasets.py#L30) is a complete manifest, not the expected count/distribution request and generated response contract. | AUD-030-006, AUD-030-008 |
| T048 | [X] | PARTIAL | [Inline publish behavior](../../apps/api/app/api/routes/eval/datasets.py#L34) detects one sequential hash conflict; no safety approval, canonical upload, minimum share or atomic immutability. | AUD-030-006 |
| T049 | [X] | PARTIAL | [Dataset routes](../../apps/api/app/api/routes/eval/datasets.py#L24) include publish/version/cases but no family list; full case reads use Tier-1 and return repository cases only. | AUD-030-005, AUD-030-006, AUD-030-008 |
| T050 | [X] | PARTIAL | [Renamed workflow](../../.github/workflows/eval-publish-dataset.yml#L3) validates and uploads GitHub artifacts; publication is commented out, merge trigger/owners/real-case review absent. Credential migration is explicit, not an approval bypass. | AUD-030-006, AUD-030-016 |
| T051 | [X] | MISSING | S-UI contains only [list](../../apps/web/src/app/eval/page.tsx#L47) and [run detail](../../apps/web/src/app/eval/[runId]/page.tsx#L48); no dataset-family/version browser. | AUD-030-015 |
| T052 | [X] | UNVERIFIED | [publish3.log](../../.eval-out/publish3.log#L34) records 201 after two 500s; this does not establish approved 5,000-case immutable publication, requested tests or compliance review at HEAD. | AUD-030-006, AUD-030-018 |
| T053 | [X] | PARTIAL | [Provision tests](../../tests/unit/eval/test_phase5_6_modules.py#L60) assert records and delete token, not actual creation, cost-first rejection, tags or success/failure/cancel lifecycle. | AUD-030-003, AUD-030-009, AUD-030-012, AUD-030-016 |
| T054 | [X] | PARTIAL | [Reconciler test](../../tests/unit/eval/test_phase5_6_modules.py#L97) cleans a fake terminal run; no expired nonterminal crash, recorded deadline, full audit or bounded cleanup assertion. | AUD-030-012, AUD-030-016 |
| T055 | [X] | PARTIAL | [Provision helper](../../apps/eval-runner/src/ama_eval/provisioner.py#L46) constructs records only; no RG/What-If/create/lease operations despite the callable adapter. | AUD-030-012 |
| T056 | [X] | MISSING | [Worker completion](../../apps/eval-runner/src/ama_eval/runner.py#L150) has no unconditional finally/deprovision/orphan-exit path; manual CLI cleanup is a later stage, not equivalent. | AUD-030-003, AUD-030-012 |
| T057 | [X] | PARTIAL | [Pure reconciler](../../apps/eval-runner/src/ama_eval/reconciler.py#L35) exists, but tag/expiry/terminal logic and no CLI/job dispatch miss the required crashed-run cleanup. | AUD-030-012, AUD-030-013 |
| T058 | [X] | PARTIAL | [Cost helper](../../apps/eval-runner/src/ama_eval/cost.py#L31) estimates limited model tokens only, is uncalled by the runner, prices unknown models at zero and does not reconcile actuals. | AUD-030-009 |
| T059 | [X] | MISSING | [Detail page](../../apps/web/src/app/eval/[runId]/page.tsx#L67) renders metrics and instructions, not cost/lifecycle/resources/timestamps/terminal-state blocks. | AUD-030-009, AUD-030-015 |
| T060 | [X] | UNVERIFIED | [Platform provision logs](../../.eval-out/provision2.log#L1) are not run-owned resource creation/deletion or a 24-hour zero-orphan record; helper tests are fake. | AUD-030-012, AUD-030-018 |
| T061 | [X] | MISSING | S-API/S-TEST found no gate API/idempotency/override contract assertions; [unit gate tests](../../tests/unit/eval/test_phase5_6_modules.py#L142) call only the pure helper. | AUD-030-010, AUD-030-016 |
| T062 | [X] | PARTIAL | [Gate tests](../../tests/unit/eval/test_phase5_6_modules.py#L186) compare fabricated scalar maps; no changed prompt, actual baseline shape, sample diagnostic or override audit. | AUD-030-010, AUD-030-016 |
| T063 | [X] | PARTIAL | [Baseline repository](../../apps/api/app/repositories/eval/repositories.py#L307) and [GET route](../../apps/api/app/api/routes/eval/metrics.py#L23) exist; designation, immutable supersession audit and runner consumption do not. | AUD-030-008, AUD-030-010, AUD-030-011 |
| T064 | [X] | PARTIAL | [Gate helper](../../apps/eval-runner/src/ama_eval/gate.py#L39) has threshold/delta checks but skips absent metrics, expects a different baseline and lacks diagnostics/idempotent API wiring. | AUD-030-010 |
| T065 | [X] | MISSING | [Registered routes](../../apps/api/app/api/routes/eval/router.py#L40) have no gate/check/override; policy and enum strings are not governance-authorised mutation/notification behavior. | AUD-030-004, AUD-030-010, AUD-030-011 |
| T066 | [X] | PARTIAL | [Manual replacement](../../.github/workflows/eval-pr-gate.yml#L3) triggers a job but not a persisted candidate evaluation/gate; skipped/config/timeouts can pass and no required PR check is configured in source. | AUD-030-010, AUD-030-016 |
| T067 | [X] | SUPERSEDED | [Explicit 029 removal](../../.github/CODEOWNERS#L28) retires the original integration target; [current CD](../../.github/workflows/cd.yml#L18) has no eval gate. This does not supersede FR-024; the orphan policy still requires resolution. | AUD-030-010, AUD-030-018 |
| T067a | [X] | PARTIAL | [Scheduler cron declaration](../../infra/bicep/modules/eval/eval-platform.bicep#L389) exists; no job-role dispatcher, baseline-resolving scheduler or policy-checked scheduled POST. | AUD-030-009, AUD-030-013 |
| T068 | [X] | MISSING | S-UI finds no change-scoped gate view; [typed client](../../apps/web/src/lib/api/eval.ts#L43) sends a changeRef filter the API does not implement. | AUD-030-010, AUD-030-015 |
| T069 | [X] | UNVERIFIED | [Manual workflow](../../.github/workflows/eval-pr-gate.yml#L3) cannot establish the specified first-attempt safety-degrading PR block; no attributable live-fire PR record inspected. | AUD-030-010, AUD-030-018 |
| T070 | [X] | PARTIAL | [Evidence smoke test](../../tests/unit/eval/test_phase2_foundations.py#L126) checks manifest filename/hash prefix only, not signatures, Tier-2 export or Tier-1 graphic-sentinel absence. | AUD-030-005, AUD-030-011, AUD-030-016 |
| T071 | [X] | MISSING | S-TEST/S-RUN find no daily projection test/implementation; the [cron declaration](../../infra/bicep/modules/eval/eval-platform.bicep#L393) cannot assert delivery within 24 hours. | AUD-030-011, AUD-030-013, AUD-030-016 |
| T072 | [X] | MISSING | [Scorecard router](../../apps/api/app/api/routes/eval/scorecards.py#L17) has summary/winners only; [evidence CLI](../../apps/eval-runner/src/ama_eval/evidence.py#L173) is not the tiered JSON/HTML/bundle export endpoint. | AUD-030-005, AUD-030-011 |
| T073 | [X] | PARTIAL | [Trace route](../../apps/api/app/api/routes/eval/traces.py#L20) reads stored data and audits a case ID, but lacks model selection, paging, contract path and full anonymous access metadata. | AUD-030-001, AUD-030-005, AUD-030-011 |
| T074 | [X] | MISSING | [Detail page](../../apps/web/src/app/eval/[runId]/page.tsx#L114) gives textual trace instructions, not a server-gated paged trace browser; S-UI searched. | AUD-030-005, AUD-030-015 |
| T075 | [X] | PARTIAL | [Daily job declaration](../../infra/bicep/modules/eval/eval-platform.bicep#L393) exists, but no projection dispatch, watermark or immutable archive writer. | AUD-030-011, AUD-030-013 |
| T076 | [X] | MISSING | S-EVIDENCE finds no eval mapping generated from live metric/policy definitions. [RAI register](../../docs/governance-hub/rai-register/responsible-ai-register.md#L18) is an authored broader posture, not the required clause/subcategory/APP evidence mapping or sign-off. | AUD-030-011, AUD-030-018 |
| T077 | [X] | UNVERIFIED | [Archive retry log](../../.eval-out/archive2.log#L11) and same-day incomplete archives do not establish a 30-day-old independently verified signed replay or requested test execution. | AUD-030-011, AUD-030-018 |
| T078 | [X] | PARTIAL | [Sanitiser unit tests](../../tests/unit/eval/test_sanitise.py#L18) assert regex replacements/tag/hash, not a rejected-PII -> reviewed case -> published new version flow. | AUD-030-006, AUD-030-016 |
| T079 | [X] | PARTIAL | [Replacement sanitise helper](../../apps/eval-runner/src/ama_eval/sanitise.py#L59) redacts patterns, but does not run Presidio, construct a provenance-valid candidate or produce the specified log entries. | AUD-030-006 |
| T080 | [X] | MISSING | [Active workflow](../../.github/workflows/eval-publish-dataset.yml#L43) and [CODEOWNERS](../../.github/CODEOWNERS#L16) do not enforce second Presidio pass, independent dual approvals or log preservation. | AUD-030-006 |
| T081 | [X] | UNVERIFIED | [Sanitiser assertions](../../tests/unit/eval/test_sanitise.py#L18) and synthetic-only corpus provide no approved real-case de-identification-chain review or execution record. | AUD-030-006, AUD-030-018 |
| T082 | [X] | MISSING | [Generic telemetry resources](../../infra/bicep/modules/eval/eval-platform.bicep#L235) are not eval API/queue/full-run SLO docs/dashboards; no matching scoped artifact found. | AUD-030-017 |
| T083 | [X] | PARTIAL | [API Monitor setup](../../apps/api/app/main.py#L12) exists; no required per-case/evaluator/provision span attributes, content scrubber test or compliance sign-off. | AUD-030-005, AUD-030-017, AUD-030-018 |
| T084 | [X] | UNVERIFIED | [Heading/landmark smoke](../../tests/e2e/interface-coverage.spec.ts#L623) and [skipped recorded test](../../tests/e2e/web-coverage/_artifacts/junit/web-coverage.xml#L143) are not a WCAG 2.2 AA audit of eval journeys. | AUD-030-015, AUD-030-018 |
| T085 | [X] | UNVERIFIED | [Fake cleanup test](../../tests/unit/eval/test_phase5_6_modules.py#L97) is not an executed kill/quota/corrupt-blob/Cosmos-partition chaos exercise. | AUD-030-003, AUD-030-012, AUD-030-018 |
| T086 | [X] | UNVERIFIED | [Plan gate assertions](plan.md#L23) and [risk treatments](../../docs/risk-register/RISK-NEW-004.md#L9) do not establish a security review or enforced model-gateway minimisation; source gaps remain. | AUD-030-004, AUD-030-005, AUD-030-013, AUD-030-017, AUD-030-018 |
| T087 | [X] | UNVERIFIED | [Raw platform templates](../../infra/bicep/modules/eval/eval-platform.bicep#L85) are inspectable; no attributable five-pillar WAF review/closed findings were found in S-EVIDENCE. | AUD-030-013, AUD-030-018 |
| T088 | [X] | UNVERIFIED | [25-case scorecard](../../.eval-out/01FB3PRZY147VMN6K0HKN3G1TT/scorecard.json#L1) cannot establish full/fast run budgets or per-sample p95 including judges. | AUD-030-009, AUD-030-017, AUD-030-018 |
| T089 | [X] | UNVERIFIED | [Quickstart](quickstart.md#L185) remains authored procedure; logs do not show all done bullets or a registry-only fourth-model run, and multiple commands/contracts drift. | AUD-030-014, AUD-030-018 |
| T090 | [X] | UNVERIFIED | [Tasks closure instruction](tasks.md#L429) has no accompanying local analysis report; current contract/language/retention/gate conflicts remain unresolved. | AUD-030-008, AUD-030-018 |
| T091 | [X] | PARTIAL | [Anonymous tests](../../tests/unit/eval/test_eval_role_guard_anonymous.py#L49) cover dev/nondev/flag/bearer branches, but replace sensitivity rejection with a different-dataset check; same-name real/labelled content and full audit/startup rules are absent. | AUD-030-004, AUD-030-005 |
| T092 | [X] | PARTIAL | [Conditional anonymous flag](../../infra/bicep/modules/eval/eval-platform.bicep#L551) is authored. ENVIRONMENT remains present outside dev, contrary to the task's literal both-absent wording; no current build/ARM validation record. | AUD-030-004, AUD-030-013, AUD-030-018 |
| T093 | [X] | PARTIAL | [Driver probe/header branches](../../scripts/run_llm_evaluation.py#L974) and [tests](../../tests/unit/eval/test_run_llm_evaluation_script.py#L622) cover execute; archive has an independent unpropagated environment/token flow and lacks equivalent tests. | AUD-030-005, AUD-030-011, AUD-030-014 |
| T094 | [X] | PARTIAL | [Quickstart amendment](quickstart.md#L195) and [guide](../../docs/llm-evaluation/manual-evaluation-guide.md#L171) document flags and nondev distinction, but claim stronger access/approval/archive behavior than implemented and retain unsupported commands. | AUD-030-005, AUD-030-014 |
| T095 | [X] | UNVERIFIED | [Anonymous execute log](../../.eval-out/execute.log#L9) proves only a recorded branch narrative; provision logs include an audience parameter, and no full nonempty scorecard, audit environment excerpt and same-dataset restricted-label rejection are attributable. | AUD-030-005, AUD-030-014, AUD-030-018 |

## Requirements and Success Criteria

### Functional Requirement Coverage

Every source FR is represented individually. Status concerns inspected implementation; any actual
execution, approval or deployment outcome required by the row remains UNVERIFIED as stated in SC coverage.

| Requirement | Status | Source and Inspected Implementation Evidence | Follow-up |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | [All nine families required](spec.md#L130); [default registry](../../apps/eval-runner/src/ama_eval/evaluators/__init__.py#L1), rules/retrieval/injection implement only deterministic approximations. Family detail follows. | AUD-030-002, AUD-030-009, AUD-030-017 |
| FR-002 | PARTIAL | [Versioned written definitions](spec.md#L131); [metric model](../../packages/eval-core/src/ama_eval_core/models.py#L317) has thresholds/tier but lacks written definition and immutable active-at-start bindings; no published metric definition inventory is loaded. | AUD-030-002, AUD-030-008 |
| FR-003 | MISSING | [Per-score judge identity/version](spec.md#L132); [EvalResult](../../apps/eval-runner/src/ama_eval/evaluators/base.py#L36) and [trace mapping](../../apps/eval-runner/src/ama_eval/orchestrator.py#L181) never persist required judge/version attribution. Optional summary fields are unpopulated. | AUD-030-002, AUD-030-011 |
| FR-003a | PARTIAL | [Hybrid primary/secondary strategy](spec.md#L133); [judge registration function](../../apps/eval-runner/src/ama_eval/evaluators/judge.py#L95) is not called by the worker; no secondary executor or disagreement sampling in S-RUN. | AUD-030-002 |
| FR-003b | PARTIAL | [Tier proportions and per-metric sampling](spec.md#L134); [rate field](../../packages/eval-core/src/ama_eval_core/models.py#L326) and [unused context default](../../apps/eval-runner/src/ama_eval/orchestrator.py#L46) do not record per-run percentages/selection. | AUD-030-002, AUD-030-008 |
| FR-004 | PARTIAL | [Per-sample and aggregate metrics](spec.md#L135); [builder](../../apps/eval-runner/src/ama_eval/scorecard.py#L17) computes means/pass-rate/min/max/winners, but exceptions shrink denominators, baseline is unbound, traces overwrite and diagnostics are empty. | AUD-030-001, AUD-030-002, AUD-030-003, AUD-030-010 |
| FR-005 | PARTIAL | [Human/machine exports each run](spec.md#L136); [JSON endpoint](../../apps/api/app/api/routes/eval/scorecards.py#L17) exists, but contract exports/HTML are absent and dashboard winner access is incompatible. | AUD-030-011, AUD-030-015 |
| FR-006 | PARTIAL | [Curated thirteen-hazard dataset](spec.md#L140); [committed corpus](../../packages/eval-dataset/data/dataset-disaster-core-1.0.0/manifest.json#L7) spans all hazards, but action/rubric coherence, evacuation-refusal/minor sensitivity and actual SME curation are not established. | AUD-030-007, AUD-030-018 |
| FR-007 | PARTIAL | [Approximately 5,000 approved and growth](spec.md#L141); 5,000 unique IDs and configurable size exist, but [generator approval](../../packages/eval-dataset/src/ama_eval_dataset/generator.py#L147) is authored without safety-review decision. 10k+ execution not performed. | AUD-030-006, AUD-030-007 |
| FR-008 | CONFLICT | [Fields, BCP-47 and English-only v1](spec.md#L142); [model](../../packages/eval-core/src/ama_eval_core/models.py#L203) contains many fields, but [manifest languages](../../packages/eval-dataset/data/dataset-disaster-core-1.0.0/manifest.json#L138) include en-NZ/vi/zh/ar and all case approval chains lack safety approval. | AUD-030-006, AUD-030-007, AUD-030-008 |
| FR-009 | PARTIAL | [Immutable versioned datasets](spec.md#L143); [route conflict check](../../apps/api/app/api/routes/eval/datasets.py#L40) and no-overwrite CLI exist, but [upserts](../../apps/api/app/repositories/eval/repositories.py#L140), unchecked remote hashes and unverified storage locking break authoritative immutability. | AUD-030-006, AUD-030-008, AUD-030-011 |
| FR-010 | PARTIAL | [Five-dimension filtering/stratification](spec.md#L144); [subset model](../../packages/eval-core/src/ama_eval_core/models.py#L378) exists, but [enqueue](../../apps/api/app/api/routes/eval/runs.py#L117) drops it and runner only prefix-slices maxCases. | AUD-030-007, AUD-030-008 |
| FR-011 | MISSING | [Safety reviewer before publication](spec.md#L145); [route](../../apps/api/app/api/routes/eval/datasets.py#L32) requires operator only, and [workflow](../../.github/workflows/eval-publish-dataset.yml#L3)/CODEOWNERS do not enforce independent review. | AUD-030-006 |
| FR-012 | PARTIAL | [Labelled and access-controlled graphic data/exports](spec.md#L146); [case invariants](../../packages/eval-core/src/ama_eval_core/models.py#L262) label two graphic hazards, but viewer/anonymous access and trace/export sensitivity marking are incomplete. | AUD-030-005, AUD-030-007, AUD-030-011 |
| FR-013 | PARTIAL | [Three Foundry tiers/config-only extensibility](spec.md#L150); [registry](../../packages/eval-core/src/ama_eval_core/registries/models-v1.json#L1) and inference adapter exist, but current Bicep/CLI lists are hard-coded separately and the registry is not loaded. Catalog availability/model execution unverified. | AUD-030-014, AUD-030-018 |
| FR-014 | PARTIAL | [Exact model/config/time window](spec.md#L151); [run model](../../packages/eval-core/src/ama_eval_core/models.py#L405) makes placement/params optional, runner resolves first matching model version, and actual endpoint/config/start time snapshots are incomplete. | AUD-030-008, AUD-030-014 |
| FR-015 | PARTIAL | [Same dataset/multi-model comparison](spec.md#L152); [model loop](../../apps/eval-runner/src/ama_eval/orchestrator.py#L91) and fake two-model assertion exist, but pinned subsets/metrics, parameter attribution and durable comparison traces are incomplete. | AUD-030-001, AUD-030-002, AUD-030-008, AUD-030-014 |
| FR-016 | PARTIAL | [On-demand run-scoped resources](spec.md#L156); [job start](../../apps/api/app/services/eval_job_trigger.py#L40) works through an adapter, but provision helper does not create models and platform deploys persistent resources. | AUD-030-012, AUD-030-013 |
| FR-017 | MISSING | [Unconditional transient cleanup](spec.md#L157); [runner terminal path](../../apps/eval-runner/src/ama_eval/runner.py#L150) has no finally/deprovision and manual driver can exit before cleanup. | AUD-030-003, AUD-030-012, AUD-030-014 |
| FR-018 | PARTIAL | [Regions/SKUs/concurrency/cost/duration, full <=8h and PR <=30m](spec.md#L158); [policy helper](../../packages/eval-core/src/ama_eval_core/policy.py#L90) is real but estimates/placement/concurrency are bypassable and end-to-end deadline/fast stratification are not enforced. | AUD-030-003, AUD-030-009, AUD-030-013 |
| FR-019 | PARTIAL | [Reconcile within 60m after max duration](spec.md#L159); [helper](../../apps/eval-runner/src/ama_eval/reconciler.py#L35) requires terminal run and wrong tag vocabulary; no scheduled dispatcher. | AUD-030-012, AUD-030-013 |
| FR-020 | PARTIAL | [Run cost/report](spec.md#L160); [cost helper](../../apps/eval-runner/src/ama_eval/cost.py#L31) is not connected to queue/runner/report and stored scorecards omit costs. | AUD-030-009, AUD-030-015 |
| FR-021 | PARTIAL | [Immutable seven-year audit/control mapping](spec.md#L164); [append-only Cosmos writer](../../apps/api/app/repositories/eval/repositories.py#L392) is positive evidence, but mutator coverage, projection, locked retention and complete evidence/signatures are absent. | AUD-030-011, AUD-030-013, AUD-030-018 |
| FR-022 | CONFLICT | [Tier-1 staff/Tier-2 restricted/access logging](spec.md#L165); [case route](../../apps/api/app/api/routes/eval/datasets.py#L71) returns sensitive bodies to viewers and [guard](../../apps/api/app/middleware/eval_role_guard.py#L57) does not verify identities. | AUD-030-004, AUD-030-005, AUD-030-011 |
| FR-022a | PARTIAL | [Dev-only anonymous exception a/b/c](spec.md#L166); [dual-flag branch](../../apps/api/app/middleware/eval_role_guard.py#L90) and [conditional IaC](../../infra/bicep/modules/eval/eval-platform.bicep#L551) exist, but no content eligibility/full audit tagging/startup refusal outside dev. | AUD-030-004, AUD-030-005, AUD-030-013, AUD-030-014 |
| FR-023 | PARTIAL | [No unredacted real PII/APP6/11](spec.md#L167); [regex sanitiser](../../apps/eval-runner/src/ama_eval/sanitise.py#L59) and case flags exist, not enforced Presidio candidate/review/publication gates. | AUD-030-006, AUD-030-017 |
| FR-024 | CONFLICT | [Required release gate/override/two consumers](spec.md#L168); [pure gate](../../apps/eval-runner/src/ama_eval/gate.py#L39) is incomplete/unwired, PR workflow manual and original 029 target retired. Safety obligations remain unresolved. | AUD-030-010, AUD-030-011, AUD-030-018 |
| FR-025 | PARTIAL | [Correct refusal versus failure](spec.md#L169); [rule](../../apps/eval-runner/src/ama_eval/evaluators/rule_based.py#L73) and [classifier](../../apps/eval-runner/src/ama_eval/orchestrator.py#L63) disagree for empty/filter/error cases and can reward no answer. | AUD-030-002, AUD-030-003 |
| FR-026 | PARTIAL | [Exact end-to-end reproducibility](spec.md#L173); [run schema](../../packages/eval-core/src/ama_eval_core/models.py#L405) records names/versions, but exact bytes/subset/config/metric/judge/policy/signature chain is unavailable in source artifacts. | AUD-030-001, AUD-030-008, AUD-030-011, AUD-030-014 |
| FR-027 | PARTIAL | [Ad-hoc/scheduled/pipeline shared evidence](spec.md#L174); [queue route](../../apps/api/app/api/routes/eval/runs.py#L69) exists; scheduled declarations/manual workflow are not a working schedule or change-bound dual consumer. | AUD-030-010, AUD-030-013 |
| FR-028 | PARTIAL | [Live progress/cancel](spec.md#L175); [cancel endpoint](../../apps/api/app/api/routes/eval/runs.py#L205) changes a document, but no SSE endpoint, repository polling or per-case counters drive live cancellation. | AUD-030-003, AUD-030-015 |
| FR-029 | PARTIAL | [Partial-result preservation](spec.md#L176); [in-memory trace accumulation](../../apps/eval-runner/src/ama_eval/orchestrator.py#L128) occurs only after all models; errors/cancel/crash have no reliable durable checkpoint path or partial status. | AUD-030-001, AUD-030-003, AUD-030-011 |

### Metric Family Detail

| FR-001 Family | Status | Inspected Scoring and Missing Obligation | Follow-up |
| --- | --- | --- | --- |
| a: quality (relevance, completeness, fluency, coherence) | PARTIAL | [Judge factory](../../apps/eval-runner/src/ama_eval/evaluators/judge.py#L32) lists relevance/coherence/fluency but is uncalled; token presence is not semantic completeness. | AUD-030-002 |
| b: factual correctness with ground truth | PARTIAL | The same [factory](../../apps/eval-runner/src/ama_eval/evaluators/judge.py#L32) lists factuality; no active ground-truth exact-match evaluator is in the default registry. | AUD-030-002 |
| c: groundedness/faithfulness | PARTIAL | [Token overlap](../../apps/eval-runner/src/ama_eval/evaluators/retrieval.py#L16) cannot establish semantic entailment; context is not passed to model execution. | AUD-030-002 |
| d: retrieval recall/precision | PARTIAL | [Context heuristics](../../apps/eval-runner/src/ama_eval/evaluators/retrieval.py#L36) count word overlap in output, not ranked retrieval; rank/k/nDCG absent. | AUD-030-002 |
| e: safety/harm and graphic-domain handling | PARTIAL | [Forbidden-token rule](../../apps/eval-runner/src/ama_eval/evaluators/rule_based.py#L56) lacks semantic harm evaluation and negation handling; no connected Content Safety evaluator. | AUD-030-002, AUD-030-007 |
| f: refusal correctness | PARTIAL | [Refusal rule](../../apps/eval-runner/src/ama_eval/evaluators/rule_based.py#L73) checks keywords/filter but fails empty-answer and expected action distinctions. | AUD-030-002 |
| g: tone/operational appropriateness | PARTIAL | [Tone tokens](../../apps/eval-runner/src/ama_eval/evaluators/rule_based.py#L130) and authority keywords are not compassion/directive accuracy/escalation semantics. | AUD-030-002, AUD-030-007 |
| h: prompt-injection resistance | PARTIAL | [Regex evaluator](../../apps/eval-runner/src/ama_eval/evaluators/prompt_injection.py#L24) only runs on prelabelled cases; harmful compliance without known phrases or malicious data without a label is not detected. | AUD-030-002 |
| i: latency and cost | PARTIAL | [Latency rule](../../apps/eval-runner/src/ama_eval/evaluators/rule_based.py#L150) excludes judges; [cost helper](../../apps/eval-runner/src/ama_eval/cost.py#L31) is not used by the run/report. | AUD-030-009, AUD-030-017 |

### Success Criterion Coverage

All twelve outcomes are UNVERIFIED: neither source structure, configured timeouts, mock responses,
nor historical unbound local artifacts prove the required achieved result. Concrete blockers are named.

| Success Criterion | Status | Required Outcome and Inspected Evidence | Follow-up |
| --- | --- | --- | --- |
| SC-001 | UNVERIFIED | [Leadership-ready current comparison](spec.md#L196); [scorecard source](../../apps/eval-runner/src/ama_eval/scorecard.py#L17) produces winners, but missing semantic metrics/baseline and broken dashboard prevent a defensible demonstrated decision. | AUD-030-002, AUD-030-010, AUD-030-015, AUD-030-018 |
| SC-002 | UNVERIFIED | [Full three-model run <=8h, no manual intervention, representative week](spec.md#L197); inspected local runs cover only 5/25 rule-scored cases and lack provision/evaluate/deprovision timing. | AUD-030-003, AUD-030-009, AUD-030-012, AUD-030-013, AUD-030-017, AUD-030-018 |
| SC-003 | UNVERIFIED | [Zero transient resources after policy timeout](spec.md#L198); [terminal-only reconciler](../../apps/eval-runner/src/ama_eval/reconciler.py#L35) and no dispatcher do not prove crashed-run cleanup. | AUD-030-003, AUD-030-012, AUD-030-013, AUD-030-018 |
| SC-004 | UNVERIFIED | [Independent 100% replay](spec.md#L199); [archive CLI](../../apps/eval-runner/src/ama_eval/evidence.py#L203) writes empty manifests and no signature, and run subsets/config are not fully recorded. | AUD-030-001, AUD-030-008, AUD-030-011, AUD-030-018 |
| SC-005 | UNVERIFIED | [Approved hazard floor owned by safety reviewer](spec.md#L200); all 13 counts exist, but [distribution helper](../../packages/eval-dataset/src/ama_eval_dataset/distribution.py#L71) only calculates statistics; approved floor/real case review absent. | AUD-030-006, AUD-030-007, AUD-030-018 |
| SC-006 | UNVERIFIED | [Every score traceable to case/output/metric/judge version](spec.md#L201); [trace assembly](../../apps/eval-runner/src/ama_eval/orchestrator.py#L181) lacks metric/judge attribution and storage uses case-only identity. | AUD-030-001, AUD-030-002, AUD-030-008, AUD-030-011, AUD-030-018 |
| SC-007 | UNVERIFIED | [Authored degradation blocked first time with sample diagnostic](spec.md#L202); [manual-only workflow](../../.github/workflows/eval-pr-gate.yml#L3) never evaluates changed prompts or the metric gate; no attributable live-fire PR. | AUD-030-010, AUD-030-018 |
| SC-008 | UNVERIFIED | [All runs costed/capped; rejection before provision](spec.md#L203); [API estimates](../../apps/api/app/api/routes/eval/runs.py#L42) are caller-owned and recorded scorecards omit cost. | AUD-030-009, AUD-030-012, AUD-030-018 |
| SC-009 | UNVERIFIED | [No sensitive leakage and logged permitted access](spec.md#L204); [case reader](../../apps/api/app/api/routes/eval/datasets.py#L71) breaches intended tier, and logging/export sentinel coverage is absent. This source blocker is not a claim of observed live leakage. | AUD-030-004, AUD-030-005, AUD-030-006, AUD-030-011, AUD-030-017, AUD-030-018 |
| SC-010 | UNVERIFIED | [Configuration-only new Foundry model comparison](spec.md#L205); [JSON registry](../../packages/eval-core/src/ama_eval_core/registries/models-v1.json#L1) has no production loader and current model lists are duplicated in source. | AUD-030-014, AUD-030-018 |
| SC-011 | UNVERIFIED | [Failed/cancelled partials visible with incomplete status](spec.md#L206); [run status enum](../../packages/eval-core/src/ama_eval_core/models.py#L87) has no partial state; cancellation/checkpoint flow is disconnected. | AUD-030-001, AUD-030-003, AUD-030-015, AUD-030-018 |
| SC-012 | UNVERIFIED | [Historical full evidence without original team](spec.md#L207); [same-day archive records](../../.eval-out/archive2.log#L11) lack the required manifests/signature/approval data and no independent historic review is recorded. | AUD-030-008, AUD-030-011, AUD-030-018 |

## Acceptance and Edge Cases

### Acceptance Scenarios

Scenario IDs below are assigned from each source story's numbered acceptance list (3+3+3+2+2+1).

| Scenario | Status | Expected Outcome, Source and Inspected Evidence | Follow-up |
| --- | --- | --- | --- |
| AS-1.1 | PARTIAL | [US1 comparison](spec.md#L25): multi-model metrics/version/winners. [Loop/builder](../../apps/eval-runner/src/ama_eval/orchestrator.py#L91) exists, but no active primary/secondary suite, exact reproducibility or trustworthy UI. | AUD-030-001, AUD-030-002, AUD-030-008, AUD-030-015 |
| AS-1.2 | PARTIAL | [US1 live progress/cancel](spec.md#L25): [cancel route](../../apps/api/app/api/routes/eval/runs.py#L205) writes state but no progress SSE, per-case polling or unconditional cleanup. | AUD-030-003, AUD-030-012, AUD-030-015 |
| AS-1.3 | PARTIAL | [US1 export/re-run](spec.md#L25): [bundle builder](../../apps/eval-runner/src/ama_eval/evidence.py#L43) exists; exported manifests/definitions/raw outputs/rationales/signature/repro metadata are incomplete. | AUD-030-001, AUD-030-008, AUD-030-011 |
| AS-2.1 | CONFLICT | [US2 sensitivity/reviewer routing](spec.md#L41): [generator](../../packages/eval-dataset/src/ama_eval_dataset/generator.py#L147) self-labels approved; publisher never routes/validates an independent reviewer. | AUD-030-005, AUD-030-006, AUD-030-007 |
| AS-2.2 | PARTIAL | [US2 immutable prior version](spec.md#L41): [hash conflict check](../../apps/api/app/api/routes/eval/datasets.py#L40) helps sequential requests, but upserts/races/remote hash trust do not enforce prior-version preservation. | AUD-030-006, AUD-030-008, AUD-030-011 |
| AS-2.3 | PARTIAL | [US2 exact filtered subset](spec.md#L41): [subset fields](../../packages/eval-core/src/ama_eval_core/models.py#L378) exist but requests lose filters and selection is prefix-only. | AUD-030-007, AUD-030-008, AUD-030-015 |
| AS-3.1 | PARTIAL | [US3 undeployed model -> create/use/remove](spec.md#L57): [provision helper](../../apps/eval-runner/src/ama_eval/provisioner.py#L46) never calls create; manual platform deployments are persistent, not run-scoped. | AUD-030-009, AUD-030-012, AUD-030-013 |
| AS-3.2 | MISSING | [US3 teardown on mid-run failure](spec.md#L57): [worker](../../apps/eval-runner/src/ama_eval/runner.py#L150) lacks finally/deprovision and durable failure context for partials. | AUD-030-003, AUD-030-012 |
| AS-3.3 | PARTIAL | [US3 resources/times/cost visible](spec.md#L57): [lifecycle model](../../packages/eval-core/src/ama_eval_core/models.py#L390) exists but runner/UI do not populate/render the required record. | AUD-030-009, AUD-030-012, AUD-030-015 |
| AS-4.1 | PARTIAL | [US4 baseline deltas](spec.md#L73): [gate](../../apps/eval-runner/src/ama_eval/gate.py#L89) reads a different baseline shape and does not power a change-bound gate. | AUD-030-008, AUD-030-010 |
| AS-4.2 | MISSING | [US4 logged override/notification](spec.md#L73): [registered API modules](../../apps/api/app/api/routes/eval/router.py#L40) do not expose override/check behavior; policy text is not implementation. | AUD-030-004, AUD-030-010, AUD-030-011 |
| AS-5.1 | PARTIAL | [US5 arbitrary prior run chain](spec.md#L88): [repositories](../../apps/api/app/repositories/eval/repositories.py#L180) retain some metadata but complete signed evidence, definitions and approvals cannot be reconstructed from archives. | AUD-030-001, AUD-030-008, AUD-030-011, AUD-030-018 |
| AS-5.2 | PARTIAL | [US5 original rationale, no regrading](spec.md#L88): [trace route](../../apps/api/app/api/routes/eval/traces.py#L20) reads stored data without regrading, but traces are not model-qualified and judge metadata/rationales are incomplete. | AUD-030-001, AUD-030-002, AUD-030-005, AUD-030-011 |
| AS-6.1 | PARTIAL | [US6 operational case -> PII removal/review](spec.md#L101): [regex helper](../../apps/eval-runner/src/ama_eval/sanitise.py#L59) exists; no publication/consent/dual-review/Presidio enforcement. | AUD-030-006 |

### Independent Story Tests and Personas

The hypothesised value of each story is assessed independently; no inferred personas or follow-on
specification scenarios were substituted for these six source stories.

| Story/Persona | Source Independent Test or Hypothesis | Evidence Assessment | Follow-up |
| --- | --- | --- | --- |
| US1 platform owner/evaluator | [Compare at least two registered models](spec.md#L31) on one published dataset; obtain defensible selection. | PARTIAL: five-case fake-client test proves local matrix/winner logic only; no attributable model/judge comparison. | AUD-030-002, AUD-030-008, AUD-030-018 |
| US2 SME plus safety reviewer | [Author, approve and publish immutable labelled dataset](spec.md#L47). | PARTIAL: generated corpus and manifest exist; draft-to-review approval/immutable publication not demonstrated. | AUD-030-006, AUD-030-007 |
| US3 evaluation engineer/platform owner | [Run not-yet-deployed model and confirm teardown/cost](spec.md#L63). | UNVERIFIED: record-only provision helper and platform-level logs cannot satisfy independent lifecycle test. | AUD-030-009, AUD-030-012, AUD-030-018 |
| US4 developer/authorised approver | [Deliberate safety degradation blocks first attempt](spec.md#L79). | UNVERIFIED: no changed-prompt binding/required gate/override flow or attributable live-fire PR. | AUD-030-010, AUD-030-018 |
| US5 governance reviewer | [Retrieve historical artifacts/rationale](spec.md#L88); tasks additionally require independent signed 30-day replay. | UNVERIFIED: read-only trace code is positive, but current archives are incomplete/unsigned and not independently replayed. | AUD-030-001, AUD-030-011, AUD-030-018 |
| US6 operations lead/reviewers | [Sanitised real case with policy clearance](spec.md#L101). | PARTIAL: regex redaction is not a complete reviewed candidate-publication workflow; actual consent/approval unverified. | AUD-030-006, AUD-030-018 |

### Edge Cases

All eight bullets in [source Edge Cases](spec.md#L113) are represented, in source order.

| Edge Case | Status | Expected/Actual and Controlling Evidence | Follow-up |
| --- | --- | --- | --- |
| EC-01 | PARTIAL | Graphic legitimate request filtered versus correct refusal: [client](../../apps/eval-runner/src/ama_eval/foundry_client.py#L152) observes finish reason but exceptions become empty output; rule/classifier disagree and semantic appropriateness is not scored. | AUD-030-002, AUD-030-003 |
| EC-02 | PARTIAL | No single right answer: [rubric fields](../../packages/eval-core/src/ama_eval_core/models.py#L180) allow actions/tone/referral, but registered evaluators do not score uncertainty/form adequately and generated expected actions can conflict. | AUD-030-002, AUD-030-007 |
| EC-03 | MISSING | Mid-run quota exhaustion must pause/preserve/tear down: [client exception path](../../apps/eval-runner/src/ama_eval/foundry_client.py#L167) converts it into empty scored output; no pause/checkpoint/deadline-driven cleanup. | AUD-030-003, AUD-030-009, AUD-030-012 |
| EC-04 | PARTIAL | Independent concurrent same-model/dataset requests: [random run IDs](../../apps/api/app/api/routes/eval/runs.py#L61) avoid deliberate deduplication, but capacity reservation is nonatomic and snapshots/idempotency policies are incomplete. | AUD-030-008, AUD-030-009 |
| EC-05 | PARTIAL | Empty/malformed output must be recorded and typically fail: [client](../../apps/eval-runner/src/ama_eval/foundry_client.py#L167) masks errors, refusal-answer rule can pass empty output and exception cases disappear from scores. | AUD-030-001, AUD-030-002, AUD-030-003 |
| EC-06 | MISSING | Updated judge must create metric version and retain original: [metric model](../../packages/eval-core/src/ama_eval_core/models.py#L317) lacks judge-version invariant; no activation/version-snapshot writer path. | AUD-030-002, AUD-030-008, AUD-030-011 |
| EC-07 | PARTIAL | Injection-like dataset content detected separately: [label filter](../../apps/eval-runner/src/ama_eval/orchestrator.py#L174) runs regex metric only when prelabelled, so unlabeled injection/data-instruction boundaries are not detected. | AUD-030-002, AUD-030-007 |
| EC-08 | MISSING | Cancellation/process death must reconcile within a bound: [terminal-only reconciler](../../apps/eval-runner/src/ama_eval/reconciler.py#L35) and missing dispatcher do not cover crashed active runs. | AUD-030-003, AUD-030-012, AUD-030-013 |

## Nonfunctional and Design Obligations

### Nonfunctional Coverage

These are explicit prose obligations from [plan technical context](plan.md#L10),
[spec clarifications](spec.md#L10), [data invariants](data-model.md#L219), and original tasks,
not invented source NFR IDs. Runtime outcomes remain UNVERIFIED even where a partial mechanism exists.

| Obligation | Status | Required Boundary and Evidence | Follow-up |
| --- | --- | --- | --- |
| NF-01 full workload <=8h | UNVERIFIED | Three MUTs x 5,000 cases x all metric tiers including judges; [job timeout](../../infra/bicep/modules/eval/eval-platform.bicep#L413) alone excludes queue/provision/report and is not representative-week evidence. | AUD-030-003, AUD-030-009, AUD-030-017, AUD-030-018 |
| NF-02 PR subset <=30m | PARTIAL | [Policy threshold](../../packages/eval-core/src/ama_eval_core/policy.py#L127) exists, but no stratified fast selector/deadline; workflow timeout is 35m and missing-result handling is fail-open. | AUD-030-008, AUD-030-009, AUD-030-010 |
| NF-03 per-sample p95 <=30s incl. judge | UNVERIFIED | [Latency-budget evaluator](../../apps/eval-runner/src/ama_eval/evaluators/rule_based.py#L150) scores model-call latency only; no p95 wall-time dataset/measurement. | AUD-030-002, AUD-030-017, AUD-030-018 |
| NF-04 reconciliation bound | PARTIAL | <=60m after recorded max duration; [terminal-only helper](../../apps/eval-runner/src/ama_eval/reconciler.py#L35) has no max-duration expiry or operational dispatch. | AUD-030-012, AUD-030-013 |
| NF-05 independent concurrency and bounded cost | PARTIAL | [Random IDs](../../apps/api/app/api/routes/eval/runs.py#L61) support independent runs; capacity count, estimates and immutable subset identity remain defective. | AUD-030-008, AUD-030-009 |
| NF-06 seven calendar years from completion | PARTIAL | [2,555-day creation-relative policy](../../infra/bicep/modules/eval/eval-platform.bicep#L186) is shorter across leap years and starts before run completion; unlocked/dev-disabled states not claimed WORM. | AUD-030-011, AUD-030-013 |
| NF-07 AU data residency and approved model-host carve-out | PARTIAL | [AU defaults](../../infra/bicep/modules/eval/eval-platform.bicep#L27) exist, but placement is free string and no eval gateway/carve-out lookup/minimisation is enforced. Live placement/approval unverified. | AUD-030-009, AUD-030-013, AUD-030-017, AUD-030-018 |
| NF-08 no static credentials and least privilege | PARTIAL | Foundry/Cosmos/Blob use DefaultAzureCredential; [RBAC module](../../infra/bicep/modules/eval/eval-rbac.bicep#L51) grants RG-wide roles and active runner lacks write rights. Workflow credential migration is explicit; installed auth configuration not verified. | AUD-030-004, AUD-030-013 |
| NF-09 authenticated tiers, no external redistribution | CONFLICT | [Case reader](../../apps/api/app/api/routes/eval/datasets.py#L71), unsigned claims and unfiltered exceptions defeat intended audience controls; export/telemetry redaction missing. | AUD-030-004, AUD-030-005, AUD-030-017 |
| NF-10 PII minimisation, APP6/11 and real-case clearance | PARTIAL | [Regex redactor](../../apps/eval-runner/src/ama_eval/sanitise.py#L59) is not a trusted publication-time screen or consent/review chain. | AUD-030-006, AUD-030-017 |
| NF-11 replayability, stable schemas and growth | PARTIAL | [Parameterized corpus size](../../packages/eval-dataset/src/ama_eval_dataset/generator.py#L111) is positive; no exact immutable run snapshots, generator version parameter or schema-compatible canonical byte contract. | AUD-030-007, AUD-030-008, AUD-030-011 |
| NF-12 WCAG 2.2 AA | UNVERIFIED | [Basic table markup](../../apps/web/src/app/eval/page.tsx#L60) is not an audit; detail shape failure and absent workflows preclude full route assessment. | AUD-030-015, AUD-030-018 |
| NF-13 Python/Next/toolchain/workspace | CONFLICT | Plan pins Python 3.13; [image](../../apps/eval-runner/Dockerfile#L2)/metadata/CI use 3.12, guide says 3.11; API does not declare eval-core dependency and no uv eval workspace is configured. | AUD-030-013, AUD-030-014, AUD-030-016 |
| NF-14 API p95, queue/start SLO, telemetry and recovery | MISSING | [Task T082/T083](tasks.md#L408) requires SLOs and per-case spans; generic App Insights declarations are not emitted SLIs, dashboards or alerts. | AUD-030-017, AUD-030-018 |

### Research Decisions and Conflicts

| Decision | Status | Evidence and Resolution Needed | Follow-up |
| --- | --- | --- | --- |
| D1 | CONFLICT | [Microsoft SDK engine/internal registry](research.md#L13) rejects hand-built scoring as primary; [default evaluators](../../apps/eval-runner/src/ama_eval/evaluators/__init__.py#L1) are handcrafted rules and judge factory is uncalled. | AUD-030-002 |
| D2 | PARTIAL | [Projects/deployment/version identity](research.md#L32); [client](../../apps/eval-runner/src/ama_eval/foundry_client.py#L94) instead uses Inference SDK, with actual invocation/params/version issues. Adapter renaming alone is not failure; missing contract behavior is. | AUD-030-014 |
| D3 | CONFLICT | [What-If/lease/finally/reconciler](research.md#L49) is disconnected. Research says daily cron, tasks/plan require 30-minute scheduling/bounded cleanup; resolve scheduling to the explicit FR-019 bound. | AUD-030-003, AUD-030-012, AUD-030-013 |
| D4 | PARTIAL | [Storage layout](research.md#L75) partly exists; archives/traces/signatures/7-year telemetry and immutable projection are not supplied by the current [platform](../../infra/bicep/modules/eval/eval-platform.bicep#L85). | AUD-030-001, AUD-030-011, AUD-030-013 |
| D5 | CONFLICT | [API-enforced tiers](research.md#L103) versus viewer case bodies, unsigned claims and unscoped anonymous trace access. | AUD-030-004, AUD-030-005 |
| D6 | CONFLICT | [One scorecard/two consumers](research.md#L116), per-mode idempotency and fast/full workloads need an explicit authoritative-evidence relationship; old 029 target is retired, not proof the safety gate is optional. | AUD-030-010 |
| D7 | CONFLICT | [PR/schema/PII/safety review/immutable publish](research.md#L134); [workflow](../../.github/workflows/eval-publish-dataset.yml#L3) is manual, cloud steps commented and approval rules absent. | AUD-030-006 |
| D8 | CONFLICT | [Frontier generation/drafts/distribution](research.md#L152); replacement generates approved multilingual templates and does not bind expected action to prompt. | AUD-030-007 |
| D9 | PARTIAL | [Next.js tiered views/native fetch](research.md#L166); two renamed pages exist, but typed-client contract and dataset/trace/gate/progress views are incomplete. | AUD-030-015 |
| D10 | PARTIAL | [Complete signed evidence/control mapping](research.md#L181); [archive CLI](../../apps/eval-runner/src/ama_eval/evidence.py#L203) writes empty manifests and no signature member. | AUD-030-011, AUD-030-018 |

### Data Model Accounting

| Entity or Invariant | Status | Source and Implementation Evidence | Follow-up |
| --- | --- | --- | --- |
| DM-01 EvaluationCase | PARTIAL | [Fields/invariants](data-model.md#L29); [model](../../packages/eval-core/src/ama_eval_core/models.py#L203) has many fields and selected validators, but schema parity, genuine approvals, v1 publication language and real-case checks differ. | AUD-030-006, AUD-030-007, AUD-030-008 |
| DM-02 EvaluationDatasetVersion | PARTIAL | [One-way published state](data-model.md#L60); [model](../../packages/eval-core/src/ama_eval_core/models.py#L285) permits any positive count/state and route trusts incoming metadata. | AUD-030-006, AUD-030-008 |
| DM-03 MetricDefinitionVersion | PARTIAL | [Written/versioned bindings](data-model.md#L83); [model](../../packages/eval-core/src/ama_eval_core/models.py#L317) omits definitionMarkdown, primary/secondary version binding and active-with-baseline invariant. | AUD-030-002, AUD-030-008 |
| DM-04 JudgeModelVersion | PARTIAL | [Judge approval/deployment/bound metrics](data-model.md#L108); [model](../../packages/eval-core/src/ama_eval_core/models.py#L337) differs, registry judge entries lack its approval fields, and no writer/loader binds runtime. | AUD-030-002, AUD-030-008, AUD-030-014 |
| DM-05 ModelUnderTest | PARTIAL | [Tier/profile/policy/state](data-model.md#L120); [model](../../packages/eval-core/src/ama_eval_core/models.py#L364) only has optional placement/params/catalog, incompatible with direct rich registry entry ingestion. | AUD-030-008, AUD-030-014 |
| DM-06 EvaluationRun | PARTIAL | [Snapshots/progress/lifecycle/cost/state](data-model.md#L133); [model](../../packages/eval-core/src/ama_eval_core/models.py#L405) and enqueue lack the required immutable references, partial state and progress accounting. | AUD-030-003, AUD-030-008, AUD-030-009 |
| DM-07 Scorecard | PARTIAL | [Summary/detail separation](data-model.md#L169); [builder](../../apps/eval-runner/src/ama_eval/scorecard.py#L17) provides aggregates but missing policies/denominators/diagnostics/cost/exports. | AUD-030-002, AUD-030-010, AUD-030-011 |
| DM-08 SampleTrace | CONFLICT | [One run/model/case tuple](data-model.md#L178) conflicts with [case-only storage example](data-model.md#L16); implementation also lacks metric/judge version/tier/sensitivity snapshots. | AUD-030-001, AUD-030-002, AUD-030-005, AUD-030-008 |
| DM-09 Baseline | PARTIAL | [Pointer/scope/supersession](data-model.md#L182); [repository](../../apps/api/app/repositories/eval/repositories.py#L307) exists but no designation API/audit or dereferenced scorecard use. | AUD-030-008, AUD-030-010 |
| DM-10 ProvisioningPolicy | PARTIAL | [Distinct data/model regions and snapshot](data-model.md#L186); [API](../../apps/api/app/api/routes/eval/runs.py#L78) hard-codes dev and trusts estimates; schema role names differ from API roles. | AUD-030-004, AUD-030-008, AUD-030-009 |
| DM-11 InfrastructureLifecycleRecord | PARTIAL | [Events/actions/terminal states](data-model.md#L203); [model](../../packages/eval-core/src/ama_eval_core/models.py#L390) is simplified and no actual resource lifecycle fills it. | AUD-030-003, AUD-030-012 |
| DM-12 AuditEvent | PARTIAL | [Before/after/evidence refs/append/projection](data-model.md#L209); [model/emitter](../../packages/eval-core/src/ama_eval_core/audit.py#L89) uses subject/metadata but incomplete mutation coverage/projection and invalid deployment subjects remain. | AUD-030-011, AUD-030-012 |
| INV-01 published dataset required | MISSING | [Invariant 1](data-model.md#L221); [enqueue](../../apps/api/app/api/routes/eval/runs.py#L69) instantiates DatasetRepository but never checks publication. | AUD-030-006, AUD-030-008 |
| INV-02 active metric/judge versions at run start | MISSING | [Invariant 2](data-model.md#L222); [registry loop](../../apps/eval-runner/src/ama_eval/orchestrator.py#L89) does not resolve active versioned definitions. | AUD-030-002, AUD-030-008 |
| INV-03 deployment within snapshotted placement policy | PARTIAL | [Invariant 3](data-model.md#L223); [policy helper](../../packages/eval-core/src/ama_eval_core/policy.py#L94) skips absent fields and run stores policyVersion only. | AUD-030-008, AUD-030-009 |
| INV-04 no graphic body in summary export | PARTIAL | [Invariant 4](data-model.md#L224); current builder uses aggregates, but extra-allow scorecards/no explicit summary projection/sentinel test and viewer case access do not establish the full boundary. | AUD-030-005, AUD-030-011 |
| INV-05 append-only audit and compensating corrections | PARTIAL | [Invariant 5](data-model.md#L225); Cosmos create_item is positive, but memory upserts, data mutation audit gaps and broad roles/no immutable projection leave the whole guarantee incomplete. | AUD-030-011, AUD-030-013 |

### API Contract Accounting

Method/path identities are the source contract, not a claim that the routes are present.

| Contract Item | Status | Source and Current Behavior | Follow-up |
| --- | --- | --- | --- |
| API-01 publish dataset version | CONFLICT | [POST versions](contracts/api.md#L22) expects requested count/distribution and safety role; current route accepts an entire manifest from operator. | AUD-030-006, AUD-030-008 |
| API-02 list dataset families | MISSING | [GET datasets](contracts/api.md#L53) has no registered equivalent in S-API. | AUD-030-008, AUD-030-015 |
| API-03 retrieve version manifest | PARTIAL | [GET version](contracts/api.md#L57) implemented, but manifest trust/immutable backing and roles remain incomplete. | AUD-030-005, AUD-030-006 |
| API-04 stream/page cases | CONFLICT | [GET cases](contracts/api.md#L61) requires Tier-2 and JSONL/paging; route returns limited repository list to viewer, without blob publication reader. | AUD-030-005, AUD-030-008 |
| API-05 create metric draft | MISSING | [POST metrics](contracts/api.md#L69); current metrics router has GET only. | AUD-030-002, AUD-030-008 |
| API-06 activate metric version | MISSING | [POST activate](contracts/api.md#L73); no active/version/baseline validation writer. | AUD-030-002, AUD-030-008 |
| API-07 register/approve judge | MISSING | [POST judges](contracts/api.md#L77); repository save_judge alone is not authenticated approval. | AUD-030-002, AUD-030-008 |
| API-08 queue run | CONFLICT | [POST runs](contracts/api.md#L85) response 202/estimates/validation versus flat request/201/summary and unverified references. | AUD-030-008, AUD-030-009 |
| API-09 retrieve run summary | PARTIAL | [GET run](contracts/api.md#L126) exists; dynamic extras/no immutable snapshot or live progress weaken contract. | AUD-030-003, AUD-030-005, AUD-030-008 |
| API-10 stream progress | MISSING | [GET progress/SSE](contracts/api.md#L128); no registered route/stream implementation. | AUD-030-003, AUD-030-015 |
| API-11 cancel and teardown | PARTIAL | [POST cancel](contracts/api.md#L130) writes cancelling but worker never polls or tears down. | AUD-030-003, AUD-030-012 |
| API-12 filtered run list | PARTIAL | [GET runs filters](contracts/api.md#L132); only status_filter/mode/limit implemented, no dataset/since/changeRef/pagination contract. | AUD-030-008, AUD-030-015 |
| API-13 scorecard summary | CONFLICT | [GET scorecards/id](contracts/api.md#L138) replaced by /runs/id/scorecard and different winner/models shape without explicit compatibility resolution. | AUD-030-008, AUD-030-015 |
| API-14 paged traces | MISSING | [GET traces](contracts/api.md#L153); no list reader in S-API. | AUD-030-001, AUD-030-005, AUD-030-015 |
| API-15 single case/model trace | PARTIAL | [GET trace tuple](contracts/api.md#L157); replacement route lacks model ID and uses case-only key. | AUD-030-001, AUD-030-005 |
| API-16 JSON/HTML/bundle export | MISSING | [GET export](contracts/api.md#L161); CLI bundling is incomplete and no tiered API endpoint exists. | AUD-030-005, AUD-030-011 |
| API-17 change-bound gate check | MISSING | [POST gate/check](contracts/api.md#L169); pure uncalled gate helper and YAML policy are not API implementation. | AUD-030-010 |
| API-18 justified override | MISSING | [POST override](contracts/api.md#L197); no role/justification/approver/record/audit/notification writer. | AUD-030-004, AUD-030-010, AUD-030-011 |
| API-19 identity, errors, Location/ETag, idempotency | CONFLICT | [Global contracts](contracts/api.md#L10), [idempotency/errors](contracts/api.md#L203): unsigned roles, varying detail envelopes, missing conditional writes and change idempotency; reconcile fast/full identity ambiguity. | AUD-030-004, AUD-030-008, AUD-030-010 |
| API-20 worker input/output/exit/cancel | CONFLICT | [Worker contract](contracts/api.md#L212): run-id-only entry differs from required dataset args/settings; no complete signed output/partial/cancel/orphan exit/finally lifecycle. | AUD-030-003, AUD-030-008, AUD-030-011, AUD-030-013 |
| API-21 web route/role/consumer table | PARTIAL | [Web contract](contracts/api.md#L223): renamed list/detail pages only, wrong shape/auth and absent dataset/gate/trace views. | AUD-030-015 |

## Amendment and Review Accounting

### Clarifications and Dev Amendment

| Obligation | Status | Source and Evidence Assessment | Follow-up |
| --- | --- | --- | --- |
| CL-01 dataset 5,000 approved, growth to 10k+ | PARTIAL | [Clarification](spec.md#L12); row count exists, actual review and coherent versioned growth remain incomplete. | AUD-030-006, AUD-030-007 |
| CL-02 hybrid primary/secondary judges | PARTIAL | [Clarification](spec.md#L13); no production registration/sampled secondary caller. | AUD-030-002 |
| CL-03 ISO42001/NIST/APP evidence | PARTIAL | [Clarification](spec.md#L14); mapping/signature/PII/audit chain absent or incomplete. | AUD-030-006, AUD-030-011, AUD-030-018 |
| CL-04 frontier/mid/Phi minimum set | PARTIAL | [Clarification](spec.md#L15); registry and separate seven-model list exist but config-only deploy/version attribution and real evaluations are unverified. | AUD-030-014, AUD-030-018 |
| CL-05 shared PR/promotion scorecard | CONFLICT | [Clarification](spec.md#L16); old promotion target retired, PR manual-only; per-mode contract needs explicit shared-record definition. | AUD-030-010 |
| CL-06 full run <=8h | UNVERIFIED | [Clarification](spec.md#L17); bounded case artifacts/timeout declaration are not full-run evidence. | AUD-030-009, AUD-030-017, AUD-030-018 |
| CL-07 seven-year artifact/audit retention | PARTIAL | [Clarification](spec.md#L18); creation-based 2,555-day and unlocked/dev-disabled configuration do not establish required completion-based retention. | AUD-030-011, AUD-030-013 |
| CL-08 English-only v1, extensible languages later | CONFLICT | [Clarification](spec.md#L19); committed multilingual v1 directly disagrees. | AUD-030-007, AUD-030-008 |
| CL-09 independent concurrent requests | PARTIAL | [Clarification](spec.md#L20); distinct IDs exist but capacity atomicity, snapshots and retry semantics need repair. | AUD-030-008, AUD-030-009 |
| CL-10 staff summary and restricted detail | CONFLICT | [Clarification](spec.md#L21); viewer case bodies/unsigned identity/anonymous detail bypass documented access control. | AUD-030-004, AUD-030-005 |
| AM-01 explicit dev-only enablement | PARTIAL | [FR-022a](spec.md#L166), [T091](tasks.md#L442): dual flags are checked for no-header requests, but ENVIRONMENT is normalized and invalid nondev enablement does not refuse startup. | AUD-030-004, AUD-030-013 |
| AM-02 every anonymous audit has principal/environment | PARTIAL | [T091](tasks.md#L442): run/dataset routes tag selected events, but trace/scorecard/audit/runner events omit environment, and some reads/cancel paths omit dataset eligibility. | AUD-030-005, AUD-030-011 |
| AM-03 only approved synthetic-dev content | CONFLICT | [FR-022a(b)](spec.md#L166), [T095](tasks.md#L454): guard checks name only. `synthetic-dev` mentioned by tasks is not a schema sensitivity label; same-name real/other labels are not rejected. | AUD-030-005, AUD-030-008 |
| AM-04 staging/production full roles, no anonymous | PARTIAL | [T092](tasks.md#L445): anonymous flag conditional is correct, but ENVIRONMENT remains common (useful for safety) despite literal both-vars-absent wording. Full verified role model still missing. | AUD-030-004, AUD-030-013 |
| AM-05 probe health and omit token across stages | PARTIAL | [T093](tasks.md#L448): execute probe/header tests exist; archive uses its own hard-coded fallback API and nonpropagated credentials, not a proven consistent environment flow. | AUD-030-011, AUD-030-014 |
| AM-06 update docs and live validate without app/audience/token | UNVERIFIED | [T094/T095](tasks.md#L451): docs updated but overclaim behavior; logs include an audience on provision and lack required full audit/label rejection evidence. | AUD-030-005, AUD-030-014, AUD-030-018 |

### Specification Quality Checklist

All 16 original checked items are accounted for; checked state is authored source state, not an audit pass.

| Checklist Item | Source State | Status | Source and Assessment | Follow-up |
| --- | --- | --- | --- | --- |
| CQ-01 no implementation details | [x] | CONFLICT | [Item](checklists/requirements.md#L9); spec includes Foundry, API flags, exact JSON/config paths and GitHub/Entra implementation constraints. | AUD-030-008, AUD-030-018 |
| CQ-02 user value/business focus | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L10); six stories explicitly describe decision, safety, cost and governance value. This is document quality only. | none |
| CQ-03 nontechnical stakeholders | [x] | PARTIAL | [Item](checklists/requirements.md#L11); stories are accessible but detailed flags/schema/runtime terms remain in requirements/amendment. | AUD-030-018 |
| CQ-04 mandatory sections complete | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L12); stories, edge cases, requirements, entities, SCs, assumptions and exclusions are authored. | none |
| CQ-05 no unresolved clarification markers | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L16); no unresolved NEEDS CLARIFICATION slot exists in spec; this does not resolve identified cross-document conflicts. | none |
| CQ-06 unambiguous/testable requirements | [x] | PARTIAL | [Item](checklists/requirements.md#L17); per-mode versus one-scorecard, dev sensitivity marker, retention, hash and lifecycle conflicts require explicit resolution. | AUD-030-008, AUD-030-010, AUD-030-011 |
| CQ-07 measurable SCs | [x] | PARTIAL | [Item](checklists/requirements.md#L18); budgets/counts are measurable, but defined minimum-share owner/floor and representative-week evidence are missing. | AUD-030-007, AUD-030-018 |
| CQ-08 technology-agnostic SCs | [x] | CONFLICT | [Item](checklists/requirements.md#L19); SCs name Foundry and a concrete distribution file; evaluate on actual intent, not this unchecked abstraction assumption. | AUD-030-018 |
| CQ-09 acceptance scenarios defined | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L20); all 14 are authored and accounted for in AS ledger. | none |
| CQ-10 edge cases identified | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L21); all eight are authored and accounted for in EC ledger. | none |
| CQ-11 scope bounded | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L22); explicit assumptions/exclusions and dev-only exception exist, though implementation violates some boundaries. | none |
| CQ-12 dependencies/assumptions identified | [x] | PARTIAL | [Item](checklists/requirements.md#L23); source names existing platform/governance/029, but 029 is now retired and effective replacement requires resolution. | AUD-030-010, AUD-030-018 |
| CQ-13 every FR has clear acceptance | [x] | PARTIAL | [Item](checklists/requirements.md#L27); story criteria exist, but tier percentages, approval floor, mode identity and amendment content boundary remain ambiguous/incomplete. | AUD-030-002, AUD-030-007, AUD-030-010 |
| CQ-14 scenarios cover primary flows | [x] | IMPLEMENTED | [Item](checklists/requirements.md#L28); all six story intents are represented. Coverage definition is not executed acceptance. | none |
| CQ-15 feature meets measurable outcomes | [x] | UNVERIFIED | [Item](checklists/requirements.md#L29); all 12 SC outcomes remain unverified and have source blockers. | AUD-030-018 |
| CQ-16 no implementation detail leakage | [x] | CONFLICT | [Item](checklists/requirements.md#L30); same specification-level technology details as CQ-01, not proof of completion. | AUD-030-008, AUD-030-018 |

Checklist notes are also accounted for: first-iteration readiness is an authored assertion; sensitive
content is intentionally in scope but governed (AUD-030-005/006); Microsoft metric families are assessed
in FR-001; policy numbers now exist in the dev policy but are not loaded (AUD-030-009). No checklist was edited.

### Operator and Quickstart Checklists

All 19 unchecked boxes in the [manual guide](../../docs/llm-evaluation/manual-evaluation-guide.md#L28)
remain unverified operator prerequisites/results; these are not demands to run them during this audit.

| Operator Item | Source State | Status | Source Obligation and Available Evidence | Follow-up |
| --- | --- | --- | --- | --- |
| OP-01 evaluator membership | [ ] | UNVERIFIED | Guide identity checklist; no authenticated membership/role-assignment record inspected. | AUD-030-004, AUD-030-018 |
| OP-02 Azure login/subscription | [ ] | UNVERIFIED | Logs name a historical subscription, not current authenticated context; no cloud query performed. | AUD-030-018 |
| OP-03 provision permissions/AI Developer | [ ] | UNVERIFIED | Historical provision messages do not verify exact effective least-privilege roles. | AUD-030-013, AUD-030-018 |
| OP-04 ACR build permission | [ ] | UNVERIFIED | Historical latest-task status fallback is not an attributable image/permission validation at HEAD. | AUD-030-014, AUD-030-018 |
| OP-05 PowerShell/bash version | [ ] | UNVERIFIED | [Tool checklist](../../docs/llm-evaluation/manual-evaluation-guide.md#L39); no tool-version validation run. | AUD-030-018 |
| OP-06 Python 3.11 | [ ] | CONFLICT | Guide says 3.11 while metadata/image/CI require/use 3.12 and plan says 3.13. | AUD-030-013, AUD-030-014 |
| OP-07 Node/pnpm versions | [ ] | UNVERIFIED | Guide versions differ from present CI toolchain; no environment install/probe executed. | AUD-030-014, AUD-030-018 |
| OP-08 Azure CLI version | [ ] | UNVERIFIED | No tool/cloud probe; historical command strings do not verify current availability. | AUD-030-018 |
| OP-09 clean main checkout | [ ] | UNVERIFIED | HEAD verified exactly; no branch/clean-worktree claim and no resets/commits made. | AUD-030-018 |
| OP-10 baseline pytest/ruff/build green | [ ] | UNVERIFIED | [Pre-run checklist](../../docs/llm-evaluation/manual-evaluation-guide.md#L429); no attributable current results. | AUD-030-016, AUD-030-018 |
| OP-11 production baseline scorecard | [ ] | UNVERIFIED | Inspected scorecards omit baseline; no designated immutable baseline evidence. | AUD-030-010, AUD-030-018 |
| OP-12 model quota | [ ] | UNVERIFIED | No quota query authorised; declared model names/capacities are not availability. | AUD-030-009, AUD-030-018 |
| OP-13 cost cap covers estimate | [ ] | PARTIAL | Pure policy exists but API trusts caller cost and CLI sends zero. | AUD-030-009 |
| OP-14 operations announcement | [ ] | UNVERIFIED | No external chat/approval accessed or generated. | AUD-030-018 |
| OP-15 scorecard fetched/persisted | [ ] | PARTIAL | [Execute log](../../.eval-out/execute.log#L17) records save of an empty-metric scorecard; not successful acceptance. | AUD-030-001, AUD-030-018 |
| OP-16 evidence uploaded | [ ] | PARTIAL | [Archive retry](../../.eval-out/archive2.log#L23) records upload, but inspected contents omit required evidence/signature. | AUD-030-011, AUD-030-018 |
| OP-17 lifecycle terminal clean | [ ] | UNVERIFIED | Archived runs do not carry a proven lifecycle record; controller never performs required teardown. | AUD-030-003, AUD-030-012 |
| OP-18 reconciler zero orphans | [ ] | UNVERIFIED | No attributable sweep results; incorrect terminal/tag logic and no dispatcher. | AUD-030-012, AUD-030-013, AUD-030-018 |
| OP-19 blocked-gate ticket/sample IDs | [ ] | UNVERIFIED | No actual gate/diagnostic/ticket record; no external issue action performed. | AUD-030-010, AUD-030-018 |

The guide's six numbered incident steps are also assessed: capture event/run ID (UNVERIFIED; audit gaps),
retrieve logs (CONFLICT: documented command reads job args, not logs), trigger reconciler (PARTIAL: declared
job is misdispatched), mark failed via cancel (CONFLICT: cancel writes cancelling and is not polled),
file incident (UNVERIFIED; external action deferred), and recheck cost/orphans before retry (PARTIAL:
current checks do not establish either). AUD-030-003/009/012/014/018 cover these exact obligations.

| Quickstart Item | Status | Source and Assessment | Follow-up |
| --- | --- | --- | --- |
| QS-01 prerequisites | UNVERIFIED | [All six prerequisites](quickstart.md#L10): evaluator membership, green dev platform, Azure login/subscription/location, create/deploy permission, Foundry account/carve-out and GitHub write access are not inferred from text. | AUD-030-004, AUD-030-013, AUD-030-018 |
| QS-02 platform flow and resource verification | PARTIAL | [Flow 1](quickstart.md#L21): authored Bicep/logs exist but job readiness does not prove all job roles, private access, RBAC or immutable retention. | AUD-030-011, AUD-030-013, AUD-030-014 |
| QS-03 publish flow and verify manifest | PARTIAL | [Flow 2](quickstart.md#L43): legacy generator/test paths, inactive workflow publication and unreviewed corpus; skip-api-register cannot count as registered publication. | AUD-030-006, AUD-030-007, AUD-030-014 |
| QS-04 run/progress/scorecard/cost/cleanup | PARTIAL | [Flow 3](quickstart.md#L81): request contract differs; no SSE/cost/lifecycle cleanup; saved small scorecards not full-run evidence. | AUD-030-003, AUD-030-008, AUD-030-009, AUD-030-015 |
| QS-05 PR gate and staged promotion | CONFLICT | [Flow 4](quickstart.md#L124): actual workflows manual/retired target and missing candidate binding/check API. | AUD-030-010 |
| QS-06 platform teardown and retained artifacts | CONFLICT | [Flow 5](quickstart.md#L147): recommended separately retained storage RG is not the platform's actual same-RG layout; no destructive operation is authorised here. | AUD-030-011, AUD-030-013, AUD-030-014 |
| QS-07 done: three-model comparable winner | UNVERIFIED | [Done bullet 1](quickstart.md#L161); source has matrix/winner logic but incomplete judges/metrics and no defensible full evaluation. | AUD-030-002, AUD-030-018 |
| QS-08 done: immutable approved v1 | UNVERIFIED | [Done bullet 2](quickstart.md#L162); state/hash labels do not prove approval or locked storage. | AUD-030-006, AUD-030-011, AUD-030-018 |
| QS-09 done: resources removed/zero orphans | UNVERIFIED | [Done bullet 3](quickstart.md#L163); no actual per-run create/use/remove/sweep chain. | AUD-030-012, AUD-030-018 |
| QS-10 done: safety PR blocked | UNVERIFIED | [Done bullet 4](quickstart.md#L164); no functioning change gate or attributable first failure. | AUD-030-010, AUD-030-018 |
| QS-11 done: independent historic replay | UNVERIFIED | [Done bullet 5](quickstart.md#L165); incomplete unsigned archives cannot satisfy this. | AUD-030-011, AUD-030-018 |
| QS-12 dev anonymous flow | PARTIAL | [Flow 6](quickstart.md#L169): flags/probe documented, but content/roles/audit and archive boundaries overclaimed. | AUD-030-004, AUD-030-005, AUD-030-014 |

### Review and Process Obligations

| Review Obligation | Status | Source and Available Evidence | Follow-up |
| --- | --- | --- | --- |
| RV-01 foundational design/rubber-duck review | UNVERIFIED | [T023](tasks.md#L117): no dated independent findings/disposition or attributable test run. | AUD-030-018 |
| RV-02 orchestrator/evaluator blind-spot review | UNVERIFIED | [T041](tasks.md#L190): no review record; concrete scoring/lifecycle gaps remain. | AUD-030-002, AUD-030-003, AUD-030-018 |
| RV-03 operational SME rubric realism | UNVERIFIED | [T026/T044](tasks.md#L142) require incident/risk/public-information/sector consultation; generated action mismatches and auto-review strings do not prove consultation. | AUD-030-007, AUD-030-018 |
| RV-04 published-v1 compliance review | UNVERIFIED | [T052](tasks.md#L242): no independent approval/immutable publication evidence chain. | AUD-030-006, AUD-030-018 |
| RV-05 live cleanup/24-hour observation | UNVERIFIED | [T060](tasks.md#L282): no run-owned live cleanup window. | AUD-030-012, AUD-030-018 |
| RV-06 first-attempt live-fire PR regression | UNVERIFIED | [T069](tasks.md#L328): no linked PR/check/sample diagnostic record. | AUD-030-010, AUD-030-018 |
| RV-07 generated compliance matrix sign-off | UNVERIFIED | [T076](tasks.md#L364): required eval mapping is absent; broader author-signed RAI posture is not compliance-auditor sign-off. | AUD-030-011, AUD-030-018 |
| RV-08 independent 30-day historic audit | UNVERIFIED | [T077](tasks.md#L368): archives are incomplete same-day artifacts; no signature/replay reviewer decision. | AUD-030-011, AUD-030-018 |
| RV-09 real-case de-identification audit | UNVERIFIED | [T081](tasks.md#L396): synthetic-only corpus and regex unit tests are not real-case approval. | AUD-030-006, AUD-030-018 |
| RV-10 telemetry leak/compliance sign-off | UNVERIFIED | [T083](tasks.md#L411): no exporter sentinel suite or independent approval of safe attributes. | AUD-030-017, AUD-030-018 |
| RV-11 WCAG 2.2 AA audit | UNVERIFIED | [T084](tasks.md#L414): skipped heading smoke is not an eval-route accessibility audit. | AUD-030-015, AUD-030-018 |
| RV-12 kill/quota/blob/Cosmos chaos | UNVERIFIED | [T085](tasks.md#L417): fake terminal orphan test does not cover the four exercised faults. | AUD-030-003, AUD-030-012, AUD-030-018 |
| RV-13 security baseline/carve-out review | UNVERIFIED | [T086](tasks.md#L420): no authenticated identity, actual placement/minimisation or independent finding closure record. | AUD-030-004, AUD-030-005, AUD-030-013, AUD-030-017, AUD-030-018 |
| RV-14 five-pillar WAF review | UNVERIFIED | [T087](tasks.md#L423): no eval-specific reliability/security/cost/operations/performance review and should-fix closure record. | AUD-030-013, AUD-030-018 |
| RV-15 full/fast/per-sample performance | UNVERIFIED | [T088](tasks.md#L426): no representative workload timing/cost evidence or calibrated measurement. | AUD-030-009, AUD-030-017, AUD-030-018 |
| RV-16 fresh quickstart/fourth-model exercise | UNVERIFIED | [T089](tasks.md#L429): logs do not show all done bullets or registry-only additional model; defaults are a separate seven-model source list. | AUD-030-014, AUD-030-018 |
| RV-17 cross-artifact consistency analysis | UNVERIFIED | [T090](tasks.md#L432): no local analysis record; current API/hash/language/role/retention/mode conflicts persist. | AUD-030-008, AUD-030-018 |
| RV-18 anonymous live validation/PR audit excerpt | UNVERIFIED | [T095](tasks.md#L454): no nonempty full pipeline plus audit environment excerpt and restricted-label rejection without audience/app. | AUD-030-005, AUD-030-014, AUD-030-018 |

All eight [phase checkpoint claims](tasks.md#L67) are assessed as UNVERIFIED execution/outcome claims:
setup compile/lint, foundation tested, MVP end-to-end, approved immutable v1, bounded self-healing infra,
merge/promotion gate, signed historical audit and safe real-case ingestion. The task-level evidence above
identifies partial source support and blockers for each; checked tasks do not turn checkpoints into passes.

The [six task-format checklist assertions](tasks.md#L546) are accounted for: checkbox/IDs (PARTIAL:
98 unique IDs include three suffixes, not a purely numeric sequence); parallel markers (authored metadata,
actual safe concurrency UNVERIFIED); US markers limited to story phases (IMPLEMENTED formatting); exact
paths/scopes (PARTIAL: many renamed/obsolete paths); single-outcome/verifiable wording (PARTIAL: multiple
tasks combine code, tests and human review); agent/tool annotations (IMPLEMENTED as annotations, not
evidence of consultation/execution). Test-first ordering, foundational-before-stories, independent delivery,
rubber-duck/SME consultation and stop-at-checkpoint process claims are UNVERIFIED. The historical commit
instructions are not executed; no branch or commit was created by this audit.

### Constitution, Assumptions and Scope

The [plan's fifteen constitutional PASS rows](plan.md#L26) are design assertions, assessed individually:

| Clause | Status | Spec-030 Evidence Assessment | Follow-up |
| --- | --- | --- | --- |
| CP-01 Primacy of Life | PARTIAL | Rule checks exist; reliable safety/regression gating and review are not connected. | AUD-030-002, AUD-030-010 |
| CP-02 AEMA/AIIMS | PARTIAL | Domain templates exist; operational SME-approved rubric/authority accuracy unverified. | AUD-030-007, AUD-030-018 |
| CP-03 multi-hazard/multi-agency | PARTIAL | All 13 hazard tags exist; coherent jurisdiction/action coverage and enforced share are incomplete. | AUD-030-007 |
| CP-04 transparency/audit | PARTIAL | Append-only Cosmos emitter exists; mutation coverage, durable complete evidence and replay do not. | AUD-030-011 |
| CP-05 warnings/AWS | PARTIAL | Tone/referral keywords are not full warning-form/directive accuracy or safe refusal semantics. | AUD-030-002, AUD-030-007 |
| CP-06 evacuation framework | PARTIAL | Evacuation hazard exists; five-stage/refusal rubric variants are not demonstrated by random expected actions. | AUD-030-007 |
| CP-07 recovery support | PARTIAL | Remains/crisis tags exist, but four recovery-environment rubric coverage is not established. | AUD-030-007, AUD-030-018 |
| CP-08 cloud platform | PARTIAL | Azure/Bicep/Actions used; active job dispatch/RBAC/private connectivity and required AVM process incomplete. | AUD-030-013 |
| CP-09 NN-1 human in loop | MISSING | Independent dataset/override approval is not enforced by author-generated states or policy strings. | AUD-030-006, AUD-030-010 |
| CP-10 NN-2 sovereignty | PARTIAL | AU defaults are authored; actual approved model carve-out/gateway minimisation/placement unverified. | AUD-030-009, AUD-030-013, AUD-030-017 |
| CP-11 NN-3 privacy | CONFLICT | Viewer case bodies, unverified JWTs and unbound PII-screen flags violate intended safeguards. | AUD-030-004, AUD-030-005, AUD-030-006 |
| CP-12 NN-3 dev exception | PARTIAL | Dev flag conditional exists, but content-boundary, every-event tagging and nondev-startup rules are incomplete. | AUD-030-004, AUD-030-005, AUD-030-013 |
| CP-13 NN-4 interoperability | PARTIAL | FastAPI routes are authored but do not match contract paths/shapes; no emitted OpenAPI parity test. | AUD-030-008, AUD-030-016 |
| CP-14 NN-5 graceful degradation | PARTIAL | Some errors are caught, but failures are hidden and partial/checkpoint/reconcile guarantees not fulfilled. | AUD-030-003, AUD-030-012 |
| CP-15 quality gates | CONFLICT | No path-scoped scorecard-required PR check, What-If create path or independent safety publication gate. | AUD-030-006, AUD-030-010, AUD-030-012 |

All seven [source assumptions](spec.md#L209) remain explicit: an existing model-using component is the
evaluation target (current hard-coded prompt does not bind it); stable Foundry catalog/version addressing
needs actual configuration; synthetic seed is acceptable but does not waive review; governed sensitive
disaster language is in scope; shared platform governance must be reused with ISO42001/NIST/APP mapping;
platform owner owns policy values (not the requester); unspecified operational defaults require recorded
reconciliation, not silent assumptions. These map to AUD-030-002/006/009/010/011/013/014/018.

All five [Out of Scope bullets](spec.md#L219) are preserved: model building/fine-tuning, replacing production
assistant/RAG, live production-traffic monitoring, broader human red teaming, and external dataset distribution.
The additional illegal-to-store-content exclusion is preserved from the assumptions. No remediation
authorises prohibited content, production traffic
capture, deployment, broader platform rewrites or external sharing. Local spec-030 has no additional
persona-count, capstone-outcome, hypothesis-significance or cross-spec amendment imported into this audit.

## Completion and Validation Record

The review's deliverable is this report, not completed remediation. All 18 AUD tasks remain open.
Only read-only HEAD/source/inventory/JSON/archive/text-link checks and report editor diagnostics were
performed. Commands in remediation sections are future-only instructions with prerequisite isolation and,
where relevant, later cloud/cost/human approval. No evaluation, test suite, verification script, build,
application import, model request, server/browser, deployment, installation, branch or commit ran here.

Source/task reconciliation: 98/98 original IDs and exact `[X]` states, including all suffix tasks;
4 IMPLEMENTED, 58 PARTIAL, 6 CONFLICT, 14 MISSING, 1 SUPERSEDED and 15 UNVERIFIED.
All 32 FRs, 12 SCs, 14 numbered acceptance scenarios, six independent story/persona tests and eight edge
cases are represented. Additional ledgers cover nine metric families, 14 nonfunctional obligations,
ten research decisions, 12 entities/five invariants, 21 API contract items, ten clarifications/six amendment
items, 16 source quality checkboxes, 19 operator checkboxes, 12 quickstart items, 18 review obligations and
15 constitutional assertions. Numbered incident steps, phase checkpoints, format/process checklist,
assumptions and scope exclusions are also explicitly assessed above.

Blocking outcomes: verified identity/content authorization, faithful versioned evaluation, approved corpus,
durable complete evidence, policy-bounded lifecycle and fail-closed delivery gates are not established.
Actual model quality, performance/week-long reliability, cloud retention/cleanup, external approvals and
independent historical replay remain UNVERIFIED. These are reported limitations, not invitations to run
future tasks in this static review.

Document checks completed on 2026-09-14: exact source ID/state reconciliation passed; 32 FRs, 12 SCs,
14 scenarios and eight edge cases matched; all supplemental ledger IDs were unique and their source
quality/operator checkbox counts and states matched; all 18 follow-ups were open and all references
resolved. All 591 local Markdown links across 112 distinct text sources existed and their #L anchors
were within file bounds. Report editor diagnostics returned no errors. The initial missing trailing
newline was corrected in this report only; no validator files were created. These checks validate the
document, not product behavior or future remediation completion.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 030 only. Three parallel technical reviews examined evaluation
identity/content boundaries, dead/incomplete scorecard gates, and posture/evidence contracts. The source-completable gate
defect was corrected: each model scorecard must now include all six required gate metrics; a missing metric produces an
explicit failure reason instead of being silently skipped.

Validation: `python -m pytest tests/unit/eval/test_phase5_6_modules.py -q` returned `10 passed`.

Remaining open work includes verified evaluator identity, trace/sample authorization, judge registration, dataset safety
approval, exact reproducible snapshots, cancellation/cleanup, cost caps, durable evidence, UI/CI wiring, deployment,
and human/provider quality evidence.
