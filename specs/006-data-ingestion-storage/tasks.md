# Tasks: Data Ingestion Pipelines, Storage Architecture, and Simulation Framework

**Input**: Design documents from `/specs/006-data-ingestion-storage/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/openapi-ingestion.yaml, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialisation, schema extension, and new domain models

- [x] T001 Create `apps/ingestion/` directory structure with `__init__.py`, `worker.py`, `pipelines/`, `normalisers/`, `simulation/`, `simulation/generators/`
- [x] T002 [P] Add `simulationRunId` property to `provenance` in `packages/schemas/signal-envelope.schema.json` (FR-002a)
- [x] T003 [P] Create `IngestionAuditEntry` Pydantic model in `packages/domain/src/domain/models/ingestion_audit.py` with fields: audit_id, signal_id, data_source_id, correlation_id, timestamp, outcome, validation_errors, raw_payload_blob_uri, normalisation_latency_ms, pipeline_id, dedup_hash
- [x] T004 [P] Create `SimulationScenario` Pydantic model in `packages/domain/src/domain/models/simulation_scenario.py` with fields: scenario_id, name, scenario_type, target_region, target_jurisdiction_ids, activated_data_source_ids, time_compression_ratio, event_phases, misinformation_ratio, historical_overlay_path, created_by, created_at
- [x] T005 [P] Create `SimulationRun` Pydantic model in `packages/domain/src/domain/models/simulation_run.py` with fields: run_id, scenario_id, status, started_at, completed_at, current_phase, signals_generated, total_signals, time_compression_ratio, misinformation_ratio, created_by, created_at and state transition validation
- [x] T006 [P] Create `IngestionPipelineConfig` Pydantic model in `apps/ingestion/pipeline_config.py` with fields: pipeline_id, source_class, data_source_ids, poll_interval_seconds, endpoint_url, endpoint_format, circuit_breaker_threshold, dedup_ttl_seconds, enabled
- [x] T007 Add `lxml`, `httpx`, `jsonschema` dependencies to `apps/ingestion/pyproject.toml` (or `apps/api/pyproject.toml` if shared)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core pipeline framework, storage layer, and shared services that MUST be complete before ANY user story

**⚠ CRITICAL**: No user story pipeline work can begin until this phase is complete

- [x] T008 Create base pipeline class `IngestionPipelineBase` in `apps/api/app/services/ingestion/pipeline_base.py` with: polling loop, circuit breaker state machine (closed→open→half-open→closed), raw payload blob storage, SignalEnvelope schema validation, correlation ID generation, provenance attachment, freshness score computation, confidence score computation, observability metric emission (FR-001, FR-013–FR-018b)
- [x] T009 Create dedup service in `apps/api/app/services/ingestion/dedup_service.py` with Redis-backed content-hash lookup, configurable TTL, source-specific canonical key computation (FR-018a)
- [x] T010 [P] Create incident association service in `apps/api/app/services/ingestion/incident_association.py` — match signal jurisdiction + location against active incidents, set `incidentId`, handle multi-incident fan-out (FR-019a)
- [x] T011 [P] Create normaliser registry in `apps/api/app/services/ingestion/normaliser_registry.py` — dispatch source-specific normalisers by endpoint_format enum
- [x] T012 Create signal repository in `packages/domain/src/domain/repositories/signal_repository.py` — Cosmos DB CRUD with hierarchical partition key (scope/jurisdictionId/dataSourceId), national signal fan-out, simulation-scoped partitioning (FR-025, FR-029). Located in shared `packages/domain` so both the API app and ingestion worker can import it without cross-app dependencies
- [x] T013 [P] Modify `apps/api/app/repositories/cosmos_scope.py` — add `simulation_scope(run_id)` and `live_scope()` helper functions for partition key generation
- [x] T014 Create raw payload blob storage helper in `apps/api/app/services/ingestion/blob_storage.py` — store under `raw-payloads/{dataSourceId}/{YYYY-MM-DD}/{signalId}.{format}` and `binary-assets/{incidentId}/{dataSourceId}/{timestamp}.{format}` (FR-026, FR-027)
- [x] T015 [P] Create audit trail writer in `apps/api/app/services/ingestion/audit_writer.py` — append IngestionAuditEntry as JSON Lines to `audit/ingestion/{YYYY-MM-DD}/{hour}.jsonl` in Blob Storage (FR-028)
- [x] T016 Create pipeline worker lifecycle manager in `apps/ingestion/worker.py` — start/stop pipeline instances from config, graceful shutdown, health check endpoints, liveness/readiness probes (FR-001a)
- [x] T017 [P] Write contract test for circuit breaker state transitions (closed→open after 3 failures, open→half-open after backoff, half-open→closed on success) in `tests/contract/test_circuit_breaker.py`
- [x] T018 [P] Write contract test for dedup hash computation and Redis TTL behaviour in `tests/contract/test_dedup_service.py`
- [x] T019 [P] Write contract test for incident association — signal inside active incident area gets `incidentId` set, outside gets null, national matches multiple in `tests/contract/test_incident_association.py`
- [x] T020 [P] Write contract test for signal repository — partition key correctness, simulation isolation, national fan-out, dashboard query latency check in `tests/contract/test_signal_storage.py`

**Checkpoint**: Pipeline framework ready — source-specific pipeline and normaliser implementation can now begin

---

## Phase 3: User Story 1 — Ingest authoritative weather and hazard feeds (Priority: P1) 🎯 MVP

**Goal**: Ingest BoM warnings, forecasts, observations, flood warnings, radar, and GA earthquake/tsunami/hotspot feeds as normalised SignalEnvelopes with provenance

**Independent Test**: Feed sample BoM XML warnings and GA GeoJSON earthquake alerts into the pipeline, verify normalisation, provenance, confidence scoring, circuit breaker, dedup, and Monitoring Agent handoff

### Implementation for User Story 1

- [x] T021 [P] [US1] Create BoM XML normaliser in `apps/ingestion/normalisers/bom_xml_normaliser.py` — parse BoM product XML (XSD v1.7), extract warning type, affected areas, issue time, map to SignalEnvelope with `category=weather`, `source.kind=authoritative`, confidence=0.95
- [x] T022 [P] [US1] Create CAP normaliser in `apps/ingestion/normalisers/cap_normaliser.py` — parse Common Alerting Protocol XML for flood/tsunami warnings, map urgency/severity/certainty to confidence
- [x] T023 [P] [US1] Create GeoJSON normaliser in `apps/ingestion/normalisers/geojson_normaliser.py` — parse GeoJSON FeatureCollection, extract properties + geometry, map to SignalEnvelope
- [x] T024 [P] [US1] Create JSON observation normaliser in `apps/ingestion/normalisers/json_observation_normaliser.py` — parse BoM JSON station observations, validate field types
- [x] T025 [P] [US1] Create binary metadata normaliser in `apps/ingestion/normalisers/binary_metadata_normaliser.py` — create metadata-only SignalEnvelope for radar/satellite with source URI, coverage area, no binary download by default (FR-009a)
- [x] T026 [US1] Create BoM warnings pipeline in `apps/ingestion/pipelines/bom_warnings.py` — poll FTP `ftp://ftp.bom.gov.au/anon/gen/fwo/`, use BoM XML normaliser, 60s interval (FR-004)
- [x] T027 [P] [US1] Create BoM observations pipeline in `apps/ingestion/pipelines/bom_observations.py` — poll BoM web service, use JSON observation normaliser, 5-min interval for summaries, 30-min for stations (FR-004)
- [x] T028 [P] [US1] Create BoM radar pipeline in `apps/ingestion/pipelines/bom_radar.py` — poll FTP `ftp://ftp.bom.gov.au/anon/gen/radar/`, use binary metadata normaliser, 5-min interval, incident-triggered download (FR-004, FR-009a)
- [x] T029 [P] [US1] Create GA earthquake pipeline in `apps/ingestion/pipelines/ga_earthquakes.py` — poll `earthquakes.ga.gov.au`, use GeoJSON normaliser, 60s interval (FR-005)
- [x] T030 [P] [US1] Create GA hotspot pipeline in `apps/ingestion/pipelines/ga_hotspots.py` — poll GA Hotspots service, use GeoJSON normaliser, 15-min interval (FR-005)
- [x] T030a [P] [US1] Create BoM RSS feed consumer in `apps/ingestion/pipelines/bom_rss.py` — subscribe to state-based warning RSS feeds from `bom.gov.au/rss/` to supplement FTP polling for lower-latency notification of new warnings. Parse Atom/RSS entries to detect new product codes, triggering immediate FTP fetch for full XML product (FR-004 RSS Feeds)
- [x] T030b [US1] Create GA tsunami warnings pipeline — configure BoM warnings pipeline (T026) to also handle tsunami warning CAP/XML products from the Joint Australian Tsunami Warning Centre at 30-second polling interval (FR-005 Tsunami Warnings). This may be a separate pipeline instance with a faster poll interval than the 60s general warnings pipeline
- [x] T031 [P] [US1] Write contract test: BoM XML warning → correct SignalEnvelope with category, source, confidence, provenance in `tests/contract/test_bom_normaliser.py`
- [x] T032 [P] [US1] Write contract test: GA earthquake GeoJSON → correct SignalEnvelope with geohazard category, Point location in `tests/contract/test_geojson_normaliser.py`
- [x] T033 [US1] Write integration test: full BoM warning pipeline lifecycle (poll → normalise → dedup → validate → store → audit) with mocked FTP endpoint in `tests/integration/test_ingestion_pipeline.py`

