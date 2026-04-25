# Feature Specification: Agent Specification Compliance Audit

**Feature Branch**: `025-agent-spec-compliance`  
**Created**: 2026-04-21  
**Status**: Draft  
**Input**: Cross-reference audit of agent code against capstone specification claims — 8 findings with merit requiring remediation across Monitoring, Risk Assessment, Evacuation, Resource Allocation, and Communication agents.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Non-Blocking Agent Pipeline Delivery (Priority: P1)

As an emergency coordinator, I need the multi-agent pipeline to process signals and produce actionable outputs within the claimed response time targets, so that time-critical decisions are not delayed by internal system bottlenecks.

**Why this priority**: Finding F10 directly undermines the capstone's "50% response time reduction" success criterion. Synchronous blocking retries across 6 call sites create a worst-case 36-second stall in the handoff chain, nullifying the core performance claim.

**Independent Test**: Trigger a pipeline run with a simulated downstream failure (unavailable target agent). Measure wall-clock time from signal ingestion to pipeline completion and verify no individual retry sequence blocks concurrent processing.

**Acceptance Scenarios**:

1. **Given** a downstream agent is temporarily unavailable, **When** a handoff delivery fails, **Then** the retry mechanism does not block the calling pipeline stage from processing other signals.
2. **Given** three concurrent signals enter the monitoring pipeline, **When** one signal's downstream delivery encounters retries, **Then** the other two signals complete processing without waiting for the retry to finish.
3. **Given** all retry attempts for a handoff are exhausted, **When** the delivery finally fails, **Then** the pipeline records a delivery failure event, continues processing, and the total blocking time per retry sequence is under 2 seconds.

---

### User Story 2 — Hazard Map Generation (Priority: P1)

As an emergency coordinator viewing the dashboard, I need the Risk Assessment agent to produce spatial hazard data (geographic polygons with severity), so that I can visualise affected zones on a map and make informed evacuation and resource decisions.

**Why this priority**: Finding F03 is HIGH severity. The capstone explicitly claims "generating real-time hazard maps" but the agent produces only text summaries with scores — zero spatial output exists. This is a direct specification compliance gap.

**Independent Test**: Submit a hazard assessment request with location-tagged signals. Verify the response includes a structured geographic representation (polygon geometry with affected area boundaries and severity classification).

**Acceptance Scenarios**:

1. **Given** a set of signals with geographic coordinates indicating a flood, **When** the Risk Assessment agent completes its assessment, **Then** the output includes a hazard map containing at least one geographic polygon defining the affected area.
2. **Given** multiple hazard signals in overlapping areas, **When** the agent generates a hazard map, **Then** the polygons reflect merged or adjacent zones with appropriate severity levels.
3. **Given** a hazard signal with only a point location (no area data), **When** the agent generates the hazard map, **Then** it produces a polygon using the signal's severity to estimate an affected radius.

---

### User Story 3 — Content Safety for Alert Messages (Priority: P1)

As the system owner responsible for life-safety communications, I need alert messages to be validated by a robust content safety mechanism before reaching the public, so that harmful, misleading, or inappropriate content is blocked before dissemination.

**Why this priority**: Finding F08 is HIGH severity. The current content safety validator uses only 2 hardcoded keywords ("terror", "hate") with a TODO comment acknowledging the gap. For life-safety communications during disasters, this is insufficient — harmful content could reach vulnerable populations.

**Independent Test**: Submit alert messages containing various categories of unsafe content (hate speech, misinformation, panic-inducing language). Verify that the safety validator correctly identifies and blocks them while passing legitimate emergency alerts.

**Acceptance Scenarios**:

1. **Given** an alert message containing harmful content in any supported language, **When** the message is submitted for safety validation, **Then** the validator blocks the message and provides a categorised rejection reason.
2. **Given** a legitimate emergency alert containing urgent but safe language (e.g., "evacuate immediately"), **When** the message is validated, **Then** it passes content safety and proceeds to delivery.
3. **Given** the external content safety service is unavailable, **When** a message is submitted, **Then** the circuit breaker trips after 3 consecutive failures, the system falls back to a local keyword-based check, delivers the message immediately with a `review_flag=true` annotation, and does not hold it for human approval.

