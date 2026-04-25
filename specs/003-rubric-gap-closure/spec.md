# Feature Specification: Rubric Gap Closure — AI Integration, CI/CD, and Agent Depth

**Feature Branch**: `003-rubric-gap-closure`  
**Created**: 2026-03-16  
**Status**: Draft  
**Input**: User description: "Close rubric evaluation gaps: integrate Azure OpenAI in agents, complete CI/CD pipeline, deepen agent orchestration, add Dockerfiles and IaC for application resources"

## Clarifications

### Session 2026-03-16

- Q: Should this feature include work on remaining rubric gaps (Application Demo 4/5, Error Handling & Alerting 4/5, Performance & Reliability 4/5), or are they out of scope? → A: All rubric gaps are in scope.
- Q: Which languages should the Communication agent produce by default in multilingual alert drafts? → A: All 6 supported languages (en-AU, zh-Hans, ar, vi, el, it) in every draft.
- Q: What should happen to queued handoffs that cannot be delivered when the target agent's circuit is open? → A: Queue to the dead-letter store (FR-025) with 3 retries over 5 minutes, then mark as failed for operator review.
- Q: How should performance regression testing coexist with the CI time budget? → A: Lightweight benchmark in CI (every PR, <60s); full load test on nightly schedule or manual trigger.
- Q: What should happen when LLM-generated alert content fails content safety validation? → A: Fall back to the deterministic template output (same as FR-004), log the safety failure with flagged content for post-hoc review.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Agents produce AI-generated outputs for live incidents (Priority: P1)

An incident commander activates an incident and ingests signals. The specialist agents — Risk Assessment and Communication — use a large language model to generate natural-language recommendation explanations and multilingual public alert drafts from the signal context. The outputs include clear rationale, supporting evidence citations, and confidence indicators. A human reviewer can assess the quality of the AI-generated content before acting on it.

**Why this priority**: The rubric evaluation scored "AI model selection and deployment" at Satisfactory (3/5) and "Use of AI technologies" at Good (4/5). Both criteria cited the absence of actual model integration as the primary gap. Closing this gap has the highest point-per-effort impact on the overall grade.

**Independent Test**: Can be fully tested by ingesting a set of mixed-provenance signals for a simulated bushfire incident and verifying that the Risk Assessment agent returns an LLM-generated explanation with cited signal IDs, and the Communication agent returns a multilingual alert draft in at least two languages, both within acceptable latency and token budgets.

**Acceptance Scenarios**:

1. **Given** a set of ingested authoritative and community signals for an active incident, **When** the Risk Assessment agent generates a recommendation, **Then** the recommendation includes a natural-language explanation that references specific signals by ID, states the confidence level, and was produced by a language model rather than a hard-coded template.
2. **Given** a recommendation of type public_alert has been approved, **When** the Communication agent drafts the public alert, **Then** the draft contains content blocks in all 6 supported languages (en-AU, zh-Hans, ar, vi, el, it), follows plain-language accessibility guidelines, and was produced by a language model.
3. **Given** the language model endpoint is unavailable or returns an error, **When** an agent attempts to generate content, **Then** the agent falls back to a deterministic template-based output, marks the output as "template_fallback", and logs the model failure with correlation ID.
4. **Given** the language model returns content that exceeds the configured token budget, **When** the agent processes the response, **Then** the agent truncates or re-requests within budget and logs the overage.

---

### User Story 2 — Every code change is automatically validated before merge (Priority: P2)

A developer pushes a commit or opens a pull request. The CI pipeline automatically runs all Python tests (contract, integration, simulation), checks code quality (linting, type checking), builds the web application, and reports pass/fail status on the PR. No code reaches the main branch without passing the full quality gate.

**Why this priority**: The rubric evaluation scored "Deployment and CI/CD" at Satisfactory (3/5), noting the pipeline only validates file existence. Automated test execution is the single most impactful improvement for development confidence and rubric score.

