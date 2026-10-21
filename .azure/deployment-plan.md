# Azure Deployment Plan

> **Status:** Deployed

**Source-only convergence update, 2026-10-20 07:07 UTC:** T053 routing and
T054/T055 preservation corrections are implemented but **not deployed**.
The explicitly approved first-party existing-parent candidate preserves all four
deployment capacities/states and complete RAI actions without vendor edits.
Actual bounded Dev ARM validation succeeds; What-If reports eight NoChange /
45 Ignore, no other or potential changes. All eight before/after payloads match.
This does not apply unrelated root drift, rebuild/publish images, change the
existing zero-business-traffic pair, renew inference budgets or approve rollout.
T056/T057 and T027/T030 remain blocked/partial for missing approved
staging/production evidence. Authoritative scope and hashes are in feature 041
`evidence/dev-preparation/convergence-{candidate-binding,preservation-review}.json`.
The deployment status/outcome below describes the earlier dependency stage,
not deployment of these newer source changes.

**Local build policy amendment, 2026-10-20:** all subsequent local image builds
must target only `linux/arm64`, including preparation and validation builds.
Use the pinned local Bake/Compose/Dev Container configuration. Container Apps
AMD64 artifacts must be built remotely in ACR or native hosted CI, never
locally. Existing images, digests and historical evidence below remain
unchanged; this amendment does not authorise deployment or image replacement.

## Actual dependency remediation outcome - 2026-10-20 04:52 UTC

The corrected pair `ca-api-dev--llm041-deps-20261020t044249` and
`ca-agents-dev--llm041-deps-20261020t044249` is Healthy. All four observed
replicas are started/ready with zero restarts. Full expected application hashes
match; the real API adapter reaches the exact internal agents revision.
Old named revisions retain 100% of shared-ingress traffic; candidates receive
zero business traffic. The agents image is unchanged.

The API's actual pipeline-status Redis client now passes PING using the
refreshing Entra provider and existing app identity. The API's actual shared
retrieval factory successfully reads the configured `corpus` alias metadata,
returning zero documents. A separate actual check also confirms the unchanged
agents image's configured retrieval client succeeds and sees zero documents;
its older SDK behavior is not inferred from the API's different SDK.
No additional agents image is needed for this observed metadata access.

Three additional bounded synthetic calls succeeded, one per tier, with the
actual app identities: 128-token caps, four generated tokens each, one wire
request each, no SDK retries, tools or business data. All provider responses
identify `gpt-5.4-2026-03-05`. Original conservative reservations total eight
of nine: reasoning/drafting are exhausted; at most one simulation reservation
remains. No budget was reset.

Final actual Foundry/account/RAI/diagnostic and Search-service protection
comparisons pass unchanged. Existing pull grants remain exact; no new IAM
grants, application secret-value operations or Foundry resource writes occurred.
No documents were uploaded and no business route or traffic promotion was
performed. The corpus is intentionally empty: approved corpus ingestion and
grounded business acceptance are still prerequisites to a separately approved
business rollout. T027/T030 remain partial for missing other-environment evidence.

Authoritative receipts are `dependency-final-acceptance.json`,
`dependency-runtime-checks-v2.json`, `dependency-unchanged-agents-retrieval.json`,
`dependency-inference.json`, `dependency-staging-v2.json`,
`dependency-publication-v2.json` and `dependency-search-staging.json`.
Earlier attempts, failures and preparation records below remain historical.

Candidate API:
https://ca-api-dev--llm041-deps-20261020t044249.livelydesert-fb4108d0.australiaeast.azurecontainerapps.io

Exact internal agents candidate:
https://ca-agents-dev--llm041-deps-20261020t044249.internal.livelydesert-fb4108d0.australiaeast.azurecontainerapps.io

## Corrected dependency runtime clients - preparation history

The first remediation pair started successfully, but actual client checks
identified two genuine runtime incompatibilities. The existing Redis prior art
incorrectly passed an OAuth scope to MSAL's `resource` argument; actual managed
identity credentials succeed with `https://redis.azure.com` and fail with the
`/.default` suffix. The shared factory now uses the resource URI. The new
Search alias resolves with `2024-05-01-preview`, while stable API versions return
404 for the alias even though the concrete index exists and has zero documents.
The shared retrieval client bundled in the API now explicitly uses that same
repository-established preview API. No extra inference was attempted.

This is an API-image repair with the existing agents image unchanged.
The agents image's actual configured retrieval metadata subsequently passed,
as recorded above. Neither an empty corpus nor successful LLM calls establishes
grounded business acceptance.

### Current validation checklist - corrected API image and pair

- [x] All validation checks pass:
  - [x] Core Validation: fresh 04:38 metadata matches the actual healthy first
    remediation pair; the exact second pair preserves all private application
    configuration, identities and old named traffic. Only the approved image,
    revision suffix and exact API-to-agents URL change.
  - [x] Docker Build: explicit amd64 build succeeds; all four changed runtime
    source files match the actual image; network-disabled held startup and
    runtime dependency closure pass. Local OCI archive index, unique platform
    manifest and config blobs are independently hash-verified before push.
  - [x] Azure Policy Validation: 27 unchanged policy/initiative observations
    remain fresh within one hour; Foundry/account/RAI/diagnostics are unchanged.
- [x] Static roles: no grant, IAM, policy, network or secret-definition writes.
- [x] 76 focused regressions, Ruff and Redis mypy pass.
- [x] Exact preparation proof and prepublication binding recorded.

### 7. Validation Proof - corrected API image and pair

`dependency-prepublication-review-v2.json` binds the verified local OCI graph:
index `sha256:8b974c16194de865a16e18cd77cc49c252cd374c296e3a3783c60fb3b2e0b9b2`,
platform `sha256:e1c0258a41e05a6cab7c65810cf51dbaa5afbe9359c119f61c682bb3887831b2`,
config `sha256:92ead4b0319461877c595728a79ca117fe31176e0d28dcabeeb4730a364228da`.
Its SHA256 is `7aaf472abd6f35dc8ae5737f1af7fa13744fb63825dcf2938239db2b57acc107`.
The Search schema/alias already exists and is read back unchanged: creation is
not replayed. `dependency-patch-review-v2.json` binds both exact requests and
requires a verified matching registry receipt before staging. Actual client
acceptance, using the real API retrieval factory rather than a synthetic
independently configured Search client, remains mandatory after startup.