---

### User Story 4 — Evacuation-to-Resource-Allocation Transport Handoff (Priority: P2)

As an emergency coordinator, I need the Evacuation agent's transport requirements (vehicle types, capacity needs, pickup/dropoff points) to be automatically forwarded to the Resource Allocation agent, so that vehicle dispatch can begin without manual re-entry.

**Why this priority**: Finding F05 is a broken inter-agent handoff. The Evacuation agent generates TransportRequirements in its pipeline but never delivers them downstream. The Resource Allocation agent has code expecting this handoff — the pipeline is half-built.

**Independent Test**: Trigger an evacuation plan that generates transport requirements. Verify the Resource Allocation agent receives a handoff event containing the transport payload.

**Acceptance Scenarios**:

1. **Given** the Evacuation agent has completed route planning with transport requirements, **When** the pipeline finalises, **Then** a handoff event containing the transport requirements is delivered to the Resource Allocation agent.
2. **Given** the Resource Allocation agent receives a transport handoff from Evacuation, **When** it processes the handoff, **Then** it extracts vehicle type, capacity, pickup/dropoff data, and priority and includes them in its allocation planning, processing higher-priority transports first.
3. **Given** the Evacuation pipeline completes but generates zero transport requirements (all evacuees are ambulatory), **When** the pipeline finalises, **Then** no transport handoff is sent and a log entry explains why.

---

### User Story 5 — Resource Allocation Dispatch Notifications (Priority: P2)

As a field team leader, I need to receive actionable dispatch notifications when the Resource Allocation agent assigns supplies or personnel to my area, so that I can act on the assignment without checking a dashboard.

**Why this priority**: Finding F06 means allocation plans are persisted to the database but never communicated to anyone. Field teams have no way to know they've been assigned tasks.

**Independent Test**: Complete a resource allocation plan that assigns resources to a field team. Verify the assignment triggers a downstream notification (handoff to Communication agent or task record in a workspace).

**Acceptance Scenarios**:

1. **Given** the Resource Allocation agent produces a deployment plan with personnel and supply assignments, **When** the plan is persisted, **Then** a handoff event targeting the Communication agent is created with dispatch details for each assignment.
2. **Given** a deployment plan assigns resources across multiple agencies, **When** the dispatch notifications are generated, **Then** each agency receives only the assignments relevant to them.
3. **Given** the Communication agent is unavailable when dispatch notifications are sent, **When** delivery fails, **Then** the system retries using the non-blocking retry mechanism (per F10 fix) and logs the failure.

---

### User Story 6 — Dynamic Road Network for Evacuation Routing (Priority: P3)

As an emergency coordinator, I need evacuation routes to account for road closures and hazard zones reported during the incident, so that evacuees are not directed into blocked or dangerous roads.

**Why this priority**: Finding F04 is MEDIUM severity. Routes are computed on a static JSON road graph loaded once at startup. During a multi-hour disaster, road conditions change — closed bridges, flooded roads, debris. The current system cannot adapt.

**Independent Test**: Load the road network, then inject a road closure signal. Re-run route planning and verify the closed road segment is excluded or penalised in the resulting routes.

**Acceptance Scenarios**:

1. **Given** a road closure signal is received from the Monitoring agent, **When** the Evacuation agent next computes routes, **Then** the affected road segment is either removed from the graph or has its cost increased so it is avoided.
2. **Given** a previously closed road is reopened (clearance signal received), **When** routes are recomputed, **Then** the road segment is restored to its original weight.
3. **Given** all routes between a zone and a shelter are blocked, **When** the agent computes routes, **Then** it reports "no viable route" for that zone-shelter pair rather than routing through blocked segments.

---

