# Data Model: Azure OpenAI Integration Configuration

**Feature**: 014-azure-openai-integration
**Date**: 2026-04-16
**Status**: Complete

## Entities

### 1. LLMClientConfig (NEW — `apps/agents/common/llm_config.py`)

Shared LLM configuration dataclass used by all agents. Follows the existing frozen-dataclass-with-env-var pattern established in all 5 agent config files.

```python
@dataclass(frozen=True)
class LLMClientConfig:
    """Shared Azure OpenAI configuration, read from environment variables at construction."""

    # Connection
    endpoint: str                        # AZURE_OPENAI_ENDPOINT (required)
    reasoning_deployment: str            # AZURE_OPENAI_REASONING_DEPLOYMENT (default: "")
    drafting_deployment: str             # AZURE_OPENAI_DRAFTING_DEPLOYMENT (default: "")
    api_version: str                     # AZURE_OPENAI_API_VERSION (default: "2024-10-21")

    # Model parameters
    model_tier: str                      # "reasoning" | "drafting" — set per agent
    temperature: float                   # 0.0 (reasoning) | 0.3 (drafting) — configurable
    max_output_tokens: int               # 4000 (reasoning) | 2000 (drafting) — configurable

    # Retry & circuit breaker
    retry_attempts: int                  # default: 3
    retry_min_wait: float                # default: 1.0 (seconds)
    retry_max_wait: float                # default: 4.0 (seconds)
    timeout_seconds: float               # default: 30.0
    circuit_breaker_failure_threshold: int   # default: 3
    circuit_breaker_recovery_timeout: float  # default: 30.0 (seconds)

    # Confidence
    confidence_threshold: float          # default: 0.7
    fallback_reduction_factor: float     # default: 0.5

    # Cost tracking
    monthly_budget_usd: float            # default: 50.0 (dev) | 500.0 (prod) — per agent
```

**Validation Rules**:
- `endpoint` MUST be non-empty; MUST contain `australiaeast` or `australiasoutheast` in the hostname
- `model_tier` MUST be one of `"reasoning"` or `"drafting"`
- `temperature` MUST be in range [0.0, 2.0]
- `max_output_tokens` MUST be > 0 and ≤ 16384
- `confidence_threshold` MUST be in range [0.0, 1.0]
- `fallback_reduction_factor` MUST be in range [0.0, 1.0]
- `monthly_budget_usd` MUST be > 0

**Environment Variable Mapping**:

| Field | Env Var | Default |
|-------|---------|---------|
| `endpoint` | `AZURE_OPENAI_ENDPOINT` | *(required)* |
| `reasoning_deployment` | `AZURE_OPENAI_REASONING_DEPLOYMENT` | `""` |
| `drafting_deployment` | `AZURE_OPENAI_DRAFTING_DEPLOYMENT` | `""` |
| `api_version` | `AZURE_OPENAI_API_VERSION` | `"2024-10-21"` |
| `model_tier` | `LLM_MODEL_TIER` | `"drafting"` |
| `temperature` | `LLM_TEMPERATURE` | tier-dependent |
| `max_output_tokens` | `LLM_MAX_OUTPUT_TOKENS` | tier-dependent |
| `timeout_seconds` | `LLM_TIMEOUT_SECONDS` | `30.0` |
| `retry_attempts` | `LLM_RETRY_ATTEMPTS` | `3` |
| `circuit_breaker_failure_threshold` | `LLM_CB_FAILURE_THRESHOLD` | `3` |
| `circuit_breaker_recovery_timeout` | `LLM_CB_RECOVERY_TIMEOUT` | `30.0` |
| `confidence_threshold` | `LLM_CONFIDENCE_THRESHOLD` | `0.7` |
| `fallback_reduction_factor` | `LLM_FALLBACK_REDUCTION_FACTOR` | `0.5` |
| `monthly_budget_usd` | `LLM_MONTHLY_BUDGET_USD` | `50.0` |

---

### 2. CircuitBreakerState (NEW — `apps/agents/common/circuit_breaker.py`)

State machine for LLM availability circuit breaker.

