# Spec 005 Staging Lookup Latency and Outage Scaffold

## Status

- State: UNVERIFIED
- Purpose: capture authorized staging evidence for AUD-026 without using production fault injection

## Required Opt-In Gate

- `AMA_STAGING_GOVERNANCE=1`
- Required config:
  - `AMA_STAGING_GOVERNANCE_BASE_URL`
  - `AMA_STAGING_GOVERNANCE_REGION` (must start with `australia`)
  - `AMA_STAGING_GOVERNANCE_ENV` (must be `staging`)
  - `AMA_STAGING_GOVERNANCE_WARM_SOURCE_IDS`
  - `AMA_STAGING_GOVERNANCE_COLD_SOURCE_IDS`
- Minimum load: `AMA_STAGING_GOVERNANCE_LOOKUP_TOTAL >= 1000`

## Command

```bash
python -m pytest tests/integration/test_governance_cache.py -k "lookup_latency or registry_outage" -q
```

## Evidence Outputs

- `specs/005-data-source-governance/evidence/lookup-latency-samples.staging.json`
- `specs/005-data-source-governance/evidence/readiness-snapshot.generated.json`
- `specs/005-data-source-governance/evidence/readiness-replay.generated.json`

## Explicit Blockers

- Redis Basic C0 availability posture remains a cost/architecture approval blocker for NFR availability claims.
- SME panel, usability denominator, and replay sign-off remain human-gated evidence outside automated checks.
