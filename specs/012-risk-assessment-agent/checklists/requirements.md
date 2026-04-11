# Comprehensive Requirements Quality Checklist: Risk Assessment Agent

**Purpose**: Validate the completeness, clarity, consistency, measurability, and coverage of the Risk Assessment Agent specification across nine focus areas — hazard prediction accuracy, reproducibility, multi-source correlation, contradictory signal handling, versioned assessments, graceful degradation, audit trail, AIDR severity alignment, and Azure-only deployment in Australian regions.  
**Created**: 2026-04-15  
**Updated**: 2026-04-15  
**Feature**: [spec.md](../spec.md)  
**Depth**: Comprehensive (formal review gate)  
**Audience**: Reviewer (PR / architecture review)

---

## Hazard Prediction Accuracy

- [ ] CHK001 — Is "hazard impact prediction" formally defined with measurable accuracy criteria, or only implied by narrative descriptions? [Clarity, Gap — no explicit accuracy metric defined; SC-003 covers contradiction detection rate but not prediction accuracy]
- [ ] CHK002 — Are the inputs to the confidence score calculation (signal confidence, freshness, source diversity, contradictions) weighted with specific formulas or ranges, or is the combination method left ambiguous? [Clarity, Spec §FR-007]
- [ ] CHK003 — Is the mapping from raw confidence score (0.0–1.0) to discrete confidence level (`low`/`medium`/`high`) specified with unambiguous boundary behaviour (e.g., does exactly 0.4 map to `low` or `medium`)? [Ambiguity, Spec §FR-007]
- [ ] CHK004 — Are the assessment type derivation rules in FR-010 complete for all signal categories the Monitoring Agent can produce, or could an unmapped category arrive? [Completeness, Spec §FR-010]
- [ ] CHK005 — Is the fallback behaviour defined when a signal's category does not match any entry in the configurable signal-to-assessment-type mapping? [Edge Case, Spec §FR-010]
- [ ] CHK006 — Are "scenario-specific risk calculation parameters" for each disaster type (bushfire, cyclone, flood, earthquake, tsunami) enumerated or left as a placeholder? [Completeness, Spec §FR-010a]
- [ ] CHK007 — Is the relationship between `affected_population_estimate` and severity computation specified with concrete thresholds or ranges, or is it described only as a contributing factor? [Clarity, Spec §FR-010d]
- [ ] CHK008 — Are prediction accuracy requirements defined for each disaster scenario type, or does the spec assume uniform accuracy across bushfire, cyclone, flood, earthquake, and tsunami? [Coverage, Gap]
- [ ] CHK009 — Is the 10-second SLA (SC-001) measured from handoff receipt to assessment persistence, or to assessment availability for downstream consumption? The boundary is not specified. [Ambiguity, Spec §SC-001]
- [ ] CHK010 — Does the spec define what "produced within 10 seconds" means when the agent must retrieve signals from an external store that may itself be slow? Is signal retrieval time included in the SLA? [Clarity, Spec §SC-001]

## Reproducibility

- [ ] CHK011 — Is reproducibility defined as bitwise-identical outputs or semantic equivalence (same category, severity, recommendation types)? FR-026 specifies "identical hazard category, severity, and recommendation types" but SC-004 says "identical assessment confidence levels and recommendation types" — are these aligned? [Consistency, Spec §FR-026 vs §SC-004]
- [ ] CHK012 — Does the spec address reproducibility across LLM model version upgrades? FR-025 stores the LLM deployment ID, but is there a requirement to maintain reproducibility when the deployment ID changes? [Coverage, Spec §FR-025]
- [ ] CHK013 — Is the requirement for LLM temperature=0 sufficient to guarantee deterministic outputs, or should the spec acknowledge that temperature=0 is necessary but not sufficient (e.g., model updates, infrastructure changes)? [Assumption, Spec §FR-026]
- [ ] CHK014 — Is the "complete input snapshot" in FR-025 defined exhaustively, or could additional implicit inputs (e.g., system clock, random seeds, Azure region) affect reproducibility without being captured? [Completeness, Spec §FR-025]
- [ ] CHK015 — Are reproducibility requirements defined for template-based fallback mode, or only for LLM-generated assessments? [Coverage, Spec §FR-026]
- [ ] CHK016 — Does the spec define how reproducibility is verified in practice — is there a requirement for a reproducibility test harness, comparison tooling, or acceptance test methodology? [Gap, Spec §SC-004]
- [ ] CHK017 — Is the "configuration version" that must be stored (FR-025) defined with a specific schema or versioning strategy, or is it left to implementation? [Clarity, Spec §FR-025]

