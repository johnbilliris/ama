# Phase 0 — Research: In-Product Help Documentation & Grounded Chat Assistant

**Spec**: [`spec.md`](./spec.md) | **Plan**: [`plan.md`](./plan.md) | **Date**: 2026-05-11

This document records option analysis for each design unknown identified during plan synthesis. Every "Decision" is binding for Phase 1 (`data-model.md`, `contracts/`, `quickstart.md`) and downstream `/speckit.tasks`. Persona ownership is in parentheses.

All NEEDS CLARIFICATION items raised during planning have been resolved (see also spec.md §Clarifications Pass 1 / Pass 2 / Pass 3).

---

## §A. Help authoring & storage backend (software-developer, data-engineer, product-owner-ba)

**Question**: Where does authoritative Help content live, and how does it reach end users + the chat retriever?

**Options considered**

1. **Headless CMS** (e.g., Contentful AU, Strapi self-hosted). *Rejected* — introduces a new tenant of state outside Cosmos, violates Australian-residency simplicity, and forces a separate auth model. Conflicts with reuse-first principle.
2. **Cosmos-as-CMS** — store article body in Cosmos, edit via in-app authoring screens. *Rejected* — couples editorial workflow to runtime Cosmos costs, no Git-grade review/PR workflow, harder to peer-review for safety-relevant content (Constitution Principle I).
3. **MDX in repo** (`apps/web/src/content/help/**`), built into both Next.js static routes and AI Search documents at CI time; Cosmos `help_articles` stores **published metadata** only. *Selected*.

**Decision**: MDX in repo (Option 3). Authoring is a normal pull request; CODEOWNERS-style dual-review is naturally enforced; the same artefact feeds both the UI and the chat retriever; the metadata projection in Cosmos enables fast persona-tag queries and freshness flags without re-rendering MDX.

**Rationale**: Aligns with the project's "config-as-code" pattern (specs, ADRs, AIDR docs all live in repo); reuses GitHub PR review as the dual-approval gate for Constitution Principle I (no silencing); MDX supports rich annotated screenshots, callouts, and accessibility primitives natively; rendering is incremental-static via Next.js, satisfying the <500 ms p95 article render goal; no new service or storage tier required.

**Alternatives considered**: as above.

---

## §B. Snapshot publication & versioning (principal-engineer, infrastructure-devops)

**Question**: How are Help-approved snapshots of the corpus published, versioned, and rolled back?

**Options considered**

1. **In-place index updates** with optimistic concurrency. *Rejected* — incompatible with FR-011a immutability and FR-011c rollback; rollback would require a re-index (minutes to hours).
2. **Index-per-snapshot + alias swap (blue/green)**, mirroring spec-036 FR-RAG-IDX-04. *Selected*.
3. **Multi-tenant single index with `snapshot_id` filter**. *Rejected* — index size grows unboundedly; rollback requires query-rewrite rather than config-flip; harder to delete superseded content under data-minimisation principles.

**Decision**: Index-per-snapshot + atomic alias swap (Option 2). Each publish stamps `help-corpus-{snapshot_id}` and updates alias `help-corpus-active`. Rollback re-binds alias to a prior `snapshot_id` — pure config flip ≤5 min (FR-011c); spec-029 FR-008 SLO honoured.

**Approval mechanics**: Two distinct CODEOWNERS groups must approve any PR that touches `apps/web/src/content/help/**` OR the `specs/` snapshot manifest: `@ama/help-content-owners` AND `@ama/safety-or-governance-leads` (FR-011b mirrors spec-005 FR-015 dual-authority). Approver identities + timestamps are persisted in `SnapshotRecord.approvers[]` and emitted to the chat audit log on publish (`audit.snapshot_published`) and rollback (`audit.snapshot_rollback`).

**Rationale**: Atomic, reversible, auditable; reuses an existing in-repo pattern; aligns with Constitution Principle IV (transparency) and Non-Negotiable #1 (human-in-the-loop).

**Alternatives considered**: as above.

---

## §C. Chat grounding pipeline — Foundry agent vs. direct RAG (ai-ml-engineer, principal-engineer)

**Question**: Should the Help chat be implemented as a Microsoft Foundry agent (spec-036 style) or as a hand-rolled retrieve-then-generate loop in `apps/api`?

**Options considered**

1. **Hand-rolled** retrieve+prompt loop in FastAPI. *Rejected* — duplicates spec-036 retrieval + audit + carve-out logic; diverges from the "single integration point" design of `apps/agents/common/retrieval_client.py`; harder to evolve consistently with the rest of the agent fleet.
2. **Foundry agent named `help_assistant`**, configured with retrieval-only tooling against alias `help-corpus-active`, reusing `model_gateway` + `llm_client` + `foundry_chat_client`. *Selected*.
3. **Reuse the spec-024 simulation chat agent** with a help-mode flag. *Rejected* — different corpus, different refusal policy, different retention; the coupling would muddy both surfaces.

