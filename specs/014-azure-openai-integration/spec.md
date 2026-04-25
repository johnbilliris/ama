# Feature Specification: Azure OpenAI Integration Configuration

**Feature Branch**: `014-azure-openai-integration`  
**Created**: 2026-04-16  
**Status**: Draft  
**Input**: User description: "Configure and integrate Azure OpenAI service into the disaster response agents, providing live LLM capabilities with proper deployment configuration, managed identity authentication, model selection per agent use case, and verified fallback to template-based outputs."

## Clarifications

The following clarifications were resolved using stakeholder feedback, existing codebase patterns, and the project constitution:

1. **Authentication method**: The existing `LLMClient` currently uses an API key via `AZURE_OPENAI_API_KEY`. This specification mandates migration to managed identity authentication (zero-trust). The API key path will be removed. This aligns with Constitution IV (Privacy, Security, and Regional Policy Compliance).

2. **Model deployment mapping**: The existing client distinguishes between `reasoning` and `drafting` deployment purposes. This specification formalises the mapping — GPT-4o for reasoning-intensive agents (Risk Assessment, Evacuation) and GPT-4o-mini for classification/summarisation agents (Monitoring, Communication, Resource Allocation) — based on AI/ML Engineer feedback.

3. **Region selection**: Constitution VI mandates Australia-only deployment. Australia East is the primary region for Azure OpenAI capacity. If Azure OpenAI is unavailable in Australia East at provisioning time, Australia Southeast is the failover region. No cross-region inference calls are permitted — per Azure Principal Architect feedback.

4. **Fallback behaviour**: The existing `LLMCallMixin._generate_with_fallback()` pattern is confirmed as the canonical fallback mechanism. When the model is unavailable, agents fall back to template-based outputs. This specification ensures that pattern is verified end-to-end with a real deployment.

5. **Content safety**: The existing `ContentSafetyValidator` is a keyword-based placeholder. This specification does not replace it with Azure AI Content Safety (that is a separate feature). It ensures all LLM outputs pass through the existing validator before reaching users.

### Session 2026-04-12

- Q: What are the default per-call max output token limits for each model tier? → A: 4000 tokens/request for GPT-4o (reasoning), 2000 tokens/request for GPT-4o-mini (drafting), configurable via environment variables.
- Q: What is the default confidence threshold below which safety-critical outputs require human review? → A: 0.7 — outputs below this threshold trigger IC review for safety-critical decisions.
- Q: What model temperature settings should each tier use to balance determinism vs. creativity? → A: 0.0 for safety-critical agents (Risk Assessment, Evacuation), 0.3 for drafting agents (Communication, Monitoring, Resource Allocation).
- Q: What is the canonical deployment naming pattern for model deployments? → A: `gpt-4o-{env}` and `gpt-4o-mini-{env}` (e.g., `gpt-4o-dev`, `gpt-4o-prod`).
- Q: Should configurable monthly cost budget thresholds be specified per agent for tracking purposes? → A: Yes — default $50/agent/month for dev, $500/agent/month for prod. Tracking and alerting only; automated enforcement remains out of scope.

### Session 2026-04-12 (Pass 2)

- Q: What are the default TPM (tokens-per-minute) quotas per model deployment per environment? → A: Dev: 30K TPM for GPT-4o, 60K TPM for GPT-4o-mini. Prod: 120K TPM for GPT-4o, 240K TPM for GPT-4o-mini. Azure OpenAI standard tier defaults for Australia East.
- Verification: Model routing (reasoning/drafting tier) ↔ temperature settings (0.0/0.3) — confirmed consistent across FR-020, Key Entities, and clarification session 1.
- Verification: Retry strategy (3 retries, exponential backoff 1s→2s→4s) — confirmed consistent across US3, FR-008, and edge cases.
- Verification: Confidence threshold default of 0.7 — confirmed consistent across clarification session 1, US6, and Key Entities.
- Verification: Content safety validation required on ALL LLM outputs — confirmed explicitly stated in FR-006, SC-005, and US4.
- Verification: Token budget defaults (4000/2000 tokens) — confirmed within GPT-4o and GPT-4o-mini output token limits (16,384 max).
- Fix: Added explicit three-tier degradation chain edge case (AU East → AU Southeast → template fallback).
- Fix: Strengthened Bicep module dependency references to cite specific existing patterns.
- Fix: Made risk register entry format explicit with structured fields.
- Fix: Added FR-022 specifying TPM quota defaults per environment.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Azure OpenAI Resource Provisioned and Accessible by Agents (Priority: P1)