## Multi-Source Correlation

- [ ] CHK018 — Are the source weight values (authoritative 2×, IoT 1×, social 0.5×) specified as defaults with a mechanism for override, or are they fixed constants? FR-011 says "weighted averaging" but FR-014 says "consistent with" FR-011 — is runtime configurability required? [Clarity, Spec §FR-011, §FR-014]
- [ ] CHK019 — Is "weighted averaging" defined with a specific formula (e.g., weighted mean of confidence scores, weighted vote count), or is the aggregation method left to implementation? [Ambiguity, Spec §FR-011]
- [ ] CHK020 — Are the source categories (authoritative, IoT, social media) exhaustive, or could signals from other source types (e.g., satellite, aerial, government reports) arrive? Is there a default weight for unmapped source types? [Completeness, Spec §FR-011]
- [ ] CHK021 — Does the spec define how geographic proximity is determined for multi-source correlation? "Same incident and geographic area" is used but the area granularity (exact coordinates, bounding box, administrative region) is not specified. [Ambiguity, Spec §FR-011]
- [ ] CHK022 — Is the correlation requirement scoped to signals within a single handoff, or does the agent also correlate signals across multiple handoffs for the same incident? [Ambiguity, Spec §FR-011]
- [ ] CHK023 — Are requirements defined for the minimum number of corroborating sources needed before the agent increases confidence beyond a single-source baseline? [Gap]
- [ ] CHK024 — Does the spec define how "diversity of corroborating sources" (FR-007) is measured — by source type, geographic origin, temporal spread, or some combination? [Clarity, Spec §FR-007]

## Contradictory Signal Handling

- [ ] CHK025 — Is "opposing risk trajectories" defined with objective criteria (e.g., one signal indicates risk increasing while another indicates risk decreasing for the same parameter), or is it left to subjective interpretation? [Clarity, Spec §FR-012]
- [ ] CHK026 — Is the 30% confidence reduction for contradictions (FR-013) applied multiplicatively (new = old × 0.7) or subtractively (new = old − 0.30)? The spec does not specify. [Ambiguity, Spec §FR-013]
- [ ] CHK027 — Are requirements defined for handling more than two contradictory signals (e.g., three-way disagreement)? Is the 30% reduction applied once regardless of the number of contradictions, or scaled? [Coverage, Spec §FR-013]
- [ ] CHK028 — Does the 95% detection target (SC-003) have a defined labelled test set size, composition, or refresh cadence, or is the benchmark left unspecified? [Measurability, Spec §SC-003]
- [ ] CHK029 — Are contradictions between signals of different source authority levels (e.g., BoM vs. community sensor) handled differently from contradictions between same-authority sources? [Coverage, Spec §FR-012, §FR-014]
- [ ] CHK030 — Is the human review flag triggered by contradiction (FR-013) defined with a specific workflow — who reviews, within what timeframe, and what actions can they take? [Gap, Spec §FR-013]
- [ ] CHK031 — Can a contradiction be detected between a fresh and a stale signal? If so, does the staleness penalty (FR-015) compound with the contradiction penalty (FR-013), and is the combined reduction defined? [Edge Case, Spec §FR-013 vs §FR-015]

## Versioned Assessments

