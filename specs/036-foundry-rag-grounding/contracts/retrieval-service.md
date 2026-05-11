# Contract — `RetrievalService` (FR-RAG-AG-01 / FR-RAG-SIM-01)

**Spec**: 036-foundry-rag-grounding
**Status**: DRAFT (spec.md frozen; this contract is the binding reference for `/speckit.tasks`)
**Owner module**: `apps/agents/common/retrieval_client.py` (NEW — file name aligned with plan.md §Project Structure and tasks.md T075; the `RetrievalService` Protocol type lives in this module)
**Consumers**: every grounded agent (`MonitoringAgent`, `RiskAssessmentAgent`, `EvacuationAgent`, `ResourceAllocationAgent`, `CommunicationAgent`) and the simulation Controller (`apps/api/app/services/simulation/controller_service.py`).

This contract defines the **shared retrieval client** invoked by all grounded callers before each prompt-bearing inference. It binds:

- the Python `Protocol` consumed by callers (FR-RAG-AG-01, FR-RAG-SIM-01),
- the wire shapes of `RetrievalRequest` and `RetrievalResult` (mirror of `data-model.md`),
- the optional REST surface `POST /v1/retrieve` (deferred — Container-Apps internal only; no public ingress per Constitution §NN-2),
- the hermetic-test stub pattern,
- the jurisdiction-union + RRF hybrid retrieval semantics (R-03, R-06).

---

## 1. Python `Protocol` (binding — caller contract)

```python
# apps/agents/common/retrieval_client.py
from __future__ import annotations
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field
from typing import Literal

Jurisdiction = Literal["act", "nsw", "nt", "qld", "sa", "tas", "vic", "wa", "national", "aidr"]
LicenceMode = Literal["full-text", "metadata-only"]


class RetrievalRequest(BaseModel):
    agent_name: Literal[
        "MonitoringAgent", "RiskAssessmentAgent", "EvacuationAgent",
        "ResourceAllocationAgent", "CommunicationAgent", "SimulationController",
    ]
    jurisdictions: list[Jurisdiction] = Field(min_length=1)
    hazard_type: str
    query_text: str
    top_k: int = Field(default=5, ge=1, le=20)
    classification_max: Literal["OFFICIAL"] = "OFFICIAL"
    tenant_id: str
    correlation_id: str


class RetrievedChunk(BaseModel):
    chunk_id: str
    sha256_of_chunk: str
    jurisdiction: Jurisdiction
    topic: str
    page: int = Field(ge=1)
    licence_mode: LicenceMode
    confidence: float = Field(ge=0.0, le=1.0)
    text: str | None = None     # present iff licence_mode == "full-text"
    summary: str | None = None  # present iff licence_mode == "metadata-only"
    source_url: str
    rendered_url: str


class RetrievalResult(BaseModel):
    chunks: list[RetrievedChunk]
    retrieval_latency_ms: int
    embedding_model_id: str
    corpus_build_sha: str
    classification_filter_applied: bool
    cache_hit: bool = False
    alias_active_index: str  # e.g. "corpus-v3"


@runtime_checkable
class RetrievalService(Protocol):
    """Shared retrieval port (FR-RAG-AG-01).

    Implementations:
      * `AzureSearchRetrievalService` — production (hybrid retrieval over the
        alias-active `corpus` index in Azure AI Search).
      * `OfflineCacheRetrievalService` — Field-Coordinator path (FR-RAG-LS-02);
        reads from the signed offline manifest.
      * `FakeRetrievalService` — hermetic test stub (see §6 below).
    """

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult: ...
```

### 1.1 Construction

```python
# Production wiring (Container Apps)
service = AzureSearchRetrievalService(
    endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
    credential=DefaultAzureCredential(),
    index_alias="corpus",          # alias points at the alias-active corpus-v{N}
    embedding_client=foundry_client,  # injected per FR-RAG-FM-07
)

# Constructor-injectable seam — FR-RAG-AG-01 + FR-RAG-FM-07 alignment.
# Tests pass FakeRetrievalService directly to the agent constructor.
```

---

## 2. Semantics

### 2.1 Jurisdiction union (R-03, FR-RAG-AG-04)

Server-side, the request's `jurisdictions[]` is unioned with `{"national", "aidr"}` before the AI Search filter clause is built. Example: a `RiskAssessmentAgent` request with `jurisdictions=["nsw"]` is rewritten to filter `jurisdiction in ("nsw", "national", "aidr")`. The original request is preserved on the `correlation_id`-tagged audit record; the union is logged as `jurisdiction_union_applied: true`.

