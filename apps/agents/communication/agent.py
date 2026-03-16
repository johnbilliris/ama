from common.llm_mixin import LLMCallMixin
from packages.domain.src.domain.models.public_alert import PublicAlert


class CommunicationAgent(LLMCallMixin):
    _SUPPORTED_LANGUAGES = ["en-AU", "zh-Hans", "ar", "vi", "el", "it"]

    def __init__(self) -> None:
        super().__init__()

    def draft_alert(self, incident_id: str, recommendation_id: str) -> PublicAlert:
        default_template = "Prepare to evacuate if directed by emergency services."
        content_blocks: dict[str, str] = {}
        generation_method = "llm"
        content_safety_result = "passed"
        model_deployment_id: str | None = None

        for language in self._SUPPORTED_LANGUAGES:
            response = self._generate_with_fallback(
                purpose="drafting",
                prompt=(
                    "Draft a plain-language emergency alert sentence for community safety. "
                    f"Language: {language}; Incident: {incident_id}."
                ),
                template_text=default_template,
                expected_language=language,
                max_output_tokens=180,
            )
            content_blocks[language] = str(response["text"])
            model_deployment_id = model_deployment_id or response["model_deployment_id"]

            response_generation_method = str(response["generation_method"])
            if response_generation_method != "llm":
                generation_method = response_generation_method

            response_safety_result = str(response["content_safety_result"])
            if response_safety_result != "passed":
                content_safety_result = response_safety_result

        return PublicAlert(
            alert_id=f"alert-{recommendation_id}",
            incident_id=incident_id,
            status="pending_approval",
            audience_segments=["affected-community"],
            languages=self._SUPPORTED_LANGUAGES,
            accessibility_attributes=["plain-language"],
            channel_set=["sms", "push"],
            content_blocks=content_blocks,
            generation_method=generation_method,
            model_deployment_id=model_deployment_id,
            content_safety_result=content_safety_result,
        )
