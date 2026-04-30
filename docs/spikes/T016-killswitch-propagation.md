# Spike T016 — Kill-Switch Push-Based Propagation Validation

**Owner**: spec-032 Stream-0
**Goal**: Validate that the proposed push-based kill-switch propagation can meet the FR-AG05 SLO of **P99 ≤ 30 seconds** end-to-end (operator toggle → all agent processes drain in-flight handoffs).
**Status**: Design complete; prototype + measurement deferred to implementation task T704–T706.

## Design

```
[Operator UI] --POST /agents/{id}/killswitch--> [API]
                                                  |
                                                  v
                                        [Cosmos: agent_killswitches/{id}]
                                                  |
                                       (Cosmos change feed processor)
                                                  |
                                                  v
                                        [Service Bus topic: killswitch-events]
                                                  |
                                       ┌──────────┼──────────┐
                                       v          v          v
                              [agent A watcher] [B] [C] ...   (subscribers)
                                       |
                                       v
                            (in-flight handoff drain ≤ 5 s)
                                       |
                                       v
                           [degraded_mode = true; template fallback]
```

## Latency budget (target P99)

| Hop | Target P99 | Notes |
|---|---:|---|
| Client POST → API write to Cosmos | 500 ms | Single-region write, eventual consistency `Session` |
| Cosmos change-feed processor pickup | 5 s | Cosmos change feed default polling 5 s; configurable |
| Service Bus topic publish | 200 ms | One topic per env; agent subscribers |
| Service Bus → agent subscriber receive | 1 s | Long-polling subscription, prefetch 1 |
| Agent in-flight handoff drain | 5 s | `handoff_timeout_ms` honoured |
| `agent.killswitch.lag_seconds` heartbeat emit | 100 ms | Single App Insights telemetry call |
| **Sum** | **≈ 12 s** | Generous headroom under 30 s SLO |

**Note**: change-feed pickup is the dominant variable. If the prototype shows P99 > 10 s here, an alternative is to push directly from the API to Service Bus (skip change feed) — change feed is only a redundancy/audit copy.

## Risks

| Risk | Mitigation |
|---|---|
| Service Bus topic outage | Fall back to direct Cosmos polling (degraded but functional); raise warning customMetric. |
| Subscriber deadletter buildup | Per-subscription DLQ + alert; re-drive on recovery. |
| Agent in-flight drain >> 5 s under load | Hard cap drain at 5 s; force-cancel outstanding LLM calls; record `killswitch.drain_timeout_total` counter. |
| Multi-region: change-feed lag during AU Southeast failover | DR runbook (T809) covers; SLO temporarily widens during declared failover. |

## Acceptance for the spike (deferred to T704)

A 100-toggle benchmark in the dev environment must produce:

- P50 ≤ 5 s
- P99 ≤ 30 s
- 0 missed toggles (every agent state visible in `/api/agents/{id}/status` post-toggle)

If P99 fails, the SLO MUST be widened in the spec (rather than silently missed) and the FR-AG05 wording renegotiated.

## Implementation pointers (carried into T704–T706)

- Use `azure-cosmos` change feed processor (lease container `agent_killswitches_lease`).
- Service Bus topic: `killswitch-events`, one subscription per agent process (filter on `agent_id` if multi-tenant).
- Agent watcher: single asyncio task in the agent process bootstrap; cancels on SIGTERM.
- Heartbeat: emit `agent.killswitch.lag_seconds` from the **agent watcher** the moment it applies the toggle, so the histogram captures the producer-to-consumer wall-clock.

---
*Spike author: SRE Engineer + AI/ML Engineer personas. Date: 2026-04-30.*