A platform operator deploys the disaster response hub to Azure. As part of the deployment, the infrastructure-as-code provisions an Azure OpenAI resource in Australia East with the required model deployments. Once deployed, each agent's configuration resolves the correct endpoint and model deployment for its use case. The operator verifies that agents can authenticate to the Azure OpenAI resource using managed identity without any API keys in configuration or environment variables.

**Why this priority**: Without a working Azure OpenAI resource with correct authentication and model deployments, no agent can perform live LLM inference. This is the foundational prerequisite for all other stories.

**Independent Test**: Can be fully tested by deploying the infrastructure module, then running a health check from each agent that verifies: (a) the endpoint is reachable, (b) managed identity authentication succeeds, and (c) the configured deployment name resolves to a valid model.

**Acceptance Scenarios**:

1. **Given** the infrastructure-as-code is deployed to an Azure subscription, **When** the Azure OpenAI module completes provisioning, **Then** an Azure OpenAI resource exists in Australia East with model deployments for both the reasoning tier (GPT-4o) and the drafting tier (GPT-4o-mini).
2. **Given** an agent process starts with the Azure OpenAI endpoint configured, **When** the agent initialises its LLM client, **Then** it authenticates using managed identity (no API key environment variable is required or used).
3. **Given** the Azure OpenAI resource is deployed, **When** any agent sends a health-check prompt, **Then** it receives a valid response confirming the deployment is operational, and the response metadata includes the deployment name and region.
4. **Given** the infrastructure-as-code is deployed with a region parameter set to a non-Australian region, **When** validation runs, **Then** the deployment fails with a clear error indicating that only Australian regions are permitted.

---

### User Story 2 — Model Selection Routes Agents to Appropriate Deployments (Priority: P1)

An emergency operations coordinator triggers the system during a bushfire emergency. The Risk Assessment Agent generates a detailed hazard impact prediction using the reasoning-tier model (GPT-4o), producing nuanced analysis with confidence scoring. Simultaneously, the Monitoring Agent classifies incoming signals using the drafting-tier model (GPT-4o-mini), which is optimised for fast classification tasks. Each agent's configuration file specifies which deployment it uses, and the LLM client routes requests accordingly.

**Why this priority**: Correct model routing is essential for both cost efficiency and output quality. Assigning a high-capability model to classification tasks wastes budget; assigning a lightweight model to complex reasoning produces inadequate outputs for life-safety decisions.

**Independent Test**: Can be tested by invoking the LLM client from each agent's context with its configured purpose and verifying that the request is routed to the expected deployment name.

**Acceptance Scenarios**:

1. **Given** the Risk Assessment Agent is configured with purpose `reasoning`, **When** it generates a hazard prediction via the LLM client, **Then** the request is routed to the GPT-4o deployment and the response metadata confirms the deployment name.
2. **Given** the Monitoring Agent is configured with purpose `drafting`, **When** it classifies an incoming signal via the LLM client, **Then** the request is routed to the GPT-4o-mini deployment and the response metadata confirms the deployment name.
3. **Given** an agent's configuration specifies a deployment name that does not exist in the Azure OpenAI resource, **When** the agent attempts an LLM call, **Then** the call fails with a descriptive error and the agent falls back to template-based output.

---

### User Story 3 — Template Fallback When Azure OpenAI Is Unavailable (Priority: P1)

During a disaster event, the Azure OpenAI service experiences a transient outage. The Monitoring Agent attempts to generate a signal classification summary via the LLM but receives repeated failures. After exhausting retries (3 attempts with exponential backoff), the agent falls back to its pre-defined template-based output, producing a structured but less nuanced classification. The system logs the fallback event, and the output is clearly marked with `generation_method: template_fallback` so that downstream agents and human operators know the output was not LLM-generated.

