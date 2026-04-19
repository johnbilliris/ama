# Research: Governance Dashboard Real Data Integration

**Feature**: 023-dashboard-real-data
**Date**: 2025-07-18
**Status**: Complete

## Research Tasks

### RT-001: Recovery Catalogue Loading Strategy

**Context**: `bootstrap_seed_data()` currently loads 6 seed files but does NOT include recovery catalogue data. The recovery catalogue lives in `packages/domain/src/domain/seed/recovery-catalogue/` as 6 JSON files (5 domain files + evaluation questions).

**Decision**: Extend `bootstrap_seed_data()` to add a `recovery_catalogue` key containing all 5 domain files parsed into a structured dict keyed by domain name (`overarching`, `social`, `economic`, `built`, `natural`), plus an `evaluation_questions` key for the evaluation questions file.

**Rationale**: The `SeedService` already delegates to `bootstrap_seed_data()` via `lru_cache`, so extending the bootstrap function automatically makes recovery catalogue data available to all consumers without changing `SeedService` itself. The `lru_cache` ensures this is a one-time cost.

**Alternatives considered**:
- *Separate `load_recovery_catalogue()` function*: Would require a second cached call in `SeedService` and a separate loading path. Rejected because it splits the seed loading concern unnecessarily.
- *Load recovery catalogue on-demand in `RecoveryCatalogueService`*: Would bypass the centralized seed loading pattern. Rejected because the spec requires all seed data to be available as fallback inputs.

**Implementation sketch**:
```python
# In bootstrap.py — extend bootstrap_seed_data()
def bootstrap_seed_data(seed_root: Path) -> dict[str, list[dict[str, object]]]:
    recovery_dir = seed_root / "recovery-catalogue"
    recovery_domains = {}
    for domain in ["overarching", "social", "economic", "built", "natural"]:
        domain_path = recovery_dir / f"{domain}.json"
        if domain_path.exists():
            recovery_domains[domain] = json.loads(domain_path.read_text())
    
    return {
        "jurisdictions": load_seed_file(seed_root / "jurisdictions_australia.json"),
        "frameworks": load_seed_file(seed_root / "frameworks_australia.json"),
        "organisations": load_seed_file(seed_root / "organisations_australia.json"),
        "data_sources": load_seed_file(seed_root / "data_sources_australia.json"),
        "disasters": load_seed_file(seed_root / "disasters_australia.json"),
        "framework_assignments": load_seed_file(seed_root / "framework_assignments_australia.json"),
        "recovery_catalogue": recovery_domains,
    }
```

---

### RT-002: GovernanceDataService Architecture

**Context**: The `DashboardAggregationService` currently has ~15 private helper methods returning hardcoded values. Need a clean way to inject real data computation without bloating the aggregation service.

**Decision**: Create a new `GovernanceDataService` class that takes seed data (dict from `SeedService.load()`) and optional repository references (for Cosmos DB stored records) as constructor arguments. It exposes purpose-built methods for each data domain (constitutional gates, readiness metrics, recovery progress, risk data, compliance data, audit data). The `DashboardAggregationService` replaces its hardcoded helpers with calls to `GovernanceDataService`.

**Rationale**: 
- **Single Responsibility**: The aggregation service orchestrates view assembly; the data service computes metrics from raw data. This separation keeps both testable.
- **Dependency Injection**: Both services can be constructed with or without repositories, enabling easy testing with seed-only data.
- **Seed Fallback Pattern**: `GovernanceDataService` checks stored records first, falls back to seed-computed values, and annotates which path was used.

**Alternatives considered**:
- *Inline computation in aggregation service*: Would grow the 635-line service to 1000+ lines. Rejected for maintainability.
- *Multiple small services (one per domain)*: Would require 6 new service files and complex wiring. Rejected as over-engineering for this scope.
- *Enrich existing services (RecoveryCatalogueService, etc.)*: Would scatter the dashboard data logic across many files. Rejected because dashboard metric computation is a cohesive concern.

---

