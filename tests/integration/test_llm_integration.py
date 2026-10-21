"""Integration tests: Full LLM call chain with fallback and circuit breaker.

Tests end-to-end flow: config → LLMClient (mocked) → content safety → response.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from apps.agents.common.llm_config import LLMClientConfig
from apps.agents.common.llm_mixin import LLMCallMixin


@pytest.fixture
def llm_mixin() -> LLMCallMixin:
    """Create an LLMCallMixin with an empty endpoint (no real LLM)."""
    config = LLMClientConfig(endpoint="", model_tier="drafting")
    return LLMCallMixin(config)


@pytest.fixture
def llm_mixin_with_mock() -> tuple[LLMCallMixin, MagicMock]:
    """Create an LLMCallMixin with mocked LLM client."""
    config = LLMClientConfig(
        endpoint="https://test.australiaeast.openai.azure.com",
        model_tier="drafting",
        reasoning_deployment="gpt-4o-dev",
        drafting_deployment="gpt-4o-mini-dev",
    )
    mixin = LLMCallMixin(config)
    mock_client = MagicMock()
    mixin._llm_client._client = mock_client
    return mixin, mock_client


@pytest.mark.integration
class TestLLMFallbackChain:
    """Test the full fallback chain: LLM → content safety → template."""

    def test_template_fallback_on_llm_error(self, llm_mixin: LLMCallMixin) -> None:
        """When LLM client has no endpoint, falls back to template."""
        result = llm_mixin._generate_with_fallback(
            purpose="drafting",
            prompt="test prompt",
            template_text="fallback template text",
        )
        assert result["generation_method"] == "template_fallback"
        assert result["text"] == "fallback template text"
        assert result["circuit_breaker_state"] in ("closed", "open", "half_open")
        assert result["confidence_adjustment"] == 0.5

    def test_circuit_breaker_opens_after_failures(self, llm_mixin: LLMCallMixin) -> None:
        """Circuit breaker opens after 3 consecutive failures."""
        for _ in range(3):
            llm_mixin._generate_with_fallback(
                purpose="drafting",
                prompt="test",
                template_text="fallback",
            )
        assert llm_mixin._circuit_breaker.state.value == "open"

    def test_circuit_breaker_skips_llm_when_open(self, llm_mixin: LLMCallMixin) -> None:
        """When circuit is OPEN, LLM is not called — direct template fallback."""
        # Force circuit breaker open
        for _ in range(3):
            llm_mixin._circuit_breaker.record_failure()
        assert llm_mixin._circuit_breaker.state.value == "open"

        result = llm_mixin._generate_with_fallback(
            purpose="drafting",
            prompt="test",
            template_text="fallback",
        )
        assert result["generation_method"] == "template_fallback"
        assert result["circuit_breaker_state"] == "open"

    def test_fallback_response_includes_required_fields(self, llm_mixin: LLMCallMixin) -> None:
        """Fallback response contains all required fields."""
        result = llm_mixin._generate_with_fallback(
            purpose="drafting",
            prompt="test",
            template_text="fallback",
            correlation_id="test-corr-123",
        )
        assert "text" in result
        assert "generation_method" in result
        assert "model_deployment_id" in result
        assert "token_usage" in result
        assert "content_safety_result" in result
        assert "circuit_breaker_state" in result
        assert "confidence_adjustment" in result

    def test_confidence_gating_flags_low_confidence(self, llm_mixin: LLMCallMixin) -> None:
        """Low confidence outputs are flagged for human review."""
        gating = llm_mixin._apply_confidence_gating(0.5, "llm")
        assert gating["requires_human_review"] is True
        assert gating["confidence"] == 0.5

    def test_confidence_gating_template_fallback_reduction(self, llm_mixin: LLMCallMixin) -> None:
        """Template fallback reduces confidence by fallback factor."""
        gating = llm_mixin._apply_confidence_gating(0.8, "template_fallback")
        assert gating["confidence"] == pytest.approx(0.4)
        assert gating["requires_human_review"] is True


@pytest.mark.integration
class TestLLMSuccessPath:
    """Test successful LLM response paths."""

    def test_successful_llm_response(self, llm_mixin_with_mock: tuple) -> None:
        """Successful LLM response returns llm generation_method."""
        mixin, mock_client = llm_mixin_with_mock

        # Mock the chat completion response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a safe test response"
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 20

        mock_client.chat.completions.create.return_value = mock_response

        result = mixin._generate_with_fallback(
            purpose="drafting",
            prompt="Generate a test response",
            template_text="fallback text",
        )
        assert result["generation_method"] == "llm"
        assert result["text"] == "This is a safe test response"
        assert result["content_safety_result"] == "passed"
        assert result["circuit_breaker_state"] == "closed"
        assert result["confidence_adjustment"] is None

    def test_content_safety_blocks_unsafe_output(self, llm_mixin_with_mock: tuple) -> None:
        """Content safety blocks LLM output with blocked keywords."""
        mixin, mock_client = llm_mixin_with_mock

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "terror threat detected"
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 10

        mock_client.chat.completions.create.return_value = mock_response

        result = mixin._generate_with_fallback(
            purpose="drafting",
            prompt="test",
            template_text="safe fallback",
        )
        assert result["generation_method"] == "safety_fallback"
        assert result["text"] == "safe fallback"

    def test_token_usage_in_response(self, llm_mixin_with_mock: tuple) -> None:
        """Token usage is included in successful responses."""
        mixin, mock_client = llm_mixin_with_mock

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Valid response text"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50

        mock_client.chat.completions.create.return_value = mock_response

        result = mixin._generate_with_fallback(
            purpose="drafting",
            prompt="test",
            template_text="fallback",
        )
        assert result["actual_token_usage"]["input_tokens"] == 100
        assert result["actual_token_usage"]["output_tokens"] == 50
