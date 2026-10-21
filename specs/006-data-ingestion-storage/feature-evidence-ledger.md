# Feature Evidence Ledger — Spec 006 (AUD-001, AUD-006, AUD-007, AUD-004, AUD-005, AUD-008, AUD-009, AUD-010, AUD-011)

Date: 2026-09-16
Scope: specs/006-data-ingestion-storage only
Execution mode: local static + focused tests only (no deploy, no commit)

## Completed AUDs

- AUD-001: Completed in code and tests
- AUD-002: Completed in code and tests
- AUD-003: Completed in code and tests
- AUD-006: Completed in code and tests
- AUD-007: Completed in code and tests
- AUD-004: Completed in code and tests
- AUD-005: Completed in code and tests
- AUD-008: Completed in code and tests
- AUD-009: Completed in code and tests
- AUD-010: Completed in code and tests
- AUD-011: Completed in code and tests
- AUD-012: Completed in code and tests
- AUD-013: Completed in code and tests
- AUD-014: Completed in code and tests
- AUD-015: Completed in code and tests
- AUD-018: Completed in code and tests
- AUD-019: Completed in code and tests
- AUD-020: Completed in code and tests
- AUD-016: Completed in code and tests
- AUD-017: Completed in code and tests
- AUD-042: Completed in code and tests
- AUD-043: Completed in code and tests
- AUD-044: Completed in code and tests
- AUD-021: Completed for formal source coverage resolution and registry/test enforcement (external provider activation remains blocked where unverified)
- AUD-031: Completed in code and focused tests
- AUD-032: Completed in code and focused tests
- AUD-033: Completed in code and focused tests (calibration constants remain UNVERIFIED)
- AUD-034: Completed in code and focused tests
- AUD-035: Completed in code and focused tests (historical overlay fixture is repository-local only)
- AUD-036: Completed in code and focused tests
- AUD-037: Completed in code and focused tests
- AUD-038: Completed in code and focused tests (IaC alarm wiring remains external/policy-gated)
- AUD-040: Completed in code and focused tests
- AUD-041: Completed in harness/tests/evidence schema (staging run evidence remains UNVERIFIED until executed)

## Open Evidence Blockers

- External model calibration constants for flood/fire/cyclone remain UNVERIFIED in repo-local fixtures/config; no claim of authoritative calibration is made.
- Licensed historical overlay dataset provenance is still required for production evidence. Current fixture is synthetic and checked in for contract testing only.
- Provider-side feed-access verification evidence remains external and is not established by local tests.
- SC-001/SC-002 staging measurements remain UNVERIFIED until AMA_SPEC006_STAGING_MEASUREMENT opt-in runs produce raw evidence artifacts.
- AUD-039 remains GOVERNANCE-BLOCKED (2026-09-16): policy discovery parity and management-group inheritance are UNVERIFIED; non-Bicep authority/drift evidence only.

### AUD-021

- Machine-readable source/provider activation registry added with per-instance endpoint owner/format, attribution, auth/access/license/rate states, enabled flags, blockers, and substitution provenance.
  - specs/006-data-ingestion-storage/evidence/provider-source-activation-registry.json
- Added missing fire instances (SA/WA/TAS/ACT/NT) and SES instances (VIC/QLD) to pipeline configs and factory bindings, default disabled with explicit blockers until evidence exists.
  - apps/ingestion/pipeline_configs.py
  - apps/ingestion/pipeline_factory.py
- Corrected GA substitution attribution to USGS in runtime payload/provenance source naming.
  - apps/ingestion/pipelines/ga_earthquakes.py
- Added static tests to enforce required coverage, unique enabled identities, catalogue/registry coherence, disabled blockers, enabled verification fields, and truthful substitution/deviation flags.
  - tests/contract/test_spec006_aud021_provider_registry.py

### AUD-039 (non-Bicep automatable scope)

- Added spec-local governance gate artifacts with UNVERIFIED discovery and explicit GOVERNANCE-BLOCKED status for AI Impact Analyzer context.
  - specs/006-data-ingestion-storage/04-governance-constraints.md
  - specs/006-data-ingestion-storage/04-governance-constraints.json
- Added static checks for authoritative IaC path selection (azure.yaml -> infra/main.bicep), legacy template deprecation evidence, orphan legacy module detection, and current probe/queue-scaling drift flags.
  - tests/contract/test_spec006_aud039_governance_static.py

## Implementation Evidence

### AUD-031

- Scenario source matrix derived from seed catalogue with checked-in exclusions and relevance rules
  - apps/ingestion/simulation/scenario_source_matrix.py
  - specs/006-data-ingestion-storage/evidence/scenario-source-exclusions.json
