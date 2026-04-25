# Feature Specification: Monitoring Agent — Signal Triage, Misinformation Detection, and Escalation

**Feature Branch**: `010-monitoring-agent`  
**Created**: 2026-03-26  
**Status**: Draft  
**Input**: User description: "The Monitoring Agent is the first agent in the disaster response pipeline. It receives normalized signals from ingestion pipelines and performs: (1) LLM-powered signal summarization with content safety, (2) misinformation detection on social media signals, (3) confidence-based triage and escalation via handoffs to risk assessment, (4) retrospective incident association, and (5) data freshness tracking. It must support graceful degradation when data sources fail and maintain an audit trail of all decisions."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Signal Triage and Escalation to Risk Assessment (Priority: P1)

An emergency operations coordinator monitors the disaster response hub dashboard. A high-confidence weather signal arrives from the Bureau of Meteorology indicating a severe thunderstorm warning for a jurisdiction with an active bushfire incident. The Monitoring Agent receives the normalised signal, evaluates its category (weather) and confidence score (≥ configurable threshold, default 0.8), determines it is high-risk, and creates an explicit handoff to the Risk Assessment Agent. The handoff includes the signal summary, category, source kind, confidence score, and incident context. The Risk Assessment Agent receives the handoff and begins impact analysis. The coordinator can see in the audit trail exactly when the signal arrived, how it was classified, and when the handoff was created. Escalation-eligible categories include fire, weather, hydrology, earthquake, and tsunami (the latter two sourced from Geoscience Australia).

**Why this priority**: This is the Monitoring Agent's core function — the pipeline cannot proceed without triage and escalation. The Constitution (Principle I) mandates that life-safety signals reach downstream agents as fast as possible, and (Principle II) requires that cross-agent handoffs be explicit with confidence and timestamps.

**Independent Test**: Can be fully tested by sending a synthetic signal with `category=fire`, `confidenceScore=0.85`, and a valid `incidentId` to the Monitoring Agent, and verifying that a correctly-formed handoff event is produced targeting `risk_assessment` with the expected payload.

**Acceptance Scenarios**:

1. **Given** a normalised signal arrives with `category` in {fire, weather, hydrology, earthquake, tsunami}, `confidenceScore >= 0.8`, and a non-null `incidentId`, **When** the Monitoring Agent processes the signal, **Then** it creates a handoff to the Risk Assessment Agent containing the signal summary (category, source kind, incident ID), the confidence score, and a timestamp.
2. **Given** a normalised signal arrives with `category=fire` and `confidenceScore=0.6`, **When** the Monitoring Agent processes the signal, **Then** no handoff is created because the confidence threshold is not met.
3. **Given** a normalised signal arrives with `category=fire`, `confidenceScore=0.9`, but `incidentId` is null, **When** the Monitoring Agent processes the signal, **Then** no handoff is created because there is no associated incident.
4. **Given** a normalised signal arrives with `category=infrastructure` and `confidenceScore=0.95`, **When** the Monitoring Agent processes the signal, **Then** no handoff to Risk Assessment is created because infrastructure is not in the escalation-eligible category set {fire, weather, hydrology, earthquake, tsunami}.
5. **Given** a handoff is successfully created, **When** the handoff event is persisted, **Then** the event includes the source agent (`monitoring`), target agent (`risk_assessment`), incident scope key, payload, confidence, and a creation timestamp.

---

### User Story 2 — Misinformation Detection on Social Media Signals (Priority: P2)

A social media signal flagged as `validationStatus=escalated` by the ingestion pipeline arrives at the Monitoring Agent. This signal contains a community report from social media claiming a major bushfire in an area where no official warnings exist. The Monitoring Agent's Tier 2 evaluation uses an LLM to assess the credibility of the escalated signal. The LLM determines the content is misinformation — a recycled photo from a previous year's fire. The Monitoring Agent blocks the handoff, preventing the false alarm from reaching the Risk Assessment Agent. The decision is recorded in the audit trail with the classification result and reasoning.

**Why this priority**: The Constitution (Principle III) requires that the system detect and flag contradictory or suspicious inputs and reduce confidence accordingly. Social media misinformation during disasters can cause panic, divert resources, and endanger lives. Blocking misinformation before it reaches downstream agents is essential for system trustworthiness.

**Independent Test**: Can be fully tested by sending a signal with `validationStatus=escalated` and `source.kind=social` to the Monitoring Agent with a mock LLM client configured to return "misinformation", and verifying that no handoff is produced and the blocking decision is logged.

**Acceptance Scenarios**:

