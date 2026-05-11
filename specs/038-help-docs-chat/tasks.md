---
description: "Actionable, dependency-ordered task list for spec-038 In-Product Help Documentation & Grounded Chat Assistant"
---

# Tasks: In-Product Help Documentation & Grounded Chat Assistant

**Branch**: `feature/help` | **Spec dir**: [`specs/038-help-docs-chat/`](./) | **Date**: 2026-05-11
**Inputs**: [`spec.md`](./spec.md) (FR-001 … FR-029b + 9 *-AMEND clauses; SC-001 … SC-012 + SC-009-AMEND), [`plan.md`](./plan.md), [`research.md`](./research.md), [`data-model.md`](./data-model.md), [`contracts/help-api.openapi.yaml`](./contracts/help-api.openapi.yaml), [`contracts/help-ui.contract.ts.md`](./contracts/help-ui.contract.ts.md), [`quickstart.md`](./quickstart.md), [`checklists/feature.md`](./checklists/feature.md) (CHK001-CHK136).

## Format & Conventions

`- [ ] T-AAxxx [P?] [Gate?] Description (file path) — FR/CHK refs`

- **Numbering**: `T-AA001…` — `AA` prefix avoids collision with prior specs.
- **[P]** parallelisable with sibling tasks (different files, no shared in-flight state).
- **[Gate]** release-blocking (cannot ship without it; mirrors checklist [Gate] entries).
- Every task lists exact paths, expected outcome, and verification step.
- Cross-references to FR(s) and CHK item(s) appear at end of the task line.

## Phase Map (and dependencies)

| Phase | Title | Depends on | # tasks |
|---|---|---|---|
| 0 | Setup (workspace, deps, scaffolding) | — | T-AA001 – T-AA012 |
| 1 | Infrastructure (Bicep, Foundry agent, indexes) | Phase 0 | T-AA013 – T-AA030 |
| 2 | Domain models (13 entities + TS twins) | Phase 0 | T-AA031 – T-AA052 |
| 3 | Backend (FastAPI routes, services, agent wiring) | Phases 1, 2 | T-AA053 – T-AA092 |
| 4 | Frontend (Next.js Help routes + components) | Phases 2, 3 | T-AA093 – T-AA127 |
| 5 | Help content authoring (articles, screenshots, glossary, playbooks) | Phase 4 | T-AA128 – T-AA163 |
| 7 | Build-time tooling (freshness, lang lint, link check) | Phases 0, 4 | T-AA174 – T-AA181 |
| 6 | Snapshot publication pipeline (CI + CODEOWNERS) | Phases 1, 3, 5, 7 | T-AA164 – T-AA173 |
| 8 | Tests (pytest, Playwright, LLM-eval, a11y) | Phases 3, 4, 5 | T-AA182 – T-AA208 |
| 9 | Operational readiness (runbooks, dashboards, baseline) | Phases 1, 6, 8 | T-AA209 – T-AA218 |
| 10 | Final integration & sign-off | All | T-AA219 – T-AA226 |

> **Phase ordering note**: Phase 6 (snapshot publication) depends on Phase 7 (build-time tooling) because the publisher invokes `tools/help/check_screenshot_freshness.py` and `tools/help/lint_lang_attributes.py`. Therefore the linear order after Phase 5 is **5 → 7 → 6 → 8**, not "6 and 7 in parallel". Phase numbers are kept for traceability with `checklists/feature.md` references.

---

## Phase 0 — Setup (workspace, dependencies, scaffolding)

**Depends on**: nothing. **Goal**: a developer can `pnpm install && uv sync && pnpm --filter @ama/domain build` cleanly and the new directories exist for downstream tasks.

- [ ] T-AA001 [Gate] Create skeleton directory tree with `.gitkeep` placeholders: `apps/web/src/app/help/{search,chat,glossary,articles,playbooks}`, `apps/web/src/components/help/`, `apps/web/src/content/help/{articles,glossary,personas}`, `apps/web/src/lib/help/`, `apps/web/__tests__/e2e/help/`, `apps/api/app/api/routes/`, `apps/agents/help_assistant/{prompts,eval_fixtures}`, `apps/ingest-runner/src/help_snapshot/`, `packages/domain/src/ama_domain/` (existing), `packages/domain/src/help/`, `infra/bicep/modules/`, `tools/help/`, `tests/contract/help/`, `tests/integration/help/`, `tests/llm-eval/help/`, `docs/runbooks/help/`, `specs/038-help-docs-chat/baselines/`. Verify: `git status` shows new tracked dirs. — FR-001…029, all CHK
- [ ] T-AA002 [P] Add Python deps in `pyproject.toml` (workspace root) — pin `next-mdx-remote-helpers` (build only), confirm `azure-search-documents`, `azure-cosmos`, `azure-storage-blob`, `azure-identity`, `azure-ai-inference`, `presidio-analyzer`, `presidio-anonymizer`, `pytest-asyncio`, `pytest-cov`, `httpx`, `respx`, `python-ulid` are present at expected versions; run `uv sync` and commit `uv.lock`. Verify: `uv run python -c "import azure.search.documents, presidio_analyzer"` exits 0. — plan §Technical Context
- [ ] T-AA003 [P] Add JS deps in `apps/web/package.json` — `next-mdx-remote`, `rehype-slug`, `rehype-autolink-headings`, `remark-gfm`, `idb`, `@axe-core/playwright`, dev: `pa11y-ci`, `vitest-axe`. Run `pnpm install`. Verify: `pnpm --filter @ama/web ls next-mdx-remote` lists package. — plan §Technical Context
- [ ] T-AA004 [P] Configure ruff + mypy strict for new modules — extend `ruff.toml` to include `apps/api/app/api/routes/help_*.py`, `apps/agents/help_assistant/`, `apps/ingest-runner/src/help_snapshot/`, `tools/help/`, `tests/contract/help/`, `tests/integration/help/`; add `[tool.mypy]` overrides for the same. Verify: `uv run ruff check tools/help apps/agents/help_assistant` succeeds on empty modules.
- [ ] T-AA005 [P] Add `pa11y-ci` config `apps/web/.pa11yci.json` with WCAG 2.2 AA standard, `chrome-launcher` headless, representative URL list (`/help`, `/help/articles/getting-started`, `/help/chat`, `/help/glossary/aiims-controller`, `/help/search?q=evacuation`). Verify: `pnpm exec pa11y-ci --config apps/web/.pa11yci.json --dry-run` exits 0.
- [ ] T-AA006 [P] Add Playwright config addition `apps/web/playwright.config.ts` for the new `help` project (testDir `__tests__/e2e/help`, axe-core fixture). Verify: `pnpm --filter @ama/web exec playwright test --list __tests__/e2e/help` shows 0 tests (empty directory) without error.
- [ ] T-AA007 [P] Wire MDX rehype plug-in stub `tools/help/rehype-lang-attr.ts` exporting a no-op visitor; register in `apps/web/next.config.mjs` `mdxOptions.rehypePlugins`. Verify: `pnpm --filter @ama/web build` succeeds with stub in place. — FR-009a-AMEND
- [ ] T-AA008 [P] Add CODEOWNERS-style scaffolding: append rules to repository `.github/CODEOWNERS` requiring `@ama/help-content-owners` AND `@ama/safety-or-governance-leads` on `apps/web/src/content/help/**`, `specs/038-help-docs-chat/**`, and `apps/ingest-runner/manifests/help-snapshot.yaml`. Verify: `gh codeowners /apps/web/src/content/help/articles/foo.mdx` lists both teams. — FR-011b
- [ ] T-AA009 [P] Create `apps/ingest-runner/manifests/help-snapshot.yaml` initial manifest skeleton listing the four corpus globs (`apps/web/src/content/help/**`, `docs/aidr/**`, `docs/corpus/**`, `specs/**` filtered to Active|Implemented). Verify: `python -c "import yaml; yaml.safe_load(open('apps/ingest-runner/manifests/help-snapshot.yaml'))"` parses. — FR-011, FR-011a
- [ ] T-AA010 [P] Add `azure.yaml` service entry note: confirm Help is shipped in existing `web` and `api` services (no new service). Verify by inspection: no diff to `azure.yaml.services` keys.
- [ ] T-AA011 [P] Create `specs/038-help-docs-chat/baselines/.gitkeep` with a README pointing forward to T-AA213 (SC-009-AMEND baseline capture). — SC-009-AMEND
- [ ] T-AA012 [P] [Gate] Add a `package.json` script `pnpm test:help` in repo root that runs the Phase-8 suite end-to-end (placeholder calls); ensure CI workflow `.github/workflows/ci.yml` will invoke it once implemented. Verify: `pnpm test:help --help` resolves.

**Checkpoint**: scaffolding ready; all subsequent phases can branch off.

---

## Phase 1 — Infrastructure (Bicep modules, Foundry agent, AI Search index alias)

**Depends on**: Phase 0. **Goal**: `azd provision` against `australiaeast` creates all new Cosmos containers, AI Search index pair (alias bound to bootstrap), Storage container, App Insights workbook, Foundry agent definition, role assignments. AVM-first; CAF naming; AU-only region.