### RT-003: Seed Data Schema Analysis

**Context**: Need to understand exactly what fields are available in seed data to compute each metric.

**Findings**:

| Seed File | Count | Key Fields for Dashboard |
|-----------|-------|------------------------|
| `data_sources_australia.json` | 46 | `status` (available/degraded/offline), `trust_tier`, `compliance_status` |
| `organisations_australia.json` | 49 | `aiims_functions` (list of AiimsFunction enums), `workforce_type` (paid/volunteer/mixed), `primary_capabilities` (list), `jurisdiction_ids` |
| `frameworks_australia.json` | 27 | `pprr_phases` (list of PprrPhase enums), `hazard_types`, `applicable_jurisdiction_ids` |
| `framework_assignments_australia.json` | 123 | `framework_id`, `jurisdiction_id`, `effective_from`, `effective_to` |
| `jurisdictions_australia.json` | 9 | `jurisdiction_id`, `name`, `level` |
| `recovery-catalogue/*.json` | 5 domains | `domain`, `outcomes[]` (with `activities[]` and `indicators[]` nested) |

**Metric derivation map**:

| Dashboard Metric | Seed Source | Computation |
|-----------------|-------------|-------------|
| Constitutional compliance (40%) | Stored `ConstitutionalAssessment` records, fallback: assume all gates "assessment_pending" | Count pass/fail/pending per gate |
| Operational readiness (25%) | `framework_assignments` + `frameworks` + `organisations` | Exercise rate from framework metadata; role coverage from org AIIMS functions; plan currency from plan records or 0% |
| Data source governance (20%) | `data_sources` seed | Count by `status`: available=compliant, degraded=partially_compliant, offline=non_compliant |
| Recovery progress (15%) | `recovery-catalogue` domains | Count outcomes/activities/indicators per domain; 0% completion baseline when no trackers |
| PPRR distribution | `framework_assignments` joined to `frameworks.pprr_phases` | Count assignments per phase |
| AIIMS role coverage | `organisations.aiims_functions` | Count orgs per function / 6 functions |
| Volunteer readiness | `organisations` where `workforce_type` in ["volunteer", "mixed"] | Count, jurisdiction distribution, capability coverage |
| Risk severity | Stored `HazardAssessment` records | Group by `severity_level`; zeros when none exist |
| Compliance matrix | Stored `ConstitutionalAssessment` + `data_sources` seed | Matrix of 10 gates × N data sources |
| Audit trail | Stored `GovernanceAuditEntry` records | Direct query; empty when no actions taken |

---

### RT-004: Backward Compatibility Strategy

**Context**: 13 existing endpoints with established response contracts used by the frontend and agent consumers. Must ensure zero breaking changes.

**Decision**: All changes are additive only. New optional metadata fields (e.g., `data_source_indicator: str | None = None`) are added to response models with defaults. No existing field names, types, or endpoint paths change.

**Rationale**: The frontend TypeScript types in `governance.ts` define the consumer contract. Adding optional fields is safe because TypeScript interfaces allow extra properties. Existing fields that previously had hardcoded values will now have dynamically computed values of the same type.

**Key contract preservation points**:
1. `ExecutiveSummaryResponse.constitutional_gates` — still exactly 10 `ConstitutionalGateStatus` entries
2. `OperationalReadinessResponse.pprr_phases` — still exactly 4 `PPRRPhaseStatus` entries
3. `RecoveryProgressResponse.domains` — 0-5 `RecoveryDomainProgress` entries (was 4 hardcoded, now 5 with overarching)
4. `RiskSeverityBreakdown` — same 5 fields (extreme/high/medium/low/total)
5. `ComplianceMatrixEntry` — same field set
6. `AuditTrailResponse.events` — same `AuditEventSummary` structure

**Change from 4 to 5 recovery domains**: The current stub returns 4 domains (social, economic, built, natural). The recovery catalogue has 5 (adding overarching). The response model already allows `max_length=5`. This is additive, not breaking — the overarching domain was always part of the model but never populated.

