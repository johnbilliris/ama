# Implementation Plan: In-Product Help Documentation & Grounded Chat Assistant

**Branch**: `feature/help` (spec dir `specs/038-help-docs-chat/`) | **Date**: 2026-05-11 | **Spec**: [`spec.md`](./spec.md)
**Input**: Feature specification from `specs/038-help-docs-chat/spec.md` (Pass 1 / Pass 2 / Pass 3 clarifications resolved)
**Status**: Draft (Phase 0 + Phase 1 complete; ready for `/speckit.tasks`)

---

## Summary

Spec 038 adds (a) a persona-aware in-product Help Centre under `apps/web/src/app/help/` with annotated screen-by-screen guides, glossary, search, and feedback; and (b) a grounded chat assistant exposed from a persistent global header affordance, served by a new FastAPI router `apps/api/app/api/routes/help_chat.py` that **reuses** the spec-036 retrieval + data-minimisation gateway stack (`apps/agents/common/retrieval_client.py`, `apps/agents/common/model_gateway.py`, `apps/agents/common/llm_client.py`, `apps/agents/common/foundry_chat_client.py`) plus the spec-036 carve-out registry, audit fields, and offline-cache pattern. No new model-plane technology is introduced; the chat is a **new Foundry agent** named `help_assistant` configured against a Help-only AI Search index alias `help-corpus-active`.

The Help corpus is a curated, dual-approved snapshot composed of: Help Articles (authored in repo as MDX under `apps/web/src/content/help/**` and indexed at build), the existing global corpora `docs/corpus/**` and `docs/aidr/**`, and the **Help-approved subset** of `specs/**` (Active/Implemented + reviewed). Each snapshot publishes an immutable AI Search index `help-corpus-{snapshot_id}`; the alias `help-corpus-active` is swung atomically to flip versions, satisfying the spec-029 5-minute reversibility SLO (FR-011c). Cosmos DB containers `help_articles`, `chat_sessions`, `chat_audit_log` (TTL 7 y), `snapshot_records`, `support_handoff_config`, `content_review_backlog`, `screenshot_registry` are added (all `/tenant_id` partitioned per existing convention; see `infra/bicep/modules/cosmos-*` precedents). Annotated screenshots (light + dark) live in an Azure Blob container `help-screenshots` behind a private endpoint with alt-text JSON sidecars. A build-time `tools/help/check_screenshot_freshness.py` computes `screen_id_hash` (FR-010a / FR-010a-AMEND) and a CI lint enforces glossary `lang`-attribute hygiene (FR-009a-AMEND).

