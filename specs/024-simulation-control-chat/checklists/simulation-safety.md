# Simulation Safety & Readiness Checklist: Simulation Control & Chat Orchestration

**Purpose**: Verify every safety, audit, comms-block, accessibility, and operational gate for the simulation control & chat orchestration feature before it ships.
**Created**: 2026-04-19
**Feature**: [spec.md](../spec.md)

## Safety & Public-Harm Prevention

- [ ] CHK001 PublicationService rejects every outbound message whose tenant starts with `sim-` and returns `410 SIM_EGRESS_BLOCKED`.
- [ ] CHK002 Outbound HTTP client wrapper (second-layer egress gate) rejects `sim-` tenants before any network request.
- [ ] CHK003 Azure Communication Services, SMS, broadcast, social connectors all honour the tenant gate — verified with integration tests for each channel.
- [ ] CHK004 10 000-message red-team egress fuzz reaches zero real destinations.
- [ ] CHK005 Every blocked message records a `synthetic-delivery` entry with payload hash, intended channel, audience, and block reason.
- [ ] CHK006 Every drafted public-info artefact inside a sim shows the `SIMULATION — DO NOT DISTRIBUTE` watermark in UI, PDF export, and email preview.
- [ ] CHK007 Warning Approve action inside a sim writes `would-have-published` and does not call any transport.

## Chat Controller Hardening

- [ ] CHK008 Controller system prompt is a versioned file in the repo; hash included on every audit record.
- [ ] CHK009 Tool allow-list (`seed_scenario`, `query_sub_agent`, `draft_warning_sim`, `summarise_state`, `pause`, `resume`, `stop`, `list_participants`) is enforced server-side independent of model output.
- [ ] CHK010 Server orchestrator rejects any tool name outside the allow-list with `tool_denied` audit event.
- [ ] CHK011 Jailbreak / red-team test suite contains ≥ 200 prompts and runs on every PR touching simulation code + nightly on `main`.
- [ ] CHK012 Jailbreak refusal rate ≥ 99% on the curated suite.
- [ ] CHK013 Controller refuses and logs any request that would issue real-world dispatch or external communication.
- [ ] CHK014 PII scrubber runs on chat input; transcripts never leave Australian Azure regions.
- [ ] CHK015 Rate limits enforced at (30/min/user/sim) and (120/min/tenant) with reject-with-retry-after semantics.

## Lifecycle & Control

- [ ] CHK016 State machine enforces `draft → active → paused ⇄ active → ended`; `ended` is terminal.
- [ ] CHK017 Start/Pause/Resume/Stop controls require `SimulationCoordinator` Entra ID role.
- [ ] CHK018 Exactly one primary coordinator per simulation; hand-over flow tested.
- [ ] CHK019 Stop cancels all in-flight sub-agent queries with outcome `cancelled-by-stop`.
- [ ] CHK020 NEMA-Level-3 auto-throttle engages within 5 s and the UI banner is non-dismissible.
- [ ] CHK021 During throttle only `summarise_state`, `pause`, `stop` tools are honoured.
- [ ] CHK022 24-hour idle auto-pause works and notifies the coordinator.

## Sub-agent Coordination

- [ ] CHK023 Controller can successfully invoke each of Monitoring, Planning, Resource Allocation, Communication, Evacuation, Risk Assessment agents with simulation tenant context.
- [ ] CHK024 Every sub-agent invocation + response is logged with correlation IDs.
- [ ] CHK025 Controller aggregates sub-agent output with citations the user can inspect.
- [ ] CHK026 Unknown / hallucinated sub-agent IDs are refused cleanly.
- [ ] CHK027 Sub-agent timeouts (>120 s) surface a graceful error and mark reply `degraded`.

## Observability & Audit

- [ ] CHK028 Every chat turn, tool invocation, and state transition is reconstructable from the audit trail.
- [ ] CHK029 Application Insights events tagged with `tenant_id` and `simulation=true`.
- [ ] CHK030 Chat transcripts + audit artefacts retained for 2 years then purged; purge job tested.
- [ ] CHK031 Data sovereignty: all transcripts demonstrably stored in Australia East / Southeast.
- [ ] CHK032 Observer role can read transcript + map overlay but not send.

## Map Overlay (spec 020 integration)

- [ ] CHK033 `active`, `paused`, `ended` sims each render a visually distinct overlay with `SIM` / `SIM · PAUSED` badge.
- [ ] CHK034 Legend entry explains each style; contrast ≥ 4.5:1.
- [ ] CHK035 Clicking a sim overlay opens a side panel linking to the sim detail screen.
- [ ] CHK036 Ended sims > 24 h hidden by default; toggle reveals them.
- [ ] CHK037 Overlay never displaces live incident styling.

## Accessibility (WCAG 2.2 AA)

- [ ] CHK038 Sim detail screen + map overlay pass axe + manual audit with zero critical findings.
- [ ] CHK039 Chat input is keyboard-navigable, properly labelled, with visible focus states.
- [ ] CHK040 `SIM` badge announces as "simulation" to screen readers.
- [ ] CHK041 `prefers-reduced-motion` disables overlay striping animation.
- [ ] CHK042 Colour is never the sole channel for state (text label accompanies every pill/badge).

## Graceful Degradation

- [ ] CHK043 When Azure OpenAI is unreachable, chat becomes read-only with a banner; all other controls stay live.
- [ ] CHK044 When Azure Maps Search fails, the Controller prompts the coordinator for lat/lon.
- [ ] CHK045 When a sub-agent is unreachable, Controller returns cached last-known state tagged `degraded`.

## Ops & Release

- [ ] CHK046 Bicep/Terraform includes simulation-related env vars (model deployment, content-safety endpoint, region pinning to Australia East).
- [ ] CHK047 `azd up` / `azd deploy` succeeds on clean env.
- [ ] CHK048 Health endpoint reports Controller availability and tool-allow-list version.
- [ ] CHK049 Runbook exists for "sim egress leak suspected" incident.
- [ ] CHK050 Post-exercise report generator produces a report record on Stop.

## Notes

- Items are gated: CHK001–CHK007 (safety) and CHK043 (degradation) are release-blocking by Constitution NON-NEGOTIABLE requirements.
- Mark items `[x]` during `/speckit.implement` and again in agent-review.
