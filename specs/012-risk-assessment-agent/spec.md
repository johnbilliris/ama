# Feature Specification: Risk Assessment Agent — Hazard Prediction, Recommendation Generation, and Multi-Agent Escalation

**Feature Branch**: `012-risk-assessment-agent`  
**Created**: 2026-04-15  
**Status**: Draft  
**Input**: User description: "The Risk Assessment Agent receives handoffs from the Monitoring Agent containing escalated signals. It must generate hazard impact predictions using LLM with traceable reasoning, produce versioned recommendations with confidence scores, incorporate data freshness and multi-source correlation, escalate to Communication Agent for high-confidence public alert recommendations, trigger Evacuation and Resource Allocation agents when relevant, support reproducible predictions for scenario-based testing, and maintain full audit trail of all assessments."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Receive Escalated Handoff and Generate Hazard Impact Prediction (Priority: P1)

An emergency operations coordinator is monitoring an active bushfire incident. The Monitoring Agent has triaged a cluster of high-confidence fire and weather signals and created handoff events targeting the Risk Assessment Agent. The Risk Assessment Agent receives these handoffs, retrieves the referenced signals and their provenance metadata, correlates the signals with data freshness indicators and existing hazard context, and generates a versioned hazard impact prediction. The prediction includes a spread forecast, affected communities, and a confidence level derived from the quality and freshness of the input signals. The coordinator can inspect the prediction and trace it back to every contributing signal, seeing which data sources were used, how fresh each input was, and what assumptions drove the assessment.

**Why this priority**: This is the Risk Assessment Agent's core function — without hazard predictions from escalated signals, no downstream agent (Communication, Evacuation, Resource Allocation) can take action. The Constitution (Principle I) mandates that the system produce explanations suitable for incident commanders, and (Principle III) requires traceable inputs and versioned, reproducible predictions.

**Independent Test**: Can be fully tested by sending a synthetic `AgentHandoffEvent` with `source_agent=monitoring`, `target_agent=risk_assessment`, and a payload containing a fire-category signal summary, then verifying that the agent produces a versioned `HazardAssessment` record with traceable `input_signal_ids`, a confidence level, and an LLM-generated or template-based summary.

**Acceptance Scenarios**:

1. **Given** an `AgentHandoffEvent` arrives from the Monitoring Agent with a payload containing a fire-category signal summary and a valid incident ID, **When** the Risk Assessment Agent processes the handoff, **Then** it produces a `HazardAssessment` record containing: the assessment type, all input signal IDs, a version number, a confidence level, and a human-readable summary explaining the predicted impact.
2. **Given** multiple handoffs arrive for the same incident within a short time window, **When** the Risk Assessment Agent processes each handoff, **Then** each successive assessment receives a monotonically increasing version number for that incident and assessment type.
3. **Given** a handoff arrives but one or more of the referenced signals have a freshness score below 0.5, **When** the Risk Assessment Agent generates the prediction, **Then** the assessment confidence is reduced to reflect the stale inputs and the summary explicitly notes which inputs had degraded freshness.
4. **Given** a handoff arrives with a payload referencing signal IDs that cannot be retrieved from the signal store, **When** the Risk Assessment Agent attempts to process the handoff, **Then** it logs the missing signal IDs, reduces assessment confidence, and proceeds with available data rather than failing entirely.

---

### User Story 2 — Generate Recommendation and Escalate to Communication Agent (Priority: P2)

An incident commander is overseeing a severe cyclone approaching a populated coastal region. The Risk Assessment Agent has produced a high-confidence hazard prediction indicating significant community impact. Based on this assessment, the agent generates a `Recommendation` of type `public_alert`, including a concise explanation that references every contributing signal ID for traceability, a confidence level, and an approval requirement. Because the recommendation is high-confidence and of type `public_alert`, the agent builds a handoff to the Communication Agent with the recommendation payload. The incident commander can see in the audit trail that the recommendation was generated, why it was generated (with signal references), and that a handoff to the Communication Agent was initiated.

**Why this priority**: Generating actionable recommendations and escalating to the Communication Agent for public alerts is the primary output of the Risk Assessment Agent. The Constitution (Principle II) mandates explicit cross-agent handoffs with inputs, outputs, confidence, and timestamps. Without this capability, risk assessments remain informational but do not drive protective action.

**Independent Test**: Can be fully tested by providing the agent with signal IDs and an incident ID, invoking the recommendation generation, and verifying that a `Recommendation` with type `public_alert` is produced with signal references in the explanation, and that a `communication` handoff event is created when confidence is high.

**Acceptance Scenarios**:

1. **Given** the Risk Assessment Agent has a high-confidence hazard assessment (confidence score ≥ 0.7) for an incident, **When** it generates a `Recommendation` of type `public_alert`, **Then** the recommendation explanation includes all contributing signal IDs, and the agent creates an `AgentHandoffEvent` targeting `communication` with the recommendation ID, summary, and explanation in the payload.
2. **Given** the Risk Assessment Agent generates a `Recommendation` of type `public_alert` with confidence score < 0.7, **When** the handoff logic is evaluated, **Then** no handoff to the Communication Agent is created; the recommendation is stored for human review.
3. **Given** the Risk Assessment Agent generates a recommendation, **When** the recommendation is persisted, **Then** it includes the `required_approval_level` (default: `incident_commander`), the `proposed_by_agent` field set to `risk_assessment`, and the `generation_method` indicating whether the explanation was LLM-generated, template-based, or a safety fallback.

---

### User Story 3 — Escalate to Evacuation and Resource Allocation Agents (Priority: P3)

A major flood event is developing across multiple jurisdictions. The Risk Assessment Agent has produced a hazard assessment indicating that community infrastructure is at risk and evacuation routes may be compromised. Based on the assessment type and severity, the agent generates recommendations of type `evacuation` and `resource_allocation` in addition to any public alert recommendation. For each high-confidence recommendation of these types, the agent creates a handoff to the corresponding downstream agent (Evacuation Agent or Resource Allocation Agent) with the relevant assessment data. The incident commander can trace which assessments triggered which downstream agent activations.

