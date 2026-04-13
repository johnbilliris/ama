# Research: AIDR Guidance Integration

**Feature**: 018-aidr-guidance-integration  
**Date**: 2025-07-20  
**Status**: Complete — all NEEDS CLARIFICATION resolved

---

## R-001: PPRR Phase Storage When No Incident Exists

**Source**: CHK045/CHK046 (checklist), FR-050 (spec)  
**Problem**: FR-050 specifies `pprr_phase` on the `Incident` model, but also states "Prevention and Preparedness phases MAY apply to scenario/region contexts without an active incident." The `Incident` model cannot host a phase when no incident record exists.

**Decision**: Introduce a `PprrPhaseContext` model that represents a PPRR phase designation for a non-incident context (region or scenario). The `Incident.pprr_phase` field handles incident-bound phases; `PprrPhaseContext` handles region/scenario-bound Prevention and Preparedness phases.

**Rationale**: 
- The existing `Incident` model has a strong semantic contract — every field assumes an incident exists (e.g., `incident_id`, `started_at`). Creating phantom incidents violates this contract and forces null-guarding across all incident-consuming code.
- `PprrPhaseContext` is a lightweight model with `context_id`, `context_type` (region|scenario), `context_reference_id` (jurisdiction_id or scenario_template_id), `pprr_phase`, `activated_at`, `activated_by`, and `notes`.
- When a Prevention/Preparedness context transitions to Response (i.e., a real incident is created), the `PprrPhaseContext` is closed and the phase transfers to the new `Incident.pprr_phase`.

**Alternatives considered**:
1. *Overload `Incident` with sentinel records* — Rejected. All incident consumers would need to handle "non-incident incidents." The existing `Incident.status` has no value for "not yet an incident."
2. *Store PPRR phase on `Jurisdiction` or `ScenarioTemplate`* — Rejected. PPRR phase is a temporal designation, not a permanent attribute of a jurisdiction. It would bloat those models with lifecycle fields.
3. *Use `TimelineEvent` without an incident* — Rejected. `TimelineEvent.incident_id` is required (not optional). Making it optional would break all existing timeline consumers.

---

## R-002: Graceful Degradation for AWS Warnings and AIIMS Role Assignment

**Source**: CHK069 (checklist), Constitution NN-5  
**Problem**: NFR-011 and NFR-012 define graceful degradation only for the lessons register and recovery dashboard. The checklist identified that AWS warning generation and AIIMS role assignment lack explicit degradation requirements, despite Constitution NN-5 mandating degradation for any single service failure.

**Decision**: Implement graceful degradation for all new AIDR capabilities:

| Capability | Degradation Behaviour |
|---|---|
| AWS warning generation | If LLM is unavailable, fall back to template-based warning generation (existing `generation_method = "template_fallback"` pattern in `PublicAlert`). If Cosmos DB is unavailable, buffer warnings locally and sync on recovery. Warning validation still runs locally (no external dependency). |
| AIIMS role assignment | If role assignment service is unavailable, agents operate with their default AIIMS mapping from configuration (static fallback). The COP displays last-known role assignments with a staleness indicator. |
| PPRR phase transitions | If transition service is unavailable, agents continue operating in their current phase. Phase transition requests are queued and applied when service recovers. |
| Evacuation stages | Evacuation agent already has circuit breaker pattern (existing `common/circuit_breaker.py`). Stage transitions buffer locally if API is unavailable. |

**Rationale**: The Constitution's non-negotiable §5 states "the platform MUST continue to function (at reduced capability) if any single agent, service, or region becomes unavailable." This is absolute — the spec's NFR gaps don't override the Constitution. The existing `circuit_breaker.py` and `template_fallback` patterns provide proven mechanisms to extend.

**Alternatives considered**:
1. *Only implement what the spec NFRs explicitly require* — Rejected. Constitution is supreme over spec; the spec is subordinate to the Constitution per the spec's own Assumptions section.
2. *Add full redundancy for every AIDR service* — Rejected. Over-engineered for the current scale. Circuit breaker + local buffering + static fallback is proportionate.

---

## R-003: Manual Recovery Indicators vs Automated Feedback Loop

**Source**: CHK087 (checklist), SC-010, Assumptions  
**Problem**: SC-010 requires community-response indicators within 24 hours of a warning. The Assumptions section states "community-response indicators may initially be manually entered." CHK087 asks whether the 24-hour target is achievable with manual entry.

