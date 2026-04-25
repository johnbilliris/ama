# Feature Specification: Automated Demo Script

**Feature Branch**: `016-automated-demo-script`  
**Created**: 2025-07-18  
**Status**: Draft  
**Input**: User description: "Create a reproducible, automated demo script that exercises the full disaster response pipeline end-to-end with seed data. The script starts all 5 agents, ingests simulated disaster signals, drives the pipeline through monitoring → risk assessment → evacuation/resource allocation/communication, and produces observable outputs (health checks, pipeline responses, alert drafts). It should be runnable in CI as a smoke test and locally for live demonstrations."

## Clarifications

### Session 2026-04-12

- Q: SC-004 lists 7 pipeline phases but FR/entities reference only 5 agent-mapped stages — which is canonical? → A: 7 phases. Five agents execute the inner phases; "activation" (startup + health checks) and "audit summary" (post-pipeline report) are script-level orchestration phases.
- Q: What is the structured output format and destination? → A: JSON. Default to stdout; optional `--output <path>` flag writes to file.
- Q: FR-008 says "verbose/interactive mode" — are these distinct modes or one? → A: Two modes only: CI (default, silent, auto-approve, <60s) and verbose (`--verbose`, narrated output, auto-approve with narration, <5min). Drop "interactive" — no user prompts in either mode.
- Q: Where does the script live and what is the CLI interface? → A: `scripts/demo.py`, Python CLI with `argparse`. Invoked as `python scripts/demo.py [--verbose] [--scenario bushfire] [--output summary.json]`.
- Q: On mid-pipeline agent failure, should the script fail-fast or attempt remaining stages? → A: Fail-fast. Stop at first stage failure, report which agent/stage failed, exit non-zero. Aligns with CI gate semantics and Constitution §I (degrade safely → conservative guidance).

## User Scenarios & Testing *(mandatory)*

### User Story 1 — End-to-End Pipeline Smoke Test (Priority: P1)

As a **developer or CI pipeline**, I want to run a single command that exercises the entire disaster response pipeline from signal ingestion through alert drafting, so that I can verify the full system works correctly after every change.

**Why this priority**: This is the core value of the feature — a single-command, zero-dependency smoke test that proves all five agents cooperate correctly. Without this, the demo script has no value. This directly addresses the rubric gap: Application Demo must show a working, reproducible end-to-end flow.

**Independent Test**: Can be fully tested by running the demo script in an environment with no Azure credentials and verifying it exits with a success code and produces structured output summarizing every pipeline stage.

**Acceptance Scenarios**:

1. **Given** a clean checkout with no Azure credentials configured, **When** the operator runs the demo script, **Then** all five agents start, the pipeline completes all stages (monitoring → risk assessment → evacuation → resource allocation → communication), and the script exits with code 0.
2. **Given** the demo script is running, **When** each agent is initialised, **Then** a health check confirms the agent is ready before the pipeline proceeds.
3. **Given** the pipeline has completed, **When** the script finishes, **Then** it outputs a structured summary including the result of each stage (signal ingested, risk assessed, evacuation route proposed, resources allocated, alert drafted) with pass/fail status for each.
4. **Given** any single agent fails its health check or returns an error, **When** the script detects the failure, **Then** it reports which agent failed, what stage was reached, and exits with a non-zero code.

---

### User Story 2 — Live Demonstration for Stakeholders (Priority: P2)

As a **presenter** (architect, incident commander, or executive leader), I want to run the demo script with human-readable, step-by-step output so that I can walk stakeholders through the disaster response pipeline in under 5 minutes during a live demonstration.

**Why this priority**: The demo is the primary vehicle for rubric scoring. A live, narrated walkthrough showing governance controls, human-in-the-loop approval, and cross-agency coordination directly addresses the Executive Leader, Incident Commander, and Public Information Officer feedback.

**Independent Test**: Can be fully tested by running the demo in verbose mode (`--verbose`) and confirming that output includes labelled stages matching the existing walkthrough steps, with clear descriptions suitable for non-technical stakeholders.

**Acceptance Scenarios**:

1. **Given** the demo script is invoked in verbose mode, **When** each pipeline stage completes, **Then** the script prints a human-readable description of the stage, the inputs used, the decision made, and the output produced.
2. **Given** the pipeline reaches the risk assessment stage, **When** a recommendation is generated, **Then** the output shows the recommendation details, the supporting signal identifiers, and a simulated human approval gate confirming the recommendation was reviewed.
3. **Given** the pipeline reaches the communication stage, **When** alert drafts are generated, **Then** the output shows draft alerts in at least six languages (en-AU, zh-Hans, ar, vi, el, it) with channel distribution targets.
4. **Given** the complete demo, **When** the presenter reviews the output, **Then** the full walkthrough completes in under 5 minutes wall-clock time.

