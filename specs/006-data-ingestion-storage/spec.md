# Feature Specification: Data Ingestion Pipelines, Storage Architecture, and Simulation Framework

**Feature Branch**: `006-data-ingestion-storage`  
**Created**: 2026-03-25  
**Status**: Draft  
**Input**: User description: "For all the identified sources of data for the solution; determine the data ingestion and storage approaches for them. Cross-reference the Constitution for the co-operating agents are involved and how they will interact with the data. Verify each data source with the source organisation's technical documentation. Each data source also requires the ingestion to be simulated in order for the solution to provide the simulation functionality. Each data simulator needs to generate all necessary data that realistically mimics the source data AND meet the simulation objective."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ingest authoritative weather and hazard feeds in near-real-time (Priority: P1)

The Monitoring Agent receives a continuous stream of weather warnings, forecasts, observations, radar imagery, flood warnings, and geohazard alerts from Bureau of Meteorology and Geoscience Australia feeds. Each ingested item is normalised into a SignalEnvelope, enriched with provenance and freshness metadata, validated against the signal-envelope schema, and persisted to the signal store. The Monitoring Agent classifies each signal by category and, when a high-confidence hazard signal is detected for an active incident, builds a typed handoff to the Risk Assessment Agent. The system retains raw payloads for audit and reproducibility.

**Why this priority**: Authoritative government feeds are Tier 1 trust sources. The hub's core value proposition — timely hazard awareness and coordinated response — depends on reliable, low-latency ingestion of these feeds. The Constitution (Principle III) mandates preferring authoritative sources for safety-critical decisions.

**Independent Test**: Can be tested by connecting to the BoM anonymous FTP/HTTP data feeds (XML warnings via the AMOC/product XSD schema, JSON observations, radar PNGs) and the GA earthquake GeoJSON API, verifying that signals arrive within the expected latency, are normalised correctly, carry correct provenance, and trigger handoffs to Risk Assessment when thresholds are met.

**Acceptance Scenarios**:

1. **Given** the BoM warnings FTP endpoint publishes a new severe thunderstorm warning in CAP/XML format for NSW, **When** the ingestion pipeline polls the feed, **Then** the system normalises the warning into a SignalEnvelope with `category=weather`, `source.kind=authoritative`, confidence derived from the source trust tier, and persists it within 60 seconds of publication.
2. **Given** the BoM automatic weather station network publishes a 10-minute JSON observation update, **When** the sensor ingestion pipeline receives the update, **Then** the system creates a SignalEnvelope with `category=weather`, `source.kind=sensor`, and attaches provenance including the station identifier, collection method (`sensor_network`), and source timestamp.
3. **Given** a Geoscience Australia earthquake alert is published as GeoJSON via their web service, **When** the ingestion pipeline retrieves it, **Then** the system normalises it to a SignalEnvelope with `category=geohazard`, location as a GeoJSON Point, and `trust_tier=tier_1_authoritative_government`.
4. **Given** the ingested signal has `category in {fire, weather, hydrology}`, `confidenceScore >= 0.8`, and an active incident exists in the affected jurisdiction, **When** the Monitoring Agent classifies it, **Then** it builds a handoff to the Risk Assessment Agent with the signal summary, category, source kind, and confidence score.
5. **Given** any ingestion pipeline fails to retrieve data from a source for longer than three consecutive polling intervals, **When** the circuit breaker trips, **Then** the system marks the data source as `degraded`, emits a structured warning log, and the dashboard shows the degraded source indicator per FR-014 of spec 001.

---

### User Story 2 - Ingest fire service incident feeds from all states and territories (Priority: P2)

The ingestion layer pulls current incident data from each state and territory fire service (NSW RFS GeoJSON feed, VIC CFA, QLD QFES, SA CFS, WA DFES, TAS TFS, ACT ESA, NT PFES) and SES flood intelligence feeds. Each feed has its own format, update cadence, and geographic scope. The system normalises all of these into a common SignalEnvelope format so that downstream agents operate on a uniform signal stream regardless of which state the incident is in.

**Why this priority**: State fire and SES services are the ground-truth sources for fire and flood incidents within their jurisdictions. Without ingesting these feeds, the hub cannot provide a national picture of active incidents.

**Independent Test**: Can be tested by configuring the NSW RFS GeoJSON feed connector, verifying that incident features (with properties: title, category, type, status, alert level, geometry) are correctly mapped to SignalEnvelope fields, and that the same normalisation produces correct output for a VIC CFA feed with its own property naming conventions.

**Acceptance Scenarios**:

1. **Given** the NSW RFS publishes current incidents as a GeoJSON FeatureCollection (available in GeoJSON, GeoRSS, and CAP formats), **When** the ingestion pipeline polls the feed, **Then** each Feature is mapped to a SignalEnvelope with `category=fire`, `source.dataSourceId=nsw-rfs-fires-near-me`, alert level mapped to confidence score, and geometry preserved as the signal location.
2. **Given** a state SES flood intelligence feed (e.g., NSW SES) publishes a flood event update, **When** the ingestion pipeline processes it, **Then** the system creates a SignalEnvelope with `category=hydrology`, correct jurisdiction, and `trust_tier=tier_1_authoritative_government`.
3. **Given** a fire service feed from one state uses different property names or data types than another state, **When** both are ingested, **Then** the normalised SignalEnvelopes are structurally identical and downstream agents process them uniformly.

---

### User Story 3 - Ingest and validate sensor, IoT, and satellite data (Priority: P3)

The sensor ingestion pipeline receives data from BoM automatic weather stations (JSON observations, 5-to-10-minute cadence), river gauge networks (real-time JSON), state EPA air quality sensors (hourly JSON), Sentinel satellite imagery (daily GeoTIFF), and Himawari-8/9 satellite imagery (10-minute JPG/GeoTIFF). Sensor data is validated for range plausibility and freshness before normalisation. Satellite imagery is stored as binary blobs with metadata references in the signal store.

**Why this priority**: Sensor and satellite data provide the physical ground truth for hazard assessments. The Risk Assessment Agent depends on sensor data to generate hazard maps and impact predictions.

**Independent Test**: Can be tested by feeding sample BoM AWS JSON observation records into the pipeline, verifying range validation (e.g., temperature between -20°C and 55°C, wind speed ≥ 0), freshness scoring, and correct SignalEnvelope creation. Satellite imagery ingestion is tested by verifying binary blob storage and metadata indexing.

**Acceptance Scenarios**:

1. **Given** a BoM automatic weather station publishes a JSON observation with temperature, humidity, wind speed, and pressure fields, **When** the sensor pipeline ingests it, **Then** each measurement is range-validated, the observation is normalised to a SignalEnvelope with `category=weather`, `source.kind=sensor`, and a freshness score computed from the time delta between observation timestamp and ingestion time.
2. **Given** a river gauge reading arrives with a water level exceeding the configured minor flood threshold for that gauge, **When** the pipeline processes it, **Then** the signal is created with `category=hydrology` and elevated confidence, and the Monitoring Agent evaluates it for handoff to Risk Assessment.
3. **Given** a Himawari-9 satellite image product is available as a GeoTIFF from the BoM FTP service, **When** the pipeline processes it, **Then** if an active incident's area overlaps the image coverage, the binary image is downloaded and stored in Azure Blob Storage under the incident-prefixed path, and a SignalEnvelope referencing the stored blob URI is created. If no active incident overlaps, only a metadata-only SignalEnvelope is created (recording the source URI, timestamp, and coverage area) without downloading the binary.
4. **Given** a sensor reading fails range validation (e.g., temperature of 150°C), **When** the pipeline validates it, **Then** the signal is created with `validationStatus=rejected`, a low confidence score, and a provenance note explaining the rejection reason.

---

### User Story 4 - Ingest social media and community reports with trust scoring (Priority: P4)

