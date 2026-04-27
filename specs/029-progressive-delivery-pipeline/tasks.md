---
description: "Tasks for 029-progressive-delivery-pipeline — sub-hour, regulator-defensible CD"
---

# Tasks: Progressive Delivery Pipeline (Option A — Sub-Hour Lead Time)

**Input**: Design documents from `C:\code\ama\specs\029-progressive-delivery-pipeline\`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
**Tests**: Test tasks ARE included — Constitution Principle VI (Validation Discipline) and FR-008/FR-009 require pipeline self-tests, contract tests for OPA policies, posture verifier, canary controller, and evidence pack producer.

## Format: `[ID] [P?] [Story] Description`

- **[P]** — Parallelisable (touches different files, no dependency on incomplete tasks)
- **[USx]** — User story label (US1 … US9)
- Each task lists **Agents** (actor agents to consult), **Tools** (`execute` `read` `edit` `search` `web` `agent` `todo`), and **Success** (verifiable criterion)

## Path Conventions (per `plan.md`)

- Workflows: `.github/workflows/`
- Pipeline tooling: `tools/pipeline/` (new Python package `tools/pipeline/src/pipeline_tools/`)
- Infrastructure: `infra/bicep/`, `infra/policy/` (new), `infra/parameters/`
- Tests: `tests/pipeline/` (new — `unit/`, `contract/`, `integration/`)
- Specs: `specs/029-progressive-delivery-pipeline/`
- Apps (`apps/web`, `apps/api`, `apps/agents`) are NOT modified by this feature; only the pipeline that delivers them.

---

## Implementation Status (auto-generated — last sweep)

The following artefacts have been created in the working tree and validated locally
(`ruff check tools/pipeline` ✓, `mypy tools/pipeline/src` ✓, `pytest tests/pipeline -q` → 10 passed, 11 skipped without OPA CLI):

| Phase | Tasks delivered as files | External-mutation tasks (script-only) |
|-------|--------------------------|---------------------------------------|
| 1     | T001–T009 (incl. T008a IDENTITY.md, T008b identity_consistency.rego) | T000a → `scripts/spec029-bootstrap/01-invite-collaborator.ps1` |
| 2     | T010–T021, T024, T024a (rego + audit-event schema + reviewer_sync) | T022 → `02-create-federated-creds.ps1`, T023 → `03-configure-gh-environments.ps1`, T024 → `04-create-entra-groups.ps1` |
| 3–11  | T025, T029, T031, T041, T051, T052, T060, T061, T062, T064–T066, T067–T070, T076–T079, T079a, T080 (workflows + Python tools) | Real Azure deploy of `posture-policy-set.bicep`, `pipeline-identity.bicep`, `evidence-store.bicep`, `audit-store.bicep`, `jump-host.bicep`, `defender-baseline.bicep` requires user execution of `az deployment sub create` against the spec-029 target subscription |
| 12    | T080 (drift detection) — workflow created | observability dashboards remain manual until first deploy emits live metrics |
| 13    | T079a inlined into `_reusable/canary-stage.yml`; T087 sweep + T088 coverage gate covered by `pr-gates.yml` (`pytest tests/pipeline`) |  |

**Spec 029 implementation does NOT mutate Azure or GitHub from this session.** All
external mutations land in idempotent scripts under `scripts/spec029-bootstrap/`
(see `scripts/spec029-bootstrap/README.md`) for the platform owner to execute
after reviewing the diffs.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Scaffold the new directories, Python tooling package, GitHub OIDC trust, and reusable composite actions that every later phase depends on.

- [ ] T000a Document and execute the **second-collaborator pre-flight** required by ADR-029-01 (research.md §R17): under the current user-owned repository (`johnbilliris/ama`), invite a second human GitHub account as a write-access collaborator so that the FR-033 dual-approval rule on posture-matrix changes (and the FR-011a "two distinct identities, neither equals the PR author" rule on emergency-hotfix approvals) is satisfiable. Record the collaborator's GitHub handle in `infra/IDENTITY.md` (field `second_collaborator`) alongside `subscription_topology` and `codeowners_handle_mode`. **This task BLOCKS T008, T024, T043, T044, T045, T046, T058 (any task depending on FR-003 / FR-011a / FR-033 reviews) and is itself blocked only on `infra/IDENTITY.md` existing (T008a). Until T000a is complete, posture-matrix and emergency-hotfix PRs will queue indefinitely under user-owned mode — this is the desired safety property of ADR-029-01, not a defect.** On future organisation migration, this task becomes a no-op (team membership replaces individual collaboration) but the recorded handle remains historically auditable.
  - **Agents**: `principal-engineer`, `security-engineer`, `compliance-auditor`
  - **Tools**: `execute` (`gh api repos/:owner/:repo/collaborators/{handle} -X PUT -f permission=push`), `edit` (`infra/IDENTITY.md`)
  - **Success**: `gh api repos/:owner/:repo/collaborators` lists the second collaborator with `push` permission; `infra/IDENTITY.md` contains `second_collaborator: <handle>`; a synthetic PR touching `infra/policy/posture-matrix.yaml` cannot be merged by the owner alone (branch protection blocks self-approval) and merges only after the second collaborator approves; the dummy PR is reverted after verification.

- [ ] T001 Create directory skeleton `infra/policy/`, `tools/pipeline/src/pipeline_tools/`, `tools/pipeline/tests/`, `tests/pipeline/{unit,contract,integration}/`, and `.github/workflows/_reusable/` per `plan.md` Project Structure
  - **Agents**: `infrastructure-devops`, `principal-engineer`
  - **Tools**: `execute`, `edit`
  - **Success**: All seven directories exist; `git status` shows them as untracked; `tree -L 3 infra/policy tools/pipeline tests/pipeline` matches the structure in `plan.md`.

- [ ] T002 [P] Initialise `tools/pipeline/pyproject.toml` declaring Python 3.12, dependencies (`azure-identity`, `azure-mgmt-resourcegraph`, `azure-storage-blob`, `azure-cosmos`, `pydantic>=2`, `pyyaml`, `jsonschema`, `cryptography`), dev deps (`pytest`, `pytest-asyncio`, `ruff`, `mypy`), and console-script entry points `posture-verifier`, `canary-controller`, `evidence-packer`, `audit-emitter`, `freeze-controller`
  - **Agents**: `software-developer`, `infrastructure-devops`
  - **Tools**: `edit`, `execute`
  - **Success**: `cd tools/pipeline && pip install -e .[dev]` succeeds; the four console scripts resolve via `which posture-verifier` (and the rest); `ruff check .` and `mypy .` exit 0 against the empty package.

- [ ] T003 [P] Add `tools/pipeline/src/pipeline_tools/__init__.py` exposing semver `__version__ = "0.1.0"` and `tools/pipeline/README.md` describing the five CLI tools and how they map to FR-005, FR-013, FR-014, FR-031, and FR-032
  - **Agents**: `software-developer`
  - **Tools**: `edit`
  - **Success**: `python -c "import pipeline_tools; print(pipeline_tools.__version__)"` prints `0.1.0`; README links to spec FR identifiers.

- [ ] T004 [P] Configure `tools/pipeline/.ruff.toml` and `tools/pipeline/mypy.ini` matching repo-wide conventions (line-length 100, `strict = true`, `disallow_untyped_defs = true`)
  - **Agents**: `software-developer`, `qa-test-engineer`
  - **Tools**: `edit`, `execute`
  - **Success**: `ruff check tools/pipeline` and `mypy --strict tools/pipeline/src` exit 0.

- [ ] T005 Create reusable composite GitHub Action `.github/workflows/_reusable/setup-oidc-azure.yml` that performs `azure/login@v2` with `client-id`, `tenant-id`, `subscription-id` inputs (no `creds:` secret), asserts the resulting token contains the expected `aud`/`sub`, and exports `AZURE_*` env vars. **Per ADR-029-01 / R16 (research.md §R16, §R17) and as referenced by T008a: after `azure/login` succeeds, the action MUST parse the YAML front-matter of `infra/IDENTITY.md` and assert that the resolved `AZURE_SUBSCRIPTION_ID` for the current GitHub Environment matches `topology_subscription_ids[$env]` from the file (where `$env` ∈ `dev`/`staging`/`production`). On mismatch the action MUST exit non-zero with a clear error message citing ADR-029-01 / R16 and the observed-vs-expected subscription IDs (do not log the GUIDs in plaintext beyond the last 4 characters), and MUST emit an audit event `action: gate.decision`, `outcome: denied`, `rationale: identity_consistency_topology_mismatch`. This is the runtime enforcement counterpart to the `identity_consistency.rego` static check from T008b.** The action MUST also set the env var `AMA_SUBSCRIPTION_TOPOLOGY` from the same file, consumed by downstream jobs (T019a, T020/T020a) for audit-event stamping.
  - **Agents**: `infrastructure-devops`, `security-engineer`
  - **Tools**: `edit`, `web` (Microsoft Learn for OIDC claim format), `read` (`infra/IDENTITY.md` schema from T008a)
  - **Success**: Workflow file YAML parses (`gh actions-syntax-check` or `actionlint`); inputs documented; no `secrets.AZURE_CREDENTIALS` reference appears anywhere in `_reusable/`; a fixture test (added to T026 or as a standalone `tests/pipeline/integration/test_setup_oidc_azure.py`) drives the action with (a) a matching `IDENTITY.md` → exit 0 + `AMA_SUBSCRIPTION_TOPOLOGY` exported, (b) a mismatched `IDENTITY.md` → exit non-zero with the documented error string and the audit event emitted.

- [ ] T006 [P] Create reusable composite action `.github/workflows/_reusable/install-opa.yml` that pins `open-policy-agent/setup-opa@v2` to a SHA, installs `conftest` v0.50+, caches both binaries by version, and prints `opa version` for evidence
  - **Agents**: `infrastructure-devops`, `compliance-auditor`
  - **Tools**: `edit`, `web` (latest OPA / conftest releases)
  - **Success**: Action runs on `ubuntu-22.04`; `actionlint` passes; pinned SHAs documented in a comment with the corresponding version tag.

- [ ] T007 [P] Create reusable composite action `.github/workflows/_reusable/setup-cosign-syft.yml` that pins `sigstore/cosign-installer` and `anchore/sbom-action` to SHAs, configures keyless signing identity via OIDC, and outputs the `COSIGN_EXPERIMENTAL=1` env
  - **Agents**: `infrastructure-devops`, `security-engineer`, `docker-container-engineer`
  - **Tools**: `edit`, `web` (Sigstore docs for keyless OIDC)
  - **Success**: `actionlint` passes; reusable action signed-test in a throwaway workflow can produce a Cosign signature against a public test image.

- [ ] T008 Add repository-level `.github/CODEOWNERS` entries claiming `infra/policy/posture-matrix.yaml` and `infra/policy/posture-exceptions.yaml` for the security and compliance CODEOWNER personas (dual-owner rule for FR-033). **Per ADR-029-01 (research.md §R17), and because the repository is currently user-owned (`johnbilliris/ama`), use the individual handle `@johnbilliris` for both persona slots; the dual-approver requirement is enforced by branch protection's "require 2 approving reviews" rather than by team membership. The future-state mapping back to `@org/security-codeowners` and `@org/compliance-codeowners` is recorded in research.md §R17 and MUST be applied verbatim once the repository migrates into a GitHub organisation.**
  - **Agents**: `security-engineer`, `compliance-auditor`
  - **Tools**: `edit`, `agent` (consult `compliance-auditor` to confirm the user-owned-repo fallback in ADR-029-01 satisfies FR-033 via branch protection)
  - **Success**: `gh api repos/:owner/:repo/codeowners/errors` returns empty; the `@johnbilliris` handle appears against both posture files; branch protection on `main` requires 2 approving reviews on PRs touching either posture file; `git log --pretty=format:'%an' -- .github/CODEOWNERS | head` shows last edit by a maintainer; `infra/IDENTITY.md` records "CODEOWNERS handle mode: user (per ADR-029-01)" with the migration trigger noted.

- [ ] T008a [P] Author **`infra/IDENTITY.md`** as the canonical record of pipeline identity decisions (referenced by T005, T008, T019a, T023, T024, T044, T084). The file MUST be a Markdown document with a YAML front-matter block declaring the following keys: `subscription_topology` (`A` \| `B`), `codeowners_handle_mode` (`team` \| `user`), `second_collaborator` (GitHub handle string \| `null`), `entra_groups` (array of `{name, object_id}`), `production_reviewers_mode` (`scim_team` \| `individual_union`), `migration_trigger` (free-text condition under which the user-mode fallback reverts), and `topology_subscription_ids` (object mapping `dev`/`staging`/`production` → subscription GUIDs; under Topology B all three values are identical). Include a worked example block for **both** topologies and a worked example for **both** CODEOWNERS handle modes (org and user) so the schema is self-documenting. The runtime topology assertion lives in T005's reusable OIDC action (which parses this file as the trust root for the deploy-target check); the static counterpart is `identity_consistency.rego`, owned by **T008b**.
  - **Agents**: `principal-engineer`, `security-engineer`, `infrastructure-devops`, `compliance-auditor`
  - **Tools**: `edit`, `read` (existing CODEOWNERS), `agent` (consult `compliance-auditor` on retention / immutability of identity record)
  - **Success**: `infra/IDENTITY.md` parses as valid YAML front-matter via `python -c "import yaml,frontmatter; print(frontmatter.load(open('infra/IDENTITY.md')).metadata)"`; the schema documents all seven keys with example values for both topologies and both handle modes; the file is referenced from `quickstart.md` Onboarding section.

- [ ] T008b [P] Author **`infra/policy/rego/identity_consistency.rego`** (the static counterpart of the T005 runtime topology assertion). The Rego MUST consume `infra/IDENTITY.md` (parsed by the OPA gate driver) and the resolved per-environment `AZURE_SUBSCRIPTION_ID` values (collected from `infra/parameters/{dev,staging,production}.bicepparam`), and emit `deny` for any of: (a) declared `subscription_topology: A` but fewer than 3 distinct subscription IDs across the parameter files; (b) declared `subscription_topology: B` but the three parameter files declare different subscription IDs; (c) declared `codeowners_handle_mode: team` but `.github/CODEOWNERS` contains user-style `@johnbilliris`-form handles (or vice versa); (d) declared `production_reviewers_mode: individual_union` but the union exceeds the 6-collaborator cap (matches the runtime check enforced by `reviewer_sync.py` per T024). Include a top-level `package identity_consistency` and at least the 4 deny rules above with rationale strings citing ADR-029-01 / R16 / R17. The contract test for this Rego file lives in T017 (`test_rego_identity_consistency.py`).
  - **Agents**: `security-engineer`, `infrastructure-devops`, `compliance-auditor`
  - **Tools**: `edit`, `read` (`infra/IDENTITY.md` schema from T008a, `.github/CODEOWNERS`), `web` (OPA Rego docs)
  - **Success**: `conftest test --policy infra/policy/rego --data infra/IDENTITY.md tests/pipeline/contract/fixtures/identity-good.json` returns 0 violations; each of the four failing fixtures from T017 produces exactly one matching `deny` with the expected rationale string; `opa fmt` reports no changes needed.

- [ ] T009 [P] Document Setup phase in `tools/pipeline/CONTRIBUTING.md` covering local install, running `pytest tests/pipeline/`, and how to dry-run any of the five CLIs against a fake Cosmos / Blob backend
  - **Agents**: `software-developer`, `principal-engineer`
  - **Tools**: `edit`
  - **Success**: A new contributor following the doc end-to-end can produce a local OPA decision against a sample Bicep What-If JSON.

**Checkpoint**: `tools/pipeline` installable, OIDC + OPA + Cosign reusable actions exist, posture-file CODEOWNERS enforce dual approval. Foundational phase can begin.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the canonical contracts, state stores, and identity boundary that every user story depends on. **No user-story phase can begin until this phase is complete.**

- [ ] T010 Author canonical `infra/policy/posture-matrix.yaml` (FR-025) covering the three environments (dev, staging, production) and the seven resource families (Cosmos, Storage, Key Vault, Container Apps, App Service, Function App, OpenAI/Foundry) per `contracts/posture-matrix.schema.yaml`; include for each cell `network_access`, `auth_modes`, `data_plane_ingress`, `min_tls`, and a `required_tags` block
  - **Agents**: `security-engineer`, `infrastructure-devops`, `compliance-auditor`, `azure-principal-architect`
  - **Tools**: `edit`, `read` (`contracts/posture-matrix.schema.yaml`), `agent` (request `compliance-auditor` to validate against PSPF / Essential 8 controls and `azure-principal-architect` to validate against WAF Reliability/Security pillars)
  - **Success**: `python -m jsonschema -i infra/policy/posture-matrix.yaml specs/029-progressive-delivery-pipeline/contracts/posture-matrix.schema.yaml` exits 0; matrix encodes the dev↔staging/prod difference clarified in spec Q5/Q6 (public+key allowed dev only; MI/OIDC mandatory staging+prod).

- [ ] T011 [P] Author initial `infra/policy/posture-exceptions.yaml` (empty `exceptions: []`) and `infra/policy/foundry-carveout.yaml` listing the named non-AU model-hosting endpoints permitted under Constitution NN-2; both files validate against `contracts/posture-exceptions.schema.yaml` and an inline schema in the file header
  - **Agents**: `security-engineer`, `compliance-auditor`
  - **Tools**: `edit`, `read`
  - **Success**: Both files validate against their schemas; `foundry-carveout.yaml` lists each carve-out with `endpoint`, `region`, `data_minimisation_owner`, and `expires_at`.

- [ ] T012 Implement `tools/pipeline/src/pipeline_tools/posture_matrix.py` with `load_matrix(path)`, `lookup(env, resource_family, property)`, and `effective_posture(env, exceptions)` — applying active exceptions and returning a frozen `PostureDecision` dataclass
  - **Agents**: `software-developer`, `security-engineer`
  - **Tools**: `edit`, `execute`
  - **Success**: `pytest tests/pipeline/unit/test_posture_matrix.py -q` passes (tests written in T013); `mypy --strict` clean.

- [ ] T013 [P] Write unit tests `tests/pipeline/unit/test_posture_matrix.py` covering: matrix load, schema rejection of malformed file, exception application, expired-exception rejection, and the dev/staging/prod cell differences from spec Q5/Q6
  - **Agents**: `qa-test-engineer`, `security-engineer`
  - **Tools**: `edit`, `execute`
  - **Success**: ≥10 test cases; coverage of `posture_matrix.py` ≥95 % via `pytest --cov`; tests fail before T012 and pass after.

- [ ] T014 Generate Rego policy `infra/policy/rego/posture.rego` that consumes `posture-matrix.yaml` (loaded as data) and the Bicep What-If JSON (input), returning `deny` messages with the exact matrix rule citation and resource id; include a top-level `package posture` and helpers for the seven resource families
  - **Agents**: `infrastructure-devops`, `security-engineer`, `compliance-auditor`
  - **Tools**: `edit`, `read` (`posture-matrix.yaml`), `web` (OPA Rego docs)
  - **Success**: `conftest test --policy infra/policy/rego --data infra/policy/posture-matrix.yaml tests/pipeline/contract/fixtures/whatif-good.json` returns 0 violations; `…/whatif-bad-staging-publickey.json` returns ≥1 deny mentioning `posture-matrix.yaml#cosmos.staging.auth_modes`.

