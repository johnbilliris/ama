# Feature 041 — G3 pinned AVM child compatibility

## Current approved first-party exception - 2026-10-20 07:07 UTC

The user explicitly selected **`approve raw bicep`** for the narrow preservation
composition and Dev validation scope recorded in
`evidence/dev-preparation/convergence-implementation-approval.json`.
No reviewed compatible AVM child exposes both required operating-state inputs.
The wrapper now calls the **first-party**
`infra/modules/cognitive-services-deployment-preservation.bicep`, not the
unchanged vendor. This is not a newly pinned, separately published or certified
AVM. The retained 0.18.0 source/license hashes remain unchanged and verified.

The child references an existing account and emits exactly one deployment at
`2026-05-01`, with explicit model/version, SKU/capacity, RAI attachment, upgrade
behavior, `currentCapacity` and `deploymentState`. Root/wrapper/Dev inputs are
required and typed for all four deployments. The separately approved RAI API
representation preserves exact observed `NONE` actions, complete filters,
mode/base and operation serialization; it does not infer `None` equivalence.
Only API-type-bundle availability warnings are narrowly suppressed.

Actual compiler/configuration contracts pass 60 cases. The fresh Dev baseline
and effective governance/access comparisons pass; actual ARM validation and
the exact bounded What-If succeed with all four deployments, all three custom
policies and diagnostics **NoChange**, identical before/after payloads and no
unsupported/potential changes. Parent/unrelated resources are Ignore. This
resolves T054/T055 for the approved Dev candidate without resource mutation.
It does not accept staging/production, all-target/full-root infrastructure,
release, inference or deployment. See `verification.md` and
`evidence/dev-preparation/convergence-preservation-review.json`.

The remainder is the **historical pinned-child research** and previous stop
conditions. Its prior consumption recommendation is superseded only by the
explicit exception above; its publication/hash findings remain intact.

> **Historical pre-approval T054 review - 2026-10-20:** The public registry now also lists account
> versions 0.19.0/0.19.1. Their tagged deployment-child interfaces at commits
> `55c62d45eaf6675c09bf663616c3e7fdd8c4560f` and
> `f1f4ba28698437d9a683d68bf181341ad3547e48` still expose neither
> `currentCapacity` nor `deploymentState`. A newer version alone therefore
> does not establish a compatible preservation path. No replacement OCI
> archive verification, new pin, vendor edit, account rewrite or infrastructure
> build/deployment was performed. T054 remains blocked on supported preservation
> or approved exact-API equivalence and the applicable target/scope gates.
> T055 likewise retains its unresolved complete RAI action semantics. See the
> current T053-T057 checkpoint in `verification.md`.

> **Operational update - 2026-10-19 22:40 UTC:** The interface/publication finding
> below is historical and does not clear live preservation. The newly approved
> corrected What-If still omits `properties.currentCapacity` and
> `properties.deploymentState` for all four deployments. The exact
> [2026-05-01 input reference](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/2026-05-01/accounts/deployments)
> exposes both fields; deploymentState controls Running/Paused inference
> availability. They must not be dismissed as proven read-only fields. This
> unchanged pinned child exposes neither input. Operational G3 preservation
> remains BLOCKED pending verified safe handling or a separately approved
> compatible composition. No upstream edits, raw-resource substitute, different
> pin or account-root deployment were made. Evidence:
> `evidence/dev-preparation/corrected-validation-review.json`.

**Verdict: G3 COMPATIBLE for the bounded, unchanged upstream deployment-child
composition below.** This is a public-artifact/interface compatibility finding,
not independent gate acceptance, a compiled candidate, live preservation
verification, or permission to author/build/execute infrastructure in this run.
Research completed on **2026-10-19**, with selected public captures at
**13:02:21Z–13:02:27Z**.

Approved scope supplied to this research: **“Approve — preserve live baseline;
use a verifiably pinned AVM child if compatible; prepare immutable application
candidates”.** No account rewrite, hand-authored deployment-resource substitute,
or raw-resource exception is required by this composition. No IaC was authored
or built; no Azure resource operation, What-If, inference, dependency install,
application build, or commit was performed.

## Publication, immutable pin and provenance

The selected parent publication is
`br/public:avm/res/cognitive-services/account:0.18.0`. **Do not consume that root
module**: it declares the account and unrelated children/defaults. Instead,
consume its unchanged, self-contained deployment child locally.

