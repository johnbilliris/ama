# Offline preflight and controlled rollout evidence

**Local build policy amendment, 2026-10-20:** all subsequent local image builds
must target only `linux/arm64`. AMD64 deployment images must be built remotely
in ACR or native hosted CI. Earlier AMD64 commands/results below are historical
observations, not instructions to repeat locally; their digests are not changed.

## Bounded Dev dependency remediation accepted - 2026-10-20 04:52 UTC

The user explicitly approved API Redis repair, an empty repository-defined
Search corpus, replacement API publication and a newly matched zero-traffic
pair using the existing agents image. Renewed authority ends conservatively
at 07:56 UTC. See `dependency-remediation-approval.json`.

The corrected pair suffix is `llm041-deps-20261020t044249`: both apps are
Healthy, four replicas are started/ready without restarts, full application
preservation hashes match, and the real API adapter reaches the exact internal
agents revision. Old named shared-ingress traffic remains 100%; candidates
remain zero. Existing identities, secrets, scale and unrelated configuration
are preserved.

The API pipeline-status store and ingestion worker share a lightweight Redis
factory with refreshing Entra credentials and validated local-development
support. Actual client testing exposed that MSAL needs the resource URI
`https://redis.azure.com`, not an OAuth `/.default` scope; the corrected actual
API client passes PING. Compatible `redis-entraid==1.2.2` and patched PyJWT
install cleanly. The actual API retrieval factory uses the existing Search
preview API required for aliases and successfully reads `corpus` metadata.
The unchanged agents image's actual configured retrieval metadata also passes.

Only the repository's 23-field, 3072-dimensional `corpus-v1` schema and missing
`corpus` alias were created, with create-only/conditional operations. No
documents were uploaded. Initial runtime failures and the publication
index-versus-config identity reconciliation remain recorded, not relabelled
as passing tests or silently replayed. Final API OCI index/platform/config
bindings are independently verified from local archive blobs and registry bytes.
76 focused regressions, Ruff, Redis mypy, exact source-byte verification,
isolated held startup and runtime dependency closure pass.

Three new app-identity synthetic calls actually succeeded, one per tier:
one wire request each, no retries/tools/business data, 128-token caps and four
generated tokens each. Provider model remains `gpt-5.4-2026-03-05`. Including
the original uncertain reservations, the maximum consumed budget is eight of
nine; reasoning/drafting are exhausted and only one simulation reservation
remains. No new grants, application secret operations, Foundry writes,
business invocations or promotion occurred.

`dependency-final-acceptance.json` is the final actual protection/health record.
Supporting receipts include `dependency-runtime-checks-v2.json`,
`dependency-unchanged-agents-retrieval.json`, `dependency-inference.json`,
`dependency-staging-v2.json`, `dependency-publication-v2.json` and
`dependency-search-staging.json`. The empty corpus establishes structural
availability, not grounded business quality. Corpus ingestion, grounded
acceptance and traffic promotion remain separately gated; feature completion
remains 50/52 because staging/production evidence is still missing.

## Unheld Dev validation outcome - 2026-10-20 03:53 UTC

The separately approved unheld/inference stage is recorded in
`evidence\dev-preparation\unheld-validation-approval.json`. The first unheld
attempt lacked required `AZURE_AI_PROJECT_REGION`; both new revisions were
contained without changing old traffic. Preparation now carries the actually
observed region and resolves all three tiers from each complete proposed
environment before writes. 64 focused tests and Ruff pass.

The corrected `llm041-val-20261020t033002` pair is Healthy, with four
successfully started/ready replicas and zero observed restarts. The API adapter
reaches the exact new internal agents revision. Both candidates remain at zero
traffic; old named revisions retain 100%. Source/request/preservation hashes,
probes, secrets, scale and all unrelated configuration remain preserved.

Three observed synthetic inference requests succeeded using verified app
identities: reasoning and drafting from API, simulation from agents. Each was
capped at 128 generated tokens, used no tools/business data and generated four
tokens. Provider model `gpt-5.4-2026-03-05` matches live protected metadata.
Retries were disabled and transport bounded to one wire request per check.
Two prior failed-handshake reservations remain consumed conservatively:
aggregate reserved maximum five, within the original nine-request limit.
No business endpoint was invoked or traffic promoted.

Cosmos database and actual Blob audit/archive metadata authorization pass.
The initial short Cosmos timeout and account-info Blob 403 were investigated,
not misreported as missing grants. Redis Entra PING succeeds with the app
identity, but the existing API pipeline-status client sends no authentication.
Search `corpus` returns 404; authenticated inventory confirms zero indexes.
These two broader application prerequisites block business release. Fixing the
client requires a new image approval; Search schema provisioning exceeds the
approved metadata-only dependency checks. Neither has been performed.

`unheld-final-acceptance.json`, `unheld-staging-v2.json`,
`unheld-local-health-v2.json`, `unheld-pair-connectivity.json`,
`unheld-inference-attempt2.json`, `unheld-dependency-authorization-details.json`
and `unheld-dependency-runtime-specific-checks.json` provide the current proof.
Final Foundry resource/protection comparisons pass unchanged at 03:53:48 UTC.
No new grants, application secret-value operations, resource retirement or
Foundry resource writes occurred. Earlier held-stage evidence below is
historical, not a restriction retrospectively applied to the later approval.

## Latest Dev checkpoint — 2026-10-20

The user approved application-only held-bootstrap staging and exact PATCH
validation, with no Foundry writes or business promotion. The original
Foundry-write preview is not accepted as preserving capacity/state/RAI actions;
its historical failures remain intact. The approved scope avoids those writes
and retains independent live preservation comparisons.

