# Research: Data Ingestion Pipelines, Storage Architecture, and Simulation Framework

## Decision: Use Cosmos DB as the hot operational signal store with Azure Blob Storage for raw payloads and binary assets

**Rationale**: The existing architecture provisions Cosmos DB (GlobalDocumentDB) in Australia East with the in-memory state store (`state_store.py`) as a development placeholder. Cosmos DB remains appropriate for the hot operational signal store because: (1) signals must be queryable by jurisdiction, incident, category, time range — all point-read and range-query patterns Cosmos DB excels at; (2) the existing codebase (cosmos_scope.py, tenant_partitioning.py) already implements partition key logic; (3) the ≤500ms p95 dashboard query target (SC-004) aligns with Cosmos DB's single-partition point read SLA; (4) 50,000 signals/hour (~14 signals/second) is well within Cosmos DB's capacity at moderate RU provisioning. Azure Blob Storage handles raw payloads, binary assets (radar, satellite), and the append-only audit trail — consistent with the existing architecture's use of Blob for audit artifacts.

**Data-Engineer Agent Review (Q7 resolution)**: The data-engineer agent's responsibilities include Cosmos DB container design, partition key strategy, and Event Hubs configuration. The following decisions are captured with data-engineer agent input:
- **Cosmos DB is appropriate** at the projected 50k signals/hour volume. Autoscale RUs handle burst during multi-incident scenarios. The 20GB logical partition limit is manageable with the chosen partition key strategy (see below).
- **OneLake/Fabric**: Not needed for initial delivery. Historical signal analysis across months of data can be addressed by a future analytical export pipeline using Cosmos DB change feed → OneLake. This is out of scope for this feature.
- **Azure Data Explorer (Kusto)**: Not needed for initial delivery. The existing Log Analytics workspace (provisioned in monitoring.bicep) can serve time-series anomaly detection needs using KQL. Full ADX cluster is warranted only when signal volume exceeds Cosmos DB cost-effectiveness, estimated at >500k signals/hour sustained.
- **Polyglot approach deferred**: The initial architecture uses Cosmos DB + Blob Storage only. A change-feed-based export to a cooler analytical tier can be added later without changing the ingestion layer.

**Alternatives considered**:

- Azure Data Explorer as primary signal store: rejected because it optimises for analytical queries and time-series append patterns, not the mixed read-write operational patterns needed for incident dashboards and agent handoff queries. ADX's ingestion latency (typically minutes) would not meet the ≤90s SC-001 target.
- Azure Blob Storage with search index as primary store: rejected because it lacks the query flexibility needed for real-time dashboard aggregation (filter by jurisdiction + incident + category + time range simultaneously). Azure Cognitive Search could overlay Blob but adds complexity and latency.
- OneLake as primary store: rejected because OneLake (Fabric) is optimised for analytical lakehouses, not low-latency operational workloads. Ingestion latency and query patterns don't match the ≤500ms p95 requirement.

## Decision: Use hierarchical partition key for signal storage with jurisdiction-scoped fan-out for national signals

**Rationale**: National signals (BoM national warnings, GA earthquake alerts) must be discoverable by jurisdiction-scoped dashboard queries. Cosmos DB hierarchical partition keys (3 levels: scope/jurisdictionId/dataSourceId) enable efficient container management while supporting both national-scope and jurisdiction-scope queries. National signals are stored with `scope=national` and fan-out records created for each affected jurisdiction's partition at ingestion time. This ensures that a NSW dashboard query returns all NSW-relevant signals (both NSW-specific and national) from a single logical partition without cross-partition queries.

**Partition key design**:
- Level 1: `scope` — values: `live`, `sim-{runId}` (simulation isolation per FR-029)
- Level 2: `jurisdictionId` — values: `national`, `nsw`, `vic`, `qld`, `sa`, `wa`, `tas`, `nt`, `act`
- Level 3: `dataSourceId` — values: the data source identifier from the seed catalogue