- [ ] CHK032 — Is the monotonically increasing version number (FR-006) guaranteed under concurrent processing? If two handoffs for the same incident arrive simultaneously, is the version assignment order defined? [Edge Case, Spec §FR-006]
- [ ] CHK033 — Does the spec define the relationship between assessment versions and recommendation versions? When a new assessment version is created, does it automatically generate new recommendations or only when the assessment content materially changes? [Gap, Spec §FR-006, §FR-017]
- [ ] CHK034 — Is the `valid_until` timestamp requirement (FR-010b) consistent with the immutability requirement (FR-006)? When an assessment is marked `superseded` or `expired`, is this a status update on an immutable record, and if so, is the exception to immutability explicitly acknowledged? [Consistency, Spec §FR-006 vs §FR-010b]
- [ ] CHK035 — Are requirements defined for querying assessment version history — can incident commanders retrieve all versions for an incident and assessment type, and is there a defined sort order? [Gap, Spec §FR-006]
- [ ] CHK036 — Is the version format `{incident_id}_v{N}` unique across assessment types for the same incident, or is N scoped per incident + assessment type? The spec says "per incident and assessment type" in FR-006 but the format only includes `incident_id`. [Ambiguity, Spec §FR-006]
- [ ] CHK037 — Does the spec define maximum version limits per incident, or could unbounded version growth during a long-duration incident create storage or performance concerns? [Edge Case, Gap]
- [ ] CHK038 — Are requirements defined for version comparison — can a user diff two versions of the same assessment to understand what changed between them? [Gap]

## Graceful Degradation

- [ ] CHK039 — Is the 20% confidence reduction in LLM fallback mode (FR-031) applied before or after other adjustments (contradiction 30%, stale signals)? Is the order of penalty application specified? [Ambiguity, Spec §FR-031]
- [ ] CHK040 — Does the spec define how the agent detects LLM unavailability — by timeout, error code, circuit breaker, or health check? The detection mechanism affects recovery behaviour. [Gap, Spec §FR-031]
- [ ] CHK041 — Is the template-based fallback content defined or referenced? Are template quality requirements specified (e.g., must include signal IDs, must be human-readable)? [Completeness, Spec §FR-008, §FR-031]
- [ ] CHK042 — Does the spec define degradation priority — if both the LLM and the signal store are partially unavailable simultaneously, how are the penalties combined? [Edge Case, Spec §FR-031 vs §FR-032]
- [ ] CHK043 — Is "proportional" confidence reduction for missing signals (FR-032) defined with a specific formula (e.g., reduce by the fraction of missing signals), or is proportionality left to interpretation? [Ambiguity, Spec §FR-032]
- [ ] CHK044 — Are requirements defined for the recovery path from degraded to normal mode? FR-031 mentions the agent "resumes generating enriched explanations" but User Story 7 Acceptance Scenario 2 is the only reference — is a warm-up or backfill requirement needed? [Gap, Spec §FR-031]
- [ ] CHK045 — Does the spec define what happens when the downstream agent (Communication, Evacuation, Resource Allocation) is unavailable? FR-023 defines retry and dead-letter, but is incident commander notification for dead-lettered handoffs specified with a delivery mechanism? [Clarity, Spec §FR-023]
- [ ] CHK046 — Is the `/health` endpoint response schema defined beyond the three status fields (LLM, signal store, queue depth), or are the field names, types, and healthy/unhealthy thresholds left unspecified? [Completeness, Spec §FR-033]
- [ ] CHK047 — Does the spec define behaviour when the Cosmos DB audit store itself is unavailable? FR-034 says the agent must not halt for any single dependency, but FR-028/FR-029 mandate audit records for every step — is this a conflict? [Conflict, Spec §FR-034 vs §FR-028]

## Audit Trail

