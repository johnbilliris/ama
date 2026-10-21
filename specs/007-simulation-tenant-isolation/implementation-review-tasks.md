# Static Implementation Audit: Simulation Tenant Isolation

**Review date:** 2026-09-11  
**Source baseline:** `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`  
**Disposition:** Significant implementation gaps; not evidence of safe concurrent live/simulation operation.  
**Coverage:** 46 original tasks; 31 FRs, 6 NFRs, 7 SCs; 21 acceptance scenarios; 7 edge cases; 11 later assumption/persona/hypothesis/scope statements.  
**Remediation:** 31 open tasks, AUD-001 through AUD-031. All are future work.

## Scope and Evidence Rules

This is a standalone, source-only audit under the central [Review Contract](../001-spec-implementation-audit/README.md#L14).
The complete local inputs were read: [spec.md](spec.md), [tasks.md](tasks.md), [plan.md](plan.md),
[research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md),
[contracts/simulation-api.md](contracts/simulation-api.md),
[contracts/tenant-middleware.md](contracts/tenant-middleware.md), and
[checklists/requirements.md](checklists/requirements.md).
The local directory contains no separate amendment log or implementation-review/sign-off record.
The later ASM/PER/HYP/SCP sections embedded in the specification are included below.

Applicable guidance included the repository [code-review instructions](../../.github/instructions/code-review.instructions.md#L15),
[Bicep review baseline](../../.github/instructions/bicep-code-best-practices.instructions.md#L1),
[Bicep policy instructions](../../.github/instructions/bicep-policy-compliance.instructions.md#L1),
the [constitution](../../.specify/memory/constitution.md#L1), and the installed Python fact-grounded coding skill.
Policy discovery, infrastructure generation, rubric grading, and external actor consultation were not performed.

`git rev-parse HEAD` matched the supplied baseline. The initial tracked worktree status was clean.
Only this report was authored. No original task, specification, source, evidence, or index was changed.
No other implementation-audit report was used. No delegation, test execution, build, deployment,
browser session, network probe, cloud operation, or repair was performed.
Read-only source inspection and JSON/document parsing are not application tests.

**Interpretation:** IMPLEMENTED means the scoped source/artifact obligation is present, not that a test or deployment passed.
PARTIAL means a concrete obligation remains unsatisfied. MISSING follows a scoped search for alternatives.
CONFLICT identifies competing contracts or contradicted behavior. UNVERIFIED applies to execution, measurement,
security outcomes, approval, and deployed state. SUPERSEDED requires explicit replacement evidence.
Static defects below describe reachable code paths and their conditional consequences; they do not assert a
demonstrated production exploit or measured performance regression.

### Reachability and Rename Checks

| Surface | Controlling evidence and conclusion |
| --- | --- |
| Authentication and tenant resolution | [Application wiring](../../apps/api/app/main.py#L55) registers legacy claims and tenant middleware. [Claims defaults](../../apps/api/app/middleware/auth_middleware.py#L11) grant anonymous `SimulationUser`; [bearer-protected prefixes](../../apps/api/app/middleware/entra_auth.py#L37) exclude simulations and incident declaration. [Tenant resolution](../../apps/api/app/middleware/tenant_middleware.py#L47) is not an authorization boundary. |
| Original simulation routes | [Module construction](../../apps/api/app/api/routes/simulations.py#L28) wires Cosmos-capable tenant/signal repositories but supplies no Redis, template Cosmos, or Blob client to the relevant services. The endpoints remain [registered before the newer router](../../apps/api/app/api/router.py#L68). |
| Live operational data | [Signal routes](../../apps/api/app/api/routes/signals.py#L1), [approval service](../../apps/api/app/services/recommendation_service.py#L11), [incident dashboard](../../apps/api/app/services/dashboard_service.py#L36), and [task repository](../../apps/api/app/repositories/coordination_tasks_repository.py#L93) do not use the resolved simulation boundary. The current [incident detail UI](../../apps/web/src/app/incidents/[incidentId]/page.tsx#L48) still calls the dashboard client. |
| Alternate signal repository | The existing [domain repository](../../packages/domain/src/domain/repositories/signal_repository.py#L13) is distinct from the [API repository](../../apps/api/app/repositories/signal_repository.py#L18). It adds a scope predicate to some queries but has unscoped memory queries and ID-only storage. It is not a complete replacement for the API/global-store paths. |
| Agent rename/migration | `create_handoff_event` was not found; [build_handoff](../../apps/agents/common/handoffs.py#L48) is the existing equivalent. That module explicitly identifies [MAF as its replacement](../../apps/agents/common/handoffs.py#L1). [Monitoring's pipeline](../../apps/agents/monitoring/pipeline.py#L289) passes an explicit tenant to its handoff, but [MAF run creation](../../apps/agents/maf_runtime/workflow/builder.py#L89) omits the repository tenant argument. Seeding does not invoke either full chain. |
| Later simulation features | [Clock/scheduler](../../apps/api/app/services/warp_scheduler.py#L131), [playback authorization](../../apps/api/app/services/playback_service.py#L43), [typed audit writer](../../apps/api/app/services/simulation/audit_writer.py#L240), and [new REST routes](../../apps/api/app/api/routes/simulations_036.py#L1) exist. They use additional storage/state/ID contracts; their existence does not retire the original endpoints or implement the original archive/report workflow. |
| Scenario packs and storage helpers | [Four curated packs](../../packages/domain/src/domain/seed/scenario_templates_australia.json#L1) and [older phase templates](../../apps/ingestion/simulation/scenario_templates.py#L1) exist. The historical `core/storage.py` reference is absent; real Blob construction exists in [RawPayloadBlobStore](../../apps/ingestion/blob_store.py#L13), but it is not injected into the simulation audit/report services. |
| Negative-search scope | Searches covered local specification files, Python sources under apps/packages/scripts, relevant web components/pages/clients, infrastructure declarations, and corresponding test sources. Calls to `check_expired_tenants`, `check_write_allowed`, `evaluate_utilisation`, and `run_delivery_loop` were sought; application source contains definitions but no application scheduling/write-path callers. A timeout in one broad search was resolved with narrower searches; absence conclusions do not rely on the timed-out search. |

## Findings by Severity

### Critical

| ID | Finding | Primary evidence | Impact |
| --- | --- | --- | --- |
| AUD-001 | Simulation authentication is fail-open in the registered stack. | [Anonymous role default](../../apps/api/app/middleware/auth_middleware.py#L11), [unvalidated header decoding](../../apps/api/app/middleware/auth_middleware.py#L28), [production prefix list](../../apps/api/app/middleware/entra_auth.py#L37). | Missing credentials can become a simulation-capable principal; the shared anonymous identity also defeats meaningful participant identity. |
| AUD-002 | Middleware tenant resolution neither validates membership nor consistently reaches ordinary data routes. | [Resolver](../../apps/api/app/middleware/tenant_middleware.py#L47), [registration without repository](../../apps/api/app/main.py#L55). | Simulation URL context is accepted without enforcement here; ordinary requests default live rather than receiving a verified simulation context. |
| AUD-003 | Operational read/write paths bypass tenant ownership. | [Signal list](../../apps/api/app/api/routes/signals.py#L28), [global approvals](../../apps/api/app/services/recommendation_service.py#L19), [dashboard](../../apps/api/app/services/dashboard_service.py#L36), [organisation-only tasks](../../apps/api/app/repositories/coordination_tasks_repository.py#L93). | Once an ID is known, the inspected paths do not separate live and simulation reads or mutations. |
| AUD-004 | Storage helpers do not provide the promised storage-enforced isolation. | [Unbound point read](../../apps/api/app/repositories/signal_repository.py#L61), [cross-partition listing](../../apps/api/app/repositories/signal_repository.py#L75), [alternate repository](../../packages/domain/src/domain/repositories/signal_repository.py#L30), [account-scoped API role](../../infra/main.bicep#L893). | A caller-supplied partition can select another tenant; shared account permissions and optional application filters are not a security boundary against filter omissions. |
| AUD-005 | Alert publication lacks resource ownership and durable simulated-publication recording. | [Publish and deliver](../../apps/api/app/services/public_alert_service.py#L66), [missing-context outbound allowance](../../apps/api/app/clients/outbound_http.py#L64). | The gate trusts ambient request context, while alerts are global and publication is already recorded as ordinary `published`; no original simulation audit event is written. Real channel adapters here are stubs, so actual external delivery remains UNVERIFIED. |

### High

| ID | Finding | Primary evidence | Impact |
| --- | --- | --- | --- |
| AUD-006 | Participant and administrator controls are incomplete across entry points. | [Unfiltered list](../../apps/api/app/api/routes/simulations.py#L119), [delete](../../apps/api/app/api/routes/simulations.py#L385), [chat](../../apps/api/app/api/routes/simulation_chat.py#L59), [new-role check](../../apps/api/app/api/dependencies/simulation_rbac.py#L222). | Simulation metadata/history or lifecycle changes are not uniformly restricted to the relevant participants and administrators. |
| AUD-007 | Cache/blob namespaces and live ingestion binding are incomplete. | [Dedup keys](../../apps/api/app/services/ingestion/dedup_service.py#L23), [raw blob names](../../apps/ingestion/blob_store.py#L28), [worker factory](../../apps/ingestion/worker.py#L208), [agent dedup](../../apps/agents/monitoring/dedup.py#L35). | Matching IDs can share dedup state; real ingestion does not establish the specified durable live partition; namespace cleanup cannot account for unprefixed data. |
| AUD-008 | Provisioning advertises Active without required durable dependencies and masks failures. | [Service construction](../../apps/api/app/api/routes/simulations.py#L28), [provisioning](../../apps/api/app/services/simulation_service.py#L40), [repository fallback](../../apps/api/app/repositories/simulation_repository.py#L35). | A successful create can have no cache/audit backing; configured-storage initialization failure silently changes persistence mode. |
| AUD-009 | Tenant, scenario partition, and scenario-run identities are unrelated. | [Three UUIDs](../../apps/api/app/services/simulation_service.py#L62), [nullable ScenarioRun tenant](../../packages/domain/src/domain/models/scenario_run.py#L7), [rehearsal creation](../../apps/api/app/services/rehearsal_orchestrator.py#L19). | The specified one-to-one identity cannot be derived or reliably point-read; lifecycle/report/state integrations refer to different IDs. |
| AUD-010 | Curated seeding is disconnected; controller seeding can report success using fake counters. | [Unconfigured template loader](../../apps/api/app/services/scenario_seeding_service.py#L147), [seed loop](../../apps/api/app/services/scenario_seeding_service.py#L30), [counter-only helper](../../apps/api/app/services/simulation/controller_service.py#L1081). | Packs are present but not loaded by the registered service; organisations/frameworks are not materialized, and UI counts can increase without stored signals. |
| AUD-011 | Seeded envelopes do not meet live schema/provenance or Cosmos document requirements. | [Arbitrary envelope model](../../packages/domain/src/domain/models/scenario_template.py#L12), [live envelope](../../apps/api/app/validators/signal_envelope.py#L26), [unadapted write](../../apps/api/app/repositories/signal_repository.py#L51). | Missing IDs/timestamps and snake-case partition fields prevent claimed processing/storage parity. |
| AUD-012 | Historical replay ignores its time window and retains live references. | [Replay implementation](../../apps/api/app/services/scenario_seeding_service.py#L77). | A replay is a capped, shallow signal copy, not a bounded independent incident snapshot with remapped graph IDs. |
| AUD-013 | Scheduled replay and pause enforcement are not connected across all paths. | [Immediate seed writes](../../apps/api/app/services/scenario_seeding_service.py#L30), [unused scheduler loop](../../apps/api/app/services/warp_scheduler.py#L188), [chat stream](../../apps/api/app/services/simulation/controller_service.py#L324), [overlapping routers](../../apps/api/app/api/router.py#L68). | Signals can appear before their due time; chat processing is not stopped by original pause state; raw-UUID and tenant-slug lifecycle routes conflict. |
| AUD-014 | Shared live/simulation agent processing and downstream ownership are unproven and incomplete. | [Seed path](../../apps/api/app/services/scenario_seeding_service.py#L30), [MAF run](../../apps/agents/maf_runtime/workflow/builder.py#L89), [dispatcher](../../apps/agents/dispatcher/agent.py#L209). | Repository writes and separate prompt-based sub-agent replies do not establish the same executable chain and artifact storage as live operations. |
| AUD-015 | Persona assignments, jurisdiction filtering, and full approval outcomes are incomplete. | [Participants route](../../apps/api/app/api/routes/simulations.py#L239), [workspace](../../apps/api/app/services/persona_workspace_service.py#L28), [approval outcome mapping](../../apps/api/app/services/recommendation_service.py#L19). | Persona assignments are discarded; workspace identity is caller-selected; escalation becomes rejection and simulation approval audit is absent. |
| AUD-016 | Simulation management/dashboard does not expose the required complete exercise workflow. | [Create page](../../apps/web/src/app/simulations/create/page.tsx#L23), [dashboard](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L94), [list](../../apps/web/src/app/simulations/page.tsx#L7). | No assigned-persona approval workspace, participant invitation UI, template/replay selection, or complete resource/throttle management is present. |
| AUD-018 | Simulation identification is not persistent on every simulation view/state. | [Banner CSS](../../apps/web/src/app/globals.css#L3949), [early returns](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L209), [playback page](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L1). | Identification is absent during loading/errors and playback, and no fixed/sticky positioning or guaranteed overlay precedence is established. |
| AUD-019 | Original runtime safety audit is incomplete and not immutable. | [Audit writer](../../apps/api/app/services/simulation_audit_writer.py#L23), [unwired Blob client](../../apps/api/app/api/routes/simulations.py#L30), [container declarations](../../infra/main.bicep#L526). | Successful actions can lack durable provenance; Blob errors are swallowed and the original containers have no declared WORM policy. |
| AUD-020 | Exercise reports are placeholder aggregates without reliable persistence. | [Report generation](../../apps/api/app/services/exercise_report_service.py#L32), [persistence](../../apps/api/app/services/exercise_report_service.py#L97), [report schema](../../packages/domain/src/domain/models/exercise_report.py#L39). | Empty sections, zero/default metrics, no benchmark/history comparison, and a URI without a stored report cannot support after-action review. |
| AUD-022 | Archive/delete workflow is largely status-only. | [Archive](../../apps/api/app/services/simulation_service.py#L191), [delete](../../apps/api/app/api/routes/simulations.py#L385). | Reports, audit and seed snapshots are not archived; operational Cosmos/state data is not reclaimed; retention and completion are not verified. |
| AUD-023 | Idle TTL warning and scheduled archival are absent. | [Expiry calculation](../../packages/domain/src/domain/models/simulation_tenant.py#L102), [uncalled expiry check](../../apps/api/app/services/simulation_service.py#L226). | No 24-hour notice, idle activity tracking, or registered periodic check prevents stale exercises from accumulating or expiring incorrectly. |
| AUD-024 | Concurrency and per-exercise budgets are not enforced atomically at write boundaries. | [Count then create](../../apps/api/app/validators/simulation_validators.py#L11), [signal writes](../../apps/api/app/repositories/signal_repository.py#L51), [configured limits](../../packages/domain/src/domain/models/simulation_tenant.py#L24). | Multiple replicas can exceed the creation cap; signal/recommendation/duration limits and truthful resource counters do not constrain processing. |
| AUD-025 | Resource governor is not an operational live-priority mechanism. | [Write check](../../apps/api/app/services/resource_governor.py#L45), [utilisation](../../apps/api/app/services/resource_governor.py#L109), [incident service construction](../../apps/api/app/api/routes/incidents.py#L8). | Uncalled checks, no RU/LLM usage input, local token state, and no participant notification fail to protect live capacity. |
| AUD-026 | Incident declare/resolve is unauthorised and not durably recorded. | [Endpoints](../../apps/api/app/api/routes/incidents.py#L20), [local incident flag](../../apps/api/app/services/resource_governor.py#L43). | Any accepted request can change the mode; replicas/restarts/new simulations do not share a reliable authoritative incident state. |
| AUD-029 | Existing tests/checklists do not substantiate completion or release safety. | [Model-only API tests](../../tests/contract/test_simulation_api_contract.py#L15), [state-only lifecycle](../../tests/integration/test_simulation_lifecycle.py#L20), [CI test selection](../../.github/workflows/ci.yml#L131). | Many checked obligations and all measured outcomes remain unverified; tests can pass without exercising the required behavior. |
| AUD-031 | Synchronous storage operations block async simulation handlers. | [Synchronous Cosmos inside async methods](../../apps/api/app/repositories/simulation_repository.py#L53), [bulk signal path](../../apps/api/app/services/scenario_seeding_service.py#L30), [Blob report I/O](../../apps/api/app/services/exercise_report_service.py#L81). | Shared API event-loop work can be blocked by simulation storage latency; the magnitude and the 10% live-impact budget are UNVERIFIED. |

### Medium and Low

| ID | Severity | Finding and evidence | Impact |
| --- | --- | --- | --- |
| AUD-017 | Medium | [Shared navigation](../../packages/ui/src/components/layout/app-shell.tsx#L6) and [footer](../../packages/ui/src/components/layout/app-shell.tsx#L60) expose Simulations on live pages. | Direct contradiction of FR-022's prohibition on simulation UI in the live view; zero operator confusion is unmeasured. |
| AUD-021 | Medium | [Report page](../../apps/web/src/app/simulations/reports/[reportId]/page.tsx#L29) calls a tenant endpoint using `reportId` and omits the timeline. | A real report deep link cannot resolve by the documented identity and cannot display all required sections. |
| AUD-027 | Medium | [Middleware](../../apps/api/app/middleware/tenant_middleware.py#L20) only sets context/header; [monitoring](../../infra/modules/monitoring.bicep#L138) consumes but does not emit the dimension. | Logs, metrics, and distributed requests cannot all be reliably filtered by `tenant_id`. |
| AUD-028 | Medium | [API contract](contracts/simulation-api.md#L1), [middleware contract](contracts/tenant-middleware.md#L15), and [implemented bodies/statuses](../../apps/api/app/api/routes/simulations.py#L191) disagree. | Documented clients/quickstart fail or select an unintended context; completion criteria are ambiguous. |
| AUD-030 | Low | [T003](tasks.md#L20) names a middleware initializer, but the inspected middleware directory contains none; the three test package initializers exist. | A specific setup deliverable is incomplete. Namespace-package imports may still work; no import failure is asserted. |

## Open Remediation Tasks

Each acceptance statement below is a future completion gate. Existing test files are reusable locations,
not evidence that proposed new cases already exist. `F1` through `F10` identify future commands and
prerequisites in the final section. Dependencies order the work; none authorises changes during this audit.

### Authentication, Boundaries, and Safety

- [x] AUD-001 - Establish authoritative authentication before simulation claims.

  **Remediation (2026-09-16):** Simulation, incident, and signal routes now resolve a validated bearer principal in production; simulation and incident routes fail closed without credentials, forwarded headers require the explicit trusted-test gate, anonymous simulation access requires an explicit non-production switch, and Entra `oid` takes precedence over `sub`. Focused validation: 18 passed; two unrelated stale governance-seed fixtures were deselected.

  **Original obligations:** T005, T010, T011, T016; FR-002, FR-006, FR-023, FR-031; US1-AS1, US3-AS1.
  **Expected/observed/impact:** Entra-authenticated identities are required. The registered
  [legacy middleware](../../apps/api/app/middleware/auth_middleware.py#L11) supplies an anonymous simulation role,
  directly decodes a caller header, and overwrites claims; [principal extraction](../../apps/api/app/core/auth.py#L17)
  uses `sub`, not the specified participant OID. The newer bearer middleware does not protect these routes.
  This is a static authentication bypass, not a claim of production exploitation.
  **Developer work:** Make one validated principal authoritative for all simulation and incident-mode routes;
  reject missing/invalid/expired/wrong-audience credentials before state access. Normalize real EasyAuth claim
  arrays only behind an enforced trusted ingress, or validate JWTs in application code. Use the authenticated OID
  for membership, preserve verified claims, and isolate any dev identity behind an explicit fail-closed dev-only switch.
  **Tester work:** Extend [API contract tests](../../tests/contract/test_simulation_api_contract.py#L15) using the
  [HTTP fixture pattern](../../tests/contract/test_playback_api.py#L25), but test credential validation separately
  from its synthetic header helper. Cover legitimate OID/sub divergence, missing/bad signature, expired token,
  wrong audience, forged EasyAuth header, role-less user, and production configuration with no auth settings.
  Assert 401/403 and zero repository/audit business writes on denial. Run F1 and F3 after repair.
  **Dependencies:** None; coordinate the identity contract with AUD-028.
  **Acceptance:** No anonymous/default role grants production access; valid identity survives the full stack;
  failures have the contracted status and cause no tenant creation or mutation.

- [x] AUD-002 - Resolve one verified request tenant and propagate it without fallback.

  **Remediation (2026-09-16):** Middleware, simulation routes, and incident-mode routes now share one `SimulationRepository`. Explicit simulation paths distinguish missing/deleted tenants (404), nonmembers (403), repository failure (503), and ambiguous active memberships (409), with no failed lookup redirected to live. Focused validation: 17 passed.

  **Original obligations:** T004, T008, T010, T012; FR-001, FR-002, FR-005; NFR-003, NFR-006.
  **Expected/observed/impact:** [The resolver](../../apps/api/app/middleware/tenant_middleware.py#L47) returns a
  path candidate even after a failed membership check; [startup](../../apps/api/app/main.py#L55) supplies no repository.
  Its optional membership branch picks the first active exercise, not an unambiguous authenticated selection.
  Ordinary data requests therefore do not receive a verified simulation context in current wiring.
  **Developer work:** Resolve the claim-versus-membership conflict explicitly; validate requested simulation IDs
  against server-side membership and permitted lifecycle state. Inject the actual shared repository; distinguish
  management, operational data, and archive/report reads. Bind downstream dependencies to this context, scope its
  lifetime, and return 401/403/404/409/503 as appropriate without redirecting storage failures to live.
  **Tester work:** Extend [tenant-context tests](../../tests/unit/test_tenant_context.py#L4) and
  [tenant-isolation tests](../../tests/integration/test_tenant_isolation.py#L21). Cover no claim, valid member,
  nonmember, two memberships, forged header/query, nonexistent/deleted tenant, repository timeout, concurrent
  live/sim requests, and exception cleanup. Assert the actual route/service/repository receives the same tenant.
  Existing ContextVar round-trip assertions do not test these cases. Use F1, F2, F3.
  **Dependencies:** AUD-001, AUD-028.
  **Acceptance:** Every operational request has a deterministic authorized tenant; no failed lookup becomes live;
  management/archive read exceptions are explicitly documented and tested.

- [x] AUD-003 - Remove tenant-blind operational reads and mutations.

  **Remediation (2026-09-16):** Operational entities already use `OperationalStore`; the remaining coordination-task Cosmos path now writes a scope-qualified storage ID and requires `c.scope` on every point, list, dependency, persona, incident, and all-task read. Same task IDs can coexist in live and simulation scopes without collision. Focused validation: 31 passed.

  **Original obligations:** T013, T021, T027, T028, T042; FR-002, FR-003, FR-017, FR-018, FR-020, FR-022, FR-024.
  **Expected/observed/impact:** [Signals](../../apps/api/app/api/routes/signals.py#L28) enumerate a global map;
  [approvals](../../apps/api/app/services/recommendation_service.py#L19) mutate by recommendation ID;
  [dashboard](../../apps/api/app/services/dashboard_service.py#L36) selects by incident ID;
  [tasks](../../apps/api/app/repositories/coordination_tasks_repository.py#L93) partition by organisation only.
  Header/middleware presence cannot prevent cross-tenant access on these paths.
  **Developer work:** Route signals, incidents, hazards, recommendations, approvals, alerts, tasks and dependencies
  through tenant-bound repositories. Include tenant ownership in persisted entities and in-memory keys. Resolve
  the actor from authentication rather than a freely supplied persona ID. Apply ownership before lookup/update,
  including dependency and fallback queries, and remove global-store bypasses from production paths.
  **Tester work:** Expand [isolation](../../tests/integration/test_tenant_isolation.py#L21) and
  [API contract tests](../../tests/contract/test_simulation_api_contract.py#L15) with one live tenant and two
  simulations using identical incident/signal/recommendation/task IDs and the same organisation. Exercise real
  GET/POST routes, absent filters, cross-ID approvals, task status updates, rejection and dashboard reads.
  Assert zero foreign rows and byte-equivalent untouched foreign records. Use F2, F3.
  **Dependencies:** AUD-001, AUD-002, AUD-004.
  **Acceptance:** No operational query or mutation can cross the bound tenant, even when optional filters are omitted.

- [ ] AUD-004 - Make storage ownership mandatory, including point reads and alternate repositories.

  **Remediation status (2026-09-16):** Application-side scope binding is complete across both signal repositories: operations are bound to constructor tenant or active `TenantContext`, forged caller scope is rejected, and Cosmos point reads distinguish not-found from service failure. Domain storage validation: 12 passed. **GOVERNANCE-BLOCKED:** account-wide Cosmos data-plane RBAC narrowing is a Bicep change and remains open until spec-007 live policy discovery, inherited-policy inventory, and Portal parity are complete.

  **Original obligations:** T008, T009, T013, T042; FR-003; NFR-003; US1-AS2; EC-02, EC-03.
  **Expected/observed/impact:** [API get_signal](../../apps/api/app/repositories/signal_repository.py#L61) ignores
  `tenant_id` on the Cosmos path and returns the supplied partition's document. Listing enables cross-partition
  SQL; [domain storage](../../packages/domain/src/domain/repositories/signal_repository.py#L30) keys memory by
  signal ID and omits scope from some memory queries. [Account-wide rights](../../infra/main.bicep#L893) mean
  partition keys alone cannot prove isolation against arbitrary application/query bugs.
  **Developer work:** Bind repository instances/operations to an authorized tenant; derive hierarchical partition
  arguments internally, verify returned ownership, and reject conflicting document/partition values. Unify the
  two signal repository contracts and scope all fallback keys. Use point reads for membership with a canonical
  partition mapping. Have security ownership resolve how the absolute FR-003 guarantee is enforced beyond a
  shared credential's application filter; do not describe optional WHERE clauses as database authorization.
  **Tester work:** Add strict fake-Cosmos assertions to [isolation](../../tests/integration/test_tenant_isolation.py#L63)
  and [storage tests](../../tests/contract/test_signal_storage.py#L72). Force a tenant-B partition with tenant-A
  context, an SDK return with foreign scope, matching IDs, omitted scope, list pagination, national fanout,
  unassociated queries, and backend errors. Test both repositories rather than only one memory dictionary.
  Use F2/F3; the chosen deployed enforcement needs separately approved F9 validation.
  **Dependencies:** AUD-002, AUD-009.
  **Acceptance:** Conflicting scope cannot read/write another tenant; 404 is distinct from storage unavailability;
  security documentation accurately states and proves the selected storage boundary.

- [x] AUD-005 - Enforce alert safety using persisted ownership and approval, and record simulated publication.

  **Remediation (2026-09-16):** Non-live delivery records one tenant-owned `published_simulation` event per alert version and returns its stable correlation ID as the synthetic receipt. Outbound HTTP now blocks and records missing or invalid tenant context instead of allowing egress. Focused validation: 19 passed.

  **Original obligations:** T017, T028, T042; FR-018, FR-019, FR-025; US1-AS5, US3-AS3.
  **Expected/observed/impact:** [publish](../../apps/api/app/services/public_alert_service.py#L66) changes a global
  alert to `published`; [deliver](../../apps/api/app/services/public_alert_service.py#L82) checks request context
  and returns a simulated receipt without persisting an audit event. Publish validation also accepts
  `pending_approval`. [The outbound wrapper](../../apps/api/app/clients/outbound_http.py#L64) allows absent context.
  The current adapters only construct dictionaries; no actual SMS/broadcast delivery was observed or attempted.
  **Developer work:** Check alert ownership, authenticated actor, and completed same-tenant approval at the final
  publication/delivery boundary. Refuse unknown/mismatched context; route every supported real channel through
  the hard gate. Persist exactly-once `published (simulation)` audit/receipt state without invoking a real adapter.
  Keep simulation blocking unconditional, including future channel additions and retry paths.
  **Tester work:** Extend [safety tests](../../tests/unit/test_simulation_controller_safety.py#L77) and
  [API contract tests](../../tests/contract/test_simulation_api_contract.py#L15) with adapter spies for SMS,
  broadcast, social, email and push. Test a valid live approval, every simulated channel, missing context,
  forged tenant, another tenant's alert ID, pending approval, replay/retry, and audit failure. Assert adapter call
  counts, stored mode, tenant audit ownership and idempotency. Existing wrapper tests manually set context and
  do not exercise PublicAlertService. Use F2/F3/F4; no live notifications in any test.
  **Dependencies:** AUD-001, AUD-002, AUD-003, AUD-019.
  **Acceptance:** Simulation/unknown ownership never reaches a real channel; publication requires valid approval
  and has one durable, tenant-owned receipt.

- [x] AUD-006 - Apply participant/coordinator/admin policy to every simulation entry point.

  **Remediation (2026-09-16):** Simulation listing and total counts are participant-scoped at the repository query, chat/history require server-side membership, participant changes require creator/coordinator authority, and deletion requires membership plus a simulation/system administrator role. Focused validation: 35 passed.

  **Original obligations:** T006, T009, T011, T016, T026, T034; FR-006, FR-023, FR-024; US3-AS1, US5-AS4.
  **Expected/observed/impact:** [List](../../apps/api/app/api/routes/simulations.py#L119) is not participant-filtered;
  [delete](../../apps/api/app/api/routes/simulations.py#L385) has neither admin nor membership enforcement;
  [chat/history](../../apps/api/app/api/routes/simulation_chat.py#L59) only check the base role and prefix.
  The newer [coordinator dependency](../../apps/api/app/api/dependencies/simulation_rbac.py#L222) compares an optional
  header to claims, not the target simulation's participant document. Playback's stronger access check is reusable.
  **Developer work:** Define and enforce the action matrix for members, coordinator, observer and administrator;
  validate OIDs and target ownership at list/detail/chat/history/new injection/lifecycle/report boundaries.
  Filter list totals before pagination. Restrict participant changes and destructive actions to the documented
  authority; make terminal tenants read-only except permitted archive/retention operations.
  **Tester work:** Reuse [RBAC stub tests](../../tests/unit/test_simulation_participant_rbac.py#L45) and
  [playback HTTP helpers](../../tests/contract/test_playback_api.py#L12). Cross every role with own/foreign/missing
  tenants, raw UUID and `sim-` forms, omitted header, duplicate/invalid OIDs, deleted tenants, and pagination.
  Assert no foreign metadata/history, no mutation on 403/404, and no extra privilege from creator-list drift
  unless explicitly approved. Use F1/F3.
  **Dependencies:** AUD-001, AUD-002, AUD-009, AUD-028.
  **Acceptance:** Every reachable endpoint follows the same documented server-side action/membership policy.

### Persistence, Processing, and Workflows

- [x] AUD-007 - Finish live-only ingestion and tenant namespaces for caches/raw data.

  **Remediation (2026-09-16):** Ingestion pipelines reject `sim-*` scope unless an explicit simulation capability is supplied; the simulation runner is the authorized constructor. Monitoring deduplication now keys by tenant scope and signal ID. Focused validation: 56 passed. Real Redis/Blob migration and deployed namespace evidence remain external.

  **Original obligations:** T008, T013, T042; FR-002, FR-003, FR-004, FR-025; EC-02, EC-03.
  **Expected/observed/impact:** [DedupService](../../apps/api/app/services/ingestion/dedup_service.py#L23) uses
  `dedup:{hash}`, [Blob storage](../../apps/ingestion/blob_store.py#L28) omits `live/`, and the
  [worker factory](../../apps/ingestion/worker.py#L208) supplies no signal repository. [Pipeline persistence](../../apps/api/app/services/ingestion/pipeline_base.py#L274)
  is conditional. [Monitoring dedup](../../apps/agents/monitoring/dedup.py#L35) is keyed by signal ID alone.
  An older [simulation runner](../../apps/ingestion/simulation/simulation_runner.py#L81) calls `save` without scope.
  **Developer work:** Inject a live-bound persistence adapter into all external ingestion pipelines; refuse
  simulation routing through that adapter. Pass a separate simulation-bound adapter to synthetic runners.
  Inventory and migrate actual Redis/local-cache callers to tenant-prefixed keys; prefix raw/audit blobs and
  preserve an explicit compatibility/read-migration plan. Cleanup must use tenant SCAN prefixes, never FLUSHDB.
  **Tester work:** Extend [storage](../../tests/contract/test_signal_storage.py#L72) and
  [isolation tests](../../tests/integration/test_tenant_isolation.py#L21) with BOM, IoT and community normalizers,
  same canonical hash/ID in live and two simulations, tampered source scope, Redis outage, and cleanup prefix
  collisions. Spy on the real factory's save/Blob/key arguments. Assert live writes cannot be redirected and
  simulation dedup does not suppress live signals. Use F2/F3; inspect all registered ingestion types, not one sample.
  **Dependencies:** AUD-002, AUD-004, AUD-008, AUD-011.
  **Acceptance:** External input is durably live-only; cache/blob state and cleanup are tenant-separated on every path.

- [x] AUD-008 - Wire durable dependencies and make provisioning/storage failures explicit.

  **Remediation (2026-09-16):** `SimulationRepository` now refuses in-memory fallback in staging/production. Namespace readiness is explicit; a configured Redis failure leaves the tenant in `Provisioning` and returns 503 instead of reporting `Active`. Focused validation: 26 passed. The 30-second provisioning target remains external measurement evidence.

  **Original obligations:** T009, T010, T012b, T015; FR-007; NFR-001, NFR-003; US1-AS1.
  **Expected/observed/impact:** [Construction](../../apps/api/app/api/routes/simulations.py#L28) omits Redis and
  Blob clients; [create_tenant](../../apps/api/app/services/simulation_service.py#L40) nevertheless moves to Active.
  [Redis errors](../../apps/api/app/services/simulation_service.py#L238) and
  [Cosmos initialization errors](../../apps/api/app/repositories/simulation_repository.py#L35) are swallowed or become memory mode.
  **Developer work:** Provide a shared, explicit dependency factory for tenant/signal/template storage, Redis,
  audit and report storage. Restrict memory backends to explicit isolated test/development configuration.
  Define provisioning stages, idempotent retries and compensation; mark Active only after required dependencies
  are usable. Distinguish missing resources from unavailable storage and surface 503 without changing tenant.
  **Tester work:** Extend [service tests](../../tests/unit/test_simulation_service.py#L18) with injected fake
  clients and strict call expectations for partition metadata, cache namespace and audit readiness. Fail each
  stage, retry after failure, restart with a fresh repository instance, and test configured production storage
  initialization failure. Assert no false Active, duplicate tenant, or silent memory success. Use F1/F3/F10;
  provisioning within 30 seconds is a separate F9 measurement.
  **Dependencies:** AUD-009, AUD-019, AUD-031.
  **Acceptance:** Production provisioning cannot succeed without its durable dependencies; failure is resumable,
  tenant-safe and visible, with timing supported by later measurement rather than this audit.

- [x] AUD-009 - Establish canonical tenant/run/partition identity and persist both entities.

  **Remediation (2026-09-16):** Creation now generates one run UUID, derives `tenant_id = sim-{run_id}`, uses the same value for `scenario_id`, and persists the tenant plus required linked `ScenarioRun` in one simulation-partition batch. Rehearsal runs use the same tenant derivation. Focused validation: 43 passed.

  **Original obligations:** T006, T007, T009, T015; FR-001, FR-006; data-model entity relationship.
  **Expected/observed/impact:** The contract requires `tenant_id = sim-{scenario_run_id}` and
  `scenario_id = scenario_run_id`; [creation](../../apps/api/app/services/simulation_service.py#L62) generates three
  unrelated UUIDs and never creates a ScenarioRun. [The model](../../packages/domain/src/domain/models/scenario_run.py#L7)
  permits no tenant, and [rehearsal](../../apps/api/app/services/rehearsal_orchestrator.py#L19) creates an unassociated run.
  **Developer work:** Generate one canonical run identity, persist/link tenant and run documents with correct
  IDs/discriminators/partition fields, and expose an explicit mapping for existing UUID-based APIs. Validate
  creator membership, required fields and resource value bounds at model/storage boundaries. Plan migration
  of existing unrelated identifiers without orphaning reports, chat or playback data.
  **Tester work:** Extend [tenant model contracts](../../tests/contract/test_simulation_api_contract.py#L71)
  and [service tests](../../tests/unit/test_simulation_service.py#L18). Assert equality relationships, durable
  reload of both documents, malformed IDs, creator absent from participants, omitted participants, migration
  mapping uniqueness, and duplicate-create retries. Use F1/F3.
  **Dependencies:** Coordinate with AUD-028; implementation precedes AUD-004/AUD-008 persistence completion.
  **Acceptance:** Every exercise has exactly one linked run; its partition is derivable or explicitly mapped;
  no orphan or inconsistent tenant/run documents are accepted.

- [x] AUD-010 - Connect curated seeding and replace counter-only success paths with real data.

  **Remediation (2026-09-16):** Curated scenario packs are loadable without an out-of-band Cosmos seed, seed organisation/framework/jurisdiction context is persisted, and controller seeding delegates to `ScenarioSeedingService`; the fake counter-only ingestion loop was removed. Focused validation: 24 passed with exact curated-pack persistence assertions.

  **Original obligations:** T022, T023, T025; FR-006, FR-012, FR-015; US2-AS1, US2-AS4.
  **Expected/observed/impact:** Four packs exist, but [the registered service](../../apps/api/app/api/routes/simulations.py#L47)
  never receives a Cosmos template client. [The seed loop](../../apps/api/app/services/scenario_seeding_service.py#L30)
  only writes signal dictionaries, not organisations/frameworks/jurisdictions. [Controller seeding](../../apps/api/app/services/simulation/controller_service.py#L990)
  starts [five counter increments](../../apps/api/app/services/simulation/controller_service.py#L1081), not ingestion.
  **Developer work:** Load the canonical seed container by kind/ID, validate compatible scenario/jurisdictions,
  copy organisations, jurisdiction assignments and frameworks into tenant-owned storage, then hand signals to
  the scheduler/chain. Make all seed entry points use that service; no fabricated resource counters or success
  receipt before durable acceptance. Define whether the optional creation template seeds automatically or is a later action.
  **Tester work:** Extend [seeding tests](../../tests/unit/test_scenario_seeding.py#L10) beyond model construction.
  Load every real curated pack; assert exact IDs/counts, QLD's six organisations and 23 scheduled signals,
  framework links, distinct seeded tenants, nonexistent/incompatible templates, failure halfway through, and
  idempotent re-entry. Compare UI counters with actual stored records, including paused chat seeding. Use F1/F2/F3.
  **Dependencies:** AUD-008, AUD-009, AUD-011, AUD-013, AUD-024.
  **Acceptance:** Each seed receipt describes actual isolated data; supported packs and initial operating picture
  are reachable through the production-configured service, not only a fixture or chat card.

- [x] AUD-011 - Normalize synthetic signals to the live envelope and persisted document schema.

  **Remediation (2026-09-16):** A shared adapter now converts curated/scheduled payloads to validated live `SignalEnvelope` and domain `Signal` shapes, derives timestamps from exercise offsets, normalizes hazard categories and source metadata, stamps simulation provenance, and persists through the canonical HPK wire path. Focused validation: 47 passed.

  **Original obligations:** T013, T022, T023, T041; FR-012, FR-015, FR-016; US2-AS3, US2-AS4.
  **Expected/observed/impact:** [Timeline entries](../../packages/domain/src/domain/models/scenario_template.py#L12)
  accept arbitrary dictionaries. All 85 curated entries omit event timestamps and Cosmos `id`; [seeding](../../apps/api/app/services/scenario_seeding_service.py#L30)
  adds `signal_id` but not `id` or timestamps. [Live validation](../../apps/api/app/validators/signal_envelope.py#L26)
  requires source/timing/confidence fields, while [Cosmos](../../infra/main.bicep#L609) partitions on camel-case fields.
  **Developer work:** Use one validated adapter from template offsets/live snapshot records to the shared live
  signal shape, then serialize storage IDs and all hierarchical partition components consistently. Generate
  exercise-relative occurrence/receipt timestamps; preserve source, location, confidence and freshness;
  set nested provenance `source_context=simulation`, not only an extra top-level key.
  **Tester work:** Reuse [seeding model tests](../../tests/unit/test_scenario_seeding.py#L11) and
  [make_signal](../../tests/contract/test_signal_storage.py#L27). Validate every pack through live envelope and
  persistence adapters; cover missing source/time, out-of-range scores, malformed location, duplicate offset,
  invalid category and caller-supplied live scope. Assert exact `id`, `scope`, jurisdiction/data-source keys,
  UTC timestamps and nested provenance. Use F1/F2/F3.
  **Dependencies:** AUD-004, AUD-009; needed before AUD-010 accepts real seed payloads.
  **Acceptance:** A valid synthetic signal follows the same schema/processing contract as live and stores under
  its actual simulation partition; malformed input is rejected before writes.

- [x] AUD-012 - Implement a bounded, independent historical incident snapshot.

  **Remediation (2026-09-16):** Replay source access is explicitly live-bound and route-authorized by incident jurisdiction; snapshots are capped at 10,000 records, deep-copied, time-windowed, and remap signal/incident IDs before canonical simulation persistence. Focused validation included the 10,000-row boundary within 43 passing tests.

  **Original obligations:** T023, T024, T025; FR-013, FR-014, FR-015; US2-AS2; EC-06.
  **Expected/observed/impact:** [Replay](../../apps/api/app/services/scenario_seeding_service.py#L77) reads the first
  10,000 live signals before incident filtering, ignores `start`, `end` and compression, shallow-copies records,
  retains incident/document/provenance references, and omits recommendations and timeline state.
  **Developer work:** Authorize source-incident access; query the specified time window with full pagination
  and a stable snapshot boundary. Deep-copy the complete supported incident graph and remap every instance ID
  and reference, distinguishing immutable catalogue IDs from live operational IDs. Preserve snapshot provenance
  without a live alias/view, and support the documented replay start point and scheduling mode.
  **Tester work:** Add service and route cases in [seeding](../../tests/unit/test_scenario_seeding.py#L10) and
  [isolation tests](../../tests/integration/test_tenant_isolation.py#L21). Cover exact window endpoints, invalid or
  inverted dates, an incident after the first 10,000 unrelated records, active live incident mutation during/after
  snapshot, nested object mutation in memory, missing source, denied source access, and repeated replay to two
  simulations. Assert no retained live operational IDs and correct graph references. Use F1/F2/F3.
  **Dependencies:** AUD-003, AUD-004, AUD-009, AUD-011, AUD-013.
  **Acceptance:** Replay is a complete authorized snapshot of only the selected segment, with new IDs and no
  ongoing read/write dependency on live state.

- [x] AUD-013 - Make scheduling and lifecycle state authoritative for injection and processing.

  **Remediation (2026-09-16):** Template/replay seeding is schedule-only, scheduler timelines and cursors are durable, delivery tasks are idempotently owned and restarted/stopped with lifecycle state, paused chat is refused, and typed UUID routes remove legacy lifecycle shadowing. Focused validation: 47 passed.

  **Original obligations:** T010, T024, T025, T034; FR-008, FR-014; US2-AS3; EC-05.
  **Expected/observed/impact:** [Seeding](../../apps/api/app/services/scenario_seeding_service.py#L30) writes all signals
  immediately; [replay_realtime](../../apps/api/app/services/scenario_seeding_service.py#L114) sleeps each absolute
  offset cumulatively and has no caller. The better [WarpScheduler](../../apps/api/app/services/warp_scheduler.py#L131)
  checks the clock, but its delivery loop is not started/restarted by the app. [Chat](../../apps/api/app/services/simulation/controller_service.py#L324)
  does not check original lifecycle state. Old/new pause URL templates overlap in [registration order](../../apps/api/app/api/router.py#L68).
  **Developer work:** Choose one authoritative lifecycle/ID mapping for tenant, raw-UUID and controller entry
  points. Schedule pending signals without making them operational early; start/resume durable workers at
  application lifecycle boundaries, recover cursors after restart, and serialize concurrent transitions.
  Gate every injection and agent entry on state; preserve reads and state during pause and do not reset an exercise
  when its coordinator disconnects. Reconcile the later in-flight-pause policy explicitly with this specification.
  **Tester work:** Extend [fake-clock scheduler tests](../../tests/unit/test_warp_scheduler.py#L25),
  [HTTP clock tests](../../tests/contract/test_warp_speed_api.py#L119) and
  [lifecycle tests](../../tests/integration/test_simulation_lifecycle.py#L20). Use offsets 0/60/120, equal offsets,
  compression, mid-delay pause/resume, restart, two workers, archived/deleted tenant, paused chat and raw UUID routes.
  Assert no pre-due/duplicate/paused delivery, correct route selection, preserved context and no lost accepted work.
  Use F1/F2/F3; do not use real sleeps for deterministic timing assertions.
  **Dependencies:** AUD-006, AUD-008, AUD-009, AUD-024.
  **Acceptance:** All producers and agents obey one lifecycle boundary; registered workers deliver each due signal
  once in order and restore processing without losing exercise state.

- [x] AUD-014 - Connect the same agent business workflow to live and synthetic inputs.

  **Remediation (2026-09-16):** Scheduled simulation signals now publish the canonical `SignalAcceptedEvent` used by live ingestion. MAF workflow entry, run records, executor payloads, checkpoints, and HITL metadata carry required tenant identity. Reachable workflow/handoff validation: 21 passed; direct MAF execution is dependency-blocked because `agent_framework` is unavailable in the local environment.

  **Original obligations:** T012, T021, T028, T042; FR-002, FR-016, FR-017; US1-AS4.
  **Expected/observed/impact:** [Monitoring's explicit handoff propagation](../../apps/agents/monitoring/pipeline.py#L289)
  is present. However, [seeding](../../apps/api/app/services/scenario_seeding_service.py#L30) stops at storage;
  [MAF creation](../../apps/agents/maf_runtime/workflow/builder.py#L89) uses the repository's default live tenant,
  and [dispatcher requests](../../apps/agents/dispatcher/agent.py#L209) produce prompt-based replies, not the full chain.
  **Developer work:** Document the approved common workflow after the explicit legacy-to-MAF migration;
  do not restore old names solely to match the task text. Feed both input modes through that graph, carry a
  validated tenant through envelopes, checkpoints, handoffs, callbacks, audit and all generated artifacts,
  and reject missing/mismatched tenant context. Ensure the worker uses production wiring, not a smoke-only entry.
  **Tester work:** Extend [handoff integration](../../tests/integration/test_handoff_chain.py#L5) and
  [isolation tests](../../tests/integration/test_tenant_isolation.py#L21) with all five agents and fake transports.
  Compare live/sim business results modulo IDs/time, retry a handoff after context loss, and use identical incident
  IDs in different tenants. Assert each downstream scope/checkpoint/artifact and zero live mutations from sim.
  The existing handoff test uses a no-op subscriber and does not prove this. Use F2/F4.
  **Dependencies:** AUD-002, AUD-003, AUD-004, AUD-011, AUD-013, AUD-019.
  **Acceptance:** The same approved graph executes in both modes and every persisted/generated artifact retains
  the authenticated triggering tenant, including retry and resumed processing.

- [x] AUD-015 - Persist persona assignments and complete tenant-scoped human workflow outcomes.

  **Remediation (2026-09-16):** Structured participant assignments are catalogue-validated and persist OID, persona, organisation, jurisdiction, and role. Authenticated assignments now control jurisdiction-scoped tasks, inbound requests, pending approvals, and workspace identity; all decision outcomes remain distinct and tenant-audited. Backend workspace validation: 33 passed; frontend refresh is 5 seconds. Multi-user browser timing remains unverified.

  **Original obligations:** T026, T027, T028; FR-018, FR-024; US3-AS1, US3-AS2, US3-AS3, US3-AS4.
  **Expected/observed/impact:** [Participants](../../apps/api/app/api/routes/simulations.py#L239) retain OIDs only;
  [workspace filtering](../../apps/api/app/services/persona_workspace_service.py#L28) selects by caller persona/org,
  not authenticated simulation assignment/jurisdiction. [Approval mapping](../../apps/api/app/services/recommendation_service.py#L19)
  treats every non-approved outcome as rejected and writes no simulation approval audit.
  **Developer work:** Persist participant-to-persona/organisation/jurisdiction assignments, validate their
  references, and resolve workspace identity server-side. Share live/simulation filtering logic without sharing
  data. Implement review, approval, rejection, escalation, and alert drafting/publication with authorized actor
  attribution and tenant audit; synchronize coordination task updates across participants.
  **Tester work:** Expand [participant tests](../../tests/unit/test_simulation_participant_rbac.py#L45),
  [isolation](../../tests/integration/test_tenant_isolation.py#L21), and
  [web exercise coverage](../../tests/e2e/web-coverage/cross-cutting/simulation-playback.spec.ts#L15).
  Test assigned versus forged personas, two jurisdictions in one org, missing/duplicate assignment, commander
  approval, officer refusal, all four decision outcomes, simultaneous task edits and two participants plus a live observer.
  Assert persisted assignment, role/jurisdiction filtering, distinct escalation, audit actor, and update visibility
  within 5 seconds in later browser validation. Use F1/F2/F3/F6/F7.
  **Dependencies:** AUD-001, AUD-002, AUD-003, AUD-006, AUD-019.
  **Acceptance:** Participants can complete the full workflow using only their authorized tenant/persona data;
  decisions and collaborative task updates never affect live or other simulations.

### User Experience and Reporting

- [x] AUD-016 - Complete the authenticated simulation management and dashboard experience.

  **Remediation (2026-09-16):**
  All simulation clients ([simulations](../../apps/web/src/lib/api/simulations.ts#L1),
  [playback](../../apps/web/src/lib/api/simulation-playback.ts#L1), [chat](../../apps/web/src/lib/api/simulation_chat.ts#L1))
  now attach a bearer through the existing MSAL helper via
  [simulation-auth](../../apps/web/src/lib/api/simulation-auth.ts#L1); no second auth stack was introduced and a
  token-acquisition failure surfaces instead of an anonymous call. The [list](../../apps/web/src/app/simulations/page.tsx#L1)
  renders load and lifecycle-action errors with retry and has functional limit/offset paging with a visible range.
  [Create](../../apps/web/src/app/simulations/create/page.tsx#L1) exposes an empty/template/replay choice (curated pack IDs)
  and structured participant assignment rows (oid, persona, organisation, jurisdiction, role) posted to the participants
  endpoint, reporting partial post-create failures rather than navigating away. The
  [dashboard](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L1) now shows cache-key and throttle status alongside
  the resource meters, and the browser-only Exercise Objectives panel (plus its CSS) was removed rather than dressed up as
  durable coordination state. Tests: `apps/web/tests/unit/spec_007/simulation-api-auth.test.ts`,
  `simulation-list-page.test.tsx`, `simulation-create-page.test.tsx` (vitest 15 files / 87 tests passed for the
  simulation suites). Assignment-backed persona workspace, 5-second refresh, persistent throttle notices, truthful
  cache states, and stable report links are now present. Focused frontend validation: 52 passed. SC-003 timing and
  role-matrix browser execution remain unverified.

  **Original obligations:** T018, T020, T021, T027, T038; FR-006, FR-020, FR-023, FR-024; US2-AS4, US5-AS3.
  **Expected/observed/impact:** [Create](../../apps/web/src/app/simulations/create/page.tsx#L23) submits an empty
  participant list and has no template/replay choice; [list](../../apps/web/src/app/simulations/page.tsx#L7) exposes
  controls without role gating, swallows list errors, has no paging UI/cache-key/throttle columns; [detail](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L94)
  is a map/chat/metadata workspace, not the specified operational dashboard. Its event poll is 8 seconds and
  objectives are local component state. [The client](../../apps/web/src/lib/api/simulations.ts#L108) supplies no bearer token.
  **Developer work:** Use the application's approved authenticated transport and server action permissions;
  implement create/seed/replay/invite/persona actions, usable pagination/error states, truthful resource and throttle
  displays, full operational components, and updates meeting the 5-second task visibility requirement.
  Do not turn local objectives or chat text into apparent durable coordination state.
  **Tester work:** Extend [existing web exercise coverage](../../tests/e2e/web-coverage/cross-cutting/simulation-playback.spec.ts#L15)
  with real tenant-backed routes and authenticated fixtures. Cover coordinator, member, observer and unauthorized
  users; empty/failure/multiple pages; create with template and participants; invite; lifecycle errors; simultaneous
  activity; page reload; throttled state. Assert the full workflow and actual resource counts, not merely page load.
  Use F3/F6/F7; time SC-003 only after the backend is complete.
  **Dependencies:** AUD-001, AUD-006, AUD-010, AUD-013, AUD-015, AUD-024, AUD-025, AUD-028.
  **Acceptance:** Authorized users can perform every management/exercise action and see accurate, tenant-scoped
  operational data; absent capabilities, auth failures and stale resource values are not hidden as success.

- [x] AUD-017 - Preserve the live-data boundary while exposing developer-only simulation navigation.

  **Revised remediation (2026-10-02):** The shared shell
  ([app-shell](../../packages/ui/src/components/layout/app-shell.tsx#L1)) exposes a Simulations navigation entry only when
  the existing developer-environment flag is enabled. The entry links to the separate `/simulations` management area and
  does not place simulation data, tenant selection, mode switching, status, or controls in a live view. Staging and
  production retain the hidden-navigation boundary. Exercise-local navigation and the mandatory simulation marker remain
  owned by [simulations layout](../../apps/web/src/app/simulations/layout.tsx#L1). Tests cover both enabled and disabled
  environments and continue to assert that the live shell renders no simulation dashboard data.

  **Original obligations:** T021, T042; FR-022; US1-AS3; SC-007.
  **Expected/observed/impact:** FR-022 prohibits simulation data and tenant-mode controls in live views, but does not
  require the separate management route to be undiscoverable in developer environments. The revised boundary preserves
  route and tenant isolation while satisfying FR-023 discoverability for local and Azure-hosted development.
  **Developer work:** Keep simulation data and controls out of live views; expose only a developer-gated link to the
  separate management area. Preserve route separation and do not introduce a live tenant picker or mode toggle.
  **Tester work:** Add desktop/mobile assertions in [web exercise coverage](../../tests/e2e/web-coverage/cross-cutting/simulation-playback.spec.ts#L15)
  for live map/detail/workspace while three simulations exist. Inspect accessible navigation, footer, mobile menu,
  all visible data and direct-link behavior. Negative assertion must fail on any simulation affordance, not just
  on a particular banner test ID. Use F6/F7; arrange the three-persona usability assessment under F9.
  **Dependencies:** AUD-002, AUD-003, AUD-016.
  **Acceptance:** Live pages contain no simulation data, tenant selector, mode toggle, status, or controls. Developer
  environments expose the separate simulation management route; non-developer environments do not.

- [x] AUD-018 - Render a persistent simulation marker across routes and UI states.

  **Remediation (2026-09-16):** A new
  [simulations route layout](../../apps/web/src/app/simulations/layout.tsx#L1) owns the marker for every `/simulations/*`
  view, so it now renders during loading, error, playback and report states instead of sitting behind each page's early
  returns; the duplicated per-page banners on the dashboard and report route were removed.
  [Banner CSS](../../apps/web/src/app/globals.css#L3949) is `position: sticky; top: 60px` with
  `z-index: calc(var(--ama-z-modal) - 1)` so it stays visible while scrolling, above page overlays and below the modal and
  nav layers. [The banner](../../apps/web/src/components/simulation-banner.tsx#L1) takes an explicit status and gained an
  `unknown` "Status pending" state; routes publish the real tenant status through
  [useReportSimulationLifecycle](../../apps/web/src/components/simulation-lifecycle.tsx#L1), so an archived or paused
  exercise is never advertised as Active and an unfetched one is not either. Tests:
  `apps/web/tests/unit/spec_007/simulation-layout-marker.test.tsx` (loading/error/playback/report states, pending default,
  lifecycle mapping, non-dismissible) and the stylesheet assertions in `live-shell-simulation-boundary.test.tsx`.
  The watermark specification now lives under the configured Playwright test directory and fails hard when the marker
  is absent. Focused frontend validation: 52 passed. Browser verification of scroll, zoom, fullscreen map, and dialog
  overlap remains unexecuted because the local Playwright installation cannot enumerate tests.

  **Original obligations:** T019, T021, T032; FR-021; US2-AS4, US3-AS1.
  **Expected/observed/impact:** [Banner CSS](../../apps/web/src/app/globals.css#L3949) has no fixed/sticky or
  overlay-priority rule. [Detail loading/error returns](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L209)
  precede the banner; [playback](../../apps/web/src/app/simulations/[tenantId]/playback/page.tsx#L1) has none.
  [Report loading/errors](../../apps/web/src/app/simulations/reports/[reportId]/page.tsx#L40) also omit it.
  **Developer work:** Own the mandatory identification at the simulation layout boundary, including initial,
  loading, error, playback and report views. Keep it non-dismissible, visible while scrolling and above relevant
  overlays without blocking controls; connect current lifecycle status rather than always showing default Active.
  **Tester work:** Extend [banner component tests](../../apps/web/tests/unit/spec_036/simulation-banner.test.tsx#L9)
  and [watermark browser test](../../apps/web/tests/a11y/simulation-watermark.spec.ts#L21). Ensure browser discovery
  is fixed first: the latter is outside the configured Playwright test directories. Test scroll, narrow viewport,
  zoom, fullscreen map, dialogs, delayed/failed fetch, lifecycle changes, direct report and playback links.
  Assert visible simulation wording and screen-reader announcement; absence must fail, not soft-skip. Use F5/F6/F7.
  **Dependencies:** AUD-016, AUD-021, AUD-029.
  **Acceptance:** Every simulation view/state continuously identifies itself; no dismissal, obscuring overlay,
  loading path or missing lifecycle prop can remove/misrepresent the marker.

- [ ] AUD-019 - Persist complete immutable audit events at every safety-critical boundary.

  **Remediation status (2026-09-16):** The process-wide simulation writer now requires managed-identity Blob configuration in staging/production, writes deterministic append-only records, treats duplicate correlation writes idempotently, and raises on storage failure. Tenant-scoped approval/publication/handoff/task audit producers bridge into this writer. Focused validation: 24 passed. **GOVERNANCE-BLOCKED:** Azure Storage immutability/WORM configuration is a Bicep change and remains open pending spec-007 policy discovery and Portal parity.

  **Original obligations:** T012b, T017, T028, T035; FR-018, FR-019, FR-025; US4-AS3; NFR-003.
  **Expected/observed/impact:** [Original audit construction](../../apps/api/app/api/routes/simulations.py#L30)
  has no Blob client; [write_event](../../apps/api/app/services/simulation_audit_writer.py#L23) stores memory entries
  or swallows Blob failure, and its wired calls cover creation/seeding, not every approval/alert/handoff/task change.
  [Original containers](../../infra/main.bicep#L526) have no WORM policy. Later
  [playback recording](../../apps/api/app/services/simulation_event_recorder.py#L48) and
  [typed audit](../../apps/api/app/services/simulation/audit_writer.py#L240) are distinct, not automatic coverage.
  **Developer work:** Unify or explicitly bridge audit ownership across these producers. Write tenant-specific,
  append-only, durable events with authenticated actor, event/resource IDs, timestamps and provenance for each
  safety-critical action before acknowledging durable success. Use an outbox/retry or fail-closed policy for
  failures. Apply and verify the appropriate immutable retention policy to the actual original audit/archive
  destinations; `overwrite=False` and mutable Cosmos upserts are not WORM proof.
  **Tester work:** Add strict Blob/failure spies in [lifecycle](../../tests/integration/test_simulation_lifecycle.py#L20)
  and [isolation tests](../../tests/integration/test_tenant_isolation.py#L21). Exercise every action class,
  concurrency/retry, missing actor, archive handoff, same IDs across tenants, Blob outage and restart.
  Assert one durable owned record per accepted action and no live-prefix record. Use F2/F3/F4/F8;
  immutability enforcement requires separately approved F9 testing against the correct container.
  **Dependencies:** AUD-001, AUD-002, AUD-009; coordinate producer integration with AUD-003/AUD-014/AUD-015.
  **Acceptance:** A complete exercise can be reconstructed from immutable tenant audit, including decisions,
  failures and actor attribution; storage failure cannot masquerade as durable audit success.

- [x] AUD-020 - Build truthful complete reports and persist/retrieve stable results.

  **Remediation (2026-09-16):** Reports use deterministic IDs, paginate tenant signals, derive participants, organisations, exact decision buckets, alerts, tasks and timeline from tenant records, preserve unavailable metrics as null, compare targets and prior runs, and publish URI/ID only after append-only persistence. Mixed-outcome/prior-run validation: 4 passed; archive integration is covered by the isolation gate. The measured 60-second target remains unverified.

  **Original obligations:** T029, T030, T031; FR-026, FR-027; US4-AS1, US4-AS2; SC-004.
  **Expected/observed/impact:** [Report generation](../../apps/api/app/services/exercise_report_service.py#L32)
  reads only up to 10,000 signals, treats participant OIDs as personas, leaves timeline/organisations/gaps/metrics/
  benchmarks empty, and uses recommendation counters rather than decisions. [Persistence](../../apps/api/app/services/exercise_report_service.py#L97)
  is optional, overwritable and failure-swallowing, but a URI is still saved. [The model](../../packages/domain/src/domain/models/exercise_report.py#L39)
  omits required rich organisation/persona and escalation/approval-latency summary shapes.
  **Developer work:** Aggregate the complete tenant's signals, decisions, approvals, alerts, task changes and
  timeline; resolve assigned personas/organisations; calculate defined metrics and gaps. Load scenario targets
  and comparable previous exercises. Version/align the report schema, paginate input, persist one identifiable
  completed result, and publish its URI only after storage success. Preserve explicit unavailable metrics rather
  than inventing zero performance.
  **Tester work:** Extend [report contracts](../../tests/contract/test_simulation_api_contract.py#L209) and
  [lifecycle tests](../../tests/integration/test_simulation_lifecycle.py#L20) using a known mixed-outcome exercise.
  Assert exact timeline/actors/counts, approved/rejected/escalated totals, timing calculations, target deltas,
  prior-run comparison, empty exercise, missing benchmark, pagination beyond 10,000, restart/readback, and Blob
  failure with no published URI. Use F2/F3/F8; measure 60 seconds separately under F9.
  **Dependencies:** AUD-003, AUD-009, AUD-010, AUD-014, AUD-015, AUD-019, AUD-031.
  **Acceptance:** Every required section is derived from actual isolated records, comparison is meaningful,
  repeated reads return the persisted report, and a missing/failed report is not a false successful URI.

- [x] AUD-021 - Correct report deep-link identity and render all report sections.

  **Remediation (2026-09-16):** Added authorized `GET /simulations/reports/{report_id}`, shared the report type through the authenticated client, exposed completed/archived report links, distinguished forbidden/not-found/pending states, and rendered timeline, decision outcomes, metrics, targets, prior deltas, and gaps. Focused frontend validation: 52 passed. Browser/mobile deep-link execution remains unverified.

  **Original obligations:** T018, T032; FR-026, FR-027; US4-AS1, US4-AS2.
  **Expected/observed/impact:** [The page](../../apps/web/src/app/simulations/reports/[reportId]/page.tsx#L29)
  sends `reportId` to `/simulations/{tenantId}/report`, has no report-to-tenant lookup, and renders no exercise
  timeline. Its locally duplicated interface narrows the required report schema.
  **Developer work:** Use a documented report-ID lookup or an explicit tenant/report route relationship;
  enforce authorization after resolution. Share the aligned report type/API client and expose links from the
  completed exercise. Render timeline, rich participants, all decision/alert outcomes, gaps, metrics, targets,
  deltas and prior-run comparison, with accurate missing/denied/error states and simulation identification.
  **Tester work:** Extend [web exercise coverage](../../tests/e2e/web-coverage/cross-cutting/simulation-playback.spec.ts#L15)
  and [report API contracts](../../tests/contract/test_simulation_api_contract.py#L209). Test a real persisted report
  whose ID differs from tenant ID, refresh/deep link, another participant, nonmember, nonexistent report,
  empty sections, pending generation and malformed response. Assert each required section and correct request ID.
  Use F3/F6/F7.
  **Dependencies:** AUD-006, AUD-018, AUD-020, AUD-028.
  **Acceptance:** A report ID resolves only to an authorized stable report and all required content is usable on desktop/mobile.

### Lifecycle and Governance

- [ ] AUD-022 - Implement durable archive, verified cleanup, and retention-aware deletion.

  **Remediation status (2026-09-16):** Archive is a leased, resumable state machine: report, enumerated/checksummed seed and audit manifest, verified tenant-resource purge, then `Archived` with retention metadata. HTTP returns `202 Archiving`, startup resumes interrupted jobs, admin deletion is not participant-gated, and retained evidence remains available. AUD-022/023/024 validation: 26 passed. **GOVERNANCE-BLOCKED:** immutable-storage policy and measured 95% reclamation/five-minute evidence remain unverified.

  **Original obligations:** T031, T034, T035; FR-009, FR-025, FR-026; NFR-005; US4-AS4, US5-AS4; SC-005.
  **Expected/observed/impact:** [archive_tenant](../../apps/api/app/services/simulation_service.py#L191) sets a string
  URI, attempts optional Redis deletion and marks Archived. It neither generates a report nor snapshots audit/
  seed data nor deletes Cosmos/state records. [Delete](../../apps/api/app/api/routes/simulations.py#L385) only changes
  status immediately. It does not actually erase archives, so actual data loss is not asserted; resource release is absent.
  **Developer work:** Create a resumable archive job: quiesce processing, generate/persist the report, verify
  complete immutable audit/seed snapshots, then clean all tenant operational stores/caches/worker state.
  Retain minimal authorized lookup metadata for reports and retention. Do not mark Archived or report success
  until required steps complete; handle retry/partial failure and cancellation. Enforce administrator permission
  and retention before any destructive deletion; return truthful 202/job state.
  **Tester work:** Replace state-only assertions in [lifecycle tests](../../tests/integration/test_simulation_lifecycle.py#L20)
  with fake storage manifests and real service calls. Cover empty/10,000-signal exercise, active/paused archive,
  Blob failure, cleanup failure, restart/retry, two archivers, retained foreign tenants, deletion before/after
  retention and report access afterward. Assert write-before-delete ordering, checksums/counts, no false Archived,
  and actual removed keys/documents. Use F2/F3/F8; F9 must measure 95% reclamation and five minutes.
  **Dependencies:** AUD-006, AUD-008, AUD-009, AUD-013, AUD-019, AUD-020, AUD-031.
  **Acceptance:** Immutable report/audit/seed evidence survives verified tenant cleanup; retention/admin policy
  governs deletion, and resource/time claims have measured evidence before being marked complete.

- [x] AUD-023 - Implement scheduled idle expiry and reliable advance notification.

  **Remediation (2026-09-16):** Expiry is idle-based, accepted writes refresh TTL, a persisted notifier/outbox records explicit recipients before archive, short-TTL and already-expired tenants receive notice, undefined/null legacy fields are handled, and ETag leases prevent competing workers. Paused tenants follow the documented idle policy. AUD-022/023/024 validation: 26 passed. Deployed notification and multi-replica evidence remain unverified.

  **Original obligations:** T036; FR-011; US5-AS2; EC-04.
  **Expected/observed/impact:** [The model](../../packages/domain/src/domain/models/simulation_tenant.py#L102)
  computes expiry from creation; [check_expired_tenants](../../apps/api/app/services/simulation_service.py#L226)
  has no scheduled caller, activity timestamp or 24-hour notice. The specification says idle TTL while the
  data model describes creation TTL, so the policy needs an explicit resolution rather than an accidental choice.
  **Developer work:** Establish authoritative activity/expiry semantics and a durable, multi-replica-safe scheduler.
  Record/deduplicate coordinator warnings at least 24 hours before eligible automatic archive, honor active and
  paused state policy, re-evaluate expiry after activity, and invoke the resumable archive workflow. Define behavior
  for TTL shorter than the notice window, failed notice delivery, clock skew and in-progress archive.
  **Tester work:** Add fake-clock/service tests to [simulation service](../../tests/unit/test_simulation_service.py#L16)
  and [lifecycle](../../tests/integration/test_simulation_lifecycle.py#L16). Cover the 24-hour boundary, 72-hour
  default, activity just before expiry, paused exercise, short TTL, duplicate schedulers, failed notice and
  archive retry. Assert notice recipient/timestamp, no premature archive and complete retained evidence. Use F1/F2/F8.
  **Dependencies:** AUD-009, AUD-022, AUD-028.
  **Acceptance:** Expiry is based on the approved idle policy, warnings meet the required lead time, and a registered
  worker safely archives eligible exercises once without affecting other tenants.

- [x] AUD-024 - Enforce concurrency and resource budgets with truthful counters.

  **Remediation (2026-09-16):** Capacity is shared across repository instances and uses a central ETag reservation in Cosmos; failed provisioning releases slots and 409 lists only capacity-occupying tenants. Signal/recommendation/duration budgets, serialized bytes, and cache keys update at guarded write boundaries with rollback. AUD-022/023/024 validation: 26 passed. Authorized 10,000-signal load evidence remains unverified.

  **Original obligations:** T002, T014, T015, T033, T038; FR-010, FR-029; US5-AS1, US5-AS3; EC-07.
  **Expected/observed/impact:** [Validation](../../apps/api/app/validators/simulation_validators.py#L11) checks a
  count before independent creation and only validates positive configured budgets. [Writes](../../apps/api/app/repositories/signal_repository.py#L51)
  never enforce these budgets. The [controller counter](../../apps/api/app/services/simulation/controller_service.py#L1081)
  is not a storage measurement. Concurrency response also omits the required active-simulation listing.
  **Developer work:** Atomically reserve/release concurrency capacity across replicas and failed provisioning;
  enforce signal/recommendation/duration limits at every write/scheduling boundary. Count accepted durable records,
  bytes and cache keys with defined consistency, not UI animation. Handle idempotent retries, deletion/archive
  release, and pagination when reporting the cap; keep live operations outside simulation budgets.
  **Tester work:** Extend [concurrency test](../../tests/unit/test_simulation_service.py#L55),
  [governor tests](../../tests/unit/test_resource_governor.py#L20), and [lifecycle](../../tests/integration/test_simulation_lifecycle.py#L20).
  Race creates through two independent repository instances, test cap-1/cap/cap+1, failed provisioning release,
  exact budget/budget+1, duplicated writes, 10,000 allowed signals, duration expiry and retry after archive.
  Assert accepted counts, unchanged live counters and a clear cap response listing active exercises. Use F1/F2/F3/F9.
  **Dependencies:** AUD-004, AUD-008, AUD-009, AUD-011, AUD-013.
  **Acceptance:** Configured limits hold across all workers and write paths; displayed consumption agrees with stored resources.

- [x] AUD-025 - Connect resource governance to real utilisation and every simulation write path.

  **Remediation (2026-09-16):** Composite configured usage providers distinguish unconfigured from unavailable telemetry; shared process/Redis reservations preserve tokens across mode changes, explicit live reservations take priority, quota-derived limits guard simulation writes, and convergence/pending state is truthful. AUD-025 validation: 13 focused tests; combined governance/telemetry validation: 99 passed, 2 skipped. Deployed utilization and latency evidence remain unverified.

  **Original obligations:** T033, T037; FR-028, FR-030; NFR-002; US5 resource governance; EC-01, EC-07.
  **Expected/observed/impact:** [check_write_allowed](../../apps/api/app/services/resource_governor.py#L45) and
  `evaluate_utilisation` have no application callers. [Utilisation](../../apps/api/app/services/resource_governor.py#L109)
  reads optional Redis memory only, not Cosmos RU or LLM usage; configured quota is not used to size/refill the
  bucket. Incident mode consumes five tokens and then one more; that is not a demonstrated 20% shared-capacity quota.
  **Developer work:** Feed measured RU/compute/cache/LLM demand into a documented live-first policy; apply it
  before seed/replay/agent writes, share reservations across replicas, derive rates/bursts from configured quotas,
  and make threshold transitions effective. Notify participants when incident throttling starts/ends, preserve
  state, avoid automatic pause, and initialize new simulations under an existing incident mode.
  **Tester work:** Extend [governor tests](../../tests/unit/test_resource_governor.py#L20) using deterministic usage
  and clock providers plus write spies. Cover 69/70/71% thresholds, configurable quotas, token exhaustion/refill,
  mixed live/sim queues, missing telemetry, independent workers, incident during seed, new/paused simulations,
  repeated declare/resolve and notification deduplication. Assert actual blocked/admitted writes and live priority,
  not only mode fields. Use F1/F2/F3; F9 measures the live latency/throughput budget.
  **Dependencies:** AUD-013, AUD-024, AUD-026, AUD-027, AUD-031.
  **Acceptance:** Simulation work yields capacity according to configuration before live contention; participants
  are notified and state survives; actual performance claims have separate measured evidence.

- [x] AUD-026 - Authorize and persist incident-mode transitions.

  **Remediation (2026-09-16):** Incident mode uses conditional, idempotent governance-container transitions; configured Cosmos outage cannot fall back to local normal. Routes resolve shared composition late, require administrators, audit only after persistence, report partial convergence truthfully, and new tenants inherit mode. AUD-026 validation: 8 focused tests; combined governance/telemetry validation: 99 passed, 2 skipped. Deployed contention/restart evidence remains unverified.

  **Original obligations:** T037b; FR-031, FR-028, FR-030.
  **Expected/observed/impact:** [Declare/resolve endpoints](../../apps/api/app/api/routes/incidents.py#L20) have no
  administrator check and [the governor](../../apps/api/app/services/resource_governor.py#L43) keeps incident state
  in a process boolean. The independently constructed simulation repository also has a separate memory fallback.
  **Developer work:** Require the established administrator permission and authenticated actor, persist
  authoritative incident-mode state in governance Cosmos with conditional/idempotent transitions, and propagate
  it to all workers and new exercises. Audit declaration/resolution and retain mode through restarts. Apply mode
  changes only after durable success; handle competing requests and unavailable governance storage explicitly.
  **Tester work:** Extend [API contracts](../../tests/contract/test_simulation_api_contract.py#L15) and
  [governor tests](../../tests/unit/test_resource_governor.py#L34). Cover admin, ordinary SimulationUser, anonymous,
  duplicate declaration, concurrent resolve, repository outage, fresh governor process and simulation created
  after declaration. Assert 403/401 as agreed, one durable transition/audit and consistent mode across instances.
  Use F1/F3/F8.
  **Dependencies:** AUD-001, AUD-006, AUD-019.
  **Acceptance:** Only an administrator can change mode; every replica observes the same persisted state and a
  failed transition does not announce success or silently restore normal processing.

### Telemetry, Contracts, and Verification

- [x] AUD-027 - Emit tenant dimensions throughout the actual telemetry pipeline.

  **Remediation (2026-09-16):** Request and child spans, log records, ingestion, scheduler, simulation-runner, and governor metrics carry structured `tenant_id`; unscoped work is `unknown` and explicit system ingestion remains `live`. SDK-backed processor/configuration health is surfaced instead of silently ignored. AUD-027 validation: 8 focused tests, 2 SDK-gated skips; combined governance/telemetry validation: 99 passed, 2 skipped. Deployed Application Insights query evidence remains unverified.

  **Original obligations:** T010, T012, T040; NFR-006; FR-002; quickstart monitoring claims.
  **Expected/observed/impact:** [Middleware](../../apps/api/app/middleware/tenant_middleware.py#L20) adds a response
  header but no telemetry dimension; [ingestion emissions](../../apps/api/app/services/ingestion/pipeline_base.py#L161)
  use pipeline dimensions, and [monitoring KQL](../../infra/modules/monitoring.bicep#L153) expects `customDimensions.tenant_id`.
  Formatting `tenant_id` into log text is not equivalent to populating that custom dimension.
  **Developer work:** Enrich request spans, dependency traces, logs and metrics with the resolved tenant using
  the supported instrumentation pipeline. Set live explicitly for system ingestion and propagate tenant through
  background/retry work. Update the shared dashboard/alert queries to the emitted schema and prevent dimension
  leakage between concurrent requests. Do not include credentials or raw sensitive payloads in telemetry.
  **Tester work:** Extend [tenant-context tests](../../tests/unit/test_tenant_context.py#L29) and
  [isolation tests](../../tests/integration/test_tenant_isolation.py#L21) with an in-memory exporter capturing
  request, repository failure, agent, ingestion, background, retry and archive emissions. Assert the dimension
  on every signal class and no cross-request carry-over. Use F1/F2/F8; later F9 validates query results in the
  shared Application Insights resource. The existing header/ContextVar tests do not establish export.
  **Dependencies:** AUD-002, AUD-014, AUD-019.
  **Acceptance:** All scoped telemetry has the correct structured `tenant_id`, and the configured per-tenant
  alerts/dashboards consume verified exported data.

- [x] AUD-028 - Reconcile wire contracts, error taxonomy, expiry policy and authored completion claims.

  **Remediation (2026-09-16):** Contract version 2 establishes canonical Title-Case statuses, 404 report reads, 202 resumable archive, idle TTL, truthful counters, current replay/participant payloads, and report-ID lookup. Machine-readable ownership/compatibility decisions are in `contracts/contract-resolution.v2.json`. Validation: 17 tests passed; Markdown lint and JSON parse passed.

  **Original obligations:** T006, T010, T016, T018, T025, T026, T031, T034, T044; FR-002, FR-005, FR-011, FR-023.
  **Expected/observed/impact:** [Contracts](contracts/simulation-api.md#L1) specify lower-case enums, replay
  `start_from/end_at/replay_mode`, string participants plus persona assignments, missing-report 404 and archiving
  202. [Routes](../../apps/api/app/api/routes/simulations.py#L191) use different bodies/Title-Case states, ignore
  replay mode, generate reports on GET, and return completed archive state. Membership/claim and idle/creation
  expiry requirements also disagree; inactive middleware rejection would block archive/report management.
  **Developer work:** Obtain an explicit contract decision for each conflict, preserving compatibility where
  necessary; implement typed input validation, pagination bounds, error responses, transition permissions and
  asynchronous status semantics. Update the spec/contract/quickstart only in later authorized work, together
  with implementation and evidence, not by weakening safety clauses to match stubs. Correct outdated helper paths,
  placeholder tenant IDs, Blob listing container, test names and claimed reviews.
  **Tester work:** Turn [model-only contract tests](../../tests/contract/test_simulation_api_contract.py#L15)
  into full HTTP cases using [the existing fixture](../../tests/contract/test_warp_speed_api.py#L24).
  Exercise every row of the endpoint matrix below, documented example bodies, bad enums/types, empty participants,
  invalid OIDs, negative paging, unavailable storage and absent reports. Assert exact schemas/statuses and no writes
  on rejected input. Use F3/F8; perform the corrected quickstart only later under F9.
  **Dependencies:** Contract decisions unblock AUD-002, AUD-006, AUD-009, AUD-013, AUD-023; implementation depends
  on the corresponding owning tasks, not a documentation-only resolution.
  **Acceptance:** Specification, contracts, clients, route behavior and future examples agree; security and
  measurement claims are explicitly backed or remain open/UNVERIFIED.

- [x] AUD-029 - Replace completion-by-checkbox with behavior tests and attributable execution/review evidence.

  **Remediation (2026-09-16):** Added the registered `spec007_isolation` marker, dedicated strict CI job, explicit minimum count, selector-completeness guard, truthful dirty-worktree/base-revision attribution, and a claim manifest separating verified source behavior from deferred WORM, staging, SDK-export, browser, and usability evidence. Exact gate: 113 selected, 111 passed, 2 SDK-gated skipped; all three static guards pass.

  **Original obligations:** T041, T042, T043, T044; all NFRs and SCs; ASM-016, PER-013, PER-014, HYP-005;
  local quality checklist and plan gates.
  **Expected/observed/impact:** [Named API tests](../../tests/contract/test_simulation_api_contract.py#L15) construct
  response dictionaries; [lifecycle](../../tests/integration/test_simulation_lifecycle.py#L20) never seeds or calls
  archive; [seeding tests](../../tests/unit/test_scenario_seeding.py#L10) only validate models.
  [Playwright discovery](../../apps/web/playwright.config.cts#L4) excludes the standalone watermark file,
  whose [missing-marker branch](../../apps/web/tests/a11y/simulation-watermark.spec.ts#L42) records a gap rather than failing.
  [Playback E2E](../../tests/e2e/web-coverage/cross-cutting/simulation-playback.spec.ts#L34) tests an outcome evaluator's
  cache, not simulation replay. CI source is not evidence that a deployment passed.
  **Developer work:** Reuse the existing test modules and helpers for the concrete cases in every AUD task,
  including real HTTP wiring and strict storage doubles. Fix browser discovery and prohibit soft-pass/empty
  fixture paths for mandatory safety checks. Make the complete isolation suite a required release gate and
  publish traceable results tied to revision/environment/configuration. Keep original checked states historical
  until an authorized reconciliation; obtain required security/product/operator reviews instead of inventing sign-off.
  **Tester work:** Execute F1-F8 only after the corresponding repairs; require nonzero selected cases and no
  unexpected skips. Under separately approved F9, measure provisioning, 10,000-signal processing/archival,
  5,000-signal end-to-end leakage, 3 concurrent simulations against the 50,000/hour live baseline, 60-second
  reporting, 95% reclamation and the under-10-minute participant flow. Conduct the three-operational-persona
  usability study, capture actor consultation/rubric hypothesis evidence, and attach signed/date-stamped results.
  **Dependencies:** All functional remedial tasks must meet their local acceptance gates before final measured
  sign-off; AUD-018/AUD-021 browser cases must be discoverable, and AUD-031 precedes performance evidence.
  **Acceptance:** Every original obligation has actual assertions and attributable results/review evidence;
  missing infrastructure or reviewers are explicit blockers, never passing placeholders.

- [x] AUD-030 - Complete or explicitly resolve the middleware package setup deliverable.

  **Remediation (2026-09-16):** Added `apps/api/app/middleware/__init__.py`. Direct package/module import succeeds and the simulation contract suite collects 15 tests.

  **Original obligations:** T001, T003.
  **Expected/observed/impact:** T003 requires an initializer in the [middleware directory](../../apps/api/app/middleware/).
  It is absent, while [tests/unit/\_\_init\_\_.py](../../tests/unit/__init__.py),
  [tests/integration/\_\_init\_\_.py](../../tests/integration/__init__.py), and
  [tests/contract/\_\_init\_\_.py](../../tests/contract/__init__.py) exist. This is a setup discrepancy, not proof that
  Python namespace-package imports fail.
  **Developer work:** In later authorized work, add the required initializer, or record an approved intentional
  namespace-package policy and reconcile the task. **Proposed new path, not existing evidence:**
  `apps/api/app/middleware/__init__.py`. Do not rename working test packages or make unrelated packaging changes.
  **Tester work:** Extend collection/import checks in [API contract tests](../../tests/contract/test_simulation_api_contract.py#L1)
  and verify both supported import styles in the configured test environment. Include clean package installation,
  module discovery and no extra namespace shadowing; F10 is a future collection check, not one performed here.
  **Dependencies:** None; coordinate any task-document reconciliation with AUD-028.
  **Acceptance:** The required package artifact exists or an explicit approved alternative explains the original
  task discrepancy, with reproducible import/collection evidence.

- [x] AUD-031 - Prevent simulation storage I/O from blocking the shared async API loop.

  **Remediation (2026-09-16):** All simulation Cosmos/Blob calls reached from `async` request, service and
  background-task code now run through the bounded offload helper
  [`app.core.async_io.run_blocking`](../../apps/api/app/core/async_io.py), which wraps `asyncio.to_thread`
  (context-copying, so tenant `ContextVar` scoping is preserved) in a per-event-loop semaphore sized by
  `SIMULATION_STORAGE_IO_WORKERS` (default 8). Converted: remaining `SimulationRepository` create/update/query/
  document paths, remaining `SignalRepository` read/query/replace paths, the report service's event-timeline read
  and archive snapshot hashing, the seeding service's template load and replay remap, the playback/annotation
  event-repository reads and writes, the simulation service's event-recorder and event-purge calls, the clock
  endpoint's scheduler-state read, and the warp scheduler's delivery-loop state reads/writes. Inline bulk work is
  bounded: seed-context writes use `gather_bounded` batches, the replay snapshot keeps its 10,000-signal cap and
  now remaps off the loop, and accepted (202) seeding still only schedules — signal delivery remains an
  `asyncio.create_task` scheduler loop, not inline request work. A repository AST scan reports zero remaining
  unoffloaded SDK calls in those modules. Validation: `tests/unit/test_simulation_storage_offload.py` 9 passed;
  focused simulation/seeding/lifecycle/scheduler/playback/contract selection 49 passed; CI `spec007_isolation`
  selector (with the new module added) 47 passed.
  **Explicitly still unmeasured:** no latency or throughput figure is claimed. The tests assert structural
  properties only — blocking doubles execute on non-loop threads, an independent loop ticker keeps progressing,
  and worker/batch limits hold. NFR-001/NFR-002/NFR-005 and SC-002/SC-004 remain UNVERIFIED pending the separately
  authorized F9 mixed-load run; the 10% live-impact budget is still unproven.

  **Original obligations:** T009, T013, T015, T023, T030, T035; NFR-001, NFR-002, NFR-005; SC-002, SC-004.
  **Expected/observed/impact:** [SimulationRepository](../../apps/api/app/repositories/simulation_repository.py#L53)
  and [SignalRepository](../../apps/api/app/repositories/signal_repository.py#L51) call synchronous Cosmos clients
  inside async methods; [seeding](../../apps/api/app/services/scenario_seeding_service.py#L30) repeats them per signal.
  Report Blob reads/writes are similarly synchronous. The declared shared-compute model therefore has an
  event-loop blocking risk; no latency percentage is inferred from this source inspection.
  **Developer work:** Use a consistent async SDK adapter or bounded worker offloading for blocking I/O;
  bound concurrency, cancellation, retries and timeouts with the governor/live-priority policy. Move long
  seed/archive/report jobs out of request processing while maintaining durable status and idempotency.
  Avoid mixing synchronous and asynchronous Cosmos interfaces between the two existing repositories.
  **Tester work:** Add controlled slow-I/O doubles in [service](../../tests/unit/test_simulation_service.py#L16),
  [seeding](../../tests/unit/test_scenario_seeding.py#L10), and [lifecycle tests](../../tests/integration/test_simulation_lifecycle.py#L16).
  Assert an independent live/health request progresses while sim storage is blocked, cancellation leaves
  resumable state, and worker limits hold. Use F1/F2/F3, then F9 for real mixed-load latency/throughput/timing.
  **Dependencies:** AUD-024/AUD-025 establish admission policy; coordinate adapter design with AUD-004/AUD-008.
  **Acceptance:** Simulation I/O does not monopolize the shared event loop; bounded execution and later measured
  live-service budgets are both demonstrated before performance requirements are closed.

## Original Task Coverage

Every original checkbox is `[X]`. States are copied, not changed or retrospectively endorsed.
Each task has one row; supplementary tests cited below were inspected as source, not run.

| Original ID | Original state | Status | Actual implementation and test evidence | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [X] | IMPLEMENTED | [Middleware directory](../../apps/api/app/middleware/), [simulation list](../../apps/web/src/app/simulations/page.tsx#L1), [detail](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L1), [report](../../apps/web/src/app/simulations/reports/[reportId]/page.tsx#L1) and all three named test directories exist. This establishes structure only. | AUD-030 for separate initializer obligation |
| T002 | [X] | IMPLEMENTED | [Settings](../../apps/api/app/core/settings.py#L27) declare defaults 3, 72, 70, 20 and 90 with environment aliases. [Sequential cap test](../../tests/unit/test_simulation_service.py#L55) and [quota-field assertion](../../tests/unit/test_resource_governor.py#L34) cover only part of their use. | AUD-023, AUD-024, AUD-025 |
| T003 | [X] | PARTIAL | Three [test initializers](../../tests/unit/__init__.py) exist; [middleware directory](../../apps/api/app/middleware/) has no initializer. Namespace imports are not proof of the named artifact. | AUD-030 |
| T004 | [X] | IMPLEMENTED | [TenantContext](../../apps/api/app/core/tenant_context.py#L6) has default live, simulation flag, prefixed scope and ContextVar get/set; [five unit tests](../../tests/unit/test_tenant_context.py#L4) assert those helpers, not request propagation. | AUD-002 |
| T005 | [X] | IMPLEMENTED | [Principal helper](../../apps/api/app/core/auth.py#L5) extracts role tuples and exposes `has_simulation_role`; [HTTP create test](../../tests/contract/test_warp_speed_api.py#L86) traverses the role check with synthetic headers. JWT/OID/trusted-header handling remains deficient. | AUD-001 |
| T006 | [X] | PARTIAL | [SimulationTenant](../../packages/domain/src/domain/models/simulation_tenant.py#L37) includes fields, regex, transitions and limits; [model contracts](../../tests/contract/test_simulation_api_contract.py#L105) test pattern/transitions. Title-Case wire values and identity/creator invariants do not match the full data contract. | AUD-006, AUD-009, AUD-024, AUD-028 |
| T007 | [X] | PARTIAL | [ScenarioRun](../../packages/domain/src/domain/models/scenario_run.py#L7) adds the requested fields, but tenant is nullable and [rehearsal construction](../../apps/api/app/services/rehearsal_orchestrator.py#L19) omits linkage. No tenant/run persistence assertion in the named tests. | AUD-009 |
| T008 | [X] | PARTIAL | [Scope helpers](../../apps/api/app/repositories/cosmos_scope.py#L4) include tenant prefixes, but signal key still accepts arbitrary scope and [actual Redis calls](../../apps/api/app/services/ingestion/dedup_service.py#L23) do not use the new helper. [Isolation test](../../tests/integration/test_tenant_isolation.py#L9) compares strings only. | AUD-002, AUD-004, AUD-007 |
| T009 | [X] | PARTIAL | [Repository](../../apps/api/app/repositories/simulation_repository.py#L62) performs CRUD/list operations but tenant/member reads are cross-partition queries, template reads live elsewhere, and initialization can switch to memory. [RBAC tests](../../tests/unit/test_simulation_participant_rbac.py#L45) use a stub, not a Cosmos point read. | AUD-004, AUD-006, AUD-008, AUD-009, AUD-031 |
| T010 | [X] | PARTIAL | [Middleware](../../apps/api/app/middleware/tenant_middleware.py#L20) sets context/header but has no full error taxonomy/telemetry and no injected repo at [startup](../../apps/api/app/main.py#L55). No full-stack identity/context assertion in original tests. | AUD-001, AUD-002, AUD-027, AUD-028 |
| T011 | [X] | PARTIAL | [RBAC helpers](../../apps/api/app/api/dependencies/rbac.py#L12) and [four stub tests](../../tests/unit/test_simulation_participant_rbac.py#L45) distinguish missing/nonmember/creator/member, but identity and endpoint coverage are incomplete. | AUD-001, AUD-006 |
| T012 | [X] | PARTIAL | [build_handoff](../../apps/agents/common/handoffs.py#L48) carries tenant; [monitoring pipeline](../../apps/agents/monitoring/pipeline.py#L289) forwards an explicit tenant. The legacy module is deprecated, [MAF](../../apps/agents/maf_runtime/workflow/builder.py#L89) defaults run ownership, and [handoff integration](../../tests/integration/test_handoff_chain.py#L5) checks a no-op subscriber only. | AUD-002, AUD-014 |
| T012b | [X] | PARTIAL | [SimulationAuditWriter](../../apps/api/app/services/simulation_audit_writer.py#L23) constructs tenant paths but uses no Blob client in [routes](../../apps/api/app/api/routes/simulations.py#L30), swallows errors and is not attached to all required actions. No original test asserts per-action durable Blob events. | AUD-019 |
| T013 | [X] | PARTIAL | [API SignalRepository](../../apps/api/app/repositories/signal_repository.py#L51) has the named methods, but explicit scope/partition and unadapted documents undermine the contract. [Four simulation isolation tests](../../tests/integration/test_tenant_isolation.py#L29) use the memory path by default. Live routes still use SIGNALS. | AUD-003, AUD-004, AUD-011, AUD-031 |
| T014 | [X] | PARTIAL | [Validators](../../apps/api/app/validators/simulation_validators.py#L11) validate sequential cap and positive settings/creator list, not runtime budgets or atomic admission. [Service tests](../../tests/unit/test_simulation_service.py#L43) cover empty participants and a sequential fourth create. | AUD-006, AUD-024, AUD-028 |
| T015 | [X] | PARTIAL | [Service](../../apps/api/app/services/simulation_service.py#L40) creates/lists/gets and transitions, but omits dependencies and canonical run association. [Create test](../../tests/unit/test_simulation_service.py#L18) checks ID prefix/status/member only, not real provisioning or 30 seconds. | AUD-008, AUD-009, AUD-024, AUD-031 |
| T016 | [X] | PARTIAL | [Create/list/detail](../../apps/api/app/api/routes/simulations.py#L83) exist, but list is unfiltered by participant and request/response conventions diverge. [Original contracts](../../tests/contract/test_simulation_api_contract.py#L15) manufacture responses; later [HTTP tests](../../tests/contract/test_warp_speed_api.py#L86) cover limited paths. | AUD-001, AUD-006, AUD-028 |
| T017 | [X] | PARTIAL | [Delivery gate](../../apps/api/app/services/public_alert_service.py#L82) blocks when ambient context is simulation; publication/ownership/audit are not secured. [Wrapper safety test](../../tests/unit/test_simulation_controller_safety.py#L77) is not a publication-route test. | AUD-005, AUD-019 |
| T018 | [X] | PARTIAL | [Client](../../apps/web/src/lib/api/simulations.ts#L108) has wrappers for all named operations; replay/participant bodies, return shapes, auth transport and report identity need alignment. Original model contracts do not assert client/server parity. | AUD-016, AUD-021, AUD-028 |
| T019 | [X] | PARTIAL | [Banner](../../apps/web/src/components/simulation-banner.tsx#L66) exists and [component tests](../../apps/web/tests/unit/spec_036/simulation-banner.test.tsx#L9) check status/accessibility. [CSS](../../apps/web/src/app/globals.css#L3949) and missing route/state rendering do not guarantee persistence. | AUD-018 |
| T020 | [X] | PARTIAL | [List page](../../apps/web/src/app/simulations/page.tsx#L7) displays core columns and create link; it lacks role gating, usable errors and pagination. [Existing E2E](../../tests/e2e/web-coverage/cross-cutting/simulation-playback.spec.ts#L15) does not assert list/create authorization. | AUD-006, AUD-016 |
| T021 | [X] | PARTIAL | [Simulation page](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L94) supplies metadata/map/chat, not full live operational components. [Live detail](../../apps/web/src/app/incidents/[incidentId]/page.tsx#L48) and [shared shell](../../packages/ui/src/components/layout/app-shell.tsx#L6) remain different. | AUD-003, AUD-014, AUD-016, AUD-017, AUD-018 |
| T022 | [X] | PARTIAL | [Template model](../../packages/domain/src/domain/models/scenario_template.py#L33) has fields/sort/positive targets; [unit assertions](../../tests/unit/test_scenario_seeding.py#L11) cover offsets and targets, but envelopes are unvalidated dicts and wire enums differ. | AUD-010, AUD-011, AUD-028 |
| T023 | [X] | PARTIAL | [Seeding/replay](../../apps/api/app/services/scenario_seeding_service.py#L30) exists but is unwired for templates, copies no organisation/framework state, and does not produce bounded remapped snapshots. [Named seeding tests](../../tests/unit/test_scenario_seeding.py#L10) never call this service. | AUD-010, AUD-011, AUD-012, AUD-031 |
| T024 | [X] | PARTIAL | [Legacy timing](../../apps/api/app/services/scenario_seeding_service.py#L114) cumulatively waits offsets and is uncalled; [new scheduler](../../apps/api/app/services/warp_scheduler.py#L188) also lacks a started loop. [Fake-clock tests](../../tests/unit/test_warp_scheduler.py#L100) manually tick delivery, not actual startup/recovery. | AUD-012, AUD-013 |
| T025 | [X] | PARTIAL | [Seed routes](../../apps/api/app/api/routes/simulations.py#L203) enforce Active and return 202, but bodies/errors differ and no real scheduled seeding is connected. Original contract tests do not call these endpoints. | AUD-010, AUD-012, AUD-013, AUD-028 |
| T026 | [X] | PARTIAL | [Participants route](../../apps/api/app/api/routes/simulations.py#L239) appends OIDs from dicts but ignores persona assignments and permits weak input/state policy. [Playback tests](../../tests/contract/test_playback_api.py#L262) exercise adding an OID, not assignment validation. | AUD-006, AUD-015, AUD-028 |
| T027 | [X] | MISSING | Full [simulation page](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L94) has no assigned-persona signal/recommendation/task filter. Existing [persona workspace service](../../apps/api/app/services/persona_workspace_service.py#L28) was checked as an alternative; it lacks simulation assignment/context. | AUD-015, AUD-016 |
| T028 | [X] | CONFLICT | Required simulation-only approvals contradict [global recommendation/approval writes](../../apps/api/app/services/recommendation_service.py#L19); escalation is not distinct. [Original lifecycle test](../../tests/integration/test_simulation_lifecycle.py#L20) never approves anything. Verification outcome is UNVERIFIED. | AUD-003, AUD-005, AUD-015, AUD-019 |
| T029 | [X] | PARTIAL | [ExerciseReport](../../packages/domain/src/domain/models/exercise_report.py#L39) exists, but participant structures and decision/alert summaries differ from [data model](data-model.md#L95). [Contract test](../../tests/contract/test_simulation_api_contract.py#L209) checks field presence on an empty model only. | AUD-020 |
| T030 | [X] | PARTIAL | [Report service](../../apps/api/app/services/exercise_report_service.py#L32) counts signals but leaves required sections/metrics/comparisons empty and omits reliable Blob persistence. No test computes known complete exercise outcomes. | AUD-020, AUD-031 |
| T031 | [X] | CONFLICT | [GET report](../../apps/api/app/api/routes/simulations.py#L259) rejects Active but creates a missing report instead of the contracted 404; repeated reads with no Blob regenerate it. Original report tests do not use HTTP. | AUD-020, AUD-022, AUD-028 |
| T032 | [X] | PARTIAL | [Report view](../../apps/web/src/app/simulations/reports/[reportId]/page.tsx#L29) has summaries but wrong lookup identity and no timeline. No inspected UI assertion establishes a real persisted report deep link. | AUD-018, AUD-020, AUD-021 |
| T033 | [X] | PARTIAL | [Governor](../../apps/api/app/services/resource_governor.py#L45) implements local bucket/mode helpers but no application write enforcement or RU/LLM telemetry. [Tests](../../tests/unit/test_resource_governor.py#L8) cover bucket booleans/mode fields, not actual protected writes. | AUD-024, AUD-025 |
| T034 | [X] | PARTIAL | [Lifecycle routes](../../apps/api/app/api/routes/simulations.py#L284) exist and [HTTP clock tests](../../tests/contract/test_warp_speed_api.py#L119) check pause/resume; delete is not admin-gated, archive is not a durable job, and newer route templates overlap. | AUD-006, AUD-013, AUD-022, AUD-028 |
| T035 | [X] | PARTIAL | [Archive service](../../apps/api/app/services/simulation_service.py#L191) performs status transitions and optional Redis cleanup only. [Lifecycle test](../../tests/integration/test_simulation_lifecycle.py#L20) directly changes statuses without exercising the workflow. | AUD-019, AUD-020, AUD-022, AUD-031 |
| T036 | [X] | PARTIAL | [Expiry helper](../../apps/api/app/services/simulation_service.py#L226) can call archive, but no schedule, idle tracking, notice or test assertion exists on the required path. [Model expiry](../../packages/domain/src/domain/models/simulation_tenant.py#L102) is creation-based. | AUD-023, AUD-028 |
| T037 | [X] | PARTIAL | [Governor](../../apps/api/app/services/resource_governor.py#L75) changes active/paused tenant fields; [tests](../../tests/unit/test_resource_governor.py#L34) assert those fields, not capacity reservation, notification, new-tenant behavior or durable mode. | AUD-025, AUD-026 |
| T037b | [X] | PARTIAL | [Incident endpoints](../../apps/api/app/api/routes/incidents.py#L20) exist but lack admin dependency and governance persistence. Original contract tests do not exercise them. | AUD-026 |
| T038 | [X] | PARTIAL | [List page](../../apps/web/src/app/simulations/page.tsx#L69) shows signal/storage and lifecycle controls, not cache-key count or throttle indicator; counts are not maintained from actual resources. | AUD-016, AUD-024, AUD-025 |
| T039 | [X] | IMPLEMENTED | [Simulation Cosmos declaration](../../infra/main.bicep#L635) has `/scenario_id` and all three named composite indexes. This is source configuration only; no Bicep build, what-if, deployment or deployed-index verification was performed. | AUD-029 for verification evidence |
| T040 | [X] | PARTIAL | [Scheduled error query](../../infra/modules/monitoring.bicep#L138) filters tenant dimensions; [middleware](../../apps/api/app/middleware/tenant_middleware.py#L20) does not emit them. No global exporter assertion accompanies the change. | AUD-027 |
| T041 | [X] | PARTIAL | All four named [context](../../tests/unit/test_tenant_context.py#L4), [service](../../tests/unit/test_simulation_service.py#L16), [governor](../../tests/unit/test_resource_governor.py#L8), [seeding](../../tests/unit/test_scenario_seeding.py#L10) files exist. Missing assertions include real provisioning, expiry, service seeding/replay, enforcement, and storage failures. | AUD-029 and owning behavioral tasks |
| T042 | [X] | PARTIAL | [Isolation](../../tests/integration/test_tenant_isolation.py#L21) checks memory repository scope; [lifecycle](../../tests/integration/test_simulation_lifecycle.py#L20) checks model transitions. Required agents, real-channel blocking, audit, Redis, FR-004 ingestion and FR-022 UI assertions are not all present. | AUD-003, AUD-004, AUD-005, AUD-007, AUD-014, AUD-017, AUD-019, AUD-022, AUD-029 |
| T043 | [X] | PARTIAL | [Original contract tests](../../tests/contract/test_simulation_api_contract.py#L15) construct dicts/models, not all endpoint requests/status/error conditions. Later [warp](../../tests/contract/test_warp_speed_api.py#L86) and [playback](../../tests/contract/test_playback_api.py#L120) tests add HTTP coverage but not the full original contract. | AUD-028, AUD-029 |
| T044 | [X] | UNVERIFIED | [Quickstart](quickstart.md#L1) is authored guidance, not a run log. Its lower-case enums, sample IDs, seeding fields, Blob container and listed test names diverge from current code. No attributable execution/monitoring result accompanies the local checked task. | AUD-028, AUD-029 |

## Requirement Coverage

All FR/NFR/SC rows below refer to this specification's identifiers, not identically numbered identifiers
from later features. Measured/security outcomes are not inferred from source, checkboxes, or test names.

### Functional Requirements

| ID | Status | Evidence and remaining obligation | Follow-up |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | [Live default](../../apps/api/app/core/tenant_context.py#L10) and sim regex exist, but [three independent IDs](../../apps/api/app/services/simulation_service.py#L62) violate run-derived tenant identity. | AUD-009 |
| FR-002 | PARTIAL | [Context helper](../../apps/api/app/core/tenant_context.py#L6), [middleware](../../apps/api/app/middleware/tenant_middleware.py#L20) and explicit monitoring tenant exist; authentication and end-to-end repository/agent/cache/audit propagation do not. | AUD-001, AUD-002, AUD-003, AUD-004, AUD-007, AUD-014, AUD-027 |
| FR-003 | PARTIAL | [Scope predicates](../../apps/api/app/repositories/signal_repository.py#L75) exist; [point read](../../apps/api/app/repositories/signal_repository.py#L61), globals and alternate stores bypass ownership. Partition keys do not restrict the shared credential's queries. | AUD-003, AUD-004, AUD-007 |
| FR-004 | PARTIAL | External [worker](../../apps/ingestion/worker.py#L208) takes no user-selected tenant, but no signal repository is injected, and [API ingestion](../../apps/api/app/api/routes/signals.py#L14) writes a tenant-blind store. No actual live-only storage assertion covers every source family. | AUD-003, AUD-007, AUD-011 |
| FR-005 | CONFLICT | [Spec clarification/default](spec.md#L23) is token-based; [middleware contract](contracts/tenant-middleware.md#L15) also selects by active membership and contains contradictory non-simulation-route language. Current resolver defaults live without a repo and ignores simulation claims. | AUD-002, AUD-028 |
| FR-006 | PARTIAL | [Create/member fields](../../apps/api/app/api/routes/simulations.py#L83) exist; OID authentication, durable membership/assignments and authorized UI actions are incomplete. | AUD-001, AUD-006, AUD-008, AUD-009, AUD-010, AUD-016 |
| FR-007 | PARTIAL | [Provisioning transition](../../apps/api/app/services/simulation_service.py#L40) exists but no mandatory cache/audit readiness; 30 seconds is UNVERIFIED. | AUD-008, AUD-031 |
| FR-008 | PARTIAL | [Pause/resume](../../apps/api/app/services/simulation_service.py#L128) preserve clock state; seeding/chat/agent/lifecycle variants are not uniformly suspended. [Clock HTTP assertions](../../tests/contract/test_warp_speed_api.py#L119) do not test agent suspension. | AUD-013 |
| FR-009 | PARTIAL | [Archive](../../apps/api/app/services/simulation_service.py#L191) marks states and attempts cache deletion, but report/audit immutability and operational cleanup are absent. | AUD-019, AUD-020, AUD-022 |
| FR-010 | PARTIAL | [Configured cap](../../apps/api/app/validators/simulation_validators.py#L11) and [sequential test](../../tests/unit/test_simulation_service.py#L55) exist; distributed atomic reservation is absent. | AUD-024 |
| FR-011 | PARTIAL | [Expiry field](../../packages/domain/src/domain/models/simulation_tenant.py#L102) and [manual helper](../../apps/api/app/services/simulation_service.py#L226) exist; idle semantics, scheduling and 24-hour notice do not. | AUD-023, AUD-028 |
| FR-012 | PARTIAL | [Four curated packs](../../packages/domain/src/domain/seed/scenario_templates_australia.json#L1) satisfy authored hazard variety; [loader/seed service](../../apps/api/app/services/scenario_seeding_service.py#L30) is disconnected and omits operational organisation/framework data. | AUD-010, AUD-011 |
| FR-013 | PARTIAL | [Replay](../../apps/api/app/services/scenario_seeding_service.py#L77) copies signals but not a bounded complete remapped incident snapshot. | AUD-012 |
| FR-014 | PARTIAL | [Scheduler helper](../../apps/api/app/services/warp_scheduler.py#L131) has fake-clock coverage; registered seeding writes early and starts no delivery loop. | AUD-013 |
| FR-015 | PARTIAL | Packs include location/confidence/freshness/provenance, but [seed conversion](../../apps/api/app/services/scenario_seeding_service.py#L30) does not produce the required live timing/source/document schema. | AUD-011, AUD-012 |
| FR-016 | PARTIAL | [Legacy monitoring](../../apps/agents/monitoring/pipeline.py#L366) and [MAF workflow](../../apps/agents/maf_runtime/workflow/builder.py#L89) exist; simulation seeding does not invoke the same complete chain. | AUD-011, AUD-014 |
| FR-017 | PARTIAL | Some handoffs/events carry tenant; [recommendation/approval stores](../../apps/api/app/services/recommendation_service.py#L19), task storage and MAF default ownership do not protect all artifacts. | AUD-003, AUD-004, AUD-014 |
| FR-018 | PARTIAL | [Approval route/service](../../apps/api/app/services/recommendation_service.py#L11) supports approve/reject only, is unscoped, and lacks complete audit/escalation/persona authorization. | AUD-003, AUD-005, AUD-015, AUD-019 |
| FR-019 | PARTIAL | [Delivery gate](../../apps/api/app/services/public_alert_service.py#L82) and [wrapper test](../../tests/unit/test_simulation_controller_safety.py#L77) exist; resource-owned blocking and durable simulated publication do not. External delivery safety outcome is UNVERIFIED. | AUD-005, AUD-019 |
| FR-020 | PARTIAL | [Simulation detail](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L94) displays tenant metadata/map/chat, not the complete live operational workflow and data. | AUD-003, AUD-014, AUD-015, AUD-016 |
| FR-021 | PARTIAL | [Banner](../../apps/web/src/components/simulation-banner.tsx#L66) is non-dismissible when rendered, but [CSS](../../apps/web/src/app/globals.css#L3949), loading/errors and playback do not ensure continuous visibility. | AUD-018 |
| FR-022 | CONFLICT | [Shared shell](../../packages/ui/src/components/layout/app-shell.tsx#L6) explicitly displays simulation navigation on live pages; [operational data paths](../../apps/api/app/api/routes/signals.py#L28) do not guarantee segregation. | AUD-003, AUD-017 |
| FR-023 | PARTIAL | [Management pages](../../apps/web/src/app/simulations/page.tsx#L7) and lifecycle routes exist, but authenticated role gating, admin deletion and complete monitoring/actions are missing. | AUD-001, AUD-006, AUD-016, AUD-022 |
| FR-024 | MISSING | [Participant update](../../apps/api/app/api/routes/simulations.py#L239) discards assignments and [workspace](../../apps/api/app/services/persona_workspace_service.py#L28) is not simulation-assignment/jurisdiction bound; no corresponding filter on the simulation page. | AUD-003, AUD-015, AUD-016 |
| FR-025 | PARTIAL | [Original writer](../../apps/api/app/services/simulation_audit_writer.py#L23) creates prefixed events; incomplete wiring, swallowed errors and absent original-container WORM violate complete immutable tenant audit. | AUD-007, AUD-019, AUD-022 |
| FR-026 | PARTIAL | [Report service](../../apps/api/app/services/exercise_report_service.py#L32) produces schema-shaped output, but most required evidence and persistence are absent. | AUD-020, AUD-021 |
| FR-027 | MISSING | [Report construction](../../apps/api/app/services/exercise_report_service.py#L49) explicitly uses an empty benchmark comparison; no target loading or previous-exercise comparison in the controlling path. Model/UI placeholders are not an implementation. | AUD-020, AUD-021 |
| FR-028 | PARTIAL | [Declare/resolve helpers](../../apps/api/app/services/resource_governor.py#L75) set fields and preserve pause state, but actual quotas/live priority/notifications are not connected. | AUD-025, AUD-026, AUD-031 |
| FR-029 | PARTIAL | [ResourceLimits](../../packages/domain/src/domain/models/simulation_tenant.py#L24) exists; validated configuration is not runtime enforcement on signals/recommendations/duration. | AUD-024 |
| FR-030 | PARTIAL | [Utilisation helper](../../apps/api/app/services/resource_governor.py#L65) checks only optional Redis memory; no active Cosmos-throughput threshold/write gate. | AUD-025, AUD-027, AUD-031 |
| FR-031 | PARTIAL | [Endpoints](../../apps/api/app/api/routes/incidents.py#L20) exist; they have no admin enforcement or durable governance incident-mode state. | AUD-001, AUD-026 |

### Non-Functional Requirements

| ID | Status | Static evidence and outcome limitation | Follow-up |
| --- | --- | --- | --- |
| NFR-001 | UNVERIFIED | [Create test](../../tests/unit/test_simulation_service.py#L18) has no timing or real provisioning assertions; missing dependencies and blocking SDK calls are static blockers to claiming 30 seconds. | AUD-008, AUD-029, AUD-031 |
| NFR-002 | UNVERIFIED | [Governor](../../apps/api/app/services/resource_governor.py#L45) is not connected to writes; no inspected test measures live latency with three active simulations against a baseline. | AUD-025, AUD-029, AUD-031 |
| NFR-003 | PARTIAL | Some failures raise errors, but [repository fallback](../../apps/api/app/repositories/simulation_repository.py#L35), [point-read swallowing](../../apps/api/app/repositories/signal_repository.py#L61) and [audit swallowing](../../apps/api/app/services/simulation_audit_writer.py#L55) contradict fail-safe error semantics. No outage behavior was executed. | AUD-002, AUD-004, AUD-008, AUD-019 |
| NFR-004 | UNVERIFIED | [10,000 default limit](../../packages/domain/src/domain/models/simulation_tenant.py#L24) and report read cap are not a 10,000-signal processing test. All packs together contain 85 entries. | AUD-010, AUD-011, AUD-024, AUD-029 |
| NFR-005 | UNVERIFIED | [Archive](../../apps/api/app/services/simulation_service.py#L191) lacks required persistence/cleanup; [lifecycle test](../../tests/integration/test_simulation_lifecycle.py#L20) has no archive timing or data volume. | AUD-022, AUD-029, AUD-031 |
| NFR-006 | PARTIAL | [Shared App Insights query](../../infra/modules/monitoring.bicep#L138) exists; [middleware](../../apps/api/app/middleware/tenant_middleware.py#L20) and [ingestion instrumentation](../../apps/ingestion/telemetry.py#L9) do not attach the required dimension globally. Exported coverage remains UNVERIFIED. | AUD-027, AUD-029 |

### Success Criteria

| ID | Status | Evidence needed versus source actually inspected | Follow-up |
| --- | --- | --- | --- |
| SC-001 | UNVERIFIED | Requires a 5,000-signal create/seed/run/archive test with no live data/audit/agent leakage. [Current isolation tests](../../tests/integration/test_tenant_isolation.py#L29) use individual memory records and omit the full workflow. | AUD-003, AUD-004, AUD-005, AUD-010, AUD-014, AUD-019, AUD-022, AUD-029 |
| SC-002 | UNVERIFIED | Requires 50,000 live signals/hour within 10% under three processing simulations. [Governor field tests](../../tests/unit/test_resource_governor.py#L34) measure no throughput; no source metric substitutes for a run. | AUD-024, AUD-025, AUD-029, AUD-031 |
| SC-003 | UNVERIFIED | Requires a complete participant flow under 10 minutes. [Simulation dashboard](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L94) lacks several required actions; [E2E playback](../../tests/e2e/web-coverage/cross-cutting/simulation-playback.spec.ts#L34) instead calls the outcome evaluator. | AUD-005, AUD-015, AUD-016, AUD-029 |
| SC-004 | UNVERIFIED | Requires every report section and generation within 60 seconds. [Empty-model contract](../../tests/contract/test_simulation_api_contract.py#L209) checks keys only; [service](../../apps/api/app/services/exercise_report_service.py#L32) returns placeholders. | AUD-020, AUD-021, AUD-029, AUD-031 |
| SC-005 | UNVERIFIED | Requires 95% actual resource reclamation in five minutes plus complete immutable audit/report. [Archive source](../../apps/api/app/services/simulation_service.py#L191) and [state-only test](../../tests/integration/test_simulation_lifecycle.py#L20) establish neither. | AUD-019, AUD-022, AUD-029 |
| SC-006 | UNVERIFIED | [CI](../../.github/workflows/ci.yml#L131) selects contract/integration directories, but the complete six-domain isolation suite is not present and no deployment results were inspected. [Egress tests](../../tests/contract/test_egress_block.py#L47) include static text checks and gated external canaries, not full original-route coverage. | AUD-003, AUD-004, AUD-005, AUD-007, AUD-014, AUD-017, AUD-019, AUD-029 |
| SC-007 | UNVERIFIED | No attributable three-persona usability study in the local review inputs. [Shared simulation navigation](../../packages/ui/src/components/layout/app-shell.tsx#L6) already contradicts the underlying UI constraint. | AUD-017, AUD-029 |

## Acceptance Scenario Coverage

`USn-ASm` labels are audit identifiers for the original story number and numbered scenario, not new specification IDs.
All 21 scenarios are enumerated; compound conditions are not satisfied by just one field or helper.

| Scenario | Status | Required result, inspected assertion/control, and gap | Follow-up |
| --- | --- | --- | --- |
| US1-AS1 | PARTIAL | Provision partition/cache/audit within 30 seconds while live ingestion continues. [Create](../../apps/api/app/services/simulation_service.py#L40) and [status test](../../tests/unit/test_simulation_service.py#L18) exist; dependencies, timing and live concurrency are not established. | AUD-001, AUD-007, AUD-008, AUD-009, AUD-029, AUD-031 |
| US1-AS2 | PARTIAL | Inject synthetic signals only into sim storage, queries/dashboard/audit. [Repository test](../../tests/integration/test_tenant_isolation.py#L29) checks a memory list; [HTTP signal route](../../apps/api/app/api/routes/signals.py#L14) is unscoped. | AUD-002, AUD-003, AUD-004, AUD-011, AUD-019 |
| US1-AS3 | CONFLICT | Live dashboard has zero sim signals/recommendations/alerts/UI. [Global data](../../apps/api/app/services/dashboard_service.py#L36) and [shared nav](../../packages/ui/src/components/layout/app-shell.tsx#L6) do not meet this; no full browser assertion. | AUD-003, AUD-017, AUD-029 |
| US1-AS4 | PARTIAL | Same chain generates simulation-owned recommendation and approval workflow. [Explicit monitoring handoff](../../apps/agents/monitoring/pipeline.py#L289) exists, but [seeding](../../apps/api/app/services/scenario_seeding_service.py#L30) stops at writes and approvals are global. | AUD-003, AUD-014, AUD-015 |
| US1-AS5 | PARTIAL | Approved simulated alert never reaches real channels and is audited as simulated. [Delivery gate](../../apps/api/app/services/public_alert_service.py#L82) returns a receipt; no ownership-backed publication/audit test. | AUD-005, AUD-019 |
| US2-AS1 | PARTIAL | QLD template seeds at least five organisations, jurisdiction/framework configuration and 20+ signals. [Pack](../../packages/domain/src/domain/seed/scenario_templates_australia.json#L1) has six/23, including current QFD naming; actual loader and operational organisation seeding are missing. No missing-pack finding is made. | AUD-010, AUD-011 |
| US2-AS2 | PARTIAL | Copy historical timeline/signals/recommendations with fresh IDs and start anywhere. [Replay](../../apps/api/app/services/scenario_seeding_service.py#L77) ignores window/graph/remapping and copies only a capped signal set. | AUD-012, AUD-013 |
| US2-AS3 | PARTIAL | Inject at original offsets in real-time mode. [Scheduler unit test](../../tests/unit/test_warp_scheduler.py#L100) manually ticks due signals; current route eagerly writes and starts no background loop. | AUD-011, AUD-013 |
| US2-AS4 | PARTIAL | Realistic seeded organisations/frameworks/timeline/initial hazards with identification. [Detail UI](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L94) shows metadata/chat/map, not the required seeded operating picture. | AUD-010, AUD-011, AUD-014, AUD-016, AUD-018 |
| US3-AS1 | MISSING | Assigned persona sees role/jurisdiction/organisation-scoped tasks/signals/recommendations. [Assignments route](../../apps/api/app/api/routes/simulations.py#L239) discards persona data; [workspace](../../apps/api/app/services/persona_workspace_service.py#L28) is not simulation-assignment bound. | AUD-001, AUD-006, AUD-015, AUD-016 |
| US3-AS2 | CONFLICT | Commander evacuation approval affects only sim and is audited. [Approval](../../apps/api/app/services/recommendation_service.py#L11) uses caller persona/global stores and no simulation audit. | AUD-003, AUD-015, AUD-019 |
| US3-AS3 | PARTIAL | Communication officer drafts/approves/publishes simulated alert without real delivery. [Controller warning](../../apps/api/app/services/simulation/controller_service.py#L940) only produces text; [publication service](../../apps/api/app/services/public_alert_service.py#L66) is not the full owned workflow. | AUD-005, AUD-015, AUD-016, AUD-019 |
| US3-AS4 | PARTIAL | Shared task updates visible within five seconds, with live unchanged. [Task service](../../apps/api/app/services/task_orchestration_service.py#L17) has organisation policy but no tenant scope; [page](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L39) polls events every eight seconds and holds objectives locally. | AUD-003, AUD-015, AUD-016, AUD-029 |
| US4-AS1 | PARTIAL | Complete structured report with all listed sections. [Service](../../apps/api/app/services/exercise_report_service.py#L32) supplies placeholders and [view](../../apps/web/src/app/simulations/reports/[reportId]/page.tsx#L29) omits timeline/wrong identity; no full-output assertion. | AUD-020, AUD-021 |
| US4-AS2 | MISSING | Side-by-side measured performance and target comparison. [Report construction](../../apps/api/app/services/exercise_report_service.py#L49) sets empty comparison/default metrics; rendering a conditional table is not computing a comparison. | AUD-020, AUD-021 |
| US4-AS3 | PARTIAL | Complete isolated signal/recommendation/approval/alert/task timeline with provenance/actor. [Playback](../../apps/api/app/services/playback_service.py#L43) authorizes reads, but [recorders](../../apps/api/app/services/simulation_event_recorder.py#L96) cover a different subset and original safety audit is incomplete. | AUD-003, AUD-019, AUD-020 |
| US4-AS4 | PARTIAL | Archive report/audit immutably and clean Cosmos/Redis. [Archive](../../apps/api/app/services/simulation_service.py#L191) does neither complete persistence nor full resource deletion; direct model transitions are not evidence. | AUD-019, AUD-020, AUD-022 |
| US5-AS1 | PARTIAL | Fourth create rejected at cap three with message and active list. [Sequential test](../../tests/unit/test_simulation_service.py#L55) asserts 409; [validator](../../apps/api/app/validators/simulation_validators.py#L11) omits active list and distributed reservation. | AUD-024, AUD-028 |
| US5-AS2 | PARTIAL | Scheduled idle-TTL archive preserves evidence and cleans all state. [Expiry helper](../../apps/api/app/services/simulation_service.py#L226) is uncalled; expiry is creation-based and archive incomplete. | AUD-022, AUD-023 |
| US5-AS3 | PARTIAL | Management shows identifier/type/time/participants/signals/storage/cache/status. [List](../../apps/web/src/app/simulations/page.tsx#L69) lacks cache count/throttle state and actual consumption measurement. | AUD-016, AUD-024, AUD-025 |
| US5-AS4 | PARTIAL | Admin archive writes report/audit/seed immutably then deletes operational partition. [Archive](../../apps/api/app/services/simulation_service.py#L191) changes states/string URI only; authorization/retention/persistence order are not complete. | AUD-006, AUD-019, AUD-020, AUD-022 |

### Edge Cases

`EC-01` through `EC-07` enumerate the seven original bullets in [Edge Cases](spec.md#L121).

| Edge | Status | Controlling evidence and missing check | Follow-up |
| --- | --- | --- | --- |
| EC-01 | PARTIAL | Real disaster during simulation: [governor](../../apps/api/app/services/resource_governor.py#L75) writes throttle fields without actual live-priority admission or participant notice. No automatic pause is introduced by that helper, but 20% capacity/state preservation was not measured. | AUD-013, AUD-025, AUD-026 |
| EC-02 | PARTIAL | Live-matching source/jurisdiction/IDs: [API memory keys](../../apps/api/app/repositories/signal_repository.py#L51) include tenant, but [domain memory storage](../../packages/domain/src/domain/repositories/signal_repository.py#L30), global artifacts and agent dedup do not. Existing tests use distinct IDs. | AUD-003, AUD-004, AUD-007 |
| EC-03 | CONFLICT | Network partition: [Cosmos fallback](../../apps/api/app/repositories/simulation_repository.py#L35), [point-read swallowing](../../apps/api/app/repositories/signal_repository.py#L61), and [Redis handling](../../apps/api/app/services/simulation_service.py#L238) acknowledge degraded/memory paths instead of required errors. No source evidence shows explicit fallback into live, but fail-safe error semantics are not met. | AUD-002, AUD-004, AUD-008, AUD-019 |
| EC-04 | PARTIAL | Forgotten exercise: [expiry helper](../../apps/api/app/services/simulation_service.py#L226) exists without schedule/notice, and incomplete archive cannot preserve evidence/reclaim state. | AUD-022, AUD-023 |
| EC-05 | UNVERIFIED | Coordinator disconnect: membership is stored independently and [playback](../../apps/api/app/services/playback_service.py#L43) does not require a coordinator session, which is positive source evidence. Participant workflow continuity under disconnect/restart was not tested and full processing is incomplete. | AUD-008, AUD-013, AUD-015, AUD-029 |
| EC-06 | PARTIAL | Active-incident replay snapshot: [shallow copy](../../apps/api/app/services/scenario_seeding_service.py#L77) retains references and ignores bounds, with no snapshot/independence assertions. | AUD-012 |
| EC-07 | PARTIAL | Large exercise/50,000-signal contention: [budget config](../../packages/domain/src/domain/models/simulation_tenant.py#L24) and [governor](../../apps/api/app/services/resource_governor.py#L45) do not enforce actual admission. Threshold behavior/live impact is not measured. | AUD-024, AUD-025, AUD-029, AUD-031 |

## Contract and Entity Reconciliation

### Endpoint Matrix

These rows cover every endpoint in the local API contract plus the two FR-031 endpoints.
General authentication/storage errors apply to every row, not only the examples listed here.

| Endpoint | Status | Expected versus observed behavior and test limitation | Follow-up |
| --- | --- | --- | --- |
| POST /api/simulations | CONFLICT | Contract uses lower-case scenario and 201 provisioning/400 empty participants. [Route/service](../../apps/api/app/api/routes/simulations.py#L83) require Title Case, auto-add creator to empty participants, return Active synchronously and do not create the linked run. Later HTTP tests intentionally use Title Case. | AUD-008, AUD-009, AUD-024, AUD-028 |
| GET /api/simulations | PARTIAL | [Route](../../apps/api/app/api/routes/simulations.py#L119) supports filters/limit/offset, caps only the upper limit and lists all tenants regardless of membership. Negative values/status case are not consistently validated. Original test checks a fabricated dict. | AUD-006, AUD-028 |
| GET /api/simulations/{tenantId} | PARTIAL | [Detail](../../apps/api/app/api/routes/simulations.py#L154) checks role and participant/creator, returning 404 if missing. OID/auth/state/error semantics remain deficient; later clock tests exercise successful HTTP detail only. | AUD-001, AUD-002, AUD-006, AUD-028 |
| POST /api/simulations/{tenantId}/pause | PARTIAL | [Original handler](../../apps/api/app/api/routes/simulations.py#L284) returns 200/409 and preserves server clock; newer UUID handler has the same URL shape and is registered later. It does not prove all processing pauses. | AUD-013, AUD-028 |
| POST /api/simulations/{tenantId}/resume | PARTIAL | [Original handler](../../apps/api/app/api/routes/simulations.py#L305) changes state/clock; no scheduler restart is connected, and raw-UUID route overlap persists. | AUD-013, AUD-028 |
| POST /api/simulations/{tenantId}/archive | CONFLICT | Contract promises 202 archiving with durable report/audit/cleanup. [Handler](../../apps/api/app/api/routes/simulations.py#L331) awaits a largely status-only workflow and returns Archived. | AUD-019, AUD-020, AUD-022, AUD-028 |
| DELETE /api/simulations/{tenantId} | PARTIAL | [Handler](../../apps/api/app/api/routes/simulations.py#L385) enforces Archived and returns 204, but lacks administrator/membership/retention checks and actual deletion. | AUD-006, AUD-022 |
| POST /api/simulations/{tenantId}/seed | CONFLICT | Contract includes replay mode and seed/organisation counts. [Body/handler](../../apps/api/app/api/routes/simulations.py#L191) accept only template ID, ignore extra replay mode, use an unwired loader and return a different shape on success. | AUD-010, AUD-011, AUD-013, AUD-028 |
| POST /api/simulations/{tenantId}/seed/replay | CONFLICT | Contract uses `start_from/end_at/replay_mode`; [body](../../apps/api/app/api/routes/simulations.py#L195) requires `start/end/time_compression`. Current service ignores bounds/compression and does no graph snapshot. | AUD-012, AUD-013, AUD-028 |
| POST /api/simulations/{tenantId}/participants | CONFLICT | Contract accepts OID strings and separate persona assignments; [handler](../../apps/api/app/api/routes/simulations.py#L235) expects dictionaries and persists only their `oid`, without full validation/authority. | AUD-006, AUD-015, AUD-028 |
| GET /api/simulations/{tenantId}/report | CONFLICT | Contract says missing report 404 and active 409; [handler](../../apps/api/app/api/routes/simulations.py#L259) does reject Active but generates missing reports on GET. Blob absence makes readback unreliable. | AUD-020, AUD-021, AUD-028 |
| POST /api/incidents/declare | PARTIAL | [Endpoint](../../apps/api/app/api/routes/incidents.py#L20) changes helper state without authenticated admin or governance persistence; no original endpoint contract assertion. | AUD-001, AUD-025, AUD-026 |
| POST /api/incidents/resolve | PARTIAL | [Endpoint](../../apps/api/app/api/routes/incidents.py#L26) restores fields without admin/durable transition or cross-replica recovery. | AUD-001, AUD-025, AUD-026 |

### Entity and Research Decisions

| Obligation | Status | Evidence assessment | Follow-up |
| --- | --- | --- | --- |
| SimulationTenant and ScenarioRun one-to-one relation | PARTIAL | Fields are authored, but [create](../../apps/api/app/services/simulation_service.py#L62) creates three identities and no linked run; model creator/required-tenant invariants are incomplete. | AUD-009 |
| ScenarioTemplate and SimulationSignal | PARTIAL | Four packs and sorted offsets exist. Real data-schema validation, timestamps, partition serialization and organization/framework materialization do not. See [model](../../packages/domain/src/domain/models/scenario_template.py#L12) and [service](../../apps/api/app/services/scenario_seeding_service.py#L30). | AUD-010, AUD-011 |
| ExerciseReport | PARTIAL | [Model](../../packages/domain/src/domain/models/exercise_report.py#L39) differs from rich participant/decision summary contract; empty fields are not measured output. | AUD-020, AUD-021 |
| R1: extended context | PARTIAL | [Value object](../../apps/api/app/core/tenant_context.py#L6) is implemented; actual transport/ownership binding is not complete. | AUD-002 |
| R2: Cosmos partition strategy | CONFLICT | [Research](research.md#L19) calls partitioning a structural guarantee and also places templates in simulation, while the [data model](data-model.md#L55) puts templates in seed. Current code uses optional predicates/account-wide access, not an unbypassable tenant boundary. | AUD-004, AUD-009, AUD-028 |
| R3: cache namespaces | PARTIAL | Helper exists, but [dedup caller](../../apps/api/app/services/ingestion/dedup_service.py#L23) remains unprefixed. | AUD-007 |
| R4: Blob prefixes and immutability | PARTIAL | Original audit path builder exists, but [raw prefixes](../../apps/ingestion/blob_store.py#L28), storage wiring and [WORM declarations](../../infra/main.bicep#L526) do not complete the decision. | AUD-007, AUD-019, AUD-022 |
| R5: authenticated participant membership | PARTIAL | [Helper](../../apps/api/app/api/dependencies/rbac.py#L18) validates members/creator for some routes; auth and consistent point-read/endpoint use remain incomplete. | AUD-001, AUD-004, AUD-006 |
| R6: live-priority throttling | PARTIAL | [Governor](../../apps/api/app/services/resource_governor.py#L45) is a disconnected local helper, not a monitored shared-resource admission path. | AUD-024, AUD-025, AUD-026 |
| R7: handoff propagation | PARTIAL | [Monitoring](../../apps/agents/monitoring/pipeline.py#L289) supports explicit scope, but automatic derivation/full-chain handling is not present. Legacy names were checked against the explicit MAF replacement. | AUD-014 |
| R8: non-bypassable publication gate | PARTIAL | [Request-context gate](../../apps/api/app/services/public_alert_service.py#L82) does not prove ownership, real-channel coverage or durable simulated publication. | AUD-005 |
| R9: reused operational dashboard and isolated live UI | CONFLICT | [Simulation page](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L94) is a separate controller surface; [live shell](../../packages/ui/src/components/layout/app-shell.tsx#L6) includes simulations. | AUD-016, AUD-017, AUD-018 |
| R10: exercise aggregation and benchmarks | PARTIAL | [Report service](../../apps/api/app/services/exercise_report_service.py#L32) counts signals and supplies placeholders rather than the promised aggregation/comparison. | AUD-020 |

### Embedded Later Statements

These are assessed as authored statements, not as evidence of the validation/sign-off they describe.

| ID | Status | Evidence and interpretation | Follow-up |
| --- | --- | --- | --- |
| ASM-015 | UNVERIFIED | [Assumption section](spec.md#L217) adopts AU-v1 and retains open gaps. [Primary region restriction](../../infra/main.bicep#L79) is source intent, not proof of the deployed operational baseline. | AUD-029 |
| ASM-016 | UNVERIFIED | [Authored consultation requirement](spec.md#L217) names security-engineer and product-owner-ba; no local attributable actor-review transcript/sign-off accompanies this spec. This audit did not invoke them. | AUD-029 |
| ASM-017 | IMPLEMENTED | [Statement](spec.md#L217) explicitly adopts the shared numbering/persona schema. This row credits the authored reference, not actual persona-schema or deployment validation. | AUD-028 for ambiguous cross-references |
| PER-013 | UNVERIFIED | [Persona section](spec.md#L225) labels AU AIIMS personas validated; no local validation record establishes that outcome or simulation assignment behavior. | AUD-015, AUD-029 |
| PER-014 | UNVERIFIED | [Persona section](spec.md#L225) references the technical actor catalogue and labels it validated; a label does not establish participation in this feature's review. | AUD-029 |
| PER-015 | IMPLEMENTED | [Explicit non-AU placeholder](spec.md#L225) and its preconditions are authored. No missing PH/JP/BD implementation finding is raised for an expressly deferred scope. | Preserve deferral |
| HYP-005 | UNVERIFIED | [Hypothesis](spec.md#L233) defines consultation and a rubric-band change with falsification/evidence-stub reference. Neither the measured change nor actual consultation is established by local inputs. | AUD-029 |
| SCP-015 | IMPLEMENTED | [Scope section](spec.md#L239) explicitly defers country variants and names promotion preconditions; this is a scope artifact only. | Preserve deferral |
| SCP-016 | IMPLEMENTED | [Scope section](spec.md#L239) preserves non-negotiable constitutional constraints rather than changing them. Compliance outcomes remain outside static proof. | AUD-029 for compliance evidence |
| SCP-017 | IMPLEMENTED | [Scope section](spec.md#L239) assigns cross-spec authority arbitration and defers specified capabilities. No unilateral redefinition is made by this report. | AUD-028 for explicit conflict decisions |
| SCP-018 | IMPLEMENTED | [Canonical enabling-infrastructure statement](spec.md#L239) and meta-scope designation are present. This does not exempt the original isolation/safety obligations. | None beyond owning findings |

## Review and Checklist Claims

### Quality Checklist: All 16 Original Checks

The [checklist](checklists/requirements.md#L1) is fully authored and checked. The checks are individually
assessed below; no row converts an authored claim into proof of testing, stakeholder review or approval.

| Original checked claim | Status | Assessment | Follow-up |
| --- | --- | --- | --- |
| No implementation details (languages/frameworks/APIs) | CONFLICT | Spec explicitly names Cosmos, Redis, Entra, Application Insights and administrative API paths. | AUD-028 |
| Focused on user value/business needs | IMPLEMENTED | Five stories explain training, safety, analysis and lifecycle value. This is document content, not stakeholder approval. | None |
| Written for non-technical stakeholders | PARTIAL | Story prose is accessible; storage keys, token claims and API details make part of it technical. | AUD-028 |
| All mandatory sections completed | IMPLEMENTED | Complete scenarios, requirements, success criteria and later metadata sections are present. | None |
| No NEEDS CLARIFICATION markers remain | IMPLEMENTED | No unresolved marker remains; substantive contract conflicts still exist. | AUD-028 |
| Requirements testable and unambiguous | CONFLICT | Token/membership selection, idle/creation TTL, inactive management access and wire enums/bodies conflict. Absolute storage isolation needs an enforceable boundary definition. | AUD-002, AUD-004, AUD-023, AUD-028 |
| Success criteria measurable | IMPLEMENTED | All seven define measurable targets; measurements were not supplied or executed. | AUD-029 |
| Success criteria technology-agnostic | IMPLEMENTED | Outcomes are primarily timing/throughput/leakage/resource/usability targets. This credits wording only. | None |
| All acceptance scenarios defined | IMPLEMENTED | All 21 numbered scenarios are present and individually mapped above. | Owning scenario findings |
| Edge cases identified | IMPLEMENTED | Seven explicit cases are present and individually mapped above. | Owning edge findings |
| Scope clearly bounded | PARTIAL | AU-v1/deferred country scope is explicit; tenant-selection and overlapping later simulation lifecycle ownership still need reconciliation. | AUD-013, AUD-028 |
| Dependencies and assumptions identified | IMPLEMENTED | Dependencies/assumptions and actor references are authored; availability/consultation is unverified. | AUD-029 |
| All functional requirements have clear acceptance criteria | PARTIAL | Core stories are covered; FR-031 was added beyond the notes' FR-030 inventory, and role/error/notification/storage details require concrete cases. | AUD-026, AUD-028, AUD-029 |
| User scenarios cover primary flows | IMPLEMENTED | Five stories cover creation, seed, participation, reports and governance. Runtime implementation is assessed separately. | None |
| Feature meets measurable outcomes in Success Criteria | UNVERIFIED | A pre-planning checklist cannot establish execution; no local measured results satisfy the seven SCs. | AUD-029 |
| No implementation details leak into specification | CONFLICT | Same contradiction as the first claim; not a second independent code defect. | AUD-028 |

Checklist notes additionally claim all items pass, cite FR-001 through FR-030 rather than the current 31 FRs,
and assert technology-free requirements. Those notes are authored assertions with the conflicts above;
the readiness claim is not an implementation acceptance or real review record.

### Plan Gates and Task Checkpoints

| Authored review/gate claim | Evidence status | Static assessment and required evidence |
| --- | --- | --- |
| Life Safety First: PASS | UNVERIFIED | [Plan gate](plan.md#L28) cites requirements, while AUD-001 through AUD-005 and AUD-025 identify missing controls. Requires implemented guards and independent safety review. |
| Multi-Agent Coordination: PASS | UNVERIFIED | A requirement citation does not show the same live/sim graph or downstream scope; AUD-014 remains open. |
| Data Trust and Provenance: PASS | UNVERIFIED | Curated provenance exists, but envelope/timestamp/live-routing gaps remain under AUD-007/AUD-011/AUD-012. |
| Privacy and Security: PASS | UNVERIFIED | Authentication, membership, storage scope and failure handling have concrete static gaps. No penetration/security outcome is certified. |
| Multilingual and Accessible: PASS | UNVERIFIED | Banner component attributes are positive source evidence; they do not establish persistent identification, accessibility regression results or operator review. |
| Azure AU Platform: PASS | UNVERIFIED | Baseline IaC intent is visible; no resource query/deployment/region-policy evidence was obtained. Current constitution has evolved beyond the plan's abbreviated principle labels. |
| Multi-tenancy boundaries: PASS | UNVERIFIED | Partition helper existence does not prove FR-003 or complete endpoint isolation. |
| Scenario-based testing: PASS | UNVERIFIED | All three required hazard pack types exist, but model/fixture tests do not execute complete exercises. |
| Drills/tabletop exercises: PASS | UNVERIFIED | Controller/map/playback artifacts exist, but full participant workflow and archive/report behavior are incomplete. |
| Pre-design gate PASS; no violations; re-check after design | UNVERIFIED | No dated independent pre/post-design sign-off is attached locally. References to requirements are design rationale only. |
| Phase 2 checkpoint: context/middleware/storage/handoff/runtime audit functional | CONFLICT | AUD-001, AUD-002, AUD-003, AUD-004, AUD-007, AUD-008, AUD-014 and AUD-019 refute treating this as implementation proof. |
| US1 checkpoint: creation/injection/dashboard/isolation/alert safety complete | CONFLICT | Source gaps in provisioning, ordinary APIs, publication and UI remain; the independent test was not executed. |
| US2 checkpoint: curated seed/replay and timing complete | CONFLICT | Loader, operational seed data, schema, snapshot and scheduler gaps remain. |
| US3 checkpoint: persona filtering and tenant approval complete | CONFLICT | Assignment persistence/filtering and scoped workflow are absent or partial. |
| US4 checkpoint: full report/gaps/benchmarks complete | CONFLICT | Report output is substantially placeholder and not reliably stored. |
| US5 checkpoint: governance/TTL/cleanup/throttle operational | CONFLICT | Status helpers do not implement scheduled notice/archive, real quotas or durable administrator control. |
| All original tasks checked, including T044 execution | UNVERIFIED | Checkboxes preserve historical assertions; source and actual test assertions are assessed in the 46-row table, and no quickstart run log was supplied. |
| Required actor consultation, operator review, PR approval, IaC what-if and quality gates | UNVERIFIED | The [constitution](../../.specify/memory/constitution.md#L280) and local actor statements require real reviews/results. None were executed or retrospectively asserted in this audit; AUD-029 tracks obtaining attributable evidence. |

## Future Validation Commands and Prerequisites

**Nothing in this section was executed.** All commands are instructions for later authorized development/test work.
Run commands from repository root unless stated otherwise. Do not point unfinished isolation tests at live data.
Before collection, prepare Python 3.12 with the API/agents and development test dependencies described in
[CI](../../.github/workflows/ci.yml#L36) and [pytest configuration](../../pyproject.toml#L28).
Use an isolated environment and injected fakes; remove production Cosmos/Blob/Redis/Foundry/telemetry endpoints
from that test process before importing modules. Do not print credentials. Existing repository constructors
can auto-connect when environment variables are present, and the existing fixtures do not comprehensively clear them.

For frontend work, use the repository's pinned pnpm dependencies, [web package](../../apps/web/package.json#L1)
and [Playwright configuration](../../apps/web/playwright.config.cts#L1), with API/agents installed and local
test-support fixtures on isolated ports. The browser configuration can reuse existing servers: verify they are
disposable local test servers, never a live session. The watermark browser file must first be placed under or
included in a configured project; passing an excluded filename on the CLI is not proof of discovery.

| Ref | Future command | Prerequisites and required assertions |
| --- | --- | --- |
| F1 | `python -m pytest tests/unit/test_tenant_context.py tests/unit/test_simulation_service.py tests/unit/test_resource_governor.py tests/unit/test_scenario_seeding.py tests/unit/test_simulation_participant_rbac.py tests/unit/test_warp_scheduler.py -q` | Add the specified fake-client/clock/identity cases first; assert real service calls, failed-stage behavior, exact scope, limits, notices and scheduling. Existing tests alone are insufficient. |
| F2 | `python -m pytest tests/integration/test_tenant_isolation.py tests/integration/test_simulation_lifecycle.py -q` | Replace state-only coverage with full tenant HTTP/service/storage wiring. Exercise all six SC-006 isolation domains plus outage, matching-ID and archive cases; require no missing/soft-skipped mandatory case. |
| F3 | `python -m pytest tests/contract/test_simulation_api_contract.py tests/contract/test_playback_api.py tests/contract/test_warp_speed_api.py tests/contract/test_signal_storage.py -q` | Expand the original API module to every endpoint/error row and both repository contracts. Positive/negative auth, participant/admin, terminal-state, schema, ownership and persistent readback assertions are mandatory. |
| F4 | `python -m pytest tests/unit/test_simulation_controller_safety.py tests/integration/test_handoff_chain.py tests/unit/test_handoff_payloads.py -q` | Add full publication adapter spies and five-agent tenant propagation. All external delivery/LLM/transport effects must be mocked; fail on any simulated real-channel call. |
| F5 | `pnpm --filter @ama/web exec vitest run tests/unit/spec_036/simulation-banner.test.tsx` | Add mandatory marker/lifecycle state cases. Component tests cannot prove viewport position or page-level persistence; retain F6/F7. |
| F6 | `pnpm --filter @ama/web exec playwright test --project=web-coverage-chromium cross-cutting/simulation-playback.spec.ts` | Expand the existing suite to actual simulation create/seed/persona/approval/report/playback and live-view isolation, replacing evaluator-cache substitution. Use strict network/data assertions and record traces/screenshots. |
| F7 | `pnpm --filter @ama/web exec playwright test --project=web-coverage-mobile cross-cutting/simulation-playback.spec.ts` | Same actual workflow on mobile, including scroll/menu/dialog/loading/error banner visibility, no live simulation affordances and collaborative updates. Add/discover the mandatory watermark accessibility cases before treating the gate as complete. |
| F8 | `bicep build infra/main.bicep --stdout` | Later only, with approved Bicep tooling and restored modules. Validate actual target-container indexes, audit/archive retention and telemetry configuration; successful compilation is not a deployed-policy/WORM test. |
| F9 | `python -m pytest tests/integration/test_simulation_lifecycle.py -k spec007_measurement -m measurement_staging -v` | **Proposed measurement tests inside this existing file**, not existing assertions. Add them under AUD-029 first; require nonzero collection and no unexpected skips. Separately approved isolated staging infrastructure, deterministic 5,000/10,000-signal packs, three active exercises, live 50,000/hour baseline, genuine RU/cache/Blob metrics, and forbidden real notifications are prerequisites. Record provisioning <=30s; live throughput/latency degradation <=10%; report <=60s; archive <=300s and >=95% reclamation; complete immutable readback. Browser/persona timing and signed three-persona usability results must accompany these machine results. No cloud action is authorized by this report. |
| F10 | `python -m pytest tests/unit/test_tenant_context.py tests/contract/test_simulation_api_contract.py --collect-only -q` | Future package/discovery check in a clean configured environment. Collection must be nonempty and import the intended modules without namespace shadowing; this is not behavioral pass evidence. |

Future end-to-end verification must also repeat the corrected quickstart with separate live/coordinator/member/
observer/admin identities; validate every error row and every acceptance/edge scenario; preserve before/after
resource counts and immutable evidence manifests; and record revision, environment, tool versions, configuration,
timestamps, selected test counts, skipped cases, observed results and reviewer identities. No future work above
is checked off by this static audit.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 007 only. Three parallel technical reviews examined storage
ownership, lifecycle/UI, and safety/governor paths. A source-completable authentication gap was fixed by adding
`/api/simulations` and `/api/incidents` to the production bearer-auth middleware protection list. Existing
tenant-scoped storage, simulation publication blocking, governor, offload, and evidence remediations were treated as
current source claims, not re-certified from prior prose.

| Area | Result | Evidence / remaining limitation |
| --- | --- | --- |
| AUD-001 / AUD-002 / AUD-003 / AUD-014 / AUD-017 / AUD-026 / AUD-031 | Current remediation is present in source, with the auth-prefix correction applied in this pass. | Focused route validation could not collect because `community_ingestion.py` imports missing `IngestionProcessingResult` from `pipeline_base.py`; no auth, browser, MAF, or incident runtime result is claimed. |
| AUD-004 | Governance-blocked. | Application-side scope checks exist, but Cosmos data-plane RBAC narrowing, inherited policy discovery, Portal parity, and deployment evidence remain open. |
| AUD-007 / AUD-019 | Governance/deployment-blocked. | Redis/Blob namespace parity and immutable/WORM audit/archive storage remain unverified; no Azure What-If, WORM, or deployed RBAC proof was created. |
| AUD-024 / AUD-025 / AUD-027 / AUD-029 | Partial/source or evidence-gated. | Governor helpers, telemetry fields, selector guards, and evidence tooling exist; capacity, live-priority, Application Insights export, CI completeness, and staging measurements remain unverified. |

No product deployment, cloud operation, browser run, live identity validation, WORM configuration, or measurement
evidence was created. The auth-prefix edit is a narrow source correction; it does not close the broader simulation
isolation or governance gates.

## Document Validation Boundary

After the report's first write, validation is limited to document task-ID/checkbox coverage, numbered requirement
and scenario coverage, local link and source-line bounds, remediation-reference integrity, trailing newline,
index preservation, and editor diagnostics for this report. Application tests, builds and cloud calls remain
prohibited in this review. Document validity is not evidence of implementation correctness or measured outcomes.