1. **Given** an escalated social signal arrives and the LLM classifies it as "misinformation", **When** the Monitoring Agent evaluates it, **Then** no handoff is created, the signal is stored with `misinformation_flagged` status for audit, and the blocking decision is recorded with classification "misinformation".
2. **Given** an escalated social signal arrives and the LLM classifies it as "credible", **When** the Monitoring Agent evaluates it, **Then** the signal proceeds to the standard triage pipeline and may produce a handoff if it meets category and confidence thresholds.
3. **Given** an escalated social signal arrives but the LLM service is unavailable, **When** the Monitoring Agent attempts evaluation, **Then** the signal is held for human review, no automatic handoff is created, and the hold decision is recorded with reason "LLM unavailable".
4. **Given** a non-escalated signal arrives (any `validationStatus` other than "escalated"), **When** the Monitoring Agent processes it, **Then** the Tier 2 LLM misinformation check is not invoked, and the signal proceeds directly to standard triage.

---

### User Story 3 — Signal Summarisation with Content Safety (Priority: P3)

A surge of signals arrives from multiple data sources during an active cyclone event. The Monitoring Agent summarises each incoming signal, extracting the category, source kind, and incident association. Summaries are attached to handoff payloads so that the Risk Assessment Agent receives a concise, structured overview of each signal without needing to re-parse raw payloads. All summarisation respects content safety — no harmful, misleading, or sensitive personal content is propagated in summaries.

**Why this priority**: Signal summarisation powers the handoff payload and enables downstream agents to act on concise, structured information. Content safety ensures that raw social media content (which may contain harmful language or personal information) is not blindly propagated through the agent pipeline.

**Independent Test**: Can be fully tested by sending signals with various categories and source kinds to the summariser and verifying that the returned summary contains the expected structured fields (category, source kind, incident ID) without raw content leakage.

**Acceptance Scenarios**:

1. **Given** a normalised signal with `category=weather`, `source.kind=authoritative`, and `incidentId=INC-001`, **When** the Monitoring Agent summarises it, **Then** the summary contains `category`, `sourceKind`, and `incidentId` as structured fields.
2. **Given** a normalised signal from a social media source with raw payload containing user-generated text, **When** the Monitoring Agent summarises it, **Then** the summary does not include unprocessed raw user content — only the structured classification fields.
3. **Given** multiple signals arrive in rapid succession, **When** each is summarised, **Then** each summary is independent and correctly reflects its own signal's metadata.

---

### User Story 4 — Retrospective Signal-to-Incident Association (Priority: P4)

An incident commander declares a new bushfire incident in a jurisdiction. Several signals had arrived in the preceding hours from sensors and community reports in that jurisdiction, but at the time they had no incident to be associated with. The Monitoring Agent retrospectively scans unassociated signals from the past 24 hours within the same jurisdiction and links them to the newly declared incident. The incident commander can now see the full timeline of early-warning signals that preceded the formal declaration.

**Why this priority**: Retrospective association provides incident commanders with a complete picture of the lead-up to an incident, enabling better situational awareness and post-incident analysis. The Constitution (Principle I) requires the system to support explanations of what data and assumptions inform decisions.

**Independent Test**: Can be fully tested by creating several unassociated signals within a jurisdiction, then invoking the retrospective association function with a new incident ID, and verifying that each previously unassociated signal is now linked to the incident.

**Acceptance Scenarios**:

1. **Given** 5 unassociated signals exist for jurisdiction "NSW-SYDNEY" from the past 12 hours, **When** a new incident "INC-042" is declared in "NSW-SYDNEY" and retrospective association is triggered, **Then** all 5 signals are updated with `incidentId=INC-042` and the count of associated signals is returned.
2. **Given** unassociated signals exist for jurisdiction "NSW-SYDNEY" from 30 hours ago (beyond the 24-hour lookback window), **When** retrospective association is triggered for "NSW-SYDNEY", **Then** those older signals are not associated.
3. **Given** signals already associated with a different incident exist in the jurisdiction, **When** retrospective association runs, **Then** those already-associated signals are not modified.
4. **Given** the signal repository is unavailable, **When** retrospective association is attempted, **Then** the function returns 0 associations and does not raise an unhandled error.

---

### User Story 5 — Graceful Degradation and Data Freshness Tracking (Priority: P5)

During a major disaster event, the Bureau of Meteorology data feed becomes temporarily unavailable. The Monitoring Agent detects that incoming signals from this source have stopped (data freshness degrades). It continues processing signals from other available sources without interruption. When the BoM feed recovers, the agent resumes processing its signals normally. Throughout the outage, the system records the degraded freshness status, and any decisions made during the outage period carry reduced confidence annotations reflecting the missing data source.

**Why this priority**: The Constitution (Non-Functional Requirements) mandates that the system continue operating with reduced functionality when a data source is unavailable. Data freshness tracking is required by Principle III to ensure agents consider freshness in decisions.