**Decision**: Foundry agent `help_assistant` (Option 2). One agent per environment (dev / test / prod). Configured with:

- **Tools**: retrieval against alias `help-corpus-active` only (no internet, no python interpreter, no other tools).
- **Inference parameters**: `temperature: 0.0`, `top_p: 0.1`, `max_output_tokens: 1500` (tight, reduces fabrication).
- **System prompt**: refusal-first; "answer only from retrieved chunks; cite every claim; refuse if no chunks; refuse if any chunk is from outside the user's tenant scope; persona = {persona_id}; jurisdiction = {jurisdiction_codes}".
- **Audit**: every turn emits a `ChatAuditEntry` via `apps/agents/common/audit.py`.
- **Carve-out registry**: entry `help_assistant` pinned to `region: australiaeast` (no §NN-2 carve-out invoked); `model_gateway` redaction still applied as defence-in-depth.

**Foundry agent name**: **`help_assistant`** (lowercase + underscore, matching spec-036 conventions).

**Rationale**: Maximum reuse of spec-036 plumbing; consistent observability + audit; one fewer code path to maintain; carve-out registry already enforces residency.

**Alternatives considered**: as above.

---

## §D. Screenshot capture, storage & staleness detection (ux-designer, software-developer, qa-test-engineer)

**Question**: How are annotated screenshots captured, stored, themed, and detected as stale?

**Options considered**

1. **Manual screenshots** + manual staleness review. *Rejected* — does not scale across ≥18 surfaces × 2 themes × ongoing UI changes; will not meet SC-012 (90% within one release).
2. **Playwright-driven capture** with deterministic `screen_id_hash`, paired light/dark passes; storage in `help-screenshots` blob container. *Selected*.
3. **Component-screenshot via Storybook**. *Rejected* — does not faithfully capture multi-component pages (Disaster Mapper, Governance Dashboard).

**Decision**: Playwright capture script `tools/help/capture_screenshots.ts` (Option 2). For each `screen_id`:

- Loads the route in test mode against a seeded fixture tenant.
- Computes `screen_id_hash = sha256(route_id + ordered DOM-fingerprint of numbered callout anchors)` — the FR-010a binding signal.
- Captures `light.webp` + `dark.webp` (and `.png` fallbacks for clipboard) plus `<screen_id>.alt.json` containing per-callout alt text and the keyboard-equivalent steps.
- Uploads to `help-screenshots/{tenant_id|global}/{screen_id}/...` (immutability policy 30 d, soft-delete 90 d).
- Updates `screenshot_registry` Cosmos doc with manifest + `screen_id_hash`.

**Build-time freshness check**: `tools/help/check_screenshot_freshness.py` re-computes `screen_id_hash` from the live build and raises a `StalenessFlag` row on mismatch. Route renames detected via the routes registry's `previous_route_id` map trigger a bulk re-baseline workflow (FR-010a-AMEND).

**Rationale**: Deterministic signal (FR-010a binding contract); CI-enforceable; light/dark coverage automatic; no human guesswork.

**Alternatives considered**: as above.

---

## §E. PII redaction reuse from spec-036 (security-engineer, ai-ml-engineer, compliance-auditor)

**Question**: Reuse the spec-036 `model_gateway.py` data-minimisation gateway for chat input, or introduce a Help-specific redactor?

**Options considered**

1. **New Help-specific Presidio pipeline**. *Rejected* — duplicate maintenance burden; risk of recogniser drift; violates reuse-first principle.
2. **Reuse `apps/agents/common/model_gateway.py` as-is**, calling `gateway.process(input, region="australiaeast")` from `help_chat.py`. *Selected*.
3. **Bypass the gateway for AU-region chat** since data residency holds. *Rejected* — defence in depth: redacting the audit log itself is a privacy benefit; FR-017 explicitly mandates user notification when redaction occurs.

**Decision**: Reuse `model_gateway.py` unchanged (Option 2). The Help chat router calls the gateway on every inbound user message; on any redaction, the response carries `meta.redaction_notice` and the UI renders an inline banner ("We redacted personal data from your message before answering."). The audit log (`ChatAuditEntry.redacted_input`) only ever contains the post-redaction form.

**Rationale**: Single control surface for PII across the platform; APP 11 retention for 7 y is satisfied (FR-029); one less moving part.

**Alternatives considered**: as above.

---

## §F. Degraded-mode caching (sre-engineer, software-developer)

**Question**: How is Help made available in degraded-connectivity mode without exceeding device storage and without introducing a parallel cache layer?

**Options considered**

1. **No offline cache**. *Rejected* — violates FR-026 and Constitution Non-Negotiable #5 (graceful degradation).
2. **Service-Worker pre-caching** of the entire corpus. *Rejected* — exceeds the ≤500 MB envelope shared with spec-036 Field Coordinator cache; many Help articles never viewed.
3. **`idb`-backed lazy cache** of previously-viewed articles + full glossary + curated FAQ topics, sharing the spec-036 `offline_cache.py` envelope. *Selected*.

