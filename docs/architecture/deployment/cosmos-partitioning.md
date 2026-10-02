---
purpose: Cosmos DB partitioning scheme showing partition key strategy, document routing, and multi-jurisdiction isolation alignment. This is the forward-authoritative page for DEPLOY-03.
personas:
  - Technical-Build
diagrams:
  - DEPLOY-03
specs:
  - spec-001
  - spec-035
---

# DEPLOY-03 — Cosmos DB Partitioning Scheme

> **Note**: The root-level `../cosmos-partitioning.md` is a legacy copy; this page is authoritative. See known-gaps COSM-MIG-01.

[→ Architecture index](../README.md)

<!-- spec-cross-ref: spec-001 -->
<!-- spec-cross-ref: spec-035 -->

![DEPLOY-03 — Cosmos DB Partitioning Scheme](./cosmos-partitioning.png)

## Partition keys

| Container set | Partition key | Reason |
| --- | --- | --- |
| `signals` | `/scope`, `/jurisdictionId`, `/dataSourceId` (hierarchical) | Separates live and simulation workloads while preserving jurisdiction and source-level isolation |
| `recommendations`, `timeline_events` | `/incident_id` | Optimises incident-scoped replay, retrieval, and operator review |
| `audit_segments` | `/segment_id` | Balances append-only evidence segments while preserving audit sealing workflows |

## Routing model

Signals are persisted with deterministic partition metadata: `scope` (`live` or `sim-*`), `jurisdictionId`, and `dataSourceId`, then composed into partition routing for the `signals` container. Disaster-event and audit records continue using their workload-specific partitioning to preserve replay and audit traversal performance.
