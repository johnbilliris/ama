---
purpose: Cosmos DB partitioning and RU budget documentation — legacy root copy; forward-authoritative page is deployment/cosmos-partitioning.md.
personas:
  - Technical-Build
diagrams: []
specs:
  - spec-001
  - spec-035
---

# Cosmos DB Tenant Partitioning + RU Budget

[→ Architecture index](README.md)

> **Redirect**: This is a legacy copy. The forward-authoritative page is [`deployment/cosmos-partitioning.md`](deployment/cosmos-partitioning.md). See known-gaps entry `COSM-MIG-01`.

**Purpose**: quantify per-tenant + per-jurisdiction RU/s budgets and partitioning strategy. Closes FR-A02.

## Partitioning strategy

| Container | Partition key | Rationale |
| --- | --- | --- |
| `signals` | `/scope`, `/jurisdictionId`, `/dataSourceId` (hierarchical) | Scope- and jurisdiction-filtered read/write |
| `incidents` | Application-specific; verify against the owning container declaration | Do not infer a tenant partition from the UI scope alone |
| `recommendations` | `/incident_id` | Recommendations cluster around incidents |
| `audit_segments` | `/segment_id` | Even distribution; range queries by `incident_id` secondary |
| `timeline_events` | `/incident_id` | Replay by incident |
| `jurisdiction_policies` | `/jurisdiction_code` | One small doc per jurisdiction |
| `agent_killswitches` | `/agent_id` | Tiny container |
| `llm_budgets` | `/scope` | `scope` ∈ {global, jurisdiction:nsw, …} |
| `eval_cases` | `/dataset_version` | Version-scoped |
| `eval_scorecards` | `/run_id` | Run-scoped |
| `consensus_events` | `/incident_id` | Incident-scoped |

## RU/s budget (production baseline)

Targeted at 9 jurisdictions concurrently active, average incident throughput per jurisdiction.

| Container | Provisioned RU/s | Autoscale max RU/s (FR-R04) | Per-tenant share | Notes |
| --- | ---: | ---: | --- | --- |
| `signals` | 1,000 | 8,000 | ~111 baseline | Bursty during severe weather |
| `incidents` | 400 | 2,000 | ~44 | Low write rate, high read |
| `recommendations` | 1,000 | 8,000 | ~111 | Spikes during multi-agent coordination |
| `audit_segments` | 800 | 6,000 | n/a | Append-only; segment hashing CPU-bound |
| `timeline_events` | 1,500 | 10,000 | ~166 | Highest write rate; partitioned by incident |
| `jurisdiction_policies` | 400 | 1,000 | ~44 | Tiny docs |
| `agent_killswitches` | 400 | 1,000 | n/a | Change-feed source for FR-AG05 |
| `llm_budgets` | 400 | 2,000 | n/a | Counters externalised here (FR-P02) |
| `eval_cases` | 400 | 4,000 | n/a | Reads dominate during eval runs |
| `eval_scorecards` | 400 | 2,000 | n/a | Append-only |
| `consensus_events` | 400 | 2,000 | ~44 | Low rate |
| **Total provisioned** | **~7,300** | **~46,000** | | |

### Headroom margin

30% headroom built into the provisioned baseline. Autoscale max-RU caps prevent runaway billing during incidents.

## Per-tenant projections (peak severe weather event, single jurisdiction)

| Workload | Peak RU/s estimate | How |
| --- | ---: | --- |
| Signal ingestion (BoM+GA+state CAD storms) | 1,200 | 100 signals/s × ~12 RU/write |
| Recommendation generation | 800 | 20 recs/s × ~40 RU/write incl. provenance fields |
| Timeline event burst | 2,000 | 200 events/s × ~10 RU/write |
| Audit segment seal | 200 | 1 seal/min × ~12,000 RU/seal (event_count=100) |
| Operator dashboard reads | 300 | Cached via Redis |
| Cross-tenant read (NEMA) | 100 | Federated query |
| **Single-tenant peak** | **~4,600** | |

Total provisioned (~46k RU/s autoscale) supports **~9 jurisdictions in simultaneous peak**, matching the AIIMS Level 3 (multi-state) coordination scenario.

## Failover scenario

During Australia East → Australia Southeast failover (RPO ≤ 15 min, RTO ≤ 60 min), Cosmos automatic failover preserves partition layout. Provisioned RU/s carries to the paired region.

## Review cadence

Every 6 months OR after any severe weather event that exceeded 70% of autoscale max for any container. Owner: Data Engineer persona.
