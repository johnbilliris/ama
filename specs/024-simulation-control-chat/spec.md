# Feature Specification: Simulation Control & Chat Orchestration

**Feature Branch**: `024-simulation-control-chat`
**Created**: 2026-04-19
**Status**: Draft
**Input**: User description: "Add chat-driven simulation control (start/pause/stop, natural-language scenario setup, hardened Azure OpenAI orchestrator coordinating monitoring/planning/resource-allocation agents) to the Simulations page, with map overlay and strict blocking of public communications during simulation."

## Overview

The Simulations page today lets an authorised exercise coordinator create, pause, resume, archive
and delete a simulation tenant (see spec 007 *Simulation-as-Tenant*). This feature layers on
**natural-language control**: within a single Simulation detail screen the coordinator can

1. **Start / Pause / Stop** a simulation with explicit, auditable state transitions.
2. **Chat in natural language** with a **Simulation Controller agent** — an Azure OpenAI
   chat-completion model hardened by a system prompt that is STRICTLY scoped to simulation
   authoring and orchestration. The coordinator types *"Start a Cat-3 bushfire exercise near
   Katoomba NSW at 14:00; strong northerlies 55 km/h, 39 °C, RH 8 %, fuel load heavy"* and
   the Controller translates that intent into a scenario timeline, seed signals, and tasking
   for the existing sub-agents (Monitoring, Planning, Resource Allocation, Communication,
   Evacuation, Risk Assessment).
3. **Watch the Disaster Map** render simulation overlays (active, paused, ended) alongside
   live incidents, visually distinct and labelled `SIM`.
4. **Trust** that simulated public warnings, SMS, email, broadcast, and social posts are
   hard-blocked from reaching the real public at every egress point.

This is an operator-facing addition; it does NOT change the tenant-isolation guarantees of
spec 007, it RE-USES the Azure OpenAI deployment scoped in spec 014, and it EXTENDS the map
layer catalogue of spec 020.

### Consolidated agent-cohort inputs

Per the author's direction, every agent persona under `.github/agents/operational/` and
`.github/agents/sectors/` was considered. To keep this spec tractable we consolidated the 77
persona files into the cohorts below; each cohort's concerns appear in the requirements.

| Cohort | Key asks that shaped this spec |
|---|---|
| **AIIMS operational (Incident Commander, Ops, Planning, Logistics, PIO, Field Coord, Executive, Risk, Observer, Resilience Planner)** | Sim must mirror real AIIMS control/coordination; chat must NEVER issue irreversible real-world orders; every Controller action must be logged with provenance; Observer must have a read-only trace view. Public Information Officer insisted that any warning drafted inside a sim be watermarked `SIMULATION — DO NOT DISTRIBUTE`. |
| **NSW sector (FRNSW, NSW RFS, NSWPF, NSW Amb, SES NSW, Marine Rescue NSW)** | Bushfire and flood scenarios dominate; chat must understand NSW-specific terminology (SFAZ, LGA, RFS districts). Combat-agency mapping must match state plans. |
| **VIC sector (CFA, FRV, Vic Pol, Vic Amb, SES VIC)** | CFA/FRV boundary logic, FireReady-style warning categories, Code Red day modelling. |
| **QLD sector (QFD, QPS, QAS, SES QLD)** | Cyclone scenarios; storm-tide surge; TC category parameters must be selectable via chat. |
| **SA / WA / TAS / NT / ACT sectors** | Jurisdictional parity — every state/territory must be a valid `jurisdiction` param in chat; DFES WA (single combined agency) must not be forced into the NSW-style split. NT cyclone pathway must exist. |
| **Commonwealth (NEMA, ADF, AFP, BOM, GA, ARC, ABF, ASA, RFDS, SLS, SJA)** | BOM must be a first-class *source* of synthetic weather in a sim; NEMA escalation pathway (Level 3) must be simulate-able; ADF DACC requests must be authored only as sim artefacts. |
| **Cross-sector (Local gov, State gov, Territory gov, Health, Transport, Utility, Community NGOs, Volunteers)** | Multi-agency interoperability. Simulations must allow multiple participating orgs; chat must understand "evacuate via V/Line", "open EvacCentre Leeton Showground", etc. |
| **Technical cohort (Solution Arch, Azure Principal Arch, AI/ML, API, Security, Data, SRE, DevOps, UX, QA, Accessibility, Compliance, Principal Engineer, Chaos, Container, Product Owner, Software Dev)** | See `plan.md` in step 4 — technical requirements are not in this spec. Security required real-world egress lock; AI/ML required system-prompt hardening + jailbreak tests; UX required WCAG 2.2 AA; QA required contract + integration + sim-mode tests. |