**Decision**: The 24-hour window is achievable with manual entry. Design the system with:
1. **Manual entry API** — Platform operators enter indicators via recovery dashboard endpoints.
2. **Indicator staleness tracking** — Each indicator has `last_updated_at` and `update_source` (manual|automated|imported) fields.
3. **24-hour alerting** — If an indicator exceeds 24 hours without update after a warning, the system flags it for operator attention.
4. **Future automation hooks** — The indicator model includes `data_source_id` (nullable) for future automated collection. The API accepts both manual POST and batch import endpoints.

**Rationale**: Manual entry within 24 hours is operationally feasible — emergency management agencies already collect shelter utilisation and evacuation compliance data manually during events. The 24-hour window refers to availability for review, not real-time streaming. The design supports progressive automation without architectural change.

**Alternatives considered**:
1. *Require automated collection from day one* — Rejected. No existing data source integrations exist for community-response indicators. Building automated collection for all indicators would delay the core AIDR capability.
2. *Extend the 24-hour window* — Rejected. SC-010 is a success criterion; changing it requires spec amendment.

---

## R-004: Warning Chain and Supersession Data Model

**Source**: CHK010 (checklist), FR-004, FR-005, FR-048  
**Problem**: The spec requires de-escalation notices that reference prior warnings and all-clear notifications that close the warning chain. The `superseded_warning_id` field on `PublicAlert` needs precise chain semantics.