### User Story 7 — IoT Signal Ingestion Adapter (Priority: P3)

As a sensor network operator, I need the Monitoring agent to accept signals from IoT devices using standard IoT messaging protocols, so that sensor data (water levels, seismic readings, air quality) reaches the system without requiring custom HTTP integration for each sensor type.

**Why this priority**: Finding F01 is MEDIUM severity. IoT signals are currently treated as generic API pulls via HTTP. Real IoT devices use protocols like MQTT with different QoS semantics.

**Independent Test**: Publish a signal to the IoT ingestion endpoint using a standard IoT messaging pattern. Verify it arrives as a normalised SignalEnvelope in the monitoring pipeline.

**Acceptance Scenarios**:

1. **Given** an IoT device publishes a water-level reading via the IoT ingestion pathway, **When** the signal is received, **Then** it is normalised into a SignalEnvelope and enters the monitoring pipeline within 5 seconds.
2. **Given** an IoT device publishes with at-least-once delivery semantics, **When** duplicate signals arrive, **Then** the adapter deduplicates them before pipeline entry.
3. **Given** the IoT ingestion pathway is unavailable, **When** a device attempts to publish, **Then** the message is retained by the messaging infrastructure and delivered when the pathway recovers.

---

### User Story 8 — Translation Quality Validation (Priority: P3)

As a multilingual alert recipient, I need translated emergency alerts to be semantically accurate, so that I receive the intended meaning and not a garbled or misleading translation.

**Why this priority**: Finding F09 is MEDIUM severity. The back-translation quality check uses word-frequency cosine similarity (bag-of-words), which misses semantic meaning. A translation could swap critical terms (e.g., "shelter" → "school") and still score high on word overlap.

**Independent Test**: Translate an alert to a target language and back-translate it. Verify the quality score reflects semantic accuracy, not just word overlap.

**Acceptance Scenarios**:

1. **Given** an alert is translated to a target language and back-translated to the source language, **When** the quality score is computed, **Then** it reflects semantic similarity rather than simple word overlap.
2. **Given** a back-translation preserves meaning but uses different phrasing (synonyms, reordering), **When** quality is assessed, **Then** the score is above the acceptance threshold (≥ 0.85).
3. **Given** a back-translation introduces a critical meaning change (e.g., "evacuate north" → "evacuate south"), **When** quality is assessed, **Then** the score falls below threshold and the translation is flagged for human review.

---

### Edge Cases

- What happens when a hazard signal has no geographic coordinates? The system MUST attempt named-location lookup to resolve coordinates; if the lookup fails, the signal is rejected with a validation error (see FR-004a).
- How does the system handle a cascading failure where all downstream agents are unavailable simultaneously? Non-blocking retries should prevent pipeline stalls, and undeliverable handoffs should be persisted for later redelivery.
- What if an IoT device sends signals faster than the pipeline can process? The ingestion adapter should apply backpressure or rate-limiting without dropping life-safety signals.
- What if the content safety service flags a legitimate emergency alert as unsafe? The human review workflow should provide an override path for authorised operators.
- What if road closures arrive after evacuation routes have already been dispatched? The system should issue updated route notifications for affected zones.

## Requirements *(mandatory)*

### Functional Requirements

**F10 — Non-Blocking Delivery**

- **FR-001**: The system MUST replace all synchronous blocking retry mechanisms in agent pipelines with non-blocking alternatives that allow concurrent signal processing during retries.
- **FR-002**: The system MUST cap maximum blocking time per individual retry sequence at 2 seconds regardless of the number of retry attempts.
- **FR-003**: The system MUST log each retry attempt and final delivery outcome (success or exhaustion) as a structured telemetry event.
- **FR-003a**: When all retry attempts for a handoff delivery are exhausted, the system MUST persist the undeliverable handoff to a dead-letter store. The system MUST automatically redeliver dead-lettered handoffs when the target agent's health endpoint returns healthy, using a background polling mechanism with configurable interval. Operators MUST also be able to manually trigger redelivery via the management API. Auto-redelivery MUST apply backoff to avoid retry storms when an agent flaps between healthy and unhealthy states. If a dead-letter entry fails both auto-redelivery (3 attempts) and a subsequent manual redelivery attempt, the system MUST transition it to `permanently_failed` status. Permanently failed entries MUST be read-only with a full audit trail (timestamps, attempt counts, failure reasons) and MUST NOT be retried again.

