"""Spec 036 — RetrievalService implementation (T075–T079).

The shared retrieval client invoked by all grounded agents and the simulation
Controller. Implements ``contracts/retrieval-service.md`` §1 (Protocol),
§2 (semantics: jurisdiction union, RRF fusion, classification ceiling, empty
result), §5 (failure modes), and §6 (hermetic test stub).

This module is the **single integration point** for retrieval: every agent
constructs an ``AzureSearchRetrievalService`` (or, in tests, a
``FakeRetrievalService``) and calls ``await service.retrieve(req)``. No agent
talks to ``azure.search.documents`` directly.

Structure:

* ``RetrievalService`` — runtime-checkable Protocol (FR-RAG-AG-01).
* ``AzureSearchRetrievalService`` — production implementation. Hybrid
  retrieval (BM25 + vector) with Reciprocal Rank Fusion (R-06; default vector
  weight 0.7 / lexical 0.3). Lazy SDK import to keep cold-start fast.
* ``FakeRetrievalService`` — hermetic stub for contract / integration tests.
  Uses an in-memory fixture; honours jurisdiction-union semantics so tests
  exercise the same surface as production.
* ``ClassificationCeilingError`` — raised when a duck-typed caller bypasses
  the pydantic ``Literal["OFFICIAL"]`` guard with a higher classification.
* ``RRF_VECTOR_WEIGHT_DEFAULT`` / ``RRF_LEXICAL_WEIGHT_DEFAULT`` — exposed
  module constants so contract tests can pin the R-06 default.

The constructor-injectable seam (FR-RAG-FM-07) is preserved: agents pass a
custom ``foundry_chat_client`` (for embeddings) and a custom ``search_client``
(for hybrid query) to ``AzureSearchRetrievalService.__init__`` in tests.

Per-agent quotas (R-09) and 5-minute LRU cache (R-06) are implemented
inline; see ``_QuotaLimiter`` and ``_QueryCache`` for details.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import time
from collections import OrderedDict
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Module constants — R-06 RRF default weights + R-03 jurisdiction union
# --------------------------------------------------------------------------- #


RRF_VECTOR_WEIGHT_DEFAULT: float = 0.7
"""Default RRF vector-arm weight (R-06). Pinned by contract test T060."""


RRF_LEXICAL_WEIGHT_DEFAULT: float = 0.3
"""Default RRF lexical-arm weight (R-06). Pinned by contract test T060."""


_JURISDICTION_UNION_BOOST: frozenset[str] = frozenset({"national", "aidr"})
"""Server-side union added to every request's jurisdictions (FR-RAG-AG-04, R-03, US7)."""


_RRF_K: int = 60
"""RRF k-parameter (R-06). Standard value from the original paper."""


_QUOTA_SOFT_QPS: float = 10.0
_QUOTA_HARD_QPS: float = 25.0
"""Per-agent QPS budgets (R-09 / contract §3)."""


_CACHE_TTL_SECONDS: float = 300.0
"""5-minute LRU cache (R-06; contract §1 RetrievalResult.cache_hit)."""


_CACHE_MAX_ENTRIES: int = 1024
"""Soft cap on the per-process cache. Bounded to keep memory predictable."""


# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #


class ClassificationCeilingError(RuntimeError):
    """Raised when ``RetrievalRequest.classification_max != 'OFFICIAL'``.

    The pydantic ``RetrievalRequest`` Literal locks the entity boundary, but
    duck-typed callers (e.g. inline shapes from tests, the simulation
    Controller's ad-hoc dict) MUST also be rejected (FR-RAG-NS-07; contract
    §2.5).
    """

    def __init__(self, attempted: str) -> None:
        super().__init__(
            f"FR-RAG-NS-07: RetrievalService refuses classification_max={attempted!r}; "
            "only 'OFFICIAL' may pass; above-OFFICIAL paths must opt out of RAG."
        )
        self.attempted = attempted


class RetrievalQuotaExceeded(RuntimeError):
    """Raised when the per-agent hard QPS cap fires (R-09)."""


# --------------------------------------------------------------------------- #
# Protocol
# --------------------------------------------------------------------------- #


@runtime_checkable
class RetrievalService(Protocol):
    """Shared retrieval port (FR-RAG-AG-01)."""

    async def retrieve(self, request: Any) -> Any: ...


# --------------------------------------------------------------------------- #
# Internal helpers — quotas + cache
# --------------------------------------------------------------------------- #


@dataclass
class _QuotaState:
    window_start: float = 0.0
    count: int = 0