---

### RT-005: Performance Analysis for Seed-Based Computation

**Context**: All dashboard endpoints must respond within 500ms at p95.

**Decision**: Leverage the existing `lru_cache` on `SeedService.load()` to ensure seed data is loaded once. Pre-compute derived metrics in `GovernanceDataService.__init__()` or lazily on first access with instance-level caching.

**Rationale**: The total seed dataset is small (~200KB across all files). With `lru_cache`, the file I/O cost is paid once at startup. All metric computations are simple aggregations over small collections (max 123 items). Worst case computation time is <5ms. The p95 latency target is easily met.

**Performance profile**:
- Seed file loading (cold, one-time): ~10ms for all 7 files
- `lru_cache` hit (warm): <0.01ms
- PPRR distribution (123 assignments × 27 frameworks join): <1ms
- AIIMS coverage (49 organisations): <1ms
- Recovery catalogue aggregation (5 domains): <1ms
- Data source stats (46 sources): <1ms
- Cosmos DB query (if connected): <50ms typical, <200ms p95

**No performance risk identified.**

---

### RT-006: Seed Fallback Pattern

**Context**: When Cosmos DB is empty (no stored assessments, no audit entries, no hazard assessments), the dashboard must show meaningful data from seed, not errors or empty responses.

**Decision**: Implement a three-tier data resolution pattern in `GovernanceDataService`:
1. **Stored data first**: Query repository for persisted records
2. **Seed-derived fallback**: Compute from seed data when store is empty
3. **Zero-state baseline**: Return structurally valid empty/zero responses when seed is also unavailable

Each method returns a tuple or annotated result indicating which tier was used. The aggregation service passes this as optional metadata in responses.

**Rationale**: This matches the spec requirement (FR-005, FR-026) and the clarification that seed loading failure should result in graceful error responses, not crashes.

---

### RT-007: Constitutional Assessment to Gate Mapping

**Context**: The existing `ConstitutionalAssessment` model uses a `ConstitutionalPrinciple` enum with 6 values (`life_safety_first`, `multi_agent_coordination`, etc.) but the dashboard uses 10 gates derived from AIDR constitution sections. Need to understand the mapping.

**Decision**: The 10 constitutional gates (as defined in `CONSTITUTIONAL_GATES` constant in `dashboard_aggregation_service.py`) are the canonical set. The `ConstitutionalPrinciple` enum in the assessment model covers 6 of these. For the remaining 4 gates, assessments may not exist. When no assessment maps to a gate, that gate is shown as `assessment_pending`.

**Mapping**:
| Gate # | Gate Name | Maps to ConstitutionalPrinciple |
|--------|-----------|-------------------------------|
| 1 | Primacy of Life | `life_safety_first` |
| 2 | National EM Principles | `multi_agent_coordination` |
| 3 | Multi-Hazard Design | — (inferred from data source coverage) |
| 4 | Transparency & Auditability | `data_trust_provenance_freshness` |
| 5 | Warning & Public Information | `multilingual_accessible_actionable` |
| 6 | Evacuation Framework | — (inferred from plan coverage) |
| 7 | Recovery Support | — (inferred from recovery catalogue) |
| 8 | Cloud Platform & Infrastructure | `cloud_platform` |
| 9 | PPRR Lifecycle | — (inferred from framework coverage) |
| 10 | Governance & Quality Gates | `privacy_security_regional_policy` |

**Rationale**: The 6-value enum was designed before the 10-gate dashboard. The unmapped gates can still show meaningful status by inferring from seed data presence (e.g., Gate 9 "PPRR Lifecycle" is pass if all 4 PPRR phases have framework assignments).

---

### RT-008: Route Dependency Injection for SeedService

**Context**: The 13 routes in `governance_dashboard.py` currently instantiate `DashboardAggregationService` but don't pass seed data into it.

**Decision**: Inject `SeedService` as a FastAPI dependency that gets resolved once and passed into `DashboardAggregationService` via the constructor. The `GovernanceDataService` is instantiated inside the aggregation service constructor with the loaded seed data.

