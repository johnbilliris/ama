# Contract: SLI Thresholds, Measurement Queries, and Alert Routing

**Feature**: 036 — Simulation Telemetry-Injection Agent (amendment cycle)
**Spec FRs**: FR-063 (Step 8 Amendment P) — blocking E2E staging gates for 5 plan-canonical SLIs
**Capstone success criteria**: SC-001 (≤ 15 s sub-agent reply), SC-009 (auto-routing coverage), SC-010 (overlay drift)
**Constitution**: I (Primacy of Life — life-safety relevance ⇒ no observation sampling), V (Graceful Degradation — error-budget governs FR-053 `degraded` tagging)
**Authoring ADR**: ADR-036-008 (SLI thresholds rationale and measurement methodology)

This contract pins the **numeric thresholds**, **KQL measurement queries**, **dimension cardinality bounds**, and **alert routing** for the five FR-063 SLIs. It is the binding artefact for `tests/staging_gates.py` (which refuses staging promotion on any breach) and `infra/bicep/modules/observability-alerts.bicep` (which provisions the Azure Monitor `scheduledQueryRules`).

---

## 1. SLI summary

| # | Name | Target | Breach | Alert |
|---|---|---|---|---|
| 1 | P95 inject→fan-out latency | 1500 ms | 2000 ms | warn=Slack, breach=SEV-3 PagerDuty |
| 2 | P99 audit gap-free invariant | 99.99 % over 7 d | any gap | SEV-2 PagerDuty + sim freeze |
| 3 | Throughput at 200 concurrent injections (P95 latency / error rate) | n/a | 3500 ms / 1 % | nightly fail → block staging promotion |
| 4 | Map-overlay drift error budget | 99.5 % over 24 h | 99.0 % | warn=Slack, breach=SEV-3 |
| 5 | P95 sub-agent reply latency (per model) | gpt-4o: 4000 ms; gpt-4o-mini: 1500 ms | gpt-4o: 5000 ms; gpt-4o-mini: 2000 ms | warn=Slack, breach=SEV-3 + FR-053 `degraded` tag |
| **6** *(NEW Cycle 2)* | **Z6 — P95 sub-agent reply latency, 24 h trailing window (SC-013 staging-promotion gate)** | gpt-4o: 4000 ms; gpt-4o-mini: 1500 ms | gpt-4o: 5000 ms; gpt-4o-mini: 2000 ms | warn=Slack, breach=block staging promotion |
| **7** *(NEW Cycle 2)* | **Z7 — Map-overlay drift error budget, 24 h trailing window (SC-013 staging-promotion gate)** | ≥ 99.5 % within 1500 ms | < 99.0 % | warn=Slack, breach=block staging promotion |

> **Cycle 2 note** (Amendment A2-02 / SC-013 / pass-1 Q2 / pass-2 Q4): Z6 and Z7 are **net-new SLIs** added for the staging-promotion gate. They complement (do NOT replace) SLI-4 / SLI-5 as defined in §§ 5–6 below — those latter remain the operational alert SLIs (5-min rolling window). Z6 and Z7 use a trailing 24 h window and a ≥ 30 sample-count minimum (`MIN_SAMPLES_PER_SLI_24H = 30`) to gate staging promotion. Z3 / Z4 / Z5 in `infra/observability/sli-kql.json` retain their Cycle 1 operational definitions (DLQ depth, Cosmos RU headroom, cascade degraded rate) unchanged.

---

## 2. SLI-1 — P95 inject→fan-out latency

**Definition**: time from inject-telemetry endpoint receipt of the chat-turn payload until the LAST subscribed sub-agent has acknowledged consumption of the resulting signal (per FR-026 fan-out, Step 8 Amendment C transactional invariant).

**Window**: rolling 5-minute window.

**Thresholds**:

- **Warn**: P95 > 1500 ms
- **Breach**: P95 > 2000 ms

**Rationale**: SC-001 requires ≤ 15 s end-to-end sub-agent reply; inject→fan-out is the first ≤ 2 s of that envelope. 2 s gives remaining 13 s for sub-agent reasoning + reply aggregation.

**KQL query**:

```kql
customEvents
| where timestamp > ago(5m)
| where name == "inject_telemetry.fan_out_complete"
| extend latency_ms = todouble(customDimensions["fan_out_latency_ms"])
| extend tenant_id = tostring(customDimensions["tenant_id"])
| summarize p95_latency_ms = percentile(latency_ms, 95)
            by bin(timestamp, 1m), tenant_id
| project timestamp, tenant_id, p95_latency_ms
```

**Dimensions**: `tenant_id` (cardinality ≤ 50). NOT split by `sim_id` (would explode cardinality).

**Sample rate**: **100 %** (no sampling — life-safety relevance).

**Alert routing**:

- Warn: Action Group `ag-sim-sre-warn` (Slack channel `#sre-sim-warnings`)
- Breach: Action Group `ag-sim-sre-prod` (SEV-3 PagerDuty, on-call SRE)

**Source-event emission**: `signal_pipeline_orchestrator.py` emits the `inject_telemetry.fan_out_complete` custom event after the last subscriber ack arrives (via Event Hubs receiver) or the FR-026 fan-out timeout fires (whichever first). Latency is wall-clock from request receipt.

---

## 3. SLI-2 — P99 audit gap-free invariant

**Definition**: percentage of `simulation_audit_entries` write windows in which `sequence_number` series is dense `[1..N]` for every sim active in the window.

**Window**: rolling 7-day window.

**Thresholds**:

- **Target**: 99.99 % gap-free
- **Breach**: any gap detected (zero-tolerance for gaps; the 0.01 % budget covers documented 503/sequence-uncertainty fail-closed events handled by ADR-036-007)

**Rationale**: FR-048 is the audit-completeness invariant underpinning Constitution IV. A single gap is an FR-049 export failure and an FR-054 lessons-capture corruption risk; gaps must be exceptional and immediately alerted.

**KQL query**:

```kql
let window = ago(7d);
let counts = AuditEntries_CL
  | where TimeGenerated > window
  | summarize maxSeq = max(sequence_number), cnt = count()
              by simulation_id_g
  | extend gap = maxSeq - cnt;
counts
  | summarize gappy = countif(gap != 0), total = count()
  | extend gap_free_pct = 100.0 * (1.0 - todouble(gappy) / total)
  | project gap_free_pct, gappy_count = gappy, total_simulations = total
```

**Dimensions**: NONE (one alert per affected `simulation_id`).

**Sample rate**: 100 %.

**Alert routing**: Action Group `ag-sim-sre-prod` (SEV-2 PagerDuty + on-call SRE + Compliance) on ANY gap. The affected simulation is automatically gated to read-only via the FR-066 idempotency-cache state-machine until the gap is reconciled by manual replay.

**Compatibility with ADR-036-007**: dead-letter queue entries with `sequence_number = -1` are NOT counted as gaps (they are documented uncertainty entries). The 0.01 % SLI-2 error budget arises from the documented 503/sequence-uncertainty fail-closed events.

---

## 4. SLI-3 — Throughput at 200 concurrent injections

**Definition**: under 200 sustained concurrent inject-telemetry requests across distinct sims, the P95 end-to-end latency of any single chat-turn (parse → fan-out → first sub-agent reply delta) MUST be ≤ 3500 ms AND the error rate MUST be ≤ 1 %.

**Window**: nightly Locust run; aggregated over the full run duration (typically 30 minutes).

**Thresholds**:

- **P95 end-to-end latency**: ≤ 3500 ms
- **Error rate** (HTTP 5xx OR RFC-9457 `injection-refused` with `reason=circuit_open`): ≤ 1 %

**Rationale**: SC-001 calls out "200-injection sample". The 3.5 s budget under high concurrency leaves 11.5 s of the 15 s SC-001 envelope for downstream sub-agent reasoning. The 1 % error rate bound is the FR-053 graceful-degradation budget (5 % at warn would mask infrastructure issues).

**Measurement** (Locust runner — NOT App Insights):

- **Runner**: `tests/load/simulation_injection_load.py` (existing Locust workflow)
- **Threshold assertion**: `tests/load/assert_locust_thresholds.py` (NEW for amendment cycle) reads the Locust `stats.csv` output and asserts:
  - `aggregated.median * percentile(95) <= 3500`
  - `error_count / total_count <= 0.01`