**Why this priority**: Multi-agent escalation beyond the Communication Agent is essential for coordinated disaster response. The Constitution (Principle II) requires that each agent's responsibilities be clear and that cross-agent handoffs be explicit. Without escalation to Evacuation and Resource Allocation agents, the hub cannot coordinate protective actions beyond public alerts.

**Independent Test**: Can be fully tested by providing a hazard assessment with `assessment_type=route_risk` or `community_impact` and verifying that `evacuation` and `resource_allocation` recommendations are generated, and handoff events target the appropriate downstream agents.

**Acceptance Scenarios**:

1. **Given** the Risk Assessment Agent produces a hazard assessment with `assessment_type=route_risk`, severity ≥ `high`, and confidence score ≥ 0.6, **When** recommendation generation is triggered, **Then** the agent produces a `Recommendation` of type `evacuation` and creates an `AgentHandoffEvent` targeting the `evacuation` agent.
2. **Given** the Risk Assessment Agent produces a hazard assessment with `assessment_type=community_impact` that generates coordination tasks, **When** recommendation generation is triggered, **Then** the agent produces a `Recommendation` of type `resource_allocation` and creates an `AgentHandoffEvent` targeting the `resource_allocation` agent.
3. **Given** a hazard assessment has severity < `high` or confidence score < 0.6 for evacuation, and no coordination tasks for resource allocation, **When** downstream escalation is evaluated, **Then** no handoff events are created for Evacuation or Resource Allocation agents; the recommendation is stored for human review only.

---

### User Story 4 — Contradictory Signal Detection and Confidence Adjustment (Priority: P4)

During an active bushfire, the Risk Assessment Agent receives multiple handoffs referencing signals from different sources. One signal from an authoritative weather service indicates wind change driving fire away from a township, while a community sensor signal indicates rapidly increasing temperatures at the same township. The Risk Assessment Agent detects the contradiction between these signals, flags them in the assessment summary, reduces the overall confidence level of the prediction, and explicitly notes the conflicting inputs so that the incident commander can make an informed decision. The assessment is still produced, but with a clear indication that conflicting data exists and which sources disagree.

**Why this priority**: The Constitution (Principle III) requires the system to detect and flag contradictory or suspicious inputs and reduce confidence accordingly. Contradictory signals are common during disasters, and surfacing them — rather than silently averaging or ignoring — is essential for incident commander trust in the system.

**Independent Test**: Can be fully tested by providing two signals for the same location with opposing implications (e.g., one indicating decreasing risk, one indicating increasing risk), and verifying that the assessment summary flags the contradiction, names the disagreeing sources, and reduces the confidence level.

**Acceptance Scenarios**:

1. **Given** the Risk Assessment Agent receives two or more signals for the same incident and geographic area that indicate opposing risk trajectories, **When** hazard assessment is generated, **Then** the assessment summary explicitly identifies the contradiction, names the disagreeing data sources, and the confidence level is reduced below what either signal alone would produce.
2. **Given** the Risk Assessment Agent detects contradictory signals, **When** the assessment is produced, **Then** an audit record is created documenting the contradiction, the signal IDs involved, and the confidence adjustment applied.
3. **Given** all input signals for an assessment are consistent and from authoritative sources, **When** hazard assessment is generated, **Then** no contradiction flag is raised and the confidence level reflects the quality of the inputs.

---

### User Story 5 — Reproducible Predictions for Scenario-Based Testing (Priority: P5)

A resilience planner runs a rehearsal scenario simulating a Category 5 cyclone making landfall in Far North Queensland. The planner replays the exact same signal inputs and handoff sequence from a previous exercise. The Risk Assessment Agent, given identical inputs (same signal IDs, same freshness scores, same provenance), produces the same hazard assessment version, the same confidence level, and the same recommendations — demonstrating reproducibility. The planner can compare the outputs side-by-side to verify consistency and evaluate the impact of any model or configuration changes between runs.

**Why this priority**: The Constitution (Principle III) mandates that hazard maps and predictions be versioned and reproducible given the same inputs. The Quality Gates section requires scenario-based testing for bushfire, cyclone, and flood. Reproducibility is essential for validating system behaviour, regulatory compliance, and post-incident learning.

**Independent Test**: Can be fully tested by running the same set of signal inputs through the agent twice and verifying that both runs produce identical hazard assessments (same confidence, same summary structure, same recommendation types) when no model or configuration changes have occurred.

**Acceptance Scenarios**:

1. **Given** a set of input signals and handoff payloads from a recorded scenario, **When** the Risk Assessment Agent processes them in a simulation tenant, **Then** the hazard assessments and recommendations produced are identical to those produced in a previous run with the same inputs and configuration.
2. **Given** a model or configuration change has occurred between two scenario runs, **When** the Risk Assessment Agent processes the same inputs, **Then** the agent records the configuration version used in each assessment, enabling the planner to attribute any output differences to the specific change.
3. **Given** a scenario run is executed in a simulation tenant, **When** assessments and recommendations are produced, **Then** they are isolated from live incident data and do not trigger real downstream agent handoffs.

---

### User Story 6 — Audit Trail of All Assessments and Decisions (Priority: P6)

After a multi-day flood event, the post-incident review team requests a complete record of every assessment and recommendation the Risk Assessment Agent made during the event. The review team retrieves a chronological log showing every handoff received, every hazard assessment generated (with version history), every recommendation produced, every downstream handoff created, every contradiction detected, and every degradation event. Each entry includes timestamps, input signal references, confidence scores, generation method, and the reasoning or assumptions that drove the output.

**Why this priority**: The Constitution (Non-Functional Requirements) mandates an append-only audit trail for safety-critical recommendations and actions. Full traceability is essential for post-incident reviews, continuous improvement, regulatory accountability, and maintaining public and inter-agency trust.

**Independent Test**: Can be fully tested by processing a sequence of handoffs resulting in assessments and recommendations, then querying the audit trail to verify that every processing step produced a corresponding record with the required fields.

**Acceptance Scenarios**:

1. **Given** the Risk Assessment Agent processes any incoming handoff, **When** the processing completes, **Then** an audit record is created containing: handoff ID, signal IDs, assessment ID (if produced), recommendation ID (if produced), decision type, confidence level, generation method, and timestamp.
2. **Given** the Risk Assessment Agent produces a hazard assessment, **When** the assessment is versioned and persisted, **Then** an audit record links the assessment version to its input signals, configuration version, and any contradictions detected.
3. **Given** the Risk Assessment Agent creates a downstream handoff to Communication, Evacuation, or Resource Allocation agents, **When** the handoff is delivered or dead-lettered, **Then** an audit record captures the handoff event ID, target agent, delivery status, and the recommendation that triggered the handoff.