class _QuotaLimiter:
    """Per-agent rolling-1s QPS limiter (R-09).

    Soft cap → log; hard cap → ``RetrievalQuotaExceeded``. Uses monotonic
    seconds windows.
    """

    def __init__(self, soft: float = _QUOTA_SOFT_QPS, hard: float = _QUOTA_HARD_QPS) -> None:
        self._soft = soft
        self._hard = hard
        self._state: dict[str, _QuotaState] = {}
        self._lock = asyncio.Lock()

    async def consume(self, agent_name: str) -> None:
        async with self._lock:
            now = time.monotonic()
            state = self._state.setdefault(agent_name, _QuotaState(window_start=now))
            if now - state.window_start >= 1.0:
                state.window_start = now
                state.count = 0
            state.count += 1
            if state.count > self._hard:
                raise RetrievalQuotaExceeded(
                    f"agent {agent_name!r} exceeded hard QPS cap {self._hard} (R-09); falling back to template path"
                )
            if state.count > self._soft:
                logger.warning(
                    "retrieval_quota_soft_breach agent=%s count=%d/%d (R-09)",
                    agent_name,
                    state.count,
                    self._hard,
                )


@dataclass
class _CachedResult:
    payload: Any
    ts: float


class _QueryCache:
    """5-minute LRU cache keyed by ``(corpus_build_sha, query_text, jurisdictions)``."""

    def __init__(self, ttl_s: float = _CACHE_TTL_SECONDS, max_entries: int = _CACHE_MAX_ENTRIES) -> None:
        self._ttl = ttl_s
        self._max = max_entries
        self._store: OrderedDict[str, _CachedResult] = OrderedDict()

    @staticmethod
    def make_key(*, corpus_build_sha: str, query_text: str, jurisdictions: Iterable[str]) -> str:
        s = "|".join((corpus_build_sha, query_text, ",".join(sorted(jurisdictions))))
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.monotonic() - entry.ts > self._ttl:
            self._store.pop(key, None)
            return None
        # LRU bump
        self._store.move_to_end(key)
        return entry.payload

    def put(self, key: str, payload: Any) -> None:
        self._store[key] = _CachedResult(payload=payload, ts=time.monotonic())
        self._store.move_to_end(key)
        while len(self._store) > self._max:
            self._store.popitem(last=False)


# --------------------------------------------------------------------------- #
# Helpers — classification + jurisdiction union
# --------------------------------------------------------------------------- #


def _enforce_classification_ceiling(request: Any) -> None:
    cls = getattr(request, "classification_max", "OFFICIAL")
    if cls != "OFFICIAL":
        raise ClassificationCeilingError(str(cls))


def _normalise_jurisdiction(value: Any) -> str:
    """Accept either a Jurisdiction enum or a raw string; return the wire value."""
    return getattr(value, "value", value)


def _expand_jurisdictions(request: Any) -> list[str]:
    """Return the unioned jurisdiction set: own + national + aidr (R-03, US7)."""
    own = [_normalise_jurisdiction(j) for j in getattr(request, "jurisdictions", []) or []]
    union = set(own) | _JURISDICTION_UNION_BOOST
    return sorted(union)


# --------------------------------------------------------------------------- #
# RRF fusion (R-06)
# --------------------------------------------------------------------------- #


def _reciprocal_rank_fusion_scored(
    *,
    vector_hits: list[Any],
    lexical_hits: list[Any],
    top_k: int,
    vector_weight: float = RRF_VECTOR_WEIGHT_DEFAULT,
    lexical_weight: float = RRF_LEXICAL_WEIGHT_DEFAULT,
    key_fn: Any = None,
) -> list[tuple[Any, float]]:
    """Reciprocal Rank Fusion returning ``(item, fused_score)`` tuples (R-06).

    The production ``retrieve()`` path uses this variant so it can derive a
    per-chunk ``confidence`` value from the fused score when projecting raw
    AI Search hits into ``RetrievedChunk`` (FR-RAG-AG-03). The score-less
    wrapper ``_reciprocal_rank_fusion`` remains for legacy callers / tests.
    """
    key = key_fn or (lambda x: getattr(x, "chunk_id", None) or getattr(x, "id", None) or repr(x))
    scores: dict[Any, float] = {}
    items: dict[Any, Any] = {}
    for rank, hit in enumerate(vector_hits, start=1):
        k = key(hit)
        scores[k] = scores.get(k, 0.0) + vector_weight / (_RRF_K + rank)
        items.setdefault(k, hit)
    for rank, hit in enumerate(lexical_hits, start=1):
        k = key(hit)
        scores[k] = scores.get(k, 0.0) + lexical_weight / (_RRF_K + rank)
        items.setdefault(k, hit)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
    return [(items[k], score) for k, score in ranked]


def _reciprocal_rank_fusion(
    *,
    vector_hits: list[Any],
    lexical_hits: list[Any],
    top_k: int,
    vector_weight: float = RRF_VECTOR_WEIGHT_DEFAULT,
    lexical_weight: float = RRF_LEXICAL_WEIGHT_DEFAULT,
    key_fn: Any = None,
) -> list[Any]:
    """Reciprocal Rank Fusion (R-06).

    fuse_score = vector_weight / (k + rank_v) + lexical_weight / (k + rank_l)

    Returns the top ``top_k`` items by fused score, deduplicated on
    ``key_fn(item)``. Thin wrapper around ``_reciprocal_rank_fusion_scored``
    that drops the score component (kept for backward compatibility).
    """
    return [
        item
        for item, _score in _reciprocal_rank_fusion_scored(
            vector_hits=vector_hits,
            lexical_hits=lexical_hits,
            top_k=top_k,
            vector_weight=vector_weight,
            lexical_weight=lexical_weight,
            key_fn=key_fn,
        )
    ]