```python
class CircuitState(Enum):
    CLOSED = "closed"          # Normal operation — LLM calls proceed
    OPEN = "open"              # LLM unavailable — skip to template fallback
    HALF_OPEN = "half_open"    # Probing — single call allowed to test recovery

@dataclass
class CircuitBreaker:
    failure_threshold: int     # Consecutive failures before opening (default: 3)
    recovery_timeout: float    # Seconds before OPEN → HALF_OPEN (default: 30.0)

    # Internal state (mutable)
    _state: CircuitState       # Current state
    _failure_count: int        # Consecutive failure counter
    _last_failure_time: float  # Timestamp of last failure (monotonic clock)
    _lock: threading.Lock      # Thread safety for state transitions
```

**State Transitions**:

```text
                 success
    ┌──────────────────────────────┐
    │                              │
    ▼                              │
 CLOSED ──── failure_threshold ───► OPEN ──── recovery_timeout ───► HALF_OPEN
    ▲         exceeded                ▲                                │
    │                                 │                                │
    │                                 └──── probe fails ───────────────┤
    │                                                                  │
    └──────────────────────── probe succeeds ──────────────────────────┘
```

**Methods**:
- `can_execute() → bool`: Returns `True` if in CLOSED or HALF_OPEN state
- `record_success()`: Reset failure count; transition HALF_OPEN → CLOSED
- `record_failure()`: Increment failure count; transition CLOSED → OPEN if threshold exceeded; transition HALF_OPEN → OPEN
- `state → CircuitState`: Current state (read-only property)

---

### 3. LLMResponse (existing — extended in `llm_client.py`)

The response dict returned by `LLMClient.generate_response()`. No schema change — existing fields are preserved.

```python
{
    "text": str,                    # Generated text content
    "deployment_id": str,           # Azure OpenAI deployment name used
    "correlation_id": str,          # Unique ID for tracing
    "latency_ms": float,            # Wall-clock time in milliseconds
    "token_usage": {
        "input_tokens": int,        # Prompt tokens consumed
        "output_tokens": int,       # Completion tokens consumed
    },
}
```

---

### 4. FallbackResponse (existing — extended in `llm_mixin.py`)

The response dict returned by `LLMCallMixin._generate_with_fallback()`. Extended with circuit breaker state.

```python
{
    "text": str,                           # Output text (LLM or template)
    "generation_method": str,              # "llm" | "template_fallback" | "safety_fallback"
    "model_deployment_id": str | None,     # Deployment used (None for template fallback)
    "token_usage": dict | None,            # Token counts (None for template fallback)
    "content_safety_result": str,          # "passed" | "not_checked" | reason string
    "circuit_breaker_state": str,          # NEW: "closed" | "open" | "half_open"
    "confidence_adjustment": float | None, # NEW: fallback reduction factor applied (None if LLM used)
}
```

---

### 5. Agent-to-Model Tier Mapping

Static mapping defining which agents use which model tier. Configured per-agent via `LLM_MODEL_TIER` env var; these are the defaults.

| Agent | Model Tier | Deployment | Temperature | Max Tokens | Rationale |
|-------|-----------|------------|-------------|------------|-----------|
| Risk Assessment | `reasoning` | `gpt-4o-{env}` | 0.0 | 4000 | Complex hazard analysis, life-safety decisions |
| Evacuation | `reasoning` | `gpt-4o-{env}` | 0.0 | 4000 | Route optimization, population safety |
| Monitoring | `drafting` | `gpt-4o-mini-{env}` | 0.3 | 2000 | Signal classification, summarisation |
| Communication | `drafting` | `gpt-4o-mini-{env}` | 0.3 | 2000 | Alert generation, multilingual |
| Resource Allocation | `drafting` | `gpt-4o-mini-{env}` | 0.3 | 2000 | Supply prioritisation, logistics |

---

### 6. Azure OpenAI Resource (Bicep — `infra/modules/azure-openai.bicep`)

Infrastructure entity representing the Azure OpenAI deployments and configuration.

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `openAiAccountName` | `string` | *(required)* | Name of existing Azure OpenAI resource |
| `location` | `string` | *(required)* | Must be `australiaeast` or `australiasoutheast` |
| `envPrefix` | `string` | *(required)* | Environment name (e.g., `dev`, `prod`) |
| `tags` | `object` | *(required)* | Resource tags |
| `reasoningModelName` | `string` | `'gpt-4o'` | Reasoning-tier model name |
| `reasoningModelVersion` | `string` | `'2024-08-06'` | Reasoning-tier model version |
| `draftingModelName` | `string` | `'gpt-4o-mini'` | Drafting-tier model name |
| `draftingModelVersion` | `string` | `'2024-07-18'` | Drafting-tier model version |
| `reasoningTpmQuota` | `int` | `30` | Reasoning-tier TPM quota (thousands); dev=30, prod=120 |
| `draftingTpmQuota` | `int` | `60` | Drafting-tier TPM quota (thousands); dev=60, prod=240 |
| `agentPrincipalIds` | `array` | `[]` | Managed identity principal IDs for RBAC |
| `logAnalyticsWorkspaceId` | `string` | *(required)* | Log Analytics workspace for diagnostics |