---

### User Story 7 — Graceful Degradation When Data or Services Are Unavailable (Priority: P7)

During a severe storm, the LLM service used for generating assessment explanations becomes temporarily unavailable. The Risk Assessment Agent continues to receive handoffs from the Monitoring Agent and must still produce hazard assessments. It falls back to template-based assessment summaries (using structured signal data without LLM enrichment) and marks all outputs with a reduced confidence annotation reflecting the absence of LLM reasoning. When the LLM service recovers, the agent resumes generating enriched explanations. Throughout the outage, all degradation events are logged and assessments carry clear indicators of the degraded generation method.

**Why this priority**: The Constitution (Principle I) mandates that the system degrade safely — falling back to conservative guidance if confidence drops or data is stale. During a disaster, the Risk Assessment Agent must never halt entirely; reduced-quality output is vastly preferable to no output.

**Independent Test**: Can be fully tested by disabling the LLM client (or configuring it to return errors), sending handoffs to the agent, and verifying that assessments are still produced with `generation_method=template_fallback` and a reduced confidence annotation.

**Acceptance Scenarios**:

1. **Given** the LLM service is unavailable, **When** the Risk Assessment Agent processes a handoff, **Then** it produces a hazard assessment using a template-based summary with `generation_method=template_fallback`, a reduced confidence level, and a degradation annotation.
2. **Given** the LLM service becomes available again, **When** the next handoff is processed, **Then** the agent resumes LLM-based generation with `generation_method=llm` and logs the recovery event.
3. **Given** a subset of input signals cannot be retrieved from the signal store, **When** the Risk Assessment Agent generates an assessment, **Then** the assessment is produced using available signals, the missing signals are documented in the audit trail, and the confidence level is reduced proportionally.

---

### Edge Cases

- What happens when a handoff arrives referencing an incident ID that does not exist in the incident store? The agent logs the error, records a `handoff_rejected` audit entry, and does not produce an assessment.
- What happens when all input signals for an assessment are stale (freshness score below the configurable staleness threshold, default 0.5 per `STALE_SIGNAL_THRESHOLD`)? The agent produces an assessment with `confidence_level=low`, explicitly notes the staleness in the summary, and does not escalate to downstream agents.
- What happens when the same handoff ID is received more than once (duplicate delivery)? The agent performs idempotency checking on handoff ID and discards duplicates, logging the discard in the audit trail.
- What happens when the LLM generates an explanation that fails content safety validation? The agent replaces the explanation with a structured template fallback, records the content safety failure in the audit trail, and continues processing.
- What happens when a handoff arrives from a simulation tenant? The agent processes the handoff in the simulation context, produces assessments and recommendations isolated from live data, and does not create real downstream handoffs to live agents.
- What happens when the Risk Assessment Agent itself becomes unhealthy? The health endpoint reports unhealthy status, the hosting platform detects the failure and restarts the agent, and unprocessed handoffs are re-delivered from the messaging infrastructure.
- What happens when a handoff arrives for a non-escalation-eligible recommendation type? The agent processes the handoff normally and produces a recommendation, but no downstream handoff is created unless the recommendation type and confidence meet the escalation criteria.

## Requirements *(mandatory)*

### Functional Requirements

#### Handoff Intake and Signal Retrieval

- **FR-001**: The Risk Assessment Agent MUST consume `AgentHandoffEvent` records where `target_agent=risk_assessment` from the Monitoring Agent via Azure Service Bus. The agent MUST acknowledge receipt of each handoff within 5 seconds of delivery. The agent MUST validate the handoff structure and reject malformed handoffs with an audit record.
- **FR-002**: Upon receiving a valid handoff, the Risk Assessment Agent MUST retrieve the referenced signals from the signal store using the signal IDs provided in the handoff payload.
- **FR-003**: The Risk Assessment Agent MUST perform idempotency checking on `handoff_id` to avoid processing the same handoff twice within a configurable deduplication window (default: 10 minutes, configurable via environment variable `HANDOFF_DEDUP_WINDOW_MINUTES`). Duplicate handoffs MUST be discarded and the discard recorded in the audit trail.
- **FR-004**: The Risk Assessment Agent MUST validate that the `incident_id` referenced in the handoff exists in the incident store. If the incident does not exist, the handoff MUST be rejected with a `rejected_handoff` audit record.

#### Hazard Assessment Generation

- **FR-005**: The Risk Assessment Agent MUST generate a `HazardAssessment` record for each valid handoff, containing: assessment type (derived from signal categories), all input signal IDs, a version number, a confidence level, a `valid_until` timestamp (configurable per hazard type, default 4 hours), a generation timestamp, and a human-readable summary.
- **FR-006**: The `HazardAssessment` version number MUST increase monotonically per incident and assessment type, using the format `ha-{incident_id}-{type}-v{N}` where `{type}` is the assessment type (e.g., `spread_prediction`) and N starts at 1 (e.g., `ha-inc001-spread_prediction-v1`). Versions MUST be immutable once created — new assessments create new versions, never overwrite existing ones. The version MUST be assigned at persistence time to ensure consistency. Status-only transitions (`active` → `superseded`/`expired` per FR-010b) are permitted on otherwise immutable records.
- **FR-007**: The Risk Assessment Agent MUST compute a raw numeric confidence score (0.0–1.0) by considering: input signal confidence scores, input signal freshness scores, the number and diversity of corroborating sources, and any detected contradictions. The raw score MUST also be mapped to a discrete confidence level (`low` < 0.4, `medium` 0.4–0.69, `high` ≥ 0.7) for display and human consumption. Escalation rules use the raw numeric score and escalation-specific thresholds (see FR-020 through FR-022).
- **FR-008**: The assessment summary MUST be generated using an LLM when available, with a template-based fallback when the LLM is unavailable. All LLM outputs MUST pass through content safety validation before inclusion in the assessment.
- **FR-009**: The assessment summary MUST include traceable references to the input signals — specifically, signal IDs MUST appear in the summary text so that incident commanders can trace the assessment back to its contributing data.
- **FR-010**: The Risk Assessment Agent MUST map signal categories to assessment types using the following default mapping (configurable per incident type):
  - `fire` → `spread_prediction`
  - `weather`, `hydrology` → `impact_projection`
  - `infrastructure` → `infrastructure_risk`
  - `community_report`, `social_report` → `community_impact`
  - `geohazard` → `impact_projection`