**Checkpoint**: BoM and GA authoritative feeds ingested — core hub value proposition operational

---

## Phase 4: User Story 2 — Ingest fire service and SES incident feeds (Priority: P2)

**Goal**: Ingest NSW RFS, VIC CFA, QLD QFES, SA CFS, WA DFES, TAS TFS, ACT ESA, NT PFES fire incidents and NSW/VIC/QLD SES flood intelligence as normalised SignalEnvelopes

**Independent Test**: Feed NSW RFS GeoJSON sample into fire pipeline, verify field mapping (title, category, status, alertLevel, geometry)

### Implementation for User Story 2

- [x] T034 [P] [US2] Create state fire service pipeline in `apps/ingestion/pipelines/fire_service.py` — parameterised for all 8 state/territory services (NSW RFS, VIC CFA, QLD QFES, SA CFS, WA DFES, TAS TFS, ACT ESA, NT PFES), use GeoJSON normaliser with per-state property mapping, 60s interval (FR-006)
- [x] T035 [P] [US2] Create SES flood intel pipeline in `apps/ingestion/pipelines/ses_flood.py` — parameterised for NSW/VIC/QLD SES, use GeoJSON normaliser, 2-min interval (FR-007)
- [x] T036 [P] [US2] Write contract test: NSW RFS GeoJSON Feature → SignalEnvelope with `category=fire`, alert level mapped to confidence, geometry preserved in `tests/contract/test_geojson_normaliser.py` (extend existing)
- [x] T037 [US2] Write contract test: different state property names produce identical normalised output — verify structural uniformity across NSW RFS, VIC CFA formats in `tests/contract/test_geojson_normaliser.py`

