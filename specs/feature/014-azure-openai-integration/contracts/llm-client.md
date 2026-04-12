# Contract: LLM Client API

**Feature**: 014-azure-openai-integration
**Module**: `apps/agents/common/llm_client.py`
**Date**: 2026-04-16

## Overview

The `LLMClient` is the sole entry point for all Azure OpenAI API calls. It handles authentication (managed identity), model routing (reasoning/drafting tier), retry logic (transient failures), and response metadata extraction. Agents do not interact with the OpenAI SDK directly.

## Class: `LLMClient`

### Constructor

```python
class LLMClient:
    def __init__(self, config: LLMClientConfig | None = None) -> None:
        """
        Initialise the Azure OpenAI client with managed identity authentication.

        Args:
            config: LLM configuration. If None, reads from environment variables.

        Raises:
            RuntimeError: If endpoint is not configured.
            ValueError: If endpoint does not resolve to an Australian Azure region.

        Authentication:
            Uses DefaultAzureCredential → azure_ad_token_provider pattern.
            NO API key support. AZURE_OPENAI_API_KEY is ignored if set.

        Validation at init:
            - Endpoint must be non-empty
            - Endpoint hostname must contain 'australiaeast' or 'australiasoutheast'
              (defense-in-depth; Bicep also enforces region)
            - If endpoint is missing, client is set to None (graceful degradation)
        """
```

### Method: `generate_response`

```python
def generate_response(
    self,
    *,
    purpose: str,                          # "reasoning" | "drafting"
    prompt: str,                           # User prompt text
    correlation_id: str | None = None,     # Optional; auto-generated if None
    max_output_tokens: int = 300,          # Overridden by agent config
    timeout_seconds: float = 30.0,         # Overridden by agent config
    temperature: float = 0.0,             # NEW: Overridden by agent config
) -> dict[str, object]:
    """
    Send a prompt to Azure OpenAI and return the response with metadata.

    Args:
        purpose: Model tier selector ("reasoning" → GPT-4o, "drafting" → GPT-4o-mini)
        prompt: The user prompt to send
        correlation_id: Tracing ID; generated if not provided
        max_output_tokens: Maximum tokens in the response
        timeout_seconds: Request timeout
        temperature: Model temperature (0.0 = deterministic, 0.3 = creative)

    Returns:
        dict with keys:
            text (str): Generated response text
            deployment_id (str): Azure OpenAI deployment name used
            correlation_id (str): Tracing correlation ID
            latency_ms (float): Call duration in milliseconds
            token_usage (dict): {"input_tokens": int, "output_tokens": int}

    Raises:
        RuntimeError: If client is not configured (no endpoint)
        RuntimeError: If deployment name is missing for the requested purpose
        openai.APIError: If all retries are exhausted (re-raised by tenacity)
    """
```

### Method: `_is_transient` (static)

```python
@staticmethod
def _is_transient(exc: BaseException) -> bool:
    """
    Return True for transient HTTP errors that warrant retry.

    Transient: HTTP 429 (rate limit), HTTP 503 (service unavailable)
    Non-transient: HTTP 400, 401, 403, 404, and all other errors
    """
```

### Retry Behaviour

- **Strategy**: Exponential backoff via `tenacity`
- **Attempts**: 3 (configurable via `LLMClientConfig.retry_attempts`)
- **Wait**: min=1s, max=4s, multiplier=1 (produces 1s, 2s, 4s)
- **Retry condition**: Only transient errors (429, 503)
- **On exhaustion**: Re-raise the exception to caller

### Authentication Contract

```text
BEFORE (current):
    AzureOpenAI(api_key=os.getenv("AZURE_OPENAI_API_KEY"), azure_endpoint=endpoint)

AFTER (this feature):
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default"
    )
    AzureOpenAI(azure_ad_token_provider=token_provider, azure_endpoint=endpoint)
```

### Breaking Changes

| Change | Impact | Migration |
|--------|--------|-----------|
| `AZURE_OPENAI_API_KEY` no longer used | Container Apps env vars | Remove `AZURE_OPENAI_API_KEY` from Bicep/env |
| `temperature` parameter added to `generate_response()` | Callers must pass or accept default | Default 0.0 preserves existing behaviour |
| Constructor accepts `LLMClientConfig` | Internal; callers use `LLMCallMixin` | No caller change needed |
| Australian endpoint validation at init | Non-AU endpoints rejected | Only affects misconfigured deployments |

### Logging Contract

Every LLM call logs at INFO level:
```text
llm_call correlation_id={id} deployment_id={dep} latency_ms={ms} input_tokens={in} output_tokens={out}
```

Failed calls log at WARNING level:
```text
LLM call failed: {error_type} status={status_code} correlation_id={id}
```