- **Cadence**: nightly on staging via `.github/workflows/simulation-load-test.yml` `cron: '0 18 * * *'` (06:00 AEST)
- **Failure semantics**: Locust exit code non-zero → workflow fails → `tests/staging_gates.py` blocks staging promotion until next successful run

**Dimensions**: signal `category` (cardinality 9), Locust user class (cardinality 1).

---

## 5. SLI-4 — Map-overlay drift error budget

**Definition**: percentage of map-overlay SSE messages that reach the web client within ≤ 1500 ms of source emission timestamp.

**Window**: rolling 24-hour window.

**Thresholds**:

- **Target**: 99.5 % within 1500 ms
- **Breach**: < 99.0 %

**Rationale**: FR-027 / FR-028 / FR-029 stipulate 10–15 s overlay SLA per category; the 1.5 s SSE-delivery slice is the network + client-render budget alone (sub-agent compute is excluded). 99.5 % is the SC-010 overlay drift target negotiated with the operational cohort (field coordinator + ops officer).

**KQL query**:

```kql
customEvents
| where timestamp > ago(24h)
| where name == "sse.map_overlay.delivered"
| extend client_received_ms = todouble(customDimensions["client_received_ms"])
| extend server_emit_ms = todouble(customDimensions["server_emit_ms"])
| extend drift_ms = client_received_ms - server_emit_ms
| extend tenant_id = tostring(customDimensions["tenant_id"])
| summarize within_budget = countif(drift_ms <= 1500), total = count()
            by bin(timestamp, 1d), tenant_id
| extend drift_budget_pct = 100.0 * todouble(within_budget) / total
| project timestamp, tenant_id, drift_budget_pct
```

**Sampling**: **10 % client-side** telemetry (cardinality control on the `client_received_ms` source); **100 % server-side** emit logging (`server_emit_ms`).

**Alert routing**:

- Warn (< 99.5 %): Action Group `ag-sim-sre-warn`
- Breach (< 99.0 %): Action Group `ag-sim-sre-prod` (SEV-3)

---

## 6. SLI-5 — P95 sub-agent reply latency (per model)

**Definition**: time from `SubAgentInvoker.invoke()` start until the sub-agent's `SubAgentReply` resolves (excludes Controller aggregation).

**Window**: rolling 5-minute window per model deployment.

**Thresholds** (per Foundry model tier):

| Model | Sub-agents | Warn (P95) | Breach (P95) |
|---|---|---|---|
| `gpt-4o` (with Foundry carve-out fallback) | Risk Assessment, Evacuation | 4000 ms | 5000 ms |
| `gpt-4o-mini` | Communication, Planning, Resource Allocation, Monitoring, Telemetry-Injection | 1500 ms | 2000 ms |

**Rationale**: matches Azure OpenAI model-tier latency profiles observed in `tests/fixtures/llm_cassettes/` baselines × 1.4 × safety margin. Aligns with SC-001 ≤ 15 s end-to-end (≤ 5 s × 3 chained agents in worst case).

**KQL query**:

```kql
customEvents
| where timestamp > ago(5m)
| where name == "sub_agent.invocation.complete"
| extend latency_ms = todouble(customDimensions["latency_ms"])
| extend sub_agent = tostring(customDimensions["sub_agent"])
| extend model_deployment = tostring(customDimensions["model_deployment"])
| summarize p95_latency_ms = percentile(latency_ms, 95)
            by bin(timestamp, 1m), sub_agent, model_deployment
| project timestamp, sub_agent, model_deployment, p95_latency_ms
```

**Dimensions**: `sub_agent` (cardinality 7) × `model_deployment` (cardinality 4 — `gpt-4o-mini-australiaeast`, `gpt-4o-mini-eastus2-carve-out`, `gpt-4o-australiaeast`, `gpt-4o-eastus2-carve-out`) = 28 series.

**Sample rate**: 100 %.

**Alert routing**:

- Warn: Action Group `ag-sim-sre-warn` (Slack)
- Breach: Action Group `ag-sim-sre-prod` (SEV-3) + the affected sub-agent's reply is auto-tagged with FR-053 `degraded=true` (Constitution V graceful degradation)

---

