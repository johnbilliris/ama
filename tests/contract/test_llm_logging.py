import logging
from types import SimpleNamespace

import pytest
from common.foundry_chat_client import FoundryResponse

from apps.agents.common.llm_client import LLMClient
from apps.agents.common.llm_config import LLMClientConfig


def test_llm_logging_with_real_wrapper_and_transport_double(caplog) -> None:
    captured: dict[str, object] = {}

    def _chat_complete(**kwargs: object) -> FoundryResponse:
        captured.update(kwargs)
        return FoundryResponse(
            text="Risk remains high for sector alpha sig-401.",
            finish_reason="stop",
            usage_prompt_tokens=15,
            usage_completion_tokens=25,
            latency_ms=21,
            safety_filter_triggered=False,
            deployment_id="reasoning-1",
            raw={"deployment": "reasoning-1"},
        )

    client = LLMClient(config=LLMClientConfig(endpoint=""), chat_complete=_chat_complete)

    with caplog.at_level(logging.INFO):
        response = client.generate_response(
            purpose="reasoning",
            prompt="Summarise risk for sig-401",
            correlation_id="test-correlation",
            max_output_tokens=64,
        )

    assert captured.get("correlation_id") == "test-correlation"
    assert captured.get("timeout_s") is not None
    assert response["deployment_id"] == "reasoning-1"
    assert response["token_usage"]["input_tokens"] == 15
    assert response["token_usage"]["output_tokens"] == 25

    combined = "\n".join(caplog.messages)
    assert "correlation_id=test-correlation" in combined
    assert "deployment_id=reasoning-1" in combined
    assert "input_tokens=15" in combined
    assert "output_tokens=25" in combined
    assert "latency_ms=" in combined


def test_llm_wrapper_fails_when_foundry_response_lacks_deployment_id() -> None:
    def _chat_complete_missing_deployment(**kwargs: object):
        _ = kwargs
        return SimpleNamespace(
            text="content",
            usage_prompt_tokens=3,
            usage_completion_tokens=5,
            latency_ms=1,
        )

    client = LLMClient(config=LLMClientConfig(endpoint=""), chat_complete=_chat_complete_missing_deployment)

    with pytest.raises(RuntimeError, match="missing deployment_id"):
        client.generate_response(
            purpose="reasoning",
            prompt="Summarise risk",
            correlation_id="test-correlation",
        )