---

### User Story 3 — Governance and Auditability Demonstration (Priority: P2)

As an **executive leader** or **incident commander**, I want the demo to visibly demonstrate governance controls — policy escalation, resource approval workflows, decision audit trails, and AIIMS-aligned handoffs — so that I can confirm the system meets governance and accountability requirements.

**Why this priority**: The Executive Leader and Incident Commander specifically called out governance, auditability, and human-in-the-loop controls. The demo must make these visible to move the rubric score beyond Satisfactory.

**Independent Test**: Can be tested by running the demo and verifying that the structured output contains audit trail entries for every decision point, including who/what approved each action, timestamps, and the policy or framework that governed the decision.

**Acceptance Scenarios**:

1. **Given** the pipeline produces a safety-critical recommendation (e.g., evacuation order), **When** the recommendation is processed, **Then** the demo output shows a human approval gate was invoked, the approval decision, and the approver role.
2. **Given** the pipeline allocates resources, **When** the allocation decision is made, **Then** the output records the allocation criteria, the policy applied, and the resource quantities assigned.
3. **Given** the demo completes, **When** the audit trail is reviewed, **Then** every cross-agent handoff includes source agent, destination agent, timestamp, data passed, and confidence level.
4. **Given** the demo scenario, **When** a decision exceeds a configured threshold (e.g., large-scale evacuation), **Then** the output shows a policy escalation event with the escalation reason and the authority level required.

---

### User Story 4 — Seed Data and Scenario Configuration (Priority: P3)

As a **developer** or **tester**, I want the demo script to load realistic seed data from the existing data directory and use a configurable disaster scenario, so that demonstrations are reproducible and can be adapted for different disaster types.

**Why this priority**: Reproducibility and scenario flexibility are important for testing and for tailoring demonstrations to different audiences (e.g., bushfire for NSW/VIC stakeholders, cyclone for QLD/NT), but the core pipeline must work first.

**Independent Test**: Can be tested by running the demo with the default bushfire scenario and verifying it loads seed data correctly, then re-running with a different scenario flag and confirming the outputs change appropriately.

**Acceptance Scenarios**:

1. **Given** the demo is invoked with the default scenario, **When** seed data is loaded, **Then** the script uses bushfire-specific data (population, road networks, resource inventories, alert templates) from the existing data directory.
2. **Given** the demo is invoked with a custom scenario parameter, **When** the scenario is loaded, **Then** the pipeline uses the corresponding seed data and produces outputs consistent with that disaster type.
3. **Given** the seed data directory is missing a required file, **When** the script starts, **Then** it reports the missing file clearly and exits with a non-zero code before starting any agents.

---

### Edge Cases

