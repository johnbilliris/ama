# Implementation Plan: Data Ingestion Pipelines, Storage Architecture, and Simulation Framework

**Branch**: `006-data-ingestion-storage` | **Date**: 2026-03-25 | **Spec**: [specs/006-data-ingestion-storage/spec.md](spec.md)
**Input**: Feature specification from `/specs/006-data-ingestion-storage/spec.md`

## Summary

Build the complete data ingestion layer for the disaster response hub: category-specific polling pipelines for 35+ Australian data sources (BoM, GA, state fire/SES services, sensors, social media, field reports), a signal normalisation framework producing validated SignalEnvelope records, multi-tenant signal storage with audit trail, and a simulation framework generating realistic synthetic data for bushfire, flood, cyclone, and severe storm scenarios. Pipelines run as background workers in Azure Container Apps with circuit-breaker resilience, content-hash deduplication, incident association at ingestion time with retrospective back-fill, tiered misinformation detection (rule-based + LLM), and structured observability. The storage architecture decision (Cosmos DB vs polyglot alternatives) is resolved in the research phase with data-engineer agent input.

## Technical Context

**Language/Version**: Python 3.12 for ingestion pipelines, API services, agent code, domain models, and simulators  
**Primary Dependencies**: FastAPI, Pydantic v2, Azure Cosmos DB SDK, Azure Blob Storage SDK, Azure Cache for Redis SDK, `ftplib`/`httpx` for source polling, `lxml` for BoM XML parsing, `jsonschema` for SignalEnvelope validation  
**Storage**: Azure Cosmos DB for operational signal store (pending data-engineer review for polyglot alternatives); Azure Blob Storage for raw payloads, binary assets, and audit trail; Azure Cache for Redis for dedup hash cache and governance lookups  
**Testing**: pytest (contract tests for each pipeline normaliser, integration tests for circuit breaker and dedup, end-to-end simulation tests); existing Playwright e2e for dashboard signal display  
**Target Platform**: Azure Container Apps (background workers for pipelines, existing API and agents containers); Azure App Service (web); Australia East region  
**Project Type**: Multi-service extension to existing monorepo — new ingestion worker service + domain model extensions + simulation framework  
**Performance Goals**: 50,000 signals/hour sustained (data-engineer quality gate); ≤90s end-to-end ingestion latency for Tier 1 sources (SC-001); ≤500ms p95 dashboard queries (SC-004)  
**Constraints**: Australian Azure regions only (Constitution VI); signals queryable by jurisdiction, incident, source, category, time range; multi-tenant isolation enforced at storage layer; concurrent simulation + live operations  
**Scale/Scope**: 35+ data sources in seed catalogue; 7 pipeline classes; 4 simulation scenario templates; schema extensions to SignalEnvelope and provenance

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate Review

- **Life Safety First**: PASS. Circuit breaker (FR-016) degrades safely when sources fail. Monitoring Agent fallback routing (FR-020) maintains processing when governance registry is unavailable. Misinformation detection prevents unverified social signals from reaching Risk Assessment without review (FR-010a). Sensor range validation rejects implausible readings (US-3).
- **Multi-Agent Coordination With Clear Roles**: PASS. Ingestion pipelines normalise → Monitoring Agent classifies → typed handoffs to Risk Assessment → downstream agents. Each agent's interaction with ingested data is explicitly defined (FR-019 through FR-024). No agent ingests directly from external sources.
- **Data Trust, Provenance, and Freshness**: PASS. Every signal carries provenance (FR-015), confidence score derived from trust tier (FR-013), and freshness score (FR-014). Raw payloads retained for audit (FR-017). Content-hash deduplication prevents redundant signals (FR-018a). Contradictory signals flagged per Constitution Principle III.
- **Privacy, Security, and Regional Policy Compliance**: PASS. All storage in Australia East (FR-031). Multi-tenant partition isolation (FR-025). Encrypted at rest. Social media ingestion collects text only, no PII (FR-010). Field reports use officer ID, not personal data.
- **Multilingual, Accessible, and Actionable Communication**: PASS. This feature does not generate alerts. It feeds data to the Communication Agent which handles multilingual requirements. No new alert generation.
- **Cloud Platform**: PASS. Azure Container Apps, Cosmos DB, Blob Storage, Redis — all Azure services in Australian regions.
- **Quality Gates and Operational Readiness**: PASS. Simulation framework (FR-032–039) provides scenario-based testing for bushfire, cyclone, flood, severe storm. Structured observability (FR-018b) integrates with existing monitoring. Circuit breaker state changes logged. Dead-letter queue for failed ingestion.

### Post-Design Gate Review

