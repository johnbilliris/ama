# Routing service MCP server (T062, spec 033)

This is the first out-of-process MCP tool consumed by the AMA MAF agents.

## Run locally

```bash
cd tools/routing_mcp_server
pip install -e .
python -m routing_mcp_server.server --port 9000
```

The server advertises semantic version `1.0.0`. The agent runtime allow-list
validates the major version on every call (FR-019a). A breaking change MUST
be released as a major-version bump and registered as a NEW
`tool_registrations` entry.
