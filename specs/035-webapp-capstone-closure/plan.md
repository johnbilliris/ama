# Implementation Plan: Web Application Capstone Closure

**Branch**: `035-webapp-capstone-closure` | **Date**: 2026-05-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from [`specs/035-webapp-capstone-closure/spec.md`](./spec.md)

## Summary

Spec-035 closes the web-application gap that spec-034 measured: the capstone Playwright suite is wired correctly but most of its persona × outcome × hazard tuples bail at affordance lookup because [`apps/web/`](../../apps/web/) ships only a generic `PersonaWorkspace` shell and the production FastAPI surface dual-guards `/api/outcomes/*` and `/api/audit/list` off. The slice ships persona-specific safety-critical workflow surfaces (US-1), production-reachable evaluator + audit-list with Entra-bound RBAC and tiered rate-limiting (US-2), 13 cycle-1 net-new sector workspaces T187..T199 (US-3), the four recovery environments + signed-PDF handover (US-4), and the cross-cutting offline / multilingual / sovereignty / accessibility primitives (US-5). The technical approach builds on three existing runtimes — the Next.js 16 App Router web app, the FastAPI coordination API, and the Python autonomous agents — composed through the existing AVM-first Bicep IaC ([`infra/main.bicep`](../../infra/main.bicep)) and the existing Cosmos / Service Bus / App Configuration / Foundry footprint.