**Decision**: Lazy `idb` cache (Option 3). Implementation reuses the `apps/agents/common/offline_cache.py` envelope (≤500 MB / 14-day TTL) — Help articles count toward the same shared cap, not in addition (FR-026b). Chat panel hides behind the standard "unavailable in degraded mode" banner per FR-026a-AMEND. On reconnect, an audit-logged refresh runs (mirrors spec-036 FR-RAG-LS-02). Articles past TTL render with a "may be stale — last cached `<YYYY-MM-DD>`" notice.

**Rationale**: Reuses an existing primitive; honours the shared envelope; degrades safely; preserves Constitution Principle I (life-safety guidance remains readable offline).

**Alternatives considered**: as above.

---

## §G. Accessibility tooling (accessibility-tester, ux-designer)

**Question**: Which tools enforce WCAG 2.2 AA (FR-009) and the embedded-`lang` requirement (FR-009a / FR-009a-AMEND)?

**Options considered**

1. **Manual review only**. *Rejected* — non-repeatable; cannot meet SC-006 (zero Level A/AA at release).
2. **Single CI gate** with axe-core after deploy. *Rejected* — no authoring-time feedback; `lang` violations slip through to production.
3. **Three-gate stack**: authoring-time MDX rehype validator + build-time CI lint + runtime Playwright + axe-core e2e on every Help route. *Selected*.

**Decision**: Three-gate stack (Option 3).

- **Authoring time** — MDX rehype plug-in `tools/help/rehype-lang-attr.ts` rejects save / commit if any glossary-tagged non-English fragment lacks a `lang` attribute (FR-009a-AMEND gate (a)).
- **Build time** — `tools/help/lint_lang_attributes.py` runs on the built static HTML in CI (FR-009a-AMEND gate (b)); `pa11y-ci` runs on a representative sample of pages.
- **Runtime** — Playwright + `@axe-core/playwright` runs in `apps/web/__tests__/e2e/help/a11y.wcag22aa.spec.ts` on every Help route; zero Level A/AA violations to merge (SC-006).

Cultural-authority enforcement: the `cultural_authority_registry` (existing `apps/agents/common/cultural_authority_registry.py`) is consulted before publishing any Help article that references Aboriginal & Torres Strait Islander language items, mirroring the spec-005 / Constitution §V-B cultural-authority pattern.

**Rationale**: Defence in depth; fastest feedback at authoring time; CI is fail-closed.

**Alternatives considered**: as above.

---

## §H. Negative-feedback handling (principal-engineer, product-owner-ba, compliance-auditor)

**Question**: How is negative chat/article feedback closed without violating Constitution Principle I (no silencing)?

**Decision**: Queue-only — never auto-disable. Per FR-022a, negative ratings enqueue `ContentReviewBacklogItem` rows scoped to the user's tenant; ≥3 negatives in a 30-day rolling window auto-promote to `needs_review`; pattern identity is `(question_intent_cluster_id, ordered_set(citation_source_ids))` (FR-022a-AMEND). Only human review via the snapshot dual-approval gate (FR-011b) may withdraw or rewrite content. (No options analysis — this is constitutionally bound.)

---

## §I. Tenant isolation in retrieval (security-engineer, data-engineer)

**Decision**: AI Search filter clause `tenant_id eq @tenant or scope eq 'global'` is hard-coded inside the retrieval-service wrapper used by `help_assistant`; the `@tenant` parameter is taken from the authenticated principal's tenant claim on every call (no caller can override). The `scope` field is set at index time — `help_articles` and `chat_sessions` are tenant-scoped, while `docs/aidr/**` and `docs/corpus/**` are `global` (FR-011-AMEND). A red-team integration test (`tests/integration/help/test_tenant_isolation.py`) executes a multi-tenant probe each CI run.

---

## §J. Persona-context resolution (software-developer, ux-designer, security-engineer)

**Decision**: Default persona = highest-authority operational role from the IdP role claim (FR-027 + FR-027-AMEND back-references spec-021 FR-025). Override via persona switcher to any entitled role. Active persona persisted on every chat turn in `ChatAuditEntry.persona_id` + `ChatAuditEntry.persona_source` ∈ {`idp_default`, `user_override`}. Multi-role landing pages render the union of entitled persona tiles ordered by AIIMS authority rank (highest first); chat uses **only** the active persona — never the union — to avoid leaking guidance scoped to an unentered role (FR-028).

---

## Outstanding NEEDS CLARIFICATION

**None.** All Pass 1 / Pass 2 / Pass 3 spec clarifications are bound to FRs; all Phase 0 unknowns enumerated in plan.md §Architecture have decisions above.
