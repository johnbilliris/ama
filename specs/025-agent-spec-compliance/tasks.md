# Tasks: Agent Specification Compliance Audit

**Input**: Design documents from `/specs/025-agent-spec-compliance/`
**Prerequisites**: plan.md, spec.md (8 user stories, 23 FRs, 9 SCs), research.md (R1-R16), data-model.md, contracts/openapi-delta.md, quickstart.md
**Branch**: `025-agent-spec-compliance`
**Generated**: 2026-04-21

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1-US8)
- All file paths are relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add dependencies and scaffold test fixture structure before any implementation begins.

**Actor Agents to solicit**:
- `@solution-architect` -- INPUT: Dependency list and version constraints. OUTPUT: Validate compatibility with existing azure-identity, azure-cosmos, openai packages.
- `@infrastructure-devops` -- INPUT: New Azure SDK versions. OUTPUT: Confirm alignment with deployed Azure service API versions in AU East.
- `@qa-test-engineer` -- INPUT: Test fixture directory layout. OUTPUT: Review corpus structure and confirm coverage plan for SC-004 and SC-009.
- `@security-engineer` -- INPUT: New SDK dependencies. OUTPUT: Flag any known CVEs or vulnerable version ranges.

- [ ] T001 Add new Python dependencies (shapely, azure-ai-contentsafety>=1.0.0, azure-iot-device>=2.12.0, numpy) to apps/agents/pyproject.toml and add PyJWT (pyjwt[crypto]) to apps/api/pyproject.toml for JWT auth middleware (T013) -- verify compatibility with existing azure-identity, azure-cosmos, openai, httpx packages by running `pip install -e ".[dev]"` in both apps/agents/ and apps/api/
- [ ] T002 [P] Create test fixture directories: tests/fixtures/content_safety/{en,zh,ar,vi,el,it}/ and tests/fixtures/translation_quality/{en,zh,ar,vi,el,it}/ for SC-004 and SC-009 corpora (R15)
- [ ] T003 [P] Add new environment variables (COSMOS_DB_ENDPOINT, MANAGEMENT_API_KEY, DEAD_LETTER_POLL_INTERVAL_SECONDS, AZURE_CONTENT_SAFETY_ENDPOINT, AZURE_CONTENT_SAFETY_KEY, AZURE_OPENAI_EMBEDDING_DEPLOYMENT, IOT_HUB_CONNECTION_STRING, IOT_HUB_EVENT_GRID_ENDPOINT) to apps/agents/.env.example and apps/api/.env.example with placeholder values and inline comments

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Convert all 6 synchronous blocking retry call sites to async (R1) and add management API auth middleware (R10/FR-021). These changes are prerequisites for EVERY user story -- no story work can begin until this phase completes.

**CRITICAL**: All 6 async conversions and the auth middleware MUST be complete and tested before any Phase 3+ work begins.

**Actor Agents to solicit**:
- `@api-architect` -- INPUT: Async handoff conversion pattern and retry contract preservation. OUTPUT: Confirm `asyncio.gather()` concurrency model won't violate ordering guarantees within incident scope. Validate middleware dependency injection pattern.
- `@principal-engineer` -- INPUT: Sync-to-async migration across 6 call sites (R1). OUTPUT: Flag callers that assume synchronous completion (e.g., code reading handoff.status immediately after deliver returns). Review for race conditions.
- `@sre-engineer` -- INPUT: 2-second blocking cap (FR-002) and P95 <=5s SLO (SC-001). OUTPUT: Confirm telemetry events are compatible with existing Application Insights / Log Analytics queries.
- `@security-engineer` -- INPUT: JWT decoding logic, RBAC role enforcement, API key fallback. OUTPUT: Validate token validation (issuer, audience, expiry), role claim extraction, audit log structure.
- `@compliance-auditor` -- INPUT: Auth middleware design (Azure AD JWT in prod, API key local). OUTPUT: Confirm approach meets Australian government data handling and access control obligations.
- `@data-engineer` -- INPUT: Dead-letter Cosmos DB partition strategy. OUTPUT: Confirm partition key choice and query patterns for dead-letter container.

### Core Async Handoff Conversion (FR-001, FR-002, FR-003 / R1)

- [ ] T004 Convert `deliver_handoff_with_retry()` from synchronous `time.sleep()` to `async def` with `asyncio.sleep()` in apps/agents/common/handoffs.py -- change function signature to async, replace `time.sleep(retry_sleep)` at L131 with `await asyncio.sleep(retry_sleep)`, change `deliver` parameter type from `Callable` to `Callable[..., Awaitable]`, add `import asyncio`. Preserve all existing retry logic: max_retries, retry_window_seconds, retry_sleep calculation, dead-letter callback (R1 call site 1, L102-139)
- [ ] T005 Enforce 2-second maximum blocking cap per retry sequence using `asyncio.wait_for(delivery_coro, timeout=2.0)` wrapped around each individual delivery attempt in apps/agents/common/handoffs.py (FR-002)
- [ ] T006 Add structured telemetry logging in apps/agents/common/handoffs.py -- after each failed attempt: `logger.warning("handoff_retry", extra={"handoff_id": str, "attempt": int, "target_agent": str, "error_reason": str})`; on success: `logger.info("handoff_delivered", extra={"handoff_id": str, "retry_count": int, "duration_ms": float})`; on exhaustion: `logger.error("handoff_dead_lettered", extra={"handoff_id": str, "retry_count": int, "dead_letter_entry_id": str})` (FR-003)
- [ ] T007 Convert OCC retry in apps/agents/risk_assessment/versioning.py to async -- replace `time.sleep(jitter)` at L64-66 with `await asyncio.sleep(jitter)`, change containing method to `async def`, add `import asyncio`, update all callers in apps/agents/risk_assessment/pipeline.py to `await` (R1 call site 2)
- [ ] T008 [P] Convert OCC retry in apps/agents/communication/versioning.py to async -- replace `time.sleep(jitter)` at L67 with `await asyncio.sleep(jitter)`, change method to `async def`, update callers in apps/agents/communication/pipeline.py (R1 call site 3)
- [ ] T009 [P] Convert OCC retry in apps/agents/evacuation/versioning.py to async -- replace `time.sleep(jitter)` at L66 with `await asyncio.sleep(jitter)`, change method to `async def`, update callers in apps/agents/evacuation/pipeline.py (R1 call site 4)
- [ ] T010 [P] Convert OCC retry in apps/agents/resource_allocation/versioning.py to async -- replace `time.sleep(jitter)` at L78 with `await asyncio.sleep(jitter)`, change method to `async def`, update callers in apps/agents/resource_allocation/pipeline.py (R1 call site 5)
- [ ] T011 [P] Convert channel delivery retry in apps/agents/communication/delivery.py to async -- replace `time.sleep(backoff)` at L167 with `await asyncio.sleep(backoff)`, change `_deliver_with_retry()` and channel methods to `async def`, update caller `deliver()` to await (R1 call site 6)
- [ ] T012 Write unit tests verifying non-blocking behaviour in tests/unit/test_async_handoff_retry.py: (1) `deliver_handoff_with_retry()` returns control within 2s on failure, (2) three concurrent handoff deliveries via `asyncio.gather()` complete independently, (3) each retry attempt emits structured telemetry, (4) final success emits delivery_success event, (5) final failure emits dead_lettered event (FR-001, FR-002, FR-003, SC-002)

### Management API Auth Middleware (FR-021 / R10)

