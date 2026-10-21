import logging
import time

from apps.agents.risk_assessment.agent import RiskAssessmentAgent


def test_template_fallback_when_llm_unavailable() -> None:
    agent = RiskAssessmentAgent()

    def _raise_error(**_: object) -> dict[str, object]:
        raise RuntimeError("model unavailable")

    agent._llm_client.generate_response = _raise_error  # type: ignore[method-assign]

    recommendation = agent.recommend_public_alert("incident-fallback", ["sig-201"])
    assert recommendation.generation_method == "template_fallback"


def test_safety_fallback_when_content_flagged() -> None:
    agent = RiskAssessmentAgent()

    def _unsafe_response(**_: object) -> dict[str, object]:
        return {
            "text": "terror threat imminent",
            "deployment_id": "drafting-1",
            "token_usage": {"input_tokens": 10, "output_tokens": 5},
        }

    agent._llm_client.generate_response = _unsafe_response  # type: ignore[method-assign]

    recommendation = agent.recommend_public_alert("incident-safety", ["sig-202"])
    assert recommendation.generation_method == "safety_fallback"


def test_deadline_expiry_uses_template_fallback_without_outbound_call() -> None:
    agent = RiskAssessmentAgent()
    called = {"value": False}

    def _should_not_be_called(**_: object) -> dict[str, object]:
        called["value"] = True
        return {
            "text": "unexpected",
            "deployment_id": "reasoning-1",
            "token_usage": {"input_tokens": 1, "output_tokens": 1},
        }

    agent._llm_client.generate_response = _should_not_be_called  # type: ignore[method-assign]

    result = agent._generate_with_fallback(
        purpose="reasoning",
        prompt="explain risk",
        template_text="template text",
        deadline_monotonic=time.monotonic() - 0.001,
    )

    assert called["value"] is False
    assert result["generation_method"] == "template_fallback"
    assert result["error_reason"] == "deadline_exceeded"


def test_safety_flagged_content_goes_to_restricted_sink_only(caplog) -> None:
    class _Sink:
        def __init__(self) -> None:
            self.rows: list[dict[str, object]] = []

        def write(self, *, correlation_id, content, retention_days, metadata):
            self.rows.append(
                {
                    "correlation_id": correlation_id,
                    "content": content,
                    "retention_days": retention_days,
                    "metadata": metadata,
                }
            )
            return "sink-ref-1"

    marker = "PII-MARKER-UNIT-001"
    sink = _Sink()
    agent = RiskAssessmentAgent()
    agent._safety_evidence_sink = sink

    def _unsafe_response(**_: object) -> dict[str, object]:
        return {
            "text": f"terror advisory {marker}",
            "deployment_id": "drafting-1",
            "token_usage": {"input_tokens": 8, "output_tokens": 5},
        }

    agent._llm_client.generate_response = _unsafe_response  # type: ignore[method-assign]

    with caplog.at_level(logging.INFO):
        result = agent._generate_with_fallback(
            purpose="reasoning",
            prompt="prompt",
            template_text="safe template",
            correlation_id="cid-sink-1",
        )

    assert result["generation_method"] == "safety_fallback"
    assert result["content_safety_reference"] == "sink-ref-1"
    assert result["content_safety_validation_method"] == "keyword_fallback"
    assert result["content_safety_reason"] == "blocked_keyword"
    assert result["requires_human_review"] is True
    assert sink.rows and marker in str(sink.rows[0]["content"])
    assert marker not in "\n".join(caplog.messages)


def test_keyword_validator_fallback_marks_safe_output_for_review() -> None:
    agent = RiskAssessmentAgent()

    def _safe_response(**_: object) -> dict[str, object]:
        return {
            "text": "Validated operational review",
            "deployment_id": "reasoning-1",
            "token_usage": {"input_tokens": 4, "output_tokens": 3},
        }

    agent._llm_client.generate_response = _safe_response  # type: ignore[method-assign]

    result = agent._generate_with_fallback(
        purpose="reasoning",
        prompt="review",
        template_text="safe template",
    )

    assert result["generation_method"] == "llm"
    assert result["content_safety_validation_method"] == "keyword_fallback"
    assert result["requires_human_review"] is True