- **FR-010a**: The Risk Assessment Agent MUST support at minimum the following disaster scenario types, each with scenario-specific risk calculation parameters: bushfire (NSW/VIC), cyclone (QLD/NT), flood (QLD/NSW), earthquake (national), and tsunami (coastal). The scenario type MUST be derived from the incident type and geographic context, and MUST influence assessment severity thresholds, risk model selection, and recommendation triggers.
- **FR-010b**: Each `HazardAssessment` MUST include a `valid_until` timestamp, calculated as `generation_timestamp + validity_duration`. The `validity_duration` MUST be configurable per hazard type (default: 4 hours, configurable via `ASSESSMENT_VALIDITY_HOURS_{HAZARD_TYPE}`). After `valid_until` elapses, the assessment MUST be marked `superseded` if a newer version for the same incident and assessment type exists, or `expired` if no newer version exists. Expired/superseded assessments remain queryable but MUST NOT drive new downstream escalations.
- **FR-010c**: Each assessment MUST be scoped to a single incident ID. The Risk Assessment Agent MUST NOT correlate signals across separate incidents in v1. However, the data model MUST NOT prevent future cross-incident correlation (v2) — specifically, assessment and recommendation records MUST support optional `related_incident_ids` metadata without schema changes.
- **FR-010d**: Each `HazardAssessment` MUST include a `severity_level` using a 4-level enum aligned with the Australian Institute for Disaster Resilience (AIDR) emergency management framework: `low` (minimal impact expected), `moderate` (potential threat), `high` (significant threat within hours), `critical` (immediate life threat). Severity MUST be computed from the combination of signal category, confidence score, and affected population estimate. The severity level is distinct from the confidence level — confidence measures input data quality and source agreement, while severity measures assessed impact magnitude on people and infrastructure.

#### Multi-Source Correlation and Contradiction Detection

- **FR-011**: When multiple signals for the same incident and geographic area are available, the Risk Assessment Agent MUST correlate them using weighted averaging where authoritative sources (Bureau of Meteorology, Geoscience Australia) receive 2× weight, IoT sensors receive 1× weight, and social media sources receive 0.5× weight. The correlation MUST identify patterns of agreement or disagreement across sources.
- **FR-012**: The Risk Assessment Agent MUST detect contradictory signals — signals that indicate opposing risk trajectories for the same area — and flag the contradiction in the assessment summary with the names of the disagreeing data sources. Both perspectives MUST be included in the recommendation explanation so that incident commanders can evaluate the conflicting evidence.
- **FR-013**: When contradictory signals are detected, the Risk Assessment Agent MUST reduce the overall confidence score by 30%, flag the assessment for human review, and include both perspectives in the recommendation explanation. The contradiction and the confidence adjustment MUST be recorded in the audit trail.
- **FR-014**: The Risk Assessment Agent MUST apply source weighting consistent with the multi-source correlation weights defined in FR-011 (authoritative 2×, IoT 1×, social 0.5×) when resolving ambiguity, and MUST explicitly note when the assessment relies primarily on unverified or crowd-sourced inputs.

#### Data Freshness Integration

- **FR-015**: The Risk Assessment Agent MUST consider the `freshnessScore` of each input signal when computing assessment confidence. Signals with freshness scores below a configurable threshold (default: 0.5, configurable via environment variable `STALE_SIGNAL_THRESHOLD`) MUST be flagged as stale in the assessment summary.
- **FR-016**: If all input signals for an assessment have freshness scores below the staleness threshold, the Risk Assessment Agent MUST set the assessment `confidence_level` to `low` and MUST NOT escalate any resulting recommendations to downstream agents.

#### Recommendation Generation

- **FR-017**: The Risk Assessment Agent MUST generate one or more `Recommendation` records based on the hazard assessment. Each recommendation MUST include: a recommendation ID, incident ID, type (one of: `evacuation`, `resource_allocation`, `coordination`, `public_alert`, `infrastructure_action`), a summary, an explanation with signal ID references, supporting signal IDs, a required approval level, a confidence level, a generation method, and the `proposed_by_agent` field set to `risk_assessment`.
- **FR-018**: The recommendation explanation MUST include all contributing signal IDs. If the LLM-generated explanation omits any signal ID, the agent MUST append the missing signal references to the explanation.
- **FR-019**: The `required_approval_level` for recommendations MUST default to `incident_commander` for all recommendation types. This is configurable per recommendation type via environment variables.

#### Downstream Agent Escalation

