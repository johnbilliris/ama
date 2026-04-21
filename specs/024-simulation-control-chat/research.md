# Research: Simulation Control & Chat Orchestration

**Phase**: 0 · **Feature**: 024 · **Date**: 2026-04-19

## R1. Azure OpenAI chat-completion with tool calling (Python)

- SDK: `openai>=1.40` with `AsyncAzureOpenAI(azure_endpoint=..., api_version="2024-08-01-preview", azure_ad_token_provider=...)`.
- Tool definitions passed as `tools=[{"type":"function","function":{...}}]`; model selects via `tool_choice="auto"`.
- Streaming: `await client.chat.completions.create(stream=True, ...)` returns `AsyncStream`.
- Defence-in-depth: the server iterates tool calls and only dispatches calls whose `name` is in the allow-list; unknown names → `tool_denied` audit event + stock refusal message injected back as tool-result so the model can recover without executing.

## R2. FastAPI SSE streaming

- Library: `sse-starlette`. `EventSourceResponse(async_gen())` lets us stream incremental JSON frames.
- Client (Next.js): `fetch(url, {method:'POST', body, headers:{Accept:'text/event-stream'}})` + `eventsource-parser` NPM library to parse chunks.
- Cancellation handled via `AbortController` on the client; server honours disconnect with `request.is_disconnected()`.

## R3. Prompt injection & jailbreak defence

Reference pattern from Microsoft "Best practices for LLM apps" (Learn) — validated via microsoft-docs skill. Three layers we adopt:

1. **Input content-safety scan** (Azure AI Content Safety, existing deployment).
2. **System-prompt scope lock** — states the assistant is a *Simulation Controller for exercises only*, must never emit real-world dispatch; tools available listed explicitly.
3. **Server allow-list** — *the only source of truth* for which tools can be executed; model output is advisory, not authoritative.

## R4. Redis rate limiting

- Library: `redis.asyncio` + token-bucket Lua script already used elsewhere in the repo.
- Keys: `rl:sim:chat:{tenant_id}:{user_oid}` (30/min) and `rl:sim:chat:{tenant_id}` (120/min).

## R5. Azure Maps Search — geocoding

- REST endpoint `https://atlas.microsoft.com/search/fuzzy/json?api-version=1.0&query=...` with Entra ID token (`scope=https://atlas.microsoft.com/.default`) OR subscription key in Key Vault.
- Fallback: ask coordinator for explicit lat/lon if Search returns no match or times out.

## R6. Sub-agent invocation

The existing monitoring/planning/resources/etc. services expose in-process async APIs (see `apps/api/app/services/*_service.py`). The Controller calls them directly — no new transport — passing `tenant_id` and a correlation ID. Outputs are normalised into a `SubAgentReply` DTO for aggregation.

## R7. Defence-in-depth egress

The existing `PublicationService` already inspects `tenant_id`. We add a second layer — an HTTP client wrapper around `httpx.AsyncClient` — that refuses any outbound request when the current request context is sim-scoped. This is attached via a FastAPI contextvar set by the existing tenancy middleware.

## R8. Audit retention

Cosmos DB container `ttl` at the item level: 63 072 000 s (2 years). Purge is automatic; an audit export nightly job writes to Blob Storage (Australia East) in Parquet for lessons-management.
