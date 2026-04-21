# Research: Agent Specification Compliance Audit

**Feature**: 025-agent-spec-compliance  
**Date**: 2026-04-21

## R1 — Non-Blocking Retry Patterns for Python Agent Pipelines (F10)

**Decision**: Replace `time.sleep()` with `asyncio.sleep()` + `asyncio.gather()` for non-blocking concurrent delivery.

**Rationale**: The codebase already uses Python 3.11+ and FastAPI (async-native). Converting the 6 blocking call sites to async is the minimal-disruption path. The existing `deliver_handoff_with_retry()` function signature changes from synchronous to `async def`, and callers wrap concurrent deliveries in `asyncio.gather()`.

**Alternatives considered**:
- Azure Service Bus topics/subscriptions for fire-and-forget delivery: Rejected because it introduces a new async messaging dependency for internal agent-to-agent calls that currently use direct function invocation. Overkill for the retry problem; Service Bus is better suited for external integration (IoT adapter).
- Thread pool executor: Rejected because asyncio is already the runtime model for FastAPI and agent pipelines. Mixing threading adds complexity without benefit.

**Affected call sites** (6 total):
1. `apps/agents/common/handoffs.py` — `deliver_handoff_with_retry()` (L102-139)
2. `apps/agents/risk_assessment/versioning.py` — OCC retry (L64-66)
3. `apps/agents/communication/versioning.py` — OCC retry (L67)
4. `apps/agents/evacuation/versioning.py` — OCC retry (L66)
5. `apps/agents/resource_allocation/versioning.py` — OCC retry (L78)
6. `apps/agents/communication/delivery.py` — channel delivery retry (L167)

**Dead-letter persistence**: The existing `on_dead_letter` callback pattern is preserved. Callers already provide a lambda that generates a dead-letter entry ID. The async conversion does not change the dead-letter contract — it changes when control returns to the caller (immediately vs after sleep).

---

## R2 — GeoJSON Hazard Polygon Generation from Point Signals (F03)

**Decision**: Add a `HazardMapGenerator` class that produces GeoJSON Polygon geometry from signal locations and severity, using a severity-indexed radius lookup table per hazard type. Output populates the existing `HazardMap` model field on `HazardAssessment`.

**Rationale**: The `HazardMap` Pydantic model already exists with `affected_area: dict[str, Any]` documented as "GeoJSON Polygon". The `HazardAssessment.hazard_map` field is `Optional` and defaults to `None`. The only missing piece is generation logic. Using Shapely's `Point.buffer()` to create circular polygons from point+radius is the standard approach for generating affected-area polygons.

**Alternatives considered**:
- API-layer on-demand computation (HazardVisualisationService): Rejected because the spec requires the agent itself to produce the map as part of its output. Deferring to the API layer would leave the agent output non-compliant.
- LLM-generated GeoJSON: Rejected because LLMs produce unreliable geometric coordinates. Deterministic geometric computation is more appropriate for life-safety spatial data.

**Radius lookup table structure**:
```python
HAZARD_RADIUS_TABLE: dict[str, dict[str, float]] = {
    "bushfire": {"low": 1000, "moderate": 2500, "high": 5000, "critical": 10000},
    "flood": {"low": 500, "moderate": 1500, "high": 3000, "critical": 5000},
    "cyclone": {"low": 5000, "moderate": 15000, "high": 30000, "critical": 50000},
    "earthquake": {"low": 2000, "moderate": 5000, "high": 10000, "critical": 20000},
    "chemical_spill": {"low": 200, "moderate": 500, "high": 1000, "critical": 2000},
    "storm": {"low": 1000, "moderate": 3000, "high": 8000, "critical": 15000},
}
```
Values in metres. Defaults to `{"low": 1000, "moderate": 2500, "high": 5000, "critical": 10000}` for unrecognised hazard types.

**Polygon merging**: When multiple signals overlap, use Shapely `unary_union()` to merge adjacent/overlapping polygons into a single MultiPolygon, preserving the highest severity level.

---

## R3 — Azure AI Content Safety Integration (F08)

**Decision**: Integrate Azure AI Content Safety SDK as the primary validator. Retain the existing keyword check as a synchronous fallback when the service is unavailable. Messages validated in fallback mode are flagged for human review.