- Scenario templates now generate activated sources from matrix and validate phase source membership
  - apps/ingestion/simulation/scenario_templates.py
- Runner source-type aware sensor generation (source id/type passed through registry)
  - apps/ingestion/simulation/simulation_runner.py
  - apps/ingestion/simulation/generators/sensor_generator.py
- Coverage and invalid-source/region tests
  - tests/simulation/test_scenario_source_matrix.py

### AUD-032

- Injectable simulation clock with now/sleep_until and interruptible scheduling loop
  - apps/ingestion/simulation/simulation_runner.py
- Strict compression validation (`time_compression_ratio > 0`) and per-source cadence scheduling
  - apps/ingestion/simulation/simulation_runner.py
- Run-phase state/progress accounting (`current_phase`, per-source counts/progress)
  - apps/ingestion/simulation/simulation_runner.py
- Boundary and abort behaviors verified in focused integration tests
  - tests/integration/test_simulation_runner.py

### AUD-033

- Versioned flood/fire/cyclone model payloads with explicit UNVERIFIED calibration provenance
  - apps/ingestion/simulation/generators/flood_generator.py
  - apps/ingestion/simulation/generators/fire_generator.py
  - apps/ingestion/simulation/generators/cyclone_generator.py
- Target-region sampling/validation utilities and root jurisdiction propagation
  - apps/ingestion/simulation/region_sampling.py
- Non-default model behavior, topology order, wind vector, pressure/RMW, and invalid-region tests
  - tests/simulation/test_flood_scenario.py
  - tests/simulation/test_bushfire_scenario.py
  - tests/simulation/test_cyclone_scenario.py

### AUD-034

- Deterministic ratio allocation with sum tolerance validation and per-run seeded RNG metadata
  - apps/ingestion/simulation/generators/social_generator.py
  - apps/ingestion/simulation/simulation_runner.py
- Target-region social coordinate sampling
  - apps/ingestion/simulation/generators/social_generator.py
- Default 14/3/3 count split and override/replay/concurrency tests
  - tests/simulation/test_social_generator.py

### AUD-035

- Historical overlay wired into runner; overlay replaces parametric generation per source when configured
  - apps/ingestion/simulation/simulation_runner.py
- Schema-legal overlay marker and recursive Point/Polygon/MultiPolygon coordinate transforms
  - apps/ingestion/simulation/generators/historical_overlay.py
- Source timestamp shift and severity plausibility bounds with explicit reject paths
  - apps/ingestion/simulation/generators/historical_overlay.py
- Checked-in overlay fixture and focused integration validation
  - specs/006-data-ingestion-storage/evidence/historical-overlay-sample.json
  - tests/integration/test_simulation_runner.py

### AUD-036

- 006 compatibility scenario/run endpoints over current simulation repository/service surface
  - apps/api/app/api/routes/simulations.py
- Durable compatibility document persistence and retrieval in simulation repository
  - apps/api/app/repositories/simulation_repository.py
- Real FastAPI contract tests for list/create/start/get/abort + validation/status cases
  - tests/contract/test_simulation_api_contract.py

### AUD-037

- Run manifest persistence (scenario/model/overlay/ratios/clock/ordered signals/decision refs) scoped by run
  - apps/ingestion/simulation/simulation_runner.py
- Fresh-instance replay from persisted manifest and explicit partial replay handling
  - apps/ingestion/simulation/simulation_runner.py
  - tests/integration/test_spec006_simulation_manifest_replay_aud037.py
- Scenario seeding replay now applies start/end filtering, pagination >10k, and time-compression offsets
  - apps/api/app/services/scenario_seeding_service.py
  - tests/contract/test_spec006_seed_replay_aud037.py

### AUD-038

- Bounded `PipelineMetrics` latency reservoir with rolling windows (5m dedup, 1h signals) and DLQ depth metric
  - apps/api/app/services/ingestion/pipeline_base.py
- Shared status transport store and mounted protected API route (`/ingestion/status`) for replica heartbeat aggregation
  - apps/api/app/services/ingestion/pipeline_status_store.py
  - apps/api/app/api/routes/ingestion_status.py
  - apps/api/app/api/router.py
- Worker status payload aligns with PipelineStatus fields plus truthful task state and stale/failed reporting
  - apps/ingestion/worker.py
- Injectable 15-minute logical partition utilization gauge seam (code-only, no IaC alarm edits)
  - apps/ingestion/telemetry.py
  - apps/ingestion/worker.py
