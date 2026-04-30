# Phase 0 — Research: AMA Rubric Improvements

This document resolves all NEEDS-CLARIFICATION items and records research-backed decisions for technologies introduced or changed by this feature. All decisions follow Azure-only, AVM-first, AU-residency, and constitutional constraints.

## R-01 — Circuit-breaker library replacement (FR-P03)

- **Decision**: Adopt `pybreaker` (synchronous + async-friendly) and wrap it behind the existing `apps.agents.common.resilience.CircuitBreaker` Protocol so call-sites are unchanged.
- **Rationale**: Mature (in PyPI > 8 years), small surface, supports state-change listeners (needed for the App Insights `circuitbreaker.state` customMetric), threshold + reset-timeout primitives match current behaviour.
- **Alternatives considered**:
  - `tenacity` — retry-only, no half-open state; rejected.
  - `aiobreaker` — async-only, niche; rejected.
  - Continue rolling our own — rubric explicitly cites this as a debt; rejected.
- **ADR**: ADR-034 to be authored in Stream 0.

## R-02 — OpenTelemetry distribution (FR-O07)

- **Decision**: Adopt **Azure Monitor OpenTelemetry Distro for Python** (`azure-monitor-opentelemetry`) with OTLP/HTTP exporter into Application Insights.
- **Rationale**: First-party Microsoft package; zero-config auto-instrumentation for FastAPI, httpx, aiohttp, requests, Azure SDKs; supports OTel customMetric path (FR-O03) without separate App Insights SDK.
- **Alternatives considered**:
  - OpenCensus (deprecated by Microsoft).
  - Bare `opentelemetry-distro` + manual Azure exporter — more wiring; rejected.
- **Trace attribute schema**: see [contracts/otel-attributes.yaml](./contracts/otel-attributes.yaml).

## R-03 — Azure AI Search SKU + index design (FR-AI01)

- **Decision**: `Standard S1` Australia East for prod, `Basic` for dev/staging. Single index `aidr-handbooks` with hybrid (BM25 + vector) profile. Vector dim 1536; embeddings via Azure OpenAI `text-embedding-3-large`. Chunking: 800-token overlap-200; metadata fields {handbook_id, chapter, page, version, language}.
- **Rationale**: AIDR corpus is ≈ 50 handbooks (≤ 200 MB after chunking); S1 supports up to 25 GB index, plenty of headroom; hybrid retrieval outperforms pure vector for emergency-management terminology.
- **Alternatives considered**:
  - Cosmos DB Vector — currently preview in Australia East; rejected for prod readiness.
  - Azure OpenAI on-your-data — black-box retrieval; rubric requires citing handbook + page in recommendation card, requires our own retrieval; rejected for prod.
- **Cost guard-rail**: AVM autoscale alert at 70% of S1 search-units per hour.

## R-04 — OIDC migration sequencing (FR-S02)

- **Decision**: Two-stage. Stage 1 = land spec 031 with `AZURE_CREDENTIALS` JSON exactly as ADR-031 documents; achieve 7 days of green CD on staging + production. Stage 2 = ADR-032 supersedes ADR-031, re-introduces OIDC federated workload identity using the simplified pipeline shape (no spec-029 complexity), per-environment rollout `dev → staging → prod` with 7-day soak between each.
- **Rationale**: Resolves spec clarification Pass-1 Q1 (FR-S02 vs ADR-031 conflict). Avoids reverting the simplification gain; preserves a defensible audit trail per Constitution IV.
- **Alternatives considered**:
  - Skip OIDC entirely (accept long-lived secret) — rubric calls this out as a P1 security regression; rejected.
  - Migrate now in parallel with spec-031 — high risk of overlapping pipeline rewrites; rejected.

## R-05 — Cosign signing model (FR-AI09)

- **Decision**: Sigstore `cosign` keyless signing using GitHub OIDC identity tokens (Fulcio). Verify in `cd.yml` against the expected GitHub Actions identity (`https://github.com/<org>/ama` with `repository_owner` claim) before deploying any prompt artifact. No long-lived signing keys.
- **Rationale**: Aligns with Stage 2 OIDC direction (no key management drift). Standard Sigstore pattern; tooling pinned by SHA.
- **Alternatives considered**:
  - GPG with rotated keys — operational toil; rejected.
  - In-repo cosign.pub — works but introduces a new long-lived secret; rejected.