**Rationale**: Azure AI Content Safety is the Azure-native service for this purpose, supports all 6 target languages (en, zh, ar, vi, el, it), and provides categorised severity scores for hate, self-harm, sexual, and violence content. The existing `ContentSafetyValidator` class interface (`validate()` returning `ContentSafetyResult`) can be preserved — the internal implementation changes from keyword matching to SDK call with keyword fallback.

**Alternatives considered**:
- Azure OpenAI built-in content filtering: Rejected as primary because it only filters LLM input/output, not arbitrary text. It cannot validate pre-composed alert templates or human-edited messages.
- Third-party content moderation API: Rejected for data sovereignty — Azure AI Content Safety can be deployed to Australia East.

**SDK dependency**: `azure-ai-contentsafety>=1.0.0`

**Infrastructure**: New Bicep module `infra/bicep/content-safety.bicep` provisioning `Microsoft.CognitiveServices/accounts` with kind `ContentSafety` in Australia East.

---

## R4 — Evacuation Transport Handoff to Resource Allocation (F05)

**Decision**: Add a new pipeline stage (Stage 9b) in the Evacuation agent that creates an `AgentHandoffEvent` with `target_agent="resource_allocation"` and a payload containing the transport requirements list. Uses the existing `deliver_handoff_with_retry()` (async version per F10).

**Rationale**: The Resource Allocation agent already has handler code at pipeline.py L267-270 that checks `handoff.source_agent == "evacuation"` and extracts `transportRequirements` from the payload. The receiving end is built; only the sending end is missing.

**Alternatives considered**:
- Surface transport tasks in Persona Workspace for human dispatch: Rejected because the Resource Allocation agent already has automated allocation logic expecting this handoff. Human-only dispatch adds latency and reduces the "50% response time" claim.

**Handoff payload schema**:
```python
{
    "transportRequirements": [
        {
            "vulnerability_category": str,
            "estimated_vehicles": int,
            "vehicle_type": str,
            "capacity_needed": int,
            "pickup_location": {"type": "Point", "coordinates": [lon, lat]},
            "dropoff_location": {"type": "Point", "coordinates": [lon, lat]},
            "priority": str,
        }
    ],
    "evacuation_plan_id": str,
    "zones_affected": list[str],
}
```

---

## R5 — Resource Allocation Dispatch Notification Handoff (F06)

**Decision**: Add a new pipeline stage (Stage 8b) in the Resource Allocation agent that creates an `AgentHandoffEvent` with `target_agent="communication"` and a payload containing dispatch assignment details. One handoff per agency to scope notifications.

**Rationale**: The Communication agent already handles incoming handoffs and generates multilingual alerts. Routing dispatch notifications through the existing alert pipeline ensures they benefit from translation, content safety, and delivery channel infrastructure.

**Alternatives considered**:
- Direct task creation in persona workspaces: Rejected because it bypasses the Communication agent's multilingual and content safety infrastructure. Dispatch notifications to field teams need the same delivery guarantees as public alerts.

**Handoff payload schema**:
```python
{
    "dispatch_type": "operational_dispatch",
    "assignments": [
        {
            "assignment_type": "personnel" | "supply",
            "quantity": int,
            "destination": {"type": "Point", "coordinates": [lon, lat]},
            "destination_name": str,
            "assigned_agency": str,
            "priority": str,
            "resource_details": str,
        }
    ],
    "plan_id": str,
    "incident_id": str,
}
```

---

## R6 — Dynamic Road Network from Monitoring Handoffs (F04)

**Decision**: The Monitoring agent sends a direct `AgentHandoffEvent` to the Evacuation agent when it classifies a signal as road-closure type. The Evacuation agent's pipeline receives this handoff and calls the existing `apply_closure()` / `remove_closure()` methods on the road network graph before route computation.

**Rationale**: The road network already has `apply_closure(edge_id, reason)` and `remove_closure(edge_id)` methods. The missing piece is: (1) Monitoring classifying road-closure signals, and (2) Evacuation receiving and applying them. Using direct handoff (per clarification Q4) keeps latency low for time-critical road updates.

**Alternatives considered**:
- Evacuation subscribes to a filtered signal feed: Rejected per clarification — direct handoff from Monitoring preferred for real-time urgency.
- Azure Maps Route API integration: Rejected as out of scope — addresses a different problem (external routing) rather than the immediate gap (static graph).

