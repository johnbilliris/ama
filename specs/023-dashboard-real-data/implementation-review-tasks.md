# Implementation Review: Governance Dashboard Real Data Integration

**Review date**: 2026-09-11  
**Reviewed revision**: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a` (HEAD matched at inspection)  
**Scope**: Specification 023 only; fresh, isolated, static implementation and test-source audit.  
**Contract**: [Review Contract](../001-spec-implementation-audit/README.md#L12).  
**Delivery assessment**: PARTIAL. The six dashboard views are not established as a stored-data dashboard.

This report is the only file authored by this audit. No branches, commits, index changes, source changes,
original task changes, other audit reports, product tests, builds, application imports, browser sessions,
servers, cloud queries, deployments, or additional agents were performed. Existing untracked audit artifacts
were left untouched. JSON parsing below inspected files; it did not execute the application.

Coverage includes all **81 original tasks**, including T006a and T006b, preserving their **81 unchecked states**;
**28 FRs**, **10 SCs**, **25 numbered acceptance scenarios**, **7 edge cases**, **5 clarification decisions**,
**9 assumptions**, and the **7 appended persona/hypothesis/scope entries**. There are no original NFR-numbered
requirements in this specification. Unnumbered nonfunctional obligations are assessed separately below.
There are **33 open remediation tasks**, all unchecked.

## Evidence Rules and Inputs

IMPLEMENTED means inspected source supports the scoped behavior or authored artifact, not that it ran
successfully. PARTIAL means a specific obligation remains absent or contradicted. MISSING follows a scoped
search for behavior, including renamed implementations. CONFLICT requires an explicit contract decision.
UNVERIFIED denotes unestablished execution, measurement, deployment, or sign-off. SUPERSEDED requires explicit
replacement evidence; no original 023 obligation is silently retired in this report.

### Documents Read in Full

| Input | Scope and evidentiary limit |
| --- | --- |
| [spec.md](spec.md) | Entire specification, six stories, requirements, clarifications, assumptions, success criteria, and appended PER/HYP/SCP sections. |
| [tasks.md](tasks.md) | Entire 81-task list, checkpoints, C1/C2/C3/C4 resolutions, dependencies, implementation strategy, and completion claims. |
| [plan.md](plan.md) | Architecture, performance target, ten declared constitutional PASS gates, and source/test locations. |
| [research.md](research.md) | All eleven research decisions, including fallback, assessment mapping, capability heuristic, and performance estimates. |
| [data-model.md](data-model.md) | All entities, service design, state transitions, validation rules, and contradictory metadata decision. |
| [contracts/dashboard-api.md](contracts/dashboard-api.md) | All thirteen endpoints, consumer compatibility, and error contract. |
| [quickstart.md](quickstart.md) | Entire implementation sequence, test instructions, performance checks, and pitfalls; instructions are not execution evidence. |
| [checklists/requirements.md](checklists/requirements.md) | Sixteen checked quality claims; assessed individually below. |
| [checklists/review.md](checklists/review.md) | All 72 unchecked requirement-review questions; assessed individually below. |
| [Persona contract](../027-spec-hardening/contracts/persona-profile.md) | Defines the validation evidence required by the appended persona claims. |
| [Hypothesis evidence contract](../028-capstone-alignment/contracts/evidence-stub.contract.md) | Defines evidence location, structure, and promotion rules. |
| [Rubric baseline](../028-capstone-alignment/evidence/rubric-baseline.md), [post-feature snapshot](../028-capstone-alignment/evidence/rubric-postfeature.md), [decision record](../028-capstone-alignment/evidence/decision-record.md) | Authored portfolio-wide assessments; not a spec-023 experiment, consultation log, or individual sign-off. |
| [Operational dashboard documentation](../../docs/governance-dashboard.md) | Read fully. Contains older endpoint/lifecycle/threshold descriptions and an executive-KPI consolidation note, not retirement of this operational dashboard. |

The local feature inventory contains nine input files and no separate amendment, execution-evidence, or
implementation-review files. Clarifications and the appended PER/HYP/SCP sections are the local amendments.
The named HYP-HYP-021 evidence file was not found; its absence and replacement search are recorded below.
Applicable code-review instructions and detailed checklists, Python fact-grounded coding guidance, and Cosmos
DB best practices were consulted. Static conclusions are bounded to inspected call paths; interpreter state,
runtime diagnostics, external identity configuration, and live database contents were not established.

### Scoped Replacement and Negative Searches

| Search scope | Result and boundary |
| --- | --- |
| S1: dashboard router, aggregation/data/health/seed services, response models, and references throughout the API application | The planned `compute_*` methods are mostly named `get_*`; aggregation helpers were replaced by direct calls. These naming changes are credited. The sole production construction of the data service supplies seed data, not a repository. |
| S2: governance repository/registry and their route callers; emergency-plan and framework routes/services; recovery service/state store | Current-assessment queries, governance audit storage, real plan CRUD, and in-process recovery state exist elsewhere. They are not wired into the 023 dashboard. Separate read endpoints do not satisfy dashboard integration. |
| S3: dashboard pages/components, typed client, Next.js rewrites, and API middleware/router registration | Traced the six screens to their thirteen endpoint family. No provenance field/badge is delivered on this path. Optional jurisdiction inputs stop at the aggregator; no tenant-aware dashboard client context is supplied. |
| S4: repository-wide governance/dashboard test filenames; literal `GovernanceDataService` search in `tests/**`; all four task-named existing suites and dashboard E2E sources | No dedicated data-service test file or direct data-service reference was found. Existing suites cover the no-service fallback, canned models, the older registry, or response shape. Missing tests are not inferred solely from historical filenames. |
| S5: entire local feature folder, linked feature-028 evidence folder, repository-wide `*HYP*021*` filenames, and 023/HYP references in docs/shared evidence | No HYP-021 replacement evidence stub found. Portfolio snapshots are present but do not establish the spec-specific hypothesis or consultation history. |
| S6: dashboard cache references across the API application | `GovernanceCacheService` has dashboard cache methods, but no inspected production caller uses them. Seed `lru_cache` and the router singleton are the effective data retention mechanisms. |

These scopes apply to the negative findings below. No absence claim is made about every possible deployed
service, external database, or uninspected historical revision. Later claims-velocity, Sendai, help, and
executive-KPI features are not independently audited here and are not used to claim completion of 023.

## Prioritized Findings

| Priority | Finding, expected versus observed, and impact | Follow-up |
| --- | --- | --- |
| P1 | **Tenant isolation must precede storage integration.** The [data service](../../apps/api/app/services/governance_data_service.py#L230) calls `list_sources()` without tenant scope, and [audit reads](../../apps/api/app/services/governance_data_service.py#L691) never pass tenant identity. The [repository](../../apps/api/app/repositories/governance_repository.py#L116) scopes audit reads by source ID, not tenant; assessments have [no tenant field](../../packages/domain/src/domain/models/constitutional_assessment.py#L20). The current seed-only route masks this shared-store risk; this is not a claim that a live cross-tenant leak was reproduced. | AUD-023-001 |
| P1 | **The dashboard application boundary does not enforce authenticated tenant/role access.** [Config](../../apps/api/app/api/routes/governance_dashboard.py#L519) alone checks caller-supplied role headers. [Entra](../../apps/api/app/middleware/entra_auth.py#L37) and [RBAC](../../apps/api/app/middleware/rbac_check.py#L32) protected prefixes omit the dashboard. [Tenant resolution](../../apps/api/app/middleware/tenant_middleware.py#L44) defaults this route family to live with no simulation repository supplied. [Export status](../../apps/api/app/api/routes/governance_dashboard.py#L752) accepts only a job ID. Deployment ingress protection remains UNVERIFIED. | AUD-023-002 |
| P1 | **Stored-data transition is disconnected.** [Router construction](../../apps/api/app/api/routes/governance_dashboard.py#L71) permanently creates `GovernanceDataService(seed_data=...)` without the registry/repositories or request DI. Real assessments, plan changes, risk records, and tracker updates therefore cannot become the dashboard's inputs merely by arriving in storage. | AUD-023-003 |
| P1 | **Constitutional results are heuristics, not current assessments.** [Gate evaluation](../../apps/api/app/services/governance_data_service.py#L77) never queries assessments or RT-007 mappings. It invents yesterday's assessment date. [Empty organisation/framework comparisons](../../apps/api/app/services/governance_data_service.py#L119) can classify gates as compliant with zero evidence; gate 8 equates source count with infrastructure compliance. This can misrepresent the dominant 40% dimension. | AUD-023-004 |
| P1 | **Compliance is not a ten-gate mixed-assessment matrix.** [Entries](../../apps/api/app/services/governance_data_service.py#L623) are one aggregate status per source; a nonempty registry replaces, rather than merges with, unassessed seed sources. No current-assessment matrix is built. [Aggregation](../../apps/api/app/services/dashboard_aggregation_service.py#L122) drops the only `data_source_type` value, so the [table](../../apps/web/src/components/governance/dashboard/ComplianceMatrix.tsx#L114) cannot distinguish stored results from baseline. | AUD-023-005, AUD-023-006 |
| P1 | **A nonempty audit path does not satisfy its response model.** [Construction](../../apps/api/app/services/dashboard_aggregation_service.py#L265) supplies `event_id/action/entity_type/entity_id/summary`, while [AuditEventSummary](../../apps/api/app/models/governance_health.py#L76) requires `id/action_type/affected_entity/outcome`. Empty results conceal this validation defect. A query without a source filter searches source `""`, and actor/keyword filters are ignored. | AUD-023-008, AUD-023-009 |
| P1 | **Audit provenance is neither traversed nor fully produced.** [Decision chains](../../apps/api/app/services/dashboard_aggregation_service.py#L296) are always empty, even for unknown IDs. The [registry](../../apps/api/app/services/governance_registry.py#L32) records source/assessment actions, but [plan transitions](../../apps/api/app/services/emergency_plan_service.py#L123) emit no consumed governance event; [seed import](../../apps/api/app/services/governance_registry.py#L57) does emit registration events. [Cosmos audit append](../../apps/api/app/repositories/governance_repository.py#L456) is an upsert, permitting replacement of a reused audit ID. | AUD-023-010, AUD-023-011, AUD-023-012 |
| P1 | **Risk results remain unconditional empty-state stubs.** [Severity and top risks](../../apps/api/app/services/governance_data_service.py#L582) never query hazard records; [detail](../../apps/api/app/services/dashboard_aggregation_service.py#L641) fabricates an unknown record for any ID. Zero is valid only after establishing no records. [AWS compliance](../../apps/api/app/services/governance_data_service.py#L590) repeats one tier-1 percentage for every principle and reports a denominator of one when there are no warning sources. | AUD-023-013, AUD-023-014 |
| P1 | **Readiness does not reflect persisted plans or jurisdictional capability gaps.** [Plan inference](../../apps/api/app/services/governance_data_service.py#L366) reads nonexistent seed `type` values instead of `framework_type`, never queries plans, and never computes overdue reviews. [Gap analysis](../../apps/api/app/services/governance_data_service.py#L419) compares global hazard unions, not jurisdictional assignments and primary capabilities. [Volunteer output](../../apps/api/app/services/governance_data_service.py#L466) equates every volunteer/mixed organisation with current availability. | AUD-023-015, AUD-023-016, AUD-023-018 |
| P1 | **Recovery fabricates activity and targets while ignoring trackers.** [Four-domain iteration](../../apps/api/app/services/governance_data_service.py#L491) manufactures absent domains and fixed targets; [aggregation](../../apps/api/app/services/dashboard_aggregation_service.py#L462) synthesizes overarching from their average, drops catalogue counts, uses `INC-LATEST`, and sets active recovery from catalogue presence. [Tracker state](../../apps/api/app/services/recovery_service.py#L58) is never consumed. Catalogue indicators lack numeric targets, but [detail](../../apps/api/app/services/governance_data_service.py#L522) substitutes indicator counts as targets and labels every indicator qualitative. | AUD-023-020, AUD-023-021, AUD-023-022 |
| P1 | **Failure and freshness information is not trustworthy.** One malformed domain aborts [bootstrap](../../packages/domain/src/domain/seed/bootstrap.py#L13); only [summary](../../apps/api/app/api/routes/governance_dashboard.py#L568) translates this to 503, with a body different from the contract. Other handlers can reach the [generic 500 handler](../../apps/api/app/middleware/error_handler.py#L209). [Freshness](../../apps/api/app/services/dashboard_aggregation_service.py#L116) is request time, not source time, and manual bypass only changes a header. | AUD-023-023, AUD-023-025 |
| P1 | **The unchanged export claim is not supported.** The [route](../../apps/api/app/api/routes/governance_dashboard.py#L738) processes `[]` regardless of filters or selected IDs. [Export processing](../../apps/api/app/services/audit_export_service.py#L62) discards generated content, has a PDF placeholder, and returns a constructed storage URL without upload. This does not export actual audit data. | AUD-023-027 |
| P1 | **The principal computation tests are absent.** No `GovernanceDataService` test references were found in S4. [Aggregation tests](../../tests/unit/test_dashboard_aggregation.py#L10) use no data service, retain ten-role assertions, and conditionally skip meaningful recovery assertions. [Route tests](../../tests/integration/test_governance_dashboard_api.py#L25) largely prove shape, not provenance, mutation, isolation, or error correctness. | AUD-023-029, AUD-023-030 |
| P2 | **Required detail is lost in response/UI assembly.** PPRR counts become booleans in [readiness assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L323); volunteer jurisdiction/capability counts are dropped; exercise-type percentages are derived from phase assignments, not exercise metadata. [Summary](../../apps/web/src/app/governance/dashboard/page.tsx#L118) labels an organisation-capability ratio as deployed-resource utilisation. | AUD-023-017, AUD-023-018, AUD-023-019, AUD-023-028 |
| P2 | **Drill-down, failure, and paging behavior are incomplete.** [Compliance detail](../../apps/api/app/services/dashboard_aggregation_service.py#L193) returns empty history and invents unknown sources. [Audit pagination](../../apps/web/src/app/governance/dashboard/audit/page.tsx#L99) forgets filters; [compliance paging](../../apps/web/src/app/governance/dashboard/compliance/page.tsx#L48) forgets sorting. Request errors are swallowed by several pages, not caught by render error boundaries. | AUD-023-007, AUD-023-024, AUD-023-026 |
| P2 | **Document and acceptance evidence do not establish completion.** Metadata guidance conflicts; numeric recovery targets are absent; “all gates PASS” and performance figures are design assertions; the HYP evidence link is unresolved. No execution/sign-off was established for T075, T076, T077, personas, or the hypothesis. | AUD-023-031, AUD-023-032, AUD-023-033 |

## Actual Request and Data Paths

The [dashboard layout](../../apps/web/src/app/governance/dashboard/layout.tsx#L7) exposes all six screens.
The [typed client](../../apps/web/src/lib/api/governance.ts#L278) uses `fetch` with `cache: "no-store"`, a session
UUID, and optional cache bypass; it does not add dashboard tenant identity. With a relative API base, the
[Next.js rewrite](../../apps/web/next.config.ts#L28) forwards to the backend; the fallback client base is a direct
localhost URL. The [API router](../../apps/api/app/api/router.py#L91) mounts the dashboard under the configured
API prefix. No query-library cache controls these screens: they use React state and direct requests.

| Contract endpoint | Controlling path and observed source | Assessment |
| --- | --- | --- |
| GET `/config` | [Config handler](../../apps/api/app/api/routes/governance_dashboard.py#L519): static role/widget configuration, seed-based summary, header roles. Static configuration itself is legitimate, not fabricated measurement data. | PARTIAL: route/config shape exists; identity and incident-driven state incomplete. |
| GET `/summary` | [Summary page](../../apps/web/src/app/governance/dashboard/page.tsx#L27) -> client -> [handler](../../apps/api/app/api/routes/governance_dashboard.py#L568) -> [aggregation](../../apps/api/app/services/dashboard_aggregation_service.py#L56) -> seed-only data service -> unchanged health algorithm. | PARTIAL: actual seed derivations coexist with heuristic gates and constant incident/risk/recovery inputs. |
| GET `/compliance` | [Page](../../apps/web/src/app/governance/dashboard/compliance/page.tsx#L22) -> [handler](../../apps/api/app/api/routes/governance_dashboard.py#L605) -> [matrix assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L122) -> seed rows; dormant registry branch. | PARTIAL: rows/filter/paging exist, but no gate matrix, mixed assessment merge, or provenance field. |
| GET `/compliance/{data_source_id}` | [Row drawer request](../../apps/web/src/app/governance/dashboard/compliance/page.tsx#L56) -> [detail assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L193). The name link instead reaches a [separate compliance page](../../apps/web/src/app/governance/[dataSourceId]/compliance/page.tsx#L26) backed by [registry compliance routes](../../apps/api/app/api/governance.py#L107). | PARTIAL: alternate current/history implementation exists; dashboard detail never returns it and does not reject unknown IDs. |
| GET `/audit` | [Page search](../../apps/web/src/app/governance/dashboard/audit/page.tsx#L30) -> [date parsing](../../apps/api/app/api/routes/governance_dashboard.py#L673) -> [assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L225) -> [repository adapter](../../apps/api/app/services/governance_data_service.py#L691). | PARTIAL: production returns empty because no repo; dormant nonempty path has filter and model defects. |
| GET `/audit/{event_id}/chain` | [Page drill-down](../../apps/web/src/app/governance/dashboard/audit/page.tsx#L44) -> [chain method](../../apps/api/app/services/dashboard_aggregation_service.py#L296). | MISSING: no record lookup or traversal, any ID produces an empty incomplete chain. |
| POST `/audit/export` | [Export action](../../apps/web/src/app/governance/dashboard/audit/page.tsx#L53) -> [handler](../../apps/api/app/api/routes/governance_dashboard.py#L717) -> in-memory job + processing of empty list. | PARTIAL: job envelope exists, real export does not. |
| GET `/audit/export/{job_id}` | [Status client](../../apps/web/src/lib/api/governance.ts#L410) -> [handler](../../apps/api/app/api/routes/governance_dashboard.py#L752) -> in-memory job lookup without caller scope. | PARTIAL: known/unknown job lookup exists; tenant ownership and durable artifact unavailable. |
| GET `/readiness` | [Page](../../apps/web/src/app/governance/dashboard/readiness/page.tsx#L20) -> [handler](../../apps/api/app/api/routes/governance_dashboard.py#L771) -> [assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L312) -> framework/org/assignment seed lists. | PARTIAL: some genuine counts; no persisted plan inputs or jurisdictional capability comparison. |
| GET `/recovery` | [Page](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L61) -> [handler](../../apps/api/app/api/routes/governance_dashboard.py#L794) -> [assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L462). | PARTIAL: four baseline domains plus synthetic overarching; active state does not mean an active tracker. |
| GET `/recovery/{domain}` | [Detail request](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L109) -> [handler](../../apps/api/app/api/routes/governance_dashboard.py#L815) -> [catalogue detail](../../apps/api/app/services/governance_data_service.py#L522). | PARTIAL: actual outcome/activity/indicator titles, but no tracker values or meaningful numeric targets; missing valid domain becomes an empty 200 response. |
| GET `/risk` | [Page](../../apps/web/src/app/governance/dashboard/risk/page.tsx#L23) -> [handler](../../apps/api/app/api/routes/governance_dashboard.py#L846) -> [risk assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L560). | PARTIAL: constant severity/empty risks and tier-1 proxy compliance. |
| GET `/risk/{risk_id}` | [Risk click](../../apps/web/src/app/governance/dashboard/risk/page.tsx#L31) -> [handler](../../apps/api/app/api/routes/governance_dashboard.py#L871) -> [detail stub](../../apps/api/app/services/dashboard_aggregation_service.py#L641). | MISSING: neither actual record details nor the required unknown-ID 404. |

### Persistence, Cache, and Provenance Distinctions

- [Seed bootstrap](../../packages/domain/src/domain/seed/bootstrap.py#L42) genuinely reads local JSON, including
  all five catalogue files and evaluation questions. [SeedService](../../apps/api/app/services/seed_service.py#L8)
  caches by resolved path string. This is file-backed reference data, not evidence of persisted operational events.
- [GovernanceRepository](../../apps/api/app/repositories/governance_repository.py#L28) chooses Cosmos when
  configured and otherwise instance-local memory. Its current-assessment query is implemented, but disconnected
  from the dashboard. No Cosmos read or write was executed in this audit.
- [EmergencyPlanRepository](../../apps/api/app/repositories/emergency_plan_repository.py#L28) supplies real
  plan CRUD/query code. [RecoveryService](../../apps/api/app/services/recovery_service.py#L27) currently writes
  trackers to [process-local dictionaries](../../apps/api/app/services/state_store.py#L16), not demonstrated
  durable persistence. Neither feeds the dashboard. The hazard [model](../../packages/domain/src/domain/models/hazard_assessment.py#L18)
  exists; the dashboard has no hazard query path.
- [Dashboard cache methods](../../apps/api/app/services/governance_cache.py#L50) have no production dashboard
  caller in S6. Header `BYPASS`/`MISS` values therefore do not establish cache invalidation or fresh storage reads.
  The summary page polls every five minutes; readiness/risk mount once, while other views refetch on user actions.
- UUIDs for sessions and jobs are generated identities, not randomized measurements. The problematic generated
  values are assessment/freshness timestamps, fixed availability/targets, fabricated detail objects, and export
  URLs. Risk/incident/recovery empty-state constants are valid only after absence of operational records is known.

### Static Seed Facts

These are read-only JSON observations at the reviewed revision, not application response measurements.

| Source | Observed content | Relevance |
| --- | --- | --- |
| [Data sources](../../packages/domain/src/domain/seed/data_sources_australia.json#L1) | 46; all `available` | A seed-only 100% availability calculation is supported; no mixed-status test is supplied by this baseline. |
| [Organisations](../../packages/domain/src/domain/seed/organisations_australia.json#L1) | 49: 25 paid, 16 volunteer, 8 mixed | 24 volunteer/mixed organisations, not a measurement of 24 available or deployed volunteers. |
| [Frameworks](../../packages/domain/src/domain/seed/frameworks_australia.json#L1) | 27; `framework_type`: 16 jurisdictional_policy, 4 communications, 3 agency_specific, 3 other, 1 aiims | No record has `type` or `review_cycle_years`; the plan and national-framework evaluators read the wrong discriminator. |
| [Assignments](../../packages/domain/src/domain/seed/framework_assignments_australia.json#L1) and [jurisdictions](../../packages/domain/src/domain/seed/jurisdictions_australia.json#L1) | 123 assignments; 9 jurisdictions | Counts must remain dynamic, including explicit orphan accounting rather than silent omission. |
| [Overarching](../../packages/domain/src/domain/seed/recovery-catalogue/overarching.json#L1) | 7 outcomes, 20 activities, 22 indicators | It is its own catalogue domain, not merely an average of four others for FR-011. |
| [Social](../../packages/domain/src/domain/seed/recovery-catalogue/social.json#L1) | 24 outcomes, 57 activities, 53 indicators | Matches the specific US3 acceptance fixture. |
| [Economic](../../packages/domain/src/domain/seed/recovery-catalogue/economic.json#L1) | 19 outcomes, 43 activities, 42 indicators | Catalogue structure exists independently of tracker activity. |
| [Built](../../packages/domain/src/domain/seed/recovery-catalogue/built.json#L1) | 5 outcomes, 19 activities, 18 indicators | Same distinction. |
| [Natural](../../packages/domain/src/domain/seed/recovery-catalogue/natural.json#L1) | 6 outcomes, 16 activities, 17 indicators | Same distinction. |
| All five indicator collections | 152 indicators; fields are ID/title/description/methodology/type; zero numeric target fields | FR-012 conflicts with available seed schema. [RecoveryIndicator](../../packages/domain/src/domain/models/recovery_environment_tracker.py#L74) separately has `target_value` and `catalogue_indicator_id`; an approved join/target-source decision is needed. |

## Open Remediation Tasks

All instructions in this section are for a later, explicitly authorized implementation/validation session.
They do not authorize edits or execution during this review. Future validation references FV-01 through FV-09
are defined after the coverage tables. Proposed test paths are identified as proposed, not existing evidence.

- [ ] **AUD-023-001 [P1] Enforce tenant scope throughout dashboard storage access.**
  **Trace**: FR-027; T003, T004, T006, T011, T048, T057, T063, T078.
  **Expected / observed / impact**: Every stored read belongs to the authenticated tenant. Current optional
  repository calls omit tenant filters; source-key partitions and an assessment without tenant identity do not
  provide isolation. Connecting the repository unchanged would expose a shared-store risk.
  **Owners**: [Data service](../../apps/api/app/services/governance_data_service.py#L230),
  [governance repository](../../apps/api/app/repositories/governance_repository.py#L116),
  [assessment model](../../packages/domain/src/domain/models/constitutional_assessment.py#L20).
  **Developer**: Require trusted tenant context on the read adapters and enforce it in both memory and Cosmos
  query/point-read paths. Define migration behavior for records without a tenant; do not treat them as belonging
  to every tenant. Preserve valid shared reference seed data separately from operational tenant records.
  **Tester positive**: Tenant A sees its own assessments, sources, audit events, and linked data.
  **Tester negative**: Tenant B cannot list, count, read by ID, traverse, or export A's data.
  **Tester edge**: Identical source IDs in two tenants, missing tenant on legacy records, interleaved requests.
  **Tests / fixtures**: [Registry fixtures](../../tests/contract/test_governance_dashboard.py#L12),
  [API suite](../../tests/integration/test_governance_dashboard_api.py#L10); extend with two-tenant records and a query spy.
  **Future validation**: FV-01, FV-03, FV-04. **Dependencies / completion**: Coordinate with AUD-023-002;
  must complete before AUD-023-003 enables stored reads; assertions must inspect returned records and query scope.

- [ ] **AUD-023-002 [P1] Protect the dashboard request and export-job boundary.**
  **Trace**: FR-027, FR-025; T004, T006, T078; thirteen-endpoint contract.
  **Expected / observed / impact**: Authenticated identity determines tenant and allowed access. Header-selected
  config roles are not enforcement, production-auth prefixes omit these routes, and export status has no caller.
  **Owners**: [Role/tenant resolution](../../apps/api/app/api/routes/governance_dashboard.py#L467),
  [tenant middleware](../../apps/api/app/middleware/tenant_middleware.py#L20),
  [Entra middleware](../../apps/api/app/middleware/entra_auth.py#L37),
  [client](../../apps/web/src/lib/api/governance.ts#L278).
  **Developer**: Apply existing verified-principal and tenant-membership policy to this endpoint family,
  including job lookup. Carry authorized context through the client/proxy. Do not trust arbitrary tenant,
  actor, or role headers as authentication; preserve test-only identity injection behind explicit guards.
  **Tester positive**: Authorized live and simulation users receive their permitted dashboard and jobs.
  **Tester negative**: Missing identity, forged headers, unknown role, foreign simulation/job are rejected.
  **Tester edge**: Multi-role users, expired identity, tenant switch while a request is outstanding.
  **Tests / fixtures**: [API auth/config fixtures](../../tests/integration/test_governance_dashboard_api.py#L15);
  extend assertions beyond presence of `tenant_id`.
  **Future validation**: FV-04, FV-06. **Dependencies / completion**: AUD-023-001; demonstrate application-boundary
  rejection independently of any unverified cloud ingress configuration.

- [ ] **AUD-023-003 [P1] Wire stored-first, per-request data resolution.**
  **Trace**: FR-005, FR-026, SC-002; T004, T006, T022; RT-002, RT-006, RT-008.
  **Expected / observed / impact**: Stored records supersede seed baselines as they become available. The
  [singleton constructor](../../apps/api/app/api/routes/governance_dashboard.py#L71) supplies only seed data.
  **Owners**: [Router](../../apps/api/app/api/routes/governance_dashboard.py#L71),
  [aggregation constructor](../../apps/api/app/services/dashboard_aggregation_service.py#L44),
  [data constructor](../../apps/api/app/services/governance_data_service.py#L55),
  [existing registry owner](../../apps/api/app/api/governance.py#L60).
  **Developer**: Inject the approved tenant-scoped read adapters through the route dependency boundary. Reuse
  the actual write stores, not fresh unrelated in-memory instances. Respect existing sync/async signatures.
  Resolve stored/seed/unavailable independently per component; distinguish empty results from query failures.
  **Tester positive**: First request uses seed; a stored write changes the next dashboard response.
  **Tester negative**: Repository timeout is not reported as successful seed or empty operational data.
  **Tester edge**: Mixed stored/seed components, empty repository with valid seed, multiple requests/tenants.
  **Tests / fixtures**: [API suite](../../tests/integration/test_governance_dashboard_api.py#L10),
  [registry fixtures](../../tests/contract/test_governance_dashboard.py#L12), copied seed records.
  **Future validation**: FV-01, FV-03. **Dependencies / completion**: AUD-023-001, AUD-023-002;
  route-level write/read assertions must reach the same underlying store without singleton monkey-patch shortcuts.

- [ ] **AUD-023-004 [P1] Derive canonical gates from current assessments.**
  **Trace**: FR-001, FR-005, FR-028; US1.2, US1.3; T007, T011, T015, T069; EC-06.
  **Expected / observed / impact**: Current assessments determine mapped gate outcomes. [Gate evaluators](../../apps/api/app/services/governance_data_service.py#L77)
  ignore those records and can produce compliant gates with no evidence or fictional assessment dates.
  **Owners**: [Gate service](../../apps/api/app/services/governance_data_service.py#L77),
  [current-assessment repository](../../apps/api/app/repositories/governance_repository.py#L64),
  [health algorithm](../../apps/api/app/services/health_score_service.py#L110).
  **Developer**: Implement the six-principle-to-ten-gate mapping, current-record selection, aggregation policy,
  and clearly marked fallback for unmapped/unassessed gates. Do not equate organisation/source count with a
  completed compliance assessment. Preserve canonical names and the 40/25/20/15 algorithm.
  **Tester positive**: Current pass/partial/fail assessments alter only their mapped gate and weighted result.
  **Tester negative**: Superseded records and an empty seed do not create a compliant assessed gate.
  **Tester edge**: Multiple sources per principle, no mapped assessment, duplicate/superseded chains, zero evidence.
  **Tests / fixtures**: [Assessment helper](../../tests/contract/test_governance_dashboard.py#L33),
  [health tests](../../tests/unit/test_health_score_service.py#L8), proposed data-service tests in AUD-023-029.
  **Future validation**: FV-01, FV-02. **Dependencies / completion**: AUD-023-003, AUD-023-006, AUD-023-031;
  all ten results must identify their real evidence or explicit pending/baseline provenance.

- [ ] **AUD-023-005 [P1] Build all ten gates for assessed and unassessed sources.**
  **Trace**: FR-022, FR-023, FR-028, SC-010; T061, T063, T064, T065; US6.1, US6.2, US6.3.
  **Expected / observed / impact**: Every registered source has ten gate results, merging current assessments
  with baseline cells. [Entry generation](../../apps/api/app/services/governance_data_service.py#L623) returns
  aggregate source status only and abandons seed-only sources once any stored sources exist.
  **Owners**: [Entry service](../../apps/api/app/services/governance_data_service.py#L623),
  [matrix assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L122),
  [matrix model](../../apps/api/app/models/governance_health.py#L34),
  [matrix UI](../../apps/web/src/components/governance/dashboard/ComplianceMatrix.tsx#L27).
  **Developer**: Merge sources by stable identity, use only current assessments for active cells, and add
  gate-level detail without removing existing row fields. Keep an explicit unknown/pending baseline and
  preserve stored-only as well as seed-only registered sources.
  **Tester positive**: One assessed source and one unassessed source both appear with ten distinguishable cells.
  **Tester negative**: Superseded failures do not contaminate current results; stored presence cannot drop other sources.
  **Tester edge**: More than 46 sources, partial principles on one source, duplicate source IDs, all-empty input.
  **Tests / fixtures**: [Registry fixtures](../../tests/contract/test_governance_dashboard.py#L12),
  [schema suite](../../tests/contract/test_governance_dashboard_contract.py#L1), seed source catalogue.
  **Future validation**: FV-01, FV-02, FV-03, FV-05. **Dependencies / completion**: AUD-023-003,
  AUD-023-004, AUD-023-006; verify each matrix cell's provenance, not merely row count.

- [ ] **AUD-023-006 [P1] Preserve fallback provenance through API and UI.**
  **Trace**: FR-005, FR-024; T006a, T006b, T079; US1.3, US6.2, US6.3.
  **Expected / observed / impact**: Users can distinguish stored assessment results from seed/computed values.
  [Raw entries](../../apps/api/app/services/governance_data_service.py#L623) have `data_source_type`, but
  [assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L142), response models, and client types omit it.
  **Owners**: [Response models](../../apps/api/app/models/governance_health.py#L20),
  [client types](../../apps/web/src/lib/api/governance.ts#L47),
  [compliance badges](../../apps/web/src/components/governance/dashboard/ComplianceMatrix.tsx#L17).
  **Developer**: Add optional provenance consistently for components and matrix cells/rows, explicitly map
  snake_case/camelCase if necessary, and render a textual seed-baseline indicator. Do not infer provenance
  from a zero score or from logs. Retain backward-compatible existing fields and default behavior.
  **Tester positive**: Stored and baseline entries render different text labels after a real serialized response.
  **Tester negative**: No baseline is labeled as assessed/live; a legitimate stored zero remains stored.
  **Tester edge**: Mixed component provenance and older responses lacking the optional field.
  **Tests / fixtures**: [Response schemas](../../tests/contract/test_governance_dashboard_contract.py#L1),
  [dashboard E2E location](../../tests/e2e/governance-dashboard.spec.ts#L72), mixed source fixture.
  **Future validation**: FV-02, FV-05, FV-06. **Dependencies / completion**: AUD-023-031;
  verify raw JSON, typed-client mapping, and visible labels, not just declaration of a field.

- [ ] **AUD-023-007 [P2] Return real compliance detail and honest not-found results.**
  **Trace**: FR-022, FR-025, FR-028; T065; US1 drill-down and compliance-detail contract.
  **Expected / observed / impact**: A known source exposes assessment evidence; an unknown source is 404.
  [Detail assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L193) always returns empty history
  and fabricates `Source {id}`. Gate links carry a `gate` query that the dashboard page/router do not consume.
  **Owners**: [Detail method](../../apps/api/app/services/dashboard_aggregation_service.py#L193),
  [drawer](../../apps/web/src/app/governance/dashboard/compliance/page.tsx#L56),
  [gate links](../../apps/web/src/components/governance/dashboard/ConstitutionalGates.tsx#L63).
  **Developer**: Reuse the [existing compliance-profile logic](../../apps/api/app/services/governance_registry.py#L148)
  in the dashboard adapter. Resolve current versus historical presentation explicitly, keep superseded records
  out of active scoring, and make gate drill-down select its evidence rather than an unfiltered matrix.
  **Tester positive**: Source drawer and selected gate show matching assessor, date, rationale, and evidence.
  **Tester negative**: Unknown/foreign source IDs do not produce successful synthetic objects.
  **Tester edge**: Known unassessed source, superseded history, no remediation actions.
  **Tests / fixtures**: [Registry assessment helper](../../tests/contract/test_governance_dashboard.py#L33),
  [API suite](../../tests/integration/test_governance_dashboard_api.py#L65).
  **Future validation**: FV-02, FV-03, FV-06. **Dependencies / completion**: AUD-023-004, AUD-023-005,
  AUD-023-031; current evidence and explicitly historical records must not be conflated.

- [ ] **AUD-023-008 [P1] Correct nonempty audit response serialization.**
  **Trace**: FR-018, FR-025, SC-006, SC-009; T054, T056, T059.
  **Expected / observed / impact**: Stored events must serialize to the existing consumer contract. The
  [constructor](../../apps/api/app/services/dashboard_aggregation_service.py#L265) omits required fields in
  [AuditEventSummary](../../apps/api/app/models/governance_health.py#L76); empty-list tests conceal the defect.
  **Owners**: [Audit assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L225),
  [data adapter](../../apps/api/app/services/governance_data_service.py#L691),
  [client audit interface](../../apps/web/src/lib/api/governance.ts#L109).
  **Developer**: Map audit ID, action, actor, source/related entity, outcome/context, timestamp, and provenance
  into the existing required fields. Populate decision-chain availability from actual relationships.
  Do not rename consumer fields to match the incorrect constructor.
  **Tester positive**: A real stored assessment event survives route serialization and appears in the UI row.
  **Tester negative**: Missing mandatory source data produces an explicit controlled failure, not fabricated context.
  **Tester edge**: Empty details, null related entity, multiple event action types, timezone-aware timestamps.
  **Tests / fixtures**: [Registry audit test](../../tests/contract/test_governance_dashboard.py#L87),
  [audit schema suite](../../tests/contract/test_governance_dashboard_contract.py#L107), API fixture.
  **Future validation**: FV-02, FV-03. **Dependencies / completion**: AUD-023-003;
  assert every required nonempty event field through the HTTP response.

- [ ] **AUD-023-009 [P1] Implement complete audit search over the tenant's records.**
  **Trace**: FR-020, FR-018; T054, T057, T059; US5.1, US5.3.
  **Expected / observed / impact**: Unfiltered search returns actual tenant records; all filters compose.
  [Search](../../apps/api/app/services/governance_data_service.py#L691) queries source `""` when entity is absent,
  ignores actor/keyword, and equates affected entity with source ID. Date-only inputs become naive datetimes;
  comparison with aware events can be swallowed as an empty result. Invalid date syntax can reach 500.
  **Owners**: [Date parsing](../../apps/api/app/api/routes/governance_dashboard.py#L673),
  [search adapter](../../apps/api/app/services/governance_data_service.py#L691),
  [repository query](../../apps/api/app/repositories/governance_repository.py#L464).
  **Developer**: Support tenant-wide enumeration plus intersecting actor/action/time/entity/keyword filters,
  preserving real related-entity IDs. Validate date ranges, normalize zones, document date-only upper-bound
  semantics, and distinguish empty results from failed queries. Paginate deterministically.
  **Tester positive**: Unfiltered and combined-filter searches return exactly the expected subset and count.
  **Tester negative**: Unmatched filters return zero; invalid/reversed ranges are controlled validation errors.
  **Tester edge**: Date-only UI values, timezone offsets, equal timestamps, related entity distinct from source ID.
  **Tests / fixtures**: [Audit fixtures](../../tests/contract/test_governance_dashboard.py#L87),
  [HTTP search tests](../../tests/integration/test_governance_dashboard_api.py#L96).
  **Future validation**: FV-01, FV-03. **Dependencies / completion**: AUD-023-001, AUD-023-008;
  assert records and totals, not merely `filters_applied` or HTTP 200.

- [ ] **AUD-023-010 [P1] Traverse actual audit decision relationships.**
  **Trace**: FR-021; T055, T058, T060; US5.4.
  **Expected / observed / impact**: Existing linked events yield their real provenance; unknown events are not
  successful empty chains. [Current method](../../apps/api/app/services/dashboard_aggregation_service.py#L296)
  performs no lookup or traversal.
  **Owners**: [Chain method](../../apps/api/app/services/dashboard_aggregation_service.py#L296),
  [audit repository](../../apps/api/app/repositories/governance_repository.py#L116),
  [audit model](../../packages/domain/src/domain/models/governance_audit.py#L36).
  **Developer**: Define source entity references separately from event-parent links; the registry currently
  stores an assessment ID in `related_entity_id`, not necessarily an audit ID. Traverse bounded, tenant-scoped
  relationships with real actors/times/evidence and correct `chain_complete`; return not found for missing roots.
  **Tester positive**: Trigger, approval, and final action appear in causal order with correct references.
  **Tester negative**: Unknown root and foreign-tenant links cannot expose or fabricate a chain.
  **Tester edge**: Cycle, broken link, branching/shared entity, incomplete chain, duplicate timestamps.
  **Tests / fixtures**: [API chain test location](../../tests/integration/test_governance_dashboard_api.py#L120),
  registry event fixtures extended with explicit links.
  **Future validation**: FV-01, FV-03, FV-06. **Dependencies / completion**: AUD-023-001,
  AUD-023-008, AUD-023-011, AUD-023-031; root existence and causal provenance must both be asserted.

- [ ] **AUD-023-011 [P1] Complete the real-action audit write contract without seed fabrication.**
  **Trace**: FR-019; CL-05; T057, T059 and task-list C2 resolution; US5.2.
  **Expected / observed / impact**: Assessment, source-status, framework-update, and plan-approval actions
  generate real contextual entries; seed loading does not. [Registry seed import](../../apps/api/app/services/governance_registry.py#L57)
  emits registrations and is called by [automatic initialization](../../apps/api/app/api/governance.py#L64).
  [Plan transition](../../apps/api/app/services/emergency_plan_service.py#L123) has no governance emission;
  [framework route](../../apps/api/app/api/routes/frameworks.py#L17) is read-only. S2 found no consumed framework-update bridge.
  **Owners**: [Registry audit helper](../../apps/api/app/services/governance_registry.py#L32),
  [plan service](../../apps/api/app/services/emergency_plan_service.py#L123), framework change owner identified at implementation.
  **Developer**: Retain real assessment/status events, add actual approved mutation event bridges, carry trusted
  actor/tenant/entity identity, and separate catalogue initialization from governance action history. Do not
  invent framework updates for read requests or alter old audit records to conceal seed-generated history.
  **Tester positive**: Each of the four actions produces a queryable event referring to the changed entity.
  **Tester negative**: Seed loading, rejected mutations, and read-only enumeration produce no successful action entry.
  **Tester edge**: Retries, supersession, failed persistence, repeated seed import, old seed-origin events.
  **Tests / fixtures**: [Registry audit tests](../../tests/contract/test_governance_dashboard.py#L87),
  [API suite](../../tests/integration/test_governance_dashboard_api.py#L96), original seed catalogues.
  **Future validation**: FV-01, FV-03. **Dependencies / completion**: AUD-023-001, AUD-023-012,
  AUD-023-031; prove mutation-to-dashboard round trips for all four required actions.

- [ ] **AUD-023-012 [P1] Preserve immutable audit events on append.**
  **Trace**: Governance Audit Entry key-entity immutability; FR-018, FR-019, FR-021; T057, T058, T059.
  **Expected / observed / impact**: Published audit entries remain immutable. [Cosmos append](../../apps/api/app/repositories/governance_repository.py#L456)
  calls upsert on the supplied ID; in-memory append retains caller-owned objects and permits duplicate IDs.
  **Owners**: [Governance repository](../../apps/api/app/repositories/governance_repository.py#L226),
  [Cosmos append](../../apps/api/app/repositories/governance_repository.py#L456).
  **Developer**: Use append semantics that reject conflicting reuse of an event identity, define safe identical
  retry handling, and detach stored memory records from caller mutation. Preserve tenant scope and existing
  historical records; this task does not require inventing a new audit ledger or changing unrelated stores.
  **Tester positive**: Append and retrieve a stable event with intact contextual fields.
  **Tester negative**: Reusing its ID with changed actor/outcome cannot overwrite the original.
  **Tester edge**: Identical retry, two tenants with conflicting IDs, mutation of the original in-memory object.
  **Tests / fixtures**: [Registry action fixtures](../../tests/contract/test_governance_dashboard.py#L87);
  extend with a storage-container spy and duplicate-ID cases.
  **Future validation**: FV-01, FV-04. **Dependencies / completion**: AUD-023-001;
  both in-memory and persisted-adapter semantics must enforce the same append contract.

- [ ] **AUD-023-013 [P1] Read actual hazard assessments for counts, ranking, and detail.**
  **Trace**: FR-014, FR-015, FR-017, SC-005; T019, T044, T045, T048, T049, T051, T052, T053.
  **Expected / observed / impact**: Stored hazards change counts and ranked risks. [Current functions](../../apps/api/app/services/governance_data_service.py#L582)
  always return zero/empty, while [detail](../../apps/api/app/services/dashboard_aggregation_service.py#L641)
  returns a synthetic record, masking threats and missing IDs.
  **Owners**: [Risk data functions](../../apps/api/app/services/governance_data_service.py#L303),
  [risk aggregation](../../apps/api/app/services/dashboard_aggregation_service.py#L560),
  [hazard model](../../packages/domain/src/domain/models/hazard_assessment.py#L18).
  **Developer**: Connect the approved actual hazard-record store/read adapter, not generated example risks.
  Map model `critical/moderate` to consumer `extreme/medium` explicitly; rank by severity then confidence with
  deterministic ties. Query detail by stable ID and tenant, returning 404 when absent. Keep honest zero state.
  **Tester positive**: Mixed severities and confidences produce exact counts, ordered risks, and matching detail.
  **Tester negative**: No records returns zeros/empty; nonexistent or foreign IDs return not found.
  **Tester edge**: Equal severity/confidence, one severity only, expired/superseded records under agreed policy.
  **Tests / fixtures**: [Risk API location](../../tests/integration/test_governance_dashboard_api.py#L215),
  [schema fixture](../../tests/contract/test_governance_dashboard_contract.py#L165), tenant-scoped HazardAssessment fixtures.
  **Future validation**: FV-01, FV-02, FV-03. **Dependencies / completion**: AUD-023-001,
  AUD-023-003, AUD-023-031; both summary and risk views must agree after a stored assessment change.

- [ ] **AUD-023-014 [P1] Define and implement evidence-based AWS compliance.**
  **Trace**: FR-016; US4.3; T046, T050, T052; CHK030, CHK031.
  **Expected / observed / impact**: Warning alignment derives from relevant configurations with an auditable
  mapping. [Current implementation](../../apps/api/app/services/governance_data_service.py#L590) duplicates
  tier-1 source proportion for all ten principles and fabricates a total of one for no warning sources.
  **Owners**: [AWS computation](../../apps/api/app/services/governance_data_service.py#L590),
  [risk assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L560).
  **Developer**: Document which available configuration evidence supports each principle and which cannot be
  assessed. Preserve the ten principle IDs, use actual denominators, mark proxy/pending results, and avoid
  reporting zero latency/reach/tier usage as measured operational results when no read path exists.
  **Tester positive**: A relevant trust/configuration change alters only supported compliance derivations.
  **Tester negative**: No warning sources yields zero actual sources and unavailable/pending evidence, not one source.
  **Tester edge**: Mixed tiers/statuses, sources without warning classification, unsupported principle evidence.
  **Tests / fixtures**: [Risk contract fixture](../../tests/contract/test_governance_dashboard_contract.py#L165),
  source catalogue plus controlled mixed-tier copies.
  **Future validation**: FV-01, FV-02. **Dependencies / completion**: AUD-023-003, AUD-023-006,
  AUD-023-031; no policy compliance claim may exceed its recorded evidence.

- [ ] **AUD-023-015 [P1] Use actual plan lifecycle and review state.**
  **Trace**: FR-002, FR-008; T013, T030, T033, T035; US2.5; CHK014, CHK015.
  **Expected / observed / impact**: Stored plans determine counts/currency; any seed expectations are explicit.
  [Current summaries](../../apps/api/app/services/governance_data_service.py#L366) never query plans, inspect
  nonexistent framework `type`, infer supersession from leftover metadata, and leave overdue counts zero.
  **Owners**: [Plan summaries](../../apps/api/app/services/governance_data_service.py#L366),
  [plan service](../../apps/api/app/services/emergency_plan_service.py#L84),
  [plan repository](../../apps/api/app/repositories/emergency_plan_repository.py#L86).
  **Developer**: Adapt actual lifecycle names to the seven existing dashboard labels, use real review/exercise
  dates, and read the real seed `framework_type` schema only for approved fallback expectations. Never infer
  “Superseded” or “Endorsed” merely from missing metadata. Resolve zero-count versus expectation wording first.
  **Tester positive**: Stored plans across all seven states and an overdue plan yield exact totals/currency.
  **Tester negative**: Frameworks with no plan evidence do not fabricate approved/superseded lifecycle records.
  **Tester edge**: Empty store, missing review date, review due today, more records than default repository limit.
  **Tests / fixtures**: [Readiness API tests](../../tests/integration/test_governance_dashboard_api.py#L162),
  [aggregation tests](../../tests/unit/test_dashboard_aggregation.py#L64), real framework fixtures.
  **Future validation**: FV-01, FV-03. **Dependencies / completion**: AUD-023-003, AUD-023-031;
  counts, overdue totals, and summary readiness inputs must reconcile with the same scoped plan records.

- [ ] **AUD-023-016 [P1] Compute capability gaps within each jurisdiction.**
  **Trace**: FR-002, FR-007, FR-009; T024, T026, T029, T032, T035; US2.2, US2.3.
  **Expected / observed / impact**: Organisations in one jurisdiction cannot hide unmet requirements in another.
  [Gap computation](../../apps/api/app/services/governance_data_service.py#L419) uses global hazard unions and
  ignores primary capabilities/assignment jurisdiction. [Role coverage](../../apps/api/app/services/governance_data_service.py#L340)
  counts organisations globally against jurisdiction count, not distinct jurisdiction coverage.
  **Owners**: [Data service](../../apps/api/app/services/governance_data_service.py#L419),
  [readiness assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L312).
  **Developer**: Join framework assignments and participating organisations by jurisdiction, apply RT-009's
  approved hazard/capability heuristic, and retain evidence of unmet requirements. Preserve the six AIIMS
  functions and label global organisation coverage honestly. Limit this task to 023 readiness obligations,
  not a reimplementation of the wider multi-jurisdiction feature.
  **Tester positive**: Matching primary capability in the required jurisdiction closes the corresponding gap.
  **Tester negative**: The same capability in an unrelated jurisdiction cannot close it.
  **Tester edge**: National/multi-jurisdiction organisations, no AIIMS functions, duplicate functions, unknown references.
  **Tests / fixtures**: [Readiness unit location](../../tests/unit/test_dashboard_aggregation.py#L64),
  framework/assignment/organisation seed copies with two contrasting jurisdictions.
  **Future validation**: FV-01, FV-03. **Dependencies / completion**: AUD-023-003, AUD-023-031;
  every reported gap must cite the jurisdictional requirement and absent capability evidence.

- [ ] **AUD-023-017 [P2] Expose real PPRR counts and orphan-assignment diagnostics.**
  **Trace**: FR-006, SC-003; T023, T028, T035; US2.1; EC-05.
  **Expected / observed / impact**: Users see assignment-derived phase distribution and unknown references.
  [Data computation](../../apps/api/app/services/governance_data_service.py#L322) joins real assignments, but
  silently skips unknown frameworks; [assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L323)
  reduces counts to active/inactive flags and exposes no unknown-entity detail.
  **Owners**: [PPRR computation](../../apps/api/app/services/governance_data_service.py#L322),
  [phase model](../../apps/api/app/models/governance_health.py#L122),
  [readiness view](../../apps/web/src/app/governance/dashboard/readiness/page.tsx#L40).
  **Developer**: Keep the existing four phase entries and fields, add count/total/reference diagnostics
  compatibly, and expose them in the view. Count orphan assignments in aggregate accounting without assigning
  them an invented phase; identify unknown jurisdiction/framework references explicitly.
  **Tester positive**: Controlled multi-phase assignments yield exact per-phase counts and total accounting.
  **Tester negative**: An unknown framework is not silently lost or attributed to a guessed phase.
  **Tester edge**: Unknown jurisdiction, no phases, repeated assignments, an empty framework collection.
  **Tests / fixtures**: [Readiness contract location](../../tests/contract/test_governance_dashboard_contract.py#L121),
  copied 123-assignment baseline plus orphan fixtures.
  **Future validation**: FV-01, FV-02, FV-05. **Dependencies / completion**: AUD-023-016,
  AUD-023-031; verify the serialized and displayed counts, not just the internal dictionary.

- [ ] **AUD-023-018 [P1] Separate volunteer organisation coverage from live availability.**
  **Trace**: FR-010, SC-003; T025, T031, T035; US2.4.
  **Expected / observed / impact**: Metrics expose actual volunteer/mixed counts, jurisdiction distribution,
  and capability coverage. [Current computation](../../apps/api/app/services/governance_data_service.py#L466)
  counts 24 organisations but marks every one available; [assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L312)
  drops jurisdiction and capability fields before rendering a workforce-readiness panel.
  **Owners**: [Volunteer computation](../../apps/api/app/services/governance_data_service.py#L466),
  [volunteer response model](../../apps/api/app/models/governance_health.py#L150),
  [readiness UI](../../apps/web/src/app/governance/dashboard/readiness/page.tsx#L172).
  **Developer**: Preserve organisation-based metrics and expose jurisdiction/capability breakdowns additively.
  Represent deployment, availability, and welfare as unknown/baseline unless actual records support them.
  Do not turn an organisation count into a count of people or available responders.
  **Tester positive**: Paid/volunteer/mixed fixture yields the exact eligible organisations and distribution.
  **Tester negative**: Paid-only organisations are excluded; unavailable status cannot become 100% available.
  **Tester edge**: Mixed organisations in several jurisdictions, no eligible organisations, missing capability lists.
  **Tests / fixtures**: [Readiness API location](../../tests/integration/test_governance_dashboard_api.py#L162),
  organisation seed copies, proposed component tests under the existing dashboard component directory.
  **Future validation**: FV-01, FV-02, FV-05. **Dependencies / completion**: AUD-023-006,
  AUD-023-016; both data and labels must distinguish reference coverage from operational workforce state.

- [ ] **AUD-023-019 [P2] Remove phase-derived exercise performance claims.**
  **Trace**: FR-002; CL-04; T013, T035; CHK003, CHK069.
  **Expected / observed / impact**: MVP exercise metrics derive from actual review/exercise metadata or show
  zero when absent. [Top-level input](../../apps/api/app/services/governance_data_service.py#L253) currently
  yields zero for this seed, but [readiness assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L312)
  derives tabletop/functional/full-scale percentages from PPRR assignments instead.
  **Owners**: [Readiness inputs](../../apps/api/app/services/governance_data_service.py#L253),
  [readiness assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L312),
  [exercise display](../../apps/web/src/app/governance/dashboard/readiness/page.tsx#L55).
  **Developer**: Use one evidence-backed exercise definition for headline and breakdown; absent exercise
  metadata must not become exercise completion through phase coverage. Document the separate role-only
  `overall_readiness_score` versus the composite readiness dimension rather than implying they are identical.
  **Tester positive**: Approved exercise/review metadata changes the relevant rate with traceable inputs.
  **Tester negative**: Adding a preparedness assignment alone does not create completed exercises.
  **Tester edge**: No metadata, partial metadata, no frameworks, rounded values and denominator zero.
  **Tests / fixtures**: [Readiness unit location](../../tests/unit/test_dashboard_aggregation.py#L64),
  original framework fixtures with no `review_cycle_years`, plus explicit metadata cases.
  **Future validation**: FV-01, FV-02. **Dependencies / completion**: AUD-023-015, AUD-023-031;
  preserve the existing health-score weighting and distinguish different readiness indicators.

- [ ] **AUD-023-020 [P1] Preserve all five real catalogue domains and their counts.**
  **Trace**: FR-011, SC-004; T036, T037, T039, T040, T042, T043; US3.1, US3.2, US3.4.
  **Expected / observed / impact**: Five actual catalogue domains remain visible as reference structure even
  without an incident. [Service iteration](../../apps/api/app/services/governance_data_service.py#L491) creates
  four rows even when files are absent, while [aggregation](../../apps/api/app/services/dashboard_aggregation_service.py#L462)
  substitutes an averaged overarching row and discards outcome/activity/indicator counts.
  **Owners**: [Recovery data service](../../apps/api/app/services/governance_data_service.py#L491),
  [recovery models](../../apps/api/app/models/governance_health.py#L194),
  [recovery page](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L147),
  [domain display](../../apps/web/src/components/governance/dashboard/RecoveryDomainTracker.tsx#L21).
  **Developer**: Load and represent each actual domain, including overarching's own 7/20/22 structure;
  expose counts compatibly and keep a visible catalogue baseline when recovery is inactive. Do not show
  nonexistent domains as zero-progress programmes. Respect 018's authority over recovery-phase semantics.
  **Tester positive**: Social shows 24/57/53, overarching 7/20/22, and all other counts match files.
  **Tester negative**: Removing a domain marks it unavailable, not an invented active row.
  **Tester edge**: Empty catalogue, a domain with no outcomes, catalogue present but no active recovery.
  **Tests / fixtures**: [Recovery unit location](../../tests/unit/test_dashboard_aggregation.py#L90),
  [API location](../../tests/integration/test_governance_dashboard_api.py#L184), five catalogue JSON files.
  **Future validation**: FV-01, FV-02, FV-03, FV-05. **Dependencies / completion**: AUD-023-023;
  verify counts and baseline visibility through serialization and the UI.

- [ ] **AUD-023-021 [P1] Merge actual tracker progress and incident state consistently.**
  **Trace**: FR-004, FR-013; T014, T018, T039, T040, T041, T043; US3.3, US3.4.
  **Expected / observed / impact**: Active trackers supply values and true active recovery. [Recovery inputs](../../apps/api/app/services/governance_data_service.py#L275)
  and [active check](../../apps/api/app/services/governance_data_service.py#L730) always say false, while
  [view assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L523) says true when catalogue rows exist.
  This leaves the health recovery dimension at 100 and the view at baseline progress regardless of updates.
  **Owners**: [Dashboard recovery](../../apps/api/app/services/dashboard_aggregation_service.py#L462),
  [tracker update service](../../apps/api/app/services/recovery_service.py#L83),
  [tracker model](../../packages/domain/src/domain/models/recovery_environment_tracker.py#L74).
  **Developer**: Read scoped actual tracker/incident state, join indicator identities to catalogue structure,
  honor selected incident, and compute the same activity state in summary and view. Remove `INC-LATEST` and
  fixed incident date/name as stand-ins for stored records; retain the unchanged no-active-recovery algorithm.
  **Tester positive**: A tracker update changes the correct incident/domain and summary dimension.
  **Tester negative**: Catalogue alone never means active recovery; a foreign or unknown incident cannot yield invented progress.
  **Tester edge**: Completed/suspended tracker, partially populated indicators, multiple incidents, no catalogue mapping.
  **Tests / fixtures**: [API recovery tests](../../tests/integration/test_governance_dashboard_api.py#L184),
  [state fixtures](../../apps/api/app/services/state_store.py#L28), RecoveryIndicator catalogue IDs and values.
  **Future validation**: FV-01, FV-03, FV-04. **Dependencies / completion**: AUD-023-001,
  AUD-023-003, AUD-023-020, AUD-023-022; distinguish process-local tracker support from durable persistence evidence.

- [ ] **AUD-023-022 [P1] Resolve recovery target provenance and preserve indicator types.**
  **Trace**: FR-012, FR-013; T037, T040, T043; CHK022, CHK023, CHK024.
  **Expected / observed / impact**: Targets come from declared indicator targets. The 152 catalogue indicators
  contain no numeric targets; [detail](../../apps/api/app/services/governance_data_service.py#L522) uses indicator
  count as a target and changes all types to qualitative; domain targets are fixed at 100.
  **Owners**: [Detail computation](../../apps/api/app/services/governance_data_service.py#L522),
  [catalogue seed](../../packages/domain/src/domain/seed/recovery-catalogue/social.json#L26),
  [tracked target fields](../../packages/domain/src/domain/models/recovery_environment_tracker.py#L74).
  **Developer**: Obtain an explicit target-source/merge decision: catalogue extension or approved tracker target
  mapping, with units, baseline, and unavailable semantics. Preserve quantitative/qualitative/both types and
  stable indicator IDs. Do not manufacture numerical progress when a meaningful denominator is absent.
  **Tester positive**: A mapped indicator with a valid target produces the agreed progress and source reference.
  **Tester negative**: Missing, zero, or incompatible targets do not become a made-up 100% target.
  **Tester edge**: Qualitative indicators, regressions, conflicting tracker/catalogue values, partial mappings.
  **Tests / fixtures**: Actual social/overarching indicator records, RecoveryIndicator target/mapping fields,
  [recovery contract tests](../../tests/contract/test_governance_dashboard_contract.py#L145).
  **Future validation**: FV-01, FV-02. **Dependencies / completion**: AUD-023-031;
  approved semantics and positive/negative numeric assertions are required before calling FR-012 implemented.

- [ ] **AUD-023-023 [P1] Isolate seed failures and implement the documented error contract.**
  **Trace**: FR-005, FR-026, SC-008; T066, T067, T068; EC-01, EC-02, EC-03.
  **Expected / observed / impact**: Partial inputs degrade independently; failed storage/seed does not look
  successful. [Bootstrap](../../packages/domain/src/domain/seed/bootstrap.py#L13) parses all domains without
  per-file recovery; missing inputs lack availability diagnostics. Most routes do not translate failures to 503.
  **Owners**: [Seed loader](../../packages/domain/src/domain/seed/bootstrap.py#L13),
  [route boundary](../../apps/api/app/api/routes/governance_dashboard.py#L568),
  [data service](../../apps/api/app/services/governance_data_service.py#L55),
  [error middleware](../../apps/api/app/middleware/error_handler.py#L110).
  **Developer**: Catch and classify independent domain/file failures, retain valid sections, and propagate
  unavailable/incomplete state. Keep legitimate no-action audit and no-hazard zero states distinct from outage.
  Align 503/404/422 bodies with the declared contract or an explicitly approved compatible envelope decision.
  **Tester positive**: Four valid domains remain usable when one file is malformed.
  **Tester negative**: Entire store/seed failure cannot return green assessed gates or successful fake details.
  **Tester edge**: Missing keys, wrong JSON shapes, empty directory, cached seed versus cold start, repository timeout.
  **Tests / fixtures**: [Temporary-directory fixture](../../tests/conftest.py#L26), copied seed directories,
  [API suite](../../tests/integration/test_governance_dashboard_api.py#L10).
  **Future validation**: FV-01, FV-03. **Dependencies / completion**: AUD-023-006, AUD-023-031;
  each documented failure must have a status/body/availability assertion, without leaking raw exception details.

- [ ] **AUD-023-024 [P2] Show explicit request failure and baseline states in the UI.**
  **Trace**: SC-008, SC-009; EC-01, EC-02, EC-03; US3.4; T068, T074, T079.
  **Expected / observed / impact**: Users can distinguish empty data from failed loading. [Compliance](../../apps/web/src/app/governance/dashboard/compliance/page.tsx#L22),
  [audit](../../apps/web/src/app/governance/dashboard/audit/page.tsx#L30), and
  [recovery](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L61) swallow request exceptions;
  render error boundaries do not supply the missing request state.
  **Owners**: Those dashboard pages; [risk page](../../apps/web/src/app/governance/dashboard/risk/page.tsx#L23)
  and [readiness page](../../apps/web/src/app/governance/dashboard/readiness/page.tsx#L20) for consistent retry behavior.
  **Developer**: Track request errors explicitly, provide retry, retain previous data only with a stale/error
  indication, and avoid blank drawers or unchanged detail after a failed selection. Keep inactive recovery
  catalogue structure visible; do not extend this task to unrelated later recovery panels.
  **Tester positive**: Valid empty results show the correct no-events/no-assessments/baseline state.
  **Tester negative**: 503, invalid JSON, and failed detail requests show failure, not “no matches.”
  **Tester edge**: Successful data followed by failure, rapid selections, recovery without an active programme.
  **Tests / fixtures**: [Dashboard E2E source](../../tests/e2e/governance-dashboard.spec.ts#L10),
  proposed colocated component tests with controlled fetch results.
  **Future validation**: FV-05, FV-06. **Dependencies / completion**: AUD-023-006, AUD-023-020,
  AUD-023-023; assert visible states and recovery from failure, not only headings.

- [ ] **AUD-023-025 [P1] Report source freshness and verify update visibility.**
  **Trace**: FR-005, FR-026, SC-001, SC-002; T070, T075; CHK055, CHK070.
  **Expected / observed / impact**: Source age and provenance remain honest after refresh. [Summary](../../apps/api/app/services/dashboard_aggregation_service.py#L116)
  labels request time as freshness; gates and seed entries generate assessment dates; [bypass](../../apps/api/app/api/routes/governance_dashboard.py#L586)
  changes only a header on a permanently seeded service. Users repeatedly see “Just now” for unchanged baselines.
  **Owners**: [Seed cache](../../apps/api/app/services/seed_service.py#L8),
  [route singleton](../../apps/api/app/api/routes/governance_dashboard.py#L71),
  [freshness display](../../apps/web/src/components/governance/dashboard/DataFreshnessIndicator.tsx#L31),
  [summary page](../../apps/web/src/app/governance/dashboard/page.tsx#L43).
  **Developer**: Separate computed-at from source-assessed/updated-at and seed-version/load time. Preserve
  consistent seed-root caching, but do not use it as a record-update cache. Make bypass semantics truthful
  and define any freshness budget with the owner; 023 does not specify a numeric maximum data age.
  **Tester positive**: A stored update changes the relevant score and source timestamp on refresh.
  **Tester negative**: Repeated polling of unchanged seed does not invent a new assessment date.
  **Tester edge**: Mixed source ages, missing timestamps, paused refresh, tenant/context changes and overlapping requests.
  **Tests / fixtures**: [Health service tests](../../tests/unit/test_health_score_service.py#L112),
  [API suite](../../tests/integration/test_governance_dashboard_api.py#L25), controlled timestamps and seed versions.
  **Future validation**: FV-01, FV-03, FV-05. **Dependencies / completion**: AUD-023-003,
  AUD-023-006; record-update visibility and timestamp semantics must be asserted without changing score weights.

- [ ] **AUD-023-026 [P2] Preserve filter/sort state across pagination and validate sort inputs.**
  **Trace**: FR-020, FR-025; T054, T057, T062, T065, T074; US5.3.
  **Expected / observed / impact**: Paging stays within the selected result set. [Audit next-page handling](../../apps/web/src/app/governance/dashboard/audit/page.tsx#L99)
  passes only the token; [compliance paging](../../apps/web/src/app/governance/dashboard/compliance/page.tsx#L48)
  omits the chosen sort. [Server sorting](../../apps/api/app/services/dashboard_aggregation_service.py#L171)
  compares raw nullable attributes, while malformed/negative tokens are not consistently rejected.
  **Owners**: Those two pages; [matrix assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L122),
  [audit assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L225).
  **Developer**: Persist the full active query state for paging/export, define stable ordering and null placement,
  whitelist sort fields/directions, and validate continuation input. Keep current optional parameters and shapes.
  **Tester positive**: More than one page remains actor-filtered or name-descending as requested.
  **Tester negative**: Invalid sort/token does not raise an unhandled error or expose a different result set.
  **Tester edge**: All-null due dates, equal keys, filter change mid-page, deletion between pages.
  **Tests / fixtures**: [Pagination API location](../../tests/integration/test_governance_dashboard_api.py#L77),
  [dashboard E2E source](../../tests/e2e/governance-dashboard.spec.ts#L72), mixed nullable multi-page records.
  **Future validation**: FV-02, FV-03, FV-05. **Dependencies / completion**: AUD-023-005, AUD-023-009;
  compare actual page contents and order across transitions.

- [ ] **AUD-023-027 [P1] Export the selected real audit records and a real artifact.**
  **Trace**: FR-018, FR-025, SC-001, SC-008, SC-009; T006, T056, T074; contract endpoints 7 and 8.
  **Expected / observed / impact**: Existing export consumers receive the selected audit data. [Handler](../../apps/api/app/api/routes/governance_dashboard.py#L738)
  passes an empty list; [service](../../apps/api/app/services/audit_export_service.py#L62) discards output and
  constructs a URL. PDF is a placeholder. This is a directly scoped consumer-path defect, not a new export feature.
  **Owners**: [Export route](../../apps/api/app/api/routes/governance_dashboard.py#L717),
  [export service](../../apps/api/app/services/audit_export_service.py#L28),
  [UI action](../../apps/web/src/app/governance/dashboard/audit/page.tsx#L53).
  **Developer**: Resolve selected IDs/filters through the same scoped audit query, generate the requested real
  content, and publish only an actually persisted/downloadable artifact. Preserve 202/job-status contracts;
  bind job ownership to authenticated identity and report failed output creation as failed, not complete.
  **Tester positive**: CSV/JSON/PDF contain exactly the permitted selected events and a usable artifact reference.
  **Tester negative**: Foreign IDs, failed generation/storage, or unknown job cannot return a successful download.
  **Tester edge**: Empty legitimate selection, duplicate IDs, retries, multiple formats, completed job on another process.
  **Tests / fixtures**: [Export API tests](../../tests/integration/test_governance_dashboard_api.py#L130),
  [export schema tests](../../tests/contract/test_governance_dashboard_contract.py#L239), fake artifact-storage adapter.
  **Future validation**: FV-03, FV-04, FV-06. **Dependencies / completion**: AUD-023-002,
  AUD-023-008, AUD-023-009; use local/test storage first, with no cloud deployment implied by test success.

- [ ] **AUD-023-028 [P2] Make summary operational counters traceable and correctly labeled.**
  **Trace**: SC-001, SC-002; T009, T020, T021, T022; summary contract.
  **Expected / observed / impact**: Active incidents and utilisation represent their advertised operational
  concepts. [Incident count](../../apps/api/app/services/governance_data_service.py#L308) is always zero;
  [utilisation](../../apps/api/app/services/governance_data_service.py#L312) counts organisations with capabilities,
  while the [UI label](../../apps/web/src/app/governance/dashboard/page.tsx#L123) describes committed response resources.
  **Owners**: [Counter methods](../../apps/api/app/services/governance_data_service.py#L308),
  [summary assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L56),
  [incident state](../../apps/api/app/services/state_store.py#L16).
  **Developer**: Count actual scoped active incident records and propagate activity consistently to health/config.
  Either obtain a true resource numerator/denominator or explicitly identify the permitted organisation-data
  fallback as a proxy; do not change the established field type or fabricate deployed resources.
  **Tester positive**: Active/closed incident changes alter the count and configured activity state.
  **Tester negative**: Adding a capability to an idle organisation does not silently claim deployed utilisation.
  **Tester edge**: No incidents/resources, zero denominator, archived incidents, mixed tenant states.
  **Tests / fixtures**: [Summary tests](../../tests/unit/test_dashboard_aggregation.py#L6),
  [API suite](../../tests/integration/test_governance_dashboard_api.py#L25), organisation and incident fixtures.
  **Future validation**: FV-01, FV-03, FV-05. **Dependencies / completion**: AUD-023-003,
  AUD-023-006, AUD-023-031; preserve literal T021 credit for a real organisation computation while fixing misleading semantics.

- [ ] **AUD-023-029 [P1] Add direct data-service tests for the required branches.**
  **Trace**: T007, T008, T023, T024, T025, T026, T036, T037, T044, T045, T046, T054, T055, T061, T078;
  every FR and edge case implemented by the data service.
  **Expected / observed / impact**: Tests exercise the actual computation and stored/seed transition. S4 found
  no data-service tests; shape-only fallback tests cannot catch its wrong seed keys, hidden record paths, or lost data.
  **Owners**: Proposed `tests/unit/test_governance_data_service.py`, plus existing
  [aggregation tests](../../tests/unit/test_dashboard_aggregation.py#L1) and
  [registry fixtures](../../tests/contract/test_governance_dashboard.py#L12).
  **Developer**: Add the planned test module or an explicitly documented equivalent. Reuse seed loaders/fixtures
  without importing the full application or invoking cloud clients. Assert canonical IDs, exact calculations,
  repository invocation/scope, serialized provenance, and mutation sensitivity. Test real public method names.
  **Tester positive**: Stored records, valid seed, current assessments, populated tracker, exact social counts.
  **Tester negative**: Foreign tenant, failed repository, stale/superseded assessment, no hazards, no actions.
  **Tester edge**: All seven spec edge cases, mixed source types, dynamic counts, missing targets, date boundaries.
  **Tests / fixtures**: Original five catalogue files and source/org/framework/assignment seed copies,
  [temporary-directory helper](../../tests/conftest.py#L26), `_register`/`_assess` fixture patterns.
  **Future validation**: FV-01, FV-04. **Dependencies / completion**: Author alongside the owning fixes;
  each missing original test task needs a named assertion and recorded later execution, not an empty module.

- [ ] **AUD-023-030 [P2] Strengthen existing route, contract, and consumer tests.**
  **Trace**: T009, T010, T027, T038, T047, T056, T062, T071, T072, T073, T074; SC-009.
  **Expected / observed / impact**: Tests verify the real route path and nonempty payloads. [Unit tests](../../tests/unit/test_dashboard_aggregation.py#L10)
  supply no data service; [contract tests](../../tests/contract/test_governance_dashboard_contract.py#L107) allow
  empty audit/recovery fixtures; [integration tests](../../tests/integration/test_governance_dashboard_api.py#L96)
  mostly assert 200. Older [registry tests](../../tests/contract/test_governance_dashboard.py#L46) cover another service.
  **Owners**: Those existing suites and [dashboard E2E source](../../tests/e2e/governance-dashboard.spec.ts#L10).
  **Developer**: Exercise injected, populated dependencies through actual endpoints; validate required model
  fields and consumer names without renaming them. Replace stale ten-role and vacuous conditional checks.
  Keep valid existing registry and algorithm coverage; distinguish mocked browser data from persistence proof.
  **Tester positive**: All thirteen endpoint contracts, six views, nonempty audit, ten gates, six functions, five domains.
  **Tester negative**: Real-data changes, unknown IDs, missing identity, failed inputs, and broken provenance must fail tests.
  **Tester edge**: Mixed baseline/stored records, paging, no tracker, absent optional metadata, repeated requests.
  **Tests / fixtures**: Existing auth/client fixtures, registry helpers, direct data-service fixtures from AUD-023-029.
  **Future validation**: FV-02, FV-03, FV-05, FV-06. **Dependencies / completion**: AUD-023-029 and owning fixes;
  no `if data exists` or “200 or 404” assertion may substitute for a mandatory acceptance outcome.

- [ ] **AUD-023-031 [P2] Reconcile conflicting specification and design decisions.**
  **Trace**: FR-005, FR-008, FR-012, FR-024, FR-025; T006a, T006b, T030, T079; all local review questions.
  **Expected / observed / impact**: Owners implement one unambiguous contract. [Data-model metadata guidance](data-model.md)
  says no fields are needed, contradicting the spec and later tasks. Plan fallback is expectations versus zero
  counts; target values are absent; lifecycle/metadata/taxonomy and old operational documentation differ.
  **Owners**: [spec.md](spec.md), [data-model.md](data-model.md), [research.md](research.md),
  [contracts/dashboard-api.md](contracts/dashboard-api.md), [checklists/review.md](checklists/review.md),
  [operational documentation](../../docs/governance-dashboard.md). No changes to these originals are made here.
  **Developer**: Obtain explicit owner decisions for provenance naming, empty/failure behavior, seven-state
  adaptation, matrix dimensions, target provenance, AWS mapping, chain linkage, freshness, and error envelopes.
  Keep canonical public paths and 40/25/20/15 weights. Document actual renamed `get_*` methods; do not resurrect stubs.
  **Tester positive**: Each approved decision has a traceable acceptance assertion and compatible response example.
  **Tester negative**: Conflicting guidance is not silently selected to mark a requirement complete.
  **Tester edge**: Existing consumers without additive fields, zero records, deferred country/018/008 authority boundaries.
  **Tests / fixtures**: [Schema tests](../../tests/contract/test_governance_dashboard_contract.py#L1),
  seed schema observations and the exact review-question ledger below.
  **Future validation**: FV-02, FV-09. **Dependencies / completion**: Product/data/governance owner decisions,
  then signed review records; preserve original checked-state history rather than retroactively ticking tasks.

- [ ] **AUD-023-032 [P2] Establish execution, performance, and rehearsal evidence later.**
  **Trace**: T001, T075, T076, T077; SC-007, SC-008, SC-009; plan PASS gates and quickstart claims.
  **Expected / observed / impact**: Successful tests, p95 measurements, rehearsal, and deployment claims have
  attributable results. Only instructions/estimates and test source were available; no required execution was established.
  **Owners**: [Original validation tasks](tasks.md#L222), [quickstart.md](quickstart.md),
  [API suite](../../tests/integration/test_governance_dashboard_api.py#L10),
  [performance logger](../../apps/api/app/api/routes/governance_dashboard.py#L49).
  **Developer**: After repairs, record revision, environment, exact command, all selected test counts, result,
  and failures. Add an endpoint-specific benchmark covering all thirteen with ten sequential requests each
  at minimum and a declared percentile method; distinguish cold/warm and populated/fallback cases.
  The existing two-second warning is not a 500ms acceptance gate. Do not recreate the historical feature branch.
  **Tester positive**: Required suites select intended tests and succeed; every endpoint meets p95 <500ms.
  **Tester negative**: Missing proposed test files, empty selections, benchmark omissions, or failed commands remain open.
  **Tester edge**: Larger data, cold bootstrap, nonempty audit/export, mixed stored/seed state, repeat runs.
  **Tests / fixtures**: [pytest configuration](../../pyproject.toml#L45), task-named suites, realistic seeded records.
  **Future validation**: FV-01 through FV-09 as applicable. **Dependencies / completion**: All relevant fixes;
  deployments require separate authorization and actual evidence. Historic branch/rehearsal facts remain UNVERIFIED until sourced.

- [ ] **AUD-023-033 [P2] Supply scoped persona, hypothesis, and review evidence.**
  **Trace**: PER-061, PER-062, PER-063, HYP-021, SCP-067, SCP-068, SCP-069; review/checklist claims.
  **Expected / observed / impact**: “Validated” personas and hypothesis uplift are supported by the required
  records. Local entries are cross-references; the HYP-HYP-021 link has no found replacement; portfolio rubric
  claims do not establish consultation on every change or this spec's causal uplift.
  **Owners**: [Appended specification sections](spec.md),
  [persona contract](../027-spec-hardening/contracts/persona-profile.md),
  [evidence contract](../028-capstone-alignment/contracts/evidence-stub.contract.md).
  **Developer**: Obtain or link actual named, dated validation records; create a conforming HYP-021 evidence
  stub in the owning feature under a separately authorized change, correcting the doubled-prefix link.
  Record an honest not-tested status until measured. Keep PH/JP/BD placeholders and 018/008 deferrals intact.
  **Tester positive**: Persona claims trace to practitioner/SME evidence and HYP results to a bounded measurement.
  **Tester negative**: A generic portfolio score or authored checkbox is not accepted as individual validation.
  **Tester edge**: Unavailable reviewers, unmet country preconditions, divergent per-criterion scores, historical evidence gaps.
  **Tests / fixtures**: The two linked contracts and [baseline](../028-capstone-alignment/evidence/rubric-baseline.md)
  / [post-feature narrative](../028-capstone-alignment/evidence/rubric-postfeature.md); evidence is documentary, not a product fixture.
  **Future validation**: FV-09. **Dependencies / completion**: AUD-023-031 and responsible human review;
  no agents, branches, source changes, country promotion, or invented sign-offs are authorized by this audit.

## Requirement Coverage

### Functional Requirements

| Requirement | Status | Inspected evidence and remaining obligation | Follow-ups |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | [Ten named gates](../../apps/api/app/services/governance_data_service.py#L16) exist; [evaluation](../../apps/api/app/services/governance_data_service.py#L77) is seed heuristic, not current assessments. | AUD-023-004 |
| FR-002 | PARTIAL | [Readiness inputs](../../apps/api/app/services/governance_data_service.py#L253) use org/framework proxies and seed-only plans; no stored lifecycle/capability integration. | AUD-023-003, AUD-023-015, AUD-023-016, AUD-023-019 |
| FR-003 | PARTIAL | [Seed status counting](../../apps/api/app/services/governance_data_service.py#L230) is real; optional registry branch counts compliance rather than availability and returns zero for an empty repository instead of seed fallback. | AUD-023-003, AUD-023-029 |
| FR-004 | PARTIAL | [Catalogue input](../../apps/api/app/services/governance_data_service.py#L275) is inspected, but only four domains and permanent inactive state feed the health score. | AUD-023-020, AUD-023-021 |
| FR-005 | PARTIAL | Seed path exists, but [responses](../../apps/api/app/models/governance_health.py#L20) have no per-component provenance and no stored-first transition. | AUD-023-003, AUD-023-006, AUD-023-023 |
| FR-006 | PARTIAL | [Join/count](../../apps/api/app/services/governance_data_service.py#L322) implemented internally; serialized distribution drops counts and orphan references. | AUD-023-017 |
| FR-007 | IMPLEMENTED | [Six-function aggregation](../../apps/api/app/services/governance_data_service.py#L340) counts actual organisation assignments and computes percentages. This does not prove distinct-jurisdiction staffing or runtime success. | AUD-023-016, AUD-023-029 |
| FR-008 | PARTIAL | [Seven summaries](../../apps/api/app/services/governance_data_service.py#L366) exist, but neither actual plans nor valid seed-schema inference determines them. Zero-versus-expectations design conflict remains. | AUD-023-015, AUD-023-031 |
| FR-009 | PARTIAL | [Global hazard comparison](../../apps/api/app/services/governance_data_service.py#L419) is not per-jurisdiction primary-capability analysis. | AUD-023-016 |
| FR-010 | PARTIAL | [Eligible org count](../../apps/api/app/services/governance_data_service.py#L466) is correct; distribution/capability data is reduced then omitted from the response, availability is assumed. | AUD-023-018 |
| FR-011 | PARTIAL | [Counts](../../apps/api/app/services/governance_data_service.py#L491) computed for four domains; [assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L462) discards them and invents overarching summary. | AUD-023-020 |
| FR-012 | CONFLICT | [Catalogue indicator schema](../../packages/domain/src/domain/seed/recovery-catalogue/social.json#L26) has no numeric targets; [detail](../../apps/api/app/services/governance_data_service.py#L522) substitutes counts. | AUD-023-022, AUD-023-031 |
| FR-013 | MISSING | [Recovery service](../../apps/api/app/services/recovery_service.py#L83) supports tracker updates; dashboard recovery methods never read them. | AUD-023-021 |
| FR-014 | MISSING | [Severity breakdown](../../apps/api/app/services/governance_data_service.py#L582) is constant and has no hazard query. | AUD-023-013 |
| FR-015 | MISSING | [Top risks](../../apps/api/app/services/governance_data_service.py#L586) is always empty, with no ranking. | AUD-023-013 |
| FR-016 | PARTIAL | [Tier proportion](../../apps/api/app/services/governance_data_service.py#L590) uses real source configuration but does not establish ten principle-specific alignments and invents empty denominator. | AUD-023-014, AUD-023-031 |
| FR-017 | IMPLEMENTED | [Zero breakdown](../../apps/api/app/services/governance_data_service.py#L582) satisfies the no-assessments case only; it does not establish that the store was checked. | AUD-023-013, AUD-023-029 |
| FR-018 | PARTIAL | [Audit adapter](../../apps/api/app/services/governance_data_service.py#L691) exists but is disconnected; [nonempty serialization](../../apps/api/app/services/dashboard_aggregation_service.py#L265) violates the model. | AUD-023-003, AUD-023-008, AUD-023-009 |
| FR-019 | PARTIAL | [Real source/assessment events](../../apps/api/app/services/governance_registry.py#L32) exist; seed import emits events, and required framework/plan bridges are not provided to this audit path. | AUD-023-011, AUD-023-012 |
| FR-020 | PARTIAL | [Search](../../apps/api/app/services/governance_data_service.py#L691) supplies action/time/source but ignores actor/keyword/related entity semantics; unfiltered and paging behavior are incorrect. | AUD-023-009, AUD-023-026 |
| FR-021 | MISSING | [Chain method](../../apps/api/app/services/dashboard_aggregation_service.py#L296) never looks up an event. | AUD-023-010 |
| FR-022 | PARTIAL | [Registry aggregate source status](../../apps/api/app/services/governance_data_service.py#L623) is not an assessment-per-principle matrix and is not production-wired. | AUD-023-003, AUD-023-005, AUD-023-007 |
| FR-023 | PARTIAL | [Seed baseline rows](../../apps/api/app/services/governance_data_service.py#L623) cover source IDs but not ten gates per source. | AUD-023-005, AUD-023-006 |
| FR-024 | MISSING | [Matrix model](../../apps/api/app/models/governance_health.py#L34), [client](../../apps/web/src/lib/api/governance.ts#L79), and [badge rendering](../../apps/web/src/components/governance/dashboard/ComplianceMatrix.tsx#L17) do not carry/show provenance. | AUD-023-006 |
| FR-025 | PARTIAL | [Thirteen paths](../../apps/api/app/api/routes/governance_dashboard.py#L518) and most field shapes remain; nonempty audit construction and error/detail/export semantics do not meet the contract. | AUD-023-007, AUD-023-008, AUD-023-010, AUD-023-013, AUD-023-023, AUD-023-027, AUD-023-030 |
| FR-026 | PARTIAL | [Seed loader](../../packages/domain/src/domain/seed/bootstrap.py#L42) exists; [route singleton](../../apps/api/app/api/routes/governance_dashboard.py#L71) cannot transition to stored data. | AUD-023-003, AUD-023-023, AUD-023-025 |
| FR-027 | PARTIAL | [Request tenant label](../../apps/api/app/api/routes/governance_dashboard.py#L475) exists, but operational reads/identity/job lookup do not enforce scoped ownership. | AUD-023-001, AUD-023-002 |
| FR-028 | MISSING | [Repository current filter](../../apps/api/app/repositories/governance_repository.py#L64) is available but not called by dashboard gates/matrix. No superseded-data exclusion assertion exists on that path. | AUD-023-004, AUD-023-005, AUD-023-029 |

### Success Criteria

| Criterion | Status | Evidence and limit | Follow-ups |
| --- | --- | --- | --- |
| SC-001 | PARTIAL | [Data service](../../apps/api/app/services/governance_data_service.py#L303) retains unconditional operational values; [detail](../../apps/api/app/services/dashboard_aggregation_service.py#L641) and [export](../../apps/api/app/services/audit_export_service.py#L62) remain synthetic. | AUD-023-004, AUD-023-013, AUD-023-018, AUD-023-019, AUD-023-020, AUD-023-021, AUD-023-022, AUD-023-025, AUD-023-027, AUD-023-028 |
| SC-002 | PARTIAL | [Algorithm](../../apps/api/app/services/health_score_service.py#L31) is input-sensitive, but [route inputs](../../apps/api/app/api/routes/governance_dashboard.py#L71) cannot observe stored changes. | AUD-023-003, AUD-023-004, AUD-023-021, AUD-023-025 |
| SC-003 | PARTIAL | Static seed has 49/123/24; [readiness assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L312) omits phase counts and volunteer breakdowns. | AUD-023-016, AUD-023-017, AUD-023-018, AUD-023-029 |
| SC-004 | PARTIAL | Five files and exact counts exist; [five displayed rows](../../apps/api/app/services/dashboard_aggregation_service.py#L462) include synthetic overarching and no count fields. | AUD-023-020 |
| SC-005 | PARTIAL | [Zero state](../../apps/api/app/services/governance_data_service.py#L582) exists; nonempty stored severity distribution does not. | AUD-023-013 |
| SC-006 | PARTIAL | [Writes](../../apps/api/app/services/governance_registry.py#L112) exist for some actions, but [read/serialize path](../../apps/api/app/services/dashboard_aggregation_service.py#L225) cannot return them correctly. | AUD-023-008, AUD-023-009, AUD-023-011 |
| SC-007 | UNVERIFIED | 500ms p95 is specified; [logging](../../apps/api/app/api/routes/governance_dashboard.py#L49) warns at 2000ms and no matching thirteen-endpoint measurements were established. | AUD-023-032 |
| SC-008 | PARTIAL | Seed-backed structures exist, but [bootstrap](../../packages/domain/src/domain/seed/bootstrap.py#L13) failure, fake details/export, and [hidden UI errors](../../apps/web/src/app/governance/dashboard/compliance/page.tsx#L22) contradict reliable empty-store behavior. | AUD-023-023, AUD-023-024, AUD-023-027, AUD-023-032 |
| SC-009 | PARTIAL | Existing clients largely share snake_case models; [nonempty audit constructor](../../apps/api/app/services/dashboard_aggregation_service.py#L265) and contract error differences break scoped obligations. Runtime consumer success UNVERIFIED. | AUD-023-008, AUD-023-023, AUD-023-030, AUD-023-032 |
| SC-010 | PARTIAL | [Source rows](../../apps/api/app/services/governance_data_service.py#L623) lack ten assessment cells and visible baseline provenance. | AUD-023-005, AUD-023-006 |

### Nonfunctional and Cross-Cutting Obligations

No original NFR IDs were found. These are obligations already expressed in the spec/plan, not newly invented NFRs.

| Obligation | Status | Evidence / boundary | Follow-ups |
| --- | --- | --- | --- |
| All thirteen endpoints below 500ms p95 | UNVERIFIED | SC-007/T076 require measurement, not the RT-005 estimates or seed-cache existence. | AUD-023-032 |
| Stable endpoint/response/error contracts | PARTIAL | Endpoint catalogue above; [error middleware](../../apps/api/app/middleware/error_handler.py#L110) does not emit the stated `detail` envelope for these routes. | AUD-023-008, AUD-023-023, AUD-023-030 |
| Tenant isolation, including concurrent requests | PARTIAL | Tenant labels do not constrain the [repository calls](../../apps/api/app/services/governance_data_service.py#L691). | AUD-023-001, AUD-023-002 |
| Growth beyond baseline counts | PARTIAL | List loops are dynamic, but all-record materialization, missing pagination guarantees, and no larger-data measurements remain. | AUD-023-026, AUD-023-029, AUD-023-032 |
| Australia East residency | UNVERIFIED | Plan/assumption and UI residency banner are assertions, not region/deployment evidence. No cloud inspection was authorized. | AUD-023-032, AUD-023-033 |
| No new external data dependencies; unchanged score weights | IMPLEMENTED | Dashboard path uses local seed; [weights](../../apps/api/app/services/health_score_service.py#L21) remain 0.40/0.25/0.20/0.15. Does not establish real stored inputs. | AUD-023-003, AUD-023-030 |
| Source freshness and manual update semantics | PARTIAL | CHK070 remains a requirements gap; [freshness timestamp](../../apps/api/app/services/dashboard_aggregation_service.py#L116) is synthetic source-age evidence. No extra freshness SLA is assumed. | AUD-023-025, AUD-023-031 |
| Immutable audit entries | PARTIAL | [Audit append](../../apps/api/app/repositories/governance_repository.py#L456) is an upsert. | AUD-023-012 |

## Acceptance Scenario Coverage

USx.y labels below correspond exactly to the numbered scenarios under each original user story.

| Scenario | Status | Required outcome versus inspected path | Follow-ups |
| --- | --- | --- | --- |
| US1.1 | PARTIAL | [Summary](../../apps/api/app/services/dashboard_aggregation_service.py#L56) uses real seed counts, but not all real dimension inputs. | AUD-023-003, AUD-023-004, AUD-023-015, AUD-023-021 |
| US1.2 | MISSING | [Gates](../../apps/api/app/services/governance_data_service.py#L77) do not read stored assessment results. | AUD-023-004 |
| US1.3 | PARTIAL | Seed heuristics exist, but no stored-empty decision or explicit fallback metadata. | AUD-023-003, AUD-023-006 |
| US1.4 | PARTIAL | [Seed status ratios](../../apps/api/app/services/governance_data_service.py#L230) work; registry operational status path and mixed-status verification incomplete. | AUD-023-003, AUD-023-029 |
| US1.5 | MISSING | [Recovery input](../../apps/api/app/services/governance_data_service.py#L275) ignores completion/tracker state. | AUD-023-021, AUD-023-022 |
| US2.1 | PARTIAL | [Actual phase join](../../apps/api/app/services/governance_data_service.py#L322) is not exposed as counts. | AUD-023-017 |
| US2.2 | IMPLEMENTED | [Six AIIMS functions](../../apps/api/app/services/governance_data_service.py#L340) derived from org assignments; execution unverified. | AUD-023-029 |
| US2.3 | PARTIAL | [Global hazard sets](../../apps/api/app/services/governance_data_service.py#L419) are not jurisdiction/primary-capability matching. | AUD-023-016 |
| US2.4 | PARTIAL | [24 eligible orgs](../../apps/api/app/services/governance_data_service.py#L466) counted; required distributions/coverage not delivered. | AUD-023-018 |
| US2.5 | MISSING | [Plan summaries](../../apps/api/app/services/governance_data_service.py#L366) never query stored plans. | AUD-023-015 |
| US3.1 | PARTIAL | [Five display rows](../../apps/api/app/services/dashboard_aggregation_service.py#L462) are not five independent catalogue-backed counts. | AUD-023-020 |
| US3.2 | PARTIAL | [Detail loops](../../apps/api/app/services/governance_data_service.py#L522) can yield 24/57/53 lists from social seed, but summary counts/types/targets/tracking remain incomplete. | AUD-023-020, AUD-023-022, AUD-023-029 |
| US3.3 | MISSING | [Tracker updates](../../apps/api/app/services/recovery_service.py#L83) never enter dashboard progress. | AUD-023-021 |
| US3.4 | PARTIAL | Zero progress is present, but [active flag](../../apps/api/app/services/dashboard_aggregation_service.py#L523) and [page inactive branch](../../apps/web/src/app/governance/dashboard/recovery/page.tsx#L147) misrepresent/hide the baseline. | AUD-023-020, AUD-023-021 |
| US4.1 | MISSING | [Severity](../../apps/api/app/services/governance_data_service.py#L582) is not calculated from records. | AUD-023-013 |
| US4.2 | PARTIAL | Zero counts exist but are unconditional, and no explicit no-assessments provenance is supplied. | AUD-023-006, AUD-023-013 |
| US4.3 | PARTIAL | [Tier heuristic](../../apps/api/app/services/governance_data_service.py#L590) lacks principled alignment/empty denominator. | AUD-023-014 |
| US4.4 | MISSING | [Top risks](../../apps/api/app/services/governance_data_service.py#L586) has no ranking. | AUD-023-013 |
| US5.1 | PARTIAL | [Read adapter](../../apps/api/app/services/governance_data_service.py#L691) is dormant; nonempty [serialization](../../apps/api/app/services/dashboard_aggregation_service.py#L265) is wrong. | AUD-023-003, AUD-023-008, AUD-023-009 |
| US5.2 | PARTIAL | [Assessment event write](../../apps/api/app/services/governance_registry.py#L112) exists; not retrievable through the routed dashboard. | AUD-023-008, AUD-023-009, AUD-023-011 |
| US5.3 | PARTIAL | Source/action/date query subset exists, actor/keyword/entity/date/paging behavior incomplete. | AUD-023-009, AUD-023-026 |
| US5.4 | MISSING | [Chain](../../apps/api/app/services/dashboard_aggregation_service.py#L296) is always empty. | AUD-023-010 |
| US6.1 | PARTIAL | [Source aggregate status](../../apps/api/app/services/governance_data_service.py#L623) is not real per-principle assessment output. | AUD-023-005 |
| US6.2 | PARTIAL | Seed source rows exist, but no ten-gate matrix or visible seed-baseline marker. | AUD-023-005, AUD-023-006 |
| US6.3 | MISSING | [Stored branch](../../apps/api/app/services/governance_data_service.py#L623) replaces seed collection instead of merging assessed/unassessed results. | AUD-023-005, AUD-023-006 |

The US1 narrative's component drill-down is also incomplete: [gate links](../../apps/web/src/components/governance/dashboard/ConstitutionalGates.tsx#L63)
lead to an unfiltered matrix, and the dashboard detail does not expose the producing assessments. AUD-023-007
tracks this narrative obligation without inventing an extra numbered acceptance scenario.

### Edge Cases

EC labels identify the seven original bullets in order; they are audit-local labels, not added requirements.

| Edge case | Status | Evidence | Follow-ups |
| --- | --- | --- | --- |
| EC-01: Empty store and failed seed | PARTIAL | [Summary catches exceptions](../../apps/api/app/api/routes/governance_dashboard.py#L568); other views may 500 or display misleading empty/synthetic data. | AUD-023-023, AUD-023-024 |
| EC-02: Partially loaded seed | PARTIAL | [Constructor defaults](../../apps/api/app/services/governance_data_service.py#L55) allow missing keys but provide no per-section incompleteness; empty comparisons can pass gates. | AUD-023-004, AUD-023-023 |
| EC-03: Missing/malformed recovery domain | MISSING | [Parser](../../packages/domain/src/domain/seed/bootstrap.py#L13) aborts on malformed JSON; service manufactures missing domain rows without unavailable status. | AUD-023-020, AUD-023-023 |
| EC-04: Organisation without AIIMS functions | IMPLEMENTED | [Function loop](../../apps/api/app/services/governance_data_service.py#L340) excludes it from assignments; [general org metrics](../../apps/api/app/services/governance_data_service.py#L312) retain organisations. Runtime edge test absent. | AUD-023-029 |
| EC-05: Assignment references unknown entity | MISSING | [PPRR join](../../apps/api/app/services/governance_data_service.py#L322) drops unknown frameworks and never flags unknown jurisdictions in detail. | AUD-023-017 |
| EC-06: Superseded constitutional assessment | MISSING | [Repository predicate](../../apps/api/app/repositories/governance_repository.py#L64) is disconnected from dashboard gate/matrix computation. | AUD-023-004, AUD-023-005 |
| EC-07: All sources have same status | IMPLEMENTED | [Available-status counting](../../apps/api/app/services/governance_data_service.py#L230) and [score formula](../../apps/api/app/services/health_score_service.py#L153) yield 100 for an all-available nonempty seed. This is static derivation, not an executed check. | AUD-023-029 |

### Clarifications and Assumptions

CL and AS labels are audit-local, preserving the original order and wording intent.

| Decision | Status | Evidence / interpretation | Follow-ups |
| --- | --- | --- | --- |
| CL-01: Canonical AIDR gate names | IMPLEMENTED | [Ten names](../../apps/api/app/services/governance_data_service.py#L16) match FR-001. Mapping those names to real assessment evidence is separately incomplete. | AUD-023-004 |
| CL-02: 46 sources is dynamic baseline | IMPLEMENTED | [Source iteration](../../apps/api/app/services/governance_data_service.py#L623) has no hard 46 limit; larger-scale outcomes unverified. | AUD-023-029, AUD-023-032 |
| CL-03: Bootstrap loads five domains and evaluation questions | IMPLEMENTED | [Loader](../../packages/domain/src/domain/seed/bootstrap.py#L13) and [returned key](../../packages/domain/src/domain/seed/bootstrap.py#L42) implement this structural change. | AUD-023-023 |
| CL-04: Seed-derived exercise MVP, zero absent exercise data | PARTIAL | [Headline input](../../apps/api/app/services/governance_data_service.py#L253) returns zero for missing metadata; exercise-type breakdown uses unrelated phase counts. | AUD-023-019 |
| CL-05: Only actual actions create audit entries | CONFLICT | [Automatic catalogue import](../../apps/api/app/api/governance.py#L64) calls [registration audit emission](../../apps/api/app/services/governance_registry.py#L57). Empty dashboard is currently caused by disconnection, not proof of compliance. | AUD-023-011 |
| AS-01: Score weighting/algorithm unchanged | IMPLEMENTED | [Health algorithm](../../apps/api/app/services/health_score_service.py#L21) and [unit assertions](../../tests/unit/test_health_score_service.py#L12) preserve weights; correct inputs remain required. | AUD-023-004, AUD-023-021 |
| AS-02: Thirteen paths/shapes; additive metadata only | PARTIAL | Paths exist; metadata is absent and nonempty audit/error paths disagree. | AUD-023-006, AUD-023-008, AUD-023-023 |
| AS-03: Dataset counts are baseline; scale without degradation | PARTIAL | Static counts confirmed and loops dynamic; no populated/larger-data p95 evidence. | AUD-023-029, AUD-023-032 |
| AS-04: All ten gates evaluable without external API | PARTIAL | [Seed heuristics](../../apps/api/app/services/governance_data_service.py#L77) avoid external calls but do not establish gate criteria or real compliance. | AUD-023-004, AUD-023-031 |
| AS-05: Existing seven plan lifecycle states | PARTIAL | [Seven response labels](../../apps/api/app/models/governance_health.py#L135) exist; [stored plan lifecycle](../../apps/api/app/services/emergency_plan_service.py#L123) requires explicit adaptation and real counting. | AUD-023-015 |
| AS-06: Six standard AIIMS functions | IMPLEMENTED | [Function list](../../apps/api/app/services/governance_data_service.py#L42) and assigned-function iteration match. | AUD-023-029 |
| AS-07: `is_current` identifies superseded assessments | IMPLEMENTED | [Model flag](../../packages/domain/src/domain/models/constitutional_assessment.py#L20) and [supersession writer](../../apps/api/app/services/governance_registry.py#L112) exist; not consumed by dashboard. | AUD-023-004, AUD-023-005 |
| AS-08: Workforce type defines volunteer inclusion | IMPLEMENTED | [Filter](../../apps/api/app/services/governance_data_service.py#L466) uses volunteer/mixed only; availability/distribution obligations remain. | AUD-023-018 |
| AS-09: All data resides in Australia East | UNVERIFIED | Documented constraint; no approved region/deployment evidence established by this static audit. | AUD-023-032, AUD-023-033 |

### Appended Persona, Hypothesis, and Scope Entries

| Entry | Status | Evidence / limit | Follow-ups |
| --- | --- | --- | --- |
| PER-061 | UNVERIFIED | AU AIIMS persona cross-reference is authored in [spec.md](spec.md); this audit did not establish named, dated practitioner validation required by the linked persona contract. | AUD-023-033 |
| PER-062 | UNVERIFIED | Technical-actor cross-reference and “validated” text exist; no scoped consultation/sign-off record establishes this claim. | AUD-023-033 |
| PER-063 | IMPLEMENTED | Explicit PH/JP/BD placeholder and preconditions are authored; no country persona validation or implementation is claimed. | AUD-023-033 |
| HYP-021 | UNVERIFIED | Hypothesis/falsification text exists, named stub is MISSING in S5, and portfolio 1.8-to-3.8 narrative does not establish this spec's consultation/causal uplift. | AUD-023-033 |
| SCP-067 | IMPLEMENTED | Country variants are explicitly deferred pending D-009, regulatory/data-sharing conditions, and responsible review. No promotion is inferred. | AUD-023-033 |
| SCP-068 | IMPLEMENTED | Constitutional changes are explicitly excluded; no constitutional amendment was made or authorized here. | AUD-023-031 |
| SCP-069 | IMPLEMENTED | 018 recovery-phase and 008 warning-authoring authority are explicitly deferred; this report targets dashboard consumption only. | AUD-023-031 |

## Original Task Coverage

Every original task has one row. Original checkboxes are reproduced literally; an unchecked task can have
IMPLEMENTED source support. Delegation-only tasks receive credit even when their upstream computation needs
separate remediation. Planned `compute_*` names were compared with actual `get_*` methods before negatives.
All test execution claims remain UNVERIFIED regardless of test-source status.

| Original task | Original state | Status | Concrete evidence / remaining obligation | Follow-ups |
| --- | --- | --- | --- | --- |
| T001 [source](tasks.md#L29) | [ ] | UNVERIFIED | Branch-creation history/from-main ancestry not established; matching spec name is not proof. Do not recreate it during remediation. | AUD-023-032 |
| T002 [source](tasks.md#L30) | [ ] | IMPLEMENTED | [Bootstrap](../../packages/domain/src/domain/seed/bootstrap.py#L13) loads five domain files and evaluation questions into the recovery catalogue key. | AUD-023-023 |
| T003 [source](tasks.md#L40) | [ ] | IMPLEMENTED | [Constructor](../../apps/api/app/services/governance_data_service.py#L55) accepts seed/optional repository and pre-indexes frameworks/organisations. | AUD-023-001, AUD-023-003 |
| T004 [source](tasks.md#L41) | [ ] | MISSING | [Route helper](../../apps/api/app/api/routes/governance_dashboard.py#L71) is a global lazy singleton, not `get_seed_data`/Depends request injection. S1 checked actual replacement. | AUD-023-003 |
| T005 [source](tasks.md#L42) | [ ] | IMPLEMENTED | [Aggregation constructor](../../apps/api/app/services/dashboard_aggregation_service.py#L44) accepts data service alongside health and repository. | AUD-023-003 |
| T006 [source](tasks.md#L43) | [ ] | PARTIAL | [Shared helper](../../apps/api/app/api/routes/governance_dashboard.py#L71) supplies seed service to data routes, but no injected stored adapters; exports follow a separate stub. | AUD-023-003, AUD-023-027 |
| T006a [source](tasks.md#L45) | [ ] | MISSING | [Response models](../../apps/api/app/models/governance_health.py#L20) omit additive `data_source_type`. | AUD-023-006 |
| T006b [source](tasks.md#L46) | [ ] | MISSING | [TypeScript types](../../apps/web/src/lib/api/governance.ts#L47) omit the planned provenance property/mapping. | AUD-023-006 |
| T007 [source](tasks.md#L62) | [ ] | MISSING | S4 found no data-service test; [fallback aggregate tests](../../tests/unit/test_dashboard_aggregation.py#L6) do not exercise current assessment gates. | AUD-023-004, AUD-023-029 |
| T008 [source](tasks.md#L63) | [ ] | MISSING | No direct mixed-status seed data-service assertions in S4; [algorithm tests](../../tests/unit/test_health_score_service.py#L19) supply precomputed stats. | AUD-023-029 |
| T009 [source](tasks.md#L64) | [ ] | PARTIAL | [Summary unit tests](../../tests/unit/test_dashboard_aggregation.py#L6) check shape/nonnegative values without the data service or seed-sensitive assertions. | AUD-023-028, AUD-023-030 |
| T010 [source](tasks.md#L65) | [ ] | PARTIAL | [Schema test](../../tests/contract/test_governance_dashboard_contract.py#L18) constructs canned values; [HTTP checks](../../tests/integration/test_governance_dashboard_api.py#L25) do not verify the populated contract fully. | AUD-023-030 |
| T011 [source](tasks.md#L69) | [ ] | PARTIAL | [Renamed gate function](../../apps/api/app/services/governance_data_service.py#L77) returns ten seed-derived gates but no stored/current assessment mapping. | AUD-023-004 |
| T012 [source](tasks.md#L70) | [ ] | IMPLEMENTED | [Seed status counters](../../apps/api/app/services/governance_data_service.py#L230) implement available/degraded derivation dynamically. Dormant stored/fallback differences are separately tracked. | AUD-023-003, AUD-023-029 |
| T013 [source](tasks.md#L71) | [ ] | PARTIAL | [Readiness inputs](../../apps/api/app/services/governance_data_service.py#L253) compute role/review/plan ratios, but plan data is not stored and metadata assumptions mismatch seed. | AUD-023-015, AUD-023-019 |
| T014 [source](tasks.md#L72) | [ ] | PARTIAL | [Recovery input](../../apps/api/app/services/governance_data_service.py#L275) reads catalogue structure but excludes overarching and never reads active trackers. | AUD-023-020, AUD-023-021 |
| T015 [source](tasks.md#L73) | [ ] | IMPLEMENTED | [Summary](../../apps/api/app/services/dashboard_aggregation_service.py#L56) delegates gates to the real data-service surface; upstream behavior incomplete. | AUD-023-004 |
| T016 [source](tasks.md#L74) | [ ] | IMPLEMENTED | [Summary](../../apps/api/app/services/dashboard_aggregation_service.py#L56) replaces 10/7/2 with data-service statistics. | AUD-023-003, AUD-023-029 |
| T017 [source](tasks.md#L75) | [ ] | IMPLEMENTED | [Summary](../../apps/api/app/services/dashboard_aggregation_service.py#L56) delegates readiness instead of fixed 75/85/80. | AUD-023-015, AUD-023-019 |
| T018 [source](tasks.md#L76) | [ ] | IMPLEMENTED | [Summary](../../apps/api/app/services/dashboard_aggregation_service.py#L56) delegates recovery input; constant inactivity moved upstream and remains a defect. | AUD-023-021 |
| T019 [source](tasks.md#L77) | [ ] | PARTIAL | Delegation exists, but [risk counts](../../apps/api/app/services/governance_data_service.py#L303) are unconditional zero rather than stored severity computation. | AUD-023-013 |
| T020 [source](tasks.md#L78) | [ ] | PARTIAL | [Incident counter](../../apps/api/app/services/governance_data_service.py#L308) replaced 1 with constant 0, not a query of actual incidents. | AUD-023-028 |
| T021 [source](tasks.md#L79) | [ ] | IMPLEMENTED | [Utilisation computation](../../apps/api/app/services/governance_data_service.py#L312) derives an org-capability ratio instead of 72.5; its operational label remains misleading. | AUD-023-028 |
| T022 [source](tasks.md#L80) | [ ] | PARTIAL | [Summary assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L56) passes structured inputs to unchanged health calculation, but several inputs are not actual records. | AUD-023-003, AUD-023-004, AUD-023-021, AUD-023-028 |
| T023 [source](tasks.md#L94) | [ ] | MISSING | No direct 123-assignment phase-count test in S4; [existing test](../../tests/unit/test_dashboard_aggregation.py#L70) checks four phase names only. | AUD-023-017, AUD-023-029 |
| T024 [source](tasks.md#L95) | [ ] | MISSING | No direct six-function/org-coverage test in S4; [fallback test](../../tests/unit/test_dashboard_aggregation.py#L80) expects ten roles. | AUD-023-016, AUD-023-029 |
| T025 [source](tasks.md#L96) | [ ] | MISSING | No data-service test of eligible workforce, jurisdiction distribution, and capabilities in S4. [Readiness tests](../../tests/unit/test_dashboard_aggregation.py#L64) omit volunteer assertions. | AUD-023-018, AUD-023-029 |
| T026 [source](tasks.md#L97) | [ ] | MISSING | [Existing readiness test](../../tests/unit/test_dashboard_aggregation.py#L84) only asserts nonnegative gap count, not jurisdiction/capability matching. | AUD-023-016, AUD-023-029 |
| T027 [source](tasks.md#L98) | [ ] | PARTIAL | [Readiness schema](../../tests/contract/test_governance_dashboard_contract.py#L121) uses canned/empty data; no populated route contract assertion. | AUD-023-030 |
| T028 [source](tasks.md#L102) | [ ] | PARTIAL | [Join](../../apps/api/app/services/governance_data_service.py#L322) computes four-phase dictionary; counts/orphan references do not survive into requested view entries. | AUD-023-017 |
| T029 [source](tasks.md#L103) | [ ] | IMPLEMENTED | [Six-function coverage](../../apps/api/app/services/governance_data_service.py#L340) counts org function assignments. Jurisdictional gap interpretation remains separate. | AUD-023-016, AUD-023-029 |
| T030 [source](tasks.md#L104) | [ ] | PARTIAL | [Seven-state helper](../../apps/api/app/services/governance_data_service.py#L366) is present but has no stored-plan query; zero/expectation instructions conflict. | AUD-023-015, AUD-023-031 |
| T031 [source](tasks.md#L105) | [ ] | PARTIAL | [Volunteer helper](../../apps/api/app/services/governance_data_service.py#L466) filters correctly but supplies only aggregate coverage counts and assumed availability. | AUD-023-018 |
| T032 [source](tasks.md#L106) | [ ] | PARTIAL | [Gap helper](../../apps/api/app/services/governance_data_service.py#L419) lacks required per-jurisdiction primary-capability/assignment comparison. | AUD-023-016 |
| T033 [source](tasks.md#L107) | [ ] | IMPLEMENTED | [Readiness assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L312) delegates plan summaries, replacing fixed seven-times-three counts. | AUD-023-015 |
| T034 [source](tasks.md#L108) | [ ] | IMPLEMENTED | [Data-backed readiness](../../apps/api/app/services/dashboard_aggregation_service.py#L312) delegates six AIIMS functions; no-service fallback still has ten old roles. | AUD-023-030 |
| T035 [source](tasks.md#L109) | [ ] | PARTIAL | [Assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L312) calls all relevant helpers but drops distributions and retains proxy exercise/availability metrics. | AUD-023-016, AUD-023-017, AUD-023-018, AUD-023-019 |
| T036 [source](tasks.md#L123) | [ ] | MISSING | No data-service five-domain/count/tracker test in S4; [unit recovery checks](../../tests/unit/test_dashboard_aggregation.py#L90) are conditional fallback tests. | AUD-023-020, AUD-023-029 |
| T037 [source](tasks.md#L124) | [ ] | MISSING | No 24/57/53 social detail assertion in S4; [detail unit test](../../tests/unit/test_dashboard_aggregation.py#L119) checks domain only. | AUD-023-020, AUD-023-022, AUD-023-029 |
| T038 [source](tasks.md#L125) | [ ] | PARTIAL | [Recovery schema cases](../../tests/contract/test_governance_dashboard_contract.py#L145) allow empty domains even when active; not real five-domain contract validation. | AUD-023-030 |
| T039 [source](tasks.md#L129) | [ ] | PARTIAL | [Domain helper](../../apps/api/app/services/governance_data_service.py#L491) handles four baseline domains; no real overarching or tracker merge. | AUD-023-020, AUD-023-021 |
| T040 [source](tasks.md#L130) | [ ] | PARTIAL | [Detail](../../apps/api/app/services/governance_data_service.py#L522) uses real titles/lists, but no completion merge and false target/type semantics. | AUD-023-021, AUD-023-022 |
| T041 [source](tasks.md#L131) | [ ] | PARTIAL | [Active helper](../../apps/api/app/services/governance_data_service.py#L730) is always false; delegated check does not inspect stored trackers. | AUD-023-021 |
| T042 [source](tasks.md#L132) | [ ] | PARTIAL | [Assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L462) replaces old percentages with four baseline rows plus synthetic overarching, not five actual domain counts. | AUD-023-020 |
| T043 [source](tasks.md#L133) | [ ] | PARTIAL | [Progress/detail assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L462) delegates some catalogue data but invents active state/incident context and lacks tracker targets. | AUD-023-020, AUD-023-021, AUD-023-022 |
| T044 [source](tasks.md#L147) | [ ] | MISSING | No stored hazard grouping/zero-state data-service test in S4; [unit risk assertions](../../tests/unit/test_dashboard_aggregation.py#L130) check nonnegativity only. | AUD-023-013, AUD-023-029 |
| T045 [source](tasks.md#L148) | [ ] | MISSING | No severity/confidence ranking test found in S4; [top-risk function](../../apps/api/app/services/governance_data_service.py#L586) is empty. | AUD-023-013, AUD-023-029 |
| T046 [source](tasks.md#L149) | [ ] | MISSING | [Existing principle count test](../../tests/unit/test_dashboard_aggregation.py#L145) does not exercise trust configuration through the data service. | AUD-023-014, AUD-023-029 |
| T047 [source](tasks.md#L150) | [ ] | PARTIAL | [Risk schema fixture](../../tests/contract/test_governance_dashboard_contract.py#L165) validates constructed types, not the populated GET result. | AUD-023-030 |
| T048 [source](tasks.md#L154) | [ ] | MISSING | [Severity function](../../apps/api/app/services/governance_data_service.py#L582) has no record query/grouping. | AUD-023-013 |
| T049 [source](tasks.md#L155) | [ ] | MISSING | [Top risks](../../apps/api/app/services/governance_data_service.py#L586) performs no query/order operation. | AUD-023-013 |
| T050 [source](tasks.md#L156) | [ ] | PARTIAL | [AWS function](../../apps/api/app/services/governance_data_service.py#L590) uses seed tiers but copies one ratio to ten principles without a supported alignment mapping. | AUD-023-014 |
| T051 [source](tasks.md#L157) | [ ] | PARTIAL | [Risk assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L560) delegates a breakdown, but delegated values remain constant. | AUD-023-013 |
| T052 [source](tasks.md#L158) | [ ] | PARTIAL | [Risk assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L560) delegates top risks/principles, not real populated risk records or sufficient warning evidence. | AUD-023-013, AUD-023-014 |
| T053 [source](tasks.md#L159) | [ ] | MISSING | [Risk detail](../../apps/api/app/services/dashboard_aggregation_service.py#L641) fabricates any ID; no actual HazardAssessment or not-found query. | AUD-023-013 |
| T054 [source](tasks.md#L173) | [ ] | MISSING | No direct full-filter data-service test in S4; [registry audit test](../../tests/contract/test_governance_dashboard.py#L87) covers another surface. | AUD-023-009, AUD-023-029 |
| T055 [source](tasks.md#L174) | [ ] | MISSING | [API chain test](../../tests/integration/test_governance_dashboard_api.py#L120) checks list shape for an arbitrary ID, not links/not-found behavior. | AUD-023-010, AUD-023-029 |
| T056 [source](tasks.md#L175) | [ ] | PARTIAL | [Audit schema](../../tests/contract/test_governance_dashboard_contract.py#L107) uses empty events; required nonempty event fields and true count are untested. | AUD-023-008, AUD-023-030 |
| T057 [source](tasks.md#L179) | [ ] | PARTIAL | [Search adapter](../../apps/api/app/services/governance_data_service.py#L691) exists but is not tenant-wide and omits required filters/related-entity behavior. | AUD-023-009 |
| T058 [source](tasks.md#L180) | [ ] | MISSING | S1/S2 found no dashboard linked-event traversal; [chain assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L296) is constant empty. | AUD-023-010 |
| T059 [source](tasks.md#L181) | [ ] | PARTIAL | [Audit assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L225) delegates but nonempty serialization has required-field mismatch. | AUD-023-008, AUD-023-009 |
| T060 [source](tasks.md#L182) | [ ] | MISSING | [Chain method](../../apps/api/app/services/dashboard_aggregation_service.py#L296) has no real delegation or lookup. | AUD-023-010 |
| T061 [source](tasks.md#L196) | [ ] | MISSING | No current/mixed/ten-gate data-service test in S4; [schema matrix test](../../tests/contract/test_governance_dashboard_contract.py#L92) only constructs empty rows. | AUD-023-005, AUD-023-029 |
| T062 [source](tasks.md#L197) | [ ] | PARTIAL | [Schema matrix](../../tests/contract/test_governance_dashboard_contract.py#L92) and [HTTP paging](../../tests/integration/test_governance_dashboard_api.py#L77) check shape/page size, not real entries. | AUD-023-026, AUD-023-030 |
| T063 [source](tasks.md#L201) | [ ] | PARTIAL | [Entries](../../apps/api/app/services/governance_data_service.py#L623) support aggregate stored sources or baseline rows, not current assessments plus unassessed-source merge. | AUD-023-005 |
| T064 [source](tasks.md#L202) | [ ] | IMPLEMENTED | [Matrix assembly](../../apps/api/app/services/dashboard_aggregation_service.py#L122) delegates to renamed data-service entry builder. | AUD-023-005, AUD-023-006 |
| T065 [source](tasks.md#L203) | [ ] | PARTIAL | [Matrix/detail](../../apps/api/app/services/dashboard_aggregation_service.py#L193) use source entries but history is always empty and unknown source succeeds. | AUD-023-005, AUD-023-007 |
| T066 [source](tasks.md#L213) | [ ] | PARTIAL | [Missing-key defaults](../../apps/api/app/services/governance_data_service.py#L55) exist; partial/incomplete status and malformed structures are not isolated. | AUD-023-023 |
| T067 [source](tasks.md#L214) | [ ] | MISSING | [Domain parser](../../packages/domain/src/domain/seed/bootstrap.py#L13) has no per-domain malformed-file handling or unavailable report. | AUD-023-020, AUD-023-023 |
| T068 [source](tasks.md#L215) | [ ] | PARTIAL | [Summary 503](../../apps/api/app/api/routes/governance_dashboard.py#L568) is partial handling; other endpoints/error bodies do not follow the same contract. | AUD-023-023, AUD-023-024 |
| T069 [source](tasks.md#L216) | [ ] | MISSING | [Current-assessment query](../../apps/api/app/repositories/governance_repository.py#L64) exists elsewhere but is unused by this data service. | AUD-023-004, AUD-023-005 |
| T070 [source](tasks.md#L217) | [ ] | IMPLEMENTED | [Resolved module path](../../apps/api/app/api/routes/governance_dashboard.py#L77) and [string cache key](../../apps/api/app/services/seed_service.py#L8) are consistent across the helper's consumers; cache-hit execution not measured. | AUD-023-025, AUD-023-032 |
| T071 [source](tasks.md#L218) | [ ] | PARTIAL | [Unit suite](../../tests/unit/test_dashboard_aggregation.py#L10) still bypasses real data and retains ten-role/vacuous recovery checks. | AUD-023-030 |
| T072 [source](tasks.md#L219) | [ ] | PARTIAL | [Registry tests](../../tests/contract/test_governance_dashboard.py#L46) do test stored source counts/gaps/audit actions, but not the new dashboard pipeline. | AUD-023-030 |
| T073 [source](tasks.md#L220) | [ ] | IMPLEMENTED | [Contract source](../../tests/contract/test_governance_dashboard_contract.py#L107) uses `events`, and config uses `user_roles/widget_layout/poll_interval_ms`; stronger behavioral assertions remain. | AUD-023-030 |
| T074 [source](tasks.md#L221) | [ ] | PARTIAL | [Integration file](../../tests/integration/test_governance_dashboard_api.py#L1) exists, but lacks populated data, mutation, filter correctness, and negative isolation assertions. | AUD-023-030 |
| T075 [source](tasks.md#L222) | [ ] | UNVERIFIED | No full-suite execution established; one named suite is absent in S4. | AUD-023-029, AUD-023-032 |
| T076 [source](tasks.md#L223) | [ ] | UNVERIFIED | No ten-request-per-endpoint p95 measurement established; [two-second logger](../../apps/api/app/api/routes/governance_dashboard.py#L49) is not the required acceptance assertion. | AUD-023-032 |
| T077 [source](tasks.md#L224) | [ ] | UNVERIFIED | [Quickstart](quickstart.md) contains commands, not validated execution or deployment records. No commands/deployments run here. | AUD-023-032 |
| T078 [source](tasks.md#L225) | [ ] | MISSING | No data-service two-tenant test in S4; [simulation API test](../../tests/integration/test_governance_dashboard_api.py#L35) only asserts a tenant field exists. | AUD-023-001, AUD-023-002, AUD-023-029 |
| T079 [source](tasks.md#L226) | [ ] | MISSING | [Compliance UI](../../apps/web/src/components/governance/dashboard/ComplianceMatrix.tsx#L17) has status badges, not stored-versus-seed-baseline badges. | AUD-023-006 |

## Review, Checklist, and Evidence Assessment

Authored checkboxes are not human approval or successful execution. The following tables assess the actual
claims/questions without changing their original states. QC labels identify the sixteen unnumbered quality
checklist rows in order. CHK IDs are the original review-checklist identifiers. Content assessment is not sign-off.

### Quality Checklist Claims

Source: [checklists/requirements.md](checklists/requirements.md). All original states are checked.

| Claim | Original state | Assessment | Evidence / follow-up |
| --- | --- | --- | --- |
| QC-01: No implementation details | [x] | PARTIAL | Spec includes model field names, an endpoint count, and bootstrap/code-contract clarifications. Authored quality claim is broader than the content. AUD-023-031. |
| QC-02: User/business value focus | [x] | IMPLEMENTED | Six stories explain emergency-management decision value in [spec.md](spec.md). |
| QC-03: Nontechnical stakeholder language | [x] | PARTIAL | Business stories are clear, but later clarifications/assumptions require code/model knowledge. AUD-023-031. |
| QC-04: Mandatory sections complete | [x] | IMPLEMENTED | Scenarios, requirements/entities, and success criteria are present. |
| QC-05: No clarification markers remain | [x] | IMPLEMENTED | No unresolved marker in the feature specification; absence of markers does not resolve the documented design conflicts. |
| QC-06: Testable/unambiguous requirements | [x] | PARTIAL | Target source, AWS mapping, plan fallback, chain semantics, and metadata decisions remain contradictory/underspecified. AUD-023-031. |
| QC-07: Measurable success criteria | [x] | PARTIAL | Counts/p95/zero-stub goals measurable; “meaningful” all-endpoint empty-store behavior needs detail/error exceptions. AUD-023-031. |
| QC-08: Technology-agnostic success criteria | [x] | PARTIAL | Outcomes are user-facing, but criteria reference endpoint response contracts and internal stub pipeline. AUD-023-031. |
| QC-09: All acceptance scenarios defined | [x] | PARTIAL | Twenty-five scenarios exist; failure, auth, mutation, target, and chain edge semantics are incomplete. AUD-023-031. |
| QC-10: Edge cases identified | [x] | IMPLEMENTED | Seven explicit original edge cases, all mapped in this report. |
| QC-11: Clearly bounded scope | [x] | IMPLEMENTED | Six views/thirteen endpoints plus explicit PER/HYP/SCP appendices; country and 018/008 deferrals retained. |
| QC-12: Dependencies/assumptions identified | [x] | PARTIAL | Named entities and assumptions exist, but stored-source adapters, framework schema, and target data were over-assumed. AUD-023-003, AUD-023-031. |
| QC-13: All FRs have clear acceptance criteria | [x] | PARTIAL | Some FRs, especially FR-012/016/019/021/027, lack full operational acceptance detail. AUD-023-031. |
| QC-14: Primary flows covered | [x] | IMPLEMENTED | Six primary user stories are authored; implementation coverage differs as shown above. |
| QC-15: Feature meets measurable outcomes | [x] | UNVERIFIED | An authored spec-quality checkbox cannot establish tests, p95, rollout, or successful stored-data behavior. AUD-023-032. |
| QC-16: No implementation leakage | [x] | PARTIAL | Same content limitation as QC-01; no retrospective checklist rewrite performed. AUD-023-031. |

The checklist note “All items pass validation” is an authored assertion, not a retained validation transcript
or reviewer signature. The “ready for clarify/plan” note does not establish implementation readiness.

### Review Checklist Questions

Source: [checklists/review.md](checklists/review.md). All 72 original states remain unchecked. References to
FR/SC/US/RT below identify the fully read local documents and the requirement tables above. All outstanding
document decisions route to AUD-023-031; execution/sign-off claims route to AUD-023-032 or AUD-023-033.

| Review item | Original state | Content assessment | Evidence / disposition |
| --- | --- | --- | --- |
| CHK001 | [ ] | IMPLEMENTED | FR-001 to FR-004 and unchanged algorithm specify 40/25/20/15, totaling 100. |
| CHK002 | [ ] | PARTIAL | Existing algorithm excludes pending and half-weights partial; spec does not state all aggregation/multi-source rules. AUD-023-004, AUD-023-031. |
| CHK003 | [ ] | PARTIAL | Algorithm averages three inputs, but FR-002 also names capabilities/assignments without a full reconciliation. AUD-023-015, AUD-023-019. |
| CHK004 | [ ] | PARTIAL | Source algorithm grants half credit for degraded-equivalent partial; spec wording and registry compliance/status semantics differ. AUD-023-003, AUD-023-031. |
| CHK005 | [ ] | PARTIAL | Average progress/no-active-100 exists, but five-domain/indicator aggregation and target meaning unresolved. AUD-023-021, AUD-023-022. |
| CHK006 | [ ] | IMPLEMENTED | Response fields and health algorithm establish 0-100 with traffic-light status; no execution implied. |
| CHK007 | [ ] | PARTIAL | FR-005 requires per-component fallback; RT-006 provides tiers but no implemented independent stored checks. AUD-023-003. |
| CHK008 | [ ] | CONFLICT | `data_source_type`, `dataSourceType`, `data_source_indicator`, and no-fields advice disagree. AUD-023-006, AUD-023-031. |
| CHK009 | [ ] | PARTIAL | Mixed fallback is required in principle; per-component response representation unspecified/absent. AUD-023-006. |
| CHK010 | [ ] | PARTIAL | Algorithm rounds to two decimals and service inputs often to one; spec precision policy absent. AUD-023-031. |
| CHK011 | [ ] | IMPLEMENTED | FR-006/RT-003 explicitly join assignments to framework phases. |
| CHK012 | [ ] | IMPLEMENTED | Six AIIMS names are consistent in FR-007, story, and data-service constant. |
| CHK013 | [ ] | PARTIAL | Required denominator/coverage meaning is ambiguous; current denominator is jurisdiction count. AUD-023-016, AUD-023-031. |
| CHK014 | [ ] | PARTIAL | Data-model lists seven dashboard states; stored lower-case lifecycle needs explicit mapping. AUD-023-015. |
| CHK015 | [ ] | CONFLICT | FR-008/data-model mention expected plans; T030/contract specify zero counts without stored plans. AUD-023-015, AUD-023-031. |
| CHK016 | [ ] | PARTIAL | RT-009 gives a heuristic but not complete jurisdiction/primary-capability matching semantics. AUD-023-016. |
| CHK017 | [ ] | PARTIAL | FR-010 specifies count/distribution/coverage, not availability/welfare inference; response drops required data. AUD-023-018. |
| CHK018 | [ ] | IMPLEMENTED | FR-010, assumption, and current workforce filter agree on volunteer/mixed. |
| CHK019 | [ ] | IMPLEMENTED | EC-04 explicitly states exclusion from AIIMS coverage and inclusion in general metrics; current loop supports it. |
| CHK020 | [ ] | PARTIAL | Capability/volunteer jurisdiction obligations explicit; all other per-jurisdiction submetric semantics are not specified. Do not import all of spec 022. AUD-023-016, AUD-023-031. |
| CHK021 | [ ] | IMPLEMENTED | Five domain names consistently specified; built/natural are contract keys for environment display names. |
| CHK022 | [ ] | PARTIAL | Progress is indicator-oriented, but complete denominator/qualitative handling unclear. AUD-023-022. |
| CHK023 | [ ] | CONFLICT | FR-012 presumes targets that the actual catalogue does not contain. AUD-023-022, AUD-023-031. |
| CHK024 | [ ] | PARTIAL | FR-013 says merge, without full key/precedence/conflict semantics; tracker model offers a catalogue ID. AUD-023-021, AUD-023-022. |
| CHK025 | [ ] | IMPLEMENTED | US3.4 explicitly requires visible catalogue with zero/baseline progress without active trackers. |
| CHK026 | [ ] | IMPLEMENTED | EC-03 explicitly requires surviving domains and missing-domain unavailability; implementation is missing. AUD-023-023. |
| CHK027 | [ ] | PARTIAL | Social 24/57/53 matches current files; broader dataset-growth assumption suggests baselines, but count-change policy needs clarity. AUD-023-031. |
| CHK028 | [ ] | CONFLICT | Story says critical/medium; hazard model critical/moderate; public response extreme/medium. Explicit adapter mapping required. AUD-023-013, AUD-023-031. |
| CHK029 | [ ] | PARTIAL | Severity then confidence specified; limit, tie-break, current/expired/recency policy unresolved. AUD-023-013. |
| CHK030 | [ ] | PARTIAL | FR-016 names trust/alignment, not a ten-principle evidence formula. AUD-023-014. |
| CHK031 | [ ] | MISSING | No specific trust-tier-to-warning-principle mapping established in local artifacts; repeated ratio is insufficient. AUD-023-014, AUD-023-031. |
| CHK032 | [ ] | IMPLEMENTED | Actual hazard model/data model constrain confidence to 0-1. |
| CHK033 | [ ] | IMPLEMENTED | FR-017/RT-010 and clarification distinguish valid risk zeros/audit emptiness from fabricated event fallbacks. |
| CHK034 | [ ] | PARTIAL | Actual grouping should handle one severity, but dedicated acceptance coverage is absent. AUD-023-013, AUD-023-029. |
| CHK035 | [ ] | PARTIAL | FR-019 identifies four required categories; available GovernanceAction values and framework/plan bridges do not fully align. AUD-023-011. |
| CHK036 | [ ] | CONFLICT | Data-model describes audit details as string; domain uses dict; aggregator fields disagree with public summary model. AUD-023-008, AUD-023-031. |
| CHK037 | [ ] | PARTIAL | Link traversal requested; entity reference versus event-parent graph is undefined and unimplemented. AUD-023-010. |
| CHK038 | [ ] | PARTIAL | Filters enumerated, but combined/date-only/related-entity semantics insufficient and current implementation incomplete. AUD-023-009. |
| CHK039 | [ ] | PARTIAL | Immutability appears in Key Entities, not a numbered FR; repository uses upsert. AUD-023-012. |
| CHK040 | [ ] | PARTIAL | Actual-actions-only rule is explicit in CL-05/RT-010, but not a distinct FR and conflicts with import audit. AUD-023-011. |
| CHK041 | [ ] | IMPLEMENTED | Clarification/RT-010/task story explicitly make empty audit the correct no-action state. |
| CHK042 | [ ] | IMPLEMENTED | FR-027/Key Entities require tenant-scoped audit records; implementation lacks it. AUD-023-001. |
| CHK043 | [ ] | PARTIAL | T079 names a seed-baseline badge; mixed cell/component representation remains unresolved and absent. AUD-023-006. |
| CHK044 | [ ] | PARTIAL | RT-007 describes pending/inference, but per-source baseline gate criteria lack complete specification. AUD-023-004, AUD-023-005. |
| CHK045 | [ ] | IMPLEMENTED | US6.3 and T063 explicitly require mixed stored/baseline handling; current branch does not implement it. |
| CHK046 | [ ] | PARTIAL | FR-001 lists ten names, but six principle entities need an explicit mapping in both gates and matrix. AUD-023-004, AUD-023-005. |
| CHK047 | [ ] | CONFLICT | Gate, assessment, and matrix status vocabularies differ; conversions and baseline semantics need documented mapping. AUD-023-005, AUD-023-031. |
| CHK048 | [ ] | CONFLICT | T006a/b/T079 require field plus presentation; final data-model section says no fields/future indicator. AUD-023-006. |
| CHK049 | [ ] | IMPLEMENTED | Contract enumerates all thirteen endpoints individually. |
| CHK050 | [ ] | IMPLEMENTED | Contract explicitly preserves paths, methods, shapes, types, request optionality, and ranges; actual fulfillment incomplete. |
| CHK051 | [ ] | CONFLICT | Multiple provenance names/values and no-fields decision coexist. AUD-023-006, AUD-023-031. |
| CHK052 | [ ] | PARTIAL | FR-027 covers store queries, but shared reference seed versus scoped operational records and legacy migration are not specified. AUD-023-001. |
| CHK053 | [ ] | IMPLEMENTED | Plan/T076 scope p95 <500ms to all thirteen with at least ten sequential requests each. Measurement remains UNVERIFIED. |
| CHK054 | [ ] | PARTIAL | FR-028 applies current-only to health/matrix, not immutable historical audit. Do not erase superseded audit history to satisfy this question. AUD-023-004, AUD-023-005, AUD-023-010. |
| CHK055 | [ ] | PARTIAL | FR-026 requires automatic transition; singleton seed route cannot perform it and timing/cache semantics are not fixed. AUD-023-003, AUD-023-025. |
| CHK056 | [ ] | CONFLICT | Edge case asks graceful unavailability, RT-006 says zero baseline, contract says 503; explicit distinction required. AUD-023-023, AUD-023-031. |
| CHK057 | [ ] | PARTIAL | Growth beyond baseline required without bounds/workload measurements. AUD-023-032. |
| CHK058 | [ ] | PARTIAL | Partial loading is an explicit edge case/T066, not a detailed per-section data contract. AUD-023-023. |
| CHK059 | [ ] | IMPLEMENTED | API contract supplies 503 and `detail` text; actual routes/global handler differ. AUD-023-023. |
| CHK060 | [ ] | IMPLEMENTED | Canonical names agree with the data-service constant and FR-001 clarification. |
| CHK061 | [ ] | PARTIAL | RT-007 mapping helps but several inference/aggregation criteria are heuristics, not established compliance assessments. AUD-023-004. |
| CHK062 | [ ] | IMPLEMENTED | Model and registry use `is_current` plus `superseded_by`; dashboard consumption absent. |
| CHK063 | [ ] | PARTIAL | Clarification says NON-NEGOTIABLE requirements map into sections, but provides no complete requirement-to-gate evidence matrix. AUD-023-031. |
| CHK064 | [ ] | CONFLICT | Pending/no-data guidance conflicts with seed inference that can mark empty gates compliant. AUD-023-004, AUD-023-023. |
| CHK065 | [ ] | PARTIAL | Existing algorithm defines pending exclusion/partial credit; all-source gate aggregation still underspecified. AUD-023-004, AUD-023-031. |
| CHK066 | [ ] | PARTIAL | General graceful degradation is stated; timeout/partial-query failures lack complete scenarios. AUD-023-023, AUD-023-029. |
| CHK067 | [ ] | PARTIAL | Tenant isolation required; no interleaved/concurrent route test established. AUD-023-001, AUD-023-002, AUD-023-029. |
| CHK068 | [ ] | IMPLEMENTED | US2.1 uses approximate example values, not fixed phase thresholds; actual fixture join must determine assertions. |
| CHK069 | [ ] | PARTIAL | CL-04/T013 capture MVP behavior, but the phase-derived exercise breakdown contradicts that intent. AUD-023-019. |
| CHK070 | [ ] | MISSING | No numeric source-age freshness requirement specified. False assessment timestamps are still a defect; do not invent a new SLA. AUD-023-025, AUD-023-031. |
| CHK071 | [ ] | PARTIAL | Unknown references are explicit in EC-05 but absent from the returned detail contract. AUD-023-017. |
| CHK072 | [ ] | IMPLEMENTED | EC-07 explicitly states all-available =100%; source formula supports the case, direct test absent. AUD-023-029. |

### Plan, Research, and Supporting Review Claims

| Claim / decision | Assessment | Evidence and limit |
| --- | --- | --- |
| Plan gate 1: Primacy of Life PASS | PARTIAL | Real input provenance is not established; heuristic compliance must not be used as life-safety assurance. AUD-023-004. |
| Plan gate 2: National EM Principles PASS | PARTIAL | Current evaluator reads missing framework `type`; broader national coordination review not established here. AUD-023-004, AUD-023-015. |
| Plan gate 3: Multi-Hazard Design PASS | PARTIAL | Hazard seed coverage exists, stored hazard assessment integration missing. AUD-023-013. |
| Plan gate 4: Transparency & Auditability PASS | PARTIAL | Serialization, filtering, write coverage, immutability, and chain findings contradict completion. AUD-023-008 through AUD-023-012 address distinct defects. |
| Plan gate 5: Warning & Public Information PASS | PARTIAL | Tier proportion is not demonstrated ten-principle compliance. AUD-023-014. |
| Plan gate 6: Evacuation Framework PASS | UNVERIFIED | Plan says no evacuation changes; no evacuation runtime/review approval was established. No new evacuation audit opened. |
| Plan gate 7: Recovery Support PASS | PARTIAL | Real catalogue structure partly used, but tracker/target/domain obligations incomplete. AUD-023-020, AUD-023-021, AUD-023-022. |
| Plan gate 8: Cloud Platform & Infrastructure PASS | UNVERIFIED | No region/deployment evidence inspected; UI banner and design constraint are not proof. AUD-023-032. |
| Plan gate 9: PPRR Lifecycle PASS | PARTIAL | Internal seed counts computed; distribution/detail and unknown-reference handling incomplete. AUD-023-017. |
| Plan gate 10: Governance & Quality Gates PASS | UNVERIFIED | Test source exists but required executions and review approvals were not established. AUD-023-029, AUD-023-030, AUD-023-032. |
| RT-001: Extend bootstrap | IMPLEMENTED | Five domains and evaluation questions loaded; actual shape is nested `domains`, consistently consumed locally. Malformed-file isolation is separate. |
| RT-002: Separate data computation service | PARTIAL | Class and aggregation boundary exist; stored adapters remain optional/unwired. AUD-023-003. |
| RT-003: All required seed fields confirmed | CONFLICT | Actual frameworks use `framework_type`, not evaluator `type`; indicator targets and exercise metadata are absent. AUD-023-015, AUD-023-019, AUD-023-022. |
| RT-004: Additive-only compatibility | PARTIAL | Paths/model fields largely retained, but no provenance field and nonempty audit constructor mismatch. AUD-023-006, AUD-023-008. |
| RT-005: <5ms computation / no performance risk | UNVERIFIED | Numbers are estimates without retained populated thirteen-endpoint timing evidence. AUD-023-032. |
| RT-006: Stored -> seed -> zero/unavailable | PARTIAL | Seed baseline exists; stored-first/independent failures not implemented and zero-versus-error guidance conflicts. AUD-023-003, AUD-023-023. |
| RT-007: Six mapped/four inferred gates | PARTIAL | Canonical names retained, actual mapping not queried and inference can overclaim compliance. AUD-023-004. |
| RT-008: FastAPI seed dependency injection | MISSING | Actual implementation is a module singleton rather than the documented dependency arrangement. AUD-023-003. |
| RT-009: Jurisdictional capability heuristic | PARTIAL | Global hazard union exists, jurisdiction/primary-capability comparison missing. AUD-023-016. |
| RT-010: Empty audit initially / existing write paths | CONFLICT | Dashboard emptiness is disconnected reads; automatic seed import creates registrations and required plan/framework coverage is absent. AUD-023-011. |
| RT-011: Optional TypeScript metadata | MISSING | Typed client has no provenance field; data-model advises the contrary. AUD-023-006, AUD-023-031. |
| Data-model validation rules | PARTIAL | Four phases, ten gates, score weights and literals are modeled. Current-assessment filtering is not consumed, and several stated entity schemas differ from actual source. AUD-023-004, AUD-023-005, AUD-023-031. |
| Data-model “no response changes needed” decision | CONFLICT | Directly conflicts with FR-005/024 and T006a/b/T079. Zero values/logs cannot distinguish real zero from seed fallback. AUD-023-006. |
| Task prerequisites/checkpoints | UNVERIFIED | Input artifacts exist; checkpoint statements that tests pass or outputs are trustworthy are not execution records. AUD-023-032. |
| Task C2 “FR-019 already implemented” resolution | PARTIAL | `_audit`, not `_record_audit`, is the real helper. Assessment/source writes are real; four-action completeness and no-seed-event rule are not met. AUD-023-011. |
| Quickstart validation/deployment | UNVERIFIED | Commands are future instructions; they were not run and no attributable successful results were established. AUD-023-032. |
| Operational documentation | CONFLICT | Old endpoint/lifecycle/AWS descriptions and 2-second target differ from this contract. Executive-KPI consolidation explicitly retains the operational dashboard, so it does not supersede 023. AUD-023-031. |
| HYP rubric/decision narratives | UNVERIFIED | Portfolio mean claims and “LANDED” text lack spec-023 consultation/measurement evidence; HYP stub unresolved. AUD-023-033. |

## Future Validation Commands

**None of these commands was executed in this audit.** Run only in a later authorized session. Configure the
repository-supported Python 3.12+ environment, API dependencies, dev/test extras, and workspace paths first.
Root [test configuration](../../tests/conftest.py#L1) adds import paths but does not guarantee cloud isolation:
the [registry constructor](../../apps/api/app/repositories/governance_repository.py#L36) uses `COSMOS_ENDPOINT`
when present, and [application startup](../../apps/api/app/main.py#L12) may configure external telemetry.
Unset external-service credentials/endpoints or inject fully local fakes before importing the application.
Use independent local tenant stores and a fake artifact sink; never run these against production records.

| Gate | Future command | Prerequisites and expected results |
| --- | --- | --- |
| FV-01 | `pytest tests/unit/test_governance_data_service.py tests/unit/test_dashboard_aggregation.py -v` | The first path is **proposed/missing today**. Create substantive tests first. Use copied seed fixtures and controlled stored adapters. Expect exact counts, current-only gates, real mutation sensitivity, valid baseline/failure distinctions; no empty selection. |
| FV-02 | `pytest tests/unit/test_health_score_service.py tests/contract/test_governance_dashboard_contract.py tests/contract/test_governance_dashboard.py -v` | Extend existing canned contracts with populated dashboard objects; preserve useful registry tests. Expect unchanged weights/field names plus compatible additive provenance and correct nonempty audit serialization. |
| FV-03 | `pytest tests/integration/test_governance_dashboard_api.py -v` | Repair isolation/setup and strengthen tests before running. Expect all thirteen endpoints, actual action/write/read transitions, scoped filters/paging, known/missing details, and controlled 404/422/503 results. |
| FV-04 | `pytest tests/unit/test_governance_data_service.py tests/integration/test_governance_dashboard_api.py -k "tenant or isolation or auth or export" -v` | Add named tests for these cases first; verify a nonzero collected count. Use two tenants, verified-principal fixtures, repeated IDs, query spies, foreign links/jobs. Expect no cross-tenant data or unauthenticated success. |
| FV-05 | `pnpm --filter @ama/web test -- src/components/governance/dashboard` | **Proposed colocated tests** must first be added under this existing component area with page/client coverage where appropriate. Workspace dependencies must be installed. Expect explicit seed labels, baseline visibility, filter/sort preservation, and request-error states. |
| FV-06 | `pnpm --filter @ama/web exec playwright test governance-dashboard.spec.ts --project=chromium` | **Explicit browser/server authorization required later.** [Playwright config](../../apps/web/playwright.config.cts#L18) starts API/web servers and writes artifacts; use isolated local fixtures and correct BASE_URL. Strengthen tests first. Expect all six flows and nonempty mutation-backed records, not conditional visibility checks. Repeat with `--project=mobile` after desktop passes. |
| FV-07 | `pytest tests/integration/test_governance_dashboard_api.py -k dashboard_p95 -v` | **Proposed benchmark test** must be added to this existing suite first. With pytest-benchmark/dev dependencies and realistic populated stores, run at least ten sequential requests per each of thirteen endpoints, state percentile calculation/cold-warm policy, and assert every p95 <500ms. No selected benchmark means failure to validate. |
| FV-08 | `pytest tests/unit/test_governance_data_service.py tests/unit/test_dashboard_aggregation.py tests/contract/test_governance_dashboard.py tests/contract/test_governance_dashboard_contract.py -v` | Original T075 gate after missing suite/fixtures are implemented. Record revision, environment, selected count, exit status, and output. Then execute remaining quickstart tests only under renewed authorization. Deployment is a separate approval/workflow, never inferred from local pass. |
| FV-09 | `git diff --check -- specs/023-dashboard-real-data` | Later approved documentation/evidence changes only; expect no whitespace errors. Also text-validate original-task coverage, requirement IDs, actual link targets/line bounds, HYP contract structure, and named review evidence. This command alone proves neither traceability nor a human sign-off. |

For T077, use an independently approved deployment plan and validated deployment tooling rather than blindly
executing historical quickstart strings. Record the actual service/revision/environment and verification
results when authorized. This report supplies no deployment approval and asserts no deployed state.

## Completion Order and Audit Validation

1. Resolve the bounded data-contract decisions in AUD-023-031; establish tenant and request identity safeguards
   in AUD-023-001 and AUD-023-002 before enabling the stored path in AUD-023-003.
2. Repair domain computations and provenance with the specifically named owners; keep score weights,
   canonical endpoint fields, and 018/008 authority boundaries intact.
3. Author AUD-023-029 tests alongside each repair and strengthen the actual route/consumer suites in
   AUD-023-030. Do not substitute another subsystem's tests or a source-code grep for a runtime acceptance result.
4. Execute only separately authorized future validation, retain measurements and review evidence, and leave
   AUD-023-032/AUD-023-033 open wherever execution or sign-off remains unestablished.

Audit-only validation checks this report's 81 original rows/states, requirement/scenario/edge/clarification/
assumption/amendment coverage, 72 review items, 16 quality claims, stable unique unchecked AUD task IDs,
existing local links and referenced line bounds, and report diagnostics via `get_errors`. It does not import
or execute product code. Final validation results are reported with the audit handoff; no unchecked follow-up
or UNVERIFIED execution is converted into completion by a text-only check.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 023 only. Three parallel technical reviews examined dashboard
auth/data boundaries, aggregation truthfulness, and audit/export persistence. The source-completable integrity defect
was corrected: unknown risk detail IDs no longer produce synthetic `Risk ... / unknown` records; the existing route
now receives `None` and returns its declared `404` response. Tenant-scoped storage, real risk/recovery inputs, export
durability, and provenance remain open.

Validation was attempted with `python -m pytest
tests/integration/test_governance_dashboard_api.py::TestRiskWarningEndpoints::test_unknown_risk_detail_returns_not_found -q`,
but the earlier `IngestionProcessingResult` import blocker has since been repaired. A rerun is still required to
validate the endpoint behavior after the source change.

### 2026-09-19 Continuation Pass

The ingestion composition blocker was repaired by restoring the shared result contract and synchronous authoritative
service wiring. The focused unknown-risk test then passed: `1 passed`; broader dashboard data, tenant scope, export,
and provenance gaps remain open.
