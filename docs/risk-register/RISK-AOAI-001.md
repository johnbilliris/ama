# Risk Register: AI Model Unavailability During Disaster Operations

| Field | Value |
|-------|-------|
| **Risk ID** | `RISK-AOAI-001` |
| **Risk Title** | AI Model Unavailability During Disaster Operations |
| **Category** | Operational / AI Reliability |
| **Probability** | Medium (20–50%) — Azure OpenAI outages during peak disaster load |
| **Impact** | High — degraded agent output quality during critical decision windows |
| **Mitigation Strategy** | (1) Template fallback for all 5 agents, (2) Circuit breaker prevents retry storms (3-failure threshold, 30s recovery), (3) Manual failover to AU Southeast via IaC parameter override, (4) Confidence threshold (0.7) blocks low-confidence outputs from automatic escalation |
| **Residual Risk** | Low — template outputs maintain operational continuity with reduced quality |
| **Owner** | Platform Operations Lead |
| **Review Cadence** | Quarterly + post-incident |
| **Created** | 2026-04-16 |
| **Last Reviewed** | 2026-04-16 |

---

# Risk Register: Token Quota Exhaustion

| Field | Value |
|-------|-------|
| **Risk ID** | `RISK-AOAI-002` |
| **Risk Title** | Token Quota Exhaustion Under Sustained Disaster Load |
| **Category** | Cost / Capacity |
| **Probability** | Low–Medium (10–30%) — concurrent multi-agent usage during prolonged disaster |
| **Impact** | Medium — HTTP 429 rate limiting causes increased latency and fallback activations |
| **Mitigation Strategy** | (1) Per-agent monthly budget tracking ($50 dev, $500 prod) with `llm.budget.exceeded` alerts, (2) Two-tier model routing minimises GPT-4o usage to safety-critical agents only, (3) Token-per-minute quotas configurable via Bicep params (30K/60K dev, 120K/240K prod), (4) Tenacity retry with exponential backoff handles transient 429s |
| **Residual Risk** | Low — budget alerts enable proactive quota adjustment; template fallback ensures continuity |
| **Owner** | Platform Operations Lead |
| **Review Cadence** | Monthly (cost review) + post-incident |
| **Created** | 2026-04-16 |
| **Last Reviewed** | 2026-04-16 |

---

# Risk Register: Credential Propagation Delays

| Field | Value |
|-------|-------|
| **Risk ID** | `RISK-AOAI-003` |
| **Risk Title** | Managed Identity Credential Propagation Delays |
| **Category** | Security / Authentication |
| **Probability** | Low (5–15%) — Entra ID role assignment propagation can take up to 10 minutes |
| **Impact** | Medium — agents unable to authenticate to Azure OpenAI during initial deployment or RBAC changes |
| **Mitigation Strategy** | (1) Graceful degradation — LLMClient sets `_client = None` on auth failure, triggers template fallback, (2) Bicep RBAC assignments use `Cognitive Services OpenAI User` role with `dependsOn` sequencing, (3) Health check endpoints verify authentication before accepting traffic, (4) `disableLocalAuth: true` ensures no accidental API key fallback |
| **Residual Risk** | Low — brief window of template-only operation during deployments; no security exposure |
| **Owner** | Platform Operations Lead |
| **Review Cadence** | Quarterly + post-deployment |
| **Created** | 2026-04-16 |
| **Last Reviewed** | 2026-04-16 |
