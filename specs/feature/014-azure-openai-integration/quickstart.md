# Quickstart: Azure OpenAI Integration

**Feature**: 014-azure-openai-integration
**Date**: 2026-04-16

## Prerequisites

- Python 3.12+
- Azure CLI (`az login` completed)
- Azure subscription with Azure OpenAI access in Australia East
- Existing disaster response hub infrastructure deployed (`azd up`)

## Local Development Setup

### 1. Install Dependencies

```bash
pip install azure-identity openai tenacity opentelemetry-api opentelemetry-sdk
```

Or via the project's dependency manager:

```bash
uv sync
```

### 2. Configure Environment Variables

Create or update your `.env` file in the repo root:

```bash
# Azure OpenAI connection (required)
AZURE_OPENAI_ENDPOINT=https://{your-env}-openai-{suffix}.openai.azure.com/

# Model deployments (required for LLM calls; omit for template-only mode)
AZURE_OPENAI_REASONING_DEPLOYMENT=gpt-4o-dev
AZURE_OPENAI_DRAFTING_DEPLOYMENT=gpt-4o-mini-dev

# API version
AZURE_OPENAI_API_VERSION=2024-10-21

# Per-agent LLM configuration (optional — defaults shown)
LLM_MODEL_TIER=reasoning              # or "drafting"
LLM_TEMPERATURE=0.0                   # 0.0 for reasoning, 0.3 for drafting
LLM_MAX_OUTPUT_TOKENS=4000            # 4000 for reasoning, 2000 for drafting
LLM_CONFIDENCE_THRESHOLD=0.7
LLM_FALLBACK_REDUCTION_FACTOR=0.5
LLM_MONTHLY_BUDGET_USD=50.0

# Circuit breaker (optional)
LLM_CB_FAILURE_THRESHOLD=3
LLM_CB_RECOVERY_TIMEOUT=30.0
```

**Note**: `AZURE_OPENAI_API_KEY` is NOT used. Authentication is via `DefaultAzureCredential`, which uses your `az login` session locally.

### 3. Run Without Azure OpenAI (Template Mode)

If `AZURE_OPENAI_ENDPOINT` is not set, agents automatically fall back to template-based outputs. This is the default local development experience — no Azure resource required.

```bash
# Start any agent — it will use template outputs
cd apps/agents
python -m risk_assessment.main
```

### 4. Run With Azure OpenAI (Live LLM Mode)

```bash
# Ensure you're logged in
az login

# Set the endpoint (from your Azure deployment)
export AZURE_OPENAI_ENDPOINT=$(az deployment group show -g {rg} -n main --query properties.outputs.AZURE_OPENAI_ENDPOINT.value -o tsv)
export AZURE_OPENAI_REASONING_DEPLOYMENT=gpt-4o-dev
export AZURE_OPENAI_DRAFTING_DEPLOYMENT=gpt-4o-mini-dev

# Start any agent — it will use live LLM
python -m risk_assessment.main
```

## Infrastructure Deployment

### Deploy Azure OpenAI with Model Deployments

```bash
# Deploy everything (including Azure OpenAI module)
azd up

# Or deploy just infrastructure
az deployment group create \
  -g {resource-group} \
  -f infra/main.bicep \
  -p environmentName=dev \
  -p location=australiaeast
```

The deployment creates:
- Azure OpenAI resource in Australia East
- GPT-4o deployment (`gpt-4o-dev`) at 30K TPM
- GPT-4o-mini deployment (`gpt-4o-mini-dev`) at 60K TPM
- RBAC role assignments for Container App managed identities
- Diagnostic settings routing to Log Analytics

### Verify Deployment

```bash
# Check the Azure OpenAI resource
az cognitiveservices account show -n {openai-name} -g {rg} --query "{location:location, endpoint:properties.endpoint, localAuth:properties.disableLocalAuth}"

# Check model deployments
az cognitiveservices account deployment list -n {openai-name} -g {rg} -o table

# Verify RBAC
az role assignment list --scope /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{openai-name} -o table
```

## Running Tests

### Contract Tests (No Azure Resource Needed)

```bash
# Run all LLM-related contract tests
pytest tests/contract/test_llm_fallback.py tests/contract/test_llm_managed_identity.py tests/contract/test_llm_model_routing.py tests/contract/test_llm_confidence.py tests/contract/test_llm_circuit_breaker.py tests/contract/test_llm_telemetry.py -v

# Run the full contract test suite
pytest tests/contract/ -v
```

### Live LLM Simulation Tests (Azure Resource Required)

```bash
# These tests are skipped unless Azure OpenAI env vars are set
pytest tests/simulation/test_quickstart_live_llm_rehearsal.py -v
```

## Verifying the Integration

### Health Check

Each agent validates LLM connectivity at startup. To manually verify:

```python
from common.llm_client import LLMClient

client = LLMClient()
response = client.generate_response(
    purpose="reasoning",
    prompt="Health check: respond with 'OK'",
    max_output_tokens=10,
    temperature=0.0,
)
print(f"Status: OK | Deployment: {response['deployment_id']} | Latency: {response['latency_ms']}ms")
```

### Verify Template Fallback

```python
from common.llm_mixin import LLMCallMixin

class TestAgent(LLMCallMixin):
    pass

agent = TestAgent()
result = agent._generate_with_fallback(
    purpose="reasoning",
    prompt="Test prompt",
    template_text="Template fallback response",
)
print(f"Method: {result['generation_method']}")
# With no Azure OpenAI configured: "template_fallback"
# With Azure OpenAI configured: "llm"
```

### Verify Content Safety

```python
from common.content_safety import ContentSafetyValidator

validator = ContentSafetyValidator()
result = validator.validate(text="Normal emergency response message")
print(f"Passed: {result.passed}")  # True
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `RuntimeError: Azure OpenAI client is not configured` | `AZURE_OPENAI_ENDPOINT` not set | Set the env var or run in template mode |
| `ValueError: Endpoint does not resolve to an Australian Azure region` | Non-AU endpoint configured | Check `AZURE_OPENAI_ENDPOINT` value |
| `AuthenticationError` | Managed identity not configured or RBAC missing | Run `az login` locally; check RBAC in Azure |
| `DeploymentNotFoundError` | Deployment name mismatch | Check `AZURE_OPENAI_REASONING_DEPLOYMENT` matches Bicep output |
| All agents returning template output | LLM unreachable or circuit breaker open | Check endpoint connectivity; circuit breaker auto-recovers after 30s |
