# Spec 035 Static Implementation Review

## Scope and Evidence Boundary

- Review date: 2026-09-14.
- Expected and observed HEAD: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`, confirmed with read-only Git metadata.
- Scope: only spec 035, Web Application Capstone Closure, including its cited implementation dependencies.
- Sole output: this report. No existing report was present when the directory and working-tree metadata were inspected.
- Other untracked audit reports were left untouched and were not read. No delegation was performed.
- Static source, test-assertion, fixture, configuration, and evidence-artifact inspection only. No product tests, builds,
  verifier scripts, imports, browsers, servers, cloud operations, installs, model execution, or human approvals.
- IMPLEMENTED means supported source or an authored artifact, not a successful execution. Historical checkmarks and
  recorded runs do not prove current deployment, accessibility, timing, or approval outcomes.

**Verdict:** Closure is not supported. Foundational types, routes, components, test sources and infrastructure modules
are authored, but the requested durable, authenticated UI workflows and fresh outcome evidence are incomplete.
There are 82 original tasks (71 `[X]`, 11 `[ ]`, including T024b), 30 FRs, 12 SCs, 24 numbered acceptance scenarios,
15 edge cases, 16 local checklist checkboxes, 68 persona depth profiles and 13 referenced cycle-1 sector scenarios.
The 22 unchecked AUD tasks below are follow-ups, not changes to original completion states.

### Inputs Read

All 20 original files in this specification folder were read completely, including long specification lines re-read
without truncation. No separate local evidence directory, amendment file, formal panel result or prior implementation
review existed. Embedded amendments and brief questions are accounted for later in this report.

| Local input | Role |
| --- | --- |
| [spec.md](spec.md#L1) | All FRs, SCs, stories, scenarios, edges, Q1-Q10, assumptions, scope and inherited contracts |
| [tasks.md](tasks.md#L1) | Every task, suffix, checkbox, success clause, checkpoint and embedded amendment |
| [plan.md](plan.md#L1) | Architecture, phases, dependencies, NFRs and both constitution-check tables |
| [research.md](research.md#L1) | All 12 decisions and alternatives |
| [data-model.md](data-model.md#L1) | All 12 entities, validation and transition rules |
| [quickstart.md](quickstart.md#L1) | Setup/mode instructions, payloads, verification matrix and troubleshooting |
| [00-overall-brief.md](00-overall-brief.md#L1) | No-echo acceptance bar and read-only scope |
| [operational-brief.md](operational-brief.md#L1) | Ten operational personas and unnumbered requirements |
| [sector-eastern-brief.md](sector-eastern-brief.md#L1) | NSW/VIC/QLD hypotheses, acceptance and endorsement requests |
| [sector-southwest-brief.md](sector-southwest-brief.md#L1) | SA/WA/TAS requirements and review questions |
| [sector-tc-brief.md](sector-tc-brief.md#L1) | ACT/NT/Commonwealth/cross-sector requirements and scope proposals |
| [technical-brief.md](technical-brief.md#L1) | All 27 technical questions and requested approval/validation inputs |
| [requirements.md](checklists/requirements.md#L1) | All 16 original checks, notes, clarification history and per-item trace |
| [production-auth-extension.contract.md](contracts/production-auth-extension.contract.md#L1) | Error/success wire contract and precedence |
| [auth-rbac.openapi.yaml](contracts/auth-rbac.openapi.yaml#L1) | Principal and impersonation schema |
| [offline-replay.openapi.yaml](contracts/offline-replay.openapi.yaml#L1) | Replay batch, hash, tier, identity and error rules |
| [rate-limit.policy.md](contracts/rate-limit.policy.md#L1) | Budgets, headers and gateway policy contract |
| [classifier-gateway.contract.md](contracts/classifier-gateway.contract.md#L1) | Five classifier branches, masks and audit requirements |
| [recovery-handover.contract.md](contracts/recovery-handover.contract.md#L1) | PDF, signing, claims freshness, hash, SAS and immutability |
| [cultural-safety.contract.md](contracts/cultural-safety.contract.md#L1) | Elder routing, timeouts, IC gate and language policy |

Required review guidance: [audit README](../001-spec-implementation-audit/README.md#L1) only lines 1-59,
[code-review.instructions.md](../../.github/instructions/code-review.instructions.md#L1),
[code-commenting.instructions.md](../../.github/instructions/code-commenting.instructions.md#L1),
[bicep-code-best-practices.instructions.md](../../.github/instructions/bicep-code-best-practices.instructions.md#L1),
[bicep-policy-compliance.instructions.md](../../.github/instructions/bicep-policy-compliance.instructions.md#L1),
and the Python fact-grounded-coding skill, used strictly at its source-evidence level. Repository memory supplied only
general suffix/state/link-validation cautions, not findings from another specification review.

Associated sources inspected include the parent evaluator contract, all 68 depth-profile texts and their schema, all
13 authored sector pages, canonical workspace routing, shared components/clients, API routing/middleware/services/stores,
all 10 spec-035 API contract test files and 3 unit files, all 5 spec-035 web unit files, bridge tests, suite fixtures,
discovery, relevant cross-cutting assertions, generated-test text inventory, reporter and stored artifacts; all four
hardening modules and their main-template/parameter wiring; workflows, branch-protection description, changelog,
architecture document, relocated ADR-033 and constitution v1.2.0. Exact anchors appear throughout the matrices.

### Priority Summary

Details retain stable AUD IDs; this summary orders findings by impact. No production incident or test result is inferred.

| Priority | Concrete finding and controlling anchor | Follow-up |
| --- | --- | --- |
| P1 security | Fixture-principal bypass and unresolved/impersonated persona allow path: [entra_auth.py](../../apps/api/app/middleware/entra_auth.py#L162) | AUD-035-002 |
| P1 security | Unknown-region/missing-gateway model egress passes original content: [foundry_chat_client.py](../../apps/agents/common/foundry_chat_client.py#L373) | AUD-035-015 |
| P1 integrity | Audit reader and writer use separate stores; post-response writes can fail silently: [audit_appender.py](../../apps/api/app/middleware/audit_appender.py#L148) | AUD-035-003 |
| P1 integrity | Worker does not queue; drain deletes before ack; replay writes audit only: [offline-sw.js](../../apps/web/public/offline-sw.js#L8) | AUD-035-004 |
| P1 integrity | PDF/signature/storage are production-default stubs: [recovery_handover_service.py](../../apps/api/app/services/recovery_handover_service.py#L115) | AUD-035-007 |
| P1 auth | Browser bearer helper has no source callers: [entra-msal.ts](../../apps/web/src/lib/auth/entra-msal.ts#L76) | AUD-035-014 |
| P1 security | Mutex checks unrelated activation flags: [activation_mutex.py](../../apps/api/app/middleware/activation_mutex.py#L71) | AUD-035-018 |
| P1 compatibility | Routability is checked after auth/schema, not before: [outcome_evaluator_service.py](../../apps/api/app/services/outcome_evaluator_service.py#L194) | AUD-035-022 |
| P1 readiness | APIM rejection handling is after the handler and budgets use untrusted keys: [rate_limit_audit.py](../../apps/api/app/middleware/rate_limit_audit.py#L37) | AUD-035-017 |
| P1 readiness | Hardening defaults off; signing identity is empty: [main.bicep](../../infra/main.bicep#L182) | AUD-035-019 |
| P1 workflow | Approval body violates canonical evaluator and fallback only echoes audit: [ic-approval-card.tsx](../../apps/web/src/app/workspaces/[personaId]/_panels/ic-approval-card.tsx#L52) | AUD-035-001 |
| P1 workflow | PIO approval callback unbound; no publication: [pio-aws-composer.tsx](../../apps/web/src/app/workspaces/[personaId]/_panels/pio-aws-composer.tsx#L113) | AUD-035-005 |
| P1 workflow | Elder service disconnected and Q5 contradictory: [cultural_safety_service.py](../../apps/api/app/services/cultural_safety_service.py#L105) | AUD-035-006 |
| P1 workflow | Canonical sector personas do not receive depth actions: [persona_workspace_service.py](../../apps/api/app/services/persona_workspace_service.py#L14) | AUD-035-012 |
| P1 evidence | Canned evaluator tests and stale empty/skipped artifacts cannot prove closure: [cycle-metadata.json](../../tests/e2e/web-coverage/_artifacts/cycle-metadata.json#L1) | AUD-035-021 |
| P2 workflow | Risk view has no route comparison or recommendation command: [risk-matrix.tsx](../../apps/web/src/app/workspaces/[personaId]/_panels/risk-matrix.tsx#L54) | AUD-035-008 |
| P2 workflow | IAP is read-only bridge output: [planning-iap-composer.tsx](../../apps/web/src/app/workspaces/[personaId]/_panels/planning-iap-composer.tsx#L34) | AUD-035-009 |
| P2 workflow | Span check receives empty reports and does not control save: [persona-workspace.tsx](../../apps/web/src/components/workspaces/persona-workspace.tsx#L84) | AUD-035-010 |
| P2 workflow | Observer receives no rows and cannot export/read back: [observer-auditor-timeline.tsx](../../apps/web/src/app/workspaces/[personaId]/_panels/observer-auditor-timeline.tsx#L32) | AUD-035-011 |
| P2 workflow | Recovery subdomains are labels over absent reads/zero claims: [page.tsx](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L76) | AUD-035-013 |
| P2 compliance | No global registry/provenance UI; checked-in reviews are overdue: [foundry_carveout_registry.json](../../data/governance/foundry_carveout_registry.json#L1) | AUD-035-016 |
| P2 contracts | Local policies, quickstart, diagram, checklist and closure claims disagree: [quickstart.md](quickstart.md#L202) | AUD-035-020 |

## Findings and Remediation

### Approval UI Does Not Implement the Evaluator Contract or an Action Transition

- [ ] AUD-035-001 Implement a persisted, authorised approval workflow from the canonical workspace

**Priority:** P1. **Original obligations:** FR-001; US1 acceptance 1; T036; dependent T037, T039, T042 and sector approvals.

**Expected:** An authorised operator supplies rationale, source references, a low/medium/high confidence value, and an
approver identity; approval changes a durable action, supports stale-state conflict handling, and exposes the new state
and associated audit row without reloading.

**Observed:** The mounted workspace supplies an empty source list and fixed rationale/confidence to the card
([persona-workspace.tsx](../../apps/web/src/components/workspaces/persona-workspace.tsx#L64)). The submit handler posts
`rationale`, `sources`, `confidence`, and `approver_identity` to a URL derived from the task ID
([ic-approval-card.tsx](../../apps/web/src/app/workspaces/[personaId]/_panels/ic-approval-card.tsx#L52)). The actual evaluator
request requires `scenario_id`, `persona_id`, `correlation_id`, and `metric_inputs`, with extra fields forbidden
([outcome_evaluator.py](../../apps/api/app/api/routes/outcome_evaluator.py#L39)). The button is disabled only while
submitting, not when required evidence is empty
([ic-approval-card.tsx](../../apps/web/src/app/workspaces/[personaId]/_panels/ic-approval-card.tsx#L148)).

**Impact:** The mounted approval path cannot satisfy the request schema, and an evaluator call is not itself evidence of
an approved operational action. A displayed panel or audit lookup cannot establish FR-001 closure.

**Relocated behaviour checked:** With both feature gates disabled, the explicit workspace bridge accepts this body and
returns `rows`, but writes only an in-memory ring buffer
([workspace_bridges.py](../../apps/api/app/api/routes/workspace_bridges.py#L69)). Its registration is selected by flags,
not an environment restriction ([router.py](../../apps/api/app/api/router.py#L184)). The canonical audit reader instead
returns `items`. This fallback is not missing, and it is not an explicit supersession of durable approval or the locked
evaluator contract. Existing bridge tests establish that alternate round-trip only
([test_workspace_bridges.py](../../tests/contract/test_workspace_bridges.py#L198)).

**Developer instructions:** Bind the card to a real action and scenario, capture and validate the required approval
inputs, invoke the owning authorised action-transition service, and refresh durable state. Keep evaluator grading
separate and preserve its locked request/response contract. Resolve the request identity from the authenticated
principal, not caller-entered identity; retain first-write-wins conflict handling and correlated append-only evidence.
Include operations/logistics function-lead workspaces required by FR-001. Do not change the spec-034 assertions to
accommodate this malformed request.

**Tester instructions:** Extend existing
[operator-panels.test.tsx](../../apps/web/tests/unit/spec_035/operator-panels.test.tsx#L14),
[test_workspace_bridges.py](../../tests/contract/test_workspace_bridges.py#L198), and
[test_production_reach.py](../../apps/api/tests/contract/spec_035/test_production_reach.py#L41).
Cover a valid approval, each empty field, unauthorised role, stale concurrent approval, refetch without
reload, evaluator-body conformance, and correlated audit read-back. Assert the persisted action state, not just a 200
response or the existence of a card. Include both guarded and bridge-selected modes, task IDs that are not SC IDs,
operations/logistics leads, and audit `items` parsing.

**Future validation:** Prepared isolated action/audit stores, canonical persona/JWKS fixtures and Node/Python test
environments; run `pnpm -C apps/web exec vitest run tests/unit/spec_035/operator-panels.test.tsx` and
`uv run pytest tests/contract/test_workspace_bridges.py apps/api/tests/contract/spec_035/test_production_reach.py -q`.
Expected: required input/role checks, actual durable approval, conflict handling and read-back all pass without an
evaluator-only false success. Later UI runs require the reviewed target configuration from AUD-035-021.

**Completion:** The canonical navigable workspace drives the authorised durable transition and the unchanged evaluator
accepts a separately valid request; all positive, negative, and conflict assertions are supported by current evidence.

### Production Authentication and Persona Authorisation Fail Open

- [ ] AUD-035-002 Enforce verified single-role identity and fail-closed persona scoping

**Priority:** P1 security. **Original obligations:** FR-010, FR-011, FR-013; Q1, Q9; US2 acceptance 3 and 6;
T007, T017, T020, T023, T024, T024b, T027, T028, T029, T046.

**Expected:** Only a validated Entra bearer with exactly one permitted role and a resolvable scoped persona reaches a
production handler. Impersonation inherits the target's route authorisation and never substitutes an unauthenticated
test identity.

**Observed:** The request resolver accepts `AMA_ENTRA_TEST_PRINCIPAL` before checking any bearer, without a dev/test
condition ([entra_auth.py](../../apps/api/app/middleware/entra_auth.py#L162)). RBAC selects the first role, permits a
missing persona lookup result, and returns immediately for an admin without validating the impersonated persona's
function ([rbac_check.py](../../apps/api/app/middleware/rbac_check.py#L65),
[rbac_check.py](../../apps/api/app/middleware/rbac_check.py#L125)). Missing persona claims produce 403 rather than FR-010's
401. The test helper deliberately supplies this bypass and builds a minimal application with synthetic endpoints
([_helpers.py](../../apps/api/tests/contract/spec_035/_helpers.py#L46)); that is not production authentication evidence.

**Impact:** Misconfiguration can bypass bearer validation; unresolved or mismatched identities and admin impersonations
are not bounded by the required persona-to-function rule. The actual deployed configuration remains UNVERIFIED.

**Developer instructions:** Restrict any fixture identity to the explicit dev/test dual guard and refuse production
startup with that escape hatch configured. Require issuer, audience, expiry, identity, exactly one closed-set AppRole,
and the applicable persona claim. Resolve all 68 canonical personas from the real registry; deny unknown lookups.
Validate an impersonated target and apply its route-family permissions. Bind handler persona fields to that resolved
principal. Preserve the locked evaluator success body and Q10 error precedence; align the legacy auth middleware so it
cannot overwrite the resolved principal. Do not add roles or sticky impersonation sessions.

**Tester instructions:** Extend existing
[_helpers.py](../../apps/api/tests/contract/spec_035/_helpers.py#L46),
[test_whoami.py](../../apps/api/tests/contract/spec_035/test_whoami.py#L1), and
[test_impersonation_pairing.py](../../apps/api/tests/contract/spec_035/test_impersonation_pairing.py#L1).
Use the real app factory and isolated signed-JWT/JWKS fixtures, not the environment bypass as proof. Cover valid scope,
no/expired/wrong-issuer/wrong-audience bearer, missing/multiple roles, unknown persona, wrong function, admin direct,
valid/unknown/disallowed impersonation, non-admin header spoofing, and consecutive requests without sticky state.
Assert HTTP/envelope, zero handler calls on denial, effective principal, and authoritative audit rows.

**Future validation:** With an already prepared Python environment and isolated persistence, run
`uv run pytest apps/api/tests/contract/spec_035/test_whoami.py apps/api/tests/contract/spec_035/test_impersonation_pairing.py -q`.
Expected: every branch above passes without external identity or cloud access. Later staging bearer checks require
separately authorised credentials and infrastructure and are not substitutes for the negative fixtures.

**Completion:** Production cannot select a test principal; all canonical identity mappings and target-route checks are
enforced, with exact Q10 errors and no denied action executed.

### Audit Writers and Readers Do Not Share the Required Durable Timeline

- [ ] AUD-035-003 Unify durable audit read-back, atomic impersonation, and idempotent emission

**Priority:** P1 integrity. **Original obligations:** FR-003, FR-009, FR-011, FR-013; Q8, Q9, Q10; SC-009;
US1 acceptance 4; US2 acceptance 1, 2, 3, 4; T014, T015, T016, T020, T028, T038, T078.

**Expected:** Allowed, denied, rate-limited, schema-rejected, and audit-list calls are observable in one append-only
timeline, with exact returned audit IDs, durable idempotency, atomic admin/action pairs, and a measurable two-second SLO.

**Observed:** The audit route delegates to the evaluator's local ledger
([audit_list.py](../../apps/api/app/api/routes/audit_list.py#L58),
[outcome_evaluator_service.py](../../apps/api/app/services/outcome_evaluator_service.py#L38)). Middleware uses a different
`AuditRepository`, excludes GET requests, sends the response before `_emit`, and swallows write failures
([audit_appender.py](../../apps/api/app/middleware/audit_appender.py#L90),
[audit_appender.py](../../apps/api/app/middleware/audit_appender.py#L148)). It trusts the raw impersonation header for
paired emission even if authorisation rejected it
([audit_appender.py](../../apps/api/app/middleware/audit_appender.py#L198)). The repository permits process-local fallback
on missing/failed Cosmos initialisation and sequential writes when transactional batch is unavailable
([audit_repository.py](../../apps/api/app/repositories/audit_repository.py#L57),
[audit_repository.py](../../apps/api/app/repositories/audit_repository.py#L129)). Repeating an evaluator request reuses its
ledger result but still traverses the independent middleware writer.

**Impact:** Read-back cannot establish the production call history, denials or paired rows; a success can be returned
without durable evidence. Restart/scale-out loses ledger/idempotency state, and a spoofed header can produce misleading
admin-override attribution. No live data loss or SLO measurement was performed or inferred.

**Developer instructions:** Route all relevant writers and readers through the same AU-region append-only store with
an explicit immutable schema and partition strategy. Allocate the response audit ID once, persist the exact error
envelope under that ID, and propagate correlation consistently. Require durable storage in production and atomic paired
writes; fail closed on unsupported batch or write failure. Emit admin pairs only from validated impersonation context,
including canonical `roles` claims, and audit GET calls without recursive read-back. Define retry/idempotency semantics
that preserve the original tuple contract without generating duplicate normal action rows. Keep cursor/cycle/max-500
behaviour compatible and measure the SLO independently of response sending.

**Tester instructions:** Extend existing
[test_audit_repository.py](../../apps/api/tests/unit/spec_035/test_audit_repository.py#L1),
[test_audit_appender.py](../../apps/api/tests/unit/spec_035/test_audit_appender.py#L1), and
[test_impersonation_pairing.py](../../apps/api/tests/contract/spec_035/test_impersonation_pairing.py#L1).
Use one isolated backing-store fixture shared by the real app and reader. Assert allowed/denied GET and POST read-back,
exact returned IDs/envelopes, one normal effect on retry, paired all-or-nothing failure, non-admin spoof rejection,
restart/second-worker visibility, immutable original bytes, cycle filtering, and pagination across 501 records.

**Future validation:** With the isolated store fixture available, run
`uv run pytest apps/api/tests/unit/spec_035/test_audit_repository.py apps/api/tests/unit/spec_035/test_audit_appender.py apps/api/tests/contract/spec_035/test_impersonation_pairing.py -q`.
Expected: no fallback or half-pair is accepted; production-shaped read-back returns the same IDs and outcomes. Staging
latency and retention/permission verification require later authorised integration work.

**Completion:** A correlated read returns the authoritative immutable records for every required request, retries and
restarts preserve identity, denied callers cannot invent admin attribution, and atomicity is never downgraded.

### Offline Capture and Replay Can Lose Actions Without Executing Them

- [ ] AUD-035-004 Implement acknowledged persona-isolated offline capture and replay

**Priority:** P1 data integrity. **Original obligations:** FR-006, FR-015, FR-019; Q4, Q7; SC-007;
US1 acceptance 3; US5 acceptance 5; T022, T030, T031, T034, T040, T041, T055, T059, T072.

**Expected:** GPS actions survive disconnection and reload, remain isolated per persona, replay life-safety first through
the dedicated authorised endpoint, and are removed only after durable acknowledgement. Offline windows, original
identity/time, overflow/displacement, and queue position remain auditable.

**Observed:** The registered worker does not intercept any fetch
([offline-sw.js](../../apps/web/public/offline-sw.js#L8)). The store counts all personas together, deletes displaced
entries without a persisted side buffer, and deletes each drained entry before acknowledgement
([queue-store.ts](../../apps/web/src/lib/offline/queue-store.ts#L182),
[queue-store.ts](../../apps/web/src/lib/offline/queue-store.ts#L222)). The field panel has no GPS capture or heartbeat;
manual replay POSTs to original routes rather than `/api/offline/replay`, counts failures without restoring entries,
and hides its banner solely on browser connectivity
([field-coordinator-offline.tsx](../../apps/web/src/app/workspaces/[personaId]/_panels/field-coordinator-offline.tsx#L90)).
The API uses a process-local dedupe dictionary, trusts `X-Persona-Id` ahead of claims, ignores the queued action payload,
and appends a fixed approved row instead of executing the original operation
([offline_replay.py](../../apps/api/app/api/routes/offline_replay.py#L77),
[offline_replay.py](../../apps/api/app/api/routes/offline_replay.py#L145)). The declared service was relocated into this
route; its absence as a separate file is not the finding. The max-50 Pydantic validator rejects before the later 413
branch, while the test permits either 413 or 422
([test_offline_replay.py](../../apps/api/tests/contract/spec_035/test_offline_replay.py#L138)).

**Impact:** Offline actions may never be queued, may be lost after a failed replay, or may be reported replayed without
their domain effect. One persona can consume another's quota; restart/multi-worker dedupe and overflow ceilings are not
provided by this path. Timing and browser persistence outcomes remain UNVERIFIED.

**Developer instructions:** Connect native SW interception and GPS capture to a shared durable queue, with per-persona
transactional admission/dedupe, authenticated original operator metadata, encrypted payloads without plaintext fallback,
and persisted displacement/overflow envelopes. Use a lease/ack protocol, retaining failures until explicit resolution.
Batch homogeneous `life_safety` and routine entries through the dedicated endpoint with refreshed auth; validate hashes,
route/method allowlists, 50-batch and 500-persona limits, and replay-window exemptions. Dispatch via the original domain
services with durable dedupe and atomic audit, not arbitrary HTTP forwarding. Reconcile the all-life-safety-at-cap
contract conflict explicitly. Keep the banner until heartbeat recovery AND queue acknowledgement; show reserved count,
80% warning, retries, and original timestamp/identity across remote jurisdictions. Depends on AUD-035-002/003.

**Tester instructions:** Extend
[offline-queue-store.test.ts](../../apps/web/tests/unit/spec_035/offline-queue-store.test.ts#L56) and
[test_offline_replay.py](../../apps/api/tests/contract/spec_035/test_offline_replay.py#L67).
Fixtures: two personas, cap override 10, 500 mixed-tier entries, 501st routine, all-life-safety cap, equal timestamps,
duplicate IDs, a 30-minute offline window, wrong payload hash, malformed route, denied identity, 50/51-entry batches,
partial 429/500/network failure, restart and concurrent replay. Assert retained failures, bounded per-persona depth,
durable side-buffer audit, actual action effects exactly once, preserved metadata, tier order, and banner lifecycle.
Add browser-level assertions in the existing cross-cutting offline home after its authorised validation phase.

**Future validation:** With the already provisioned local test environment, run
`pnpm -C apps/web exec vitest run tests/unit/spec_035/offline-queue-store.test.ts` and
`uv run pytest apps/api/tests/contract/spec_035/test_offline_replay.py -q` after discovery defects are repaired.
Later authenticated browser runs must measure 50-entry life-safety/routine drains within 30 seconds and a 500-entry
drain within five minutes. No browser or product test was run here.

**Completion:** Every captured action remains recoverable until acknowledged, has exactly one durable domain effect,
and passes identity, tier, cap, failure, restart, and audit assertions before any SC-007 timing claim is accepted.

### Warning Composition Stops Before Approval and Publication

- [ ] AUD-035-005 Connect multilingual warning drafts to IC approval and public publication

**Priority:** P1. **Original obligations:** FR-002, FR-020, FR-029; SC-005; US1 acceptance 2; US3 acceptance 4;
US5 acceptance 4; T037, T046, T059, T073; operational PIO brief.

**Expected:** A persisted AWS draft with canonical level values and real community-language content passes accessibility
and explicit IC approval before publication, then appears on the affected jurisdiction's public-warning surface.

**Observed:** The composer stores variants only in React state, sends display-form levels, defaults to English only,
and invokes an optional approval callback without a mounted implementation
([pio-aws-composer.tsx](../../apps/web/src/app/workspaces/[personaId]/_panels/pio-aws-composer.tsx#L45),
[pio-aws-composer.tsx](../../apps/web/src/app/workspaces/[personaId]/_panels/pio-aws-composer.tsx#L113),
[persona-workspace.tsx](../../apps/web/src/components/workspaces/persona-workspace.tsx#L74)). The reachable bridge
returns English carrier text with language labels, not translations or persisted warning records
([agents.py](../../apps/api/app/api/routes/agents.py#L181)). The inline scan loads a bare browser module dynamically,
uses only WCAG 2.0 tags, labels the result 2.1, and does not gate approval. There is no publish operation in this composer.

**Impact:** A language label or preview cannot prove multilingual reach, IC approval, or the two-minute warning outcome.
The existing warning-chain services must be reused where suitable, but their existence does not connect this composer.

**Developer instructions:** Bind draft/edit/submit/approve/publish to a versioned warning entity and the existing warning
and communication services. Use snake_case machine levels; reject missing hazard/location/action and require a reviewed
community variant plus English fallback. Wire IC identity/approval server-side, make unauthorised and pre-approval
publication impossible, and publish/read back the same immutable warning ID on the public route. Persist language-pack
source, approval, variant evidence and timestamps in the shared audit store. Bundle the actual supported accessibility
scan and block the defined failures. Treat unreviewed translations as unavailable, never as completed translated text.
Reuse one composer across canonical sector PIOs and broadcast consumers. Depends on AUD-035-001/002/003/006.

**Tester instructions:** Extend
[operator-panels.test.tsx](../../apps/web/tests/unit/spec_035/operator-panels.test.tsx#L1) and the existing unchanged
AWS-warning cross-cutting assertions when future authorised execution is available. Use English/Chinese/reviewed ATSI,
missing/declined translation, empty inputs, all three levels, PIO versus IC tokens, stale approval, failed accessibility,
post-approval edit, and repeat publish fixtures. Assert persisted draft/approval/publication state, no request for a
forbidden UI action, server rejection of direct bypass, public read-back, `lang`/fallback labels, and evidence timestamps.

**Future validation:** After fixing test discovery, run
`pnpm -C apps/web exec vitest run tests/unit/spec_035/operator-panels.test.tsx`; later run the existing
`aws-warning-compliance.spec.ts` through the repository's web-coverage configuration with isolated seeded scenarios and
real fixture persona authentication. Expected: real post-transition assertions, no bailouts, and separately measured
approval-to-community-render latency at most two minutes.

**Completion:** The canonical PIO and sector journeys produce approved, translated, publicly readable warnings with
durable correlated evidence. Scan, timing, and community/human review outcomes require later evidence.

### Elder Routing Is Disconnected and Timeout Policy Contradicts Q5

- [ ] AUD-035-006 Resolve the cultural-safety contract and wire durable elder approval

**Priority:** P1. **Original obligations:** FR-016, FR-029; Q5; US3 acceptance 2; US5 acceptance 4;
T011, T049, T050, T053, T056, T059, T073.

**Expected:** A real elder/community request with a configurable 90-second window yields approved, declined or held
state; the Q5 Watch and Act/Emergency override requires an IC, publishes only English and Chinese, suppresses ATSI,
notifies the community contact, and audits every identity and variant decision.

**Observed:** The service's optional elder hook returns without routing when unset; timeout is a caller-invoked pure
decision, not a scheduled persisted transition
([cultural_safety_service.py](../../apps/api/app/services/cultural_safety_service.py#L105)). Only Emergency Warning is
override-eligible; the Watch and Act test positively asserts rejection
([cultural_safety_service.py](../../apps/api/app/services/cultural_safety_service.py#L55),
[test_cultural_safety.py](../../apps/api/tests/contract/spec_035/test_cultural_safety.py#L67)). The component's elder and
override controls are optional callbacks
([index.tsx](../../apps/web/src/components/cultural-safety/index.tsx#L122)). Q5/T049 conflict with the lower-level
contract ([cultural-safety.contract.md](contracts/cultural-safety.contract.md#L17)), research R-010, data model, T011,
and quickstart. No explicit amendment resolves that conflict.

**Impact:** Rendering a pending badge or returning an audit-shaped dictionary does not route to an elder, record
consent, suppress publication, or implement the specified life-safety exception.

**Developer instructions:** Obtain an explicit recorded policy decision; do not infer supersession from the existing
code/test. Then align the contract, configuration, server and UI. Connect authenticated elder routing and acknowledgement
to the persisted warning, durable deadlines, IC confirmation, variant suppression, English/Chinese publication and
out-of-band notification. Persist decisions through AUD-035-003 rather than returning an unconsumed dictionary. Bind
language source, fallback, missing-pack badge and reviewer identity in the shared registry; fail closed on missing elder
or infrastructure. Preserve the 68-persona inventory and no new identity provider.

**Tester instructions:** Extend
[test_cultural_safety.py](../../apps/api/tests/contract/spec_035/test_cultural_safety.py#L34),
[language-packs.test.ts](../../apps/web/tests/unit/spec_035/language-packs.test.ts#L1), and
[us3-components.test.tsx](../../apps/web/tests/unit/spec_035/us3-components.test.tsx#L1).
Use a fake clock and queue adapter for approve, decline, no elder, 89/90/91 seconds, IC absent/present/wrong-role,
repeated/late acknowledgement, unavailable pack, expired approval and each AWS level in WA/TAS/NT. Assert actual queue
enqueue, saved state, notification, published/suppressed variants, fallback visibility, and exact audited identities.

**Future validation:** After the policy decision and isolated adapters, run
`uv run pytest apps/api/tests/contract/spec_035/test_cultural_safety.py -q` and
`pnpm -C apps/web exec vitest run tests/unit/spec_035/language-packs.test.ts tests/unit/spec_035/us3-components.test.tsx`.
Expected: both eligible override levels follow the agreed policy; no unapproved variant is published. Human/community
review is a separate later gate, never inferred from a boolean fixture.

**Completion:** One consistent policy drives persisted routing, approval, timeout, override, language rendering and
audit, with explicit source decisions and negative publication tests.

### Recovery Export Is Neither a Valid Signed PDF nor an Immutable Download

- [ ] AUD-035-007 Replace recovery signing stubs and align the download contract

**Priority:** P1 evidence integrity. **Original obligations:** FR-007, FR-022, FR-023; Q2; SC-008;
US3 acceptance 5; US4 acceptance 2; signing-TTL edge; T010, T012, T044, T045, T060, T065, T066.

**Expected:** A single readable signed PDF contains the actual handover content, is signed using a valid managed-identity
Key Vault certificate, remains immutable and re-fetchable, and has a hash of the downloaded bytes and a real audit ID.

**Observed:** The renderer emits PDF-like comments containing hashes instead of document content; signing is a literal
`PKCS7-DETACHED` marker and storage is an in-memory dictionary returning an `.invalid` host
([recovery_handover_service.py](../../apps/api/app/services/recovery_handover_service.py#L115),
[recovery_handover_service.py](../../apps/api/app/services/recovery_handover_service.py#L146),
[recovery_handover_service.py](../../apps/api/app/services/recovery_handover_service.py#L162)). The hash is computed before
signature bytes are appended, unknown claims snapshots are invented as fresh, and audit is optional
([recovery_handover_service.py](../../apps/api/app/services/recovery_handover_service.py#L98),
[recovery_handover_service.py](../../apps/api/app/services/recovery_handover_service.py#L209)). The route constructs these
defaults when no service is injected ([recovery_handover.py](../../apps/api/app/api/routes/recovery_handover.py#L29)).
The mounted workspace supplies only `scenario_id`; the API requires a complete handover. The panel expects `pdf_url`,
`sas_expiry`, `signed_at` instead of the server's `blob_uri`, `sas_url_expires_at`, and artefact fields
([resilience-handover-pdf.tsx](../../apps/web/src/app/workspaces/[personaId]/_panels/resilience-handover-pdf.tsx#L14)).
Its expired-key branch requires detail which the common envelope helper drops. The hash test recomputes `_render_pdf`
without fetching stored bytes ([test_recovery_handover.py](../../apps/api/tests/contract/spec_035/test_recovery_handover.py#L64)).

**Impact:** A successful response can falsely represent a signed, downloadable evidence artifact; the UI cannot consume
that response, and neither snapshot freshness nor signature/retention assertions establish the required controls.

**Developer instructions:** Inject real PDF rendering, signing, claims lookup, immutable blob and audit adapters in the
production app; reject missing adapters instead of selecting stubs. Validate populated four-environment content, true
snapshot existence/24-hour freshness, finite losses and Sendai boundary. Produce a standards-valid signed PDF, hash the
exact canonical stored/downloaded bytes, issue a bounded 15-minute SAS with authenticated reissue, and persist export
time/identity/reference. Read certificate expiry and fail before signing; reconcile `signing_key_expired` with the
closed error envelope explicitly and surface rotation ETA/runbook without fallback signing. Align panel request and
response fields. Retain PDF-only scope and AU-region/AVM requirements; depends on AUD-035-002/003 and infrastructure.

**Tester instructions:** Extend
[test_recovery_handover.py](../../apps/api/tests/contract/spec_035/test_recovery_handover.py#L54) and
[operator-panels.test.tsx](../../apps/web/tests/unit/spec_035/operator-panels.test.tsx#L1).
Fixtures: valid/expired cert, absent signer, missing/23h/24h/25h claims snapshot, four populated versus empty/missing
environments, loss zero/negative/nonfinite, ratio .29/.30, repeat export, failed upload/audit and expired SAS. Parse the
PDF with an independent reader, verify cryptographic signature with the public certificate, compare fetched-byte hash,
assert content/identity/immutable first artifact, and drive download/error/runbook through the real panel contract.

**Future validation:** With isolated cryptographic/blob adapters and repaired discovery, run
`uv run pytest apps/api/tests/contract/spec_035/test_recovery_handover.py -q` and the operator-panel Vitest command.
Expected: invalid/missing signer never yields an artifact; every success is a verifiable PDF and working download.
Live Key Vault, retention, SAS timing and deployment checks remain later authorised work.

**Completion:** No production stub path exists; the downloadable PDF, signature, content, hash, expiry behaviour and
immutable audit reference are independently verified, with no JSON sidecar.

### Risk Recommendations Are Static and Cannot Reach Command Queues

- [ ] AUD-035-008 Connect live route-risk comparisons to authorised evacuation recommendations

**Priority:** P2. **Original obligations:** FR-004; US1 narrative; operational Risk Manager brief; T039; SC-006.
**Expected/observed/impact:** FR-004 needs at least two live route alternatives and a recommendation appearing in both
IC and Planning queues. The panel performs one fetch per scenario and renders a single matrix cell and text controls
([risk-matrix.tsx](../../apps/web/src/app/workspaces/[personaId]/_panels/risk-matrix.tsx#L54)); its bridge selects a fixed
profile from scenario-ID keywords ([agents.py](../../apps/api/app/api/routes/agents.py#L40)). No route selection or
recommendation action is exposed. A scenario-name match cannot prove live risk or decision-to-action improvement.

**Developer instructions:** Bind actual scenario observations and provenance to the existing risk/recommendation
services; display and refresh multiple route risks, expose an authorised recommend-evacuation command, and persist the
recommendation and destination IC/Planning task IDs. Audit comparison changes and handoff. Keep AI advisory, retain
manual fallback, and do not treat a deterministic bridge as a live agent result. Depends on AUD-035-001/002/003/014/015.

**Tester instructions:** Extend
[operator-panels.test.tsx](../../apps/web/tests/unit/spec_035/operator-panels.test.tsx#L67) and inspect the existing
[risk-manager.predictive-evac-lead.spec.ts](../../tests/e2e/web-coverage/operational/risk-manager.predictive-evac-lead.spec.ts#L1)
as the read-only acceptance home. Fixtures: two conflicting route risks, changing evidence, missing provenance, no safe
route, denied role, duplicate recommendation and unavailable agent. Assert ordered comparisons, refresh without reload,
correct IC/Planning queue entries, no irreversible autonomous action, and correlated evidence.
**Future validation:** Prepared local API/agent fakes and repaired panel fixtures; run the operator-panel Vitest command
and later `pnpm -C apps/web test:web-coverage -- operational/risk-manager.predictive-evac-lead.spec.ts` using a reviewed
target configuration. Expect durable handoff, negative controls and independently measured latency.
**Completion:** Live observations drive route comparison and one authorised, observable command-queue recommendation.

### Planning Does Not Support Editing, Provenance or IC Handoff

- [ ] AUD-035-009 Implement editable provenance-bound forecasts and IAP handoff

**Priority:** P2. **Original obligations:** FR-005; US1 narrative; operational Planning brief; T042; SC-006.
**Expected/observed/impact:** The panel offers only a draft-fetch button and read-only forecast/list/preformatted text
([planning-iap-composer.tsx](../../apps/web/src/app/workspaces/[personaId]/_panels/planning-iap-composer.tsx#L34)). The
bridge derives forecasts and IAP text from scenario keywords ([agents.py](../../apps/api/app/api/routes/agents.py#L223)).
It does not support source-level edits, contradictions, section provenance or a destination IC. The displayed draft
therefore does not satisfy a persisted planning workflow.

**Developer instructions:** Reuse the planning and task services to load real forecast sources, edit/version the IAP,
flag source contradictions, preserve evidence/correlation provenance per section, and submit to the resolved IC queue.
Validate scope and stale edits server-side; publish no warning or irreversible action from an advisory draft. Preserve
existing schema consumers and scenario identity; depends on AUD-035-002/003/014.
**Tester instructions:** Extend
[operator-panels.test.tsx](../../apps/web/tests/unit/spec_035/operator-panels.test.tsx#L67) and the existing
[planning-officer.predictive-risk-evac.spec.ts](../../tests/e2e/web-coverage/operational/planning-officer.predictive-risk-evac.spec.ts#L1)
acceptance home. Use agreeing/conflicting/absent/stale source fixtures, an edited section, missing IC, denied role and
concurrent update. Assert editable values, contradiction badges, every section's provenance, persisted version and the
exact destination identity/audit row after handoff; no silent fallback to invented forecast facts.
**Future validation:** Prepared deterministic planning fixtures; run operator-panel Vitest, then the named operational
file via `pnpm -C apps/web test:web-coverage -- operational/planning-officer.predictive-risk-evac.spec.ts` after target
configuration repair. Expected: data-bound editing and audited IC receipt without reload.
**Completion:** An edited, source-attributed IAP persists and appears in the correct IC queue with its audit chain.

### Span-of-Control Is Not Connected to the Organisation State or Save Boundary

- [ ] AUD-035-010 Enforce command-tier span-of-control before saving a direct report

**Priority:** P2. **Original obligations:** FR-008; US1 acceptance 5; sector span edge; T043; operational IC brief.
**Expected/observed/impact:** The component's greater-than-seven condition exists, but the workspace always passes an
empty list ([persona-workspace.tsx](../../apps/web/src/components/workspaces/persona-workspace.tsx#L84)). The component
suppresses only Planning Officer and describes a blocked save without controlling one; delegation is optional
([span-of-control-warning.tsx](../../apps/web/src/app/workspaces/[personaId]/_panels/span-of-control-warning.tsx#L23)).
The isolated nine-report rendering test does not establish a warning on adding the eighth real direct report.

**Developer instructions:** Bind current organisation/incident reports and proposed additions to the existing AIIMS
assignment boundary. Apply the explicit command-tier allowlist, show the guidance and delegation options before save,
persist authorised delegation, and audit the breach. Suppress for every Tier-N/A role, not merely Planning Officer.
Preserve jurisdiction/tenant scope and first-write-wins updates; depends on identity/audit fixes.
**Tester instructions:** Extend
[operator-panels.test.tsx](../../apps/web/tests/unit/spec_035/operator-panels.test.tsx#L46) and the existing
[span-of-control.spec.ts](../../tests/e2e/web-coverage/cross-cutting/span-of-control.spec.ts#L1).
Fixtures: six/seven/eight reports, IC and sector command tiers, Planning and other Tier-N/A roles, stale add, denied
delegate, successful delegation. Assert warning before save, blocked request where required, exact new hierarchy and
audit; assert suppression on the actual canonical page, not a standalone prop-only render.
**Future validation:** Use an isolated organisation graph; run operator-panel Vitest and later
`pnpm -C apps/web test:web-coverage -- cross-cutting/span-of-control.spec.ts` after suite-target repair.
Expected: correct positive and negative tier behaviour and persisted delegation.
**Completion:** Real hierarchy edits enforce the threshold and create the required evidence without false warnings.

### The Observer Workspace Has No Audit Data, Read-Back or Evidence Export

- [ ] AUD-035-011 Wire the observer timeline to authoritative audit reads and evidence export

**Priority:** P2. **Original obligations:** FR-003; US1 acceptance 4; audit pagination edge; T038; operational observer brief.
**Expected/observed/impact:** The mounted observer panel receives `rows={[]}`
([persona-workspace.tsx](../../apps/web/src/components/workspaces/persona-workspace.tsx#L76)); its synthetic denial POST
ignores the response and never refetches the original row
([observer-auditor-timeline.tsx](../../apps/web/src/app/workspaces/[personaId]/_panels/observer-auditor-timeline.tsx#L32)).
There is no export or pagination control in that component. The rejection label is useful authored UX, not proof that
the authoritative record remained byte-identical or that an evidence file was produced.

**Developer instructions:** Load the unified timeline from AUD-035-003, paginate stable cycle-filtered results, surface
server-confirmed rejected mutation evidence and refetch the original immutable row. Add authorised hash-recorded
evidence export with a working detail route; reuse the existing denial and evidence services where suitable. Distinguish
transport failure from confirmed denial. Do not add an actual write/delete capability to immutable rows.
**Tester instructions:** Extend
[operator-panels.test.tsx](../../apps/web/tests/unit/spec_035/operator-panels.test.tsx#L29),
[audit-append-only.spec.ts](../../tests/e2e/web-coverage/cross-cutting/audit-append-only.spec.ts#L1), and
[observer-auditor.append-only-timeline.spec.ts](../../tests/e2e/web-coverage/operational/observer-auditor.append-only-timeline.spec.ts#L1).
Use one existing immutable row, denied PATCH/DELETE, network failure, unauthorised export, 501 entries and two cycles.
Assert server denial plus appended rationale/operator record, byte-identical original, cursor continuity, valid download
and downloaded-byte hash. A local message alone must not pass.
**Future validation:** After unified store and authenticated local fixtures, run operator-panel Vitest and the two named
read-only E2E homes through
`pnpm -C apps/web test:web-coverage -- cross-cutting/audit-append-only.spec.ts operational/observer-auditor.append-only-timeline.spec.ts`.
Expected: real rejection/read-back/export with
no mutation or silent failure. Storage immutability permissions remain a later authorised gate.
**Completion:** The canonical observer and audit-bearing routes expose usable, authoritative append-only evidence.

### Sector Pages Do Not Drive Their Canonical Persona Depth Contracts

- [ ] AUD-035-012 Bind canonical sector personas to complete jurisdiction-specific workflows

**Priority:** P1 scope closure. **Original obligations:** FR-001, FR-002, FR-014, FR-015, FR-016, FR-017, FR-018,
FR-019, FR-020, FR-021, FR-022; SC-003, SC-004; US3 acceptance 1, 2, 3, 4, 5;
T050, T051, T052, T054, T055, T056, T057, T058, T059, T060, T061, T072; all sector briefs.

**Expected/observed/impact:** The 13 pages are reachable from the authored sector index
([page.tsx](../../apps/web/src/app/(operations)/sectors/page.tsx#L166)), but the canonical persona workspace sets role to
the persona ID ([persona_workspace_service.py](../../apps/api/app/services/persona_workspace_service.py#L14)) and only
matches operational IDs in panel selection. Sector pages use fixed scenarios, identities and empty sources instead of
the seed-bound persona's workflow. SAPOL has no delegation or role-separated transition; SES-SA has no convoy, shelter
or air-bridge controls. The overlay component is a list of toggle buttons without GeoJSON
([index.tsx](../../apps/web/src/components/infrastructure-overlay/index.tsx#L86)). SJA-NT is titled tropical cyclone
instead of the required disease/RFDS/telemedicine workflow
([page.tsx](../../apps/web/src/app/(operations)/sectors/sja-nt-tropical/page.tsx#L15)). BoM acknowledgement is local state
only ([page.tsx](../../apps/web/src/app/(operations)/sectors/bom-broadcast-relay/page.tsx#L38)); NEMA composes generic
panels without DACC/JATWC lifecycle. These are authored shells, not the required state-changing depth.

**Developer instructions:** Use the existing 68-persona registry and depth-profile routes/selectors, mapping function,
jurisdiction and field/remote capability rather than treating sector IDs as operational roles. Connect the canonical
workspace to the appropriate shared workflow, not a new persona inventory. Implement the specific missing capabilities
listed in the 13-row sector accounting table below: delegated LGA authority/role separation; convoy/shelter/air bridge;
reviewed cultural warning; real port/rail/power and ferry/air overlays with prioritisation and handoff; AFP/territory
cross-identity command/declaration; disease/RFDS/telemedicine; published-warning ABC/SBS relay acknowledgement; full DACC
and JATWC lifecycle; ICA funding handoff with Built/Economic deltas. Use the existing domain services where present,
enforce auth/redaction at their controlling boundaries, and persist every transition with audit. Dependencies are the
approval, warning, cultural-safety, offline, recovery and identity/audit tasks; preserve seed shape and read-only suite.

**Tester instructions:** Extend
[us3-components.test.tsx](../../apps/web/tests/unit/spec_035/us3-components.test.tsx#L16); the sector accounting table
names each existing E2E home. Fixtures: two LGAs and denied publisher; disconnected convoy; approved/held language packs;
port/rail/power outage and inaccessible private overlay; ferry plus medevac interruption; AFP/ACT authority collision;
each named NT disease and failed RFDS connection; ABC and SBS ack/no-ack; DACC request through after-action and illegal
skipped stages; insurance handoff with measurable two-environment deltas. Assert persisted states, identity/correlation,
actual maps/content, no unauthorised network call, and post-transition audit from each canonical persona route.

**Future validation:** Prepared canonical seed scenarios and authorised role fixtures; run US3 component Vitest, then
`pnpm -C apps/web test:web-coverage -- sectors/` with reviewed production-target support. Expected: all 13 unchanged
cycle-1 tests exercise real transitions with no bailout, and eastern-state inherited depths do not regress.
**Completion:** All canonical sector workflows satisfy their own selectors, transitions, negative authority cases and
audit obligations. A sector index link or descriptive label alone cannot close a row.

### Recovery Subdomains Are Labels and Placeholder Data Rather Than Editable State

- [ ] AUD-035-013 Connect four recovery environments and claims handoff to current incident data

**Priority:** P2. **Original obligations:** FR-022, FR-023, FR-024; SC-008; US4 acceptance 1, 3;
US3 acceptance 5; T052, T060, T062, T063, T064, T065, T066.

**Expected/observed/impact:** The dashboard renders six subdomain names and reads unimplemented claims/Sendai URLs,
retaining zero-valued placeholders or silently omitting data on failure
([page.tsx](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L28),
[page.tsx](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L76),
[page.tsx](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L206)). The utility page always supplies a zero
snapshot ([page.tsx](../../apps/web/src/app/(operations)/sectors/utility-insurance-recovery/page.tsx#L11)). Existing
incident recovery indicator updates are real reusable source
([recovery.py](../../apps/api/app/api/routes/recovery.py#L59)), but these new views do not call them. Current read-only
widgets therefore do not establish four updatable environments or an Economic/Built funding delta.

**Developer instructions:** Reuse incident recovery/catalogue services and map their domains explicitly to Social,
Built, Economic and Natural. Connect current claims, losses and six subdomain actions to incident-scoped persistence;
refresh all panels when incident or underlying data changes, without reload. Replace silent placeholders with honest
loading/unavailable/error states. Implement authorised funding handoff and Built/Economic deltas, audit each action and
bind the real signed handover from AUD-035-007. Compute/display the ratio consistently and preserve seed compatibility;
trace rows must be produced by evidence of the action, never directly forged by the UI.

**Tester instructions:** Extend the existing
[us3-components.test.tsx](../../apps/web/tests/unit/spec_035/us3-components.test.tsx#L39) and
[recovery-environments.spec.ts](../../tests/e2e/web-coverage/cross-cutting/recovery-environments.spec.ts#L1).
The originally proposed recovery-dashboard and insurance-handoff integration files are not present; proposed homes are
`apps/web/tests/integration/spec_035/recovery-dashboard.test.tsx` and
`apps/web/tests/integration/spec_035/insurance-recovery-handoff.test.tsx` (not existing evidence).
Use two incidents, four populated/empty environments, all six subdomains, stale claims, denied funding, pending/error
reads, ratio .29/.30, and a successful utility funding transfer. Assert incident isolation, visible/updateable values,
refresh without reload, two durable environment deltas, audit and the correct SC-005 parent outcome tuple.

**Future validation:** After adding the proposed discovered tests and isolated API fixtures, run
`pnpm -C apps/web exec vitest run tests/integration/spec_035/` and later the existing recovery E2E home with its canonical
resilience-planner scenario. Expected: every domain is data-backed and editable, failures are visible and no placeholder
can satisfy a recovery outcome.
**Completion:** Current incident data and audited operator updates drive all four environments, claims and handover.

### Browser Requests Never Use the Authored Bearer Helper

- [ ] AUD-035-014 Integrate bearer acquisition and principal-aware requests into the real UI clients

**Priority:** P1 integration. **Original obligations:** FR-009, FR-010, FR-011, FR-030; T024, T029, T036, T037,
T040, T044, T046; US2 and authenticated US1/US3 workflows.
**Expected/observed/impact:** MSAL acquisition exists
([entra-msal.ts](../../apps/web/src/lib/auth/entra-msal.ts#L76)), but the bounded web/shared-UI source search found no
caller. Workspace loading uses bare fetch ([personas.ts](../../apps/web/src/lib/api/personas.ts#L35)); the panels and
offline replay do likewise. The rewrite only forwards requests
([next.config.ts](../../apps/web/next.config.ts#L28)). An authored MSAL helper therefore does not make UI requests
production-authenticated, and adding the production guard can turn the displayed controls into failing requests.

**Developer instructions:** Connect existing sign-in state and a shared authenticated API client to every relevant
workspace, warning, recovery, audit and replay call. Acquire/refresh the correctly scoped bearer and preserve the
effective persona, correlation and explicit per-request impersonation. Match the actual who-am-I contract after
AUD-035-022; enforce permitted controls before sending and handle 401/403/429 visibly without retry storms. Never send
bearers to arbitrary external URLs; retain dev/test isolation without a production anonymous fallback.
**Tester instructions:** Extend existing
[operator-panels.test.tsx](../../apps/web/tests/unit/spec_035/operator-panels.test.tsx#L14) and
[test_whoami.py](../../apps/api/tests/contract/spec_035/test_whoami.py#L48). A focused MSAL client test at
`apps/web/tests/unit/spec_035/authenticated-api.test.ts` is proposed, not existing evidence. Fixtures: valid/expired
token, silent refresh, interaction-required failure, missing configuration, mismatched persona, per-request admin target,
401/403/429 and offline reconnect. Assert bearer destination/scope, request and audit correlation, no forbidden request,
no sticky impersonation and explicit error UX.
**Future validation:** Prepared mocked MSAL and API adapters; run
`pnpm -C apps/web exec vitest run tests/unit/spec_035/` and the who-am-I pytest file. Later authorised staging validation
must prove Entra-issued tokens work; no token acquisition or authentication attempt occurred here.
**Completion:** Real navigable UI requests use verified identity consistently and enforce route permissions at both ends.

### Model Classification Is Not Fail-Closed Across the Actual Egress Boundary

- [ ] AUD-035-015 Enforce structured fail-closed classification at every model egress

**Priority:** P1 security. **Original obligations:** FR-025, FR-027; Q6, Q9; SC-011; US5 acceptance 1, 2;
PSPF-translation edge; T021, T025, T046.
**Expected/observed/impact:** The spec-035 middleware is limited to five API prefixes and scans raw JSON with regex
([classifier_gateway.py](../../apps/api/app/middleware/classifier_gateway.py#L35)); replacing a numeric JSON token with
an unquoted mask marker can corrupt the payload. PSPF+PII is labelled only PSPF, and the unreadable-body branch does
not set `classifier_failed`. The claimed fifth failure branch and admin rejection are not exercised by
[test_classifier_branches.py](../../apps/api/tests/contract/spec_035/test_classifier_branches.py#L44).
Relocated protection is present: the real Foundry caller invokes the shared model gateway before completion. However,
an absent region or missing gateway import returns original messages, only string user messages are scanned, and tool
schemas/non-user content pass through ([foundry_chat_client.py](../../apps/agents/common/foundry_chat_client.py#L367)).
The shared classifier falls back on analyser failure ([model_gateway.py](../../apps/agents/common/model_gateway.py#L135)).
Neither path supplies the complete Q6 identities/outcomes and AU-source link to the canonical audit/UI chain. No actual
data transit was executed or asserted in this review.

**Developer instructions:** Reuse the shared model gateway rather than adding another parallel policy. Require an
authoritative endpoint/region/registry binding; deny on unknown configuration, unavailable classifier, timeout or error.
Classify all potentially regulated message/tool fields structurally while preserving schema and routing metadata.
Implement deterministic PSPF/PII/both/clean/failure outcomes, no admin bypass, zero prohibited outbound calls, durable
correlated classifier evidence and the mask UI. Resolve the contract's AU-original retention conflict explicitly;
provide an authorised AU-source link if Q6 remains authoritative. Keep translation and human-only fallback within the
same boundary and preserve existing Foundry transport compatibility. Depends on AUD-035-002/003/016/020/022.
**Tester instructions:** Extend
[test_classifier_branches.py](../../apps/api/tests/contract/spec_035/test_classifier_branches.py#L64),
[test_data_minimisation_gateway.py](../../tests/integration/test_data_minimisation_gateway.py#L1), and
[test_foundry_chat_client.py](../../tests/contract/test_foundry_chat_client.py#L1).
Fixtures: each PSPF marking, TFN/Medicare checksums, landline/mobile/email/DOB/address/name, mixed PSPF+PII, numeric JSON,
Unicode-escaped text, tool and non-user content, classifier error/timeout/unavailable module, unknown region, admin and
translation. Use an outbound-call spy; assert zero calls on denial, exact safe bytes on mask, repeat-mask idempotency,
unchanged schema, correct audit/response correlation and visible AU-source link. Do not call a model.
**Future validation:** Prepared fake Foundry transport and isolated audit; run
`uv run pytest apps/api/tests/contract/spec_035/test_classifier_branches.py tests/integration/test_data_minimisation_gateway.py tests/contract/test_foundry_chat_client.py -q`.
Expected: all five Q6 branches and every egress failure fail closed, with no real network/model execution in unit tests.
**Completion:** All model-bound regulated data passes one enforceable policy, and the operator can inspect its exact
decision in the authoritative timeline.

### Residency Labels Do Not Surface Registry Freshness or Recommendation Provenance

- [ ] AUD-035-016 Surface authoritative sovereignty and carve-out state across regulated routes

**Priority:** P2 compliance. **Original obligations:** FR-025, FR-026, FR-027, FR-028, FR-029; SC-010, SC-011;
US5 acceptance 1, 3; stale-registry/banner edges; T035, T046, T067, T069, T070, T071, T073, T074.
**Expected/observed/impact:** The root layout renders the shared shell without sovereignty or registry state
([layout.tsx](../../apps/web/src/app/layout.tsx#L27),
[app-shell.tsx](../../packages/ui/src/components/layout/app-shell.tsx#L16)). Fixed AU labels exist on directory,
governance, help and sector surfaces, but not every regulated route. No web/shared-UI registry consumer or MSAL-connected
model-source label was found. The repository accepts empty approvers and missing-file empty success, returns unsigned
unpaginated entries, and derives staleness from file dates
([carveout_registry_repository.py](../../apps/api/app/repositories/carveout_registry_repository.py#L49),
[governance.py](../../apps/api/app/api/governance.py#L313)). All five checked-in rows are 129-130 days old as of this
review ([foundry_carveout_registry.json](../../data/governance/foundry_carveout_registry.json#L1)). The review workflow
is manual-only ([foundry-carveout-review.yml](../../.github/workflows/foundry-carveout-review.yml#L3)). Recorded names and
notes are not evidence of current human approvals or deployed residency.

**Developer instructions:** Put first-party residency/registry state in common regulated-route chrome, with a working
compliance registry link, model-source badge, render-time correlated audit, stale/empty/malformed/missing approval
warnings and exact `GAP-CARVEOUT-STALE` reporting. Preserve the explicit file-backed deferral in T070 but enforce its
schema, freshness, authentication, signed/paginated contract and failure semantics; do not fabricate review dates or
approvals. Align CI freshness enforcement with the actual consumed registry. Repair mask-detail/AU-source navigation
and language-source/fallback state; no third-party suppressible banner widget. Depends on identity/audit/gateway fixes.
**Tester instructions:** Existing homes are
[classifier-banner.test.tsx](../../apps/web/tests/unit/spec_035/classifier-banner.test.tsx#L13),
[data-sovereignty.spec.ts](../../tests/e2e/web-coverage/cross-cutting/data-sovereignty.spec.ts#L13), and
[accessibility-and-multilingual.spec.ts](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts#L14).
Proposed local replacement for the absent claimed T067 test:
`apps/web/tests/unit/spec_035/sovereignty-banner.test.tsx` (not existing evidence).
Use 89/90/91-day entries, empty approvers, invalid dates, unavailable store, AU/non-AU recommendation and each regulated
route/deep-link. Assert warnings and labels from actual data, working keyboard-accessible links, no placeholder approval,
render-event audit and matching server pagination/signature verification.
**Future validation:** Prepared local clock/registry fixtures; run the proposed banner test and existing classifier
banner Vitest test, then the named cross-cutting E2E homes only after the approved suite-target/coverage decision.
Expected: every required route and freshness edge is covered. Human review renewal is a separate future approval gate.
**Completion:** The shared UI accurately reports region, model origin, freshness and approval state, including failure
states, without converting an authored label into a deployment or approval claim.

### Rate Limits Are Not Bound to Verified Identity or the Actual Request Path

- [ ] AUD-035-017 Enforce authenticated rate budgets before side effects and audit real rejections

**Priority:** P1. **Original obligations:** FR-006, FR-009, FR-012, FR-013; Q3, Q7; US2 acceptance 4;
T009, T011, T012, T019, T026; SC-009, SC-012.
**Expected/observed/impact:** The APIM module declares budgets but keys on caller-controlled `X-Persona-Id` and
subscription, has no admin/replay/dev exemptions, and nests `<on-error>` inside `<inbound>`
([apim-rate-limit.bicep](../../infra/modules/apim-rate-limit.bicep#L96)). It declares no API/backend routing for the
application. The middleware waits until after the handler for a response header that an upstream APIM rejection cannot
send through that handler ([rate_limit_audit.py](../../apps/api/app/middleware/rate_limit_audit.py#L37)). Thus the
isolated injected-header test establishes response conversion only, not 10/minute, 600/hour or global 600/minute control.

**Developer instructions:** Bind APIM to the real API route with trusted JWT claim extraction and stripped/spoof-proof
internal headers. Key per-persona budgets on verified persona plus canonical route, and implement admin bypass and the
bounded offline replay exemption while retaining one true global ceiling. Enforce budgets before domain side effects,
integrate actual gateway rejections into durable Q10 audit/envelopes, and consume App Configuration values. Use AVM
composition and a documented supported policy structure; reconcile gateway-first rate enforcement with Q10 precedence.
Preserve dev/test no-limit mode and avoid a process-local replacement counter. Depends on AUD-035-002/003/018/019/022.
**Tester instructions:** Extend
[test_rate_limit.py](../../apps/api/tests/contract/spec_035/test_rate_limit.py#L38) with a policy/request adapter and
isolated clock rather than a handler that injects a header. Cover calls 10/11, hourly 600/601, multi-persona/subscription
global 600/601, claimed-persona spoof, admin, replay-window expiry, dev/test and schema-error collisions. Assert no domain
call on rejection, correct bucket attribution/state, matching Retry-After/envelope and canonical audit read-back.
**Future validation:** Local fixtures first: `uv run pytest apps/api/tests/contract/spec_035/test_rate_limit.py -q`.
Later, with an approved isolated APIM deployment, validate policy compilation and actual budgets through the configured
gateway; do not infer these results from FastAPI header mocks or run them against production without approval.
**Completion:** Real request budgets, exceptions, precedence and rejected-call evidence are proven on the routed path.

### The Activation Mutex Checks Different Flags from the Auth Routers

- [ ] AUD-035-018 Enforce the real auth activation mutex at startup and in CI

**Priority:** P1 security. **Original obligations:** FR-009, FR-013; Q8; US2 acceptance 6; dual-guard edge;
T005, T013, T014, T027, T028, T076.
**Expected/observed/impact:** The router selects `AMA_TEST_SUPPORT`, resolved environment and
`AMA_ENABLE_PRODUCTION_AUTH` ([router.py](../../apps/api/app/api/router.py#L136)). The startup invariant instead checks
`ACTIVATION_SIMULATION` and `ACTIVATION_PRODUCTION`
([activation_mutex.py](../../apps/api/app/middleware/activation_mutex.py#L71)); its audit is best effort and lacks the
specified resolved environment/middleware fields. The script scans those unrelated flags and Bicep simulation switches,
not the route guards or middleware wiring ([verify-activation-mutex.ps1](../../scripts/verify-activation-mutex.ps1#L47)).
Tests exercise only those alternate flags, so they cannot establish prevention of actual auth co-activation.

**Developer instructions:** Share one canonical resolved activation model across router registration, middleware and
lifespan. Refuse prohibited production/test-support combinations and dev/test co-activation before serving traffic;
persist the exact violation context to boot-independent durable audit before nonzero termination. Make fixture-principal
configuration fail closed in production. Change the static CI check to inspect the actual guard/wiring, run for
test/staging/production and explicitly skip dev, retaining the lifespan invariant everywhere. Preserve legitimate
dual-guard CI behaviour; no fallback registration in production can silently weaken the protected contract.
**Tester instructions:** Extend
[test_activation_mutex.py](../../apps/api/tests/unit/spec_035/test_activation_mutex.py#L16) and
[test_production_reach.py](../../apps/api/tests/contract/spec_035/test_production_reach.py#L16).
Use the full environment/flag matrix, real app startup, missing middleware registration and independent audit-store
failure/restart fixtures. Assert refusal before handlers, exactly one durable violation with all fields, next-boot
read-back, correct dev exemption and clean mutually exclusive registrations. Do not substitute alternate flag names.
**Future validation:** Prepared isolated store; run
`uv run pytest apps/api/tests/unit/spec_035/test_activation_mutex.py apps/api/tests/contract/spec_035/test_production_reach.py -q`.
Only in a later authorised phase run `pwsh -File scripts/verify-activation-mutex.ps1` over clean and deliberately
conflicting configuration fixtures. Expected: the canonical flag conflict fails and only the build-time dev leg skips.
**Completion:** The actual auth paths cannot co-activate, and failure evidence survives the failed boot.

### Hardening Infrastructure Is Authored but Disabled and Disconnected

- [ ] AUD-035-019 Wire hardening resources, signing identity and configuration through the deployment graph

**Priority:** P1 production readiness. **Original obligations:** T009, T010, T011, T012; FR-006, FR-007, FR-012,
FR-013, FR-016; ASM-004, ASM-006, ASM-009; Q2, Q3, Q4, Q5, Q7, Q8.
**Expected/observed/impact:** Four AVM-composed modules are present, but the main switch defaults false and is omitted
from checked-in dev/staging/production parameter files
([main.bicep](../../infra/main.bicep#L182)). AppConfig is only a deployment dependency; its outputs, gateway routing,
blob access and signing configuration are not fed into the applications. The signing module receives `apiPrincipalId:
''` ([main.bicep](../../infra/main.bicep#L224)), creates a key but leaves the certificate out of band
([recovery-signing-keyvault.bicep](../../infra/modules/recovery-signing-keyvault.bicep#L1)). The blob's legal-hold tag is
metadata, not an applied hold ([blob-immutable.bicep](../../infra/modules/blob-immutable.bicep#L78)). AppConfig lacks the
elder targets/fallback chains and T044 rotation-runbook key
([app-configuration.bicep](../../infra/modules/app-configuration.bicep#L76)). Comments and generated templates do not
prove resources, permissions or immutability are deployed.

**Developer instructions:** Complete the existing deployment graph without replacing working shared resources: explicit
environment selection, validated gateway/backend routing, private connectivity/DNS, required RBAC, AU persistence,
real signing certificate and managed identity, enforced legal hold/version retention, and consumed configuration
outputs. Align key names with actual code and document any AVM child-resource exception. Discover/obey target governance
constraints in the later approved infrastructure phase; never change policy to fit a template. Maintain additive
resource compatibility, no extra IdP/non-Azure hosting, and operator-controlled signing rotation. Depends on AUD-035-007,
AUD-035-017 and AUD-035-018; no resource operation is authorised by this report.
**Tester instructions:** Use the existing Bicep module files and parameter files as fixture homes; a focused static
assertion home `infra/tests/spec-035-hardening.tests.ps1` is proposed, not existing evidence. Assert selected environment,
nonempty identity, consumed outputs, legal-hold versus metadata, certificate expiry, trusted route budgets and mandatory
settings. Negative fixtures omit each dependency, disable private reachability or reference an unapproved region.
**Future validation:** With the already installed matching Bicep toolchain, run
`bicep build infra/main.bicep` and `bicep build infra/modules/apim-rate-limit.bicep` in a later authorised build phase.
Then obtain an approved sandbox, governance constraints and credentials for what-if/policy/access/retention validation.
Expected: additive changes, usable private endpoints, correct identity permissions and verifiable retention/signature.
**Completion:** The application consumes the actual hardened resources and settings, and independent approved deployment
evidence establishes their state; authored IaC alone is insufficient.

### Local Specifications and Closure Documents Disagree About Required Behaviour

- [ ] AUD-035-020 Resolve contract conflicts and correct the operational documentation with explicit decisions

**Priority:** P2 contract governance. **Original obligations:** Q1, Q2, Q5, Q6, Q7, Q8, Q10; FR-001, FR-006,
FR-007, FR-009, FR-010, FR-011, FR-016, FR-027, FR-030; T008, T011, T024, T044, T045, T068, T074,
T078, T079, T080, T081; research, model, checklist, briefs and quickstart.
**Expected/observed/impact:** An implementer should have one consistent contract. Conflicts include Q5's two override
levels versus the lower-level one-level policy; low/medium/high versus decimal confidence; unconditional life-safety
admission versus rejecting an all-life-safety full queue; an unspecified pre-existing AU-source reference policy under
Q6 versus the contract's prohibition on persisting originals after masking;
seven error codes versus T044/T045's `signing_key_expired`; missing persona claim 401 versus task 403; `pass|fail|gap`
versus `inconclusive`; and forbidden simultaneous auth versus quickstart Mode B
([spec.md](spec.md#L37), [data-model.md](data-model.md#L42), [quickstart.md](quickstart.md#L40)). The quickstart's
verification matrix renames many SCs and its mutex description describes an unrelated runtime behaviour
([quickstart.md](quickstart.md#L202)). The architecture diagram includes uninstalled drivers and a different middleware
order ([spec-035-middleware-and-offline.md](../../docs/architecture/spec-035-middleware-and-offline.md#L28)); the
changelog claims a missing global banner and complete workflows ([CHANGELOG.md](../../CHANGELOG.md#L80)). No current
formal panel or human approval record was found. These contradictions cannot be silently resolved by the newest code.

**Developer instructions:** Obtain an explicit source decision for each conflict in the accounting tables, respecting
the original spec/constitution and read-only suite boundary. Repair quickstart payloads, persona IDs, environment names,
correct 12-SC mapping and repository commands; remove advice to strip PSPF labels as a workaround. Distinguish authored
source, deferred infrastructure and unmeasured outcomes in diagrams/changelog. Complete the deferred diagrams/overview
references only in a separately authorised documentation change, without fabricating sign-offs or checking old tasks.
Preserve T068's explicit supersession and the T067/T070/T078/T079 scope amendments as historical decisions, not proof.
**Tester instructions:** Use this spec folder, the architecture document, existing
[test_closed_set_parity.py](../../apps/api/tests/contract/spec_035/test_closed_set_parity.py#L76), and
[test_workspace_bridges.py](../../tests/contract/test_workspace_bridges.py#L76) as existing review/test homes.
Construct positive/negative contract fixtures for every resolved conflict; compare exact IDs/enums/fields/flags and
validate local links. A later staging rehearsal must follow the corrected instructions literally and retain redacted
command/results evidence without changing the original task state retrospectively.
**Future validation:** Text inventory and Markdown diagnostics first; after decisions, run
`uv run pytest apps/api/tests/contract/spec_035/test_closed_set_parity.py tests/contract/test_workspace_bridges.py -q`.
Prerequisites for T081's later rehearsal are an approved staging slot, seeded canonical personas, correct Entra role
tokens, signing/storage configuration and completed workflow fixes. Expected: one coherent contract and reproducible
steps, not merely green document checkmarks.
**Completion:** Each conflict has an explicit decision and aligned implementation/tests/docs, with historical and
runtime/human evidence clearly separated. No original input document is changed by this review.

### The Gate Can Grade Canned Evaluations Without Proving the Required UI Outcomes

- [ ] AUD-035-021 Establish non-vacuous workflow coverage and fresh revision-bound closure evidence

**Priority:** P1 release evidence. **Original obligations:** FR-028, FR-030; SC-001, SC-002, SC-003, SC-004,
SC-005, SC-006, SC-007, SC-008, SC-009, SC-010, SC-011, SC-012;
T001, T002, T003, T004, T005, T017, T018, T019, T020, T021, T022, T023, T032, T033, T034, T035,
T047, T048, T049, T061, T062, T066, T067, T068, T074, T075, T076, T077, T078, T079, T080, T081.

**Expected/observed/impact:** All outcomes must follow real UI state changes at the specified revision and target.
Static inventory found 90 operational/sector spec files using canned `METRIC_INPUTS`, no click/fill/select/offline
interaction calls, and 81 callers of the directory-only `ws.goto()`
([incident-commander.approve-cross-agency-action.spec.ts](../../tests/e2e/web-coverage/operational/incident-commander.approve-cross-agency-action.spec.ts#L39),
[workspaces.po.ts](../../tests/e2e/web-coverage/_support/pages/workspaces.po.ts#L20)). The fixture resolves identities
only through test-support, not production bearer state
([persona.fixture.ts](../../tests/e2e/web-coverage/_support/fixtures/persona.fixture.ts#L40)). Warning/offline/audit/span/
recovery cross-cutting tests also substitute evaluator metrics. Axe asserts zero violations on only three landing routes
([accessibility-and-multilingual.spec.ts](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts#L14)).
The Playwright configuration starts localhost dev/test services
([playwright.config.cts](../../apps/web/playwright.config.cts#L18)); the spec-035 gate is manual and omits browser/preview
validation ([spec-035-gate.yml](../../.github/workflows/spec-035-gate.yml#L3)). General CI does have real shard/merge/gate
definitions, but uses dev/test and uploads `junit-*.xml` instead of the configured nested JUnit path
([ci.yml](../../.github/workflows/ci.yml#L308)). The reporter lacks severity-stratified accessibility output and defaults
missing route/audit metadata ([coverage-reporter.ts](../../tests/e2e/web-coverage/_support/reporter/coverage-reporter.ts#L249)).

**Historical evidence:** The partial trace has zero rows; the stored 2026-05-06 run records zero expected passes and 76
skips. Cycle metadata names `f7fb35e6bf78b8249c4b7012dabd4223b3b905a2`, not reviewed HEAD
([cycle-metadata.json](../../tests/e2e/web-coverage/_artifacts/cycle-metadata.json#L1)). The parent trace is a placeholder
([coverage-trace.md](../034-webapp-capstone-coverage/coverage-trace.md#L1)); the gap JSON has one old closed entry with
no severity ([gap-register.json](../034-webapp-capstone-coverage/gap-register.json#L1)). These records do not prove any
current production, timing, accessibility or human-review outcome. The local baseline inventories, recovery integration
tests, T067 banner test, performance/a11y reports and formal 85-agent register are absent in the bounded inventory.

**Developer instructions:** Preserve the existing suite in this review. Obtain an explicit owner/scope decision for
FR-030/OOS-003 versus the needed production fixture/config and non-vacuous assertion changes; add independent tests in
the existing app-owned test homes in the meantime. Require real route entry, state transition, persistence/read-back,
identity, trace linkage and negative cases for each profile. Repair API tests that assert merely not-404 or enum order;
test actual full-stack precedence/budgets/pairing/egress. Wire CI gating, correct artifact paths, required-status plan,
severity-stratified a11y reporting, revision/environment/seed provenance and all outcome thresholds. Enrich all required
audit outcomes, not only the two pure cultural decisions. Do not close gaps, invent approvals or run deployment as part
of this documentation-only audit; follow the three-cycle escalation/rollback rules in future implementation.

**Tester instructions:** Existing homes are the 5 web unit files, 10 API contract files, 3 API unit files, bridge tests,
the 13 sector files and cross-cutting files indexed below. The integration package contains only its initializer.
Create the specifically proposed missing app-owned tests, keeping them discoverable. Include broken-route, missing
handler, canned-metric-only, denied identity, stale audit, unreviewed language, offline replay failure, invalid PDF,
missing manifest, skipped-only/empty trace and wrong-revision negative fixtures; each must prevent closure. Cover every
P1 deep route, keyboard/focus/labels/contrast, community variants and at least three required jurisdictions; automated axe
does not replace human accessibility review or certify WCAG conformance by itself.

**Future validation:** Already prepared local Python/Node environments and isolated store/JWKS/clock/agent fixtures:
`uv run pytest apps/api/tests/contract/spec_035 apps/api/tests/unit/spec_035 apps/api/tests/integration/spec_035 -q`
and `pnpm -C apps/web exec vitest run tests/unit/spec_035/ tests/integration/spec_035/`.
After explicit suite-scope and target approval, use `pnpm -C apps/web test:web-coverage` with a reviewed target config
that disables local servers for production and supplies legitimate persona bearers. Do not use the quickstart's
nonexistent suite package commands. Expected: complete discovery, positive/negative behaviour assertions, fresh
revision-bound JSON/JUnit/a11y/trace artifacts, >=95% valid tuples, zero unresolved HIGH+ gaps, all 13 sector outcomes,
the stated timing thresholds and <=45-minute full-suite wall clock. Deployment, human/community sign-off and live
resource checks require separate authorisation and evidence.

**Completion:** Every numbered criterion and scenario has current non-vacuous evidence; empty, skipped, stale,
stub-only, unsigned, unauthenticated or wrong-target records cannot produce a ready verdict.

### Error Precedence and Wire Schemas Are Declared but Not Enforced End to End

- [ ] AUD-035-022 Enforce the additive error ladder and shared request-response contracts

**Priority:** P1 compatibility. **Original obligations:** FR-009, FR-010, FR-011, FR-012, FR-013, FR-030;
Q10; US2 acceptance 1, 3, 4, 5, 6; T008, T017, T018, T019, T021, T022, T023, T027, T028, T029.
**Expected/observed/impact:** Unroutable SC IDs must produce 400 before classifier/auth regardless of bearer state. The
only routability check is inside the service after request validation and middleware
([outcome_evaluator_service.py](../../apps/api/app/services/outcome_evaluator_service.py#L194),
[main.py](../../apps/api/app/main.py#L67)). Precedence tests only index an enum
([test_precedence_ladder.py](../../apps/api/tests/contract/spec_035/test_precedence_ladder.py#L14)). The actual who-am-I
model omits `principal_oid` and `tenant_id` and always includes a differently shaped impersonation block
([auth_whoami.py](../../apps/api/app/api/routes/auth_whoami.py#L19)), while its test asserts that different shape.
Pydantic permits non-null retry fields for every code despite the stricter JSON Schema
([extension_envelope.py](../../apps/api/app/domain/extension_envelope.py#L62),
[extension_envelope.schema.json](../../packages/schemas/spec_035/extension_envelope.schema.json#L36)). Error response IDs
are newly generated without binding them to persisted rows; no central handler maps all production schema errors to
the required extension. Success-body `gap` must not become `inconclusive` merely to match the stale local example.

**Developer instructions:** Implement one explicit pre-auth routability check and the agreed Q10 ladder before handler
effects. Preserve parent 400/404/422/503 semantics unless an explicit additive decision defines a mode-specific envelope;
never break the locked success body. Validate principal, replay and extension contracts from the same schemas; enforce
conditional retry fields, numeric/UUID constraints and exact who-am-I shape. Allocate and persist response audit IDs
once through AUD-035-003; retain required operator-facing error detail in a contract-approved field, especially signing
expiry. Align the actual middleware order and gateway rejections, not only a constant tuple.
**Tester instructions:** Extend
[test_precedence_ladder.py](../../apps/api/tests/contract/spec_035/test_precedence_ladder.py#L18),
[test_production_reach.py](../../apps/api/tests/contract/spec_035/test_production_reach.py#L41),
[test_whoami.py](../../apps/api/tests/contract/spec_035/test_whoami.py#L48), and
[test_closed_set_parity.py](../../apps/api/tests/contract/spec_035/test_closed_set_parity.py#L179).
Use the real app with every stacked pair of errors, malformed body plus sc-006/sc-011, invalid token plus PSPF,
wrong-role plus exhausted bucket, valid request and missing seed, unknown persona/scenario, five routable outcomes,
retry-field violations and 51-entry replay. Assert exact HTTP/body/schema, zero lower-priority handler calls, identical
response/audit IDs and envelopes, and unchanged dual-guard success/errors.
**Future validation:** Isolated full-stack fixture with resolved policy decisions; run
`uv run pytest apps/api/tests/contract/spec_035/test_precedence_ladder.py apps/api/tests/contract/spec_035/test_production_reach.py apps/api/tests/contract/spec_035/test_whoami.py apps/api/tests/contract/spec_035/test_closed_set_parity.py -q`.
Expected: all stacked conditions return the contractually highest-priority result, and schemas agree across languages.
**Completion:** The real request path, not an enum-order test, enforces the agreed additive contract and audit linkage.

## Original Task Coverage

States below reproduce the original source literally, including uppercase `[X]`. There are 82 task rows, not the
81 claimed by the original summary. T024b is a separate task. IMPLEMENTED assesses source/artifact obligations only;
test/build/install/deployment/human execution is never implied. Pure execution tasks remain UNVERIFIED.
Negative artifact searches are bounded in the later search ledger; no missing historical path alone is used as proof.

| Original task | Original state | Status | Concrete evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [X] | PARTIAL | All four web dependencies and lock entries exist: [package.json](../../apps/web/package.json#L22), [pnpm-lock.yaml](../../pnpm-lock.yaml#L25). Install/typecheck outcome unverified; the named `typecheck` script is absent. | AUD-035-020, AUD-035-021 |
| T002 | [X] | PARTIAL | Azure identity/certificates/blob and jose are declared, but `endesive` is not: [pyproject.toml](../../apps/api/pyproject.toml#L10). Signing remains a marker; sync/import/lock execution unverified. | AUD-035-007, AUD-035-021 |
| T003 | [X] | IMPLEMENTED | Shared package has exports, declarations and build/typecheck scripts: [package.json](../../packages/domain/package.json#L1), [index.ts](../../packages/domain/src/index.ts#L14). Placeholder task progressed to real types; build execution not claimed. | AUD-035-021 |
| T004 | [X] | IMPLEMENTED | Contract/unit/integration package initializers exist; [pyproject.toml](../../pyproject.toml#L45) uses importlib discovery. Actual collection not run; integration directory still contains only its initializer. | AUD-035-021 |
| T005 | [X] | PARTIAL | [spec-035-gate.yml](../../.github/workflows/spec-035-gate.yml#L3) is manual-only, runs contract/unit checks, omits preview E2E and environment matrix. General [ci.yml](../../.github/workflows/ci.yml#L263) is dev/test, not the requested production-mirror gate. | AUD-035-018, AUD-035-021 |
| T006 | [X] | IMPLEMENTED | Exact 20 values in [audit-outcome.ts](../../packages/domain/src/audit-outcome.ts#L9) and [audit_outcome.py](../../apps/api/app/domain/audit_outcome.py#L14), with [parity assertions](../../apps/api/tests/contract/spec_035/test_closed_set_parity.py#L76). Writers do not all enforce this enum. | AUD-035-003 |
| T007 | [X] | PARTIAL | Exact 11 values and guard in [app-role.ts](../../packages/domain/src/app-role.ts#L7), [app_role.py](../../apps/api/app/domain/app_role.py#L14). [Parity test](../../apps/api/tests/contract/spec_035/test_closed_set_parity.py#L118) lacks the specified 12th-role negative; RBAC has fail-open scope. | AUD-035-002, AUD-035-021 |
| T008 | [X] | PARTIAL | Schema and re-exported model exist: [schema](../../packages/schemas/spec_035/extension_envelope.schema.json#L36), [model](../../apps/api/app/domain/extension_envelope.py#L62). Conditional retry restriction is absent from Pydantic; tests only check permissive round trips. | AUD-035-022 |
| T009 | [X] | PARTIAL | AVM APIM host and policy authored: [apim-rate-limit.bicep](../../infra/modules/apim-rate-limit.bicep#L71). Untrusted header key, unsupported nested error section, missing application route/exemptions; no build or PSRule run. | AUD-035-017, AUD-035-019 |
| T010 | [X] | PARTIAL | Versioned retention configuration exists, but legal hold is metadata: [blob-immutable.bicep](../../infra/modules/blob-immutable.bicep#L78). Deployment/hold/overwrite proof absent. | AUD-035-007, AUD-035-019 |
| T011 | [X] | PARTIAL | Scalar keys authored: [app-configuration.bicep](../../infra/modules/app-configuration.bicep#L76). No consumed output wiring, elder/fallback/runbook keys, or named spec parameter file; Q5 override conflict persists. | AUD-035-006, AUD-035-019, AUD-035-020 |
| T012 | [X] | PARTIAL | Modules are conditional and signing principal empty: [main.bicep](../../infra/main.bicep#L182), [main.bicep](../../infra/main.bicep#L224). Certificate deferred and resource outputs disconnected; deployment unverified. | AUD-035-019 |
| T013 | [X] | CONFLICT | [verify-activation-mutex.ps1](../../scripts/verify-activation-mutex.ps1#L47) checks different flags, omits resolved auth guards/dev exemption and returns different breach code. Script not executed. | AUD-035-018 |
| T014 | [X] | CONFLICT | Installed lifespan checks alternate flags and best-effort audit: [activation_mutex.py](../../apps/api/app/middleware/activation_mutex.py#L71). [Tests](../../apps/api/tests/unit/spec_035/test_activation_mutex.py#L16) validate that different invariant, not Q8. | AUD-035-003, AUD-035-018 |
| T015 | [X] | PARTIAL | Paired batch method exists but falls back to sequential creates: [audit_repository.py](../../apps/api/app/repositories/audit_repository.py#L116). [Tests](../../apps/api/tests/unit/spec_035/test_audit_repository.py#L55) use memory, not mocked atomic Cosmos batch. | AUD-035-003 |
| T016 | [X] | PARTIAL | Appender installed; [audit_appender.py](../../apps/api/app/middleware/audit_appender.py#L90) skips reads, writes after response, trusts raw impersonation and swallows failures. [Tests](../../apps/api/tests/unit/spec_035/test_audit_appender.py#L79) cover synthetic writes only. | AUD-035-003 |
| T017 | [X] | PARTIAL | Relocated [test_production_reach.py](../../apps/api/tests/contract/spec_035/test_production_reach.py#L41) checks `!=404` for one SC with an invalid body, not five exact 200 success contracts. | AUD-035-021, AUD-035-022 |
| T018 | [X] | PARTIAL | Relocated [test_precedence_ladder.py](../../apps/api/tests/contract/spec_035/test_precedence_ladder.py#L18) compares enum indices only; no stacked HTTP conditions or middleware order tested. | AUD-035-022 |
| T019 | [X] | PARTIAL | [test_rate_limit.py](../../apps/api/tests/contract/spec_035/test_rate_limit.py#L38) injects a header on a 200 handler; never tests 11/601 calls, hourly ceiling, identity key or actual audit. | AUD-035-017, AUD-035-021 |
| T020 | [X] | PARTIAL | [test_impersonation_pairing.py](../../apps/api/tests/contract/spec_035/test_impersonation_pairing.py#L70) checks an in-memory recorder; no actual transaction, timeline read or spoofed-header audit assertion. | AUD-035-002, AUD-035-003 |
| T021 | [X] | PARTIAL | [test_classifier_branches.py](../../apps/api/tests/contract/spec_035/test_classifier_branches.py#L64) tests clean/PII/PSPF/mixed paths in an isolated stack; failure and authenticated-admin/no-bypass audit cases absent. | AUD-035-015, AUD-035-021 |
| T022 | [X] | PARTIAL | [test_offline_replay.py](../../apps/api/tests/contract/spec_035/test_offline_replay.py#L67) tests local ledger/dedupe/time, accepts either 413/422, omits real payload effects, overflow and full auth. | AUD-035-004 |
| T023 | [X] | CONFLICT | [test_whoami.py](../../apps/api/tests/contract/spec_035/test_whoami.py#L48) asserts implementation's non-contract shape and omits RBAC middleware/non-admin-header negative. | AUD-035-002, AUD-035-022 |
| T024 | [X] | PARTIAL | JWKS signature/issuer/audience logic exists: [entra_auth.py](../../apps/api/app/middleware/entra_auth.py#L85). Environment-unbounded fixture bypass and missing exact-role/claim checks remain; inner auth overwrites claims. | AUD-035-002, AUD-035-014 |
| T024b | [X] | PARTIAL | [rbac_check.py](../../apps/api/app/middleware/rbac_check.py#L125) returns for admin, allows unresolved persona, selects first role. Real seed has all 68 mappings; complete mapping enforcement is missing. | AUD-035-002 |
| T025 | [X] | PARTIAL | Classifier resides in [middleware](../../apps/api/app/middleware/classifier_gateway.py#L80), not a separate service. Limited prefixes, raw JSON regex, incomplete failure/mixed outcome handling and egress linkage. | AUD-035-015 |
| T026 | [X] | PARTIAL | [rate_limit_audit.py](../../apps/api/app/middleware/rate_limit_audit.py#L37) converts a downstream header only after handler execution; not actual APIM rejection/audit integration. | AUD-035-017 |
| T027 | [X] | CONFLICT | [main.py](../../apps/api/app/main.py#L55) installs new and legacy auth; real order lacks pre-auth routability, legacy overwrites identity, mutex checks unrelated flags. | AUD-035-002, AUD-035-018, AUD-035-022 |
| T028 | [X] | PARTIAL | Additive production router registration exists: [router.py](../../apps/api/app/api/router.py#L157). Middleware does not stay inert with dual guard, store remains local, fallback path has another schema. | AUD-035-003, AUD-035-018, AUD-035-022 |
| T029 | [X] | CONFLICT | Mounted [auth_whoami.py](../../apps/api/app/api/routes/auth_whoami.py#L19) returns different identity/impersonation fields and no tenant ID; conflicts with OpenAPI. | AUD-035-002, AUD-035-022 |
| T030 | [X] | PARTIAL | Logic relocated into [offline_replay.py](../../apps/api/app/api/routes/offline_replay.py#L102). Audits without executing payload; header persona, memory dedupe and incomplete limits/metadata remain. | AUD-035-004 |
| T031 | [X] | PARTIAL | [offline_queue_overflow_repository.py](../../apps/api/app/repositories/offline_queue_overflow_repository.py#L25) exists but has no production caller and omits specified displacement/tier/depth fields. No dedicated/replacement test found. | AUD-035-004, AUD-035-021 |
| T032 | [X] | UNVERIFIED | Checked source claims a local/staging run: [tasks.md](tasks.md#L234). Integration package is empty of tests and no current staging evidence is present; no run performed. | AUD-035-021 |
| T033 | [ ] | MISSING | Required baseline inventory is absent in bounded web test/artifact search: [task obligation](tasks.md#L251). Historical empty trace is not a replacement. | AUD-035-021 |
| T034 | [X] | PARTIAL | [offline-queue-store.test.ts](../../apps/web/tests/unit/spec_035/offline-queue-store.test.ts#L56) covers small-cap/dedupe/ordering/encryption helpers; not per-persona isolation, side buffer, retained failures or 500-entry replay. | AUD-035-004, AUD-035-021 |
| T035 | [X] | IMPLEMENTED | [classifier-banner.test.tsx](../../apps/web/tests/unit/spec_035/classifier-banner.test.tsx#L13) asserts count/link and suppression for other outcomes. Component test source is complete; real navigation/egress integration is not. | AUD-035-015, AUD-035-016 |
| T036 | [X] | PARTIAL | Relocated [approval card](../../apps/web/src/app/workspaces/[personaId]/_panels/ic-approval-card.tsx#L52) is mounted but body/schema/state/evidence capture are wrong; bridge only echoes audit. | AUD-035-001 |
| T037 | [X] | PARTIAL | [PIO composer](../../apps/web/src/app/workspaces/[personaId]/_panels/pio-aws-composer.tsx#L56) drafts English-labelled variants, has unbound approval callback, no publish and inadequate inline scan. | AUD-035-005, AUD-035-006 |
| T038 | [X] | PARTIAL | [Observer panel](../../apps/web/src/app/workspaces/[personaId]/_panels/observer-auditor-timeline.tsx#L32) has denial copy, but empty mounted rows, no confirmed read-back/export/pagination; actual denial endpoint writes separate buffer. | AUD-035-003, AUD-035-011 |
| T039 | [X] | PARTIAL | [Risk matrix](../../apps/web/src/app/workspaces/[personaId]/_panels/risk-matrix.tsx#L54) shows one static bridge profile; no alternatives, live updates, recommendation or destination queues. | AUD-035-008 |
| T040 | [X] | PARTIAL | [queue-store.ts](../../apps/web/src/lib/offline/queue-store.ts#L137) has IndexedDB/AES/config; worker is no-op, cap global, displacement/drain destructive, no producer caller. | AUD-035-004 |
| T041 | [X] | PARTIAL | [Field panel](../../apps/web/src/app/workspaces/[personaId]/_panels/field-coordinator-offline.tsx#L90) shows depth/browser offline and manual original-route replay, not GPS capture/heartbeat/dedicated acknowledged drain. | AUD-035-004 |
| T042 | [X] | PARTIAL | [Planning panel](../../apps/web/src/app/workspaces/[personaId]/_panels/planning-iap-composer.tsx#L34) requests a read-only bridge draft; no editable forecast, provenance, contradiction or IC handoff. | AUD-035-009 |
| T043 | [X] | PARTIAL | [Span component](../../apps/web/src/app/workspaces/[personaId]/_panels/span-of-control-warning.tsx#L23) has threshold branch but empty mounted data, optional delegation and no save boundary/tier-complete guard. | AUD-035-010 |
| T044 | [X] | PARTIAL | [Handover panel](../../apps/web/src/app/workspaces/[personaId]/_panels/resilience-handover-pdf.tsx#L14) expects wrong success fields and lost error detail; mounted payload incomplete, download not valid. | AUD-035-007 |
| T045 | [X] | PARTIAL | [Service](../../apps/api/app/services/recovery_handover_service.py#L189) validates ratio but uses PDF/signature/blob stubs, optional audit, invented snapshot freshness and no real cert binding. | AUD-035-007 |
| T046 | [X] | PARTIAL | [MSAL helper](../../apps/web/src/lib/auth/entra-msal.ts#L76) and [mask banner](../../apps/web/src/lib/classifier/banner.tsx#L30) exist; no helper callers, bearer attachment or actual source/audit navigation. | AUD-035-014, AUD-035-015, AUD-035-016 |
| T047 | [ ] | UNVERIFIED | [Staging operational gate](tasks.md#L323) has no current run/coverage proof; stored run is skipped-only and wrong revision. | AUD-035-021 |
| T048 | [ ] | MISSING | [Sector baseline obligation](tasks.md#L340) has no inventory file or replacement in local test/artifact search. | AUD-035-021 |
| T049 | [X] | CONFLICT | [Cultural test](../../apps/api/tests/contract/spec_035/test_cultural_safety.py#L67) requires Watch and Act override rejection, opposite the amended task and Q5. | AUD-035-006, AUD-035-020 |
| T050 | [X] | PARTIAL | [Language registry](../../apps/web/src/lib/i18n/language-packs.ts#L151) and [panel](../../apps/web/src/components/cultural-safety/index.tsx#L122) provide source-level fallback/controls; no real routing/source labelling/audited variants. | AUD-035-006 |
| T051 | [X] | PARTIAL | [Overlay](../../apps/web/src/components/infrastructure-overlay/index.tsx#L32) lists four categories with toggles; no GeoJSON, geometry, boundaries or real priority data. Test asserts toggles only. | AUD-035-012 |
| T052 | [X] | PARTIAL | [Claims dashboard](../../apps/web/src/components/claims-velocity/index.tsx#L43) displays/sorts props; production view uses zero placeholder, no source snapshot identity or funding action, sort ARIA on button. | AUD-035-013, AUD-035-021 |
| T053 | [X] | PARTIAL | [Cultural service](../../apps/api/app/services/cultural_safety_service.py#L105) returns pure decisions; no installed Service Bus/timer/persistence driver, no elder-approve implementation or published/suppressed language audit. | AUD-035-006 |
| T054 | [X] | PARTIAL | [SAPOL page](../../apps/web/src/app/(operations)/sectors/sapol-control-centre/page.tsx#L20) combines empty generic panels; no multi-LGA delegation or operator/approver/publisher enforcement. | AUD-035-012 |
| T055 | [X] | PARTIAL | [SES-SA page](../../apps/web/src/app/(operations)/sectors/ses-sa-multi-lga/page.tsx#L20) combines offline/IAP/approval shells; no convoy/shelter/air-bridge transition. | AUD-035-004, AUD-035-012 |
| T056 | [X] | PARTIAL | [WA](../../apps/web/src/app/(operations)/sectors/dfes-wa-cultural-safety/page.tsx#L20), [TAS](../../apps/web/src/app/(operations)/sectors/taspol-multilingual/page.tsx#L20), [NT](../../apps/web/src/app/(operations)/sectors/ntes-multilingual/page.tsx#L20) use empty variants/unbound callbacks and default-AU PIO composition. | AUD-035-005, AUD-035-006, AUD-035-012 |
| T057 | [X] | PARTIAL | [Iron-ore](../../apps/web/src/app/(operations)/sectors/dfes-wa-iron-ore/page.tsx#L20), [island](../../apps/web/src/app/(operations)/sectors/at-tas-island-isolation/page.tsx#L20) select cosmetic overlays; no actual geography/prioritisation/ferry-medical handoff. | AUD-035-012 |
| T058 | [X] | PARTIAL | [AFP](../../apps/web/src/app/(operations)/sectors/afp-act-precinct/page.tsx#L20), [ACT declaration](../../apps/web/src/app/(operations)/sectors/ses-act-declaration/page.tsx#L20) lack federal/territory geometry and cross-identity transition/declaration. | AUD-035-012 |
| T059 | [X] | PARTIAL | [SJA](../../apps/web/src/app/(operations)/sectors/sja-nt-tropical/page.tsx#L15), [BoM](../../apps/web/src/app/(operations)/sectors/bom-broadcast-relay/page.tsx#L38), [NEMA](../../apps/web/src/app/(operations)/sectors/nema-dacc-jatwc/page.tsx#L20) lack disease/logistics, persisted relay and DACC lifecycle. | AUD-035-004, AUD-035-005, AUD-035-012 |
| T060 | [X] | PARTIAL | [Utility page](../../apps/web/src/app/(operations)/sectors/utility-insurance-recovery/page.tsx#L11) uses a zero snapshot and incomplete handover payload; no Built/Economic funding transition/evidence. | AUD-035-007, AUD-035-013 |
| T061 | [ ] | UNVERIFIED | [Sector staging run](tasks.md#L407) has no current result; all 13 test sources use evaluator proxies rather than required UI actions. | AUD-035-012, AUD-035-021 |
| T062 | [ ] | MISSING | [Recovery integration obligation](tasks.md#L424) has no authored test or equivalent interaction assertions in bounded app test search. Proposed home is identified in AUD-035-013. | AUD-035-013, AUD-035-021 |
| T063 | [X] | PARTIAL | [Recovery route](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L61) uses an existing read-only tracker and new labels; missing claims/ratio handlers and editable four-environment flow. | AUD-035-013 |
| T064 | [X] | PARTIAL | [Subdomain labels](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L206) and claims display exist; no named data-slice actions, funding delta or two-environment trace. | AUD-035-013 |
| T065 | [X] | PARTIAL | [Ratio threshold](../../apps/api/app/services/recovery_handover_service.py#L76) exists, but panel cannot consume full contract/detail; [.10 test](../../apps/api/tests/contract/spec_035/test_recovery_handover.py#L76) does not cover exact .29/.30 boundary and UI. | AUD-035-007, AUD-035-013 |
| T066 | [ ] | UNVERIFIED | [Recovery staging run](tasks.md#L446) and SAS timing not evidenced; current default URL is intentionally invalid. | AUD-035-007, AUD-035-021 |
| T067 | [X] | MISSING | Embedded amendment claims a jsdom replacement at [tasks.md](tasks.md#L463), but neither that test nor original E2E home exists in bounded tests. Fixed banner labels are not replacement test evidence. | AUD-035-016, AUD-035-021 |
| T068 | [X] | SUPERSEDED | Explicit [task decision](tasks.md#L468) transfers coverage to the existing [axe test](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts#L14) and artifact ownership to T077. Successor still scans only three landings, not all P1 surfaces. | AUD-035-021 |
| T069 | [X] | PARTIAL | Local fixed residency labels exist, but [root layout](../../apps/web/src/app/layout.tsx#L27) and [shared shell](../../packages/ui/src/components/layout/app-shell.tsx#L16) lack a global banner/registry badge/link. | AUD-035-016 |
| T070 | [X] | PARTIAL | Explicit file-backed deferral accepted: [task amendment](tasks.md#L480), [repository](../../apps/api/app/repositories/carveout_registry_repository.py#L49). API unsigned/unpaginated, accepts empty approvers; no runtime UI consumer. | AUD-035-016 |
| T071 | [X] | PARTIAL | [Workflow](../../.github/workflows/foundry-carveout-review.yml#L3) has a 90-day check but is manual-only; no demonstrated PR gate/staging negative run. Entries are statically overdue. | AUD-035-016, AUD-035-021 |
| T072 | [X] | PARTIAL | [Operations layout](../../apps/web/src/app/(operations)/layout.tsx#L18) registers a no-op worker; canonical workspaces lie outside it and persona payload has no field/remote conditional. | AUD-035-004, AUD-035-012 |
| T073 | [X] | PARTIAL | [PIO picker](../../apps/web/src/app/workspaces/[personaId]/_panels/pio-aws-composer.tsx#L164) offers Chinese and registry languages; no all-route picker or true translated/public fallback chain. | AUD-035-005, AUD-035-006, AUD-035-016 |
| T074 | [ ] | PARTIAL | Existing [axe test](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts#L14) and [config](../../apps/web/playwright.config.cts#L68) exist, but three-route scope, unmatched `@a11y` grep and absent hardening/report results remain. | AUD-035-021 |
| T075 | [ ] | UNVERIFIED | [Cross-cutting staging obligation](tasks.md#L505) has no current three-jurisdiction outcome/a11y/offline evidence. | AUD-035-021 |
| T076 | [ ] | UNVERIFIED | [Matrix run obligation](tasks.md#L516) lacks execution/required-check evidence; existing script checks unrelated flags. | AUD-035-018, AUD-035-021 |
| T077 | [ ] | UNVERIFIED | [Full production gate](tasks.md#L521) unsupported by empty partial trace, skipped run, wrong SHA, placeholder parent trace and absent a11y summary. | AUD-035-021 |
| T078 | [X] | PARTIAL | [OTEL helper](../../apps/api/app/observability/audit_span.py#L20) is invoked by pure cultural decisions only, not every new audit path; no staging query evidence. Web enrichment explicitly deferred. | AUD-035-003, AUD-035-021 |
| T079 | [X] | PARTIAL | [Mermaid document](../../docs/architecture/spec-035-middleware-and-offline.md#L23) exists under explicit amendment, but misstates installed order/drivers and lacks requested draw.io images/overview evidence. | AUD-035-020 |
| T080 | [X] | PARTIAL | [Changelog entry](../../CHANGELOG.md#L80) lists nine panels/thirteen pages, but not a supported one-line entry per FR and includes false-completeness claims. | AUD-035-020 |
| T081 | [ ] | UNVERIFIED | [Dry-run obligation](tasks.md#L541) has no current staging evidence; quickstart modes/payloads/SC matrix contradict the source. | AUD-035-020, AUD-035-021 |

## Functional Requirement Coverage

Every original FR is separate. References to the parent evaluator's SC IDs are distinct from this specification's
12 closure SCs; for example parent `sc-005` measures economic loss, while local SC-005 measures warning publication.

| Requirement | Status | Evidence and full-obligation assessment | Follow-up |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | [Obligation](spec.md#L161); [mounted card](../../apps/web/src/components/workspaces/persona-workspace.tsx#L64) has immutable props, empty sources, task-derived endpoint and no durable action. Operations/logistics approval panels, field validation, authorised transitions and post-state selector/evaluator binding incomplete. | AUD-035-001, AUD-035-002, AUD-035-014 |
| FR-002 | PARTIAL | [Obligation](spec.md#L162); [composer](../../apps/web/src/app/workspaces/[personaId]/_panels/pio-aws-composer.tsx#L56) has inputs/language picker but display levels, English-only default, labelled English variants, ungated incomplete scan, no IC callback/publish/public read-back. Sector reuse does not supply jurisdiction/state. | AUD-035-005, AUD-035-006, AUD-035-014, AUD-035-021 |
| FR-003 | PARTIAL | [Obligation](spec.md#L163); [observer](../../apps/web/src/app/workspaces/[personaId]/_panels/observer-auditor-timeline.tsx#L32) declares append-only but loads no rows, ignores denial response, never reads original bytes or exports. [Denial route](../../apps/api/app/api/routes/audit.py#L43) is a separate unauthenticated buffer. | AUD-035-003, AUD-035-011 |
| FR-004 | PARTIAL | [Obligation](spec.md#L164); [risk panel](../../apps/web/src/app/workspaces/[personaId]/_panels/risk-matrix.tsx#L54) shows one keyword-based profile, not live alternative routes; no evacuation recommendation or IC/Planning queue chain. | AUD-035-008 |
| FR-005 | PARTIAL | [Obligation](spec.md#L165); [planning panel](../../apps/web/src/app/workspaces/[personaId]/_panels/planning-iap-composer.tsx#L71) is read-only, without source pills/contradictions/edits/destination IC or persisted handoff. | AUD-035-009 |
| FR-006 | PARTIAL | [Obligation](spec.md#L166); [worker](../../apps/web/public/offline-sw.js#L8), [store](../../apps/web/src/lib/offline/queue-store.ts#L182), [replay](../../apps/api/app/api/routes/offline_replay.py#L102) do not deliver capture/GPS/heartbeat/500-per-persona/side-buffer/reserved count/ack drain/metadata/domain effect/durable dedupe/auth exemption. Native IDB and helper ordering exist. | AUD-035-004, AUD-035-017 |
| FR-007 | PARTIAL | [Obligation](spec.md#L167); [signer](../../apps/api/app/services/recovery_handover_service.py#L115) validates some fields but emits invalid PDF-like stub, marker signature and nonexistent download with optional audit. Canonical signed content/hash/identity/time/immutable refetch absent. | AUD-035-007, AUD-035-019 |
| FR-008 | PARTIAL | [Obligation](spec.md#L168); [span branch](../../apps/web/src/app/workspaces/[personaId]/_panels/span-of-control-warning.tsx#L23) exists but real hierarchy, before-save control, all Tier-N/A negatives, delegation and breach audit are disconnected. | AUD-035-010 |
| FR-009 | PARTIAL | [Obligation](spec.md#L172); [router](../../apps/api/app/api/router.py#L157) exposes the same canonical handlers behind a flag, but store/identity/error ladder, per-call audit and body compatibility are incomplete. Parent shapes are implemented only in the local evaluator branch. | AUD-035-001, AUD-035-003, AUD-035-018, AUD-035-022 |
| FR-010 | PARTIAL | [Obligation](spec.md#L173); [JWT validation](../../apps/api/app/middleware/entra_auth.py#L85) exists, but fixture principal bypass, exact-role/claim gaps, 403 missing-persona response and overwritten request claims violate the production guarantee. | AUD-035-002, AUD-035-014 |
| FR-011 | PARTIAL | [Obligation](spec.md#L174); [registry](../../apps/api/app/auth/rbac_registry.py#L20) defines 11 roles and seed has 68 functions. [Enforcement](../../apps/api/app/middleware/rbac_check.py#L125) permits unknown persona/admin target without checks; paired emission lacks verified identity, shared read and mandatory atomicity. | AUD-035-002, AUD-035-003 |
| FR-012 | PARTIAL | [Obligation](spec.md#L175); [policy](../../infra/modules/apim-rate-limit.bicep#L96) contains nominal budgets but no trusted claim binding/global semantics/exemptions; [middleware](../../apps/api/app/middleware/rate_limit_audit.py#L37) cannot audit upstream rejections as designed. | AUD-035-017, AUD-035-019 |
| FR-013 | PARTIAL | [Obligation](spec.md#L176); [appender](../../apps/api/app/middleware/audit_appender.py#L90) omits GETs, writes after response, loses failure guarantees/fields; [mutex](../../apps/api/app/middleware/activation_mutex.py#L71) and CI inspect wrong flags. Startup postmortem visibility absent. | AUD-035-003, AUD-035-018, AUD-035-022 |
| FR-014 | PARTIAL | [Obligation](spec.md#L180); [SAPOL shell](../../apps/web/src/app/(operations)/sectors/sapol-control-centre/page.tsx#L20) has no delegation across two LGAs, publisher/approver/operator separation or persisted authority; eastern analogue endorsement not evidenced. | AUD-035-002, AUD-035-012 |
| FR-015 | PARTIAL | [Obligation](spec.md#L181); [SES-SA shell](../../apps/web/src/app/(operations)/sectors/ses-sa-multi-lga/page.tsx#L20) lacks convoy staging, inter-LGA shelter routing, air bridge and working offline-first delayed sync. | AUD-035-004, AUD-035-012 |
| FR-016 | CONFLICT | [Obligation](spec.md#L182) permits both Watch and Act/Emergency timeout override; [service](../../apps/api/app/services/cultural_safety_service.py#L55) and contract permit only Emergency. No real elder approval/deadline/notification/publish driver or complete language/identity audit. | AUD-035-005, AUD-035-006, AUD-035-020 |
| FR-017 | PARTIAL | [Obligation](spec.md#L183); [overlay](../../apps/web/src/components/infrastructure-overlay/index.tsx#L86) lists categories, not geometry/status/priorities. WA mutual aid/private redaction/recovery link and TAS ferry/air/rescue-to-care workflow absent from the mounted compositions. | AUD-035-012 |
| FR-018 | PARTIAL | [Obligation](spec.md#L184); [AFP](../../apps/web/src/app/(operations)/sectors/afp-act-precinct/page.tsx#L20) and [SES-ACT](../../apps/web/src/app/(operations)/sectors/ses-act-declaration/page.tsx#L20) have no precinct boundaries or differentiated declaration/cross-identity transition. | AUD-035-012 |
| FR-019 | PARTIAL | [Obligation](spec.md#L185); [SJA-NT page](../../apps/web/src/app/(operations)/sectors/sja-nt-tropical/page.tsx#L15) offers generic cyclone risk/offline panels, not mosquito/Strongyloides/melioidosis, RFDS or store-forward telemedicine. | AUD-035-004, AUD-035-012 |
| FR-020 | PARTIAL | [Obligation](spec.md#L186); [BoM](../../apps/web/src/app/(operations)/sectors/bom-broadcast-relay/page.tsx#L23) neither consumes a published warning nor records ABC/SBS source. Ack only toggles local state; scripts are draft previews. | AUD-035-005, AUD-035-012 |
| FR-021 | PARTIAL | [Obligation](spec.md#L187); [NEMA](../../apps/web/src/app/(operations)/sectors/nema-dacc-jatwc/page.tsx#L20) lacks request/approve/deploy/withdraw/after-action and BoM-to-SES/NEMA handoff. Profile has only Commonwealth tag, not required state/territory reach. | AUD-035-012, AUD-035-021 |
| FR-022 | PARTIAL | [Obligation](spec.md#L188); [utility](../../apps/web/src/app/(operations)/sectors/utility-insurance-recovery/page.tsx#L11) renders zero claims and incomplete export payload, with no ICA/state funding transfer or Built/Economic persisted evidence. | AUD-035-007, AUD-035-013 |
| FR-023 | PARTIAL | [Obligation](spec.md#L192); [dashboard](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L61) reuses recovery reads, but claims/loss URLs are not implemented and incident selection does not refresh those data. Current four-environment/ratio completeness not established. | AUD-035-013 |
| FR-024 | PARTIAL | [Obligation](spec.md#L193); [six labels](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L206) are not data-backed housing/rebuild/grant/supply-chain/tourism actions; [existing indicator API](../../apps/api/app/api/routes/recovery.py#L59) is not wired to them. | AUD-035-013 |
| FR-025 | PARTIAL | [Obligation](spec.md#L197); fixed labels exist on some routes, but [common shell](../../packages/ui/src/components/layout/app-shell.tsx#L16) lacks residency/registry, recommendation-source label and render audit. | AUD-035-015, AUD-035-016 |
| FR-026 | PARTIAL | [Obligation](spec.md#L198); [repository](../../apps/api/app/repositories/carveout_registry_repository.py#L49) computes stale flags but accepts empty approvals; five [records](../../data/governance/foundry_carveout_registry.json#L1) overdue, UI warning/GAP emission absent. | AUD-035-016 |
| FR-027 | PARTIAL | [Obligation](spec.md#L199); [middleware](../../apps/api/app/middleware/classifier_gateway.py#L102) lacks complete branches/metadata and does not own model egress; relocated [Foundry gateway call](../../apps/agents/common/foundry_chat_client.py#L367) has fail-open cases and no Q6 timeline/UI linkage. | AUD-035-015, AUD-035-003 |
| FR-028 | PARTIAL | [Obligation](spec.md#L200); [axe test](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts#L14) covers three landings only. Static issues include `aria-sort` on a button and nested main landmarks; no current clean scan, all-route gap emission or manual review proof. | AUD-035-021 |
| FR-029 | PARTIAL | [Obligation](spec.md#L201); [registry](../../apps/web/src/lib/i18n/language-packs.ts#L35) has Chinese/ATSI names and reviewer fallback, but [draft bridge](../../apps/api/app/api/routes/agents.py#L181) labels English as variants; missing source-labelled public fallback and universal language picker. | AUD-035-005, AUD-035-006, AUD-035-016 |
| FR-030 | CONFLICT | [Obligation](spec.md#L205) demands unchanged suite and positive production auth-error assertions; [fixture](../../tests/e2e/web-coverage/_support/fixtures/persona.fixture.ts#L40) requires test-support, [config](../../apps/web/playwright.config.cts#L18) starts local services, tests use canned metrics. Explicit owner/scope resolution needed. | AUD-035-020, AUD-035-021, AUD-035-022 |

## Success Criteria Coverage

All 12 SC outcomes are UNVERIFIED at reviewed HEAD. The source blockers are specified, but no static review can certify
production runs, latency, WCAG conformance, deployed residency, human approvals or cryptographic artifact availability.

| Criterion | Status | Required outcome and evidence assessment | Follow-up |
| --- | --- | --- | --- |
| SC-001 | UNVERIFIED | [>=95% production tuples](spec.md#L226): [partial trace](../../tests/e2e/web-coverage/_artifacts/coverage-trace.partial-1.json#L1) has zero rows; parent final trace is placeholder; no current final JSON. | AUD-035-021 |
| SC-002 | UNVERIFIED | [Zero Open HIGH+ and <=3 iterations](spec.md#L227): [gap JSON](../034-webapp-capstone-coverage/gap-register.json#L1) has one old closed, severity-less record, not a complete current inventory. | AUD-035-021 |
| SC-003 | UNVERIFIED | [All retired bails pass production](spec.md#L228): [persona test](../../tests/e2e/web-coverage/operational/incident-commander.approve-cross-agency-action.spec.ts#L44) uses canned metrics; historical run is skipped-only and fixture requires test-support. | AUD-035-021 |
| SC-004 | UNVERIFIED | [13 sector depth transitions](spec.md#L229): authored pages and tests exist but [SAPOL assertion](../../tests/e2e/web-coverage/sectors/sa/sapol.state-control-centre-rbac.spec.ts#L38) illustrates no sector UI action. All 13 individually accounted below. | AUD-035-012, AUD-035-021 |
| SC-005 | UNVERIFIED | [Emergency warning approval/community render <=2 min](spec.md#L230): [PIO callback](../../apps/web/src/app/workspaces/[personaId]/_panels/pio-aws-composer.tsx#L113) does not publish; no public read-back/timing trace. | AUD-035-005, AUD-035-006, AUD-035-021 |
| SC-006 | UNVERIFIED | [Signal-to-action <=5/15/30 min](spec.md#L231): [evaluator](../../apps/api/app/services/outcome_evaluator_service.py#L138) grades supplied values, not persisted signal/action timestamps across real UI transitions. | AUD-035-001, AUD-035-008, AUD-035-009, AUD-035-021 |
| SC-007 | UNVERIFIED | [Tiered 30s/50 and 5min/500 replay](spec.md#L232): [drain](../../apps/web/src/lib/offline/queue-store.ts#L222) deletes before ack; no real capture/server effect/overflow metadata or timing artifact. | AUD-035-004, AUD-035-021 |
| SC-008 | UNVERIFIED | [Four editable environments/signed artifact/ratio >=.30](spec.md#L233): [dashboard](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L206) is labels/read-only data and [signer](../../apps/api/app/services/recovery_handover_service.py#L189) is stubbed. | AUD-035-007, AUD-035-013, AUD-035-021 |
| SC-009 | UNVERIFIED | [100% production auth/RBAC/audit <=2s](spec.md#L234): [auth bypass](../../apps/api/app/middleware/entra_auth.py#L162), [GET omission](../../apps/api/app/middleware/audit_appender.py#L90) and disconnected reader defeat the guarantee. | AUD-035-002, AUD-035-003, AUD-035-014, AUD-035-017, AUD-035-021 |
| SC-010 | UNVERIFIED | [Every P1 surface WCAG 2.2 AA](spec.md#L235): [three-route scan source](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts#L14) is not comprehensive; no fresh results or human accessibility review. | AUD-035-021 |
| SC-011 | UNVERIFIED | [Residency banners/fresh registry/PSPF-PII gating](spec.md#L236): [stale registry](../../data/governance/foundry_carveout_registry.json#L1), missing global consumer and [fail-open egress](../../apps/agents/common/foundry_chat_client.py#L373). No cloud/resource data-transit verification. | AUD-035-015, AUD-035-016, AUD-035-019, AUD-035-021 |
| SC-012 | UNVERIFIED | [111-spec production suite <=45 min + JUnit/JSON](spec.md#L237): [CI timeout](../../.github/workflows/ci.yml#L267) is a limit, not a measurement. Local config/fixture, artifact-glob mismatch and old 76-skipped run do not prove it. | AUD-035-021 |

## Acceptance Scenario Coverage

USx-Ay labels are review-local references to the original numbered scenarios, not invented specification IDs.

| Scenario | Status | Expected versus observed evidence | Follow-up |
| --- | --- | --- | --- |
| US1-A1 | PARTIAL | [IC rationale/source/confidence approval](spec.md#L60): [card submit](../../apps/web/src/app/workspaces/[personaId]/_panels/ic-approval-card.tsx#L52) has wrong body, no editable fields or persisted action/refetch; no COP/two-second proof. | AUD-035-001, AUD-035-003, AUD-035-014 |
| US1-A2 | PARTIAL | [QLD warning draft/scan/IC/publish](spec.md#L61): [PIO](../../apps/web/src/app/workspaces/[personaId]/_panels/pio-aws-composer.tsx#L113) stops at optional callback and English-labelled variants; no approval-enforced publication or measured reach. | AUD-035-005, AUD-035-006, AUD-035-021 |
| US1-A3 | PARTIAL | [Four GPS reports/30m outage/order/dedupe/banner](spec.md#L62): [field panel](../../apps/web/src/app/workspaces/[personaId]/_panels/field-coordinator-offline.tsx#L90) has no capture/heartbeat, drains destructively and hides banner before ack. | AUD-035-004 |
| US1-A4 | PARTIAL | [Tamper denial/byte-identical read/export hash](spec.md#L63): [observer](../../apps/web/src/app/workspaces/[personaId]/_panels/observer-auditor-timeline.tsx#L32) declares denial without data/readback/export; API appends to separate buffer. | AUD-035-003, AUD-035-011 |
| US1-A5 | PARTIAL | [Seventh-to-eighth report warning/delegate and Planning negative](spec.md#L64): [isolated tests](../../apps/web/tests/unit/spec_035/operator-panels.test.tsx#L46) only render nine-report props; canonical data is always empty. | AUD-035-010 |
| US2-A1 | PARTIAL | [Real Entra evaluation and <=2s read](spec.md#L78): [production test](../../apps/api/tests/contract/spec_035/test_production_reach.py#L41) accepts any non-404, bypasses JWT and supplies invalid body; local evaluator shape exists. | AUD-035-002, AUD-035-003, AUD-035-022 |
| US2-A2 | PARTIAL | [Same tuple same verdict/ID no new row](spec.md#L79): [local idempotency](../../apps/api/app/services/outcome_evaluator_service.py#L241) exists, but independent middleware always appends and process restart loses state. | AUD-035-003 |
| US2-A3 | PARTIAL | [401/403 denial with no compute](spec.md#L80): [auth/RBAC](../../apps/api/app/middleware/rbac_check.py#L94) has basic rejection but bypass, unresolved persona and claim error mismatch; denial timeline not readable. | AUD-035-002, AUD-035-003, AUD-035-022 |
| US2-A4 | PARTIAL | [Real exceeded bucket 429/retry/audit](spec.md#L81): [rate middleware](../../apps/api/app/middleware/rate_limit_audit.py#L37) converts post-handler header, not actual budget exhaustion. | AUD-035-017 |
| US2-A5 | CONFLICT | [sc-006 to sc-011 400 regardless of bearer](spec.md#L82): [service check](../../apps/api/app/services/outcome_evaluator_service.py#L194) runs after auth/schema; enum-only tests miss precedence. | AUD-035-022 |
| US2-A6 | PARTIAL | [CI dual guard with production path inert](spec.md#L83): [guard](../../apps/api/app/middleware/test_support_guard.py#L31) exists, but production flag still installs middleware and wrong mutex cannot reject co-activation. | AUD-035-018 |
| US3-A1 | CONFLICT | [SA-control-centre role/two LGAs/pre-call denial](spec.md#L97): named AppRole is outside Q1's 11; [SAPOL](../../apps/web/src/app/(operations)/sectors/sapol-control-centre/page.tsx#L20) has no role-separated delegation or movement. | AUD-035-002, AUD-035-012, AUD-035-020 |
| US3-A2 | PARTIAL | [Kimberley elder approval/source/fallback](spec.md#L98): [WA page](../../apps/web/src/app/(operations)/sectors/dfes-wa-cultural-safety/page.tsx#L20) uses empty variants/unbound elder callback; no signed approval or actual translation. | AUD-035-005, AUD-035-006, AUD-035-012 |
| US3-A3 | PARTIAL | [AFP precinct/territory/cross-identity command](spec.md#L99): [AFP page](../../apps/web/src/app/(operations)/sectors/afp-act-precinct/page.tsx#L20) only selects a list toggle, with fixed IC identity. | AUD-035-012 |
| US3-A4 | PARTIAL | [Published AWS/ABC-SBS script/ack completion](spec.md#L100): [BoM ack](../../apps/web/src/app/(operations)/sectors/bom-broadcast-relay/page.tsx#L38) only changes React boolean; no source consumption or persisted acknowledgement. | AUD-035-005, AUD-035-012 |
| US3-A5 | PARTIAL | [ICA claims/signed immutable handoff/two recovery rows](spec.md#L101): [utility](../../apps/web/src/app/(operations)/sectors/utility-insurance-recovery/page.tsx#L11) passes zero snapshot and incomplete sign payload. | AUD-035-007, AUD-035-013 |
| US4-A1 | PARTIAL | [Four current environments/economic losses/ratio](spec.md#L115): [dashboard](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L76) calls missing unscoped reads and keeps placeholders; existing tracker not editable through new surfaces. | AUD-035-013 |
| US4-A2 | PARTIAL | [Single signed PDF with full content/hash/identity](spec.md#L116): [renderer/signing](../../apps/api/app/services/recovery_handover_service.py#L115) produce markers, not full readable signed content; download contract mismatched. | AUD-035-007 |
| US4-A3 | PARTIAL | [ICA state funding updates Economic/Built and tuple](spec.md#L117): [claims table](../../apps/web/src/components/claims-velocity/index.tsx#L43) only displays/sorts, no funding transition. | AUD-035-013 |
| US5-A1 | PARTIAL | [Every regulated route/source badge/render audit](spec.md#L131): [shell](../../packages/ui/src/components/layout/app-shell.tsx#L16) has no global registry/badge; isolated AU labels do not meet the requirement. | AUD-035-015, AUD-035-016 |
| US5-A2 | PARTIAL | [PSPF/PII denied/masked before non-AU with audit](spec.md#L132): relocated [egress gateway](../../apps/agents/common/foundry_chat_client.py#L367) protects some user strings, but failure/unknown-region paths and Q6 metadata remain incomplete. | AUD-035-015 |
| US5-A3 | UNVERIFIED | [All P1 surfaces automated WCAG checks](spec.md#L133): [axe source](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts#L14) scans only three landings; no current execution or manual keyboard/focus proof. | AUD-035-021 |
| US5-A4 | PARTIAL | [CALD variant-first/English fallback/source label](spec.md#L134): [resolver](../../apps/web/src/lib/i18n/language-packs.ts#L157) supports fallback, but actual draft is English and no complete source-labelled public rendering. | AUD-035-005, AUD-035-006 |
| US5-A5 | PARTIAL | [NT telemedicine intermittent GPS replay metadata](spec.md#L135): [SJA composition](../../apps/web/src/app/(operations)/sectors/sja-nt-tropical/page.tsx#L20) has no telemedicine/GPS action and reuses incomplete offline panel. | AUD-035-004, AUD-035-012 |

## Edge Case Coverage

E01-E15 are review labels for the original unnumbered edge bullets, in source order.

| Edge | Status | Source and assessment | Follow-up |
| --- | --- | --- | --- |
| E01 | PARTIAL | [Untailored persona](spec.md#L139): canonical route loads generic tasks, no depth transition/GAP-WORKSPACE-MISSING emission; [role switch](../../apps/web/src/components/workspaces/persona-workspace.tsx#L64) omits sector IDs. | AUD-035-012, AUD-035-021 |
| E02 | PARTIAL | [Missing/mismatched AppRole](spec.md#L140): [RBAC](../../apps/api/app/middleware/rbac_check.py#L94) rejects some claims but unknown persona passes and denial audit/read-back incomplete. | AUD-035-002, AUD-035-003 |
| E03 | CONFLICT | [Production/test-support coactivation](spec.md#L141): [mutex](../../apps/api/app/middleware/activation_mutex.py#L71) checks different flags; CI no correct matrix. | AUD-035-018 |
| E04 | PARTIAL | [Cross-cycle idempotency](spec.md#L142): [local ledger](../../apps/api/app/services/outcome_evaluator_service.py#L241) has fresh-ID/current/all semantics in one process, not durable multi-worker history. | AUD-035-003 |
| E05 | PARTIAL | [Sector command tier versus Tier-N/A](spec.md#L143): [span check](../../apps/web/src/app/workspaces/[personaId]/_panels/span-of-control-warning.tsx#L23) only excludes Planning and has no real hierarchy. | AUD-035-010, AUD-035-012 |
| E06 | CONFLICT | [No elder identity/AWS-level timeout](spec.md#L144): [policy](../../apps/api/app/services/cultural_safety_service.py#L55) disagrees on Watch and Act; no notification or language suppression/publication driver. | AUD-035-006, AUD-035-020 |
| E07 | PARTIAL | [Unavailable variant/fallback badge/audit](spec.md#L145): [resolver](../../apps/web/src/lib/i18n/language-packs.ts#L157) falls back but no hazard-aware missing badge or fallback audit. | AUD-035-005, AUD-035-006 |
| E08 | CONFLICT | [Overflow oldest preservation/newest rejection/priority](spec.md#L146): [store](../../apps/web/src/lib/offline/queue-store.ts#L182) deletes displaced entries, has no side buffer and contradicts unconditional life-safety admission at full life-safety cap. | AUD-035-004, AUD-035-020 |
| E09 | PARTIAL | [Signing TTL blocks/rotation runbook/no unsigned output](spec.md#L147): [expiry check](../../apps/api/app/services/recovery_handover_service.py#L189) only uses optional injected time; actual certificate absent, error detail dropped and default signing stub remains. | AUD-035-007, AUD-035-019 |
| E10 | PARTIAL | [First-party banner despite extension](spec.md#L148): fixed labels are first-party but absent on deep workspace/root; [shell](../../packages/ui/src/components/layout/app-shell.tsx#L16) has no common banner. No claim of absolute resistance to user extensions. | AUD-035-016, AUD-035-021 |
| E11 | PARTIAL | [Registry >90d warning/GAP](spec.md#L149): all [five records](../../data/governance/foundry_carveout_registry.json#L1) overdue; repository flag not consumed in UI or tested by actual registry assertion. | AUD-035-016, AUD-035-021 |
| E12 | MISSING | [Concurrent IC 409/first writer/audit](spec.md#L150): no action/version mutation in [approval handler](../../apps/api/app/api/routes/workspace_bridges.py#L69); no connected compare-and-set conflict UX after scoped action/client search. | AUD-035-001 |
| E13 | PARTIAL | [Cycle-all 500 cursor/load-more](spec.md#L151): [reader](../../apps/api/app/services/outcome_evaluator_service.py#L295) paginates local rows, but observer exposes no cursor and no stable durable read window. | AUD-035-003, AUD-035-011 |
| E14 | PARTIAL | [PSPF translation denied/manual fallback](spec.md#L152): shared gateway has some denial, but [PIO draft](../../apps/api/app/api/routes/agents.py#L196) is unclassified English carrier and actual egress failure paths remain open. | AUD-035-005, AUD-035-015 |
| E15 | PARTIAL | [Mining cascade/triage/private redaction](spec.md#L153): [WA overlay page](../../apps/web/src/app/(operations)/sectors/dfes-wa-iron-ore/page.tsx#L20) lacks real assets, mutual-aid actions and authorised-redaction/audit states. | AUD-035-012 |

## Clarifications and Contract Amendments

Q1-Q10 refer to the original clarification order. A later implementation is not treated as a scope decision.

| Clarification | Status | Decision and inspected evidence | Follow-up |
| --- | --- | --- | --- |
| Q1 | PARTIAL | [11 roles/admin not a persona](spec.md#L37) is reflected in both enums and 68 seed records; [RBAC](../../apps/api/app/middleware/rbac_check.py#L65) lacks exact-one-role/unknown-target enforcement. SA-control-centre AppRole wording in US3 is inconsistent. | AUD-035-002, AUD-035-020 |
| Q2 | PARTIAL | [Signed PDF only](spec.md#L38) explicitly replaces the brief's PDF-or-JSON choice; [signer](../../apps/api/app/services/recovery_handover_service.py#L189) is still marker/in-memory default. No machine sidecar is demanded. | AUD-035-007 |
| Q3 | PARTIAL | [10/min, 600/hr and 600/min global](spec.md#L39) appears as parameters, not trusted routed enforcement/admin exemptions: [policy](../../infra/modules/apim-rate-limit.bicep#L96). | AUD-035-017, AUD-035-019 |
| Q4 | PARTIAL | [Native SW/IDB/dedicated replay](spec.md#L40) chosen explicitly, but [worker](../../apps/web/public/offline-sw.js#L8) does not intercept and client replay bypasses endpoint. | AUD-035-004 |
| Q5 | CONFLICT | [Two-level override with en+Chinese](spec.md#L41) conflicts with [contract](contracts/cultural-safety.contract.md#L17), R-010, entity rules, T011, component and tests. Actual routing/publish/notification absent. | AUD-035-006, AUD-035-020 |
| Q6 | PARTIAL | [PSPF deny/PII mask/both deny/failure closed](spec.md#L42) partly implemented; [egress](../../apps/agents/common/foundry_chat_client.py#L373) still bypasses unknown region/import failure. A pre-existing AU-source link could coexist with no post-mask original persistence, but that reference/retention boundary is not defined or implemented. | AUD-035-015, AUD-035-020 |
| Q7 | CONFLICT | [500 per persona/priority/side buffer/SLOs](spec.md#L43) conflicts with all-life-safety rejection in [model](data-model.md#L203); source global cap/destructive drain does not implement either full contract. | AUD-035-004, AUD-035-020 |
| Q8 | CONFLICT | [Actual auth mutex/CI dev exemption/durable failure](spec.md#L44) differs from [installed invariant](../../apps/api/app/middleware/activation_mutex.py#L71) and quickstart co-activation. | AUD-035-018, AUD-035-020 |
| Q9 | PARTIAL | [Explicit header/atomic pair/no gateway bypass](spec.md#L45) has source helpers, but [appender](../../apps/api/app/middleware/audit_appender.py#L198) trusts a raw header, uses overwritten claims and permits sequential fallback/unreadable pairs. | AUD-035-002, AUD-035-003, AUD-035-015 |
| Q10 | CONFLICT | [Additive errors/locked parent shape/precedence](spec.md#L46) conflicts with local `inconclusive` examples and schema-envelope changes; [runtime check](../../apps/api/app/services/outcome_evaluator_service.py#L194) occurs after auth/validation. | AUD-035-020, AUD-035-022 |

### Research Decisions

| Decision | Status | Assessment | Follow-up |
| --- | --- | --- | --- |
| R-001 | PARTIAL | [Single bearer middleware/JWKS/cache](research.md#L13) exists, but not dev/test-inert/exclusive and legacy middleware overwrites claims. Claim issuer settings differ from quickstart. | AUD-035-002, AUD-035-014, AUD-035-018 |
| R-002 | PARTIAL | [APIM-native budgets](research.md#L26) authored; route wiring, trusted key and upstream rejection audit are absent. No scale-out budget proof. | AUD-035-017, AUD-035-019 |
| R-003 | PARTIAL | [Native SW/IDB](research.md#L39) selected over Workbox/localStorage; current SW is no-op, no insertion caller, destructive global queue, wrong replay path. | AUD-035-004 |
| R-004 | MISSING | [OfflineStatusProvider/30s heartbeat/10s response](research.md#L52) has no matching provider/probe in offline source; only browser events and 1.5s IDB-depth polling. | AUD-035-004 |
| R-005 | CONFLICT | [Auth guard/wiring CI and lifespan](research.md#L65) is replaced in code by unrelated simulation flags without explicit decision. | AUD-035-018 |
| R-006 | PARTIAL | [Atomic Cosmos pairs](research.md#L80) method exists but sequential fallback contradicts atomicity; no shared reader or record-ID binding. | AUD-035-003 |
| R-007 | CONFLICT | [Error-only extension/ladder](research.md#L93) declared but constant order does not enforce request order; local contract also changes old error shapes. | AUD-035-022, AUD-035-020 |
| R-008 | PARTIAL | [Structured regulated-data classifier](research.md#L116) reduced to raw regex on a short prefix list; actual shared gateway is not complete fail-closed Q6 evidence. | AUD-035-015 |
| R-009 | PARTIAL | [Real render/Key Vault/immutable Blob](research.md#L133) has stubs rather than selected renderer/signer/storage; claims freshness is invented. | AUD-035-007, AUD-035-019 |
| R-010 | CONFLICT | [Emergency-only English override](research.md#L150) conflicts with Q5's two levels and English+Chinese. No production elder driver exists. | AUD-035-006, AUD-035-020 |
| R-011 | PARTIAL | [Cosmos registry/side panel/CI freshness](research.md#L168) explicitly deferred to file seed by T070; list exists but UI/pagination/signature/approval validation missing. | AUD-035-016 |
| R-012 | PARTIAL | [All-P1 axe integration](research.md#L180) has three-route test source only; `@a11y` project grep does not match those test titles. Full WCAG/timing execution unverified. | AUD-035-021 |

### Entity and Schema Accounting

All 12 local data-model entities are covered; DM numbers follow original headings. Shared schema declarations are not
assumed to validate arbitrary dictionary writes in repositories or API responses.

| Entity | Status | Field, relationship, validation and transition assessment | Follow-up |
| --- | --- | --- | --- |
| DM01 PersonaWorkspace | PARTIAL | [Model](data-model.md#L12) expects function/panels/language/offline from canonical registry/depth; [service](../../apps/api/app/services/persona_workspace_service.py#L14) returns ID-as-role and generic tasks, no capability-driven composition. | AUD-035-012, AUD-035-014 |
| DM02 SafetyCriticalActionCard | CONFLICT | [Model](data-model.md#L31) decimal confidence versus FR-001 enum; actual card lacks required action UUID/transition/evidence inputs and server-resolved approver/persistence. | AUD-035-001, AUD-035-020 |
| DM03 AwsWarningDraft | PARTIAL | [Draft entity](data-model.md#L53) requires durable draft/pending/approved/published/withdrawn plus cultural states; current composer has transient variants only. Cultural validation contradicts Q5. | AUD-035-005, AUD-035-006 |
| DM04 AuditTimelineEntry | PARTIAL | [Schema](data-model.md#L81) requires hash/identity/route/paired immutable data; actual writers use divergent dictionaries/outcomes/stores. UI prohibition on mutation affordances conflicts with explicit tamper-attempt UX, which must not mutate actual records. | AUD-035-003, AUD-035-011, AUD-035-020 |
| DM05 EvaluatorJudgement | CONFLICT | [Entity](data-model.md#L132) says `inconclusive`; [parent contract](../034-webapp-capstone-coverage/contracts/outcome-evaluator.contract.md#L151) says `gap`. Current canonical evaluator matches parent but bridge does not. | AUD-035-020, AUD-035-022 |
| DM06 EntraAppRoleBinding | PARTIAL | [11-role scope entity](data-model.md#L148) has enums, route prefix map and 68 seed functions; unknown persona and admin target authorisation are not enforced. | AUD-035-002 |
| DM07 SystemAdministratorGrant | PARTIAL | [Grant](data-model.md#L163) includes grant/reviewer metadata and per-request impersonation; only role/header handling exists, not a persisted reviewed grant lifecycle. No sticky state was found, but validated target/audit remain missing. | AUD-035-002, AUD-035-003, AUD-035-020 |
| DM08 OfflineQueueEntry | PARTIAL | [Queue fields](data-model.md#L181) require original operator/hash/cipher/position/status/displacement; store omits several, uses `life-safety` versus canonical `life_safety`, global cap and no ack state. | AUD-035-004, AUD-035-022 |
| DM09 CulturalSafetyTemplate | CONFLICT | [Template](data-model.md#L209) includes routing/timeout/fallback registry, but source stores language labels and pure outcomes; policy differs from Q5 and real deadlines/elder identities are absent. | AUD-035-006, AUD-035-020 |
| DM10 RecoveryHandoverArtefact | PARTIAL | [Entity](data-model.md#L237) requires full content, hash/signing/immutable URI; marker renderer stores neither full content nor real signature/blob. | AUD-035-007 |
| DM11 InfrastructureOverlayLayer | PARTIAL | [GeoJSON and lifeline/economic/cultural priority](data-model.md#L259) are absent from [component](../../apps/web/src/components/infrastructure-overlay/index.tsx#L23), which uses labels and P1/P2/P3. | AUD-035-012 |
| DM12 ClaimsVelocitySnapshot | PARTIAL | [Snapshot/event/captured fields](data-model.md#L272) differ from UI props; no real snapshot resolver or funding persistence. Sort/display helper exists, not the underlying data lineage. | AUD-035-007, AUD-035-013 |

### Assumptions

| Original ID | Status | Source and evidence assessment | Follow-up |
| --- | --- | --- | --- |
| ASM-001 | PARTIAL | [Entra/11-role inventory](spec.md#L241) remains in source; admin absent-persona allowance conflicts with FR-010's required claim, and test-principal bypass is not real Entra. | AUD-035-002, AUD-035-020 |
| ASM-002 | PARTIAL | [Additive seed shape](spec.md#L242) is preserved for 68 identities, but proposed claims/precinct/language domain data are not connected; no historical execution proof inferred. | AUD-035-012, AUD-035-013 |
| ASM-003 | IMPLEMENTED | [Depth-only ABC/SBS/AGD/ABCB/BNHCRC/JATWC/JUSF/ICA](spec.md#L243) explicitly rejects new persona inventory. Seed still has 68; capability delivery is partial, not waived. | AUD-035-012 |
| ASM-004 | UNVERIFIED | [AU Foundry availability](spec.md#L244) is not measured. Existing [shared transport](../../apps/agents/common/foundry_chat_client.py#L373) supports non-AU paths under the constitution carve-out; local no-new-non-AU wording needs alignment. | AUD-035-015, AUD-035-019, AUD-035-020 |
| ASM-005 | IMPLEMENTED | [OFFICIAL: Sensitive ceiling/PROTECTED+ deferred](spec.md#L245) is an explicit scope decision. This review requests no higher-classification feature; current boundary enforcement assessed separately. | AUD-035-015 |
| ASM-006 | PARTIAL | [AVM baseline](spec.md#L246) followed for hosts; raw child policy resources and missing production connectivity/identity/consumer settings need reviewed justification and validation. | AUD-035-019 |
| ASM-007 | UNVERIFIED | [Three-cycle escalation/rollback](spec.md#L247) is stated, but old one-entry gap artifact cannot establish current cycles/escalation/rollback outcomes. | AUD-035-021 |
| ASM-008 | PARTIAL | [Shared canonical router/service](spec.md#L248) implemented in [router](../../apps/api/app/api/router.py#L157); shared service remains process-local and does not automatically inherit production safety. | AUD-035-003, AUD-035-022 |
| ASM-009 | UNVERIFIED | [Data-layer append-only assumption](spec.md#L249) cannot be established from write methods/comments; memory fallback/sequential pairs and disconnected reader undermine the claim. No live permissions checked. | AUD-035-003, AUD-035-019 |
| ASM-010 | PARTIAL | [Native SW feasibility](spec.md#L250) supported by authored registration/store code, not by actual offline interception/capture or cross-browser proof. | AUD-035-004, AUD-035-021 |

### Scope Boundaries

IMPLEMENTED in this table means an explicit scope decision was authored and preserved in this review, not all enclosed
features have shipped. Only an explicit decision, not newer code, can supersede an earlier scope proposal.

| Original ID | Status | Source and assessment | Follow-up |
| --- | --- | --- | --- |
| OOS-001 | IMPLEMENTED | [No persona expansion](spec.md#L254); 68-profile/identity inventory preserved. Additional Commonwealth brief request explicitly deferred by ASM-003. | AUD-035-012 |
| OOS-002 | IMPLEMENTED | [Asia-Pacific deferred](spec.md#L255); no APAC features required or introduced by this review. | none |
| OOS-003 | CONFLICT | [Suite/spec generator read-only](spec.md#L256) is respected; FR-030 production-error expectations and T074 configuration extension cannot be delivered by pretending existing tests perform those actions. | AUD-035-020, AUD-035-021 |
| OOS-004 | IMPLEMENTED | [Constitution unchanged](spec.md#L257); no amendment made. Local NN/QG numbering is inaccurate and must not rewrite the constitution by implication. | AUD-035-020 |
| OOS-005 | IMPLEMENTED | [Entra-only IdP](spec.md#L258) explicit; existing MSAL/JWKS stay within it. Test-principal bypass is a defect, not an approved second identity provider. | AUD-035-002, AUD-035-014 |
| OOS-006 | IMPLEMENTED | [Azure-only](spec.md#L259) explicit. `.invalid` signing URL is not a third-party deployment, but also not working Azure storage. | AUD-035-007, AUD-035-019 |
| OOS-007 | PARTIAL | [AVM-first/no raw unless unavailable](spec.md#L260); AVM hosts present, raw child policy resources have no inspected exception decision. No AVM lookup/deployment performed. | AUD-035-019 |
| OOS-008 | IMPLEMENTED | [No PROTECTED+ workflow](spec.md#L261) explicit. Classifier-negative fixtures do not expand this scope. | AUD-035-015 |
| OOS-009 | PARTIAL | [Additive engine/seed/audit changes only](spec.md#L262); seed preserved, but new disconnected audit ledgers cannot stand in for existing durable store. No engine rewrite requested. | AUD-035-003, AUD-035-012 |
| OOS-010 | IMPLEMENTED | [No pixel-perfect visual regression](spec.md#L263); only future behavioural/accessibility checks requested, no browser/screenshot execution in this review. | AUD-035-021 |
| OOS-011 | IMPLEMENTED | [PDF-only/no JSON sidecar or machine ingestion](spec.md#L264) explicit; no sidecar demanded in remediation. Real signed PDF still partial. | AUD-035-007 |

### Unnumbered Requirements and NFRs

There are no original `NFR-*` IDs. U01-U14 below are review-local group labels for unnumbered obligations, not extra
original requirements. Detailed numeric outcomes remain in the individual SC rows.

| Obligation | Status | Source and assessment | Follow-up |
| --- | --- | --- | --- |
| U01 Real UI outcomes, not seed-only echo | PARTIAL | [Overall key requirement](00-overall-brief.md#L7); 90 generated persona tests use canned evaluator values and the panels are mostly non-mutating shells. | AUD-035-001, AUD-035-012, AUD-035-021 |
| U02 End-to-end navigable production and dev/test journeys | PARTIAL | [Acceptance bar](00-overall-brief.md#L21); directory/sector navigation exists, but canonical panels/auth/replay/public routes do not complete the journeys. | AUD-035-012, AUD-035-014, AUD-035-018 |
| U03 Canonical machine identifiers | CONFLICT | [Terminology](spec.md#L18) requires snake_case AWS levels; PIO/bridge use display strings and offline client uses a hyphenated tier. | AUD-035-005, AUD-035-022 |
| U04 TDD and no weakened acceptance | UNVERIFIED | [Task test policy](tasks.md#L6), [plan](plan.md#L12): authored tests exist but no red-before-green evidence; current assertions often do not cover required behaviour. | AUD-035-021 |
| U05 Immutable evidence and human-in-the-loop | PARTIAL | [Plan gates](plan.md#L82), [constitution](../../.specify/memory/constitution.md#L270): signed export and approval paths incomplete; comments/checkmarks are not human approval. | AUD-035-001, AUD-035-003, AUD-035-005, AUD-035-007 |
| U06 AU persistence, privacy and Azure-only resources | UNVERIFIED | [Plan constraints](plan.md#L56) and [constitution](../../.specify/memory/constitution.md#L272) constrain deployment; no cloud state checked, and gateway/read/write fail-open cases remain. | AUD-035-015, AUD-035-019 |
| U07 WCAG keyboard/focus/labels/contrast/announcements | UNVERIFIED | [Technical Q17](technical-brief.md#L43), FR-002/028 and SC-010 require deep-surface coverage; current three-landings axe and invalid sort-ARIA are insufficient. | AUD-035-005, AUD-035-021 |
| U08 Multilingual source, reviewer, fallback and no silent drop | PARTIAL | [Operational PIO](operational-brief.md#L25) asks en plus three community languages; spec minimum is one plus baselines with no explicit rejection of the stricter brief. Registry labels and English carriers do not prove translation or reviewer consent. | AUD-035-005, AUD-035-006, AUD-035-020 |
| U09 Native offline, encrypted device payload and conservative safety | PARTIAL | [Plan/research](research.md#L39), [queue entity](data-model.md#L181): native IDB/AES helper exists but plaintext fallback, global quota, no interceptor/GPS and destructive replay violate the complete design. | AUD-035-004 |
| U10 Evergreen browsers/Safari 16.4 and optional PWA install | UNVERIFIED | [Target platform](plan.md#L12); no cross-browser/offline execution. Installed worker alone is not feasibility/performance proof. | AUD-035-004, AUD-035-021 |
| U11 Audit every call within <=2s versus plan p95 | CONFLICT | FR-013/SC-009 say every call; [plan performance goals](plan.md#L12) use p95. Neither measured; appender skips reads and writes after response. Explicit measurement contract required. | AUD-035-003, AUD-035-020, AUD-035-021 |
| U12 Loss sanity, claims <24h, SAS <=15m and expiry rotation | PARTIAL | [Recovery validation](contracts/recovery-handover.contract.md#L31), T044/T045: finite/populated data and real claims/cert/SAS not enforced by stubs; .29/.30 edge coverage absent. | AUD-035-007 |
| U13 Existing agents/services reused additively | PARTIAL | [Plan structure decision](plan.md#L256) says consume existing agents unchanged; bridges generate fixed text instead of invoking them. Existing warning-chain, task and recovery indicator services were found and credited. | AUD-035-005, AUD-035-008, AUD-035-009, AUD-035-012 |
| U14 Rollout, evidence-gate, chaos and capacity validation | UNVERIFIED | [Technical Q20/Q21/Q25](technical-brief.md#L49), [plan phases](plan.md#L258): no current rollout/chaos/build-size/slot/human proof. Future authorised validation and max-three-cycle escalation remain required. | AUD-035-019, AUD-035-021 |

### Existing Behaviour Retained in the Assessment

The canonical task-status path is a real mutation: [task-status-panel.tsx](../../apps/web/src/components/workspaces/task-status-panel.tsx#L16)
calls [tasks.ts](../../apps/web/src/lib/api/tasks.ts#L3), then [tasks.py](../../apps/api/app/api/routes/tasks.py#L14),
[TaskOrchestrationService](../../apps/api/app/services/task_orchestration_service.py#L17), and
[CoordinationTasksRepository](../../apps/api/app/repositories/coordination_tasks_repository.py#L210).
It sets `in_progress` and checks assignment against a caller-supplied persona; it is not a verified principal-bound
approval/allocation/publish/handover transition. This is credited, not labelled a wholly missing workspace.

The recovery page reads [DashboardAggregationService](../../apps/api/app/services/dashboard_aggregation_service.py#L462)
and [GovernanceDataService](../../apps/api/app/services/governance_data_service.py#L491): four domains plus overarching
are authored, but progress/current values are fixed at zero rather than current incident tracker state. The companion
table and domain-detail navigation exist. The independent incident indicator write API was found, but is not connected
to the six FR-024 subdomain actions. Existing alert/CAP/compliance helpers at
[warning_chain.py](../../apps/api/app/api/routes/warning_chain.py#L27) are also credited as reusable, not as proof that
the PIO composer reaches them.

## Persona Depth Accounting

All 68 identity records have `persona_id`, role and `aiims_function`, and all 68 depth profiles were read as text.
The shared controlling path is [canonical page](../../apps/web/src/app/workspaces/[personaId]/page.tsx#L23) ->
[workspace service](../../apps/api/app/services/persona_workspace_service.py#L14) ->
[panel selection](../../apps/web/src/components/workspaces/persona-workspace.tsx#L64).
Every profile routes to `/workspaces/<persona-id>`. The generic Start Task mutation is credited, but does not implement
the distinct depth transition. No execution or persona endorsement is inferred from profile existence.

For the entries below, the action words imply the profile's actual targets: Declare -> POST declarations (201);
Escalate -> incident severity PATCH (200); Publish -> warnings POST (201); Handover -> handoffs POST (200);
Allocate -> resources allocation POST (200); Queue/sync -> mutual-aid queue POST (202); Approve -> warning PATCH (200);
Tamper/read -> audit PATCH (403) then audit-list GET (200); Report -> governance report GET (200); Export -> governance
evidence export GET (200). These exact route contracts remain separate from a canned evaluator request. Each profile
also names an evaluator and a header-sourced audit correlation; the generated tests do not execute those action lists.

| Persona | Profile source | Prescribed transition / parent evaluator | Status and observed canonical behaviour | Follow-up |
| --- | --- | --- | --- | --- |
| abf | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/abf.depth.yaml#L1) | Declare / sc-005 | PARTIAL: generic task-only shell; no declaration | AUD-035-012, AUD-035-021 |
| act-ambulance | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/act-ambulance.depth.yaml#L1) | Escalate / sc-002 | PARTIAL: no severity transition | AUD-035-012, AUD-035-021 |
| act-esa | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/act-esa.depth.yaml#L1) | Publish / sc-003 | PARTIAL: no bound AWS composer | AUD-035-005, AUD-035-012 |
| act-fr | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/act-fr.depth.yaml#L1) | Declare / sc-001 | PARTIAL: no declaration | AUD-035-012 |
| act-policing | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/act-policing.depth.yaml#L1) | Declare / sc-002 | PARTIAL: no declaration | AUD-035-012 |
| act-rfs | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/act-rfs.depth.yaml#L1) | Declare / sc-001 | PARTIAL: no declaration | AUD-035-012 |
| adf | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/adf.depth.yaml#L1) | Handover / sc-004 | PARTIAL: no DACC handover action | AUD-035-012 |
| afp-act | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/afp-act.depth.yaml#L1) | Declare / sc-002 | PARTIAL: no canonical declaration or precinct command | AUD-035-012 |
| afp-commonwealth | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/afp-commonwealth.depth.yaml#L1) | Declare / sc-002 | PARTIAL: no declaration | AUD-035-012 |
| arc | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/arc.depth.yaml#L1) | Handover / sc-005 | PARTIAL: no recovery handover | AUD-035-007, AUD-035-012 |
| asa | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/asa.depth.yaml#L1) | Handover / sc-005 | PARTIAL: no maritime handover | AUD-035-012 |
| at | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/at.depth.yaml#L1) | Escalate / sc-002 | PARTIAL: no severity/rescue-to-care action | AUD-035-012 |
| av | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/av.depth.yaml#L1) | Escalate / sc-001 | PARTIAL: no medical escalation | AUD-035-012 |
| bom-national | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/bom-national.depth.yaml#L1) | Publish / sc-003 | PARTIAL: no canonical publish/ABC-SBS ack | AUD-035-005, AUD-035-012 |
| bushfires-nt | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/bushfires-nt.depth.yaml#L1) | Declare / sc-001 | PARTIAL: no declaration/remote queue | AUD-035-004, AUD-035-012 |
| cfa-vic | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/cfa-vic.depth.yaml#L1) | Declare / sc-001 | PARTIAL: no declaration/Code Red joint command | AUD-035-012 |
| community-ngos | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/community-ngos.depth.yaml#L1) | Handover / sc-005 | PARTIAL: no recovery handover | AUD-035-012, AUD-035-013 |
| dfes-wa | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/dfes-wa.depth.yaml#L1) | Declare / sc-004 | PARTIAL: no canonical declaration/cultural/infrastructure action | AUD-035-006, AUD-035-012 |
| executive-leader | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/executive-leader.depth.yaml#L1) | Export / sc-005 | PARTIAL: no executive export/economic action panel | AUD-035-011, AUD-035-012, AUD-035-013 |
| field-coordinator | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/field-coordinator.depth.yaml#L1) | Escalate / sc-002 | CONFLICT: profile escalation differs from brief GPS; offline panel provides neither durable capture nor severity action | AUD-035-004, AUD-035-020 |
| frnsw | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/frnsw.depth.yaml#L1) | Declare / sc-001 | PARTIAL: no declaration | AUD-035-012 |
| frv | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/frv.depth.yaml#L1) | Declare / sc-001 | PARTIAL: no declaration | AUD-035-012 |
| ga-national | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/ga-national.depth.yaml#L1) | Publish / sc-001 | PARTIAL: no published tsunami warning handoff | AUD-035-005, AUD-035-012 |
| health | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/health.depth.yaml#L1) | Escalate / sc-001 | PARTIAL: no severity/health workflow | AUD-035-012 |
| incident-commander | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/incident-commander.depth.yaml#L1) | Approve / sc-001 | PARTIAL: card sends incompatible evaluator payload, no warning PATCH/real approval | AUD-035-001 |
| local-government | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/local-government.depth.yaml#L1) | Declare / sc-005 | PARTIAL: no local declaration/funding action | AUD-035-012, AUD-035-013 |
| logistics-officer | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/logistics-officer.depth.yaml#L1) | Queue/sync / sc-004 | PARTIAL: no logistics approval or mutual-aid queue panel | AUD-035-001, AUD-035-012 |
| mrnsw | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/mrnsw.depth.yaml#L1) | Publish / sc-003 | PARTIAL: no canonical AWS publication | AUD-035-005, AUD-035-012 |
| nema | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/nema.depth.yaml#L1) | Handover / sc-004 | PARTIAL: no canonical DACC/JATWC handover; only Commonwealth tag | AUD-035-012, AUD-035-021 |
| nsw-ambulance | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/nsw-ambulance.depth.yaml#L1) | Escalate / sc-001 | PARTIAL: no medical escalation | AUD-035-012 |
| nsw-rfs | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/nsw-rfs.depth.yaml#L1) | Declare / sc-001 | PARTIAL: no declaration/IAP command | AUD-035-009, AUD-035-012 |
| nswpf | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/nswpf.depth.yaml#L1) | Declare / sc-002 | PARTIAL: no declaration/cross-agency movement | AUD-035-012 |
| ntes | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/ntes.depth.yaml#L1) | Publish / sc-003 | PARTIAL: no canonical publish/elder approval | AUD-035-005, AUD-035-006, AUD-035-012 |
| ntfrs | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/ntfrs.depth.yaml#L1) | Declare / sc-001 | PARTIAL: no declaration/remote action | AUD-035-004, AUD-035-012 |
| ntpf | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/ntpf.depth.yaml#L1) | Declare / sc-002 | PARTIAL: no declaration | AUD-035-012 |
| observer-auditor | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/observer-auditor.depth.yaml#L1) | Tamper/read / sc-004 | PARTIAL: empty timeline/synthetic emit, no byte read-back/export | AUD-035-003, AUD-035-011 |
| operations-officer | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/operations-officer.depth.yaml#L1) | Allocate / sc-002 | PARTIAL: only empty span props; no allocation/approval panel | AUD-035-001, AUD-035-010, AUD-035-012 |
| planning-officer | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/planning-officer.depth.yaml#L1) | Declare / sc-003 | CONFLICT: profile declaration differs from read-only IAP; neither full declaration nor forecast handoff implemented | AUD-035-009, AUD-035-020 |
| public-information-officer | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/public-information-officer.depth.yaml#L1) | Publish / sc-001 | PARTIAL: draft-only composer, no Publish selector/route | AUD-035-005 |
| qas | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/qas.depth.yaml#L1) | Escalate / sc-001 | PARTIAL: no medical escalation | AUD-035-012 |
| qfd | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/qfd.depth.yaml#L1) | Declare / sc-004 | PARTIAL: no declaration/Coastal Hazard Plan action | AUD-035-012 |
| qps | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/qps.depth.yaml#L1) | Declare / sc-002 | PARTIAL: no declaration/traffic movement | AUD-035-012 |
| resilience-planner | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/resilience-planner.depth.yaml#L1) | Handover / sc-005 | PARTIAL: incomplete signing request and no handoff transition | AUD-035-007, AUD-035-013 |
| rfds | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/rfds.depth.yaml#L1) | Escalate / sc-001 | PARTIAL: no remote medical escalation/queue | AUD-035-004, AUD-035-012 |
| risk-manager | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/risk-manager.depth.yaml#L1) | Report / sc-003 | CONFLICT: profile report-generation differs from brief live risk; panel provides neither report nor recommendation | AUD-035-008, AUD-035-020 |
| saas | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/saas.depth.yaml#L1) | Escalate / sc-002 | PARTIAL: no medical escalation | AUD-035-012 |
| sacfs | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/sacfs.depth.yaml#L1) | Declare / sc-001 | PARTIAL: no declaration/outback offline action | AUD-035-004, AUD-035-012 |
| samfs | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/samfs.depth.yaml#L1) | Declare / sc-001 | PARTIAL: no declaration | AUD-035-012 |
| sapol | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/sapol.depth.yaml#L1) | Declare / sc-002 | PARTIAL: no canonical declaration or delegated LGA control | AUD-035-012 |
| ses-act | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/ses-act.depth.yaml#L1) | Publish / sc-003 | PARTIAL: no canonical publication/territory declaration | AUD-035-005, AUD-035-012 |
| ses-nsw | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/ses-nsw.depth.yaml#L1) | Publish / sc-003 | PARTIAL: no NSW publication/multi-LGA flow | AUD-035-005, AUD-035-012 |
| ses-qld | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/ses-qld.depth.yaml#L1) | Publish / sc-003 | PARTIAL: no QLD publication/evacuation flow | AUD-035-005, AUD-035-012 |
| ses-sa | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/ses-sa.depth.yaml#L1) | Publish / sc-003 | PARTIAL: no canonical publish/convoy flow | AUD-035-005, AUD-035-012 |
| ses-tas | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/ses-tas.depth.yaml#L1) | Publish / sc-003 | PARTIAL: no publication/island logistics flow | AUD-035-005, AUD-035-012 |
| ses-vic | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/ses-vic.depth.yaml#L1) | Publish / sc-003 | PARTIAL: no publication/EMV coordination | AUD-035-005, AUD-035-012 |
| sja-national | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/sja-national.depth.yaml#L1) | Escalate / sc-001 | PARTIAL: no medical escalation | AUD-035-012 |
| sja-nt | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/sja-nt.depth.yaml#L1) | Escalate / sc-001 | PARTIAL: no canonical disease/telemedicine escalation | AUD-035-004, AUD-035-012 |
| sja-wa | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/sja-wa.depth.yaml#L1) | Escalate / sc-001 | PARTIAL: no remote medical escalation | AUD-035-004, AUD-035-012 |
| state-government | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/state-government.depth.yaml#L1) | Declare / sc-005 | PARTIAL: no state declaration/funding flow | AUD-035-012, AUD-035-013 |
| surf-lifesaving | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/surf-lifesaving.depth.yaml#L1) | Handover / sc-003 | PARTIAL: no coastal handover | AUD-035-012 |
| taspol | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/taspol.depth.yaml#L1) | Declare / sc-002 | PARTIAL: no canonical declaration/palawa publish | AUD-035-006, AUD-035-012 |
| territory-government | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/territory-government.depth.yaml#L1) | Declare / sc-005 | PARTIAL: no differentiated territory declaration | AUD-035-012 |
| tfs | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/tfs.depth.yaml#L1) | Declare / sc-001 | PARTIAL: no declaration/island offline action | AUD-035-004, AUD-035-012 |
| transport | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/transport.depth.yaml#L1) | Allocate / sc-004 | PARTIAL: no transport allocation | AUD-035-012 |
| utility | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/utility.depth.yaml#L1) | Allocate / sc-005 | PARTIAL: no canonical allocation/insurance recovery | AUD-035-012, AUD-035-013 |
| vicpol | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/vicpol.depth.yaml#L1) | Declare / sc-002 | PARTIAL: no declaration/joint command | AUD-035-012 |
| volunteer | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/volunteer.depth.yaml#L1) | Handover / sc-001 | PARTIAL: no surge handover | AUD-035-012 |
| wapol | [profile](../../tests/e2e/web-coverage/_lib/depth-profiles/wapol.depth.yaml#L1) | Declare / sc-002 | PARTIAL: no declaration/private mining mutual aid | AUD-035-012 |

### Cycle-1 Sector Scenarios

T187-T199 below are parent-spec scenario references, not extra original tasks in the 82-row matrix. Each test file
exists. Its body grades canned evaluator inputs and reads evaluator audit, not the sector action named by its title;
source-defined pages and controls are credited but cannot establish the claimed passing production scenario.

| Parent reference | Existing tester home | Existing owning page / missing domain behaviour | Status | Follow-up |
| --- | --- | --- | --- | --- |
| T187 | [SAPOL RBAC](../../tests/e2e/web-coverage/sectors/sa/sapol.state-control-centre-rbac.spec.ts#L21) | [SAPOL](../../apps/web/src/app/(operations)/sectors/sapol-control-centre/page.tsx#L20): two-LGA delegation, operator/approver/publisher separation and authority audit missing | PARTIAL | AUD-035-002, AUD-035-012 |
| T188 | [SES-SA multi-LGA](../../tests/e2e/web-coverage/sectors/sa/ses-sa.long-distance-multi-lga-evacuation.spec.ts#L1) | [SES-SA](../../apps/web/src/app/(operations)/sectors/ses-sa-multi-lga/page.tsx#L20): convoy staging, shelter routing, SAPOL air bridge and delayed sync missing | PARTIAL | AUD-035-004, AUD-035-012 |
| T189 | [WA ATSI](../../tests/e2e/web-coverage/sectors/wa/dfes-wa.atsi-handoff-culturally-safe.spec.ts#L1) | [WA cultural](../../apps/web/src/app/(operations)/sectors/dfes-wa-cultural-safety/page.tsx#L20): actual reviewed dialect/elder request/approval/IC override missing | PARTIAL | AUD-035-005, AUD-035-006, AUD-035-012 |
| T190 | [WA iron-ore](../../tests/e2e/web-coverage/sectors/wa/dfes-wa.iron-ore-critical-infrastructure.spec.ts#L1) | [Iron-ore](../../apps/web/src/app/(operations)/sectors/dfes-wa-iron-ore/page.tsx#L20): real port/rail/power priorities, DFES/WAPOL/private mutual aid, redaction and recovery handoff missing | PARTIAL | AUD-035-012 |
| T191 | [TAS island medevac](../../tests/e2e/web-coverage/sectors/tas/at.island-isolation-aeromedical-disruption.spec.ts#L1) | [Island](../../apps/web/src/app/(operations)/sectors/at-tas-island-isolation/page.tsx#L20): ferry/air status, alternatives and AT/State Health rescue-to-care missing | PARTIAL | AUD-035-004, AUD-035-012 |
| T192 | [TAS palawa](../../tests/e2e/web-coverage/sectors/tas/taspol.palawa-multilingual-warning.spec.ts#L1) | [TasPol](../../apps/web/src/app/(operations)/sectors/taspol-multilingual/page.tsx#L20): empty variants, default-AU PIO, no palawa approval/publication/small-channel accessibility | PARTIAL | AUD-035-005, AUD-035-006, AUD-035-021 |
| T193 | [ACT security](../../tests/e2e/web-coverage/sectors/act/afp.national-capital-security-mechanics.spec.ts#L1) | [AFP](../../apps/web/src/app/(operations)/sectors/afp-act-precinct/page.tsx#L20): federal/Defence geometry, tenancy collision and dual-identity command absent | PARTIAL | AUD-035-012 |
| T194 | [ACT declaration](../../tests/e2e/web-coverage/sectors/act/ses-act.territory-emergency-declaration.spec.ts#L1) | [SES-ACT](../../apps/web/src/app/(operations)/sectors/ses-act-declaration/page.tsx#L20): territory/state distinction and persisted declaration absent | PARTIAL | AUD-035-012 |
| T195 | [NT ATSI](../../tests/e2e/web-coverage/sectors/nt/ntes.atsi-multilingual-at-persona-level.spec.ts#L1) | [NTES](../../apps/web/src/app/(operations)/sectors/ntes-multilingual/page.tsx#L20): empty variants and unbound elder route; no real Yolngu Matha/Pitjantjatjara/Warlpiri publication | PARTIAL | AUD-035-005, AUD-035-006, AUD-035-012 |
| T196 | [NT tropical disease](../../tests/e2e/web-coverage/sectors/nt/sja-nt.tropical-disease-remote-logistics.spec.ts#L1) | [SJA-NT](../../apps/web/src/app/(operations)/sectors/sja-nt-tropical/page.tsx#L15): cyclone shell, not mosquito/Strongyloides/melioidosis, RFDS or telemedicine | PARTIAL | AUD-035-004, AUD-035-012 |
| T197 | [BoM ABC/SBS](../../tests/e2e/web-coverage/sectors/commonwealth/bom-national.abc-sbs-warning-relay.spec.ts#L1) | [BoM relay](../../apps/web/src/app/(operations)/sectors/bom-broadcast-relay/page.tsx#L38): boolean ack, no consumed published warning, ABC/SBS source or persisted multilingual script/ack | PARTIAL | AUD-035-005, AUD-035-012 |
| T198 | [NEMA DACC/JATWC](../../tests/e2e/web-coverage/sectors/commonwealth/nema.dacc-jatwc-cross-jurisdiction.spec.ts#L1) | [NEMA](../../apps/web/src/app/(operations)/sectors/nema-dacc-jatwc/page.tsx#L20): no request/approve/deploy/withdraw/after-action or BoM/SES/NEMA cross-jurisdiction records/tags | PARTIAL | AUD-035-012, AUD-035-021 |
| T199 | [Utility insurance](../../tests/e2e/web-coverage/sectors/cross-sector/utility.insurance-recovery-handoff.spec.ts#L1) | [Utility](../../apps/web/src/app/(operations)/sectors/utility-insurance-recovery/page.tsx#L11): zero claims, no state funding handoff, signed PDF or Built/Economic delta trace | PARTIAL | AUD-035-007, AUD-035-013 |

## Checklist and Formal Review Accounting

The local checklist has 16 checked quality items. Those checks are preserved below, not accepted as proof of delivered
features. Its prose claims 22 scenarios, 16 edges and 10 OOS items; actual source has 24, 15 and 11 respectively.
The task summary says 81 but includes T024b, making 82. These are documentation discrepancies, not authority to drop rows.

| Check | Original state | Original item / source | Status and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| C01 | [x] | [No implementation details](checklists/requirements.md#L9) | CONFLICT: spec explicitly requires Entra, SW/IndexedDB, APIM, native APIs and middleware contract details | AUD-035-020 |
| C02 | [x] | [User value and business needs](checklists/requirements.md#L10) | IMPLEMENTED: five stories are expressed around operator/capstone outcomes, independent of shipping success | none |
| C03 | [x] | [Nontechnical stakeholders](checklists/requirements.md#L11) | PARTIAL: business summaries exist, but API/schema/middleware language remains substantial | AUD-035-020 |
| C04 | [x] | [Mandatory sections completed](checklists/requirements.md#L12) | IMPLEMENTED: stories, requirements, entities, SCs, assumptions and scope sections exist | none |
| C05 | [x] | [No unresolved markers](checklists/requirements.md#L16) | IMPLEMENTED: no unresolved marker in spec source; contradictions still require decisions | AUD-035-020 |
| C06 | [x] | [Testable and unambiguous](checklists/requirements.md#L17) | CONFLICT: Q5, Q7, error/claim/SC and quickstart contracts disagree | AUD-035-020, AUD-035-022 |
| C07 | [x] | [Measurable SCs](checklists/requirements.md#L18) | IMPLEMENTED: thresholds/artifacts are authored for all 12 SCs; measurements unverified | AUD-035-021 |
| C08 | [x] | [Technology-agnostic SCs](checklists/requirements.md#L19) | PARTIAL: numerical outcomes exist but exact Playwright/Entra/runner/path bindings remain | AUD-035-020 |
| C09 | [x] | [Acceptance scenarios defined](checklists/requirements.md#L20) | IMPLEMENTED: all 24 scenarios exist, not the claimed 22; implementation coverage recorded individually | AUD-035-020 |
| C10 | [x] | [Edges identified](checklists/requirements.md#L21) | IMPLEMENTED: 15 edge bullets exist, not the claimed 16; all reviewed separately | AUD-035-020 |
| C11 | [x] | [Scope bounded](checklists/requirements.md#L22) | PARTIAL: 11 OOS clauses explicit, but suite-read-only versus production assertions/config extension unresolved | AUD-035-020, AUD-035-021 |
| C12 | [x] | [Dependencies/assumptions identified](checklists/requirements.md#L23) | IMPLEMENTED: ten assumptions plus dependency graph authored; cloud availability and review outputs unverified | AUD-035-019, AUD-035-021 |
| C13 | [x] | [Every FR has clear acceptance](checklists/requirements.md#L27) | PARTIAL: FR-004/005 have only narrative coverage and policy/schema conflicts remain | AUD-035-008, AUD-035-009, AUD-035-020 |
| C14 | [x] | [User scenarios cover primary flows](checklists/requirements.md#L28) | PARTIAL: story breadth exists; logistics/operations/executive endorsement and full 68-depth execution are not evidence | AUD-035-012, AUD-035-021 |
| C15 | [x] | [Feature meets measurable outcomes](checklists/requirements.md#L29) | UNVERIFIED: no current production/scenario/latency/accessibility/signature or human evidence supports this claim | AUD-035-021 |
| C16 | [x] | [No implementation details leak](checklists/requirements.md#L30) | CONFLICT: repeats C01 despite detailed implementation mandates in FRs and clarifications | AUD-035-020 |

### Plan Gate Claims

Both plan tables are authored design reviews. Each original row says PASS and has no checkbox (`none`); none proves a
runtime/human gate. The spec's NN-1..NN-5 shorthand also does not match the actual constitution numbering: the current
[constitution](../../.specify/memory/constitution.md#L268) lists human authorisation, sovereignty, privacy,
interoperability and graceful degradation. Its quality gates are prose bullets, not the local QG-1..QG-3 labels.
The explicit FR obligations still bind; the attribution discrepancy must be corrected without amending the constitution.

| Gate row | Original state | Status | Evidence assessment | Follow-up |
| --- | --- | --- | --- | --- |
| Initial-NN1 | none (PASS) | PARTIAL | [Initial table](plan.md#L82): sovereignty policy declared, actual egress/identity and deployed AU persistence incomplete/unverified | AUD-035-015, AUD-035-019 |
| Initial-NN2 | none (PASS) | PARTIAL | [Initial table](plan.md#L82): audit declaration contradicted by split local/durable stores and non-atomic fallback | AUD-035-003 |
| Initial-NN3 | none (PASS) | UNVERIFIED | [Initial table](plan.md#L82): no complete current WCAG scan/manual review | AUD-035-021 |
| Initial-NN4 | none (PASS) | PARTIAL | [Initial table](plan.md#L82): language names exist, translations/approval/public fallback incomplete | AUD-035-005, AUD-035-006 |
| Initial-NN5 | none (PASS) | PARTIAL | [Initial table](plan.md#L82): worker no-op and replay incomplete | AUD-035-004 |
| Initial-QG1 | none (PASS) | UNVERIFIED | [Initial table](plan.md#L82): authored tests do not prove failing-first chronology or sufficient assertions | AUD-035-021 |
| Initial-QG2 | none (PASS) | PARTIAL | [Initial table](plan.md#L82): named artifacts exist as empty/stale placeholders, not current outcomes | AUD-035-021 |
| Initial-QG3 | none (PASS) | PARTIAL | [Initial table](plan.md#L82): signed immutable evidence stubbed | AUD-035-003, AUD-035-007 |
| Initial-AVM | none (PASS) | PARTIAL | [Initial table](plan.md#L82): AVM hosts authored but raw policies/connectivity/principal/consumer wiring incomplete | AUD-035-019 |
| Initial-Human | none (PASS) | PARTIAL | [Initial table](plan.md#L82): approval/publish/elder paths not installed end to end | AUD-035-001, AUD-035-005, AUD-035-006 |
| Post-NN1 | none (PASS) | PARTIAL | [Post table](plan.md#L279): contract existence is not actual egress/region proof | AUD-035-015, AUD-035-019 |
| Post-NN2 | none (PASS) | PARTIAL | [Post table](plan.md#L279): entity/batch shape does not establish durable atomic timeline | AUD-035-003 |
| Post-NN3 | none (PASS) | UNVERIFIED | [Post table](plan.md#L279): quickstart instruction is not WCAG evidence | AUD-035-021 |
| Post-NN4 | none (PASS) | CONFLICT | [Post table](plan.md#L279): cultural contract conflicts with Q5 and does not publish real variants | AUD-035-006, AUD-035-020 |
| Post-NN5 | none (PASS) | PARTIAL | [Post table](plan.md#L279): replay schema does not implement interception/durable action effects | AUD-035-004 |
| Post-QG1 | none (PASS) | UNVERIFIED | [Post table](plan.md#L279): naming a test directory is not TDD/coverage evidence | AUD-035-021 |
| Post-QG2 | none (PASS) | CONFLICT | [Post table](plan.md#L279): quickstart verification matrix maps the wrong SC meanings | AUD-035-020 |
| Post-QG3 | none (PASS) | PARTIAL | [Post table](plan.md#L279): PDF contract is authored, signer/blob remain stubs | AUD-035-007 |
| Post-AVM | none (PASS) | PARTIAL | [Post table](plan.md#L279): no current build/what-if/policy/permission evidence | AUD-035-019 |
| Post-Human | none (PASS) | UNVERIFIED | [Post table](plan.md#L279): no actual IC/elder/security/community approval records | AUD-035-001, AUD-035-006, AUD-035-021 |

### Embedded Task Changes

| Amendment | Status | Source decision and remaining obligation | Follow-up |
| --- | --- | --- | --- |
| A01 T024b insertion | PARTIAL | [Separate RBAC task](tasks.md#L194) retained; summary not updated from 81 to 82 and enforcement incomplete | AUD-035-002, AUD-035-020 |
| A02 T040 configurable cap | PARTIAL | [Environment-sourced cap](tasks.md#L288) and small-cap test exist; per-persona transactional limits/replay still missing | AUD-035-004 |
| A03 T044 expiry banner/runbook | CONFLICT | [Expiry-specific envelope](tasks.md#L308) versus seven-code schema/detail-dropping helper; no configured runbook or matching UI | AUD-035-007, AUD-035-022 |
| A04 T045 fail-closed expired signing | PARTIAL | [No fallback/auto-rotate requirement](tasks.md#L313) not satisfied by default stub without actual certificate expiry | AUD-035-007, AUD-035-019 |
| A05 T049 Watch and Act override | CONFLICT | [Explicit test addition](tasks.md#L345) contradicts current test/contract requiring hold | AUD-035-006, AUD-035-020 |
| A06 T064 six recovery subdomains | PARTIAL | [Explicit domains](tasks.md#L436) rendered as labels only, no data/action/test evidence | AUD-035-013 |
| A07 T067 jsdom substitution | MISSING | [Explicit replacement claim](tasks.md#L463) accepted as intended format, but replacement test not present | AUD-035-016, AUD-035-021 |
| A08 T068 retired duplicate axe spec | SUPERSEDED | [Explicit supersession](tasks.md#L468) accepted only for duplicate spec; successor coverage and T077 a11y artifact remain incomplete | AUD-035-021 |
| A09 T070 file seed/Cosmos deferral | PARTIAL | [Explicit deferral](tasks.md#L480) respected; file-backed source is not a missing Cosmos implementation claim, but schema/UI/signature/pagination remain incomplete | AUD-035-016 |
| A10 T072 operations-group bootstrap | PARTIAL | [Layout scope](tasks.md#L490) installed only on operations group, not canonical workspaces; no persona field/remote gating or worker capture | AUD-035-004, AUD-035-012 |
| A11 T073 non-cultural Chinese baseline | PARTIAL | [Expanded picker requirement](tasks.md#L495) partly met by PIO options; no every-regulated-route picker or real translated bulletin | AUD-035-005, AUD-035-016 |
| A12 T074 config-only suite exception | CONFLICT | [Config extension/hardening](tasks.md#L500) is a narrow exception, not approval to rewrite assertions; production fixture and scope conflicts still require a decision | AUD-035-020, AUD-035-021 |
| A13 T077 a11y artifact ownership | UNVERIFIED | [Transferred severity report](tasks.md#L521) has no emitted file or reporter implementation, no current full run | AUD-035-021 |
| A14 T078 API helper/web deferral | PARTIAL | [Explicit web deferral](tasks.md#L526) retained; only two cultural outcomes use helper, no complete outcome query evidence | AUD-035-003, AUD-035-021 |
| A15 T079 Mermaid/drawio deferral | PARTIAL | [Explicit artifact change](tasks.md#L531) credited; Mermaid exists but describes uninstalled stack, image/export/overview obligations still deferred | AUD-035-020 |

### Panel Requirements and Hypotheses

The six local briefs are inputs to a requested review loop, not its outputs. No completed per-panel response,
consolidated merit register or final formal review is present in this folder. The session-only 85-agent register named
in [overall inputs](00-overall-brief.md#L15) is unavailable in the workspace inventory; no other implementation-review
report was read. All requested acceptance/edge/audit/constitutional/endorsement responses are therefore UNVERIFIED as
reviews, even where a requirement has subsequently been made explicit in spec.md. The following records preserve each
distinct brief requirement and hypothesis without silently adding proposed personas or higher classifications.

| Brief item | Status | Source, decision and evidence assessment | Follow-up |
| --- | --- | --- | --- |
| OP-IC | PARTIAL | [Approve/Decline and immutable rationale](operational-brief.md#L19): card does not mutate action or capture evidence | AUD-035-001 |
| OP-Planning | PARTIAL | [Editable provenance/contradictions/IC handoff](operational-brief.md#L22): read-only keyword draft only | AUD-035-009 |
| OP-PIO | PARTIAL | [Three community languages/accessibility/IC/publish](operational-brief.md#L25): draft-only English carriers; stricter language cardinality not explicitly resolved | AUD-035-005, AUD-035-020 |
| OP-Field | PARTIAL | [Offline GPS and preserved metadata](operational-brief.md#L28): capture/ack/replay absent | AUD-035-004 |
| OP-Observer | PARTIAL | [Tamper/read-back/export](operational-brief.md#L31): empty panel, no original-byte proof | AUD-035-011 |
| OP-Risk | PARTIAL | [Live alternatives/recommend to IC/Planning](operational-brief.md#L34): static one-cell recommendation, no handoff | AUD-035-008 |
| OP-Resilience | PARTIAL | [Real handover/content/signing](operational-brief.md#L37): PDF-or-JSON option explicitly narrowed by Q2/OOS-011; signed PDF still stubbed | AUD-035-007 |
| OP-Logistics | UNVERIFIED | [No-gap endorsement](operational-brief.md#L40): no current review/run proof, and canonical mutual-aid depth action absent | AUD-035-012, AUD-035-021 |
| OP-Operations | UNVERIFIED | [No-gap endorsement](operational-brief.md#L40): canonical allocation/approval absent despite shell | AUD-035-001, AUD-035-012, AUD-035-021 |
| OP-Executive | UNVERIFIED | [No-gap endorsement](operational-brief.md#L40): no canonical evidence export panel or passing outcome proof | AUD-035-011, AUD-035-013, AUD-035-021 |
| OP-Shared | PARTIAL | [Composer reuse/offline/audit on all surfaces](operational-brief.md#L43): shared components exist but wiring incomplete | AUD-035-004, AUD-035-005, AUD-035-011, AUD-035-012 |
| EAST-NSW | PARTIAL | [SES/RFS/ABF/Health/Police, LGAs, Reconstruction Authority](sector-eastern-brief.md#L15): current canonical depths lack required actions; no positive endorsement output | AUD-035-012, AUD-035-020, AUD-035-021 |
| EAST-VIC | PARTIAL | [CFA/SES/AV/Police/DEECA/EMV, Code Red/joint command](sector-eastern-brief.md#L16): generic canonical shell, no positive UI-depth proof or specific scope response | AUD-035-012, AUD-035-020, AUD-035-021 |
| EAST-QLD | PARTIAL | [QFES/QPS/QAS/QRA/Resources, coastal plan/recovery](sector-eastern-brief.md#L17): generic shell and no documented panel response; accepted 68 IDs must not be expanded by implication | AUD-035-012, AUD-035-020, AUD-035-021 |
| EAST-Hypothesis | CONFLICT | [Silence does not mean east is fine](sector-eastern-brief.md#L7): code contradicts presumed depth completion; endorsement needs explicit current evidence | AUD-035-012, AUD-035-021 |
| EAST-Additional asks | UNVERIFIED | [Coronial/IGEM export, language, insurance, remote geography](sector-eastern-brief.md#L19): proposed scope/criteria and per-persona PASS/FAIL response not retained; no new features silently added | AUD-035-020, AUD-035-021 |
| SW-SA-RBAC | PARTIAL | [Control-centre delegated authority](sector-southwest-brief.md#L13): SAPOL shell lacks role-separated LGA actions | AUD-035-012 |
| SW-SA-Evac | PARTIAL | [Convoy/shelter/air bridge/offline](sector-southwest-brief.md#L16): SES-SA composition does not implement them | AUD-035-004, AUD-035-012 |
| SW-WA-Culture | PARTIAL | [Kimberley/Pilbara elder handoff](sector-southwest-brief.md#L19): registry labels but no real approval/translation | AUD-035-006, AUD-035-012 |
| SW-WA-Infrastructure | PARTIAL | [Port/rail/power/DFES/WAPOL/private recovery](sector-southwest-brief.md#L22): toggle list only | AUD-035-012 |
| SW-TAS-Island | PARTIAL | [Ferry/air/AT-State Health handoff](sector-southwest-brief.md#L25): no status or transition | AUD-035-012 |
| SW-TAS-Language | PARTIAL | [Palawa/small-population channels](sector-southwest-brief.md#L28): no approved translated warning or complete accessibility evidence | AUD-035-006, AUD-035-021 |
| SW-Shared | PARTIAL | [Remote offline/single cultural subsystem/overlay](sector-southwest-brief.md#L31): shared source exists but is disconnected; requested confirm/deepen review unverified | AUD-035-004, AUD-035-006, AUD-035-012, AUD-035-021 |
| TC-ACT | PARTIAL | [Federal tenancy/AFP/territory declaration](sector-tc-brief.md#L13): absent real geometry/authority transition | AUD-035-012 |
| TC-NT-Language | PARTIAL | [Three NT languages/remote elder](sector-tc-brief.md#L16): labels only, no routed approval | AUD-035-006, AUD-035-012 |
| TC-NT-Disease | PARTIAL | [Disease/RFDS/telemedicine/public-health audit](sector-tc-brief.md#L19): cyclone shell substituted | AUD-035-004, AUD-035-012 |
| TC-Broadcast | PARTIAL | [ABC/SBS consumption/script/ack](sector-tc-brief.md#L22): explicit canonical BoM binding preserves persona count, but local ack is not persisted | AUD-035-005, AUD-035-012 |
| TC-Inventory | SUPERSEDED | [Additional persona proposal](sector-tc-brief.md#L25) explicitly rejected/deferred by [ASM-003](spec.md#L243) and OOS-001; capabilities remain depth-only on canonical BoM/NEMA/Utility | AUD-035-012 |
| TC-Insurance-DACC | PARTIAL | [ICA/state funding and DACC/JATWC](sector-tc-brief.md#L28): separate labels not persisted lifecycle/handoff | AUD-035-012, AUD-035-013 |
| TC-Recovery | PARTIAL | [Built/Economic subdomains](sector-tc-brief.md#L31): names present, current data/editing missing | AUD-035-013 |
| TC-Shared | PARTIAL | [Warnings/model-source/DACC lifecycle](sector-tc-brief.md#L34): no completed actual workflow or review response | AUD-035-005, AUD-035-012, AUD-035-016, AUD-035-021 |

### Technical Panel Questions

All 27 questions are accounted for separately. A source decision is credited only where actually documented; no panel
execution, architecture approval or human consensus is invented. Each question's six requested output categories
(decision, anchor, acceptance, risks, Azure resources, tests) are covered by the local planning artifacts only in part;
the missing consolidated panel response remains UNVERIFIED under AUD-035-020/021.

| Question | Status | Source / decision and evidence assessment | Follow-up |
| --- | --- | --- | --- |
| TQ01 | PARTIAL | [RSC versus client state](technical-brief.md#L15): Next App Router/client panels authored, but no coherent durable workflow state machine | AUD-035-001, AUD-035-005 |
| TQ02 | UNVERIFIED | [Shared/per-jurisdiction Foundry](technical-brief.md#L16): plan reuses existing Foundry; actual availability/translation integration unverified | AUD-035-005, AUD-035-019 |
| TQ03 | PARTIAL | [Offline architecture choice](technical-brief.md#L17): Q4/R-003 select native SW+IDB, implementation incomplete | AUD-035-004 |
| TQ04 | PARTIAL | [Entra sector/elder roles](technical-brief.md#L18): Q1/Q9 fix 11 roles and impersonation, scope/routing enforcement incomplete | AUD-035-002, AUD-035-006 |
| TQ05 | PARTIAL | [Tamper-resistant timeline UX](technical-brief.md#L19): declared denial copy, no authoritative read-back/export | AUD-035-003, AUD-035-011 |
| TQ06 | PARTIAL | [Production evaluator contract](technical-brief.md#L23): Q10/additive routes exist, auth/ladder/evidence unresolved | AUD-035-002, AUD-035-022 |
| TQ07 | PARTIAL | [Cursor/sort/max-page contract](technical-brief.md#L24): local sorted ledger/max500 exists, not durable snapshot or UI load-more | AUD-035-003, AUD-035-011 |
| TQ08 | MISSING | [Named APIs for all 13 scenarios](technical-brief.md#L25): no complete delegated-LGA/precinct/DACC/disease/claims contracts/handlers in scoped local inputs/source | AUD-035-012, AUD-035-020 |
| TQ09 | PARTIAL | [Signed immutable handover store](technical-brief.md#L29): R-009 decision authored, actual renderer/signer/store stubbed | AUD-035-007, AUD-035-019 |
| TQ10 | PARTIAL | [Claims/grants/KPI entities](technical-brief.md#L30): data-model descriptions and props exist; persistent event/snapshot/subdomain actions not implemented | AUD-035-013 |
| TQ11 | PARTIAL | [Language-pack storage/jurisdiction](technical-brief.md#L31): static registry exists, no actual reviewed language content/elder targets | AUD-035-006 |
| TQ12 | PARTIAL | [Model-source visibility/audit](technical-brief.md#L35): source labelling and common registry UI absent | AUD-035-015, AUD-035-016 |
| TQ13 | PARTIAL | [Correct tamper attempt UX](technical-brief.md#L36): synthetic record endpoint exists, no real failed PATCH/DELETE/refetch proof | AUD-035-011 |
| TQ14 | IMPLEMENTED | [Higher classifications](technical-brief.md#L37): explicit ASM-005/OOS-008 defers PROTECTED+, not an implementation failure | none |
| TQ15 | PARTIAL | [Production role/rate/audit](technical-brief.md#L38): declared stack incomplete at identity, rate, shared audit boundaries | AUD-035-002, AUD-035-003, AUD-035-017 |
| TQ16 | CONFLICT | [Read-only suite/YAML fix policy](technical-brief.md#L42): preserved; FR-030 production/error/depth expectations not realizable by existing test assertions | AUD-035-020, AUD-035-021 |
| TQ17 | PARTIAL | [AWS alt text/lang/keyboard/announcements](technical-brief.md#L43): some labels/live regions exist, but inline scan tags/wiring and deep-surface coverage incomplete | AUD-035-005, AUD-035-021 |
| TQ18 | PARTIAL | [Visible fallback chain](technical-brief.md#L44): resolver source present, actual variant-first/source-labelled public rendering absent | AUD-035-005, AUD-035-006 |
| TQ19 | UNVERIFIED | [Replay SLO definition/evidence](technical-brief.md#L48): Q7/SC-007 define limits, no actual capture/drain measurement | AUD-035-004, AUD-035-021 |
| TQ20 | UNVERIFIED | [Canary/config production rollout](technical-brief.md#L49): new hardening flag off, no current staging/production rollout record | AUD-035-019, AUD-035-021 |
| TQ21 | UNVERIFIED | [Offline/evaluator/elder chaos plan](technical-brief.md#L50): no completed local plan/result for these failures; remediation fixtures specify minimum negatives for later execution | AUD-035-004, AUD-035-006, AUD-035-021 |
| TQ22 | PARTIAL | [Translation model/prompt/temperature/human fallback](technical-brief.md#L54): inherited transport exists, but PIO uses English carrier bridge, no actual translation invocation contract | AUD-035-005, AUD-035-015 |
| TQ23 | PARTIAL | [JATWC advisory/human approve/publish](technical-brief.md#L55): NEMA page lacks chain and persisted approval | AUD-035-012 |
| TQ24 | PARTIAL | [Culturally safe reviewed output](technical-brief.md#L56): reviewer flag and fallback helpers exist, no actual consent/content-safety evidence | AUD-035-006 |
| TQ25 | UNVERIFIED | [Standalone size/App Service capacity](technical-brief.md#L60): standalone config exists; no build/measurement/deployed capacity reviewed | AUD-035-019, AUD-035-021 |
| TQ26 | PARTIAL | [Degraded banner/sync/error recovery](technical-brief.md#L61): banner/depth controls exist, hide early and discard failed requests | AUD-035-004 |
| TQ27 | IMPLEMENTED | [Backlog ordering](technical-brief.md#L62): [plan phases](plan.md#L258) explicitly put auth before operator/sector/recovery/horizontals; authored ordering is not shipping proof | AUD-035-021 |

### Story and Checkpoint Claims

| Claim | Status | Source and assessment | Follow-up |
| --- | --- | --- | --- |
| US1 independent operational gate | UNVERIFIED | [Operational shard + five cross-cutting files](spec.md#L56): no current staging/production >=95%/zero-HIGH proof | AUD-035-021 |
| US2 independent bearer/evaluator gate | UNVERIFIED | [Production evaluator/audit](spec.md#L74): no Entra-issued bearer run, and current helper bypasses JWT | AUD-035-002, AUD-035-021 |
| US3 independent 13-sector gate | UNVERIFIED | [Sector gate](spec.md#L93): test names exist, not real depth action evidence | AUD-035-012, AUD-035-021 |
| US4 independent recovery gate | UNVERIFIED | [Recovery + resilience gate](spec.md#L111): no valid signed download or editable four-domain measurement | AUD-035-007, AUD-035-013, AUD-035-021 |
| US5 independent horizontal gate | UNVERIFIED | [Three-jurisdiction cross-cutting gate](spec.md#L127): no complete offline/language/sovereignty/axe run | AUD-035-021 |
| Setup/foundational checkpoints | UNVERIFIED | [Task phase checkpoints](tasks.md#L75): package/modules/source do not establish installed toolchain, deploy-ready infra or unblocked features | AUD-035-019, AUD-035-021 |
| US2/MVP/US3/US4/US5 closure checkpoints | UNVERIFIED | [Task plan](tasks.md#L234): success prose and checked implementation boxes do not satisfy the independently unchecked gate tasks | AUD-035-021 |
| Review-loop/human approval completion | UNVERIFIED | [Overall workflow](00-overall-brief.md#L28): briefs request 85-agent/panel input, no retained completed review outputs or human/community signatures | AUD-035-020, AUD-035-021 |

## Bounded Search and Relocation Ledger

Searches were restricted to the named spec and its implementation/test/contract dependencies. No other
implementation-review report was opened. `rg` was unavailable; file search, targeted text search, full file reads and
read-only PowerShell text/metadata inspection were used. Direct literal-path checks confirmed absent named artifacts;
the table records where renamed or adjacent behaviour was inspected before assigning MISSING/PARTIAL.

| Search | Bounded scope / controlling source inspected | Result and limit |
| --- | --- | --- |
| NS01 Approval panel relocation | Web app routes/components, [persona-workspace.tsx](../../apps/web/src/components/workspaces/persona-workspace.tsx#L4), canonical workspace page | Found outside `(operations)` at `app/workspaces/[personaId]/_panels`; not MISSING. Wrong request/state is the defect. |
| NS02 Alternate approval/evaluator route | [router.py](../../apps/api/app/api/router.py#L176), [workspace_bridges.py](../../apps/api/app/api/routes/workspace_bridges.py#L69), bridge tests | Found explicit gates-off fallback with another schema and memory audit. Does not replace durable approval or authorise production bypass. |
| NS03 Existing generic mutation | [task-status-panel.tsx](../../apps/web/src/components/workspaces/task-status-panel.tsx#L16), tasks client/handler/service/repository | Found genuine `in_progress` update. No rationale/approval/version/CAS/handoff semantics on that path. |
| NS04 IC stale-state handling | Approval panel, bridge, canonical evaluator and adjacent task transition source | No connected action version or first-write-wins 409 UX found; E12 MISSING is limited to this approval journey, not a claim that no 409 exists anywhere. |
| NS05 Auth identity mapping | New/legacy auth middleware, RBAC registry, persona repository and complete 68-record seed | Found all mappings and JWT code, but unknown persona/admin target allow and inner claim overwrite. Missing claim validation is not inferred from missing filenames. |
| NS06 Audit/tamper relocation | Observer, [audit.py](../../apps/api/app/api/routes/audit.py#L43), audit-list, evaluator ledger, audit repository/appender, bridge tests | Found denial recorder, canonical reader and real batch API; separate stores/raw-header pairing/non-atomic fallback prevent required proof. |
| NS07 Offline interception/producer | `apps/web/src/lib/offline`, field panel, operations layout/bootstrap, `public/offline-sw.js`; web/shared-UI enqueue/registration searches | Actual worker is no-op; store created only by field panel; no enqueue producer, heartbeat provider or acknowledged dedicated replay path found. |
| NS08 Offline server service/overflow | API routers/services/repositories; [offline_replay.py](../../apps/api/app/api/routes/offline_replay.py#L102) and overflow repository | Planned service moved into route; audit-only replay is present. Overflow helper has no production caller in searched API scope. |
| NS09 Communication/risk/planning bridges | Panels -> [agents.py](../../apps/api/app/api/routes/agents.py#L129); adjacent warning-chain and shared agent transport | Found deterministic bridges and reusable agents; missing connection/stateful workflow, not missing route or entire agent implementation. |
| NS10 Elder/cultural integration | Cultural panel/language registry; all API route/service/repository references to `CulturalSafetyService`/elder routing | Found pure decision service and language registry, no installed queue/deadline/approval/publication driver. No external elder system contacted. |
| NS11 Sector workflow relocation | All 13 pages plus index/shell; canonical workspace/seed/profiles; API route/service search for convoy, precinct, DACC/JATWC, disease and claims | Simulation feed references exist but do not connect sector controls to persisted actions. Existing incident/hand-off infrastructure is not treated as satisfying an unconnected page. |
| NS12 Recovery data/actions | Dashboard/claims/hand-over panels -> governance aggregation/data service; incident recovery indicator API and signing service | Found four catalogue domains plus overarching, indicator writes and ratio helper. Missing dashboard claims/Sendai endpoints, live values/funding updates and real signing remain bounded to these paths. |
| NS13 Signer/blob injection | Recovery route/service, app factory, all API references to `recovery_handover_service`, hardening modules/main params | No production real signer/blob/claims adapter injection found; defaults are marker and in-memory storage. No certificate or blob was fetched. |
| NS14 Sovereignty component relocation | Root/shared shell, every web-source `au-region-banner`/carveout/sovereignty match; governance/workspace/help/sector layouts | Fixed labels found on several pages, so not wholly MISSING. No common banner/registry/model-source consumer; planned component directory absent. |
| NS15 Model gateway relocation | [relocated ADR](../../docs/corpus/aidr/decisions/adr-033-phi-shadow-boundary.md#L1), API middleware, `llm_mixin` -> `llm_client` -> `foundry_chat_client` -> `model_gateway` | Found real non-AU classification. Audited shortcomings are fail-open/field-coverage/Q6 linkage, not absence of all egress protection. |
| NS16 Missing tests/baselines | Exact paths plus recursive names/content under `apps/web/tests`, `apps/web/__tests__`, `apps/api/tests`, relevant root tests | No baseline/sector-baseline JSON, recovery integration, insurance-handoff integration, or claimed T067 jsdom/E2E file found. Five web unit files and relocated API tests credited. |
| NS17 Infrastructure/config records | Four hardening modules, main template, dev/staging/production parameter JSON, `infra/parameters`, `infra/tests` | Named spec-035 bicepparam absent. All three parameters omit hardening flag; template default false. No real deployment/config state inferred. |
| NS18 Review/evidence/amendments | Complete local spec directory (20 inputs), cited session register filename inventory, architecture/changelog, embedded task notes | No local review/evidence/agent-review directory or completed consolidated panel report. Only briefs and design/checklist claims; embedded changes preserved individually. |
| NS19 Coverage/report artifacts | Web-coverage `_artifacts`, parent coverage/gap files, reporter, Playwright config, general/spec-035 CI and descriptive branch-protection file | Empty partial trace, 76-skipped historical run, wrong cycle SHA, placeholder parent trace, no final JSON/a11y/audit-p95 artifact. Existing JUnit is a stored record, not a current run. |
| NS20 Shared test discovery | [Vitest include/setup](../../apps/web/vitest.config.ts#L19), [pytest config](../../pyproject.toml#L45), full spec-035 test inventories | Five web unit/ten API contract/three API unit files authored; API integration initializer only. No product collection, import, test, build or benchmark executed. |

## Future Validation and Completion Gates

The exact developer/tester work is defined per unchecked AUD task. None is authorised for execution by this review.
The following sequencing preserves the current scope and avoids converting deployment or approval assumptions into proof:

1. Resolve explicit policy/schema conflicts and the read-only suite/production-fixture boundary. Keep all original
   task/checklist/evidence files unchanged until a separately authorised implementation/documentation change.
2. Prepare isolated identity, clock, queue, persistence, signing and model-transport fixtures. Use the real app factory
   and routes; reject missing/unknown identities, half audit pairs, schema drift and any outbound model call on denial.
3. Implement durable domain transitions and connect canonical persona routes. Run the existing app-owned test homes
   and proposed missing tests listed in AUD tasks; assertions must observe persisted effects, not placeholder labels.
4. Only after explicit target/config approval, run behavioural E2E and complete WCAG/keyboard/manual checks, offline
   timing, signed-PDF validation and the full unchanged-or-formally-amended suite. Current Playwright config starts local
   dev/test servers; setting a production URL elsewhere does not make this a production run.
5. Provision/deploy or inspect live Azure resources only in a separately authorised phase with governance constraints,
   proper Entra roles, private connectivity, durable stores and actual signing material. Never put secrets in the report.
6. Retain revision/environment/seed/run provenance, authentic audit IDs, complete JUnit/JSON/accessibility evidence,
   valid signed downloads and required human/community/security decisions. Enforce max-three-cycle escalation and
   rollback. Empty/skipped/stale/wrong-revision/missing-signature results must not close an SC or follow-up.

**Required future outcomes:** Every original task source obligation and all 30 FRs must be addressed; all 24 acceptance
scenarios and 15 edges must have positive/negative coverage; every canonical profile must exercise its actual transition;
all 13 named sector scenarios must pass real depth assertions. The 12 local SCs require >=95% valid production tuples,
zero Open HIGH+ gaps within the cycle bound, real warning and decision timings, acknowledged 50/500-entry replay limits,
four editable recovery environments with >=.30 ratio and signed PDF, complete auth/audit <=2s, complete accessibility,
fresh approved sovereignty state and <=45-minute complete suite evidence. These outcomes are not currently verified.

## Static Verification Record

- Expected HEAD matched `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a` via read-only metadata.
- All 20 local inputs were fully read; previously truncated spec lines were read in full. Existing report was absent.
- Exact original ID/state comparison passed for 82 task rows: 71 `[X]`, 11 `[ ]`, including T024b once.
- Separate source-ID comparisons passed for 30 FRs and 12 SCs; individual accounting exists for 24 scenarios and 15 edges.
- All 68 persona rows match the actual seed inventory; all 13 cycle-1 test/page mappings resolve to existing files.
- Accounting checks cover 10 clarifications, 12 research decisions, 12 entities, 10 assumptions, 11 exclusions,
  14 unnumbered obligation groups, 16 original checklist items, 20 plan gate rows, 15 embedded task amendments and
  all 27 technical questions. These review-local group IDs are not invented original task or requirement IDs.
- Every follow-up uses a unique unchecked `AUD-035-001`-style checkbox, with requirement/task IDs, expected/observed
  behaviour, impact, owning implementation, compatibility/dependencies, existing/proposed tester homes, cases,
  future commands/prerequisites/expected results and completion criteria. No follow-up is marked complete.
- Local evidence links were checked for existing targets and valid 1-based line bounds after every substantive report
  increment. An initial out-of-bounds parity-test anchor was corrected and rechecked. No nonexistent proposed file is
  presented as linked evidence.
- Report editor diagnostics passed during the review. Two inspected Bicep files also had no editor diagnostics; this
  was not a compile, lint command, what-if, policy scan or deployment validation.
- No tests, verifier scripts, builds, imports, browser/Playwright/server, cloud/model/runtime execution, installs,
  external approvals, branches or commits were performed. Only this report was manually edited; EOF-only mechanical
  newline formatting was used once to satisfy the editor's Markdown diagnostic.

**Remaining verification limits:** Production reachability, actual Entra/JWKS acceptance, deployed RBAC/rate budgets,
durable retention/atomicity, certificate validity, signed artifact access, data transit, latency/load/offline timing,
complete WCAG/manual accessibility, TDD chronology, branch-protection application and human/community reviews are
UNVERIFIED. Several inputs conflict and missing evidence cannot be manufactured by static inspection. The report is
complete as a static implementation review, not a claim that the feature or its original tasks are complete.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 035 only. Three parallel technical reviews examined production
auth/approval, model-gateway/offline replay, and durable audit/handover evidence. The cited model-gateway fail-open
hypothesis was checked and is already falsified by current source: missing region raises configuration failure, missing
gateway loading raises configuration failure, and non-AU text is transformed before dispatch. No duplicate patch was
applied. The broader auth, approval publication, durable audit, offline acknowledgement, signed handover, and production
evidence gaps remain open.
