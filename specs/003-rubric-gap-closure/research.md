# Research: Rubric Gap Closure — AI Integration, CI/CD, and Agent Depth

## Decision: Use the openai Python SDK with Azure OpenAI deployment for agent LLM calls

**Rationale**: The existing agents are Python-based and the constitution mandates Azure. The `openai` Python SDK natively supports Azure OpenAI endpoints via `AzureOpenAI` client configuration. This avoids adding a new framework dependency and aligns with the dual-model pattern established in feature 001's research (high-capability model for risk assessment reasoning, lower-cost model for communication drafts).

**Alternatives considered**:

- LangChain or Semantic Kernel as an orchestration layer: rejected because the agents already have deterministic orchestration logic; adding a framework for two call sites introduces unnecessary abstraction and dependency weight.
- Direct HTTP calls to the Azure OpenAI REST API: rejected because the `openai` SDK handles authentication, retry, streaming, and token counting; reimplementing that adds risk.
- Microsoft Agent Framework SDK `model_client`: rejected for this increment because the agents are not yet migrated to the framework runtime; the `openai` SDK can be wrapped in a mixin that a future migration can replace.

## Decision: Implement LLM integration as a shared mixin with per-agent prompt templates

**Rationale**: Both Risk Assessment and Communication agents need LLM calls with identical cross-cutting concerns: token budget enforcement, correlation ID propagation, latency logging, template fallback, and content safety validation. A `LLMCallMixin` in `apps/agents/common/llm_mixin.py` encapsulates these concerns once. Each agent provides its own system/user prompt templates, keeping domain logic in the agent and infrastructure in the mixin.

**Alternatives considered**:

- Duplicate LLM call logic in each agent: rejected because it violates DRY and creates maintenance risk for safety-critical fallback logic.
- Centralized LLM service in the API layer that agents call via HTTP: rejected because it adds a network hop and coupling for what should be an in-process capability of the agent runtime.

## Decision: Use rule-based content safety validation as the initial implementation

**Rationale**: The spec assumption states rule-based validation (keyword filtering, length validation, language detection) rather than a separate AI content safety service. This is sufficient for the rubric gap closure scope: check for profanity/harm keywords, validate output lengths, confirm language tags match requested languages. The architecture allows swapping in Azure AI Content Safety later without changing the agent interface.

**Alternatives considered**:

- Azure AI Content Safety service: deferred — adds a network dependency and cost; the rule-based approach satisfies the rubric requirement and can be upgraded in a follow-on feature.
- No content safety validation: rejected because the constitution requires safe outputs for public-facing alerts and the spec mandates FR-006.

## Decision: Use tenacity for retry with exponential backoff in API middleware

**Rationale**: The existing resilience middleware in `apps/api/app/middleware/resilience.py` has circuit breaker logic but no retry capability. `tenacity` is a well-maintained Python library purpose-built for retry with exponential backoff, jitter, and configurable stop conditions. It integrates cleanly as a decorator on service methods that call Cosmos DB or Redis.

**Alternatives considered**:

- Custom retry loop: rejected because tenacity handles edge cases (jitter, max delay caps, exception filtering) that are easy to get wrong in a hand-rolled implementation.
- Azure SDK built-in retry (azure-cosmos retry policy): partially used — the Azure SDK has its own transport-level retry, but application-level retries on transient failures (e.g., 429 throttled) benefit from tenacity's decorator pattern at the service boundary.

## Decision: Extend the existing in-memory event bus with subscriber dispatch and dead-letter

**Rationale**: The spec assumption states the in-memory event bus can be extended without replacing it. The current `EventBus` in `apps/api/app/services/event_bus.py` is a no-op stub that returns the envelope. It needs subscriber registration, dispatch to registered handlers, delivery status tracking, and dead-letter routing on failure. This keeps the same interface while enabling handoff chaining (FR-011–014) and dead-letter handling (FR-014, FR-025).

**Alternatives considered**:

- Replace with Azure Service Bus immediately: rejected per spec assumption — the in-memory implementation is sufficient for the rubric demonstration and local testing; production broker is a follow-on concern.
- Keep the no-op stub and simulate handoffs in tests only: rejected because the rubric requires demonstrable agent autonomy and dynamic coordination, which needs real dispatch logic.

