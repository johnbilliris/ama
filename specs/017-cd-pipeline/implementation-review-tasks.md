# Implementation Review: 017 CD Pipeline

## Review Boundary

- Review date: **2026-09-11**. Reviewed source revision: **5b44c249f00e0e4a13ea2579c8c33d06e2471d7a**, confirmed against local HEAD.
- Fresh, isolated, review-only assessment under the [Review Contract](../001-spec-implementation-audit/README.md#L12). No other implementation audit reports were read or used.
- Sole authorized deliverables are this report and the self-contained historical-folder report. No source, original documents, original checkboxes, audit index, branches, or commits were changed. No delegation, product imports, tests, builds, deployments, cloud queries, or external approvals were performed.
- Source declarations and test assertions are evidence of authored behavior, not successful execution. GitHub environment settings, deployed identities, actual secrets, resource locations, run results, and human approvals remain unverified.
- Coverage: **54 original tasks, all originally [x]; 15 FRs plus FR-CAP-017-001; 10 SCs; 18 acceptance scenarios; 10 edge cases; 15 clarification answers; 16 quality assertions; 87 comprehensive checklist questions; all seven historical artifacts**. There are **22 unchecked remediation tasks**. Shared AUD IDs identify the same work in both reports; this report contains all instructions needed to act independently.

### Inputs Read in Full

| Input | Scope |
| --- | --- |
| [spec.md](spec.md#L1) | All 233 lines, including clarifications, personas, hypothesis, scope, and capstone amendment. |
| [tasks.md](tasks.md#L1) | All 282 lines, T001 through T054 individually, checkpoint claims and sequencing. |
| [requirements checklist](checklists/requirements.md#L1) | All 16 checked assertions and explanatory notes. |
| [comprehensive checklist](checklists/comprehensive.md#L1) | All 87 unchecked questions and priority notes. |
| [historical plan](../feature/017-cd-pipeline/plan.md#L1) | Architecture, performance goals, constitution assessment and deliverables. |
| [historical research](../feature/017-cd-pipeline/research.md#L1) | R-001 through R-009, alternatives and claimed findings. |
| [historical data model](../feature/017-cd-pipeline/data-model.md#L1) | All eight entities, invariants, relationships and transitions. |
| [historical quickstart](../feature/017-cd-pipeline/quickstart.md#L1) | Prerequisites, four verification procedures, flow, recovery and troubleshooting. |
| [CD contract](../feature/017-cd-pipeline/contracts/cd-workflow.md#L1) | Triggers, identity, jobs, outputs, errors, concurrency and timeout budget. |
| [rollback contract](../feature/017-cd-pipeline/contracts/rollback-script.md#L1) | Arguments, discovery, exit codes, recovery, logging, security and timing. |
| [drift contract](../feature/017-cd-pipeline/contracts/drift-detection-workflow.md#L1) | Schedule, identity, comparison, filtering, report and failure semantics. |

No separate local amendment, review transcript, execution evidence, or historical task file exists in these two input inventories. Embedded amendments are covered below. Also inspected the directly controlling workflows, scripts, parameter files, IaC resource declarations, four original DevOps test modules and fixtures; the explicit spec-031 replacement decisions; the current constitution; and the linked portfolio rubric evidence. Applicable code-review, code-commenting and Bicep instructions were read. Azure validation guidance was consulted only for prerequisite/identity review criteria, not invoked as a deployment workflow.

## Status and Replacement Decisions

| Status | Meaning in this report |
| --- | --- |
| IMPLEMENTED | Full scoped authored behavior/artifact supported by source; runtime success not implied. |
| PARTIAL | Some behavior exists; a stated obligation is absent or contradicted. |
| MISSING | Required artifact/behavior absent after the specified scoped search. |
| CONFLICT | Requirement, task, decision or implementation disagrees; resolution required. |
| UNVERIFIED | Source cannot establish execution, outcome, sign-off or deployed state. |
| SUPERSEDED | Explicit repository replacement/retirement decision exists; not a missing-file defect. |

1. **Main-to-staging and chained production jobs are SUPERSEDED.** [Spec 031](../031-simplify-cicd-pipeline/spec.md#L1) expressly changes deployment to dev/staging/production branches. Its [CD contract](../031-simplify-cicd-pipeline/contracts/cd-workflow.md#L102) explicitly removes the old gate/production jobs. Restore retained safeguards in the current design; do not recreate the retired pipeline by default.
2. **OIDC is operationally SUPERSEDED for CD/drift, not silently omitted.** [ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L31) accepts a time-bound per-environment credential exception. Rotation and review triggers are operator obligations, not proven facts. The exception does not retire application-secret isolation.
3. **Spec-029 reusable calls and tooling are intentionally retired.** [Spec-031 research R6](../031-simplify-cicd-pipeline/research.md#L83) enumerates deleted workflows, composite actions and tools. No active reusable workflow call was found. Their absence is not an AUD-017 implementation defect.
4. **Four-service health and staging rollback remain required.** The [replacement CD contract](../031-simplify-cicd-pipeline/contracts/cd-workflow.md#L91) still requires all four checks; [research R4](../031-simplify-cicd-pipeline/research.md#L63) explicitly rejects deleting rollback. Merely commenting that API health covers internal services does not replace these requirements.
5. **Missing-resource-group drift behavior changed explicitly.** The [replacement drift contract](../031-simplify-cicd-pipeline/contracts/drift-detection.contract.md#L67) permits a warning/skip for an unprovisioned environment. This does not authorize treating access denial or parser failure as a clean comparison.
6. The original production-rollback exclusion is replaced by spec-031 staging/production recovery. Required-reviewer settings remain operator-owned, not proven removed or applied. Spec-031's statement that CI already enforces `pip-audit` is contradicted by the inspected workflow chain.

## Controlling Execution Paths

- [CI triggers](../../.github/workflows/ci.yml#L1): push on main/dev/staging/production; PR only to main. CI runs lint, selected test suites, type/build and other jobs. [Python strict typing](../../.github/workflows/ci.yml#L116) is explicitly nonblocking; [test selection](../../.github/workflows/ci.yml#L131) does not include the original DevOps suite.
- [CD trigger and guards](../../.github/workflows/cd.yml#L20): successful, push-origin CI on an environment branch; [checkout](../../.github/workflows/cd.yml#L66) pins the validated head SHA. One dynamic environment job, 60-minute timeout, per-environment non-cancelling concurrency. There is no cross-environment promotion dependency or local reusable invocation.
- [CD identity/bootstrap](../../.github/workflows/cd.yml#L94): environment credential login, separate azd service-principal login, resource-group creation, azd environment variables. It then [purges soft-deleted accounts](../../.github/workflows/cd.yml#L190), calls [carve-out verification](../../.github/workflows/cd.yml#L213), provisions and deploys.
- [azd manifest](../../azure.yaml#L8): shared Bicep entrypoint, four services; postprovision calls the [seed hook](../../scripts/seed-database.sh#L1), which invokes [seed_loader](../../scripts/seed_loader.py#L643). This is a data-writing provisioning dependency, not a passive deployment prerequisite. Web packaging also runs its build hook.
- [CD health/baseline/recovery](../../.github/workflows/cd.yml#L230): only API/web probes, revision outputs, a partially populated coverage manifest, health-failure-only rollback, critical issue, then an always-run status summary. [Rollback](../../scripts/rollback.sh#L337) discovers/restores containers, optionally redeploys web, and checks health serially.
- [Drift](../../.github/workflows/drift-detection.yml#L12): weekly/manual staging+production matrix, same environment credentials, what-if against the default-branch template and literal environment parameter files, inline jq, Markdown and issue creation. No deployment lock or deployed-SHA selection is connected.
- [Security scan](../../.github/workflows/security-scan.yml#L8) is a separate push/PR workflow, not a CD dependency. [Staging promotion](../../.github/workflows/staging-promotion.yml#L27) is scheduled/manual with its own static, smoke and runtime jobs. Its locally created tag and comment do not gate CD. This audit does not infer successful SLI checks from that workflow's presence.

### Scoped Negative Searches

| Search ID | Scope, terms and result |
| --- | --- |
| N01 | Complete `.github/workflows/` inventory and text search for `workflow_call`, local `_reusable` uses, `pip-audit`, `deployment-gates`, `gates-passed`, `gate-failures`: no matches. Retired topology is explained above; missing vulnerability enforcement is not. |
| N02 | `tests/**` search for `deployment-gates`, `deploy-staging`, `AZURE_CREDENTIALS`, `rollback.sh`, `pip-audit`; inspected all `tests/devops/` paths and four matching test modules. Old CD assertions and source-only rollback tests exist; no replacement CD gate/production behavior test or rollback workflow integration test was found. |
| N03 | `.github/**` search for `timeout-minutes: 4320`, `required_reviewers`, `wait_timer`, and relevant workflow calls; full CD/drift and branch-protection files read. No 72-hour approval-expiry implementation or applied production-environment evidence found. GitHub's actual settings were not queried. |
| N04 | CD, azd manifest, base/staging/production parameters read; no environment parameter-file selector in the provision path. Drift explicitly names those files. This is an absent source connection, not a claim about a particular deployed environment. |
| N05 | Full rollback/CD/known-good helper read and consumers searched. No rollback consumer of the stored manifest, no web artifact download, no all-four persisted baseline, and no authenticated-discovery-versus-empty-result distinction found. |
| N06 | Main Bicep Key Vault/module/identity/secret references searched and compute declarations read. Only the conditional recovery-signing vault is wired; application registry passwords are inline secret values, not per-environment vault references. No claim that Azure contains no manually provisioned vaults. |
| N07 | Exact HYP-HYP-015 path read failed; `specs/028-capstone-alignment/evidence/**` searched for HYP-015 and spec 017. Portfolio rubric documents exist; the named per-hypothesis stub and spec-specific consultation evidence were not found. |
| N08 | Full local input inventories contain no run logs, approval exports, timing series, rollback measurements or validation transcript supporting T051/T052/T053/T054. Their checked states are preserved, not accepted as execution proof. |

## Priority-Ordered Findings

| Priority | Finding and impact | Controlling evidence | Follow-up |
| --- | --- | --- | --- |
| P1 | Wrong rollback resource names and swallowed discovery errors can return bootstrap success without restoration. | [discovery](../../scripts/rollback.sh#L153), [bootstrap](../../scripts/rollback.sh#L377), [actual names](../../infra/main.bicep#L1007) | AUD-017-001 |
| P1 | Web rollback is skipped without an explicit value; its supposed history helper queries publishing credentials, and ZIP deployment requires an artifact rather than an arbitrary deployment ID. | [web discovery](../../scripts/rollback.sh#L172), [web rollback](../../scripts/rollback.sh#L243) | AUD-017-002 |
| P1 | Known-good state is incomplete, misidentifies web/source commit, is not reliably persisted, and is not consumed by recovery. | [revision capture](../../.github/workflows/cd.yml#L291), [manifest update](../../.github/workflows/cd.yml#L331), [manifest helper](../../scripts/web-coverage/known-good.py#L99) | AUD-017-003 |
| P1 | Two weak probes cannot validate four services; TLS checking is disabled, redirects accepted, and worst-case probe time is 210 seconds before discovery. | [health](../../.github/workflows/cd.yml#L230), [API stub health](../../apps/api/app/api/health.py#L10), [private/headless compute](../../infra/main.bicep#L1117) | AUD-017-004 |
| P1 | Partial service deployment failure never reaches the rollback guard. Provisioning already mutates app templates and reference data. | [provision/deploy](../../.github/workflows/cd.yml#L224), [guard](../../.github/workflows/cd.yml#L355), [postprovision](../../azure.yaml#L15) | AUD-017-005 |
| P1 | Authored environment parameters are disconnected from CD selection; production-tier and alert configuration cannot be inferred from matching filenames. | [environment setup](../../.github/workflows/cd.yml#L143), [base parameters](../../infra/main.parameters.json#L4), [tier default](../../infra/main.bicep#L121) | AUD-017-006 |
| P1 | Retirement of duplicate gates relies on CI having a dependency scan that is absent. Separate security/SLI workflows do not block this deployment chain. | [replacement claim](../031-simplify-cicd-pipeline/contracts/cd-workflow.md#L102), [CI](../../.github/workflows/ci.yml#L59), N01 | AUD-017-007 |
| P1 | Required production reviewers and 72-hour auto-rejection are unproved; drift shares the production environment, potentially waiting on deployment approvals. | [environment](../../.github/workflows/cd.yml#L40), [drift environment](../../.github/workflows/drift-detection.yml#L30), N03 | AUD-017-008 |
| P1 | Invalid drift JSON/parsing is converted to no drift; any failed resource-group lookup is classified as unprovisioned. | [lookup](../../.github/workflows/drift-detection.yml#L57), [fallback](../../.github/workflows/drift-detection.yml#L134) | AUD-017-009 |
| P1 | Per-environment application-secret vault handling is not implemented by the inspected compute path; managed identities elsewhere do not prove this requirement. | [inline registry secret](../../infra/main.bicep#L1023), [conditional vault](../../infra/main.bicep#L224), N06 | AUD-017-010 |
| P1 | Every normal CD run can permanently purge matching soft-deleted Cognitive Services accounts before the policy gate, without a distinct recovery authorization. | [purge step](../../.github/workflows/cd.yml#L190), [constitution](../../.specify/memory/constitution.md#L249) | AUD-017-011 |
| P2 | Dry-run still invokes Azure discovery; missing flag values can fail at `shift 2`, and authentication failure is not mapped to the declared exit code. | [arguments](../../scripts/rollback.sh#L77), [validation](../../scripts/rollback.sh#L123), [dry-run placement](../../scripts/rollback.sh#L212) | AUD-017-012 |
| P2 | Serial post-rollback probes alone permit 440 seconds, exceeding the entire five-minute recovery budget. | [health loop](../../scripts/rollback.sh#L400), [retry constants](../../scripts/rollback.sh#L20) | AUD-017-013 |
| P2 | Drift reports lose false values, may omit nested differences, use broad regex filters and unescaped property text, and do not preserve a report on issue failure. | [parser](../../.github/workflows/drift-detection.yml#L110), [report](../../.github/workflows/drift-detection.yml#L150) | AUD-017-014 |
| P2 | Drift can compare the wrong branch/parameters/images during a deployment and report expected rollout differences as drift. | [checkout/what-if](../../.github/workflows/drift-detection.yml#L33), [deployment lock](../../.github/workflows/cd.yml#L50) | AUD-017-015 |
| P2 | Deployment output can say success after a later baseline failure, or critical rollback failure when no rollback occurred; summaries omit precise restored targets. | [status](../../.github/workflows/cd.yml#L395), [summary](../../.github/workflows/cd.yml#L409) | AUD-017-016 |
| P2 | Tests retain retired main/OIDC/job expectations, mostly check strings, and are not selected by the CI test command. | [old assertions](../../tests/devops/test_cd_workflow.py#L49), [rollback tests](../../tests/devops/test_rollback_script.py#L57), [CI selection](../../.github/workflows/ci.yml#L131) | AUD-017-017 |
| P2 | Deployment latency, report latency and rollback success-rate claims lack measurements or a denominator. | [SCs](spec.md#L138), [60-minute job](../../.github/workflows/cd.yml#L45), N08 | AUD-017-018 |
| P2 | Sovereignty gate validates registry fields but is not bound to effective deployment resources; strict near-expiry warnings do not fail. | [gate call](../../.github/workflows/cd.yml#L213), [date check](../../scripts/verify-carveout.ps1#L99), [optional binding](../../scripts/verify-carveout.ps1#L121) | AUD-017-019 |
| P2 | Original contracts, quality pass claims and the unreviewed comprehensive checklist do not describe one consistent current delivery contract. | [quality notes](checklists/requirements.md#L32), [research](../feature/017-cd-pipeline/research.md#L164), [contracts](../feature/017-cd-pipeline/contracts/cd-workflow.md#L131) | AUD-017-020 |
| P2 | HYP-015's linked evidence is missing; portfolio scores and persona labels do not establish this spec's consultation or improvement claim. | [hypothesis](spec.md#L215), [portfolio snapshot](../028-capstone-alignment/evidence/rubric-postfeature.md#L25), N07 | AUD-017-021 |
| P2 | Checked execution tasks and plan PASS labels have no scoped validation or approval receipts. | [execution tasks](tasks.md#L171), [plan assessment](../feature/017-cd-pipeline/plan.md#L22), N08 | AUD-017-022 |

## Open Remediation Tasks

### Recovery and Delivery Safety

- [ ] AUD-017-001 (P1) Resolve real rollback targets and fail closed on discovery errors.

**Basis / expected / observed / impact:** FR-004, FR-011, FR-012; T005, T006, T007, T023, T036. A previous healthy release must be restored; [discovery](../../scripts/rollback.sh#L153) constructs `staging-api`, selects an unsorted second active entry, suppresses errors, then [bootstrap](../../scripts/rollback.sh#L377) can return success. Real names are environment-prefixed through IaC. An authentication/name failure can be advertised as recovery.

**Developer:** DevOps and SRE own the rollback discovery functions and CD caller. Resolve by scoped resource outputs/service tags, preserving the logical `ingestion` key despite physical `ingest` naming. Distinguish authenticated zero-history from not-found/access/CLI failures; choose a validated baseline, not array order. Depend on AUD-017-003; retain staging/production support and no dev rollback.

**Tester:** Extend [rollback tests](../../tests/devops/test_rollback_script.py#L1) and [fixtures](../../tests/devops/conftest.py#L1) with fake `az` command logs. Positive: shuffled real resource names restore pinned revisions. Negative: 403/expired auth/unknown name never yield bootstrap success. Edge: authenticated first deployment and already-active target produce explicit distinct outcomes without deactivating the target.

**Future validation:** V-RB after installing the fake CLI harness; assert resource-group scoping, no unintended resource calls, correct exit/outcome for every case. **Complete when:** discovery errors cannot report successful restoration and all four target identities are deterministic.

- [ ] AUD-017-002 (P1) Restore web from a verified deployable artifact.

**Basis / expected / observed / impact:** FR-004, FR-011; T006, T007, T033. [Web rollback](../../scripts/rollback.sh#L243) skips when no revision is passed; its unused [discovery helper](../../scripts/rollback.sh#L172) queries publishing credentials, not history. `config-zip --src` is given the alleged deployment ID. This does not restore the previous package.

**Developer:** App Service release owner and DevOps must define a retained ZIP/artifact reference with digest and environment identity, retrieve/verify it, and pass a local package to the restore operation. Remove the publishing-credential lookup. Coordinate the historical rollback interface and Service Revision model with AUD-017-003; keep compatibility explicit if `--revision-web` changes meaning.

**Tester:** In the existing rollback test home, fake artifact retrieval and `az` responses. Positive: exact known-good ZIP is deployed to the discovered web app. Negative: missing/expired artifact, digest mismatch or wrong-environment package fails without deployment. Edge: first deployment and an already-restored package are reported accurately.

**Future validation:** V-RB with retained-package fixtures and network disabled. **Complete when:** a web deployment ID/resource ID cannot be mistaken for a ZIP path and web participates in verified four-service restoration.

- [ ] AUD-017-003 (P1) Persist and consume a complete environment-bound known-good release.

**Basis / expected / observed / impact:** FR-011, FR-004; T022, T024, T033, T037. [Capture](../../.github/workflows/cd.yml#L291) stores an ARM resource ID for web; its JSON includes only API/web. [Update](../../.github/workflows/cd.yml#L341) uses workflow-context `github.sha`, attempts a push with read-only contents permission to workflow-context `ref_name`, and tolerates push failure. The [helper](../../scripts/web-coverage/known-good.py#L99) accepts missing traces/invalid revision JSON and has no environment key; rollback does not read it (N05).

**Developer:** DevOps with the spec-034 manifest owner must use the validated `head_sha`, all four immutable targets, environment, time and run identity. Persist atomically through an authorized durable mechanism, retrieve before mutation, and update only after all required health checks. Do not simply broaden token permissions or overwrite the coverage manifest's separate purpose. Coordinate AUD-017-001/002/004.

**Tester:** Extend [CD tests](../../tests/devops/test_cd_workflow.py#L1) and rollback fixtures. Positive: two releases then rollback restores the first. Negative: missing target, wrong environment, stale SHA, persistence denial or corrupt manifest blocks baseline acceptance. Edge: replay, concurrent runs and missing coverage trace cannot silently replace a good baseline.

**Future validation:** V-CD and V-RB using two-release manifests and fake artifact persistence. **Complete when:** the consumer restores the same complete tuple the successful producer recorded, without cross-environment or default-branch ambiguity.

- [ ] AUD-017-004 (P1) Validate all four services with a bounded, trustworthy health contract.

**Basis / expected / observed / impact:** FR-010, FR-001; T008, T021, T032; US1-AS2, US3-AS1. [CD](../../.github/workflows/cd.yml#L230) probes only API/web with five 30-second attempts and four 15-second sleeps: 210 seconds. It disables TLS verification and accepts redirects. [API health](../../apps/api/app/api/health.py#L10) checks configuration presence only, not agents/ingestion. The replacement contract retains four checks.

**Developer:** Service owners and DevOps must implement observable readiness for API, agents, ingestion and web without exposing private ingress. Preserve web-root HTTP-200/content-exclusion semantics unless explicitly amended. Authenticate internal checks, verify TLS, enforce a total deadline including discovery, and define three total attempts versus three retries unambiguously. Update the historical R-004/health entity after owner agreement.

**Tester:** Use existing CD/rollback test homes, fake `curl`/clock and service-response fixtures. Positive: four healthy services complete within 120 seconds. Negative: only agents or ingestion fails, timeout, TLS failure or redirect cannot produce a green release. Edge: web HTTP 200 error content remains accepted under the explicit original exclusion; flapping checks obey the documented attempt count.

**Future validation:** V-CD/V-RB, then V-REHEARSAL only with authorization and reachable private-service probes. **Complete when:** every service has independently attributable results and a deterministic two-minute maximum.

- [ ] AUD-017-005 (P1) Recover partial deployment failures and classify provisioning mutations.

**Basis / expected / observed / impact:** FR-004, FR-012, FR-013; T020, T023, T032, T035; CHK046, CHK055. The [historical error contract](../feature/017-cd-pipeline/contracts/cd-workflow.md#L131) requires rollback on service-deploy failure, but [the guard](../../.github/workflows/cd.yml#L355) requires a failed health step. Failed deployment skips that step. Bicep changes app images and [postprovision seeding](../../scripts/seed_loader.py#L670) writes data before the deploy step, invalidating a blanket assumption that provision failures change no services.

**Developer:** DevOps/SRE must capture a baseline before mutation and track provisioning, packaging, per-service deployment and health phases. Define supported compensation and manual recovery for infrastructure/data changes; do not attempt to reverse arbitrary data writes with a container rollback. Reconcile the narrower spec-031 guard with the retained safety obligation through the owner, keeping dev behavior explicit. Depends on AUD-017-001/002/003.

**Tester:** Existing CD/rollback tests should inject failure before provisioning, in the seed hook, after one container deployment, during web packaging and after health starts. Positive: normal rollout does not recover. Negative: mixed-version deployment cannot be left as success. Edge: zero-mutation failure does not claim a rollback, and partial IaC/data mutation names the required manual actions.

**Future validation:** V-CD/V-RB with command-order logs, then approved V-REHEARSAL. **Complete when:** every failing phase produces an explicit recovery decision and the supported service failures restore the full baseline.

- [ ] AUD-017-006 (P1) Select and validate effective environment configuration.

**Basis / expected / observed / impact:** FR-005, FR-009, FR-013; T002, T003, T014, T015, T019, T020, T031. [CD setup](../../.github/workflows/cd.yml#L143) sets basic azd variables but does not select the authored staging/production files. [Base parameters](../../infra/main.parameters.json#L4) and [production parameters](../../infra/main.parameters.production.json#L4) differ; neither environment file sets the [tier default](../../infra/main.bicep#L121). Placeholder production alert destinations remain. Drift and deployment can evaluate different desired states.

**Developer:** IaC and DevOps owners must implement one supported parameter resolution path shared with drift, explicitly map `production` to the template's `prod` tier, validate principal type/ID, subscription/resource group, regions and intended operational values before provisioning. Preserve schema/azd compatibility and the four-service definition. Account for azd auth, seed data-plane permissions and the failing postprovision hook; do not hide environment creation errors with unconditional success.

**Tester:** Extend [parameter tests](../../tests/devops/test_parameter_files.py#L12) beyond JSON names to rendered configuration and command arguments. Positive: staging and production select distinct resources and intended flags. Negative: foreign environment, non-AU region, unresolved substitution, invalid tier or missing required principal fails pre-mutation. Edge: repeat bootstrap and optional dev configuration reuse the same mechanism.

**Future validation:** V-PARAM and, after approval, V-IAC with isolated rendered parameter fixtures. **Complete when:** CD and drift use demonstrably identical environment-specific desired state and no production setting falls through accidentally to a dev default.

- [ ] AUD-017-007 (P1) Restore blocking security evidence in the replacement workflow chain.

**Basis / expected / observed / impact:** FR-002; SC-002, SC-006; T025, T027, T028, T029. [Spec-031's removal rationale](../031-simplify-cicd-pipeline/contracts/cd-workflow.md#L102) says CI already enforces lint and `pip-audit`. [Lint exists](../../.github/workflows/ci.yml#L59), dependency auditing does not (N01). Separate security and staging-promotion workflows cannot prevent CD from proceeding. Strict Python typing is advisory by explicit later configuration, not a blocking gate.

**Developer:** Security and release owners must define the retained required checks for the exact release SHA and connect them to the authoritative CI/CD readiness decision. Restore dependency auditing of the actual deployable dependency set or approve a documented equivalent; decide the ownership of staging evidence under branch-based production. Do not resurrect retired reusable jobs or claim a separate green badge is a dependency. Resolve advisory-versus-blocking checks explicitly.

**Tester:** Extend the existing CD test module with a dependency graph and event fixtures. Positive: complete matching-SHA test/security/health evidence permits release. Negative: vulnerability, failed required check, missing result, wrong SHA or still-running parallel security scan blocks it. Edge: PR-origin, cancelled and skipped CI runs never deploy; permitted advisory checks remain distinct.

**Future validation:** V-CD, followed by approved negative V-REHEARSAL. **Complete when:** no production release can bypass the agreed security requirements and the removed-gate rationale is factually correct.

- [ ] AUD-017-008 (P1) Resolve production approval expiry and read-only drift authorization.

**Basis / expected / observed / impact:** FR-003, FR-006; T026, T030, T038, T042; CHK015, CHK043, CHK074. [Dynamic environment binding](../../.github/workflows/cd.yml#L40) is not proof of reviewers or 72-hour expiry. [Drift](../../.github/workflows/drift-detection.yml#L30) uses the same production environment and can inherit its approval wait. The historical wait-timer statement does not implement auto-rejection; branch-protection files only describe main.

**Developer:** Repository administrators and Security own the actual environment policy and release checks. Decide how the retained approval obligation fits spec-031, implement an expiring approval bound to commit/environment, and separately authorize scheduled read-only drift without weakening production deployment protection. Record exception owner/review/rotation evidence under ADR-031; never place real credential values in evidence.

**Tester:** Use V-CD policy fixtures and fake time. Positive: an authorized current approval permits the matching deployment. Negative: unauthorized, missing, revoked or more-than-72-hour-old approval does not. Edge: reject/retry, commit replacement, and a scheduled drift run pending during a production approval retain correct scope.

**Future validation:** V-POLICY only after administrator authorization; capture redacted policy snapshots and an approved/denied/expired test-run sequence. **Complete when:** policy configuration and observed expiry enforcement agree, and weekly drift is not dependent on unattended deployment approval.

- [ ] AUD-017-009 (P1) Make drift comparison failures distinguishable from a clean result.

**Basis / expected / observed / impact:** FR-006, FR-007; T043, T044, T047; US5-AS1, EDGE-05. [What-if output](../../.github/workflows/drift-detection.yml#L41) combines stderr/stdout; [parser fallback](../../.github/workflows/drift-detection.yml#L134) turns invalid input into `[]`. Any group lookup error becomes a not-provisioned skip. This can hide drift or lost access as a green run.

**Developer:** DevOps owns the inline comparison/parser boundary. Keep diagnostic streams separate, validate the supported response envelope and change array, propagate parse/schema errors, and distinguish authenticated resource absence from authorization/transport failure. Preserve spec-031's explicitly allowed genuine-absence warning without calling it an evaluated clean state. Depend on AUD-017-015 for release context.

**Tester:** Extend [drift tests](../../tests/devops/test_drift_detection.py#L1) with supplied JSON/error fixtures, not string-presence assertions. Positive: valid empty changes is clean. Negative: malformed JSON, warning-prefixed output, absent change envelope, CLI failure and 403 are failed/unknown, never clean. Edge: genuine unprovisioned environment and an envelope variant supported by the pinned CLI have explicit results.

**Future validation:** V-DRIFT with fake `az` and `gh`, no Azure calls. **Complete when:** only a validated successful comparison can emit no drift.

- [ ] AUD-017-010 (P1) Satisfy the retained application-secret isolation contract.

**Basis / expected / observed / impact:** FR-005; SC-004; T003, T014, T015, T031. [Compute secrets](../../infra/main.bicep#L1023) contain registry passwords directly; the [conditional signing vault](../../infra/main.bicep#L224) does not supply an all-environment application secret store. Managed identities and Cosmos RBAC exist but do not prove vault access or environment isolation (N06).

**Developer:** IaC/Security owners must separate application secrets from the accepted MVP pipeline credential exception. Prefer identity-based access that eliminates secrets; for retained secrets implement dedicated environment vaults, scoped service identities and required data-plane grants. Formally reconcile any no-secret alternative with FR-005. Preserve policy constraints and verify bootstrap can create roles without broad permanent privileges.

**Tester:** Extend parameter/IaC contract assertions in existing DevOps test homes with environment-resource graphs and mocked authorization. Positive: each service accesses only its own environment's necessary resources. Negative: staging identity cannot retrieve production values; no real secret appears in outputs or reports. Edge: missing vault/grant, rotation and first provision fail safely.

**Future validation:** V-PARAM/V-IAC, then redacted authorized V-POLICY access evidence. **Complete when:** the retained secret store and identity boundary are wired in source and demonstrated without exposing secrets.

- [ ] AUD-017-011 (P1) Require explicit authorization for destructive bootstrap recovery.

**Basis / expected / observed / impact:** FR-013; T019, T020, T031; plan Life Safety and [constitution human authorization](../../.specify/memory/constitution.md#L249). [Normal CD](../../.github/workflows/cd.yml#L190) permanently purges every matching soft-deleted Cognitive Services kind in the target group before carve-out verification. RG scoping limits scope but does not preserve recoverable resources or prove approval of deletion.

**Developer:** Platform/Security owners must move irreversible purge behind a distinct approved recovery action or fail with actionable restoration instructions. Bind approval to exact resource IDs and intended operation; distinguish restore from recreate. Keep ordinary first-run group creation automatic and avoid expanding permissions solely to accommodate purge. Coordinate provisioning recovery with AUD-017-005.

**Tester:** Add command-order cases in the existing CD module. Positive: fresh environment provisions without purge. Negative: existing soft-deleted account causes a hold and no destructive command without authorization. Edge: multiple kinds, similar RG names and partial purge failure preserve an exact audit trail and do not continue blindly.

**Future validation:** V-CD with fake soft-delete inventories; any real recovery is separately authorized, never part of this audit. **Complete when:** a routine push cannot irreversibly delete recoverable resources without the documented human decision.

### Contract, Tests and Evidence

- [ ] AUD-017-012 (P2) Enforce rollback argument, authentication and offline dry-run semantics.

**Basis / expected / observed / impact:** FR-004, FR-014; T004, T005, T009, T034. [Parsing](../../scripts/rollback.sh#L77) can reach `shift 2` without a value. [Dry-run](../../scripts/rollback.sh#L212) is checked after Azure calls, and the main loop performs additional discovery. The contract's auth exit 3 is not implemented as a session check.

**Developer:** Rollback owner must validate complete flag/value pairs before side effects, reject unsupported environment/group combinations, define authentication failure mapping, and build a plan without invoking Azure in dry-run. Preserve all documented flags and exit codes, with an explicit unknown-target plan when no local baseline is supplied. Do not treat quoting as proof of complete validation.

**Tester:** Existing rollback fixtures must place sentinel `az`/`curl` executables on PATH. Positive: valid explicit targets produce the expected plan. Negative: lone flags, flag-as-value, empty group, invalid environment and missing/expired CLI session return the intended codes. Edge: spaces, shell metacharacters, repeated flags and help make no unintended commands.

**Future validation:** V-RB; assert zero sentinel calls for dry-run, exact exit 2/3 on errors, no command injection. **Complete when:** interface behavior is executable-test-backed rather than merely containing flag strings.

- [ ] AUD-017-013 (P2) Bound and report post-rollback health verification.

**Basis / expected / observed / impact:** FR-010, FR-012; SC-003; T008, T010, T037. [Serial verification](../../scripts/rollback.sh#L400) permits four times 110 seconds before discovery/restoration overhead; it cannot meet the historical five-minute budget in the worst case.

**Developer:** SRE/rollback owner must run independent checks concurrently under one recovery deadline, retain per-service results and join every child process, and report restoration versus health-verification failures distinctly. Share the health semantics agreed in AUD-017-004, including private worker readiness and retry terminology. Preserve contracted exit 4 for failed post-restore health.

**Tester:** Extend the same fake-clock/CLI rollback suite. Positive: all targets restore and report versions/timings. Negative: one slow/failed service yields exit 4 with its identity. Edge: simultaneous timeouts, an interrupted child and bootstrap skip do not hang, leak processes or count as a measured successful restore.

**Future validation:** V-RB with controlled clock and command durations. **Complete when:** health takes at most 120 seconds and the complete supported recovery meets the agreed 300-second budget or an explicit approved amendment replaces it.

- [ ] AUD-017-014 (P2) Preserve accurate, safe and retrievable drift evidence.

**Basis / expected / observed / impact:** FR-006, FR-007; T040, T044, T045, T046, T047. [Parsing](../../.github/workflows/drift-detection.yml#L110) uses broad regex matching and `// "null"`, which substitutes for boolean false, and assumes flat deltas/type fields. [Reporting](../../.github/workflows/drift-detection.yml#L150) inserts raw values into Markdown and saves the report only on the runner before issue creation.

**Developer:** Drift/report owner must normalize the pinned CLI response, traverse nested changes, retain false/zero/null distinctions and true resource type, use precise system-property filters, escape Markdown, redact secret-bearing values, and retain a sanitized artifact/summary if issue creation is denied or rate-limited. Preserve the existing label, metrics and intentional-drift review workflow.

**Tester:** Existing drift tests need real-shaped synthetic Create/Delete/Modify/NoChange fixtures. Positive: changed declarative values produce exact expected/actual rows. Negative: secret values never appear and nested real changes are not filtered. Edge: false, zero, null, newlines, pipes, regex-lookalike property names and issue API failure leave complete retrievable findings.

**Future validation:** V-DRIFT with fake `gh` and captured reports. **Complete when:** report assertions verify property fidelity, safe rendering and retained failure evidence, not only issue-command presence.

- [ ] AUD-017-015 (P2) Compare a stable deployed environment against its intended release.

**Basis / expected / observed / impact:** FR-006, FR-015; T042, T043; CHK061. [Drift checkout](../../.github/workflows/drift-detection.yml#L33) defaults to the repository branch, while CD deploys environment-branch head SHAs. It compares literal parameter files/default image parameters and has no coordination with the deployment concurrency group. A valid deployment can appear as unauthorized drift.

**Developer:** DevOps/SRE must bind drift to the environment's approved release SHA and effective parameter/image set from AUD-017-003/006. Define a bounded wait or explicit pending result during a deployment; coordinate access without cancelling writes or deadlocking reusable locks. Preserve weekly UTC schedule, dev exclusion and independent environment failure handling.

**Tester:** Existing drift/CD tests should model two environment SHAs and overlapping release/scan operations. Positive: a stable matching release reports no drift. Negative: true unauthorized scale change is reported. Edge: in-flight deployment, queued newer release, missing baseline and differing main commit yield pending/unknown or a correctly scoped comparison, not a false clean or spurious issue.

**Future validation:** V-CD/V-DRIFT with deterministic scheduling fixtures, then approved V-REHEARSAL. **Complete when:** report metadata identifies the exact intended release and no comparison races an environment mutation.

- [ ] AUD-017-016 (P2) Make native deployment outcomes and failure summaries truthful.

**Basis / expected / observed / impact:** FR-007, FR-012; SC-008; T024, T029, T037, T038, T050. [Status selection](../../.github/workflows/cd.yml#L395) considers health before later failures, and otherwise can label a pre-deploy failure critical rollback failure. [Summary](../../.github/workflows/cd.yml#L409) omits per-service restoration targets. GitHub environment association can produce native deployment records; YAML outputs alone do not prove the required outcome semantics.

**Developer:** DevOps/SRE must compute outcomes from phase, mutation and verification results, provide failing check/service/reason/remediation and baseline identifiers, and preserve failure visibility when notification delivery itself fails. Specify whether a critical outcome holds subsequent queued releases and how the operator resumes; do not invent a successful rollback for authenticated first-run skips. Keep notifications GitHub-native.

**Tester:** In CD fixtures test success, deploy failure, rollback success, rollback exits 1/2/3/4, post-health persistence failure and issue API denial. Positive: successful complete run is success. Negative: failed baseline persistence cannot advertise complete success. Edge: early checkout/login failure has useful context without unset-variable errors or a false rollback claim.

**Future validation:** V-CD and V-REHEARSAL; assert structured outcomes and actionable reports within the agreed 120-second reporting target. **Complete when:** summaries, outputs and native run/deployment status tell the same phase-accurate story.

- [ ] AUD-017-017 (P2) Replace stale structural assertions with connected behavioral coverage.

**Basis / expected / observed / impact:** FR-001, FR-002, FR-004, FR-006, FR-008; T012, T013, T025, T026, T034, T035, T039, T040, T054. [CD tests](../../tests/devops/test_cd_workflow.py#L49) still assert main/OIDC and removed jobs; [rollback tests](../../tests/devops/test_rollback_script.py#L57) only search source. N02 found no equivalent rollback workflow integration test. [CI](../../.github/workflows/ci.yml#L131) does not run this suite.

**Developer:** QA/DevOps must reconcile tests with the explicit spec-031 topology without deleting retained health/security/recovery assertions. Reuse the four existing test modules and conftest; add hermetic fake-command execution and workflow dependency assertions there or a clearly proposed integration home. Add a required CI selection for the maintained suite, with the no-CI-edit historical constraint explicitly superseded rather than ignored.

**Tester:** Positive: valid environment pushes, complete baseline and valid drift fixtures pass. Negative: mutate a guard, remove one service check, swallow parser failure or bypass security and observe targeted failures. Edge: cancelled/skipped/PR CI, reordered revisions and missing dependencies remain deterministic and offline.

**Future validation:** V-CD/V-RB/V-DRIFT/V-PARAM then V-SUITE. **Complete when:** current tests no longer demand retired shapes, each material finding has a regression assertion, and CI selects those assertions.

- [ ] AUD-017-018 (P2) Measure the performance and reliability outcomes honestly.

**Basis / expected / observed / impact:** SC-001, SC-003, SC-008, SC-010; T021, T048, T053. Original budgets are 900 seconds deployment, 300 seconds rollback, 120 seconds reporting and at least 95% successful restoration. [Current timeout](../../.github/workflows/cd.yml#L45) is 60 minutes and health arithmetic already exceeds stated budgets. No scoped measurements establish the outcomes (N08).

**Developer:** SRE/QA must define timestamp boundaries, first-provision versus warm-deploy cohorts, recovery attempt denominator, observation window and exclusions. Count bootstrap skips and unsupported recovery separately, not as successful rollbacks. Seek explicit owner resolution for changed cold-start targets; retain the original unmet criteria in historical traceability.

**Tester:** Add metric fixture assertions in the existing CD/rollback test homes. Positive: boundary values and a 95/100 valid-restoration sample meet the definitions. Negative: 94/100, missing endpoints/timestamps, partial restore or altered denominator fail. Edge: cancelled runs, no rollback attempts and first provision are unknown/separate, never fabricated 100% success.

**Future validation:** V-SUITE for calculations; V-REHEARSAL for measured outcomes after authorization. **Complete when:** timestamped, revision-bound measurements support each retained SC or a reviewed amendment explicitly changes it.

- [ ] AUD-017-019 (P2) Bind sovereignty validation to actual deployment intent.

**Basis / expected / observed / impact:** FR-009; SC-007; T014, T052; plan cloud/security claims. [CD](../../.github/workflows/cd.yml#L213) supplies only registry and `-Strict`; [resource comparison](../../scripts/verify-carveout.ps1#L121) is optional and not supplied. [Date validation](../../scripts/verify-carveout.ps1#L99) rejects dates older than six months but only warns for recent expiry, even under strict mode. Registry assertions and literal region tests do not establish effective resources or approvals.

**Developer:** Security/IaC owners must validate schema and approval dates consistently, fail strict warnings as promised, and bind a rendered deployment intent to the registry and allowed resource locations. Handle nested resource locations and the current constitutional model-hosting exception explicitly; do not widen data-service residency or activate FR-CAP-017-001. Preserve the current AU primary template constraint.

**Tester:** Extend existing [carve-out workflow tests](../../tests/devops/test_foundry_carveout_workflow.py#L1) and parameter fixtures. Positive: matching current approved AU intent passes. Negative: expired within six months, empty registry for a deployment, missing binding, invalid schema, non-AU data service and placeholder reviewer fail. Edge: timezone/date boundary and approved model-only exception require an explicit documented decision.

**Future validation:** V-SOV/V-PARAM and authorized V-IAC. **Complete when:** the executable gate's assertions match its description and the recorded approval evidence refers to effective deployment resources.

- [ ] AUD-017-020 (P2) Reconcile the historical contracts and checklist claims without erasing history.

**Basis / expected / observed / impact:** FR-002, FR-003, FR-008, FR-010; T025, T026, T030, T048, T053; R-001 through R-009 and CHK001 through CHK087 are individually assessed below. [Quality notes](checklists/requirements.md#L32) falsely say tooling appears only outside FRs; [CD error table](../feature/017-cd-pipeline/contracts/cd-workflow.md#L131) implies a wait timer cancels approval; research's serial fallback conflicts with the health deadline. Checked plan/task statements are not execution evidence.

**Developer:** Product owner, DevOps and technical writer must append an approved replacement/clarification map covering triggers, auth, retired jobs, required security, approval expiry, retry terminology, baseline schema, partial deployment, bootstrap, drift errors, cold-start timing and quickstart permissions. Keep every original task/checklist state unchanged unless a separately authorized lifecycle update records why. Update owned historical plan/research/data-model/contracts/quickstart consistently in future work, not in this audit.

**Tester:** Documentation reviewers should verify positive current examples, negative forbidden bypasses and edge-case decisions against the same source contracts and future executable tests. Check links, exact task IDs, all checklist dispositions, no operational claims backed solely by a checkbox, and no obsolete CI-main procedure presented as current deployment.

**Future validation:** V-DOC plus V-SUITE after authorized documentation work. **Complete when:** a maintainer can use the historical set to understand both what was replaced and which safeguards remain outstanding.

- [ ] AUD-017-021 (P2) Repair scoped persona/hypothesis evidence and preserve deferrals.

**Basis / expected / observed / impact:** PER-043, PER-044, PER-045, HYP-015, SCP-048, SCP-049, SCP-050, SCP-051, FR-CAP-017-001; T053 documentation verification. [HYP-015](spec.md#L215) links to a missing stub (N07). [Portfolio scores](../028-capstone-alignment/evidence/rubric-postfeature.md#L25) are not spec-017 per-criterion scores or proof of consultation on every change. Persona labels are declarations, not SME validation receipts.

**Developer:** Spec-017 and spec-028 evidence owners must create or correct the proposed hypothesis evidence location, record actual consultation provenance and spec-specific before/after criterion scores, and link persona validation records. If unavailable, explicitly label not tested/unverified instead of backfilling success. Preserve the PH/JP/BD and sovereign-region deferral preconditions and cross-spec ownership.

**Tester:** Review positive linked evidence with matching revision/actors, negative missing or aggregate-only evidence, and edge cases where mean improves but one criterion regresses. No country deployment or delegation is required to close a documentation-status correction; any future consultation or SME exercise needs separate authorization.

**Future validation:** V-DOC and later approved rubric evaluation. **Complete when:** links resolve, claims match the granularity of evidence, and deferred requirements are not reported as missing active implementations or silently promoted.

- [ ] AUD-017-022 (P2) Obtain reproducible execution and approval receipts for the checked validation tasks.

**Basis / expected / observed / impact:** T051, T052, T053, T054; SC-004, SC-006, SC-007, SC-009; plan PASS labels and quality readiness assertions. N08 found no scoped shellcheck/build/validate/test/quickstart execution evidence. Source-only inspection cannot confirm successful Azure provisioning, gates, isolation, human sign-off or unchanged historical CI behavior.

**Developer:** QA/release owner must identify the authorized revision, prerequisites, clean runner/tool versions, parameter selection, artifact hashes and approvers before running future validation. Record original failure results and subsequent fixes as new evidence, with sanitized run URLs/timestamps and explicit limits. Never rewrite old checked tasks as proof or treat this audit's text validation as product testing.

**Tester:** Execute V-LINT, V-SUITE, then authorized V-IAC/V-POLICY/V-REHEARSAL after prerequisite findings close. Positive: capture complete passing outputs; negative: retain failed gates and prove deployment blocked; edge: missing auth, quota/network issues or unavailable tools are blocked/unverified, not pass. Compare a named CI baseline before claiming regression freedom.

**Future validation:** The command catalogue below is instructional only. **Complete when:** each execution claim has revision-bound evidence and an accountable reviewer, and unresolved external facts remain labelled UNVERIFIED.

## Functional and Nonfunctional Coverage

| ID | Status | Expected versus observed evidence | Follow-ups |
| --- | --- | --- | --- |
| FR-001 | SUPERSEDED | Main trigger replaced explicitly; four services still declared in [azd](../../azure.yaml#L28), but four-service health/release proof is partial. | AUD-017-004, AUD-017-017, AUD-017-020 |
| FR-002 | CONFLICT | Old gate jobs explicitly retired; [claimed CI dependency scan](../031-simplify-cicd-pipeline/contracts/cd-workflow.md#L102) absent (N01), no staging prerequisite for production. | AUD-017-007, AUD-017-020 |
| FR-003 | UNVERIFIED | [Environment binding](../../.github/workflows/cd.yml#L40) exists; reviewers not inspected; no 72-hour expiry code found. | AUD-017-008 |
| FR-004 | PARTIAL | [Rollback](../../scripts/rollback.sh#L337) is wired for health failure but targets/discovery/web recovery are defective. | AUD-017-001, AUD-017-002, AUD-017-005 |
| FR-005 | PARTIAL | Separate named parameter artifacts and identities exist; selection, vault handling and effective isolation are incomplete. | AUD-017-006, AUD-017-010 |
| FR-006 | PARTIAL | [Schedule/matrix](../../.github/workflows/drift-detection.yml#L12) exists; parser can fail open and release context is not bound. | AUD-017-009, AUD-017-014, AUD-017-015 |
| FR-007 | PARTIAL | [Native issue/summary steps](../../.github/workflows/cd.yml#L365) exist; phase/service accuracy and issue-failure retention are incomplete. | AUD-017-014, AUD-017-016 |
| FR-008 | SUPERSEDED | Separate CI/CD retained; main-only/no-CI-edit constraints explicitly changed by [031](../031-simplify-cicd-pipeline/spec.md#L1). | AUD-017-017, AUD-017-020 |
| FR-009 | PARTIAL | [Literal AU tests](../../tests/devops/test_parameter_files.py#L63) and primary restriction exist; effective-intent/approval assurance incomplete. | AUD-017-006, AUD-017-019 |
| FR-010 | PARTIAL | [Two probes](../../.github/workflows/cd.yml#L230), 210-second possible duration and no internal-service verification contradict retained contract. | AUD-017-004, AUD-017-013 |
| FR-011 | PARTIAL | [Revision outputs](../../.github/workflows/cd.yml#L291) exist; baseline incomplete and disconnected from rollback. | AUD-017-003 |
| FR-012 | PARTIAL | [Critical issue](../../.github/workflows/cd.yml#L365) conditional exists; false bootstrap success can bypass escalation. | AUD-017-001, AUD-017-013, AUD-017-016 |
| FR-013 | PARTIAL | [Group creation](../../.github/workflows/cd.yml#L136), resource-group template and provision/deploy exist; effective params, recovery and bootstrap mutation safeguards incomplete. | AUD-017-005, AUD-017-006, AUD-017-011 |
| FR-014 | SUPERSEDED | [ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L31) explicitly replaces workflow OIDC; no evidence of current rotation/review completion. | AUD-017-008, AUD-017-020, AUD-017-022 |
| FR-015 | PARTIAL | [Per-environment non-cancelling lock](../../.github/workflows/cd.yml#L50) exists. Job limit now 60 minutes; this is not a durable FIFO guarantee for every burst of commits or a drift lock. | AUD-017-015, AUD-017-017, AUD-017-020 |
| NFR-RES (plan alias) | PARTIAL | Plan resilience obligation: retries/recovery exist but fail-open discovery and incomplete restoration defeat it. | AUD-017-001, AUD-017-005, AUD-017-013 |
| NFR-AUD (plan alias) | UNVERIFIED | Plan append-only trail claim: normal Actions logs, mutable files and issue text are not retention/immutability or approval evidence. | AUD-017-003, AUD-017-016, AUD-017-022 |
| NFR-WAF (plan alias) | PARTIAL | Plan reliability/security/operational excellence assessment is authored, not an executed WAF or deployment review. | AUD-017-008, AUD-017-010, AUD-017-019, AUD-017-022 |

The source has no separately numbered NFR list. The three NFR aliases above identify the historical plan's named NFR rows, not invented original requirement IDs. Its timing, sovereignty, security and extensibility constraints are also traced through FR/SC and checklist rows.

| ID | Status | Outcome assessment | Follow-ups |
| --- | --- | --- | --- |
| SC-001 | UNVERIFIED | Original main flow superseded; no 15-minute cohort evidence, current job limit 60 minutes. | AUD-017-018, AUD-017-020 |
| SC-002 | PARTIAL | Successful CI required, but dependency-security and staging prerequisites are not all connected. | AUD-017-007, AUD-017-008 |
| SC-003 | PARTIAL | Serial recovery health allows 440 seconds before restoration overhead; no five-minute measurements. | AUD-017-013, AUD-017-018 |
| SC-004 | UNVERIFIED | Distinct names are source-supported, actual isolation not demonstrated and secret/config wiring partial. | AUD-017-006, AUD-017-010, AUD-017-022 |
| SC-005 | UNVERIFIED | Weekly cron is correct; no run cadence/issue receipts, and silent parse failures can hide changes. | AUD-017-008, AUD-017-009, AUD-017-015 |
| SC-006 | SUPERSEDED | Identical CI/additive-only contract intentionally changed; no baseline-backed claim of functional regression freedom. | AUD-017-017, AUD-017-020, AUD-017-022 |
| SC-007 | UNVERIFIED | AU source declarations do not establish all deployed locations or effective policy/approval state. | AUD-017-019, AUD-017-022 |
| SC-008 | PARTIAL | Summaries/issues authored but phase/service detail and two-minute receipt measurements absent. | AUD-017-014, AUD-017-016, AUD-017-018 |
| SC-009 | PARTIAL | Three environment branches now exist in design; effective config/isolation and arbitrary environment extensibility not demonstrated. | AUD-017-006, AUD-017-017, AUD-017-022 |
| SC-010 | UNVERIFIED | No denominator, observation window or measured all-service rollback success rate. | AUD-017-018 |

### Acceptance Scenarios

Scenario labels below are audit-local references to the numbered scenarios within the [five original stories](spec.md#L8).

| Scenario | Status | Evidence and remaining obligation | Follow-ups |
| --- | --- | --- | --- |
| US1-AS1 | SUPERSEDED | Main promotion replaced; automatic matching-branch flow is authored, latency unverified. | AUD-017-018, AUD-017-020 |
| US1-AS2 | PARTIAL | Only API/web probed; internal health not established. | AUD-017-004 |
| US1-AS3 | PARTIAL | Success/push guard exists; not every named quality/security failure is blocking. | AUD-017-007, AUD-017-017 |
| US1-AS4 | PARTIAL | Environment lock exists; burst ordering/cancellation and recovery behavior need adversarial tests. | AUD-017-015, AUD-017-017 |
| US2-AS1 | SUPERSEDED | Chained production step retired; retained security assurance incomplete. | AUD-017-007, AUD-017-020 |
| US2-AS2 | PARTIAL | Ruff present; no connected dependency scan or specific finding report. | AUD-017-007, AUD-017-016 |
| US2-AS3 | UNVERIFIED | Required reviewer setting and authorization evidence not available. | AUD-017-008 |
| US2-AS4 | PARTIAL | No dependency on separate security/SLI workflows; native failure summaries incomplete. | AUD-017-007, AUD-017-016 |
| US3-AS1 | PARTIAL | Health guard calls defective recovery; not a verified four-service revert. | AUD-017-001, AUD-017-002, AUD-017-005 |
| US3-AS2 | PARTIAL | Serial health exists; exact restored versions/reason not surfaced in CD summary. | AUD-017-013, AUD-017-016 |
| US3-AS3 | PARTIAL | Green two-service health records incomplete baseline; failed persistence can still say success. | AUD-017-003, AUD-017-004, AUD-017-016 |
| US3-AS4 | PARTIAL | Exit-4/issue paths authored; discovery errors can incorrectly bypass them. | AUD-017-001, AUD-017-013, AUD-017-016 |
| US4-AS1 | PARTIAL | Staging file exists but its selection not wired to provision path. | AUD-017-006 |
| US4-AS2 | UNVERIFIED | No deployed negative cross-environment secret-access evidence. | AUD-017-010, AUD-017-022 |
| US4-AS3 | PARTIAL | Production region literal exists; effective tier/config and isolation not established. | AUD-017-006, AUD-017-019 |
| US5-AS1 | PARTIAL | Clean summary exists but invalid JSON can reach it. | AUD-017-009 |
| US5-AS2 | PARTIAL | Property table authored; filtering/nesting/false-value fidelity incomplete. | AUD-017-014 |
| US5-AS3 | PARTIAL | Labelled issue command exists; report retention and actual issue creation unverified. | AUD-017-014, AUD-017-022 |

### Edge Cases

| ID | Original case | Status and evidence | Follow-ups |
| --- | --- | --- | --- |
| EDGE-01 | New deployment while one runs | PARTIAL: per-environment lock authored; burst/recovery behavior not tested. | AUD-017-015, AUD-017-017 |
| EDGE-02 | Missing resource group | PARTIAL: create step exists; parameter/identity/bootstrap prerequisites incomplete. | AUD-017-006, AUD-017-011 |
| EDGE-03 | Health timeout | PARTIAL: finite curl timeout but wrong total window/incomplete service set. | AUD-017-004, AUD-017-013 |
| EDGE-04 | Rollback also fails | PARTIAL: issue path exists; false success and notification failure remain. | AUD-017-001, AUD-017-016 |
| EDGE-05 | Drift authentication failure | PARTIAL: login fails natively; subsequent authorization lookup errors become absence. | AUD-017-009 |
| EDGE-06 | Only some services unhealthy | PARTIAL: unprobed workers cannot trigger restore; web restore is skipped. | AUD-017-002, AUD-017-004 |
| EDGE-07 | OIDC token exchange failure | SUPERSEDED: credential exception; replacement login failure still needs evidence. | AUD-017-008, AUD-017-022 |
| EDGE-08 | Hung deployment blocks queue | CONFLICT: original default-six-hour text versus 20-minute task and current 60-minute job; no durable every-commit queue proof. | AUD-017-017, AUD-017-020 |
| EDGE-09 | Provision fails before service deploy | CONFLICT: source IaC and seeding can mutate app/data state during provision; no-service-mutation assumption false. | AUD-017-005 |
| EDGE-10 | Web returns 200 error content | IMPLEMENTED: body not inspected, matching explicit exclusion; acceptance of redirects is a separate defect. | AUD-017-004 |

### Clarifications and Amendments

CL labels follow the eight Session-1 and seven Pass-2 answers in source order; they are not new original IDs.

| ID | Decision / status | Evidence or follow-up |
| --- | --- | --- |
| CL-01 | OIDC authentication: SUPERSEDED operationally. | ADR-031; AUD-017-008, AUD-017-020. |
| CL-02 | 30s/three attempts/two minutes and six services: CONFLICT; four-service correction is explicit in Pass 2. | R-004 clarifies three total attempts; current checks differ; AUD-017-004, AUD-017-020. |
| CL-03 | pip-audit rather than safety: PARTIAL. | Dependency scan absent, not automatically replaced by separate security workflow; AUD-017-007. |
| CL-04 | Per-environment vault/app identities: PARTIAL; pipeline identity part SUPERSEDED. | Compute secret source and ADR-031; AUD-017-010. |
| CL-05 | GitHub-native notifications: PARTIAL. | Native steps present, accuracy/retention incomplete; AUD-017-014, AUD-017-016. |
| CL-06 | Per-environment queue: PARTIAL. | Non-cancelling lock exists; burst delivery semantics unproved; AUD-017-017. |
| CL-07 | Saturday 16:00 UTC drift: IMPLEMENTED as authored schedule. | [cron](../../.github/workflows/drift-detection.yml#L14); run cadence UNVERIFIED. |
| CL-08 | Production-only approval and 72h expiry: UNVERIFIED. | N03; AUD-017-008. |
| CL-09 | Four azd services, not six: IMPLEMENTED manifest; validation PARTIAL. | [services](../../azure.yaml#L28); AUD-017-004. |
| CL-10 | Four endpoint paths/ports: CONFLICT with private/headless deployment reachability. | [compute](../../infra/main.bicep#L1117), Dockerfile health instructions; AUD-017-004. |
| CL-11 | CD/drift/rollback file homes: IMPLEMENTED; filenames retained. | Current three implementation files; no missing-file finding. |
| CL-12 | Main workflow_run: SUPERSEDED by explicit branch routing. | [replacement](../031-simplify-cicd-pipeline/spec.md#L1); AUD-017-020. |
| CL-13 | Environment parameter files: PARTIAL; artifacts exist, wiring missing. | N04; AUD-017-006. |
| CL-14 | Default-six-hour hung-job bound: CONFLICT with subsequent explicit limits. | T048 and CD 60-minute limit; AUD-017-018, AUD-017-020. |
| CL-15 | Resource-group scope/bootstrap: PARTIAL. | Group create exists; permissions, mutation and configuration require work; AUD-017-005, AUD-017-006. |
| PER-043 | UNVERIFIED validation claim; cross-reference to AIIMS personas is authored. | [persona](spec.md#L207); AUD-017-021. |
| PER-044 | UNVERIFIED validation claim; technical actor catalogue reference is authored. | [persona](spec.md#L208); AUD-017-021. |
| PER-045 | IMPLEMENTED explicit placeholder/SME preconditions; not a validated non-AU persona. | [persona](spec.md#L209); AUD-017-021 preserves deferral. |
| HYP-015 | MISSING named evidence stub; spec-specific improvement/consultation UNVERIFIED. | [hypothesis](spec.md#L215), N07; AUD-017-021. |
| SCP-048 | IMPLEMENTED documented country deferral, not delivered variants. | [scope](spec.md#L223); no country deployment requested. |
| SCP-049 | IMPLEMENTED documented constitutional-change exclusion. | [scope](spec.md#L224); AUD-017-019 respects it. |
| SCP-050 | IMPLEMENTED authority deferral; arbitration execution UNVERIFIED. | [scope](spec.md#L225); AUD-017-020. |
| SCP-051 | IMPLEMENTED enabling-infrastructure label; not a capstone-outcome measurement. | [scope](spec.md#L226); AUD-017-021. |
| FR-CAP-017-001 | IMPLEMENTED as an explicit DEFERRED requirement, not an active country-topology feature. | [amendment](spec.md#L231); no missing-country-pipeline finding; AUD-017-019, AUD-017-021. |

## Original Task Coverage

Every row retains the exact checkbox from [the original task list](tasks.md#L29). Status assesses current scoped evidence, not whether a historical execution might once have succeeded. File consolidation is credited where behavior exists; retired job names are not treated as automatically missing.

| Original ID | Original checkbox | Status | Concrete evidence / remaining obligation | Follow-ups |
| --- | --- | --- | --- | --- |
| T001 | [x] | IMPLEMENTED | Test package and [conftest](../../tests/devops/conftest.py#L12) exist with shared YAML/JSON fixtures. | AUD-017-017 |
| T002 | [x] | IMPLEMENTED | [Staging file](../../infra/main.parameters.staging.json#L4) contains requested literal values. Runtime consumption is separately incomplete. | AUD-017-006 |
| T003 | [x] | PARTIAL | [Production file](../../infra/main.parameters.production.json#L4) exists; example-domain alert values are not production-ready operator settings. | AUD-017-006 |
| T004 | [x] | PARTIAL | [All flags parsed](../../scripts/rollback.sh#L77); missing values can bypass intended validation/exit mapping. | AUD-017-012 |
| T005 | [x] | PARTIAL | [CLI/env/group checks](../../scripts/rollback.sh#L123) exist; authenticated session and cross-target validation absent. | AUD-017-001, AUD-017-012 |
| T006 | [x] | PARTIAL | [Container discovery](../../scripts/rollback.sh#L153) uses wrong names/unsorted order; web helper is wrong and uncalled. | AUD-017-001, AUD-017-002 |
| T007 | [x] | PARTIAL | [Activate/deactivate](../../scripts/rollback.sh#L188) and ZIP command exist, but targets/artifact semantics do not restore the declared release. | AUD-017-001, AUD-017-002 |
| T008 | [x] | PARTIAL | [Health function](../../scripts/rollback.sh#L275) has 30/3/10 settings and exit 4, but serial calls and inaccessible targets violate recovery budget. | AUD-017-004, AUD-017-013 |
| T009 | [x] | PARTIAL | [Dry-run guard](../../scripts/rollback.sh#L212) occurs after Azure discovery; not zero Azure commands. | AUD-017-012 |
| T010 | [x] | IMPLEMENTED | [Logging helpers](../../scripts/rollback.sh#L44) and terminal summary emit contracted prefixes/status symbols. Accuracy of underlying outcomes is separate. | AUD-017-013, AUD-017-016 |
| T011 | [x] | IMPLEMENTED | [Shebang/strict mode](../../scripts/rollback.sh#L1) authored; read-only Git index inspection confirms mode 100755. Shellcheck execution unverified. | AUD-017-022 |
| T012 | [x] | CONFLICT | Consolidated [syntax tests](../../tests/devops/test_cd_workflow.py#L16) exist but still demand main/OIDC. | AUD-017-017 |
| T013 | [x] | CONFLICT | [Job tests](../../tests/devops/test_cd_workflow.py#L75) demand the removed deploy-staging job and old timeout. | AUD-017-017 |
| T014 | [x] | PARTIAL | [Schema/region tests](../../tests/devops/test_parameter_files.py#L12) cover literals, not rendered template compatibility/effective parameters. | AUD-017-006, AUD-017-019 |
| T015 | [x] | PARTIAL | [Isolation tests](../../tests/devops/test_parameter_files.py#L89) check names/text, not effective settings or denied secret access. | AUD-017-006, AUD-017-010 |
| T016 | [x] | SUPERSEDED | Main/OIDC top-level design explicitly replaced; [current workflow](../../.github/workflows/cd.yml#L18) remains separate and named cd. | AUD-017-020 |
| T017 | [x] | SUPERSEDED | Named deploy-staging replaced by [dynamic deploy](../../.github/workflows/cd.yml#L34), retaining success/push and per-env lock. | AUD-017-017, AUD-017-020 |
| T018 | [x] | SUPERSEDED | [Validated SHA checkout](../../.github/workflows/cd.yml#L66) and credential auth explicitly replace old action/auth prescriptions. | AUD-017-008, AUD-017-020 |
| T019 | [x] | PARTIAL | [Group creation/env setup](../../.github/workflows/cd.yml#L136) exists; file selection/bootstrap failures not fully handled. | AUD-017-006 |
| T020 | [x] | PARTIAL | [azd calls](../../.github/workflows/cd.yml#L224) exist, with seed/package dependencies; partial-mutation recovery incomplete. | AUD-017-005, AUD-017-006 |
| T021 | [x] | PARTIAL | [Health step](../../.github/workflows/cd.yml#L230) is parallel but two services, five attempts and wrong total budget. | AUD-017-004 |
| T022 | [x] | PARTIAL | [Revision capture](../../.github/workflows/cd.yml#L291) misidentifies web and omits two services from persisted JSON. | AUD-017-003 |
| T023 | [x] | PARTIAL | [Guard/call](../../.github/workflows/cd.yml#L355) exists; recovery can falsely succeed and deploy failures skip it. | AUD-017-001, AUD-017-005 |
| T024 | [x] | PARTIAL | [Status output](../../.github/workflows/cd.yml#L395) exists but phase/persistence failures can be misreported. | AUD-017-003, AUD-017-016 |
| T025 | [x] | SUPERSEDED | Old gate-job test shape explicitly retired with [removed jobs](../031-simplify-cicd-pipeline/contracts/cd-workflow.md#L102); replacement scan assurance still absent. | AUD-017-007, AUD-017-017 |
| T026 | [x] | SUPERSEDED | Old deploy-production structural assertion replaced by the [branch-based job](../../.github/workflows/cd.yml#L40); actual reviewer policy remains unverified. | AUD-017-008, AUD-017-017 |
| T027 | [x] | SUPERSEDED | Gate job intentionally removed by the [replacement contract](../031-simplify-cicd-pipeline/contracts/cd-workflow.md#L102), not missing by accident; its security rationale is unsupported. | AUD-017-007, AUD-017-020 |
| T028 | [x] | CONFLICT | [Ruff in CI](../../.github/workflows/ci.yml#L59); no pip-audit in current active workflows despite replacement claim (N01). | AUD-017-007 |
| T029 | [x] | PARTIAL | [Summary](../../.github/workflows/cd.yml#L409) is not the old gates-passed/gate-failures contract or an equivalent complete check report. | AUD-017-016, AUD-017-020 |
| T030 | [x] | SUPERSEDED | [Single environment job](../../.github/workflows/cd.yml#L34) replaces chained production; review/expiry obligations unresolved. | AUD-017-008, AUD-017-020 |
| T031 | [x] | PARTIAL | [Parameterized bootstrap/auth](../../.github/workflows/cd.yml#L94) exists; effective production settings/secret boundary incomplete. | AUD-017-006, AUD-017-010 |
| T032 | [x] | PARTIAL | [Shared deploy/health path](../../.github/workflows/cd.yml#L224) handles production but only checks two services. | AUD-017-004, AUD-017-005 |
| T033 | [x] | PARTIAL | [Shared capture](../../.github/workflows/cd.yml#L291) does not yield a restorable complete production baseline. | AUD-017-002, AUD-017-003 |
| T034 | [x] | PARTIAL | [Rollback tests](../../tests/devops/test_rollback_script.py#L1) search strings; no executable argument/dry-run assertions. | AUD-017-012, AUD-017-017 |
| T035 | [x] | MISSING | No scoped rollback workflow integration test or equivalent failure-chain assertions found (N02); caller is [CD](../../.github/workflows/cd.yml#L355). | AUD-017-005, AUD-017-017 |
| T036 | [x] | PARTIAL | [Bootstrap branch](../../scripts/rollback.sh#L377) and text test exist, but discovery failure is indistinguishable from genuine first run. | AUD-017-001, AUD-017-017 |
| T037 | [x] | PARTIAL | [Rolled-back summary](../../.github/workflows/cd.yml#L409) lacks exact service targets and accepts unverified skip as rollback. | AUD-017-013, AUD-017-016 |
| T038 | [x] | PARTIAL | [Critical issue step](../../.github/workflows/cd.yml#L365) exists; false-success suppression/delivery failure evidence unresolved. | AUD-017-001, AUD-017-016 |
| T039 | [x] | CONFLICT | Consolidated [drift syntax tests](../../tests/devops/test_drift_detection.py#L15) preserve schedule but demand retired id-token permission. | AUD-017-017 |
| T040 | [x] | PARTIAL | [Drift structure tests](../../tests/devops/test_drift_detection.py#L56) check broad presence, not exact parser/report/error assertions. | AUD-017-009, AUD-017-014, AUD-017-017 |
| T041 | [x] | IMPLEMENTED | [Weekly/manual definition](../../.github/workflows/drift-detection.yml#L10) present; OIDC permission portion explicitly superseded. | AUD-017-022 |
| T042 | [x] | SUPERSEDED | OIDC detail replaced; [matrix/environment](../../.github/workflows/drift-detection.yml#L22) and isolated job declaration retained. | AUD-017-008, AUD-017-020 |
| T043 | [x] | PARTIAL | [What-if arguments](../../.github/workflows/drift-detection.yml#L65) have group scope/full payload/JSON, but wrong release context and mixed diagnostics remain. | AUD-017-009, AUD-017-015 |
| T044 | [x] | PARTIAL | [Filter](../../.github/workflows/drift-detection.yml#L110) exists; unanchored regex, flattened fields and failure fallback can hide changes. | AUD-017-009, AUD-017-014 |
| T045 | [x] | PARTIAL | [Markdown/metrics](../../.github/workflows/drift-detection.yml#L150) authored; property fidelity, safe rendering and redaction incomplete. | AUD-017-014 |
| T046 | [x] | PARTIAL | [Conditional issue](../../.github/workflows/drift-detection.yml#L218) and clean summary exist; no persisted report on API failure or verified issue receipt. | AUD-017-014, AUD-017-022 |
| T047 | [x] | PARTIAL | [Error branch](../../.github/workflows/drift-detection.yml#L75) fails what-if; group/parse errors and retained diagnostics incomplete. True absence skip is explicitly superseded. | AUD-017-009, AUD-017-014 |
| T048 | [x] | CONFLICT | [60-minute timeout](../../.github/workflows/cd.yml#L45) differs from requested 20 minutes; no measured 15-minute result. | AUD-017-018, AUD-017-020 |
| T049 | [x] | IMPLEMENTED | [Drift timeout](../../.github/workflows/drift-detection.yml#L24) is 30 minutes. | AUD-017-022 |
| T050 | [x] | PARTIAL | [Environment declaration](../../.github/workflows/cd.yml#L40) enables native deployment tracking; no inspected explicit phase-accurate status publication beyond job outputs/summary. | AUD-017-016, AUD-017-022 |
| T051 | [x] | UNVERIFIED | [Script source](../../scripts/rollback.sh#L1) and mode inspected; no scoped shellcheck execution receipt (N08). | AUD-017-022 |
| T052 | [x] | UNVERIFIED | [Bicep entrypoint](../../infra/main.bicep#L1) and parameters inspected; build and Azure validate were not run and no scoped receipt found. | AUD-017-006, AUD-017-019, AUD-017-022 |
| T053 | [x] | UNVERIFIED | [Quickstart](../feature/017-cd-pipeline/quickstart.md#L48) contains procedures, not run/approval evidence; some steps now stale. | AUD-017-018, AUD-017-020, AUD-017-022 |
| T054 | [x] | CONFLICT | All-pass cannot describe [current literal main/OIDC/job assertions](../../tests/devops/test_cd_workflow.py#L49) against current YAML; historical test success is not disproved or established by this review. | AUD-017-017, AUD-017-022 |

## Historical Artifact and Evidence Assessment

### Research and Data Contracts

| Record | Status | Assessment / follow-up |
| --- | --- | --- |
| R-001 | SUPERSEDED | Main-only chaining replaced explicitly; separate workflow_run and success guard retained. AUD-017-020. |
| R-002 | PARTIAL | azd calls exist; selecting parameter files merely through an environment name is not wired/proven. Provision can mutate services/data. AUD-017-005, AUD-017-006. |
| R-003 | SUPERSEDED | OIDC replaced by ADR-031; actual credentials/permissions/rotation remain unverified. AUD-017-008. |
| R-004 | CONFLICT | Three total attempts give 110 seconds in parallel; serial fallback and current two-service/210-second checks do not satisfy the stated bound. AUD-017-004, AUD-017-013. |
| R-005 | PARTIAL | Reactivation/ZIP skeleton exists; discovery, artifact retrieval and known-good consumer are incomplete. Research `--services` suggestion is not in the binding interface; do not add selective rollback contrary to all-service consistency. AUD-017-001, AUD-017-002, AUD-017-003. |
| R-006 | PARTIAL | UTC/AEST/AEDT reasoning and schedule are authored correctly; parser/report behavior and execution unverified. AUD-017-009, AUD-017-014, AUD-017-015. |
| R-007 | PARTIAL | Literal environment files exist; production destinations, parameter selection and tier sizing not established. AUD-017-006. |
| R-008 | PARTIAL | Lock declaration exists; not a durable FIFO/every-commit execution proof, timeout documentation differs. AUD-017-017, AUD-017-020. |
| R-009 | CONFLICT | Duplicate jobs retired on unsupported CI scan premise; wait timers do not implement the promised rejection path. AUD-017-007, AUD-017-008, AUD-017-020. |
| Environment entity | PARTIAL | Name/group/parameter conventions exist; two-value enum conflicts with current dev branch; effective approval/configuration unverified. AUD-017-006, AUD-017-008, AUD-017-020. |
| Deployment Revision entity | PARTIAL | Unique environment baseline, git/run/timestamp identity and valid transitions not enforced by current mutable partial manifest. AUD-017-003, AUD-017-016. |
| Service Revision entity | CONFLICT | Web resource ID is not deployment ID/artifact; ingestion output named ingest; private/headless reachability differs from table. AUD-017-002, AUD-017-003, AUD-017-004. |
| Deployment Gate entity | SUPERSEDED | Chained gate topology retired; required security/approval evidence remains unresolved, not automatically fulfilled. AUD-017-007, AUD-017-008. |
| Drift Report entity | PARTIAL | Environment/time/run metadata authored; valid comparison and issue number/retained evidence not fully established. AUD-017-009, AUD-017-014. |
| Drifted Resource entity | PARTIAL | Create/Delete/Modify normalized superficially; unknown resource type/nesting and overly broad change acceptance need tests. AUD-017-014. |
| Property Change entity | PARTIAL | Expected/actual/path fields exist but false/null and nested differences are lossy. AUD-017-014. |
| Health Check Result entity | PARTIAL | Rollback prints attempts/status/time; CD lacks four-service results and complete error/timeout records. AUD-017-004, AUD-017-013, AUD-017-016. |

| Contract surface | Status | Assessment / follow-up |
| --- | --- | --- |
| CD trigger, permissions, repository identity variables | SUPERSEDED | Current explicit replacement differs; no reason to recreate old OIDC/main shape. AUD-017-020. |
| CD staging steps: checkout/auth/bootstrap/provision/deploy | PARTIAL | Current one-job equivalent exists; effective config and mutation recovery incomplete. AUD-017-005, AUD-017-006. |
| CD staging health, capture and recovery outputs | PARTIAL | Two checks, wrong/incomplete baseline and defective restoration. AUD-017-001, AUD-017-002, AUD-017-003, AUD-017-004. |
| CD automated gates and gates-passed/gate-failures | CONFLICT | Job retired but claimed replacement security not implemented; error details not equivalent. AUD-017-007, AUD-017-016. |
| CD production provisioning, health, baseline | PARTIAL | Shared branch job replaces named job; retained behavior has the same defects as staging. AUD-017-002, AUD-017-003, AUD-017-004, AUD-017-006. |
| CD manual approval and timeout | UNVERIFIED | No applied reviewers/expiry evidence; wait timer claim unsupported. AUD-017-008. |
| CD concurrency and timeout budget | PARTIAL | Per-env lock present; no every-commit guarantee or measured original timing. AUD-017-015, AUD-017-018. |
| CD error table and critical/manual recovery | CONFLICT | Deploy failure skips rollback; provision may already mutate; phase summaries inaccurate. AUD-017-005, AUD-017-016. |
| Rollback parameters and exit codes | PARTIAL | All flags and exit literals exist; auth/missing-value execution contract not proven. AUD-017-012. |
| Rollback discovery and operation order | PARTIAL | Wrong target names, unsorted revisions, no usable web history/artifact. AUD-017-001, AUD-017-002. |
| Rollback health and five-minute budget | PARTIAL | Serial checks violate budget; private/headless targets not reachable as assumed. AUD-017-004, AUD-017-013. |
| Rollback output format | IMPLEMENTED | Prefixes/status symbols authored; successful examples are not run output. AUD-017-016, AUD-017-022. |
| Rollback no secrets/no escalation/idempotence | PARTIAL | No sudo in rollback, quoted args; unused publishing-credential query and unpinned rediscovery conflict with stronger safety/idempotence assertions. AUD-017-001, AUD-017-002, AUD-017-012. |
| Rollback dependency availability | UNVERIFIED | Required tools/session are documented, not verified on a runner. AUD-017-022. |
| Drift trigger/matrix/auth | SUPERSEDED | Schedule and matrix retained; auth changed explicitly. Runtime scheduling/approval prerequisites unverified. AUD-017-008. |
| Drift what-if/filter contract | PARTIAL | Correct command family present; error normalization and stable desired state incomplete. AUD-017-009, AUD-017-015. |
| Drift issue format/metrics/next steps | PARTIAL | Template authored; exact property fidelity, redaction and retained API-error evidence missing. AUD-017-014. |
| Drift error table | CONFLICT | True unprovisioned skip explicitly replaced old failure; permission/parse errors must not inherit this exception. AUD-017-009. |
| Quickstart Azure/GitHub prerequisites | UNVERIFIED | OIDC setup operationally replaced; Contributor alone does not establish role-assignment/data-plane rights required by provisioning and seed hooks. AUD-017-006, AUD-017-008, AUD-017-010. |
| Quickstart verification 1 (merge/main) | SUPERSEDED | Main now CI-only; this is not a valid current deploy rehearsal. AUD-017-020. |
| Quickstart verification 2 (local endpoints) | UNVERIFIED | Commands authored; not proof of Azure reachability or worker health. AUD-017-004, AUD-017-022. |
| Quickstart verification 3 (dry-run) | PARTIAL | No-change wording weaker than task's no-Azure-calls promise; actual discovery still executes. AUD-017-012. |
| Quickstart verification 4 (drift dispatch) | UNVERIFIED | Instructions exist, no execution/issue receipt. AUD-017-022. |
| Quickstart flow, concurrency, rollback, env table, troubleshooting | CONFLICT | Describes retired promotion and optimistic recovery/config assumptions. Retain historical narrative and append accurate current instructions. AUD-017-020. |

### Plan and Review Claims

The [plan](../feature/017-cd-pipeline/plan.md#L22) is a design-stage self-assessment, not a signed review. Its historical principle labels also do not match all names/numbering in the current constitution.

| Plan row / claim | Original assertion | Status / evidence assessment |
| --- | --- | --- |
| 1 Life Safety | PASS | PARTIAL: rollback plan exists but restoration can be skipped falsely; AUD-017-001, AUD-017-005. |
| 2 Multi-Agent Coordination | PASS | CONFLICT: all-or-nothing rollback is asserted, not implemented atomically; AUD-017-002, AUD-017-003. |
| 3 Provenance | PASS | PARTIAL: validated checkout exists, but persisted SHA/revisions are incorrect/incomplete; AUD-017-003. |
| 4 Privacy/Security | PASS | PARTIAL: OIDC operationally superseded; vault/review obligations unfulfilled or unverified; AUD-017-008, AUD-017-010. |
| 5 Public alerts | N/A | IMPLEMENTED scope exclusion: pipeline is not the public-warning author. No public-alert validation claimed. |
| 6 Australian cloud | PASS | PARTIAL: source AU defaults/restrictions exist, effective resource/approval evidence incomplete; AUD-017-019. |
| 7 Resilience NFR | PASS | PARTIAL: retry/recovery defects remain; AUD-017-001, AUD-017-013. |
| 8 Audit Trail NFR | PASS | UNVERIFIED: normal Actions logs are not proof of immutable retention or captured approvals; AUD-017-022. |
| 9 WAF NFR | PASS | UNVERIFIED assessment outcome; authored design is not a performed WAF review; AUD-017-022. |
| 10 Quality Gates | PASS | CONFLICT: dependency/security chain incomplete; AUD-017-007. |
| Gate result / no violations | ALL PASS | CONFLICT: a design conclusion cannot certify the inspected implementation or current constitution mapping; AUD-017-020, AUD-017-022. |
| Task prerequisites/checkpoints | Complete / fully functional | UNVERIFIED execution; design files exist but end-to-end/first-red tests and approvals are not evidenced; AUD-017-017, AUD-017-022. |

### Quality Checklist: All 16 Original Checked Claims

Q labels identify source order because this checklist supplies no original item IDs. Original states are reproduced, not changed.

| Claim | Original checkbox | Status | Assessment / follow-up |
| --- | --- | --- | --- |
| Q01 No implementation details | [x] | CONFLICT | FRs prescribe workflow names, tools, paths and flags; AUD-017-020. |
| Q02 User value/business focus | [x] | IMPLEMENTED | Five role-based delivery/recovery/governance stories provide rationale. |
| Q03 Nontechnical stakeholders | [x] | PARTIAL | User stories accessible, detailed FR/tool prescriptions require technical context; AUD-017-020. |
| Q04 Mandatory sections complete | [x] | IMPLEMENTED | Scenarios, requirements, entities and measurable outcomes exist. |
| Q05 No clarification markers | [x] | IMPLEMENTED | No NEEDS CLARIFICATION markers in the original spec. |
| Q06 Testable/unambiguous | [x] | PARTIAL | Retry count, expiry, baseline and altered topology unresolved; AUD-017-020. |
| Q07 Measurable success criteria | [x] | PARTIAL | Numbers present; denominator/measurement windows missing; AUD-017-018. |
| Q08 Technology-agnostic SCs | [x] | CONFLICT | SCs prescribe Azure regions/GitHub issue mechanism; scope constraint should be distinguished from outcomes; AUD-017-020. |
| Q09 All acceptance scenarios defined | [x] | IMPLEMENTED | All 18 numbered scenarios authored; execution separately unverified. |
| Q10 Edge cases identified | [x] | IMPLEMENTED | Ten cases authored; coverage does not imply handling succeeds. |
| Q11 Clearly bounded scope | [x] | PARTIAL | Original exclusions explicit, current retirement boundaries need reconciliation; AUD-017-020. |
| Q12 Dependencies/assumptions identified | [x] | PARTIAL | Lists exist; parameter selection, worker reachability and seed/RBAC assumptions need correction; AUD-017-006, AUD-017-020. |
| Q13 Every FR has clear acceptance | [x] | PARTIAL | Expiry and persistence security cases not fully operationalized; AUD-017-008, AUD-017-017. |
| Q14 Primary flows covered | [x] | IMPLEMENTED | Stories cover deploy, gates, recovery, isolation and drift. |
| Q15 Feature meets measured outcomes | [x] | UNVERIFIED | No scoped measurements/deployments demonstrate this; AUD-017-018, AUD-017-022. |
| Q16 No implementation leakage | [x] | CONFLICT | Same concrete prescriptions as Q01; notes also reference obsolete safety tooling; AUD-017-020. |

The note "all 16 checklist items pass" is not supported as a current review conclusion. Its claim that ruff/azd/Bicep appear only in assumptions/constraints is directly contradicted by FR-002, FR-004, FR-005, FR-008, FR-010 and FR-013.

### Comprehensive Checklist: All 87 Original Unchecked Questions

Each question remains originally **[ ]** even where an answer is supported. These are requirement-quality questions, not 87 new product requirements. Missing decisions require owner disposition, not automatic scope expansion. Evidence references are the full spec/historical records and controlling paths above.

| ID | Original checkbox | Status | Scoped answer / follow-up |
| --- | --- | --- | --- |
| CHK001 | [ ] | PARTIAL | azd deploy ordering/partial-failure semantics not specified adequately; AUD-017-005, AUD-017-020. |
| CHK002 | [ ] | SUPERSEDED | Main-only filter replaced with explicit environment branches; AUD-017-020. |
| CHK003 | [ ] | IMPLEMENTED | Spec expressly excludes web content checks; real internal-service readiness remains separate; AUD-017-004. |
| CHK004 | [ ] | PARTIAL | Outputs/helper exist, durable complete producer-consumer baseline absent; AUD-017-003. |
| CHK005 | [ ] | PARTIAL | T036 defines first-run skip, but source conflates failure and absence; AUD-017-001. |
| CHK006 | [ ] | PARTIAL | Quickstart Contributor recommendation insufficient to establish all role/data-plane permissions; AUD-017-006, AUD-017-010. |
| CHK007 | [ ] | SUPERSEDED | Shared OIDC expressly replaced with environment credential auth; AUD-017-008. |
| CHK008 | [ ] | IMPLEMENTED | Historical drift contract supplies title, label, metrics/table/next steps; fidelity remains partial; AUD-017-014. |
| CHK009 | [ ] | SUPERSEDED | Production originally specified in contract, now a direct environment-branch run; AUD-017-020. |
| CHK010 | [ ] | PARTIAL | Logging documented, retention/immutability/approval receipt not established; AUD-017-016, AUD-017-022. |
| CHK011 | [ ] | PARTIAL | Dev branch now supported in source; config mechanism and future extension boundary unclear; AUD-017-006, AUD-017-020. |
| CHK012 | [ ] | IMPLEMENTED | Host-specific strategy documented in assumptions and rollback contract; actual restore flawed; AUD-017-002. |
| CHK013 | [ ] | PARTIAL | Four names hard-coded, no service-list parity assertion; AUD-017-004, AUD-017-017. |
| CHK014 | [ ] | PARTIAL | Overall successful CI required, advisory strict typing and separate security result differ; AUD-017-007. |
| CHK015 | [ ] | UNVERIFIED | Authorized reviewer membership/config not established; AUD-017-008. |
| CHK016 | [ ] | PARTIAL | Known-good intent clear but source selects second active revision, not health provenance; AUD-017-001, AUD-017-003. |
| CHK017 | [ ] | PARTIAL | Required report fields stated; stage/service/remediation completeness lacking; AUD-017-016. |
| CHK018 | [ ] | PARTIAL | Static issue guidance exists, phase-specific guidance incomplete; AUD-017-016. |
| CHK019 | [ ] | PARTIAL | Critical issue/manual intervention described; recovery skip can suppress it; AUD-017-001, AUD-017-016. |
| CHK020 | [ ] | PARTIAL | Separate groups/vaults intended, actual secret/identity denial not evidenced; AUD-017-010. |
| CHK021 | [ ] | PARTIAL | Extensibility wording lacks a measurable change boundary; AUD-017-020. |
| CHK022 | [ ] | IMPLEMENTED | PropertyChange path/expected/actual and report contract define granularity; implementation loses values; AUD-017-014. |
| CHK023 | [ ] | PARTIAL | R-004 uses sleep between completed attempts, but "retries" versus attempts needs unification; AUD-017-004, AUD-017-020. |
| CHK024 | [ ] | IMPLEMENTED | Pass 2 explicitly corrects six to four services; old log is historical, not a new six-service requirement. AUD-017-020. |
| CHK025 | [ ] | SUPERSEDED | Original gate entity/order mapped; chained jobs now retired, assurance still incomplete; AUD-017-007. |
| CHK026 | [ ] | PARTIAL | Manual approval follows automated gates in original model; branch model/expiry unresolved; AUD-017-008. |
| CHK027 | [ ] | PARTIAL | Notification intent covers failures, but current phase outcomes/delivery failures incomplete; AUD-017-016. |
| CHK028 | [ ] | CONFLICT | Parallel three attempts resolves old serial arithmetic; current two checks/five attempts violate deadline; AUD-017-004. |
| CHK029 | [ ] | PARTIAL | Historical budget includes restoration plus verification; source serial health exceeds it; AUD-017-013. |
| CHK030 | [ ] | PARTIAL | AU-only original wording consistent; current primary-only restriction and bounded constitutional carve-out need mapping; AUD-017-019, AUD-017-020. |
| CHK031 | [ ] | SUPERSEDED | Pipeline OIDC/no-long-lived-secret rule changed by explicit ADR; app-secret requirements remain; AUD-017-010, AUD-017-020. |
| CHK032 | [ ] | UNVERIFIED | Estimated phase budgets are not measured feasibility evidence; AUD-017-018. |
| CHK033 | [ ] | PARTIAL | 95% threshold exists, denominator/window absent; AUD-017-018. |
| CHK034 | [ ] | PARTIAL | Initial setup is documented but zero-manual-step cohort boundary unstated; AUD-017-018, AUD-017-020. |
| CHK035 | [ ] | PARTIAL | Gate-completion reference given, delivered-report timestamp/evidence absent; AUD-017-016, AUD-017-018. |
| CHK036 | [ ] | UNVERIFIED | No named CI regression baseline/receipt; literal no-edit scope superseded; AUD-017-022. |
| CHK037 | [ ] | PARTIAL | 18 scenarios usable, but identity, timing and failure fixtures incomplete; AUD-017-017. |
| CHK038 | [ ] | SUPERSEDED | Original full chain documented; current branch workflow intentionally differs; AUD-017-020. |
| CHK039 | [ ] | SUPERSEDED | Original production steps existed in contract; retired shape not a missing feature; AUD-017-020. |
| CHK040 | [ ] | PARTIAL | Clean report defined/implemented but parser failures can impersonate it; AUD-017-009. |
| CHK041 | [ ] | PARTIAL | Infra-only pushes run normal azd path; impact/compensation needs explicit decision; AUD-017-005. |
| CHK042 | [ ] | PARTIAL | Service-only pushes still provision and seed; behavior not a service-only transaction; AUD-017-005, AUD-017-006. |
| CHK043 | [ ] | PARTIAL | Expiry/retry policy missing; wait timer not rejection implementation; AUD-017-008. |
| CHK044 | [ ] | PARTIAL | Platform rerun is possible in principle, but same-SHA/idempotent recovery semantics untested; AUD-017-003, AUD-017-017. |
| CHK045 | [ ] | IMPLEMENTED | Drift contract next steps distinguish intentional IaC update from unintended restore; safe evidence incomplete; AUD-017-014. |
| CHK046 | [ ] | CONFLICT | Contract says deploy failure rolls back; health-only guard skips that case; AUD-017-005. |
| CHK047 | [ ] | IMPLEMENTED | Success/push guard rejects failed/cancelled/skipped/PR-origin CI at source level; tests to maintain in AUD-017-017. |
| CHK048 | [ ] | PARTIAL | Provision failure stops subsequent steps; partial mutation/remediation classification incomplete; AUD-017-005. |
| CHK049 | [ ] | PARTIAL | Exit codes declared but parser/auth/caller behavior not exercised; AUD-017-012, AUD-017-017. |
| CHK050 | [ ] | PARTIAL | Command failures stop jobs; discovery swallows network failures and phase reporting incomplete; AUD-017-001, AUD-017-016. |
| CHK051 | [ ] | PARTIAL | Distinct failure modes not faithfully represented in summary/status; AUD-017-016. |
| CHK052 | [ ] | PARTIAL | Manual intervention stated; resume/hold semantics need owner decision and tests; AUD-017-016, AUD-017-020. |
| CHK053 | [ ] | PARTIAL | Corrupt/missing baseline not safely distinguished from bootstrap; AUD-017-003. |
| CHK054 | [ ] | IMPLEMENTED | Historical report next steps define review/reconcile/close; no remediation execution claimed. |
| CHK055 | [ ] | PARTIAL | Provision modifies templates/data; partial-resource recovery not a no-op; AUD-017-005. |
| CHK056 | [ ] | IMPLEMENTED | Explicit HTTP-200 content exclusion retained; do not add body inspection unilaterally. |
| CHK057 | [ ] | PARTIAL | One running deployment enforced in YAML; durable FIFO/every-pending-commit promise not established; AUD-017-017, AUD-017-020. |
| CHK058 | [ ] | PARTIAL | First successful attempt wins; flapping readiness policy requires explicit decision; AUD-017-004. |
| CHK059 | [ ] | PARTIAL | Actions pinned, ubuntu-latest and CLI versions/dependencies still evolving; AUD-017-017, AUD-017-022. |
| CHK060 | [ ] | IMPLEMENTED | Fixed UTC schedule and accepted AEDT shift documented in R-006. |
| CHK061 | [ ] | PARTIAL | No shared release-context/coordination guard for drift and deploy; AUD-017-015. |
| CHK062 | [ ] | PARTIAL | Issue command fails but sanitized findings not retained/uploaded on failure; AUD-017-014. |
| CHK063 | [ ] | CONFLICT | Historical phase budgets, T048's 20 minutes and current 60 minutes differ; AUD-017-018, AUD-017-020. |
| CHK064 | [ ] | UNVERIFIED | GitHub outage/delayed-schedule recovery behavior and SLA evidence absent; AUD-017-018, AUD-017-022. |
| CHK065 | [ ] | PARTIAL | Summaries/prefixes exist, coherent release/run/service records incomplete; AUD-017-003, AUD-017-016. |
| CHK066 | [ ] | PARTIAL | Research cheaper staging claim not substantiated by effective tier/SKU selection; AUD-017-006, AUD-017-020. |
| CHK067 | [ ] | PARTIAL | Security contract authored; dry-run/auth/input and secret-discovery issues remain; AUD-017-002, AUD-017-012. |
| CHK068 | [ ] | UNVERIFIED | Approval identities and retention settings not inspected; AUD-017-008, AUD-017-022. |
| CHK069 | [ ] | PARTIAL | Lock pattern named but burst backlog/latency/delivery guarantees unmeasured; AUD-017-018. |
| CHK070 | [ ] | CONFLICT | API health is configuration-only, agents private and ingestion headless in IaC; Docker health commands do not prove pipeline reachability; AUD-017-004. |
| CHK071 | [ ] | PARTIAL | Setup action pinned but azd version contract not fixed/tested; AUD-017-017, AUD-017-022. |
| CHK072 | [ ] | PARTIAL | Environment/location parameters exist; effective selection and production tier unresolved; AUD-017-006. |
| CHK073 | [ ] | PARTIAL | Runner/toolchain setup exists; shell/seed/CLI availability is not a successful-run receipt; AUD-017-022. |
| CHK074 | [ ] | IMPLEMENTED | Required-reviewer setup documented in quickstart; applied policy still UNVERIFIED; AUD-017-008. |
| CHK075 | [ ] | PARTIAL | Subscription/quota/federation prerequisites listed; role-creation, data-plane and provider readiness not demonstrated; AUD-017-006, AUD-017-022. |
| CHK076 | [ ] | PARTIAL | Shared Bicep entrypoint documented; env-file selection and postprovision effects not captured fully; AUD-017-005, AUD-017-006. |
| CHK077 | [ ] | IMPLEMENTED | Historical R-004 explicitly resolves serial arithmetic through parallelism; current implementation still violates that resolution; AUD-017-004. |
| CHK078 | [ ] | CONFLICT | Original CI verification plus repeated security is explicit in R-009; later removal rests on missing CI scan; AUD-017-007. |
| CHK079 | [ ] | IMPLEMENTED | Pass-2 correction preserves history; do not reinterpret Session-1 six services as active scope. |
| CHK080 | [ ] | PARTIAL | Host rollback strategy documented, but artifact/baseline connection absent; AUD-017-002, AUD-017-003. |
| CHK081 | [ ] | IMPLEMENTED | Dedicated per-environment vault intent explicit; implementation not wired for retained app secrets; AUD-017-010. |
| CHK082 | [ ] | PARTIAL | Primary AU location restriction exists, but failover pipeline responsibility not specified/proven; AUD-017-019, AUD-017-020. |
| CHK083 | [ ] | IMPLEMENTED | FR-001 through FR-015 unique; capstone amendment separately identified. |
| CHK084 | [ ] | IMPLEMENTED | Scenario-to-FR trace supplied by this review; product assertions still partial. |
| CHK085 | [ ] | IMPLEMENTED | SC-to-behavior trace supplied above; measurements not implied. |
| CHK086 | [ ] | PARTIAL | Ten edge cases traced; provision/expiry/recovery conflicts remain; AUD-017-005, AUD-017-008. |
| CHK087 | [ ] | IMPLEMENTED | Priorities are assigned to stories, not individual original FRs; no requirement for invented FR priorities. |

## Future Validation Catalogue

**None of these commands were executed in this audit.** Run only after the named owner authorizes the next work, dependencies are fixed, and the selected environment is safe. Offline fake-command tests must not import/start production applications or reach Azure. New fixture cases in existing homes are proposed work, not current evidence.

| Code | Future command / procedure | Prerequisites and expected assertions |
| --- | --- | --- |
| V-CD | `pytest tests/devops/test_cd_workflow.py -q` | Configured Python test environment, PyYAML, maintained fixtures. Assert branch/event/SHA, required-check dependencies, parameter selection, phase failures, approvals and four-service results. |
| V-RB | `pytest tests/devops/test_rollback_script.py -q` | Bash-compatible runner; sentinel/fake az, curl, clock and artifact commands; no live credentials. Assert exact targets, exit codes, zero-command dry-run, idempotence, all-service restoration and deadlines. |
| V-DRIFT | `pytest tests/devops/test_drift_detection.py -q` | Fake CLI/issue client and pinned-shape what-if fixtures. Assert valid-clean only, property fidelity, unknown/error state, correct env/SHA and retained sanitized report. |
| V-PARAM | `pytest tests/devops/test_parameter_files.py -q` | Extended rendered-parameter/resource graph fixtures. Assert true effective environment isolation, AU locations, tier/identity mapping and no unresolved substitutions. |
| V-SUITE | `pytest tests/devops -q` | All maintained test dependencies installed; retired assumptions reconciled; fixtures offline. Zero unexpected failures/skips, plus mutation tests demonstrating the named safeguards fail when removed. |
| V-LINT | `shellcheck scripts/rollback.sh`; `actionlint .github/workflows/ci.yml .github/workflows/cd.yml .github/workflows/drift-detection.yml .github/workflows/staging-promotion.yml` | Installed pinned linters and applicable platform support. No shell/workflow errors; lint passing is not deployment evidence. |
| V-SOV | `pwsh -NoProfile -File scripts/verify-carveout.ps1 -RegistryPath "$REGISTRY_FIXTURE" -WhatIfPath "$WHAT_IF_FIXTURE" -Strict` | PowerShell, Python YAML dependency, synthetic approved/denied fixtures, no cloud session. Require valid binding and strict expiry/schema/location rejection. |
| V-IAC | `az bicep build --file infra/main.bicep --stdout`; `az deployment group validate --resource-group "$AUDIT_SANDBOX_RG" --template-file infra/main.bicep --parameters "@$RENDERED_PARAMS"` | Later explicit authorization; pinned CLI/Bicep, modules, isolated RG and scoped identity, correctly rendered environment file, policy/role prerequisites. Capture validation errors or successful receipts per environment; never infer live resources from compile success. |
| V-POLICY | `gh api "repos/$REPOSITORY/environments/production"`; inspect redacted authorized approval/denial/expiry run records | Repository admin consent and access; no secret values in logs. Demonstrate required reviewers, source/environment binding, expiry enforcement and independent read-only drift access. |
| V-REHEARSAL | Controlled release/failure rehearsals on approved environment branches; inspect with `gh run view "$RUN_ID" --repo "$REPOSITORY" --json headSha,event,conclusion,jobs,url` | Separate deployment authorization, known-good artifact, seeded sandbox, scoped identity and recovery operator. Measure CI-finish to healthy release, failure-to-restoration and report delivery; prove wrong-SHA/failed gates cannot deploy. CD has no workflow_dispatch; do not suggest manually dispatching it. |
| V-DOC | `npx --no-install markdownlint-cli2 specs/017-cd-pipeline/implementation-review-tasks.md specs/feature/017-cd-pipeline/implementation-review-tasks.md` and scoped text/link/ID validation | Installed documentation tooling; no product execution. Check all 54 original states, all requirement/scenario/checklist rows, 22 unchecked AUD tasks per report, resolving local source links and valid line bounds. |

## Completion Boundary

This review identifies source-supported implementation, explicit supersessions, retained defects and unverified claims. It does **not** certify feature completion, deployment readiness, cloud policy compliance, test success or human approval. Mechanical report validation is limited to text coverage, states, follow-up integrity, local links/line bounds and editor diagnostics on the two allowed files. Original task/checklist states remain historical evidence, not retrospective attestations.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 017 only. Three parallel technical reviews examined rollback
safety, CD workflow/gates, and drift/evidence. The source-completable destructive-operation defect was corrected:
routine CD no longer purges soft-deleted Cognitive Services accounts. It now performs a read-only check and fails with
an explicit recovery instruction when such accounts exist; irreversible purge remains a separately authorized action.

Validation: `python -m pytest tests/devops/test_cd_workflow.py -q` returned `19 passed`; `git diff --check` passed.

Remaining open work includes dedicated release baseline/artifact contracts, rollback discovery and web restoration,
four-service health, partial-deployment recovery, effective environment parameter selection, security/approval gates,
Key Vault isolation, drift fail-closed parsing, Azure policy/what-if/deployment evidence, and human/measurement proof.