Implemented strict held startup and separate startup/liveness/readiness for
API and dispatcher. Normal entrypoints passed isolated-network startup,
business containment and graceful exit 0. The published immutable image pair
was verified against authoritative registry manifest bytes and the exact
approved config digests, including the containerd index/platform/config chain.
Both explicit app-identity AcrPull grants now exist at the ACR resource only.
Publication completed at 2026-10-20 01:08:19Z; application updates had not yet
occurred at that publication checkpoint.

Fresh target/protection evidence and 27 policy/initiative semantic comparisons
passed under renewed G0, 00:06:01Z–04:06:00Z, with a one-hour observation limit.
57 focused preparation/bootstrap/health/adapter tests passed, Ruff passed and
the four changed runtime modules passed mypy. These checks do not prove
downstream authorisation or inference readiness.

Evidence is in `evidence/dev-preparation/`: `held-bootstrap-approval.json`,
`bootstrap-normal-entrypoint-smoke.json`, `bootstrap-image-identity-bindings.json`,
`held-bootstrap-prestage-refresh.json`, `held-bootstrap-prestage-policy.json`
and `held-bootstrap-publication.json`.

### Actual held staging and live verification

At 2026-10-20 01:36 UTC both exact revisions
`ca-api-dev--llm041-held-20261020t010013` and
`ca-agents-dev--llm041-held-20261020t010013` are provisioned successfully.
Each has two Running replicas, successful startup probes, zero restarts and
intentional held readiness false. Old named revisions keep 100% traffic;
both candidates have zero business traffic.

`held-bootstrap-patch-review-v3.json` binds the exact requests. The API
post-check initially stopped on provider reordering of the three
type-discriminated probes. Ordering by probe type alone reproduces the exact
original pre-write aggregate hash; no config change was accepted as noise.
`held-bootstrap-probe-order-reconciliation.json` proves that comparison.
The API was not rewritten; only the unchanged reviewed pending agents request
was then sent. Genuine secret-reference/definition and scale drift still fail
the focused regression checks.

Final `held-bootstrap-staging.json` and `held-bootstrap-live-verification.json`
record complete writable configuration preservation and independent unchanged
Foundry/account/RAI/diagnostic comparisons. There were zero secret-value
requests, zero secret definitions submitted, zero Foundry writes and zero
inference calls. No business startup seeding, traffic promotion or commit.
Business activation remains blocked; old unhealthy placeholders are not a
healthy rollback pair. Clearing hold creates new revisions and still requires
separate unheld-startup, actual dependency/inference and final pairing evidence.

## Authority and current status

This contains the T029 procedure and final T052 human review handover for the
local comparison tool, including the optional T046 migration interface. It is **not**
permission to collect evidence, run What-If, call a model, provision, activate
or retire resources. Approved target evidence is absent: **target P1 readiness
and real P2 operational acceptance remain BLOCKED**. Synthetic fixtures, dev
observations and a passing local command cannot satisfy those gates.

Baseline states are `uncollected -> observed -> reconciled -> approved`:

- **Uncollected**: no target observation; never populate from repository
  defaults, another environment or historical dev observations.
- **Observed**: G0-authorised collection records actual target properties,
  collection time, source revision, scope and current image/config pairs.
- **Reconciled**: review the repository/compiled proposal against observed and
  baseline properties, including explicit candidate bindings. Resolve every
  discrepancy; do not homogenise protections or model selections.
- **Approved**: an accountable approver accepts the exact scoped evidence,
  policy/version, revisions and validity window. This is baseline approval,
  **not** G4 release approval.

G0 records approver, target tenant/subscription/resource group/account/environment,
operations, credential arrangements, collection/validation scope and window.
An inventory/metadata collection grant is not What-If or canary authority.
A later G0 validation scope may authorise target checks/CI-CD What-If needed
for G4. G4 separately specifies permitted canary, switch and promotion stages
and windows. G5a provisioning, G5b traffic and G6 retirement remain independent.
No command below authorises an Azure operation.

## Executable interface

Run from `C:\code\ama` with **already authorised, reviewed local files**:

```powershell
.\.venv\Scripts\python.exe scripts/verify-llm-deployment-preflight.py --inventory C:\evidence\inventory.json --baseline C:\evidence\baseline.json --outputs C:\evidence\outputs.json --candidate C:\evidence\candidate.json
```

The CLI has those four required file arguments and optional synthetic `--at`.
Optional `--migration <local JSON>` and
`--stage {provision,canary,switch,forward,rollback,retain,retire}` must be supplied
together; they compare the P2 evidence contract in
[naming-migration.md](naming-migration.md), never execute a stage.
Paths are resolved locally; arbitrary current working directories are supported.
It makes no ARM, data-plane, model, subprocess or refresh calls and writes no
files. Python bytecode writes are disabled before the shared routing import.
There is no credentials input, activation mode or permissive routing switch.

Exit/status contract:

| Result | Exit | stdout | stderr |
| --- | --- | --- | --- |
| Supplied comparisons pass | 0 | One JSON object below | Empty |
| Missing/malformed/unreadable/stale/inconsistent evidence | 1 | Empty | `ERROR: <location>: <actionable rule>` |
| Missing/invalid CLI arguments | 2 | Empty | argparse usage and diagnostic |

```json
{"status": "pass", "scope": "local supplied-evidence comparison only", "target_readiness": "not established"}
```

Diagnostics identify schema/rule locations, not supplied payloads, secrets,
tenant values or prompts. Files remain under the operator's custody. This
is an equality/freshness validator, **not an authenticity verifier**: approval,
collection and invalidation declarations must be independently authenticated
by the authorised reviewers. It never infers external authority from JSON.

## Exact JSON input contract

