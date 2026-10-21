from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pytest
from common.foundry_chat_client import FoundryConfigurationError, FoundryGatewayDenied, LiveFoundryChatClient


@dataclass(frozen=True)
class _GatewayResult:
    gateway_decision: str
    transmitted_text: str
    reason: str = ""


def _stub_gateway() -> Callable[..., _GatewayResult]:
    def _apply(*, text: str, deployment_region: str) -> _GatewayResult:
        if "DENY" in text:
            return _GatewayResult(gateway_decision="deny", transmitted_text="", reason="policy")
        return _GatewayResult(gateway_decision="redact", transmitted_text=f"redacted::{text}")

    return _apply


def test_non_au_requires_region_to_be_set() -> None:
    client = LiveFoundryChatClient(region="", gateway_apply=_stub_gateway())
    with pytest.raises(FoundryConfigurationError):
        client._apply_gateway(messages=[{"role": "user", "content": "hello"}])


def test_gateway_applies_to_all_supported_text_content() -> None:
    client = LiveFoundryChatClient(region="eastus", gateway_apply=_stub_gateway())

    guarded = client._apply_gateway(
        messages=[
            {"role": "system", "content": "system prompt"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "user text"},
                    "inline string",
                    {"type": "input_image", "image_url": {"url": "https://example.invalid/image.png"}},
                ],
            },
            {"role": "tool", "content": "tool output"},
        ]
    )

    assert guarded[0]["content"] == "redacted::system prompt"
    assert guarded[1]["content"][0]["text"] == "redacted::user text"
    assert guarded[1]["content"][1] == "redacted::inline string"
    assert guarded[2]["content"] == "redacted::tool output"


def test_gateway_deny_fails_closed_for_any_supported_message_text() -> None:
    client = LiveFoundryChatClient(region="eastus", gateway_apply=_stub_gateway())
    with pytest.raises(FoundryGatewayDenied):
        client._apply_gateway(messages=[{"role": "assistant", "content": "DENY this"}])
