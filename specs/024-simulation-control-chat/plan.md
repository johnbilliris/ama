# Implementation Plan: Simulation Control & Chat Orchestration

**Branch**: `024-simulation-control-chat` | **Date**: 2026-04-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/024-simulation-control-chat/spec.md`

## Summary

Add a chat-driven Simulation Controller to the simulations detail screen. The Controller is
an Azure OpenAI chat-completion assistant, hardened by (a) a versioned system prompt stored
in-repo, (b) a server-side **tool allow-list** that is enforced independently of the model's
output, and (c) a rate limiter. Coordinators author scenarios in natural language; the
Controller confirms with a structured scenario card, then invokes existing sub-agents
(Monitoring, Planning, Resource Allocation, Communication, Evacuation, Risk Assessment) via
the `query_sub_agent` tool. Start / Pause / Resume / Stop controls are exposed on the detail
screen and wired into the simulation state machine. The Disaster Mapper page (spec 020) gets
a new `sim-overlay` layer. Public-facing communications are hard-blocked for any `sim-*`
tenant at two independent egress points: the `PublicationService` **and** the outbound HTTP
client wrapper. Every chat turn, tool call, state transition, and blocked outbound message
is recorded in the simulation audit trail for 2 years.

## Technical Context

**Language/Version**: TypeScript 5.8 (Next.js 16 / React 19) · Python 3.12 (FastAPI)
**Primary dependencies**: `openai>=1.40` (Azure OpenAI via `AsyncAzureOpenAI`),
`azure-identity`, `azure-maps-search`, `azure-cosmos`, `azure-monitor-opentelemetry`,
`fastapi`, `pydantic v2`, `sse-starlette` (chat streaming). Frontend: `@azure/maps-control`
(already in use), `eventsource-parser` for SSE consumption, `@radix-ui` primitives for chat
shell (already in design system).
**Storage**: Cosmos DB `disaster-hub` database. New containers:
- `sim_chat_turns` (partition key: `/tenant_id`)
- `sim_tool_invocations` (partition key: `/tenant_id`)
- `sim_synthetic_deliveries` (partition key: `/tenant_id`)
**Testing**: pytest (unit + contract + integration + sim-mode), Playwright (e2e), axe-core
(accessibility), `promptfoo` / custom harness for the jailbreak suite.
**Target platform**: Web (desktop + tablet; minimum 360 px viewport for the control bar).
**Project type**: pnpm monorepo (existing — `apps/web`, `apps/api`, `packages/ui`, `packages/domain`).
**Performance goals**: Scenario-card round-trip ≤ 8 s P95; sub-agent query ≤ 10 s P95 (SC-003);
control bar reaction ≤ 500 ms; egress block decision ≤ 5 ms P99.
**Constraints**: Data sovereignty (Australia East / Southeast only). WCAG 2.2 AA. Rate limits
30/min/user/sim + 120/min/tenant. No non-Azure model providers.
**Scale/Scope**: Up to 10 concurrent active simulations; ≤ 1 primary coordinator per sim;
≤ 50 observers per sim; ≤ 30 chat turns/min/user; ≤ 120/min global.

## Consolidated technical-cohort input (17 personas)

| Persona | Key commitment reflected in this plan |
|---|---|
| Solution Architect | Reuse spec 007 tenant model and spec 014 OpenAI deployment; no new Bicep module for Azure OpenAI. |
| Azure Principal Architect | Pin region Australia East; enable private endpoint on Azure OpenAI; Key Vault-backed endpoint+API-key+model-name. |
| AI/ML Engineer | System prompt hash in audit trail; content-safety input+output filters; function-calling with enforced allow-list. |
| API Architect | POST streaming endpoint `POST /api/v1/simulations/{tenantId}/chat` (SSE); control endpoints `POST /.../start|pause|resume|stop`. |
| Security Engineer | Second-layer egress gate in the outbound HTTP client wrapper (`app/clients/outbound_http.py`); explicit tenant claim from Entra ID; RBAC guards on every route. |
| Data Engineer | New Cosmos containers; retention TTL = 63 072 000 s (2 years); `sim_synthetic_deliveries` indexed by channel + created_at. |
| SRE | SLOs: chat P95 ≤ 10 s, control P95 ≤ 0.5 s, error budget 1%/mo; chaos drill "OpenAI down" in quarterly game day. |
| DevOps / Infra | CI step runs jailbreak suite; `azd` env vars: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_MAPS_CLIENT_ID`. |
| UX | Chat pane right-docked 420 px; control bar sticky top; follow disaster-hub design tokens; reduced-motion disables stripe animation. |
| QA | pytest + playwright coverage; contract tests for each tool; jailbreak suite `tests/security/jailbreak/`. |
| Accessibility | aria-live="polite" for Controller replies; axe audit in CI. |
| Compliance Auditor | 2-year retention documented; data residency attested; audit export formatted for lessons-management. |
| Principal Engineer | No ad-hoc `requests.post` allowed inside simulation path — only the wrapped client. Lint rule added. |
| Chaos Engineer | Sub-agent failure injection; OpenAI 429 injection; egress-bypass attempt. |
| Docker Container Engineer | No new container image; extend existing `apps/api` image; ensure OpenTelemetry exporter configured. |
| Product Owner / BA | Re-map SC-001..SC-008 to acceptance tests in tasks.md. |
| Software Developer | Thin FastAPI route → service → repository pattern; Pydantic v2 models. |