UTF-8 JSON objects only. Duplicate properties, NaN/Infinity, wrong types,
missing fields, empty required strings and null/unreadable properties fail.
All timestamps are ISO-8601 with explicit timezone. Object order is irrelevant;
types and array order are preserved in comparisons. Additional properties in
target, bindings and snapshots participate in equality; they cannot disappear
between evidence items.

### Common envelope (all four files)

| Field | Required contents |
| --- | --- |
| `target` | Non-empty strings `tenant`, `subscription`, `resource_group`, `account_id`, `environment`, `endpoint`, `region`. Identical throughout; region must be Australian. Use actual approved account resource ID/endpoint, not an alias. |
| `observed_at` | Collection/build observation time, not future at use. |
| `source_revision` | Exact evidence source/repository revision, not a default branch label. Baseline can predate candidate. |
| `approval` | `{ "approver": "...", "approved_at": "...", "valid_until": "..." }`. Approved at/after observation, not future, not expired. Durations come from supplied approvals, never a tool TTL. |
| `policy_id`, `policy_version` | Exact approved policy ID/version from baseline. |
| `bindings` | Non-empty strings `configuration_digest`, `api_image`, `agents_image`, `compiled_proposal_revision`. Exact candidate bindings, except explicit reconciled pre-candidate baseline below. Compiled revision identifies the exact compiled IaC **and parameters**. |
| `invalidation` | `{ "evaluated_at": "...", "events": [] }`. Evaluation between observation and use; absent/unevaluated or any invalidating event blocks reuse. |
| `synthetic` | `true` for every synthetic fixture. Required for using `--at`, which is restricted to synthetic testing; omit `--at` for real evidence so current UTC is used. |

`configuration_digest` is lowercase SHA-256 of the UTF-8 canonical JSON
object `{"api": <API environment object>, "agents": <agents environment object>}`,
using Python `json.dumps(value, sort_keys=True, separators=(",", ":"),
ensure_ascii=True)`. Hash the **actual complete candidate environments**,
not a selected subset. `api_image` and `agents_image` equal their corresponding
immutable `sha256:<64 lowercase hex>` service image digests. Evidence source
revisions remain explicit even where all candidate bindings match.

### Inventory and baseline snapshots

Both contain `snapshot`:

```text
snapshot:
  deployments:
    reasoning: Deployment
    drafting: Deployment
    simulation: Deployment
  embedding: EmbeddingDeployment
  controls:
    rbac: non-empty property object
    managed_identity: non-empty property object
    access: non-empty property object
    network: non-empty property object
    authentication: non-empty property object
    diagnostics: non-empty property object
    residency: "AU"
  services:
    api: ServicePair
    agents: ServicePair
```

`Deployment` has non-empty string `name`, `model_id`, `model_version`, `format`,
`sku`, `rai_policy`, `version_upgrade`; positive integer `capacity`; and a
non-empty `effective_filters` property object. `EmbeddingDeployment` has all
those fields plus positive integer `dimensions`. Capture observed effective
RAI/filter content, role assignments/identities, network, local authentication,
diagnostics and residency properties in full; an unreadable property is a
blocker, not an empty-object/default substitute. False/zero controls are
readable values, not missing evidence. Reviewers establish actual completeness;
local comparison cannot discover omitted Azure properties.

`ServicePair` is:

```text
image: immutable sha256 digest
revision: exact revision reference
environment: complete JSON object of string setting values
```

Both API and agents pairs are mandatory. Inventory snapshot must exactly equal
approved baseline snapshot, including current pair revisions. This prevents
silently comparing another running image/environment.

Inventory additionally contains `collection_authority`:

```text
reference: G0 collection-authority record reference
approver: accountable authoriser reference
target: exact common target object
operations: ["inventory", "metadata"]
valid_from: timezone-bearing timestamp
valid_until: timezone-bearing timestamp
```

That supplied scope/window must cover **both** baseline and inventory collection
observations. Expired collection authority does not retrospectively invalidate
an authorised observation; current reuse is governed by the approved freshness
policy and current evidence approvals. The tool does not exercise that grant.
If the original baseline collection is outside the supplied scope/window,
supply the properly authorised evidence rather than widen/fabricate a grant.

Baseline additionally requires `state: "approved"` and `freshness_policy`:

```text
id: approved policy identifier
version: approved policy version
approval: approval object
max_age_seconds:
  inventory: positive number or null
  baseline: positive number or null
  outputs: positive number or null
  candidate: positive number or null
invalidation_actions:
  destination: ["recollect", "reapprove"]
  model: ["recollect", "reapprove"]
  protection: ["recollect", "reapprove"]
  embedding: ["recollect", "reapprove"]
  policy: ["recollect", "reapprove"]
  rbac: ["recollect", "reapprove"]
  network: ["recollect", "reapprove"]
  images: ["recollect", "reapprove"]
  configuration: ["recollect", "reapprove"]
  compiled_proposal: ["recollect", "reapprove"]
  scope: ["recollect", "reapprove"]
  drift: ["recollect", "reapprove"]
```

The action arrays must be non-empty and contain `recollect` and/or `reapprove`
as the **approved policy** requires; the example does not choose a production
policy. Explicit `null` means that policy supplies no age limit for that item;
it does not bypass approval expiry, bindings or invalidation. Missing policy,
version, approver, window decision or invalidation decision fails closed.
The tool never clears events, performs actions or automatically refreshes.
Applicable G0 is needed for recollection and the responsible approver for
reapproval. Refresh does not grant G4/G5.

If a pre-candidate baseline's bindings differ, baseline must additionally carry:

```text
reconciliation:
  from_bindings: exact original baseline bindings
  to_bindings: exact candidate bindings
  target: exact common target
  source_revision: exact baseline source_revision
  policy_id: exact approved policy ID
  policy_version: exact approved policy version
  approval: current approval object, at/after baseline observation
```

