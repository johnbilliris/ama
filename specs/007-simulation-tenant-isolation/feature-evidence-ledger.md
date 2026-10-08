# Feature Evidence Ledger - 007 Simulation Tenant Isolation

## Disposition

Status: 28 of 31 implementation findings complete.

Open governance-dependent findings:

- AUD-004: application ownership is complete; Cosmos RBAC narrowing is blocked.
- AUD-019: fail-closed append-only audit source is complete; immutable storage policy is blocked.
- AUD-022: leased archive, manifest, verified cleanup, and retained evidence are complete; immutable-storage verification and measured reclamation remain blocked.

No deployment, policy compliance, browser completion, human usability, or staging performance success is claimed.

## Implemented Source Evidence

### Authentication and Tenant Ownership (AUD-001 to AUD-009)

- Simulation and incident routes fail closed without an authenticated principal; Entra `oid` is canonical.
- Middleware, routes, and services use late-bound shared simulation composition with explicit 403, 404, 409, and 503 outcomes.
- Operational stores, coordination tasks, and signal repositories enforce tenant ownership in memory and Cosmos query/document shape.
- Simulation alert delivery records an idempotent tenant-owned synthetic receipt and unresolved outbound context is blocked.
- Participant, coordinator, observer, and administrator checks apply at list, detail, chat, history, lifecycle, participant, report, and delete boundaries.
- Ingestion namespaces and monitoring deduplication include simulation scope.
- Production/staging repositories and provisioning fail closed instead of falling back to memory or false Active state.
- One run UUID derives tenant, scenario, and run identity; tenant and run are persisted together.

### Seeding, Replay, and Workflow (AUD-010 to AUD-015)

- Curated templates are reachable and persist organisation, framework, jurisdiction, and benchmark context.
- Synthetic entries are converted to the canonical live signal envelope/domain/HPK shape.
- Replay is authorized, bounded to 10,000 signals, deep-copied, time-windowed, and remaps operational IDs.
- Seeding is schedule-only; durable timelines/cursors and lifecycle-owned workers prevent early or duplicate delivery.
- Scheduled signals enter the same `SignalAcceptedEvent` and MAF workflow seam as live ingestion with tenant-owned runs, checkpoints, and HITL metadata.
- Structured participant assignments are catalogue-validated and drive jurisdiction-scoped tasks, inbound requests, pending approvals, and workspace identity.

### User Experience and Reporting (AUD-016 to AUD-021)

- Simulation clients use the existing MSAL bearer flow, show errors, support pagination, template/replay creation, structured participants, resource/throttle state, and 5-second workspace refresh.
- Shared live views contain no simulation data or controls. Local and Azure-hosted developer navigation links to the separate simulation area; non-developer navigation and Help remain free of simulation affordances.
- A non-dismissible lifecycle-aware route marker covers simulation loading, error, playback, dashboard, and report views. The Playwright test is discoverable and fails hard on absence.
- Simulation audit uses managed-identity Blob configuration in deployed environments, deterministic append-only IDs, idempotent duplicates, and fail-closed errors across approval, publication, handoff, task, and lifecycle producers.
- Reports have deterministic IDs and derive exact decision buckets, timeline, participants, organisations, alerts, tasks, targets, prior-run deltas, and nullable metrics before publishing URI/ID.
- Report-ID lookup authorizes the resolved tenant, completed exercises link to reports, and the web report handles forbidden, missing, pending, and complete states.

### Lifecycle, Governance, and Telemetry (AUD-022 to AUD-031)

- Archive uses cross-replica leases and persisted stages: report, enumerated/checksummed seed and audit manifest, verified cleanup, then Archived. Retained evidence survives operational deletion.
- Idle expiry refreshes on accepted activity, records explicit notice recipients through a persisted notifier/outbox, handles short TTL, and uses ETag claims.
- Capacity and budgets are shared/conditional, release on failure/archive, include truthful signals, recommendations, bytes, and cache keys, and preserve live priority.
- Composite usage providers distinguish unconfigured and unavailable telemetry; process/Redis reservations preserve token state and report partial convergence.
- Incident mode is administrator-only, conditional, idempotent, late-bound, fail-safe on governance outage, and inherited by new simulations.
- Structured `tenant_id` is added to spans, logs, ingestion/scheduler/governor metrics, and explicit background scopes.
- Version 2 contracts reconcile lifecycle casing, replay/participant bodies, idle TTL, report reads, archive semantics, and counters.
- The required `spec007_isolation` CI gate has selector completeness, minimum-case, attribution, and async-offload guards.
- Middleware is an explicit Python package.
- Simulation Cosmos/Blob calls reachable from async code use bounded context-preserving offload; committed AST validation covers 17 modules.

## Automated Validation

- Exact `spec007_isolation` gate: 113 selected; 111 passed; 2 skipped because the local OpenTelemetry SDK/exporter package is unavailable.
- Broad cross-feature regression selection: 270 passed; 2 skipped for the same optional SDK dependency.
- Focused frontend spec-007 suite: 52 passed.
- Final Python validation before ledger publication: 111 passed, 2 skipped, with two upstream Starlette/AnyIO deprecation warnings.
- `check_spec007_isolation_selector.py`: PASS.
- `check_spec007_async_offload.py`: PASS; 17 modules clean.
- `check_spec007_evidence_attribution.py`: PASS.
- Reconciled simulation API Markdown and evidence files: lint/parse PASS.
- Changed source diagnostics: no errors.

## Deferred External Evidence

- Azure Portal policy-assignment parity and management-group inheritance completeness.
- Policy-cleared Cosmos RBAC and Blob immutability Bicep changes plus build/what-if evidence.
- Deployed immutable audit/archive verification.
- Authorized 10,000-signal, 50,000/hour, live-impact, latency, report-time, and reclamation measurements.
- Deployed Cosmos/Redis multi-replica contention and restart evidence.
- Real participant notification transport delivery evidence.
- OpenTelemetry SDK exporter and deployed Application Insights query evidence.
- Browser execution for marker overlap, desktop/mobile deep links, live/simulation boundary, and accessibility.
- Three-persona usability and actor consultation evidence.
- Direct MAF runtime execution is locally dependency-blocked because `agent_framework` is unavailable.

## Governance Gate

See `04-governance-constraints.md` and `04-governance-constraints.json`.

Authenticated scoped and subscription-wide Azure Policy queries returned zero assignments, but inherited-policy completeness and Portal parity are UNVERIFIED. No Bicep edits were made.
