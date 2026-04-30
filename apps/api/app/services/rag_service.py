"""RAG service over the AIDR handbook corpus (spec-032 FR-AI01, T603).

Thin client over Azure AI Search. Honours:
  - Private Endpoint only (no public network access)
  - Citation contract (every chunk returns handbook + page reference)
  - Retrieval P95 ≤ 400 ms target (SLO-8)
  - rag.retrieval.lag_milliseconds + rag.retrieval.hit_count customMetrics

When AZURE_AI_SEARCH_ENDPOINT is unset (dev / unit tests), the service operates
in stub mode returning empty hits — agents fall through to template flows
gracefully.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from packages.domain.src.domain.models.rag_citation import RagCitation

logger = logging.getLogger(__name__)


class RagService:
    """Retrieval over Azure AI Search ``aidr-handbooks`` index."""

    DEFAULT_INDEX = "aidr-handbooks"

    def __init__(
        self,
        endpoint: str | None = None,
        index_name: str | None = None,
        client: Any | None = None,
    ) -> None:
        self._endpoint = endpoint or os.getenv("AZURE_AI_SEARCH_ENDPOINT")
        self._index_name = index_name or os.getenv("AZURE_AI_SEARCH_INDEX", self.DEFAULT_INDEX)
        self._client = client or self._build_client()

    def _build_client(self) -> Any | None:
        if not self._endpoint:
            logger.info("AZURE_AI_SEARCH_ENDPOINT not set; RagService running in stub mode")
            return None
        try:
            from azure.identity import DefaultAzureCredential
            from azure.search.documents import SearchClient

            return SearchClient(
                endpoint=self._endpoint,
                index_name=self._index_name,
                credential=DefaultAzureCredential(),
            )
        except Exception:  # noqa: BLE001
            logger.exception("AI Search client init failed; running in stub mode")
            return None

    def search(self, query: str, *, top_k: int = 5) -> list[RagCitation]:
        """Hybrid search (BM25 + vector) returning RagCitation hits.

        Always returns a list (possibly empty); never raises so upstream agents
        can degrade gracefully to template-only output.
        """
        if not query or not query.strip():
            return []
        if self._client is None:
            return []

        start = time.perf_counter()
        hits: list[RagCitation] = []
        try:
            results = self._client.search(
                search_text=query,
                top=top_k,
                query_type="semantic" if os.getenv("AI_SEARCH_SEMANTIC", "true").lower() == "true" else "simple",
                semantic_configuration_name=os.getenv("AI_SEARCH_SEMANTIC_CFG", "default") or None,
                select=["chunk_id", "handbook_id", "chapter", "page", "content"],
            )
            for r in results:
                content = (r.get("content") or "")
                quote = content[:480] + ("…" if len(content) > 480 else "")
                hits.append(
                    RagCitation(
                        chunk_id=str(r.get("chunk_id", "")),
                        handbook_id=str(r.get("handbook_id", "")),
                        chapter=r.get("chapter"),
                        page=r.get("page"),
                        score=float(r.get("@search.score", 0.0)),
                        quote=quote,
                    )
                )
        except Exception:  # noqa: BLE001
            logger.exception("RAG search failed; returning empty result")
            hits = []
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            self._emit_metrics(elapsed_ms, len(hits))
        return hits

    def _emit_metrics(self, elapsed_ms: float, hit_count: int) -> None:
        try:
            from apps.api.app.observability.metrics import emit_counter, emit_histogram

            emit_histogram(
                "rag.retrieval.lag_milliseconds", elapsed_ms, {"index": self._index_name}, unit="ms"
            )
            emit_counter(
                "rag.retrieval.hit_count", hit_count, {"index": self._index_name}
            )
        except Exception:  # noqa: BLE001
            logger.debug("rag metrics emit failed", exc_info=True)