| Binding | Verified value |
| --- | --- |
| OCI repository | `mcr.microsoft.com/bicep/avm/res/cognitive-services/account` |
| Published parent version | `0.18.0` |
| OCI manifest SHA256 | `46982b96fd9dd36089aaa6b6b440562d9a8ba0fc60b3002222201f630d8695b9` |
| Compiled root layer SHA256 | `78c8c1899a3a408a96a94b625d79164efcbba3d7f95d99bdc23c20b23d089976` |
| Source archive layer SHA256 | `dffcff2af477628e3ede3df9d3c76aa6ac7b143c6dc479a97caf6dae6e02c9ed` |
| Upstream Git tag | `avm/res/cognitive-services/account/0.18.0` |
| Resolved commit | `f1070229a704c42897f07bdc19913cba26895bae` |
| Upstream child path | `avm/res/cognitive-services/account/deployment/main.bicep` |
| Archive child path | `files/deployment/main.bicep` |
| Child raw-byte SHA256 | `a0d007d0f61a143949c0d0acb771f59c9bc96f72db4d952fc03dc8a4d1834aa1` |
| Child source bytes | `1755`; archive source and commit-addressed source are byte-identical |
| License | MIT; Microsoft Corporation copyright; full notice must accompany redistribution |
| Commit LICENSE SHA256 | `c2cfccb812fe482101a8f04597dfc5a9991a6b2748266c47ac91b6a5aae15383` |
| Compiled child extraction SHA256 | `3afc13d3e759487c5dc6713aaf5b774b1b56beb6e7d53738d94816bbce949988` |

The manifest digest equals the registry's `Docker-Content-Digest`. Both layer
byte hashes equal their manifest descriptors. The manifest documentation
annotation names the same upstream tag. The published root source differs
from the commit root source only in the telemetry version placeholder
`-..--..-` being replaced by `0.18.0`; the **child has no difference**.
These are content/provenance checks, not a claim of signature verification.

The exact standalone child registry repository's `tags/list` returned **404**
at **13:02:27Z**. A separately published
`br/public:avm/res/cognitive-services/account/deployment:<version>` is therefore
**not established and must not be invented**. The consumable publication is
the child included in the verified parent OCI source/template layers.

Previously considered parent **0.9.2 is unsuitable for this child-only route**:
its published root declares deployment resources inline; its source archive
does not contain `deployment/main.bicep`, and the child at its resolved commit
`86ca03b043a56974b4b8dbe5e5efe3e834c6ac00` returns 404. Current `main` is not used
as evidence for either release.

## Exact consumption boundary

Preferred future implementation: vendor **only the exact 1755-byte child
source** from the pinned commit, with the complete pinned MIT notice and a
provenance/hash record. Do not edit it, regenerate a lookalike resource, vendor
the parent as a substitute, or fetch mutable `main`. No imports or subordinate
module declarations are needed by this child. The local module's provenance
is tied to the **published** source layer, not merely source availability.

This is reuse of the published AVM implementation under the user's express
pinned-child approval, **not a claim that a local copy is a separately
published/independently certified AVM registry module**. It does not grant a
raw-resource exemption or approval to modify upstream resource bodies. If
project acceptance requires a standalone registry address instead of unchanged
vendoring, G3 must remain blocked for that additional distribution constraint;
the 404 cannot be bypassed by substituting the account root.

An alternative, without reauthoring resource bodies, is to extract the
published compiled child object at JSON pointer
`/resources/cognitiveService_deployments/properties/template`. The recorded
extraction serialization is UTF-8
`json.dumps(child, sort_keys=True, separators=(',', ':')) + '\n'`.
The evidence copy ends in `.json.txt` and is **not wired into production**.
[Microsoft Learn — Bicep modules](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/modules)
explicitly supports local Bicep and ARM JSON modules and explicit inter-module
dependencies. Prefer unchanged source vendoring; this alternative is not
permission to hand-extract/rewrite only selected resource properties.

## Existing-parent and preservation contract

The child declares `Microsoft.CognitiveServices/accounts@2025-06-01`
**existing**, receiving `accountName`. Its only writable resource is
`Microsoft.CognitiveServices/accounts/deployments@2026-05-01`.
The compiled child confirms that account `existing: true` and contains no
account write, telemetry deployment, identity, RBAC, network, diagnostic,
private-endpoint, RAI-policy, or unrelated-resource write.

