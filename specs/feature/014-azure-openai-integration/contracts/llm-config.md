# Contract: LLM Configuration Per Agent

**Feature**: 014-azure-openai-integration
**Module**: `apps/agents/*/config.py` (all 5 agent configs)
**Date**: 2026-04-16

## Overview

Each agent's frozen dataclass configuration is extended with LLM-specific fields. These fields follow the existing env-var-at-construction pattern (`field(default_factory=lambda: os.getenv(...))`). The fields are read once at process startup and immutable thereafter.

## Fields Added to Each Agent Config

```python
# --- LLM Configuration ---

# Model tier: which Azure OpenAI deployment this agent uses
llm_model_tier: str = field(
    default_factory=lambda: os.getenv("LLM_MODEL_TIER", "{agent_default}")
)

# Temperature: controls determinism vs. creativity
llm_temperature: float = field(
    default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "{agent_default}"))
)

# Max output tokens per LLM call
llm_max_output_tokens: int = field(
    default_factory=lambda: int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "{agent_default}"))
)

# Confidence threshold for safety-critical output gating
llm_confidence_threshold: float = field(
    default_factory=lambda: float(os.getenv("LLM_CONFIDENCE_THRESHOLD", "0.7"))
)

# Fallback reduction factor applied to confidence when template fallback is used
llm_fallback_reduction_factor: float = field(
    default_factory=lambda: float(os.getenv("LLM_FALLBACK_REDUCTION_FACTOR", "0.5"))
)

# Monthly budget threshold in USD (tracking only, no enforcement)
llm_monthly_budget_usd: float = field(
    default_factory=lambda: float(os.getenv("LLM_MONTHLY_BUDGET_USD", "{agent_default}"))
)
```

## Per-Agent Defaults

| Agent | `LLM_MODEL_TIER` | `LLM_TEMPERATURE` | `LLM_MAX_OUTPUT_TOKENS` | `LLM_MONTHLY_BUDGET_USD` |
|-------|------------------|--------------------|-------------------------|--------------------------|
| Risk Assessment | `reasoning` | `0.0` | `4000` | `50.0` |
| Evacuation | `reasoning` | `0.0` | `4000` | `50.0` |
| Monitoring | `drafting` | `0.3` | `2000` | `50.0` |
| Communication | `drafting` | `0.3` | `2000` | `50.0` |
| Resource Allocation | `drafting` | `0.3` | `2000` | `50.0` |

**Note**: The `$50/agent/month` default is for dev environments. Prod environments override via `LLM_MONTHLY_BUDGET_USD=500.0` set in the Container App's environment variables through Bicep parameters.

## Integration with `compute_config_hash()`

Each agent's `compute_config_hash()` method MUST be updated to include the new LLM fields:

```python
def compute_config_hash(self) -> str:
    config_str = (
        # ... existing fields ...
        f"llm_model_tier={self.llm_model_tier};"
        f"llm_temperature={self.llm_temperature};"
        f"llm_max_output_tokens={self.llm_max_output_tokens};"
        f"llm_confidence_threshold={self.llm_confidence_threshold};"
        f"llm_fallback_reduction_factor={self.llm_fallback_reduction_factor};"
        f"llm_monthly_budget_usd={self.llm_monthly_budget_usd};"
    )
    return hashlib.sha256(config_str.encode()).hexdigest()
```

## Validation Contract

Validation occurs at config construction time. Invalid values MUST cause the agent to fail fast at startup with a descriptive error:

```python
def __post_init__(self) -> None:
    """Validate LLM configuration values immediately after construction."""
    if self.llm_model_tier not in ("reasoning", "drafting"):
        raise ValueError(f"Invalid LLM_MODEL_TIER: {self.llm_model_tier}")
    if not (0.0 <= self.llm_temperature <= 2.0):
        raise ValueError(f"LLM_TEMPERATURE must be 0.0–2.0, got {self.llm_temperature}")
    if self.llm_max_output_tokens <= 0 or self.llm_max_output_tokens > 16384:
        raise ValueError(f"LLM_MAX_OUTPUT_TOKENS must be 1–16384, got {self.llm_max_output_tokens}")
    if not (0.0 <= self.llm_confidence_threshold <= 1.0):
        raise ValueError(f"LLM_CONFIDENCE_THRESHOLD must be 0.0–1.0, got {self.llm_confidence_threshold}")
    if not (0.0 <= self.llm_fallback_reduction_factor <= 1.0):
        raise ValueError(f"LLM_FALLBACK_REDUCTION_FACTOR must be 0.0–1.0, got {self.llm_fallback_reduction_factor}")
```

**Note on frozen dataclass + `__post_init__`**: Python's `@dataclass(frozen=True)` supports `__post_init__` for validation — it runs after `__init__` sets the fields but before the freeze takes effect. This is the standard Python pattern.

## Environment Variable Precedence

1. Container App env vars (set in Bicep) — highest priority
2. `.env` file (local development) — loaded by agent startup scripts
3. Dataclass field defaults (hardcoded in config.py) — lowest priority

This matches the existing pattern across all agent configs.