The social media ingestion pipeline monitors X/Twitter disaster hashtags, Facebook community groups, and Reddit Australian subreddits for disaster-relevant posts. Community reporting platforms (Snap Send Solve, volunteer organisation feeds) are also ingested. All social and community content receives a Tier 5-6 trust classification and is subject to misinformation detection heuristics. Ingestion complies with each platform's API terms of service and rate limits.

**Why this priority**: Social media provides early community intelligence that may precede official warnings. However, it carries high misinformation risk. The Constitution (Principle III) requires that social/unverified inputs be explicitly flagged and not used as the sole basis for safety-critical decisions.

**Independent Test**: Can be tested by feeding sample social media posts through the pipeline, verifying that trust tiers are correctly assigned, misinformation heuristics flag suspicious content, and downstream agents receive signals with the appropriate low-confidence markers.

**Acceptance Scenarios**:

1. **Given** a tweet matching a disaster hashtag is detected via the X/Twitter API, **When** the social media pipeline ingests it, **Then** a SignalEnvelope is created with `source.kind=social`, `trust_tier=tier_6_social_unverified`, `category` inferred from content analysis, and `validationStatus=pending`.
2. **Given** a community volunteer report from Snap Send Solve contains a geotagged photo of a road closure, **When** the community pipeline ingests it, **Then** a SignalEnvelope is created with `source.kind=community`, `trust_tier=tier_5_community_volunteer`, location from the geotag, and `category=infrastructure`.
3. **Given** a burst of social media posts repeats unverified claims about a non-existent hazard, **When** the misinformation detection heuristic flags the burst, **Then** affected signals are marked with `validationStatus=escalated` and confidence is reduced, and the Monitoring Agent does not forward them for risk assessment without human review.

---

### User Story 5 - Store ingested signals with multi-tenant partitioning and audit trail (Priority: P5)

All normalised signals, raw payloads, binary assets, and ingestion metadata are stored in the hub's data platform. Signals are partitioned by tenant scope (jurisdiction + agency) in Cosmos DB. Raw payloads and binary assets (satellite imagery, radar images) are stored in Azure Blob Storage with incident-ID-prefixed paths. An append-only audit trail captures every ingestion event. Storage complies with Australian data residency requirements (Australia East region) per the Constitution (Principle VI).

**Why this priority**: Reliable, partitioned storage underpins every downstream capability — dashboards, agent processing, audit, replay, and scenario rehearsal. Without correct partitioning and audit, the system cannot support multi-agency coordination with data isolation.

**Independent Test**: Can be tested by ingesting signals for two different jurisdictions, verifying that Cosmos DB partition keys correctly isolate the data, that raw payloads are retrievable from Blob Storage, and that the audit trail captures every ingestion event with correlation IDs.

**Acceptance Scenarios**:

1. **Given** a signal is ingested for an incident in NSW, **When** the signal is persisted, **Then** it is stored in the Cosmos DB signals container with a partition key derived from the tenant scope (jurisdiction + organisation), and is not visible to queries scoped to VIC or QLD.
2. **Given** a radar image is ingested during an active incident, **When** it is stored, **Then** the binary is written to Azure Blob Storage under the path `binary-assets/{incidentId}/{dataSourceId}/{timestamp}.png`, and a reference to the blob URI is stored in the signal's `payload.binaryAssetUri` field.
3. **Given** any signal is ingested, **When** the ingestion completes, **Then** an immutable audit entry is written to the audit container with the signal ID, data source ID, ingestion timestamp, correlation ID, and any validation outcomes.
4. **Given** the Cosmos DB container for signals is configured, **Then** the partition key strategy enables ≤ 500ms p95 query latency for dashboard aggregation queries against a single incident.

---

### User Story 6 - Simulate all data sources for scenario rehearsal (Priority: P6)

A preparedness planner or system administrator configures a simulation scenario (e.g., "Category 3 cyclone approaching Cairns" or "Major flooding along the Hawkesbury-Nepean river system"). The simulation framework generates realistic synthetic data for every registered data source involved in that scenario type, producing signals that mimic the structure, cadence, geographic distribution, and escalation pattern of real source data. Simulated signals flow through the same ingestion pipelines and agent handoff chains as real data, but are clearly marked as simulation data so they cannot be confused with live signals.

**Why this priority**: The Constitution (Quality Gates section) requires scenario-based testing for bushfire, cyclone, and flood scenarios. Simulation is essential for operational exercises, agent evaluation, and demonstrating SC-004 through SC-006 of spec 001.

**Independent Test**: Can be tested by starting a flood simulation scenario for the Hawkesbury-Nepean catchment, verifying that the simulator generates BoM flood warnings, river gauge readings with rising water levels, SES flood intelligence updates, road closure signals from Transport for NSW, and social media posts — all following a realistic temporal escalation pattern — and that the Monitoring Agent processes them identically to real signals.

**Acceptance Scenarios**:

1. **Given** a planner starts a bushfire simulation for the Blue Mountains region, **When** the simulation begins, **Then** the framework generates synthetic signals from relevant data sources (BoM warnings, GA hotspots, NSW RFS incidents, EPA air quality alerts, social media reports) following a realistic temporal progression from initial detection through escalation.
2. **Given** the simulation is running, **When** synthetic signals are generated, **Then** each SignalEnvelope has `provenance.collectionMethod=simulation`, a `simulationRunId` in the provenance metadata, and is stored in a simulation-scoped partition that does not mix with live operational data.
3. **Given** a flood simulation targets the Brisbane River catchment, **When** the simulator generates river gauge data, **Then** the synthetic readings follow a realistic hydrograph curve (gradual rise, peak, gradual recession) with values that cross minor, moderate, and major flood thresholds at appropriate time intervals.
4. **Given** the simulation includes social media sources, **When** synthetic social posts are generated, **Then** they include a realistic mix of accurate community reports, duplicate information, and a configurable proportion of misinformation, so that the hub's trust scoring and misinformation detection are exercised.
5. **Given** a simulation scenario completes, **When** a planner reviews the results, **Then** the system can replay the full sequence of simulated signals, agent handoffs, and recommendations for post-exercise review.

---

### User Story 7 - Field reports and incident management system integration (Priority: P7)

The ingestion layer receives field officer reports (manual text entries) and structured feeds from incident management systems (ICON and WebEOC) used by state emergency services. Field reports are normalised into SignalEnvelopes with `source.kind=field_report` and `trust_tier=tier_4_field_reports`. The system supports both API-based pull from IMS platforms and manual submission through the hub's own interface.

**Why this priority**: Field reports are direct observations from trained personnel and provide ground-truth intelligence that complements sensor and authoritative data. IMS integration avoids duplicate data entry for agencies already using ICON or WebEOC.

**Independent Test**: Can be tested by submitting a field officer report via the hub's API and verifying its normalisation to a SignalEnvelope, and by pulling a sample feed from a WebEOC test endpoint and verifying mapping.

**Acceptance Scenarios**:

1. **Given** a field officer submits a text report through the hub's API endpoint (`POST /signals`), **When** the signal is processed, **Then** it is normalised to a SignalEnvelope with `source.kind=field_report`, the officer's identity in the provenance, and `trust_tier=tier_4_field_reports`.
2. **Given** the ICON IMS publishes an incident update via its API, **When** the field report pipeline polls the feed, **Then** the update is mapped to a SignalEnvelope with structured fields extracted from the ICON payload (incident ID, type, status, location, responding units).

---

### Edge Cases

- A data source changes its data format or API schema without notice (e.g., BoM modifies its XML product schema); the ingestion pipeline must detect the incompatibility, reject unparseable payloads, and alert operators.
- Two authoritative sources provide contradictory information for the same location and time (e.g., a flood warning is issued but river gauge readings show no rise); the system records both signals with independent provenance and flags the contradiction for human review per Constitution Principle III.
- A satellite imagery download partially fails (truncated file); the pipeline must detect the corruption, discard the incomplete blob, and retry on the next available pass.
- During a simulation, a real incident begins; the system must prevent simulation signals from contaminating the live operational data partition and vice versa.
- A social media API imposes rate limiting during a high-volume disaster event; the pipeline must throttle gracefully, prioritise newer posts, and log the throttling event.
- A sensor reading arrives with a timestamp significantly in the future (clock drift); the pipeline must detect and flag the anomaly rather than accepting it as fresh data.
- The Cosmos DB partition for a specific tenant approaches the 20GB logical partition limit during a prolonged incident; the system must alert operators before the limit is reached.