- [ ] T013 Implement `authorize_management()` FastAPI dependency in apps/api/app/middleware/auth.py -- production: decode JWT from `Authorization: Bearer <token>`, validate Azure AD issuer and audience via `jwt.decode()`, extract `roles` claim, require `operator` or `admin`; local dev: accept `X-API-Key` header matching MANAGEMENT_API_KEY env var; switch mode via `ENVIRONMENT` env var (R10)
- [ ] T014 Add structured security audit logging for all auth failures in apps/api/app/middleware/auth.py -- `logger.warning("management_auth_failure", extra={"reason": str, "ip": str, "path": str, "method": str})` for 401 and `logger.warning("management_auth_forbidden", extra={"identity": str, "roles": list, "required_role": str, "path": str})` for 403 (FR-021)
- [ ] T015 Write unit tests for auth middleware in tests/unit/test_management_auth.py: valid JWT with admin role passes, valid JWT with operator role passes, expired JWT returns 401, JWT with viewer role returns 403, valid API key passes in local mode, missing key returns 401, all failures logged as security audit events

**Checkpoint**: Foundation ready -- all 6 call sites async, 2-second blocking cap enforced, auth middleware functional. User story implementation can now begin.

---

## Phase 3: User Story 1 -- Non-Blocking Agent Pipeline Delivery (Priority: P1) MVP

**Goal**: When all retries for a handoff delivery are exhausted, persist to dead-letter store with automatic and manual redelivery, including a terminal `permanently_failed` state for entries that exhaust all recovery paths.

**Independent Test**: Trigger a pipeline run with a simulated downstream failure. Verify the handoff lands in dead-letter store, auto-redelivery fires when the target recovers, and the management API allows inspection and manual redelivery. Verify permanently_failed entries are read-only.

**Actor Agents to solicit**:
- `@data-engineer` -- INPUT: Dead-letter Cosmos DB collection schema, partition key strategy. OUTPUT: Confirm partition key (`/target_agent` for query efficiency), TTL policy for old entries, and indexing for status+target_agent compound queries.
- `@sre-engineer` -- INPUT: Redelivery poller backoff strategy (exponential, base=30s, max=300s). OUTPUT: Confirm retry storm prevention during agent flapping, validate poll interval defaults.
- `@observer-auditor` -- INPUT: Permanently_failed audit trail (auto_redeliver_attempts, manual_redeliver_attempts, failure_reasons, timestamps). OUTPUT: Confirm trail is complete and queryable for incident review (R14).
- `@operations-officer` -- INPUT: Dead-letter operational workflow (inspect, manual redeliver, permanent failure). OUTPUT: Validate the workflow matches AIIMS logistics officer escalation procedures.
- `@chaos-engineer` -- INPUT: Dead-letter behaviour spec under cascading multi-agent failures (edge case from spec.md). OUTPUT: Design chaos test scenario for simultaneous 3-agent outage with recovery stagger.
- `@api-architect` -- INPUT: Dead-letter REST contract (Sections 3a, 3b, 5a, 5b from openapi-delta.md). OUTPUT: Validate pagination, filtering, and 409 Conflict for permanently_failed.

### Implementation for User Story 1

- [ ] T016 [US1] Extend DeadLetterEntry model with `permanently_failed` status value, `auto_redeliver_attempts: int` (max 3), `manual_redeliver_attempts: int`, `failure_reasons: list[str]`, and `permanently_failed_at: datetime | None` fields in apps/agents/common/dead_letters.py (FR-003a, R14)
- [ ] T017 [US1] Implement dead-letter persistence in apps/agents/common/handoffs.py -- when `deliver_handoff_with_retry()` exhausts all retries, serialise the handoff via `model_dump(mode="json")` and write to Cosmos DB `dead_letters` collection with status=`dead_lettered`, `failed_at` timestamp, and `failure_reason` string (FR-003a)
- [ ] T018 [US1] Implement `DeadLetterRedeliveryPoller` background service in apps/agents/common/dead_letters.py -- async loop polling target agent `/health` endpoints at DEAD_LETTER_POLL_INTERVAL_SECONDS (default 30s) via httpx.AsyncClient; on healthy-recovered transition, query dead_lettered entries for that target_agent, re-invoke delivery with exponential backoff (`min(30 * 2^failures, 300)` seconds); increment `auto_redeliver_attempts` on each failure; cap at 3 auto attempts (FR-003a)
- [ ] T019 [US1] Register `DeadLetterRedeliveryPoller` as a background task in the agent service startup (apps/agents/common/startup.py), NOT in apps/api/app/main.py -- the poller calls `deliver_handoff_with_retry()` directly and must share the agent process. The API service handles only REST endpoints for dead-letter inspection and manual redelivery. Ensure the poller starts on agent service boot and gracefully cancels on shutdown (FR-003a)
- [ ] T020 [US1] Implement dead-letter inspection endpoint `GET /api/v1/dead-letters` in apps/api/app/routes/dead_letters.py -- query filters: incident_id, target_agent, status (including permanently_failed); pagination via limit (default 20) and offset; response includes full audit trail fields for permanently_failed entries (contracts Section 3a + 5a)
- [ ] T021 [US1] Implement manual redelivery endpoint `POST /api/v1/dead-letters/{handoff_id}/redeliver` in apps/api/app/routes/dead_letters.py -- fetch entry, reset status to `pending`, increment `manual_redeliver_attempts`, re-invoke async delivery; return 202 Accepted; return 404 if not found or not in dead_lettered status (contracts Section 3b)
- [ ] T022 [US1] Implement permanently_failed transition in apps/agents/common/dead_letters.py -- after 3 auto-redelivery failures AND 1 subsequent manual redelivery failure, set status=`permanently_failed`, record `permanently_failed_at` timestamp, append reason to `failure_reasons`. Entry becomes read-only: no further retries permitted (R14)
- [ ] T023 [US1] Return 409 Conflict with `{"error": "permanently_failed", "message": "...", "handoff_id": str}` when `POST /api/v1/dead-letters/{handoff_id}/redeliver` is called on a permanently_failed entry in apps/api/app/routes/dead_letters.py (contracts Section 5b)
- [ ] T024 [US1] Apply `authorize_management()` dependency to dead-letter redelivery endpoint -- require `operator` or `admin` role in apps/api/app/routes/dead_letters.py (FR-021)
- [ ] T025 [US1] Write unit tests for dead-letter lifecycle in tests/unit/test_dead_letter_redelivery.py: (1) persist on exhaustion with correct schema, (2) auto-redeliver on agent recovery, (3) exponential backoff between auto-redeliver attempts, (4) manual redeliver via API resets status, (5) permanently_failed after 3 auto + 1 manual, (6) 409 on redeliver of permanently_failed, (7) audit trail fields populated correctly
- [ ] T026 [US1] Write benchmark test in tests/benchmark/test_pipeline_latency.py -- simulate single-agent failure, measure P95 end-to-end pipeline latency from signal ingestion to final handoff delivery across 100 runs, assert <=5 seconds (SC-001)

**Checkpoint**: Dead-letter persistence, auto/manual redelivery, and permanently_failed terminal state all functional. Pipeline latency P95 <=5s under failure confirmed.

---

## Phase 4: User Story 2 -- Hazard Map Generation (Priority: P1)

**Goal**: Risk Assessment agent produces GeoJSON Polygon/MultiPolygon hazard maps from signal locations and severity, with admin-editable Cosmos DB radius lookup and named-location coordinate resolution for signals missing lat/lon.

