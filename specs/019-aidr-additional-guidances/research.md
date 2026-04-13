# Research: AIDR Additional Guidance Integration

**Feature**: 019-aidr-additional-guidances  
**Date**: 2025-07-19  
**Input**: [spec.md](./spec.md) + [plan.md](./plan.md) Technical Context unknowns

---

## R-001: Planning Agent Architecture

**Decision**: Create a new `planning` agent under `apps/agents/planning/` following the existing `create_app()` factory pattern, with the Planning Agent class, frozen `PlanningConfig` dataclass, request/response models, and plan assembly pipeline.

**Rationale**: The spec explicitly mandates a new planning agent mapping to the AIIMS Planning function (spec Assumptions). The existing agent architecture uses a consistent pattern: `create_app()` factory returning a `FastAPI` app, dependencies stored on `app.state`, `GET /health` endpoint, `__main__.py` entrypoint with uvicorn. This agent consumes handoffs from the incident management system (plan activation during incidents) and produces handoffs to the monitoring agent (M&E framework triggers) and lessons service (post-event review triggers).

**Alternatives considered**:
- *Extend the existing risk assessment agent with planning capabilities*: Rejected because risk assessment has a distinct AIIMS function (Intelligence), and planning maps to the separate AIIMS Planning function. Combining them would violate the AIIMS functional alignment (Constitution §II-A).
- *Create a standalone API service instead of an agent*: Rejected because agents have the `LLMCallMixin` for AI-assisted plan generation and the handoff infrastructure for inter-agent communication. A pure API service would miss these capabilities.

---

## R-002: Emergency Plan State Machine Design

**Decision**: Implement the 7-state lifecycle (`Draft` → `InConsultation` → `UnderReview` → `Endorsed` → `Activated` → `PostEventReview` → `Superseded`) as a validated state transition table in `apps/agents/planning/plan_lifecycle.py`, following the pattern established by `common/pprr_lifecycle.py` for PPRR phase transitions.

**Rationale**: The PPRR lifecycle module (`common/pprr_lifecycle.py`) establishes the project's pattern for state machines: a `VALID_TRANSITIONS` dict mapping current state → list of valid target states, a `validate_transition()` function returning `(bool, error_message)`, and a `build_transition_payload()` function for audit timeline events. The emergency plan lifecycle adds authorization requirements per transition (Planning Officer, Designated Authority, Incident Controller) which extends this pattern with a role check.

**Alternatives considered**:
- *Use a state machine library (e.g., `transitions` package)*: Rejected because the existing codebase uses hand-rolled transition tables for PPRR, and adding a new dependency for a 7-state machine introduces unnecessary complexity. The validation logic is straightforward.
- *Store state transitions in Cosmos DB as event sourcing*: Rejected because the existing architecture uses direct document updates with audit timeline events, not event sourcing. Changing the persistence pattern for one feature would be inconsistent.

---

## R-003: Cosmos DB Container Strategy for New Data

**Decision**: Create 3 new Cosmos DB containers in a new Bicep module `infra/modules/emergency-planning.bicep`:
- `emergency-plans` — partitioned by `region_id` (plans are region-scoped, queried by region for hierarchy views)
- `recovery-programmes` — partitioned by `incident_id` (M&E frameworks are incident-scoped, consistent with `recovery` container pattern)
- `recovery-catalogue` — partitioned by `domain` (immutable reference data browsed by domain, ~5 partitions with well-distributed entries)

**Rationale**: The existing Cosmos containers follow clear partition key strategies: incident-scoped operational data uses `incident_id` (recovery, lessons, aiims-assignments, evacuation-stages), reference/lookup data uses semantic keys (`kind` for seed, `partitionKey` for governance). Emergency plans are region-scoped (a plan covers a geographic area, not an incident), so `region_id` enables efficient queries for "all plans in this region" and hierarchy views. The recovery catalogue uses `domain` because browsing is always domain-first (~5 well-distributed partitions). All containers use `autoscaleSettings.maxThroughput: 1000` consistent with existing non-signal containers.

**Alternatives considered**:
- *Partition emergency plans by `plan_id`*: Rejected because most queries are "find plans for this region" (hierarchy views, incident-triggered plan lookup). Partitioning by `plan_id` would require cross-partition fan-out for all region-scoped queries.
- *Store catalogue data in the existing `seed` container*: Rejected because catalogue data is queried at runtime (not just during seeding) — outcome selection, indicator suggestions, and activity recommendations all hit the catalogue. The `seed` container's `kind` partition key and infrequent access pattern don't match these runtime query needs.
- *Use a single container for all new data*: Rejected because emergency plans (mutable, region-scoped), M&E frameworks (mutable, incident-scoped), and catalogue data (immutable, domain-scoped) have fundamentally different access patterns, partition strategies, and lifecycle requirements.