**Why this priority**: The Constitution (Principle I) mandates safe degradation — agents must continue functioning when AI capabilities are unavailable. During a disaster is precisely when outages are most likely and when continued operation is most critical.

**Independent Test**: Can be tested by configuring the LLM client with an unreachable endpoint, triggering a generation request, and verifying that the agent produces template-based output with the correct `generation_method` marker within the timeout window.

**Acceptance Scenarios**:

1. **Given** the Azure OpenAI endpoint is unreachable, **When** an agent invokes `_generate_with_fallback()`, **Then** the method returns within the configured timeout, the output text matches the provided template text, and `generation_method` is `template_fallback`.
2. **Given** the Azure OpenAI endpoint returns HTTP 503 errors, **When** the LLM client retries the request, **Then** it retries up to 3 times with exponential backoff (1s, 2s, 4s maximum) before raising the exception to the fallback handler.
3. **Given** the Azure OpenAI endpoint returns HTTP 429 (rate limit), **When** the LLM client retries, **Then** it follows the same retry pattern and, if all retries fail, the agent falls back to template output.
4. **Given** an agent falls back to template output, **When** the fallback event is recorded, **Then** the audit trail includes the error reason, timestamp, correlation ID, and the number of retry attempts made.

---

### User Story 4 — Content Safety Validation on All LLM Outputs (Priority: P2)

A Communication Agent generates an emergency alert message using the LLM. Before the message reaches any delivery channel, the content safety validator checks it for blocked content, length violations, and language appropriateness. If the output fails validation, the agent substitutes the pre-approved template text and marks the output as `safety_fallback`. The incident commander can see in the audit trail that content safety intervened and why.

**Why this priority**: The Constitution (Principle I) treats public alerts as safety-critical outputs. LLM outputs are non-deterministic and must be validated before reaching the public. Content safety is a mandatory gate, not an optional enhancement.

**Independent Test**: Can be tested by providing the content safety validator with outputs containing blocked keywords, excessive length, and language mismatches, then verifying that each case produces the correct rejection reason and that the agent substitutes template text.

**Acceptance Scenarios**:

1. **Given** an LLM output contains a blocked keyword, **When** the content safety validator runs, **Then** it returns `passed: false` with reason `blocked_keyword` and the agent uses template text with `generation_method: safety_fallback`.
2. **Given** an LLM output exceeds the maximum length threshold, **When** the content safety validator runs, **Then** it returns `passed: false` with reason `length_exceeded`.
3. **Given** an LLM output is empty, **When** the content safety validator runs, **Then** it returns `passed: false` with reason `empty_output`.
4. **Given** an LLM output passes all content safety checks, **When** the validator completes, **Then** it returns `passed: true` with result `passed` and the original LLM text is used.

---

### User Story 5 — Token Budget Management and Cost Tracking (Priority: P2)

A platform operator monitors the cost of running the disaster response hub. Each agent tracks token consumption per LLM call (input tokens, output tokens) and reports usage through the existing telemetry pipeline. The operator can view per-agent token usage to identify cost anomalies and ensure the system stays within the allocated budget. If an individual call's output token count exceeds the configured maximum, the response is trimmed before delivery.

**Why this priority**: Uncontrolled LLM token usage can lead to unexpected costs, especially during sustained disaster events when call volume is high. Token budgets prevent runaway costs and ensure fair resource distribution across agents.

**Independent Test**: Can be tested by making LLM calls with known prompts, capturing the token usage metadata from responses, and verifying that telemetry records include per-call token counts and that responses exceeding the max output tokens are trimmed.

**Acceptance Scenarios**:

1. **Given** an agent makes an LLM call, **When** the response is returned, **Then** the response metadata includes `token_usage` with `input_tokens` and `output_tokens` as non-negative integers.
2. **Given** an LLM response uses more output tokens than the configured `max_output_tokens`, **When** the mixin processes the response, **Then** the text is trimmed and a warning is logged with the actual and maximum token counts.
3. **Given** multiple agents are running concurrently, **When** token usage is reported via telemetry, **Then** each metric is tagged with the agent name and deployment ID, enabling per-agent cost breakdown.