**Independent Test**: Can be fully tested by simulating a source going offline (no signals arriving for multiple polling intervals), verifying that freshness scores degrade, the degraded status is recorded, and other signal sources continue processing normally.

**Acceptance Scenarios**:

1. **Given** signals from a data source carry a `freshnessScore` computed by the ingestion pipeline, **When** the Monitoring Agent receives a signal with a low freshness score (e.g., below 0.5), **Then** the agent records the freshness concern in the signal audit trail and factors the reduced freshness into triage decisions (e.g., lowering effective confidence for escalation).
2. **Given** all signals from a specific source have stopped arriving for an extended period, **When** the Monitoring Agent detects the gap, **Then** it logs a data-source degradation warning and continues processing signals from other sources without interruption.
3. **Given** a previously degraded source begins sending signals again with acceptable freshness scores, **When** the Monitoring Agent processes the first recovered signal, **Then** the degraded status is cleared and the recovery is logged.

---

### User Story 6 — Audit Trail of All Agent Decisions (Priority: P6)

An incident post-mortem review requires a complete record of every decision the Monitoring Agent made during a 48-hour bushfire event. The review team can retrieve a chronological log showing every signal received, every summary generated, every misinformation classification, every handoff created or blocked, every retrospective association, and every degradation event. Each entry includes timestamps, inputs, outputs, confidence scores, and the reasoning or rule that drove the decision.

**Why this priority**: The Constitution (Non-Functional Requirements) mandates an append-only audit trail for safety-critical recommendations and actions. Traceability is essential for post-incident learning, regulatory compliance, and maintaining public trust in the system.

**Independent Test**: Can be fully tested by processing a sequence of signals (including escalated, high-risk, low-confidence, and normal signals) and then querying the audit trail to verify that every decision point produced a corresponding audit record.

**Acceptance Scenarios**:

1. **Given** the Monitoring Agent processes any signal, **When** the processing completes, **Then** an audit record is created containing: signal ID, timestamp, decision type (summarised / escalated / blocked / handed-off / held-for-review), inputs used, output produced, and confidence score.
2. **Given** a misinformation detection decision is made, **When** the decision is recorded, **Then** the audit entry includes the LLM classification result (credible / misinformation / llm_unavailable) and the signal content that was evaluated.
3. **Given** a retrospective association is performed, **When** signals are linked to an incident, **Then** an audit entry is created for each association including the signal ID, incident ID, and the lookback window used.
4. **Given** a handoff is created, **When** the handoff event is persisted, **Then** the audit trail links the handoff event ID to the originating signal ID and includes the full handoff payload.

---

### Edge Cases

- What happens when a signal arrives with `confidenceScore` exactly at the threshold boundary (0.8)? The agent treats 0.8 as meeting the threshold (≥ 0.8) and proceeds with triage.
- What happens when a signal has `validationStatus=escalated` but `source.kind` is not social (e.g., a sensor signal was escalated due to anomalous readings)? The Tier 2 LLM evaluation still runs for all escalated signals regardless of source kind, since the escalation flag indicates the ingestion pipeline already detected something suspicious.
- What happens when the LLM returns an unexpected response (neither "credible", "suspicious", nor "misinformation")? The agent holds the signal for human review and does not create an automatic handoff (fail-safe-CLOSED per Constitution Principle I). The unexpected response is logged for investigation. This ensures potentially dangerous signals are not automatically escalated without proper evaluation.
- What happens when multiple signals for the same incident arrive simultaneously? Each signal is processed independently. The agent performs basic idempotency checking per FR-029: if the same `signal_id` is received twice within the configurable deduplication window (default 10 minutes), the duplicate is silently discarded and logged. Full cross-pipeline deduplication remains the responsibility of the ingestion pipeline (spec 006).
- What happens when a retrospective association is triggered but the lookback period overlaps with signals from a simulation tenant? Only signals matching the requesting tenant scope (live vs. simulation) are considered for association, per the tenant isolation spec (007).
- What happens when the Monitoring Agent itself becomes unhealthy? The health check reports an unhealthy status, the hosting platform detects the failure, and a new instance is started. In-flight signals that were not yet processed are re-delivered from the messaging infrastructure.

## Requirements *(mandatory)*

### Functional Requirements

#### Signal Intake and Summarisation

