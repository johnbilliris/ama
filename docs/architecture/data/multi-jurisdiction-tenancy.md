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

This page shows how AMA isolates each Australian jurisdiction as a separate tenant while keeping Cosmos DB partitioning aligned to `/tenant_id`.

![SECTOR-01: Multi-Jurisdiction Tenancy](multi-jurisdiction-tenancy.png)

## Key Elements

- FR-015 coverage for NSW, VIC, QLD, SA, WA, TAS, ACT, NT, and Commonwealth tenant boundaries.
- Lead-agency designation is called out per tenant so operational ownership stays explicit.
- Cosmos DB partition alignment uses `/tenant_id` for jurisdiction-scoped isolation.

## Related Pages

- [SECTOR-02 — Ingestion Data-Flow](ingestion-data-flow.md)
- [SECTOR-03 — Integration-Point Map](integration-point-map.md)
- [SECTOR-04 — Jurisdiction-Filter Behaviour](jurisdiction-filter.md)
- [Architecture known gaps](../known-gaps.md)
