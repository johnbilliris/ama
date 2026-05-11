# Contract — Foundry Chat Client Seam (FR-RAG-FM-01 / FM-02 / FM-03 / FM-07)

**Spec**: 036-foundry-rag-grounding
**Status**: DRAFT (spec.md frozen; this contract is the binding reference for `/speckit.tasks`)
**Authority**: Constitution §NN-2 Amendment 1.2.0 (Foundry carve-out); spec.md FR-RAG-FM-01..07.

This contract defines the **constructor-injectable `chat_complete` callable seam** that all three Foundry call-site migrations MUST adopt:

| Module | Migration | Source FR |
|---|---|---|
| `apps/agents/common/llm_client.py` | `openai.AzureOpenAI` → Foundry chat client | FR-RAG-FM-01 |
| `apps/agents/maf_runtime/chat_client.py` | `agent_framework_openai.OpenAIChatClient` → Foundry chat client (factory signature preserved) | FR-RAG-FM-02 |
| `apps/api/app/services/simulation/controller_service.py` | `AsyncAzureOpenAI` → Foundry async chat client | FR-RAG-FM-03 |

The seam pattern mirrors the **already-shipped reference** in `apps/eval-runner/src/ama_eval/foundry_client.py`. Spec 036 lifts that pattern from a one-off into a **shared shape** consumed by all three call sites.

---

## 1. Python `Protocol` (binding)