## Clarifications

### Session 2026-03-25

- Q: How should the ingestion framework handle duplicate source products across consecutive polls (e.g., BoM FTP products remain available for 8-36 hours, fire GeoJSON feeds return all current incidents each poll)? → A: Content-hash deduplication (Option A). Each pipeline computes a hash of the source product's canonical identifier (e.g., BoM product code + issue timestamp, GeoJSON feature ID + update timestamp) and skips re-ingestion if the hash already exists in the signal store. A new signal is created only when the content or metadata has changed.
- Q: Should the spec require structured observability signals (metrics, logs, traces) from the ingestion pipelines, or defer metric selection to implementation? → A: Yes, define minimum observability signals (Option A). Each pipeline must emit structured metrics (signals ingested/sec per source, dedup hit rate, normalisation latency p50/p95, circuit breaker state changes, dead-letter queue depth) and structured logs integrated with the hub's existing monitoring infrastructure (Azure Monitor / Application Insights).
- Q: How should ingested signals be associated with specific incidents, given that signals arrive continuously, multiple concurrent incidents can exist in the same jurisdiction, and signals ingested before an incident is declared need retrospective association? → A: Associate at ingestion time (Option A, extended). The ingestion pipeline checks for active incidents by jurisdiction and location overlap when persisting each signal, setting the `incidentId` field on the SignalEnvelope. Signals arriving before any matching incident have `incidentId=null`. When a new incident is declared, the Monitoring Agent (or a subagent of it) retrospectively associates `incidentId` on previously ingested signals that match the new incident's jurisdiction and location.
- Q: How should simulation realism be grounded — should simulators replay historical data, generate from parametric models, or both? → A: Hybrid (Option C). Simulators use parametric generation from domain-specific models (e.g., hydrograph curves, fire spread rate formulas, cyclone track models calibrated against published Australian reference data) by default. Historical event datasets (e.g., Black Summer 2019-20, Lismore 2022 flood) can optionally be loaded as scenario overlays to enhance realism. Historical data is not required for the framework to function.
- Q: Should all radar and satellite imagery be ingested nationally (high storage cost), scoped to active incidents, or stored as metadata-only with on-demand retrieval? → A: Hybrid metadata-only with incident-triggered full ingestion. By default, store only metadata references (source URI, timestamp, coverage area) for radar and satellite products. When an active incident exists, automatically ingest full binary imagery from stations within or adjacent to the incident area and satellite imagery covering the incident region. On-demand retrieval remains available for any metadata reference outside active incident scope. Simulation scenarios also activate full binary ingestion for the simulated region.
- Q: Should this spec acknowledge and require SignalEnvelope schema extensions for `incidentId` (root level), `simulationRunId` (in provenance), and `binaryAssetUri` (in payload), given the existing schema has `additionalProperties: false` at root? → A: Yes, require schema extensions in this spec (Option A). The spec explicitly requires extending the SignalEnvelope schema to add `incidentId` (optional string, root level) and `simulationRunId` (optional string, in `provenance`). The `binaryAssetUri` fits within `payload` (already allows additionalProperties). The data-engineer agent is consulted during planning to validate these changes.
- Q: How should national/multi-jurisdiction signals (e.g., BoM national warnings, GA earthquake alerts, Himawari satellite imagery) be partitioned in the signal store, given FR-025 uses `{jurisdictionId}_{organisationId}` but national signals have no single jurisdiction? Additionally, is Cosmos DB the appropriate storage solution for this scale and volume of signals, or should an alternative such as OneLake, Azure Data Explorer, or Azure Blob Storage (with query layer) be considered? → A: **Referred to data-engineer agent** for architecture review during planning. The data-engineer agent (with handoff to solution-architect and azure-principal-architect as needed) must evaluate and recommend:
  1. Whether Cosmos DB remains the appropriate primary signal store given the expected signal volume (50,000+/hr sustained, burst during multi-incident scenarios), binary metadata references, national-scope fan-out requirements, and 20GB logical partition limits.
  2. Alternative or complementary storage options: OneLake (Fabric) for analytical workloads over historical signals, Azure Data Explorer (Kusto) for time-series signal queries and anomaly detection, Azure Blob Storage with a lightweight query index for raw/binary payloads, or a polyglot approach combining Cosmos DB for hot operational queries with a cooler tier for historical analysis.
  3. The partition key strategy for national and multi-jurisdiction signals — whether to fan-out to affected jurisdiction partitions, use a hierarchical partition key, maintain a `national` scope partition with cross-partition query patterns, or apply a different approach based on the chosen storage technology.
  4. The impact of simulation partition isolation (FR-029) on the chosen storage architecture.
  The data-engineer agent's recommendation has been captured in the implementation plan (see research.md). The resolved decision is: Cosmos DB with hierarchical partition key (`scope/jurisdictionId/dataSourceId`) and national signal fan-out. FR-025 has been updated to reflect this resolution.
- Q: What level of misinformation detection should the social media ingestion pipeline implement, given that the spec references "misinformation detection heuristics" but does not define the mechanism? → A: Tiered — rules at ingestion, LLM at classification (Option C). The ingestion pipeline applies fast, deterministic rule-based heuristics (burst detection, contradiction detection, duplicate amplification) to flag obvious patterns and set `validationStatus=escalated`. The Monitoring Agent then applies LLM-based analysis (using its existing LLM integration) to the flagged subset for deeper evaluation before deciding whether to forward to Risk Assessment or hold for human review.
- Q: How should ingestion pipelines be deployed and scaled, given polling intervals from 30 seconds to 6 hours and a throughput target of 50,000 signals/hour with surge capacity during multi-state disasters? → A: Background workers in Azure Container Apps (Option B). Pipelines run as long-lived background worker processes within the existing Azure Container Apps deployment (consistent with the architecture). Each pipeline class runs as a separate worker with its own polling loop. Container Apps auto-scale based on queue depth or CPU metrics to handle surge during active incidents.
- Q: Should the system support running simulation scenarios concurrently with live operational ingestion, given the Constitution requires scenario-based drills and the edge case "during a simulation, a real incident begins" implies concurrency? → A: Yes, require concurrent support (Option A). The system MUST support running one or more simulation scenarios simultaneously with live operational ingestion. Simulation signals and live signals share the same pipeline workers but are isolated at the storage partition level (FR-029). Pipeline workers handle both scopes without cross-contamination.

## Requirements *(mandatory)*

### Functional Requirements

#### Ingestion Pipelines

- **FR-001**: The system MUST implement category-specific ingestion pipelines for each source class: authoritative government feeds, sensor/IoT networks, satellite imagery, social media, community platforms, field reports, and incident management systems.
- **FR-001a**: Ingestion pipelines MUST be deployed as long-lived background worker processes within Azure Container Apps, consistent with the existing hub architecture. Each pipeline class (authoritative, sensor, satellite, social, community, field report/IMS) MUST run as a separate worker with its own polling loop and independent lifecycle. Container Apps MUST be configured to auto-scale pipeline workers based on queue depth and CPU utilisation, enabling surge capacity during multi-state disaster events. Each worker MUST support graceful shutdown (completing in-progress ingestion cycles before terminating) and health checks for liveness and readiness probes.
- **FR-002**: Each ingestion pipeline MUST normalise source-specific payloads into the SignalEnvelope schema defined in `packages/schemas/signal-envelope.schema.json`, including all required fields: source (dataSourceId, name, kind), category, occurredAt, receivedAt, location, payload, confidenceScore, freshnessScore, validationStatus, and provenance.
- **FR-002a**: This feature MUST extend the SignalEnvelope JSON schema (`packages/schemas/signal-envelope.schema.json`) with the following field:
  - `simulationRunId` (optional string, within the `provenance` object): The identifier of the simulation run that generated this signal. Present only for simulated signals (FR-037). The `provenance` sub-schema MUST be extended to include this field (currently has `additionalProperties: false`).
  Note: `incidentId` already exists at root level in the current schema — no extension needed. `binaryAssetUri` is stored within `payload` (which allows additionalProperties) — no schema constraint change needed. The Signal Pydantic model (`packages/domain/src/domain/models/signal.py`) already has `incident_id` and `provenance` as `dict[str, Any]`, so `simulationRunId` is accepted dynamically — no model change needed.
  These schema extensions MUST be validated with the data-engineer agent during planning to ensure backward compatibility with existing signal consumers.