---

### User Story 6 — Confidence Thresholds and Human Review Gates (Priority: P2)

An incident commander is overseeing a cyclone response. The Risk Assessment Agent generates an evacuation recommendation with a confidence score of 0.55, which is below the escalation threshold of 0.7. Because this output influences a life-safety decision (evacuation), the system flags it for human review rather than automatically escalating to the Evacuation Agent. The incident commander reviews the recommendation, the supporting data, and the confidence rationale before deciding whether to approve or reject the escalation.

**Why this priority**: The Constitution (Principle I) mandates human override for safety-critical outputs, and the Risk Manager requires confidence thresholds to prevent low-confidence AI outputs from driving protective actions without human verification.

**Independent Test**: Can be tested by generating a recommendation with a confidence score below the configured threshold and verifying that no automatic escalation occurs and that the recommendation is marked for human review.

**Acceptance Scenarios**:

1. **Given** an agent generates a safety-critical output with a confidence score below the configured threshold, **When** the output is evaluated for escalation, **Then** no automatic handoff is created and the output is marked `requires_human_review: true`.
2. **Given** an agent generates a safety-critical output with a confidence score at or above the configured threshold, **When** the output is evaluated for escalation, **Then** the automatic handoff proceeds as normal.
3. **Given** an output is marked for human review, **When** the incident commander inspects the output, **Then** the review interface shows the confidence score, the contributing data sources, and the reasoning summary.
4. **Given** the LLM was unavailable and the agent fell back to template output, **When** the confidence score is computed, **Then** it is automatically reduced by the configured fallback reduction factor and the output is flagged for human review.

---

### User Story 7 — Azure OpenAI Infrastructure as Code (Priority: P3)

A DevOps engineer adds a new model deployment or changes the token-per-minute quota for an existing deployment. They update the infrastructure-as-code module parameters and run the deployment pipeline. The module provisions or updates the Azure OpenAI resource, model deployments, managed identity role assignments, and diagnostic settings without manual portal intervention. All changes are version-controlled and auditable.

**Why this priority**: Infrastructure-as-code ensures repeatable, auditable deployments and prevents configuration drift. While the resource must exist for P1, the IaC module's extensibility for future changes is a lower-priority concern.

**Independent Test**: Can be tested by deploying the Bicep module to a test subscription and verifying that the Azure OpenAI resource, model deployments, role assignments, and diagnostic settings match the parameter values.

**Acceptance Scenarios**:

1. **Given** the Bicep module is deployed with default parameters for the dev environment, **When** the deployment completes, **Then** the Azure OpenAI resource exists in the specified Australian region with the reasoning-tier deployment (GPT-4o) at 30K TPM and the drafting-tier deployment (GPT-4o-mini) at 60K TPM.
2. **Given** the Bicep module includes a managed identity parameter, **When** the deployment completes, **Then** the specified identity has the Cognitive Services OpenAI User role on the Azure OpenAI resource.
3. **Given** the Bicep module includes diagnostic settings, **When** the deployment completes, **Then** Azure OpenAI diagnostic logs and metrics are routed to the existing Log Analytics workspace.
4. **Given** an operator changes the token-per-minute quota parameter and redeploys, **When** the deployment completes, **Then** the model deployment reflects the updated quota without recreating the resource.

---

### User Story 8 — Model Performance Monitoring and Token Usage Metrics (Priority: P3)

A platform operator reviews the operational dashboard after a 48-hour flood response. They can see per-agent LLM call counts, average latency, token consumption trends, error rates, and fallback frequency. These metrics flow through the existing telemetry pipeline and are available in the monitoring workspace for alerting and analysis.

**Why this priority**: Operational visibility is essential for long-term reliability but is not required for initial integration. The existing telemetry infrastructure provides the foundation; this story extends it with LLM-specific metrics.

**Independent Test**: Can be tested by making a series of LLM calls, then querying the telemetry backend for the expected metrics and verifying that counters, histograms, and labels are correctly recorded.

**Acceptance Scenarios**:

1. **Given** agents are making LLM calls, **When** telemetry is collected, **Then** the following metrics are available: LLM call count (by agent, deployment, outcome), latency histogram, input/output token counters, fallback count (by type: template, safety), and error count (by error category).
2. **Given** an LLM call succeeds, **When** the telemetry event is recorded, **Then** it includes the correlation ID, deployment ID, latency in milliseconds, and token usage.
3. **Given** an LLM call triggers a fallback, **When** the telemetry event is recorded, **Then** it includes the fallback type (template or safety) and the error reason if applicable.

---

### Edge Cases

- What happens when the Azure OpenAI endpoint is reachable but the specific model deployment is deleted or renamed? The LLM client must handle deployment-not-found errors the same as unreachable endpoint errors — retry, then fall back to template output.
- What happens when managed identity token acquisition fails (e.g., identity not assigned, role not granted)? The LLM client must fail fast with a descriptive error during initialisation rather than failing on the first LLM call.
- What happens when the LLM returns a valid response that is semantically inappropriate (e.g., a hazard prediction that contradicts sensor data)? Content safety catches blocked content and format issues; semantic validation is the responsibility of the consuming agent's domain logic, not the LLM integration layer.
- What happens when token usage reporting from the Azure OpenAI API is unavailable or returns zeros? The system must log a warning and proceed; token tracking is best-effort and must not block agent operation.
- What happens when two agents make concurrent calls and one triggers rate limiting (HTTP 429)? Each agent's LLM client retries independently; rate limiting on one agent must not block or crash other agents.
- What happens when the Azure OpenAI resource is provisioned in Australia East but that region experiences an outage? The IaC module supports a failover region parameter (Australia Southeast). Redeployment to the failover region is a manual operator action, not automatic — per the Azure Principal Architect's guidance that automatic cross-region failover risks violating data residency during partial outages.
- What is the complete degradation chain when Azure OpenAI capacity is unavailable? Three tiers: (1) Primary region (Australia East) serves all LLM requests under normal operation. (2) If Australia East is unavailable at provisioning time or experiences a sustained outage, an operator manually redeploys the IaC module targeting Australia Southeast. (3) If the LLM endpoint is unreachable at runtime (regardless of region), each agent falls back to template-based output after exhausting retries (3 attempts, exponential backoff). Tiers 1→2 require operator intervention; tier 2→3 is automatic per-agent.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provision an Azure OpenAI resource exclusively within Australian Azure regions (Australia East primary, Australia Southeast failover) as mandated by Constitution VI.
- **FR-002**: The system MUST deploy two model tiers: a reasoning-tier deployment (GPT-4o) for complex analysis tasks and a drafting-tier deployment (GPT-4o-mini) for classification and summarisation tasks.
- **FR-003**: Each agent's configuration MUST specify which model tier (reasoning or drafting) it uses, and the LLM client MUST route requests to the corresponding deployment.
- **FR-004**: The system MUST authenticate to Azure OpenAI using managed identity. API key authentication MUST NOT be used in any environment (Constitution IV — zero trust).
- **FR-005**: The LLM client MUST validate that the configured Azure OpenAI endpoint resolves to an Australian Azure region at initialisation time.
- **FR-006**: All LLM outputs MUST pass through the content safety validator before being used by any agent or delivered to any user.
- **FR-007**: When the LLM is unavailable or content safety validation fails, the system MUST fall back to template-based outputs and mark the response with the appropriate `generation_method` (`template_fallback` or `safety_fallback`).
- **FR-008**: The LLM client MUST retry transient failures (HTTP 429, 503) with exponential backoff (3 attempts, 1–4 second delays) before triggering fallback.
- **FR-009**: Each LLM call response MUST include token usage metadata (input tokens, output tokens) and the metadata MUST be emitted via the existing telemetry pipeline.
- **FR-010**: The system MUST enforce per-call output token limits (default: 4000 tokens for reasoning-tier GPT-4o, 2000 tokens for drafting-tier GPT-4o-mini, configurable via environment variables) and trim responses that exceed the configured maximum.
- **FR-011**: For safety-critical outputs (evacuation recommendations, public alerts), the system MUST apply confidence thresholds — outputs below the configured threshold MUST be flagged for human review and MUST NOT automatically escalate to downstream agents.
- **FR-012**: When an agent uses template fallback, the confidence score for that output MUST be automatically reduced by the configured fallback reduction factor.
- **FR-013**: The system MUST provide an infrastructure-as-code module that provisions the Azure OpenAI resource, model deployments, managed identity role assignments, and diagnostic settings.
- **FR-014**: The infrastructure-as-code module MUST reject deployment to non-Australian Azure regions with a clear validation error.
- **FR-015**: All LLM calls MUST include a correlation ID that links the request to the originating agent pipeline execution for end-to-end traceability.
- **FR-016**: LLM-specific telemetry metrics MUST include: call count, latency, token usage, fallback frequency, and error rate — all labelled by agent name and deployment ID.
- **FR-017**: The system MUST NOT make cross-region inference calls — all LLM requests MUST be served by the Azure OpenAI resource in the configured Australian region.
- **FR-018**: Structured LLM outputs MUST be validated against the agent's existing data models before use, and validation failures MUST trigger template fallback.
- **FR-019**: A risk register entry MUST be created documenting AI model reliability risks during disasters. The entry MUST use a structured format with: Risk ID, Risk Title, Probability (Low/Medium/High with percentage range), Impact (Low/Medium/High/Critical with operational consequence), Mitigation Strategy (specific actions — e.g., template fallback, manual redeployment), Residual Risk (rating after mitigation), Owner (role responsible), and Review Cadence (frequency of reassessment). At minimum, the entry MUST cover: model unavailability during peak disaster load, token quota exhaustion under sustained usage, and managed identity credential propagation delays.
- **FR-020**: The LLM client MUST set model temperature to 0.0 for safety-critical agents (Risk Assessment, Evacuation) and 0.3 for drafting agents (Communication, Monitoring, Resource Allocation) by default, configurable via each agent's frozen dataclass configuration.
- **FR-021**: Each agent MUST have a configurable monthly token budget threshold (default: $50/agent/month for dev, $500/agent/month for prod). Token usage MUST be tracked against this threshold via telemetry; breaching the threshold MUST emit a warning metric. Automated enforcement (request blocking) remains out of scope.
- **FR-022**: The infrastructure-as-code module MUST configure TPM (tokens-per-minute) quotas per model deployment with environment-aware defaults: Dev — 30K TPM for GPT-4o reasoning-tier, 60K TPM for GPT-4o-mini drafting-tier; Prod — 120K TPM for GPT-4o, 240K TPM for GPT-4o-mini. These quotas MUST be exposed as Bicep parameters to allow operator override without module modification.