- **FR-001**: The Monitoring Agent MUST receive normalised signals in the SignalEnvelope format from upstream ingestion pipelines as defined in spec 006.
- **FR-002**: The Monitoring Agent MUST summarise each incoming signal, producing a structured summary containing at minimum: `category`, `sourceKind`, and `incidentId`.
- **FR-003**: The Monitoring Agent MUST NOT propagate raw, unprocessed user-generated content (e.g., social media post text) in signal summaries or handoff payloads. Only structured classification fields may be included.
- **FR-029**: The Monitoring Agent MUST perform basic idempotency checking to avoid processing the same `signal_id` twice within a configurable deduplication time window (default: 10 minutes, configurable via environment variable `SIGNAL_DEDUP_WINDOW_MINUTES`). If a duplicate `signal_id` is detected within the window, the signal MUST be silently discarded and the discard recorded in the audit trail. Full cross-pipeline deduplication remains the responsibility of the ingestion pipeline (spec 006).

#### Misinformation Detection

- **FR-004**: The Monitoring Agent MUST perform Tier 2 LLM-based misinformation evaluation on any signal with `validationStatus=escalated`.
- **FR-005**: If the LLM classifies an escalated signal as "misinformation", the Monitoring Agent MUST block the signal from producing a handoff to any downstream agent. The blocked signal MUST still be persisted in the signal store with a `misinformation_flagged` status for audit purposes.
- **FR-006**: If the LLM service is unavailable during misinformation evaluation, the Monitoring Agent MUST hold the signal for human review and MUST NOT create an automatic handoff. The hold decision MUST be recorded with reason "LLM unavailable".
- **FR-007**: The misinformation evaluation prompt MUST instruct the LLM to classify signals as one of: "credible", "suspicious", or "misinformation". If the LLM returns an unexpected response (not one of the three valid classifications), times out, or is unavailable, the signal MUST be held for human review (fail-safe-CLOSED, per Constitution Principle I). A "suspicious" classification MUST apply a configurable confidence penalty (default: 0.15, configurable via environment variable `SUSPICIOUS_CONFIDENCE_PENALTY`) to the signal's effective confidence before triage.
- **FR-008**: The Monitoring Agent MUST record the LLM classification result for every misinformation evaluation in the audit trail.

#### Confidence-Based Triage and Escalation

- **FR-009**: The Monitoring Agent MUST create a handoff to the Risk Assessment Agent when all of the following conditions are met: (a) signal `category` is one of {fire, weather, hydrology, earthquake, tsunami}, (b) `effectiveConfidence` (computed as `confidenceScore × freshnessScore`) is ≥ the configurable escalation threshold (default: 0.8, configurable via environment variable `ESCALATION_CONFIDENCE_THRESHOLD`), and (c) `incidentId` is non-null.
- **FR-010**: Each handoff event MUST include: source agent (`monitoring`), target agent (`risk_assessment`), incident scope key, confidence score, creation timestamp, and a payload containing the signal summary.
- **FR-011**: Handoff events MUST conform to the AgentHandoffEvent contract defined in the common handoffs module (`apps/agents/common/handoffs.py`). Handoff delivery MUST use exponential backoff with a maximum of 3 retries. If all retries are exhausted, the handoff MUST be dead-lettered via the `on_dead_letter` callback. Dead-lettered handoffs MUST be surfaced to incident commanders (e.g., via dashboard alert or notification) so they are not silently lost.
- **FR-012**: If a signal meets category and confidence thresholds but has no associated incident, the Monitoring Agent MUST NOT create a handoff. The signal remains in the signal store for potential retrospective association.

#### Retrospective Incident Association

- **FR-013**: When a new incident is declared, the Monitoring Agent MUST support a retrospective association function that scans unassociated signals from the same jurisdiction using jurisdiction + location matching within a configurable lookback window (default: 24 hours, configurable via environment variable `RETROSPECTIVE_LOOKBACK_HOURS`).
- **FR-014**: Retrospective association MUST only update signals that have a null `incidentId`. Signals already associated with another incident MUST NOT be modified.
- **FR-015**: Retrospective association MUST respect tenant isolation boundaries — signals from simulation tenants MUST NOT be associated with live incidents and vice versa. More broadly, the Monitoring Agent MUST respect simulation tenant boundaries per spec 007: signals from simulation runs MUST NOT cross into production processing at any stage (triage, escalation, or retrospective association).
- **FR-016**: The Monitoring Agent MUST return the count of newly associated signals after each retrospective association operation.

#### Data Freshness and Provenance

- **FR-017**: The Monitoring Agent MUST consider the `freshnessScore` carried by each signal (as computed by the ingestion pipeline per spec 006) when making triage decisions.
- **FR-018**: The Monitoring Agent MUST log a degradation warning when it detects signals arriving with freshness scores below a configurable per-source-type staleness threshold. Default thresholds: authoritative sources (BoM, Geoscience Australia) stale after 15 minutes, IoT sensors stale after 5 minutes, social media sources stale after 30 minutes. Thresholds MUST be configurable per source type.
- **FR-019**: Every signal processed by the Monitoring Agent MUST retain its provenance metadata (source, collection method, time, location precision, and validation status) as received from the ingestion pipeline.