**Signal-to-edge mapping**: Road closure signals must include a `road_segment_id` or sufficient location data (coordinates + road name) to identify the affected `RoadEdge` in the graph. If only coordinates are provided, nearest-edge lookup using Shapely spatial index.

---

## R7 — IoT Signal Ingestion via Azure IoT Hub (F01)

**Decision**: Deploy Azure IoT Hub as the ingestion gateway. IoT Hub routes device-to-cloud messages via Event Grid to an Azure Function (or Container App endpoint) that normalises messages into `SignalEnvelope` format and submits them to the Monitoring agent's existing pipeline.

**Rationale**: Azure IoT Hub is the Azure-native IoT gateway supporting MQTT, AMQP, and HTTPS protocols with built-in device management, at-least-once delivery, and deduplication. Event Grid integration provides reliable message routing to downstream processors.

**Alternatives considered**:
- MQTT broker (Mosquitto/EMQX) on Container Apps: Rejected because it requires managing broker infrastructure, TLS certificates, and device authentication manually. IoT Hub provides these as managed services.
- Direct MQTT adapter in the Monitoring agent: Rejected because embedding protocol handling in the agent code violates the architecture's separation of collection and triage (the same principle that justified dismissing F02).

**Deduplication**: IoT Hub provides message deduplication via `MessageId` property. The adapter also deduplicates by `(device_id, sequence_number)` composite key using a 30-second in-memory sliding window with TTL-based eviction before pipeline entry. At 10K msg/s scale, in-memory dedup avoids external store latency.

**Infrastructure**: New Bicep module `infra/bicep/iot-hub.bicep` provisioning `Microsoft.Devices/IotHubs` + Event Grid subscription routing to the monitoring agent's Container App endpoint.

---

## R8 — Embedding-Based Translation Quality Validation (F09)

**Decision**: Replace the word-frequency cosine similarity in `_compute_similarity()` with embedding-based cosine similarity using the Azure OpenAI `text-embedding-3-small` model (already available via the existing Azure OpenAI deployment).

**Rationale**: The existing `_compute_similarity()` method uses bag-of-words vectors, which miss semantic meaning. Embedding-based similarity captures meaning preservation across paraphrasing and synonym substitution. The Azure OpenAI service already deployed for the Communication agent's LLM calls can serve embedding requests without additional infrastructure.

**Alternatives considered**:
- BLEU/ROUGE scores: Rejected because they are surface-level metrics (n-gram overlap) that share the same fundamental weakness as word-frequency cosine similarity — they measure lexical overlap, not semantic equivalence.
- Local sentence-transformers model: Rejected for operational simplicity — adding a local model increases container image size and memory requirements. The existing Azure OpenAI endpoint already handles the load.

---

## R9 — Circuit Breaker Pattern for Content Safety Fallback (FR-009)

**Decision**: Implement a dedicated `ContentSafetyCircuitBreaker` class that wraps Azure AI Content Safety calls with 3-failure trip threshold, 60-second cooldown window, and single-probe recovery. Five structured telemetry events for full observability.

**Rationale**: Per-request fallback (try Azure AI → catch → keyword) compounds timeout latency when the service is down. During a 30-minute outage, every validation attempt waits for the HTTP timeout before falling back. A circuit breaker eliminates this penalty after 3 failures by routing directly to the keyword fallback for the cooldown window, then testing with a single probe. This pattern is standard for external dependency resilience (Microsoft REST API guidelines, Azure Architecture Center).

**Alternatives considered**:
- Per-request try/catch fallback: Rejected because it multiplies timeout latency by validation volume during outages.
- Azure Service Health webhook to toggle mode: Rejected because Service Health events are delayed and coarse-grained — a circuit breaker provides immediate, fine-grained detection.

**Telemetry events** (5):
1. `content_safety_circuit_opened` — WARNING, emitted when 3rd consecutive failure trips the breaker
2. `content_safety_probe_attempted` — INFO, emitted when the cooldown expires and a probe is sent
3. `content_safety_circuit_closed` — INFO, emitted when the probe succeeds
4. `content_safety_probe_failed` — WARNING, emitted when the probe fails (resets cooldown)
5. `content_safety_fallback_summary` — INFO, emitted when the circuit closes, with count of messages validated via fallback