## 6a. SLI-Z6 — P95 sub-agent reply latency (24 h staging-promotion gate) *(NEW Cycle 2)*

**Source amendment**: Cycle 2 Amendment A2-02 / FR-063 STRENGTHEN / SC-013 (NEW success criterion); Cycle 2 pass-1 Q2 (24 h freshness window); Cycle 2 pass-2 Q4 (≥ 30 sample minimum).

**Definition**: time from `SubAgentInvoker.invoke()` start until the sub-agent's `SubAgentReply` resolves (excludes Controller aggregation), aggregated across the trailing 24 h, filtered to the staging environment.

**Window**: rolling **24 h trailing** window (per Cycle 2 pass-1 Q2 — symmetric with Z7 for one-parameter, one-CI-step operability; SLI-5's 5-min window is the alert cadence, not the promotion-evidence freshness).

**Sample-size minimum**: ≥ 30 distinct `customEvents.name == "sub_agent.invocation.complete"` rows within `ago(24h)` (per Cycle 2 pass-2 Q4 — Central-Limit-Theorem rule-of-thumb for P95 estimation; ~1.25 synthetic injections/hour ambient cost). Constant: `MIN_SAMPLES_PER_SLI_24H: Final[int] = 30`.

**Thresholds** (per Foundry model tier — same as SLI-5):

| Model | Sub-agents | Warn (P95) | Breach (P95) |
|---|---|---|---|
| `gpt-4o` (with Foundry carve-out fallback) | Risk Assessment, Evacuation | 4000 ms | 5000 ms |
| `gpt-4o-mini` | Communication, Planning, Resource Allocation, Monitoring, Telemetry-Injection | 1500 ms | 2000 ms |

**KQL query** (the query MUST emit a `sample_count` column alongside the SLI metric so the gate can assert both values from a single query result — per Cycle 2 pass-2 Q4):

```kql
customEvents
| where timestamp > ago(24h)
| where name == "sub_agent.invocation.complete"
| extend latency_ms = todouble(customDimensions["latency_ms"])
| extend sub_agent = tostring(customDimensions["sub_agent"])
| extend model_deployment = tostring(customDimensions["model_deployment"])
| extend env = tostring(customDimensions["env"])
| extend tenant_id = tostring(customDimensions["tenant_id"])
| where env == "staging"
| where tenant_id == "tnt-stg-smoke"
| summarize p95_latency_ms = percentile(latency_ms, 95),
            sample_count = count()
            by sub_agent, model_deployment
| project sub_agent, model_deployment, p95_latency_ms, sample_count
```

**Dimensions**: `sub_agent` × `model_deployment` (28 series — same cardinality as SLI-5).

**Filters**: `env == "staging"`; `tenant_id == "tnt-stg-smoke"` (Cycle 3 Pass-1 Q2 isolation guarantee (iv) — smoke-injected events are visible to the staging-promotion gate but never contaminate production-tenant SLI evaluation; the same KQL run against the production workspace returns zero rows).

**Sample rate**: 100 % (life-safety relevance — SC-001 lineage).

**Alert routing**:

- Warn: Action Group `ag-sim-sre-warn` (Slack)
- Breach: blocks staging promotion via `tests/staging_gates.py:assert_sli_thresholds()` (per Cycle 2 pass-1 Q2). NO PagerDuty page on Z6 (operational alerting remains on SLI-5's 5-min window).

**SC anchor**: `sc_refs: ["SC-001"]` in `infra/observability/sli-kql.json`.

---

## 6b. SLI-Z7 — Map-overlay drift error budget (24 h staging-promotion gate) *(NEW Cycle 2)*

**Source amendment**: Cycle 2 Amendment A2-02 / FR-063 STRENGTHEN / SC-013 (NEW success criterion); Cycle 2 pass-1 Q2 (24 h freshness window); Cycle 2 pass-2 Q4 (≥ 30 sample minimum).

**Definition**: percentage of map-overlay SSE messages that reach the web client within ≤ 1500 ms of source emission timestamp, aggregated across the trailing 24 h, filtered to the staging environment.

**Window**: rolling **24 h trailing** window (per Cycle 2 pass-1 Q2 — natural alignment with SLI-4's 24 h window; symmetric with Z6 for one-parameter operability).

**Sample-size minimum**: ≥ 30 distinct `customEvents.name == "sse.map_overlay.delivered"` rows within `ago(24h)` (per Cycle 2 pass-2 Q4 — binomial-proportion stability for drift-budget estimation). Constant: `MIN_SAMPLES_PER_SLI_24H: Final[int] = 30`.

**Thresholds**:

- **Target / Warn**: ≥ 99.5 % within 1500 ms
- **Breach**: < 99.0 %

**Rationale**: aligns with SLI-4 thresholds; the 1.5 s SSE-delivery slice is the network + client-render budget alone. 99.5 % is the SC-010 overlay drift target negotiated with the operational cohort.

**KQL query** (emits `sample_count` per Cycle 2 pass-2 Q4):

```kql
customEvents
| where timestamp > ago(24h)
| where name == "sse.map_overlay.delivered"
| extend client_received_ms = todouble(customDimensions["client_received_ms"])
| extend server_emit_ms = todouble(customDimensions["server_emit_ms"])
| extend drift_ms = client_received_ms - server_emit_ms
| extend env = tostring(customDimensions["env"])
| extend tenant_id = tostring(customDimensions["tenant_id"])
| extend model_deployment = tostring(customDimensions["model_deployment"])
| where env == "staging"
| where tenant_id == "tnt-stg-smoke"
| summarize within_budget = countif(drift_ms <= 1500),
            sample_count = count()
            by model_deployment
| extend drift_budget_pct = 100.0 * todouble(within_budget) / sample_count
| project model_deployment, drift_budget_pct, sample_count
```

**Dimensions**: `model_deployment` (per-model partition for the staging-promotion gate — Cycle 3 / A3-06 alignment with Z6 cardinality). SLI-4 retains its `tenant_id` dimension for operational alerting.

**Filters**: `env == "staging"`; `tenant_id == "tnt-stg-smoke"` (Cycle 3 Pass-1 Q2 isolation guarantee (iv) — smoke-injected events are visible to the staging-promotion gate but never contaminate production-tenant SLI evaluation; the same KQL run against the production workspace returns zero rows).

**Sample rate**: 100 % server-side (`server_emit_ms`); 10 % client-side (`client_received_ms`) — same as SLI-4.

**Alert routing**:

- Warn (< 99.5 %): Action Group `ag-sim-sre-warn` (Slack)
- Breach (< 99.0 %): blocks staging promotion via `tests/staging_gates.py:assert_sli_thresholds()` (per Cycle 2 pass-1 Q2). NO PagerDuty page on Z7 (operational alerting remains on SLI-4's 24 h window with `tenant_id` dimension).

**SC anchor**: `sc_refs: ["SC-010"]` in `infra/observability/sli-kql.json`.

---

## 6c. SLI-Z3 — DLQ depth (sequence-uncertainty fail-closed) *(Cycle 1 operational SLI)*

**Source**: Cycle 1 ADR-036-007 fail-closed sequence-uncertainty handling. Promoted to this contract in Cycle 3 / T-AA34 alignment audit per Pass-1 Q5 dynamic parametrisation (`spec.md:1183-1250`) so all seven SLIs in `infra/observability/sli-kql.json` participate in the FR-073 canonicalisation contract test.

**Definition**: count of `customEvents` with name `audit.sequence.uncertainty` over the rolling 1-hour window — non-zero indicates the fail-closed sequence allocator has rejected one or more entries due to allocator uncertainty.

**Window**: rolling 1-hour window.

**Thresholds**:

- **Warn**: ≥ 1 entry
- **Breach**: ≥ 1 entry (zero-tolerance — the fail-closed path is exceptional and any DLQ-aged entry is an operational incident pending manual reconciliation per ADR-036-007)

**KQL query**:

```kql
customEvents
| where timestamp > ago(1h)
| where name == "audit.sequence.uncertainty"
| summarize dlq_depth = count()
```

**Dimensions**: NONE (one alert per affected `simulation_id` is operational at SLI-2 alert level; this query is the high-level scalar gate).

**Sample rate**: 100 % (life-safety relevance — ADR-036-007 fail-closed path).

**Alert routing**: Action Group `ag-sim-sre-prod` (SEV-2 PagerDuty + Compliance) on ANY non-zero DLQ depth.

---

## 6d. SLI-Z4 — Cosmos RU consumption headroom *(Cycle 1 operational SLI)*

**Source**: Cycle 1 baseline observability per FR-063 capacity headroom guarantee. Promoted to this contract in Cycle 3 / T-AA34 alignment audit per Pass-1 Q5 dynamic parametrisation.

**Definition**: P95 of `requestCharge_s` (RU per request) on Cosmos data-plane requests over the rolling 15-minute window. Surfaces RU saturation BEFORE Cosmos returns 429 throttling responses.

**Window**: rolling 15-minute window.

**Thresholds**:

- **Warn**: P95 RU > 70 % of provisioned (heads up — review autoscale ceiling)
- **Breach**: P95 RU > 90 % of provisioned (raise autoscale ceiling OR investigate query inefficiency)

**KQL query**:

```kql
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.DOCUMENTDB"
| where Category == "DataPlaneRequests"
| summarize p95_ru = percentile(todouble(requestCharge_s), 95)
            by bin(TimeGenerated, 1m)
```

**Dimensions**: NONE (workspace-level scalar; per-container splits are operational dashboards, not gate conditions).

**Sample rate**: 100 % (Azure Diagnostics — no sampling override).

**Alert routing**: Action Group `ag-sim-sre-warn` on warn; `ag-sim-sre-prod` on breach.

---

## 6e. SLI-Z5 — Cascade degraded-to-annotation rate *(Cycle 1 operational SLI)*

**Source**: Cycle 1 T-Q03 affinity-ladder telemetry; FR-053 graceful-degradation budget. Promoted to this contract in Cycle 3 / T-AA34 alignment audit per Pass-1 Q5 dynamic parametrisation.

**Definition**: percentage of cascade fan-out completions that recorded a `cascade.degraded_to_annotation` event over the rolling 1-hour window — the fraction of fan-outs that exceeded their per-category SLA and were tagged `degraded` per FR-053.

**Window**: rolling 1-hour window.

**Thresholds**:

- **Warn**: > 5 % degraded
- **Breach**: > 10 % degraded (Constitution V graceful-degradation budget exhausted; raise on-call)

**KQL query**:

```kql
customEvents
| where timestamp > ago(1h)
| where name in ("cascade.degraded_to_annotation", "cascade.fan_out_complete")
| summarize degraded_pct = 100.0 * countif(name == "cascade.degraded_to_annotation") / count()
```

**Dimensions**: NONE (workspace-level scalar; per-category splits are operational dashboards).

**Sample rate**: 100 %.

**Alert routing**: Action Group `ag-sim-sre-warn` on warn; `ag-sim-sre-prod` on breach (SEV-3).

**SC anchor**: `sc_refs: ["SC-009"]` in `infra/observability/sli-kql.json`.

---

## 7. Cross-cutting concerns

### 7.1 Application Insights sampling override

Workspace default sampling is 5 %. For all five SLIs the per-resource `samplingPercentage` is overridden to **100** for operation names matching `simulation-*`. Configured in `infra/bicep/modules/observability-alerts.bicep`.

### 7.2 Action Groups (Bicep)

- `ag-sim-sre-warn`: Slack webhook to `#sre-sim-warnings`. Cooldown 5 min.
- `ag-sim-sre-prod`: PagerDuty integration on rotation `Sim-SRE-Primary`. SEV-2 → page; SEV-3 → page during business hours, Slack out-of-hours.

### 7.3 Staging promotion gate

`tests/staging_gates.py` enforces:

```python
MIN_SAMPLES_PER_SLI_24H: Final[int] = 30  # Cycle 2 pass 2 Q4 — CLT floor; raise to 100 if false-positive rate exceeds 5 %

def assert_sli_thresholds(env: str = "staging") -> None:
    """Refuse promotion from staging to prod if any SLI is in breach."""
    for sli_id in (1, 2, 3, 4, 5):
        result = run_kql_or_locust(sli_id, env)
        assert result.is_target_or_better(), f"SLI-{sli_id} breach: {result}"
    # Cycle 2 SC-013 staging-promotion gate — Z6 + Z7 over the trailing
    # 24 h window with sample-count minimum (per pass 1 Q2 + pass 2 Q4).
    for sli_id in ("Z6", "Z7"):
        result = run_kql(sli_id, env, window_hours=24)
        assert result.sample_count >= MIN_SAMPLES_PER_SLI_24H, (
            f"SLI-{sli_id} sample-size starvation: {result.sample_count} < {MIN_SAMPLES_PER_SLI_24H}"
        )
        assert result.is_target_or_better(), f"SLI-{sli_id} breach: {result}"
```

The script runs as a pre-promotion CI step in `.github/workflows/release-promotion.yml`.

### 7.4 Dashboard

- **Tool**: Azure Monitor Workbooks (single workspace, no extra cost). Grafana Managed Service is deferred (per ADR-036-008 § "Open question").
- **Workbook**: `infra/bicep/modules/observability-workbook-sim-slis.bicep` (NEW; co-located with the alert rules).
- **Layout**: one row per SLI with target/breach lines, current 5-min/24-h/7-d window value, alert state. Z6 + Z7 occupy a separate "SC-013 staging-promotion" row group (24 h window).

---

## 8. Testing

| Test | File | Purpose |
|---|---|---|
| Contract — KQL queries return numeric | `tests/devops/test_sli_kql_smoke.py` | Each query returns numeric (no null) on the staging dataset |
| Contract — Locust thresholds encoded | `tests/load/assert_locust_thresholds.py` | SLI-3 thresholds match this contract |
| Devops — Bicep alert rules | `tests/devops/test_observability_alerts_bicep.py` | All five `scheduledQueryRules` present with correct thresholds |
| Staging gate | `tests/staging_gates.py` | Refuses promotion on any breach |

---

## 9. Versioning

This contract is versioned alongside ADR-036-008. Threshold changes require an ADR amendment + this contract revision + a corresponding update to `tests/staging_gates.py` and `infra/bicep/modules/observability-alerts.bicep` in a single PR.

---

## 10. KQL canonicalisation contract *(NEW Cycle 3 — Amendment A3-05 / FR-073)*

**Source amendment**: Cycle 3 Amendment A3-05 (folds A3-06) / FR-073 (`spec.md:3660-3677`); Cycle 3 plan-decision PD-C3-01 (`plan.md:498-572`); Cycle 3 Pass-1 Q1 (`spec.md:838-925`); Cycle 3 Pass-2 Q2 (`spec.md:1388-1483`).

**Purpose**: Define the deterministic, idempotent, byte-exact transformation that maps any KQL string into a canonical form for byte-equality comparison. Each implementation KQL in `infra/observability/sli-kql.json` MUST canonicalise to the same byte-sequence as the canonical KQL in this contract for the corresponding SLI; the parametric contract test `tests/contract/test_sli_kql_canonical_match.py` enforces this across **all seven SLIs (Z1–Z7)** without `pytest.mark.xfail` / `@pytest.mark.skip` / hard-coded subset (Pass-2 Q3 anti-patterns).

### 10.1 Algorithm (six-step pipeline)

The canonicaliser MUST apply these steps in order; each step is independently deterministic and the composition is idempotent (running the canonicaliser on its own output is a fixed point).

1. **Strip comments.** Remove every line comment (`// …` to end-of-line) and every block comment (`/* … */`, including multi-line spans). The output contains zero `//` or `/*` substrings.
2. **Whitespace collapse with pipe-newline preservation.** Collapse runs of ASCII whitespace (spaces, tabs, multiple line-breaks) to a single space, preserving exactly one `\n` immediately before each pipe (`|`) so the canonical form is line-oriented per-clause.
3. **Lowercase Kusto reserved keywords.** Lowercase the reserved keywords `extend`, `where`, `summarize`, `by`, `project`, `let`, `and`, `or`, `in`, `between`, `ascending`, `descending`. Identifier and column names are NOT lowercased (case-sensitivity preserved for `customDimensions["sub_agent"]` etc.).
4. **Sort `by` clause column lists lexicographically.** For each `by ...` clause, sort the comma-separated column-reference list lexicographically so semantically-equivalent inputs (`by sub_agent, model_deployment` and `by model_deployment, sub_agent`) canonicalise to the same byte-sequence.
5. **Sort `summarize` aggregate-expression lists by left-hand-side alias.** For each `summarize ...` clause, sort the comma-separated `alias = expression` pairs by `alias` lexicographically (`summarize p95 = ..., sample_count = ...` vs `summarize sample_count = ..., p95 = ...` canonicalise alike).
6. **Strip redundant outer parentheses around `extend` target expressions.** `extend env = (tostring(customDimensions["env"]))` → `extend env = tostring(customDimensions["env"])`. Inner parentheses required by precedence are preserved.

### 10.2 Invariants

- **Idempotence**: `canonicalise_kql(canonicalise_kql(x)) == canonicalise_kql(x)` for every input `x` (fixed-point property).
- **Determinism**: the same input yields byte-identical output across Python interpreter restarts, hash-randomisation seeds, and dict-iteration orders (Python ≥ 3.7 dict insertion-order preservation is exploited; no `set()`-of-strings sorting paths participate).
- **Stability under semantic-no-op rewrites**: re-ordering `by` columns, re-ordering `summarize` aliases, adding/removing whitespace, adding/removing comments, and parenthesising/unparenthesising `extend` targets all canonicalise to the same byte-sequence.

### 10.3 Public Python API surface

The canonicaliser is implemented in `tests/contract/_kql_canonicaliser.py` (private leading-underscore module name signalling the symbol is internal to the contract-test surface) but exposes a stable public API via `__all__`:

```python
__all__ = ["canonicalise_kql", "canonical_kql_for_sli"]


def canonicalise_kql(text: str) -> str: ...
"""Public entry point — applies the six-step canonicalisation pipeline to *text*."""


def canonical_kql_for_sli(
    sli_id: str,
    *,
    thresholds_path: Path | None = None,
) -> str: ...
"""Return the canonicalised form of the contract KQL for *sli_id*.

Parses the matching ```` ```kql ... ``` ```` fenced block out of
*thresholds_path* (defaults to ``_THRESHOLDS_PATH``). Raises ``KeyError``
on unknown ``sli_id``; raises ``ValueError`` on a malformed contracts file.
"""
```

The module-level constant `_THRESHOLDS_PATH = Path(__file__).resolve().parents[2] / "specs" / "036-sim-agent-extend" / "contracts" / "sli-thresholds.md"` resolves to the present file; the resolution mirrors the established `_SLI_PATH` pattern at `tests/contract/test_sli_kql_schema_v2.py:25`.

### 10.4 Error contracts

- `KeyError("SLI-NONEXISTENT not found in <path>")` — `sli_id` does not match any fenced KQL block in the contracts file.
- `ValueError("Failed to extract canonical KQL for <sli_id>: <reason>")` — the contracts file is malformed (missing fence-close, empty fenced body, etc.).

### 10.5 Rejected alternatives — Kusto-AST equivalence

The Cycle 3 Pass-1 Q1 cohort weighed **strict-string canonicalisation** (this contract) against **Kusto-AST equivalence** (parsing the KQL into a Kusto AST, normalising the tree, then comparing structurally). AST equivalence was rejected on three grounds (PD-C3-01):

1. **No production-grade Kusto parser is permissively-licensed for Python.** The Microsoft Kusto.Language parser is .NET-only; the open-source `kustopy` family is incomplete and unmaintained. Strict-string canonicalisation requires zero new dependencies.
2. **AST equivalence allows silent drift on whitespace-significant operator forms.** In Kusto, `summarize` followed by `by` carries semantic meaning that an AST might normalise away (e.g. by re-ordering aggregate functions). The strict-string form preserves the operator-order semantics the spec author committed to.
3. **AST equivalence is harder to debug.** When the parametric test fails, a diff between two strings names the offending column; an AST diff names a tree-node and forces the engineer to re-walk both trees.

The strict-string approach trades algorithmic minimality for transparency and CI-cycle simplicity — the conscious trade-off recorded in PD-C3-01.

---

*Cycle 3 KQL canonicalisation contract authored 2026-05-10 in the Cycle 3 amendment cycle; aligned with Amendment A3-05 / FR-073, PD-C3-01, and Cycle 3 Pass-1 Q1 / Pass-2 Q2 / Pass-2 Q3.*