- **Life Safety First**: PASS. The data model enforces safe degradation through CircuitBreakerState (transitions to `open` after 3 failures, exponential backoff). Tiered misinformation detection (FR-010a) prevents unverified social signals from reaching Risk Assessment — Tier 1 rules flag at ingestion, Tier 2 LLM evaluates at Monitoring Agent, and safe fallback holds escalated signals for human review when LLM is unavailable. IngestionAuditEntry provides immutable audit trail for every ingested signal. Sensor range validation rejects implausible readings before they reach any agent.
- **Multi-Agent Coordination With Clear Roles**: PASS. The pipeline framework creates normalised SignalEnvelopes that the Monitoring Agent consumes via event-driven triggers. Agent interaction is explicitly defined: Monitoring Agent classifies → typed handoff to Risk Assessment → downstream agents (Evacuation, Resource, Communication) operate on stored data only. Incident association at ingestion time (FR-019a) and retrospective back-fill (FR-019b) ensure signals are correctly routed. No agent ingests directly from external sources.
- **Data Trust, Provenance, and Freshness**: PASS. Every signal carries full provenance (collectionMethod, sourceUri, sourceTimestamp, collector). Confidence score computed from trust tier (tier 1 = 0.95, tier 6 = 0.3). Freshness score computed from time delta vs expected update frequency. Content-hash deduplication prevents redundant signals. Contradiction detection flags social signals contradicting authoritative sources. Raw payloads retained in Blob Storage for reproducibility.
- **Privacy, Security, and Regional Policy Compliance**: PASS. All storage in Australia East. Cosmos DB hierarchical partition key enforces tenant isolation (scope/jurisdictionId/dataSourceId). Blob Storage containers for raw payloads, binary assets, and audit are encrypted at rest. Social media ingestion collects text content only, no media download or PII extraction. Simulation data is partition-isolated from operational data, preventing accidental exposure.
- **Multilingual, Accessible, and Actionable Communication**: PASS. This feature does not generate alerts or public-facing content. Ingested signals feed downstream agents that handle multilingual requirements. No new communication workflows introduced.
- **Cloud Platform**: PASS. All infrastructure uses Azure services in Australia East: Cosmos DB, Blob Storage, Redis Cache, Container Apps, Application Insights. Ingestion worker deployed as a separate Container App with managed identity.
- **Quality Gates and Operational Readiness**: PASS. Simulation framework provides parametric generation for bushfire (FFDI model), flood (hydrograph curves), cyclone (track models), and severe storm scenarios. Structured observability (FR-018b) emits throughput, dedup rate, latency, circuit breaker state, dead-letter depth. Quickstart defines phased test-first validation (Phases A–I) covering every FR and SC. All 9 success criteria have concrete verification methods.

## Project Structure

### Documentation (this feature)