## Constitution Check

| # | Constitution Requirement | Alignment | Status |
|---|---|---|---|
| 1 | Human-in-the-loop (NON-NEG 1) | FR-005/006/009/033 — assistant confirms state changes; tool allow-list server-enforced; Approve never publishes. | ✅ PASS |
| 2 | Data sovereignty (NON-NEG 2) | FR-024 — all chat + audit in Australia East; Azure OpenAI deployment pinned; Azure Maps Australia East. | ✅ PASS |
| 3 | Privacy by design (NON-NEG 3) | PII scrubber on chat input; 2-year retention with automatic purge (FR-031). | ✅ PASS |
| 4 | Interoperability (NON-NEG 4) | Warning drafts use AWS-compliant structure; FastAPI OpenAPI exposed. | ✅ PASS |
| 5 | Graceful degradation (NON-NEG 5) | FR-034 — OpenAI-down fallback; chaos drill enumerated. | ✅ PASS |
| 6 | Azure-native (Section VIII) | Azure OpenAI, Azure Maps, Azure Cosmos, Azure Monitor. | ✅ PASS |
| 7 | Transparency & Auditability (Section IV) | FR-007/013/037 — transcript hash, prompt hash, tool correlation IDs. | ✅ PASS |
| 8 | AWS three-tier (Section V-A) | Draft warnings use Advice / Watch and Act / Emergency Warning + watermark. | ✅ PASS |
| 9 | Quality gates | Lint, unit, contract, integration, e2e, jailbreak in CI. | ✅ PASS |

**Gate result: ALL PASS — proceed.**

## Project Structure

```text
specs/024-simulation-control-chat/
├── plan.md                          # this file
├── research.md                      # Phase 0 research summary
├── data-model.md                    # Phase 1 entities
├── quickstart.md                    # developer run-through
├── contracts/
│   ├── simulation-chat-api.md       # SSE + JSON contracts
│   └── simulation-control-api.md    # start/pause/resume/stop contracts
├── checklists/
│   ├── requirements.md
│   └── simulation-safety.md
└── tasks.md                         # produced by /speckit.tasks
```

### Source-code additions