def _project_to_retrieved_chunk(hit: Any, fused_score: float, max_fused_score: float) -> Any:
    """Project a raw AI Search hit (dict / ``SearchResult``) into a
    ``RetrievedChunk`` (FR-RAG-AG-03).

    The live ``azure.search.documents.aio.SearchClient`` returns hits with
    extra fields (``corpus_entry_id``, ``embedding_model_id``,
    ``corpus_build_sha``, ``tokens``, ``@search.score`` etc.). The pydantic
    ``RetrievedChunk`` model is ``extra="forbid"``, so feeding raw hits in
    triggers validation errors and silently collapses every retrieval to
    ``chunks=[]``. This projection drops the extras, supplies the required
    ``confidence`` (derived from the RRF fused score normalised against the
    batch maximum), and honours the licence-mode / text-vs-summary
    invariant (R-11). Pass-through if ``hit`` is already a
    ``RetrievedChunk``.
    """
    from ama_domain.retrieval import RetrievedChunk  # noqa: PLC0415

    if isinstance(hit, RetrievedChunk):
        return hit

    confidence = (fused_score / max_fused_score) if max_fused_score > 0 else 0.0
    confidence = max(0.0, min(1.0, confidence))

    licence_mode = _chunk_field(hit, "licence_mode", "full-text") or "full-text"
    text_value = _chunk_field(hit, "text", None)
    summary_value = _chunk_field(hit, "summary", None)
    page_value = _chunk_field(hit, "page", 1)
    try:
        page_int = int(page_value) if page_value is not None else 1
    except (TypeError, ValueError):
        page_int = 1

    return RetrievedChunk(
        chunk_id=_chunk_field(hit, "chunk_id", "") or "",
        sha256_of_chunk=_chunk_field(hit, "sha256_of_chunk", "") or "",
        jurisdiction=_chunk_field(hit, "jurisdiction", "") or "",
        topic=_chunk_field(hit, "topic", "") or "",
        page=page_int,
        licence_mode=licence_mode,
        confidence=confidence,
        text=text_value if licence_mode == "full-text" else None,
        summary=summary_value if licence_mode == "metadata-only" else None,
        source_url=_chunk_field(hit, "source_url", "") or "",
        rendered_url=_chunk_field(hit, "rendered_url", "") or "",
    )


# --------------------------------------------------------------------------- #
# F-A1 (T183) — agency-filtered retrieval helpers
# --------------------------------------------------------------------------- #


def filter_by_agency(
    chunks: list[Any],
    *,
    requested_agency: str | None = None,
    requested_role: str | None = None,
) -> list[Any]:
    """Filter ``chunks`` to those matching ``requested_agency`` / ``requested_role``.

    Plan §F-A1.3: agency-filtered retrieval so urban-fire and rural-fire
    queries within the same jurisdiction never collide. ``None`` filters
    are no-ops; both filters are AND-combined.
    """
    if not requested_agency and not requested_role:
        return chunks
    out: list[Any] = []
    for chunk in chunks:
        agency = getattr(chunk, "agency", None) or (chunk.get("agency") if isinstance(chunk, dict) else None)
        role = getattr(chunk, "agency_role", None) or (chunk.get("agency_role") if isinstance(chunk, dict) else None)
        if requested_agency and agency != requested_agency:
            continue
        if requested_role and role != requested_role:
            continue
        out.append(chunk)
    return out


# --------------------------------------------------------------------------- #
# F-A3 (T185) — deterministic precedence tie-break (Pass 1 Q-P1-02; ADR-13)
# --------------------------------------------------------------------------- #


def _chunk_field(chunk: Any, name: str, default: Any = None) -> Any:
    if isinstance(chunk, dict):
        return chunk.get(name, default)
    return getattr(chunk, name, default)


