# Research: Azure OpenAI Integration Configuration

**Feature**: 014-azure-openai-integration
**Date**: 2026-04-16
**Status**: Complete — all NEEDS CLARIFICATION items resolved

## R1: Managed Identity Authentication Migration

**Question**: How to migrate `LLMClient` from API-key (`AZURE_OPENAI_API_KEY`) to managed identity (`DefaultAzureCredential`) without breaking existing `LLMCallMixin` contract?

**Decision**: Replace the `AzureOpenAI(api_key=...)` constructor with `AzureOpenAI(azure_ad_token_provider=get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"))` from `azure.identity`. Remove all references to `AZURE_OPENAI_API_KEY`.

**Rationale**:
- The `openai` Python SDK natively supports `azure_ad_token_provider` parameter, which accepts a callable that returns a bearer token. This is the recommended pattern for Azure-managed workloads.
- `DefaultAzureCredential` automatically chains `ManagedIdentityCredential` (production) → `AzureCliCredential` (local dev) → `EnvironmentCredential` (CI), providing seamless auth across environments.
- Token caching and refresh are handled internally by `azure-identity` — no custom logic needed (CHK011 resolved).
- Token expiry during long-running processes is handled by the `azure_ad_token_provider` pattern, which re-acquires tokens on each call (CHK073 resolved).
- System-assigned managed identity is already configured on the Container Apps (`identity: { type: 'SystemAssigned' }` in `main.bicep` lines 435, 504, 555). The Bicep module adds `Cognitive Services OpenAI User` RBAC role assignment.

**Alternatives Considered**:
- `ManagedIdentityCredential` directly: rejected — less flexible for local dev and CI scenarios.
- Certificate-based `ServicePrincipal`: rejected — adds secret management complexity, violates zero-trust simplicity goal.
- Keep API key as fallback: rejected — Constitution IV mandates zero API keys; `disableLocalAuth: true` on the resource enforces this.

## R2: Frozen Dataclass Configuration with Environment Variables (CHK018)

**Question**: How do frozen dataclasses accept environment-variable overrides if they're immutable after construction?

**Decision**: Env vars are read at construction time via `field(default_factory=lambda: os.getenv(...))`. The dataclass is frozen *after* construction — values are set once from env vars, then immutable for the process lifetime. This is the existing pattern across all 5 agent configs.

**Rationale**:
- Examined `apps/agents/risk_assessment/config.py` (lines 14-119): `@dataclass(frozen=True)` with `field(default_factory=lambda: float(os.getenv("...", "default")))` — env vars are evaluated during `__init__`, before the freeze.
- Same pattern in `monitoring/config.py`, `communication/config.py`, `evacuation/config.py`, `resource_allocation/config.py`.
- Override mechanism: set env vars before the process starts (container env vars in Bicep, `.env` files locally). No hot-reload needed (CHK068 — explicitly out of scope per spec).
- New LLM config fields (`model_tier`, `temperature`, `max_output_tokens`, `confidence_threshold`, `fallback_reduction_factor`, `monthly_budget_usd`) follow this exact pattern.

**Alternatives Considered**:
- Mutable config with hot-reload: rejected — adds complexity, frozen pattern is established codebase convention.
- Separate config file (YAML/TOML): rejected — env-var pattern is the established codebase convention and is container-native.

## R3: Circuit Breaker for LLM Recovery After Fallback (CHK022, CHK024)

**Question**: How should agents recover from LLM unavailability after falling back to templates? Currently, each call retries independently — there's no mechanism to avoid hammering a failed endpoint or to detect recovery.

**Decision**: Implement a lightweight circuit breaker in `apps/agents/common/circuit_breaker.py` with three states: CLOSED (normal), OPEN (skip LLM, use template), HALF_OPEN (probe LLM availability). Integrate into `LLMCallMixin._generate_with_fallback()`.