- What happens when one agent's health check passes but the agent fails mid-pipeline? The script MUST fail-fast: stop at the first stage failure, report which agent failed and at what stage, and exit with a non-zero code. Remaining stages are not attempted.
- What happens when seed data files are corrupt or contain invalid data? The script must validate seed data on load and report specific validation errors before starting the pipeline.
- What happens when the script is run in CI without a terminal (no TTY)? The script must produce valid structured output regardless of whether a terminal is attached, with no interactive prompts in non-verbose mode.
- What happens when the demo is interrupted mid-run (e.g., Ctrl+C)? The script must clean up any in-memory state and exit cleanly without leaving orphaned processes.
- What happens when alert template files are missing for one or more languages? The pipeline must still complete for available languages and report which languages were skipped.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The demo script MUST be invocable as a single command from the repository root: `python scripts/demo.py`. The script uses `argparse` with flags `--verbose`, `--scenario <type>`, and `--output <path>`.
- **FR-002**: The demo script MUST start all five agents (monitoring, risk assessment, evacuation, resource allocation, communication) and the platform API (`apps/api/app/main.py`) as in-process TestClients and verify each is healthy before proceeding.
- **FR-003**: The demo script MUST run without any external service dependencies — no live Azure services, no network connections, no running databases.
- **FR-004**: The demo script MUST load seed data from the existing data directory, including alert templates, population data, road network data, and resource inventory data.
- **FR-005**: The demo script MUST ingest at least one simulated disaster signal (bushfire scenario by default) into the monitoring agent and propagate it through the full pipeline.
- **FR-006**: The demo script MUST produce a JSON-formatted structured output summarising every pipeline phase (all 7: activation, ingestion, risk analysis, evacuation routing, resource allocation, alert drafting, audit summary) with pass/fail status, inputs consumed, and outputs produced. Output goes to stdout by default; `--output <path>` writes to file instead.
- **FR-007**: The demo script MUST exit with code 0 on full pipeline success and a non-zero code on any failure, suitable for CI gate usage.
- **FR-008**: The demo script MUST include a verbose mode (`--verbose`) that prints human-readable, narrated descriptions of each stage suitable for live demonstrations. No interactive prompts are used; approval gates are auto-approved with narration.
- **FR-009**: The demo script MUST demonstrate human-in-the-loop approval gates for safety-critical decisions (evacuation recommendations, resource allocation above threshold) using simulated approvals.
- **FR-010**: The demo script MUST produce multilingual alert drafts in at least six languages (en-AU, zh-Hans, ar, vi, el, it) using seeded alert templates.
- **FR-011**: The demo script MUST record an audit trail for every decision point, including the agent responsible, the decision made, supporting data references, timestamps, and the governance policy applied.
- **FR-012**: The demo script MUST show explicit cross-agent handoffs with source agent, destination agent, data transferred, and confidence levels.
- **FR-013**: The demo script MUST complete the full pipeline in under 60 seconds wall-clock time in CI environments.
- **FR-014**: The demo script MUST validate seed data completeness on startup: structural files (population data, road network, resource inventory) are mandatory and cause abort on absence; individual language template files are expected but degradable — missing templates produce a warning and the pipeline continues for available languages (see Edge Case 5).
- **FR-015**: The demo script MUST use a realistic bushfire disaster scenario by default, consistent with the Constitution's Life Safety First principle and the existing scenario-based testing requirement.
- **FR-016**: The demo script MUST support a configurable scenario parameter to allow different disaster types (bushfire, cyclone, flood) for tailored demonstrations.
- **FR-017**: The demo script MUST produce output that demonstrates the AIIMS-aligned workflow: activation → ingestion → analysis → recommendation → approval → alert publishing.

### Key Entities

- **Demo Run**: A single execution of the demo script; attributes include run identifier, scenario type, start time, end time, overall pass/fail status, and the ordered list of stage results.
- **Pipeline Stage**: One step in the disaster response pipeline; the full pipeline comprises 7 phases: activation (script startup and health checks), ingestion (monitoring agent), risk analysis (risk assessment agent), evacuation routing (evacuation agent), resource allocation (resource allocation agent), alert drafting (communication agent), and audit summary (script-level post-pipeline report). Each phase has attributes: phase name, responsible agent (or "orchestrator" for activation/audit summary), inputs, outputs, duration, and pass/fail status.
- **Simulated Signal**: A seed disaster event ingested by the monitoring agent; attributes include signal type, source provenance, location, severity, and timestamp.
- **Decision Record**: An audit entry for a human-in-the-loop or automated decision; attributes include decision type, approver role, policy applied, approval status, supporting data references, and timestamp.
- **Alert Draft**: A communication output produced by the communication agent; attributes include language, channel target, content body, safety validation status, and approval mode.
- **Stage Handoff**: A data transfer between two agents; attributes include source agent, destination agent, payload summary, confidence level, and timestamp.

## Assumptions

- The existing `create_app()` factory pattern for each agent supports in-process instantiation without binding to TCP ports, consistent with the existing TestClient usage in rehearsal tests.
- Template-based fallback responses are adequate for the demo and smoke test — live LLM integration is not required and the demo explicitly avoids it.
- The existing alert template JSON files in `data/alert-templates/` cover all six required languages and follow a consistent schema.
- The existing seed data (population, road networks, resource inventories) is sufficient to drive a realistic bushfire scenario without generating new data.
- The simulated human approval gate uses an auto-approve mechanism (approval is always granted) to keep the demo deterministic and scriptable; verbose mode narrates the approval as if a human reviewed it.
- The bushfire scenario is the primary/default scenario; cyclone and flood scenarios are stretch goals that reuse the same pipeline with different seed data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The demo script completes the full five-agent pipeline end-to-end in a single command with exit code 0, achieving 100% stage pass rate on every run.
- **SC-002**: The demo walkthrough (verbose mode) completes in under 5 minutes wall-clock time, matching the target from the existing demo walkthrough document.
- **SC-003**: The CI smoke test (non-verbose mode) completes in under 60 seconds wall-clock time.
- **SC-004**: The structured output covers all 7 pipeline phases (activation, ingestion, risk analysis, evacuation routing, resource allocation, alert drafting, audit summary) with verifiable pass/fail per stage.
- **SC-005**: Alert drafts are produced in all 6 target languages (en-AU, zh-Hans, ar, vi, el, it) on every successful run.
- **SC-006**: The audit trail contains a decision record for every safety-critical action, with 100% of handoffs between agents documented with source, destination, timestamp, and confidence.
- **SC-007**: The Application Demo rubric score improves from 3 (Satisfactory) to 4 or higher (Good/Excellent) as assessed by the rubric evaluation criteria.
- **SC-008**: The demo runs successfully with zero external service dependencies — no Azure credentials, no network access, no running databases required.