- [ ] T015 [P] Generate Rego policy `infra/policy/rego/cross-env.rego` enforcing FR-029 + FR-016 (no `dev` resource id, key vault URI, or connection string referenced in `staging`/`production` parameter files or RBAC role assignments; OIDC-only identity). **The rule MUST evaluate at BOTH boundaries to support the dual subscription topology (research.md §R16): (a) under Topology B, the boundary is the resource group — string-match `rg-ama-{env}-…` is sufficient; (b) under Topology A, the boundary is the subscription — the rule MUST parse the full ARM resource ID and assert that the `subscriptions/{guid}` segment matches the environment's declared subscription in `infra/IDENTITY.md` (not a foreign environment's subscription). Rejecting a `staging`-sub resource that references a `dev`-sub key vault by full ARM ID is a P1 deny case under Topology A.**
  - **Agents**: `security-engineer`, `infrastructure-devops`
  - **Tools**: `edit`, `read` (`infra/IDENTITY.md` for topology declaration shape)
  - **Success**: `conftest test` blocks a fixture that grants a dev-scoped Key Vault role to a production identity (FR-029 / spec US9 acceptance scenario d); under a Topology A fixture, `conftest test` also blocks a `staging`-RG resource that references a `dev`-subscription Key Vault by full ARM ID; under a Topology B fixture, the same logical violation is caught by the RG-name match.

- [ ] T016 [P] Generate Rego policy `infra/policy/rego/foundry-carveout.rego` permitting non-AU model endpoints only when listed in `foundry-carveout.yaml` and rejecting any non-AU resource of a regulated kind (Cosmos, Storage, Key Vault, etc.)
  - **Agents**: `security-engineer`, `compliance-auditor`, `ai-ml-engineer`
  - **Tools**: `edit`, `agent` (consult `ai-ml-engineer` on which Foundry SKUs require carve-out and which are AU-resident)
  - **Success**: `conftest test` accepts a Foundry endpoint listed in carve-out, rejects an unlisted one, and rejects a Cosmos DB in `eastus`.

- [ ] T017 Write contract tests `tests/pipeline/contract/test_rego_posture.py` and `…/test_rego_cross_env.py` and `…/test_rego_foundry_carveout.py` and `…/test_rego_identity_consistency.py` driving each Rego file with at least three positive and three negative fixtures stored under `tests/pipeline/contract/fixtures/`. **The cross-env contract test MUST include at least one Topology A fixture (parameter files declaring three distinct subscription GUIDs) and one Topology B fixture (parameter files declaring the same shared subscription GUID with three RG names) so both R16 modes are covered. The identity-consistency contract test MUST cover: passing case (declared topology matches resolved subscription IDs), failing case (declared Topology A but only one subscription resolved), and failing case (CODEOWNERS handle mode declared as `team` but `.github/CODEOWNERS` contains user handles).**
  - **Agents**: `qa-test-engineer`, `security-engineer`, `compliance-auditor`
  - **Tools**: `edit`, `execute`
  - **Success**: All four contract test files run via `pytest tests/pipeline/contract -q` and pass; each has ≥6 fixtures (3 allow, 3 deny); negative fixtures reference the exact rule cited in the deny message; cross-env file has ≥1 Topology A and ≥1 Topology B fixture; identity-consistency file covers both topology mismatch and CODEOWNERS-mode mismatch cases.

- [ ] T018 Author Bicep module `infra/bicep/modules/pipeline-state.bicep` provisioning a Cosmos container `pipeline_state` (PartitionKey `/pk` → `{env}-{kind}`) inside the existing audit Cosmos account, plus a Blob Storage container `evidence-packs` in `australiaeast` with time-based immutability `7y`, legal-hold ON, and customer-managed key from existing Key Vault
  - **Agents**: `infrastructure-devops`, `data-engineer`, `azure-principal-architect`, `compliance-auditor`
  - **Tools**: `edit`, `read` (`infra/bicep/main.bicep` for existing audit account name), `agent` (consult `data-engineer` on partition key strategy and `compliance-auditor` on immutability period vs PSPF)
  - **Success**: `bicep build infra/bicep/modules/pipeline-state.bicep` exits 0; `az deployment group what-if` against a sandbox RG shows the two new resources with the immutability/legal-hold flags set; `compliance-auditor` agent confirms 7y satisfies retention.

- [ ] T019 [P] Wire `pipeline-state.bicep` into `infra/bicep/main.bicep` and provide environment-specific values in `infra/parameters/{dev,staging,production}.bicepparam` (legal hold OFF in dev, ON in staging+prod per FR-031/FR-024)
  - **Agents**: `infrastructure-devops`, `compliance-auditor`
  - **Tools**: `edit`, `read`
  - **Success**: `bicep build infra/bicep/main.bicep` exits 0; What-If shows `evidence-packs` container created in all three envs with correct legal-hold flag.

- [ ] T019a Introduce the **`subscriptionTopology` parameter** (`'A' | 'B'`, default `'B'`) at the root of `infra/bicep/main.bicep` per research.md §R16, and switch the Azure Policy assignment scope conditionally based on the parameter value: under Topology A the AU-region, posture, and deny-public-endpoint policy assignments resolve to `targetScope = 'subscription'` (assignments at subscription scope); under Topology B they resolve to `targetScope = 'resourceGroup'` and are assigned per-RG. Surface the resolved topology as a deployment output (`pipelineIdentity.subscription_topology`) consumed by T023 (environment-variable wiring) and T044 (branch-protection identity check). The parameter MUST be set per-environment in `infra/parameters/{dev,staging,production}.bicepparam` (in user-owned-mode tenants typically `'B'` everywhere; multi-subscription tenants typically `'A'` everywhere). The OPA topology assertion (T015 + identity-consistency rule from T008a) MUST reject any What-If where the resolved subscription IDs disagree with the declared topology.
  - **Agents**: `infrastructure-devops`, `azure-principal-architect`, `security-engineer`
  - **Tools**: `edit`, `read` (`infra/IDENTITY.md`), `web` (Microsoft Learn Bicep policy-assignment scope docs), `agent` (`azure-principal-architect` to review the conditional-scope pattern)
  - **Success**: `bicep build infra/bicep/main.bicep` exits 0 for both `--parameters subscriptionTopology=A` and `=B`; What-If under Topology A shows policy assignments at subscription scope, under Topology B at RG scope; an attempt to deploy a Topology-A parameter file against a single shared subscription is rejected by the identity-consistency Rego rule (T015 / T008a); the deployment output `pipelineIdentity.subscription_topology` matches the parameter file value.