### Assumptions

- **A1**: Simulation tenants are already created and authenticated via spec 007 mechanisms.
  This feature does not alter tenant provisioning.
- **A2**: The hub runs on Azure; Azure OpenAI (gpt-4o-mini or equivalent, deployed in
  Australia East) is reachable via the same deployment used by spec 014.
- **A3**: Only users with the `SimulationCoordinator` role (Entra ID app role) may Start/
  Pause/Stop a simulation or send chat messages to the Controller. `SimulationObserver`
  users may read the chat transcript and map overlay but not send.
- **A4**: The existing `PublicationService` enforces the comms-block for spec 007. This
  feature extends that enforcement and adds a synthetic-delivery receipt visible in-sim.
- **A5**: Disaster map page (spec 020) already renders tenant-scoped layers; this feature
  adds a `simulation-overlay` layer source.
- **A6**: Simulations run at wall-clock speed by default; a future enhancement may allow
  accelerated time. Out-of-scope here.

## Clarifications

### Session 2026-04-19 (pass 2)

- Q: What happens to in-flight sub-agent queries when the coordinator clicks Stop? → A: Cancel in-flight; record the outcome as `cancelled-by-stop`; idempotent completion writes are allowed for safety.
- Q: Where does the Simulation Controller system prompt + tool manifest live? → A: Versioned file in repo at `apps/api/app/services/simulation/controller_prompt.md`, loaded at startup; the prompt hash is recorded on every chat turn for auditability.
- Q: Is the 30 msgs/min rate-limit per user, per sim, or per tenant? → A: Per user per sim (30/min) AND a global per-tenant cap of 120/min to protect shared Azure OpenAI quota.
- Q: When and how often does the jailbreak suite run? → A: On every PR that touches simulation code plus nightly on `main`; minimum 200 prompts; regressions block merge.
- Q: How is the NEMA-Level-3 auto-throttle surfaced in the sim UI? → A: Non-dismissible banner on the sim detail screen + toast + audit event; during the throttle the chat accepts only `summarise_state`, `pause`, and `stop` tools.



## User Scenarios & Testing *(mandatory)*

### User Story 1 — Start a simulation via chat, in natural language (Priority: P1)

An authorised Exercise Coordinator opens the Simulations page, picks *"New Simulation"*,
and is taken to a detail screen with a chat pane on the right and a Start/Pause/Stop
control bar on top. They type: *"Start a bushfire exercise: Katoomba NSW, start at now + 5
minutes, severe fire danger, NW winds 55 km/h gusts 80, temp 39 °C, RH 8 %, fuel load heavy
continuous eucalypt, threat approach from the west."* The Simulation Controller confirms
the interpreted scenario as a structured card (location, time, hazard class, weather, fuel,
threat vector), asks for confirmation, then on approval calls the Monitoring agent to seed
synthetic BOM + sensor signals, Planning agent to propose initial IAP, and Resource Allocation
to propose tasking.

**Why this priority**: This is the core value — translating natural language into a running,
coordinated simulation. Without this, the feature does not exist.

**Independent Test**: With a pre-existing simulation tenant, sending the above chat message
results in (a) a structured scenario card presented back to the user, (b) on confirmation,
the simulation status transitions to `active`, (c) synthetic signals appear only in the sim
tenant partition, (d) sub-agent tasking records appear in the sim audit trail, (e) the
Disaster Map shows a `SIM` overlay at Katoomba within 10 seconds.

**Acceptance Scenarios**:

1. **Given** a `SimulationCoordinator` user on a new (draft) simulation, **When** they submit
   the bushfire-Katoomba chat message, **Then** the Controller returns a structured scenario
   card within 8 seconds and the simulation remains in `draft` until the user confirms.
2. **Given** a drafted scenario card, **When** the user taps *"Confirm & Start"*, **Then**
   the simulation transitions to `active`, synthetic BOM / IoT signals begin streaming into
   the sim tenant partition, and the Planning + Resource Allocation + Monitoring agents each
   log an initial action within 30 seconds.