#### Audit Trail

- **FR-020**: The Monitoring Agent MUST produce an audit record for every decision, including: signal receipt, summarisation, misinformation evaluation, handoff creation, handoff blocking, signal hold for human review, retrospective association, degradation detection, and duplicate signal discard (idempotency).
- **FR-021**: Each audit record MUST include: signal ID (`signal_id`), decision type (`decision`), confidence score (`confidence`), timestamp, agent version (`agent_version`), reasoning summary (`reasoning_summary`), inputs used, and output produced. Audit records MUST be stored as append-only events in Azure Cosmos DB.
- **FR-022**: The audit trail MUST be append-only in Azure Cosmos DB. Existing records MUST NOT be modified or deleted. The Cosmos DB container MUST be configured with no TTL (infinite retention) and partition key aligned with incident scope for efficient querying.

#### Graceful Degradation

- **FR-023**: The Monitoring Agent MUST continue processing signals from available sources when one or more data sources become unavailable. The agent MUST NOT halt entirely when a source fails. When a source is unavailable, the agent MUST reduce overall triage confidence proportionally to reflect the missing data source and MUST log degradation events with the affected source, timestamp, and impact on confidence.
- **FR-024**: When the LLM service (Azure OpenAI) is unavailable, the Monitoring Agent MUST degrade gracefully: non-escalated signals MUST fall back to rule-based triage (threshold-only evaluation using `confidenceScore` and `category`, with no LLM summarisation) and MUST carry a reduced confidence annotation reflecting the absence of LLM enrichment. Escalated signals MUST be held for human review per FR-006.
- **FR-025**: The Monitoring Agent MUST expose a `/health` endpoint that reports agent readiness for Azure Container Apps health probes. The health response MUST include: (a) LLM connectivity status (can reach Azure OpenAI), (b) data source freshness status (per-source healthy/degraded/offline from DataFreshnessIndicator), and (c) processing queue depth (number of signals awaiting processing). The endpoint MUST respond within 1 second under normal operation per SC-007.

#### Content Safety

- **FR-026**: The Monitoring Agent MUST NOT include harmful, misleading, or personally identifiable content in summaries, handoff payloads, or any output propagated to downstream agents.
- **FR-027**: All LLM interactions MUST use system prompts that scope the LLM's role to disaster response credibility assessment and MUST NOT allow the LLM to be repurposed via prompt injection from signal content.
- **FR-028**: All LLM-based evaluations (misinformation detection and signal summarisation) MUST use Azure OpenAI with content safety filters enabled. The content safety filters MUST be configured to detect and block harmful content in both prompts and completions. Additionally, all LLM outputs MUST pass through the `ContentSafetyValidator` (`apps/agents/common/content_safety.py`) before being included in handoff payloads. This includes keyword filtering (blocked terms), language validation (expected locale matching), and length checks (max output length). If content safety validation fails, the output MUST be replaced with a structured fallback and the failure recorded in the audit trail.

### Non-Functional Requirements

#### Scalability

- **NFR-001**: The Monitoring Agent MUST handle a minimum sustained throughput of 1,000 signals per minute during peak disaster events, consistent with the constitution's "1,000+ lives saved annually" target requiring rapid signal processing.
- **NFR-002**: The Monitoring Agent MUST be deployed on Azure Container Apps with auto-scaling enabled. Scaling rules MUST be based on processing queue depth (signals awaiting processing) to handle traffic spikes during multi-hazard events.

#### Observability

- **NFR-003**: The Monitoring Agent MUST emit structured telemetry to Azure Monitor / Application Insights, including distributed tracing for end-to-end signal processing flows. Key metrics that MUST be emitted: `signal_processing_latency` (time from signal receipt to decision), `escalation_rate` (handoffs created per time window), `misinformation_detection_rate` (misinformation classifications per time window), `degradation_events` (count of source freshness degradation events), and `handoff_success_rate` (delivered vs. failed/dead-lettered handoffs). All metrics MUST support the constitution's audit requirements and WAF Operational Excellence pillar.

#### Multi-Region Deployment

- **NFR-004**: Per the constitution, Azure deployment MUST be within Australia. The Monitoring Agent MUST be deployable to both `australiaeast` (primary) and `australiasoutheast` (DR) regions. Each regional deployment MUST operate independently with no cross-region data leakage — signals processed in one region MUST NOT be visible to or affect the other region's processing. Regional failover configuration is managed at the Azure Container Apps and Cosmos DB level.

### Key Entities

