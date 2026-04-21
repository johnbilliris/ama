# Contract: Simulation Chat API

**Phase**: 1 · **Feature**: 024

## POST `/api/v1/simulations/{tenant_id}/chat`

Streaming chat endpoint for the Simulation Controller.

**Auth**: Entra ID bearer token; caller must have `SimulationCoordinator` role on the
referenced simulation (or `SimulationObserver` for read-only transcript retrieval — use GET).

**Request body** (`application/json`):

```json
{ "message": "Start a bushfire exercise near Katoomba at 14:00...", "correlation_id": "uuid-v4" }
```

**Response**: `text/event-stream` (SSE). Events:

| event | data schema | meaning |
|---|---|---|
| `turn.start` | `{ "turn_id": "uuid", "role": "assistant" }` | assistant turn opened |
| `turn.delta` | `{ "turn_id": "uuid", "delta": "text chunk" }` | token stream |
| `tool.call` | `{ "turn_id": "uuid", "tool_call_id": "uuid", "name": "...", "arguments": {...} }` | assistant requested a tool |
| `tool.result` | `{ "tool_call_id": "uuid", "outcome": "ok|refused|error", "result": {...} }` | server executed/refused |
| `card.scenario` | `SimScenarioCard JSON` | structured confirmation card |
| `banner.throttle` | `{ "reason": "nema-l3" }` | auto-throttle active |
| `turn.end` | `{ "turn_id": "uuid", "content_hash": "sha256" }` | assistant turn closed |
| `error` | `{ "code": "...", "message": "..." }` | terminal error |

**Errors**: `401`, `403`, `404 simulation_not_found`, `409 sim_ended`, `429 rate_limited`,
`503 openai_unavailable`.

## GET `/api/v1/simulations/{tenant_id}/chat?after=<turn_id>&limit=50`

Read transcript. Observers allowed. Returns `{ "turns": [...], "next_cursor": "..." }`.

## POST `/api/v1/simulations/{tenant_id}/chat/cancel`

Cancel in-flight turn. `204 No Content`.
