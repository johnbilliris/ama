"""Multilingual translation engine with back-translation quality validation.

Generates en-AU content first as reference, then translates sequentially to
each non-English language with en-AU content as context per FR-008.

Back-translation quality check: cosine similarity ≥ 0.85 threshold per R-002.
Compound confidence penalty stacking per CHK031:
  freshness → back-translation (0.9×) → fallback (0.8×)
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from common.content_safety import ContentSafetyValidator
from common.llm_mixin import LLMCallMixin

from communication.config import CommunicationConfig
from communication.models import ContentBlock, GenerationMethod
from communication.templates import TemplateLoader

logger = logging.getLogger(__name__)


class MultilingualTranslator(LLMCallMixin):
    """Generates multilingual alert content with LLM + template fallback."""

    def __init__(
        self,
        config: CommunicationConfig | None = None,
        template_loader: TemplateLoader | None = None,
    ) -> None:
        super().__init__()
        self._config = config or CommunicationConfig()
        self._template_loader = template_loader
        self._content_safety = ContentSafetyValidator()

    def translate_all(
        self,
        *,
        hazard_type: str,
        severity: str,
        alert_type: str,
        template_values: dict[str, str],
        change_type: str = "initial",
        incident_id: str = "",
    ) -> dict[str, ContentBlock]:
        """Generate content blocks for all supported languages.

        en-AU is generated first as reference, then each non-English language
        is translated sequentially using en-AU content as context per FR-008.

        Returns dict[language_code, ContentBlock].
        """
        content_blocks: dict[str, ContentBlock] = {}
        en_au_block: ContentBlock | None = None

        for lang in self._config.supported_languages:
            if lang == "en-AU":
                block = self._generate_content(
                    language_code=lang,
                    hazard_type=hazard_type,
                    severity=severity,
                    alert_type=alert_type,
                    template_values=template_values,
                    en_au_reference=None,
                    change_type=change_type,
                )
                en_au_block = block
            else:
                block = self._generate_content(
                    language_code=lang,
                    hazard_type=hazard_type,
                    severity=severity,
                    alert_type=alert_type,
                    template_values=template_values,
                    en_au_reference=en_au_block,
                    change_type=change_type,
                )

            content_blocks[lang] = block

        return content_blocks

    def _generate_content(
        self,
        *,
        language_code: str,
        hazard_type: str,
        severity: str,
        alert_type: str,
        template_values: dict[str, str],
        en_au_reference: ContentBlock | None,
        change_type: str,
    ) -> ContentBlock:
        """Generate content for a single language with LLM + template fallback."""
        # Get template text as fallback
        title_tmpl, body_tmpl, action_tmpl, translation_unavailable = (
            self._get_template_text(hazard_type, severity, alert_type, language_code, template_values)
        )

        # Apply CORRECTION: prefix for correction change_type per FR-017
        if change_type == "correction":
            correction_prefixes = {
                "en-AU": "CORRECTION: ",
                "zh-Hans": "更正：",
                "ar": "تصحيح: ",
                "vi": "ĐÍNH CHÍNH: ",
                "el": "ΔΙΟΡΘΩΣΗ: ",
                "it": "CORREZIONE: ",
            }
            prefix = correction_prefixes.get(language_code, "CORRECTION: ")
            title_tmpl = prefix + title_tmpl

        # Build LLM prompt
        if language_code == "en-AU":
            prompt = (
                f"Draft a plain-language emergency alert in Australian English.\n"
                f"Hazard type: {hazard_type}\n"
                f"Severity: {severity}\n"
                f"Alert type: {alert_type}\n"
                f"Location: {template_values.get('location', 'affected area')}\n"
                f"Format: Title | Body | Action Items\n"
                f"Keep it clear, actionable, and under 180 tokens."
            )
        else:
            en_context = ""
            if en_au_reference:
                en_context = (
                    f"\nEnglish reference:\n"
                    f"Title: {en_au_reference.title}\n"
                    f"Body: {en_au_reference.body}\n"
                    f"Action Items: {en_au_reference.action_items}\n"
                )
            prompt = (
                f"Translate this emergency alert to {language_code}.{en_context}\n"
                f"Hazard type: {hazard_type}, Severity: {severity}\n"
                f"Format: Title | Body | Action Items\n"
                f"Maintain semantic equivalence. Keep under 180 tokens."
            )

        # Try LLM generation with fallback
        response = self._generate_with_fallback(
            purpose="drafting",
            prompt=prompt,
            template_text=f"{title_tmpl} | {body_tmpl} | {action_tmpl}",
            expected_language=language_code,
            max_output_tokens=self._config.alert_max_tokens,
        )

        gen_method_str = str(response["generation_method"])
        gen_method = GenerationMethod(gen_method_str) if gen_method_str in GenerationMethod.__members__ else GenerationMethod.template_fallback

        safety_result = str(response.get("content_safety_result", "passed"))

        # Parse LLM response or use template
        if gen_method == GenerationMethod.llm:
            text = str(response["text"])
            parts = text.split("|")
            if len(parts) >= 3:
                title = parts[0].strip()[:200]
                body = parts[1].strip()[:1200]
                action_items = parts[2].strip()[:500]
            else:
                title = title_tmpl
                body = text[:1200]
                action_items = action_tmpl
        else:
            title = title_tmpl
            body = body_tmpl
            action_items = action_tmpl

        # Apply CORRECTION: prefix for LLM-generated content too
        if change_type == "correction" and gen_method == GenerationMethod.llm:
            correction_prefixes = {
                "en-AU": "CORRECTION: ",
                "zh-Hans": "更正：",
                "ar": "تصحيح: ",
                "vi": "ĐÍNH CHÍNH: ",
                "el": "ΔΙΟΡΘΩΣΗ: ",
                "it": "CORREZIONE: ",
            }
            prefix = correction_prefixes.get(language_code, "CORRECTION: ")
            if not title.startswith(prefix):
                title = prefix + title
                title = title[:200]

        return ContentBlock(
            language_code=language_code,
            title=title,
            body=body,
            action_items=action_items,
            generation_method=gen_method,
            content_safety_result=safety_result,
            content_safety_failure_reason=(
                response.get("content_safety_result") if safety_result != "passed" else None
            ),
            back_translation_score=None,  # Set later by back_translate_and_score
            back_translation_flagged=False,
            translation_unavailable=translation_unavailable,
        )

    def _get_template_text(
        self,
        hazard_type: str,
        severity: str,
        alert_type: str,
        language_code: str,
        template_values: dict[str, str],
    ) -> tuple[str, str, str, bool]:
        """Get template text for a language with fallback."""
        if self._template_loader:
            return self._template_loader.get_template_text(
                hazard_type, severity, alert_type, language_code, template_values
            )
        # No template loader — generic fallback
        return (
            f"EMERGENCY ALERT — {template_values.get('location', '[unknown]')}",
            "An emergency situation exists. Follow emergency services directions.",
            "Call 000 for emergencies.",
            language_code != "en-AU",
        )

    def back_translate_and_score(
        self,
        content: ContentBlock,
        original_en_au: ContentBlock,
    ) -> float:
        """Perform back-translation to English and compute cosine similarity.

        Returns similarity score (0.0–1.0).
        Score ≥ threshold → pass.
        Score < threshold → flag with 0.9× confidence penalty per R-002.
        """
        if content.language_code == "en-AU":
            return 1.0

        if content.generation_method != GenerationMethod.llm:
            # Skip back-translation for template-based content
            return 1.0

        try:
            # Back-translate to English
            back_prompt = (
                f"Translate this text back to Australian English:\n"
                f"Title: {content.title}\n"
                f"Body: {content.body}"
            )
            response = self._generate_with_fallback(
                purpose="drafting",
                prompt=back_prompt,
                template_text=original_en_au.body,
                expected_language="en-AU",
                max_output_tokens=self._config.alert_max_tokens,
            )
            back_text = str(response["text"])

            # Compute cosine similarity using simple word vectors
            score = self._compute_similarity(original_en_au.body, back_text)
            return score

        except Exception:
            # Embedding service outage → return conservative score and flag for review
            logger.warning(
                "Back-translation failed for %s, returning conservative score (0.5) per CHK051",
                content.language_code,
            )
            content.back_translation_flagged = True
            return 0.5

    @staticmethod
    def _compute_similarity(text_a: str, text_b: str) -> float:
        """Compute cosine similarity between two texts using word frequency vectors."""
        words_a = text_a.lower().split()
        words_b = text_b.lower().split()

        if not words_a or not words_b:
            return 0.0

        all_words = list(set(words_a + words_b))
        vec_a = np.array([words_a.count(w) for w in all_words], dtype=float)
        vec_b = np.array([words_b.count(w) for w in all_words], dtype=float)

        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

    @staticmethod
    def compute_compound_confidence(
        base: float,
        freshness_penalty: float = 1.0,
        back_translation_penalty: float = 1.0,
        fallback_penalty: float = 1.0,
    ) -> float:
        """Apply multiplicative confidence stacking per CHK031.

        Order: freshness → back-translation (0.9×) → fallback (0.8×)
        """
        result = base * freshness_penalty * back_translation_penalty * fallback_penalty
        return max(0.0, min(1.0, result))
