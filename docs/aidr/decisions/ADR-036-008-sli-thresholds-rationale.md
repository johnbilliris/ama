# ADR-036-008: SLI Threshold Rationale and Measurement Methodology

**Status**: Accepted
**Deciders**: SRE Engineer, Solution Architect, QA/Test Engineer, Principal Engineer
**Date**: 2026-05-08
**Spec**: 036-sim-agent-extend
**FR coverage**: FR-063 (Step 8 Amendment P), SC-001, SC-009, SC-010
**Constitution**: I (Primacy of Life), V (Graceful Degradation)
**Capstone success criteria**: SC-001 (≤15 s sub-agent reply), SC-009 (auto-routing coverage), SC-010 (overlay drift)

## Context

The Step 8 cross-cohort review (technical SRE + QA cohorts) flagged
that the spec referred to "5 plan-canonical SLIs" without numeric
thresholds, blocking E2E gates, or measurement queries. The Step 8
Amendment P (FR-063) demands BLOCKING staging-gate evidence for all
five SLIs before promotion to production.

Without committed thresholds the staging gates cannot be encoded
declaratively in CI, the alerting rules in
`infra/bicep/modules/observability-alerts.bicep` cannot be wired,
and the FR-053 graceful-degradation tagging in chat replies cannot
be triggered. Each threshold must therefore have:

- A numeric **target** (warn) and **objective** (breach) value.
- A **measurement query** in Application Insights / Log Analytics
  with explicit dimension cardinality bounds.
- A **sample-rate** policy that does not bias life-safety
  observations.
- A defined **alert routing** (warn → SRE channel; breach → SEV-3
  PagerDuty).

## Decision

Adopt the following five SLIs with the numeric thresholds below as
the canonical FR-063 set, codified in
`specs/036-sim-agent-extend/contracts/sli-thresholds.md` (NEW
contract artefact added in this amendment cycle) and enforced via
`tests/staging_gates.py` BEFORE staging promotion:

### SLI-1: P95 inject→fan-out latency

- **Definition**: time from inject-telemetry endpoint receipt of
  the chat-turn payload until the LAST subscribed sub-agent has
  acknowledged consumption of the resulting signal (per FR-026
  fan-out, Step 8 Amendment C transactional invariant).
- **Warn threshold**: 1500 ms (P95 over rolling 5-minute window)
- **Breach threshold**: 2000 ms (P95)
- **Rationale**: SC-001 requires ≤15 s end-to-end sub-agent reply;
  inject→fan-out is the first ≤2 s of that envelope. 2 s gives
  remaining 13 s for sub-agent reasoning + reply aggregation.
- **Measurement**:
  ```kql
  customEvents
  | where name == "inject_telemetry.fan_out_complete"
  | extend latency_ms = todouble(customDimensions["fan_out_latency_ms"])
  | summarize percentile(latency_ms, 95) by bin(timestamp, 5m), tenant_id
  ```
- **Dimensions**: `tenant_id` (cardinality ≤ 50). NOT split by
  `sim_id` (would explode cardinality).
- **Sample rate**: 100 % (no sampling — life-safety relevant).

### SLI-2: P99 audit gap-free invariant

- **Definition**: percentage of `simulation_audit_entries` write
  windows in which `sequence_number` series is dense [1..N] for
  every sim active in the window.
- **Target/objective**: **99.99 %** over any rolling 7-day window
  (zero tolerance for gaps; the 0.01 % budget covers documented
  503/sequence-uncertainty fail-closed events handled by ADR-036-007).
- **Rationale**: FR-048 is the audit-completeness invariant
  underpinning Constitution IV. A single gap is an FR-049 export
  failure and an FR-054 lessons-capture corruption risk; gaps must
  be exceptional and immediately alerted.
- **Measurement**:
  ```kql
  let window = ago(7d);
  let counts = AuditEntries_CL | where TimeGenerated > window
    | summarize maxSeq = max(sequence_number), cnt = count() by simulation_id_g
    | extend gap = maxSeq - cnt;
  counts | summarize gappy = countif(gap != 0), total = count()
        | extend gap_free_pct = 100.0 * (1.0 - todouble(gappy) / total)
  ```
- **Alert**: ≥ 1 gap detected → SEV-2 PagerDuty + simulation freeze
  (the affected sim is gated to read-only until the gap is
  reconciled by manual replay).

### SLI-3: Throughput at 200 concurrent injections

- **Definition**: under 200 sustained concurrent inject-telemetry
  requests across distinct sims, the **P95 end-to-end latency** of
  any single chat-turn (parse → fan-out → first sub-agent reply
  delta) MUST be ≤ 3500 ms and the **error rate** (HTTP 5xx OR
  RFC-9457 `injection-refused` with `reason=circuit_open`) MUST be
  ≤ 1 %.
- **Rationale**: SC-001 calls out "200-injection sample". The 3.5 s
  budget under high concurrency leaves 11.5 s of the 15 s SC-001
  envelope for downstream sub-agent reasoning. The 1 % error rate
  bound is the FR-053 graceful-degradation budget (5 % at warn would
  mask infrastructure issues).
- **Measurement**: Locust runner
  `tests/load/simulation_injection_load.py` (existing) extended in
  this amendment to produce these P95/error-rate exports; assertion
  driven by `tests/load/assert_locust_thresholds.py`.