Dependency review artifact SHA256: `a9d051b1ff557c9816c25a03d6dbc2b15f206401f84b6d5dc9ec003b47f3ac2b`

## Approved dependency remediation - 2026-10-20

The user selected `Approve bounded dependency remediation` after the successful
unheld validation stage. This explicitly permits implementing/testing API Redis
Entra authentication, provisioning only the missing empty Search corpus using
the repository schema on `srch-dev-w3uq6w`, publishing an updated API image and
staging it with the existing verified agents image as a newly matched
zero-business-traffic pair. Existing subscription
`74a25c57-d6e4-446e-8c99-7f5ace60011b`, resource group `ama`, Australia East,
app identities and resource protections remain fixed.

The new four-hour authority is conservatively bounded to
`2026-10-20T07:56:00Z`; the first post-approval clock observation was
`2026-10-20T03:58:10Z`. Obtain fresh actual source-state and policy observations
before cloud writes. Preserve the successful v2 pair and all historical receipts.
No new IAM grants, Foundry resource changes, secret-value retrieval/replacement,
document ingestion, destructive cleanup, business-route invocation or traffic
promotion is approved. Preserve named old traffic and compare complete app
configuration. Use the established narrow JSON Merge PATCH procedure, not root
provisioning.

The original inference budget is retained: five of nine aggregate reservations
are consumed, leaving at most one reasoning, one drafting and two simulation
requests. A single additional request per tier would raise reservations to
eight. Each request remains bounded to at most 512 generated tokens, without
tools or business data; do not replay existing ledgers.

### Dependency remediation checklist

- [x] Reuse repository Redis authentication patterns and compatible dependencies;
  preserve local operation and surface configured-client failures.
- [x] Resolve existing Search schema/alias conventions without inventing a new
  business schema; prepare an empty, non-destructive provisioning request.
- [x] Run focused regressions, lint/type checks and the exact API build.
- [x] Refresh live source/policy metadata against the actual successful v2 pair;
  review exact schema and digest-bound app requests.
- [x] Complete azure-validate before executing through azure-deploy.
- [x] Provision only the reviewed missing corpus, publish/restage the approved
  image pair at zero traffic, and verify actual clients and remaining inference.
- [x] Persist actual outcomes; keep business promotion closed.

The Redis factory is shared by API pipeline status and ingestion dedup without
importing the worker's logging/telemetry side effects. Azure uses the existing
system-assigned identity and the refreshing `redis-entraid` provider; only
validated local development connections may remain anonymous. Configured
construction errors surface, and degraded runtime operations log safe error
types rather than silently claiming shared persistence. Package-feed metadata
confirms `redis-entraid==1.2.2` supports patched PyJWT (`>=2.15,<3`), unlike
1.2.1's restrictive metadata; the API manifest and workspace lock are updated.
75 focused regressions/package-policy checks and Ruff pass; both changed Redis
runtime modules pass mypy.

Search preparation reuses `_build_index_definition` from the ingest runner:
`corpus-v1`, 23 fields, 3072-dimensional embedding, existing HNSW/profile and
provenance conventions, with `corpus` pointing to `corpus-v1`. Authenticated
reads using the repository's `2024-05-01-preview` alias API confirm the alias
is absent; stable index metadata confirms zero indexes. Creation will use a
create-only index operation and conditional alias creation, never an update
of existing content or a fabricated parity-gate result. No documents are
approved for upload; an empty schema does not establish grounded business
retrieval quality.

### Current validation checklist - dependency schema and publication

- [x] All validation checks pass:
  - [x] Core Validation: exact authenticated subscription/tenant, fresh full
    source-state hashes, explicit create-only Search schema/conditional alias
    requests, scoped operations and unchanged protected resources. The prior
    narrow data-plane/JSON Merge PATCH amendment remains applicable: root ARM
    validation/What-If is neither authorized nor an equivalent preview of
    Search data-plane creation or registry publication.
  - [x] Docker Build: explicit `linux/amd64` final build succeeds. Config digest
    `sha256:f199b4888b3cf92eca4a7234dcae35c9822ffe0cce9aae459330e8d16ad749f3`.
    All three changed source files match bytes inside the actual image.
    Runtime packages are Redis 8.1.0, redis-entraid 1.2.2 and PyJWT 2.15.1.
    Isolated network-disabled held startup returns liveness/startup 200,
    readiness/business-route 503. No cloud dependencies are invoked.
  - [x] Azure Policy Validation: actual 04:08 UTC metadata capture plus 27
    freshly recollected unchanged assigned initiative/relevant rule semantics.
- [x] Static role verification: generated operations contain no IAM or policy
  writes; retain existing system identities and ACR-scoped pull assignments.
  Existing same-identity Redis Entra PING already established access.
  Operator uses existing Search access; no grant fallback is permitted.
- [x] Record proof and exact prepublication review below.

### 7. Validation Proof - dependency schema and publication

`dependency-prepublication-review.json` binds the complete repository Search
schema and alias, actual missing targets, unchanged service resource hash,
successful v2 source pair, full protected comparison, existing pull roles and
the exact built API config. `dependency-image-source-verification.json` and
`dependency-image-isolated-smoke.json` record actual offline image checks.
75 focused tests pass, Ruff passes, and mypy passes for both changed Redis
runtime modules. The built runtime's `pip check` reports no broken requirements.
No unresolved failures apply to this exact scope.

Prepublication review artifact SHA256: `c2418b2ba61f55d3fc5a1da09fb580de7fde2796d34efec3f1beb9c26729430b`

### Actual schema/publication outcome and next exact pair

The empty `corpus-v1` schema and conditional `corpus` alias creation succeeded;
the complete expected schema and unchanged Search service resource were read
back. No document ingestion occurred.

The API push succeeded, but its first verification correctly stopped at an
identity-type mismatch: Docker containerd's `Id`/`Descriptor` identifies the
OCI **index**, not the image config. The original receipt/review is retained
with that incorrectly labelled field; it is not rewritten as a successful
comparison. Read-only reconciliation verified the exact unchanged tested
index `sha256:82846c07343adebdba8298377e2f89fbbf3a0c263f7babe4cc65f2e76942c919`,
its unique linux/amd64 child and the exact built config
`sha256:f199b4888b3cf92eca4a7234dcae35c9822ffe0cce9aae459330e8d16ad749f3`.
No image changed and no push was repeated. The authoritative publication
receipt is `dependency-publication-verified.json`; the agents image is unchanged.