- [ ] T020 Implement `tools/pipeline/src/pipeline_tools/audit_emitter.py` exposing `emit(event: AuditEvent)` that validates against `contracts/audit-event.schema.json`, signs the canonical JSON with the workflow's OIDC token, and writes to the Cosmos audit container; expose CLI `audit-emitter --event-file event.json`
  - **Agents**: `software-developer`, `security-engineer`, `data-engineer`
  - **Tools**: `edit`, `read` (`contracts/audit-event.schema.json`)
  - **Success**: `audit-emitter --event-file tests/pipeline/contract/fixtures/audit-deploy.json` writes a document; round-tripping the document validates against the schema; signature verifies offline.

- [ ] T020a Author **`contracts/audit-event.schema.json`** as the JSON Schema (draft 2020-12) implementation of FR-015's structured deployment audit-event contract. The schema MUST require: `actor` (string, GitHub identity), `timestamp` (RFC 3339 UTC), `action` (enum: `deploy.start`, `deploy.success`, `deploy.failure`, `gate.decision`, `promotion`, `rollback`, `freeze.activate`, `freeze.release`, `evidence-pack.write`, `evidence-pack.reconciled`, `devkey.issue`, `devkey.rotate`), `rationale` (string, ≤2000 chars), `outcome` (enum: `success`, `denied`, `error`, `timeout`), and deployment-specific fields `environment` (`dev`\|`staging`\|`production`), `subscription_topology` (`A`\|`B`, sourced per R16 — populated from the `AMA_SUBSCRIPTION_TOPOLOGY` env var exported by T005's reusable OIDC action), `commit_sha`, `pr_number` (nullable), `gate_set` (array), `signature` (sigstore bundle ref). Forward-compatible additionalProperties MUST be allowed for non-required fields. **Wire `jsonschema` validation into `tools/pipeline/src/pipeline_tools/audit_emitter.py` (T020) so every `emit()` call rejects non-conforming payloads before persistence — the emitter is the canonical write path.** If a future task introduces an additional Cosmos write path that bypasses the emitter, that task MUST also import the schema and validate before write; this rule is enforced by a unit test in T021 that asserts the schema module is the sole import source for audit validation logic. The schema is the canonical contract; deviations require a contract-version bump (`/$id` and a `version` field).
  - **Agents**: `data-engineer`, `security-engineer`, `compliance-auditor`, `principal-engineer`
  - **Tools**: `edit`, `web` (JSON Schema 2020-12 docs), `agent` (`compliance-auditor` to confirm the field set satisfies PSPF audit retention requirements, `data-engineer` for partition-key compatibility with Cosmos audit container)
  - **Success**: `python -c "import json,jsonschema; jsonschema.Draft202012Validator.check_schema(json.load(open('contracts/audit-event.schema.json')))"` exits 0; the contract test from T021 passes against the new schema; an audit event missing `subscription_topology` is rejected by `audit-emitter` with a clear validation error; the schema's `/$id` is referenced from T020's helper module.

- [ ] T021 [P] Write contract test `tests/pipeline/contract/test_audit_event_schema.py` covering: required fields enforced, action enum exhaustive (matches `audit-event.schema.json`), invalid timestamp rejected, oversize rationale rejected, and forward-compatible additional optional fields accepted
  - **Agents**: `qa-test-engineer`
  - **Tools**: `edit`, `execute`
  - **Success**: ≥8 cases; `pytest tests/pipeline/contract/test_audit_event_schema.py -q` passes.

- [ ] T022 Configure GitHub Actions OIDC trust on the Azure side: create three federated credentials (per environment) under app registration `ama-pipeline-{env}`; only `production` and `staging` workloads can write to evidence/audit stores at runtime; `dev` workflow has `Reader` only; document the `aud`/`sub`/`repo:org/repo:environment:{env}` claim shape
  - **Agents**: `security-engineer`, `infrastructure-devops`
  - **Tools**: `execute` (`az ad app federated-credential create`), `edit` (document in `quickstart.md` or `infra/IDENTITY.md`), `web` (Microsoft Learn OIDC claim docs)
  - **Success**: `az ad app federated-credential list --id <app>` shows three creds with environment-scoped subjects; a dry-run workflow on each environment exchanges OIDC successfully and `az account show` returns the expected app object id.

