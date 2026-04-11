from dataclasses import dataclass


@dataclass(frozen=True)
class ContentSafetyResult:
    passed: bool
    result: str
    reason: str | None = None


class ContentSafetyValidator:
    def __init__(self) -> None:
        # Only block truly inappropriate terms.
        # Disaster-context words (kill, attack, bomb) removed to avoid
        # false positives in legitimate disaster comms like "bushfire killed
        # livestock" or "bomb cyclone".
        # TODO: Integrate Azure AI Content Safety service for production.
        self._blocked_keywords = {
            "terror",
            "hate",
        }

    def _looks_like_language(self, text: str, expected_language: str | None) -> bool:
        if not expected_language:
            return True
        if expected_language == "en-AU":
            return all(ord(char) < 128 for char in text)
        if expected_language == "zh-Hans":
            return any("\u4e00" <= char <= "\u9fff" for char in text)
        if expected_language in {"ar", "vi", "el", "it"}:
            return len(text.strip()) > 0
        return True

    def validate(
        self,
        *,
        text: str,
        expected_language: str | None = None,
        max_length: int = 1200,
    ) -> ContentSafetyResult:
        if not text.strip():
            return ContentSafetyResult(False, "failed_with_fallback", "empty_output")

        if len(text) > max_length:
            return ContentSafetyResult(False, "failed_with_fallback", "length_exceeded")

        normalized = text.lower()
        if any(keyword in normalized for keyword in self._blocked_keywords):
            return ContentSafetyResult(False, "failed_with_fallback", "blocked_keyword")

        if not self._looks_like_language(text, expected_language):
            return ContentSafetyResult(False, "failed_with_fallback", "language_mismatch")

        return ContentSafetyResult(True, "passed")