### Current validation checklist - dependency application PATCH pair

- [x] All validation checks pass:
  - [x] Core Validation: complete exact source comparison against the healthy
    v2 pair, immutable verified image identities, new exact internal agents
    revision binding, resolver-complete environment and no secret definitions.
    Only the previously approved narrow JSON Merge PATCH delta is generated.
  - [x] Docker Build: successful exact linux/amd64 image, actual source/package
    verification, isolated startup and clean dependency closure as above.
  - [x] Azure Policy Validation: same fresh 04:08 metadata/policy observations
    remain within their one-hour validity; no changed identity/security/model
    bindings or resource scope.
- [x] Static roles: no generated grants; existing app identities and exact
  ACR scope preserved. No root provisioning or secret reconstruction.
- [x] Exact second-stage request review and protection proof recorded.

### 7. Validation Proof - dependency application PATCH pair

`dependency-patch-review.json` binds both complete PATCH hashes, protected
resource comparison, the new suffix and exact internal pair URL. All tiers
resolve from the actual proposed environments. The published API is bound to
the verified OCI graph/config above; the agents index/config is unchanged.
Schema availability is now proven, but app-identity Search and actual repaired
Redis client checks remain runtime acceptance, not inferred from provisioning.

First-remediation pair review artifact SHA256: `5c5415845b07705154e547270a8bd05ca95657e9aea50c08ca4b3c1dd233cbfc`

## Approved unheld Dev validation - actual outcome at 03:53 UTC

The corrected pair `ca-api-dev--llm041-val-20261020t033002` and
`ca-agents-dev--llm041-val-20261020t033002` is Healthy. All four observed
replicas passed startup/readiness with zero restarts. The API's real adapter
configuration reached the exact internal agents revision successfully.
Both candidates remain at zero traffic; old named revisions retain 100%.

Actual app-identity inference passed reasoning, drafting and simulation:
three observed wire requests, 128-token caps, no SDK retries, no tools or
business data, and four generated tokens per response. Each provider response
identified `gpt-5.4-2026-03-05`, matching the independently observed model state.
The two earlier failed console-handshake reservations remain conservatively
consumed; aggregate reserved maximum is five requests, not a reset budget.
See `unheld-inference-attempt2.json` and its referenced first-attempt ledger.

Complete application hashes match both exact expected requests. Final actual
Foundry/account/RAI/diagnostic preservation passed at 03:53:48 UTC. There were
no new grants, application secret-value requests/submissions, Foundry resource
writes, business route invocations or traffic promotion.

**Remaining business-readiness blockers:** the configured Search target
`corpus` returns 404 and authenticated metadata shows no indexes. The API's
pipeline-status Redis client sends no authentication and fails, while an
Entra-authenticated PING with that same app identity succeeds. These are not
missing Foundry permissions. Cosmos database authorization and both actual
Blob audit/archive container checks pass. An initial five-second Cosmos probe
was inconclusive; the bounded 15-second follow-up passed. Blob account-info
403 is not a valid substitute for the successful application container checks.

Redis client/dependency changes require a rebuilt API image, outside this
stage's unchanged-image approval. Provisioning Search schema/aliases also
exceeds metadata-only dependency checks. Neither repair nor business promotion
has been performed. The current healthy validation pair remains at zero traffic.
Authoritative outcome: `unheld-final-acceptance.json`.

### Scope of the completed stage

After successful held staging, the user explicitly approved
`unheldDevValidation=true` and `syntheticInference=true`. Continue the exact
existing Dev subscription, region, app identities and verified image pair.
Create new zero-business-traffic unheld revisions, bind the exact API-to-agents
validation pair, permit normal Dev startup governance/coordination writes and
maintenance, and inspect the existing configured dependencies' metadata and
authorization. Containment may stop only these newly created validation
revisions. No new grants, Foundry resource changes, secret-value retrieval/
replacement or traffic promotion.

Only after startup checks pass, allow at most three small synthetic requests
per existing reasoning/drafting/simulation alias (nine total), with at most
512 generated tokens each, no business data/tools and explicit accounting for
retries. The existing authority window ends 2026-10-20 04:06 UTC.
Refresh observations against the actual held state; preserve all previous
evidence. Run prepare/validate/deploy for the new exact requests before writes.
Final business promotion remains separately gated.

### Current validation checklist - unheld application PATCH pair

- [x] All predeployment validation checks pass:
  - [x] Core Validation: authenticated exact Dev target, complete read-only
    request review, same-environment exact agents revision binding, fresh source
    fingerprints, zero secret definitions and no root provisioning. The existing
    specifically approved JSON Merge PATCH amendment applies; ARM PUT What-If
    is not represented as validation of a different request.
  - [x] Docker Build: reuse the already built and verified immutable pair;
    no runtime source/image changes or republication in this stage.
  - [x] Azure Policy Validation: actual 03:13 UTC preservation capture and
    27 freshly recollected unchanged policy/initiative semantics.
- [x] Static role verification: preserve existing identities and ACR pull
  bindings; no role assignment, network or Foundry writes in this operation.
- [x] Record focused regressions and exact request/preservation proof.
- [x] Execute agents first; verify its actual revision FQDN equals the reviewed
  API binding before applying the API request. Preserve named old traffic.
- [x] Check actual startup/readiness and bounded dependency authorization.
  Perform synthetic inference only after startup checks pass.
- [ ] Resolve Search corpus provisioning and API Redis authentication before
  considering a separately approved business promotion.

Unheld review file: `unheld-patch-review-v2.json`.
Unheld review artifact SHA256: `3166402bad9c77e5d9723d7f6278504e2b38614248a1ef745cc9336ae4e3c3eb`

The first unheld attempt provisioned both requests with exact preservation,
but lacked the resolver-required `AZURE_AI_PROJECT_REGION`; actual replicas
were not ready. Bounded console probes timed out, so no dependency or inference
success is inferred. Only those two new validation revisions were deactivated.
No inference requests or traffic promotion occurred. First-attempt review,
stage receipts and recorded diagnostic observations remain separate history.

The corrected v2 proposal adds the actually observed/verified Australia East
region to the explicit routing settings. Both complete proposed environments
now pass the actual shared resolver for all three tiers before any write.
64 focused tests and Ruff pass, including complete-environment resolution and
missing/foreign-region rejection. The source is the exact preserved first
attempt, with both previous candidates verified contained; images and all
other approved boundaries are unchanged.