**Deployments Created**:
- `gpt-4o-{envPrefix}` — reasoning tier, TPM = `reasoningTpmQuota * 1000`
- `gpt-4o-mini-{envPrefix}` — drafting tier, TPM = `draftingTpmQuota * 1000`

**RBAC Assignments**:
- `Cognitive Services OpenAI User` (`5e0bd9bd-7b93-4f28-af87-19fc36ad61bd`) for each principal in `agentPrincipalIds`

**Diagnostic Settings**:
- Log categories: `RequestResponse`, `Audit`
- Metric categories: `AllMetrics`
- Destination: Log Analytics workspace

---

### 7. Risk Register Entry (FR-019 — `docs/risk-register/RISK-AOAI-001.md`)

| Field | Value |
|-------|-------|
| **Risk ID** | `RISK-AOAI-001` |
| **Risk Title** | AI Model Unavailability During Disaster Operations |
| **Probability** | Medium (20–50%) — Azure OpenAI outages during peak disaster load |
| **Impact** | High — degraded agent output quality during critical decision windows |
| **Mitigation Strategy** | (1) Template fallback for all agents, (2) Circuit breaker prevents retry storms, (3) Manual failover to AU Southeast via IaC, (4) Confidence threshold blocks low-confidence outputs from automatic escalation |
| **Residual Risk** | Low — template outputs maintain operational continuity with reduced quality |
| **Owner** | Platform Operations Lead |
| **Review Cadence** | Quarterly + post-incident |

Additional risk entries for token quota exhaustion (`RISK-AOAI-002`) and credential propagation delays (`RISK-AOAI-003`) follow the same format.

---

### 8. LLM Telemetry Metrics (NEW — emitted via OpenTelemetry)

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `llm.call.count` | Counter | `agent`, `deployment`, `outcome` | Total LLM calls |
| `llm.call.duration_ms` | Histogram | `agent`, `deployment` | Call latency distribution |
| `llm.tokens.input` | Counter | `agent`, `deployment` | Cumulative input tokens |
| `llm.tokens.output` | Counter | `agent`, `deployment` | Cumulative output tokens |
| `llm.fallback.count` | Counter | `agent`, `fallback_type` | Fallback events (template/safety) |
| `llm.error.count` | Counter | `agent`, `error_category` | Error events by category |
| `llm.circuit_breaker.state_change` | Counter | `agent`, `from_state`, `to_state` | Circuit breaker transitions |
| `llm.budget.exceeded` | Counter | `agent` | Monthly budget threshold breaches |
| `llm.confidence.below_threshold` | Counter | `agent` | Outputs flagged for human review |

## Configurable Parameters Summary

All LLM configuration fields added to each agent's existing `config.py`:

| Parameter | Env Var | Risk Assessment | Evacuation | Monitoring | Communication | Resource Allocation |
|-----------|---------|----------------|------------|------------|---------------|-------------------|
| Model tier | `LLM_MODEL_TIER` | `reasoning` | `reasoning` | `drafting` | `drafting` | `drafting` |
| Temperature | `LLM_TEMPERATURE` | `0.0` | `0.0` | `0.3` | `0.3` | `0.3` |
| Max output tokens | `LLM_MAX_OUTPUT_TOKENS` | `4000` | `4000` | `2000` | `2000` | `2000` |
| Confidence threshold | `LLM_CONFIDENCE_THRESHOLD` | `0.7` | `0.7` | `0.7` | `0.7` | `0.7` |
| Fallback reduction | `LLM_FALLBACK_REDUCTION_FACTOR` | `0.5` | `0.5` | `0.5` | `0.5` | `0.5` |
| Monthly budget (dev) | `LLM_MONTHLY_BUDGET_USD` | `50.0` | `50.0` | `50.0` | `50.0` | `50.0` |
| Monthly budget (prod) | `LLM_MONTHLY_BUDGET_USD` | `500.0` | `500.0` | `500.0` | `500.0` | `500.0` |
