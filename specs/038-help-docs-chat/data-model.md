# Phase 1 — Data Model: In-Product Help Documentation & Grounded Chat Assistant

**Spec**: [`spec.md`](./spec.md) | **Plan**: [`plan.md`](./plan.md) | **Research**: [`research.md`](./research.md) | **Date**: 2026-05-11

This document defines the entities introduced by spec-038, their Pydantic v2 source-of-truth shapes (in `packages/domain/src/ama_domain/`), the corresponding TypeScript twins (in `packages/domain/src/help/`), Cosmos partition keys + TTLs, and the AI Search index schema for the Help corpus.

All entities follow existing conventions:

- Pydantic v2 `BaseModel` with `model_config = ConfigDict(extra="forbid", frozen=False)`.
- Cosmos partition key is `/tenant_id` (matches `cosmos-simulation-containers.bicep` and spec-024 / spec-036). Global-scope rows use `tenant_id = "__global__"`.
- Every entity carries `id: str` (ULID), `created_at`/`updated_at: datetime` (UTC, ISO 8601), and `etag: str | None` for optimistic concurrency where mutations are allowed.
- TS twins are `type` aliases generated 1:1 from the Pydantic schema; the build CI verifies they stay in sync.
- "Citation" is reused from the existing `apps/agents/common/citation_filter.py` / `packages/domain/src/ama_domain/citation.py` (spec-036) — not redefined here.

---

## Entity catalogue

| # | Entity | Cosmos container | Partition key | TTL | Purpose |
|---|---|---|---|---|---|
| 1 | `HelpArticle` | `help_articles` | `/tenant_id` | none | Published article metadata (body in MDX + Search) |
| 2 | `AnnotatedScreenshot` | `screenshot_registry` | `/tenant_id` | none | Manifest of stored screenshot variants + `screen_id_hash` |
| 3 | `GlossaryTerm` | `help_articles` (kind=`glossary`) | `/tenant_id` | none | Canonical AIIMS / AIDR / jurisdictional / Hub term |
| 4 | `PersonaHelpProfile` | `help_articles` (kind=`persona`) | `/tenant_id` | none | Persona-aware landing-page tile set |
| 5 | `KnowledgeCorpusSource` | `snapshot_records` (sub-doc) | `/tenant_id` | none | Registered source admitted into a snapshot |
| 6 | `ChatSession` | `chat_sessions` | `/tenant_id` | 30 days | User-visible conversation transcript (FR-029) |
| 7 | `Citation` | (reused from spec-036 `citation.py`) | n/a | n/a | Inline citation envelope returned with chat answers |
| 8 | `HelpFeedback` | `content_review_backlog` (linked) | `/tenant_id` | 7 years | Helpfulness rating + comment per article or chat turn |
| 9 | `StalenessFlag` | `screenshot_registry` (sub-doc) | `/tenant_id` | none | Raised by build pipeline on `screen_id_hash` mismatch |
| 10 | `SnapshotRecord` | `snapshot_records` | `/tenant_id` | none (immutable) | Versioned, dual-approved Help-corpus snapshot |
| 11 | `SupportHandoffRecord` | `support_handoff_config` | `/tenant_id` | none | Per-tenant escalation destination (FR-023a) |
| 12 | `ContentReviewBacklogItem` | `content_review_backlog` | `/tenant_id` | 7 years | Aggregated negative-feedback work item (FR-022a) |
| 13 | `ChatAuditEntry` | `chat_audit_log` | `/tenant_id` | **7 years** (Privacy Act APP 11 / spec-001 NFR-012) | Append-only system-of-record for every chat turn |

---

## 1. `HelpArticle`

