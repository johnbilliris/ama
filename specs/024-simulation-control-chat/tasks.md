# Tasks: Simulation Control & Chat Orchestration

**Feature**: 024 · **Branch**: `024-simulation-control-chat` · **Plan**: [plan.md](./plan.md)

Tasks are dependency-ordered. `[P]` = parallelisable within a phase.

## Phase A — Domain & data stores

- **T001 [P]** Add Pydantic models under `packages/domain/src/domain/models/`: `SimChatTurn`, `SimToolInvocation`, `SimScenarioCard`, `SimSyntheticDelivery` (per `data-model.md`).
- **T002 [P]** Add `draft`, `ended` statuses to `SimulationTenant` enum; update validators to reject illegal transitions.
- **T003** Create Cosmos containers `sim_chat_turns`, `sim_tool_invocations`, `sim_synthetic_deliveries` (Bicep module + migration script; TTL 63072000 s; `/tenant_id` partition key).
- **T004 [P]** Repositories: `sim_chat_repository.py`, `sim_tool_repository.py`, `sim_egress_repository.py` (async CRUD + cursor paging).

## Phase B — Safety gates (egress block) — RELEASE-BLOCKING

- **T010** Implement `apps/api/app/clients/outbound_http.py` — wraps `httpx.AsyncClient`; inspects request tenant contextvar; raises `SimEgressBlocked` for `sim-*`.
- **T011** Implement `synthetic_delivery_service.py` — records every block in `sim_synthetic_deliveries` with payload hash + channel + reason.
- **T012** Update `PublicationService` (spec 008) to call `synthetic_delivery_service.record_and_block()` when tenant is `sim-*`.
- **T013** Replace every existing `httpx`/`requests` outbound call in the simulation path with the wrapped client. Add a ruff/eslint custom lint rule to forbid raw `httpx.AsyncClient()` inside `apps/api/app/services/simulation/`.
- **T014 [P]** Add `sim_egress_middleware.py` — final-resort FastAPI middleware that sets the tenant contextvar on every request.

## Phase C — Rate limiter & location resolver

- **T020 [P]** `rate_limiter.py` — Redis token bucket, two limits (`30/min/user/sim`, `120/min/tenant`).
- **T021 [P]** `location_resolver.py` — Azure Maps Search wrapper with fallback to user-provided lat/lon; uses wrapped outbound client so sim-egress still records.

## Phase D — Simulation Controller (Azure OpenAI orchestrator)

- **T030** Author `controller_prompt.md` — hardened system prompt with: role lock, tool list, refusal rules, watermark requirement, state-change confirmation.
- **T031** `controller_tools.py` — Pydantic schemas + JSON schemas for each allow-listed tool; central registry.
- **T032** `sub_agent_invoker.py` — adapters to `MonitoringService`, `PlanningService` (if present) / fallback to existing equivalents, `RecommendationService`, `PublicAlertService`, `EvacuationService`, `RiskAssessmentService`. Normalise results to `SubAgentReply`.
- **T033** `controller_service.py` — Azure OpenAI chat-completion orchestrator:
  - Loads prompt + records its hash on every turn.
  - Runs input through Content Safety (existing integration).
  - Streams model output; emits SSE events per contract.
  - On each tool call: validate against allow-list; dispatch via orchestrator (NOT model output); record invocation.
  - Aggregates sub-agent output with citations.
  - Enforces rate limiter; returns 429 via SSE `error` event when tripped.
- **T034 [P]** Scenario-card renderer — validates Controller's `seed_scenario` tool arguments into a `SimScenarioCard` Pydantic model.
- **T035 [P]** Unknown-tool refusal path: server emits stock refusal + audit entry; inject tool-result back so the model can recover.

## Phase E — Lifecycle control endpoints

- **T040** `simulation_control.py` route module — `start`, `pause`, `resume`, `stop`, `handover`; integrate with `SimulationService` and the extended state machine.
- **T041** On `stop`: cancel in-flight sub-agent tasks (asyncio task registry keyed by `simulation_id`); write `cancelled-by-stop` outcomes.
- **T042** NEMA Level-3 throttle integration: on declaration, downgrade tool allow-list to `summarise_state|pause|stop`; emit SSE `banner.throttle`.

## Phase F — Chat endpoint (SSE)