- [ ] T023 [P] Configure three GitHub Environments (`dev`, `staging`, `production`) with: required reviewers (`staging`: 1 SRE; `production`: 2 reviewers — 1 SRE + 1 incident-commander group member), `production` deployment branch policy `main` only, environment-scoped variables `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `AZURE_RG`. **Per the dual-topology decision in research.md §R16: under Topology A the three `AZURE_SUBSCRIPTION_ID` values MUST be three distinct subscription IDs (one per environment); under Topology B all three MUST be the same single subscription ID with the per-environment isolation expressed via `AZURE_RG`. The chosen topology MUST be recorded in `infra/IDENTITY.md` as `subscription_topology: A` or `B`, and a startup assertion in T005's reusable OIDC action MUST validate that the resolved `AZURE_SUBSCRIPTION_ID` for the current environment matches the declared topology (reject mismatch).**
  - **Agents**: `infrastructure-devops`, `security-engineer`, `sre-engineer`
  - **Tools**: `execute` (`gh api …/environments/…`), `edit` (snapshot in `infra/IDENTITY.md`)
  - **Success**: `gh api repos/:owner/:repo/environments/production` returns the two required reviewers; environment vars present; merge to `main` triggers env protection prompts as expected on a manual test.

- [ ] T024 Provision the three privileged Entra ID groups `ama-oncall-sre`, `ama-incident-commander`, `ama-emergency-approver`, populate them, and gate the `production` GitHub environment reviewer list on those group memberships. **Per ADR-029-01 (research.md §R17), gating mode is conditional on repository ownership: under an organisation-owned repository, gate via SCIM-synced GitHub teams that mirror the Entra groups. Under the current user-owned repository (`johnbilliris/ama`), GitHub teams are not available; in this mode each Entra group member MUST be added individually to the `production` environment's required-reviewers list, and an idempotent reconciler script `tools/pipeline/src/pipeline_tools/reviewer_sync.py` MUST run nightly to assert that the `production` reviewer set equals the union of the three Entra groups (logging drift to the audit store). The reconciler MUST also assert membership-change audit events are emitted for any add/remove. The Entra groups themselves remain authoritative for FR-011 / FR-011a regardless of ownership mode; the GitHub-side enforcement is the second factor.** **Per the ≤6-collaborator constraint added to ADR-029-01 (research.md §R17): under user-owned mode, `len(union(group_members)) ≤ 6` because GitHub Environments hard-cap required reviewers at 6 distinct identities per environment. The reconciler MUST fail loudly (non-zero exit, audit `action: deploy.warning`) when this cap is reached or breached, with a recommendation to migrate to organisation mode.**
  - **Agents**: `security-engineer`, `infrastructure-devops`, `sre-engineer`
  - **Tools**: `execute` (`az ad group create` / `az ad group member add`), `edit` (reconciler), `agent` (consult `sre-engineer` for membership policy and `security-engineer` for break-glass)
  - **Success**: `az ad group show --group ama-emergency-approver` returns expected members; under organisation mode, SCIM sync log shows the GitHub teams pulled the same members; under user-owned mode (current), `gh api repos/:owner/:repo/environments/production` shows each Entra-group member as an individual reviewer and `reviewer_sync.py --check` reports zero drift; under user-owned mode, `reviewer_sync.py --check` exits non-zero and emits `action: deploy.warning` when `len(union(group_members)) > 6`; an out-of-group user attempting to approve a `production` deploy is denied; `infra/IDENTITY.md` records the active gating mode and the current union size.

- [ ] T024a [P] Author **`tests/pipeline/integration/test_reviewer_sync.py`** covering the user-owned-mode reconciler `tools/pipeline/src/pipeline_tools/reviewer_sync.py` (introduced by T024). Required test cases: (a) **happy path** — mocked Entra group members exactly equal the GitHub `production` environment reviewer list → `reviewer_sync.py --check` exits 0, no audit event emitted; (b) **drift detected** — Entra group has a member missing from GitHub reviewers → `--check` exits non-zero, an audit event with `action: deploy.warning` and `outcome: denied` is emitted with the diff; (c) **drift remediated** — same fixture as (b) under `--apply` mode → reviewer is added via `gh api …/environments/production -X PUT`, audit event with `action: gate.decision` and `outcome: success` is emitted; (d) **membership change** — Entra group member added since last run → re-sync triggered, audit event records the add; (e) **cap breach** — `len(union(group_members)) == 7` (one over the GitHub Environments hard limit per ADR-029-01 amendment) → `--check` exits non-zero, recommendation to migrate to org mode appears in stderr, audit `action: deploy.warning` with `rationale` citing R17. All HTTP calls MUST be mocked with `responses` or `pytest-httpserver`; no real GitHub or Entra calls. Add the test to T088's coverage gate (assert ≥85 % branch coverage on `reviewer_sync.py`).
  - **Agents**: `qa-test-engineer`, `sre-engineer`, `security-engineer`
  - **Tools**: `edit`, `execute`, `agent` (`qa-test-engineer` for fixture design, `security-engineer` for cap-breach rationale)
  - **Success**: `pytest tests/pipeline/integration/test_reviewer_sync.py -q` passes offline (no network); ≥5 cases including the cap-breach case; `coverage report` shows ≥85 % branch coverage on `reviewer_sync.py`; T088's self-validation gate references this test file.

- [ ] T025 Implement `tools/pipeline/src/pipeline_tools/posture_verifier.py` that runs an Azure Resource Graph query covering all RGs `rg-ama-{env}-australiaeast`, evaluates each resource against `posture_matrix.effective_posture`, and returns a JSON report `{env, total, passed, failed:[…with rule_id, resource_id, observed, expected]}`
  - **Agents**: `software-developer`, `security-engineer`, `infrastructure-devops`, `azure-principal-architect`
  - **Tools**: `edit`, `web` (Resource Graph schema for relevant resource families), `agent` (`azure-principal-architect` to validate Resource Graph query is the right primitive)
  - **Success**: CLI runs against a sandbox subscription and reports correctly on a deliberately misconfigured Storage account (public network) with a non-zero `failed` count and the exact rule citation.

- [ ] T026 [P] Write integration test `tests/pipeline/integration/test_posture_verifier.py` using a recorded Resource Graph response (VCR-style fixture) covering one passing and one failing resource per family, with assertions on the JSON report shape from T025
  - **Agents**: `qa-test-engineer`
  - **Tools**: `edit`, `execute`
  - **Success**: `pytest tests/pipeline/integration/test_posture_verifier.py -q` passes offline (no Azure call); coverage ≥85 % for `posture_verifier.py`.

- [ ] T027 Implement `tools/pipeline/src/pipeline_tools/freeze_controller.py` exposing `is_frozen(env)` (reads `pipeline_state` Cosmos container `change-freeze` document), `set_freeze(env, on, actor, reason)`, and CLI `freeze-controller {status|on|off} --env <env> --reason "<text>"`; only members of `ama-incident-commander` may set freeze
  - **Agents**: `software-developer`, `sre-engineer`, `security-engineer`
  - **Tools**: `edit`, `read` (`data-model.md` for the `change-freeze` schema), `agent` (`sre-engineer` to confirm freeze granularity = per env)
  - **Success**: CLI round-trips a freeze toggle; `is_frozen("production")` returns the freshly-written value; an invocation by a non-incident-commander identity is rejected at the audit emitter step.

- [ ] T028 [P] Unit + integration tests `tests/pipeline/unit/test_freeze_controller.py` and `tests/pipeline/integration/test_freeze_controller.py` covering RBAC rejection, freeze status read, freeze toggle, audit event emission on every state change, and concurrent toggle race (last-writer-wins with optimistic concurrency)
  - **Agents**: `qa-test-engineer`, `security-engineer`
  - **Tools**: `edit`, `execute`
  - **Success**: ≥12 cases; passes `pytest tests/pipeline -q -k freeze`.

**Checkpoint**: Posture matrix is the canonical source of truth and is enforced by Rego at PR time and the Resource Graph verifier at deploy time; OIDC + RG-scoped identities exist for all three environments; freeze state and audit emission are operable. **All user-story phases may now begin in parallel.**

---

## Phase 3: User Story 1 — Sub-Hour Lead Time via Trunk-Based Auto-Promotion (Priority: P1) 🎯 MVP

**Goal**: Merging a low-risk change to `main` reaches 100 % of production traffic within 60 minutes with no human intervention and the lead-time metric is recorded.

**Independent Test**: Merge a copy update on a non-safety-critical page; observe full prod rollout < 60 min and lead-time metric in dashboard. (spec line 37)

### Tests for User Story 1

- [ ] T029 [P] [US1] Write integration test `tests/pipeline/integration/test_lead_time_metric.py` asserting that after a synthetic merge, an audit event of `action: deploy.completed` with `env: production` and `result: success` is emitted within 60 minutes wall-clock and that a `lead_time_seconds` field is present and ≤ 3600
  - **Agents**: `qa-test-engineer`, `sre-engineer`
  - **Tools**: `edit`, `execute`
  - **Success**: Test fails until T031–T033 land; passes after — verified via a dry-run on the dev environment using a no-op merge.

### Implementation for User Story 1

- [ ] T030 [US1] Implement `tools/pipeline/src/pipeline_tools/lead_time.py` providing `record_merge(commit_sha)` and `record_prod_complete(commit_sha)` which together compute and emit the `lead_time_seconds` audit field; persist intermediate state in `pipeline_state` container `lead-time` document keyed by commit SHA
  - **Agents**: `software-developer`, `sre-engineer`
  - **Tools**: `edit`
  - **Success**: Round-trip test in `tests/pipeline/unit/test_lead_time.py` (write in same task) confirms metric computed from the difference of the two timestamps and round-trips through audit emitter.

- [ ] T031 [US1] Author `.github/workflows/cd.yml` `on: push: branches: [main]` job graph `gates → build → staging-deploy → staging-gate-set → prod-canary-5 (10 min window) → prod-canary-25 (15 min) → prod-canary-50 (30 min) → prod-canary-100 (60 min)` per FR-006 / FR-007 using reusable composite actions from Phase 1; the `staging-gate-set` job is the reusable workflow defined by **T079a** (Phase 13) and runs the **full e2e suite, the 5-min load smoke at documented burst targets, and the chaos-lite scenario (one external-feed outage + one data-store partition)**; each canary transition calls `canary-controller decide` (US4) AND `posture-verifier` (Phase 2); a non-zero `posture-verifier` result on staging or production dispatches `repository_dispatch: slo-burn` with `reason: posture-failure` to trigger T049 rollback (FR-031); on success calls `lead_time.record_prod_complete`
  - **Agents**: `infrastructure-devops`, `sre-engineer`, `software-developer`, `principal-engineer`, `chaos-engineer`
  - **Tools**: `edit`, `read` (`research.md` R2/R3/R4), `agent` (`sre-engineer` for observation windows; `chaos-engineer` for chaos-lite scenarios; `principal-engineer` for job graph)
  - **Success**: `actionlint .github/workflows/cd.yml` exits 0; a dry-run via `gh workflow run cd.yml --ref main -f dry-run=true` walks **all four canary stages** (5/25/50/100); the no-op merge test from T029 produces `lead_time_seconds` ≤ 3600; an injected posture failure causes a `slo-burn` dispatch with `reason: posture-failure` within 60 s.

- [ ] T032 [US1] Configure Container Apps revision-mode multiple in `infra/bicep/modules/container-app.bicep` so that production weight splits 5/95, 25/75, 50/50, 100/0 are achievable via `az containerapp ingress traffic set` (per FR-007 four-stage canary); thread the same change into `apps/api` and `apps/agents` modules
  - **Agents**: `infrastructure-devops`, `azure-principal-architect`, `docker-container-engineer`
  - **Tools**: `edit`, `web` (Microsoft Learn — Container Apps traffic splitting), `agent` (`azure-principal-architect` to validate revision mode + zone redundancy interplay)
  - **Success**: `bicep build` exits 0; `az containerapp revision list` after a What-If shows two revisions can coexist; weight commands succeed in a sandbox env.

- [ ] T033 [P] [US1] Configure `apps/web` (Next.js on App Service slot) staged-slot swap with the **same four-stage canary as Container Apps (5 → 25 → 50 → 100 %)** per FR-010, using App Service traffic routing rules between `staging` and `production` slots; each stage MUST evaluate the same SLO burn-rate criteria as the API tier before advancing (FR-010)
  - **Agents**: `infrastructure-devops`, `software-developer`, `azure-principal-architect`, `sre-engineer`
  - **Tools**: `edit`, `web` (App Service slot swap + `Sites/slots/config/web` traffic routing rules)
  - **Success**: Bicep + workflow snippet pass `actionlint`/`bicep build`; sandbox ramp walks all four stages; smoke endpoint returns 200 throughout; `canary-controller decide` is invoked at every stage transition with the web SLO signals.

- [ ] T034 [US1] Add three KPI tiles (Azure Workbook JSON) under `infra/observability/workbook-pipeline-kpis.json` per FR-020 — each on a rolling 30-day basis sourced from the `audit` Cosmos container: (a) **lead-time** p50/p90, (b) **change-failure-rate** = `count(deploy.rolledback ∪ deploy.aborted ∪ deploy.emergency) / count(deploy.completed)`, (c) **MTTR** = mean(`deploy.recovered.timestamp − deploy.failure.timestamp`) per affected revision
  - **Agents**: `sre-engineer`, `infrastructure-devops`, `ux-designer`
  - **Tools**: `edit`, `web` (Workbooks Cosmos data-source docs), `agent` (`ux-designer` for at-a-glance layout; `sre-engineer` to confirm CFR/MTTR formulae)
  - **Success**: Workbook deploys via `az monitor app-insights workbook create`; sample 7-day queries populate all three tiles using events from T029 + simulated rollback/recovery events; SC-003 (CFR < 15 %) and SC-004 (MTTR < 30 min) become measurable from the tiles.

**Checkpoint US1**: Merge → prod in < 60 min on a no-op change, verified end-to-end. Lead-time metric persisted and visible. MVP scope is testable.

---

## Phase 4: User Story 2 — Build-Once Signed Artefact with Verified Provenance (Priority: P1)

**Goal**: A single immutable artefact (digest, signature, SBOM, SLSA-3 provenance) is produced once per merge and identically promoted across staging and every production canary stage. (spec lines 48–63)

**Independent Test**: Inspect two consecutive deployments — digest, signature, SBOM hash, and provenance attestation must be identical across staging and all prod canary stages.

### Tests for User Story 2

- [ ] T035 [P] [US2] Contract test `tests/pipeline/contract/test_artefact_immutability.py` asserts that for a given commit SHA, `cosign verify`, `cosign verify-attestation --type slsaprovenance`, and SBOM SHA-256 match across the staging deploy and all three canary stages by reading the audit events emitted in each stage
  - **Agents**: `qa-test-engineer`, `security-engineer`
  - **Tools**: `edit`, `execute`
  - **Success**: Test fails when an artefact is rebuilt mid-flow; passes when the same digest is reused.

### Implementation for User Story 2

- [ ] T036 [US2] Add `build` job to `.github/workflows/cd.yml` (or extract to `.github/workflows/_reusable/build-once.yml`) that produces, per FR-004, **both deployable artefact kinds**: (1) one OCI image per runtime to `acr-ama-prod.azurecr.io/{api|agents|web}:sha-${GITHUB_SHA}`, AND (2) one **infrastructure bundle** (`infra/**` packaged as an OCI artefact `acr-ama-prod.azurecr.io/infra-bundle:sha-${GITHUB_SHA}` via `oras push`); for **every** artefact (image + infra bundle) emit (a) Syft SBOM (SPDX + CycloneDX), (b) Cosign keyless signature, (c) SLSA-3 provenance attestation via `slsa-framework/slsa-github-generator`; outputs the digest list (containing both image and infra-bundle digests) as a job output
  - **Agents**: `infrastructure-devops`, `security-engineer`, `docker-container-engineer`, `software-developer`
  - **Tools**: `edit`, `web` (SLSA generator usage, Cosign keyless, `oras push` for OCI artefacts), `agent` (`docker-container-engineer` to validate base-image pinning and multi-stage layout)
  - **Success**: `actionlint` passes; running the job on a test branch produces in ACR one tag per runtime AND one infra-bundle tag, each with all four attestations; `cosign verify` exits 0 for both image AND infra-bundle digests; T037 / T039 verifier consume the infra-bundle digest before any `az deployment group create`.

- [ ] T037 [US2] Modify all downstream deploy jobs in `cd.yml` to consume the `build` job's `digests` output rather than re-computing tags; pass `--image @sha256:…` (digest-pinned) to `az containerapp update` and `az webapp config container set`; fail-fast if any deploy job derives a tag from `${{ github.sha }}` directly
  - **Agents**: `infrastructure-devops`, `principal-engineer`
  - **Tools**: `edit`, `search` (`grep -n 'github.sha' .github/workflows/cd.yml`), `execute`
  - **Success**: `grep -n 'github.sha' .github/workflows/cd.yml` returns matches only inside the `build` job and the audit emit step; `actionlint` clean.

- [ ] T038 [P] [US2] Implement `tools/pipeline/src/pipeline_tools/artefact_verifier.py` with `verify(digest)` that runs `cosign verify` + `cosign verify-attestation` + SBOM SHA match against the digest recorded in `pipeline_state`'s `artefact:{sha}` document; expose CLI `artefact-verifier verify --sha <git-sha>`
  - **Agents**: `software-developer`, `security-engineer`
  - **Tools**: `edit`, `web` (Cosign API), `execute`
  - **Success**: CLI returns 0 on a freshly built artefact; non-zero with reason on a tampered SBOM.

- [ ] T039 [US2] Insert `artefact-verifier verify --sha <sha>` as a *first* step in `staging-deploy`, `prod-canary-5`, `prod-canary-25`, `prod-canary-100`; on failure emit audit `action: deploy.aborted` with `result: artefact-tamper`
  - **Agents**: `infrastructure-devops`, `security-engineer`
  - **Tools**: `edit`, `execute`
  - **Success**: A deliberate test fixture that flips one byte of the SBOM aborts the workflow at the next stage with the correct audit event written.

**Checkpoint US2**: Build-once-promote-the-digest is enforced by code path AND by automated verification gate at every stage transition.

---

## Phase 5: User Story 3 — Comprehensive PR Quality Gates Within a 10-Minute Budget (Priority: P1)

**Goal**: Every PR runs unit + integration + contract tests, OPA posture checks, secret scan, SAST, dependency scan, and Bicep What-If; median wall-clock from PR open to gate completion ≤ 10 min; deliberately bad changes (vuln, posture violation) are blocked. (spec lines 65–80)

**Independent Test**: Submit representative PRs (Python, TypeScript, Bicep, safety-critical path, deliberate vuln) — all gates run; median time ≤ 10 min; bad PRs blocked.

### Tests for User Story 3

- [ ] T040 [P] [US3] Integration test `tests/pipeline/integration/test_pr_gate_budget.py` opens five synthetic PRs via `gh pr create` (one per representative type) and asserts: (a) each gate job ran, (b) median total time ≤ 10 min computed from `gh run list --json`, (c) the deliberately-bad PRs failed at the expected gate
  - **Agents**: `qa-test-engineer`, `sre-engineer`
  - **Tools**: `edit`, `execute`
  - **Success**: Test runs only when invoked manually with `pytest -m e2e_pr_gates`; passes after T041–T045.

### Implementation for User Story 3

- [ ] T041 [US3] Author `.github/workflows/ci.yml` (replacing the existing one if present — read first) per FR-001 with parallel jobs covering **all 14 spec-mandated gate categories**: `lint`, `typecheck` (mypy + tsc --noEmit), `unit-tests-py`, `unit-tests-web`, `contract-tests`, `integration-tests`, `simulation-tests` (signal → incident → recommendation → alert end-to-end fixture), `a11y-audit` (axe-core + Pa11y per Constitution V), `benchmark` (locust smoke), `bicep-whatif`, `opa-posture`, `opa-cross-env`, `opa-foundry-carveout`, `secret-scan` (gitleaks), `sast` (Semgrep), `dep-scan` (Dependabot review action + `pip-audit`/`npm audit`), `container-scan` (Trivy on every image built in PR); each job pinned to a SHA-pinned action and uses path filters to skip when irrelevant
  - **Agents**: `infrastructure-devops`, `qa-test-engineer`, `security-engineer`, `software-developer`, `accessibility-tester`
  - **Tools**: `read` (existing `.github/workflows/ci.yml`), `edit`, `web` (latest action SHAs, axe-core/Pa11y CI usage), `agent` (`qa-test-engineer` to confirm test job split; `accessibility-tester` to confirm a11y rule set)
  - **Success**: `actionlint` passes; on a sample PR the workflow runs in < 10 min p50 measured across 5 runs; **all 14 categories appear as required status checks** matching FR-001.

- [ ] T042 [P] [US3] Add `bicep-whatif` job that runs `az deployment group what-if` against a throwaway RG `rg-ama-pr-${{ github.event.number }}` (auto-deleted in cleanup job), saves the JSON output as an artefact, then passes it to a `conftest test` step against `infra/policy/rego/`
  - **Agents**: `infrastructure-devops`, `security-engineer`
  - **Tools**: `edit`, `web` (What-If JSON schema)
  - **Success**: Sample bad PR (public Cosmos in staging) produces a What-If that triggers the OPA `deny` from T014.

- [ ] T043 [P] [US3] Add `safety-critical-path` job that detects PRs touching paths under `apps/api/app/api/routes/incident*`, `apps/agents/incident*`, or `apps/web/src/app/incidents/**` and requires an additional review by the incident-domain CODEOWNER (`@johnbilliris` under user-owned-repo mode per ADR-029-01; substitute `@org/incident-domain-codeowners` on org migration) plus passing of the heavier `tests/integration/incident-*` suite
  - **Agents**: `qa-test-engineer`, `security-engineer`, `principal-engineer`
  - **Tools**: `edit`, `search` (existing CODEOWNERS)
  - **Success**: A PR that adds a comment to `apps/api/app/api/routes/incidents.py` triggers the additional review requirement; a PR that only changes `apps/web/src/app/about/page.tsx` does not.

- [ ] T044 [P] [US3] Configure repo-level branch protection on `main`: require all CI checks above + dual reviewers for any change to `infra/policy/posture-matrix.yaml` or `infra/policy/posture-exceptions.yaml`; **add `infra/**` to `.github/CODEOWNERS` requiring infrastructure CODEOWNER review on any infrastructure change (Constitution Quality Gates "What-If / Plan review") — under the current user-owned repository the handle is `@johnbilliris` per ADR-029-01, to be substituted with `@org/infrastructure-codeowners` on org migration**; disallow merge commits (squash only)
  - **Agents**: `infrastructure-devops`, `security-engineer`, `compliance-auditor`
  - **Tools**: `execute` (`gh api repos/:owner/:repo/branches/main/protection -X PUT …`), `edit` (`.github/CODEOWNERS`, snapshot in `infra/IDENTITY.md`)
  - **Success**: `gh api repos/:owner/:repo/branches/main/protection` returns required check list matching the CI job names; CODEOWNERS shows `infra/** @johnbilliris` (or `@org/infrastructure-codeowners` once migrated); a PR touching `infra/bicep/main.bicep` requires the infrastructure CODEOWNER's review.

- [ ] T045 [US3] Add `gate-budget-monitor` job (FR-002 / SC-002) that posts to the PR a comment with each gate's wall-clock and a 30-day **p50 + p95** trend retrieved from the audit store; if **p50 > 10 min OR p95 > 15 min** over the trailing 7 days, it labels the PR `pipeline-budget-breach` and pings the SRE CODEOWNER (`@johnbilliris` per ADR-029-01; restore `@org/sre-codeowners` on org migration)
  - **Agents**: `sre-engineer`, `software-developer`
  - **Tools**: `edit`, `execute`, `agent` (`sre-engineer` to validate the budget alerting threshold and label scheme)
  - **Success**: A synthetic PR receives the comment showing both p50 and p95; deliberately slowing one job past 10 min p50 OR past 15 min p95 on three consecutive PRs adds the label.

**Checkpoint US3**: Every PR exercises every gate; median ≤ 10 min; bad PRs are blocked with cited rules; budget breaches are visible.

---

## Phase 6: User Story 4 — SLO Burn-Rate Auto-Promotion and Auto-Rollback (Priority: P2)

**Goal**: Fast-burn breach during a canary triggers automated rollback to the previous known-good revision within 5 minutes of the initial breach. (spec lines 82–98)

**Independent Test**: Inject latency in 5 % canary; observe fast-burn alert + auto-rollback completes ≤ 5 min from breach.

### Tests for User Story 4

- [ ] T046 [P] [US4] Integration test `tests/pipeline/integration/test_burn_rate_rollback.py` simulates a fast-burn alert payload and asserts `canary_controller.decide(...)` returns `decision: rollback`, `target: <previous-known-good>` and that `record_rollback(...)` writes the audit `action: deploy.rolledback` within 5 min of the simulated breach; additional cases cover **slow-burn (decision = hold + opens issue labelled `slow-burn-pause` routed to the SRE CODEOWNER — `@johnbilliris` under ADR-029-01, `@org/sre-codeowners` after org migration — per FR-009)** and **telemetry-unavailable (decision = hold + opens issue labelled `telemetry-unavailable` per FR-024)**; finally a case covers **posture-failure dispatch from T031** producing `decision: rollback, reason: posture-failure`
  - **Agents**: `qa-test-engineer`, `sre-engineer`
  - **Tools**: `edit`, `execute`
  - **Success**: ≥9 cases (fast-burn, slow-burn-with-issue-label, **telemetry-unavailable-with-issue-label**, no-burn, freeze-active, no-prior-known-good, multi-error-budget, **posture-failure-rollback**, **author-not-self-approver-rejection cross-link**); passes after T047–T049.

### Implementation for User Story 4

- [ ] T047 [US4] Implement `tools/pipeline/src/pipeline_tools/canary_controller.py` per `contracts/canary-promotion.api.md` and FR-007 / FR-008 / FR-009 / FR-024: `decide(env, current_stage, observation_window_min, slo_signals)` returns `promote|hold|rollback` with rationale; encode the spec-mandated **per-stage observation windows (10/15/30/60 min for stages 5/25/50/100)** and **minimum-sample threshold per service**; cover decision branches `fast-burn → rollback`, `slow-burn → hold + open slow-burn-pause issue`, **`telemetry-unavailable → hold at current stage + open telemetry-unavailable issue (FR-024)`**, `posture-failure → rollback`, `freeze-active → hold`, `no-prior-known-good → hold + page SRE`; `record_rollback(env, target_digest, reason)` performs `az containerapp ingress traffic set` + audit emit
  - **Agents**: `software-developer`, `sre-engineer`, `infrastructure-devops`
  - **Tools**: `edit`, `read` (`contracts/canary-promotion.api.md`), `agent` (`sre-engineer` to validate burn-rate windows + telemetry-unavailable hold semantics)
  - **Success**: Unit + integration tests in `tests/pipeline/unit/test_canary_controller.py` (write in same task) cover **all six decision branches**; CLI `canary-controller decide --env production --stage 50 --window 30` returns the expected JSON; injecting an empty `slo_signals` payload returns `decision: hold, reason: telemetry-unavailable`.

- [ ] T048 [US4] Define the **five spec-mandated SLO signals from FR-007** in `infra/observability/slo-signals.yaml` — `availability`, `api_latency_p95`, `dashboard_load_p95`, `signal_freshness`, `recommendation_correctness` — each with target, fast-burn window (5 % of error budget in 1 h), slow-burn window (10 % in 6 h); **also author `infra/observability/min-samples.yaml` declaring per-service × per-signal minimum-sample thresholds (e.g., `api/availability: 1000 requests`, `api/api_latency_p95: 500 requests`, `web/dashboard_load_p95: 200 page-loads`, `agents/recommendation_correctness: 50 decisions`, `ingestion/signal_freshness: 300 ingestion-cycles`) consumed by `canary_controller.decide` so windows below threshold yield `decision: hold, reason: insufficient-samples`**; provision Azure Monitor metric alerts (one per signal × env) and an Alert webhook routing to the workflow `repository_dispatch` event `slo-burn`; emit a `telemetry-unavailable` event when a signal stops reporting for > 5 min
  - **Agents**: `sre-engineer`, `infrastructure-devops`, `azure-principal-architect`
  - **Tools**: `edit`, `web` (Azure Monitor alert webhook → GH dispatch), `agent` (`azure-principal-architect` for alert design; `sre-engineer` to validate signal definitions AND per-service min-sample thresholds match SLO doc)
  - **Success**: Bicep deploy provisions all 5 × 2 = 10 alerts (staging + prod); firing a synthetic alert in sandbox triggers the GH `repository_dispatch`; `canary_controller` receives the payload and returns the correct decision; muting a signal for > 5 min produces a `telemetry-unavailable` dispatch; **a canary stage entered with sample count below the `min-samples.yaml` threshold returns `decision: hold, reason: insufficient-samples` rather than promoting**.

- [ ] T049 [US4] Wire a new workflow `.github/workflows/canary-rollback.yml` triggered on `repository_dispatch: slo-burn`; the workflow checks freeze state, calls `canary_controller decide`, executes the rollback if returned, and emits audit events; targets the *previous known-good* digest selected per SQL in `contracts/canary-promotion.api.md`
  - **Agents**: `infrastructure-devops`, `sre-engineer`
  - **Tools**: `edit`, `execute`, `read` (`contracts/canary-promotion.api.md`)
  - **Success**: `actionlint` clean; sandbox simulation injects latency, alert fires, traffic returns to previous revision in < 5 min wall-clock; audit shows `deploy.rolledback` with rationale referencing the alert id.

**Checkpoint US4**: Burn-rate triggered rollback works end-to-end in sandbox; previous known-good is selected deterministically.

---

## Phase 7: User Story 5 — Immutable Evidence Pack and Unified Audit Trail (Priority: P2)

**Goal**: Every prod promotion produces, within 5 min, an immutable evidence pack in AU storage with legal hold; pack hash recorded in audit store with same schema as incident events; tamper attempts denied. (spec lines 100–115)

**Independent Test**: Trigger prod promotion; pack appears within 5 min, all contents retrievable, hash recorded in audit, modify/delete denied.

### Tests for User Story 5

- [ ] T050 [P] [US5] Contract test `tests/pipeline/contract/test_evidence_pack_schema.py` against `contracts/evidence-pack.schema.json`: required content kinds present, manifest hash matches recomputed hash, AU region required
  - **Agents**: `qa-test-engineer`, `compliance-auditor`
  - **Tools**: `edit`, `execute`
  - **Success**: ≥7 cases; passes after T051.

- [ ] T051 [P] [US5] Integration test `tests/pipeline/integration/test_evidence_pack_immutability.py` uploads a sample pack, writes audit, then attempts `az storage blob delete` and `az storage blob upload --overwrite` against the pack — both must fail with `BlobImmutableDueToPolicy` / `BlobImmutableDueToLegalHold`
  - **Agents**: `qa-test-engineer`, `security-engineer`, `compliance-auditor`
  - **Tools**: `edit`, `execute`
  - **Success**: Both negative operations error with the expected codes against a sandbox container with immutability ON.

### Implementation for User Story 5

- [ ] T052 [US5] Implement `tools/pipeline/src/pipeline_tools/evidence_packer.py` that collects `(workflow_run_log, sbom, cosign_signature, slsa_provenance, posture_verifier_report, what_if_json, opa_decisions, slo_dashboard_snapshot, approver_list, audit_event_window)`, builds a manifest per `evidence-pack.schema.json`, computes SHA-256 of the canonicalised manifest, uploads to Blob with `--immutability-period-days 2555 --legal-hold true`, then calls `audit_emitter.emit({action:"evidence.pack.created", artefact:{hash:..., uri:...}})`
  - **Agents**: `software-developer`, `security-engineer`, `compliance-auditor`, `data-engineer`
  - **Tools**: `edit`, `read` (`contracts/evidence-pack.schema.json`), `agent` (`compliance-auditor` to confirm content list satisfies regulator expectations)
  - **Success**: CLI `evidence-packer pack --run-id <id>` produces a pack in sandbox container in < 5 min from prod-canary-100 success; subsequent `az storage blob delete` returns the expected immutability error; manifest validates against the schema.

- [ ] T053 [US5] Add `evidence-pack` job at the end of `cd.yml` `prod-canary-100` (and at the end of `canary-rollback.yml` for rollback events) that calls `evidence-packer pack --run-id ${{ github.run_id }}`; on failure marks the deploy `result: incomplete-evidence` and pages the compliance CODEOWNER (`@johnbilliris` per ADR-029-01; restore `@org/compliance-codeowners` on org migration)
  - **Agents**: `infrastructure-devops`, `compliance-auditor`, `sre-engineer`
  - **Tools**: `edit`, `execute`
  - **Success**: A successful prod canary run leaves a pack in storage and a matching audit event within 5 minutes.

- [ ] T054 [P] [US5] Implement helper CLI `evidence-packer fetch --run-id <id> --out <dir>` that downloads the pack and verifies the manifest hash before extraction; document in `quickstart.md` flow #6
  - **Agents**: `software-developer`, `compliance-auditor`
  - **Tools**: `edit`
  - **Success**: Round-trip from `pack` then `fetch` reproduces every content item; hash mismatch on a tampered local copy raises a clear error.

**Checkpoint US5**: Evidence packs auto-produced, immutable, fetchable, and audit-linked end-to-end.

---

## Phase 8: User Story 6 — Incident-Mode Change Freeze with Emergency-Hotfix Lane (Priority: P2)

**Goal**: Incident-commander can freeze deploys; normal merges queue; a labelled emergency-hotfix PR with two recorded approvers may deploy; complete evidence pack within 24 h after lift. (spec lines 117–132)

**Independent Test**: Activate freeze; normal merge queues; labelled hotfix with two approvers deploys; evidence pack present within 24 h after lift.

### Tests for User Story 6

- [ ] T055 [P] [US6] Integration test `tests/pipeline/integration/test_change_freeze.py` toggles freeze ON, posts a synthetic merge to `main`, asserts the `cd.yml` run reaches the `freeze-check` step and queues; toggles OFF and asserts the queued run resumes
  - **Agents**: `qa-test-engineer`, `sre-engineer`
  - **Tools**: `edit`, `execute`
  - **Success**: Round-trip works in sandbox; audit shows `change-freeze.activated` and `change-freeze.lifted` events tied to the right actor.

- [ ] T056 [P] [US6] Integration test `tests/pipeline/integration/test_emergency_hotfix.py` opens a PR with label `emergency-hotfix`, two approvers from `ama-emergency-approver` group, and asserts the hotfix workflow deploys to prod even with freeze ON, then evidence pack appears within 24 h
  - **Agents**: `qa-test-engineer`, `security-engineer`, `compliance-auditor`
  - **Tools**: `edit`, `execute`
  - **Success**: Hotfix deploy succeeds; audit emits `deploy.emergency` with `approvers:[…]`; pack appears.

### Implementation for User Story 6

- [ ] T057 [US6] Add `freeze-check` step at the head of every deploy job in `cd.yml` and `canary-rollback.yml` that calls `freeze-controller status --env <env>` and exits the workflow with status `queued` (re-runnable on freeze lift) if frozen — except when `${{ github.event.pull_request.labels.*.name == 'emergency-hotfix' }}` is true
  - **Agents**: `infrastructure-devops`, `sre-engineer`
  - **Tools**: `edit`
  - **Success**: A merge during freeze is queued; an `emergency-hotfix` PR bypasses the gate.

- [ ] T058 [US6] Author `.github/workflows/emergency-hotfix.yml` triggered by `pull_request: labeled` for `emergency-hotfix`; requires environment `production` reviewers (two approvers from `ama-emergency-approver` per T023+T024); per **FR-011a** the workflow MUST verify, via the GitHub API at deploy time, that the **two approvers are distinct identities AND neither equals the PR author** (rejecting self-approval) and the membership-change audit event was emitted; per **FR-012 / FR-028** the workflow MUST run the **emergency gate set** — all of `lint`, `typecheck`, `unit`, `contract`, `sast`, `secret-scan`, `dep-scan`, `container-scan`, `bicep-whatif`, `opa-posture`, `opa-cross-env`, `opa-foundry-carveout`, signature/SBOM/provenance verification, and CODEOWNERS reviews — before fast-tracking; only long-running gates (full integration, simulation, a11y full sweep, load smoke, chaos-lite) may be deferred and MUST be reconciled into the evidence pack within 24 h; fast-track build → prod-canary-25 → prod-canary-50 → prod-canary-100 (may skip 5 % only); always emits `action: deploy.emergency` with the labelled-by actor and both approvers
  - **Agents**: `infrastructure-devops`, `security-engineer`, `compliance-auditor`, `incident-commander` (operational), `sre-engineer`
  - **Tools**: `edit`, `agent` (`incident-commander` operational agent to validate approver workflow against AIIMS; `compliance-auditor` to confirm gate set list)
  - **Success**: Sandbox dry-run with two distinct approvers from the right group succeeds; with one approver missing → env protection blocks; **with the PR author attempting to be one of the two approvers → workflow self-aborts with `result: self-approval-rejected`**; **with `opa-posture` or `bicep-whatif` failing → workflow blocks even on emergency lane**; audit event records both approvers and the deferred-gate list.

- [ ] T059 [P] [US6] Add scheduled `evidence-pack-backfill.yml` (`schedule: cron: '0 */6 * * *'`) that scans for any `deploy.emergency` event in the last 24 h whose `evidence.pack.created` follow-up is missing and forces a pack creation against the recorded run; pages the compliance CODEOWNER (`@johnbilliris` per ADR-029-01; restore `@org/compliance-codeowners` on org migration) if any backfill fails
  - **Agents**: `compliance-auditor`, `infrastructure-devops`, `sre-engineer`
  - **Tools**: `edit`
  - **Success**: A simulated emergency deploy that suppresses the inline pack step is recovered by the next backfill run within 24 h.