Reconciliation is a supplied reviewed decision, not a converter that accepts
model/protection drift. Snapshot parity and policy windows still apply.
Other evidence items must already bind the exact candidate. No inference
from an old `approved` state or recent timestamp substitutes for reconciliation.

### Outputs and candidate

Candidate has `services` with the exact paired candidate images, revisions and
environments. Outputs has `snapshot` with unchanged deployments, embedding and
controls, but its `services` must equal candidate services exactly. Changing
code/env is intentional; changing resource/model/protection properties is not.

Outputs also has `parameters` and `child_parameters`, each an object with
exactly these nine non-empty string selections:

```text
reasoningDeploymentName   reasoningModelName   reasoningModelVersion
draftingDeploymentName    draftingModelName    draftingModelVersion
simulationDeploymentName  simulationModelName  simulationModelVersion
```

Each matches its approved tier snapshot; child selections equal top-level
selections. Existing names remain explicit: purpose/environment defaults
(`reasoning-${environmentName}`, etc.) are for **new resources only**, never
a way to rename an existing P1 resource. Already-established purpose-named
baselines are valid too. T024–T027/T030 must later prove actual compiler
pass-through/defaulting and complete resource-diff acceptance; synthetic
`outputs.json` is **not** that proof.

Both candidate environments must publish the complete `_DEPLOYMENT`,
`_MODEL_ID`, `_MODEL_VERSION`, derived `_MODEL_KEY` for all three tiers,
the exact target endpoint/region and unchanged `EMBEDDING_DEPLOYMENT_NAME`.
Their actual `AZURE_AI_PROJECT_DEPLOYMENTS` CSV is checked by the shared
validator **before** conversion, then compared with required aliases,
unambiguous exact model/version coordinates, unchanged embedding coordinate
and previously configured unambiguous legacy keys. Shared coordinates across
distinct destinations are omitted; no speculative aliases are accepted.
The current baseline CSV may contain the known conflict; its individual raw
entries are validated and only unambiguous legacy keys retained in the candidate.
It is never accepted as a strict candidate CSV. The shared resolver additionally
checks all tier identities and simulation/live isolation.

## Executable synthetic example and limits

This builds labelled **synthetic** JSON from the test fixture into a new
repository-local scratch directory, then compares it. It does not collect or regenerate
any historical baseline:

```powershell
$example = Join-Path (Get-Location) '.feature041-example'
if (Test-Path $example) { throw 'Refusing to overwrite existing example directory' }
New-Item -ItemType Directory -Path $example | Out-Null
try {
    .\.venv\Scripts\python.exe -c "import json,sys; from pathlib import Path; from tests.contract.test_llm_deployment_configuration import synthetic_bundle; b=synthetic_bundle(shared=True); [(Path(sys.argv[1])/f'{k}.json').write_text(json.dumps(v),encoding='utf-8') for k,v in b.items()]" $example
    if ($LASTEXITCODE -ne 0) { throw 'Synthetic fixture generation failed' }
    .\.venv\Scripts\python.exe scripts\verify-llm-deployment-preflight.py --inventory "$example\inventory.json" --baseline "$example\baseline.json" --outputs "$example\outputs.json" --candidate "$example\candidate.json" --at 2040-01-01T12:00:00Z
    Write-Output "SYNTHETIC_PREFLIGHT_EXIT=$LASTEXITCODE"
} finally {
    Remove-Item -LiteralPath $example -Recurse -Force
}
```

The two-hour fixture age window and all 2040 times are synthetic, **not** an
approved production TTL. No real target readiness follows from exit 0.
Unit/contract tests execute subprocess boundaries, nonzero diagnostics and
file immutability; an audit-hook child also prohibits network, subprocess and
write operations during a passing CLI run.
Final checkpoint execution: **exit 0**, exact pass JSON above, synthetic example
directory removed. No target evidence was collected.

## P1 activation and rollback sequence (future, separately authorised)

1. Obtain scoped G0 collection/validation authority and current G1–G3 baseline,
   governance/inherited-policy and pinned AVM compatibility evidence. The CLI
   compares inventory/baseline/output/candidate only; it does **not** validate
   governance, AVM artifacts, What-If or rollback evidence. The approved policy
   must also define their observation windows, invalidation, bindings and
   refresh/reapproval decisions in the release evidence reviewed by G4.
2. Complete compatible provenance **readers before writers**. Validate absence
   semantics and unchanged historical bytes. Local T034–T044 reader-first
   implementation and request-bound fake-transport checks pass; deployed
   reader versions and target writer activation remain unverified.
3. After the separately unblocked IaC tasks, compare actual compiled outputs
   and parameters to the target baseline. Mandatory build/lint/PSRule,
   reviewed What-If, strict carve-out and target metadata checks remain.
   Require zero P1 creates/renames/replacements/deletions and zero changes to
   model/version/format/SKU/capacity/RAI/effective filters/upgrade policy,
   embedding or access/network/auth/diagnostics/residency controls.
4. Build corrected immutable **API and agents image + cleaned env pairs**,
   bind their config digest/image/compiled revisions, preflight both, and
   retain a verified compatible rollback pair. Strict images plus their
   cleaned env are **one activation unit**, not an env-only rollout or
   permissive fallback. Eval clients needing an omitted shared coordinate
   receive an explicitly selected, unambiguous per-run eval mapping.
5. Obtain G4 approval for the exact authorised canary/switch/promotion stages,
   window and candidate/rollback bindings. Before that, local acceptance is
   not permission to call real models or activate anything.
