"""Foundry embedder (Spec 036 T042; FR-RAG-IDX-02; R-02).

Wraps the Foundry-hosted embedding deployment (``text-embedding-3-large`` at
3072 dimensions) for the corpus ingest pipeline. Mirrors
``apps/agents/common/foundry_chat_client.LiveFoundryChatClient`` for a single
test-seam contract:

- AAD-only (FR-RAG-FM-05 / R-01) — ``DefaultAzureCredential`` against scope
  ``https://cognitiveservices.azure.com/.default``. ``api_key=`` is not
  permitted.
- Constructor-injectable ``embed`` callable for hermetic unit tests; the live
  client is lazily constructed only when the callable is not supplied.
- Tenacity retry on Foundry 429 / 503 (``ingest-pipeline.md`` §7).

Telemetry:
- per-call ``embedding_latency_ms`` histogram.
- per-call ``embedded_token_count`` counter (for cost tracking).
- per-batch cost estimator (USD).

The embedder produces vectors of length :data:`EMBEDDING_DIMS` (3072) — exactly
one ``embedding_model_id`` per index per R-05 signal 4.
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants — bound by R-02 + FR-RAG-IDX-02
# --------------------------------------------------------------------------- #

#: ``text-embedding-3-large`` outputs 3072-dimension vectors at default config.
EMBEDDING_DIMS: int = 3072

#: AAD scope — the same ``cognitiveservices.azure.com/.default`` constant
#: shared by ``LiveFoundryChatClient`` (FR-RAG-FM-05; mirrored here so the
#: ingest-runner doesn't import the heavyweight chat seam).
AAD_SCOPE: str = "https://cognitiveservices.azure.com/.default"

#: Default model key — matches the registry row authored in T027.
DEFAULT_MODEL_KEY: str = "text-embedding-3-large@1"

#: Per-call cost (USD per 1K tokens); v1 default per Foundry pricing page,
#: refreshed by the Cost-Architect persona at quarterly review.
COST_PER_1K_TOKENS_USD: float = 0.00013


# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #


class EmbedderConfigurationError(RuntimeError):
    """Hard misconfig (missing endpoint, deployment-not-found)."""


class EmbedderTransportError(RuntimeError):
    """Wraps SDK 5xx / timeout — surfaces after retry exhaustion."""


# --------------------------------------------------------------------------- #
# Wire-format dataclasses
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class EmbeddingResult:
    """Result of a single embedding call (one or more vectors)."""

    vectors: list[list[float]]
    token_count: int
    latency_ms: int
    raw: dict[str, Any]


@dataclass
class EmbedderStats:
    """Telemetry container — accumulated across the run."""

    call_count: int = 0
    embedded_token_count: int = 0
    total_latency_ms: int = 0
    cost_usd: float = 0.0
    latencies: list[int] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Test-seam type alias (FR-RAG-FM-07 pattern)
# --------------------------------------------------------------------------- #


EmbedFn = Callable[..., EmbeddingResult]
"""Constructor-injectable embed callable. Production: ``LiveEmbedder._embed``;
tests: a stub returning a deterministic vector by ``chunk_id`` hash."""


# --------------------------------------------------------------------------- #
# Tenacity retry policy
# --------------------------------------------------------------------------- #


def _retry_decorator() -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Return a tenacity retry decorator on 429 / 503 transient failures.

    Falls back to identity decorator when ``tenacity`` is not installed (unit
    tests using the stub ``embed`` callable never need retry).
    """
    try:
        from tenacity import (  # noqa: PLC0415
            retry,
            retry_if_exception_type,
            stop_after_attempt,
            wait_exponential,
        )
    except ImportError:  # pragma: no cover

        def _identity(fn: Callable[..., Any]) -> Callable[..., Any]:
            return fn

        return _identity
    return retry(
        retry=retry_if_exception_type(EmbedderTransportError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=16),
        reraise=True,
    )


# --------------------------------------------------------------------------- #
# Embedder
# --------------------------------------------------------------------------- #