**Independent Test**: Submit a hazard assessment request with location-tagged signals. Verify GeoJSON polygons in response. Submit a coordinate-less signal with device name and verify named-location resolution. Edit radius table via management API and verify next generation uses updated values without restart.

**Actor Agents to solicit**:
- `@risk-manager` -- INPUT: Seed radius values (bushfire 1000-10000m, flood 500-5000m, earthquake 2000-20000m, cyclone 5000-50000m, chemical_spill 200-2000m). OUTPUT: Approve or adjust values against AIDR hazard profiles for Australian conditions.
- `@bom-national` -- INPUT: Cyclone and flood radius ranges. OUTPUT: Validate against Bureau of Meteorology warning zone conventions and tropical cyclone category mapping.
- `@ga-national` -- INPUT: Earthquake radius ranges (2000-20000m by severity 1-5). OUTPUT: Validate alignment with Geoscience Australia Modified Mercalli Intensity zones.
- `@planning-officer` -- INPUT: Merged polygon output (MultiPolygon from overlapping signals). OUTPUT: Confirm output is actionable for AIIMS situation assessment; identify any missing spatial attributes.
- `@data-engineer` -- INPUT: Cosmos DB collection design for radius_lookup (partition key = hazard_type) and named_locations (partition key = location_id). OUTPUT: Confirm indexing, seed data loading, and query patterns.
- `@observer-auditor` -- INPUT: Named-location resolution logging. OUTPUT: Confirm audit trail captures source identifier and matched coordinates for traceability (FR-004a).
- `@local-government` -- INPUT: Named-location lookup table schema. OUTPUT: Validate that location_id naming conventions cover common municipal IoT sensor and gauge naming.

### Implementation for User Story 2

- [ ] T027 [P] [US2] Create `HazardRadiusLookup` Pydantic model in apps/agents/risk_assessment/hazard_radius.py -- fields: id (str, = hazard_type), hazard_type (str), radii (dict[str, float] mapping severity "1"-"5" to metres), last_updated (datetime), updated_by (str). Add Cosmos DB client wrapper for `radius_lookup` collection (R12)
- [ ] T028 [P] [US2] Create `NamedLocation` Pydantic model in apps/agents/risk_assessment/named_locations.py -- fields: location_id (str, partition key), display_name (str), latitude (float, WGS84), longitude (float, WGS84), last_updated (datetime). Add Cosmos DB client wrapper for `named_locations` collection (R11)
- [ ] T029 [US2] Implement Cosmos DB CRUD for radius_lookup collection in apps/agents/risk_assessment/hazard_radius.py -- `get_radius(hazard_type, severity) -> float`, `list_all() -> list[HazardRadiusLookup]`, `upsert(entry)`, `create(entry)` with 409 on duplicate; add seed data loader for 5 hazard types x severity 1-5 (bushfire: 1000/2500/5000/7500/10000, flood: 500/1500/3000/4500/5000, earthquake: 2000/5000/10000/15000/20000, cyclone: 5000/15000/30000/40000/50000, chemical_spill: 200/500/1000/1500/2000) from R12. Changes effective without restart.
- [ ] T030 [US2] Implement named-location coordinate resolution in apps/agents/risk_assessment/named_locations.py -- `resolve(location_id: str) -> tuple[float, float]` queries Cosmos DB by location_id; on match: return (lat, lon), log `logger.info("named_location_resolved", extra={"location_id": str, "lat": float, "lon": float})`; on miss: raise `ValidationError` specifying missing location identifier (FR-004a)
- [ ] T031 [US2] Implement `HazardMapGenerator` class in apps/agents/risk_assessment/hazard_map.py -- `generate(signals, hazard_type, severity_level)` method: (1) extract (lon, lat) from each signal, (2) query `get_radius(hazard_type, severity_level)` from Cosmos DB, (3) create polygon via `shapely.geometry.Point(lon, lat).buffer(radius_m / 111_320)` for approximate degree conversion, (4) generate `shapely.geometry.mapping()` for GeoJSON output. Each polygon includes boundary geometry, severity_level, hazard_type, and timestamp (FR-004, FR-005, R2)
- [ ] T032 [US2] Implement polygon merging for overlapping signals using `shapely.ops.unary_union()` in apps/agents/risk_assessment/hazard_map.py -- merge adjacent/overlapping polygons into MultiPolygon, preserve highest severity level across merged zones (R2)
- [ ] T033 [US2] Integrate `HazardMapGenerator` as new pipeline stage in apps/agents/risk_assessment/pipeline.py -- after assessment generation, call `generator.generate()`, populate `HazardAssessment.hazard_map` field with GeoJSON result (FR-004)
- [ ] T034 [US2] Add named-location fallback to pipeline pre-processing in apps/agents/risk_assessment/pipeline.py -- when signal has no geographic coordinates, call `NamedLocation.resolve(signal.location_id)`; on success, inject resolved coordinates into signal; on failure, reject signal with validation error and skip hazard map for that signal (FR-004a)
- [ ] T035 [US2] Implement radius lookup CRUD API under `/api/v1/admin/radius-lookup` in apps/api/app/routes/radius_lookup.py -- GET list (Section 4a), GET by hazard_type (Section 4b, 404 on miss), PUT update radii (Section 4c, admin only), POST create new type (Section 4d, admin only, 409 on duplicate). All per contracts Section 4
- [ ] T036 [US2] Apply `authorize_management()` dependency to radius lookup endpoints -- `operator` or `admin` role for GET reads, `admin` only for PUT/POST writes in apps/api/app/routes/radius_lookup.py (FR-021)
- [ ] T037 [US2] Write unit tests in tests/unit/test_hazard_map_generation.py: (1) single-point polygon from severity with correct radius, (2) multi-signal merge produces MultiPolygon, (3) valid GeoJSON structure (type, coordinates, properties), (4) severity propagation preserves highest, (5) unknown hazard type uses default radii, (6) EPSG:4326 coordinate bounds respected (SC-003)
- [ ] T038 [P] [US2] Write unit tests in tests/unit/test_named_location_lookup.py: (1) successful resolution returns (lat, lon), (2) failed lookup raises ValidationError with location identifier, (3) resolution logged with source identifier and coordinates (FR-004a)

**Checkpoint**: Risk Assessment produces spatial hazard maps with GeoJSON polygons. Radius table admin-editable via RBAC-protected API. Named-location lookup resolves coordinate-less signals.

---

## Phase 5: User Story 3 -- Content Safety for Alert Messages (Priority: P1)

**Goal**: Communication agent validates all outbound alerts through 3-layer pipeline: (a) Azure AI Content Safety, (b) factual consistency check, (c) tone-level alignment against Australian Warning System tiers -- with circuit breaker fallback to keyword-based check when Azure AI is unavailable.

**Independent Test**: Submit unsafe content in multiple languages and verify blocking. Submit legitimate emergency alerts and verify passage. Simulate Azure AI outage and verify circuit breaker trips after 3 failures, keyword fallback activates with review_flag=true, probe recovers after 60s cooldown.

