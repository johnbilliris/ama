import logging
import os
import time
from importlib import import_module
from uuid import uuid4

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self) -> None:
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self._reasoning_deployment = os.getenv("AZURE_OPENAI_REASONING_DEPLOYMENT", "")
        self._drafting_deployment = os.getenv("AZURE_OPENAI_DRAFTING_DEPLOYMENT", "")

        self._client: object | None = None
        if endpoint and api_key:
            azure_openai_cls = getattr(import_module("openai"), "AzureOpenAI")
            self._client = azure_openai_cls(
                api_key=api_key,
                azure_endpoint=endpoint,
                api_version="2024-10-21",
            )

    def _deployment_for(self, purpose: str) -> str:
        if purpose == "reasoning":
            return self._reasoning_deployment
        return self._drafting_deployment

    def generate_response(
        self,
        *,
        purpose: str,
        prompt: str,
        correlation_id: str | None = None,
        max_output_tokens: int = 300,
        timeout_seconds: float = 30.0,
    ) -> dict[str, object]:
        if self._client is None:
            raise RuntimeError("Azure OpenAI client is not configured")

        deployment = self._deployment_for(purpose)
        if not deployment:
            raise RuntimeError(f"Missing deployment configuration for purpose '{purpose}'")

        resolved_correlation_id = correlation_id or uuid4().hex
        start = time.perf_counter()

        response = self._client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are an emergency response assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_output_tokens,
            timeout=timeout_seconds,
            extra_headers={"X-Correlation-ID": resolved_correlation_id},
        )

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        usage = response.usage
        content = response.choices[0].message.content if response.choices else ""

        input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)

        logger.info(
            "llm_call correlation_id=%s deployment_id=%s"
            " latency_ms=%s input_tokens=%s output_tokens=%s",
            resolved_correlation_id,
            deployment,
            elapsed_ms,
            input_tokens,
            output_tokens,
        )

        return {
            "text": content or "",
            "deployment_id": deployment,
            "correlation_id": resolved_correlation_id,
            "latency_ms": elapsed_ms,
            "token_usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        }
