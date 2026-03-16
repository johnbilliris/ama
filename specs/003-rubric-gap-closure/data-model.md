# Data Model: Rubric Gap Closure — AI Integration, CI/CD, and Agent Depth

> This document defines the **new and modified** entities introduced by feature 003. Entities from feature 001 that are unchanged are not repeated here. See `specs/001-disaster-response-hub/data-model.md` for the base data model.

## ModelDeployment

**Purpose**: Represents an Azure OpenAI language model endpoint configuration used by agents for LLM-generated content. Each deployment defines the endpoint, authentication, token budget, and fallback behavior.

**Fields**:
- `deploymentId`: string, immutable identifier (matches Azure OpenAI deployment name)
- `endpointUrl`: string, Azure OpenAI endpoint URL
- `modelName`: string, underlying model identifier (e.g., `gpt-4o`, `gpt-4o-mini`)
- `modelVersion`: string, model version string
- `apiVersion`: string, Azure OpenAI API version
- `tokenBudgetInput`: integer, maximum input tokens per request
- `tokenBudgetOutput`: integer, maximum output tokens per request
- `contentSafetyPolicy`: enum (`rule_based`, `azure_content_safety`, `none`)
- `fallbackMode`: enum (`template`, `error`)
- `timeoutSeconds`: float, request-level timeout
- `purpose`: enum (`reasoning`, `drafting`), maps to the dual-model pattern from research
- `status`: enum (`active`, `disabled`, `degraded`)

**Relationships**:
- Used by Risk Assessment agent (purpose=`reasoning`) and Communication agent (purpose=`drafting`).
- Referenced in LLM call logs for traceability.

**Validation rules**:
- `endpointUrl` must be a valid HTTPS URL.
- `tokenBudgetInput` and `tokenBudgetOutput` must be positive integers.
- `timeoutSeconds` must be > 0 and ≤ 120.
- `contentSafetyPolicy` must not be `none` when the deployment is used for public-facing alert content.

---

## AgentHandoffEvent (extends existing AgentHandoff)

**Purpose**: An executed handoff between agents, extending the existing `AgentHandoff` dataclass with delivery lifecycle tracking. Replaces the frozen dataclass with a mutable model that tracks delivery status, retries, and dead-letter routing.

**Fields** (inherited from AgentHandoff):
- `sourceAgent`: string, originating agent identifier
- `targetAgent`: string, destination agent identifier
- `scopeKey`: string, tenant-scoped key for the handoff
- `confidence`: float, 0.0–1.0
- `payload`: dict, handoff payload

**Fields** (new):
- `handoffId`: string, unique identifier for the handoff event
- `incidentId`: string, associated incident
- `status`: enum (`pending`, `delivered`, `retrying`, `failed`, `dead_lettered`)
- `retryCount`: integer, number of delivery attempts (0–3)
- `maxRetries`: integer, default 3
- `retryWindowSeconds`: integer, default 300 (5 minutes)
- `nextRetryAt`: datetime or null, scheduled next retry
- `timelineEventId`: string or null, reference to the recorded TimelineEvent
- `deadLetterEntryId`: string or null, reference to DeadLetterEntry if failed
- `createdAt`: datetime
- `deliveredAt`: datetime or null
- `failedAt`: datetime or null
- `failureReason`: string or null

**Relationships**:
- One AgentHandoffEvent creates one TimelineEvent (FR-013).
- One AgentHandoffEvent may create one DeadLetterEntry on permanent failure (FR-014).
- Many AgentHandoffEvents belong to one Incident.

**Validation rules**:
- `confidence` must be between 0.0 and 1.0 inclusive.
- `retryCount` must not exceed `maxRetries`.
- `status` can only transition: `pending` → `delivered` | `retrying`; `retrying` → `delivered` | `failed`; `failed` → `dead_lettered`.
- `scopeKey` must match the incident's tenant scope.

**State transitions**:
```
pending ──→ delivered       (target agent processes successfully)
pending ──→ retrying        (target circuit open or delivery timeout)
retrying ──→ delivered      (retry succeeds)
retrying ──→ failed         (max retries exhausted)
failed ──→ dead_lettered    (stored in dead-letter store)
```