The 10 clarifications captured in [`spec.md` § Clarifications](./spec.md#clarifications) lock the contract surface: **Q1** fixes the 11-AppRole inventory, **Q2** locks signed-PDF-only recovery handover, **Q3** fixes per-`(persona_id, route)` token bucket plus global CI ceiling, **Q4** fixes the Service-Worker + IndexedDB + `/api/offline/replay` offline subsystem, **Q5** fixes the AWS-level-conditional cultural-safety timeout, **Q6** fixes the four-branch model-gateway classifier policy (PSPF→deny, PII→mask, both→deny, fail→deny), **Q7** fixes the 500-entry tiered offline queue + tiered SLO, **Q8** fixes the dual-enforcement activation mutex (CI gate + lifespan invariant), **Q9** fixes the `X-Impersonate-Persona` header impersonation surface with paired audit rows, and **Q10** fixes the additive production-auth error-contract extension envelope layered on the spec-034 evaluator contract.

## Technical Context

**Language/Version**:

- Web: TypeScript 5.7, Next.js 16 (App Router), React 19, Node.js ≥ 20
- API: Python 3.13, FastAPI 0.115, Pydantic v2
- Agents: Python 3.13, Microsoft Agent Framework SDK ([`apps/agents/maf_runtime/`](../../apps/agents/maf_runtime/))
- Tests: Playwright 1.49 (E2E), pytest (API), Vitest (web unit)

**Primary Dependencies**:

- Web: Next.js (App Router + Server Components), `@azure/msal-react` for Entra bearer acquisition, native Service Worker with Workbox helpers for the offline subsystem, IndexedDB via `idb`, `@axe-core/playwright` for in-suite WCAG 2.2 AA scans, `pdf-lib` for the signed recovery handover
- API: FastAPI, Pydantic v2, `azure-identity` (Entra token validation via JWKS), Azure Cosmos SDK, Azure Service Bus SDK, Azure App Configuration SDK, Azure Communication Services SDK, OpenTelemetry (existing observability layer)
- Agents: Microsoft Agent Framework runtime ([`apps/agents/maf_runtime/`](../../apps/agents/maf_runtime/)), shared with the existing `communication / evacuation / monitoring / planning / resource_allocation / risk_assessment` agents
- Shared: `packages/domain` (TypeScript domain types), `packages/schemas` (JSON-Schema contracts)

**Storage**:

- Cosmos DB (audit-timeline container, append-only at the data layer per [ASM-009](./spec.md#assumptions)) — the AU-region store for audit, evidence, incidents, recommendations
- Cosmos DB (carve-out registry container) — Foundry carve-out list with `review_date`, `approver_identities[]`
- Azure Blob Storage (signed-PDF recovery handover artefacts) — versioned, immutability policy on the container ([FR-007](./spec.md#functional-requirements))
- Azure App Configuration (rate-limit budgets, feature flags, environment toggles per [ADR-031](../../docs/aidr/decisions/adr-031-progressive-delivery-pipeline.md))
- Browser IndexedDB (offline queue, per `persona_id`, capped at 500 entries per [Clarifications Q7](./spec.md#clarifications))
- Azure Key Vault (signing key for handover PDFs, JWKS cache) — never holds regulated platform data

**Testing**:

- API: pytest with `apps/api/app/tests/` and `apps/api/tests/` (existing); new contract tests under `apps/api/tests/contract/spec_035/`
- Web unit: Vitest (existing under `apps/web/`)
- E2E: Playwright suite at [`tests/e2e/web-coverage/`](../../tests/e2e/web-coverage/) — **read-only for spec-035** per [OOS-003](./spec.md#out-of-scope)
- Accessibility: `@axe-core/playwright` integrated into the cross-cutting `accessibility-and-multilingual.spec.ts`
- Offline: Playwright `context.setOffline(true)` plus a deterministic IndexedDB fixture seeding 500 entries (life-safety + routine tier mix) for SC-007 tier-SLO assertions
- Activation-mutex: a CI gate script at `scripts/verify-activation-mutex.ps1` plus a FastAPI lifespan smoke test asserting non-zero exit on co-activation ([FR-013](./spec.md#functional-requirements))

**Target Platform**:

- Production: Azure App Service (Linux container, AU-East), AVM-deployed per [`infra/main.bicep`](../../infra/main.bicep)
- API gateway / rate-limit policy: Azure APIM (AVM module) per [FR-012](./spec.md#functional-requirements)
- Foundry carve-out endpoint: explicitly allowed non-AU model-hosting only; data-minimisation enforced at the platform model gateway per [Constitution NN-1](../../.specify/memory/constitution.md) carve-out
- Browser: Service Worker–supporting evergreen browsers (Chromium, Firefox, Safari 16.4+); native PWA install optional, not required by [FR-006](./spec.md#functional-requirements)

**Project Type**: Multi-runtime web platform (Next.js dashboard + FastAPI coordination API + Python autonomous agents). The repo is a pnpm + uv monorepo with apps under [`apps/`](../../apps/), shared packages under [`packages/`](../../packages/), IaC under [`infra/`](../../infra/), and the validation suite under [`tests/e2e/web-coverage/`](../../tests/e2e/web-coverage/).

**Performance Goals**:

- Audit-append latency ≤ 2 s p95 for every production call ([SC-009](./spec.md#measurable-outcomes), inherited from spec-034)
- AWS warning publish-to-render time ≤ 2 minutes (including community-language variant), [SC-005](./spec.md#measurable-outcomes)
- Decision-to-action latency ≤ 5 / 15 / 30 minutes for AIIMS Levels 1 / 2 / 3, [SC-006](./spec.md#measurable-outcomes)
- Offline-queue replay tiered SLOs per [SC-007](./spec.md#measurable-outcomes) per [Clarifications Q7](./spec.md#clarifications): life-safety ≤ 30 s for 50 entries; routine ≤ 30 s per 50-entry batch; full-cap drain ≤ 5 minutes
- Suite ceiling ≤ 45 minutes wall-clock on `ubuntu-latest`, [SC-012](./spec.md#measurable-outcomes)
- Per-`(persona_id, route)` rate-limit: 10 req/min, 600 req/hr; global CI ceiling 600 req/min ([FR-012](./spec.md#functional-requirements))

**Constraints**:

- AU-region data residency for all regulated platform data ([Constitution NN-1](../../.specify/memory/constitution.md)); only Foundry model-hosting endpoints may sit non-AU under the carve-out, with PSPF→deny / PII→mask / fail→deny gateway policy per [FR-027](./spec.md#functional-requirements) / [Clarifications Q6](./spec.md#clarifications)
- Append-only audit timeline ([Constitution NN-2](../../.specify/memory/constitution.md), [FR-003](./spec.md#functional-requirements), [FR-013](./spec.md#functional-requirements)) — UI + API both surface and enforce append-only semantics
- WCAG 2.2 AA on every operator surface ([Constitution NN-3](../../.specify/memory/constitution.md), [FR-028](./spec.md#functional-requirements), [SC-010](./spec.md#measurable-outcomes))
- Multilingual baseline (Simplified Chinese v1 + ATSI placeholder) plus jurisdiction-specific language packs ([Constitution NN-4](../../.specify/memory/constitution.md), [FR-016](./spec.md#functional-requirements), [FR-029](./spec.md#functional-requirements))
- Offline-capable for field roles ([Constitution NN-5](../../.specify/memory/constitution.md), [FR-006](./spec.md#functional-requirements))
- TDD ([QG-1](../../.specify/memory/constitution.md)) — every FR-001..FR-030 lands behind a failing test first; see [`tests/e2e/web-coverage/`](../../tests/e2e/web-coverage/) (read-only) plus new `apps/api/tests/contract/spec_035/`
- AVM-first IaC ([ASM-006](./spec.md#assumptions), [OOS-007](./spec.md#out-of-scope)) — no hand-rolled `Microsoft.*` resources unless an AVM module does not exist
- Spec-034 contract is locked ([OOS-003](./spec.md#out-of-scope)) — spec-035 layers an additive production-auth extension envelope per [Clarifications Q10](./spec.md#clarifications); no breaking changes to SC-001..SC-005 evaluator response shape

**Scale/Scope**:

- 68 personas × ~10 outcomes × ~10 hazards = ~6 800 coverage tuples in [`coverage-trace.json`](../../tests/e2e/web-coverage/_artifacts/) target ≥ 95% pass rate
- 13 net-new persona workspaces (T187..T199) plus the 10 operational persona workspace surfaces
- 30 functional requirements (FR-001..FR-030), 12 success criteria (SC-001..SC-012), 11 OOS items, 10 ASM items
- 11-role Entra AppRole inventory, ~7 new web routes / panels, ~5 new API endpoints (`/api/offline/replay`, `/api/auth/whoami`, `/api/audit/list` production reach, classifier-gateway-side endpoints, `/api/recovery/handover/sign`)

## Constitution Check

> *Reference: [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md) v1.2.0*

**GATE — Initial check (pre-Phase 0)**:

| Constitution clause | Spec-035 mapping | Status | Evidence |
|---|---|---|---|
| **NN-1 Data sovereignty** (AU-region; Foundry carve-out; data-minimisation gateway) | [FR-009](./spec.md#functional-requirements)..[FR-013](./spec.md#functional-requirements), [FR-025](./spec.md#functional-requirements)..[FR-027](./spec.md#functional-requirements); [Clarifications Q6](./spec.md#clarifications); [SC-011](./spec.md#measurable-outcomes) | **PASS** | All persistence is AU-East ([ASM-009](./spec.md#assumptions)); only Foundry model-hosting may sit non-AU; PSPF→deny / PII→mask gateway policy in [FR-027](./spec.md#functional-requirements) |
| **NN-2 Append-only audit** | [FR-003](./spec.md#functional-requirements), [FR-013](./spec.md#functional-requirements); [SC-009](./spec.md#measurable-outcomes) | **PASS** | UI + API both surface and enforce append-only semantics; [FR-013](./spec.md#functional-requirements) requires every prod call (allowed/denied/rate-limited/schema-rejected) to append a row within ≤ 2 s |
| **NN-3 WCAG 2.2 AA** | [FR-028](./spec.md#functional-requirements); [SC-010](./spec.md#measurable-outcomes) | **PASS** | Every P1 surface enumerated in spec-034 FR-014 emits `GAP-A11Y-WORKSPACE` if it fails; `@axe-core/playwright` enforces in-suite |
| **NN-4 Multilingual (incl. ATSI + Simplified Chinese)** | [FR-002](./spec.md#functional-requirements), [FR-016](./spec.md#functional-requirements), [FR-029](./spec.md#functional-requirements); [Clarifications Q5](./spec.md#clarifications) | **PASS** | Cultural-safety subsystem with AWS-level-conditional timeout outcomes ([FR-016](./spec.md#functional-requirements)); fallback chain en → community-language → en visible to operator |
| **NN-5 Offline-capable for field roles** | [FR-006](./spec.md#functional-requirements); [Clarifications Q4 + Q7](./spec.md#clarifications); [SC-007](./spec.md#measurable-outcomes) | **PASS** | Service-Worker + IndexedDB + `/api/offline/replay`; 500-entry cap with life-safety / routine tiering and tiered SLOs |
| **QG-1 TDD** | [FR-001](./spec.md#functional-requirements)..[FR-030](./spec.md#functional-requirements) all behind failing-tests-first | **PASS** | spec-034 web-coverage suite is the failing-test surface for the UI work (read-only [OOS-003](./spec.md#out-of-scope)); new pytest contract suite covers FR-009..FR-013 |
| **QG-2 Evidence-bound** | Every SC-001..SC-012 names an artefact / numeric threshold | **PASS** | [`coverage-trace.json`](../../tests/e2e/web-coverage/_artifacts/), [`gap-register.json`](../../specs/034-webapp-capstone-coverage/), audit-timeline rows |
| **QG-3 Immutable evidence** | [FR-007](./spec.md#functional-requirements) signed PDF, [FR-013](./spec.md#functional-requirements) audit hash chain | **PASS** | Recovery handover PDF is signed + immutably referenced ([Clarifications Q2](./spec.md#clarifications)); audit-timeline rows are byte-identical on read-back |
| **AVM-first IaC** | [ASM-006](./spec.md#assumptions), [OOS-007](./spec.md#out-of-scope) | **PASS** | New rate-limit / WAF / App Configuration consumed via existing AVM modules in [`infra/modules/`](../../infra/modules/); no new hand-rolled `Microsoft.*` |
| **Human-in-the-loop** (Constitution Non-Negotiable #1) | [FR-001](./spec.md#functional-requirements) IC approval gate, [FR-016](./spec.md#functional-requirements) IC override on cultural-safety timeout, [FR-008](./spec.md#functional-requirements) span-of-control | **PASS** | No publish path bypasses IC approval; admin override audited per [FR-011](./spec.md#functional-requirements) / [Clarifications Q9](./spec.md#clarifications) |

**Initial gate verdict**: **PASS** — no constitutional violations identified. No entries required in `## Complexity Tracking`.

**GATE — Post-Phase-1 re-check**: see end of this document.

## Project Structure

### Documentation (this feature)

```text
specs/035-webapp-capstone-closure/
├── spec.md                       # Feature specification (locked after /speckit.clarify rounds 1+2; 10 clarifications integrated)
├── plan.md                       # This file (/speckit.plan output)
├── research.md                   # Phase 0 output — research decisions resolving the technical-context unknowns
├── data-model.md                 # Phase 1 output — entities + relationships derived from spec.md § Key Entities
├── quickstart.md                 # Phase 1 output — step-by-step run guide for production-reachable mode + dev/test mode
├── contracts/                    # Phase 1 output — interface contracts
│   ├── production-auth-extension.contract.md   # FR-009 / Clarifications Q10 — extension envelope, error precedence
│   ├── offline-replay.openapi.yaml             # FR-006 / Clarifications Q4 + Q7 — /api/offline/replay request/response + 500-cap rejection
│   ├── auth-rbac.openapi.yaml                  # FR-010 / FR-011 / Clarifications Q1 + Q9 — Entra bearer + 11 AppRoles + X-Impersonate-Persona
│   ├── rate-limit.policy.md                    # FR-012 / Clarifications Q3 — APIM rate-limit policy + global CI ceiling
│   ├── classifier-gateway.contract.md          # FR-027 / Clarifications Q6 — PSPF→deny / PII→mask / fail→deny + audit shape
│   ├── recovery-handover.contract.md           # FR-007 / Clarifications Q2 — signed-PDF only, hash + signing identity
│   └── cultural-safety.contract.md             # FR-016 / Clarifications Q5 — AWS-level-conditional timeout outcomes + IC confirmer
├── checklists/
│   └── requirements.md           # Spec quality checklist (round-1 + round-2 audit trail)
└── tasks.md                      # Phase 2 output — produced by /speckit.tasks (NOT by /speckit.plan)
```

### Source Code (repository root)

The repo is an existing pnpm + uv monorepo. Spec-035 is **additive only** to the source layout below; no directories are renamed or restructured.

```text
apps/
├── web/                                  # Next.js 16 App Router web dashboard
│   ├── src/
│   │   ├── app/
│   │   │   ├── (operations)/
│   │   │   │   ├── workspaces/[personaId]/
│   │   │   │   │   ├── page.tsx                              # PersonaWorkspace shell (existing)
│   │   │   │   │   └── _panels/                              # NEW: persona-specific safety-critical panels
│   │   │   │   │       ├── ic-approval-card.tsx              # FR-001 — IC approve/decline with rationale + source refs + confidence
│   │   │   │   │       ├── pio-aws-composer.tsx              # FR-002 — AWS-compliant PIO composer (level + nested model + community-language)
│   │   │   │   │       ├── field-coordinator-offline.tsx     # FR-006 / Q4 + Q7 — degraded-mode banner + queue-depth indicator
│   │   │   │   │       ├── observer-auditor-timeline.tsx     # FR-003 — append-only audit-timeline UX
│   │   │   │   │       ├── risk-matrix.tsx                   # FR-004 — Live Risk Matrix with route comparison
│   │   │   │   │       ├── planning-iap-composer.tsx         # FR-005 — Forecast + IAP composer with provenance pills
│   │   │   │   │       ├── resilience-handover-pdf.tsx       # FR-007 / Q2 — signed-PDF composer
│   │   │   │   │       └── span-of-control-warning.tsx       # FR-008 — > 7 direct reports warning
│   │   │   │   ├── sectors/                                  # NEW: T187..T199 sector workspaces
│   │   │   │   │   ├── sapol-control-centre/page.tsx         # FR-014 (T187)
│   │   │   │   │   ├── ses-sa-multi-lga/page.tsx             # FR-015 (T188)
│   │   │   │   │   ├── dfes-wa-cultural-safety/page.tsx      # FR-016 (T189) — re-used by TasPol/NTES
│   │   │   │   │   ├── dfes-wa-iron-ore/page.tsx             # FR-017 (T190)
│   │   │   │   │   ├── at-tas-island-isolation/page.tsx      # FR-017 (T191)
│   │   │   │   │   ├── taspol-multilingual/page.tsx          # FR-016 (T192)
│   │   │   │   │   ├── afp-act-precinct/page.tsx             # FR-018 (T193)
│   │   │   │   │   ├── ses-act-declaration/page.tsx          # FR-018 (T194)
│   │   │   │   │   ├── ntes-multilingual/page.tsx            # FR-016 (T195)
│   │   │   │   │   ├── sja-nt-tropical/page.tsx              # FR-019 (T196)
│   │   │   │   │   ├── bom-broadcast-relay/page.tsx          # FR-020 (T197)
│   │   │   │   │   ├── nema-dacc-jatwc/page.tsx              # FR-021 (T198)
│   │   │   │   │   └── utility-insurance-recovery/page.tsx   # FR-022 (T199)
│   │   │   ├── governance/dashboard/recovery/page.tsx        # FR-023 / FR-024 — four recovery environments + Sendai counterfactual
│   │   │   └── api/                                          # Next.js Route Handlers (proxy / SW glue only — business logic stays in FastAPI)
│   │   ├── components/
│   │   │   ├── workspaces/
│   │   │   ├── cultural-safety/                              # NEW — language-pack registry, elder-approval routing UI
│   │   │   ├── infrastructure-overlay/                       # NEW — iron-ore / maritime / federal-precinct overlays
│   │   │   ├── claims-velocity/                              # NEW — ICA dashboard
│   │   │   └── audit-timeline/                               # extended for append-only UX + admin-impersonation badge
│   │   ├── lib/
│   │   │   ├── auth/entra-msal.ts                            # NEW — MSAL bearer acquisition for production-reachable mode
│   │   │   ├── offline/service-worker.ts                     # NEW — SW intercept + IndexedDB queue (Q4 + Q7)
│   │   │   ├── offline/queue-store.ts                        # NEW — IndexedDB wrapper with 500-cap + tier classification
│   │   │   ├── classifier/banner.tsx                         # NEW — "this content was masked before processing" banner (Q6)
│   │   │   └── i18n/language-packs.ts                        # NEW — Kimberley/Pilbara, palawa, Yolŋu Matha, Pitjantjatjara, Warlpiri registry
│   │   └── instrumentation.ts                                # Existing OTEL hook (extended for sovereignty banner audit + classifier audit)
│   └── tests/                                                # Vitest (existing) — extended with offline-queue-store + classifier-banner unit tests
│
├── api/                                  # FastAPI coordination API
│   ├── app/
│   │   ├── api/
│   │   │   ├── router.py                                     # Modified — production-reachable registration block for FR-009..FR-013
│   │   │   └── routes/
│   │   │       ├── outcome_evaluator.py                      # Existing — dual-guarded; production registration is layered, not replaced
│   │   │       ├── audit_list.py                             # Existing — same pattern
│   │   │       ├── offline_replay.py                         # NEW — POST /api/offline/replay with dedupe + tier audit + 500-cap reject (Q4 + Q7)
│   │   │       ├── auth_whoami.py                            # NEW — GET /api/auth/whoami returning resolved AppRole + persona_id + impersonation context
│   │   │       └── recovery_handover.py                      # NEW — POST /api/recovery/handover/sign emitting signed PDF with hash + signing identity
│   │   ├── middleware/
│   │   │   ├── test_support_guard.py                         # Existing — dual-guard env check
│   │   │   ├── entra_auth.py                                 # NEW — JWKS bearer validation, AppRole + persona_id claim extraction, X-Impersonate-Persona handling (Q9)
│   │   │   ├── activation_mutex.py                           # NEW — lifespan invariant rejecting co-activation (FR-013 / Q8); appends activation_mutex_violation
│   │   │   ├── rate_limit_audit.py                           # NEW — APIM passes 429s; this middleware appends the per-call audit row
│   │   │   ├── classifier_gateway.py                         # NEW — model-gateway PSPF/PII deny/mask (Q6); proxies to ADR-033 Layer 2
│   │   │   └── audit_appender.py                             # NEW — single transaction, paired-row writer for Q9 admin-impersonation
│   │   ├── services/
│   │   │   ├── outcome_evaluator_service.py                  # Existing — unchanged contract; production registration only adds auth + audit middleware around it
│   │   │   ├── recovery_handover_service.py                  # NEW — gather Sendai counterfactual, render PDF, KeyVault sign, blob immutability
│   │   │   ├── cultural_safety_service.py                    # NEW — elder-approval routing, AWS-level-conditional timeout (Q5)
│   │   │   ├── classifier_gateway_service.py                 # NEW — ADR-033 Layer 2 deterministic redaction client
│   │   │   └── offline_replay_service.py                     # NEW — dedupe by (persona_id, correlation_id), tier accounting, overflow rejection
│   │   ├── repositories/
│   │   │   ├── audit_repository.py                           # Existing — extended with paired-row transaction support (Q9)
│   │   │   ├── carveout_registry_repository.py               # Existing or extended for Q6 — review_date, approver_identities[]
│   │   │   └── offline_queue_overflow_repository.py          # NEW — overflow envelopes for queue_overflow audit
│   │   ├── core/                                             # Existing config / settings
│   │   ├── observability/                                    # Existing OTEL — extended with new audit-row outcomes
│   │   └── main.py                                           # Modified — wire activation_mutex lifespan + entra_auth middleware
│   └── tests/
│       ├── contract/spec_035/                                # NEW — pytest contract tests for FR-009..FR-013 + Q6/Q7/Q8/Q9/Q10
│       ├── integration/spec_035/                             # NEW — auth + RBAC + impersonation + classifier + offline-replay
│       └── unit/                                             # NEW — middleware unit tests (entra_auth, activation_mutex, classifier_gateway)
│
├── agents/                              # Python autonomous agents (Microsoft Agent Framework)
│   ├── communication/                                        # Existing — extended to consume Q5 cultural-safety service for ATSI variants
│   ├── evacuation/                                           # Existing — consumes FR-015 multi-LGA logistics
│   ├── monitoring/                                           # Existing
│   ├── planning/                                             # Existing — consumes FR-005 IAP composer
│   ├── resource_allocation/                                  # Existing
│   ├── risk_assessment/                                      # Existing — emits FR-004 live risk matrix recommendations
│   ├── maf_runtime/                                          # Existing — agent shell; spec-035 does NOT add new agent classes (additive UI surfaces consume existing agent outputs)
│   └── common/                                               # Existing shared utilities; extended with Q6 classifier client
│
├── eval-runner/                          # Existing — LLM evaluation harness; out of scope for spec-035 except for compatibility
└── ingestion/                            # Existing — data ingestion pipeline; out of scope

packages/
├── domain/                                                   # NEW — TypeScript domain types: AppRole, PersonaId, OfflineQueueEntry tier, AuditOutcome enum
├── schemas/                                                  # Extended — JSON-Schema for offline-replay envelope, paired-audit shape (Q9), classifier audit (Q6)
├── prompts/                                                  # Existing
├── ui/                                                       # Existing shared UI primitives
├── eval-core/                                                # Existing
└── eval-dataset/                                             # Existing

infra/
├── main.bicep                                                # Modified — wire APIM rate-limit policy module, App Configuration values for FR-012, additional KeyVault key for FR-007 PDF signing
├── modules/
│   ├── apim-rate-limit.bicep                                 # NEW — AVM-composed APIM policy for per-(persona_id, route) bucket + global ceiling (FR-012 / Q3)
│   ├── blob-immutable.bicep                                  # NEW — AVM-composed Blob container with immutability policy for FR-007 signed PDFs
│   ├── app-configuration.bicep                               # Extended — rate-limit budget keys, cultural-safety timeout default (90s), offline-cap (500)
│   └── ...                                                   # Existing modules unchanged
├── policies/                                                 # Existing — extended with FR-027 deny-by-default classifier policy doc reference
└── policy/                                                   # Existing PSRule policies — extended for activation-mutex CI gate (FR-013 / Q8)

scripts/
├── verify-activation-mutex.ps1                               # NEW — CI gate for FR-013 / Q8: fails build if co-activation detected for ENVIRONMENT in {test,staging,production}
├── verify-spec-hardening.ps1                                 # Existing
└── ...

tests/
└── e2e/web-coverage/                                         # READ-ONLY for spec-035 (OOS-003); spec-035 work is judged by this suite running green
```

**Structure Decision**: Multi-runtime web platform — Next.js 16 web ([`apps/web/`](../../apps/web/)) + FastAPI 0.115 API ([`apps/api/`](../../apps/api/)) + Python autonomous agents ([`apps/agents/`](../../apps/agents/)) — composed via the existing AVM-first Bicep IaC ([`infra/main.bicep`](../../infra/main.bicep)). Spec-035 ships **additive surfaces only**: new persona panels, new sector workspaces, new middleware (entra_auth, activation_mutex, rate_limit_audit, classifier_gateway), and new endpoints (`/api/offline/replay`, `/api/auth/whoami`, `/api/recovery/handover/sign`). The autonomous agents are **consumed unchanged** — spec-035 wires their existing outputs into the new operator-facing affordances rather than introducing new agent classes. The Playwright suite at [`tests/e2e/web-coverage/`](../../tests/e2e/web-coverage/) is the failing-test surface for the UI work and is read-only per [OOS-003](./spec.md#out-of-scope).

## Implementation Phases (high-level — detail goes into tasks.md)

This plan ends at Phase 2 planning per the speckit.plan command contract. Implementation phases are sketched only to make the dependency graph legible:

- **Phase A — Production-reachable evaluator + audit-list (US-2 / P2)**: entra_auth middleware, activation_mutex lifespan invariant, rate_limit middleware + APIM policy, audit_appender paired-row writer, contract tests for FR-009..FR-013 + Q10 error precedence. Lands first because every UI workflow assertion in P1 reads back through `/api/audit/list` in production. Independently testable per [US-2 § Independent Test](./spec.md#user-story-2--capstone-evaluator-and-audit-list-endpoints-reachable-in-production-with-auth-and-rbac-priority-p2).
- **Phase B — Operational persona panels (US-1 / P1)**: 8 panels under `apps/web/src/app/(operations)/workspaces/[personaId]/_panels/` + offline subsystem (Q4 + Q7) + observer-auditor append-only UX + risk matrix + IAP composer + signed-PDF handover. Depends on Phase A so audit reads succeed in production; depends on shared UI primitives in `packages/ui`. Independently testable per [US-1 § Independent Test](./spec.md#user-story-1--safety-critical-operator-workflows-drive-real-state-changes-priority-p1).
- **Phase C — Sector workspaces T187..T199 (US-3 / P3)**: 13 sector pages re-using the IC approval card, the cultural-safety subsystem (FR-016 / Q5), the infrastructure-overlay component, and the claims-velocity dashboard. Depends on Phase B for shared affordances. Independently testable per [US-3 § Independent Test](./spec.md#user-story-3--cycle-1-net-new-persona-scenarios-t187t199-pass-against-the-real-ui-priority-p3).
- **Phase D — Recovery environments + Sendai (US-4 / P4)**: `/governance/dashboard/recovery` four-environment view + signed-PDF handover service. Depends on Phase B (signed-PDF panel) + Phase C (utility-insurance-recovery T199 feeds Built+Economic). Independently testable per [US-4 § Independent Test](./spec.md#user-story-4--recovery-environments--economic-loss-surfaces-close-sc-005-priority-p4).
- **Phase E — Cross-cutting horizontals (US-5 / P5)**: sovereignty banner on every regulated route, classifier mask banner (Q6), Foundry carve-out badge, multilingual fallback chain, WCAG 2.2 AA hardening across all P1..P4 surfaces. Depends on Phases A–D. Independently testable per [US-5 § Independent Test](./spec.md#user-story-5--offline-multilingual-sovereignty-and-accessibility-surfacing-across-all-fieldremote-personas-priority-p5).

## Phase 0 → research.md

Research consolidating decisions for the unknown / multi-option technical-context items: see [`research.md`](./research.md) for the full Decision / Rationale / Alternatives-considered records covering the 12 research items derived from the Technical Context unknowns.

## Phase 1 → data-model.md, contracts/, quickstart.md

- Entities + relationships derived from [`spec.md` § Key Entities](./spec.md#key-entities-include-if-feature-involves-data) and the 10 clarifications: see [`data-model.md`](./data-model.md).
- Interface contracts (per spec-035 surface): see [`contracts/`](./contracts/).
- End-to-end run guide for production-reachable mode and dev/test mode: see [`quickstart.md`](./quickstart.md).
- Agent context update: run `pwsh -File .specify/scripts/powershell/update-agent-context.ps1 -AgentType copilot` (executed during Phase 1).

## Constitution Check — Post-Phase-1 re-evaluation

After completing Phase 1 artefacts (research.md, data-model.md, contracts/, quickstart.md, agent context update):

| Constitution clause | Phase-1 surface | Status | Evidence |
|---|---|---|---|
| **NN-1 Data sovereignty** | [`contracts/classifier-gateway.contract.md`](./contracts/classifier-gateway.contract.md), [`contracts/auth-rbac.openapi.yaml`](./contracts/auth-rbac.openapi.yaml) | **PASS** | Classifier-gateway contract enforces PSPF→deny / PII→mask / fail→deny; auth-rbac contract carries no PII to non-AU model endpoints |
| **NN-2 Append-only audit** | [`data-model.md` § AuditTimelineEntry](./data-model.md), [`contracts/auth-rbac.openapi.yaml`](./contracts/auth-rbac.openapi.yaml) | **PASS** | Entity-level immutability policy + paired-row transaction shape per Q9 |
| **NN-3 WCAG 2.2 AA** | [`quickstart.md`](./quickstart.md) § Accessibility verification | **PASS** | `@axe-core/playwright` step before merge |
| **NN-4 Multilingual** | [`contracts/cultural-safety.contract.md`](./contracts/cultural-safety.contract.md) | **PASS** | Language-pack registry + AWS-level-conditional timeout outcomes |
| **NN-5 Offline** | [`contracts/offline-replay.openapi.yaml`](./contracts/offline-replay.openapi.yaml) | **PASS** | 500-entry tiered cap, `/api/offline/replay` dedupe by (persona_id, correlation_id), overflow audit |
| **QG-1 TDD** | Phase A starts with the existing failing `tests/e2e/web-coverage/` suite + new `apps/api/tests/contract/spec_035/` | **PASS** | Both surfaces named in `## Project Structure` |
| **QG-2 Evidence-bound** | All SC-001..SC-012 named in [`quickstart.md`](./quickstart.md) verification matrix | **PASS** | Numeric / artefact-bound thresholds preserved |
| **QG-3 Immutable evidence** | [`contracts/recovery-handover.contract.md`](./contracts/recovery-handover.contract.md) | **PASS** | Signed-PDF only ([Clarifications Q2](./spec.md#clarifications)); blob immutability policy |
| **AVM-first IaC** | `infra/modules/apim-rate-limit.bicep` (NEW, AVM-composed) | **PASS** | No hand-rolled `Microsoft.*` |
| **Human-in-the-loop** | All P1 transitions emit IC approval / paired audit per Q9 | **PASS** | No publish path bypasses approval |

**Post-Phase-1 verdict**: **PASS** — no new constitutional violations introduced. `## Complexity Tracking` remains empty.

## Complexity Tracking

> *Fill ONLY if Constitution Check has violations that must be justified.*

No constitutional violations identified at the initial gate or the post-Phase-1 re-check. Section is empty by design.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| _(none)_ | _(none)_ | _(none)_ |

## Stop & Report

This plan ends at Phase 2 planning per the speckit.plan command contract. Phase 2 (`tasks.md`) is produced by `/speckit.tasks`, not by `/speckit.plan`.

- **Branch**: `035-webapp-capstone-closure`
- **IMPL_PLAN path**: [`specs/035-webapp-capstone-closure/plan.md`](./plan.md)
- **Generated artefacts**:
  - [`specs/035-webapp-capstone-closure/research.md`](./research.md)
  - [`specs/035-webapp-capstone-closure/data-model.md`](./data-model.md)
  - [`specs/035-webapp-capstone-closure/quickstart.md`](./quickstart.md)
  - [`specs/035-webapp-capstone-closure/contracts/production-auth-extension.contract.md`](./contracts/production-auth-extension.contract.md)
  - [`specs/035-webapp-capstone-closure/contracts/offline-replay.openapi.yaml`](./contracts/offline-replay.openapi.yaml)
  - [`specs/035-webapp-capstone-closure/contracts/auth-rbac.openapi.yaml`](./contracts/auth-rbac.openapi.yaml)
  - [`specs/035-webapp-capstone-closure/contracts/rate-limit.policy.md`](./contracts/rate-limit.policy.md)
  - [`specs/035-webapp-capstone-closure/contracts/classifier-gateway.contract.md`](./contracts/classifier-gateway.contract.md)
  - [`specs/035-webapp-capstone-closure/contracts/recovery-handover.contract.md`](./contracts/recovery-handover.contract.md)
  - [`specs/035-webapp-capstone-closure/contracts/cultural-safety.contract.md`](./contracts/cultural-safety.contract.md)
- **Next command**: `/speckit.tasks` to derive `tasks.md` from this plan.