**Checkpoint**: National fire and flood incident picture available — all 8 states/territories + 3 SES feeds

---

## Phase 5: User Story 3 — Ingest sensor, IoT, and satellite data (Priority: P3)

**Goal**: Ingest BoM AWS station observations, river gauge networks, EPA air quality sensors with range validation; ingest Sentinel and Himawari satellite imagery with hybrid metadata-only / incident-triggered download

**Independent Test**: Feed sample BoM AWS JSON observations with valid and invalid sensor readings, verify range validation, freshness scoring, and rejected signal handling

### Implementation for User Story 3

- [x] T038 [P] [US3] Create BoM AWS sensor pipeline in `apps/ingestion/pipelines/sensor_aws.py` — poll BoM web service JSON, use JSON observation normaliser with range validation (temp -20–55°C, wind ≥0, pressure 900–1100hPa), 5-min interval (FR-008)
- [x] T039 [P] [US3] Create river gauge pipeline in `apps/ingestion/pipelines/sensor_river_gauge.py` — poll BoM Water Data Online, use JSON observation normaliser with flood threshold comparison, 5-min interval (FR-008)
- [x] T040 [P] [US3] Create EPA air quality pipeline in `apps/ingestion/pipelines/sensor_epa_air.py` — poll state EPA JSON endpoints, use JSON observation normaliser, 30-min interval (FR-008)
- [x] T041 [P] [US3] Create Sentinel satellite pipeline in `apps/ingestion/pipelines/satellite_sentinel.py` — poll Copernicus Data Space API, use binary metadata normaliser, 6-hour interval, incident-triggered GeoTIFF download (FR-009, FR-009a)
- [x] T042 [P] [US3] Create Himawari satellite pipeline in `apps/ingestion/pipelines/satellite_himawari.py` — poll BoM FTP `ftp://ftp.bom.gov.au/anon/gen/gms/`, use binary metadata normaliser, 10-min interval, incident-triggered download (FR-009, FR-009a)
- [x] T043 [P] [US3] Write contract test: BoM AWS observation with valid readings → correct SignalEnvelope with freshness score in `tests/contract/test_bom_normaliser.py` (extend)
- [x] T044 [P] [US3] Write contract test: sensor reading failing range validation (temp=150°C) → `validationStatus=rejected`, low confidence in `tests/contract/test_bom_normaliser.py` (extend)
- [x] T045 [US3] Write integration test: satellite pipeline metadata-only mode vs incident-triggered download mode in `tests/integration/test_ingestion_pipeline.py` (extend)
- [x] T045a [US3] Create on-demand binary retrieval service in `apps/api/app/services/ingestion/binary_retrieval.py` — given a signal ID with metadata-only `binaryAssetUri` (pointing to source), download the full binary from the source (subject to BoM FTP delete-time), store in Blob Storage per FR-027, and update the signal's `payload.binaryAssetUri` to the stored blob URI (FR-009a on-demand retrieval)
- [x] T045b [P] [US3] Write contract test: on-demand retrieval downloads binary, stores in `binary-assets/_on-demand/`, updates signal payload in `tests/contract/test_signal_storage.py` (extend)

