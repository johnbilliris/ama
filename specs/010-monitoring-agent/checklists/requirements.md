# Requirements Quality Checklist: Monitoring Agent

**Purpose**: Validate that the Monitoring Agent specification's requirements are complete, clear, consistent, measurable, and ready for implementation — "unit tests for requirements written in English"  
**Created**: 2026-07-12  
**Feature**: [spec.md](../spec.md)  
**Focus Areas**: Life safety mandate, Azure-only Australian deployment, graceful degradation, audit trail, content safety, tenant isolation, scalability (1000 signals/min)  
**Depth**: Comprehensive  
**Audience**: Architecture reviewer / PR review gate  

---

## Requirement Completeness

- [ ] CHK001 — Are requirements defined for what happens when a SignalEnvelope arrives with missing or null required fields (e.g., `category`, `confidenceScore`, `freshnessScore`)? FR-001 assumes all required fields are populated per the ingestion pipeline, but no validation or rejection behaviour is specified at the Monitoring Agent boundary. [Gap, Spec §FR-001, Assumptions]
- [ ] CHK002 — Are requirements specified for signal processing order or prioritisation during peak load? The spec mandates 1,000 signals/min throughput but does not state whether life-safety categories (fire, earthquake, tsunami) should be prioritised over lower-risk categories in the processing queue. [Gap, Spec §NFR-001]
- [ ] CHK003 — Are requirements defined for maximum LLM call concurrency or rate-limiting when multiple escalated signals arrive simultaneously? The spec defines retry/backoff for handoff delivery (FR-011) but not for LLM invocation itself. [Gap, Spec §FR-004]
- [ ] CHK004 — Are requirements specified for the dead-letter surfacing mechanism? FR-011 states dead-lettered handoffs "MUST be surfaced to incident commanders (e.g., via dashboard alert or notification)" but does not define the notification channel, latency expectation, or acknowledgement workflow. [Completeness, Spec §FR-011]
- [ ] CHK005 — Are requirements defined for the structured fallback content when ContentSafetyValidator rejects an LLM output? FR-028 states "replaced with a structured fallback" but does not specify the fallback's schema, content, or how downstream agents should interpret it. [Gap, Spec §FR-028]
- [ ] CHK006 — Are requirements specified for what constitutes "harmful, misleading, or personally identifiable content" in the context of disaster response signals? FR-026 uses these terms without defining classification criteria or referencing a PII taxonomy. [Gap, Spec §FR-026]
- [ ] CHK007 — Are requirements defined for Cosmos DB partition key strategy beyond "aligned with incident scope"? FR-022 mentions partition key alignment but does not specify the key path, hot-partition mitigation, or cross-partition query patterns needed for audit trail retrieval. [Gap, Spec §FR-022]
- [ ] CHK008 — Are requirements specified for audit trail data growth management given infinite retention (no TTL)? The spec mandates append-only with no TTL but defines no archival, tiering, or cost-management strategy for long-running deployments. [Gap, Spec §FR-022]
- [ ] CHK009 — Are requirements defined for concurrent retrospective association requests? If two incidents are declared simultaneously in overlapping jurisdictions, the spec does not address race conditions or conflict resolution for unassociated signals that could match both. [Gap, Spec §FR-013]
- [ ] CHK010 — Are requirements specified for the "processing queue depth" metric referenced in FR-025 and NFR-002? No threshold values are defined for what queue depth triggers auto-scaling or what depth constitutes an unhealthy state. [Gap, Spec §FR-025, NFR-002]
- [ ] CHK011 — Are requirements defined for how the Monitoring Agent discovers or is notified of newly declared incidents to trigger retrospective association? FR-013 says "when a new incident is declared" but does not specify the trigger mechanism (event subscription, polling, API call). [Gap, Spec §FR-013]
- [ ] CHK012 — Are requirements specified for LLM prompt versioning or change management? The spec references system prompts for misinformation classification (FR-007, FR-027) but does not address how prompt changes are tracked, tested, or rolled back. [Gap, Spec §FR-007, FR-027]
- [ ] CHK013 — Are requirements defined for the maximum acceptable latency of misinformation evaluation? SC-001 defines a 5-second SLA for high-risk escalation, but no latency target exists for the LLM-based misinformation check that must complete before escalation can proceed. [Gap, Spec §SC-001, FR-004]
- [ ] CHK014 — Are requirements specified for handling signals that arrive during the agent's startup or restart window? The edge case section mentions re-delivery from messaging infrastructure, but no requirement addresses partial processing or exactly-once semantics during restarts. [Gap, Edge Cases]
- [ ] CHK015 — Are requirements defined for the `agent_version` field in audit records (FR-021)? No versioning scheme, format, or update cadence is specified. [Gap, Spec §FR-021]