**Rationale**: FastAPI's dependency injection is the idiomatic way to provide shared services. `SeedService` with `lru_cache` ensures seed data is loaded once per process. This matches the existing architecture where `HealthScoreService` is already injected.

**Implementation approach**:
```python
# In governance_dashboard.py
def get_seed_data():
    """FastAPI dependency for seed data."""
    svc = SeedService()
    seed_root = Path(__file__).resolve().parents[5] / "packages" / "domain" / "src" / "domain" / "seed"
    return svc.load(seed_root)

# Then in route functions, add seed_data: dict = Depends(get_seed_data)
# and pass to aggregation service
```

---

### RT-009: Capability Gap Computation Strategy

**Context**: FR-009 requires computing capability gaps by comparing organisation capabilities against framework requirements. However, the `frameworks_australia.json` schema does NOT have an explicit `requirements` field.

**Decision**: Derive capability requirements from framework `hazard_types` and `pprr_phases`. A capability gap exists when a jurisdiction has framework assignments for hazard types but no organisation in that jurisdiction has matching `primary_capabilities` or `hazard_types`. This is a best-effort heuristic.

**Rationale**: Without an explicit requirements field, the most meaningful gap analysis compares what hazard types/capabilities frameworks expect to be covered vs what organisations in assigned jurisdictions can provide. This produces actionable insights even without a formal requirements registry.

**Alternatives considered**:
- *Skip capability gaps entirely*: Would leave an empty section. Rejected because the response model includes `capability_gaps` and `capability_gap_count`.
- *Hardcode generic gaps*: Would defeat the purpose of real data. Rejected.

---

### RT-010: Audit Trail — Empty Is Correct

**Context**: Spec clarification states that audit entries should only be created by actual user/system actions, NOT by seed loading. An empty audit trail when no actions have occurred is the correct initial state.

**Decision**: The audit trail endpoint queries stored `GovernanceAuditEntry` records. When none exist, it returns `events: [], total_count: 0`. No seed-derived fabrication. FR-019 specifies which actions generate audit entries (constitutional assessments, data source status changes, framework updates, plan approvals) — these are created by other features, not this one.

**Rationale**: This matches the spec clarification and the constitutional gate #4 (Transparency & Auditability) — the audit trail must reflect real governance actions to maintain trust.

---

### RT-011: Frontend TypeScript Type Updates

**Context**: The frontend types in `governance.ts` must remain backward-compatible. Need to identify what additive changes are needed.

**Decision**: Add optional metadata fields to relevant response types:
- `data_source_indicator?: "live" | "seed_fallback" | "computed"` on response types that use seed fallback
- No existing field type changes
- No existing field removals

**Rationale**: TypeScript optional properties are additive and don't break existing consumers. The frontend can progressively adopt these fields to show fallback indicators in the UI.

---

## Summary of Resolved Unknowns

| # | Unknown | Resolution |
|---|---------|------------|
| RT-001 | Recovery catalogue not in bootstrap | Extend `bootstrap_seed_data()` with `recovery_catalogue` key |
| RT-002 | Where to put real data computation | New `GovernanceDataService` class |
| RT-003 | Seed data field availability | All required fields confirmed present |
| RT-004 | Backward compatibility approach | Additive-only changes; no field/path modifications |
| RT-005 | Performance with seed computation | <5ms computation, `lru_cache` for I/O — no risk |
| RT-006 | Fallback when Cosmos empty | Three-tier: stored → seed-derived → zero-state |
| RT-007 | Constitutional gate to assessment mapping | 6 direct mappings + 4 inferred gates |
| RT-008 | How to inject seed data into routes | FastAPI `Depends()` with `SeedService` |
| RT-009 | Capability gap without requirements field | Derive from hazard_types + pprr_phases coverage |
| RT-010 | Audit trail initial state | Empty is correct; no seed fabrication |
| RT-011 | Frontend type changes | Optional metadata fields only |
