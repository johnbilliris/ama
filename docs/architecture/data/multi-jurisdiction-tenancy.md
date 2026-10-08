---
purpose: Shows multi-jurisdiction tenant isolation boundaries, Cosmos DB partition key alignment, and lead-agency designation for all 8 Australian jurisdictions plus Commonwealth.
personas:
  - Sector
diagrams:
  - SECTOR-01
specs:
  - spec-015
  - spec-022
---

# SECTOR-01 — Multi-Jurisdiction Tenancy

[→ Architecture index](../README.md)

This page documents production isolation boundaries using hierarchical partition metadata: `/scope`, `/jurisdictionId`, and `/dataSourceId`.

![SECTOR-01: Multi-Jurisdiction Tenancy](multi-jurisdiction-tenancy.png)

## Key Elements

- FR-015 coverage for NSW, VIC, QLD, SA, WA, TAS, ACT, NT, and Commonwealth boundaries.
- Scope and jurisdiction are separate controls: `scope=live` for operational traffic and `scope=sim-*` for simulation replay traffic.
- Cosmos partition alignment uses `scope/jurisdictionId/dataSourceId`, with jurisdiction filters on read paths.
- Lead-agency designation is hazard-dependent (for example fire suppression, flood response, or welfare recovery) and is not a static per-state mapping.

## Related Pages

- [SECTOR-02 — Ingestion Data-Flow](ingestion-data-flow.md)
- [SECTOR-03 — Integration-Point Map](integration-point-map.md)
- [SECTOR-04 — Jurisdiction-Filter Behaviour](jurisdiction-filter.md)
- [Architecture known gaps](../known-gaps.md)