---

## Requirement Clarity

- [ ] CHK016 — Is "reduce overall triage confidence proportionally" (FR-023) quantified with a specific formula or algorithm? The term "proportionally" is ambiguous — it could mean linear reduction, weighted by source trust tier, or percentage-based. [Ambiguity, Spec §FR-023]
- [ ] CHK017 — Is the "reduced confidence annotation" for rule-based fallback (FR-024) defined with a specific reduction factor or range? The spec states confidence should be reduced but not by how much. [Ambiguity, Spec §FR-024]
- [ ] CHK018 — Is "jurisdiction + location matching" for retrospective association (FR-013) defined with specific precision criteria? Does matching require exact jurisdiction ID equality, GeoJSON polygon containment, or proximity radius? [Ambiguity, Spec §FR-013]
- [ ] CHK019 — Is the LLM timeout behaviour specified when the LLM responds but exceeds a reasonable response time? FR-006 covers total unavailability, but slow responses (e.g., 30+ seconds) are not addressed — does a timeout count as "unavailable"? [Ambiguity, Spec §FR-006]
- [ ] CHK020 — Is "expected locale matching" in ContentSafetyValidator (FR-028) defined with specific locale codes or language detection criteria? The expected locale for Australian disaster response is presumably English, but this is not stated. [Ambiguity, Spec §FR-028]
- [ ] CHK021 — Is the distinction between "degraded" and "offline" status for DataFreshnessIndicator explicitly defined? The entity description lists both statuses but does not specify the transition criteria from healthy → degraded → offline. [Ambiguity, Key Entities §DataFreshnessIndicator]
- [ ] CHK022 — Is "promptly" or the timing expectation for clearing degraded status defined? FR-023/User Story 5 states the degraded status is cleared when signals resume, but no maximum detection latency is specified for the recovery transition. [Ambiguity, Spec §US-5]
- [ ] CHK023 — Are the "configurable per source type" staleness thresholds (FR-018) defined with a configuration mechanism? The spec lists default values and says "configurable" but does not specify whether this is via environment variables (like other thresholds), config file, or runtime API. [Ambiguity, Spec §FR-018]
- [ ] CHK024 — Is "basic idempotency checking" (FR-029) defined with the specific deduplication mechanism? Does it use in-memory cache, distributed cache, or database lookup? This affects behaviour under multi-instance scaling. [Ambiguity, Spec §FR-029]
- [ ] CHK025 — Is the "reasoning_summary" field in audit records (FR-021) defined with expected content, format, or maximum length? Without constraints, this field could contain anything from a single word to unbounded text. [Ambiguity, Spec §FR-021]

---

## Requirement Consistency

- [ ] CHK026 — Are the freshness threshold values consistent between the spec sections? FR-018 defines per-source defaults (authoritative: 15 min, IoT: 5 min, social: 30 min) while the Assumptions section also states these same values — are these guaranteed to stay synchronised, and is there a single source of truth? [Consistency, Spec §FR-018, Assumptions]
- [ ] CHK027 — Is the "suspicious" LLM classification (FR-007) consistently handled? FR-007 defines three possible classifications (credible/suspicious/misinformation) but the fail-safe-open rule treats only "misinformation" as blocking — the spec does not specify any differential treatment for "suspicious" vs. "credible" signals (e.g., reduced confidence, flagging). [Consistency, Spec §FR-007, FR-005]
- [ ] CHK028 — Are the escalation-eligible categories consistent between User Story 1 and FR-009? Both list {fire, weather, hydrology, earthquake, tsunami} — but no single authoritative enum or reference table is defined, risking future divergence. [Consistency, Spec §US-1, FR-009]
- [ ] CHK029 — Is the health endpoint response time requirement (1 second, FR-025) consistent with SC-007 which states the same? Are these intentionally duplicated, or should one reference the other to avoid maintenance drift? [Consistency, Spec §FR-025, SC-007]
- [ ] CHK030 — Does the 5-second escalation SLA (SC-001) account for the LLM-based misinformation check time? If an escalated signal must undergo Tier 2 LLM evaluation before handoff, the 5-second window may conflict with typical LLM latency, but no exception or adjusted SLA is defined for escalated signals. [Conflict, Spec §SC-001, FR-004]
- [ ] CHK031 — Is the fail-safe-open behaviour for unexpected LLM responses (Edge Cases) consistent with the content safety mandate (FR-026, FR-028)? Allowing signals through on unexpected LLM output could conflict with the requirement to block harmful content. [Conflict, Edge Cases, FR-026]
- [ ] CHK032 — Are the audit trail decision types consistent across FR-020, FR-021, and the MonitoringDecisionRecord entity? FR-020 lists nine decision types while the entity lists eight — is "discarded" (from FR-029 idempotency) consistently included in all references? [Consistency, Spec §FR-020, Key Entities]