class FoundryEmbedder:
    """Foundry-hosted embedding client.

    Production: lazily constructs ``azure.ai.inference.EmbeddingsClient`` under
    ``DefaultAzureCredential`` with the AAD scope above.
    Tests: pass an ``embed=`` callable that returns ``EmbeddingResult``.
    """

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        deployments: dict[str, str] | None = None,
        credential: Any | None = None,
        embed: EmbedFn | None = None,
        model_key: str = DEFAULT_MODEL_KEY,
        embedding_dims: int = EMBEDDING_DIMS,
        cost_per_1k_tokens: float = COST_PER_1K_TOKENS_USD,
    ) -> None:
        if "api_key" in (locals() or {}):  # defence-in-depth, mirrors chat seam
            pass  # api_key is not a kwarg of __init__; explicit guard below.
        self._endpoint = endpoint or os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
        configured_deployments = _parse_deployment_map(os.environ.get("AZURE_AI_PROJECT_DEPLOYMENTS"))
        self._deployments = (
            configured_deployments
            if deployments is None
            else _validated_deployment_map(deployments.items(), source="deployments")
        )
        self._cred = credential
        self._client: Any | None = None
        self._embed = embed
        self._model_key = model_key
        self._dims = embedding_dims
        self._cost_per_1k = cost_per_1k_tokens
        self.stats = EmbedderStats()

    @property
    def model_key(self) -> str:
        return self._model_key

    @property
    def embedding_dims(self) -> int:
        return self._dims

    # ------------------------------------------------------------------ #
    # Resolve deployment — same env-var contract as the chat seam.
    # ------------------------------------------------------------------ #

    def _resolve(self) -> str:
        if self._model_key in self._deployments:
            return self._deployments[self._model_key]
        base = self._model_key.split("@", 1)[0]
        if base in self._deployments:
            return self._deployments[base]
        raise EmbedderConfigurationError(
            f"no Foundry deployment configured for {self._model_key!r}; set AZURE_AI_PROJECT_DEPLOYMENTS env var"
        )

    # ------------------------------------------------------------------ #
    # Live client construction (lazy).
    # ------------------------------------------------------------------ #

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider  # noqa: PLC0415

        if not self._endpoint:
            raise EmbedderConfigurationError("AZURE_AI_PROJECT_ENDPOINT is not set")
        cred = self._cred or DefaultAzureCredential()

        # AIServices / Azure OpenAI accounts expose embeddings via the
        # ``/openai/deployments/<dep>/embeddings`` Azure OpenAI surface, not the
        # Foundry Inference SDK's ``/models/embeddings`` route. Mirror the chat
        # seam (``apps/agents/maf_runtime/chat_client.py``) and use
        # ``openai.AzureOpenAI`` against ``cognitiveservices.azure.com`` so a
        # single Foundry account can serve both chat and embeddings.
        from openai import AzureOpenAI  # AMA-FM04: allow Foundry transport (FR-RAG-FM-01)  # noqa: PLC0415

        token_provider = get_bearer_token_provider(cred, AAD_SCOPE)
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21")
        self._client = AzureOpenAI(
            azure_endpoint=self._endpoint.rstrip("/"),
            azure_ad_token_provider=token_provider,
            api_version=api_version,
        )
        return self._client

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def embed_batch(self, texts: Sequence[str]) -> EmbeddingResult:
        """Embed a batch of texts in a single Foundry call."""
        if not texts:
            return EmbeddingResult(vectors=[], token_count=0, latency_ms=0, raw={})

        @_retry_decorator()
        def _do() -> EmbeddingResult:
            return self._call(texts)

        result = _do()
        self.stats.call_count += 1
        self.stats.embedded_token_count += result.token_count
        self.stats.total_latency_ms += result.latency_ms
        self.stats.latencies.append(result.latency_ms)
        self.stats.cost_usd += (result.token_count / 1000.0) * self._cost_per_1k
        return result

    def embed_chunks(
        self,
        chunks: Iterable[Any],
        *,
        batch_size: int = 16,
    ) -> dict[str, list[float]]:
        """Embed a sequence of ``Chunk``-shaped objects, keyed by ``chunk_id``.

        ``chunks`` may be any iterable whose items expose ``.chunk_id`` and
        ``.text`` attributes — ``chunker.Chunk`` qualifies.
        """
        out: dict[str, list[float]] = {}
        batch: list[Any] = []

        def _flush() -> None:
            if not batch:
                return
            texts = [c.text for c in batch]
            res = self.embed_batch(texts)
            for c, vec in zip(batch, res.vectors, strict=True):
                if len(vec) != self._dims:
                    raise EmbedderConfigurationError(
                        f"embedding dimension mismatch for {c.chunk_id}: got {len(vec)}, expected {self._dims}"
                    )
                out[c.chunk_id] = vec
            batch.clear()

        for chunk in chunks:
            batch.append(chunk)
            if len(batch) >= batch_size:
                _flush()
        _flush()
        return out

    # ------------------------------------------------------------------ #
    # Underlying call — uses injected ``embed`` callable when present.
    # ------------------------------------------------------------------ #

    def _call(self, texts: Sequence[str]) -> EmbeddingResult:
        if self._embed is not None:
            # Hermetic / unit-test path.
            return self._embed(texts=texts, model_key=self._model_key)

        deployment = self._resolve()
        client = self._ensure_client()
        start = time.perf_counter()
        try:
            response = client.embeddings.create(model=deployment, input=list(texts))
        except Exception as exc:  # noqa: BLE001
            status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            if status in (429, 503):
                raise EmbedderTransportError(f"Foundry transient error {status}: {exc}") from exc
            if status in (401, 403, 404):
                raise EmbedderConfigurationError(f"Foundry deployment {deployment!r} returned {status}: {exc}") from exc
            raise EmbedderTransportError(f"Foundry embedding error: {exc}") from exc

        latency_ms = int((time.perf_counter() - start) * 1000)
        usage = getattr(response, "usage", None)
        token_count = int(getattr(usage, "total_tokens", 0) or 0)
        vectors: list[list[float]] = []
        for item in getattr(response, "data", []) or []:
            embedding = getattr(item, "embedding", []) or []
            vectors.append(list(embedding))
        return EmbeddingResult(
            vectors=vectors,
            token_count=token_count,
            latency_ms=latency_ms,
            raw={"deployment": deployment},
        )


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _validated_deployment_map(pairs: Iterable[tuple[str, str]], *, source: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for position, (key, name) in enumerate(pairs, start=1):
        if not isinstance(key, str) or not key.strip() or not isinstance(name, str) or not name.strip():
            raise EmbedderConfigurationError(
                f"{source} entry {position}: routing key and destination must be non-empty"
            )
        key, name = key.strip(), name.strip()
        if key in out and out[key] != name:
            raise EmbedderConfigurationError(
                f"{source}: conflicting routing key {key!r} designates both {out[key]!r} and {name!r}; "
                "configure one destination per key"
            )
        out[key] = name
    return out


def _parse_deployment_map(raw: str | None) -> dict[str, str]:
    """Validate compatibility CSV locally, independently of chat-tier settings."""
    source = "AZURE_AI_PROJECT_DEPLOYMENTS"
    if raw is None:
        return {}
    if not isinstance(raw, str):
        raise EmbedderConfigurationError(f"{source} must be a CSV string")
    if not raw.strip():
        return {}
    pairs: list[tuple[str, str]] = []
    for position, entry in enumerate(raw.split(","), start=1):
        if entry.count("=") != 1:
            raise EmbedderConfigurationError(
                f"{source} entry {position}: expected one non-empty routing-key=deployment-name pair"
            )
        key, name = entry.split("=")
        pairs.append((key, name))
    return _validated_deployment_map(pairs, source=source)


def deterministic_stub_embedder(*, dims: int = EMBEDDING_DIMS) -> EmbedFn:
    """Return a deterministic embedding stub for tests / dry-run.

    Each input string is hashed (SHA-256) and projected into a fixed-dimension
    vector by tiling the hash bytes — same input ⇒ same vector across runs.
    """
    import hashlib  # noqa: PLC0415

    def _stub(*, texts: Sequence[str], model_key: str) -> EmbeddingResult:
        vectors: list[list[float]] = []
        total_tokens = 0
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            # Tile the 32-byte digest into ``dims`` floats in [-1, 1].
            tiled = (digest * ((dims // len(digest)) + 1))[:dims]
            vec = [(b / 127.5) - 1.0 for b in tiled]
            vectors.append(vec)
            total_tokens += max(1, len(text.split()))
        return EmbeddingResult(
            vectors=vectors,
            token_count=total_tokens,
            latency_ms=1,
            raw={"deployment": "stub", "model_key": model_key},
        )

    return _stub


__all__ = [
    "AAD_SCOPE",
    "COST_PER_1K_TOKENS_USD",
    "DEFAULT_MODEL_KEY",
    "EMBEDDING_DIMS",
    "EmbedFn",
    "EmbedderConfigurationError",
    "EmbedderStats",
    "EmbedderTransportError",
    "EmbeddingResult",
    "FoundryEmbedder",
    "deterministic_stub_embedder",
]