**Actor Agents to solicit**:
- `@public-information-officer` -- INPUT: Tone-level alignment keywords and AWS tier mapping (Advice / Watch and Act / Emergency Warning). OUTPUT: Validate keyword sets correctly distinguish between warning tiers. Confirm review_flag=true workflow for fallback-validated messages.
- `@security-engineer` -- INPUT: Managed identity auth for Azure AI Content Safety (DefaultAzureCredential in prod). OUTPUT: Validate no API key leakage in production, confirm managed identity role assignment pattern.
- `@compliance-auditor` -- INPUT: Content safety approach for life-safety emergency alerts. OUTPUT: Confirm meets Australian Communications and Media Authority standards for emergency broadcasting.
- `@ai-ml-engineer` -- INPUT: Azure AI Content Safety SDK integration, severity threshold (<=2), confidence normalization (severity/6.0). OUTPUT: Validate threshold is appropriate for emergency context (not too aggressive blocking legitimate alerts).
- `@chaos-engineer` -- INPUT: Circuit breaker pattern (3-failure trip, 60s cooldown, single probe). OUTPUT: Validate behaviour under extended outage (hours), rapid flapping, and partial degradation.
- `@sre-engineer` -- INPUT: 5 telemetry events for circuit breaker state transitions. OUTPUT: Confirm events map to actionable alerts in monitoring dashboard.
- `@infrastructure-devops` -- INPUT: Bicep module for Azure AI Content Safety. OUTPUT: Validate resource provisioning in Australia East, managed identity assignment, network restrictions.
- `@accessibility-tester` -- INPUT: Content safety across 6 languages (en, zh, ar, vi, el, it) including RTL (Arabic). OUTPUT: Confirm Azure AI supports all 6 languages with consistent quality.
- `@qa-test-engineer` -- INPUT: Test corpus specification (R15: >=50 unsafe + >=50 safe x 6 languages, 6 violation categories). OUTPUT: Validate corpus composition covers edge cases (legitimate alerts with urgent language, false positive scenarios).

### Implementation for User Story 3

- [ ] T039 [US3] Implement Azure AI Content Safety client wrapper in apps/agents/common/content_safety.py -- instantiate `ContentSafetyClient(endpoint, DefaultAzureCredential())` when ENVIRONMENT=production, `ContentSafetyClient(endpoint, AzureKeyCredential(key))` for local dev; call `analyze_text(AnalyzeTextOptions(text=message))` for Hate, SelfHarm, Sexual, Violence categories; pass threshold: all categories severity <= 2 (R3, FR-007a)
- [ ] T040 [US3] Add `confidence: float` (normalized 0.0-1.0) and `validation_method: str` fields to ContentSafetyResult model in apps/agents/common/content_safety.py -- mapping: Azure AI `severity / 6.0`, factual `match=0.0 / mismatch=1.0`, tone `pass=0.0 / fail=1.0`; validation_method values: `"azure_ai"`, `"factual"`, `"tone"`, `"keyword_fallback"` (R13)
- [ ] T041 [US3] Implement factual consistency check in apps/agents/common/content_safety.py -- `validate_factual(alert_message, originating_signal) -> ContentSafetyResult`: verify hazard_type, severity_level, and location_name in the alert match the originating signal data passed through the pipeline; return confidence=0.0 on match, 1.0 on mismatch, validation_method="factual" (FR-007b)
- [ ] T042 [US3] Implement tone-level alignment check in apps/agents/common/content_safety.py -- `validate_tone(alert_message, warning_tier: str) -> ContentSafetyResult`: verify alert urgency language does not exceed the assigned Australian Warning System tier (Advice=calm informational, Watch and Act=action-oriented, Emergency Warning=immediate threat); operate on pre-translation English source text only; return validation_method="tone" (FR-007c, clarification Q13)
- [ ] T043 [US3] Create `ContentSafetyCircuitBreaker` class in apps/agents/common/circuit_breaker.py -- fields: state ("closed"|"open"|"half_open"), failure_count (int), trip_threshold (3), cooldown_seconds (60.0), last_failure_at (datetime|None), fallback_message_count (int); state machine: CLOSED -> (3 failures) -> OPEN -> (60s) -> HALF_OPEN -> (probe success) -> CLOSED / (probe fail) -> OPEN (R9)
- [ ] T044 [US3] Implement 5 structured telemetry events in apps/agents/common/circuit_breaker.py -- (1) `logger.warning("content_safety_circuit_opened", extra={"consecutive_failures": N, "cooldown_seconds": 60})`, (2) `logger.info("content_safety_probe_attempted")`, (3) `logger.info("content_safety_circuit_closed", extra={"open_duration_seconds": D})`, (4) `logger.warning("content_safety_probe_failed", extra={"next_probe_seconds": 60})`, (5) `logger.info("content_safety_fallback_summary", extra={"fallback_message_count": N})` on close (R9, FR-009)
- [ ] T045 [US3] Implement keyword-based fallback validation in apps/agents/common/content_safety.py -- when circuit breaker is OPEN/HALF_OPEN, route to keyword check; set `review_flag=true` on result; deliver message immediately without holding for human approval; return validation_method="keyword_fallback"; human reviewers MAY retroactively retract (FR-009, clarification Q6)
- [ ] T046 [US3] Integrate 3-layer content safety pipeline into Communication agent in apps/agents/communication/pipeline.py -- sequence: (1) circuit breaker wraps Azure AI Content Safety call, on open route to keyword fallback, (2) factual consistency check against originating signal data, (3) tone alignment check on English source text; any failure blocks message with categorised rejection reason; all 3 results logged (FR-007)
- [ ] T047 [US3] Write unit tests for Azure AI integration in tests/unit/test_content_safety_azure.py: mock SDK client, verify pass/fail categorisation by severity threshold, verify confidence normalization (severity 4 -> 0.667), verify DefaultAzureCredential path vs AzureKeyCredential path, verify multi-language support (FR-008)
- [ ] T048 [P] [US3] Write unit tests for factual consistency in tests/unit/test_content_safety_factual.py: matching fields pass with confidence=0.0, mismatched hazard_type fails with confidence=1.0, mismatched severity_level fails, mismatched location_name fails, partial mismatch handling
- [ ] T049 [P] [US3] Write unit tests for tone-level alignment in tests/unit/test_content_safety_tone.py: Advice-tier message with emergency language fails, Emergency Warning with appropriate urgency passes, Watch and Act tier boundary cases, verify operates on English source text only (not translated output)
- [ ] T050 [P] [US3] Write unit tests for circuit breaker in tests/unit/test_circuit_breaker.py: trip after 3 consecutive failures, cooldown timing (60s), probe success closes circuit, probe failure resets cooldown, fallback_message_count tracked correctly, all 5 telemetry events emitted with correct extra fields
- [ ] T051 [US3] Write integration test in tests/integration/test_content_safety_integration.py: end-to-end pipeline with mocked Azure AI -- unsafe message blocked, legitimate alert passed, circuit breaker trip and recovery, factual mismatch caught, tone violation caught
- [ ] T052 [US3] Create content safety test corpus in tests/fixtures/content_safety/ -- >=50 unsafe + >=50 safe messages per language (en, zh, ar, vi, el, it = 600+ messages); unsafe messages cover all 6 categories: hate speech, violence incitement, sexual content, self-harm, factual inconsistency, tone-level violation (R15, SC-004)
- [ ] T052b [US3] Write benchmark test in tests/benchmark/test_content_safety_accuracy.py -- run full test corpus (≥600 messages) through content safety pipeline, compute detection rate for unsafe messages and pass-through rate for safe messages, assert ≥95% unsafe detection rate and ≥99% safe pass-through rate across all 6 languages (SC-004)
- [ ] T053 [P] [US3] Author Azure AI Content Safety Bicep module in infra/bicep/content-safety.bicep -- provision `Microsoft.CognitiveServices/accounts` kind=`ContentSafety` in Australia East, system-assigned managed identity, output endpoint URL and resource ID (R3, constitution NON-NEG 2 data sovereignty)