**State machine**: CLOSED → (3 failures) → OPEN → (60s cooldown) → HALF_OPEN → (probe success) → CLOSED / (probe failure) → OPEN

---

## R10 — Management API RBAC Authorization (FR-021)

**Decision**: Add FastAPI middleware that enforces Azure RBAC in production and API key auth for local development. Management endpoints (dead-letter redelivery, radius table CRUD) require `operator` or `admin` role claim.

**Rationale**: Management endpoints modify system state (radius lookup values, dead-letter redelivery) and must be restricted. Mirrors the FR-007 pattern where Azure AI Content Safety uses `DefaultAzureCredential` in production and API key locally. Azure RBAC leverages existing identity infrastructure (Azure AD/Entra ID app registrations used by Container Apps).

**Alternatives considered**:
- Shared secret header for all environments: Rejected — does not support role differentiation (operator vs admin) and is weaker than identity-based auth.
- Separate admin service: Rejected — over-engineering for a handful of endpoints that naturally live in the same FastAPI app.

**Implementation**:
- FastAPI `Depends()` with an `authorize_management()` dependency
- Production: Decode JWT from `Authorization: Bearer <token>`, validate Azure AD issuer and audience, check `roles` claim for `operator` or `admin`
- Local: Accept `X-API-Key` header matching `MANAGEMENT_API_KEY` env var
- 401 for missing/invalid credentials, 403 for insufficient role
- All auth failures logged as structured security audit events

---

## R11 — Named-Location Coordinate Resolution (FR-004a)

**Decision**: Add a named-location lookup table (Cosmos DB) that maps device names and location identifiers to lat/lon coordinates. When a hazard signal has no geographic coordinates, the Risk Assessment agent attempts resolution from this table before rejecting the signal.

**Rationale**: IoT devices commonly use named locations without embedding lat/lon in every message. A lookup table is the simplest approach — avoids external geocoding API latency and keeps the resolution deterministic and auditable.

**Alternatives considered**:
- Azure Maps geocoding API: Rejected because it introduces external API latency and non-deterministic results (address parsing variability). Named locations for IoT devices are a known, finite set.
- Require all IoT devices to include coordinates: Rejected because existing device firmware may not embed GPS. The adapter needs to handle both cases.

**Schema**:
```python
class NamedLocation(BaseModel):
    location_id: str       # Device name or location identifier
    display_name: str      # Human-readable name
    latitude: float        # WGS84
    longitude: float       # WGS84
    last_updated: datetime
```

**Behaviour**: Lookup is attempted on `location_id` match → return (lat, lon). Log resolution with source identifier. On miss → reject signal with validation error specifying missing location.

---

## R12 — Admin-Editable Cosmos DB Radius Lookup Table (FR-006)

**Decision**: Migrate the hazard radius lookup from a static Python dict to a Cosmos DB collection editable via management API. Seed configuration loaded on first deployment. Changes take effect on next hazard map generation without restart.

**Rationale**: The original R2 research defined a static `HAZARD_RADIUS_TABLE` dict. Clarification Q14 requires admin-editable storage with management API. Cosmos DB is already the primary data store; adding a collection is minimal overhead. The agent reads from Cosmos DB per generation cycle, so changes take effect immediately without restart.

**Alternatives considered**:
- App Configuration / Feature Flags: Rejected because the table has structured multi-column data (hazard_type × severity → radius) that doesn't map well to key-value flags.
- Environment variables: Rejected because structured table data in env vars is fragile and requires container restart.

**Schema** (Cosmos DB document):
```json
{
  "id": "bushfire",
  "hazard_type": "bushfire",
  "radii": {
    "1": 1000, "2": 2500, "3": 5000, "4": 7500, "5": 10000
  },
  "last_updated": "2026-04-21T00:00:00Z",
  "updated_by": "system-seed"
}
```

**Seed data**: 5 hazard types (flood, bushfire, earthquake, cyclone, chemical_spill), severity 1–5.

**API endpoints** (under FR-021 RBAC):
- `GET /api/v1/admin/radius-lookup` — list all entries
- `GET /api/v1/admin/radius-lookup/{hazard_type}` — get one
- `PUT /api/v1/admin/radius-lookup/{hazard_type}` — update radii
- `POST /api/v1/admin/radius-lookup` — add new hazard type

