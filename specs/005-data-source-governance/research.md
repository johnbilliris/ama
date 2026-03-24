# Research: Data Source Identification, Constitutional Review, and Governance Assignment

## Decision: Use a centralized governance registry backed by Cosmos DB with Redis cache

**Rationale**: The governance registry serves as the single source of truth for which data sources are approved, how they comply with constitutional principles, and how signals from each source are routed through agents. Centralizing this in Cosmos DB is consistent with the existing operational data backbone (spec 001) and supports low-latency point reads needed for handoff-chain lookups (NFR-001: ≤50ms p95). A Redis cache layer provides agent-side governance data with configurable TTL (NFR-002: default 5 minutes) and graceful degradation when the registry is unreachable (NFR-003).

**Alternatives considered**:

- Distributed governance embedded in agent configuration files: rejected because it creates synchronization challenges, makes auditing difficult, and cannot support dynamic re-review workflows (FR-012, FR-012a).
- Relational database for governance data: rejected because the existing hub already uses Cosmos DB, adding a separate relational store would increase operational complexity without proportional benefit.
- In-memory-only governance data: rejected because it does not survive restarts, cannot support audit trail persistence (FR-013), and fails the durability requirements for compliance records.

## Decision: Deliver the seed catalogue as a JSON file following the existing seed data pattern

**Rationale**: The project already has a `bootstrap_seed_data()` function in `packages/domain/src/domain/seed/bootstrap.py` that loads JSON files for jurisdictions, frameworks, and organisations. Delivering `data_sources_australia.json` in the same directory and extending `bootstrap_seed_data()` maintains consistency, enables programmatic import for tests and SC-001 measurement, and leverages the established pattern without new tooling.

**Alternatives considered**:

- YAML format: rejected because all existing seed files use JSON, and introducing YAML would create format inconsistency requiring a second parser.
- Database migration script instead of seed file: rejected because the seed file allows deterministic bootstrapping, version-controlled content, and automated measurement of SC-001 catalogue completeness.
- Embedded seed data directly in Python code: rejected because it prevents non-developer stakeholders from reviewing and contributing to the catalogue content.

## Decision: Use a two-level categorisation model (kind + sub_category) rather than a flat expanded enum

**Rationale**: This was confirmed in clarification session 2026-03-24. The existing `kind` field on DataSource is already used throughout signal ingestion and agent routing. Adding `sub_category` as a secondary classification preserves backward compatibility and enables granular filtering (FR-003) without breaking existing consumers. The `kind` field retains its 7-value enum; `sub_category` is a constrained string validated at the API boundary.

**Alternatives considered**:

- Single expanded enum with 20+ values: rejected because it breaks backward compatibility with existing `kind` consumers and creates an unwieldy enum that mixes abstraction levels.
- Free-form tags instead of structured sub-category: rejected because tags lack the semantic consistency needed for constitutional assessment criteria and governance dashboard filtering.

## Decision: Map trust tiers to the existing authority_rank integer field

**Rationale**: The spec defines 7 trust tiers (FR-002a) that map directly to `authority_rank` 1–7. The existing DataSource model already has `authority_rank: int`, so the trust tier semantic layer maps cleanly onto the existing field. A new `trust_tier` property provides the human-readable tier name while `authority_rank` provides the numeric ordering for comparison and precedence logic.

**Alternatives considered**:

- Separate trust_tier field alongside authority_rank: rejected because it creates redundancy and risks divergence between two fields encoding the same concept.
- Replace authority_rank entirely: rejected because existing code references authority_rank; a breaking change would affect signal ingestion and agent routing in spec 001.

## Decision: Implement functional-domain precedence with jurisdictional inheritance for contradictory signal resolution

**Rationale**: When two data sources of equal trust tier provide contradictory signals, the system needs a deterministic resolution mechanism. The functional-domain precedence model (confirmed in clarification session 2026-03-24) records which source is authoritative for each hazard type, with national defaults and optional state/territory overrides. This avoids enumerating every source × hazard × jurisdiction combination while providing clear precedence rules.