- Focused contract tests for exact status fields, rolling expiry, stale heartbeat, failed/stopped tasks, and two-replica aggregation
  - tests/contract/test_ingestion_status_contract.py

### AUD-040

- Replaced tautological `>= 0` assertions with exact behavior assertions in ingestion integration tests
  - tests/integration/test_ingestion_pipeline.py
- Flood scenario contract test now performs real JSON Schema validation against canonical schema
  - tests/simulation/test_flood_scenario.py
- Simulation API contract unit checks now assert exact response shapes/values instead of key-presence loops
  - tests/contract/test_simulation_api_contract.py

### AUD-041

- Locust ingestion envelope repaired to canonical schema shape using catalogue source fixture defaults and auth header seam
  - tests/load/locustfile.py
  - tests/load/spec006_load_payload.py
- Added local fake-path functional tests validating canonical envelope schema and catalogue eligibility
  - tests/load/test_spec006_ingestion_harness.py
- Added staging-only SC-001/SC-002 harness tests with explicit opt-in, minimum sample counts, and raw output artifacts
  - tests/load/test_spec006_staging_harness.py
- Added machine-readable evidence record schema/template plus strict validator that blocks PASS without raw evidence and exact threshold computation
  - specs/006-data-ingestion-storage/evidence/load-evidence-record.schema.json
  - specs/006-data-ingestion-storage/evidence/load-evidence-record.template.json
  - tests/load/spec006_evidence_validator.py
  - tests/load/test_spec006_evidence_validator.py

### AUD-001

- Ingestion container import closure and runtime module path
  - apps/ingestion/Dockerfile
- Worker startup dependency validation and fail-closed behavior
  - apps/ingestion/worker.py
- Success audit write moved before success metrics/event publication
  - apps/api/app/services/ingestion/pipeline_base.py
- Docker static contract test
  - tests/contract/test_ingestion_worker_container_contract.py

### AUD-002

- API/manual ingestion now routes through canonical ingestion pipeline entry
  - apps/api/app/services/ingestion/authoritative_ingestion.py
  - apps/api/app/services/ingestion/pipeline_base.py
  - apps/api/app/api/routes/signals.py
- Legacy process-local signal persistence removed from AuthoritativeIngestionService
  - apps/api/app/services/ingestion/authoritative_ingestion.py
- Authenticated principal identity enforcement for collector/agency assertions
  - apps/api/app/services/ingestion/pipeline_base.py
  - apps/api/app/api/routes/signals.py
- Ingestion wrappers delegate to canonical async service path
  - apps/api/app/services/ingestion/iot_ingestion.py
  - apps/api/app/services/ingestion/community_ingestion.py

### AUD-003

- Signal ownership field added and persisted for agency-scoped access
  - packages/domain/src/domain/models/signal.py
  - packages/domain/src/domain/repositories/signal_wire.py
- Protected signal ingestion enforces simulation tenant and provenance binding
  - apps/api/app/services/ingestion/pipeline_base.py
  - apps/api/app/validators/signal_envelope.py
- GET/list scope intersection applies principal agency/jurisdiction and source eligibility
  - apps/api/app/api/routes/signals.py
- Repository query surfaces extended with ownership/jurisdiction predicates
  - apps/api/app/repositories/signal_repository.py
  - packages/domain/src/domain/repositories/signal_repository.py
- Isolation test for same signal IDs across live + three simulations
  - tests/contract/test_signal_storage.py

### AUD-006

- Public audit sink protocol
  - apps/api/app/services/ingestion/audit_sink.py
- Audit writer uses sink protocol append API, includes validation status/archival flag
  - apps/api/app/services/ingestion/audit_writer.py
- Append-only local and Azure append-blob behavior
  - apps/api/app/services/ingestion/blob_storage.py
  - apps/ingestion/blob_store.py
- Ingestion audit outcome set and invariants expanded
  - packages/domain/src/domain/models/ingestion_audit.py
- Focused audit append/concurrency/hour rollover tests
  - tests/contract/test_ingestion_audit_storage.py

### AUD-007

- Required compiled schema validator dependency in pipeline
  - apps/api/app/services/ingestion/pipeline_base.py
- Compile-once schema validator at worker startup
  - apps/ingestion/worker.py
- Raw evidence archival before normalization/validation
  - apps/api/app/services/ingestion/pipeline_base.py
- Durable DLQ creation for normalization/schema/model validation failures
  - apps/api/app/services/ingestion/pipeline_base.py
- Null optional field omission and non-empty sourceUri enforcement
  - apps/api/app/services/ingestion/pipeline_base.py
