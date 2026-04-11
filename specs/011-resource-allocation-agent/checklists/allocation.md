# Requirements Quality Checklist: Resource Allocation Agent

**Purpose**: Validate the completeness, clarity, consistency, and measurability of the Resource Allocation Agent specification before implementation planning  
**Created**: 2025-07-23  
**Feature**: [spec.md](../spec.md)  
**Focus Areas**: Algorithmic scoring, cross-incident priority, partial allocation, multi-agent integration  
**Depth**: Thorough (safety-critical disaster response domain)  
**Audience**: Peer reviewer / specification author

---

## Requirement Completeness

- [ ] CHK001 — Are the specific numeric values for `priority_weight` defined for each priority tier (Tier 1/2/3) and urgency level (critical/high/medium/low) in the scoring formula? The formula `score = capability_match × (1/distance) × availability_factor × priority_weight` references `priority_weight` but no weight table is provided. [Gap, Spec §FR-011]
- [ ] CHK002 — Is the `availability_factor` reduction formula for `returning` resources specified? FR-011 states it is "reduced for `returning` based on estimated return time" but does not define the reduction function (linear decay, step function, threshold). [Gap, Spec §FR-011]
- [ ] CHK003 — Are travel speed assumptions defined for estimated deployment timeline calculations? FR-017 specifies mobilisation overhead and Haversine distance but does not define how distance is converted to travel time (speed assumptions per resource type, terrain factors). [Gap, Spec §FR-017]
- [ ] CHK004 — Is the confidence level calculation formula specified for deployment plans? The spec references confidence as "0.0–1.0 numeric and categorical" and a 0.8 multiplier in fallback, but no base confidence calculation method is defined. [Gap, Spec §FR-014, §FR-033]
- [ ] CHK005 — Are requirements defined for how the consolidated demand queue (FR-009) handles demand removal, fulfilment, or cancellation? The spec defines insertion ordering but not lifecycle management of queue entries. [Gap, Spec §FR-009]
- [ ] CHK006 — Are data retention and time-to-live (TTL) requirements specified for audit records? FR-030/031 define append-only audit records but no archival, retention period, or storage capacity planning requirements exist. [Gap, Spec §FR-030]
- [ ] CHK007 — Are notification or event-emission requirements defined for plan status transitions (proposed → approved → dispatched)? Downstream consumers (dashboard, other agents) need to be informed of plan changes, but no publication mechanism is specified. [Gap]
- [ ] CHK008 — Are requirements defined for what happens when a commander does not approve or reject a plan within a defined time window? No plan expiration, timeout, or escalation requirements exist for pending approvals. [Gap, Spec §FR-026]
- [ ] CHK009 — Are requirements specified for handling resource inventory updates that arrive during active plan generation (race conditions)? The spec does not address the scenario where a resource becomes unavailable between scoring and plan persistence. [Gap, Spec §FR-011]
- [ ] CHK010 — Are requirements defined for load shedding or backpressure when the processing queue depth exceeds the system's capacity? NFR-001 specifies 30 concurrent plans but no behaviour is defined when this threshold is exceeded. [Gap, Spec §NFR-001]
- [ ] CHK011 — Are requirements specified for rollback behaviour when an approved plan's assigned resource becomes unavailable before dispatch? The spec addresses resource destruction (edge cases) but not the plan-level recovery flow after approval. [Gap, Edge Case]
- [ ] CHK012 — Are the format and structural requirements for the human-readable plan summary defined beyond "plain language suitable for incident commanders"? No template structure, required sections, maximum length, or example format is specified. [Gap, Spec §FR-016]
- [ ] CHK013 — Are requirements defined for batch processing of multiple simultaneous handoffs for the same incident? The spec addresses multiple handoffs (US1, scenario 3) via versioning but not whether they should be batched into a single planning cycle or processed sequentially. [Gap, Spec §FR-001]

## Requirement Clarity

- [ ] CHK014 — Is "proportional distribution" for equal-priority tie-breaking precisely defined? FR-022 states "distribute contested resources proportionally based on the ratio of unmet demands" but does not specify whether this is by demand count, demand quantity, population-at-risk, or another metric. [Ambiguity, Spec §FR-022]
- [ ] CHK015 — Is the trade-off analysis format for cross-incident reallocation specified? FR-021 requires "a trade-off analysis showing what each affected incident loses" but does not define the structure, granularity, or content of this analysis. [Ambiguity, Spec §FR-021]
- [ ] CHK016 — Is "AIIMS terminology" sufficiently bounded? FR-016 requires summaries "consistent with AIIMS terminology" but does not reference a specific AIIMS glossary version or list the mandatory terms. [Ambiguity, Spec §FR-016]
- [ ] CHK017 — Are the conditions under which "mechanical issues" are reported for vehicle flagging defined? FR-019(c) flags vehicles with "reported mechanical issues" but does not specify the signal format, severity threshold, or reporting mechanism. [Ambiguity, Spec §FR-019]
- [ ] CHK018 — Is the "configurable staleness window" for last-known-good inventory snapshots specified with a minimum/maximum bound? FR-034 defaults to 30 minutes but does not define acceptable upper limits or behaviour when the snapshot exceeds the window. [Clarity, Spec §FR-034]
- [ ] CHK019 — Is the scope of "content safety validation" for AI-generated outputs defined? FR-037 requires content safety validation but does not specify what constitutes a failure (profanity, bias, factual inaccuracy, harmful recommendations) or the validation mechanism. [Ambiguity, Spec §FR-037]

