# Feature 041 — observed Dev deployment baseline

**G1: OBSERVED, NOT APPROVED. Reconciliation records unresolved differences.**
G2 remains **PARTIAL / STOP**. This report grants no infrastructure, model,
configuration, inference, traffic, rollback or retirement authority.

## Authority, scope and evidence

- Source of G0 authority: the requesting user's explicit fleet collection
  instruction in this run, using existing CLI credentials. An independently
  named approver and approval timestamp were not supplied; none is invented.
- Exact collection window: **2026-10-19T09:15:34Z–2026-10-19T17:15:34Z**.
  This is collection authority, not a baseline freshness TTL.
- Actual reads: **2026-10-19T09:39:41.560683Z–2026-10-19T10:28:14.830829Z**.
- Tenant: `8ae9933a-1eb0-4922-8ecf-c71a136feff3`.
  Subscription: `74a25c57-d6e4-446e-8c99-7f5ace60011b`.
  Resource group: `ama`; environment: `dev`; region: `australiaeast`.
- Actual account: `cog-dev-w3uq6w`, kind `AIServices`, SKU `S0`.
  Account resource ID is recorded in the accompanying JSON.
  Endpoint: `https://dev-aif-w3uq6w.cognitiveservices.azure.com/`.
  The endpoint label is not the ARM account name. No account name was guessed
  or alternate account probed.
- Source HEAD: `a9a7949674ef1090a16049a4e53549f402042083`, with existing
  dirty work preserved. File-specific SHA256 bindings are in the manifest.
  No compiled candidate or release image is bound by this observation.

The accompanying [JSON report](deployment-baseline.json) references **24**
captured evidence files in the current session's `files` directory:

`C:\Users\prbillir\.copilot\session-state\6cfd864e-5202-418c-8388-236f4576ce64\files`

`041-baseline-evidence-manifest.json` records each exact CLI command, start/end
timestamp, exit code and SHA256, plus inspected source-file hashes. Its SHA256 is
`192bf1724d64bd029533933a093f5d19ed862c5fa7f673657048e1d5e8d37698`.
Raw evidence remains session-local, not checked into this repository.

Every Azure command explicitly selected the subscription; no account context
was changed. Reads were ARM/CLI metadata and ACR repository enumeration only.
No keys, secret values or tokens were requested. Environment responses were
sanitized in memory **before output or persistence**. Plaintext Application
Insights connection strings were withheld, not hashed; secret reference names
were retained. Exact secret-bearing configuration digests are **blocked**.
Evidence-file SHA256 values identify sanitized captures, not complete original
cloud payloads. Final captures include only allowlisted response Date, ETag
and request/correlation/routing ID header lines; earlier captures have body
ETags where returned, not HTTP header traces.

## Observed deployments — preserve every identity and protection

All four returned deployments have format `OpenAI`, provisioning state
`Succeeded`, and version upgrade option `OnceNewDefaultVersionAvailable`.
Initial and final deployment responses were equal, including ETags.
Names below are observations, **not approved parameter selections**.

| Purpose inferred from current explicit env | Actual deployment | Actual model | Actual version | SKU | Capacity | Attached RAI policy |
| --- | --- | --- | --- | --- | --- | --- |
| reasoning | `gpt-5.4-dev` | `gpt-5.4` | `2026-03-05` | `GlobalStandard` | 30 | `reasoning-em-domain-dev` |
| drafting | `gpt-5.4-mini-dev` | `gpt-5.4` | `2026-03-05` | `GlobalStandard` | 60 | `drafting-em-domain-dev` |
| simulation | `gpt-5.4-sim-dev` | `gpt-5.4` | `2026-03-05` | `GlobalStandard` | 20 | `sim-em-domain-dev` |
| embedding lookup | `text-embedding-3-large-dev` | `text-embedding-3-large` | `1` | `Standard` | 60 | `Microsoft.DefaultV2` |

`mini` does **not** identify a different underlying model here. Chat rate-limit
metadata is respectively 30,000/60,000/20,000 tokens per 60 seconds and
300/600/200 requests per 60 seconds. Embedding reports 60,000 tokens per 60
seconds and 60 requests per 10 seconds; preserve these distinct unit semantics.
Embedding dimensions are **not exposed** by the deployment or account-model
metadata. The repository's 3072-dimensional expectation is not an observed
runtime result. No inference was made to establish dimensions.

### RAI configuration and effective-filter composition

All three attached custom policies are `UserManaged`, mode `Blocking`, based
on `Microsoft.DefaultV2`. Each explicitly overrides Violence Prompt and
Completion to `High`, with `enabled=true`, `blocking=true`, `action=NONE`.
Do not interpret the returned `action=NONE` as overriding `blocking=true`.

The returned system-managed base has 11 filters:

| Filter | Source | Enabled | Blocking | Severity |
| --- | --- | --- | --- | --- |
| Hate | Prompt / Completion | true | true | Medium |
| Sexual | Prompt / Completion | true | true | Medium |
| Violence | Prompt / Completion | true | true | Medium |
| Selfharm | Prompt / Completion | true | true | Medium |
| Jailbreak | Prompt | true | true | not returned |
| Protected Material Text | Completion | true | true | not returned |
| Protected Material Code | Completion | true | false | not returned |

Every base filter also returns `action=NONE`. The configuration-level effective
composition for each chat policy is this base with the two Violence overrides;
embedding retains the unmodified base. This is a composition of observed
policy definitions, **not runtime enforcement/inference evidence**. No
`IndirectAttack` filter is present in the returned base; do not substitute the
module comment's claimed defaults for the actual policy contents.

## Account, identity, access, network and residency

- Account managed identity: SystemAssigned,
  `8f509bbc-44c8-4280-a3ed-9cfc053c95f7`, in the target tenant.
- `disableLocalAuth=true`, `publicNetworkAccess=Enabled`,
  `privateEndpointConnections=[]`. `networkAcls`, encryption customization
  and outbound-restriction properties are **not returned**, not assumed false
  or replaced with recommended defaults.
- Target-scoped RBAC enumeration returned 50 direct/inherited assignments.
  API identity `7dc8a9f2-1bdc-41c8-9481-aea97b09717a` and agents identity
  `0b986a72-f194-41f5-8f6b-ea070229aaeb` each have account-scoped
  **Cognitive Services OpenAI User**, role ID
  `5e0bd9bd-7b93-4f28-af87-19fc36ad61bd`, with no returned condition.
  Both also have RG-inherited Search Index Data Reader. Complete assignments,
  scopes and conditions are retained in the raw RBAC evidence; this is not
  proof of all possible tenant-level access or a live authorization test.
- Diagnostic setting `openai-diagnostics`: RequestResponse and Audit enabled;
  AllMetrics enabled; AzureOpenAIRequestUsage, Trace and ManagedNetworkEvent
  disabled. Per-setting retention is disabled with days 0.
  Destination `log-dev` is in `australiaeast`, retention 30 days, public
  ingestion/query enabled.
- Explicitly referenced Cosmos account `cosmos-dev-w3uq6w`: sole observed
  read/write location Australia East; continuous 7-day backup; local auth
  remains enabled, public access enabled, IP rules retained in raw evidence.
- Explicitly referenced Storage account `stdevw3uq6w2`: Australia East,
  Standard_LRS, no returned secondary location; HTTPS-only, TLS1_2, no public
  blob access, network default Allow. `allowSharedKeyAccess` is not returned.
  Microsoft-managed blob/file encryption is enabled.
- AU placement of these persistence/diagnostic resources is observed. It
  does not prove an exhaustive residency assessment or AU-only inference:
  the existing chat SKU is **GlobalStandard**, and must not be silently
  changed to Standard or otherwise homogenized.

## Actual application/configuration pairs and readiness

| Service | Only returned revision; active and latest-ready pointer | Traffic | Revision health / running state | Immutable running SHA256 |
| --- | --- | --- | --- | --- |
| API | `ca-api-dev--n6l54uy` | 100%, latest revision | Unhealthy / ActivationFailed | unavailable |
| agents | `ca-agents-dev--pm412va` | 100%, latest revision | Unhealthy / ActivationFailed | unavailable |

Both revision templates specify
`mcr.microsoft.com/azuredocs/containerapps-helloworld:latest`, **not an ACR
application image**. Both applications report provisioning Succeeded and
runningStatus Running, but their revision and replica evidence contradicts
operational readiness. Each has two replicas; all four containers returned
`ready=false`, with CrashLoopBackOff/restarts or a restarting container.
Latest-ready pointer equality is not a successful readiness check.

Final app reads at 10:28Z retained the same revision/image/identity/traffic
bindings. The sanitized application and corresponding revision environment
arrays were equal. Complete nonsecret environment arrays, secretRefs,
resources, probes and app configuration are preserved in the app/revision
evidence; they are not replaced with only a routing subset.

Both apps have the following identical routing observations:

```text
AZURE_AI_PROJECT_ENDPOINT=https://dev-aif-w3uq6w.cognitiveservices.azure.com/
AZURE_AI_PROJECT_DEPLOYMENTS=gpt-5.4@2026-03-05=gpt-5.4-dev,gpt-5.4@2026-03-05=gpt-5.4-mini-dev,gpt-5.4@2026-03-05=gpt-5.4-sim-dev,text-embedding-3-large@1=text-embedding-3-large-dev
AZURE_AI_REASONING_MODEL_KEY=gpt-5.4@2026-03-05
AZURE_AI_DRAFTING_MODEL_KEY=gpt-5.4@2026-03-05
AZURE_AI_SIMULATION_MODEL_KEY=gpt-5.4@2026-03-05
AZURE_AI_REASONING_DEPLOYMENT=gpt-5.4-dev
AZURE_AI_DRAFTING_DEPLOYMENT=gpt-5.4-mini-dev
AZURE_AI_SIMULATION_DEPLOYMENT=gpt-5.4-sim-dev
```