### 7. Validation Proof - unheld validation preparation

The read-only operational preparation compared the complete current app states
against their exact held-stage hashes, generated both held=false requests,
verified unchanged Foundry/account/RAI/diagnostic controls, and persisted only
safe request fingerprints. Both requests preserve all original secrets and
non-approved configuration. The API proposal rejects missing/shared/cross-
environment agent URLs and requires the matching internal revision FQDN.
64 focused tests pass; Ruff checks pass. Existing build/isolated-entrypoint and
published manifest/platform/config proofs apply to the unchanged image pair.
Runtime outcomes are now recorded above; passing static checks alone was not
used as runtime or inference evidence.
Authenticated `az account show` matches the exact approved subscription/tenant.
A second independent read-only request reconstruction matches the review
exactly. Actual ACR-scoped role assignment GETs match both published app
principals, the exact ACR scope and the AcrPull definition. No new RBAC changes
are generated. Fresh complete protection comparison passes again.

The completed held-deployment record below remains historical evidence.

Historical validation scope: the exact digest-bound held-bootstrap application
PATCH pair. Publication and both scoped pull grants completed at
2026-10-20 01:08:19Z; registry bytes/config digests match the approved images.
The second checkpoint completed and both exact held requests were applied.
No business release, unheld startup or inference is included.

## Actual deployment outcome — 2026-10-20 01:36 UTC

Both apps provisioned successfully with revision suffix
`llm041-held-20261020t010013`. Each has two Running replicas with successful
startup probes, `started=true`, zero restarts and intentionally `ready=false`.
Both exact registry digest/config bindings and system-identity pull grants are
verified. Full normalized writable configuration matches the pre-write expected
hashes; secret definitions were never submitted or their values requested.

Old named revisions retain 100% traffic; each held candidate has zero business
traffic. No inference, startup seeding, business promotion or Foundry write
occurred. All four model deployments, RAI, account protections and diagnostics
compare unchanged. Old unhealthy placeholders remain incident-state references,
not a healthy rollback pair. This is held initialization acceptance only.

Authoritative outcome: `held-bootstrap-staging.json` and
`held-bootstrap-live-verification.json` in feature 041 Dev preparation evidence.
57 focused tests, Ruff and prior four-module mypy pass; no commit was created.
Unheld initialization, actual downstream authorization/inference, exact final
API-to-agents pairing and business traffic promotion remain separately gated.

Existing API ingress (still pinned to the old revision):
https://ca-api-dev.livelydesert-fb4108d0.australiaeast.azurecontainerapps.io

Existing internal agents ingress (also pinned to the old revision):
https://ca-agents-dev.internal.livelydesert-fb4108d0.australiaeast.azurecontainerapps.io

### Current validation checklist — held application PATCH pair

- [x] All validation checks pass:
  - [x] Core Validation: exact 2025-07-01 Update request contract, complete
    request-delta review, fresh source fingerprints and zero secret definitions.
    The explicitly approved PATCH method replaces only the non-equivalent PUT
    What-If for these two requests.
  - [x] Docker Build: unchanged vetted images; authoritative registry bytes,
    platform manifests and approved configs match isolated entrypoint evidence.
  - [x] Azure Policy Validation: unchanged effective assignments/27 semantics;
    no new location, Foundry resource, security exclusion or broader role scope.
- [x] Complete old configuration privately compared; only the approved image,
  routing, hold/runtime, probes, registry auth, revision mode/suffix and named
  traffic pins differ. Real provider location `Australia East` is preserved.
- [x] Live pull-grant visibility: both exact principals have AcrPull at the ACR,
  confirmed after provisioning; no root `azd provision` is permitted.
- [x] First-bootstrap containment accepted; no healthy rollback or business
  readiness asserted. No unheld initialization, inference or traffic promotion.
- [x] Exact reviewed requests bound to this plan; immediate source comparison
  and complete post-PATCH preservation comparison enforced before continuing.

Review artifact SHA256: `2c78468d8676a377433ab6f2bee75110b1b763d8447b1323444e66bc7df7d9ef`

Review file: `held-bootstrap-patch-review-v3.json`. It records the documented
`application/json` media type with JSON Merge Patch semantics and fully
specified probes. Initial/v2 reviews are retained separately, never executed.
No application request has been sent at this validation checkpoint.

Execution checkpoint: API provisioned successfully at the approved held
revision. The first post-check stopped on provider reordering of the three
type-discriminated probes. Exact original pre-write aggregate hash
`59be622fccf473d7cd6d92156c56f571c7c2a4c921ecb55cf7c958f3389d66bd`
matches the live application after probe-type ordering alone; no writable
configuration discrepancy remains. The reconstruction also matches that same
pre-write hash, rather than assuming values or accepting other differences.
See `held-bootstrap-probe-order-reconciliation.json`. 57 focused checks now
pass, including genuine secret/scale drift detection. Resume never re-sends
the API PATCH; it must verify that original expected hash and recheck the
unchanged reviewed agents source/request before sending only the pending one.

### Completed publication validation — publication and scoped pull grants

- [x] All validation checks pass:
  - [x] Core Validation (CLI/auth; exact imperative request review). No ARM
    resource template is being deployed in this checkpoint. The user explicitly
    accepted exact PATCH review rather than a non-equivalent ARM PUT What-If
    for the subsequent application updates.
  - [x] Docker Build: both approved local images built and normal-entrypoint
    isolated-network smoke passed; graceful shutdown exit 0.
  - [x] Azure Policy Validation: 11 unchanged assignments and 27 unchanged
    relevant policy/initiative semantics captured at this checkpoint.
- [x] Static role verification: precisely AcrPull
  `7f951dda-4ed3-4680-a7ca-43fe172d538d`, both approved app principals and
  exact ACR scope. No general Contributor/Owner or Foundry role writes.
- [x] Registry prerequisites: live LegacyRegistryPermissions mode and enabled
  ARM-token authentication confirmed; existing SystemAssigned principals match.
- [x] Record final focused-check results and validation proof.

## 7. Validation Proof — current 041 held-bootstrap operation

