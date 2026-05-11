---
purpose: Maps all external integration points showing data format, ingestion endpoint, and consuming agent for each external system (BoM, GA, NEMA, state agencies).
personas:
  - Sector
diagrams:
  - SECTOR-03
specs:
  - spec-014
---

# SECTOR-03 — Integration-Point Map

[→ Architecture index](../README.md)

This page maps each named external system to its incoming data format, its AMA ingestion endpoint, and the agent that consumes the resulting signal.

![SECTOR-03: Integration-Point Map](integration-point-map.png)

## Key Elements

- FR-014 coverage names BoM, GA, NEMA, and state agency feeds explicitly.
- Each source identifies its payload format before it reaches the matching ingestion endpoint.
- Consuming agents are shown so reviewers can trace operational ownership end to end.

## Related Pages

- [SECTOR-01 — Multi-Jurisdiction Tenancy](multi-jurisdiction-tenancy.md)
- [SECTOR-02 — Ingestion Data-Flow](ingestion-data-flow.md)
- [SECTOR-04 — Jurisdiction-Filter Behaviour](jurisdiction-filter.md)
- [Architecture known gaps](../known-gaps.md)