- [ ] CHK048 — Is the audit record schema (FR-029) complete? The field list includes `handoff_id, input_signals, assessment_result, confidence, version, model_used, prompt_template_version, processing_duration, decision_rationale, generation_method, agent_version, configuration_version, timestamp` — but the Key Entities section for `RiskAssessmentDecisionRecord` lists different fields. Are these consistent? [Consistency, Spec §FR-029 vs Key Entities]
- [ ] CHK049 — Is "append-only with no TTL" (FR-030) reconcilable with data retention obligations? Does the spec define or reference a data retention policy, or is indefinite retention assumed? [Gap, Spec §FR-030]
- [ ] CHK050 — Are audit trail query requirements defined — who can query, what filters are available, what response times are expected for retrieval? User Story 6 describes a post-incident review but no query interface requirements are specified. [Gap, Spec §US-6]
- [ ] CHK051 — Is the audit record for "content safety failure" (FR-028) defined with sufficient detail — does it capture the original LLM output that failed validation, or only the fact that a failure occurred? [Clarity, Spec §FR-028, §FR-035]
- [ ] CHK052 — Are audit records required for successful outcomes (e.g., "no contradiction detected", "all signals fresh") or only for anomalous events? FR-028 says "every processing step" but the enumerated list appears to focus on exception paths. [Ambiguity, Spec §FR-028]
- [ ] CHK053 — Does the spec define audit record ordering guarantees — must records be queryable in causal order, or is timestamp ordering sufficient given potential clock skew across distributed components? [Gap, Spec §FR-029]
- [ ] CHK054 — Is the relationship between `RiskAssessmentDecisionRecord` (audit entry) and `HazardAssessment`/`Recommendation` records defined as referential links, or are they independent documents? [Clarity, Spec Key Entities]
- [ ] CHK055 — Are storage sizing or partitioning requirements for audit records addressed? Given append-only with no TTL and 100 concurrent assessments at peak, are growth projections or capacity requirements documented? [Gap, Spec §FR-030, §NFR-001]

## AIDR Severity Alignment

- [ ] CHK056 — Are the AIDR severity levels (`low`, `moderate`, `high`, `critical`) in FR-010d mapped to specific AIDR framework references or publication versions, or is the alignment stated without citation? [Traceability, Spec §FR-010d]
- [ ] CHK057 — Is the severity computation formula (from signal category, confidence score, and affected population estimate) specified with concrete thresholds or decision boundaries, or is the combination method left ambiguous? [Clarity, Spec §FR-010d]
- [ ] CHK058 — Is the relationship between severity level and escalation thresholds consistent? FR-021 requires severity ≥ `high` for evacuation escalation, but FR-020 (communication) uses only confidence score — is this asymmetry intentional and documented? [Consistency, Spec §FR-020 vs §FR-021]
- [ ] CHK059 — Does the fallback severity mapping in FR-031 (e.g., `fire→high`, `cyclone→critical`) align with the AIDR framework definitions in FR-010d, or could the default mappings contradict the stated AIDR semantics? [Consistency, Spec §FR-010d vs §FR-031]
- [ ] CHK060 — Is the one-level severity downgrade in fallback mode (FR-031, when confidence < 0.4) defined for all severity levels — can `low` be downgraded further, or is it a floor? [Edge Case, Spec §FR-031]
- [ ] CHK061 — Are severity levels required to be stable within a single assessment version, or can severity change during processing? If the affected population estimate is revised mid-assessment, are requirements defined for handling this? [Gap, Spec §FR-010d]
- [ ] CHK062 — Does the spec distinguish between severity as assessed by the agent and severity as perceived by incident commanders? Is there a requirement for severity justification or explanation beyond the numeric computation? [Gap, Spec §FR-010d]

## Azure-Only Deployment & Australian Regions

- [ ] CHK063 — Are Azure region requirements specified for data sovereignty — must all data (signals, assessments, recommendations, audit records) remain within Australian Azure regions, and which specific regions are designated? [Gap — spec mentions Azure services but not region constraints]
- [ ] CHK064 — Is the requirement for Azure Service Bus as the messaging transport (FR-001, Assumptions) consistent with Australian region availability, and are failover region requirements defined? [Completeness, Spec §FR-001]
- [ ] CHK065 — Are Cosmos DB region and replication requirements defined for the audit trail and assessment storage? Is geo-redundancy within Australian regions required or optional? [Gap, Spec §FR-029, §FR-030]
- [ ] CHK066 — Is the Azure OpenAI deployment region specified or constrained to Australian regions? If Azure OpenAI is not available in Australian regions, are the data residency implications of cross-region LLM calls addressed? [Gap, Spec Assumptions]
- [ ] CHK067 — Are Azure Container Apps scaling limits in Australian regions documented or referenced? NFR-001 requires 100 concurrent assessments — is this validated against Australian region capacity? [Gap, Spec §NFR-001]
- [ ] CHK068 — Does the spec define network isolation requirements (e.g., VNet integration, private endpoints) for Azure services used by the agent? [Gap]
- [ ] CHK069 — Are disaster recovery requirements for the agent itself defined — multi-region failover, RPO/RTO targets, or backup region designation within Australia? [Gap]
- [ ] CHK070 — Is compliance with Australian government data classification requirements (e.g., PROTECTED, OFFICIAL:Sensitive) addressed or referenced for the assessment and audit data? [Gap]