**Checkpoint US6**: Freeze gates normal flow; labelled hotfix with dual approval bypasses; evidence is guaranteed within 24 h.

---

## Phase 9: User Story 8 — Environment-Tiered Infrastructure Posture (Priority: P2)

**Goal**: Same Bicep produces dev (public + key allowed) vs staging/production (private + MI/OIDC only); dev resources non-confusable with regulated envs. (spec lines 151–168)

**Independent Test**: Deploy same stack to dev/staging/prod; confirm posture differences and naming/tagging isolation.

### Tests for User Story 8

- [ ] T060 [P] [US8] Integration test `tests/pipeline/integration/test_env_tiered_posture.py` (FR-025 / FR-027) runs `bicep build` + `az deployment what-if` against each env's parameter file and asserts: dev Storage shows `publicNetworkAccess: Enabled`; staging+prod show `Disabled`; staging+prod Cosmos shows `disableLocalAuth: true`; tags and names differ between envs
  - **Agents**: `qa-test-engineer`, `security-engineer`, `infrastructure-devops`
  - **Tools**: `edit`, `execute`
  - **Success**: Test passes deterministically against parameter files written in T061.

### Implementation for User Story 8

- [ ] T061 [US8] Author / update `infra/parameters/dev.bicepparam`, `staging.bicepparam`, `production.bicepparam` (FR-026 / FR-027) so that the *same* Bicep produces the env-specific posture: dev (`publicNetworkAccess: Enabled`, `disableLocalAuth: false`, `keyExpirationHours: 24`), staging+prod (`publicNetworkAccess: Disabled`, `disableLocalAuth: true`, `keyExpirationHours: 0` — keys disabled)
  - **Agents**: `infrastructure-devops`, `security-engineer`, `compliance-auditor`
  - **Tools**: `edit`, `read` (`posture-matrix.yaml`)
  - **Success**: `bicep build` exits 0 for all three; T060 passes; `posture-verifier` against a sandbox dev RG returns 0 failures.