## Requirement Consistency

- [ ] CHK020 — Are the priority level taxonomies consistent between handoff sources? FR-007 defines urgency as `critical > high > medium > low`, while FR-008 defines transport priority as `critical > immediate > high`. These are different scales from different agents — is the interleaving/mapping between them specified? [Conflict, Spec §FR-007 vs §FR-008]
- [ ] CHK021 — Is the eligibility of `reserved` resources for allocation consistent with the state machine? FR-010 defines a `reserved` state ("held for specific incident"), but FR-011 only lists `available` and `returning` as eligible statuses. Are `reserved` resources intentionally excluded from matching, and if so, is this explicitly documented? [Consistency, Spec §FR-010 vs §FR-011]
- [ ] CHK022 — Are the reallocation approval requirements consistent between FR-013 and FR-021? FR-013 requires commander approval for reassigning resources from active plans; FR-021 requires commander approval for cross-incident reallocation. Are these the same approval mechanism or distinct workflows? [Consistency, Spec §FR-013 vs §FR-021]
- [ ] CHK023 — Is the plan generation SLA consistent across plan types? SC-001 specifies 15 seconds for allocation plans and 30 seconds for cross-incident analysis. Are plans that involve both single-incident allocation AND cross-incident considerations subject to the 15-second or 30-second threshold? [Consistency, Spec §SC-001]
- [ ] CHK024 — Does the dependency attribution for `AgentHandoffEvent` align with the actual source? The Dependencies section (spec 001) claims spec 001 defines `AgentHandoffEvent`, but the entity is more fully defined in spec 012 (Risk Assessment Agent). Is the canonical definition location documented? [Consistency, Spec §Dependencies]

## Acceptance Criteria Quality

- [ ] CHK025 — Can SC-006's "30% improvement in resource deployment efficiency compared to manual allocation baselines" be objectively measured? No baseline measurement methodology, sample scenario set, or statistical test is specified. How is "manual allocation baseline" established and what deployment scenarios are included? [Measurability, Spec §SC-006]
- [ ] CHK026 — Can SC-010's "90% of incident commanders rate plans as clear, actionable, and appropriately prioritised" be objectively measured? No minimum sample size, statistical confidence interval, or survey administration protocol is defined. [Measurability, Spec §SC-010]
- [ ] CHK027 — Are the observability metric alerting thresholds specified? NFR-002 states "all metrics MUST support alerting thresholds" but does not define any specific thresholds (e.g., what `allocation_latency` p99 triggers an alert). [Gap, Spec §NFR-002]
- [ ] CHK028 — Is the health endpoint's 1-second response time requirement (FR-035) defined for degraded conditions? The spec states "under normal operation" — what is the acceptable response time when dependencies are unhealthy? [Gap, Spec §FR-035]

## Scenario Coverage

- [ ] CHK029 — Are requirements defined for the scenario where a transport dispatch request references a superseded evacuation plan AND no newer active plan exists for that incident? The edge case addresses superseded plans but only when a newer plan exists. [Coverage, Edge Case]
- [ ] CHK030 — Are requirements specified for how the agent handles a resource that transitions from `en_route` or `deployed` back to `available` unexpectedly (e.g., resource recalled by its managing organisation)? The state machine permits this but no business rules govern the impact on active plans. [Coverage, Spec §FR-010]
- [ ] CHK031 — Are requirements defined for the scenario where the same resource is recommended for reallocation by two different cross-incident analyses simultaneously? No concurrency control for cross-incident reallocation recommendations is specified. [Coverage, Gap]
- [ ] CHK032 — Are requirements specified for handling handoffs that arrive for an incident that has been resolved or closed? FR-004 validates incident existence but not incident status (active vs. closed). [Coverage, Spec §FR-004]
- [ ] CHK033 — Are requirements defined for the scenario where a partial allocation plan is approved but the remaining unmet demands are later fulfillable (new resources become available)? Is automatic re-planning triggered, or does it require a new handoff? [Coverage, Gap]
- [ ] CHK034 — Are acceptance scenarios defined for User Story 6 (Resource Status Tracking) that cover the full state machine cycle including the `reserved` → `assigned` and `reserved` → `available` transitions? US6 scenarios cover deployed/consumed/rotation but not the reservation lifecycle. [Coverage, Spec §US6]

## Edge Case & Boundary Coverage