- **FR-020**: The Risk Assessment Agent MUST create an `AgentHandoffEvent` targeting the `communication` agent when a `Recommendation` of type `public_alert` has a confidence score ≥ 0.7 (lower than the Monitoring Agent's 0.8 threshold because the monitoring agent has already filtered). The handoff payload MUST include the recommendation ID, summary, and explanation.
- **FR-021**: The Risk Assessment Agent MUST create an `AgentHandoffEvent` targeting the `evacuation` agent when a `Recommendation` of type `evacuation` has severity ≥ `high` AND confidence score ≥ 0.6. The handoff payload MUST include the recommendation ID, summary, and the relevant hazard assessment ID.
- **FR-022**: The Risk Assessment Agent MUST create an `AgentHandoffEvent` targeting the `resource_allocation` agent when a hazard assessment generates coordination tasks, regardless of a specific confidence threshold. The handoff payload MUST include the recommendation ID, summary, and the relevant hazard assessment ID.
- **FR-023**: Handoff delivery to downstream agents MUST use exponential backoff with a maximum of 3 retries. If all retries are exhausted, the handoff MUST be dead-lettered and the dead-letter event MUST be surfaced to incident commanders.
- **FR-024**: When no escalation threshold is met (i.e., confidence score < 0.7 for public alerts, severity < `high` or confidence score < 0.6 for evacuation, and no coordination tasks for resource allocation), the Risk Assessment Agent MUST NOT create downstream agent handoffs. Recommendations below threshold MUST be stored for human review only.

#### Reproducibility

- **FR-025**: The Risk Assessment Agent MUST store the complete input snapshot with each assessment, including: all input signals (with their confidence scores, freshness scores, and provenance), model version, prompt template version, configuration thresholds, and the LLM deployment ID. This enables full reproducibility verification and post-incident auditing.
- **FR-026**: Given identical input signals (same IDs, same freshness scores, same provenance) and identical configuration version, the Risk Assessment Agent MUST produce identical hazard category, severity, and recommendation types. LLM temperature MUST be set to 0 for deterministic outputs to ensure reproducibility.
- **FR-027**: The Risk Assessment Agent MUST support processing handoffs in simulation tenant contexts per spec 007. Assessments and recommendations produced in simulation MUST be isolated from live data and MUST NOT trigger handoffs to live downstream agents.

#### Audit Trail

- **FR-028**: The Risk Assessment Agent MUST produce an audit record for every processing step, including: handoff receipt, signal retrieval, assessment generation, recommendation generation, downstream handoff creation, contradiction detection, degradation events, duplicate handoff discard, and content safety failures.
- **FR-029**: Each audit record MUST be stored in Cosmos DB (append-only, no TTL) and MUST include: handoff ID, input_signals, assessment_result, confidence (raw score and categorical level), version, model_used, prompt_template_version, processing_duration, decision_rationale, generation method, agent version, configuration version, and timestamp.
- **FR-030**: The audit trail MUST be append-only with no TTL. Existing records MUST NOT be modified or deleted. Cosmos DB is the designated persistence store for all risk assessment audit records.

#### Graceful Degradation

- **FR-031**: When Azure OpenAI is unavailable, the Risk Assessment Agent MUST fall back to rule-based assessment using signal category and confidence thresholds only. No LLM-generated explanations are used in fallback mode — only template-based explanations. Confidence MUST be reduced by 20% in fallback mode. All fallback outputs MUST carry `generation_method=template_fallback`. In fallback mode, severity MUST be computed using the following default signal-category-to-severity mapping: `fire` → `high`, `cyclone` → `critical`, `flood` → `high`, `earthquake` → `critical`, `tsunami` → `critical`; all other signal categories default to `moderate`. The mapped severity MAY be downgraded by one level if the confidence score (after 20% reduction) falls below 0.4.
- **FR-032**: When the signal store is partially unavailable and some referenced signals cannot be retrieved, the Risk Assessment Agent MUST produce assessments using the available signals, document the missing signals in the audit trail, and reduce the assessment confidence proportionally.
- **FR-033**: The Risk Assessment Agent MUST expose a `/health` endpoint that reports agent readiness. The health response MUST include: LLM connectivity status, signal store connectivity status, and processing queue depth. The endpoint MUST respond within 1 second under normal operation.
- **FR-034**: The Risk Assessment Agent MUST NOT halt entirely when any single dependency (LLM, signal store, downstream agent) is unavailable. It MUST continue processing with degraded capabilities and log all degradation events.

#### Content Safety

- **FR-035**: All LLM-generated outputs (assessment summaries, recommendation explanations) MUST pass through `ContentSafetyValidator` before inclusion in any persisted record or handoff payload. If validation fails, the output MUST be replaced with a structured template fallback and the failure recorded in the audit trail. Template-based fallback text is pre-approved and does NOT require runtime content safety checks.
- **FR-036**: All LLM interactions MUST use system prompts that scope the model's role to disaster risk assessment and MUST NOT allow the model to be repurposed via prompt injection from signal content.

#### Human Override

- **FR-037**: Incident commanders MUST be able to override any recommendation's status (`approve`, `reject`, `modify`). An override MUST update the recommendation's `status` field and record the `override_by_user_id`, `override_by_role`, `override_justification`, and `override_timestamp` in both the recommendation record and the audit trail.
- **FR-038**: When an incident commander modifies a recommendation, the modified recommendation MUST be stored as a new version linked to the original, preserving the original recommendation intact. The override audit record MUST be append-only and immutable, consistent with the Constitution's human override mandate.

### Non-Functional Requirements

#### Scalability

- **NFR-001**: The Risk Assessment Agent MUST handle at minimum 100 concurrent assessments during peak disaster events. This is lower than the Monitoring Agent's 1,000 signals/min capacity because the Monitoring Agent filters before escalation. Azure Container Apps auto-scaling MUST be used to scale assessment processing capacity horizontally based on Service Bus queue depth.

#### Observability

- **NFR-002**: The Risk Assessment Agent MUST emit telemetry to Azure Monitor / Application Insights. The following metrics MUST be tracked: `assessment_latency` (p50, p95, p99), `escalation_rate_by_type` (per recommendation type), `contradiction_detection_rate` (percentage of assessments with contradictions), `fallback_mode_activations` (count per time window), `handoff_success_rate` (delivery vs. dead-letter ratio), and `version_count_per_incident` (assessment versions produced per incident). All metrics MUST support alerting thresholds.

### Key Entities

- **HazardAssessment**: A versioned prediction of hazard impact produced by fusing and analysing escalated signals. Key attributes: assessment ID, incident ID, assessment type (spread prediction, impact projection, route risk, infrastructure risk, community impact), input signal IDs, version number (format: `ha-{incident_id}-{type}-v{N}`), confidence score (0.0–1.0) and confidence level (low/medium/high), severity level (`low`/`moderate`/`high`/`critical` per AIDR framework — computed from signal category, confidence, and affected population; distinct from confidence level), summary, generation timestamp, `valid_until` timestamp (configurable per hazard type, default 4 hours), status (`active`, `superseded`, `expired`), generation method, configuration version, optional `related_incident_ids` (reserved for v2 cross-incident correlation), `hazard_map` (structured JSON: `affected_area` as GeoJSON polygon, `severity_level`, `hazard_type`, `confidence_score`, `time_horizon`, `population_estimate`), and complete input snapshot for reproducibility. Each assessment is immutable once persisted — new assessments create new versions, never overwrite. Status-only transitions (`active` → `superseded`/`expired`) are the sole permitted mutation. Versions increase monotonically per incident and assessment type. Hazard maps are stored as structured JSON in Cosmos DB; graphical rendering is the web UI's responsibility.

- **Recommendation**: A proposed protective action generated from a hazard assessment. Key attributes: recommendation ID, incident ID, type (evacuation, resource allocation, coordination, public alert, infrastructure action), summary, explanation (with signal ID references), supporting signal IDs, required approval level, confidence level, status (proposed → under review → approved/rejected/escalated → executed/expired), `override_by_user_id` (optional), `override_by_role` (optional), `override_justification` (optional), `override_timestamp` (optional), proposed-by agent, generation method, model deployment ID, and token usage. Recommendations are the primary output consumed by downstream agents and human decision-makers. Incident commanders can override any recommendation's status; overrides are logged immutably in the audit trail.

- **RiskAssessmentDecisionRecord**: An audit trail entry capturing a single processing step or decision made by the Risk Assessment Agent. Key attributes: record ID, handoff ID, signal IDs, assessment ID (when applicable), recommendation ID (when applicable), decision type (handoff_received, handoff_rejected, duplicate_discarded, signals_retrieved, assessment_generated, recommendation_generated, handoff_created, handoff_delivered, handoff_dead_lettered, contradiction_detected, degradation_detected, content_safety_failure), confidence level, generation method, configuration version, agent version, reasoning summary, and timestamp. Append-only; no updates or deletes permitted.

- **AgentHandoffEvent**: An explicit handoff record created when the Risk Assessment Agent escalates a recommendation to a downstream agent (Communication, Evacuation, or Resource Allocation). Key attributes: handoff ID, incident ID, source agent (`risk_assessment`), target agent, scope key, confidence, payload (containing recommendation ID, summary, and explanation or assessment ID), tenant ID, status, retry count, and timestamps. Created by the Risk Assessment Agent; consumed by downstream agents.

### Assumptions

- The Monitoring Agent (spec 010) delivers handoffs in the `AgentHandoffEvent` format with all required fields populated, including signal summary in the payload, incident ID, and confidence score. The Risk Assessment Agent does not re-triage or re-validate signal escalation eligibility.
- Signals referenced in handoff payloads are retrievable from the signal store (spec 006). If signals are missing, the agent degrades gracefully rather than failing.
- The LLM client uses Azure OpenAI with content safety filters enabled. The `_generate_with_fallback` method from `LLMCallMixin` provides the primary generation pattern with automatic template fallback. When Azure OpenAI is unavailable, rule-based fallback applies with 20% confidence reduction and severity computed from default signal-category-to-severity mappings (see FR-031).
- Downstream escalation uses numeric confidence thresholds: ≥ 0.7 for Communication (public alerts), severity ≥ "high" AND ≥ 0.6 for Evacuation, and coordination task generation for Resource Allocation. Recommendations below threshold are stored for human review.
- The `required_approval_level` for all recommendation types defaults to `incident_commander`. The system supports but does not replace human authority over safety-critical decisions.
- The assessment type mapping from signal categories is configurable per incident type but ships with sensible defaults derived from Australian disaster response patterns.
- Tenant isolation (simulation vs. live) is enforced at the data layer per spec 007. The Risk Assessment Agent respects tenant boundaries for all assessments, recommendations, and downstream handoffs.
- The Communication, Evacuation, and Resource Allocation agents are the downstream consumers of Risk Assessment handoffs. Their internal processing is out of scope for this specification.
- Data freshness thresholds for staleness (default 0.5) are consistent with the Monitoring Agent's freshness tracking but may be tuned independently for risk assessment purposes.
- Each assessment is scoped to a single incident. Cross-incident correlation (e.g., compound disasters) is explicitly deferred to v2. The data model supports optional `related_incident_ids` to avoid blocking future cross-incident work.
- Handoff delivery from the Monitoring Agent uses Azure Service Bus as the messaging transport. The Risk Assessment Agent acts as a Service Bus consumer with at-least-once delivery semantics.

### Out of Scope

- Replacement of incident commander authority over evacuation orders, resource deployment, or public alert publication.
- Direct generation of public alerts — the Risk Assessment Agent recommends alerts but does not compose or publish them (that is the Communication Agent's responsibility).
- Evacuation route calculation or resource inventory management — the Risk Assessment Agent recommends actions but delegates detailed planning to the Evacuation and Resource Allocation agents.
- Re-triage of signals — the Monitoring Agent is responsible for signal triage; the Risk Assessment Agent consumes already-escalated signals.
- Real-time geospatial visualisation or hazard map rendering — the agent produces structured JSON hazard map data (GeoJSON polygons, severity, confidence, time horizon, population estimate) stored in Cosmos DB; graphical rendering is the web UI's responsibility and out of scope for this agent.
- Cross-incident correlation and compound disaster analysis — deferred to v2. Each assessment is scoped to a single incident in v1, but the data model preserves optional `related_incident_ids` to avoid blocking future cross-incident work.

### Dependencies

- **spec 001 (Disaster Response Hub)**: Defines the Signal, Recommendation, HazardAssessment, AgentHandoffEvent, and TimelineEvent data models that the Risk Assessment Agent operates on.
- **spec 005 (Data Source Governance)**: Defines the data source registry and trust tiers that inform how the Risk Assessment Agent weighs signals from different sources.
- **spec 006 (Data Ingestion & Storage)**: Defines the signal store that the Risk Assessment Agent queries to retrieve referenced signals and their provenance.
- **spec 007 (Simulation & Tenant Isolation)**: Defines the tenant isolation model that the Risk Assessment Agent must respect for simulation vs. live processing.
- **spec 010 (Monitoring Agent)**: Defines the upstream agent that produces handoffs consumed by the Risk Assessment Agent. The handoff format, escalation criteria, and signal summary structure are defined in spec 010.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Hazard assessments are produced within 10 seconds of receiving a valid handoff from the Monitoring Agent, ensuring timely downstream escalation during active incidents. If processing exceeds 10 seconds, the assessment MUST still complete but MUST log an SLA breach event with the actual processing duration.
- **SC-002**: 100% of hazard assessments include traceable signal ID references — every input signal that contributed to the assessment is identifiable in the assessment summary and audit trail.
- **SC-003**: Contradictory signals are detected and flagged in at least 95% of cases where two or more signals indicate opposing risk trajectories for the same geographic area, as measured against a labelled test set.
- **SC-004**: Given identical inputs and configuration, the Risk Assessment Agent produces identical assessment confidence levels and recommendation types in 100% of reproducibility test runs.
- **SC-005**: When the LLM service is unavailable, the Risk Assessment Agent continues producing assessments using template fallbacks within 10 seconds, with no processing interruption — measured as 0% handoff drop rate during LLM outage periods.
- **SC-006**: Every processing step has a corresponding audit record — audit completeness is 100% verifiable via reconciliation of handoff IDs processed vs. audit records created.
- **SC-007**: High-confidence recommendations trigger downstream agent handoffs within 15 seconds of assessment completion, supporting the constitution's target of 50% reduction in coordinated response time.
- **SC-008**: At least 90% of incident commanders in scenario-based exercises rate the assessment explanations as clear and traceable, using a structured post-exercise survey with a 5-point rubric across clarity, traceability, and decision confidence.

## Clarifications

### Session 2026-04-11

- Q: What versioning format should HazardAssessment use, and are versions mutable? → A: Use `{incident_id}_v{N}` format with monotonically increasing N. Versions are immutable once created — new assessments create new versions, never overwrite.
- Q: What numeric confidence thresholds trigger escalation to each downstream agent? → A: Communication Agent: confidence ≥ 0.7 (lower than monitoring's 0.8 since monitoring already filtered). Evacuation: severity ≥ "high" AND confidence ≥ 0.6. Resource Allocation: any assessment generating coordination tasks.
- Q: How should multi-source signals be correlated and weighted? → A: Weighted averaging with authoritative sources (BoM, GA) at 2× weight, IoT at 1× weight, and social media at 0.5× weight.
- Q: How should contradictory signals be handled quantitatively? → A: Reduce overall confidence by 30%, flag for human review, include both perspectives in recommendation explanation.
- Q: What must be stored for reproducibility, and how is determinism ensured? → A: Store complete input snapshot (all signals, freshness scores, model version, prompt template version). LLM temperature=0 for deterministic outputs.
- Q: What is the LLM fallback behavior when Azure OpenAI is unavailable? → A: Fall back to rule-based assessment using signal category + confidence thresholds. Template-based explanations only (no LLM). Confidence reduced by 20%.
- Q: What are the specific audit record fields and storage requirements? → A: Store in Cosmos DB (append-only, no TTL) with: input_signals, assessment_result, confidence, version, model_used, prompt_template_version, processing_duration, decision_rationale.
- Q: Which disaster scenario types must be supported? → A: Bushfire (NSW/VIC), cyclone (QLD/NT), flood (QLD/NSW), earthquake (national), tsunami (coastal). Each has different risk calculation parameters.

### Session 2026-04-11 (Round 2)

- Q: What is the scalability target for concurrent assessments? → A: Minimum 100 concurrent assessments during peak disaster events (lower than monitoring's 1,000 signals/min because monitoring filters). Azure Container Apps auto-scaling applies.
- Q: What observability metrics must be tracked? → A: Azure Monitor / Application Insights with: `assessment_latency`, `escalation_rate_by_type`, `contradiction_detection_rate`, `fallback_mode_activations`, `handoff_success_rate`, `version_count_per_incident`.
- Q: What is the hazard map data format and storage? → A: Structured JSON in Cosmos DB with: `affected_area` (GeoJSON polygon), `severity_level`, `hazard_type`, `confidence_score`, `time_horizon`, `population_estimate`. Graphical rendering is the web UI's responsibility.
- Q: How should multiple simultaneous incidents be handled? → A: Each assessment scoped to a single incident. Cross-incident correlation deferred to v2. Data model includes optional `related_incident_ids` to avoid blocking future work.
- Q: Do assessments expire? → A: Assessments include `valid_until` timestamp (configurable per hazard type, default 4 hours). After expiry: `superseded` if newer version exists, `expired` if not.
- Q: Can incident commanders override recommendations? → A: Yes — override any recommendation status (approve, reject, modify). Overrides logged in audit trail with user role and justification, per Constitution's human override mandate.
- Q: Must LLM-generated recommendation text pass content safety? → A: Yes, all LLM text must pass `ContentSafetyValidator`. Template-based fallback text is pre-approved and skips runtime safety checks.
- Q: How does the agent receive handoffs from monitoring? → A: Via Azure Service Bus. Acknowledge receipt within 5 seconds, process within 10-second SLA. If processing exceeds 10 seconds, still complete but log SLA breach.

### Session 2026-04-11 (Round 3)

- Q: What are the discrete severity levels, how are they computed, and what does each level mean? → A: 4-level enum aligned with AIDR: `low` (minimal impact expected), `moderate` (potential threat), `high` (significant threat within hours), `critical` (immediate life threat). Computed from signal category, confidence score, and affected population estimate. Severity is distinct from confidence — confidence measures data quality, severity measures impact magnitude.
- Q: When the LLM is unavailable, how is severity computed in rule-based fallback mode? → A: Default signal-category-to-severity mapping: `fire` → `high`, `cyclone` → `critical`, `flood` → `high`, `earthquake` → `critical`, `tsunami` → `critical`; others default to `moderate`. Mapped severity downgraded one level if confidence (after 20% reduction) falls below 0.4.

## Assumptions

Scoped to this spec's domain (hazard risk-index calibration). Tagging follows `specs/027-spec-hardening` taxonomy: `[RISK]` (open externally-driven risk), `[DECISION]` (deliberate scoping decision), bare bullet (operating assumption).

- **ASM-033**: The AU-v1 deployment context defined in `specs/001-disaster-response-hub/spec.md` is the operational baseline for this spec; capstone-country variants (PH / JP / BD) are deferred. `linked_gaps:` `specs/shared/gap-id-register.md` A-GAP-001..003. `status:` Open.
- **ASM-034** [DECISION]: This spec's deliverables (hazard risk-index calibration) integrate with the actor catalogue (`specs/004-actor-github-agents/spec.md`); responsible technical agents - risk-manager, ga-national, ntes, bom-national - are consulted via the `agent` tool during authoring and review.
- **ASM-035**: Speckit conventions (FR/SC numbering, ASM/HYP/PER/SCP families) and the persona-profile YAML schema (`specs/027-spec-hardening/contracts/persona-profile.md`) are authoritative; this spec defers to those rather than redefining them.

## Personas

Authored against the `specs/027-spec-hardening/contracts/persona-profile.md` schema. AU-v1 personas are validated; PH / JP / BD entries are explicit placeholders pending capstone-reinterpretation (D-009) and SME validation per FR-023.

- **PER-028**: cross-ref to `specs/001-disaster-response-hub/spec.md` AIIMS personas (Incident Commander / Planning Officer / Operations Officer / Logistics Officer / Public Information Officer) per `specs/027-spec-hardening/contracts/persona-profile.md`. `status:` validated. `preconditions:` none.
- **PER-029**: cross-ref to `specs/004-actor-github-agents/spec.md` actor catalogue covering all `.github/agents/technical/*.agent.md` actors. `status:` validated. `preconditions:` none.
- **PER-030** [non-AU placeholder]: capstone-country operator personas for PH (NDRRMC), JP (Cabinet Office DRR / FDMA), BD (DDM / CPP volunteers). `status:` placeholder. `preconditions:` capstone-reinterpretation decision per D-009; SME validation via `ama-rubric-grader`-vetted SME interviews.

## Hypotheses

Hypotheses use the FR-018 statement format (`If <condition> then <observable>`) and link to a structured evidence stub conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. Capstone-country hypotheses for this spec's agent ownership (where applicable) are allocated in feature 028 / US2.

- **HYP-010**: If the actors named in `specs/004-actor-github-agents/spec.md` consult on every change to this spec via the `agent` tool, then the AMA rubric criterion mean (Assumptions / Requirements / Personas / Hypotheses / Scope) for this spec rises by at least +1 band relative to the baseline captured in `specs/028-capstone-alignment/evidence/rubric-baseline.md`. **Falsification**: post-feature rubric snapshot shows a regression in any of those five criteria for this spec. **Evidence stub**: `specs/028-capstone-alignment/evidence/HYP-HYP-010.md` (created in feature 028 polish).

## Out of Scope

Items explicitly deferred from this spec; promotion to in-scope requires the named preconditions to clear. Cross-references to other specs use the canonical overlap phrasing (`authoritative for: <capability>` / `defers-to: <NNN> (<capability>)`).

- **SCP-031** [DEFERRED]: Capstone-country variants (PH typhoon, JP earthquake, BD flood) of this spec's capabilities are out of scope until: (i) capstone-reinterpretation decision per D-009; (ii) per-country regulatory + data-sharing preconditions documented in `specs/005-data-source-governance/spec.md` clear; (iii) responsible technical agents (risk-manager, ga-national, ntes, bom-national) sign off on country-specific calibration.
- **SCP-032**: Constitutional-level changes (NON-NEGOTIABLE #1..#5) are not modified by this spec; any tension is documented as `[RISK]` in Assumptions, never resolved here.
- **SCP-033**: Cross-spec authority disputes are arbitrated via `product-owner-ba` and the speckit governance flow; this spec does not unilaterally claim ownership of capabilities owned elsewhere. `defers-to:` 018 (recovery-phase indicators, triggers, phase-exit criteria); 008 (warning-tier authoring, multilingual delivery, misinformation defence) where applicable.


## Capstone-Aligned Requirements (Feature 028 / P-004)

The hazard taxonomy owned here is *extended* - not replaced - to name capstone-country instances of the existing AU hazard classes.

| Hazard class (AU-v1) | Capstone country | Country-scoped instance | Status |
| --- | --- | --- | --- |
| Tropical cyclone (analog) | Philippines | Typhoon (Pacific basin) | Deferred - see ASM [RISK] AU-residency tension |
| Earthquake (existing) | Japan | Subduction-zone earthquake + tsunami | Deferred |
| Riverine flood (existing) | Bangladesh | Monsoon + cyclone-driven coastal flood | Deferred |

> No existing AU hazard row is modified.


## Capstone-Country Hypotheses (Feature 028 / US2)

> Three deferred capstone-country hypotheses for hazard risk-index calibration. Each cites an evidence stub at `specs/012-risk-assessment-agent/evidence/HYP-<id>.md` conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. `Status = Not tested` until D-009 capstone-reinterpretation clears and per-cohort preconditions are met.

- **HYP-039** [PH deferred]: We believe typhoon (Pacific basin) risk-index calibration using PAGASA + historical track data will produce risk-index calibration error <= 15% on out-of-sample historical typhoon events for the Philippines operator persona; we will know we are wrong if calibration error > 25% on out-of-sample PH events during PH typhoon season Jun-Nov is observed in the measurement window (PH typhoon season Jun-Nov).
  - **Falsification**: calibration error > 25% on out-of-sample PH events during PH typhoon season Jun-Nov.
  - **Evidence stub**: `specs/012-risk-assessment-agent/evidence/HYP-039.md` (created by feature 028 / US2 / T034..T038).
- **HYP-040** [JP deferred]: We believe subduction-zone earthquake + tsunami risk-index calibration using JMA + JSHIS data will produce risk-index calibration error <= 10% on out-of-sample historical earthquake events for the Japan operator persona; we will know we are wrong if calibration error > 20% on out-of-sample JP events during quarterly review is observed in the measurement window (JP continuous; quarterly review).
  - **Falsification**: calibration error > 20% on out-of-sample JP events during quarterly review.
  - **Evidence stub**: `specs/012-risk-assessment-agent/evidence/HYP-040.md` (created by feature 028 / US2 / T034..T038).
- **HYP-041** [BD deferred]: We believe monsoon flood + cyclonic-flood risk-index calibration using BWDB + BMD data will produce risk-index calibration error <= 20% on out-of-sample historical flood events for the Bangladesh operator persona; we will know we are wrong if calibration error > 30% on out-of-sample BD events during BD monsoon Apr-Sep is observed in the measurement window (BD monsoon Apr-Sep).
  - **Falsification**: calibration error > 30% on out-of-sample BD events during BD monsoon Apr-Sep.
  - **Evidence stub**: `specs/012-risk-assessment-agent/evidence/HYP-041.md` (created by feature 028 / US2 / T034..T038).