---

## Acceptance Criteria Quality

- [ ] CHK033 — Is the SC-008 false-positive rate target (< 5%) defined with a specific test set size, composition, and labelling methodology? "A representative test set of labelled disaster-related social media posts" is not quantified. [Measurability, Spec §SC-008]
- [ ] CHK034 — Is SC-004's "at least 90% of eligible unassociated signals" threshold justified? No rationale is provided for why 90% rather than 100%, and the 10% margin does not specify what happens to unlinked signals. [Measurability, Spec §SC-004]
- [ ] CHK035 — Is SC-005's "within 10 seconds of detecting a data source outage" measurable given that detection itself has no defined latency? The 10-second clock starts at "detecting" but detection timing is unspecified. [Measurability, Spec §SC-005]
- [ ] CHK036 — Can SC-006's "100% audit completeness" be verified independently? The reconciliation approach (signal IDs processed vs. audit records created) assumes both sets are independently queryable, but no requirement specifies a reconciliation endpoint or process. [Measurability, Spec §SC-006]
- [ ] CHK037 — Is the 5-second handoff SLA (SC-001) defined with measurement boundaries? Does the clock start at message receipt from the queue, deserialization, or the first byte on the wire? Does it end at handoff event creation or successful delivery acknowledgement? [Measurability, Spec §SC-001]

---

## Scenario Coverage

- [ ] CHK038 — Are requirements defined for a signal that meets all escalation criteria but whose handoff target (Risk Assessment Agent) is unavailable or unhealthy? The spec covers dead-lettering after retries but not proactive circuit-breaking or queue-overflow scenarios. [Coverage, Spec §FR-011]
- [ ] CHK039 — Are requirements defined for batch/bulk retrospective association when a large incident encompasses thousands of unassociated signals? SC-004 sets a 30-second SLA for "eligible" signals but does not define performance expectations at scale. [Coverage, Spec §SC-004, FR-013]
- [ ] CHK040 — Are requirements defined for what happens when the Cosmos DB audit store itself becomes unavailable? FR-020-022 mandate audit recording for every decision, but no degradation path is specified if the audit store is down. [Coverage, Gap]
- [ ] CHK041 — Are requirements specified for the transition from manual human review back to automated processing for held signals (FR-006)? The spec defines that signals are held but not how they are released, re-evaluated, or eventually resolved. [Coverage, Spec §FR-006]
- [ ] CHK042 — Are requirements defined for the interaction between misinformation detection and retrospective association? If a signal is blocked as misinformation, can it be retrospectively associated to an incident? Should it be excluded from association scans? [Coverage, Spec §FR-005, FR-013]
- [ ] CHK043 — Are requirements defined for multi-hazard scenarios where a single signal is relevant to multiple categories (e.g., a weather event that triggers both flood and fire risk)? FR-009 checks `category` against a set but assumes a single category per signal. [Coverage, Gap]
- [ ] CHK044 — Are requirements defined for configuration change propagation? Multiple thresholds (escalation confidence, dedup window, lookback hours, staleness thresholds) are configurable via environment variables — are changes applied at startup only, or can they be hot-reloaded without restart? [Coverage, Gap]

---

## Edge Case Coverage

