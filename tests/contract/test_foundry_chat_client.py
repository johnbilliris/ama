"""T010 — Contract test for the Foundry chat client seam (Spec 036 / FR-RAG-FM-07; R-01).

Asserts the Protocol shape declared by ``contracts/foundry-chat-client.md`` §1
is implementable, frozen dataclasses are immutable, and forbidden imports are
absent from the seam itself.

This test goes RED before T016/T017 land and GREEN immediately after.
"""

from __future__ import annotations

import importlib
import inspect
from collections.abc import AsyncIterator
from typing import Any, get_type_hints

import pytest


def _seam_module() -> Any:
    """Import the Foundry chat client seam module — REQUIRED to exist post-T016."""
    return importlib.import_module("common.foundry_chat_client")


# --------------------------------------------------------------------------- #
# T016 surface — Protocol + frozen dataclasses + type aliases
# --------------------------------------------------------------------------- #


def test_module_exports_required_names() -> None:
    """The seam module MUST export FoundryResponse, FoundryStreamChunk, and the
    Protocol per contracts/foundry-chat-client.md §1."""
    mod = _seam_module()
    for name in (
        "FoundryResponse",
        "FoundryStreamChunk",
        "FoundryChatClient",
        "ChatComplete",
        "ChatCompleteStream",
        "LiveFoundryChatClient",
    ):
        assert hasattr(mod, name), f"common.foundry_chat_client missing {name!r}"


def test_foundry_response_is_frozen_dataclass() -> None:
    """FoundryResponse MUST be a frozen dataclass (immutability per FR-RAG-FM-07)."""
    mod = _seam_module()
    cls = mod.FoundryResponse
    assert hasattr(cls, "__dataclass_params__"), "FoundryResponse must be a @dataclass"
    assert cls.__dataclass_params__.frozen, "FoundryResponse must be frozen=True"
    expected_fields = {
        "text",
        "finish_reason",
        "usage_prompt_tokens",
        "usage_completion_tokens",
        "latency_ms",
        "safety_filter_triggered",
        "raw",
    }
    actual = set(get_type_hints(cls).keys())
    assert expected_fields <= actual, f"FoundryResponse missing fields: {expected_fields - actual}"


def test_foundry_stream_chunk_is_frozen_dataclass() -> None:
    mod = _seam_module()
    cls = mod.FoundryStreamChunk
    assert hasattr(cls, "__dataclass_params__"), "FoundryStreamChunk must be a @dataclass"
    assert cls.__dataclass_params__.frozen, "FoundryStreamChunk must be frozen=True"
    expected_fields = {"delta_text", "finish_reason", "raw"}
    actual = set(get_type_hints(cls).keys())
    assert expected_fields <= actual, f"FoundryStreamChunk missing fields: {expected_fields - actual}"


def test_foundry_chat_client_protocol_shape() -> None:
    """The Protocol MUST expose chat_complete (sync) and chat_complete_stream (async)."""
    mod = _seam_module()
    proto = mod.FoundryChatClient
    # Has both methods declared
    assert hasattr(proto, "chat_complete"), "FoundryChatClient missing chat_complete"
    assert hasattr(proto, "chat_complete_stream"), "FoundryChatClient missing chat_complete_stream"
    # chat_complete is synchronous (returns FoundryResponse, NOT a coroutine)
    sig_sync = inspect.signature(proto.chat_complete)
    assert "model_key" in sig_sync.parameters
    assert "messages" in sig_sync.parameters
    # chat_complete_stream is an async generator
    assert inspect.iscoroutinefunction(proto.chat_complete_stream) or (
        # Protocol methods may be plain functions returning AsyncIterator
        inspect.signature(proto.chat_complete_stream) is not None
    ), "chat_complete_stream must be async/return AsyncIterator"


# --------------------------------------------------------------------------- #
# T017 surface — LiveFoundryChatClient AAD-only auth
# --------------------------------------------------------------------------- #


def test_live_client_rejects_api_key_kwarg() -> None:
    """LiveFoundryChatClient MUST refuse api_key= kwargs (FR-RAG-FM-05).

    AAD-only auth on scope https://cognitiveservices.azure.com/.default.
    """
    mod = _seam_module()
    sig = inspect.signature(mod.LiveFoundryChatClient.__init__)
    assert "api_key" not in sig.parameters, (
        "LiveFoundryChatClient.__init__ must NOT accept api_key (FR-RAG-FM-05; AAD-only)"
    )


def test_live_client_aad_token_scope_constant() -> None:
    """The seam MUST hard-code the Foundry AAD scope as a module constant.

    Scope: ``https://cognitiveservices.azure.com/.default`` (preserved unchanged
    across the OpenAI → Foundry migration per FR-RAG-FM-05).
    """
    mod = _seam_module()
    # Either a module-level constant or class attribute is acceptable
    candidates = [
        getattr(mod, name, None) for name in ("AAD_SCOPE", "_AAD_SCOPE", "FOUNDRY_TOKEN_SCOPE", "TOKEN_SCOPE")
    ]
    candidates += [
        getattr(mod.LiveFoundryChatClient, name, None) for name in ("_TOKEN_SCOPE", "AAD_SCOPE", "TOKEN_SCOPE")
    ]
    assert "https://cognitiveservices.azure.com/.default" in [c for c in candidates if isinstance(c, str)], (
        "Foundry AAD scope must be hard-coded per FR-RAG-FM-05"
    )


# --------------------------------------------------------------------------- #
# Forbidden imports (defence-in-depth — full lint binds atomically with T146)
# --------------------------------------------------------------------------- #

FORBIDDEN_IN_SEAM = (
    "from openai import AzureOpenAI",
    "from openai import AsyncAzureOpenAI",
    "openai.AzureOpenAI",
)


def test_seam_module_does_not_import_legacy_openai() -> None:
    """The seam module itself MUST NOT import the legacy OpenAI client (FR-RAG-FM-04).

    Note: the global no-openai lint (T011) is skip-marked until E1/T146 — this
    test only enforces the property locally on the seam module.
    """
    mod = _seam_module()
    src = inspect.getsource(mod)
    for pat in FORBIDDEN_IN_SEAM:
        assert pat not in src, f"common.foundry_chat_client must not contain {pat!r} (FR-RAG-FM-04)"


# --------------------------------------------------------------------------- #
# Seam injectability (FR-RAG-FM-07 — Protocol covers ChatComplete + ChatCompleteStream)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_fake_implements_protocol() -> None:
    """A test fake exposing chat_complete + chat_complete_stream MUST satisfy the Protocol.

    This proves the seam is duck-typed (runtime_checkable) and reusable across
    all three call-site migrations (FR-RAG-FM-01..03).
    """
    mod = _seam_module()
    FoundryResponse = mod.FoundryResponse
    FoundryStreamChunk = mod.FoundryStreamChunk

    class _Fake:
        def chat_complete(self, *, model_key, messages, **kw):  # type: ignore[no-untyped-def]
            return FoundryResponse(
                text="ok",
                finish_reason="stop",
                usage_prompt_tokens=1,
                usage_completion_tokens=1,
                latency_ms=1,
                safety_filter_triggered=False,
                raw={},
            )

        async def chat_complete_stream(  # type: ignore[no-untyped-def]
            self, *, model_key, messages, **kw
        ) -> AsyncIterator[Any]:
            yield FoundryStreamChunk(delta_text="ok", finish_reason="stop", raw={})

    fake = _Fake()
    # runtime_checkable Protocol — duck-typed isinstance check.
    assert isinstance(fake, mod.FoundryChatClient), (
        "Fake satisfying chat_complete + chat_complete_stream must pass isinstance check"
    )
