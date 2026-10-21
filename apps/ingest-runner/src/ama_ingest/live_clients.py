"""Live AI Search clients for the ingest-runner (Spec 036 FR-RAG-IDX-04).

The runner's ``indexer.py`` defines two thin Protocols (``IndexClient``,
``AliasService``) plus in-memory test fakes. This module provides the
production wrappers so the CLI can write the corpus to the live AI Search
service.

Design:

* ``LiveAzureSearchIndex`` — wraps ``azure.search.documents.SearchClient`` for
  document upload + idempotency probes against a single index.
* ``LiveAzureSearchAlias`` — wraps ``azure.search.documents.indexes
  .SearchIndexClient`` for alias and index management (create-if-missing,
  flip).
* ``ensure_index_schema`` — idempotently creates the index with the schema
  the retrieval client expects (``apps/agents/common/retrieval_client.py``):
  vector field ``embedding`` (3072-dim), filterable provenance fields
  (``jurisdiction``, ``licence_mode``, ``embedding_model_id``, ``agency``,
  …), searchable text fields (``text``, ``summary``).
* ``build_live_clients`` — factory used by the CLI when ``--search-endpoint``
  is set.

Document keys: AI Search restricts ``chunk_id`` to letters, digits, ``_``,
``-``, ``=``. The corpus emits keys containing ``/`` (path separators) and
``#`` (metadata-only suffix), so ``LiveAzureSearchIndex`` transparently
re-encodes the key on upload + lookup. The original ``chunk_id`` is mirrored
to a non-key ``corpus_entry_id``-style field so ``retrieval_client.py`` can
present the unchanged value back to humans.

All clients use ``DefaultAzureCredential`` (AAD-only — FR-S03). The
ingest-runner UAMI is granted ``Search Service Contributor`` and
``Search Index Data Contributor`` by ``infra/main.bicep``.
"""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Sequence
from typing import Any

# Build-time version banner — appears on first import so deployment logs
# definitively show which version is running. Bumped whenever this module
# is materially edited.
LIVE_CLIENTS_VERSION = "2026-05-10-v5-alias-preview-api"

logger = logging.getLogger(__name__)
logger.info("LIVE_CLIENTS_VERSION=%s", LIVE_CLIENTS_VERSION)


# --------------------------------------------------------------------------- #
# Document-key sanitisation (AI Search constraint)
# --------------------------------------------------------------------------- #


_KEY_SAFE_RE = re.compile(r"[^A-Za-z0-9_\-=]")


def _safe_key(chunk_id: str) -> str:
    """Encode ``chunk_id`` so it is a legal AI Search document key.

    AI Search keys may only contain letters, digits, ``_``, ``-`` and ``=``.
    The corpus emits keys like ``aidr/community-recovery#metadata`` or
    ``national/handbook-1#p12``. We map every non-allowed character to ``_``
    plus a hex code (``__2F`` for ``/``, ``__23`` for ``#``) so the original
    is recoverable and collisions stay impossible across the corpus.
    """
    if not chunk_id:
        return chunk_id

    def _replace(match: re.Match[str]) -> str:
        return f"__{ord(match.group(0)):02X}"

    return _KEY_SAFE_RE.sub(_replace, chunk_id)