**Independent Test**: Can be fully tested by creating a PR with a deliberately failing test and verifying the pipeline blocks merge, then fixing the test and verifying the pipeline passes.

**Acceptance Scenarios**:

1. **Given** a developer pushes to a feature branch or opens a PR, **When** the CI pipeline runs, **Then** it executes all Python tests, Python linting, TypeScript type-checking, and the web application build, and reports granular pass/fail for each stage.
2. **Given** a test failure occurs in any stage, **When** the pipeline completes, **Then** the PR is marked as failing with a clear indication of which stage and test failed.
3. **Given** all stages pass, **When** the pipeline completes, **Then** the PR is marked as passing and eligible for merge.

---

### User Story 3 — Agents coordinate dynamically through event-driven handoffs (Priority: P3)

During an active incident, when the Monitoring agent classifies an incoming signal as high-risk, it automatically triggers the Risk Assessment agent via a typed handoff through the event bus. The Risk Assessment agent processes the signal context, and if its recommendation warrants public communication, it issues a further handoff to the Communication agent. Each handoff is scoped to the incident tenant, recorded in the audit timeline, and visible in the operator dashboard.

**Why this priority**: The rubric scored "Autonomy and orchestration" and "Multi-agent coordination" at Good (4/5), citing minimal agent stubs and absence of dynamic chaining. Implementing event-driven handoff execution deepens the agentic behavior scores.

**Independent Test**: Can be fully tested by ingesting a high-risk authoritative signal and verifying that the system automatically chains Monitoring → Risk Assessment → Communication without manual intervention, with each handoff recorded as a timeline event.

**Acceptance Scenarios**:

1. **Given** the Monitoring agent receives a signal classified as high-risk, **When** it completes classification, **Then** it publishes a typed handoff to the Risk Assessment agent via the event bus, scoped to the incident's tenant.
2. **Given** the Risk Assessment agent produces a recommendation of type public_alert with high confidence, **When** the recommendation is stored, **Then** it publishes a typed handoff to the Communication agent to draft an alert.
3. **Given** any agent-to-agent handoff occurs, **When** the handoff is processed, **Then** a TimelineEvent is recorded with the source agent, target agent, scope key, confidence, and payload summary.
4. **Given** the target agent's circuit breaker is open, **When** a handoff is attempted, **Then** the handoff is retried up to 3 times over 5 minutes; if all retries fail, the handoff is stored in the dead-letter store, the originating agent is notified, and the dashboard reflects the failed handoff status.

---

### User Story 4 — Application containers are deployable from source (Priority: P4)

A platform operator builds container images for the API service and the agent runtime from the repository, pushes them to a container registry, and deploys them to the target environment. The container definitions are version-controlled, reproducible, and follow security best practices (non-root user, minimal base image, no secrets baked in).

**Why this priority**: The rubric noted missing Dockerfiles as a gap under CI/CD and Implementation Completeness. Container definitions are a prerequisite for any cloud deployment and close a concrete gap.

**Independent Test**: Can be fully tested by building each Dockerfile locally, running the resulting container, and verifying the health endpoint responds.

**Acceptance Scenarios**:

1. **Given** the API application source code, **When** the Dockerfile is built, **Then** the resulting image starts the FastAPI server, exposes the health endpoint, runs as a non-root user, and contains no embedded secrets or credentials.
2. **Given** the agent runtime source code, **When** the Dockerfile is built, **Then** the resulting image starts the agent worker process, runs as a non-root user, and can reach the API service.
3. **Given** either Dockerfile, **When** it is rebuilt after a code change, **Then** the build uses layer caching effectively and completes within 5 minutes for a clean build or 2 minutes for an incremental (code-only) change.

---

### User Story 5 — Infrastructure for application resources is defined as code (Priority: P5)

A platform engineer provisions the full application environment — container hosting, database, cache, storage, and AI model endpoint — from version-controlled infrastructure definitions. The definitions enforce Australian data residency, enable monitoring integration, and follow least-privilege access patterns.

