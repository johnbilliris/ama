# Quickstart: Data Ingestion Pipelines, Storage Architecture, and Simulation Framework

## Phase A — Schema Extension & Foundation (test-first)

### A1. Extend SignalEnvelope schema
1. Add `simulationRunId` to `provenance.properties` in `packages/schemas/signal-envelope.schema.json`
2. Write contract test: validate that a SignalEnvelope with `provenance.simulationRunId` passes schema validation
3. Write contract test: validate that a SignalEnvelope without `simulationRunId` still passes (backward compatibility)
4. Verify existing tests still pass (no regression)

### A2. Create domain models
1. Create `IngestionAuditEntry` Pydantic model in `packages/domain/src/domain/models/ingestion_audit.py`
2. Create `SimulationScenario` Pydantic model in `packages/domain/src/domain/models/simulation_scenario.py`
3. Create `SimulationRun` Pydantic model in `packages/domain/src/domain/models/simulation_run.py`
4. Write unit tests for each model's validation rules and state transitions

## Phase B — Pipeline Framework (test-first)

### B1. Base pipeline class
1. Create `apps/ingestion/worker.py` — pipeline worker lifecycle manager
2. Create `apps/api/app/services/ingestion/pipeline_base.py` — `IngestionPipelineBase` with:
   - Polling loop with configurable interval
   - Circuit breaker (3 failures → trip → exponential backoff → half-open)
   - Content-hash deduplication via Redis lookup
   - Raw payload storage to Blob
   - SignalEnvelope schema validation
   - Incident association at ingestion time (FR-019a)
   - Audit entry creation
   - Observability metric emission
3. Write contract tests for circuit breaker state transitions
4. Write contract tests for dedup hash computation and skip logic
5. Write integration test for full pipeline lifecycle (poll → normalise → validate → store → audit)

### B2. Dedup service
1. Create `apps/api/app/services/ingestion/dedup_service.py` — Redis-backed content hash lookup
2. Write contract test: hash hit returns existing signal ID, ingestion skipped
3. Write contract test: hash miss allows ingestion, writes hash with TTL
4. Write contract test: expired hash allows re-ingestion

### B3. Incident association service
1. Create `apps/api/app/services/ingestion/incident_association.py` — match signal location/jurisdiction to active incidents
2. Write contract test: signal in active incident area gets `incidentId` set
3. Write contract test: signal outside any incident gets `incidentId=null`
4. Write contract test: national signal matching multiple incidents creates fan-out records

## Phase C — Source-Specific Normalisers (test-first)

### C1. BoM XML normaliser
1. Create `apps/ingestion/normalisers/bom_xml_normaliser.py` — parse BoM product XML (XSD v1.7) to SignalEnvelope
2. Write contract test with sample BoM warning XML → verify correct `category`, `source.kind`, `confidenceScore`, `provenance`
3. Write contract test with sample BoM forecast XML → verify different signal properties

### C2. GeoJSON normaliser
1. Create `apps/ingestion/normalisers/geojson_normaliser.py` — parse GeoJSON FeatureCollection to SignalEnvelopes
2. Write contract test with NSW RFS GeoJSON sample → verify `category=fire`, `alertLevel` mapping to confidence, geometry preservation
3. Write contract test with GA earthquake GeoJSON → verify `category=geohazard`, Point location

### C3. JSON observation normaliser
1. Create `apps/ingestion/normalisers/json_observation_normaliser.py` — parse BoM JSON observations, river gauges, EPA data
2. Write contract test with BoM AWS observation sample → verify sensor range validation
3. Write contract test with river gauge reading exceeding flood threshold → verify elevated confidence

### C4. CAP normaliser
1. Create `apps/ingestion/normalisers/cap_normaliser.py` — parse Common Alerting Protocol XML
2. Write contract test with BoM flood warning CAP → verify correct category and urgency mapping

### C5. Binary metadata normaliser
1. Create `apps/ingestion/normalisers/binary_metadata_normaliser.py` — create metadata-only SignalEnvelope for radar/satellite
2. Write contract test: no active incident → metadata-only envelope with source URI, no binary download
3. Write contract test: active incident in radar coverage → full binary download, blob URI in payload

## Phase D — Individual Pipelines (test-first)