### Key Entities

- **Azure OpenAI Resource**: The cloud resource hosting model deployments, scoped to a single Australian region, with managed identity access control and diagnostic logging enabled.
- **Model Deployment**: A named deployment of a specific model version within the Azure OpenAI resource. Each deployment has a model tier (reasoning or drafting), a token-per-minute (TPM) quota, and maps to specific agent use cases. Default TPM quotas: Dev — 30K TPM for GPT-4o, 60K TPM for GPT-4o-mini; Prod — 120K TPM for GPT-4o, 240K TPM for GPT-4o-mini (Azure OpenAI standard tier for Australia East).
- **LLM Client Configuration**: The set of parameters (endpoint, deployment names, timeout, max tokens, temperature) that an agent uses to connect to Azure OpenAI, read from environment variables at startup. Default temperature: 0.0 for reasoning tier, 0.3 for drafting tier.
- **Token Budget**: The per-call maximum output token limit (default: 4000 tokens for GPT-4o, 2000 for GPT-4o-mini) and the per-agent tracking of cumulative token usage over time for cost monitoring. Monthly cost thresholds default to $50/agent for dev, $500/agent for prod.
- **Confidence Threshold**: A configurable numeric boundary per agent (default: 0.7) that determines whether a safety-critical LLM output requires human review before escalation. Outputs scoring below 0.7 are flagged `requires_human_review: true`.
- **Fallback Reduction Factor**: A multiplier applied to confidence scores when template fallback is used, reflecting reduced output quality compared to LLM-generated analysis.
- **Risk Register Entry**: A documented risk assessment for AI model reliability during disaster operations. Structured format: Risk ID (e.g., `RISK-AOAI-001`), Risk Title, Probability (Low <20% / Medium 20–50% / High >50%), Impact (Low / Medium / High / Critical — with operational consequence description), Mitigation Strategy (actionable steps), Residual Risk (rating after mitigation), Owner (accountable role), Review Cadence (e.g., quarterly or post-incident). Must cover at minimum: model unavailability during peak load, token quota exhaustion, and credential propagation delays.