def _with_safe_key(doc: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow copy with ``chunk_id`` encoded for AI Search.

    The original value is preserved on the document under
    ``chunk_id_original`` so the retrieval client (and audit replay) can
    surface the human-readable key without reverse-decoding.
    """
    chunk_id = doc.get("chunk_id")
    if not isinstance(chunk_id, str):
        return doc
    encoded = _safe_key(chunk_id)
    if encoded == chunk_id:
        new_doc = dict(doc)
        new_doc.setdefault("chunk_id_original", chunk_id)
        return new_doc
    new_doc = dict(doc)
    new_doc["chunk_id"] = encoded
    new_doc["chunk_id_original"] = chunk_id
    return new_doc


# --------------------------------------------------------------------------- #
# Schema definition (must stay in sync with retrieval_client.py field names)
# --------------------------------------------------------------------------- #


VECTOR_DIMS_DEFAULT: int = 3072
"""``text-embedding-3-large`` default output dimensionality."""


VECTOR_PROFILE_NAME: str = "corpus-vector-profile"
HNSW_ALG_NAME: str = "corpus-hnsw"


def _build_index_definition(
    *,
    index_name: str,
    vector_dims: int,
) -> Any:
    """Construct an AI Search index definition matching the chunker output schema.

    Field set is the union of:

    * ``REQUIRED_PROVENANCE_FIELDS`` from ``indexer.py``.
    * Additional fields written by ``chunks_to_index_docs`` in ``chunker.py``.
    * ``embedding`` vector field referenced by ``retrieval_client.py`` line 752.

    All filterable string fields use the default tokenizer (no analyser) so
    ``filter=jurisdiction eq 'national'`` style clauses work without
    surprises. ``text`` and ``summary`` are ``searchable`` so BM25 hits both.
    """
    from azure.search.documents.indexes.models import (  # noqa: PLC0415
        HnswAlgorithmConfiguration,
        SearchableField,
        SearchField,
        SearchIndex,
        SimpleField,
        VectorSearch,
        VectorSearchProfile,
    )

    fields: list[Any] = [
        SimpleField(name="chunk_id", type="Edm.String", key=True, filterable=True),
        SimpleField(name="chunk_id_original", type="Edm.String", filterable=False),
        SimpleField(name="corpus_entry_id", type="Edm.String", filterable=True),
        SimpleField(name="jurisdiction", type="Edm.String", filterable=True, facetable=True),
        SimpleField(name="topic", type="Edm.String", filterable=True, facetable=True),
        SimpleField(name="page", type="Edm.Int32", filterable=True),
        SimpleField(name="tokens", type="Edm.Int32", filterable=True),
        SimpleField(name="sha256_of_chunk", type="Edm.String", filterable=True),
        SimpleField(name="licence_mode", type="Edm.String", filterable=True, facetable=True),
        SimpleField(name="source_url", type="Edm.String", filterable=False),
        SimpleField(name="rendered_url", type="Edm.String", filterable=False),
        SimpleField(name="cross_page", type="Edm.Boolean", filterable=True),
        SimpleField(name="embedding_model_id", type="Edm.String", filterable=True),
        SimpleField(name="corpus_build_sha", type="Edm.String", filterable=True),
        SimpleField(name="agency", type="Edm.String", filterable=True, facetable=True),
        SimpleField(name="agency_role", type="Edm.String", filterable=True, facetable=True),
        SimpleField(name="authority_level", type="Edm.String", filterable=True, facetable=True),
        SimpleField(name="precedence_rank", type="Edm.Int32", filterable=True),
        SimpleField(name="cultural_classification", type="Edm.String", filterable=True, facetable=True),
        SimpleField(name="cultural_authority_required", type="Edm.Boolean", filterable=True),
        SearchableField(name="text", type="Edm.String", searchable=True),
        SearchableField(name="summary", type="Edm.String", searchable=True),
        SearchField(
            name="embedding",
            type="Collection(Edm.Single)",
            searchable=True,
            vector_search_dimensions=vector_dims,
            vector_search_profile_name=VECTOR_PROFILE_NAME,
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name=HNSW_ALG_NAME)],
        profiles=[
            VectorSearchProfile(
                name=VECTOR_PROFILE_NAME,
                algorithm_configuration_name=HNSW_ALG_NAME,
            )
        ],
    )

    return SearchIndex(name=index_name, fields=fields, vector_search=vector_search)


# --------------------------------------------------------------------------- #
# Live IndexClient — write path
# --------------------------------------------------------------------------- #


class LiveAzureSearchIndex:
    """Production ``IndexClient`` — wraps ``azure.search.documents.SearchClient``.

    Implements the same surface as ``InMemoryIndex`` (``upload_documents``,
    ``get_document_by_chunk_id``, ``list_chunk_ids``, ``count``,
    ``distinct_embedding_model_ids``) so ``BlueGreenIndexer`` works without
    branching.

    ``upload_documents`` uses ``merge_or_upload_documents`` to make every
    re-run idempotent on ``chunk_id`` (FR-RAG-IDX-04).
    """

    def __init__(self, *, endpoint: str, index_name: str, credential: Any | None = None) -> None:
        from azure.identity import DefaultAzureCredential  # noqa: PLC0415
        from azure.search.documents import SearchClient  # noqa: PLC0415

        self.name = index_name
        self._cred = credential or DefaultAzureCredential()
        self._client = SearchClient(endpoint=endpoint, index_name=index_name, credential=self._cred)

    def upload_documents(self, documents: Sequence[dict[str, Any]]) -> int:
        if not documents:
            return 0
        # AI Search hard caps a single ``merge_or_upload_documents`` call at
        # 1000 docs and 16 MB. With 3072-dim float embeddings each chunk is
        # ~12-15 KB on the wire so we stay well under both limits at 100/batch.
        BATCH_SIZE = 100  # noqa: N806 — local constant
        sanitised = [_with_safe_key(doc) for doc in documents]
        succeeded_total = 0
        failures_logged = 0
        for i in range(0, len(sanitised), BATCH_SIZE):
            batch = sanitised[i : i + BATCH_SIZE]
            result = self._client.merge_or_upload_documents(batch)
            batch_ok = sum(1 for r in result if getattr(r, "succeeded", True))
            succeeded_total += batch_ok
            if batch_ok != len(batch) and failures_logged < 3:
                failures = [r for r in result if not getattr(r, "succeeded", True)]
                logger.warning(
                    "AI Search upload partial batch %d-%d: %d/%d ok; failures=%s",
                    i,
                    i + len(batch),
                    batch_ok,
                    len(batch),
                    failures[:3],
                )
                failures_logged += 1
        if succeeded_total != len(documents):
            logger.warning(
                "AI Search upload aggregate: %d/%d ok",
                succeeded_total,
                len(documents),
            )
        return succeeded_total

    def get_document_by_chunk_id(self, chunk_id: str) -> dict[str, Any] | None:
        try:
            doc = self._client.get_document(key=_safe_key(chunk_id))
        except Exception as exc:  # noqa: BLE001
            status = getattr(exc, "status_code", None)
            if status == 404:
                return None
            raise
        if not doc:
            return None
        result = dict(doc)
        # Restore the human-readable chunk_id so callers (parity gate, audit)
        # see the original value rather than the encoded key.
        original = result.get("chunk_id_original")
        if original:
            result["chunk_id"] = original
        return result

    def list_chunk_ids(self) -> list[str]:
        ids: list[str] = []
        results = self._client.search(
            search_text="*",
            select=["chunk_id_original", "chunk_id"],
            top=1000,
            include_total_count=False,
        )
        for r in results:
            cid = (r.get("chunk_id_original") if isinstance(r, dict) else getattr(r, "chunk_id_original", None)) or (
                r.get("chunk_id") if isinstance(r, dict) else getattr(r, "chunk_id", None)
            )
            if cid:
                ids.append(str(cid))
        return ids

    def count(self) -> int:
        results = self._client.search(search_text="*", top=0, include_total_count=True)
        return int(results.get_count() or 0)

    def distinct_embedding_model_ids(self) -> list[str]:
        seen: set[str] = set()
        results = self._client.search(search_text="*", select=["embedding_model_id"], top=1000)
        for r in results:
            mid = r.get("embedding_model_id") if isinstance(r, dict) else getattr(r, "embedding_model_id", None)
            if mid:
                seen.add(str(mid))
        return sorted(seen)


# --------------------------------------------------------------------------- #
# Live AliasService — alias and index management
# --------------------------------------------------------------------------- #


class LiveAzureSearchAlias:
    """Production ``AliasService`` — wraps ``SearchIndexClient`` alias APIs."""

    def __init__(
        self,
        *,
        endpoint: str,
        alias_name: str,
        credential: Any | None = None,
    ) -> None:
        from azure.identity import DefaultAzureCredential  # noqa: PLC0415
        from azure.search.documents.indexes import SearchIndexClient  # noqa: PLC0415

        self.alias = alias_name
        self._cred = credential or DefaultAzureCredential()
        self._mgmt = SearchIndexClient(endpoint=endpoint, credential=self._cred)
        self._endpoint = endpoint
        self.last_flip_latency_s: float = 0.0
        self._cached_active: str | None | _Sentinel = _SENTINEL
        self._cached_active_model: str | None = None

    def get_active_index(self) -> str | None:
        if self._cached_active is _SENTINEL:
            self._cached_active = self._read_alias_target()
        return self._cached_active  # type: ignore[return-value]

    def get_active_embedding_model_id(self) -> str | None:
        return self._cached_active_model

    def set_active_embedding_model_id(self, value: str) -> None:
        self._cached_active_model = value

    def register_index(self, name: str) -> None:
        """No-op — index creation is handled by ``ensure_index_schema``."""
        return None

    def list_indices(self) -> list[str]:
        return [idx.name for idx in self._mgmt.list_indexes()]

    _ALIAS_API_VERSION = "2024-05-01-preview"

    def flip(self, *, alias: str, target_index: str) -> float:
        from azure.core.rest import HttpRequest  # noqa: PLC0415

        if alias != self.alias:
            raise ValueError(f"alias mismatch {alias!r} ≠ {self.alias!r}")
        start = time.perf_counter()
        body = {"name": alias, "indexes": [target_index]}
        url = f"/aliases/{alias}?api-version={self._ALIAS_API_VERSION}"
        request = HttpRequest("PUT", url, json=body, headers={"Content-Type": "application/json"})
        response = self._mgmt.send_request(request)
        if response.status_code not in (200, 201):
            raise RuntimeError(f"Alias PUT failed: status={response.status_code} body={response.text()[:500]}")
        self.last_flip_latency_s = time.perf_counter() - start
        self._cached_active = target_index
        return self.last_flip_latency_s

    def _read_alias_target(self) -> str | None:
        from azure.core.rest import HttpRequest  # noqa: PLC0415

        url = f"/aliases/{self.alias}?api-version={self._ALIAS_API_VERSION}"
        request = HttpRequest("GET", url)
        response = self._mgmt.send_request(request)
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise RuntimeError(f"Alias GET failed: status={response.status_code} body={response.text()[:500]}")
        body = response.json()
        targets = list(body.get("indexes") or [])
        return targets[0] if targets else None


# --------------------------------------------------------------------------- #
# Index creation
# --------------------------------------------------------------------------- #


def ensure_index_schema(
    *,
    endpoint: str,
    index_name: str,
    vector_dims: int = VECTOR_DIMS_DEFAULT,
    credential: Any | None = None,
) -> None:
    """Create the index with the corpus schema if it doesn't already exist."""
    from azure.identity import DefaultAzureCredential  # noqa: PLC0415
    from azure.search.documents.indexes import SearchIndexClient  # noqa: PLC0415

    cred = credential or DefaultAzureCredential()
    client = SearchIndexClient(endpoint=endpoint, credential=cred)
    try:
        client.get_index(index_name)
        logger.info("AI Search index %s already exists; skipping schema creation", index_name)
        return
    except Exception as exc:  # noqa: BLE001
        status = getattr(exc, "status_code", None)
        if status not in (404, None):
            raise
    definition = _build_index_definition(index_name=index_name, vector_dims=vector_dims)
    client.create_index(definition)
    logger.info("AI Search index %s created (vector_dims=%d)", index_name, vector_dims)


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #


class _Sentinel:
    pass


_SENTINEL = _Sentinel()


def build_live_clients(
    *,
    endpoint: str,
    alias_name: str,
    target_index: str,
    vector_dims: int = VECTOR_DIMS_DEFAULT,
    credential: Any | None = None,
) -> tuple[LiveAzureSearchIndex, LiveAzureSearchAlias]:
    """Return ``(index, alias)`` clients for the given alias + target index.

    Idempotently ensures the target index exists with the correct schema.
    Caller is responsible for flipping the alias once the new index has been
    populated and the parity gate has signed off.
    """
    ensure_index_schema(
        endpoint=endpoint,
        index_name=target_index,
        vector_dims=vector_dims,
        credential=credential,
    )
    index = LiveAzureSearchIndex(endpoint=endpoint, index_name=target_index, credential=credential)
    alias = LiveAzureSearchAlias(endpoint=endpoint, alias_name=alias_name, credential=credential)
    return index, alias


__all__ = [
    "HNSW_ALG_NAME",
    "LiveAzureSearchAlias",
    "LiveAzureSearchIndex",
    "VECTOR_DIMS_DEFAULT",
    "VECTOR_PROFILE_NAME",
    "build_live_clients",
    "ensure_index_schema",
]