def apply_precedence_tiebreak(chunks: list[Any]) -> tuple[list[Any], list[str]]:
    """Apply the deterministic 4-tier tie-break to ``chunks``.

    Returns ``(ordered_chunks, applied_tiers)`` where ``applied_tiers`` is
    a list of tier names actually triggered (in tier order). Tier definitions
    per Pass 1 Q-P1-02 + ADR-13 + Plan §F-A3.3:

      1. ``recency``           — newer ``corpus_build_generated_at`` wins.
      2. ``licence_mode``      — ``full-text`` > ``metadata-only``.
      3. ``embedding_model_id`` — lexicographic ascending.
      4. ``chunk_id``           — lexicographic ascending.

    Higher tiers (lower index) are evaluated first; only when they tie does
    the next tier engage. ``applied_tiers`` lists every tier that was *needed*
    to produce a strict order.
    """
    if not chunks:
        return ([], [])

    licence_priority = {"full-text": 0, "metadata-only": 1}

    def sort_key(chunk: Any) -> tuple[str, int, str, str]:
        return (
            # Recency: descending → invert by negating the ISO string sort.
            # Use the string itself with reverse=True at sort-time.
            _chunk_field(chunk, "corpus_build_generated_at", ""),
            licence_priority.get(_chunk_field(chunk, "licence_mode", ""), 99),
            _chunk_field(chunk, "embedding_model_id", "") or "",
            _chunk_field(chunk, "chunk_id", "") or "",
        )

    # Two-pass sort: descending recency first; everything else ascending.
    # We achieve this with a stable sort + composite key where recency is the
    # primary descending dimension; Python's sort is stable so we apply
    # ascending sub-keys first then reverse-sort by recency.
    ordered = sorted(
        chunks,
        key=lambda c: (
            licence_priority.get(_chunk_field(c, "licence_mode", ""), 99),
            _chunk_field(c, "embedding_model_id", "") or "",
            _chunk_field(c, "chunk_id", "") or "",
        ),
    )
    ordered = sorted(ordered, key=lambda c: _chunk_field(c, "corpus_build_generated_at", ""), reverse=True)

    # Determine which tiers were "needed". A tier is "applied" when it was
    # required to disambiguate at least one adjacent pair: either because
    # this tier broke the tie (after all higher tiers tied), or because
    # this is a higher tier that *also* distinguished. In other words,
    # "applied" lists every tier traversed top-down up to the deepest
    # deciding tier across all adjacent pairs (inclusive).
    applied: list[str] = []
    tier_names = ("recency", "licence_mode", "embedding_model_id", "chunk_id")
    tier_extractors = (
        lambda c: _chunk_field(c, "corpus_build_generated_at", ""),
        lambda c: _chunk_field(c, "licence_mode", ""),
        lambda c: _chunk_field(c, "embedding_model_id", "") or "",
        lambda c: _chunk_field(c, "chunk_id", "") or "",
    )
    max_depth = 0
    for i in range(len(ordered) - 1):
        # Find the first tier at which this adjacent pair became distinct.
        for tier_idx in range(len(tier_names)):
            if tier_extractors[tier_idx](ordered[i]) != tier_extractors[tier_idx](ordered[i + 1]):
                # depth is 1-indexed (number of tiers traversed inclusive).
                if tier_idx + 1 > max_depth:
                    max_depth = tier_idx + 1
                break
    applied = list(tier_names[:max_depth])

    return (ordered, applied)


# --------------------------------------------------------------------------- #
# F-A3 (T186) — COMDISPLAN activation interlock (FR-RAG-COMP-04)
# --------------------------------------------------------------------------- #


_NATIONAL_EMERGENCY_ACTIVE: bool = False

# F-A3 (T187) — Reversible feature flag (Pass 2 Q-P2-08)
# When False, retrieval ranking falls back to recency-only ordering (no
# precedence_rank elevation, no tie-break by licence_mode/embedding_model_id).
_AUTHORITY_PRECEDENCE_RANKING_ENABLED: bool = True


def get_authority_precedence_ranking_enabled() -> bool:
    """Return the current ``feature.authority_precedence_ranking.enabled`` flag."""
    return _AUTHORITY_PRECEDENCE_RANKING_ENABLED


def set_authority_precedence_ranking_flag(
    *,
    value: bool,
    actor: str,
    change_reason: str,
    audit_sink: Any | None = None,
    now_fn: Any = None,
) -> None:
    """Flip the ``feature.authority_precedence_ranking.enabled`` flag (T187,
    Reversible class per Pass 2 Q-P2-08).

    Disabling falls back to recency-only ranking. Emits the audit event
    ``authority_precedence_ranking_disabled`` (Plan §F-A3.5) with
    ``{flag_name, old_value, new_value, actor_id, change_reason}``.
    """
    from datetime import UTC, datetime  # noqa: PLC0415

    global _AUTHORITY_PRECEDENCE_RANKING_ENABLED
    if not actor:
        raise ValueError("actor required for feature-flag change (audit invariant)")
    if not change_reason:
        raise ValueError("change_reason required for Reversible flag flip")
    old_value = _AUTHORITY_PRECEDENCE_RANKING_ENABLED
    _AUTHORITY_PRECEDENCE_RANKING_ENABLED = bool(value)
    if audit_sink is not None:
        ts = (now_fn or (lambda: datetime.now(tz=UTC)))()
        audit_sink(
            {
                "event_type": "authority_precedence_ranking_disabled"
                if not bool(value)
                else "authority_precedence_ranking_enabled",
                "flag_name": "feature.authority_precedence_ranking.enabled",
                "old_value": old_value,
                "new_value": _AUTHORITY_PRECEDENCE_RANKING_ENABLED,
                "actor_id": actor,
                "change_reason": change_reason,
                "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
            }
        )