**Decision**: Warning chains are implemented as a singly-linked list using `superseded_warning_id`:
- Each warning optionally references the `alert_id` of the warning it supersedes.
- A "chain" is the set of warnings linked by `superseded_warning_id` traversal.
- Chains do NOT branch — each warning has at most one successor and one predecessor.
- De-escalation creates a new warning at a lower tier that supersedes the higher-tier warning.
- All-clear creates a terminal warning with `warning_tier = null` (it's not a tiered warning) that references the last active warning in the chain.
- Multi-hazard scenarios create independent chains per hazard type (per edge case specification).

**Rationale**: Singly-linked lists are the simplest chain structure. Branching chains would create ambiguity about which warning is "current" for a given hazard/location. The existing `PublicAlert.status` lifecycle (`draft → pending_approval → approved → published → superseded → cancelled`) already supports supersession semantics.

**Alternatives considered**:
1. *Tree-based warning chains (branching)* — Rejected. No spec requirement supports branching. Each hazard/location has one current active warning.
2. *Separate `WarningChain` entity* — Rejected. Over-engineered. The linked-list approach via `superseded_warning_id` is self-describing and requires no additional entity.

---

## R-005: AIIMS Role Assignment vs Existing Framework Models

**Source**: CHK028 (checklist), FR-049, clarification Pass 2  
**Problem**: The existing `OperatingFramework` and `FrameworkAssignment` models define AIIMS as a framework type and assign frameworks to jurisdictions/organisations. FR-049 requires a new `AiimsRoleAssignment` that maps individual agents to AIIMS functions per incident. The relationship between these models needs clarification.

**Decision**: Three-tier AIIMS model hierarchy:
1. **`OperatingFramework`** (existing) — Defines AIIMS as a framework with principles, control model, and escalation rules. One record (`aiims-national` in seed data). Unchanged.
2. **`FrameworkAssignment`** (existing) — Maps the AIIMS framework to jurisdictions/organisations. Defines which entities operate under AIIMS. Unchanged.
3. **`AiimsRoleAssignment`** (new) — Maps a specific agent to one AIIMS function for a specific incident during a specific period. This is the operational layer — created when an incident starts, updated as agents are reassigned.

**Consultation pattern**:
- When an incident is created, the platform checks `FrameworkAssignment` to determine if participating organisations operate under AIIMS.
- If AIIMS applies, `AiimsRoleAssignment` records are created for each agent, consulting the `OperatingFramework` for role definitions.
- Agents query their own `AiimsRoleAssignment` to determine their current AIIMS function.
- The COP reads all `AiimsRoleAssignment` records for an incident to display the AIIMS structure.

**Rationale**: This three-tier design separates framework definition (what AIIMS is), framework applicability (who uses AIIMS), and operational assignment (which agent fills which role right now). Each tier has different lifecycles and consumers.

**Alternatives considered**:
1. *Extend `FrameworkAssignment` with agent-level fields* — Rejected. `FrameworkAssignment` is org/jurisdiction-scoped, not agent-scoped. Adding agent-level assignments would conflate two different granularities.
2. *Store AIIMS role on the agent configuration directly* — Rejected. AIIMS roles are per-incident, not per-agent-globally. An agent might be Intelligence for one incident and Planning for another.

---

## R-006: Recovery Agent Architecture

**Source**: Assumptions (spec), FR-035, FR-032–037  
**Problem**: The spec states "recovery agents" are existing agents operating in recovery-phase mode, not a new standalone agent. How should existing agents gain recovery capabilities?

**Decision**: Implement recovery as a cross-cutting mode on existing agents + a new platform-level recovery service:

1. **Recovery service** (`apps/api/app/services/recovery_service.py`) — Manages `RecoveryEnvironmentTracker` entities, indicator CRUD, regression detection, dashboard data assembly. Exposed via `apps/api/app/api/routes/recovery.py`.
2. **Agent recovery mode** — Each agent checks `Incident.pprr_phase` to determine if it should operate in recovery mode. Specific behaviours:
   - **Resource Allocation Agent**: In recovery mode, prioritises reconstruction resources over response resources (FR-045).
   - **Communication Agent**: In recovery mode, generates community-facing recovery updates aligned with six National Recovery Principles (FR-033).
   - **Monitoring Agent**: In recovery mode, monitors recovery indicator data sources for regression (edge case).
3. **Handoff chain extensions** — New recovery-phase handoff chains route signals through agents configured for recovery (FR-054).

**Rationale**: The spec explicitly disclaims a standalone Recovery Agent. The platform-level service pattern is consistent with how other cross-cutting concerns work (e.g., `public_alert_service.py` for alerts). Agent-mode switching uses the `pprr_phase` field that already exists on `Incident`.

**Alternatives considered**:
1. *Create a dedicated Recovery Agent* — Rejected. Spec Assumptions explicitly state this is not mandated and would be a future enhancement.
2. *Implement recovery only in the API with no agent involvement* — Rejected. FR-035 requires "recovery agents" to activate in parallel with response agents, implying agents must have recovery-aware behaviour.

---

## R-007: Lessons Management Architecture

**Source**: FR-038–042, Assumptions (spec)  
**Problem**: Lessons management is described as "platform-wide" and "cross-cutting," not assigned to a single agent. The design needs to support lessons capture from any agent, trend analysis, and PR quality gate integration.

**Decision**: Implement as a platform service with API endpoints + quality gate webhook:

1. **Lessons service** (`apps/api/app/services/lessons_service.py`) — Manages `Lesson` entities, captures from incidents/exercises, trend analysis, assignment tracking.
2. **Lessons API** (`apps/api/app/api/routes/lessons.py`) — CRUD endpoints, trend analysis endpoint, register view.
3. **Auto-trigger** — When an incident with `incident_level ≥ 2` transitions to `closed` status, or when an exercise report is generated, the event bus triggers lessons capture by creating a `TimelineEvent` with `event_type = "system"` and payload `{"action": "lessons_capture_triggered"}`.
4. **PR quality gate** — A lightweight GitHub Actions check that verifies PR descriptions referencing lesson IDs match open lessons in the register. Implemented as a CI script, not an agent.
5. **Cosmos container** — `lessons` container in the existing Cosmos DB account, partitioned by `incident_id` (or `scenario_run_id` for exercises).

**Rationale**: A platform service is the right pattern for cross-cutting concerns. The event bus already supports system-triggered events via `TimelineEvent`. The PR quality gate is a CI/CD concern, not a runtime agent concern.

**Alternatives considered**:
1. *Dedicated Lessons Agent* — Rejected. Lessons management doesn't fit the agent pattern (it doesn't process signals or make hazard decisions). It's an administrative/governance function.
2. *Embed lessons capture in each agent* — Rejected. Would duplicate capture logic across 5 agents. Centralised service with an API is cleaner.

---

## R-008: Community-Response Indicator Collection for Total Warning System

**Source**: FR-012, SC-010, Assumptions  
**Problem**: The Total Warning System requires community-response indicators (e.g., evacuation compliance, shelter utilisation) to close the feedback loop. The spec assumes manual entry initially.

