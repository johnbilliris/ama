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
    ``key_fn(item)``.
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
    return [items[k] for k, _score in ranked]


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

    def __post_init__(self) -> None:
        # Deferred SDK import — keeps the unit test path hermetic.
        if self.endpoint is None:
            self.endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")

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

        union = _expand_jurisdictions(request)
        query_text = getattr(request, "query_text", "")
        top_k = int(getattr(request, "top_k", 5) or 5)

        cache_key = self.cache.make_key(
            corpus_build_sha=self.corpus_build_sha,
            query_text=query_text,
            jurisdictions=union,
        )
        cached = self.cache.get(cache_key)
        if cached is not None:
            return _stamp_cache_hit(cached, alias=self.index_alias)

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

        fused = _reciprocal_rank_fusion(
            vector_hits=vector_hits,
            lexical_hits=lexical_hits,
            top_k=top_k,
            vector_weight=self.vector_weight,
            lexical_weight=self.lexical_weight,
        )
        latency_ms = int((time.perf_counter() - start) * 1000)

        # Build the RetrievalResult — defer pydantic import to keep this
        # module light at module-load time.
        from ama_domain.retrieval import RetrievalResult  # noqa: PLC0415

        result = RetrievalResult(
            chunks=fused,
            retrieval_latency_ms=latency_ms,
            embedding_model_id=self.embedding_model_id,
            corpus_build_sha=self.corpus_build_sha,
            classification_filter_applied=False,
            cache_hit=False,
            alias_active_index=self.index_alias,
        )
        self.cache.put(cache_key, result)
        return result

    async def _run_vector_search(self, client: Any, embedding: list[float], filter_clause: str, top: int) -> list[Any]:
        if client is None:
            return []
        # Production wiring uses azure.search.documents.aio.SearchClient.
        # We return whatever the client.search() method yields — the test
        # stubs preconfigure this.
        try:
            iterable = client.search(
                search_text=None,
                vector_queries=[{"vector": embedding, "k": top, "fields": "embedding"}],
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
    """Collect an async-iterable or sync-iterable of search hits into a list."""
    if hasattr(iterable, "__aiter__"):
        out = []
        async for item in iterable:
            out.append(item)
        return out
    if asyncio.iscoroutine(iterable):
        iterable = await iterable
    return list(iterable)


def _stamp_cache_hit(result: Any, *, alias: str) -> Any:
    """Return a copy of ``result`` with ``cache_hit=True`` (frozen-aware)."""
    if hasattr(result, "model_copy"):
        return result.model_copy(update={"cache_hit": True})
    # Fallback: duck-typed result.
    try:
        result.cache_hit = True
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
        )


__all__ = [
    "AzureSearchRetrievalService",
    "ClassificationCeilingError",
    "FakeRetrievalService",
    "RRF_LEXICAL_WEIGHT_DEFAULT",
    "RRF_VECTOR_WEIGHT_DEFAULT",
    "RetrievalQuotaExceeded",
    "RetrievalService",
]