def get_national_emergency_active() -> bool:
    """Return the current ``national_emergency_active`` flag value."""
    return _NATIONAL_EMERGENCY_ACTIVE


def set_national_emergency_flag(
    *,
    value: bool,
    actor: str,
    audit_sink: Any | None = None,
    now_fn: Any = None,
) -> None:
    """Flip the ``national_emergency_active`` flag and emit
    ``audit.feature_flag_change`` per Plan §F-A6.4.

    ``audit_sink`` accepts a callable receiving a single dict event.
    Production wires this to the AuditWriter; tests inject a list-append.
    """
    from datetime import UTC, datetime  # noqa: PLC0415

    global _NATIONAL_EMERGENCY_ACTIVE
    if not actor:
        raise ValueError("actor required for feature-flag change (audit invariant)")
    old_value = _NATIONAL_EMERGENCY_ACTIVE
    _NATIONAL_EMERGENCY_ACTIVE = bool(value)
    if audit_sink is not None:
        ts = (now_fn or (lambda: datetime.now(tz=UTC)))()
        audit_sink(
            {
                "event_type": "audit.feature_flag_change",
                "flag": "national_emergency_active",
                "old_value": old_value,
                "new_value": _NATIONAL_EMERGENCY_ACTIVE,
                "actor": actor,
                "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
            }
        )


def apply_comdisplan_activation(
    chunks: list[Any],
    *,
    national_emergency_active: bool | None = None,
) -> list[Any]:
    """Elevate ``authority_level=commonwealth`` chunks to ``precedence_rank=1``
    when the ``national_emergency_active`` flag is set (FR-RAG-COMP-04).

    Returns shallow copies of the chunks with the elevated rank; non-commonwealth
    chunks are returned unchanged. When the flag is unset, the input is returned
    as-is.

    Pass ``national_emergency_active`` explicitly OR rely on the module-level
    flag set via ``set_national_emergency_flag``.
    """
    flag = national_emergency_active if national_emergency_active is not None else _NATIONAL_EMERGENCY_ACTIVE
    if not flag:
        return chunks
    out: list[Any] = []
    for chunk in chunks:
        level = _chunk_field(chunk, "authority_level")
        if level != "commonwealth":
            out.append(chunk)
            continue
        if isinstance(chunk, dict):
            elevated = dict(chunk)
            elevated["precedence_rank"] = 1
            out.append(elevated)
        else:
            # Pydantic / frozen dataclass — try model_copy / replace.
            if hasattr(chunk, "model_copy"):
                out.append(chunk.model_copy(update={"precedence_rank": 1}))
            else:
                # Best-effort mutation; if frozen will raise, caller must
                # use dicts in COMDISPLAN flows (or wrap in a non-frozen
                # adapter). The retrieval pipeline uses dicts at this stage
                # of the pipeline so frozen-mutation is not exercised in
                # production paths.
                try:
                    chunk.precedence_rank = 1
                except AttributeError:
                    pass
                out.append(chunk)
    return out


# --------------------------------------------------------------------------- #
# AzureSearchRetrievalService (production)
# --------------------------------------------------------------------------- #