- [ ] T062 [P] [US8] Update naming and tagging in `infra/bicep/main.bicep` so dev resources carry prefix `dev-` and tag `env=dev,never-prod-bind=true`; staging/prod carry `env=staging|prod,regulated=true` plus an Azure Policy assignment that denies cross-env reference (paired with the OPA cross-env check)
  - **Agents**: `infrastructure-devops`, `security-engineer`, `azure-principal-architect`
  - **Tools**: `edit`, `agent` (`azure-principal-architect` to validate Policy assignment vs duplication of OPA rule)
  - **Success**: `az deployment what-if` shows the tags and names; an Azure Policy `deny` assignment named `ama-cross-env-isolation` is created.

- [ ] T063 [P] [US8] Author developer-key-issuance workflow `.github/workflows/dev-key-issue.yml` per `contracts/dev-key-issue.workflow.md` — issues a 24 h, scoped Cosmos / Storage key into `kv-ama-dev/secrets/devkey-{alias}-{service}` after asserting requester is in `ama-developers` group; emits `action: dev-key.issued`
  - **Agents**: `infrastructure-devops`, `security-engineer`, `software-developer`
  - **Tools**: `edit`, `read` (`contracts/dev-key-issue.workflow.md`)
  - **Success**: Sandbox run with `inputs.alias=jdoe inputs.service=cosmos` deposits the secret with TTL 24 h; non-`ama-developers` user invocation is rejected; audit recorded.

**Checkpoint US8**: Dev / staging / prod posture matches spec Q5/Q6; dev key issuance operable.

---

## Phase 10: User Story 9 — Pipeline-Enforced Posture Boundaries (Priority: P2)

**Goal**: PRs that try to violate the posture matrix (shared-key in staging Cosmos, public network on prod Storage, embedded connection string in prod params, dev-scoped role bound to prod identity) are blocked with a clear cited failure. (spec lines 170–186)

**Independent Test**: Submit four representative bad PRs; all four fail with citations to the posture-matrix rule.

### Tests for User Story 9

- [ ] T064 [P] [US9] Contract tests `tests/pipeline/contract/test_posture_enforcement.py` exercising the four spec acceptance scenarios (a)-(d) by constructing the corresponding What-If JSON and asserting `conftest test` returns the expected deny with the exact `posture-matrix.yaml#…` citation
  - **Agents**: `qa-test-engineer`, `security-engineer`
  - **Tools**: `edit`, `execute`
  - **Success**: All four scenarios fail OPA deterministically; messages include resource id and rule id.

### Implementation for User Story 9

- [ ] T065 [US9] Generate the corresponding Azure Policy initiative `infra/policy/azure-policy/initiative-posture.json` from `posture-matrix.yaml` via a script `tools/pipeline/src/pipeline_tools/policy_generator.py generate-initiative` — one policy per (env × resource family × property) cell with `deny`/`audit` effect aligned to the matrix; assign the initiative to each env's RG via Bicep
  - **Agents**: `infrastructure-devops`, `security-engineer`, `compliance-auditor`, `azure-principal-architect`
  - **Tools**: `edit`, `read`, `agent` (`azure-principal-architect` to validate initiative composition vs MS built-ins)
  - **Success**: `policy-generator generate-initiative` produces deterministic JSON; `bicep build` of assignments exits 0; What-If shows the initiative bound to all three RGs.

- [ ] T066 [P] [US9] Implement scheduled `infra/policy/auto-sweep-exceptions.yml` workflow (`schedule: cron: '0 6 * * *'`) that opens a PR removing any entry in `posture-exceptions.yaml` whose `expires_at` is past, and labels the PR `posture-exception-expiry`; PR auto-merges if the only change is removal of expired entries
  - **Agents**: `security-engineer`, `compliance-auditor`, `infrastructure-devops`
  - **Tools**: `edit`, `execute`
  - **Success**: A test exception entry with `expires_at` in the past is removed by the scheduled run on the next cycle; PR carries the label and merges automatically once CI is green.

- [ ] T067 [P] [US9] Add `posture-exception-pr` validation step in `ci.yml` that, for any PR modifying `infra/policy/posture-exceptions.yaml`, requires (a) approvals from both security and compliance CODEOWNERS, (b) every new entry has `expires_at` ≤ today + 90 days, (c) every entry validates against `contracts/posture-exceptions.schema.yaml`
  - **Agents**: `security-engineer`, `compliance-auditor`
  - **Tools**: `edit`
  - **Success**: A PR with a 120-day exception fails with a clear message; a 60-day exception with both approvers passes.

**Checkpoint US9**: Posture matrix is enforced at three layers (PR OPA, Azure Policy at runtime, scheduled exception sweep) with unified citations.

---

## Phase 11: User Story 7 — Continuous Drift Detection and OIDC-Only Identity (Priority: P3)

**Goal**: No long-lived cloud secrets exist; nightly drift detection labels issues with the specific property and resource that drifted. (spec lines 134–149)

**Independent Test**: (a) Audit shows no cloud secrets in repo or workflows. (b) Manually mutate an Azure resource; next nightly run files a labelled issue.

### Tests for User Story 7

- [ ] T068 [P] [US7] Repo audit script `tools/pipeline/src/pipeline_tools/secret_audit.py` (FR-016) plus integration test `tests/pipeline/integration/test_no_long_lived_secrets.py` that runs `gh secret list`, `gh actions-secret list` (per env), and a `gitleaks` scan of the workflow files; asserts every Azure-related secret is OIDC-only (no `AZURE_CREDENTIALS`, no client-secret entries)
  - **Agents**: `qa-test-engineer`, `security-engineer`
  - **Tools**: `edit`, `execute`
  - **Success**: Audit returns 0 findings; test passes; if a long-lived secret is present, the test names which secret and environment.

- [ ] T069 [P] [US7] Integration test `tests/pipeline/integration/test_drift_detection_issue.py` writes a fake Resource Graph delta to `pipeline_state` `drift-finding`, runs the issue-filer step, and asserts an issue is opened with label `drift`, body containing `resource_id` and `property`
  - **Agents**: `qa-test-engineer`, `infrastructure-devops`
  - **Tools**: `edit`, `execute`
  - **Success**: Synthetic drift produces a properly labelled issue.

### Implementation for User Story 7