**Checkpoint**: Physical ground-truth sensor + satellite data flowing with validation — Risk Assessment Agent can generate hazard assessments

---

## Phase 6: User Story 4 — Ingest social media and community reports (Priority: P4)

**Goal**: Ingest X/Twitter, Facebook, Reddit social feeds and Snap Send Solve community reports with trust scoring and tiered misinformation detection

**Independent Test**: Feed sample social media posts through pipeline, verify trust tier assignment, Tier 1 burst/contradiction/amplification detection, and confidence reduction

### Implementation for User Story 4

- [x] T046 [P] [US4] Create misinformation detector in `apps/api/app/services/ingestion/misinformation_detector.py` — implement Tier 1 rule-based heuristics: burst detection (≥20 posts/10min), contradiction detection (social vs authoritative), duplicate amplification (cosine similarity >0.9 in 5min) (FR-010a)
- [x] T047 [P] [US4] Create X/Twitter pipeline in `apps/ingestion/pipelines/social_twitter.py` — X API v2 filtered stream, keyword matching (bushfire/flood/cyclone/evacuation/emergency/SES), trust tier 6, rate limit compliance (FR-010)
- [x] T048 [P] [US4] Create Facebook pipeline in `apps/ingestion/pipelines/social_facebook.py` — Meta Graph API for emergency pages, 5-min interval, trust tier 6 (FR-010)
- [x] T049 [P] [US4] Create Reddit pipeline in `apps/ingestion/pipelines/social_reddit.py` — Reddit JSON API for Australian subreddits, 2-min active/15-min idle interval, trust tier 6 (FR-010)
- [x] T050 [P] [US4] Create Snap Send Solve pipeline in `apps/ingestion/pipelines/community_snap.py` — partner API, geotagged reports, 5-min interval, trust tier 5 (FR-011)
- [x] T051 [P] [US4] Write contract test: burst detection flags 20+ posts on same topic in 10 min → `validationStatus=escalated` in `tests/contract/test_misinformation_detector.py`
- [x] T052 [P] [US4] Write contract test: contradiction detection — social signal with no matching authoritative signal → reduced confidence in `tests/contract/test_misinformation_detector.py`
- [x] T053 [P] [US4] Write contract test: duplicate amplification — near-identical text in 5 min → earliest retained, duplicates escalated in `tests/contract/test_misinformation_detector.py`
- [x] T054 [US4] Modify Monitoring Agent in `apps/agents/monitoring/agent.py` — add Tier 2 LLM-based evaluation of `validationStatus=escalated` social signals using existing `LLMCallMixin`, with safe fallback (hold for human review when LLM unavailable) (FR-010a)
- [x] T055 [US4] Write contract test: Monitoring Agent Tier 2 LLM classifies misinformation → `validationStatus=rejected`, not forwarded to Risk Assessment in test file extending existing monitoring agent tests