@dataclass
class AzureSearchRetrievalService:
    """Production retrieval client.

    Hybrid retrieval over the alias-active ``corpus`` index in Azure AI Search:

    1. Embed ``query_text`` via the injected Foundry chat client.
    2. Vector search the ``embedding`` field.
    3. BM25 / semantic search over ``text`` + ``topic`` + ``summary``.
    4. Apply the ``jurisdiction in (union)`` filter to both arms (R-03).
    5. Reciprocal Rank Fusion (R-06; vector 0.7 / lexical 0.3 by default).
    6. Truncate to ``top_k`` and return.

    Constructor-injectable seam (FR-RAG-FM-07): pass ``search_client=...`` and
    ``embed_query=...`` to bypass the SDK in tests / dry runs.
    """

    endpoint: str | None = None
    index_alias: str = "corpus"
    credential: Any | None = None
    search_client: Any | None = None
    embed_query: Any | None = None
    foundry_chat_client: Any | None = None
    embedding_model_id: str = "text-embedding-3-large"
    corpus_build_sha: str = "0" * 64
    vector_weight: float = RRF_VECTOR_WEIGHT_DEFAULT
    lexical_weight: float = RRF_LEXICAL_WEIGHT_DEFAULT
    quota_limiter: _QuotaLimiter = field(default_factory=_QuotaLimiter)
    cache: _QueryCache = field(default_factory=_QueryCache)
    # F-A7 / ADR-16 — pinned index resolver. Tests inject a stub returning the
    # concrete name (e.g. "corpus-v3"); production wires this to the AI Search
    # alias-management API. None → fall back to ``index_alias`` itself
    # (legacy behaviour pre-Phase-F).
    alias_resolver: Any | None = None

    def __post_init__(self) -> None:
        # Deferred SDK import — keeps the unit test path hermetic.
        if self.endpoint is None:
            self.endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")

    async def resolve_alias_to_index_name(self) -> str:
        """Resolve ``self.index_alias`` to the concrete index name (F-A7 / ADR-16).

        Pinned ONCE at query start; the same concrete name MUST flow through
        every downstream operation (vector search, BM25 search, RetrievalResult,
        AuditRecord.retrieval_index_name) for the rest of the query's
        lifecycle. SSE multi-turn sessions pin once at session start; no
        alias re-resolution mid-query.

        Resolution order:
          1. Injected ``alias_resolver`` callable (test seam) — preferred.
          2. Env var ``RETRIEVAL_INDEX_NAME_OVERRIDE`` — useful for canary
             pinning during chaos game-days.
          3. Fall back to ``self.index_alias`` itself (legacy behaviour).
        """
        if self.alias_resolver is not None:
            result = self.alias_resolver(self.index_alias)
            if asyncio.iscoroutine(result):
                result = await result
            if isinstance(result, str) and result:
                return result
        override = os.environ.get("RETRIEVAL_INDEX_NAME_OVERRIDE")
        if override:
            return override
        return self.index_alias

    def _ensure_search_client(self) -> Any:
        if self.search_client is not None:
            return self.search_client
        if not self.endpoint:
            raise RuntimeError("AzureSearchRetrievalService requires endpoint or AZURE_SEARCH_ENDPOINT")
        from azure.identity.aio import DefaultAzureCredential  # noqa: PLC0415
        from azure.search.documents.aio import SearchClient  # noqa: PLC0415

        cred = self.credential or DefaultAzureCredential()
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_alias,
            credential=cred,
        )
        return self.search_client

    async def _embed(self, query_text: str) -> list[float]:
        """Embed ``query_text`` via the injected Foundry seam.

        The seam is constructor-injectable per FR-RAG-FM-07; in tests it
        defaults to a deterministic stub.
        """
        if self.embed_query is not None:
            result = self.embed_query(query_text)
            if asyncio.iscoroutine(result):
                return await result
            return result
        # Production path delegates to the foundry chat client's embedding API.
        # We fall back to a deterministic hash-based vector when no embedding
        # client is wired (e.g. the eval-runner replays from cached vectors).
        h = hashlib.sha256(query_text.encode("utf-8")).digest()
        return [b / 255.0 for b in h]

    async def retrieve(self, request: Any) -> Any:
        """Hybrid retrieval (BM25 + vector) with RRF (R-06).

        Parameters mirror the pydantic ``RetrievalRequest`` shape; duck-typed
        objects (test stubs, simulation-Controller dicts) are accepted as long
        as they expose ``classification_max``, ``jurisdictions``, ``query_text``,
        ``top_k``, ``agent_name``, ``correlation_id``, ``tenant_id``.
        """
        _enforce_classification_ceiling(request)
        agent_name = getattr(request, "agent_name", "UnknownAgent")
        await self.quota_limiter.consume(agent_name)

        # F-A7 / ADR-16 — pin the alias-resolved concrete index name ONCE at
        # query start. The pinned name flows through cache key, search calls,
        # and the RetrievalResult so audit replay sees the exact index name
        # used at decision time, not whichever index the alias happens to
        # point at when the audit is replayed.
        pinned_index_name = await self.resolve_alias_to_index_name()

        # Spec 036 / F-A11 / T234 — emit retrieval.retrieve OTel span with
        # the agent_name / jurisdiction / hazard_type tags and the pinned
        # index name as an attribute. Failures are captured via the context
        # manager's error handling.
        from common.otel_telemetry import retrieval_span  # noqa: PLC0415

        union = _expand_jurisdictions(request)
        primary_jurisdiction = union[0] if union else "unknown"
        with retrieval_span(
            agent_name=agent_name,
            jurisdiction=primary_jurisdiction,
            hazard_type=getattr(request, "hazard_type", "unknown") or "unknown",
            retrieval_index_name=pinned_index_name,
            correlation_id=getattr(request, "correlation_id", None),
        ) as _otel_span:
            result = await self._retrieve_inner(
                request=request,
                agent_name=agent_name,
                pinned_index_name=pinned_index_name,
                union=union,
            )
            _otel_span.histograms["retrieval_chunk_count"] = len(getattr(result, "chunks", []))
            return result

    async def _retrieve_inner(
        self,
        *,
        request: Any,
        agent_name: str,
        pinned_index_name: str | None,
        union: list[str],
    ) -> Any:
        query_text = getattr(request, "query_text", "")
        top_k = int(getattr(request, "top_k", 5) or 5)

        cache_key = self.cache.make_key(
            corpus_build_sha=self.corpus_build_sha,
            query_text=query_text,
            jurisdictions=union,
        )
        cached = self.cache.get(cache_key)
        if cached is not None:
            return _stamp_cache_hit(
                cached,
                alias=self.index_alias,
                pinned_index_name=pinned_index_name,
            )

        start = time.perf_counter()
        embedding = await self._embed(query_text)
        client = self.search_client
        if client is None:
            try:
                client = self._ensure_search_client()
            except RuntimeError:
                client = None

        # Filter clause (R-03 + FR-RAG-IDX-02 server-side excluded filter is
        # implicit — the index never carried excluded chunks).
        jurisdiction_filter = " or ".join(f"jurisdiction eq '{j}'" for j in union)
        filter_clause = f"({jurisdiction_filter}) and (licence_mode eq 'full-text' or licence_mode eq 'metadata-only')"

        oversample = top_k * 4
        try:
            vector_hits = await self._run_vector_search(client, embedding, filter_clause, oversample)
            lexical_hits = await self._run_lexical_search(client, query_text, filter_clause, oversample)
        except Exception:  # noqa: BLE001
            logger.exception("retrieval_search_503 agent=%s; returning empty result", agent_name)
            vector_hits = []
            lexical_hits = []

        fused_with_scores = _reciprocal_rank_fusion_scored(
            vector_hits=vector_hits,
            lexical_hits=lexical_hits,
            top_k=top_k,
            vector_weight=self.vector_weight,
            lexical_weight=self.lexical_weight,
        )
        max_score = max((s for _, s in fused_with_scores), default=1.0)
        latency_ms = int((time.perf_counter() - start) * 1000)

        # Build the RetrievalResult — defer pydantic import to keep this
        # module light at module-load time.
        from ama_domain.retrieval import RetrievalResult  # noqa: PLC0415

        # Project raw AI Search hits into RetrievedChunk: drops extra fields
        # (corpus_entry_id, embedding_model_id, corpus_build_sha, tokens,
        # @search.score, …) that would otherwise blow up extra="forbid",
        # supplies the required confidence from the fused score, and honours
        # the licence-mode text-vs-summary invariant (R-11). Failures are
        # logged and skipped so a malformed hit can't sink the whole batch.
        projected_chunks: list[Any] = []
        for hit, fused_score in fused_with_scores:
            try:
                projected_chunks.append(_project_to_retrieved_chunk(hit, fused_score, max_score))
            except Exception:  # noqa: BLE001
                logger.warning("retrieval_chunk_projection_failed; skipping hit", exc_info=True)

        result = RetrievalResult(
            chunks=projected_chunks,
            retrieval_latency_ms=latency_ms,
            embedding_model_id=self.embedding_model_id,
            corpus_build_sha=self.corpus_build_sha,
            classification_filter_applied=False,
            cache_hit=False,
            alias_active_index=self.index_alias,
            retrieval_index_name=pinned_index_name,
        )
        self.cache.put(cache_key, result)
        return result

    async def _run_vector_search(self, client: Any, embedding: list[float], filter_clause: str, top: int) -> list[Any]:
        if client is None:
            return []
        # Production wiring uses azure.search.documents.aio.SearchClient.
        # We return whatever the client.search() method yields — the test
        # stubs preconfigure this. The ``kind: "vector"`` discriminator is
        # REQUIRED by AI Search REST 2024-05-01-preview and later; omitting
        # it returns 400 ``InvalidVectorQuery: 'kind' parameter is not set``
        # which silently downgrades retrieval to lexical-only.
        try:
            iterable = client.search(
                search_text=None,
                vector_queries=[{"kind": "vector", "vector": embedding, "k": top, "fields": "embedding"}],
                filter=filter_clause,
                top=top,
            )
            return await _collect(iterable)
        except Exception:
            logger.warning("vector_search_failed; returning []", exc_info=True)
            return []

    async def _run_lexical_search(self, client: Any, query_text: str, filter_clause: str, top: int) -> list[Any]:
        if client is None:
            return []
        try:
            iterable = client.search(
                search_text=query_text,
                filter=filter_clause,
                top=top,
            )
            return await _collect(iterable)
        except Exception:
            logger.warning("lexical_search_failed; returning []", exc_info=True)
            return []