## Requirement Completeness (Cross-Cutting)

- [ ] CHK071 — Are requirements defined for the `hazard_map` structured JSON output referenced in Key Entities — who produces the GeoJSON polygon, what coordinate system is used, and what validation applies? [Gap, Spec Key Entities §HazardAssessment]
- [ ] CHK072 — Is the `population_estimate` field in the hazard map sourced from a specified data set, or is the data source left undefined? This field directly influences severity computation (FR-010d). [Gap, Spec Key Entities]
- [ ] CHK073 — Are requirements for the `time_horizon` field in the hazard map specified — what units, what range, and how is it computed? [Gap, Spec Key Entities]
- [ ] CHK074 — Is the Recommendation status lifecycle (`proposed → under review → approved/rejected/escalated → executed/expired`) defined with state transition rules, or is it listed without transition constraints? [Clarity, Spec Key Entities §Recommendation]
- [ ] CHK075 — Are requirements defined for concurrent human overrides — what happens if two incident commanders attempt to override the same recommendation simultaneously? [Edge Case, Spec §FR-037]
- [ ] CHK076 — Does the spec define authorization requirements for human overrides — must the overriding user have a specific role, and is role-based access control specified? [Gap, Spec §FR-037]
- [ ] CHK077 — Is the `scope_key` field in `AgentHandoffEvent` (Key Entities) defined or referenced? It appears in the entity definition but no functional requirement addresses it. [Gap, Spec Key Entities §AgentHandoffEvent]
- [ ] CHK078 — Are performance requirements defined for audit trail writes — must audit records be written synchronously (blocking assessment delivery) or can they be asynchronous (risking audit gaps)? [Gap, Spec §FR-028]

## Requirement Clarity & Ambiguity

- [ ] CHK079 — Is "human-readable summary" (FR-005) defined with clarity criteria — minimum content, maximum length, target reading level, or required information elements? [Clarity, Spec §FR-005]
- [ ] CHK080 — Is "clear and traceable" (SC-008) defined with specific rubric dimensions beyond the mention of "5-point rubric across clarity, traceability, and decision confidence"? Are the rubric scales defined? [Measurability, Spec §SC-008]
- [ ] CHK081 — Is "timely downstream escalation" (SC-001) quantified beyond the 10-second processing SLA? The 15-second handoff delivery target (SC-007) is separate — is the total end-to-end time from handoff receipt to downstream agent notification specified? [Clarity, Spec §SC-001 vs §SC-007]
- [ ] CHK082 — Is "at least 90% of incident commanders" (SC-008) based on a defined minimum sample size, or could a single exercise with two participants satisfy this criterion? [Measurability, Spec §SC-008]
- [ ] CHK083 — Is "exponential backoff with a maximum of 3 retries" (FR-023) specified with initial delay, backoff multiplier, and maximum delay values? [Clarity, Spec §FR-023]
- [ ] CHK084 — Is the "5-second acknowledgement" requirement (FR-001) defined as time-to-first-byte on the Service Bus message, or time to persist an audit record of receipt? [Ambiguity, Spec §FR-001]

## Scenario Coverage & Edge Cases

- [ ] CHK085 — Are requirements defined for handling a handoff that references an incident which is already closed or resolved? The spec covers missing incidents (FR-004) but not closed ones. [Edge Case, Gap]
- [ ] CHK086 — Are requirements defined for rate limiting or backpressure when handoff volume exceeds the 100-concurrent-assessment capacity? [Edge Case, Spec §NFR-001]
- [ ] CHK087 — Does the spec address the scenario where a simulation tenant handoff is accidentally routed to the live processing path, or vice versa? Are guardrails specified beyond "tenant isolation at the data layer"? [Edge Case, Spec §FR-027]
- [ ] CHK088 — Are requirements defined for assessment ordering when multiple assessment types are generated from the same handoff? Must spread_prediction complete before community_impact, or can they be parallel? [Gap, Spec §FR-010]
- [ ] CHK089 — Does the spec define behaviour when the content safety validator itself is unavailable? FR-035 mandates validation but FR-034 mandates no halt for any single dependency. [Conflict, Spec §FR-035 vs §FR-034]
- [ ] CHK090 — Are requirements defined for handling a modified recommendation (FR-038) that has already triggered a downstream handoff? Can the downstream handoff be recalled or superseded? [Edge Case, Spec §FR-038]
- [ ] CHK091 — Is the interaction between assessment expiry (FR-010b, `valid_until`) and active downstream handoffs defined? If an assessment expires while a downstream agent is still processing its handoff, are there requirements for notification or recall? [Edge Case, Spec §FR-010b]

