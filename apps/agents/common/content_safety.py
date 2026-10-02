"""Content safety validation — 3-layer pipeline (FR-007, FR-008, FR-009).

Layer 1: Azure AI Content Safety (primary) with circuit breaker fallback to keywords.
Layer 2: Factual consistency check against originating signal data.
Layer 3: Tone-level alignment against Australian Warning System tiers.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass

from common.content_safety_circuit_breaker import ContentSafetyCircuitBreaker

logger = logging.getLogger(__name__)

# Australian Warning System tier keywords
_AWS_TIERS = {
    "Advice": {"calm", "informational", "monitor", "aware", "stay informed"},
    "Watch and Act": {"action", "prepare", "ready", "act now", "conditions changing"},
    "Emergency Warning": {
        "immediate",
        "threat",
        "danger",
        "life-threatening",
        "seek shelter",
        "evacuate",
        "emergency",
        "critical",
    },
}

_EMERGENCY_ESCALATION_WORDS = {
    "immediate",
    "life-threatening",
    "evacuate now",
    "danger",
    "critical danger",
    "extreme",
    "catastrophic",
}

_EN_STOPWORDS = {
    "the",
    "and",
    "to",
    "of",
    "in",
    "for",
    "with",
    "evacuate",
    "warning",
    "emergency",
}

_AR_STOPWORDS = {"من", "في", "على", "إلى", "هذا", "هذه", "يرجى", "تحذير", "طارئ"}
_VI_STOPWORDS = {"và", "là", "trong", "cho", "hãy", "khẩn", "cấp", "cảnh", "báo", "ngay"}
_EL_STOPWORDS = {"και", "είναι", "στο", "στη", "σε", "κίνδυνος", "άμεση", "εκκένωση", "προειδοποίηση"}
_IT_STOPWORDS = {"e", "di", "il", "la", "per", "con", "allerta", "emergenza", "evacuazione", "subito"}
_STIGMATISING_PHRASES = {
    "the disabled",
    "invalid people",
    "foreigners",
    "illegal residents",
    "normal people only",
}


@dataclass(frozen=False)
class ContentSafetyResult:
    passed: bool
    result: str
    reason: str | None = None
    confidence: float = 0.0
    validation_method: str = "keyword_fallback"
    review_flag: bool = False


class ContentSafetyValidator:
    """3-layer content safety validation pipeline."""

    def __init__(
        self,
        circuit_breaker: ContentSafetyCircuitBreaker | None = None,
        azure_client: object | None = None,
    ) -> None:
        self._circuit_breaker = circuit_breaker or ContentSafetyCircuitBreaker()
        self._azure_client = azure_client
        self._blocked_keywords = {"terror", "hate"}

        # Attempt Azure AI client initialization
        if self._azure_client is None:
            self._azure_client = self._init_azure_client()

    @staticmethod
    def _init_azure_client():
        """Initialize Azure AI Content Safety client if credentials available."""
        endpoint = os.environ.get("AZURE_CONTENT_SAFETY_ENDPOINT", "")
        if not endpoint:
            return None
        try:
            from azure.ai.contentsafety import ContentSafetyClient

            env = os.environ.get("ENVIRONMENT", "local")
            if env == "local":
                from azure.core.credentials import AzureKeyCredential

                key = os.environ.get("AZURE_CONTENT_SAFETY_KEY", "")
                if key:
                    return ContentSafetyClient(endpoint, AzureKeyCredential(key))
            else:
                from azure.identity import DefaultAzureCredential

                return ContentSafetyClient(endpoint, DefaultAzureCredential())
        except Exception:
            logger.debug("Azure AI Content Safety client not available")
        return None

    @staticmethod
    def _word_tokens(text: str) -> list[str]:
        return re.findall(r"[\w'-]+", text.lower(), flags=re.UNICODE)

    def _obvious_english_substitution(self, words: list[str]) -> bool:
        if not words:
            return False
        en_hits = sum(1 for word in words if word in _EN_STOPWORDS)
        return en_hits >= max(2, len(words) // 5)

    @staticmethod
    def _script_ratio(text: str, start: int, end: int) -> float:
        letters = [char for char in text if char.isalpha()]
        if not letters:
            return 0.0
        matches = sum(1 for char in letters if start <= ord(char) <= end)
        return matches / len(letters)

    def _looks_like_language(self, text: str, expected_language: str | None) -> bool:
        if not expected_language:
            return True
        words = self._word_tokens(text)
        english_substitution = self._obvious_english_substitution(words)

        if expected_language == "en-AU":
            return not (
                self._script_ratio(text, 0x0600, 0x06FF) > 0.2
                or self._script_ratio(text, 0x0370, 0x03FF) > 0.2
                or any("\u4e00" <= char <= "\u9fff" for char in text)
            )
        if expected_language == "zh-Hans":
            return any("\u4e00" <= char <= "\u9fff" for char in text)
        if expected_language == "ar":
            if english_substitution:
                return False
            return self._script_ratio(text, 0x0600, 0x06FF) >= 0.25 and any(w in _AR_STOPWORDS for w in words)
        if expected_language == "vi":
            if english_substitution:
                return False
            vi_hits = sum(1 for word in words if word in _VI_STOPWORDS)
            has_vi_diacritic = bool(
                re.search(r"[ăâđêôơưáàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]", text.lower())
            )
            return vi_hits >= 2 or has_vi_diacritic
        if expected_language == "el":
            if english_substitution:
                return False
            return self._script_ratio(text, 0x0370, 0x03FF) >= 0.25 and any(w in _EL_STOPWORDS for w in words)
        if expected_language == "it":
            if english_substitution:
                return False
            it_hits = sum(1 for word in words if word in _IT_STOPWORDS)
            return it_hits >= 2
        return True

    def validate(
        self,
        *,
        text: str,
        expected_language: str | None = None,
        max_length: int = 1200,
    ) -> ContentSafetyResult:
        """Run Azure AI Content Safety with circuit breaker fallback."""
        if not text.strip():
            return ContentSafetyResult(False, "failed_with_fallback", "empty_output")

        if len(text) > max_length:
            return ContentSafetyResult(False, "failed_with_fallback", "length_exceeded")

        # Language checks must run regardless of which safety provider path succeeds.
        if not self._looks_like_language(text, expected_language):
            return ContentSafetyResult(
                passed=False,
                result="failed_with_fallback",
                reason="language_mismatch",
                confidence=0.5,
                validation_method="language_check",
                review_flag=True,
            )

        # Try Azure AI Content Safety (Layer 1)
        if self._azure_client and not self._circuit_breaker.is_open:
            try:
                result = self._validate_azure_ai(text)
                self._circuit_breaker.record_success()
                return result
            except Exception as exc:
                self._circuit_breaker.record_failure()
                logger.warning("Azure AI Content Safety call failed: %s", exc)

        # Fallback to keyword check
        self._circuit_breaker.record_fallback_usage()
        return self._validate_keywords(text, expected_language)

    def _validate_azure_ai(self, text: str) -> ContentSafetyResult:
        """Validate using Azure AI Content Safety SDK."""
        from azure.ai.contentsafety.models import AnalyzeTextOptions

        request = AnalyzeTextOptions(text=text)
        response = self._azure_client.analyze_text(request)

        max_severity = 0
        for category in (
            response.hate_result,
            response.self_harm_result,
            response.sexual_result,
            response.violence_result,
        ):
            if category and category.severity > max_severity:
                max_severity = category.severity

        # Pass threshold: all categories severity <= 2
        passed = max_severity <= 2
        confidence = max_severity / 6.0

        return ContentSafetyResult(
            passed=passed,
            result="passed" if passed else "failed_with_fallback",
            reason=None if passed else f"severity_{max_severity}",
            confidence=confidence,
            validation_method="azure_ai",
        )

    def _validate_keywords(
        self,
        text: str,
        expected_language: str | None = None,
    ) -> ContentSafetyResult:
        """Keyword-based fallback validation — flags for human review."""
        normalized = text.lower()
        if any(keyword in normalized for keyword in self._blocked_keywords):
            return ContentSafetyResult(
                passed=False,
                result="failed_with_fallback",
                reason="blocked_keyword",
                confidence=0.8,
                validation_method="keyword_fallback",
                review_flag=True,
            )

        return ContentSafetyResult(
            passed=True,
            result="passed",
            confidence=0.0,
            validation_method="keyword_fallback",
            review_flag=True,
        )

    def validate_factual(
        self,
        alert_message: str,
        originating_signal: dict,
    ) -> ContentSafetyResult:
        """Validate factual consistency against originating signal data (FR-007b)."""
        alert_lower = alert_message.lower()
        mismatches = []

        hazard_type = originating_signal.get("hazard_type", "")
        if hazard_type and hazard_type.lower() not in alert_lower:
            mismatches.append(f"hazard_type '{hazard_type}' not found in alert")

        severity = str(originating_signal.get("severity_level", ""))
        if severity and severity not in alert_message:
            mismatches.append(f"severity_level '{severity}' not found in alert")

        location = originating_signal.get("location_name", "")
        if location and location.lower() not in alert_lower:
            mismatches.append(f"location_name '{location}' not found in alert")

        if mismatches:
            return ContentSafetyResult(
                passed=False,
                result="failed_with_fallback",
                reason="; ".join(mismatches),
                confidence=1.0,
                validation_method="factual",
            )

        return ContentSafetyResult(
            passed=True,
            result="passed",
            confidence=0.0,
            validation_method="factual",
        )

    def validate_tone(
        self,
        alert_message: str,
        warning_tier: str,
    ) -> ContentSafetyResult:
        """Validate tone-level alignment against AWS tiers (FR-007c).

        Operates on English source text only (pre-translation).
        """
        alert_lower = alert_message.lower()

        # Check if the alert uses language exceeding its assigned tier
        if warning_tier == "Advice":
            for word in _EMERGENCY_ESCALATION_WORDS:
                if word in alert_lower:
                    return ContentSafetyResult(
                        passed=False,
                        result="failed_with_fallback",
                        reason=f"Advice-tier alert contains emergency language: '{word}'",
                        confidence=1.0,
                        validation_method="tone",
                    )
        elif warning_tier == "Watch and Act":
            emergency_only = _EMERGENCY_ESCALATION_WORDS - _AWS_TIERS["Watch and Act"]
            for word in emergency_only:
                if word in alert_lower:
                    return ContentSafetyResult(
                        passed=False,
                        result="failed_with_fallback",
                        reason=f"Watch and Act alert contains emergency-only language: '{word}'",
                        confidence=1.0,
                        validation_method="tone",
                    )

        return ContentSafetyResult(
            passed=True,
            result="passed",
            confidence=0.0,
            validation_method="tone",
        )

    def validate_cultural(self, alert_message: str) -> ContentSafetyResult:
        """Reject known stigmatising audience language before retention."""
        normalized = " ".join(alert_message.casefold().split())
        phrase = next((item for item in _STIGMATISING_PHRASES if item in normalized), None)
        if phrase is not None:
            return ContentSafetyResult(
                passed=False,
                result="failed_with_fallback",
                reason=f"stigmatising_language:{phrase}",
                confidence=1.0,
                validation_method="cultural",
                review_flag=True,
            )
        return ContentSafetyResult(
            passed=True,
            result="passed",
            confidence=0.0,
            validation_method="cultural",
        )