# --------------------------------------------------------------------------- #
# Result helpers
# --------------------------------------------------------------------------- #


async def _collect(iterable: Any) -> list[Any]:
    """Collect an async-iterable, awaitable, or sync-iterable of search hits into a list.

    Production wiring (``azure.search.documents.aio.SearchClient.search``)
    returns an ``AsyncSearchItemPaged``. Some SDK versions expose ``__aiter__``
    as a descriptor that ``hasattr`` cannot detect reliably; we therefore
    attempt async iteration first and fall back via ``TypeError``. Test stubs
    pass plain lists or coroutines.
    """
    if asyncio.iscoroutine(iterable) or asyncio.isfuture(iterable):
        iterable = await iterable
    try:
        return [item async for item in iterable]
    except TypeError:
        return list(iterable)


def _stamp_cache_hit(result: Any, *, alias: str, pinned_index_name: str | None = None) -> Any:
    """Return a copy of ``result`` with ``cache_hit=True`` (frozen-aware).

    F-A7 / ADR-16 — when a cache-hit occurs, the cached result's
    ``retrieval_index_name`` MUST be re-stamped to the freshly-pinned name.
    The pinned name comes from the *current* query's alias resolution, not
    the original cache-fill query's resolution; this preserves the invariant
    that ``audit.retrieval_index_name`` reflects the index actually queried
    during *this* call.
    """
    update: dict[str, Any] = {"cache_hit": True}
    if pinned_index_name:
        update["retrieval_index_name"] = pinned_index_name
    if hasattr(result, "model_copy"):
        return result.model_copy(update=update)
    # Fallback: duck-typed result.
    try:
        result.cache_hit = True
        if pinned_index_name:
            result.retrieval_index_name = pinned_index_name
    except AttributeError:
        pass
    return result