**Why this priority**: The rubric noted that Bicep templates exist only for monitoring, not for the application resources themselves. Completing IaC closes gaps in both CI/CD and Performance/Reliability scores.

**Independent Test**: Can be fully tested by running a what-if deployment of the infrastructure definitions and verifying all resources are created in the correct Australian region with expected configurations.

**Acceptance Scenarios**:

1. **Given** the infrastructure definitions, **When** a what-if deployment is executed, **Then** it plans creation of the container hosting environment, database account, cache instance, blob storage account, and AI model endpoint, all in an Australian Azure region.
2. **Given** the infrastructure definitions, **When** they are deployed, **Then** the monitoring resources (Log Analytics, Application Insights) are connected to the application resources via diagnostic settings.
3. **Given** the infrastructure definitions, **When** reviewed for security, **Then** all resources use managed identity for inter-service authentication, no connection strings are stored in plain text, and network access follows least-privilege rules.

---

### User Story 6 — Executive-ready demo walkthrough (Priority: P6)

A program evaluator or executive stakeholder views a recorded demo walkthrough and accompanying slide deck that demonstrates the hub's core incident workflow end-to-end. The demo tells a specific disaster story, shows the shared operating picture, persona workspace, approval workflow, and multilingual alert publishing, and closes with before/after KPI comparisons. The materials are polished enough for a non-technical audience and serve as the primary evidence for the Application Demo rubric criterion.

**Why this priority**: The rubric scored "Application Demo" at Good (4/5), citing the absence of a recorded demo video or executive-facing presentation artifact. A demo walkthrough directly addresses this.

**Independent Test**: Can be fully tested by having a non-technical reviewer watch the demo and confirm they can describe the hub's purpose, core workflow, and measurable impact without additional explanation.

**Acceptance Scenarios**:

1. **Given** the hub is seeded with a multi-jurisdiction bushfire scenario, **When** the demo walkthrough is recorded, **Then** it covers incident activation, signal ingestion, dashboard, persona workspace, recommendation approval, multilingual alert publishing, and scenario replay in under 5 minutes.
2. **Given** the demo walkthrough exists, **When** an executive stakeholder reviews it, **Then** the accompanying slide deck shows before/after KPI comparisons (SC-004 through SC-007 from the original feature) and a clear value proposition.
3. **Given** the demo materials exist, **When** reviewed for completeness, **Then** they include annotated screenshots or GIF recordings of every major UI surface.

---

### User Story 7 — Errors are handled robustly with actionable alerts (Priority: P7)

When an external dependency fails, a signal ingestion request is malformed, or an internal service error occurs, the system catches the error, returns a structured error response with correlation ID, and triggers an alert to the operations team. Failed messages are routed to a dead-letter store for later inspection. Transient failures against Cosmos DB and Redis are retried with exponential backoff before surfacing as errors.

**Why this priority**: The rubric scored "Error handling and alerting" at Good (4/5), noting missing alert action groups/notification targets, incomplete alerting rules, and no dead-letter or retry handling.

**Independent Test**: Can be fully tested by simulating a Cosmos DB transient failure and verifying the retry succeeds, then simulating a permanent failure and verifying the alert fires and the failed operation lands in the dead-letter store.

**Acceptance Scenarios**:

1. **Given** an API request encounters a transient storage or cache failure, **When** the retry policy executes, **Then** the system retries with exponential backoff (up to 3 attempts) and succeeds transparently if the dependency recovers.
2. **Given** a permanent dependency failure or unhandled exception occurs, **When** the error is caught, **Then** the API returns a structured JSON error response with the correlation ID, HTTP status code, and a non-leaking error description.
3. **Given** alert action groups are configured, **When** the high-error-rate or latency alert fires, **Then** notifications are delivered to the configured targets (e.g., email, webhook, or Teams channel).
4. **Given** a signal ingestion or event bus delivery fails permanently, **When** the failure is recorded, **Then** the failed payload is stored in a dead-letter store with the correlation ID, timestamp, and failure reason for later inspection.