- **SignalEnvelope**: The normalised signal format received from ingestion pipelines. Key attributes: source (data source ID, name, kind), optional incident ID, category, occurred-at timestamp, received-at timestamp, optional jurisdiction ID, location (GeoJSON), payload, confidence score (0–1), freshness score (0–1), validation status, and provenance metadata. Defined in spec 006; consumed (not created) by the Monitoring Agent.

- **AgentHandoffEvent**: An explicit handoff record created when the Monitoring Agent escalates a signal to the Risk Assessment Agent. Key attributes: handoff ID, incident ID, source agent, target agent, scope key, confidence, payload (containing the signal summary), tenant ID, status (pending → delivered/failed/dead-lettered), retry count, and timestamps. Created by the Monitoring Agent; consumed by the Risk Assessment Agent.

- **MonitoringDecisionRecord**: An audit trail entry capturing a single decision made by the Monitoring Agent, stored as an append-only event in Azure Cosmos DB. Key attributes: record ID, signal ID (`signal_id`), decision type (`decision`: summarised / escalated / blocked / handed-off / held-for-review / associated / degradation-detected / discarded), inputs, output, confidence at decision time (`confidence`), LLM classification result (when applicable), agent version (`agent_version`), reasoning summary (`reasoning_summary`), and timestamp. Append-only; no updates or deletes permitted.

- **DataFreshnessIndicator**: A per-source freshness status tracking whether signals from a given data source are arriving within expected intervals. Key attributes: data source ID, source type (authoritative / iot / social), last signal received timestamp, current freshness score, staleness threshold (authoritative: 15 min, IoT: 5 min, social: 30 min — configurable per source type), status (healthy / degraded / offline), and last status change timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: High-risk signals (fire, weather, hydrology, earthquake, tsunami with confidence ≥ 0.8 and an associated incident) produce a handoff to Risk Assessment within 5 seconds of receipt by the Monitoring Agent.
- **SC-002**: 100% of escalated social signals undergo misinformation evaluation before any handoff is created — no escalated signal bypasses the credibility check.
- **SC-003**: When the LLM service is unavailable, 100% of escalated signals are held for human review rather than being silently dropped or automatically escalated.
- **SC-004**: Retrospective association links at least 90% of eligible unassociated signals to a newly declared incident within 30 seconds of the association being triggered.
- **SC-005**: The Monitoring Agent continues processing non-affected signals within 10 seconds of detecting a data source outage, with no interruption to other source pipelines.
- **SC-006**: Every decision made by the Monitoring Agent has a corresponding audit record — audit completeness is 100% verifiable via reconciliation of signal IDs processed vs. audit records created.
- **SC-007**: The health endpoint responds within 1 second under normal operation, enabling container orchestration to detect failures and restart the agent within the platform's configured health check interval.
- **SC-008**: Misinformation detection correctly blocks confirmed misinformation signals while allowing credible community intelligence through — measured by a false-positive rate of less than 5% on a representative test set of labelled disaster-related social media posts.

## Assumptions

- The ingestion pipelines (spec 006) deliver normalised signals in the SignalEnvelope format with all required fields populated, including `confidenceScore`, `freshnessScore`, `validationStatus`, and `provenance`. The Monitoring Agent does not re-normalise or re-validate signals at intake.
- The confidence threshold for high-risk escalation defaults to 0.8 and is configurable via environment variable (`ESCALATION_CONFIDENCE_THRESHOLD`). Per-source-type freshness staleness thresholds are also configurable: authoritative sources (BoM, GA) stale after 15 minutes, IoT sensors after 5 minutes, social media after 30 minutes. These may be tuned per jurisdiction or disaster type in future iterations.
- The 24-hour default lookback window for retrospective association is sufficient for most incident types. Longer lookback periods may be needed for slow-onset events (e.g., drought) and can be configured per invocation.
- Full cross-pipeline signal deduplication is handled by the ingestion pipeline (spec 006), not by the Monitoring Agent. However, the Monitoring Agent performs basic idempotency checking on `signal_id` within a configurable time window (default 10 minutes) to avoid reprocessing the same signal due to delivery retries or infrastructure-level at-least-once semantics (FR-029).
- The LLM client uses Azure OpenAI with content safety filters enabled. It supports system prompts and user prompts with configurable max output tokens and timeout. The Monitoring Agent's misinformation prompt expects a single-word response for classification efficiency.
- Tenant isolation (simulation vs. live) is enforced at the data layer per spec 007. The Monitoring Agent respects tenant boundaries at all processing stages — triage, escalation, and retrospective association. Signals from simulation runs MUST NOT cross into production processing.
- The Risk Assessment Agent is the sole downstream recipient of monitoring handoffs. Future agent additions (e.g., a dedicated social intelligence agent) would require specification updates.
- The `/health` endpoint checks LLM connectivity (Azure OpenAI reachability), data source freshness status (per-source healthy/degraded/offline), and processing queue depth. It is designed to respond within 1 second to support Azure Container Apps health probes, but its readiness determination depends on connectivity to external services.

