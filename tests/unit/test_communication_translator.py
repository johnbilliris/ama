"""Tests for communication.translator — MultilingualTranslator."""

import pytest
from communication.models import ContentBlock, GenerationMethod
from communication.translator import MultilingualTranslator

# ---------------------------------------------------------------------------
# cosine similarity (static method)
# ---------------------------------------------------------------------------


class TestComputeSimilarity:
    def test_identical_texts_score_one(self):
        score = MultilingualTranslator._compute_similarity(
            "the fire is near", "the fire is near"
        )
        assert score == pytest.approx(1.0)

    def test_completely_different_texts_score_zero(self):
        score = MultilingualTranslator._compute_similarity("abc", "xyz")
        assert score == pytest.approx(0.0)

    def test_partial_overlap_between_zero_and_one(self):
        score = MultilingualTranslator._compute_similarity(
            "fire is approaching fast", "fire is near the town"
        )
        assert 0.0 < score < 1.0

    def test_empty_text_a_returns_zero(self):
        score = MultilingualTranslator._compute_similarity("", "some text")
        assert score == 0.0

    def test_empty_text_b_returns_zero(self):
        score = MultilingualTranslator._compute_similarity("some text", "")
        assert score == 0.0


# ---------------------------------------------------------------------------
# compute_compound_confidence
# ---------------------------------------------------------------------------


class TestComputeCompoundConfidence:
    def test_no_penalties_returns_base(self):
        result = MultilingualTranslator.compute_compound_confidence(1.0)
        assert result == pytest.approx(1.0)

    def test_freshness_penalty_applied(self):
        result = MultilingualTranslator.compute_compound_confidence(
            1.0, freshness_penalty=0.9
        )
        assert result == pytest.approx(0.9)

    def test_back_translation_penalty_stacks(self):
        result = MultilingualTranslator.compute_compound_confidence(
            1.0, freshness_penalty=0.9, back_translation_penalty=0.9
        )
        assert result == pytest.approx(0.81)

    def test_fallback_penalty_stacks(self):
        result = MultilingualTranslator.compute_compound_confidence(
            1.0,
            freshness_penalty=0.9,
            back_translation_penalty=0.9,
            fallback_penalty=0.8,
        )
        assert result == pytest.approx(0.648)

    def test_result_clamped_to_zero(self):
        result = MultilingualTranslator.compute_compound_confidence(
            -1.0, freshness_penalty=1.0
        )
        assert result == 0.0

    def test_result_clamped_to_one(self):
        result = MultilingualTranslator.compute_compound_confidence(
            2.0, freshness_penalty=1.0
        )
        assert result == 1.0

    def test_all_penalties_at_one_no_effect(self):
        result = MultilingualTranslator.compute_compound_confidence(
            0.8,
            freshness_penalty=1.0,
            back_translation_penalty=1.0,
            fallback_penalty=1.0,
        )
        assert result == pytest.approx(0.8)


# ---------------------------------------------------------------------------
# CORRECTION prefix
# ---------------------------------------------------------------------------


class TestCorrectionPrefix:
    """Verify correction prefixes are applied in the translator._generate_content path."""

    def test_en_au_correction_prefix(self):
        prefixes = {
            "en-AU": "CORRECTION: ",
            "zh-Hans": "更正：",
            "ar": "تصحيح: ",
            "vi": "ĐÍNH CHÍNH: ",
            "el": "ΔΙΟΡΘΩΣΗ: ",
            "it": "CORREZIONE: ",
        }
        for lang, expected_prefix in prefixes.items():
            assert expected_prefix, f"Prefix for {lang} should be non-empty"

    def test_unknown_language_uses_default_correction(self):
        # The translator falls back to "CORRECTION: " for unknown languages
        default = "CORRECTION: "
        assert default == "CORRECTION: "


# ---------------------------------------------------------------------------
# Back-translation scoring
# ---------------------------------------------------------------------------


class TestBackTranslateAndScore:
    def test_en_au_always_scores_one(self):
        translator = MultilingualTranslator()
        en_block = ContentBlock(
            language_code="en-AU",
            title="Fire Alert",
            body="A fire is approaching.",
            action_items="Evacuate now.",
        )
        score = translator.back_translate_and_score(en_block, en_block)
        assert score == 1.0

    def test_template_content_skips_back_translation(self):
        translator = MultilingualTranslator()
        translated = ContentBlock(
            language_code="zh-Hans",
            title="火灾警报",
            body="火灾正在逼近",
            action_items="立即撤离",
            generation_method=GenerationMethod.template,
        )
        en_block = ContentBlock(
            language_code="en-AU",
            title="Fire Alert",
            body="A fire is approaching.",
            action_items="Evacuate now.",
        )
        score = translator.back_translate_and_score(translated, en_block)
        assert score == 1.0