---

### User Story 8 — Performance targets are validated under load (Priority: P8)

A platform engineer runs a load test suite that simulates 1,000 concurrent operators and 50,000 signals/hour burst ingestion against the API. The test results validate or refute the documented performance targets (<2s dashboard load, <500ms p95 reads, <60s hazard update visibility). Performance regression checks run in CI to catch degradation before merge.

**Why this priority**: The rubric scored "Performance and reliability" at Good (4/5), citing missing load test results and no performance regression testing in CI.

**Independent Test**: Can be fully tested by running the load test suite against a local or staging environment and verifying the results meet or fail documented thresholds.

**Acceptance Scenarios**:

1. **Given** the load test suite is configured, **When** it runs against the API with 1,000 simulated concurrent users, **Then** the dashboard endpoint responds in under 2 seconds at p95 and signal ingestion sustains 50,000 signals/hour without error rate exceeding 1%.
2. **Given** the load test suite produces results, **When** compared against documented targets, **Then** a pass/fail report is generated for each target (dashboard load, read latency, signal throughput).
3. **Given** a code change degrades API response time beyond the threshold, **When** the CI pipeline runs the lightweight performance benchmark, **Then** the pipeline flags the regression and blocks merge within the 10-minute CI time budget.

### Edge Cases

- The language model returns harmful, biased, or nonsensical content in a generated alert draft.
- The language model endpoint throttles requests during a high-signal-volume incident, causing agent backlogs.
- A CI pipeline stage hangs indefinitely due to an external dependency (e.g., npm registry timeout).
- A container build fails because a Python dependency has been yanked from PyPI between pipeline runs.
- An infrastructure deployment partially succeeds — some resources created, others failed — leaving the environment in an inconsistent state.
- Two agents attempt to process the same handoff concurrently due to duplicate event delivery.
- An alert action group notification target is unreachable (e.g., Teams webhook down), causing alert delivery to silently fail.
- A load test run produces inconsistent results due to shared test environment contention.
- The dead-letter store grows unbounded because no operator reviews or purges failed messages.
- The demo recording becomes stale after a UI change and no longer matches the live application.

## Requirements *(mandatory)*

### Functional Requirements

**AI Integration in Agents**

- **FR-001**: The Risk Assessment agent MUST use a language model to generate natural-language recommendation explanations from incident signal context, citing specific signal identifiers in the output.
- **FR-002**: The Communication agent MUST use a language model to draft public alert content in all 6 supported languages (en-AU, zh-Hans, ar, vi, el, it), adhering to plain-language accessibility guidelines.
- **FR-003**: Each agent that calls a language model MUST enforce a configurable token budget per request and handle budget exceedances gracefully (truncation or re-request).
- **FR-004**: Each agent that calls a language model MUST implement a fallback to deterministic template-based output when the model endpoint is unavailable, marking the output as template-generated.
- **FR-005**: All language model requests and responses MUST include the correlation ID from the resilience middleware and be logged with token usage, latency, and model deployment identifier.
- **FR-006**: Language model outputs used in public-facing alerts MUST pass a content safety validation step before being presented to the approver. If validation fails, the system MUST fall back to the deterministic template output (same fallback as FR-004), mark the output as "safety_fallback", and log the flagged content with correlation ID for post-hoc review.

**CI/CD Pipeline**

- **FR-007**: The CI pipeline MUST execute all Python tests (contract, integration, simulation) on every push and pull request.
- **FR-008**: The CI pipeline MUST run Python linting and TypeScript type-checking and fail the build on any violation.
- **FR-009**: The CI pipeline MUST build the web application and report build success or failure.
- **FR-010**: The CI pipeline MUST produce a clear, stage-by-stage summary visible on the pull request indicating which steps passed and which failed.

**Agent Orchestration Depth**