**Rationale**:
- **CLOSED** → OPEN: After `failure_threshold` consecutive failures (default: 3, matching retry count), the circuit opens. All subsequent calls skip LLM and go directly to template fallback — no retries wasted.
- **OPEN** → HALF_OPEN: After `recovery_timeout` seconds (default: 30), the next call is allowed through as a probe.
- **HALF_OPEN** → CLOSED: If the probe succeeds, circuit closes, normal operation resumes.
- **HALF_OPEN** → OPEN: If the probe fails, circuit re-opens, timer resets.
- State is per-agent-instance (not global), so one agent's circuit state doesn't affect others (aligns with US3 edge case — rate limiting on one agent must not block others).
- This pattern is well-established (Polly, Hystrix, resilience4j) and keeps the retry logic in `tenacity` unchanged — the circuit breaker wraps the entire retry+call sequence.

**Alternatives Considered**:
- No circuit breaker (retry every call independently): rejected — wastes retry budget on a known-down endpoint, increases latency during outages.
- Global shared circuit breaker across agents: rejected — agents run independently, shared state adds coupling.
- External circuit breaker (Azure API Management): rejected — adds infrastructure dependency for a client-side concern.

**Implementation Notes**:
- Thread-safe: use `threading.Lock` for state transitions (agents may have concurrent async tasks).
- Testable: pure state machine with injectable clock for deterministic testing.
- Configurable: `failure_threshold`, `recovery_timeout` as constructor params with env-var defaults.

## R4: Fallback Confidence Reduction Factor (CHK026)

**Question**: What should the default fallback reduction factor be, and how is it applied?

**Decision**: Default fallback reduction factor is **0.5** (halve confidence when using template fallback). Applied as a multiplier: `confidence = base_confidence × fallback_reduction_factor`.

**Rationale**:
- Template outputs are structurally correct but lack the nuance of LLM analysis. A 50% confidence reduction reflects that template outputs are significantly less reliable for safety-critical decisions.
- Example: Risk Assessment generates a confidence score of 0.85 from LLM → passes threshold (0.7). Same input with template fallback → 0.85 × 0.5 = 0.425 → below threshold → flagged for human review.
- The existing `fallback_reduction_factor` field in `risk_assessment/config.py` (line 54) uses 0.8 for contradiction-based reduction. LLM fallback warrants a steeper reduction (0.5) because the output quality gap is larger.
- Configurable via `LLM_FALLBACK_REDUCTION_FACTOR` env var in each agent's config.

**Alternatives Considered**:
- Factor of 0.8 (match existing contradiction reduction): rejected — template fallback represents a bigger quality drop than data contradiction.
- Factor of 0.0 (always require review on fallback): rejected — too aggressive; some template outputs for non-safety-critical tasks are adequate.
- Additive penalty (subtract 0.3): rejected — multiplicative scaling preserves relative ordering of scores.

## R5: Token Budget Trimming Mechanism (CHK040)

**Question**: What does "trim" mean for responses exceeding max output tokens?

**Decision**: Trim at the character level using the existing pattern: `text[: max(80, int(len(text) * 0.8))]`. This is already implemented in `llm_mixin.py` line 43.

**Rationale**:
- The existing `LLMCallMixin._generate_with_fallback()` already implements character-based trimming when `output_tokens > max_output_tokens`.
- The trim preserves at least 80 characters (minimum readable content) and retains 80% of the text.
- The Azure OpenAI `max_tokens` parameter is the primary enforcement — it instructs the API to stop generating at the limit. The client-side trim is a safety net for edge cases where the API slightly exceeds the requested limit.
- Sentence-boundary trimming would require NLP processing — overengineered for a safety net.

**Alternatives Considered**:
- Token-boundary trimming (using tiktoken): rejected — adds a dependency for a rarely-triggered safety net.
- Sentence-boundary trimming: rejected — requires NLP processing, disproportionate complexity.
- No trimming (just log warning): rejected — FR-010 requires enforcement, not just reporting.

## R6: Endpoint Region Validation (FR-005, CHK042)

**Question**: How does the LLM client validate that the Azure OpenAI endpoint resolves to an Australian region?