- **Cadence**: nightly on staging via
  `.github/workflows/simulation-load-test.yml`.

### SLI-4: Map-overlay drift error budget

- **Definition**: percentage of map-overlay SSE messages that reach
  the web client within ≤ 1500 ms of source emission timestamp.
- **Target**: **99.5 %** over any rolling 24-hour window.
- **Rationale**: FR-027 / FR-028 / FR-029 stipulate 10–15 s overlay
  SLA per category; the 1.5 s SSE-delivery slice is the network +
  client-render budget alone (sub-agent compute is excluded). 99.5 %
  is the SC-010 overlay drift target negotiated with the operational
  cohort (field coordinator + ops officer).
- **Measurement**:
  ```kql
  customEvents
  | where name == "sse.map_overlay.delivered"
  | extend drift_ms = todouble(customDimensions["client_received_ms"]) - todouble(customDimensions["server_emit_ms"])
  | summarize within_budget = countif(drift_ms <= 1500), total = count() by bin(timestamp, 1d)
  | extend drift_budget_pct = 100.0 * todouble(within_budget) / total
  ```
- **Sampling**: 10 % client-side telemetry (cardinality control); 100 %
  server-side emit logging.

### SLI-5: P95 sub-agent reply latency (per model)

- **Definition**: time from `SubAgentInvoker.invoke()` start until
  the sub-agent's `SubAgentReply` resolves (excludes Controller
  aggregation).
- **Thresholds**:
  - **gpt-4o models** (Risk Assessment, Evacuation): warn 4000 ms /
    breach 5000 ms (P95)
  - **gpt-4o-mini models** (Comms, Planning, Resource Allocation,
    Monitoring, Telemetry-Injection): warn 1500 ms / breach 2000 ms (P95)
- **Rationale**: matches Azure OpenAI model-tier latency profiles
  observed in `tests/fixtures/llm_cassettes/` baselines × 1.4× safety
  margin. Aligns with SC-001 ≤15 s end-to-end (≤5 s × 3 chained
  agents in worst case).
- **Measurement**: existing
  `customEvents | where name == "sub_agent.invocation.complete"`,
  split by `sub_agent` and `model_deployment` dimensions
  (cardinality 7 sub-agents × 4 deployments = 28).
- **Alert routing**: warn → SRE channel; breach → page SRE + auto-tag
  the sub-agent reply with FR-053 `degraded=true`.

## Alerts and routing summary

| SLI | Warn | Breach | Routing |
|---|---|---|---|
| SLI-1 inject→fan-out P95 | 1500 ms | 2000 ms | warn=Slack #sre, breach=SEV-3 PagerDuty |
| SLI-2 gap-free 99.99% | n/a | any gap | SEV-2 PagerDuty + sim freeze |
| SLI-3 throughput P95 / error rate | n/a | 3500 ms / 1 % | nightly fail → block staging promotion |
| SLI-4 overlay drift 99.5% | 99.5 % | 99.0 % | warn=Slack, breach=SEV-3 |
| SLI-5 sub-agent reply P95 | model-dep | model-dep | warn=Slack, breach=SEV-3 + FR-053 tag |

## Alternatives considered

- **No SLI thresholds, only soft warnings**: rejected — Step 8 Amendment P explicitly demands blocking staging gates.
- **Stricter SLOs (P99 inject→fan-out 1500 ms)**: rejected — would
  mask transient Cosmos retries (per ADR-036-001 Session-token path)
  and produce false alerts during normal operation.
- **Looser SLO (P95 5000 ms inject→fan-out)**: rejected — would
  consume the entire SC-001 envelope before sub-agent compute begins.
- **Per-sim cardinality split**: rejected — would explode the App
  Insights bill at 200 concurrent sims × 6 sub-agents.
- **Static, non-rolling windows**: rejected — alerting noise on
  daily boundaries; rolling windows are industry-standard.

## Consequences

**Positive**:

- Five blocking, declaratively-enforced SLIs aligned to the
  Capstone success criteria.
- Alerts route to the appropriate channel by severity (no PagerDuty
  noise for warn-level).
- Staging gates are deterministic (`tests/staging_gates.py` produces
  binary pass/fail).

**Negative**:

- App Insights cost increases ~AU$5/month for the additional custom
  metrics + dimensions.
- Alert tuning will require 2–4 weeks of post-launch operational
  data to validate; the Sample period above is conservative.

**Test obligations**:

- `tests/staging_gates.py` MUST run against the 5 SLIs and refuse
  promotion on any breach.
- `tests/load/assert_locust_thresholds.py` MUST encode SLI-3
  numeric thresholds explicitly (no "approximately").
- A nightly SRE smoke test MUST verify all 5 KQL queries return
  numeric results (no "no data" / null).

## References

- Spec FR-063 (Step 8 Amendment P), SC-001, SC-009, SC-010
- Step 8 cross-cohort synthesis: `step8-synthesis.md` § H10
  ("SLI/E2E staging gates blocking promotion")
- ADR-036-007 (sequence allocator — the 0.01 % SLI-2 error budget
  arises from the documented 503/sequence-uncertainty fail-closed
  events)
- Capstone success criteria: `capstone.md` SC-001, SC-009, SC-010
- Microsoft Learn — SLO measurement: <https://learn.microsoft.com/azure/well-architected/reliability/metrics>