3. **Given** a malformed or out-of-scope request (e.g., *"order the ADF to actually deploy"*),
   **When** the user sends it, **Then** the Controller refuses with a scoped, helpful message
   and logs a `refusal` audit event — it NEVER emits a real-world instruction.
4. **Given** an already-active simulation, **When** the user sends further chat (*"add a spot
   fire 3 km south"*), **Then** the Controller appends to the running scenario and the new
   signals are tenant-scoped; live operators see nothing change.

### User Story 2 — Pause and stop a running simulation (Priority: P1)

The Exercise Coordinator clicks **Pause** on the control bar. The simulation enters `paused`:
synthetic signal generation halts, sub-agents finish their in-flight cycle and idle, the
chat remains available for annotations but executes no tasking. On **Stop**, the simulation
enters `ended` (terminal); a post-exercise report is queued.

**Why this priority**: Operator control is non-negotiable; an uncontrollable simulation is
worse than no simulation.

**Independent Test**: From an `active` sim, click Pause → within 5 seconds all synthetic
emitters quiesce and the status pill shows `paused`; click Resume → emitters restart within
5 seconds; click Stop → status becomes `ended`, no further emitters run, and the chat input
is disabled with an explanatory message.

**Acceptance Scenarios**:

1. **Given** an `active` simulation, **When** the coordinator clicks Pause, **Then** status
   becomes `paused`, no new synthetic signals are emitted, the Controller refuses tasking
   chat messages (but allows notes), and the map overlay colour changes to the paused style.
2. **Given** a `paused` simulation, **When** the coordinator clicks Resume, **Then** status
   returns to `active` and signal generation resumes from the paused state (no duplicate
   replay of past signals).
3. **Given** any simulation in `active` or `paused`, **When** the coordinator clicks Stop,
   **Then** status becomes `ended`, all emitters stop, the sub-agents release locks, the
   chat input is disabled, and a post-exercise report record is created with the final
   audit trail reference.
4. **Given** a live incident is activated by NEMA at Level 3 while a simulation is `active`,
   **When** the throttling policy from spec 007 kicks in, **Then** the sim auto-throttles
   (no pause) and the coordinator sees a banner explaining the degradation.

### User Story 3 — Sub-agent coordination during the exercise (Priority: P1)

During an active simulation the Controller acts as a conversational hub: the user asks
*"what's planning recommending?"*, *"are we short on tankers?"*, *"give a PIO draft warning"*
and the Controller relays to the right sub-agent, returns the result in natural language,
and records each relay in the audit trail. The sub-agents are the existing Monitoring,
Planning, Resource Allocation, Communication, Evacuation, and Risk Assessment agents (specs
010, 008, 011, 009, 012), invoked with simulation tenant context.

**Why this priority**: The user request explicitly calls for chat-mediated coordination
between sub-agents. Without it, the chat is just a scenario seeder, not an operations hub.

**Independent Test**: Submit each of the three sample queries above and verify (a) the
Controller returns a substantive reply backed by the correct sub-agent's output, (b) an
audit entry exists naming the sub-agent and request/response pair, (c) responses stay
inside simulation tenant scope.

**Acceptance Scenarios**:

1. **Given** an `active` sim with the bushfire scenario, **When** the user asks *"what's
   Planning recommending?"*, **Then** within 10 seconds the Controller returns a plain-
   language summary of the Planning agent's current IAP recommendations and cites at least
   one identifier the user can click through to.
2. **Given** an `active` sim, **When** the user asks for *"a PIO draft emergency warning
   for Katoomba residents"*, **Then** the Controller returns a draft Australian Warning
   System (AWS) -compliant message stamped `SIMULATION — DO NOT DISTRIBUTE` and offers
   Approve/Discard; Approve records the draft in the sim tenant only.
3. **Given** a request to a sub-agent would require real-world action (e.g., *"call AV
   dispatch"*), **When** the Controller would otherwise invoke a real integration, **Then**
   the invocation is intercepted at the PublicationService boundary, recorded as
   `synthetic-delivery`, and never reaches external channels.

### User Story 4 — Disaster map shows simulation overlay with clear distinction (Priority: P2)

On the Disaster Map page, simulations in `active`, `paused`, or `ended` states render as
semi-transparent overlays with a striped pattern and a persistent `SIM` badge. Clicking an
overlay opens a side panel linking to the simulation detail screen. Live incidents remain
fully opaque and unmistakeably separate. An accessibility-compliant legend explains the
visual language.

**Why this priority**: Situational awareness — no operator should ever confuse a sim with
a live event. High priority but not P1 because the simulation detail screen is usable
without map integration.

**Independent Test**: With one live incident and one simulation active, open the Disaster
Map and confirm (a) both render, (b) the sim is visually distinct per the spec, (c) the
`SIM` badge is present, (d) a screen-reader announces the overlay as "simulation".

**Acceptance Scenarios**:

1. **Given** a live incident and an active sim at different locations, **When** the map
   renders, **Then** both appear with clearly different styling and a legend entry describes
   each.
2. **Given** a `paused` sim, **When** the map renders, **Then** the overlay uses the paused
   colour family (desaturated amber) and the badge reads `SIM · PAUSED`.
3. **Given** an `ended` sim older than 24 h, **When** the map renders, **Then** the overlay
   is hidden by default but available via a *"Show ended simulations"* legend toggle.
4. **Given** a user with `SimulationObserver` but not `SimulationCoordinator` role, **When**
   they click a sim overlay, **Then** the side panel shows a read-only detail view.

### User Story 5 — Public communications are hard-blocked during any simulation (Priority: P1)

The PublicationService, SMS gateway, Azure Communication Services (email/SMS), social media
connector, and broadcast integrations MUST inspect tenant context on every outbound message
and reject any message whose tenant begins with `sim-`. Rejections are recorded as
`synthetic-delivery` and made visible in the sim audit UI.

**Why this priority**: Constitutional — irreversible real-world action without authorisation
is forbidden. A single false-positive delivery from a sim would be a catastrophic failure.

**Independent Test**: Inject, from a sim, one of each message type (SMS, email, broadcast,
social) and confirm none reach any real gateway; all are logged as `synthetic-delivery` in
the sim audit trail with payload + intended channel.

**Acceptance Scenarios**:

1. **Given** an `active` sim, **When** the Comms agent attempts to publish an SMS via Azure
   Communication Services, **Then** the egress interceptor returns a `410 SIM_EGRESS_BLOCKED`
   result and writes a `synthetic-delivery` audit entry.
2. **Given** an `active` sim, **When** the Comms agent attempts a broadcast API call, **Then**
   the HTTP client wrapper (responsible for all outbound calls) refuses at the tenant-context
   check before any network request is made.
3. **Given** an `active` sim producing 100 outbound messages in a minute, **When** the
   synthetic-delivery log is queried, **Then** every message is recorded with payload hash,
   intended channel, and block reason.

### Edge Cases

- Chat model returns an unsafe or jailbroken response attempting real-world action → the
  server-side orchestrator's *action allow-list* refuses execution regardless of model output.
- Chat model hallucinates a non-existent sub-agent → Controller detects the unknown agent ID
  and returns a sanitised error; no tasking occurs.
- User sends PII in chat → PII detector redacts and warns; sim transcripts never leave the
  Australian tenant boundary.
- Browser tab closed mid-conversation → simulation state is server-authoritative; re-opening
  resumes from the last server snapshot.
- Sub-agent takes > 30 s → Controller returns a *"working on it"* acknowledgement and streams
  progress; timeout at 120 s with a graceful error.
- Network partition between Controller and sub-agents → Controller falls back to cached
  last-known state, marks the reply as `degraded`.
- Multiple coordinators on the same simulation → last-write-wins for control ops, chat is
  per-coordinator transcript but all are visible in the shared audit trail.
- Simulation left `active` for > 24 h with no chat activity → automatic move to `paused`
  with a coordinator notification.

## Requirements *(mandatory)*

### Functional Requirements

**Control & lifecycle**

- **FR-001**: System MUST provide Start, Pause, Resume, Stop controls on the Simulation
  detail screen, restricted to users with the `SimulationCoordinator` Entra ID role.
- **FR-002**: System MUST maintain simulation states `draft → active → paused ⇄ active → ended`
  and record every transition with timestamp, actor, reason.
- **FR-003**: `ended` is terminal; no state MAY transition back from `ended`.
- **FR-004**: System MUST auto-pause (or throttle per spec 007) if a Level-3 live incident is
  declared by NEMA, and surface a banner to the coordinator.

**Chat Controller agent**

- **FR-005**: System MUST provide a chat interface backed by Azure OpenAI chat-completion,
  scoped by a **Simulation System Prompt** that:
  - Declares the assistant's role as *Simulation Controller for AIDR exercises only*.
  - Forbids issuing real-world dispatch, alerts, or external communications.
  - Requires the assistant to call only allow-listed tools named `seed_scenario`,
    `query_sub_agent`, `draft_warning_sim`, `summarise_state`, `pause`, `resume`, `stop`,
    `list_participants`.
  - Requires confirmation before any state-changing action.
  - Watermarks any drafted public-information artefact with `SIMULATION — DO NOT DISTRIBUTE`.
- **FR-006**: System MUST execute tool calls through a server-side orchestrator that enforces
  the allow-list independently of the model's output (defence in depth against prompt
  injection).
- **FR-007**: System MUST record each chat turn (user, assistant, tool call, tool result) in
  the sim tenant audit trail with content-hash and model/version metadata.
- **FR-008**: System MUST support natural language input in English and accept jurisdiction,
  place, hazard type (bushfire, flood, cyclone, storm, heat, earthquake, tsunami, pandemic,
  other), and conditions (temp, wind, RH, fuel, tide/surge, seismic intensity, etc.).
- **FR-009**: Controller MUST return a structured scenario card for user confirmation before
  seeding a scenario; the card MUST include location, start time, hazard class, key
  parameters, and an AWS default warning level.
- **FR-010**: Controller MUST refuse and log any request that attempts real-world action,
  jailbreak, prompt exfiltration, or out-of-scope conversation.
- **FR-011**: Users MUST see streaming output for Controller replies and visible progress
  indicators when sub-agents are queried.

**Sub-agent coordination**

- **FR-012**: Controller MUST be able to invoke the Monitoring, Planning, Resource
  Allocation, Communication, Evacuation, and Risk Assessment agents via the `query_sub_agent`
  tool, always with the simulation tenant context.
- **FR-013**: Every sub-agent invocation and response MUST be logged with correlation IDs
  linking the chat turn, sub-agent, and any downstream state changes.
- **FR-014**: Controller MUST aggregate sub-agent outputs into a single plain-language reply
  while preserving citations (identifiers) the user can inspect.

**Map overlay**

- **FR-015**: Disaster Map MUST render each simulation in `active`, `paused`, or `ended`
  state as a distinct overlay with a `SIM` badge, following the Disaster Mapper UI (spec 020)
  layer conventions.
- **FR-016**: Map MUST support a legend entry explaining each sim state's visual style.
- **FR-017**: Clicking a sim overlay MUST open a side panel with summary info and a deep
  link to the simulation detail screen.
- **FR-018**: Ended simulations older than 24 h MUST be hidden by default with a toggle to
  show them.

**Comms block**

- **FR-019**: System MUST prevent any outbound public-facing communication (SMS, email,
  social media, broadcast, CAP push) whose originating tenant is a simulation tenant.
- **FR-020**: Each blocked message MUST be recorded as `synthetic-delivery` with payload
  hash, intended channel, audience, and block reason.
- **FR-021**: The egress gate MUST be enforced at the outbound HTTP client wrapper level
  (not only at the PublicationService), providing defence in depth.
- **FR-022**: A visible watermark `SIMULATION — DO NOT DISTRIBUTE` MUST appear in every
  rendered warning draft, PDF export, or email preview inside the sim.

**Observability, audit, safety**

- **FR-023**: System MUST emit Application Insights telemetry tagged with `tenant_id` and
  `simulation=true` for all sim-originated operations.
- **FR-024**: All Controller chat transcripts and sub-agent interactions MUST remain inside
  Australian Azure regions (data sovereignty — Constitution NON-NEGOTIABLE #2).
- **FR-025**: System MUST provide an Observer read-only view (for `SimulationObserver` role)
  of the simulation detail screen, chat transcript, and audit trail.
- **FR-026**: System MUST rate-limit chat submissions (default 30 messages/minute per user)
  to protect the Azure OpenAI deployment.
- **FR-027**: System MUST include red-team / jailbreak regression tests that run in CI.
- **FR-031**: Chat transcripts and sim audit artefacts MUST be retained for 2 years, then
  automatically purged (aligned with live audit retention).
- **FR-032**: Controller MUST resolve free-text locations via Azure Maps Search API; if zero
  results, it MUST request lat/lon from the coordinator before proceeding.
- **FR-033**: Approving a simulated warning draft MUST pin it to the sim audit trail with
  disposition `would-have-published` and MUST NOT transmit to any real channel.
- **FR-034**: If Azure OpenAI is unreachable, the chat input MUST become read-only with a
  banner explaining the degradation; Start/Pause/Stop controls, map, and sub-agent data
  MUST remain fully functional.
- **FR-035**: Exactly one user MAY hold the `primary-coordinator` claim on a simulation at
  any time; additional authorised users join as observers or request hand-over.
- **FR-036**: On Stop, in-flight sub-agent queries MUST be cancelled; each cancellation MUST
  be recorded with outcome `cancelled-by-stop`; idempotent completion writes from the
  sub-agent ARE permitted to avoid partial-state corruption.
- **FR-037**: The Simulation Controller system prompt and tool manifest MUST be stored in a
  versioned file inside the repository; at runtime the file hash MUST be included on every
  chat-turn audit record.
- **FR-038**: Rate limits MUST apply as (a) 30 messages/minute per user per simulation, and
  (b) 120 messages/minute per tenant across all simulations in that tenant.
- **FR-039**: The jailbreak / red-team suite MUST run on every pull request that modifies
  simulation code and nightly on `main`; the suite MUST contain at least 200 adversarial
  prompts; any regression blocks merge.
- **FR-040**: NEMA-Level-3 auto-throttle MUST render a non-dismissible banner on the sim
  detail screen, emit a toast notification, and record an audit event; during the throttle
  the Controller MUST only honour `summarise_state`, `pause`, and `stop` tool calls.

**Accessibility, localisation, UX**

- **FR-028**: Simulation detail screen MUST meet WCAG 2.2 AA; chat input MUST be keyboard-
  navigable, screen-reader labelled, and support reduced-motion preferences.
- **FR-029**: Map overlay legend entries MUST meet contrast ratio ≥ 4.5:1 against the base
  map; `SIM` badge MUST be announced by screen readers as "simulation".
- **FR-030**: System SHOULD render coordinator chat and Controller replies in a format that
  is printable/export-friendly for after-action reports.

### Key Entities

- **Simulation** (extends spec 007 tenant model): identifier `sim-{scenarioRunId}`, status
  (`draft|active|paused|ended`), scenario metadata, created-by, participants.
- **Simulation Scenario Card**: the structured representation of the coordinator's intent,
  produced by the Controller, including hazard class, location (GeoJSON or locality name +
  resolved coordinates), start time, weather/environmental parameters, fuel/load/tide/surge,
  AWS default warning level.
- **Chat Turn**: role (`user|assistant|tool`), content, tool-call metadata, model version,
  tenant ID, timestamp, hash.
- **Tool Invocation**: allow-list name, arguments, tenant context, sub-agent target (if any),
  result, latency, outcome (`ok|refused|error`).
- **Synthetic Delivery Record**: channel, audience, payload hash, block reason, timestamp,
  tenant ID.
- **Sim Map Overlay**: layer ID, visual style (`active|paused|ended`), geometry, linked
  simulation ID.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A coordinator can start a viable simulation from scratch using only chat, in
  under 90 seconds from opening the detail screen to the first sub-agent tasking.
- **SC-002**: 100% of outbound public-facing messages originating from a simulation are
  blocked before leaving the platform; zero real deliveries across 10,000 red-team test
  messages.
- **SC-003**: 95% of Controller replies for routine sub-agent queries return within 10
  seconds end-to-end.
- **SC-004**: 100% of chat turns, tool invocations, and state transitions are recoverable
  from the audit trail with full provenance.
- **SC-005**: The Controller refuses or safely redirects ≥ 99% of a curated jailbreak /
  out-of-scope test set (≥ 200 prompts) in CI.
- **SC-006**: Operators viewing the Disaster Map correctly identify the sim vs live
  status of every overlay on first glance ≥ 95% of the time in usability testing.
- **SC-007**: The simulation detail screen and map overlay pass WCAG 2.2 AA automated + manual
  audit with zero critical findings.
- **SC-008**: Auto-throttle during a live Level-3 incident engages within 5 seconds of NEMA
  declaration; no sim action interferes with live operations in that window.

## Out of Scope

- This spec is delivery-hygiene / enabling infrastructure; capstone-outcome-critical-path ownership lives in specs 001, 020, 021, 023.

- **Accelerated / time-warped simulation playback** (may be a future feature).
- **Multi-lingual chat input beyond English** (follow-up).
- **Role-play for external participants without Entra ID accounts** (covered by spec 007
  participant list; no change here).
- **Realistic social-media crowd-sourced injects** (future feature; synthetic injects only
  for now).
- **Non-Azure model providers** — Azure OpenAI only per Constitution VIII.

## Dependencies

- Spec 007 — simulation-tenant-isolation (tenant model, throttling, participant list).
- Spec 008 — communication-agent (PublicationService egress gate).
- Spec 009 — evacuation-agent (sub-agent).
- Spec 010 — monitoring-agent (sub-agent, synthetic signal emitter).
- Spec 011 — resource-allocation-agent (sub-agent).
- Spec 012 — risk-assessment-agent (sub-agent).
- Spec 014 — azure-openai-integration (model deployment, content safety).
- Spec 020 — disaster-mapper-ui (map layer host).

## Assumptions

Scoped to this spec's domain (conversational simulation control). Tagging follows `specs/027-spec-hardening` taxonomy: `[RISK]` (open externally-driven risk), `[DECISION]` (deliberate scoping decision), bare bullet (operating assumption).

- **ASM-071**: The AU-v1 deployment context defined in `specs/001-disaster-response-hub/spec.md` is the operational baseline for this spec; capstone-country variants (PH / JP / BD) are deferred. `linked_gaps:` `specs/shared/gap-id-register.md` A-GAP-001..003. `status:` Open.
- **ASM-072** [DECISION]: This spec's deliverables (conversational simulation control) integrate with the actor catalogue (`specs/004-actor-github-agents/spec.md`); responsible technical agents - ux-designer, product-owner-ba - are consulted via the `agent` tool during authoring and review.
- **ASM-073**: Speckit conventions (FR/SC numbering, ASM/HYP/PER/SCP families) and the persona-profile YAML schema (`specs/027-spec-hardening/contracts/persona-profile.md`) are authoritative; this spec defers to those rather than redefining them.

## Personas

Authored against the `specs/027-spec-hardening/contracts/persona-profile.md` schema. AU-v1 personas are validated; PH / JP / BD entries are explicit placeholders pending capstone-reinterpretation (D-009) and SME validation per FR-023.

- **PER-064**: cross-ref to `specs/001-disaster-response-hub/spec.md` AIIMS personas (Incident Commander / Planning Officer / Operations Officer / Logistics Officer / Public Information Officer) per `specs/027-spec-hardening/contracts/persona-profile.md`. `status:` validated. `preconditions:` none.
- **PER-065**: cross-ref to `specs/004-actor-github-agents/spec.md` actor catalogue covering all `.github/agents/technical/*.agent.md` actors. `status:` validated. `preconditions:` none.
- **PER-066** [non-AU placeholder]: capstone-country operator personas for PH (NDRRMC), JP (Cabinet Office DRR / FDMA), BD (DDM / CPP volunteers). `status:` placeholder. `preconditions:` capstone-reinterpretation decision per D-009; SME validation via `ama-rubric-grader`-vetted SME interviews.

## Hypotheses

Hypotheses use the FR-018 statement format (`If <condition> then <observable>`) and link to a structured evidence stub conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. Capstone-country hypotheses for this spec's agent ownership (where applicable) are allocated in feature 028 / US2.

- **HYP-022**: If the actors named in `specs/004-actor-github-agents/spec.md` consult on every change to this spec via the `agent` tool, then the AMA rubric criterion mean (Assumptions / Requirements / Personas / Hypotheses / Scope) for this spec rises by at least +1 band relative to the baseline captured in `specs/028-capstone-alignment/evidence/rubric-baseline.md`. **Falsification**: post-feature rubric snapshot shows a regression in any of those five criteria for this spec. **Evidence stub**: `specs/028-capstone-alignment/evidence/HYP-HYP-022.md` (created in feature 028 polish).