- Validation and sibling-continuation tests
  - tests/integration/test_ingestion_pipeline.py

### AUD-004

- Shared wire contract helper and HPK helper
  - packages/domain/src/domain/repositories/signal_wire.py
- API repository uses shared wire helper and 3-part point key handling
  - apps/api/app/repositories/signal_repository.py
- Domain repository uses shared wire helper and fan-out distinct reference IDs
  - packages/domain/src/domain/repositories/signal_repository.py
- Legacy shape backfill utility (dry-run/apply)
  - scripts/backfill_signal_hpk_shape.py
- Contract tests verify helper names against infra/main.bicep HPK paths and fan-out readability
  - tests/contract/test_signal_storage.py

### AUD-005

- In-memory store keyed by (scope, signal_id)
  - packages/domain/src/domain/repositories/signal_repository.py
- Explicit scope required for query and update paths
  - packages/domain/src/domain/repositories/signal_repository.py
  - apps/agents/monitoring/agent.py
- Scoped update_incident_id path implemented (memory + Cosmos query/replace)
  - packages/domain/src/domain/repositories/signal_repository.py
- Parity/isolation tests for duplicate IDs across scopes
  - tests/contract/test_signal_storage.py

### AUD-008

- Filename-only local seen caches removed from BoM warnings/radar/rss/tsunami/Himawari pipelines
  - apps/ingestion/pipelines/bom_warnings.py
  - apps/ingestion/pipelines/bom_radar.py
  - apps/ingestion/pipelines/bom_rss.py
  - apps/ingestion/pipelines/ga_tsunami.py
  - apps/ingestion/pipelines/satellite_himawari.py
- Version-aware canonical identity uses parsed product identity plus source version metadata (MDTM)
  - apps/ingestion/normalisers/bom_xml_normaliser.py
  - apps/ingestion/normalisers/cap_normaliser.py
  - apps/ingestion/pipelines/bom_warnings.py
  - apps/ingestion/pipelines/ga_tsunami.py
- Post-durable-mark protocol handled by dedup claim/commit in pipeline base
  - apps/api/app/services/ingestion/pipeline_base.py

### AUD-009

- Dedup protocol upgraded to try_claim/commit/release with Redis SET NX EX and bounded local expiry fallback
  - apps/api/app/services/ingestion/dedup_service.py
- Dedup keys are scope + pipeline namespaced and include hash identity
  - apps/api/app/services/ingestion/pipeline_base.py
- Effective dedup TTL from pipeline config is propagated into each claim/commit operation
  - apps/ingestion/pipeline_factory.py
  - apps/api/app/services/ingestion/pipeline_base.py
- Contract/integration tests assert contention, expiry, scoped independence, and TTL propagation
  - tests/contract/test_dedup_service.py
  - tests/integration/test_ingestion_pipeline.py

### AUD-010

- Added strict provider timestamp parser module with UTC-aware outputs and explicit parse errors
  - apps/ingestion/normalisers/timestamps.py
- Wired BoM/GeoJSON/JSON observation/binary/social/community/IMS/GA earthquake ingestion paths to parser outputs
  - apps/ingestion/normalisers/bom_xml_normaliser.py
  - apps/ingestion/normalisers/cap_normaliser.py
  - apps/ingestion/normalisers/geojson_normaliser.py
  - apps/ingestion/normalisers/json_observation_normaliser.py
  - apps/ingestion/normalisers/binary_metadata_normaliser.py
  - apps/ingestion/pipelines/ga_earthquakes.py
  - apps/ingestion/pipelines/social_twitter.py
  - apps/ingestion/pipelines/social_facebook.py
  - apps/ingestion/pipelines/social_reddit.py
  - apps/ingestion/pipelines/community_snap.py
  - apps/ingestion/pipelines/ims_webeoc.py
- Occurred time and publication/update/source timestamps are now carried separately where source data provides both
  - apps/ingestion/normalisers/geojson_normaliser.py
  - apps/ingestion/normalisers/json_observation_normaliser.py
  - apps/ingestion/normalisers/binary_metadata_normaliser.py

### AUD-011

- Element truthiness fallbacks removed in BoM/CAP parsing; explicit namespaced/non-namespaced finders implemented
  - apps/ingestion/normalisers/bom_xml_normaliser.py
  - apps/ingestion/normalisers/cap_normaliser.py
- Required AMOC/CAP fields validated with hard failure (no fabricated Canberra/time/source URI defaults)
  - apps/ingestion/normalisers/bom_xml_normaliser.py
  - apps/ingestion/normalisers/cap_normaliser.py