Held-pair checkpoint: 53 focused tests pass (the preparation/bootstrap/adapter/
health modules named below), Ruff passes; runtime source/images are unchanged.
Preparation proves source identities/region/ports, complete configuration
preservation, exact approved MI-auth rebind and pinned old traffic, rejects
unreviewed init-container activity, and compares all captured Foundry state.
Registry provenance and both live grant assignments are recorded in
`held-bootstrap-publication.json`. The reviewed source and request hashes in
the v3 artifact are rechecked immediately before each application mutation.
Command: `.\.venv\Scripts\python.exe -m pytest tests\unit\test_llm_application_pair_preparation.py tests\contract\test_bootstrap_hold.py tests\unit\test_llm_adapter_snapshots.py tests\contract\test_api_health_dependencies.py -q --no-cov`.

Fresh source: `held-bootstrap-prestage-refresh.json`, 2026-10-20 00:47:49Z.
Policy proof: `held-bootstrap-prestage-policy.json`, 27 unchanged semantics.
Isolated startup proof: `bootstrap-normal-entrypoint-smoke.json`, both image
IDs match the user's explicit publication approval.
The bounded operation driver permits publication and only the two approved
resource-scoped grants; it never persists credentials or literal environment
values. Application staging requires a separately bound exact request-review
artifact and immediate drift check. The previous Foundry-write preview is not
used to validate this application-only operation.

Publication checkpoint results: exact subscription/tenant Enabled; registry
mode and ARM-token authentication confirmed by authorised metadata reads.
48 focused preparation/bootstrap/health/adapter tests passed; Ruff passed and
mypy found no issues in the four changed runtime modules. Both approved images
were built successfully and their normal entrypoints passed isolated-network
containment with startup/liveness 200, readiness/business 503 and exit 0.
No failure remains for this publication-only checkpoint. Historical unrelated
test failures are not claimed resolved, and business release is not validated.

Docker's containerd store identifies local images by OCI index/manifest rather
than config digest. The first publication attempt stopped at local lookup,
before any image push or role grant. A streamed local image archive verified
both complete cryptographic index/platform/config bindings against the exact
approved configs; no image contents or credentials were persisted. Evidence:
`bootstrap-image-identity-bindings.json`. The corrected publisher selects these
already smoke-tested immutable local references, not mutable tags.

## Current approved operation: application-only held bootstrap

This section supersedes historical operation scopes below, not their evidence.
The user approved application-only preparation and subsequently explicitly
approved both resource-scoped AcrPull grants, immutable image publication,
system-identity registry configuration and held Multiple-mode staging for
`ca-api-dev` and `ca-agents-dev` in the existing confirmed Dev subscription/RG.
No Foundry resource will be written. The supported JSON Merge PATCH contract,
exact request review and pre/post preservation checks are the explicitly
accepted validation method for these two updates; a different ARM PUT What-If
is not represented as equivalent.

The inherited role is Search Index Data Reader, not registry pull access.
The two authorised AcrPull assignments are restricted to `crdevw3uq6w`:
API principal `7dc8a9f2-1bdc-41c8-9481-aea97b09717a` and agents principal
`0b986a72-f194-41f5-8f6b-ea070229aaeb`. No broader role or permission change.
Both currently have a password-reference registry binding, not an MI binding.
The approved system-identity configuration replaces that registry authentication
reference only; it neither reads nor changes the underlying `acr-password`
secret definition/value. Other registry entries remain unchanged.

The vetted local image IDs are API
`sha256:c42aff32ee93a012a6bbd5869c0279ed461b6ebe4c200de147b387be0b3dd0f8`
and agents
`sha256:ac7290a1e0a6eb1a40788743effee0ca4335afd1c6e6e9b551196af027327a97`.
Both normal entrypoints passed isolated-network startup, held readiness (503),
business-request containment and graceful exit (0). These are local config IDs,
not authoritative registry manifest digests; verify those after publication.

Stage exact digest references with `AMA_BOOTSTRAP_HOLD=true`, dispatcher runtime,
explicit probes and existing named traffic pinned at 100%; candidates receive
zero business traffic. Omit secret definitions entirely, preserve unknown
secret values, identities, existing registry entries, other environment values,
scale, volumes, sidecars and all other non-approved configuration.

The old placeholder revisions are unhealthy incident-state references, not a
healthy rollback pair. Held staging verifies initialization/containment only;
readiness 503 is intentional, not business-readiness acceptance. Failure means
containment and forward repair, never a claimed healthy rollback. Clearing hold,
startup seeding, inference and promotion require separate approval. The full
root template, `azd up`, staging and production remain excluded.

Renewed observation authority is recorded in
`resumed-validation-approval.json` under feature 041 Dev preparation evidence:
2026-10-20 00:06:01Z–04:06:00Z, with maximum one-hour observation age.
The publication/staging approval is recorded separately. Plan validation applies
only to this bounded held-bootstrap operation; business release remains blocked.

## Resumed blocker remediation — 2026-10-20

The user requested resuming implementation and thoroughly addressing deployment
blockers, with technical-agent assistance permitted. Continue the existing Dev
target and bounded scope; preserve unrelated work and all earlier evidence.

1. Resolve deployment capacity/state and RAI action preservation using verified
   supported interfaces; do not edit the pinned vendored child or silently
   substitute an unapproved raw-resource composition.
2. Establish complete application configuration preservation, actual immutable
   publication candidates and a safe paired bootstrap/rollback procedure.
3. Renew the expired scoped Azure observation/validation authority, refresh
   evidence and reconcile changed candidate bindings before live validation.
4. Run required local and actual scoped validation, then obtain the stage-specific
   release decision against exact image/configuration/template bindings.

The prior G0 window has expired. Local implementation/research may proceed;
new live operations require the renewed scope. No full-root deployment, unrelated
resource change, permission change, secret disclosure or automatic traffic switch.

## Current carve-out approval and explicit quorum waiver

On 2026-10-20 the project lead explicitly instructed skipping the additional
approver requirement, then selected **All environments** with waiver review
deadline **2030-11-20**. `infra/parameters/foundry-carveout.yaml` records this
as `quorum_waiver`, with `johnbilliris` as the sole authoriser. No independent
approval is asserted. Normal quorum settings remain unchanged and resume when
the waiver expires at the end of that UTC date; malformed/expired waivers fail.

The registry now includes the actual `gpt-5.4` model for Dev, approved only by
`johnbilliris`. Its model review deadline remains **2027-04-08**, on the existing
registry review cycle, not the waiver's 2030 deadline. AU region checks,
data-protection flags, model identity and model review windows remain enforced.
Both schemas, PowerShell and OPA recognise the explicit exception.