**Checkpoint**: Social and community intelligence flowing with misinformation safeguards — completes the full spectrum of signal sources

---

## Phase 7: User Story 5 — Multi-tenant storage and audit trail (Priority: P5)

**Goal**: Cosmos DB signal storage with hierarchical partition key, Blob Storage for raw payloads and binaries, append-only audit trail, national signal fan-out, simulation isolation

**Independent Test**: Ingest signals for two different jurisdictions, verify partition isolation, raw payload retrievability, and audit trail completeness

### Implementation for User Story 5

- [x] T056 [US5] Configure Cosmos DB `signals` container with hierarchical partition key `/scope/jurisdictionId/dataSourceId` and composite index on `(jurisdictionId, category, occurredAt DESC)` in `infra/bicep/main.bicep` (FR-025)
- [x] T057 [P] [US5] Configure Cosmos DB `simulation` container with partition key `/scenario_id` in `infra/bicep/main.bicep`
- [x] T058 [P] [US5] Configure Azure Blob Storage containers: `raw-payloads`, `binary-assets`, `audit`, `simulation` in `infra/bicep/main.bicep`
- [x] T059 [P] [US5] Configure ingestion worker Azure Container App (internal ingress, 1-6 replicas, system managed identity, KEDA scaling rules) in `infra/bicep/main.bicep` (FR-001a)
- [x] T060 [US5] Implement national signal fan-out in signal repository — when signal has `geographic_coverage=national`, create reference records in each affected jurisdiction partition in `apps/api/app/repositories/signal_repository.py` (research decision: hierarchical partition key)
- [x] T061 [US5] Modify Monitoring Agent in `apps/agents/monitoring/agent.py` — add retrospective incident association subagent: scan signals with `incidentId=null` matching new incident's jurisdiction/location within configurable lookback window (default 24h), update `incidentId`, write audit entry (FR-019b)
- [x] T062 [P] [US5] Modify `GET /signals` route in `apps/api/app/api/routes/signals.py` — add query parameters: `jurisdictionId`, `category`, `dataSourceId`, `since`, `validationStatus`, `limit`, `offset` (contract: openapi-ingestion.yaml)
- [x] T063 [US5] Write contract test: signals partitioned by jurisdiction — NSW signal invisible to VIC query scope in `tests/contract/test_signal_storage.py` (extend)
- [x] T064 [P] [US5] Write contract test: every persisted signal has corresponding raw payload blob and audit entry (SC-007) in `tests/contract/test_signal_storage.py` (extend)
- [x] T065 [US5] Write contract test: simulation signal stored in `sim_{runId}` scope, invisible to live queries (SC-009) in `tests/contract/test_signal_storage.py` (extend)

**Checkpoint**: Storage layer complete with multi-tenant isolation, audit trail, and simulation partitioning

---

## Phase 8: User Story 6 — Simulation framework (Priority: P6)

**Goal**: Parametric signal generators for bushfire, flood, cyclone, severe storm scenarios with configurable temporal progression, geographic coherence, social media misinformation mix, and optional historical overlay

**Independent Test**: Start a flood simulation for Hawkesbury-Nepean catchment, verify BoM flood warnings, river gauge hydrograph progression, SES updates, and social media signals generated with simulation provenance

### Implementation for User Story 6

