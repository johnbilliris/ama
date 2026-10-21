# Quickstart Validation: LLM Deployment Routing

> Local cross-cutting checkpoint T049–T052 | 2026-10-19

## Scope and prerequisites

This is a local validation guide, not a deployment script or release approval.
Local story implementation is present; infrastructure tasks
T024–T027/T030 remain blocked on G1–G3. Run tests with injected fakes and
no Azure inference. Use Python >=3.12, the repository's existing uv environment,
PowerShell 7, and existing pytest dependencies. Do not install/upgrade SDKs or
change Azure/azd configuration for this plan.

From the repository root:

```powershell
Set-Location C:\code\ama
uv run --no-sync python --version
git --no-pager status --short
```

If the environment is absent, follow the repository's approved developer setup
separately. Do not use a planning validation failure to trigger deployments.

Contract references:
- [Routing configuration](contracts/routing-configuration.md)
- [Inference provenance](contracts/inference-provenance.md)
- [Preflight and rollout](contracts/rollout-and-preflight.md)
- [Entities and state transitions](data-model.md)

## 1. Final local result and existing regressions

```powershell
.\.venv\Scripts\python.exe -m pytest tests\contract\test_foundry_chat_client_aoai.py -q -p no:cacheprovider
```

The planning **10 passed** is historical, not current feature acceptance.
First-write-wins expectations have been replaced with strict conflict checks.
The final **47-selector union** in
[verification.md](verification.md#final-local-cross-cutting-checkpoint--t049t052)
ran **1,259 cases: 1,255 passed, 4 failed**, exit 1, 98.17 seconds.
The four failures are unchanged stale audit-type expectations in
`apps\api\tests\test_audit_schemas_19_types.py` (26 HEAD types versus 24 expected
and two missing examples). They were not repaired or hidden. Required local
routing/provenance/preflight/migration and original regressions account for
**1,137 passing cases**; adjacent regressions add 118 passes and those four
failures. No full-repository pass or release readiness is claimed.

Additional existing regression groups for implementation validation:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\contract\test_foundry_chat_client.py tests\contract\test_foundry_gateway_fail_closed.py tests\contract\test_llm_model_routing.py tests\contract\test_llm_fallback.py tests\contract\test_llm_logging.py -q
.\.venv\Scripts\python.exe -m pytest tests\contract\test_audit_record_shape.py tests\contract\test_audit_record_amend_loop_fields.py tests\contract\test_simulation_api_contract.py -q
```

These selectors passed within the final union, including the explicitly
corrected routing/error outcomes. Existing chat/SSE/simulation/tool, embedding,
eval, replay/export and telemetry selectors are enumerated in verification.md.
The isolated audit-snapshot collector still needs the established test bootstrap:
production-auth route imports are not independently collectable in that helper.
It passes in the recorded consolidated process; no auth guard was weakened.

## 2. Focused regression acceptance (offline only)

The following files now exist. These are convenient focused rerun commands;
the final checkpoint executed their union with the identified regressions once,
not each convenience command separately.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_llm_deployment_routing.py tests\contract\test_llm_deployment_routing.py tests\integration\test_llm_deployment_routing.py -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest tests\contract\test_llm_deployment_provenance_schema.py tests\unit\test_llm_inference_attempt_evidence.py tests\contract\test_llm_deployment_provenance.py tests\unit\test_llm_provenance_admission.py tests\integration\test_llm_deployment_provenance.py -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest tests\unit\test_llm_deployment_migration_preflight.py tests\unit\test_llm_deployment_preflight.py tests\contract\test_llm_deployment_configuration.py -q -p no:cacheprovider
```

Use synthetic endpoints, credential fakes, SDK spies and HTTP mock transports.
Clear inherited AZURE_AI/AZURE_OPENAI settings in fixtures. Do not export the
synthetic settings globally or invoke a live model.

| Scenario | Required expected result |
| --- | --- |
| Three distinct destinations share model/version; six CSV orderings | Every inventoried production chat path reaches its designated tier; no first/last-write selection |
| Explicit reasoning/drafting, no CSV tier aliases | Both MAF factories and common clients resolve; no ValueError from alias lookup |
| Explicit tier conflicts with otherwise valid map destination | Explicit tier wins |
| Explicit A, new identity absent, unique legacy coordinate maps to B | Route A; model metadata unavailable, not B's identity; matching A association may supply metadata; wrong-account proof rejected |
| Same raw key names two destinations | Actionable error names key and both destinations; zero SDK calls in every ordering |
| Duplicate equal pair | Idempotent, same destination |
| Malformed entry, empty key/value, unsupported tier, partial metadata | Required-path error before SDK call; unrelated paths need not stop |
| Controller and every dispatcher role, simulation key same as reasoning | Explicit simulation destination only |
| Missing/empty simulation explicit setting with legacy reasoning/simulation keys present | Configuration error/degraded evidence, zero inference and zero live-tier fallback |
| Explicit simulation equals effective live-tier deployment | Isolation validation fails before SDK dispatch, including alias/exact/base live paths with no explicit live env and mixed explicit/legacy live tiers; distinct destinations pass |
| Unambiguous legacy exact/base model keys | Supported non-simulation/eval lookup remains compatible |
| Embedding compatibility | Ingest lookup and direct query deployment/dimensions unchanged |
| Valid sync, streaming, MAF and dispatcher inference | Separate correct model_id, version and deployment; actual usage |
| Submitted-request timeout/4xx/5xx/partial stream | Attempt true, failed outcome, no success fabrication |
| Proved remote submission, completion/terminal failure evidence unavailable | true/unknown; one eligible inference row at owning writer, no fabricated completion/usage |
| Config/gateway/client/local SDK validation failure or template before request | No inference-call row; false/not_attempted and unavailable invoked-deployment fields |
| SDK method entered but submission evidence unavailable | null/unknown; zero inference rows/projections; retain uncertainty in existing agent/event envelope and correlate transport evidence |
| Post-call safety fallback / empty completion | Retain real attempt evidence and actual usage, not a fabricated no-call result |
| HTTP loss/timeout to dispatcher | API marks unknown, not false/no-call or a guessed deployment |
| Controller no-RAG, tool loop and later-round failure | Per-request evidence and existing opt-out/RAG rules; earlier requests not lost |
| Historical/new audit rows and old dispatcher payloads | Both readable; absent status unavailable; historical fixtures byte-identical |
| Chat/SSE/tools/citations/tenant isolation | Existing flow contracts preserved; only specified routing/error changes |
| Writer admission matrix under existing audit eligibility | Per-call counts true/succeeded=1, true/failed=1, true/unknown completion=1, false/not_attempted=0, null/unknown submission=0; two controller rounds total 1 if second submission unknown, 2 if both proved; no outer-layer duplicate |
| Offline freshness/invalidation fixtures | Missing/unapproved policy, wrong target/config/image/proposal binding, expired policy window or invalidating change without refresh fail closed; approved policy/current exact bindings pass; no assumed universal TTL |

The integration group is hermetic: exercise dispatcher via ASGI transport and
the controller with fake completion streaming/tool replies. Assert at the
actual SDK request arguments, not only the resolver return value. Stub MAF
client construction and its request boundary; factory-only success is not
enough. Inventory-to-test coverage must be complete for SC-001 percentages.

Actual local results: **168/168** named caller/order cells (C01–C23/A01–A05),
**112/112** focused provenance cases, **315/315** preflight/configuration/
migration cases (including 144 migration cases), and **50/50** original raw-byte
historical anchors unchanged. These populations overlap the final union; do
not add them to its total or represent synthetic records as production samples.
The earlier **15/15** named migration tabletop outcomes remain synthetic.

## 3. Exact offline preflight interface

```powershell
.\.venv\Scripts\python.exe scripts\verify-llm-deployment-preflight.py --help
```

Four required local JSON files are `--inventory`, `--baseline`, `--outputs`,
`--candidate`. Optional paired `--migration` and `--stage` compare P2 evidence;
stages are `provision`, `canary`, `switch`, `forward`, `rollback`, `retain`,
`retire`. No stage executes its named operation. `--at` is synthetic-only;
omit it for authorised real evidence so current UTC applies. Exit 0 is a
supplied-evidence comparison, 1 an evidence blocker, 2 usage error.

The exact project-local synthetic example in
[rollout-evidence.md](rollout-evidence.md#executable-synthetic-example-and-limits)
was run at this checkpoint: exit **0**, stdout
`{"status": "pass", "scope": "local supplied-evidence comparison only", "target_readiness": "not established"}`.
Inputs were created only under the repository and removed afterwards; the
checker itself writes no files. Fixture clocks, approvers, images and quota
claims do not authenticate a real approval or establish readiness.

For scoped Ruff/format/mypy and the final selector union, use the exact command
blocks in verification.md. Ruff and format passed **40 touched Python files**;
configured mypy passed **38 files plus one separately checked fixture**.
The known mixed-import legacy routing module is not a mypy target.
Repository test overrides apply; this is not an unqualified strict typing
claim. No Markdown lint executable/root lint script is installed; none was
downloaded. CRLF-aware whitespace and local evidence links are checked.

## 4. Infrastructure validation (blocked; not executed)

Before any Bicep edit or build, satisfy G1–G3 in the release contract. Azure
baseline/governance reads require recorded scoped G0 collection authority,
not an already approved baseline. After G1–G3/local candidate review, target
metadata reads, What-If and carve-out validation require an explicit G0
validation scope to collect G4 evidence, not G4 approval in advance.
Canary/activation/switch/promotion require later G4 stage authorisation.
Credentials alone confer none of these permissions. These gates are **not
cleared by this refinement**.

After authorised implementation, local examples:

```powershell
az bicep lint --file infra/main.bicep
az bicep build --file infra/main.bicep --outfile infra/main.json
git --no-pager diff -- infra/main.bicep infra/main.json infra/modules/azure-openai.bicep infra/parameters
```

Use the installed approved Bicep toolchain; do not trigger tool installation
or azd provisioning. Regenerate any other affected checked-in ARM artifacts
through the same compiler. Review generated JSON rather than editing it.

Expected: all nine selections passed through; per-tier metadata consistent;
collision-free map preserves embedding. Compare each target's parameter/output
fixture with its approved baseline. Zero deployment-name/model/version/SKU/
capacity/RAI/access changes in P1.

Execute the existing CI/CD What-If and carve-out gates only in a separately
authorised target session. Require zero unexpected deployment creates,
replacements or deletions, current inherited-policy compliance and verified
Azure model properties. Unknown/mismatch means STOP, not a successful check.
Require an approved target freshness/invalidation policy/version, timestamps
and target/config/image/compiled-proposal bindings for each evidence item.
Missing policy/binding or invalidated/stale evidence means STOP; do not invent
a TTL or count a formerly approved baseline as indefinitely valid. Follow
the release contract's refresh/reapproval rules under scoped G0 authority.

## 5. Controlled rollout and opt-in migration rehearsal

Use [the rollout contract](contracts/rollout-and-preflight.md) in order:

1. Verify the exact matched candidate image/environment pair before switching.
2. Demonstrate P1 routing and audit with existing resource identities.
3. Prove rollback restores a compatible safe pair, never ambiguous CSV under a
   strict image or simulation inference through a known unsafe old dispatcher.
4. Locally rehearse P2 branches with synthetic evidence, clearly labelled as
   procedure verification only. For separately approved **real P2** only,
   collect actual replacement headroom/readiness, model/protection equivalence,
   traffic switch, failed-check rollback and post-rollback verification.
   Synthetic rehearsal cannot satisfy SC-006 operational acceptance.
5. Confirm old resources remain and no retirement occurs without another
   recorded approval.

**Never activate strict routing readers against old ambiguous maps, or update
only environment settings on an incompatible old dispatcher.** API and agents
must each use a corrected immutable image plus its reviewed cleaned environment
as a matched activation/rollback unit. Deployed compatibility has not been
verified merely because local reader-first changes pass.

Do not execute provisioning, traffic switching, inference or retirement from
this guide. The exact target candidate/rollback image digests, revisions and
configuration digests are **not supplied**, as recorded in the handover in
rollout-evidence.md. G0 collection/validation, G1–G3, G4 stages, G5a/G5b and
G6 remain independent. Capture future evidence by FR/SC ID without secrets,
prompts or tenant PII.

## Completion criteria

| Level | Required evidence / boundary |
| --- | --- |
| Local implementation/procedure verification | Hermetic routing/provenance/preflight regressions, historical-byte preservation and synthetic P2 branch coverage. Target gates may remain blocked; label affected FR/SC acceptance pending, not passed. |
| Target P1 release readiness | Current exact-target/revision evidence under the approved freshness policy, G1–G3, reader-first compatibility, reviewed What-If/carve-out/metadata validation and G4 stage approvals. No implication that activation happened or is authorised beyond the recorded stages. |
| Real P2 operational migration acceptance | Independent G5 approval and actual replacement readiness, traffic switch, forward and rollback verification with unchanged models and chat/streaming contracts; this is SC-006 evidence. Synthetic/local tests are insufficient. Retention and G6 retirement approval remain distinct. |

Report coverage of FR-001–FR-016/SC-001–SC-007 against these levels; do not
claim all acceptance passed while real P2 or target evidence is pending.
P1 may retain old explicit names without opting into P2. This checkpoint
completes **47/52 local task records**, not the feature or a deployment:
T024–T027/T030 stay unchecked and externally blocked. Return the evidence to
human review; no automatic handoff or operational authority is conferred.
