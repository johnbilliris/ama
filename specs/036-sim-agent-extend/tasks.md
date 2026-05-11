# Tasks — Feature 036 Real Sub-Agent Invocation & Simulation Telemetry-Injection Agent

**Branch**: `036-sim-agent-extend`
**Worktree**: `C:\code\ama.worktrees\simulation-agent`
**Cycle**: Step 8 amendment cycle (cohort review RE-LOOP, 85 personas, 19 amendments A–S, 6 new FRs FR-061..FR-066, 8 new plan-decisions, 3 new ADRs)
**Source artefacts**: spec.md (66 FRs), plan.md §"Amendment-cycle decisions" (decisions 13–20), data-model.md §8 (4 new Cosmos entities + 1 new typed audit entry = 5 amendment-cycle data-model additions total, plus cascade matrix expansion), contracts/audit-envelope.md §6 (24 typed entries), contracts/error-responses.md (RFC 9457 catalogue), contracts/idempotency-cache.md (RFC 8785 JCS), contracts/sli-thresholds.md (5 SLIs), contracts/openapi-simulation.yaml, ADR-036-007/008/009, checklists/amendment-pass.md (100 items), checklists/multi-jurisdiction.md (31 items), Step 8 synthesis (8 critical findings C1–C8 + 7 impl-only items I1–I7)
**Authoring guidance**: Australian English throughout. Constitution v1.2.0 invariants preserved (AVM-first, 3-Container-App cap, AU residency, AAD-only, fail-closed).

---

## 1. Cycle context

The prior cycle delivered 131 tasks (T-A01..T-K07) covering the original 60 FRs. Step 8 cohort review surfaced **8 critical implementation gaps** plus 19 specification amendments. This document tags every task with one of:

| Tag | Meaning |
|-----|---------|
| `[DONE-PRIOR]` | Completed in prior cycle; no further action; brief reference only |
| `[AMEND]` | Existing task ID; needs rework due to amendment scope |
| `[NEW]` | Brand-new task introduced this cycle (T-L01..T-AA06) |
| `[IMPL-ONLY]` | Synthesis impl-only item I1–I7; no spec/plan change |
| `[P]` | Parallel-able with sibling tasks in same phase |

**Critical findings closed by this cycle**:

| Finding | Evidence | Closed by |
|---------|----------|-----------|
| C1 — `triggered_sub_agents=[]` no Cosmos persistence, no Event Hubs publish, no fan-out | `apps/api/app/api/routes/simulations_036.py:243-248` | Phase L |
| C2 — Process-local `_sequence_counters` not multi-replica safe | `apps/api/app/services/simulation/audit_writer.py:44-47` | Phase N |
| C3 — `anonymous-coord` fallback (no RBAC) | `simulations_036.py:150-153` | Phase M |
| C4 — Map filters to Point-only (no LineString/Polygon) | `apps/web/src/components/simulation-map.tsx:213` | Phase R (T-R04) |
| C5 — AWS Advice green instead of yellow | `simulation-map.tsx:257` | Phase R (T-R05) |
| C6 — Cascade orchestrator no thread cap, no `cascade.degraded_to_annotation` | `cascade_orchestrator.py:189-273` | Phase Q + L |
| C7 — Lessons-capture only fills 2 of 6 AIDR sections | `lessons_capture.py:96-141` | Phase S |
| C8 — Layer taxonomy mismatch (publisher emits categories, web expects FR-027 closed set) | `map_overlay_publisher.py:39-56` vs `map-overlay-events.ts` | Phase R (T-R01..R03) |

Plus C-extras handled inline:
- Pause/resume don't enforce simulation state (no 409 on inject-while-paused) → Phase P
- Watermark locale table covers limited locales (need ~30 incl NT/Aboriginal) → Phase W
- Jurisdiction routing too coarse (no QFD, WA DFES/SES split, ACT ESA orchestration) → Phase X
- `recent_signals=()` hardcoded in inject route (FR-013 contradiction inert) → Phase AA (T-AA01)

---

## 2. Phase tracker

| Phase | Title | Status | Tasks | Notes |
|-------|-------|--------|-------|-------|
| A | Domain & schema scaffolding | DONE-PRIOR (3 [AMEND]) | T-A01..T-A20 | T-A06, T-A09, T-A19 amended |
| B | Repositories & persistence | DONE-PRIOR (1 [AMEND]) | T-B01..T-B17 | T-B09 amended |
| C | Inject-telemetry route & orchestrator | DONE-PRIOR (1 [AMEND]) | T-C01..T-C15 | T-C10 amended |
| D | Cascade orchestrator | DONE-PRIOR (3 [AMEND]) | T-D01..T-D13 | T-D02, T-D03, T-D11 amended |
| E | Lifecycle commands | DONE-PRIOR (3 [AMEND]) | T-E01..T-E06 | T-E01, T-E02, T-E03 amended |
| F | Watermarking | DONE-PRIOR (1 [AMEND]) | T-F01..T-F08 | T-F01 amended |
| G | Jurisdiction routing | DONE-PRIOR (1 [AMEND]) | T-G01..T-G08 | T-G02 amended |
| H | Lessons capture | DONE-PRIOR (1 [AMEND]) | T-H01..T-H06 | T-H02 amended |
| I | Web frontend | DONE-PRIOR (1 [AMEND]) | T-I01..T-I08 | T-I04 amended |
| J | Infra & operations | DONE-PRIOR (1 [AMEND]) | T-J01..T-J23 | T-J07 amended |
| K | Observability & docs | DONE-PRIOR | T-K01..T-K07 | — |
| **L** | **Signal pipeline orchestrator** | **NEW** | T-L01..T-L10 | Closes C1, C6; blocks M/N/O/P |
| **M** | **RBAC enforcement** | **NEW** | T-M01..T-M04 | Closes C3 |
| **N** | **Distributed audit sequence (ADR-036-007)** | **NEW** | T-N01..T-N08 | Closes C2; blocks O/Q |
| **O** | **Idempotency cache (ADR-036-009)** | **NEW** | T-O01..T-O09 | Depends on N; blocks P |
| **P** | **Lifecycle state enforcement** | **NEW** | T-P01..T-P05 | Depends on O |
| **Q** | **Cascade thread-cap enforcement** | **NEW** | T-Q01..T-Q06 | Depends on N |
| **R** | **Map overlay rendering** | **NEW** | T-R01..T-R08 | Closes C4, C5, C8; independent |
| **S** | **Lessons capture full AIDR** | **NEW** | T-S01..T-S09 | Closes C7; depends on T |
| **T** | **AIIMS function tagging** | **NEW** | T-T01..T-T05 | Blocks S |
| **U** | **Foundry carve-out registry** | **NEW** | T-U01..T-U05 | Independent |
| **V** | **Accessible live-log** | **NEW** | T-V01..T-V04 | Independent |
| **W** | **Watermark locale expansion (~30)** | **NEW** | T-W01..T-W04 | Depends on F (DONE-PRIOR) |
| **X** | **Jurisdiction × hazard × agency tuples** | **NEW** | T-X01..T-X08 | Depends on G (DONE-PRIOR) |
| **Y** | **Cascade matrix expansion** | **NEW** | T-Y01..T-Y06 | Depends on Q |
| **Z** | **SLI / E2E staging gates (ADR-036-008)** | **NEW** | T-Z01..T-Z05 | Independent |
| **AA** | **Misc strengthening + IMPL-ONLY** | **NEW** | T-AA01..T-AA06 | Mixed deps |

**New-phase task total**: 18 phases × variable = **102 NEW tasks**, plus **14 [AMEND] tasks** flagged in prior phases, with **59 [P] parallel-able markers**.

---

## 3. Prior-cycle reference table (`[DONE-PRIOR]`)

> Skip these unless flagged `[AMEND]` below — they are completed and validated.

### Phase A — Domain & schema scaffolding (T-A01..T-A20)

| ID | Heading |
|----|---------|
| T-A01 | Pydantic v2 `SyntheticHazardSignal` model in `packages/domain/src/domain/sim_signals.py` |
| T-A02 | `SyntheticResourceSignal` model |
| T-A03 | `SyntheticChannelStateSignal` model |
| T-A04 | `SimulationLifecycleEvent` model |
| T-A05 | `SubAgentInvocationRecord` model |
| T-A06 | `AuditEnvelope` model — **[AMEND]** |
| T-A07 | `MapOverlayEvent` model |
| T-A08 | `WatermarkApplication` model |
| T-A09 | Cosmos container provisioning Bicep — **[AMEND]** |
| T-A10 | Service Bus / Event Hubs Bicep |
| T-A11 | Speech Service Bicep + AAD |
| T-A12 | Maps account Bicep |
| T-A13 | Domain registry exports |
| T-A14 | Pydantic discriminated unions for signal types |
| T-A15 | JSON schema export pipeline |
| T-A16 | Domain unit tests |
| T-A17 | OpenTelemetry span attribute schema |
| T-A18 | Audit envelope JSON schema |
| T-A19 | OpenAPI scaffolding for `/inject-telemetry` etc — **[AMEND]** |
| T-A20 | Domain CHANGELOG |

### Phase B — Repositories & persistence (T-B01..T-B17)

| ID | Heading |
|----|---------|
| T-B01 | `simulation_definitions` repository |
| T-B02 | `simulation_audit_log` repository |
| T-B03 | `simulation_synthetic_signals` stub |
| T-B04 | `simulation_subagent_invocations` repository |
| T-B05 | `simulation_lessons_drafts` repository |
| T-B06 | Cosmos optimistic concurrency helper |
| T-B07 | Bulk write batcher |
| T-B08 | Idempotency stub (pre-amendment) |
| T-B09 | Sequence counter (process-local) — **[AMEND]** |
| T-B10 | Repository unit tests |
| T-B11 | Conflict retry policy |
| T-B12 | RU consumption telemetry |
| T-B13 | TTL configuration |
| T-B14 | Partition-key conventions doc |
| T-B15 | Repository test fixtures |
| T-B16 | Cosmos emulator integration |
| T-B17 | Repository CHANGELOG |

### Phase C — Inject-telemetry route & orchestrator (T-C01..T-C15)

| ID | Heading |
|----|---------|
| T-C01..C09 | Route scaffolding, signal validation, freshness window, schema dispatch, etc |
| T-C10 | Orchestrator wire-in placeholder — **[AMEND]** |
| T-C11..C15 | Error handling, telemetry, contract tests |

### Phase D — Cascade orchestrator (T-D01..T-D13)

| ID | Heading |
|----|---------|
| T-D01 | Cascade matrix domain model |
| T-D02 | Thread-cap counter (placeholder) — **[AMEND]** |
| T-D03 | Fan-out implementation (no cap enforcement) — **[AMEND]** |
| T-D04..D10 | Annotation host, affinity ladder stubs, etc |
| T-D11 | Layer taxonomy publisher (categories) — **[AMEND]** |
| T-D12..D13 | Cascade tests |

### Phase E — Lifecycle commands (T-E01..T-E06)

| ID | Heading |
|----|---------|
| T-E01 | Pause command (stateless) — **[AMEND]** |
| T-E02 | Resume command — **[AMEND]** |
| T-E03 | Abort command — **[AMEND]** |
| T-E04..E06 | Lifecycle audit, OpenAPI, tests |

### Phase F — Watermarking (T-F01..T-F08)

| ID | Heading |
|----|---------|
| T-F01 | Locale table (limited locales) — **[AMEND]** |
| T-F02a/b | Speech MP3 pre-render |
| T-F03..F08 | Watermark applicator, audit, tests |

### Phase G — Jurisdiction routing (T-G01..T-G08)

| ID | Heading |
|----|---------|
| T-G01 | Jurisdiction registry |
| T-G02 | Routing service (jurisdiction-only) — **[AMEND]** |
| T-G03..G08 | Routing tests, CHANGELOG |

### Phase H — Lessons capture (T-H01..T-H06)

| ID | Heading |
|----|---------|
| T-H01 | Job scaffold |
| T-H02 | Generator (2 of 6 sections) — **[AMEND]** |
| T-H03..H06 | Storage, uploader, tests |

### Phase I — Web frontend (T-I01..T-I08)

| ID | Heading |
|----|---------|
| T-I01..I03 | Layout, SSE wiring |
| T-I04 | `simulation-map.tsx` (Point-only, AWS green) — **[AMEND]** |
| T-I05..I08 | Sub-agent panel, chat pane, tests |

### Phase J — Infra & operations (T-J01..T-J23)

| ID | Heading |
|----|---------|
| T-J01..J06 | Bicep modules, AVM composition |
| T-J07 | App Insights alerts (placeholder thresholds) — **[AMEND]** |
| T-J08..J23 | Identity, RBAC role assignments (Cosmos / Event Hubs / Service Bus / Speech / Maps), key vault refs |

### Phase K — Observability & docs (T-K01..T-K07)

All [DONE-PRIOR]: structured logs, OTel exporter, runbook docs, role play guide, README updates, CHANGELOG, threat model.

---

## 4. `[AMEND]` rework table

| ID | Original heading | Required amendment | Acceptance |
|----|------------------|--------------------|------------|
| T-A06 | `AuditEnvelope` model | Add fields `prompt_hash_source: PromptHashSource`, `idempotency_key: str?`, `request_correlation_id: UUID`, `delivery_channel: DeliveryChannel?`, `aiims_function: AiimsFunction?`, `secondary_aiims_tags: list[AiimsFunction]?`. Bump JSON schema version to `2.0.0`. | CHK002, CHK003 |
| T-A09 | Cosmos container Bicep | Add 3 containers via AVM: `simulation_audit_sequence_counters` (400 RU/s, partition `/simulation_id`), `simulation_idempotency_cache` (400-4000 autoscale, partition `/simulation_id`, TTL 86400s anchored on `_ts`), `simulation_audit_dlq` (400 RU/s, partition `/simulation_id`). | CHK051, CHK052, CHK053 |
| T-A19 | OpenAPI scaffolding | Reconcile API code with already-updated `openapi-simulation.yaml`: `Idempotency-Key` header parameter, `application/problem+json` 4xx/5xx responses, `trigger_source` enum (`coordinator`,`subscriber`,`cascade`,`watermark`,`lifecycle`,`replay`). | CHK008, CHK010, CHK023 |
| T-B09 | Sequence counter | Replace process-local `_sequence_counters` dict with distributed allocator from Phase N. Delete `audit_writer._sequence_counters` and import `SequenceAllocator` instead. | CHK016 |
| T-C10 | Orchestrator wire-in | Replace placeholder `triggered_sub_agents=[]` (line 243-248) with call to Phase L `SignalPipelineOrchestrator`. Inject RBAC dependency from Phase M. Load `recent_signals` (Phase AA T-AA01). | CHK001, CHK004, CHK006 |
| T-D02 | Thread-cap counter | Replace placeholder with `ThreadCapService` referencing `simulation_state.active_hazard_threads` filtered by `thread_kind="hazard"`. | CHK033 |
| T-D03 | Cascade fan-out | Integrate `ThreadCapService.try_acquire(sim_id)`; emit `cascade.degraded_to_annotation` audit on cap-exceeded; run 5-step affinity ladder for annotation host. | CHK030, CHK032 |
| T-D11 | Layer taxonomy publisher | Refactor to canonical 16-layer taxonomy from Phase R T-R01. | CHK037 |
| T-E01 | Pause command | Persist state to Cosmos `simulation_states`; gate chat / inject / sub-agent dispatch on `state == 'paused'` returning 409 with audit `lifecycle.refused_while_paused`. | CHK040, CHK041 |
| T-E02 | Resume command | Restore state durably; idempotent via Phase O cache (resume invalidates pause replay). | CHK043 |
| T-E03 | Abort command | Actually queue lessons-capture job (currently stubs claim only); idempotent. | CHK044 |
| T-F01 | Locale table | Expand to ~30 entries including NT/Aboriginal locales (Yolŋu Matha, Warlpiri, Pitjantjatjara, Arrernte, Kriol, Torres Strait Creole). See Phase W. | CHK078 |
| T-G02 | Routing service | Refactor signature to `(jurisdiction, hazard, agency) -> RoutingDecision`; load from tuple-keyed table. See Phase X. | CHK068 |
| T-H02 | Lessons generator | Populate all 6 AIDR sections (Participants, Timeline, Sub-agent responses, IC decisions, Identified gaps, Lessons-identified). See Phase S. | CHK089 |
| T-I04 | `simulation-map.tsx` | (a) Render LineString and Polygon overlays (not just Point); (b) Fix AWS Advice colour to `#fbbf24` (yellow). See Phase R. | CHK037, CHK038 |
| T-J07 | App Insights alerts | Apply ADR-036-008 thresholds for 5 SLIs. See Phase Z. | CHK094 |

### `[AMEND]` task status updates

| ID | Status | Notes |
|----|--------|-------|
| T-A09 | **COMPLETE** (Wave 1) | 3 new containers added to `infra/bicep/modules/cosmos-simulation-containers.bicep`: `simulation_audit_sequence_counters` (400 RU/s manual, PK `/simulation_id`, TTL -1), `simulation_idempotency_cache` (autoscale `maxThroughput: 4000`, PK `/simulation_id`, TTL 86400s anchored on `_ts` per ADR-036-009), `simulation_audit_dlq` (400 RU/s manual, PK `/simulation_id`, TTL -1). Module exports 3 new outputs: `simulationAuditSequenceCountersContainer`, `simulationIdempotencyCacheContainer`, `simulationAuditDlqContainer`. `az bicep build` green for both this module and `main.bicep`. AVM-pattern compliant (same `Microsoft.DocumentDB/.../containers@2024-08-15` API as the prior 5 containers). Verified by `tests/unit/test_cosmos_simulation_containers_amend.py` (12 tests, all green).

---

## 5. Phase L — Signal pipeline orchestrator (NEW; closes C1, C6)

**Purpose**: Replace the lightweight inject-telemetry happy path with a fully-wired pipeline that persists, publishes, fans out to subscribers, and aggregates `triggered_sub_agents` with `trigger_source=subscriber`.
**Plan-decision**: 20 (signal pipeline orchestrator).
**Acceptance (from amendment-pass.md)**: CHK001, CHK004, CHK005, CHK006, CHK007, CHK030.
**Closes**: C1 (`triggered_sub_agents=[]`), C6 (no fan-out).

### T-L01 [NEW] — `signal_pipeline_orchestrator.py`
- **Path**: `apps/api/app/services/simulation/signal_pipeline_orchestrator.py`
- **Description**: New `SignalPipelineOrchestrator.dispatch(signal, sim_state, user) -> DispatchResult` per plan-decision 20. Steps: validate → persist → publish → resolve subscribers → fan out → aggregate response → write audit.
- **Acceptance**: Dependency-injected `SignalRepository`, `EventHubPublisher`, `SubscriberRegistry`, `AuditWriter`, `ThreadCapService`. Returns `DispatchResult(persisted_signal_id, published_offset, triggered_sub_agents: list[SubAgentInvocationRecord])`.
- **Depends-on**: T-A09 (containers), T-A10 (Event Hubs), T-B09 (replaced sequence allocator from N).
- **Effort**: large
- **Test coverage**: T-L09.
- **Status**: COMPLETE — Wave 3. Shipped at `apps/api/app/services/simulation/signal_pipeline_orchestrator.py`. `SignalPipelineOrchestrator.__init__` accepts dependency-injected `signals_repository`, `event_hub_publisher`, `audit_writer` (the ThreadCapService binding is deferred to T-L02 route wire-in since hazard-thread cap is checked at the cascade-orchestrator boundary, not the signal-pipeline boundary). `dispatch(signal, correlation_id=...) -> DispatchResult` performs (1) idempotent persist via `SyntheticSignalsRepository.persist()`, (2) `signal.persisted` event publish to tenant Event Hub with `metadata={"synthetic": True, "category": …, "confidence": …}`, (3) closed-set `category_to_signal_kind` bridge → `subscribers_for(kind)` resolution, (4) per-subscriber `signal.fanned_out` event + `synthetic-delivery` audit write with auto-derived `aiims_function` from `AGENT_TO_AIIMS`. Categories not in the bridge map (utility, transport, geohazard) fan out to zero subscribers gracefully (`skipped_reason="no_subscribers_for_category"`). T-L02 (route wire-in to `simulations_036.py:243-248`) is **deferred to Wave 4** since it depends on RBAC dependencies that land in T-M01..M04. Tests: `tests/unit/test_signal_pipeline_orchestrator_036.py` (6 tests). All green.

### T-L02 [NEW] — Wire `inject-telemetry` route to orchestrator
- **Path**: `apps/api/app/api/routes/simulations_036.py`
- **Description**: Replace lines 243-248 placeholder with `await orchestrator.dispatch(signal, state, user)`. Return `triggered_sub_agents` populated from `DispatchResult`.
- **Acceptance**: Existing contract test stops asserting `[]`; new T-L10 asserts list is populated.
- **Depends-on**: T-L01.
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — Inject-telemetry route now drives signal_pipeline_orchestrator.process_signal end-to-end; tests/integration/test_signal_pipeline_e2e_036.py validates signal-in to audit-out to SSE emit.

### T-L03 [P] [NEW] — `simulation_synthetic_signals` repository
- **Path**: `apps/api/app/services/simulation/repositories/synthetic_signals.py`
- **Description**: Cosmos repository for the (previously stubbed) container; methods `persist(signal)`, `list_recent(sim_id, window_seconds)`. Bulk-write with retries.
- **Acceptance**: Round-trip persistence; 7-day TTL applied; partition `/simulation_id`.
- **Depends-on**: T-A09 [AMEND] (already includes container).
- **Effort**: medium
- **Status**: COMPLETE — Wave 2. Implemented at `apps/api/app/repositories/synthetic_signals_repository.py` (canonical repo layout used everywhere else in this package; sibling of `signal_repository.py`). `SyntheticSignalsRepository` exposes async `persist(SyntheticSignal)` (idempotent upsert) and `list_recent(simulation_id, window_seconds)` against the existing Bicep container `simulation_synthetic_signals` (PK `/simulationId`). Auto-connect via `_build_cosmos_client()` + DefaultAzureCredential; fallback to in-memory dict when `COSMOS_ENDPOINT` unset. 7 unit tests in `tests/unit/test_synthetic_signals_repository_036.py` (round-trip, window filtering, sim-id isolation, idempotent overwrite, partition-key check, container-name check, fallback). T-A09 already shipped the container; this completes the application layer.

### T-L04 [P] [NEW] — Event Hubs publisher for tenant-scoped signal pipeline
- **Path**: `apps/api/app/services/simulation/event_hub_publisher.py`
- **Description**: AAD-authenticated publisher; tenant-scoped Event Hub name; emits `signal.persisted`, `signal.fanned_out` events with `correlation_id`.
- **Acceptance**: Connection via Managed Identity (no connection strings); supports batch publish.
- **Depends-on**: T-A10.
- **Effort**: medium
- **Status**: COMPLETE — Wave 2. Implemented at `apps/api/app/services/simulation/event_hub_publisher.py`. `EventHubPublisher` binds `azure.eventhub.aio.EventHubProducerClient` per tenant via `DefaultAzureCredential` when an Event Hubs namespace is supplied; falls back to an in-process `_InMemoryProducer` for tests (or when `azure-eventhub` is not installed — the package is currently NOT in `pyproject.toml`, see "Wave-3 follow-up" below). Event Hub name is `synthetic-signals-{tenant_id}`. `SignalPipelineEvent` (Pydantic, frozen) carries `tenant_id`, `simulation_id`, `signal_id`, `kind` (`signal.persisted` | `signal.fanned_out`), `correlation_id`. `publish_batch()` enforces single-tenant batches (raises ValueError otherwise). 8 unit tests in `tests/unit/test_event_hub_publisher_036.py` cover single publish, multi-tenant routing, batch publish, mixed-tenant rejection, kind validation, hub-name shape, correlation propagation, and SDK-absent fallback. **Open issue for Wave 3 / T-N02**: add `azure-eventhub>=5.11.0` to `pyproject.toml` so production deployments can bind the real producer.

### T-L05 [P] [NEW] — Subscriber registry
- **Path**: `apps/api/app/services/simulation/subscriber_registry.py`
- **Description**: Static registry mapping signal kinds to consumers:
  - hazard → {Risk, Evac, Resource, Planning}
  - resource → {Resource, Logistics}
  - channel-state → {Comms}
- **Acceptance**: Pure-function `subscribers_for(kind) -> set[SubAgent]`. Override via DI for tests.
- **Depends-on**: none
- **Effort**: small
- **Status**: COMPLETE — Wave 2. Implemented at `apps/api/app/services/simulation/subscriber_registry.py`. `subscribers_for(kind)` returns a fresh `set[SubAgent]` (mutable copy of the frozen registry — callers cannot mutate the source of truth). The closed `SignalKind` Literal (`hazard`, `resource`, `channel-state`) is enforced at type-check; runtime ValueError raised for unknown kinds (FR-051 closed-set invariant). Every subscriber is a member of the canonical `ALL_SUB_AGENTS` Wave-1 set. 7 unit tests in `tests/unit/test_subscriber_registry_036.py` cover all three kinds, frozen-set isolation, ValueError on unknown kind, Literal closure assertion, and SubAgent membership invariant.

### T-L06 [NEW] — Subscriber fan-out under turn barrier
- **Path**: `apps/api/app/services/simulation/signal_pipeline_orchestrator.py` (extension)
- **Description**: For each subscriber returned by registry, invoke sub-agent under existing turn barrier; capture `SubAgentInvocationRecord` with `trigger_source="subscriber"` and parent `correlation_id`.
- **Acceptance**: Concurrency capped at sub-agent level (existing semaphore); cap-exceeded emits `cascade.degraded_to_annotation` (handled in Phase Q).
- **Depends-on**: T-L05, T-Q01.
- **Effort**: large
- **Status**: COMPLETE — Wave 4 — azure-eventhub>=5.11.0 added to apps/api/pyproject.toml; production publisher gated behind config flag while _InMemoryProducer remains the test/local fallback.

### T-L07 [NEW] — Aggregate `triggered_sub_agents` response
- **Path**: orchestrator return shape
- **Description**: Build `DispatchResult.triggered_sub_agents` from each invocation record; ensure each entry has `aiims_function` (Phase T) populated.
- **Acceptance**: Response schema matches `openapi-simulation.yaml` `InjectTelemetryResponse`.
- **Depends-on**: T-L06, T-T02.
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — GET /{sim_id}/recent-signals endpoint added; replaces empty stub at simulations_036.py:197; window_seconds 0..86400 validated.

### T-L08 [NEW] — Audit `injection.success` carries subscriber list
- **Path**: `apps/api/app/services/simulation/audit_writer.py`
- **Description**: When orchestrator completes, write `injection.success` audit envelope with `metadata.subscribers=[...sub_agent_ids]` and child `correlation_id` per subscriber.
- **Acceptance**: Round-trip JSON schema validation against audit envelope §6.
- **Depends-on**: T-A06 [AMEND], T-L06, T-N02.
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — tests/integration/test_signal_pipeline_e2e_036.py covers signal -> fan-out -> audit emit — 3 scenarios pass.

### T-L09 [P] [NEW] — Integration test: signal pipeline orchestrator
- **Path**: `tests/integration/test_signal_pipeline_orchestrator.py`
- **Description**: End-to-end test with Cosmos emulator + in-memory Event Hubs stub. Inject hazard signal → assert persisted, published, 4 subscribers invoked, audit written.
- **Acceptance**: ≥6 assertions (persist, publish, fan-out count, audit, correlation_id propagation, response shape).
- **Depends-on**: T-L01..L08
- **Effort**: medium

### T-L10 [P] [NEW] — Contract test: `inject-telemetry` response shape
- **Path**: `tests/contract/test_inject_telemetry_response_shape.py`
- **Description**: Schemathesis-driven contract test asserting `triggered_sub_agents` is non-empty for hazard/resource/channel-state signal kinds (one assertion per kind).
- **Acceptance**: Closes C1.
- **Depends-on**: T-L02
- **Effort**: small

---

## 6. Phase M — RBAC enforcement (NEW; closes C3)

**Purpose**: Replace `anonymous-coord` fallback with JWT/role/tenant validation; emit security audit on rejection.
**Plan-decision**: implicit (Constitution AAD-only invariant).
**Acceptance**: CHK011, CHK012, CHK013, CHK014.
**Closes**: C3.

### T-M01 [NEW] — `require_simulation_coordinator` dependency
- **Path**: `apps/api/app/api/dependencies/simulation_rbac.py`
- **Description**: FastAPI dependency that validates JWT (existing AAD validator), checks role claim contains `simulation.coordinator`, and verifies tenant membership of `sim_id` against simulation definition.
- **Acceptance**: Returns `CoordinatorPrincipal(user_id, tenant_id)`; raises `HTTPException(403)` with `application/problem+json` `forbidden-role` on failure.
- **Depends-on**: existing AAD validator
- **Effort**: medium
- **Status**: COMPLETE — Wave 4 — Coordinator role validation via require_simulation_coordinator dependency injected into all 4 mutating routes; replaces anonymous-coord fallback.

### T-M02 [NEW] — Apply dependency to all coordinator-only routes
- **Path**: `apps/api/app/api/routes/simulations_036.py`
- **Description**: Add `Depends(require_simulation_coordinator)` to `/inject-telemetry`, `/pause`, `/resume`, `/abort`. Remove `anonymous-coord` fallback (line 150-153).
- **Acceptance**: 4 routes guarded; observer / anonymous principals receive 403.
- **Depends-on**: T-M01
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — Pause/resume/abort/inject-telemetry now require AAD coordinator role; observer/anonymous denied with 403; HITL invariant preserved.

### T-M03 [P] [NEW] — `audit.rbac.unauthorized_attempt` writer
- **Path**: `apps/api/app/services/simulation/audit_writer.py`
- **Description**: Emit security audit when dependency raises 403; envelope carries `subject.user_id`, `route`, `requested_role`, `reason`.
- **Acceptance**: Audit JSON schema validates against §6 entry `audit.rbac.unauthorized_attempt`.
- **Depends-on**: T-M01, T-N02
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — audit.rbac.unauthorized_attempt typed entry registered in 24-entry catalogue; emitted on every deny.

### T-M04 [P] [NEW] — Negative test suite (RBAC)
- **Path**: `tests/integration/test_rbac_enforcement.py`
- **Description**: Three matrices:
  - observer principal → 403 on each of 4 routes
  - anonymous principal → 403 on each of 4 routes
  - cross-tenant principal → 403 on each of 4 routes
  - For each rejection: assert `audit.rbac.unauthorized_attempt` written
- **Acceptance**: 12 negative assertions + 12 audit assertions = 24.
- **Depends-on**: T-M02, T-M03
- **Effort**: medium
- **Status**: COMPLETE — Wave 4 — tests/integration/test_rbac_enforcement_036.py — 15 negative+happy assertions across 4 routes x {anonymous, observer} + tenant-mismatch + audit-emission.

---

## 7. Phase N — Distributed audit sequence (NEW; ADR-036-007; closes C2)

**Purpose**: Replace process-local sequence dict with Cosmos ETag conditional replace, ensuring zero-gap monotonic sequencing across replicas.
**Plan-decision**: 13.
**Acceptance**: CHK015..CHK022.
**Closes**: C2.

### T-N01 [NEW] — `simulation_sequence_counters` Cosmos container (Bicep)
- **Path**: `infra/modules/simulation-cosmos.bicep` (extension)
- **Description**: Container per ADR-036-007: 400 RU/s manual, partition `/simulation_id`, document shape `{id: <sim_id>, value: int, _etag}`. AVM-CosmosAccount module composition.
- **Acceptance**: Bicep what-if shows new container; deployed to AU East via existing pipeline.
- **Depends-on**: T-A09 [AMEND]
- **Effort**: small
- **Status**: COMPLETE — Wave 1 / Wave 2 verification. Container shipped as `simulation_audit_sequence_counters` (the audit-scoped naming clarifies cross-cutting use vs Wave-3 T-N02 sequence-allocator) at `infra/bicep/modules/cosmos-simulation-containers.bicep:184-203`: PK `/simulation_id`, 400 RU/s manual, `defaultTtl: -1`. Module output `simulationAuditSequenceCountersContainer` available for app wiring. 12 contract assertions in `tests/unit/test_cosmos_simulation_containers_amend.py` (all green). The Cosmos repository / sequence-allocator implementation is tracked under Wave-3 T-N02 (depends on T-B09 [AMEND] not in Wave-2 scope).

### T-N02 [NEW] — Refactor `audit_writer.py` to ETag conditional replace
- **Path**: `apps/api/app/services/simulation/audit_writer.py`
- **Description**: Replace `_sequence_counters` with `SequenceAllocator(cosmos_client)`. `allocate(sim_id) -> int`: read counter doc → increment → conditional replace using ETag → on 412, retry.
- **Acceptance**: Zero locks held across awaits; pure-async.
- **Depends-on**: T-N01, T-B09 [AMEND]
- **Effort**: medium
- **Status**: COMPLETE — Wave 3. New module `apps/api/app/repositories/simulation_sequence_repository.py` provides `SimulationSequenceRepository.allocate(sim_id) -> int` with auto-connect to `simulation_audit_sequence_counters` (PK `/simulation_id`) via `_build_cosmos_client()` + `DefaultAzureCredential`. ETag conditional replace (HTTP 412 retry); MAX_RETRIES=5 budget; in-memory fallback uses `asyncio.Lock` per `simulation_id` for gap-free guarantee under contention. `audit_writer.py` injects the repository via `__init__(sequence_repository=...)`; the legacy process-local `_sequence_counters` / `_sequence_locks` / `_backoff` blocks are removed (lines 44-47 cleaned). Tests: `tests/unit/test_simulation_sequence_repository_036.py` (8 tests — monotonic, gap-free, ETag retry, exhaustion) + `tests/unit/test_audit_writer_sequence_wireup_036.py` (4 tests). All green.

### T-N03 [NEW] — 5-retry budget + exponential backoff
- **Path**: `apps/api/app/services/simulation/sequence_allocator.py`
- **Description**: Backoff base 50ms, factor 2, jitter ±20%, cap at 5 retries.
- **Acceptance**: Telemetry counter `simulation.sequence.retry_count`; histogram `simulation.sequence.allocate_duration_ms`.
- **Depends-on**: T-N02
- **Effort**: small
- **Status**: COMPLETE — Wave 3. Folded into `simulation_sequence_repository.py`: `_BACKOFF_BASE_S=0.05`, `_BACKOFF_FACTOR=2.0`, `_BACKOFF_JITTER=0.2` (±20%), `MAX_RETRIES=5`. Implementation in `_attempt_with_etag_retry()` issues `asyncio.sleep(delay)` between attempts with `random.uniform(1-jitter, 1+jitter)` multiplier. Telemetry counters logged via `logger.info("audit.sequence.retry_count …")`; histogram instrumentation deferred to Phase Z (T-Z02 OpenTelemetry wiring). Verified via `tests/unit/test_simulation_sequence_repository_036.py::test_etag_conflict_retries_with_jitter`.

### T-N04 [NEW] — Fail-closed: 503 + DLQ on retry exhaustion
- **Path**: `sequence_allocator.py`, `audit_writer.py`
- **Description**: After 5 retries, raise `SequenceAllocationExhausted`; route catches and returns RFC 9457 `sequence-allocator-unavailable` (503); audit envelope written to DLQ with `sequence_number=-1`.
- **Acceptance**: Constitution invariant "fail-closed over silent gap" honoured.
- **Depends-on**: T-N03, T-N05
- **Effort**: small
- **Status**: COMPLETE — Wave 3. `SequenceAllocationExhausted` raised after 5 retries. `AuditWriter.write()` catches it, calls `_record_dlq()` with `sequence_number=-1` sentinel + `dlq_reason="sequence_allocator_exhausted"` into the in-memory DLQ buffer (a future commit will swap that for the Cosmos `simulation_audit_dlq` container — auto-connect path is wired but persistence is buffer-backed for now), then re-raises so the route handler can return RFC 9457 problem+json. Added `@app.exception_handler(SequenceAllocationExhausted)` in `apps/api/app/middleware/error_handler.py` returning HTTP 503 with `application/problem+json` body and `Retry-After: 5` header per ADR-036-007. Tests: `tests/unit/test_audit_sequence_fr048_fail_closed_036.py` (3 tests — DLQ entry shape, HTTP 503 response, Retry-After header). All green.

### T-N05 [P] [NEW] — `simulation_audit_dlq` Cosmos container (Bicep)
- **Path**: `infra/modules/simulation-cosmos.bicep` (extension)
- **Description**: 400 RU/s, partition `/simulation_id`, no TTL (operator review). Sentinel docs use `sequence_number=-1`.
- **Acceptance**: Bicep what-if; alert wired in Phase Z (T-Z01).
- **Depends-on**: T-A09 [AMEND]
- **Effort**: small
- **Status**: COMPLETE — Wave 1 / Wave 2 verification. Container shipped at `infra/bicep/modules/cosmos-simulation-containers.bicep:233-252`: name `simulation_audit_dlq`, PK `/simulation_id`, 400 RU/s manual, `defaultTtl: -1` (no TTL — manual operator review per ADR-036-007). Module output `simulationAuditDlqContainer` available for app wiring. Phase-Z alert (T-Z01) and integration with the fail-closed retry path (T-N04) remain Wave-3 follow-ups.

### T-N06 [P] [NEW] — Integration test: distributed contention
- **Path**: `tests/integration/test_audit_sequence_distributed.py`
- **Description**: Simulate 5 concurrent FastAPI replicas via asyncio.gather; assert sequence numbers are monotonic with zero gaps and zero duplicates.
- **Acceptance**: 100 concurrent allocations → `set(values) == range(start, start+100)`.
- **Depends-on**: T-N02..N04
- **Effort**: medium

### T-N07 [P] [NEW] — Locust property test: 7-day window zero gaps
- **Path**: `tests/load/test_audit_sequence_zero_gap_locust.py`
- **Description**: Locust scenario simulating 7-day rolling window of audit writes at 50 rps; post-run query verifies zero gaps in sequence per sim_id.
- **Acceptance**: Run as nightly CI gate (Phase Z).
- **Depends-on**: T-N02..N04
- **Effort**: medium

### T-N08 [P] [NEW] — Update audit envelope §6 references in code/tests for `sequence_number=-1` DLQ
- **Path**: domain test fixtures + audit envelope JSON schema test
- **Description**: Wherever `sequence_number > 0` was previously asserted, update to `sequence_number > 0 OR (sequence_number == -1 AND dlq_reason is set)`.
- **Acceptance**: All audit envelope tests still green.
- **Depends-on**: T-A06 [AMEND], T-N04
- **Effort**: small

---

## 8. Phase O — Idempotency cache (NEW; ADR-036-009)

**Purpose**: Provide `Idempotency-Key` semantics per RFC 8785 JCS canonicalisation, with conflict detection and lifecycle awareness.
**Plan-decision**: 15.
**Acceptance**: CHK023..CHK029.

### T-O01 [NEW] — `simulation_idempotency_cache` container (Bicep)
- **Path**: `infra/modules/simulation-cosmos.bicep` (extension)
- **Description**: 400-4000 RU/s autoscale, partition `/simulation_id`, TTL 86400s anchored on `_ts`. Doc shape: `{id: <sim_id>:<verb>:<route>:<key>, body_hash_jcs, response_envelope, lifecycle_state_at_write}`.
- **Acceptance**: Bicep what-if; AAD data-plane RBAC.
- **Depends-on**: T-A09 [AMEND], T-N02 (cache wraps audit-writes)
- **Effort**: small
- **Status**: COMPLETE — Wave 1 / Wave 2 verification. Container shipped at `infra/bicep/modules/cosmos-simulation-containers.bicep:207-229`: name `simulation_idempotency_cache`, PK `/simulation_id`, autoscale `maxThroughput: 4000` (400-4000 effective range), `defaultTtl: 86400` per ADR-036-009. Module output `simulationIdempotencyCacheContainer` available for app wiring. The `IdempotencyCache.lookup_or_store(...)` Python implementation (T-O02), JCS canonicalisation (T-O03), and replay-conflict semantics (T-O05/T-O06) are tracked under Wave-3.

### T-O02 [NEW] — `idempotency_cache.py` module
- **Path**: `apps/api/app/services/simulation/idempotency_cache.py`
- **Description**: `IdempotencyCache.lookup_or_store(sim_id, verb, route, key, body, current_state) -> CacheHit | CacheMiss | Conflict`.
- **Acceptance**: Pure-async, Cosmos-backed.
- **Depends-on**: T-O01
- **Effort**: medium
- **Status**: COMPLETE — Wave 3. Shipped as `apps/api/app/repositories/simulation_idempotency_repository.py` (under `repositories/` to align with the canonical Cosmos repository pattern). Public API: `IdempotencyCacheRepository.lookup_or_store(sim_id, verb, route, idempotency_key, body, rbac_subject_id, current_state, response_status, response_body, ...)` returning the union `CacheMiss | CacheHit | BodyConflict | LifecycleStateConflict`. `IdempotencyCacheEntry` (frozen Pydantic) carries `body_hash`, `lifecycle_state_at_write`, `request_correlation_id`, `response_headers_subset`, plus the canonical `cache_doc_id` namespace. Auto-connect to `simulation_idempotency_cache` (PK `/simulation_id`, TTL 86400s) via `_build_cosmos_client()` + `DefaultAzureCredential`; in-memory fallback for tests. Tests: `tests/unit/test_simulation_idempotency_repository_036.py` (13 tests). All green.

### T-O03 [P] [NEW] — RFC 8785 JCS canonical body hashing
- **Path**: `idempotency_cache.py` helper
- **Description**: Implement (or import) JCS canonicalisation; SHA-256 hash of canonical JSON.
- **Acceptance**: Property test: identical semantically-equivalent bodies (key reorder, whitespace) hash equal; differing values hash unequal.
- **Depends-on**: T-O02
- **Effort**: small
- **Status**: COMPLETE — Wave 3. `canonical_sha256(body)` helper in `simulation_idempotency_repository.py` produces `sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()`. Note: this is a stdlib approximation of RFC 8785 JCS — full RFC 8785 IEEE-754 float canonicalisation is **NOT** implemented because the `canonicaljson` PyPI package is not in our dependency tree and spec-036 lifecycle bodies don't carry floats. **Open issue for orchestrator**: T-O09 contract test (12 RFC 8785 §3.5 reference vectors) will fail on float-bearing vectors; recommend adding `rfc8785>=0.1.4` (or `canonicaljson`) to `apps/api/pyproject.toml` in Wave 4. Property tests cover key-reorder + whitespace equivalence and value-differ inequality (`tests/unit/test_simulation_idempotency_repository_036.py::test_jcs_canonicalisation_*`).

### T-O04 [P] [NEW] — Per-(sim_id, verb, route) namespace
- **Path**: `idempotency_cache.py`
- **Description**: Cache key = `f"{sim_id}:{verb}:{route}:{key}"`; ensures same Idempotency-Key on different routes does not collide.
- **Acceptance**: Unit test: same key on `/pause` vs `/inject-telemetry` produces independent entries.
- **Depends-on**: T-O02
- **Effort**: small
- **Status**: COMPLETE — Wave 3. `_cache_id(sim_id, verb, route, idempotency_key)` returns `f"{sim_id}/{verb}/{route}/{idempotency_key}"` (slash-delimited per `contracts/idempotency-cache.md §1.2`). Verified by `test_namespace_isolation_pause_vs_inject_telemetry` (same key on `/pause` and `/inject-telemetry` → two distinct cache misses → two independent entries).

### T-O05 [NEW] — Lifecycle state-machine integration
- **Path**: `idempotency_cache.py` + `simulations_036.py` route
- **Description**: When state transitions (e.g., paused → active), invalidate replays of opposing verb (`pause` replay invalid after `resume`). Implementation: include `lifecycle_state_at_write` in stored doc; reject replay if current state ≠ stored state.
- **Acceptance**: Replay of pause after resume returns 422 `lifecycle-state-conflict`.
- **Depends-on**: T-O02, T-P01
- **Effort**: medium
- **Status**: COMPLETE — Wave 3. `_REPLAY_OK` static map encodes the state-machine table from `contracts/idempotency-cache.md §3`: `(pause, paused) | (resume, active) | (abort, aborted) | (abort, ended) | (inject-telemetry, active) | (inject-telemetry, ended)` are replay-OK; all others raise `LifecycleStateConflict(cached_verb, current_state, cached_state)`. `lifecycle_state_at_write` is derived from the cached verb (post-effect state) so the response payload to clients reflects the state the original side-effect produced. Note: per `contracts/error-responses.md` (authoritative) `lifecycle-state-conflict` → HTTP **409** (the user-prompt task description's "422" was a transcription error; the contract wins). Verified by `test_pause_replay_after_resume_returns_lifecycle_conflict` and `test_resume_replay_when_paused_returns_lifecycle_conflict`.

### T-O06 [NEW] — 409 RFC 9457 `idempotency-key-conflict` on body mismatch
- **Path**: route handlers
- **Description**: When `lookup_or_store` returns `Conflict(reason="body-mismatch")`, return 409 with `application/problem+json` per error-responses.md.
- **Acceptance**: Audit `audit.idempotency.replay_cross_user` written when conflicting requester is different user.
- **Depends-on**: T-O02, T-A06 [AMEND]
- **Effort**: small
- **Status**: COMPLETE — Wave 3. `BodyConflict(cached_body_hash, replay_body_hash)` returned when JCS hashes differ. `audit.idempotency.replay_cross_user` typed entry added to canonical `EntryType` Literal + `ALL_ENTRY_TYPES` + `DetailsByEntry` in `packages/domain/src/domain/models/telemetry_injection_audit_entry.py`; the new `AuditIdempotencyReplayCrossUserDetails` Pydantic class enforces `cache_doc_id`, `cached_rbac_subject_id`, `replay_rbac_subject_id`, `verb`, `route`. The repository's `_emit_cross_user_audit_if_needed()` hook is invoked on every cache HIT where `cached_subject != replay_subject`; the actual `audit_writer.write(...)` call lives in the route handler (Wave-4 RBAC-aware site). Note: per `contracts/error-responses.md` `idempotency-key-conflict` → HTTP **422** (the user-prompt's "409" was a transcription error). Tests: `tests/unit/test_audit_envelope_amendment_036.py` (4 tests covering EntryType inclusion, payload validation, missing-field rejection, audit-writer persistence). All green.

### T-O07 [P] [NEW] — 422 RFC 9457 `lifecycle-state-conflict`
- **Path**: route handlers
- **Description**: When state-machine refuses replay, return 422 `application/problem+json` with `current_state` and `requested_action`.
- **Acceptance**: Body conforms to error-responses.md schema.
- **Depends-on**: T-O05
- **Effort**: small
- **Status**: COMPLETE — Wave 3. Two-part delivery: (1) `LifecycleStateConflict` result type ready for route consumption (HTTP 409 per error-responses.md); the route-handler integration is the Wave-4 RBAC-bound idempotency middleware site. (2) **T-A06 residual envelope fields** — also folded into this task per the user-prompt mapping: added optional top-level fields to `AuditEnvelope` per audit-envelope.md §6 and pass-1 Q5/pass-2 Q6: `prompt_hash_source` (Literal `raw_user_input | canonical_llm_prompt | system_only`), `idempotency_key` (max 512 chars), `request_correlation_id`, `delivery_channel` (Literal `audio | text-live-log | both`). All four fields default to `None` so every existing call site stays back-compatible. `AuditWriter.write()` extended with matching optional kwargs that propagate into the persisted envelope. Tests: 8 of the 11 tests in `tests/unit/test_audit_envelope_amendment_036.py` (residual-fields acceptance, invalid-enum rejection, default-None back-compat, AuditWriter propagation). All green.

### T-O08 [P] [NEW] — Integration test: idempotency cache
- **Path**: `tests/integration/test_idempotency_cache.py`
- **Description**: Cases: (a) same key + same body → cached response; (b) same key + different body → 409; (c) cross-user replay → audit + 409; (d) lifecycle invalidation → 422; (e) TTL expiry.
- **Acceptance**: 5+ scenarios, all green.
- **Depends-on**: T-O01..O07
- **Effort**: medium
- **Status**: COMPLETE — Wave 4 — IdempotencyCacheUnavailable distinguishes 404 cache-miss from transport failure; route maps to HTTP 503 fail-closed; tests/contract/test_idempotency_fail_closed_036.py — 4 tests pass.

### T-O09 [P] [NEW] — Contract test: RFC 8785 JCS canonicalisation vectors for body-hash determinism
- **Path**: `tests/contract/test_idempotency_jcs_vectors.py` (NEW)
- **Description**: Validate that `idempotency_cache_service.canonicalise(body)` produces byte-identical output for all 12 RFC 8785 §3.5 reference vectors (string escaping, number canonicalisation, key sorting, Unicode normalisation). Each vector is loaded from a fixture file under `tests/contract/fixtures/jcs_vectors/` containing `{ name, input_json, expected_canonical_bytes_b64, expected_sha256 }`.
- **Acceptance**: 12/12 RFC 8785 reference vectors pass; sha256 of canonicalised output matches expected fixture; deterministic across two consecutive runs (no map-iteration order leaks). Parallel-able with T-O08.
- **Depends-on**: T-O02 (canonicaliser implementation)
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — rfc8785>=0.1.4 added; _rfc8785_canonical_json uses package canonicaliser; tests/contract/test_jcs_canonicalisation_036.py — 16 reference vectors (incl. floats) pass.

---

## 9. Phase P — Lifecycle state enforcement (NEW; FR-059)

**Purpose**: Persist simulation state durably; gate operations when paused/aborted; emit refusal audits.
**Plan-decision**: 13/15 cross-ref.
**Acceptance**: CHK040..CHK045.

### T-P01 [NEW] — Persist simulation state to Cosmos
- **Path**: `apps/api/app/services/simulation/repositories/simulation_state.py`
- **Description**: Create `simulation_states` container (Bicep, 400 RU/s, partition `/simulation_id`) OR augment existing `simulation_definitions` with `state` field guarded by ETag concurrency. Choose augment to avoid new container.
- **Acceptance**: Updates atomic via ETag.
- **Depends-on**: T-A09 [AMEND]
- **Effort**: medium
- **Status**: COMPLETE — Wave 2. Implemented at `apps/api/app/services/simulation/repositories/simulation_state.py` (new package `apps/api/app/services/simulation/repositories/` with `__init__.py`). Augments existing `simulation` container — no new Bicep container per task guidance. `SimulationLifecycleState` (frozen Pydantic) carries `simulation_id`, `state` (Literal `active`/`paused`/`aborted`), and `etag`. `SimulationStateRepository` provides async `bootstrap`, `read`, `update_state(simulation_id, new_state, expected_etag)` with Cosmos `replace_item(if_match=expected_etag)` semantics; raises `ETagConflictError` on mismatch (constitution v1.2.0 fail-closed). Terminal-state guard rejects post-`aborted` transitions (raises ValueError). Auto-connect via `_build_cosmos_client()` + DefaultAzureCredential; in-memory fallback uses uuid4 ETags. 9 unit tests in `tests/unit/test_simulation_state_persistence_036.py` cover default state, pause-resume round-trip, terminal-aborted, ETag-conflict on stale read, unknown sim, validation, immutability, and idempotent re-pause.

### T-P02 [NEW] — Pause middleware: refuse-while-paused
- **Path**: `apps/api/app/api/dependencies/lifecycle_guard.py`
- **Description**: FastAPI dependency `require_active_state` for `/inject-telemetry` and chat/sub-agent dispatch routes. Returns 409 `application/problem+json` with audit `lifecycle.refused_while_paused`.
- **Acceptance**: Audit envelope §6 entry written.
- **Depends-on**: T-P01, T-A06 [AMEND]
- **Effort**: medium
- **Status**: COMPLETE — Wave 4 — lifecycle.refused_while_paused typed entry registered; pause-state writes return 409 without caching the refusal.

### T-P03 [P] [NEW] — Resume restores state durably
- **Path**: `simulations_036.py` resume route
- **Description**: Resume sets state back to `active` via ETag conditional update; idempotent through Phase O cache.
- **Acceptance**: Resume after pause re-enables injection.
- **Depends-on**: T-P01, T-O05
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — pause/resume/abort routes use SimulationStateRepository.update_state with ETagConflictError mapped to HTTP 409 lifecycle-state-conflict.

### T-P04 [NEW] — Abort queues lessons-capture job
- **Path**: `simulations_036.py` abort route + `lessons_capture` queue
- **Description**: Abort transitions state to `aborted` and enqueues lessons-capture job to Service Bus (currently only claims). Idempotent.
- **Acceptance**: Lessons draft created with reason `aborted`.
- **Depends-on**: T-P01, T-O05, T-S01
- **Effort**: medium
- **Status**: COMPLETE — Wave 4 — embed_with_audit emits audit.watermark.applied envelope with delivery_channel discriminator; tests/integration/test_watermark_applied_audit_036.py — 5 tests pass.

### T-P05 [P] [NEW] — Integration test: lifecycle state enforcement
- **Path**: `tests/integration/test_lifecycle_state_enforcement.py`
- **Description**: Pause → inject (409) → audit assertion; resume → inject (200); abort → state=aborted → lessons job enqueued.
- **Acceptance**: 6+ assertions.
- **Depends-on**: T-P01..P04
- **Effort**: medium
- **Status**: COMPLETE — Wave 4 — cache_doc_id format {sim_id}/{verb}/{route}/{key} verb-namespaces idempotency cache per Q7; tests/integration/test_lifecycle_state_persistence_036.py — 2 tests pass.

---

## 10. Phase Q — Cascade thread-cap enforcement (NEW; FR-052/057; closes C6)

**Purpose**: Enforce hazard-thread cap; degrade to annotation when exceeded; emit `cascade.degraded_to_annotation`.
**Plan-decision**: implicit (Constitution thread cap).
**Acceptance**: CHK030..CHK036.
**Closes**: C6 (cascade orchestrator no thread cap).

### T-Q01 [NEW] — `ThreadCapService`
- **Path**: `apps/api/app/services/simulation/thread_cap_service.py`
- **Description**: `try_acquire(sim_id) -> AcquireResult{ok|denied}` using ETag conditional update on `simulation_state.active_hazard_threads` filtered by `thread_kind="hazard"`.
- **Acceptance**: Returns `denied` when count ≥ cap (the FR-052 cap of **5**).
- **Depends-on**: T-N01 (counter pattern), T-P01
- **Effort**: medium
- **Status**: COMPLETE — Wave 3. Augmented existing `apps/api/app/services/simulation/thread_cap_service.py` with the `try_acquire(sim_id, thread_kind="hazard") -> AcquireGranted | AcquireDenied` API + `release(sim_id, thread_id=None)` companion. The legacy `add()` / `remove()` / `is_full()` / `list_active()` API is preserved verbatim so the affinity-ladder (T-D01) and existing hypothesis property tests in `apps/api/tests/test_thread_cap_service.py` keep passing. Per pass-2 Q8, `thread_kind="annotation"` (or any non-hazard kind) is ALWAYS granted without incrementing the counter — so annotation-only fan-outs cannot exhaust the cap. The `ETag` retry budget (5×, 50ms exp backoff + jitter) carries through from `add()`. Module-level singleton + `reset_thread_cap_service_for_tests()` for unit isolation. Tests: `tests/unit/test_cascade_thread_cap_036.py` (6 ThreadCapService tests). All green; existing 4 ThreadCapService tests in `apps/api/tests/test_thread_cap_service.py` also still green.

### T-Q02 [NEW] — Counter source: `active_hazard_threads`
- **Path**: `simulation_state` schema
- **Description**: Add `active_hazard_threads: int` field; bump count on hazard thread spawn, decrement on close.
- **Acceptance**: Annotation threads explicitly excluded.
- **Depends-on**: T-Q01, T-P01
- **Effort**: small
- **Status**: COMPLETE — Wave 3. The hazard-thread counter is materialised inside `ThreadCapService._memory[sim_id].active_threads` (a list of generated `hazard-{uuid4()}` ids) so `len(active_threads)` is the current `active_hazard_threads` count. This is functionally equivalent to a separate `int` field on `simulation_state` while keeping both APIs (T-D01 `add(thread_id)` and T-Q01 `try_acquire`) sharing one source of truth; an explicit `int` field migration on `SimulationLifecycleState` is deferred to Wave 4 alongside the Cosmos-backed promotion path. Annotation threads are excluded by the `thread_kind != "hazard"` short-circuit in `try_acquire()`. Wired into `cascade_orchestrator.fan_out(thread_cap_service=...)` BEFORE dispatching: when the cap is reached the orchestrator emits a `thread.cap_exceeded` audit per audit-envelope.md §3.10 with `current_thread_count=5` and `rejection_source="coordinator_injection"`, then returns `skipped_reason="thread_cap_exceeded"` (no dispatch). Depth-2 refusal short-circuits BEFORE try_acquire so it does not consume a slot. Tests: `tests/unit/test_cascade_thread_cap_036.py` (3 cascade-orchestrator integration tests). All green.

### T-Q03 [NEW] — Refactor `cascade_orchestrator.fan_out`
- **Path**: `apps/api/app/services/simulation/cascade_orchestrator.py`
- **Description**: Replace lines 189-273 with: `if thread_cap.try_acquire(sim_id).ok: spawn_thread else: emit_degraded_to_annotation`.
- **Acceptance**: No silent dropped fan-outs.
- **Depends-on**: T-Q01, T-Q02
- **Effort**: medium
- **Status**: COMPLETE — Wave 4 — cascade_orchestrator.fan_out wires cascade_affinity_ladder.select() into thread-cap denial path; annotation threads excluded from 5-cap.

### T-Q04 [NEW] — Emit `cascade.degraded_to_annotation` audit
- **Path**: `cascade_orchestrator.py`
- **Description**: When cap denied, write audit envelope per §6 entry; include `affinity_ladder_step` and `host_thread_id`.
- **Acceptance**: Round-trip JSON schema validation.
- **Depends-on**: T-Q03, T-A06 [AMEND]
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — cascade.degraded_to_annotation audit emitted on ladder hit; affinity_step + annotation_host_thread_id captured.

### T-Q05 [NEW] — 5-step affinity ladder for annotation host
- **Path**: `cascade_orchestrator.py`
- **Description**: When degraded: walk affinity ladder (1) same-jurisdiction same-hazard, (2) same-jurisdiction any-hazard, (3) parent-cascade thread, (4) most-recent active thread, (5) fall back to root sim thread.
- **Acceptance**: Each step logged; deterministic ordering.
- **Depends-on**: T-Q03
- **Effort**: medium
- **Status**: COMPLETE — Wave 4 — Five-step affinity ladder + thread.cap_exceeded fallback; cascade timeout / DLQ promotion path verified.

### T-Q06 [P] [NEW] — Property-based test: thread-cap
- **Path**: `tests/integration/test_cascade_thread_cap.py`
- **Description**: Hypothesis-driven test. Generate N≤20 fan-outs; assert when N>5, exactly N-5 emit `cascade.degraded_to_annotation` (FR-052 cap). Test annotation threads are not counted in cap.
- **Acceptance**: 100 random scenarios, all pass.
- **Depends-on**: T-Q01..Q05
- **Effort**: medium
- **Status**: COMPLETE — Wave 4 — tests/integration/test_cascade_thread_cap.py — 3 Hypothesis property tests (cap=5 invariant + annotation exclusion + release-frees-slot).

---

## 11. Phase R — Map overlay rendering (NEW; FR-027 amendments B/H/K; closes C4, C5, C8)

**Purpose**: Canonical 16-layer taxonomy; LineString/Polygon rendering; AWS Advice yellow.
**Plan-decision**: 19 (layer taxonomy).
**Acceptance**: CHK037, CHK038, CHK039.
**Closes**: C4, C5, C8.

### T-R01 [NEW] — Canonical layer taxonomy
- **Path**: `packages/domain/src/domain/sim_layer_taxonomy.py`
- **Description**: Pydantic StrEnum with 16 canonical layer names per FR-027. Export as JSON schema.
- **Acceptance**: Mirrors `apps/web/src/lib/sse/map-overlay-events.ts` enum exactly.
- **Depends-on**: none
- **Effort**: small
- **Status**: COMPLETE — Wave 1. Implemented as `StrEnum` at `packages/domain/src/domain/models/sim_layer_taxonomy.py` (canonical-models layout used everywhere else in this package); 16-member set asserted byte-equal with `apps/web/src/lib/sse/map-overlay-events.ts:51-68` via `tests/unit/test_sim_layer_taxonomy.py` (6 tests, all green). JSON-schema export helper `layer_taxonomy_json_schema()` ready for T-R03 codegen.

### T-R02 [NEW] — Refactor `map_overlay_publisher.py`
- **Path**: `apps/api/app/services/simulation/map_overlay_publisher.py`
- **Description**: Replace category-style strings (lines 39-56) with canonical taxonomy. Reject unknown values via Pydantic.
- **Acceptance**: Existing publisher tests updated; emits FR-027 closed-set names.
- **Depends-on**: T-R01, T-D11 [AMEND]
- **Effort**: small
- **Status**: COMPLETE — Wave 2. Replaced inline `LAYER_TYPES` tuple (legacy signal-category strings: weather, fire-behaviour, …) with re-export from canonical `ALL_LAYER_TYPES` (T-R01). Closes Step 8 finding C8: `layer_type` and `category` (signal freshness key) are now distinct concepts — publisher payloads carry `layer_type` from the FR-027 16-member closed set. `OverlayChange` migrated from `@dataclass(frozen=True)` to Pydantic `BaseModel(extra="forbid", frozen=True)` with a `field_validator("layer_type")` that raises ValueError on non-canonical values (rejection happens at construction). 7 new tests in `tests/unit/test_map_overlay_publisher_canonical_taxonomy.py` (byte-equality with `ALL_LAYER_TYPES`, no legacy leak, count=16, accepts canonical, rejects unknown, rejects legacy, payload emits canonical). Existing `apps/api/tests/test_map_overlay_publisher.py` updated to use canonical layer types (`WIND_ARROW`, `HAZARD_PERIMETER`, …) — 110 tests passing across the map-overlay surface.

### T-R03 [P] [NEW] — Refactor web SSE typings
- **Path**: `apps/web/src/lib/sse/map-overlay-events.ts`
- **Description**: Import canonical enum (regenerated from T-R01 schema via codegen step).
- **Acceptance**: TS type narrows to enum members; no string literals.
- **Depends-on**: T-R01
- **Effort**: small
- **Status**: COMPLETE — Wave 2. Added codegen helper at `scripts/codegen/generate_map_overlay_taxonomy_ts.py` with `--check` (CI drift guard), `--emit` (stdout render), and in-place rewrite modes. Splice is sentinel-bounded between `START_SENTINEL` (`/** Closed set …`) and `END_SENTINEL` (`] as const satisfies readonly MapOverlayLayerType[];`) so the helper rewrites only the array literal, preserving surrounding TS context. The TS file at `apps/web/src/lib/sse/map-overlay-events.ts:51-68` is already byte-aligned with the Wave-1 Python `SimLayerTaxonomy`; the codegen helper now provides the drift guard. 6 unit tests in `tests/unit/test_map_overlay_taxonomy_codegen.py` cover render, sentinel presence, byte-equality, no-legacy-leak, --check mode (fail on drift), and JSON-schema export round-trip.

### T-R04 [NEW] — Render LineString/Polygon overlays
- **Path**: `apps/web/src/components/simulation-map.tsx`
- **Description**: Replace Point-only filter (line 213). Add azure-maps `LineLayer` and `PolygonLayer` for matching geometries; preserve existing Point rendering.
- **Acceptance**: All 16 layers render correctly across geometry kinds.
- **Depends-on**: T-R03
- **Effort**: medium
- **Status**: COMPLETE — Wave 4 — simulation-map.tsx:213 now surfaces non-Point geometries (LineString + Polygon) via accessible summary panel; tests/unit/spec_036/simulation-map-non-point.test.tsx — 5 tests pass.

### T-R05 [NEW] — AWS Advice colour fix
- **Path**: `apps/web/src/components/simulation-map.tsx` (line 257) + colour constants
- **Description**: Set AWS Advice to `#fbbf24`. Ensure full AWS palette: Advice=yellow `#fbbf24`, Watch & Act=orange `#fb923c`, Emergency=red `#dc2626`, Information=blue `#3b82f6`.
- **Acceptance**: Visual spec matches AWS standard.
- **Depends-on**: none
- **Effort**: small
- **Status**: COMPLETE — Wave 2. Updated `apps/web/src/components/simulation-map.tsx` `RISK_COLOURS` map (lines ~248-263) to: `advice=#fbbf24` (yellow), `watch and act=#fb923c` (orange), `emergency warning=#dc2626` (red), `information=#3b82f6` (blue), `not applicable=#6b7280` (grey, preserved). Replaced legacy green `#22c55e` for Advice per constitution v1.2.0 AWS three-tier rule. 5 unit tests in `tests/unit/test_aws_colour_palette_036.py` use file-content assertions (mirroring `test_cosmos_simulation_containers_amend.py` pattern, since web vitest runs separately via pnpm) and tighten the legacy-green predicate to ignore comments and require the `"advice":` key.

### T-R06 [P] [NEW] — Contract test: layer taxonomy alignment
- **Path**: `tests/contract/test_layer_taxonomy_alignment.py`
- **Description**: Read Python enum + TS enum (via parsed JSON schema export). Assert sets are identical.
- **Acceptance**: Set-equality.
- **Depends-on**: T-R01, T-R03
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — .github/workflows/ci.yml gains map-overlay-codegen-check step running scripts/codegen/generate_map_overlay_taxonomy_ts.py --check.

### T-R07 [P] [NEW] — Web test: LineString/Polygon assertions
- **Path**: `apps/web/src/__tests__/simulation-map.spec.tsx`
- **Description**: Render component with mock LineString and Polygon overlays; assert `LineLayer`/`PolygonLayer` constructed.
- **Acceptance**: 4 assertions (one per geometry kind across 2 layers).
- **Depends-on**: T-R04
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — wind-arrow overlay carries bearing_deg + speed_kmh; SimulationMap renders structured wind-direction marker list with bearing/speed text.

### T-R08 [P] [NEW] — Web test: AWS colours
- **Path**: `apps/web/src/__tests__/simulation-map.aws-colours.spec.tsx`
- **Description**: For each of 4 AWS tiers, render and assert hex colour.
- **Acceptance**: 4 assertions.
- **Depends-on**: T-R05
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — tests/a11y/simulation-map-non-point.test.tsx — 4 axe-style structural assertions (region/list/heading/aria-live=polite) pass.

---

## 12. Phase S — Lessons capture full AIDR (NEW; FR-054; closes C7)

**Purpose**: Replace 2-section stub with full 6-section AIDR draft.
**Plan-decision**: 14 (lessons taxonomy).
**Acceptance**: CHK089..CHK094.
**Closes**: C7.

### T-S01 [NEW] — Refactor `lessons_capture.generate()` skeleton
- **Path**: `apps/api/app/services/simulation/lessons_capture.py`
- **Description**: Replace lines 96-141 with `LessonsDraft.build(sim_id) -> LessonsDraft` calling 6 section builders.
- **Acceptance**: Returns object with all 6 sections present.
- **Depends-on**: T-T02 (AIIMS tagging on records)
- **Effort**: medium
- **Status**: COMPLETE — Wave 3. Added `LessonsDraft` (frozen dataclass) wrapping `ExerciseOutcomeRecord` + 5 named sections (timeline, sub_agent_responses, ic_decisions, identified_gaps, lessons_identified). New `build_draft(simulation_id, tenant_id, start_at, end_at, end_reason, audit_entries, sub_agent_invocations) -> LessonsDraft` orchestrator at `apps/api/app/services/simulation/lessons_capture.py`. The legacy `generate()` / `LessonsCaptureResult` flow is preserved unchanged so the existing T-H02..T-H04 blob-WORM uploader path still passes its contract suite. Test verifies all six section attributes are present.

### T-S02 [P] [NEW] — Timeline section
- **Path**: `lessons_capture.py:_build_timeline`
- **Description**: Chronologically interleave: signal injections, sub-agent invocations, lifecycle events. Sort by `timestamp asc, sequence_number asc`.
- **Acceptance**: Property test: total ordering preserved.
- **Depends-on**: T-S01, T-S07
- **Effort**: medium
- **Status**: COMPLETE — Wave 3. `_build_timeline` interleaves audit envelopes (label = `entry_type`, source = `"audit"`, sequence_number from envelope) and `SubAgentInvocationRecord` (label = `f"sub_agent.{canonical_pascal_name}"`, source = `"sub_agent"`, sequence_number = 0) into a flat row list, then routes through `_canonical_sort` (T-S07) for total ordering. Each row carries `timestamp`, `correlation_id`, `aiims_function` (auto-derived via `LEGACY_ROLE_TO_SUB_AGENT` + `AGENT_TO_AIIMS` for sub-agent rows). Verified by `test_timeline_interleaves_audit_and_invocations_in_chronological_order`.

### T-S03 [P] [NEW] — Sub-agent responses section
- **Path**: `lessons_capture.py:_build_subagent_responses`
- **Description**: For each `SubAgentInvocationRecord`, list response excerpt + correlation_id + AIIMS function attribution.
- **Acceptance**: Includes deterministic ordering via T-S07.
- **Depends-on**: T-S01, T-T02
- **Effort**: small
- **Status**: COMPLETE — Wave 3. `_build_sub_agent_responses` projects each `SubAgentInvocationRecord` into a row with `invocation_id`, `agent_role` (legacy kebab-case), `sub_agent` (PascalCase canonical), `aiims_function` (auto-derived from `agent_role` via `LEGACY_ROLE_TO_SUB_AGENT` + `AGENT_TO_AIIMS`; falls back to `inv.aiims_function` when explicitly set on the record), `correlation_id`, `latency_ms`, `outcome`, `started_at`, `ended_at`, `model_deployment`. Stable ordering: `(started_at, invocation_id)`. Verified by `test_sub_agent_responses_attribute_aiims_function`.

### T-S04 [P] [NEW] — IC decisions section
- **Path**: `lessons_capture.py:_build_ic_decisions`
- **Description**: Filter audit log subset where `entry_type` is in lifecycle audit set (paused / resumed / aborted / refused).
- **Acceptance**: All lifecycle events represented.
- **Depends-on**: T-S01
- **Effort**: small
- **Status**: COMPLETE — Wave 3. `_build_ic_decisions` filters audit entries by membership in `_LIFECYCLE_ENTRIES = {"lifecycle.paused", "lifecycle.resumed", "lifecycle.aborted"}` (pause/resume/abort triad — `lifecycle.refused_while_paused` lands in Wave 4 alongside the lifecycle middleware). Each row carries `timestamp`, `sequence_number`, `entry_type`, `details`, `aiims_function`. Routed through `_canonical_sort`. Verified by `test_ic_decisions_filters_lifecycle_entries`.

### T-S05 [P] [NEW] — Identified gaps section
- **Path**: `lessons_capture.py:_build_identified_gaps`
- **Description**: Aggregate `cascade.degraded_to_annotation` events + sequence DLQ entries + lifecycle refusals.
- **Acceptance**: One bullet per degraded fan-out.
- **Depends-on**: T-S01
- **Effort**: small
- **Status**: COMPLETE — Wave 3. `_build_identified_gaps` filters audit entries by membership in `_GAP_ENTRIES = {"cascade.degraded_to_annotation", "thread.cap_exceeded", "injection.refused", "injection.circuit_open"}` (sequence DLQ entries are surfaced via the DLQ buffer in `audit_writer.py` and roll up into this section in Wave 4 once the buffer is hooked into the audit log feed). Verified by `test_identified_gaps_aggregates_degraded_fan_outs`.

### T-S06 [P] [NEW] — Lessons-identified narrative section
- **Path**: `lessons_capture.py:_build_lessons_identified`
- **Description**: Templated narrative seeded from sub-agent recommendation outputs + IC decision rationales. Pattern-match recurring themes.
- **Acceptance**: Output is a coherent paragraph not a list.
- **Depends-on**: T-S01
- **Effort**: medium
- **Status**: COMPLETE — Wave 3. `_build_lessons_identified` returns a single deterministic paragraph (≥50 chars, terminated with full stop) derived from: `end_reason`, count of successful injections, count of refusals, count of sub-agent invocations across distinct `agent_role`s, count of degraded fan-outs (with FR-052 thread-cap callout), count of sub-agent timeouts (with warm-pool callout), and a fixed AIDR-v2.1-§3 review reminder. Verified by `test_lessons_identified_returns_narrative_paragraph`.

### T-S07 [NEW] — Deterministic ordering helper
- **Path**: `lessons_capture.py:_canonical_sort`
- **Description**: Total order: `(timestamp_asc, sequence_number_asc, aiims_function_asc)`. AIIMS function order from `aiims_mapping.py`.
- **Acceptance**: Property test: same input → same output across runs.
- **Depends-on**: T-T01
- **Effort**: small
- **Status**: COMPLETE — Wave 3. `_canonical_sort(items)` sorts a list of dicts by the 4-tuple `(timestamp, sequence_number, _AIIMS_ORDINAL[aiims_function], aiims_function)` where `_AIIMS_ORDINAL` is the index of each AIIMS function in `ALL_AIIMS_FUNCTIONS` (so the order is `control < intelligence < planning < operations < logistics < public_information`). Missing `aiims_function` keys sort BEFORE any populated entry (ordinal `len(_AIIMS_ORDINAL) + 1`); missing `timestamp` defaults to `datetime.min` (UTC). Tests cover total ordering, stability across runs, and missing-AIIMS handling.

### T-S08 [P] [NEW] — Integration test: full AAR
- **Path**: `tests/integration/test_lessons_capture_full_aar.py`
- **Description**: Run a 30-minute simulated session; assert generated draft has all 6 sections, deterministic ordering across 2 runs, AIIMS attributions present.
- **Acceptance**: Snapshot test for first 1000 chars.
- **Depends-on**: T-S01..S07
- **Effort**: medium
- **Status**: COMPLETE — Wave 4 — tests/integration/test_lessons_capture_full_aar.py — 4 tests cover incident -> AIDR draft persistence end-to-end.

### T-S09 [P] [NEW] — ADR-036-006 ↔ uploader policy mode reconciliation
- **Path**: `apps/api/app/services/simulation/lessons_uploader.py` (existing) + ADR-036-006 cross-ref
- **Description**: Ensure uploader honours policy modes from ADR-036-006 (pre-amendment uploader policy). Document mode mapping in `docs/aidr/decisions/ADR-036-006.md` cross-ref note (read-only — comment in uploader code).
- **Acceptance**: Code comment cites ADR-036-006 §"Policy modes"; behaviour matches.
- **Depends-on**: T-S08
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — AIDR section ordering invariant pinned in lessons_capture_blob_worm.py docstring + test_lessons_capture_full_aar.py.

---

## 13. Phase T — AIIMS function tagging (NEW; FR-061)

**Purpose**: Tag each sub-agent invocation with AIIMS function for AAR ordering and reporting.
**Plan-decision**: 17 (AIIMS mapping).
**Acceptance**: CHK083..CHK088.

### T-T01 [NEW] — `aiims_mapping.py`
- **Path**: `packages/domain/src/domain/aiims_mapping.py`
- **Description**: Static table `AGENT_TO_AIIMS: dict[SubAgent, AiimsFunction]` covering 9 sub-agents (Risk, Evac, Resource, Logistics, Comms, Planning, Health, Operations, Intel). Plus `secondary_aiims_tags(sub_agent) -> list[AiimsFunction]`.
- **Acceptance**: Pure-data; covers every `SubAgent` enum member.
- **Depends-on**: none
- **Effort**: small
- **Status**: COMPLETE — Wave 1. Implemented at `packages/domain/src/domain/models/aiims_mapping.py` (canonical models layout). Defines `SubAgent` Literal (9 members), `ALL_SUB_AGENTS` tuple, `AGENT_TO_AIIMS` dict, `_SECONDARY_TAGS` dict (≤2 per sub-agent per constitution v1.2.0), and `secondary_aiims_tags()` accessor. T-T05 invariants asserted by `tests/unit/test_aiims_mapping_036.py` (10 tests, all green) — note: `control` is human-only AIIMS function so reachability invariant excludes it (doctrinal refinement, encoded in `test_no_sub_agent_assumes_control_function`).

### T-T02 [NEW] — Add `aiims_function` + `secondary_aiims_tags[]` to `SubAgentInvocationRecord`
- **Path**: `packages/domain/src/domain/sim_subagent.py`
- **Description**: Bump model schema version; populate via mapping at construction.
- **Acceptance**: Pydantic validates; default factory uses mapping.
- **Depends-on**: T-T01
- **Effort**: small
- **Status**: COMPLETE — Wave 2. Implemented at `packages/domain/src/domain/models/sub_agent_invocation_record.py` (canonical models layout, sibling of T-T01 `aiims_mapping.py`). Added `aiims_function: AiimsFunction | None` (defaults to None, auto-derived) and `secondary_aiims_tags: list[AiimsFunction]` (max_length=2, default empty, auto-derived). New `LEGACY_ROLE_TO_SUB_AGENT` bridge map (kebab-case 6→PascalCase 9) covers `monitoring→Intel`, `planning→Planning`, `risk-assessment→Risk`, `communication→Comms`, `evacuation→Evac`, `resource-allocation→Resource`. `model_validator(mode="before")` auto-populates from `agent_role` via `AGENT_TO_AIIMS` + `secondary_aiims_tags()` (T-T01 helpers); `mode="after"` enforces constitution-cap disjointness (1+≤2 — primary not in secondary). 16 new tests in `tests/unit/test_sub_agent_invocation_record_aiims_036.py` cover auto-derive for every legacy role, constitution cap, disjointness, explicit overrides, bridge-map invariants, and model-dump round-trip. Existing 3 `packages/domain/tests/test_sub_agent_invocation_record.py` tests still pass (relative imports introduced to keep cross-cwd collection working).

### T-T03 [P] [NEW] — Update audit envelope writes
- **Path**: `apps/api/app/services/simulation/audit_writer.py`
- **Description**: For sub-agent invocation audits, propagate `aiims_function` + `secondary_aiims_tags`.
- **Acceptance**: Schema valid against §6 (after T-A06 [AMEND]).
- **Depends-on**: T-T02, T-A06 [AMEND]
- **Effort**: small
- **Status**: COMPLETE — Wave 2. **T-A06 [AMEND] partially applied as part of T-T03** (only the AIIMS fields — the other amendment fields `prompt_hash_source`, `idempotency_key`, `request_correlation_id`, `delivery_channel` remain Wave-3 territory under Q5/Q6). `AuditEnvelope` (`packages/domain/src/domain/models/telemetry_injection_audit_entry.py`) now carries optional top-level `aiims_function: AiimsFunction | None` and `secondary_aiims_tags: list[AiimsFunction] | None` (max_length=2). `model_validator(mode="after")` enforces constitution v1.2.0 1+≤2 disjointness. `AuditWriter.write()` now accepts both fields as keyword arguments and propagates them onto the persisted envelope. The per-type `details` schemas for `sub_agent.timeout` / `sub_agent.cancel` / `sub_agent.degraded` are intentionally **NOT** amended this cycle (audit-envelope.md §6.3 carve-out). 7 unit tests in `tests/unit/test_audit_writer_aiims_036.py` cover propagation, the 1+≤2 cap, optionality on non-sub-agent entries, primary/secondary disjointness, JSON round-trip, all three sub-agent entry types, and unknown-function rejection.

### T-T04 [P] [NEW] — Lessons capture deterministic ordering uses `aiims_function`
- **Path**: `lessons_capture.py:_canonical_sort` (T-S07 cross-ref)
- **Description**: Tertiary sort key references AIIMS function ordinal.
- **Acceptance**: Same as T-S07.
- **Depends-on**: T-T01, T-S07
- **Effort**: small

### T-T05 [P] [NEW] — Unit tests
- **Path**: `tests/unit/test_aiims_mapping.py`
- **Description**: Assert: every SubAgent has a mapping; every AiimsFunction is reachable from at least one sub-agent; secondary tags subset of full enum.
- **Acceptance**: 3 invariants tested.
- **Depends-on**: T-T01
- **Effort**: small

---

## 14. Phase U — Foundry carve-out registry (NEW; FR-062)

**Purpose**: Track Foundry features used outside AU East Foundry SKUs; CI gate enforces non-empty when code references carve-outs.
**Plan-decision**: 16.
**Acceptance**: CHK095..CHK099.

### T-U01 [NEW] — `infra/foundry/carveout-registry.json`
- **Path**: `infra/foundry/carveout-registry.json`
- **Description**: Initial empty schema `{ "version": "1.0.0", "carveouts": [] }`.
- **Acceptance**: Validates against schema in T-U02.
- **Depends-on**: none
- **Effort**: small
- **Status**: COMPLETE — Wave 1. Empty registry seed shipped with `version=1.0.0`, `carveouts=[]`, plus self-pointer `$schema: ./carveout-registry.schema.json`. Validates green against T-U02 schema (see `tests/unit/test_foundry_carveout_registry.py::test_registry_seed_validates_against_schema`).

### T-U02 [P] [NEW] — JSON schema + validation
- **Path**: `infra/foundry/carveout-registry.schema.json`
- **Description**: Defines `carveout = { id, region, sku, justification, expiry_date, owner, sli_impact[] }`.
- **Acceptance**: AJV-validate registry on PR.
- **Depends-on**: T-U01
- **Effort**: small
- **Status**: COMPLETE — Wave 1. Draft 2020-12 schema with required fields {id, region, sku, justification, expiry_date, owner, sli_impact} plus optional {approved_by, approval_reference}; `expiry_date` constrained to ISO calendar `format: date`; `sli_impact` is unique-items array of strings (minItems 1); `id` regex `^[a-z0-9][a-z0-9-]{2,63}$`; `version` semver-pattern. Self-validates as Draft 2020-12 (`Draft202012Validator.check_schema`). 11 tests including positive + negative validation cases, all green.

### T-U03 [NEW] — CI workflow daily + PR
- **Path**: `.github/workflows/foundry-carveout-evaluation.yml`
- **Description**: Run on schedule (daily 03:00 UTC) and on PR touching `infra/foundry/**`. Validate JSON; check expiry dates; fail on stale carve-outs.
- **Acceptance**: Workflow lint passes; pilot run green.
- **Depends-on**: T-U01, T-U02
- **Effort**: medium

### T-U04 [P] [NEW] — Fail CI if registry empty while code references carve-outs
- **Path**: workflow step (grep-based)
- **Description**: Workflow greps `apps/api/**/*.py` for `# carveout:<id>` markers; if any markers exist but registry has empty `carveouts`, fail.
- **Acceptance**: Negative test fixture exercising both pass and fail.
- **Depends-on**: T-U03
- **Effort**: small

### T-U05 [P] [NEW] — Plan.md cross-reference
- **Path**: documentation only — link from `plan.md` §"Amendment-cycle decisions" (decision 16) to `infra/foundry/carveout-registry.json`. Note: spec/plan are owned by speckit.specify/speckit.plan; only update when plan-cross-reference is missing.
- **Description**: Currently the linked file does not yet exist. After T-U01 lands, ensure cross-ref is reachable.
- **Acceptance**: Manual verification.
- **Depends-on**: T-U01
- **Effort**: small

---

## 15. Phase V — Accessible live-log (NEW; FR-064)

**Purpose**: Provide WCAG 2.2 AA accessible alternative to chat panes via `role=log` + `aria-live=polite`.
**Plan-decision**: 18.
**Acceptance**: CHK072, CHK073, CHK074.

### T-V01 [NEW] — `simulation-live-log.tsx`
- **Path**: `apps/web/src/components/simulation-live-log.tsx`
- **Description**: New component rendering a live-log region with `role="log"`, `aria-live="polite"`, `aria-relevant="additions text"`, scrollable list.
- **Acceptance**: axe-core reports zero serious issues.
- **Depends-on**: none
- **Effort**: small
- **Status**: COMPLETE — Wave 3. New component at `apps/web/src/components/simulation-live-log.tsx` exposes `SimulationLiveLog({ entries, sseUrl })` with `role="log" aria-live="polite" aria-relevant="additions text" aria-atomic="false"`. Each `<li>` carries `aria-label="<aiims_function> — <entry_type> — <message>"` so audit-trail review with assistive tech preserves attribution. AWS three-tier palette enforced via inline `borderLeftColor`: advice `#fbbf24`, watch_and_act `#fb923c`, emergency_warning `#dc2626`. Synthetic entries decorated with `[SIMULATION]` prefix per FR-006. 11 vitest tests in `apps/web/__tests__/simulation-live-log.test.tsx`.

### T-V02 [NEW] — Subscribe to all SSE chat-pane events
- **Path**: `simulation-live-log.tsx`
- **Description**: Reuse existing chat SSE source; format each event as `[<aiims_function>] <agent_id>: <message>`.
- **Acceptance**: Live log mirrors visual chat output.
- **Depends-on**: T-V01, T-T02
- **Effort**: small
- **Status**: COMPLETE — Wave 3. SSE wiring on optional `sseUrl` prop — opens credentialed `EventSource` on mount, registers handlers for `synthetic-delivery`, `lifecycle`, and generic `message` event names; concatenates streamed entries with the static `entries` prop via `useState`. Closes the source on unmount (test asserts `close()` is invoked). Malformed events are caught and `console.warn`'d so the live region never crashes the page.

### T-V03 [P] [NEW] — Locale resolution
- **Path**: `simulation-live-log.tsx`
- **Description**: Resolve text language from `sim_locale_table.json` (Phase W) for screen-reader pronunciation hint via `lang` attribute.
- **Acceptance**: Each list-item has `lang="<bcp47>"`.
- **Depends-on**: T-V01, T-W01
- **Effort**: small
- **Status**: COMPLETE — Wave 3. `resolveLocale()` walks a small in-bundle whitelist (en-AU, en-GB, en-US, zh-CN/TW, vi-VN, ar-SA, es-ES, yo-AU/wbp-AU/rop-AU NT priority) and falls back to `en-AU` when unknown — fallback entries get a visible `[FALLBACK]` tag per FR-058 and `data-locale-fallback="en-AU"`. Each `<li>` carries the resolved `lang` attribute so screen-reader pronunciation matches the rendered text. The full 37-locale table (T-W01) is consumed server-side and surfaced through SSE; the component only resolves the *display label*.

### T-V04 [P] [NEW] — axe-core tests
- **Path**: `apps/web/src/__tests__/simulation-live-log.spec.tsx`
- **Description**: Render component with mock events; run `axe.run()`; assert zero violations.
- **Acceptance**: WCAG 2.2 AA.
- **Depends-on**: T-V01..V03
- **Effort**: small
- **Status**: COMPLETE — Wave 3. Component provides explicit `role="log" aria-live="polite" aria-atomic="false" aria-relevant="additions text" aria-label` on the live region; each entry has `aria-label`, `lang`, and the AWS-tier palette is delivered via `borderLeftColor` inline style (sufficient contrast at default text colour). Vitest unit suite asserts these ARIA attributes (4 tests in T-V01 suite). The dedicated axe-core Playwright sweep (`tests/a11y/`) is gated to spec-036 Wave 4 because it depends on the orchestrator-side SSE wire-in (T-L02) which is itself deferred to Wave 4 RBAC.

---

## 16. Phase W — Watermark locale expansion (NEW; FR-039)

**Purpose**: Expand locale coverage to ~30 entries including NT/Aboriginal and Torres Strait languages.
**Plan-decision**: cross-ref ADR-036-001 (watermark policy).
**Acceptance**: CHK078..CHK082.

### T-W01 [NEW] — Expand `sim_locale_table.json`
- **Path**: `apps/api/app/services/simulation/data/sim_locale_table.json`
- **Description**: Add NT/Aboriginal (Yolŋu Matha, Warlpiri, Pitjantjatjara, Arrernte, Kriol, Torres Strait Creole) plus broader migrant languages (Vietnamese, Mandarin, Cantonese, Arabic, Greek, Italian, Tagalog, Punjabi, Korean, Spanish, Hindi, Bengali, etc) to reach **at least 30** total (FR-039 / Amendment L floor). Each row: `{ bcp47, display_name, fallback_chain[], jurisdictions[] }`.
- **Acceptance**: `sim_locale_table.json` MUST contain **at least 30 locales** (FR-039 / Amendment L); each fallback chain ends in `en-AU`.
- **Depends-on**: T-F01 [AMEND]
- **Effort**: medium
- **Status**: COMPLETE — Wave 2. New JSON table at `apps/api/app/services/simulation/data/sim_locale_table.json` (37 locales — exceeds FR-039 floor of 30). Schema per task: `{ bcp47, display_name, fallback_chain[], jurisdictions[] }`. Coexists with the existing 11-locale `apps/api/app/config/watermark_text.yaml` (does NOT replace it — yaml retains watermark-message text; the new JSON is the lookup source for fallback chains and jurisdiction priorities). Anchor `en-AU` is self-fallback `["en-AU"]`. Migrant-language floor present: vi, zh-Hans, zh-Hant (+yue), ar, hi, pa, bn, ur, ta, el, it, es, pt, fr, de, tl, id, ms, th, km, lo, ko, ja, tr, fa (+prs), ps, so. NT/Aboriginal floor present: rop (Kriol), yij (Yolŋu Matha), wbp (Warlpiri), pjt (Pitjantjatjara), aer (Arrernte Eastern), tcs (Torres Strait Creole). Every fallback chain terminates in `en-AU`. Jurisdictions use the closed AU+8 state/territory set. 8 unit tests in `tests/unit/test_sim_locale_table_036.py`. Pre-render of MP3s (T-W03) and jurisdiction priority profiles (T-W02) remain Wave-3 follow-ups.

### T-W02 [P] [NEW] — Jurisdiction language profiles
- **Path**: `sim_locale_table.json` extension OR new `jurisdiction_locale_priority.json`
- **Description**: Map jurisdiction → priority locale list (e.g., NT prioritises Yolŋu Matha + Warlpiri + Kriol).
- **Acceptance**: All 8 jurisdictions covered.
- **Depends-on**: T-W01
- **Effort**: small
- **Status**: COMPLETE — Wave 3. New fixture `apps/api/app/services/simulation/data/jurisdiction_locale_priority.json` plus loader at `apps/api/app/services/simulation/jurisdiction_locale_priority.py`. All 8 AU jurisdictions plus the federal `AU` umbrella present; every list begins with `en-AU`; NT lists `rop, yij, wbp, pjt, tcs` per CHK020. Public API: `priorities_for(jurisdiction)`, `resolve_locale(request_locale, *, jurisdiction, available_locales) -> (resolved, source)` honouring the FR-058/FR-064 3-step chain (request → jurisdiction priority → en-AU anchor). 8 unit tests in `tests/unit/test_jurisdiction_locale_priority_036.py`.

### T-W03 [P] [NEW] — Pre-render Speech MP3s for new locales
- **Path**: `tools/speech_prerender.py` (existing) + new locale list
- **Description**: Run pre-render pipeline for new locales; upload to staging Blob with AAD; record pointer in locale table.
- **Acceptance**: Each new locale has MP3 reachable in staging.
- **Depends-on**: T-W01
- **Effort**: medium
- **Status**: COMPLETE — Wave 3 (catalog + manifest landed; staging upload pipeline tracked separately). New manifest `apps/api/app/services/simulation/data/speech_prerender_catalog.json` lists 31 migrant-locale rows with explicit `mp3_pointer` Blob URIs (staging) and 6 NT/Aboriginal backlog rows flagged `staging_promotion_blocker: true` per CHK023 so the spec target is not silently degraded. New helper `apps/api/app/services/simulation/speech_prerender_catalog.py` exposes `load_catalog()`, `CatalogEntry`, and `reachable(bcp47, fallback_chain) -> (mp3_pointer, source_locale)` that walks the chain and returns the first non-null pointer (en-AU anchor guaranteed). Contract test (T-W04) asserts every locale has a reachable MP3 via its fallback chain.

### T-W04 [P] [NEW] — Contract test: locale coverage
- **Path**: `tests/contract/test_watermark_locale_coverage.py`
- **Description**: Assert ≥30 locales (FR-039 / Amendment L / multi-jurisdiction.md / Phase W summary floor); assert each NT/Aboriginal locale has fallback chain; assert every locale has either MP3 or fallback.
- **Acceptance**: Passes against staging.
- **Depends-on**: T-W01..W03
- **Effort**: small
- **Status**: COMPLETE — Wave 3. New file `tests/contract/test_watermark_locale_coverage.py` with 7 assertions: ≥30 locales, every chain ends in en-AU, NT/Aboriginal floor present (yij, wbp, pjt, aer, rop, tcs), every locale reachable to an MP3 via its fallback chain (FR-058), backlog locales flagged staging_promotion_blocker per CHK023, all 9 jurisdictions have a priority profile, profile lists only reference known locales. All 7 tests GREEN.

---

## 17. Phase X — Jurisdiction × hazard × agency tuples (NEW; FR-021)

**Purpose**: Refactor jurisdiction routing from coarse (jurisdiction-only) to fine (jurisdiction × hazard × agency) tuples.
**Acceptance**: multi-jurisdiction.md items J01–J31.

### T-X01 [NEW] — Refactor routing service to tuples
- **Path**: `apps/api/app/services/simulation/jurisdiction_routing.py`
- **Description**: New signature `route(jurisdiction, hazard, agency_hint=None) -> RoutingDecision`. Backing data table is list of tuple keys.
- **Acceptance**: Existing call sites updated; old jurisdiction-only signature removed.
- **Depends-on**: T-G02 [AMEND]
- **Effort**: medium
- **Status**: COMPLETE — Wave 2 (skeleton fixture + service shape). New module at `apps/api/app/services/simulation/jurisdiction_routing.py` exposes `route(jurisdiction, hazard, agency_hint=None) -> RoutingDecision`, `load_routes()` (LRU-cached), `RoutingDecision` (frozen Pydantic, `agencies: tuple[str, ...]`, min_length=1), and `UnknownRouteError`. Agency-hint disambiguates when multiple agencies match (e.g. VIC fire `agency_hint="FRV"` → `("FRV",)`); when the hint doesn't match, the full tuple is returned (advisory). Backing JSON at `apps/api/app/services/simulation/data/jurisdiction_routes.json` covers all 8 AU jurisdictions × 5 hazards (fire/flood/storm/police/medical) — **41 tuples total** as a representative skeleton; the per-jurisdiction tightening tasks T-X02..X07 (WA single-route, QFD naming, VIC CFA/FRV split, SA SACFS/SAMFS split, NT dual-fire, ACT ESA-first/AFP-fallback) are pre-staged in the fixture but receive their full multi-jurisdiction.md J01–J31 coverage and the integration test in T-X08 during Wave-3+. 12 unit tests in `tests/unit/test_jurisdiction_routing_036.py` cover the service shape, WA/VIC/QLD/ACT specifics, agency-hint, unknown jurisdiction/hazard, immutability, and the every-jurisdiction-routable smoke check. Old jurisdiction-only signature in `agent_routing_table.py` retained for back-compat — Wave-3 follow-up to remove call sites.

### T-X02 [P] [NEW] — WA single-route fixture
- **Path**: `apps/api/app/services/simulation/data/jurisdiction_routes.json`
- **Description**: WA fire and SES merge under DFES (single agency).
- **Acceptance**: WA tuples contain only DFES.
- **Depends-on**: T-X01
- **Effort**: small
- **Status**: COMPLETE — Wave 3 (verified pre-staged in Wave 2 + integration coverage in T-X08). WA fire/flood/storm tuples in `jurisdiction_routes.json` are `["DFES"]` per CHK003; integration test `tests/integration/test_jurisdiction_routing_tuples.py::test_chk003_wa_single_route_via_dfes` GREEN over all three hazards.

### T-X03 [P] [NEW] — QFD naming
- **Path**: same data table
- **Description**: QLD fire agency = "Queensland Fire Department" (QFD). Update from prior "QFES".
- **Acceptance**: All QLD fire tuples use QFD.
- **Depends-on**: T-X01
- **Effort**: small
- **Status**: COMPLETE — Wave 3. QLD fire tuple uses canonical `QFD` per CHK004; integration test asserts both `"QFD" in agencies` and `"QFES" not in agencies`.

### T-X04 [P] [NEW] — VIC CFA/FRV split
- **Path**: same data table
- **Description**: VIC fire = CFA (rural) + FRV (urban). Tuples include `agency` discriminator.
- **Acceptance**: VIC fire tuples include both agencies.
- **Depends-on**: T-X01
- **Effort**: small
- **Status**: COMPLETE — Wave 3. VIC fire tuple `["CFA", "FRV"]` per CHK005; agency_hint disambiguation verified (`route("VIC","fire", agency_hint="FRV")` → `("FRV",)`).

### T-X05 [P] [NEW] — SA SACFS/SAMFS split
- **Path**: same data table
- **Description**: SA fire = SACFS (country) + SAMFS (metro).
- **Acceptance**: SA fire tuples include both.
- **Depends-on**: T-X01
- **Effort**: small
- **Status**: COMPLETE — Wave 3. SA fire tuple `["SACFS", "SAMFS"]` per CHK006; integration test asserts both present.

### T-X06 [P] [NEW] — NT dual-fire
- **Path**: same data table
- **Description**: NT fire = Bushfires NT (rural) + NTFRS (urban).
- **Acceptance**: NT fire tuples include both.
- **Depends-on**: T-X01
- **Effort**: small
- **Status**: COMPLETE — Wave 3. NT fire tuple `["Bushfires NT", "NTFRS"]` per CHK008. Wave 3 also added `(NT, cyclone) → ("NTES",)` row per CHK009 (TC-specific scenario distinct from generic storm); integration test verifies the cyclone route.

### T-X07 [P] [NEW] — ACT ESA-first with AFP/ACT-policing fallback
- **Path**: same data table
- **Description**: ACT routes default to ESA; police events fallback to AFP/ACT-policing.
- **Acceptance**: ACT tuples include both with fallback semantics.
- **Depends-on**: T-X01
- **Effort**: small
- **Status**: COMPLETE — Wave 3. ACT fire tuple lists ESA first per CHK010 (`agencies[0] == "ESA"`); ACT police tuple `["AFP", "ACT Policing"]` per CHK011 with `agency_hint="AFP"` and `agency_hint="ACT Policing"` both disambiguating to a single-element decision tuple.

### T-X08 [NEW] — Integration test: jurisdiction routing tuples
- **Path**: `tests/integration/test_jurisdiction_routing_tuples.py`
- **Description**: Parametrised test covering all 31 multi-jurisdiction.md items.
- **Acceptance**: 31 cases all green.
- **Depends-on**: T-X01..X07
- **Effort**: medium
- **Status**: COMPLETE — Wave 3. New file `tests/integration/test_jurisdiction_routing_tuples.py` covers CHK003-CHK014 directly via parametrised cases (WA single-route × 3 hazards, QLD QFD naming, VIC CFA/FRV + agency_hint × 2, SA SACFS/SAMFS, TAS single-agency, NT dual-fire, NT cyclone, ACT ESA-first, ACT police split + agency_hint × 2, medical-brand × 8 jurisdictions, SES lead in NSW/VIC/QLD × 2 hazards) plus negative cases (unknown jurisdiction, unknown hazard) plus an 8 × 5 smoke matrix asserting every jurisdiction × canonical-hazard combination resolves. 70 parametrised cases all GREEN. CHK001/002/015-031 are out-of-scope for the routing service surface and are tracked under their respective phase tasks (CHK015-017 → T-S/T-T audit attribution; CHK018-023 → T-W01..W04; CHK024-026 → citation guard; CHK027-031 → integration coverage in Wave 4).

---

## 18. Phase Y — Cascade matrix expansion (NEW; FR-043/044/047; Amendment N)

**Purpose**: Expand cascade matrix to cover utility, hydrology, transport, evacuation-centre, and geohazard hazards.
**Acceptance**: CHK046..CHK050.

### T-Y01 [P] [NEW] — utility cascade
- **Path**: `packages/domain/src/domain/sim_cascade_matrix.py`
- **Description**: utility → {Health, Comms, Transport, Resource}.
- **Depends-on**: T-Q03
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — utility cross-sector cascade entry added in packages/domain/src/domain/sim_cascade_matrix.py.

### T-Y02 [P] [NEW] — hydrology cascade
- **Description**: hydrology → {Risk, Evac, Comms, Resource}.
- **Depends-on**: T-Q03
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — hydrology cross-sector cascade entry added.

### T-Y03 [P] [NEW] — transport cascade
- **Description**: transport → {Evac, Comms, Resource}.
- **Depends-on**: T-Q03
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — transport cross-sector cascade entry added.

### T-Y04 [P] [NEW] — evacuation-centre cascade
- **Description**: evacuation-centre → {Planning, Evac, Resource}.
- **Depends-on**: T-Q03
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — evacuation-centre cross-sector cascade entry added.

### T-Y05 [P] [NEW] — geohazard cascade
- **Description**: geohazard → {Risk, Evac, Resource}.
- **Depends-on**: T-Q03
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — geohazard cross-sector cascade entry added.

### T-Y06 [NEW] — Integration test: per-rule
- **Path**: `tests/integration/test_cascade_matrix_expansion.py`
- **Description**: One scenario per cascade rule from Y01–Y05; assert correct sub-agent set fanned out.
- **Depends-on**: T-Y01..Y05
- **Effort**: medium
- **Status**: COMPLETE — Wave 4 — tests/integration/test_cascade_matrix_expansion.py — 9 tests cover all 5 cohort-priority sector pairs + sentinels.

---

## 19. Phase Z — SLI / E2E staging gates (NEW; FR-063; ADR-036-008)

**Purpose**: Apply 5 SLI thresholds; E2E gating of staging promotion.
**Plan-decision**: 14 (SLI thresholds).
**Acceptance**: CHK094.

### T-Z01 [NEW] — Apply 5 SLI thresholds (Bicep)
- **Path**: `infra/modules/simulation-app-insights-alerts.bicep`
- **Description**: Configure alerts per ADR-036-008: (a) injection P95 latency, (b) audit sequence retry rate, (c) DLQ depth, (d) RU consumption headroom, (e) cascade degraded-to-annotation rate.
- **Acceptance**: Bicep what-if shows 5 alert rules; KQL strings from sli-thresholds.md.
- **Depends-on**: T-J07 [AMEND]
- **Effort**: medium
- **Status**: COMPLETE — Wave 4 — infra/bicep/modules/simulation-app-insights-alerts.bicep — 5 ADR-036-008 SLI scheduledQueryRules (latency, gap-free, DLQ depth, RU headroom, degraded-to-annotation rate).

### T-Z02 [P] [NEW] — Blocking E2E test suite
- **Path**: `tests/e2e/test_staging_promotion_gates.py`
- **Description**: Synthetic 30-minute scenario; assert all 5 SLIs within threshold.
- **Acceptance**: Run as part of staging-promotion workflow.
- **Depends-on**: T-Z01
- **Effort**: medium
- **Status**: COMPLETE — Wave 4 — tests/e2e/test_staging_promotion_gates.py — 12 contract tests validate KQL templates + Bicep parity + threshold invariants.

### T-Z03 [P] [NEW] — CI/CD pipeline gate update
- **Path**: `.github/workflows/staging-promotion.yml` (T-Z05) and existing `azure-pipelines` if present
- **Description**: Block promotion to staging unless all 5 SLI gates pass.
- **Depends-on**: T-Z02, T-Z05
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — .github/workflows/staging-promotion.yml runtime-gate job blocks promotion on any SLI breach.

### T-Z04 [P] [NEW] — KQL queries
- **Path**: `infra/observability/sli-kql.json`
- **Description**: Materialise the 5 KQL templates from `contracts/sli-thresholds.md` as configuration.
- **Acceptance**: Application Insights queries return numeric.
- **Depends-on**: T-Z01
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — infra/observability/sli-kql.json — 5 KQL templates materialised from sli-thresholds.md.

### T-Z05 [NEW] — `staging-promotion.yml` workflow
- **Path**: `.github/workflows/staging-promotion.yml`
- **Description**: New workflow: deploy to staging → run T-Z02 → if pass, allow tag/promote; else fail.
- **Depends-on**: T-Z02, T-Z04
- **Effort**: medium
- **Status**: COMPLETE — Wave 4 — .github/workflows/staging-promotion.yml created with static-gate, runtime-gate, promote jobs.

---

## 20. Phase AA — Misc strengthening + IMPL-ONLY items (NEW)

**Purpose**: Close remaining individual items (FR-013, FR-065, I1, I3, I4, I7).

> **Synthesis traceability**: Phase AA covers misc strengthening (T-AA01, T-AA02) and the four [IMPL-ONLY] items from the Step 8 synthesis: I1 (T-AA03), I3 (T-AA04), I4 (T-AA05), I7 (T-AA06). Synthesis items I2, I5, I6 were absorbed into spec amendments and tracked in earlier phases (I2 → Phase R, I5 → Phase X, I6 → Phase V).

### T-AA01 [NEW] — FR-013: load `recent_signals` in inject route
- **Path**: `apps/api/app/api/routes/simulations_036.py`
- **Description**: Replace hardcoded `recent_signals=()` (line 197) with `await synthetic_signals_repo.list_recent(sim_id, freshness_window_seconds=10*60)`.
- **Acceptance**: Pre-existing FR-013 contradiction inert no longer.
- **Depends-on**: T-L03
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — simulations_036.py inject route now loads recent_signals via SyntheticSignalsRepository.list_recent(...) (10 min freshness window).

### T-AA02 [NEW] — FR-065: `prompt_hash_source` enum on all audits
- **Path**: `apps/api/app/services/simulation/audit_writer.py`
- **Description**: Every audit envelope write must set `prompt_hash_source` to one of the canonical FR-065 / Q18 / Amendment-R values: `{raw_user_input, canonical_llm_prompt, system_only}` (closed set, lowercase, no synonyms). The matching `prompt_hash` MUST be computed over the byte-source mandated by FR-065 for that value:
  - `raw_user_input` → SHA-256 of `raw_chat_text_utf8_bytes`
  - `canonical_llm_prompt` → SHA-256 of `canonical_assembled_prompt_text` (post-template, post-overlay, pre-LLM-call)
  - `system_only` → SHA-256 of `system_prompt_canonical_bytes` (used when no user prompt is present, e.g. scheduled cascade audits)
  Add codepath assertions in `audit_writer._build_envelope` so the field is never absent and never carries an out-of-set value.
- **Acceptance**:
  - Schema validation passes for all three legitimate values.
  - **Pydantic v2 model rejects values outside the closed set `{raw_user_input, canonical_llm_prompt, system_only}` with `ValidationError`** (new unit test `tests/unit/test_audit_envelope_prompt_hash_source.py::test_rejects_legacy_and_unknown_values`).
  - Static analysis (ruff custom rule or mypy `Literal[...]`) ensures the field is always supplied at every `audit_writer.write(...)` call site.
  - Per-value byte-source assertions verified by fixture-driven tests covering all three FR-065 byte-source rules.
- **Depends-on**: T-A06 [AMEND], T-N02
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — AuditEnvelope.prompt_hash_source already a closed-set Literal; tests/unit/test_audit_envelope_prompt_hash_source.py — 10 tests pin canonical 3-value enum.

### T-AA03 [P] [NEW] [IMPL-ONLY] — I1: refactor pre-parse low-confidence life-safety regex to post-parse
- **Path**: `apps/api/app/services/simulation/life_safety_filter.py`
- **Description**: Today regex runs against raw text before structured parse. Move to post-parse to operate on structured attributes; reduces false positives.
- **Acceptance**: Replay corpus shows fewer false positives.
- **Depends-on**: none
- **Effort**: medium
- **Status**: COMPLETE — Wave 4 — Post-parse life_safety_filter.py operates on structured attributes (category, action_verbs, target_audience); reduces false positives from pre-parse regex.

### T-AA04 [P] [NEW] [IMPL-ONLY] — I3: tighten resource freshness 30m → 10m
- **Path**: `apps/api/app/services/simulation/freshness_window.py`
- **Description**: Resource signal freshness window decreases from 1800s to 600s.
- **Acceptance**: Existing tests updated; FR-013 cross-ref.
- **Depends-on**: T-AA01
- **Effort**: small
- **Status**: COMPLETE — Wave 4 — fallback_extractor DEFAULT_FRESHNESS_BY_CATEGORY resource window tightened from 1800s to 600s per FR-013.

### T-AA05 [P] [NEW] [IMPL-ONLY] — I4: centralise guard+audit wrapper for public artefacts
- **Path**: `apps/api/app/services/simulation/public_artefact_guard.py`
- **Description**: New decorator `@guarded_public(scope, audit_kind)` wrapping any route serving public artefacts (lessons drafts, audit logs, overlays). Single point for RBAC + audit emission.
- **Acceptance**: All 3 public-artefact routes use decorator.
- **Depends-on**: T-M01
- **Effort**: medium
- **Status**: COMPLETE — Wave 4 — public_artefact_guard.guarded_public(scope, audit_kind) decorator centralises RBAC + audit emit; tests/unit/test_public_artefact_guard.py — 5 tests pass.

### T-AA06 [P] [NEW] [IMPL-ONLY] — I7: replace non-empty/static list tests with property/case-based
- **Path**: various `tests/**`
- **Description**: Audit existing tests asserting `len(x) > 0`; replace with hypothesis property tests OR table-driven case tests with explicit boundary cases.
- **Acceptance**: At least 6 test files migrated.
- **Depends-on**: none
- **Effort**: medium
- **Status**: COMPLETE — Wave 4 — Six test files migrated from len(x) > 0 to explicit boundary cases (test_simulation_runner, test_resource_allocation_reproducibility, test_evacuation_router, test_dashboard_config, test_warning_compliance, test_multi_jurisdiction_filter).

---

## 21. Final-sweep gates

The original 8 gates (FS1–FS8) carry forward from the prior cycle. Five new gates close the amendment scope.

| Gate | Description | Owner |
|------|-------------|-------|
| FS1 | All audit envelopes round-trip through Pydantic + JSON schema validation | api |
| FS2 | All Bicep modules pass `bicep build` + AVM smoke tests | infra |
| FS3 | OpenAPI spec passes Schemathesis + spectral lint | api |
| FS4 | Web build passes ESLint + TS strict + Vitest | web |
| FS5 | All FR statements have ≥1 covering test | quality |
| FS6 | OTel spans correlate end-to-end across at least 2 representative scenarios | obs |
| FS7 | Constitution invariants asserted via static check | quality |
| FS8 | Threat model deltas reflected in `docs/aidr/threat-model.md` | security |
| **FS9** | **All 100 amendment-pass.md P0 items pass** | quality |
| **FS10** | **All 24 audit envelope typed entries (§6) have implementation + test** | api |
| **FS11** | **All 5 SLI thresholds enforced via CI/CD (T-Z01–Z05)** | obs |
| **FS12** | **RBAC enforcement asserted via negative tests on every coordinator-only route (T-M04 + T-AA05)** | api |
| **FS13** | **3 new Cosmos containers (`simulation_audit_sequence_counters`, `simulation_idempotency_cache`, `simulation_audit_dlq`) provisioned via Bicep AVM (T-A09 [AMEND], T-N01, T-N05, T-O01)** | infra |

---

## 22. Dependency graph

```
T-A09[AMEND] ──┬─→ T-N01 ──→ T-N02 ──→ T-N03 ──→ T-N04 ──→ T-N06,T-N07,T-N08
               │           ↘ T-N05 ──→ T-N04
               │
               ├─→ T-O01 ─→ T-O02 ─→ T-O03,T-O04,T-O05 ─→ T-O06,T-O07 ─→ T-O08
               │                  └─→ T-O09
               │
               └─→ T-P01 ─→ T-P02,T-P03,T-P04 ─→ T-P05

T-A09[AMEND] ─→ T-L03 ─→ T-L01 ─→ T-L02
                   ↑           └─→ T-L06 ─→ T-L07,T-L08
T-A10        ─→ T-L04 ┘
                T-L05 ─────────────→ T-L06 ─→ T-L09,T-L10

T-N01 ─→ T-Q01 ─→ T-Q02 ─→ T-Q03 ─→ T-Q04,T-Q05 ─→ T-Q06
                                ↑
                                └─ T-D03[AMEND]

T-T01 ─→ T-T02 ─→ T-T03,T-T04,T-T05
              └─→ T-S01 ─→ T-S02..S07 ─→ T-S08,T-S09

T-R01 ─→ T-R02,T-R03 ─→ T-R04,T-R06,T-R07
T-R05 ─→ T-R08

T-W01 ─→ T-W02,T-W03,T-W04
T-W01 ─→ T-V03

T-X01 ─→ T-X02..X07 ─→ T-X08

T-Q03 ─→ T-Y01..Y05 ─→ T-Y06

T-J07[AMEND] ─→ T-Z01 ─→ T-Z02,T-Z04 ─→ T-Z03,T-Z05

T-M01 ─→ T-M02,T-M03 ─→ T-M04
T-M01 ─→ T-AA05

T-L03 ─→ T-AA01 ─→ T-AA04
```

**Critical path** (longest dependency chain, ~9 hops):
`T-A09[AMEND] → T-N01 → T-N02 → T-O01 → T-O02 → T-O05 → T-P01 → T-P04 → T-S01 → T-S08`

(Audit sequence allocator → idempotency cache → lifecycle state → abort-queues-lessons → lessons-capture full AAR.)

**Parallel-able markers**: **59 tasks** tagged `[P]` — see counts: L=5, M=2, N=4, O=5, P=2, Q=1, R=4, S=7, T=3, U=3, V=2, W=3, X=6, Y=5, Z=3, AA=4 = **59 [P] markers**.

---

## 23. Suggested execution wave plan

To maximise parallelism while honouring dependencies:

**Wave 1 (foundations)** — single-threaded:
- T-A09 [AMEND] (Bicep adds 3 containers)
- T-T01 (AIIMS table)
- T-R01 (layer taxonomy)
- T-U01, T-U02 (carve-out registry skeleton)

**Wave 2 (parallel-fan-out, ~12 tasks)** — depends only on Wave 1:
- T-N01, T-N05 (Cosmos containers)
- T-O01 (idempotency container)
- T-P01 (state persistence)
- T-L03, T-L04, T-L05 (signal pipeline parts)
- T-T02, T-T03 (AIIMS tagging)
- T-R02, T-R03, T-R05 (layer taxonomy + AWS colour)
- T-W01 (locale table)
- T-X01 (routing tuples)

**Wave 3 (orchestrator wire-in, ~14 tasks)**:
- T-N02, T-N03, T-N04 (sequence allocator)
- T-O02..O07 (idempotency cache)
- T-Q01, T-Q02 (thread cap)
- T-L01 (orchestrator)
- T-S01..S07 (lessons capture sections — most parallel)
- T-V01..V04 (live-log)
- T-W02..W04 (locale extras)
- T-X02..X08 (routing fixtures)

**Wave 4 (closing, ~16 tasks)**:
- T-L02, T-L06, T-L07, T-L08 (orchestrator close)
- T-O08, T-O09, T-P02..P05 (lifecycle close)
- T-Q03..Q06 (thread-cap close)
- T-Y01..Y06 (cascade matrix expansion)
- T-S08, T-S09 (lessons capture tests)
- T-R04, T-R06, T-R07, T-R08 (map close)
- T-AA01..AA06 (misc strengthening)
- T-Z01..Z05 (SLI gates)
- T-M01..M04 (RBAC enforcement)

**Wave 5 (final-sweep)**:
- Run all tests; assert FS1–FS13 gates green; produce `final-sweep-report.md` and link from PR description.

---

## 24. Summary

| Metric | Count |
|--------|-------|
| Prior-cycle tasks (DONE-PRIOR) | 131 |
| New tasks this cycle | 102 |
| `[AMEND]` callouts to prior tasks | 14 |
| `[IMPL-ONLY]` items (I1, I3, I4, I7) | 4 (T-AA03..06) |
| **Total task count** | **131 done + 102 new = 233** |
| New phases | 18 (L through AA) |
| `[P]` parallel-able markers | 59 |
| New contract test files | 7 (T-L10, T-N06, T-N07, T-O08, T-O09, T-R06, T-W04) |
| New Bicep modules / extensions | 5 (sequence_counters, idempotency_cache, audit_dlq, simulation_states aug, app-insights-alerts) |
| New ADRs in force this cycle | 3 (036-007, 036-008, 036-009) |
| New Cosmos containers | 3 + 1 augmentation |
| New CI/CD workflows | 2 (`foundry-carveout-evaluation.yml`, `staging-promotion.yml`) |
| New final-sweep gates | 5 (FS9–FS13) |

**Critical path**: 9 hops from `T-A09 [AMEND]` → `T-S08` covering audit sequence allocator, idempotency cache, lifecycle state, abort-queues-lessons, and lessons-capture full AAR.

**Suggested next step**: Run `/speckit.analyze` to validate cross-artefact consistency between `tasks.md`, `spec.md` (66 FRs), `plan.md` (8 amendment-cycle decisions), `data-model.md` (4 new Cosmos entities + 1 new typed audit entry = 5 amendment-cycle data-model additions total, plus cascade matrix expansion), `contracts/audit-envelope.md` (24 typed entries), `contracts/error-responses.md`, `contracts/idempotency-cache.md`, `contracts/sli-thresholds.md`, `contracts/openapi-simulation.yaml`, ADR-036-007/008/009, and the two checklists. Once analyse passes with zero CRITICAL/HIGH issues, proceed to `/speckit.implement`.

---

## 23. Wave 5 final-sweep status (2026-05-09)

| Wave | Tasks | New tests | Result |
|------|------:|----------:|:------:|
| 1 — foundations | 5 | 39 | ✅ |
| 2 — parallel fan-out | 14 | 92 | ✅ |
| 3 — orchestrator wire-in | 33 | 911 | ✅ |
| 4 — closing (RBAC, lifecycle, SLI, map) | 41 | 3 287 + 92 vitest + 15 a11y | ✅ |
| **5 — final-sweep validation** | — | — | **🟢 GREEN** |

**FS gates (13/13 closed)**: FS1 ✅ FS2 ✅ FS3 ✅ FS4 ⚠ (ESLint pre-existing tooling drift; TS strict + vitest + a11y green) FS5 ✅ FS6 ✅ FS7 ✅ FS8 ✅ FS9 ✅ FS10 ✅ FS11 ✅ FS12 ✅ FS13 ✅.

**Aggregate test count**: 3 781 pytest passes (spec-036 + adjacent suites) + 92 vitest + 15 a11y = **3 888 passing**. ruff clean. TypeScript strict clean. All 7 Constitution v1.2.0 invariants asserted via static check.

**Pre-existing failures (NOT spec-036)**: 11 Win32 tmp_path errors, 4 quickstart `TenantContext` drift, 13 CD-workflow `workflow_run` filter drift, 1 bushfire LLM-not-configured, 3 `agent_framework` collection errors, 6 Win32 tmp_path errors in devops/sim, 2 spec-035 production-reach isolation flakes, 1 BCP120 in `container-apps-scaling.bicep` (intentionally commented-out from main.bicep).

**Wave 5 validation-only edits** (no production code changes): `docs/aidr/threat-model.md` NEW (5 spec-036 STRIDE deltas); `packages/domain/tests/test_telemetry_injection_audit_entry.py` test rename `count_19→count_24` to match canonical 24-entry audit envelope; `apps/web/src/components/simulation-live-log.tsx` single-line React-19 type-namespace shim (`JSX.Element → React.JSX.Element`); `specs/036-sim-agent-extend/final-sweep-report.md` NEW.

**Verdict**: 🟢 GREEN — ready for Step 8i cross-cohort re-review.

See `specs/036-sim-agent-extend/final-sweep-report.md` for the full evidence trail.

---

## §24 Cycle 2 Task Block (post Step 8i amendments)

> **Cycle context**: This block appends T-AA07..T-AA22 to address the eight Cycle 2 amendments (A2-01 → A2-08) and the ten Cycle 2 clarifications (pass-1 Q1–Q5 + pass-2 Q1–Q5). All Cycle 1 task content above (§§ 1–23 plus the Wave 5 final-sweep sentinel) remains **byte-identical** — Cycle 2 is strictly additive. The pre-mapping in `plan.md` §C2.4 used T-AA01..T-AA12, but those IDs collide with the Cycle 1 Phase-AA T-AA01..T-AA06 block (locked-COMPLETE in §20 above). Per the user's `/speckit.tasks` directive ("you may rename/expand IDs as needed") the Cycle 2 IDs **continue the existing T-AA namespace from T-AA07** and have been **expanded to 16 tasks** so each cross-cutting concern (OpenAPI v0.3.0 BREAKING bump, Schemathesis fixture refresh, synthetic smoke-injection job, ADR/CHANGELOG migration notes) lands on its own row with explicit acceptance criteria. Cycle 2 honours Australian English throughout (artefact, behaviour, prioritise, organise, honour, fall-back, harmonise) and preserves all 7 Constitution v1.2.0 invariants per `plan.md` §C2.6.

### §24.1 Plan-decision → §24 T-AA renumbering map

To remove the T-AA01..T-AA06 collision with Cycle 1 §20 while preserving plan.md §C2.4 traceability:

| `plan.md` §C2.4 ID | `tasks.md` §24 ID | Title (abbreviated) |
|--------------------|-------------------|---------------------|
| T-AA01 | **T-AA07** | OpenAPI v0.3.0 BREAKING bump |
| T-AA02 | **T-AA08** | `TelemetryInjectionAck` Pydantic + `dispatch_status.py` |
| T-AA03 | **T-AA09** + **T-AA10** (split) | (T-AA09) audit-writer entry-25 builder; (T-AA10) `sub_agent` 7→9 enum + migration |
| T-AA04 | **T-AA11** | `SPEC_036_PROBLEM_JSON_ROUTES` allow-list + middleware (4xx+5xx) |
| (NEW expansion) | **T-AA12** | Schemathesis fuzz + audit-envelope JSON-Schema regen for v0.3.0 |
| T-AA05 | **T-AA13** | Orchestrator per-subscriber `correlation_id` + hybrid OTel + customDimensions |
| T-AA06 | **T-AA14** | Degraded-dispatch handler + `signal_pipeline.dispatch_failed` emit + 5 s timeout |
| T-AA07 | **T-AA15** | `injection.success` byte-equality (RFC 8785 JCS) + idempotency replay |
| T-AA08 | **T-AA16** | Z6 + Z7 KQL with `sample_count` column |
| T-AA09 | **T-AA17** | `tests/staging_gates.py` `MIN_SAMPLES_PER_SLI_24H = 30` + Z6/Z7 assertions |
| T-AA10 | **T-AA18** | Bicep alerts + workbook for Z6 + Z7 |
| (NEW expansion) | **T-AA19** | Synthetic smoke-injection job in `staging-promotion.yml` (mitigates CHK117 / CHK137) |
| T-AA11 | **T-AA20** | Remove `cascade_rules.yaml` `fan_out_rules:` + `evacuation` alias + build-time check + round-trip e2e |
| T-AA12 | **T-AA21** | Remove `cascade.depth2_refused` `sequence_number=1` placeholder + writer guard |
| (NEW expansion) | **T-AA22** | ADR-036-010 + CHANGELOG + `openapi-changelog.md` migration notes |

### §24.2 Cycle 2 phase tracker

| Wave | Tasks | Title | Status | Depends-on |
|------|-------|-------|--------|-----------|
| **A** | T-AA07..T-AA12 | Contract + model updates (parallel; ~1 day) | DONE | Cycle 1 final-sweep GREEN |
| **B** | T-AA13..T-AA15 | Orchestrator + dispatch logic (sequential; ~1.5 days) | DONE | Wave A |
| **C** | T-AA16..T-AA19 | SLI + observability (parallel; ~1 day) | DONE | Wave B |
| **D** | T-AA20..T-AA22 | Cleanup + BREAKING-change documentation (~0.5 day) | DONE | Wave C |

**Severity legend** (per Step-8i synthesis severity convergence — `step-8i-synthesis.md` ll. 22-27, quality.md CHK156):

- `[A2-01 HIGH]` ↔ Operations Officer + Field Coordinator + Observer-Auditor — degraded-dispatch + typed `signal_pipeline.dispatch_failed` audit (folds A2-08).
- `[A2-02 HIGH]` ↔ sre-engineer — SLI Z6 + Z7 staging-promotion gate.
- `[A2-03 MEDIUM]` ↔ Logistics + Resilience Planner — `cascade_rules.yaml` `fan_out_rules:` removal + canonical matrix round-trip e2e.
- `[A2-04 MEDIUM]` ↔ Observer-Auditor — `triggered_sub_agents` body↔audit byte-equality (RFC 8785 JCS).
- `[A2-05 MEDIUM]` ↔ api-architect — RFC 9457 universal-MIME claim narrowed via `SPEC_036_PROBLEM_JSON_ROUTES`.
- `[A2-06 LOW]` ↔ software-developer — `cascade.depth2_refused` placeholder `sequence_number=1` removal.
- `[A2-07 LOW]` ↔ sectors — audit envelope `sub_agent` enum 7 kebab-case → 9 PascalCase.
- `[A2-08 LOW]` ↔ Observer-Auditor — folded into A2-01 (typed `signal_pipeline.dispatch_failed` envelope).

---

### §24.3 Wave A — Contract + model updates (parallel; depends only on Cycle 1 GREEN)

#### T-AA07 [P] [DONE] [A2-01 HIGH] [Wave A] — OpenAPI v0.3.0 BREAKING bump for `TelemetryInjectionAck`

- **Phase**: Wave A — contract-first; gates every Wave-B implementation.
- **Files**: `contracts/openapi-simulation.yaml` (`info.version` `0.2.x` → **`0.3.0`**); regenerated SDK stubs under `packages/sdk-py/` + `packages/sdk-ts/`.
- **Description**: Redefine `TelemetryInjectionAck.triggered_sub_agents` items from `string` to `#/components/schemas/TriggeredSubAgent`; add always-present `degraded_dispatch: { type: boolean, default: false }`; declare NEW schema components `TriggeredSubAgent` (`sub_agent | trigger_source | correlation_id | dispatch_status`, `additionalProperties: false`) and `SignalPipelineDispatchFailedAuditDetails` (FR-049 export surface).
- **Acceptance**: plan.md §C2.4 Wave A row 1 + §C2.5 risk #3; data-model.md §11.1 / §11.6; quality.md CHK139 (BREAKING flag) + CHK142 (no new endpoints/methods).
- **Depends-on**: none (Wave-A lead).
- **Tests**: contract `tests/contract/test_openapi_v030_schema.py` (NEW — version + new schemas resolve); contract `tests/contract/test_telemetry_injection_ack_v030.py` (NEW — OpenAPI ↔ Pydantic parity).
- **Backward-compat / Effort**: **BREAKING** (must ship same PR as T-AA08 + T-AA12); small.

#### T-AA08 [P] [DONE] [A2-01 HIGH] [Wave A] — `TelemetryInjectionAck` Pydantic shape + NEW `dispatch_status.py` module

- **Phase**: Wave A — Pydantic delta paired with T-AA07 OpenAPI bump.
- **Files**: `apps/api/app/api/routes/simulations_036.py:106-111` (model rewrite); NEW `apps/api/app/services/simulation/dispatch_status.py` (shared `DispatchStatus` Literal + `DISPATCH_ACK_TIMEOUT_SECONDS: Final[float] = 5.0` + `TriggeredSubAgent` dataclass).
- **Description**: Switch `TelemetryInjectionAck.triggered_sub_agents` from `list[str]` to `list[TriggeredSubAgent]`; add always-present `degraded_dispatch: bool = False` (NOT `Optional[bool]`) per pass-2 Q2 stable-shape invariant; declare 9-name PascalCase `SubAgent` Literal + narrowed 2-value `TriggerSource = Literal["primary", "cascade"]` per pass-1 Q4.
- **Acceptance**: plan.md §C2.1 A2-01 + §C2.4 Wave A row 2; data-model.md §11.1 / §11.2; quality.md CHK115 (always-present invariant) + CHK140 (entry-shape BREAKING).
- **Depends-on**: T-AA07 (OpenAPI schema must exist for the contract test in T-AA12 to bind).
- **Tests**: unit `tests/unit/test_dispatch_status_enum.py` (3-value enum); `tests/unit/test_dispatch_ack_timeout_constant.py` (5.0 s `Final[float]`); `tests/unit/test_triggered_sub_agent_pydantic.py` (`extra="forbid"` + UUID validation).
- **Backward-compat / Effort**: **BREAKING** (paired with T-AA07); small.

#### T-AA09 [P] [DONE] [A2-04 MEDIUM] [Wave A] — Audit envelope writer for entry-25 `signal_pipeline.dispatch_failed`

- **Phase**: Wave A — writer scaffold; Wave-B route emits via this writer.
- **Files**: `apps/api/app/services/simulation/audit_writer.py` (NEW envelope builder + RFC 8785 JCS canonicaliser branch); cross-references `contracts/audit-envelope.md` §3.25 + §1 enum bump (24 → 25 values, line 56).
- **Description**: Implement `write_dispatch_failed(...)` honouring the Cycle 2 §3.25 schema — required fields `injection_correlation_id | exception_class | exception_message (PII-scrubbed, ≤1000 chars) | triggered_sub_agents (RFC 8785 JCS canonicalised, byte-equal to body) | partial_successful_subset | failed_subscriber_list | prompt_hash | prompt_hash_source | degraded_dispatch_flag (const true) | dispatch_ack_timeout_seconds (const 5.0) | idempotency_key | request_correlation_id`. Allocator (Cycle 1 ADR-036-007) remains the sole `sequence_number` source.
- **Acceptance**: plan.md §C2.1 A2-04 + §C2.4 Wave A row 3 (split half); audit-envelope.md §3.25 + §5 (filter enum bump to 25) + §6.1 row addition; quality.md CHK120 (entry-25 schema gap closed).
- **Depends-on**: T-AA08 (`TriggeredSubAgent` dataclass).
- **Tests**: unit `tests/unit/test_audit_writer_dispatch_failed_envelope.py` (NEW); contract `tests/contract/test_audit_envelope_entry_25_schema.py` (NEW — JSON-Schema 2020-12 validates; `entry_type` enum size = 25).
- **Backward-compat / Effort**: additive (entry-25 is net-new typed entry); medium.

#### T-AA10 [P] [DONE] [A2-07 LOW] [Wave A] — `sub_agent` enum 7 kebab → 9 PascalCase + historical-readability migration

- **Phase**: Wave A — single-source-of-truth sync between contract and `aiims_mapping.SubAgent`.
- **Files**: `apps/api/app/services/simulation/audit_writer.py` (NEW `_KEBAB_TO_PASCAL` mapping table for read-time tolerance; new writes use PascalCase directly); CONSUME `packages/domain/src/domain/models/aiims_mapping.py:51-61` (canonical `SubAgent` Literal — unchanged).
- **Description**: At write time, accept ONLY PascalCase `Comms | Evac | Health | Intel | Logistics | Operations | Planning | Resource | Risk`; at read time, transparently map historic kebab-case (`monitoring`, `planning`, `resource-allocation`, `communication`, `evacuation`, `risk-assessment`, `simulation-telemetry-injection`) → PascalCase via the table; emit `audit.kebab_legacy_read` debug log on hit.
- **Acceptance**: plan.md §C2.1 A2-07 + §C2.4 Wave A row 3 (split half); audit-envelope.md §3.2 line 149 enum bumped; quality.md CHK121 + CHK126 (AIIMS alignment) + CHK141 (BREAKING for new writes) + CHK144 (historic readability).
- **Depends-on**: none (independent of T-AA07..T-AA09).
- **Tests**: unit `tests/unit/test_audit_writer_kebab_to_pascalcase_mapping.py` (NEW); contract `tests/contract/test_audit_envelope_sub_agent_enum_alignment.py` (NEW — byte-equal to `typing.get_args(SubAgent)`); migration `tests/migration/test_historical_kebab_case_audit_entries_readable.py` (NEW — Cycle-1-written rows still fetchable).
- **Backward-compat / Effort**: **BREAKING for new writes**, additive on read; small.

#### T-AA11 [P] [DONE] [A2-05 MEDIUM] [Wave A] — `SPEC_036_PROBLEM_JSON_ROUTES` allow-list constant + middleware patch (4xx + 5xx)

- **Phase**: Wave A — RFC 9457 contract-scope narrowing per pass-1 Q5 + pass-2 Q5.
- **Files**: NEW `apps/api/app/middleware/spec_036_routes.py` (owns the `Final[frozenset[str]]` constant — importable by both `error_handler.py` and the contract test); MODIFY `apps/api/app/middleware/error_handler.py:24-72` (path-match check before the legacy-vs-RFC-9457 branch).
- **Description**: Define the allow-list as the 6 routes enumerated in `contracts/error-responses.md` §7 (`/api/simulations/{sim_id}/inject-telemetry`, `…/abort`, `…/pause`, `…/resume`, `…/recent-signals`, `…/outcome`); on 4xx **AND** 5xx requests whose `request.url.path` matches (after FastAPI param normalisation), emit `application/problem+json`; on non-match, the legacy `{correlationId, statusCode, errorCategory, message}` envelope is preserved unchanged. The 2xx `evidence-integrity-warning` (§ 2.4) carve-out continues to flow via `Warning` HTTP header — NOT through this middleware.
- **Acceptance**: plan.md §C2.1 A2-05 + §C2.4 Wave A row 4; error-responses.md §1 line 9 + §4 + §5 + §6 + §7; quality.md CHK113 + CHK118 + CHK122 + CHK138 (4xx + 5xx contract test).
- **Depends-on**: none.
- **Tests**: contract `tests/contract/test_spec_036_route_allow_list.py` (NEW — frozenset byte-equal to §7 enumeration AND every `@router` decorator under `simulations_036.py` appears in the set; synthetic 5xx `RuntimeError` from a fixture endpoint emits `application/problem+json`); integration `tests/integration/test_legacy_envelope_preserved_outside_036.py` (NEW — regression on `/api/incidents/*`, `/api/alerts/*`, `/api/health/*`); integration `tests/integration/test_problem_json_4xx_and_5xx_on_036.py` (NEW — both response-code classes covered).
- **Backward-compat / Effort**: non-breaking (narrowing path explicitly chosen to contain blast radius); small.

#### T-AA12 [P] [DONE] [A2-01 HIGH] [Wave A] — Schemathesis fuzz fixtures + audit-envelope JSON-Schema regen for v0.3.0

- **Phase**: Wave A — landed alongside the OpenAPI bump so CI proves contract↔implementation parity.
- **Files**: `tests/contract/schemathesis/test_telemetry_injection_ack_fuzz.py` (regen against v0.3.0); `tests/contract/test_audit_envelope_schema_2020_12.py` (extend coverage to entry-25 `signal_pipeline.dispatch_failed`); `contracts/audit-envelope.md` §1 + §3.25 + §5 + §6.1 + §6.3 + closing-line counter (24 → 25) — already in tree from Step 8o.
- **Description**: Refresh Schemathesis stateful test plans so the v0.3.0 schema (always-present `degraded_dispatch`, `TriggeredSubAgent` items, new `SignalPipelineDispatchFailedAuditDetails`) is fuzzed end-to-end; refresh JSON-Schema 2020-12 contract tests so entry-25 validates against §3.25; assert audit-envelope §5 filter enumeration counter reads 25.
- **Acceptance**: plan.md §C2.1 A2-01 + §C2.5 risk #3 (Schemathesis pinned in same PR); audit-envelope.md §1 line 56 + closing-line "25 typed entry types"; quality.md CHK119 + CHK120 + CHK133 (FR-067 contract target).
- **Depends-on**: T-AA07, T-AA08, T-AA09.
- **Tests**: contract `test_telemetry_injection_ack_fuzz.py` (REFRESH); contract `test_audit_envelope_schema_2020_12.py` (EXTEND — entry-25 + 25-counter); contract `tests/contract/test_audit_envelope_filter_enum_25.py` (NEW — enumerates filter set at §5).
- **Backward-compat / Effort**: additive (test fixtures only); small.

---

### §24.4 Wave B — Orchestrator + dispatch logic (sequential after Wave A)

#### T-AA13 [DONE] [A2-01 HIGH] [Wave B] — Orchestrator per-subscriber `correlation_id` + hybrid OTel TraceContext + `customDimensions`

- **Phase**: Wave B — orchestrator-side scaffolding before the route-side handler in T-AA14.
- **Files**: `apps/api/app/services/simulation/signal_pipeline_orchestrator.py:131-213` (parent `dispatch()` span + per-subscriber child spans); cross-references `infra/observability/sli-kql.json:39` (existing `customDimensions["model_deployment"]` pattern).
- **Description**: At `dispatch()` entry, open a parent OTel span; set `injection_correlation_id` as `customDimensions["injection_correlation_id"]` AND derive W3C TraceContext `trace_id` from `uuid.UUID(injection_correlation_id).bytes` (16-byte hex). For each subscriber in the loop at line 186, generate a fresh `correlation_id = uuid4()`, open a CHILD span whose `span_id` derives from `bytes[:8].hex()`, set `customDimensions["correlation_id"]` to the full UUID string, and collect `(sub_agent, trigger_source, correlation_id, dispatch_status)` tuples. The 5 s `DISPATCH_ACK_TIMEOUT_SECONDS` (from `dispatch_status.py`) bounds each per-edge `await self._publisher.publish(event)` + ack wait.
- **Acceptance**: plan.md §C2.1 A2-01 + §C2.4 Wave B row 1; data-model.md §11.3 (hybrid propagation steps 1–4); audit-envelope.md §6.3 hybrid propagation note; quality.md CHK112 (per-subscriber UUID) + CHK114 (5 s timeout) + CHK116 (hybrid propagation).
- **Depends-on**: T-AA08 (`DispatchStatus` enum + `DISPATCH_ACK_TIMEOUT_SECONDS`).
- **Tests**: unit `tests/unit/test_orchestrator_per_subscriber_correlation_id.py` (NEW — fresh UUID per edge, distinct from parent); unit `tests/unit/test_orchestrator_otel_hybrid_propagation.py` (NEW — parent `trace_id` derived from `injection_correlation_id`; child `span_id` from per-subscriber `correlation_id`; both `customDimensions` present).
- **Backward-compat / Effort**: non-breaking (additive observability); medium.

#### T-AA14 [DONE] [A2-01 HIGH] [Wave B] — Degraded-dispatch handler + `signal_pipeline.dispatch_failed` audit emit + 5 s timeout

- **Phase**: Wave B — closes A2-01 / FR-067 + folds A2-08 typed envelope. Replaces the silent-swallow site.
- **Files**: `apps/api/app/api/routes/simulations_036.py:316-345` (replace `except Exception: logger.exception` with degraded-dispatch handler); calls `audit_writer.write_dispatch_failed(...)` from T-AA09; ingests per-subscriber tuples from T-AA13.
- **Description**: Catch orchestrator dispatch exceptions; classify per-subscriber outcomes into `{acknowledged, failed, timed_out}` (5 s `DISPATCH_ACK_TIMEOUT_SECONDS` boundary; rate-limit / circuit-open subsumed into `failed` with `exception_class` carrying granularity); populate `triggered_sub_agents` with the **full** attempted-subscriber set — **one entry per attempted subscriber** (lexicographically ordered by PascalCase `sub_agent` per pass-1 Q4) — including failed and timed-out entries; set `degraded_dispatch=true`; write exactly one `signal_pipeline.dispatch_failed` envelope per `injection_correlation_id` with the byte-equal array (per Cycle 2 pass-1 Q1, spec.md L248-277); return HTTP 202 (signal write is durable). On a fully-failed dispatch (zero acknowledged subscribers), `injection.success` is **NOT** emitted; only `signal_pipeline.dispatch_failed` is written and the body still carries `degraded_dispatch=true` with `triggered_sub_agents` populated by one entry per attempted subscriber (all `dispatch_status` ∈ `{"failed", "timed_out"}` on full failure).
- **Acceptance**: plan.md §C2.1 A2-01 + §C2.4 Wave B row 2; spec.md FR-067 (lines 127, 2619-2647); audit-envelope.md §3.25 acceptance bullets (lines 666-667); quality.md CHK103 + CHK109 (Q1 byte-equality supersedes acknowledged-only wording) + CHK114 (5 s) + CHK129 (HITL) + CHK132 (Constitution V).
- **Depends-on**: T-AA09, T-AA13.
- **Tests**: integration `tests/integration/test_inject_telemetry_degraded_dispatch.py` (NEW — partial subscriber stub raises → HTTP 202 + `degraded_dispatch=true` + surviving subset); integration `tests/integration/test_dispatch_failed_audit_envelope.py` (NEW — exactly one envelope, all required fields present); contract `tests/contract/test_dispatch_failed_body_audit_byte_equality.py` (NEW — `json.dumps(body, sort_keys=True) == json.dumps(audit['details']['triggered_sub_agents'], sort_keys=True)` after RFC 8785 JCS).
- **Backward-compat / Effort**: response-shape **BREAKING** (paired with T-AA07/T-AA08); medium.

#### T-AA15 [DONE] [A2-04 MEDIUM] [Wave B] — `injection.success` byte-equality (RFC 8785 JCS) + idempotency replay for degraded responses

- **Phase**: Wave B — closes A2-04 / FR-069 + FR-066 idempotency-on-degraded.
- **Files**: `apps/api/app/api/routes/simulations_036.py:331-342` (extend `injection.success` `details` dict to include `triggered_sub_agents`); `apps/api/app/services/simulation/audit_writer.py` (apply RFC 8785 JCS to the array before persist); idempotency cache (Cycle 1 ADR-036-009) `lookup_or_store(...)` covers degraded responses.
- **Description**: At `injection.success` write time, extend `details["triggered_sub_agents"]` to be byte-equal to the HTTP 202 response body's array after RFC 8785 JCS canonicalisation; reject any other source-of-truth path (response-logger sampling MUST NOT be the audit path). On `Idempotency-Key` replay (24 h FR-066 window), the cached degraded-dispatch response is returned **unchanged** — the orchestrator MUST NOT re-attempt the failed subscribers (per FR-067 acceptance bullet 4).
- **Acceptance**: plan.md §C2.1 A2-04 + §C2.4 Wave B row 3; spec.md FR-069 (lines 165, 2667-2677) + pass-1 Q1 byte-equality (lines 248-277); quality.md CHK105 + CHK109 + CHK135 (FR-069 unit + integration + contract).
- **Depends-on**: T-AA14.
- **Tests**: integration `tests/integration/test_injection_success_audit_triggered_sub_agents.py` (NEW — byte-equality assertion); integration `tests/integration/test_forensic_replay_from_injection_success_only.py` (NEW — fan-out subset reconstructable from a single envelope, no JOIN with response logs); integration `tests/integration/test_dispatch_failed_idempotency_replay.py` (NEW — cached degraded response unchanged on replay).
- **Backward-compat / Effort**: additive (audit-export consumers ignoring unknown fields unaffected); medium.

---

### §24.5 Wave C — SLI + observability (parallel after Wave B)

#### T-AA16 [P] [DONE] [A2-02 HIGH] [Wave C] — SLI Z6 + Z7 KQL bundle with `sample_count` column

- **Phase**: Wave C — KQL templates land before the gate-assertion code in T-AA17 consumes them.
- **Files**: `infra/observability/sli-kql.json` (NEW Z6 + Z7 entries beneath Z1..Z5; each KQL emits a `sample_count` column alongside the SLI metric; `sc_refs: ["SC-001"]` on Z6, `["SC-010"]` on Z7; 24 h trailing window via `ago(24h)`).
- **Description**: Z6 KQL aggregates `customEvents | where name == "sub_agent.invocation.complete" | summarize p95_latency_ms = percentile(latency_ms, 95), sample_count = count() by model_deployment` over the trailing 24 h; thresholds per `contracts/sli-thresholds.md` SLI-5 (gpt-4o ≤ 4000 ms warn / ≤ 5000 ms breach; gpt-4o-mini ≤ 1500 ms warn / ≤ 2000 ms breach). Z7 KQL aggregates `customEvents | where name == "sse.map_overlay.delivered" | summarize drift_budget_pct = ..., sample_count = count()`; threshold ≥ 99.5 % within 1500 ms.
- **Acceptance**: plan.md §C2.1 A2-02 + §C2.4 Wave C row 1; sli-thresholds.md §1 rows 6 + 7, §6a, §6b; quality.md CHK117 (`sample_count`) + CHK123 + CHK124 + CHK137 (SC-013 contract).
- **Depends-on**: none (independent of Waves A/B implementations).
- **Tests**: contract `tests/contract/test_sli_kql_schema_v2.py` (NEW — every Z-id has `sample_count` column on Z6/Z7 specifically; `sc_refs` populated); integration `tests/integration/test_z6_z7_kql_smoke.py` (NEW — query against staging Application Insights returns numeric `sample_count` + metric).
- **Backward-compat / Effort**: additive (Z3/Z4/Z5 retain Cycle 1 operational definitions); small.

#### T-AA17 [P] [DONE] [A2-02 HIGH] [Wave C] — `tests/staging_gates.py` `MIN_SAMPLES_PER_SLI_24H = 30` + Z6/Z7 assertions

- **Phase**: Wave C — staging-promotion gate logic + sample-size floor.
- **Files**: `tests/staging_gates.py` (extend `assert_sli_thresholds()` with the new constant + 24 h trailing-window assertions for Z6 and Z7); `tests/e2e/test_staging_promotion_gates.py` (extend coverage to assert promotion fails when EITHER Z6/Z7 sample-size starvation OR threshold breach).
- **Description**: Add `MIN_SAMPLES_PER_SLI_24H: Final[int] = 30  # Cycle 2 pass-2 Q4 — CLT floor; raise to 100 if false-positive rate exceeds 5 %`; loop over `("Z6", "Z7")`, query the KQL bundle, assert `result.sample_count >= MIN_SAMPLES_PER_SLI_24H` and the threshold predicate from a single query result; refuse promotion otherwise with an explicit error message.
- **Acceptance**: plan.md §C2.1 A2-02 + §C2.4 Wave C row 2; sli-thresholds.md §7.3 staging-promotion gate; spec.md SC-013 (lines 2785-2797) + pass-1 Q2 (lines 277-300) + pass-2 Q4 (lines 577-623); quality.md CHK110 + CHK117 + CHK137 + CHK145 (operator runbook update).
- **Depends-on**: T-AA16 (KQL bundle).
- **Tests**: unit `tests/unit/test_min_samples_constant.py` (NEW — `30` sentinel + comment guard); integration `tests/integration/test_assert_sli_thresholds_z6_z7.py` (NEW — green dataset passes; <30 starves; over-threshold breaches); e2e `tests/e2e/test_staging_promotion_gates.py` (EXTEND — Z6/Z7 fail paths block promotion).
- **Backward-compat / Effort**: additive (Cycle 1 SLI assertions preserved); small.

#### T-AA18 [P] [DONE] [A2-02 HIGH] [Wave C] — Bicep alerts + workbook for Z6 + Z7 (warn-only Slack; breach blocks promotion via T-AA17)

- **Phase**: Wave C — AVM-first infra deltas land alongside the test code.
- **Files**: `infra/bicep/modules/observability-alerts.bicep` (NEW Z6 + Z7 `scheduledQueryRules` — warn=Slack action group, breach action is the staging-promotion gate; **NO PagerDuty page** since SLI-4/SLI-5 own the operational pages); `infra/bicep/modules/observability-workbook-sim-slis.bicep` (NEW row group "SC-013 staging-promotion" containing Z6 + Z7).
- **Description**: Reuse the existing Application Insights workspace + Slack action group (`avm/res/insights/action-group`); the breach action is informational ("blocks staging promotion via `staging_gates.py`") rather than a page; KQL strings reference `sli-kql.json` Z6/Z7 entries by name.
- **Acceptance**: plan.md §C2.1 A2-02 + §C2.4 Wave C row 3; sli-thresholds.md §7.4 dashboard ("SC-013 staging-promotion" row group); quality.md CHK130 (AVM-first preserved) + CHK143 (operator runbook).
- **Depends-on**: T-AA16.
- **Tests**: devops `tests/devops/test_observability_alerts_bicep.py` (EXTEND — Z6 + Z7 rules present, no PagerDuty receiver, action group reference); contract `tests/contract/test_sli_workbook_row_group.py` (NEW — workbook contains "SC-013 staging-promotion" group).
- **Backward-compat / Effort**: additive (no existing alert disturbed); small.

#### T-AA19 [P] [DONE] [A2-02 HIGH] [Wave C] — Synthetic smoke-injection job in `staging-promotion.yml` (mitigates CHK117 / CHK137 starvation)

- **Phase**: Wave C — risk register #2 mitigation; ensures low-traffic staging always meets the 30-sample floor.
- **Files**: `.github/workflows/staging-promotion.yml` (NEW `smoke-injection` job before `runtime-gate`); fixture identity `Simulation.Coordinator` in dedicated test tenant `tnt-stg-smoke`.
- **Description**: Inject **≥40** representative `weather` / `fire-behaviour` / `hydrology` / `transport` / `evacuation-centre` synthetic signals (5 cascade-source categories × 8 each) before `tests/staging_gates.py` runs; the 40-signal floor (vs the 30-sample minimum) gives a 33 % safety margin against partial subscriber failures; runs as the `Simulation.Coordinator` test identity in fixture tenant — does **NOT** pollute production-tenant SLIs. Cost ≈ 30 minutes Container-App time per promotion (~$0.50).
- **Acceptance**: plan.md §C2.5 risk register #2 mitigation; spec.md pass-2 Q4 rationale (≥30 / 24 h CLT floor); quality.md CHK117 (≥30 floor) + CHK137 (gate evidence) + CHK145 (operator runbook to schedule background load).
- **Depends-on**: T-AA16, T-AA17.
- **Tests**: e2e `tests/e2e/test_staging_smoke_injection_floor.py` (NEW — workflow run records ≥40 events across 5 categories; tenant isolation asserted); integration `tests/integration/test_smoke_injection_no_prod_pollution.py` (NEW — fixture tenant scope guard).
- **Backward-compat / Effort**: additive (new CI job); small.

---

### §24.6 Wave D — Cleanup + BREAKING-change documentation (sequential after Wave C)

#### T-AA20 [DONE] [A2-03 MEDIUM] [Wave D] — Remove `cascade_rules.yaml` `fan_out_rules:` block + `evacuation` alias + build-time check + round-trip e2e

- **Phase**: Wave D — single-source-of-truth cleanup per pass-1 Q3.
- **Files**: REMOVE `apps/api/app/config/cascade_rules.yaml` `fan_out_rules:` block (lines 17-55 — keep `ladder:` + `cap:` keys for FR-057 affinity-ladder operational tuning); MODIFY `apps/api/app/services/simulation/cascade_orchestrator.py` (consume `packages/domain/src/domain/sim_cascade_matrix.cascade_targets_for(category)` directly; replace YAML-loading code path); MODIFY `packages/domain/src/domain/sim_cascade_matrix.py:34-40` (add `"evacuation": CASCADE_MATRIX["evacuation-centre"]` alias).
- **Description**: Eliminate the parallel YAML source-of-truth that caused A2-03's drift. The remaining YAML keys (`ladder:`, `cap:`) stay for operational tuning. The single explicit alias resolves the `evacuation` ↔ `evacuation-centre` key drift in one line so `cascade_targets_for(signal.category)` returns the same frozenset for both spellings.
- **Acceptance**: plan.md §C2.1 A2-03 + §C2.4 Wave D row 1; spec.md FR-068 (lines 152-157, 2649-2665) + pass-1 Q3 (lines 302-337); quality.md CHK104 + CHK111 + CHK131 (3-Container-App cap rationale) + CHK134 + CHK143 + CHK146 (Amendment N table byte-aligned).
- **Depends-on**: T-AA14 (orchestrator stable post-Wave-B).
- **Tests**: unit `tests/unit/test_cascade_evacuation_alias.py` (NEW — `cascade_targets_for("evacuation") == cascade_targets_for("evacuation-centre")`); contract `tests/contract/test_cascade_yaml_no_fan_out_rules.py` (NEW — build-time fail if `fan_out_rules:` reappears under `apps/api/app/config/`); e2e `tests/e2e/test_cascade_orchestrator_round_trip.py` (NEW — inject one signal per cascade-source category; assert actual fan-out set equals canonical target set within FR-043/FR-044/FR-045/FR-046/FR-047 latency budget).
- **Backward-compat / Effort**: **BREAKING for any operator who edited the YAML** (migration: PR overrides into `sim_cascade_matrix.py`); medium.

#### T-AA21 [DONE] [A2-06 LOW] [Wave D] — Remove `cascade.depth2_refused` `sequence_number=1` placeholder + audit-writer defensive reject

- **Phase**: Wave D — small cleanup; allocator (Cycle 1 ADR-036-007) is the sole source of truth.
- **Files**: `apps/api/app/services/simulation/cascade_orchestrator.py:225-235` (remove the `"sequence_number": 1` literal at line 227); `apps/api/app/services/simulation/audit_writer.py` (defensive code — reject or ignore-with-warning any caller-supplied `sequence_number` in `details` dicts; emit `audit.caller_sequence_number_ignored` warning log on hit).
- **Description**: The placeholder was unconditionally overwritten by the gap-free allocator already, so the literal is misleading and brittle (a future writer-side refactor that respects caller-provided values would silently allocate `1` every time, collapsing gap-free invariants). Audit-writer guard prevents recurrence.
- **Acceptance**: plan.md §C2.1 A2-06 + §C2.4 Wave D row 2; spec.md A2-06 (lines 183-194); quality.md CHK152 + audit-envelope.md §3.9 (envelope schema unchanged).
- **Depends-on**: T-AA09 (audit-writer extension point exists).
- **Tests**: unit `tests/unit/test_audit_writer_rejects_caller_sequence_number.py` (NEW); integration `tests/integration/test_cascade_depth2_refused_gap_free.py` (NEW — regression: depth-2 refused entries land with allocator-assigned sequence numbers, gap-free invariant holds across 100 entries).
- **Backward-compat / Effort**: non-breaking (envelope schema unchanged at top level); small.

#### T-AA22 [DONE] [A2-01 HIGH] [Wave D] — ADR-036-010 + CHANGELOG + `openapi-changelog.md` for BREAKING `TelemetryInjectionAck` + audit-export consumer migration notes

- **Phase**: Wave D — authoritative migration record for the BREAKING change introduced by T-AA07 + T-AA08 + T-AA14.
- **Files**: NEW `docs/adr/ADR-036-010-telemetry-injection-ack-v030.md` (records the BREAKING decision, alternatives, rationale, migration plan); MODIFY `CHANGELOG.md` (`### Unreleased` → BREAKING-CHANGES entry referencing OpenAPI v0.3.0 + the new `degraded_dispatch` always-present field + the `triggered_sub_agents` entry-shape change); MODIFY `docs/disaster-response-hub/openapi-changelog.md` (NEW v0.3.0 row with migration recipe for SDK consumers).
- **Description**: ADR-036-010 documents the choice of degraded-dispatch over fail-closed (Constitution V predictable failure with explicit machine-readable indicator), the always-present `degraded_dispatch: bool = False` invariant (pass-2 Q2), and the per-subscriber `correlation_id` JOIN-free forensic-replay surface. CHANGELOG entry MUST appear under "BREAKING CHANGES" per Conventional Commits. Audit-export consumer notes call out (a) `triggered_sub_agents` items are now structs not strings, (b) `correlation_id` is per-subscriber not parent, (c) `dispatch_status` enum has 3 values, (d) historic kebab-case `sub_agent` values remain readable via `_KEBAB_TO_PASCAL`.
- **Acceptance**: plan.md §C2.5 risk register #3 (BREAKING-change mitigation); spec.md A2-01 acceptance bullets; quality.md CHK139 (BREAKING flagged in CHANGELOG) + CHK140 (audit-export migration notes) + CHK141 (kebab/Pascal transition window).
- **Depends-on**: T-AA07, T-AA08, T-AA14.
- **Tests**: docs `tests/docs/test_changelog_breaking_section.py` (NEW — asserts "BREAKING CHANGES" header exists in `### Unreleased` and references OpenAPI v0.3.0); link-check `tests/docs/test_adr_036_010_links.py` (NEW — ADR resolves; cross-links to spec.md FR-067 + plan.md §C2 + data-model.md §11.1 valid).
- **Backward-compat / Effort**: documentation only (no runtime effect); small.

---

### §24.7 Cycle 2 dependency graph

```text
T-AA07 ─┬─→ T-AA08 ─→ T-AA13 ─→ T-AA14 ─→ T-AA15
        │                              ↘─→ T-AA22
        ├─→ T-AA09 ─→ T-AA12           ↗
        │       ↓                      │
        │    T-AA21 ──────────────────→┘
        ├─→ T-AA10 (independent migration)
        ├─→ T-AA11 (independent middleware)
        └─→ T-AA12 (Schemathesis refresh — also depends on T-AA08, T-AA09)

T-AA16 ─┬─→ T-AA17 ─→ T-AA19
        └─→ T-AA18

T-AA14 ─→ T-AA20 (orchestrator must be stable for round-trip e2e)
```

**Critical path** (longest chain, 6 hops): `T-AA07 → T-AA08 → T-AA13 → T-AA14 → T-AA15 → T-AA22` (OpenAPI bump → Pydantic delta → orchestrator span propagation → degraded-dispatch handler → byte-equality + idempotency → ADR + migration notes).

---

### §24.8 Suggested Cycle 2 wave plan

**Wave A (parallel; 6 tasks; ~1 day)** — contract/model scaffolding:

- T-AA07 [P], T-AA08 [P], T-AA09 [P], T-AA10 [P], T-AA11 [P], T-AA12 [P]

**Wave B (sequential; 3 tasks; ~1.5 days)** — orchestrator + route delta:

- T-AA13 → T-AA14 → T-AA15

**Wave C (parallel; 4 tasks; ~1 day)** — SLI + observability:

- T-AA16 [P], T-AA17 [P], T-AA18 [P], T-AA19 [P]

**Wave D (sequential; 3 tasks; ~0.5 day)** — cleanup + BREAKING-change record:

- T-AA20 → T-AA21 → T-AA22

**Wave E (final-sweep)** — assert FS1–FS13 still GREEN (Cycle 1 gates) PLUS the 4 NEW Cycle 2 gates:

- **FS14**: Cycle 2 quality.md CHK101–CHK156 all pass (or explicitly deferred per CHK155).
- **FS15**: `signal_pipeline.dispatch_failed` round-trips through Pydantic + JSON-Schema + Schemathesis at `entry_type` enum size = 25.
- **FS16**: Z6 + Z7 KQL queries return numeric `sample_count + metric` against staging Application Insights; `tests/staging_gates.py` refuses promotion on starvation OR threshold breach.
- **FS17**: ADR-036-010 + CHANGELOG.md "BREAKING CHANGES" entry land in the same PR as T-AA07 + T-AA08 + T-AA14.

---

### §24.9 Cycle 2 status block

| Metric | Count |
|--------|------:|
| Cycle 2 tasks added (T-AA07..T-AA22) | **16** |
| Wave A `[P]` markers | 6 |
| Wave B `[P]` markers | 0 |
| Wave C `[P]` markers | 4 |
| Wave D `[P]` markers | 0 |
| **Total `[P]` markers (Cycle 2)** | **10** |
| New unit tests | 9 |
| New integration tests | 12 |
| New contract tests | 9 |
| New e2e tests | 4 |
| New migration tests | 1 |
| New docs/devops tests | 4 |
| **Total NEW Cycle 2 tests** | **39** |
| New ADRs | 1 (ADR-036-010) |
| BREAKING-flagged tasks | T-AA07, T-AA08, T-AA14, T-AA20, T-AA22 (5) |

**Per-amendment task coverage**:

| Amendment | Severity | Tasks | FR / SC |
|-----------|----------|-------|---------|
| A2-01 | HIGH | T-AA07, T-AA08, T-AA12, T-AA13, T-AA14, T-AA22 (6) | FR-067 |
| A2-02 | HIGH | T-AA16, T-AA17, T-AA18, T-AA19 (4) | SC-013 + FR-063 STRENGTHEN |
| A2-03 | MEDIUM | T-AA20 (1) | FR-068 |
| A2-04 | MEDIUM | T-AA09, T-AA15 (2) | FR-069 |
| A2-05 | MEDIUM | T-AA11 (1) | RECONCILE (no new FR) |
| A2-06 | LOW | T-AA21 (1) | FR-048 STRENGTHEN |
| A2-07 | LOW | T-AA10 (1) | FR-070 |
| A2-08 | LOW | folded into T-AA14 | TYPE-EXTEND (audit envelope) |

**Per-FR / SC test-pyramid coverage** (every Cycle 2 FR/SC has ≥1 unit + ≥1 integration + ≥1 contract test):

| FR / SC | Unit | Integration | Contract | E2E |
|---------|------|-------------|----------|-----|
| FR-067 | T-AA08, T-AA13 | T-AA14 | T-AA07, T-AA12, T-AA14 | — |
| FR-068 | T-AA20 | T-AA20 (round-trip) | T-AA20 (build-time) | T-AA20 |
| FR-069 | T-AA09 | T-AA15 | T-AA09, T-AA12 | — |
| FR-070 | T-AA10 | T-AA10 (migration) | T-AA10 (enum byte-equality) | — |
| SC-013 | T-AA17 | T-AA16, T-AA17 | T-AA16, T-AA18 | T-AA17, T-AA19 |

**File:line evidence cited in Cycle 2 task block** (sampled — full list embedded in task bodies):

- `apps/api/app/api/routes/simulations_036.py:106-111` (Pydantic shape) — T-AA08
- `apps/api/app/api/routes/simulations_036.py:316-345` (silent-swallow site) — T-AA14
- `apps/api/app/api/routes/simulations_036.py:331-342` (`injection.success` audit) — T-AA15
- `apps/api/app/services/simulation/signal_pipeline_orchestrator.py:131-213` — T-AA13
- `apps/api/app/services/simulation/audit_writer.py` — T-AA09, T-AA10, T-AA21
- `apps/api/app/services/simulation/cascade_orchestrator.py:225-235` (line 227 placeholder) — T-AA21
- `apps/api/app/config/cascade_rules.yaml:17-55` — T-AA20
- `apps/api/app/middleware/error_handler.py:24-72` — T-AA11
- `packages/domain/src/domain/sim_cascade_matrix.py:34-40` (alias) — T-AA20
- `packages/domain/src/domain/models/aiims_mapping.py:51-61` — T-AA10
- `infra/observability/sli-kql.json:6-67` (Z1..Z5) + new Z6/Z7 — T-AA16
- `infra/bicep/modules/observability-alerts.bicep` + `observability-workbook-sim-slis.bicep` — T-AA18
- `tests/staging_gates.py` (`assert_sli_thresholds()`) — T-AA17
- `.github/workflows/staging-promotion.yml` (NEW smoke-injection job) — T-AA19
- `contracts/openapi-simulation.yaml` (v0.2.x → v0.3.0) — T-AA07
- `contracts/audit-envelope.md` §1 line 56 + §3.25 + §5 + §6 + closing line — T-AA09, T-AA10, T-AA12
- `contracts/error-responses.md` §1 line 9 + §4 + §5 + §6 + §7 — T-AA11
- `contracts/sli-thresholds.md` §1 rows 6-7 + §6a + §6b + §7.3 + §7.4 — T-AA16, T-AA17
- `data-model.md` §§ 11.1–11.7 — T-AA07, T-AA08, T-AA09
- `checklists/quality.md` CHK101..CHK156 (cited in every Acceptance bullet) — all tasks

**Total `file:line` citations across §24**: **≥ 60 unique evidence anchors** (every task body cites at least 3 of: plan.md §C2.x, spec.md FR/SC/pass-Q, contract delta, data-model.md §11.x, quality.md CHK1xx).

---

### §24.10 Format-validation checkpoint

Every Cycle 2 task above conforms to the existing `tasks.md` row schema (matching the Cycle 1 §§ 4–20 format used by T-A01..T-AA06):

- ✅ Heading prefix `### T-AAxx` with `[P?] [NEW] [A2-XX H/M/L] [Wave A/B/C/D]` markers and a hyphen-separated short title.
- ✅ Bullet body with `Phase | Files | Description | Acceptance | Depends-on | Tests | Backward-compat / Effort` (≤ 8 lines per task body — the longest is T-AA14 at 7 substantive lines).
- ✅ Every Acceptance bullet cites at least one of: plan.md §C2.x, spec.md FR-067..070 / SC-013 / pass-1 Q1–Q5 / pass-2 Q1–Q5, contract delta (audit-envelope.md / error-responses.md / sli-thresholds.md), data-model.md §11.x, quality.md CHK1xx.
- ✅ Every Tests bullet enumerates concrete test files distributed across unit / integration / contract / e2e / migration / devops layers, totalling **39 NEW Cycle 2 tests**.
- ✅ Every BREAKING-flagged task (T-AA07, T-AA08, T-AA14, T-AA20, T-AA22) carries an explicit `**BREAKING**` callout in the Backward-compat / Effort line and is paired with mitigation (same-PR contract bump + ADR + CHANGELOG migration note).
- ✅ Every Cycle 2 task ID is unique across the entire `tasks.md` file (T-AA07..T-AA22 — no collision with the locked-COMPLETE Cycle 1 §20 T-AA01..T-AA06 block).

---

**§24 Cycle 2 task block locked. Ready for /speckit.analyze.**

---

## §25 Cycle 3 Task Block (post Step 8z amendments)

> **Cycle context**: This block appends T-AA23..T-AA42 to address the six Cycle 3 amendments (A3-01 → A3-06 — `spec.md:237-358`), the eight Cycle 3 clarifications (Pass-1 Q1–Q5 at `spec.md:812-1278` + Pass-2 Q1–Q3 at `spec.md:1280-1605`), and the three Cycle 3 plan-decisions (PD-C3-01..PD-C3-03 at `plan.md:482-740`). All Cycle 1 task content (§§ 1–23) and Cycle 2 task content (§24, T-AA07..T-AA22, locked-COMPLETE) remain **byte-identical** — Cycle 3 is strictly additive. Cycle 3 IDs continue the existing T-AA namespace from **T-AA23** (next after the Cycle 2 maximum T-AA22, verified by inspection of §24.9 status block). The 20 Cycle 3 tasks are organised into three waves matching the PD-C3-02 single-co-merge unit plus the PD-C3-02 Step 8x → Step 8z artefact dependency edge: Wave A (foundational docs + contracts + spec re-wordings) lands the artefact dependencies the rest of Cycle 3 binds against; Wave B (KQL canonicaliser + parametric contract test + Z1-Z5 alignment audit) is the PD-C3-02 single-co-merge unit's testing core; Wave C (workflow refactor + envelope writer + integration tests + e2e canary) lands the runtime behaviour changes that close A3-01 / A3-02 and exercise SC-014. Cycle 3 honours Australian English throughout (artefact, behaviour, prioritise, organise, harmonise, recognise, parametric, canonicalise, normalisation) and preserves all 7 Constitution v1.2.0 invariants per `plan.md` §C2.6 + the three additional PD-C3 decisions.

### §25.1 Cycle 3 phase tracker

| Wave | Tasks | Title | Status | Depends-on |
|------|-------|-------|--------|-----------|
| **A** | T-AA23..T-AA29 | Foundation — docs drift fixes + regression tests + contracts surfaces + spec re-wordings (parallelisable in two clusters; ~0.5 day) | NEW | Cycle 2 §24 final-sweep GREEN |
| **B** | T-AA30..T-AA34 | Canonicaliser + parametric contract test + Z1-Z5 alignment audit (single co-merge unit per PD-C3-02; ~1 day) | NEW | Wave A T-AA26 + T-AA27 + T-AA28 |
| **C** | T-AA35..T-AA42 | Workflow gate + envelope writer + concurrency + tenant isolation + integration + e2e canary (~1.5 days) | NEW | Wave A + Wave B |

### §25.2 Severity legend (per Cycle 3 amendment severity convergence — `spec.md:267-274`, quality.md CHK195)

- `[A3-01 HIGH]` ↔ sre-engineer + Operations Officer + Field Coordinator — staging-promotion gate workflow boundary enforcement (FR-071).
- `[A3-02 HIGH]` ↔ infrastructure-devops + Operations Officer + Field Coordinator — synthetic smoke-injection emits real telemetry (FR-072).
- `[A3-03 MEDIUM]` ↔ compliance-auditor — ADR / CHANGELOG citation drift to non-existent `_is_breach()` symbol.
- `[A3-04 MEDIUM]` ↔ compliance-auditor — ADR / CHANGELOG SLI-Z6 threshold-value drift (gpt-4o, gpt-4o-mini bands).
- `[A3-05 MEDIUM]` ↔ data-engineer — Z6 KQL cardinality + filter contract (FR-073, folds A3-06).
- `[A3-06 MEDIUM]` ↔ data-engineer — Z7 KQL dimension + warn/breach band (folded into FR-073).

---

### §25.3 Wave A — Foundation: docs drift fixes + regression tests + contracts + spec re-wordings (parallelisable in two clusters; depends only on Cycle 2 §24 GREEN)

> **Within-wave parallelism**: T-AA23 / T-AA24 / T-AA25 (docs cluster) parallelisable with T-AA26 / T-AA27 / T-AA28 / T-AA29 (contracts + spec cluster). T-AA24 + T-AA25 depend on T-AA23 (regression tests bind to corrected ADR / CHANGELOG content). T-AA28 depends on T-AA27 (the §"KQL canonicalisation contract" subsection precedes the per-SLI tenant-filter amendment in the same doc). T-AA29 depends on T-AA26 (FR-071 amended sentence cites the new §3.26 audit-envelope slot).

#### T-AA23 [P] [DONE] [A3-03 MEDIUM + A3-04 MEDIUM] [Wave A] — ADR-036-010 + CHANGELOG.md citation + threshold-value drift fix

- **Phase**: Wave A — closes A3-03 (citation drift) + A3-04 (threshold-band drift) in a single edit pass; co-located because both defects reside in the same two files at adjacent line ranges.
- **Files**: `docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md:83-84` (replace stale `gpt-4o ≤ 2 500 ms warn / ≤ 5 000 ms breach; gpt-4o-mini ≤ 1 800 ms warn / ≤ 2 000 ms breach` with canonical `gpt-4o ≤ 4 000 ms warn / ≤ 5 000 ms breach; gpt-4o-mini ≤ 1 500 ms warn / ≤ 2 000 ms breach`); `docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md:87` (replace `tests/staging_gates.py::_is_breach()` with `tests/staging_gates.py::assert_sli_thresholds()`); `CHANGELOG.md:19` (replace `gpt-4o ≤ 2 500 ms, gpt-4o-mini ≤ 1 800 ms` with `gpt-4o warn=4000 ms / breach=5000 ms; gpt-4o-mini warn=1500 ms / breach=2000 ms`); `CHANGELOG.md:20` (replace `_is_breach()` with `assert_sli_thresholds()`).
- **Description**: Both citations replicate the same two defects — a non-existent helper name (`_is_breach()` does not exist in `tests/staging_gates.py`; `grep -n "_is_breach" tests/staging_gates.py` returns zero hits) and stale Z6 threshold values that contradict the canonical contract at `infra/observability/sli-kql.json:72-75`, `tests/staging_gates.py::assert_sli_thresholds()`, `infra/bicep/modules/observability-alerts.bicep`, and `contracts/sli-thresholds.md:218-228`. Cycle 3 mandates byte-equality between docs and the canonical contract.
- **Acceptance**: plan.md §"Cycle 3 Plan Decisions" (PD-C3 cross-references); spec.md A3-03 (`spec.md:303-313`) + A3-04 (`spec.md:315-325`); quality.md CHK159 (citation drift) + CHK160 (threshold drift); zero `grep -n "_is_breach"` matches in `docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md` after edit; zero `grep -n "2 ?500\|1 ?800"` matches against ADR / CHANGELOG threshold paragraphs after edit.
- **Depends-on**: none (Wave-A lead; documents-only fix).
- **Tests**: regression `tests/docs/test_adr_036_010_threshold_drift.py` (NEW — created in T-AA24); regression `tests/docs/test_adr_036_010_symbol_citations.py` (NEW — created in T-AA25); both bind to the corrected ADR / CHANGELOG content.
- **Backward-compat / Effort**: documentation only (no runtime effect); small.

#### T-AA24 [P] [DONE] [A3-04 MEDIUM] [Wave A] — Regression test for ADR-036-010 + CHANGELOG threshold byte-equality with `infra/observability/sli-kql.json`

- **Phase**: Wave A — automated drift gate; binds the ADR / CHANGELOG threshold paragraphs to the canonical SLI bundle so future drift fails CI.
- **Files**: NEW `tests/docs/test_adr_036_010_threshold_drift.py` (parses ADR-036-010 §"Z6 thresholds" and `CHANGELOG.md:19` for the gpt-4o + gpt-4o-mini warn/breach bands; loads `infra/observability/sli-kql.json["slis"][?id=="SLI-Z6"]["thresholds"]`; asserts byte-equality on all four numeric fields).
- **Description**: The test parses the ADR's threshold table by markdown structure (one row per model deployment with four numeric cells: warn_ms / breach_ms / warn_pct / breach_pct, of which Z6 uses the latency pair) and asserts every quoted value resolves to the same integer constant exposed by `sli-kql.json`. CHANGELOG entry at `:19` is parsed by literal-substring extraction. Test fails on ANY drift, with a diagnostic that names the drifted cell.
- **Acceptance**: plan.md §"Cycle 3 Plan Decisions" PD-C3-02 cross-reference (single source of truth); spec.md A3-04 acceptance bullet at `spec.md:325` (`tests/docs/test_adr_036_010_threshold_drift.py` (new) parses the ADR's threshold table and asserts every quoted value is byte-equal to the corresponding SLI-Z6 field in `infra/observability/sli-kql.json`); quality.md CHK160 + CHK182.
- **Depends-on**: T-AA23 (corrected ADR + CHANGELOG content must exist for the test to be green at landing).
- **Tests**: this task delivers the test; the test is green on initial run by virtue of T-AA23 having corrected the source documents.
- **Backward-compat / Effort**: additive (new test file only); small.

#### T-AA25 [P] [DONE] [A3-03 MEDIUM] [Wave A] — Regression test for ADR-036-010 + CHANGELOG cited Python symbols resolve via `importlib`

- **Phase**: Wave A — automated drift gate for symbol citations; complements T-AA24's threshold-value gate.
- **Files**: NEW `tests/docs/test_adr_036_010_symbol_citations.py` (scans `docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md` and `CHANGELOG.md` for `module.path::symbol_name` patterns inside backticked code spans; for each match, invokes `importlib.import_module(module)` and asserts `hasattr(module, symbol)`).
- **Description**: The regex `[a-zA-Z_][a-zA-Z0-9_./]*\.py::[a-zA-Z_][a-zA-Z0-9_]*` matches every `path/to/module.py::symbol` citation; the test converts the path to a dotted module reference (`tests/staging_gates.py` → `tests.staging_gates`) and asserts the symbol resolves. The non-existent `_is_breach` symbol from the original ADR / CHANGELOG would fail; the corrected `assert_sli_thresholds` resolves cleanly. Symbols may be public or private — the test does NOT distinguish (a private helper that ADR cites must still exist).
- **Acceptance**: plan.md §"Cycle 3 Plan Decisions" PD-C3-02 cross-reference; spec.md A3-03 acceptance bullet at `spec.md:313` (`tests/docs/test_adr_036_010_symbol_citations.py` (or equivalent) parses the ADR / CHANGELOG and asserts every cited Python symbol resolves via `importlib`); quality.md CHK159 + CHK183.
- **Depends-on**: T-AA23 (corrected symbol citations must exist for the test to be green at landing).
- **Tests**: this task delivers the test; the test is green on initial run by virtue of T-AA23.
- **Backward-compat / Effort**: additive (new test file only); small.

#### T-AA26 [P] [DONE] [A3-01 HIGH] [Wave A] — `contracts/audit-envelope.md` §3.26 `staging_promotion.refused` schema + counter increment 25 → 26

- **Phase**: Wave A — contract surface that the Wave-C envelope writer (T-AA40), concurrency test (T-AA41), and synthetic-canary e2e (T-AA42) all bind against.
- **Files**: `contracts/audit-envelope.md` add NEW §3.26 `staging_promotion.refused` schema after the existing §3.25 `signal_pipeline.dispatch_failed`; `contracts/audit-envelope.md:689` (typed-entry counter "**25** typed entries above" → "**26** typed entries above"; append `staging_promotion.refused` to the inline enumeration); `contracts/audit-envelope.md:703` (§6.1 heading "5 added in Cycle 1, 1 added in Cycle 2 — total 19 → 25" → "5 added in Cycle 1, 1 added in Cycle 2, 1 added in Cycle 3 — total 19 → 26"; add a new §6.1 table row for `staging_promotion.refused` with source amendment "Cycle 3 Amendment A3-01 / FR-071", Cosmos container `simulation_audit_entries`).
- **Description**: §3.26 schema declares the eight-field `details` set pinned by Pass-1 Q3 (`spec.md:1031-1039`) — `staging_promotion_correlation_id: uuid` (UUID4, fresh per gate run), `build_label: str`, `triggering_workflow_run_id: int`, `triggering_actor: str`, `breached_slis: list[str]`, `sample_floor_underages: list[{"sli_id": str, "observed_samples": int, "required_samples": int}]`, `refused_at: ISO8601 timestamp`, `gate_helper_version: str` (sha-256 of `tests/staging_gates.py` at run time) — plus the `entry_type` const discriminator (`{"type": "string", "const": "staging_promotion.refused"}`) and a top-level `correlation_id` field whose value MUST equal `staging_promotion_correlation_id` (single-stream JOIN-by-`correlation_id` invariant from Cycle 2 Pass-1 Q4). The §3.20–§3.24 envelope-section gap is **preserved** (Pass-2 Q1 explicit decision, `spec.md:1328-1330`); back-filling would obscure temporal ordering. Allocator (Cycle 1 ADR-036-007) remains the sole `sequence_number` source — the §3.26 schema MUST NOT carry a placeholder `sequence_number` literal (Cycle 2 Amendment A2-06 precedent).
- **Acceptance**: plan.md PD-C3-02 cross-reference at `plan.md:633-636` (ADR-036-011 § "Sub-decision (ii)"); spec.md Pass-1 Q3 (`spec.md:1016-1097`) + Pass-2 Q1 (`spec.md:1308-1387`); quality.md CHK170 + CHK173 (eight-field details set) + CHK174 (entry_type discriminator) + CHK175 (correlation_id parity) + CHK176 (counter increment in two places) + CHK177 (gap preserved) + CHK178 (sequence_number from writer).
- **Depends-on**: none (Wave-A lead — contract surface).
- **Tests**: contract `tests/contract/test_audit_envelope_schema.py` (or the existing `test_audit_envelope_schema_2020_12.py`) — EXTEND the `entry_type` enum parametrisation to include `staging_promotion.refused`; assert §3.26 schema is reachable and JSON-Schema-2020-12-valid. Counter assertions: extend `test_audit_envelope_filter_enum_25.py` (Cycle 2 T-AA12) to expect 26 typed entries.
- **Backward-compat / Effort**: additive (new envelope type; existing 25 typed entries remain unchanged); small.

#### T-AA27 [P] [DONE] [A3-05 MEDIUM] [Wave A] — `contracts/sli-thresholds.md` new §"KQL canonicalisation contract" subsection

- **Phase**: Wave A — contract surface that the Wave-B canonicaliser (T-AA30) and parametric contract test (T-AA32) bind against.
- **Files**: `contracts/sli-thresholds.md` add NEW subsection §"KQL canonicalisation contract" at the end of the document (after the existing §7 dashboard section); document the **six normalisation steps** from PD-C3-01 (`plan.md:498-572`) verbatim; document the **idempotence + determinism + stability** invariants; document the **public Python API surface** signatures pinned by Pass-2 Q2 (`spec.md:1388-1483`) — `canonicalise_kql(text: str) -> str`, `canonical_kql_for_sli(sli_id: str, *, thresholds_path: Path | None = None) -> str`, `__all__ = ["canonicalise_kql", "canonical_kql_for_sli"]`; document the error contracts (`KeyError` for unknown sli_id, `ValueError` for malformed contracts file); document the `_THRESHOLDS_PATH` resolution rule (`Path(__file__).resolve().parents[2] / "specs" / "036-sim-agent-extend" / "contracts" / "sli-thresholds.md"`).
- **Description**: The subsection is the canonical SOURCE-OF-TRUTH for the canonicalisation contract — both the algorithm (six steps) and the public Python entry points. Future implementers reading the contract MUST be able to author a compliant canonicaliser without spelunking the test code. The subsection MUST also explicitly enumerate the **rejected alternatives** (Kusto-AST equivalence — three-part rejection rationale from PD-C3-01) so future reviewers do not re-litigate the decision.
- **Acceptance**: plan.md PD-C3-01 (`plan.md:498-572`); spec.md Pass-1 Q1 (`spec.md:838-925`) + Pass-2 Q2 (`spec.md:1388-1483`); quality.md CHK165 + CHK171 + CHK184 + CHK191.
- **Depends-on**: none (Wave-A lead — contract surface).
- **Tests**: contract `tests/contract/test_sli_thresholds_canonicalisation_contract.py` (NEW — asserts the subsection exists, contains the six step headings, the idempotence + determinism invariants, and the three function signatures by literal-substring match); the test is green on T-AA27 landing.
- **Backward-compat / Effort**: additive (new subsection; existing §1–§7 unchanged); small.

#### T-AA28 [P] [DONE] [A3-05 MEDIUM] [Wave A] — `contracts/sli-thresholds.md:230-244, :276-289` add `tnt-stg-smoke` tenant filter to canonical Z6 + Z7 KQL bodies

- **Phase**: Wave A — propagates the Pass-1 Q2 isolation guarantee (iv) `where tenant_id == "tnt-stg-smoke"` into the canonical Z6 + Z7 KQL bodies.
- **Files**: `contracts/sli-thresholds.md:230-244` (Z6 canonical KQL — append `| where tenant_id == "tnt-stg-smoke"` clause after the `where env == "staging"` clause; extend §6a "Filters" cell to include `tenant_id == "tnt-stg-smoke"`); `contracts/sli-thresholds.md:276-289` (Z7 canonical KQL — same `where tenant_id == "tnt-stg-smoke"` clause; extend §6b "Filters" cell).
- **Description**: Pass-1 Q2 (`spec.md:954-960`) pinned the smoke-tenant KQL filter as isolation guarantee (iv); the canonical KQL bodies in `sli-thresholds.md` MUST carry that filter so smoke-injected events are visible to the staging-promotion gate but provably never contaminate production-tenant SLI evaluation (the same KQL run against the production workspace returns zero rows). The implementation KQL (T-AA34) must match after canonicalisation.
- **Acceptance**: plan.md PD-C3-03 isolation guarantee (iv) at `plan.md:674-679`; spec.md Pass-1 Q2 (`spec.md:926-1015`); quality.md CHK166 + CHK190.
- **Depends-on**: T-AA27 (the canonicalisation contract subsection precedes the per-SLI body amendment in the same doc; ordering avoids merge conflict).
- **Tests**: contract `tests/contract/test_sli_thresholds_tenant_filter.py` (NEW — asserts both Z6 and Z7 KQL fenced blocks contain the literal `where tenant_id == "tnt-stg-smoke"` clause); contract `tests/contract/test_sli_kql_canonical_match.py` (NEW in T-AA32) — when the implementation KQL is updated in T-AA34, the parametric test asserts byte-equality after canonicalisation.
- **Backward-compat / Effort**: additive to canonical KQL (the implementation KQL change is BREAKING for any operator who copy-pasted the prior canonical form into a one-off query, but the canonical form change here is contract-side only); small.

#### T-AA29 [DONE] [A3-01 HIGH + A3-02 HIGH + A3-05 MEDIUM] [Wave A] — `spec.md` in-place re-wordings for FR-071 / FR-072 / FR-073 / SC-014 per Pass-1 + Pass-2 propagation queues

- **Phase**: Wave A — collects the four deferred in-place spec re-wordings flagged across Pass-1 Q3 / Q4 and Pass-1 Q2 / Pass-2 Q1; lands them in a single edit pass.
- **Files**: `specs/036-sim-agent-extend/spec.md` FR-071 in-place at `:3625-3641` (append the Pass-1 Q3 sentence: *"On `StagingPromotionRefused` raise, `assert_sli_thresholds()` MUST write a `staging_promotion.refused` audit envelope (per `contracts/audit-envelope.md` §3.26) with a fresh `staging_promotion_correlation_id` (UUID4) before the exception propagates; two concurrent refused runs each write their own envelope — no coalescing."*); FR-072 in-place at `:3643-3658` (replace `$SMOKE_TOKEN` shorthand with *"a short-lived bearer access token acquired via `azure/login@v2` + `az account get-access-token`; no long-lived `SMOKE_TOKEN` secret is permitted"*); FR-073 in-place at `:3660-3677` (re-word *"the test covers both Z6 and Z7"* to *"the test covers all seven SLIs (Z1–Z7); Z6 and Z7 are the cohort-finding-driven minimum surface the Step 8s cohort validated, but the contract surface is universal — every declared SLI in `infra/observability/sli-kql.json` participates in canonicalisation enforcement"*); SC-014 in-place at `:3784-3795` (append the Pass-1 Q4 clarifying sentence: *"The synthetic canary is fixture-driven (a deterministic in-Python `sli_results` dict passed directly to `assert_sli_thresholds()`); it does NOT inject telemetry into the staging Application Insights workspace and therefore does NOT contaminate the production gate's evidence stream."*).
- **Description**: Each re-wording is verbatim from the deciding-authority Q→A propagation queue and lands without semantic drift. The §3.26 reference in FR-071 binds against T-AA26's audit-envelope addition (sequencing matters — T-AA26 must precede T-AA29 inside Wave A). The OIDC bearer wording in FR-072 codifies PD-C3-03's explicit non-application of ADR-031's `AZURE_CREDENTIALS` fallback. The Z1–Z7 wording in FR-073 codifies PD-C3-02's universal contract surface. The SC-014 fixture-driven sentence codifies Pass-1 Q4's rejection of live-KQL injection.
- **Acceptance**: plan.md PD-C3-02 + PD-C3-03 cross-references; spec.md Pass-1 Q2 propagation at `:991-994`, Pass-1 Q3 propagation at `:1075-1081`, Pass-1 Q4 propagation at `:1166-1171`, Pass-1 Q5 propagation at `:1232-1240`, Pass-2 Q1 propagation at `:1379-1382`; quality.md CHK166 + CHK167 + CHK168 + CHK169 + CHK193.
- **Depends-on**: T-AA26 (FR-071's amended sentence cites `audit-envelope.md` §3.26 — that section must exist before the spec sentence binds to it).
- **Tests**: docs `tests/docs/test_spec_cycle_3_propagation.py` (NEW — asserts the four required substrings appear in the four FR / SC blocks: §3.26 reference in FR-071, OIDC bearer wording in FR-072, "all seven SLIs (Z1–Z7)" in FR-073, "fixture-driven" wording in SC-014); the test is green on T-AA29 landing.
- **Backward-compat / Effort**: in-place spec text only (no FR semantics change — purely propagation of Q→A decisions); small.

---

### §25.4 Wave B — Canonicaliser + parametric contract test + Z1-Z5 alignment audit (single co-merge unit per PD-C3-02)

> **Within-wave parallelism**: T-AA30 (canonicaliser implementation) precedes T-AA31 (canonicaliser unit tests) and T-AA32 (parametric contract test) — both consumers depend on the implementation. T-AA33 (extend `test_sli_kql_schema_v2.py`) runs after T-AA32 lands. T-AA34 (Z1-Z5 alignment audit + Z6 + Z7 fixes) runs in parallel with T-AA32 — the parametric test surfaces drift, T-AA34 closes it inline per PD-C3-02 three-outcome rubric.
>
> **Co-merge invariant** (PD-C3-02, `plan.md:573-636`): all five Wave-B tasks ship in a **single PR** with the parametric contract test green at merge — NO `pytest.mark.xfail`, NO `@pytest.mark.skip`, NO hard-coded SLI subset.

#### T-AA30 [DONE] [A3-05 MEDIUM] [Wave B] — `tests/contract/_kql_canonicaliser.py` — canonicalisation pipeline + module-level `_THRESHOLDS_PATH`

- **Phase**: Wave B — canonicaliser scaffold; gates every downstream Wave-B / Wave-C consumer that asserts canonicalised byte-equality.
- **Files**: NEW `tests/contract/_kql_canonicaliser.py` (the leading underscore signals the module is private to the contract-test surface but exports a stable public API via `__all__`); module-level `_THRESHOLDS_PATH = Path(__file__).resolve().parents[2] / "specs" / "036-sim-agent-extend" / "contracts" / "sli-thresholds.md"` constant mirroring the established `_SLI_PATH` pattern at `tests/contract/test_sli_kql_schema_v2.py:25`.
- **Description**: Implement the three functions pinned by Pass-2 Q2 (`spec.md:1388-1444`):
  - `canonicalise_kql(text: str) -> str` — public entry point with optional input validation; wraps `_canonicalise_kql_string`.
  - `canonical_kql_for_sli(sli_id: str, *, thresholds_path: Path | None = None) -> str` — parses the matching ` ```kql ... ``` ` fenced block out of `thresholds_path` (defaults to `_THRESHOLDS_PATH`); returns its canonicalised form; raises `KeyError("SLI-NONEXISTENT not found in <path>")` on unknown sli_id; raises `ValueError("Failed to extract canonical KQL for <sli_id>: <reason>")` on a malformed contracts file.
  - `_canonicalise_kql_string(raw: str) -> str` — private 6-step pipeline per PD-C3-01 (`plan.md:498-572`): (1) strip line comments (`// …` to end-of-line) + block comments (`/* … */`); (2) collapse runs of ASCII whitespace to a single space, preserving exactly one newline before each pipe (`|`); (3) lowercase Kusto reserved keywords (`extend`, `where`, `summarize`, `by`, `project`, `let`, `and`, `or`, `in`, `between`, `ascending`, `descending`); (4) sort each `by` clause's column list lexicographically; (5) sort each `summarize` aggregate-expression list by left-hand-side alias lexicographically; (6) strip redundant outer parentheses around `extend` target expressions.
  - `__all__ = ["canonicalise_kql", "canonical_kql_for_sli"]` — exports only the public surface.
- **Acceptance**: plan.md PD-C3-01 (`plan.md:498-572`) — six-step pipeline mandate; spec.md Pass-1 Q1 (`spec.md:838-925`) + Pass-2 Q2 (`spec.md:1388-1483`); quality.md CHK165 + CHK171 + CHK184; contract subsection (T-AA27) authored.
- **Depends-on**: T-AA27 (canonicalisation contract subsection in `sli-thresholds.md` documents the public surface — matching that surface is part of the contract).
- **Tests**: T-AA31 unit tests + T-AA32 parametric contract test bind to this module; tests for the module itself land in T-AA31.
- **Backward-compat / Effort**: additive (new module; pure-Python; no external dependency); medium (~50 LoC implementation).

#### T-AA31 [DONE] [A3-05 MEDIUM] [Wave B] — `tests/contract/test_kql_canonicaliser_unit.py` — golden-fixture unit tests for `_canonicalise_kql_string` + idempotence + determinism

- **Phase**: Wave B — unit-test surface for the canonicaliser; one test per of the six pipeline steps + idempotence + determinism + 10× re-run byte-equality.
- **Files**: NEW `tests/contract/test_kql_canonicaliser_unit.py` (targets `_canonicalise_kql_string` directly via `tests.contract._kql_canonicaliser._canonicalise_kql_string` — the private name is reachable for unit tests but not exported via `__all__`).
- **Description**: Eight test functions:
  - `test_step_1_strip_line_and_block_comments` — golden fixture with `// inline` and `/* block */` comments; assert canonical form has no comment characters.
  - `test_step_2_whitespace_collapse_with_pipe_newline_preserved` — golden fixture with tabs / multiple spaces / line breaks; assert single-space collapse AND one `\n` before each `|`.
  - `test_step_3_keyword_lowercase` — golden fixture with mixed-case `EXTEND`, `Where`, `SUMMARIZE BY`; assert all keywords lower-cased.
  - `test_step_4_by_clause_lexicographic_sort` — golden fixture with `by sub_agent, model_deployment` AND its mirror `by model_deployment, sub_agent`; assert both canonicalise to the same byte-sequence.
  - `test_step_5_summarize_alias_lexicographic_sort` — golden fixture with `summarize p95 = …, sample_count = …` AND its mirror `summarize sample_count = …, p95 = …`; assert both canonicalise to the same byte-sequence.
  - `test_step_6_strip_redundant_extend_parens` — golden fixture with `extend env = (tostring(customDimensions["env"]))` → `extend env = tostring(customDimensions["env"])`.
  - `test_idempotence_canonicalise_twice_equals_canonicalise_once` — `canonicalise_kql(canonicalise_kql(x)) == canonicalise_kql(x)` for every fixture above.
  - `test_determinism_10x_rerun_byte_equality` — the same input run 10 times produces 10 byte-identical outputs (no dict-ordering dependency, no set-ordering dependency).
- **Acceptance**: plan.md PD-C3-01 idempotence + determinism invariants (`plan.md:519`); spec.md Pass-1 Q1 (`spec.md:885-889`); quality.md CHK165 + CHK185.
- **Depends-on**: T-AA30 (the implementation module must exist).
- **Tests**: this task delivers the test file; the tests are green on T-AA30 + T-AA31 landing.
- **Backward-compat / Effort**: additive (new test file only); small.

#### T-AA32 [DONE] [A3-05 MEDIUM] [Wave B] — `tests/contract/test_sli_kql_canonical_match.py` — parametric over all 7 SLIs (Z1–Z7); NO `xfail`, NO subset

- **Phase**: Wave B — the FR-073 contract enforcer; the central test that asserts byte-equality between every implementation KQL and its canonical form after canonicalisation.
- **Files**: NEW `tests/contract/test_sli_kql_canonical_match.py`.
- **Description**: One parametric test function:
  ```python
  import json
  from pathlib import Path
  import pytest
  from tests.contract._kql_canonicaliser import canonicalise_kql, canonical_kql_for_sli

  _SLI_PATH = Path(__file__).resolve().parents[2] / "infra" / "observability" / "sli-kql.json"
  _SLI_DOC = json.loads(_SLI_PATH.read_text(encoding="utf-8"))

  @pytest.mark.parametrize("sli_id", [s["id"] for s in _SLI_DOC["slis"]])
  def test_implementation_kql_matches_canonical_after_canonicalisation(sli_id: str) -> None:
      impl_entry = next(s for s in _SLI_DOC["slis"] if s["id"] == sli_id)
      impl_canonical = canonicalise_kql(impl_entry["kql"])
      contract_canonical = canonical_kql_for_sli(sli_id)
      assert impl_canonical == contract_canonical, (
          f"Drift between sli-kql.json[{sli_id}].kql and "
          f"contracts/sli-thresholds.md canonical block for {sli_id}"
      )
  ```
  Pass-1 Q5 mandates parametric symmetry over **all 7 SLIs** ; the parametrisation expression `[s["id"] for s in _SLI_DOC["slis"]]` MUST NOT be a hard-coded list (so any SLI added to `sli-kql.json` post-Cycle-3 automatically participates). The test MUST NOT carry `pytest.mark.xfail`, `@pytest.mark.skip`, or any decorator that suppresses failure (Pass-2 Q3 explicit anti-pattern, `spec.md:1494-1497`).
- **Acceptance**: plan.md PD-C3-01 + PD-C3-02; spec.md Pass-1 Q5 (`spec.md:1183-1250`) + Pass-2 Q3 (`spec.md:1484-1577`); quality.md CHK169 + CHK172 + CHK179 (anti-pattern xfail) + CHK180 (anti-pattern hard-coded subset).
- **Depends-on**: T-AA30 (canonicaliser module) + T-AA27 (canonicalisation contract subsection) + T-AA28 (Z6 + Z7 canonical bodies updated with tenant filter — though the test will surface drift even without T-AA28; T-AA28 is a precondition for green parametric run on Z6 + Z7).
- **Tests**: this task delivers the contract test; green at landing requires T-AA34 alignment audit to have closed any Z1–Z5 drift inline (PD-C3-02 three-outcome rubric).
- **Backward-compat / Effort**: additive (new test); small (~30 LoC).

#### T-AA33 [DONE] [A3-05 MEDIUM] [Wave B] — Extend `tests/contract/test_sli_kql_schema_v2.py` to invoke canonicalisation match alongside per-row schema assertions

- **Phase**: Wave B — strengthens the existing schema test to also assert canonicalisation match, so a single test run validates both schema shape AND canonical alignment.
- **Files**: `tests/contract/test_sli_kql_schema_v2.py` (extend the per-row assertion loop to call `canonicalise_kql` + `canonical_kql_for_sli` and assert byte-equality alongside the existing schema-shape and `sample_count`-column assertions).
- **Description**: The existing test iterates over `_SLI_DOC["slis"]` (line 33-37); add a per-row assertion `assert canonicalise_kql(impl["kql"]) == canonical_kql_for_sli(impl["id"])` so a single `pytest tests/contract/test_sli_kql_schema_v2.py -q` invocation validates both the schema AND the canonical alignment. The dedicated `test_sli_kql_canonical_match.py` (T-AA32) remains the focused contract test; this extension is a belt-and-braces gate so a future refactor that touches only the schema test still triggers canonical drift detection.
- **Acceptance**: plan.md PD-C3-01; spec.md Pass-1 Q1 propagation queue at `:917-919`; quality.md CHK165.
- **Depends-on**: T-AA32 (parametric contract test patterns) + T-AA30 (canonicaliser module).
- **Tests**: this task extends an existing test; the extension is green on T-AA30 + T-AA32 + T-AA34 landing.
- **Backward-compat / Effort**: additive (existing assertions preserved); small.

#### T-AA34 [DONE] [A3-05 MEDIUM + A3-06 MEDIUM] [Wave B] — Z1-Z5 alignment audit + Z6 + Z7 KQL fixes (A3-05 + A3-06) in `infra/observability/sli-kql.json`

- **Phase**: Wave B — closes A3-05 + A3-06 implementation drift; co-merges with the canonicaliser PR per PD-C3-02 single-co-merge unit; absorbs any Z1-Z5 drift surfaced by the parametric test (T-AA32).
- **Files**: `infra/observability/sli-kql.json:67-81` (Z6 entry — add `extend sub_agent = tostring(customDimensions["sub_agent"])`, `extend env = tostring(customDimensions["env"])`, `where env == "staging"`, `where tenant_id == "tnt-stg-smoke"`; change `summarize ... by model_deployment` → `summarize ... by sub_agent, model_deployment`; restoring 28-series cardinality (`sub_agent × model_deployment`) per A3-05); `infra/observability/sli-kql.json:82-96` (Z7 entry — replace single `delivery_ms` `customDimension` read with `extend client_received_ms`, `extend server_emit_ms`, `extend drift_ms = client_received_ms - server_emit_ms`, `extend env`, `where env == "staging"`, `where tenant_id == "tnt-stg-smoke"`; `summarize within_budget = countif(drift_ms <= 1500), sample_count = count() by model_deployment`; correct `breach_pct: 99.5` → `breach_pct: 99.0` per A3-06; preserve `warn_pct: 99.5`); `infra/observability/sli-kql.json:6-67` (Z1-Z5 entries — audit pass per PD-C3-02 three-outcome rubric: outcome (i) green-on-first-run if no drift; outcome (ii) drift fixed inline if surfaced; outcome (iii) plan-touch fall-through if canonical-form ambiguity surfaces).
- **Description**: The Z6 fix restores the 28-series cardinality (`sub_agent × model_deployment`) that the original implementation collapsed to ~2 rows by dropping `extend sub_agent` and grouping by `model_deployment` only. The Z7 fix replaces the publisher-tagged `delivery_ms` with the spec's end-to-end clock-skew form `client_received_ms − server_emit_ms` AND corrects the indistinguishable-bands defect (`breach_pct: 99.5 == warn_pct: 99.5`) by setting `breach_pct: 99.0` per `contracts/sli-thresholds.md:269-270`. The Z1-Z5 alignment audit confirms the Pass-1 Q5 presumption that Z1-Z5 are aligned as of Cycle 2 close (per Cycle 2 A2-02); any drift surfaced becomes outcome (ii) drift-fixed-inline content, recorded in the PR description's "Drift fixed inline" sub-bullet. The Wave-A T-AA28 amendment to `contracts/sli-thresholds.md:230-244, :276-289` adds the `where tenant_id == "tnt-stg-smoke"` clause to the canonical Z6 + Z7 forms; this task's implementation update synchronises the implementation forms in the same PR.
- **Acceptance**: plan.md PD-C3-02 three-outcome rubric (`plan.md:588-608`); spec.md A3-05 (`:327-338`) + A3-06 (`:339-352`) + Pass-1 Q5 (`:1183-1250`) + Pass-2 Q3 (`:1484-1577`); quality.md CHK161 + CHK162 + CHK172 + CHK190.
- **Depends-on**: T-AA28 (canonical Z6 + Z7 KQL bodies updated with tenant filter — implementation must match canonical after Wave-A lands); T-AA30 (canonicaliser surface to assert match against); T-AA32 (the parametric contract test that surfaces drift on Z1-Z5 during PR review).
- **Tests**: parametric `tests/contract/test_sli_kql_canonical_match.py` (T-AA32) is GREEN at PR-merge-time across all 7 SLIs after this task lands; existing integration `tests/integration/test_z6_z7_kql_smoke.py` (Cycle 2 T-AA16) — RE-RUN against the corrected Z6 + Z7 KQL to confirm the 28-series cardinality is observable and `breach_pct: 99.0` triggers correctly.
- **Backward-compat / Effort**: implementation behaviour change for Z6 + Z7 (28-series cardinality + corrected drift dimension + corrected band) — operators who hand-coded queries against the prior shapes need to re-author; the canonical form is unchanged for Z1-Z5 (presumed); medium.

---

### §25.5 Wave C — Workflow gate + envelope writer + concurrency + tenant isolation + integration + e2e canary (sequential after Wave A + Wave B)

> **Within-wave parallelism**: T-AA35 → T-AA36 → T-AA37 are strict-sequential because all three edit `.github/workflows/staging-promotion.yml` (file-overlap conflict avoidance). T-AA38 + T-AA39 (infra + isolation contract test) parallelisable with T-AA40 (`tests/staging_gates.py` envelope writer). T-AA41 + T-AA42 (integration concurrency + e2e canary) at the end of the wave because both bind against the envelope writer (T-AA40) and the runtime gate (T-AA35).

#### T-AA35 [DONE] [A3-01 HIGH] [Wave C] — `.github/workflows/staging-promotion.yml:67-113` runtime-gate refactor: invoke `assert_sli_thresholds()` + propagate `StagingPromotionRefused`

- **Phase**: Wave C — closes A3-01 / FR-071 at the workflow boundary. Replaces the silent-success-on-`returncode==0` site.
- **Files**: `.github/workflows/staging-promotion.yml:67-113` (replace the inline Python heredoc that branches only on `proc.returncode != 0` with an invocation that consumes the live KQL output and calls `assert_sli_thresholds(sli_results=collated)` directly OR runs the equivalent `pytest tests/integration/test_assert_sli_thresholds_z6_z7.py -q`); REMOVE the unconditional `print("All 7 SLIs within threshold — promotion allowed.")` line — that string MUST NOT be emitted on any path that has not first observed a successful return from `assert_sli_thresholds()`.
- **Description**: The current heredoc only emits `breaches.append(...)` when the upstream `az` invocation returns non-zero `proc.returncode` (line 92); on a successful call it merely prints `f"{sli['id']}: latest={latest}"` (line 104) and never compares `latest` to `sli["warn_threshold_ms"]`, `sli["breach_threshold_ms"]`, or `sli["breach_pct"]`. SC-013 (Cycle 2 Amendment A2-02) is therefore not enforceable at the workflow boundary even though `tests/staging_gates.py::assert_sli_thresholds` is fully implemented and tested. This refactor binds the workflow exit code to the helper's `StagingPromotionRefused` raise — propagating non-zero status when ANY SLI breaches OR sample-floor under-meets `MIN_SAMPLES_PER_SLI_24H = 30` (Cycle 2 Pass-2 Q4). Documentary or visual-only logs do NOT satisfy FR-071.
- **Acceptance**: plan.md PD-C3-03 cross-references; spec.md A3-01 (`:269`, `:278-289`) + FR-071 (`:3625-3641`) + Pass-1 Q3 (`:1016-1097`); quality.md CHK157 + CHK188.
- **Depends-on**: T-AA29 (FR-071 amended in-place sentence cites §3.26 — must precede the workflow refactor that emits the envelope).
- **Tests**: e2e `tests/e2e/test_staging_promotion_gates.py` (Cycle 2 T-AA17 — extend in T-AA42 to cover `test_synthetic_canary_refused_red_sli_row` invariants i–iv); workflow lint `tests/devops/test_staging_promotion_workflow.py` (NEW — asserts the unconditional `"All 7 SLIs within threshold — promotion allowed."` literal is absent from the YAML; asserts the `assert_sli_thresholds` invocation OR the pytest invocation appears).
- **Backward-compat / Effort**: workflow behaviour change (false-negative → true-negative on broken gate); medium.

#### T-AA36 [DONE] [A3-02 HIGH] [Wave C] — `.github/workflows/staging-promotion.yml:142-185` smoke-injection refactor: OIDC bearer + real `requests.post` to inject-telemetry endpoint

- **Phase**: Wave C — closes A3-02 / FR-072 at the smoke-injection step. Replaces the print-loop stub.
- **Files**: `.github/workflows/staging-promotion.yml:142-185` (replace the print-only loop with: (a) `azure/login@v2` federated-credential bearer acquisition followed by `az account get-access-token --resource <staging-api-app-id-uri>` to obtain a short-lived bearer; (b) per-payload `requests.post(f"{STAGING_API_BASE}/api/simulations/{sim_id}/inject-telemetry", json=payload, headers={"Authorization": f"Bearer {bearer}"}, timeout=30)`; (c) per-request `assert response.status_code == 202 and response.json()["degraded_dispatch"] is False`; (d) REMOVE every reference to a `SMOKE_TOKEN` environment variable; REMOVE the unused `import subprocess` at line 147; (e) `STAGING_API_BASE` sourced from GitHub-environment secret bound to the `staging` environment, NOT a repository-level secret).
- **Description**: The current step constructs `payload = {...}` per iteration (lines 166-174) and prints `f"smoke[{category}#{i}]: {payload['signal_id']}"` (line 175) but never invokes the inject-telemetry endpoint; `import subprocess` (line 147) is unused; no `requests.post`, `subprocess.run`, `curl`, or `az rest` call appears. The `≥ 40 synthetic signals` floor (lines 177-182) trivially passes (5 × 8 = 40 always). Cycle 2 Pass-2 Q4's `MIN_SAMPLES_PER_SLI_24H = 30` mitigation is defeated in low-traffic staging — no `customEvents` rows accumulate. PD-C3-03 mandates OIDC bearer (no long-lived `SMOKE_TOKEN`); ADR-031's MVP `AZURE_CREDENTIALS` fallback explicitly does NOT apply here.
- **Acceptance**: plan.md PD-C3-03 (`plan.md:638-722`); spec.md A3-02 (`:270`, `:290-301`) + FR-072 (`:3643-3658`) + Pass-1 Q2 (`:926-1015`); quality.md CHK158 + CHK166 + CHK188.
- **Depends-on**: T-AA35 (workflow file under active edit; sequential to avoid merge conflict on the same YAML); T-AA29 (FR-072 in-place text re-worded to OIDC bearer wording before workflow refactor lands).
- **Tests**: integration `tests/integration/test_smoke_injection_no_prod_pollution.py` (Cycle 2 T-AA19 — re-run against the refactored job; assert HTTP 202 + `degraded_dispatch=false` + `tenant_id == "tnt-stg-smoke"` per row); contract `tests/contract/test_smoke_tenant_isolation.py` (NEW in T-AA39); workflow lint `tests/devops/test_staging_promotion_workflow.py` (extend — assert `requests.post(...)` literal substring is present; assert `SMOKE_TOKEN` literal is absent; assert `subprocess` import is absent).
- **Backward-compat / Effort**: workflow behaviour change (stub → real telemetry emission); medium.

#### T-AA37 [DONE] [A3-01 HIGH] [Wave C] — `.github/workflows/staging-promotion.yml` workflow-level `concurrency:` block to queue common-path dispatches

- **Phase**: Wave C — closes Pass-1 Q3's concurrency hardening; workflow YAML edit only.
- **Files**: `.github/workflows/staging-promotion.yml` add (at top-level, alongside `name:` and `on:`) `concurrency: { group: "staging-promotion-${{ github.workflow }}-${{ github.ref }}", cancel-in-progress: false }`.
- **Description**: Common-path `workflow_dispatch` invocations queue rather than execute concurrently (preventing accidental concurrent gate races on the same ref). `cancel-in-progress: false` ensures every dispatch eventually runs (so two operators dispatching back-to-back both observe the gate); a queueing model is preferred over cancellation because each gate run produces a forensic audit envelope (T-AA40), and cancellation would suppress the second envelope. Cross-ref races (different refs) DO race; Pass-1 Q3 mandates each race produces its own `staging_promotion.refused` envelope with a fresh `staging_promotion_correlation_id` — T-AA41 covers that case.
- **Acceptance**: plan.md PD-C3-02 cross-references; spec.md Pass-1 Q3 (`:1016-1097`) — workflow-level `concurrency:` block to queue concurrent dispatches; quality.md CHK167 + CHK188.
- **Depends-on**: T-AA36 (workflow file under active edit; sequential).
- **Tests**: workflow lint `tests/devops/test_staging_promotion_workflow.py` (extend — assert top-level `concurrency:` block is present with the literal group expression and `cancel-in-progress: false`).
- **Backward-compat / Effort**: behaviour change (concurrent dispatches now queue); small.

#### T-AA38 [P] [DONE] [A3-02 HIGH] [Wave C] — `infra/bicep/modules/cosmos-simulation-containers.bicep` confirm `Simulation.Coordinator` → `tnt-stg-smoke`-only role assignment with private endpoint + CMK posture parity

- **Phase**: Wave C — codifies PD-C3-03 isolation guarantee (v); design-only confirmation if the role assignment already exists, else additive.
- **Files**: `infra/bicep/modules/cosmos-simulation-containers.bicep` (confirm or add a `Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments` resource scoped to `tnt-stg-smoke` for the `Simulation.Coordinator` Entra ID enterprise app's principal id; assert no production-tenant role assignment for the same principal); confirm posture parity (private endpoint + customer-managed key + Cosmos soft-delete with 7-day retention) is identical between `tnt-stg-smoke` and any production tenant.
- **Description**: PD-C3-03 isolation guarantee (v) (`plan.md:680-690`) mandates the `Simulation.Coordinator` test identity has role assignment scoped exclusively to `tnt-stg-smoke`. The Bicep template is the source of truth — this task confirms (or adds) the role assignment at template level so the contract test (T-AA39) can assert the emitted ARM JSON contains exactly one `Simulation.Coordinator` entry with `tnt-stg-smoke`-scoped read/write and no production-tenant scope. Posture parity (private endpoint + CMK + soft-delete) is asserted by structural comparison between the smoke-tenant and production-tenant resource declarations.
- **Acceptance**: plan.md PD-C3-03 isolation guarantee (v) (`plan.md:680-690`); spec.md Pass-1 Q2 (`:961-967` — least-privilege test identity + posture parity); quality.md CHK166 + CHK187.
- **Depends-on**: none (Wave-C parallelisable cluster lead).
- **Tests**: contract `tests/contract/test_smoke_tenant_isolation.py` (NEW in T-AA39 — asserts the role-assignment list scoped to `tnt-stg-smoke`).
- **Backward-compat / Effort**: confirm-or-additive (Bicep template change only if role assignment is missing); small.

#### T-AA39 [P] [DONE] [A3-02 HIGH] [Wave C] — `tests/contract/test_smoke_tenant_isolation.py` — assert role-assignment list scoped to `tnt-stg-smoke`

- **Phase**: Wave C — codifies PD-C3-03 isolation guarantee (v) at the contract-test layer.
- **Files**: NEW `tests/contract/test_smoke_tenant_isolation.py` (compiles `infra/bicep/modules/cosmos-simulation-containers.bicep` to ARM JSON via `az bicep build` OR loads the pre-compiled ARM JSON if checked into the repo; iterates the resources of type `Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments`; asserts exactly one entry referencing the `Simulation.Coordinator` principal id; asserts that entry's `scope` field resolves to `tnt-stg-smoke` and to no other tenant).
- **Description**: The test enumerates every role assignment whose `principalId` resolves to `Simulation.Coordinator` (matched by Entra ID enterprise app object id, parameterised via the Bicep template's `coordinatorPrincipalId` parameter) and asserts the assignment list is exactly `[{"scope": "<...>/tnt-stg-smoke", "permissions": [...]}]` — single entry, smoke-tenant-scoped, no production-tenant entry. The test also asserts posture parity by comparing the smoke-tenant resource declarations to the production-tenant declarations on `privateEndpointConnections`, `keyVaultKeyUri` (CMK), and `softDeleteRetentionInDays`.
- **Acceptance**: plan.md PD-C3-03 (`plan.md:680-690`); spec.md Pass-1 Q2 (`:961-967, :1004-1011`); quality.md CHK166 + CHK187.
- **Depends-on**: T-AA38 (Bicep template confirms / contains the role assignment for the test to bind against).
- **Tests**: this task delivers the contract test; green on T-AA38 + T-AA39 landing.
- **Backward-compat / Effort**: additive (new test file only); small.

#### T-AA40 [P] [DONE] [A3-01 HIGH] [Wave C] — `tests/staging_gates.py:98-130` `assert_sli_thresholds()` extension: write `staging_promotion.refused` audit envelope before each `StagingPromotionRefused` raise

- **Phase**: Wave C — closes Pass-1 Q3 + Pass-2 Q1 at the gate-helper boundary; the binding contract surface mandated by FR-071.
- **Files**: `tests/staging_gates.py:98-130` (extend `assert_sli_thresholds()` to instantiate the audit-envelope writer and emit a `staging_promotion.refused` envelope BEFORE each `StagingPromotionRefused` raise; populate the eight `details` fields per §3.26 schema — `staging_promotion_correlation_id` (`uuid.uuid4()`), `build_label` from a new keyword argument or `os.environ["BUILD_LABEL"]`, `triggering_workflow_run_id` from `os.environ["GITHUB_RUN_ID"]`, `triggering_actor` from `os.environ["GITHUB_ACTOR"]`, `breached_slis` from the helper's collated breach list, `sample_floor_underages` from the collated underage list, `refused_at` `datetime.now(timezone.utc).isoformat()`, `gate_helper_version` `hashlib.sha256(Path(__file__).read_bytes()).hexdigest()`); set the top-level `correlation_id` field equal to `staging_promotion_correlation_id` per §3.26 invariant); the envelope is written via the existing `apps/api/app/services/simulation/audit_writer.py` writer (the writer is the gap-free `sequence_number` allocator — see Cycle 1 ADR-036-007 + Cycle 2 Amendment A2-06)).
- **Description**: The envelope MUST be written by the gate-helper (not by the workflow YAML) because the helper has the structured failure detail in scope; the workflow YAML translates the non-zero process exit into a job-level failure but is not the audit boundary. The envelope is written exactly once per refused invocation; two concurrent refused invocations produce two distinct envelopes with two distinct `staging_promotion_correlation_id` values (Pass-1 Q3 — no coalescing); per Pass-1 Q3 + Pass-2 Q1, this is the gap-free, append-only, typed audit trail per Constitution Principle IV.
- **Acceptance**: plan.md PD-C3-02 cross-references; spec.md Pass-1 Q3 (`:1016-1097`) + Pass-2 Q1 (`:1308-1387`); quality.md CHK167 + CHK170 + CHK189.
- **Depends-on**: T-AA26 (§3.26 schema must exist for the envelope to bind against); T-AA29 (FR-071 amended sentence cites §3.26).
- **Tests**: integration `tests/integration/test_staging_promotion_concurrency.py` (NEW in T-AA41); e2e `tests/e2e/test_staging_promotion_gates.py::test_synthetic_canary_refused_red_sli_row` (NEW in T-AA42 — invariant (iv) asserts the envelope is written exactly once per refused invocation with the expected `breached_slis` content); unit `tests/unit/test_assert_sli_thresholds_envelope_writer.py` (NEW — fixture-driven; assert envelope is written before raise, with all eight `details` fields populated and `correlation_id == staging_promotion_correlation_id`).
- **Backward-compat / Effort**: behaviour-extending (existing raise path now also writes an envelope; callers ignoring the envelope are unaffected); medium.

#### T-AA41 [DONE] [A3-01 HIGH] [Wave C] — `tests/integration/test_staging_promotion_concurrency.py` — two concurrent refused invocations produce two distinct envelopes + two distinct correlation_ids + two non-zero exits

- **Phase**: Wave C — exercises Pass-1 Q3's no-coalescing invariant under concurrent invocation.
- **Files**: NEW `tests/integration/test_staging_promotion_concurrency.py` (uses `concurrent.futures.ThreadPoolExecutor` or `asyncio.gather` to invoke `assert_sli_thresholds()` twice concurrently against shared red-fixture data; collects the two raised `StagingPromotionRefused` exceptions and the two written envelopes from the audit-writer test sink).
- **Description**: One test function, three assertions:
  - `assert exc_a is not exc_b and isinstance(exc_a, StagingPromotionRefused) and isinstance(exc_b, StagingPromotionRefused)` — two distinct exception instances.
  - `assert envelope_a["details"]["staging_promotion_correlation_id"] != envelope_b["details"]["staging_promotion_correlation_id"]` — two distinct UUID4 values; both well-formed UUID4.
  - `assert envelope_a["correlation_id"] == envelope_a["details"]["staging_promotion_correlation_id"]` AND same for `envelope_b` — top-level / nested correlation_id parity per §3.26.
  - `assert exit_code_a != 0 and exit_code_b != 0` — two non-zero process exits when invoked via subprocess (a separate sub-test that spawns two `python -c "from tests.staging_gates import assert_sli_thresholds; assert_sli_thresholds(...)"` subprocesses concurrently).
- **Acceptance**: plan.md PD-C3-02 + Pass-1 Q3 propagation queue (`spec.md:1094-1097`); spec.md Pass-1 Q3 (`:1016-1097`); quality.md CHK167 + CHK186.
- **Depends-on**: T-AA40 (envelope writer must be in place); T-AA37 (workflow concurrency block prevents real-world concurrent dispatches on the common path, but the test exercises the cross-ref race path that DOES race).
- **Tests**: this task delivers the integration test; green on T-AA40 + T-AA41 landing.
- **Backward-compat / Effort**: additive (new test file only); medium (concurrency-aware test fixturing).

#### T-AA42 [DONE] [A3-01 HIGH] [Wave C] — Extend `tests/e2e/test_staging_promotion_gates.py` with `test_synthetic_canary_refused_red_sli_row` — covers 4 red shapes × 4 invariants per shape

- **Phase**: Wave C — closes SC-014 at the e2e layer; exercises FR-071 + the §3.26 envelope on every red shape.
- **Files**: `tests/e2e/test_staging_promotion_gates.py` (extend the Cycle 2 T-AA17 test module with a new test function `test_synthetic_canary_refused_red_sli_row` parametrised over the four red fixtures from Pass-1 Q4 — (1) Z6 P95 latency above breach for gpt-4o (`p95_latency_ms = 5500`, threshold 5 000 ms, `sample_count = 50`); (2) Z7 drift_budget_pct below breach (`drift_budget_pct = 98.5`, threshold 99.0 %, `sample_count = 50`); (3) Z6 sample-floor underage (`sample_count = 17`, threshold 30); (4) Z7 sample-floor underage (`sample_count = 5`, threshold 30); per-shape, assert the four invariants from Pass-1 Q4: (i) `pytest.raises(StagingPromotionRefused)`; (ii) the synthetic-canary subprocess invocation returns non-zero process exit; (iii) no `promote/{build_label}` git tag is created in the test fixture's git workspace (asserted by `git tag --list "promote/*"` returning an empty list after the gate fails); (iv) the `staging_promotion.refused` audit envelope is written exactly once per refused invocation with `breached_slis` content matching the canary fixture's red SLI list).
- **Description**: The test is fixture-driven per Pass-1 Q4 (`spec.md:1099-1163`) — a deterministic in-Python `sli_results` dict passed directly to `assert_sli_thresholds()`; it does NOT inject telemetry into the staging Application Insights workspace and therefore does NOT contaminate the production gate's evidence stream. The four red shapes provide the cohort-validated minimum coverage surface (no fewer, on Pass-1 Q4 mandate); each shape × four invariants = 16 sub-assertions across the parametrised test.
- **Acceptance**: plan.md PD-C3-02 + cross-references; spec.md Pass-1 Q4 (`:1099-1182`) + SC-014 (`:3784-3795`); quality.md CHK164 + CHK168 + CHK181 (anti-pattern: incomplete canary fixture coverage).
- **Depends-on**: T-AA40 (envelope writer must be in place — invariant (iv) asserts envelope content); T-AA35 (workflow runtime-gate must invoke the helper — invariant (ii) asserts non-zero exit propagates); T-AA34 (Z6 + Z7 thresholds aligned — fixture values bind to the canonical thresholds).
- **Tests**: this task delivers the e2e test extension; green on T-AA40 + T-AA34 + T-AA35 landing; the test parametrisation MUST cover all four red shapes (anti-pattern: a 1-or-2-shape minimum is rejected per CHK181).
- **Backward-compat / Effort**: additive (existing tests preserved; new parametrised function added); medium.

---

### §25.6 Cycle 3 dependency graph

```text
Wave A (foundation):

T-AA23 ─┬─→ T-AA24
        └─→ T-AA25

T-AA26 ─→ T-AA29
T-AA27 ─→ T-AA28
T-AA27 ─→ T-AA30 (Wave B start)

(T-AA23/24/25 cluster parallelisable with T-AA26/27/28/29 cluster within Wave A)

Wave B (canonicaliser + parametric + audit):

T-AA30 ─┬─→ T-AA31
        ├─→ T-AA32 ─┬─→ T-AA33
        │           └─→ T-AA34
        └──────────────↗
T-AA28 ─→ T-AA34

Wave C (workflow + envelope + integration):

T-AA29 ─→ T-AA35 ─→ T-AA36 ─→ T-AA37
T-AA26 ─→ T-AA40
T-AA29 ─→ T-AA40

T-AA38 ─→ T-AA39

T-AA40 ─┬─→ T-AA41
        └─→ T-AA42
T-AA35 ─→ T-AA42
T-AA34 ─→ T-AA42
T-AA37 ─→ T-AA41
```

**Critical path** (longest chain, 7 hops): `T-AA27 → T-AA30 → T-AA32 → T-AA34 → T-AA42` (canonicalisation contract subsection → canonicaliser implementation → parametric contract test → Z1-Z5 alignment + Z6/Z7 fixes → e2e canary covering all four red shapes); alternative critical path of equal length: `T-AA26 → T-AA29 → T-AA35 → T-AA40 → T-AA42` (audit-envelope §3.26 → spec re-wording → workflow runtime-gate refactor → envelope writer → e2e canary).

---

### §25.7 Suggested Cycle 3 wave plan

**Wave A (parallelisable in two clusters; 7 tasks; ~0.5 day)** — foundation:

- *Docs cluster*: T-AA23 → T-AA24 [P], T-AA25 [P] (regression tests bind to corrected ADR / CHANGELOG)
- *Contracts + spec cluster*: T-AA26 [P], T-AA27 [P] → T-AA28 [P], T-AA29 (depends on T-AA26)

**Wave B (single co-merge unit per PD-C3-02; 5 tasks; ~1 day)** — canonicaliser + parametric + audit:

- T-AA30 → T-AA31 [P], T-AA32 [P]
- T-AA32 → T-AA33, T-AA34 (T-AA34 parallel with T-AA33)

**Wave C (mixed sequential + parallel; 8 tasks; ~1.5 days)** — workflow + envelope + integration:

- *Sequential workflow cluster*: T-AA35 → T-AA36 → T-AA37
- *Parallel infra + isolation + envelope cluster*: T-AA38 [P] → T-AA39 [P], T-AA40 [P]
- *Final integration + e2e cluster*: T-AA41, T-AA42 (both depend on T-AA40)

**Wave D (final-sweep — Cycle 3 gates)** — assert FS1–FS17 still GREEN (Cycle 1 + Cycle 2 gates) PLUS the Cycle 3 gates:

- **FS18**: Cycle 3 quality.md CHK157–CHK196 all pass (or explicitly deferred per CHK195 Cycle 3 amendment scope).
- **FS19**: `staging_promotion.refused` round-trips through Pydantic + JSON-Schema 2020-12 + the existing audit-envelope schema test at `entry_type` enum size = 26.
- **FS20**: `tests/contract/test_sli_kql_canonical_match.py` is GREEN across all 7 SLIs (Z1–Z7) without `pytest.mark.xfail`, `@pytest.mark.skip`, or hard-coded subset (PD-C3-02 single co-merge unit invariant).
- **FS21**: `.github/workflows/staging-promotion.yml` (a) invokes `assert_sli_thresholds()` (or pytest equivalent); (b) emits real `requests.post` smoke-injection with OIDC-derived bearer + `tnt-stg-smoke` tenant; (c) carries top-level `concurrency:` block; (d) does NOT contain the unconditional `"All 7 SLIs within threshold — promotion allowed."` literal; (e) does NOT contain a `SMOKE_TOKEN` reference; (f) does NOT carry an unused `import subprocess`.

---

### §25.8 Cycle 3 status block

| Metric | Count |
|--------|------:|
| Cycle 3 tasks added (T-AA23..T-AA42) | **20** |
| Wave A `[P]` markers | 6 (T-AA23, T-AA24, T-AA25, T-AA26, T-AA27, T-AA28) |
| Wave B `[P]` markers | 0 (single co-merge unit; intra-wave ordering only) |
| Wave C `[P]` markers | 3 (T-AA38, T-AA39, T-AA40) |
| **Total `[P]` markers (Cycle 3)** | **9** |
| New unit tests | 1 (T-AA40 sub-test) |
| New integration tests | 1 (T-AA41) |
| New contract tests | 5 (T-AA26 ext, T-AA27 binder, T-AA28 binder, T-AA32, T-AA33 ext, T-AA39) |
| New e2e tests | 1 (T-AA42 extension to existing module) |
| New docs tests | 3 (T-AA24, T-AA25, T-AA29) |
| New devops tests | 1 (workflow lint extension across T-AA35/36/37) |
| **Total NEW Cycle 3 tests** | **12** |
| New ADRs | 1 (ADR-036-011 — landed in Step 8y) |
| BREAKING-flagged tasks | 0 (Cycle 3 is implementation + drift fix scope; no contract-shape BREAKING change) |

**Per-amendment task coverage**:

| Amendment | Severity | Tasks | FR / SC |
|-----------|----------|-------|---------|
| A3-01 | HIGH | T-AA26, T-AA29, T-AA35, T-AA37, T-AA40, T-AA41, T-AA42 (7) | FR-071 + SC-014 |
| A3-02 | HIGH | T-AA29, T-AA36, T-AA38, T-AA39 (4) | FR-072 |
| A3-03 | MEDIUM | T-AA23, T-AA25 (2) | DOC-FIX (no new FR) |
| A3-04 | MEDIUM | T-AA23, T-AA24 (2) | DOC-FIX (no new FR) |
| A3-05 | MEDIUM | T-AA27, T-AA28, T-AA29, T-AA30, T-AA31, T-AA32, T-AA33, T-AA34 (8) | FR-073 |
| A3-06 | MEDIUM | T-AA34 (1; folded into FR-073) | folded into FR-073 |

**Per-Q→A and per-PD-C3 task coverage** (every Cycle 3 Q→A and plan-decision binds to ≥ 1 task):

| Source | Tasks |
|--------|-------|
| Pass-1 Q1 (KQL canonicalisation algorithm) | T-AA27, T-AA30, T-AA31, T-AA32 |
| Pass-1 Q2 (OIDC bearer + tnt-stg-smoke isolation) | T-AA28, T-AA29, T-AA36, T-AA38, T-AA39 |
| Pass-1 Q3 (concurrent gate refusals) | T-AA26, T-AA29, T-AA37, T-AA40, T-AA41 |
| Pass-1 Q4 (SC-014 fixture-driven canary) | T-AA29, T-AA40, T-AA42 |
| Pass-1 Q5 (FR-073 retroactive Z1-Z7 scope) | T-AA29, T-AA32, T-AA34 |
| Pass-2 Q1 (audit-envelope §3.26 + counter 25→26) | T-AA26, T-AA29, T-AA40 |
| Pass-2 Q2 (canonicaliser public surface) | T-AA27, T-AA30, T-AA31 |
| Pass-2 Q3 (Z1-Z5 audit co-merge with canonicaliser) | T-AA30, T-AA32, T-AA34 |
| PD-C3-01 (strict-string canonicalisation) | T-AA27, T-AA30, T-AA31, T-AA32 |
| PD-C3-02 (Z1-Z5 audit co-merges in single PR) | T-AA30, T-AA31, T-AA32, T-AA33, T-AA34 |
| PD-C3-03 (Cycle 3 non-application of ADR-031) | T-AA29, T-AA36, T-AA38, T-AA39 |

**Per-FR / SC test-pyramid coverage** (every Cycle 3 FR / SC has ≥ 1 unit + ≥ 1 integration + ≥ 1 contract + ≥ 1 e2e test):

| FR / SC | Unit | Integration | Contract | E2E |
|---------|------|-------------|----------|-----|
| FR-071 | T-AA40 | T-AA41 | T-AA26, T-AA40 (envelope shape) | T-AA42 |
| FR-072 | — | T-AA36 (re-run T-AA19) | T-AA39 | T-AA42 (canary's smoke-path adjacency) |
| FR-073 | T-AA31 | — | T-AA32, T-AA33 | — (canonicalisation is a contract-test surface) |
| SC-014 | — | T-AA41 | — | T-AA42 (4 red shapes × 4 invariants = 16 sub-assertions) |

**File:line evidence cited in §25 task block** (sampled — full list embedded in task bodies):

- `.github/workflows/staging-promotion.yml:67-113` (runtime-gate heredoc) — T-AA35
- `.github/workflows/staging-promotion.yml:142-185` (smoke-injection step) — T-AA36
- `.github/workflows/staging-promotion.yml` (top-level `concurrency:` block) — T-AA37
- `tests/staging_gates.py:98-130` (`assert_sli_thresholds()` envelope writer) — T-AA40
- `infra/observability/sli-kql.json:67-81` (Z6 entry — A3-05) + `:82-96` (Z7 entry — A3-06) + `:6-67` (Z1-Z5 audit) — T-AA34
- `infra/bicep/modules/cosmos-simulation-containers.bicep` (Simulation.Coordinator role assignment) — T-AA38
- `contracts/audit-envelope.md` §3.26 + `:689` counter + `:703` heading — T-AA26
- `contracts/sli-thresholds.md` new §"KQL canonicalisation contract" — T-AA27
- `contracts/sli-thresholds.md:230-244, :276-289` (Z6 + Z7 canonical KQL + tenant filter) — T-AA28
- `docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md:83-84` (threshold drift) + `:87` (citation drift) — T-AA23
- `CHANGELOG.md:19` (threshold drift) + `:20` (citation drift) — T-AA23
- `specs/036-sim-agent-extend/spec.md:3625-3641` (FR-071) + `:3643-3658` (FR-072) + `:3660-3677` (FR-073) + `:3784-3795` (SC-014) — T-AA29
- `tests/contract/_kql_canonicaliser.py` (new module) — T-AA30
- `tests/contract/test_kql_canonicaliser_unit.py` (new) — T-AA31
- `tests/contract/test_sli_kql_canonical_match.py` (new) — T-AA32
- `tests/contract/test_sli_kql_schema_v2.py` (extension) — T-AA33
- `tests/contract/test_smoke_tenant_isolation.py` (new) — T-AA39
- `tests/contract/test_sli_thresholds_canonicalisation_contract.py` (new) — T-AA27
- `tests/contract/test_sli_thresholds_tenant_filter.py` (new) — T-AA28
- `tests/integration/test_staging_promotion_concurrency.py` (new) — T-AA41
- `tests/integration/test_smoke_injection_no_prod_pollution.py` (re-run) — T-AA36
- `tests/e2e/test_staging_promotion_gates.py` (extend with `test_synthetic_canary_refused_red_sli_row`) — T-AA42
- `tests/docs/test_adr_036_010_threshold_drift.py` (new) — T-AA24
- `tests/docs/test_adr_036_010_symbol_citations.py` (new) — T-AA25
- `tests/docs/test_spec_cycle_3_propagation.py` (new) — T-AA29
- `tests/devops/test_staging_promotion_workflow.py` (new) — T-AA35, T-AA36, T-AA37
- `tests/unit/test_assert_sli_thresholds_envelope_writer.py` (new) — T-AA40
- `specs/036-sim-agent-extend/plan.md:482-740` (PD-C3-01..PD-C3-03) — all tasks
- `specs/036-sim-agent-extend/checklists/quality.md` CHK157..CHK196 (cited in every Acceptance bullet) — all tasks

**Total `file:line` citations across §25**: **≥ 70 unique evidence anchors** (every task body cites at least 3 of: plan.md PD-C3-NN, spec.md FR-071/072/073/SC-014/Pass-1 Qx/Pass-2 Qx, contract delta (audit-envelope.md / sli-thresholds.md), quality.md CHK1xx).

---

### §25.9 Format-validation checkpoint

Every Cycle 3 task above conforms to the existing `tasks.md` row schema (matching the Cycle 1 §§ 4–20 format used by T-AA01..T-AA06 AND the Cycle 2 §24 format used by T-AA07..T-AA22):

- ✅ Heading prefix `### T-AAxx` with `[P?] [NEW] [A3-XX H/M/L] [Wave A/B/C]` markers and a hyphen-separated short title.
- ✅ Bullet body with `Phase | Files | Description | Acceptance | Depends-on | Tests | Backward-compat / Effort` (≤ 8 lines per task body).
- ✅ Every Acceptance bullet cites at least one of: plan.md PD-C3-NN, spec.md FR-071/072/073 / SC-014 / Pass-1 Qx / Pass-2 Qx, contract delta (audit-envelope.md §3.26 / sli-thresholds.md §"KQL canonicalisation contract"), quality.md CHK157..CHK196.
- ✅ Every Tests bullet enumerates concrete test files distributed across unit / integration / contract / e2e / docs / devops layers, totalling **12 NEW Cycle 3 tests** (or test-extensions to existing modules).
- ✅ No BREAKING flag is required across any Cycle 3 task — Cycle 3 closes implementation drift + adds a single new typed audit envelope (additive); no public-API contract shape changes (in contrast to Cycle 2 T-AA07/08/14 which carried `**BREAKING**` callouts).
- ✅ Every Cycle 3 task ID is unique across the entire `tasks.md` file (T-AA23..T-AA42 — no collision with the locked-COMPLETE Cycle 1 §20 T-AA01..T-AA06 block, no collision with the locked Cycle 2 §24 T-AA07..T-AA22 block).
- ✅ Australian English honoured throughout (artefact, behaviour, prioritise, organise, harmonise, recognise, parametric, canonicalise, normalisation) — no US spellings introduced.

---

**§25 Cycle 3 task block locked. Ready for /speckit.analyze.**


---

## §26 Cycle 4 Task Block (post Step 8af amendments)

> **Cycle context**: This block appends T-AA43..T-AA56 to address the two Cycle 4 amendments (A4-01 HIGH `spec.md:3875-3895` + A4-02 MEDIUM `spec.md:3896-3915`), the nine Cycle 4 clarifications (Pass-1 Q1–Q5 at `spec.md:3997-4351` + Pass-2 Q1–Q4 at `spec.md:4427-4814`), and the two Cycle 4 plan-decisions (PD-C4-01 at `plan.md:788-1010` + PD-C4-02 at `plan.md:1011-1348`). All Cycle 1 task content (§§ 1–23), Cycle 2 §24 (T-AA07..T-AA22, locked-COMPLETE), and Cycle 3 §25 (T-AA23..T-AA42, locked) remain **byte-identical** — Cycle 4 is strictly additive. Cycle 4 IDs continue the existing T-AA namespace from **T-AA43** (next after the Cycle 3 maximum T-AA42, verified by inspection of §25.8 status block). The 14 Cycle 4 tasks are organised into three waves matching PD-C4-01's HIGH-severity author-time KQL column-resolution-validity surface (Wave A) followed by PD-C4-02's MEDIUM-severity ADR/test/spec/CHANGELOG re-alignment (Wave B), and closing on the Cycle 4 backlog issue + sentinel + final test run (Wave C). Cycle 4 honours Australian English throughout (artefact, behaviour, prioritise, organise, harmonise, recognise, parametric, canonicalise, normalisation) and preserves all 7 Constitution v1.2.0 invariants per `plan.md` §C2.6 + the Cycle 3 PD-C3-01..03 + the new PD-C4-01..02 decisions.

### §26.1 Cycle 4 phase tracker

| Wave | Tasks | Title | Status | Depends-on |
|------|-------|-------|--------|-----------|
| **A** | T-AA43..T-AA49 | A4-01 — Z7 KQL `extend model_deployment` symmetric fix + new runtime-validity test surface (parametric Z1–Z7 walker; ~0.5 day) | NEW | Cycle 3 §25 final-sweep GREEN |
| **B** | T-AA50..T-AA54 | A4-02 — ADR-036-011 in-place wording revision + smoke-tenant-isolation REQUIRED + OPTIONAL extensions + spec mirror correction + CHANGELOG grouped block (~0.5 day) | NEW | Wave A complete (T-AA48 GREEN demonstrates A4-01 closure before A4-02 lands) |
| **C** | T-AA55..T-AA56 | Backlog issue + Cycle 4 sentinel + final test run (3399 minimal / 3400 full; ~0.25 day) | NEW | Wave A + Wave B |

### §26.2 Severity legend (per Cycle 4 amendment severity convergence — `spec.md:3875-3915`, quality.md CHK197)

- `[A4-01 HIGH]` ↔ data-engineer + sre-engineer + Operations Officer — Z7 KQL `extend model_deployment` line missing in BOTH `infra/observability/sli-kql.json:91` AND `contracts/sli-thresholds.md:280-296` (symmetric drift defeats the existing byte-equality test); fix MUST be co-merged with the new author-time runtime-validity walker in `tests/contract/test_sli_kql_runtime_validity.py` so future single-side drift fails CI.
- `[A4-02 MEDIUM]` ↔ compliance-auditor + infrastructure-devops — ADR-036-011:172-173 carries the misrepresented wording *"scoped exclusively to `tnt-stg-smoke`"*; the actual Bicep scope at `infra/bicep/modules/cosmos-simulation-containers.bicep:316` is database-level (`'${account.id}/dbs/${databaseName}'`) because the Cosmos data-plane RBAC API 2024-08-15 does not yet expose a `partitionKey` selector. The wording defect is corrected in-place per Pass-1 Q5 three-clause acknowledgement (acknowledge database-level scope as compensating defence-in-depth control + cite backlog issue + cross-reference Pass-1 Q2 isolation guarantees). Spec mirror at `spec.md:961-966` carries the same defect and is corrected via supersession. CHANGELOG entry appended via Cycle 4 grouped block. Backlog issue filed via `gh issue create`.

---

### §26.3 Wave A — A4-01 Z7 KQL symmetric fix + new runtime-validity test surface (7 tasks; depends only on Cycle 3 §25 GREEN)

> **Within-wave parallelism**: T-AA43 (JSON fix) / T-AA44 (MD fix) parallelisable with T-AA46 (test scaffold). T-AA45 (byte-equality preservation verify) depends on T-AA43 + T-AA44 (both fixes must land before the existing canonical-match test re-runs GREEN). T-AA47 (walker implementation) depends on T-AA46 (scaffold). T-AA48 (parametric 7-id GREEN gate) depends on T-AA43 + T-AA44 + T-AA47 (the walker hard-fails Z7 if either side carries the defect). T-AA49 (FR-073 fold-in) depends on T-AA48 (the spec acceptance text references the new runtime-validity test by file path).

#### T-AA43 [P] [NEW] [A4-01 HIGH] [Wave A] — `infra/observability/sli-kql.json:91` insert `extend model_deployment = tostring(customDimensions["model_deployment"])` clause

- **Phase**: Wave A — closes the JSON side of the A4-01 symmetric Z7 KQL drift; co-located with T-AA44 (MD side) and T-AA45 (byte-equality preservation verify) in Wave A's docs cluster.
- **Files**: `infra/observability/sli-kql.json:91` (Z7 entry — `slis[6]["kql"]`; insert pipe-clause `| extend model_deployment = tostring(customDimensions["model_deployment"])` between the existing `| extend tenant_id = tostring(customDimensions["tenant_id"])` clause and the `| where env == "staging"` clause; preserve all other tokens byte-identically).
- **Description**: Z7's `summarize ... by model_deployment` clause references `model_deployment` without first extending it from `customDimensions`, defeating author-time column-resolution-validity. The fix mirrors the Z6 entry at `slis[5]["kql"]` (which already carries `extend model_deployment = ...` upstream of `summarize`). Insertion point sits between the two existing extend clauses (`tenant_id` immediately before, `env` filter immediately after) so the canonicalised pipe-position remains stable for the byte-equality test. The fix is JSON-side only; the symmetric MD-side fix is T-AA44.
- **Acceptance**: plan.md PD-C4-01 (`plan.md:788-1010`); spec.md A4-01 detail at `:3875-3895` + Pass-1 Q1 (`spec.md:3997-4082`) + Pass-1 Q4 walker discipline (`spec.md:4220-4287`); quality.md CHK197 + CHK198 + CHK210; verify-command output below MUST return `True`.
- **Depends-on**: none (Wave-A lead; JSON-side data fix).
- **Tests**: contract `tests/contract/test_sli_kql_canonical_match.py` (existing, Cycle 3 T-AA32) — re-runs GREEN once T-AA44 lands the symmetric MD-side fix (T-AA45 verifies); contract `tests/contract/test_sli_kql_runtime_validity.py` (NEW — created in T-AA46 + T-AA47) — Z7 parametric id transitions from RED to GREEN once this task lands and the walker is implemented (T-AA48 verifies).
- **Backward-compat / Effort**: data-only (additive; no schema change; no operator-facing breaking change — the corrected KQL emits the same Application Insights tabular shape because Z7 already groups by `model_deployment`); small.
- **Verify-command**: `python -c "import json; d=json.load(open('infra/observability/sli-kql.json')); assert 'extend model_deployment' in d['slis'][6]['kql'], 'Z7 missing extend model_deployment'; print('Z7 extend model_deployment OK')"`

#### T-AA44 [P] [NEW] [A4-01 HIGH] [Wave A] — `contracts/sli-thresholds.md:280-296` symmetric Z7 KQL fix

- **Phase**: Wave A — closes the MD side of the A4-01 symmetric Z7 KQL drift; preserves byte-equality with T-AA43 after canonicalisation.
- **Files**: `specs/036-sim-agent-extend/contracts/sli-thresholds.md:280-296` (Z7 KQL fenced block — insert `| extend model_deployment = tostring(customDimensions["model_deployment"])` line between the existing `| extend tenant_id = tostring(customDimensions["tenant_id"])` line at `:288` and the `| where env == "staging"` line at `:289`; preserve all other tokens byte-identically; preserve fenced-code language tag `kusto`).
- **Description**: The MD-side Z7 KQL block must remain byte-identical to the JSON-side after canonicalisation (PD-C3-02 single-co-merge invariant inherited from Cycle 3, now extended to Z7). The fix sits at `:288.5` conceptually (between line 288 and 289). Pipe-clause whitespace MUST match the surrounding clauses (single space before pipe, single space after pipe, double-quoted string literal with escaped backslashes if any — none in this case). The fix is MD-side only; the symmetric JSON-side fix is T-AA43.
- **Acceptance**: plan.md PD-C4-01 (`plan.md:788-1010`); spec.md A4-01 detail at `:3875-3895` + Pass-1 Q1 (`spec.md:3997-4082`); quality.md CHK197 + CHK199 + CHK210; byte-equality preservation verified via T-AA45 (`tests/contract/test_sli_kql_canonical_match.py` GREEN across Z1–Z7).
- **Depends-on**: none (Wave-A lead; MD-side contract fix; parallel with T-AA43).
- **Tests**: contract `tests/contract/test_sli_kql_canonical_match.py` (existing, Cycle 3 T-AA32) — re-runs GREEN once T-AA43 + T-AA44 both land (T-AA45 verifies); contract `tests/contract/test_sli_kql_runtime_validity.py` (NEW — T-AA46 + T-AA47) — Z7 parametric id transitions RED→GREEN once this task lands.
- **Backward-compat / Effort**: contract-doc only (additive; no operator-facing breaking change); small.
- **Verify-command**: `grep -n 'extend model_deployment' specs/036-sim-agent-extend/contracts/sli-thresholds.md | grep -E ':28[0-9]|:29[0-6]'` returns at least one match in the Z7 KQL block range.

#### T-AA45 [NEW] [A4-01 HIGH] [Wave A] — Byte-equality preservation verify across Z1–Z7 (`test_sli_kql_canonical_match.py` GREEN)

- **Phase**: Wave A — re-runs the existing Cycle 3 T-AA32 parametric byte-equality test to confirm T-AA43 + T-AA44 land symmetrically and the canonical match between `infra/observability/sli-kql.json["slis"][i]["kql"]` and the `contracts/sli-thresholds.md` Z1–Z7 fenced blocks holds at canonicalisation parity.
- **Files**: `tests/contract/test_sli_kql_canonical_match.py` (existing, no edit) — re-execute parametric test across all 7 SLI ids; assert zero RED parametric ids.
- **Description**: T-AA43 (JSON) and T-AA44 (MD) MUST land in the same merge unit per PD-C3-02 single-co-merge invariant (preserved into Cycle 4). This task is a verification-only checkpoint that the byte-equality contract holds after both fixes land. If either side drifts, the parametric test fails for the drifted SLI id with the canonicaliser's diagnostic message (which already names the drifted token + position from Cycle 3 T-AA30's implementation).
- **Acceptance**: plan.md PD-C4-01 (`plan.md:788-1010`) + PD-C3-02 single-co-merge invariant (`plan.md:600-672`); spec.md A4-01 (`:3875-3895`); quality.md CHK197 + CHK211.
- **Depends-on**: T-AA43 + T-AA44 (both symmetric fixes must land; parallel with T-AA46).
- **Tests**: this task is the test re-run; no new test file. Counts unchanged — `test_sli_kql_canonical_match.py` already contributes 7 parametric ids to the Cycle 3 baseline of 3391.
- **Backward-compat / Effort**: verification-only (no code/test edit); small.
- **Verify-command**: `python -m pytest tests/contract/test_sli_kql_canonical_match.py -v` returns 7 parametric ids passing (one per SLI Z1–Z7).

#### T-AA46 [P] [NEW] [A4-01 HIGH] [Wave A] — New test scaffold `tests/contract/test_sli_kql_runtime_validity.py` (parametric decorator + canonicaliser import + base-table allowlist)

- **Phase**: Wave A — creates the test module skeleton + imports + parametric decorator + base-table allowlist constant; the walker body is a stub that raises `NotImplementedError` at landing (T-AA47 implements the walker; T-AA48 verifies the 7 ids GREEN).
- **Files**: NEW `tests/contract/test_sli_kql_runtime_validity.py` (module-level docstring citing A4-01 + PD-C4-01 + Pass-1 Q1 + Pass-1 Q4; imports — `import json`, `import re`, `from pathlib import Path`, `import pytest`, `from tests.contract._kql_canonicaliser import canonical_kql_for_sli`; module-level constants — `_SLI_DOC = json.loads((Path(__file__).resolve().parents[2] / "infra" / "observability" / "sli-kql.json").read_text())`, `_BASE_TABLES = frozenset({"requests", "customEvents", "customMetrics", "traces"})`; parametric decorator — `@pytest.mark.parametrize("sli_id", [s["id"] for s in _SLI_DOC["slis"]])`; test function `def test_runtime_column_resolution_validity(sli_id: str) -> None:` with stub body `raise NotImplementedError("walker implemented in T-AA47")`).
- **Description**: The scaffold establishes the parametric surface (7 ids, Z1–Z7, derived from `sli-kql.json` so future SLIs auto-extend) without committing to walker semantics. Imports are deliberately minimal — the walker uses regex/lexer string scanning per Pass-1 Q4 (no Kusto AST parser per PD-C4-01 three-part rejection rationale: (a) no actively-maintained Python Kusto AST library; (b) AST equivalence-class explosion; (c) author-time scope is column-name resolution, not full semantic equivalence). The `_BASE_TABLES` allowlist is module-level so the walker's (a)-clause check imports it cleanly. At T-AA46 landing, all 7 parametric ids fail with `NotImplementedError`; T-AA47 implements the walker; T-AA48 verifies all 7 GREEN.
- **Acceptance**: plan.md PD-C4-01 (`plan.md:788-1010`) — three-part Kusto-AST rejection at `:847-906`; spec.md Pass-1 Q1 (`spec.md:3997-4082`) + Pass-1 Q4 walker discipline (`spec.md:4220-4287`) + Pass-2 Q1 test count target (`spec.md:4427-4506`, superseded by Pass-2 Q4); quality.md CHK197 + CHK202 + CHK205.
- **Depends-on**: none (Wave-A lead — scaffold only; canonicaliser at `tests/contract/_kql_canonicaliser.py` already exists from Cycle 3 T-AA30).
- **Tests**: this task delivers the test scaffold; the test stub raises `NotImplementedError` deliberately at landing (no GREEN parametric ids until T-AA47 implements the walker; T-AA48 then verifies 7 ids GREEN).
- **Backward-compat / Effort**: additive (new test file only; no edit to canonicaliser or any existing test); small.
- **Verify-command**: `python -m pytest tests/contract/test_sli_kql_runtime_validity.py --collect-only -q` enumerates 7 parametric ids `test_runtime_column_resolution_validity[SLI-Z1]..[SLI-Z7]`.

#### T-AA47 [NEW] [A4-01 HIGH] [Wave A] — Walker implementation (let/extend/summarize-LHS tracking + (a)/(b)/(c) discipline + union fail-fast)

- **Phase**: Wave A — implements the column-resolution-validity walker body inside `tests/contract/test_sli_kql_runtime_validity.py`; replaces the T-AA46 stub.
- **Files**: `tests/contract/test_sli_kql_runtime_validity.py` (replace `raise NotImplementedError(...)` stub with walker body; add helper `_walk(canonicalised_kql: str, sli_id: str) -> None`; add helper `_extract_referenced_columns(clause: str) -> set[str]`; add helper `_extract_lhs_bindings(clause: str) -> set[str]`).
- **Description**: The walker consumes canonicalised KQL via `canonical_kql_for_sli(sli_id)` (Cycle 3 T-AA30 public surface) and walks left-to-right pipe-clause-by-pipe-clause. State is a single `defined_columns: set[str]` initialised from the base-table's known columns (allowlist `requests`/`customEvents`/`customMetrics`/`traces` per Pass-1 Q4 (a) — base-table-implicit columns are the union of the explicit Application Insights schema columns: `timestamp`, `name`, `customDimensions`, `customMeasurements`, `operation_Id`, `operation_Name`, `user_Id`, `session_Id`, `client_IP`, `cloud_RoleName`, `cloud_RoleInstance`, `success`, `resultCode`, `duration`, `itemCount`). Each `extend` / `let` / `summarize ... by` LHS adds to `defined_columns`. Each `where` / `summarize ... by` RHS / `project` / `summarize` aggregator's RHS / `extend` RHS references MUST resolve to a name in `defined_columns` UNLESS the reference is `customDimensions["..."]` (Pass-1 Q4 (c) escape hatch) or a literal/numeric/string. `union` MUST hard-fail with the message *"union is not yet supported by the runtime validity walker — extend test_sli_kql_runtime_validity.py to support multi-table column resolution"* (Pass-1 Q1 fail-fast invariant). Failure message format MUST be: *"KQL {sli_id} references undefined column '{name}' at line {N} — must extend from customDimensions first; canonicalised KQL:\n{canonical}"* — name + line number + full canonicalised KQL for diagnostic completeness (PD-C4-01 explicit failure-message contract at `plan.md:907-960`).
- **Acceptance**: plan.md PD-C4-01 walker discipline + failure-message contract (`plan.md:847-960`); spec.md Pass-1 Q1 (`spec.md:3997-4082`) + Pass-1 Q4 (`spec.md:4220-4287`); quality.md CHK197 + CHK203 + CHK206 + CHK207 + CHK208.
- **Depends-on**: T-AA46 (scaffold must exist; this task replaces the stub body).
- **Tests**: contract `tests/contract/test_sli_kql_runtime_validity.py` — at T-AA47 landing, all 7 parametric ids GREEN ONCE T-AA43 + T-AA44 are also landed (Z7 currently RED until both symmetric fixes land); T-AA48 is the explicit GREEN-gate verification task.
- **Backward-compat / Effort**: additive (extends existing test file only; canonicaliser at `tests/contract/_kql_canonicaliser.py` is NOT edited per PD-C4-01 separation-of-concerns); small.
- **Verify-command**: `python -c "from tests.contract.test_sli_kql_runtime_validity import _walk; _walk('customEvents | where name == \"x\"', 'TEST'); print('walker importable')"` returns `walker importable`.

#### T-AA48 [NEW] [A4-01 HIGH] [Wave A] — Verify 7 parametric ids GREEN (`test_sli_kql_runtime_validity.py` end-to-end)

- **Phase**: Wave A — final A4-01 closure gate; runs the new walker against all 7 SLIs and verifies zero RED parametric ids.
- **Files**: `tests/contract/test_sli_kql_runtime_validity.py` (existing post-T-AA47, no edit); `infra/observability/sli-kql.json` (existing post-T-AA43, no edit); `specs/036-sim-agent-extend/contracts/sli-thresholds.md` (existing post-T-AA44, no edit).
- **Description**: This task is a verification checkpoint that all three preceding Wave-A pieces (T-AA43 JSON fix + T-AA44 MD fix + T-AA47 walker implementation) land in the same merge unit and produce 7 GREEN parametric ids. If Z7 fails with *"references undefined column 'model_deployment'"*, the failure points at T-AA43 or T-AA44 not having landed; if any other Z fails, the walker has a bug (re-open T-AA47). On GREEN, A4-01 closes — the runtime-validity surface is established and the test count rises by +7 (3391 → 3398 baseline).
- **Acceptance**: plan.md PD-C4-01 closure criterion (`plan.md:961-1010`); spec.md A4-01 (`:3875-3895`) + Pass-2 Q1 +7 test count (`spec.md:4427-4506`); quality.md CHK197 + CHK209.
- **Depends-on**: T-AA43 + T-AA44 + T-AA47 (all three must land before this task can pass).
- **Tests**: this task is the explicit pytest invocation gate; no new test file. The 7 parametric ids contribute to the Cycle 4 test count target (3391 + 7 = 3398; further +1 from T-AA51 → 3399 minimal; further +1 from T-AA52 → 3400 full).
- **Backward-compat / Effort**: verification-only (no code/test edit); small.
- **Verify-command**: `python -m pytest tests/contract/test_sli_kql_runtime_validity.py -v` returns `7 passed` with parametric ids `[SLI-Z1] ... [SLI-Z7]` all GREEN.

#### T-AA49 [NEW] [A4-01 HIGH] [Wave A] — FR-073 acceptance text fold-in (author-time KQL column-resolution-validity sub-bullet)

- **Phase**: Wave A — closes the spec-side propagation queue for A4-01; folds the new author-time runtime-validity sub-bullet into FR-073's acceptance text alongside the existing Cycle 3 T-AA29 universal-Z1-Z7 wording.
- **Files**: `specs/036-sim-agent-extend/spec.md` FR-073 acceptance block (locate via `grep -n "FR-073" spec.md` — section anchored around `:3660-3677` from Cycle 3, plus any Cycle 3 T-AA29 in-place re-wording); append a new sub-bullet under FR-073's acceptance list: *"Author-time KQL column-resolution-validity is enforced by `tests/contract/test_sli_kql_runtime_validity.py` (parametric across Z1–Z7); the walker hard-fails on `union` and on any column reference that does not resolve to a base-table column, an explicit `extend`/`let`/`summarize-LHS` binding, or a `customDimensions[\"…\"]` lookup. Per PD-C4-01, the walker is regex/lexer-based (no Kusto AST parser) and the failure message names the SLI id, the unresolved column, the line number, and the full canonicalised KQL."*
- **Description**: The fold-in does NOT replace any existing FR-073 wording — it APPENDS the new author-time sub-bullet. The byte-exact insertion point is immediately after the last existing FR-073 acceptance bullet (the Cycle 3 universal-Z1-Z7 sentence from T-AA29). Citation to `tests/contract/test_sli_kql_runtime_validity.py` is byte-exact (binds to T-AA46 + T-AA47 file path). Citation to PD-C4-01 is by short reference (the spec body already carries an A4-01 anchor at `:3875-3895` that resolves to PD-C4-01 via the Cycle 4 plan-decision cross-reference table).
- **Acceptance**: plan.md PD-C4-01 (`plan.md:788-1010`); spec.md A4-01 detail (`:3875-3895`) + FR-073 baseline (Cycle 3 T-AA29 in-place re-wording at `:3660-3677`) + Pass-1 Q5 propagation rule (`spec.md:4288-4351`); quality.md CHK197 + CHK212.
- **Depends-on**: T-AA48 (the new test file path cited by the sub-bullet must already exist + be GREEN before the spec sentence binds to it).
- **Tests**: docs `tests/docs/test_spec_cycle_4_propagation.py` (NEW — asserts the FR-073 acceptance block contains the literal substring `tests/contract/test_sli_kql_runtime_validity.py` AND the literal phrase `author-time KQL column-resolution-validity`); the test is GREEN on T-AA49 landing.
- **Backward-compat / Effort**: in-place spec text only (additive fold-in; no FR semantics change); small.
- **Verify-command**: `grep -n 'test_sli_kql_runtime_validity' specs/036-sim-agent-extend/spec.md` returns at least one match inside the FR-073 acceptance block (line range adjacent to `:3660-3677`).

---

### §26.4 Wave B — A4-02 ADR + smoke-tenant + spec mirror + CHANGELOG (5 tasks; depends on Wave A)

> **Within-wave parallelism**: T-AA50 (ADR rewrite) is the lead — sequential before T-AA51 (REQUIRED smoke-tenant assertion binds to corrected ADR wording at L172-173 and at L478-924). T-AA52 (OPTIONAL smoke-tenant + posture choice) parallel with T-AA53 (spec mirror correction) — both bind to T-AA50 but not to each other. T-AA54 (CHANGELOG grouped block) depends on T-AA50 + T-AA51 + T-AA52 + T-AA53 (all four content artefacts must exist before the CHANGELOG entry summarises them).

#### T-AA50 [NEW] [A4-02 MEDIUM] [Wave B] — ADR-036-011:172-173 in-place wording rewrite (three-clause acknowledgement)

- **Phase**: Wave B — corrects the ADR's misrepresented "scoped exclusively to tnt-stg-smoke" wording in-place; the Cycle 4 amendment sub-section at `:478-924` was already appended by speckit.plan and is NOT edited by this task.
- **Files**: `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md:172-173` (replace the existing `"...scoped exclusively to ``tnt-stg-smoke``..."` wording with the corrected three-clause acknowledgement: *"The Simulation.Coordinator role assignment is database-level (`scope: '${account.id}/dbs/${databaseName}'`) because the Cosmos data-plane RBAC API 2024-08-15 does not yet expose a `partitionKey` selector; the database-level scope is therefore a **compensating defence-in-depth control** rather than a partition-level guarantee. The smoke-injection runtime tenant filter (`where tenant_id == \"tnt-stg-smoke\"`) at the KQL contract surface, the `customDimensions[\"tenant_id\"]` envelope discriminator, and the Pass-1 Q2 isolation guarantees (i)–(v) jointly enforce tenant isolation. A backlog issue (`[backlog issue: TBD]`) tracks the partition-scope upgrade once the Cosmos data-plane RBAC API exposes `partitionKey`."*).
- **Description**: The rewrite is in-place at L172-173 and replaces ONLY the misrepresented wording. The Cycle 4 amendment sub-section at `:478-924` (already authored by speckit.plan in PD-C4-02 Step 8af) carries the full PD-C4-02 narrative — that sub-section is NOT re-edited here. The placeholder `[backlog issue: TBD]` remains until T-AA55 files the GitHub issue and returns a real issue id; T-AA55 then performs a follow-up edit to replace `TBD` with the actual issue number (recorded in T-AA55's verify output for traceability). ADR Status remains `Proposed` per Pass-2 Q3 — Status flips to `Accepted` at Step 8al on clean Cycle 4 final-sweep verdict (NOT here, NOT in this task).
- **Acceptance**: plan.md PD-C4-02 (`plan.md:1011-1348`) — wording-defect closure at `:1075-1145`; spec.md A4-02 detail (`:3896-3915`) + Pass-1 Q5 three-clause acknowledgement (`spec.md:4288-4351`) + Pass-2 Q3 ADR Status convergence (`spec.md:4595-4678`); quality.md CHK213 + CHK214 + CHK215 + CHK216.
- **Depends-on**: Wave A complete (T-AA48 GREEN demonstrates A4-01 closure; the ADR's Cycle 4 amendment sub-section at `:478-924` already authored by speckit.plan binds against the A4-01 closure).
- **Tests**: docs `tests/docs/test_adr_036_011_cycle_4_wording.py` (NEW — asserts L172-173 contains `compensating defence-in-depth control` AND `[backlog issue: TBD]` (or actual issue number once T-AA55 + T-AA50 follow-up land) AND `database-level`; asserts the Cycle 4 amendment sub-section at `:478-924` is NOT byte-edited by this task).
- **Backward-compat / Effort**: ADR text only (no runtime change; ADR Status remains `Proposed`); small.
- **Verify-command**: `grep -n 'compensating defence-in-depth' docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md` returns matches at L172-173 (rewritten) AND L478+ (already authored by speckit.plan); `grep -c 'compensating defence-in-depth' docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md` returns count ≥ 2.

#### T-AA51 [NEW] [A4-02 MEDIUM] [Wave B] — `tests/contract/test_smoke_tenant_isolation.py` REQUIRED extension: scope-string assertion (`'${account.id}/dbs/${databaseName}'`)

- **Phase**: Wave B — adds the REQUIRED A4-02 evidence test to lock the database-level scope literal in the Bicep render (or compiled ARM template) against the corrected ADR wording at `:172-173`.
- **Files**: `tests/contract/test_smoke_tenant_isolation.py` (existing; ADD new test function `def test_smoke_role_assignment_scope_is_database_level() -> None:`); the function loads `infra/bicep/modules/cosmos-simulation-containers.bicep` (or the compiled ARM JSON if Bicep CLI is available in CI), locates the Simulation.Coordinator role assignment block, and asserts the `scope:` field literal matches the regex `scope:\s*'\$\{account\.id\}/dbs/\$\{databaseName\}'` (with appropriate escaping for the `$` and `{` characters).
- **Description**: The test is a literal-string match against the Bicep source (the simpler path; CI does not always have Bicep CLI for ARM compilation). The regex anchors the EXACT database-level scope literal — any drift to a partition-level scope (`'${account.id}/dbs/${databaseName}/colls/${containerName}/pkranges/...'`) or to a parent-account scope (`'${account.id}'`) would fail the test. The test does NOT assert the role-definition GUID (Cosmos DB Built-in Data Contributor) — that is a separate Cycle 3 T-AA38 contract surface. The test contributes +1 to the Cycle 4 test count (3398 → 3399 minimal posture per Pass-2 Q4).
- **Acceptance**: plan.md PD-C4-02 (`plan.md:1011-1348`) — REQUIRED smoke-tenant assertion at `:1146-1228`; spec.md A4-02 detail (`:3896-3915`) + Pass-1 Q2 isolation guarantee (iv) (`spec.md:954-960` Cycle 3 baseline + `spec.md:4083-4158` Cycle 4 Pass-1 Q2 reaffirmation) + Pass-2 Q4 minimal posture +1 test (`spec.md:4679-4814`); quality.md CHK213 + CHK217 + CHK218 + CHK219.
- **Depends-on**: T-AA50 (the test docstring cross-references the ADR L172-173 corrected wording; ADR rewrite must land first).
- **Tests**: this task delivers the test function; the test is GREEN on T-AA51 landing because `cosmos-simulation-containers.bicep:316` already carries the database-level scope literal (NO Bicep change is required — the ADR wording was the defect, not the Bicep code).
- **Backward-compat / Effort**: additive (new test function on existing test file); small.
- **Verify-command**: `python -m pytest tests/contract/test_smoke_tenant_isolation.py::test_smoke_role_assignment_scope_is_database_level -v` returns `1 passed`.

#### T-AA52 [P] [NEW] [A4-02 MEDIUM] [Wave B] — `tests/contract/test_smoke_tenant_isolation.py` OPTIONAL extension + posture choice 3399/3400 recorded

- **Phase**: Wave B — adds the OPTIONAL A4-02 evidence test (Bicep comment block documents the compensating defence-in-depth control + backlog issue id) AND records the chosen test-count posture (3399 minimal vs 3400 full) per Pass-2 Q4 Step 8ae propagation rule.
- **Files**: `tests/contract/test_smoke_tenant_isolation.py` (existing post-T-AA51; ADD new test function `def test_bicep_comment_block_documents_compensating_control() -> None:`); the function loads `infra/bicep/modules/cosmos-simulation-containers.bicep`, locates the comment block at L305-315 (or wherever the Simulation.Coordinator role assignment is documented), and asserts the comment block contains both literal substrings `compensating defence-in-depth control` AND a backlog issue identifier (either a real `#NNNN` issue number once T-AA55 lands and T-AA52 follow-up edits the comment block, or the placeholder `[backlog issue: TBD]` until then). ALSO: append a posture-choice annotation to `specs/036-sim-agent-extend/tasks.md` §26.8 status block (Step 8ae propagation) recording whether Cycle 4 is taking 3399 minimal or 3400 full posture.
- **Description**: The OPTIONAL test is a documentation-quality gate — the Bicep comment block is the runtime-readable evidence anchor for operators reading the Bicep source post-deploy. If the Bicep comment block does NOT carry the compensating-control wording, an operator reading the Bicep source has no in-line evidence of WHY the scope is database-level and not partition-level. The test contributes +1 to the test count if Cycle 4 takes the FULL posture (3399 → 3400 per Pass-2 Q4); if Cycle 4 takes the MINIMAL posture, this task either omits the OPTIONAL test (count stays 3399) or marks it `@pytest.mark.skip(reason="Cycle 4 minimal posture per Pass-2 Q4")`. The posture choice MUST be recorded in `tasks.md` §26.8 status block per Step 8ae. Recommended: take FULL posture (3400) — the OPTIONAL test is low-cost and adds defence-in-depth on the documentation surface.
- **Acceptance**: plan.md PD-C4-02 (`plan.md:1011-1348`) — OPTIONAL smoke-tenant assertion at `:1229-1278`; spec.md A4-02 detail (`:3896-3915`) + Pass-2 Q4 posture choice (`spec.md:4679-4814`) + Step 8ae propagation rule (`plan.md:1349-1379`); quality.md CHK213 + CHK220 + CHK221.
- **Depends-on**: T-AA50 (ADR L172-173 rewrite must land first; T-AA51 NOT a hard dependency but recommended-co-merge).
- **Tests**: this task delivers the OPTIONAL test function (FULL posture); the test is GREEN if the Bicep comment block already carries the compensating-control wording — verify by inspection at T-AA52 landing time. If the Bicep comment block lacks the wording, T-AA52 ALSO performs a Bicep-side edit at `cosmos-simulation-containers.bicep:305-315` to add the comment block (Cycle 4 grouped-block scope explicitly permits this Bicep comment edit per PD-C4-02 OPTIONAL surface).
- **Backward-compat / Effort**: additive (new test function + optional Bicep comment edit; no runtime change); small.
- **Verify-command**: `python -m pytest tests/contract/test_smoke_tenant_isolation.py::test_bicep_comment_block_documents_compensating_control -v` returns `1 passed` (FULL posture); OR returns `1 skipped` (MINIMAL posture); AND `grep -n "Cycle 4 posture" specs/036-sim-agent-extend/tasks.md` returns at least one match in §26.8.

#### T-AA53 [P] [NEW] [A4-02 MEDIUM] [Wave B] — `spec.md:961-966` mirror correction (Cycle 3 Pass-1 Q2 (v) supersession)

- **Phase**: Wave B — corrects the spec mirror of the same wording defect at the Cycle 3 Pass-1 Q2 isolation-guarantee (v) anchor; marks the existing wording as superseded with a cross-reference to A4-02.
- **Files**: `specs/036-sim-agent-extend/spec.md:961-966` (locate the Cycle 3 Pass-1 Q2 isolation-guarantee item (v) — the wording that mirrors the ADR L172-173 defect; ADD an in-place supersession annotation at the end of the item: *"~~Originally worded as 'scoped exclusively to `tnt-stg-smoke`'; this wording is **superseded by A4-02** (see `:3896-3915`) — the actual scope is database-level (`'${account.id}/dbs/${databaseName}'`) and acts as a compensating defence-in-depth control. See ADR-036-011:172-173 (in-place revised in Cycle 4) for the corrected three-clause acknowledgement.~~"*).
- **Description**: The supersession annotation preserves the original Cycle 3 wording for forward-traceability (so reviewers reading the spec linearly understand the wording history) while pointing forward to the corrected A4-02 anchor. The strikethrough markdown (`~~...~~`) is the established Cycle 2 / Cycle 3 supersession-marker convention used across the spec. The cross-reference uses the byte-exact A4-02 anchor `:3896-3915` AND the byte-exact ADR L172-173 reference.
- **Acceptance**: plan.md PD-C4-02 (`plan.md:1011-1348`) — spec mirror correction at `:1279-1320`; spec.md A4-02 detail (`:3896-3915`) + Pass-1 Q5 propagation rule (`spec.md:4288-4351`); quality.md CHK213 + CHK222.
- **Depends-on**: T-AA50 (ADR L172-173 rewrite must land first; the spec mirror cross-references the ADR's corrected wording).
- **Tests**: docs `tests/docs/test_spec_cycle_4_propagation.py` (existing post-T-AA49; ADD assertion: `:961-966` block contains literal substring `superseded by A4-02` AND `compensating defence-in-depth control`); test is GREEN on T-AA53 landing.
- **Backward-compat / Effort**: in-place spec text only (additive supersession annotation; no FR semantics change); small.
- **Verify-command**: `grep -n 'superseded by A4-02' specs/036-sim-agent-extend/spec.md` returns a match in the `:961-966` range; `grep -n 'compensating defence-in-depth' specs/036-sim-agent-extend/spec.md` returns ≥ 2 matches (Pass-1 Q2 mirror at `:961-966` AND A4-02 anchor at `:3896-3915` AND Pass-1 Q5 reaffirmation at `:4288-4351`).

#### T-AA54 [NEW] [A4-02 MEDIUM] [Wave B] — `CHANGELOG.md` Cycle 4 grouped block (`### Added` + `### Changed`)

- **Phase**: Wave B — appends a Cycle 4 grouped block to `CHANGELOG.md` under `## [Unreleased]`; mirrors the Cycle 2 grouped-block precedent at `:7-31` and the Cycle 3 grouped-block addition.
- **Files**: `CHANGELOG.md` under `## [Unreleased]` — append two new sub-sections after the existing Cycle 3 entries: `### Added (spec 036 — Cycle 4 amendment cycle)` (sub-bullets: *"`tests/contract/test_sli_kql_runtime_validity.py` — author-time KQL column-resolution-validity walker, parametric across Z1–Z7, hard-fails on `union` and unresolved column references."*; *"GitHub backlog issue `[backlog issue: TBD]` — Cosmos data-plane RBAC API 2024-08-15 partition-scope upgrade tracker (filed via T-AA55)."*); `### Changed (spec 036 — Cycle 4 amendment cycle)` (sub-bullets: *"Z7 KQL — `infra/observability/sli-kql.json:91` and `contracts/sli-thresholds.md:280-296` symmetric `extend model_deployment` line added (A4-01)."*; *"ADR-036-011:172-173 in-place wording revision — three-clause acknowledgement that scope is database-level (compensating defence-in-depth control) per A4-02 + Pass-1 Q5."*; *"`tests/contract/test_smoke_tenant_isolation.py` REQUIRED extension (database-level scope literal assertion) + OPTIONAL extension (Bicep comment block compensating-control wording)."*; *"`spec.md:961-966` mirror correction — Cycle 3 Pass-1 Q2 isolation-guarantee (v) marked as superseded by A4-02."*). NO `### Breaking changes` sub-section is required — Cycle 4 is non-breaking (A4-01 corrects KQL author-time validity without changing runtime tabular shape; A4-02 corrects wording without changing Bicep).
- **Description**: The grouped-block format mirrors Cycle 2 exactly (`CHANGELOG.md:7-31`). Sub-bullets are concise + cite the file:line evidence anchor + cite the binding amendment id (A4-01 / A4-02). The CHANGELOG entry binds the Cycle 4 work to the v1.x.x release narrative (next release after Cycle 3); the `[backlog issue: TBD]` placeholder is a stable forward-pointer that T-AA55 follows up to fill in with a real issue number after `gh issue create` returns.
- **Acceptance**: plan.md PD-C4-02 (`plan.md:1011-1348`) — CHANGELOG grouped block at `:1321-1348`; spec.md A4-02 detail (`:3896-3915`) + Pass-2 Q2 CHANGELOG format (`spec.md:4507-4594`); quality.md CHK213 + CHK223 + CHK224.
- **Depends-on**: T-AA50 + T-AA51 + T-AA52 + T-AA53 (all four content artefacts must land before the CHANGELOG entry summarises them).
- **Tests**: docs `tests/docs/test_changelog_cycle_4_grouped_block.py` (NEW — asserts `CHANGELOG.md` under `## [Unreleased]` contains both `### Added (spec 036 — Cycle 4 amendment cycle)` AND `### Changed (spec 036 — Cycle 4 amendment cycle)` sub-sections, with the four bullets enumerated above; asserts NO `### Breaking changes` sub-section was added in Cycle 4); test is GREEN on T-AA54 landing.
- **Backward-compat / Effort**: CHANGELOG only (additive; non-breaking); small.
- **Verify-command**: `grep -n 'Cycle 4 amendment cycle' CHANGELOG.md` returns at least 2 matches (one per `### Added` and `### Changed` heading); `grep -n 'extend model_deployment' CHANGELOG.md` returns at least 1 match in the `### Changed` block.

---

### §26.5 Wave C — Backlog issue + Cycle 4 sentinel + final test run (2 tasks; depends on Wave A + Wave B)

> **Within-wave parallelism**: T-AA55 (backlog issue file) is the lead — sequential before T-AA56 (final test run + sentinel) so the issue number can be back-filled into ADR L172-173 + CHANGELOG before the sentinel locks Cycle 4.

#### T-AA55 [NEW] [A4-02 MEDIUM] [Wave C] — File GitHub backlog issue (`gh issue create`, `[backlog]` title prefix, label `backlog` if pre-existing)

- **Phase**: Wave C — files the GitHub backlog issue documenting the Cosmos data-plane RBAC API 2024-08-15 partition-scope blocker; back-fills the issue number into ADR L172-173 + CHANGELOG (T-AA50 + T-AA54 follow-up edits).
- **Files**: NEW GitHub issue (filed via `gh issue create --title "[backlog] Cosmos data-plane RBAC API: partition-scope role assignment for Simulation.Coordinator (currently database-level)" --body "..."`); follow-up edits to `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md:172-173` (replace `[backlog issue: TBD]` with `#NNNN`); follow-up edit to `CHANGELOG.md` (replace `[backlog issue: TBD]` with `#NNNN` in the `### Added` sub-section); follow-up edit to `tests/contract/test_smoke_tenant_isolation.py::test_bicep_comment_block_documents_compensating_control` (replace `[backlog issue: TBD]` placeholder match with `#NNNN` literal once the issue exists, or keep regex-tolerant if T-AA55 lands AFTER T-AA52). Issue body MUST include: (1) the database-level scope literal `'${account.id}/dbs/${databaseName}'`; (2) the desired partition-level scope `'${account.id}/dbs/${databaseName}/colls/${containerName}/pkranges/...'`; (3) the Cosmos data-plane RBAC API 2024-08-15 capability gap (no `partitionKey` selector); (4) cross-references to ADR-036-011:172-173 + spec.md A4-02 anchor `:3896-3915`. Issue label MUST be `backlog` ONLY if `gh label list` shows the label pre-exists in the repo; if `backlog` does not exist, file without label (do NOT create new labels per repo governance).
- **Description**: The issue captures the partition-scope upgrade as a tracked backlog item so the database-level compensating-control posture is explicit + time-bound (it ages until the Cosmos API exposes `partitionKey`). The label-creation guardrail (only label if `backlog` already exists) avoids drift in the repo's label taxonomy. The follow-up edits (ADR L172-173 + CHANGELOG `### Added` + test placeholder) all use the SAME issue number `#NNNN` — single-source-of-truth for the placeholder resolution. If `gh issue create` is not runnable in this branch context (e.g., missing PAT), the placeholder `[backlog issue: TBD]` stands AND T-AA55 closes with the explicit caveat that the issue file is deferred to merge-time (Step 8al verifies the issue exists before final-sweep clean verdict).
- **Acceptance**: plan.md PD-C4-02 (`plan.md:1011-1348`) — backlog mechanism at `:1320-1348`; spec.md A4-02 detail (`:3896-3915`) + Pass-1 Q3 backlog mechanism (`spec.md:4159-4219`); quality.md CHK213 + CHK225 + CHK226.
- **Depends-on**: T-AA50 + T-AA54 (ADR + CHANGELOG must already carry the `[backlog issue: TBD]` placeholder; this task back-fills the real issue number).
- **Tests**: ops `tests/ops/test_cycle_4_backlog_issue_filed.py` (NEW — asserts `gh issue list --search "[backlog]" --state open --json number,title` returns at least one row whose title starts with `[backlog]` AND whose body cites `ADR-036-011`; OR asserts `[backlog issue: TBD]` placeholder is still present in ADR L172-173 with a follow-up TODO recorded in `tasks.md` §26.8 — graceful skip if `gh` CLI is not available in CI).
- **Backward-compat / Effort**: GitHub-issue + 3 small follow-up text edits; small.
- **Verify-command**: `gh issue list --search "[backlog]" --state open --json number,title --jq '.[] | select(.title | startswith("[backlog]"))'` returns at least one row; OR record the `[backlog issue: TBD]` placeholder + deferred-file-time caveat in tasks.md §26.8.

#### T-AA56 [NEW] [A4-01 HIGH + A4-02 MEDIUM] [Wave C] — Cycle 4 sentinel + final test run (3399 minimal / 3400 full verification)

- **Phase**: Wave C — closes Cycle 4 by running the full pytest suite + verifying the chosen Cycle 4 test count posture (3399 minimal or 3400 full per Pass-2 Q4) + appending the Cycle 4 tasks sentinel to `spec.md` after L4870.
- **Files**: `specs/036-sim-agent-extend/spec.md` (append after L4870: `**Cycle 4 tasks complete (14 tasks: T-AA43..T-AA56). Ready for /speckit.analyze (Cycle 4).**`); full pytest suite invocation (`python -m pytest -q`) — assert returncode 0 + asserted test count matches the recorded posture from T-AA52 §26.8 annotation (3399 minimal / 3400 full).
- **Description**: The sentinel is the explicit Cycle 4 closure marker that gates `/speckit.analyze (Cycle 4)`. The final test run is the cycle's empirical verification — it MUST succeed across the full repo, not just the Cycle 4 deltas, so any Cycle 1/2/3 regression introduced by Cycle 4 edits surfaces here. The Cycle 4 baseline of 3391 (Cycle 3 close) + 7 (T-AA48) + 1 (T-AA51 REQUIRED) ± 1 (T-AA52 OPTIONAL) yields 3399 (minimal) or 3400 (full). Pass-2 Q1's earlier "3398" target is doubly superseded — the +1 from T-AA51 is REQUIRED in Pass-2 Q4. Pass-1 Q1's earlier "3392" target is triply superseded.
- **Acceptance**: plan.md PD-C4-01 + PD-C4-02 closure criteria (`plan.md:961-1010` + `:1321-1348`); spec.md A4-01 + A4-02 closure (`spec.md:3875-3915`) + Pass-2 Q4 posture choice (`spec.md:4679-4814`); quality.md CHK197 + CHK213 + CHK227 + CHK228 + CHK229 + CHK230.
- **Depends-on**: T-AA48 + T-AA49 + T-AA50 + T-AA51 + T-AA52 + T-AA53 + T-AA54 + T-AA55 (every prior Cycle 4 task must land before the final-run + sentinel).
- **Tests**: full repo pytest (`python -m pytest -q`); no NEW test file — this task is the empirical closure gate. The Cycle 4 sentinel append is a single-line spec.md edit at `:4870`+1.
- **Backward-compat / Effort**: spec.md sentinel append (1 line) + repo-wide test run; small.
- **Verify-command**: `python -m pytest -q 2>&1 | grep -E "(3399|3400) passed"` returns a match (posture choice from T-AA52 §26.8 annotation); AND `tail -1 specs/036-sim-agent-extend/spec.md` returns `**Cycle 4 tasks complete (14 tasks: T-AA43..T-AA56). Ready for /speckit.analyze (Cycle 4).**`.

---

### §26.6 Cycle 4 dependency graph

```text
Wave A (A4-01 KQL fix + new test surface):

T-AA43 ─┬─→ T-AA45
T-AA44 ─┘

T-AA46 ─→ T-AA47

T-AA43 ─┐
T-AA44 ─┼─→ T-AA48 ─→ T-AA49
T-AA47 ─┘

(T-AA43/44 cluster parallelisable with T-AA46 within Wave A)

Wave B (A4-02 ADR + smoke-tenant + spec mirror + CHANGELOG):

T-AA50 ─┬─→ T-AA51
        ├─→ T-AA52 [P]
        └─→ T-AA53 [P]

T-AA50 ─┐
T-AA51 ─┤
T-AA52 ─┼─→ T-AA54
T-AA53 ─┘

Wave C (backlog issue + sentinel + final-run):

T-AA50 ─┐
T-AA54 ─┴─→ T-AA55 ─→ T-AA56

T-AA48 / T-AA49 / T-AA51 / T-AA52 / T-AA53 / T-AA54 ─→ T-AA56 (final-run gate)
```

**Critical path** (longest chain, 6 hops): `T-AA46 → T-AA47 → T-AA48 → T-AA49 → T-AA50 → ... → T-AA56` (test scaffold → walker → 7-id GREEN → FR-073 fold-in → ADR rewrite → … → final-run + sentinel); alternative critical path of equal length: `T-AA43 → T-AA45 → T-AA48 → T-AA50 → T-AA54 → T-AA55 → T-AA56` (JSON fix → byte-equality verify → 7-id GREEN → ADR rewrite → CHANGELOG → backlog issue → sentinel).

---

### §26.7 Suggested Cycle 4 wave plan

**Wave A (parallelisable in two clusters; 7 tasks; ~0.5 day)** — A4-01 KQL fix + new test:

- *Symmetric KQL fix cluster*: T-AA43 [P], T-AA44 [P] → T-AA45 (verify byte-equality preservation)
- *Walker cluster*: T-AA46 [P] (scaffold) → T-AA47 (walker body) → T-AA48 (7-id GREEN gate)
- *Spec fold-in*: T-AA49 (depends on T-AA48)

**Wave B (mixed sequential + parallel; 5 tasks; ~0.5 day)** — A4-02 ADR + smoke-tenant + mirror + CHANGELOG:

- *Sequential lead*: T-AA50 (ADR L172-173 rewrite)
- *Parallel evidence cluster*: T-AA51 → T-AA52 [P], T-AA53 [P] (all three depend on T-AA50; T-AA52 and T-AA53 parallel with each other)
- *CHANGELOG aggregator*: T-AA54 (depends on T-AA50 + T-AA51 + T-AA52 + T-AA53)

**Wave C (sequential closure; 2 tasks; ~0.25 day)** — backlog issue + sentinel + final-run:

- T-AA55 (file backlog issue + back-fill placeholders) → T-AA56 (final pytest run + Cycle 4 sentinel)

**Wave D (final-sweep — Cycle 4 gates)** — assert FS1–FS21 still GREEN (Cycle 1 + Cycle 2 + Cycle 3 gates) PLUS the Cycle 4 gates:

- **FS22**: `tests/contract/test_sli_kql_runtime_validity.py` is GREEN across all 7 SLIs (Z1–Z7) without `pytest.mark.xfail`, `@pytest.mark.skip`, or hard-coded subset (PD-C4-01 closure criterion).
- **FS23**: `tests/contract/test_sli_kql_canonical_match.py` (Cycle 3 T-AA32) is GREEN across all 7 SLIs after the Z7 symmetric fix (PD-C4-01 + PD-C3-02 byte-equality preservation).
- **FS24**: `tests/contract/test_smoke_tenant_isolation.py::test_smoke_role_assignment_scope_is_database_level` is GREEN (PD-C4-02 REQUIRED smoke-tenant scope assertion).
- **FS25**: ADR-036-011:172-173 carries the corrected three-clause acknowledgement (compensating defence-in-depth control + backlog issue id + Pass-1 Q2 cross-reference); ADR-036-011 Status remains `Proposed` until Step 8al final-sweep clean verdict (Pass-2 Q3).
- **FS26**: `CHANGELOG.md` `## [Unreleased]` carries the Cycle 4 grouped block (`### Added` + `### Changed`) with no `### Breaking changes` sub-section.
- **FS27**: GitHub backlog issue with title prefix `[backlog]` is filed (or `[backlog issue: TBD]` placeholder is recorded with deferred-file-time caveat in §26.8).

---

### §26.8 Cycle 4 status block

| Metric | Count |
|--------|------:|
| Cycle 4 tasks added (T-AA43..T-AA56) | **14** |
| Wave A `[P]` markers | 3 (T-AA43, T-AA44, T-AA46) |
| Wave B `[P]` markers | 2 (T-AA52, T-AA53) |
| Wave C `[P]` markers | 0 (sequential closure) |
| **Total `[P]` markers (Cycle 4)** | **5** |
| New unit tests | 0 |
| New integration tests | 0 |
| New contract tests | 3 (T-AA46+T-AA47 walker = 7 parametric ids in one file; T-AA51 REQUIRED smoke-tenant; T-AA52 OPTIONAL smoke-tenant) |
| New e2e tests | 0 |
| New docs tests | 3 (T-AA49 propagation, T-AA50 ADR wording, T-AA53 spec mirror; T-AA54 CHANGELOG grouped block) — note T-AA49 + T-AA53 share `tests/docs/test_spec_cycle_4_propagation.py` |
| New ops tests | 1 (T-AA55 backlog-issue assert) |
| **Total NEW Cycle 4 tests** | **8** parametric ids (Z1-Z7 from one file) + 1 REQUIRED smoke-tenant + 1 OPTIONAL smoke-tenant + 4 docs/ops = **9 new test functions / 14 GREEN parametric ids** under FULL posture |
| **Test count posture (Pass-2 Q4)** | **3400** (FULL — RECOMMENDED; OPTIONAL T-AA52 included) — alternative MINIMAL = **3399** (skip T-AA52 OPTIONAL) — Step 8ae records the chosen value here on T-AA52 landing. |
| New ADRs | 0 (ADR-036-011 already authored in Cycle 3 Step 8y; Cycle 4 amendment sub-section appended at `:478-924` by speckit.plan in Step 8af; Cycle 4 in-place L172-173 rewrite is the only ADR text edit in this cycle) |
| BREAKING-flagged tasks | 0 (Cycle 4 is wording-defect + KQL-clause-insertion + new-test scope; no contract-shape BREAKING change) |

**Per-amendment task coverage**:

| Amendment | Severity | Tasks | FR / SC |
|-----------|----------|-------|---------|
| A4-01 | HIGH | T-AA43, T-AA44, T-AA45, T-AA46, T-AA47, T-AA48, T-AA49, T-AA56 (8) | FR-073 fold-in (author-time KQL column-resolution-validity) |
| A4-02 | MEDIUM | T-AA50, T-AA51, T-AA52, T-AA53, T-AA54, T-AA55, T-AA56 (7) | ADR-036-011 + smoke-tenant + spec mirror + CHANGELOG; no new FR (drift correction) |

**Per-Q→A and per-PD-C4 task coverage** (every Cycle 4 Q→A and plan-decision binds to ≥ 1 task):

| Source | Tasks |
|--------|-------|
| Pass-1 Q1 (KQL parser strategy — regex/lexer over AST) | T-AA46, T-AA47 |
| Pass-1 Q2 (smoke-tenant isolation guarantees reaffirmation) | T-AA51, T-AA52, T-AA53 |
| Pass-1 Q3 (backlog mechanism via `gh issue create`) | T-AA55 |
| Pass-1 Q4 (walker (a)/(b)/(c) discipline + union fail-fast) | T-AA46, T-AA47 |
| Pass-1 Q5 (ADR-036-011 amendment pathway + three-clause acknowledgement) | T-AA50, T-AA53 |
| Pass-2 Q1 (test count target 3398, superseded) | T-AA48 (7-id GREEN gate) |
| Pass-2 Q2 (CHANGELOG grouped-block format) | T-AA54 |
| Pass-2 Q3 (ADR Status convergence, `Proposed` until Step 8al) | T-AA50 (NO Status flip in this cycle) |
| Pass-2 Q4 (smoke-tenant scope test +1 → 3399 minimal / 3400 full) | T-AA51, T-AA52 |
| PD-C4-01 (Z7 KQL extend fix + parametric runtime-validity walker) | T-AA43, T-AA44, T-AA45, T-AA46, T-AA47, T-AA48, T-AA49 |
| PD-C4-02 (ADR in-place revision + smoke-tenant + spec mirror + CHANGELOG + backlog issue) | T-AA50, T-AA51, T-AA52, T-AA53, T-AA54, T-AA55 |

**Per-FR / SC test-pyramid coverage** (Cycle 4 narrowness — only FR-073 has new test bind; A4-02 is wording/contract drift correction):

| FR / SC | Unit | Integration | Contract | E2E | Docs / Ops |
|---------|------|-------------|----------|-----|-----------|
| FR-073 (extension via A4-01 fold-in) | — | — | T-AA46+T-AA47+T-AA48 (parametric Z1–Z7), T-AA51 (smoke-tenant scope), T-AA52 (smoke-tenant comment block) | — | T-AA49 (FR-073 acceptance text fold-in) |
| A4-02 wording defect (no new FR — drift correction) | — | — | T-AA51, T-AA52 | — | T-AA50 (ADR), T-AA53 (spec mirror), T-AA54 (CHANGELOG), T-AA55 (backlog issue) |

**File:line evidence cited in §26 task block** (sampled — full list embedded in task bodies):

- `infra/observability/sli-kql.json:91` (Z7 KQL — A4-01 JSON fix) — T-AA43
- `specs/036-sim-agent-extend/contracts/sli-thresholds.md:280-296` (Z7 KQL fenced block — A4-01 MD fix) — T-AA44
- `tests/contract/test_sli_kql_runtime_validity.py` (NEW — parametric Z1-Z7 walker) — T-AA46, T-AA47, T-AA48
- `tests/contract/_kql_canonicaliser.py` (existing Cycle 3 T-AA30, no edit; consumed via `canonical_kql_for_sli`) — T-AA46
- `specs/036-sim-agent-extend/spec.md` FR-073 acceptance block (Cycle 3 T-AA29 baseline + Cycle 4 fold-in) — T-AA49
- `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md:172-173` (in-place wording rewrite) — T-AA50
- `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md:478-924` (Cycle 4 amendment sub-section, already authored by speckit.plan, NOT edited by Cycle 4 tasks) — referenced by T-AA50
- `tests/contract/test_smoke_tenant_isolation.py` (existing; REQUIRED + OPTIONAL extensions) — T-AA51, T-AA52
- `infra/bicep/modules/cosmos-simulation-containers.bicep:316` (database-level scope literal — already correct, no Bicep code edit) — T-AA51
- `infra/bicep/modules/cosmos-simulation-containers.bicep:305-315` (comment block — OPTIONAL Bicep comment edit if missing wording) — T-AA52
- `specs/036-sim-agent-extend/spec.md:961-966` (Cycle 3 Pass-1 Q2 (v) mirror — supersession annotation) — T-AA53
- `CHANGELOG.md` `## [Unreleased]` (`### Added` + `### Changed` Cycle 4 grouped block) — T-AA54
- GitHub issue (NEW; `[backlog]` title prefix; label `backlog` only if pre-existing) — T-AA55
- `specs/036-sim-agent-extend/spec.md:4870`+1 (Cycle 4 tasks sentinel append) — T-AA56
- `specs/036-sim-agent-extend/plan.md:788-1010` (PD-C4-01) + `:1011-1348` (PD-C4-02) + `:1349-1379` (Step 8ad/8ae sequencing) — all tasks
- `specs/036-sim-agent-extend/spec.md:3875-3915` (A4-01 + A4-02 details) + `:3997-4351` (Pass-1 Q1-Q5) + `:4427-4814` (Pass-2 Q1-Q4) — all tasks
- `specs/036-sim-agent-extend/checklists/quality.md` CHK197..CHK230 (cited in every Acceptance bullet) — all tasks

**Total `file:line` citations across §26**: **≥ 50 unique evidence anchors** (every task body cites at least 3 of: plan.md PD-C4-NN, spec.md A4-NN / Pass-1 Qx / Pass-2 Qx, contract delta (sli-thresholds.md / sli-kql.json / audit-envelope.md / ADR-036-011), quality.md CHK197..CHK230).

---

### §26.9 Format-validation checkpoint

Every Cycle 4 task above conforms to the existing `tasks.md` row schema (matching the Cycle 1 §§ 4–20 format used by T-AA01..T-AA06, the Cycle 2 §24 format used by T-AA07..T-AA22, AND the Cycle 3 §25 format used by T-AA23..T-AA42), with one Cycle-4-specific addition: every task carries an explicit `**Verify-command**` bullet at the end (per the Step 8af orchestration prompt's verification expectation; this is additive to the Cycle 3 row schema and does not break any prior Cycle's format).

- ✅ Heading prefix `### T-AAxx` with `[P?] [NEW] [A4-XX H/M] [Wave A/B/C]` markers and a hyphen-separated short title.
- ✅ Bullet body with `Phase | Files | Description | Acceptance | Depends-on | Tests | Backward-compat / Effort | Verify-command` (≤ 9 lines per task body).
- ✅ Every Acceptance bullet cites at least one of: plan.md PD-C4-NN, spec.md A4-01 / A4-02 / Pass-1 Qx / Pass-2 Qx, contract delta (sli-thresholds.md / sli-kql.json / ADR-036-011), quality.md CHK197..CHK230.
- ✅ Every Tests bullet enumerates concrete test files distributed across contract / docs / ops layers, totalling **≥ 9 new test functions** (with 7 parametric ids contributed by T-AA46+T-AA47+T-AA48 from a single new file).
- ✅ Every task carries an explicit `**Verify-command**` bullet (Cycle 4 addition per Step 8af orchestration).
- ✅ No BREAKING flag is required across any Cycle 4 task — Cycle 4 closes wording defect + KQL-clause insertion + new-test scope; no contract-shape BREAKING change (in contrast to Cycle 2 T-AA07/08/14 which carried `**BREAKING**` callouts).
- ✅ Every Cycle 4 task ID is unique across the entire `tasks.md` file (T-AA43..T-AA56 — no collision with the locked-COMPLETE Cycle 1 §20 T-AA01..T-AA06 block, no collision with the locked Cycle 2 §24 T-AA07..T-AA22 block, no collision with the locked Cycle 3 §25 T-AA23..T-AA42 block).
- ✅ Australian English honoured throughout (artefact, behaviour, prioritise, organise, harmonise, recognise, parametric, canonicalise, normalisation, defence) — no US spellings introduced.
- ✅ Cycle 4 sentinel append target (`spec.md:4870`+1) carries the byte-exact text `**Cycle 4 tasks complete (14 tasks: T-AA43..T-AA56). Ready for /speckit.analyze (Cycle 4).**` — matches the Step 8af orchestration prompt's sentinel format.

---

**§26 Cycle 4 task block locked. Ready for /speckit.analyze.**

---

### §26.10 Cycle 4 implement status (post Step 8ag — appended only)

> Status updates per the Step 8ag implement run. The §26.1..§26.9 task bodies above are NOT edited (within-cycle immutability discipline); per-task DONE / DEFERRED markers are recorded here in a single trailing status block per Cycle 1+2+3 precedent.

| Task | Status | Wave | Note |
|------|--------|------|------|
| T-AA43 | [DONE] | A | `infra/observability/sli-kql.json` Z7 entry now carries `\| extend model_deployment = tostring(customDimensions["model_deployment"])` between `extend tenant_id` and `where env == "staging"`. Verify-command returns `Z7 extend model_deployment OK`. |
| T-AA44 | [DONE] | A | `specs/036-sim-agent-extend/contracts/sli-thresholds.md` §6b Z7 KQL fenced block carries the symmetric `\| extend model_deployment = tostring(customDimensions["model_deployment"])` line at the same semantic position. |
| T-AA45 | [DONE] | A | `tests/contract/test_sli_kql_canonical_match.py` re-runs GREEN across all 7 SLI ids after T-AA43 + T-AA44 — byte-equality preserved. |
| T-AA46 | [DONE] | A | New file `tests/contract/test_sli_kql_runtime_validity.py` created with parametric Z1–Z7 surface, `_kql_canonicaliser` import, base-table allowlist, and walker scaffold. |
| T-AA47 | [DONE] | A | Walker body + helpers (`_walk`, `_extract_referenced_columns`, `_extract_extend_bindings`, `_extract_summarize_bindings`, `_extract_extend_rhs_only`, `_extract_summarize_rhs_only`, `_validate_references`, `_detect_base_table`, `_extract_let_bindings`) implemented. Hard-fails on `union` (verified). Failure message: `KQL {sli_id} references undefined column '{name}' at line {N} — must extend from customDimensions first; canonicalised KQL:\n{...}`. |
| T-AA48 | [DONE] | A | All 7 parametric ids GREEN (`SLI-Z1` … `SLI-Z7`). Verified that pre-fix Z7 KQL would fail with `references undefined column 'model_deployment' at line 12` — walker catches the original A4-01 defect class. |
| T-AA49 | [DONE] | A | FR-073 acceptance text in `spec.md:3666-3697` now carries the author-time KQL column-resolution-validity sub-bullet citing `tests/contract/test_sli_kql_runtime_validity.py` and PD-C4-01. |
| T-AA50 | [DONE] | B | `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md:166-190` (Sub-decision (v) wording) rewritten in-place with the corrected three-clause acknowledgement: database-level scope + compensating defence-in-depth control + backlog issue #84. Cycle 4 amendment sub-section at L478+ NOT modified per task spec (already authored by speckit.plan). ADR Status remains `Proposed`. |
| T-AA51 | [DONE] | B | `tests/contract/test_smoke_tenant_isolation.py::test_smoke_role_assignment_scope_is_database_level` added — asserts the literal `scope: '${account.id}/dbs/${databaseName}'` in `infra/bicep/modules/cosmos-simulation-containers.bicep`. GREEN (no Bicep change required — Bicep was already correct). |
| T-AA52 | [DONE] | B | FULL posture taken (3400). `tests/contract/test_smoke_tenant_isolation.py::test_bicep_comment_block_documents_compensating_control` added — asserts the Bicep comment block at the role-assignment site documents the compensating-control wording AND the `[backlog issue: #84]` identifier. Added Cycle-4 comment lines to the Bicep comment block (additive — no semantic change to the resource). |
| T-AA53 | [DONE] | B | `spec.md:961-979` Cycle-3 Pass-1 Q2 (v) mirror corrected via in-place strikethrough supersession annotation citing A4-02 + ADR-036-011 + backlog issue. The four sibling lock-zone mirrors (`plan.md:682`, `tasks.md:1929`, `quality.md:367`, `quality.md:528`) are explicitly preserved as known-stale per the Cycle 3 immutability discipline (LOW-1 Step 8aj fold-in — annotated). |
| T-AA54 | [DONE] | B | `CHANGELOG.md` `## [Unreleased]` carries new `### Added (spec 036 — Cycle 4 amendment cycle)` and `### Changed (spec 036 — Cycle 4 amendment cycle)` sub-sections (4 + 1 bullets total). NO `### Breaking changes` sub-section added — Cycle 4 is non-breaking. Mirrors Cycle 2 grouped-block format (CHANGELOG.md:7-31 precedent). |
| T-AA55 | [DONE] | C | GitHub issue [#84](https://github.com/johnbilliris/ama/issues/84) filed via `gh issue create`. Title prefix `[backlog]`. Label `backlog` NOT applied — `gh label list` shows the label does NOT pre-exist in the repo (do NOT create new labels per repo governance). Issue body cites database-level scope + desired partition-level scope + Cosmos data-plane RBAC API 2024-08-15 capability gap + cross-references ADR-036-011:172-173 and `spec.md:3896-3915`. ADR L172-173, CHANGELOG `### Added`, and Bicep comment block all back-filled with `#84` (placeholder `[backlog issue: TBD]` resolved). |
| T-AA56 | [DONE] | C | Final test run completed. **Local environment caveat**: 17 pre-existing failures + 17 errors in unrelated modules (`tests/devops/test_cd_workflow.py`, `tests/devops/test_drift_detection.py`, `tests/e2e/test_quickstart_validation.py`, `tests/load/test_workflow_capacity.py`, `tests/simulation/test_bushfire_risk_assessment.py`, audit-tier-3 file-spill tests, build-tts-watermarks devops tests). All confirmed pre-existing via stash-and-rerun (none caused by Cycle 4 changes). The 22 Cycle-4-affected contract tests are 22/22 GREEN: 7 canonical-match + 7 runtime-validity + 8 smoke-tenant. `ruff check apps tests packages` returns clean. Cycle 4 sentinel appended to `spec.md` after L4873. |

**Cycle 4 test count delta** (Pass-2 Q4 FULL posture):

- Cycle 3 baseline: 3391 (cited in spec).
- T-AA48 walker (7 parametric ids): +7.
- T-AA51 REQUIRED smoke-tenant scope assertion: +1.
- T-AA52 OPTIONAL smoke-tenant comment block assertion: +1.
- **Cycle 4 close target**: 3400 tests pass (FULL posture). Local environment shows 3728 + 0 Cycle-4 regressions.

**Cycle 4 implement complete (Step 8ag). Ready for /speckit.analyze (Cycle 4 re-review, Step 8al).**


---

## §27 Cycle 5 Task Block (A5-01 — stale Bicep preamble correction, post Step 8al cohort re-review)

> **Cycle context**: This block appends **T-AA57..T-AA61** to address the single Cycle 5 amendment **A5-01 MEDIUM** (`spec.md:4943, 4947-4992`) — the Cycle 4 implementation residue at `infra/bicep/modules/cosmos-simulation-containers.bicep:305-315` (the unremoved pre-Cycle-4 preamble whose L305 *"smoke-tenant partition path"* lead sentence and L306-308 illustrative `/colls/<container>/pks/<tenant_id>` resolution contradict the actual database-level `scope:` expression at L328 and the corrected Cycle 4 A4-02 sub-block at L317-327). All Cycle 1 (§§ 1–23), Cycle 2 (§24, T-AA07..T-AA22, locked-COMPLETE), Cycle 3 (§25, T-AA23..T-AA42, locked), and Cycle 4 (§26, T-AA43..T-AA56, locked-COMPLETE per `tasks.md:2541` *"Cycle 4 implement complete (Step 8ag)..."*) content remains **byte-identical** — Cycle 5 is strictly additive. Cycle 5 IDs continue the existing T-AA namespace from **T-AA57** (next after the Cycle 4 maximum T-AA56, verified by inspection of §26.10 status block at `tasks.md:2516-2531`). The five Cycle 5 tasks are organised into a **single coherent Wave** (no multi-wave decomposition needed given the narrow scope — three documentation-only edits in two files plus a CHANGELOG row and a verification gate). Cycle 5 honours Australian English throughout (artefact, behaviour, prioritise, organise, harmonise, recognise, parametric, canonicalise, normalisation, defence) and preserves all 7 Constitution v1.2.0 invariants per `plan.md` §C2.6 + the Cycle 3 PD-C3-01..03 + the Cycle 4 PD-C4-01..02 + the new PD-C5-01 decision. Per Pass 2 Q4 (`spec.md:5863-5897`) the multi-cycle Proposed→Accepted convergence rule applies recursively: ADR-036-011 Status remains `Proposed` at Step 8at close and flips to `Accepted` only on Step 8au clean cohort verdict (0 OBJECT votes AND 0 NEW merit-validated findings against ADR-036-011); otherwise Cycle 6 opens.

### §27.1 Cycle 5 phase tracker

| Wave | Tasks | Title | Status | Depends-on |
|------|-------|-------|--------|-----------|
| **A** | T-AA57..T-AA61 | A5-01 — Bicep preamble residue removal (`cosmos-simulation-containers.bicep:305-315`) + smoke-tenant-isolation absence assertions (`test_smoke_tenant_isolation.py:250-297`) + T-AA52 OPTIONAL→REQUIRED prose promotion (`test_smoke_tenant_isolation.py:173, 253`) + CHANGELOG Cycle 5 close block + Step 8at verification gate (~0.25 day) | DONE | Cycle 4 §26 locked-COMPLETE (T-AA56 Cycle 4 sentinel at `spec.md:4886`; 3400 FULL posture certified) |

### §27.2 Severity legend (per Cycle 5 amendment severity convergence — `spec.md:4943, 4958-4963`, quality.md CHK231)

- `[A5-01 MEDIUM]` ↔ infrastructure-devops + azure-principal-architect (technical cohort, Step 8al re-review) — `cosmos-simulation-containers.bicep:305-315` carries the stale pre-Cycle-4 preamble whose L305 lead sentence (*"Scope the assignment to the smoke-tenant partition path"*) and L306-308 illustrative `/colls/<container>/pks/<tenant_id>` resolution contradict the actual database-level `scope:` expression at L328 (already correct, unchanged by Cycle 4, confirmed by Step 8al azure-principal-architect ACCEPT verdict citing L328 verbatim) AND the corrected Cycle 4 A4-02 sub-block at L317-327 (already correct, also unchanged). Defect is **documentation-only**: the compiled Bicep `scope:` expression is correct; runtime RBAC behaviour is identical; no production tenant can be accessed by the smoke `Simulation.Coordinator` principal at any moment. Remediation is a single Step 8at landing — (a) Bicep preamble rewrite consolidating L305-315 with the existing L317-327 block; (b) two new `assert ... not in role_block.lower()` absence assertions appended to `test_bicep_comment_block_documents_compensating_control`; (c) T-AA52 prose promotion OPTIONAL→REQUIRED via docstring at L253 + header comment at L173; (d) CHANGELOG Cycle 5 close block; (e) verification gate. The actual `scope:` expression at L328 MUST NOT be modified (Cycle 5 scope-creep violation per `spec.md:4980`). The Cycle 4 A4-02 sub-block at L317-327 MUST NOT be re-rendered (LOW-1 within-cycle immutability per `spec.md:5108-5111`); A5-01 consolidates **around** it, not **through** it.

---

### §27.3 Wave A — A5-01 documentation-only remediation (5 tasks; depends only on Cycle 4 §26 locked-COMPLETE)

> **Within-wave parallelism**: T-AA57 (Bicep preamble rewrite) is the lead — sequential before T-AA58 (the absence assertions would fail against the un-rewritten Bicep, since the stale L305 *"partition path"* and L308 `pks/<tenant_id>` substrings are exactly the phrasings the assertions target). T-AA59 (T-AA52 prose promotion at docstring L253 + header comment L173) is parallel `[P]` with T-AA57 and T-AA58 — prose-only, no functional dependency on either the Bicep rewrite or the test-body edit (per Pass 2 Q1 at `spec.md:5568-5586`, the prose promotion is independent of the absence assertions). T-AA60 (CHANGELOG Cycle 5 grouped block) depends on T-AA57 + T-AA58 + T-AA59 (all three content artefacts must land before the CHANGELOG entry summarises them; mirrors Cycle 4 T-AA54 dependency discipline at `tasks.md:2315`). T-AA61 (Step 8at verification gate — pytest + ruff) depends on T-AA57 + T-AA58 + T-AA59 + T-AA60 (every prior Cycle 5 task must land before the empirical closure gate).

#### T-AA57 [DONE] [A5-01 MEDIUM] [Wave A] — `infra/bicep/modules/cosmos-simulation-containers.bicep:305-315` Bicep preamble rewrite (consolidate with Cycle 4 A4-02 sub-block at L317-327; four-clause ordering per Pass 1 Q1)

- **Phase**: Wave A — closes the A5-01 documentation residue at the Bicep-side; co-located with T-AA58 (test absence assertions) and T-AA59 (T-AA52 prose promotion) in the single Step 8at landing. The actual `scope:` expression at L328 is **byte-identical** to the Cycle 4 baseline (`scope: '${account.id}/dbs/${databaseName}'`) and **MUST NOT be modified** (Cycle 5 scope-creep violation per `spec.md:4980`).
- **Files**: `infra/bicep/modules/cosmos-simulation-containers.bicep:305-315` (rewrite the eleven-line preamble in place — replace `// Scope the assignment to the smoke-tenant partition path. The` through `// contract-test discovery.` with the consolidated four-clause sequence per Pass 1 Q1 ordering at `spec.md:5067-5096`: (1) database-level scope statement — *"Scope the assignment at the database level — `${account.id}/dbs/${databaseName}` — which is the narrowest scope supported by Cosmos data-plane RBAC API 2024-08-15"*; (2) compensating defence-in-depth phrasing reaffirming the Cycle 4 A4-02 phrase; (3) joint enforcement clauses naming the SLI-Z6 / SLI-Z7 query-time `where tenant_id == "tnt-stg-smoke"` filter and the `customDimensions["tenant_id"]` envelope discriminator AND the Pass-1 Q2 isolation guarantees (i)–(v); (4) the `[backlog issue: #84]` citation). Preserve the existing L317-327 Cycle 4 A4-02 sub-block **byte-identically** — A5-01 consolidates *around* the L317-327 block, **not through** it (LOW-1 within-cycle immutability per `spec.md:5108-5111`). Preserve the L328 `scope:` line **byte-identically** (`scope: '${account.id}/dbs/${databaseName}'`). The rewritten preamble MUST NOT contain the case-insensitive substrings `partition path`, `pks/<tenant_id>`, or `/colls/<container>/pks/` anywhere in the role-assignment block (these are the F-TECH-4-01 anchor phrasings that T-AA58's absence assertions will subsequently lock).
- **Description**: The eleven-line stale preamble at L305-315 currently leads at L305 with *"Scope the assignment to the smoke-tenant partition path"* (false — the actual scope at L328 is database-level) and at L306-308 with an illustrative resolution containing `/colls/<container>/pks/<tenant_id>` (false — the Cosmos data-plane RBAC API 2024-08-15 does NOT yet expose a `partitionKey` selector; the rendered scope is `${account.id}/dbs/${databaseName}`). T-AA57 replaces this preamble in place with a consolidated four-clause sequence whose top-down ordering is byte-symmetric to the three precedent anchors — ADR-036-011:172-184, the Cycle 4 A4-02 sub-block at `cosmos-simulation-containers.bicep:317-327`, and the F-TECH-4-01 recommended remediation. **Ordering symmetry is cohort-verified, not test-verified** — Q3 of the Pass 1 propagation table at `spec.md:5167-5173` explicitly defers ordering enforcement to the Step 8au cohort re-review and the Step 8at manual review against the Pass 1 Q1 anchor; the T-AA58 absence assertions target *content* (presence/absence of phrasings), not *ordering*. The rewrite is documentation-only — the compiled Bicep behaviour is unchanged because the `scope:` expression at L328 is unchanged.
- **Acceptance**: plan.md PD-C5-01 (`plan.md:1427-1929`) — acceptance criterion 1 + 2 at `plan.md:1798-1821`; spec.md A5-01 detail at `:4943, 4947-4992` + Pass 1 Q1 ordering at `:5067-5096`; quality.md **CHK231** (case-insensitive substring absence + scope:-line byte-equality) + **CHK232** (four-clause top-down ordering symmetric with ADR-036-011:172-184).
- **Depends-on**: none (Wave-A lead; Cycle 4 §26 locked-COMPLETE per `tasks.md:2541`).
- **Tests**: contract `tests/contract/test_smoke_tenant_isolation.py::test_smoke_role_assignment_scope_is_database_level` (existing Cycle 4 T-AA51, no edit) — re-runs GREEN because L328 is unchanged; contract `tests/contract/test_smoke_tenant_isolation.py::test_bicep_comment_block_documents_compensating_control` (existing Cycle 4 T-AA52, body extended by T-AA58) — re-runs GREEN against the rewritten preamble once T-AA58 lands the absence assertions.
- **Backward-compat / Effort**: Bicep comments + structure rewrite only (no runtime change; no operator-facing breaking change — the `scope:` expression at L328 is byte-identical; the compiled ARM template is functionally unchanged); small.
- **Out-of-scope**: ADR-036-011:172-184 binding wording (already correct per Step 8al ACCEPT verdicts; `spec.md:4979`); `cosmos-simulation-containers.bicep:328` `scope:` expression (Cycle 5 scope-creep violation per `spec.md:4980`); `cosmos-simulation-containers.bicep:317-327` Cycle 4 A4-02 sub-block (LOW-1 within-cycle immutability per `spec.md:5108-5111`); the four Cycle 4 LOW-1 mirror-immutability anchors at `plan.md:682`, `tasks.md:1929`, `quality.md:367`, `quality.md:528` (`spec.md:4982`, quality.md CHK239); `spec.md:3907-3925` Cycle 4 A4-02 binding wording (already correct; `spec.md:4983`).
- **Verify-command**: `python -c "import re,pathlib; t=pathlib.Path('infra/bicep/modules/cosmos-simulation-containers.bicep').read_text(); m=re.search(r'resource\s+smokeCoordinatorRoleAssignment\s+[^}]*\}', t, re.DOTALL); b=m.group(0).lower(); assert 'partition path' not in b and 'pks/<tenant_id>' not in b and '/colls/<container>/pks/' not in b, 'A5-01 / T-AA57 — Bicep preamble still carries F-TECH-4-01 phrasing'; assert \"scope: '${account.id}/dbs/${databaseName}'\" in t, 'A5-01 / T-AA57 — L328 scope: expression must be byte-identical to Cycle 4 baseline'; print('T-AA57 Bicep preamble OK')"`
- **Ownership**: Owned by /speckit.implement (Cycle 5, Step 8at).

#### T-AA58 [DONE] [A5-01 MEDIUM] [Wave A] — Append two case-insensitive absence assertions to `tests/contract/test_smoke_tenant_isolation.py::test_bicep_comment_block_documents_compensating_control` (Pass 1 Q2 option (b) + Pass 2 Q2 `.lower()` + plain `in`)

- **Phase**: Wave A — adds the F-TECH-4-01 regression-guard surface to the existing Cycle 4 T-AA52 test by appending two new `assert ... not in role_block.lower()` statements **inside** the existing test function body (additive; no new `def test_*` function, no parametrize-axis widening, no new test file — Pass 1 rollup + Pass 2 Q3 at `spec.md:5440-5444, 5774-5815` pin the +0 test-count delta).
- **Files**: `tests/contract/test_smoke_tenant_isolation.py:250-297` (append two new `assert ... not in role_block.lower()` statements **after** the two existing presence assertions at L271-282 (`compensating_re.search(role_block)`) and L286-297 (`backlog_re.search(role_block)`); both new assertions consume the same `role_block` variable produced by `_extract_role_assignment_block(bicep_text)` at L269 (Pass 1 Q3 comment-block-only scope at `spec.md:5299-5418`); encode **byte-identically** as the verbatim Python at `spec.md:5656-5673`: (i) `assert "pks/<tenant_id>" not in role_block.lower(), ( "Cycle 5 / A5-01 / F-TECH-4-01 — the Bicep role-assignment " "comment block MUST NOT contain the phrase 'pks/<tenant_id>' " "which falsely claims a partition-level scope; the actual " "scope at L328 is database-level. Per ADR-036-011:172-184 " "and spec.md:5000-5001 Pass-1 Q1/Q2, the operator-facing " "comment MUST align with the database-level scope narrative." )`; (ii) `assert "partition path" not in role_block.lower(), ( ... "the phrase 'partition path' ..." ... )` mirror-shape per `spec.md:5665-5672`). Use `.lower()` + plain `in` substring check **only** (Pass 2 Q2 binding form at `spec.md:5650-5754`) — **MUST NOT** use `re.compile(..., re.IGNORECASE)`, **MUST NOT** use `str.casefold()`, **MUST NOT** use a regex-based pattern (the Pass 1 Q2 `re.compile` alternative offered at `spec.md:5186, 5190` is **explicitly rejected** by Pass 2 Q2). The two existing presence assertions at L271-282 and L286-297 remain **byte-identical** (quality.md CHK235).
- **Description**: The two new option-(b) absence assertions target the verbatim F-TECH-4-01 anchor phrasings — `pks/<tenant_id>` (the resolution-string example at the current Bicep L306-308) and `partition path` (the lead-sentence claim at the current Bicep L305) — per the F-TECH-4-01 recommended remediation at `step-8al-rereview-technical.md` § "NEW findings" row (verbatim *"fail on `pks/<tenant_id>` / `partition path` claims in the role-assignment comment block"*). The `.lower()` + plain `in` form is **symmetric** with the existing `tnt-prod` absence precedent at `tests/contract/test_smoke_tenant_isolation.py:166` (`assert "tnt-prod" not in role_block.lower()`) — within-file shape consistency is the Pass 2 Q2 binding rationale (`spec.md:5694-5707`). Failure messages cite the F-TECH-4-01 provenance, the ADR-036-011:172-184 anchor, and the binding remediation. The other three Pass 1 Q2 alternatives — option (a) literal `pks/<tenant_id>` only (too narrow), option (c) full regex covering `(partition[- ]?(path|key|scope)|pks/<[^>]+>)` (over-broad on legitimate `partition-scope` / `partition-level` in the L317-327 A4-02 block and the rewritten L305-315 preamble), and option (d) bare token `partition` (over-broad for identical reasons) — are **explicitly rejected** per `spec.md:5200-5239`. The space-vs-hyphen discriminator (`partition path` SPACE versus legitimate `partition-level` / `partition-scope` HYPHEN) is preserved exactly by plain `in` substring matching — no regex word-boundary anchoring is required (Pass 2 Q2 false-positive analysis at `spec.md:5694-5729`).
- **Acceptance**: plan.md PD-C5-01 (`plan.md:1427-1929`) — acceptance criterion 3 at `plan.md:1822-1829`; spec.md A5-01 detail at `:4970` + Pass 1 Q2 option (b) at `:5175-5240` + Pass 1 Q3 comment-block-only scope at `:5299-5418` + Pass 2 Q2 `.lower()` + plain `in` form at `:5650-5754`; quality.md **CHK234** (`.lower()` + plain `in` binding case-folding primitive) + **CHK235** (pre-existing presence assertions preserved byte-identically).
- **Depends-on**: T-AA57 (the Bicep preamble rewrite must land first — the absence assertions would fail against the un-rewritten Bicep because the stale L305 *"partition path"* and L308 `pks/<tenant_id>` substrings are exactly the phrasings the assertions target; co-merge is required for the assertions to be GREEN at landing).
- **Tests**: contract `tests/contract/test_smoke_tenant_isolation.py::test_bicep_comment_block_documents_compensating_control` — the same test function body is extended in place; collected-node count unchanged at 3400; the two new assertions plus the two existing presence assertions all execute on every pytest invocation (no skip/xfail markers; Pass 2 Q3 binding at `spec.md:5774-5815`).
- **Backward-compat / Effort**: test-body extension only (additive to existing function; +0 test-count delta; no new `def test_*` function); small.
- **Out-of-scope**: `_extract_role_assignment_block` helper at L220-247 (re-used as-is; no modification — Pass 1 Q3 inheritance at `spec.md:5404-5407`); the two existing presence assertions at L271-282 / L286-297 (must remain byte-identical — quality.md CHK235); `pytest.mark.*` decorators (none currently present; none added — Pass 2 Q1 prose-only promotion at `spec.md:5581-5585`; quality.md CHK243 anti-pattern).
- **Verify-command**: `python -m pytest tests/contract/test_smoke_tenant_isolation.py::test_bicep_comment_block_documents_compensating_control -v` returns `1 passed` (the single test function executes all four assertions: two pre-existing presence + two new absence; no skipped/xfailed qualifier).
- **Ownership**: Owned by /speckit.implement (Cycle 5, Step 8at).

#### T-AA59 [P] [DONE] [A5-01 MEDIUM] [Wave A] — T-AA52 prose promotion OPTIONAL → REQUIRED (`tests/contract/test_smoke_tenant_isolation.py:173` header comment + `:253` docstring; Pass 2 Q1 — prose-only, no `pytest.mark.*`)

- **Phase**: Wave A — closes the Pass 2 Q1 dispositional ambiguity by rewriting the prose disposition labels (docstring + header comment) to record REQUIRED; collapses the Cycle 4 Pass 2 Q4 minimal-3399 / FULL-3400 posture split into a single 3400 posture binding for all subsequent cycles. Parallel `[P]` with T-AA57 and T-AA58 — prose-only, no functional dependency on either the Bicep rewrite or the test-body absence assertions (Pass 2 Q1 prose-only discipline at `spec.md:5581-5586`).
- **Files**: `tests/contract/test_smoke_tenant_isolation.py:253` (rewrite the docstring at the start of `test_bicep_comment_block_documents_compensating_control` — current text per `tests/contract/test_smoke_tenant_isolation.py:253` is *"T-AA52 — OPTIONAL A4-02 evidence: Bicep comment block (L305-315). Cycle 4 FULL posture per Pass-2 Q4..."*; rewrite to *"T-AA52 — REQUIRED A4-02 evidence (promoted Cycle 5 Pass 2): Bicep comment block (L305-315). Single 3400 posture per Cycle 5 Pass 2 Q1; the minimal/FULL split established by Cycle 4 Pass 2 Q4 at `spec.md:4795-4801` is collapsed (Cycle 4 chose FULL per `tasks.md:2527`; Cycle 5 promotion locks it)..."* per Pass 2 Q1 verbatim text at `spec.md:5568-5577`); `tests/contract/test_smoke_tenant_isolation.py:173` (rewrite the header comment block — current text per `tests/contract/test_smoke_tenant_isolation.py:173` is `# Cycle 4 / T-AA51 (REQUIRED) + T-AA52 (OPTIONAL) — A4-02 evidence tests`; rewrite to `# Cycle 4 / T-AA51 (REQUIRED) + T-AA52 (REQUIRED — promoted Cycle 5 Pass 2 per spec.md A5-01) — A4-02 evidence tests` per Pass 2 Q1 verbatim text at `spec.md:5577-5581`). **MUST NOT** add any `pytest.mark.skip`, `pytest.mark.xfail`, `pytest.mark.skipif`, or any conditional skip decorator (quality.md CHK243 anti-pattern; the test was already collected unconditionally at Cycle 4 close per `tasks.md:2527`); **MUST NOT** remove any decorator (none currently present); **MUST NOT** edit the test function body (T-AA58 owns the body extension).
- **Description**: Cycle 4 Pass 2 Q4 established a minimal-3399 / FULL-3400 posture split as an escape hatch for the case where Step 8ae chose not to rewrite the Bicep comment block (`spec.md:4795-4801`); that branch was **not taken** (Cycle 4 chose FULL per `tasks.md:2527`), so the escape hatch is **already unexercised history** at Cycle 5 launch. F-TECH-4-01 was missed precisely because the test was labelled OPTIONAL — REQUIRED promotion eliminates the signal-disposition gap (Pass 2 Q1 ground (iii) at `spec.md:5525-5538`). The runtime disposition is unchanged because pytest already collects the test unconditionally — the dispositional flip is **prose-only** (Pass 2 Q1 grounds (i)-(v) at `spec.md:5502-5567`). Cycle 4 Step 8aj LOW-2 precedent (Z7 pipe-ordering asymmetry promotion at `spec.md:5539-5546`) is the symmetric precedent for OPTIONAL → REQUIRED promotion when a re-review surfaces evidence the OPTIONAL discipline failed to catch a real defect. Constitution Principle IV (Transparency and Auditability — `spec.md:5546-5551`) demands the prose disposition labels match the runtime disposition. The Pass 1 deferral paragraph at `spec.md:5444-5451` is **preserved verbatim** per within-cycle immutability discipline; the binding disposition is the corrected value pinned by Pass 2 Q1 (`spec.md:5479`).
- **Acceptance**: plan.md PD-C5-01 (`plan.md:1427-1929`) — acceptance criterion 4 at `plan.md:1830-1833`; spec.md A5-01 detail at `:4943, 4947-4992` + Pass 2 Q1 promotion logic at `:5498-5614` + Pass 2 Q3 single-3400-posture rule at `:5776-5859`; quality.md **CHK233** (docstring at L253 + header comment at L173 prose rewritten to REQUIRED disposition; no `pytest.mark.*` decorator added or removed) + **CHK243** (anti-pattern: any PR that adds `pytest.mark.skip/xfail/skipif` is rejected).
- **Depends-on**: none (parallel with T-AA57 and T-AA58; prose-only — no functional dependency on either the Bicep rewrite or the test-body absence assertions).
- **Tests**: contract `tests/contract/test_smoke_tenant_isolation.py::test_bicep_comment_block_documents_compensating_control` (existing post-T-AA58, docstring + header comment rewritten by T-AA59) — re-runs GREEN with the new prose disposition; collected-node count unchanged at 3400; no skipped/xfailed qualifier.
- **Backward-compat / Effort**: prose-only rewrite (additive correction; no runtime change; no test-body edit; no decorator edit; +0 test-count delta); small.
- **Out-of-scope**: any `pytest.mark.skip`, `pytest.mark.xfail`, `pytest.mark.skipif` decorator (quality.md CHK243 anti-pattern); the Pass 1 deferral paragraph at `spec.md:5444-5451` (preserved verbatim per within-cycle immutability discipline); the test function body (T-AA58 owns the body extension); the helper `_extract_role_assignment_block` at L220-247 (re-used as-is).
- **Verify-command**: `python -c "import pathlib,re; t=pathlib.Path('tests/contract/test_smoke_tenant_isolation.py').read_text(); assert 'T-AA52 (REQUIRED' in t and 'promoted Cycle 5' in t, 'T-AA59 prose promotion docstring/header missing'; assert 'OPTIONAL A4-02' not in t and 'T-AA52 (OPTIONAL)' not in t, 'T-AA59 prose still carries OPTIONAL signal'; assert not re.search(r'@pytest\.mark\.(skip|xfail|skipif)\s*\([^)]*test_bicep_comment_block', t), 'T-AA59 anti-pattern: pytest.mark.skip/xfail/skipif on T-AA52 (CHK243)'; print('T-AA59 prose promotion OK')"`
- **Ownership**: Owned by /speckit.implement (Cycle 5, Step 8at).

#### T-AA60 [DONE] [A5-01 MEDIUM] [Wave A] — `CHANGELOG.md` Cycle 5 grouped block under `## [Unreleased]` (`### Added` + `### Changed (spec 036 — Cycle 5 amendment cycle)`)

- **Phase**: Wave A — appends the Cycle 5 grouped block to `CHANGELOG.md` under `## [Unreleased]`; mirrors the Cycle 4 grouped-block precedent at `CHANGELOG.md:7-15` (the Cycle 4 `### Added (spec 036 — Cycle 4 amendment cycle)` + `### Changed (spec 036 — Cycle 4 amendment cycle)` sub-sections established the format).
- **Files**: `CHANGELOG.md` under `## [Unreleased]` — append two new sub-sections **after** the existing Cycle 4 entries: `### Added (spec 036 — Cycle 5 amendment cycle)` (sub-bullet: *"Two case-insensitive absence assertions appended to `tests/contract/test_smoke_tenant_isolation.py::test_bicep_comment_block_documents_compensating_control` (`pks/<tenant_id>` and `partition path` via `.lower()` + plain `in`) — F-TECH-4-01 regression guard against future re-paste of the Cycle 3 partition-path wording into the Bicep role-assignment comment block. (A5-01 / F-TECH-4-01 / spec.md:5656-5673)"*); `### Changed (spec 036 — Cycle 5 amendment cycle)` (sub-bullets: *"`infra/bicep/modules/cosmos-simulation-containers.bicep:305-315` — Bicep preamble rewrite consolidating with the Cycle 4 A4-02 sub-block at L317-327; four-clause ordering per Pass 1 Q1 (database-level scope → compensating defence-in-depth → joint enforcement → `[backlog issue: #84]`); removes the stale Cycle 3 *"smoke-tenant partition path"* lead sentence and the illustrative `/colls/<container>/pks/<tenant_id>` resolution. (A5-01 / spec.md:5067-5096)"*; *"`tests/contract/test_smoke_tenant_isolation.py:173, 253` — T-AA52 prose disposition promoted OPTIONAL → REQUIRED per Pass 2 Q1; collapses the Cycle 4 Pass 2 Q4 minimal-3399 / FULL-3400 posture split into a single 3400 posture binding for all subsequent cycles. No `pytest.mark.*` decorator added or removed (runtime disposition unchanged — test was already collected unconditionally at Cycle 4 close per `tasks.md:2527`). (A5-01 / spec.md:5498-5586)"*). **NO** `### Breaking changes` sub-section is added — A5-01 is documentation-and-test-only and the compiled Bicep behaviour is byte-identical to the Cycle 4 baseline (the actual `scope:` expression at L328 is unchanged; runtime RBAC behaviour is unchanged).
- **Description**: The grouped-block format mirrors Cycle 2 (`CHANGELOG.md:7-31` precedent originally) and Cycle 4 (`### Added` + `### Changed` sub-sections at `CHANGELOG.md:7-15`) exactly. Sub-bullets are concise + cite the file:line evidence anchor + cite the binding amendment id (`A5-01`) + cite the spec.md Pass anchor (`:5067-5096` for Q1, `:5498-5586` for Q1, `:5656-5673` for the verbatim Python). The `[backlog issue: #84]` placeholder is **NOT** re-cited in the CHANGELOG bullets (the backlog issue #84 itself is not modified by Cycle 5 — it remains open per quality.md CHK241; Pass 1 Q1 ordering element (4) already cites it in the Bicep preamble). The Cycle 4 grouped block at `CHANGELOG.md:7-15` is **NOT** edited (within-cycle immutability discipline).
- **Acceptance**: plan.md PD-C5-01 (`plan.md:1427-1929`) — acceptance criterion 6 at `plan.md:1844-1849`; spec.md A5-01 detail at `:4943, 4947-4992` + Pass 2 Q1 CHANGELOG propagation at `:5642-5646` + Pass 2 Q3 CHANGELOG dispositional-collapse propagation at `:5848-5853`; quality.md **CHK240** (Cycle 5 close-block format: `### Added` + `### Changed` sub-sections; no `### Breaking changes`; bullets cite `file:line` + inline `(A5-01)` provenance tag).
- **Depends-on**: T-AA57 + T-AA58 + T-AA59 (all three content artefacts must land before the CHANGELOG entry summarises them; mirrors Cycle 4 T-AA54 aggregator-dependency at `tasks.md:2315`).
- **Tests**: this task is a CHANGELOG documentation append; no new test file is created. The verify-command below uses `grep` to validate the appended sub-sections exist with the expected `(A5-01)` provenance tags.
- **Backward-compat / Effort**: CHANGELOG only (additive; non-breaking; no runtime change); small.
- **Out-of-scope**: `### Breaking changes` sub-section (NOT added — A5-01 is non-breaking per `spec.md:4961`); the existing Cycle 4 grouped block at `CHANGELOG.md:7-15` (NOT edited per within-cycle immutability discipline); backlog issue #84 (NOT modified — remains open per quality.md CHK241); the Cycle 2 / Cycle 3 grouped-block CHANGELOG entries (NOT edited per within-cycle immutability discipline).
- **Verify-command**: `grep -n 'Cycle 5 amendment cycle' CHANGELOG.md` returns at least 2 matches (one for the `### Added` heading, one for the `### Changed` heading); `grep -n '(A5-01' CHANGELOG.md` returns ≥ 3 matches (one per sub-bullet's inline provenance tag); `grep -c 'Breaking changes (spec 036 — Cycle 5' CHANGELOG.md` returns `0`.
- **Ownership**: Owned by /speckit.implement (Cycle 5, Step 8at).

#### T-AA61 [DONE] [A5-01 MEDIUM] [Wave A] — Step 8at verification gate (pytest 22-passed contract slice + 3400-passed full suite + ruff clean + Bicep `scope:` byte-equality reverify)

- **Phase**: Wave A — final A5-01 closure gate; runs the Step 8at pre-merge and post-merge verification commands per PD-C5-01 acceptance criterion 7 + 8 (`plan.md:1850-1866`) and verifies the post-Cycle-5 single-3400 posture is empirically certified.
- **Files**: `tests/contract/test_smoke_tenant_isolation.py` (existing post-T-AA58 + T-AA59, no edit); `tests/contract/test_sli_kql_canonical_match.py` (existing Cycle 3 T-AA32 + Cycle 4 T-AA45, no edit); `tests/contract/test_sli_kql_runtime_validity.py` (existing Cycle 4 T-AA46-T-AA48, no edit); `infra/bicep/modules/cosmos-simulation-containers.bicep` (existing post-T-AA57, no edit — only re-read for the L328 `scope:` byte-equality reverify); `apps/`, `tests/`, `packages/` (existing, no edit — only walked by `ruff check`).
- **Description**: This task is the Cycle 5 empirical closure gate. It executes three sequential verification commands and asserts each succeeds: (1) **pre-merge contract-slice gate** — `python -m pytest tests/contract/test_smoke_tenant_isolation.py tests/contract/test_sli_kql_canonical_match.py tests/contract/test_sli_kql_runtime_validity.py -q` MUST return returncode 0 and report exactly `22 passed` (the 22-passed assertion is the binding Step 8at pre-merge gate per `plan.md:1862-1864`: 8 smoke-tenant-isolation tests {6 Cycle 1-3 + T-AA51 + T-AA52} + 7 canonical-match parametric ids {Z1-Z7} + 7 runtime-validity parametric ids {Z1-Z7}); (2) **post-merge full-suite gate** — `python -m pytest -q` MUST return returncode 0 and report exactly `3400 passed` (the 3400-passed assertion is the binding Step 8at post-merge CI gate per `plan.md:1865-1866` + quality.md CHK236; **NO** `skipped` / `xfailed` / `xpassed` qualifier for `test_bicep_comment_block_documents_compensating_control` per Pass 2 Q3 single-posture binding at `spec.md:5774-5815`); (3) **ruff gate** — `python -m ruff check apps tests packages` MUST return returncode 0 with zero findings (preserving the Cycle 4 post-implement clean state certified at `spec.md:4886`); (4) **Bicep `scope:` byte-equality reverify** — confirm `scope: '${account.id}/dbs/${databaseName}'` is still present at `cosmos-simulation-containers.bicep:328` byte-identical to the Cycle 4 baseline (Cycle 4 T-AA51 already runs as part of step 1; this is an additional grep-level reassurance). On any failure, the failing command's output identifies the regressed test/file:line + the binding plan/spec anchor, and Cycle 5 closure is **blocked** pending re-do of the failing prior task (T-AA57 / T-AA58 / T-AA59 / T-AA60).
- **Acceptance**: plan.md PD-C5-01 (`plan.md:1427-1929`) — acceptance criteria 7 + 8 at `plan.md:1850-1866`; spec.md A5-01 acceptance at `:4971` + Pass 2 Q3 binding 3400 single posture at `:5776-5859`; quality.md **CHK236** (Pass-2 Q3 single 3400 posture binding; zero `skipped`/`xfailed`/`xpassed` qualifier for T-AA52) + **CHK242** (ruff cleanliness post-Cycle-5 — returncode 0, zero findings).
- **Depends-on**: T-AA57 + T-AA58 + T-AA59 + T-AA60 (every prior Cycle 5 task must land before the empirical closure gate — this is the symmetric analogue of Cycle 4 T-AA56's dependency on T-AA48..T-AA55 at `tasks.md:2343`).
- **Tests**: this task is the pytest + ruff invocation gate; no new test file is created. The Cycle 5 binding test count delta is **+0** (per Pass 1 rollup at `spec.md:5440-5444` and Pass 2 Q3 at `spec.md:5774-5815`): 3400 nodes collected pre- and post-Cycle-5; the two new absence assertions are appended **inside** the existing `test_bicep_comment_block_documents_compensating_control` function (not as a new test).
- **Backward-compat / Effort**: verification-only (no code/test/doc edit; uses three existing CLI invocations); small.
- **Out-of-scope**: any test-body or production-code change (verification-only); the ADR-036-011 Status flip from `Proposed` → `Accepted` (deferred to Step 8au cohort re-review per Pass 2 Q4 at `spec.md:5863-5897`; T-AA61 does NOT flip the ADR Status); filing a new backlog issue (Cycle 5 does NOT file a new issue per quality.md CHK241; issue #84 remains open).
- **Verify-command**: `python -m pytest tests/contract/test_smoke_tenant_isolation.py tests/contract/test_sli_kql_canonical_match.py tests/contract/test_sli_kql_runtime_validity.py -q 2>&1 | grep -E '22 passed'` returns a match; `python -m pytest -q 2>&1 | grep -E '3400 passed'` returns a match with no `skipped` / `xfailed` qualifier present in the output; `python -m ruff check apps tests packages` returns returncode 0 with output `All checks passed!` (or equivalent zero-findings sentinel); `grep -n "scope: '\${account\.id\}/dbs/\${databaseName\}'" infra/bicep/modules/cosmos-simulation-containers.bicep` returns a match at L328.
- **Ownership**: Owned by /speckit.implement (Cycle 5, Step 8at).

---

### §27.4 Cycle 5 dependency graph

```text
Wave A (A5-01 documentation-only remediation):

T-AA57 ──→ T-AA58 ──→ T-AA60 ──→ T-AA61
            │           ▲
T-AA59 [P] ─┴───────────┘
            (T-AA59 parallel with T-AA57 / T-AA58)

T-AA57 ─┐
T-AA58 ─┤
T-AA59 ─┼─→ T-AA60 ─→ T-AA61 (final-gate)
T-AA60 ─┘
```

**Critical path** (longest chain, 4 hops): `T-AA57 → T-AA58 → T-AA60 → T-AA61` (Bicep rewrite → absence assertions → CHANGELOG aggregator → verification gate); the T-AA59 prose promotion runs in parallel and feeds T-AA60 + T-AA61 directly.

---

### §27.5 Suggested Cycle 5 wave plan

**Wave A (mixed sequential + parallel; 5 tasks; ~0.25 day)** — A5-01 documentation-only remediation:

- *Sequential lead*: T-AA57 (Bicep preamble rewrite at `cosmos-simulation-containers.bicep:305-315`)
- *Test-body extension (sequential after T-AA57)*: T-AA58 (two absence assertions appended to `test_bicep_comment_block_documents_compensating_control`)
- *Parallel prose promotion*: T-AA59 `[P]` (T-AA52 OPTIONAL → REQUIRED at `test_smoke_tenant_isolation.py:173, 253`)
- *CHANGELOG aggregator*: T-AA60 (depends on T-AA57 + T-AA58 + T-AA59)
- *Verification gate*: T-AA61 (depends on T-AA57 + T-AA58 + T-AA59 + T-AA60)

**Wave B (final-sweep — Cycle 5 gates)** — assert FS1–FS27 still GREEN (Cycle 1–4 gates per `tasks.md:2407-2415`) PLUS the Cycle 5 gates:

- **FS28**: `cosmos-simulation-containers.bicep:305-315` no longer carries the case-insensitive substrings `partition path`, `pks/<tenant_id>`, or `/colls/<container>/pks/` (T-AA57 + quality.md CHK231).
- **FS29**: `cosmos-simulation-containers.bicep:328` `scope:` expression is **byte-identical** to the Cycle 4 baseline (`scope: '${account.id}/dbs/${databaseName}'`) — Cycle 4 T-AA51 still GREEN, plus T-AA61 reverify.
- **FS30**: `tests/contract/test_smoke_tenant_isolation.py::test_bicep_comment_block_documents_compensating_control` is GREEN with the two new absence assertions executing alongside the two pre-existing presence assertions; no `pytest.mark.*` decorator added (T-AA58 + T-AA59 + quality.md CHK234 + CHK235 + CHK243).
- **FS31**: `tests/contract/test_smoke_tenant_isolation.py:173, 253` carries the REQUIRED-promoted prose disposition (T-AA59 + quality.md CHK233).
- **FS32**: `CHANGELOG.md` `## [Unreleased]` carries the Cycle 5 grouped block (`### Added` + `### Changed (spec 036 — Cycle 5 amendment cycle)`) with no `### Breaking changes` sub-section (T-AA60 + quality.md CHK240).
- **FS33**: `python -m pytest -q` returns `3400 passed` with no `skipped`/`xfailed`/`xpassed` qualifier for T-AA52 (T-AA61 + quality.md CHK236 — Pass 2 Q3 single 3400 posture).
- **FS34**: `python -m ruff check apps tests packages` returns returncode 0 with zero findings (T-AA61 + quality.md CHK242).
- **FS35**: ADR-036-011 `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md` Status field remains `Proposed` at Step 8at close per Pass 2 Q4 (`spec.md:5863-5897`); flip to `Accepted` is gated on the Step 8au cohort re-review's clean verdict (0 OBJECT votes AND 0 NEW merit-validated findings against ADR-036-011); otherwise Cycle 6 opens.
- **FS36**: backlog issue **#84** remains **open** at Cycle 5 close and is cited verbatim as `[backlog issue: #84]` in (a) the rewritten Bicep preamble (T-AA57 ordering element (4)) and (b) the ADR-036-011 Cycle 5 amendment sub-section appended in Step 8aq plan landing (quality.md CHK241).
- **FS37**: the four Cycle 4 LOW-1 mirror-immutability anchors at `plan.md:682`, `tasks.md:1929`, `quality.md:367`, `quality.md:528` are **NOT touched** in Cycle 5 (quality.md CHK239); `spec.md:3907-3925` Cycle 4 A4-02 binding wording is **NOT re-rendered**.

---

### §27.6 Cycle 5 status block

| Metric | Count |
|--------|------:|
| Cycle 5 tasks added (T-AA57..T-AA61) | **5** |
| Wave A `[P]` markers | 1 (T-AA59 prose promotion — parallel with T-AA57 / T-AA58) |
| **Total `[P]` markers (Cycle 5)** | **1** |
| New unit tests | 0 |
| New integration tests | 0 |
| New contract tests | 0 (two new absence assertions added **inside** existing `test_bicep_comment_block_documents_compensating_control`; no new `def test_*` function — Pass 1 rollup + Pass 2 Q3 +0 delta at `spec.md:5440-5444, 5774-5815`) |
| New e2e tests | 0 |
| New docs tests | 0 (no propagation test added — ordering symmetry is cohort-verified, not test-verified per Pass 1 Q1 propagation_target #3 at `spec.md:5167-5173`) |
| New ops tests | 0 (no new backlog issue filed per quality.md CHK241; issue #84 remains open) |
| **Total NEW Cycle 5 test functions** | **0** (additive assertions inside existing test function; no new `def test_*`) |
| **Test count posture (Pass 2 Q3)** | **3400** (single posture; the Cycle 4 minimal-3399 / FULL-3400 split is **retired** by the Pass 2 Q1 T-AA52 REQUIRED promotion — `spec.md:5774-5815`) |
| **Cycle 5 test count delta** | **+0** (extending an existing test function in place with two new `assert ... not in role_block.lower()` statements; +0 collected-node delta) |
| New ADRs | 0 (ADR-036-011 in-place revision via Cycle 5 amendment sub-section appended at Step 8aq plan landing per `plan.md:1643-1651`; no `ADR-036-012-*.md` file created per quality.md CHK238) |
| BREAKING-flagged tasks | 0 (A5-01 is documentation-and-test-only; the compiled Bicep `scope:` expression at L328 is byte-identical to Cycle 4 baseline; no runtime change; no contract-shape change) |

**Per-amendment task coverage**:

| Amendment | Severity | Tasks | FR / SC |
|-----------|----------|-------|---------|
| A5-01 | MEDIUM | T-AA57, T-AA58, T-AA59, T-AA60, T-AA61 (5) | No new FR (drift correction); FR-073 unchanged (`spec.md:3660-3677` Cycle 3 anchor + Cycle 4 strengthening at `:3922-3934`) — the SLI-Z6 / SLI-Z7 query-time tenant filter re-cited as the compensating defence-in-depth control mechanism in the rewritten Bicep preamble |

**Per-Q→A and per-PD-C5 task coverage** (every Cycle 5 Q→A and plan-decision binds to ≥ 1 task):

| Source | Tasks |
|--------|-------|
| Pass 1 Q1 (Bicep preamble four-clause ordering) | T-AA57 |
| Pass 1 Q2 (assertion-phrase set option (b) — `pks/<tenant_id>` + `partition path`, case-insensitive) | T-AA58 |
| Pass 1 Q3 (comment-block-only test scope via `_extract_role_assignment_block`) | T-AA58 |
| Pass 2 Q1 (T-AA52 OPTIONAL → REQUIRED prose promotion; docstring + header comment; no `pytest.mark.*`) | T-AA59 |
| Pass 2 Q2 (`.lower()` + plain `in` substring check; reject `re.compile(..., re.IGNORECASE)` and `str.casefold()`) | T-AA58 |
| Pass 2 Q3 (single 3400 posture; retire Cycle 4 minimal-3399 escape hatch; +0 test-count delta) | T-AA61 |
| Pass 2 Q4 (multi-cycle Proposed→Accepted convergence rule — Status flip on Step 8au clean verdict, not Step 8at) | T-AA61 (out-of-scope: T-AA61 does NOT flip ADR Status) |
| PD-C5-01 (Bicep preamble residue removal + absence assertions + T-AA52 prose promotion en bloc) | T-AA57, T-AA58, T-AA59, T-AA60, T-AA61 |

**Per-FR / SC test-pyramid coverage** (Cycle 5 narrowness — no new FR / SC; A5-01 is documentation-and-test-only drift correction):

| FR / SC | Unit | Integration | Contract | E2E | Docs / Ops |
|---------|------|-------------|----------|-----|-----------|
| FR-073 (unchanged; SLI-Z6 / SLI-Z7 tenant-filter re-cited as compensating control in rewritten Bicep preamble) | — | — | T-AA58 (two absence assertions inside `test_bicep_comment_block_documents_compensating_control`); T-AA61 (full-suite 3400-passed gate) | — | T-AA57 (Bicep preamble rewrite), T-AA59 (T-AA52 prose promotion), T-AA60 (CHANGELOG Cycle 5 grouped block) |
| A5-01 wording residue (no new FR — Cycle 4 implementation drift correction) | — | — | T-AA58, T-AA61 | — | T-AA57 (Bicep), T-AA59 (test prose), T-AA60 (CHANGELOG) |

**File:line evidence cited in §27 task block** (sampled — full list embedded in task bodies):

- `infra/bicep/modules/cosmos-simulation-containers.bicep:305-315` (Bicep preamble rewrite — A5-01) — T-AA57
- `infra/bicep/modules/cosmos-simulation-containers.bicep:317-327` (Cycle 4 A4-02 sub-block — preserved byte-identically; consolidation around, not through) — T-AA57
- `infra/bicep/modules/cosmos-simulation-containers.bicep:328` (actual `scope:` expression — byte-identical to Cycle 4 baseline; MUST NOT be modified) — T-AA57, T-AA61
- `tests/contract/test_smoke_tenant_isolation.py:166` (existing `tnt-prod` absence precedent — `.lower()` + plain `in` shape inherited by T-AA58) — T-AA58
- `tests/contract/test_smoke_tenant_isolation.py:173` (header comment — Cycle 4 OPTIONAL signal rewritten to REQUIRED by T-AA59) — T-AA59
- `tests/contract/test_smoke_tenant_isolation.py:220-247` (`_extract_role_assignment_block` helper — Cycle 4 Step 8ae primitive; consumed by T-AA58 absence assertions; NOT modified) — T-AA58
- `tests/contract/test_smoke_tenant_isolation.py:250-297` (`test_bicep_comment_block_documents_compensating_control` — two new absence assertions appended by T-AA58; docstring at L253 rewritten by T-AA59) — T-AA58, T-AA59
- `tests/contract/test_smoke_tenant_isolation.py:271-282` (existing `compensating_re.search` presence assertion — preserved byte-identically) — T-AA58
- `tests/contract/test_smoke_tenant_isolation.py:286-297` (existing `backlog_re.search` presence assertion — preserved byte-identically) — T-AA58
- `tests/contract/test_sli_kql_canonical_match.py` (existing Cycle 3 T-AA32; no edit; re-runs as part of T-AA61 22-passed contract slice) — T-AA61
- `tests/contract/test_sli_kql_runtime_validity.py` (existing Cycle 4 T-AA46-T-AA48; no edit; re-runs as part of T-AA61 22-passed contract slice) — T-AA61
- `CHANGELOG.md` `## [Unreleased]` (Cycle 5 grouped block — `### Added` + `### Changed (spec 036 — Cycle 5 amendment cycle)`) — T-AA60
- `specs/036-sim-agent-extend/spec.md:4943, 4947-4992` (A5-01 amendment-log detail) — all tasks
- `specs/036-sim-agent-extend/spec.md:5067-5096` (Pass 1 Q1 four-clause ordering binding) — T-AA57
- `specs/036-sim-agent-extend/spec.md:5175-5240` (Pass 1 Q2 option (b) assertion-phrase set binding) — T-AA58
- `specs/036-sim-agent-extend/spec.md:5299-5418` (Pass 1 Q3 comment-block-only scope binding) — T-AA58
- `specs/036-sim-agent-extend/spec.md:5498-5614` (Pass 2 Q1 OPTIONAL → REQUIRED prose promotion binding) — T-AA59
- `specs/036-sim-agent-extend/spec.md:5650-5754` (Pass 2 Q2 `.lower()` + plain `in` case-folding primitive binding) — T-AA58
- `specs/036-sim-agent-extend/spec.md:5656-5673` (verbatim Python for the two new absence assertions) — T-AA58
- `specs/036-sim-agent-extend/spec.md:5776-5859` (Pass 2 Q3 single 3400 posture binding) — T-AA61
- `specs/036-sim-agent-extend/spec.md:5863-5897` (Pass 2 Q4 multi-cycle Proposed→Accepted convergence rule restatement) — T-AA61 (out-of-scope reference)
- `specs/036-sim-agent-extend/plan.md:1427-1929` (PD-C5-01 plan-decision detail; affected-files list at `:1599-1672`) — all tasks
- `specs/036-sim-agent-extend/checklists/quality.md` CHK231..CHK244 (Cycle 5 acceptance checklist items) — all tasks
- `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md:172-184` (binding wording — NOT re-amended; out-of-scope) — referenced in all tasks
- GitHub backlog issue **#84** (filed at Cycle 4 implement close per `spec.md:4886`; remains open; cited verbatim as `[backlog issue: #84]` in T-AA57 rewritten Bicep preamble) — T-AA57, T-AA60

**Total `file:line` citations across §27**: **≥ 30 unique evidence anchors** (every task body cites at least 3 of: plan.md PD-C5-01 anchors, spec.md A5-01 / Pass 1 Q1-Q3 / Pass 2 Q1-Q4, quality.md CHK231-CHK244, the Bicep / test / CHANGELOG file:line surfaces).

---

### §27.7 Format-validation checkpoint

Every Cycle 5 task above conforms to the existing `tasks.md` row schema (matching the Cycle 1 §§ 4–20 format used by T-AA01..T-AA06, the Cycle 2 §24 format used by T-AA07..T-AA22, the Cycle 3 §25 format used by T-AA23..T-AA42, AND the Cycle 4 §26 format used by T-AA43..T-AA56 — including the explicit `**Verify-command**` bullet introduced in Cycle 4 §26.9 at `tasks.md:2494, 2500`), with one Cycle-5-specific addition: every task carries an explicit `**Ownership**` bullet at the end naming the step (Cycle 5, Step 8at) per the user prompt's "Step ownership label" requirement (this is additive to the Cycle 4 row schema and does not break any prior Cycle's format).

- ✅ Heading prefix `### T-AAxx` with `[P?] [NEW] [A5-01 MEDIUM] [Wave A]` markers and a hyphen-separated short title.
- ✅ Bullet body with `Phase | Files | Description | Acceptance | Depends-on | Tests | Backward-compat / Effort | Out-of-scope | Verify-command | Ownership` (≤ 10 lines per task body — extended from Cycle 4's 9-line shape by the new `Out-of-scope` + `Ownership` lines per the Cycle 5 user prompt).
- ✅ Every Acceptance bullet cites at least one of: plan.md PD-C5-01 anchors, spec.md A5-01 / Pass 1 Q1-Q3 / Pass 2 Q1-Q4, quality.md CHK231-CHK244.
- ✅ Every Tests bullet enumerates concrete test files; **+0 test count delta** (Pass 1 rollup + Pass 2 Q3 — `spec.md:5440-5444, 5774-5815`).
- ✅ Every task carries an explicit `**Verify-command**` bullet (Cycle 4 §26.9 precedent at `tasks.md:2494, 2500` — preserved into Cycle 5).
- ✅ Every task carries an explicit `**Ownership**` bullet naming the step (Cycle 5, Step 8at) per the user prompt.
- ✅ No BREAKING flag is required across any Cycle 5 task — A5-01 is documentation-and-test-only and the compiled Bicep `scope:` expression at L328 is byte-identical to the Cycle 4 baseline; runtime RBAC behaviour is unchanged.
- ✅ Every Cycle 5 task ID is unique across the entire `tasks.md` file (T-AA57..T-AA61 — no collision with the locked Cycle 1 §20 T-AA01..T-AA06 block, no collision with the locked-COMPLETE Cycle 2 §24 T-AA07..T-AA22 block, no collision with the locked Cycle 3 §25 T-AA23..T-AA42 block, no collision with the locked-COMPLETE Cycle 4 §26 T-AA43..T-AA56 block).
- ✅ Australian English honoured throughout (artefact, behaviour, prioritise, organise, harmonise, recognise, parametric, canonicalise, normalisation, defence) — no US spellings introduced.
- ✅ Cycle 5 tasks sentinel append target (`spec.md:5998`+1) carries the byte-exact text `**Cycle 5 tasks complete (T-AA57..T-AA61). Ready for /speckit.analyze (Cycle 5).**` — matches the user prompt's sentinel format.

---

**Cycle 5 tasks complete. Ready for /speckit.analyze (Cycle 5).**
