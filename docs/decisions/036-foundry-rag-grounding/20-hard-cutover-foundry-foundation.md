# ADR 20 — Hard cutover migration to Microsoft Foundry as the LLM foundation

**FR**: FR-RAG-FM-06 (amended); FR-RAG-FM-02 (amended)
**Cluster**: Step 9 user pivot 2026-05-09 — supersedes the per-agent canary cutover originally settled by Pass 2 Q-P2-01
**Persona memo citation**: User directive 2026-05-09: *"There will be NO gradual cutover of OpenAI to Azure Foundry. The entire existing Azure infra will be deleted and redeployed with Azure AI Foundry as the foundation for all LLMs."*
**Approver**: Product Owner (user) 2026-05-09; ratified by AMA Spec-036 Architecture Review same day
**Status**: Accepted — supersedes ADR-16 §"per-agent canary cutover" semantics; ADR-16 is retained for **index-version blue/green** (corpus rebuilds), which remains the production pattern.

## Context

Spec 036 originally settled — at Pass 2 Q-P2-01 — a **per-agent canary** approach to migrating the LLM inference plane from Azure OpenAI to Microsoft Foundry. That approach assumed:

- A blue/green window during which both AOAI and Foundry deployments coexist.
- An equivalence gate (`apps/eval-runner/src/ama_eval/per_agent_canary_gate.py`) running ≥95% decision-equivalence before each agent's `FEATURE_FOUNDRY_RAG_<AGENT>` flag flipped to `1`.
- A `LEGACY_AZURE_OPENAI=1` rollback escape hatch retained until the final agent flipped.
- An equivalence-regression alert (`infra/bicep/modules/foundry-rag-cutover-alerts.bicep` Alert 3) that paused the canary on per-agent equivalence drop.

Verification on 2026-05-09 against the live `rg-ama` resource group revealed that:

1. The deployed chat plane is the legacy Azure OpenAI account (`Microsoft.CognitiveServices/accounts` kind `OpenAI`) carrying three GPT-5.4 deployments.
2. The Foundry-RAG infra is gated behind `enableSpec036FoundryRag=false`, so AI Search and the corpus ingest job are **not** provisioned.
3. The container apps are wired to `AZURE_OPENAI_ENDPOINT`; `AZURE_AI_PROJECT_ENDPOINT` is **unset** in their environment.
4. None of the per-agent canary feature flags have ever been flipped — the equivalence gate has never run against live traffic.

The product owner has elected to delete the existing infrastructure and redeploy from scratch, with Microsoft Foundry as the foundation for all LLM traffic from day one. There is no operational reason to preserve a coexistence window that was never exercised, and removing it eliminates an entire class of cutover-only failure modes.

## Decision

1. **Hard cutover, not phased migration.** The migration path from Azure OpenAI to Microsoft Foundry is a single atomic transition: tear down the existing Azure resources, then redeploy with `Microsoft.CognitiveServices/accounts` `kind: 'AIServices'` (Foundry) as the chat plane. There is no dual-running window.
2. **Foundry endpoint is the only chat plane.** Both `AZURE_AI_PROJECT_ENDPOINT` and the legacy `AZURE_OPENAI_ENDPOINT` env vars point at the same Foundry endpoint URL, so existing code paths reading either variable transparently target Foundry. Code-level removal of the legacy variable is deferred to a follow-on cleanup PR (the env-var compatibility seam costs nothing at runtime).
3. **`FEATURE_FOUNDRY_RAG_<AGENT>` is on by default in the deployed environment.** The flag's default value in code remains `false` so that test environments do not silently activate grounding paths, but Bicep sets the env var to `1` for all five named agents on the `agents` Container App. This means the hard-cutover deploy lands with all agents grounded.
4. **The per-agent canary gate is retained as a *regression* gate, not a *cutover* gate.** `apps/eval-runner/src/ama_eval/per_agent_canary_gate.py` continues to run as part of CI and as a corpus-rebuild quality check, but it no longer participates in any per-agent activation flow.
5. **The equivalence-regression alert is retired for migration purposes.** `foundry-rag-cutover-alerts.bicep` Alert 3 (decision-equivalence regression) is no longer wired into production action groups. The other three alerts (gateway-deny, citation-drop, offline-cache TTL) remain in production. The Bicep module is preserved for index-rebuild-quality monitoring per ADR-16; deletion of Alert 3 is a follow-on cleanup.
6. **`LEGACY_AZURE_OPENAI=1` is deprecated.** The flag remains importable in code so historical rollback drills (FR-RAG-FM-06) replay correctly, but no production environment sets it. The flag is marked for removal in the next minor cleanup.
7. **All seed data is reseeded on redeploy.** `azd down --force --purge` deletes the Cosmos account; `azd provision` reruns the post-provision seeder via `scripts/seed-database.ps1`/`.sh`, restoring all 855 seed records, recovery catalogue, and coordination tasks.