Every constitutional non-negotiable is honoured: AU-only data plane (Australia East primary, Australia Southeast paired), tenant isolation by partition + filter at retrieval, append-only audit (Principle IV), graceful degradation with a 14-day / ≤500 MB shared cache (Non-Negotiable #5, mirrors spec-036 FR-RAG-LS-02), no silencing of safety-relevant guidance (Principle I — negative feedback queues, never auto-disables), and human-in-the-loop dual sign-off on every snapshot publish/rollback (Non-Negotiable #1, mirrors spec-005 FR-015).

---

## Technical Context

**Language/Version**: Python 3.13 (FastAPI router, ingest/snapshot tooling, freshness checker) on FastAPI + Pydantic v2; TypeScript 5.8 / React 19 / Next.js 16.2 (`apps/web`) for Help UI + chat panel; uv-managed virtualenvs.
**Primary Dependencies**: `azure-search-documents` (existing — Help-corpus index), `azure-ai-inference` (existing — Foundry chat client via `apps/agents/common/foundry_chat_client.py`), `azure-identity`, `azure-cosmos` (existing — new containers), `azure-storage-blob` (existing — `help-screenshots` container), `presidio-analyzer/anonymizer` (existing — reused from `model_gateway.py`), `next-mdx-remote` + `rehype/remark` plug-ins (NEW for Help authoring), `@axe-core/playwright` (existing — accessibility CI), `pa11y-ci` (NEW — author-time accessibility lint).
**Storage**: Azure AI Search Standard S1 (AU East, private endpoint — extends the spec-036 module) with new immutable indexes `help-corpus-{snapshot_id}` and alias `help-corpus-active`; Cosmos DB SQL API (AU East containers `help_articles`, `chat_sessions`, `snapshot_records`, `support_handoff_config`, `content_review_backlog`, `screenshot_registry` with default TTL aligned to FR-029, plus `chat_audit_log` with 7-year TTL); Azure Blob Storage (AU East — `help-screenshots/{tenant_id|global}/{screen_id}/{light|dark}.{webp|png}` + `.alt.json` sidecars, append-only versioning); Application Insights (AU East — chat SLO + WCAG e2e telemetry).
**Testing**: pytest with `pytest-asyncio` + `pytest-cov` (contract / integration in `tests/contract/help/`, `tests/integration/help/`); Playwright (`apps/web/__tests__/e2e/help/` with `@axe-core/playwright` for WCAG 2.2 AA gates and screen-reader announcements); `tests/llm-eval/help/` reusing the spec-030 LLM evaluation framework for grounded-answer / refusal / fabrication eval sets; `ruff`, `mypy --strict`, `eslint`, `bicep lint`, and `pa11y-ci` on every PR.
**Target Platform**: Azure AU East (prod) / AU Southeast (paired DR). Help UI on App Service (existing `web` service in `azure.yaml`); Help chat router on the existing `api` Container App; snapshot publisher reuses the existing `ingest-runner` / GitHub Actions pattern (no new compute).
**Project Type**: Multi-app monorepo (Next.js web + FastAPI api + Python agents + IaC); pnpm + uv per workspace.
**Performance Goals**: SC-007 — chat median time-to-first-useful-answer <5 s on a representative connectivity profile; chat token-stream first-byte <800 ms p95 (mirrors spec-036 retrieval p95 ≤300 ms guidance); snapshot alias flip <60 s (FR-011c); Help article render p95 <500 ms (cached); offline-cache lookup ≤50 ms (per spec-036 FR-RAG-LS-02 envelope).
**Constraints**: Constitution Principles I (no silencing of safety-relevant guidance), III (multi-hazard, multi-agency), IV (append-only auditable provenance), V/V-A/V-B/V-C (multilingual + accessible communications including embedded `lang` per FR-009a), VIII (Azure-only); Non-Negotiables #1 (human-in-the-loop on every snapshot publish + rollback), #2 (AU residency — chat never leaves AU; the Foundry §NN-2 model-hosting carve-out is **not** invoked for Help and `help_assistant` is pinned to AU regions in the carve-out registry, with `model_gateway` redaction still applied as a defence-in-depth measure), #3 (privacy by design — Presidio redaction at ingress), #5 (graceful degradation — Help cache + chat-disabled banner). WCAG 2.2 AA conformance (zero open Level A/AA issues at release).
**Scale/Scope**: ≥10 operational personas + 6 sector clusters with ≥1 landing page each (FR-002); ≥9 Help content domains (Help Content Domains §1–§9); ≥1 annotated screenshot per primary surface in light + dark (≥18 screen IDs at launch, growing); estimated ~250 Help articles + ~600 glossary terms at launch; ~20 active Help-approved spec snapshots/year (one per release plus out-of-cycle); per-tenant ~100 chat turns/day → ~36k turns/year/tenant in audit log retained for 7 years.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.* All gates currently **PASS**; no entries in Complexity Tracking.

The technical-persona traceability column records which `.github/agents/technical/*.agent.md` persona owned each gate decision (per the Persona Input Synthesis brief).

| Gate | Mandate | Plan compliance | Evidence | Persona owner |
|---|---|---|---|---|
| **Principle I — Primacy of life / no silencing** | No safety-relevant guidance may be silently withdrawn or auto-disabled. | FR-022a backlog never auto-disables; snapshot rollback shows deprecation notice (FR-011d / FR-011d-AMEND); stale screenshots get a banner with grace period (FR-010b). Chat refusal pattern always returns a handoff (FR-014, FR-023). | `data-model.md` §ContentReviewBacklogItem, §SnapshotRecord; `contracts/help-api.openapi.yaml` `/help/articles/{id}` (no DELETE without dual-approval flow); `research.md` §H. | **principal-engineer**, **product-owner-ba** |
| **Principle III — Resilience / multi-agency / graceful degradation** | Function continues at reduced capability when any single dependency is unavailable. | Help cache (≤500 MB / 14 d shared with spec-036 Field Coordinator cache), chat-disabled banner, AI Search alias allows zero-downtime cutover, snapshot rollback ≤5 min. | Non-Negotiable #5; FR-026 / FR-026a / FR-026b; `research.md` §F (Degraded mode), §C (Foundry agent). | **sre-engineer**, **chaos-engineer** |
| **Principle IV — Transparency & auditability** | Every action and decision logged with provenance. | Every chat turn writes a `ChatAuditEntry` (redacted prompt, retrieved citation IDs, response, refusal reason, persona, snapshot_id) with 7-year TTL; every snapshot publish/rollback emits `audit.snapshot_published` / `audit.snapshot_rollback`; transcript reconstruction emits `audit.transcript_reconstructed`. | `data-model.md` §ChatAuditEntry; FR-011c, FR-020, FR-029b. | **compliance-auditor**, **security-engineer** |
| **Principle V — Warning & public information / multilingual & accessible** | WCAG 2.2 AA + `lang` attribute hygiene + cultural-authority correctness. | WCAG 2.2 AA verified via axe-core in CI; `lang` enforced at authoring + build (FR-009a-AMEND); embedded glossary terms validated. PIO multilingual authoring guide is a Help domain (FR-024). Cultural-authority registry (`apps/agents/common/cultural_authority_registry.py`) consulted before publishing Help articles referencing Aboriginal & Torres Strait Islander language items. | `research.md` §G (Accessibility tooling); `contracts/help-ui.contract.ts.md` §A11y; `tests/contract/help/test_lang_attr_lint.py`. | **accessibility-tester**, **ux-designer** |
| **Non-Negotiable #1 — Human-in-the-loop** | No agent takes irreversible real-world action without explicit human authorisation. | Chat is read-only / advisory (FR-out-of-scope: chat-initiated state changes); all snapshot publish + rollback require dual sign-off (Help-content owner + safety/governance lead) recorded in `SnapshotRecord.approvers[]` (FR-011b). | spec.md Out-of-Scope; FR-011b; `data-model.md` §SnapshotRecord. | **principal-engineer**, **solution-architect** |
| **Non-Negotiable #2 — Australian data sovereignty** | Regulated platform data stays in AU. | All compute (api / web / ingest job), all data stores (Cosmos, Storage, AI Search, App Insights, Log Analytics, Key Vault), and the `help_assistant` Foundry deployment are pinned to AU East (DR AU Southeast). The §NN-2 carve-out is **not** invoked for Help; the carve-out registry entry for `help_assistant` records `region: australiaeast` and the data-minimisation gateway is still applied to redact PII before any retrieval/inference call (defence in depth). | `infra/parameters/foundry-carveout.yaml` (extended); FR-018; `research.md` §C. | **azure-principal-architect**, **security-engineer**, **compliance-auditor** |
| **Non-Negotiable #3 — Privacy by design (Privacy Act 1988)** | PII handling complies with APP. | Presidio-based redaction in `model_gateway.process()` runs on every chat input before retrieval/inference; user is notified when redaction occurs (FR-017); audit log stores **redacted** input only (FR-020); 7-year audit retention satisfies APP 11 (FR-029). | spec-036 `model_gateway.py` reuse; `data-model.md` §ChatAuditEntry; `research.md` §E. | **security-engineer**, **compliance-auditor** |
| **Non-Negotiable #4 — Interoperability** | APIs use standards. | New Help/chat APIs are OpenAPI 3.1, `application/json`, conventional error envelope shared with the api app, `Accept-Language` honoured, ETag on article reads. | `contracts/help-api.openapi.yaml`. | **api-architect** |
| **Non-Negotiable #5 — Graceful degradation** | See Principle III row. | — | — | **sre-engineer** |
| **Quality Gates** | PR linting + tests + IaC What-If; human review for public-facing outputs. | All tests added; `bicep what-if` on all infra PRs; snapshot publish IS the dual-approval gate for public-facing content. | `quickstart.md` §CI. | **infrastructure-devops**, **qa-test-engineer** |

Additional persona inputs reflected in the design (no separate gate, but binding):

- **software-developer**: Reuse-first — extend `apps/web/src/app/help/` (existing route segment) and `apps/api/app/api/routes/` (existing FastAPI surface); no new Python package or pnpm workspace member.
- **data-engineer**: Cosmos containers are partitioned by `/tenant_id` (matches `cosmos-simulation-containers.bicep` and spec-024 / spec-036 convention); snapshot ingest is idempotent on `(snapshot_id, source_id, content_hash)` tuple.
- **ai-ml-engineer**: `help_assistant` Foundry agent is configured with `temperature: 0.0`, `top_p: 0.1`, refusal system prompt, and strict tool list (retrieval only — no internet, no python, no code-interpreter). Embedding model reused from spec-036 (`foundry_query_embedder.py`).
- **docker-container-engineer**: No new image — Help chat router ships in the existing `apps/api` Dockerfile; snapshot publisher reuses the existing `ingest-runner` image with a new entrypoint flag `--mode help-snapshot`.
- **ux-designer**: Persistent global Help affordance (header `?` button + `Ctrl+/` shortcut) consistent with existing layout; light/dark theme tokens reused from `packages/ui`; persona switcher uses the spec-021 multi-role widget.
- **api-architect**: REST resource model `/help/articles`, `/help/chat/ask` (SSE), `/help/chat/feedback`, `/help/snapshots`, `/help/screenshots/staleness`, `/help/support-handoff` — all under `/api/v1/`, idempotent where feasible (PUT with ETag).
- **qa-test-engineer**: Three-tier test pyramid — pytest contract/integration; Playwright e2e w/ axe; spec-030 LLM-eval harness for grounded-answer / refusal / fabrication / cross-tenant-leak / PII-redaction suites; chaos drill (chaos-engineer-owned) for snapshot-rollback within 5 min.
- **chaos-engineer**: Quarterly chaos drill — kill AI Search index alias mid-publish, verify rollback completes within FR-011c 5-minute SLO and audit event emitted.
- **compliance-auditor**: Verifies APP 11 retention (7 y), tenant-isolation red-team, and AU residency attestation per release.
- **product-owner-ba**: Owns persona content backlog, dual-approval sign-off as Help-content owner, SC-009 baseline capture (SC-009-AMEND).

---

## Project Structure

### Documentation (this feature)

```text
specs/038-help-docs-chat/
├── plan.md                                # this file
├── research.md                            # Phase 0 — option analyses + chosen approach
├── data-model.md                          # Phase 1 — Pydantic v2 + TS twin entities, Cosmos partition keys, AI Search schema
├── quickstart.md                          # Phase 1 — local run, indexer seed, snapshot publish flow
├── contracts/
│   ├── help-api.openapi.yaml              # FastAPI surface (chat ask/feedback, snapshot publish/rollback, articles, screenshots staleness, search, handoff)
│   └── help-ui.contract.ts.md             # Help UI module-boundary contract (component props, route segments, telemetry events)
├── checklists/                            # (existing) speckit.checklist outputs
├── baselines/
│   └── pre-launch-support.md              # SC-009-AMEND pre-launch 2-week baseline (created prior to release)
└── tasks.md                               # produced by /speckit.tasks (NOT here)
```

### Source Code (repository root)

Concrete layout — **all paths are extensions of existing locations**; no new pnpm workspace members or Python packages are introduced.

```text
apps/web/                                  # existing Next.js 16.2 app
├── src/app/help/                          # EXTEND — existing route; add (help) route group surfaces below
│   ├── layout.tsx                         # NEW — persistent Help shell + persona switcher
│   ├── page.tsx                           # EXTEND — persona-aware landing
│   ├── search/page.tsx                    # NEW — full-text search
│   ├── chat/page.tsx                      # NEW — full-page chat (the global affordance opens a side panel that links here)
│   ├── glossary/[term]/page.tsx           # NEW
│   ├── articles/[slug]/page.tsx           # NEW — MDX render with annotated-screenshot component
│   └── playbooks/[id]/page.tsx            # NEW
├── src/components/help/                   # NEW — HelpAffordance, ChatPanel, CitationBadge, AnnotatedScreenshot, KeyboardSteps, StalenessBanner, FeedbackBar, PersonaTile, RefusalCard, DeprecationNotice
├── src/content/help/                      # NEW — MDX articles + glossary YAML (source of truth, indexed at build into AI Search)
│   ├── articles/**/*.mdx
│   ├── glossary/*.yaml
│   └── personas/<persona-id>/landing.mdx
├── src/lib/help/                          # NEW — telemetry hooks, deep-link parser, offline cache binding (extends idb)
└── __tests__/e2e/help/                    # NEW — Playwright + axe-core e2e suites

apps/api/                                  # existing FastAPI app
└── app/api/routes/
    ├── help_chat.py                       # NEW — POST /help/chat/ask (SSE), POST /help/chat/feedback, GET /help/chat/sessions/{id}
    ├── help_articles.py                   # NEW — articles CRUD (read-only public; write via snapshot pipeline)
    ├── help_snapshots.py                  # NEW — POST /help/snapshots/publish, POST /help/snapshots/{id}/rollback, GET listing
    ├── help_screenshots.py                # NEW — staleness flag list + clear, signed URL issuance
    ├── help_search.py                     # NEW — GET /help/search
    └── help_support_handoff.py            # NEW — per-tenant handoff config GET/PUT

apps/agents/                               # existing Python package
├── common/                                # REUSE (no edits required) — retrieval_client, model_gateway, llm_client, foundry_chat_client, citation_filter, audit, offline_cache
└── help_assistant/                        # NEW — Foundry agent definition + system prompt + refusal templates
    ├── __init__.py
    ├── agent.py                           # constructs the Foundry agent against `help-corpus-active` only
    ├── prompts/                           # NEW — system prompt, refusal, deprecation-notice templates
    └── eval_fixtures/                     # NEW — gold/refusal/out-of-scope sets consumed by tests/llm-eval/help/

apps/ingest-runner/                        # existing (spec-036) container-app job
└── src/help_snapshot/                     # NEW — entrypoint --mode help-snapshot: pulls Help articles + docs/aidr + docs/corpus + Help-approved specs, builds AI Search index, swings alias

packages/domain/src/ama_domain/            # EXTEND — add Pydantic v2 models
├── help_article.py
├── annotated_screenshot.py
├── glossary_term.py
├── persona_help_profile.py
├── knowledge_corpus_source.py
├── chat_session.py                        # extends Citation reuse from spec-036
├── help_feedback.py
├── staleness_flag.py
├── snapshot_record.py
├── support_handoff_record.py
├── content_review_backlog_item.py
└── chat_audit_entry.py

packages/domain/src/                        # EXTEND — TS twins (one .ts per Pydantic model)
└── help/*.ts

infra/bicep/modules/                       # NEW Bicep modules
├── cosmos-help-containers.bicep           # 7 containers, /tenant_id partition, TTL per container, autoscale RU
├── help-search-index-pair.bicep           # parameterised: stamps a new help-corpus-{snapshot_id} index + rebinds alias
├── help-screenshots-storage.bicep         # blob container w/ private endpoint, soft-delete, immutability policy
└── help-app-insights-dashboard.bicep      # SLO dashboard (chat first-byte, refusal rate, fabrication rate, snapshot-publish duration)

tools/help/                                # NEW — build-time + author-time tooling
├── check_screenshot_freshness.py          # FR-010a / FR-010a-AMEND
├── lint_lang_attributes.py                # FR-009a-AMEND
└── publish_snapshot.py                    # local one-shot mirror of CI pipeline for testing

tests/
├── contract/help/                         # NEW
├── integration/help/                      # NEW
└── llm-eval/help/                         # NEW — reuses spec-030 framework
```

**Structure Decision**: Web + API + Agent monorepo (the existing structure). Help is delivered as **extensions** of existing services and packages — no new app or workspace member. The only NEW deployable artefact is the Foundry `help_assistant` agent definition, which is a configuration object (not a service).

---

## Architecture (key cross-cutting decisions)

The full option analysis is in `research.md`; these are the locked-in summaries that downstream tasks must implement.

1. **(Help authoring/storage)** — MDX in repo at `apps/web/src/content/help/**` is the source of truth; build-time pipeline emits both (a) Next.js static routes and (b) AI Search documents. Cosmos `help_articles` stores **published metadata** only (title, persona tags, surface tags, snapshot_id, freshness flags); body lives in MDX + Search. (See research §A.) — *owners: software-developer, data-engineer*

2. **(Snapshot publication & versioning)** — Each publish stamps an immutable AI Search index `help-corpus-{snapshot_id}` and a `SnapshotRecord` (Cosmos); the `help-corpus-active` alias is swung atomically by the publisher. Rollback re-binds the alias to a prior `snapshot_id` — code-free, ≤5 min (FR-011c). Dual sign-off enforced in CI by CODEOWNERS-style gate over `apps/web/src/content/help/**` and `specs/**` snapshot manifest. (See research §B.) — *owners: principal-engineer, infrastructure-devops*

3. **(Chat grounding pipeline)** — A single Foundry agent `help_assistant` (one per environment) configured with: tools = retrieval-only against alias `help-corpus-active`; reuses `apps/agents/common/retrieval_client.AzureSearchRetrievalService` (FR-RAG-AG-01 protocol); reuses `apps/agents/common/model_gateway.process()` for PII redaction and PSPF DENY before retrieval; reuses `apps/agents/common/llm_client` + `foundry_chat_client` for inference; emits citations via the spec-036 `citation_filter`. Streaming via SSE on `POST /help/chat/ask`. (See research §C.) — *owners: ai-ml-engineer, principal-engineer*

4. **(Screenshot capture/storage/staleness detection)** — Authors capture light + dark variants via a Playwright-based capture script (`tools/help/capture_screenshots.ts`) that computes `screen_id_hash = sha256(route_id + ordered DOM-fingerprint of numbered callout anchors)` and writes the manifest. Storage: `help-screenshots` blob container (private endpoint, immutability policy 30 d, soft-delete 90 d). Build-time `tools/help/check_screenshot_freshness.py` recomputes the hash from the live build and raises `StalenessFlag` rows on mismatch; route-rename detected via `previous_route_id` registry (FR-010a-AMEND) triggers bulk re-baseline. (See research §D.) — *owners: ux-designer, software-developer, qa-test-engineer*

5. **(PII redaction)** — Reuses `apps/agents/common/model_gateway.py` from spec-036 unchanged; the Help chat router calls `gateway.process(input, region="australiaeast")` and returns `redaction_notice` to the user when fields are masked (FR-017). No new Presidio configuration; the existing AU-mobile / email / person-name / credit-card recognisers cover the surface. (See research §E.) — *owners: security-engineer, ai-ml-engineer*

6. **(Degraded-mode caching)** — Reuses `apps/agents/common/offline_cache.py` envelope (≤500 MB / 14-day TTL) shared with the Field Coordinator cache (FR-026b). Help client uses `idb` (already in `apps/web/package.json`) to mirror previously-viewed articles + full glossary + curated FAQ (FR-026a). Chat panel hides behind the standard "unavailable in degraded mode" message (FR-026a-AMEND). Audit-logged refresh on reconnect. (See research §F.) — *owners: sre-engineer, software-developer*

7. **(Accessibility tooling)** — Three gates: (1) authoring-time `lang`-attribute validation via the MDX rehype plug-in (refuses save if a glossary-tagged non-English fragment is missing `lang`); (2) build-time `tools/help/lint_lang_attributes.py` on published articles; (3) CI Playwright + `@axe-core/playwright` runs on every Help route covering keyboard navigation, focus indicators, screen-reader announcements, and contrast. Cultural-authority registry consulted before any publish referencing Aboriginal & Torres Strait Islander language items. (See research §G.) — *owners: accessibility-tester, ux-designer*

---

## Risk

| # | Risk | Likelihood × Impact | Mitigation |
|---|---|---|---|
| R1 | Snapshot alias swing causes momentary 0-result window for in-flight retrieval. | L × M | Publisher pre-warms new index, swings alias only after `health_query` returns ≥1 doc; SDK retries handle ≤1 s window. |
| R2 | Foundry agent fabricates despite refusal prompt. | M × H | `citation_filter` rejects any answer with zero retrieved chunks (existing spec-036 behaviour); SC-003 sampled audit; LLM-eval suite blocks merge on regression. |
| R3 | Cross-tenant retrieval leak via mis-scoped query. | L × H | AI Search filter `tenant_id eq @tenant or scope eq 'global'` baked into `retrieval_client` query layer; red-team test in `tests/integration/help/test_tenant_isolation.py`; chaos-engineer drill. |
| R4 | PII slips past redaction (novel pattern). | M × M | Audit log stores **redacted** input; quarterly recogniser-set review by security-engineer; user-visible "redaction occurred" banner deters PII pasting. |
| R5 | Stale screenshots during high-velocity UI churn. | H × M | Bulk re-baseline workflow on route rename (FR-010a-AMEND); banner shown immediately; one-release grace period; SC-012 (90% within one cycle) tracked in App Insights. |
| R6 | Snapshot rollback exceeds 5 min SLO under load. | L × H | Alias swing is config-only (≤5 s typical); chaos drill quarterly verifies the SLO; on breach, runbook escalates to SRE on-call. |
| R7 | Negative-feedback brigading falsely flags safe content. | L × M | FR-022a queues for **human review** only — never auto-disables; pattern identity uses `(intent_cluster, citation_set)` tuple (FR-022a-AMEND) so single-source brigading on one article cannot silence others. |
| R8 | Help cache exceeds 500 MB envelope. | M × M | LRU eviction inside `offline_cache.py` envelope; per-device telemetry; alert at 80% of cap. |

---

## Testing strategy

Three-tier pyramid + dedicated LLM evaluation, mapped to acceptance scenarios and SCs.

### Tier 1 — Contract tests (pytest) — `tests/contract/help/`

- `test_help_api_openapi.py` — schema-validate every response in `contracts/help-api.openapi.yaml`.
- `test_chat_audit_schema.py` — every `ChatAuditEntry` round-trips through the Pydantic model.
- `test_snapshot_record_dual_approval.py` — publish endpoint rejects payloads without two distinct approver identities (FR-011b).
- `test_lang_attr_lint.py` — `tools/help/lint_lang_attributes.py` on a fixture corpus passes for valid content, fails for missing `lang` (FR-009a-AMEND).
- `test_screen_id_hash.py` — `screen_id_hash` is deterministic across platforms (FR-010a).
- `test_retrieval_filters_tenant.py` — filter clause is always present (R3 guard).

### Tier 2 — Integration tests (pytest) — `tests/integration/help/`

- `test_chat_end_to_end.py` — POST /help/chat/ask returns SSE stream with at least one citation; refusal path emits `audit.chat_refusal`.
- `test_snapshot_publish_rollback.py` — publish stamps new index, alias swings, rollback re-binds within 5 min budget (chaos-engineer-owned).
- `test_pii_redaction_notice.py` — input with AU mobile is redacted; user notice rendered; audit log carries redacted form only (FR-017 / FR-020).
- `test_tenant_isolation.py` — queries scoped to tenant A never return tenant B docs (R3 / SC-004).
- `test_degraded_mode.py` — service-worker cache returns articles offline; chat is disabled with banner (FR-026 / FR-026a-AMEND).
- `test_support_handoff_sla.py` — NEMA-Level-3 banner triggers incident-mode channel; SLA breach emits `audit.support_handoff_unack_timeout` (FR-023a-AMEND / FR-023b).

### Tier 3 — End-to-end (Playwright + axe-core) — `apps/web/__tests__/e2e/help/`

- `landing.persona.spec.ts` — every persona's landing tile loads with first-15-minutes tour (FR-002, US-1).
- `screenshot.theme.spec.ts` — light/dark variants swap with theme; alt text + adjacent keyboard steps present (FR-007 / FR-008, US-3).
- `chat.citations.spec.ts` — every chat answer renders ≥1 citation badge that deep-links to article anchor (FR-012, US-2).
- `a11y.wcag22aa.spec.ts` — axe-core runs on every Help route; zero Level A/AA violations (SC-006, US-3).
- `keyboard.only.spec.ts` — full Help + chat operable via keyboard (FR-009).
- `degraded.offline.spec.ts` — offline-first cache + chat-disabled banner (FR-026, US-1 edge case).

### Tier 4 — LLM evaluation (spec-030 framework) — `tests/llm-eval/help/`

- `eval_grounded_answers.jsonl` — ≥200 in-scope Q/A; gate ≥90% pass with ≥1 valid citation (SC-002).
- `eval_refusals.jsonl` — out-of-scope set (weather, legal/medical, cross-tenant); gate 100% refused (SC-002).
- `eval_fabrication_audit.py` — sampled-audit script over chat audit log; SC-003 fail-closed at any verified fabrication.
- `eval_persona_tailoring.jsonl` — persona-tagged Q/A; gate that responses cite persona-relevant articles.

### Telemetry & Observability (sre-engineer-owned)

App Insights workbook `help-slis` tracks: chat first-byte p95, refusal rate, fabrication-audit hit rate, snapshot publish duration, snapshot rollback duration, screenshot staleness backlog age, support handoff acknowledgement latency. Alerts at SC thresholds; on-call runbook in `docs/runbooks/help.md` (created in Phase 2).

---

## Complexity Tracking

> **Empty — no Constitution Check violations.**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| *(none)* | — | — |