- **FR-011**: The Monitoring agent MUST automatically publish a typed handoff to the Risk Assessment agent when a signal is classified as high-risk, using the existing event bus and scoped to the incident tenant.
- **FR-012**: The Risk Assessment agent MUST automatically publish a typed handoff to the Communication agent when a recommendation of type public_alert with high confidence is produced.
- **FR-013**: Every agent-to-agent handoff MUST be recorded as a TimelineEvent in the audit trail, capturing source agent, target agent, scope key, confidence, and a payload summary.
- **FR-014**: Handoff delivery MUST respect circuit breaker state; if the target agent's circuit is open, the handoff MUST be retried up to 3 times over a 5-minute window with exponential backoff. If all retries fail, the handoff MUST be stored in the dead-letter store (FR-025) and marked as failed for operator review.

**Container Definitions**

- **FR-015**: The repository MUST include a Dockerfile for the API service that produces a container running the FastAPI application as a non-root user with no embedded secrets.
- **FR-016**: The repository MUST include a Dockerfile for the agent runtime that produces a container running the agent worker as a non-root user.
- **FR-017**: Both Dockerfiles MUST use multi-stage builds to minimise image size and leverage layer caching for dependency installation.

**Infrastructure as Code**

- **FR-018**: Infrastructure definitions MUST provision the container hosting environment, database, cache, blob storage, and AI model endpoint as code.
- **FR-019**: All provisioned resources MUST be located in Australian Azure regions, enforcing data residency.
- **FR-020**: Infrastructure definitions MUST configure managed identity for inter-service authentication and connect application resources to existing monitoring resources.

**Demo Artifacts**

- **FR-021**: The repository MUST include a recorded demo walkthrough (video or annotated screenplay) covering the full incident workflow: activation, signal ingestion, dashboard, persona workspace, recommendation approval, multilingual alert publishing, and scenario replay.
- **FR-022**: The repository MUST include an executive-facing slide deck with before/after KPI comparisons and annotated screenshots of every major UI surface.

**Error Handling and Alerting**

- **FR-023**: The API MUST return structured JSON error responses for all failure modes, including correlation ID, HTTP status code, error category, and a non-leaking message.
- **FR-024**: The API MUST implement retry policies with exponential backoff (up to 3 attempts) for transient failures against Cosmos DB and Redis.
- **FR-025**: Failed signal ingestion payloads and event bus deliveries MUST be stored in a dead-letter store with correlation ID, timestamp, and failure reason.
- **FR-026**: Alert rules MUST be configured with action groups that deliver notifications to at least one operational target (email, webhook, or messaging channel).
- **FR-027**: The Bicep latency alert rule MUST be completed and validated alongside the existing error-rate alert.

**Performance Validation**

- **FR-028**: The repository MUST include a load test suite that simulates concurrent operator load and burst signal ingestion against the API.
- **FR-029**: Load test results MUST produce a pass/fail report comparing measured values against documented performance targets (dashboard load <2s p95, read API <500ms p95, signal throughput 50,000/hour).
- **FR-030**: The CI pipeline MUST include a lightweight performance benchmark (<60 seconds, ~50 concurrent requests) that checks key endpoint p95 latency against configured thresholds and blocks merge on regression. The full load test suite (FR-028) MUST run on a nightly schedule or manual trigger against a staging environment.

### Key Entities

- **ModelDeployment**: Represents a language model endpoint configuration including deployment identifier, endpoint URL, token budget, content safety policy, and fallback mode.
- **AgentHandoffEvent**: An executed handoff between agents, extending the existing AgentHandoff with delivery status (delivered, queued, failed), retry count, and associated TimelineEvent ID.
- **PipelineStage**: A discrete step in the CI/CD pipeline (e.g., python-test, lint, web-build) with name, status (pass/fail/skip), duration, and error summary.
- **ContainerDefinition**: A Dockerfile specification for an application service, including base image, build stages, exposed port, health check command, and security constraints.
- **DeadLetterEntry**: A failed operation record stored for later inspection, including the original payload, correlation ID, failure reason, timestamp, and retry count.
- **AlertActionGroup**: A notification target configuration for operational alerts, including target type (email, webhook, messaging channel), recipient, and escalation priority.
- **LoadTestResult**: A performance test execution result including scenario name, concurrent users, duration, measured p95 latency, throughput, error rate, and pass/fail status per target.