```text
specs/006-data-ingestion-storage/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── openapi-ingestion.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
apps/
├── api/
│   └── app/
│       ├── api/routes/
│       │   └── signals.py                 # MODIFY — add simulation run routes, signal query filters
│       ├── services/
│       │   └── ingestion/
│       │       ├── authoritative_ingestion.py  # MODIFY — refactor into pipeline framework
│       │       ├── iot_ingestion.py             # MODIFY — refactor into pipeline framework
│       │       ├── community_ingestion.py       # MODIFY — refactor into pipeline framework
│       │       ├── pipeline_base.py             # NEW — base pipeline class (polling, circuit breaker, dedup, provenance)
│       │       ├── normaliser_registry.py       # NEW — source-specific normaliser dispatch
│       │       ├── dedup_service.py             # NEW — content-hash deduplication (FR-018a)
│       │       ├── incident_association.py      # NEW — incident matching at ingestion time (FR-019a)
│       │       └── misinformation_detector.py   # NEW — Tier 1 rule-based heuristics (FR-010a)
│       ├── repositories/
│       │   ├── cosmos_scope.py            # MODIFY — add simulation partition scope
│       │   └── governance_repository.py   # EXISTING — governance data access
│       └── validators/
│           └── signal_envelope.py         # MODIFY — add simulationRunId to provenance
├── agents/
│   └── monitoring/
│       └── agent.py                       # MODIFY — add retrospective incident association (FR-019b),
│                                          #          Tier 2 LLM misinformation analysis (FR-010a)
├── ingestion/                             # NEW — background worker service for polling pipelines
│   ├── __init__.py
│   ├── worker.py                          # NEW — pipeline worker lifecycle (FR-001a)
│   ├── pipelines/
│   │   ├── __init__.py
│   │   ├── bom_warnings.py               # NEW — BoM XML warning pipeline (FR-004)
│   │   ├── bom_observations.py           # NEW — BoM JSON observation pipeline (FR-004)
│   │   ├── bom_radar.py                  # NEW — BoM radar image pipeline (FR-004, FR-009a)
│   │   ├── ga_earthquakes.py             # NEW — GA GeoJSON earthquake pipeline (FR-005)
│   │   ├── ga_hotspots.py               # NEW — GA Sentinel hotspot pipeline (FR-005)
│   │   ├── fire_service.py              # NEW — State fire service GeoJSON pipeline (FR-006)
│   │   ├── ses_flood.py                 # NEW — State SES flood intelligence pipeline (FR-007)
│   │   ├── sensor_aws.py               # NEW — BoM AWS sensor pipeline (FR-008)
│   │   ├── sensor_river_gauge.py        # NEW — River gauge pipeline (FR-008)
│   │   ├── sensor_epa_air.py            # NEW — EPA air quality pipeline (FR-008)
│   │   ├── satellite_sentinel.py        # NEW — Copernicus Sentinel pipeline (FR-009)
│   │   ├── satellite_himawari.py        # NEW — Himawari satellite pipeline (FR-009)
│   │   ├── social_twitter.py            # NEW — X/Twitter filtered stream pipeline (FR-010)
│   │   ├── social_facebook.py           # NEW — Facebook Graph API pipeline (FR-010)
│   │   ├── social_reddit.py             # NEW — Reddit API pipeline (FR-010)
│   │   ├── community_snap.py            # NEW — Snap Send Solve pipeline (FR-011)
│   │   └── ims_webeoc.py               # NEW — WebEOC/ICON IMS pipeline (FR-012)
│   ├── normalisers/
│   │   ├── __init__.py
│   │   ├── bom_xml_normaliser.py        # NEW — BoM XML to SignalEnvelope (XSD v1.7)
│   │   ├── geojson_normaliser.py        # NEW — GeoJSON FeatureCollection to SignalEnvelope
│   │   ├── json_observation_normaliser.py # NEW — generic JSON observations to SignalEnvelope
│   │   ├── cap_normaliser.py            # NEW — CAP/XML to SignalEnvelope
│   │   └── binary_metadata_normaliser.py # NEW — radar/satellite to metadata-only SignalEnvelope
│   └── simulation/
│       ├── __init__.py
│       ├── simulation_runner.py         # NEW — scenario orchestrator (FR-032, FR-037a)
│       ├── scenario_templates.py        # NEW — bushfire/flood/cyclone/storm templates (FR-038)
│       └── generators/
│           ├── __init__.py
│           ├── weather_generator.py     # NEW — BoM warning/forecast signal generator
│           ├── fire_generator.py        # NEW — fire service incident signal generator
│           ├── flood_generator.py       # NEW — hydrograph + flood warning generator (FR-033)
│           ├── cyclone_generator.py     # NEW — cyclone track + intensity generator (FR-033)
│           ├── sensor_generator.py      # NEW — sensor reading generator (FR-033)
│           ├── social_generator.py      # NEW — social media with misinformation mix (FR-036)
│           └── historical_overlay.py    # NEW — historical event replay with perturbation (FR-033a)
└── web/                                  # NO CHANGES — dashboard already displays signals

packages/
├── domain/
│   └── src/domain/
│       └── models/
│           ├── signal.py                # MODIFY — add simulation fields if needed
│           ├── ingestion_audit.py       # NEW — IngestionAuditEntry model
│           ├── simulation_scenario.py   # NEW — SimulationScenario model (FR-032)
│           └── simulation_run.py        # NEW — SimulationRun model (FR-039)
│       └── repositories/
│           └── signal_repository.py     # NEW — Cosmos DB signal persistence (FR-025). In shared
│                                        #        packages/domain so both API and ingestion worker import it
├── schemas/
│   └── signal-envelope.schema.json      # MODIFY — extend provenance with simulationRunId (FR-002a)
└── ui/                                   # NO CHANGES

infra/
└── bicep/
    └── main.bicep                        # MODIFY — add Cosmos DB containers, Blob containers,
                                          #          ingestion worker Container App

tests/
├── contract/
│   ├── test_bom_normaliser.py           # NEW — BoM XML normalisation contract tests
│   ├── test_geojson_normaliser.py       # NEW — GeoJSON normalisation contract tests
│   ├── test_dedup_service.py            # NEW — deduplication hash contract tests
│   ├── test_misinformation_detector.py  # NEW — Tier 1 heuristic rule tests
│   ├── test_incident_association.py     # NEW — ingestion-time incident matching tests
│   └── test_signal_storage.py           # NEW — storage partition isolation tests
├── integration/
│   ├── test_circuit_breaker.py          # NEW — circuit breaker state transition tests
│   ├── test_ingestion_pipeline.py       # NEW — end-to-end pipeline integration tests
│   └── test_simulation_runner.py        # NEW — simulation scenario generation tests
└── simulation/
    ├── test_bushfire_scenario.py         # NEW — bushfire scenario validation
    ├── test_flood_scenario.py           # NEW — flood scenario validation (hydrograph)
    ├── test_cyclone_scenario.py         # NEW — cyclone scenario validation
    └── test_storm_scenario.py           # NEW — severe storm scenario validation
```

**Structure Decision**: Extend the existing monorepo. Ingestion pipelines are added as a new `apps/ingestion/` service deployed as a separate Azure Container App background worker (FR-001a). Source-specific normalisers and simulation generators are co-located with the ingestion service. Domain models follow the existing pattern in `packages/domain/`. Schema extensions to `signal-envelope.schema.json` are minimal and additive. No new top-level projects beyond the ingestion worker.

## Complexity Tracking

No constitution violations or justified exceptions were identified during planning.