- **FR-003**: Each ingestion pipeline MUST validate the normalised SignalEnvelope against the JSON Schema before persistence. Payloads that fail schema validation MUST be routed to the dead-letter queue with the validation error details.

#### Source-Specific Ingestion Approaches (Verified Against Source Technical Documentation)

- **FR-004**: The Bureau of Meteorology ingestion pipeline MUST support the following data products as documented by BoM's public data feed service (ref: bom.gov.au/catalogue/data-feeds.shtml):
  - **Warnings**: Pull from the BoM anonymous FTP/HTTP service (`ftp://ftp.bom.gov.au/anon/gen/fwo/`). Products are XML documents conforming to the BoM product XML schema (XSD v1.7 at `bom.gov.au/schema/v1.7/product.xsd`) and AMOC schema (`bom.gov.au/schema/v1.7/amoc.xsd`). Warnings include severe weather, tropical cyclone, flood, fire weather, and coastal warnings. Products are event-driven and are deleted from FTP within 8-36 hours of publication (per BoM's FTP delete-time policy). Polling interval: 60 seconds.
  - **Forecasts**: Pull from FTP (`ftp://ftp.bom.gov.au/anon/gen/fwo/`). XML format conforming to the same product XSD. State-based products include: précis forecast, city forecast, town forecast, district forecast, coastal waters and local waters forecasts (ref: BoM text forecasts user guide). Updated on a scheduled basis (typically every 6-12 hours). Polling interval: 15 minutes.
  - **Observations (State Summaries)**: Pull from BoM web service. XML format with 10-minute update intervals (ref: BoM State-based Observations 10-minute updates user guide, `bom.gov.au/catalogue/Observations-XML.pdf`). Polling interval: 5 minutes.
  - **Observations (Individual Stations)**: Pull from BoM web service. Available in XML, AXF, and JSON formats. 72-hour station-based observational products with half-hourly updates (ref: BoM 72-hour historical observations user guide, `bom.gov.au/catalogue/72_hr_historical_obs.pdf`). Polling interval: 30 minutes.
  - **Radar**: Pull radar images from FTP (`ftp://ftp.bom.gov.au/anon/gen/radar/`). Product codes prefixed with IDR. Images are issued every 5 minutes per radar station. Format is PNG. Static radar transparencies and overlays available separately in `ftp://ftp.bom.gov.au/anon/gen/radar_transparencies/` (ref: BoM radar images user guide). Polling interval: 5 minutes.
  - **Flood Warnings**: Pull from FTP as part of the warnings product set. CAP/XML format conforming to the product XSD. Event-driven publication. Polling interval: 60 seconds.
  - **RSS Feeds**: State-based warning RSS feeds available from `bom.gov.au/rss/`. Can supplement FTP polling for lower-latency notification of new warnings. Format: Atom/RSS with links to full XML products.
- **FR-005**: The Geoscience Australia ingestion pipeline MUST support:
  - **Earthquake Alerts**: Pull from the GA Earthquakes web service (`earthquakes.ga.gov.au`). Data is GeoJSON format with earthquake magnitude, depth, location (latitude/longitude), origin time, and seismic phase data. Event-driven publication. Polling interval: 60 seconds.
  - **Tsunami Warnings**: Pull from the Joint Australian Tsunami Warning Centre (co-operated by BoM and GA). Warnings published in CAP/XML format via BoM's FTP service. Event-driven. Polling interval: 30 seconds.
  - **Sentinel Hotspots**: Pull from GA's Digital Earth Australia Hotspots service (previously Sentinel hotspot program). GeoJSON format with satellite-detected thermal anomalies including location, temperature, confidence, satellite source (Himawari-8, MODIS, VIIRS), and acquisition time. Updated per satellite pass (approximately every 10 minutes for Himawari-8, every 2-6 hours for MODIS/VIIRS). Polling interval: 15 minutes.
- **FR-006**: The state/territory fire service ingestion pipeline MUST support each service's public incident feed:
  - **NSW RFS (Fires Near Me)**: GeoJSON FeatureCollection from `rfs.nsw.gov.au`. Also available in GeoRSS and Common Alerting Protocol (CAP) formats. GeoJSON Feature properties include: `title` (incident name), `category` (e.g., "Nat Haz Bush Fire"), `type`, `status` (Responding | Not Yet Controlled | Being Controlled | Under Control), `alertLevel` (Emergency Warning | Watch and Act | Advice | Not Applicable). Geometry includes both Point and Polygon representations. Licensed under Creative Commons Attribution 3.0 Australia. Real-time updates auto-refresh. Polling interval: 60 seconds.
  - **VIC CFA**: GeoJSON feed for current incidents from the CFA website. Properties include incident type, status, location, and alert level. Real-time updates. Polling interval: 60 seconds.
  - **QLD QFES**: GeoJSON/RSS feed for current incidents. Real-time updates. Polling interval: 60 seconds.
  - **SA CFS, WA DFES, TAS TFS, ACT ESA, NT PFES**: Each publishes incident data via a public feed (GeoJSON or RSS depending on the service). Polling interval: 60 seconds per service.
- **FR-007**: The state SES flood intelligence ingestion pipeline MUST support:
  - **NSW SES, VIC SES, QLD SES**: Pull from their respective public intelligence feeds. JSON/GeoJSON format with flood status, affected areas, and evacuation orders. Event-driven. Polling interval: 2 minutes.
- **FR-008**: The sensor and IoT ingestion pipeline MUST support:
  - **BoM Automatic Weather Stations**: JSON observation data from the BoM web service. Fields include: station ID, station name, temperature (°C), dew point (°C), relative humidity (%), wind speed (km/h), wind gust (km/h), wind direction, mean sea level pressure (hPa), rainfall since 9am (mm). Updated every 5-10 minutes. Polling interval: 5 minutes.
  - **River Gauge Networks**: JSON data from BoM Water Data Online and state water monitoring services. Fields include: gauge ID, gauge name, water level (metres AHD), flow rate (ML/day), trend (rising/falling/steady), minor/moderate/major flood level thresholds. Real-time updates. Polling interval: 5 minutes.
  - **EPA Air Quality Sensors**: JSON data from state EPA networks (NSW DPIE, VIC EPA, QLD DES). Fields include: station ID, PM2.5, PM10, ozone levels, AQI category (Good/Fair/Poor/Very Poor/Hazardous). Hourly updates. Polling interval: 30 minutes.
- **FR-009**: The satellite imagery ingestion pipeline MUST support:
  - **Sentinel (Copernicus)**: Download via the Copernicus Data Space Ecosystem API. GeoTIFF format. Products include multispectral imagery for vegetation health (NDVI), burn scar mapping (NBR), and land surface temperature. Spatial resolution 10-60m depending on band. Daily availability per overpass. Polling interval: 6 hours.
  - **Himawari-8/9**: Download from BoM's satellite imagery FTP service (`ftp://ftp.bom.gov.au/anon/gen/gms/`). Available in JPG and GeoTIFF formats. Images issued every 10 minutes. Product codes prefixed with IDE. Full-disk and regional images. (ref: BoM satellite images user guides for JPG format and GeoTIFF format). Polling interval: 10 minutes.
- **FR-009a**: Radar and satellite imagery ingestion MUST follow a hybrid metadata-only with incident-triggered full ingestion strategy:
  - **Default (no active incident in region)**: The pipeline MUST ingest only a metadata reference for each radar and satellite product, recording the source URI, product timestamp, coverage area (as a bounding box or polygon), product type, and data source ID. The metadata reference MUST be stored as a SignalEnvelope with `payload` containing the metadata fields and a `binaryAssetUri` pointing to the source rather than a stored blob. No binary download occurs.
  - **Active incident**: When one or more incidents are active, the pipeline MUST automatically download and store full binary imagery from radar stations within or geographically adjacent to the incident's affected area, and satellite imagery products whose coverage area overlaps the incident region. Downloaded binaries MUST be stored per FR-027. The geographic adjacency threshold for radar stations (e.g., stations whose coverage circle intersects the incident area plus a buffer) MUST be configurable (default buffer: 50 km).
  - **Simulation**: Simulation scenarios MUST activate full binary ingestion for the simulated region, following the same geographic scoping rules as active incidents.
  - **On-demand retrieval**: For any metadata-only reference (outside active incident scope), the system MUST support on-demand download of the full binary asset when requested by an agent or operator, provided the source product has not yet been deleted from the source FTP/HTTP service (subject to BoM's FTP delete-time policy of 8-36 hours). On-demand retrieval MUST store the downloaded binary per FR-027 and update the SignalEnvelope's `payload.binaryAssetUri` to reference the stored blob.
- **FR-010**: The social media ingestion pipeline MUST support:
  - **X/Twitter**: Pull via the X API v2 filtered stream endpoint, matching disaster-relevant keywords (bushfire, flood, cyclone, evacuation, emergency, SES) and official emergency account handles for Australian jurisdictions. Rate limits must be respected per the X API terms of service. Real-time streaming with reconnection backoff. Text content only (no media download for initial scope).
  - **Facebook**: Pull via the Meta Graph API for public pages of emergency services and community groups. Rate limits per Meta's API terms (200 calls/hour per user token). Polling interval: 5 minutes.
  - **Reddit**: Pull via the Reddit JSON API for Australian subreddits (r/australia, r/sydney, r/melbourne, r/brisbane, state-specific subreddits) during active events. Rate limit: 60 requests/minute per Reddit API guidelines. Polling interval: 2 minutes during active events, 15 minutes otherwise.
- **FR-010a**: The social media and community ingestion pipelines MUST implement a tiered misinformation detection approach:
  - **Tier 1 — Rule-based heuristics at ingestion time** (deterministic, fast, auditable):
    - **Burst detection**: Flag when the volume of posts referencing a specific topic, hazard type, or location exceeds a configurable threshold (default: 20 posts within a 10-minute window from distinct accounts) without a corresponding authoritative signal for the same location/hazard. Flagged signals receive `validationStatus=escalated`.
    - **Contradiction detection**: Flag when a social/community signal asserts a hazard condition (e.g., "flooding in [location]") but no authoritative or sensor signal for that location and hazard type exists within a configurable time window (default: 30 minutes). Flagged signals receive a reduced `confidenceScore` (halved from base tier confidence).
    - **Duplicate amplification detection**: Flag when multiple posts share near-identical text (cosine similarity > 0.9 on normalised text) within a short time window (default: 5 minutes), suggesting coordinated or copy-paste activity. Flagged signals are grouped and only the earliest is retained at normal confidence; duplicates receive `validationStatus=escalated`.
  - **Tier 2 — LLM-based analysis at Monitoring Agent classification** (applied only to Tier 1 flagged signals):
    - The Monitoring Agent MUST apply its existing LLM integration (via `LLMCallMixin`) to evaluate signals flagged with `validationStatus=escalated` by Tier 1 heuristics. The LLM assessment determines whether the signal is credible, suspicious, or misinformation, and the Monitoring Agent sets the final `validationStatus` accordingly.
    - Signals classified as misinformation by Tier 2 MUST NOT be forwarded to Risk Assessment. They MUST be retained in the signal store with `validationStatus=rejected` and a provenance note recording the LLM assessment rationale.
    - If the LLM is unavailable (fallback mode), Tier 1 escalated signals MUST remain with `validationStatus=escalated` and MUST NOT be forwarded to Risk Assessment without human review, consistent with Constitution Principle I (safe degradation).
- **FR-011**: The community and volunteer ingestion pipeline MUST support:
  - **Snap Send Solve**: Pull via their public or partner API. Geotagged reports with category, description, and optional photo reference. Polling interval: 5 minutes.
  - **Volunteer Bushfire Brigades**: Manual entry or structured report submission through the hub's API. Event-driven.
  - **Surf Life Saving Australia**: Manual entry or structured report submission. Event-driven.
- **FR-012**: The field report and IMS ingestion pipeline MUST support:
  - **Agency Field Officer Reports**: Manual submission via `POST /signals` API endpoint. Free-text with structured metadata (officer ID, location as coordinates, incident reference, category, timestamp).
  - **ICON IMS**: Pull via ICON's API (used by NSW and other states). JSON format with incident details, resource deployment, situation reports, and status updates. Polling interval: 2 minutes.
  - **WebEOC IMS**: Pull via WebEOC's REST API. JSON format with board data, incident logs, and resource tracking. Polling interval: 2 minutes.

#### Ingestion Processing

- **FR-013**: Each ingestion pipeline MUST compute a `confidenceScore` (0-1) based on the source's trust tier (tier 1 = 0.95 base confidence, tier 6 = 0.3 base confidence), signal validation status, and source-specific quality indicators (e.g., sensor calibration status, social media account verification, alert level severity).
- **FR-014**: Each ingestion pipeline MUST compute a `freshnessScore` (0-1) based on the time delta between the signal's `occurredAt` timestamp and `receivedAt` timestamp, scaled relative to the source's expected update frequency. A signal received within the expected cadence receives a high freshness score (≥ 0.8); signals exceeding 3× the expected cadence receive a freshnessScore below 0.3.
- **FR-015**: Each ingestion pipeline MUST attach a `provenance` object including: `collectionMethod` (matching the data source registry entry, e.g., `api_pull`, `sensor_network`, `manual_entry`, `satellite_downlink`), `sourceUri` (the URL or path from which the data was retrieved), `sourceTimestamp` (the original publication timestamp from the source), and `collector` (the pipeline instance identifier).
- **FR-016**: The ingestion framework MUST support circuit-breaker patterns: after 3 consecutive failures to retrieve data from a source, the pipeline MUST trip, mark the data source as `degraded` in the registry, emit a structured error log, and back off with exponential delay (initial: 30s, max: 5 minutes). The circuit breaker MUST half-open after the backoff period to test connectivity.
- **FR-017**: The ingestion framework MUST retain the raw, unmodified source payload alongside the normalised SignalEnvelope for audit, debugging, and replay purposes. Raw payloads MUST be stored in Azure Blob Storage.
- **FR-018**: All ingestion pipelines MUST attach a correlation ID (UUID) to each signal that is propagated through all downstream processing (agent handoffs, recommendations, alerts) to enable end-to-end tracing.
- **FR-018a**: Each ingestion pipeline MUST implement content-hash deduplication to prevent re-ingestion of unchanged source products across consecutive polling cycles. The pipeline MUST compute a hash from the source product's canonical identifier (e.g., BoM product code + issue timestamp, GeoJSON feature ID + last-updated timestamp) and check it against the signal store before creating a new SignalEnvelope. A new signal MUST be created only when the content or metadata has materially changed. This prevents redundant storage, avoids spurious agent handoffs, and ensures SC-002 throughput reflects genuinely new signals.
- **FR-018b**: Each ingestion pipeline MUST emit structured observability signals that integrate with the hub's existing monitoring infrastructure (Azure Monitor / Application Insights). At minimum, the following signals MUST be emitted:
  - **Ingestion throughput**: signals ingested per second, per data source, measured after deduplication (only genuinely new signals counted).
  - **Deduplication hit rate**: percentage of polled source products skipped due to content-hash match (FR-018a), per data source, per 5-minute window.
  - **Normalisation latency**: time from raw payload receipt to persisted SignalEnvelope, reported at p50 and p95, per pipeline.
  - **Circuit breaker state changes**: structured log event emitted on every state transition (closed → open, open → half-open, half-open → closed), per data source.
  - **Dead-letter queue depth**: current count of unresolved dead-letter entries, per pipeline, updated on each ingestion cycle.
  - **Source poll outcome**: success/failure/timeout per poll attempt, per data source, enabling upstream availability dashboards.
  - **Partition size monitoring**: estimated document count and storage size per Cosmos DB logical partition, sampled periodically (default: every 15 minutes), with alerts when any partition exceeds 80% of the 20GB logical partition limit.

#### Agent Interaction with Ingested Data (Cross-Referenced Against Constitution Principle II)

- **FR-019**: The Monitoring Agent MUST operate as the first-stage consumer of all ingested signals. Per the Constitution (Principle II), the Monitoring Agent Network ingests near-real-time signals from weather sensors, IoT sources, and social media, and classifies them by category. The Monitoring Agent does NOT ingest raw data from external sources directly; it receives normalised SignalEnvelopes from the ingestion pipelines via an event-driven trigger (signals appearing in the signal store or via an internal event channel).
- **FR-019a**: At ingestion time, each pipeline MUST check for active incidents by comparing the signal's jurisdiction and geographic location against the jurisdiction boundaries and affected areas of all active incidents. If a matching incident is found, the pipeline MUST set the `incidentId` field on the SignalEnvelope before persistence. If no matching incident exists, the signal MUST be persisted with `incidentId=null`. If the signal's location overlaps multiple active incidents, the pipeline MUST create one signal record per matching incident, each with a distinct `incidentId` and sharing the same correlation ID. This ensures each incident's signal partition contains all relevant signals for that incident's dashboard and agent processing.
- **FR-019b**: When a new incident is declared, the Monitoring Agent (or a designated subagent) MUST retrospectively scan recently ingested signals with `incidentId=null` that match the new incident's jurisdiction and geographic area, and associate them with the new incident by setting their `incidentId`. The lookback window for retrospective association MUST be configurable (default: 24 hours). Retrospective association MUST be recorded in the audit trail with the association timestamp and the triggering incident declaration event.
- **FR-020**: The Monitoring Agent MUST evaluate each signal against the handoff routing rules defined in the governance registry (spec 005, FR-009a). When the governance registry is unavailable, the agent MUST fall back to its current hardcoded routing: forward signals with `category in {fire, weather, hydrology}` and `confidenceScore >= 0.8` to the Risk Assessment Agent. This is consistent with Constitution Principle II requiring explicit handoffs and Principle I requiring safe degradation.
- **FR-021**: The Risk Assessment Agent MUST operate on stored signals retrieved from the signal store. Per Constitution Principle II, it generates hazard maps and impact predictions with traceable inputs and assumptions. It receives handoff events from the Monitoring Agent containing signal references, then queries the signal store for the full signal data and related signals to generate hazard assessments and recommendations. It does NOT ingest data directly from external sources.
- **FR-022**: The Evacuation Agent MUST operate on stored data: hazard assessments, road network status (from Transport authority signals ingested by the pipeline), and population data. Per Constitution Principle II, it proposes optimal routes and transport coordination plans. It is invoked by the Risk Assessment Agent via handoff when an evacuation recommendation is generated.
- **FR-023**: The Resource Allocation Agent MUST operate on stored coordination tasks and resource inventories. Per Constitution Principle II, it prioritises supplies and personnel allocation using objective criteria. It does NOT interact with the ingestion layer directly; it receives task prioritisation requests from the incident workflow.
- **FR-024**: The Communication Agent MUST operate on stored recommendations and approved alert content. Per Constitution Principle II, it generates targeted, multilingual alerts. It is invoked by the Risk Assessment Agent via handoff when a public alert recommendation is generated. It does NOT interact with the ingestion layer directly. `defers-to:` 008 (warning-tier multilingual authoring + delivery — the canonical authority sits in `specs/008-communication-agent/spec.md` per feature 028 / US3 / T044; this clause is retained as a contract-level pointer only).

#### Storage Architecture

- **FR-025**: Normalised signals MUST be stored in Azure Cosmos DB in the `signals` container with a hierarchical partition key (`/scope/jurisdictionId/dataSourceId`). This was resolved during the planning phase with data-engineer agent input (see research.md). The partition key design is:
  - Level 1 `scope`: `live` for operational signals, `sim-{runId}` for simulation signals (FR-029).
  - Level 2 `jurisdictionId`: `national`, `nsw`, `vic`, `qld`, `sa`, `wa`, `tas`, `nt`, `act`.
  - Level 3 `dataSourceId`: the data source identifier from the seed catalogue.
  For national signals, the ingestion pipeline creates the primary record in the `national` partition and fan-out reference records in each affected jurisdiction partition. This ensures jurisdiction-scoped dashboard queries surface national signals without cross-partition queries. The following constraints apply:
  - Signals MUST be queryable by jurisdiction, incident, data source, category, and time range.
  - Queries scoped to a single incident MUST meet the ≤ 500ms p95 latency target.
  - National signals MUST be discoverable by jurisdiction-scoped queries (i.e., a NSW dashboard query must surface national BoM warnings affecting NSW).
  - Multi-tenant isolation MUST be enforced at the storage layer.
  - All data MUST reside in Australian Azure regions (Australia East primary).
- **FR-026**: Raw source payloads MUST be stored in Azure Blob Storage in a container structured as `raw-payloads/{dataSourceId}/{YYYY-MM-DD}/{signalId}.{format}`. Payloads MUST be stored in the same Australian Azure region as the Cosmos DB instance (Australia East).
- **FR-027**: Binary assets (radar images, satellite imagery) downloaded during active incidents or on-demand retrieval MUST be stored in Azure Blob Storage in a container structured as `binary-assets/{incidentId}/{dataSourceId}/{timestamp}.{format}`. For on-demand retrievals outside an incident context, the path MUST use `binary-assets/_on-demand/{dataSourceId}/{timestamp}.{format}`. A URI reference to the blob MUST be stored in the signal's `payload.binaryAssetUri` field, replacing the original source URI.
- **FR-028**: An immutable audit trail for every ingestion event MUST be maintained in Azure Blob Storage as append-only JSON Lines files, partitioned by date: `audit/ingestion/{YYYY-MM-DD}/{hour}.jsonl`. Each audit entry MUST include: signal ID, data source ID, correlation ID, ingestion timestamp, normalisation outcome (success/failure/rejected), validation status, and any error details.
- **FR-029**: Simulation signals MUST be stored in a separate logical partition from operational signals. The partition key MUST include a simulation scope marker (e.g., `sim-{simulationRunId}`) so that simulation data is never returned by queries targeting live operational data. Simulation raw payloads MUST be stored under a separate blob prefix: `simulation/{simulationRunId}/`.
- **FR-030**: The Cosmos DB container configuration MUST support the data engineer agent's quality gate of ≤ 500ms p95 for dashboard queries and the governance registry's NFR-001 of ≤ 50ms p95 for single handoff-chain lookups.
- **FR-031**: Storage MUST comply with the Constitution (Principle IV and VI): all data stored in Australian Azure regions (Australia East primary), sensitive data encrypted at rest using platform-managed keys, and access controlled via Entra ID RBAC with tenant-scoped isolation.

#### Simulation Framework

- **FR-032**: The simulation framework MUST generate synthetic signals for every data source registered in the seed catalogue (`packages/domain/src/domain/seed/data_sources_australia.json`) that is relevant to the chosen scenario type (bushfire, flood, cyclone, severe storm).
- **FR-033**: Each data source simulator MUST produce signals that structurally conform to the real source's data format (same fields, value ranges, coordinate systems, and temporal cadence) as documented in the source-specific ingestion requirements (FR-004 through FR-012). Simulators MUST use parametric generation from domain-specific models as the default realism approach:
  - **Flood simulators**: Hydrograph curves calibrated against BoM flood classification thresholds (minor, moderate, major) for the target catchment, with configurable rise rate, peak duration, and recession rate.
  - **Bushfire simulators**: Fire spread rate and perimeter expansion models based on the McArthur Forest Fire Danger Index (FFDI) or Grassland Fire Danger Index (GFDI), with wind speed, temperature, humidity, and fuel load as inputs.
  - **Cyclone simulators**: Track and intensity models based on published BoM tropical cyclone climatology, with configurable central pressure, radius of maximum wind, and forward speed.
  - **Sensor simulators**: Value generation within documented plausible ranges for each sensor type (e.g., temperature -20°C to 55°C, river gauge levels 0m to historical maximum + 20% margin).
- **FR-033a**: The simulation framework MUST support optional historical event overlays. When a historical event dataset is loaded for a scenario (e.g., actual BoM/RFS/gauge data from the 2019-20 Black Summer bushfire or the 2022 Lismore flood), the simulator MUST use the historical data as the signal source instead of parametric generation, with configurable perturbations (shifted geographic location, altered timing, modified severity scaling). Historical datasets are stored as structured files within the simulation assets directory. Historical overlay is an enhancement; the framework MUST function fully using parametric generation alone.
- **FR-034**: The simulation framework MUST support temporal scenario progression: simulators generate signals that follow a realistic event lifecycle from detection through escalation, peak, and (optionally) de-escalation. The lifecycle timeline MUST be configurable (e.g., compress a 48-hour flood event into a 2-hour exercise).
- **FR-035**: Scenario simulators MUST generate geographically coherent data: all simulated signals for a scenario MUST reference locations within the defined scenario area, and geographic relationships between signals must be plausible (e.g., upstream gauges rise before downstream gauges in a flood scenario, fire perimeter expands in the prevailing wind direction).
- **FR-036**: The social media simulator MUST generate a configurable mix of: accurate community observations (70% default), duplicate/redundant posts (15% default), and misinformation (15% default). The mix ratios MUST be adjustable per simulation run.
- **FR-037**: Simulated signals MUST flow through the same ingestion pipelines and agent handoff chains as real signals. The only difference is the `provenance.collectionMethod=simulation` marker and the simulation-scoped storage partition (FR-029).
- **FR-037a**: The system MUST support running one or more simulation scenarios concurrently with live operational ingestion. Simulation signals and live signals MUST share the same pipeline worker processes but MUST be completely isolated at the storage partition level (FR-029) and throughout downstream agent processing. Specifically:
  - Pipeline workers MUST distinguish simulation-generated signals from live signals using the `provenance.collectionMethod=simulation` marker and `simulationRunId` field (FR-002a), and route them to the correct storage partition.
  - The Monitoring Agent MUST process simulation signals within the simulation scope and MUST NOT mix simulation handoffs with live incident handoffs.
  - If a real incident is declared while a simulation is running, the system MUST continue both the simulation and live ingestion independently. Live signals MUST NOT be affected by the simulation, and simulation signals MUST NOT appear in any live operational view or dashboard.
  - The system MUST support at least 3 concurrent simulation runs alongside live operations without degrading live ingestion throughput below the SC-002 target (50,000 signals/hour).
- **FR-038**: The simulation framework MUST support the following minimum scenario templates, each defining which data sources are activated, what event progression pattern is used, and what parametric models drive generation (with optional historical overlay per FR-033a):
  - **Bushfire**: BoM fire weather warnings → GA Sentinel hotspot detections → State fire service incidents (escalating from Advice → Watch and Act → Emergency Warning) → EPA air quality alerts (AQI escalating from Fair → Poor → Hazardous) → Social media reports → Transport road closures → Evacuation signals.
  - **Flood**: BoM severe weather warnings → BoM flood warnings (minor → moderate → major) → River gauge readings (hydrograph curve with rise, peak, recession) → SES flood intelligence updates → Transport road closures → Social media reports → Evacuation signals.
  - **Cyclone**: BoM tropical cyclone watch → BoM tropical cyclone warning → Himawari satellite imagery showing cyclone track and intensification → BoM severe weather/rainfall warnings → River gauge readings → State emergency service incidents → Social media reports.
  - **Severe Storm**: BoM severe thunderstorm warnings → BoM radar imagery (storm cell tracking) → BoM observations (pressure drop, wind gusts, rainfall intensity) → Social media reports → SES/emergency service incidents.
- **FR-039**: Each simulation run MUST record the simulation parameters (scenario type, target region, time compression ratio, active data sources, misinformation ratio) and MUST be replayable for post-exercise review.

### Key Entities

- **IngestionPipeline**: A configured processing component responsible for polling or receiving data from one or more data sources of the same class (authoritative, sensor, social, etc.), normalising payloads to SignalEnvelopes, and routing them to the signal store and agent handoff chain. Key attributes: pipeline ID, source class, polling configuration (interval, endpoint, format), circuit breaker state, last successful poll timestamp, error count.
- **IngestionAuditEntry**: An immutable record of a single ingestion event. Key attributes: signal ID, data source ID, correlation ID, timestamp, outcome (success/rejected/failed), validation errors if any, raw payload blob reference.
- **SimulationScenario**: A configured disaster scenario template specifying the scenario type (bushfire/flood/cyclone/severe_storm), geographic target area (as a GeoJSON polygon), time compression ratio, activated data sources (subset of seed catalogue), event progression timeline with phases and triggers, and per-source simulator parameters. Referenced by SimulationRun.
- **SimulationRun**: An execution of a SimulationScenario, producing synthetic signals across all activated data source simulators. Key attributes: run ID, scenario reference, start/end times, time compression ratio, total signals generated per source, status (configuring/running/completed/aborted), created_by persona.
- **DataSourceSimulator**: A per-data-source generator that produces synthetic SignalEnvelopes mimicking the real source's structure, cadence, and value ranges. Configured by a SimulationScenario to produce geographically and temporally coherent output aligned with the scenario progression.

### Assumptions

- The Bureau of Meteorology's anonymous FTP/HTTP data feed service remains freely available for non-commercial data access as documented on `bom.gov.au/catalogue/data-feeds.shtml`. Products conform to the BoM product XSD v1.7 and AMOC schema. Production SLA guarantees may require Registered User access.
- State fire service and SES public feeds (GeoJSON/GeoRSS/CAP) remain publicly accessible. The NSW RFS feed is under Creative Commons Attribution 3.0 Australia licence. Format changes will be detected by schema validation and handled as edge cases.
- Social media API access (X v2, Meta Graph API, Reddit JSON API) is available under current API terms and pricing at the time of implementation. API terms changes may require pipeline reconfiguration.
- GA earthquake service (`earthquakes.ga.gov.au`) and Sentinel Hotspots service continue to be publicly accessible via their current web service endpoints and GeoJSON format.
- ICON and WebEOC APIs are accessible to the hub under data-sharing agreements with participating state emergency services. These agreements are negotiated outside the scope of this spec (per spec 005 Out of Scope).
- Copernicus Data Space Ecosystem API access is available for Sentinel satellite data downloads within their fair-use policy.
- The simulation framework generates data that passes the same schema validation as real data, but does NOT require approval from source organisations (simulated data is clearly marked and never published externally).
- The existing SignalEnvelope schema already includes `incidentId` at root level. The only schema extension needed is adding `simulationRunId` to the `provenance` object (see FR-002a). The `binaryAssetUri` field is stored within `payload` (which allows additionalProperties). The Signal Pydantic model already has `incident_id` and accepts `simulationRunId` in `provenance` dynamically. The data-engineer agent validated backward compatibility during planning. No other schema changes are required.

### Out of Scope

- Negotiation of API access agreements with data source providers (governed by spec 005 and operational agreements).
- Modification of external source APIs or data formats.
- Implementation of new external-facing APIs for third-party consumers of the hub's data.
- AI/ML model training on ingested data (downstream capability operating on stored data).
- Real-time alerting to the public (Communication Agent's responsibility, spec 001).
- Agent business logic beyond the ingestion-to-handoff interface (e.g., risk scoring algorithms, evacuation route computation).
- Data retention policy enforcement and automated archival (future lifecycle management feature).
- Changes to the governance registry or constitutional assessment workflows (spec 005).
- Agent runtime refactoring to consume governance-registry handoff rules (spec 005, FR-009b).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Authoritative government feed signals (BoM warnings, GA earthquake alerts) are ingested and normalised within 90 seconds of publication by the source, measured end-to-end from source FTP/HTTP availability to SignalEnvelope persistence in Cosmos DB, across 95% of ingested signals.
- **SC-002**: The ingestion framework sustains a throughput of at least 50,000 signals per hour at steady state, consistent with the data engineer agent's quality gate.
- **SC-003**: At least 95% of ingested signals pass schema validation on first attempt, with rejected signals routed to the dead-letter queue with diagnostic details.
- **SC-004**: Dashboard aggregation queries against a single incident's signals return within 500ms at the 95th percentile, consistent with the data engineer agent's quality gate.
- **SC-005**: Simulation scenarios for bushfire, flood, cyclone, and severe storm each generate synthetic signals from at least 80% of the data sources relevant to that scenario type within the seed catalogue.
- **SC-006**: Simulated signals are structurally indistinguishable from real signals (same schema, value ranges, temporal cadence) except for the simulation provenance marker, verified by passing the same schema validation pipeline.
- **SC-007**: Raw payloads and ingestion audit entries achieve 100% correlation: every persisted SignalEnvelope has a corresponding raw payload in Blob Storage and an audit entry, verified by audit trail reconciliation.
- **SC-008**: Circuit breaker activation correctly marks degraded data sources within 3 minutes of sustained source unavailability, and auto-recovers within 1 minute of source restoration.
- **SC-009**: Simulation data is fully isolated from live operational data: a query targeting live data returns zero simulation signals, and vice versa, verified by cross-partition query tests.

## Assumptions

Scoped to this spec's domain (ingestion + storage of authoritative hazard feeds). Tagging follows `specs/027-spec-hardening` taxonomy: `[RISK]` (open externally-driven risk), `[DECISION]` (deliberate scoping decision), bare bullet (operating assumption).

- **ASM-011**: The AU-v1 deployment context defined in `specs/001-disaster-response-hub/spec.md` is the operational baseline for this spec; capstone-country variants (PH / JP / BD) are deferred. `linked_gaps:` `specs/shared/gap-id-register.md` A-GAP-001..003. `status:` Open.
- **ASM-012** [DECISION]: This spec's deliverables (ingestion + storage of authoritative hazard feeds) integrate with the actor catalogue (`specs/004-actor-github-agents/spec.md`); responsible technical agents - data-engineer, bom-national, ga-national - are consulted via the `agent` tool during authoring and review.
- **ASM-013**: Speckit conventions (FR/SC numbering, ASM/HYP/PER/SCP families) and the persona-profile YAML schema (`specs/027-spec-hardening/contracts/persona-profile.md`) are authoritative; this spec defers to those rather than redefining them.
- **ASM-014** [RISK]: AU-only data residency (constitution NON-NEGOTIABLE #2; Azure `australiaeast` / `australiasoutheast` only) is in tension with the capstone Asia framing (PH / JP / BD sovereign-data handling). Resolution requires a constitution-level amendment owned outside this feature (see `specs/028-capstone-alignment/research.md` D-009). `linked_gaps:` constitution NON-NEGOTIABLE #2. `status:` Open.

## Personas

Authored against the `specs/027-spec-hardening/contracts/persona-profile.md` schema. AU-v1 personas are validated; PH / JP / BD entries are explicit placeholders pending capstone-reinterpretation (D-009) and SME validation per FR-023.

- **PER-010**: cross-ref to `specs/001-disaster-response-hub/spec.md` AIIMS personas (Incident Commander / Planning Officer / Operations Officer / Logistics Officer / Public Information Officer) per `specs/027-spec-hardening/contracts/persona-profile.md`. `status:` validated. `preconditions:` none.
- **PER-011**: cross-ref to `specs/004-actor-github-agents/spec.md` actor catalogue covering all `.github/agents/technical/*.agent.md` actors. `status:` validated. `preconditions:` none.
- **PER-012** [non-AU placeholder]: capstone-country operator personas for PH (NDRRMC), JP (Cabinet Office DRR / FDMA), BD (DDM / CPP volunteers). `status:` placeholder. `preconditions:` capstone-reinterpretation decision per D-009; SME validation via `ama-rubric-grader`-vetted SME interviews.

## Hypotheses

Hypotheses use the FR-018 statement format (`If <condition> then <observable>`) and link to a structured evidence stub conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. Capstone-country hypotheses for this spec's agent ownership (where applicable) are allocated in feature 028 / US2.

- **HYP-004**: If the actors named in `specs/004-actor-github-agents/spec.md` consult on every change to this spec via the `agent` tool, then the AMA rubric criterion mean (Assumptions / Requirements / Personas / Hypotheses / Scope) for this spec rises by at least +1 band relative to the baseline captured in `specs/028-capstone-alignment/evidence/rubric-baseline.md`. **Falsification**: post-feature rubric snapshot shows a regression in any of those five criteria for this spec. **Evidence stub**: `specs/006-data-ingestion-storage/evidence/HYP-044.md` (owner-scoped replacement for the missing cross-spec stub).

## Out of Scope

Items explicitly deferred from this spec; promotion to in-scope requires the named preconditions to clear. Cross-references to other specs use the canonical overlap phrasing (`authoritative for: <capability>` / `defers-to: <NNN> (<capability>)`).

- **SCP-012** [DEFERRED]: Capstone-country variants (PH typhoon, JP earthquake, BD flood) of this spec's capabilities are out of scope until: (i) capstone-reinterpretation decision per D-009; (ii) per-country regulatory + data-sharing preconditions documented in `specs/005-data-source-governance/spec.md` clear; (iii) responsible technical agents (data-engineer, bom-national, ga-national) sign off on country-specific calibration.
- **SCP-013**: Constitutional-level changes (NON-NEGOTIABLE #1..#5) are not modified by this spec; any tension is documented as `[RISK]` in Assumptions, never resolved here.
- **SCP-014**: Cross-spec authority disputes are arbitrated via `product-owner-ba` and the speckit governance flow; this spec does not unilaterally claim ownership of capabilities owned elsewhere. `defers-to:` 018 (recovery-phase indicators, triggers, phase-exit criteria); 008 (warning-tier authoring, multilingual delivery, misinformation defence) where applicable.

## Capstone-Aligned Requirements (Feature 028 / FR-009)

The candidate capstone-country hazard feeds below are deferred until the named preconditions clear. `defers-to:` 005 for residency / lawful basis; `defers-to:` 028 for capstone-reinterpretation.

- **FR-CAP-006-001** [DEFERRED]: Philippines feed candidate **PAGASA** (typhoon + flood). Preconditions: (i) data-sharing MoU with DOST-PAGASA; (ii) JSON / CAP schema validator; (iii) freshness SLO <= 15 min during typhoon season (Jun-Nov).
- **FR-CAP-006-002** [DEFERRED]: Japan feed candidate **JMA** (earthquake + tsunami; JAXA / QZSS for location-augmenting signals). Preconditions: (i) JMA data-licensing terms; (ii) sub-second seismic-event ingestion validator; (iii) 24x7 freshness SLO.
- **FR-CAP-006-003** [DEFERRED]: Bangladesh feed candidate **BWDB / FFWC** (riverine flood). Preconditions: (i) BWDB data-sharing arrangement; (ii) hydro-station schema validator; (iii) freshness SLO <= 30 min during monsoon (Apr-Sep).

> **Overlap note**: This spec carries an existing FR-024 that overlaps with `specs/008-communication-agent`. `defers-to:` 008 (warning-tier multilingual authoring + delivery); the canonical reciprocal `supersedes:` rule is added in spec 008 by feature 028 / US3 / T044.
