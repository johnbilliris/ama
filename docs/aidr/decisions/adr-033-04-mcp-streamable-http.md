# ADR-033-04: `MCPStreamableHTTPTool` for the Routing Service

## Status

Accepted

## Context

Feature `033-maf-adoption` (FR-018, FR-019, FR-019a, FR-020, FR-021, US4) requires that out-of-process tools be exposed to agents through a single standard protocol — Model Context Protocol (MCP) — with a per-agent allow-list and pinned major versions. The first such tool in this feature is the routing service.

The MAF Python SDK exposes three MCP tool transports in 1.2.2:

- `agent_framework.MCPStdioTool` — spawns the tool as a sub-process per session over stdio.
- `agent_framework.MCPStreamableHTTPTool` — connects over the MCP HTTP-Streamable transport (HTTP POST + Server-Sent Events).
- `agent_framework.MCPWebsocketTool` — connects over the MCP WebSocket transport.

Operational realities of the routing service:

- Already deployed (or will be) as a long-lived containerised process — ergo not per-session-spawnable.
- Co-located in the same Azure Container Apps environment as the agents app, with internal-only ingress.
- Authenticated via managed identity to its own backing services (Azure Maps, route data store).
- Used by potentially multiple agents per workflow run — bursts of concurrent invocations.

## Decision

The routing service is exposed to MAF agents via **`agent_framework.MCPStreamableHTTPTool`**.

```python
from agent_framework import MCPStreamableHTTPTool

routing_tool = MCPStreamableHTTPTool(
    name="routing_service",
    url="https://ca-routing-mcp-drh-{env}.{region}.azurecontainerapps.io/mcp",
    # Major-version pinning enforced in apps/agents/maf_runtime/mcp/routing_tool.py
    # by reading `tool_registrations` Cosmos container before invocation.
)
```

The routing service container app:

- Internal-only ingress (no public endpoint).
- Managed identity for outbound calls.
- Same RG and region as `ca-agents-drh-{env}`.
- Advertises its semantic version through the MCP `serverInfo` block; consumed by `apps/agents/maf_runtime/mcp/routing_tool.py` (T063) and validated against `pinned_major_version` from the `tool_registrations` Cosmos container (T067).

## Alternatives Rejected

- **`MCPStdioTool`** — assumes the tool is spawnable per-session. Wrong topology for a long-lived containerised service; sub-process startup latency unacceptable for the per-step retry budget (FR-012, 30 s total elapsed); no managed-identity story.
- **`MCPWebsocketTool`** — viable but introduces ingress / load-balancer / connection-state operational complexity without delivering anything HTTP-Streamable does not. Azure Container Apps' default ingress better matches HTTP than WebSockets.
- **HostedMCPTool (Foundry-managed)** — preview-only at the time of writing; would re-introduce the Foundry server-side-session class of tools that ADR-033-01 explicitly rejected; out of scope.
- **Bespoke HTTP client per tool** — explicitly forbidden by FR-018 ("agents MUST NOT contain bespoke per-tool transport or auth code").

## Consequences

- ✅ **Same auth posture as the rest of the platform**: Container-Apps internal ingress + managed identity. No new secret material.
- ✅ **FR-019a (semver pinning)** enforced in our wrapper: agents only invoke a tool whose advertised `serverInfo.version` major matches the allow-list entry.
- ✅ **FR-021 (typed tool failure)** — `MCPStreamableHTTPTool` surfaces typed errors for unreachable / timeout / malformed-response that we re-raise as `ToolUnreachableError` / `ToolTimeoutError` / `ToolMalformedResponseError` from `apps/agents/maf_runtime/errors.py` (T011b, T063 case (e)).
- ⚠️ **Latency**: the HTTP-Streamable transport adds one network hop per tool invocation. The routing service is co-located in the same Container Apps environment, so the hop is intra-VNet and routinely <10 ms; well within the FR-012 30 s per-step budget.
- ⚠️ **Connection lifecycle**: `MCPStreamableHTTPTool` opens a fresh connection per invocation by default. We accept the small connection-setup overhead in exchange for stateless server semantics, which simplifies the routing service's deployment model.
- ✅ **Forward path** to additional MCP tools follows the same pattern: each new tool gets a new entry in the agent's `tool_allow_list` (`agent-definition.schema.yaml`) and a new `tool_registrations` document. No agent code changes.

## References

- `agent_framework.MCPStreamableHTTPTool` (PyPI agent-framework 1.2.2).
- Microsoft Learn — *Using MCP tools with Agents*: <https://learn.microsoft.com/agent-framework/agents/tools/mcp>
- Spec 033 §FR-018, §FR-019, §FR-019a, §FR-021, §SC-006.
- `contracts/tool-registration.schema.json` — composite-id versioning shape.

## Related

- ADR-033-01 (chat client — provides the `Agent` host into which `MCPStreamableHTTPTool` is plugged).
- T062 (routing-service MCP server scaffold).
- T063 (`routing_tool.py` wrapper + version-mismatch enforcement).
- T065 (wiring into Evacuation agent's `tool_allow_list`).
- T066 (Container App Bicep).
- T068 (Application Insights alert on `tool.outcome=version_mismatch`).
