# Quickstart: Data Source Governance

## Purpose

Validate the governance registry design through a development-ready setup, failing tests first, and a scenario walkthrough that exercises data source registration, constitutional assessment, agent assignment, handoff chain validation, grace-period compliance lapsing, and consolidated dashboard filtering.

## Prerequisites

- Python 3.12
- Node.js 22 and pnpm
- Azure Developer CLI or equivalent Azure deployment tooling
- Access to Azure resources in Australian regions only
- Existing hub environment from spec 001 (API, agents, web, packages/domain)
- Test credentials for Entra ID-backed development tenants

## Planned workspace shape

```text
apps/api/app/api/data_sources.py
apps/api/app/api/governance.py
apps/api/app/services/governance_registry.py
apps/api/app/services/governance_cache.py
apps/api/app/repositories/governance_repository.py
apps/api/app/validators/governance_validators.py
apps/web/src/app/governance/
packages/domain/src/domain/models/constitutional_assessment.py
packages/domain/src/domain/models/agent_governance.py
packages/domain/src/domain/models/handoff_chain.py
packages/domain/src/domain/models/governance_audit.py
packages/domain/src/domain/seed/data_sources_australia.json
tests/contract/test_data_source_registry.py
tests/contract/test_constitutional_compliance.py
tests/contract/test_governance_assignment.py
tests/contract/test_governance_dashboard.py
tests/integration/test_governance_grace_period.py
tests/integration/test_governance_rereview.py
tests/integration/test_governance_cache.py
tests/e2e/test_governance_dashboard.spec.ts
```

## Setup sequence

1. Extend `packages/domain/src/domain/models/data_source.py` with governance fields: `sub_category`, `trust_tier`, `provider`, `collection_method`, `data_type`, `update_frequency`, `geographic_coverage`, `compliance_status`, `governance_status`, `grace_period_start`, `grace_period_end`.
2. Create new domain model files for `ConstitutionalAssessment`, `AgentGovernanceAssignment`, `HandoffChainDefinition`, `FunctionalDomainPrecedence`, and `GovernanceAuditEntry`.
3. Add `data_sources_australia.json` seed file to `packages/domain/src/domain/seed/` and extend `bootstrap.py` with a `data_sources` key.
4. Create governance API routes (`data_sources.py`, `governance.py`) and register them with the FastAPI application.
5. Create governance services (`governance_registry.py`, `governance_cache.py`) and repository (`governance_repository.py`).
6. Create governance validators (`governance_validators.py`) for handoff chain continuity and agent catalogue validation.
7. Add governance dashboard pages and components to the web application under `/governance`.
8. Configure `.env` with any additional settings for governance cache TTL.

## Test-first validation flow

### Phase A: Data source registry (FR-001–003)

1. Write and run failing contract tests for:
   - Listing data sources with filtering by kind, sub_category, trust_tier, compliance_status, governance_status
   - Registering a new data source with full metadata
   - Deactivating a data source and verifying history retention
   - Seed catalogue loading and SC-001 measurement (at least 90% of enumerated sources present)
2. Implement the minimum code to make these tests pass.

### Phase B: Constitutional compliance (FR-004–006)

1. Write and run failing contract tests for:
   - Creating a constitutional assessment for each of the 6 principles
   - Validating that `conditions` and `gaps` are required for partially_compliant and non_compliant statuses
   - Preventing non-compliant sources from active ingestion (FR-006)
   - Presenting principle-specific assessment criteria (FR-004a)
   - Superseding assessments and maintaining `is_current` integrity
2. Implement the minimum code to make these tests pass.

### Phase C: Agent assignment and handoff chains (FR-007–010)

1. Write and run failing contract tests for:
   - Assigning agents to data sources with primary/secondary roles
   - Validating agent names against the agent catalogue (FR-009c)
   - Defining handoff chains with step ordering and chain continuity
   - Rejecting invalid handoff chains (broken continuity, unknown agents, out-of-range thresholds)
   - Blocking assignments for non-compliant sources (FR-006 interaction)
   - Supporting shared-responsibility sources with multiple agents (FR-010)
