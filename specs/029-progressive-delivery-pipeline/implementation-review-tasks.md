# Spec 029 Static Implementation Review

## Metadata and Boundaries

- Review date: 2026-09-14.
- Expected and confirmed HEAD: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`.
- Scope: only the obligations of spec 029, traced into their existing implementation dependencies.
- Method: fresh independent static review; no delegation, product execution, cloud operations, or external approvals.
- Only this report is writable. Original specifications, task states, checklists, evidence, source, configuration,
  the audit index, branches, and commits are unchanged by this review.
- No pre-existing report was present; no prior implementation review was used. No other specification's
  implementation-review-tasks document was read.
- Authority: [review contract](../001-spec-implementation-audit/README.md#L11) and
  [code review instructions](../../.github/instructions/code-review.instructions.md#L1).
- All 13 local inputs were read in full: [spec.md](spec.md), [tasks.md](tasks.md), [plan.md](plan.md),
  [research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md),
  [requirements checklist](checklists/requirements.md),
  [posture matrix contract](contracts/posture-matrix.schema.yaml),
  [exception contract](contracts/posture-exceptions.schema.yaml),
  [evidence contract](contracts/evidence-pack.schema.json), [audit contract](contracts/audit-event.schema.json),
  [canary contract](contracts/canary-promotion.api.md), and [key-issuance contract](contracts/dev-key-issue.workflow.md).
- There are no separate local evidence, validation, amendment, or review files beyond the embedded records above.
  Local filesystem inventory, including directory existence checks, was used rather than assuming search-index completeness.
- Additional applicable guidance read: [Bicep conventions](../../.github/instructions/bicep-code-best-practices.instructions.md),
  [policy compliance](../../.github/instructions/bicep-policy-compliance.instructions.md),
  [commenting guidance](../../.github/instructions/code-commenting.instructions.md),
  [review checklist](../../.github/instructions/references/code-review-checklists.md),
  [current development guidelines](../../.github/agents/copilot-instructions.md), and the installed
  `python-fact-grounded-coding` skill. Only its static evidence discipline was used; no imports, interpreter probes,
  Pylance runtime operations, tests, verifier scripts, builds, browser sessions, servers, installs, or cloud calls were run.
- Source support establishes authored behavior, not successful execution, deployed state, measured success, or human sign-off.
  Those outcomes remain UNVERIFIED without the corresponding evidence.

## Review Conclusion

The original spec-029 progressive-delivery implementation is operationally retired by explicit repository
decisions, not fully delivered by the current pipeline. This report is not a completion certification or an
authorization to restore the retired architecture. Current shared CD, rollback, drift, infrastructure, gateway
and metric risks are included only where spec 029 independently requires that behavior; local historical
contract, checklist and evidence conflicts are separately accounted for under AUD-029-011.

Coverage is complete for 94 original tasks, 34 FRs, 18 SCs, 40 acceptance scenarios, 15 edge cases,
16 clarification answers and all 16 original checklist items. Additional accounting covers 17 research decisions,
10 nonfunctional constraints, six contracts, 15 entities, seven quickstart flows and the original review checkpoints.
There are 11 stable unchecked follow-ups: nine P1 and two P2. All 18 measured success criteria remain UNVERIFIED.
Original task statuses: 45 SUPERSEDED, 17 MISSING, 14 PARTIAL, 2 CONFLICT and 16 UNVERIFIED; no original checkbox changed.

## Controlling Path and Supersession

[cd.yml](../../.github/workflows/cd.yml#L19) accepts completed CI runs only on the three environment branches;
the deploy job additionally requires a successful push-triggered CI run. It provisions and deploys through
[azure.yaml](../../azure.yaml#L8), rebuilding from the checked-out source rather than promoting a signed digest.
[Spec 031 research](../031-simplify-cicd-pipeline/research.md#L83) explicitly records branch-based replacement,
weekly drift detection, and deletion of the spec-029 workflows, helper package, identity record, and policy bundle.
[ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L3) records a time-bound credential-based
identity deviation and explicitly preserves the constitutional residency obligation. Retirement is not delivery,
and is not evidence of human review or deployment success.

## Prioritized Findings and Follow-Ups

### P1: Retained Rollback Can Report Success Without Restoring Service

- [ ] AUD-029-001 Make retained rollback fail closed on unresolved targets and verify restoration

**Obligations:** FR-008, FR-021, FR-023; SC-004, SC-010; US4 acceptance 2 and 5; T031, T046, T047, T049,
T057, T081, T082. The retired burn-rate mechanism is not being requested back; the retained health-failure
rollback must still have a truthful outcome.

**Expected / actual / impact:** CD discovers `ca-api-drh-{env}`, `ca-agents-drh-{env}`, `ca-ingest-drh-{env}`
and a dynamically named App Service, but its [rollback invocation](../../.github/workflows/cd.yml#L355)
passes only environment and resource group. [Revision discovery](../../scripts/rollback.sh#L153) and rollback
construct `{env}-{service}` instead, suppress Azure lookup errors into an empty string, and take the second
unsorted active revision rather than a verified known-good record. [Web rollback](../../scripts/rollback.sh#L240)
skips when no deployment is supplied. If all targets are empty, the
[bootstrap branch](../../scripts/rollback.sh#L376) exits zero before health verification; CD then reports
`rolled-back` and does not enter its rollback-failure alert path. An unresolved or unauthorized lookup can
therefore masquerade as successful restoration after an actual health failure.

**Developer:** Preserve branch/environment binding and the no-dev-rollback decision. Pass validated actual
resource IDs and pre-deploy known-good targets for all four services; distinguish genuine first deployment
from lookup/authentication failure; reject unknown targets during a regression. Use an immutable web package
locator rather than a site ID as `config-zip --src`. Restore once, verify all relevant internal/external health
paths, and propagate failure to the critical issue step without retrying arbitrary historical revisions.
Keep known-good retention and schema changes compatible with existing consumers.
Use the validated upstream `head_sha` in records: CD currently passes `github.sha` to
[known-good update](../../.github/workflows/cd.yml#L340), emits only API/web in its revisions JSON,
and never reads that manifest in the rollback call. The
[current manifest](../034-webapp-capstone-coverage/known-good.json#L4) has no entries or update timestamp.
Retain at least three independently healthy targets per service, or explicitly resolve the retired signed-digest
retention requirement before making any corresponding claim. Discovery order is not health evidence.

**Tester:** Extend [tests/devops/test_rollback_script.py](../../tests/devops/test_rollback_script.py) and
[tests/devops/test_cd_workflow.py](../../tests/devops/test_cd_workflow.py). Add mocked Azure CLI and HTTP fixtures
for the actual resource names, explicit known-good targets, shuffled revisions, 403/not-found/empty responses,
first deploy with failed health, missing web package, internal-only services, failed activation, and failed
post-rollback health. Assert no mutation for an invalid target, no success on lookup failure, one restoration
attempt, and a critical issue when restoration fails. Test successful restoration separately from bootstrap.

**Future validation only:** In a prepared offline test environment with the repository's test dependencies,
run `pytest tests/devops/test_rollback_script.py tests/devops/test_cd_workflow.py -q` after adding command-level
mock fixtures. Expected: all positive and fail-gate cases pass without real cloud calls. A later authorized
isolated deployment drill must measure restoration latency and prove the health outcome; none was run here.

**Done:** Actual deployed resources are restored to independently recorded known-good versions; failures cannot
be reported as successful rollback; regression assertions are gate-connected and the measured drill is separately evidenced.

### P1: Green CI Does Not Establish the Required Delivery Gates

- [ ] AUD-029-002 Bind required checks to the exact deployment candidate and exercise failing gates

**Obligations:** FR-001, FR-003, FR-006, FR-023; US3-AS1, US3-AS3, US9-AS5;
T040, T041, T042, T043, T044, T074, T079a, T080, T084, T086, T088.

**Expected / actual / impact:** The declared gate set must block a bad candidate before deployment.
[CD](../../.github/workflows/cd.yml#L19) listens only for `ci` success.
[Security scanning](../../.github/workflows/security-scan.yml#L8) runs separately; neither it nor
[staging promotion](../../.github/workflows/staging-promotion.yml#L28) is a CD prerequisite.
[CodeQL](../../.github/workflows/codeql.yml#L9) is manual and its analysis steps are commented out.
[CI](../../.github/workflows/ci.yml#L128) tolerates Python type errors, runs contract/integration suites but
does not invoke the general unit, simulation, or DevOps suites, and has a warn-only citation accessibility job.
The security job scans the filesystem, not every built deployment image. No rendered PR What-If/029 policy
driver, independent fourteen-category gate set, or universal structured failure reporter is connected.
The [branch-protection file](../../.github/branch-protection.json#L2) explicitly says it is descriptive only.
A successful `ci` run can therefore start CD while another required check is failed or still running.

**Developer:** Agree the retained gate contract under spec 031; do not restore deleted canary jobs by implication.
Make every retained mandatory check a dependency of a single authoritative candidate result, bound to upstream
commit and push context. Gate deployment on that result, including failure, cancellation, missing check, and
timeout. Keep PR/fork checks unprivileged; do not give untrusted PR code production credentials to run What-If.
Add fail-closed secret/configuration validation and image scanning at the appropriate candidate boundary.
Preserve explicit, approved adoption exceptions rather than disguising warning-only checks as full delivery.
Require a maintainer-applied protection snapshot separately from repository configuration.

**Tester:** Update [CD tests](../../tests/devops/test_cd_workflow.py#L48),
[rollback tests](../../tests/devops/test_rollback_script.py#L1), and
[shared YAML fixtures](../../tests/devops/conftest.py#L69). Existing CD tests expect `main`, `id-token: write`,
and `deploy-staging`, contrary to active source; rollback tests assert strings, not command results.
Create offline event fixtures for successful CI with failed security, absent/cancelled checks, mismatched SHA,
PR versus push, each environment branch, unsafe parameters, a vulnerable built image, and unavailable SAST.
Assert zero deployment calls on every adverse fixture, correct candidate checkout on success, accurate failure
links, and that the selected DevOps regression tests themselves occur in the authoritative CI path.

**Future validation only:** With Python test dependencies, a YAML loader preserving Actions `on`, and a
mocked workflow/command harness, run `pytest tests/devops/test_cd_workflow.py tests/devops/test_rollback_script.py -q`.
Expected: candidate-gate denial and current branch behavior pass offline. Later authorized representative PR
runs must provide gate timing and required-check receipts; no run was performed in this review.

**Done:** Failure of a mandatory check prevents the same candidate reaching any deploy step; tests reflect
the current graph and are invoked by it; remote protection and measured budgets are separately evidenced.

### P1: Retained Posture Declarations Do Not Control the Deployed Stack

- [ ] AUD-029-003 Resolve and enforce the retained environment posture at the active deployment root

**Obligations:** FR-017, FR-025, FR-026, FR-027, FR-028, FR-029, FR-031, FR-032; SC-014, SC-015;
T010, T014, T015, T018, T019, T019a, T025, T060, T061, T062, T064, T065, T082, T083, T085.

**Expected / actual / impact:** Three isolated environments must have an effective, reviewable posture.
The [current matrix](../../infra/policy/posture-matrix.yaml#L1) is explicitly a spec-033 retention stub; it has
none of the original environment/resource-type matrix structure. The
[retained initiative](../../infra/bicep/modules/posture-policy-set.bicep#L7) hard-codes three built-in IDs,
always has subscription scope, and uses `subscriptionTopology` only as metadata. It neither reads the matrix
nor switches assignment scope, and neither root template calls it.
[Active ACR/Storage/Cosmos](../../infra/main.bicep#L479) enable ACR admin credentials and public data-plane access;
Cosmos metadata-write protection is not `disableLocalAuth`. Container configuration embeds evaluated ACR
passwords [directly](../../infra/main.bicep#L1015), not Key Vault references. These are not alleged literal leaked
credentials in Git; the defect is the deployed authentication/configuration path.
[Parameter files](../../infra/parameters/production.bicepparam#L1) preserve tags/topology but do not set the
required auth/network differences. CD uses [azd's root](../../azure.yaml#L8), not those `.bicepparam` files.
`subscriptionTopology` is merely [exported](../../infra/main.bicep#L1430), not validated against the target.

**Developer:** Obtain a scoped decision on which private-network, identity, isolation, and unknown-type rules
survive the spec-031 retirement. Then express them in the actual root and actual parameter path, with one
canonical environment-token mapping. Do not re-enable portal overrides or weaken existing Azure Policy.
For retained A/B support, enforce subscription/RG boundaries before mutation and select policy assignment
scope accordingly; do not treat a declared GUID or output as an assertion. Replace registry passwords with
supported managed-identity pulls, add service-specific private endpoints/DNS, and ensure the deployment runner
has an approved private access route. Connect a full inventory verifier and fail/rollback regulated deployments
on violations; dev may create a tracked issue only if that asymmetry is explicitly retained. Distinguish
unsupported service capabilities with named, approved exceptions, not silent defaults.

For retained dev anomaly/JIT requirements, connect the
[Defender module](../../infra/bicep/modules/defender-baseline.bicep#L9), Entra risk-event forwarding and authenticated
audit ingestion, plus [Bastion/jump-host](../../infra/bicep/modules/jump-host.bicep#L25) with actual PIM activation,
time limits and session logs. Pricing resources and boot diagnostics do not implement those controls. Any API
addition requires explicit resolution of T085 versus the plan's no-application-source-change boundary.

**Tester:** Extend [parameter-file tests](../../tests/devops/test_parameter_files.py) and
[CD tests](../../tests/devops/test_cd_workflow.py); proposed new test: `tests/devops/test_delivery_posture.py`.
Use offline resource payloads for dev/public/authenticated, staging/private/MI, production/public or shared-key,
unknown type, empty/incomplete inventory, nested foreign Key Vault ID, same-RG/different-subscription reference,
both topologies, mixed topology, missing tags, and a parameter file not consumed by CD.
Assert exact resource/property/rule diagnostics, denial before deploy, correct policy scope, and no password value
in generated application settings. Test error and pagination paths for any future inventory adapter.

For anomaly/JIT adapters, add signed alert, wrong-tenant alert, unauthenticated ingestion, disabled forwarding,
expired PIM and missing session-log fixtures; assert only authorized alerts reach the AU audit store and expired
access is denied without opening a public backend.

**Future validation only:** After the agreed implementation and prepared local dependencies, run
`pytest tests/devops/test_parameter_files.py tests/devops/test_delivery_posture.py -q` against offline fixtures.
Expected: all adverse configurations are denied and both approved topology modes pass. Bicep validation and
authorized isolated posture/rollback trials are subsequent prerequisites to deployed-state claims, not this audit.

**Done:** The active deployment path consumes the approved posture, validates its actual target, and cannot
silently deploy dev-grade configuration to a regulated environment; all retained rules have fail-gate tests.

### P1: The Relocated Carve-Out Check Does Not Verify the Resources Being Deployed

- [ ] AUD-029-004 Bind carve-out approval to rendered model resources and validated reviewer evidence

**Obligations:** FR-018; SC-006; US3-AS3; edge 9; R13; T011, T016, T017, T042, T067, T085.

**Expected / actual / impact:** Credit the restored pre-provision registry check, but it does not establish full
registry/resource parity. [CD](../../.github/workflows/cd.yml#L214) passes `-RegistryPath` and `-Strict`, never
`-WhatIfPath`. [The optional walker](../../scripts/verify-carveout.ps1#L118) is therefore skipped.
[Model defaults](../../infra/modules/azure-openai.bicep#L28) are `gpt-5.4`, with three environment-suffixed
deployment names; [the registry](../../infra/parameters/foundry-carveout.yaml#L21) instead lists `gpt-4o-mini`,
`gpt-4o`, and embeddings. The walker compares a deployment-name segment to `model_name`, and reads
`change.location` rather than consistently extracting the resource payload. It validates selected AI resource
types only. [Review validation](../../scripts/verify-carveout.ps1#L86) counts strings, not distinct authenticated
approvers, and rejects dates older than six months but does not reject every already-expired review date.
`-Strict` writes warnings without adding them to the error list. The
[new Rego file](../../infra/policy/rego/foundry_carveout.rego#L1) is not invoked by the PowerShell CD script.

[Its contract test](../../tests/contract/test_foundry_carveout.py#L75) falls back to a Python reimplementation
when OPA is unavailable; the inspected CI install steps do not install OPA. That fallback even defaults a missing
environment to production, whereas the Rego's legacy branch applies the dev floor. It cannot prove policy execution.

**Developer:** Retain the explicit modern AU-only model policy unless a new approved decision changes it.
Use a versioned structured registry and normalized ARM resource/model identities; compare it to the exact
rendered candidate across nested resources and effective locations before provisioning. Require valid schema,
current expiry, actual distinct reviewer identities and approval references; missing/empty/parsing failures must
deny, not skip. Enforce every non-model data-persisting resource's AU boundary. Resolve the two registry
locations' authority and OPA/PowerShell differences without resurrecting the retired 029 registry silently.

**Tester:** Extend [carve-out workflow tests](../../tests/devops/test_foundry_carveout_workflow.py), which currently
cover review-comment helpers, not this deploy decision; proposed `tests/devops/test_carveout_deploy_gate.py`.
Fixtures: matching suffixed deployment with correct model/version, current `gpt-5.4` mismatch, missing registry,
empty deployments, duplicate reviewer, expired yesterday, exactly expiry, invalid date, future review beyond
the cap, nested resource location, foreign Storage/Cosmos, and malformed What-If. Assert a nonzero gate and zero
provision calls on each invalid fixture; positive fixtures must verify the actual candidate, not just registry text.

If OPA remains authoritative, test it with the actual engine and make absence/parsing failure a gate failure;
include the missing-environment fixture rather than certifying an independently reimplemented rule.

**Future validation only:** With PowerShell 7 and test dependencies in an isolated offline harness, run
`pytest tests/devops/test_carveout_deploy_gate.py tests/devops/test_foundry_carveout_workflow.py -q`.
The proposed test must substitute local render/registry fixtures and prohibit Azure/GitHub calls.
Expected: exact resource/model mismatch diagnostics and fail-closed approval/date behavior.

**Done:** Every deployed resource is evaluated against the authoritative, valid approval registry; stale,
duplicate, absent, or mismatched approvals cannot yield a green deployment preflight.

### P1: Gateway Fallback Can Bypass the Retained Non-AU Privacy Boundary

- [ ] AUD-029-005 Fail closed when model-region or data-minimisation assurance is unavailable

**Obligations:** FR-018, R14, constitution NN-2; SC-006; T016 and T087's retained FR-018 coverage obligation.

**Expected / actual / impact:** Non-AU transit requires minimisation of personal/classified content.
[The client](../../apps/agents/common/foundry_chat_client.py#L363) returns messages unchanged when region is
unset or the gateway import fails, and transforms only string `user` messages. System/tool/structured content
and tools remain outside that guard. [The gateway](../../apps/agents/common/model_gateway.py#L130) catches
Presidio absence/failure and falls back to regex patterns that do not cover names or addresses.
[Tests](../../tests/integration/test_data_minimisation_gateway.py#L27) exercise the helper's phone redaction,
classification denial, and AU bypass, not the live client's bypass branches. Active Bicep defaults are AU;
this is a source-proven unsafe configurable non-AU path, not a claim that regulated data has actually left AU.

**Developer:** Depend on AUD-029-004 for trusted endpoint/region binding. Reject unknown region or unavailable
mandatory classifier/redactor at the boundary, or route to an explicitly approved local fallback without
transmission. Cover every content-bearing request field and response handling required by the retained
contract. Do not classify tool schemas or arbitrary nested data by blind string replacement; use their typed
content contracts. Preserve existing sync/async signatures and AU behavior only where explicitly authorized.
Emit redacted allow/deny audit metadata without the denied payload; do not weaken classification to recover availability.

**Tester:** Extend [gateway integration tests](../../tests/integration/test_data_minimisation_gateway.py) using
injected clients. Include non-AU missing region metadata, gateway import failure, Presidio failure with a person
name/address, classified system/tool messages, structured message content, tools containing regulated data,
safe text, and valid approved AU endpoints. Assert denied/fallback cases invoke the remote client zero times;
assert only sanitized payloads reach both sync and streaming clients, and failure logs contain no raw content.

**Future validation only:** In the prepared offline Python environment with injected SDK doubles, run
`pytest tests/integration/test_data_minimisation_gateway.py -q`. Expected: positive sanitized calls succeed;
unknown/unavailable assurance and classified content never cross the remote-call boundary. No model was invoked here.

**Done:** Every supported outbound content path honors the documented regional privacy decision; missing
configuration/dependencies cannot silently convert denial into passthrough; boundary-level assertions prove it.

### P1: Retained Storage Does Not Prove Immutable Deployment Evidence

- [ ] AUD-029-006 Define the surviving deployment evidence obligation and make its retention enforceable

**Obligations:** FR-013, FR-014, FR-015, FR-021; SC-005, SC-010, SC-012; US5-AS1, US5-AS3;
T018, T019, T050, T051, T052, T053, T054, T059, T076, T078, T081.

**Expected / actual / impact:** The old pack producer was explicitly retired, so absence of its CLI is not a
new missing-file defect. But no replacement CD pack is demonstrated. The
[retained store](../../infra/bicep/modules/evidence-store.bicep#L15) uses Microsoft-managed encryption keys,
declares time retention, and declares neither a legal hold nor a lock operation; it has no active root caller.
[Audit storage](../../infra/bicep/modules/audit-store.bicep#L20) declares a non-expiring container, not an
append-only authorization boundary. [The active archive](../../infra/main.bicep#L781) belongs to spec 037;
it is not a CD pack assembler. The [CI publication gate](../../.github/workflows/ci.yml#L406) validates different
evidence artifacts. No inspected CD step captures all gate/scan/approval/What-If outcomes on success and failure,
uploads a signed pack, or confirms its availability before declaring success. Soft delete and no TTL are not WORM.

**Developer:** First record which deployment evidence/retention obligations survive retirement (AUD-029-011).
For retained obligations, connect an always-run evidence finalizer to actual deploy outcomes and AUD-029-007's
versioned audit path. Inventory required content kinds and hashes, sign a canonical manifest, and upload using
least-privileged append/create operations to a validated AU store. Provision and verify the required legal hold,
locked retention and CMK where required; preserve retention for old records during any migration. On storage
outage, do not claim complete evidence: fail closed with a durable immutable buffer, tracked gap and idempotent
replay. Fetch must verify archive and item hashes before safe extraction; block path traversal. Do not overwrite
an immutable pack to reconcile deferred results; append a linked successor with its own signature and audit record.

**Tester:** Proposed `tests/devops/test_deployment_evidence.py`, using fake clock, Blob, signer and audit adapters.
Cover successful and failed deploys, every missing mandatory content kind, corrupt item/manifest, replayed run,
outage during upload/audit, hash mismatch on fetch, unsafe archive paths, and predecessor retention. Assert
success cannot be reported with incomplete evidence, no overwrite/delete operation, exactly-once linked events,
and bounded finalization timing. Test doubles do not prove Azure immutability enforcement.

**Future validation only:** After approving the retained contract and preparing dependencies, run
`pytest tests/devops/test_deployment_evidence.py -q` offline. Expected: all adversarial fixtures fail closed.
A later separately authorized sandbox retention test must document real overwrite/delete denial, effective
legal hold/lock, AU location and restoration of a retained target; no such test or cloud operation ran here.

**Done:** There is an explicit disposition for retired pack obligations; any claimed replacement produces
complete verifiable artifacts and enforceable retention, with real storage denial evidence distinguished from mocks.

### P1: The Audit Contract Does Not Enforce Its Own Amendment

- [ ] AUD-029-007 Reconcile deployment audit schemas and enforce one validated append path

**Obligations:** FR-015, FR-011a, FR-014; T020, T020a, T021, T024, T024a, T052, T085, T086.

**Expected / actual / impact:** T020a requires rationale, environment, topology, commit, nullable PR, gate set,
signature and an explicit deployment event vocabulary, validated before every append.
[The implementation schema](../../contracts/audit-event.schema.json#L8) requires only id/actor/timestamp/action/
outcome; the added fields remain optional, and the enum omits required events such as `deploy.success`,
`deploy.failure`, `promotion`, `rollback`, and `evidence-pack.write`. The
[local schema](contracts/audit-event.schema.json#L8) differs further: no deployment metadata and no additional
properties. The [data model](data-model.md#L136), task prose, and quickstart use several incompatible action names.
The deleted emitter has no active CD replacement. Schema existence cannot establish a unified provenance chain.

**Developer:** Preserve existing incident/operator consumers and historical records. Define a canonical
versioned envelope plus typed event-specific payloads, an explicit migration/translation strategy for legacy
names, and format validation for UTC timestamps, digests and signatures. Require every retained field before
persistence; allow forward-compatible non-required metadata as contracted. Emit from the actual candidate
identity and verified actor, not arbitrary workflow input; privileged actions require independent authorization.
Use create/append semantics, idempotency keys, least-privileged data access and an externally verifiable signature.
Coordinate with AUD-029-006 and AUD-029-009; do not repurpose mutable pipeline state as immutable audit storage.

**Tester:** Proposed `tests/devops/test_deployment_audit_contract.py` using the existing root schema and a fake
append adapter. Cases: each supported event, every required-field omission, malformed UTC timestamp, 2001-character
rationale, unknown action/outcome, legacy translation, optional metadata, missing topology/signature, duplicate
idempotency key, unauthorized actor, revoked group membership, and append outage. Assert validation precedes
all writes and failed authorization is logged without falsely recording a successful state change.

**Future validation only:** With local JSON Schema format support and injected signer/store, run
`pytest tests/devops/test_deployment_audit_contract.py -q`. Expected: all required omissions are denied,
documented legacy events remain readable, and no alternate unvalidated deployment write path survives.

**Done:** The agreed amendment and producer/consumer schemas match, every retained deployment event uses the
validated append path, and signature/retention assertions are supported separately from schema validation.

### P1: Drift Parsing Can Turn an Error into a Clean Report

- [ ] AUD-029-008 Distinguish drift-query failure from a verified clean inventory

**Obligations:** FR-019, FR-022, FR-023, FR-031; SC-011; US7-AS3, US7-AS4, US9-AS3;
T069, T070, T082, T084.

**Expected / actual / impact:** Weekly cadence and staging/production-only scope are explicitly selected by
[spec 031 R5](../031-simplify-cicd-pipeline/research.md#L73), superseding the nightly mechanism, not justifying
false negatives. [The parser](../../.github/workflows/drift-detection.yml#L109) substitutes `[]` on jq failure
and treats absent `.changes` as empty; [the RG check](../../.github/workflows/drift-detection.yml#L56) also
treats any failed lookup as unprovisioned. Malformed output or authorization/transport errors can therefore
report no drift/skipped. Filtering uses unanchored regex property names, and only top-level deltas are projected.
Issue creation reports properties but does not deduplicate/update existing findings or append an audit event.
[Current tests](../../tests/devops/test_drift_detection.py#L1) inspect YAML and labels, not parser failure behavior.

**Developer:** Preserve the explicitly chosen cadence until a new SLA decision. Separate not-found from
permission/network errors; require a valid expected What-If shape before comparison; reject parse failure or
partial inventory. Filter exact structural system paths and walk nested property deltas without hiding security
changes. Redact secret values in reports. Deduplicate by environment/resource/property and emit the agreed audit
event. Add read-only PR context for overlapping open drift and reconciliation findings after AUD-029-007;
do not auto-mutate infrastructure as a drift reporting side effect.

**Tester:** Extend [drift tests](../../tests/devops/test_drift_detection.py) with fixture-fed parsing and command
doubles: genuine empty changes, create/delete, nested auth/public-network change, harmless system change,
similarly named security property, truncated JSON, missing changes, 403, 404, timeout, duplicate findings,
secret-bearing delta, and PR path overlap/non-overlap. Assert only the valid clean fixture reports clean;
errors fail/report uncertainty, secrets are absent from issue bodies, repeated findings update one issue,
and overlapping retained blockers prevent the candidate progressing.

**Future validation only:** Run `pytest tests/devops/test_drift_detection.py -q` in the prepared offline fixture
harness, with GitHub/Azure calls mocked. Expected: parser failures never yield a clean result and issue/audit
side effects match each fixture. A later scheduled-run record is required to establish detection/closure latency.

**Done:** A clean report is backed by a complete successful comparison; all failures remain visible,
resource/property findings are traceable, and the agreed cadence/SLA is stated without a fictitious 24-hour claim.

### P1: Approval and Identity Claims Lack a Current Enforcement Record

- [ ] AUD-029-009 Record and enforce the surviving authorization and identity-deviation boundaries

**Obligations:** FR-003, FR-011, FR-011a, FR-012, FR-016, FR-033; SC-007, SC-008, SC-013, SC-018;
T000a, T005, T008, T008a, T008b, T022, T023, T024, T024a, T043, T044, T058, T067, T068, T071.

**Expected / actual / impact:** [ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L31)
authorizes a temporary credential-based pipeline, with a 90-day manual rotation process and
[review triggers](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L100). It does not prove
rotation, review, least privilege or group membership occurred. CD names an environment, not its effective
reviewer rules. [CODEOWNERS](../../.github/CODEOWNERS#L28) explicitly removes the 029 ownership rules and
retains a few incident paths; it does not cover all actual safety paths such as
[evacuation implementation](../../apps/agents/evacuation/pipeline.py), nor provide two-person authorization.
The [protection snapshot](../../.github/branch-protection.json#L2) is descriptive, main-only, and has no reviewer
configuration. Freeze, emergency approvals and reviewer reconciliation were retired; no live permission
snapshot or sign-off was obtained. Treating a declared handle/team or environment name as approval would be unsafe.

**Developer:** Have the authorized owner determine the current scope and review status of the time-bound
deviation and retired incident controls. Record an explicit residual-risk decision, owners, expiry/trigger,
rotation procedure and evidence references; do not infer approval from this report. Independently enforce
required reviews for surviving safety-critical/infra paths and actual deploy branches. Use trusted, authenticated
distinct reviewer identities bound to the exact change; do not assume listing multiple environment reviewers
requires all of them. If the old emergency lane is reauthorized, require two non-author approved group members,
audit membership changes, preserve mandatory gates and block unreconciled emergency changes after 24 hours.
Apply least-privileged environment-scoped identity without widening credentials as a workaround.

**Tester:** Proposed `tests/devops/test_delivery_authority.py` with offline GitHub/Entra/protection snapshots.
Cover author self-approval, duplicate accounts, missing/revoked group membership, stale SHA approvals, absent
CODEOWNER coverage, user/team modes, zero/one/two non-author approvals, six/seven-person legacy reviewer unions,
expired exception, wrong target subscription, freeze active, and overdue emergency evidence if that lane is retained.
Assert denial of every unauthorized path and preserve auditable rejected attempts. Real collaborator access,
credential rotation and environment protection require separate owner-provided receipts.

**Future validation only:** After the authorized policy decision and fixture implementation, run
`pytest tests/devops/test_delivery_authority.py -q` offline. Expected: only exact authorized candidates proceed.
No invitations, remote approval queries, group changes, credential inspection, or external approvals occurred here.

**Done:** Current authorization is enforceable and independently evidenced; retirement, conditional deviation,
and successful human approval are distinct records, with no unsupported zero-credential or two-person claim.

### P2: DORA Proxies Do Not Prove the Spec-029 Measures

- [ ] AUD-029-010 Compute attributable deployment metrics and preserve missing-data uncertainty

**Obligations:** FR-002, FR-020; SC-001, SC-002, SC-003, SC-004, SC-009, SC-011, SC-016;
T029, T030, T034, T040, T045, T072, T077, T078.

**Expected / actual / impact:** [The replacement publisher](../../scripts/dora_metrics_publish.py#L74) uses
successful GitHub runs and incident issues, not the requested audit events. It computes a mean commit-to-run
delta rather than median merge-to-100%-traffic, counts incidents rather than distinct failed deployments,
and reuses all incidents' close/open durations for every environment. Multiple issues after one deploy can
inflate CFR above 100%; rollbacks/hotfixes without an incident issue are omitted. Empty/API-failure data can
become zero metrics and publishing errors are nonfatal. [The workflow](../../.github/workflows/dora-metrics.yml#L7)
is manual despite the [daily publication documentation](../../docs/ci-cd/dora-metrics.md#L14).
The workbook is explicitly future work. [Two tests](../../tests/devops/test_dora_metrics_publish.py#L23)
test pagination shapes only; there are no inspected calculations or measured spec-029 results.

**Developer:** Explicitly distinguish any approved spec-032 proxy metric from spec-029 acceptance measures.
Use the actual deployed commit/environment and audit/candidate correlation, stable time semantics, distinct
deployment denominators, merge timestamps, restore events, freeze exclusions and incident-mode segmentation.
Report unknown/no samples instead of healthy zero on collection failure. Add appropriate gauge/distribution
instruments, p50/p95 gate budget trends and a versioned dashboard/query contract if those targets are retained.
Depend on AUD-029-001 and AUD-029-007 for trustworthy rollback and event data. Schedule publication only after
permission, retention, and rate-limit behavior are established; do not label mocked timings as a soak.

**Tester:** Extend [DORA tests](../../tests/devops/test_dora_metrics_publish.py) with a fake clock and API/audit
fixtures: one failed deploy with multiple incidents, a rollback without an issue, unrelated incidents, multiple
environments, old issues updated recently, freeze periods, no data, HTTP error, missing timestamps, more than
500 records, and publisher failure. Assert CFR is bounded and counts distinct attributable deploys, no cross-env
MTTR contamination, correct quantiles, explicit unknowns, and deterministic sample-window boundaries.

**Future validation only:** Run `pytest tests/devops/test_dora_metrics_publish.py -q` offline after adding the
calculation cases. Expected: hand-computed fixtures match exactly and unavailable data never advertises success.
Later SC validation requires dated real 7-day/30-day samples, queries and denominator definitions; none was collected.

**Done:** Metric definitions, source events, schedule and dashboard agree; claims are reproducible from
traceable samples and cannot be mistaken for the retired canary's measured success.

### P2: Historical Contracts and Checkmarks Cannot Serve as Completion Evidence

- [ ] AUD-029-011 Publish an explicit retirement and residual-obligation ledger with validated evidence

**Obligations:** Every original review/validation obligation; T000a, T009, T013, T017, T021, T024a, T026,
T028, T029, T035, T040, T046, T050, T051, T055, T056, T060, T064, T069, T072, T073, T075, T076,
T077, T078, T079a, T080, T081, T082, T083, T084, T085, T086, T087, T088; all SCs and checklist items.

**Expected / actual / impact:** The [task summary](tasks.md#L28) claims authored work and a historical
10-pass/11-skip sweep, but has no attached run record; all 94 source tasks remain unchecked. It refers to plain
T079 although the actual task is T079a, and calls T080 drift work although T080 is plaintext-secret detection.
The [checklist notes](checklists/requirements.md#L33) still describe 24 FRs, seven stories and 13 SCs; the actual
inventory is 34 FRs, nine stories and 18 SCs. The validation directory, style record and 029 test package are absent.
The local contracts also disagree: object versus array exceptions, two reviewer personas versus one fallback
handle, one extra collaborator versus two non-author approvals, per-secret access-policy claims, optional
versus required audit fields, 60-minute versus six-hour slow-burn window, known-good SQL missing the not-rolled-back
predicate, and updated evidence versus immutable objects. T023's mandatory environment reviewers conflicts with
US1's no-manual-approval path; T027's incident-commander-only freeze conflicts with FR-011's SRE alternative.
Task T085's API addition also conflicts with the plan's no-application-changes boundary.

The original timing design also needs an explicit disposition: 10 + 15 + 30 = 55 minutes before 100% traffic,
plus the mandatory five-minute staging load smoke already reaches 60 minutes before build/deploy/e2e/chaos
overhead. A strict sub-60-minute sequential graph cannot satisfy both obligations without an agreed scheduling
or measurement change. The 100% stage's later 60-minute stability window is correctly a different clock and
does not resolve this pre-100% budget conflict.

The [relocated runbook](../../docs/ci-cd/progressive-delivery.md#L14) claims CodeQL, Cosign deploy verification,
daily DORA and SLO-driven rollback that the current entrypoints do not implement. Its manual multi-day promotion
procedure is evidence of replacement, not evidence for sub-hour delivery. The
[cleanup recommendations](../031-simplify-cicd-pipeline/fr020-recommendations.md#L1) record defaults but leave
maintainer sign-off pending; no actual review completion can be inferred from those defaults.

**Developer:** Preserve historical source checkboxes and evidence. Have owners record a separate versioned
disposition for every retired mechanism and each still-binding safety obligation, referencing spec 031 R6 and
ADR-031 with precise scope rather than treating them as blanket completion. Correct active runbooks/entrypoint
references only under a separately authorized change. Reconcile retained schema/event/action vocabulary,
approval cardinality, environment tokens, retention/reconciliation semantics and the listed source conflicts.
Do not recreate absent tests solely to certify a retired design; map each to a current equivalent or an explicitly
approved retirement. Proposed new ledger: `docs/ci-cd/spec-029-disposition.md`. Link real results only when produced;
record missing evidence, failed measurements and outstanding human reviews as such.

**Tester:** In existing [tests/docs](../../tests/docs) or a proposed `tests/docs/test_spec029_disposition.py`,
add text/contract fixtures covering all 94 task IDs and exact states, FR-011a and all suffix tasks, 52 FR/SC rows,
40 acceptance scenarios, 15 edges, 16 clarifications, every checklist row, missing links, wrong line bounds,
unsupported SUPERSEDED claims and duplicate follow-ups. Assert no original checkbox is changed and no invented
artifact or checkmark can satisfy an execution/sign-off obligation. Link restored behavioral tests to the
authoritative CI gate under AUD-029-002; static source tests alone cannot prove cloud outcomes.

**Future validation only:** A prepared doc-test environment may run
`pytest tests/docs/test_spec029_disposition.py -q` after that proposed test exists. Expected: complete one-to-one
coverage and no unsupported evidence claims. A later approved validation campaign must separately address the
seven quickstart flows, all 18 SCs, 7-day soak, 30-day metrics, RU baseline, quarterly reviews and real approvals.
Neither historical checkmarks nor this review authorize those external actions.

**Done:** Every original obligation has an explicit, evidence-backed disposition; active instructions are
usable; all retained outcomes have appropriate source, execution, measurement or human evidence, with unresolved
items left open. The original tasks and this report's remediation checkboxes remain distinct.

## Evidence Inventory and Search Bounds

Negative claims below apply to this revision's inspected working files, not to all possible historical commits,
external services, or unpublished evidence. Read-only status for the spec folder and primary CI/CD/root/rollback
paths showed only this untracked report. No other review report was opened. No historical implementation was
reconstructed from another review, and no absent test is claimed to have run.

| Scope | What was inspected and what the bound establishes |
| --- | --- |
| S1: Local obligation inventory | Full recursive inventory and complete reads of the 13 inputs listed above. No validation directory, validation ZIP, SC-results, post-remediation analyze report, STYLE record, or separate local amendment/review/evidence file exists. Inline clarifications, R16/R17 amendments, inserted task suffixes and checklist notes are included. |
| S2: Workflow reachability | Complete active [CI](../../.github/workflows/ci.yml), [CD](../../.github/workflows/cd.yml), [drift](../../.github/workflows/drift-detection.yml), [security](../../.github/workflows/security-scan.yml), [CodeQL](../../.github/workflows/codeql.yml), [staging promotion](../../.github/workflows/staging-promotion.yml), and [DORA](../../.github/workflows/dora-metrics.yml) were read; workflow/action inventories and searches for controller, emitter, signing, state and policy calls checked relocation. Old spec029/reusable/freeze/hotfix/key/pack workflows are absent. Other prompt/corpus signing references concern their own artifacts, not CD images or bundles. |
| S3: Implementation and tests | Exact historical paths were checked for existence; the pipeline package, pipeline tests, bootstrap scripts, identity record and old action folders are absent. Searches in tools, scripts, tests and workflow sources for pipeline_tools, controller/verifier/emitter names, pipeline_state, deploy.emergency, freeze.activate, and original test-name stems found no equivalent delivery controller. Reviewed current DevOps YAML/string tests, DORA tests, gateway integration tests and Foundry contract tests as possible replacements. Absence of an old test is MISSING unless a specific decision retires that test; R6 explicitly left pipeline tests for later triage. |
| S4: Infrastructure and configuration | Active [root](../../infra/main.bicep), relevant complete controlling resource blocks, [alternate root](../../infra/bicep/main.bicep), [azd descriptor](../../azure.yaml), root and environment JSON params, three retained Bicep params, original retained evidence/audit/Defender/jump-host/posture modules, present Rego files and module callers were inspected. Neither root invokes the five retained 029 modules. Original pipeline-state, ACR-retention, cross-env/new-type policies, security-alert routing, matrix generator and SLO/sample/load-target files are absent in their named locations and no equivalent was found in the inspected roots/callers. |
| S5: Relocated behavior and records | Read spec-031 research and FR020 recommendations, ADR-031, constitution, current CODEOWNERS/protection descriptor, relocated progressive-delivery and DORA docs, root audit schema, current model registry/verifier/model module and gateway call boundary. Read the empty known-good JSON and its writer. Spec-029 execution, signing, access-denial, reviewer, deployment and metric receipts were not located in S1 or those cited records; remote state was not queried. |
| S6: Active hooks | [Seed shell hook](../../scripts/seed-database.sh#L44) and [PowerShell hook](../../scripts/seed-database.ps1#L57) invoke the [seed loader](../../scripts/seed_loader.py#L643), not staging/load/chaos or deployment evidence controls. The [Cosmos auth selector](../../scripts/seed_loader.py#L180) supports direct COSMOS_KEY or DefaultAzureCredential; this is not dev-only Key Vault issuance/rotation. Cosmos upsert failures raise, while Blob create errors are broadly reported as already-existing. Missing endpoints can select a dry run. No seed path proves successful backend onboarding or regulated-data absence. |

### Active Event and Outcome Graph

| Surface | Event / dependency / condition | Actual outcome and limit |
| --- | --- | --- |
| ci | Push on main/dev/staging/production; PRs targeting main. Quality is initial; Windows, golden-set, citation accessibility, web shards and publication gate depend on quality; web merge depends on shards, web gate on merge. | Runs source checks and local test/build commands; Python typing and citation accessibility tolerate failure. Most steps are inside one quality status. No measured 10-minute budget, complete original gate set, or applied protection state follows from this graph. |
| cd | Completed successful ci, source event push, source branch dev/staging/production; one dynamic-environment job with no-cancel per-environment concurrency. | Checks out upstream head SHA; credential login; azd environment creation; carve-out registry check; provision then deploy; API/web HTTP probes; record current revisions. Main never starts CD. No caller of signed build, stage polling, freeze, pack, or full posture verifier. |
| CD failures | Rollback only after health-check failure and non-dev; rollback is continue-on-error; critical issue only if rollback step outcome is failure. | Provision/deploy/hook failure before health does not invoke rollback. Dev never rolls back. Lookup-empty rollback can return zero before health (AUD-029-001). Status logic also cannot represent a later known-good-record failure as a complete evidence chain. |
| staging-promotion | Dispatch or daily schedule; static gate first. Smoke and runtime require dispatch; runtime needs static plus smoke; tag step needs all three. | Z6/Z7 SLI evaluation is not the five-signal 029 canary. Schedule skips live stages. The final tag is local only. No cd dependency consumes this result, despite its header claiming that dependency. |
| security-scan / CodeQL | Security push/PR runs independently; CodeQL dispatch only. | Gitleaks, PSRule and Trivy filesystem actions exist; CodeQL has no live analysis steps. Their presence does not make them CD or protected-merge prerequisites. |
| drift | Weekly Saturday cron or dispatch, staging/production matrix, environment credentials. | What-If -> JSON delta -> issue. Auth/parse failures may masquerade as missing/clean; no original full Resource Graph posture join, deploy-time cross-env check, append audit or PR-context link. |
| dora-metrics | Dispatch only; no CD dependency. | GitHub run/issue proxy metrics; optional telemetry publishing; not the requested audit-derived, continuously published quantiles or measured SC proof. |
| azure.yaml | Active infra root is infra/main.bicep; four services; postprovision seed hooks; web prepackage build. | Rebuild/deploy from source. No digest/SBOM/signature/provenance handoff, staging chaos gate, or uniform private/MI-only posture is inferred. |

### Supersession Rule

SUPERSEDED below means an explicit operational retirement/replacement, principally
[R1](../031-simplify-cicd-pipeline/research.md#L5),
[R5](../031-simplify-cicd-pipeline/research.md#L73),
[R6](../031-simplify-cicd-pipeline/research.md#L83),
[CODEOWNERS deletion note](../../.github/CODEOWNERS#L28), or
[ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L31).
It is not IMPLEMENTED and does not waive the unchanged constitution, prove formal amendment of spec 029,
or prove that a now-retired task previously passed. Retained modules and replacement controls are assessed
on their own actual behavior. A full restoration requires an explicit future scope decision.

## Original Task Coverage

All 94 task IDs and states are transcribed from [tasks.md](tasks.md). Every state is `[ ]`; there is no plain
T079 and no invented plain T000. The historical summary's ranges and claimed completion are not used as states.
Where a task contains both authoring and execution, its explanation separates those axes. Commands and tester
steps in the follow-ups are future-only; no original task has been completed by this review.

| Original ID | Original state | Status | Existing evidence and explanation | Follow-up |
| --- | --- | --- | --- | --- |
| T000a | [ ] | UNVERIFIED | [R17](research.md#L143) requires a second collaborator; S1/S3 contain no invitation/protection receipt. Bootstrap/identity files were retired by R6; collaborator access is unknown. | AUD-029-009, AUD-029-011 |
| T001 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires package/reusable directories; S3 confirms absence. Surviving policy directory is not the complete seven-directory scaffold. | AUD-029-011 |
| T002 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires the complete Python package, dependencies and five entrypoints; no package-install success is evidenced. | AUD-029-011 |
| T003 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes package version/export/README; current root metadata is not that package. | AUD-029-011 |
| T004 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes package lint/type settings; [root settings](../../pyproject.toml#L97) cover apps/packages, not the retired slice. | AUD-029-011 |
| T005 | [ ] | SUPERSEDED | [ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L31) removes OIDC/topology trust-root assertions; [CD](../../.github/workflows/cd.yml#L86) uses creds. Original mismatch audit/export not delivered by this path. | AUD-029-009 |
| T006 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) identifies relocated install-opa action for deletion; S2/S3 confirm no original installer caller. | AUD-029-002, AUD-029-011 |
| T007 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes setup-cosign-syft. Other signing references are prompt/corpus artifacts, not deployment images/bundles. | AUD-029-011 |
| T008 | [ ] | SUPERSEDED | [CODEOWNERS](../../.github/CODEOWNERS#L28) explicitly deletes posture/identity ownership rules with spec 031; no two-person approval can be inferred. | AUD-029-009 |
| T008a | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) explicitly deletes IDENTITY.md. S3 confirms the canonical seven-key trust-root is absent. | AUD-029-009, AUD-029-011 |
| T008b | [ ] | SUPERSEDED | [ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L91) accepts loss of topology validation; S3/S4 find no identity-consistency rule. | AUD-029-003, AUD-029-009 |
| T009 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes package contribution/dry-run docs; [old quickstart](quickstart.md#L1) is not an executable replacement. | AUD-029-011 |
| T010 | [ ] | PARTIAL | [Recreated matrix](../../infra/policy/posture-matrix.yaml#L1) is a spec-033 retention stub, not three environments/seven families or the original schema. | AUD-029-003, AUD-029-011 |
| T011 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires old registries; [new registry](../../infra/parameters/foundry-carveout.yaml#L21) has a different scope and no matching gpt-5.4 row. | AUD-029-004, AUD-029-011 |
| T012 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) deletes posture loader/effective-exception package. S3 finds no replacement PostureDecision path. | AUD-029-003, AUD-029-011 |
| T013 | [ ] | MISSING | S3: no pipeline unit tests or equivalent matrix load/schema/expiry suite. [Original contract](contracts/posture-matrix.schema.yaml#L8) remains, not the required ten tests or coverage result. | AUD-029-003, AUD-029-011 |
| T014 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires original posture Rego and driver. [Current matrix](../../infra/policy/posture-matrix.yaml#L1) is not consumed as a full gate. | AUD-029-003 |
| T015 | [ ] | SUPERSEDED | [ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L91) accepts topology-check removal; S4 finds no A/B cross-env rule or deploy Resource Graph assertion. | AUD-029-003, AUD-029-009 |
| T016 | [ ] | PARTIAL | [Relocated Rego](../../infra/policy/rego/foundry_carveout.rego#L1) checks registry rows, not all rendered resources; [CD check](../../scripts/verify-carveout.ps1#L118) leaves What-If optional. Original registry retired. | AUD-029-004, AUD-029-005 |
| T017 | [ ] | MISSING | S3: four original contract suites and 3-allow/3-deny A/B fixtures absent. [New Foundry test](../../tests/contract/test_foundry_carveout.py#L75) can run a Python substitute, not the original four policies. | AUD-029-003, AUD-029-004, AUD-029-011 |
| T018 | [ ] | PARTIAL | [Audit module](../../infra/bicep/modules/audit-store.bicep#L20) and [evidence module](../../infra/bicep/modules/evidence-store.bicep#L15) survive; neither provides pipeline_state with /pk, CMK and legal hold or active root wiring. | AUD-029-003, AUD-029-006 |
| T019 | [ ] | MISSING | S4: no pipeline-state module/root call. [Active descriptor](../../azure.yaml#L8) selects another root; retained params do not wire per-env legal hold. | AUD-029-003, AUD-029-006 |
| T019a | [ ] | PARTIAL | [Root topology parameter](../../infra/main.bicep#L123) defaults B and exports a value, but [retained policy module](../../infra/bicep/modules/posture-policy-set.bicep#L7) always has subscription scope and no caller. | AUD-029-003 |
| T020 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) deletes audit emitter/signing CLI; [root schema](../../contracts/audit-event.schema.json#L1) alone does not validate/persist events. | AUD-029-007 |
| T020a | [ ] | CONFLICT | [Root schema required list](../../contracts/audit-event.schema.json#L8) omits mandatory amendment fields; action/outcome vocabulary differs and no canonical writer is connected. | AUD-029-007 |
| T021 | [ ] | MISSING | S3: no original schema test or equivalent eight-case deployment schema validation suite. [Root schema](../../contracts/audit-event.schema.json#L8) shows omissions, not passing validation. | AUD-029-007, AUD-029-011 |
| T022 | [ ] | UNVERIFIED | No Entra federation/exchange/role receipts in S1/S5; [ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L31) replaces the intended path. No historical provision is inferred. | AUD-029-009 |
| T023 | [ ] | UNVERIFIED | [CD environment binding](../../.github/workflows/cd.yml#L41) exists; actual reviewer lists, per-env variables, topology and approval prompts are remote and unverified. Source reviewers also conflict with no-manual US1. | AUD-029-009, AUD-029-011 |
| T024 | [ ] | UNVERIFIED | S1/S5 provide no group/membership/reviewer-sync evidence; [R6](../031-simplify-cicd-pipeline/research.md#L83) retires reconciler/bootstrap ownership. A descriptor is not group creation. | AUD-029-009 |
| T024a | [ ] | MISSING | S3: reviewer-sync integration file, five mocked cases and branch-coverage receipt absent; [task amendment](tasks.md#L205) remains unsupported. | AUD-029-009, AUD-029-011 |
| T025 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) deletes full-sweep posture verifier; [drift](../../.github/workflows/drift-detection.yml#L42) is a What-If comparison, not its replacement. | AUD-029-003, AUD-029-008 |
| T026 | [ ] | MISSING | S3: no recorded Resource Graph one-pass/one-fail-per-family verifier fixtures or 85% result; [parameter tests](../../tests/devops/test_parameter_files.py#L61) only inspect static values. | AUD-029-003, AUD-029-011 |
| T027 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes freeze controller/state/workflow. Task commander-only authority also differs from FR-011. | AUD-029-009, AUD-029-011 |
| T028 | [ ] | MISSING | S3: no freeze RBAC/concurrency/audit tests or twelve-case execution record; [canary contract](contracts/canary-promotion.api.md#L46) is a design, not assertions. | AUD-029-009, AUD-029-011 |
| T029 | [ ] | UNVERIFIED | S1/S3: no synthetic merge-to-production timing result or original test. [DORA helper](../../scripts/dora_metrics_publish.py#L74) measures a different proxy. | AUD-029-010, AUD-029-011 |
| T030 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes lead-time state helper; [new DORA definitions](../../docs/ci-cd/dora-metrics.md#L5) are not merge-to-100% state. | AUD-029-010 |
| T031 | [ ] | SUPERSEDED | [R1/R6](../031-simplify-cicd-pipeline/research.md#L5) replace main/canary graph; [CD](../../.github/workflows/cd.yml#L19) has one branch-based deploy with no staging-gate/controller/posture chain. | AUD-029-001, AUD-029-002, AUD-029-011 |
| T032 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires canary flow; [current API configuration](../../infra/main.bicep#L1006) has no explicit multiple-revision weighted-canary configuration. | AUD-029-001, AUD-029-011 |
| T033 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires staged flow; [web resource](../../infra/main.bicep#L1271) is a Basic-plan site with no declared slots or four-stage routing. | AUD-029-011 |
| T034 | [ ] | PARTIAL | [DORA doc](../../docs/ci-cd/dora-metrics.md#L26) explicitly leaves workbook future work; [publisher](../../scripts/dora_metrics_publish.py#L74) exists but not audit-derived p50/p90/CFR/restore measures. | AUD-029-010 |
| T035 | [ ] | MISSING | S3: no cross-stage artifact immutability test. [CD](../../.github/workflows/cd.yml#L227) provisions/deploys without a digest/signature handoff. | AUD-029-002, AUD-029-011 |
| T036 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes signed build flow; [azure.yaml](../../azure.yaml#L29) builds service source and web, not an OCI infra bundle with four attestations. | AUD-029-002, AUD-029-011 |
| T037 | [ ] | SUPERSEDED | [R1/R6](../031-simplify-cicd-pipeline/research.md#L5) replace downstream stages; [CD deploy](../../.github/workflows/cd.yml#L227) consumes no build digests output. | AUD-029-011 |
| T038 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes artefact verifier CLI; no equivalent image/infra attestation gate in S2/S3. | AUD-029-002, AUD-029-011 |
| T039 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires signed-stage steps; [CD](../../.github/workflows/cd.yml#L227) does not emit tamper-abort events or verify signatures before deploy. | AUD-029-002, AUD-029-007 |
| T040 | [ ] | UNVERIFIED | S1/S3: no five-PR trial or gate timing samples; [CI graph](../../.github/workflows/ci.yml#L14) is not measurement evidence. | AUD-029-002, AUD-029-010 |
| T041 | [ ] | PARTIAL | [CI](../../.github/workflows/ci.yml#L14) and [security](../../.github/workflows/security-scan.yml#L18) provide subsets; fourteen mandatory categories, every image scan, strict typing and coupled approvals are not all enforced. | AUD-029-002 |
| T042 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires OPA PR driver. [Remaining What-If](../../.github/workflows/drift-detection.yml#L42) is weekly, not a required PR diff/review gate. Constitutional review remains unresolved. | AUD-029-002, AUD-029-003 |
| T043 | [ ] | PARTIAL | [Incident patterns](../../.github/CODEOWNERS#L36) exist; S2 finds no extra safety-critical-path job and heavier matching suite/protection proof. | AUD-029-002, AUD-029-009 |
| T044 | [ ] | UNVERIFIED | [Protection descriptor](../../.github/branch-protection.json#L2) explicitly is not applied by GitHub; [CODEOWNERS](../../.github/CODEOWNERS#L28) deletes broad 029 rules. Remote two-review/squash settings not checked. | AUD-029-009 |
| T045 | [ ] | MISSING | S2/S3: no gate-budget-monitor, 30-day p50/p95 comment or breach labels. [DORA calculations](../../scripts/dora_metrics_publish.py#L109) do not supply gate quantiles. | AUD-029-002, AUD-029-010 |
| T046 | [ ] | MISSING | S3: nine-case burn-rate/posture/freeze/self-approval suite absent. [Rollback tests](../../tests/devops/test_rollback_script.py#L123) assert text, not selection, timing or issue side effects. | AUD-029-001, AUD-029-011 |
| T047 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires canary decision tool. [Retained rollback](../../scripts/rollback.sh#L188) is not a six-branch burn-rate/sample controller. | AUD-029-001, AUD-029-011 |
| T048 | [ ] | MISSING | S4: five-signal/min-samples configuration and slo-burn bridge absent. [Staging runtime](../../.github/workflows/staging-promotion.yml#L64) considers Z6/Z7, not the named 029 set or CD stages. | AUD-029-002, AUD-029-011 |
| T049 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires canary flow; no slo-burn workflow in S2. [Current health rollback](../../.github/workflows/cd.yml#L355) remains and has AUD-029-001 defects. | AUD-029-001 |
| T050 | [ ] | MISSING | S3: no original pack-contract test. [Manifest schema](contracts/evidence-pack.schema.json#L33) permits a single item and does not require kind or all mandated content categories. | AUD-029-006, AUD-029-011 |
| T051 | [ ] | UNVERIFIED | S1/S3: no storage overwrite/delete-denial execution result. [Standalone retention](../../infra/bicep/modules/evidence-store.bicep#L50) neither establishes deployment nor a legal hold/locked policy. | AUD-029-006 |
| T052 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes pack producer. [Current publication gate](../../.github/workflows/ci.yml#L406) targets other artifacts and is not production finalization. | AUD-029-006, AUD-029-007 |
| T053 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires pack workflow; [CD terminal steps](../../.github/workflows/cd.yml#L395) summarize status, not signed complete evidence. | AUD-029-006 |
| T054 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) deletes fetch CLI; [quickstart flow 6](quickstart.md#L111) downloads/unzips without the required manifest/item verification contract. | AUD-029-006, AUD-029-011 |
| T055 | [ ] | UNVERIFIED | S1/S3: no freeze/queued-merge/resume exercise result; [R6](../031-simplify-cicd-pipeline/research.md#L83) explicitly removes freeze flow. | AUD-029-009, AUD-029-011 |
| T056 | [ ] | UNVERIFIED | No dual-human hotfix/evidence-within-24h result in S1/S3/S5. [New hotfix runbook](../../docs/ci-cd/progressive-delivery.md#L56) is a cherry-pick procedure, not the original assertion. | AUD-029-009, AUD-029-011 |
| T057 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires freeze checks; [CD](../../.github/workflows/cd.yml#L34) does not inspect freeze state or emergency labels. | AUD-029-009 |
| T058 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) expressly deletes emergency-hotfix workflow. Neither environment naming nor new runbook proves two non-author group members approved. | AUD-029-009 |
| T059 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires emergency/pack pipeline; no backfill workflow or deferred-gate execution loop in S2/S3. | AUD-029-006, AUD-029-011 |
| T060 | [ ] | UNVERIFIED | No three-environment What-If/verification result in S1. [Existing parameter tests](../../tests/devops/test_parameter_files.py#L61) check names/regions, not public-access/local-auth changes or deployed posture. | AUD-029-003, AUD-029-011 |
| T061 | [ ] | PARTIAL | [Dev](../../infra/parameters/dev.bicepparam#L1), [staging](../../infra/parameters/staging.bicepparam#L1), [production](../../infra/parameters/production.bicepparam#L1) exist but set no key lifetime/local-auth/public-access switches and are not the azd input path. | AUD-029-003 |
| T062 | [ ] | PARTIAL | [Optional tags](../../infra/main.bicep#L130) and [retained params](../../infra/parameters/dev.bicepparam#L9) exist; active defaults do not add never-prod-bind/regulated tags or cross-env deny assignment. | AUD-029-003, AUD-029-011 |
| T063 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) deletes dev-key issuance. [Seed key auth](../../scripts/seed_loader.py#L180) is not scoped KV issuance/rotation or group verification. | AUD-029-009, AUD-029-011 |
| T064 | [ ] | MISSING | S3: no four-case What-If posture-enforcement suite; [remaining Rego](../../infra/policy/rego/foundry_carveout.rego#L1) does not cover shared key/public/secret/cross-env cases. | AUD-029-003, AUD-029-011 |
| T065 | [ ] | PARTIAL | [Retained initiative](../../infra/bicep/modules/posture-policy-set.bicep#L21) is hard-coded and uncalled, not a deterministic matrix generator or per-env assignment. | AUD-029-003 |
| T066 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) names relocated posture-exception sweep for deletion; no active exception remover in S2/S3. | AUD-029-009, AUD-029-011 |
| T067 | [ ] | SUPERSEDED | [CODEOWNERS retirement note](../../.github/CODEOWNERS#L28) and [R6](../031-simplify-cicd-pipeline/research.md#L83) remove posture-file workflow/driver; no dual-role/current-date exception PR gate remains. | AUD-029-009, AUD-029-011 |
| T068 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes secret-audit helper; [ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L31) changes cloud identity model. No credential inventory audit was executed. | AUD-029-009 |
| T069 | [ ] | MISSING | S3: no fake-delta issue/audit side-effect test. [Current drift tests](../../tests/devops/test_drift_detection.py#L1) check YAML label text only. | AUD-029-008, AUD-029-011 |
| T070 | [ ] | PARTIAL | [Active drift](../../.github/workflows/drift-detection.yml#L42) compares What-If and creates issues, but parser can mask errors; no original Resource Graph posture/snapshot/audit path. Cadence/auth explicitly replaced. | AUD-029-008 |
| T071 | [ ] | SUPERSEDED | [ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L31) mandates the opposite of the old OIDC-only sweep; current creds usage is not an accidental missing rename. | AUD-029-009 |
| T072 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes documented package; [relocated instructions](../../.github/agents/copilot-instructions.md#L9) describe current structure, not a live 029 tooling/key workflow. | AUD-029-011 |
| T073 | [ ] | PARTIAL | [Seven old flows](quickstart.md#L1) and [new runbook](../../docs/ci-cd/progressive-delivery.md#L1) exist; original named operations runbook absent in S5, and new gate claims conflict with source. | AUD-029-011 |
| T074 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires package; [active CI](../../.github/workflows/ci.yml#L135) does not execute pipeline/DevOps coverage. Current regression-gate gap is separate. | AUD-029-002, AUD-029-011 |
| T075 | [ ] | UNVERIFIED | S1 lacks prerequisite/analyze output. [Task/plan conflicts](tasks.md#L195) remain; no checker execution is inferred from authoring. | AUD-029-011 |
| T076 | [ ] | UNVERIFIED | S1 has no validation ZIP or seven-flow run; [quickstart](quickstart.md#L1) is procedural documentation, not execution or compliance sign-off. | AUD-029-011 |
| T077 | [ ] | UNVERIFIED | S1 has no SC-results or seven-day soak. [DORA proxy](../../scripts/dora_metrics_publish.py#L74) is not a dated measurement dataset. | AUD-029-010, AUD-029-011 |
| T078 | [ ] | UNVERIFIED | No RU baseline/tuning record in S1/S5; [audit container](../../infra/bicep/modules/audit-store.bicep#L20) is not requested pipeline-state partition or p95 RU measurement. | AUD-029-006, AUD-029-010, AUD-029-011 |
| T079a | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires canary/staging flow; [new staging gate](../../.github/workflows/staging-promotion.yml#L64) lacks a CD dependency and full e2e/load/two-fault suite. | AUD-029-002, AUD-029-011 |
| T080 | [ ] | PARTIAL | [Gitleaks](../../.github/workflows/security-scan.yml#L19) exists separately; no inspected detect-secrets plus parameter regex/rule driver or all-failure file/line PR reporting in S2/S3/S4. | AUD-029-002, AUD-029-003 |
| T081 | [ ] | MISSING | S4: no ACR retention/locking guard or below-three alert; [ACR](../../infra/main.bicep#L479) has only admin credentials in properties. [Known-good record](../034-webapp-capstone-coverage/known-good.json#L4) is empty. | AUD-029-001, AUD-029-006 |
| T082 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes verifier/controller owner; [CD rollback condition](../../.github/workflows/cd.yml#L355) is health-only, not posture dispatch plus cancel. | AUD-029-001, AUD-029-003 |
| T083 | [ ] | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires original policy/PR driver; S4 finds no unknown-type deny. [Matrix stub](../../infra/policy/posture-matrix.yaml#L1) cannot serve as type inventory. | AUD-029-003 |
| T084 | [ ] | MISSING | S2/S3: no candidate PR-context audit query or path-overlap gate. [Drift issues](../../.github/workflows/drift-detection.yml#L223) are created independently and not consumed by CI. | AUD-029-008 |
| T085 | [ ] | PARTIAL | [Defender pricing module](../../infra/bicep/modules/defender-baseline.bicep#L9) survives without caller, Entra-risk ingestion, alert export, audit/evidence attachment or declared API route wiring in S4. | AUD-029-003, AUD-029-007, AUD-029-011 |
| T086 | [ ] | MISSING | S2/S3: no original failure-report composite/schema or universal gate wrapper. [CD failure issue](../../.github/workflows/cd.yml#L367) covers only failed rollback, not every failed gate/evidence outcome. | AUD-029-002, AUD-029-007 |
| T087 | [ ] | CONFLICT | [Task amendment](tasks.md#L680) requests STYLE, labels, literal-citation and naming repairs; S1/S4 lack those artifacts. [Stale checklist counts](checklists/requirements.md#L33) and prod/production/schema conflicts remain. | AUD-029-011 |
| T088 | [ ] | UNVERIFIED | S1 lacks post-remediation analyze/coverage output; S3 lacks coverage_check and reviewer/schema suites. [Claimed sweep](tasks.md#L28) is not a report of all original gates passing. | AUD-029-002, AUD-029-011 |

## Requirement and Success-Criterion Coverage

Source states are `none`: these obligations have no checkboxes. There are 34 FRs (including FR-011a),
18 SCs and no separately numbered NFRs. Nonfunctional constraints, clarifications and edge cases are accounted
for separately below. IMPLEMENTED means fully supported authored behavior, not runtime success; PARTIAL means
a specific part exists; MISSING is bounded absence; CONFLICT is a documented disagreement; UNVERIFIED is an
unproved execution/outcome/sign-off; SUPERSEDED requires the explicit retirement evidence stated above.

| ID | Source state | Status | Obligation | Existing evidence and limit | Follow-up |
| --- | --- | --- | --- | --- | --- |
| FR-001 | none | PARTIAL | [Complete independent PR gates](spec.md#L217) | [CI](../../.github/workflows/ci.yml#L14) runs a subset; [security](../../.github/workflows/security-scan.yml#L18) is separate; [CodeQL](../../.github/workflows/codeql.yml#L9) is disabled analysis. No full candidate-bound set. | AUD-029-002 |
| FR-002 | none | UNVERIFIED | [Median gates under ten minutes](spec.md#L218) | [CI graph](../../.github/workflows/ci.yml#L175) has sequential dependencies, caching and shards, but no measured distribution or budget monitor. | AUD-029-010 |
| FR-003 | none | PARTIAL | [Safety-critical CODEOWNERS reviews](spec.md#L219) | [Current patterns](../../.github/CODEOWNERS#L36) cover only selected incident paths; [protection descriptor](../../.github/branch-protection.json#L2) is not applied proof. | AUD-029-002, AUD-029-009 |
| FR-004 | none | SUPERSEDED | [Build once, SBOM, signing, SLSA-3](spec.md#L220) | [R6 retirement](../031-simplify-cicd-pipeline/research.md#L83); [azd service definitions](../../azure.yaml#L29) rebuild source without the old attestations or infra bundle. | AUD-029-002, AUD-029-011 |
| FR-005 | none | SUPERSEDED | [Same verified digest at every deploy](spec.md#L221) | [R6](../031-simplify-cicd-pipeline/research.md#L83) deletes verifier; [CD](../../.github/workflows/cd.yml#L227) has no build digest output to consume. | AUD-029-002, AUD-029-011 |
| FR-006 | none | SUPERSEDED | [Automatic staging e2e/load/two-fault chaos](spec.md#L222) | [Replacement](../031-simplify-cicd-pipeline/research.md#L5) is branch-based; [staging workflow](../../.github/workflows/staging-promotion.yml#L64) is separate and not an equivalent required gate set. | AUD-029-002, AUD-029-011 |
| FR-007 | none | SUPERSEDED | [5/25/50/100 stages, five signals, sample floors](spec.md#L223) | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires canary; [CD health probes](../../.github/workflows/cd.yml#L233) are not tiered observation windows. | AUD-029-001, AUD-029-011 |
| FR-008 | none | PARTIAL | [Fast-burn rollback to reverified known-good within five minutes](spec.md#L224) | [Health-failure invocation](../../.github/workflows/cd.yml#L355) remains; [selection/bootstrap](../../scripts/rollback.sh#L153) can skip restoration and is not verified known-good. Timing is unverified. | AUD-029-001 |
| FR-009 | none | SUPERSEDED | [Slow-burn hold plus tracked issue](spec.md#L225) | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires controller; no slow-burn decision/issue branch in active [CD](../../.github/workflows/cd.yml#L34). | AUD-029-011 |
| FR-010 | none | SUPERSEDED | [Equivalent web slot canary](spec.md#L226) | [R6](../031-simplify-cicd-pipeline/research.md#L83); [active web site](../../infra/main.bicep#L1271) has no declared slots/staged routing. | AUD-029-011 |
| FR-011 | none | SUPERSEDED | [Authorized freeze and queued normal changes](spec.md#L227) | [R6](../031-simplify-cicd-pipeline/research.md#L83) explicitly removes freeze workflow/state. Environment concurrency is not a freeze. | AUD-029-009, AUD-029-011 |
| FR-011a | none | SUPERSEDED | [Two distinct non-author group members; membership audit](spec.md#L228) | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes emergency/reconciler tooling; [environment reference](../../.github/workflows/cd.yml#L41) proves no actual reviewer membership. | AUD-029-009 |
| FR-012 | none | SUPERSEDED | [Mandatory emergency gates and 24-hour reconciliation/block](spec.md#L229) | [R6](../031-simplify-cicd-pipeline/research.md#L83); [replacement hotfix procedure](../../docs/ci-cd/progressive-delivery.md#L56) is immediate branch cherry-pick, not a two-person reconciled lane. | AUD-029-006, AUD-029-009 |
| FR-013 | none | SUPERSEDED | [Complete signed production evidence within five minutes](spec.md#L230) | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes pack flow. [CI publication gate](../../.github/workflows/ci.yml#L406) concerns other artifacts; no CD success/failure finalizer. | AUD-029-006 |
| FR-014 | none | PARTIAL | [AU evidence/audit, seven years and legal hold](spec.md#L231) | [Retained evidence module](../../infra/bicep/modules/evidence-store.bicep#L50) declares time retention but no hold/lock; [audit module](../../infra/bicep/modules/audit-store.bicep#L20) has no TTL, not append-only enforcement. Neither is root-wired. | AUD-029-006 |
| FR-015 | none | PARTIAL | [All deployment events in shared append-only schema](spec.md#L232) | [Root schema](../../contracts/audit-event.schema.json#L8) exists with incomplete required fields/event vocabulary; no deployment emitter. [Known-good writer](../../scripts/web-coverage/known-good.py#L138) is a different local audit path. | AUD-029-007 |
| FR-016 | none | SUPERSEDED | [OIDC-only and no long-lived cloud credentials](spec.md#L233) | [ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L31) explicitly authorizes a temporary opposing identity model; rotation/review execution remains unverified. | AUD-029-009 |
| FR-017 | none | PARTIAL | [KV-only application secrets and fail-closed deploy lint](spec.md#L234) | [Gitleaks](../../.github/workflows/security-scan.yml#L19) covers source; [registry passwords](../../infra/main.bicep#L1015) are evaluated directly into deployment secrets, and no KV-only deploy validator is connected. | AUD-029-002, AUD-029-003 |
| FR-018 | none | PARTIAL | [AU enforcement, named Foundry exception and minimisation](spec.md#L235) | [Root AU allow-list](../../infra/main.bicep#L78), [registry verifier](../../scripts/verify-carveout.ps1#L118), and [gateway](../../apps/agents/common/foundry_chat_client.py#L363) exist, but candidate parity, reviewer/date validation and privacy fail-closed paths are incomplete. | AUD-029-004, AUD-029-005 |
| FR-019 | none | PARTIAL | [Nightly desired/live drift, issue and audit](spec.md#L236) | [R5](../031-simplify-cicd-pipeline/research.md#L73) expressly changes cadence to weekly; [current parser](../../.github/workflows/drift-detection.yml#L109) can mask errors and does not append audit. | AUD-029-008 |
| FR-020 | none | PARTIAL | [Rolling audit-derived lead time/CFR/MTTR](spec.md#L237) | [New publisher](../../scripts/dora_metrics_publish.py#L74) derives different GitHub proxies; [manual workflow](../../.github/workflows/dora-metrics.yml#L7), no delivered workbook. | AUD-029-010 |
| FR-021 | none | MISSING | [Retain three previous known-good digests](spec.md#L238) | S2/S3/S4: [ACR config](../../infra/main.bicep#L479) has no known-good retention/locking controller; [manifest](../034-webapp-capstone-coverage/known-good.json#L4) is empty. | AUD-029-001, AUD-029-006 |
| FR-022 | none | MISSING | [PR context for overlapping drift/reconciliation](spec.md#L239) | S2/S3: [drift issue creation](../../.github/workflows/drift-detection.yml#L223) has no CI consumer or file-overlap reconciliation gate. | AUD-029-008 |
| FR-023 | none | PARTIAL | [Actionable failures across every gate/deploy/pack](spec.md#L240) | [CD critical issue](../../.github/workflows/cd.yml#L367) links a failed rollback; no universal report/schema/audit wrapper, and some failures are masked. | AUD-029-001, AUD-029-002, AUD-029-008 |
| FR-024 | none | SUPERSEDED | [Never advance on missing telemetry](spec.md#L241) | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires advancement. [Detached SLI gate](../../.github/workflows/staging-promotion.yml#L64) cannot protect current CD. | AUD-029-002, AUD-029-011 |
| FR-025 | none | PARTIAL | [Exactly three environments and canonical full posture matrix](spec.md#L242) | [CD branches](../../.github/workflows/cd.yml#L23) have the three names; [retention stub](../../infra/policy/posture-matrix.yaml#L1) is not the required resource/environment rule matrix. | AUD-029-003 |
| FR-026 | none | PARTIAL | [Dev names/tags, auth/logs, short keys and Defender/EIP](spec.md#L243) | [Dev params](../../infra/parameters/dev.bicepparam#L9) add tags off the active path; [Storage](../../infra/main.bicep#L493) disables anonymous blobs, but no full access-log/Entra-risk forwarding or scoped key lifecycle is shown. | AUD-029-003, AUD-029-009 |
| FR-027 | none | CONFLICT | [Private-only, MI-only staging/production](spec.md#L244) | [Active Storage/Cosmos/ACR](../../infra/main.bicep#L479) permit public/admin/shared-key paths. Retirement of a policy driver is not evidence that this posture is delivered. | AUD-029-003 |
| FR-028 | none | SUPERSEDED | [Non-skippable posture PR/emergency gate](spec.md#L245) | [R6](../031-simplify-cicd-pipeline/research.md#L83) explicitly retires the gate/lane; [PSRule](../../.github/workflows/security-scan.yml#L35) is not the original matrix evaluator or CD prerequisite. | AUD-029-002, AUD-029-003 |
| FR-029 | none | SUPERSEDED | [Static plus deploy-time cross-environment checks](spec.md#L246) | [ADR-031 accepted loss](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L91); [exported topology](../../infra/main.bicep#L1430) is not an assertion or Resource Graph traversal check. | AUD-029-003, AUD-029-009 |
| FR-030 | none | SUPERSEDED | [Exclusive, scoped 24-hour developer key lifecycle](spec.md#L247) | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes dev-key workflow. [Direct key fallback](../../scripts/seed_loader.py#L180) does not validate dev scope, TTL, KV isolation or prior-key revocation. | AUD-029-009, AUD-029-011 |
| FR-031 | none | SUPERSEDED | [Full post-deploy posture sweep and regulated rollback](spec.md#L248) | [R6](../031-simplify-cicd-pipeline/research.md#L83) deletes verifier; [CD health-only rollback](../../.github/workflows/cd.yml#L355) cannot establish actual posture or include its report in a pack. | AUD-029-001, AUD-029-003 |
| FR-032 | none | SUPERSEDED | [Unknown resource type denies until explicit rule approved](spec.md#L249) | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires original policy bundle; [matrix stub](../../infra/policy/posture-matrix.yaml#L1) has no environment/type allow inventory. | AUD-029-003 |
| FR-033 | none | SUPERSEDED | [Dual-approved named 90-day exceptions, sweep and quarterly audit](spec.md#L250) | [R6](../031-simplify-cicd-pipeline/research.md#L83) deletes registry/sweep; [remaining contract](contracts/posture-exceptions.schema.yaml#L35) is not an active approval/expiry/audit mechanism. | AUD-029-009, AUD-029-011 |
| SC-001 | none | UNVERIFIED | [Median merge-to-100% under 60 minutes](spec.md#L273) | No timing samples in S1/S5; [manual multi-day promotion](../../docs/ci-cd/progressive-delivery.md#L47) replaces the target mechanism. | AUD-029-010, AUD-029-011 |
| SC-002 | none | UNVERIFIED | [Gate p50 under 10m and p95 under 15m](spec.md#L274) | No gate-duration distribution or representative PR trial; [CI structure](../../.github/workflows/ci.yml#L14) cannot prove elapsed percentiles. | AUD-029-002, AUD-029-010 |
| SC-003 | none | UNVERIFIED | [30-day failure rate below 15%](spec.md#L275) | No attributable 30-day sample; [publisher numerator](../../scripts/dora_metrics_publish.py#L114) counts issues, not distinct failed deployments. | AUD-029-010 |
| SC-004 | none | UNVERIFIED | [Restore under 30m normal / 10m incident](spec.md#L276) | No measured regression drill; [rollback](../../scripts/rollback.sh#L376) can return success without restoration and DORA does not segment incident mode. | AUD-029-001, AUD-029-010 |
| SC-005 | none | UNVERIFIED | [Every production pack complete/retrievable within five minutes](spec.md#L277) | No pack latency/coverage denominator in S1/S5; [retained store](../../infra/bicep/modules/evidence-store.bicep#L50) is not a production promotion result. | AUD-029-006, AUD-029-011 |
| SC-006 | none | UNVERIFIED | [All actual resources AU except approved model hosts](spec.md#L278) | [Root guard](../../infra/main.bicep#L78) supports source intent; live inventory, effective runtime policy, registry parity and denial evidence unavailable. | AUD-029-004, AUD-029-005 |
| SC-007 | none | UNVERIFIED | [Quarterly proof of zero long-lived credentials](spec.md#L279) | No quarterly audit/rotation receipt. [ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L31) knowingly changes the zero-secret design, so this criterion cannot be claimed passed. | AUD-029-009 |
| SC-008 | none | UNVERIFIED | [All safety-critical merges have two persona approvals](spec.md#L280) | [CODEOWNERS](../../.github/CODEOWNERS#L36) is not historical review evidence; actual protection/membership and merge approval records not obtained. | AUD-029-009 |
| SC-009 | none | UNVERIFIED | [Pipeline toil below 50% of SRE capacity](spec.md#L281) | No time/capacity dataset or dashboard. Its T072 pointer names an instruction update, not an observability dashboard. [DORA docs](../../docs/ci-cd/dora-metrics.md#L26) defer even that workbook. | AUD-029-010, AUD-029-011 |
| SC-010 | none | UNVERIFIED | [Every rollback restores health without rebuild](spec.md#L282) | No retention audit or successful drill; [bootstrap skip](../../scripts/rollback.sh#L376) and [empty known-good](../034-webapp-capstone-coverage/known-good.json#L4) prevent source-based assurance. | AUD-029-001, AUD-029-006 |
| SC-011 | none | UNVERIFIED | [Drift detected within 24h, closed within seven days](spec.md#L283) | No detection/closure samples. [Weekly cron](../../.github/workflows/drift-detection.yml#L12) expressly replaces the daily cadence and cannot guarantee the old latency. | AUD-029-008, AUD-029-010 |
| SC-012 | none | UNVERIFIED | [Auditor reconstructs production trail within 15m](spec.md#L284) | No retrieval exercise; [quickstart flow](quickstart.md#L111) is documentation with no current matching emitter/pack writer. | AUD-029-006, AUD-029-007, AUD-029-011 |
| SC-013 | none | UNVERIFIED | [No normal deploy under freeze; every hotfix reconciled by 24h](spec.md#L285) | No event/approval/deferred-gate receipts; [R6](../031-simplify-cicd-pipeline/research.md#L83) retires the controls. | AUD-029-009, AUD-029-011 |
| SC-014 | none | UNVERIFIED | [Quarterly proof of private-only regulated data plane](spec.md#L286) | No actual inventory/audit; [active public settings](../../infra/main.bicep#L493) contradict the asserted desired posture. | AUD-029-003 |
| SC-015 | none | UNVERIFIED | [Zero regulated shared-key paths; all S2S MI/Entra](spec.md#L287) | No auth-path audit; [registry admin/password path](../../infra/main.bicep#L1015) is present, while MI usage elsewhere cannot prove the universal claim. | AUD-029-003, AUD-029-009 |
| SC-016 | none | UNVERIFIED | [Developer backend loop within 15 minutes](spec.md#L288) | No timed onboarding record; [seed auth selector](../../scripts/seed_loader.py#L180) accepts key/AAD but is not short-lived KV issuance or proof of a successful local request. | AUD-029-009, AUD-029-010 |
| SC-017 | none | UNVERIFIED | [Every dev key <=24h, isolated KV storage and environment scope](spec.md#L289) | No issued-key/revocation/access-denial sample; [R6](../031-simplify-cicd-pipeline/research.md#L83) retires key workflow. KV expiry alone would not prove resource-key invalidation. | AUD-029-009, AUD-029-011 |
| SC-018 | none | UNVERIFIED | [All exceptions justified and quarterly reviewed](spec.md#L290) | No exception inventory/review receipt. [Contract](contracts/posture-exceptions.schema.yaml#L1) and deleted original registry cannot prove review or a vacuous 100% success. | AUD-029-009, AUD-029-011 |

## Acceptance Scenario Coverage

`USn-ASm` is this review's stable key for the original numbered acceptance scenario m in user story n;
it does not add or renumber source requirements. Every scenario has source state `none`.
For each independent-test paragraph, the corresponding story rows cover its positive/negative assertions;
none of those independent exercises was performed here.

| Scenario | Source state | Status | Original acceptance obligation | Existing evidence and limit | Follow-up |
| --- | --- | --- | --- | --- | --- |
| US1-AS1 | none | SUPERSEDED | [Noncritical merge reaches 100% under 60m without approval](spec.md#L34) | [R1](../031-simplify-cicd-pipeline/research.md#L5) excludes main CD; actual timing unverified. | AUD-029-010, AUD-029-011 |
| US1-AS2 | none | SUPERSEDED | [Healthy 10/15/30m stages auto-advance](spec.md#L34) | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes canary controller; no stages in current CD. | AUD-029-011 |
| US1-AS3 | none | SUPERSEDED | [Pause/cancel/roll-forward control audited with rationale](spec.md#L34) | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires control surface; generic GitHub cancellation does not write its audit envelope. | AUD-029-007, AUD-029-009 |
| US1-AS4 | none | PARTIAL | [Dashboard exposes 30-day lead time/CFR/MTTR](spec.md#L34) | [DORA helper](../../scripts/dora_metrics_publish.py#L74) exists; [workbook](../../docs/ci-cd/dora-metrics.md#L26) remains future and formulas differ. | AUD-029-010 |
| US2-AS1 | none | SUPERSEDED | [One signed digest/SBOM/provenance per service/merge](spec.md#L51) | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes build flow; [azd](../../azure.yaml#L29) is source build/deploy. | AUD-029-002, AUD-029-011 |
| US2-AS2 | none | SUPERSEDED | [Fail closed on unverified deployment artifact](spec.md#L51) | [R6](../031-simplify-cicd-pipeline/research.md#L83); [active deploy](../../.github/workflows/cd.yml#L227) has no verifier. | AUD-029-002, AUD-029-011 |
| US2-AS3 | none | SUPERSEDED | [Digest query retrieves commit/build/scans/signing identity](spec.md#L51) | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires artifact metadata path; root schema alone proves no queryable production chain. | AUD-029-006, AUD-029-007 |
| US2-AS4 | none | SUPERSEDED | [Manually tagged image rejected and security-audited](spec.md#L51) | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes provenance gate; [image parameters](../../infra/main.bicep#L90) are not expected-build identity checks. | AUD-029-002, AUD-029-007 |
| US3-AS1 | none | PARTIAL | [Every named gate reports an individual status](spec.md#L68) | [CI quality steps](../../.github/workflows/ci.yml#L14) combine categories; full fourteen-category set not required by current graph. | AUD-029-002 |
| US3-AS2 | none | UNVERIFIED | [Median queue-to-complete under ten minutes](spec.md#L68) | No sampled durations; [CI timeouts](../../.github/workflows/ci.yml#L175) are not measured elapsed budgets. | AUD-029-010 |
| US3-AS3 | none | PARTIAL | [Vulnerability/secret/a11y/non-AU PR blocked with report](spec.md#L68) | [Security workflow](../../.github/workflows/security-scan.yml#L18) exists; [CodeQL](../../.github/workflows/codeql.yml#L9) disabled, a11y warn-only, no complete candidate-bound deny/report chain. | AUD-029-002, AUD-029-004 |
| US3-AS4 | none | PARTIAL | [All safety-critical paths require security/compliance reviews](spec.md#L68) | [CODEOWNERS](../../.github/CODEOWNERS#L36) retains narrow incident patterns, not the full domains or verified dual-review state. | AUD-029-009 |
| US4-AS1 | none | SUPERSEDED | [All five SLOs pass windows; 60m final stability](spec.md#L85) | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires stages; separate Z6/Z7 gate is not an equivalent. | AUD-029-001, AUD-029-011 |
| US4-AS2 | none | PARTIAL | [Fast burn restores known-good and audits within five minutes](spec.md#L85) | [Health-triggered rollback](../../.github/workflows/cd.yml#L355) remains but selects unsafe targets and lacks burn-rate/audit/timing assurance. | AUD-029-001, AUD-029-007 |
| US4-AS3 | none | SUPERSEDED | [Slow burn holds traffic and opens SLO issue](spec.md#L85) | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes hold controller; active CD has no live traffic-share state. | AUD-029-011 |
| US4-AS4 | none | SUPERSEDED | [Web slot follows same percentages and burn criteria](spec.md#L85) | [R6](../031-simplify-cicd-pipeline/research.md#L83); [web site](../../infra/main.bicep#L1271) has no equivalent staged slot mechanism. | AUD-029-011 |
| US4-AS5 | none | PARTIAL | [Unhealthy rollback target causes critical alert and stop](spec.md#L85) | [Critical issue](../../.github/workflows/cd.yml#L367) exists, but [bootstrap skip](../../scripts/rollback.sh#L376) can avoid both health verification and escalation. | AUD-029-001 |
| US5-AS1 | none | SUPERSEDED | [Complete AU pack within five minutes on success/failure](spec.md#L103) | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes production pack flow; newer CI publication artifact is not equivalent. | AUD-029-006 |
| US5-AS2 | none | PARTIAL | [Pack write appends compatible audit event/hash](spec.md#L103) | [Root schema](../../contracts/audit-event.schema.json#L8) is incomplete and no current CD pack/emitter pair consumes it. | AUD-029-007 |
| US5-AS3 | none | UNVERIFIED | [Modify/delete denied and attempt security-logged](spec.md#L103) | No negative storage execution/audit record; [module](../../infra/bicep/modules/evidence-store.bicep#L50) lacks declared legal hold/lock and caller. | AUD-029-006 |
| US5-AS4 | none | UNVERIFIED | [Incident-window query correlates operators/recommendations/deploys](spec.md#L103) | No query/trace receipt in S1/S5; [local audit contract](contracts/audit-event.schema.json#L8) is not deployment correlation behavior. | AUD-029-007, AUD-029-011 |
| US6-AS1 | none | SUPERSEDED | [Authorized freeze holds inflight and queues subsequent deploys](spec.md#L120) | [R6](../031-simplify-cicd-pipeline/research.md#L83) deletes freeze; [CD concurrency](../../.github/workflows/cd.yml#L45) is only an environment execution lock. | AUD-029-009 |
| US6-AS2 | none | SUPERSEDED | [Two humans permit hotfix with mandatory gate subset](spec.md#L120) | [R6](../031-simplify-cicd-pipeline/research.md#L83) deletes hotfix; [new runbook](../../docs/ci-cd/progressive-delivery.md#L56) has no group/author/gate checks. | AUD-029-002, AUD-029-009 |
| US6-AS3 | none | SUPERSEDED | [By 24h pack complete and deferred-gate issue recorded](spec.md#L120) | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes pack/hotfix owner; S2/S3 find no deferred-gate runner or deadline blocker. | AUD-029-006, AUD-029-009 |
| US6-AS4 | none | SUPERSEDED | [Release freeze resumes ordered queue and audits transition](spec.md#L120) | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes singleton/control; no durable ordered resume implementation in CD. | AUD-029-007, AUD-029-009 |
| US7-AS1 | none | SUPERSEDED | [Every cloud-touching step uses least-privileged OIDC](spec.md#L137) | [ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L31) explicitly changes active CD/drift auth. Later OIDC workflows do not establish universal compliance. | AUD-029-009 |
| US7-AS2 | none | PARTIAL | [Reject all plaintext secrets outside KV references](spec.md#L137) | [Gitleaks](../../.github/workflows/security-scan.yml#L19) scans source, not all evaluated deployment secrets; [ACR password](../../infra/main.bicep#L1024) has no KV reference. | AUD-029-002, AUD-029-003 |
| US7-AS3 | none | PARTIAL | [Nightly drift creates detailed issue and audit entry](spec.md#L137) | [Weekly replacement](../../.github/workflows/drift-detection.yml#L12) reports resource/property issues but masks some failures and has no append audit. | AUD-029-008 |
| US7-AS4 | none | MISSING | [Next affected PR surfaces open drift issue](spec.md#L137) | S2/S3: [current issue creation](../../.github/workflows/drift-detection.yml#L223) has no corresponding CI path-overlap consumer. | AUD-029-008 |
| US8-AS1 | none | PARTIAL | [Dev public/key access with dev tags, auth and logs](spec.md#L154) | [Storage configuration](../../infra/main.bicep#L493) forbids anonymous blobs; dev labels are only in off-path params and full access-log/anomaly routing is not wired. | AUD-029-003 |
| US8-AS2 | none | CONFLICT | [Regulated data-plane private/MI-only](spec.md#L154) | [Active root](../../infra/main.bicep#L479) configures public Storage/Cosmos and ACR admin auth for all environments. | AUD-029-003 |
| US8-AS3 | none | PARTIAL | [Developer uses KV short key or MI without code changes](spec.md#L154) | [Seed client](../../scripts/seed_loader.py#L180) accepts key/AAD, but no developer-specific KV retrieval/scope/TTL lifecycle or successful request record. | AUD-029-009, AUD-029-011 |
| US8-AS4 | none | SUPERSEDED | [Public/shared-key/connection-string regulated PR denied](spec.md#L154) | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires posture gate; current source settings do not provide a replacement deny control. | AUD-029-002, AUD-029-003 |
| US8-AS5 | none | SUPERSEDED | [Scheduled rotation revokes old and expired keys](spec.md#L154) | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes dev-key issuance; S2/S3 find no scheduled per-developer resource-key revoker. | AUD-029-009, AUD-029-011 |
| US8-AS6 | none | UNVERIFIED | [Cross-developer KV read denied and audited](spec.md#L154) | No access-policy/role/denial receipt; [key contract](contracts/dev-key-issue.workflow.md#L37) describes intent but the workflow is retired. | AUD-029-009 |
| US9-AS1 | none | SUPERSEDED | [Deny public/local-auth/literal-secret/cross-env resource changes](spec.md#L173) | [R6](../031-simplify-cicd-pipeline/research.md#L83) retires the policy driver; surviving generic scans are not the four required rules. | AUD-029-002, AUD-029-003 |
| US9-AS2 | none | SUPERSEDED | [Unknown type blocked pending explicit compliance-approved rule](spec.md#L173) | [R6](../031-simplify-cicd-pipeline/research.md#L83) deletes original bundle; [current matrix](../../infra/policy/posture-matrix.yaml#L1) is not the type registry. | AUD-029-003 |
| US9-AS3 | none | PARTIAL | [Posture drift high-severity issue with actor/time audit](spec.md#L173) | [Drift report](../../.github/workflows/drift-detection.yml#L149) reports deltas but no posture classification/attribution/audit append; errors can appear clean. | AUD-029-008 |
| US9-AS4 | none | SUPERSEDED | [Every deploy checks actual posture and fails if nonconformant](spec.md#L173) | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes verifier; [CD probes](../../.github/workflows/cd.yml#L233) only inspect API/web responses. Dev nonblocking clarification also needs preserved precedence. | AUD-029-003, AUD-029-011 |
| US9-AS5 | none | SUPERSEDED | [Emergency status cannot skip posture gate](spec.md#L173) | [R6](../031-simplify-cicd-pipeline/research.md#L83) deletes both posture driver and emergency workflow; branch hotfix procedure proves no equivalent gate. | AUD-029-002, AUD-029-009 |

## Edge-Case Coverage

EC keys identify the original edge bullets in order; they are reviewer keys, not new source requirements.
All source states are `none`. Retirement evidence is scoped as defined above.

| Edge | Source state | Status | Source obligation and current evidence | Follow-up |
| --- | --- | --- | --- | --- |
| EC-01 | none | SUPERSEDED | [Telemetry unavailable: hold, issue, manual advance](spec.md#L197). [R6](../031-simplify-cicd-pipeline/research.md#L83) retires canary; detached SLI checks cannot protect active CD. | AUD-029-002, AUD-029-011 |
| EC-02 | none | SUPERSEDED | [Emergency during telemetry outage: two humans, record outage, known-good target](spec.md#L198). [R6](../031-simplify-cicd-pipeline/research.md#L83) removes emergency/controller/evidence mechanisms; no outage exercise proof. | AUD-029-001, AUD-029-009 |
| EC-03 | none | PARTIAL | [Concurrent merges queue per service](spec.md#L199). [CD concurrency](../../.github/workflows/cd.yml#L45) serializes per environment, not a persisted per-service FIFO canary queue; no ordered-resume assertion. | AUD-029-002, AUD-029-011 |
| EC-04 | none | SUPERSEDED | [Evidence-store outage fails closed with immutable buffer/replay](spec.md#L200). [R6](../031-simplify-cicd-pipeline/research.md#L83) removes pack flow; no current buffer/replay code in S2/S3. | AUD-029-006 |
| EC-05 | none | UNVERIFIED | [Unavailable CODEOWNERS queue normal changes](spec.md#L201). [Protection descriptor](../../.github/branch-protection.json#L2) is not actual reviewer enforcement; no blocked-merge receipt. | AUD-029-009 |
| EC-06 | none | SUPERSEDED | [Later failed artifact re-verification stops promotion and opens issue](spec.md#L202). [R6](../031-simplify-cicd-pipeline/research.md#L83) removes verification owner; prompt signatures do not substitute for images. | AUD-029-002, AUD-029-011 |
| EC-07 | none | PARTIAL | [Flaky a11y/simulation/load gates fail with issue, no automatic retry](spec.md#L203). [Playwright config](../../apps/web/playwright.config.cts#L3) sets no automatic retries, but [citation accessibility](../../.github/workflows/ci.yml#L229) is warn-only and universal flake-issue handling is absent. | AUD-029-002 |
| EC-08 | none | SUPERSEDED | [Freeze at 50% holds except breach/operator action](spec.md#L204). [R6](../031-simplify-cicd-pipeline/research.md#L83) deletes both stage and freeze state; generic concurrency is not equivalent. | AUD-029-009 |
| EC-09 | none | PARTIAL | [Non-AU deny at PR and runtime, named model-only exception](spec.md#L205). [Root region guard](../../infra/main.bicep#L78) and [new registry check](../../scripts/verify-carveout.ps1#L118) exist, not a complete rendered-resource/policy proof. | AUD-029-004, AUD-029-005 |
| EC-10 | none | MISSING | [Retain known-good images; missing target escalates without rebuild](spec.md#L206). S4 has no retention controller; [rollback empty discovery](../../scripts/rollback.sh#L376) can return success instead of escalation. | AUD-029-001, AUD-029-006 |
| EC-11 | none | PARTIAL | [Bastion/PIM/MI JIT; never open regulated backend](spec.md#L207). [Jump-host module](../../infra/bicep/modules/jump-host.bicep#L25) has Bastion and VM identity, no root call or PIM/session-audit wiring; active backend is public. | AUD-029-003 |
| EC-12 | none | PARTIAL | [Committed dev key blocked; main leak revoked next cycle and audited](spec.md#L208). [Gitleaks](../../.github/workflows/security-scan.yml#L19) exists independently; key rotation/audit path was removed by [R6](../031-simplify-cicd-pipeline/research.md#L83). | AUD-029-002, AUD-029-009 |
| EC-13 | none | SUPERSEDED | [Unknown type denied until explicit reviewed matrix rule](spec.md#L209). [R6](../031-simplify-cicd-pipeline/research.md#L83) removes bundle; [matrix stub](../../infra/policy/posture-matrix.yaml#L1) is not a type gate. | AUD-029-003 |
| EC-14 | none | SUPERSEDED | [Dev reference from regulated templates denied](spec.md#L210). [ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L91) accepts removed topology checks; env-name parameters do not verify every reference. | AUD-029-003, AUD-029-009 |
| EC-15 | none | SUPERSEDED | [Legacy-auth exceptions named, compensated and quarterly reviewed](spec.md#L211). [R6](../031-simplify-cicd-pipeline/research.md#L83) removes register/sweep; no current quarterly exception record proves the original outcome. | AUD-029-009, AUD-029-011 |

## Clarifications and Amendments

Q keys number all 16 original clarification answers in order. None has a source checkbox. Letter-suffix tasks
T000a, T008a, T008b, T019a, T020a, T024a and T079a are individually covered above; no suffix was discarded.

| Clarification | Source state | Status | Clarified obligation and evidence assessment | Follow-up |
| --- | --- | --- | --- | --- |
| Q01 | none | CONFLICT | [Tiered windows versus sub-hour arrival](spec.md#L12): 55m pre-100% windows plus [T079a five-minute smoke](tasks.md#L624) consume the full budget before other work. Current flow is retired, but the original timing conflict remains unclosed. | AUD-029-010, AUD-029-011 |
| Q02 | none | SUPERSEDED | [Only long gates deferred; 24h reconciliation](spec.md#L13). [R6](../031-simplify-cicd-pipeline/research.md#L83) removes emergency workflow; no execution receipts or post-deadline blocker. | AUD-029-009, AUD-029-011 |
| Q03 | none | PARTIAL | [Most recent fully observed, unrolled-back, reverified known-good](spec.md#L14). [Rollback](../../scripts/rollback.sh#L153) chooses an unsorted second active revision; [manifest](../034-webapp-capstone-coverage/known-good.json#L4) empty. | AUD-029-001 |
| Q04 | none | SUPERSEDED | [Privileged Entra groups verified twice and membership-audited](spec.md#L15). [R6](../031-simplify-cicd-pipeline/research.md#L83) retires controllers/reconciler; current environment descriptor is not a verified human group claim. | AUD-029-009 |
| Q05 | none | PARTIAL | [Uniform seven-year legal hold for evidence and all audit](spec.md#L16). [Retained store](../../infra/bicep/modules/evidence-store.bicep#L50) has retention but no hold/lock/caller; no uniform audit authorization proof. | AUD-029-006, AUD-029-007 |
| Q06 | none | PARTIAL | [Named model-hosting-only non-AU exception with minimisation](spec.md#L17). [Constitution](../../.specify/memory/constitution.md#L265) retains the narrow carve-out; [current script](../../scripts/verify-carveout.ps1#L71) is stricter AU-only but not full resource/approval parity. | AUD-029-004, AUD-029-005 |
| Q07 | none | PARTIAL | [Uniform topology A/B and correct policy scope](spec.md#L18). [Root parameter](../../infra/main.bicep#L123) survives without assertion; [initiative](../../infra/bicep/modules/posture-policy-set.bicep#L7) always subscription-scoped. | AUD-029-003, AUD-029-009 |
| Q08 | none | PARTIAL | [Single shared dev, per-developer data/key separation only](spec.md#L22). [CD branch mapping](../../.github/workflows/cd.yml#L70) creates one dev RG; dev-key control is retired and actual tenant isolation not inspected. | AUD-029-003, AUD-029-009 |
| Q09 | none | PARTIAL | [Dev open IPs compensated by auth, synthetic data, rotation/logging/alerts](spec.md#L23). [Storage](../../infra/main.bicep#L493) disables anonymous blobs, but all five compensating controls are not demonstrated; synthetic-data runtime assertion unverified. | AUD-029-003 |
| Q10 | none | PARTIAL | [Bastion/jump-host with PIM 1h default/8h max and logs](spec.md#L24). [Module](../../infra/bicep/modules/jump-host.bicep#L25) lacks active caller, PIM policies and session audit; [quickstart](quickstart.md#L27) contains a placeholder role-assignment condition. | AUD-029-003, AUD-029-011 |
| Q11 | none | PARTIAL | [Matrix sole source for OPA/runtime generator/verifier](spec.md#L25). [Recreated file](../../infra/policy/posture-matrix.yaml#L1) is a differently shaped retention stub; three consumers absent/unconnected. | AUD-029-003 |
| Q12 | none | SUPERSEDED | [OIDC self-service per-developer key issuance/revocation/audit](spec.md#L26). [R6](../031-simplify-cicd-pipeline/research.md#L83) removes workflow; raw key auth in seed loader is not a replacement. | AUD-029-009, AUD-029-011 |
| Q13 | none | SUPERSEDED | [Structural What-If plus deploy Resource Graph cross-env checks](spec.md#L27). [ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L91) retires trust-root checking; no active two-layer boundary proof. | AUD-029-003 |
| Q14 | none | SUPERSEDED | [Full sweep every deploy; dev issue, regulated fail/rollback](spec.md#L28). [R6](../031-simplify-cicd-pipeline/research.md#L83) deletes verifier; health probing and weekly diff do not establish posture. | AUD-029-003, AUD-029-008 |
| Q15 | none | SUPERSEDED | [Dual approval, <=90d expiry, auto-removal, fresh renewal, audit pointer](spec.md#L29). [R6](../031-simplify-cicd-pipeline/research.md#L83) retires registry/sweep; [schema](contracts/posture-exceptions.schema.yaml#L35) merely describes relational dates and lacks distinctness enforcement. | AUD-029-009, AUD-029-011 |
| Q16 | none | PARTIAL | [Defender plus Entra risk signals at proper subscription scope, routed/audited](spec.md#L30). [Defender module](../../infra/bicep/modules/defender-baseline.bicep#L9) only declares pricing; no active caller or risk-event routing. | AUD-029-003, AUD-029-007 |

### Research Decision Accounting

These are authored decision records, not completed experiments or human approvals. The source says research
is complete; that wording does not establish deployment or execution. All research rows have source state `none`.

| Decision | Status | Current trace / contradiction | Follow-up |
| --- | --- | --- | --- |
| R1 | SUPERSEDED | [OPA/conftest decision](research.md#L10) is explicitly retired by [spec-031 R6](../031-simplify-cicd-pipeline/research.md#L83); newer isolated Rego is not the original matrix gate. | AUD-029-003, AUD-029-011 |
| R2 | SUPERSEDED | [Build/sign/SBOM decision](research.md#L23) replaced by [azd source build](../../azure.yaml#L29); no retained attestations for deployed images. | AUD-029-002, AUD-029-011 |
| R3 | SUPERSEDED | [Per-tier canary decision](research.md#L34) retired by R6; root has no equivalent web slot/weighted revision graph. | AUD-029-001, AUD-029-011 |
| R4 | SUPERSEDED | [Five-signal decision](research.md#L46) has no surviving controller; detached Z6/Z7 workflow is not equivalent. | AUD-029-002, AUD-029-011 |
| R5 | SUPERSEDED | [Two-layer boundary decision](research.md#L52) removed under ADR-031 topology deviation; declarations are not assertions. | AUD-029-003, AUD-029-009 |
| R6 | SUPERSEDED | [Full-sweep decision](research.md#L60) retired; current weekly What-If is not a full actual-posture join. | AUD-029-003, AUD-029-008 |
| R7 | SUPERSEDED | [Exception lifecycle decision](research.md#L66) retired with registry/sweep; no quarterly execution proof. | AUD-029-009, AUD-029-011 |
| R8 | PARTIAL | [Dev anomaly decision](research.md#L72) has retained pricing module only, no Entra risk-event forwarding/audit path. | AUD-029-003 |
| R9 | SUPERSEDED | [Key issuance decision](research.md#L81) retired by spec-031 R6; key capability/expiry/isolation still must be resolved before reuse. | AUD-029-009, AUD-029-011 |
| R10 | PARTIAL | [WORM decision](research.md#L87) has standalone retention declaration, no active legal-hold/lock or producer. | AUD-029-006 |
| R11 | MISSING | [Pipeline-state decision](research.md#L93): S3/S4 find no pipeline_state container or known-good cursor; retained audit module uses different database/container/partition. | AUD-029-001, AUD-029-006, AUD-029-011 |
| R12 | SUPERSEDED | [Two-point authority decision](research.md#L99) retired with freeze/hotfix/emitter; no mapped human identity/group verification evidence. | AUD-029-009 |
| R13 | PARTIAL | [Carve-out decision](research.md#L105) has renamed newer registry/verifier; candidate parity and runtime policy still not established. | AUD-029-004 |
| R14 | PARTIAL | [Gateway decision](research.md#L111) maps to current helper/client but fail-open/missing-content branches remain. | AUD-029-005 |
| R15 | PARTIAL | [JIT decision](research.md#L117) has retained VM/Bastion fragment, not active PIM/session logging/private backend. | AUD-029-003 |
| R16 | CONFLICT | [Dual-topology amendment](research.md#L123) is only partially declared; its cost paragraph permits disabling dev Defender under A, contradicting FR-026's mandatory dev coverage. Resolve rather than treating cost prose as exemption. | AUD-029-003, AUD-029-011 |
| R17 / ADR-029-01 | UNVERIFIED | [User/team fallback amendment](research.md#L143) exists; two non-author approvals need sufficient eligible humans, not merely a second total account. Actual collaborator/team/reviewer union and migration status remain unknown; old control files retired. | AUD-029-009, AUD-029-011 |

### Nonfunctional Constraints

NF keys are review-only identifiers for all ten bullets in [Constraints](spec.md#L321); the source contains
no numbered NFR IDs and no checkboxes. Assumptions/dependencies are inputs, not assertions of deployed capability.

| Constraint | Status | Evidence accounting | Follow-up |
| --- | --- | --- | --- |
| NF-01: Constitutional AU placement | PARTIAL | [Active root](../../infra/main.bicep#L78) constrains primary location; full inventory/runtime policy and model boundary require separate proof. | AUD-029-004, AUD-029-005 |
| NF-02: OIDC-only identity | SUPERSEDED | [ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L31) explicitly changes the operational identity path with review triggers. | AUD-029-009 |
| NF-03: Append-only immutable audit | PARTIAL | [Retention fragment](../../infra/bicep/modules/evidence-store.bicep#L50) is neither complete deployment WORM nor validated shared-event persistence. | AUD-029-006, AUD-029-007 |
| NF-04: Existing pipeline continuity | SUPERSEDED | [Spec-031 R1/R6](../031-simplify-cicd-pipeline/research.md#L5) intentionally replaces the mechanism. No continuity/cutover execution record is inferred. | AUD-029-011 |
| NF-05: No downstream rebuild | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes signed-digest owner; current azd rebuild path is not a single artifact promotion chain. | AUD-029-011 |
| NF-06: No new external notification dependency | IMPLEMENTED | Within S2's active CD/drift reporting, [failure issue](../../.github/workflows/cd.yml#L367) and [drift issue](../../.github/workflows/drift-detection.yml#L223) use GitHub-native mechanisms; no new notification service is introduced by those paths. Does not establish all required audit notifications. | AUD-029-007 |
| NF-07: Freeze overrides lead-time objectives | SUPERSEDED | [R6](../031-simplify-cicd-pipeline/research.md#L83) removes freeze; any retained life-safety incident-control obligation needs explicit current disposition. | AUD-029-009, AUD-029-011 |
| NF-08: Dev relaxations cannot enter regulated environments | CONFLICT | [Active public/admin settings](../../infra/main.bicep#L479) are not tiered by environment; no matrix enforcement is connected. | AUD-029-003 |
| NF-09: No regulated data in dev | UNVERIFIED | [Seed hook](../../scripts/seed_loader.py#L643) loads reference data, but source inspection cannot establish everything stored or logged in a deployed dev environment. | AUD-029-003, AUD-029-011 |
| NF-10: Single shared dev; no per-PR/per-developer persistent estate | PARTIAL | [CD mapping](../../.github/workflows/cd.yml#L70) uses one dev RG; developer-key separation retired and actual estate inventory not queried. | AUD-029-009, AUD-029-011 |

### Contract and Entity Accounting

All six local contracts were read fully. They are retained authored artifacts, not evidence of the former
controllers running. The following design defects matter if any portion is reused; none authorizes source edits now.

| Contract | Status | Exact retained contract assessment | Follow-up |
| --- | --- | --- | --- |
| Posture matrix schema | CONFLICT | [Schema](contracts/posture-matrix.schema.yaml#L8) requires a list of three environments and >=2 persona entries, unlike the task's family/property vocabulary and recreated stub. It does not ensure the three names are distinct; its final staging/prod implication is `then: true`, so it does not enforce the advertised security constraint. | AUD-029-003, AUD-029-011 |
| Posture exceptions schema | CONFLICT | [Contract](contracts/posture-exceptions.schema.yaml#L5) is an array; T011 demands an object with exceptions: []. Dates carry descriptions, not the <=90-day relational rule; two handles need not be distinct. Active approvals/renewal/audit require more than validation of this shape. | AUD-029-009, AUD-029-011 |
| Evidence-pack schema | PARTIAL | [Manifest](contracts/evidence-pack.schema.json#L33) allows one inventory item; kind is optional and all required categories are not enforced. No explicit AU restriction on storage_uri, signature verification, actual file/hash match, or two-distinct-approver enforcement; pack_digest self-hash canonicalization also needs an explicit exclusion rule. | AUD-029-006, AUD-029-011 |
| Audit-event schema | CONFLICT | [Local](contracts/audit-event.schema.json#L8) and [root](../../contracts/audit-event.schema.json#L8) differ on metadata/additional properties; neither implements T020a's required list and action enum. Runtime emitter removed. | AUD-029-007 |
| Canary control API | CONFLICT | [Selection query](contracts/canary-promotion.api.md#L54) requires superseded_by IS NULL but omits the explicit not-subsequently-rolled-back condition; this does not specify fallback among three retained historical good images. Hold pseudocode lacks a terminal/continue path before the final advance branch; no implementation resolves it after retirement. | AUD-029-001, AUD-029-011 |
| Dev-key workflow | CONFLICT | [Contract](contracts/dev-key-issue.workflow.md#L37) lists service kinds that conflict with audit service enum and omits audit id. KV secret expiry is not proof a Cosmos/Storage credential expires; account-key regeneration is not automatically per-developer isolation. Per-secret authorization must be specified using a supported RBAC boundary, not asserted from a vault-wide access-policy operation. Issuance fails intact on rotation failure, but no current implementation proves it. | AUD-029-009, AUD-029-011 |

| Data-model entity | Status | Current persistence / lifecycle trace | Follow-up |
| --- | --- | --- | --- |
| Artefact | SUPERSEDED | [Entity 1](data-model.md#L32) belongs to retired signed-build flow; current deployment source does not populate its known-good/provenance fields. | AUD-029-001, AUD-029-011 |
| Canary Stage | SUPERSEDED | [Entity 2](data-model.md#L60) has no live stage cursor after R6 retirement. | AUD-029-011 |
| SLO Burn-Rate Window | CONFLICT | [Entity 3](data-model.md#L87) labels a 60-minute slow-burn window, contrary to the six-hour requirement/contract; no active controller resolves it. | AUD-029-011 |
| Evidence Pack | PARTIAL | [Entity 4](data-model.md#L102) has a schema and retained storage fragment, but not a connected current deploy assembler/retrieval path. | AUD-029-006 |
| Audit Event | PARTIAL | [Entity 5](data-model.md#L127) shares five fields conceptually; source vocabulary/partitioning differs from root schema and retained module. | AUD-029-007 |
| Change Freeze | SUPERSEDED | [Entity 6](data-model.md#L151) singleton/control removed; names also differ across tasks (change-freeze) and model (change_freeze). | AUD-029-009, AUD-029-011 |
| Emergency Hotfix Approval | SUPERSEDED | [Entity 7](data-model.md#L169) has no authoritative approval/deferred-gate producer after retirement. | AUD-029-009 |
| Drift Finding | PARTIAL | [Entity 8](data-model.md#L185) partly maps to current property-diff issue; no persisted status/attribution/audit relationship. | AUD-029-008 |
| CODEOWNERS Path | PARTIAL | [Entity 9](data-model.md#L203) maps only to narrow current path rules, not the full persona ownership graph/protection state. | AUD-029-009 |
| Pipeline Identity | SUPERSEDED | [Entity 10](data-model.md#L215) reflects removed OIDC trust-root; ADR-031 governs current identity. | AUD-029-009 |
| Environment Profile | PARTIAL | [Entity 11](data-model.md#L232) has parameter-name fragments, not assured isolation/private posture or runtime assignments. | AUD-029-003 |
| Posture Matrix | PARTIAL | [Entity 12](data-model.md#L250) differs from recreated retention stub and has no three-consumer enforcement chain. | AUD-029-003 |
| Posture Exception | SUPERSEDED | [Entity 13](data-model.md#L274) register/lifecycle retired; no active approval/expiry proof. | AUD-029-009, AUD-029-011 |
| Developer API Key | SUPERSEDED | [Entity 14](data-model.md#L301) issuer/revoker retired; a developer-supplied COSMOS_KEY is not this lifecycle. | AUD-029-009, AUD-029-011 |
| Foundry Carve-out Entry | PARTIAL | [Entity 15](data-model.md#L326) has a renamed modern registry, but field vocabulary, model parity and review validation differ. | AUD-029-004 |

## Original Checklist and Review Evidence

### Specification Quality Checklist

All 16 original boxes are `[x]` and remain unchanged. CHK keys below are reviewer-assigned in source order,
not original IDs. IMPLEMENTED here assesses an authored document property only, never product delivery.

| Review key | Original state | Status | Original checklist item | Evidence assessment | Follow-up |
| --- | --- | --- | --- | --- | --- |
| CHK-01 | [x] | CONFLICT | No implementation details (languages, frameworks, APIs) | [Source item](checklists/requirements.md#L9) conflicts with detailed OPA/Resource Graph/workflow/SDK prescriptions in clarifications; note permits nouns but not the entire implementation prescription. | AUD-029-011 |
| CHK-02 | [x] | IMPLEMENTED | Focused on user value and business needs | [Nine stories](spec.md#L32) describe roles, value and priorities; not implementation success. | none |
| CHK-03 | [x] | PARTIAL | Written for non-technical stakeholders | [User stories](spec.md#L32) are readable, but clarifications/requirements include detailed identity, API and policy internals. | AUD-029-011 |
| CHK-04 | [x] | IMPLEMENTED | All mandatory sections completed | [Spec structure](spec.md#L32) includes stories, requirements, entities, success criteria, assumptions, dependencies and constraints. | none |
| CHK-05 | [x] | IMPLEMENTED | No [NEEDS CLARIFICATION] markers remain | Full source read found no unresolved marker in the spec; [clarification answers](spec.md#L8) are authored. No claim that contradictions are resolved. | AUD-029-011 |
| CHK-06 | [x] | CONFLICT | Requirements are testable and unambiguous | Timing, freeze authority, audit schema, key capabilities and no-app-change conflicts remain (AUD-029-011); a checked item is not resolution. | AUD-029-011 |
| CHK-07 | [x] | PARTIAL | Success criteria are measurable | [18 SCs](spec.md#L269) name targets; no denominators/samples for universal claims or toil dashboard, and current DORA proxies differ. | AUD-029-010, AUD-029-011 |
| CHK-08 | [x] | PARTIAL | Success criteria are technology-agnostic (no implementation details) | Metrics are largely outcomes, but Azure-region, private-endpoint, identity and KV criteria explicitly depend on technology constraints. | AUD-029-011 |
| CHK-09 | [x] | IMPLEMENTED | All acceptance scenarios are defined | Full spec has 40 numbered scenarios across nine stories, as enumerated above; not evidence they pass. | none |
| CHK-10 | [x] | IMPLEMENTED | Edge cases are identified | [15 edge bullets](spec.md#L195) are fully accounted for in EC rows. | none |
| CHK-11 | [x] | PARTIAL | Scope is clearly bounded | [Constraints](spec.md#L321) bound scope; T085's API addition and source-plan paths still conflict with the no-app-change declaration. | AUD-029-011 |
| CHK-12 | [x] | IMPLEMENTED | Dependencies and assumptions identified | [Both sections](spec.md#L292) are present; their existence does not establish provisioned endpoints, identities, telemetry or retained artifacts. | AUD-029-011 |
| CHK-13 | [x] | PARTIAL | All functional requirements have clear acceptance criteria | 34 FRs including FR-011a are traced above; source contradictions and missing explicit test evidence prevent treating every criterion as settled. | AUD-029-011 |
| CHK-14 | [x] | IMPLEMENTED | User scenarios cover primary flows | [Nine stories](spec.md#L32) cover the named flows; checklist notes incorrectly still say seven stories. | AUD-029-011 |
| CHK-15 | [x] | UNVERIFIED | Feature meets measurable outcomes defined in Success Criteria | No SC run/soak/sign-off in S1/S5; all 18 measured SC outcomes remain UNVERIFIED. | AUD-029-010, AUD-029-011 |
| CHK-16 | [x] | CONFLICT | No implementation details leak into specification | Same concrete prescriptions as CHK-01; [notes](checklists/requirements.md#L33) explain some nouns but do not reconcile the full technical instructions. | AUD-029-011 |

### Plan and Constitution Claims

The plan's [initial check](plan.md#L76) has 14 rows and an overall PASS; its
[post-design check](plan.md#L221) repeats PASS. These are design assessments with source state `none`,
not authenticated persona reviews, deployed security assertions or test results.

| Original plan row | Source claim | Review status | Assessment and current evidence | Follow-up |
| --- | --- | --- | --- | --- |
| 1: Life safety | PASS | UNVERIFIED | Original evidence is the planned freeze; retired mechanism and defective retained rollback do not prove safety operation. | AUD-029-001, AUD-029-009 |
| 2: National principles | PASS | UNVERIFIED | Proposed continual-improvement metrics lack measured audit-derived CFR/MTTR/drift evidence. | AUD-029-010 |
| 3: Multi-hazard design | PASS | IMPLEMENTED | Scoped pipeline design is hazard-agnostic; this does not validate downstream application hazards. | none |
| 4: Transparency/audit | PASS | PARTIAL | Retained schemas/storage do not form an active immutable deployment provenance chain. | AUD-029-006, AUD-029-007 |
| 5: Warning information | PASS / user-mode PASS-WITH-MITIGATION | UNVERIFIED | Mitigation depends on real reviewer authorization/collaboration/protection; no proof was supplied. | AUD-029-009 |
| 6: Evacuation | PASS, not applicable | IMPLEMENTED | Design treats pipeline feature as distinct from evacuation algorithm changes; no downstream evacuation sign-off inferred. | none |
| 7: Recovery | PASS, not applicable | IMPLEMENTED | Design scope statement, not measured recovery/MTTR assurance. | AUD-029-001, AUD-029-010 |
| 8: Azure infrastructure | PASS | PARTIAL | Azure IaC/Actions authored; deployment/correct isolation and actual provisioned state unverified. | AUD-029-003 |
| NN-1: Human in loop | PASS | UNVERIFIED | Group membership, distinct non-author approvals, effective protection and authorization receipts unavailable. | AUD-029-009 |
| NN-2: AU sovereignty | PASS with carve-out | PARTIAL | Root region guard/gateway/registry exist with the identified coverage gaps; live inventory unknown. | AUD-029-004, AUD-029-005 |
| NN-3: Privacy | PASS | UNVERIFIED | Synthetic-only dev claim and mandatory redaction are not established by design checkmark; gateway has bypass cases. | AUD-029-003, AUD-029-005 |
| NN-4: Interoperability | PASS | IMPLEMENTED | GitHub/Azure API integration is authored in scoped workflows; no runtime exchange success implied. | none |
| NN-5: Graceful degradation | PASS | PARTIAL | Retired telemetry hold and evidence-buffer design do not demonstrate active degradation safety; retained rollback has false success. | AUD-029-001, AUD-029-006 |
| QG: Quality gates | PASS | PARTIAL | Current gate graph has missing/disconnected/warn-only categories and no mandatory PR What-If review evidence. | AUD-029-002 |
| Initial overall gate | PASS | UNVERIFIED | No independent approval or executed design gate record accompanies [the conclusion](plan.md#L101). | AUD-029-011 |
| Post-design overall gate | PASS | UNVERIFIED | [Repeated conclusion](plan.md#L221) cites authored schemas, not complete contract enforcement or execution. | AUD-029-007, AUD-029-011 |

### Original Execution and Review Obligations

Source state is `none` for the checkpoint prose. All original named-agent consultations and human/owner approvals
remain UNVERIFIED: listing an agent under a task does not record a consultation or authorize delegation in this
review. This review used no subagents, external approvals, remote queries, installs or product execution.

| Record / obligation | Review status | Accounting and required evidence | Follow-up |
| --- | --- | --- | --- |
| Historical implementation sweep | UNVERIFIED | [Task summary](tasks.md#L28) claims ruff/mypy and 10 passed/11 skipped without OPA; no attached logs, command environment, revision or result artifact. Not proof of later amended requirements or current active delivery. | AUD-029-011 |
| Phase 1 checkpoint | UNVERIFIED | [Setup checkpoint](tasks.md#L112) requires installable tools/actions and dual approval. Current package retired; no historical install/signature/review receipt. | AUD-029-009, AUD-029-011 |
| Phase 2 checkpoint | UNVERIFIED | [Foundation checkpoint](tasks.md#L230) asserts matrix enforcement, identities, freeze/audit operability. No actual policy/identity/side-effect evidence. | AUD-029-003, AUD-029-007, AUD-029-009 |
| US1 checkpoint and independent exercise | UNVERIFIED | [Checkpoint](tasks.md#L274) needs no-op merge-to-prod metric; current source/empty known-good record does not supply timed success. | AUD-029-010, AUD-029-011 |
| US2 checkpoint and independent exercise | UNVERIFIED | [Checkpoint](tasks.md#L313) needs same digest, signature, SBOM and provenance across deployments; no such run artifacts in S1/S5. | AUD-029-006, AUD-029-011 |
| US3 checkpoint and independent exercise | UNVERIFIED | [Checkpoint](tasks.md#L357) needs representative PRs and deliberate negatives with budgets/required statuses; none obtained. | AUD-029-002, AUD-029-010 |
| US4 checkpoint and independent exercise | UNVERIFIED | [Checkpoint](tasks.md#L391) needs injected latency/fast-burn and measured restored health; current source-string tests are not this drill. | AUD-029-001 |
| US5 checkpoint and independent exercise | UNVERIFIED | [Checkpoint](tasks.md#L430) needs complete signed pack, retrieval and real modify/delete denial; schema/retention declarations do not prove it. | AUD-029-006, AUD-029-007 |
| US6 checkpoint and independent exercise | UNVERIFIED | [Checkpoint](tasks.md#L469) needs blocked normal change, two-human hotfix and reconciled evidence. No state-transition/approval receipt; prose also alternates deadline after deploy versus after freeze lift. | AUD-029-009, AUD-029-011 |
| US8 checkpoint and independent exercise | UNVERIFIED | [Checkpoint](tasks.md#L503) needs three actual deployments and dev-key exercise; parameter documents are not runtime posture/access proof. | AUD-029-003, AUD-029-009 |
| US9 checkpoint and independent exercise | UNVERIFIED | [Checkpoint](tasks.md#L537) needs four denied bad PRs, runtime policy enforcement and expired-exception removal; absent original tests/receipts. | AUD-029-003, AUD-029-009 |
| US7 checkpoint and independent exercise | UNVERIFIED | [Checkpoint](tasks.md#L571) needs secret audit plus induced drift issue/audit; active credential deviation and weekly diff cannot certify that prior outcome. | AUD-029-008, AUD-029-009 |
| Phase 13 checkpoint | UNVERIFIED | [Coverage remediation](tasks.md#L616) names C2/C17 staging, C5 secrets, C6 retention/naming, C8 posture rollback, C9 new type, C10 PR context, C12 alert/citation, C15 reports, C18/C19 terminology and added schema/reviewer gates. Individual tasks are covered above; no final analyze report proves all 20 cited findings closed. | AUD-029-011 |
| Original test-case/coverage quotas | UNVERIFIED | T013 >=10/95%; T017 four suites each >=6 fixtures plus A/B; T021 >=8 and sole-validator check; T024a >=5/85%; T026 family pairs/85%; T028 >=12; T046 >=9; T050 >=7; T088 >=95% literal citations. No original suite/coverage artifact exists in S1/S3 to prove any quota or red-before/green-after result. | AUD-029-002, AUD-029-011 |
| T075/T088 analyze executions | UNVERIFIED | No prerequisite-script output, original analyze report, post-remediation report or coverage_check results. Embedded remediation descriptions identify intended fixes, not proof of completion. | AUD-029-011 |
| T076 seven-flow validation archive | UNVERIFIED | Exact historical validation directory/ZIP absent in S1; future path is not linked as evidence. Every quickstart flow is accounted for below. | AUD-029-011 |
| T077 seven-day soak and SC results | UNVERIFIED | No SC-results artifact; all 18 SC rows have explicit limits. A seven-day soak alone would also not establish every rolling-30-day or quarterly claim. | AUD-029-010, AUD-029-011 |
| T078 Cosmos RU performance review | UNVERIFIED | No p95 RU/write baseline, workload/cadence definition, partition tuning or migration record. Retained audit module is not measured pipeline_state behavior. | AUD-029-006, AUD-029-010 |
| External mutations in summary | UNVERIFIED | Script-only descriptions at [tasks.md](tasks.md#L28) expressly defer cloud/GitHub changes. Removed scripts do not prove earlier execution or effective tenant settings. | AUD-029-009, AUD-029-011 |
| Current known-good artifact | UNVERIFIED | [Existing JSON](../034-webapp-capstone-coverage/known-good.json#L4) has empty entries and null update metadata. It is an authored empty artifact, not deployment history or restoration proof. | AUD-029-001 |
| Current branch-protection artifact | UNVERIFIED | [Descriptor](../../.github/branch-protection.json#L2) explicitly says GitHub does not consume it; no remote protection/reviewer setting has been established. | AUD-029-009 |
| Current alternative test assertions | PARTIAL | DevOps tests mostly parse YAML/strings; DORA tests only pagination; Foundry test can use reimplementation. Gateway tests exercise helper allow/deny but not all call-boundary branches. Assertions inspected, none executed. | AUD-029-002, AUD-029-004, AUD-029-005, AUD-029-010 |
| Replacement decision human sign-off | UNVERIFIED | [ADR-031](../../docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md#L3) is an accepted time-bound authored decision; [recommendations](../031-simplify-cicd-pipeline/fr020-recommendations.md#L1) still await maintainer dispositions. No actual approval, rotation or governance-review execution is inferred. | AUD-029-009, AUD-029-011 |

### Quickstart Flow Accounting

The introduction says four flows but seven sections exist. Each procedure's actual capability and its execution
are separate: none of the seven end-to-end outcomes was demonstrated in this review or by local 029 run evidence.

| Flow | Source | Implementation disposition / usability | Execution |
| --- | --- | --- | --- |
| QS-01: Dev key | [Flow 1](quickstart.md#L7) | SUPERSEDED issuer; no current per-developer KV/expiry/revocation path. | UNVERIFIED |
| QS-02: JIT backend access | [Flow 2](quickstart.md#L29) | PARTIAL standalone Bastion module; PIM activation command is a placeholder, no active role/session-log proof. | UNVERIFIED |
| QS-03: Freeze | [Flow 3](quickstart.md#L56) | SUPERSEDED workflow; normal Actions cancel/concurrency does not implement it. | UNVERIFIED |
| QS-04: Emergency hotfix | [Flow 4](quickstart.md#L78) | SUPERSEDED original lane; no equivalent two-person gate/deferred-result finalizer. | UNVERIFIED |
| QS-05: Posture exception | [Flow 5](quickstart.md#L88) | SUPERSEDED original register/gate/sweep; schema and approval cardinality conflict remains. | UNVERIFIED |
| QS-06: Evidence retrieval | [Flow 6](quickstart.md#L112) | SUPERSEDED pack/emitter; documented download/unzip is not manifest/hash/retention assurance. | UNVERIFIED |
| QS-07: Foundry carve-out | [Flow 7](quickstart.md#L138) | PARTIAL renamed modern registry/verifier/gateway; actual candidate parity and valid review enforcement incomplete. | UNVERIFIED |

## Verification Receipt

Report-only checks already passed after the corresponding edits: initial metadata/link validation; 11 unique
unchecked complete follow-ups; exact 94 original task IDs/states (45 SUPERSEDED, 17 MISSING, 14 PARTIAL,
2 CONFLICT, 16 UNVERIFIED); exact 34 FR + 18 SC inventory; all 40 acceptance scenarios; existing local link paths
and line bounds. One out-of-bounds test anchor was corrected and the same check rerun successfully.

The combined final document-only parity check passed: exact task IDs, states and order; exact FR/SC and
acceptance inventories; unique edge/clarification/constraint/flow keys; verbatim checklist items and states;
all research/entity/contract rows; 11 unique unchecked follow-ups with all required fields and no dangling IDs;
637 existing local links with in-bounds line anchors. No nonexistent proposed path is linked as evidence.

Report diagnostics were checked with `get_errors`; the sole issue was MD047 (single trailing newline), addressed
by the permitted mechanical EOF normalization and a closing report-only diagnostic check. No source/configuration,
original task/checklist/evidence, audit-index, branch or commit change was made by this review.

Remaining limits are evidence limits, not blockers to this static report: no original validation ZIP, measured
soak/SC results, deployment/rollback history proving restoration, applied cloud/GitHub authorization state,
real storage-denial record, or authenticated human sign-off was established. Every command in a follow-up is
future-only and requires its stated prerequisites and any necessary separate authorization.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 029 only. Three parallel technical reviews examined retained
rollback behavior, exact-candidate/security gates, and posture/evidence contracts while respecting spec-031 retirement.
The source-completable false-success defect was corrected: when no known-good rollback target is resolved, `rollback.sh`
now exits nonzero instead of treating the condition as a successful first-deployment bootstrap.

Validation: `C:\Program Files\Git\bin\bash.exe -n scripts/rollback.sh` passed. No Azure or GitHub deployment operation
was run. Exact-SHA gate binding, known-good artifact contracts, posture/retention policy, and measured restoration remain
open.