**Checkpoint**: All outbound alerts pass through 3-layer content safety pipeline. Circuit breaker provides graceful fallback with 5 telemetry events. Test corpus covers 6 languages x 6 violation categories. Bicep module ready for deployment.

---

## Phase 6: User Story 4 -- Evacuation-to-Resource-Allocation Transport Handoff (Priority: P2)

**Goal**: Evacuation agent creates and delivers a handoff event to Resource Allocation containing transport requirements (vehicle type, capacity, pickup/dropoff, priority 1-5) when the evacuation plan includes non-ambulatory evacuees.

**Independent Test**: Trigger an evacuation plan with transport requirements. Verify Resource Allocation receives handoff with correct payload. Trigger all-ambulatory evacuation and verify no handoff is sent.

**Actor Agents to solicit**:
- `@logistics-officer` -- INPUT: Transport requirement fields (vehicle_type, capacity_needed, pickup/dropoff). OUTPUT: Validate field set matches AIIMS logistics coordination data requirements for vehicle dispatch.
- `@operations-officer` -- INPUT: Priority 1-5 triage ordering aligned with hazard severity. OUTPUT: Confirm priority mapping supports field deployment urgency decisions.
- `@transport` -- INPUT: Vehicle type categories ("bus", "ambulance", "wheelchair_transport"). OUTPUT: Validate categories cover Australian emergency evacuation fleet types including DACC assets.
- `@incident-commander` -- INPUT: Transport handoff from Evacuation to Resource Allocation. OUTPUT: Confirm handoff supports multi-agency coordination for large-scale evacuations across jurisdictions.
- `@health` -- INPUT: Vulnerability categories (mobility_impaired, elderly, general). OUTPUT: Validate categories align with Australian health sector evacuation priority classifications.
- `@api-architect` -- INPUT: Handoff payload schema. OUTPUT: Validate adherence to contracts Section 1a, confirm GeoJSON Point structure.

### Implementation for User Story 4

- [ ] T054 [US4] Create `TransportHandoffPayload` and `TransportRequirement` Pydantic models in apps/agents/evacuation/pipeline.py -- TransportRequirement: vulnerability_category (str), estimated_vehicles (int >=1), vehicle_type (str), capacity_needed (int >=1), pickup_location (GeoJSON Point), dropoff_location (GeoJSON Point), priority (int 1-5, 5=critical, aligned with hazard severity per R16); payload: transportRequirements (list[TransportRequirement]), evacuation_plan_id (str), zones_affected (list[str])
- [ ] T055 [US4] Implement pipeline Stage 9b in apps/agents/evacuation/pipeline.py -- after route planning, create `AgentHandoffEvent` with source_agent="evacuation", target_agent="resource_allocation", payload=TransportHandoffPayload; deliver via async `deliver_handoff_with_retry()` (R4, FR-010)
- [ ] T056 [US4] Implement zero-transport guard in apps/agents/evacuation/pipeline.py -- when evacuation plan generates zero transport requirements (all evacuees ambulatory), skip handoff and log `logger.info("transport_handoff_skipped", extra={"reason": "all_evacuees_ambulatory", "plan_id": str, "zones": list})` (US4 acceptance scenario 3)
- [ ] T057 [US4] Update Resource Allocation pipeline handler at apps/agents/resource_allocation/pipeline.py L267-270 -- extract `priority` integer field from each TransportRequirement, sort by priority descending (5 first), process higher-priority transports before lower in allocation planning (FR-011, R16)
- [ ] T058 [US4] Write unit tests in tests/unit/test_evacuation_transport_handoff.py: (1) handoff created with correct payload schema, (2) priority is int 1-5, (3) zero-transport guard skips handoff with log, (4) Resource Allocation receives and prioritises correctly (SC-005)
- [ ] T059 [US4] Write contract test in tests/contract/test_evacuation_resource_handoff.py -- validate handoff schema matches contracts Section 1a: all required fields present, GeoJSON Point structure valid, priority in range 1-5, transportRequirements non-empty

**Checkpoint**: Evacuation agent delivers transport requirements to Resource Allocation via async handoff. Priority triage ordering operational. Zero-transport edge case handled.

---

## Phase 7: User Story 5 -- Resource Allocation Dispatch Notifications (Priority: P2)

**Goal**: Resource Allocation agent creates handoff events to Communication agent containing dispatch details for each resource assignment, scoped per agency.

**Independent Test**: Complete a resource allocation plan assigning resources across multiple agencies. Verify each agency receives only its relevant dispatch notification via Communication agent handoff.

**Actor Agents to solicit**:
- `@field-coordinator` -- INPUT: Dispatch notification content (assignment_type, quantity, destination, resource_details). OUTPUT: Validate content meets ground-level coordination needs for field teams.
- `@operations-officer` -- INPUT: Per-agency scoping of dispatch notifications. OUTPUT: Confirm scoping prevents information overload and supports multi-agency operational tempo.
- `@logistics-officer` -- INPUT: Assignment fields (personnel/supply, quantity). OUTPUT: Validate field granularity supports logistics tracking and resource accountability.
- `@public-information-officer` -- INPUT: Dispatch routing through Communication agent. OUTPUT: Confirm notifications benefit from multilingual translation and content safety pipeline.
- `@community-ngos` -- INPUT: Dispatch notification format. OUTPUT: Validate format supports Red Cross and Salvation Army evacuation centre operations and volunteer coordination.
- `@local-government` -- INPUT: Dispatch notification per agency. OUTPUT: Confirm compatibility with municipal emergency management plan activation procedures.
- `@api-architect` -- INPUT: Handoff payload schema. OUTPUT: Validate adherence to contracts Section 1b.

### Implementation for User Story 5

- [ ] T060 [US5] Create `DispatchHandoffPayload` and `DispatchAssignment` Pydantic models in apps/agents/resource_allocation/pipeline.py -- DispatchAssignment: assignment_type ("personnel"|"supply"), quantity (int >=1), destination (GeoJSON Point), destination_name (str), assigned_agency (str), priority (str), resource_details (str); payload: dispatch_type="operational_dispatch", assignments (list[DispatchAssignment]), plan_id (str), incident_id (str)
- [ ] T061 [US5] Implement pipeline Stage 8b in apps/agents/resource_allocation/pipeline.py -- after deployment plan persisted, group assignments by `assigned_agency`, map transport priority int (1–5) to dispatch priority str using defined mapping (5→"critical", 4→"high", 3→"moderate", 1–2→"low"), create one `AgentHandoffEvent` per agency with target_agent="communication" and DispatchHandoffPayload containing only that agency's assignments; deliver each via async `deliver_handoff_with_retry()` (R5, FR-012)
- [ ] T062 [US5] Add validation and logging for each dispatch notification in apps/agents/resource_allocation/pipeline.py -- validate all FR-013 fields present (assignment_type, quantity, destination, assigned_agency); log `logger.info("dispatch_notification_sent", extra={"agency": str, "assignment_count": int, "plan_id": str})` per handoff
- [ ] T063 [US5] Write unit tests in tests/unit/test_resource_dispatch_handoff.py: (1) one handoff per agency from multi-agency plan, (2) each payload contains only that agency's assignments, (3) all FR-013 fields present, (4) Communication unavailable triggers non-blocking retry via dead-letter (SC-006)
- [ ] T064 [US5] Write contract test in tests/contract/test_resource_communication_handoff.py -- validate handoff schema matches contracts Section 1b: dispatch_type value, GeoJSON Point structure, assignment_type enum, non-empty assignments list