## Decision: Use Locust for load testing

**Rationale**: Locust is a Python-based load testing tool that fits naturally into the existing Python test infrastructure. It supports programmatic test scenarios, real-time metrics, and headless CI execution. The load test suite simulates concurrent operator sessions and burst signal ingestion against FastAPI endpoints.

**Alternatives considered**:

- k6: strong alternative but requires JavaScript/TypeScript test scripts, adding a second language to the test infrastructure.
- Apache JMeter: rejected because it requires Java and XML-based test plans, which are harder to version-control and review.
- pytest-benchmark for full load tests: rejected because pytest-benchmark is suitable for micro-benchmarks (used in CI lightweight check) but not for sustained concurrent load simulation.

## Decision: Use pytest-benchmark for the CI lightweight performance regression check

**Rationale**: FR-030 requires a <60-second benchmark in CI that catches p95 regressions. `pytest-benchmark` runs as part of the existing pytest infrastructure, measures endpoint response times with statistical rigor, and can compare against stored baselines. It avoids spawning a separate load testing framework in the CI pipeline.

**Alternatives considered**:

- Locust in CI with reduced concurrency: rejected because Locust's startup overhead and warmup period exceed the 60-second budget for a meaningful test.
- Custom timing script: rejected because pytest-benchmark provides statistical analysis, baseline comparison, and CI-friendly JSON output out of the box.

## Decision: Use multi-stage Docker builds with python:3.12-slim base

**Rationale**: Multi-stage builds satisfy FR-017 (minimize image size, layer caching). The `python:3.12-slim` base image is the standard minimal Python image, significantly smaller than the full image while including necessary system libraries. A builder stage installs dependencies, a runtime stage copies only the installed packages and application code.

**Alternatives considered**:

- Alpine-based image (`python:3.12-alpine`): rejected because Alpine uses musl libc, which causes compatibility issues with some Python packages (numpy, certain Azure SDK native extensions) and increases build complexity.
- Distroless Python image: considered but rejected because it complicates debugging and doesn't provide a shell for health check commands; the non-root user constraint (FR-015, FR-016) provides the security hardening.

## Decision: Structure application IaC as a single main.bicep that references the existing monitoring module

**Rationale**: The existing `infra/bicep/monitoring.bicep` deploys Log Analytics and Application Insights. A new `main.bicep` provisions Container Apps Environment, Container Apps (API + agents), Cosmos DB account, Redis Cache, Blob Storage account, and Azure OpenAI resource, referencing monitoring outputs for diagnostic settings integration (FR-020). This avoids restructuring the existing monitoring template.

**Alternatives considered**:

- Merge everything into monitoring.bicep: rejected because it conflates monitoring concerns with application provisioning.
- Separate Bicep files per resource type with a parameters file: considered but overcomplicated for the current resource count; a single main.bicep with monitoring as a module is the right complexity level.
- Terraform: rejected because the project already uses Bicep and the constitution mandates Azure.

## Decision: Produce a screenplay-format demo document with annotated screenshots rather than video

**Rationale**: FR-021 allows "video or annotated screenplay." A version-controlled Markdown screenplay with embedded annotated screenshots/GIFs is more maintainable, reviewable, and resilient to UI changes than a recorded video. It can be rendered as a presentation or converted to video later. The slide deck (FR-022) accompanies it as a separate Markdown or PDF artifact.

**Alternatives considered**:

- Recorded video only: rejected because video is hard to update when the UI changes and harder to review in a PR.
- Interactive demo application: out of scope — the spec requires documentation artifacts, not a separate demo app.

## Decision: Add action groups to the existing monitoring Bicep with email and webhook targets

**Rationale**: FR-026 requires alert rules to deliver notifications to at least one target. Bicep action groups (`Microsoft.Insights/actionGroups`) connect to the existing alert rules. Email and webhook are the most universally available targets and don't require Teams or PagerDuty integrations in the initial scope.

**Alternatives considered**:

- Teams channel integration: deferred — requires Teams connector configuration that is environment-specific and not demonstrable in a what-if deployment.
- No action groups (alerts fire but don't notify): rejected because the rubric specifically cited missing notification targets as a gap.