- **T050** `simulation_chat.py` route — POST streaming, GET transcript, POST cancel. Reuses `controller_service`.
- **T051** Route auth — require `SimulationCoordinator` for POST; `SimulationObserver` for GET; enforce `primary-coordinator` claim for POST.
- **T052** Register routes in `apps/api/app/api/router.py`.

## Phase G — Frontend (Next.js)

- **T060** `apps/web/src/lib/api/simulation_chat.ts` — typed SSE client with `eventsource-parser`.
- **T061** `ControlBar.tsx` — Start / Pause / Resume / Stop buttons with role gating; shows status pill.
- **T062** `ChatPane.tsx` — chat shell with streaming assistant messages, tool-call bubbles, scenario-card component, inline approve/discard for drafted warnings (approve writes `would-have-published`).
- **T063** `ScenarioConfirmCard.tsx` — renders the structured card; Confirm & Start button.
- **T064** `NemaThrottleBanner.tsx` — non-dismissible banner when `banner.throttle` received.
- **T065** Simulation detail page composition (`app/simulations/[tenantId]/page.tsx`) — add right-docked chat + top control bar; preserve existing lists.
- **T066 [P]** Shared `ChatShell` + `ChatMessage` + `SimWatermark` in `packages/ui/src/components/chat/`.

## Phase H — Disaster Map overlay (spec 020 extension)

- **T070** Data API: extend `/api/v1/incidents/map` OR add `/api/v1/simulations/map` returning sim overlays (GeoJSON + status).
- **T071** `SimOverlayLayer.tsx` — distinct styling per status (`active|paused|ended`); `SIM` / `SIM · PAUSED` badges.
- **T072** Legend entry + "Show ended simulations" toggle (default off for >24 h old).
- **T073** Side panel deep-link to `/simulations/{tenantId}`; read-only view for observers.

## Phase I — Tests

- **T080 [P]** Unit: tool allow-list, rate limiter, location resolver fallback, scenario-card validation, egress wrapper.
- **T081 [P]** Contract: `tests/contract/simulation_chat/` — SSE event shapes; `tests/contract/simulation_control/` — state transitions.
- **T082 [P]** Integration: full happy path (chat → seed → start → query sub-agent → stop); NEMA-Level-3 throttle; handover.
- **T083** Security / egress: `tests/security/egress_block/test_fuzz.py` — 10 000 message fuzz must produce 0 real deliveries (mock transports assert-on-call).
- **T084** Security / jailbreak: `tests/security/jailbreak/test_suite.py` — ≥ 200 adversarial prompts; refusal rate ≥ 99%; runs on PR + nightly.
- **T085** Accessibility: axe in Playwright for simulation detail screen + sim overlay panel; zero critical findings.
- **T086** E2E Playwright: coordinator journey — create sim → chat → confirm card → start → observe sub-agent reply → pause → stop.
- **T087** Frontend degradation: when chat endpoint returns `503 openai_unavailable`, ChatPane switches to read-only with a banner; Start/Pause/Stop + map + sub-agent summaries remain functional (FR-034).
- **T088** Transcript export: "Download transcript" action on sim detail screen produces a printable HTML and Markdown bundle with the `SIMULATION — DO NOT DISTRIBUTE` watermark (FR-030).

## Phase J — Observability & infra

- **T090** Application Insights: custom dimensions `tenant_id`, `simulation=true`, `tool_name`, `sub_agent`.
- **T091** `infra/modules/simulation_telemetry.bicep` — workbook + alert rules (egress-blocked spike, jailbreak-refusal drop, rate-limit saturation).
- **T092** `azd up` / `azd deploy` env vars documented in `infra/` and `azure.yaml`.
- **T093** CI wiring: add GitHub Actions jobs `sim-jailbreak-pr` (50-prompt fast subset on PR), `sim-jailbreak-nightly` (full ≥200-prompt suite nightly), `sim-egress-fuzz` (PR + nightly). Block merges on failure for PR jobs.

## Phase K — Docs & runbook

- **T100** Update root README with "Simulations Chat" section + link to `specs/024-simulation-control-chat/quickstart.md`.
- **T101** Runbook `docs/runbooks/sim-egress-leak.md` — response steps if a synthetic-delivery record reaches a real destination.

## Dependencies (high-level)

```text
A → B → C → D → (E ‖ F) → G → H → I → J → K
              (D needs A,B,C; E needs D; F needs D,E)
```

Items marked `[P]` are parallelisable within their phase.