- [ ] T070 [US7] Read existing `.github/workflows/drift-detection.yml`; replace any long-lived auth with OIDC (FR-019); add a step that calls `posture-verifier` and a step that diffs current Resource Graph state vs the last known IaC state stored in `pipeline_state` `iac-snapshot` document; for each diff open / update a GitHub issue labelled `drift` and emit audit `action: drift.detected`
  - **Agents**: `infrastructure-devops`, `security-engineer`, `software-developer`, `sre-engineer`
  - **Tools**: `read`, `edit`, `execute`
  - **Success**: Sandbox tampering produces an issue with the property name; OIDC is the only identity used.

- [ ] T071 [P] [US7] Sweep all workflows in `.github/workflows/` for `AZURE_CREDENTIALS`, `client-secret`, `password:` patterns; replace with OIDC composite from T005; document deprecated secrets to delete via `gh secret delete`
  - **Agents**: `security-engineer`, `infrastructure-devops`
  - **Tools**: `search` (`grep -rn 'AZURE_CREDENTIALS\|client-secret\|password:' .github/workflows/`), `edit`, `execute`
  - **Success**: Search returns zero matches; `gh secret list` shows no Azure long-lived secrets; T068 passes.

**Checkpoint US7**: OIDC-only across all workflows; drift findings are labelled, actor-attributed, and visible.

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, hardening, and end-to-end validation across all stories.

- [ ] T072 [P] Update `.github/copilot-instructions.md` to describe the new `tools/pipeline/` package, the canonical posture-matrix workflow, and the dev-key-issuance flow (preserving manual sections between markers)
  - **Agents**: `principal-engineer`, `software-developer`
  - **Tools**: `edit`, `execute` (`pwsh .specify/scripts/powershell/update-agent-context.ps1 -AgentType copilot` if marker-driven)
  - **Success**: File updated; new contributor can read the file and understand pipeline package and posture flow.

- [ ] T073 [P] Update root `README.md` and `docs/operations/runbook.md` (or create) with the seven `quickstart.md` flows, links to `evidence-packer fetch`, and the freeze toggle commands
  - **Agents**: `principal-engineer`, `sre-engineer`, `compliance-auditor`
  - **Tools**: `edit`, `read` (`quickstart.md`)
  - **Success**: Runbook covers each flow; on-call SRE can find the freeze command in < 30 s.

- [ ] T074 [P] Add `tools/pipeline` to root pre-commit / lint pipeline so that `ruff`/`mypy`/`pytest tests/pipeline -q` runs on every PR touching `tools/pipeline/**` or `infra/policy/**`
  - **Agents**: `software-developer`, `qa-test-engineer`
  - **Tools**: `edit`, `execute`
  - **Success**: PR touching `tools/pipeline/src/pipeline_tools/posture_matrix.py` triggers the new lint job; PR not touching it does not.

- [ ] T075 [P] Run `.specify/scripts/powershell/check-prerequisites.ps1` and the speckit analyze prompt; resolve any cross-artefact inconsistencies between `spec.md`, `plan.md`, `tasks.md`
  - **Agents**: `product-owner-ba`, `principal-engineer`, `compliance-auditor`
  - **Tools**: `execute`, `agent` (`speckit.analyze` agent)
  - **Success**: Analyze report has no MUST findings; all SHOULD findings have a recorded decision.

- [ ] T076 Run end-to-end validation per `quickstart.md`: walk all 7 flows in a sandbox tenant; capture the resulting evidence pack and attach to a `validation-run-029.zip` under `specs/029-progressive-delivery-pipeline/validation/`
  - **Agents**: `qa-test-engineer`, `compliance-auditor`, `sre-engineer`
  - **Tools**: `execute`, `edit`, `agent` (`compliance-auditor` to sign off)
  - **Success**: All 7 flows pass; evidence pack passes schema validation; compliance-auditor agent's review produces no blocking findings.

- [ ] T077 Run the spec's success criteria SC-001…SC-N against captured pipeline metrics (lead-time, gate budget, rollback time, evidence-pack latency) over a 7-day soak; record results in `specs/029-progressive-delivery-pipeline/validation/sc-results.md`
  - **Agents**: `sre-engineer`, `qa-test-engineer`, `product-owner-ba`
  - **Tools**: `read` (`spec.md` SC section), `execute`, `edit`
  - **Success**: Each SC has a result column with PASS / FAIL and a query / artefact link; PASS on every P1 / P2 SC; any FAIL has an open issue with remediation owner.

- [ ] T078 [P] Performance review of pipeline state Cosmos container — confirm partition key strategy yields `< 10` RU/s p95 per write under typical merge cadence; tune if needed
  - **Agents**: `data-engineer`, `sre-engineer`, `azure-principal-architect`
  - **Tools**: `execute` (Cosmos metrics), `edit`, `agent`
  - **Success**: Documented baseline RU usage; if > 10 RU/s p95, partition key revisited and migration recorded.

---

## Phase 13: Coverage Remediation (Post-Analyze)

> **Naming convention**: Letter-suffix IDs (`Tnnn{a..z}`, e.g., `T000a`, `T008a`, `T008b`, `T019a`, `T020a`, `T024a`, `T079a`) denote tasks inserted by `/speckit.analyze` remediation passes. Gaps in the numeric sequence (e.g., no plain `T079`) are intentional — the letter suffix preserves traceability back to the analyze report that introduced the task.

**Goal**: Close every gap surfaced by the `/speckit.analyze` consistency report so each Functional Requirement (FR-001 … FR-033) has at least one task that fully satisfies it. Tasks here either supplement edits already made to T031–T058 or introduce new artefacts that no earlier task owned.

### FR-006 Staging Gate Set (resolves analyze C2 / C17)

- [ ] T079a [US1] Implement the **`staging-gate-set` reusable workflow** at `.github/workflows/_reusable/staging-gates.yml` invoked by T031, containing three required jobs: (1) `e2e` — full Playwright + pytest end-to-end suite, (2) `load-smoke` — 5-minute Locust run at the burst targets in `infra/observability/load-targets.yaml` asserting p95 latency ≤ SLO, (3) `chaos-lite` — Toxiproxy / Azure Chaos Studio scenario that injects **one external-feed outage AND one data-store partition** in series and asserts service stays within burn-rate budget; each job emits an audit event `staging-gate.<name>.completed`
  - **Agents**: `qa-test-engineer`, `chaos-engineer`, `sre-engineer`, `infrastructure-devops`
  - **Tools**: `edit`, `web` (Locust + Azure Chaos Studio docs), `agent` (`chaos-engineer` to validate scenario realism; `sre-engineer` for burst targets)
  - **Success**: `actionlint` clean; sandbox run shows all three jobs execute and emit audit events; intentionally regressing a service so p95 latency exceeds SLO causes `load-smoke` to fail and blocks promotion to `prod-canary-5`.

### FR-017 Plaintext-Secret Detection (resolves analyze C5)

- [ ] T080 [P] [US3] Add a **plaintext-secret detection** job to `.github/workflows/ci.yml` that runs (a) `gitleaks` with the existing ruleset, (b) a custom `detect-secrets` scan tuned for connection strings, account keys, JWTs, and PEM blocks, AND (c) a Bicep/Terraform parameter linter that fails on any value resembling a credential (regex set in `infra/policy/secret-detection-rules.yaml`); the job blocks merge and posts a PR comment naming the file + line
  - **Agents**: `security-engineer`, `infrastructure-devops`, `compliance-auditor`
  - **Tools**: `edit`, `web` (`detect-secrets` plugin docs), `agent` (`security-engineer` to ratify rule set)
  - **Success**: PR with a deliberately committed `AccountKey=…` in `infra/parameters/dev.bicepparam` is blocked with a precise comment; PR with no secrets passes; rule set covers `AccountKey`, `SharedAccessKey`, `eyJ` JWT prefix, `-----BEGIN`, and `https://[^/]+:[^@]+@` patterns.

### FR-021 ACR Digest Retention ≥ 3 (resolves analyze C6)

- [ ] T081 [US2] Author `infra/bicep/modules/acr-retention.bicep` that configures **content-trust + retention policy** on `acr-ama-prod` so each repository (`api`, `agents`, `web`, `infra-bundle`) **always retains at least 3 known-good digests** (last 30 days OR last 3 production-promoted digests, whichever is greater) and never garbage-collects a digest referenced by an open audit event with `result: deployed`; emit an alert if retention falls below 3
  - **Agents**: `infrastructure-devops`, `security-engineer`, `azure-principal-architect`, `sre-engineer`
  - **Tools**: `edit`, `web` (ACR retention + image-lock APIs), `agent` (`azure-principal-architect` to validate retention semantics under Premium SKU)
  - **Success**: `bicep build` clean; sandbox ACR shows ≥ 3 retained digests per repo after 5 simulated promotions + 2 simulated rollbacks; an attempt to delete a digest referenced by an open `deployed` audit event is denied; retention-below-3 metric alert fires when forced to 2.

### FR-031 Posture-Verifier → Rollback Wiring (resolves analyze C8 — supplements T031 edit)

- [ ] T082 [P] [US4] Implement `tools/pipeline/src/pipeline_tools/posture_verifier.py::verify_or_dispatch(env, stage, target_digest)` that calls the existing `posture-verifier`; on failure it (a) emits audit event `posture.verify.failed` with full diff, (b) issues `gh api repos/:owner/:repo/dispatches -f event_type=slo-burn -f client_payload='{...,"reason":"posture-failure","target":"<previous-known-good>"}'`, (c) cancels the in-flight `cd.yml` run; covered by integration test `tests/pipeline/integration/test_posture_failure_rollback.py`
  - **Agents**: `software-developer`, `security-engineer`, `sre-engineer`, `infrastructure-devops`
  - **Tools**: `edit`, `execute`, `agent` (`security-engineer` to confirm posture-failure semantics)
  - **Success**: Forcing a private-endpoint mis-configuration on the staging env produces all three side-effects within 60 s; `canary_controller.decide` (T047) receives the dispatch and returns `decision: rollback, reason: posture-failure`.

### FR-032 New-Resource-Type Block (resolves analyze C9)

- [ ] T083 [P] [US9] Add Rego rule `infra/policy/rego/new_resource_type.rego` and matching CI job `opa-new-resource-type` that diffs the **set of `Microsoft.*/*` resource types** present in the latest `az deployment group what-if` JSON against the **keys of `infra/policy/posture-matrix.yaml`**; deny merge if any deployed type is absent from the matrix; the job runs in `ci.yml` after `bicep-whatif`
  - **Agents**: `security-engineer`, `infrastructure-devops`, `compliance-auditor`, `azure-principal-architect`
  - **Tools**: `edit`, `web` (OPA Rego JSONpath against What-If schema), `agent` (`compliance-auditor` to validate enforcement matches FR-032)
  - **Success**: PR introducing `Microsoft.EventGrid/topics` (not in matrix) is blocked with rule citation; adding `Microsoft.EventGrid/topics` to `posture-matrix.yaml` with required posture entries unblocks the same PR.

### FR-022 PR-time Drift / Reconciliation Surfacing (resolves analyze C10)

- [ ] T084 [P] [US3] Add `pr-context` job to `.github/workflows/ci.yml` that queries the Cosmos `audit` container for (a) **open drift alerts** (`drift.detected` events without a closing `drift.reconciled`) and (b) **evidence-pack reconciliation issues** (`evidence.pack.reconciliation.failed` in last 7 d) and posts a PR comment with the counts + links; if the touched paths overlap with a drifting resource, the job blocks merge until the drift is reconciled (FR-022)
  - **Agents**: `software-developer`, `sre-engineer`, `compliance-auditor`
  - **Tools**: `edit`, `execute`, `agent` (`compliance-auditor` to confirm comment template meets evidence reqs)
  - **Success**: Synthetic open-drift on `infra/bicep/modules/cosmos-pipeline-state.bicep` produces a blocking PR comment when that file is touched; non-overlap PRs receive an informational comment only.

### FR-026 Defender for Cloud + Entra ID Protection → Audit Store (resolves analyze C12)

- [ ] T085 [US8] Provision in `infra/bicep/modules/security-alerts-routing.bicep` an Event Grid system topic + subscription that forwards (a) **Defender for Cloud security alerts** (Sub-level) and (b) **Entra ID Protection risky-user / risky-sign-in events** to a Function in `apps/api` (`/internal/security-alert-ingest`) that normalises and writes them into the Cosmos `audit` container with `kind: security-alert`, `source: defender|entra-id-protection`, and the original payload as an attachment in evidence-store
  - **Agents**: `security-engineer`, `infrastructure-devops`, `compliance-auditor`, `azure-principal-architect`
  - **Tools**: `edit`, `web` (Defender alert export + EIP risk-event Graph API), `agent` (`security-engineer` to validate alert taxonomy; `azure-principal-architect` for Event Grid wiring)
  - **Success**: Bicep deploys; firing a synthetic Defender alert in sandbox writes an `audit` document with the right schema within 60 s; firing a synthetic risky-sign-in via Graph API likewise lands in `audit`; both retrievable through evidence-pack `pack` for the corresponding 24 h window.