---

## R-004: AIDR Recovery Catalogue Seeding Strategy

**Decision**: Seed catalogue data as JSON files in `packages/domain/src/domain/seed/recovery-catalogue/` (one file per domain: `overarching.json`, `social.json`, `economic.json`, `built.json`, `natural.json`, plus `evaluation-questions.json`), loaded via the existing `scripts/seed_loader.py` pipeline that is wired as a post-provision hook in `azure.yaml`.

**Rationale**: The existing seeding infrastructure (`scripts/seed_loader.py` → reads JSON from `packages/domain/src/domain/seed/` → upserts into Cosmos DB) is already wired into the deployment pipeline via `azure.yaml` post-provision hooks. Extending this pattern maintains consistency and requires no new tooling. Each domain file contains outcomes with nested activities and indicators, using the hierarchical ID scheme (`aidr:{domain}:{outcome-slug}`, `:act:{index}`, `:ind:{index}`). Catalogue scale: ~61 outcomes, ~200 activities, ~300 indicators (~561 total documents).

**Alternatives considered**:
- *Parse directly from Markdown handbook files at deployment*: Rejected because handbook Markdown is prose-oriented and would require complex, fragile parsing. Pre-structured JSON ensures deterministic seeding with explicit field mapping.
- *Load catalogue at application startup from embedded data*: Rejected because the existing architecture uses Cosmos DB as the source of truth for reference data (see `ScenarioSeedingService` reading from `seed` container). Embedding catalogue data in application code would duplicate the data and create drift risk.
- *Use Azure Cognitive Search for catalogue indexing*: Over-engineered for ~561 documents. Cosmos DB point reads and simple queries are sufficient. If full-text search is needed later, it can be added as a future enhancement.

---

## R-005: M&E Framework Integration with Existing Recovery Tracking

**Decision**: The M&E Framework entity is a new model that wraps and extends the existing `RecoveryEnvironmentTracker`. The M&E Framework holds program-level configuration (selected outcomes, program logic, evaluation domains, standards of success) while the `RecoveryEnvironmentTracker` continues to hold live indicator data. The link is via `incident_id` (both are incident-scoped). The existing `RecoveryIndicator` model gains an optional `catalogue_indicator_id: str | None` field to connect tracker indicators to their AIDR catalogue counterparts.

**Rationale**: Spec 018 established `RecoveryEnvironmentTracker` with 21 indicators across 4 environments. Spec 019 adds the M&E framework layer (program logic, evaluation, outcomes selection) on top without replacing the tracker. This preserves backward compatibility: existing trackers work unchanged, and the M&E framework adds enrichment when configured. The `catalogue_indicator_id` field is optional to support both spec 018-era indicators (no catalogue link) and new AIDR-catalogue-linked indicators.

**Alternatives considered**:
- *Replace `RecoveryEnvironmentTracker` with a new comprehensive model*: Rejected because spec 019 explicitly states it "extends — not replaces — spec 018" (spec Assumptions). Breaking the existing model would invalidate spec 018's tests, contracts, and implementation.
- *Embed M&E configuration directly in `RecoveryEnvironmentTracker`*: Rejected because M&E configuration (program logic, evaluation domains, standards of success) is program-level metadata, not indicator-level data. The tracker is incident-scoped indicator storage; the M&E framework is program-level evaluation configuration. They have different lifecycles and access patterns.

---

## R-006: AI-Assisted Cross-Domain Analysis Architecture

**Decision**: Implement AI analysis as a service within the monitoring agent (`apps/agents/monitoring/indicator_analysis.py`) using the existing `LLMCallMixin` pattern. Analysis is triggered via API endpoints, not automatic background processing. The analysis service:
1. Queries indicator data across domains from the `recovery` Cosmos container
2. Computes statistical correlations using simple trend comparison (not full statistical libraries)
3. Sends structured prompts to Azure OpenAI via `LLMClient` for natural-language interpretation
4. Queries the `recovery-catalogue` container for activity recommendations matching lagging outcomes
5. All AI outputs pass through `ContentSafetyValidator` before presentation (FR-028)

**Rationale**: The existing `LLMCallMixin` in `common/llm_mixin.py` provides a battle-tested pattern: LLM client + content safety + circuit breaker + budget tracking + structured output validation + fallback. Reusing this pattern ensures consistency with how the monitoring agent already handles LLM calls (e.g., `evaluate_escalated_signal`). Statistical correlation is kept simple (trend direction comparison across domains) because NFR-004 requires ≤30s completion for up to 50 indicators — complex statistical methods would exceed this budget.