- CAP certainty now participates in confidence scoring and multi-info/area blocks are preserved
  - apps/ingestion/normalisers/cap_normaliser.py
- GA tsunami pipeline now dispatches to CAP normaliser
  - apps/ingestion/pipelines/ga_tsunami.py
- Product-schema validation seam added via optional XML schema validator callback
  - apps/ingestion/normalisers/bom_xml_normaliser.py

### AUD-012

- Persisted-signal to Monitoring chain now uses a tenant-scoped outbox enqueue + consumer path
  - apps/api/app/services/signal_accepted_workflow.py
  - apps/api/app/services/state_store.py
  - apps/api/app/services/ingestion/pipeline_base.py
- Outbox state captures per-correlation attempt_count/retry_count/result and terminal DLQ metadata
  - apps/api/app/services/signal_accepted_workflow.py
  - apps/api/app/services/state_store.py
- Monitoring-to-risk handoff now carries exact stored reference fields (signal_id, scope, jurisdiction_id, data_source_id)
  - apps/agents/monitoring/agent.py
  - packages/domain/src/domain/models/signal_accepted_event.py
- Risk retrieval now prefers exact HPK reference reads via repository method get_by_hpk
  - apps/agents/risk_assessment/pipeline.py
  - packages/domain/src/domain/repositories/signal_repository.py
  - apps/api/app/repositories/signal_repository.py
- Focused integration and unit coverage for outbox idempotency/gate outcomes and exact-reference retrieval
  - tests/integration/test_aud012_signal_accepted_outbox.py
  - tests/unit/test_risk_assessment_pipeline.py

### AUD-013

- Tier-1 misinformation detection is invoked in canonical ingestion flow for social/community before model persistence
  - apps/api/app/services/ingestion/pipeline_base.py
  - apps/ingestion/worker.py
- Detector context loading is scope/jurisdiction/category/time bounded via repository query surface
  - apps/api/app/services/ingestion/pipeline_base.py
- Tier-1 flags and result status are persisted into payload/provenance for downstream auditability
  - apps/api/app/services/ingestion/pipeline_base.py
- Integration tests validate scope-local context use and deterministic persistence behavior
  - tests/integration/test_ingestion_pipeline.py

### AUD-014

- Burst detection now enforces distinct-account threshold and suppresses on authoritative corroboration
  - apps/api/app/services/ingestion/misinformation_detector.py
- Duplicate amplification uses cosine similarity, earliest-post retention semantics, and cross-batch context support
  - apps/api/app/services/ingestion/misinformation_detector.py
- Contradiction logic validates authoritative corroboration context and handles non-point geometry checks safely
  - apps/api/app/services/ingestion/misinformation_detector.py
- Contract tests cover threshold boundaries, timestamp disorder, corroboration suppression, and context windows
  - tests/contract/test_misinformation_detector.py

### AUD-015

- Tier-2 escalation evaluation now produces structured decisions with strict parsing and fail-closed malformed/unavailable handling
  - apps/agents/monitoring/agent.py
- Monitoring pipeline persists Tier-2 decision/rationale before triage and blocks forwarding for non-allow decisions
  - apps/agents/monitoring/pipeline.py
  - apps/api/app/repositories/signal_repository.py
  - packages/domain/src/domain/repositories/signal_repository.py
- SignalAccepted workflow gate now uses shared monitoring decision path for escalated signals and preserves non-escalated compatibility
  - apps/api/app/services/signal_accepted_workflow.py
- Contract/unit/integration tests assert non-forwarding, persistence-before-delivery, and gate behavior parity
  - tests/contract/test_monitoring_escalation.py
  - tests/unit/test_monitoring_pipeline.py
  - tests/integration/test_aud007_signal_accepted_workflow.py

### AUD-018

- Pipeline freshness is now always computed server-side from normalized occurredAt plus expected_update_seconds
  - apps/api/app/services/ingestion/pipeline_base.py
- External/API envelopes cannot force freshness via payload body claims
  - apps/api/app/services/ingestion/pipeline_base.py
- Future skew beyond tolerance and unknown timestamp parsing are explicitly tagged in provenance validation notes
  - apps/api/app/services/ingestion/pipeline_base.py

### AUD-019

- Declarative measurement mapping added for AWS/EPA/river observations, including river value+parametertype mapping
  - apps/ingestion/normalisers/json_observation_normaliser.py
- Finite numeric enforcement added (reject NaN/inf), plus hard reject when no recognized measurement exists
  - apps/ingestion/normalisers/json_observation_normaliser.py
- Sydney coordinate fallback removed; station coordinates now required from record or station metadata seam
  - apps/ingestion/normalisers/json_observation_normaliser.py
