"""Contract tests: Confidence threshold gating (US6).

Verifies:
- Confidence below threshold → requires_human_review=True
- Confidence at/above threshold → normal escalation
- Template fallback → confidence multiplied by fallback_reduction_factor
"""

from __future__ import annotations

import pytest

from apps.agents.common.llm_config import LLMClientConfig
from apps.agents.common.llm_mixin import LLMCallMixin


class TestConfidenceGating:
    """Verify confidence threshold gating logic."""

    def _make_mixin(self, **config_kwargs) -> LLMCallMixin:
        defaults = {
            "endpoint": "",
            "model_tier": "drafting",
            "confidence_threshold": 0.7,
            "fallback_reduction_factor": 0.5,
        }
        defaults.update(config_kwargs)
        config = LLMClientConfig(**defaults)
        return LLMCallMixin(config)

    def test_confidence_below_threshold_flags_human_review(self) -> None:
        mixin = self._make_mixin()
        result = mixin._apply_confidence_gating(0.5, "llm")
        assert result["requires_human_review"] is True
        assert result["confidence"] == 0.5

    def test_confidence_at_threshold_no_review(self) -> None:
        mixin = self._make_mixin()
        result = mixin._apply_confidence_gating(0.7, "llm")
        assert result["requires_human_review"] is False
        assert result["confidence"] == 0.7

    def test_confidence_above_threshold_no_review(self) -> None:
        mixin = self._make_mixin()
        result = mixin._apply_confidence_gating(0.9, "llm")
        assert result["requires_human_review"] is False
        assert result["confidence"] == 0.9

    def test_template_fallback_reduces_confidence(self) -> None:
        mixin = self._make_mixin()
        result = mixin._apply_confidence_gating(0.8, "template_fallback")
        # 0.8 * 0.5 = 0.4, which is below 0.7
        assert result["confidence"] == 0.4
        assert result["requires_human_review"] is True

    def test_template_fallback_high_confidence_still_reduced(self) -> None:
        mixin = self._make_mixin()
        result = mixin._apply_confidence_gating(1.0, "template_fallback")
        # 1.0 * 0.5 = 0.5, still below 0.7
        assert result["confidence"] == 0.5
        assert result["requires_human_review"] is True

    def test_custom_threshold_and_factor(self) -> None:
        mixin = self._make_mixin(confidence_threshold=0.5, fallback_reduction_factor=0.9)
        result = mixin._apply_confidence_gating(0.6, "template_fallback")
        # 0.6 * 0.9 = 0.54, above 0.5
        assert result["confidence"] == pytest.approx(0.54)
        assert result["requires_human_review"] is False
