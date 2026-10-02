import hashlib as _hashlib
import json as _json
import logging
import time
from typing import Any as _Any
from typing import Protocol

from common.circuit_breaker import CircuitBreaker
from common.content_safety import ContentSafetyValidator
from common.llm_client import LLMClient
from common.llm_config import LLMClientConfig
from common.token_budget import Tokenizer, create_tokenizer
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class RestrictedSafetySink(Protocol):
    """Restricted sink for safety-flagged raw content evidence."""

    def write(
        self,
        *,
        correlation_id: str | None,
        content: str,
        retention_days: int,
        metadata: dict[str, object],
    ) -> str: ...


class LLMCallMixin:
    """Mixin providing LLM generation with circuit breaker, content safety, and confidence gating.

    Integrates:
    - Circuit breaker: prevents retry storms when LLM is unavailable
    - Content safety: validates all LLM outputs before returning
    - Confidence gating: reduces confidence on template fallback, flags for human review
    - Structured output validation: validates LLM JSON output against Pydantic models
    - Budget tracking: tracks cumulative token costs and emits warnings
    """

    def __init__(
        self,
        config: LLMClientConfig | None = None,
        tokenizer: Tokenizer | None = None,
        safety_evidence_sink: RestrictedSafetySink | None = None,
    ) -> None:
        self._llm_config = config or LLMClientConfig()
        self._llm_client = LLMClient(self._llm_config)
        self._content_safety = ContentSafetyValidator()
        self._tokenizer = tokenizer or create_tokenizer(self._llm_config.model_tier)
        self._safety_evidence_sink = safety_evidence_sink
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=self._llm_config.circuit_breaker_failure_threshold,
            recovery_timeout=self._llm_config.circuit_breaker_recovery_timeout,
        )
        # In-memory monthly budget tracker
        self._cumulative_cost_usd: float = 0.0
        self._budget_reset_month: int = time.gmtime().tm_mon

    def _estimate_cost(self, deployment_id: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD for a single LLM call based on deployment tier."""
        # GPT-4o pricing: ~$2.50/1M input, ~$10.00/1M output
        # GPT-4o-mini pricing: ~$0.15/1M input, ~$0.60/1M output
        if "mini" in deployment_id:
            return (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000
        return (input_tokens * 2.50 + output_tokens * 10.00) / 1_000_000

    def _track_budget(self, deployment_id: str, input_tokens: int, output_tokens: int) -> None:
        """Track cumulative cost and log warning if monthly budget exceeded."""
        current_month = time.gmtime().tm_mon
        if current_month != self._budget_reset_month:
            self._cumulative_cost_usd = 0.0
            self._budget_reset_month = current_month

        cost = self._estimate_cost(deployment_id, input_tokens, output_tokens)
        self._cumulative_cost_usd += cost

        if self._cumulative_cost_usd > self._llm_config.monthly_budget_usd:
            logger.warning(
                "Monthly LLM budget exceeded: $%.4f / $%.2f",
                self._cumulative_cost_usd,
                self._llm_config.monthly_budget_usd,
            )

    def _apply_output_budget(
        self,
        *,
        text: str,
        max_output_tokens: int,
        correlation_id: str | None,
        provider_token_usage: dict[str, int] | None = None,
    ) -> dict[str, object]:
        measured_output_tokens = self._tokenizer.count_tokens(text)
        provider_usage = provider_token_usage or {"input_tokens": 0, "output_tokens": measured_output_tokens}
        provider_output_tokens = int(provider_usage.get("output_tokens", measured_output_tokens))
        actual_output_tokens = max(measured_output_tokens, provider_output_tokens)

        retained_text = text
        retained_output_tokens = measured_output_tokens
        if measured_output_tokens > max_output_tokens:
            retained_text = self._tokenizer.truncate_to_tokens(text, max_output_tokens)
            retained_output_tokens = self._tokenizer.count_tokens(retained_text)
            logger.warning(
                "Token budget exceeded (correlation_id=%s): output_actual=%s retained_output=%s max_output=%s",
                correlation_id,
                actual_output_tokens,
                retained_output_tokens,
                max_output_tokens,
            )

        retained_usage = {
            "input_tokens": int(provider_usage.get("input_tokens", 0)),
            "output_tokens": retained_output_tokens,
        }
        actual_usage = {
            "input_tokens": int(provider_usage.get("input_tokens", 0)),
            "output_tokens": actual_output_tokens,
        }
        return {
            "text": retained_text,
            "retained_token_usage": retained_usage,
            "actual_token_usage": actual_usage,
            "output_truncated": measured_output_tokens > max_output_tokens,
        }

    def enforce_post_append_budget(
        self,
        *,
        text: str,
        max_output_tokens: int,
        correlation_id: str | None,
        provider_token_usage: dict[str, int] | None = None,
    ) -> dict[str, object]:
        """Re-apply output budget after post-generation text mutations."""
        return self._apply_output_budget(
            text=text,
            max_output_tokens=max_output_tokens,
            correlation_id=correlation_id,
            provider_token_usage=provider_token_usage,
        )

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
        deadline_monotonic: float | None = None,
        temperature: float = 0.0,
        response_model: type | None = None,
    ) -> dict[str, object]:
        """Generate LLM response with circuit breaker, content safety, and fallback chain.

        Args:
            purpose: Model tier ("reasoning" or "drafting").
            prompt: The user prompt.
            template_text: Fallback text if LLM is unavailable.
            correlation_id: Tracing correlation ID.
            expected_language: Expected output language for content safety.
            max_output_tokens: Max output tokens per call.
            timeout_seconds: Request timeout.
            temperature: Model temperature.
            response_model: Optional Pydantic model for structured output validation (FR-018).
        """
        cb_state = self._circuit_breaker.state
        max_input_tokens = self._llm_config.max_input_tokens
        measured_input_tokens = self._tokenizer.count_tokens(prompt)

        if deadline_monotonic is not None:
            remaining = deadline_monotonic - time.monotonic()
            if remaining <= 0:
                logger.warning(
                    "LLM deadline exceeded before dispatch (correlation_id=%s)",
                    correlation_id,
                )
                return self._template_fallback_response(
                    template_text=template_text,
                    circuit_breaker_state=cb_state.value,
                    correlation_id=correlation_id,
                    error_reason="deadline_exceeded",
                    token_usage={"input_tokens": 0, "output_tokens": 0},
                    actual_token_usage={"input_tokens": measured_input_tokens, "output_tokens": 0},
                )
            timeout_seconds = min(timeout_seconds, remaining)

        if measured_input_tokens > max_input_tokens:
            logger.warning(
                "Input token budget exceeded (correlation_id=%s): input_tokens=%s max_input_tokens=%s",
                correlation_id,
                measured_input_tokens,
                max_input_tokens,
            )
            return self._template_fallback_response(
                template_text=template_text,
                circuit_breaker_state=cb_state.value,
                correlation_id=correlation_id,
                error_reason="input_budget_exceeded",
                token_usage={"input_tokens": 0, "output_tokens": 0},
                actual_token_usage={"input_tokens": measured_input_tokens, "output_tokens": 0},
            )

        # Circuit breaker OPEN — skip directly to template fallback
        if not self._circuit_breaker.can_execute():
            logger.warning(
                "Circuit breaker OPEN — skipping LLM call, using template fallback (correlation_id=%s)",
                correlation_id,
            )
            return self._template_fallback_response(
                template_text=template_text,
                circuit_breaker_state=cb_state.value,
                correlation_id=correlation_id,
                error_reason="circuit_breaker_open",
            )

        try:
            response = self._llm_client.generate_response(
                purpose=purpose,
                prompt=prompt,
                correlation_id=correlation_id,
                max_output_tokens=max_output_tokens,
                timeout_seconds=timeout_seconds,
                deadline_monotonic=deadline_monotonic,
                temperature=temperature,
            )
            text = str(response.get("text", "")).strip()

            token_usage = response.get("token_usage", {"input_tokens": 0, "output_tokens": 0})
            deployment_id = str(response.get("deployment_id", ""))
            input_tokens = int(token_usage.get("input_tokens", 0))
            output_tokens = int(token_usage.get("output_tokens", 0))

            # Track budget
            self._track_budget(deployment_id, input_tokens, output_tokens)

            budgeted = self._apply_output_budget(
                text=text,
                max_output_tokens=max_output_tokens,
                correlation_id=correlation_id,
                provider_token_usage={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                },
            )
            text = str(budgeted["text"])
            retained_usage = budgeted["retained_token_usage"]
            actual_usage = budgeted["actual_token_usage"]

            # Structured output validation (FR-018 / T007b)
            if response_model is not None:
                try:
                    response_model.model_validate_json(text)
                except (ValidationError, Exception) as val_err:
                    logger.warning(
                        "Structured output validation failed for %s: %s — falling back to template",
                        response_model.__name__,
                        val_err,
                    )
                    self._circuit_breaker.record_success()
                    return self._template_fallback_response(
                        template_text=template_text,
                        circuit_breaker_state=self._circuit_breaker.state.value,
                        correlation_id=correlation_id,
                        error_reason=f"validation_error: {val_err}",
                        token_usage=token_usage,
                        actual_token_usage=actual_usage,
                        deployment_id=deployment_id,
                    )

            # Content safety validation
            safety = self._content_safety.validate(
                text=text,
                expected_language=expected_language,
            )
            if not safety.passed:
                evidence_ref = "dropped"
                retention_days = 7
                if self._safety_evidence_sink is not None:
                    try:
                        evidence_ref = self._safety_evidence_sink.write(
                            correlation_id=correlation_id,
                            content=text,
                            retention_days=retention_days,
                            metadata={
                                "reason": safety.reason or "unknown",
                                "validation_method": safety.validation_method,
                            },
                        )
                    except Exception as sink_error:
                        logger.warning(
                            "safety_evidence_sink_write_failed correlation_id=%s retention_days=%s error=%s",
                            correlation_id,
                            retention_days,
                            sink_error,
                        )
                else:
                    logger.warning(
                        "safety_evidence_sink_unavailable correlation_id=%s retention_days=%s action=dropped",
                        correlation_id,
                        retention_days,
                    )

                self._circuit_breaker.record_success()
                return {
                    "text": template_text,
                    "generation_method": "safety_fallback",
                    "model_deployment_id": response.get("deployment_id"),
                    "token_usage": retained_usage,
                    "actual_token_usage": actual_usage,
                    "content_safety_result": safety.result,
                    "content_safety_validation_method": safety.validation_method,
                    "content_safety_reason": safety.reason or "",
                    "content_safety_reference": evidence_ref,
                    "circuit_breaker_state": self._circuit_breaker.state.value,
                    "confidence_adjustment": None,
                    "correlation_id": correlation_id,
                    "requires_human_review": True,
                    "output_truncated": False,
                }

            # Success path — apply confidence gating
            self._circuit_breaker.record_success()
            gating = self._apply_confidence_gating(confidence=1.0, generation_method="llm")
            return {
                "text": text,
                "generation_method": "llm",
                "model_deployment_id": response.get("deployment_id"),
                "token_usage": retained_usage,
                "actual_token_usage": actual_usage,
                "content_safety_result": "passed",
                "content_safety_validation_method": safety.validation_method,
                "content_safety_reason": safety.reason or "",
                "circuit_breaker_state": self._circuit_breaker.state.value,
                "confidence_adjustment": gating.get("confidence_adjustment"),
                "correlation_id": correlation_id,
                "requires_human_review": bool(safety.review_flag or gating.get("requires_human_review", False)),
                "output_truncated": bool(budgeted["output_truncated"]),
            }

        except Exception as error:
            self._circuit_breaker.record_failure()
            logger.warning(
                "LLM generation failed; falling back to template: %s (correlation_id=%s, circuit_breaker_state=%s)",
                error,
                correlation_id,
                self._circuit_breaker.state.value,
            )
            return self._template_fallback_response(
                template_text=template_text,
                circuit_breaker_state=self._circuit_breaker.state.value,
                correlation_id=correlation_id,
                error_reason=str(error),
            )

    def _template_fallback_response(
        self,
        *,
        template_text: str,
        circuit_breaker_state: str,
        correlation_id: str | None = None,
        error_reason: str = "",
        token_usage: dict | None = None,
        actual_token_usage: dict | None = None,
        deployment_id: str | None = None,
    ) -> dict[str, object]:
        """Build a template fallback response with confidence reduction."""
        return {
            "text": template_text,
            "generation_method": "template_fallback",
            "model_deployment_id": deployment_id,
            "token_usage": token_usage,
            "actual_token_usage": actual_token_usage,
            "content_safety_result": "not_checked",
            "circuit_breaker_state": circuit_breaker_state,
            "confidence_adjustment": self._llm_config.fallback_reduction_factor,
            "requires_human_review": True,
            "output_truncated": False,
            "error_reason": error_reason,
            "correlation_id": correlation_id,
        }

    def _apply_confidence_gating(self, confidence: float, generation_method: str) -> dict[str, object]:
        """Apply confidence threshold gating.

        Returns dict with adjusted confidence and human_review flag.
        """
        adjusted = confidence
        if generation_method == "template_fallback":
            adjusted = confidence * self._llm_config.fallback_reduction_factor

        requires_review = adjusted < self._llm_config.confidence_threshold
        if requires_review:
            logger.info(
                "Confidence %.3f below threshold %.3f — flagging for human review",
                adjusted,
                self._llm_config.confidence_threshold,
            )

        return {
            "confidence": adjusted,
            "requires_human_review": requires_review,
        }


# ---------------------------------------------------------------------------
# T-B01: Canonical prompt-hash for sub-agent invocation records (FR-060)
# ---------------------------------------------------------------------------


def compute_prompt_hash(
    system_prompt: str,
    user_payload: _Any,
    tool_schemas: list[dict[str, _Any]] | None = None,
) -> str:
    """Return a deterministic SHA-256 hex digest for a prompt envelope.

    Per ``contracts/sub-agent-adapter.md`` Section 8 the hash is over a JSON
    object serialised with ``sort_keys=True`` and ``separators=(",", ":")``
    so that *identical inputs produce identical digests across machines*.

    The hash is recorded in every ``SubAgentInvocationRecord`` (FR-060) and
    on every ``injection.success`` audit envelope so auditors can later
    re-derive the prompt independently.
    """
    payload = {
        "system": system_prompt,
        "user": user_payload,
        "tools": tool_schemas or [],
    }
    canonical = _json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return _hashlib.sha256(canonical.encode("utf-8")).hexdigest()
