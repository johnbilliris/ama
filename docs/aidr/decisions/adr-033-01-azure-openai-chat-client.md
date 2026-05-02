# ADR-033-01: Use `OpenAIChatClient` (Azure OpenAI via Entra ID), Not `FoundryAgent`, as the ChatClient Backing for All MAF Agents

## Status

Accepted

## Context

Feature `033-maf-adoption` migrates the five named operational agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication) onto the Microsoft Agent Framework (MAF) Python SDK. Each agent is constructed as an instance of `agent_framework.Agent` and therefore needs a backing chat client implementing `SupportsChatGetResponse`.

Two candidate clients exist in the GA-track SDK as of `agent-framework` 1.2.2:

1. **`agent_framework_openai.OpenAIChatClient`** — supports both OpenAI (default) and Azure OpenAI deployments via the `azure_endpoint`, `credential`, and `api_version` constructor parameters. State (conversation history, agent session) is **client-side**: every checkpoint taken by `WorkflowBuilder`'s checkpoint hook captures it.
2. **Azure AI Foundry / `FoundryAgent`-style server-side-session agents** — exposed via the `agent-framework-azure-ai` and `agent-framework-foundry` packages. State is held **server-side** at the model endpoint.

The relevant Microsoft Agent Framework documentation (Workflows → Advanced → Agent Executor → Checkpointing) explicitly warns:

> *Checkpointing with agents that use server-side sessions (such as `FoundryAgent`) has limitations. Server-side session state is not captured in checkpoints and can be modified by subsequent runs. Consider implementing a custom executor if you need reliable checkpointing with server-side sessions.*

Feature 033 specifies hard guarantees that are incompatible with that limitation:

- **FR-006 / FR-007**: workflow runs must checkpoint at agent-step boundaries and resume after a process restart with no re-execution.
- **SC-002**: ≥99 of 100 fault-injection trials must successfully resume mid-incident.

Additionally, Constitution NN-2 (Data sovereignty) and FR-025 forbid API-key authentication; all platform service access must use managed identity (Entra ID).

## Decision

All five MAF `Agent` instances will be backed by **`agent_framework_openai.OpenAIChatClient`**, constructed for each environment as:

```python
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from agent_framework_openai import OpenAIChatClient

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default",
)
client = OpenAIChatClient(
    model=<deployment_name_for_tier>,
    azure_endpoint=<environment_aoai_endpoint>,
    api_version="2024-10-21",
    credential=token_provider,
)
```

The `api_key` parameter must never be set. The credential parameter accepts either an `azure.core.credentials.TokenCredential` directly or a callable token provider; both routes are managed-identity-compatible.

`agent-framework-foundry` and `agent-framework-azure-ai` are explicitly out of scope for this feature. The `agent-framework-azure-ai` 1.0.0rc6 release is also incompatible with the installed `agent-framework-core` 1.2.2 (it imports `BaseContextProvider`, which has been renamed to `ContextProvider`); even setting aside the checkpoint concern, that package would not load against our pinned versions.

## Consequences

- ✅ **FR-007 / SC-002 are satisfiable**: all conversational state is client-side and serialisable into the workflow checkpoint, so a kill-and-restart resumes deterministically.
- ✅ **FR-025 / Constitution NN-2** preserved: `DefaultAzureCredential` resolves to managed identity in Azure Container Apps; no API keys appear in code, config, or logs.
- ⚠️ **Trade-off**: we forgo the Azure AI Foundry agent-orchestration features (server-side tool execution, server-side hosted-MCP). Those features map cleanly to MAF's client-side equivalents (`FunctionTool`, `MCPStreamableHTTPTool`) — the migration loses no capability our spec requires.
- ⚠️ **Open follow-up**: when `agent-framework-azure-ai` is rebuilt against `agent-framework-core ≥ 1.2`, we will re-evaluate whether a Foundry-backed evaluation harness adds value alongside (not in place of) the OpenAIChatClient agents.
- ✅ **Cost / latency parity**: the Azure OpenAI deployments referenced by `OpenAIChatClient` are the same deployments the legacy pipeline already uses; SC-007 (≤10% latency regression) is achievable with no model change.

## References

- Microsoft Learn — *Agent Framework — Agent Executor — Checkpointing* (warns about `FoundryAgent` server-side sessions): <https://learn.microsoft.com/agent-framework/workflows/advanced/agent-executor#checkpointing>
- Microsoft Learn — *Agent Framework — Overview*: <https://learn.microsoft.com/agent-framework/overview/>
- `agent-framework-openai` package (PyPI 1.2.2) — `OpenAIChatClient.__init__` signature confirms `azure_endpoint` + `credential` parameters.
- Spec 033 §FR-007, §FR-025, §SC-002.
- Constitution v1.2.0 §Non-Negotiable #2 (Data sovereignty / managed identity).

## Related

- ADR-031 (AZURE_CREDENTIALS MVP carve-out) — runtime-side credentials for Azure resource access; complementary, not in conflict.
- ADR-033-02 (Cosmos checkpoint storage).
- ADR-033-03 (HITL via custom executor + spec-008 envelope).
- ADR-033-04 (MCP Streamable HTTP transport).