```python
# apps/agents/common/foundry_chat_client.py  (NEW)
from __future__ import annotations
from collections.abc import Callable, AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class FoundryResponse:
    """Mirrors apps/eval-runner/src/ama_eval/foundry_client.py FoundryResponse."""
    text: str
    finish_reason: str
    usage_prompt_tokens: int
    usage_completion_tokens: int
    latency_ms: int
    safety_filter_triggered: bool
    raw: dict[str, Any]


@dataclass(frozen=True)
class FoundryStreamChunk:
    """Streamed token / delta. Carries only the fields the simulation Controller
    needs for its existing SSE emission (FR-RAG-FM-03 / spec 024)."""
    delta_text: str
    finish_reason: str | None
    raw: dict[str, Any]


# Synchronous chat (LLMClient.generate_response — FR-RAG-FM-01, FR-RAG-FM-02)
ChatComplete = Callable[..., FoundryResponse]

# Asynchronous streaming chat (Controller.handle_chat_turn — FR-RAG-FM-03)
ChatCompleteStream = Callable[..., AsyncIterator[FoundryStreamChunk]]


@runtime_checkable
class FoundryChatClient(Protocol):
    """The unified Foundry seam. Production wires Azure AI Inference SDK
    (`azure-ai-inference.ChatCompletionsClient`) under DefaultAzureCredential
    against scope `https://cognitiveservices.azure.com/.default`.

    Tests inject a fake by passing `chat_complete=FakeFoundryClient(...).chat_complete`
    into the production class — no monkey-patching the SDK transport.
    """

    def chat_complete(
        self,
        *,
        model_key: str,        # e.g. "gpt-4o-mini@2024-07-18"
        messages: list[dict],  # OpenAI-style messages list (preserved across migration)
        tools: list[dict] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout_s: float = 30.0,
    ) -> FoundryResponse: ...

    async def chat_complete_stream(
        self,
        *,
        model_key: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout_s: float = 60.0,
    ) -> AsyncIterator[FoundryStreamChunk]: ...
```

---

## 2. Production wiring

### 2.1 `LiveFoundryChatClient` (the live class)

```python
# apps/agents/common/foundry_chat_client.py
import os
from azure.ai.inference import ChatCompletionsClient                        # sync
from azure.ai.inference.aio import ChatCompletionsClient as AsyncChatClient  # async/streaming
from azure.identity import DefaultAzureCredential
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential


class LiveFoundryChatClient:
    """Production Foundry chat client. AAD-only; api_key arg is rejected.

    Reads:
      AZURE_AI_PROJECT_ENDPOINT       # Foundry account endpoint
      AZURE_AI_PROJECT_DEPLOYMENTS    # CSV of `modelId@version=deploymentName`

    Token scope: `https://cognitiveservices.azure.com/.default`
      (preserved unchanged across the OpenAI → Foundry migration — FR-RAG-FM-05).
    """

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        deployments: dict[str, str] | None = None,
        credential: Any | None = None,
    ) -> None:
        self._endpoint = endpoint or os.environ["AZURE_AI_PROJECT_ENDPOINT"]
        self._deployments = deployments or _parse_deployment_map(
            os.environ.get("AZURE_AI_PROJECT_DEPLOYMENTS")
        )
        self._cred = credential or DefaultAzureCredential()
        self._async_cred = AsyncDefaultAzureCredential()
        self._sync = ChatCompletionsClient(endpoint=self._endpoint, credential=self._cred)
        self._async = AsyncChatClient(endpoint=self._endpoint, credential=self._async_cred)

    def chat_complete(self, *, model_key: str, messages: list[dict], **kw) -> FoundryResponse:
        deployment = self._resolve(model_key)
        # ... call self._sync.complete(...); map response to FoundryResponse
        ...

    async def chat_complete_stream(self, *, model_key: str, messages: list[dict], **kw) -> AsyncIterator[FoundryStreamChunk]:
        deployment = self._resolve(model_key)
        # ... call self._async.complete(stream=True, ...); yield FoundryStreamChunk per delta
        ...

    def _resolve(self, model_key: str) -> str:
        # Preferred: 'modelId@version' match. Fallback: 'modelId' (version-agnostic).
        if model_key in self._deployments:
            return self._deployments[model_key]
        base = model_key.split("@", 1)[0]
        if base in self._deployments:
            return self._deployments[base]
        raise FoundryConfigurationError(f"no deployment for {model_key!r}")
```

### 2.2 The three migration anchors — REQUIRED constructor signatures

#### `apps/agents/common/llm_client.py` (FR-RAG-FM-01)

```python
class LLMClient:
    def __init__(
        self,
        *,
        chat_complete: ChatComplete | None = None,   # NEW seam (FR-RAG-FM-07)
        retrieval_service: RetrievalService | None = None,
        # ... existing kwargs preserved
    ) -> None:
        if chat_complete is None:
            chat_complete = LiveFoundryChatClient().chat_complete
        self._chat = chat_complete
        self._retrieval = retrieval_service
        # ...
```

The pre-existing `_generate_with_fallback` template-fallback chain (spec 014) MUST remain intact — Foundry-side regressions degrade to template, never silence (FR-RAG-FM-06; Constitution Principle I).

#### `apps/agents/maf_runtime/chat_client.py` (FR-RAG-FM-02)

The factory function signature is **preserved** so MAF Agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication) keep their constructor contract:

```python
def build_chat_client(
    *,
    chat_complete: ChatComplete | None = None,  # NEW seam (FR-RAG-FM-07)
    # ... existing kwargs preserved
) -> ChatClientLike:
    """Factory used by MAF Agent constructors. Preserved across the Foundry migration."""
    if chat_complete is None:
        chat_complete = LiveFoundryChatClient().chat_complete
    return _FoundryAgentChatClient(chat_complete=chat_complete, ...)
```

#### `apps/api/app/services/simulation/controller_service.py` (FR-RAG-FM-03)

```python
class SimulationControllerService:
    def __init__(
        self,
        *,
        chat_complete_stream: ChatCompleteStream | None = None,  # NEW seam (FR-RAG-FM-07)
        retrieval_service: RetrievalService | None = None,
        # ... existing kwargs preserved
    ) -> None:
        if chat_complete_stream is None:
            chat_complete_stream = LiveFoundryChatClient().chat_complete_stream
        self._stream = chat_complete_stream
        self._retrieval = retrieval_service
        # ... existing controller_prompt.md system prompt + tool manifest (spec 024) preserved
```

---

## 3. Forbidden imports (FR-RAG-FM-04)

CI lint MUST fail any PR that introduces:

```python
from openai import AzureOpenAI            # FR-RAG-FM-01 anchor
from openai import AsyncAzureOpenAI       # FR-RAG-FM-03 anchor
from agent_framework_openai import OpenAIChatClient  # FR-RAG-FM-02 anchor (when used in azure_openai mode)
```

…outside of:

- (a) historical specs under `specs/01[0-4]-*/`,
- (b) the migration ADR (`docs/decisions/036-foundry-rag-grounding/00-foundry-cutover.md`),
- (c) explicitly-marked test fixtures with `# noqa: AMA-FM04` and a `tests/fixtures/legacy_aoai/` path.

The lint binds **atomically** in the same PR that deletes the legacy client (FR-RAG-FM-06) — never blocks an in-flight per-agent canary.

Implementation: `tools/lint/check_no_legacy_aoai.py` invoked by `ci.yml`.

---

## 4. Hermetic test stub

```python
# tests/fixtures/foundry_fakes.py
from collections.abc import AsyncIterator
from apps.agents.common.foundry_chat_client import FoundryResponse, FoundryStreamChunk, FoundryChatClient


class FakeFoundryClient:
    """Deterministic Foundry stub for hermetic contract + integration tests.

    Conforms to FoundryChatClient via duck-typing (runtime_checkable).
    No network; no AAD; no Azure AI Inference SDK transport.
    """

    def __init__(
        self,
        *,
        canned_response: str = "ok",
        canned_stream_chunks: list[str] | None = None,
        finish_reason: str = "stop",
        safety_filter_triggered: bool = False,
        raise_on_call: Exception | None = None,
    ) -> None:
        self._response = canned_response
        self._chunks = canned_stream_chunks or [canned_response]
        self._finish = finish_reason
        self._safety = safety_filter_triggered
        self._raise = raise_on_call
        self.calls: list[dict] = []

    def chat_complete(self, *, model_key, messages, tools=None, **kw) -> FoundryResponse:
        self.calls.append({"model_key": model_key, "messages": messages, "tools": tools})
        if self._raise:
            raise self._raise
        return FoundryResponse(
            text=self._response,
            finish_reason=self._finish,
            usage_prompt_tokens=10,
            usage_completion_tokens=20,
            latency_ms=1,
            safety_filter_triggered=self._safety,
            raw={"fake": True},
        )

    async def chat_complete_stream(self, *, model_key, messages, **kw) -> AsyncIterator[FoundryStreamChunk]:
        self.calls.append({"model_key": model_key, "messages": messages, "stream": True})
        if self._raise:
            raise self._raise
        for i, c in enumerate(self._chunks):
            yield FoundryStreamChunk(
                delta_text=c,
                finish_reason=self._finish if i == len(self._chunks) - 1 else None,
                raw={"fake": True, "i": i},
            )


def test_fake_protocol_compliance():
    fake = FakeFoundryClient()
    assert isinstance(fake, FoundryChatClient)


def test_agent_constructor_accepts_seam():
    """FR-RAG-FM-07: every agent and the simulation Controller MUST accept
    `chat_complete=` (or `chat_complete_stream=`) at construction."""
    from apps.agents.common.llm_client import LLMClient
    fake = FakeFoundryClient(canned_response="grounded answer")
    client = LLMClient(chat_complete=fake.chat_complete)
    response = client.generate_response("hello", agent_name="RiskAssessmentAgent")
    assert "grounded answer" in response
    assert len(fake.calls) == 1
```

This stub is the canonical `FakeFoundryClient` referenced by every contract test in `tests/contract/test_foundry_seam_*.py` and every integration test in `tests/integration/test_*_grounding.py`.

---

## 5. Failure modes

| Failure | Behaviour | Audit |
|---|---|---|
| Foundry 4xx (auth, deployment-not-found) | Raise `FoundryConfigurationError`; agent falls back to template (Constitution Principle I no-silencing) | `foundry_config_error` |
| Foundry 5xx / timeout | Raise `FoundryTransportError`; agent falls back to template | `foundry_transport_error` |
| Safety filter triggered | `FoundryResponse.safety_filter_triggered = true`; agent treats as "no answer" + logs | `safety_filter_triggered` |
| Embedding model mismatch (caller-side) | `FoundryEmbeddingMismatch`; ingest fails closed | startup failure |
| Per-agent quota exceeded (R-09) | Gateway returns 429; agent falls back to template | `foundry_quota_exceeded` |

All failure paths emit an `AuditRecord` with `call_kind="inference"`, `gateway_decision` populated, and `rag_used` set per the actual retrieval state.

---

## 6. Mapping to FRs / SCs / data-model

| Surface | FR / SC | Source |
|---|---|---|
| `FoundryChatClient.chat_complete` | FR-RAG-FM-01, FR-RAG-FM-02 | spec.md L205–206 |
| `FoundryChatClient.chat_complete_stream` | FR-RAG-FM-03 | spec.md L207 |
| `chat_complete=` constructor seam | FR-RAG-FM-07 | spec.md L211 |
| AAD-only auth, scope `https://cognitiveservices.azure.com/.default` | FR-RAG-FM-05 | spec.md L209 |
| No-legacy-AOAI lint | FR-RAG-FM-04 | spec.md L208 |
| Per-agent canary + equivalence gate (spec 029 + spec 033) | FR-RAG-FM-06 | spec.md L210 |
| `FoundryResponse` shape | mirror of `apps/eval-runner/src/ama_eval/foundry_client.py:28-36` | reference pattern |
| Constitution §NN-2 carve-out | every Foundry call traverses the gateway with a registered `(model_name, region)` row | Constitution L244–270 |