## Personas

Authored against the `specs/027-spec-hardening/contracts/persona-profile.md` schema. AU-v1 personas are validated; PH / JP / BD entries are explicit placeholders pending capstone-reinterpretation (D-009) and SME validation per FR-023.

- **PER-040**: cross-ref to `specs/001-disaster-response-hub/spec.md` AIIMS personas (Incident Commander / Planning Officer / Operations Officer / Logistics Officer / Public Information Officer) per `specs/027-spec-hardening/contracts/persona-profile.md`. `status:` validated. `preconditions:` none.
- **PER-041**: cross-ref to `specs/004-actor-github-agents/spec.md` actor catalogue covering all `.github/agents/technical/*.agent.md` actors. `status:` validated. `preconditions:` none.
- **PER-042** [non-AU placeholder]: capstone-country operator personas for PH (NDRRMC), JP (Cabinet Office DRR / FDMA), BD (DDM / CPP volunteers). `status:` placeholder. `preconditions:` capstone-reinterpretation decision per D-009; SME validation via `ama-rubric-grader`-vetted SME interviews.

## Hypotheses

Hypotheses use the FR-018 statement format (`If <condition> then <observable>`) and link to a structured evidence stub conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. Capstone-country hypotheses for this spec's agent ownership (where applicable) are allocated in feature 028 / US2.

- **HYP-014**: If the actors named in `specs/004-actor-github-agents/spec.md` consult on every change to this spec via the `agent` tool, then the AMA rubric criterion mean (Assumptions / Requirements / Personas / Hypotheses / Scope) for this spec rises by at least +1 band relative to the baseline captured in `specs/028-capstone-alignment/evidence/rubric-baseline.md`. **Falsification**: post-feature rubric snapshot shows a regression in any of those five criteria for this spec. **Evidence stub**: `specs/028-capstone-alignment/evidence/HYP-HYP-014.md` (created in feature 028 polish).

## Out of Scope

- This spec is delivery-hygiene / enabling infrastructure; capstone-outcome-critical-path ownership lives in specs 001, 020, 021, 022, 023.

Items explicitly deferred from this spec; promotion to in-scope requires the named preconditions to clear. Cross-references to other specs use the canonical overlap phrasing (`authoritative for: <capability>` / `defers-to: <NNN> (<capability>)`).

- **SCP-044** [DEFERRED]: Capstone-country variants (PH typhoon, JP earthquake, BD flood) of this spec's capabilities are out of scope until: (i) capstone-reinterpretation decision per D-009; (ii) per-country regulatory + data-sharing preconditions documented in `specs/005-data-source-governance/spec.md` clear; (iii) responsible technical agents (product-owner-ba, qa-test-engineer) sign off on country-specific calibration.
- **SCP-045**: Constitutional-level changes (NON-NEGOTIABLE #1..#5) are not modified by this spec; any tension is documented as `[RISK]` in Assumptions, never resolved here.
- **SCP-046**: Cross-spec authority disputes are arbitrated via `product-owner-ba` and the speckit governance flow; this spec does not unilaterally claim ownership of capabilities owned elsewhere. `defers-to:` 018 (recovery-phase indicators, triggers, phase-exit criteria); 008 (warning-tier authoring, multilingual delivery, misinformation defence) where applicable.
- **SCP-047** [META]: This spec is delivery-hygiene / enabling infrastructure; capstone-outcome-critical-path ownership lives in specs (canonical list — see the verbatim bullet inserted by feature 028 / US4 elsewhere in this section). (See `specs/028-capstone-alignment/contracts/meta-spec-flag.contract.md`; the verbatim canonical bullet is added in US4.)