Per-tier `_MODEL_ID` / `_MODEL_VERSION` and direct embedding env settings are
absent in both returned templates. The embedding CSV entry is present and
must be preserved. No new value is proposed to fill an absent setting.

API ingress is external on 8000; agents ingress is internal on 8080; both
disallow insecure ingress. API's anonymous Dev/map flags are enabled,
map-auth disabled and Entra tenant/audience settings empty. These are observed
settings, **not approvals or requested security changes**.

Both registries reference `acr-password` through `passwordSecretRef`; no
password was requested. ACR `crdevw3uq6w` is in Australia East, admin user
enabled, anonymous pull disabled, public access enabled,
LegacyRegistryPermissions. Its authorized repository enumeration returned
`[]`. There is therefore no observed matching ACR repository/manifest to
resolve for these MCR tags. ARM revision/replica metadata did not expose a
running image digest; containerd container IDs are not SHA256 image digests.
No mutable-tag lookup was substituted for the deployed image identity.
No registry credentials, image blobs, builds, pushes or pulls were requested.

**Rollback:** only one revision per service was returned. The pair above is an
observed current pair, not a verified healthy compatible rollback pair.
No retained corrected pair was established by these metadata reads. The known
pre-P1 ambiguous-key/simulation-misrouting defect makes an unverified old pair
unsafe for simulation rollback. No claim is made that the placeholder image
actually executes that code; no application inference was performed.

## Repository-versus-live reconciliation — unresolved, no IaC edits

| Inspected source | Observed comparison | Decision in this collection |
| --- | --- | --- |
| `infra\main.bicep`, module block | Does not expose/pass the nine explicit chat name/model/version selections | Unresolved; no authoring while G2 STOP |
| `infra\modules\azure-openai.bicep` | Defaults all chat models to `gpt-5.6@2026-03-05`, hardcodes `gpt-5.6*` aliases; live is `gpt-5.4*` | Do not apply defaults or rename/create resources |
| `infra\main.parameters.dev.json` | Checked-in environmentName `drh-dev`, not observed Dev suffix `dev`; lacks reviewed per-tier values | This file is not proven to be the live deployment's input |
| `infra\main.parameters.json` | Uses unresolved environment interpolation | Actual substituted/compiled parameter revision unavailable |
| Shared child SKU/quota defaults | Chat GlobalStandard 30/60/20 and embedding Standard 60 match nominal live allocations | Observed agreement only, not approved selections |
| Child RAI definitions | Base and Violence High overrides match observed custom definitions | Preserve full returned base/overrides, including embedding DefaultV2 |
| Upgrade/embedding protection | Child omits upgrade option and embedding RAI attachment | Preserve observed OnceNewDefaultVersionAvailable and DefaultV2; no assumed AVM defaults |
| Both app env producers | Publish explicit aliases/keys but not independent model IDs/versions; CSV duplicates one key for three destinations | Strict-reader activation blocked; image/config must be corrected and reviewed together |
| Current app pair | Placeholder mutable images, unhealthy revisions, no immutable digest or healthy rollback pair | No release/canary/switch/rollback readiness |

No Bicep edits, build, lint, PSRule, What-If or provisioning were run.
Existing serialization and all resources/protections were left unchanged.
G2 remains as recorded in the existing governance artifacts: **11 effective
assignments, 3 subscription-direct / 8 MG-inherited; Portal parity unavailable
because sign-in is required**. No Portal action was taken.

## Outstanding gates and unobservable fields

1. Named G1 approver, baseline approval, and approved freshness/invalidation
   policy ID/version/windows are absent. There is no inferred TTL.
2. Exact candidate image/configuration and compiled IaC/parameter bindings
   are absent. Current pointers are bound observationally, not as a release.
   Redacted plaintext prevents a complete secret-bearing config digest.
3. Immutable deployed image SHA256, healthy candidate/rollback pair and
   successful readiness are not established by available metadata.
4. Embedding runtime dimensions and runtime effective-policy enforcement
   are not established; no inference is authorized.
5. G2 Portal parity and target-specific AVM preservation proof remain blocked
   or unprovided; governance is not cleared.
6. Independent G4/G5a/G5b/G6 stage approvals, a proposed resource/model
   selection and traffic authority are absent. Collection is not approval.

**Stop here.** Existing 47/52 task markers and dirty implementation work are
preserved. Nothing was provisioned or changed in Azure.
