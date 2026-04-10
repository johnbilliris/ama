# Data Model: Data Ingestion Pipelines, Storage Architecture, and Simulation Framework

## Naming Convention

Field names follow the project's established convention: **camelCase** in JSON schemas and API contracts (e.g., `simulationRunId`, `incidentId`, `binaryAssetUri`), **snake_case** in Python Pydantic models (e.g., `simulation_run_id`, `incident_id`). The SignalEnvelope JSON schema uses camelCase; the Signal Pydantic model uses snake_case.

## SignalEnvelope Schema Extensions (FR-002a)

**Purpose**: Extend the existing SignalEnvelope JSON schema and Signal Pydantic model to support simulation provenance.

**Schema change** (`packages/schemas/signal-envelope.schema.json`):
- Add `"simulationRunId": { "type": "string" }` to `provenance.properties`
- `incidentId` already exists at root level — no change needed
- `binaryAssetUri` is stored within `payload` (allows additionalProperties) — no schema change needed

**Pydantic model** (`packages/domain/src/domain/models/signal.py`):
- No structural change needed — `provenance` is already `dict[str, Any]`, so `simulationRunId` is accepted dynamically
- `incident_id` already exists as `str | None`

**Validation rules**:
- `simulationRunId` is optional; present only when `provenance.collectionMethod == "simulation"`
- When `simulationRunId` is present, the signal MUST be stored in a simulation-scoped partition

## IngestionPipelineConfig

**Purpose**: Runtime configuration for a single ingestion pipeline, loaded from environment or configuration file.

**Fields**:
- `pipeline_id`: string, unique identifier (e.g., `bom-warnings`, `nsw-rfs-fire`)
- `source_class`: enum (`authoritative`, `sensor`, `satellite`, `social`, `community`, `field_report`, `ims`)
- `data_source_ids`: list of string, the seed catalogue data source IDs this pipeline handles
- `poll_interval_seconds`: integer, polling cadence (e.g., 60, 300, 600)
- `endpoint_url`: string, the source FTP/HTTP/API endpoint
- `endpoint_format`: enum (`xml_bom`, `geojson`, `json`, `cap_xml`, `rss`, `png`, `geotiff`, `text`)
- `circuit_breaker_threshold`: integer, consecutive failures before tripping (default: 3)
- `circuit_breaker_backoff_initial_seconds`: integer (default: 30)
- `circuit_breaker_backoff_max_seconds`: integer (default: 300)
- `dedup_ttl_seconds`: integer, Redis hash TTL for dedup keys (default: 2× poll_interval)
- `enabled`: boolean (default: true)

**Relationships**:
- References one or more DataSource entries from the seed catalogue via `data_source_ids`
- Used by the pipeline worker to instantiate and configure pipeline instances

## IngestionAuditEntry

**Purpose**: Immutable record of a single ingestion event for the append-only audit trail (FR-028).

**Fields**:
- `audit_id`: string, immutable identifier (UUID)
- `signal_id`: string, the ID of the created SignalEnvelope (null if ingestion failed before signal creation)
- `data_source_id`: string, the seed catalogue data source ID
- `correlation_id`: string (UUID), propagated through all downstream processing
- `timestamp`: datetime, when the ingestion event occurred
- `outcome`: enum (`success`, `rejected`, `failed`, `deduplicated`)
- `validation_errors`: list of string, schema validation error details (empty on success)
- `raw_payload_blob_uri`: string, Azure Blob Storage URI for the raw payload
- `normalisation_latency_ms`: float, time from raw payload receipt to SignalEnvelope persistence
- `pipeline_id`: string, which pipeline instance processed this signal
- `dedup_hash`: string, the content hash computed for deduplication (present even for deduplicated entries)

**Storage**:
- Persisted as JSON Lines in Azure Blob Storage: `audit/ingestion/{YYYY-MM-DD}/{hour}.jsonl`
- Append-only, never modified or deleted

**Validation rules**:
- `correlation_id` is required
- `timestamp` is required
- `outcome=rejected` requires non-empty `validation_errors`
- `outcome=success` requires non-null `signal_id` and `raw_payload_blob_uri`

## CircuitBreakerState

**Purpose**: Tracks the health state of a pipeline's connection to its source, enabling graceful degradation (FR-016).

**Fields**:
- `pipeline_id`: string
- `data_source_id`: string
- `state`: enum (`closed`, `open`, `half_open`)
- `consecutive_failures`: integer
- `last_failure_at`: datetime or null
- `last_success_at`: datetime or null
- `backoff_until`: datetime or null (when the circuit will half-open)
- `total_trips`: integer, cumulative count of circuit breaker activations

**State transitions**:
- `closed` → `open`: when `consecutive_failures >= threshold`
- `open` → `half_open`: when current time > `backoff_until`
- `half_open` → `closed`: on successful poll
- `half_open` → `open`: on failed poll (resets backoff with exponential increase)

**Storage**: In-memory per worker instance (not persisted — resets on restart, which is safe because the circuit breaker re-evaluates on the first poll attempt)

## DedupHashEntry

**Purpose**: Content-hash record for deduplication (FR-018a), stored in Redis.