```text
# Backend (apps/api)
apps/api/app/
├── clients/
│   └── outbound_http.py             # NEW — wrapped HTTP client with sim-egress gate
├── services/simulation/
│   ├── __init__.py                  # NEW
│   ├── controller_prompt.md         # NEW — hardened system prompt (versioned)
│   ├── controller_tools.py          # NEW — tool allow-list + schemas
│   ├── controller_service.py        # NEW — Azure OpenAI chat orchestrator
│   ├── sub_agent_invoker.py         # NEW — bridge to Monitoring/Planning/etc.
│   ├── scenario_card.py             # NEW — Pydantic model for confirm card
│   ├── rate_limiter.py              # NEW — per-user-sim + per-tenant limits
│   ├── synthetic_delivery_service.py# NEW — block + record outbound
│   └── location_resolver.py         # NEW — Azure Maps Search wrapper
├── api/routes/
│   ├── simulation_chat.py           # NEW — POST /simulations/{tid}/chat (SSE)
│   └── simulation_control.py        # NEW — POST /simulations/{tid}/{start|pause|resume|stop}
├── repositories/
│   ├── sim_chat_repository.py       # NEW — Cosmos container sim_chat_turns
│   ├── sim_tool_repository.py       # NEW — Cosmos container sim_tool_invocations
│   └── sim_egress_repository.py     # NEW — Cosmos container sim_synthetic_deliveries
└── middleware/
    └── sim_egress_middleware.py     # NEW — second-layer gate for egress HTTP

# Domain (packages/domain)
packages/domain/src/domain/models/
├── sim_chat_turn.py                 # NEW
├── sim_tool_invocation.py           # NEW
├── sim_scenario_card.py             # NEW
└── sim_synthetic_delivery.py        # NEW

# Frontend (apps/web)
apps/web/src/
├── app/simulations/[tenantId]/
│   ├── page.tsx                     # EXTEND — add chat pane + control bar
│   └── _components/
│       ├── ControlBar.tsx           # NEW
│       ├── ChatPane.tsx             # NEW
│       ├── ScenarioConfirmCard.tsx  # NEW
│       └── NemaThrottleBanner.tsx   # NEW
├── app/disasters/
│   └── _components/SimOverlayLayer.tsx # NEW — map layer addition
└── lib/api/simulation_chat.ts       # NEW — SSE client

# Shared UI (packages/ui)
packages/ui/src/components/chat/
├── ChatShell.tsx                    # NEW — a11y-correct chat container
├── ChatMessage.tsx                  # NEW
└── SimWatermark.tsx                 # NEW — "SIMULATION — DO NOT DISTRIBUTE" banner

# Tests
tests/
├── contract/simulation_chat/        # API contracts
├── integration/simulation_control/  # lifecycle + coordination
├── security/jailbreak/              # ≥200 adversarial prompts
├── security/egress_block/           # 10 000 fuzz messages
├── e2e/simulation_chat.spec.ts      # Playwright coordinator journey
└── unit/simulation/                 # tool allow-list, rate limiter, etc.

# Infrastructure (infra/)
infra/modules/
├── openai.bicep                     # UPDATE — add deployment if not present
└── simulation_telemetry.bicep       # NEW — App Insights custom dimension setup
```

## Phase 0 — Research (baseline)

1. **Azure OpenAI chat-completion with function calling** — Python SDK `openai>=1.40` supports
   tool/function calling with Azure. Reuse the deployment from spec 014.
2. **SSE streaming from FastAPI** — `sse-starlette` `EventSourceResponse` is stable and
   handles cancellation cleanly. Browser consumption via native `EventSource` or
   `fetch + ReadableStream`; we'll use `fetch` + `eventsource-parser` for POST SSE.
3. **Prompt-injection defence** — two layers: (a) content safety on the *input*; (b) server
   tool-allow-list ignores any function call the model fabricates outside the registered set.
4. **Rate-limiting** — token-bucket in Redis (already provisioned), shared across API pods.
5. **Azure Maps Search REST API** — authenticate via Entra ID (`Azure Maps Data Reader`).

## Phase 1 — Design artefacts

`research.md`, `data-model.md`, `contracts/*.md`, `quickstart.md` produced in same commit as
this plan. Minimal enough to drive `/speckit.tasks` without duplicating requirements content.

## Complexity Tracking

| Area | Rationale | Mitigation |
|---|---|---|
| Two-layer egress gate | Defence in depth for constitutional NON-NEG 1 | Single shared helper; unit tests for every channel |
| SSE chat | Streaming UX + cancellation | `sse-starlette` + abort controller; tested with Playwright |
| Jailbreak suite in CI | 200+ prompts adds ~3 min to pipeline | Nightly on main; PR path uses curated 50-prompt subset |
| Sub-agent fan-out | 6 agents — risk of cascading latency | Parallel `asyncio.gather` with 10 s soft deadline, 120 s hard cap |
