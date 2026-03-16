import logging

from common.content_safety import ContentSafetyValidator
from common.llm_client import LLMClient

logger = logging.getLogger(__name__)


class LLMCallMixin:
    def __init__(self) -> None:
        self._llm_client = LLMClient()
        self._content_safety = ContentSafetyValidator()

    def _generate_with_fallback(
        self,
        *,
        purpose: str,
        prompt: str,
        template_text: str,
        correlation_id: str | None = None,
        expected_language: str | None = None,
        max_output_tokens: int = 300,
        timeout_seconds: float = 30.0,
    ) -> dict[str, object]:
        try:
            response = self._llm_client.generate_response(
                purpose=purpose,
                prompt=prompt,
                correlation_id=correlation_id,
                max_output_tokens=max_output_tokens,
                timeout_seconds=timeout_seconds,
            )
            text = str(response.get("text", "")).strip()

            token_usage = response.get("token_usage", {"input_tokens": 0, "output_tokens": 0})
            output_tokens = int(token_usage.get("output_tokens", 0))
            if output_tokens > max_output_tokens:
                logger.warning(
                    "Token budget exceeded: output_tokens=%s max_output_tokens=%s",
                    output_tokens,
                    max_output_tokens,
                )
                text = text[: max(80, int(len(text) * 0.8))]

            safety = self._content_safety.validate(
                text=text,
                expected_language=expected_language,
            )
            if not safety.passed:
                return {
                    "text": template_text,
                    "generation_method": "safety_fallback",
                    "model_deployment_id": response.get("deployment_id"),
                    "token_usage": token_usage,
                    "content_safety_result": safety.result,
                }

            return {
                "text": text,
                "generation_method": "llm",
                "model_deployment_id": response.get("deployment_id"),
                "token_usage": token_usage,
                "content_safety_result": "passed",
            }
        except Exception as error:
            logger.warning("LLM generation failed; falling back to template: %s", error)
            return {
                "text": template_text,
                "generation_method": "template_fallback",
                "model_deployment_id": None,
                "token_usage": None,
                "content_safety_result": "not_checked",
            }