2. Implement the minimum code to make these tests pass.

### Phase D: Governance dashboard (FR-011, FR-014)

1. Write and run failing contract tests for:
   - Dashboard summary counts (total, compliant, non-compliant, assigned, unassigned, etc.)
   - Filtering by compliance_status, governance_status, kind, agent_name, geographic_coverage
   - Flagging governance gaps (unassessed or unassigned sources)
   - Re-review pending count (FR-012a)
2. Implement the minimum code to make these tests pass.

### Phase E: Re-review and grace period (FR-012, FR-012a, FR-012b)

1. Write and run failing integration tests for:
   - Triggering re-review when a data source's characteristics change
   - Triggering re-review when constitution is amended (all assessments flagged)
   - Grace period lifecycle: compliance-lapsed → warning → auto-block after 72 hours
   - Governance lead override: immediate block or extend grace period
   - Source continues operating during grace period
2. Implement the minimum code to make these tests pass.

### Phase F: Governance cache and performance (NFR-001–003)

1. Write and run failing integration tests for:
   - Handoff-chain lookup returns within ≤50ms p95
   - Cache hit/miss tracking and TTL expiry
   - Fallback to cached data when registry is unreachable
   - Safe default routing when no cache is available (NFR-003)
2. Implement the minimum code to make these tests pass.

### Phase G: Audit trail (FR-013)

1. Write and run failing contract tests for:
   - Audit entries created for every governance action (registration, assessment, approval, rejection, assignment, handoff definition, re-review, grace period operations)
   - Audit entries are immutable (no update or delete)
   - Audit trail queryable by data source, action type, and date range
2. Verify audit trail completeness by replaying the audit log against registry state (SC-006).

### Phase H: Governance dashboard e2e (US-4)

1. Write and run failing Playwright tests for:
   - Dashboard loads with summary counts and data source list
   - Filtering updates the displayed sources
   - Governance gaps are visually flagged
   - Drill-down to compliance and assignment views works correctly
2. Implement the minimum frontend code to make these tests pass.

## Scenario rehearsal

1. **Seed catalogue bootstrap**: Load `data_sources_australia.json` and verify all expected sources appear in the registry with correct metadata.
2. **Constitutional assessment workflow**: Select Bureau of Meteorology warnings, perform constitutional assessment against all 6 principles, and verify the compliance profile is fully populated.
3. **Agent assignment workflow**: Assign Monitoring Agent as primary for BoM warnings, define handoff chain (Monitoring → Risk Assessment → Evacuation), and verify chain validation passes.
4. **Shared responsibility source**: Assign both Monitoring (primary) and Risk Assessment (secondary) to BoM warnings, verify both assignments are recorded without ambiguity.
5. **Non-compliant source blocking**: Register a hypothetical social media source, mark it non-compliant on Privacy, and verify the system blocks agent assignment until remediation.
6. **Grace period scenario**: Simulate a re-review failure on a previously approved source, verify the source enters compliance-lapsed state with a 72-hour grace period, and verify the dashboard displays the warning.
7. **Governance gap identification**: Open the governance dashboard, verify sources without assessments or assignments are flagged, and confirm the summary counts are accurate.
8. **Functional-domain precedence**: Set BoM as authoritative for weather nationally, set NSW RFS as authoritative for fire in NSW, verify conflict resolution uses the correct precedence chain.

## Acceptance checks

- Seed catalogue loads with at least 90% of enumerated Australian data sources (SC-001).
- Every registered source has a completed constitutional compliance assessment (SC-002).
- Every approved source has an agent assignment and handoff chain (SC-003).
- Full governance workflow (register → assess → assign → define handoff) completes in under 30 minutes (SC-004).
- Governance dashboard accurately reflects current state; users identify gaps within 2 minutes (SC-005).
- All governance actions appear in the audit trail with no gaps (SC-006).
- Handoff-chain lookup latency ≤50ms p95 (NFR-001).
- Governance dashboard loads in under 2 seconds.