**F03 — Hazard Map Generation**

- **FR-004**: The Risk Assessment agent MUST produce a spatial hazard map output containing geographic polygons with severity classification for each assessed hazard.
- **FR-004a**: When a hazard signal has no geographic coordinates, the system MUST attempt to resolve coordinates from a named-location lookup table (device name or location identifier → lat/lon). If the lookup succeeds, the resolved coordinates MUST be used for hazard map generation and the resolution MUST be logged with the source identifier and matched location. If the lookup fails, the signal MUST be rejected with a validation error specifying the missing location, and no hazard map MUST be produced for that signal.
- **FR-005**: Each hazard polygon MUST include: boundary geometry, severity level, hazard type, and timestamp.
- **FR-006**: The system MUST generate a polygon from a point location and severity when no area geometry is provided in the source signals. The affected radius MUST be determined by a severity-indexed lookup table specific to each hazard type. The table MUST cover at minimum the hazard types already present in the codebase: flood, bushfire, earthquake, cyclone, and chemical_spill. Severity levels MUST be integer 1–5. The lookup table MUST be stored in Cosmos DB and editable via a management API endpoint, with a seed configuration loaded on first deployment. Changes to the lookup table MUST take effect on the next hazard map generation without requiring a restart.

**F08 — Content Safety Validation**

- **FR-007**: The Communication agent MUST validate all outbound alert messages against: (a) Azure AI Content Safety for hate speech, violence incitement, sexual content, and self-harm content, (b) a factual consistency check verifying that key alert fields (hazard type, severity level, location name) match the originating signal data passed through the pipeline, and (c) a warning-level tone check verifying that the alert's urgency language does not exceed the assigned Australian Warning System tier (Advice / Watch and Act / Emergency Warning). The tone check (c) MUST operate on the pre-translation English source text; translated outputs are guarded against tone drift by FR-019's semantic similarity check. In production, the Azure AI Content Safety client MUST authenticate via managed identity (`DefaultAzureCredential`); API key authentication is permitted only for local development.
- **FR-008**: The content safety validator MUST support all languages that the Communication agent translates alerts into.
- **FR-009**: The system MUST fall back to a local keyword-based check when the external content safety service is unavailable. The fallback MUST be triggered by a circuit breaker: after 3 consecutive Azure AI Content Safety failures, the circuit opens and routes all subsequent validations directly to the keyword fallback for a cooldown window (default 60 seconds), after which a single probe request is sent to test recovery; if the probe succeeds the circuit closes and normal Azure AI validation resumes. The circuit breaker MUST emit structured telemetry for each state transition: `logger.warning("content_safety_circuit_opened", extra={"consecutive_failures": N, "cooldown_seconds": 60})` when the circuit opens, `logger.info("content_safety_probe_attempted")` when a probe fires, `logger.info("content_safety_circuit_closed", extra={"open_duration_seconds": D})` when the probe succeeds, `logger.warning("content_safety_probe_failed", extra={"next_probe_seconds": 60})` when the probe fails, and MUST maintain a counter of fallback-validated messages emitted as `logger.info("content_safety_fallback_summary", extra={"fallback_message_count": N})` when the circuit closes. Fallback-validated messages MUST be delivered immediately with a `review_flag=true` annotation; they MUST NOT be held pending human approval. Human reviewers MAY retroactively retract a delivered message if the keyword check is later found insufficient. The system MUST NOT automatically throttle or pause outbound alerts during fallback mode; operators may manually pause delivery if needed.

**F05 — Evacuation Transport Handoff**

