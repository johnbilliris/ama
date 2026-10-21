# Spec 031 Static Implementation Audit

## Metadata and Boundaries

- Review date: 2026-09-14.
- Expected and verified HEAD: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`.
- Scope: only the obligations of [spec.md](spec.md#L1), including its local design, contracts, task list, checklists, and review records.
- Contract: [Review Contract](../001-spec-implementation-audit/README.md#L11), read through line 59; [code-review instructions](../../.github/instructions/code-review.instructions.md#L1), read fully.
- Source integrity: read-only `git rev-parse HEAD` matched the expected revision. Initial scoped `git status --porcelain=v1` returned no changes in the reviewed implementation and spec-031 paths.
- Sole writable artifact: this report. No other implementation-review reports were read; no delegation was performed.
- Execution boundary: static source, test assertions, configuration, and artifact inspection only. No product tests, repository scripts/verifiers, builds, imports, installs, browser/server/debug sessions, cloud operations, deployments, or external approvals were executed.
- Evidence rule: an authored artifact or checked task is not proof of a completed test, deployment, performance result, operator setup, or approval. Such outcomes remain UNVERIFIED without attributable evidence.

## Inputs and Method

All 12 original local input files were read completely:

| Input | Purpose |
| --- | --- |
| [spec.md](spec.md#L1) | Five stories, clarification answers, 26 FRs including suffixes, eight SCs, six edges, assumptions and exclusions. |
| [tasks.md](tasks.md#L1) | All 33 original IDs: 32 `[x]`, one `[ ]` (T016), including T009a, T011a and T012a; success conditions and operator/reviewer duties. |
| [plan.md](plan.md#L1) | Scope, performance goals, constitution self-assessment and preserved behavior. |
| [research.md](research.md#L1) | R1-R10 decisions; binding 21-entry R6 deletion list and explicit exclusions. |
| [data-model.md](data-model.md#L1) | Environment, identity, parameter, ADR and state-transition contracts. |
| [quickstart.md](quickstart.md#L1) | Setup, promotion, rollback, rotation, eight smoke tests and troubleshooting. |
| [fr020-recommendations.md](fr020-recommendations.md#L1) | Five-workflow review artifact, three proposals and unfilled dispositions. |
| [requirements checklist](checklists/requirements.md#L1) | All 16 original checked items, including the notes qualifying artifact-specific terminology. |
| [CI contract](contracts/ci-workflow.md#L1) | Events, original quality steps, five behavior rows and three acceptance tests. |
| [CD contract](contracts/cd-workflow.md#L1) | Conditions, ordering, outputs, nine behavior rows and five acceptance tests. |
| [drift contract](contracts/drift-detection.contract.md#L1) | Six behavior rows, matrix, errors, issue creation and four acceptance tests. |
| [credential schema](contracts/azure-credentials.schema.json#L1) | Required fields, types, URI constraints, additional-property policy and example. |

There are no additional local amendment, evidence, or review files in this specification directory.
The directory and its contracts/checklists subdirectories were enumerated before this report was created.
All 25 current workflow YAML files were read fully. Primary paths were followed through azd configuration,
parameter files, selected Bicep resources, seeding, API health, rollback, known-good persistence, drift
parsing, eval polling and relevant test fixtures/discovery. Later specifications were read only at
the explicitly relevant decision/task boundaries, not audited independently.

Required review rules included [detailed review checklists](../../.github/instructions/references/code-review-checklists.md#L1),
[commenting rules](../../.github/instructions/code-commenting.instructions.md#L1),
[Bicep rules](../../.github/instructions/bicep-code-best-practices.instructions.md#L1),
[Bicep policy precedence](../../.github/instructions/bicep-policy-compliance.instructions.md#L1),
and the [constitution](../../.specify/memory/constitution.md#L1). The Python fact-grounded-coding skill
was loaded for static helper/test inspection. No interpreter setup, imports, Pylance execution,
model evaluation, deployment validation, or cloud-policy discovery was performed. External action
implementations, live permissions, secret stores, branch protections, PR approvals, and run histories
were not inspected. SHA comments on pinned actions are authored version labels, not independently
verified release provenance. `rg` was unavailable; bounded read-only `git grep` searches were used
instead, always excluding every implementation-review report.

Statuses are IMPLEMENTED, PARTIAL, MISSING, CONFLICT, UNVERIFIED, and SUPERSEDED as defined by the
review contract. IMPLEMENTED means supported source behavior or an authored artifact only.
Runtime outcomes remain UNVERIFIED. `none` means the original obligation has no checkbox.

## Initial Hypothesis and Check

Hypothesis: the CD entry point preserves the upstream CI commit and environment boundary.
The cheap discriminating check is to compare the event, branch, checkout, and concurrency predicates in
[cd.yml](../../.github/workflows/cd.yml#L19) with [the CD contract](contracts/cd-workflow.md#L7).
The inspected entry point filters to completed `ci` runs on `dev`, `staging`, and `production`,
requires both successful completion and a push event, checks out `workflow_run.head_sha`, and
uses a per-branch concurrency group with cancellation disabled. These source-level predicates are
present. They do not establish correctness of downstream helpers, queue ordering, or a successful deployment.

The first report edit was immediately checked with read-only text assertions for the revision,
local line anchors, and those exact CD predicates, followed by report diagnostics. The checks passed;
report-only newline/indentation diagnostics were corrected and rechecked before further work.

## Scoped Supersession Decisions

| Decision | Supported effect on this audit | Limits |
| --- | --- | --- |
| [Spec 032 auth sequencing](../032-rubric-improvements/spec.md#L14) and [ADR-032](../../docs/corpus/aidr/decisions/adr-032-oidc-supersession.md#L3) | A two-stage OIDC migration is explicitly planned within the simplified branch model. | ADR-032 is still Proposed; approval and seven-day per-environment soaks are UNVERIFIED. Do not infer all FR-007 through FR-010 are retired. |
| [ADR-036-011 sub-decision iii](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L155) | Explicit exception for staging-promotion's OIDC identity, especially its smoke-injection job. | This does not exempt unrelated workflows. The Accepted heading is a repository decision record, not independently confirmed human approval evidence. |
| [Spec 033 T011](../033-maf-adoption/tasks.md#L110) and [Spec 036 T025](../036-foundry-rag-grounding/tasks.md#L97) | Explicit later instructions restore the posture matrix and a Rego control. The corresponding two R6 deletion obligations have narrow supersession. | No authority to restore the ten retired workflows, three composite actions, or pipeline package; no inference that restored controls are fully wired or executed. |
| [Spec 032 CI requirements](../032-rubric-improvements/spec.md#L200), [blocking benchmark](../032-rubric-improvements/spec.md#L285), [SHA pins](../032-rubric-improvements/spec.md#L295), [Spec 036 Windows/matrix tasks](../036-foundry-rag-grounding/tasks.md#L728) | Explicit later additions qualify T013's byte-identical quality-job and current-major-pin expectations. | These additions do not retire branch routing, deployment isolation, required failure behavior, or SC-007 latency evidence. |

No explicit local decision was found retiring the eval PR trigger, dataset push trigger, drift/deploy
coordination, individual FR-020 feedback, or spec-031 acceptance evidence. Relevant source/config,
local spec documents, ADR-031/032/036-011 and bounded decision/onboarding searches were inspected;
an uninspected remote PR could contain further evidence and is not presumed absent.

## Severity-Ordered Findings

### F01 - Critical: Rollback can report success without restoring the deployed services

CD calls rollback with only the environment and resource group, not any known-good revision
([cd.yml](../../.github/workflows/cd.yml#L357)). The helper constructs names such as `staging-api`
([rollback.sh](../../scripts/rollback.sh#L155)), while CD discovers `ca-api-drh-staging` and a
suffix-bearing App Service ([cd.yml](../../.github/workflows/cd.yml#L243)). Discovery suppresses CLI
errors and selects the second active revision without sorting. All empty results are interpreted as
first-run bootstrap and exit zero before health validation ([rollback.sh](../../scripts/rollback.sh#L377)).
Web restoration is also skipped when no deployment package is supplied
([rollback.sh](../../scripts/rollback.sh#L248)). Consequently, the caller can emit `rolled-back` and
skip the critical issue while a staging or production outage remains. This is a source-backed failure
path, not a claim that it occurred in Azure. Follow-up: AUD-031-001.

### F02 - High: Deployment health and summaries can overstate success

[CD health](../../.github/workflows/cd.yml#L230) probes only API and web, accepts 2xx or 3xx,
and disables TLS verification. Its transitive-health comment is contradicted by
[API health](../../apps/api/app/api/health.py#L10): configured variables become `healthy`, with no
network checks and no agents/ingestion checks. Internal agents and headless ingestion are confirmed
in [the template](../../infra/main.bicep#L1118) and [ingestion configuration](../../infra/main.bicep#L1196).
[Final status](../../.github/workflows/cd.yml#L395) tests only the health outcome first: a subsequent
revision/manifest failure can still produce a successful deployment summary. Earlier failures are
not named by step, and checkout failure occurs before TARGET_ENV is populated. Follow-up: AUD-031-002.

### F03 - High: Versioned environment parameters are not wired into the CD provisioning path

[The dev file](../../infra/main.parameters.dev.json#L4) contains the eight R3 values, but
[azd configuration](../../azure.yaml#L8) selects `infra/main` and
[CD](../../.github/workflows/cd.yml#L143) never selects an environment-specific parameter file.
[The default azd parameters](../../infra/main.parameters.json#L4) omit network policy, model SKU,
alert destinations and environment tier. Drift explicitly uses the per-environment files instead
([drift workflow](../../.github/workflows/drift-detection.yml#L46)), so the two paths have different
desired inputs. The claimed non-production scale-to-zero is contradicted by
[fixed API replicas](../../infra/main.bicep#L1099), [agents replicas](../../infra/main.bicep#L1179),
[ingestion replicas](../../infra/main.bicep#L1237), and [fixed B1 web SKU](../../infra/main.bicep#L1258).
T001 also says seven parameters while enumerating eight. No deployment or cost result was inferred.
Follow-up: AUD-031-003.

### F04 - High: The documented bootstrap principal cannot satisfy the template's RBAC writes

[Quickstart setup](quickstart.md#L43) grants the deployment SP only subscription Contributor.
The human operator's broader prerequisite does not transfer to that SP. The shared template creates
unconditional [Azure role assignments](../../infra/main.bicep#L546), plus conditional
[deployer data-plane grants](../../infra/main.bicep#L830). Contributor alone excludes
`Microsoft.Authorization/roleAssignments/write`. The same deployment then invokes a mandatory
[postprovision hook](../../azure.yaml#L14), whose [seed client](../../scripts/seed_loader.py#L185)
uses the deployment identity and propagates Cosmos write failures. A fresh deployment therefore
needs an explicit, least-privilege bootstrap authorization contract beyond the runbook's grant;
actual tenant permissions remain UNVERIFIED. Follow-up: AUD-031-004.

### F05 - High: Drift neither coordinates with deployment nor selects the deployed revision

[Drift's job](../../.github/workflows/drift-detection.yml#L21) has no shared concurrency group or
in-progress deployment check; its checkout uses the dispatch/default ref, not the target environment's
last deployed SHA. [CD's lock](../../.github/workflows/cd.yml#L46) is not shared by drift. Main-only
changes or partially applied deployments can therefore be reported as staging/production drift,
contrary to the explicit overlap edge. Follow-up: AUD-031-005.

### F06 - High: Drift errors are converted into clean-state evidence

[Resource-group lookup](../../.github/workflows/drift-detection.yml#L57) treats every CLI failure,
including denied access, as an absent group with exit zero. What-If merges stderr into JSON;
[the parser](../../.github/workflows/drift-detection.yml#L108) defaults missing changes and jq errors
to `[]`, suppresses diagnostics, then reports no drift. Regex substring filtering can also hide
mutable paths that merely contain a system-property name. An unreadable/malformed response is not
evidence of a clean environment. Follow-up: AUD-031-006.

### F07 - High: Known-good state loses deployed-commit, environment and restoration provenance

[Manifest update](../../.github/workflows/cd.yml#L331) uses `github.sha` and pushes to `github.ref_name`
in a workflow_run context, rather than the checked-out upstream SHA/branch. The token has only
[contents: read](../../.github/workflows/cd.yml#L28); push failure is downgraded to a warning. The
[revision JSON](../../.github/workflows/cd.yml#L319) omits agents/ingest and records web's ARM ID,
not a restorable package. [The helper](../../scripts/web-coverage/known-good.py#L93) accepts a
checked-in trace without binding it to this CI run, skips a missing trace successfully and stores no
environment discriminator. The rollback caller does not consume that manifest. Follow-up: AUD-031-009.

### F08 - High: The eval path no longer gates PRs and can pass without a correlated verdict

[Eval PR workflow](../../.github/workflows/eval-pr-gate.yml#L3) is dispatch-only, but still uses PR
payload fields and attempts a PR comment. It skips Azure evaluation when vars are absent and
[polls the newest execution](../../.github/workflows/eval-pr-gate.yml#L74), ignoring the started
run's identity; timeout/CLI errors can leave status empty, while only literal `Failed` fails the job.
[Dataset publishing](../../.github/workflows/eval-publish-dataset.yml#L3) also lost its documented
push trigger. Its retained, commented Azure block has the right `creds` input, but its API publish
[references an undefined token producer](../../.github/workflows/eval-publish-dataset.yml#L110).
There is no source-backed guarantee that activating that block works. Follow-up: AUD-031-008.

### F09 - High: CI completion ordering can roll an environment back to an older push

[CI](../../.github/workflows/ci.yml#L3) allows concurrent runs. [CD](../../.github/workflows/cd.yml#L37)
accepts each successful push completion and checks out its SHA, with no obsolete-commit or
push-order check. If newer commit B finishes CI and deploys before older A completes CI, A remains
eligible and can overwrite B. A per-environment deployment mutex does not order upstream CI
completion. AT-CD-005 promises commit order; that promise is not encoded. The Actions service's
queue retention/order was not measured. Follow-up: AUD-031-010.

### F10 - Important: Credential diagnostics cover only an empty CD secret

[The CD guard](../../.github/workflows/cd.yml#L84) checks emptiness, not JSON structure or required
fields. Drift and eval have no equivalent environment-naming validation. Native login may reject bad
credentials, but no inspected source guarantees FR-016's exact secret/environment diagnostic or an
expired-secret rotation instruction. [Data-model rules](data-model.md#L81) require UUID v4 while
[the schema](contracts/azure-credentials.schema.json#L15) uses general `uuid` and an all-zero
example. Validation must resolve that contract mismatch rather than silently reject valid Azure IDs.
Follow-up: AUD-031-007.

### F11 - Important: Workflow tests assert retired behavior and are outside CI discovery

[CD tests](../../tests/devops/test_cd_workflow.py#L50) demand `main`, OIDC and `deploy-staging`;
[drift tests](../../tests/devops/test_drift_detection.py#L34) still demand OIDC and only check
membership, not exact matrix equality. [Rollback tests](../../tests/devops/test_rollback_script.py#L62)
look for exit-code strings. [Parameter tests](../../tests/devops/test_parameter_files.py#L34) omit
the new dev file and azd selection. [CI's test command](../../.github/workflows/ci.yml#L133) selects
contract/integration paths, not devops or the root unit tier. The YAML fixtures correctly normalize
`on` ([conftest](../../tests/devops/conftest.py#L69)); parser quirks do not explain the stale assertions.
These are source contradictions, not reported pytest failures. Follow-up: AUD-031-011.

### F12 - Important: The rotation procedure depends on a credential file setup tells operators to delete

[Setup](quickstart.md#L73) deletes the local JSON credentials. [Rotation](quickstart.md#L135)
subsequently reads that same file twice, without a reconstruction or supported secret-retrieval path.
It then pipes JSON while specifying `--body -` instead of unambiguously passing the JSON on stdin;
the CLI body argument must not become a literal hyphen. Old-key revocation is only commented out.
A claimed 90-day rotation process is not operationally demonstrated. Follow-up: AUD-031-012.

### F13 - Important: The remaining-workflow review and global auth claim are stale

[The review record](fr020-recommendations.md#L7) covers five workflows; 25 exist. The narrow
staging-promotion exception is explicit, but [help snapshot](../../.github/workflows/help-snapshot.yml#L25)
still binds `prod`, reads a legacy client ID, and has no login. Its current
[alias helper](../../apps/ingest-runner/src/help_snapshot/alias_swinger.py#L22) only writes a local
file, so it is not proof of a working Azure publication path. [DORA](../../.github/workflows/dora-metrics.yml#L15)
uses a connection string without an environment binding. Other workflows retain unused `id-token`
permissions; cosign's genuine need is distinct. The original blanket zero-triplet/one-secret claim
requires scoped reconciliation, not removal of an explicitly approved OIDC flow. Follow-up: AUD-031-013.

### F14 - Important: The ADR exists, but onboarding and governance links are broken or misleading

[ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L1) is authored and has a
named [owner/contact](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L118).
[README](../../README.md#L368) still points to its old location; the relocated ADR's
[three spec/runbook/schema backlinks](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L124)
resolve under `docs/specs`, not the repository's `specs`. The spec has no direct link to this ADR.
The [architecture page](../../docs/architecture/deployment/cicd-pipeline.md#L21) describes
What-If/manual promotion stages that CD does not contain, and
[the gate matrix](../../docs/ci-cd/progressive-delivery.md#L14) claims disconnected/manual/disabled
checks and metric-triggered rollback. Historical references and restored controls must be distinguished
from live dependencies; T012's literal global-zero claim is not satisfied. Follow-up: AUD-031-014.

### F15 - Important: Recommendation defaults bypass the required individual feedback boundary

[FR-020](spec.md#L171) and [T028](tasks.md#L272) require separate accept/reject/modify feedback
before action. The [review artifact](fr020-recommendations.md#L3) instead activates defaults unless
overridden, while [all dispositions](fr020-recommendations.md#L82) remain awaiting the maintainer.
Three structured proposals exist; three explicit decisions, accountable follow-ups, or three
separate review interactions are not evidenced. Later implementation of similar controls does not
retroactively supply those approvals. Follow-up: AUD-031-015.

### F16 - Important: Checked operator, review and performance tasks have no attributable local run evidence

[T012a](tasks.md#L120), [operator tasks](tasks.md#L189), and [T029](tasks.md#L281) require What-If,
environment/identity setup, eight smoke results and the explicit missing-secret experiment.
The local inputs contain instructions and checkmarks, not corresponding raw outputs, run IDs,
reviewer confirmations or baseline/candidate timings. [The plan](plan.md#L41) caps CD at 20 minutes;
[current YAML](../../.github/workflows/cd.yml#L41) allows 60 and comments on 25-35 minute bootstrap.
Neither the timeout nor the comment measures SC-007's push-to-completion time. Outcomes and
approval execution remain UNVERIFIED, not failed-by-assumption. Follow-up: AUD-031-016.

## Unchecked Follow-Up Tasks

- [ ] AUD-031-001 Make staging and production rollback restore verified deployment revisions

**Affected obligations:** FR-015, FR-015a; T014, T029; US1 acceptance 2; AT-CD-002;
production force-push edge; CD contract steps 9-14 and staging/production failure scenarios.

**Expected versus observed / impact:** A health failure must restore the correct environment's
known-good services, verify recovery, and open a critical issue if restoration fails. The current
name mismatch, swallowed discovery errors, absent revision inputs, and unconditional bootstrap
success can leave the failed release active without escalation. Existing tests assert only strings
such as `bootstrap` and `exit 0`, not this behavior
([test_rollback_script.py](../../tests/devops/test_rollback_script.py#L127)).

**Developer directions:** Fix the contract between
[cd.yml](../../.github/workflows/cd.yml#L291) and
[rollback.sh](../../scripts/rollback.sh#L151). Resolve resource identities from the same deployment
outputs/tags as provisioning; distinguish the `ingestion` service key from its `ingest` resource
suffix. Supply environment-bound prior revisions and a retrievable App Service package, not its
ARM resource ID. Distinguish a confirmed first deployment from authorization, network, missing
resource, and parse errors. Sort revision history and handle inactive known-good revisions.
Verify all restored services through topology-appropriate health checks before success. Preserve
the dev no-rollback/no-issue boundary, existing CLI compatibility where practical, and nonzero
rollback exit semantics consumed by the critical-issue condition. Coordinate revision persistence
with the existing known-good helper; do not broaden workflow token permissions as a shortcut.

**Tester directions:** Extend the existing
[rollback tests](../../tests/devops/test_rollback_script.py#L1) and
[CD workflow tests](../../tests/devops/test_cd_workflow.py#L1) with an isolated fake CLI, not live
Azure. Positive fixtures: current `ca-*-drh-staging` names, suffix-bearing web name, unsorted
history containing an inactive known-good revision, and a real test ZIP. Assert exact resource
group/revision arguments, restored package, post-restore health, and success only after restoration.
Negative fixtures: CLI 403, invalid JSON, missing target resource, failed activation, and failed
post-rollback health; assert nonzero exit and critical escalation. Edge fixtures: confirmed empty
initial history, one prior revision, force-push SHA, and dev; assert bootstrap is explicit and dev
never invokes rollback or issue creation. Future command:
`pytest tests/devops/test_rollback_script.py tests/devops/test_cd_workflow.py -q`, after updating
stale YAML expectations, with pytest, PyYAML, Bash, and fake CLI fixtures available.
Expected: all assertions pass without network access.

**Completion criteria:** A failed lookup cannot be reported as recovery; staging and production
restore and verify the intended prior release or expose a failed rollback and critical issue;
dev remains unchanged. An attributable later controlled smoke run is still required for runtime
acceptance. No remediation or future validation command was executed in this audit.

- [ ] AUD-031-002 Make health gating and deployment summaries reflect the whole release

**Affected obligations:** FR-015, FR-015a, FR-015b; T014, T029; CD contract steps 9-14;
US1 deployment scenarios; SC-001 and SC-005.

**Expected versus observed / impact:** See F02. HTTP success from an environment-variable-only
endpoint does not prove four-service health; a successful probe does not make later failed steps
successful. Early failures also need an environment and failing-step summary.

**Developer directions:** Own [CD health/status](../../.github/workflows/cd.yml#L230), with the
[API health owner](../../apps/api/app/api/health.py#L19) only where required. Define a bounded,
topology-aware release-health contract for public API/web, internal agents and headless ingestion.
Do not expose internal ingress just to satisfy a public curl. Require authenticated TLS and an
explicit acceptable body/status policy; assign step IDs and derive final status from all required
steps, including post-health manifest work. Resolve environment from the event even after checkout
failure. Preserve dev's no-rollback/no-issue behavior; only call rollback on its documented condition.
Coordinate with AUD-031-001 and AUD-031-009.

**Tester directions:** Extend [CD tests](../../tests/devops/test_cd_workflow.py#L1) and
[rollback tests](../../tests/devops/test_rollback_script.py#L1). Positive: all four deployment
components ready and all required steps successful, assert one success summary. Negative: API 200
with agents down, web redirect-to-login, invalid TLS, or manifest failure after green probes, assert
no success status. Edge: headless worker readiness, first provision failure and checkout failure,
assert correct environment/failed step/rollback-not-attempted fields; dev emits no issue.
Future command: `pytest tests/devops/test_cd_workflow.py tests/devops/test_rollback_script.py -q`.
Prerequisites: updated YAML tests and isolated HTTP/CLI/step-result fixtures; no network needed.

**Completion criteria:** Every required component and step contributes to the verdict; failed runs
cannot say deployed successfully; failure summaries identify environment, step and rollback outcome.

---

- [ ] AUD-031-003 Wire reviewed environment parameters and reconcile the dev sizing contract

**Affected obligations:** FR-004, FR-004a; T001, T014, T024, T025, T029; SC-001, SC-005;
R3, data-model entities 5/6, CD/drift provisioning contracts.

**Expected versus observed / impact:** See F03. The authored file matches the eight R3 values but
is disconnected from the inspected CD invocation; drift and deploy can compare different intent.
The claimed lower-cost dev configuration is not expressed by the fixed replica/SKU settings.

**Developer directions:** Own [azd configuration](../../azure.yaml#L8),
[CD environment setup](../../.github/workflows/cd.yml#L143),
[default parameters](../../infra/main.parameters.json#L4),
[per-environment parameters](../../infra/main.parameters.dev.json#L4) and relevant
[Bicep knobs](../../infra/main.bicep#L1099). Explicitly select the reviewed environment input and
map production to the template's supported tier vocabulary. Carry the same parameter digest into
drift. Keep Australia East and current governance constraints; do not weaken policy to implement
the obsolete scale-to-zero rationale. Obtain a scoped decision for cheaper permitted SKUs/replicas
or revise the claim. Resolve seven-versus-eight wording through the original-spec owner in a later
authorized change. Preserve staging/production settings and all current services.

**Tester directions:** Extend [parameter tests](../../tests/devops/test_parameter_files.py#L1) and
[fixtures](../../tests/devops/conftest.py#L49). Positive: dev, staging and production each resolve
their own environmentName, region, SKU, network flags and recipient values. Negative: wrong-env
file, unknown branch, absent parameter file or prod mapped to dev tier, assert refusal before deploy.
Edge: a harmless dev-only sentinel must reach the selected parameter set and not the other two;
assert identical deploy/drift digests. Future command:
`pytest tests/devops/test_parameter_files.py tests/devops/test_cd_workflow.py tests/devops/test_drift_detection.py -q`.
Prerequisites: deterministic offline parameter-selection fixtures and agreed sizing decision.

**Completion criteria:** The version-controlled per-environment file is demonstrably consumed;
deploy/drift intent agrees and dev cost claims match permitted source settings. Runtime/cost/What-If
acceptance remains subject to AUD-031-016.

---

- [ ] AUD-031-004 Define a least-privilege bootstrap and seed authorization path

**Affected obligations:** T021, T022, T012a, T014, T029; FR-004a, FR-007; SC-001, SC-005;
quickstart prerequisites and one-secret first-deployment scenario.

**Expected versus observed / impact:** See F04. Human Owner access and an SP granted Contributor
are not equivalent. Fresh role-assignment writes and postprovision data writes need explicit authority.

**Developer directions:** Own [quickstart setup](quickstart.md#L35),
[RBAC resource declarations](../../infra/main.bicep#L535),
[deployer Cosmos grants](../../infra/main.bicep#L830), and
[seeding](../../scripts/seed-database.sh#L44). Document a separately approved bootstrap role with
necessary role-assignment authority, or provision role assignments out of band before lowering the
deployment role. Do not solve this by unconditionally granting Owner. Ensure the authenticated SP's
object ID/type and data-plane grants reach the selected parameters, including after rotation.
Keep credentials per environment and fail clearly before partial mutation when prerequisites fail.
Depends on AUD-031-003; no cloud grants are authorized by this report.

**Tester directions:** Use [parameter tests](../../tests/devops/test_parameter_files.py#L1) and
[seed-loader tests](../../tests/unit/test_seed_loader.py#L1). Positive: authorized mock principal
with role-assignment and Cosmos/Blob rights reaches successful seeding. Negative: Contributor-only,
wrong object ID, and denied data-plane writes, assert actionable preflight/error and nonzero outcome.
Edge: existing resources, empty principal ID and newly rotated identity, assert no cross-env grant
and no silent seed success. Future command:
`pytest tests/devops/test_parameter_files.py tests/unit/test_seed_loader.py -q`.
Prerequisites: reviewed bootstrap policy and offline role/SDK fixtures; later live verification must
use an explicitly approved disposable environment.

**Completion criteria:** A new operator can understand and satisfy the actual authorization contract
without guessing extra secrets or broad privileges; denied bootstrap/seed operations remain failures.

---

- [ ] AUD-031-005 Coordinate drift with deployments and compare the deployed environment revision

**Affected obligations:** FR-005, FR-011, FR-012; T014, T018, T024, T029;
drift/deploy overlap edge; US3 acceptance 1-3; AT-DD-001 through AT-DD-003.

**Expected versus observed / impact:** See F05. Drift must not observe a partially deployed stack
or compare production to an unrelated main/dispatch revision.

**Developer directions:** Own [drift job/checkout](../../.github/workflows/drift-detection.yml#L21)
and [CD lock](../../.github/workflows/cd.yml#L46). Introduce shared per-environment serialization
or an explicit in-flight pending/no-op protocol with race protection. Select the last successfully
deployed SHA and parameter digest for that environment, not merely its current branch head.
Coordinate with AUD-031-003/009/010. Retain both staging and production, fail-fast false, schedule,
manual dispatch, and no dev choice; do not cancel an in-flight deployment.

**Tester directions:** Extend [drift tests](../../tests/devops/test_drift_detection.py#L53) and
[CD tests](../../tests/devops/test_cd_workflow.py#L75). Positive: stable deployed staging revision
is compared once. Negative: main ahead of staging or deployment midway through apply, assert no
false drift issue and explicit pending/skip output. Edge: simultaneous staging/prod runs and a
manual dispatch from dev, assert independent environment locks and exactly two allowed targets.
Future command: `pytest tests/devops/test_drift_detection.py tests/devops/test_cd_workflow.py -q`.
Prerequisites: offline deployment-record and event-scheduler fixtures.

**Completion criteria:** Drift reads a stable, environment-correct desired state and cannot race
an apply or suppress legitimate post-deploy drift; overlap runtime evidence is captured later.

---

- [ ] AUD-031-006 Make drift classification fail closed on lookup and parsing errors

**Affected obligations:** T018, T024, T029; US3 acceptance 3; AT-DD-003;
drift contract no-drift, missing-RG, one-env-failure and issue behavior; FR-015 visibility intent.

**Expected versus observed / impact:** See F06. A confirmed nonexistent RG is an allowed skip;
403, transport failure, malformed JSON and unsupported response shapes are not clean-state evidence.

**Developer directions:** Own [What-If capture](../../.github/workflows/drift-detection.yml#L41)
and [parsing/report conditions](../../.github/workflows/drift-detection.yml#L86). Separate stdout
and stderr; preserve useful diagnostics without credentials. Classify a genuine not-found separately
from other CLI failures. Require a supported changes envelope and validate change/delta shape.
Replace catch-all `[]` fallbacks with failure outputs; anchor ignore rules to known property paths.
Only report clean after a successful, valid analysis. Preserve fail-fast false and issue labels.

**Tester directions:** Extend [drift tests](../../tests/devops/test_drift_detection.py#L1) using
isolated command and JSON fixtures. Positive: empty changes and ignored-only system deltas produce
zero issues; real Create/Delete/Modify in staging produces exactly one staging issue. Negative: 403,
429, invalid JSON and `{}` produce nonzero status, no clean summary, and no fabricated drift issue.
Edge: stderr warning with valid stdout, genuine RG 404, and mutable
`properties.provisioningStateOverride`, assert correct classification and no substring suppression.
Future command: `pytest tests/devops/test_drift_detection.py -q`.
Prerequisites: updated fixture runner with fake az/gh and the parser under test, not a copied algorithm.

**Completion criteria:** Analysis errors cannot become no-drift evidence; missing-group behavior and
independent matrix execution remain intact.

---

- [ ] AUD-031-007 Validate credential payloads and emit environment-specific authentication guidance

**Affected obligations:** FR-007, FR-008, FR-010, FR-016; T017, T018, T019, T021, T022, T029;
US2 acceptance 1/4; expired-secret edge; credential schema and data-model rules.

**Expected versus observed / impact:** See F10. Empty CD credentials have a useful error, but
malformed/incomplete payloads and expired secrets lack a source-backed uniform diagnostic contract.

**Developer directions:** Own [CD validation/login](../../.github/workflows/cd.yml#L84),
[drift login](../../.github/workflows/drift-detection.yml#L36),
[eval login](../../.github/workflows/eval-pr-gate.yml#L55), and the
[credential schema](contracts/azure-credentials.schema.json#L6). Validate securely before Azure
side effects; name `AZURE_CREDENTIALS`, target environment and corrective action without printing
the payload or secret-derived values. Resolve general-UUID versus v4 policy with the contract owner;
do not enforce an incompatible Azure identifier restriction silently. Keep native auth failure
nonzero and add safe rotation guidance for expiry. Respect the explicit OIDC exception in AUD-031-013.

**Tester directions:** Extend [CD tests](../../tests/devops/test_cd_workflow.py#L1) and
[drift tests](../../tests/devops/test_drift_detection.py#L1); add eval cases in the existing devops
test package (new test module, if chosen, is proposed, not existing evidence). Positive: valid
canonical JSON and optional HTTPS endpoints accepted. Negative: blank, invalid JSON, missing or
empty clientSecret, wrong field type and expired-auth response; assert nonzero exit before provision
and both secret/environment names, with no raw credential bytes in logs. Edge: extra keys and
non-v4 valid Azure IDs follow the resolved schema policy. Future command: `pytest tests/devops -q`.
Prerequisites: stale devops assertions repaired and isolated login/JSON fixtures.

**Completion criteria:** All non-exempt Azure entry points enforce the same actionable, non-leaking
contract; live secret presence/expiry and the FR-016 smoke outcome remain UNVERIFIED until recorded.

---

- [ ] AUD-031-008 Restore or explicitly retire eval triggers and require a correlated terminal verdict

**Affected obligations:** FR-019, FR-019a, FR-019b; T019, T020, T027, T029;
clarification Q5, non-deploy Azure edge and data-model workflow triggers.

**Expected versus observed / impact:** See F08. A manual run without a PR, an unconfigured runner,
a timed-out poll, or a different execution's result cannot establish a passing PR evaluation.

**Developer directions:** Own [eval PR workflow](../../.github/workflows/eval-pr-gate.yml#L3) and
[dataset workflow](../../.github/workflows/eval-publish-dataset.yml#L3). Restore specified triggers
or secure an explicit scoped retirement decision; do not silently change the contract. Retain dev
environment auth, capture the actual execution ID from job start and poll only that execution.
Fail missing required config, CLI errors, timeout, cancelled/unknown states and Failed distinctly.
Require a usable PR identity before commenting. Keep dataset Azure publication dormant; correct
its token-producing step and API audience contract before activation, without adding split secrets.
Coordinate auth validation with AUD-031-007 and test discovery with AUD-031-011.

**Tester directions:** Use the existing [devops fixtures](../../tests/devops/conftest.py#L18) and
devops package for isolated event/az/gh fixtures. Positive: path-matching main PR and its own
Succeeded execution yield one verdict/comment. Negative: Failed, no config, 60 polls without a
terminal state, CLI error, or a newer unrelated success must not pass. Edge: manual dispatch with
no PR, fork PR with no secret and concurrent PRs; assert no inappropriate secret use/comment and
no cross-run verdict. Dataset fixture: uncomment in memory and assert valid environment/login/token
references without publishing. Future commands: `pytest tests/devops -q` and
`actionlint .github/workflows/eval-pr-gate.yml .github/workflows/eval-publish-dataset.yml`.
Prerequisites: proposed test cases in the existing package, fake commands and actionlint installed
out of band; no Azure job invocation during offline tests.

**Completion criteria:** PR evaluation is genuinely invoked or explicitly retired, every required
run has its own fail-closed verdict, and the dormant publisher's activation instructions are coherent.

---

- [ ] AUD-031-009 Bind known-good records to the deployed SHA, environment and restorable artifacts

**Affected obligations:** FR-003a, FR-004, FR-015, FR-015a; T014, T029;
CD contract revision outputs and rollback behavior; force-push and cross-environment edges.

**Expected versus observed / impact:** See F07. A default-branch SHA, stale trace, global manifest
and ARM web ID cannot safely identify the environment's last recoverable release.

**Developer directions:** Own [revision/persistence steps](../../.github/workflows/cd.yml#L291)
and [known-good helper](../../scripts/web-coverage/known-good.py#L93). Bind commit to
`workflow_run.head_sha`, trace to the triggering CI run/commit, and records to target environment.
Persist all four service identities and immutable restore references in an approved store/artifact.
Fail missing/stale trace or invalid revision input where required; never silently publish incomplete
known-good state. Do not push a detached environment checkout to default-branch context; choose an
explicit least-privilege persistence mechanism rather than simply widening contents permission.
Feed validated previous records to AUD-031-001 and deployed-intent records to AUD-031-005.

**Tester directions:** Extend [CD tests](../../tests/devops/test_cd_workflow.py#L1) with isolated
helper I/O/trace/git fixtures. Positive: distinct default SHA A and deployed SHA B record B, correct
environment and four restore references. Negative: trace from A, absent trace, malformed revisions
or denied persistence, assert failure and no success manifest. Edge: simultaneous staging/prod,
missing prior release and force-push, assert isolation and no write to main. Future command:
`pytest tests/devops/test_cd_workflow.py -q`.
Prerequisites: injectable temporary manifest/audit paths, fake GitHub artifacts and git transport;
no live push or helper execution against repository evidence.

**Completion criteria:** A successful release has an attributable, retrievable environment-specific
restore record; persistence failure is visible; rollback consumes rather than merely mentions it.

---

- [ ] AUD-031-010 Encode same-environment release ordering across out-of-order CI completions

**Affected obligations:** FR-005; T014, T029; US1 acceptance 5; AT-CD-005;
R9, rapid-push edge and CD contract commit-order guarantee.

**Expected versus observed / impact:** See F09. A deployment mutex prevents overlap but does not
prevent an older successful CI completion from deploying over a newer release.

**Developer directions:** Own [CD eligibility/concurrency](../../.github/workflows/cd.yml#L37)
and its relationship to [CI events](../../.github/workflows/ci.yml#L3). Define an explicit
push-order queue or obtain a scoped decision permitting stale-release skips. Preserve no in-flight
cancellation and cross-environment independence; a silent latest-only policy would itself alter
the original every-run/queue contract. Handle re-runs, force-push ancestry and missing SHA explicitly.
Coordinate with the deployed-SHA record in AUD-031-009 and drift serialization in AUD-031-005.

**Tester directions:** Extend [CD tests](../../tests/devops/test_cd_workflow.py#L75) with a fake
event scheduler. Positive: A then B finishing normally deploy serially. Negative: B's CI finishes
before A, assert final deployed SHA cannot regress from B to A. Edge: three rapid pushes, duplicate
completion/re-run, force-push with non-ancestor SHA, and simultaneous dev/staging; assert the
approved queue/skip policy and no cross-env serialization. Future command:
`pytest tests/devops/test_cd_workflow.py -q`.
Prerequisites: approved ordering policy and event-ledger fixtures; later GitHub run observation is
required to establish service-level pending-run behavior.

**Completion criteria:** Actual release order matches the documented policy; no older completion
can silently overwrite a newer deployment and no in-flight apply is cancelled.

---

- [ ] AUD-031-011 Replace stale pipeline assertions and wire meaningful regression discovery

**Affected obligations:** T012, T013, T014, T017, T018, T019, T023, T024, T025, T027, T029;
FR-001 through FR-020 validation; all CI/CD/drift acceptance tests and constitution quality review.

**Expected versus observed / impact:** See F11. File names and strings do not exercise event
eligibility, parameter selection, process exit behavior, auth errors or rollback. Selected CI tests
omit the existing devops package; source-only inspection cannot establish a passing baseline.

**Developer directions:** Own [devops fixtures](../../tests/devops/conftest.py#L69), the existing
CD/drift/rollback/parameter test modules and [CI selection](../../.github/workflows/ci.yml#L133).
Update retired expectations to the resolved contracts, preserving YAML `on` normalization. Add
real branch/condition evaluation and isolated subprocess fixtures around actual helpers; do not
copy implementation algorithms into tests or weaken assertions to text existence. Wire the devops
tier into a blocking CI path and accurately document which unit suites are collected. Preserve
explicit later CI gates instead of reverting quality steps to spec-031's historical byte sequence.
An actionlint gate remains subject to AUD-031-015's feedback boundary.

**Tester directions:** Positive: all canonical branches, exact drift set, pinned upstream SHA,
dev rollback exclusions and valid helper exits. Negative: PR/failed-CI/main deployment attempt,
extra dev matrix entry, legacy auth without exception and each fault fixture from AUD-031-001/006/008.
Edge: YAML boolean key normalization, reordered matrix entries, skipped upstream job and helper
nonzero exit. Assert exact values and that mutating each guard makes its test fail. Future commands:
`pytest tests/devops --collect-only -q`, then `pytest tests/devops -q`;
`actionlint .github/workflows/ci.yml .github/workflows/cd.yml .github/workflows/drift-detection.yml`.
Prerequisites: dependencies already installed and offline-safe fixtures; do not run the old suite
as evidence of the new contract without reviewing its assertions first.

**Completion criteria:** Correct contract cases are discovered by CI, negative controls fail for the
intended reason, and an attributable later test result establishes the repaired baseline.

---

- [ ] AUD-031-012 Make manual secret rotation work after secure setup cleanup

**Affected obligations:** R10; T021, T022, T026, T029, T030; FR-017;
US2 credential lifecycle and expired-secret edge; ADR-031 rotation mitigation.

**Expected versus observed / impact:** See F12. The operator must be able to rotate without
retaining plaintext credentials that setup requires deleting or accidentally writing a non-JSON secret.

**Developer directions:** Own [rotation instructions](quickstart.md#L129) and
[ADR consequence a](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L60).
Retain only nonsecret client/tenant/subscription metadata in a documented location; reconstruct the
new JSON securely from the new secret instead of reading the deleted file. Use a verified stdin
or body form, schema-check without logging credentials, verify the new identity, revoke the old
key and remove temporary material. Define failure recovery and overlap bounds; preserve the
90-day manual cadence and the later OIDC migration boundary. No real rotation is authorized here.

**Tester directions:** Use [devops tests](../../tests/devops/test_parameter_files.py#L1) as the
existing home for an offline runbook fixture or a proposed adjacent test in the same package.
Positive: empty workstation with retained nonsecret metadata receives a generated valid JSON body.
Negative: deleted source file, failed reset or failed secret update must stop without revoking the
working key. Edge: retry after partial rotation and key-revocation failure, assert explicit operator
action, no secret in logs, and no literal `-` secret value. Future command: `pytest tests/devops -q`.
Prerequisites: fake az/gh, disposable fixture values and reviewed CLI argument semantics.

**Completion criteria:** Setup and rotation are internally consistent, revocation/cleanup are
explicit, and a later controlled rotation transcript contains no secret material.

---

- [ ] AUD-031-013 Reconcile the full workflow inventory with narrow authentication exceptions

**Affected obligations:** FR-008, FR-009, FR-010, FR-019; T017, T018, T019, T020, T023, T027;
SC-002; US2 acceptance 1-3; data-model workflow/environment inventory.

**Expected versus observed / impact:** See F13 and the workflow table below. Five historic rows
cannot attest the current 25 workflows. Unused token grants, stale client-ID references and a
local-only publisher differ from the claimed uniform, relevant Azure workflow set.

**Developer directions:** Review all existing workflow files against actual invoked code. Update
the maintained inventory with purpose, event, env, auth, permission rationale, dependencies and
version-pin exceptions. Preserve [staging-promotion's explicit decision](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L155)
and cosign's legitimate OIDC requirement; do not force those paths back to long-lived secrets.
Resolve [help snapshot's prod/client-ID configuration](../../.github/workflows/help-snapshot.yml#L25)
and [local-only alias implementation](../../apps/ingest-runner/src/help_snapshot/alias_swinger.py#L22)
through its owner, clearly marking it non-operational until integrated. Classify telemetry-only
connection strings separately and decide required environment binding. Remove genuinely unused
permissions. Do not declare the Proposed ADR-032 rollout complete without its approval/soak evidence.

**Tester directions:** Extend the [devops package](../../tests/devops/conftest.py#L18) with an
inventory assertion over the actual workflow directory. Positive: each Azure login is env-bound,
uses the agreed auth policy, or matches one exact documented exception. Negative: new undeclared
login, legacy secret in a non-exempt workflow, `prod` alias without mapping, and unused id-token
grant must fail. Edge: commented publisher, telemetry-only job and cosign CLI consumer must be
classified correctly, not rejected by a raw substring search. Future commands:
`pytest tests/devops -q` and `actionlint .github/workflows/*.yml`.
Prerequisites: reviewed exception registry and offline test fixtures; version provenance can be
checked later without equating a comment to a verified action release.

**Completion criteria:** All current workflows have attributable static review notes and an explicit
policy disposition; no blanket supersession or unsupported runtime-publication claim remains.

---

- [ ] AUD-031-014 Repair relocated ADR links and reconcile live pipeline documentation with retirement

**Affected obligations:** FR-013, FR-014, FR-017, FR-018; T002, T009, T009a, T011, T011a,
T012, T025, T026, T030; SC-003, SC-006; US4/US5; R6 and onboarding conventions.

**Expected versus observed / impact:** See F14. The ADR is present but not reachable through its
original links. Literal zero-reference checks conflict with historical annotations and explicit
later restoration of two paths; live diagrams/gate prose also describe unconnected controls.

**Developer directions:** Own [README onboarding](../../README.md#L368),
[relocated ADR links](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L124),
[pipeline documentation](../../docs/architecture/deployment/cicd-pipeline.md#L21) and the maintained
retirement manifest. Correct relative backlinks and add the required spec-to-ADR link in a later
authorized docs change. Keep the 19 retired R6 paths absent and preserve expressly restored
posture/Rego owners; do not mass-delete historical references or new controls. Distinguish removed
CODEOWNERS rules from explanatory comments. Label authored diagrams as design unless their
event/job/gate chain matches source. Retain the valid CD ownership rule and operator rollback path.

**Tester directions:** Existing [CD/parameter tests](../../tests/devops/test_cd_workflow.py#L1)
can host a scoped link/retirement assertion; a new docs test, if needed, is proposed. Positive:
README to ADR to spec/runbook/schema resolves from each file's actual directory. Negative:
one-directory-short ADR backlink and a revived retired workflow fail. Edge: authorized posture
matrix/Rego restoration and historical ADR comments are accepted only with explicit decision
references; assert no active `uses`/workflow_run/package dependency on deleted entries.
Future commands: `pytest tests/devops -q` and
`git grep -n -E 'spec029|tools/pipeline|setup-oidc-azure' -- .github/workflows`.
Prerequisites: exact retirement/exception list and a read-only local Markdown link checker; zero
matches is expected for active dependency expressions, not every historical word in the repo.

**Completion criteria:** Governance navigation works, live onboarding matches the actual pipeline,
and retirement assertions distinguish explicit supersession from genuine stale dependencies.

---

- [ ] AUD-031-015 Obtain and record individual recommendation dispositions before implementation

**Affected obligations:** FR-020; T027, T028; SC-008; US5 governance review;
R7/R10 follow-ups and the recommendation record's approval boundary.

**Expected versus observed / impact:** See F15. Authored recommendations are supported; blank
dispositions plus automatic defaults do not meet individual consent before action.

**Developer directions:** The maintainer/review owner must resolve each of A, B and C separately
as accept, reject or modify, with identity/date, rationale and an owner or existing issue for any
accepted/modified work. Reconcile proposals with explicitly added later controls so approval is
for current work, not a duplicated historical plan. Remove default-before-feedback semantics from
the maintained review artifact in an authorized follow-up. Keep ADR-032 Proposed until its own
approval conditions are met; do not treat this audit or agent-authored decisions as human sign-off.
No remote approval requests or remediation actions were performed here.

**Tester/reviewer directions:** Use [the existing disposition table](fr020-recommendations.md#L82)
and scoped text/PR-evidence checks. Positive: three distinct attributable decisions and follow-up
owners resolve. Negative: one blanket approval, blank identity, default acceptance or missing
modified scope is rejected. Edge: rejected proposal has a reason and no implementation task;
already-implemented later control needs a retrospective factual note, not fabricated prior consent.
Future command: `git diff --check -- specs/031-simplify-cicd-pipeline/fr020-recommendations.md`;
then inspect the three referenced decision records. Prerequisites: explicit permission to contact
the maintainer and authentic records, obtained outside this audit.

**Completion criteria:** Three separate feedback decisions are discoverable and any future action
respects them; the authored proposal count is not confused with performed-review evidence.

---

- [ ] AUD-031-016 Capture attributable acceptance evidence and reconcile deployment latency targets

**Affected obligations:** T012a, T015, T016, T021, T022, T023, T025, T026, T027, T028, T029;
SC-001 through SC-008; all runtime acceptance/independent tests, operator setup and plan performance goals.

**Expected versus observed / impact:** See F16. Checkmarks, authored diagrams, a timeout value,
and unrelated passing suites cannot establish the exact revision's deployments, safeguards,
approvals or performance. T016 remains explicitly deferred and is not silently a deploy blocker.

**Developer/review directions:** After technical repairs and explicit operator authorization,
capture redacted evidence for branches, environment-scoped secrets, SP scopes, CODEOWNERS/protection
settings, dev What-If and its human review, each smoke test, all three env deployments, negative
auth/CI/PR cases and overlap/ordering/rollback behavior. Record run ID, tested SHA, env, command,
exit/result, timestamp and reviewer where applicable. Measure comparable previous-pipeline and
candidate push-to-complete timings, including CI and queue time; distinguish bootstrap from warm
deploys. Resolve the plan's 20-minute cap versus YAML's 60-minute timeout explicitly. Do not change
original checked states or create fabricated evidence during this audit. Coordinate every preceding
AUD task and leave unmet outcomes visibly UNVERIFIED.

**Tester directions:** Follow [the eight smoke rows](quickstart.md#L152) and
[T029's extra FR-016 case](tasks.md#L281) only in an approved isolated environment. Positive:
each allowed push deploys only its target and records elapsed time. Negative: failed CI, PR event,
missing/malformed/expired auth, health failure and failed rollback produce their exact required
non-deploy/error/issue outcomes. Edge: fast overlapping pushes, force-push, first deploy and concurrent
drift; record both expected and observed results and secret restoration without exposing values.
Future read-only evidence commands: `gh run list --workflow ci.yml --branch dev --limit 20`,
`gh run list --workflow cd.yml --branch dev --limit 20`, and `gh run view <run-id> --log`.
Compare workflow_run head_branch/head_sha metadata explicitly; branch filtering alone may describe
the default-branch workflow context. The actual smoke/What-If commands are the existing runbook and
T012a instructions, not commands executed here.

**Completion criteria:** Each original execution/approval obligation has attributable evidence or
an explicit unresolved/approved deferred disposition; measured SC-007 and timing constraints are
reported honestly. Authentication, permissions, capacity, baseline data and approval access are
future prerequisites, not assumed present.

## Original Task Coverage

The checkbox column transcribes the original task list exactly, including lowercase `x` and suffixes.
Evidence of current source does not establish that the historical command, reviewer interaction, or
operator action in that task occurred. No original checkbox was changed.

| Original ID | Original state | Status | Evidence and explanation | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [x] | PARTIAL | [Original](tasks.md#L40); [dev JSON](../../infra/main.parameters.dev.json#L4) matches eight R3 values, not the stated seven; CD does not select it and fixed sizing contradicts its cost rationale. | AUD-031-003 |
| T002 | [x] | PARTIAL | [Original](tasks.md#L45); [relocated ADR](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L1) contains the intended sections, rotation and carve-out risk; backlinks are broken after relocation. | AUD-031-014 |
| T003 | [x] | IMPLEMENTED | [Original](tasks.md#L60); all three named workflow paths in [R6](research.md#L94) are absent in the read-only path check; all current workflow definitions were searched for consumers. | none |
| T004 | [x] | IMPLEMENTED | [Original](tasks.md#L65); both reusable files and the entire `_reusable` directory are absent; no current workflow uses them. [Binding scope](spec.md#L139). | none |
| T005 | [x] | IMPLEMENTED | [Original](tasks.md#L70); all five named standalone retired workflows are absent under the bounded workflow directory. [Deletion list](research.md#L94). | none |
| T006 | [x] | IMPLEMENTED | [Original](tasks.md#L75); all three specified composite-action directories are absent; all current workflows were checked for `uses` consumers. | none |
| T007 | [x] | IMPLEMENTED | [Original](tasks.md#L80); freeze file and now-unused state directory are absent in the direct path check. | none |
| T008 | [x] | PARTIAL | [Original](tasks.md#L85); pipeline package tree is absent and no active workflow installs it. The additional workstation `pip show` outcome was not inspected or executed. | AUD-031-016 |
| T009 | [x] | SUPERSEDED | [Original](tasks.md#L90); Identity, exceptions and old carve-out files remain absent; [Spec 033 T011](../033-maf-adoption/tasks.md#L110) and [Spec 036 T025](../036-foundry-rag-grounding/tasks.md#L97) explicitly restore only the posture matrix/Rego portion. The retained policy module exists. | AUD-031-014 |
| T009a | [x] | PARTIAL | [Original](tasks.md#L95); [subscriptionId description](../../infra/main.bicep#L127) is corrected, but other `Spec 029` descriptions remain at [topology](../../infra/main.bicep#L123) and [tags](../../infra/main.bicep#L130), so the literal zero-pattern criterion is not met. No Bicep build ran. | AUD-031-014, AUD-031-016 |
| T010 | [x] | IMPLEMENTED | [Original](tasks.md#L100); bootstrap directory is absent and [rollback helper](../../scripts/rollback.sh#L1) still exists. Its functional defects are separately traced, not proof of failed deletion. | AUD-031-001 |
| T011 | [x] | CONFLICT | [Original](tasks.md#L105); development parameter file is absent and [dev replacement](../../infra/main.parameters.dev.json#L1) exists. Literal repository-wide zero references conflicts even with preserved task/research history; no live renamed owner was assumed missing. | AUD-031-014 |
| T011a | [x] | PARTIAL | [Original](tasks.md#L110); dead ownership rules removed and [CD rule retained](../../.github/CODEOWNERS#L34). Historical comments still match parts of the prescribed grep; remote CODEOWNERS validation is UNVERIFIED. | AUD-031-014, AUD-031-016 |
| T012 | [x] | CONFLICT | [Original](tasks.md#L115); bounded tracked-text search finds later controls, relocated ADRs, historic references and stale live claims outside the original three-location allowance. Restored policy owners are explicit, not undeleted by inference. | AUD-031-014, AUD-031-016 |
| T012a | [x] | UNVERIFIED | [Original What-If/reviewer requirement](tasks.md#L120); no local raw What-If, reviewer decision, cleanup receipt or PR attachment. Commands were not run. | AUD-031-004, AUD-031-016 |
| T013 | [x] | PARTIAL | [Original](tasks.md#L137); [CI events](../../.github/workflows/ci.yml#L3) exactly match. Later [quality additions](../032-rubric-improvements/spec.md#L200) supersede byte-identical steps; current tests omit devops and the original runtime checks are UNVERIFIED. | AUD-031-011, AUD-031-016 |
| T014 | [x] | PARTIAL | [Original](tasks.md#L142); [single deploy job](../../.github/workflows/cd.yml#L33), exact SHA and dev exclusions exist; provisioning, health, rollback, ordering, manifest and summary defects prevent full contract coverage. | AUD-031-001, AUD-031-002, AUD-031-003, AUD-031-005, AUD-031-009, AUD-031-010 |
| T015 | [x] | UNVERIFIED | [Original](tasks.md#L147); [branch-creation runbook](quickstart.md#L16) exists; remote branch refs and PR-prerequisite acknowledgment were not inspected. | AUD-031-016 |
| T016 | [ ] | UNVERIFIED | [Explicitly deferred original](tasks.md#L152); [recommended protections](quickstart.md#L29) are documented. No protection API/UI evidence; not promoted to an implementation/deployment blocker by this audit. | AUD-031-016 |
| T017 | [x] | IMPLEMENTED | [Original](tasks.md#L169); [CD creds input](../../.github/workflows/cd.yml#L94), env binding and read/issues/actions permissions are present without OIDC. SHA pins have later [explicit authority](../032-rubric-improvements/spec.md#L295); actual auth remains UNVERIFIED. | AUD-031-007 |
| T018 | [x] | IMPLEMENTED | [Original](tasks.md#L174); [drift binding/matrix/login](../../.github/workflows/drift-detection.yml#L25) implements the requested auth changes. Preserved error/overlap behavior has separate defects. | AUD-031-005, AUD-031-006, AUD-031-007 |
| T019 | [x] | PARTIAL | [Original](tasks.md#L179); [dev creds binding](../../.github/workflows/eval-pr-gate.yml#L18) exists, but PR trigger is absent and config-based guards/polling permit no-verdict success. | AUD-031-007, AUD-031-008 |
| T020 | [x] | PARTIAL | [Original](tasks.md#L184); [dormant creds and binding note](../../.github/workflows/eval-publish-dataset.yml#L83) exist. API token reference is unbound and the documented push trigger is absent. | AUD-031-008 |
| T021 | [x] | CONFLICT | [Original](tasks.md#L189); [Contributor-only recipe](quickstart.md#L43) conflicts with template role-assignment writes. Creation, scopes and payload validation of all three real SPs remain UNVERIFIED. | AUD-031-004, AUD-031-007, AUD-031-012, AUD-031-016 |
| T022 | [x] | UNVERIFIED | [Original](tasks.md#L194); [environment/secret recipe](quickstart.md#L54) exists, not proof of GitHub state or local credential-file cleanup. | AUD-031-007, AUD-031-012, AUD-031-016 |
| T023 | [x] | PARTIAL | [Original](tasks.md#L199); six active login workflows use creds, while the explicit staging OIDC exception and [help's legacy reference](../../.github/workflows/help-snapshot.yml#L39) defeat the blanket zero-pattern assertion; unused token grants remain. | AUD-031-013 |
| T024 | [x] | IMPLEMENTED | [Original](tasks.md#L216); [FR-011 annotation and exact two-entry matrix](../../.github/workflows/drift-detection.yml#L25) exist with fail-fast false. Runtime evaluation/overlap is not proven. | AUD-031-005, AUD-031-006, AUD-031-016 |
| T025 | [x] | PARTIAL | [Original](tasks.md#L235); 19 of 21 R6 paths absent now, two explicitly restored. No historical verification/staging output recorded locally; see the retirement table below. | AUD-031-014, AUD-031-016 |
| T026 | [x] | PARTIAL | [Original](tasks.md#L254); [named owner/contact and triggers](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L100) exist at the relocated ADR. Maintainer confirmation and PR review are UNVERIFIED. | AUD-031-014, AUD-031-016 |
| T027 | [x] | PARTIAL | [Original](tasks.md#L267); [five authored notes](fr020-recommendations.md#L7) exist, but 25 workflows now exist and several notes overstate active gates. This report's current static review is not historical sign-off. | AUD-031-008, AUD-031-013, AUD-031-016 |
| T028 | [x] | CONFLICT | [Original](tasks.md#L272); [three structured proposals](fr020-recommendations.md#L21) exist; [blank dispositions](fr020-recommendations.md#L82) and defaults-before-feedback conflict with individual approval. | AUD-031-015 |
| T029 | [x] | UNVERIFIED | [Original](tasks.md#L281); no local eight-row result transcript, explicit FR-016 observed error/restoration record, or comparable timing baseline. Static source defects are not substituted for execution evidence. | AUD-031-016 |
| T030 | [x] | PARTIAL | [Original](tasks.md#L286); [README links the quickstart](../../README.md#L370), but the ADR link and relocated backlinks fail and live gate/architecture descriptions disagree with source. | AUD-031-014 |

## Requirement Coverage

Every original FR and suffix has a separate row. There are no original NFR IDs; additional
unnumbered plan/data-model obligations are assessed separately below.

| Original ID | Original state | Status | Evidence and explanation | Follow-up |
| --- | --- | --- | --- | --- |
| FR-001 | none | IMPLEMENTED | [Requirement](spec.md#L116); [CI push branches](../../.github/workflows/ci.yml#L3) are exactly main/dev/staging/production. | AUD-031-011, AUD-031-016 |
| FR-002 | none | IMPLEMENTED | [Requirement](spec.md#L117); [PR main filter](../../.github/workflows/ci.yml#L10) is present. | AUD-031-011, AUD-031-016 |
| FR-003 | none | IMPLEMENTED | [Requirement](spec.md#L118); [separate workflow_run trigger](../../.github/workflows/cd.yml#L19) and [success plus push guard](../../.github/workflows/cd.yml#L37) match. Actual event execution UNVERIFIED. | AUD-031-011, AUD-031-016 |
| FR-003a | none | PARTIAL | [Requirement](spec.md#L119); [checkout and routing](../../.github/workflows/cd.yml#L61) use upstream context, but [known-good metadata](../../.github/workflows/cd.yml#L341) reverts to default workflow context. | AUD-031-009 |
| FR-004 | none | PARTIAL | [Requirement](spec.md#L120); [one dynamic job/RG](../../.github/workflows/cd.yml#L33) is present; parameter consumption and environment-specific restore records are incomplete. | AUD-031-003, AUD-031-009 |
| FR-004a | none | PARTIAL | [Requirement](spec.md#L121); same template and dev file exist, but [azd](../../azure.yaml#L8) does not select the file and [fixed replicas](../../infra/main.bicep#L1099) contradict R3. | AUD-031-003, AUD-031-004 |
| FR-005 | none | PARTIAL | [Requirement](spec.md#L122); [per-branch non-cancelling lock](../../.github/workflows/cd.yml#L46) prevents same-group overlap, not out-of-order CI release regression or drift overlap. | AUD-031-005, AUD-031-010 |
| FR-006 | none | IMPLEMENTED | [Requirement](spec.md#L123); [push-only guard](../../.github/workflows/cd.yml#L37) rejects PR CI. | AUD-031-011, AUD-031-016 |
| FR-007 | none | UNVERIFIED | [Requirement](spec.md#L127); [schema](contracts/azure-credentials.schema.json#L6) and [setup recipe](quickstart.md#L54) authored, but no real environment secrets inspected. | AUD-031-007, AUD-031-016 |
| FR-008 | none | CONFLICT | [Requirement](spec.md#L128); core creds paths exist, but [accepted staging exception](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L155) narrows the blanket rule; [help legacy client ID](../../.github/workflows/help-snapshot.yml#L39) is not covered by that decision. | AUD-031-007, AUD-031-013 |
| FR-009 | none | PARTIAL | [Requirement](spec.md#L129); core workflows drop id-token, but [chaos](../../.github/workflows/chaos-quarterly.yml#L18), [DR drill](../../.github/workflows/dr-drill.yml#L17) and other inventory rows retain unused grants; cosign/OIDC exceptions have real consumers. | AUD-031-013 |
| FR-010 | none | PARTIAL | [Requirement](spec.md#L130); drift/eval/corpus are env-bound; [DORA telemetry](../../.github/workflows/dora-metrics.yml#L15) is not, and help uses the separate `prod` name. Telemetry versus management auth needs an explicit scope decision. | AUD-031-013 |
| FR-011 | none | IMPLEMENTED | [Requirement](spec.md#L134); [matrix](../../.github/workflows/drift-detection.yml#L25) is exactly staging/production with no dev override. | AUD-031-005, AUD-031-006, AUD-031-016 |
| FR-012 | none | IMPLEMENTED | [Requirement](spec.md#L135); [dispatch trigger](../../.github/workflows/drift-detection.yml#L12) uses the same fixed matrix. | AUD-031-016 |
| FR-013 | none | PARTIAL | [Binding obligation](spec.md#L139); 19 R6 paths remain absent; two restored control paths are narrowly [superseded](../033-maf-adoption/tasks.md#L110), not evidence that all retirement duties ended. | AUD-031-014 |
| FR-014 | none | PARTIAL | [Requirement](spec.md#L152); no live dependency on the ten retired workflows/package found. [Stale gate/architecture claims](../../docs/architecture/deployment/cicd-pipeline.md#L21) and literal reference criteria still need reconciliation. | AUD-031-014 |
| FR-015 | none | PARTIAL | [Requirement](spec.md#L156); [summary](../../.github/workflows/cd.yml#L409) exists but omits the failed step and can overstate success; rollback can report false recovery. | AUD-031-001, AUD-031-002, AUD-031-009 |
| FR-015a | none | PARTIAL | [Requirement](spec.md#L157); [rollback and issue guards](../../.github/workflows/cd.yml#L355) exist, but helper failures can collapse to successful bootstrap and suppress escalation. | AUD-031-001, AUD-031-002 |
| FR-015b | none | IMPLEMENTED | [Requirement](spec.md#L158); [dev exclusions](../../.github/workflows/cd.yml#L357) and [failed-no-rollback status](../../.github/workflows/cd.yml#L401) are explicit. Runtime issue absence still UNVERIFIED. | AUD-031-002, AUD-031-016 |
| FR-016 | none | PARTIAL | [Requirement](spec.md#L159); [empty CD secret check](../../.github/workflows/cd.yml#L84) names both values; malformed, incomplete, expired and other-workflow diagnostics lack equivalent validation. | AUD-031-007 |
| FR-017 | none | IMPLEMENTED | [Requirement](spec.md#L163); [relocated ADR](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L1) records rationale, risks, triggers and named owner. Authored status is not confirmed review/rotation execution. | AUD-031-012, AUD-031-014, AUD-031-016 |
| FR-018 | none | PARTIAL | [Requirement](spec.md#L164); [ADR backlink text](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L124) exists but resolves to nonexistent docs/specs after relocation. | AUD-031-014 |
| FR-019 | none | PARTIAL | [Requirement](spec.md#L168); [historic review](fr020-recommendations.md#L7) covers five, not the 25 current workflows; this report inventories the current source and limitations. | AUD-031-013, AUD-031-016 |
| FR-019a | none | PARTIAL | [Requirement](spec.md#L169); [dev creds](../../.github/workflows/eval-pr-gate.yml#L18) exist, but manual-only trigger and uncorrelated/empty verdict do not preserve PR eval operation. | AUD-031-007, AUD-031-008 |
| FR-019b | none | PARTIAL | [Requirement](spec.md#L170); [commented auth migration](../../.github/workflows/eval-publish-dataset.yml#L83) exists, but activating the undefined token reference does not produce the promised correct block. | AUD-031-008 |
| FR-020 | none | CONFLICT | [Requirement](spec.md#L171); [three recommendations](fr020-recommendations.md#L21) exist, but [automatic defaults and blank responses](fr020-recommendations.md#L76) do not satisfy individual feedback before action. | AUD-031-015 |

### Success Criteria

| Original ID | Original state | Status | Evidence and explanation | Follow-up |
| --- | --- | --- | --- | --- |
| SC-001 | none | UNVERIFIED | [Criterion](spec.md#L185); branch wiring exists, but no attributable three-env CI-to-CD deployment results; F01-F09 identify source risks. | AUD-031-001, AUD-031-002, AUD-031-003, AUD-031-004, AUD-031-009, AUD-031-010, AUD-031-016 |
| SC-002 | none | CONFLICT | [Criterion](spec.md#L186); six of seven active azure/login workflow files use creds, one has an explicit OIDC exception; extra legacy reference and telemetry paths prevent the original blanket assertion. | AUD-031-013, AUD-031-016 |
| SC-003 | none | IMPLEMENTED | [Criterion](spec.md#L187); all ten retired workflow files, reusable directory and pipeline package are absent in the static path check. This narrower SC does not include the two restored R6 policy paths. | none |
| SC-004 | none | UNVERIFIED | [Criterion](spec.md#L188); two-entry matrix is supported in source; exactly two observed jobs and zero historic dev drift runs were not inspected. | AUD-031-005, AUD-031-006, AUD-031-016 |
| SC-005 | none | UNVERIFIED | [Criterion](spec.md#L189); [runbook](quickstart.md#L35) exists but Contributor bootstrap and disconnected dev parameters are source blockers; no observed contributor onboarding. | AUD-031-003, AUD-031-004, AUD-031-007, AUD-031-012, AUD-031-016 |
| SC-006 | none | PARTIAL | [Criterion](spec.md#L190); named ADR owner/trigger exists, but no direct spec-to-ADR link and relocated backlinks/README navigation are broken. | AUD-031-014, AUD-031-016 |
| SC-007 | none | UNVERIFIED | [Criterion](spec.md#L191); no comparable previous/candidate push-to-complete timing; plan 20-minute target and current 60-minute timeout disagree but do not measure latency. | AUD-031-016 |
| SC-008 | none | PARTIAL | [Criterion](spec.md#L192); [three structured proposals](fr020-recommendations.md#L21) are authored; separate presentation/feedback is not evidenced. | AUD-031-015, AUD-031-016 |

### Unnumbered Design Obligations

Labels in this table are audit locators, not invented original requirement IDs. Original checkbox
state is `none` for each. These include nonfunctional constraints omitted by an FR-only inventory.

| Audit locator | Original state | Status | Original obligation and source assessment | Follow-up |
| --- | --- | --- | --- | --- |
| PLAN-CI-TIME | none | UNVERIFIED | [CI clean-push time no worse than baseline](plan.md#L40); no comparable timing artifact. | AUD-031-016 |
| PLAN-CD-TIME | none | CONFLICT | [CD at most 20 minutes](plan.md#L42) versus [60-minute timeout](../../.github/workflows/cd.yml#L45); neither proves measured runtime. | AUD-031-016 |
| PLAN-AU | none | PARTIAL | [AU constraint](plan.md#L49) and [allowed primary location](../../infra/main.bicep#L78) exist. Selected source is AU-bound; deployed topology and complete What-If review are UNVERIFIED. | AUD-031-003, AUD-031-004, AUD-031-016 |
| PLAN-QUALITY | none | PARTIAL | [Constitution check](plan.md#L57) claims PR lint/unit/integration and What-If review. CI selects contract/integration, omits devops/root unit; What-If review not evidenced. | AUD-031-011, AUD-031-016 |
| PLAN-RUNTIME-BOUNDARY | none | IMPLEMENTED | [Pipeline-only intended change](plan.md#L8); current deployment still packages api/agents/ingestion/web through [azd services](../../azure.yaml#L29). No source changes made by this audit. Historical diff attribution UNVERIFIED. | AUD-031-016 |
| MD-BRANCH | none | CONFLICT | [Lifecycle text](data-model.md#L40) says force-push only on main, while [production edge](spec.md#L104) leaves protection policy out of scope and expects resulting-head deployment. Clarify the advisory/required boundary. | AUD-031-010, AUD-031-014 |
| MD-ENV | none | PARTIAL | [Environment identities/schema rule](data-model.md#L46) partly wired; help uses prod, real env stores UNVERIFIED, malformed creds not uniformly checked. | AUD-031-007, AUD-031-013, AUD-031-016 |
| MD-CREDS | none | CONFLICT | [UUID v4/lifecycle rules](data-model.md#L81) differ from general uuid schema; rotation requires deleted JSON; optional HTTPS schema patterns exist but no workflow schema-validation call. | AUD-031-007, AUD-031-012 |
| MD-WORKFLOWS | none | PARTIAL | [Five-workflow trigger/auth inventory](data-model.md#L91) is historical; eval triggers changed and 20 more workflows exist. | AUD-031-008, AUD-031-013 |
| MD-RG | none | PARTIAL | [Three RG/template relationships](data-model.md#L108) reflected in CD names; explicit parameter selection and live isolation remain incomplete/unverified. | AUD-031-003, AUD-031-016 |
| MD-PARAMS | none | CONFLICT | [Per-env settings](data-model.md#L116) claim GlobalStandard for all three; [production file](../../infra/main.parameters.production.json#L11) uses Standard, as the original preserved-production directive permits. CD selection still needs resolution. | AUD-031-003, AUD-031-014 |
| MD-ADR | none | PARTIAL | [ADR section table](data-model.md#L131) enumerates eight sections despite task prose saying seven; content and owner exist, links do not resolve. | AUD-031-014 |
| MD-STATE | none | CONFLICT | [State diagram](data-model.md#L181) implies any staging/prod failure rolls back; [FR-015a](spec.md#L157) and source scope this to health failure only. Auth/provision failures need accurate not-attempted summaries. | AUD-031-002, AUD-031-014 |
| CI-PERMISSIONS | none | PARTIAL | [Contract contents: read](contracts/ci-workflow.md#L26) is not explicitly declared in [CI](../../.github/workflows/ci.yml#L1); effective repo defaults are UNVERIFIED. | AUD-031-013, AUD-031-016 |
| CD-OUTPUTS | none | PARTIAL | [Output table](contracts/cd-workflow.md#L123) describes target_env/revision-ingestion; source uses TARGET_ENV and revision-ingest, and manifest omits internal services. Consumer compatibility needs explicit mapping. | AUD-031-001, AUD-031-009 |

### Clarification Decisions

| Original locator | Original state | Status | Evidence and effect | Follow-up |
| --- | --- | --- | --- | --- |
| Q1 (2026-04-30) | none | PARTIAL | [Full-footprint deletion decision](spec.md#L12); 19 R6 paths absent, two expressly restored later. | AUD-031-014 |
| Q2 (2026-04-30) | none | PARTIAL | [Dedicated dev RG and file](spec.md#L13); source names match but selected parameters/lower sizing do not. | AUD-031-003, AUD-031-004 |
| Q3 (2026-04-30) | none | IMPLEMENTED | [Separate CI/CD workflow_run decision](spec.md#L14); [entry path](../../.github/workflows/cd.yml#L19) matches. Runtime remains UNVERIFIED. | AUD-031-016 |
| Q4 (2026-04-30) | none | IMPLEMENTED | [No dev rollback/issues](spec.md#L15); [both guards](../../.github/workflows/cd.yml#L357) encode it. | AUD-031-002, AUD-031-016 |
| Q5 (2026-04-30) | none | PARTIAL | [Eval auth/preserved dormant publisher](spec.md#L16); creds migration exists, trigger/poll/token regressions remain. | AUD-031-007, AUD-031-008 |

## Acceptance and Edge Coverage

US/edge/behavior labels below are audit locators for originally numbered or unnumbered scenarios.
All original AT IDs are retained exactly. Observed execution is UNVERIFIED unless a scenario is
itself static artifact inspection; a PARTIAL/CONFLICT row identifies a source defect, not a run result.

### User-Story Acceptance Scenarios

| Scenario | Original state | Status | Original scenario and implementation evidence | Follow-up |
| --- | --- | --- | --- | --- |
| US1-AS1 | none | UNVERIFIED | [Dev push CI/status](spec.md#L30); [CI event](../../.github/workflows/ci.yml#L3) configured, no observed run. Later jobs extend the original single quality job. | AUD-031-011, AUD-031-016 |
| US1-AS2 | none | PARTIAL | [Staging-only deploy after success](spec.md#L31); [routing](../../.github/workflows/cd.yml#L73) present, downstream parameters/health/restore incomplete. | AUD-031-001, AUD-031-002, AUD-031-003, AUD-031-009, AUD-031-016 |
| US1-AS3 | none | UNVERIFIED | [Failed production CI means no deploy](spec.md#L32); [success guard](../../.github/workflows/cd.yml#L37) supported, no negative-event run evidence. | AUD-031-011, AUD-031-016 |
| US1-AS4 | none | UNVERIFIED | [Main/non-env must not deploy](spec.md#L33); [CD branch filter](../../.github/workflows/cd.yml#L23) supported, no observed negative run. | AUD-031-011, AUD-031-016 |
| US1-AS5 | none | PARTIAL | [Same-env queueing](spec.md#L34); [mutex](../../.github/workflows/cd.yml#L46) present, queue/order behavior and out-of-order CI safety not established. | AUD-031-010, AUD-031-016 |
| US2-AS1 | none | CONFLICT | [Uniform secret use](spec.md#L48); current exception/inventory prevents the blanket assertion and real secret stores are unverified. [Accepted exception](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L155). | AUD-031-007, AUD-031-013, AUD-031-016 |
| US2-AS2 | none | CONFLICT | [No legacy references](spec.md#L49); [staging exception](../../.github/workflows/staging-promotion.yml#L74) plus [unresolved help reference](../../.github/workflows/help-snapshot.yml#L39). | AUD-031-013 |
| US2-AS3 | none | PARTIAL | [No unnecessary OIDC permission](spec.md#L50); core workflows comply; unused grants remain alongside genuine signing/OIDC needs. [Chaos grant](../../.github/workflows/chaos-quarterly.yml#L18). | AUD-031-013 |
| US2-AS4 | none | PARTIAL | [Missing/malformed actionable error](spec.md#L51); [CD empty-only guard](../../.github/workflows/cd.yml#L84) is narrower. | AUD-031-007, AUD-031-016 |
| US3-AS1 | none | UNVERIFIED | [Scheduled two-env matrix](spec.md#L65); [schedule/matrix](../../.github/workflows/drift-detection.yml#L12) supported, no scheduled-run receipt. | AUD-031-016 |
| US3-AS2 | none | UNVERIFIED | [Manual two-env matrix](spec.md#L66); [dispatch/matrix](../../.github/workflows/drift-detection.yml#L25) supported, no dispatch receipt. | AUD-031-016 |
| US3-AS3 | none | PARTIAL | [Staging drift issue](spec.md#L67); [issue step](../../.github/workflows/drift-detection.yml#L221) exists but parse/lookup fallback can conceal drift. | AUD-031-005, AUD-031-006, AUD-031-016 |
| US4-AS1 | none | IMPLEMENTED | [Three workflow files absent](spec.md#L81); direct path enumeration confirms all three absent. | none |
| US4-AS2 | none | IMPLEMENTED | [No remaining workflow dependency](spec.md#L82); all 25 YAML files read, no retired workflow_run/uses/package consumer found. [Current CD trigger](../../.github/workflows/cd.yml#L19). | none |
| US5-AS1 | none | IMPLEMENTED | [Decision contents inspectable](spec.md#L96); [relocated ADR](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L7) records old/new pattern, trade-off and OIDC follow-up. | AUD-031-014 |
| US5-AS2 | none | PARTIAL | [Decision discoverable at governance review](spec.md#L97); [README ADR link](../../README.md#L368) and backlinks broken; checkpoint review unverified. | AUD-031-014, AUD-031-016 |

### Contract Acceptance Tests

| Original ID | Original state | Status | Original test and source support | Follow-up |
| --- | --- | --- | --- | --- |
| AT-CI-001 | none | UNVERIFIED | [One dev CI run](contracts/ci-workflow.md#L71); event configured in [CI](../../.github/workflows/ci.yml#L3), no run observation. | AUD-031-011, AUD-031-016 |
| AT-CI-002 | none | UNVERIFIED | [Main PR then merge, neither deploys](contracts/ci-workflow.md#L72); [CI filters](../../.github/workflows/ci.yml#L3) and [CD guard](../../.github/workflows/cd.yml#L37) support it. | AUD-031-011, AUD-031-016 |
| AT-CI-003 | none | IMPLEMENTED | [Feature push excluded](contracts/ci-workflow.md#L73); exact [CI branch allowlist](../../.github/workflows/ci.yml#L5) statically excludes the named feature branch; execution unverified. | AUD-031-011, AUD-031-016 |
| AT-CD-001 | none | UNVERIFIED | [Dev deploy/no issue](contracts/cd-workflow.md#L117); routing/dev guards supported, full deploy result absent. | AUD-031-003, AUD-031-004, AUD-031-016 |
| AT-CD-002 | none | PARTIAL | [Staging induced health failure](contracts/cd-workflow.md#L118); [invocation](../../.github/workflows/cd.yml#L355) correct but helper restoration not reliable. | AUD-031-001, AUD-031-002, AUD-031-016 |
| AT-CD-003 | none | UNVERIFIED | [Main has no CD run](contracts/cd-workflow.md#L119); branch exclusion supported, Actions history not read. | AUD-031-011, AUD-031-016 |
| AT-CD-004 | none | UNVERIFIED | [PR never deploys](contracts/cd-workflow.md#L120); push guard supported, no runtime receipt. | AUD-031-011, AUD-031-016 |
| AT-CD-005 | none | PARTIAL | [Two production pushes in commit order](contracts/cd-workflow.md#L121); [CD mutex](../../.github/workflows/cd.yml#L46) lacks upstream completion-order protection. | AUD-031-010, AUD-031-016 |
| AT-DD-001 | none | UNVERIFIED | [Dispatch two jobs](contracts/drift-detection.contract.md#L76); [matrix](../../.github/workflows/drift-detection.yml#L27) supported, no observed jobs. | AUD-031-016 |
| AT-DD-002 | none | UNVERIFIED | [No dev jobs](contracts/drift-detection.contract.md#L77); fixed matrix supports source intent, historic/run UI evidence absent. | AUD-031-016 |
| AT-DD-003 | none | PARTIAL | [Deliberate staging drift](contracts/drift-detection.contract.md#L78); [issue path](../../.github/workflows/drift-detection.yml#L221) can be bypassed by swallowed parse errors. | AUD-031-005, AUD-031-006, AUD-031-016 |
| AT-DD-004 | none | IMPLEMENTED | [No id-token permission](contracts/drift-detection.contract.md#L79); [permissions](../../.github/workflows/drift-detection.yml#L17) contain contents/issues only. Static inspection is the requested test. | none |

### Edge Cases

| Edge locator | Original state | Status | Original edge and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| EDGE-01 | none | PARTIAL | [Two environment pushes](spec.md#L103); CI has no cross-env cancellation and CD uses separate groups, but release/manifest ordering and isolation need verification. | AUD-031-005, AUD-031-009, AUD-031-010, AUD-031-016 |
| EDGE-02 | none | PARTIAL | [Production force-push](spec.md#L104); checkout pins resulting SHA, contract permits checkout failure if unreachable; rollback/revision provenance is defective. | AUD-031-001, AUD-031-009, AUD-031-010 |
| EDGE-03 | none | PARTIAL | [Expired clientSecret](spec.md#L105); native login failure expected but environment-specific rotation guidance is not encoded. | AUD-031-007, AUD-031-012, AUD-031-016 |
| EDGE-04 | none | MISSING | [Drift during staging deploy](spec.md#L106); searched complete CD/drift YAML, azd config and their invoked helpers; no shared lock, pending-state check or deployed-SHA selection exists. | AUD-031-005 |
| EDGE-05 | none | IMPLEMENTED | [PR-driven CI must not deploy](spec.md#L107); [push-only CD guard](../../.github/workflows/cd.yml#L37) is explicit. Event execution UNVERIFIED. | AUD-031-011, AUD-031-016 |
| EDGE-06 | none | PARTIAL | [Non-deploy Azure workflows](spec.md#L108); dev creds/dormant input rewritten, but eval trigger, verdict and publisher-token defects remain. | AUD-031-007, AUD-031-008 |

### Independent Story Tests

| Test locator | Original state | Status | Source and evidence limit | Follow-up |
| --- | --- | --- | --- | --- |
| US1-IT | none | UNVERIFIED | [Push each env after US2 setup](spec.md#L26); no recorded three-env end-to-end deployment. | AUD-031-016 |
| US2-IT | none | UNVERIFIED | [Single dev secret then push](spec.md#L44); no credential-store inspection or login result. | AUD-031-007, AUD-031-016 |
| US3-IT | none | UNVERIFIED | [Scheduled/manual drift observation](spec.md#L61); no observed matrix run. | AUD-031-016 |
| US4-IT | none | IMPLEMENTED | [List workflows/references](spec.md#L77); current static enumeration confirms named workflow/package retirement; literal doc-reference refinements remain separately noted. | AUD-031-014 |
| US5-IT | none | PARTIAL | [Read decision rationale/risk/owner](spec.md#L92); relocated authored ADR supports content, broken discoverability and feedback evidence remain. | AUD-031-014, AUD-031-015 |

### Contract Behavior Rows

These rows ensure unnumbered contract scenarios are not lost behind the AT identifiers.

| Behavior locator | Original state | Status | Original row and evidence | Follow-up |
| --- | --- | --- | --- | --- |
| CI-B01 | none | UNVERIFIED | [Push main](contracts/ci-workflow.md#L63); source CI filter/CD exclusion present, completion not observed. | AUD-031-016 |
| CI-B02 | none | UNVERIFIED | [Push env branches](contracts/ci-workflow.md#L64); source CI/CD chain exists, deployment outcome not observed. | AUD-031-003, AUD-031-004, AUD-031-016 |
| CI-B03 | none | UNVERIFIED | [Main PR](contracts/ci-workflow.md#L65); push-only CD guard present, no run evidence. | AUD-031-016 |
| CI-B04 | none | IMPLEMENTED | [Other branch push](contracts/ci-workflow.md#L66); CI allowlist statically excludes it. | AUD-031-011 |
| CI-B05 | none | UNVERIFIED | [Overlapping dev CI](contracts/ci-workflow.md#L67); no CI cancellation block, both completion outcomes unobserved. | AUD-031-010, AUD-031-016 |
| CD-B01 | none | PARTIAL | [Dev success/health-failure rule](contracts/cd-workflow.md#L105); dev rollback exclusions work in source, complete deployment and health verdict do not have evidence. | AUD-031-002, AUD-031-003, AUD-031-004, AUD-031-016 |
| CD-B02 | none | PARTIAL | [Staging rollback/escalation](contracts/cd-workflow.md#L106); false-success helper path defeats restoration/escalation. | AUD-031-001, AUD-031-002 |
| CD-B03 | none | PARTIAL | [Production rollback/escalation](contracts/cd-workflow.md#L107); same helper defect, production identity still passed explicitly. | AUD-031-001, AUD-031-002 |
| CD-B04 | none | IMPLEMENTED | [Main excluded](contracts/cd-workflow.md#L108); [branch filter](../../.github/workflows/cd.yml#L23) encodes it, not an observed run assertion. | AUD-031-016 |
| CD-B05 | none | IMPLEMENTED | [PR excluded](contracts/cd-workflow.md#L109); [event guard](../../.github/workflows/cd.yml#L37) encodes it. | AUD-031-016 |
| CD-B06 | none | IMPLEMENTED | [Failed CI excluded](contracts/cd-workflow.md#L110); [conclusion guard](../../.github/workflows/cd.yml#L38) encodes it. | AUD-031-016 |
| CD-B07 | none | PARTIAL | [Both quick pushes complete](contracts/cd-workflow.md#L111); mutex exists but order/queue outcomes not established and older CI can deploy later. | AUD-031-010, AUD-031-016 |
| CD-B08 | none | PARTIAL | [Missing secret at login](contracts/cd-workflow.md#L112); source fails earlier in a useful explicit guard; exact runtime message not captured and malformed inputs lack parity. | AUD-031-007, AUD-031-016 |
| CD-B09 | none | PARTIAL | [Unavailable force-pushed SHA](contracts/cd-workflow.md#L113); checkout of exact SHA is encoded, failure accepted by contract, but early summary can omit target environment. | AUD-031-002, AUD-031-016 |
| DD-B01 | none | PARTIAL | [Scheduled clean environments](contracts/drift-detection.contract.md#L67); genuine clean path exists but errors can become clean, so result cannot be trusted generally. | AUD-031-006 |
| DD-B02 | none | PARTIAL | [Staging-only drift](contracts/drift-detection.contract.md#L68); matrix-specific issue exists; wrong revision, overlap and swallowed errors undermine it. | AUD-031-005, AUD-031-006 |
| DD-B03 | none | UNVERIFIED | [Manual same matrix/results](contracts/drift-detection.contract.md#L69); no dispatch evidence. | AUD-031-016 |
| DD-B04 | none | PARTIAL | [Absent RG exits zero](contracts/drift-detection.contract.md#L70); source does so, but also treats denied/failed lookup as absent. | AUD-031-006 |
| DD-B05 | none | PARTIAL | [One env missing secret](contracts/drift-detection.contract.md#L71); fail-fast false and native login encoded; actionable validation and observed independent completion unverified. | AUD-031-007, AUD-031-016 |
| DD-B06 | none | IMPLEMENTED | [No dev input](contracts/drift-detection.contract.md#L72); fixed matrix/no env-choice input supports it statically. | AUD-031-016 |

## Checklist Coverage

The checklist has 16 unnumbered items; CL labels below are audit-only identifiers. All original
states are `[x]`. Its notes explicitly permit artifact-specific names, so that vocabulary alone
is not reported as a defect. Checklist authorship is not review or deployment proof.

| Checklist locator | Original state | Status | Exact original item and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| CL-031-01 | [x] | IMPLEMENTED | [No implementation details (languages, frameworks, APIs)](checklists/requirements.md#L9); read with the explicit artifact-surface exception in its notes. | none |
| CL-031-02 | [x] | IMPLEMENTED | [Focused on user value and business needs](checklists/requirements.md#L10); all five stories state actor value. | none |
| CL-031-03 | [x] | IMPLEMENTED | [Written for non-technical stakeholders](checklists/requirements.md#L11); operator/maintainer stories are readable, technical contracts are intentionally separate. | none |
| CL-031-04 | [x] | IMPLEMENTED | [All mandatory sections completed](checklists/requirements.md#L12); stories, requirements, outcomes, assumptions and exclusions exist. | none |
| CL-031-05 | [x] | IMPLEMENTED | [No \[NEEDS CLARIFICATION\] markers remain](checklists/requirements.md#L16); no unresolved placeholder in the spec itself. This does not prove the later contradictions resolved. | none |
| CL-031-06 | [x] | PARTIAL | [Requirements are testable and unambiguous](checklists/requirements.md#L17); seven/eight parameters, UUID v4, queue ordering, 20/60-minute cap and data-model rollback wording need reconciliation. | AUD-031-003, AUD-031-007, AUD-031-010, AUD-031-014, AUD-031-016 |
| CL-031-07 | [x] | PARTIAL | [Success criteria are measurable](checklists/requirements.md#L18); metrics identified but SC-007 has no captured comparable baseline or complete timing method. | AUD-031-016 |
| CL-031-08 | [x] | IMPLEMENTED | [Success criteria are technology-agnostic (no implementation details)](checklists/requirements.md#L19); artifact-specific vocabulary expressly permitted by notes, not an implementation proof. | none |
| CL-031-09 | [x] | IMPLEMENTED | [All acceptance scenarios are defined](checklists/requirements.md#L20); 16 story scenarios and 12 contract AT IDs are authored and individually covered here. | none |
| CL-031-10 | [x] | IMPLEMENTED | [Edge cases are identified](checklists/requirements.md#L21); six explicit edges authored; their implementation status is separately assessed. | none |
| CL-031-11 | [x] | PARTIAL | [Scope is clearly bounded](checklists/requirements.md#L22); original boundary clear, two later restores and auth exception need bounded reconciliation rather than global retirement. | AUD-031-013, AUD-031-014 |
| CL-031-12 | [x] | PARTIAL | [Dependencies and assumptions identified](checklists/requirements.md#L23); US1/US2/operator dependencies exist, but bootstrap rights and deleted-file rotation dependency are incomplete. | AUD-031-004, AUD-031-012 |
| CL-031-13 | [x] | PARTIAL | [All functional requirements have clear acceptance criteria](checklists/requirements.md#L27); many are explicit, but auth diagnostics, overlap/order and feedback assumptions are not actually enforced. | AUD-031-005, AUD-031-007, AUD-031-010, AUD-031-015 |
| CL-031-14 | [x] | IMPLEMENTED | [User scenarios cover primary flows](checklists/requirements.md#L28); deploy/auth/drift/retirement/governance stories all exist. | none |
| CL-031-15 | [x] | UNVERIFIED | [Feature meets measurable outcomes defined in Success Criteria](checklists/requirements.md#L29); no attributable runtime/performance/approval evidence supports this checkmark. | AUD-031-016 |
| CL-031-16 | [x] | IMPLEMENTED | [No implementation details leak into specification](checklists/requirements.md#L30); accepted artifact-surface exception is documented, not proof of delivery. | none |

## Binding Retirement Evidence

All entries originate in [research R6](research.md#L94). Names of absent files below are historical
path text, not fabricated links to existing evidence. Direct read-only Test-Path checks found
19 absent entries and two existing, explicitly restored entries. The retained policy module and
rollback script were also confirmed present; legacy development parameters and `_reusable`/state
directories were absent. The report did not execute T008's package-manager or T025's staging checks.

| R6 path (historical target) | Original state | Status | Static result and authority | Follow-up |
| --- | --- | --- | --- | --- |
| .github/workflows/spec029-ci.yml | none | IMPLEMENTED | Absent; current CI owner is [ci.yml](../../.github/workflows/ci.yml#L1). | none |
| .github/workflows/spec029-cd.yml | none | IMPLEMENTED | Absent; current deploy owner is [cd.yml](../../.github/workflows/cd.yml#L17). | none |
| .github/workflows/spec029-drift-detection.yml | none | IMPLEMENTED | Absent; current owner is [drift-detection.yml](../../.github/workflows/drift-detection.yml#L10). | none |
| .github/workflows/_reusable/pr-gates.yml | none | IMPLEMENTED | Absent; full reusable directory absent; [R6 authority](research.md#L94). | none |
| .github/workflows/_reusable/canary-stage.yml | none | IMPLEMENTED | Absent; no active uses consumer; [R6 authority](research.md#L94). | none |
| .github/workflows/change-freeze.yml | none | IMPLEMENTED | Absent under current workflow directory; [original task](tasks.md#L70). | none |
| .github/workflows/posture-exception-sweep.yml | none | IMPLEMENTED | Absent; [original task](tasks.md#L70). | none |
| .github/workflows/evidence-pack.yml | none | IMPLEMENTED | Absent; later CI publication gate is a different owner, not this retired workflow. [Current gate](../../.github/workflows/ci.yml#L433). | none |
| .github/workflows/dev-key-issue.yml | none | IMPLEMENTED | Absent; [original task](tasks.md#L70). | none |
| .github/workflows/emergency-hotfix.yml | none | IMPLEMENTED | Absent; [original task](tasks.md#L70). | none |
| .github/actions/install-opa/ | none | IMPLEMENTED | Directory absent; [original task](tasks.md#L75). | none |
| .github/actions/setup-cosign-syft/ | none | IMPLEMENTED | Directory absent; later [cosign installer](../../.github/workflows/prompts-publish.yml#L23) does not restore it. | none |
| .github/actions/setup-oidc-azure/ | none | IMPLEMENTED | Directory absent; [later OIDC exception](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L155) uses azure/login directly. | none |
| .github/state/freeze.json | none | IMPLEMENTED | File and state directory absent; [original task](tasks.md#L80). | none |
| tools/pipeline/ | none | IMPLEMENTED | Package directory absent; [original task](tasks.md#L85). Installed-package state not checked. | AUD-031-016 |
| infra/IDENTITY.md | none | IMPLEMENTED | Absent; [corrected subscriptionId description](../../infra/main.bicep#L127) no longer refers to it. | AUD-031-014 |
| infra/policy/posture-matrix.yaml | none | SUPERSEDED | Exists as [new audit-retention matrix](../../infra/policy/posture-matrix.yaml#L1), explicitly required by [Spec 033 T011](../033-maf-adoption/tasks.md#L110). Not proof of a working OPA gate. | AUD-031-014 |
| infra/policy/posture-exceptions.yaml | none | IMPLEMENTED | Absent; [original task](tasks.md#L90). | none |
| infra/policy/foundry-carveout.yaml | none | IMPLEMENTED | Old path absent; [new registry](../../infra/parameters/foundry-carveout.yaml#L1) has explicit [Spec 032 authority](../032-rubric-improvements/spec.md#L249). | AUD-031-014 |
| infra/policy/rego/ | none | SUPERSEDED | Directory exists; [Spec 036 T025](../036-foundry-rag-grounding/tasks.md#L97) explicitly materializes the new control, with later T152 amendments. | AUD-031-014 |
| scripts/spec029-bootstrap/ | none | IMPLEMENTED | Directory absent; [original task](tasks.md#L100); [rollback](../../scripts/rollback.sh#L1) retained. | none |

Negative-search scope: all 25 current workflow definitions; direct checks of every R6 path plus
replacement/keep paths; tracked-text search across `.github`, `infra`, `scripts`, `apps`, `packages`,
`tests`, `tools`, `docs`, root documents and relevant later specs, excluding this report, all other
implementation-review reports and the audit inventory. No active workflow_run/uses/pip dependency
on the retired workflows/actions/package was found. Surviving historical words, new policy consumers,
the [old-gate load comment](../../.github/workflows/spec-036-50-agent-load.yml#L8), and
[live architecture prose](../../docs/architecture/deployment/cicd-pipeline.md#L21) require different
dispositions. They are not all deletable or all evidence of an old workflow still executing.

## Current Workflow Review

This is a fresh static FR-019 review of all 25 files, not an assertion that T027's prior review
was performed or that any job passed. Verdict RELEVANT refers to the workflow's intended role;
the status records source gaps within this audit. No workflow is deleted by this report.
Pinned SHA release labels were not independently resolved. Mutable v4/v5 action tags and absent
explicit permissions are recorded as review exceptions, not proof of an exploit.

| Workflow | Original state | Status | Current event/job/auth/exit review and relevance | Follow-up |
| --- | --- | --- | --- | --- |
| [amend-loop-coupling.yml](../../.github/workflows/amend-loop-coupling.yml#L10) | none | PARTIAL | RELEVANT policy coupling, manual-only. Its changed-file step needs PR SHAs/body absent from dispatch, so the claimed PR gate is disconnected. Read-only token, no Azure auth; mutable checkout v4. | AUD-031-013, AUD-031-014 |
| [cd.yml](../../.github/workflows/cd.yml#L19) | none | PARTIAL | RELEVANT sole branch deploy. One successful-push job, env-scoped creds, exact upstream checkout and non-cancelling group. Actual helpers expose F01-F07/F09; SHA pins present, persistence lacks write permission and uses wrong context. | AUD-031-001, AUD-031-002, AUD-031-003, AUD-031-004, AUD-031-005, AUD-031-007, AUD-031-009, AUD-031-010 |
| [chaos-quarterly.yml](../../.github/workflows/chaos-quarterly.yml#L7) | none | PARTIAL | RELEVANT staging exercise, scheduled/manual and env-bound creds. Polling stops at terminal status but does not reject Failed/Cancelled; issue is always a summary, not proof of a successful exercise. id-token unused; SHA pins present. | AUD-031-013, AUD-031-016 |
| [ci.yml](../../.github/workflows/ci.yml#L1) | none | PARTIAL | RELEVANT four-branch/main-PR validation. quality precedes Windows, canonical, accessibility, web shards and publication gates; merge follows shards, final web gate follows merge; docs-arch is independent. mypy/accessibility are warn-only; explicit test selection omits devops/root unit; no explicit workflow permissions. Later additions are not automatically rolled back. | AUD-031-011, AUD-031-013, AUD-031-016 |
| [codeql.yml](../../.github/workflows/codeql.yml#L1) | none | PARTIAL | RELEVANT intended security analysis, but manual-only matrix currently echoes unavailability. Analysis steps are commented out with a licensing rationale; actual license and security scan execution unverified. No Azure auth. | AUD-031-013, AUD-031-014, AUD-031-016 |
| [corpus-ingest.yml](../../.github/workflows/corpus-ingest.yml#L17) | none | PARTIAL | RELEVANT manual ingest, dev/staging/production choice and creds binding. Schedule comments are stale; no-drift output is not wired to skip later build steps. Build/update/seed chain mutates the chosen RG outside CD. id-token has a genuine cosign consumer; missing bundle steps can skip successfully. This is not a second spec-031 app deployment. | AUD-031-013, AUD-031-014 |
| [dora-metrics.yml](../../.github/workflows/dora-metrics.yml#L7) | none | PARTIAL | RELEVANT telemetry, dispatch-only rather than daily. No GitHub env; connection-string exporter, not azure/login. [Helper](../../scripts/dora_metrics_publish.py#L130) makes absent config/publish failures nonfatal. Its averages are not SC-007 comparative run evidence. | AUD-031-013, AUD-031-016 |
| [dr-drill.yml](../../.github/workflows/dr-drill.yml#L6) | none | PARTIAL | RELEVANT scheduled/manual failover drill, dynamic env and creds, but resource variables remain staging-specific even if target_environment changes. Unused id-token; failback best effort, issue always emitted. Not a proof of RPO/RTO or normal CD safety. | AUD-031-013, AUD-031-016 |
| [drift-detection.yml](../../.github/workflows/drift-detection.yml#L12) | none | PARTIAL | RELEVANT weekly/manual, exactly two env jobs, fail-fast false, creds and contents/issues only. No deploy lock/deployed-ref selection; lookup/parse errors can become clean; env-specific issue step exists. | AUD-031-005, AUD-031-006, AUD-031-007 |
| [eval-pr-gate.yml](../../.github/workflows/eval-pr-gate.yml#L3) | none | PARTIAL | RELEVANT intended PR eval, now dispatch-only. Dev creds conditional on vars; start ID not used for polling; absent/timeout verdict can pass; PR comment uses nonexistent dispatch PR context and is continue-on-error. | AUD-031-007, AUD-031-008 |
| [eval-publish-dataset.yml](../../.github/workflows/eval-publish-dataset.yml#L3) | none | PARTIAL | RELEVANT manual dataset validation, hashing and artifact upload. Azure block remains dormant with creds/binding note, but API token producer is undefined. No active Azure login or id-token grant; original dataset push trigger absent. | AUD-031-008 |
| [foundry-carveout-review-6mo.yml](../../.github/workflows/foundry-carveout-review-6mo.yml#L12) | none | PARTIAL | RELEVANT local date-window review, dispatch-only and contents read. Inline code fails stale/invalid dates but checks no deployed resource. Mutable checkout v4; a green result would not prove human reapproval. | AUD-031-013, AUD-031-016 |
| [foundry-carveout-review.yml](../../.github/workflows/foundry-carveout-review.yml#L3) | none | PARTIAL | RELEVANT local 90-day review; manual event makes the PR-only prompt-hash/comment job unreachable. No Azure login; first job has no explicit permissions, v4/v5 tags remain. Two distinct date-review workflows need a documented relevance/rationale check. | AUD-031-013, AUD-031-014 |
| [help-gates.yml](../../.github/workflows/help-gates.yml#L3) | none | PARTIAL | RELEVANT local help lints/link checks, dispatch-only. Screenshot gate skips missing files; no automatic PR gate despite comments. No Azure auth or explicit permissions; mutable v4/v5 tags. | AUD-031-013, AUD-031-014 |
| [help-snapshot.yml](../../.github/workflows/help-snapshot.yml#L3) | none | PARTIAL | RELEVANT intended content publisher on main push/manual mode, separate prod environment, legacy client-ID input and no login. [Embedding fallback](../../apps/ingest-runner/src/help_snapshot/embedder.py#L63) returns zero vectors on errors; [alias helper](../../apps/ingest-runner/src/help_snapshot/alias_swinger.py#L22) writes local state. Not evidence of a working production publication. | AUD-031-013, AUD-031-014 |
| [nightly-load.yml](../../.github/workflows/nightly-load.yml#L7) | none | PARTIAL | RELEVANT scheduled/manual env-bound load/telemetry. pytest errors are explicitly ignored; exporter errors are nonfatal, so failure-conditional issue does not reliably represent a test regression. Connection string, no Azure login; unused id-token. | AUD-031-013, AUD-031-016 |
| [prompts-publish.yml](../../.github/workflows/prompts-publish.yml#L7) | none | PARTIAL | RELEVANT signing. id-token is required by actual cosign keyless command, not legacy Azure auth. Manual-only event makes push-conditioned signature commit unreachable; shallow checkout/HEAD~1 failure is swallowed. No CD cosign verification step found in complete CD source. | AUD-031-013, AUD-031-014 |
| [security-scan.yml](../../.github/workflows/security-scan.yml#L8) | none | IMPLEMENTED | RELEVANT independent four-branch/main-PR gitleaks, PSRule and Trivy scans. No Azure management login; scoped token and SHA pins. Trivy sets exit-code 1. CD listens to ci completion, not this workflow; this row does not claim scans gate deployment or passed. | AUD-031-013, AUD-031-014, AUD-031-016 |
| [simulation-load-test.yml](../../.github/workflows/simulation-load-test.yml#L4) | none | IMPLEMENTED | RELEVANT manual Locust experiment followed by threshold-checker invocation; no management auth, contents read, caller-specified target. Artifacts always uploaded. Mutable action tags are an inventory exception; no measured load result inspected. | AUD-031-013, AUD-031-016 |
| [simulation-stub-sweep.yml](../../.github/workflows/simulation-stub-sweep.yml#L3) | none | PARTIAL | RELEVANT static sweep invokes `--enforce`, but is manual-only despite blocking-PR commentary. No explicit permissions; mutable action tags. No claim that a required status is actually configured remotely. | AUD-031-013, AUD-031-014, AUD-031-016 |
| [spec-035-gate.yml](../../.github/workflows/spec-035-gate.yml#L3) | none | PARTIAL | RELEVANT manual invariant/test/type/schema check. Two script invocations skip absent files; independent explicit tests remain. Contents read, no Azure login, action SHAs. No source connection to ci's conclusion/CD eligibility. | AUD-031-013, AUD-031-014 |
| [spec-036-50-agent-load.yml](../../.github/workflows/spec-036-50-agent-load.yml#L12) | none | PARTIAL | RELEVANT scheduled/manual load exercise. Baseline block prints an existing p95 or warns, rather than comparing newly generated CSV. No env binding/auth, unused id-token and retired pre-release comment. Not SC-007 evidence. | AUD-031-013, AUD-031-014, AUD-031-016 |
| [spec-036-blue-green-e2e.yml](../../.github/workflows/spec-036-blue-green-e2e.yml#L13) | none | PARTIAL | RELEVANT manual test, hermetic default. No env/login and unused id-token. [Real-staging test](../../tests/e2e/test_blue_green_alias_flip.py#L221) explicitly fails; in-memory timing/alias assertions are not deployed E2E evidence. | AUD-031-013, AUD-031-014, AUD-031-016 |
| [staging-promotion.yml](../../.github/workflows/staging-promotion.yml#L23) | none | PARTIAL | RELEVANT separate SLI gate: static -> smoke -> runtime -> local tag; schedule runs only static. OIDC is explicitly excepted by ADR-036-011, not an accidental blanket regression. CD neither needs this workflow nor consumes its local tag; claimed promotion integration remains unconnected. | AUD-031-013, AUD-031-014, AUD-031-016 |
| [web-coverage-iteration.yml](../../.github/workflows/web-coverage-iteration.yml#L9) | none | PARTIAL | RELEVANT scheduled/manual/closed-PR evidence maintenance, no Azure auth, contents/PR/issues write and per-ref lock. Artifact download has no upstream run identifier; errors are allowed, panel helper failures warn, and no diff exits zero. Authoring a PR is not human review evidence. | AUD-031-013, AUD-031-014, AUD-031-016 |

### Primary Control-Flow Assessment

CI's completion aggregates its non-ignored jobs, not just the historic quality job. The primary
quality step invokes lint, formatting, import checks, selected pytest paths, typecheck/build and
benchmark; mypy is explicitly continue-on-error. The
[coverage ratchet](../../scripts/coverage-ratchet.ps1#L29) uses a zero Phase-A floor and returns
success for missing coverage; no inspected CI step downloads the prior coverage file. The
[web gate helper](../../scripts/web-coverage/_lib/schema_validators.py#L82) fails explicit invalid
rows/thresholds, but its persona/outcome counts are not equivalent to actual passing end-to-end
tests; its depth-profile command has separate schema checks. Those later domain gates are not
re-audited here as independent specs and do not supply missing spec-031 workflow test coverage.

CD has no `needs` relationship to security-scan, staging-promotion, eval-pr-gate or prompt signing;
those workflows' existence cannot establish deploy gating. CD's sequence is checkout -> target env
-> credentials -> azd/SP/toolchain -> RG/environment -> soft-delete purge -> carve-out verifier
-> provision/postprovision seed -> deploy -> API/web health -> revisions/manifest -> conditional
rollback/escalation -> always status/summary. The purge is a real mutation before provisioning;
it is not a read-only validation step. [Carve-out validation](../../scripts/verify-carveout.ps1#L121)
checks proposed-resource membership only when WhatIfPath is supplied; CD passes no such argument.
`-Strict` only emits a near-expiry warning at [its branch](../../scripts/verify-carveout.ps1#L115),
not a fatal warning. The restored control is therefore not proof of a completed What-If review or
universal deployment-policy coverage. The [registry](../../infra/parameters/foundry-carveout.yaml#L14)
is an authored approval list; approver identities/date text were not independently confirmed.

All relevant fixture/test modules were read as source, including devops conftest's `on` normalization,
root test configuration, rollback/CD/drift/parameter tests, seed-loader tests and the blue-green
mode distinction. No pytest collection, imports, verifier invocation or actionlint was executed.

## Performed-Review and Smoke Evidence

These rows assess evidence quality, not future task completion. All are originally uncheckboxed
evidence duties (`none`); the original task checkbox states appear only in the task table above.

| Evidence duty | Original state | Status | What is actually supported | Follow-up |
| --- | --- | --- | --- | --- |
| REV-SOURCE | none | IMPLEMENTED | Expected SHA verified read-only; initial scoped worktree was clean. This establishes the inspected revision, not deployed state. | none |
| REV-INPUTS | none | IMPLEMENTED | All 12 original local inputs fully read; no local evidence/amendment directories omitted. No other implementation-review report read. | none |
| REV-WHATIF | none | UNVERIFIED | [T012a](tasks.md#L120) describes output + architect review; neither exists locally. Drift YAML is not a substitute for that reviewed dev What-If. | AUD-031-004, AUD-031-016 |
| REV-BRANCHES | none | UNVERIFIED | [T015/T016](tasks.md#L147) runbook exists; actual remote branch/protection state not inspected; T016 remains deferred. | AUD-031-016 |
| REV-IDENTITIES | none | UNVERIFIED | [T021](tasks.md#L189) claims SP creation/schema validation; no authentic creation/scope receipt. Contributor-only recipe has a separate source conflict. | AUD-031-004, AUD-031-016 |
| REV-SECRETS | none | UNVERIFIED | [T022](tasks.md#L194) describes per-env secrets and cleanup; no secret store or operator filesystem inspected. | AUD-031-007, AUD-031-012, AUD-031-016 |
| REV-RETIREMENT | none | PARTIAL | Direct static check: 19 absent, two later restored. [T012/T025](tasks.md#L115) historical grep/staged-deletion evidence not present; no package-manager inspection. | AUD-031-014, AUD-031-016 |
| REV-CODEOWNERS | none | PARTIAL | [CD ownership rule](../../.github/CODEOWNERS#L34) exists and dead rules are gone; remote validation/reviewer enforcement unverified. | AUD-031-014, AUD-031-016 |
| REV-AUTH-SECURITY | none | PARTIAL | Core env creds and no raw credential output in examined guards; malformed validation, unnecessary permissions and declared exceptions assessed in F10/F13. Actual SP least privilege/action release provenance/dependency vulnerability state unverified. | AUD-031-004, AUD-031-007, AUD-031-013, AUD-031-016 |
| REV-ROLLBACK-SRE | none | UNVERIFIED | [T014 SRE review requirement](tasks.md#L142) not corroborated by an attributable record. Existing string tests cannot establish restore correctness. | AUD-031-001, AUD-031-002, AUD-031-016 |
| REV-EVAL-QA | none | UNVERIFIED | [T019 QA review requirement](tasks.md#L179) has no associated execution/reviewer record; manual-only/timeout defects are current source findings. | AUD-031-008, AUD-031-016 |
| REV-ADR | none | PARTIAL | Relocated ADR contains named owner/contact and Accepted text; [T026 confirmation](tasks.md#L254) and actual governance checkpoint not evidenced. | AUD-031-014, AUD-031-016 |
| REV-WORKFLOWS | none | PARTIAL | [Five historic notes](fr020-recommendations.md#L7) are authored; this audit statically reviewed all 25. Neither means every workflow ran successfully or had human review. | AUD-031-013, AUD-031-016 |
| REV-REC-A | none | UNVERIFIED | [Proposal A](fr020-recommendations.md#L23) has change/reason/trade-off/default, but [disposition](fr020-recommendations.md#L82) is awaiting maintainer. Later carve-out source is not prior approval evidence. | AUD-031-015 |
| REV-REC-B | none | UNVERIFIED | [Proposal B](fr020-recommendations.md#L42) has a follow-up idea; [disposition](fr020-recommendations.md#L83) blank, ADR-032 still Proposed. | AUD-031-015 |
| REV-REC-C | none | UNVERIFIED | [Proposal C](fr020-recommendations.md#L59) exists; [disposition](fr020-recommendations.md#L84) blank and no actionlint gate in inspected CI. | AUD-031-015 |
| REV-CONSTITUTION | none | UNVERIFIED | [Plan PASS self-assessment](plan.md#L57) and entity diagrams are authored design artifacts, not confirmed PR/What-If review, deployment, AU-residency audit or runtime safeguard evidence. | AUD-031-016 |
| REV-TESTS | none | UNVERIFIED | Test source and discovery paths inspected; no product tests, pytest collection, builds or imports executed. [T029](tasks.md#L281) run claims are not proven by checkboxes. | AUD-031-011, AUD-031-016 |
| SMOKE-01 | none | UNVERIFIED | [Dev push deploys only dev](quickstart.md#L153); no matching run IDs/SHA/resource delta evidence. | AUD-031-016 |
| SMOKE-02 | none | UNVERIFIED | [Single secret](quickstart.md#L154); no live secret-list result; current auth exceptions need scoped treatment. | AUD-031-013, AUD-031-016 |
| SMOKE-03 | none | IMPLEMENTED | [Retired workflow/package inventory](quickstart.md#L155) confirmed statically by direct path enumeration; no historical smoke command claimed. | none |
| SMOKE-04 | none | UNVERIFIED | [Drift two-job dispatch](quickstart.md#L156); exact source matrix exists, no observed run. | AUD-031-016 |
| SMOKE-05 | none | UNVERIFIED | [Contributor onboarding within 30 minutes](quickstart.md#L157); no timed operator session; bootstrap rights/parameters need fixes. | AUD-031-003, AUD-031-004, AUD-031-016 |
| SMOKE-06 | none | PARTIAL | [ADR existence/links](quickstart.md#L158); relocated artifact exists with owner/review trigger, original command path and backlinks are broken. | AUD-031-014 |
| SMOKE-07 | none | UNVERIFIED | [No deployment-time regression](quickstart.md#L159); no comparable old/new run records. DORA helper/commented timing estimates are not equivalent. | AUD-031-016 |
| SMOKE-08 | none | PARTIAL | [Three recommendations](quickstart.md#L160) authored; separate presentation and decisions not evidenced. | AUD-031-015, AUD-031-016 |
| SMOKE-FR016 | none | UNVERIFIED | [T029 missing-secret/restore experiment](tasks.md#L281) lacks observed error text and restoration receipt; no secret modified by this audit. | AUD-031-007, AUD-031-016 |

### Review Contract Compliance

| Contract item | Original state | Status | Report evidence |
| --- | --- | --- | --- |
| RC-1 | none | IMPLEMENTED | [Contract item 1](../001-spec-implementation-audit/README.md#L21): metadata, exact revision, date, all local inputs and limits recorded above. |
| RC-2 | none | IMPLEMENTED | [Contract item 2](../001-spec-implementation-audit/README.md#L22): severity-ordered findings cite existing relative paths and source line anchors. |
| RC-3 | none | IMPLEMENTED | [Contract item 3](../001-spec-implementation-audit/README.md#L23): 16 stable unchecked AUD tasks identify obligations, expectation/impact, owners, developer/tester steps and completion criteria. |
| RC-4 | none | IMPLEMENTED | [Contract item 4](../001-spec-implementation-audit/README.md#L25): all FR/SC IDs, unnumbered constraints, story scenarios, ATs, edges and behavior rows separately covered. |
| RC-5 | none | IMPLEMENTED | [Contract item 5](../001-spec-implementation-audit/README.md#L26): all 33 original IDs including suffixes have exact original state, status, evidence and follow-ups. |
| RC-6 | none | IMPLEMENTED | [Contract item 6](../001-spec-implementation-audit/README.md#L29): authored reviews/diagrams/checkmarks separated from unverified run/approval/performance evidence. |
| RC-7 | none | IMPLEMENTED | [Contract item 7](../001-spec-implementation-audit/README.md#L31): future commands, prerequisites, fixtures, assertions and expected results included per task; none executed as remediation. |

## Validation and Remaining Limits

The report covers 33 original tasks, 26 FRs, eight SCs, 16 story acceptance scenarios, 12 named
contract ATs, six edges, five independent story tests, 20 unnumbered contract behavior rows,
16 original checklist items, five clarification decisions, eight smoke rows plus the extra FR-016
experiment, all 21 R6 deletion entries, and all 25 current workflows. It contains 16 unique
unchecked follow-ups. The 15 additional unnumbered design/plan rows are audit locators, not new
original requirements.

Final read-only validation results:

| Check performed in this audit | Result |
| --- | --- |
| Original task IDs and exact checkbox states | PASS: 33 separate rows, including all suffixes; 32 lowercase `[x]` and T016 `[ ]`. |
| Original requirements and named contract tests | PASS: 26 FRs plus eight SCs, and all 12 AT IDs, each once with original state `none`. |
| Scenario, edge, behavior, independent-test and smoke coverage | PASS: 16 story scenarios, six edges, 20 behavior rows, five independent tests, eight smoke rows and the extra FR-016 row. |
| Checklist and clarification coverage | PASS: 16 exact original checklist states and source-line mappings; all five clarification decisions. |
| Follow-up IDs, references and instructions | PASS: 16 sequential, unique unchecked AUD IDs; no undefined references; affected obligations, developer/tester directions, future commands and completion criteria present. |
| Workflow and retirement inventories | PASS: every one of 25 current workflows and 21 original R6 entries represented separately. Direct path check: 19 absent entries, two explicitly restored. |
| Local evidence links and anchors | PASS: 522 link occurrences resolve to existing local files and in-range, nonblank source lines. Broken original links are discussed, not reused as report evidence links. |
| JSON syntax | PASS: credential schema and all three environment parameter files parse through read-only ConvertFrom-Json. No schema engine, Bicep build or product validation was run. |
| Report diagnostics | PASS: get_errors reports no errors; no hard tabs and one terminal newline. |
| Revision and source integrity | PASS: HEAD remains `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`; scoped status shows only this new report, with no source/workflow/config/original-spec/task/evidence modifications. No branches or commits created. |

No static-audit completion blocker remains. Runtime acceptance, cloud/secret/branch state, external
reviews, action release provenance and measured performance remain UNVERIFIED under the authorized
boundary. They require the future prerequisites and evidence in AUD-031-016, not inferred passes
or remediation execution during this review. No product tests, repository scripts/verifiers, builds,
imports, browsers, servers, cloud operations, deployments, installs, runtime/debug sessions or external
approval requests were performed.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 031 only. Three parallel technical reviews examined branch/SHA
binding, AZURE_CREDENTIALS validation, and drift classification. The source-completable drift defect was corrected:
the parser now validates the What-If object and `changes` array and exits nonzero on malformed output or jq failure,
instead of converting parser errors into an empty clean result. A stale OIDC test assertion was aligned with the active
environment-secret workflow contract.

Validation: `python -m pytest tests/devops/test_drift_detection.py -q` returned `17 passed`.

Remaining open work includes exact deployed-SHA provenance, canonical parameter selection, credential schema/preflight,
drift authorization/404 classification, concurrency coordination, GitHub environment state, Azure RBAC, deployment,
and external approval/evidence.
