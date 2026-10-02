# Implementation Review: Historical 017 CD Pipeline Artifacts

## Scope and Limitations

**Review date:** 2026-09-11. **Source revision:** 5b44c249f00e0e4a13ea2579c8c33d06e2471d7a, confirmed against local HEAD.

This is a self-contained static review of this folder's seven historical design artifacts and the implementation obligations they describe. The governing [Review Contract](../../001-spec-implementation-audit/README.md#L12) was read in full. This folder has **no local spec.md or tasks.md**; its 54 original task obligations come from the [canonical task list](../../017-cd-pipeline/tasks.md#L1). All 54 originally have **[x]**. Their states are reproduced individually below, not retrospectively changed. The report also assesses all canonical requirements, scenarios, amendments and checklist claims needed to interpret those historical artifacts.

No other implementation audit reports were read or relied upon. No source, original documents, original checkboxes, audit index, branches or commits were changed. No delegation, application imports, product tests/builds, deployments, cloud queries or external approvals were performed. The only authorized writes are the two 017 review reports. No assertion here establishes a successful deployment, tested rollback, actual environment protection, secret rotation, measured performance or deployed identity policy.

**Coverage:** seven historical artifacts, 54 original task rows, 15 FRs plus FR-CAP-017-001, 10 SCs, 18 acceptance scenarios, 10 edge cases, 15 clarification answers, 16 checked quality claims and 87 unchecked comprehensive questions. **22 unchecked AUD-017 remediation tasks** are fully described here. Shared AUD IDs denote the same remediation work across both 017 reports; no other audit is needed to implement or test these tasks.

### Inputs Read in Full