For national signals, the ingestion pipeline creates the primary record in the `national` partition AND fan-out reference records in each affected jurisdiction partition. Fan-out records are lightweight (signal ID + reference to the `national` record) to minimise storage duplication. Dashboard queries hit a single jurisdiction partition and use a `UNION` with the `national` partition via a stored procedure or application-level query combiner.

**Alternatives considered**:

- Single-level `{jurisdictionId}_{organisationId}` partition key (original FR-025): rejected because national signals have no single jurisdiction, creating a hot partition problem and requiring expensive cross-partition queries for jurisdiction-scoped dashboards.
- Full signal replication to every jurisdiction partition: rejected because it multiplies storage by 8× for every national signal and creates write amplification during high-volume events.
- Cross-partition queries at read time: rejected because Cosmos DB cross-partition queries are significantly more expensive in RU consumption and latency, violating the ≤500ms p95 target.

## Decision: Extend SignalEnvelope schema with `simulationRunId` in provenance only; `incidentId` already exists

**Rationale**: Code review reveals the SignalEnvelope JSON schema already includes `incidentId` as an optional string at root level, and the Signal Pydantic model already has `incident_id`. The only schema extension needed is adding `simulationRunId` to the `provenance` object. Since provenance currently has `additionalProperties: false`, this requires a targeted schema change. The `binaryAssetUri` field naturally fits within `payload` (which allows additionalProperties).

**Changes required**:
- `signal-envelope.schema.json`: Add `"simulationRunId": { "type": "string" }` to `provenance.properties`. No change needed for `incidentId` (already present) or `binaryAssetUri` (goes in payload).
- `signal.py` Pydantic model: No changes needed — `provenance` is already `dict[str, Any]`, so `simulationRunId` is accepted.
- `signal_envelope.py` validator: No changes needed — `provenance` is already `dict[str, Any]`.

**Alternatives considered**:

- Adding `simulationRunId` at root level: rejected because it's a provenance attribute (how the signal was collected), not a signal characteristic. Keeping it in provenance maintains semantic consistency.
- Changing provenance to allow additionalProperties: rejected because explicit schema fields with documentation are more discoverable and validate at ingestion time.

## Decision: Content-hash deduplication using Redis with source-specific canonical keys

**Rationale**: Polling-based pipelines re-encounter the same source products on every poll cycle (BoM FTP products persist 8-36 hours, fire service GeoJSON returns all current incidents). Content-hash deduplication prevents redundant signal creation. Redis (already provisioned in the infrastructure) provides a fast, ephemeral hash lookup with configurable TTL. The hash key is computed from the source-specific canonical identifier:
- BoM warnings: `{productId}:{issueTimestamp}`
- GeoJSON features: `{featureId}:{lastUpdated}`
- Sensor observations: `{stationId}:{observationTimestamp}`
- Social media: `{platform}:{postId}`

Hash entries expire after 2× the source's FTP delete-time or expected update frequency (e.g., 72 hours for BoM warnings, 20 minutes for sensor observations). This bounds Redis memory usage.

**Alternatives considered**:

- Deduplication against Cosmos DB point reads: rejected because each check would consume RUs and add latency to every poll cycle. Redis provides sub-millisecond lookups at no RU cost.
- Local in-memory hash sets per pipeline worker: rejected because Container App scale-out creates multiple worker instances that wouldn't share dedup state, allowing duplicates across instances.

## Decision: Use a base pipeline class with strategy pattern for source-specific normalisation

**Rationale**: All 20+ pipelines share identical lifecycle concerns: polling loop, circuit breaker, deduplication, raw payload storage, SignalEnvelope validation, incident association, audit logging, and observability. Only the normalisation step (converting source-specific formats to SignalEnvelope) varies. A base `IngestionPipelineBase` class implements the shared lifecycle; each source provides a `normalise(raw_payload) → SignalEnvelope` method. This eliminates code duplication across 20+ pipelines and ensures consistent behaviour for FR-016 (circuit breaker), FR-018a (dedup), FR-018b (observability), FR-019a (incident association).

