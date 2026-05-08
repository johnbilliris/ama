"""Integration tests: Full LLM call chain with fallback and circuit breaker.

Tests end-to-end flow: config → LLMClient (mocked Foundry seam) → content
safety → response.

Spec 036 (T146): updated to use the constructor-injectable ``chat_complete``
seam (FR-RAG-FM-07) instead of the legacy ``self._client.chat.completions.create``
mock surface. The fixture wires ``LLMClient._chat_complete`` directly.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from apps.agents.common.llm_config import LLMClientConfig
from apps.agents.common.llm_mixin import LLMCallMixin


@pytest.fixture
def llm_mixin() -> LLMCallMixin:
    """Create an LLMCallMixin with no Foundry endpoint (no real LLM)."""
    config = LLMClientConfig(endpoint="", model_tier="drafting")
    return LLMCallMixin(config)


@pytest.fixture
def llm_mixin_with_mock() -> tuple[LLMCallMixin, MagicMock]:
    """Create an LLMCallMixin with a mocked Foundry seam (post-T146).

    Returns ``(mixin, mock_seam)`` where ``mock_seam`` is the callable bound
    to ``mixin._llm_client._chat_complete``. Tests configure
    ``mock_seam.return_value = <FoundryResponse-shaped mock>`` to stub the
    chat completion result.
    """
    config = LLMClientConfig(
        endpoint="https://test.australiaeast.openai.azure.com",
        model_tier="drafting",
        reasoning_deployment="gpt-4o-dev",
        drafting_deployment="gpt-4o-mini-dev",
    )
    mixin = LLMCallMixin(config)
    mock_seam = MagicMock()
    # Override the seam directly — bypasses Foundry SDK initialisation.
    mixin._llm_client._chat_complete = mock_seam
    return mixin, mock_seam


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


def _foundry_response(content: str, prompt_tokens: int, completion_tokens: int) -> MagicMock:
    """Build a ``FoundryResponse``-shaped mock with .choices[0].message.content + .usage."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    mock_response.usage.prompt_tokens = prompt_tokens
    mock_response.usage.completion_tokens = completion_tokens
    return mock_response


@pytest.mark.integration
class TestLLMSuccessPath:
    """Test successful LLM response paths via the Foundry seam (T146)."""

    def test_successful_llm_response(self, llm_mixin_with_mock: tuple) -> None:
        """Successful LLM response returns llm generation_method."""
        mixin, mock_seam = llm_mixin_with_mock
        mock_seam.return_value = _foundry_response("This is a safe test response", 50, 20)

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
        mixin, mock_seam = llm_mixin_with_mock
        mock_seam.return_value = _foundry_response("terror threat detected", 50, 10)

        result = mixin._generate_with_fallback(
            purpose="drafting",
            prompt="test",
            template_text="safe fallback",
        )
        assert result["generation_method"] == "safety_fallback"
        assert result["text"] == "safe fallback"

    def test_token_usage_in_response(self, llm_mixin_with_mock: tuple) -> None:
        """Token usage is included in successful responses."""
        mixin, mock_seam = llm_mixin_with_mock
        mock_seam.return_value = _foundry_response("Valid response text", 100, 50)

        result = mixin._generate_with_fallback(
            purpose="drafting",
            prompt="test",
            template_text="fallback",
        )
        assert result["token_usage"]["input_tokens"] == 100
        assert result["token_usage"]["output_tokens"] == 50