**Fields**:
- `hash_key`: string, computed as `{dataSourceId}:{canonicalIdentifier}` where canonical identifier is source-specific (e.g., `{productCode}:{issueTimestamp}` for BoM)
- `signal_id`: string, the ID of the signal created from this source product
- `first_seen_at`: datetime, when the hash was first recorded
- `ttl_seconds`: integer, Redis expiry (2× source's expected update frequency)

**Storage**: Redis SET with TTL. Key format: `dedup:{hash_key}`, value: `{signal_id}:{first_seen_at}`

**Validation rules**:
- `hash_key` must be non-empty
- `ttl_seconds` must be > 0

## SimulationScenario

**Purpose**: A configured disaster scenario template for generating synthetic signals (FR-032, FR-038).

**Fields**:
- `scenario_id`: string, immutable identifier
- `name`: string, human-readable name (e.g., "Blue Mountains Bushfire 2024")
- `scenario_type`: enum (`bushfire`, `flood`, `cyclone`, `severe_storm`)
- `target_region`: GeoJSON Polygon, the geographic area for the simulation
- `target_jurisdiction_ids`: list of string, jurisdictions affected
- `activated_data_source_ids`: list of string, subset of seed catalogue sources to simulate
- `time_compression_ratio`: float, ratio for temporal compression (e.g., 24.0 compresses 24 hours into 1 hour)
- `event_phases`: list of EventPhase objects (ordered)
- `misinformation_ratio`: float 0–1, proportion of social media signals that are misinformation (default: 0.15)
- `historical_overlay_path`: string or null, path to historical event dataset file for replay
- `created_by`: string, persona ID of the planner
- `created_at`: datetime

**EventPhase** (embedded object):
- `phase_name`: string (e.g., "detection", "escalation", "peak", "de-escalation")
- `phase_order`: integer, 1-based
- `duration_minutes`: integer, real-time duration of this phase after compression
- `data_sources_active`: list of string, which sources produce signals in this phase
- `escalation_triggers`: list of string, conditions that advance to the next phase (e.g., "river_gauge > major_threshold")
- `signal_generation_params`: dict, per-source parametric model parameters (e.g., `{"fire_ffdi": 75, "wind_speed_kmh": 40}`)

**Relationships**:
- Referenced by SimulationRun
- References DataSource entries from the seed catalogue
- References Jurisdiction entries for geographic scoping

**Validation rules**:
- `scenario_type` must be one of the 4 defined values
- `target_region` must be a valid GeoJSON Polygon
- `activated_data_source_ids` must all exist in the seed catalogue
- `event_phases` must contain at least one phase
- `time_compression_ratio` must be > 0
- `misinformation_ratio` must be 0–1

## SimulationRun

**Purpose**: An execution instance of a SimulationScenario (FR-039).

**Fields**:
- `run_id`: string, immutable identifier (UUID)
- `scenario_id`: string, reference to SimulationScenario
- `status`: enum (`configuring`, `running`, `completed`, `aborted`)
- `started_at`: datetime or null
- `completed_at`: datetime or null
- `current_phase`: string, name of the active event phase
- `signals_generated`: dict of `{data_source_id: count}`, per-source signal counts
- `total_signals`: integer, cumulative count
- `time_compression_ratio`: float, effective compression (may differ from scenario default)
- `misinformation_ratio`: float, effective ratio for this run
- `created_by`: string, persona ID
- `created_at`: datetime

**State transitions**:
- `configuring` → `running`: when the simulation runner starts signal generation
- `running` → `completed`: when all phases complete or the scenario timeline elapses
- `running` → `aborted`: when a planner aborts the simulation
- `configuring` → `aborted`: when cancelled before starting

**Relationships**:
- References one SimulationScenario
- Generates signals stored in `sim_{run_id}` partition scope

**Validation rules**:
- `scenario_id` must reference an existing SimulationScenario
- `status` transitions follow the defined state machine
- `signals_generated` keys must be valid data source IDs

## Entity Relationship Summary

```
DataSource (from seed catalogue)
    ├── referenced by IngestionPipelineConfig.data_source_ids (1..*)
    ├── referenced by SimulationScenario.activated_data_source_ids (1..*)
    ├── referenced by IngestionAuditEntry.data_source_id (1..*)
    └── referenced by DedupHashEntry.hash_key prefix (1..*)

Signal (existing, extended)
    ├── one IngestionAuditEntry per signal
    ├── one raw payload blob per signal
    ├── optional binary asset blob (radar/satellite)
    └── optional SimulationRun reference via provenance.simulationRunId

SimulationScenario (1) ──── (0..*) SimulationRun
SimulationRun.run_id ──── Signal.provenance.simulationRunId (scope marker)

IngestionPipelineConfig ──── CircuitBreakerState (1:1 per source)
```

## Cosmos DB Container Design

### `signals` container
- **Hierarchical partition key**: `/scope/jurisdictionId/dataSourceId`
- **Scope values**: `live` for operational; `sim_{runId}` for simulation
- **Index policy**: Composite index on `(jurisdictionId, category, occurredAt DESC)` for dashboard queries
- **TTL**: None (signals retained indefinitely; future retention policy feature)
- **Estimated RU**: 1000 RU/s autoscale (baseline), burst to 4000 RU/s during multi-incident events

### `simulation` container
- **Partition key**: `/scenario_id`
- **Stores**: SimulationScenario and SimulationRun documents
- **Estimated RU**: 400 RU/s autoscale

## Azure Blob Storage Container Design

| Container | Path Structure | Content | Lifecycle |
|-----------|---------------|---------|-----------|
| `raw-payloads` | `{dataSourceId}/{YYYY-MM-DD}/{signalId}.{format}` | Raw unmodified source payloads | Retained for audit |
| `binary-assets` | `{incidentId}/{dataSourceId}/{timestamp}.{format}` | Radar PNG, satellite GeoTIFF (active incidents only) | Retained per incident |
| `binary-assets` | `_on-demand/{dataSourceId}/{timestamp}.{format}` | On-demand retrieved binaries | 30-day TTL |
| `audit` | `ingestion/{YYYY-MM-DD}/{hour}.jsonl` | IngestionAuditEntry JSON Lines | Append-only, immutable |
| `simulation` | `{simulationRunId}/raw/{signalId}.{format}` | Simulation raw payloads | Retained per run |