- [x] T066 [US6] Create simulation runner in `apps/ingestion/simulation/simulation_runner.py` — orchestrate scenario lifecycle: configuring → running → completed/aborted, time compression, phase progression, concurrent-safe (FR-032, FR-037a)
- [x] T067 [P] [US6] Create scenario templates in `apps/ingestion/simulation/scenario_templates.py` — define bushfire, flood, cyclone, severe_storm templates with phase definitions, activated sources, and parametric model references (FR-038)
- [x] T068 [P] [US6] Create flood generator in `apps/ingestion/simulation/generators/flood_generator.py` — hydrograph curve model with configurable rise rate, peak duration, recession, crossing minor/moderate/major thresholds (FR-033)
- [x] T069 [P] [US6] Create fire generator in `apps/ingestion/simulation/generators/fire_generator.py` — FFDI/GFDI-based fire spread model with wind, temperature, humidity, fuel load inputs (FR-033)
- [x] T070 [P] [US6] Create cyclone generator in `apps/ingestion/simulation/generators/cyclone_generator.py` — track and intensity model with central pressure, radius of max wind, forward speed (FR-033)
- [x] T071 [P] [US6] Create weather generator in `apps/ingestion/simulation/generators/weather_generator.py` — BoM warning/forecast signal generator paired to scenario type
- [x] T072 [P] [US6] Create sensor generator in `apps/ingestion/simulation/generators/sensor_generator.py` — plausible sensor readings within documented ranges per sensor type (FR-033)
- [x] T073 [P] [US6] Create social media generator in `apps/ingestion/simulation/generators/social_generator.py` — configurable mix: 70% accurate, 15% duplicate, 15% misinformation (FR-036)
- [x] T074 [P] [US6] Create historical overlay in `apps/ingestion/simulation/generators/historical_overlay.py` — replay historical event dataset with perturbation (shifted location, altered timing, severity scaling) (FR-033a)
- [x] T075 [US6] Add simulation API routes in `apps/api/app/api/routes/` — `POST/GET /simulations/scenarios`, `POST /simulations/runs`, `GET /simulations/runs/{runId}`, `POST /simulations/runs/{runId}/abort` per openapi-ingestion.yaml contract
- [x] T076 [P] [US6] Write contract test: each generator output passes SignalEnvelope schema validation (SC-006) in `tests/simulation/test_flood_scenario.py`, `tests/simulation/test_bushfire_scenario.py`, `tests/simulation/test_cyclone_scenario.py`, `tests/simulation/test_storm_scenario.py`
- [x] T077 [US6] Write integration test: flood simulation generates hydrograph with correct threshold crossings in `tests/integration/test_simulation_runner.py`
- [x] T078 [US6] Write integration test: concurrent simulation + live ingestion — no cross-contamination (SC-009), live throughput ≥ 50k signals/hr (FR-037a) in `tests/integration/test_simulation_runner.py`
- [x] T078a [US6] Write contract test: time compression ratio correctly scales signal generation cadence — a 24:1 ratio produces signals at 24× the normal cadence in `tests/simulation/test_flood_scenario.py` (FR-034)
- [x] T078b [US6] Write contract test: geographic coherence for flood scenario — upstream gauge readings rise before downstream gauge readings within the same simulation run in `tests/simulation/test_flood_scenario.py` (FR-035)

**Checkpoint**: Full simulation framework operational — scenario rehearsals, agent evaluation, and Constitutional Quality Gate exercises enabled

---

## Phase 9: User Story 7 — Field reports and IMS integration (Priority: P7)

**Goal**: Ingest manual field officer reports via `POST /signals` and structured feeds from ICON/WebEOC incident management systems

**Independent Test**: Submit a field officer report via the API, verify normalisation to SignalEnvelope with `source.kind=field_report` and `trust_tier=tier_4_field_reports`

### Implementation for User Story 7

- [x] T079 [P] [US7] Create IMS pipeline in `apps/ingestion/pipelines/ims_webeoc.py` — poll WebEOC REST API and ICON API for incident updates, map to SignalEnvelope with `source.kind=field_report`, 2-min interval (FR-012)
- [x] T080 [US7] Modify `POST /signals` route in `apps/api/app/api/routes/signals.py` — ensure field officer reports submitted via API are processed through the pipeline framework (normalise, validate, store, audit) with `source.kind=field_report`, `trust_tier=tier_4_field_reports` (FR-012)
- [x] T081 [P] [US7] Write contract test: field report via `POST /signals` → SignalEnvelope with correct kind, trust tier, officer identity in provenance in existing signal contract tests

**Checkpoint**: All 7 ingestion source categories operational — authoritative, fire/SES, sensor/satellite, social/community, field/IMS

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Observability, pipeline health endpoint, documentation, performance validation