## R-06 — Customer-managed keys (CMK) (FR-S05)

- **Decision**: HSM-backed CMK in Key Vault Premium (existing module pattern in `infra/modules/log-analytics-key.bicep`). Apply to Cosmos DB account-level encryption + Storage account encryption + Application Insights workspace. Rotation: Azure Policy `Audit usage of CMKs` + 90-day rotation policy.
- **Rationale**: Matches Australian PSPF + Essential Eight Maturity Level 2 expectations from Commonwealth tenants (NEMA, ABF, ADF). Reuses an established pattern.
- **Alternatives considered**:
  - Microsoft-managed keys only — works but rubric calls out CMK gap explicitly; rejected.

## R-07 — Phi shadow path boundary (FR-AI03)

- **Decision**: Inputs are PII-minimised at the model gateway (existing `apps/agents/common/safety/redaction.py`); requests routed via the Foundry Phi deployment (subject to constitution carve-out documentation); outputs land in the AU-resident audit/eval store (Cosmos `recommendations` container) with `shadow=true`, `model_id=phi-3.5-mini`, `parent_recommendation_id=<prod_id>`. Operator UI filters out `shadow=true`. 7-year retention.
- **Rationale**: Preserves Constitution Non-Negotiable #2 (no regulated data persisted outside AU; egress only via the gateway with minimisation; nothing user-facing depends on Phi).
- **ADR**: ADR-033 in Stream 0.

## R-08 — Web testing tier (FR-T02)

- **Decision**: **Vitest** + React Testing Library, configured against the Next.js 16.2 / React 19 stack. Tests live under `apps/web/__tests__/` mirroring source layout.
- **Rationale**: Vitest is Vite-native (Next.js 16 ships Turbopack but Vitest+SWC is still the fastest config), 2-3× faster than Jest, ESM-first.
- **Alternatives considered**:
  - Jest — slower; ESM friction with React 19; rejected.
  - Cypress component tests — overlaps Playwright; rejected.

## R-09 — Coverage tooling (FR-T01)

- **Decision**: `pytest-cov` with `--cov-fail-under=80` for `tests/unit`, `--cov-fail-under=60` for `tests/integration`, `--cov-fail-under=50` for `tests/contract`. Reports posted to PRs via `5monkeys/cobertura-action` (SHA-pinned) using Cobertura XML output.
- **Rationale**: Native pytest integration; thresholds enforceable per-tier; existing memory note confirms `pytest tests/unit tests/integration tests/contract` is the canonical CI test-set.

## R-10 — Synthetic monitoring (FR-O10)

- **Decision**: Application Insights **availability tests** (multi-step web tests) covering `/api/health`, `/api/docs`, the public dashboard URL, the governance hub. Five locations: Sydney (AU), Melbourne (AU), Auckland (NZ), Singapore, Tokyo. Frequency 5 minutes; failure threshold 3/5 locations failing for 10 minutes.
- **Rationale**: APAC-focused locations match user base; multi-step tests can verify auth + critical journey rather than just 200 OK.
- **Alternatives considered**:
  - Azure Monitor URL ping — single endpoint; rejected.
  - Third-party (Datadog Synthetics, Pingdom) — non-Azure; rejected.

## R-11 — Cosmos backup/restore + paired region (FR-D04)

- **Decision**: Enable **Continuous (7-day) backup mode** + **point-in-time restore** on the Cosmos account in `infra/main.bicep`. Paired region for failover = Australia Southeast. Connection-string-aware client supports paired-region read for the dashboard.
- **Rationale**: Continuous backup mode is the only mode that supports PITR at item granularity; matches RPO ≤ 15 min target.
- **Alternatives considered**:
  - Periodic backup (4-hour interval) — exceeds RPO; rejected.

## R-12 — Cosmos partitioning math (FR-A02)