6. Under the approved stage authority, switch paired revisions, then repeat
   target identity/protection/freshness comparisons and chat/streaming/tool/
   citation/degradation/audit checks. Drift invalidates dependent evidence:
   stop promotion, follow approved refresh/reapproval and rollback decisions.
7. Roll back both image/config pairs to the last verified **corrected**
   compatible pair; never replay ambiguous CSV into a strict image. An old
   dispatcher may also be incompatible with omitted shared keys. If the only
   pre-P1 pair has unsafe simulation misrouting, leave simulation inference
   unavailable through existing operational controls. Never redirect it to
   reasoning/drafting capacity for availability.

## Acceptance levels and checkpoint

| Level | Required evidence | Current status |
| --- | --- | --- |
| Local implementation/procedure acceptance | Hermetic routing and synthetic offline CLI/rollout tests | Local only; commands/results in `verification.md` |
| Real target P1 release readiness | Approved current exact-target G1–G3 evidence, policy, compatible readers and paired candidates, actual compiled comparisons, reviewed What-If/carve-out/metadata and stage-scoped G4 | **BLOCKED**, not supplied; T024–T027/T030 untouched |
| Real P2 operational migration acceptance | Separately authorised G5a proposal/headroom/provisioning; G0 post-provision readiness; G5b traffic/switch/post-switch/forward-and-rollback verification with retained pairs | **BLOCKED**, not supplied; synthetic rehearsal cannot satisfy SC-006 |

G6 retirement remains a later independent decision. No optional P2 action is
required for P1, and no resource rename or replacement occurs in P1.
The original offline lane ended after T022/T023/T028/T029. Later local
authorisations and their results are recorded in verification.md; that
historical stop is not an outstanding instruction or release approval.

<a id="t052--human-review-handover-2026-10-19"></a>

## T052 — human review handover (2026-10-19)

**Decision requested, not issued:** independently review the local evidence,
the four unchanged adjacent test failures and the missing target items below.
Local T049–T052 completion records delivery of this handover, not satisfaction
of any external gate. **47/52 tasks recorded complete; T024–T027/T030 remain
unchecked and blocked. Feature completion, target P1 readiness and real
P2/SC-006 acceptance are not claimed.**

### Exact revision and cleaned configuration references

No real target image/config references were supplied or built. The following
are exact required evidence locations, **not fabricated deployment values**:

| Review object | Exact reference required in supplied evidence | Current target value / stop |
| --- | --- | --- |
| Candidate API | `candidate.services.api.image`, `.revision`, `.environment`; `candidate.bindings.api_image` | **NOT SUPPLIED**; immutable `sha256:<64 hex>` image and exact revision required |
| Candidate agents | `candidate.services.agents.image`, `.revision`, `.environment`; `candidate.bindings.agents_image` | **NOT SUPPLIED**; no old-dispatcher env-only compatibility assumption |
| Cleaned paired configuration | Complete `candidate.services.{api,agents}.environment`; `bindings.configuration_digest` in all four evidence files, using the canonical digest defined above | **NOT SUPPLIED**; raw CSV must pass strict validation before conversion |
| Compiled proposal and target binding | `bindings.compiled_proposal_revision`, common `target`, source revision, policy/version, timestamps, approvals and evaluated invalidation | **NOT SUPPLIED**; no compiled-output/parameter or target parity acceptance |
| Observed current pair | `inventory.snapshot.services.{api,agents}` exactly equal to `baseline.snapshot.services.{api,agents}` | **NOT SUPPLIED**; per-environment G1 approval required |
| Corrected rollback pair | Independently reviewed retained API/agents image digests, revision/environment snapshots and canonical paired config digest, bound to target/proposal/policy/window in the release record | **NOT SUPPLIED**; never infer safety from an old image tag |

All synthetic values in tests/tabletop are excluded from this target table.
These missing references are handover blockers to activation, not placeholders
an implementer may fill from dev observations or repository defaults.

### Reader/writer compatibility and safe rollback

- Local strict Pydantic/JSON readers and export/replay projections were changed
  and checked before new writers. Old rows/payload absence stays unavailable;
  required identity strings retain `unknown`, nullable wire values remain null.
  Actual deployed reader compatibility still requires independent review.
- The eligible owning inference writer admits **1/1/1/0/0** rows for
  true/succeeded, true/failed, true/unknown completion, false/not_attempted,
  null/unknown submission. Agent/event envelopes retain uncertainty without
  fabricated inference rows. Controller rounds are separate; API consumers
  do not duplicate the dispatcher writer.
- Strict routing and cleaned configuration activate together for **both**
  services. Never put a strict reader over an old conflicting CSV or apply
  cleaned env alone to an incompatible pre-P1 dispatcher. Old eval consumers
  requiring omitted shared coordinates need explicit unambiguous per-run maps.
- Retain the last verified **corrected** paired revisions and old resources.
  Rollback both images/configurations and reverify destination, model/version,
  protections, chat/SSE/tools/citations, degradation and provenance under
  separately recorded rollback authority. If only unsafe pre-P1 simulation
  rollback exists, keep simulation inference unavailable; never use live tiers.
  No rollback, switch or retirement was executed locally.

### Outstanding independent gates and stage-specific stops