**Alternatives considered**:

- Always defer to the highest trust tier: rejected because two sources can have the same tier (e.g., two Tier 1 government agencies) and the system needs a domain-specific tiebreaker.
- Always flag conflicts for human resolution without any automated precedence: rejected because it would overwhelm operators during major incidents with high signal volume. Functional-domain precedence resolves the majority of conflicts automatically, with human escalation only when no precedence record exists.

## Decision: Use a grace-period model for compliance-lapsed data sources rather than immediate blocking

**Rationale**: Confirmed in clarification session 2026-03-24. Immediately blocking a previously approved data source that fails re-review could remove critical data feeds during active incidents. The grace-period model (FR-012b: default 72 hours) allows continued operation with visible warnings while governance leads remediate. Governance leads can manually block immediately or extend the grace period based on operational circumstances.

**Alternatives considered**:

- Immediate blocking on re-review failure: rejected because it risks removing safety-critical data during active operations.
- Indefinite grace period with no automatic blocking: rejected because it removes enforcement pressure and could leave non-compliant sources operating permanently.

## Decision: Validate agent names against spec 004 agent catalogue rather than a hardcoded list

**Rationale**: FR-009c requires that agent governance assignments reference only agents that exist in the agent catalogue maintained by spec 004. Validating against the catalogue (rather than a static list in 005) ensures that the governance registry stays synchronized when agents are added, removed, or renamed. The initial implementation validates against the 5 operational agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication) with the validation mechanism designed to consume an extensible catalogue.

**Alternatives considered**:

- Hardcoded agent enum in the governance module: rejected because it would require code changes every time spec 004 modifies the agent catalogue.
- No validation (accept any string as agent name): rejected because it allows typos and references to non-existent agents, creating governance gaps that are hard to detect.

## Decision: Structure constitutional assessments as discrete per-principle records rather than a single assessment document

**Rationale**: Each data source requires assessment against up to 6 constitutional principles. Storing each principle assessment as a separate `ConstitutionalAssessment` record enables independent updates (one principle can be re-assessed without touching others), supports partial compliance profiles (some principles assessed before others), and simplifies querying for dashboard aggregation (e.g., "show all sources non-compliant on Privacy").

**Alternatives considered**:

- Single assessment document per source with embedded principle sections: rejected because updating one principle requires rewriting the entire document, complicating audit trails and concurrent assessments.
- Assessment matrix stored as a flat key-value map: rejected because it loses the structured metadata (assessor, date, conditions) that the spec requires per principle.

## Decision: Expose handoff chain definitions as a structured query API rather than configuration files

**Rationale**: FR-009a requires the governance registry to expose handoff chain definitions in a format agents can query at runtime. An API endpoint returns the handoff chain for a given data source, including target agents, confidence thresholds, and category filters. This is consistent with the existing FastAPI route pattern and supports the Redis cache layer for low-latency lookups. Agent-side consumption of this API is deferred per FR-009b.

**Alternatives considered**:

- Static configuration files distributed to agents: rejected because it requires agent restarts to pick up governance changes and doesn't support the dynamic re-review workflows.
- Event-driven push of governance changes to agents: rejected for the initial implementation because it adds messaging complexity; the pull-based API with caching is simpler and meets the latency requirement. Event-driven updates could be added in a follow-up if cache invalidation latency becomes a concern.

## Decision: Emit structured observability signals using the existing hub monitoring infrastructure

**Rationale**: NFR-005 requires the governance registry to emit query latency, cache hit/miss rate, governance-gap counts, grace-period warnings, and audit-trail write failures. The existing hub uses Azure Monitor, Application Insights, and structured logging. The governance registry will emit these signals through the same channels, using structured log entries and custom metrics rather than introducing a separate observability stack.

**Alternatives considered**:

- Separate monitoring dashboard for governance: rejected because it fragments the operational view and duplicates infrastructure.
- No observability beyond basic logging: rejected because NFR-005 explicitly requires 5 categories of structured signals.