**Alternatives considered**:
- *Use Azure AI Foundry for analysis*: Considered but deferred. The existing Azure OpenAI integration via `LLMClient` is sufficient for natural-language summarization and recommendation generation. Azure AI Foundry could enhance M&E analysis with custom models trained on recovery data, but this would require new infrastructure provisioning beyond spec scope. Recommended as a future enhancement.
- *Dedicated analysis agent*: Rejected because the analysis capability is an extension of the monitoring agent's existing signal analysis role. Creating a separate agent would fragment the recovery monitoring domain across two agents.
- *Pre-computed correlation tables*: Rejected because recovery data is dynamic and community-specific. Pre-computed correlations would not account for the unique patterns of each disaster's recovery trajectory.

---

## R-007: Emergency Plan Document Assembly

**Decision**: Emergency plan document assembly (`apps/agents/planning/pipeline.py`) collects the 27 AIDR-required plan sections from the plan's Cosmos document and assembles them into a structured JSON response (API interop) and optionally a PDF export (human distribution). The assembly pipeline validates completeness against the AIDR eight planning principles and the 27-element checklist. Assembly target: ≤15 seconds (NFR-001).

**Rationale**: The spec mandates 27 plan elements (FR-002) and lists CSV import for indicators and JSON/PDF export for plans (Assumptions). The communication agent's existing `pipeline.py` pattern shows how to structure a multi-step document assembly pipeline. The planning agent pipeline follows the same pattern: input validation → content assembly → completeness check → output formatting.

**Alternatives considered**:
- *Use a template engine (Jinja2) for plan generation*: Acceptable for PDF generation but unnecessary for JSON output. If PDF export is implemented, Jinja2 templates for plan sections would be appropriate, but the core assembly is JSON-based.
- *AI-generated plan content*: Rejected as the primary mechanism because emergency plans require authoritative content written by human Planning Officers. The AI assists with risk assessment structuring and completeness validation, not content generation. Human-in-the-loop (NN-1) mandates human authorship for plans.

---

## R-008: Plan Hierarchy and Activation Linking

**Decision**: Emergency plans reference parent plans via a `parent_plan_id: str | None` field, forming a hierarchy tree (national → state → regional → local). Plan-to-incident linking uses a `PlanActivationRecord` embedded in the plan document, recording the incident ID, activation timestamp, activating IC, and deactivation timestamp. The plan hierarchy is queried by region (using the `region_id` partition key) and filtered by hierarchy level.

**Rationale**: The spec defines plan hierarchy (FR-005) with national/state/regional/local levels and requires plan activation during incidents (FR-007). Storing the parent reference on the child plan (rather than a separate join table) follows the document-oriented Cosmos DB pattern used throughout the project. The activation record is part of the plan document because a plan's activation history is intrinsic to its lifecycle — querying "was this plan ever activated?" should be a single document read.

**Alternatives considered**:
- *Separate `plan-activations` Cosmos container*: Rejected because activation records are always queried in the context of a specific plan. A separate container would require cross-container joins (not natively supported in Cosmos DB) or denormalization.
- *Bi-directional parent-child references*: Rejected because updating all children when a parent plan changes introduces write amplification. The parent reference on children + a query for "all plans with parent_plan_id = X" is sufficient.

---

## R-009: Evaluation Report Structure

**Decision**: Evaluation reports are generated as structured documents addressing the five M&E key evaluation question (KEQ) domains (governance, community engagement, effectiveness, efficiency, implementation). Each domain section contains: evaluation questions (seeded from AIDR M&E Framework §5.2), findings with evidence references, and recommendations. Reports are stored in the `recovery-programmes` Cosmos container as documents linked to their M&E framework.

**Rationale**: The spec defines KEQ domains as evaluation structuring dimensions (FR-011) and requires evidence-based findings (SC-009). Storing reports in the `recovery-programmes` container (rather than a separate container) is justified because reports are always accessed in the context of a specific recovery program — they share the `incident_id` partition key with their M&E framework.

**Alternatives considered**:
- *Separate evaluation-reports container*: Rejected for the same reason as plan activations — reports are always queried with their program context.
- *Generate reports on-the-fly without persistence*: Rejected because evaluation reports may be reviewed, amended, and disseminated over time. Persistent storage enables version tracking and stakeholder sharing.

---

## R-010: Service Bus Topics for Planning Agent

