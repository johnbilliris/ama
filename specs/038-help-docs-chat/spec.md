# Feature Specification: In-Product Help Documentation & Grounded Chat Assistant

**Feature Branch**: `038-help-docs-chat`
**Created**: 2026-05-11
**Status**: Draft
**Input**: User description: "highly detailed in-product help documentation with a grounded chat assistant for the Autonomous Disaster Response Coordination Hub. Help must support every persona, be visually rich (annotated screenshots), include a chat that answers questions grounded ONLY in the help corpus + `docs/corpus/**` + `docs/aidr/**` + active spec docs, refuses out-of-scope questions, cites sources, supports persona context, preserves Australian data residency, redacts PII (per spec-036 data-minimisation gateway), and meets WCAG 2.2 AA."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Persona-aware Getting-Started & Workflow Guides (Priority: P1)

Any signed-in user — operational role (e.g., Incident Commander, Public Information Officer) or sector representative (e.g., NSW RFS, Victoria Ambulance, NEMA, local government) — opens the in-product Help Centre and is greeted with a curated landing page tailored to their persona. They can discover what the Hub does for *their* role, follow a step-by-step "first 15 minutes" guide, and drill into a screen-by-screen walkthrough of every primary surface they will use, with annotated screenshots showing exactly where to click.

**Why this priority**: Without persona-aware onboarding, multi-agency users (10 operational roles, ~80 sector roles spanning fire, ambulance, police, SES/marine, Commonwealth coordination, and cross-sector partners) cannot navigate the Hub during an active incident. Help that mirrors AIIMS roles is a prerequisite for safe adoption — every other help capability builds on this content backbone.

**Independent Test**: A new user from any persona can open the Help Centre, see content filtered/highlighted for their role, complete the persona's "first 15 minutes" tour, and locate the screen-by-screen guide for at least three Hub surfaces (e.g., Disaster Mapper, Governance Dashboard, Simulation Control) without consulting any external resource. Annotated screenshots match the live UI in both light and dark modes.

**Acceptance Scenarios**:

1. **Given** an Incident Commander logs into the Hub for the first time, **When** they open the Help Centre, **Then** the landing page surfaces an "Incident Commander quickstart" tile, links to the AIIMS Controller workflow guide, an annotated screenshot tour of the shared operating picture, the public-alert approval flow, and the cross-jurisdiction escalation path.
2. **Given** a Public Information Officer is preparing a multilingual alert, **When** they open Help from the alert composer, **Then** Help opens in-context to the "Drafting & submitting public alerts for IC approval" guide, including screenshots of the multilingual editor, accessibility checker, and channel-selection panel.
3. **Given** a NSW RFS sector representative opens Help, **When** they browse persona content, **Then** they see the frontline-fire cluster guide covering signal ingestion, jurisdictional filter usage, resource availability publishing, and tasking acknowledgement, with screenshots showing NSW-jurisdiction theming.
4. **Given** an Observer-Auditor opens Help, **When** they search for "audit trail review", **Then** they reach a guide describing the read-only audit surface, append-only timeline navigation, compliance verification checklist, and lessons-learned export — matching the role's read-only decision rights.
5. **Given** a user toggles dark mode, **When** they re-open any help article containing screenshots, **Then** the screenshots displayed match the active theme (light or dark) and remain legible.

---

### User Story 2 — Grounded In-Product Chat Assistant (Priority: P1)

A user opens a chat panel from anywhere in the Hub and asks a natural-language question (e.g., "How do I escalate a cross-border bushfire to NEMA?", "What does the amber confidence badge mean?", "How do I run a warp-playback simulation?"). The assistant answers using ONLY the approved knowledge corpus (Help articles, `docs/corpus/**`, `docs/aidr/**`, and the active spec documents under `specs/**`), cites its sources with deep links, respects the user's persona/jurisdiction context, refuses out-of-scope questions politely, and never invents information.

**Why this priority**: The user's stated requirement is that users "do not have to troll through links and read text on their screen". Chat is the primary access path for time-pressured operational users; it must be grounded to be safe in a life-safety context (Constitution Principle I). Without grounding + refusal, the assistant is unsafe to ship.

**Independent Test**: For a fixed evaluation set covering each persona cluster, the assistant (a) answers in-scope questions with at least one citation each pointing to an approved corpus document, (b) refuses out-of-scope questions (e.g., medical advice, legal opinions, weather forecasts not present in corpus, anything about other tenants) with a standard refusal message, and (c) returns no answer containing claims that cannot be traced to a citation.

**Acceptance Scenarios**:

1. **Given** an Operations Officer asks "How do I reassign a coordination task to another agency?", **When** the assistant responds, **Then** the answer references the relevant Help article and the underlying data-model entity, includes clickable citations, and offers a "Take me there" deep-link to the task-reassignment surface.
2. **Given** a user asks "What is the weather in Sydney tomorrow?", **When** the assistant evaluates the question, **Then** it refuses with a message explaining it answers only questions about using the Hub and points to the `bom-national` data feed surface for live forecasts.
3. **Given** a user asks about another tenant's incidents or another organisation's private data, **When** the assistant evaluates the question, **Then** it refuses on tenant-isolation grounds and does not return any cross-tenant content.
4. **Given** a user pastes text containing personal data (names, phone numbers, addresses) into the chat, **When** the message is processed, **Then** PII is redacted before the message reaches the grounding/answering pipeline (consistent with the data-minimisation gateway pattern), and the user is notified that redaction occurred.
5. **Given** a Public Information Officer with persona context set asks "How do I publish in Vietnamese and Auslan?", **When** the assistant responds, **Then** it returns persona-tailored steps from the multilingual/accessibility guide and cites Constitution Principle V plus the alert-composer Help article.
6. **Given** the corpus contains no answer to an in-scope question, **When** the assistant evaluates confidence, **Then** it states it cannot answer from the available material, suggests the closest related articles, and offers a "Contact support" handoff rather than guessing.
7. **Given** any chat answer is rendered, **When** the user inspects it, **Then** every factual claim has at least one inline citation badge, and clicking the badge opens the cited article at the relevant heading.

---

### User Story 3 — Visually Rich, Annotated Screen-by-Screen Guides (Priority: P2)

Help authors and the system together maintain an annotated screenshot library that covers every primary screen of the Hub and every persona's typical workflow. Screenshots include callouts, numbered steps, alt text, and equivalent versions for light and dark modes. Keyboard-only and screen-reader navigation paths are documented alongside the visual guides.

**Why this priority**: The user explicitly requires "very visually pleasing" help with screenshots wherever required. Annotated visuals reduce time-to-competence for sector users who use the Hub episodically, and equivalent text/keyboard paths are mandatory for WCAG 2.2 AA.

**Independent Test**: Every primary Hub screen (Disaster Mapper, Governance Dashboard, Simulation Control, Multi-Jurisdiction Filter, Agent surfaces for Communication / Evacuation / Risk / Resource, Audit/Observer view, Alert Composer, Login & persona switcher) has at least one annotated screenshot in both light and dark modes, each with alt text and a documented keyboard-only equivalent. Auditors can verify by opening each persona workflow guide and counting screenshots, alt text, and keyboard notes.

**Acceptance Scenarios**:

1. **Given** an article describes the Disaster Mapper, **When** it is rendered, **Then** it displays an annotated screenshot with numbered callouts matching numbered steps in the prose, alt text describing each callout, and a light/dark variant toggle.
2. **Given** the Hub UI changes (new control added or relabelled), **When** the change is shipped, **Then** the corresponding Help screenshots are flagged as out-of-date so authors can refresh them before the next release; stale screenshots are visibly marked in Help.
3. **Given** a screen-reader user navigates a workflow guide, **When** they reach a screenshot, **Then** the alt text plus an adjacent "Keyboard steps" block describes the same workflow without requiring vision.