| Gate / stage | Evidence and independent owner decision still required | STOP condition |
| --- | --- | --- |
| G0 collection / validation | Scoped target, approver, operations, credentials and window; validation scope specifically covers metadata, mandatory What-If and strict carve-out collection | No scoped authority, stale/unbound evidence or unevaluated invalidation: no collection/validation |
| G1 baseline | Platform owner reconciles each exact environment's existing deployment/model/version/format/SKU/capacity/RAI/effective filters/upgrade/access/network/auth/diagnostics/residency/embedding and running pairs | Missing approval or any unresolved drift: no target parameter selection or provisioning |
| G2 governance | Current feature-041 MD/JSON with inherited effects/property paths/required values and Portal parity, independently reviewed | Missing current target parity: no IaC authoring/build |
| G3 AVM | Independently reviewed published pinned consumable composition preserving existing parent, properties and child-operation serialization; explicit scope decision if wider work needed | Missing compatibility or proposed account rewrite: no IaC authoring/build |
| G4 P1 | Independent target metadata, generated ARM/PSRule, mandatory What-If and strict carve-out reviews, matched candidate/rollback references, freshness policy and human stage/window approval | No evidence or only local test/quality approval: no canary, activation, switch or promotion |
| G5a P2 provision | Independent target-bound unchanged-model/protection proposal, approved observation/retention criteria and actual-pool old+new allocations with margin, governance/What-If and provisioning window | No headroom/proposal approval: no replacements; actual replacement readiness is not invented before creation |
| G5b P2 traffic | After approved provisioning, G0-authorised actual parity/readiness; compatible paired candidates, retained corrected rollback pair; independent canary/switch/forward/rollback approvals and windows | Provision approval alone or missing actual readiness: no traffic; failed forward checks stop promotion and require approved rollback/reverification |
| Retention and G6 | Real observation and rollback evidence, no active revision/worker/eval/rollback dependencies, independent human deletion approval | Missing observation, remaining dependency or absent G6: retain old deployments/pairs; zero automatic deletion |

Approvals are candidate/target/stage specific. Changes to models, protections,
scope, policy, images/config or compiled proposal invalidate dependent evidence
under the approved policy; recollect/reapprove only with applicable authority.
No universal TTL, independent reviewer approval or release decision is supplied
by this handover. Local tests cannot satisfy real SC-005 or SC-006.

### Local result supplied to reviewers

