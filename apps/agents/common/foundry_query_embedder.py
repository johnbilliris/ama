"""Foundry-hosted query embedder for the runtime retrieval path.

This module is the production-side counterpart to
``apps/ingest-runner/src/ama_ingest/embedder.py`` (which embeds *corpus
chunks* at index-build time). At query time, the same Foundry-hosted
``text-embedding-3-large`` deployment that built the index is used to embed
the agent's query string so that vector similarity is meaningful — both
sides MUST agree on the model + dimensionality (R-02; FR-RAG-IDX-02).

Why this exists
---------------
``AzureSearchRetrievalService._embed()`` falls back to a 32-byte SHA-256
hash when no ``embed_query`` callable is wired. The corpus index is built
with 3072-dim Foundry vectors, so an unwired query path would either be
rejected by AI Search (vector dim mismatch) or produce meaningless
results — silently degrading every agent / simulation citation. The
``build_query_embedder()`` helper here ensures the runtime always has a
proper embedder when ``AZURE_AI_PROJECT_ENDPOINT`` is configured.

Auth + transport
----------------
* AAD-only (FR-RAG-FM-05 / R-01) via ``DefaultAzureCredential`` against
  ``https://cognitiveservices.azure.com/.default``.
* Uses the Azure OpenAI surface (``openai.AzureOpenAI``) to mirror the
  ingest-runner embedder — a single Foundry / AIServices account serves
  both chat and embeddings via ``/openai/deployments/<dep>/embeddings``.
* Calls block on a sync HTTP client; we wrap in ``asyncio.to_thread`` so
  the retrieval coroutine doesn't stall the event loop.
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Awaitable, Callable
from typing import Any

logger = logging.getLogger(__name__)


AAD_SCOPE: str = "https://cognitiveservices.azure.com/.default"
"""Same AAD scope shared by the chat seam and ingest embedder."""


DEFAULT_EMBEDDING_DEPLOYMENT: str = "text-embedding-3-large-ama"
"""Bicep-provisioned embedding deployment name. Override via
``EMBEDDING_DEPLOYMENT_NAME`` env var if the deployment is renamed."""


DEFAULT_EMBEDDING_DIMS: int = 3072
"""``text-embedding-3-large`` output dimension. Asserted against the AI
Search index schema by the ingest-runner; mismatch ⇒ vector search 4xx."""


EmbedQueryFn = Callable[[str], Awaitable[list[float]]]


class FoundryQueryEmbedder:
    """Lazily-constructed Foundry embedding client for query-time embedding.

    Instances are cheap (no I/O on construction); the underlying
    ``AzureOpenAI`` client + ``DefaultAzureCredential`` are lazily built
    on first call and reused across calls.

    Parameters
    ----------
    endpoint:
        Foundry / AIServices account endpoint
        (e.g. ``https://ama-aif-zo6bb5.cognitiveservices.azure.com/``).
        Defaults to ``AZURE_AI_PROJECT_ENDPOINT`` env var.
    deployment:
        Embedding deployment name on the Foundry account. Defaults to
        ``EMBEDDING_DEPLOYMENT_NAME`` env var, then
        :data:`DEFAULT_EMBEDDING_DEPLOYMENT`.
    api_version:
        Azure OpenAI API version. Defaults to ``AZURE_OPENAI_API_VERSION``
        env var, then ``2024-10-21``.
    expected_dims:
        Expected output vector dimensionality; mismatched responses raise
        ``RuntimeError`` so retrieval fails loudly rather than silently
        landing empty results.
    credential:
        Optional AAD credential override. Production uses
        ``DefaultAzureCredential``; tests may inject a stub.
    """

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        deployment: str | None = None,
        api_version: str | None = None,
        expected_dims: int = DEFAULT_EMBEDDING_DIMS,
        credential: Any | None = None,
    ) -> None:
        self._endpoint = endpoint or os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
        self._deployment = deployment or os.environ.get("EMBEDDING_DEPLOYMENT_NAME") or DEFAULT_EMBEDDING_DEPLOYMENT
        self._api_version = api_version or os.environ.get("AZURE_OPENAI_API_VERSION") or "2024-10-21"
        self._expected_dims = expected_dims
        self._credential = credential
        self._client: Any | None = None

    @property
    def deployment(self) -> str:
        return self._deployment

    @property
    def expected_dims(self) -> int:
        return self._expected_dims

    def _ensure_client(self) -> Any:
        """Construct the AzureOpenAI client + AAD token provider once."""
        if self._client is not None:
            return self._client
        if not self._endpoint:
            raise RuntimeError("FoundryQueryEmbedder requires AZURE_AI_PROJECT_ENDPOINT to be set")
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider  # noqa: PLC0415
        from openai import AzureOpenAI  # AMA-FM04: allow Foundry transport (FR-RAG-FM-01)  # noqa: PLC0415

        cred = self._credential or DefaultAzureCredential()
        token_provider = get_bearer_token_provider(cred, AAD_SCOPE)
        self._client = AzureOpenAI(
            azure_endpoint=self._endpoint.rstrip("/"),
            azure_ad_token_provider=token_provider,
            api_version=self._api_version,
        )
        return self._client

    def _embed_sync(self, query_text: str) -> list[float]:
        client = self._ensure_client()
        response = client.embeddings.create(
            model=self._deployment,
            input=[query_text],
        )
        data = list(getattr(response, "data", []) or [])
        if not data:
            raise RuntimeError("Foundry embedding response contained no data")
        vec = list(getattr(data[0], "embedding", []) or [])
        if len(vec) != self._expected_dims:
            raise RuntimeError(f"Foundry embedding returned {len(vec)} dims, expected {self._expected_dims}")
        return vec

    async def embed_query(self, query_text: str) -> list[float]:
        """Async embed a single query string. Wraps the blocking SDK in a thread."""
        return await asyncio.to_thread(self._embed_sync, query_text)


def build_query_embedder() -> EmbedQueryFn | None:
    """Return an ``embed_query`` callable wired to Foundry, or ``None``.

    Returns ``None`` when ``AZURE_AI_PROJECT_ENDPOINT`` is unset — the
    caller (``AzureSearchRetrievalService``) then falls back to its
    deterministic stub path, which is appropriate for hermetic tests but
    NOT for production. ``build_default_retrieval_service()`` in
    ``retrieval_client`` enforces "production needs an endpoint".
    """
    if not os.environ.get("AZURE_AI_PROJECT_ENDPOINT"):
        return None
    embedder = FoundryQueryEmbedder()
    return embedder.embed_query


__all__ = [
    "AAD_SCOPE",
    "DEFAULT_EMBEDDING_DEPLOYMENT",
    "DEFAULT_EMBEDDING_DIMS",
    "EmbedQueryFn",
    "FoundryQueryEmbedder",
    "build_query_embedder",
]