---

## R13 — Normalized Confidence Scoring for ContentSafetyResult (FR-007)

**Decision**: ContentSafetyResult reports a normalized confidence score (0.0–1.0) with explicit mapping per validation layer, plus a `validation_method` field identifying which check produced the result.

**Rationale**: Azure AI returns severity 0–6 (integer), factual check is binary (match/mismatch), tone check is binary (pass/fail). A unified 0.0–1.0 confidence enables consistent threshold-based alerting and dashboard display across all three layers without consumers needing to know the source.

**Mapping**:
- Azure AI Content Safety: `severity / 6.0` (linear normalization, 0→0.0, 6→1.0)
- Factual consistency: `match → 0.0`, `mismatch → 1.0`
- Tone check: `pass → 0.0`, `fail → 1.0`

**validation_method values**: `"azure_ai"`, `"factual"`, `"tone"`, `"keyword_fallback"`

**ContentSafetyResult fields**:
- `passed: bool`
- `result: str`
- `reason: str | None`
- `confidence: float` (0.0–1.0, normalized)
- `validation_method: str`

---

## R14 — Dead-Letter Permanently Failed Terminal State (FR-003a)

**Decision**: Add `permanently_failed` as a terminal status for dead-letter entries that exhaust both auto-redelivery (3 attempts) and a subsequent manual redelivery.

**Rationale**: Without a terminal state, dead-letter entries can be retried indefinitely. Stale handoffs (e.g., from hours-ago incidents) may be operationally irrelevant. An explicit terminal state prevents unbounded retry loops and makes the lifecycle clear.

**State transitions** (updated):
```
pending → delivered     (successful delivery)
pending → failed        (temporary failure)
failed  → pending       (retry attempt)
failed  → dead_lettered (max retries exhausted)
dead_lettered → pending (auto/manual redelivery attempt)
dead_lettered → permanently_failed (3 auto + 1 manual redelivery failed)
```

**Audit trail for permanently_failed entries**:
- `auto_redeliver_attempts: int` (max 3)
- `manual_redeliver_attempts: int` (max 1 before terminal)
- `failure_reasons: list[str]`
- `last_attempt_at: datetime`
- `permanently_failed_at: datetime`

---

## R15 — Test Corpus Requirements for SC-004 and SC-009

**Decision**: Define minimum test corpus sizes and composition to make success criteria measurable and repeatable.

**Rationale**: Without corpus minimums, SC-004 and SC-009 could pass with trivially small test sets. Explicit minimums ensure statistical significance and coverage of edge cases.

**SC-004 corpus** (content safety):
- ≥50 unsafe messages per supported language (en, zh, ar, vi, el, it = 300+ total)
- ≥50 safe messages per supported language (300+ total)
- Unsafe messages cover all 6 violation categories: hate, violence, sexual, self-harm, factual inconsistency, tone-level violation
- Located in `tests/fixtures/content_safety/`

**SC-009 corpus** (translation quality):
- ≥30 translation pairs per supported language
- ≥10 meaning-preserving pairs (synonym substitution, reordering)
- ≥10 meaning-altering pairs (critical term swaps, directional inversions, severity changes)
- Located in `tests/fixtures/translation_quality/`

---

## R16 — Priority Field in Transport Handoff (FR-011)

**Decision**: Add `priority: int` (1–5, aligned with hazard severity) to the transport handoff payload (FR-011) and the `TransportRequirement` entity.

**Rationale**: During multi-hazard events, transport resources are scarce. Priority enables the Resource Allocation agent to triage transport assignments — processing critical evacuations (severity 5) before moderate ones (severity 2). The existing `TransportRequirement` entity already has a `priority: str` field ("critical"/"high"/"moderate"/"low"); changing to integer 1–5 aligns with the numeric hazard severity scale and simplifies sorting.

**Mapping**: 1 = lowest priority, 5 = critical (matches hazard severity scale).

**Implementation**: The `_compute_similarity()` static method becomes an instance method (or accepts an embedding client) that calls `client.embeddings.create(model="text-embedding-3-small", input=[text_a, text_b])` and computes cosine similarity on the returned vectors. Threshold remains ≥ 0.85.

**Fallback**: If the embedding endpoint is unavailable, fall back to the existing word-frequency method and log a warning. This preserves graceful degradation.