- **FR-010**: The Evacuation agent MUST create and deliver a handoff event to the Resource Allocation agent containing transport requirements when the evacuation plan includes non-ambulatory evacuees.
- **FR-011**: The transport handoff payload MUST include vehicle type, capacity needed, pickup location, dropoff location, and priority (integer 1–5, aligned with hazard severity) for each transport requirement.

**F06 — Dispatch Notifications**

- **FR-012**: The Resource Allocation agent MUST create a handoff event to the Communication agent containing dispatch details for each resource assignment in a deployment plan.
- **FR-013**: Dispatch notifications MUST include assignment type (personnel or supply), quantity, destination, and assigned agency.

**F04 — Dynamic Road Network**

- **FR-014**: The Evacuation agent MUST accept road closure and reopening signals delivered as direct handoff events from the Monitoring agent, and MUST adjust its road network graph weights before the next route computation.
- **FR-015**: The system MUST log each road network modification with the originating signal ID and the affected road segment.

**F01 — IoT Ingestion Adapter**

- **FR-016**: The Monitoring agent MUST accept signals via a standard IoT messaging pathway in addition to the existing HTTP endpoint.
- **FR-017**: The IoT adapter MUST normalise incoming IoT messages into SignalEnvelope format before pipeline entry.
- **FR-018**: The IoT adapter MUST deduplicate signals that arrive with at-least-once delivery semantics. Deduplication MUST use a composite key of (device_id, sequence_number) with a 30-second in-memory sliding window using TTL-based eviction. Messages with a (device_id, sequence_number) pair already present in the window MUST be silently dropped before pipeline entry.

**F09 — Translation Quality Validation**

- **FR-019**: The back-translation quality check MUST use embedding-based semantic similarity rather than word-frequency overlap to score translation accuracy.
- **FR-020**: The system MUST flag translations for human review when the quality score falls below the 0.85 threshold.

**Management API Authorization**

- **FR-021**: All management API endpoints (dead-letter redelivery, radius lookup table CRUD, and any future administrative operations) MUST require authentication and authorization. In production, the caller MUST present a valid Azure identity with an `operator` or `admin` role claim, enforced via middleware. For local development, API key authentication is permitted. Unauthenticated or unauthorized requests MUST return HTTP 401/403 and MUST be logged as security audit events.

### Key Entities