- River gauge pipeline now passes station metadata cache and per-gauge flood thresholds for minor/moderate/major crossings
  - apps/ingestion/pipelines/sensor_river_gauge.py
- EPA observations and station metadata paths are split, with metadata attached to observation payloads
  - apps/ingestion/pipelines/sensor_epa_air.py

### AUD-020

- SignalEnvelope schema provenance now explicitly permits closed derived provenance fields consumed by runtime/dashboard
  - packages/schemas/signal-envelope.schema.json
- Signal domain model now stores first-class derived source values (source_name/source_kind/trust_tier/source_timestamp/raw_payload_uri)
  - packages/domain/src/domain/models/signal.py
- Pipeline enrichment now derives source identity/trust metadata from governance registry and rejects source mismatch/unknown
  - apps/api/app/services/ingestion/pipeline_base.py
- GeoJSON geometry handling preserves MultiPolygon and rejects unsupported/empty geometry (no [0,0] fallback)
  - apps/ingestion/normalisers/geojson_normaliser.py
- Snap road-closure report types map to infrastructure category
  - apps/ingestion/pipelines/community_snap.py

### AUD-016

- Incident association now uses scope-aware incident reader with jurisdiction + footprint intersection semantics
  - apps/api/app/services/ingestion/incident_association.py
- Fallback jurisdiction-only match only applies when incident footprint is absent and is annotated as low precision
  - apps/api/app/services/ingestion/incident_association.py
- Pipeline processing now uses associate_multi fanout and persists one signal record per matched incident with distinct IDs
  - apps/api/app/services/ingestion/pipeline_base.py

### AUD-017

- Unified SignalReadWrite protocol added for retrospective query/update operations
  - packages/domain/src/domain/repositories/signal_read_write.py
- Shared and API repositories now implement scoped query_unassociated and conditional update_incident_id with expected current incident guard
  - packages/domain/src/domain/repositories/signal_repository.py
  - apps/api/app/repositories/signal_repository.py
- Incident declaration route now triggers retrospective association with declaration event id, replay idempotency, scope, lookback, and per-signal outcomes
  - apps/api/app/api/routes/incidents.py
- Monitoring retrospective helper now performs conditional update semantics
  - apps/agents/monitoring/agent.py

### AUD-042

- Canonical simulation scope helper now adds `sim-` exactly once and rejects empty run IDs
  - apps/api/app/repositories/cosmos_scope.py
- Simulation runner scope assignment now delegates to the canonical helper
  - apps/ingestion/simulation/simulation_runner.py
- Production ingestion schema loader now enforces the v1 schema ID fail-closed guard
  - apps/ingestion/worker.py
- Signal envelope contract authority documented: v1 authoritative, v2 experimental/spec036-only
  - packages/schemas/signal-envelope.schema.json
  - packages/schemas/signal-envelope.schema.v2.json
- Versioned contract resolution table created for owner/status/migration/acceptance impacts
  - specs/006-data-ingestion-storage/contracts/contract-resolution.v1.json

### AUD-043

- Per-claim evidence manifest added with VERIFIED/UNVERIFIED/PARTIAL/DEFERRED classification
  - specs/006-data-ingestion-storage/evidence/claim-manifest.aud-043.json
- Owner-scoped six-heading HYP evidence stub created with unique ID and Not tested status
  - specs/006-data-ingestion-storage/evidence/HYP-044.md
- Spec HYP reference repaired to local evidence stub and cross-spec placeholder removed
  - specs/006-data-ingestion-storage/spec.md

### AUD-044

- `/api/signals` query parameters now enforce typed bounds and enums with deterministic 422 behavior
  - apps/api/app/api/routes/signals.py
- Naive `since` timestamps are normalized to UTC; malformed values now fail request validation
  - apps/api/app/api/routes/signals.py
- Repository query paths now enforce true total result limits (not page-size-only) and deterministic ordering
  - packages/domain/src/domain/repositories/signal_repository.py
- Unassociated query now supports explicit `limit` for memory/Cosmos parity
  - packages/domain/src/domain/repositories/signal_repository.py

## Automated Validation

Commands executed:

- py -3.14 -m compileall apps/ingestion/worker.py apps/api/app/services/ingestion/pipeline_base.py apps/api/app/services/ingestion/audit_writer.py apps/api/app/services/ingestion/blob_storage.py apps/ingestion/blob_store.py apps/api/app/repositories/signal_repository.py packages/domain/src/domain/repositories/signal_repository.py packages/domain/src/domain/repositories/signal_wire.py scripts/backfill_signal_hpk_shape.py
- py -3.14 -m pytest -q tests/contract/test_ingestion_worker_container_contract.py tests/contract/test_ingestion_audit_storage.py tests/contract/test_signal_storage.py tests/integration/test_ingestion_pipeline.py tests/integration/test_ingestion_signal_repository_wiring.py
- py -3.14 -m compileall apps/api/app/services/ingestion/authoritative_ingestion.py apps/api/app/services/ingestion/pipeline_base.py apps/api/app/api/routes/signals.py apps/api/app/services/ingestion/iot_ingestion.py apps/api/app/services/ingestion/community_ingestion.py packages/domain/src/domain/models/signal.py packages/domain/src/domain/repositories/signal_repository.py packages/domain/src/domain/repositories/signal_wire.py apps/api/app/repositories/signal_repository.py tests/integration/test_aud006_signal_semantics.py tests/contract/test_live_incident_contract.py tests/contract/test_signal_storage.py
- py -3.14 -m pytest -q tests/integration/test_aud006_signal_semantics.py tests/contract/test_live_incident_contract.py tests/contract/test_signal_storage.py
- python -m py_compile apps/ingestion/normalisers/timestamps.py apps/ingestion/normalisers/bom_xml_normaliser.py apps/ingestion/normalisers/cap_normaliser.py apps/ingestion/normalisers/geojson_normaliser.py apps/ingestion/normalisers/json_observation_normaliser.py apps/ingestion/normalisers/binary_metadata_normaliser.py apps/api/app/services/ingestion/dedup_service.py apps/api/app/services/ingestion/pipeline_base.py apps/ingestion/pipelines/bom_warnings.py apps/ingestion/pipelines/bom_radar.py apps/ingestion/pipelines/bom_rss.py apps/ingestion/pipelines/ga_tsunami.py apps/ingestion/pipelines/satellite_himawari.py apps/ingestion/pipelines/ga_earthquakes.py apps/ingestion/pipelines/social_twitter.py apps/ingestion/pipelines/social_facebook.py apps/ingestion/pipelines/social_reddit.py apps/ingestion/pipelines/community_snap.py apps/ingestion/pipelines/ims_webeoc.py apps/ingestion/pipeline_factory.py
- python -m pytest tests/contract/test_timestamp_parsers.py tests/contract/test_bom_normaliser.py tests/contract/test_geojson_normaliser.py tests/contract/test_dedup_service.py tests/integration/test_ingestion_pipeline.py -q
- py -3.14 -m py_compile apps/api/app/services/ingestion/pipeline_base.py tests/integration/test_ingestion_pipeline.py
- py -3.14 -m pytest -q tests/integration/test_ingestion_pipeline.py
- py -3.14 -m py_compile apps/ingestion/normalisers/json_observation_normaliser.py apps/ingestion/pipelines/sensor_river_gauge.py apps/ingestion/pipelines/sensor_epa_air.py tests/contract/test_json_observation_normaliser.py
- py -3.14 -m pytest -q tests/contract/test_json_observation_normaliser.py
- py -3.14 -m py_compile apps/api/app/repositories/cosmos_scope.py apps/ingestion/simulation/simulation_runner.py apps/ingestion/worker.py apps/api/app/api/routes/signals.py packages/domain/src/domain/repositories/signal_repository.py
- py -3.14 -m pytest -q tests/contract/test_spec006_contract_resolution_aud042.py tests/contract/test_spec006_evidence_manifest_aud043.py tests/contract/test_signal_query_validation_aud044.py tests/contract/test_signal_storage.py
- py -3.14 -m py_compile apps/api/app/services/ingestion/pipeline_base.py apps/api/app/validators/signal_envelope.py apps/ingestion/normalisers/geojson_normaliser.py apps/ingestion/pipelines/community_snap.py packages/domain/src/domain/models/signal.py tests/contract/test_signal_provenance_schema_contract.py tests/contract/test_geojson_normaliser.py
- py -3.14 -m pytest -q tests/contract/test_signal_provenance_schema_contract.py tests/contract/test_geojson_normaliser.py tests/integration/test_ingestion_pipeline.py
- py -3.14 -m py_compile apps/api/app/services/ingestion/incident_association.py apps/api/app/services/ingestion/pipeline_base.py tests/contract/test_incident_association.py tests/integration/test_ingestion_pipeline.py
- py -3.14 -m pytest -q tests/contract/test_incident_association.py tests/integration/test_ingestion_pipeline.py
- py -3.14 -m py_compile packages/domain/src/domain/repositories/signal_read_write.py packages/domain/src/domain/repositories/signal_repository.py apps/api/app/repositories/signal_repository.py apps/api/app/api/routes/incidents.py apps/agents/monitoring/agent.py tests/contract/test_incident_declaration_association.py
- py -3.14 -m pytest -q tests/contract/test_signal_storage.py tests/contract/test_incident_declaration_association.py tests/contract/test_incident_association.py
- py -3.14 -m pytest -q tests/unit/test_monitoring_pipeline.py tests/contract/test_monitoring_escalation.py tests/integration/test_aud007_signal_accepted_workflow.py
- py -3.14 -m pytest -q tests/integration/test_aud012_signal_accepted_outbox.py tests/unit/test_risk_assessment_pipeline.py tests/integration/test_ingestion_pipeline.py tests/unit/test_monitoring_pipeline.py tests/contract/test_monitoring_escalation.py tests/integration/test_aud007_signal_accepted_workflow.py
- py -3.14 -m py_compile apps/api/app/services/state_store.py apps/api/app/services/signal_accepted_workflow.py apps/api/app/services/ingestion/pipeline_base.py packages/domain/src/domain/models/signal_accepted_event.py apps/agents/monitoring/agent.py apps/agents/risk_assessment/pipeline.py packages/domain/src/domain/repositories/signal_repository.py apps/api/app/repositories/signal_repository.py tests/integration/test_aud012_signal_accepted_outbox.py tests/unit/test_risk_assessment_pipeline.py tests/integration/test_aud007_signal_accepted_workflow.py tests/contract/test_monitoring_escalation.py tests/unit/test_monitoring_pipeline.py