### D1. Authoritative pipelines
1. Create `apps/ingestion/pipelines/bom_warnings.py` — BoM FTP warning pipeline using BoM XML normaliser
2. Create `apps/ingestion/pipelines/bom_observations.py` — BoM observation pipeline using JSON normaliser
3. Create `apps/ingestion/pipelines/bom_radar.py` — BoM radar pipeline using binary metadata normaliser
4. Create `apps/ingestion/pipelines/ga_earthquakes.py` — GA earthquake pipeline using GeoJSON normaliser
5. Create `apps/ingestion/pipelines/ga_hotspots.py` — GA hotspot pipeline using GeoJSON normaliser
6. Write integration tests for each pipeline with mocked source endpoints

### D2. Fire and SES pipelines
1. Create `apps/ingestion/pipelines/fire_service.py` — parameterised for NSW RFS, VIC CFA, QLD QFES, etc.
2. Create `apps/ingestion/pipelines/ses_flood.py` — parameterised for NSW/VIC/QLD SES
3. Write integration tests with state-specific GeoJSON format samples

### D3. Sensor pipelines
1. Create `apps/ingestion/pipelines/sensor_aws.py` — BoM AWS stations
2. Create `apps/ingestion/pipelines/sensor_river_gauge.py` — river gauge networks
3. Create `apps/ingestion/pipelines/sensor_epa_air.py` — EPA air quality
4. Write contract tests for sensor range validation (reject implausible, flag anomalous)

### D4. Satellite pipelines
1. Create `apps/ingestion/pipelines/satellite_sentinel.py` — Copernicus Sentinel
2. Create `apps/ingestion/pipelines/satellite_himawari.py` — Himawari via BoM FTP
3. Write integration test: verify metadata-only mode and incident-triggered download mode

### D5. Social media and community pipelines
1. Create `apps/ingestion/pipelines/social_twitter.py` — X API v2 filtered stream
2. Create `apps/ingestion/pipelines/social_facebook.py` — Meta Graph API
3. Create `apps/ingestion/pipelines/social_reddit.py` — Reddit JSON API
4. Create `apps/ingestion/pipelines/community_snap.py` — Snap Send Solve
5. Write contract tests for trust tier assignment and confidence scoring

### D6. Field report and IMS pipelines
1. Create `apps/ingestion/pipelines/ims_webeoc.py` — WebEOC + ICON IMS
2. Write contract tests for field report normalisation via `POST /signals`

## Phase E — Misinformation Detection (test-first)

### E1. Tier 1 rule-based heuristics
1. Create `apps/api/app/services/ingestion/misinformation_detector.py`
2. Write contract test: burst detection — 20+ posts same topic in 10 min → `validationStatus=escalated`
3. Write contract test: contradiction — social signal with no matching authoritative signal → reduced confidence
4. Write contract test: duplicate amplification — cosine similarity >0.9 within 5 min → earliest retained, duplicates escalated

### E2. Tier 2 LLM analysis (Monitoring Agent)
1. Modify `apps/agents/monitoring/agent.py` — add method to evaluate escalated social signals via LLM
2. Write contract test: LLM classifies as misinformation → `validationStatus=rejected`, not forwarded
3. Write contract test: LLM unavailable → signal stays escalated, not forwarded (safe degradation)

## Phase F — Storage Layer (test-first)

### F1. Cosmos DB signal repository
1. Create `apps/api/app/repositories/signal_repository.py` — Cosmos DB CRUD with hierarchical partition key
2. Write contract test: signal stored with correct partition key `{scope}/{jurisdictionId}/{dataSourceId}`
3. Write contract test: national signal creates fan-out reference in each affected jurisdiction partition
4. Write contract test: simulation signal stored in `sim-{runId}` scope, invisible to live queries
5. Write contract test: dashboard query within ≤500ms p95 against sample dataset

### F2. Blob storage for raw payloads and audit
1. Create raw payload storage helper — store under `raw-payloads/{dataSourceId}/{YYYY-MM-DD}/{signalId}.{format}`
2. Create audit trail writer — append to `audit/ingestion/{YYYY-MM-DD}/{hour}.jsonl`
3. Create binary asset storage — store under `binary-assets/{incidentId}/{dataSourceId}/{timestamp}.{format}`
4. Write integration test: every ingested signal has corresponding raw payload blob and audit entry (SC-007)