- **SignalEnvelope**: Normalised representation of an incoming signal from any source (HTTP, IoT). Contains source metadata, geographic coordinates, timestamp, signal type, and payload.
- **HazardMap**: Spatial output from Risk Assessment containing one or more geographic polygons with severity levels, hazard types, and temporal validity.
- **TransportRequirement**: Evacuation output specifying vehicle type, capacity, pickup/dropoff locations, and priority for non-ambulatory evacuees.
- **AgentHandoffEvent**: Inter-agent communication message containing source agent, target agent, event type, and structured payload. Used for evacuation→resource-allocation and resource-allocation→communication handoffs.
- **DispatchNotification**: Outbound message from Resource Allocation (via Communication agent) containing assignment details for field teams.
- **ContentSafetyResult**: Validation outcome from the content safety pipeline, including pass/fail status, violation categories, normalized confidence score (0.0–1.0, where Azure AI severity 0–6 is mapped linearly to 0.0–1.0, factual consistency maps match=0.0/mismatch=1.0, tone check maps pass=0.0/fail=1.0), reason string, and validation method (`azure_ai`, `factual`, `tone`, `keyword_fallback`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: P95 end-to-end pipeline latency from signal ingestion to final handoff delivery MUST be ≤ 5 seconds, measured under simulated single-agent failure conditions using the benchmark test suite.
- **SC-002**: No individual retry sequence blocks pipeline processing for more than 2 seconds, measured under simulated downstream failures.
- **SC-003**: 100% of Risk Assessment outputs include a spatial hazard map with at least one geographic polygon when the input signals contain location data.
- **SC-004**: Content safety validation catches 95% or more of unsafe test messages across all supported languages while passing 99% of legitimate emergency alerts. The test corpus MUST contain ≥50 unsafe messages and ≥50 safe messages per supported language, with unsafe messages covering all 4 Azure AI Content Safety categories (hate, violence, sexual, self-harm) plus factual inconsistency and tone-level violations.
- **SC-005**: 100% of evacuation plans with transport requirements result in a successfully delivered handoff event to the Resource Allocation agent.
- **SC-006**: 100% of resource deployment plans result in dispatch notifications delivered to the Communication agent.
- **SC-007**: Evacuation routes computed after a road closure signal exclude the affected road segment.
- **SC-008**: IoT signals published via the messaging pathway arrive in the monitoring pipeline within 5 seconds, with duplicates eliminated.
- **SC-009**: Back-translation quality scores correctly distinguish semantically accurate translations (score ≥ 0.85) from meaning-altering translations (score < 0.85) with at least 90% accuracy on a test corpus. The test corpus MUST contain ≥30 translation pairs per supported language, with ≥10 meaning-preserving pairs (synonym substitution, reordering) and ≥10 meaning-altering pairs (critical term swaps, directional inversions, severity changes).

## Assumptions

- The existing domain model `HazardMap` with `affected_area: dict[str, Any]` (documented as GeoJSON Polygon) provides a sufficient data structure for hazard map output — no new models are needed, only generation logic.
- The `AgentHandoffEvent` mechanism and delivery infrastructure already exist and are functional — findings F05 and F06 require adding handoff creation, not building the delivery system.
- An external content safety service is available in the deployment environment. The fallback keyword check is a degraded-mode safeguard, not the primary validation path.
- IoT ingestion can be addressed at the infrastructure boundary (gateway/broker) rather than requiring protocol-level changes within the Monitoring agent's codebase — the adapter normalises messages into SignalEnvelope regardless of transport.
- The existing cosine similarity threshold of 0.85 for translation quality is appropriate — this feature changes the similarity computation method, not the threshold.
- Human-in-the-loop approval gates for alert delivery (documented as intentional in F07, dismissed) remain unchanged. Content safety validation operates before the human approval step.
- The system MUST support up to 1,000 concurrent signals in the pipeline, 10,000 IoT messages per second at the ingestion boundary, and 50 concurrent dead-letter redelivery attempts without degradation.

## Clarifications

### Session 2026-04-21

- Q: When a handoff event exhausts all retries and cannot be delivered, what should happen? → A: Persist to a dead-letter store and automatically redeliver when the target agent recovers via a health-check polling mechanism. Operators may also trigger manual redelivery via the management API. Auto-redelivery must include backoff to prevent retry storms during agent flapping.
- Q: What radius model should be used when generating a hazard polygon from a point location? → A: Severity-indexed lookup table per hazard type (e.g., flood at severity 4 = 2km, chemical spill at severity 4 = 500m).
- Q: Should outbound alerts be throttled or paused when the content safety service is unavailable and fallback is active? → A: No automatic throttle — continue sending with keyword fallback and human review flag; operators can manually pause if needed.
- Q: How should the Evacuation agent receive road closure signals? → A: Monitoring agent sends a direct handoff event to Evacuation when it classifies a signal as road-closure type.
- Q: What type of semantic comparison should FR-019 require for translation quality? → A: Embedding-based semantic similarity without specifying which model or service.
- Q: During content safety fallback mode, should alerts be held for human review before delivery or delivered immediately with a review flag? → A: Deliver immediately with a review flag; human reviewers can retroactively retract if needed. Delivery latency for life-safety alerts outweighs the risk window.
- Q: What happens to a dead-letter entry that fails both auto-redelivery and manual redelivery? → A: Transition to `permanently_failed` terminal state — read-only with full audit trail, no further retries. Stale handoffs may be operationally irrelevant; an explicit terminal state prevents unbounded retry loops.
- Q: Should production deployments require managed identity for Azure AI Content Safety, or is API key auth also acceptable? → A: Managed identity only in production (`DefaultAzureCredential`); API key auth permitted only for local development.
- Q: What scale should the system target for concurrent signals, IoT ingestion rate, and dead-letter redelivery? → A: Large — up to 1,000 concurrent signals, 10,000 IoT msg/s, 50 concurrent redeliveries.
- Q: How should the content safety fallback be triggered — per-request failure or circuit breaker? → A: Circuit breaker — after 3 consecutive Azure AI failures, trip to keyword fallback for a 60-second cooldown window, then probe to recover. Avoids compounding timeout latency during outages.
- Q: How should IoT signal deduplication work at 10K msg/s scale — what key, window, and storage? → A: (device_id, sequence_number) composite key with 30-second in-memory sliding window and TTL eviction. Avoids payload hashing; naturally bounded per device.
- Q: SC-001 claims "50% reduction" but has no baseline — how do we make it testable? → A: Replace with absolute target: P95 end-to-end pipeline latency ≤ 5 seconds from signal ingestion to final handoff delivery under simulated single-agent failure.
- Q: FR-007(c) tone keywords are English-only but FR-008 mandates multilingual support — does the tone check run on translated output too? → A: English source text only. The tone check validates authored alert language pre-translation; FR-019's semantic similarity check guards against translation-induced tone drift.
- Q: FR-006 radius lookup table — how many hazard types, what severity scale, and who maintains it? → A: Admin-editable. Cover flood, bushfire, earthquake, cyclone, chemical_spill with severity 1–5. Stored in Cosmos DB, editable via management API, seed config on first deploy.
- Q: FR-011 omits priority but the TransportRequirement entity includes it — is priority required in the handoff payload? → A: Yes. Add priority (integer 1–5, aligned with hazard severity) to FR-011. Scarce transport resources require triage ordering during multi-hazard events.
- Q: What happens when a hazard signal has no geographic coordinates — reject or resolve? → A: Named-location fallback first. Attempt to resolve coordinates from a device/location lookup table; reject only if lookup fails. IoT devices commonly use named locations without lat/lon.
- Q: Who is authorized to use management API endpoints (dead-letter redelivery, radius table edits)? → A: Azure RBAC in production (operator/admin role claim via middleware); API key for local development. Mirrors the FR-007 content safety auth pattern.
- Q: Should circuit breaker state transitions emit structured telemetry? → A: Yes — full telemetry: circuit opened (with failure count), probe attempted, probe succeeded (circuit closed with open duration), probe failed, and fallback-validated message count summary on close.
- Q: ContentSafetyResult entity says "confidence scores" but Azure AI returns severity 0–6, not probabilities — what should it report? → A: Normalized confidence (0.0–1.0) mapped from Azure AI severity 0–6 linearly. Factual consistency: match=0.0/mismatch=1.0. Tone check: pass=0.0/fail=1.0. Unified interface across all three validation layers.
- Q: SC-004 and SC-009 reference test corpora with no defined size or composition — should the spec define minimums? → A: Yes. SC-004: ≥50 unsafe + ≥50 safe messages per language covering all 6 violation categories. SC-009: ≥30 pairs per language with ≥10 meaning-preserving and ≥10 meaning-altering examples.

## Dismissed Findings *(mandatory)*

Two audit findings were reviewed and dismissed with justification. Each MUST be recorded as an entry in the project's architectural decisions register (ADR) so the rationale is preserved and discoverable.

- **F02 — Monitoring agent: No social media connector**: Dismissed because the architecture intentionally delegates signal collection to upstream Data Source adapters. The Monitoring agent's responsibility is triage, not collection. The boundary decision is sound. **ADR required**: Document the deliberate separation of collection and triage responsibilities and why the Monitoring agent does not implement source-specific connectors.
- **F07 — Communication agent: "Autonomously" contradicted by human approval gate**: Dismissed because autonomous public alerting without human review is irresponsible for life-safety communications. OPA guardrails, approval workflows, and runbooks all mandate human-in-the-loop. **ADR required**: Document the intentional deviation from the "autonomous" spec language and the safety rationale for requiring human approval on outbound public alerts.


## Personas

Authored against the `specs/027-spec-hardening/contracts/persona-profile.md` schema. AU-v1 personas are validated; PH / JP / BD entries are explicit placeholders pending capstone-reinterpretation (D-009) and SME validation per FR-023.

- **PER-067**: cross-ref to `specs/001-disaster-response-hub/spec.md` AIIMS personas (Incident Commander / Planning Officer / Operations Officer / Logistics Officer / Public Information Officer) per `specs/027-spec-hardening/contracts/persona-profile.md`. `status:` validated. `preconditions:` none.
- **PER-068**: cross-ref to `specs/004-actor-github-agents/spec.md` actor catalogue covering all `.github/agents/technical/*.agent.md` actors. `status:` validated. `preconditions:` none.
- **PER-069** [non-AU placeholder]: capstone-country operator personas for PH (NDRRMC), JP (Cabinet Office DRR / FDMA), BD (DDM / CPP volunteers). `status:` placeholder. `preconditions:` capstone-reinterpretation decision per D-009; SME validation via `ama-rubric-grader`-vetted SME interviews.

## Hypotheses

Hypotheses use the FR-018 statement format (`If <condition> then <observable>`) and link to a structured evidence stub conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. Capstone-country hypotheses for this spec's agent ownership (where applicable) are allocated in feature 028 / US2.

- **HYP-023**: If the actors named in `specs/004-actor-github-agents/spec.md` consult on every change to this spec via the `agent` tool, then the AMA rubric criterion mean (Assumptions / Requirements / Personas / Hypotheses / Scope) for this spec rises by at least +1 band relative to the baseline captured in `specs/028-capstone-alignment/evidence/rubric-baseline.md`. **Falsification**: post-feature rubric snapshot shows a regression in any of those five criteria for this spec. **Evidence stub**: `specs/028-capstone-alignment/evidence/HYP-HYP-023.md` (created in feature 028 polish).

## Out of Scope

- This spec is delivery-hygiene / enabling infrastructure; capstone-outcome-critical-path ownership lives in specs all capstone-critical-path specs (001, 005, 006, 008, 009, 010, 011, 012, 014, 015, 018, 019, 020, 021, 022, 023).

Items explicitly deferred from this spec; promotion to in-scope requires the named preconditions to clear. Cross-references to other specs use the canonical overlap phrasing (`authoritative for: <capability>` / `defers-to: <NNN> (<capability>)`).

- **SCP-074** [DEFERRED]: Capstone-country variants (PH typhoon, JP earthquake, BD flood) of this spec's capabilities are out of scope until: (i) capstone-reinterpretation decision per D-009; (ii) per-country regulatory + data-sharing preconditions documented in `specs/005-data-source-governance/spec.md` clear; (iii) responsible technical agents (qa-test-engineer, product-owner-ba) sign off on country-specific calibration.
- **SCP-075**: Constitutional-level changes (NON-NEGOTIABLE #1..#5) are not modified by this spec; any tension is documented as `[RISK]` in Assumptions, never resolved here.
- **SCP-076**: Cross-spec authority disputes are arbitrated via `product-owner-ba` and the speckit governance flow; this spec does not unilaterally claim ownership of capabilities owned elsewhere. `defers-to:` 018 (recovery-phase indicators, triggers, phase-exit criteria); 008 (warning-tier authoring, multilingual delivery, misinformation defence) where applicable.
- **SCP-077** [META]: This spec is delivery-hygiene / enabling infrastructure; capstone-outcome-critical-path ownership lives in specs (canonical list — see the verbatim bullet inserted by feature 028 / US4 elsewhere in this section). (See `specs/028-capstone-alignment/contracts/meta-spec-flag.contract.md`; the verbatim canonical bullet is added in US4.)