## Rationale

- **Why hard cutover?** A coexistence window only earns its complexity if it is exercised. The per-agent canary was never run against live traffic, so the eight pieces of machinery it requires (feature flags, equivalence gate, regression alert, runbook, action-group routing, audit-record `legacy_or_foundry` discriminator, fallback chain, dual-endpoint env vars) are pure cost. Eliminating them removes ~600 lines of conditional code paths and one persistent attack surface (the legacy AOAI account remained credentialled with managed identity).
- **Why keep the env-var compatibility seam?** Code in five places (`apps/agents/maf_runtime/chat_client.py`, `apps/agents/common/llm_client.py`, `apps/api/app/services/simulation/controller_service.py`, plus two indirect readers) inspects `AZURE_OPENAI_ENDPOINT`. Pointing it at the Foundry endpoint costs zero at runtime and avoids a code-churn PR right before a cold redeploy. The cleanup PR is fast-follow, not gating.
- **Why retain the canary gate?** The same equivalence harness is the highest-confidence regression detector for corpus rebuilds (ADR-16 blue/green). Deleting it would force re-creating an equivalent gate later. Repurposing it costs nothing.
- **Why is the code default still `false`?** Test envs do not set `AZURE_AI_PROJECT_ENDPOINT`, so a `True` default would break thousands of unit tests that assume legacy behaviour. The Bicep-level activation in production is the authoritative source for the deployed-system default.

## Consequences

**Positive**
- Single, deterministic deploy state: every fresh `azd up` lands with Foundry as the chat plane and all five agents flagged on. No "is this env half-migrated?" question.
- ~600 lines of cutover-specific code paths become inert; identifiable for follow-on deletion.
- The legacy AOAI account is gone, eliminating a credential surface and a billing line.
- Audit records always carry `provider: foundry`; replay does not need to reason about the AOAI/Foundry discriminator.

**Negative / mitigations**
- Loss of in-place rollback to AOAI: a rollback now requires re-provisioning AOAI from a saved Bicep snapshot. Mitigated: production change-management already requires a 24h staging burn-in before prod redeploy; if Foundry behaves badly in staging the deploy never reaches prod.
- Cold reseed deletes any incident records created via the old deployment. Acceptable: pre-cutover, the deployment carried no production tenants.
- The `enableSpec036FoundryRag` Bicep flag is **not** flipped on by this ADR, because the AI Search + Service-Bus + ingest-runner stack requires Service Bus to be provisioned and a corpus index to be built end-to-end. That is tracked separately; this ADR scope is the *chat plane only*.

## Cross-references

- Supersedes ADR-16 §"alias-flip" semantics for the **migration** scenario; ADR-16 retained for index-version blue/green (corpus rebuilds).
- Spec 036 spec.md Session 6 — records the user pivot and the FR amendments.
- `infra/main.bicep:744-755` — `Microsoft.CognitiveServices/accounts` kind change (`OpenAI` → `AIServices`).
- `infra/main.bicep:825-836` and `:894-911` — container-app env-var rewiring.
- `apps/api/app/api/health.py` — health-check renames `openai` → `foundry`.
- `infra/bicep/modules/foundry-rag-cutover-alerts.bicep` — Alert 3 deactivation noted in module header.
- Cleanup follow-on tasks: see `specs/036-foundry-rag-grounding/HANDOFF.md` §"Hard-cutover follow-ups".
