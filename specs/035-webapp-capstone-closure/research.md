# Phase 0 Research — Web Application Capstone Closure (spec-035)

**Spec**: [`specs/035-webapp-capstone-closure/spec.md`](./spec.md)
**Plan**: [`specs/035-webapp-capstone-closure/plan.md`](./plan.md)
**Date**: 2026-05-05

This document resolves the multi-option / unknown items in [`plan.md` § Technical Context](./plan.md#technical-context). Every research item below uses the format **Decision / Rationale / Alternatives considered**, per `/speckit.plan` Phase 0 contract.

The 10 clarifications already integrated in [`spec.md` § Clarifications](./spec.md#clarifications) leave no `NEEDS CLARIFICATION` markers in [`plan.md` § Technical Context](./plan.md#technical-context); however, the *implementation path* for each clarification still has multiple plausible approaches. The 12 research items below pick exactly one path per clarification / non-trivial constraint.

---

## R-001 — Entra ID bearer validation in FastAPI

**Question**: How does [`apps/api/`](../../apps/api/) validate production Entra ID bearer tokens, extract the `roles` (AppRole) claim, and bind a `persona_id` claim per [Clarifications Q1](./spec.md#clarifications) and [FR-010](./spec.md#functional-requirements)?

- **Decision**: Build a single FastAPI middleware [`apps/api/app/middleware/entra_auth.py`](../../apps/api/app/middleware/entra_auth.py) that uses `azure-identity` + cached JWKS (with the issuer / audience and tenant pinned via App Configuration) to validate the bearer; an internal Pydantic v2 `EntraPrincipal` model carries `persona_id`, `app_role` (one of the 11 from [Clarifications Q1](./spec.md#clarifications)), `tenant_id`, `oid`, plus the optional `impersonated_persona_id` resolved from the `X-Impersonate-Persona` header per [Clarifications Q9](./spec.md#clarifications). The middleware MUST be a no-op in `dev`/`test` when [`apps/api/app/middleware/test_support_guard.py`](../../apps/api/app/middleware/test_support_guard.py) is enabled and MUST be the only auth path in `staging`/`production` per [FR-013](./spec.md#functional-requirements) / [Clarifications Q8](./spec.md#clarifications).
- **Rationale**: `azure-identity` is the Microsoft-maintained library and integrates with managed-identity-attested JWKS download. JWKS caching avoids the latency budget hit on the ≤ 2 s audit-append SLO ([SC-009](./spec.md#measurable-outcomes)). A single middleware (rather than per-route dependencies) keeps the 11-role inventory enumerated in one place and matches the existing `test_support_guard` middleware shape, so the dual-guard contract from [FR-013](./spec.md#functional-requirements) is symmetric.
- **Alternatives considered**:
  - `fastapi-azure-auth` (community library): rejected — adds a maintenance dependency for behaviour we want pinned, and its claim-extraction surface does not natively support a per-request `X-Impersonate-Persona` override.
  - Per-route `Depends(...)` validation: rejected — would scatter the 11-role enum and the impersonation-header logic across ~5 endpoints, making a constitution audit harder.
  - APIM JWT validation only: rejected — APIM strips the bearer to a header but FastAPI still needs to extract `persona_id` and emit audit rows with the impersonation context, so we need server-side extraction anyway.

---

## R-002 — APIM rate-limit policy shape

**Question**: How is the per-`(persona_id, route)` rate-limit (10 req/min, 600 req/hr) plus the global CI ceiling (600 req/min) implemented per [FR-012](./spec.md#functional-requirements) / [Clarifications Q3](./spec.md#clarifications)?

- **Decision**: Use Azure APIM's built-in `rate-limit-by-key` policy with `counter-key="@(context.Subscription.Id + ':' + context.Request.Headers.GetValueOrDefault('X-Persona-Id', '') + ':' + context.Operation.Name)"` for the per-`(persona_id, route)` budget, layered with a global `rate-limit` policy at the API scope for the CI ceiling. APIM emits `429 Too Many Requests` with a `Retry-After` header; the FastAPI middleware [`apps/api/app/middleware/rate_limit_audit.py`](../../apps/api/app/middleware/rate_limit_audit.py) appends the audit row when the bypass header (set by APIM on a 429) is observed. The policy ships in [`infra/modules/apim-rate-limit.bicep`](../../infra/modules/apim-rate-limit.bicep), AVM-composed.
- **Rationale**: APIM is already the production gateway path per the existing IaC; the `rate-limit-by-key` counter-key syntax supports the exact tuple required by [Clarifications Q3](./spec.md#clarifications). FastAPI emitting the audit row (rather than APIM logging directly to Cosmos) keeps the audit-append code path identical for allowed and rate-limited calls — the same `audit_appender` is the single writer per [FR-013](./spec.md#functional-requirements).
- **Alternatives considered**:
  - In-process token bucket inside FastAPI (e.g., `slowapi`): rejected — does not survive horizontal scale-out without a shared backplane, and would force a Redis dependency just for rate-limiting.
  - Front Door rate-limit: rejected — Front Door's rate-limit policies do not support per-claim keys (only IP + header), so cannot key by `persona_id`.
  - Cosmos-backed in-process counter: rejected — adds latency to every request and competes with the audit-append SLO budget.

---

## R-003 — Service-Worker + IndexedDB offline subsystem

**Question**: How does [`apps/web/`](../../apps/web/) implement the offline queue per [FR-006](./spec.md#functional-requirements) / [Clarifications Q4 + Q7](./spec.md#clarifications) — Service Worker, IndexedDB schema, 500-entry cap, life-safety vs routine tiering, batched replay against `/api/offline/replay`?

- **Decision**: A native Service Worker registered from [`apps/web/src/lib/offline/service-worker.ts`](../../apps/web/src/lib/offline/service-worker.ts) intercepts `POST` requests to `/api/outcomes/*` and `/api/audit/*` when `navigator.onLine === false` OR when a heartbeat probe to `/api/health` fails. Failed mutations are written to an IndexedDB store (via `idb`) keyed by `(persona_id, correlation_id)`, with a per-record `tier` field set by client-side classification of the route + payload (life-safety vs routine, per [Clarifications Q7](./spec.md#clarifications)). On reconnect, the SW drains life-safety first (single batch, ≤ 50 entries) and then routine entries in 50-entry batches, calling `POST /api/offline/replay` with a `BatchedReplayEnvelope`. The IndexedDB store enforces the 500-entry cap with displacement-of-oldest-routine when life-safety arrives and the queue is full; overflow rejection is surfaced in the UI via the queue-depth indicator.
- **Rationale**: Native SW + IndexedDB is the standard PWA-shaped stack and is supported on all evergreen browsers + Safari 16.4+ (the browser baseline named in [`plan.md` § Target Platform](./plan.md#technical-context)). `idb` is the de-facto thin promise wrapper over IndexedDB; it adds no runtime weight and avoids the heavy Workbox module surface. Heartbeat-driven offline detection (in addition to `navigator.onLine`) is required because `navigator.onLine` is unreliable on captive-portal Wi-Fi often encountered by field operators.
- **Alternatives considered**:
  - Workbox full background-sync recipes: rejected — opinionated about retry semantics that conflict with the tiered-batched replay contract from [Clarifications Q7](./spec.md#clarifications).
  - localStorage queue: rejected — synchronous, 5 MB limit per origin, no transactional semantics for the dedupe-on-reconnect requirement.
  - Server-side queueing only (no SW): rejected — defeats the offline contract from [Constitution NN-5](../../.specify/memory/constitution.md) and [FR-006](./spec.md#functional-requirements).

---

## R-004 — PWA degraded-mode banner driver

**Question**: What signal drives the degraded-mode banner that the Field Coordinator workspace shows during connectivity loss?

- **Decision**: A React context provider [`OfflineStatusProvider`](../../apps/web/src/lib/offline/) listens to `online`/`offline` events PLUS a 30 s `setInterval` heartbeat probe to `/api/health` (a 200 response within 10 s is "online"; anything else flips to "degraded"). The banner sub-component reads queue depth from the IndexedDB store, computes `X/500` and the `Y life-safety reserved` sub-counter, and surfaces the ≥ 80% warning per [Clarifications Q7](./spec.md#clarifications). The component is reused by the cross-cutting `field-offline-mode.spec.ts` Playwright spec and by all five remote-area NT/WA/TAS/SA persona workspaces (US-5 / P5).
- **Rationale**: Heartbeat + native events is the same pattern as [R-003](#r-003--service-worker--indexeddb-offline-subsystem); reusing it for the banner keeps the offline subsystem to a single source of truth. Reading queue depth from IndexedDB rather than holding it in memory means the indicator survives a tab reload.
- **Alternatives considered**:
  - WebSocket heartbeat: rejected — adds a long-lived connection that the offline scenario explicitly assumes is unavailable.
  - Server-Sent Events: rejected for the same reason.
  - `navigator.onLine` only: rejected — captive-portal false negatives confirmed in field testing.

---

## R-005 — Activation-mutex enforcement

**Question**: How is the dual-enforcement activation mutex from [FR-013](./spec.md#functional-requirements) / [Clarifications Q8](./spec.md#clarifications) implemented — build-time CI gate (`ENVIRONMENT in {test, staging, production}`) plus container-startup lifespan invariant (all envs incl. `dev`)?

- **Decision**:
  - **Build-time gate**: `scripts/verify-activation-mutex.ps1` runs in the CI workflow ahead of the build step, statically inspects [`apps/api/app/api/routes/outcome_evaluator.py`](../../apps/api/app/api/routes/outcome_evaluator.py) and [`apps/api/app/api/routes/audit_list.py`](../../apps/api/app/api/routes/audit_list.py) for the dual-guard pattern, verifies the production-Entra middleware is wired in [`apps/api/app/main.py`](../../apps/api/app/main.py), and fails the build if `production` + `AMA_TEST_SUPPORT=1` could co-resolve. The gate runs only when `ENVIRONMENT in {test, staging, production}`; `dev` is exempt per [Clarifications Q8](./spec.md#clarifications).
  - **Lifespan invariant**: A FastAPI `lifespan` context-manager handler in [`apps/api/app/middleware/activation_mutex.py`](../../apps/api/app/middleware/activation_mutex.py) runs at every container startup (all envs incl. `dev`), evaluates whether *both* activation paths resolve to true, and if so appends an `outcome: activation_mutex_violation, environment, ama_test_support, app_role_middleware_loaded` audit row before raising `SystemExit(1)` so App Service marks the container unhealthy. The audit row is observable on the next successful boot.
- **Rationale**: Two enforcement points are required by [Clarifications Q8](./spec.md#clarifications) (CI gate AND lifespan invariant). The CI gate is fast feedback before deploy; the lifespan invariant is the runtime safety net that survives misconfigured deploys and dev-host accidents. Auditing the violation before exiting (rather than after) means the row reaches Cosmos before the process dies.
- **Alternatives considered**:
  - Lifespan invariant only: rejected — gives no pre-deploy signal; CI catches the misconfig earlier and at lower cost.
  - CI gate only: rejected — does not catch dev-host or local-tunnel accidents, and does not protect against runtime-config drift.
  - PSRule-only enforcement: rejected — PSRule covers IaC drift but not the application-code dual-guard pattern.

---

## R-006 — `X-Impersonate-Persona` paired-audit transaction

**Question**: How does the API write the paired audit rows from [Clarifications Q9](./spec.md#clarifications) (one `admin_override` row + one normal-outcome row, both in a single transaction within the ≤ 2 s SLO)?

- **Decision**: The new [`apps/api/app/middleware/audit_appender.py`](../../apps/api/app/middleware/audit_appender.py) module exposes a single async API `append_paired(rows: list[AuditRow]) -> None` that batches up to 2 rows into a Cosmos DB `TransactionalBatch` keyed by the same `correlation_id` partition key. The `entra_auth` middleware ([R-001](#r-001--entra-id-bearer-validation-in-fastapi)) sets `request.state.impersonation_context`; the route handler emits two `AuditRow` instances (one with `outcome="admin_override"` carrying `operator_identity`, `impersonated_persona_id`, `route`, `sc_id|null`, `correlation_id`; the second is the normal outcome with `operator_identity, persona_id=<target>, impersonated_by, route, correlation_id`). Direct admin actions (no header) emit a single row with `impersonated_persona_id="none"`. `GET /api/audit/list` MUST NOT hide either row (verified by the production contract test).
- **Rationale**: Cosmos DB transactional batches are atomic on a single partition key; using `correlation_id` as the partition key lets us co-locate both rows. The 2 s SLO is comfortable for a 2-row batch insert. A single writer (`append_paired`) avoids any code path that could produce one row without the other.
- **Alternatives considered**:
  - Two independent writes: rejected — creates a window where the suite can observe one row without the other, breaking [FR-011](./spec.md#functional-requirements).
  - Service Bus topic + Cosmos Change Feed projection: rejected — adds asynchronous latency that risks blowing the 2 s SLO.
  - Sticky-session impersonation: explicitly forbidden by [Clarifications Q9](./spec.md#clarifications).

---

## R-007 — Production-auth extension envelope and error precedence

**Question**: What exact wire shape do FR-009 / [Clarifications Q10](./spec.md#clarifications) errors take, and how is the precedence ladder enforced inside FastAPI?

- **Decision**:
  - **Success body** (unchanged from spec-034): `{status, evidence_refs[], metric_value, threshold, audit_id}`.
  - **Error body** (spec-035 extension envelope): `{error_code: string, retry_after_seconds: integer|null, audit_id: string, correlation_id: string}` with `error_code ∈ {unauthorized, forbidden, sovereignty_denied, rate_limited, evaluator_not_routable, schema_invalid, seed_not_ready}`.
  - **Precedence (highest → lowest)**, enforced by ordering FastAPI dependency injection / middleware:
    1. `400 evaluator_not_routable` — sc-006..sc-011 (regardless of bearer state)
    2. `403 sovereignty_denied` — NN-1 wins
    3. `401 unauthorized` — invalid / missing / expired bearer
    4. `403 forbidden` — valid bearer, wrong AppRole (FR-011 stage-b)
    5. `429 too_many_requests` — rate-limit hit
    6. `422 schema_invalid` / `503 seed_not_ready`
  - The contract is captured in [`contracts/production-auth-extension.contract.md`](./contracts/production-auth-extension.contract.md) and referenced by every contract test in `apps/api/tests/contract/spec_035/`.
- **Rationale**: Spec-034's success body MUST NOT change ([OOS-006 preserved](./spec.md#out-of-scope) / [Clarifications Q10](./spec.md#clarifications)); the extension envelope is *additive* to the error path only. The precedence ladder reflects safety priority — unrouted SC-IDs surface first because they are cheapest to detect and the response body names the CI-job owner; sovereignty wins over auth because [Constitution NN-1](../../.specify/memory/constitution.md) is non-negotiable.
- **Alternatives considered**:
  - RFC 7807 Problem Details: rejected — Q10 specifies a flat envelope; introducing `+json` content-type negotiation is gratuitous variance.
  - Extending the success body with `errors[]`: rejected — breaks [OOS-006](./spec.md#out-of-scope).
  - Error precedence enforced per-route: rejected — too easy to drift; centralising in the middleware ladder makes the contract auditable.

---

## R-008 — Classifier gateway (PSPF / PII deny / mask)

**Question**: How is the four-branch model-gateway classifier from [FR-027](./spec.md#functional-requirements) / [Clarifications Q6](./spec.md#clarifications) implemented as ADR-033 Layer 2?

- **Decision**: A FastAPI middleware [`apps/api/app/middleware/classifier_gateway.py`](../../apps/api/app/middleware/classifier_gateway.py) intercepts every request whose route processes regulated platform data (configured via App Configuration). It calls [`apps/api/app/services/classifier_gateway_service.py`](../../apps/api/app/services/classifier_gateway_service.py) which delegates to ADR-033 Layer 2 — a deterministic regex + dictionary classifier (PSPF caveats, AU-format PII patterns: TFN, Medicare, address ranges, phone, email, DOB, name+suffix combos). Branches (per [Clarifications Q6](./spec.md#clarifications)):
  - **PSPF-marked → DENY** unconditionally → `403 sovereignty_denied`; audit `outcome: classifier_deny, classifier_layer, content_class: pspf, persona_id, route`.
  - **PII without PSPF → MASK in place** (deterministic redaction); UI banner "this content was masked before processing"; audit `outcome: classifier_mask, masked_field_count, persona_id, route`.
  - **PSPF + PII → DENY** (PSPF precedence); audit `outcome: classifier_deny, content_class: pspf+pii`.
  - **Classifier failure / timeout → DENY fail-closed**; audit `outcome: classifier_failed`.
- **Rationale**: A deterministic classifier is auditable, reproducible, and fast (sub-100 ms); regex + dictionary stays well within the 2 s audit-append SLO. Fail-closed on classifier error is the only safe default given [Constitution NN-1](../../.specify/memory/constitution.md). The middleware sits inside the AU-region API process, before any model-hosting request leaves the boundary.
- **Alternatives considered**:
  - ML-based classifier: rejected — non-deterministic, drift risk, expensive to audit.
  - Foundry Content Safety + Custom Categories: rejected as Layer 2 — Content Safety is Layer 3 (semantic), but Layer 2 must be deterministic per ADR-033.
  - Mask PSPF rather than deny: rejected — Q6 fixes PSPF to DENY unconditionally.

---

## R-009 — Signed-PDF recovery handover

**Question**: How is the recovery-handover artefact rendered, signed, and stored per [FR-007](./spec.md#functional-requirements) / [Clarifications Q2](./spec.md#clarifications)?

- **Decision**:
  - **Render**: Server-side in [`apps/api/app/services/recovery_handover_service.py`](../../apps/api/app/services/recovery_handover_service.py) using `pdf-lib` (or `reportlab` if a Python-native renderer is preferred — final pick deferred to Phase 2 task estimation). The PDF includes: gap analysis, framework-modelling outputs, lessons integration, the four recovery environments (Social, Built, Economic, Natural), and the Sendai counterfactual `(baseline_loss − projected_loss) / baseline_loss`.
  - **Sign**: Detached PKCS#7 signature using a Key Vault–backed certificate; the signing identity is the App Service managed identity (audit row records the principal OID + thumbprint).
  - **Store**: Azure Blob container with a legal-hold immutability policy ([`infra/modules/blob-immutable.bicep`](../../infra/modules/blob-immutable.bicep), AVM-composed). The audit row stores blob URI + SHA-256 hash + signing identity; the UI streams the blob over a SAS URL on download.
  - **Out of scope**: machine-ingestible JSON / structured sidecars per [OOS-011](./spec.md#out-of-scope).
- **Rationale**: Server-side PDF generation keeps the signing key inside the Key Vault boundary; signing in the browser would require shipping the cert. PKCS#7 detached signature is the AS 4536-aligned standard for AU government documents. Blob immutability satisfies [QG-3](../../.specify/memory/constitution.md).
- **Alternatives considered**:
  - Client-side PDF generation with server-only signing: rejected — adds round-trips and risks payload tampering on the wire before signing.
  - Foundry-rendered PDF: rejected — would route regulated platform data through Foundry; even with carve-out compliance, the simpler in-AU-region path is preferred.
  - JSON-LD sidecar alongside PDF: rejected — out of scope per [OOS-011](./spec.md#out-of-scope).

---

## R-010 — Cultural-safety subsystem

**Question**: How are AWS-level-conditional timeout outcomes from [FR-016](./spec.md#functional-requirements) / [Clarifications Q5](./spec.md#clarifications) implemented?

- **Decision**:
  - **Routing**: [`apps/api/app/services/cultural_safety_service.py`](../../apps/api/app/services/cultural_safety_service.py) routes a draft warning to the configured community elder for the persona's jurisdiction (NT, WA, TAS, etc.) via Service Bus; the elder responds via a UI affordance authenticated by Entra (existing tenant; no new IdP per [OOS-005](./spec.md#out-of-scope)).
  - **Timeout**: 90-second default (sourced from App Configuration). On timeout:
    - **AWS level = Emergency Warning (Red)**: IC may publish English-only with a `cultural_safety_timeout_override` audit row identifying the IC operator. Cultural-safety variant continues to render as "pending elder approval" until the elder responds.
    - **AWS level = Watch and Act (Orange)**: warning is held; suite renders a "cultural-safety pending" badge and the IC may extend the timeout once.
    - **AWS level = Advice (Yellow)**: warning is held until elder approval is recorded.
  - **Audit**: every state transition (draft, sent-to-elder, elder-approved, elder-declined, timeout, override) appends a row identifying the elder and the IC-confirmer where applicable.
- **Rationale**: Life-safety calculus dictates the override; Red-level warnings have direct safety consequences and must surface even if the cultural-safety path is delayed, but the override must be IC-authorised and audited. Lower levels can afford to wait for elder approval.
- **Alternatives considered**:
  - Always block on elder approval: rejected — risks delaying Red warnings; conflicts with [Constitution V-A](../../.specify/memory/constitution.md) (life-saving principle).
  - Always publish on timeout: rejected — strips the cultural-safety guarantee for lower-urgency warnings.

---

## R-011 — Foundry carve-out registry surfacing

**Question**: How is the Foundry carve-out registry surfaced per [FR-026](./spec.md#functional-requirements) / [SC-011](./spec.md#measurable-outcomes)?

- **Decision**: A Cosmos DB container `carveout_registry` keyed by `(model_name, region)` with fields `business_justification, approver_identities[], review_date`. A read-only API `GET /api/governance/carveout-registry` surfaces the list; the web sovereignty banner contains a "Carve-out registry" link that opens a side panel rendering the list. CI fails if any entry has `review_date` older than 90 days (fail-build per [SC-011](./spec.md#measurable-outcomes)).
- **Rationale**: Cosmos is already the AU-region store; the registry is small (< 50 entries) so cost is negligible. Banner link surfaces the registry without forcing every page to render the full list.
- **Alternatives considered**:
  - Markdown file in repo: rejected — drifts from runtime state and cannot enforce 90-day review at runtime.
  - App Configuration entries: rejected — App Configuration is for feature flags / scalars, not list data with structured per-row metadata.

---

## R-012 — `@axe-core/playwright` integration

**Question**: How is WCAG 2.2 AA enforced in-suite per [FR-028](./spec.md#functional-requirements) / [SC-010](./spec.md#measurable-outcomes)?

- **Decision**: The cross-cutting `accessibility-and-multilingual.spec.ts` Playwright spec invokes `@axe-core/playwright` against every P1 surface (persona workspace, governance dashboard route, AWS composer, simulation control surface, audit-timeline view). The check is run in `Standard` rule-set (which covers WCAG 2.2 AA-relevant rules); the spec fails on any `critical` violation. New / updated P1 surfaces opt-in via a `data-axe="page"` attribute on the root layout.
- **Rationale**: `@axe-core/playwright` is the official Deque integration; the `Standard` rule-set is calibrated to WCAG 2.2 AA. Failing on `critical` only (rather than `serious` or below) matches [SC-010](./spec.md#measurable-outcomes)'s "no critical violations" wording while leaving room for non-blocking warnings.
- **Alternatives considered**:
  - Pa11y CI: rejected — runs against the deployed URL, not the Playwright session, and would duplicate auth setup.
  - Storybook a11y addon: rejected — covers components in isolation, not the full page composition the suite asserts.

---

## Summary table — research items → spec clauses

| Research | Spec clause(s) |
|---|---|
| R-001 Entra bearer validation | [FR-010](./spec.md#functional-requirements), [Clarifications Q1](./spec.md#clarifications) |
| R-002 APIM rate-limit | [FR-012](./spec.md#functional-requirements), [Clarifications Q3](./spec.md#clarifications) |
| R-003 SW + IndexedDB queue | [FR-006](./spec.md#functional-requirements), [Clarifications Q4 + Q7](./spec.md#clarifications) |
| R-004 Degraded-mode banner | [FR-006](./spec.md#functional-requirements) |
| R-005 Activation mutex | [FR-013](./spec.md#functional-requirements), [Clarifications Q8](./spec.md#clarifications) |
| R-006 Paired-audit transaction | [FR-011](./spec.md#functional-requirements), [Clarifications Q9](./spec.md#clarifications) |
| R-007 Auth extension envelope | [FR-009](./spec.md#functional-requirements), [Clarifications Q10](./spec.md#clarifications) |
| R-008 Classifier gateway | [FR-027](./spec.md#functional-requirements), [Clarifications Q6](./spec.md#clarifications) |
| R-009 Signed-PDF handover | [FR-007](./spec.md#functional-requirements), [Clarifications Q2](./spec.md#clarifications) |
| R-010 Cultural-safety timeout | [FR-016](./spec.md#functional-requirements), [Clarifications Q5](./spec.md#clarifications) |
| R-011 Carve-out registry | [FR-026](./spec.md#functional-requirements) |
| R-012 axe-core integration | [FR-028](./spec.md#functional-requirements), [SC-010](./spec.md#measurable-outcomes) |

All `NEEDS CLARIFICATION` items from [`plan.md` § Technical Context](./plan.md#technical-context) are resolved. No deferrals remain at the Phase-0 boundary.
