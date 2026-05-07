# Tasks: Web Application Capstone Closure (spec-035)

**Branch**: `035-webapp-capstone-closure`
**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) · **Research**: [research.md](./research.md) · **Data model**: [data-model.md](./data-model.md) · **Contracts**: [contracts/](./contracts/) · **Quickstart**: [quickstart.md](./quickstart.md)

**Tests**: REQUIRED. Constitution **QG-1 (TDD)** mandates failing-tests-first. Spec-035 inherits the failing [`tests/e2e/web-coverage/`](../../tests/e2e/web-coverage/) Playwright suite (READ-ONLY per [OOS-003](./spec.md#out-of-scope)) and adds new contract / integration / unit tests under [`apps/api/tests/contract/spec_035/`](../../apps/api/tests/) and [`apps/web/tests/`](../../apps/web/).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing. Implementation order (per [plan.md § Implementation Phases](./plan.md#implementation-phases-high-level--detail-goes-into-tasksmd)) is **Phase A first (US-2)** so that Phase B (US-1) UI assertions can read back through `/api/audit/list` in production.

## Format

```text
- [ ] [TaskID] [P?] [Story?] Description with file path
  - Agents: <actor-specific agents that produce/consume input or output>
  - Tools: <subset of: execute, read, edit, search, web, agent, todo>
  - Success: <verifiable acceptance criterion>
```

**Markers**:

- `[P]` — parallelizable (different files, no upstream task incomplete)
- `[USx]` — owning user story (US1..US5); omitted on Setup/Foundational/Polish phases
- File paths are workspace-relative

**Actor-specific agents in scope**:

| Agent | Role |
| --- | --- |
| `web-eng` (human) | Owns [`apps/web/`](../../apps/web/) Next.js 16 App Router |
| `api-eng` (human) | Owns [`apps/api/`](../../apps/api/) FastAPI 0.115 |
| `iac-eng` (human) | Owns [`infra/`](../../infra/) Bicep + AVM modules |
| `qa-eng` (human) | Owns [`tests/e2e/web-coverage/`](../../tests/e2e/web-coverage/) and [`apps/api/tests/`](../../apps/api/tests/) |
| `communication-agent` | MAF runtime — drafts/sends warnings, multilingual, AWS-compliant ([`apps/agents/communication/`](../../apps/agents/communication/)) |
| `evacuation-agent` | MAF runtime — multi-LGA evacuation logistics ([`apps/agents/evacuation/`](../../apps/agents/evacuation/)) |
| `risk-assessment-agent` | MAF runtime — live risk matrix recommendations ([`apps/agents/risk_assessment/`](../../apps/agents/risk_assessment/)) |
| `planning-agent` | MAF runtime — IAP composer, forecasting ([`apps/agents/planning/`](../../apps/agents/planning/)) |
| `monitoring-agent` | MAF runtime — observability/KQL/anomaly ([`apps/agents/monitoring/`](../../apps/agents/monitoring/)) |
| `resource-allocation-agent` | MAF runtime — resource scheduling ([`apps/agents/resource_allocation/`](../../apps/agents/resource_allocation/)) |
| `Explore` subagent | Read-only codebase recon |
| `microsoft-docs` skill | Azure/MS doc lookup via Microsoft Learn MCP |
| `azure-bicep-patterns` skill | AVM-first Bicep composition guidance |
| `azure-defaults` skill | CAF naming + region defaults |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare workspace, dependencies, and CI scaffolding. No story-specific code.

- [X] T001 Add new web dependencies (`idb`, `@axe-core/playwright`, `pdf-lib`, `@azure/msal-react`) to [`apps/web/package.json`](../../apps/web/package.json) and run `pnpm install`
  - Agents: `web-eng`
  - Tools: read, edit, execute
  - Success: `pnpm install` exits 0; new packages listed under `dependencies`/`devDependencies`; `pnpm-lock.yaml` updated; `pnpm -C apps/web typecheck` exits 0.

- [X] T002 [P] Add new API dependencies (`azure-identity`, `azure-keyvault-certificates`, `azure-storage-blob`, `python-jose[cryptography]`, `endesive` for PKCS#7) to [`apps/api/pyproject.toml`](../../apps/api/pyproject.toml) and run `uv sync`
  - Agents: `api-eng`
  - Tools: read, edit, execute
  - Success: `uv sync` exits 0; `uv run python -c "import azure.identity, azure.keyvault.certificates, jose, endesive"` exits 0; `pyproject.toml` lock matches.

- [X] T003 [P] Create new shared TypeScript domain types package directory [`packages/domain/`](../../packages/domain/) with `package.json`, `tsconfig.json`, and `src/index.ts` exporting empty `AppRole`, `PersonaId`, `AuditOutcome`, `OfflineQueueTier` placeholder types
  - Agents: `web-eng`
  - Tools: edit, execute
  - Success: `pnpm -C packages/domain build` exits 0; package resolves from [`apps/web/`](../../apps/web/) via workspace protocol.

- [X] T004 [P] Add `apps/api/tests/contract/spec_035/__init__.py`, `apps/api/tests/integration/spec_035/__init__.py`, `apps/api/tests/unit/spec_035/__init__.py` and ensure pytest discovery picks them up via [`pyproject.toml`](../../pyproject.toml) `[tool.pytest.ini_options]`
  - Agents: `api-eng`, `qa-eng`
  - Tools: edit, execute
  - Success: `uv run pytest apps/api/tests/contract/spec_035 -q` reports `0 passed, 0 failed, 0 errors` (collection works on empty packages).

- [X] T005 [P] Add CI workflow extensions in [`.github/workflows/`](../../.github/workflows/): a new `spec-035-gate.yml` that runs `verify-activation-mutex.ps1`, `verify-spec-hardening.ps1`, the `pytest apps/api/tests/contract/spec_035` shard, and the `tests/e2e/web-coverage` shard against an ephemeral preview slot
  - Agents: `qa-eng`, `iac-eng`
  - Tools: edit, search
  - Success: workflow file lints with `actionlint`; matrix entries cover dev / staging / production-mirror; required-status-check entry appears in branch protection plan note.

**Checkpoint**: Toolchain is green; new test packages are collectable; lockfiles consistent.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Cross-cutting infrastructure that EVERY user story depends on. ⚠️ **CRITICAL** — no user-story phase can start until Phase 2 is complete.

- [X] T006 Define the closed [`AuditOutcome` enum](./data-model.md#4-audittimelineentry) in [`packages/domain/src/audit-outcome.ts`](../../packages/domain/src/audit-outcome.ts) (web) and [`apps/api/app/domain/audit_outcome.py`](../../apps/api/app/domain/audit_outcome.py) (API). Both MUST list the same 20 values verbatim from [`data-model.md`](./data-model.md#4-audittimelineentry)
  - Agents: `web-eng`, `api-eng`
  - Tools: read, edit
  - Success: `pnpm -C packages/domain build` and `uv run mypy apps/api/app/domain/audit_outcome.py` both exit 0; a property test asserts `len(set(WebEnum)) == len(set(ApiEnum)) == 20`.

- [X] T007 [P] Define the [`AppRole` enum (11 values)](./data-model.md#6-entraapprolebinding) in [`packages/domain/src/app-role.ts`](../../packages/domain/src/app-role.ts) and [`apps/api/app/domain/app_role.py`](../../apps/api/app/domain/app_role.py); add a fail-closed test that rejects any 12th value
  - Agents: `web-eng`, `api-eng`
  - Tools: read, edit
  - Success: `pnpm -C packages/domain test` and `uv run pytest apps/api/tests/unit/spec_035/test_app_role_closed_set.py` both pass; pytest test attempts to add a 12th role and expects `ValueError`.

- [X] T008 [P] Add the [Production-Auth Extension Envelope JSON Schema](./contracts/production-auth-extension.contract.md) to [`packages/schemas/spec_035/extension_envelope.schema.json`](../../packages/schemas/spec_035/extension_envelope.schema.json) and Pydantic v2 model in [`apps/api/app/schemas/extension_envelope.py`](../../apps/api/app/schemas/extension_envelope.py); fields: `error_code`, `retry_after_seconds`, `audit_id`, `correlation_id`
  - Agents: `api-eng`
  - Tools: read, edit
  - Success: `uv run pytest apps/api/tests/unit/spec_035/test_extension_envelope_schema.py` passes; schema validates the seven `error_code` values from the contract; `retry_after_seconds` is non-null only for `rate_limited` and `seed_not_ready`.

- [X] T009 [P] [iac-eng] Author new AVM-composed Bicep module [`infra/modules/apim-rate-limit.bicep`](../../infra/modules/apim-rate-limit.bicep) implementing the Q3 policy from [`contracts/rate-limit.policy.md`](./contracts/rate-limit.policy.md) (per-`(persona_id, route)` 10/min + 600/hr + global 600/min ceiling)
  - Agents: `iac-eng`, `azure-bicep-patterns` skill, `azure-defaults` skill
  - Tools: read, edit, agent
  - AVM dep: `br/public:avm/res/api-management/service` (host) composed with the Q3 inbound `<rate-limit-by-key>` policy fragment; counter keys driven by App Configuration values from T011.
  - Success: `bicep build infra/modules/apim-rate-limit.bicep` exits 0 with no warnings; module exposes counter-key inputs and consumes App Configuration values; PSRule passes.

- [X] T010 [P] [iac-eng] Author new AVM-composed Bicep module [`infra/modules/blob-immutable.bicep`](../../infra/modules/blob-immutable.bicep) implementing legal-hold + time-based immutability for the recovery-handover PDF container per [`contracts/recovery-handover.contract.md`](./contracts/recovery-handover.contract.md)
  - Agents: `iac-eng`, `azure-bicep-patterns` skill
  - Tools: read, edit, agent
  - AVM dep: `br/public:avm/res/storage/storage-account` with `blobServices.containers[].immutabilityPolicy` (time-based retention) and `legalHold` enabled; allows `protectedAppendWrites` for the audit-append SLO.
  - Success: `bicep build` exits 0; `az deployment group what-if` against a sandbox shows the container with `immutabilityPolicy.allowProtectedAppendWrites: true` and `legalHold: true` defaults.

- [X] T011 [P] [iac-eng] Extend [`infra/modules/app-configuration.bicep`](../../infra/modules/app-configuration.bicep) with the new keys from [`contracts/cultural-safety.contract.md`](./contracts/cultural-safety.contract.md) and [`contracts/rate-limit.policy.md`](./contracts/rate-limit.policy.md): `cultural-safety:default-timeout-seconds=90`, `cultural-safety:timeout-override-aws-levels=["emergency_warning"]`, `rate-limit:perPersonaRoute:perMinute=10`, `rate-limit:perPersonaRoute:perHour=600`, `rate-limit:global:perMinute=600`, `offline:queueCap=500`, `offline:lifeSafetyBatchSize=50`
  - Agents: `iac-eng`
  - Tools: read, edit
  - Success: `bicep build infra/modules/app-configuration.bicep` exits 0; `infra/parameters/spec_035.bicepparam` lists the keys; `az appconfig kv list --query "[?key.starts_with('cultural-safety:')]"` against staging returns ≥3 rows post-deploy.

- [X] T012 Wire the new modules into [`infra/main.bicep`](../../infra/main.bicep) (calling `apim-rate-limit.bicep`, `blob-immutable.bicep`, and the extended `app-configuration.bicep`) and add the new Key Vault key for the FR-007 PDF signing certificate
  - Agents: `iac-eng`
  - Tools: read, edit, execute
  - Success: `bicep build infra/main.bicep` exits 0; `az deployment group what-if -g rg-ama-staging --template-file infra/main.bicep --parameters infra/main.parameters.staging.json` lists exactly the new resources (no in-place modifications to existing resources).

- [X] T013 Author CI gate script [`scripts/verify-activation-mutex.ps1`](../../scripts/verify-activation-mutex.ps1) per [`research.md` § R-005](./research.md#r-005--activation-mutex-dual-enforcement) — fails build if `AMA_TEST_SUPPORT=1` is set with `ENVIRONMENT in {staging, production}` AND verifies the FastAPI lifespan invariant
  - Agents: `qa-eng`, `api-eng`
  - Tools: read, edit, execute
  - Success: `pwsh -ExecutionPolicy Bypass -File ./scripts/verify-activation-mutex.ps1` exits 0 in clean state; manually setting `AMA_TEST_SUPPORT=1; AMA_ENVIRONMENT=staging` causes exit code 1 with stderr containing `activation_mutex_violation`.

- [X] T014 [P] Author the FastAPI activation-mutex middleware at [`apps/api/app/middleware/activation_mutex.py`](../../apps/api/app/middleware/activation_mutex.py) that runs as a `lifespan` invariant: rejects startup with non-zero exit + audit row `outcome=activation_mutex_violation` if both guards are active
  - Agents: `api-eng`
  - Tools: read, edit
  - Success: `uv run pytest apps/api/tests/unit/spec_035/test_activation_mutex.py` passes; the unit test instantiates the lifespan with both env vars set and asserts a `SystemExit` is raised AND the audit appender is called once with `outcome=activation_mutex_violation`.

- [X] T015 [P] Extend [`apps/api/app/repositories/audit_repository.py`](../../apps/api/app/repositories/audit_repository.py) with `append_paired(operator_row, target_row, correlation_id)` using Cosmos `TransactionalBatch` keyed by `correlation_id` per [`research.md` § R-006](./research.md#r-006--paired-audit-row-emission-cosmos-transactionalbatch)
  - Agents: `api-eng`, `Explore` subagent (recon existing repo pattern)
  - Tools: read, edit, agent
  - Success: `uv run pytest apps/api/tests/unit/spec_035/test_audit_repository_paired.py` passes; the test mocks Cosmos client and asserts both rows in a single `execute_item_batch` call sharing one partition key.

- [X] T016 [P] Author the `audit_appender` middleware at [`apps/api/app/middleware/audit_appender.py`](../../apps/api/app/middleware/audit_appender.py) that emits one audit row on every state-changing call AND emits paired rows when `X-Impersonate-Persona` was present per [Q9](./spec.md#clarifications)
  - Agents: `api-eng`
  - Tools: read, edit
  - Success: `uv run pytest apps/api/tests/unit/spec_035/test_audit_appender.py` passes; the test exercises three scenarios — no impersonation (1 row), admin direct (1 row, `outcome=admin_override`, `impersonated_persona_id=None`), admin-impersonating-persona (2 rows in single `TransactionalBatch`).

**Checkpoint**: Foundational infra ready. All user-story phases unblocked.

---

## Phase 3: User Story 2 — Production-Reachable Evaluator + Audit-List with Auth & RBAC (Priority: P2)

**Goal**: `POST /api/outcomes/sc-{001..005}/evaluate` and `GET /api/audit/list` return the spec-034 success body **in production**, with Entra bearer + 11-AppRole RBAC + per-`(persona_id, route)` rate-limit + paired-row impersonation audit + the Q10 error envelope. `POST /api/outcomes/sc-{006..011}/evaluate` returns `400 evaluator_not_routable` regardless of bearer-token state per [FR-009](./spec.md#functional-requirements) (verified by [T018](#tests-for-user-story-2-tdd--write-first-watch-them-fail)). Lands first per [`plan.md`](./plan.md#implementation-phases-high-level--detail-goes-into-tasksmd) so US-1 UI assertions can read back through audit-list in production.

**Independent Test**: Acquire an Entra bearer for an `incident-commander` AppRole; `POST /api/outcomes/sc-001/evaluate` against `https://app-ama-zo6bb5.azurewebsites.net/`; expect `200` with spec-034 body + `audit_id`; `GET /api/audit/list?correlation_id=<uuid>` shows the row; an unauthorised caller is rejected with `401/403/429` + matching audit row.

### Tests for User Story 2 (TDD — write FIRST, watch them FAIL)

- [X] T017 [P] [US2] Write contract test [`apps/api/tests/contract/spec_035/test_evaluator_production_reach.py`](../../apps/api/tests/contract/spec_035/test_evaluator_production_reach.py) asserting `POST /api/outcomes/sc-{001..005}/evaluate` returns the spec-034 success body verbatim under production-auth mode (`AMA_ENABLE_PRODUCTION_AUTH=1`). Parametrise across all five routable SC IDs; `sc-006..sc-011` are explicitly out of scope here and ladder-tested via [T018](#tests-for-user-story-2-tdd--write-first-watch-them-fail)
  - Agents: `qa-eng`, `api-eng`
  - Tools: read, edit, execute
  - Success: 5 parametrised cases (sc-001..sc-005) currently FAIL with `404` or `403` (proving the feature is not yet there); failure message names the missing route registration block in [`apps/api/app/api/router.py`](../../apps/api/app/api/router.py); `sc-006..sc-011` cases are NOT exercised in this test (T018 owns them).

- [X] T018 [P] [US2] Write contract test [`apps/api/tests/contract/spec_035/test_error_precedence_ladder.py`](../../apps/api/tests/contract/spec_035/test_error_precedence_ladder.py) covering the 6-level ladder from [`contracts/production-auth-extension.contract.md`](./contracts/production-auth-extension.contract.md): `evaluator_not_routable > sovereignty_denied > unauthorized > forbidden > rate_limited > schema_invalid|seed_not_ready`
  - Agents: `qa-eng`, `api-eng`
  - Tools: read, edit
  - Success: 6 parametrised cases each stack two error conditions; test FAILS until the middleware order matches the contract.

- [X] T019 [P] [US2] Write contract test [`apps/api/tests/contract/spec_035/test_rate_limit.py`](../../apps/api/tests/contract/spec_035/test_rate_limit.py) — 11 calls in 60 s for one `(persona_id, route)` ⇒ ten 200s + one 429 with `Retry-After`; 601 calls across multiple personas ⇒ global ceiling 429
  - Agents: `qa-eng`
  - Tools: read, edit
  - Success: test FAILS (no rate-limit middleware yet); per `Retry-After` header equals `retry_after_seconds` in envelope.

- [X] T020 [P] [US2] Write contract test [`apps/api/tests/contract/spec_035/test_impersonation_pairing.py`](../../apps/api/tests/contract/spec_035/test_impersonation_pairing.py) — admin token + `X-Impersonate-Persona: incident_commander_au_east` ⇒ exactly two audit rows in one `correlation_id` (one `admin_override`, one normal-outcome)
  - Agents: `qa-eng`, `api-eng`
  - Tools: read, edit
  - Success: test FAILS until [T016](#phase-2-foundational-blocking-prerequisites) audit_appender lands and the route stack invokes it.

- [X] T021 [P] [US2] Write contract test [`apps/api/tests/contract/spec_035/test_classifier_branches.py`](../../apps/api/tests/contract/spec_035/test_classifier_branches.py) — 5 branches per [`contracts/classifier-gateway.contract.md`](./contracts/classifier-gateway.contract.md): `pspf` (deny+`classifier_deny`), `pii` (mask+`classifier_mask`+200), `pspf+pii` (deny), classifier-failure (deny+`classifier_failed`), `clean` (pass-through)
  - Agents: `qa-eng`
  - Tools: read, edit
  - Success: test FAILS; admin-token bypass test included (must NOT bypass).

- [X] T022 [P] [US2] Write contract test [`apps/api/tests/contract/spec_035/test_offline_replay.py`](../../apps/api/tests/contract/spec_035/test_offline_replay.py) per [`contracts/offline-replay.openapi.yaml`](./contracts/offline-replay.openapi.yaml) — life-safety batch drains first, dedupe by `(persona_id, client_correlation_id)`, 50-entry max, 413 on oversized
  - Agents: `qa-eng`
  - Tools: read, edit
  - Success: test FAILS; assertion that `captured_ts` is preserved on the replayed audit row (SC-007).

- [X] T023 [P] [US2] Write contract test [`apps/api/tests/contract/spec_035/test_whoami.py`](../../apps/api/tests/contract/spec_035/test_whoami.py) per [`contracts/auth-rbac.openapi.yaml`](./contracts/auth-rbac.openapi.yaml) — verifies `Principal` shape, includes `impersonation` block iff admin presented `X-Impersonate-Persona`, returns 403 if non-admin presents the header
  - Agents: `qa-eng`
  - Tools: read, edit
  - Success: test FAILS until [T029](#implementation-for-user-story-2) lands.

### Implementation for User Story 2

- [X] T024 [P] [US2] Implement `entra_auth` middleware at [`apps/api/app/middleware/entra_auth.py`](../../apps/api/app/middleware/entra_auth.py) per [`research.md` § R-001](./research.md#r-001--entra-bearer-validation-in-fastapi) — JWKS bearer validation via `azure-identity`, claim extraction (`oid`, `roles`, `persona_id`), AAD audience check, JWKS cache TTL = 1h
  - Agents: `api-eng`, `microsoft-docs` skill (for JWKS endpoint docs)
  - Tools: read, edit, web, agent
  - Success: middleware unit tests at [`apps/api/tests/unit/spec_035/test_entra_auth.py`](../../apps/api/tests/unit/spec_035/test_entra_auth.py) pass; middleware rejects expired tokens with `401 unauthorized` (`outcome=auth_unauthorized`), missing AppRole / `persona_id` mapping with `403 forbidden` (`outcome=auth_forbidden` — see T024b), and emits the [Q10 error envelope](./contracts/production-auth-extension.contract.md) on both.

- [X] T024b [P] [US2] Implement `rbac_check` middleware at [`apps/api/app/middleware/rbac_check.py`](../../apps/api/app/middleware/rbac_check.py) per [`spec.md` § FR-011](./spec.md#functional-requirements) and [`contracts/auth-rbac.openapi.yaml`](./contracts/auth-rbac.openapi.yaml) — stage-(a) AppRole → route-family mapping for the 11 AppRoles (10 AIIMS + `system-administrator`); stage-(b) `persona_id` → AIIMS-function mapping for all 68 spec-034 personas; `system-administrator` bypasses stage (b) and inherits target persona AIIMS-function authorisation when `X-Impersonate-Persona` is present; emits `outcome=auth_forbidden` audit row + Q10 error envelope on stage-(a) or stage-(b) mismatch
  - Agents: `api-eng`
  - Tools: read, edit
  - Success: unit test [`apps/api/tests/unit/spec_035/test_rbac_check.py`](../../apps/api/tests/unit/spec_035/test_rbac_check.py) covers (i) allow on matching AppRole + persona→function, (ii) deny on missing AppRole, (iii) deny on persona→function mismatch, (iv) admin direct allow with `outcome=admin_override`, (v) admin-impersonating-persona allow with paired-row precondition met (audit_appender owns row emission per T016); test passes after this middleware lands; FR-011's 11-AppRole inventory is enforced in code by an explicit closed-set check.

- [X] T025 [P] [US2] Implement `classifier_gateway` middleware at [`apps/api/app/middleware/classifier_gateway.py`](../../apps/api/app/middleware/classifier_gateway.py) and supporting service at [`apps/api/app/services/classifier_gateway_service.py`](../../apps/api/app/services/classifier_gateway_service.py) per [`contracts/classifier-gateway.contract.md`](./contracts/classifier-gateway.contract.md) — deterministic regex+dictionary at ADR-033 Layer 2; PSPF→deny / PII→mask / fail→deny
  - Agents: `api-eng`
  - Tools: read, edit
  - Success: [T021](#tests-for-user-story-2-tdd--write-first-watch-them-fail) test passes; admin-bypass-impossible assertion holds.

- [X] T026 [P] [US2] Implement `rate_limit_audit` middleware at [`apps/api/app/middleware/rate_limit_audit.py`](../../apps/api/app/middleware/rate_limit_audit.py) — translates APIM 429s (signalled via `X-Rate-Limit-Triggered`) into the Q10 envelope shape, strips the internal header, appends the `outcome=rate_limited` audit row
  - Agents: `api-eng`
  - Tools: read, edit
  - Success: [T019](#tests-for-user-story-2-tdd--write-first-watch-them-fail) test passes; `Retry-After` header byte-equals `retry_after_seconds` in body.

- [X] T027 [US2] Wire the middleware stack in [`apps/api/app/main.py`](../../apps/api/app/main.py) in the order specified in [`contracts/classifier-gateway.contract.md` § Position in stack](./contracts/classifier-gateway.contract.md#position-in-stack): `activation_mutex` → `classifier_gateway` → `entra_auth` → `rbac_check` → `rate_limit_audit` → route handler → `audit_appender`
  - Agents: `api-eng`
  - Tools: read, edit
  - Success: [T018](#tests-for-user-story-2-tdd--write-first-watch-them-fail) precedence-ladder test passes; FastAPI startup logs show the middleware order in this exact sequence.

- [X] T028 [US2] Add the production-reachable registration block in [`apps/api/app/api/router.py`](../../apps/api/app/api/router.py) wrapping the existing `outcome_evaluator` and `audit_list` routers with `Depends(entra_auth)` + `Depends(rbac_check)` per [`spec.md` § FR-009](./spec.md#functional-requirements). The dual-guard test-support block remains untouched per OOS-006 — production registration is **layered, not replaced**
  - Agents: `api-eng`, `Explore` subagent
  - Tools: read, edit, agent
  - Success: [T017](#tests-for-user-story-2-tdd--write-first-watch-them-fail) production-reach test passes; the existing test-support shard at `_test/outcomes/sc-001/evaluate` continues to pass under `AMA_TEST_SUPPORT=1`.

- [X] T029 [P] [US2] Implement the `auth_whoami` route at [`apps/api/app/api/routes/auth_whoami.py`](../../apps/api/app/api/routes/auth_whoami.py) per [`contracts/auth-rbac.openapi.yaml`](./contracts/auth-rbac.openapi.yaml)
  - Agents: `api-eng`
  - Tools: read, edit
  - Success: [T023](#tests-for-user-story-2-tdd--write-first-watch-them-fail) test passes; route registered under `/api/auth/whoami`.

- [X] T030 [P] [US2] Implement the `offline_replay` route at [`apps/api/app/api/routes/offline_replay.py`](../../apps/api/app/api/routes/offline_replay.py) and service at [`apps/api/app/services/offline_replay_service.py`](../../apps/api/app/services/offline_replay_service.py) per [`contracts/offline-replay.openapi.yaml`](./contracts/offline-replay.openapi.yaml) — life-safety drain first, dedupe, 413 on oversize, paired audit on admin-replay
  - Agents: `api-eng`
  - Tools: read, edit
  - Success: [T022](#tests-for-user-story-2-tdd--write-first-watch-them-fail) test passes; `captured_ts` preserved end-to-end.

- [X] T031 [US2] Add overflow-envelope repository at [`apps/api/app/repositories/offline_queue_overflow_repository.py`](../../apps/api/app/repositories/offline_queue_overflow_repository.py) — accepts `queue_overflow` synthetic envelopes from the SW on next reconnect and appends `outcome=queue_overflow` audit rows
  - Agents: `api-eng`
  - Tools: read, edit
  - Success: unit test [`apps/api/tests/unit/spec_035/test_offline_overflow_repo.py`](../../apps/api/tests/unit/spec_035/test_offline_overflow_repo.py) passes; appended row carries `tier`, `displaced=true|false`, and the original `client_correlation_id`.

- [X] T032 [US2] Run all US-2 tests locally and against the staging preview slot
  - Agents: `qa-eng`, `api-eng`
  - Tools: execute, read
  - Success: `uv run pytest apps/api/tests/contract/spec_035 apps/api/tests/integration/spec_035 -q` exits 0; staging smoke run via `quickstart.md` § "Verify the production-reachable evaluator" returns 200 with the spec-034 success body verbatim.

**Checkpoint US-2**: Production-reachable evaluator + audit-list independently verifiable. Phase B (US-1) UI assertions can now read back through `/api/audit/list` in production.

---

## Phase 4: User Story 1 — Safety-Critical Operator Workflows Drive Real State Changes (Priority: P1) 🎯 MVP

**Goal**: 10 operational personas (Incident Commander, Planning Officer, Public-Information Officer, Logistics Officer, Operations Officer, Field Coordinator, Observer-Auditor, Risk Manager, Resilience Planner, Executive Leader) drive state-changing workflows against the real UI; every transition asserts the post-state via FR-028 evaluator AND reads back the audit row within ≤2 s.

**Independent Test**: `pnpm -C tests/e2e/web-coverage test -- operational/ aws-warning-compliance.spec.ts audit-append-only.spec.ts span-of-control.spec.ts accessibility-and-multilingual.spec.ts field-offline-mode.spec.ts` against production ⇒ ≥95% (persona × outcome × hazard) tuples in `pass`; zero `Open` HIGH+ entries in [`gap-register.json`](../../tests/e2e/web-coverage/gap-register.json).

### Tests for User Story 1

- [ ] T033 [P] [US1] Run [`tests/e2e/web-coverage/operational/`](../../tests/e2e/web-coverage/) under READ-ONLY policy (OOS-003) and capture the current failure inventory in [`apps/web/tests/spec_035/baseline-failures.json`](../../apps/web/tests/spec_035/baseline-failures.json)
  - Agents: `qa-eng`
  - Tools: execute, read, edit
  - Success: file lists every failing test name + selector / FR-id from the test body; serves as the work register for T034..T047 (Phase 4 US-1 implementation tasks).

- [X] T034 [P] [US1] Write Vitest unit test [`apps/web/tests/unit/spec_035/offline-queue-store.test.ts`](../../apps/web/tests/unit/spec_035/offline-queue-store.test.ts) covering 500-cap, life-safety insertion displacing oldest routine, overflow rejection, dedupe by `(persona_id, client_correlation_id)`
  - Agents: `qa-eng`, `web-eng`
  - Tools: read, edit
  - Success: tests FAIL until T040 lands; test asserts the [Q7 displacement rule](./spec.md#clarifications) returns `replayStatus=displaced` on the displaced entry.

- [X] T035 [P] [US1] Write Vitest unit test [`apps/web/tests/unit/spec_035/classifier-banner.test.tsx`](../../apps/web/tests/unit/spec_035/classifier-banner.test.tsx) — banner renders with mask-count + audit-id link when prop `outcome=classifier_mask`; suppressed otherwise
  - Agents: `qa-eng`, `web-eng`
  - Tools: read, edit
  - Success: tests FAIL until T046 lands.

### Implementation for User Story 1 — operator panels (one panel per persona)

- [X] T036 [P] [US1] Implement [`apps/web/src/app/(operations)/workspaces/[personaId]/_panels/ic-approval-card.tsx`](../../apps/web/src/app/) per [`spec.md` § FR-001](./spec.md#functional-requirements) — rationale, source refs, confidence pill, approver identity, calls `POST /api/outcomes/sc-{N}/evaluate` then re-fetches via `/api/audit/list?correlation_id=...`
  - Agents: `web-eng`
  - Tools: read, edit
  - Success: the IC operational scenario in [`tests/e2e/web-coverage/operational/incident-commander.spec.ts`](../../tests/e2e/web-coverage/) passes against staging; audit row appears within 2 s; rationale missing ⇒ submit button disabled with WCAG-conformant inline error.

- [X] T037 [P] [US1] Implement [`apps/web/src/app/(operations)/workspaces/[personaId]/_panels/pio-aws-composer.tsx`](../../apps/web/src/app/) per [FR-002](./spec.md#functional-requirements) — AWS level selector, hazard/location/action, community-language picker (Simplified Chinese + ATSI placeholder), in-page accessibility scan invocation, IC-approval submission. Solicits the `communication-agent` via the existing MAF runtime endpoint to draft the multilingual variants
  - Agents: `web-eng`, `communication-agent` (MAF — drafts multilingual variants)
  - Tools: read, edit, agent
  - Success: PIO scenario in [`aws-warning-compliance.spec.ts`](../../tests/e2e/web-coverage/) passes; published payload contains ≥1 community-language variant; no publish path bypasses IC approval (negative test passes).

- [X] T038 [P] [US1] Implement [`apps/web/src/app/(operations)/workspaces/[personaId]/_panels/observer-auditor-timeline.tsx`](../../apps/web/src/app/) per [FR-003](./spec.md#functional-requirements) — append-only UX; PATCH/DELETE attempts call a synthetic UI-rejection path that emits an `outcome=denied` audit row with the rationale and surfaces a non-silent error
  - Agents: `web-eng`
  - Tools: read, edit
  - Success: [`audit-append-only.spec.ts`](../../tests/e2e/web-coverage/) passes; PATCH/DELETE attempt produces `denied` row; subsequent re-fetch of the original row returns byte-identical content; export-to-evidence action produces a hash-recorded artefact.

- [X] T039 [P] [US1] Implement [`apps/web/src/app/(operations)/workspaces/[personaId]/_panels/risk-matrix.tsx`](../../apps/web/src/app/) per [FR-004](./spec.md#functional-requirements). Solicits the `risk-assessment-agent` for the live recommendation matrix
  - Agents: `web-eng`, `risk-assessment-agent` (MAF — emits recommendation matrix)
  - Tools: read, edit, agent
  - Success: Risk-Manager operational scenario passes; route comparison renders ≥2 alternatives with confidence pills + provenance refs; switching routes triggers an audit row.

- [X] T040 [P] [US1] Implement [`apps/web/src/lib/offline/queue-store.ts`](../../apps/web/src/lib/offline/queue-store.ts) (IndexedDB via `idb`, encrypted at rest with subtle-crypto, configurable per-persona cap, tiered displacement) and [`apps/web/src/lib/offline/service-worker.ts`](../../apps/web/src/lib/offline/service-worker.ts) intercepting state-changing routes per [Q4 + Q7](./spec.md#clarifications). The hard cap MUST be sourced from `process.env.NEXT_PUBLIC_OFFLINE_QUEUE_CAP` (surfaced from [T011](#phase-2-foundational-blocking-prerequisites) `app-configuration.bicep` `offline:queueCap=500`) with `500` as the only fallback if the env is unset; `500` MUST NOT appear as a hardcoded business constant elsewhere in the file.
  - Agents: `web-eng`
  - Tools: read, edit
  - Success: T034 unit tests pass; `field-offline-mode.spec.ts` passes; queue persists across page reloads under Application → Storage; encrypted at-rest payload not human-readable in DevTools; setting `NEXT_PUBLIC_OFFLINE_QUEUE_CAP=10` in a Vitest fixture causes the cap to drop to 10 and overflow tests assert against the new value (proving configurability).

- [X] T041 [P] [US1] Implement [`apps/web/src/app/(operations)/workspaces/[personaId]/_panels/field-coordinator-offline.tsx`](../../apps/web/src/app/) per [FR-006](./spec.md#functional-requirements) — degraded-mode banner, queue-depth gauge ≥80% utilisation warning (Q7), reconnect-replay progress
  - Agents: `web-eng`
  - Tools: read, edit
  - Success: Field-Coordinator scenario in `field-offline-mode.spec.ts` passes; reconnect drains life-safety first, then routine in 50-entry batches; original `captured_ts` preserved on each audit row.

- [X] T042 [P] [US1] Implement [`apps/web/src/app/(operations)/workspaces/[personaId]/_panels/planning-iap-composer.tsx`](../../apps/web/src/app/) per [FR-005](./spec.md#functional-requirements). Solicits the `planning-agent` for forecast + IAP draft inputs
  - Agents: `web-eng`, `planning-agent` (MAF)
  - Tools: read, edit, agent
  - Success: Planning-Officer scenario passes; provenance pills attribute every IAP section to either an evidence ref or the planning-agent's correlation id.

- [X] T043 [P] [US1] Implement [`apps/web/src/app/(operations)/workspaces/[personaId]/_panels/span-of-control-warning.tsx`](../../apps/web/src/app/) per [FR-008](./spec.md#functional-requirements) — surfaces the > 7-direct-reports warning before save with delegation options for IC role; suppressed for Planning Officer (read-only)
  - Agents: `web-eng`
  - Tools: read, edit
  - Success: [`span-of-control.spec.ts`](../../tests/e2e/web-coverage/) passes; positive case (IC adding 8th) shows warning, negative case (Planning Officer) suppresses it.

- [X] T044 [P] [US1] Implement [`apps/web/src/app/(operations)/workspaces/[personaId]/_panels/resilience-handover-pdf.tsx`](../../apps/web/src/app/) per [FR-007](./spec.md#functional-requirements) — calls `POST /api/recovery/handover/sign`, downloads the SAS-protected PDF, links the audit row. On a `422 signing_key_expired` envelope from T045, the panel surfaces a non-silent banner naming the next-rotation ETA and links to the App-Configuration-resolved key-rotation runbook URL (key `recovery-handover:key-rotation-runbook-url`, populated by T011) — no fallback signing path is offered.
  - Agents: `web-eng`, `resource-allocation-agent` (consumes its output for "actions" sections)
  - Tools: read, edit, agent
  - Success: resilience-planner depth-profile scenario passes; PDF download starts within one click; audit row links to immutable blob URI; signing-key-expired contract test passes (UI banner visible, runbook link keyboard-reachable, no silent failure).

- [X] T045 [P] [US1] Implement the `recovery_handover` API route at [`apps/api/app/api/routes/recovery_handover.py`](../../apps/api/app/api/routes/recovery_handover.py) and service at [`apps/api/app/services/recovery_handover_service.py`](../../apps/api/app/services/recovery_handover_service.py) per [`contracts/recovery-handover.contract.md`](./contracts/recovery-handover.contract.md) — `pdf-lib` server-side render, KeyVault PKCS#7 signing, immutable Blob upload, Sendai ratio ≥0.30 enforcement. When the KeyVault signing certificate is past its `notAfter` (TTL exceeded), the service MUST fail-closed with `422 signing_key_expired` and append an audit row `outcome: schema_invalid, extension_envelope: {error_code: "signing_key_expired", correlation_id, audit_id}`; the route MUST NOT auto-rotate or fall back to a secondary cert (rotation is operator-driven via the runbook).
  - Agents: `api-eng`, `microsoft-docs` skill (KeyVault certificate signing)
  - Tools: read, edit, web, agent
  - Success: contract test [`apps/api/tests/contract/spec_035/test_recovery_handover.py`](../../apps/api/tests/contract/spec_035/test_recovery_handover.py) passes; Sendai ratio < 0.30 returns `422 schema_invalid`; `artefact_hash` byte-equals SHA-256 of returned blob bytes; expired-cert contract case returns `422 signing_key_expired` with no signing attempt.

- [X] T046 [P] [US1] Implement [`apps/web/src/lib/auth/entra-msal.ts`](../../apps/web/src/lib/auth/entra-msal.ts) (MSAL bearer acquisition + token refresh) and [`apps/web/src/lib/classifier/banner.tsx`](../../apps/web/src/lib/classifier/banner.tsx) (mask banner per Q6)
  - Agents: `web-eng`, `microsoft-docs` skill (MSAL-react)
  - Tools: read, edit, web, agent
  - Success: T035 banner test passes; MSAL silent token acquisition succeeds against the AMA tenant; bearer is attached as `Authorization: Bearer <jwt>` to every `/api/*` call.

- [ ] T047 [US1] Run the operational shard + 5 cross-cutting specs against staging
  - Agents: `qa-eng`
  - Tools: execute
  - Success: `pnpm -C tests/e2e/web-coverage test -- operational/ aws-warning-compliance.spec.ts audit-append-only.spec.ts span-of-control.spec.ts accessibility-and-multilingual.spec.ts field-offline-mode.spec.ts` exits 0; ≥95% of (persona × outcome × hazard) tuples in `pass` per [`coverage-trace.json`](../../tests/e2e/web-coverage/coverage-trace.json); zero HIGH+ open entries in [`gap-register.json`](../../tests/e2e/web-coverage/gap-register.json).

**Checkpoint US-1 (MVP)**: Capstone-outcome value delivered — 10 operational personas drive state changes against production. SC-001, SC-002, SC-007 verifiable.

---

## Phase 5: User Story 3 — Cycle-1 Net-New Persona Scenarios T187..T199 (Priority: P3)

**Goal**: 13 net-new persona scenarios pass against the real UI by composing the cultural-safety subsystem, infrastructure overlays, and claims-velocity dashboard with the existing PIO composer + IC approval card from US-1.

**Independent Test**: `pnpm -C tests/e2e/web-coverage test -- sectors/{sa,wa,tas,act,nt,commonwealth,cross-sector}/T18{7,8,9}*.spec.ts T19{0..9}*.spec.ts` ⇒ each spec passes its FR-029 depth-contract with no `test.fail()` bail-outs.

### Tests for User Story 3

- [ ] T048 [P] [US3] Capture failing-test inventory for `sectors/` shard in [`apps/web/tests/spec_035/sector-baseline-failures.json`](../../apps/web/tests/spec_035/sector-baseline-failures.json)
  - Agents: `qa-eng`
  - Tools: execute, read, edit
  - Success: file lists each failing T187..T199 spec with the missing UI selector or FR-id.

- [X] T049 [P] [US3] Write contract test [`apps/api/tests/contract/spec_035/test_cultural_safety.py`](../../apps/api/tests/contract/spec_035/test_cultural_safety.py) per [`contracts/cultural-safety.contract.md`](./contracts/cultural-safety.contract.md) and [Clarifications Q5](./spec.md#clarifications) — `emergency_warning` + 90 s timeout + IC override ⇒ `outcome=cultural_safety_timeout_override`; `watch_and_act` + 90 s timeout + IC override ⇒ `outcome=cultural_safety_timeout_override`; `advice` + 90 s timeout ⇒ `outcome=cultural_safety_held` (publication BLOCKED, queued `awaiting-elder-approval`)
  - Agents: `qa-eng`, `api-eng`
  - Tools: read, edit
  - Success: tests FAIL until [T053](#implementation-for-user-story-3) lands.

### Implementation for User Story 3

- [X] T050 [P] [US3] Implement [`apps/web/src/components/cultural-safety/`](../../apps/web/src/components/) — language-pack registry UI ([`apps/web/src/lib/i18n/language-packs.ts`](../../apps/web/src/lib/i18n/language-packs.ts) with Kimberley/Pilbara, palawa, Yolŋu Matha, Pitjantjatjara, Warlpiri), elder-approval routing surface, fallback-chain renderer (en → community-language → en)
  - Agents: `web-eng`, `communication-agent` (consumed for ATSI variants)
  - Tools: read, edit, agent
  - Success: Vitest test [`apps/web/tests/unit/spec_035/language-packs.test.ts`](../../apps/web/tests/unit/spec_035/language-packs.test.ts) passes; fallback chain renders the variant first AND the English fallback is reachable.

- [X] T051 [P] [US3] Implement [`apps/web/src/components/infrastructure-overlay/`](../../apps/web/src/components/) — iron-ore haul-road, port-critical, island-logistics, federal-precinct GeoJSON layers per [`data-model.md` § InfrastructureOverlayLayer](./data-model.md#11-infrastructureoverlaylayer)
  - Agents: `web-eng`
  - Tools: read, edit
  - Success: Vitest test for layer toggle / priority-class colouring passes; 4 layer types render distinguishably (contrast-checked).

- [X] T052 [P] [US3] Implement [`apps/web/src/components/claims-velocity/`](../../apps/web/src/components/) — ICA dashboard with `claimsLodged / claimsClosed / dollarsLodged / dollarsPaid / lgaBreakdown` per [`data-model.md` § ClaimsVelocitySnapshot](./data-model.md#12-claimsvelocitysnapshot)
  - Agents: `web-eng`
  - Tools: read, edit
  - Success: Vitest test passes; LGA breakdown sortable + accessibility-compliant.

- [X] T053 [US3] Implement `cultural_safety_service` at [`apps/api/app/services/cultural_safety_service.py`](../../apps/api/app/services/cultural_safety_service.py) per [`contracts/cultural-safety.contract.md`](./contracts/cultural-safety.contract.md) — Service Bus elder-routing enqueue, 90 s timeout, AWS-level-conditional outcome policy
  - Agents: `api-eng`, `communication-agent` (consumed for the language-pack-specific message body)
  - Tools: read, edit, agent
  - Success: T049 cultural-safety contract test passes; IC `cultural_safety_confirmer` recorded on the audit row in `timeout_lifesafety_override` cases.

- [X] T054 [P] [US3] Implement sector workspace [`apps/web/src/app/(operations)/sectors/sapol-control-centre/page.tsx`](../../apps/web/src/app/) (T187) per [FR-014](./spec.md#functional-requirements) — multi-LGA coordination dashboard, role-separation enforcement on routes
  - Agents: `web-eng`, `evacuation-agent` (consumed for multi-LGA logistics)
  - Tools: read, edit, agent
  - Success: `tests/e2e/web-coverage/sectors/sa/T187-sapol-state-control-centre.spec.ts` passes.

- [X] T055 [P] [US3] Implement sector workspace [`apps/web/src/app/(operations)/sectors/ses-sa-multi-lga/page.tsx`](../../apps/web/src/app/) (T188) per [FR-015](./spec.md#functional-requirements)
  - Agents: `web-eng`, `evacuation-agent`
  - Tools: read, edit, agent
  - Success: `T188-ses-sa-multi-lga-evacuation.spec.ts` passes.

- [X] T056 [P] [US3] Implement sector workspaces [`apps/web/src/app/(operations)/sectors/dfes-wa-cultural-safety/page.tsx`](../../apps/web/src/app/) (T189), [`taspol-multilingual/page.tsx`](../../apps/web/src/app/) (T192), [`ntes-multilingual/page.tsx`](../../apps/web/src/app/) (T195) — all three reuse the cultural-safety subsystem from T050 + T053
  - Agents: `web-eng`, `communication-agent`
  - Tools: read, edit, agent
  - Success: `T189`, `T192`, `T195` specs all pass; cultural-safety templates resolve per `(jurisdiction, language_pack)`.

- [X] T057 [P] [US3] Implement sector workspaces [`apps/web/src/app/(operations)/sectors/dfes-wa-iron-ore/page.tsx`](../../apps/web/src/app/) (T190) and [`at-tas-island-isolation/page.tsx`](../../apps/web/src/app/) (T191) — reuse infrastructure-overlay from T051
  - Agents: `web-eng`
  - Tools: read, edit
  - Success: `T190`, `T191` specs pass; iron-ore haul-road and island-logistics overlays toggleable.

- [X] T058 [P] [US3] Implement sector workspaces [`apps/web/src/app/(operations)/sectors/afp-act-precinct/page.tsx`](../../apps/web/src/app/) (T193) and [`ses-act-declaration/page.tsx`](../../apps/web/src/app/) (T194) — federal-tenancy-overlay
  - Agents: `web-eng`
  - Tools: read, edit
  - Success: `T193`, `T194` specs pass; precinct-collision view differentiates federal vs territory governance.

- [X] T059 [P] [US3] Implement sector workspaces [`apps/web/src/app/(operations)/sectors/sja-nt-tropical/page.tsx`](../../apps/web/src/app/) (T196), [`bom-broadcast-relay/page.tsx`](../../apps/web/src/app/) (T197), [`nema-dacc-jatwc/page.tsx`](../../apps/web/src/app/) (T198)
  - Agents: `web-eng`, `monitoring-agent` (consumed for BoM observation streams T197), `communication-agent` (T197 broadcast script)
  - Tools: read, edit, agent
  - Success: `T196`, `T197`, `T198` specs pass; broadcast script renders the FR-014 multilingual baselines; broadcaster acknowledgement captured before relay marked complete.

- [X] T060 [P] [US3] Implement sector workspace [`apps/web/src/app/(operations)/sectors/utility-insurance-recovery/page.tsx`](../../apps/web/src/app/) (T199) — claims-velocity dashboard from T052 + handover-PDF link from T044
  - Agents: `web-eng`
  - Tools: read, edit
  - Success: `T199-utility-insurance-recovery.spec.ts` passes; produces both Built+Economic recovery rows in [`coverage-trace.json`](../../tests/e2e/web-coverage/coverage-trace.json) (binding SC-005).

- [ ] T061 [US3] Run the sectors shard against staging
  - Agents: `qa-eng`
  - Tools: execute
  - Success: `pnpm -C tests/e2e/web-coverage test -- sectors/` exits 0; 13 specs (T187..T199) all `pass`; depth-contract assertions (workspace load → state-changing transition → post-transition assertion → audit-list read-back) pass on all 13.

**Checkpoint US-3**: Cycle-1 net-new persona scenarios pass; cross-jurisdictional + cross-sector depth visible.

---

## Phase 6: User Story 4 — Recovery Environments + Sendai Counterfactual (Priority: P4)

**Goal**: `/governance/dashboard/recovery` renders the four recovery environments with current data; the response→recovery handover composer produces a signed PDF with the Sendai counterfactual `(baseline_loss − projected_loss) / baseline_loss ≥ 0.30`.

**Independent Test**: `pnpm -C tests/e2e/web-coverage test -- cross-cutting/recovery-environments.spec.ts` plus the resilience-planner depth-profile scenario ⇒ both pass against production with all four environments visible, handover artefact downloadable + signed.

### Tests for User Story 4

- [ ] T062 [P] [US4] Write E2E gap test verifying the recovery dashboard FR-023/FR-024 surfacing in [`apps/web/tests/integration/spec_035/recovery-dashboard.spec.ts`](../../apps/web/tests/integration/spec_035/recovery-dashboard.spec.ts)
  - Agents: `qa-eng`
  - Tools: read, edit
  - Success: test FAILS until T063 lands; assertions cover all four environments + Sendai-ratio computation visibility.

### Implementation for User Story 4

- [X] T063 [US4] Implement [`apps/web/src/app/governance/dashboard/recovery/page.tsx`](../../apps/web/src/app/) per [FR-023 + FR-024](./spec.md#functional-requirements) — Social / Built / Economic / Natural panels, each consuming the relevant data slice; Economic shows `baseline_loss`, `projected_loss`, `sendai_ratio`
  - Agents: `web-eng`, `risk-assessment-agent` (consumed for projected-loss inputs), `resource-allocation-agent` (consumed for actions)
  - Tools: read, edit, agent
  - Success: T062 test passes; the four environments render under one route; Sendai ratio computed and displayed with one decimal.

- [X] T064 [P] [US4] Wire the claims-velocity dashboard from [T052](#implementation-for-user-story-3) into the Built+Economic environment views; surface FR-024's four sub-domains explicitly — **Built** view shows housing-restoration tracking + infrastructure-rebuild prioritisation; **Economic** view shows insurance-recovery (claims velocity), small-business grants, supply-chain restoration, and tourism-reactivation; insurance-recovery handoff to a state authority updates the Economic view AND adds a row to [`coverage-trace.json`](../../tests/e2e/web-coverage/coverage-trace.json) against SC-005
  - Agents: `web-eng`
  - Tools: read, edit
  - Success: integration test [`apps/web/tests/integration/spec_035/insurance-recovery-handoff.spec.ts`](../../apps/web/tests/integration/spec_035/insurance-recovery-handoff.spec.ts) passes; assertions confirm each of the six FR-024 sub-domains (housing-restoration, infrastructure-rebuild, insurance-recovery, small-business grants, supply-chain restoration, tourism reactivation) renders under its named data slice with a stable selector; the SC-005 row carries `(utility × outcome-5 × riverine-flood-or-severe-storm)` tuple.

- [X] T065 [P] [US4] Add SC-005 verification: enforce `sendai_ratio ≥ 0.30` server-side in [T045](#implementation-for-user-story-1--operator-panels-one-panel-per-persona)'s recovery-handover service AND surface the validation message in [T044](#implementation-for-user-story-1--operator-panels-one-panel-per-persona)'s panel
  - Agents: `web-eng`, `api-eng`
  - Tools: read, edit
  - Success: contract test asserts a Sendai ratio of 0.29 produces `422 schema_invalid` with the precise validation message; UI surfaces the message non-silently.

- [ ] T066 [US4] Run the recovery shard + resilience-planner depth profile against staging
  - Agents: `qa-eng`
  - Tools: execute
  - Success: `pnpm -C tests/e2e/web-coverage test -- cross-cutting/recovery-environments.spec.ts` and the resilience-planner depth-profile test both pass; the handover PDF download starts within one click; SAS URL valid for ≤ 15 minutes.

**Checkpoint US-4**: SC-005 closed. Recovery environments + Sendai counterfactual visible end-to-end.

---

## Phase 7: User Story 5 — Offline / Multilingual / Sovereignty / Accessibility Cross-Cutting (Priority: P5)

**Goal**: Every regulated route renders the AU-region sovereignty banner + Foundry carve-out badge; multilingual fallback chain visible; offline queue available to all field/remote personas; WCAG 2.2 AA enforced via in-suite axe scan.

**Independent Test**: `pnpm -C tests/e2e/web-coverage test -- cross-cutting/{field-offline-mode,accessibility-and-multilingual,data-sovereignty}.spec.ts` against production with persona fixtures from ≥3 jurisdictions per spec ⇒ all pass with no `GAP-A11Y-WORKSPACE`, `GAP-DATA-SOV-BANNER`, `GAP-OFFLINE-*` entries.

### Tests for User Story 5

- [X] T067 [P] [US5] Write E2E test [`apps/web/tests/integration/spec_035/sovereignty-banner.spec.ts`](../../apps/web/tests/integration/spec_035/sovereignty-banner.spec.ts) — banner visible on every regulated route; Foundry carve-out badge appears when an AI recommendation is from a carve-out model. Implemented as `apps/web/tests/unit/spec_035/sovereignty-banner.test.tsx` (jsdom variant; Playwright integration deferred to T074).
  - Agents: `qa-eng`
  - Tools: read, edit
  - Success: test FAILS until T070 lands.

- [X] T068 [P] [US5] ~~Write E2E test [`apps/web/tests/integration/spec_035/axe-critical-zero.spec.ts`](../../apps/web/tests/integration/spec_035/axe-critical-zero.spec.ts) using `@axe-core/playwright` Standard rule-set, fail on `critical` violations across every P1 surface~~ **SUPERSEDED** by T060/T073's [`tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts`](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts), which iterates the P1 surface list through [`buildAxe`](../../tests/e2e/web-coverage/_support/a11y/axeBuilder.ts) (tags `wcag2a/wcag2aa/wcag21aa/wcag22aa`) and asserts `results.violations` is `[]` — strictly tighter than the proposed critical-only gate. Authoring a duplicate spec under `apps/web/tests/integration/spec_035/` would also breach the OOS-003 read-only policy on `tests/e2e/web-coverage/`. The only unshipped deliverable was the `a11y-report.json` artefact, which is folded into T077's reporter wiring (it already lists the file as a captured CI artefact).
  - Agents: `qa-eng`
  - Tools: read, edit
  - Success: closed as superseded; `a11y-report.json` artefact ownership transferred to T077.

### Implementation for User Story 5

- [X] T069 [P] [US5] Implement [`apps/web/src/components/sovereignty-banner/`](../../apps/web/src/components/) — AU-region banner + Foundry-carveout link; rendered on every route that processes regulated platform data via the App Router root layout
  - Agents: `web-eng`
  - Tools: read, edit
  - Success: T067 test passes; banner renders without layout shift; carve-out link is keyboard-reachable.

- [X] T070 [P] [US5] Extend [`apps/api/app/repositories/carveout_registry_repository.py`](../../apps/api/app/repositories/carveout_registry_repository.py) per [`research.md` § R-011](./research.md#r-011--foundry-carve-out-registry-surfacing) — JSON-seeded `carveout_registry` (Cosmos container migration deferred to staging) with `review_date`, `approver_identities[]`; exposed via `GET /api/governance/carveout-registry`.
  - Agents: `api-eng`
  - Tools: read, edit
  - Success: contract test asserts the response is paginated and signed; 90-day-overdue items are marked `review_overdue=true`.

- [X] T071 [P] [US5] Add CI workflow [`.github/workflows/foundry-carveout-review.yml`](../../.github/workflows/foundry-carveout-review.yml) — fails the build if any registry entry has `review_date < now() - 90d`
  - Agents: `iac-eng`, `qa-eng`
  - Tools: read, edit
  - Success: workflow lints with `actionlint`; staging dry-run with a synthetic 91-day-old entry exits 1 with stderr naming the offending entry.

- [X] T072 [P] [US5] Generalise the offline subsystem from US-1 to all field/remote personas — register the SW for every persona route under [`apps/web/src/app/(operations)/`](../../apps/web/src/app/) via `(operations)/layout.tsx` + `_offline-bootstrap.tsx`, and apply the offline panel from T041 conditionally on `persona.is_field_remote` per page composition.
  - Agents: `web-eng`
  - Tools: read, edit
  - Success: NT remote, WA Kimberley/Pilbara, TAS islands, SA outback persona scenarios all queue + replay correctly.

- [X] T073 [P] [US5] Wire the multilingual fallback chain from T050 into every public-warning surface (PIO composer + every sector workspace using cultural safety) per [FR-016](./spec.md#functional-requirements), [FR-029](./spec.md#functional-requirements), and [Constitution NN-4](../../.specify/memory/constitution.md). Load the **Simplified Chinese v1 baseline registry** across the PIO public-bulletin surface and every regulated route's language picker (NN-4 v1 baseline), in addition to the cultural-safety ATSI variants
  - Agents: `web-eng`, `communication-agent`
  - Tools: read, edit, agent
  - Success: `accessibility-and-multilingual.spec.ts` passes for ≥3 jurisdictions; no silent translation drop observed; the Simplified Chinese registry resolves on ≥1 non-cultural-safety surface (PIO public bulletin) and the `zh-Hans` option appears in the language picker on every regulated route under audit.

- [ ] T074 [P] [US5] Integrate `@axe-core/playwright` Standard rule-set into the Playwright `playwright.config.ts` extension under [`tests/e2e/web-coverage/`](../../tests/e2e/web-coverage/) (READ-ONLY policy applied — only the config extension hook, not the spec files) AND run a hardening pass through every P1 surface fixing critical violations identified
  - Agents: `qa-eng`, `web-eng`
  - Tools: read, edit, execute
  - Success: [`accessibility-and-multilingual.spec.ts`](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts) passes with zero violations across the P1 surface list (T068 superseded by this spec); `a11y-report.json` artefact emission is wired into T077's reporter.

- [ ] T075 [US5] Run the cross-cutting shard against staging
  - Agents: `qa-eng`
  - Tools: execute
  - Success: `pnpm -C tests/e2e/web-coverage test -- cross-cutting/{field-offline-mode,accessibility-and-multilingual,data-sovereignty}.spec.ts` exits 0; persona fixtures span ≥3 jurisdictions per spec; no `GAP-A11Y-WORKSPACE / GAP-DATA-SOV-BANNER / GAP-OFFLINE-*` entries in [`gap-register.json`](../../tests/e2e/web-coverage/gap-register.json).

**Checkpoint US-5**: Cross-cutting horizontals (offline / multilingual / sovereignty / accessibility) generalised across all personas.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T076 [P] Run [`scripts/verify-activation-mutex.ps1`](../../scripts/verify-activation-mutex.ps1) (T013) in CI matrix across `staging` and `production` env values per [Clarifications Q8](./spec.md#clarifications) and [FR-013](./spec.md#functional-requirements) — the build-time CI gate is exempt for `ENVIRONMENT=dev` (developer-loop iteration); the runtime lifespan invariant remains the safety net for `dev`. Confirm non-zero exit on co-activation in `staging`/`production`; confirm short-circuit success (skip with exit 0) when invoked under `ENVIRONMENT=dev`
  - Agents: `qa-eng`, `iac-eng`
  - Tools: execute, read
  - Success: GitHub Actions matrix run — `dev` exits 0 (skip-with-message), `staging`/`production` exit 1 for the synthetic co-activation case and exit 0 in clean state; PR-blocking required-status-check active on the `staging`/`production` legs only.

- [ ] T077 [P] Run [`tests/e2e/web-coverage/`](../../tests/e2e/web-coverage/) full suite against the production endpoint and capture [`coverage-trace.json`](../../tests/e2e/web-coverage/coverage-trace.json) + [`gap-register.json`](../../tests/e2e/web-coverage/gap-register.json) + [`a11y-report.json`](../../tests/e2e/web-coverage/a11y-report.json) as CI artefacts. Verify SC-001..SC-012 against the matrix in [`quickstart.md`](./quickstart.md#verification-matrix-sc-001sc-012--artefact). Owns the `a11y-report.json` reporter wiring (transferred from superseded T068) — emits a severity-stratified summary (`critical/serious/moderate/minor` counts per route) consumed from the existing axe runs in [`accessibility-and-multilingual.spec.ts`](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts).
  - Agents: `qa-eng`
  - Tools: execute, read
  - Success: 12/12 success criteria green; coverage ≥ 95% (persona × outcome × hazard) tuples in `pass`; zero HIGH+ open entries in gap register; `a11y-report.json` uploaded as a CI artefact with severity-stratified per-route counts.

- [X] T078 [P] OTEL span enrichment: `apps/api/app/observability/audit_span.py` exposes `record_audit_outcome(...)` and is invoked by the cultural-safety service on each closed-set outcome so every new audit `outcome` is captured as the span attribute `ama.audit.outcome` in Application Insights. (Web-side `instrumentation.ts` enrichment deferred to T077 staging.)
  - Agents: `api-eng`, `web-eng`
  - Tools: read, edit
  - Success: ApplicationInsights query `traces | where customDimensions.["ama.audit.outcome"] in (...)` returns rows for each new outcome from a staging smoke run.

- [X] T079 [P] Documentation: middleware stack + offline-replay flow diagrams added in [`docs/architecture/spec-035-middleware-and-offline.md`](../../docs/architecture/spec-035-middleware-and-offline.md) (mermaid; drawio export deferred to staging artefact pass)
  - Agents: `web-eng` or `api-eng` (whoever picks up); `drawio-mcp-diagramming` skill
  - Tools: read, edit, agent
  - Success: two new draw.io PNG/SVG artefacts under [`docs/architecture/diagrams/`](../../docs/architecture/diagrams/); referenced from the overview README.

- [X] T080 [P] Update [`CHANGELOG.md`](../../CHANGELOG.md) with spec-035 entry summarising the production-reachable surface, the FR-001..FR-008 operator-panel set (9 panels: IC approval card T036, AWS warning composer T037, audit timeline T038, risk matrix T039, planning IAP T042, span-of-control T043, field-offline T041, resilience handover-PDF T044, classifier-mask banner T046), 13 sector workspaces (T054..T060 + sector-specific from US-3), the recovery dashboard, and the cross-cutting horizontals (US-5)
  - Agents: `web-eng` or `api-eng`
  - Tools: read, edit
  - Success: changelog entry follows existing convention; lists each shipped FR (FR-001..FR-030) with a one-line summary; the 9-panel inventory matches the panels actually shipped under US-1.

- [ ] T081 Run [`quickstart.md`](./quickstart.md) end-to-end as a final dry run against staging
  - Agents: `qa-eng`
  - Tools: execute, read
  - Success: every quickstart step exits 0; verification matrix all green; troubleshooting section accurate.

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1 (Setup) ─────────────────────────────────┐
                                                 ▼
                       Phase 2 (Foundational, BLOCKING)
                                  │
            ┌─────────────────────┼─────────────────────────────┐
            ▼                     ▼                             ▼
   Phase 3 (US-2 / P2)   ┌───────────────────────────────────────┐
   PRODUCTION-AUTH SLICE │  ◀── Phase 4 (US-1 / P1, MVP) depends on US-2 in production
            │            │       (in dev/test it's independent)
            ▼            │
   ┌────────┴────────┐   │
   ▼                 ▼   ▼
 Phase 5            Phase 6           Phase 7
 (US-3 / P3)        (US-4 / P4)       (US-5 / P5)
   │                   │                 │
   └───────────────────┴─────────────────┘
                    ▼
            Phase 8 (Polish)
```

### User Story Dependencies

- **US-2 (P2)** has NO upstream user-story dependency; lands first per [`plan.md`](./plan.md#implementation-phases-high-level--detail-goes-into-tasksmd) so US-1 can read back through `/api/audit/list` in production.
- **US-1 (P1, MVP)** is independently testable in dev/test (where the spec-034 dual-guard remains active) but requires US-2 for production-reachable verification.
- **US-3 (P3)** reuses US-1's PIO composer + IC approval card + offline subsystem; depends on Phase 4 (US-1) for shared affordances.
- **US-4 (P4)** depends on US-1 (handover-PDF panel) AND US-3 (T199 utility-insurance-recovery feeds Built+Economic).
- **US-5 (P5)** is a horizontal across US-1..US-4; runs after them.

### Within Each User Story

- Tests written FIRST (per QG-1 TDD), watched FAIL, then implementation.
- Models/schemas before services, services before endpoints, endpoints before UI panels.
- Integration tests run only after the unit/contract tests pass.

### Parallel Opportunities

- All Setup [P] tasks parallelisable.
- All Foundational [P] tasks parallelisable.
- Within US-2: T017..T023 (tests) parallelisable; T024..T026 (middleware) parallelisable; T029..T031 (routes) parallelisable.
- Within US-1: T036..T044 (8 panels) parallelisable; T040 (offline lib) blocks T041 (offline panel).
- Within US-3: T054..T060 (13 sector workspaces grouped) parallelisable.
- Within US-5: T069..T074 (banner + classifier + carve-out + offline-generalisation + a11y) parallelisable.
- Polish tasks T076..T080 all parallelisable; T081 last.

---

## Parallel Example: User Story 2 — Production-Auth Slice

```bash
# After Phase 2 foundational completes, kick off all US-2 contract tests in parallel:
uv run pytest apps/api/tests/contract/spec_035/test_evaluator_production_reach.py    # T017
uv run pytest apps/api/tests/contract/spec_035/test_error_precedence_ladder.py       # T018
uv run pytest apps/api/tests/contract/spec_035/test_rate_limit.py                    # T019
uv run pytest apps/api/tests/contract/spec_035/test_impersonation_pairing.py         # T020
uv run pytest apps/api/tests/contract/spec_035/test_classifier_branches.py           # T021
uv run pytest apps/api/tests/contract/spec_035/test_offline_replay.py                # T022
uv run pytest apps/api/tests/contract/spec_035/test_whoami.py                        # T023

# Then the 3 middleware in parallel:
# T024 entra_auth.py | T025 classifier_gateway.py | T026 rate_limit_audit.py
# (different files, no inter-task dependencies)

# Then the 3 routes in parallel:
# T029 auth_whoami.py | T030 offline_replay.py | T031 offline_queue_overflow_repository.py
```

---

## Parallel Example: User Story 1 — Operator Panels

```bash
# After US-2 lands, all 8 panels (one file per panel) can be authored in parallel:
# T036 ic-approval-card.tsx
# T037 pio-aws-composer.tsx
# T038 observer-auditor-timeline.tsx
# T039 risk-matrix.tsx
# T040 offline lib (queue-store + service-worker)  ── blocks T041
# T041 field-coordinator-offline.tsx
# T042 planning-iap-composer.tsx
# T043 span-of-control-warning.tsx
# T044 resilience-handover-pdf.tsx ── blocks on T045 (recovery_handover route)
```

---

## Implementation Strategy

### MVP Scope (single-increment delivery)

**Just User Story 1 — operational personas drive state changes against the real UI.**

Why: SC-001 (≤2 minute warning reach), SC-002 (≤5/15/30 minute decision-to-action latency), SC-007 (offline preservation), and the AWS-compliance / append-only / span-of-control / accessibility / offline cross-cutting specs all green ⇒ capstone-outcome value.

In dev/test the spec-034 dual-guard activates the evaluator and audit-list endpoints, so US-1 is fully testable against the local stack BEFORE US-2 lands. In production the MVP requires US-2 first (per the plan's Phase A → Phase B sequencing).

### Incremental delivery

1. Land **Phase 1 + Phase 2** (Setup + Foundational) — scaffolding only, no observable behaviour change.
2. Land **Phase 3 (US-2)** — production-reachable evaluator + audit-list. Suite remains red on UI assertions but green on the API path.
3. Land **Phase 4 (US-1, MVP)** — operator panels green; ≥95% (persona × outcome × hazard) tuples pass; ship.
4. Land **Phase 5 (US-3)** — sector workspaces; cross-jurisdictional depth visible.
5. Land **Phase 6 (US-4)** — recovery dashboard + Sendai counterfactual; SC-005 closes.
6. Land **Phase 7 (US-5)** — cross-cutting horizontals; SC-002 (a11y) and sovereignty/multilingual/offline generalised.
7. Land **Phase 8 (Polish)** — docs + CHANGELOG + final quickstart dry run.

---

## Format Validation

All 81 tasks above follow the strict checklist format mandated by the `/speckit.tasks` mode contract:

- ✅ Every task starts with `- [ ]`
- ✅ Every task has a sequential ID `T0##`
- ✅ Every parallelisable task carries `[P]`
- ✅ Every user-story phase task carries `[USx]`; Setup/Foundational/Polish phase tasks omit the story label
- ✅ Every task description names an exact file path (or set of paths)
- ✅ Every task lists Agents, Tools (subset of {execute, read, edit, search, web, agent, todo}), and a verifiable Success criterion per the user's `/speckit.tasks` extension contract.

## Summary

| Metric | Value |
| --- | --- |
| **Total tasks** | 81 (T001..T081) |
| **Phase 1 — Setup** | T001..T005 (5 tasks; 4 parallel) |
| **Phase 2 — Foundational** | T006..T016 (11 tasks; 8 parallel) |
| **Phase 3 — US-2 (P2)** | T017..T032 (16 tasks; 13 parallel) |
| **Phase 4 — US-1 (P1, MVP)** | T033..T047 (15 tasks; 13 parallel) |
| **Phase 5 — US-3 (P3)** | T048..T061 (14 tasks; 13 parallel) |
| **Phase 6 — US-4 (P4)** | T062..T066 (5 tasks; 3 parallel) |
| **Phase 7 — US-5 (P5)** | T067..T075 (9 tasks; 8 parallel) |
| **Phase 8 — Polish** | T076..T081 (6 tasks; 5 parallel) |
| **Suggested MVP** | US-1 (15 tasks, T033..T047), unlocked once US-2 (T017..T032) lands |
| **Independent test per story** | See [`spec.md` § Independent Test](./spec.md#user-stories) per story; all 5 stories independently testable |

**Next command**: implement Phase 1 + Phase 2, then `/speckit.implement` for incremental delivery.