**Decision**: URL pattern matching on the endpoint hostname. Australian Azure OpenAI endpoints follow the pattern `*.australiaeast.api.cognitive.microsoft.com` or `*.australiasoutheast.api.cognitive.microsoft.com` (or custom subdomain with region in DNS resolution). Validate at `LLMClient.__init__()` — fail fast if the pattern doesn't match.

**Rationale**:
- Azure OpenAI custom subdomains resolve to regional endpoints. The endpoint URL provided via `AZURE_OPENAI_ENDPOINT` can be validated by checking that it contains an Australian region identifier.
- The Bicep module enforces region at provisioning time (FR-014 `@allowed` parameter). The Python-side check is defense-in-depth.
- DNS-based validation (resolving the IP and checking Azure region mapping) is fragile and adds network dependency at startup.
- Azure metadata API requires the client to be running inside Azure — not available during local dev.

**Alternatives Considered**:
- DNS resolution + IP geolocation: rejected — fragile, adds startup latency, requires network.
- Azure Resource Manager API call: rejected — adds ARM dependency, requires additional permissions.
- No client-side validation (rely on Bicep only): rejected — defense-in-depth principle; spec requires client validation.

## R7: Structured Output Validation (FR-018, CHK044)

**Question**: Which LLM outputs are "structured" and what models must they validate against?

**Decision**: Structured outputs are agent-specific data models that the agent expects the LLM to populate (e.g., risk assessment scores, evacuation route recommendations). Validation uses the existing Pydantic models in each agent. The `LLMCallMixin` provides a hook for post-LLM validation; each agent implements its own validator. Validation failure triggers template fallback.

**Rationale**:
- Each agent already defines its output structures (e.g., `RiskAssessment`, `EvacuationPlan`, `AlertMessage`). These are the "existing data models" referenced in FR-018.
- The LLM client returns raw text; the consuming agent parses it into its domain model. If parsing/validation fails, the mixin's fallback path handles it.
- Adding a generic `validate_structured_output(text, model_class)` method to the mixin keeps the contract clean while delegating model-specific validation to each agent.

**Alternatives Considered**:
- JSON mode with schema enforcement at the API level: rejected — Azure OpenAI JSON mode doesn't guarantee schema conformance, only valid JSON.
- Central schema registry: rejected — overengineered for 5 agents with existing Pydantic models.

## R8: Transient Error Classification (CHK041)

**Question**: Is the "transient failures" definition in FR-008 exhaustive, and could it include non-transient errors?

**Decision**: Transient failures are exclusively HTTP 429 (rate limit) and HTTP 503 (service unavailable). All other HTTP errors (400, 401, 403, 404, etc.) are non-transient and should NOT be retried.

**Rationale**:
- The existing `LLMClient._is_transient()` (line 88-92) already correctly checks `status in (429, 503)`.
- HTTP 401 (auth failure) with managed identity should never be transient — it indicates misconfigured RBAC, which won't self-resolve through retries.
- HTTP 400 (bad request) indicates a prompt/parameter error that won't change on retry.
- This is consistent across FR-008, US3 acceptance scenarios, and clarification session 2.

## R9: Azure OpenAI Bicep Module Design

**Question**: How should the new Bicep module be structured to follow existing `infra/modules/` conventions?

**Decision**: Create `infra/modules/azure-openai.bicep` as a dedicated module that provisions model deployments, RBAC role assignments, and diagnostic settings for an existing Azure OpenAI resource. The resource itself remains in `main.bicep` (where it already exists at line 379).

**Rationale**:
- The OpenAI resource (`Microsoft.CognitiveServices/accounts`) is already provisioned in `main.bicep` line 379-390. Moving it would be a breaking change.
- The new module adds: (1) model deployments with TPM quotas, (2) RBAC role assignments for agent managed identities, (3) diagnostic settings routing to Log Analytics.
- Follow existing parameter conventions: `param location string`, `param envPrefix string`, `param tags object` (seen in all modules).
- Follow existing RBAC pattern from `communication-agent.bicep` lines 264-273 (`cognitiveServicesOpenAiRole`).
- Follow existing diagnostic pattern from `main.bicep` lines 695-706 (`envDiagnostic`).
- Add `@allowed(['australiaeast', 'australiasoutheast'])` on location parameter (FR-014).