- [ ] CHK045 — Are requirements defined for a signal with `confidenceScore` of exactly 0.0 or 1.0? The threshold behaviour at 0.8 is documented, but boundary behaviour at the extreme ends of the 0–1 range is implicit. [Edge Case, Spec §FR-009]
- [ ] CHK046 — Are requirements defined for the deduplication window boundary (FR-029)? If a duplicate signal arrives at exactly the window expiry time (e.g., 10 minutes + 0 seconds), is it treated as duplicate or new? [Edge Case, Spec §FR-029]
- [ ] CHK047 — Are requirements specified for a signal where `validationStatus=escalated` AND the signal also meets high-risk triage criteria? The interaction between Tier 2 LLM evaluation and standard triage flow is described (LLM must pass first) but not as an explicit requirement with acceptance criteria. [Edge Case, Spec §FR-004, FR-009]
- [ ] CHK048 — Are requirements defined for retrospective association when the lookback window crosses a deployment region boundary? NFR-004 mandates no cross-region data leakage, and FR-013 uses a time-based lookback — but cross-region signal visibility during failover is not addressed. [Edge Case, Spec §NFR-004, FR-013]
- [ ] CHK049 — Are requirements defined for handling a signal whose `incidentId` references an incident that has been closed or resolved? The spec checks for non-null `incidentId` (FR-009) but does not specify validation against incident status. [Edge Case, Spec §FR-009]
- [ ] CHK050 — Are requirements defined for what happens when ContentSafetyValidator blocks the LLM prompt itself (not just the response)? FR-028 specifies output validation but does not address the scenario where the signal content being sent to the LLM triggers content safety rejection of the input. [Edge Case, Spec §FR-028]

---

## Non-Functional Requirements Coverage

- [ ] CHK051 — Are latency requirements defined for all processing paths, not just the high-risk escalation path? SC-001 specifies 5 seconds for escalation, but no SLA exists for non-escalated signal processing, misinformation evaluation, or summarisation. [Gap, Spec §SC-001]
- [ ] CHK052 — Are resource consumption requirements or constraints specified? The spec defines throughput (1,000 signals/min) and scaling (auto-scale on queue depth) but not memory, CPU, or cost ceilings per instance. [Gap, Spec §NFR-001, NFR-002]
- [ ] CHK053 — Are security requirements defined beyond content safety? The spec addresses content safety (FR-026-028) but does not specify authentication/authorisation for the agent's own endpoints (e.g., `/health`, retrospective association API), network security (private endpoints, VNet integration), or secrets management. [Gap]
- [ ] CHK054 — Are data residency requirements explicitly stated beyond "Azure deployment within Australia"? NFR-004 mandates Australian regions but does not address whether all data (including LLM prompts sent to Azure OpenAI) must remain within Australian data centres, or whether Azure OpenAI regional availability supports this. [Gap, Spec §NFR-004]
- [ ] CHK055 — Are disaster recovery requirements defined beyond multi-region deployability? NFR-004 mentions DR region but does not specify RPO, RTO, failover trigger criteria, or data synchronisation between regions. [Gap, Spec §NFR-004]
- [ ] CHK056 — Are availability requirements (uptime SLA) specified for the Monitoring Agent? The constitution's "life safety first" mandate implies high availability, but no specific target (e.g., 99.9%, 99.99%) is stated. [Gap]
- [ ] CHK057 — Are requirements specified for backward compatibility when the SignalEnvelope schema (spec 006) evolves? The agent assumes a fixed format but no schema versioning or compatibility strategy is defined. [Gap, Spec §FR-001, Dependencies]
- [ ] CHK058 — Are logging and telemetry requirements defined with specific retention periods? NFR-003 mandates Azure Monitor / Application Insights emission but does not specify log retention, sampling rates, or cost controls for telemetry. [Gap, Spec §NFR-003]

---

## Dependencies & Assumptions

- [ ] CHK059 — Is the assumption that "all required fields are populated" by the ingestion pipeline (Assumptions) validated against spec 006's actual guarantees? If spec 006 allows optional fields, the Monitoring Agent has no defined rejection or default-value behaviour. [Assumption, Spec §Assumptions, Dependencies]
- [ ] CHK060 — Is the assumption that Azure OpenAI is available in Australian regions validated? NFR-004 mandates Australian deployment, and the spec requires Azure OpenAI — but Azure OpenAI regional availability in `australiaeast` and `australiasoutheast` should be confirmed. [Assumption, Spec §NFR-004, FR-028]
- [ ] CHK061 — Is the dependency on `apps/agents/common/handoffs.py` (FR-011) and `apps/agents/common/content_safety.py` (FR-028) documented with version or interface expectations? The spec references specific file paths but not their API contracts. [Dependency, Spec §FR-011, FR-028]
- [ ] CHK062 — Is the assumption that the Risk Assessment Agent is "the sole downstream recipient" (Assumptions) reflected as a constraint in the handoff requirements? FR-010 hardcodes `target agent = risk_assessment`, but no requirement addresses extensibility or the need for spec updates when adding recipients. [Assumption, Spec §Assumptions, FR-010]
- [ ] CHK063 — Are the dependencies on spec 005 (Data Source Governance) reflected in specific Monitoring Agent requirements? The dependency is listed but no FR/NFR explicitly references trust tiers or governance assignments from spec 005 in decision logic. [Dependency, Spec §Dependencies]
- [ ] CHK064 — Is the dependency on spec 007 (Simulation & Tenant Isolation) specified with enough detail for the Monitoring Agent? FR-015 mandates tenant boundary respect but delegates enforcement to "the data layer" — are requirements missing for agent-level tenant validation? [Dependency, Spec §FR-015, Dependencies]