**Checkpoint**: All resource deployment plans produce per-agency dispatch notifications delivered to Communication agent.

---

## Phase 8: User Story 6 -- Dynamic Road Network for Evacuation Routing (Priority: P3)

**Goal**: Monitoring agent classifies road closure signals and delivers them to Evacuation agent, which updates road network graph weights before next route computation. Reopening signals restore original weights.

**Independent Test**: Load road network, inject road closure signal from Monitoring. Verify Evacuation excludes closed segment. Send reopening signal and verify restoration.

**Actor Agents to solicit**:
- `@operations-officer` -- INPUT: Road closure classification criteria. OUTPUT: Validate classification covers field-reported conditions (flood water, debris, structural damage).
- `@transport` -- INPUT: Road closure/reopening signal types. OUTPUT: Confirm types cover Australian road authority reporting standards (VicRoads, RMS, DTMR).
- `@incident-commander` -- INPUT: Route update propagation. OUTPUT: Confirm updates propagate to all active evacuation plans for affected zones.
- `@planning-officer` -- INPUT: "No viable route" reporting when all routes blocked. OUTPUT: Confirm this enables informed AIIMS re-planning (alternative shelter, airlift).
- `@data-engineer` -- INPUT: Road segment spatial matching (nearest-edge lookup via Shapely). OUTPUT: Review spatial index approach for O(log n) lookup performance.
- `@state-government` -- INPUT: Road closure signal integration. OUTPUT: Validate alignment with state road authority notification protocols (e.g., VicTraffic API format).

### Implementation for User Story 6

- [ ] T065 [US6] Create `RoadClosureSignalPayload` Pydantic model in apps/agents/monitoring/pipeline.py -- fields: closure_type ("road_closure"|"road_reopening"), road_segment_id (str|None), location (GeoJSON Point|None for nearest-edge lookup), road_name (str|None), reason (str), source_signal_id (str)
- [ ] T066 [US6] Add road-closure signal classification in Monitoring pipeline in apps/agents/monitoring/pipeline.py -- detect signals matching road closure/reopening patterns by signal_type and keywords; extract road_segment_id or location coordinates for spatial matching (R6)
- [ ] T067 [US6] Create Monitoring-to-Evacuation handoff for road closure signals in apps/agents/monitoring/pipeline.py -- create `AgentHandoffEvent` with source_agent="monitoring", target_agent="evacuation", payload=RoadClosureSignalPayload; deliver via async `deliver_handoff_with_retry()` (contracts Section 1c, FR-014)
- [ ] T068 [US6] Add road closure handoff handler in Evacuation pipeline in apps/agents/evacuation/pipeline.py -- on receipt, resolve road_segment_id: direct match if provided, else nearest-edge Shapely spatial lookup from location coordinates; call `apply_closure(edge_id, reason)` for closures or `remove_closure(edge_id)` for reopenings before route computation (FR-014, R6)
- [ ] T069 [US6] Add audit logging for road network modifications in apps/agents/evacuation/pipeline.py -- `logger.info("road_network_modified", extra={"action": "closure"|"reopening", "signal_id": str, "road_segment_id": str, "road_name": str|None})` (FR-015)
- [ ] T070 [US6] Write unit tests in tests/unit/test_road_network_dynamic.py: (1) closure signal removes/penalises segment from graph, (2) reopening restores original weight, (3) all-routes-blocked reports "no viable route" for zone-shelter pair, (4) audit log emitted with signal ID and segment ID (SC-007)

**Checkpoint**: Evacuation routes dynamically adapt to road closures and reopenings. Full audit trail for every network modification.

---

## Phase 9: User Story 7 -- IoT Signal Ingestion Adapter (Priority: P3)

**Goal**: Monitoring agent accepts IoT device signals via Azure IoT Hub + Event Grid, normalises into SignalEnvelope format, and deduplicates at-least-once delivery using (device_id, sequence_number) composite key with 30-second in-memory window.

**Independent Test**: Publish IoT signal via Event Grid webhook. Verify normalised SignalEnvelope arrives in monitoring pipeline within 5 seconds. Send duplicates and verify deduplication.

**Actor Agents to solicit**:
- `@data-engineer` -- INPUT: IoT Hub, Event Grid, Container App webhook architecture. OUTPUT: Validate message flow, confirm Cosmos DB not needed for dedup at 10K msg/s (in-memory sufficient).
- `@infrastructure-devops` -- INPUT: Bicep module for IoT Hub + Event Grid subscription. OUTPUT: Validate S1 tier for 10K msg/s throughput, Event Grid subscription routing, Container App endpoint registration.
- `@sre-engineer` -- INPUT: In-memory dedup at 10K msg/s with 30s TTL window. OUTPUT: Confirm memory growth bounded (~300K entries max at 10K/s x 30s), TTL eviction prevents unbounded growth.
- `@bom-national` -- INPUT: sensor_type field values. OUTPUT: Validate values (water_level, wind_speed, temperature) align with Bureau of Meteorology automatic weather station telemetry.
- `@utility` -- INPUT: sensor_type coverage. OUTPUT: Confirm includes utility-sector sensors (water_level, air_quality, seismic, power_status).
- `@docker-container-engineer` -- INPUT: Container App endpoint for Event Grid webhook. OUTPUT: Validate Event Grid subscription validation handshake handling and TLS configuration.
- `@solution-architect` -- INPUT: SignalEnvelope normalisation. OUTPUT: Confirm normalised output is indistinguishable from HTTP-sourced signals in downstream pipeline processing.

### Implementation for User Story 7

- [ ] T071 [US7] Create `IoTSignalMessage` Pydantic model in apps/agents/monitoring/iot_adapter.py -- fields: device_id (str), sequence_number (int), message_id (str), timestamp (datetime), sensor_type (str), value (float), unit (str), location (GeoJSON Point dict), metadata (dict)
- [ ] T072 [US7] Implement IoT message normaliser in apps/agents/monitoring/iot_adapter.py -- `normalise(iot_msg: IoTSignalMessage) -> SignalEnvelope`: map device_id to source_id, sensor_type to signal_type, location to coordinates, timestamp to ingested_at; preserve metadata in envelope extras (FR-017)
- [ ] T073 [US7] Implement in-memory deduplication in apps/agents/monitoring/iot_adapter.py -- dict keyed by `(device_id, sequence_number)` tuple with 30-second TTL; use `asyncio.get_event_loop().call_later(30, evict_func)` for TTL-based eviction; silently drop messages with existing key before pipeline entry (FR-018, R7 -- composite key per clarification Q11)
- [ ] T074 [US7] Implement Event Grid webhook endpoint in apps/agents/monitoring/iot_adapter.py -- handle `Microsoft.Devices.DeviceTelemetry` events; extract IoT message from `event.data.body`; handle Event Grid subscription validation handshake (SubscriptionValidation event type); return 200 on success (contracts Section 2a, FR-016)
- [ ] T075 [US7] Integrate IoT adapter with Monitoring pipeline in apps/agents/monitoring/pipeline.py -- register webhook endpoint at `/api/v1/iot/telemetry`; route normalised SignalEnvelopes into existing pipeline alongside HTTP-sourced signals (FR-016)
- [ ] T076 [P] [US7] Author Azure IoT Hub + Event Grid Bicep module in infra/bicep/iot-hub.bicep -- provision `Microsoft.Devices/IotHubs` S1 tier for 10K msg/s in Australia East; provision Event Grid subscription routing `Microsoft.Devices.DeviceTelemetry` events to monitoring agent Container App HTTPS endpoint (R7)
- [ ] T077 [US7] Write unit tests in tests/unit/test_iot_adapter.py: (1) normalisation produces valid SignalEnvelope with correct field mapping, (2) dedup drops duplicate (device_id, sequence_number) within 30s, (3) dedup allows same sequence_number from different device_id, (4) TTL eviction after 30s allows key reuse, (5) Event Grid validation handshake returns correct response (SC-008)