| Artifact | Local scope and claims |
| --- | --- |
| [plan.md](plan.md#L1) | 83 lines: four-service/two-environment architecture, performance budgets, ten constitution/quality rows, ALL PASS assertion, file inventory and no-violations claim. |
| [research.md](research.md#L1) | 176 lines: R-001 through R-009, rejected alternatives, trigger/auth/parameter/health/recovery/drift/concurrency/gate decisions. |
| [data-model.md](data-model.md#L1) | 179 lines: Environment, Deployment Revision, Service Revision, Deployment Gate, Drift Report, Drifted Resource, Property Change, Health Check Result. |
| [quickstart.md](quickstart.md#L1) | 180 lines: Azure/GitHub prerequisites, file list, four verification procedures, pipeline/concurrency/recovery diagrams, environment table and troubleshooting. |
| [contracts/cd-workflow.md](contracts/cd-workflow.md#L1) | 154 lines: trigger, permissions/variables, three jobs and outputs, concurrency, eight failure modes and timeout budget. |
| [contracts/rollback-script.md](contracts/rollback-script.md#L1) | 138 lines: all flags, five exit codes, discovery/restoration sequence, logging examples, security/idempotence, dependencies and five-minute budget. |
| [contracts/drift-detection-workflow.md](contracts/drift-detection-workflow.md#L1) | 158 lines: weekly/manual trigger, auth, environment matrix, what-if/filter/report/issue contracts, failure handling and ignore list. |
| [canonical spec](../../017-cd-pipeline/spec.md#L1) | All 233 lines, including both clarification passes, persona/hypothesis/scope additions and deferred country-topology requirement. |
| [canonical tasks](../../017-cd-pipeline/tasks.md#L1) | All 282 lines, exact T001 through T054 states, prerequisites, checkpoint and execution claims. |
| [quality checklist](../../017-cd-pipeline/checklists/requirements.md#L1) | All 16 originally checked assertions and explanatory notes. |
| [comprehensive checklist](../../017-cd-pipeline/checklists/comprehensive.md#L1) | All 87 originally unchecked questions, including high-priority arithmetic/gate ambiguities. |

There are no additional local amendment, review-transcript or execution-evidence files in either input inventory. Embedded amendments are assessed below. Related source inspection followed the current CI/CD/drift workflows, their scripts/hooks, configuration/IaC, original DevOps test assertions, explicit spec-031 replacement decisions, current constitution and linked portfolio rubric records. Code-review, code-commenting and Bicep instructions were loaded. Azure validation guidance supplied review criteria only; its operational workflow was not run.

## Evidence Statuses and Supersession

| Status | Meaning |
| --- | --- |
| IMPLEMENTED | Full scoped authored behavior/artifact supported by inspected source; runtime success not implied. |
| PARTIAL | Some behavior exists; a specific obligation is absent or contradicted. |
| MISSING | Required artifact/behavior absent after a scoped search described below. |
| CONFLICT | Documents, task instructions, decisions or implementation disagree. |
| UNVERIFIED | Source cannot establish execution, outcome, approval or deployed state. |
| SUPERSEDED | Explicit repository evidence replaces/retires the requirement; not a missing-file inference. |

- [Spec 031](../../031-simplify-cicd-pipeline/spec.md#L1) explicitly replaces main-to-staging/chained promotion with dev/staging/production branch routing. Its [replacement CD contract](../../031-simplify-cicd-pipeline/contracts/cd-workflow.md#L102) removes deployment-gates and deploy-production jobs. Their old names must not be recreated merely to satisfy historical text.
- [ADR-031](../../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L31) expressly accepts a time-bound per-environment service-principal credential exception. This operationally supersedes workflow OIDC, not the retained application-secret isolation requirement. The ADR's existence does not prove rotation or governance review occurred.
- [Spec-031 research R6](../../031-simplify-cicd-pipeline/research.md#L83) enumerates retirement of spec-029 workflows, reusable jobs, composite actions and pipeline tooling. No active reusable call was found. This is explicit retirement, not unexplained implementation loss.
- Four-service health remains in the [replacement CD step contract](../../031-simplify-cicd-pipeline/contracts/cd-workflow.md#L91). [Research R4](../../031-simplify-cicd-pipeline/research.md#L63) explicitly retains rollback. Spec 031 expands automatic rollback to production but does not authorize removing internal-service health or the restorable release requirement.
- The [replacement drift contract](../../031-simplify-cicd-pipeline/contracts/drift-detection.contract.md#L67) permits warning/skip for genuine unprovisioned resource groups. It does not permit an authorization or parser failure to masquerade as a clean comparison.
- The removed-gates rationale says lint and `pip-audit` were already enforced by CI. Lint is present; no active workflow dependency audit was found. This is a retained assurance gap, distinct from the intentional topology change.

## Actual Workflow and Dependency Trace

1. [CI](../../../.github/workflows/ci.yml#L1) runs on push to main/dev/staging/production and PRs to main. Its [test step](../../../.github/workflows/ci.yml#L131) selects contract/integration tests, not the original DevOps suite. [Strict typing](../../../.github/workflows/ci.yml#L116) has a later explicit advisory exception.
2. [CD](../../../.github/workflows/cd.yml#L20) consumes successful, push-origin CI for environment branches only. [Checkout](../../../.github/workflows/cd.yml#L66) pins upstream head SHA. One dynamic environment job uses per-environment concurrency and a 60-minute timeout, not the historical three-job model.
3. [Identity/bootstrap](../../../.github/workflows/cd.yml#L94) uses an environment credential for Azure login and separate azd login, creates the group, then sets basic azd variables. It does not explicitly select the authored environment parameter file.
4. CD [purges soft-deleted Cognitive Services resources](../../../.github/workflows/cd.yml#L190), invokes the registry verifier, then calls provision/deploy. [azure.yaml](../../../azure.yaml#L15) runs a postprovision [shell hook](../../../scripts/seed-database.sh#L1), which invokes [seed_loader](../../../scripts/seed_loader.py#L643). That path upserts data and creates blob containers; provision is not guaranteed to be mutation-free for applications/data. Web packaging also runs its build hook.
5. [Health](../../../.github/workflows/cd.yml#L230) probes only API/web. [Revision capture and manifest update](../../../.github/workflows/cd.yml#L291) are incomplete. [Recovery](../../../.github/workflows/cd.yml#L355) runs only after a failed health step, calls the legacy rollback script without pinned targets, and conditionally creates a critical issue. [Status](../../../.github/workflows/cd.yml#L395) can misclassify other phases.
6. [Rollback](../../../scripts/rollback.sh#L337) performs discovery/restoration, optionally skips web, may return a false first-run success, then checks services serially. It does not consume the manifest written by CD.
7. [Drift](../../../.github/workflows/drift-detection.yml#L12) is weekly/manual, staging+production only, environment-bound and independent per matrix entry. It reads default-branch IaC, explicitly selects the environment file, parses what-if using inline jq and posts Markdown. It has no deployed-SHA binding or coordination with CD's lock.
8. [Security-scan](../../../.github/workflows/security-scan.yml#L8) is a separate workflow; [staging-promotion](../../../.github/workflows/staging-promotion.yml#L27) is scheduled/manual with static/smoke/runtime jobs and a local tag. Neither is a dependency of current CD. A comment saying promotion gates CD is not an executable relationship or successful gate result.

### Scoped Searches Supporting Negative Findings

| Search | Scope, terms and observed result |
| --- | --- |
| N01 | Complete active workflow inventory plus `pip-audit`, `deployment-gates`, `gates-passed`, `gate-failures`, `workflow_call`, local `_reusable` references: none found. Explicit retirement explains topology absence, not retained missing security. |
| N02 | `tests/**` searched for deployment-gates/deploy-staging/AZURE_CREDENTIALS/rollback.sh/pip-audit; full original DevOps modules/fixtures read. Consolidated syntax/parameter/drift tests exist; no equivalent rollback workflow integration or replacement gate/production assertion found. |
| N03 | `.github/**` searched for 4320-minute timeout, required_reviewers and wait_timer; full CD/drift/protection records inspected. No 72-hour expiry implementation or applied production policy receipt found. Actual GitHub settings were not queried. |
| N04 | Full CD, azd manifest and base/staging/production parameters read. No selector connects environment files to CD provision; drift names them explicitly. This is a source wiring gap, not a live-environment observation. |
| N05 | CD, rollback and known-good helper read; baseline/revision consumers traced. No complete four-service persisted baseline, rollback consumer, web artifact download or fail-closed discovery distinction found. |
| N06 | Main Bicep vault/identity/secret/module references searched; compute declarations read. Only a conditional signing vault is wired; registry secrets are inline values. No claim that manually provisioned Azure vaults are absent. |
| N07 | Reading the named HYP-HYP-015 evidence path failed; the spec-028 evidence folder was searched for HYP-015/spec-017. Only aggregate rubric references were found, not the promised stub or per-spec consultation record. |
| N08 | Full eleven-input inventory contains no execution/approval/timing receipts supporting the checked validation tasks or plan ALL PASS. Authored examples are not transcripts. |

## Priority-Ordered Findings

| Priority | Expected / observed / impact | Evidence | Task |
| --- | --- | --- | --- |
| P1 | Recovery must restore real resources; wrong constructed names and swallowed CLI errors can return bootstrap success without restoring anything. | [discovery](../../../scripts/rollback.sh#L153), [skip](../../../scripts/rollback.sh#L377), [actual names](../../../infra/main.bicep#L1007) | AUD-017-001 |
| P1 | Web needs a known-good package; no explicit target means unconditional skip, and deployment IDs are not ZIP artifacts. | [unused history helper](../../../scripts/rollback.sh#L172), [web restore](../../../scripts/rollback.sh#L243) | AUD-017-002 |
| P1 | A complete environment release must be durable; current capture omits services, uses web resource identity/default-branch commit context and has no recovery consumer. | [capture](../../../.github/workflows/cd.yml#L291), [update](../../../.github/workflows/cd.yml#L331), [helper](../../../scripts/web-coverage/known-good.py#L99) | AUD-017-003 |
| P1 | Four services need reliable health; only two are checked, API is not transitive, TLS is bypassed and timing can reach 210 seconds. | [health](../../../.github/workflows/cd.yml#L230), [API](../../../apps/api/app/api/health.py#L10) | AUD-017-004 |
| P1 | Partial deploy failures require a recovery decision; health-only guard skips them while provision also mutates app/data state. | [commands](../../../.github/workflows/cd.yml#L224), [guard](../../../.github/workflows/cd.yml#L355), [hook](../../../azure.yaml#L15) | AUD-017-005 |
| P1 | Environment settings must be selected, not just authored; CD and drift have different parameter paths and production tier is not explicitly bound. | [CD setup](../../../.github/workflows/cd.yml#L143), [base file](../../../infra/main.parameters.json#L4), [tier](../../../infra/main.bicep#L121) | AUD-017-006 |
| P1 | Retired duplicate gates require an equivalent security guarantee; claimed CI dependency scan is absent and parallel workflows are disconnected. | [replacement rationale](../../031-simplify-cicd-pipeline/contracts/cd-workflow.md#L102), [CI lint](../../../.github/workflows/ci.yml#L59), N01 | AUD-017-007 |
| P1 | Approval/expiry must be enforced and evidenced; dynamic environment alone proves neither, and scheduled drift inherits the production environment gate. | [CD environment](../../../.github/workflows/cd.yml#L40), [drift environment](../../../.github/workflows/drift-detection.yml#L30) | AUD-017-008 |
| P1 | Clean drift must mean valid comparison; malformed output becomes empty changes and access denial becomes unprovisioned. | [group lookup](../../../.github/workflows/drift-detection.yml#L57), [parser fallback](../../../.github/workflows/drift-detection.yml#L134) | AUD-017-009 |
| P1 | Application-secret isolation survives credential exception; inline registry passwords and conditional signing vault do not satisfy the full contract. | [secret](../../../infra/main.bicep#L1023), [conditional vault](../../../infra/main.bicep#L224) | AUD-017-010 |
| P1 | Ordinary bootstrap should not silently destroy recovery resources; pre-gate purge is automatic for all matching deleted Cognitive Services kinds. | [purge](../../../.github/workflows/cd.yml#L190), [constitution](../../../.specify/memory/constitution.md#L249) | AUD-017-011 |
| P2 | Dry-run must make no Azure calls; discovery runs first, missing values can break parsing and auth exit mapping is incomplete. | [parser](../../../scripts/rollback.sh#L77), [dry-run position](../../../scripts/rollback.sh#L212) | AUD-017-012 |
| P2 | Five-minute restore budget includes health; serial checks alone allow 440 seconds. | [health loop](../../../scripts/rollback.sh#L400) | AUD-017-013 |
| P2 | Drift evidence must preserve exact values; false becomes null, nested deltas/filter precision and safe retained reports are incomplete. | [parser](../../../.github/workflows/drift-detection.yml#L110), [report](../../../.github/workflows/drift-detection.yml#L150) | AUD-017-014 |
| P2 | Drift should compare stable deployed intent; default-branch checkout and no deployment coordination can create false findings. | [drift checkout](../../../.github/workflows/drift-detection.yml#L33), [CD lock](../../../.github/workflows/cd.yml#L50) | AUD-017-015 |
| P2 | Status must describe the failed phase; current output can say success after baseline failure or critical rollback failure when no rollback ran. | [status](../../../.github/workflows/cd.yml#L395), [summary](../../../.github/workflows/cd.yml#L409) | AUD-017-016 |
| P2 | Tests should enforce retained behavior; original assertions expect retired layout and mostly inspect strings, outside CI's selected suite. | [old tests](../../../tests/devops/test_cd_workflow.py#L49), [CI selection](../../../.github/workflows/ci.yml#L131) | AUD-017-017 |
| P2 | Numeric success claims need evidence; no latency series, rollback denominator or observation window is scoped here. | [original outcomes](../../017-cd-pipeline/spec.md#L138), [timeout](../../../.github/workflows/cd.yml#L45) | AUD-017-018 |
| P2 | Sovereignty assurance must bind intent to approval; optional what-if binding is not supplied and strict near-expiry warning does not fail. | [call](../../../.github/workflows/cd.yml#L213), [date handling](../../../scripts/verify-carveout.ps1#L99) | AUD-017-019 |
| P2 | Historical contract set should identify supersession and unresolved decisions; its optimistic pass/timeout/health claims are inconsistent. | [plan](plan.md#L22), [error table](contracts/cd-workflow.md#L131), [quality notes](../../017-cd-pipeline/checklists/requirements.md#L32) | AUD-017-020 |
| P2 | Persona/hypothesis assertions need matching evidence; named stub absent and aggregate rubric scores do not prove this spec's improvement. | [HYP-015](../../017-cd-pipeline/spec.md#L215), [portfolio](../../028-capstone-alignment/evidence/rubric-postfeature.md#L25) | AUD-017-021 |
| P2 | Checked verification tasks require receipts; no shellcheck, build, validate, test, quickstart or approval execution is established. | [T051 onward](../../017-cd-pipeline/tasks.md#L171), N08 | AUD-017-022 |

## Local Artifact Assessments

### Plan Claims

The [plan's ten-row assessment](plan.md#L22) is authored design material. Its historical principle names/numbering do not all match the current constitution. ALL PASS is not a current implementation or approval result.

| Plan row / claim | Original assertion | Assessment |
| --- | --- | --- |
| 1 Life Safety | PASS | PARTIAL: rollback deliverable exists but false-success recovery remains; AUD-017-001, AUD-017-005. |
| 2 Multi-Agent Coordination | PASS | CONFLICT: atomic/all-or-nothing recovery is claimed, not established by current operations; AUD-017-002, AUD-017-003. |
| 3 Provenance | PASS | PARTIAL: pinned checkout exists but persisted complete release identity does not; AUD-017-003. |
| 4 Privacy/Security | PASS | PARTIAL: workflow auth explicitly superseded; application vault/approval obligations incomplete; AUD-017-008, AUD-017-010. |
| 5 Public alerts | N/A | IMPLEMENTED scope exclusion: this pipeline does not author public alerts. |
| 6 Australian cloud | PASS | PARTIAL: regional source settings exist, effective/deployed-state assurance incomplete; AUD-017-019. |
| 7 Resilience NFR | PASS | PARTIAL: retry/restore logic has retained defects; AUD-017-001, AUD-017-013. |
| 8 Audit Trail NFR | PASS | UNVERIFIED: ordinary Actions logs/issue records do not prove immutable retention or approvals; AUD-017-022. |
| 9 WAF NFR | PASS | UNVERIFIED as a performed assessment; design discussion is not a review receipt; AUD-017-022. |
| 10 Quality Gates | PASS | CONFLICT: dependency-security enforcement is not connected; AUD-017-007. |
| Gate result/no violations | ALL PASS | CONFLICT with retained source defects and current policy mapping; AUD-017-020, AUD-017-022. |
| Structure/performance/no application changes | Design complete | PARTIAL: file inventory and estimates authored; source evolution includes seed/package hooks and changed health hosting. AUD-017-005, AUD-017-018, AUD-017-020. |

### Research Decisions

| Record | Status | Expected versus current evidence / follow-up |
| --- | --- | --- |
| R-001 | SUPERSEDED | Main-only trigger changed explicitly; separate workflow_run/success guard retained. AUD-017-020. |
| R-002 | PARTIAL | azd provision/deploy are called; environment-name-based parameter selection is not implemented as described; provisioning can mutate apps/data. AUD-017-005, AUD-017-006. |
| R-003 | SUPERSEDED | OIDC exception explicitly accepted by ADR-031; actual credentials, rotation and permissions unverified. AUD-017-008. |
| R-004 | CONFLICT | Three total attempts in parallel yield 110s; serial fallback and current five-attempt/two-service path violate the resolution. AUD-017-004, AUD-017-013. |
| R-005 | PARTIAL | Reactivation/ZIP skeleton exists; no durable consumer, correct history or web package. Research's `--services` suggestion is not in the binding interface and must not introduce partial rollback contrary to version consistency. AUD-017-001, AUD-017-002, AUD-017-003. |
| R-006 | PARTIAL | What-if/schedule/AEDT explanation authored; comparison/filter/report safety incomplete. AUD-017-009, AUD-017-014, AUD-017-015. |
| R-007 | PARTIAL | Two literal files exist; selection, production destinations and effective tier/SKU claims are not established. AUD-017-006. |
| R-008 | PARTIAL | Environment lock exists; every queued commit/FIFO and timing claims are not proven. AUD-017-017, AUD-017-020. |
| R-009 | CONFLICT | Gate topology retired on false existing-CI-scan premise; 72h auto-reject mechanism still absent. AUD-017-007, AUD-017-008. |

### Data Model Invariants

| Entity | Status | Concrete assessment / follow-up |
| --- | --- | --- |
| Environment | PARTIAL | Enum only staging/production is historical; dev exists in current design. Resource naming present, effective parameter selection/approval unverified. AUD-017-006, AUD-017-008, AUD-017-020. |
| Deployment Revision | PARTIAL | One known-good per environment, full SHA/run/timestamp tuple and forward-only transitions not enforced by the partial mutable coverage manifest. AUD-017-003, AUD-017-016. |
| Service Revision | CONFLICT | Web resource ID is not deployment ID/package; ingestion output uses ingest; worker reachability differs from fixed endpoint table. AUD-017-002, AUD-017-003, AUD-017-004. |
| Deployment Gate | SUPERSEDED | Original ordered four-stage model retired operationally; security and authorization assurances remain unresolved. AUD-017-007, AUD-017-008, AUD-017-020. |
| Drift Report | PARTIAL | Environment/time/run/report text exist; validated comparison, stored issue identity and failure evidence not fully maintained. AUD-017-009, AUD-017-014. |
| Drifted Resource | PARTIAL | Flat normalized entries exist; type/nesting/allowed-change semantics need real-shaped fixtures. AUD-017-014. |
| Property Change | PARTIAL | Path/expected/actual emitted but boolean false/null and nested details are lossy. AUD-017-014. |
| Health Check Result | PARTIAL | Rollback prints attempt/code/timing, CD lacks complete four-service structured results and coherent timeout/error records. AUD-017-004, AUD-017-013, AUD-017-016. |

### Contract and Quickstart Obligations

| Surface | Status | Evidence assessment / follow-up |
| --- | --- | --- |
| CD trigger, permissions and repository variables | SUPERSEDED | Explicit spec-031/ADR changes, not accidental loss. Retain historical interface and replacement mapping; AUD-017-020. |
| CD staging checkout/auth/bootstrap/provision/deploy | PARTIAL | One-job equivalent exists but selection and mutation recovery incomplete; AUD-017-005, AUD-017-006. |
| CD staging health/revision/recovery outputs | PARTIAL | Two checks and incomplete baseline do not satisfy four-service recovery; AUD-017-001, AUD-017-002, AUD-017-003, AUD-017-004. |
| CD gates and gates-passed/gate-failures outputs | CONFLICT | Old job retired; asserted CI security equivalent not present and reporting not equivalent; AUD-017-007, AUD-017-016. |
| CD production provision/health/baseline | PARTIAL | Shared environment job replaces named job; same retained defects apply; AUD-017-003, AUD-017-004, AUD-017-006. |
| CD production reviewers and auto-reject | UNVERIFIED | Settings not queried, no 72h implementation found; wait timer is not evidence of rejection; AUD-017-008. |
| CD concurrency and timing | PARTIAL | One-running-job declaration exists, not every-commit FIFO or measured 15-minute staging; AUD-017-015, AUD-017-018. |
| CD error table | CONFLICT | Service-deploy failure skips rollback; provisioning may already change apps/data; phase statuses inaccurate; AUD-017-005, AUD-017-016. |
| Rollback flags and five exit codes | PARTIAL | Tokens exist but missing values/session failure paths do not fully meet contract; AUD-017-012. |
| Rollback discovery | PARTIAL | Wrong names, unsorted active list, web helper incorrectly queries publishing credentials and is unused; AUD-017-001, AUD-017-002. |
| Rollback activate/deactivate/ZIP operations | PARTIAL | Commands exist without complete known-good target/artifact wiring; AUD-017-001, AUD-017-002, AUD-017-003. |
| Rollback verification and five-minute budget | PARTIAL | Serial 440s health and private/headless targets contradict budget/availability; AUD-017-004, AUD-017-013. |
| Rollback stdout/stderr examples | IMPLEMENTED | Prefixes/status symbols authored; example transcripts are not observed executions; AUD-017-016, AUD-017-022. |
| Rollback no-secrets/no-escalation/idempotence | PARTIAL | No sudo and quoted values supported; unused credential-discovery query, unpinned discovery and dry-run side effects require repair; AUD-017-001, AUD-017-002, AUD-017-012. |
| Rollback dependency availability | UNVERIFIED | az/curl/jq/session prerequisites documented; no successful runner check recorded; AUD-017-022. |
| Drift schedule/auth/matrix | SUPERSEDED | Schedule/matrix retained; credential path changed explicitly. Runtime approval and cadence unverified; AUD-017-008. |
| Drift what-if/filter list | PARTIAL | Command family/list exists but source envelope/errors/regex precision not safe; AUD-017-009, AUD-017-014. |
| Drift issue title/label/body/summary/next steps | PARTIAL | Template present; property fidelity, escaping/redaction and retained failure evidence missing; AUD-017-014. |
| Drift errors/clean result | CONFLICT | Actual absence skip explicitly replaced old fail behavior; permission/parse errors must remain distinct; AUD-017-009. |
| Quickstart Azure prerequisites | UNVERIFIED | Identity/quota setup is a procedure, not deployed evidence; Contributor does not establish role-assignment and seed data-plane authority; AUD-017-006, AUD-017-010. |
| Quickstart GitHub prerequisites | SUPERSEDED | OIDC variables replaced; required-reviewer and label existence unverified. The critical label is also needed by recovery; AUD-017-008, AUD-017-022. |
| Quickstart verify 1: merge to main | SUPERSEDED | Main now CI-only; no current deployment expected from that procedure; AUD-017-020. |
| Quickstart verify 2: local health | UNVERIFIED | Authored curl commands do not prove deployed internal-service reachability; AUD-017-004, AUD-017-022. |
| Quickstart verify 3: dry-run | PARTIAL | Script avoids mutation there but still queries Azure; task promises no Azure calls; AUD-017-012. |
| Quickstart verify 4: drift dispatch | UNVERIFIED | Instructions not an actual scheduled/manual run or issue receipt; AUD-017-022. |
| Quickstart diagrams/env table/troubleshooting | CONFLICT | Retired flow, wrong current recovery assumptions and differing parameter-selection semantics need appended current guidance; AUD-017-020. |

## Complete Open Remediation Instructions

### Recovery and Delivery Safety

- [ ] AUD-017-001 (P1) Resolve deployed rollback identities and separate discovery errors from bootstrap.

**Basis / expected / observed / impact:** FR-004, FR-011, FR-012; T005, T006, T007, T023, T036; local rollback discovery/exit contract. [Discovery](../../../scripts/rollback.sh#L153) constructs old names, takes an unsorted second active item and suppresses errors; [bootstrap](../../../scripts/rollback.sh#L377) can then claim success. Real [IaC names](../../../infra/main.bicep#L1007) differ. This can leave an unhealthy environment unrecovered.

**Developer:** DevOps and SRE own discovery and the CD caller; historical contract owner owns the interface amendment. Resolve scoped resource outputs/tags, map logical ingestion to physical ingest, and distinguish authenticated empty history from access/not-found/CLI failure. Use a validated baseline, not response ordering. Depend on AUD-017-003 and retain staging/production support with no dev rollback.

**Tester:** Extend [rollback tests](../../../tests/devops/test_rollback_script.py#L1) and [conftest](../../../tests/devops/conftest.py#L1) with fake az logs. Positive: shuffled named resources restore pinned targets. Negative: 403, expired auth, CLI failure or missing resource cannot become bootstrap success. Edge: true first deployment, already-active target and reordered active revisions have explicit safe outcomes.

**Future validation:** V-RB with offline command fixtures; assert exact RG/resource identities and exits. **Complete when:** only authenticated zero-history produces a labelled skip and every claimed recovery restores the intended targets.

- [ ] AUD-017-002 (P1) Define and retrieve the previous web deployment package.

**Basis / expected / observed / impact:** FR-004, FR-011; T006, T007, T033; local Service Revision and rollback contracts. [Web restore](../../../scripts/rollback.sh#L243) skips when no target is passed. The uncalled [history helper](../../../scripts/rollback.sh#L172) queries publishing credentials, not deployments; an arbitrary ID is passed as ZIP source. Web can remain on the failed release.

**Developer:** App Service release owner and DevOps must retain an environment-bound ZIP/artifact with digest, retrieve and verify it, and deploy the local verified package to the discovered app. Remove the credential-history query. Reconcile `--revision-web` compatibility and Service Revision semantics; depend on AUD-017-003, without silently changing historical ID meaning.

**Tester:** Existing rollback test home: positive valid retained package is restored exactly; negative missing/expired artifact, bad digest and wrong-environment artifact never deploy; edge first release and already-restored package are explicit. Fake retrieval and CLI commands must verify no publishing credentials are requested.

**Future validation:** V-RB, then authorized V-REHEARSAL for a retained sandbox ZIP. **Complete when:** web recovery uses a real immutable artifact and participates in the same verified release as the containers.

- [ ] AUD-017-003 (P1) Implement a complete durable release baseline and its recovery consumer.

**Basis / expected / observed / impact:** FR-011, FR-004; T022, T024, T033, T037; Deployment Revision invariants. [Capture](../../../.github/workflows/cd.yml#L291) records web's ARM identity and persists only API/web JSON. [Update](../../../.github/workflows/cd.yml#L341) uses workflow-context SHA/ref and attempts a read-only-token push with tolerated failure. [Helper](../../../scripts/web-coverage/known-good.py#L99) tolerates missing trace/bad revision JSON and has no environment identity; rollback never consumes it (N05).

**Developer:** DevOps and spec-034 manifest owner must define all-four immutable targets with environment, validated head SHA, run ID and timestamps; persist atomically before advertising known-good and load before mutation. Preserve the coverage manifest's separate purpose, avoid broadening token permissions as a substitute for design, and update local data-model/outputs explicitly. Coordinate AUD-017-001/002/004.

**Tester:** Reuse CD/rollback fixtures with two successive releases. Positive: the failed second release restores the first complete tuple. Negative: corrupted/partial/wrong-env/wrong-SHA records and denied persistence cannot certify known-good. Edge: replay, concurrent attempts and missing coverage trace cannot erase a good baseline or bypass verification.

**Future validation:** V-CD/V-RB with fake persistence and two-release manifests. **Complete when:** producer and recovery consumer share the same complete environment-bound release record and persistence failure is observable.

- [ ] AUD-017-004 (P1) Validate four-service readiness within the two-minute window.

**Basis / expected / observed / impact:** FR-010, FR-001; T008, T021, T032; R-004 and Health Check Result. [CD health](../../../.github/workflows/cd.yml#L230) checks only API/web, disables TLS checks and accepts redirects. Five attempts permit 210s. [API health](../../../apps/api/app/api/health.py#L10) only checks environment variables and does not cover agents/ingestion. Private/headless [hosting](../../../infra/main.bicep#L1117) contradicts assumed public probes.

**Developer:** Service owners and DevOps must provide authenticated observable readiness for each service without opening private ingress. Align deadline, attempts and per-service results across CD and rollback; preserve web-root HTTP-200/content exclusion unless explicitly amended. Update R-004 and entity definitions, resolving attempts versus retries; do not infer worker health from API configuration.

**Tester:** Existing CD/rollback homes with fake HTTP/clock. Positive: four successful results within 120s. Negative: worker-only failure, TLS error, timeout or redirect blocks known-good. Edge: flapping results obey the approved attempt count, and web HTTP 200 error content remains accepted under the explicit content-level exclusion.

**Future validation:** V-CD/V-RB, then authorized private-network V-REHEARSAL. **Complete when:** all four independently attributable checks are trustworthy and total discovery/probing remains bounded.

- [ ] AUD-017-005 (P1) Cover partial deployment failure and provisioning mutation recovery.

**Basis / expected / observed / impact:** FR-004, FR-012, FR-013; T020, T023, T032, T035; local [CD error table](contracts/cd-workflow.md#L131). Contract requires deploy failure recovery, but [guard](../../../.github/workflows/cd.yml#L355) needs a failed health step that is skipped after deploy failure. Provisioning changes app image templates and [seed data](../../../scripts/seed_loader.py#L670); the blanket no-service-mutation assumption is false.

**Developer:** SRE/DevOps must capture the baseline before mutation and distinguish provision, seed, package, per-service deploy and health phases. Implement compensation for supported service mutations; explicitly require manual recovery for unsupported infrastructure/data effects instead of pretending container rollback undoes data. Resolve spec-031's narrower guard with the safety owner and update local error/state contracts. Depend on AUD-017-001/002/003.

**Tester:** Existing CD/rollback fixtures: positive complete release does not roll back; negative failure after one deployed service or during web packaging cannot leave a success/mixed-version report; edge early zero-mutation failure, seed-hook failure and partial IaC changes get accurate manual or automated recovery decisions.

**Future validation:** V-CD/V-RB with command-order logs, later V-REHEARSAL only with recovery authorization. **Complete when:** every failing phase has a tested recovery decision and supported partial deploy failures restore the complete baseline.

- [ ] AUD-017-006 (P1) Connect historical parameter contracts to effective CD configuration.

**Basis / expected / observed / impact:** FR-005, FR-009, FR-013; T002, T003, T014, T015, T019, T020, T031; R-002/R-007/Environment entity. [CD env setup](../../../.github/workflows/cd.yml#L143) does not select literal environment files. [Base parameters](../../../infra/main.parameters.json#L4) differ from [production](../../../infra/main.parameters.production.json#L4); template [environmentTier](../../../infra/main.bicep#L121) defaults dev, and alert destinations remain examples. Drift/CD can compare/deploy different intent.

**Developer:** IaC/DevOps must implement a supported common resolver, map production to prod tier explicitly, validate principal/subscription/group/region and required operational values, and fail unresolved substitutions before mutation. Keep schema/azd compatibility and four service names. Document seed data-plane and role-creation prerequisites; avoid swallowed environment setup failures. Update R-002/R-007 and quickstart selection procedure together.

**Tester:** Extend [parameter tests](../../../tests/devops/test_parameter_files.py#L12) to rendered values/commands. Positive: intended settings differ correctly by environment. Negative: cross-env resources, non-AU region, missing principal, invalid tier and unresolved token fail preflight. Edge: repeated first provision and optional dev use the same explicit resolution path.

**Future validation:** V-PARAM and authorized V-IAC with isolated rendered parameter fixtures. **Complete when:** CD and drift demonstrably share effective intended configuration with no accidental production-to-dev fallback.

- [ ] AUD-017-007 (P1) Restore a real required security gate after pipeline retirement.

**Basis / expected / observed / impact:** FR-002; SC-002, SC-006; T025, T027, T028, T029; R-009/Deployment Gate. [Replacement rationale](../../031-simplify-cicd-pipeline/contracts/cd-workflow.md#L102) assumes CI runs pip-audit, but only [ruff](../../../.github/workflows/ci.yml#L59) is present (N01). Separate security/SLI workflows do not gate current CD; advisory typing is not blocking assurance.

**Developer:** Security/release owners must define required checks for the exact release SHA and connect security results to the authoritative readiness decision. Add dependency auditing for deployed dependencies or approve an explicit equivalent; decide how staging evidence is required in the branch model. Do not restore retired jobs just for their filenames or regard an independent green check as a dependency. Reconcile local R-009/gate outputs.

**Tester:** Existing CD module with event/result graph fixtures. Positive: matching complete required evidence releases. Negative: vulnerability, absent result, wrong SHA, failed check or unfinished parallel scan blocks release. Edge: PR/cancelled/skipped CI never deploys and explicitly advisory checks remain distinguishable.

**Future validation:** V-CD, then authorized failing-gate V-REHEARSAL. **Complete when:** no agreed security obligation can be bypassed and the retirement rationale accurately describes the connected replacement.

- [ ] AUD-017-008 (P1) Enforce and evidence production approval expiry without blocking read-only drift.

**Basis / expected / observed / impact:** FR-003, FR-006; T026, T030, T038, T042; manual-approval model. [Environment binding](../../../.github/workflows/cd.yml#L40) proves neither reviewer membership nor 72h rejection. [Drift](../../../.github/workflows/drift-detection.yml#L30) inherits the production environment gate; local wait-timer wording does not implement expiry (N03).

**Developer:** Repository admin and Security must resolve retained approval scope under spec-031, bind current approvals to environment/SHA, implement expiry and preserve production protection. Give scheduled read-only drift a separately scoped authorized path, not a production approval bypass. Record ADR-031 owner/review/rotation status with redacted evidence and reconcile quickstart/error table; do not publish credentials.

**Tester:** Existing CD fixtures with policy snapshots/fake time. Positive: authorized unexpired matching approval permits deployment. Negative: unauthorized, missing, revoked or expired approval blocks it. Edge: replaced commit, reject/retry and scheduled drift while production waits do not bypass or stall the wrong operation.

**Future validation:** V-CD offline, then V-POLICY with admin authorization and actual approved/denied/expired receipts. **Complete when:** the 72h rule and authorization are demonstrated, and unattended drift has correct independent read-only scope.

- [ ] AUD-017-009 (P1) Reject invalid drift comparisons rather than emitting clean status.

**Basis / expected / observed / impact:** FR-006, FR-007; T043, T044, T047; local drift errors. [What-if](../../../.github/workflows/drift-detection.yml#L41) combines stderr/stdout and [jq fallback](../../../.github/workflows/drift-detection.yml#L134) substitutes `[]`; failed group lookup becomes absence. Genuine drift or lost permissions can disappear behind a green report.

**Developer:** DevOps must separate diagnostics, validate supported response envelopes/arrays, fail parser/schema errors, and distinguish authenticated missing RG from auth/transport failure. Preserve the explicit spec-031 genuine-absence skip with a skipped, not evaluated-clean, outcome. Align local drift error table and entity status semantics; depend on AUD-017-015 for release context.

**Tester:** Extend [drift tests](../../../tests/devops/test_drift_detection.py#L1). Positive: valid empty changes is clean. Negative: malformed/truncated/warning-prefixed JSON, missing changes envelope, command failure and 403 are failed/unknown. Edge: genuine bootstrap absence and a supported pinned-CLI envelope variant are classified explicitly.

**Future validation:** V-DRIFT using fake az/gh and offline payload fixtures. **Complete when:** only a validated successful comparison can say no drift, and errors retain usable diagnostics.

- [ ] AUD-017-010 (P1) Implement the retained application-secret and identity boundaries.

**Basis / expected / observed / impact:** FR-005; SC-004; T003, T014, T015, T031; Environment/quickstart security assumptions. [Registry passwords](../../../infra/main.bicep#L1023) are inline secret values. The [conditional signing vault](../../../infra/main.bicep#L224) is not the dedicated environment secret path promised for all applications (N06). Existing managed identities/Cosmos roles do not prove vault or cross-env isolation.

**Developer:** IaC/Security must distinguish app secrets from accepted pipeline credentials. Prefer eliminating secrets using identities; implement environment-specific vault storage/grants for retained secrets or obtain an explicit no-secret-equivalent decision. Preserve discovered policy constraints and bootstrap role/data-plane boundaries. Update local Environment, auth prerequisites and R-007 without claiming ADR-031 removed application isolation.

**Tester:** Existing parameter/DevOps fixtures should check rendered resource graphs. Positive: each service accesses only required same-env resources. Negative: staging cannot retrieve production values and no secrets appear in outputs/evidence. Edge: missing vault/grant, rotation and bootstrap fail safely without broad permanent privileges.

**Future validation:** V-PARAM/V-IAC, then authorized redacted V-POLICY access checks. **Complete when:** source wiring and negative access evidence substantiate the retained isolation requirement.

- [ ] AUD-017-011 (P1) Separate destructive soft-delete cleanup from routine bootstrap.

**Basis / expected / observed / impact:** FR-013; T019, T020, T031; plan life-safety/constitution boundary. [CD purge](../../../.github/workflows/cd.yml#L190) permanently removes all matching soft-deleted Cognitive Services kinds before the policy gate. Group scoping does not prove authorization to destroy recoverable resources.

**Developer:** Platform/Security owners must require a distinct approved recovery action or fail with restoration guidance. Bind approval to exact resources/operation, distinguish restore from recreate, preserve routine automatic RG bootstrap, and avoid adding broad purge permissions by default. Update the historical bootstrap/error guide; coordinate partial-mutation handling with AUD-017-005.

**Tester:** Existing CD module with deleted-account inventories. Positive: fresh deploy needs no purge. Negative: a recoverable resource causes a hold with no destructive call without approval. Edge: mixed kinds, similar names, wrong group and partial cleanup errors cannot continue blindly or affect unrelated recovery resources.

**Future validation:** V-CD with fake commands only; real purge never belongs to this audit. **Complete when:** an ordinary push cannot irreversibly delete recoverable resources without an auditable authorized decision.

### Contract, Validation and Evidence Work

- [ ] AUD-017-012 (P2) Implement exact argument, session and zero-call dry-run behavior.

**Basis / expected / observed / impact:** FR-004, FR-014; T004, T005, T009, T034; rollback interface/security contract. [Parser](../../../scripts/rollback.sh#L77) can shift past a missing value, [validation](../../../scripts/rollback.sh#L123) checks CLI presence but not session failure semantics, and [dry-run guard](../../../scripts/rollback.sh#L212) is after discovery. Source-string tests cannot establish correct exits or zero Azure calls.

**Developer:** Rollback owner must validate full flag/value pairs and target boundaries before side effects, map authentication failures explicitly, and render an offline plan from supplied baseline values. Preserve all flags/exit-code contracts; represent unknown targets honestly instead of querying Azure during dry-run. Reconcile quickstart's weaker no-change wording with the task's stronger zero-call rule.

**Tester:** Use sentinel az/curl executables in existing rollback fixtures. Positive: valid explicit targets produce expected plan. Negative: lone flags, flag-as-value, empty RG, invalid env and missing/expired session return intended errors. Edge: spaces/metacharacters, repeated flags and help neither inject commands nor reach Azure.

**Future validation:** V-RB; exact codes and zero sentinel calls in dry-run are required. **Complete when:** executable tests enforce the published interface rather than merely locate flag strings.

- [ ] AUD-017-013 (P2) Make post-restore checks concurrent, bounded and attributable.

**Basis / expected / observed / impact:** FR-010, FR-012; SC-003; T008, T010, T037; rollback timeout budget. [Serial loop](../../../scripts/rollback.sh#L400) permits four 110s probe sequences, exceeding the whole 300s budget before restore overhead.

**Developer:** SRE/rollback owner must run independent checks concurrently under one recovery deadline, join child processes, preserve per-service target/code/timing results and distinguish restore failure from post-restore health failure. Reuse AUD-017-004's internal readiness semantics and preserve exit 4. Update local time budget and output examples only with supported semantics.

**Tester:** Existing fake-clock rollback tests: positive all targets restore/verify within budget; negative a slow/failed target yields exit 4 and its identity; edge simultaneous timeouts, interrupted child and no-history skip cannot hang or count as a measured successful restoration.

**Future validation:** V-RB with deterministic durations. **Complete when:** health is at most 120s and complete supported rollback meets 300s, or an explicit approved amendment transparently replaces the original target.

- [ ] AUD-017-014 (P2) Preserve exact and safe drift report content through notification failures.

**Basis / expected / observed / impact:** FR-006, FR-007; T040, T044, T045, T046, T047; Drifted Resource/Property Change/report contract. [Parser](../../../.github/workflows/drift-detection.yml#L110) uses broad regexes, substitutes null for false and assumes flat fields. [Report](../../../.github/workflows/drift-detection.yml#L150) injects unescaped values and is not retained if issue creation fails.

**Developer:** Drift/report owner must normalize pinned CLI shape, traverse nested deltas, preserve false/zero/null and actual resource type, filter exact system paths, escape Markdown and redact secret-bearing data. Retain a sanitized artifact/summary on rate limit or permission failure. Keep label/title/metrics/intentional-drift next steps compatible with the historical contract.

**Tester:** Existing drift module with synthetic real-shaped Create/Delete/Modify/NoChange payloads. Positive: exact expected/actual metrics/rows. Negative: nested declarative changes not filtered and secrets never rendered. Edge: false, zero, null, pipes/newlines, regex-lookalike names and denied/rate-limited gh calls retain complete sanitized findings.

**Future validation:** V-DRIFT with fake gh and captured artifacts. **Complete when:** assertions verify report fidelity, safe handling and availability after notification failure.

- [ ] AUD-017-015 (P2) Bind drift to the deployed release and coordinate with active deployments.

**Basis / expected / observed / impact:** FR-006, FR-015; T042, T043; CHK061. [Drift](../../../.github/workflows/drift-detection.yml#L33) uses default-branch IaC and literal params/default images, unlike environment-branch CD. There is no connection to [CD's lock](../../../.github/workflows/cd.yml#L50). Normal deployment can be reported as unauthorized drift.

**Developer:** DevOps/SRE must compare the environment's approved release SHA and effective parameter/image set from AUD-017-003/006. Define bounded waiting or explicit pending state during mutation, without cancelling deployment or deadlocking locks. Preserve Saturday UTC schedule, dev exclusion and independent environments. Add this context to local Drift Report and R-006/R-008 contracts.

**Tester:** Existing drift/CD fixtures with two environment SHAs and overlapping operations. Positive: stable matching state is clean. Negative: true unexpected scale change is reported. Edge: main differs, a newer release queues, baseline is missing or deployment is in-flight yields a scoped pending/unknown result, not spurious or false-clean findings.

**Future validation:** V-CD/V-DRIFT then approved V-REHEARSAL. **Complete when:** comparison metadata identifies exact intended release and no scan races environment mutation.

- [ ] AUD-017-016 (P2) Make deployment state, summaries and critical notifications phase-accurate.

**Basis / expected / observed / impact:** FR-007, FR-012; SC-008; T024, T029, T037, T038, T050; Deployment Revision state machine. [Status](../../../.github/workflows/cd.yml#L395) prioritizes healthy probe outcome over later failure and can label pre-deploy failure as critical rollback failure. [Summary](../../../.github/workflows/cd.yml#L409) lacks exact restored targets. Environment association can generate native deployment records, but outputs alone do not prove correct lifecycle semantics.

**Developer:** DevOps/SRE must derive outcomes from phase/mutation/verification, provide check/service/reason/remediation plus baseline identity, retain errors on failed issue delivery and differentiate skipped bootstrap from rollback success. Decide hold/resume behavior for subsequent queued releases after critical failure with the owner. Keep native GitHub notifications; update local state/error/output contracts consistently.

**Tester:** Existing CD fixtures: positive complete successful release; negative baseline persistence failure cannot advertise complete success; edge pre-checkout/login failure, rollback exit 1/2/3/4, skip and issue API denial all receive correct context without unbound-variable errors or false recovery claims.

**Future validation:** V-CD plus approved V-REHEARSAL; assert coherent output/native status and actionable report within 120s. **Complete when:** every failure describes what actually ran and what must happen next.

- [ ] AUD-017-017 (P2) Maintain tests for the replacement design and retained safety obligations.

**Basis / expected / observed / impact:** FR-001, FR-002, FR-004, FR-006, FR-008; T012, T013, T025, T026, T034, T035, T039, T040, T054. [Old assertions](../../../tests/devops/test_cd_workflow.py#L49) require main/OIDC/removed jobs. [Rollback tests](../../../tests/devops/test_rollback_script.py#L57) search strings and N02 found no workflow integration equivalent. [CI](../../../.github/workflows/ci.yml#L131) omits the DevOps suite.

**Developer:** QA/DevOps must reuse the four existing modules/conftest, migrate obsolete shape assertions while retaining behavior, add hermetic fake-command execution and connected-workflow assertions, and select the maintained suite in required CI. Any new integration path is proposed until created. Explicitly reconcile the superseded no-CI-edit restriction and keep historical test-path consolidation traceable.

**Tester:** Positive correct branch/event/SHA, complete baseline and validated comparison pass. Negative mutations removing guards, workers, required security or parser errors cause targeted failures. Edge cancelled/skipped/PR runs, reordered revisions and unavailable tools remain deterministic, offline and fail-safe.

**Future validation:** V-CD/V-RB/V-DRIFT/V-PARAM then V-SUITE. **Complete when:** no maintained test requires retired architecture, meaningful failure modes are exercised, and CI actually selects those tests.

- [ ] AUD-017-018 (P2) Define and measure deployment, recovery and reporting outcomes.

**Basis / expected / observed / impact:** SC-001, SC-003, SC-008, SC-010; T021, T048, T053; plan performance goals. Targets are 900s release, 300s restore, 120s report, at least 95% complete recovery. [Current job limit](../../../.github/workflows/cd.yml#L45) is 60 minutes; no scoped measured series/denominator exists (N08).

**Developer:** SRE/QA must define start/end events, cold/warm cohorts, denominator/window and exclusions. Separate bootstrap skip/no-attempt cases from successful restoration. Get owner resolution for evolved cold-provision targets; preserve original unmet historical goals rather than relabeling them achieved. Attach revision/environment/toolchain/timestamp provenance to measurements.

**Tester:** Existing CD/rollback homes can hold metric fixtures. Positive boundary budgets and 95/100 valid restorations meet the definition. Negative 94/100, incomplete service restoration, missing timestamps or denominator changes fail. Edge no attempts, cancelled runs and initial provision return explicit separate/unknown outcomes.

**Future validation:** V-SUITE for calculation tests, approved V-REHEARSAL for actual timings. **Complete when:** retained SC claims are supported by measurements or transparently replaced by an approved amendment.

- [ ] AUD-017-019 (P2) Verify effective sovereignty intent and strict approval-date semantics.

**Basis / expected / observed / impact:** FR-009; SC-007; T014, T052; plan cloud/security claims. [CD verifier call](../../../.github/workflows/cd.yml#L213) lacks effective what-if input. [Verifier](../../../scripts/verify-carveout.ps1#L99) only rejects old dates beyond six months and merely warns on more recent expiry even with Strict; [resource comparison](../../../scripts/verify-carveout.ps1#L121) is optional. Literal region tests do not prove deployed location or actual approval.

**Developer:** Security/IaC must enforce schema/date/strict failures as advertised and bind rendered deployment intent to allowed locations and approval registry. Cover nested effective resource locations and the current bounded model-hosting exception without widening data residency. Preserve AU primary restriction and deferred FR-CAP-017-001; reconcile historical blanket AU wording through the owner.

**Tester:** Reuse [carve-out workflow test home](../../../tests/devops/test_foundry_carveout_workflow.py#L1) and parameter fixtures. Positive valid current approved AU intent. Negative recently expired review, invalid schema, missing binding/registry entry, placeholder reviewer and non-AU data resource fail. Edge midnight/timezone and approved model-only exception require explicit policy treatment.

**Future validation:** V-SOV/V-PARAM plus authorized V-IAC. **Complete when:** effective resources, executable strict checks and redacted approval evidence agree.

- [ ] AUD-017-020 (P2) Reconcile this folder's contracts, research and quickstart as historical records.

**Basis / expected / observed / impact:** FR-002, FR-003, FR-008, FR-010; T025, T026, T030, T048, T053; all R/CHK records assessed here. [Plan PASS](plan.md#L22), [R-009](research.md#L164), [CD errors](contracts/cd-workflow.md#L131) and quality checklist notes combine retired design, absent expiry, ambiguous retries and unsupported completion claims.

**Developer:** Product owner, DevOps and technical writer own an append-only replacement/clarification map for local plan, research, data model, all three contracts and quickstart. Resolve trigger/auth/job retirement, retained security, expiry, baseline schema, retries, partial provisioning/deploy, bootstrap, drift errors, timing and permissions. Preserve original checkbox/evidence history; any later state change needs a separately authorized lifecycle record. This audit does not modify those originals.

**Tester:** Review positive current examples, negative forbidden bypasses and edge-case decisions against source and future assertions. Check every CHK disposition, all original task IDs, no unsupported pass claims, and no obsolete main-merge instruction advertised as today's deployment procedure. Validate all local/cross-folder links.

**Future validation:** V-DOC and V-SUITE after authorized updates. **Complete when:** these seven artifacts independently explain the retired design, current authority and outstanding retained safeguards without misleading completion claims.

- [ ] AUD-017-021 (P2) Supply scoped amendment evidence without activating deferred country scope.

**Basis / expected / observed / impact:** PER-043, PER-044, PER-045, HYP-015, SCP-048, SCP-049, SCP-050, SCP-051, FR-CAP-017-001; T053 documentation verification. [Named hypothesis evidence](../../017-cd-pipeline/spec.md#L215) is missing (N07). [Portfolio rubric](../../028-capstone-alignment/evidence/rubric-postfeature.md#L25) is aggregate, not proof of this spec's per-criterion uplift or consultation on every change. Persona validation labels are not receipts.

**Developer:** Spec-017/spec-028 evidence owners must correct or create the proposed evidence location, record actual revision/actor consultation and per-spec before/after scores, and link real persona validation. Otherwise mark not tested/unverified rather than backfill success. Preserve PH/JP/BD placeholders, sovereignty preconditions, constitutional exclusions and cross-spec deferrals; no country deployment is needed.

**Tester:** Positive matching revision/actors/scores support the scoped claim. Negative missing stub, aggregate-only evidence or unverifiable validation does not. Edge mean improvement with one regressing criterion must fail the hypothesis's own rule. Any future SME exercise/delegation requires separate authorization.

**Future validation:** V-DOC and later approved rubric review. **Complete when:** links resolve, claims match evidence granularity and deferred capabilities remain explicitly deferred.

- [ ] AUD-017-022 (P2) Record actual verification and approval evidence for original checked tasks.

**Basis / expected / observed / impact:** T051, T052, T053, T054; SC-004, SC-006, SC-007, SC-009; plan ALL PASS/quality readiness. No scoped execution/approval receipts establish shellcheck, IaC validate, quickstart rehearsal, tests or effective isolation (N08). This static report cannot supply them.

**Developer:** QA/release owner must prepare an authorized revision, safe runner, tool versions, module/dependency prerequisites, effective parameter files and reviewers. Record failures and fixes as new sanitized evidence with run IDs/hashes/times, not replacements for original checked boxes. A source declaration or this report's text validation is never product execution proof.

**Tester:** Run V-LINT/V-SUITE before authorized V-IAC/V-POLICY/V-REHEARSAL, after prerequisites close. Positive complete passing receipts; negative failed gates retained with proof that release stopped; edge auth/quota/network/tool unavailability recorded blocked/unverified. Compare a named prior CI baseline before any regression-free claim.

**Future validation:** Use the catalogue below only in later authorized work. **Complete when:** every retained execution claim has reproducible revision-bound evidence and an accountable reviewer; unknown external state remains UNVERIFIED.

## Requirement and Outcome Coverage

| ID | Status | Source-supported assessment | Follow-ups |
| --- | --- | --- | --- |
| FR-001 | SUPERSEDED | Main staging route explicitly replaced; four declared [services](../../../azure.yaml#L28) remain, validation partial. | AUD-017-004, AUD-017-017, AUD-017-020 |
| FR-002 | CONFLICT | Gate jobs retired on unsupported [CI scan claim](../../031-simplify-cicd-pipeline/contracts/cd-workflow.md#L102). | AUD-017-007, AUD-017-020 |
| FR-003 | UNVERIFIED | [Environment](../../../.github/workflows/cd.yml#L40) is not reviewer/expiry evidence. | AUD-017-008 |
| FR-004 | PARTIAL | [Recovery](../../../scripts/rollback.sh#L337) exists but wrong targets/skip/web defects prevent full guarantee. | AUD-017-001, AUD-017-002, AUD-017-005 |
| FR-005 | PARTIAL | Parameter/identity declarations exist; effective selection/vault isolation incomplete. | AUD-017-006, AUD-017-010 |
| FR-006 | PARTIAL | [Scheduled matrix](../../../.github/workflows/drift-detection.yml#L12) present, comparison can fail open/race. | AUD-017-009, AUD-017-014, AUD-017-015 |
| FR-007 | PARTIAL | [Native issue/summary](../../../.github/workflows/cd.yml#L365) authored, phase accuracy and retained report incomplete. | AUD-017-014, AUD-017-016 |
| FR-008 | SUPERSEDED | Separate workflow retained; main-only/no-CI-edit explicitly changed by [031](../../031-simplify-cicd-pipeline/spec.md#L1). | AUD-017-017, AUD-017-020 |
| FR-009 | PARTIAL | AU literals/restriction exist; [tests](../../../tests/devops/test_parameter_files.py#L63) do not establish effective intent. | AUD-017-006, AUD-017-019 |
| FR-010 | PARTIAL | [Two checks](../../../.github/workflows/cd.yml#L230) and possible 210s contradict retained four-service/two-minute requirement. | AUD-017-004, AUD-017-013 |
| FR-011 | PARTIAL | [Capture](../../../.github/workflows/cd.yml#L291) incomplete and not consumed by restore. | AUD-017-003 |
| FR-012 | PARTIAL | [Critical issue path](../../../.github/workflows/cd.yml#L365) exists but false bootstrap success can bypass it. | AUD-017-001, AUD-017-013, AUD-017-016 |
| FR-013 | PARTIAL | [Group creation](../../../.github/workflows/cd.yml#L136)/provision exist; config and mutation safeguards incomplete. | AUD-017-005, AUD-017-006, AUD-017-011 |
| FR-014 | SUPERSEDED | [ADR-031](../../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L31) operational exception exists; compliance/rotation unverified. | AUD-017-008, AUD-017-020, AUD-017-022 |
| FR-015 | PARTIAL | [Per-env lock](../../../.github/workflows/cd.yml#L50) implemented in YAML, not durable FIFO/burst execution or drift coordination. | AUD-017-015, AUD-017-017, AUD-017-020 |
| NFR-RES (plan alias) | PARTIAL | Resilience retries/recovery exist, retained defects defeat complete guarantee. | AUD-017-001, AUD-017-005, AUD-017-013 |
| NFR-AUD (plan alias) | UNVERIFIED | Append-only retention, complete release provenance and approval capture not established. | AUD-017-003, AUD-017-016, AUD-017-022 |
| NFR-WAF (plan alias) | PARTIAL | Reliability/security/operations design present, review outcome not proven. | AUD-017-008, AUD-017-010, AUD-017-019, AUD-017-022 |

NFR aliases identify this plan's named NFR rows. There are no separately numbered original NFRs. Other nonfunctional constraints are covered by the FRs, SCs and checklist questions, not invented as new original requirements.

| ID | Status | Measurable outcome assessment | Follow-ups |
| --- | --- | --- | --- |
| SC-001 | UNVERIFIED | Main flow superseded; no 15-minute measurement, current 60-minute limit. | AUD-017-018, AUD-017-020 |
| SC-002 | PARTIAL | CI success guard exists; security/staging/approval assurance not all connected. | AUD-017-007, AUD-017-008 |
| SC-003 | PARTIAL | Serial health permits 440s before restore overhead; no five-minute evidence. | AUD-017-013, AUD-017-018 |
| SC-004 | UNVERIFIED | Separate names do not demonstrate no shared secrets/config; wiring partial. | AUD-017-006, AUD-017-010, AUD-017-022 |
| SC-005 | UNVERIFIED | Correct weekly cron, no cadence/issue proof and fail-open comparison risk. | AUD-017-008, AUD-017-009, AUD-017-015 |
| SC-006 | SUPERSEDED | Literal unchanged-CI scope replaced; functional regression freedom lacks a baseline receipt. | AUD-017-017, AUD-017-020, AUD-017-022 |
| SC-007 | UNVERIFIED | AU source settings do not prove deployed locations or approval/policy state. | AUD-017-019, AUD-017-022 |
| SC-008 | PARTIAL | Summary/report authored, complete actionable detail and delivery timing missing. | AUD-017-014, AUD-017-016, AUD-017-018 |
| SC-009 | PARTIAL | Three environment branches designed; effective isolation/config extensibility incomplete. | AUD-017-006, AUD-017-017, AUD-017-022 |
| SC-010 | UNVERIFIED | No observation window or denominator for at least 95% full restoration. | AUD-017-018 |

### Acceptance Scenarios

USx-ASy are local labels for the source's numbered [acceptance scenarios](../../017-cd-pipeline/spec.md#L8), not new product requirements.

| Scenario | Status | Assessment | Follow-ups |
| --- | --- | --- | --- |
| US1-AS1 | SUPERSEDED | Main promotion replaced; branch-specific automatic flow/timing unverified. | AUD-017-018, AUD-017-020 |
| US1-AS2 | PARTIAL | All four deployed health endpoints not checked. | AUD-017-004 |
| US1-AS3 | PARTIAL | Success/push guard present; required security/advisory-type boundaries unresolved. | AUD-017-007, AUD-017-017 |
| US1-AS4 | PARTIAL | Lock authored; burst/queue/recovery semantics not exercised. | AUD-017-015, AUD-017-017 |
| US2-AS1 | SUPERSEDED | Chained promotion intentionally removed; retained security assurance absent. | AUD-017-007, AUD-017-020 |
| US2-AS2 | PARTIAL | Lint exists, dependency scan and precise failure report incomplete. | AUD-017-007, AUD-017-016 |
| US2-AS3 | UNVERIFIED | Required-reviewer authorization not demonstrated. | AUD-017-008 |
| US2-AS4 | PARTIAL | Parallel security/SLI failure not a CD dependency; notification incomplete. | AUD-017-007, AUD-017-016 |
| US3-AS1 | PARTIAL | Health guard calls defective all-service recovery. | AUD-017-001, AUD-017-002, AUD-017-005 |
| US3-AS2 | PARTIAL | Restore checks serial; summary lacks exact targets/reasons. | AUD-017-013, AUD-017-016 |
| US3-AS3 | PARTIAL | Two green probes record incomplete baseline; later persistence failure may still say success. | AUD-017-003, AUD-017-004, AUD-017-016 |
| US3-AS4 | PARTIAL | Exit-4/issue path exists; discovery-error skip can bypass critical response. | AUD-017-001, AUD-017-013, AUD-017-016 |
| US4-AS1 | PARTIAL | Staging parameter file authored but selection disconnected. | AUD-017-006 |
| US4-AS2 | UNVERIFIED | No actual denied cross-environment secret-access evidence. | AUD-017-010, AUD-017-022 |
| US4-AS3 | PARTIAL | Production location literal exists; effective tier/identity/config not established. | AUD-017-006, AUD-017-019 |
| US5-AS1 | PARTIAL | Invalid comparison can emit clean result. | AUD-017-009 |
| US5-AS2 | PARTIAL | Property report loses values/nesting and filter precision. | AUD-017-014 |
| US5-AS3 | PARTIAL | Issue command authored; retained API-error report and real issue receipt absent. | AUD-017-014, AUD-017-022 |

### Edge Cases

| ID | Original case | Assessment | Follow-ups |
| --- | --- | --- | --- |
| EDGE-01 | In-flight/new deployment | PARTIAL: lock exists; burst/version recovery behavior not established. | AUD-017-015, AUD-017-017 |
| EDGE-02 | Resource group absent | PARTIAL: create exists; selection/identity/cleanup safeguards incomplete. | AUD-017-006, AUD-017-011 |
| EDGE-03 | Health timeout | PARTIAL: curl timeout finite, full-service/global bound wrong. | AUD-017-004, AUD-017-013 |
| EDGE-04 | Rollback also fails | PARTIAL: critical path present but false success/notification failure remain. | AUD-017-001, AUD-017-016 |
| EDGE-05 | Drift auth failure | PARTIAL: login native failure; lookup access errors still become absence. | AUD-017-009 |
| EDGE-06 | Some services fail | PARTIAL: workers unprobed and web restoration skipped. | AUD-017-002, AUD-017-004 |
| EDGE-07 | OIDC exchange fails | SUPERSEDED operationally; replacement credential failure needs evidence. | AUD-017-008, AUD-017-022 |
| EDGE-08 | Hung deployment | CONFLICT: six-hour text, 20-minute task, 60-minute current job differ; every pending commit not guaranteed. | AUD-017-017, AUD-017-020 |
| EDGE-09 | Provision fails before deploy | CONFLICT: IaC and seeding can already mutate app/data; not inherently no-rollback-needed. | AUD-017-005 |
| EDGE-10 | Web 200 error content | IMPLEMENTED explicit content-exclusion behavior; accepting redirects remains separate defect. | AUD-017-004 |

### Clarifications and Later Amendments

CL identifiers map to Session 1's eight and Pass 2's seven answers in source order. All original persona/hypothesis/scope/capstone IDs are retained.

| ID | Status / decision | Evidence or disposition |
| --- | --- | --- |
| CL-01 | SUPERSEDED workflow OIDC | ADR-031 explicit temporary replacement; AUD-017-008, AUD-017-020. |
| CL-02 | CONFLICT health retry/six-service statement | Pass 2 corrects to four; three-attempt 110s intent differs from current; AUD-017-004, AUD-017-020. |
| CL-03 | PARTIAL pip-audit over safety | No active workflow implementation despite explicit tool decision; AUD-017-007. |
| CL-04 | PARTIAL per-env vault/MI | Application obligation retained, workflow OIDC part replaced; AUD-017-010. |
| CL-05 | PARTIAL native notifications | Native commands exist; accuracy/retention need work; AUD-017-014, AUD-017-016. |
| CL-06 | PARTIAL per-env queue | Non-cancelling lock authored, burst delivery not proven; AUD-017-017. |
| CL-07 | IMPLEMENTED UTC weekly schedule | [Cron](../../../.github/workflows/drift-detection.yml#L14) matches Saturday 16:00; execution unverified. |
| CL-08 | UNVERIFIED production-only 72h approval | N03; AUD-017-008. |
| CL-09 | IMPLEMENTED four-service definition | [azure.yaml](../../../azure.yaml#L28) matches; health incomplete; AUD-017-004. |
| CL-10 | CONFLICT endpoint reachability | Internal agents/headless ingestion differ from assumed public checks; AUD-017-004. |
| CL-11 | IMPLEMENTED workflow/script homes | CD, drift and rollback files remain; no missing-file finding. |
| CL-12 | SUPERSEDED main workflow_run | Explicit environment-branch replacement; AUD-017-020. |
| CL-13 | PARTIAL environment parameter files | Files present, no selector in provision path; AUD-017-006. |
| CL-14 | CONFLICT default-six-hour timeout | T048/current bound differ; AUD-017-018, AUD-017-020. |
| CL-15 | PARTIAL RG-scoped bootstrap | Group create supported; permission/config/mutation handling incomplete; AUD-017-005, AUD-017-006. |
| PER-043 | UNVERIFIED validation label | [AIIMS reference](../../017-cd-pipeline/spec.md#L207) authored; no scoped validation receipt; AUD-017-021. |
| PER-044 | UNVERIFIED validation label | [Technical actor reference](../../017-cd-pipeline/spec.md#L208) authored; no proof of consultation on every change; AUD-017-021. |
| PER-045 | IMPLEMENTED placeholder/preconditions | [Non-AU persona](../../017-cd-pipeline/spec.md#L209) remains explicitly unvalidated; no country work inferred. |
| HYP-015 | MISSING named stub; outcome UNVERIFIED | [Hypothesis](../../017-cd-pipeline/spec.md#L215), N07; aggregate rubric cannot establish it; AUD-017-021. |
| SCP-048 | IMPLEMENTED documented deferral | [Country scope](../../017-cd-pipeline/spec.md#L223) subject to decision/regulatory/sign-off preconditions. |
| SCP-049 | IMPLEMENTED constitutional exclusion | [Scope](../../017-cd-pipeline/spec.md#L224) not authority to amend constitution; AUD-017-019 respects it. |
| SCP-050 | IMPLEMENTED ownership deferral | [Arbitration rule](../../017-cd-pipeline/spec.md#L225) authored; execution unverified; AUD-017-020. |
| SCP-051 | IMPLEMENTED enabling/meta label | [Scope](../../017-cd-pipeline/spec.md#L226) not direct capstone outcome proof. |
| FR-CAP-017-001 | IMPLEMENTED as explicitly DEFERRED | [Country topology](../../017-cd-pipeline/spec.md#L231) is not a missing active deployment feature; AUD-017-019, AUD-017-021 preserve preconditions. |

## Original Task Coverage

These are the **54 inherited original tasks**, not fabricated local historical tasks. Each row retains its exact source checkbox from the [canonical list](../../017-cd-pipeline/tasks.md#L29), with local implementation/test evidence and actionable follow-ups. Consolidated test filenames are credited; deliberately retired job shapes are not automatically missing.

| Original ID | Original checkbox | Status | Concrete evidence / remaining obligation | Follow-ups |
| --- | --- | --- | --- | --- |
| T001 | [x] | IMPLEMENTED | Test package and [conftest](../../../tests/devops/conftest.py#L12) exist with shared loaders/fixtures. | AUD-017-017 |
| T002 | [x] | IMPLEMENTED | [Staging parameters](../../../infra/main.parameters.staging.json#L4) contain requested literal values; consumption separately incomplete. | AUD-017-006 |
| T003 | [x] | PARTIAL | [Production parameters](../../../infra/main.parameters.production.json#L4) exist but example alert values not operational destinations. | AUD-017-006 |
| T004 | [x] | PARTIAL | [Flag parsing](../../../scripts/rollback.sh#L77) exists, missing-value behavior incomplete. | AUD-017-012 |
| T005 | [x] | PARTIAL | [CLI/env/group checks](../../../scripts/rollback.sh#L123) exist, authenticated-session/target errors incomplete. | AUD-017-001, AUD-017-012 |
| T006 | [x] | PARTIAL | [Discovery](../../../scripts/rollback.sh#L153) uses wrong names/unsorted revisions; web helper incorrect and unused. | AUD-017-001, AUD-017-002 |
| T007 | [x] | PARTIAL | [Restore commands](../../../scripts/rollback.sh#L188) authored, correct identities/artifact not supplied. | AUD-017-001, AUD-017-002 |
| T008 | [x] | PARTIAL | [Health function](../../../scripts/rollback.sh#L275) has requested retry constants/exit 4 but serial/inaccessible-target problems remain. | AUD-017-004, AUD-017-013 |
| T009 | [x] | PARTIAL | [Dry-run](../../../scripts/rollback.sh#L212) follows Azure discovery, not zero-call behavior. | AUD-017-012 |
| T010 | [x] | IMPLEMENTED | [Prefix helpers](../../../scripts/rollback.sh#L44) and final status symbols authored; result accuracy separate. | AUD-017-013, AUD-017-016 |
| T011 | [x] | IMPLEMENTED | [Shebang/strict mode](../../../scripts/rollback.sh#L1) exist; read-only index inspection confirms executable mode 100755. | AUD-017-022 |
| T012 | [x] | CONFLICT | Consolidated [syntax assertions](../../../tests/devops/test_cd_workflow.py#L16) still demand main/OIDC. | AUD-017-017 |
| T013 | [x] | CONFLICT | [Job assertions](../../../tests/devops/test_cd_workflow.py#L75) expect retired deploy-staging shape/timeout. | AUD-017-017 |
| T014 | [x] | PARTIAL | [Parameter tests](../../../tests/devops/test_parameter_files.py#L12) verify literal keys/regions, not effective rendered intent. | AUD-017-006, AUD-017-019 |
| T015 | [x] | PARTIAL | [Isolation assertions](../../../tests/devops/test_parameter_files.py#L89) check names/text, not access denial or selected settings. | AUD-017-006, AUD-017-010 |
| T016 | [x] | SUPERSEDED | Main/OIDC design explicitly replaced; [current CD](../../../.github/workflows/cd.yml#L18) remains separate/named cd. | AUD-017-020 |
| T017 | [x] | SUPERSEDED | [Dynamic deploy](../../../.github/workflows/cd.yml#L34) replaces named staging job while retaining guard/lock. | AUD-017-017, AUD-017-020 |
| T018 | [x] | SUPERSEDED | [Exact upstream SHA](../../../.github/workflows/cd.yml#L66) and accepted credential path replace action/auth prescription. | AUD-017-008, AUD-017-020 |
| T019 | [x] | PARTIAL | [Group/env setup](../../../.github/workflows/cd.yml#L136) authored; file selector/error handling incomplete. | AUD-017-006 |
| T020 | [x] | PARTIAL | [Provision/deploy](../../../.github/workflows/cd.yml#L224) include hooks; partial mutation recovery incomplete. | AUD-017-005, AUD-017-006 |
| T021 | [x] | PARTIAL | [Health](../../../.github/workflows/cd.yml#L230) parallel but only two services and wrong retry/deadline values. | AUD-017-004 |
| T022 | [x] | PARTIAL | [Capture](../../../.github/workflows/cd.yml#L291) misidentifies web and omits services from persisted JSON. | AUD-017-003 |
| T023 | [x] | PARTIAL | [Recovery guard](../../../.github/workflows/cd.yml#L355) exists; deploy failure skipped and false bootstrap success possible. | AUD-017-001, AUD-017-005 |
| T024 | [x] | PARTIAL | [Status](../../../.github/workflows/cd.yml#L395) may misclassify baseline/pre-deploy failures. | AUD-017-003, AUD-017-016 |
| T025 | [x] | SUPERSEDED | [Removed gate job](../../031-simplify-cicd-pipeline/contracts/cd-workflow.md#L102) retires old test shape, not security assurance. | AUD-017-007, AUD-017-017 |
| T026 | [x] | SUPERSEDED | Old production structural test replaced by [branch job](../../../.github/workflows/cd.yml#L40); policy still unverified. | AUD-017-008, AUD-017-017 |
| T027 | [x] | SUPERSEDED | [Replacement contract](../../031-simplify-cicd-pipeline/contracts/cd-workflow.md#L102) removes gate job intentionally; rationale unsupported. | AUD-017-007, AUD-017-020 |
| T028 | [x] | CONFLICT | [CI lint](../../../.github/workflows/ci.yml#L59) exists; no dependency audit in active workflows (N01). | AUD-017-007 |
| T029 | [x] | PARTIAL | [Summary](../../../.github/workflows/cd.yml#L409) is not a complete equivalent gate-failure output contract. | AUD-017-016, AUD-017-020 |
| T030 | [x] | SUPERSEDED | [Single environment job](../../../.github/workflows/cd.yml#L34) replaces chained production; reviewer/expiry unresolved. | AUD-017-008, AUD-017-020 |
| T031 | [x] | PARTIAL | [Bootstrap/auth](../../../.github/workflows/cd.yml#L94) generalized; effective production config/secret boundaries incomplete. | AUD-017-006, AUD-017-010 |
| T032 | [x] | PARTIAL | [Shared deploy/health](../../../.github/workflows/cd.yml#L224) covers production but only two health targets. | AUD-017-004, AUD-017-005 |
| T033 | [x] | PARTIAL | [Shared revisions](../../../.github/workflows/cd.yml#L291) not a restorable complete production baseline. | AUD-017-002, AUD-017-003 |
| T034 | [x] | PARTIAL | [Rollback tests](../../../tests/devops/test_rollback_script.py#L1) source-only, not executable argument/exit/dry-run coverage. | AUD-017-012, AUD-017-017 |
| T035 | [x] | MISSING | N02 found no equivalent workflow rollback integration assertion for the [CD caller](../../../.github/workflows/cd.yml#L355). | AUD-017-005, AUD-017-017 |
| T036 | [x] | PARTIAL | [Bootstrap branch](../../../scripts/rollback.sh#L377) and text test exist but discovery error falsely qualifies. | AUD-017-001, AUD-017-017 |
| T037 | [x] | PARTIAL | [Summary](../../../.github/workflows/cd.yml#L409) omits exact restored targets and accepts skip as rolled-back. | AUD-017-013, AUD-017-016 |
| T038 | [x] | PARTIAL | [Critical issue](../../../.github/workflows/cd.yml#L365) authored; false-success suppression and delivery evidence unresolved. | AUD-017-001, AUD-017-016 |
| T039 | [x] | CONFLICT | [Drift syntax tests](../../../tests/devops/test_drift_detection.py#L15) preserve schedule but require retired OIDC permission. | AUD-017-017 |
| T040 | [x] | PARTIAL | [Structure tests](../../../tests/devops/test_drift_detection.py#L56) test broad presence, not parser/report/error behavior. | AUD-017-009, AUD-017-014, AUD-017-017 |
| T041 | [x] | IMPLEMENTED | [Weekly/manual workflow](../../../.github/workflows/drift-detection.yml#L10) exists; auth permission expressly superseded. | AUD-017-022 |
| T042 | [x] | SUPERSEDED | OIDC portion replaced; [matrix/environment](../../../.github/workflows/drift-detection.yml#L22) retained. | AUD-017-008, AUD-017-020 |
| T043 | [x] | PARTIAL | [What-if flags](../../../.github/workflows/drift-detection.yml#L65) present, stable release context and diagnostics handling incomplete. | AUD-017-009, AUD-017-015 |
| T044 | [x] | PARTIAL | [Filter](../../../.github/workflows/drift-detection.yml#L110) has broad regex/flat parsing/fallback defects. | AUD-017-009, AUD-017-014 |
| T045 | [x] | PARTIAL | [Report/metrics](../../../.github/workflows/drift-detection.yml#L150) authored but fidelity/escaping/redaction incomplete. | AUD-017-014 |
| T046 | [x] | PARTIAL | [Conditional issue](../../../.github/workflows/drift-detection.yml#L218) exists; no retained API-failure report or actual issue receipt. | AUD-017-014, AUD-017-022 |
| T047 | [x] | PARTIAL | [What-if failure](../../../.github/workflows/drift-detection.yml#L75) surfaced; access/parser failures still misclassified. Genuine absence skip explicitly replaced. | AUD-017-009, AUD-017-014 |
| T048 | [x] | CONFLICT | [Current 60-minute limit](../../../.github/workflows/cd.yml#L45) differs from 20-minute task; no 15-minute outcome evidence. | AUD-017-018, AUD-017-020 |
| T049 | [x] | IMPLEMENTED | [Drift limit](../../../.github/workflows/drift-detection.yml#L24) is 30 minutes. | AUD-017-022 |
| T050 | [x] | PARTIAL | [Environment association](../../../.github/workflows/cd.yml#L40) enables native tracking; phase-accurate status beyond output/summary not established. | AUD-017-016, AUD-017-022 |
| T051 | [x] | UNVERIFIED | [Rollback source](../../../scripts/rollback.sh#L1)/mode inspected, no scoped shellcheck receipt. | AUD-017-022 |
| T052 | [x] | UNVERIFIED | [Bicep](../../../infra/main.bicep#L1)/params inspected, build/Azure validate not executed or evidenced. | AUD-017-006, AUD-017-019, AUD-017-022 |
| T053 | [x] | UNVERIFIED | [Quickstart procedures](quickstart.md#L48) are not run/approval evidence and some are retired. | AUD-017-018, AUD-017-020, AUD-017-022 |
| T054 | [x] | CONFLICT | [Current old-shape assertions](../../../tests/devops/test_cd_workflow.py#L49) contradict current YAML; a historic successful run is neither proven nor ruled out. | AUD-017-017, AUD-017-022 |

## Checklist and Review Evidence

No local signed implementation review or execution receipt accompanies the seven historical artifacts. The canonical tasks' prerequisite and checkpoint claims are design/checkbox assertions; writing tests first, observing initial failures, end-to-end validation and approvals are **UNVERIFIED**. AUD-017-022 obtains later evidence without altering those original records.

### Sixteen Originally Checked Quality Assertions

Q labels identify source order; descriptive labels are retained to make this assessment usable without opening another report.

| Claim | Original checkbox | Status | Assessment / follow-up |
| --- | --- | --- | --- |
| Q01 No implementation details | [x] | CONFLICT | FRs prescribe paths, tools, YAML and flags; AUD-017-020. |
| Q02 User/business value | [x] | IMPLEMENTED | Five role-based stories explain delivery/recovery/governance value. |
| Q03 Nontechnical stakeholders | [x] | PARTIAL | Accessible stories coexist with technical prescriptions; AUD-017-020. |
| Q04 Mandatory sections complete | [x] | IMPLEMENTED | Required spec sections authored. |
| Q05 No clarification markers | [x] | IMPLEMENTED | No NEEDS CLARIFICATION markers remain in the original spec. |
| Q06 Testable/unambiguous | [x] | PARTIAL | Baseline/expiry/retries/retirement ambiguities persist; AUD-017-020. |
| Q07 Measurable outcomes | [x] | PARTIAL | Numeric targets exist, measurement denominator/window incomplete; AUD-017-018. |
| Q08 Technology-agnostic SCs | [x] | CONFLICT | Azure regions and GitHub issue mechanism prescribed; AUD-017-020. |
| Q09 All scenarios defined | [x] | IMPLEMENTED | All 18 acceptance scenarios authored, not necessarily executed. |
| Q10 Edge cases identified | [x] | IMPLEMENTED | Ten original edge cases present. |
| Q11 Scope bounded | [x] | PARTIAL | Original exclusions clear, changed authority needs mapping; AUD-017-020. |
| Q12 Dependencies/assumptions identified | [x] | PARTIAL | Lists exist, selection/health/seed/permission assumptions need correction; AUD-017-006, AUD-017-020. |
| Q13 Every FR clear acceptance | [x] | PARTIAL | Expiry/persistence/security cases not fully operationalized; AUD-017-008, AUD-017-017. |
| Q14 Primary flows covered | [x] | IMPLEMENTED | Deploy/gates/recovery/isolation/drift stories present. |
| Q15 Feature meets outcomes | [x] | UNVERIFIED | No scoped measurements/deployment receipts; AUD-017-018, AUD-017-022. |
| Q16 No implementation leakage | [x] | CONFLICT | Concrete FR prescriptions contradict this and the checklist note; AUD-017-020. |

The quality checklist's "all 16 pass" and "tooling confined to assumptions/constraints" notes are contradicted by the detailed FRs and do not certify completion. Their original [x] states remain intact.

### Eighty-Seven Originally Unchecked Comprehensive Questions

These rows answer requirement-quality questions, not invent 87 mandatory new features. Source states remain **[ ]** even where a question can now be answered. Owner decisions may explicitly bound gaps rather than expand product scope.

| ID | Original checkbox | Status | Scoped assessment / follow-up |
| --- | --- | --- | --- |
| CHK001 | [ ] | PARTIAL | Deployment order and partial-success recovery not defined sufficiently; AUD-017-005, AUD-017-020. |
| CHK002 | [ ] | SUPERSEDED | Main-only filtering explicitly replaced by environment branches; AUD-017-020. |
| CHK003 | [ ] | IMPLEMENTED | Web content checks explicitly excluded; independent worker readiness still required; AUD-017-004. |
| CHK004 | [ ] | PARTIAL | Outputs/helper exist, complete durable baseline consumer absent; AUD-017-003. |
| CHK005 | [ ] | PARTIAL | T036 defines skip, but source cannot separate error from true first run; AUD-017-001. |
| CHK006 | [ ] | PARTIAL | Contributor guidance does not establish role-assignment/data-plane grants; AUD-017-006, AUD-017-010. |
| CHK007 | [ ] | SUPERSEDED | Same OIDC intent replaced with per-env credential login; AUD-017-008. |
| CHK008 | [ ] | IMPLEMENTED | Local drift contract specifies title/label/table/metrics/next steps; fidelity incomplete; AUD-017-014. |
| CHK009 | [ ] | SUPERSEDED | Production was specified locally; current direct branch job replaces chain; AUD-017-020. |
| CHK010 | [ ] | PARTIAL | Logs described, retention/immutability/reviewer receipts absent; AUD-017-016, AUD-017-022. |
| CHK011 | [ ] | PARTIAL | Dev routing exists; effective config/extensibility boundary unresolved; AUD-017-006, AUD-017-020. |
| CHK012 | [ ] | IMPLEMENTED | Host strategy documented in assumptions/local rollback contract; implementation incomplete; AUD-017-002. |
| CHK013 | [ ] | PARTIAL | Service lists hard-coded, no maintained parity assertion; AUD-017-004, AUD-017-017. |
| CHK014 | [ ] | PARTIAL | Entire CI success required; advisory typing/separate security differ; AUD-017-007. |
| CHK015 | [ ] | UNVERIFIED | Actual reviewer authorization/config absent; AUD-017-008. |
| CHK016 | [ ] | PARTIAL | Known-good intent not equivalent to second active revision; AUD-017-001, AUD-017-003. |
| CHK017 | [ ] | PARTIAL | Report fields stated but phase/service completeness incomplete; AUD-017-016. |
| CHK018 | [ ] | PARTIAL | Static guidance exists, phase-specific remediation incomplete; AUD-017-016. |
| CHK019 | [ ] | PARTIAL | Critical/manual-intervention semantics stated, false skip suppresses them; AUD-017-001, AUD-017-016. |
| CHK020 | [ ] | PARTIAL | Separate group/vault intent stated, actual negative isolation not shown; AUD-017-010. |
| CHK021 | [ ] | PARTIAL | No measurable redesign/config-change boundary; AUD-017-020. |
| CHK022 | [ ] | IMPLEMENTED | Local Property Change/report defines granularity; parser still lossy; AUD-017-014. |
| CHK023 | [ ] | PARTIAL | R-004 sleeps between attempts; retry/attempt wording needs consistency; AUD-017-004, AUD-017-020. |
| CHK024 | [ ] | IMPLEMENTED | Pass 2 expressly corrects six to four, preserving historical log; AUD-017-020. |
| CHK025 | [ ] | SUPERSEDED | Original gate types/order documented; chained jobs retired, assurance incomplete; AUD-017-007. |
| CHK026 | [ ] | PARTIAL | Manual gate originally follows automatic checks; replacement/expiry unresolved; AUD-017-008. |
| CHK027 | [ ] | PARTIAL | Failure notification intent complete, actual state/delivery failures not; AUD-017-016. |
| CHK028 | [ ] | CONFLICT | Historical parallelism resolves serial arithmetic; actual five-attempt path violates bound; AUD-017-004. |
| CHK029 | [ ] | PARTIAL | Budget includes restore plus health; serial code exceeds it; AUD-017-013. |
| CHK030 | [ ] | PARTIAL | Original AU language consistent, current carve-out/primary-only rule needs map; AUD-017-019, AUD-017-020. |
| CHK031 | [ ] | SUPERSEDED | Workflow secret exception explicit, app-secret isolation retained; AUD-017-010, AUD-017-020. |
| CHK032 | [ ] | UNVERIFIED | Local phase estimates not measured feasibility; AUD-017-018. |
| CHK033 | [ ] | PARTIAL | 95% target lacks denominator/window; AUD-017-018. |
| CHK034 | [ ] | PARTIAL | Setup documented, zero-manual-step measurement boundary not; AUD-017-018, AUD-017-020. |
| CHK035 | [ ] | PARTIAL | Gate completion given as origin, delivered-report timestamp absent; AUD-017-016, AUD-017-018. |
| CHK036 | [ ] | UNVERIFIED | No named original/current CI regression receipt; AUD-017-022. |
| CHK037 | [ ] | PARTIAL | Scenarios actionable, failure/identity/timing assertions incomplete; AUD-017-017. |
| CHK038 | [ ] | SUPERSEDED | Local full chain documented, current branch design intentionally differs; AUD-017-020. |
| CHK039 | [ ] | SUPERSEDED | Production contract present, old job now explicitly retired; AUD-017-020. |
| CHK040 | [ ] | PARTIAL | Clean summary exists but malformed input can reach it; AUD-017-009. |
| CHK041 | [ ] | PARTIAL | Infra-only change still runs full provision/deploy path; compensation needs decision; AUD-017-005. |
| CHK042 | [ ] | PARTIAL | Service-only change also provisions/seeds; not an isolated service transaction; AUD-017-005, AUD-017-006. |
| CHK043 | [ ] | PARTIAL | Timeout/retry policy absent; wait timer not rejection mechanism; AUD-017-008. |
| CHK044 | [ ] | PARTIAL | Platform rerun possible in principle, same-SHA recovery not tested; AUD-017-003, AUD-017-017. |
| CHK045 | [ ] | IMPLEMENTED | Local drift next steps distinguish intentional reconciliation; report safety incomplete; AUD-017-014. |
| CHK046 | [ ] | CONFLICT | Local deploy-failure rollback conflicts with health-only guard; AUD-017-005. |
| CHK047 | [ ] | IMPLEMENTED | Source success/push condition excludes failure/cancelled/skipped/PR runs; AUD-017-017 maintains tests. |
| CHK048 | [ ] | PARTIAL | Failed provision stops later steps, partial mutation classification incomplete; AUD-017-005. |
| CHK049 | [ ] | PARTIAL | Exit codes authored, runtime error/session/caller contract untested; AUD-017-012, AUD-017-017. |
| CHK050 | [ ] | PARTIAL | Discovery swallows network failures despite other fail-fast steps; AUD-017-001, AUD-017-016. |
| CHK051 | [ ] | PARTIAL | Distinct failure phases not faithfully summarized; AUD-017-016. |
| CHK052 | [ ] | PARTIAL | Manual intervention stated, hold/resume behavior needs decision; AUD-017-016, AUD-017-020. |
| CHK053 | [ ] | PARTIAL | Lost/corrupt baseline not distinguished safely from bootstrap; AUD-017-003. |
| CHK054 | [ ] | IMPLEMENTED | Local report defines review/reconcile/close process, no actual remediation claimed. |
| CHK055 | [ ] | PARTIAL | Provision can mutate apps/data; partial infrastructure recovery not no-op; AUD-017-005. |
| CHK056 | [ ] | IMPLEMENTED | Explicit web HTTP-200 content exclusion remains scope boundary. |
| CHK057 | [ ] | PARTIAL | Lock does not demonstrate durable FIFO/every pending commit execution; AUD-017-017, AUD-017-020. |
| CHK058 | [ ] | PARTIAL | First healthy attempt wins; flapping policy needs owner decision; AUD-017-004. |
| CHK059 | [ ] | PARTIAL | Pinned actions coexist with changing runner/CLI dependencies; AUD-017-017, AUD-017-022. |
| CHK060 | [ ] | IMPLEMENTED | Local R-006 documents fixed UTC and accepted AEDT shift. |
| CHK061 | [ ] | PARTIAL | No release-context/coordination between drift and active deploy; AUD-017-015. |
| CHK062 | [ ] | PARTIAL | gh failure fails step but report not retained as promised; AUD-017-014. |
| CHK063 | [ ] | CONFLICT | Local budgets, 20-minute task and 60-minute current job differ; AUD-017-018, AUD-017-020. |
| CHK064 | [ ] | UNVERIFIED | Outage/delayed schedule recovery and cadence not demonstrated; AUD-017-018, AUD-017-022. |
| CHK065 | [ ] | PARTIAL | Prefixes/summaries exist but complete release/service provenance missing; AUD-017-003, AUD-017-016. |
| CHK066 | [ ] | PARTIAL | Claimed cheaper staging not established by effective tier/SKU selection; AUD-017-006, AUD-017-020. |
| CHK067 | [ ] | PARTIAL | Security contract exists, auth/input/dry-run/discovery issues remain; AUD-017-002, AUD-017-012. |
| CHK068 | [ ] | UNVERIFIED | Approval identities and retention configuration not inspected; AUD-017-008, AUD-017-022. |
| CHK069 | [ ] | PARTIAL | Per-env lock declared, backlog and latency/delivery guarantees unmeasured; AUD-017-018. |
| CHK070 | [ ] | CONFLICT | API configuration-only health, private agents and headless ingestion undermine assumed reachability; Docker health instructions not pipeline proof; AUD-017-004. |
| CHK071 | [ ] | PARTIAL | Setup action pinned, azd version contract not fixed/tested; AUD-017-017, AUD-017-022. |
| CHK072 | [ ] | PARTIAL | Env/location parameters exist but production tier and effective selector missing; AUD-017-006. |
| CHK073 | [ ] | PARTIAL | Toolchain setup authored, seed/shell/CLI availability not successful-run evidence; AUD-017-022. |
| CHK074 | [ ] | IMPLEMENTED | Quickstart documents required reviewers; actual policy UNVERIFIED; AUD-017-008. |
| CHK075 | [ ] | PARTIAL | Quota/subscription/auth prerequisites listed, full role/provider/data-plane readiness not shown; AUD-017-006, AUD-017-022. |
| CHK076 | [ ] | PARTIAL | Shared Bicep entrypoint documented, selector/hook effects not fully modeled; AUD-017-005, AUD-017-006. |
| CHK077 | [ ] | IMPLEMENTED | R-004 expressly resolves old serial math with parallel checks; current implementation still differs; AUD-017-004. |
| CHK078 | [ ] | CONFLICT | Original CI-verification/repeated-security order explicit; later deletion relies on absent CI audit; AUD-017-007. |
| CHK079 | [ ] | IMPLEMENTED | Pass-2 correction means six-service historical note is not active scope. |
| CHK080 | [ ] | PARTIAL | Host recovery relationship described, durable target/artifact connection absent; AUD-017-002, AUD-017-003. |
| CHK081 | [ ] | IMPLEMENTED | Dedicated environment vault intent clear, retained app-secret path incomplete; AUD-017-010. |
| CHK082 | [ ] | PARTIAL | AU primary restriction exists, failover pipeline ownership not demonstrated; AUD-017-019, AUD-017-020. |
| CHK083 | [ ] | IMPLEMENTED | Fifteen unique FR IDs plus separately identified capstone amendment. |
| CHK084 | [ ] | IMPLEMENTED | Complete scenario trace supplied here, product proof still partial. |
| CHK085 | [ ] | IMPLEMENTED | All SCs mapped to behavior/evidence, measurements not implied. |
| CHK086 | [ ] | PARTIAL | All ten edges traced, provision/expiry/recovery conflicts persist; AUD-017-005, AUD-017-008. |
| CHK087 | [ ] | IMPLEMENTED | Source assigns priorities to stories, not every FR; no invented per-FR priority requirement. |

## Future Validation Commands and Acceptance Evidence

**These are instructions for future authorized work, not commands run during this audit.** Proposed fixtures belong in the existing homes named below; their tests are not claimed to exist today. Establish an isolated runner and use fake commands for unit-level checks. Cloud/approval/release exercises require separate explicit consent and scoped identities; never print credentials.

| Code | Future command / procedure | Prerequisites / expected assertions |
| --- | --- | --- |
| V-CD | `pytest tests/devops/test_cd_workflow.py -q` | Configured Python/PyYAML and maintained offline fixtures; assert branch/event/SHA, dependencies, parameters, approvals, phase results and four-service readiness. |
| V-RB | `pytest tests/devops/test_rollback_script.py -q` | Bash runner with sentinel az/curl/clock/artifact commands and no live credentials; assert exact targets/exits, zero-call dry-run, idempotence, deadlines and all-service restore. |
| V-DRIFT | `pytest tests/devops/test_drift_detection.py -q` | Fake CLI/gh, pinned-shaped payloads; valid-clean only, exact values/nesting/metrics, safe retained report and correct release context. |
| V-PARAM | `pytest tests/devops/test_parameter_files.py -q` | Extended rendered-parameter/resource graph fixtures; distinct effective env settings, production-tier/identity binding, AU constraints, no unresolved substitutions. |
| V-SUITE | `pytest tests/devops -q` | All maintained dependencies and new fixtures, no product/cloud execution; no unexpected failures/skips; guard-removal mutations must fail the intended tests. |
| V-LINT | `shellcheck scripts/rollback.sh`; `actionlint .github/workflows/ci.yml .github/workflows/cd.yml .github/workflows/drift-detection.yml .github/workflows/staging-promotion.yml` | Pinned installed tools; no syntax/shell errors. Lint success is not runtime or approval proof. |
| V-SOV | `pwsh -NoProfile -File scripts/verify-carveout.ps1 -RegistryPath "$REGISTRY_FIXTURE" -WhatIfPath "$WHAT_IF_FIXTURE" -Strict` | PowerShell, Python YAML dependency and synthetic fixtures; fail invalid schema/binding/expiry/location/reviewer, pass approved matching intent, no cloud session. |
| V-IAC | `az bicep build --file infra/main.bicep --stdout`; `az deployment group validate --resource-group "$AUDIT_SANDBOX_RG" --template-file infra/main.bicep --parameters "@$RENDERED_PARAMS"` | Later authorization, pinned CLI/modules, isolated group, scoped identity, selected rendered params and policy/role prerequisites. Capture per-env validation receipts; compile/validate is not proof of live deployment or isolation. |
| V-POLICY | `gh api "repos/$REPOSITORY/environments/production"`; inspect approved/denied/expired run records | Admin consent, redacted actual settings/receipts; matching reviewers/SHA/environment and 72h expiry enforced, read-only drift independent, no secret data exposed. |
| V-REHEARSAL | Controlled authorized environment-branch release/failure rehearsal; `gh run view "$RUN_ID" --repo "$REPOSITORY" --json headSha,event,conclusion,jobs,url` | Recovery operator, known-good packages, sandbox state and scoped identity. Capture four-service restoration, failed-gate blocking, reporting/latency/denominator evidence. CD has no workflow_dispatch, so do not propose dispatching cd.yml. |
| V-DOC | `npx --no-install markdownlint-cli2 specs/017-cd-pipeline/implementation-review-tasks.md specs/feature/017-cd-pipeline/implementation-review-tasks.md` and scoped text/link/ID checks | Documentation tooling already installed; verify all original states/rows, complete local artifact assessments, 22 unchecked follow-ups, resolving source paths and in-bounds line references. No product execution. |

## Closure Standard

This historical report is usable on its own: it contains the local artifact assessments, canonical task states, all retained requirement/scenario/checklist dispositions and complete developer/tester remediation instructions. It does not certify that any original checked task was successfully executed. Closure requires future implementation plus appropriate isolated tests and separately authorized runtime/approval evidence; report-text validation alone establishes only coverage, checkbox integrity, follow-up completeness, local link/line validity and editor diagnostics.