The strict **offline replay** of the unchanged corrected Dev preview now passes,
as does actual OPA evaluation of the registry. OPA evaluation after waiver expiry
denies the one-approver row and restores the normal quorum. Evidence:
`specs/041-llm-deployment-routing/evidence/dev-preparation/single-approver-waiver-replay.json`.
Earlier captured live checks remain historical; this is not fresh ARM validation.

Release is still blocked by capacity/state and RAI preservation, fresh authorised
live evidence with the changed registry binding, immutable publication/config
and safe rollback/bootstrap readiness, plus stage-specific release approval.
This policy amendment grants no deployment or staging/production model change.
No Azure requests, image push, inference, deployment or commit occurred.

## Historical carve-out validator correction

The user requested rectification of the registry check. The check now compares
`after.properties.model.name` with registry `model_name`, never the deployment
alias or previous model. Missing proposed identities fail closed; Ignore/Delete
entries do not constitute model deployments. Region checks cover both legacy
top-level and actual proposed-resource locations. No approval record was added.

Offline replay of the unchanged corrected Dev preview now accepts the embedding
deployment through its registered `text-embedding-3-large` model. The three chat
aliases are still rejected for the genuine missing `gpt-5.4` registry entry.
The new replay is `model-identity-carveout-replay.json` in the evidence directory;
prior preview/check results remain historical and immutable.

All ten new regression cases pass; the combined related run reports 27 passed
and the same pre-existing invalid positive fixture failure (eastus / 2030 date).
PowerShell parsing and focused Python lint/format pass. No Azure requests,
publication or deployment occurred for this correction. Release remains blocked.

## Historical Dev deployment request and corrected live preview

The user requested **"deploy to dev"**, then explicitly approved fresh validation
of the corrected bounded candidate **with release gates enforced**. No genuine
dual-review approval reference was supplied.

At 2026-10-19 22:35 UTC, refreshed target/protection/application metadata matched
the earlier baseline and all 27 relevant policy semantics were unchanged.
ARM validation passed. The corrected real preview reports **seven Modify,
one NoChange, 45 Ignore, zero resource creates/deletes**. Diagnostics are now
**NoChange**, proving the local preservation correction against the live target.

The strict carve-out still fails, exit 4, for the four exact Dev deployment
names. The remaining seven modifications omit deployment currentCapacity/state
and RAI action fields. The exact 2026-05-01 deployment input reference includes
currentCapacity and deploymentState; Running/Paused affects inference availability.
These omissions are not proven read-only noise and cannot be silently cleared.
The unchanged pinned AVM child does not expose those inputs.

`evidence/dev-preparation/corrected-validation-review.json` under feature 041
records the authoritative raw JSON, exact hashes, approval, documentation review
and unresolved release blockers. Prior evidence remains unchanged.
Capture scripts now accept distinct output paths to avoid invalidating old hashes.
The validation workflow remains at error resolution, not Validated.

No image publication, resource deployment, inference, traffic change, permission
change or commit occurred. Full-root deployment remains prohibited.

## Current operation: 041 bounded Dev validation

The historical deployment record below concerns a different application target
and grants no authority for this operation.

- Mode: MODIFY; existing development resources, no new service or capacity.
- Target tenant: `8ae9933a-1eb0-4922-8ecf-c71a136feff3`.
- Subscription: `74a25c57-d6e4-446e-8c99-7f5ace60011b`.
- Resource group: `ama`; region: `australiaeast`.
- Existing AIServices account: `cog-dev-w3uq6w`.
- Recipe: Azure CLI bounded ARM validation and What-If, not deployment.
- Approved scope: refreshed metadata/policy evidence, strict carve-out validation,
  and preview of four existing deployments, three RAI policies and diagnostics.
- Template: `specs\041-llm-deployment-routing\evidence\dev-preparation\deployments.template.json`,
  SHA256 `694566b23dfeebdb32f330795b074c49f7eec2591987e92750cdc68d9c443f3c`.
- Parameters: adjacent `deployments.parameters.json`,
  SHA256 `d96c2f010bebdc04634e764e6cda5639e2df8ec05ec92cec86bf726a3c4de0d7`.
- Approval: current user approved this exact preview scope and renewed its window
  for two hours after the 2026-10-19 21:43 UTC expiry check. Record exact new
  timestamps in the operation's approval evidence before live requests.
- Evidence freshness: maximum one hour; changed bindings require reconciliation
  and reapproval.
- Exclusions: no parent account writes, role assignments, model changes, capacity
  changes, permission changes, image publication, inference, activation or traffic.
- Do not deploy `infra\main.json` or run `azd up`: unrelated drift is not approved.
- Applications: real API/agents local candidates exist; registry manifest digests
  and a healthy corrected rollback pair are not established. Release remains blocked.
- Staging/production: no authority or accepted baseline.

### Current validation checklist

- [ ] All validation checks pass:
  - [x] Core validation commands: CLI/auth, exact bounded build, ARM validation and What-If.
  - [x] Docker builds: both real local application candidates built; not published.
  - [x] Azure Policy validation: refreshed effective assignments and 27 relevant semantics unchanged.
- [x] Bounded candidate preparation and actual local application builds recorded.
- [x] Refresh target, deployment, protection, policy and revision evidence.
- [x] Verify exact compiled template and parameter hashes.
- [x] Run strict carve-out against the captured bounded preview: latest offline replay PASS under the explicit quorum waiver; fresh live validation remains pending.
- [x] Run ARM What-If and review every material difference: eight Modify, 45 Ignore.
- [x] Record passing and failing evidence without declaring release readiness.
- [ ] Obtain separate release-stage authority before any cloud mutation.

### Current validation proof: 2026-10-19 21:57 UTC

Evidence is under `specs\041-llm-deployment-routing\evidence\dev-preparation`.
`validation-review.json` binds exact raw evidence hashes and lists every delta.
Metadata refreshed at 21:51 UTC matches original protected-state observations;
all 11 effective policy assignments and 27 relevant definition semantics match.
ARM validation and What-If operations succeeded, but that is not release clearance.