---

### User Story 4 — Simulation, Agent, and Observer Playbooks (Priority: P2)

Help includes deep playbooks for the major Hub capabilities: running a simulation (incl. warp/playback), using each domain agent (Communication, Evacuation, Monitoring, Risk Assessment, Resource Allocation), and operating in observer/audit mode. Each playbook walks the user from start to finish with screenshots, decision points, and "what could go wrong" sections.

**Why this priority**: These capabilities are where the Hub creates its differentiated value, but they have the steepest learning curve. Without playbooks, only specialist users can exercise them.

**Independent Test**: A user new to a capability can complete a representative end-to-end task by following only the playbook (e.g., set up a bushfire simulation, run it at 8× warp, generate an evacuation recommendation, get IC approval, log to audit) without consulting an external trainer.

**Acceptance Scenarios**:

1. **Given** a Resilience Planner opens the simulation playbook, **When** they follow the steps, **Then** they can configure a multi-jurisdiction scenario, run warp playback, and export observations without leaving the playbook.
2. **Given** an Operations Officer opens the Evacuation Agent playbook, **When** they follow the steps, **Then** they can request a recommendation, review provenance, route it for IC approval, and trace the audit entry.
3. **Given** an Observer-Auditor opens the audit/observer playbook, **When** they follow the steps, **Then** they can reconstruct an incident timeline, identify framework deviations, and generate a lessons-learned export.

---

### User Story 5 — Search, Glossary, Troubleshooting & FAQ (Priority: P3)

Users can full-text search across all Help content (and through the chat), browse a glossary of AIIMS, AIDR, jurisdictional, and Hub-specific terms, and find a curated troubleshooting/FAQ section for the most common issues (login, persona switching, jurisdiction filter, degraded-connectivity banner, alert approval failures, simulation reset).

**Why this priority**: Search and glossary increase discoverability and reduce repeat questions but are dependent on the content created in Stories 1–4.

**Independent Test**: Searching any glossary term returns the canonical definition first; the top 20 troubleshooting topics each resolve in a self-contained article.

**Acceptance Scenarios**:

1. **Given** a user types "AIIMS Controller" into Help search, **When** results render, **Then** the glossary entry appears first followed by the Incident Commander persona guide.
2. **Given** a user encounters a degraded-connectivity banner, **When** they search "degraded mode", **Then** the troubleshooting article explains the banner, expected behaviour, and recovery steps.

---

### Edge Cases

- **Out-of-scope chat questions**: Refused with a standard explanation and a pointer to the right surface or human contact; refusal is logged for review.
- **Cross-tenant or cross-organisation question**: Refused on isolation grounds; no content from outside the user's tenant or permitted scope is retrieved or returned.
- **PII in user input**: Redacted at the gateway before reaching the grounding pipeline; user is informed.
- **Corpus disagreement**: When two corpus sources conflict, the assistant surfaces the conflict, cites both, and recommends human verification rather than picking one silently.
- **No matching corpus answer**: Assistant states it cannot answer from the available material and offers nearest articles + "contact support".
- **Stale screenshots**: Flagged in-product; users see a "this image may be out of date" notice.
- **Offline / degraded connectivity**: Help articles previously cached on the device remain readable; chat is disabled with an explanation; the user is directed to cached troubleshooting content.
- **Screen reader / keyboard-only**: Every visual element has an alt-text and keyboard-equivalent path; chat is fully operable from the keyboard with announced status changes.
- **Multilingual users**: PIO multilingual content authoring guide is available; Help UI itself supports at minimum English with planned expansion (see Assumptions).
- **Audit-mode user (read-only)**: Chat answers never include any action that would imply the read-only user can modify state; they receive observation/audit-oriented guidance.

## Requirements *(mandatory)*

### Functional Requirements

#### Help Content

- **FR-001**: The Hub MUST provide an in-product Help Centre accessible from every primary screen via a persistent control.
- **FR-002**: The Help Centre MUST present a persona-aware landing page for each of the 10 operational roles (incident-commander, operations-officer, planning-officer, logistics-officer, public-information-officer, field-coordinator, resilience-planner, executive-leader, observer-auditor, risk-manager) and for each sector cluster (frontline-fire, frontline-medical, frontline-police, frontline-ses, commonwealth, cross-sector).
- **FR-003**: Help content MUST cover the following domains: getting started, persona-specific workflows, screen-by-screen guides for every primary surface, simulation playbook (incl. warp/playback), playbooks for the Evacuation, Communication, Monitoring, Risk Assessment, and Resource Allocation agents, audit/observer mode guide, accessibility how-tos, troubleshooting/FAQ, and a glossary of AIIMS / AIDR / jurisdictional / Hub-specific terms.
- **FR-004**: Each persona landing page MUST link to the role's typical workflows, decision rights, scope boundaries, and handoff destinations consistent with the role definition in `.github/agents/`.
- **FR-005**: Help articles MUST be openable contextually (e.g., from a "Help on this screen" affordance) and deep-linkable.

#### Visual & Accessibility

- **FR-006**: Every primary Hub screen and every persona's typical workflow MUST have at least one annotated screenshot with numbered callouts that map to numbered prose steps.
- **FR-007**: Screenshots MUST be available in both light and dark mode variants and MUST switch automatically with the user's active theme.
- **FR-008**: Every screenshot MUST have descriptive alt text and an adjacent keyboard-only equivalent set of steps.
- **FR-009**: Help content (UI chrome, articles, chat panel) MUST conform to WCAG 2.2 AA, including keyboard-only navigation, visible focus indicators, screen-reader compatibility, and minimum colour-contrast ratios.
- **FR-009a**: Embedded non-English glossary terms, place names, language-of-country attributions, and acronyms with non-English expansions (e.g., Aboriginal & Torres Strait Islander language items, AIIMS-adjacent terms in community languages) MUST be wrapped with a correct `lang` attribute (HTML `lang`, or the screen-reader-API equivalent on non-HTML surfaces) per WCAG 2.2 SC 3.1.2 (Language of Parts) so assistive technologies announce them with the appropriate phoneme set. The Help-UI surface itself remains English (per the 2026-05-11 Pass 1 clarification); this requirement governs *embedded fragments* within otherwise-English content.
- **FR-010**: The Hub MUST flag screenshots as potentially stale when the corresponding UI surface changes, and surface a visible "may be out of date" notice to readers until refreshed.
- **FR-010a**: Stale-screenshot **detection signal** MUST be a deterministic `screen_id_hash` computed at UI build time from (route id + the ordered set of DOM-element fingerprints corresponding to each numbered callout anchor). The Help asset registry stores the `screen_id_hash` recorded at screenshot-capture time; on each release the build pipeline MUST compare the live `screen_id_hash` against the stored value and raise the `Staleness Flag` when they differ. Visual-diff thresholds and screen-id conventions remain implementation choices within this contract; the binding signal is the hash mismatch.
- **FR-010b**: A **grace period of one release cycle** applies after a stale flag is raised: the "may be out of date" notice is shown to readers immediately (FR-010), authors receive a refresh task on flag-raise, and if not refreshed by the next release the article MUST be downgraded with an additional "screenshots not yet refreshed for this release" banner. The article is never automatically removed (Constitution Principle I — no silencing of safety-relevant guidance).

#### Chat Assistant — Grounding & Safety

