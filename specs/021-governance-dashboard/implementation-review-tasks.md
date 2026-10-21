# Implementation Review: Governance Dashboard (021)

**Review date**: 2026-09-11  
**Source revision**: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a` (HEAD verified by read-only Git query)  
**Scope**: Specification 021 only. Static implementation and test-source review.  
**Report status**: Static review complete; 100/100 original tasks accounted for and 28 open follow-ups.
**Report validation finalized**: 2026-09-14. Task IDs, original checkbox states, local evidence links,
line bounds, and editor diagnostics checked; product execution and external approvals remain unverified.

## Review Boundary and Inputs

This report follows the complete [Review Contract](../001-spec-implementation-audit/README.md#L13).
Only this report may be written. No source, original tasks, original evidence, audit index, branches,
or commits are changed. No other audits or delegated reviews are performed. No product tests,
builds, imports, browser sessions, development servers, cloud queries, or deployments are run.
Report validation is limited to text structure, identifiers, original checkbox preservation in the
coverage table, existing link targets and line bounds, and editor diagnostics for this file.

Fully read specification inputs:

- [Specification, acceptance scenarios, edge cases, clarifications, and later persona/hypothesis/scope additions](spec.md#L1).
- [All original tasks and execution notes](tasks.md#L1).
- [Plan, constitutional mapping, binding conflict resolutions, and ten-role widget mapping](plan.md#L1).
- [All research decisions R-001 through R-013](research.md#L1).
- [Domain entities, view models, retention, and container strategy](data-model.md#L1).
- [Complete API contract](contracts/governance-dashboard-api.yaml#L1).
- [Governance checklist CHK001 through CHK090](checklists/governance.md#L1).
- [Original 16-item requirements checklist](checklists/requirements.md#L1).
- [Quickstart and implementation-completion claims](quickstart.md#L1).
- [Associated developer documentation](../../docs/governance-dashboard.md#L1).
- [Constitution, including its amendment history](../../.specify/memory/constitution.md#L1).
- [HYP-019's linked portfolio baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L1)
and the relocated [portfolio post-feature snapshot](../028-capstone-alignment/evidence/rubric-postfeature.md#L1).
- [Section-scoped executive KPI replacement record](../../docs/governance-hub/executive-kpi/surface.md#L27).

Evidence statuses are used literally: **IMPLEMENTED** means inspected source supports the full
scoped behavior or authored artifact, not runtime success; **PARTIAL** means a specific obligation
is absent or contradicted; **MISSING** requires a stated scoped search; **CONFLICT** requires an
explicit contract resolution; **UNVERIFIED** covers execution, outcomes, approvals, or deployed
state not established by records; **SUPERSEDED** requires an explicit replacement record.
Checked tasks and matching mocks are not runtime evidence. Human sign-offs remain UNVERIFIED
unless a dated, attributable record is found.

## Static Trace and Search Scope

The actual entry path is [AppShell navigation](../../packages/ui/src/components/layout/app-shell.tsx#L6),
[the governance redirect](../../apps/web/src/app/governance/page.tsx#L25),
[dashboard layout](../../apps/web/src/app/governance/dashboard/layout.tsx#L20), the six dashboard
pages, and [the typed client](../../apps/web/src/lib/api/governance.ts#L277).
[Next.js rewrites](../../apps/web/next.config.ts#L28) forward requests to the API;
[the API router](../../apps/api/app/api/router.py#L91) mounts the dedicated dashboard router.
The [application composition](../../apps/api/app/main.py#L25) installs authentication, tenant,
production-auth, and audit middleware. The actual default API prefix is
[/api](../../apps/api/app/core/settings.py#L10), not the contract's /api/v1.

The controlling data path is [the dashboard factory](../../apps/api/app/api/routes/governance_dashboard.py#L71)
to [SeedService](../../apps/api/app/services/seed_service.py#L1),
[GovernanceDataService](../../apps/api/app/services/governance_data_service.py#L52), and
[DashboardAggregationService](../../apps/api/app/services/dashboard_aggregation_service.py#L41).
It does not inject the [governance repository](../../apps/api/app/repositories/governance_repository.py#L29).
Existing [assessment/gap logic](../../apps/api/app/services/governance_registry.py#L363),
[operational state](../../apps/api/app/services/state_store.py#L16),
[emergency-plan storage](../../apps/api/app/repositories/emergency_plan_repository.py#L28), and
[incident recovery tracking](../../apps/api/app/services/recovery_service.py#L58) were checked as
nearby alternative owners. Their existence does not connect them to this dashboard or prove
their deployed state. Remediation must adapt these interfaces with tenant authorization, not
blindly treat all existing stores as safe live-data providers.

Negative-search boundaries:

- All files under this feature folder were inventoried and read. No separate local amendment,
review, or execution-evidence files were present; amendments are embedded in the specification.
- Dashboard pages, governance components, the API client, and all web source were searched for
role/config/polling/tenant/telemetry component usages and CRUD-navigation audit actions.
- Dashboard routes, services, repositories, validators, domain models, middleware, and Python
tests were searched for relocated dashboard queries, cache calls, validators, and audit writers.
- All repository dependency manifests matching pyproject, requirements, or uv.lock were searched
for ReportLab. It was absent. No package installation was attempted.
- Infrastructure, workflows, scripts, and tools were searched for the dashboard module reference,
governance-exports, audit-exports, and health-score-history. Only the standalone Bicep module
contained the latter infrastructure definitions; no deployment composition reference was found.
- Web route files were searched for recovery/catalogue alternatives; the promised catalogue URL
was not found. Existing recovery and utility/insurance-sector pages do not implement that URL.
- Feature-linked evidence and local attestation/accessibility/testing/governance-hub records were
searched for this feature and HYP-019/PER-055/PER-056/PER-057. The exact hypothesis stub was not
found. The two portfolio rubric documents are not per-021 consultation or measured validation.

Relocation credit: role-widget configuration exists
[inside the router](../../apps/api/app/api/routes/governance_dashboard.py#L88), not in the historical
dashboard_config model path. The [UI export map](../../packages/ui/package.json#L19) resolves the
lowercase health-score-gauge import to its existing PascalCase file. Existing assessment history
is available on [the linked legacy page](../../apps/web/src/app/governance/[dataSourceId]/compliance/page.tsx#L25),
but the new inline panel does not use it. The broader suite has an actual
[axe invocation for the summary entry page](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts#L21).
Its [AU badge assertion](../../tests/e2e/web-coverage/cross-cutting/data-sovereignty.spec.ts#L12)
proves only a UI assertion exists, and its
[recovery evaluator assertions](../../tests/e2e/web-coverage/cross-cutting/recovery-environments.spec.ts#L29)
do not inspect this dashboard's five-domain results. No other specification audit was performed.

## Prioritized Findings and Remediation

Priorities are impact-ordered: P1 security, integrity, and misleading operational information;
P2 completeness, usability, contract, and evidence gaps. IDs are stable identifiers, not sort order.
Validation profiles and fixture recipes below apply to every task; all commands are future-only.

### P1: The application does not authorize dashboard requests from trusted AIIMS claims

- [ ] AUD-021-002 Enforce authenticated, role-authorized access on every dashboard endpoint.

**Obligations**: FR-024, FR-025, FR-026; US7-AS1 through US7-AS4; no-role and revocation edges;
T013, T017, T037, T081, T083, T085, T090; CHK046, CHK047, CHK049, CHK067, CHK073, CHK083.

**Expected / actual / impact**: Authentication and valid AIIMS assignments must govern server reads,
details, exports, and status polling. [Role resolution](../../apps/api/app/api/routes/governance_dashboard.py#L467)
instead trusts X-User-Roles/X-User-Role; only config rejects an empty role list, and unknown nonempty
roles resolve to an empty layout with a successful config response. Other handlers have no role
dependency. [Legacy auth](../../apps/api/app/middleware/auth_middleware.py#L22) supplies anonymous
default claims. Both [Entra](../../apps/api/app/middleware/entra_auth.py#L37) and
[RBAC](../../apps/api/app/middleware/rbac_check.py#L32) protected-prefix lists omit governance/dashboard.
Thus application-layer dashboard authorization is not established even by enabling production-auth.
External ingress authentication, if deployed, is UNVERIFIED and cannot substitute for per-operation
role authorization. No unauthorized runtime request was made in this audit.

**Developer**: Protect the mounted dashboard route family using validated principals and canonical
AIIMS assignment resolution. Ignore untrusted identity/role headers; fail closed for absent, expired,
malformed, unknown, or revoked assignments. Make 401/403 responses contract-consistent. Carry the
trusted identity into exports and audit records. Cover direct detail/status URLs independently of
the UI; preserve authorized read-only access for all ten original roles.

**Tester positive**: Authenticated fixtures for each original role and a multi-role principal may
access only their permitted views. **Negative**: missing/invalid/expired bearer credentials,
forged role headers, unknown roles, and revoked assignments cannot read data or create exports.
**Edge**: production-auth on/off and direct deep links must not silently introduce an anonymous
production mode. Extend [API integration tests](../../tests/integration/test_governance_dashboard_api.py#L235)
with AUTH fixtures and V-API; assert 401/403 and no data/job/audit-success side effect, not an
allowed set of success-or-denial codes. **Dependencies / completion**: none for initial enforcement;
coordinate AUD-021-003 and AUD-021-012. Complete with trusted-principal tests at the mounted app
boundary and attributable future execution evidence.

### P1: Simulation context and export-job ownership are not enforced end to end

- [ ] AUD-021-003 Enforce tenant scope on every dashboard read, job, cache, and visible context.

**Obligations**: FR-026A, FR-026, FR-027; simulation/live and revocation edges; T013, T014, T023,
T037, T051, T052, T055, T085, T090; R-007; CHK046 through CHK054, CHK083.

**Expected / actual / impact**: The trusted session must resolve live or its authorized simulation.
[Composition](../../apps/api/app/main.py#L55) installs TenantMiddleware without a simulation
repository; [its resolver](../../apps/api/app/middleware/tenant_middleware.py#L47) therefore reaches
live on dashboard paths. [Principal extraction](../../apps/api/app/core/auth.py#L17) does not extract
a simulation tenant claim. The route has an [X-Tenant-Id fallback](../../apps/api/app/api/routes/governance_dashboard.py#L475)
when state is absent, but in the mounted default path state normally exists and is live. Do not
misdescribe that fallback as proof that the mounted app honors arbitrary tenant headers.
Data-service methods accept tenant_id but use common seed lists; optional repository calls omit
tenant filtering. [Job lookup](../../apps/api/app/api/routes/governance_dashboard.py#L752) receives no
request, principal, or tenant and retrieves the global job by ID alone. TenantBanner is not mounted.
This permits scope confusion and lacks object authorization; current stored/deployed exposure was not tested.

**Developer**: Resolve simulation membership from trusted claims/session state; reject ambiguous or
unauthorized context instead of silently falling back to live. Require tenant scope at repository,
aggregation, cache, export creation/status/download, and audit boundaries. Verify job owner as well
as tenant. Mount the persistent simulation banner from config and clear data on scope changes.
Never add a client-selectable tenant switcher as the fix.

**Tester positive**: AUTH and DATA fixtures with the same entity/job IDs in live and two simulations
return only the principal's records. **Negative**: forged tenant parameters, other-user job IDs,
other-tenant tokens, and simulation-only principals cannot read live data. **Edge**: mid-session
scope change/revocation clears old rows and suppresses late responses. Extend
[tenant-context tests](../../tests/unit/test_tenant_context.py#L4) and
[mounted API tests](../../tests/integration/test_governance_dashboard_api.py#L35), using V-SERVICE,
V-API, and V-WEB. Assert differing tenant fixture values, mandatory scoped queries, matching banner,
and rejected foreign job access, not merely presence of tenant_id.
**Dependencies / completion**: AUD-021-002 precedes data activation; AUD-021-004/010/012/014 must
preserve this boundary. Complete when every endpoint and storage read has negative isolation coverage.

### P1: Bundled reference data is reported as current governance health

- [ ] AUD-021-004 Connect dashboard composition to authoritative, explicitly scoped data providers.

**Obligations**: FR-001, FR-002, FR-003, FR-005, FR-013 through FR-023; SC-004, SC-005, SC-009;
T014, T033, T036, T044, T051, T062, T069, T075; assumption of read-accessible data; CHK001,
CHK024, CHK052, CHK085, CHK086, CHK087.

**Expected / actual / impact**: Live governance changes must drive displayed values. The
[factory](../../apps/api/app/api/routes/governance_dashboard.py#L71) always loads packaged seed data
and passes no repository. [The data service](../../apps/api/app/services/governance_data_service.py#L55)
indexes those shared catalogues. [Gates](../../apps/api/app/services/governance_data_service.py#L77)
are inferred from counts/configuration, with assessment dates manufactured as yesterday; gate 8
uses data-source count, not infrastructure assessment. [Incident/risk counts and utilisation](../../apps/api/app/services/governance_data_service.py#L303)
are fixed zero or organisational-capability ratios rather than operational metrics. Source availability
is treated as compliance. This can conceal incidents, failures, and actual governance changes behind
plausible scores. Matching seed fixtures do not establish live data.

**Developer**: Inject explicit authorized read providers for assessments, source registry, incidents,
resources, readiness, warnings/risks, and recovery. Reuse the existing owners identified above, with
adapters and freshness/provenance contracts; do not create a parallel writable governance store.
Separate reference catalogues, valid empty operational results, and unavailable live data. Preserve
per-source observation timestamps and fail visibly when a required provider is disconnected.

**Tester positive**: DATA fixtures intentionally differ from bundled seeds; changing an assessment,
incident, assignment, or tracker changes the corresponding view without restarting the process.
**Negative**: absent/unavailable providers must not yield seed-derived live compliance. **Edge**:
valid empty stores, partial records, mixed observation dates, and tenant-identical IDs remain distinct.
Extend [aggregation tests](../../tests/unit/test_dashboard_aggregation.py#L6) and
[API tests](../../tests/integration/test_governance_dashboard_api.py#L25), V-SERVICE/V-API.
**Dependencies / completion**: AUD-021-002/003 first; domain-specific AUD-021-005/006/008/016/017/018
define metric semantics. Complete with populated-provider assertions and visible unavailable states;
production connectivity and measurements still need separately authorized evidence.

### P1: Export jobs do not export selected records or produce stored download files

- [ ] AUD-021-001 Restore real, provenance-preserving audit exports.

**Obligations**: FR-012, FR-027; US3-AS4, US8-AS3; concurrent-export edge case;
T002, T006, T010, T049, T050, T052, T055, T058, T059, T094; R-005 and R-011;
CHK005, CHK027, CHK035, CHK069, CHK072, CHK083.

**Expected versus actual / impact**: Selected or filtered authorized audit records must become
downloadable PDF, CSV, or JSON files with provenance intact. The routed endpoint instead invokes
[processing with an empty list](../../apps/api/app/api/routes/governance_dashboard.py#L738).
The worker discards generated content and constructs a
[storage URL without an upload](../../apps/api/app/services/audit_export_service.py#L86);
[PDF generation returns placeholder bytes](../../apps/api/app/services/audit_export_service.py#L129).
Consequently source does not implement the claimed download artifact, record scope, or regulatory
reporting fidelity. This is a source-supported defect, not a claim that a download was attempted.

**Search scope / owning surfaces**: The mounted governance-dashboard route, its imported
AuditExportService, and the existing export unit and dashboard API integration tests were inspected.
The finding concerns this direct call chain, not similarly named simulation export implementations.

**Developer instructions**: Resolve selected IDs or validated filters against the authorized audit
store; retain that selection in a durable job; implement actual PDF rendering and complete CSV/JSON
provenance serialization; store generated bytes before marking a job complete. Return an authorized,
expiring download reference and a complete job response. Preserve the read-only governance boundary.
Use a durable per-user queue with bounded admission, failure handling, and 24-hour export expiry;
do not confuse disposable export files with seven-year audit-record retention. Job retrieval and
downloads must enforce authenticated ownership and tenant scope, not possession of a job ID.

**Tester instructions**: Extend the existing
[export service tests](../../tests/unit/test_audit_export_service.py#L26) and
[API export tests](../../tests/integration/test_governance_dashboard_api.py#L129).
Positive: distinct selected and filter-matched records, all three parseable formats, actual stored
bytes, and every provenance field. Negative: foreign-tenant/foreign-owner IDs, upload/render failure,
and invalid filters must not yield a successful download. Edge: no matches, Unicode and multiline
values, heterogeneous record fields, maximum selection, queue saturation, process restart, and
expiry. Existing [PDF assertions](../../tests/unit/test_audit_export_service.py#L52) check only
`complete`, so they do not establish PDF validity or storage.

**Future validation / prerequisites**: In a separately authorized test run, use the repository's
prepared Python test environment with controlled audit/job/blob doubles for unit coverage, then
isolated storage for persistence integration. From the repository root, run:

```text
python -m pytest tests/unit/test_audit_export_service.py tests/integration/test_governance_dashboard_api.py -k export -v
```

Expected assertions: exact selected IDs and count, valid PDF structure, no lost provenance, readable
uploaded content, truthful state transitions, enforced owner/tenant checks, and expiry behavior.
No command in this section was executed during the audit.

**Dependencies / completion**: Requires trusted identity, tenant-scoped audit reads, contract-aligned
job fields, and provisioned export storage. Complete only when those behaviors are implemented and
the above future checks produce attributable evidence; a non-null URL or mocked `complete` is insufficient.

### P1: Health-score calculations disagree with the binding algorithm and missing-data task

- [ ] AUD-021-005 Reconcile and enforce health-score semantics, configuration, and invariants.

**Obligations**: FR-001, FR-002; US1-AS1; incomplete/all-missing-data edges; T004, T029, T032,
T035, T036; R-004; configurable-weight assumption; CHK001, CHK020, CHK074.

**Expected / actual / impact**: The four outer weights and traffic-light derivation exist, and pending
gates are excluded from the denominator. However, [readiness scoring](../../apps/api/app/services/health_score_service.py#L130)
averages three inputs equally instead of 30/30/20/20 with capability gaps; data-source scoring uses
partially compliant rather than grace-period counts; recovery averages every supplied domain,
including overarching, and missing recovery contributes 100. The
[test explicitly expects 15 for all-missing data](../../tests/unit/test_health_score_service.py#L99),
contradicting T032's zero target. All stale flags are false, and weights/thresholds have no
administrator configuration in this path. [Model validation](../../packages/domain/src/domain/models/governance_health_score.py#L40)
checks totals but not distinct dimensions, each product, or status consistency.

**Developer**: Adopt R-004's subweights and four-concrete-domain rule; define known-no-recovery
separately from unknown recovery. Obtain an explicit resolution for the all-missing case rather
than editing assertions to match the implementation. Validate four distinct dimensions, products,
sum, ranges, and traffic light consistently, and wire validated administrative settings. Propagate
source stale flags and counted evidence, not unconditional false values.
**Tester positive**: unequal DATA dimension inputs must match a hand-calculated oracle; test the
50/80 boundaries and partial/pending gates. **Negative**: duplicate dimensions, false status,
inconsistent products, invalid weights, and unassessed data must not manufacture credit.
**Edge**: all missing, all pending, no active recovery, missing concrete domain, and one stale input.
Use [model tests](../../tests/unit/test_governance_health_score_model.py#L57) and
[algorithm tests](../../tests/unit/test_health_score_service.py#L8), V-MODEL/V-SERVICE.
**Dependencies / completion**: AUD-021-004 and AUD-021-027's ambiguity decision. Complete with
nonuniform oracle assertions, explicit unknown semantics, and configuration-boundary coverage.

### P1: Populated audit searches cannot construct the declared response model

- [ ] AUD-021-008 Repair audit search mapping, filtering, and stable pagination across the full trail.

**Obligations**: FR-009, FR-010, FR-027; US3-AS1/AS2, US8-AS4; T014, T017, T050, T051, T053,
T056, T059; R-001/R-006; CHK028, CHK029, CHK030, CHK031, CHK035.

**Expected / actual / impact**: Nonempty results require id, action_type, affected_entity, outcome,
and provenance. [The mapper](../../apps/api/app/services/dashboard_aggregation_service.py#L266)
supplies event_id/action/entity_type/entity_id/summary instead of required fields in
[AuditEventSummary](../../apps/api/app/models/governance_health.py#L74). The current no-repository
path returns [], hiding the mismatch. Even if connected, [the adapter](../../apps/api/app/services/governance_data_service.py#L691)
ignores actor and keyword and queries only affected_entity or the empty-string source. Repository
queries are source-partitioned, not tenant-wide paginated searches. The UI omits affected-entity
input and provenance output, offers only two dashboard action types, and
[next-page handling drops filters](../../apps/web/src/app/governance/dashboard/audit/page.tsx#L94).

**Developer**: Map stored provenance to the declared result schema; apply all six filters to the
authorized population with stable ordering and continuation tokens. Preserve filters/selection
through URL state, pagination, and export. Render provenance and all six dashboard action choices.
Define date-only input boundaries and timezone conversion explicitly; do not silently reset invalid tokens.
**Tester positive**: AUDIT fixtures contain multiple actors/actions/entities, equal timestamps, and
more than 50 rows; every filter combination and subsequent page returns exactly the expected IDs
and count. **Negative**: nonmatching/foreign records never appear, malformed ranges/tokens reject
predictably. **Edge**: empty results, Unicode keywords, inclusive end date, concurrent append,
changed search with stale selection. Extend [API tests](../../tests/integration/test_governance_dashboard_api.py#L96),
[contract tests](../../tests/contract/test_governance_dashboard_contract.py#L103), and
[browser tests](../../tests/e2e/governance-dashboard.spec.ts#L79), V-API/V-SERVICE/V-WEB.
**Dependencies / completion**: AUD-021-002/003/004/022. Complete with nonempty model construction,
exact filter/page assertions, full provenance, and separately measured 2s/5s behavior.

### P1: Decision-chain retrieval is an unconditional empty response

- [ ] AUD-021-009 Retrieve real decision chains and distinguish missing, incomplete, and unverifiable evidence.

**Obligations**: FR-011; US3-AS3; T051, T054, T057, T059; CHK024, CHK027, CHK028, CHK032.

**Expected / actual / impact**: The timeline should connect trigger, approvals, final action, rationale,
and evidence integrity. [get_decision_chain](../../apps/api/app/services/dashboard_aggregation_service.py#L296)
always returns an empty chain for any supplied ID, so the route's not-found branch is ineffective.
[The timeline component](../../apps/web/src/components/governance/dashboard/AuditDecisionChain.tsx#L29)
can display real steps, but has none from this source; the search model defaults has_decision_chain=false.
Investigators cannot reconstruct decisions or distinguish absent records from incomplete chains.

**Developer**: Join authorized audit/correlation/evidence records into ordered steps and check root
existence before returning 404. Set chain_complete only when required trigger/action evidence exists;
return incomplete chains honestly and derive integrity from verifiable evidence, not display defaults.
**Tester positive**: AUDIT fixtures include trigger, two timestamped approvers, final action, rationale,
and verified hashes. **Negative**: unknown or foreign roots return 404/denial, and altered evidence
never reports verified. **Edge**: pending approval, missing external step, duplicate timestamps,
and unavailable verifier preserve partial evidence. Extend
[decision-chain integration assertions](../../tests/integration/test_governance_dashboard_api.py#L118)
and [browser suite](../../tests/e2e/governance-dashboard.spec.ts#L79), V-API/V-WEB.
**Dependencies / completion**: AUD-021-003/008/010. Complete with ordered populated chains, truthful
integrity/complete flags, actionable not-found behavior, and provenance-preserving UI display.

### P1: Required dashboard interaction auditing is not wired to the platform trail

- [ ] AUD-021-010 Emit and retrieve complete dashboard interaction records, including completed exports.

**Obligations**: FR-027, SC-008; all US8 scenarios; T007, T086, T087, T088, T089, T090;
R-002/R-010/R-011; CHK025, CHK030, CHK034, CHK035, CHK036, CHK050, CHK087.

**Expected / actual / impact**: Six action kinds and full actor/role/view/parameters/result-count/session
provenance are required. The [domain enum exists](../../packages/domain/src/domain/models/governance_audit.py#L6),
but the dashboard handlers never append those events. [Generic middleware skips GET](../../apps/api/app/middleware/audit_appender.py#L90)
and sends POST records to [audit-events](../../apps/api/app/repositories/audit_repository.py#L42),
with a different shape and no dashboard selection/result details. It uses X-Correlation-Id, whereas
the dashboard client sends X-Session-Id. The dashboard searches the separate governance trail.
[T087 assertions](../../tests/integration/test_governance_dashboard_api.py#L294) only inspect HTTP
success, not emitted records. An auditor therefore cannot verify all interactions through this view.

**Developer**: Append typed interaction events after meaningful view/filter/search/detail outcomes,
before confirmed CRUD navigation, and after export completion with actual scope/format/count.
Use trusted identity and roles, tenant, anonymous session correlation, and deliberate handling of
failed/retried actions. Integrate the resulting records into the searchable trail without recursive
self-auditing loops. Specify durable retry/outage behavior; logging exceptions alone is not capture.
**Tester positive**: AUTH/AUDIT fixtures produce all six action kinds with exact persisted fields
and searchable results. **Negative**: denied requests cannot be logged as successful; telemetry must
not receive actor PII. **Edge**: duplicate polling, retries, export failure, writer outage, and audit
search itself do not lose or recursively amplify records. Extend
[audit unit tests](../../tests/unit/test_dashboard_audit_logging.py#L8) and
[integration tests](../../tests/integration/test_governance_dashboard_api.py#L294), V-SERVICE/V-API/V-WEB.
**Dependencies / completion**: AUD-021-002/003/008/011/020. Complete with persisted-record assertions,
export-completion provenance, a documented outage policy, and recorded coverage of every interaction.

### P1: Dashboard audit retention and immutable archival are not implemented on its storage path

- [ ] AUD-021-011 Implement the agreed audit-record retention and archival lifecycle separately from exports.

**Obligations**: FR-027 and immutable-audit assumption; plan/R-011 retention; T007, T052, T088,
T093, T094, T096; CHK025, CHK026, CHK033, CHK036, CHK087.

**Expected / actual / impact**: Compliance records require seven-year retention; dashboard interactions
require 90-day hot retention and archive through seven years. [Governance audit writes](../../apps/api/app/repositories/governance_repository.py#L456)
use upsert, while the alternative [AuditRepository](../../apps/api/app/repositories/audit_repository.py#L92)
uses create but is not the dashboard read path. Neither inspected path implements the promised
dashboard TTL/archive handoff. The Bicep 90-day TTL concerns health-score-history, not interaction
archival. Source alone cannot establish deployed immutability policies or seven-year retention.

**Developer**: Choose the platform append-only trail with tenant-aware dashboard integration; reject
record replacement, implement durable archive-before-expiry with reconciliation/retry, and retain
compliance versus operational classes for their agreed periods. Preserve provenance and authorized
historical search. Do not delete audit records using the disposable-export lifecycle rule.
**Tester positive**: AUDIT fixtures age across 90 days and remain recoverable through archival.
**Negative**: duplicate-ID replacement and archive-write failure must not overwrite or prematurely
expire evidence. **Edge**: retry, replay, legal retention boundary, clock skew, and partial archival
completion remain idempotent. Extend [audit logging tests](../../tests/unit/test_dashboard_audit_logging.py#L8)
and [API tests](../../tests/integration/test_governance_dashboard_api.py#L294), V-SERVICE/V-API;
then separately authorized storage-policy validation with versioned evidence.
**Dependencies / completion**: AUD-021-003/010/025/027. Complete only with enforced storage semantics,
archive reconciliation tests, approved retention interpretation, and actual policy evidence.

### P1: Readiness metrics represent catalogue coverage rather than operational readiness

- [ ] AUD-021-016 Derive readiness from plan lifecycles, exercises, role assignments, and PPRR context.

**Obligations**: FR-013, FR-014, FR-015, FR-016; all US4 scenarios; T060 through T066;
R-004/R-012; CHK006, CHK007, CHK017, CHK064, CHK075, CHK085.

**Expected / actual / impact**: [The data service](../../apps/api/app/services/governance_data_service.py#L322)
counts framework phases, organisational functions, and catalogue version fields. It returns six
functions rather than the ten required AIIMS roles; review-overdue counts stay zero. Exercise
completion derives from framework review metadata and assignment counts, with
[last_date always null](../../apps/api/app/services/dashboard_aggregation_service.py#L443).
Overall readiness equals role coverage rather than a complete readiness measure. The UI displays
seven plan-state counts but no per-plan overdue days, latest exercise date, or overall score.
Actual staffing and expired plans can therefore remain concealed by reference-data proxies.

**Developer**: Read PPRR contexts, current assignments, emergency-plan lifecycle/review dates,
exercise outcomes by type, and capability gaps from authorized providers. Cover all seven states
and ten roles; keep expired as an overlay for any state and handle UTC plus Australian display
time correctly. Show assigned/required, overdue days, last exercise date, and overall readiness.
Reuse [plan storage](../../apps/api/app/repositories/emergency_plan_repository.py#L84) and
[operational state interfaces](../../apps/api/app/services/state_store.py#L16) through scoped adapters.
**Tester positive**: READINESS fixtures vary staffing, exercise types/dates, phases, and all seven
plan states. **Negative**: a catalogue-only plan or organisation must not count as an active role
assignment/exercise completion. **Edge**: review due now/null, AEDT transition, superseded overdue
plan, zero exercises, understaffed versus unassigned roles, and overlapping PPRR phases.
Extend [readiness unit tests](../../tests/unit/test_dashboard_aggregation.py#L65) and
[integration tests](../../tests/integration/test_governance_dashboard_api.py#L160), V-SERVICE/V-API/V-WEB.
**Dependencies / completion**: AUD-021-003/004/005/013/015. Complete with exact metric oracles and
UI assertions for dates, days overdue, ten role identities, and the full readiness score.

### P1: Recovery reports an active programme even when the data service says none exists

- [ ] AUD-021-017 Implement incident-scoped recovery progress, truthful empty states, and complete details.

**Obligations**: FR-017, FR-018, FR-019, SC-009; all US5 scenarios; multi-incident edge;
T067 through T072; R-013; CHK008, CHK009, CHK066, CHK077.

**Expected / actual / impact**: [The service reports no active recovery](../../apps/api/app/services/governance_data_service.py#L730),
yet [get_recovery_domains](../../apps/api/app/services/governance_data_service.py#L491) always emits
four zero-percent domains with 100% targets. The aggregator creates an INC-LATEST row and sets
[has_active_recovery from row existence](../../apps/api/app/services/dashboard_aggregation_service.py#L523).
It does not enumerate/filter real incident trackers; arbitrary incident IDs relabel the same values.
Overarching is numerically averaged but trend is fixed stable, and detail derives catalogue labels
with zero/not-assessed values. The UI renders only outcomes/activities, not community/M&E results;
the empty-state catalogue URL has no matching web route in the searched route tree.

**Developer**: Use [actual recovery tracker semantics](../../apps/api/app/services/recovery_service.py#L58)
and M&E/catalogue definitions through authorized adapters. Enumerate real active/recent programmes,
choose the documented most recent one, and support incident-specific and agreed cross-incident
aggregation. Compute progress, trajectory, and trends from measured values; roll four concrete
domains into overarching cross-cutting outcomes. Return empty domains/404 detail when no programme
exists, and render all four detail sections with a valid catalogue destination.
**Tester positive**: RECOVERY fixtures have two incidents with unequal outcomes, positive/negative
variance, trends, qualitative/quantitative indicators, and M&E evidence. **Negative**: unknown or
foreign incidents do not synthesize records; catalogue presence alone is not active recovery.
**Edge**: no programmes, missing domain measurements, concurrent incident switch, stale detail
response, and overarching weighting remain truthful. Extend
[recovery unit tests](../../tests/unit/test_dashboard_aggregation.py#L91) and
[API tests](../../tests/integration/test_governance_dashboard_api.py#L184), V-SERVICE/V-API/V-WEB.
**Dependencies / completion**: AUD-021-003/004/015/022/027. Complete with actual incident IDs,
five-domain or explicit-empty invariants, measured trends, all details, and working empty-state navigation.

### P1: Risk and warning metrics are constants or trust-tier proxies

- [ ] AUD-021-018 Derive risk, treatment, warning latency, reach, and principle compliance from records.

**Obligations**: FR-020, FR-021, FR-021A, FR-022, FR-023; all US6 scenarios; T073 through T076;
warning-threshold assumption; CHK037, CHK038, CHK040, CHK042, CHK043, CHK045, CHK071.

**Expected / actual / impact**: Risk counts/top risks are fixed zero/empty; treatment closure is zero.
[Alert metrics](../../apps/api/app/services/dashboard_aggregation_service.py#L620) fix latency to zero,
threshold to 120, violations empty, tier counts/reach zero. Every principle uses the same
[data-source trust-tier ratio](../../apps/api/app/services/governance_data_service.py#L590), not warning
assessments, and failing-warning IDs are always empty. [Risk detail](../../apps/api/app/services/dashboard_aggregation_service.py#L641)
fabricates unknown severity/treatments for any ID. This can falsely indicate no severe risks or
latency breaches while genuine records exist elsewhere.

**Developer**: Aggregate authorized risk assessments/treatment histories and warning approval,
delivery, AWS-tier, and per-principle assessment records. Respect the configured warning threshold,
define reach/denominators and observation windows, rank open extreme/high treatments first with
owner/due date, and return 404 for absent risks. Preserve unknown/unassessed as distinct from zero
and avoid inferring warning compliance from publisher trust.
**Tester positive**: WARNING fixtures include all tiers/severities, open/closed/overdue treatments,
different principle failures, and alerts on both sides of the configured threshold.
**Negative**: trusted publishers with noncompliant warnings are still failures; unknown/foreign risks
do not return synthetic details. **Edge**: zero eligible warnings, one slow alert despite a low
average, missing approval, duplicate deliveries, and exact-threshold equality.
Extend [risk unit tests](../../tests/unit/test_dashboard_aggregation.py#L134) and
[API tests](../../tests/integration/test_governance_dashboard_api.py#L212), V-SERVICE/V-API.
**Dependencies / completion**: AUD-021-003/004/027. Complete with record-level oracles, genuine
failed-warning IDs, config-driven thresholds, and populated risk treatment/history assertions.

### P2: Compliance detail, grace information, and gap counts do not use the existing assessments

- [ ] AUD-021-006 Join real compliance history, remediation, grace periods, and audit references.

**Obligations**: FR-005, FR-006, FR-008; US2-AS1/AS2/AS4; T008, T042, T043, T044, T046,
T047, T048; CHK004, CHK070, CHK076, CHK085.

**Expected / actual / impact**: [Seed entries](../../apps/api/app/services/governance_data_service.py#L623)
are all pending, have zero gaps, and use now as last assessment. The optional repository branch
reads updated_at, not assessed_at, and does not call the existing gap detector. [Detail retrieval](../../apps/api/app/services/dashboard_aggregation_service.py#L193)
returns empty history/remediation/audit arrays even for found rows, and invents a pending source
for unknown IDs. The table shows only remaining days, omitting grace reason/expiry; the inline panel
renders history JSON only. [Existing history/gap logic](../../apps/api/app/services/governance_registry.py#L149)
was located, so this is disconnected behavior rather than absence of the platform feature.

**Developer**: Join current/history assessments and remediation to registered sources; derive gap
counts from the agreed detector and assessment dates from assessment records. Resolve the duplicate
grace_period_end/expiry representation and retain reasons. Return 404 on nonexistent/deactivated
detail according to an explicit policy. Render history date/assessor/result/notes, remediation
status/due dates, audit links, expiry, reason, and countdown without a raw JSON-only panel.
**Tester positive**: DATA fixtures include multiple assessment revisions, two gaps, and active grace
with reason/expiry. **Negative**: unknown IDs, offline lookup, and unrelated source audit records do
not appear as successful pending detail. **Edge**: expiry at now, less than one day left, null next
review date, and deregistration while detail is open. Extend
[compliance unit tests](../../tests/unit/test_dashboard_aggregation.py#L42) and
[API tests](../../tests/integration/test_governance_dashboard_api.py#L68), V-SERVICE/V-API/V-WEB.
**Dependencies / completion**: AUD-021-003/004/008/015/022. Complete with exact joined fields,
meaningful missing-source behavior, and all required detail/grace UI assertions.

### P2: Compliance sorting, date filtering, and pagination lose the user's query

- [ ] AUD-021-007 Make compliance filtering and pagination complete, stable, and URL-driven.

**Obligations**: FR-007; US2-AS3; T014, T017, T042, T043, T044, T045, T047, T048;
R-006; CHK003, CHK076, CHK080.

**Expected / actual / impact**: The route has no assessment-date range and defaults to no sort;
[in-memory sorting](../../apps/api/app/services/dashboard_aggregation_service.py#L122) uses raw
attribute names, not the contract's name/next_due_date/gap_count aliases. Mixed null/datetime sort
keys are not normalized; invalid/negative offsets are accepted or reset. The
[page drops sort on pagination](../../apps/web/src/app/governance/dashboard/compliance/page.tsx#L48),
stores no URL query, and replaces rows for a button labeled Load more. Category options omit
registered kinds such as iot/field_report/social. Non-compliant rows are not automatically most-overdue-first.

**Developer**: Implement bounded date/category/status filters, documented aliases/directions, null
ordering, deterministic tie-breakers, and real server continuation tokens scoped to the query and
tenant. Preserve sort/filter state in the URL and across pages; either append for Load more or use
truthful page navigation. Expose every supported category and define overdue ordering explicitly.
**Tester positive**: DATA contains more than two pages, duplicate names/dates, each category, and
distinct overdue dates. **Negative**: malformed/foreign-query tokens and unsupported sort values
return defined errors rather than silently broadening results. **Edge**: null dates, date boundaries,
filter reset after paging, browser back/forward, and records added during traversal.
Use [compliance tests](../../tests/unit/test_dashboard_aggregation.py#L42),
[integration tests](../../tests/integration/test_governance_dashboard_api.py#L77), V-SERVICE/V-API/V-WEB.
**Dependencies / completion**: AUD-021-003/006/022/027. Complete when every page preserves the exact
query and each source appears once in the expected order with accurate totals.

### P2: Personalisation configuration is unconsumed and incomplete for the original role catalogue

- [ ] AUD-021-012 Wire role-based landing, full widget sets, restricted views, and role-change refresh.

**Obligations**: FR-024, FR-025, FR-026; SC-001, SC-010; all US7 scenarios; T005, T018,
T080 through T085; plan role mapping; CHK010, CHK011, CHK057, CHK067, CHK073.

**Expected / actual / impact**: The [router's relocated role map](../../apps/api/app/api/routes/governance_dashboard.py#L88)
and authority-ordered union logic exist. Several original widget sets are incomplete, including
task/staging/supply-chain/exercise/gap/assessment-history metrics. [RoleWidgetGrid](../../apps/web/src/components/governance/dashboard/RoleWidgetGrid.tsx#L15)
also exists, but the all-web-source usage search found only its definition. Config fetch and
TenantBanner are likewise unconsumed. The [layout](../../apps/web/src/app/governance/dashboard/layout.tsx#L20)
always exposes the six tabs and the same executive landing, with no restricted-role message.

**Developer**: Consume trusted config before presenting authorized data, resolve all ten original
role layouts and their actual data-backed widget implementations, and land on each mapped view.
Preserve ordered widget union for multi-role users and authorized manual navigation. Refresh role
context and clear forbidden data when assignments change. Preserve compatible later role additions
only through an explicit contract extension; do not remove them merely to match an old filename.
**Tester positive**: AUTH role matrix checks exact default view, widget IDs/order, and two-step
access for each original persona. **Negative**: no-role/unknown-role users see restricted guidance
and no protected widgets. **Edge**: duplicate/multi-role assignments, revoked primary role, delayed
config, and missing widget implementation must not silently hide an expected metric.
Extend [config tests](../../tests/unit/test_dashboard_config.py#L10) and
[browser suite](../../tests/e2e/governance-dashboard.spec.ts#L10), V-SERVICE/V-API/V-WEB.
**Dependencies / completion**: AUD-021-002/003/004/013/018/019. Complete with all ten exact mappings,
rendered data-backed widgets, denial coverage, and role-change transitions without stale exposure.

### P2: Polling is fixed at five minutes on summary and absent from other automatic views

- [ ] AUD-021-013 Apply server-configured per-view polling, manual refresh, and context revalidation.

**Obligations**: FR-029, FR-026A; SC-004, SC-005; US7-AS4; T022, T037, T040, T041,
T048, T059, T066, T072, T079, T085; R-003; CHK013, CHK053, CHK063, CHK073.

**Expected / actual / impact**: [Summary polling](../../apps/web/src/app/governance/dashboard/page.tsx#L42)
hard-codes 300000 ms. Risk/readiness/compliance/recovery load once. The existing
[polling hook](../../apps/web/src/lib/api/governance.ts#L452) has no callers, and config hard-codes
intervals/TTL while its incident detector always sees the stub zero. No page revalidates roles or
tenant context. Users may keep obsolete data and permissions beyond the required refresh cycle.

**Developer**: Use R-003's view policy: summary/risk 30s during active incidents, steady views 5min,
audit search manual-only; make validated operational settings effective. Revalidate trusted context
on refresh, support manual bypass on every view, cancel superseded requests, and avoid overlapping
timers or late-response overwrites. Do not implement a client tenant selector.
**Tester positive**: OUTAGE/AUTH fixtures change active-incident state and assert 30s/5min/manual
behavior with a controlled clock. **Negative**: disabled polling and manual-only audit must not issue
automatic data searches. **Edge**: rapid role/tenant changes, interval changes, in-flight requests,
manual refresh during polling, and unmount. Extend
[API config tests](../../tests/integration/test_governance_dashboard_api.py#L235) and
[browser suite](../../tests/e2e/governance-dashboard.spec.ts#L112), V-API/V-WEB.
**Dependencies / completion**: AUD-021-003/004/012/014/015. Complete when refresh headers, schedules,
context clearing, and per-view visible updates satisfy one-cycle assertions.

### P2: Dashboard cache helpers are disconnected and cache headers describe no cache operation

- [ ] AUD-021-014 Integrate tenant/view cache semantics with truthful headers and invalidation.

**Obligations**: FR-029; SC-004, SC-005; T015, T034, T036, T038, T041; R-003/R-004;
CHK014, CHK052, CHK063, CHK065.

**Expected / actual / impact**: [Cache helpers](../../apps/api/app/services/governance_cache.py#L50)
support TTL/bypass but have no dashboard callers. [Summary](../../apps/api/app/api/routes/governance_dashboard.py#L568)
always computes and labels MISS or BYPASS solely from the header, never HIT. Cached seed loading
is not governance-result caching. The required tenant keys, five-minute TTL, local manual bypass,
and active-incident freshness guarantees therefore are not implemented together.

**Developer**: Invoke the cache from the controlling aggregation path with tenant/view/query/version
keys; report HIT/MISS/BYPASS from actual behavior. Honor supported Cache-Control directives and
validated TTL settings. Define invalidation so five-minute storage does not hide active updates
required in one 30-second cycle; manual bypass must not flush unrelated users' valid data.
**Tester positive**: DATA/OUTAGE fixtures and controlled clocks assert MISS then HIT, expiry, and
manual bypass with provider-call counts. **Negative**: tenant/filter collisions and stale entries
cannot be served as current. **Edge**: exact TTL boundary, recovery after outage, simultaneous refresh,
and changed active data. Extend [existing cache test home](../../tests/integration/test_governance_cache.py#L21)
with dashboard cases; current tests exercise handoff chains only. Run V-CACHE/V-API in the future.
**Dependencies / completion**: AUD-021-003/004/013/015/027. Complete with header/provider-count
assertions, isolation, version invalidation, and an approved TTL-versus-freshness interpretation.

### P2: Freshness and failure displays do not preserve honest per-widget last-known-good state

- [ ] AUD-021-015 Implement per-source degradation, trustworthy timestamps, and actionable retry.

**Obligations**: FR-030, FR-031; SC-007; US1-AS3/AS4; all/half-backend outage edge;
T019, T020, T021, T034, T036, T038, T040; CHK014, CHK036, CHK056, CHK065, CHK074, CHK076.

**Expected / actual / impact**: [Summary freshness](../../apps/api/app/services/dashboard_aggregation_service.py#L116)
is request time rather than oldest observation. Other view models lack per-source freshness.
[WidgetErrorBoundary](../../apps/web/src/components/governance/dashboard/WidgetErrorBoundary.tsx#L20)
records error time as last-known data and retries only render state. It cannot catch swallowed
fetch rejections. Most pages suppress errors without retry; only summary keeps prior data and a
generic banner. The data adapter can turn repository failures into []/seed data without a degraded flag.

**Developer**: Carry observation time, source availability, stale state, and last-known-good values
from each provider. Isolate failures so unaffected widgets continue updating. Return the agreed
degraded response with safe source identifiers/timestamps; connect retry to data retrieval, not
just rerender. Keep navigation and explicit unavailable/empty distinctions on every view.
**Tester positive**: OUTAGE fixtures make one of four sources fail while three advance, then recover.
**Negative**: all failures cannot stamp old data as fresh or show successful empty results.
**Edge**: 50% outage, first load with no prior data, stale cache, absent/invalid timestamp, removed
detail record, and retry failure. Extend [API suite](../../tests/integration/test_governance_dashboard_api.py#L25)
and [browser suite](../../tests/e2e/governance-dashboard.spec.ts#L10), V-API/V-WEB.
**Dependencies / completion**: AUD-021-004/013/014/022. Complete when each widget shows its true
age, source-specific failure/retry, preserved values, and recovery without losing navigation.

### P2: Risk/warning detail interactions and persona metrics stop at summary display

- [ ] AUD-021-019 Complete risk treatments, failed-warning drill-down, and PIO metric displays.

**Obligations**: FR-021A, FR-022, FR-023, FR-024; US6-AS3/AS4, US7-AS2; T077, T078,
T079, T082, T084; CHK039, CHK040, CHK041, CHK045.

**Expected / actual / impact**: [WarningCompliancePanel](../../apps/web/src/components/governance/dashboard/WarningCompliancePanel.tsx#L21)
never consumes alerts_exceeding_threshold or non_compliant_warning_ids; principles are noninteractive
divs. Multilingual and accessibility percentages are literal 0%. The
[risk detail panel](../../apps/web/src/app/governance/dashboard/risk/page.tsx#L75) renders only severity,
likelihood, and consequence, omitting treatments/history/audit URLs. Presentational added authority
and hazard selectors do not drive data, but new filtering capabilities are not independently
required here; do not count them as delivered metric filtering.

**Developer**: Wire actionable principle rows to failing warnings and their specific failed principles;
show each over-threshold alert and actual approval time. Render risk treatments/history/audit links.
Source PIO multilingual/accessibility indicators from measured records, or expose unavailable status.
Keep tier tokens and text labels, without repurposing publisher metadata as warning evidence.
**Tester positive**: WARNING fixtures include distinct failures and nonzero PIO metrics; keyboard
selection opens the correct warning/risk details. **Negative**: compliant warnings never appear in
failure lists; absent metrics cannot display an asserted 0% observation. **Edge**: one slow alert
under a low mean, no failures, missing treatment owner, changed selection, and unavailable detail.
Extend [risk browser test home](../../tests/e2e/governance-dashboard.spec.ts#L105) and
[API risk suite](../../tests/integration/test_governance_dashboard_api.py#L212), V-API/V-WEB.
**Dependencies / completion**: AUD-021-008/018/023. Complete with asserted record IDs, actual times,
all treatment fields, functioning audit links, and no static metric placeholders.

### P2: Dashboard-to-CRUD navigation skips the required confirmation and audit intent

- [ ] AUD-021-020 Guard dashboard-origin governance-action navigation without adding inline mutations.

**Obligations**: FR-028, FR-027; SC-012; T089, T088; R-002; CHK012, CHK035, CHK068.

**Expected / actual / impact**: The binding plan resolves read-only versus state changes as confirmed,
audited navigation to existing CRUD. The [compliance table](../../apps/web/src/components/governance/dashboard/ComplianceMatrix.tsx#L129)
links directly to [the assessment page](../../apps/web/src/app/governance/[dataSourceId]/compliance/page.tsx#L57).
That page mounts [AssessmentForm](../../apps/web/src/components/governance/AssessmentForm.tsx#L69),
which submits to [the assessment endpoint](../../apps/api/app/api/governance.py#L117) and
[registry persistence](../../apps/api/app/services/governance_registry.py#L111). No dashboard-origin
interstitial or dashboard_navigate_to_crud emitter was found. This finding is about the missing
021 navigation safeguard, not a claim that clicking the link itself mutates data.

**Developer**: Identify dashboard links with governance-action intent; confirm target and intent,
log the trusted navigation action before redirect, and route to the existing approval workflow.
Cancel must leave the user/data unchanged. Navigation confirmation is not server authorization;
do not add new inline governance mutation endpoints or treat a UI dialog as approval of a later write.
**Tester positive**: DATA/AUTH fixture selects reassessment, confirms once, produces one intent row,
and arrives at the existing target. **Negative**: cancel/denial produces no navigation or mutation.
**Edge**: double click, keyboard activation, unavailable audit writer, and role revocation before
confirmation. Extend [browser suite](../../tests/e2e/governance-dashboard.spec.ts#L72) and
[audit integration suite](../../tests/integration/test_governance_dashboard_api.py#L294), V-WEB/V-API.
**Dependencies / completion**: AUD-021-002/010/023. Complete with cancel/confirm/audit-ordering
assertions and a verified handoff to, not replacement of, the existing approval boundary.

### P2: Summary indicators do not lead to their promised domain details

- [ ] AUD-021-021 Make every summary indicator an authorized, context-preserving drill-down.

**Obligations**: FR-004, FR-002; US1-AS2; SC-001; T018, T039, T040; CHK003, CHK023, CHK058.

**Expected / actual / impact**: Health/incident/resource/risk summary widgets are static containers
in [the executive page](../../apps/web/src/app/governance/dashboard/page.tsx#L92). Gates have links,
but their /compliance?gate=N destination is not read by the compliance page or API. Breadcrumbs are
absent. Users cannot reach the relevant gate or summary-domain evidence as specified.

**Developer**: Define authorized destinations for every indicator, preserve tenant/query context,
implement meaningful gate detail filtering, and supply breadcrumbs/back behavior. Reuse existing
domain pages where appropriate rather than inventing disconnected detail placeholders.
**Tester positive**: DATA fixture activates each summary indicator by pointer and keyboard and
asserts destination plus selected domain/gate. **Negative**: unauthorized/missing targets expose
safe guidance, never unrelated records. **Edge**: browser back, multiple roles, empty metrics, and
deep-link restoration. Extend [navigation tests](../../tests/e2e/governance-dashboard.spec.ts#L30),
V-WEB with API-backed fixtures. **Dependencies / completion**: AUD-021-006/008/012/020/023/027;
complete with every destination mapped and the agreed two-step journeys asserted.

### P2: The published contract and validators disagree with the routed interface

- [ ] AUD-021-022 Reconcile contract/model drift and enforce request and response constraints.

**Obligations**: FR-005 through FR-012, FR-017, FR-023, FR-026; T004, T005, T006, T008,
T009, T010, T016, T017, T030, T031, T045, T050, T055, T068; CHK049, CHK069, CHK083, CHK088.

**Expected / actual / impact**: [The contract](contracts/governance-dashboard-api.yaml#L1) declares
/api/v1, sort_order and aliases, event_ids, export format/requested_at/record_count/expiry,
compliance current_status, and risk id/current_treatments. The implementation uses /api, sort_dir,
record_ids, a smaller [job response](../../apps/api/app/models/audit_export.py#L16), compliance_status,
and risk_id/treatments. Contract/data model require five recovery rows even for an empty state;
implementation permits 0..5 without an active/empty invariant. The extra field_coordinator role is
absent from the closed contract. [Validators](../../apps/api/app/validators/governance_validators.py#L74)
are not invoked; dates use raw fromisoformat, filter enums/tokens/count limits are not enforced,
and action_type validation is absent. DataSource.governance_gap_count lacks ge=0, and export
state-transition checks are advisory rather than enforced.

**Developer**: Resolve intentional compatibility differences explicitly and adopt one canonical
wire contract, with transitional aliases where needed. Validate formats, timezone-aware ordered
ranges, action/sort/category enums, page tokens, maximum selections, and job state-dependent fields
before work starts. Correct error envelopes and recovery active/empty invariants; validate negative
gap counts and invalid transitions. Preserve historical callers through a documented migration.
**Tester positive**: compare actual populated responses for all 13 routes with the checked-in
contract, including headers and errors. **Negative**: malformed dates, reversed/mixed-timezone
ranges, unsupported enums, >10000 selected records, negative gaps, queued download URLs, and invalid
transitions fail explicitly. **Edge**: empty recovery, extra compatible roles, aliases, null sort
keys, and absent optional fields. Extend [contract suite](../../tests/contract/test_governance_dashboard_contract.py#L1),
[export model tests](../../tests/unit/test_audit_export_model.py#L10), and V-MODEL/V-API.
**Dependencies / completion**: AUD-021-001/003/005/007/008/017/027. Complete with actual contract
validation rather than merely instantiating the same implementation models with matching fixtures.

### P2: Accessibility and 375px usability are incomplete, not proven by the current browser suite

- [ ] AUD-021-023 Complete chart alternatives, keyboard/focus behavior, and small-viewport layouts.

**Obligations**: FR-032, FR-033, FR-033A; SC-011; T024 through T027, T040, T047, T058,
T064, T071, T077, T078, T092, T099; R-009; CHK059, CHK081, CHK082.

**Expected / actual / impact**: Health/recovery companion tables, gauge ARIA text, gate focus styles,
and [AWS tokens](../../packages/ui/src/styles/tokens.css#L46) are real source positives. Resource and
treatment progress bars and warning visualizations lack required companion tables. Sortable table
headers are [pointer-only](../../apps/web/src/components/governance/dashboard/ComplianceMatrix.tsx#L103).
[The export dialog](../../apps/web/src/components/governance/dashboard/AuditExportDialog.tsx#L27)
has dialog attributes but no Escape/focus trap/return-focus behavior; detail close buttons are
unnamed. Dashboard main nests inside AppShell main, and tab roles lack tab keyboard/panel behavior.
Fixed four-phase/four-severity rows and crowded summary controls have no narrow-layout handling;
actual clipping/contrast is UNVERIFIED without rendering.

**Developer**: Give every chart a truthful toggleable semantic table and ARIA summary. Use keyboard
operable sort controls, coherent link-or-tab semantics, a single main landmark, labeled detail
controls, and managed dialog focus/Escape/return. Reflow dense metrics at 375px and contain wide
tables without hiding required information. Preserve severity tokens with non-colour meaning.
**Tester positive**: VIEW fixtures exercise all six populated/error/empty pages, every table toggle,
sort, modal, and detail with keyboard and a screen reader. **Negative**: no focus escape behind a
modal, orphan labels, inaccessible chart, or horizontal page overflow at 375px. **Edge**: long names,
zoom, high counts, zero values, and reduced motion. Extend
[the dashboard suite](../../tests/e2e/governance-dashboard.spec.ts#L129) and credit the existing
[summary axe assertion](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts#L21).
Run future V-WEB plus six-view axe and recorded NVDA/VoiceOver checks; original >=0 table-count
assertions and 10-second visibility waits do not prove AA or performance.
**Dependencies / completion**: AUD-021-006/012/015/017/019/020. Complete with nonvacuous automated
checks, 375px layout evidence, verified contrast, and attributable manual screen-reader sign-off.

### P2: Widget telemetry is an unused console hook and endpoint logs omit required context

- [ ] AUD-021-024 Instrument actual dashboard loads and widgets with a tested audit/telemetry privacy boundary.

**Obligations**: FR-034, FR-035; T090, T097, T098; R-010; CHK034, CHK060, CHK061, CHK084.

**Expected / actual / impact**: [useWidgetTelemetry](../../apps/web/src/lib/api/governance.ts#L499)
has no callers and only console.debug in production; it does not send App Insights events or include
correlation/freshness/tenant type. [Endpoint timing](../../apps/api/app/api/routes/governance_dashboard.py#L49)
logs six successful paths with raw tenant_id, but no status code/cache status/anonymized correlation
or page/widget timing. [Global Azure Monitor setup](../../apps/api/app/main.py#L12) is a conditional
source hook, not evidence these metrics arrive. No telemetry capture proves absence of PII.

**Developer**: Instrument mounted pages, fetches, and widget lifecycles with a defined structured
schema and error outcomes. Emit to the platform telemetry integration using anonymous correlation
and tenant_type; keep actor identity only in the authorized audit trail. Redact/allowlist search
parameters, URLs, and exception fields before instrumentation can export them.
**Tester positive**: VIEW/AUDIT fixtures capture page load, API latency, render time, error rate,
cache status, and freshness once with the required fields. **Negative**: distinctive email/name/
search-text markers and identity headers never reach telemetry. **Edge**: widget retry, failed
export, missing telemetry configuration, and unmount remain nonblocking and do not duplicate events.
Extend [API tests](../../tests/integration/test_governance_dashboard_api.py#L25) and
[browser suite](../../tests/e2e/governance-dashboard.spec.ts#L19), V-API/V-WEB with captured telemetry doubles.
**Dependencies / completion**: AUD-021-003/010/013/015. Complete with schema/PII assertions and later
authorized delivery evidence; this review does not claim an observed PII leak or successful ingestion.

### P2: Infrastructure definitions are uncomposed and disagree with application storage

- [ ] AUD-021-025 Align and compose dashboard storage, indexes, export expiry, and policy evidence.

**Obligations**: T093, T094; R-005/R-006/R-011; FR-012, FR-026A, FR-029; CHK026, CHK047,
CHK069, CHK083, CHK089; plan cloud/quality gates.

**Expected / actual / impact**: [The standalone module](../../infra/modules/governance-dashboard.bicep#L35)
creates governance-dashboard and health-score-history, not the repository's governance container
or the specified governance_audit query indexes. Its composite indexes omit the required four-field
audit, assessment, and source patterns. [Export storage](../../infra/modules/governance-dashboard.bicep#L142)
uses audit-exports with a 90-day rule, while the service constructs governance-exports URLs with
24-hour expiry metadata. No module reference was found in the infrastructure/workflow/script/tool
search. Deployed resources, AU residency, policies, and What-If review are UNVERIFIED.

**Developer**: Reconcile actual containers, partition keys, type discriminators, queries, and indexes;
compose the module through the real deployment entry point. Implement 24-hour disposable export
retention independently of audit archival. Merge account-wide lifecycle rules without destroying
unrelated policies. Follow AVM-first and discovered Azure Policy constraints; retain AU-resident
data stores and least-privilege storage access. Obtain approvals for any necessary raw-resource exception.
**Tester positive**: a future compiled entry-point artifact contains the exact container/index/rule
names used by the adapters. **Negative**: no stale container name, tenantless query index, 90-day
export rule, or unrelated lifecycle-rule deletion. **Edge**: existing account rules, migration of
historical data, parameterized environments, and retention boundaries. Use V-IAC and a separately
approved isolated deployment/What-If review; no cloud command was run here.
**Dependencies / completion**: AUD-021-001/003/008/011/027. Complete with composed IaC, non-destructive
plan evidence, policy/region approval records, and authorized storage integration assertions.

### P2: Existing tests and completion checkmarks do not substantiate the required outcomes

- [ ] AUD-021-026 Strengthen the existing tests and record performance, accessibility, usability, and setup evidence.

**Obligations**: all SCs, all eight story test checkpoints, T029 through T034, T042/T043,
T049/T050, T060/T061, T067/T068, T073/T074, T080/T081, T086/T087, T091/T092, T097, T099,
T100; CHK055, CHK056, CHK058, CHK061, CHK062, CHK078, CHK079, CHK080, CHK084, CHK090.

**Expected / actual / impact**: [Aggregation tests](../../tests/unit/test_dashboard_aggregation.py#L6)
mostly instantiate no-provider services; recovery assertions are conditional and may execute no
assertion for active data. [Contract tests](../../tests/contract/test_governance_dashboard_contract.py#L1)
never load the YAML or validate all 13 responses. [API tests](../../tests/integration/test_governance_dashboard_api.py#L294)
claim audit emission without reading a trail. [Original E2E tests](../../tests/e2e/governance-dashboard.spec.ts#L10)
do not assert actual export/download, measured 3s/2s targets, filters/pagination, or detail content;
some checks are conditional or tautological. A separate summary axe test exists, but not proof of
all six views or manual AA verification. Quickstart's all-100-complete statement is not an execution record.

**Developer**: Repair test assertions alongside the owning fixes; use populated and deliberately
unequal fixtures, explicit denies, real response-schema checks, and observable persisted records.
Keep mock-bound tests labeled as such. Define the measurement workload/network/user methodology,
then commission separate authorized performance, fault-tolerance, usability, screen-reader, and
clean-setup runs. Do not alter historical boxes or invent retrospective test/approval evidence.
**Tester positive**: execute V-MODEL/V-SERVICE/V-API/V-CACHE/V-WEB after prerequisites/fixes and
capture immutable revision/configuration/results. **Negative**: deliberately reintroduce each
scoped stub/omission in isolated mutation checks and ensure its assertion fails. **Edge**: >50 rows,
50% and total outage, multiple users/tenants, long export, 375px, and all ten roles.
For SC-006 record the recruited cohort, task, elapsed times, and numerator/denominator achieving
90% within 30s. For load/search record 3s initial, 1s drill-down, 2s normal/5s degraded search under
the agreed profile. **Dependencies / completion**: all owning remediation tasks plus AUD-021-027;
complete only when nonvacuous coverage and attributable execution/review records satisfy the outcomes.

### P2: Conflicting documentation and unresolved checklist decisions prevent a single acceptance baseline

- [ ] AUD-021-027 Reconcile the feature's contract, documentation, and requirement-quality decisions.

**Obligations**: both original checklists; plan conflict resolutions; R-001 through R-013;
T010, T016, T032, T045, T052, T068, T093 through T100; assumptions; CHK001 through CHK090.

**Expected / actual / impact**: The [developer guide](../../docs/governance-dashboard.md#L11)
lists obsolete endpoints, different role defaults, wrong plan states and AWS principle names,
90-day exports, and different performance targets. [Quickstart](quickstart.md#L126) runs root test
paths from apps/api and names pnpm e2e although the checked-in script is test:e2e; prerequisites
say Python 3.11 while manifests require 3.12, and ReportLab is absent. The requirements checklist
still claims 33 FRs/six edges while the current specification contains 38 FRs/seven edges. All 90
governance items remain unchecked. Some design questions are resolved by the plan; others still
lack measurable criteria or conflict across artifacts.

**Developer**: With the feature owner, record a bounded acceptance baseline and explicit dispositions
for every checklist question. Resolve all-missing score, cache-versus-refresh guarantees, empty
recovery schema, export selection/queue interpretation, and read-only navigation wording. Define
metric populations, configurable limits/owners, gate assessment evidence/frequency, and measurement
profiles where needed. Classify checklist suggestions outside 021 as explicit deferrals, not new
mandatory product features. Correct docs/contracts through a future authorized change without
rewriting historical audit evidence or silently redefining delivered behavior.
**Tester positive**: trace each resolved decision to an FR/task/scenario and an executable assertion
or clearly owned manual evidence gate. **Negative**: contradictory defaults, unmeasurable claims,
or unsupported approvals cannot be marked passed. **Edge**: later compatible roles, section-scoped
executive deprecation, and deferred international scope retain precise ownership.
Use V-RECORDS and future V-API/V-WEB/clean-setup verification, grounded in
[the actual runner](../../apps/web/playwright.config.cts#L3) and
[package scripts](../../apps/web/package.json#L6).
**Dependencies / completion**: feature-owner decisions unblock AUD-021-005/007/011/014/017/022/025/026;
complete with reconciled authored artifacts and separately recorded approvals, not automatic checkbox conversion.

### P2: Later persona and hypothesis claims lack feature-specific supporting evidence

- [ ] AUD-021-028 Resolve the HYP-019 evidence reference and qualify persona/consultation claims.

**Obligations**: PER-055, PER-056, PER-057, HYP-019, SCP-061, SCP-062, SCP-063; associated
review/sign-off claims; [later additions](spec.md#L289).

**Expected / actual / impact**: The spec labels AU cross-referenced personas validated and promises
actor consultation plus at least one-band improvement for this spec. The exact linked HYP-HYP-019
stub is absent after the named feature/evidence search. [Baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L1)
and [post-feature rubric](../028-capstone-alignment/evidence/rubric-postfeature.md#L1) are portfolio
structural summaries, not per-021 measured results or records of each actor consultation. The
executive KPI author's sign-off is for that different publication, not this dashboard's delivery.

**Developer**: Ask the owning reviewers to locate existing dated per-021 consultation, persona,
and before/after evidence; repair the reference in a future authorized documentation change or
mark the claim explicitly not yet evidenced. Preserve PH/JP/BD placeholders and SCP preconditions;
do not promote country scope or alter constitutional requirements. A new hypothesis evidence file,
if needed, is a proposed artifact, not existing proof. No delegation occurred in this audit.
**Tester positive**: a future evidence record identifies this spec, revision, criteria, measurement
method, dated reviewers, and actual findings. **Negative**: portfolio means, bare validated labels,
or another publication's sign-off are rejected as feature-specific proof. **Edge**: missing baseline,
regressed criterion, withdrawn approval, and deferred country personas remain explicit.
Use V-RECORDS; no rubric grading, interviews, or consultation executions were performed here.
**Dependencies / completion**: AUD-021-027 and original evidence owners. Complete only with traceable
records or honest unresolved/not-tested labels, without fabricating retrospective approvals.

## Future Validation Profiles and Fixtures

These are instructions for a later authorized implementation/validation agent, not executed commands.
From the repository root, use an already prepared Python 3.12+ environment containing API and test
dependencies; [root pytest configuration](../../pyproject.toml#L42) and
[test import setup](../../tests/conftest.py#L10) define the test home. Isolate credentials/endpoints
and process state so importing the app cannot contact production or initialize real storage.
For HTTP negatives, use controlled trusted-principal fixtures at the real middleware boundary,
not X-User-Role as proof of authentication. Add cases to the named existing test files.

| Profile | Future command or procedure | Prerequisites and expected assertions |
| --- | --- | --- |
| V-MODEL | `python -m pytest tests/unit/test_governance_health_score_model.py tests/unit/test_audit_export_model.py -v` | Prepared local environment; exact arithmetic, invalid products/statuses/counts, state transitions, and terminal-only download fields. |
| V-SERVICE | `python -m pytest tests/unit/test_health_score_service.py tests/unit/test_dashboard_aggregation.py tests/unit/test_audit_export_service.py tests/unit/test_dashboard_config.py tests/unit/test_dashboard_audit_logging.py tests/unit/test_tenant_context.py -v` | Reset controlled stores/clocks; populated unequal fixtures, exact metric/role/tenant results, real writer-call assertions, and negative cases. |
| V-API | `python -m pytest tests/integration/test_governance_dashboard_api.py tests/contract/test_governance_dashboard_contract.py -v` | Isolated providers and trusted auth fixtures; all 13 mounted routes, nonempty contract validation, exact errors/headers/filter/pagination/job/audit assertions. |
| V-CACHE | `python -m pytest tests/integration/test_governance_cache.py -v` | Add dashboard-specific cases to this existing handoff-cache test home; controlled clock, provider-call counts, tenant/query keys, expiry, and truthful headers. |
| V-WEB | `pnpm --filter @ama/web exec playwright test governance-dashboard.spec.ts --project=chromium --project=mobile` | pnpm 10.6.3, installed browser/dependencies, isolated approved API/web servers, BASE_URL matching the runner, and strengthened fixtures/assertions. The runner starts servers and writes artifacts, so it was expressly not invoked in this audit. Assert six views, real selections/download bytes, timed/role/tenant/error journeys, and an explicit 375px case rather than assuming Pixel 7 equals 375px. |
| V-IAC | `bicep build infra/modules/governance-dashboard.bicep --stdout` followed by the composed entry-point build and an explicitly approved What-If/policy review | Bicep CLI/modules available, approved discovered policy/AVM constraints and isolated target selected by owner. Inspect template container/index/lifecycle equality; compilation alone does not prove deployment, AU residency, storage access, or expiry. |
| V-RECORDS | `git log -- specs/021-governance-dashboard docs/governance-dashboard.md` plus human inspection of dated evidence and requirement/checklist traceability | Read-only history inspection and original evidence-owner review. Require revision, scope, actor, methodology, artifacts, and approval record; authored checkmarks and portfolio summaries are not execution proof. |

Fixture names below are proposed test-data recipes to add within the existing homes, not new files
or claimed production records. Each remediation task names its required recipe and exact cases.

| Recipe | Existing home and required contents |
| --- | --- |
| AUTH | [API suite](../../tests/integration/test_governance_dashboard_api.py#L15), [config suite](../../tests/unit/test_dashboard_config.py#L10): all ten original roles, no/unknown/revoked roles, multi-role ordering, live and two simulation principals, same/foreign job owners. |
| DATA | [Aggregation suite](../../tests/unit/test_dashboard_aggregation.py#L6), [governance repository](../../apps/api/app/repositories/governance_repository.py#L134): unequal non-seed values, >100 sources, every category/status, assessments, gaps, grace dates/reasons, and tenant collisions. Do not call production stores. |
| AUDIT | [Audit tests](../../tests/unit/test_dashboard_audit_logging.py#L8), [export tests](../../tests/unit/test_audit_export_service.py#L11): >100 events, multiple actors/actions/entities, all provenance fields, complete/incomplete/tampered chains, distinct selection/filter sets, durable job/blob doubles. |
| READINESS | [Aggregation suite](../../tests/unit/test_dashboard_aggregation.py#L65): all seven plan states, UTC/AEST/AEDT boundaries, actual exercise outcomes/types/dates, ten role identities with under/over/zero staffing, and overlapping phases. |
| RECOVERY | [Aggregation suite](../../tests/unit/test_dashboard_aggregation.py#L91): two real programme IDs, four distinct concrete-domain measures, overarching oracle, trend history, mixed indicators, M&E results, and true empty/unknown variants. |
| WARNING | [Aggregation suite](../../tests/unit/test_dashboard_aggregation.py#L134): all severities/tiers, treatments/history, observed delivery denominators, configurable latency threshold, per-warning principle failures, multilingual/accessibility observations. |
| OUTAGE | [API suite](../../tests/integration/test_governance_dashboard_api.py#L25), [cache home](../../tests/integration/test_governance_cache.py#L21): independently failing providers, unchanged observation times, controlled clocks, zero/half/all outage, recovery, and in-flight context changes. |
| VIEW | [Dashboard browser suite](../../tests/e2e/governance-dashboard.spec.ts#L10): fixtures for populated/empty/error/denied states on all six routes, keyboard/modal interactions, long labels, 375px/desktop/zoom, download validation, and captured telemetry with distinctive PII markers. Mock responses prove UI handling only. |

Coverage accounting below uses the original task states and the contract's source-evidence statuses.

## Original Task Coverage

Every original task is reproduced once below with its exact original checked state. All 100 were
`[x]`; none was changed. IMPLEMENTED on a component/model/test-authoring task credits only that
scoped authored artifact, not its integration or successful execution. End-to-end gaps remain
explicit in the requirement and scenario tables. No historical TDD sequence is established.

| Original task | Original state | Review status | Concrete source/test evidence and remaining obligation | Follow-ups |
| --- | --- | --- | --- | --- |
| [T001](tasks.md#L31) | [x] | IMPLEMENTED | Six page directories and governance/a11y/shared-UI homes exist; [layout](../../apps/web/src/app/governance/dashboard/layout.tsx#L7) and [shared barrel](../../packages/ui/src/components/governance/index.ts#L1) confirm the created structure. | None for directory creation. |
| [T002](tasks.md#L32) | [x] | MISSING | [API dependencies](../../apps/api/pyproject.toml#L10) omit ReportLab; dependency-manifest search found no relocated declaration. uv sync execution is UNVERIFIED. | AUD-021-001, AUD-021-026 |
| [T003](tasks.md#L33) | [x] | IMPLEMENTED | [Governance entry](../../apps/web/src/app/governance/page.tsx#L25) calls router.replace to the new dashboard; [E2E redirect assertion](../../tests/e2e/governance-dashboard.spec.ts#L11) exists, not executed. | AUD-021-026 for execution evidence. |
| [T004](tasks.md#L45) | [x] | PARTIAL | [Health models](../../packages/domain/src/domain/models/governance_health_score.py#L13) validate ranges/list size/totals, but not distinct dimensions, products, or score/status consistency. | AUD-021-005, AUD-021-022 |
| [T005](tasks.md#L46) | [x] | CONFLICT | [Widget models](../../packages/domain/src/domain/models/dashboard_widget_config.py#L10) include the ten roles plus field_coordinator and rank 11; the closed original contract remains ten/rank 1..10. Types/refresh enums exist. | AUD-021-012, AUD-021-022, AUD-021-027 |
| [T006](tasks.md#L47) | [x] | PARTIAL | [Export model](../../packages/domain/src/domain/models/audit_export.py#L14) has format, status, expiry, and filter fields; transitions are a predicate only and terminal-only download/24h constraints are not enforced. | AUD-021-001, AUD-021-022 |
| [T007](tasks.md#L48) | [x] | IMPLEMENTED | [Audit model](../../packages/domain/src/domain/models/governance_audit.py#L6) includes all six dashboard actions and tenant/view/session fields; their emission is assessed separately under T088. | AUD-021-010 for integration. |
| [T008](tasks.md#L49) | [x] | PARTIAL | [DataSource](../../packages/domain/src/domain/models/data_source.py#L35) adds four fields, but gap count lacks ge=0 and grace expiry duplicates the existing end field without a synchronized write path. | AUD-021-006, AUD-021-022 |
| [T009](tasks.md#L53) | [x] | PARTIAL | [View models](../../apps/api/app/models/governance_health.py#L20) exist for all views; compliance/risk naming, recovery invariants, and unconstrained role/detail fields disagree with the design. | AUD-021-008, AUD-021-017, AUD-021-022 |
| [T010](tasks.md#L54) | [x] | CONFLICT | [Export request/response](../../apps/api/app/models/audit_export.py#L8) follows task record_ids/progress wording but not contract event_ids or required format/requested_at fields. | AUD-021-001, AUD-021-022, AUD-021-027 |
| [T011](tasks.md#L55) | [x] | IMPLEMENTED | [Router](../../apps/api/app/api/routes/governance_dashboard.py#L519) declares all 13 operations. Current handlers replace the initial skeleton; initial 501 behavior/history is not claimed. Individual behavior is assessed below. | AUD-021-022 for contract parity. |
| [T012](tasks.md#L56) | [x] | IMPLEMENTED | [API router registration](../../apps/api/app/api/router.py#L91) mounts the router carrying the specified governance/dashboard prefix and tag. | None for registration. |
| [T013](tasks.md#L57) | [x] | PARTIAL | [Tenant middleware](../../apps/api/app/middleware/tenant_middleware.py#L20) sets context, but [composition](../../apps/api/app/main.py#L55) provides no simulation membership resolver and the principal omits simulation claim handling. | AUD-021-002, AUD-021-003 |
| [T014](tasks.md#L58) | [x] | MISSING | [Repository public methods](../../apps/api/app/repositories/governance_repository.py#L29) lack the six required tenant-mandatory dashboard queries and continuation paging; relocated [data service](../../apps/api/app/services/governance_data_service.py#L52) uses seed/global reads, not equivalent behavior. | AUD-021-003, AUD-021-004, AUD-021-007, AUD-021-008 |
| [T015](tasks.md#L59) | [x] | PARTIAL | [Dashboard cache helpers](../../apps/api/app/services/governance_cache.py#L50) exist with default TTL, but no dashboard callers, enforced tenant-key construction, or header-driven bypass at the cache boundary. | AUD-021-014, AUD-021-015 |
| [T016](tasks.md#L60) | [x] | PARTIAL | [Validators](../../apps/api/app/validators/governance_validators.py#L74) define format/count/date checks, but action_type is never checked and helpers are not invoked by the routed dashboard. | AUD-021-007, AUD-021-008, AUD-021-022 |
| [T017](tasks.md#L64) | [x] | PARTIAL | [Typed client](../../apps/web/src/lib/api/governance.ts#L277) covers endpoints, token parameters, and summary no-cache header; errors are plain Error, contract aliases differ, and trusted auth/context integration is absent. | AUD-021-002, AUD-021-003, AUD-021-008, AUD-021-013, AUD-021-022 |
| [T018](tasks.md#L65) | [x] | PARTIAL | [Layout](../../apps/web/src/app/governance/dashboard/layout.tsx#L20) has six tabs and active highlighting, but no config/refresh/tenant integration or breadcrumbs. | AUD-021-003, AUD-021-012, AUD-021-013, AUD-021-021, AUD-021-023 |
| [T019](tasks.md#L66) | [x] | PARTIAL | [Widget boundary](../../apps/web/src/components/governance/dashboard/WidgetErrorBoundary.tsx#L20) catches render errors, mislabels failure time as last-known-data time, and retry does not refetch. | AUD-021-015 |
| [T020](tasks.md#L67) | [x] | PARTIAL | [Freshness badge](../../apps/web/src/components/governance/dashboard/DataFreshnessIndicator.tsx#L17) calculates age on render; only summary uses it and its timestamp is request time, not per-widget observation time. | AUD-021-013, AUD-021-015 |
| [T021](tasks.md#L68) | [x] | IMPLEMENTED | [Degraded banner](../../apps/web/src/components/governance/dashboard/DegradedModeBanner.tsx#L13) renders an alert/list from unavailable-source props. Actual source diagnosis and all-view wiring are separate gaps. | AUD-021-015 for integration. |
| [T022](tasks.md#L69) | [x] | PARTIAL | [RefreshControls](../../apps/web/src/components/governance/dashboard/RefreshControls.tsx#L20) provides controls; summary's parent sends no-cache, but interval is fixed and other views lack controls. | AUD-021-013, AUD-021-014 |
| [T023](tasks.md#L70) | [x] | PARTIAL | [TenantBanner](../../apps/web/src/components/governance/dashboard/TenantBanner.tsx#L14) is non-dismissible and token-styled, but its all-web-source usage search found no mounted caller. | AUD-021-003, AUD-021-012 |
| [T024](tasks.md#L71) | [x] | IMPLEMENTED | [CompanionDataTable](../../apps/web/src/components/governance/a11y/CompanionDataTable.tsx#L21) has sr-only default, toggle, caption, column scope, and controlled region. Not every chart consumes it. | AUD-021-023 for chart-wide integration. |
| [T025](tasks.md#L72) | [x] | IMPLEMENTED | [ARIA utility](../../apps/web/src/components/governance/a11y/ChartAriaLabel.tsx#L38) generates gauge/value/status summaries and is consumed by the health gauge. | AUD-021-023 for all-view verification. |
| [T026](tasks.md#L76) | [x] | IMPLEMENTED | [TrafficLightIndicator](../../packages/ui/src/components/governance/TrafficLightIndicator.tsx#L41) combines icon, text, status role, and accessible name for three states. | AUD-021-026 for execution evidence. |
| [T027](tasks.md#L77) | [x] | IMPLEMENTED | [HealthScoreGauge](../../packages/ui/src/components/governance/HealthScoreGauge.tsx#L126) renders bounded gauge, status text, ARIA label, and dimension companion table; [export map](../../packages/ui/package.json#L19) resolves its import. | AUD-021-005 for displayed formula semantics; AUD-021-023 for verification. |
| [T028](tasks.md#L78) | [x] | IMPLEMENTED | [Shared barrel](../../packages/ui/src/components/governance/index.ts#L1) exports both required components. | None for barrel authoring. |
| [T029](tasks.md#L82) | [x] | IMPLEMENTED | [Model test source](../../tests/unit/test_governance_health_score_model.py#L14) asserts ranges, thresholds, weight/sum rejection, and gate-number bounds. Additional invariant gaps are outside these existing assertions; execution UNVERIFIED. | AUD-021-005, AUD-021-026 |
| [T030](tasks.md#L83) | [x] | PARTIAL | [Export model tests](../../tests/unit/test_audit_export_model.py#L10) check transition predicates and defaults, but the URL-only-when-complete test never supplies a URL on a noncomplete job or enforces transition mutation. | AUD-021-022, AUD-021-026 |
| [T031](tasks.md#L84) | [x] | PARTIAL | [Contract suite](../../tests/contract/test_governance_dashboard_contract.py#L1) constructs implementation models, does not load the OpenAPI file, and omits several detail/error schemas. | AUD-021-022, AUD-021-026 |
| [T032](tasks.md#L100) | [x] | CONFLICT | [Algorithm tests](../../tests/unit/test_health_score_service.py#L99) assert all-missing=15 versus task=0; stale test only expects false. Outer weights/thresholds/pending/no-recovery assertions exist. | AUD-021-005, AUD-021-026, AUD-021-027 |
| [T033](tasks.md#L101) | [x] | IMPLEMENTED | [Summary unit tests](../../tests/unit/test_dashboard_aggregation.py#L6) assert shape, ten gates, four severities, and nonnegative incident count exactly as authored, using no-provider fallback; not live correctness proof. | AUD-021-004, AUD-021-026 |
| [T034](tasks.md#L102) | [x] | PARTIAL | [Summary API tests](../../tests/integration/test_governance_dashboard_api.py#L25) check success/fields but not freshness/cache headers or injected 503 degradation. | AUD-021-014, AUD-021-015, AUD-021-026 |
| [T035](tasks.md#L106) | [x] | PARTIAL | [Health calculation](../../apps/api/app/services/health_score_service.py#L32) implements outer weights/thresholds/pending exclusion; R-004 readiness/grace/concrete-recovery semantics differ. | AUD-021-005 |
| [T036](tasks.md#L107) | [x] | PARTIAL | [Summary aggregation](../../apps/api/app/services/dashboard_aggregation_service.py#L56) composes fields but uses seed/constant providers, no dashboard cache, and request-time freshness. | AUD-021-004, AUD-021-005, AUD-021-014, AUD-021-015 |
| [T037](tasks.md#L108) | [x] | PARTIAL | [Config endpoint](../../apps/api/app/api/routes/governance_dashboard.py#L519) returns fields but reads header roles, resolves default live, hard-codes intervals, and detects incidents from a constant-zero provider. | AUD-021-002, AUD-021-003, AUD-021-004, AUD-021-013 |
| [T038](tasks.md#L109) | [x] | PARTIAL | [Summary endpoint](../../apps/api/app/api/routes/governance_dashboard.py#L568) emits headers/503 but no actual HIT/bypass operation, oldest-observation timestamp, or last-known-good degraded payload. | AUD-021-014, AUD-021-015, AUD-021-022 |
| [T039](tasks.md#L110) | [x] | PARTIAL | [Gate grid](../../apps/web/src/components/governance/dashboard/ConstitutionalGates.tsx#L48) renders statuses/severity/links, but generated gate query is ignored by the destination. | AUD-021-004, AUD-021-021 |
| [T040](tasks.md#L111) | [x] | PARTIAL | [Summary page](../../apps/web/src/app/governance/dashboard/page.tsx#L20) renders widgets/skeletons, but uses a client fetch for summary only, never config, fixed polling, and incomplete per-widget error/freshness/alternatives. | AUD-021-012, AUD-021-013, AUD-021-015, AUD-021-021, AUD-021-023 |
| [T041](tasks.md#L112) | [x] | PARTIAL | [Polling hook](../../apps/web/src/lib/api/governance.ts#L452) has interval/manual logic, but consumes no config itself and has no page callers; active-incident transition remains absent. | AUD-021-013, AUD-021-014 |
| [T042](tasks.md#L128) | [x] | PARTIAL | [Compliance unit tests](../../tests/unit/test_dashboard_aggregation.py#L42) check default page size/filter echo on empty data, not multi-page records, grace countdown, or gap aggregation. | AUD-021-006, AUD-021-007, AUD-021-026 |
| [T043](tasks.md#L129) | [x] | PARTIAL | [Compliance API tests](../../tests/integration/test_governance_dashboard_api.py#L68) assert fields/page-size/200, without content accuracy, detail histories, or unknown-source 404. | AUD-021-006, AUD-021-007, AUD-021-026 |
| [T044](tasks.md#L133) | [x] | PARTIAL | [Matrix/detail aggregation](../../apps/api/app/services/dashboard_aggregation_service.py#L122) uses seed rows/list slicing and empty detail arrays, not assessment/gap joins or Cosmos continuation paging. | AUD-021-003, AUD-021-004, AUD-021-006, AUD-021-007 |
| [T045](tasks.md#L134) | [x] | PARTIAL | [Compliance route](../../apps/api/app/api/routes/governance_dashboard.py#L605) passes status/category/sort/token, but documented aliases/default order/date ranges/validation are incomplete. | AUD-021-007, AUD-021-022 |
| [T046](tasks.md#L135) | [x] | PARTIAL | [Detail route](../../apps/api/app/api/routes/governance_dashboard.py#L636) has a 404 branch that the synthetic fallback never reaches; histories/remediation/audit arrays remain empty. | AUD-021-006, AUD-021-022 |
| [T047](tasks.md#L136) | [x] | PARTIAL | [ComplianceMatrix](../../apps/web/src/components/governance/dashboard/ComplianceMatrix.tsx#L27) renders table/status/category/countdown/row click, but categories, query persistence, and keyboard sort are incomplete. | AUD-021-006, AUD-021-007, AUD-021-023 |
| [T048](tasks.md#L137) | [x] | PARTIAL | [Compliance page](../../apps/web/src/app/governance/dashboard/compliance/page.tsx#L16) fetches client-side without URL state, drops sort on next page, hides failures, and shows raw history without remediation/audit links. | AUD-021-006, AUD-021-007, AUD-021-013, AUD-021-015 |
| [T049](tasks.md#L153) | [x] | PARTIAL | [Export tests](../../tests/unit/test_audit_export_service.py#L11) cover job flags/admission, but never parse PDF/CSV/JSON or inspect stored bytes/provenance. | AUD-021-001, AUD-021-022, AUD-021-026 |
| [T050](tasks.md#L154) | [x] | PARTIAL | [Audit API tests](../../tests/integration/test_governance_dashboard_api.py#L96) check success/shapes, permit 200 or 202, and omit 2s measurement, populated chain, job progression, concurrent 429, and ownership negatives. | AUD-021-001, AUD-021-003, AUD-021-008, AUD-021-009, AUD-021-026 |
| [T051](tasks.md#L158) | [x] | PARTIAL | [Audit aggregation](../../apps/api/app/services/dashboard_aggregation_service.py#L225) has wrong populated-model mapping, local offsets, omitted downstream actor/keyword filters, and unconditional empty chains. | AUD-021-003, AUD-021-008, AUD-021-009 |
| [T052](tasks.md#L159) | [x] | PARTIAL | [Export service](../../apps/api/app/services/audit_export_service.py#L21) stores jobs/counts in memory, discards serializer outputs, has PDF placeholder, no durable queue/upload/SAS, and a fabricated storage URL. | AUD-021-001, AUD-021-003, AUD-021-011, AUD-021-025 |
| [T053](tasks.md#L160) | [x] | PARTIAL | [Audit route](../../apps/api/app/api/routes/governance_dashboard.py#L657) accepts six parameters but does raw date parsing and delegates to incomplete search; 2s outcome UNVERIFIED. | AUD-021-008, AUD-021-022, AUD-021-026 |
| [T054](tasks.md#L161) | [x] | PARTIAL | [Chain route](../../apps/api/app/api/routes/governance_dashboard.py#L696) delegates to a guaranteed empty response; the root-existence/ordered-evidence requirement is absent. | AUD-021-009 |
| [T055](tasks.md#L162) | [x] | PARTIAL | [Export routes](../../apps/api/app/api/routes/governance_dashboard.py#L717) create then process [] synchronously; status lookup is unscoped and initial response reads the stale queued object. | AUD-021-001, AUD-021-003, AUD-021-022 |
| [T056](tasks.md#L163) | [x] | PARTIAL | [AuditTrailSearch](../../apps/web/src/components/governance/dashboard/AuditTrailSearch.tsx#L19) has several filters/selection, but no affected-entity input or provenance column and incomplete dashboard action choices. | AUD-021-008 |
| [T057](tasks.md#L164) | [x] | IMPLEMENTED | [Decision-chain visualizer](../../apps/web/src/components/governance/dashboard/AuditDecisionChain.tsx#L29) renders ordered supplied steps, actor/time/rationale and all integrity badges. Actual retrieval is not delivered by this component. | AUD-021-009, AUD-021-023 |
| [T058](tasks.md#L165) | [x] | PARTIAL | [Export dialog](../../apps/web/src/components/governance/dashboard/AuditExportDialog.tsx#L27) has three formats/scope/progress/download/error controls; parent uses constant progress and a 30-attempt timeout, and focus/Escape handling is absent. | AUD-021-001, AUD-021-023 |
| [T059](tasks.md#L166) | [x] | PARTIAL | [Audit page](../../apps/web/src/app/governance/dashboard/audit/page.tsx#L20) connects components but not URL filters, retains no query on paging, omits export filters, and uses a bespoke finite polling loop. | AUD-021-001, AUD-021-008, AUD-021-009, AUD-021-013, AUD-021-015 |
| [T060](tasks.md#L182) | [x] | PARTIAL | [Readiness unit tests](../../tests/unit/test_dashboard_aggregation.py#L65) inspect no-provider phase/state/role counts, without active phases, UTC/AEST overdue calculations, or real exercise/type/role values. | AUD-021-016, AUD-021-026 |
| [T061](tasks.md#L183) | [x] | PARTIAL | [Readiness API tests](../../tests/integration/test_governance_dashboard_api.py#L160) assert four phases/seven rows but not ten role identities, overdue correctness, or capability values. | AUD-021-016, AUD-021-026 |
| [T062](tasks.md#L187) | [x] | PARTIAL | [Readiness aggregation](../../apps/api/app/services/dashboard_aggregation_service.py#L312) uses catalogue proxies, six functions, zero overdue counts, and assignment-derived exercise rates with no last dates. | AUD-021-003, AUD-021-004, AUD-021-016 |
| [T063](tasks.md#L188) | [x] | PARTIAL | [Readiness route](../../apps/api/app/api/routes/governance_dashboard.py#L771) returns the model but controlling data does not implement ten-role staffing/actual plan and exercise metrics. | AUD-021-016 |
| [T064](tasks.md#L189) | [x] | IMPLEMENTED | [PPRR indicator](../../apps/web/src/components/governance/dashboard/PPRRPhaseIndicator.tsx#L25) renders four phase labels with active/elevated styling and per-phase ARIA states from props. | AUD-021-016 for data; AUD-021-023 for 375px verification. |
| [T065](tasks.md#L190) | [x] | PARTIAL | [EmergencyPlanStatus](../../apps/web/src/components/governance/dashboard/EmergencyPlanStatus.tsx#L25) uses seven named lifecycle states and overdue count overlay, but no individual days-past-due count. | AUD-021-016 |
| [T066](tasks.md#L191) | [x] | PARTIAL | [Readiness page](../../apps/web/src/app/governance/dashboard/readiness/page.tsx#L16) renders phases/plans/rates/gaps/role table, but omits last exercise date/overall readiness score and has one-shot/error-only loading. | AUD-021-013, AUD-021-015, AUD-021-016, AUD-021-023 |
| [T067](tasks.md#L207) | [x] | PARTIAL | [Recovery unit tests](../../tests/unit/test_dashboard_aggregation.py#L91) conditionally assert active rows/average on an inactive no-provider service; no real variance or incident fixtures. | AUD-021-017, AUD-021-026 |
| [T068](tasks.md#L208) | [x] | PARTIAL | [Recovery API tests](../../tests/integration/test_governance_dashboard_api.py#L184) conditionally assert five rows and allow 200 or 404 detail; no incident isolation, M&E content, or invalid-domain assertion. | AUD-021-003, AUD-021-017, AUD-021-022, AUD-021-026 |
| [T069](tasks.md#L212) | [x] | PARTIAL | [Recovery aggregation](../../apps/api/app/services/dashboard_aggregation_service.py#L462) averages four synthetic zero domains, invents INC-LATEST, has fixed trend/target data, and overrides no-active status from row count. | AUD-021-003, AUD-021-004, AUD-021-017 |
| [T070](tasks.md#L213) | [x] | PARTIAL | [Recovery routes](../../apps/api/app/api/routes/governance_dashboard.py#L794) validate domain names but return synthetic/empty details for valid domains without an active recovery and fabricated incident choices. | AUD-021-017, AUD-021-022 |
| [T071](tasks.md#L214) | [x] | IMPLEMENTED | [RecoveryDomainTracker](../../apps/web/src/components/governance/dashboard/RecoveryDomainTracker.tsx#L20) renders supplied percentage/trend/variance/cross-cutting row, keyboard buttons, and companion table. | AUD-021-017 for data; AUD-021-023 for verification. |
| [T072](tasks.md#L215) | [x] | PARTIAL | [Recovery page](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L50) has selector/empty/detail branches but no community/M&E display, valid catalogue destination, polling, or scope-change detail clearing. | AUD-021-013, AUD-021-015, AUD-021-017, AUD-021-023 |
| [T073](tasks.md#L231) | [x] | PARTIAL | [Risk unit tests](../../tests/unit/test_dashboard_aggregation.py#L134) assert nonnegative/percentage/count bounds on zeros, not actual severity totals, threshold violations, principle failures, or returned IDs. | AUD-021-018, AUD-021-026 |
| [T074](tasks.md#L232) | [x] | PARTIAL | [Risk API tests](../../tests/integration/test_governance_dashboard_api.py#L212) check shape and ten principles only; no ordering, treatments/history, or missing-risk 404. | AUD-021-018, AUD-021-019, AUD-021-026 |
| [T075](tasks.md#L236) | [x] | PARTIAL | [Risk aggregation](../../apps/api/app/services/dashboard_aggregation_service.py#L560) uses zero risk/treatment/latency/reach values, fixed threshold, trust-tier principle ratios, and synthetic risk details. | AUD-021-003, AUD-021-004, AUD-021-018 |
| [T076](tasks.md#L237) | [x] | PARTIAL | [Risk routes](../../apps/api/app/api/routes/governance_dashboard.py#L846) exist but cannot meet real metrics or unknown-risk 404 because the service always creates a detail object. | AUD-021-018, AUD-021-022 |
| [T077](tasks.md#L238) | [x] | PARTIAL | [RiskRegisterView](../../apps/web/src/components/governance/dashboard/RiskRegisterView.tsx#L41) has severity/rate/table/click; resulting detail lacks treatment history/audit links and the gauge lacks its table alternative. | AUD-021-019, AUD-021-023 |
| [T078](tasks.md#L239) | [x] | PARTIAL | [Warning panel](../../apps/web/src/components/governance/dashboard/WarningCompliancePanel.tsx#L21) displays ten rates and tier tokens, but no failing-warning actions or individual latency violations; PIO metrics are literal 0%. | AUD-021-018, AUD-021-019, AUD-021-023 |
| [T079](tasks.md#L240) | [x] | PARTIAL | [Risk page](../../apps/web/src/app/governance/dashboard/risk/page.tsx#L18) renders two panels and minimal detail; failed-warning panel, history/links, refresh, and actionable failures are missing. | AUD-021-013, AUD-021-015, AUD-021-019 |
| [T080](tasks.md#L256) | [x] | PARTIAL | [Role tests](../../tests/unit/test_dashboard_config.py#L10) check role existence/some defaults/nonempty sets, but not each exact required widget set, full merge ordering, or restricted response. | AUD-021-012, AUD-021-026 |
| [T081](tasks.md#L257) | [x] | PARTIAL | [Config API tests](../../tests/integration/test_governance_dashboard_api.py#L235) rely on role headers, permit unknown-role 200/403, and do not exercise no-role trusted denial or revocation. | AUD-021-002, AUD-021-003, AUD-021-012, AUD-021-026 |
| [T082](tasks.md#L261) | [x] | PARTIAL | Configuration relocated to [router map](../../apps/api/app/api/routes/governance_dashboard.py#L88); original roles/defaults and authority ranks exist but several complete widget sets are omitted. | AUD-021-012, AUD-021-022 |
| [T083](tasks.md#L262) | [x] | PARTIAL | [Resolver](../../apps/api/app/api/routes/governance_dashboard.py#L483) merges by authority, but [config](../../apps/api/app/api/routes/governance_dashboard.py#L519) reads untrusted role headers and its restricted shape disagrees with contract. | AUD-021-002, AUD-021-012, AUD-021-022 |
| [T084](tasks.md#L263) | [x] | PARTIAL | [RoleWidgetGrid](../../apps/web/src/components/governance/dashboard/RoleWidgetGrid.tsx#L15) sorts supplied widgets and silently skips unmapped IDs, but has no callers or supplied component mapping. | AUD-021-012 |
| [T085](tasks.md#L264) | [x] | MISSING | [Layout](../../apps/web/src/app/governance/dashboard/layout.tsx#L20) does not consume config/widget grid/default view/restricted state; all-web-source usage search found no relocated integration. | AUD-021-002, AUD-021-003, AUD-021-012, AUD-021-013 |
| [T086](tasks.md#L280) | [x] | PARTIAL | [Audit unit tests](../../tests/unit/test_dashboard_audit_logging.py#L8) instantiate enum-bearing objects; do not invoke an emitter or assert actor role/result count/session provenance in persisted records. | AUD-021-010, AUD-021-026 |
| [T087](tasks.md#L281) | [x] | PARTIAL | [Audit integration tests](../../tests/integration/test_governance_dashboard_api.py#L294) assert only HTTP codes and accepted session header, never query or inspect emitted events. | AUD-021-010, AUD-021-026 |
| [T088](tasks.md#L285) | [x] | MISSING | [Dashboard handlers](../../apps/api/app/api/routes/governance_dashboard.py#L568) have no required interaction writers. [Generic middleware](../../apps/api/app/middleware/audit_appender.py#L90) excludes GET and writes a different POST shape/store. | AUD-021-010, AUD-021-011 |
| [T089](tasks.md#L286) | [x] | MISSING | [Direct compliance link](../../apps/web/src/components/governance/dashboard/ComplianceMatrix.tsx#L129) has no interstitial or navigation-audit action; scoped all-web-source search found no relocated guard. | AUD-021-020 |
| [T090](tasks.md#L287) | [x] | PARTIAL | [Client session header](../../apps/web/src/lib/api/governance.ts#L263) uses a lazy UUID for requests, but no role/identity resolution and server audit uses another correlation header. | AUD-021-002, AUD-021-010, AUD-021-024 |
| [T091](tasks.md#L299) | [x] | PARTIAL | [E2E suite](../../tests/e2e/governance-dashboard.spec.ts#L10) contains broad visibility/navigation checks with conditional paths, but no measured targets, export download, correct pagination/filter results, or populated details. | AUD-021-026 |
| [T092](tasks.md#L300) | [x] | PARTIAL | [Original a11y tests](../../tests/e2e/governance-dashboard.spec.ts#L129) do not run axe and permit zero tables; [relocated summary axe test](../../tests/e2e/web-coverage/cross-cutting/accessibility-and-multilingual.spec.ts#L21) covers only the entry page, not all six views/manual screen-reader proof. | AUD-021-023, AUD-021-026 |
| [T093](tasks.md#L304) | [x] | PARTIAL | [Bicep indexes](../../infra/modules/governance-dashboard.bicep#L35) target a new container with different keys; no required audit/assessment/source index triplet or deployment reference was found. | AUD-021-025 |
| [T094](tasks.md#L305) | [x] | CONFLICT | [Export container/lifecycle](../../infra/modules/governance-dashboard.bicep#L142) declares audit-exports/90 days, not governance-exports/24 hours; deployed state UNVERIFIED. | AUD-021-001, AUD-021-025, AUD-021-027 |
| [T095](tasks.md#L309) | [x] | CONFLICT | [Quickstart configuration](quickstart.md#L179) lists environment variables, but setup/test paths/scripts/prerequisites and effective settings disagree with source; verified setup is UNVERIFIED. | AUD-021-013, AUD-021-026, AUD-021-027 |
| [T096](tasks.md#L310) | [x] | CONFLICT | [Developer guide](../../docs/governance-dashboard.md#L11) exists but lists incorrect routes/states/principles/retention/role defaults. Only executive roll-up is explicitly superseded, not this operational guide. | AUD-021-022, AUD-021-027 |
| [T097](tasks.md#L314) | [x] | PARTIAL | [Performance logger](../../apps/api/app/api/routes/governance_dashboard.py#L49) logs duration on six success paths but omits required status/cache/tenant_type fields, error outcomes, and measured target evidence. | AUD-021-024, AUD-021-026 |
| [T098](tasks.md#L315) | [x] | PARTIAL | [Telemetry hook](../../apps/web/src/lib/api/governance.ts#L499) is unused console output, not App Insights JS events with anonymous correlation/freshness/tenant_type. | AUD-021-024 |
| [T099](tasks.md#L316) | [x] | UNVERIFIED | [Checked verification claim](tasks.md#L316) has no dated six-view AA/contrast/screen-reader record in the scoped evidence search; [component defects](../../apps/web/src/components/governance/dashboard/AuditExportDialog.tsx#L27) remain. | AUD-021-023, AUD-021-026 |
| [T100](tasks.md#L317) | [x] | UNVERIFIED | [Quickstart completion assertion](quickstart.md#L239) supplies no clean-environment run record, commands/results, or revision-specific approval; no execution was performed here. | AUD-021-026, AUD-021-027 |

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 021 only. Three parallel technical reviews examined dashboard
authorization, data truthfulness, and UI/API contract surfaces. The source-completable middleware boundary was corrected:
the `/api/governance/dashboard` route family is now included in both Entra authentication and RBAC protection registries.
The recovery empty-state hypothesis was checked and was already represented honestly by the current service, so no edit
was made there.

Validation: `python -m pytest tests/integration/test_rbac_enforcement_036.py -q` returned `15 passed` (2 existing
deprecation warnings).

Remaining open work includes trusted role resolution beyond headers, tenant/simulation scope, export ownership and
durability, dashboard data formulas and degraded states, API contract alignment, polling/cache behavior, accessibility,
telemetry, infrastructure composition, deployment, performance, and human evidence.