# --------------------------------------------------------------------------- #
# FakeRetrievalService — hermetic test stub (contract §6)
# --------------------------------------------------------------------------- #


class FakeRetrievalService:
    """Deterministic in-memory stub. Conforms to ``RetrievalService`` (duck-typed).

    Honours jurisdiction-union semantics so contract tests exercise the same
    surface as production (R-03). Returns a frozen ``RetrievalResult`` shaped
    identically to ``AzureSearchRetrievalService``.
    """

    def __init__(self, fixture: list[Any] | None = None) -> None:
        self._fixture = list(fixture or [])

    async def retrieve(self, request: Any) -> Any:
        _enforce_classification_ceiling(request)
        union = set(_expand_jurisdictions(request))
        top_k = int(getattr(request, "top_k", 5) or 5)
        chunks = []
        for c in self._fixture:
            jurisdiction = getattr(c, "jurisdiction", None)
            jurisdiction_value = getattr(jurisdiction, "value", jurisdiction)
            if jurisdiction_value in union:
                chunks.append(c)
                if len(chunks) >= top_k:
                    break

        from ama_domain.retrieval import RetrievalResult  # noqa: PLC0415

        return RetrievalResult(
            chunks=chunks,
            retrieval_latency_ms=1,
            embedding_model_id="text-embedding-3-large",
            corpus_build_sha="0" * 64,
            classification_filter_applied=False,
            cache_hit=False,
            alias_active_index="corpus-test",
            retrieval_index_name="corpus-test",
        )


# --------------------------------------------------------------------------- #
# Production builder — wires endpoint + Foundry embedder for runtime callers
# --------------------------------------------------------------------------- #


def build_default_retrieval_service() -> AzureSearchRetrievalService | None:
    """Auto-construct the production retrieval service, or return ``None``.

    Returns ``None`` when ``AZURE_SEARCH_ENDPOINT`` is unset — disables
    grounding gracefully so the API / agents containers still boot when
    the spec-036 cutover flag is off (the Bicep flag controls whether the
    env var is set).

    When the env var IS set, the service is constructed with:

    * ``endpoint`` from ``AZURE_SEARCH_ENDPOINT``.
    * ``index_alias`` from ``RETRIEVAL_INDEX_ALIAS`` (default ``"corpus"``).
    * ``embed_query`` wired to a :class:`FoundryQueryEmbedder` so query
      vectors match the 3072-dim corpus index. Without this wiring the
      runtime would fall back to a 32-byte hash and AI Search would 4xx
      every vector search — silently downgrading every citation.

    Failures during construction are logged and ``None`` is returned so
    a misconfigured Foundry endpoint doesn't crash the host service —
    the retrieval path is best-effort by design (R-12).
    """
    endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
    if not endpoint:
        return None
    try:
        from common.foundry_query_embedder import build_query_embedder  # noqa: PLC0415

        embed_query = build_query_embedder()
        return AzureSearchRetrievalService(
            endpoint=endpoint,
            index_alias=os.environ.get("RETRIEVAL_INDEX_ALIAS", "corpus"),
            embed_query=embed_query,
        )
    except Exception:  # noqa: BLE001
        logger.exception("build_default_retrieval_service_failed; grounding disabled for this process")
        return None


__all__ = [
    "AzureSearchRetrievalService",
    "ClassificationCeilingError",
    "FakeRetrievalService",
    "RRF_LEXICAL_WEIGHT_DEFAULT",
    "RRF_VECTOR_WEIGHT_DEFAULT",
    "RetrievalQuotaExceeded",
    "RetrievalService",
    "apply_comdisplan_activation",
    "apply_precedence_tiebreak",
    "build_default_retrieval_service",
    "filter_by_agency",
    "get_authority_precedence_ranking_enabled",
    "get_national_emergency_active",
    "set_authority_precedence_ranking_flag",
    "set_national_emergency_flag",
]