**Checkpoint**: IoT devices publish via IoT Hub, Event Grid, monitoring adapter, normalised SignalEnvelope, pipeline. Duplicates eliminated. <=5s ingestion latency.

---

## Phase 10: User Story 8 -- Translation Quality Validation (Priority: P3)

**Goal**: Replace bag-of-words cosine similarity with embedding-based semantic similarity using Azure OpenAI text-embedding-3-small for back-translation quality scoring. Flag translations below 0.85 threshold for human review.

**Independent Test**: Translate an alert, back-translate, score. Semantically accurate but rephrased translations score >=0.85. Meaning-altering translations (critical term swaps) score <0.85 and are flagged.

**Actor Agents to solicit**:
- `@ai-ml-engineer` -- INPUT: text-embedding-3-small model for multilingual semantic similarity. OUTPUT: Validate embedding dimension, confirm cosine similarity is appropriate distance metric, review any known language-pair weaknesses.
- `@public-information-officer` -- INPUT: 0.85 threshold for translation quality. OUTPUT: Confirm threshold balances quality assurance with delivery latency for life-safety alerts (too strict = delayed alerts, too lenient = meaning drift).
- `@accessibility-tester` -- INPUT: Embedding similarity across 6 languages including RTL (Arabic). OUTPUT: Validate no systematic bias against specific language pairs.
- `@qa-test-engineer` -- INPUT: Test corpus specification (R15: >=30 pairs per language, >=10 preserving, >=10 altering). OUTPUT: Review corpus composition for edge cases (medical terminology, geographic directions, severity-level terminology).

### Implementation for User Story 8

- [ ] T078 [US8] Replace `_compute_similarity()` in apps/agents/communication/delivery.py -- change from word-frequency cosine similarity to `client.embeddings.create(model="text-embedding-3-small", input=[original, back_translated])`, compute cosine similarity on returned vectors using `numpy.dot(a, b) / (numpy.linalg.norm(a) * numpy.linalg.norm(b))`; threshold remains >=0.85 (FR-019, R8)
- [ ] T079 [US8] Add graceful fallback in apps/agents/communication/delivery.py -- if Azure OpenAI embedding endpoint is unavailable (ConnectionError, Timeout), fall back to existing word-frequency method and log `logger.warning("embedding_fallback", extra={"reason": "endpoint_unavailable"})` (R8 graceful degradation)
- [ ] T080 [US8] Ensure translations scoring below 0.85 are flagged for human review in apps/agents/communication/delivery.py -- set review flag and log `logger.warning("translation_quality_below_threshold", extra={"score": float, "target_language": str, "alert_id": str})` (FR-020)
- [ ] T081 [US8] Write unit tests in tests/unit/test_translation_embedding.py: (1) mock embedding client, verify cosine similarity computation, (2) semantically equivalent texts score >=0.85, (3) meaning-altered texts score <0.85, (4) fallback to word-frequency on endpoint failure with warning log, (5) below-threshold flagged for review (SC-009)
- [ ] T082 [US8] Create translation quality test corpus in tests/fixtures/translation_quality/ -- >=30 pairs per language (6 languages = 180+ pairs), >=10 meaning-preserving (synonym substitution, reordering), >=10 meaning-altering (critical term swaps: "north" to "south", severity changes, directional inversions) (R15, SC-009)

**Checkpoint**: Translation quality scoring reflects semantic accuracy. Meaning-preserving rephrasings pass. Critical meaning changes caught and flagged.

---

## Phase 11: Polish and Cross-Cutting Concerns

**Purpose**: Infrastructure integration, ADR documentation, and full validation across all user stories.

**Actor Agents to solicit**:
- `@infrastructure-devops` -- INPUT: Bicep module references in main.bicep. OUTPUT: Validate deployment order, parameter file consistency, managed identity role assignments.
- `@observer-auditor` -- INPUT: ADR drafts for dismissed findings F02 and F07. OUTPUT: Confirm justifications are audit-trail sufficient and discoverable.
- `@qa-test-engineer` -- INPUT: Full test suite results. OUTPUT: Identify untested edge cases or missing coverage.
- `@compliance-auditor` -- INPUT: All 23 FRs and 9 SCs implementation status. OUTPUT: Final compliance sign-off against audit findings.
- `@incident-commander` -- INPUT: All 8 compliance fixes from AIIMS coordination perspective. OUTPUT: Confirm changes support Incident Controller multi-agency response coordination.
- `@docker-container-engineer` -- INPUT: Dockerfile changes for new SDK dependencies. OUTPUT: Validate image size impact, suggest multi-stage optimisations if needed.
- `@speckit.analyze` -- INPUT: spec.md, plan.md, tasks.md artifacts. OUTPUT: Cross-artifact consistency check.

- [ ] T083 [P] Update infra/main.bicep to add module references for infra/bicep/content-safety.bicep and infra/bicep/iot-hub.bicep with Australia East region parameters and managed identity role assignments
- [ ] T084 [P] Update infra/main.parameters.development.json, infra/main.parameters.staging.json, and infra/main.parameters.production.json with new resource configuration parameters for Content Safety and IoT Hub
- [ ] T085 Run full test suite: `python -m pytest tests/unit/ tests/contract/ tests/integration/ tests/benchmark/ -v --tb=short` -- verify all tests pass, no regressions in existing tests
- [ ] T086 Validate quickstart.md steps end-to-end: install dependencies, set env vars, run each of the 13 test commands, verify all execute successfully
- [ ] T087 [P] Write ADR for dismissed finding F02 in docs/aidr/decisions/ -- document deliberate separation of signal collection (upstream adapters) and signal triage (Monitoring agent) responsibilities; reference constitution II-A AIIMS functional alignment
- [ ] T088 [P] Write ADR for dismissed finding F07 in docs/aidr/decisions/ -- document intentional deviation from "autonomous" spec language; safety rationale for human-in-the-loop approval on outbound public alerts; reference constitution NON-NEG 1

**Checkpoint**: All infrastructure modules connected. ADRs documented. Full test suite green. Compliance audit complete.

---

## Dependencies and Execution Order

### Phase Dependencies

```
Phase 1: Setup                                   > No dependencies
Phase 2: Foundational                            > Depends on Phase 1
Phase 3: US1 Non-Blocking Delivery (P1)          > Depends on Phase 2 (async handoff)
Phase 4: US2 Hazard Map Generation (P1)          > Depends on Phase 2 (auth middleware for radius API)
Phase 5: US3 Content Safety (P1)                 > Depends on Phase 2 (async handoff for pipeline)
Phase 6: US4 Evacuation Transport Handoff (P2)   > Depends on Phase 2 (async handoff)
Phase 7: US5 Dispatch Notifications (P2)         > Depends on Phase 2 (async handoff)
Phase 8: US6 Dynamic Road Network (P3)           > Depends on Phase 2 (async handoff)
Phase 9: US7 IoT Adapter (P3)                    > Depends on Phase 2 (async handoff + infra)
Phase 10: US8 Translation Quality (P3)           > Depends on Phase 2 only (independent)
Phase 11: Polish                                 > Depends on Phases 3-10 all complete
```