## Dependencies

- **spec 001 (Disaster Response Hub)**: Defines the Signal, AgentHandoffEvent, and TimelineEvent data models that the Monitoring Agent operates on.
- **spec 005 (Data Source Governance)**: Defines the data source registry, trust tiers, and governance assignments that inform how the Monitoring Agent treats signals from different sources.
- **spec 006 (Data Ingestion & Storage)**: Defines the ingestion pipelines that produce normalised SignalEnvelope records consumed by the Monitoring Agent. Also defines signal storage, partitioning, and provenance enrichment.
- **spec 007 (Simulation & Tenant Isolation)**: Defines the tenant isolation model that the Monitoring Agent must respect during retrospective association and signal processing.

## Clarifications

### Session 2026-04-11

- Q: What is the correct confidence threshold for escalation and should it be configurable? → A: 0.8 default, configurable via environment variable `ESCALATION_CONFIDENCE_THRESHOLD`.
- Q: Which signal categories should be eligible for escalation to risk assessment? → A: Fire, weather, hydrology, earthquake, and tsunami (earthquake/tsunami from Geoscience Australia per constitution).
- Q: How should social media signals flagged as misinformation be handled post-blocking? → A: Blocked from escalation but stored with `misinformation_flagged` status for audit. LLM-based detection uses Azure OpenAI with content safety filters.
- Q: What are the data freshness staleness thresholds per source type? → A: Authoritative sources (BoM, GA) stale after 15 min, IoT sensors after 5 min, social media after 30 min. Configurable per source type.
- Q: What is the expected behavior when a data source fails? → A: Continue with remaining sources, reduce overall confidence proportionally, log degradation events. MUST NOT halt entirely.
- Q: What is the audit trail storage format and required fields? → A: Append-only events in Cosmos DB with signal_id, decision, confidence, timestamp, agent_version, and reasoning_summary.
- Q: How should retrospective signal-to-incident association match signals? → A: Jurisdiction + location matching. Lookback window configurable, default 24 hours.
- Q: How is tenant isolation enforced for simulation runs? → A: Monitoring Agent must respect simulation tenant boundaries per spec 007. Signals from simulation runs must not cross into production processing at any stage.

### Session 2026-04-11 (Round 2)

- Q: What are the scalability targets for signal throughput? → A: Minimum 1,000 signals/minute during peak disaster events. Azure Container Apps auto-scaling based on queue depth.
- Q: What observability signals should the agent emit? → A: Azure Monitor / Application Insights for metrics and distributed tracing. Key metrics: signal_processing_latency, escalation_rate, misinformation_detection_rate, degradation_events, handoff_success_rate.
- Q: How should non-escalated signals be handled when the LLM is unavailable? → A: Fall back to rule-based triage (threshold-only, no summarisation) with reduced confidence annotation. Consistent with constitution's graceful degradation mandate.
- Q: What is the specific handoff retry policy? → A: Exponential backoff, max 3 retries, then dead-letter per `apps/agents/common/handoffs.py`. Dead-lettered handoffs surfaced to incident commanders.
- Q: How are LLM outputs validated before inclusion in handoff payloads? → A: All LLM outputs pass through ContentSafetyValidator (`apps/agents/common/content_safety.py`) — keyword filtering, language validation, and length checks. Failures produce structured fallback.
- Q: Should the Monitoring Agent perform any signal deduplication? → A: Basic idempotency checking on signal_id within a configurable time window (default 10 min). Full deduplication remains out of scope (ingestion pipeline responsibility).
- Q: What should the /health endpoint report? → A: LLM connectivity status, data source freshness status (per-source), and processing queue depth. Supports Container Apps health probes.
- Q: What are the multi-region deployment requirements? → A: Deployable to australiaeast (primary) and australiasoutheast (DR). No cross-region data leakage. All Azure deployment within Australia per constitution.


## Personas

Authored against the `specs/027-spec-hardening/contracts/persona-profile.md` schema. AU-v1 personas are validated; PH / JP / BD entries are explicit placeholders pending capstone-reinterpretation (D-009) and SME validation per FR-023.

- **PER-022**: cross-ref to `specs/001-disaster-response-hub/spec.md` AIIMS personas (Incident Commander / Planning Officer / Operations Officer / Logistics Officer / Public Information Officer) per `specs/027-spec-hardening/contracts/persona-profile.md`. `status:` validated. `preconditions:` none.
- **PER-023**: cross-ref to `specs/004-actor-github-agents/spec.md` actor catalogue covering all `.github/agents/technical/*.agent.md` actors. `status:` validated. `preconditions:` none.
- **PER-024** [non-AU placeholder]: capstone-country operator personas for PH (NDRRMC), JP (Cabinet Office DRR / FDMA), BD (DDM / CPP volunteers). `status:` placeholder. `preconditions:` capstone-reinterpretation decision per D-009; SME validation via `ama-rubric-grader`-vetted SME interviews.