The real JSON contains zero resource creates/deletes, eight Modify and 45 Ignore.
The helper's text counter counted nested property lines (23 Modify / 21 Delete),
not resource changes; those console counts must not be reported as resources.
Four deployment modifications omit returned currentCapacity/deploymentState;
diagnostics omit three disabled categories and zero-day retention fields;
three RAI policies omit returned action=NONE. These differences remain unresolved,
not silently accepted as provider defaults or cleared preservation checks.

`verify-carveout.ps1 -Strict -WhatIfPath <actual preview>` failed, exit 4,
for all four exact Dev deployment names. The registry has older model-name rows
and no gpt-5.4 approval. No reviewer identity, approval date or exemption was invented.
All deployment/publication/inference/traffic gates remain closed.

### Local-only diagnostic remediation

The user selected **"Continue local remediation only; keep deployment blocked"**.
No dual-review approval evidence was supplied; no further Azure validation was run.

The Dev snapshot now explicitly preserves all five log categories, their exact
enabled/disabled states, zero-day disabled retention and the existing metric.
The root/module interface and both Dev parameter surfaces carry the same snapshot;
omitted overrides retain the previous defaults for other environments.
The compiler contract now compares full diagnostic entries, not only enabled
category names, and covers explicit empty arrays independently of missing fields.

Actual local results: 48 compiled/configuration tests passed, root/module build
and lint passed, focused Python lint/format passed, and Dev PSRule reported
797 Pass / zero Fail. PSRule needed its already installed Bicep executable and
the repository's 60-second expansion timeout explicitly supplied to this process;
no installation or policy configuration change was made.

The corrected files are `diagnostics-reconciled.template.json` and
`diagnostics-reconciled.parameters.json` in the evidence directory; exact hashes
and unchanged application source/image/CSV bindings are recorded in
`diagnostics-remediation-bindings.json`. The original preview does NOT validate
this corrected candidate. Its changed bindings require separately approved fresh
What-If. RAI action/returned deployment field deltas and the strict registry
approval failure remain unresolved. No registry approval requirement was waived.

Generated: 2026-10-16

---

## 1. Project Overview

**Goal:** Fix Azure Monitor Live Metrics authentication in the API, grant its managed identity telemetry-publishing access, rebuild the container image, and roll it out to the existing dev Container App.

**Path:** Modify existing Azure application

## 2. Requirements

| Attribute | Value |
|-----------|-------|
| Classification | Development |
| Scale | Small; existing single Container App |
| Budget | Cost-optimized; no infrastructure or SKU changes |
| Subscription | ME-MngEnvMCAP035973-prbillir-2 (`74a25c57-d6e4-446e-8c99-7f5ace60011b`), confirmed by user |
| Location | Australia East, confirmed by user |

## 3. Components Detected

| Component | Type | Technology | Path |
|-----------|------|------------|------|
| AMA API | API | Python 3.12, FastAPI, Azure Monitor OpenTelemetry | `apps/api` |
| API image | Container | Docker; remotely built in ACR | `apps/api/Dockerfile` |
| Telemetry authorization | RBAC | AVM resource-scoped role assignment | `infra/bicep/modules/eval/eval-platform.bicep` |

## 4. Recipe Selection

**Selected:** Azure CLI — targeted application-image update

**Rationale:** The API is already deployed and its image is built remotely by ACR. Apply only the scoped App Insights role assignment and API image update; do not redeploy the full evaluation platform. Refresh the existing `dev` image tag and use a new revision suffix so the app deploys the new digest while keeping its configured image reference consistent.

## 5. Architecture

**Stack:** Existing Azure Container Apps deployment

### Service Mapping

| Component | Azure Service | SKU |
|-----------|---------------|-----|
| API | Container App `app-ama-api-dev` in `rg-ama-eval-dev` | Existing Consumption profile; no change |
| Container image | ACR `acramaevaldevzeaes6.azurecr.io` | Existing registry; no change |
| Telemetry | Existing Application Insights connection string and user-assigned managed identity | No resource change |
| Telemetry authorization | Monitoring Metrics Publisher role on the existing App Insights component | One resource-scoped assignment to the API identity |

### Supporting Services

| Service | Purpose |
|---------|---------|
| Azure Container Registry | Build and store the API image |
| Azure Container Apps | Run the API using the updated image |
| User-assigned managed identity | Authenticate the Live Metrics exporter |
| Application Insights | Existing destination for application telemetry |

## 6. Provisioning Limit Checklist

No compute, storage, or monitoring resources/SKUs will be added. One resource-scoped `Microsoft.Authorization/roleAssignments` assignment will be created for the API identity on the existing App Insights component. The operation also rebuilds an image in the existing ACR and updates the existing Container App revision; service provisioning quotas are not applicable.

| Resource Type | Number to Deploy | Total After Deployment | Limit/Quota | Notes |
|---------------|------------------|------------------------|-------------|-------|
| `Microsoft.Authorization/roleAssignments` | 1 | 1 | Not applicable | Scoped to the existing App Insights component; only `Monitoring Metrics Publisher` for the API identity |

**Status:** No new service provisioning; one narrow RBAC assignment.

## 7. Execution Checklist

### Phase 1: Planning
- [x] Analyze workspace and existing Azure deployment
- [x] Confirm subscription and location with user
- [x] Prepare resource inventory; no new resources
- [x] Scan API and Docker build configuration
- [x] Select targeted Azure CLI recipe
- [x] User approved this plan
- [x] User approved the scoped App Insights role assignment and deployment

### Phase 2: Execution
- [x] Pass `AZURE_CLIENT_ID` to `ManagedIdentityCredential`
- [x] Add an AVM resource-scoped `Monitoring Metrics Publisher` assignment for the API identity
- [x] Synchronize the generated eval-platform ARM template
- [x] Run API syntax validation and test suite
- [x] Build and push `ama/api:dev` to the existing ACR
- [ ] Deploy only the scoped App Insights role assignment (no full platform deployment)
- [ ] Update `app-ama-api-dev` with a unique revision suffix
- [x] Omit unsupported temperature from GPT-5 Foundry requests
- [x] Run focused Foundry client tests
- [x] Build and push `eval-runner:dev` to the existing ACR
- [x] Update `caj-eval-runner-dev` to the rebuilt image

### Phase 3: Validation
- [x] All validation checks pass
  - [x] Focused Foundry client test suite
  - [x] ACR remote build for eval-runner
- [x] Targeted Azure deployment preflight passed
  - [x] Azure CLI auth, Bicep compile, group validation, and role-assignment what-if
  - [x] Docker image build (remote ACR build; local Docker daemon unavailable)
  - [x] Azure Policy review (no applicable deny conflict)