### 2.2 Hybrid retrieval + Reciprocal Rank Fusion (R-06)

For each request:

1. Embed `query_text` via the Foundry-hosted `text-embedding-3-large` (3072 dims) (FR-RAG-IDX-02). Embedding call emits its own `AuditRecord` with `call_kind="embedding"` (R-13).
2. Issue **vector** search against the `embedding` field with `top = top_k * 4` (oversample for fusion).
3. Issue **BM25 / semantic** search against `text` + `topic` + `summary` with `top = top_k * 4`.
4. Apply the AI Search filter `jurisdiction in (union) and licence_mode in ('full-text','metadata-only')` to both arms.
5. Fuse with **RRF weights 0.7 vector / 0.3 lexical** (R-06); fuse score = `0.7 * 1/(60 + rank_v) + 0.3 * 1/(60 + rank_l)`.
6. Truncate to `top_k`; return.

Confidence per `RetrievedChunk.confidence` follows R-16: `min(embedding_similarity, semantic_coherence, licence_mode_safety_gate)`.

### 2.3 Empty result handling (FR-RAG-AG-05, FR-RAG-SIM-03)

If post-fusion `chunks[]` is empty, the service returns `RetrievalResult(chunks=[], …)`. Callers MUST NOT fabricate citations; agents fall back to template responses (spec-014 `_generate_with_fallback`); the simulation Controller emits `citations: []` with a "no corpus match — recommend operator verification" note.

### 2.4 Excluded licence mode (FR-RAG-IDX-02)

`licence_mode == "excluded"` chunks are never indexed and never returned. The retrieval service does not need to filter them at query time (the index never carried them).

### 2.5 Classification ceiling (FR-RAG-NS-07)

`classification_max` is fixed at `"OFFICIAL"`. Any path that would carry above-OFFICIAL content opts out of RAG entirely (FR-RAG-NS-07) and never reaches this service.

---

## 3. Latency & quotas

| Property | Target | Source |
|---|---|---|
| p50 retrieval latency | ≤ 250 ms | plan.md §Performance Goals (Solution-Architect memo target; non-binding) |
| p95 retrieval latency | ≤ 800 ms | plan.md §Performance Goals (Solution-Architect memo target; non-binding) — bounded by SC-012 (sim chat-turn p95 latency growth ≤ 30% over spec-024 baseline) |
| Embedding call timeout | 5 s | R-09 (per-agent quota) |
| Per-agent QPS soft cap | 10 RPS | R-09 |
| Per-agent QPS hard cap | 25 RPS | R-09 |

Quotas enforced via the model-gateway side-car (R-09) and audited; over-cap rejections downgrade the agent to template fallback.

---

## 4. Wire format — REST (optional / deferred)

If a future spec exposes retrieval over the network (e.g. for a non-Python consumer), the REST surface is:

```yaml
# OpenAPI 3.1 — informational; not provisioned in spec 036
openapi: 3.1.0
info:
  title: AMA RetrievalService
  version: 0.1.0
servers:
  - url: https://retrieval.internal.<env>.platform.local
paths:
  /v1/retrieve:
    post:
      operationId: retrieve
      security:
        - aadManagedIdentity: []
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/RetrievalRequest' }
      responses:
        '200':
          content:
            application/json:
              schema: { $ref: '#/components/schemas/RetrievalResult' }
        '422': { description: validation error }
        '429': { description: per-agent quota exceeded (R-09) }
        '503': { description: index alias not yet flipped (transient during blue-green cutover) }
components:
  securitySchemes:
    aadManagedIdentity:
      type: oauth2
      flows:
        clientCredentials:
          tokenUrl: https://login.microsoftonline.com/<tenant>/oauth2/v2.0/token
          scopes:
            https://search.azure.com/.default: AI Search data plane
  schemas:
    RetrievalRequest: { description: see §1 above }
    RetrievalResult:  { description: see §1 above }
```

**Spec 036 ships only the in-process Python port (§1).** The REST surface is documented here so a future spec can lift it without contract drift.

---

## 5. Failure modes & graceful degradation