---

## Ambiguities & Potential Conflicts

- [ ] CHK065 — Does the spec define what "human review" entails operationally? FR-006 holds signals for human review when LLM is unavailable, but no requirements define the review interface, reviewer role, SLA for review completion, or escalation if review is not completed. [Ambiguity, Spec §FR-006]
- [ ] CHK066 — Is there a conflict between the fail-safe-open misinformation policy (FR-007, Edge Cases) and the life-safety-first constitution mandate? Allowing potentially suspicious signals through on unexpected LLM responses prioritises information flow over safety, but the constitution may require the opposite for certain categories. [Conflict, Spec §FR-007, Constitution Principle I]
- [ ] CHK067 — Is there an ambiguity in whether "content safety filters enabled" (FR-028) refers to Azure OpenAI's built-in content filtering, the ContentSafetyValidator, or both? The requirement mentions both but their relationship (sequential, redundant, complementary) is not explicitly stated. [Ambiguity, Spec §FR-028]
- [ ] CHK068 — Is there a gap in how the 5-second escalation SLA (SC-001) interacts with handoff retry behaviour (FR-011)? If the first handoff delivery attempt fails, does the SLA clock reset for retries, or must all retries complete within 5 seconds? [Ambiguity, Spec §SC-001, FR-011]
- [ ] CHK069 — Is the term "incident scope key" (FR-010) defined? It appears in the handoff event payload requirement but is not included in the Key Entities definitions or cross-referenced to another spec. [Ambiguity, Spec §FR-010]
- [ ] CHK070 — Is there an ambiguity in the freshness score's effect on escalation decisions? FR-017 says the agent "MUST consider" freshness scores, and FR-023 says to "reduce overall triage confidence" — but FR-009's escalation condition only checks `confidenceScore`, not an adjusted/effective confidence that incorporates freshness. Are these requirements aligned? [Conflict, Spec §FR-009, FR-017, FR-023]

---

## Traceability & Specification Hygiene

- [ ] CHK071 — Is a requirement and acceptance criteria ID scheme established that maps FRs to acceptance scenarios? User Stories define numbered scenarios but these are not cross-referenced to specific FRs. [Traceability]
- [ ] CHK072 — Are all Constitution principles referenced in the spec traceable to specific requirements? The spec references Principles I, II, and III and NFRs, but no traceability matrix maps each principle to its implementing FR/NFR. [Traceability, Spec §US-1, US-2, US-5]
- [ ] CHK073 — Are the configurable parameters documented in a single consolidated table? Configuration values (escalation threshold, dedup window, lookback hours, staleness thresholds per source, max output tokens, LLM timeout) are scattered across multiple FRs and Assumptions with no summary reference. [Completeness, Gap]
- [ ] CHK074 — Is the spec's "Draft" status (line 5) reflected in the maturity of requirements? Some requirements reference specific file paths (`apps/agents/common/handoffs.py`) which may indicate premature implementation coupling in a draft spec. [Clarity, Spec §Status]

---

**Summary**

| Quality Dimension | Item Count |
|---|---|
| Requirement Completeness | 15 (CHK001–CHK015) |
| Requirement Clarity | 10 (CHK016–CHK025) |
| Requirement Consistency | 7 (CHK026–CHK032) |
| Acceptance Criteria Quality | 5 (CHK033–CHK037) |
| Scenario Coverage | 7 (CHK038–CHK044) |
| Edge Case Coverage | 6 (CHK045–CHK050) |
| Non-Functional Requirements | 8 (CHK051–CHK058) |
| Dependencies & Assumptions | 6 (CHK059–CHK064) |
| Ambiguities & Conflicts | 6 (CHK065–CHK070) |
| Traceability & Hygiene | 4 (CHK071–CHK074) |
| **Total** | **74** |