- **FR-011**: The chat assistant MUST answer using ONLY the approved knowledge corpus consisting of: in-product Help articles, `docs/corpus/**`, `docs/aidr/**`, and the **Help-approved snapshot** of feature spec documents under `specs/**` (specs in `Active`/`Implemented` status that have passed Help-approval review) for the user's tenant. Draft, experimental, archived, and unreviewed specs MUST NOT be admitted to the grounding corpus.
- **FR-011a**: The Help-approved spec snapshot MUST be versioned, auditable (snapshot id, included spec ids+versions, approver identity, approval timestamp), refreshed at minimum each release, and re-published only via the same approval gate. The chat retrieval pipeline MUST resolve the active snapshot, never a live `HEAD` of `specs/**`.
- **FR-011b**: Snapshot **approval gate** MUST require dual sign-off from a Help-content owner AND a safety-lead (or governance-lead) — mirroring the spec-005 FR-015 dual-authority pattern. Approver identities and timestamps MUST be persisted with the snapshot record and surfaced in the chat audit log.
- **FR-011c**: Snapshot **rollback** MUST be performed by re-publishing a previously-approved snapshot id (snapshots are immutable; no in-place edit). Rollback MUST complete within the spec-029 FR-008 5-minute reversibility SLO via configuration flip (no code redeploy) and MUST emit an `audit.snapshot_rollback` event with `previous_snapshot_id`, `restored_snapshot_id`, `actor_id`, `change_reason`.
- **FR-011d**: When a user follows a deep link that resolves to content removed or superseded by a newer snapshot, chat MUST render a **deprecation notice** ("This guidance was published in snapshot `<id>` and replaced on `<YYYY-MM-DD>` by snapshot `<id>`; current guidance is …") and surface a citation to the current equivalent article rather than silently substituting content (Constitution Principle IV — provenance & transparency).
- **FR-012**: The chat assistant MUST cite at least one source for every factual claim in its response, with citations rendered as inline references that deep-link to the cited article and heading.
- **FR-013**: The chat assistant MUST refuse out-of-scope questions (anything not answerable from the approved corpus, including but not limited to live operational data not present in the corpus, weather forecasts, legal/medical advice, and information from outside the user's tenant) using a standard, non-judgmental refusal message and suggest the right surface or contact.
- **FR-014**: The chat assistant MUST NOT fabricate content; when corpus support is insufficient, it MUST explicitly say so and offer nearest related articles plus a support handoff.
- **FR-015**: The chat assistant MUST accept and use the user's persona and jurisdiction context to bias retrieval and tailor answers, without exposing other personas' or other tenants' content.
- **FR-016**: The chat assistant MUST surface conflicts when corpus sources disagree, cite both, and recommend human verification.

#### Chat Assistant — Privacy, Residency, Tenancy

- **FR-017**: User input to the chat MUST pass through a PII-redaction gateway consistent with the data-minimisation pattern established in spec-036 before reaching the grounding/answering pipeline; users MUST be notified when redaction occurs.
- **FR-018**: All chat processing, retrieval, storage, and logs MUST remain within Australian data-residency boundaries as defined by the project Constitution.
- **FR-019**: Chat retrieval and answers MUST be strictly scoped to the user's tenant and authorised content; cross-tenant retrieval MUST be impossible by design.
- **FR-020**: Chat interactions (prompt, redacted input, retrieved citations, response, refusal reason if any) MUST be recorded in an append-only audit log per Constitution Principle III, available to Observer-Auditors.

#### Search, Discovery & Feedback

- **FR-021**: Help MUST provide full-text search across all articles and the glossary, returning the glossary definition first when the query matches a glossary term.
- **FR-022**: Each article and each chat response MUST allow the user to mark it as helpful / not helpful and submit free-text feedback; feedback MUST be retained for content improvement.
- **FR-023**: The chat panel MUST offer a one-click handoff to a human support contact when the assistant cannot answer or the user requests it.
- **FR-023a**: Each tenant MUST configure a **support handoff destination record** with: channel type (email | shared mailbox | on-call rotation | chat link), address/identifier, business-hours window (or `24x7`), and incident-mode override channel. When no record is configured, chat MUST fall back to a platform-default support address rather than failing silently.
- **FR-023b**: Handoff acknowledgement **SLA**: during a declared NEMA-Level-3 (or equivalent state-declared) incident, the configured incident-mode channel MUST surface a human acknowledgement within **5 minutes** (mirrors spec-036 Q-P1-03 / FR-RAG-COORD-02 escalation-unack timer); during routine operations the SLA target is **4 business hours**. SLA breach MUST emit an `audit.support_handoff_unack_timeout` event for Observer-Auditor review. The Hub does not directly enforce tenant staffing; the SLA is a contractual expectation surfaced in the audit log, not a system guarantee.
- **FR-022a**: Negative feedback (a "not helpful" rating, with or without a comment) on either an article or a chat turn MUST be enqueued in a **content-review backlog** scoped to the user's tenant and visible to Help authors. When the same article or chat-answer pattern accumulates ≥3 negative ratings within a 30-day rolling window, the backlog item MUST be auto-promoted to "needs review" so authors can prioritise. Negative feedback MUST NOT auto-disable, hide, or alter the article or answer (Constitution Principle I — no silencing of safety-relevant guidance; only humans may withdraw content via the snapshot approval gate FR-011b).

#### Multilingual & Read-Only Modes

- **FR-024**: Help MUST include a multilingual content authoring guide for the Public Information Officer covering language coverage expectations (English plus relevant community and Aboriginal & Torres Strait Islander languages where impacted) and accessibility for public-facing communications.
- **FR-025**: When the active user holds a read-only role (Observer-Auditor), chat and Help MUST tailor guidance to observation/audit actions and MUST NOT instruct the user to perform state-changing operations.

#### Degraded Connectivity

- **FR-026**: Previously-viewed Help articles MUST remain readable when the Hub is in degraded-connectivity mode; the chat assistant MUST be visibly disabled with an explanatory message and a pointer to cached troubleshooting content.
- **FR-026a**: The degraded-mode Help cache MUST contain, at minimum: previously-viewed articles, the full glossary, and the curated troubleshooting/FAQ topics enumerated in FR-021 / Help Content Domains §8. Full-text search results are limited to the cached subset; the chat assistant, free-text search across uncached corpus, and any retrieval against `docs/aidr/**`, `docs/corpus/**`, or the spec snapshot are unavailable in degraded mode and MUST display the standard "unavailable in degraded mode" message.
- **FR-026b**: Cache **TTL is 14 days** and the per-device cache footprint MUST stay within the ≤500 MB envelope established by spec-036 FR-RAG-LS-02 (shared with the Field Coordinator offline corpus cache, not additive). On reconnect, an audit-logged refresh MUST occur (mirrors FR-RAG-LS-02). Articles whose cached copy exceeds the TTL MUST be displayed with a "may be stale — last cached `<YYYY-MM-DD>`" banner until refreshed.

#### Persona Context Resolution

- **FR-027**: Persona context for chat retrieval and Help personalisation MUST be resolved as follows: (a) the **default persona** is derived from the user's identity-provider role claim (the highest-authority operational role, per the spec-021 FR-025 multi-role pattern); (b) the user MAY override the default via the persona switcher (FR-002 / Help Content Domains §1) to any other persona they are entitled to hold; (c) the **active persona** at the moment of each chat turn or article load MUST be recorded in the audit log alongside the role-claim source so an Observer-Auditor can reconstruct which persona context shaped any given answer.
- **FR-028**: Users entitled to **multiple roles** (e.g., an officer who is both Operations Officer and Observer-Auditor) MUST see, on the Help landing page, the union of their entitled persona tiles ordered by authority rank with the highest-authority role first (mirrors spec-021 FR-025). Chat MUST use only the *active* selected persona, never the union, to avoid leaking guidance scoped to a role the user has not explicitly entered.

#### Conversation Persistence

- **FR-029**: Chat conversations MUST be persisted per-tenant in Cosmos DB within Australian data-residency boundaries (Constitution Non-Negotiable #2). User-visible conversation **transcripts** MUST be retained for **30 days** (operational data class, **strict** ≤30-day cap per spec-001 NFR-002 operational retention envelope) so users can revisit recent answers. The append-only **chat audit log** (FR-020) is the system-of-record and MUST be retained for **7 years** per spec-001 NFR-012 and spec-036 FR-RAG-COMP-01 (APP 11 retention; system-audit data class). Both retention windows MUST be enforced by automatic purge. Help chat transcripts are **not** classified as "incident evidence" because the chat is help/navigation only and never instructs state-changing operations (FR-025); incident-evidence reconstruction needs are met by the 7-year audit log via FR-029a/b.
- **FR-029a**: An Observer-Auditor MAY retrieve any chat audit-log entry within their tenant scope at any time during the 7-year window; transcripts older than 30 days are reconstructable from the audit log (which carries redacted input, retrieved citations, and response — FR-020) but are no longer surfaced in the user's own conversation history.
- **FR-029b**: When an Observer-Auditor reconstructs an expired transcript from the audit log, the reconstruction MUST be rendered ONLY inside the audit tooling surface (Observer-Auditor read-only view), MUST be visibly labelled "Reconstructed from audit log — not visible to original user", and MUST NOT be re-surfaced in the original user's conversation history. Each reconstruction action itself MUST emit an `audit.transcript_reconstructed` event capturing observer identity, target user id, time window, and access reason (Constitution Principle IV — no covert access).

#### Spec Amendments — Checklist Gap Resolutions (Session 2026-05-11 Pass 3)

The following clauses tighten requirements where the speckit.checklist run surfaced ambiguity. Each clause is binding and supersedes any conflicting earlier wording.

- **FR-011-AMEND (Corpus tenancy scope)**: The `docs/corpus/**` and `docs/aidr/**` reference bodies are **global** Australian-residency corpora (national/jurisdictional doctrine, AIDR handbooks). Tenant scoping in FR-011 / FR-019 applies to: (a) Help Articles, (b) chat transcripts, (c) chat audit log, (d) the *composition* of the Help-approved spec snapshot (a tenant MAY exclude specs irrelevant to its operations, but MAY NOT include specs from another tenant), and (e) the support-handoff configuration record (FR-023a). Global corpora are read-only and shared across tenants without modification.
- **FR-022a-AMEND (Chat-answer pattern identity)**: A "chat-answer pattern" for the ≥3-negatives-in-30-days threshold (FR-022a) is identified by the deterministic tuple `(question_intent_cluster_id, ordered_set(citation_source_ids))` — i.e., semantically-clustered question intent (via the same retrieval embedding pipeline used for grounding) combined with the exact ordered set of source citations returned. Two answers belong to the same pattern iff both fields match. Pattern ids MUST be persisted with each chat turn for backlog aggregation.
- **FR-009a-AMEND (lang-attribute enforcement mechanism)**: `lang`-attribute hygiene (FR-009a) MUST be enforced at TWO gates: (a) **authoring time** — the Help authoring surface MUST validate that any term tagged in the glossary as a non-English fragment is wrapped in the correct `lang` attribute when inserted, and reject save if missing; (b) **build time** — a CI lint MUST scan published Help articles for declared glossary terms missing `lang` attributes and fail the build. No runtime injection — `lang` attributes are part of the source content.
- **FR-026a-AMEND (Degraded-mode search scope indicator)**: When the Hub is in degraded-connectivity mode, the search UI MUST display a persistent "Showing cached results only — full search unavailable offline" indicator above the result list, and the chat panel MUST display the standard "unavailable in degraded mode" message (per FR-026) rather than appearing functional.
- **FR-027-AMEND (Authority rank back-reference)**: The "highest-authority operational role" ordering for multi-role users (FR-027 / FR-028) is the **AIIMS authority rank** as enumerated in spec-021 FR-025; if spec-021 FR-025 is amended, this spec defers to that amendment without re-issue. Implementation MUST source the rank table from a single shared registry to prevent drift.
- **FR-023a-AMEND (Incident-mode auto-detection vs manual)**: The "incident-mode override channel" in FR-023a is **auto-activated** by the active NEMA-Level-3 banner state from spec-024 (no per-tenant manual toggle for routine incidents). A tenant MAY additionally configure a manual override flag for declared local incidents below Level-3 — when set, the override channel is used; when unset, the routine business-hours channel applies.
- **SC-009-AMEND (Pre-release baseline capture)**: The "pre-release baseline" referenced in SC-009 (40% reduction in navigation support tickets) MUST be captured during a **2-week observation window immediately preceding feature launch**, recording: support-ticket volume tagged as navigation/help-related, persona breakdown, and median time-to-resolution. The baseline record is published as `specs/038-help-docs-chat/baselines/pre-launch-support.md` before SC-009 measurement begins. Without this baseline, SC-009 is unmeasurable and the gate cannot pass.
- **FR-011d-AMEND (No-replacement deprecation)**: When a deep link resolves to content that has been retired with **no current equivalent** (article withdrawn, not superseded), chat MUST render: "This guidance was published in snapshot `<id>` and was withdrawn on `<YYYY-MM-DD>` with no current replacement; please contact your support handoff." The notice MUST surface the FR-023 support-handoff destination directly. The original snapshot id MUST remain reconstructable from the audit log per FR-020.
- **FR-010a-AMEND (Route-rename bulk re-baseline)**: When a UI route is renamed (the `route_id` itself changes, not just its DOM), the build pipeline MUST detect the rename via the route registry's `previous_route_id` mapping and trigger a **bulk re-baseline workflow** — all screenshots tied to the old `route_id` are flagged stale en masse with a single grouped author task ("Route renamed: re-baseline N screenshots") rather than N independent stale flags. Articles continue to render existing screenshots with the standard staleness banner during the grace period.

### Key Entities *(include if feature involves data)*

- **Help Article**: A single piece of help content. Attributes include title, persona tags, jurisdiction tags, surface/screen tags, body, embedded annotated screenshots, alt text, keyboard-equivalent steps, version, last-updated timestamp, freshness/staleness flag.
- **Annotated Screenshot**: A visual asset bound to one or more Help Articles. Attributes include light/dark variants, numbered callouts, alt text, screen identifier (so the system can flag staleness when that screen changes).
- **Glossary Term**: Canonical definition of an AIIMS / AIDR / jurisdictional / Hub-specific term, with cross-links to related articles.
- **Persona Help Profile**: Mapping from a persona (operational role or sector cluster) to its landing-page tiles, recommended workflows, and decision-rights summary.
- **Knowledge Corpus Source**: A registered, indexed source the chat assistant is permitted to ground in (Help Articles, `docs/corpus/**`, `docs/aidr/**`, `specs/**`). Attributes include path/identifier, tenant scope, last-indexed timestamp, content classification.
- **Chat Session**: A user's conversation with the assistant. Attributes include persona context, jurisdiction context, redacted message history, retrieved citations per turn, response, refusal reason (if any), feedback rating.
- **Citation**: A reference returned with a chat answer. Attributes include source id, source title, anchor/heading, snippet.
- **Help Feedback**: User-submitted helpfulness rating and comment, scoped to an article or a chat turn.
- **Staleness Flag**: A signal that a screenshot or article may no longer match the live UI; raised by surface-change events and cleared by author refresh.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 95% of users from any persona can locate the correct Help article for a given task within 60 seconds of opening Help (measured via task-based usability testing).
- **SC-002**: 90% of in-scope chat questions in a representative evaluation set are answered with at least one valid citation, and 100% of out-of-scope questions are refused (zero false-acceptance on a maintained out-of-scope test set).
- **SC-003**: 0 verified cases of chat fabrication (claims not traceable to a cited corpus source) per release, measured continuously against a sampled audit of chat sessions.
- **SC-004**: 0 cross-tenant retrievals or cross-tenant answers occur in any environment (verified by audit log review and red-team test).
- **SC-005**: 100% of primary Hub screens have at least one annotated screenshot in both light and dark modes with alt text and a documented keyboard-equivalent path.
- **SC-006**: WCAG 2.2 AA conformance verified for all Help surfaces and the chat panel, with zero unresolved Level A/AA issues at release.
- **SC-007**: Median time-to-first-useful-answer in chat is under 5 seconds for in-scope questions on a representative connectivity profile.
- **SC-008**: Time-to-competence for a new sector user to complete the persona "first 15 minutes" guide is under 15 minutes for at least 80% of test participants across the operational and sector clusters.
- **SC-009**: Within the first three months of release, the volume of human support requests related to "how do I…" navigation questions decreases by at least 40% compared to the pre-release baseline.
- **SC-010**: 100% of chat interactions are recorded in the append-only audit log with redacted input, citations, and response, retrievable by an Observer-Auditor within their tenant scope.
- **SC-011**: 100% of chat data processing remains within Australian data-residency boundaries (verified by infrastructure attestation per release).
- **SC-012**: Stale-screenshot turnaround: 90% of screenshots flagged stale by a UI change are refreshed within one release cycle.

## Personas — Help Needs by Role *(mandatory)*

### Operational roles (10)

- **Incident Commander**: AIIMS Controller workflow, shared operating picture, public-alert approval flow, cross-jurisdiction escalation, span-of-control warnings, audit traceability.
- **Operations Officer**: Tactical task assignment & reassignment, multi-sector coordination, staging strategy, agent recommendations review, escalation upward to IC.
- **Planning Officer**: Situation reporting, intelligence aggregation, resource forecasting, action plan templates, map overlays, confidence/provenance reading.
- **Logistics Officer**: Supply chain dashboards, transport coordination, forward staging requests, consumption tracking, supplier directory.
- **Public Information Officer**: Multilingual alert composer, accessibility checker, channel selection, IC approval submission, social monitoring view, Constitution Principle V coverage.
- **Field Coordinator**: Mobile/field workflows, degraded-connectivity behaviour, local situation reporting, forward staging accountability, conservative life-safety defaults.
- **Resilience Planner**: Scenario design, simulation configuration & warp playback, gap analysis exports, lessons-learned ingestion from audits.
- **Executive Leader**: Strategic dashboards, cross-jurisdiction status, escalations, policy decision logs, executive briefing exports.
- **Observer-Auditor**: Read-only audit timeline navigation, framework-deviation review, append-only integrity verification, lessons-learned export. Help and chat MUST NOT instruct state-changing actions.
- **Risk Manager**: Hazard assessment, risk levels, consequence analysis, risk-informed decision support, integration with Risk Assessment Agent.

### Sector clusters (~80 agencies, grouped)

- **frontline-fire** (NSW RFS, FRNSW, CFA-VIC, FRV, SAMFS, SACFS, QFD, DFES-WA, TFS, NTFRS, ACT-FR, ACT-RFS, surf-lifesaving, bushfires-NT, ASA): incident intake, jurisdictional theming/filter, resource availability publishing, tasking acknowledgement, mutual-aid handoffs.
- **frontline-medical** (AV, NSW Ambulance, QAS, SAAS, SJA-WA/-NT/-national, AT, ACT Ambulance, RFDS): patient-load reporting, hospital availability views, medical supply requests, retrieval coordination.
- **frontline-police** (VicPol, NSWPF, QPS, SAPOL, WAPOL, TasPol, NTPF, ACT Policing, AFP, ABF): public-safety perimeter coordination, traffic management, evacuation enforcement support, multi-agency liaison.
- **frontline-ses & marine** (SES VIC/NSW/QLD/SA/TAS/ACT, NTES, MRNSW): storm/flood/marine response workflows, volunteer activation, rescue tasking, water-domain situational awareness.
- **commonwealth** (NEMA, ADF, BoM-national, Geoscience Australia, Australian Red Cross): national coordination dashboards, request-for-assistance flows, weather/geo data interpretation, recovery hand-off.
- **cross-sector** (community NGOs, health, local government, state government, territory government, transport, utility, volunteer): partner intake, jurisdictional context, recovery coordination, volunteer activation, infrastructure status reporting.

Each persona/cluster MUST have its own landing page with: role overview, decision rights summary, recommended first-15-minutes tour, screen-by-screen guides for the surfaces the persona uses, and chat starter prompts tuned to the persona.

## Help Content Domains *(mandatory)*

1. **Getting started** — Hub overview, signing in, persona switcher, jurisdiction filter, theme/accessibility settings.
2. **Persona-specific workflows** — One curated journey per operational role and per sector cluster.
3. **Screen-by-screen guides** — Disaster Mapper, Governance Dashboard, Multi-Jurisdiction Filter, Simulation Control, Alert Composer, Agent surfaces (Communication / Evacuation / Monitoring / Risk Assessment / Resource Allocation), Audit/Observer view, Persona switcher, Settings.
4. **Simulation playbook** — Scenario configuration, warp/playback, multi-jurisdiction scenarios, observation export.
5. **Agent playbooks** — One per Communication, Evacuation, Monitoring, Risk Assessment, Resource Allocation agent, including provenance, confidence, and human-approval steps.
6. **Audit & observer mode** — Append-only timeline, framework-deviation review, lessons-learned export.
7. **Accessibility how-tos** — Keyboard navigation, screen-reader use, contrast/theme, multilingual authoring for PIO.
8. **Troubleshooting / FAQ** — Login, persona switching, jurisdiction filter, degraded mode, alert approval failures, simulation reset, chat refusals.
9. **Glossary** — AIIMS, AIDR, jurisdictional, and Hub-specific terms.

## Visual Requirements *(mandatory)*

- Annotated screenshots with numbered callouts on every primary screen and every persona's typical workflow.
- Light and dark mode variants for every screenshot, switching with the active theme.
- Alt text and adjacent keyboard-equivalent step list for every screenshot.
- Visible focus indicators in any embedded interactive examples.
- Stale-screenshot detection with a visible "may be out of date" badge until refreshed.

## Chat Requirements *(mandatory)*

- Grounded ONLY in: Help articles, `docs/corpus/**`, `docs/aidr/**`, and the **Help-approved snapshot** of `specs/**` (Active/Implemented + approved) for the user's tenant. Live `HEAD` of `specs/**` is never grounded.
- Refuses out-of-scope questions with a standard message and a pointer to the right surface or contact.
- Cites every factual claim with deep-linkable inline references.
- Persona- and jurisdiction-aware retrieval; never returns other personas' or other tenants' content.
- PII redaction at the gateway (consistent with spec-036 data-minimisation pattern); user is notified when redaction occurs.
- Australian data residency for all processing, retrieval, storage, and logs.
- Surfaces source conflicts; recommends human verification.
- Disabled with explanation in degraded-connectivity mode.
- All interactions recorded in an append-only audit log retrievable by Observer-Auditors within tenant scope.

## Accessibility *(mandatory)*

- WCAG 2.2 AA conformance for all Help surfaces and the chat panel.
- Full keyboard operability with visible focus indicators and announced status changes.
- Screen-reader compatibility, with text equivalents for all visual content.
- Multilingual capability for Public Information Officer authoring needs (Constitution Principle V), including English plus relevant community languages and Aboriginal & Torres Strait Islander languages where communities are impacted.

## Australian Residency & Tenant Isolation *(mandatory)*

- All chat processing, embeddings/indexes, retrieval, storage, and logs remain within Australian data-residency boundaries per the project Constitution.
- Retrieval and answers are strictly scoped to the active user's tenant and authorised content; cross-tenant retrieval is impossible by design.
- Audit logs of chat interactions are tenant-scoped and append-only.

## Assumptions

- The tenant model, jurisdictional filtering, and persona model defined in spec-001 and spec-022 are reused; this feature does not redefine them.
- The PII redaction / data-minimisation gateway pattern established in spec-036 is reused for chat input pre-processing.
- Constitution principles I (Life Safety First), III (Provenance & Transparency), and V (Multilingual & Accessible Communications) apply unchanged.
- Help UI language is English-only at launch (resolved 2026-05-11; see Clarifications). Multilingual *authoring* support remains required for PIO-produced public communications per Constitution Principle V; multilingual Help UI chrome itself is out of scope for this feature.
- Chat grounding uses an explicitly published "Help-approved" snapshot of `specs/**` (resolved 2026-05-11; see Clarifications). Only specs in `Active`/`Implemented` status that have passed Help-approval review are admitted to the snapshot; draft, experimental, archived, or unreviewed specs are excluded. Snapshots are versioned, auditable, and refreshed on a defined cadence (at minimum each release; out-of-cycle refresh permitted via the same approval gate).
- Stale-screenshot detection relies on a screen-identifier convention to be agreed during design; no specific implementation is mandated here.
- Human-support handoff destinations (e.g., support email, on-call channel) are configurable per tenant — see FR-023a/FR-023b for required record fields and SLA expectations (resolved 2026-05-11 Pass 2).

## Out of Scope

- Localisation of the Help UI itself into non-English languages (only PIO authoring multilingual *content* is in scope).
- Voice-driven chat input/output.
- Public (unauthenticated) help portal.
- Replacing AIIMS doctrine training; Help complements, not replaces, formal training.
- Chat-initiated state changes in the Hub (chat is read-only / advisory; any action it suggests must be performed by the user via the regular UI with existing approval flows).

## Dependencies

- spec-001 (data model: Persona, Organisation, Incident, AuditEntry).
- spec-020 (Disaster Mapper UI) and spec-021 (Governance Dashboard) — primary surfaces to document.
- spec-022 (multi-jurisdiction filter) — jurisdictional context propagation.
- spec-024 (simulation control & chat) and spec-026 (sim warp playback) — simulation playbook content.
- spec-008/009/010/011/012 (Communication, Evacuation, Monitoring, Resource Allocation, Risk Assessment agents) — agent playbooks.
- spec-036 (Foundry RAG grounding & data-minimisation gateway) — chat grounding & PII redaction patterns.
- spec-018/019 (AIDR guidance integration) — `docs/aidr/**` corpus.
- spec-005 (data-source governance) — corpus classification & tenant scoping.
- Constitution principles I, III, V; Australian data-residency NFRs.

## Clarifications

### Session 2026-05-11 (Auto-resolved per constitution + corpus + prior specs)

- **Q: Help UI localisation scope — should the Help Centre UI itself be available in non-English languages at launch, or limited to English with PIO authoring multilingual public-facing content?**
  **A: English-only at launch.** The Help UI chrome (navigation, articles, chat panel) ships in English; PIO multilingual *authoring* of public-facing communications remains in scope per Constitution Principle V.
  *Rationale:* Constitution Principle V's multilingual obligation targets *public-facing warnings* for affected communities (CALD, Aboriginal & Torres Strait Islander, etc.), not internal operator tooling. Help users are authenticated operational/sector personnel within Australian emergency services who operate in English. WCAG 2.2 AA does not require UI localisation. The spec's own "Out of Scope" section already excludes Help-UI localisation. Future expansion may be revisited if community-need data emerges.
  *Citations:* `.specify/memory/constitution.md` §V (Warning and Public Information) and §V-B (Ten Warning Principles); `specs/038-help-docs-chat/spec.md` Out of Scope (Help-UI localisation excluded); spec-024 chat scope (operator-facing, English).

- **Q: Chat answer freshness — should the assistant ground continuously against `specs/**` HEAD, or only against an explicitly published "Help-approved" snapshot?**
  **A: Help-approved snapshot only.** Chat retrieval resolves an explicitly published, versioned snapshot composed of specs in `Active`/`Implemented` status that have passed Help-approval review. Live `HEAD` of `specs/**` is never grounded. Snapshots are auditable (snapshot id, included spec ids+versions, approver identity, approval timestamp) and refreshed at minimum each release, out-of-cycle via the same approval gate.
  *Rationale:* Constitution Principle I (Primacy of Life) makes chat answers safety-relevant during incidents; Warning Principle V-B.3 requires answers be "trusted, authoritative, and verifiable"; Quality Gates require human review before dissemination of public-facing outputs. Surfacing in-flight or experimental requirements to operational users would violate all three. Spec-036 (Foundry RAG + data-minimisation gateway) and spec-005 (data-source governance) both assume a curated, classified corpus model rather than ungated HEAD content. Spec-018/019 (AIDR guidance integration) treats the AIDR corpus as a published reference body, mirroring the snapshot model adopted here.
  *Citations:* `.specify/memory/constitution.md` §I (Primacy of Life), §IV (Transparency and Auditability), §V-B principle 3, Quality Gates ("Public-facing outputs ... reviewed by a human operator before dissemination"); spec-005 (data-source governance / classification); spec-036 (Foundry RAG grounding & data-minimisation gateway); spec-018/019 (AIDR guidance integration as published reference); `specs/038-help-docs-chat/spec.md` Assumptions (Active/Implemented gate already presumed).

### Session 2026-05-11 (Pass 2 — residual ambiguities, auto-resolved)

Pass 2 re-read the spec end-to-end after Pass 1 closed the two retained `[NEEDS CLARIFICATION]` markers. Eight residual ambiguities were material and have been resolved against the constitution + corpus + prior specs (001 / 005 / 021 / 024 / 029 / 036). One area was confirmed already clear and required no edit. Each decision below is bound to a new or amended FR in the body of the spec.

- **Q-P2-01: Snapshot publication mechanics — who approves, what is the rollback procedure, how is content deprecation surfaced to users?**
  **A:** Dual sign-off (Help-content owner + safety/governance lead) is required to publish a snapshot; rollback is performed by re-publishing a previously-approved immutable snapshot id within the spec-029 5-minute reversibility SLO; users following deep links into superseded content see an explicit deprecation notice with a citation to the current equivalent (no silent substitution).
  *Updates:* **FR-011b**, **FR-011c**, **FR-011d**.
  *Citations:* spec-005 FR-015 (dual-authority approval pattern: governance leads + safety leads + system architects); spec-029 FR-008 (5-minute rollback via flag flip, no code redeploy); Constitution Principle IV (Transparency & Auditability — provable provenance); spec-036 A12 (audit-event-on-flip pattern).

- **Q-P2-02: Stale-screenshot governance — what is the concrete detection signal, and what grace period applies before content is escalated?**
  **A:** Detection signal is a deterministic `screen_id_hash = hash(route_id + ordered DOM-element fingerprints of numbered callout anchors)` computed at UI build time and compared against the value stored at screenshot capture; mismatch raises the Staleness Flag immediately. Grace period is **one release cycle** — the "may be out of date" notice shows from flag-raise; if not refreshed by the next release, an additional "screenshots not yet refreshed for this release" banner is added. Articles are never auto-removed (Constitution Principle I).
  *Updates:* **FR-010a**, **FR-010b**.
  *Citations:* spec-005 FR-012b (grace-period-with-warning pattern, default 72 h, never abrupt removal during incidents); spec-036 FR-RAG-FRESH-01/02 (timestamp-based freshness signal precedent); SC-012 (90% refresh-within-one-release target already in this spec); Constitution Principle I (no silencing of safety-relevant guidance).

- **Q-P2-03: Per-tenant support handoff — what is the configuration shape and the SLA expectation when chat refuses or escalates?**
  **A:** Each tenant configures a handoff destination record (channel type, address, business-hours window or 24x7, incident-mode override channel). SLA: 5-minute human acknowledgement during NEMA-Level-3 (or state-equivalent) incidents; 4 business-hours otherwise. SLA breach emits an `audit.support_handoff_unack_timeout` event for Observer-Auditor review. The Hub does not enforce tenant staffing — the SLA is contractual and surfaced via audit, not a system guarantee.
  *Updates:* **FR-023a**, **FR-023b**; **Assumptions** (handoff bullet now back-references FR-023a/b).
  *Citations:* spec-036 Q-P1-03 / FR-RAG-COORD-02 (5-minute escalation-unack timer for safety-relevant escalations); spec-024 FR-040 (NEMA-Level-3 banner / audit-event pattern); Constitution Principle IV (auditability of every escalation event).

- **Q-P2-04: Persona-context resolution — IdP role claim, user selection, or both? What about users with multiple roles?**
  **A:** Default persona is derived from the IdP role claim (highest-authority operational role for multi-role users); the user MAY override via the persona switcher to any persona they are entitled to hold; the **active** persona at each turn is recorded in the audit log alongside its source. Multi-role landing pages show the union of entitled persona tiles ordered by authority rank (highest first); chat uses only the *active* persona, never the union, to prevent leaking guidance scoped to an unentered role.
  *Updates:* **FR-027**, **FR-028**.
  *Citations:* spec-021 FR-025 (multi-AIIMS-role users — combine widgets, highest-authority role first); spec-001 §Personas + Observer/Auditor authority_scope (read-only / audit role definition); Constitution Principle IV (provenance of which persona context shaped each answer).

- **Q-P2-05: Chat conversation persistence — ephemeral or stored, retention, tenancy/audit implications?**
  **A:** Conversations are persisted per-tenant in Cosmos DB within Australian residency boundaries. User-visible **transcripts** retained 30 days (operational data class — strict cap per spec-001 NFR-002). Append-only **audit log** retained 7 years (Privacy Act APP 11 + spec-001 NFR-012; system-audit data class). Both windows enforced by automatic purge. Observer-Auditors may retrieve any audit entry within tenant scope at any time during the 7-year window; older transcripts are reconstructable from the audit log but no longer surfaced in the user's own conversation history.
  *Updates:* **FR-029**, **FR-029a**.
  *Citations:* spec-001 NFR-002 (operational retention ≤30 d / incident evidence 7 y / system audit 7 y) and NFR-012 (≥7-year tamper-evident audit retention); spec-024 plan.md (Cosmos `/tenant_id` partition precedent); spec-036 FR-RAG-COMP-01 (APP 11 7-year retention with encryption at rest); Constitution Non-Negotiable #2 (Australian data sovereignty). **Note:** spec-024 retains sim chat for 2 years because sim chat is part of incident-management exercises (incident-evidence class); Help chat is help/navigation only (operational class) and therefore subject to the 30-day cap. Audit log preserves all reconstruction-relevant content for 7 years.

- **Q-P2-06: Negative chat-feedback closure — queued for content review, or auto-disable the answer?**
  **A:** Queued for human content review only. Negative ratings enter a tenant-scoped content-review backlog visible to Help authors; ≥3 negatives in a 30-day rolling window auto-promote the backlog item to "needs review". Negative feedback **never** auto-disables, hides, or alters articles or chat answers — only humans may withdraw content via the snapshot approval gate (FR-011b).
  *Updates:* **FR-022a**.
  *Citations:* Constitution Principle I (Primacy of Life — no silencing of safety-relevant guidance; humans must remain in the loop); spec-036 FR-RAG-CA-04 / A12 (Locked-on / human-in-loop pattern for safety-relevant gates); spec-005 FR-012b (warn-and-grace, never abrupt removal); FR-022 baseline (feedback retained for content improvement).

- **Q-P2-07: Degraded-connectivity behaviour — exactly which features remain available, what cache TTL applies?**
  **A:** Cached and available offline: previously-viewed Help articles, the full glossary, and the curated troubleshooting/FAQ topics. Unavailable offline: the chat assistant (visibly disabled per FR-026), free-text search across uncached corpus, and any retrieval against `docs/aidr/**`, `docs/corpus/**`, or the spec snapshot. Cache TTL = **14 days**; per-device footprint stays within the ≤500 MB envelope shared with the Field Coordinator offline cache (not additive). On reconnect an audit-logged refresh occurs; cached articles past TTL display a "may be stale — last cached `<date>`" banner until refreshed.
  *Updates:* **FR-026a**, **FR-026b**.
  *Citations:* spec-036 FR-RAG-LS-02 (≤500 MB cache cap, 14-day TTL, audit-logged refresh on re-sync, dual-signature integrity); FR-021 + Help Content Domains §8 (troubleshooting/FAQ enumerated topics); existing FR-026 (chat disabled with explanation in degraded mode); Constitution Principle I (life-safety guidance must remain readable when offline).

- **Q-P2-08: Accessibility — how are non-English embedded glossary terms (e.g., AIIMS-adjacent terms, Aboriginal & Torres Strait Islander language items, place names) announced by screen readers?**
  **A:** Embedded non-English fragments MUST carry a correct `lang` attribute (HTML `lang`, or screen-reader-API equivalent on non-HTML surfaces) per WCAG 2.2 SC 3.1.2 (Language of Parts) so assistive technologies switch to the correct phoneme set. The Help-UI surface itself remains English (Pass 1 decision); this requirement governs *embedded fragments* within otherwise-English content.
  *Updates:* **FR-009a**.
  *Citations:* WCAG 2.2 Success Criterion 3.1.2 (Language of Parts, Level AA — already required by FR-009's blanket WCAG 2.2 AA conformance, made explicit here); Constitution §V-B (cultural authority — correct pronunciation of Aboriginal & Torres Strait Islander language is part of respectful warning communication); Pass 1 Help-UI English-only decision (scope clarification — embedded fragments are not UI localisation).

- **Q-P2-09 (confirmed clear, no edit): Observer-Auditor read-only enforcement — can observers query chat freely, or are write-side workflow questions blocked?**
  **A (no change):** Observers MAY query the chat freely. The "read-only" constraint applies to *the actions chat instructs the user to take* — FR-025 already requires chat to "tailor guidance to observation/audit actions and MUST NOT instruct the user to perform state-changing operations". There is no restriction on the *questions* an Observer-Auditor may ask; chat answers them within the same grounded corpus and tenant scope as any other persona, but framed for observation/audit. No FR change required; FR-025 is sufficient.
  *Citations:* FR-025 (existing); spec-001 §Personas Observer/Auditor `authority_scope: Read-only / audit`; Edge Case "Audit-mode user (read-only)" in this spec.

**Pass 2: 8 material clarifications resolved + 1 confirmed already clear. Spec is ready for `/speckit.plan`.**

### Session 2026-05-11 (Pass 3 — checklist gap analysis, auto-resolved)

The `speckit.checklist` run (CHK001–CHK136) surfaced 10 residual ambiguities. Each is bound to an `*-AMEND` clause in the Functional Requirements section above. Source authority: same hierarchy as Pass 1 / Pass 2 (Constitution + corpus + prior specs).

1. **FR-011 corpus tenancy** → FR-011-AMEND (global vs tenant-scoped sources delineated).
2. **FR-022a chat-answer pattern identity** → FR-022a-AMEND (intent-cluster + citation-set tuple).
3. **FR-009a `lang` enforcement mechanism** → FR-009a-AMEND (authoring-time + build-time gates).
4. **FR-026a degraded-mode search-scope indicator** → FR-026a-AMEND (persistent banner).
5. **FR-027 authority rank back-reference** → FR-027-AMEND (single shared registry).
6. **FR-023a incident-mode auto-detection** → FR-023a-AMEND (NEMA-Level-3 banner auto, optional manual sub-Level-3 override).
7. **SC-009 baseline definition** → SC-009-AMEND (2-week pre-launch observation window).
8. **FR-029 transcript visibility post-purge** → FR-029b (audit-tooling-only reconstruction surface).
9. **FR-011d no-replacement deprecation** → FR-011d-AMEND (withdrawn-no-replacement notice + handoff).
10. **FR-010a route-rename behaviour** → FR-010a-AMEND (bulk re-baseline workflow via route registry).

**Pass 3: 10 checklist-surfaced gaps resolved.**

## Clarifications Needed

_All open clarifications resolved on 2026-05-11 (Pass 1 + Pass 2) — see "Clarifications" section above._

## Analysis Resolutions

> Auto-resolutions applied during the `/speckit.analyze` cross-artefact consistency pass on 2026-05-11. Each entry: **issue → decision → authority citation → files changed**. No clarifications were left for the user — all items resolved per the constitution + prior-spec authority hierarchy under the user's auto-resolution mandate.

1. **AR-001 — Transcript retention 90 days violated spec-001 NFR-002 operational data-class cap** → Reduced user-visible transcript retention from 90 days to **30 days** (operational data class). Audit log retention remains 7 years (system-audit class). Rationale: spec-001 NFR-002 strictly bounds operational class at ≤30 d; Help chat is help/navigation only and never instructs state-changing operations (FR-025), so it is operational rather than incident-evidence; reconstruction needs are met by the 7-year audit log via FR-029a/b. *Citations:* spec-001 NFR-002 (`retention ≤ {operational: 30 d, incident evidence: 7 y, system audit: 7 y}`); spec-001 NFR-012 (≥7 y audit retention); Constitution Principle IV (auditability). *Files changed:* `spec.md` FR-029, FR-029a, Pass 2 Q-P2-05; `data-model.md` entity table, `ChatSession`, Bicep mapping; `contracts/help-api.openapi.yaml` `/help/chat/sessions/{sessionId}` summary; `checklists/feature.md` CHK069, CHK073; `checklists/requirements.md` notes; `tasks.md` T-AA013, T-AA036, T-AA060.

2. **AR-002 — `pattern_id` hasher used `sorted(citation_source_ids)` but FR-022a-AMEND mandates "exact ordered set"** → T-AA050 rewritten to preserve exact citation order returned by the assistant; sorting is explicitly forbidden. Two answers with the same intent cluster but different citation orders therefore yield different `pattern_id`s, matching the spec's "iff both fields match" semantics. *Citations:* `spec.md` FR-022a-AMEND ("the **exact ordered set** of source citations returned"). *Files changed:* `tasks.md` T-AA050.

3. **AR-003 — `screen_id_hash` hasher used `sorted(callout.anchor_dom_path)` but FR-010a mandates "ordered set of DOM-element fingerprints corresponding to each numbered callout anchor"** → T-AA051 rewritten to sort callouts by `Callout.number` ascending and emit anchors in that order (callout-number ordering, not lexicographic anchor sort). Reordering callouts changes the hash. *Citations:* `spec.md` FR-010a ("the ordered set of DOM-element fingerprints corresponding to each numbered callout anchor"). *Files changed:* `tasks.md` T-AA051.

4. **AR-004 — Phase 6 dependency contradiction in `tasks.md` Phase Map** → Phase 6 (snapshot publication) "Depends on: Phases 1, 3, 5, 7" yet the Phase Map listed Phases 6 and 7 in parallel after Phase 5. Snapshot publisher actually invokes the freshness and `lang`-attribute linters, so 7 must precede 6. Reordered Phase Map rows so Phase 7 appears before Phase 6, and updated the linear dep chain to `0 → (1, 2 in parallel) → (3, 4 partial parallel) → 5 → 7 → 6 → 8 → 9 → 10`. Phase numbers preserved for cross-reference traceability. *Citations:* `tasks.md` Phase 6 stated dependencies. *Files changed:* `tasks.md` Phase Map, Phase dependencies note.

5. **AR-005 — OpenAPI contract missing two screenshot routes called out by `tasks.md` T-AA075** → T-AA075 specified `POST /help/screenshots/staleness/{id}/clear` (author-only flag clear) and `GET /help/screenshots/{screen_id}/url?theme=light|dark` (signed-URL issuance for the active-theme variant). Neither was in `help-api.openapi.yaml`. Added both endpoints to the OpenAPI contract with full schemas (signed URL envelope: `{ url, expires_at, theme }`; 5-minute expiry per existing platform Blob signed-URL convention). *Citations:* `tasks.md` T-AA075; `spec.md` FR-007 (theme-aware screenshot serving), FR-010b (clear after refresh). *Files changed:* `contracts/help-api.openapi.yaml`.

6. **AR-006 — CHK reference drift in `tasks.md` task-line annotations** → Many individual task lines reference CHK ids that do not align 1:1 with current `checklists/feature.md` numbering (CHK001…CHK136), apparently written against an earlier checklist draft. The authoritative FR/SC ↔ Task coverage is the **Verification Matrix** at the end of `tasks.md` (which is consistent: 0 orphan FRs, 0 orphan SCs). Did not bulk-rewrite ~150 inline CHK refs (low-value, high-noise change); instead recorded this resolution so future readers know the Verification Matrix is canonical for FR/SC traceability and that release sign-off (T-AA220) walks the checklist directly rather than relying on inline task-line CHK refs. *Citations:* `tasks.md` Verification Matrix preamble ("Orphan FRs: 0; Orphan SCs: 0"); T-AA220 ("Walk every CHK001–CHK136 entry in `checklists/feature.md`"). *Files changed:* none required (documentation-only resolution); future bulk-renumber may run as a separate housekeeping pass.

**Analysis pass summary**: 6 issues found, 6 auto-resolved, 0 left for the user. Constitution alignment re-verified; all FR↔task coverage preserved (Verification Matrix unchanged); cross-spec citations (spec-001 NFR-002/NFR-012, spec-005 FR-015, spec-021 FR-025, spec-024, spec-029 FR-008, spec-036 FR-RAG-LS-02 / FR-RAG-COMP-01 / FR-RAG-COORD-02 / FR-RAG-CA-04 / FR-RAG-AG-01 / FR-RAG-IDX-04 / A12) all verified to exist in their target specs.