**Decision**: Implement a community-response indicator model as a subset of the recovery tracking system:
1. **Community-response indicators** are a specialised view of recovery indicators, specifically the Social and Built environment indicators that relate to immediate post-warning behaviour.
2. **Indicator entry** — Manual POST endpoint for operators to submit indicators. Batch import endpoint for future automated sources.
3. **Warning linkage** — Each community-response indicator record references the `alert_id` of the warning it relates to, enabling the feedback loop.
4. **24-hour SLA tracking** — The system tracks whether indicators have been submitted within 24 hours of warning issuance (SC-010).

**Rationale**: Community-response indicators and recovery environment indicators are conceptually related — both track community state. Sharing the underlying data model avoids duplication while allowing different views for different contexts (Total Warning System feedback loop vs. long-term recovery tracking).

**Alternatives considered**:
1. *Separate community-response indicator model* — Rejected. Would create data duplication with recovery indicators. Shelter utilisation is both a community-response indicator and a Built environment recovery indicator.
2. *Defer community-response indicators entirely* — Rejected. SC-010 requires the feedback loop to be closed.

---

## R-009: Interoperability for New AIDR Endpoints

**Source**: Constitution NN-4, CHK093  
**Problem**: Constitution non-negotiable §4 requires standards-based APIs (CAP, EDXL, GeoJSON, OpenAPI). New AIDR capabilities need to comply.

**Decision**:
1. **OpenAPI** — All new FastAPI endpoints automatically generate OpenAPI schemas (FastAPI built-in). No additional work needed.
2. **CAP (Common Alerting Protocol)** — AWS warning generation should produce CAP-compatible alert structures. The existing `PublicAlert` content model can render to CAP XML format via a dedicated serialiser. Implement as an optional `/alerts/{alert_id}/cap` endpoint.
3. **GeoJSON** — Location data in warnings, evacuation zones, and recovery areas uses GeoJSON format. The existing `EvacuationZone` model already uses geographic coordinates; standardise to GeoJSON `Feature` objects.
4. **EDXL** — EDXL-DE (Distribution Element) support for inter-agency message exchange. Implement as a message envelope format option on the warning delivery pipeline, not a separate API.

**Rationale**: FastAPI provides OpenAPI out of the box. CAP and GeoJSON are the most immediately relevant standards for warning and location data. EDXL support can be layered onto the existing delivery pipeline.

**Alternatives considered**:
1. *Only implement OpenAPI, defer others* — Rejected. Constitution non-negotiable requirements cannot be deferred.
2. *Full EDXL-HAVE/EDXL-SitRep implementation* — Rejected. Over-scoped for this feature. EDXL-DE as a message envelope is sufficient for the initial integration.

---

## R-010: Evacuation Stage Re-entry and State Machine

**Source**: CHK036 (checklist), SC-003, edge case (evacuation abandonment)  
**Problem**: Evacuation stages normally progress sequentially (Decision→Warning→Withdrawal→Shelter→Return), but SC-003 allows re-entry to earlier stages (e.g., Decision re-activation during Withdrawal). The state machine needs explicit transition rules.

**Decision**: Implement evacuation stages as a state machine with the following valid transitions:

```
Decision → Warning → Withdrawal → Shelter → Return → Completed
    ↑          ↑          ↑
    └──────────┴──────────┘  (re-entry from any active stage)

Decision → ShelterInPlace → (monitoring) → Decision (re-evaluation)
```

- **Forward transitions**: Decision→Warning→Withdrawal→Shelter→Return→Completed (normal flow).
- **Re-entry transitions**: Any active stage may transition back to Decision when conditions change (route impassable, new hazard data).
- **Shelter-in-place**: Decision may transition to ShelterInPlace instead of Warning. ShelterInPlace may transition back to Decision for re-evaluation.
- Every transition is recorded as a `TimelineEvent` with the source stage, target stage, rationale, and authorising user.
- Re-entry increments a `re_entry_count` on the `EvacuationStage` record for audit.

**Rationale**: A flexible state machine with audited transitions supports the edge cases described in the spec (route impassable, shelter-in-place evaluation) while maintaining sequential normal-flow semantics. The audit trail satisfies Constitution §IV (transparency and auditability).

**Alternatives considered**:
1. *Strict sequential stages with no re-entry* — Rejected. SC-003 explicitly allows re-entry. Edge case describes Decision re-activation during Withdrawal.
2. *Free-form stage transitions (any stage to any stage)* — Rejected. Too permissive. Decision is the only valid re-entry target because it's the decision-making stage that evaluates new conditions.

---

## R-011: Incident Level Field Design