- [ ] T-AA013 [Gate] Author `infra/bicep/modules/cosmos-help-containers.bicep` — 7 containers (`help_articles`, `screenshot_registry`, `chat_sessions` TTL 30 d, `chat_audit_log` TTL 7 y, `snapshot_records`, `support_handoff_config`, `content_review_backlog` TTL 7 y), `/tenant_id` partition, autoscale 400-4000 RU, composite indexes per data-model.md §Bicep mapping. Use AVM `br/public:avm/res/document-db/database-account` extension pattern. Verify: `bicep build` clean; `az deployment group what-if` shows 7 new containers. — FR-029, FR-022a, FR-020, CHK091…CHK096, CHK117
- [ ] T-AA014 [Gate] Author `infra/bicep/modules/help-search-index-pair.bicep` — parameterised module that stamps `help-corpus-{snapshotId}` immutable index (schema per data-model.md §AI Search) and (re)binds alias `help-corpus-active`; private endpoint reused from spec-036 search service. Verify: `bicep lint` clean. — FR-011a, FR-011c, CHK064, CHK068
- [ ] T-AA015 [Gate] Author `infra/bicep/modules/help-screenshots-storage.bicep` — Blob container `help-screenshots`, private endpoint, immutability policy 30 d, soft-delete 90 d, customer-managed key reuse. Verify: `bicep what-if` shows new container under existing storage account. — FR-006, FR-007, CHK053
- [ ] T-AA016 [P] [Gate] Author `infra/bicep/modules/help-app-insights-dashboard.bicep` — App Insights workbook `help-slis` with charts: chat first-byte p95, refusal rate, fabrication-audit hit, snapshot publish duration, snapshot rollback duration, screenshot staleness backlog age, support-handoff acknowledgement latency. Verify: `bicep build` clean. — SC-007, SC-002, SC-003, SC-012, FR-023b
- [ ] T-AA017 [Gate] Wire all four new modules into `infra/main.bicep` (add `module helpCosmos`, `helpSearch`, `helpScreenshotsStorage`, `helpDashboard`). Pass tags (env, owner, costCentre) per `azure-defaults` skill. Verify: `az deployment sub what-if --location australiaeast --template-file infra/main.bicep --parameters infra/main.parameters.dev.json` succeeds. — plan §Project Structure, CHK104
- [ ] T-AA018 [P] [Gate] Add Foundry agent definition `infra/parameters/foundry-agents/help_assistant.yaml` — name `help_assistant`, region `australiaeast`, tools=[retrieval against alias `help-corpus-active`], temperature 0.0, top_p 0.1, max_output_tokens 1500, system prompt path `apps/agents/help_assistant/prompts/system.md`. Verify: schema validation against existing `foundry-agents` JSON schema passes. — FR-018, FR-011, CHK068, CHK105
- [ ] T-AA019 [P] [Gate] Extend `infra/parameters/foundry-carveout.yaml` with entry `help_assistant: { region: australiaeast, carveout: false, redaction: required }` — record that the §NN-2 carve-out is NOT invoked. Verify: `python tools/validate_carveout_registry.py` (existing) passes. — Constitution NN-2, FR-018, plan §Constitution Check, CHK128
- [ ] T-AA020 [P] Add managed-identity role assignment Bicep: `apps/api` SystemAssigned identity gets `Cosmos DB Built-in Data Contributor` on the 7 new containers (insert-only on `chat_audit_log` + `snapshot_records` enforced via custom RBAC role). Verify: `az role assignment list` post-provision shows the assignments. — FR-020, plan §data-model.md
- [ ] T-AA021 [P] Add Storage `Storage Blob Data Reader` role for the `web` SystemAssigned identity on `help-screenshots`; `Storage Blob Data Contributor` for `ingest-runner`. Verify: post-provision check.
- [ ] T-AA022 [P] Diagnostics settings: route Cosmos, AI Search, Storage, App Insights logs to the existing AU-East Log Analytics workspace; retention 30 d hot / 7 y archive. Verify: `az monitor diagnostic-settings list` shows entries. — FR-018, CHK105
- [ ] T-AA023 [P] Alerts: App Insights metric alerts for chat first-byte p95 > 800 ms (warn) / > 5 s (critical, SC-007); snapshot publish duration > 60 s; staleness backlog > 90 days; support-handoff SLA breach event count > 0. Verify: `az monitor metrics alert list` shows new alerts. — SC-007, FR-023b, FR-011c, CHK129
- [ ] T-AA024 [P] Update `infra/main.parameters.dev.json` and `infra/main.parameters.prod.json` with help-specific parameters (containerThroughputMin, immutabilityDays, etc.). Verify: `bicep what-if` against both succeeds.
- [ ] T-AA025 [P] Add `ps-rule.yaml` exclusions ONLY where AVM does not yet cover (document each in inline comment). Verify: `pwsh -c "Invoke-PSRule -InputPath infra/"` exits 0.
- [ ] T-AA026 [P] Add Bicep test fixture `infra/tests/help_what_if.bicepparam` for the deployment-stack chaos drill (used by T-AA189). — R6, FR-011c
- [ ] T-AA027 [P] Document infra changes in `docs/infrastructure/help.md` (new Cosmos containers + alias semantics + carve-out registry note). — CHK105
- [ ] T-AA028 [Gate] One-shot bootstrap script `tools/help/bootstrap_search_index.py` that creates `help-corpus-bootstrap` index + binds alias on first deploy. Verify: dry-run lists planned actions. — FR-011a
- [ ] T-AA029 [P] [Gate] AU-residency attestation script `tools/help/attest_au_residency.py` — queries every Help-related Azure resource and asserts `location ∈ {australiaeast, australiasoutheast}`; emits JSON attestation. Verify: dry-run on dev env passes. — FR-018, SC-011, CHK128
- [ ] T-AA030 [Gate] Run `azd provision` end-to-end against `ama-help-dev` and capture deployment log under `docs/infrastructure/help-dev-provision-{date}.log`. — checkpoint, CHK104

**Checkpoint**: dev infra fully provisioned, Foundry agent registered, alias bound to a stub index.

---

## Phase 2 — Domain models (Pydantic v2 + TypeScript twins)

**Depends on**: Phase 0. **Goal**: 13 entities live in `packages/domain/src/ama_domain/` with TS twins in `packages/domain/src/help/`; CI sync test passes.

- [ ] T-AA031 [P] Implement `packages/domain/src/ama_domain/help_article.py` (HelpArticle + ArticleKind, ArticleStatus enums; validators per data-model.md §1). Unit test in `tests/contract/help/test_help_article_model.py`. — FR-002, FR-003
- [ ] T-AA032 [P] Implement `packages/domain/src/ama_domain/annotated_screenshot.py` (AnnotatedScreenshot + Callout). Test. — FR-006, FR-008, FR-010a
- [ ] T-AA033 [P] Implement `packages/domain/src/ama_domain/glossary_term.py`. Test BCP-47 tag validation. — FR-009a
- [ ] T-AA034 [P] Implement `packages/domain/src/ama_domain/persona_help_profile.py` with authority_rank from shared registry (T-AA044). Test. — FR-027, FR-028, FR-027-AMEND
- [ ] T-AA035 [P] Implement `packages/domain/src/ama_domain/knowledge_corpus_source.py`; enforce `spec_status ∈ {Active, Implemented}` when `source_kind=='spec'`. Test rejects draft. — FR-011, FR-011-AMEND
- [ ] T-AA036 [P] Implement `packages/domain/src/ama_domain/chat_session.py` (ChatSession + ChatTurn). Test 30-day TTL annotation. — FR-029
- [ ] T-AA037 [P] Implement `packages/domain/src/ama_domain/help_feedback.py`. Test pattern_id required for chat_turn. — FR-022, FR-022a-AMEND
- [ ] T-AA038 [P] Implement `packages/domain/src/ama_domain/staleness_flag.py`. Test grace_release_id required. — FR-010, FR-010a, FR-010b
- [ ] T-AA039 [P] Implement `packages/domain/src/ama_domain/snapshot_record.py` (SnapshotRecord + Approver, frozen=True; min two distinct approver identities, at least one help_content_owner AND one safety_lead|governance_lead). Test rejects single-approver payload. — FR-011a, FR-011b, FR-011c, CHK065
- [ ] T-AA040 [P] Implement `packages/domain/src/ama_domain/support_handoff_record.py`. Test SLA defaults (4 h routine, 5 min incident). — FR-023a, FR-023b, FR-023a-AMEND
- [ ] T-AA041 [P] Implement `packages/domain/src/ama_domain/content_review_backlog_item.py`. Test auto-promote at ≥3 negatives in 30 d. — FR-022a
- [ ] T-AA042 [P] Implement `packages/domain/src/ama_domain/chat_audit_entry.py` (frozen=True). Test redacted-input field is the only input form. — FR-017, FR-020, FR-029, CHK046, CHK117
- [ ] T-AA043 [P] Reuse Citation from existing `packages/domain/src/ama_domain/citation.py` — add re-export and conformance test in `tests/contract/help/test_citation_reexport.py`. — FR-012
- [ ] T-AA044 [Gate] Add shared authority-rank registry `packages/domain/src/ama_domain/authority_rank_registry.py` with the AIIMS rank table sourced from spec-021 FR-025. Single source of truth used by PersonaHelpProfile + chat persona resolution. Test loads fixture. — FR-027-AMEND, CHK132
- [ ] T-AA045 [P] Generate TypeScript twins in `packages/domain/src/help/` — one `.ts` per Pydantic model (`help-article.ts`, `annotated-screenshot.ts`, `glossary-term.ts`, `persona-help-profile.ts`, `knowledge-corpus-source.ts`, `chat-session.ts`, `help-feedback.ts`, `staleness-flag.ts`, `snapshot-record.ts`, `support-handoff-record.ts`, `content-review-backlog-item.ts`, `chat-audit-entry.ts`, `index.ts` re-exporting Citation). — plan §Project Structure
- [ ] T-AA046 [P] Add type-export barrel `packages/domain/src/help/index.ts` so consumers can `import { HelpArticle, ChatTurn } from '@ama/domain/help'`. — contract §1
- [ ] T-AA047 [Gate] Add Pydantic↔TS sync test `tests/contract/help/test_domain_twin_sync.py` — uses existing twin-sync harness (or implement: parse Pydantic JSON schema; compare with TS-generated schema via `ts-json-schema-generator`). Fails on drift. — plan §data-model.md preamble
- [ ] T-AA048 [P] Add `packages/domain/__init__.py` re-export for new modules.
- [ ] T-AA049 [P] Cosmos repository helpers `apps/api/app/repositories/help_repositories.py` — typed wrappers for each container with `/tenant_id` partition enforcement. Unit test mocks Cosmos client. — FR-019, R3
- [ ] T-AA050 [P] Add `pattern_id` deterministic hasher `packages/domain/src/ama_domain/chat_pattern_id.py` — `sha256(question_intent_cluster_id + ":" + ":".join(citation_source_ids))` preserving the **exact citation order returned by the assistant** (FR-022a-AMEND mandates "exact ordered set"; do NOT sort). Test that two answers with the same intent cluster but different citation order produce DIFFERENT pattern ids. — FR-022a-AMEND
- [ ] T-AA051 [P] Add `screen_id_hash` deterministic hasher `packages/domain/src/ama_domain/screen_id_hash.py` — `sha256(route_id + "|" + "|".join(callout.anchor_dom_path for callout in sorted_by_callout_number))` preserving the **callout-number order** (FR-010a mandates "ordered set of DOM-element fingerprints"; do NOT lexicographically sort the anchors — sort callouts by `Callout.number` ascending and emit anchors in that order). Test cross-platform stability and that reordering callouts changes the hash. — FR-010a
- [ ] T-AA052 [Gate] Run `pnpm --filter @ama/domain build && uv run pytest tests/contract/help -k model` — all model tests green. — checkpoint

