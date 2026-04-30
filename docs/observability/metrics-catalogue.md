# Custom Metrics Catalogue

**Purpose**: every Application Insights customMetric is registered here per FR-O02. Source of truth for both the Bicep Workbook tiles (FR-O04) and the runtime registration in `apps/api/app/observability/metrics.py`.

> **Convention**: name uses dot.case namespacing; dimensions use snake_case. `kind` ∈ {counter, gauge, histogram}. `unit` is UCUM where possible. `retention_days` aligns to the FR-O01 per-tier policy (audit 2555, operational 90, security 365, eval 2555).

## Ingestion / Signals

| Name | Kind | Unit | Dimensions | Source module | SLO | Retention |
|---|---|---|---|---|---|---|
| `signal.ingestion.lag_seconds` | histogram | s | `source`, `jurisdiction` | `apps.ingestion.pipeline` | SLO-1 | 90 d |
| `signal.ingestion.dead_letter_total` | counter | 1 | `source`, `reason` | same | n/a | 90 d |

## Agents

| Name | Kind | Unit | Dimensions | Source module | SLO | Retention |
|---|---|---|---|---|---|---|
| `agent.handoff.success_total` | counter | 1 | `source_agent`, `target_agent` | `apps.agents.common.resilience.handoffs` | SLO-2 | 90 d |
| `agent.handoff.failure_total` | counter | 1 | `source_agent`, `target_agent`, `reason` | same | SLO-2 | 90 d |
| `agent.handoff.dead_letter_depth` | gauge | 1 | `queue` | same | SLO-2 | 90 d |
| `agent.handoff.attempt_total` | counter | 1 | `source_agent`, `target_agent`, `attempt` | same | n/a | 90 d |
| `agent.killswitch.lag_seconds` | histogram | s | `agent_id` | `apps.agents.common.lifecycle.killswitch` | SLO-7 | 90 d |
| `agent.killswitch.transitions_total` | counter | 1 | `agent_id`, `direction` | same | n/a | 90 d |

## Recommendations + Audit

| Name | Kind | Unit | Dimensions | Source module | SLO | Retention |
|---|---|---|---|---|---|---|
| `recommendation.created_total` | counter | 1 | `agent`, `jurisdiction`, `shadow` | `apps.api.app.repositories.recommendation_repository` | n/a | 90 d |
| `recommendation.consensus_total` | counter | 1 | `agents_count` | `apps.api.app.services.consensus_detector` | n/a | 90 d |
| `audit.integrity_check.runs_total` | counter | 1 | — | `apps.api.app.services.audit_integrity_service` | SLO-5 | 2555 d |
| `audit.integrity_check.failures_total` | counter | 1 | — | same | SLO-5 | 2555 d |
| `audit.segment.sealed_total` | counter | 1 | `tenant_id` | `apps.api.app.repositories.audit_segment_repository` | n/a | 2555 d |

## Alerts (Public Information)

| Name | Kind | Unit | Dimensions | Source module | SLO | Retention |
|---|---|---|---|---|---|---|
| `alert.publish.lag_seconds` | histogram | s | `jurisdiction`, `language`, `channel` | `apps.api.app.services.alert_publication_service` | SLO-3 | 90 d |
| `alert.published_total` | counter | 1 | `jurisdiction`, `aws_level`, `channel` | same | n/a | 90 d |
| `alert.blocked_by_safety_total` | counter | 1 | `reason` | `apps.agents.communication` | n/a | 90 d |

## LLM + RAG

| Name | Kind | Unit | Dimensions | Source module | SLO | Retention |
|---|---|---|---|---|---|---|
| `llm.tokens.total` | counter | 1 | `model`, `deployment`, `operation` | `apps.agents.llm.llm_mixin` | n/a | 90 d |
| `llm.cost.aud_micros` | counter | uAUD | `model`, `deployment`, `operation`, `incident_id` | same | SLO-6 | 2555 d (eval) |
| `llm.budget.warning_total` | counter | 1 | `scope` | same | SLO-6 | 90 d |
| `llm.fallback_step_total` | counter | 1 | `from_strategy`, `to_strategy` | `apps.agents.llm.strategies` | n/a | 90 d |
| `llm.shadow.divergence_score` | histogram | 1 | `prod_model`, `shadow_model` | `apps.eval-runner.shadow` | n/a | 2555 d (eval) |
| `rag.retrieval.lag_milliseconds` | histogram | ms | `index` | `apps.api.app.services.rag_service` | SLO-8 | 90 d |
| `rag.retrieval.hit_count` | histogram | 1 | `index` | same | n/a | 90 d |

## Resilience

| Name | Kind | Unit | Dimensions | Source module | SLO | Retention |
|---|---|---|---|---|---|---|
| `circuitbreaker.state` | gauge | 1 | `name` | `apps.agents.common.resilience.circuit_breaker` | n/a | 90 d |
| `circuitbreaker.transitions_total` | counter | 1 | `name`, `from_state`, `to_state` | same | n/a | 90 d |

## Security / Sovereignty

| Name | Kind | Unit | Dimensions | Source module | SLO | Retention |
|---|---|---|---|---|---|---|
| `gateway.classification.denied_total` | counter | 1 | `class`, `target_region` | `apps.agents.common.safety.classification` | n/a | 365 d |
| `shadow.classification.denied_total` | counter | 1 | `class` | same | n/a | 365 d |
| `pii.canary_detected_total` | counter | 1 | `field`, `severity` | `apps.api.app.middleware.pii_redaction_validator` | n/a | 365 d |
| `carveout.deploy_blocked_total` | counter | 1 | `model_name`, `reason` | `scripts.verify-carveout` | n/a | 365 d |
| `network.public_probe_blocked_total` | counter | 1 | `service` | probe job | SLO-10 | 365 d |
| `network.public_probe_succeeded_total` | counter | 1 | `service` | probe job | SLO-10 | 365 d |

## CI/CD (DORA)

| Name | Kind | Unit | Dimensions | Source module | SLO | Retention |
|---|---|---|---|---|---|---|
| `dora.deployment_frequency_per_day` | gauge | 1 | `environment` | DORA aggregator | n/a | 365 d |
| `dora.lead_time_hours` | histogram | h | `environment` | same | n/a | 365 d |
| `dora.change_failure_rate` | gauge | 1 | `environment` | same | n/a | 365 d |
| `dora.mttr_minutes` | histogram | min | `environment` | same | n/a | 365 d |

## Review cadence

Reviewed quarterly by SRE Engineer + Software Developer. Adding a metric requires updating this catalogue AND `apps/api/app/observability/metrics.py` registry in the same PR.