Original T049–T052 checkpoint: 47 selectors, **1,255 passed / 4 unchanged
stale adjacent failures**, required population **1,137/1,137 passed**.
The subsequently approved E1/E2 corrective checkpoint supersedes the current
local implementation/quality result: **1,313 passed / the same 4 stale
failures**, 56 selectors; focused provenance **62 passed**. Ruff/format
**41 files**, configured mypy **39 plus one separate fixture**, original
fingerprints **50/50 unchanged**. The eight added cases and 50 additional
existing workflow/translation checks account for the expanded population.
Exact corrective commands and limitations:
[verification.md](verification.md#e1e2-provenance-remediation-2026-10-19).
Original commands and FR/SC crosswalk:
[verification.md](verification.md#final-local-cross-cutting-checkpoint--t049t052).
Reviewer-owned CHK markers and built-in checklist lifecycle remain unchanged;
[requirements-review.md](requirements-review.md#t050--post-implementation-re-evaluation-2026-10-19)
requests independent re-evaluation without issuing it.

E1 retains completed model evidence across local processing exceptions. E2
projects genuine request evidence through in-process workflow/model metadata
to timeline events; generated flags cannot assert inference, and false/unknown
submission remains suppressed. No public/domain reader or wire schema change
was needed: typed evidence is private to internal model subclasses and is not
serialised into recommendation/alert responses or persisted checkpoints.
Timeline records retain actual request identity/usage and failed/unknown
completion where observed, without duplicating strict owning-writer audit rows.
Both corrections now await **independent read-only re-verification**. This
handover supplies no independent verification, target readiness or new authority.
The existing 47/52 task markers and reviewer checklist bytes are unchanged;
T024–T027/T030 remain externally blocked.

**STOP after T052.** No Azure operations, real inference, infrastructure
authoring/build, target model/config changes, staging/commits, hooks/workflows
or automatic handoffs. Return this local evidence and blockers to the
orchestrator/human reviewer.
# Current preparation-only handover — 2026-10-19

The current user's preservation/pinned-child/immutable-candidate approval
authorised **local preparation only**. T024–T026 are implemented and actual
compiler contracts pass; T027 and T030 remain **partial/unchecked** because
staging/production baselines and approvals are absent. Earlier authoring-stop
entries below are historical for this bounded Dev work, not release clearance.

- Dev metadata was refreshed at `2026-10-19T13:13:17.862389Z`; all four exact
  existing model identities, capacities, SKUs, upgrades and RAI were preserved.
  All 50 direct/inherited access assignments, all 11 policy bindings and
  diagnostics matched original captures. Account/network/auth/identity and
  unhealthy current app revision/image metadata are in
  `evidence/dev-preparation/refresh.json`; full protection comparisons are
  in `protection-comparison.json`.
- The **one-hour maximum age at use** is the approved freshness policy.
  Refresh before What-If/activation; changed bindings require reconciliation
  and explicit reapproval. No fabricated valid-until field was added.
- The bounded compiled proposal is `deployments.template.json` plus
  `deployments.parameters.json` in that evidence directory. The parent is
  existing-only; no account recreation, resource rename, new model, capacity
  change, RAI weakening, network/auth/access redesign or embedding change is
  proposed. Four deployment calls use the unchanged pinned AVM child and the
  original fully serialized RAI/deployment chain.
- Local API and agents candidates are built from real current dirty source,
  not mutable hello-world placeholders. `app-source-bindings.json` records the
  build source hashes and base image digest; `candidate-bindings.json` records
  local immutable image IDs, identical complete LLM config, source/template
  bindings and successful network-isolated resolver checks.
  Local image IDs are **not verified ACR manifests**; no ACR publication occurred.
  Existing other environment/secretRefs must be retained; no secret values or
  complete secret-derived configuration digest was requested or invented.
  API build and network-isolated resolver smoke succeeded; the first agents
  build encountered a public dependency-download timeout/DNS failure.
  Independent DNS probes succeeded afterward and the unchanged build was
  retried once. That unchanged retry **succeeded, exit 0**; the successful
  preparation record at **2026-10-19T14:09:17.762034Z** binds both real local image
  candidates as complete. API:
  `sha256:5bbd6497c7c74c0aa8e11a67326c8bfffc1f68ca4c894b30344e4e8dbd6474cb`;
  agents:
  `sha256:2bee5de4feeb4794253f62d4769799c05a83debb0798120fab0b3bc8ffd3cd1f`.
  Both packaged-source hash and three-tier resolver checks passed without a
  network. No older image or live-health/rollback proof was substituted.
- **Do not deploy full `main.json` or run `azd up`.** Regeneration exposes
  pre-existing source/ARM drift outside this feature; exact inventory is in
  `main-inventory-review.json`. Full-main scope needs a separate decision.
- Existing API/agents active revisions remain **Unhealthy/ActivationFailed**;
  the user did not waive a healthy paired rollback gate. No live rollback
  images or readiness have been fabricated.

Actual local results: Bicep build/lint and explicit Dev parameter compilation
exit 0; **618** compiler/config/preflight contracts and **357** mocked
routing/provenance tests passed; explicit-Dev existing PSRule baseline reports
**797 Pass / zero Fail**. Full `infra/` PSRule stops on unpopulated old validation
parameters; no staging/production selections were guessed. See the current
`verification.md` addendum and raw logs for qualifications/warnings.

Local-only build commands (repository root, no remote builder or push):

```powershell
docker build --platform linux/amd64 --pull=false -f apps\api\Dockerfile -t ama041-api:preparation .
docker build --platform linux/amd64 --pull=false -f apps\agents\Dockerfile --target dispatcher-runtime -t ama041-agents:preparation .
.\.venv\Scripts\python.exe specs\041-llm-deployment-routing\evidence\dev-preparation\prepare.py
```

The source manifest/base digest must match before reusing these bindings.
Docker tags are just local build handles; use the recorded immutable IDs for
local checks. Dependencies are resolved by the existing Dockerfiles, not changed
by this task; observed installed versions are captured alongside build logs.
Rebuilding can produce a different image ID and requires a new reviewed binding.

**Next gate, not executed:** parent reviews immutable source/image/config/
template bindings and requests separately scoped approval for fresh metadata
and a Dev-only bounded What-If against the existing account/RG. Changed
bindings require reconciliation/reapproval. Publication, paired application
release with healthy rollback, inference and activation require their own
explicit authorisation. **No What-If, deployment, push, remote cloud build,
inference, permission change, secret request, commit, hook or workflow ran.**

## Bounded Dev preview checkpoint - 2026-10-19 21:57 UTC

This checkpoint supersedes the previous "What-If not executed" state only.
The user approved the exact bounded Foundry preview and renewed its expired G0
window for two hours. `evidence/dev-preparation/validation-approval.json` records
a conservative executable interval ending 23:43:19 UTC; it grants no release,
image publication, inference, permission change or traffic authority.

Fresh target/protection/revision evidence at 21:51 UTC matches the original
candidate baseline. All 11 effective assignment bindings and all 27 relevant
policy/initiative semantics are unchanged. The application pair is still unhealthy.
The exact approved template and parameter hashes are unchanged.

ARM validation passed and the actual bounded What-If succeeded. Machine JSON
reports **eight Modify, 45 Ignore, zero resource creates/deletes**. The validation
helper's console counters include nested property lines and are not a resource
inventory. `validation-what-if.json` and hashed `validation-review.json` are
authoritative, not the helper's apparent overall PASS.

The preservation review remains **BLOCKED**:

- Four deployment deltas omit returned `currentCapacity` and `deploymentState`;
  no model/version/SKU/capacity/RAI/upgrade input change was returned. Do not
  automatically exempt the returned-field omissions without provider verification.
- Diagnostics omit three existing disabled log categories and zero-day retention
  fields. Preservation reconciliation is still required.
- Three RAI deltas omit returned `contentFilters.action=NONE`. The documented
  2024-10-01 input shape has no action member; API projection/default semantics
  must be established rather than assuming a harmless safety-policy difference.
- The existing strict carve-out script against this real JSON fails, exit 4,
  for all four exact deployment names. The registry contains old model-name rows
  and no gpt-5.4 row. Dual-review evidence must be genuine; neither a second
  reviewer nor a new approval date has been fabricated, and the gate is unchanged.

No cloud resources were mutated, no images published, no inference or traffic
changes performed, and no commit created. Local implementation remains 50/52
tasks complete; T027/T030 are partial for missing staging/production acceptance.
Registry manifest digests, complete preserved configuration binding, a healthy
corrected rollback/bootstrap pair and separate G4 authority are still absent.
The full root template remains prohibited.

## Local-only preservation remediation after preview

The user selected **"Continue local remediation only; keep deployment blocked"**.
The accompanying approval-evidence response supplied no review reference; no
registry approval, reviewer identity, gate exemption or release authority is
inferred from it.

Fixed the proved diagnostic omission locally: an optional approved snapshot
passes through the root and child module, and both explicit Dev parameter
surfaces retain all five observed log categories, enabled/disabled values,
zero-day disabled retention and the observed AllMetrics entry. Other environments
retain the old module defaults unless they explicitly supply their own snapshot.
No guessed staging/production settings or RAI action/API changes were added.

The actual compiler regression failed before the fix on missing retention and
disabled categories. After the fix, **48 compiled/configuration tests passed**,
including full snapshot equality and explicit-empty versus omitted-field cases.
Root/module Bicep build/lint and focused Python lint/format passed.
The actual explicit-Dev PSRule baseline returned **797 Pass / zero Fail**.
The existing Bicep path and 60-second timeout needed explicit process-local
PSRule configuration; no tooling was installed and no rule/exemption was changed.

New candidate files are `diagnostics-reconciled.template.json` and
`diagnostics-reconciled.parameters.json`, bound in
`diagnostics-remediation-bindings.json`. They are distinct from the original
approved preview files, which remain unchanged and retained as historical evidence.
Application packaged source and LLM CSV remain unchanged; the two local image
IDs remain available. The changed IaC bindings invalidate reuse of the old
What-If for the corrected candidate and require reapproval before a new preview.

**No further Azure calls followed the local-only decision.** The diagnostic
proposal is locally corrected, not live-applied or re-previewed. RAI action and
deployment-returned-field differences, real strict carve-out approval failure,
registry publication, complete configuration/rollback evidence and G4 remain
unresolved. Deployment remains blocked as requested.

## Renewed Dev deployment request - corrected live preview

The user subsequently requested **"deploy to dev"**, then approved **fresh
validation of the corrected bounded candidate; keep release gates enforced**.
No dual-review approval reference was supplied. The new approval is bound in
`corrected-validation-approval.json`; it does not waive missing release evidence.
The renewed checks below supersede the preceding local-only stop for this
specific validation stage, not for activation.

Fresh evidence at **2026-10-19T22:35:42.590688Z** matches all target/account/model/
RAI/diagnostic/policy/RBAC/application identity and configuration observations.
All **27** relevant policy/initiative semantic comparisons pass.
ARM validation and the corrected What-If operation succeeded. Actual resource
counts are **7 Modify / 1 NoChange / 45 Ignore / zero Create/Delete**.
`openai-diagnostics` is **NoChange**: the preservation correction is now verified
against the live target rather than only compared locally.

Release still **BLOCKED**. The actual strict carve-out fails, exit 4, on all
four exact Dev names; no approval identities, approval date or exception were
invented. Four deployments still omit currentCapacity/deploymentState, and
three RAI policies omit returned action=NONE. The exact 2026-05-01 deployment
input reference exposes both capacity and Running/Paused state inputs, so
read-only-noise clearance is not justified. The unchanged pinned AVM child
does not expose them. The RAI API/casing/default mismatch is also unresolved.

The raw JSON, every remaining delta, authoritative documentation references
and evidence hashes are in `corrected-validation-review.json`. All original
preview hashes remain valid; distinct output paths preserve prior evidence.
No images were published, resources deployed, inference performed, traffic or
permissions changed, or commits created. Configuration/healthy rollback
evidence, genuine carve-out review and later G4 remain required.

## Carve-out identity matching corrected

The user requested rectification of the registry check. The script now matches
the proposed resource's `after.properties.model.name` to registry `model_name`,
not the alias extracted from its resource ID. A missing proposed identity fails
closed without an alias or old-model fallback. Ignore/Delete changes are skipped
by this model-approval check, not authorised for execution. Proposed non-AU
locations are checked at both root and `after.location`. Registry metadata and
approval requirements are unchanged; schema/help clarify the model identifier.

An **offline replay**, not a fresh Azure call, of the unchanged corrected real
preview now accepts `text-embedding-3-large-dev` through its registered model.
The remaining three failures correctly identify underlying **gpt-5.4** for
reasoning/drafting/simulation. No gpt-5.4 approval record exists in the checked
registries, and no older model's reviewers/date were copied onto a new model.
Raw output and hashed script/registry/preview bindings are retained in
`evidence/dev-preparation/model-identity-carveout-replay.*`.

All ten new regression cases pass. The combined related run reports **27 passed /
one unchanged baseline failure**: the old security positive fixture uses a
non-AU region and 2030 review date, both rejected before this change. No
unrelated fixture was changed. PowerShell parser and focused Python lint/format
checks pass. Remaining preservation, registry approval and paired release gates
stay blocked. No Azure read/write, image push, inference or deployment occurred.

## Project-lead-authorised quorum exception — 2026-10-20

The user explicitly instructed: **"You are ordered to skip the second approver
requirement."** On the scope/deadline form the user selected **All environments**
and **2030-11-20**. This supersedes the additional-approver prerequisite only,
not model review, data-residency, preservation, freshness, rollout or rollback
controls. `quorum_waiver` records scope, sole authoriser `johnbilliris`, approval
reference and inclusive UTC expiry. Normal prod/dev quorum settings remain in
place for expiry/removal; no fictitious second identity was added.

`gpt-5.4` is now registered for **Dev** with the one genuine approver, both
data-protection flags and Australia East placement. Its model review deadline
is **2027-04-08**, aligned with the existing registry review cycle; the 2030
waiver deadline does not extend any model review window. The waiver's all-
environment scope does not supply staging/production deployment evidence or
authorise model changes there. GlobalStandard AU-only inference is not asserted.

PowerShell, both runtime/design schemas and OPA now recognise the exception.
The focused run reports **64 passed / the same one pre-existing invalid positive
security fixture failure**. The schema and runtime regressions exercise normal
quorum restoration, each environment, missing/invalid/expired waivers, and
unchanged model-region/review/flag/identity controls. Actual OPA 0.70.0 evaluation
was used, not just the existing Python fallback.

Strict **offline replay** against the unchanged corrected real Dev What-If
returns **0**; the whole registry also has an empty OPA deny set. Advancing OPA's
evaluation clock past **2030-11-20 UTC** denies the expired waiver and the single-
approver model. New immutable evidence/logs:
`evidence/dev-preparation/single-approver-waiver-replay.*`.
Prior captured live evidence is unchanged. Release remains **BLOCKED** by
preservation, fresh authorised evidence/reconciled bindings, publication/config/
rollback readiness and stage-specific approval. No Azure operation occurred.