- **Decision**: Document per-tenant RU budget breakdown in `docs/architecture/cosmos-partitioning.md`. Headroom margin 30%. Partitioning strategy retained: `/tenant_id` for tenant-scoped containers, `/incident_id` for incident-scoped (audit, recommendations, timeline). Autoscale max-RU caps per container set in `main.bicep` (FR-R04).
- **Rationale**: Closes rubric item 1.2 (math currently asserted but not quantified). Caps prevent runaway billing.

## R-13 — Defender for Cloud + Sentinel (FR-S04)

- **Decision**: Defender for Cloud Standard tier on AKS/Container Apps/Cosmos/Storage/Key Vault/Container Registry/AI services; Microsoft Sentinel deployed onto the existing Log Analytics workspace; Bicep-driven analytics rules: `IdentityRiskHighSignIn`, `KeyVaultAnomalousAccess`, `CosmosFirewallChange`, `BicepDriftDetected`, `CosmosCMKRotationOverdue`. Action group routes Sentinel high-severity to PagerDuty webhook + email.
- **Rationale**: Single SIEM; reuses existing workspace; minimal new modules.

## R-14 — Chaos Studio experiment design (FR-R05, FR-T03)

- **Decision**: Quarterly Chaos Studio gameday targeting (a) Container App restart on the monitoring agent, (b) Cosmos throttling on the audit container, (c) AOAI region failure simulated by network drop, (d) Service Bus dead-letter inundation. Experiments pinned to staging only. Results posted to App Insights + GitHub issue.
- **Rationale**: Targets actual rubric-mentioned resilience seams. Staging-only protects production.

## R-15 — DORA metrics sourcing (FR-C04)

- **Decision**: Deployment Frequency + Lead Time = GitHub `workflow_run` API; Change Failure Rate + MTTR = GitHub Issues with `incident` label correlated to deployments. Daily aggregator GitHub Action posts to App Insights customMetrics; visualised in a dedicated Workbook.
- **Rationale**: Source data already exists; no new system needed.

## R-16 — Pre-commit + CONTRIBUTING set-up (FR-Q04, FR-DOC04)

- **Decision**: `.pre-commit-config.yaml` with hooks: `pre-commit-hooks` (whitespace, EOF), `ruff` (lint + format), `mypy`, `import-linter`, `gitleaks` (secret scan), `bicep-lint`. CONTRIBUTING.md covers branch conventions (env-branches per spec 031), spec-driven workflow (the 9-step process in this very work), and code-review etiquette.
- **Rationale**: Mirrors CI gates; reduces "fixed in CI" cycles.

## R-17 — Loom walkthrough hosting (FR-DOC01)

- **Decision**: Record a 60-second Loom video; link from README. If Loom unavailable due to org policy, fall back to a hosted MP4 in Azure Storage `walkthroughs` container with public-read SAS rotation policy.
- **Rationale**: Leightweight; no new persistent infra.

## R-18 — Redoc hosting in Next.js (FR-DOC02)

- **Decision**: New Next.js route `apps/web/src/app/api-docs/page.tsx` mounts `redoc-react` (SHA-pinned npm) reading `apps/api/openapi.yaml` from the build artifact. Auth-free read.
- **Rationale**: Same domain as web app; no separate hosting.

## R-19 — Governance hub consolidation (FR-DOC03)

- **Decision**: Create `docs/governance-hub/index.md` with redirects/symlinks pointing into the existing `docs/llm-evaluation/`, `docs/disaster-response-hub/evaluation/`, and `governance-dashboard.md`. Top nav of the web app gets a single "Governance" entry pointing here.
- **Rationale**: Avoid breaking existing internal links; lightweight unification.

## R-20 — Container Apps base image pinning (FR-D02)

- **Decision**: All Dockerfiles pin to a specific digest (`python:3.12.5-slim-bookworm@sha256:...`); Dependabot watches Dockerfiles + GitHub Actions; weekly PRs.
- **Rationale**: Eliminates `latest` tag drift while keeping patching automated.

---

All NEEDS-CLARIFICATION resolved. Phase 1 (data-model, contracts, quickstart) proceeds.