---

## DeadLetterEntry

**Purpose**: A failed operation record stored for later operator inspection. Captures failed handoff deliveries, signal ingestion failures, and event bus delivery failures with full context for debugging and replay.

**Fields**:
- `entryId`: string, unique identifier
- `entryType`: enum (`handoff_failure`, `ingestion_failure`, `event_delivery_failure`)
- `correlationId`: string, from resilience middleware
- `originalPayload`: dict, the full payload that failed
- `failureReason`: string, human-readable failure description
- `failureCode`: string, machine-readable failure code (e.g., `CIRCUIT_OPEN`, `TIMEOUT`, `VALIDATION_ERROR`)
- `retryCount`: integer, number of retries attempted before dead-lettering
- `sourceService`: string, the service or agent that produced the payload
- `targetService`: string, the intended recipient
- `incidentId`: string or null, associated incident if applicable
- `tenantScopeKey`: string, tenant scope for access control
- `createdAt`: datetime, when the entry was dead-lettered
- `reviewedAt`: datetime or null, when an operator reviewed the entry
- `reviewedBy`: string or null, operator persona ID
- `resolution`: enum (`pending`, `replayed`, `discarded`, `escalated`) default `pending`

**Relationships**:
- One DeadLetterEntry may reference one AgentHandoffEvent.
- Many DeadLetterEntries belong to one tenant scope.

**Validation rules**:
- `correlationId` is required.
- `originalPayload` must not be empty.
- `failureReason` must not be empty.
- `tenantScopeKey` is required for multi-tenant access control scoping.
- `resolution` can only transition: `pending` → `replayed` | `discarded` | `escalated`.

---

## LoadTestResult

**Purpose**: A performance test execution result capturing scenario outcomes and pass/fail status per documented performance target.

**Fields**:
- `resultId`: string, unique identifier
- `scenarioName`: string, e.g. `dashboard_concurrent_load`, `signal_burst_ingestion`
- `executedAt`: datetime
- `durationSeconds`: float, total test duration
- `concurrentUsers`: integer, number of simulated users
- `totalRequests`: integer
- `successfulRequests`: integer
- `failedRequests`: integer
- `errorRate`: float, percentage 0.0–100.0
- `p50LatencyMs`: float
- `p95LatencyMs`: float
- `p99LatencyMs`: float
- `throughputPerSecond`: float, requests per second sustained
- `targetName`: string, the performance target being validated (e.g., `dashboard_p95_lt_2s`)
- `targetThreshold`: float, the threshold value
- `targetUnit`: string, e.g. `ms`, `req/hour`, `percent`
- `passed`: boolean, whether measured value meets the target
- `environment`: enum (`local`, `staging`, `production`)
- `notes`: string or null

**Relationships**:
- Many LoadTestResults are produced by one load test execution.
- LoadTestResults reference documented performance targets from the spec.

**Validation rules**:
- `concurrentUsers` must be positive.
- `errorRate` must be between 0.0 and 100.0.
- `p50LatencyMs` ≤ `p95LatencyMs` ≤ `p99LatencyMs`.
- `passed` must be consistent with `targetThreshold` and measured value.

---

## PipelineStage

**Purpose**: A discrete step in the CI/CD pipeline, used for reporting granular pass/fail status per FR-010. This entity is primarily represented in GitHub Actions workflow YAML rather than as a runtime domain model.

**Fields**:
- `stageName`: string, e.g. `python-test`, `python-lint`, `ts-typecheck`, `web-build`, `perf-benchmark`
- `status`: enum (`pass`, `fail`, `skip`, `running`)
- `durationSeconds`: float or null
- `errorSummary`: string or null, first failure message if status is `fail`

**Relationships**:
- Many PipelineStages belong to one CI run.

**Validation rules**:
- `stageName` must be unique within a pipeline run.
- `errorSummary` is required when `status` is `fail`.

> Note: This entity is not persisted in the application's data store. It describes the structure of CI pipeline output for human and automated consumption. Stage names (python-test, python-lint, ts-typecheck, web-build, perf-benchmark) align with the GitHub Actions workflow step naming convention for FR-010 compliance.

---

## ContainerDefinition