Result summary:

- Compile: pass
- Focused tests: 27 passed
- Compile (AUD-002/003 targeted): pass
- Focused tests (AUD-002/003 targeted): 21 passed
- Compile (AUD-008/009/010/011 targeted): pass
- Focused tests (AUD-008/009/010/011 targeted): 63 passed
- Focused tests (AUD-018 targeted): 11 passed
- Focused tests (AUD-019 targeted): 8 passed
- Focused tests (AUD-020 targeted): 26 passed
- Focused tests (AUD-016 targeted): 19 passed
- Focused tests (AUD-017 targeted): 19 passed
- Focused tests (AUD-015 targeted): 45 passed
- Focused tests (AUD-012 plus chain targeted): 72 passed

### Final Aggregate Gate (2026-09-16)

- Combined contract, integration, simulation, load, provider-registry, governance-static, and cross-spec evidence suite: 242 passed, 2 skipped, 2 warnings in 13.19s.
- Skips: two staging-only checks; no staging credentials or authorised 50,000-signals/hour run were available.
- Warnings: upstream Starlette `httpx` and AnyIO `BlockingPortal` deprecations; no spec-006 assertion warnings.
- Cross-spec HYP ownership: PASS after allocating HYP-044 to spec 006 and preserving spec 005 ownership of HYP-043.
- Spec-005 AUD-028 evidence validator: PASS.
- Actor catalogue and actor feature-evidence validators: PASS.
- Implementation status: 43 of 44 AUD findings complete; AUD-039 remains GOVERNANCE-BLOCKED and unchecked.

### AUD-039 Revision Pass (2026-09-16T03:01:23Z)

- Authenticated exact subscription-scope Azure Policy query: 0 assignments returned.
- Authenticated subscription-wide Azure Policy query: 0 assignments returned.
- Subscription: AI Impact Analyzer (`879c3e12-a379-45c7-b1b1-5a44f3cc2713`); tenant: `72f988bf-86f1-41af-91ab-2d7cd011db47`.
- Portal parity and management-group inheritance completeness: UNVERIFIED; the inspectable Portal session remained unauthenticated and no independent Portal count was available.
- Decision: repository governance instructions require STOP before Bicep planning or edits. AUD-039 remains open; no policy or deployment compliance is claimed.

## External / Non-automated Evidence Still Required

- Deployed ingestion image verification in runtime environment (managed identity, resolved imports, startup probes)
- Azure append-blob behavior against real storage account policies
- Cosmos live container data backfill run approval and execution evidence
- Production reconciliation evidence linking audit rows to persisted signals under operational load
- Live Azure Policy assignment inventory, management-group inheritance, effect classification, and Portal parity for AUD-039
- Authorised staging load evidence at 50,000 signals/hour
- Provider access/licensing attestations, calibration evidence, and production historical-overlay provenance

## Explicitly Out of Scope for This Batch

- Any Bicep edits
- docs/architecture/README.md changes
- Deployment, commit, or global audit README updates