**Source**: FR-015, FR-050, Key Entities (Incident Level)  
**Problem**: The spec defines three incident levels (1, 2, 3) as a separate concept from `Incident.severity` and `HazardAssessment.severity_level`. Where to store this and how it relates to existing fields needs design.

**Decision**: Add `incident_level` as a new field on `Incident`:
- Type: `Literal[1, 2, 3]` with default `1`.
- Independent of `severity` (triage urgency) and `HazardAssessment.severity_level` (risk assessment).
- Level changes trigger `TimelineEvent` records.
- Level determines coordination scope: Level 1 = single-agency autonomous, Level 2 = shared COP + cross-agency, Level 3 = full multi-tier + NCM integration.
- Level also triggers lessons capture: Level 2+ closure auto-triggers the lessons-capture process (FR-038).

**Rationale**: The spec's Key Entities section explicitly states Incident Level is "a new field on existing `Incident` model" and is "independent of `Incident.severity`." An integer Literal is the simplest representation that maps directly to the AIIMS three-level classification.

**Alternatives considered**:
1. *Derive level from severity automatically* — Rejected. Spec clarification (Pass 2) explicitly states there is no automatic mapping between severity scales.
2. *String enum ("level_1", "level_2", "level_3")* — Rejected. Integer is more natural for ordinal comparison (`if incident.incident_level >= 2`).

---

## R-012: Privacy Controls for Social Recovery Data

**Source**: NFR-014, Constitution NN-3  
**Problem**: Social recovery environment data (health, employment, social issues) may contain sensitive information. NFR-014 requires community-level aggregations not be identifiable to fewer than 10 individuals.

**Decision**: Implement k-anonymity (k=10) at the data model level:
1. **Aggregation field** — `RecoveryEnvironmentTracker` indicators include a `population_coverage` integer field recording how many individuals the aggregation covers.
2. **Validation rule** — A Pydantic validator on Social environment indicators rejects records where `population_coverage < 10`.
3. **Geographic granularity** — Social indicators are stored at the LGA (Local Government Area) level minimum, never at individual address level.
4. **Data classification** — Social indicator records carry a `data_classification: Literal["public", "official", "sensitive"]` field. Indicators derived from health or employment data default to `"sensitive"`.

**Rationale**: k-anonymity at k=10 is the minimum required by NFR-014. Enforcing it at the model level (Pydantic validator) prevents accidental insertion of under-aggregated data. LGA-level geographic granularity aligns with how Australian government agencies publish community statistics.

**Alternatives considered**:
1. *Enforce privacy only at the API layer* — Rejected. If the model accepts low-k data, it could leak through non-API paths (e.g., direct Cosmos queries, export scripts).
2. *Differential privacy* — Rejected. Over-engineered for the current scale. k-anonymity is simpler and sufficient for the stated requirement.

---

## R-013: Cosmos DB Container Design for New Models

**Source**: Technical architecture  
**Problem**: New domain models need Cosmos DB containers with appropriate partition keys for query performance within the stated NFR targets.

**Decision**:

| Container | Partition Key | Models Stored | Rationale |
|---|---|---|---|
| `recovery` | `/incident_id` | `RecoveryEnvironmentTracker` | Recovery indicators are always queried per-incident. Dashboard loads all four environments for one incident (NFR-004: ≤10s). |
| `lessons` | `/incident_id` | `Lesson` | Lessons are captured per-incident/exercise. Exercise lessons use `scenario_run_id` as a synthetic incident reference. |
| `aiims-assignments` | `/incident_id` | `AiimsRoleAssignment` | Role assignments are always queried per-incident for COP display. |
| `evacuation-stages` | `/incident_id` | `EvacuationStage` | Stage tracking is per-incident. Queries retrieve all stages for one evacuation operation. |
| `pprr-contexts` | `/context_reference_id` | `PprrPhaseContext` | Non-incident PPRR phases are queried by region (jurisdiction_id) or scenario. |

All containers reside in the existing `disaster-hub` Cosmos DB account, in Azure Australia East (NFR-015).

**Rationale**: Partition key selection follows the dominant query pattern for each model. All new containers use the same Cosmos DB account to avoid multi-account complexity. The existing account already has 5 containers; adding 5 more is within Cosmos DB's operational norms.

**Alternatives considered**:
1. *Single container with document type discrimination* — Rejected. Different models have different partition key needs. A single container would force a compromise partition key.
2. *Separate Cosmos DB account* — Rejected. No operational benefit; adds infra complexity. The existing account has capacity headroom.