### FR-023 Standardised Failure-Report Action (resolves analyze C15)

- [ ] T086 [P] Author reusable composite action `.github/actions/failure-report/action.yml` that — when any gate job fails — uploads a structured `failure-report.json` (schema `contracts/failure-report.schema.json`, write in same task) with `gate_name`, `failed_step`, `error_summary`, `links: {logs, actor, evidence_pack_id?}`, posts it as a PR comment, AND emits audit event `gate.failure.reported`; wrap **every** PR gate (T041 jobs) and CD gate (T031, T039, T049, T058) with this action
  - **Agents**: `infrastructure-devops`, `qa-test-engineer`, `compliance-auditor`, `software-developer`
  - **Tools**: `edit`, `execute`, `agent` (`compliance-auditor` to confirm report meets evidence requirements)
  - **Success**: Schema validates with `ajv`; a deliberately broken `unit-tests-py` PR gets a comment pointing to logs + a downloadable `failure-report.json`; the same artefact appears in the evidence pack of the next attempted promotion of that commit.

### Terminology + Issue-Label Hygiene (resolves analyze C18, C19)

- [ ] T087 [P] Run a terminology sweep across `spec.md`, `plan.md`, `tasks.md`, `quickstart.md`, and `contracts/*` so the **first reference per document** uses the full form **"Microsoft Foundry"** and subsequent references may use "Foundry"; commit a `STYLE.md` snippet under `specs/029-progressive-delivery-pipeline/` recording the rule. Also seed `.github/labels/pipeline-029.yml` with the FR-009 issue labels — `slow-burn-pause`, `telemetry-unavailable`, `pipeline-budget-breach`, `posture-failure`, `evidence-pack-reconciliation-failed` — each with a CODEOWNER routing entry in `.github/CODEOWNERS`. **Per ADR-029-01 (research.md §R17): under the current user-owned repository, route ALL five labels to `@johnbilliris`. Once the repository migrates into a GitHub organisation, the routing MUST be substituted to `@org/sre-codeowners` for `slow-burn-pause` / `telemetry-unavailable` / `pipeline-budget-breach`, `@org/security-codeowners` for `posture-failure`, and `@org/compliance-codeowners` for `evidence-pack-reconciliation-failed`** (the future-state mapping table in research.md §R17 is the canonical reference). **Additionally, this sweep MUST close the analyze citation gaps (C12, C13): append literal `(FR-XXX)` parentheticals to every implementing task that currently covers a requirement only by keyword (FR-003, FR-015, FR-018, FR-030 plus any others surfaced by the coverage_check.py invocation in T088); append literal `(SC-XXX)` parentheticals to every task implementing a Success Criterion (SC-005..SC-017 plus any newly added). The sweep MUST also resolve the environment-token naming inconsistency (analyze C6): pick one canonical token for resource-name placement (recommended: `prod` in resource names, `production` only in human-readable env labels and GitHub Environment names) and amend T019, T019a, T023, T062 plus all `infra/parameters/*.bicepparam` references for consistency. Record the canonical naming rule in `STYLE.md` so future tasks inherit it.**
  - **Agents**: `principal-engineer`, `compliance-auditor`, `sre-engineer`
  - **Tools**: `read`, `edit`, `search`, `agent` (`compliance-auditor` for label routing and citation policy)
  - **Success**: `grep -rn 'Foundry' specs/029-progressive-delivery-pipeline/ | head -1` shows "Microsoft Foundry" on first hit per file; `gh label list` includes the five labels; opening a synthetic issue with each label auto-assigns the right CODEOWNER team; `python tools/pipeline/src/pipeline_tools/coverage_check.py specs/029-progressive-delivery-pipeline` reports ≥95 % literal-citation coverage for both FR and SC IDs; `STYLE.md` documents the env-token rule and `grep -E "rg-ama-(production|prod)"` shows uniform usage of the chosen token across `tasks.md`, `plan.md`, `infra/parameters/*.bicepparam`, and the Bicep modules.

### Coverage Re-Validation

- [ ] T088 [P] Re-run `/speckit.analyze` (`.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks`) and assert the report contains **0 CRITICAL, 0 HIGH** findings and that every FR-001 … FR-033 + SC-001 … SC-018 row in the coverage table reads "Full"; commit the resulting report to `specs/029-progressive-delivery-pipeline/validation/analyze-post-remediation.md`. **Additionally, this task MUST author and run a small validator `tools/pipeline/src/pipeline_tools/coverage_check.py` that scans `tasks.md` for literal `(FR-XXX)` and `(SC-XXX)` citations against the spec inventory and asserts ≥95 % literal-citation coverage for both axes (closing analyze C12, C13). The task MUST also gate on the new `tests/pipeline/integration/test_reviewer_sync.py` (T024a) passing and on the new `contracts/audit-event.schema.json` validating cleanly (T020a). Any HIGH or CRITICAL finding from the coverage_check or analyze rerun blocks the Phase 13 checkpoint.**
  - **Agents**: `principal-engineer`, `compliance-auditor`, `product-owner-ba`
  - **Tools**: `execute`, `edit`, `agent` (`speckit.analyze`)
  - **Success**: Report committed; CRITICAL/HIGH counts both 0; coverage 100 % Full for all P1 + P2 FRs; any remaining `partial` ratings have a recorded justification; `python tools/pipeline/src/pipeline_tools/coverage_check.py specs/029-progressive-delivery-pipeline --min 0.95` exits 0; `pytest tests/pipeline/integration/test_reviewer_sync.py tests/pipeline/contract/test_audit_event_schema.py -q` passes.

**Checkpoint Phase 13**: All 20 analyze findings closed; coverage table re-published showing ≥ 95 % Full; constitution still satisfied.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** — no dependencies, start immediately. **T000a (second-collaborator pre-flight) is a hard prerequisite for T008, T024, T043, T044, T045, T046, T058 under user-owned mode (ADR-029-01); it is itself blocked only on T008a (`infra/IDENTITY.md` existing).**
- **Foundational (Phase 2)** — depends on Phase 1; **BLOCKS every user story**. **T008a (author `infra/IDENTITY.md`) → T008b (`identity_consistency.rego`) → T019a (Bicep `subscriptionTopology` parameter) → T015 (cross-env Rego dual-mode) → T017 (contract tests with both topologies + identity-consistency cases) is a hard chain. T020a (audit-event JSON Schema) → T020 (audit emitter) → T021 (schema contract test) is another hard chain. T024 → T024a (reviewer-sync integration tests) under user-owned mode. T005 (reusable OIDC action) depends on T008a because its runtime topology assertion parses `infra/IDENTITY.md`.**
- **Cross-phase prerequisite (user-owned mode only)**: T000a (Phase 1) BLOCKS T008, T024, T043–T046, T058 across Phases 2 and 7. Org-mode tenants may treat T000a as a no-op. The dependency graph tooling MUST honour this even when a scheduler dispatches phases in parallel — a dispatcher reading only the phase headers will mis-order without reading T000a's prose.
- **User Stories (Phases 3–11)** — all depend on Phase 2; once Phase 2 is done they may run in parallel by different teams (most stories touch different files).
- **Polish (Phase 12)** — depends on all desired user stories being complete (T076 / T077 require ≥US1–US6 done; T072–T074 can start once any one story is done).
- **Coverage Remediation (Phase 13)** — supplements specific stories: T079a → US1; T080, T084 → US3; T081 → US2; T082 → US4; T083 → US9; T085 → US8; T086 → wraps every gate (depends on T031, T039, T041, T049, T058); T087 → doc-only, may run in parallel; T088 → final, depends on all of T079a–T087 **plus T020a (schema) and T024a (reviewer-sync tests) which T088's coverage gate explicitly references**.

### User Story Dependencies (Cross-Story)

- **US1 (P1)** — needs Phase 2; integrates strongly with US2 (build-once) and US4 (rollback). Can be implemented first and demonstrated end-to-end with a temporary "always promote" stub for US4 if needed for the MVP.
- **US2 (P1)** — needs Phase 2. Independent of US1 in code (different jobs in `cd.yml`) but US1 silently depends on US2 to be production-credible.
- **US3 (P1)** — needs Phase 2 only. Fully independent of US1/US2 in implementation (different workflow file `ci.yml`).
- **US4 (P2)** — needs Phase 2 + US1 in place to integrate the rollback into the canary flow. Logic in `canary_controller.py` can be developed in parallel.
- **US5 (P2)** — needs Phase 2 + US2 (artefact metadata feeds the pack). Pack producer logic developed in parallel; final wiring waits for US2.
- **US6 (P2)** — needs Phase 2 + US1 (freeze step injected into existing deploy jobs).
- **US8 (P2)** — needs Phase 2 only. Independent of other stories.
- **US9 (P2)** — needs Phase 2 + US8 (parameter files referenced by enforcement tests).
- **US7 (P3)** — needs Phase 2; touches the existing `drift-detection.yml`. Can be done last.

### Within Each User Story

- Tests first (write to fail), then implementation.
- Models / contracts before services; services before workflow wiring.
- Workflow wiring last; verify in sandbox.

### Parallel Opportunities

- **Phase 1**: T002 ∥ T003 ∥ T004 ∥ T006 ∥ T007 ∥ T009 (T001 first; T000a/T005/T008 sequential touchpoints; T000a depends on T008a; T005 depends on T008a for the topology-assertion read).
- **Phase 2**: T008a (no Phase-2 prereq); then T008b ∥ T011 ∥ T013 ∥ T015 ∥ T016 ∥ T019 ∥ T021 ∥ T023 ∥ T024a ∥ T026 ∥ T028 after T008a / T010 / T012 / T014 / T018 / T019a / T020+T020a / T022 / T024 / T025 / T027 respectively (T019a depends on T008a + T019; T020a depends on T008a; T024a depends on T024).
- **Across stories** (after Phase 2): A team of 3–4 can run US1 + US3 + US8 + US7 in parallel; US2 + US5 are a tight pair; US6 grafts onto US1; US9 grafts onto US8.

---

## Parallel Example: User Story 3 (PR Quality Gates)

```bash
# After T041 (workflow scaffold) lands, run in parallel:
Task T042 — bicep-whatif job + OPA wiring  →  .github/workflows/ci.yml (whatif job block)
Task T043 — safety-critical-path job        →  .github/workflows/ci.yml (separate job block)
Task T044 — branch protection               →  GitHub API only (no workflow file conflict)
```

---

## Implementation Strategy

### MVP (User Story 1 + minimal US2/US4 stubs)

1. Phases 1 + 2.
2. Phase 3 (US1) with `artefact-verifier` stubbed (returns OK) and `canary-controller` stubbed (always `promote`).
3. **STOP & VALIDATE**: merge a no-op change to `main`, observe < 60 min lead-time and lead-time tile populated.
4. Demo / cut a release tag.

### Incremental Delivery (recommended sequence)

1. MVP as above.
2. Replace stubs by completing US2 (build-once) and US4 (burn-rate rollback) → pipeline becomes credible for production.
3. US3 (gates) → defect bar raised at PR time.
4. US5 (evidence pack) → regulator-ready.
5. US6 (freeze + emergency hotfix) → incident-safe.
6. US8 + US9 (env-tiered posture + enforcement) → infrastructure defensible end-to-end.
7. US7 (drift + OIDC-only) → final sweep.
8. Phase 12 polish + 7-day soak.

### Parallel Team Strategy

- **Team A (DevOps + SRE)**: US1, US4, US6 (the deploy / rollback / freeze flows).
- **Team B (Security + Compliance + DevOps)**: US2, US5, US7, US9 (artefacts, evidence, drift, enforcement).
- **Team C (DevOps + Software Dev)**: US3, US8 (PR gates, env-tiered posture).
- All teams meet daily on shared files (`cd.yml`, `posture-matrix.yaml`) to avoid merge conflict.

---

## Notes

- `[P]` = different file or no dependency on incomplete tasks.
- Every task lists the actor agents to consult and the tool kinds it needs — solicit each agent's input on the task it owns before declaring success.
- Test tasks intentionally fail before implementation; verify the red state before going green.
- Commit after each task or logical group; PRs touching `infra/policy/posture-matrix.yaml` or `infra/policy/posture-exceptions.yaml` require dual approval (security + compliance CODEOWNER).
- Avoid: changing `apps/api`, `apps/agents`, or `apps/web` business logic in this feature — the pipeline delivers them, it does not modify them.
- Stop at any **Checkpoint** to validate the user story independently and decide whether to ship or continue.