## Assumptions

- Azure OpenAI GPT-4o and GPT-4o-mini models are available in the Australia East Azure region at the time of deployment. If not, Australia Southeast is used as the fallback provisioning region.
- The existing `LLMCallMixin._generate_with_fallback()` pattern in `apps/agents/common/llm_mixin.py` is the canonical integration point — this specification extends it with managed identity support, not replaces it.
- All agents already have template-based output implementations that produce acceptable (if less nuanced) results when the LLM is unavailable.
- The existing `ContentSafetyValidator` in `apps/agents/common/content_safety.py` is sufficient for the initial integration. Migration to Azure AI Content Safety is a separate, future feature.
- Managed identity infrastructure (user-assigned or system-assigned) is provisioned as part of each agent's existing container deployment module; this specification adds the role assignment to the Azure OpenAI resource.
- The existing telemetry pipeline (OpenTelemetry with optional no-op fallback) is operational and can accept additional metrics without architectural changes.
- Token-per-minute (TPM) quotas are configured per model deployment in the IaC module. Default quotas: Dev — 30K TPM (GPT-4o), 60K TPM (GPT-4o-mini); Prod — 120K TPM (GPT-4o), 240K TPM (GPT-4o-mini). These are Azure OpenAI standard tier defaults for Australia East, configurable via Bicep parameters.
- The model deployment naming convention uses hyphenated model names with environment suffix: `gpt-4o-{env}` and `gpt-4o-mini-{env}` (e.g., `gpt-4o-dev`, `gpt-4o-prod`).

## Dependencies

- **Constitution VI**: Mandates Azure-only deployment in Australian regions — this specification implements that requirement for the Azure OpenAI resource.
- **Constitution IV**: Mandates privacy, security, and zero-trust — this specification implements managed identity authentication.
- **Constitution I**: Mandates safe degradation and human override — this specification implements template fallback and confidence thresholds with human review gates.
- **Existing LLM integration layer**: `apps/agents/common/llm_client.py`, `llm_mixin.py`, and `content_safety.py` provide the integration foundation.
- **Existing agent configuration pattern**: `apps/agents/*/config.py` frozen dataclass pattern for environment-variable-driven configuration.
- **Existing telemetry infrastructure**: `apps/agents/*/telemetry.py` OpenTelemetry pattern with no-op fallbacks.
- **Existing infrastructure modules**: `infra/modules/*.bicep` pattern for parameterised Azure resource provisioning. The new Azure OpenAI module MUST follow the existing conventions: `param location string`, `param envPrefix string`, `param tags object` as standard parameters; `Microsoft.Authorization/roleAssignments@2022-04-01` for RBAC (see `communication-agent.bicep` line ~266 for existing `cognitiveServicesOpenAiRole` pattern); diagnostic settings routed to the shared Log Analytics workspace (see `monitoring.bicep`).
- **Managed identity provisioning**: Depends on agent container deployment modules having managed identity configured.

## Out of Scope