**Changes to `main.bicep`**:
- Set `disableLocalAuth: true` on the existing `openAi` resource (currently `false` at line 389).
- Add module reference to `azure-openai.bicep` for deployments, RBAC, diagnostics.
- Add new env vars to Container Apps: `AZURE_OPENAI_REASONING_DEPLOYMENT`, `AZURE_OPENAI_DRAFTING_DEPLOYMENT`.

**Alternatives Considered**:
- Inline everything in `main.bicep`: rejected — `main.bicep` is already 722 lines; a module is more maintainable.
- Move the entire OpenAI resource to the module: rejected — breaking change to existing deployment.

## R10: Cost Tracking and Budget Warning (FR-021, CHK033, CHK052)

**Question**: How is the dollar-to-token conversion calculated, and is the "warning metric" consistent with "real-time cost alerting" being out of scope?

**Decision**: Token-to-dollar conversion uses Azure OpenAI pricing for the Australia East region. The warning is emitted as an OpenTelemetry metric (`llm.budget_exceeded` counter), NOT as a real-time alert. This is consistent with FR-021 ("emit a warning metric") and the out-of-scope declaration ("Real-time cost alerting").

**Rationale**:
- FR-021 specifies "emit a warning metric" — this is a telemetry metric, not an Azure Monitor alert.
- The out-of-scope item "Real-time cost alerting" refers to automated enforcement (request blocking) and Azure Monitor alert rules, not metric emission.
- Pricing for Australia East (approximate, subject to Azure pricing changes):
  - GPT-4o: ~$2.50/1M input tokens, ~$10.00/1M output tokens
  - GPT-4o-mini: ~$0.15/1M input tokens, ~$0.60/1M output tokens
- Budget tracking is cumulative within a monthly window, tracked in-memory per agent process. Process restarts reset the counter — this is acceptable because the telemetry pipeline provides durable historical data for cost analysis.
- No database persistence for budget tracking — aligns with "tracking only, no enforcement" scope.

**Alternatives Considered**:
- Azure Cost Management API integration: rejected — adds external dependency for a monitoring-only feature.
- Persistent budget tracking in Cosmos DB: rejected — overengineered for tracking-only with no enforcement.
- Azure Monitor alert rule for budget breach: rejected — explicitly out of scope.

## R11: Model Deployment Availability in Australia East (CHK082)

**Question**: Are GPT-4o and GPT-4o-mini available in Australia East?

**Decision**: Confirmed available. Both models are listed in the Azure OpenAI model availability matrix for Australia East as of 2026-04.

**Rationale**:
- Azure OpenAI has expanded Australian region support since 2024. Both GPT-4o (2024-08-06) and GPT-4o-mini are available in Australia East for standard deployments.
- If unavailable at provisioning time, the spec defines Australia Southeast as the fallover region (Assumption 1).
- The Bicep module uses `@allowed(['australiaeast', 'australiasoutheast'])` to restrict to these two regions only.

## R12: Dev/Test Environment Without Azure OpenAI (CHK069)

**Question**: Can developers run agents locally without an Azure OpenAI resource?

**Decision**: Yes — the existing `LLMClient` already handles missing configuration gracefully. When `AZURE_OPENAI_ENDPOINT` is not set, `self._client` is `None`, and `generate_response()` raises `RuntimeError("Azure OpenAI client is not configured")`. The `LLMCallMixin` catches this and falls back to template output.

**Rationale**:
- The existing fallback pattern (`LLMCallMixin._generate_with_fallback()` catch-all at line 65) already provides dev/test support — no Azure OpenAI resource needed.
- With managed identity migration, the `AzureCliCredential` in `DefaultAzureCredential` allows developers who are logged in via `az login` to test against a real Azure OpenAI resource.
- For fully offline development, agents produce template outputs automatically.
- No new mock/stub infrastructure is needed.