| Preservation surface | Required future binding / constraint |
| --- | --- |
| Parent and scope | Pass actual ARM name `cog-dev-w3uq6w`, not endpoint label `dev-aif-w3uq6w`; execute child modules only in subscription `74a25c57-d6e4-446e-8c99-7f5ace60011b`, RG `ama`. No parent creation/migration. |
| Reasoning | Name `gpt-5.4-dev`; model `{format: OpenAI, name: gpt-5.4, version: 2026-03-05}`; SKU `GlobalStandard`, capacity `30`; policy `reasoning-em-domain-dev`. |
| Drafting | Name `gpt-5.4-mini-dev`; the same actual `gpt-5.4` model/version; SKU `GlobalStandard`, capacity `60`; policy `drafting-em-domain-dev`. Do not infer another model from `mini`. |
| Simulation | Name `gpt-5.4-sim-dev`; same actual model/version; SKU `GlobalStandard`, capacity `20`; policy `sim-em-domain-dev`. |
| Embedding | Name `text-embedding-3-large-dev`; model `{format: OpenAI, name: text-embedding-3-large, version: 1}`; SKU `Standard`, capacity `60`; explicitly attach `Microsoft.DefaultV2`. No dimensions inference/change. |
| Upgrade behavior | Explicitly pass `OnceNewDefaultVersionAvailable` to all four; never leave the nullable upstream input omitted. |
| Upstream defaults | Override the entire SKU input for every call; upstream defaults `Standard/1` are not approved substitutions. Pass model version and RAI name explicitly. |
| Effective RAI content | Child only references the policy name. Retain existing custom policy definitions, Blocking mode, DefaultV2 base and observed filters unchanged; do not replace policies using the account root or infer filters from comments. |
| Access, endpoint, residency | Child has no controls that rewrite account identity, local auth, network, endpoint, tags, RBAC or diagnostic settings. Keep these surrounding resources unchanged; GlobalStandard remains GlobalStandard, not an assertion of AU-only inference. |

The table binds interface capability to the supplied approved preservation
scope; it does **not** refresh the earlier live observations. Evidence age at
future use must meet the approved **one-hour maximum**. Changed candidate
bindings require explicit reconciliation/reapproval, and evidence must be
refreshed immediately before What-If and activation.

## Serialization and outputs

Preserve the full existing operation chain in the future outer composition:

`reasoning RAI → reasoning child module → drafting RAI → drafting child module
→ simulation RAI → simulation child module → embedding child module`.

Use module completion/output references and explicit dependencies where needed
to retain **both** RAI/deployment and deployment/deployment barriers. Existing
parent declaration and literal policy names alone do not create these barriers.
The root publication uses `copy.mode=serial, batchSize=1` for deployment
modules, but extracting/vendoring the child **does not inherit that loop**.
Do not parallelize four standalone calls or permit overlapping target runs.
Leave existing RAI definitions untouched rather than widening this adoption
into RAI/account refactoring.

Verified child outputs are **`name`, `resourceId`, `resourceGroupName`**, all
strings. There is no `resourceName`, endpoint, principal ID or model-identity
output. The outer wrapper can preserve its existing public outputs using these
three values plus independently approved configuration; do not invent upstream
outputs or use them as live model-verification evidence.

## Boundaries and stop

- The selected child writes API **2026-05-01**, unlike the repository's
  **2024-10-01** child resources. Upstream explicitly suppresses BCP081; model
  and SKU derived types reference **2025-06-01**. These facts are retained,
  not “fixed” by modifying upstream. Publication proves an available compiled
  contract, **not** target RP API support, identical server-side behavior,
  successful no-op deployment, or a successful local compiler run.
- After separately cleared G1/G2/G3 acceptance, any later authorised local
  work must verify supported Bicep tooling, generated ARM, exact property/
  resource preservation, PSRule, and target API/metadata compatibility.
  Unexpected behavior or a need to change upstream code stops that route.
  What-If and activation require their own fresh, approved evidence/scope.
- Governance MD/JSON were read; complete G2 discovery is not G2 acceptance or
  resource compliance. Nothing in this finding waives inherited constraints.
- Unhealthy placeholder application revisions are not a safe rollback pair.
  Immutable application/configuration bindings and G4 remain pending.
- T024–T027/T030 remain untouched; this research does not mark any task done
  or authorise an automatic next step.

## Current-run proof files

Public-only capture files are retained in
`evidence\g3-avm\selected-*` beside this feature artifact, not under `infra`.
[selected-proof.json](evidence/g3-avm/selected-proof.json) records exact public
URLs, observation times, HTTP status, raw-byte hashes, the resolved Git ref,
archive members and extraction pointer/hash. Its SHA256 at completion is
`f66c78278ee7d4d7d6c2bb4ed249d32345323ccc62876d9f1a17257c68efae6d`.
The raw sources/templates are evidence-only `.txt` files; the compressed source
archive and full upstream MIT notice are retained for reproducibility.
