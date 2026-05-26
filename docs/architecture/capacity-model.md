---
purpose: Capacity model documenting production baseline throughput, resource sizing, and SLO linkage for the Disaster Response Coordination Hub.
personas:
  - Technical-Build
  - Technical-Quality
diagrams: []
specs:
  - spec-032
---

# Capacity Model — Disaster Response Coordination Hub

[→ Architecture index](README.md)

> **Migration**: This file is at the repository root of `docs/architecture/`. See known-gaps entry `CAP-MIG-01` for the follow-up migration to `deployment/` or `governance/`.

**Purpose**: published capacity numbers tied to FR-O06 SLOs and FR-A02 partitioning math. Closes spec-032 FR-R03.

## Headline numbers (production baseline)

| Workload | Sustained throughput | Peak throughput | Constraint |
| --- | ---: | ---: | --- |
| Signals ingested | 200 / s | 1,000 / s (15 min) | Event Hubs partition count + ingestion Container Apps replicas |
| Recommendations generated | 30 / s | 200 / s (15 min) | Azure OpenAI TPM quota + agent runtime CPU |
| Public alerts published | 15 / s | 100 / s (5 min) | Communication channels + Content Safety throughput |
| Concurrent operators | 200 | 1,000 (declared incident) | App Service plan + dashboard SignalR fan-out |
| Concurrent declared incidents | 9 (one per AU jurisdiction) | 30 (national emergency) | Cosmos partition headroom |
| Public dashboard viewers | 50 / s | 5,000 / s (broadcast moment) | App Service auto-scale + CDN cache |

## Resource sizing baseline

| Resource | Baseline SKU | Scale-out trigger | Max RU/s or replicas |
| --- | --- | --- | --- |
| Container Apps — apps/api | min 2 / max 10 | HTTP concurrent > 30 | 10 replicas |
| Container Apps — apps/agents/monitoring | min 1 / max 8 | Service Bus queue > 50 | 8 replicas |
| Container Apps — apps/agents/risk_assessment | min 1 / max 6 | Service Bus queue > 30 | 6 replicas |
| Container Apps — apps/agents/communication | min 1 / max 6 | Service Bus queue > 30 | 6 replicas |
| Container Apps — apps/agents/evacuation | min 1 / max 4 | Service Bus queue > 20 | 4 replicas |
| Container Apps — apps/agents/resource_allocation | min 1 / max 4 | Service Bus queue > 20 | 4 replicas |
| Container Apps — apps/ingestion | min 1 / max 5 | Event Hubs unprocessed > 1000 | 5 replicas |
| Cosmos `signals` | 1,000 baseline | 70% util | autoscale max 8,000 |
| Cosmos `recommendations` | 1,000 baseline | 70% util | autoscale max 8,000 |
| Cosmos `audit_segments` | 800 baseline | 70% util | autoscale max 6,000 |
| Cosmos `timeline_events` | 1,500 baseline | 70% util | autoscale max 10,000 |
| Azure OpenAI reasoning | 60 K TPM | n/a | quota request when >75% sustained |
| Azure OpenAI drafting | 200 K TPM | n/a | quota request when >75% sustained |
| AI Search S1 | 1 replica + 1 partition | 70% search-units | scale to S2 if sustained breach |
| App Service plan (web) | P1V3 × 2 | CPU > 70% | autoscale to 6 |
| Application Insights | Pay-as-you-go | n/a | retention split per FR-O01 |

## Per-tenant projections

Per spec-032 FR-A02 + `cosmos-partitioning.md`:

- **Single-jurisdiction peak**: ~4,600 RU/s combined (signals 1,200 + recommendations 800 + timeline events 2,000 + dashboard reads 300 + audit 200 + cross-tenant 100).
- **9-jurisdiction simultaneous peak (Level-3 AIIMS)**: ~41,400 RU/s — comfortably inside the 46,000 RU/s autoscale max provisioned.
- **Headroom margin**: 30% baked into baseline; Cosmos autoscale max-RU caps prevent runaway billing.

## SLO linkage

| SLO | Capacity dependency |
| --- | --- |
| SLO-1 signal ingestion P95 ≤ 60 s | Event Hubs partition count ≥ 4; ingestion replicas ≥ baseline |
| SLO-2 handoff success ≥ 99.5% | Service Bus throughput units; dead-letter queue depth alarms |
| SLO-3 alert publish P95 ≤ 90 s | Content Safety throughput; channel broker rate limits |
| SLO-4 dashboard ≥ 99.9% | App Service plan instances; CDN cache hit ratio |
| SLO-6 LLM cost / incident | Azure OpenAI TPM quotas + budget tracker (Cosmos-backed) |
| SLO-8 RAG retrieval P95 ≤ 400 ms | AI Search S1 replicas; vector index size |

## Review cadence

- After every Level-2 or Level-3 incident.
- Every 6 months as standing item.
- Owner: SRE Engineer + Solution Architect personas.

## Failover capacity

Australia Southeast (paired region): provisioned at 50% of primary baseline; will scale to 100% within 60 minutes of an operator-led failover drill or incident failover (RTO compliance per FR-D01).