- [x] Confirm deployment and active revision
- [x] Check `/api/health` and app logs for the Live Metrics credential error
- [x] Record validation proof below

### Phase 4: Deployment
- [x] Report deployed image and revision
- [x] Update `caj-eval-runner-dev` to the rebuilt image

## 7. Validation Proof

Validation so far:

| Check | Command Run | Result | Timestamp |
|-------|-------------|--------|-----------|
| Python syntax | `python -m compileall -q apps/api/app/main.py` | Passed | 2026-10-16 |
| API tests | `python -m pytest -q apps/api/tests` | 241 passed; 19 failed and 4 errors in unrelated API/contract tests | 2026-10-16 |
| ACR API image build | `az acr build --registry acramaevaldevzeaes6 --image ama/api:dev --file apps/api/Dockerfile --platform linux/amd64 .` | Remote run `cr3` succeeded; digest `sha256:5edcebc192736c9acad1a10a6ac7f27d85233dcef162e4ac27c093e90981b304` | 2026-10-16 |
| Eval Bicep compile | `az bicep build --file infra/bicep/modules/eval/eval-platform.bicep --outfile $env:TEMP\eval-platform-validation.json` | Passed with existing `no-hardcoded-env-urls` warning | 2026-10-16 |
| Updated eval Bicep compile | `az bicep build --file infra/bicep/modules/eval/eval-platform.bicep --outfile $env:TEMP\eval-platform-role-validation.json` | Passed; existing `no-hardcoded-env-urls` warning only | 2026-10-16 |
| Foundry client tests | `python -m pytest -q tests/unit/eval/test_foundry_failures.py` | 15 passed | 2026-10-17 |
| Runner Foundry + build-context tests | `python -m pytest -q tests/unit/eval/test_foundry_failures.py tests/unit/eval/test_run_llm_evaluation_script.py` | 63 passed | 2026-10-17 |
| Eval-runner ACR build | `az acr build --registry acramaevaldevzeaes6 --image eval-runner:dev --file <minimal-context>\apps\eval-runner\Dockerfile --platform linux/amd64 --no-logs <minimal-context>` | Run `cr6` succeeded; digest `sha256:38398c3cb9e05578990b431786465ecaeb470d1cdd6b952b0f05856b3da7f3d6` | 2026-10-17 |
| Runner ACR pull role | `az role assignment list --scope <ACR-resource-id> --assignee <runner-principal-id> --include-inherited` | `AcrPull` present | 2026-10-17 |
| Single-role ARM validation | `az deployment group validate --resource-group rg-ama-eval-dev --template-file .azure/appinsights-rbac-once.bicep --parameters principalId=... appInsightsResourceId=...` | Succeeded; validated one role assignment | 2026-10-16 |
| Single-role what-if | `az deployment group what-if --resource-group rg-ama-eval-dev --template-file .azure/appinsights-rbac-once.bicep --parameters principalId=... appInsightsResourceId=...` | Exactly 1 role assignment Create; 17 existing resources ignored; no other changes | 2026-10-16 |
| API identity registry role | `az role assignment list --scope <ACR-resource-id> --assignee <API-principal-id>` | `AcrPull` present | 2026-10-16 |
| App Insights identity role | `az role assignment list --scope <App-Insights-resource-id> --assignee <API-principal-id> --include-inherited` | `Monitoring Metrics Publisher` assigned at the App Insights component scope | 2026-10-16 |
| Policy review | Subscription policy query and project governance constraints | No applicable deny policy for the resource-scoped publisher assignment | 2026-10-16 |

Local Docker daemon was unavailable, so the API image was built by ACR instead. The API test suite failures include unrelated contract assertions and a missing local `redis` dependency; none reference the changed startup file. Azure validation is pending.

The ACR build command's local log streamer exited on a Windows code-page encoding error, but ACR run `cr3` completed with `Succeeded`; its reported image digest is recorded above. The full API suite reported 241 passed, 19 failed, and 4 errors in tests unrelated to the changed startup file (including a missing local `redis` package); those unrelated failures are recorded and were not modified. The targeted Bicep/ARM and image-build checks passed.

## 8. Deployment Results

| Item | Result |
|------|--------|
| App Insights role assignment | `Monitoring Metrics Publisher`, assignment `b1d51d26-19b0-5fcd-8dff-e4998d136f21`, scoped to the eval Application Insights component |
| Role deployment | `api-appinsights-role-20261016` succeeded |
| API image | `acramaevaldevzeaes6.azurecr.io/ama/api:dev` (`sha256:5edcebc192736c9acad1a10a6ac7f27d85233dcef162e4ac27c093e90981b304`) |
| Container App revision | `app-ama-api-dev--otel-uai-1016`, Provisioned and Healthy, 1 replica, 100% traffic |
| Health endpoint | HTTP 200; overall status `healthy` (its separate tenant-telemetry status fields remain unconfigured) |
| Live Metrics | Three QuickPulse pings returned HTTP 200; 24 telemetry transmissions succeeded; no exporter errors in the inspected logs |
| Runner image deployment | `az containerapp job update --name caj-eval-runner-dev --resource-group rg-ama-eval-dev --container-name runner --image acramaevaldevzeaes6.azurecr.io/eval-runner:dev` | Succeeded; job provisioning state `Succeeded`; image points to rebuilt dev tag | 2026-10-17 |

**Validated by:** Azure validation workflow  
**Validation timestamp:** 2026-10-16

## 9. Files to Change

| File | Purpose | Status |
|------|---------|--------|
| `apps/api/app/main.py` | Select the configured user-assigned managed identity for Azure Monitor | Updated |
| `apps/eval-runner/src/ama_eval/foundry_client.py` | Omit temperature for GPT-5 Foundry inference calls | Updated |
| `tests/unit/eval/test_foundry_failures.py` | Assert GPT-5 requests omit temperature | Updated |
| `infra/bicep/modules/eval/eval-platform.bicep` | Grant the API identity scoped telemetry-publishing rights | Updated |
| `infra/bicep/modules/eval/eval-platform.json` | Keep compiled ARM template synchronized with Bicep | Updated |
| `.azure/deployment-plan.md` | Record the deployment plan and validation results | In progress |

## 10. Next Steps

> Current: Complete

Deployment completed and verified.