**Decision**: The Planning Agent consumes handoffs from a new `planning-handoffs` Service Bus queue (following the pattern of `evacuation-handoffs` in the evacuation agent). Handoffs include plan activation requests from the incident management system and post-event review triggers from incident closure. The Planning Agent produces handoffs to `monitoring` (M&E framework initialization when recovery plans exist) and to `lessons_service` (post-event review findings).

**Rationale**: The existing inter-agent communication uses Service Bus queues per agent (`evacuation-handoffs` consumed by `evacuation/agent.py:658-707`) and the `build_handoff()` pattern in `common/handoffs.py`. Adding `planning-handoffs` follows this established pattern. Plan activation is triggered when an incident occurs in a region with an existing plan (User Story 5), requiring async handoff from incident management to the planning agent.

**Alternatives considered**:
- *HTTP-based direct calls between agents*: The communication agent supports this via `POST /process-handoff`, but Service Bus provides built-in retry, dead-letter, and decoupling. The project already uses Service Bus for agent-to-agent communication.
- *Event Grid for plan activation events*: Over-engineered for the current scale. Service Bus queues provide sufficient async messaging with simpler configuration.

---

## R-011: Existing Recovery Indicator Extension (catalogue_indicator_id)

**Decision**: Add `catalogue_indicator_id: str | None = None` to the existing `RecoveryIndicator` model in `packages/domain/src/domain/models/recovery_environment_tracker.py`. This field is optional (defaulting to `None`) for full backward compatibility with spec 018. When set, it contains the hierarchical catalogue ID (e.g., `aidr:social:community-health-levels:ind:1`) linking the tracker indicator to its AIDR catalogue counterpart.

**Rationale**: The spec explicitly defines this extension (FR-015, Terminology §Catalogue indicator vs tracker indicator). Making it optional preserves backward compatibility — all existing spec 018 tests pass unchanged, and existing tracker indicators continue to work without catalogue links. New indicators created through the M&E framework UI will automatically receive catalogue IDs when selected from the AIDR catalogue.

**Alternatives considered**:
- *Create a new indicator model replacing `RecoveryIndicator`*: Rejected because the spec mandates backward compatibility (Assumptions: "extends — not replaces").
- *Store the link in a separate mapping table*: Rejected because the relationship is 1:1 (each tracker indicator links to at most one catalogue indicator) and always accessed when the indicator is loaded. A separate table would require a join for every indicator display.

---

## R-012: Planning Agent Port and Health Endpoint

**Decision**: The Planning Agent runs on port 8085 (next available after monitoring:8080, risk_assessment:8081, communication:8084, evacuation:8082, resource_allocation:8083). It exposes `GET /health` following the established health endpoint pattern: Pydantic response model, `app.state`-backed checks, overall `healthy/degraded/unhealthy` status, with checks for LLM connectivity, Cosmos DB connectivity, and plan assembly pipeline status.

**Rationale**: The existing agents use sequential port assignments in their `__main__.py` files. The health endpoint pattern is consistent across all agents (confirmed in monitoring, communication, risk_assessment, evacuation) and is required by the shared Dockerfile's healthcheck (`http://localhost:$PORT/health`).

**Alternatives considered**:
- *Dynamic port assignment*: Rejected because the shared Dockerfile and Container Apps configuration reference specific ports.
- *Skip health endpoint*: Not an option — all agents require health endpoints per the project's architectural pattern and the Dockerfile healthcheck.

---

## R-013: Telemetry Metrics for New Capabilities

**Decision**: Emit the five telemetry metrics specified in NFR-007 using the existing telemetry patterns (`apps/agents/*/telemetry.py`):
- `emergency_plan_activation_count` — counter, incremented on each plan activation
- `me_framework_completion_rate` — gauge, ratio of M&E frameworks with all required configuration complete
- `recovery_indicator_collection_rate` — gauge, ratio of on-time indicator collections to scheduled collections
- `outcome_achievement_rate` — gauge, ratio of outcomes meeting their standard of success
- `plan_currency_compliance_ratio` — gauge, ratio of plans within their review schedule to total active plans

**Rationale**: Each existing agent has a `telemetry.py` module defining metrics. The new planning agent will have its own telemetry module, and the monitoring agent's telemetry will be extended for M&E metrics. Metrics use the same Azure Monitor / Application Insights integration configured via `APPLICATIONINSIGHTS_CONNECTION_STRING` (see monitoring agent.py lines 15-25).

**Alternatives considered**:
- *Custom metrics backend*: Rejected — the project uses Azure Monitor consistently.
- *Log-based metrics only*: Rejected — structured metrics are needed for alerting and dashboard integration.