### User Story Independence

- **US1 (P1)**: After Phase 2 -- no dependency on other stories
- **US2 (P1)**: After Phase 2 -- independent of US1
- **US3 (P1)**: After Phase 2 -- independent of US1, US2
- **US4 (P2)**: After Phase 2 -- independent; integrates with US1 dead-letter for retry failures
- **US5 (P2)**: After Phase 2 -- independent; integrates with US4 but independently testable
- **US6 (P3)**: After Phase 2 -- independent
- **US7 (P3)**: After Phase 2 -- independent; requires infra/bicep/iot-hub.bicep for integration testing
- **US8 (P3)**: After Phase 2 -- fully independent

### Within Each User Story

1. Pydantic models/entities FIRST
2. Core business logic (services, generators, adapters)
3. Pipeline integration (stage wiring, handler registration)
4. API endpoints (REST routes with auth middleware)
5. Unit tests, contract tests, integration tests, benchmark tests

### Agent Involvement Matrix

| Agent | Stories | Role |
|-------|---------|------|
| `@solution-architect` | Setup, US7 | Dependency validation, normalisation consistency |
| `@api-architect` | Foundation, US1, US4, US5, US6 | Handoff contracts, REST endpoints, middleware |
| `@data-engineer` | Foundation, US1, US2, US7 | Cosmos DB design, IoT architecture |
| `@sre-engineer` | Foundation, US1, US3, US7 | SLO validation, circuit breaker monitoring, scale |
| `@security-engineer` | Foundation, US3 | RBAC, managed identity, audit logging |
| `@principal-engineer` | Foundation | Async patterns, race condition review |
| `@ai-ml-engineer` | US3, US8 | Azure AI Content Safety, embedding similarity |
| `@chaos-engineer` | US1, US3 | Cascading failure testing, circuit breaker validation |
| `@infrastructure-devops` | Setup, US3, US7, Polish | Bicep modules, Azure provisioning |
| `@qa-test-engineer` | Setup, US3, US8, Polish | Test corpus, fixture structure, full validation |
| `@compliance-auditor` | Foundation, US3, Polish | Australian standards, access control |
| `@observer-auditor` | US1, US2, Polish | Audit trail, ADR documentation |
| `@risk-manager` | US2 | Hazard radius operational realism |
| `@planning-officer` | US2, US6 | AIIMS situation assessment, re-planning |
| `@operations-officer` | US1, US4, US5, US6 | Field deployment, priority triage, road status |
| `@logistics-officer` | US4, US5 | Transport coordination, assignment tracking |
| `@field-coordinator` | US5 | Ground-level coordination needs |
| `@public-information-officer` | US3, US8 | Alert language, AWS tiers, translation quality |
| `@incident-commander` | US4, US6, Polish | Multi-agency coordination, route propagation |
| `@bom-national` | US2, US7 | Hazard radius ranges, sensor telemetry standards |
| `@ga-national` | US2 | Earthquake radius validation |
| `@transport` | US4, US6 | Vehicle categories, road closure standards |
| `@accessibility-tester` | US3, US8 | Multilingual validation, RTL support |
| `@docker-container-engineer` | US7, Polish | Container endpoint config, image optimisation |
| `@local-government` | US2, US5 | Sensor naming, municipal emergency plans |
| `@community-ngos` | US5 | Evacuation centre operations |
| `@health` | US4 | Vulnerable population categories |
| `@utility` | US7 | Sensor type coverage |
| `@state-government` | US6 | Road authority notification protocols |
| `@speckit.analyze` | Polish | Cross-artifact consistency |

---

## Parallel Opportunities

### After Phase 2 Completes (Maximum Parallelism)

```
                    +-- US1 (Non-Blocking Delivery)
                    +-- US2 (Hazard Map Generation)
Phase 2 ---------->+-- US3 (Content Safety)
(Foundational)      +-- US4 (Transport Handoff)
                    +-- US5 (Dispatch Notifications)
                    +-- US6 (Dynamic Road Network)
                    +-- US7 (IoT Adapter)
                    +-- US8 (Translation Quality)
```

All 8 user stories can execute in parallel after Phase 2 -- each targets different source files with independent test suites.

### Within User Story 2 (Example)

```bash
# Parallel (different files):
T027: "HazardRadiusLookup model in hazard_radius.py"
T028: "NamedLocation model in named_locations.py"

# Sequential (model dependencies):
T029: "Cosmos DB CRUD for radius_lookup" (depends on T027)
T030: "Named-location resolution" (depends on T028)
T031: "HazardMapGenerator with Shapely" (depends on T029)

# Then integration + API + tests
T033-T038: pipeline integration, CRUD API, unit tests
```

### Within User Story 3 (Example)

```bash
# Sequential core pipeline layers:
T039: "Azure AI client wrapper"
T040: "Confidence normalization" (depends on T039)
T041: "Factual check" (parallel with T042)
T042: "Tone check" (parallel with T041)
T043: "Circuit breaker" (depends on T039)

# Parallel tests:
T047-T050: all 4 test files target different test modules

# Independent of pipeline:
T052: "Test corpus" (parallel with everything)
T053: "Bicep module" (parallel with everything)
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only)

1. Phase 1: Setup (T001-T003)
2. Phase 2: Foundational -- async conversion + auth middleware (T004-T015)
3. Phase 3: US1 -- Dead-letter persistence and redelivery (T016-T026)
4. **VALIDATE**: Benchmark P95 <=5s, dead-letter lifecycle works
5. Phase 4: US2 -- Hazard map generation (T027-T038)
6. **VALIDATE**: GeoJSON polygons generated, radius API functional
7. Phase 5: US3 -- Content safety pipeline (T039-T053)
8. **VALIDATE**: Unsafe content blocked, circuit breaker telemetry works
9. **MVP DELIVERED**: Core HIGH-severity compliance gaps closed (F10, F03, F08)

### Incremental Delivery (P2 + P3)

10. Phase 6: US4 -- Transport handoff, test independently
11. Phase 7: US5 -- Dispatch notifications, test independently
12. Phase 8: US6 -- Dynamic road network, test independently
13. Phase 9: US7 -- IoT adapter, test independently
14. Phase 10: US8 -- Translation quality, test independently
15. Phase 11: Polish, final validation

### Parallel Team Strategy

With 3 developers after Phase 2:

- **Developer A**: US1 (dead-letter) then US4 (transport handoff) then US7 (IoT adapter)
- **Developer B**: US2 (hazard map) then US6 (dynamic road network) then US8 (translation)
- **Developer C**: US3 (content safety) then US5 (dispatch) then Polish

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | **89** |
| Setup tasks | 3 (T001-T003) |
| Foundational tasks | 12 (T004-T015) |
| US1 tasks | 11 (T016-T026) |
| US2 tasks | 12 (T027-T038) |
| US3 tasks | 16 (T039-T053 incl. T052b) |
| US4 tasks | 6 (T054-T059) |
| US5 tasks | 5 (T060-T064) |
| US6 tasks | 6 (T065-T070) |
| US7 tasks | 7 (T071-T077) |
| US8 tasks | 5 (T078-T082) |
| Polish tasks | 6 (T083-T088) |
| Parallelizable tasks [P] | 28 |
| Actor agents involved | 30 unique agents |
| FRs covered | 23/23 (FR-001 through FR-021 + FR-003a + FR-004a) |
| SCs covered | 9/9 (SC-001 through SC-009) |