### Assumptions

- The Azure OpenAI resource and model deployment will be provisioned in an Australian Azure region or a region with acceptable latency, subject to model availability.
- The existing event bus abstraction in `event_bus.py` can be extended to support subscriber registration and delivery confirmation without replacing the current in-memory implementation during this feature scope. A production event broker (Azure Service Bus or Event Hubs) is a follow-on concern.
- Content safety validation for language model outputs will use a rule-based approach initially (keyword filtering, length validation, language detection) rather than a separate AI content safety service.
- The CI pipeline runs on GitHub Actions using the existing `ci.yml` workflow file, extended with additional steps.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Risk Assessment agent produces LLM-generated recommendation explanations that cite at least one signal ID in 95% of invocations when the model endpoint is available.
- **SC-002**: The Communication agent produces multilingual alert drafts in all 6 supported languages (en-AU, zh-Hans, ar, vi, el, it) for every public_alert recommendation, within a 30-second total latency budget per complete draft set.
- **SC-003**: Agent model-call failures result in a template-based fallback output within 2 seconds, with zero lost recommendations or alert drafts.
- **SC-004**: The CI pipeline executes all test suites and quality checks on every PR, completing in under 10 minutes, and blocks merge on any failure.
- **SC-005**: A high-risk signal triggers the full Monitoring → Risk Assessment → Communication handoff chain automatically within 30 seconds, with each handoff recorded as a timeline event.
- **SC-006**: Both container images build successfully from source, pass health checks, and run as non-root users.
- **SC-007**: Infrastructure definitions pass a what-if validation deploying all application resources to an Australian Azure region with managed identity and monitoring integration.
- **SC-008**: A recorded demo walkthrough and executive slide deck exist in the repository, covering the full incident workflow with before/after KPI comparisons.
- **SC-009**: All API error responses include correlation ID and structured JSON body; no stack traces or internal details leak to clients.
- **SC-010**: Transient storage/cache failures are retried up to 3 times with exponential backoff, with transparent recovery in 90%+ of transient failure scenarios.
- **SC-011**: Alert rules fire notifications to configured action group targets within 5 minutes of threshold breach.
- **SC-012**: The full load test validates dashboard p95 <2s, read API p95 <500ms, and signal ingestion sustains 50,000/hour with <1% error rate on nightly/manual runs. The CI lightweight benchmark completes in <60 seconds and catches p95 regressions on every PR.
- **SC-013**: The overall AMA rubric score improves from 55/60 to 60/60, with every criterion scored at Excellent (5/5).

## Assumptions

Scoped to this spec's domain (AMA rubric uplift programme). Tagging follows `specs/027-spec-hardening` taxonomy: `[RISK]` (open externally-driven risk), `[DECISION]` (deliberate scoping decision), bare bullet (operating assumption).

- **ASM-001**: The AU-v1 deployment context defined in `specs/001-disaster-response-hub/spec.md` is the operational baseline for this spec; capstone-country variants (PH / JP / BD) are deferred. `linked_gaps:` `specs/shared/gap-id-register.md` A-GAP-001..003. `status:` Open.
- **ASM-002** [DECISION]: This spec's deliverables (AMA rubric uplift programme) integrate with the actor catalogue (`specs/004-actor-github-agents/spec.md`); responsible technical agents - product-owner-ba, qa-test-engineer - are consulted via the `agent` tool during authoring and review.
- **ASM-003**: Speckit conventions (FR/SC numbering, ASM/HYP/PER/SCP families) and the persona-profile YAML schema (`specs/027-spec-hardening/contracts/persona-profile.md`) are authoritative; this spec defers to those rather than redefining them.

