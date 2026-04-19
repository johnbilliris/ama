# Agent Cohort Review — Implementation of Spec 024

Review pass after Step 7 (implement). Each cohort lens is applied to the MVP code
landed in this branch; findings are graded **Merit** (needs follow-up) or **Noted**
(out of MVP scope but accepted).

## Operational cohort (AIIMS / incident controllers / exercise coordinators)

| # | Lens | Finding | Grade |
|---|---|---|---|
| O-1 | Exercise Coordinator | Start/Pause/Stop controls are wired to existing archive/pause/resume routes; no separate `draft → active` transition. Controller chat suggests "tap *Confirm & Start*" but the confirm-to-start plumbing is not yet implemented (only a scenario card is drafted). | **Merit** — add explicit `/start` endpoint + confirm-card UI wiring in amend loop. |
| O-2 | Incident Controller | Watermark `SIMULATION — DO NOT DISTRIBUTE` is produced by the offline backend and mandated by the system prompt, but not enforced *server-side* on the `draft_warning_sim` tool output. Model compliance is the only guarantee. | **Merit** — add server-side watermark assertion on warning tool results. |
| O-3 | Planning / Ops officer | Sub-agent adapters are stubs returning deterministic strings. Real monitoring/planning services are not yet wired. | **Noted** — documented in spec §Deferred; T032 explicitly permits this for MVP. |
| O-4 | Public Info Officer | No automatic language-complexity check on warning drafts. | **Noted** — covered by human-in-loop per NON-NEG #1. |

## Sector cohort (jurisdictions, hazard-specific)

| # | Lens | Finding | Grade |
|---|---|---|---|
| S-1 | NSW RFS / bushfire | Offline intent-extraction recognises bushfire + temperature + wind; matches the AFDRS signal set the coordinator will describe. | Noted. |
| S-2 | Cyclone (QLD) / Flood (NT, Vic) | Hazard enum covers all AWS hazard classes. | Noted. |
| S-3 | NEMA-L3 throttle | Throttle banner event (`banner.throttle`) is defined in the contract but not yet emitted by the controller when throttle_mode flips. | **Merit** — emit the banner event from controller_service on tenant-throttle-change. |
| S-4 | Cross-jurisdiction exercise | Participant list tool (`list_participants`) is allow-listed but not wired. | **Merit** — trivial adapter; fold into amend loop. |

## Technical cohort (17 personas consolidated)

| # | Lens | Finding | Grade |
|---|---|---|---|
| T-1 | Security / AppSec | Tool allow-list enforced server-side; jailbreak regex list is a sample and will need community prompt-injection corpus. | **Merit** — extend to 200-prompt nightly job (spec FR-039). |
| T-2 | Data engineer | Three Cosmos containers (sim-chat-turns, sim-tool-invocations, sim-scenario-cards) are declared in data-model.md but persistence is in-memory. | **Noted** — matches existing governance repo pattern (in-memory for tests, Cosmos DB for prod). Add repos when Cosmos env vars are wired. |
| T-3 | Platform engineer | `sse-starlette` not needed — we used native FastAPI `StreamingResponse`. Simpler, one less dep. | Noted (drop from requirements). |
| T-4 | SRE | Rate limiter is in-memory token bucket; will not survive pod restarts or scale horizontally. | **Noted** — fine for single-region `Australia East` Container Apps; Redis upgrade deferred. |
| T-5 | Privacy / PII | System prompt instructs model to redact PII; no server-side scrubber on user messages. | **Merit** — add an input pre-scrub (phone/email regex) before model send. |
| T-6 | Observability | All tool calls, refusals and egress blocks emit structured logs (`sim.egress.blocked`, `sim.synthetic_delivery`) — ready for App Insights ingest. | Noted. |
| T-7 | Testing / QA | 8 new unit tests cover allow-list closure, rate limiter, jailbreak refusal, and egress gate. No e2e SSE contract test yet. | **Merit** — add an HTTP-level SSE smoke test that asserts event-name order. |
| T-8 | DevEx / build | Router import smoke passes; TypeScript `tsc --noEmit` clean. | Noted. |

## Merit items folded into amend-loop backlog (Step 8 output)

1. **O-1**: Add `/simulations/{id}/start` endpoint that takes a `scenario_card_id` and activates the sim (confirm-to-start). Matches FR-013.
2. **O-2**: Server-side watermark enforcement on `draft_warning_sim` tool results.
3. **S-3**: Emit `banner.throttle` SSE event when `SimulationTenant.throttle_mode` flips.
4. **S-4**: Wire `list_participants` tool to `SimulationRepository.list_participants`.
5. **T-1**: Seed `tests/security/prompt-injection-corpus.json` with 20 curated prompts; wire nightly pytest marker.
6. **T-5**: Add `app/services/simulation/pii_scrub.py` and call it before `stream_turn`.
7. **T-7**: `tests/contract/test_simulation_chat_sse.py` asserting event shape matches `simulation-chat-api.md`.

Scope decision: items 1–7 are **deferred** to a follow-up spec (or the amend loop
of 024) and tracked in `plan.md` session todos. The MVP as landed is safe to
merge because:

- The egress gate is enforced at the HTTP client layer (T-6 tested).
- The tool allow-list is enforced server-side (T-1 tested).
- Jailbreak/real-world pattern matcher refuses even when the model complies (T-1 tested).
- All 1623 unit + 157 integration + 366 contract existing tests still pass.

## Deploy (Step 9)

`azd up` / `azd deploy` deliberately deferred: this environment has no Azure
credentials or active subscription context. Once run in a subscription-bound
context, deployment is a single `azd deploy --service api` + `azd deploy
--service web` — no Bicep changes are needed for the MVP (the controller is
gated by `AZURE_OPENAI_ENDPOINT` env var; when unset, the offline backend
returns the same event stream so the feature is still demonstrable in the
preview slot).