- [x] T082 [P] Add `GET /ingestion/status` endpoint in `apps/api/app/api/routes/` — aggregated pipeline health: per-pipeline circuit breaker state, signals/hour, dedup hit rate, normalisation latency p95, dead-letter depth (per openapi-ingestion.yaml PipelineStatus schema)
- [x] T083 [P] Refactor existing ingestion services — replace `AuthoritativeIngestionService`, `IoTIngestionService`, `CommunityIngestionService` placeholders in `apps/api/app/services/ingestion/` to use the new pipeline framework
- [x] T084 [P] Add pipeline configuration file or environment variable loader — define all 20+ pipeline instances with their polling intervals, endpoints, and data source IDs from seed catalogue
- [x] T085 Run quickstart.md verification checklist — validate all phases A–I complete
- [x] T086 [P] Write integration test: end-to-end ingestion latency ≤90s for Tier 1 authoritative source (SC-001) in `tests/integration/test_ingestion_pipeline.py`
- [x] T087 [P] Write integration test: sustained throughput ≥50,000 signals/hour (SC-002) in `tests/integration/test_ingestion_pipeline.py`
- [x] T088 [P] Write integration test: circuit breaker marks degraded source within 3 minutes, auto-recovers within 1 minute (SC-008) in `tests/integration/test_circuit_breaker.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — first MVP deliverable
- **US2 (Phase 4)**: Depends on Phase 2 — can start in parallel with US1 (uses same GeoJSON normaliser)
- **US3 (Phase 5)**: Depends on Phase 2 — can start in parallel with US1/US2
- **US4 (Phase 6)**: Depends on Phase 2 — can start in parallel, but Tier 2 LLM (T054) depends on Monitoring Agent understanding from US1
- **US5 (Phase 7)**: Depends on Phase 2 — storage tasks (T056-T059) can start in parallel with US1; repo integration (T060-T065) depends on signal repository from Phase 2
- **US6 (Phase 8)**: Depends on Phases 2 + normalisers from US1 — simulation feeds through same pipelines
- **US7 (Phase 9)**: Depends on Phase 2 — can start in parallel with all other user stories
- **Polish (Phase 10)**: Depends on all user stories being functionally complete

### User Story Dependencies

- **US1 (P1)**: Independent after Phase 2 — creates normalisers reused by US2, US3, US6
- **US2 (P2)**: Independent after Phase 2 — reuses GeoJSON normaliser from US1 (T023), but has its own pipeline files
- **US3 (P3)**: Independent after Phase 2 — extends JSON observation normaliser, adds satellite pipelines
- **US4 (P4)**: Independent after Phase 2 — misinformation detector is self-contained; Tier 2 LLM modifies Monitoring Agent
- **US5 (P5)**: Infrastructure tasks (T056-T059) are independent; storage integration tasks depend on signal repository (T012)
- **US6 (P6)**: Depends on normalisers existing (from US1/US2/US3) — generators inject into same pipelines
- **US7 (P7)**: Independent after Phase 2 — simplest story, extends existing `POST /signals`

### Parallel Opportunities Per Phase

**Phase 1**: T002, T003, T004, T005, T006, T007 all parallelisable  
**Phase 2**: T010+T011+T013+T015 parallel; T017+T018+T019+T020 parallel (tests)  
**Phase 3**: T021+T022+T023+T024+T025 parallel (normalisers); T027+T028+T029+T030 parallel (pipelines); T031+T032 parallel (tests)  
**Phase 4**: T034+T035 parallel; T036+T037 parallel (tests)  
**Phase 5**: T038+T039+T040+T041+T042 all parallel; T043+T044 parallel (tests)  
**Phase 6**: T046+T047+T048+T049+T050 all parallel; T051+T052+T053 parallel (tests)  
**Phase 7**: T056+T057+T058+T059 parallel (infra); T062+T064 parallel  
**Phase 8**: T067+T068+T069+T070+T071+T072+T073+T074 all parallel (generators); T076 parallel (tests)  
**Phase 9**: T079 parallel with T081  
**Phase 10**: T082+T083+T084+T086+T087+T088 all parallel  

### Implementation Strategy

- **MVP**: Phase 1 + Phase 2 + Phase 3 (US1) — BoM + GA authoritative feeds flowing through the full pipeline with dedup, circuit breaker, storage, and audit
- **Incremental delivery**: Add US2 (fire/SES) → US3 (sensors/satellite) → US4 (social) → US5 (storage polish) → US7 (field reports) → US6 (simulation)
- **Suggested reorder**: US6 (simulation) can be moved earlier after US1 if simulation exercises are a priority for stakeholder demos