## Personas

Authored against the `specs/027-spec-hardening/contracts/persona-profile.md` schema. AU-v1 personas are validated; PH / JP / BD entries are explicit placeholders pending capstone-reinterpretation (D-009) and SME validation per FR-023.

- **PER-001**: cross-ref to `specs/001-disaster-response-hub/spec.md` AIIMS personas (Incident Commander / Planning Officer / Operations Officer / Logistics Officer / Public Information Officer) per `specs/027-spec-hardening/contracts/persona-profile.md`. `status:` validated. `preconditions:` none.
- **PER-002**: cross-ref to `specs/004-actor-github-agents/spec.md` actor catalogue covering all `.github/agents/technical/*.agent.md` actors. `status:` validated. `preconditions:` none.
- **PER-003** [non-AU placeholder]: capstone-country operator personas for PH (NDRRMC), JP (Cabinet Office DRR / FDMA), BD (DDM / CPP volunteers). `status:` placeholder. `preconditions:` capstone-reinterpretation decision per D-009; SME validation via `ama-rubric-grader`-vetted SME interviews.

## Hypotheses

Hypotheses use the FR-018 statement format (`If <condition> then <observable>`) and link to a structured evidence stub conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. Capstone-country hypotheses for this spec's agent ownership (where applicable) are allocated in feature 028 / US2.

- **HYP-001**: If the actors named in `specs/004-actor-github-agents/spec.md` consult on every change to this spec via the `agent` tool, then the AMA rubric criterion mean (Assumptions / Requirements / Personas / Hypotheses / Scope) for this spec rises by at least +1 band relative to the baseline captured in `specs/028-capstone-alignment/evidence/rubric-baseline.md`. **Falsification**: post-feature rubric snapshot shows a regression in any of those five criteria for this spec. **Evidence stub**: `specs/028-capstone-alignment/evidence/HYP-HYP-001.md` (created in feature 028 polish).

## Out of Scope

- This spec is delivery-hygiene / enabling infrastructure; capstone-outcome-critical-path ownership lives in specs all capstone-critical-path specs (001, 005, 006, 008, 009, 010, 011, 012, 014, 015, 018, 019, 020, 021, 022, 023).

Items explicitly deferred from this spec; promotion to in-scope requires the named preconditions to clear. Cross-references to other specs use the canonical overlap phrasing (`authoritative for: <capability>` / `defers-to: <NNN> (<capability>)`).

- **SCP-001** [DEFERRED]: Capstone-country variants (PH typhoon, JP earthquake, BD flood) of this spec's capabilities are out of scope until: (i) capstone-reinterpretation decision per D-009; (ii) per-country regulatory + data-sharing preconditions documented in `specs/005-data-source-governance/spec.md` clear; (iii) responsible technical agents (product-owner-ba, qa-test-engineer) sign off on country-specific calibration.
- **SCP-002**: Constitutional-level changes (NON-NEGOTIABLE #1..#5) are not modified by this spec; any tension is documented as `[RISK]` in Assumptions, never resolved here.
- **SCP-003**: Cross-spec authority disputes are arbitrated via `product-owner-ba` and the speckit governance flow; this spec does not unilaterally claim ownership of capabilities owned elsewhere. `defers-to:` 018 (recovery-phase indicators, triggers, phase-exit criteria); 008 (warning-tier authoring, multilingual delivery, misinformation defence) where applicable.
- **SCP-004** [META]: This spec is delivery-hygiene / enabling infrastructure; capstone-outcome-critical-path ownership lives in specs (canonical list — see the verbatim bullet inserted by feature 028 / US4 elsewhere in this section). (See `specs/028-capstone-alignment/contracts/meta-spec-flag.contract.md`; the verbatim canonical bullet is added in US4.)