### F3. Retrospective incident association (Monitoring Agent)
1. Modify `apps/agents/monitoring/agent.py` — add retrospective scan on incident declaration
2. Write contract test: new incident declared → signals with `incidentId=null` matching jurisdiction/location updated
3. Write contract test: lookback window configurable (default 24h)

## Phase G — Simulation Framework (test-first)

### G1. Simulation runner
1. Create `apps/ingestion/simulation/simulation_runner.py` — scenario orchestrator
2. Create `apps/ingestion/simulation/scenario_templates.py` — 4 scenario type definitions
3. Write integration test: start a bushfire simulation → signals generated for all activated sources

### G2. Parametric generators
1. Create `apps/ingestion/simulation/generators/flood_generator.py` — hydrograph curve model
2. Create `apps/ingestion/simulation/generators/fire_generator.py` — FFDI-based fire spread
3. Create `apps/ingestion/simulation/generators/cyclone_generator.py` — cyclone track model
4. Create `apps/ingestion/simulation/generators/sensor_generator.py` — plausible sensor readings
5. Create `apps/ingestion/simulation/generators/weather_generator.py` — BoM warning/forecast signals
6. Create `apps/ingestion/simulation/generators/social_generator.py` — social media with misinformation mix
7. Write contract tests for each: output passes SignalEnvelope schema validation (SC-006)

### G3. Historical overlay
1. Create `apps/ingestion/simulation/generators/historical_overlay.py` — replay with perturbation
2. Write integration test: historical event dataset replayed with shifted location and timing

### G4. Concurrent simulation + live
1. Write integration test: simulation and live ingestion running simultaneously, no cross-contamination (SC-009)
2. Write integration test: 3 concurrent simulation runs + live, throughput ≥ 50,000 signals/hour (FR-037a)

## Phase H — API Routes & Observability (test-first)

### H1. Simulation API routes
1. Add `POST /simulations/scenarios`, `GET /simulations/scenarios`, `POST /simulations/runs`, `GET /simulations/runs/{runId}`, `POST /simulations/runs/{runId}/abort` to API router
2. Write contract tests for each endpoint against the OpenAPI contract

### H2. Pipeline status endpoint
1. Add `GET /ingestion/status` — aggregated pipeline health
2. Write contract test: returns pipeline states, throughput, dedup rates, dead-letter depth

### H3. Extended signal query filters
1. Modify `GET /signals` — add `jurisdictionId`, `category`, `dataSourceId`, `since`, `validationStatus`, `limit`, `offset` parameters
2. Write contract test: filtered queries return correct subsets

## Phase I — Infrastructure (Bicep)

### I1. Cosmos DB containers
1. Add `signals` container with hierarchical partition key to `infra/bicep/main.bicep`
2. Add `simulation` container with partition key `/scenario_id`

### I2. Ingestion worker Container App
1. Add ingestion worker Container App (internal ingress, 1-6 replicas, system managed identity)
2. Configure KEDA scaling rules for CPU and queue depth

### I3. Blob containers
1. Add `raw-payloads`, `binary-assets`, `audit`, `simulation` blob containers

## Verification Checklist

- [ ] All existing tests pass (no regression from schema extension)
- [ ] BoM XML/CAP normaliser handles product XSD v1.7 format correctly
- [ ] GeoJSON normaliser maps NSW RFS properties (title, category, status, alertLevel) correctly
- [ ] Circuit breaker trips after 3 failures, recovers on successful half-open poll
- [ ] Dedup prevents re-ingestion of unchanged BoM warnings across 60-second polling cycles
- [ ] National signals discoverable from jurisdiction-scoped dashboard queries
- [ ] Simulation signals fully isolated from live queries (SC-009)
- [ ] Each simulated signal passes same schema validation as real signals (SC-006)
- [ ] Audit trail has 100% correlation with persisted signals (SC-007)
- [ ] Misinformation Tier 1 heuristics flag burst/contradiction/amplification patterns correctly
- [ ] Monitoring Agent Tier 2 LLM evaluates flagged social signals before forwarding
