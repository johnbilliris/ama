# Quickstart: Governance Dashboard Real Data Integration

**Feature**: 023-dashboard-real-data
**Date**: 2025-07-18

## Overview

This feature replaces ~15 hardcoded stub methods in the governance dashboard with real data computed from seed catalogues and stored records. After implementation, all 6 dashboard views (health score, operational readiness, recovery progress, risk overview, compliance matrix, audit trail) display real data.

## Key Files to Change

| Priority | File | What Changes |
|----------|------|-------------|
| 1 | `packages/domain/src/domain/seed/bootstrap.py` | Add `recovery_catalogue` key to returned dict |
| 2 | `apps/api/app/services/governance_data_service.py` | **NEW** — All real metric computation |
| 3 | `apps/api/app/services/dashboard_aggregation_service.py` | Replace ~15 hardcoded helpers → delegate to `GovernanceDataService` |
| 4 | `apps/api/app/api/routes/governance_dashboard.py` | Inject `SeedService` via `Depends()` |
| 5 | `apps/api/app/services/health_score_service.py` | Minor: adapt inputs if needed |
| 6 | `tests/unit/test_governance_data_service.py` | **NEW** — Test metric computation |
| 7 | `tests/unit/test_dashboard_aggregation.py` | Update assertions for real data |
| 8 | `tests/contract/test_governance_dashboard_contract.py` | Verify backward compatibility |

## Architecture at a Glance

```
Seed Files (JSON)
    ↓ bootstrap_seed_data() [extended with recovery catalogue]
SeedService.load() [lru_cache]
    ↓
GovernanceDataService [NEW - computes real metrics]
    ↓
DashboardAggregationService [existing - orchestrates views]
    ↓
HealthScoreService [existing - algorithm unchanged]
    ↓
13 Route Endpoints [existing - inject SeedService via Depends]
```

## Implementation Order

### Step 1: Extend Seed Bootstrap (< 30 min)

Edit `packages/domain/src/domain/seed/bootstrap.py`:

```python
def bootstrap_seed_data(seed_root: Path) -> dict[str, list[dict[str, object]]]:
    # ... existing 6 keys ...
    
    # NEW: Load recovery catalogue
    recovery_dir = seed_root / "recovery-catalogue"
    recovery_catalogue = {}
    for domain in ["overarching", "social", "economic", "built", "natural"]:
        domain_file = recovery_dir / f"{domain}.json"
        if domain_file.exists():
            recovery_catalogue[domain] = json.loads(domain_file.read_text())
    
    return {
        # ... existing keys ...
        "recovery_catalogue": recovery_catalogue,
    }
```

### Step 2: Create GovernanceDataService (Core work — ~4 hours)

Create `apps/api/app/services/governance_data_service.py`:
- Constructor takes `seed_data: dict` and optional `governance_repo`
- Implement methods for each dashboard domain (see data-model.md)
- Each method follows the three-tier pattern: stored → seed → zero-state
- Pre-index seed data in `__init__` for O(1) lookups

### Step 3: Refactor DashboardAggregationService (~2 hours)

In `apps/api/app/services/dashboard_aggregation_service.py`:
- Add `GovernanceDataService` to constructor
- Replace each `_get_*` / `_build_*` helper with delegation to `GovernanceDataService`
- Keep the public method signatures identical

### Step 4: Wire Dependencies in Routes (~1 hour)

In `apps/api/app/api/routes/governance_dashboard.py`:
- Add FastAPI dependency for seed data loading
- Pass seed data into service construction

### Step 5: Write Tests (~3 hours)

- Unit tests for `GovernanceDataService` with test seed data
- Update integration tests to assert real data values
- Contract tests to verify response structure stability

## Seed Data Quick Reference

| Key | Source File | Count | Key Fields |
|-----|-----------|-------|------------|
| `jurisdictions` | `jurisdictions_australia.json` | 9 | id, name, level |
| `frameworks` | `frameworks_australia.json` | 27 | id, pprr_phases, hazard_types |
| `organisations` | `organisations_australia.json` | 49 | id, aiims_functions, workforce_type, primary_capabilities |
| `data_sources` | `data_sources_australia.json` | 46 | id, status, trust_tier |
| `framework_assignments` | `framework_assignments_australia.json` | 123 | framework_id, jurisdiction_id |
| `recovery_catalogue` | `recovery-catalogue/*.json` | 5 domains | domain, outcomes, activities, indicators |

## Testing Approach

```bash
# Run unit tests
pytest tests/unit/test_governance_data_service.py -v

# Run existing dashboard tests (must still pass)
pytest tests/unit/test_dashboard_aggregation.py -v

# Run contract tests (backward compatibility)
pytest tests/contract/test_governance_dashboard.py -v
pytest tests/contract/test_governance_dashboard_contract.py -v

# Run integration tests
pytest tests/integration/test_governance_dashboard_api.py -v
```

## Performance Verification

All endpoints must respond within 500ms at p95. Verify with:
1. Seed data is loaded once (check `lru_cache` hit in logs)
2. Metric computation adds <5ms per endpoint
3. No N+1 query patterns in GovernanceDataService

## Common Pitfalls

1. **Don't modify `HealthScoreService.calculate()` algorithm** — only change the inputs passed to it
2. **Don't add to `ConstitutionalPrinciple` enum** — the 6 values cover existing assessments; unmapped gates are inferred
3. **Don't create audit entries during seed loading** — empty audit trail is correct initial state
4. **Don't change response model field names** — additive optional fields only
5. **Recovery domains increased from 4→5** — the `overarching` domain was always in the Literal type but never populated; `max_length=5` already permits this
6. **`lru_cache` key is `seed_root` string** — ensure consistent path resolution to avoid cache misses