- [ ] CHK035 — Are boundary conditions defined for the scoring formula when distance approaches zero (resource co-located with demand)? The formula uses `1/distance`, which produces infinity at zero distance. Is a minimum distance floor or alternative scoring specified? [Edge Case, Spec §FR-011]
- [ ] CHK036 — Are requirements defined for handling resource inventory items with missing or invalid location coordinates? The Haversine calculation requires valid coordinates — what happens when a resource has no location data? [Edge Case, Spec §FR-011]
- [ ] CHK037 — Are requirements defined for the edge case where optimistic concurrency control fails repeatedly during plan version creation (high contention)? FR-015 specifies optimistic concurrency but no retry limit, backoff strategy, or failure mode is defined. [Edge Case, Spec §FR-015]
- [ ] CHK038 — Is the boundary between "in-memory buffer exhausted" and "local file fallback" for audit storage degradation quantified? FR-031a defines the three tiers but not the memory buffer capacity or the trigger condition for tier 3 activation. [Edge Case, Spec §FR-031a]
- [ ] CHK039 — Are requirements defined for what constitutes a "valid state transition" rejection in FR-018? If an invalid transition is requested (e.g., `available` → `deployed` skipping `assigned` and `en_route`), is the signal rejected, the resource flagged, or the transition logged as an anomaly? [Edge Case, Spec §FR-018]

## Non-Functional Requirements Coverage

- [ ] CHK040 — Are security requirements specified for the override mechanism? FR-024 records `override_by_user_id` and `override_by_role` but no authentication, authorisation, or role-based access control requirements are defined for who may perform overrides. [Gap, Security]
- [ ] CHK041 — Are data sensitivity and encryption requirements specified for deployment plans containing location coordinates, personnel assignments, and incident details? No data classification or protection requirements are defined. [Gap, Security]
- [ ] CHK042 — Are performance requirements specified for the resource matching algorithm at scale? FR-011 defines the algorithm but no maximum inventory size, maximum demand count, or computational complexity constraints are documented. [Gap, Spec §FR-011, §NFR-001]
- [ ] CHK043 — Are accessibility requirements defined for the human-readable plan summaries? FR-016 targets incident commanders but no readability level, format accessibility, or multi-format output requirements are specified. [Gap, Accessibility]

## Dependencies & Assumptions

- [ ] CHK044 — Is the assumption that "resource inventory is pre-loaded from a static configuration file" (Assumptions) consistent with the dynamic `resource_status` signal processing requirement (FR-018)? Are the boundaries between static inventory structure and dynamic status updates clearly delineated? [Assumption, Spec §Assumptions vs §FR-018]
- [ ] CHK045 — Is the dependency on spec 009's `TransportRequirement` entity format validated against spec 011's consumption requirements (FR-005, FR-008)? The priority levels used in FR-008 (`critical > immediate > high`) must match what spec 009 actually produces. [Dependency, Spec §FR-005, §FR-008]
- [ ] CHK046 — Is the assumption that "the agent does not directly interface with physical dispatch systems" clearly reflected in all functional requirements? FR-010's state machine includes `en_route` and `deployed` transitions — are the signal sources for these transitions specified, or is this a gap in the assumption? [Assumption, Spec §Assumptions vs §FR-010]

## Traceability

- [ ] CHK047 — Does every acceptance scenario in User Stories 1–8 map to at least one functional requirement (FR-001–FR-037) and one success criterion (SC-001–SC-010)? Are there acceptance scenarios without corresponding FRs, or FRs without acceptance scenario coverage? [Traceability]
- [ ] CHK048 — Is a requirement and acceptance criteria ID scheme established that enables bidirectional tracing between user stories, functional requirements, success criteria, and test scenarios? [Traceability]

---

## Summary

| Dimension                      | Item Count |
| ------------------------------ | ---------- |
| Requirement Completeness       | 13         |
| Requirement Clarity            | 6          |
| Requirement Consistency        | 5          |
| Acceptance Criteria Quality    | 4          |
| Scenario Coverage              | 6          |
| Edge Case & Boundary Coverage  | 5          |
| Non-Functional Requirements    | 4          |
| Dependencies & Assumptions     | 3          |
| Traceability                   | 2          |
| **Total**                      | **48**     |

## Notes

- **Defaults applied**: Depth = Thorough (safety-critical domain), Audience = Peer Reviewer, Focus = All major domains with emphasis on algorithmic scoring, cross-incident priority, partial allocation, and multi-agent integration.
- **Highest-risk findings**: CHK001 (undefined priority weights in scoring formula), CHK020 (inconsistent priority taxonomies across agents), CHK035 (division-by-zero in scoring at zero distance), CHK025 (unmeasurable 30% efficiency improvement baseline).
- **Existing checklist**: `requirements.md` covers 16 generic spec-readiness items (all passing). This checklist provides domain-specific requirements quality validation at a deeper level.
- **Cross-spec validation**: Verified dependency contracts against specs 001, 006, 007, 009, and 012. Key finding: `AgentHandoffEvent` canonical definition location is ambiguous between spec 001 and spec 012 (CHK024).