**Checkpoint**: domain layer ready; backend + frontend can begin in parallel.

---

## Phase 3 — Backend (FastAPI routes, services, agent integration)

**Depends on**: Phases 1, 2. **Goal**: every `/help/*` route in the OpenAPI contract is implemented, returns conformant responses, persists to Cosmos with tenant scoping, integrates the Foundry `help_assistant` agent via `apps/agents/common/`.

### 3a — Services (no HTTP yet)

- [X] T-AA053 [P] Implement `apps/api/app/services/help/snapshot_publisher.py` — orchestrates: dual-approval validation → emit `SnapshotRecord` → call `apps/ingest-runner` (or local `tools/help/publish_snapshot.py`) → swing alias → emit `audit.snapshot_published`. — FR-011a, FR-011b, FR-011c, CHK064, CHK065
- [X] T-AA054 [P] Implement `apps/api/app/services/help/snapshot_indexer.py` — wraps `azure-search-documents` admin client to create `help-corpus-{id}` index with the schema from data-model.md §AI Search and (re)bind alias. — FR-011a
- [X] T-AA055 [P] Implement `apps/api/app/services/help/staleness_checker.py` — given a `route_id` + live DOM-fingerprint set, recomputes `screen_id_hash`, raises/clears `StalenessFlag`. — FR-010a, FR-010a-AMEND, FR-010b
- [X] T-AA056 [P] Implement `apps/api/app/services/help/feedback_aggregator.py` — on each `HelpFeedback`, upserts/creates `ContentReviewBacklogItem`; auto-promotes to `needs_review` when ≥3 negatives in 30 days for the same `(article_id | pattern_id)`. NEVER auto-disables. — FR-022a, CHK113
- [X] T-AA057 [P] Implement `apps/api/app/services/help/support_handoff_sla_monitor.py` — a periodic job (Cosmos change-feed lease) that emits `audit.support_handoff_unack_timeout` when an open handoff exceeds its SLA (4 h routine, 5 min incident-mode auto-activated by NEMA-Level-3 banner from spec-024). — FR-023a, FR-023a-AMEND, FR-023b, CHK124
- [X] T-AA058 [P] Implement `apps/api/app/services/help/persona_resolver.py` — resolves active persona per FR-027 (IdP claim → highest-authority operational role; user override) using the shared authority rank registry (T-AA044); records `persona_source ∈ {idp_default, user_override}`. — FR-027, FR-027-AMEND, FR-028, CHK131, CHK132
- [X] T-AA059 [P] Implement `apps/api/app/services/help/chat_audit_writer.py` — append-only writer for `ChatAuditEntry`; refuses UPDATE/DELETE at the application layer; records snapshot_id, persona, persona_source, gateway_decision. — FR-020, FR-029, CHK046, CHK117
- [X] T-AA060 [P] Implement `apps/api/app/services/help/transcript_reconstructor.py` — Observer-Auditor-only reconstruction from `ChatAuditEntry` for transcripts past the 30-day window; emits `audit.transcript_reconstructed` per FR-029b. — FR-029a, FR-029b, CHK119
- [X] T-AA061 [P] Implement `apps/api/app/services/help/deprecation_resolver.py` — given a deep-link slug + snapshot_id, returns `current_replacement | withdrawn_no_replacement`; populates `<DeprecationNotice />` props. — FR-011d, FR-011d-AMEND, CHK067
- [X] T-AA062 [P] Implement `apps/api/app/services/help/conflict_surfacer.py` — when retrieval returns ≥2 sources with conflicting claims (citation set heuristic), wraps the answer with conflict notice and both citations. — FR-016, CHK090
- [X] T-AA063 [P] Implement `apps/api/app/services/help/content_classification_guard.py` — rejects any source whose `classification` is above `OFFICIAL` from snapshot ingestion (defence in depth even though FR-011 admission gate already filters). — FR-011, plan §C

### 3b — Agent integration (Foundry `help_assistant`)

- [X] T-AA064 [P] [Gate] Implement `apps/agents/help_assistant/agent.py` — constructs the Foundry agent using `apps/agents/common/foundry_chat_client.py`, retrieval-only tool against alias `help-corpus-active`, configured per T-AA018; exposes `async run(turn_input, persona_id, jurisdictions, tenant_id) -> ChatTurn`. — FR-011, FR-015, plan §C
- [X] T-AA065 [P] [Gate] Author `apps/agents/help_assistant/prompts/system.md` — refusal-first system prompt; persona/jurisdiction interpolation; explicit "answer only from retrieved chunks; cite every claim; refuse if no chunks; refuse if any chunk is from outside the user's tenant scope". — FR-013, FR-014, FR-015, CHK087
- [X] T-AA066 [P] Author `apps/agents/help_assistant/prompts/refusal.md` — standard refusal template referencing FR-013 categories (`out_of_scope`, `cross_tenant`, `no_corpus_match`, `pii_blocked`, `above_official_classification`, `deprecated_no_replacement`). — FR-013, FR-014, FR-023, CHK088
- [X] T-AA067 [P] Author `apps/agents/help_assistant/prompts/deprecation_notice.md` — template for FR-011d / FR-011d-AMEND deprecation notices. — FR-011d, FR-011d-AMEND
- [X] T-AA068 [P] Wire `apps/agents/common/retrieval_client` to enforce the hard tenant filter `tenant_id eq @tenant or scope eq 'global'` for any call originating from `help_assistant` (config flag, not user input). — FR-019, FR-011-AMEND, R3, CHK097
- [X] T-AA069 [P] Wire `apps/agents/common/citation_filter` to the help_assistant pipeline so any answer with zero retrieved chunks is converted to a refusal (`no_corpus_match`). — FR-014, R2, CHK089
- [X] T-AA070 [P] Confirm `apps/agents/common/model_gateway.process(input, region="australiaeast")` is invoked for every Help chat turn; on redaction emit `meta.redaction_notice = true`. Add wrapper `apps/agents/help_assistant/redaction_wrapper.py`. — FR-017, CHK045
- [X] T-AA071 [P] Author `apps/agents/help_assistant/eval_fixtures/{grounded.jsonl,refusals.jsonl,fabrication_audit.jsonl,persona_tailoring.jsonl,cross_tenant_probe.jsonl,pii_probe.jsonl}` — gold sets consumed by Phase 8 LLM-eval. — SC-002, SC-003, SC-004, plan §Tier 4

### 3c — FastAPI routes