**Purpose**: A Dockerfile specification for an application service, describing the base image, build stages, exposed port, health check command, and security constraints. This entity describes version-controlled build artifacts rather than runtime domain objects.

**Fields**:
- `baseImage`: string, e.g. `python:3.12-slim`
- `buildStages`: array of stage names, e.g. `[builder, runtime]`
- `exposedPort`: integer or null, e.g. `8000`
- `healthCheckCommand`: string or null, e.g. `CMD curl -f http://localhost:8000/health || exit 1`
- `nonRootUser`: boolean, must be `true`
- `embeddedSecrets`: boolean, must be `false`

**Relationships**:
- One ContainerDefinition per deployable service (API, agent runtime).
- Referenced by IaC templates (main.bicep) for container image configuration.

**Validation rules**:
- `nonRootUser` must be `true` (FR-015, FR-016).
- `embeddedSecrets` must be `false`.
- `baseImage` should use a minimal variant (e.g., `-slim`).

> Note: This entity is a build artifact specification (Dockerfile), not a runtime domain model.

---

## AlertActionGroup

**Purpose**: A notification target configuration for operational alerts, referenced by Bicep alert rules to deliver notifications when thresholds are breached.

**Fields**:
- `actionGroupName`: string, Azure resource name
- `shortName`: string, ≤12 characters for SMS display
- `targets`: array of ActionTarget:
  - `targetType`: enum (`email`, `webhook`, `sms`)
  - `name`: string, display name
  - `endpoint`: string, email address, webhook URL, or phone number
  - `isEnabled`: boolean
- `tags`: dict, Azure resource tags

**Relationships**:
- One AlertActionGroup is referenced by many alert rules.
- Defined in Bicep IaC (infra/bicep/monitoring.bicep).

**Validation rules**:
- `shortName` must be ≤12 characters.
- At least one target must be enabled.
- Webhook endpoints must be valid HTTPS URLs.
- Email addresses must be valid format.

> Note: This entity is an infrastructure-as-code resource definition, not a runtime domain model.

---

## Modifications to Existing Entities

### Recommendation (modified)

**New fields**:
- `generationMethod`: enum (`llm`, `template`, `template_fallback`, `safety_fallback`), indicates how the explanation was produced.
- `modelDeploymentId`: string or null, references the ModelDeployment used (null for template-generated).
- `tokenUsage`: object or null, `{ input_tokens: int, output_tokens: int }` when LLM-generated.

**Modified behavior**:
- `explanation` field is now populated by the LLM when available, with signal ID citations embedded in the text.
- When `generationMethod` is `template_fallback` or `safety_fallback`, the explanation uses the existing deterministic template.

### TimelineEvent (modified)

**New event_type values**:
- `"handoff"`: records agent-to-agent handoff events (FR-013).
- `"dead_letter"`: records when a handoff or delivery is dead-lettered.
- `"llm_call"`: records LLM invocations with model deployment, latency, and token usage.

**New payload fields for handoff events**:
- `source_agent`: string
- `target_agent`: string
- `scope_key`: string
- `confidence`: float
- `handoff_status`: enum (`delivered`, `failed`, `dead_lettered`)
- `payload_summary`: string, truncated summary of the handoff payload

### PublicAlert (modified)

**New fields**:
- `generationMethod`: enum (`llm`, `template`, `template_fallback`, `safety_fallback`), mirrors Recommendation.
- `modelDeploymentId`: string or null.
- `contentSafetyResult`: enum (`passed`, `failed_with_fallback`, `not_checked`) default `not_checked`.

**Modified behavior**:
- `content_blocks` dict keys are language codes (e.g., `en-AU`, `zh-Hans`); values are LLM-generated or template-generated content per language.
- All 6 supported languages are populated in every draft per clarification decision.

### EventBus (modified service)

**New capabilities**:
- Subscriber registration: `subscribe(channel: str, handler: Callable)`.
- Dispatch: `publish()` now invokes registered handlers for the envelope's channel.
- Delivery status: returns delivery result (success/failure per subscriber).
- Dead-letter routing: on permanent delivery failure, stores the envelope in DeadLetterEntry via dead_letter_service.