## Dependencies & Assumptions

- [ ] CHK092 — Is the dependency on spec 005 (Data Source Governance) for trust tiers mapped to specific weight values in FR-011, or is the trust-tier-to-weight mapping defined independently in this spec? [Consistency, Spec §FR-011 vs Dependencies]
- [ ] CHK093 — Are the Monitoring Agent's handoff payload fields documented or referenced with sufficient detail to validate FR-001 and FR-002 without consulting spec 010? [Completeness, Spec Assumptions]
- [ ] CHK094 — Is the assumption that "downstream agent processing is out of scope" (Out of Scope) consistent with the requirement to surface dead-lettered handoffs to incident commanders (FR-023)? Surfacing implies some awareness of downstream status. [Consistency, Spec §FR-023 vs Out of Scope]
- [ ] CHK095 — Does the spec define the contract between the Risk Assessment Agent and the signal store (spec 006) — query interface, expected latency, error codes, pagination for large signal sets? [Gap, Spec Dependencies]
- [ ] CHK096 — Is the assumption that `LLMCallMixin` provides `_generate_with_fallback` validated against the actual implementation, or is this an unverified dependency? [Assumption, Spec Assumptions]

## Non-Functional Requirements Coverage

- [ ] CHK097 — Are security requirements defined for the agent beyond content safety (FR-035/FR-036) — authentication, authorization, encryption at rest, encryption in transit, secret management? [Gap]
- [ ] CHK098 — Are latency requirements defined for individual sub-operations (signal retrieval, LLM call, Cosmos DB write, Service Bus publish), or only for the end-to-end 10-second SLA? [Gap, Spec §SC-001]
- [ ] CHK099 — Are the observability metrics in NFR-002 defined with alerting thresholds, or are thresholds stated as required without specifying values? [Clarity, Spec §NFR-002]
- [ ] CHK100 — Is a requirement for structured logging defined, or is "log" used throughout the spec without specifying log format, level, or correlation ID propagation? [Gap, Spec §FR-003, §FR-004, §FR-031]
- [ ] CHK101 — Are testing requirements beyond reproducibility (SC-004) and contradiction detection (SC-003) defined — load testing, chaos testing, integration testing with upstream/downstream agents? [Gap]
- [ ] CHK102 — Is the requirement for 100 concurrent assessments (NFR-001) accompanied by a load profile — expected burst duration, ramp-up pattern, sustained vs. peak? [Completeness, Spec §NFR-001]

---

## Notes

- **Focus areas selected**: Hazard prediction accuracy, reproducibility, multi-source correlation, contradictory signal handling, versioned assessments, graceful degradation, audit trail, AIDR severity alignment, Azure-only deployment in Australian regions.
- **Depth level**: Comprehensive — suitable for formal architecture or PR review gate.
- **Audience**: Reviewers and architects validating specification quality before implementation planning.
- **Key observation**: The spec is thorough on functional requirements (FR-001 through FR-038) and user stories, but gaps concentrate in three areas: (1) computation formulas and boundary conditions are often stated qualitatively rather than quantitatively, (2) Azure region and data sovereignty constraints are absent despite the Australian disaster response domain, and (3) cross-requirement interactions (penalty stacking, concurrent edge cases, dependency failures) are not fully addressed.
- **Traceability**: 95 of 102 items include at least one spec section reference or explicit `[Gap]` marker.
- Items are numbered CHK001–CHK102 for cross-reference in reviews.
- Check items off as resolved: `[x]`
- Add inline findings or clarification answers as sub-bullets beneath each item.
