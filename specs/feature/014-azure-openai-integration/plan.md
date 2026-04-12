# Implementation Plan: Azure OpenAI Integration Configuration

**Branch**: `feature/014-azure-openai-integration` | **Date**: 2026-04-16 | **Spec**: [spec.md](../../014-azure-openai-integration/spec.md)
**Input**: Feature specification from `/specs/014-azure-openai-integration/spec.md`

## Summary

Configure and integrate Azure OpenAI into the disaster response hub's five agents (Risk Assessment, Evacuation, Monitoring, Communication, Resource Allocation). The feature provisions an Azure OpenAI resource in Australia East via Bicep IaC, migrates the existing `LLMClient` from API-key to managed-identity authentication, implements two-tier model routing (GPT-4o for reasoning, GPT-4o-mini for drafting), extends the `LLMCallMixin` fallback chain with circuit-breaker recovery, adds LLM-specific telemetry metrics, and configures per-agent token budgets with confidence-threshold gating for safety-critical outputs.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI, Pydantic v2, tenacity (retry), azure-identity (DefaultAzureCredential), openai (Azure OpenAI SDK), opentelemetry-api + opentelemetry-sdk
**Storage**: Azure Cosmos DB (existing — no new storage for this feature)
**Testing**: pytest (contract tests, integration tests, simulation tests)
**Target Platform**: Linux containers (Azure Container Apps)
**Project Type**: Multi-agent web service (disaster response coordination hub)
**Performance Goals**: <10s LLM response time (SC-001), <15s total with retries (SC-003), telemetry within 60s (SC-006)
**Constraints**: Australia-only regions (Constitution VI), zero API keys (Constitution IV), safe degradation to templates (Constitution I), <15s inclusive of 3× exponential-backoff retry (1s+2s+4s = 7s retry delay budget)
**Scale/Scope**: 5 agents, 2 model deployments, 2 environments (dev/prod), concurrent agent LLM calls under disaster load

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Requirement | Status | Notes |
|---|-----------|-------------|--------|-------|
| I | Life Safety First | Safe degradation when LLM unavailable; human override for low-confidence outputs | ✅ PASS | FR-007 template fallback, FR-011/FR-012 confidence thresholds, circuit-breaker recovery (CHK022) |
| I | Explanations for IC | Confidence scores, data sources, reasoning summary visible to IC | ✅ PASS | US6 acceptance scenario 3; existing `reasoning_summary` pattern in agents |
| II | Multi-Agent Coordination | Explicit handoffs, no silent state changes | ✅ PASS | `generation_method` marker on all outputs; `requires_human_review` flag blocks automatic escalation |
| III | Data Provenance | Traceable inputs and assumptions | ✅ PASS | FR-015 correlation ID links every LLM call to pipeline execution |
| IV | Privacy & Security | Managed identity, zero-trust, data residency | ✅ PASS | FR-004 managed identity only, FR-005 Australian endpoint validation, FR-017 no cross-region inference |
| V | Multilingual Communication | Alerts validated for language appropriateness | ✅ PASS | FR-006 content safety validates language via existing `ContentSafetyValidator` |
| VI | Azure Cloud, AU Regions | Azure-only, Australian regions only | ✅ PASS | FR-001 AU East primary / AU Southeast failover, FR-014 IaC rejects non-AU regions |
| NFR | Resilient to outages | Continue with reduced functionality | ✅ PASS | Three-tier degradation: AU East → AU Southeast (manual) → template fallback (automatic) |
| NFR | Append-only audit trail | Safety-critical actions logged | ✅ PASS | US3 scenario 4 — fallback events include error reason, timestamp, correlation ID, retry count |
| NFR | Well-Architected Framework | WAF compliance | ✅ PASS | Reliability (retry+fallback), Security (MI auth), Cost (token budgets), Operational Excellence (telemetry) |

**Gate Result**: ✅ ALL PASS — no violations, proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/feature/014-azure-openai-integration/
├── plan.md              # This file
├── research.md          # Phase 0: research findings
├── data-model.md        # Phase 1: entity and config models
├── quickstart.md        # Phase 1: developer quickstart
├── contracts/           # Phase 1: interface contracts
│   ├── llm-client.md    #   LLMClient public API contract
│   ├── llm-config.md    #   LLM configuration contract per agent
│   ├── bicep-module.md  #   Azure OpenAI Bicep module interface
│   └── telemetry.md     #   LLM telemetry metrics contract
└── tasks.md             # Phase 2 output (NOT created by plan)
```

### Source Code (repository root)

```text
apps/agents/common/
├── llm_client.py           # MODIFY: migrate API key → managed identity, add temperature, circuit breaker
├── llm_mixin.py            # MODIFY: add circuit-breaker state, structured output validation, confidence reduction
├── content_safety.py       # NO CHANGE (existing validator sufficient per spec)
├── llm_config.py           # NEW: shared LLM configuration dataclass
└── circuit_breaker.py      # NEW: circuit breaker for LLM availability recovery (CHK022)

apps/agents/risk_assessment/
├── config.py               # MODIFY: add LLM config fields (model_tier, temperature, max_output_tokens, confidence_threshold, monthly_budget)
└── telemetry.py            # MODIFY: add LLM-specific metrics

apps/agents/evacuation/
├── config.py               # MODIFY: add LLM config fields
└── telemetry.py            # MODIFY: add LLM-specific metrics (NEW file — does not exist yet)

apps/agents/monitoring/
├── config.py               # MODIFY: add LLM config fields
└── telemetry.py            # MODIFY: add LLM-specific metrics (NEW file — does not exist yet)

apps/agents/communication/
├── config.py               # MODIFY: add LLM config fields
└── telemetry.py            # MODIFY: add LLM-specific metrics

apps/agents/resource_allocation/
├── config.py               # MODIFY: add LLM config fields
└── telemetry.py            # MODIFY: add LLM-specific metrics

infra/
├── main.bicep              # MODIFY: add model deployments to existing openAi resource, add RBAC, add diagnostics, set disableLocalAuth=true
└── modules/
    └── azure-openai.bicep  # NEW: dedicated module for OpenAI deployments, RBAC, diagnostics

tests/
├── contract/
│   ├── test_llm_fallback.py           # MODIFY: add circuit-breaker recovery test
│   ├── test_llm_managed_identity.py   # NEW: verify MI auth, no API key paths
│   ├── test_llm_model_routing.py      # NEW: verify purpose→deployment routing
│   ├── test_llm_confidence.py         # NEW: verify confidence threshold gating
│   ├── test_llm_circuit_breaker.py    # NEW: verify circuit breaker state transitions
│   └── test_llm_telemetry.py          # NEW: verify LLM metric emission
├── integration/
│   └── test_llm_integration.py        # NEW: end-to-end LLM call with fallback chain
└── simulation/
    └── test_quickstart_live_llm_rehearsal.py  # MODIFY: update for MI auth

docs/
└── risk-register/
    └── RISK-AOAI-001.md    # NEW: AI model reliability risk register entry (FR-019)
```

**Structure Decision**: Extends the existing monorepo structure. No new top-level directories. The LLM integration modifies existing `apps/agents/common/` files and extends each agent's `config.py`. A new dedicated Bicep module `azure-openai.bicep` follows the existing `infra/modules/` convention. The circuit breaker is a new module in `common/` rather than inlining it in the mixin, for testability and single-responsibility.

## Complexity Tracking

> No constitution violations — this section is intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