- [X] T-AA072 [Gate] `apps/api/app/api/routes/help_chat.py` — `POST /help/chat/ask` (SSE: `meta`, `delta`×N, `citation`×N, `done`, optional `refusal`); `POST /help/chat/feedback` (202 → enqueues backlog); `GET /help/chat/sessions/{id}` (own user only). Wires services T-AA058, T-AA059, T-AA064, T-AA070. — FR-011, FR-012, FR-013, FR-015, FR-017, FR-022, FR-023, contract §/help/chat/*
- [X] T-AA073 [Gate] `apps/api/app/api/routes/help_articles.py` — `GET /help/articles?...filters` (paginated; ETag); `GET /help/articles/{slug}` (returns published metadata + body URI). Read-only; writes happen via snapshot pipeline. — FR-001, FR-005, FR-021, contract §/help/articles*
- [X] T-AA074 [Gate] `apps/api/app/api/routes/help_snapshots.py` — `GET /help/snapshots`; `POST /help/snapshots/publish` (422 if dual approver missing); `POST /help/snapshots/{id}/rollback` (≤5 min budget; emits `audit.snapshot_rollback`). — FR-011a, FR-011b, FR-011c, contract §/help/snapshots*
- [X] T-AA075 [Gate] `apps/api/app/api/routes/help_screenshots.py` — `GET /help/screenshots/staleness` (list active flags); `POST /help/screenshots/staleness/{id}/clear` (author-only); `GET /help/screenshots/{screen_id}/url?theme=light|dark` (signed-URL issuance). — FR-010, FR-010a, FR-010b, contract §/help/screenshots/*
- [X] T-AA076 [Gate] `apps/api/app/api/routes/help_search.py` — `GET /help/search?q=...` (glossary-first ordering when query matches a glossary term canonical or alias). — FR-021, contract §/help/search
- [X] T-AA077 [Gate] `apps/api/app/api/routes/help_support_handoff.py` — `GET /help/support-handoff` (per-tenant); `PUT /help/support-handoff` (admin-scoped). — FR-023a, FR-023a-AMEND, FR-023b, contract §/help/support-handoff
- [X] T-AA078 [P] Mount the 6 routers in `apps/api/app/main.py` under prefix `/api/v1`. Verify: `uv run uvicorn app.main:app` then `curl http://127.0.0.1:8000/openapi.json` includes `/api/v1/help/...` paths.
- [X] T-AA079 [P] Add `Accept-Language` plumbing on every Help route per Constitution NN-4. — plan §Constitution Check NN-4
- [X] T-AA080 [P] Add error envelope conforming to existing platform `Error` schema (`code`, `message`, `correlation_id`). — contract §components.responses
- [X] T-AA081 [P] Add ETag / If-Match support on `GET /help/articles/{slug}` and `PUT /help/support-handoff` (optimistic concurrency). — contract
- [X] T-AA082 [P] Tenant-claim middleware: every `/help/*` request derives `tenant_id` from authenticated principal; rejects requests where claim missing. — FR-019, R3
- [X] T-AA083 [P] Persona-entitlement middleware: `POST /help/chat/ask` returns 403 if `persona_id` not entitled for the user. — FR-028, contract §5
- [X] T-AA084 [P] Degraded-mode detector: if `help-corpus-active` alias resolves but health-query returns 0 docs, return `503 { code: snapshot_unavailable }` from `/help/chat/ask`. — FR-026, R1
- [X] T-AA085 [P] OpenAPI router-doc strings emit components matching `contracts/help-api.openapi.yaml`. Verify via `tests/contract/help/test_openapi_conformance.py` (T-AA183). — contract
- [X] T-AA086 [P] Implement `apps/ingest-runner/src/help_snapshot/__main__.py` — entrypoint for `ingest-runner --mode help-snapshot` invoked by both CI workflow and `tools/help/publish_snapshot.py`; idempotent on `(snapshot_id, source_id, content_hash)`. — FR-011a, plan §A, plan §B
- [X] T-AA087 [P] Implement `apps/ingest-runner/src/help_snapshot/source_loaders.py` — loads MDX articles + `docs/aidr/**` + `docs/corpus/**` + Active/Implemented specs from `specs/**` (per manifest). — FR-011, FR-011-AMEND
- [X] T-AA088 [P] Implement `apps/ingest-runner/src/help_snapshot/embedder.py` — uses spec-036 `foundry_query_embedder` for body_vector. — plan §C, data-model §AI Search
- [X] T-AA089 [P] Implement `apps/ingest-runner/src/help_snapshot/alias_swinger.py` — pre-warms new index (≥1 doc), waits for health-query, atomically swings alias. — R1, FR-011c
- [X] T-AA090 [P] Audit-event emitters: `audit.snapshot_published`, `audit.snapshot_rollback`, `audit.transcript_reconstructed`, `audit.support_handoff_unack_timeout`, `audit.chat_refusal`. Verify each via integration tests. — FR-011c, FR-023b, FR-029b, plan §Constitution Check IV
- [X] T-AA091 [Gate] PSPF DENY enforcement: any retrieval result with `classification != OFFICIAL` is filtered out of the response set returned to chat (defence in depth). — FR-011, plan §C
- [X] T-AA092 [Gate] Smoke-run `uv run uvicorn app.main:app` and exercise each route with `httpx`; commit a `tests/contract/help/test_route_smoke.py` invoking each. — checkpoint

**Checkpoint**: backend ready; frontend can integrate against running API.

---

## Phase 4 — Frontend (Next.js Help routes + components)

**Depends on**: Phases 2, 3. **Goal**: every component in `contracts/help-ui.contract.ts.md` exists with correct props, telemetry, and a11y; routes render server-side; persona-aware landing works.

### 4a — Library / shell

- [ ] T-AA093 [P] Implement `apps/web/src/lib/help/telemetry.ts` — typed wrappers around Application Insights `trackEvent` for the 10 events in contract §3. — contract §3, FR-020
- [ ] T-AA094 [P] Implement `apps/web/src/lib/help/deepLinkParser.ts` — parses `?help=open&surface=...`, `?persona=...`, validates entitlement claim. — FR-005, contract §1
- [ ] T-AA095 [P] Implement `apps/web/src/lib/help/offlineCache.ts` — `idb`-backed cache binding to `apps/agents/common/offline_cache` envelope (≤500 MB / 14-day TTL); records on each viewed article + glossary + curated FAQ topics; emits "may be stale" once past TTL. — FR-026, FR-026a, FR-026b, CHK139, CHK140
- [ ] T-AA096 [P] Implement `apps/web/src/lib/help/sseClient.ts` — typed SSE consumer for `/help/chat/ask` with reconnect + cancel. — contract §2 ChatPanel
- [ ] T-AA097 [P] Implement `apps/web/src/lib/help/personaContext.ts` — client hook resolving `personaId` + `personaSource` (mirrors backend T-AA058). — FR-027, FR-028
- [ ] T-AA098 [P] Implement `apps/web/src/lib/help/degradedModeDetector.ts` — listens for `navigator.connection` + service-worker offline event + 503 from `/help/chat/ask`; toggles degraded UI. — FR-026, FR-026a-AMEND, CHK141, CHK142

### 4b — Layout + routes

- [ ] T-AA099 [Gate] `apps/web/src/app/help/layout.tsx` — persistent Help shell, persona switcher (reuses spec-021 multi-role widget), telemetry mount. — contract §1, FR-001, CHK026
- [ ] T-AA100 [Gate] `apps/web/src/app/help/page.tsx` — persona-aware landing; renders `<PersonaTile />` union for multi-role users ordered by `authority_rank` desc; tour shortcut. — FR-002, FR-027, FR-028, CHK001-CHK016
- [ ] T-AA101 [Gate] `apps/web/src/app/help/search/page.tsx` — full-text search via `/help/search`; glossary-first ordering visible. — FR-021, CHK025, CHK030
- [ ] T-AA102 [Gate] `apps/web/src/app/help/chat/page.tsx` — full-page chat surface; mounts `<ChatPanel />`; mirrors side-panel state. — FR-012, FR-013, FR-014, FR-017, contract §1
- [ ] T-AA103 [Gate] `apps/web/src/app/help/articles/[slug]/page.tsx` — MDX render; embeds `<AnnotatedScreenshot />` + `<KeyboardSteps />`. — FR-005, FR-006, FR-008, CHK027
- [ ] T-AA104 [Gate] `apps/web/src/app/help/glossary/[term]/page.tsx` — glossary entry + cross-links; honours `lang` attribute on non-English fragments. — FR-009a, FR-021, CHK025, CHK132
- [ ] T-AA105 [Gate] `apps/web/src/app/help/playbooks/[id]/page.tsx` — long-form playbook layout (simulation/agent/observer). — FR-003, CHK020-CHK022

### 4c — Components

- [ ] T-AA106 [Gate] `apps/web/src/components/help/HelpAffordance.tsx` — global header `?` button + `Ctrl+/`/`⌘+/` shortcut; opens side panel; `aria-label`, `aria-keyshortcuts`. Mounted in `apps/web/src/app/layout.tsx`. — FR-001, contract §2, CHK026, CHK040
- [ ] T-AA107 [Gate] `apps/web/src/components/help/ChatPanel.tsx` — SSE consumer; renders `<RefusalCard />`, `<DeprecationNotice />`, `<CitationBadge />`; degraded banner; `role="log" aria-live="polite"`. — FR-012, FR-013, FR-026, contract §2, CHK087-CHK090, CHK140
- [ ] T-AA108 [Gate] `apps/web/src/components/help/AnnotatedScreenshot.tsx` — `<picture>` light/dark variants; numbered callouts as list with `aria-describedby`; staleness banner integration. — FR-006, FR-007, FR-008, FR-010, contract §2, CHK051-CHK055, CHK078
- [ ] T-AA109 [Gate] `apps/web/src/components/help/CitationBadge.tsx` — inline anchor with `aria-label`; popover on focus/hover. — FR-012, contract §2, CHK089
- [ ] T-AA110 [Gate] `apps/web/src/components/help/StalenessBanner.tsx` — `role="status"`; downgraded variant after grace expires. — FR-010, FR-010b, contract §2, CHK078, CHK080
- [ ] T-AA111 [Gate] `apps/web/src/components/help/DeprecationNotice.tsx` — replacement-or-handoff variants; surfaces tenant `SupportHandoffRecord` when no replacement. — FR-011d, FR-011d-AMEND, contract §2, CHK067
- [ ] T-AA112 [Gate] `apps/web/src/components/help/RefusalCard.tsx` — non-judgmental wording per refusal reason; suggested surface + handoff. — FR-013, FR-014, FR-023, contract §2, CHK088
- [ ] T-AA113 [Gate] `apps/web/src/components/help/FeedbackBar.tsx` — POSTs to `/help/chat/feedback`; toast confirmation; never alters rated content. — FR-022, FR-022a, contract §2, CHK112, CHK113
- [ ] T-AA114 [Gate] `apps/web/src/components/help/PersonaTile.tsx` — used in landing union; visually highlights active. — FR-002, FR-028, contract §2
- [ ] T-AA115 [Gate] `apps/web/src/components/help/KeyboardSteps.tsx` — `<ol>` with `aria-labelledby` paired with screenshot caption. — FR-008, contract §2, CHK054
- [ ] T-AA116 [P] `apps/web/src/components/help/ConflictNotice.tsx` — surfaced when chat backend reports source disagreement. — FR-016, CHK090
- [ ] T-AA117 [P] `apps/web/src/components/help/RedactionNotice.tsx` — inline banner shown when `meta.redaction_notice = true`. — FR-017, CHK045
- [ ] T-AA118 [P] `apps/web/src/components/help/DegradedSearchBanner.tsx` — persistent "Showing cached results only — full search unavailable offline" indicator. — FR-026a-AMEND, CHK142
- [ ] T-AA119 [P] `apps/web/src/components/help/SupportHandoffButton.tsx` — one-click handoff using tenant `SupportHandoffRecord`. — FR-023, FR-023a, CHK122
- [ ] T-AA120 [P] `apps/web/src/components/help/FirstFifteenMinutesTour.tsx` — persona-driven tour overlay used by landing. — US1, FR-002, CHK001-CHK010
- [ ] T-AA121 [P] Theme-aware screenshot serving — extend Tailwind/CSS theme tokens so `<AnnotatedScreenshot />` swaps automatically with `prefers-color-scheme`. — FR-007, CHK052
- [ ] T-AA122 [P] Add `apps/web/src/app/help/loading.tsx` and `error.tsx` shells for resilience. — Constitution III
- [ ] T-AA123 [P] Add `apps/web/src/app/help/sitemap.ts` so `pa11y-ci --sitemap` works. — quickstart §6
- [ ] T-AA124 [P] Implement service-worker registration `apps/web/src/lib/help/sw-register.ts` for offline cache persistence. — FR-026
- [ ] T-AA125 [P] Add `aria-keyshortcuts` registration to global keyboard map; visible-focus CSS verified ≥3:1 contrast. — FR-009, contract §4, CHK040, CHK041
- [ ] T-AA126 [P] Add reduced-motion handling for any animations in Help (chat-typing indicator, toast). — contract §4
- [ ] T-AA127 [Gate] `pnpm --filter @ama/web build` succeeds; `pnpm --filter @ama/web start` and smoke-test `/help` route renders. — checkpoint

**Checkpoint**: UI shell functional; ready for content authoring.

---

## Phase 5 — Help content authoring (articles, screenshots, glossary, playbooks)

**Depends on**: Phase 4 (components must exist to embed). **Goal**: every persona, every primary surface, every domain has authored content; light + dark screenshots captured; glossary populated.

### 5a — Persona landings (10 ops + 6 sectors)

- [ ] T-AA128 [P] [Gate] Author `apps/web/src/content/help/personas/incident-commander/landing.mdx` (+ first-15-min tour, AIIMS Controller workflow, public-alert approval, cross-jurisdiction escalation, span-of-control warnings, audit traceability links). — FR-002, FR-004, CHK001
- [ ] T-AA129 [P] [Gate] Author `apps/web/src/content/help/personas/operations-officer/landing.mdx` + tour + tactical task assignment, multi-sector coordination, staging strategy, agent-recommendations review, escalation-up. — CHK002
- [ ] T-AA130 [P] [Gate] Author `apps/web/src/content/help/personas/planning-officer/landing.mdx` + content per CHK003. — CHK003
- [ ] T-AA131 [P] [Gate] Author `apps/web/src/content/help/personas/logistics-officer/landing.mdx` + content per CHK004. — CHK004
- [ ] T-AA132 [P] [Gate] Author `apps/web/src/content/help/personas/public-information-officer/landing.mdx` + multilingual alert composer guide + accessibility checker + Principle V coverage. — CHK005, FR-024
- [ ] T-AA133 [P] [Gate] Author `apps/web/src/content/help/personas/field-coordinator/landing.mdx` + degraded-connectivity behaviour. — CHK006
- [ ] T-AA134 [P] [Gate] Author `apps/web/src/content/help/personas/resilience-planner/landing.mdx` + scenario design. — CHK007
- [ ] T-AA135 [P] [Gate] Author `apps/web/src/content/help/personas/executive-leader/landing.mdx`. — CHK008
- [ ] T-AA136 [P] [Gate] Author `apps/web/src/content/help/personas/observer-auditor/landing.mdx` — observation/audit-only language; chat starter prompts must NOT instruct state-changing actions. — CHK009, FR-025
- [ ] T-AA137 [P] [Gate] Author `apps/web/src/content/help/personas/risk-manager/landing.mdx`. — CHK010
- [ ] T-AA138 [P] [Gate] Author `apps/web/src/content/help/personas/frontline-fire/landing.mdx` + NSW-jurisdiction screenshot variant. — CHK011, US1#3
- [ ] T-AA139 [P] [Gate] Author `apps/web/src/content/help/personas/frontline-medical/landing.mdx`. — CHK012
- [ ] T-AA140 [P] [Gate] Author `apps/web/src/content/help/personas/frontline-police/landing.mdx`. — CHK013
- [ ] T-AA141 [P] [Gate] Author `apps/web/src/content/help/personas/frontline-ses-marine/landing.mdx`. — CHK014
- [ ] T-AA142 [P] [Gate] Author `apps/web/src/content/help/personas/commonwealth/landing.mdx`. — CHK015
- [ ] T-AA143 [P] [Gate] Author `apps/web/src/content/help/personas/cross-sector/landing.mdx`. — CHK016

### 5b — Screen-by-screen guides (every primary surface)

- [ ] T-AA144 [P] [Gate] Author screen-by-screen articles for: Disaster Mapper, Governance Dashboard, Multi-Jurisdiction Filter, Simulation Control, Alert Composer, Agent surfaces (Communication / Evacuation / Monitoring / Risk Assessment / Resource Allocation), Audit/Observer view, Persona switcher, Settings, Login under `apps/web/src/content/help/articles/screen-by-screen/*.mdx`. Each MUST embed `<AnnotatedScreenshot />` + `<KeyboardSteps />`. — FR-006, FR-007, FR-008, CHK019, CHK051-CHK055
- [ ] T-AA145 [P] [Gate] Capture light + dark screenshots for every primary surface via `tools/help/capture_screenshots.ts` (T-AA176); commit manifests to `screenshot_registry`. — FR-006, FR-007, SC-005, CHK051, CHK052, CHK053
- [ ] T-AA146 [P] [Gate] Author alt-text JSON sidecars `<screen_id>.alt.json` per callout + keyboard-equivalent steps. — FR-008, CHK054, CHK078

### 5c — Domain content

- [ ] T-AA147 [P] [Gate] Author "Getting started" article(s) — Hub overview, sign-in, persona switcher, jurisdiction filter, theme/accessibility settings. — FR-003 D1, CHK017
- [ ] T-AA148 [P] [Gate] Author Simulation Playbook (`apps/web/src/content/help/articles/playbooks/simulation.mdx`) — scenario configuration, warp/playback, multi-jurisdiction scenarios, observation export. — CHK020, US4#1
- [ ] T-AA149 [P] [Gate] Author Agent Playbooks (5 articles): Communication, Evacuation, Monitoring, Risk Assessment, Resource Allocation — each with provenance, confidence, human-approval steps. — CHK021, US4#2
- [ ] T-AA150 [P] [Gate] Author Audit/Observer mode guide — append-only timeline navigation, framework-deviation review, lessons-learned export. — CHK022, US4#3
- [ ] T-AA151 [P] [Gate] Author Accessibility how-tos — keyboard navigation, screen-reader use, contrast/theme; multilingual authoring guide for PIO. — CHK023, FR-024
- [ ] T-AA152 [P] [Gate] Author Troubleshooting/FAQ — login, persona switching, jurisdiction filter, degraded mode, alert approval failures, simulation reset, chat refusals. — CHK024, FR-021
- [ ] T-AA153 [P] [Gate] Author Glossary — AIIMS, AIDR, jurisdictional, Hub-specific terms in `apps/web/src/content/help/glossary/*.yaml` with correct `lang` attributes for non-English fragments. — CHK025, FR-009a, FR-021
- [ ] T-AA154 [P] Author "Help on this screen" mapping config `apps/web/src/content/help/surfaceMap.yaml` mapping `route_id → article_slug`. — FR-005, CHK027
- [ ] T-AA155 [P] Author chat starter prompts per persona in each landing MDX (consumed by `<ChatPanel />`). — US2, FR-002
- [ ] T-AA156 [P] Author Constitution Principle V coverage article (referenced by PIO landing). — FR-024, CHK132
- [ ] T-AA157 [P] Author "What does the amber confidence badge mean?" article (US2 example). — US2 acceptance scenarios
- [ ] T-AA158 [P] Author "Cross-border bushfire escalation to NEMA" article (US2 example). — US2 acceptance scenarios
- [ ] T-AA159 [P] Author multilingual content authoring guide for PIO (community languages + Aboriginal & Torres Strait Islander considerations; cultural-authority registry references). — FR-024, plan §G
- [ ] T-AA160 [P] [Gate] Cultural-authority registry consultation: for any article referencing Aboriginal & Torres Strait Islander language items, file consultation evidence under `docs/cultural-authority/help/` with ID linking back to the article. — plan §G, CHK132
- [ ] T-AA161 [P] [Gate] Verify every glossary term has `related_article_ids` and every persona has at least one workflow article cross-link. — FR-021
- [ ] T-AA162 [P] Add `apps/web/src/content/help/articles/observer-mode-guide.mdx` aligned with FR-025 read-only constraint. — CHK009, FR-025
- [ ] T-AA163 [P] [Gate] Editorial review: dual-approval PR for the bootstrap content set; record `SnapshotRecord` approver identities. — FR-011b

**Checkpoint**: corpus is publishable; Phase 6 can run.

---

## Phase 6 — Snapshot publication pipeline (CI + CODEOWNERS gate)

**Depends on**: Phases 1, 3, 5, 7. **Goal**: a merged PR auto-publishes a new immutable snapshot, dual-approval gated; rollback works via alias swap within ≤5 min.

- [ ] T-AA164 [Gate] Author GitHub Actions workflow `.github/workflows/help-snapshot.yml` — triggers on `main` merge touching `apps/web/src/content/help/**` OR `specs/**` snapshot manifest; runs `python tools/help/publish_snapshot.py` with merged approver identities; publishes to dev → test → prod via stack environments. — FR-011a, FR-011b, FR-011c, CHK064, CHK065, CHK066
- [ ] T-AA165 [Gate] Implement `tools/help/publish_snapshot.py` — local + CI publisher; idempotent on `(snapshot_id, source_id, content_hash)`; calls `apps/ingest-runner --mode help-snapshot`; swings alias; emits `audit.snapshot_published`. Supports `rollback --restored-snapshot-id` subcommand within 5 min budget. — FR-011a, FR-011c, CHK064, CHK068
- [ ] T-AA166 [Gate] CODEOWNERS gate enforcement test `tests/contract/help/test_codeowners_dual_approval.py` — uses `gh codeowners` to confirm both teams required on `apps/web/src/content/help/**` and snapshot manifest. — FR-011b, CHK065
- [ ] T-AA167 [P] Approver-identity persistence: snapshot publish endpoint records full approver identity + role + ISO timestamp into `SnapshotRecord.approvers[]`. Verify via integration test. — FR-011b, CHK065
- [ ] T-AA168 [P] Rollback flow: `POST /help/snapshots/{id}/rollback` re-binds alias to a prior snapshot; emits `audit.snapshot_rollback` with `previous_snapshot_id`, `restored_snapshot_id`, `actor_id`, `change_reason`. — FR-011c, CHK066
- [ ] T-AA169 [P] Spec-snapshot composition rule: only specs with status ∈ {Active, Implemented} that are listed in the manifest are admitted; draft/experimental excluded. Enforced in `apps/ingest-runner/src/help_snapshot/source_loaders.py`; tested in T-AA185. — FR-011, CHK063
- [ ] T-AA170 [P] Per-tenant snapshot composition override: manifest may contain `tenants.<id>.exclude` lists. Enforced + tested. — FR-011-AMEND
- [ ] T-AA171 [P] Snapshot immutability: `snapshot_records` Cosmos role permits insert-only for the publisher identity. Verify via Cosmos role assignment list. — FR-011a
- [ ] T-AA172 [P] Deprecation-notice pipeline: when a publish supersedes content, the publisher writes a `deprecation_map` JSON enabling `/help/articles/{slug}` to render `<DeprecationNotice />`. Withdrawn-no-replacement entries surface support-handoff. — FR-011d, FR-011d-AMEND, CHK067
- [ ] T-AA173 [Gate] End-to-end publish→verify→rollback rehearsal in dev env captured under `docs/runbooks/help/snapshot-publish-rollback-rehearsal-{date}.md`. Confirms ≤5 min alias swing. — FR-011c, R6, CHK066

---

## Phase 7 — Build-time tooling (freshness, lang lint, link checker)

**Depends on**: Phases 0, 4. **Goal**: build pipeline catches stale screenshots, missing `lang` attributes, dead deep links.

- [ ] T-AA174 [Gate] Implement `tools/help/check_screenshot_freshness.py` — recomputes `screen_id_hash` from current build (using `tools/help/route_registry.py`), compares with stored value in `screenshot_registry`, raises `StalenessFlag` on mismatch; supports `--register-only` mode. — FR-010a, FR-010a-AMEND, FR-010b, CHK074, CHK075
- [ ] T-AA175 [Gate] Implement `tools/help/lint_lang_attributes.py` — scans built static HTML for declared glossary terms missing `lang`; fails build on violation. CI gate. — FR-009a, FR-009a-AMEND, CHK046, CHK047
- [ ] T-AA176 [Gate] Implement `tools/help/capture_screenshots.ts` — Playwright-driven capture of light + dark variants per route id; computes `screen_id_hash`; uploads to `help-screenshots` blob container; updates `screenshot_registry`. — FR-006, FR-007, FR-010a, plan §D, CHK051-CHK053
- [ ] T-AA177 [Gate] Implement `tools/help/route_registry.py` — single source of truth for `route_id` ↔ Next.js path; supports `previous_route_id` for bulk re-baseline. — FR-010a-AMEND, CHK076
- [ ] T-AA178 [Gate] Implement `tools/help/link_checker.py` — build-time link checker for MDX articles; verifies every internal deep-link resolves to a known slug; verifies every citation deep-link resolves to a heading anchor. Fails build on broken link. — FR-005, FR-012, CHK089
- [ ] T-AA179 [P] Implement `tools/help/rehype-lang-attr.ts` (move from stub T-AA007) — at authoring time, rejects MDX commit if a glossary-tagged non-English fragment lacks a `lang` attribute. — FR-009a-AMEND, plan §G
- [ ] T-AA180 [P] Implement `tools/help/bulk_rebaseline.py` — invoked when `route_registry.previous_route_id` changes; raises grouped staleness flag with `bulk_baseline_id`. — FR-010a-AMEND, CHK076
- [ ] T-AA181 [P] CI wiring: extend `.github/workflows/ci.yml` to invoke each tool above on every PR. Verify CI yaml lint passes. — quickstart §6

---

## Phase 8 — Tests (contract, integration, e2e, LLM-eval, a11y, tenant isolation)

**Depends on**: Phases 3, 4, 5. **Goal**: gates from `quickstart.md §6` and the full FR/SC matrix are exercised in CI.

### 8a — Contract (pytest)

- [ ] T-AA182 [P] [Gate] `tests/contract/help/test_help_api_openapi.py` — validates every response in `contracts/help-api.openapi.yaml` against the running app. — contract, plan §Tier 1
- [ ] T-AA183 [P] [Gate] `tests/contract/help/test_chat_audit_schema.py` — every `ChatAuditEntry` round-trips through Pydantic. — FR-020, plan §Tier 1
- [ ] T-AA184 [P] [Gate] `tests/contract/help/test_snapshot_record_dual_approval.py` — publish endpoint rejects payloads without two distinct approver identities (one help_content_owner + one safety_lead|governance_lead). — FR-011b, CHK065
- [ ] T-AA185 [P] [Gate] `tests/contract/help/test_lang_attr_lint.py` — `tools/help/lint_lang_attributes.py` passes on valid corpus, fails on missing `lang`. — FR-009a-AMEND, CHK046
- [ ] T-AA186 [P] [Gate] `tests/contract/help/test_screen_id_hash.py` — hash deterministic across platforms; mismatched anchor set → flag raised. — FR-010a, CHK074
- [ ] T-AA187 [P] [Gate] `tests/contract/help/test_retrieval_filters_tenant.py` — every retrieval call carries the tenant filter; cannot be overridden by caller. — FR-019, R3, CHK097
- [ ] T-AA188 [P] [Gate] `tests/contract/help/test_pattern_id_stability.py` — `pattern_id` stable across citation orderings. — FR-022a-AMEND
- [ ] T-AA189 [P] `tests/contract/help/test_route_smoke.py` — every router returns 200 / 401 / 422 as appropriate. — Phase 3 checkpoint

### 8b — Integration (pytest)

- [ ] T-AA190 [P] [Gate] `tests/integration/help/test_chat_end_to_end.py` — POST /help/chat/ask returns SSE stream with ≥1 citation; refusal path emits `audit.chat_refusal`. — FR-012, FR-013, plan §Tier 2
- [ ] T-AA191 [P] [Gate] `tests/integration/help/test_snapshot_publish_rollback.py` — publish stamps new index, alias swings; rollback re-binds within 5 min budget. — FR-011a, FR-011c, R6
- [ ] T-AA192 [P] [Gate] `tests/integration/help/test_pii_redaction_notice.py` — input with AU mobile is redacted; UI notice rendered; audit log carries redacted form only. — FR-017, FR-020, CHK045, CHK046
- [ ] T-AA193 [P] [Gate] `tests/integration/help/test_tenant_isolation.py` — multi-tenant probe: queries scoped to tenant A never return tenant B docs. — FR-019, SC-004, R3, CHK097-CHK101
- [ ] T-AA194 [P] [Gate] `tests/integration/help/test_degraded_mode.py` — service-worker cache returns articles offline; chat is disabled with banner; degraded search banner present. — FR-026, FR-026a, FR-026a-AMEND, FR-026b, CHK139-CHK142
- [ ] T-AA195 [P] [Gate] `tests/integration/help/test_support_handoff_sla.py` — NEMA-Level-3 banner triggers incident-mode channel; SLA breach emits `audit.support_handoff_unack_timeout`. — FR-023a-AMEND, FR-023b, CHK124, CHK125
- [ ] T-AA196 [P] [Gate] `tests/integration/help/test_persona_resolution.py` — multi-role users see union ordered by authority rank; chat uses only active persona; `persona_source` recorded. — FR-027, FR-028, CHK131-CHK134
- [ ] T-AA197 [P] [Gate] `tests/integration/help/test_transcript_reconstruction.py` — Observer-Auditor reconstruction renders only inside audit tooling; emits `audit.transcript_reconstructed`; original user history unchanged. — FR-029a, FR-029b, CHK119
- [ ] T-AA198 [P] [Gate] `tests/integration/help/test_deprecation_notice.py` — deep link to superseded content shows `<DeprecationNotice />`; withdrawn-no-replacement surfaces support handoff. — FR-011d, FR-011d-AMEND, CHK067
- [ ] T-AA199 [P] [Gate] `tests/integration/help/test_negative_feedback_no_silencing.py` — 4 negative feedbacks on same article+pattern do NOT auto-disable; backlog promotes to `needs_review`. — FR-022a, CHK113

### 8c — E2E (Playwright + axe-core)

- [ ] T-AA200 [P] [Gate] `apps/web/__tests__/e2e/help/landing.persona.spec.ts` — every persona landing tile loads with first-15-min tour. — FR-002, US1, CHK001-CHK016
- [ ] T-AA201 [P] [Gate] `apps/web/__tests__/e2e/help/screenshot.theme.spec.ts` — light/dark variants swap with theme; alt text + adjacent keyboard steps present. — FR-007, FR-008, US3
- [ ] T-AA202 [P] [Gate] `apps/web/__tests__/e2e/help/chat.citations.spec.ts` — every chat answer renders ≥1 `<CitationBadge />` that deep-links to the article anchor. — FR-012, US2
- [ ] T-AA203 [P] [Gate] `apps/web/__tests__/e2e/help/a11y.wcag22aa.spec.ts` — axe-core on every Help route; zero Level A/AA violations. — FR-009, SC-006, CHK040-CHK048
- [ ] T-AA204 [P] [Gate] `apps/web/__tests__/e2e/help/keyboard.only.spec.ts` — full Help + chat operable via keyboard; visible focus throughout. — FR-009, CHK040, CHK041
- [ ] T-AA205 [P] [Gate] `apps/web/__tests__/e2e/help/degraded.offline.spec.ts` — offline-first cache + chat-disabled banner + degraded-search indicator. — FR-026, FR-026a-AMEND, US1 edge case

### 8d — LLM evaluation (spec-030 framework)

- [ ] T-AA206 [P] [Gate] `tests/llm-eval/help/eval_grounded_answers.py` — runs `eval_grounded_answers.jsonl` (≥200 in-scope Q/A); gate ≥90% pass with ≥1 valid citation. — SC-002, plan §Tier 4
- [ ] T-AA207 [P] [Gate] `tests/llm-eval/help/eval_refusals.py` — out-of-scope set; gate 100% refused. — SC-002, FR-013
- [ ] T-AA208 [P] [Gate] `tests/llm-eval/help/eval_fabrication_audit.py` — sampled audit script over `chat_audit_log`; fail-closed on any verified fabrication. — SC-003, FR-014, R2
- [ ] T-AA209 [P] [Gate] `tests/llm-eval/help/eval_persona_tailoring.py` — persona-tagged Q/A; gate that responses cite persona-relevant articles. — FR-015, US2

**Checkpoint**: all CI gates green; ready for operational readiness.

---

## Phase 9 — Operational readiness (runbooks, dashboards, baseline)

**Depends on**: Phases 1, 6, 8. **Goal**: on-call SRE can operate Help; SC-009 baseline is captured.

- [ ] T-AA210 [P] [Gate] Author `docs/runbooks/help/on-call.md` — chat outage, snapshot publish failure, rollback procedure, alias-bind issues, AI Search throttling, redaction recogniser failure. — Constitution III, R1, R6, CHK128
- [ ] T-AA211 [P] [Gate] Author `docs/runbooks/help/snapshot-publish-rollback.md` — step-by-step including the dual-approval gate, the 5-min SLO, audit-event verification. — FR-011a, FR-011b, FR-011c
- [ ] T-AA212 [P] Author `docs/runbooks/help/screenshot-staleness.md` — bulk re-baseline workflow + grace period guidance. — FR-010a-AMEND, FR-010b, CHK076
- [ ] T-AA213 [P] [Gate] Author `docs/configuration/help-support-handoff.md` — per-tenant `SupportHandoffRecord` configuration, channel kinds, business-hours window, incident-mode auto-activation, SLAs. — FR-023a, FR-023a-AMEND, FR-023b, CHK122-CHK125
- [ ] T-AA214 [P] [Gate] **SC-009-AMEND baseline capture**: produce `specs/038-help-docs-chat/baselines/pre-launch-support.md` from a 2-week observation window immediately preceding launch — support-ticket volume tagged navigation/help-related, persona breakdown, median time-to-resolution. Without this baseline, SC-009 is unmeasurable. — SC-009-AMEND, CHK176, CHK183
- [ ] T-AA215 [P] Configure App Insights workbook `help-slis` and pin to dashboards used by SRE. — SC-007, plan §Telemetry
- [ ] T-AA216 [P] Configure metric alerts (per T-AA023): chat first-byte p95, snapshot publish duration, staleness backlog age, support-handoff SLA breach event count. Verify alert action group routes to on-call.
- [ ] T-AA217 [P] [Gate] Author quarterly chaos drill plan `docs/runbooks/help/chaos-drill-snapshot-rollback.md` — kill alias mid-publish; verify rollback completes within FR-011c 5-min SLO and audit event emitted. — R6, FR-011c
- [ ] T-AA218 [P] AU-residency attestation per release: invoke T-AA029 script and store output under `docs/attestations/help-{release}.json`. — FR-018, SC-011, CHK128, CHK181

---

## Phase 10 — Final integration & sign-off

**Depends on**: All prior phases. **Goal**: full `azd up` smoke succeeds; every CHK001–CHK136 verified; every SC has documented verification approach executed.

- [ ] T-AA219 [Gate] Run `azd up` from a clean environment; capture log under `docs/runbooks/help/azd-up-smoke-{date}.log`; smoke-check Help loads, chat answers, refuses, redacts; degraded mode behaves; snapshot publish + rollback work. — checkpoint, CHK104, quickstart
- [ ] T-AA220 [Gate] Walk every CHK001–CHK136 entry in `checklists/feature.md`; tick `[x]` only when evidence is linked. Any unchecked Gate item blocks release. — CHK001-CHK136
- [ ] T-AA221 [Gate] Execute SC-001 task-based usability test (≥20 participants across persona clusters); record results. — SC-001
- [ ] T-AA222 [Gate] Execute SC-002 LLM-eval gates (T-AA206 + T-AA207) on the release candidate; ≥90% in-scope pass + 100% refusal pass; archive results. — SC-002
- [ ] T-AA223 [Gate] Execute SC-003 fabrication-audit sample (T-AA208); zero verified fabrications; archive results. — SC-003
- [ ] T-AA224 [Gate] Execute SC-004 + SC-010 + SC-011 verification: tenant-isolation red-team (T-AA193); audit-log retrieval drill; AU-residency attestation (T-AA218). — SC-004, SC-010, SC-011
- [ ] T-AA225 [Gate] Execute SC-005, SC-006, SC-007, SC-008, SC-012 verification: screenshot inventory check; axe-core CI run; chat first-byte p95 telemetry review; persona time-to-competence test (≥80% finishing 15-min tour ≤15 min); staleness backlog SLA report. — SC-005, SC-006, SC-007, SC-008, SC-012
- [ ] T-AA226 [Gate] Final release sign-off recorded under `docs/runbooks/help/release-signoff-{date}.md` with dual approver identities (help-content owner + safety/governance lead) per FR-011b. — FR-011b, all CHK [Gate]

---

## Dependencies & Execution Order

### Phase dependencies

- 0 → (1, 2 in parallel) → (3, 4 partial parallel) → 5 → 7 → 6 → 8 → 9 → 10
- Phase 4 components do not require Phase 5 content to compile (use empty content fixtures); content is needed for Phase 8 e2e + LLM-eval suites.
- Phase 7 (build-time tooling) precedes Phase 6 (snapshot publication) because the snapshot publisher invokes the freshness and lang-attribute linters.

### Within phases

- Tasks marked `[P]` may run in parallel; non-`[P]` tasks must wait for sibling tasks listed above them in the same phase.
- All `[Gate]` tasks must be green before phase checkpoint.

### Parallel opportunities (examples)

- All Phase 2 model tasks (T-AA031 – T-AA046) — different files, no shared state.
- All Phase 5 persona-landing authoring (T-AA128 – T-AA143) — different files.
- All Phase 8a contract tests (T-AA182 – T-AA189) — different files.

### Implementation strategy

1. **MVP**: Phases 0 + 1 + 2 + 3 (chat backend) + 4 (UI shell) + 5a/5c (minimum content for 1 persona + 1 surface) + 6 (publishable snapshot) + 8a/8b minimal subset + 9 (basic runbook). Demonstrates the chat assistant grounded against a small corpus end-to-end.
2. **Incremental delivery**: add personas + screen-by-screen content per release; expand LLM-eval set; widen e2e coverage.
3. **Parallel team strategy**: `web` engineers own Phase 4; `api` + `agents` engineers own Phase 3 + 6; content authors own Phase 5; SRE owns Phase 1 + 9; QA owns Phase 8.

---

## Verification Matrix — FRs & SCs ↔ Tasks

> Coverage target: every FR-001 … FR-029b (plus 9 *-AMEND clauses) and every SC-001 … SC-012 (plus SC-009-AMEND) maps to at least one task. **Orphan count: 0**.

### Functional Requirements

| FR | Tasks |
|---|---|
| FR-001 | T-AA099, T-AA106, T-AA073 |
| FR-002 | T-AA031, T-AA100, T-AA114, T-AA128–T-AA143 |
| FR-003 | T-AA031, T-AA147–T-AA152, T-AA144 |
| FR-004 | T-AA128–T-AA137, T-AA034 |
| FR-005 | T-AA073, T-AA094, T-AA103, T-AA154, T-AA178 |
| FR-006 | T-AA015, T-AA032, T-AA108, T-AA144, T-AA145, T-AA176 |
| FR-007 | T-AA015, T-AA108, T-AA121, T-AA145, T-AA176 |
| FR-008 | T-AA032, T-AA108, T-AA115, T-AA146 |
| FR-009 | T-AA125, T-AA126, T-AA203, T-AA204 |
| FR-009a | T-AA033, T-AA104, T-AA153, T-AA175 |
| FR-009a-AMEND | T-AA007, T-AA175, T-AA179, T-AA185 |
| FR-010 | T-AA055, T-AA075, T-AA108, T-AA110, T-AA174 |
| FR-010a | T-AA032, T-AA051, T-AA055, T-AA174, T-AA176, T-AA186 |
| FR-010a-AMEND | T-AA055, T-AA174, T-AA177, T-AA180 |
| FR-010b | T-AA038, T-AA055, T-AA110, T-AA174, T-AA212 |
| FR-011 | T-AA009, T-AA035, T-AA063, T-AA064, T-AA068, T-AA169, T-AA091 |
| FR-011-AMEND | T-AA035, T-AA068, T-AA170 |
| FR-011a | T-AA014, T-AA028, T-AA053, T-AA054, T-AA086, T-AA164, T-AA165, T-AA171, T-AA191 |
| FR-011b | T-AA008, T-AA039, T-AA053, T-AA163, T-AA164, T-AA166, T-AA167, T-AA184, T-AA226 |
| FR-011c | T-AA014, T-AA053, T-AA074, T-AA089, T-AA164, T-AA165, T-AA168, T-AA173, T-AA191, T-AA217 |
| FR-011d | T-AA061, T-AA111, T-AA172, T-AA198 |
| FR-011d-AMEND | T-AA061, T-AA067, T-AA111, T-AA172, T-AA198 |
| FR-012 | T-AA043, T-AA069, T-AA072, T-AA107, T-AA109, T-AA178, T-AA202 |
| FR-013 | T-AA065, T-AA066, T-AA072, T-AA112, T-AA190, T-AA207 |
| FR-014 | T-AA065, T-AA066, T-AA069, T-AA072, T-AA112, T-AA208 |
| FR-015 | T-AA058, T-AA064, T-AA065, T-AA068, T-AA083, T-AA209 |
| FR-016 | T-AA062, T-AA116 |
| FR-017 | T-AA042, T-AA070, T-AA072, T-AA117, T-AA192 |
| FR-018 | T-AA018, T-AA019, T-AA022, T-AA029, T-AA218 |
| FR-019 | T-AA049, T-AA068, T-AA082, T-AA187, T-AA193 |
| FR-020 | T-AA042, T-AA059, T-AA090, T-AA093, T-AA183, T-AA192 |
| FR-021 | T-AA073, T-AA076, T-AA101, T-AA152, T-AA153, T-AA161 |
| FR-022 | T-AA037, T-AA072, T-AA113 |
| FR-022a | T-AA041, T-AA056, T-AA113, T-AA199 |
| FR-022a-AMEND | T-AA037, T-AA050, T-AA188 |
| FR-023 | T-AA066, T-AA077, T-AA112, T-AA119 |
| FR-023a | T-AA040, T-AA057, T-AA077, T-AA119, T-AA213 |
| FR-023a-AMEND | T-AA040, T-AA057, T-AA195, T-AA213 |
| FR-023b | T-AA023, T-AA040, T-AA057, T-AA090, T-AA195, T-AA213 |
| FR-024 | T-AA132, T-AA151, T-AA156, T-AA159 |
| FR-025 | T-AA065, T-AA136, T-AA162 |
| FR-026 | T-AA084, T-AA095, T-AA098, T-AA107, T-AA124, T-AA194, T-AA205 |
| FR-026a | T-AA095, T-AA194 |
| FR-026a-AMEND | T-AA098, T-AA118, T-AA194, T-AA205 |
| FR-026b | T-AA095, T-AA194 |
| FR-027 | T-AA034, T-AA058, T-AA097, T-AA100, T-AA196 |
| FR-027-AMEND | T-AA034, T-AA044, T-AA058 |
| FR-028 | T-AA058, T-AA083, T-AA097, T-AA100, T-AA114, T-AA196 |
| FR-029 | T-AA013, T-AA036, T-AA042, T-AA059 |
| FR-029a | T-AA060, T-AA197 |
| FR-029b | T-AA060, T-AA197 |

### Success Criteria

| SC | Tasks |
|---|---|
| SC-001 | T-AA221 |
| SC-002 | T-AA071, T-AA206, T-AA207, T-AA222 |
| SC-003 | T-AA208, T-AA223 |
| SC-004 | T-AA193, T-AA224 |
| SC-005 | T-AA145, T-AA225 |
| SC-006 | T-AA203, T-AA225 |
| SC-007 | T-AA016, T-AA023, T-AA215, T-AA225 |
| SC-008 | T-AA120, T-AA225 |
| SC-009 / SC-009-AMEND | T-AA011, T-AA214 |
| SC-010 | T-AA059, T-AA060, T-AA197, T-AA224 |
| SC-011 | T-AA029, T-AA218, T-AA224 |
| SC-012 | T-AA174, T-AA216, T-AA225 |

**Orphan FRs**: 0.
**Orphan SCs**: 0.

---

## Notes

- `[P]` tasks may run in parallel within a phase but never across a phase boundary unless their inputs already exist.
- `[Gate]` tasks are release-blockers and align 1:1 with the `[Gate]` items in `checklists/feature.md`.
- Every task lists its file path(s); add new files only at the listed paths to keep phase boundaries clean.
- All Azure resources MUST stay in `australiaeast` (primary) / `australiasoutheast` (paired DR); no exceptions.
- AVM-first: where an AVM module exists for a resource type, prefer it over hand-rolled Bicep; document any exception in inline comment + ADR.
- Snapshot pipeline is the ONLY mechanism to publish or withdraw Help content (no in-place edits); both publish and rollback require dual sign-off (FR-011b).
- Negative feedback NEVER auto-disables content (FR-022a / Constitution Principle I).