## Hypotheses

Hypotheses use the FR-018 statement format (`If <condition> then <observable>`) and link to a structured evidence stub conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. Capstone-country hypotheses for this spec's agent ownership (where applicable) are allocated in feature 028 / US2.

- **HYP-008**: If the actors named in `specs/004-actor-github-agents/spec.md` consult on every change to this spec via the `agent` tool, then the AMA rubric criterion mean (Assumptions / Requirements / Personas / Hypotheses / Scope) for this spec rises by at least +1 band relative to the baseline captured in `specs/028-capstone-alignment/evidence/rubric-baseline.md`. **Falsification**: post-feature rubric snapshot shows a regression in any of those five criteria for this spec. **Evidence stub**: `specs/028-capstone-alignment/evidence/HYP-HYP-008.md` (created in feature 028 polish).

## Out of Scope

Items explicitly deferred from this spec; promotion to in-scope requires the named preconditions to clear. Cross-references to other specs use the canonical overlap phrasing (`authoritative for: <capability>` / `defers-to: <NNN> (<capability>)`).

- **SCP-025** [DEFERRED]: Capstone-country variants (PH typhoon, JP earthquake, BD flood) of this spec's capabilities are out of scope until: (i) capstone-reinterpretation decision per D-009; (ii) per-country regulatory + data-sharing preconditions documented in `specs/005-data-source-governance/spec.md` clear; (iii) responsible technical agents (planning-officer, risk-manager, ai-ml-engineer) sign off on country-specific calibration.
- **SCP-026**: Constitutional-level changes (NON-NEGOTIABLE #1..#5) are not modified by this spec; any tension is documented as `[RISK]` in Assumptions, never resolved here.
- **SCP-027**: Cross-spec authority disputes are arbitrated via `product-owner-ba` and the speckit governance flow; this spec does not unilaterally claim ownership of capabilities owned elsewhere. `defers-to:` 018 (recovery-phase indicators, triggers, phase-exit criteria); 008 (warning-tier authoring, multilingual delivery, misinformation defence) where applicable.


## Capstone-Country Hypotheses (Feature 028 / US2)

> Three deferred capstone-country hypotheses for hazard-feed monitoring + signal triage. Each cites an evidence stub at `specs/010-monitoring-agent/evidence/HYP-<id>.md` conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. `Status = Not tested` until D-009 capstone-reinterpretation clears and per-cohort preconditions are met.

- **HYP-033** [PH deferred]: We believe PAGASA typhoon + flood feed ingestion with CAP / JSON validation and freshness SLO <= 15 min will produce >= 99% feed availability during typhoon-season exercise windows; signal-to-alert end-to-end p95 <= 5 min for the Philippines operator persona; we will know we are wrong if feed availability < 95% or signal-to-alert p95 > 10 min during PH typhoon season Jun-Nov is observed in the measurement window (PH typhoon season Jun-Nov).
  - **Falsification**: feed availability < 95% or signal-to-alert p95 > 10 min during PH typhoon season Jun-Nov.
  - **Evidence stub**: `specs/010-monitoring-agent/evidence/HYP-033.md` (created by feature 028 / US2 / T034..T038).
- **HYP-034** [JP deferred]: We believe JMA seismic + tsunami feed ingestion with sub-second event detection latency SLO will produce >= 99.9% feed availability continuous; seismic-event-to-alert p95 <= 30s for the Japan operator persona; we will know we are wrong if seismic-event-to-alert p95 > 60s during quarterly review is observed in the measurement window (JP continuous; quarterly review).
  - **Falsification**: seismic-event-to-alert p95 > 60s during quarterly review.
  - **Evidence stub**: `specs/010-monitoring-agent/evidence/HYP-034.md` (created by feature 028 / US2 / T034..T038).
- **HYP-035** [BD deferred]: We believe BWDB / FFWC hydro-station feed ingestion with freshness SLO <= 30 min during monsoon will produce >= 99% feed availability during monsoon exercise windows; signal-to-alert p95 <= 10 min for the Bangladesh operator persona; we will know we are wrong if feed availability < 95% during BD monsoon Apr-Sep is observed in the measurement window (BD monsoon Apr-Sep).
  - **Falsification**: feed availability < 95% during BD monsoon Apr-Sep.
  - **Evidence stub**: `specs/010-monitoring-agent/evidence/HYP-035.md` (created by feature 028 / US2 / T034..T038).