**Alternatives considered**:

- Fully independent pipeline implementations per source: rejected because it would duplicate ~200 lines of lifecycle code across 20+ files, creating maintenance burden and inconsistency risk.
- Function-based composition: rejected because the lifecycle has stateful concerns (circuit breaker state, poll timing, error count) that benefit from object encapsulation.

## Decision: Simulation framework as a specialised signal generator with same-pipeline injection

**Rationale**: FR-037 and FR-037a require simulated signals to flow through the same ingestion pipelines as real signals. The simulation runner generates synthetic source payloads and submits them to the same normalisation pipeline, with `provenance.collectionMethod=simulation` and `provenance.simulationRunId` set. This ensures simulated signals pass identical schema validation, deduplication (skipped for simulation), and incident association logic. Simulation isolation is enforced at the storage partition level via the `sim-{runId}` scope prefix.

**Alternatives considered**:

- Separate simulation pipeline that creates SignalEnvelopes directly: rejected because it would bypass normalisation validation and diverge from real signal processing, making SC-006 (structural indistinguishability) untestable.
- Simulation as a replay of pre-generated signal files: rejected because it doesn't support configurable time compression, geographic targeting, or parametric generation with runtime parameters.

## Decision: Tiered misinformation detection with rule-based heuristics at ingestion and LLM evaluation at Monitoring Agent

**Rationale**: The ingestion pipeline applies fast, deterministic checks (burst volume, contradiction with authoritative sources, duplicate text amplification) that run in <10ms per signal. Flagged signals are marked `validationStatus=escalated` and forwarded to the Monitoring Agent, which applies its existing LLM integration for deeper analysis on the flagged subset only. This bounds LLM token cost to ~15% of social media signals (the expected flag rate) while providing sub-second ingestion latency.

**Alternatives considered**:

- LLM analysis on all social signals at ingestion time: rejected because it would add 1-3 seconds per signal, blow token budgets, and create a bottleneck in the social media pipeline during high-volume events.
- Rule-based only with no LLM tier: rejected because sophisticated misinformation (e.g., plausible-sounding false reports with correct geography) requires semantic understanding beyond pattern matching.

## Decision: Background workers in Azure Container Apps with per-class scaling

**Rationale**: The existing architecture uses Azure Container Apps for API and agents. Adding a third Container App for ingestion workers (internal ingress, 1-6 replicas) maintains architectural consistency. Each pipeline class runs as a separate async task within the worker process, managed by a supervision loop. Container Apps KEDA-based scaling monitors queue depth (dead-letter queue + signal processing backlog) and CPU utilisation to scale replicas. Graceful shutdown completes in-progress polling cycles before termination.

**Alternatives considered**:

- Azure Functions with timer triggers: rejected because cold-start latency (up to 10s on Consumption plan) would miss the 60-second polling interval for BoM warnings, and the 10-minute execution limit conflicts with potential satellite imagery download times.
- Dedicated VM worker pool: rejected because it adds infrastructure management overhead not justified at this scale, and Container Apps provide sufficient auto-scaling automation.

## Decision: Radar and satellite imagery uses hybrid metadata-only with incident-triggered download (FR-009a)

**Rationale**: BoM operates ~80 radar stations producing images every 5 minutes (~960 images/hour). Himawari-9 produces full-disk images every 10 minutes. Downloading and storing all nationally would generate terabytes of blob storage. The hybrid approach stores metadata-only references by default and triggers full binary download only for stations within/adjacent to active incidents (50km buffer). This reduces storage to ~5-10% of the full-download scenario while retaining all operationally relevant imagery. On-demand retrieval provides access to any metadata reference for up to 8-36 hours (BoM FTP delete window).

**Alternatives considered**:

- Full national download always: rejected due to projected storage cost (~2-5TB/month for radar alone) with no operational benefit for imagery distant from active incidents.
- Metadata-only always (no auto-download): rejected because it adds retrieval latency during active incidents when analysts need immediate access to radar and satellite imagery.