| Failure | Behaviour | Audit |
|---|---|---|
| Embedding call timeout | Return `RetrievalResult(chunks=[], cache_hit=false)` after 5 s; agent falls back to template | `embedding_timeout` event |
| AI Search 503 (transient blue-green flip) | Retry once with 100 ms backoff; on second 503 return empty `chunks[]` | `search_503` event |
| Index alias unset | `RuntimeError` at construction; Container App fails health probe (fail-closed per Constitution Principle I) | startup failure |
| Per-agent quota exceeded (R-09) | Return empty `chunks[]`; agent falls back to template | `retrieval_quota_exceeded` event |
| `embedding_model_id` mismatch between query embedding and index | Hard error (signals R-05 invariant violation); CD pre-deploy gate would have caught this | `embedding_model_mismatch` event + Sev2 page |

---

## 6. Hermetic test stub

```python
# tests/contract/test_retrieval_service.py
from apps.agents.common.retrieval_client import RetrievalService, RetrievalRequest, RetrievalResult, RetrievedChunk

class FakeRetrievalService:
    """Deterministic stub for hermetic agent + sim contract tests.

    Conforms to RetrievalService Protocol via duck-typing (runtime_checkable).
    No network calls; no Foundry; no Azure AI Search.
    """

    def __init__(self, fixture: list[RetrievedChunk] | None = None) -> None:
        self._fixture = fixture or []

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        # Honour jurisdiction union semantics in the fixture filter so contract tests
        # exercise the same surface as production (R-03).
        union = set(request.jurisdictions) | {"national", "aidr"}
        chunks = [c for c in self._fixture if c.jurisdiction in union][: request.top_k]
        return RetrievalResult(
            chunks=chunks,
            retrieval_latency_ms=1,
            embedding_model_id="text-embedding-3-large",
            corpus_build_sha="0" * 64,
            classification_filter_applied=False,
            cache_hit=False,
            alias_active_index="corpus-test",
        )


def test_retrieval_service_protocol_compliance():
    fake = FakeRetrievalService()
    assert isinstance(fake, RetrievalService)


async def test_jurisdiction_union_applied():
    fixture = [
        RetrievedChunk(chunk_id="n1", sha256_of_chunk="a"*64, jurisdiction="national",
                        topic="aiims", page=12, licence_mode="full-text", confidence=0.9,
                        text="…", source_url="https://x", rendered_url="/docs/corpus/national/aiims/handbook.md#page-12"),
        RetrievedChunk(chunk_id="v1", sha256_of_chunk="b"*64, jurisdiction="vic",
                        topic="evac", page=3, licence_mode="full-text", confidence=0.8,
                        text="…", source_url="https://x", rendered_url="/docs/corpus/vic/evac/handbook.md#page-3"),
    ]
    fake = FakeRetrievalService(fixture)
    result = await fake.retrieve(RetrievalRequest(
        agent_name="RiskAssessmentAgent",
        jurisdictions=["nsw"],
        hazard_type="bushfire",
        query_text="aiims span of control",
        top_k=5,
        tenant_id="t1",
        correlation_id="c1",
    ))
    # 'national' is in the union; 'vic' is not.
    chunk_ids = [c.chunk_id for c in result.chunks]
    assert "n1" in chunk_ids
    assert "v1" not in chunk_ids
```

This stub is the canonical `FakeRetrievalService` referenced by every contract + integration test under `tests/contract/test_*_grounding.py` and `tests/integration/test_simulation_grounding.py`.

---

## 7. Mapping to FRs / SCs / data-model

| Surface | FR / SC | Source |
|---|---|---|
| `RetrievalService.retrieve` | FR-RAG-AG-01, FR-RAG-SIM-01 | spec.md §Functional Requirements |
| `RetrievalRequest` / `RetrievalResult` shapes | data-model.md §RetrievalRequest, §RetrievalResult | data-model.md L96–138 |
| Jurisdiction union | FR-RAG-AG-04, R-03 | research.md R-03 |
| Hybrid + RRF | R-06 | research.md R-06 |
| Confidence | R-16 | research.md R-16 |
| Empty-result handling | FR-RAG-AG-05, FR-RAG-SIM-03 | spec.md §FR-RAG-AG-05 |
| Latency budget (sim chat-turn) | SC-012 | spec.md §Success Criteria |
| Per-agent quota | R-09 | research.md R-09 |
| Hermetic test seam | FR-RAG-FM-07 | spec.md §FR-RAG-FM-07 |
| Excluded licence mode | FR-RAG-IDX-02 | spec.md §FR-RAG-IDX-02 |
| Classification ceiling | FR-RAG-NS-07 | spec.md §FR-RAG-NS-07 |