```python
# packages/domain/src/ama_domain/help_article.py
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

ArticleKind = Literal["article", "playbook", "faq", "glossary", "persona"]
ArticleStatus = Literal["draft", "published", "withdrawn"]


class HelpArticle(BaseModel):
    """Published Help-article metadata. Body is MDX in `apps/web/src/content/help/**`;
    full text is indexed into AI Search. Cosmos stores metadata only."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="ULID; matches MDX file slug")
    tenant_id: str = Field(..., description="`__global__` for cross-tenant articles")
    kind: ArticleKind
    title: str
    slug: str
    persona_tags: list[str] = Field(default_factory=list, description="persona ids — FR-002")
    sector_tags: list[str] = Field(default_factory=list, description="sector cluster ids")
    surface_tags: list[str] = Field(default_factory=list, description="route ids — for `Help on this screen`")
    jurisdiction_tags: list[str] = Field(default_factory=list, description="ISO + state codes")
    domain: Literal[
        "getting-started", "persona-workflow", "screen-by-screen", "simulation-playbook",
        "agent-playbook", "audit-observer", "accessibility", "troubleshooting", "glossary",
    ]
    body_uri: HttpUrl | str = Field(..., description="repo-relative MDX path or signed URL")
    screenshot_ids: list[str] = Field(default_factory=list)
    snapshot_id: str = Field(..., description="SnapshotRecord.id this article was last published under")
    version: int = Field(default=1, ge=1)
    status: ArticleStatus = "published"
    staleness_flag_id: str | None = None
    last_reviewed_at: datetime
    created_at: datetime
    updated_at: datetime
    etag: str | None = None
```

**TS twin**: `packages/domain/src/help/help-article.ts`.

**Validation rules**: `id == slug` (lowercase kebab); `persona_tags` ∈ enumerated 10 ops + 6 sector clusters (FR-002); `kind=="glossary"` requires non-empty `glossary_term_links` (cross-link, see GlossaryTerm); `status` transitions are append-only via the snapshot pipeline.

---

## 2. `AnnotatedScreenshot`

```python
class AnnotatedScreenshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str  # ULID
    tenant_id: str  # usually `__global__`
    screen_id: str  # logical screen identifier, e.g. `disaster-mapper.main`
    route_id: str   # Next.js route id, e.g. `/disasters/[id]`
    previous_route_id: str | None = None  # FR-010a-AMEND bulk re-baseline
    screen_id_hash: str  # sha256 — FR-010a binding signal
    light_blob_uri: str
    dark_blob_uri: str
    alt_text_blob_uri: str  # JSON sidecar with per-callout alt text + keyboard steps
    callouts: list["Callout"]
    captured_at: datetime
    captured_by: str  # author identity
    article_ids: list[str]
    staleness_flag_id: str | None = None
    created_at: datetime
    updated_at: datetime


class Callout(BaseModel):
    model_config = ConfigDict(extra="forbid")
    number: int = Field(..., ge=1)
    anchor_dom_path: str  # used in screen_id_hash computation
    alt_text: str
    keyboard_steps: list[str]
```

---

## 3. `GlossaryTerm`

```python
class GlossaryTerm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str  # canonical slug, e.g. `aiims.controller`
    tenant_id: str  # usually `__global__`
    term: str
    definition: str  # markdown
    domain: Literal["aiims", "aidr", "jurisdictional", "hub"]
    aliases: list[str] = Field(default_factory=list)
    related_article_ids: list[str] = Field(default_factory=list)
    lang: str = "en"  # if non-English, MUST carry correct BCP-47 tag — FR-009a
    cultural_authority_ref: str | None = None  # cultural_authority_registry id when applicable
    created_at: datetime
    updated_at: datetime
```

---

## 4. `PersonaHelpProfile`

```python
class PersonaHelpProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str  # persona id e.g. `incident-commander`
    tenant_id: str  # `__global__` unless tenant overrides
    persona_kind: Literal["operational", "sector"]
    authority_rank: int  # mirrors spec-021 FR-025 — FR-027-AMEND single shared registry
    landing_tile_ids: list[str]
    recommended_workflow_article_ids: list[str]
    decision_rights_summary: str
    handoff_destinations: list[str]
    chat_starter_prompts: list[str]
    created_at: datetime
    updated_at: datetime
```

---

## 5. `KnowledgeCorpusSource`

```python
class KnowledgeCorpusSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    snapshot_id: str
    source_kind: Literal["help_article", "docs_corpus", "docs_aidr", "spec"]
    source_path: str  # repo-relative
    spec_id: str | None = None
    spec_version: str | None = None
    spec_status: Literal["Active", "Implemented"] | None = None  # FR-011 admission gate
    content_hash: str  # sha256
    classification: Literal["OFFICIAL", "OFFICIAL: SENSITIVE"] = "OFFICIAL"
    scope: Literal["tenant", "global"]  # FR-011-AMEND
    indexed_at: datetime
```

---

## 6. `ChatSession`

```python
class ChatSession(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    tenant_id: str
    user_id: str  # IdP subject claim
    persona_id: str
    persona_source: Literal["idp_default", "user_override"]
    jurisdiction_codes: list[str]
    snapshot_id_at_open: str
    turns: list["ChatTurn"]
    started_at: datetime
    last_turn_at: datetime
    # Cosmos default-TTL = 30 days (FR-029)


class ChatTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    turn_index: int = Field(..., ge=0)
    user_input_redacted: str
    redaction_occurred: bool
    answer_text: str
    citations: list[str]  # Citation ids — see spec-036 citation_filter
    refusal_reason: Literal[
        "out_of_scope", "cross_tenant", "no_corpus_match", "pii_blocked",
        "above_official_classification", "deprecated_no_replacement",
    ] | None = None
    pattern_id: str  # `(intent_cluster, citation_set)` tuple hash — FR-022a-AMEND
    feedback_id: str | None = None
    audit_entry_id: str
    created_at: datetime
```

---

## 8. `HelpFeedback`

```python
class HelpFeedback(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    tenant_id: str
    target_kind: Literal["article", "chat_turn"]
    target_id: str  # HelpArticle.id OR f"{ChatSession.id}:{turn_index}"
    rating: Literal["helpful", "not_helpful"]
    comment: str | None = None
    submitted_by: str
    pattern_id: str | None = None  # populated for chat_turn — FR-022a-AMEND
    created_at: datetime
```

---

## 9. `StalenessFlag`

```python
class StalenessFlag(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    tenant_id: str
    target_kind: Literal["screenshot", "article"]
    target_id: str
    raised_reason: Literal["screen_id_hash_mismatch", "route_renamed", "manual"]
    raised_at: datetime
    grace_release_id: str  # release tag at which the article must be downgraded if still stale (FR-010b)
    cleared_at: datetime | None = None
    cleared_by: str | None = None
    bulk_baseline_id: str | None = None  # FR-010a-AMEND group id
```

---

## 10. `SnapshotRecord` (immutable)

```python
class SnapshotRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str  # snapshot id, e.g. `2026.05.11-01`
    tenant_id: str  # `__global__` for the canonical snapshot; per-tenant overrides allowed
    sources: list[KnowledgeCorpusSource]
    ai_search_index_name: str  # `help-corpus-{id}`
    approvers: list["Approver"] = Field(..., min_length=2)  # FR-011b dual sign-off
    published_at: datetime
    published_by: str
    rollback_of: str | None = None  # if this publish was a rollback, points at the predecessor


class Approver(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    identity: str  # IdP subject
    role: Literal["help_content_owner", "safety_lead", "governance_lead"]
    approved_at: datetime
```

**Validation**: at least one approver of role `help_content_owner` AND at least one of `safety_lead | governance_lead` (FR-011b). `frozen=True` enforces immutability.

---

## 11. `SupportHandoffRecord`

```python
class SupportHandoffRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    tenant_id: str
    channel_kind: Literal["email", "shared_mailbox", "on_call_rotation", "chat_link"]
    address: str
    business_hours_window: str  # cron-like or `24x7` — FR-023a
    incident_mode_channel: "SupportHandoffRecord | None" = None
    auto_activate_on_nema_level3: bool = True  # FR-023a-AMEND
    manual_override_active: bool = False
    sla_routine_business_hours: int = 4
    sla_incident_minutes: int = 5  # FR-023b
    created_at: datetime
    updated_at: datetime
```

---

## 12. `ContentReviewBacklogItem`

```python
class ContentReviewBacklogItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    tenant_id: str
    target_kind: Literal["article", "chat_pattern"]
    target_id: str  # HelpArticle.id OR pattern_id (FR-022a-AMEND)
    feedback_ids: list[str]
    negative_count_30d: int = 0
    status: Literal["new", "needs_review", "in_review", "resolved", "wont_change"] = "new"
    auto_promoted_at: datetime | None = None  # FR-022a ≥3-in-30-days
    resolved_by: str | None = None
    resolved_snapshot_id: str | None = None  # snapshot that closed the loop, if any
    created_at: datetime
    updated_at: datetime
```

---

## 13. `ChatAuditEntry` (append-only, 7-year retention)

```python
class ChatAuditEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    tenant_id: str
    chat_session_id: str
    turn_index: int
    user_id: str
    persona_id: str
    persona_source: Literal["idp_default", "user_override"]
    jurisdiction_codes: list[str]
    snapshot_id: str
    foundry_agent_name: Literal["help_assistant"] = "help_assistant"
    user_input_redacted: str
    redaction_occurred: bool
    retrieved_citation_ids: list[str]
    response_text: str
    refusal_reason: str | None = None
    pattern_id: str
    gateway_decision: Literal["allow", "deny", "redact"]  # mirrors spec-036 model_gateway audit field
    created_at: datetime  # immutable; partition key /tenant_id
```

Cosmos container `chat_audit_log` is configured with default TTL = `7 * 365 * 24 * 3600` seconds; auto-purge on TTL expiry. Append-only at the application layer (no UPDATE/DELETE permitted by the role-assigned managed identity used by `help_chat.py`).

---

## AI Search index schema — `help-corpus-{snapshot_id}`

One **immutable** index per snapshot; alias `help-corpus-active` swung atomically on publish/rollback (FR-011c). Schema (S1 tier; AU East):

| Field | Type | Searchable | Filterable | Facetable | Sortable | Vector? | Notes |
|---|---|---|---|---|---|---|---|
| `id` | `Edm.String` (key) | — | — | — | — | — | `{source_kind}:{content_hash}` |
| `tenant_id` | `Edm.String` | — | ✅ | ✅ | — | — | always set; `__global__` for shared sources |
| `scope` | `Edm.String` | — | ✅ | ✅ | — | — | `tenant` \| `global` (FR-011-AMEND) |
| `source_kind` | `Edm.String` | — | ✅ | ✅ | — | — | `help_article` \| `docs_corpus` \| `docs_aidr` \| `spec` |
| `source_path` | `Edm.String` | — | ✅ | — | — | — | repo-relative |
| `spec_id` / `spec_version` / `spec_status` | `Edm.String` | — | ✅ | ✅ | — | — | populated for `source_kind=spec`; admission requires `spec_status ∈ {Active, Implemented}` (FR-011) |
| `persona_tags` | `Collection(Edm.String)` | — | ✅ | ✅ | — | — | persona-aware retrieval bias (FR-015) |
| `jurisdiction_tags` | `Collection(Edm.String)` | — | ✅ | ✅ | — | — | jurisdiction filter |
| `surface_tags` | `Collection(Edm.String)` | — | ✅ | ✅ | — | — | "Help on this screen" deep-link mapping |
| `title` | `Edm.String` | ✅ | — | — | ✅ | — | analyzer `en.microsoft` |
| `body` | `Edm.String` | ✅ | — | — | — | — | analyzer `en.microsoft` |
| `body_vector` | `Collection(Edm.Single)` (dim per spec-036 `foundry_query_embedder`) | — | — | — | — | ✅ | hybrid retrieval (BM25 + vector + RRF — `apps/agents/common/retrieval_client.py`) |
| `heading_anchor` | `Edm.String` | — | ✅ | — | — | — | citation deep-link target |
| `classification` | `Edm.String` | — | ✅ | ✅ | — | — | `OFFICIAL` only admitted (FR-011 / spec-036 ceiling) |
| `lang` | `Edm.String` | — | ✅ | ✅ | — | — | BCP-47; default `en` |
| `last_reviewed_at` | `Edm.DateTimeOffset` | — | ✅ | — | ✅ | — | for staleness sort |

**Hard tenant-isolation filter** (applied by `retrieval_client` wrapper): `tenant_id eq @tenant or scope eq 'global'` (FR-019, FR-011-AMEND). The `@tenant` parameter is taken from the authenticated principal — never user-controlled.

**Indexing pipeline**: orchestrated by `apps/ingest-runner --mode help-snapshot`; idempotent on `(snapshot_id, source_id, content_hash)`.

---

## Bicep mapping (new module `infra/bicep/modules/cosmos-help-containers.bicep`)

| Container | Partition key | TTL | Notes |
|---|---|---|---|
| `help_articles` | `/tenant_id` | none | composite indexes on `(persona_tags, surface_tags)` and `(snapshot_id, status)` |
| `screenshot_registry` | `/tenant_id` | none | unique key constraint on `(tenant_id, screen_id)` |
| `chat_sessions` | `/tenant_id` | 30 days (default-TTL = 2,592,000 s) | FR-029 (operational data class — spec-001 NFR-002 ≤30 d cap) |
| `chat_audit_log` | `/tenant_id` | 7 years (default-TTL = 220,752,000 s) | FR-029 / APP 11 |
| `snapshot_records` | `/tenant_id` | none | immutable; managed identity has insert-only; analytics store enabled |
| `support_handoff_config` | `/tenant_id` | none | one root doc per tenant |
| `content_review_backlog` | `/tenant_id` | 7 years | aligns with audit retention |

All containers use autoscale RU between 400 (min) and 4000 (max) at launch; revisit per spec-036 70%-capacity alerting pattern.