- **Changing agent decision logic**: This specification configures the LLM integration layer; it does not modify how agents interpret or act on LLM outputs beyond the existing patterns.
- **Azure AI Content Safety migration**: Replacing the keyword-based `ContentSafetyValidator` with the Azure AI Content Safety service is a separate feature.
- **Fine-tuning or custom model training**: This specification uses standard Azure OpenAI model deployments; custom models are out of scope.
- **Automatic cross-region failover**: Failover to Australia Southeast is a manual operator action via IaC redeployment, not an automatic runtime behaviour.
- **Multi-model orchestration**: Agents use a single model deployment per purpose; orchestrating multiple models within a single agent pipeline is out of scope.
- **Prompt engineering for individual agents**: The prompts each agent sends to the LLM are defined by the agents themselves; this specification provides the transport and configuration layer.
- **Input-side prompt injection protection**: Sanitising agent prompts constructed from untrusted inputs (e.g., social media signals) is the responsibility of each agent's input processing pipeline, not the LLM transport layer configured here. Constitution IV is satisfied at the agent boundary, not the client layer.
- **Real-time cost alerting**: Token usage is tracked via telemetry for operational monitoring; automated budget enforcement with spending caps is out of scope.
- **New agent capabilities**: No new AI-powered features are introduced; existing LLM integration points are connected to a live deployment.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All five disaster response agents can make live LLM calls to Azure OpenAI and receive valid responses within 10 seconds under normal operating conditions.
- **SC-002**: No API keys appear in any configuration file, environment variable definition, or deployment artefact — 100% managed identity authentication.
- **SC-003**: When the Azure OpenAI endpoint is unreachable, every agent produces template-based output within 15 seconds (inclusive of retry delays) with zero unhandled exceptions.
- **SC-004**: Reasoning-tier agents (Risk Assessment, Evacuation) route to GPT-4o; drafting-tier agents (Monitoring, Communication, Resource Allocation) route to GPT-4o-mini — verified by deployment ID in response metadata.
- **SC-005**: All LLM outputs pass through content safety validation — zero LLM-generated text reaches users or downstream agents without validation.
- **SC-006**: Per-agent token usage metrics are available in the telemetry pipeline within 60 seconds of an LLM call, enabling operational cost tracking.
- **SC-007**: Safety-critical outputs with confidence below the configured threshold are blocked from automatic escalation 100% of the time.
- **SC-008**: The infrastructure-as-code module successfully provisions the Azure OpenAI resource, model deployments, and role assignments in a single deployment with no manual portal steps.
- **SC-009**: The Azure OpenAI resource is deployed exclusively in an Australian Azure region — verified by resource metadata and endpoint URL validation.
- **SC-010**: A documented risk register entry for AI model reliability exists, is reviewed by the Risk Manager, and includes mitigation strategies with residual risk ratings.


## Personas

Authored against the `specs/027-spec-hardening/contracts/persona-profile.md` schema. AU-v1 personas are validated; PH / JP / BD entries are explicit placeholders pending capstone-reinterpretation (D-009) and SME validation per FR-023.

- **PER-034**: cross-ref to `specs/001-disaster-response-hub/spec.md` AIIMS personas (Incident Commander / Planning Officer / Operations Officer / Logistics Officer / Public Information Officer) per `specs/027-spec-hardening/contracts/persona-profile.md`. `status:` validated. `preconditions:` none.
- **PER-035**: cross-ref to `specs/004-actor-github-agents/spec.md` actor catalogue covering all `.github/agents/technical/*.agent.md` actors. `status:` validated. `preconditions:` none.
- **PER-036** [non-AU placeholder]: capstone-country operator personas for PH (NDRRMC), JP (Cabinet Office DRR / FDMA), BD (DDM / CPP volunteers). `status:` placeholder. `preconditions:` capstone-reinterpretation decision per D-009; SME validation via `ama-rubric-grader`-vetted SME interviews.

## Hypotheses

Hypotheses use the FR-018 statement format (`If <condition> then <observable>`) and link to a structured evidence stub conforming to `specs/028-capstone-alignment/contracts/evidence-stub.contract.md`. Capstone-country hypotheses for this spec's agent ownership (where applicable) are allocated in feature 028 / US2.

- **HYP-012**: If the actors named in `specs/004-actor-github-agents/spec.md` consult on every change to this spec via the `agent` tool, then the AMA rubric criterion mean (Assumptions / Requirements / Personas / Hypotheses / Scope) for this spec rises by at least +1 band relative to the baseline captured in `specs/028-capstone-alignment/evidence/rubric-baseline.md`. **Falsification**: post-feature rubric snapshot shows a regression in any of those five criteria for this spec. **Evidence stub**: `specs/028-capstone-alignment/evidence/HYP-HYP-012.md` (created in feature 028 polish).
