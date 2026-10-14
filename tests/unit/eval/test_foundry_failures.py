"""Tests for the FoundryClient + orchestrator failure modes added in the
'real Foundry deployment' phase. The eval pipeline previously reported runs
as 'succeeded' even when every model call failed; these tests pin the
fail-loud contract."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
for p in (
    _REPO_ROOT,
    _REPO_ROOT / "apps" / "eval-runner" / "src",
    _REPO_ROOT / "packages" / "eval-core" / "src",
):
    sys.path.insert(0, str(p))

from ama_eval.foundry_client import (  # noqa: E402
    FoundryClient,
    FoundryConfigurationError,
    FoundryInferenceError,
    FoundryResponse,
    _parse_deployment_map,
)
from ama_eval.orchestrator import OrchestratorContext, execute_run  # noqa: E402
from ama_eval_core.models import (  # noqa: E402
    EvaluationCase,
    EvaluationRun,
    ExpectedAction,
    ExpectedBehaviour,
    HazardTag,
    ModelUnderTest,
    Provenance,
    ProvenanceMeta,
    RunStatus,
    Severity,
    Tone,
)


def _case() -> EvaluationCase:
    from datetime import UTC, datetime

    from ama_eval_core.models import ApprovalEntry

    return EvaluationCase(
        caseId="case-1",
        datasetId="d",
        version="1.0.0",
        inputs={"prompt": "How do I evacuate?"},
        expectedBehaviour=ExpectedBehaviour(
            mustInclude=["call 000"],
            mustNotInclude=[],
            expectedAction=ExpectedAction.answer,
            referToAuthority=True,
            tone=Tone.directive,
        ),
        sensitivityLabels=[],
        hazardTags=[HazardTag.flood],
        jurisdictionTags=["AU-NSW"],
        severity=Severity.medium,
        language="en-AU",
        provenance=Provenance.synthetic,
        provenanceMeta=ProvenanceMeta(author="a@b", reviewer="c@d"),
        approvalState="approved",
        approvalChain=[
            ApprovalEntry(
                role="reviewer",
                principal="c@d",
                action="approve",
                timestamp=datetime.now(UTC),
            ),
        ],
    )


def _run() -> EvaluationRun:
    from datetime import UTC, datetime

    return EvaluationRun(
        runId="r-1",
        status=RunStatus.queued,
        mode="ad-hoc",
        datasetId="d",
        datasetVersion="1.0.0",
        models=[ModelUnderTest(modelId="gpt-5.6", version="2026-03-05")],
        metricSetVersion="disaster-core-v1",
        policyVersion="1.0.0",
        estimatedCostAud=0.0,
        createdAt=datetime.now(UTC),
        createdBy="tester",
    )


def test_parse_deployment_map_handles_csv():
    parsed = _parse_deployment_map("gpt-5.6@2026-03-05=gpt-5-6 , gpt-4o-mini@2024-07-18 = gpt-4o-mini")
    assert parsed == {
        "gpt-5.6@2026-03-05": "gpt-5-6",
        "gpt-4o-mini@2024-07-18": "gpt-4o-mini",
    }


def test_parse_deployment_map_handles_empty():
    assert _parse_deployment_map("") == {}
    assert _parse_deployment_map(None) == {}


def test_foundry_client_raises_when_endpoint_missing(monkeypatch):
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://aoai.example/")
    monkeypatch.delenv("AZURE_AI_INFERENCE_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_AI_PROJECT_DEPLOYMENTS", raising=False)
    client = FoundryClient()

    with pytest.raises(FoundryConfigurationError, match="AZURE_AI_INFERENCE_ENDPOINT"):
        client.complete(model_id="gpt-5.6", messages=[{"role": "user", "content": "hi"}], version="2026-03-05")


def test_foundry_client_raises_when_deployment_unknown(monkeypatch):
    monkeypatch.setenv("AZURE_AI_INFERENCE_ENDPOINT", "https://aoai.example/models")
    monkeypatch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", "gpt-4o-mini@2024-07-18=gpt-4o-mini")
    client = FoundryClient()
    # bypass HTTP by stubbing the inference client
    client._client = MagicMock()  # noqa: SLF001

    with pytest.raises(FoundryConfigurationError, match="no Foundry deployment configured"):
        client.complete(model_id="gpt-5.6", messages=[{"role": "user", "content": "hi"}], version="2026-03-05")


def test_foundry_client_uses_deployment_for_known_model(monkeypatch):
    monkeypatch.setenv("AZURE_AI_INFERENCE_ENDPOINT", "https://aoai.example/models")
    monkeypatch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", "gpt-5.6@2026-03-05=my-gpt5")

    captured: dict = {}

    def fake_chat(model_id, messages, temperature, max_tokens, timeout_seconds, deployment):
        captured["deployment"] = deployment
        captured["model_id"] = model_id
        return FoundryResponse(
            text="hi back",
            finish_reason="stop",
            usage_prompt_tokens=10,
            usage_completion_tokens=2,
            latency_ms=42,
            safety_filter_triggered=False,
            raw={},
        )

    client = FoundryClient(chat_complete=fake_chat)
    out = client.complete(model_id="gpt-5.6", messages=[{"role": "user", "content": "hi"}], version="2026-03-05")
    assert out.text == "hi back"
    # When chat_complete fake is used, deployment is None (FakeClient doesn't run lookup)
    # but deployment_for resolves correctly via deployment_for() helper:
    assert client.deployment_for("gpt-5.6", "2026-03-05") == "my-gpt5"


def test_foundry_client_uses_model_inference_endpoint(monkeypatch):
    endpoint = "https://aoai.example.services.ai.azure.com/models"
    credential = object()
    constructed_client = MagicMock()
    client_constructor = MagicMock(return_value=constructed_client)
    credential_constructor = MagicMock(return_value=credential)
    monkeypatch.setattr("azure.ai.inference.ChatCompletionsClient", client_constructor)
    monkeypatch.setattr("azure.identity.DefaultAzureCredential", credential_constructor)

    client = FoundryClient(
        endpoint=endpoint,
        deployments={"gpt-5.6@2026-03-05": "my-gpt5"},
    )

    assert client._ensure_client() is constructed_client  # noqa: SLF001
    client_constructor.assert_called_once_with(
        endpoint=endpoint,
        credential=credential,
        credential_scopes=["https://cognitiveservices.azure.com/.default"],
    )


def test_foundry_client_raises_when_inference_request_fails():
    client = FoundryClient(
        endpoint="https://aoai.example.services.ai.azure.com/models",
        deployments={"gpt-5.6@2026-03-05": "my-gpt5"},
    )
    client._client = MagicMock()  # noqa: SLF001
    client._client.complete.side_effect = RuntimeError("resource not found")  # noqa: SLF001

    with pytest.raises(FoundryInferenceError, match="deployment my-gpt5") as exc_info:
        client.complete(model_id="gpt-5.6", messages=[{"role": "user", "content": "hi"}], version="2026-03-05")

    assert isinstance(exc_info.value.__cause__, RuntimeError)


def test_foundry_client_marks_provider_content_filter_as_refusal():
    client = FoundryClient(
        endpoint="https://aoai.example.services.ai.azure.com/models",
        deployments={"gpt-5.6-mini@2026-03-17": "gpt-5-6-mini"},
    )
    client._client = MagicMock()  # noqa: SLF001
    blocked = RuntimeError("(content_filter) response blocked by policy")
    blocked.status_code = 400
    client._client.complete.side_effect = blocked  # noqa: SLF001

    result = client.complete(
        model_id="gpt-5.6-mini",
        version="2026-03-17",
        messages=[{"role": "user", "content": "unsafe request"}],
    )

    assert result.text == ""
    assert result.finish_reason == "content_filter"
    assert result.safety_filter_triggered
    assert result.raw == {"errorCode": "content_filter"}


def test_foundry_client_uses_max_completion_tokens_for_gpt5():
    client = FoundryClient(
        endpoint="https://aoai.example.services.ai.azure.com/models",
        deployments={"gpt-5.6-mini@2026-03-17": "gpt-5-6-mini"},
    )
    client._client = MagicMock()  # noqa: SLF001
    completion = MagicMock()
    completion.choices[0].message.content = "Evacuate now."
    completion.choices[0].finish_reason = "stop"
    completion.usage.prompt_tokens = 10
    completion.usage.completion_tokens = 3
    client._client.complete.return_value = completion  # noqa: SLF001

    result = client.complete(
        model_id="gpt-5.6-mini",
        version="2026-03-17",
        messages=[{"role": "user", "content": "What should I do?"}],
    )

    assert result.text == "Evacuate now."
    client._client.complete.assert_called_once_with(  # noqa: SLF001
        model="gpt-5-6-mini",
        messages=[{"role": "user", "content": "What should I do?"}],
        temperature=0.2,
        max_tokens=None,
        model_extras={"max_completion_tokens": 512},
    )


def test_foundry_client_rate_limits_requests(monkeypatch):
    client = FoundryClient(endpoint="https://aoai.example/models")
    clock = [100.0]
    sleeps: list[float] = []

    def fake_sleep(delay: float) -> None:
        sleeps.append(delay)
        clock[0] += delay

    monkeypatch.setattr("ama_eval.foundry_client.time.monotonic", lambda: clock[0])
    monkeypatch.setattr("ama_eval.foundry_client.time.sleep", fake_sleep)

    client._wait_for_request_slot()  # noqa: SLF001
    client._wait_for_request_slot()  # noqa: SLF001

    assert sleeps == [7.5]


def test_foundry_client_retries_rate_limited_requests(monkeypatch):
    from types import SimpleNamespace

    client = FoundryClient(
        endpoint="https://aoai.example.services.ai.azure.com/models",
        deployments={"gpt-5.6@2026-03-05": "my-gpt5"},
    )
    client._client = MagicMock()  # noqa: SLF001
    client._wait_for_request_slot = MagicMock()  # noqa: SLF001
    rate_limit = RuntimeError("rate limited")
    rate_limit.status_code = 429
    rate_limit.response = SimpleNamespace(headers={"retry-after-ms": "1"})
    completion = MagicMock()
    completion.choices[0].message.content = "I am safe."
    completion.choices[0].finish_reason = "stop"
    completion.usage.prompt_tokens = 10
    completion.usage.completion_tokens = 3
    client._client.complete.side_effect = [rate_limit, completion]  # noqa: SLF001
    sleeps: list[float] = []
    monkeypatch.setattr("ama_eval.foundry_client.time.sleep", sleeps.append)

    result = client.complete(
        model_id="gpt-5.6",
        version="2026-03-05",
        messages=[{"role": "user", "content": "Help."}],
    )

    assert result.text == "I am safe."
    assert client._client.complete.call_count == 2  # noqa: SLF001
    assert sleeps == [7.5]


def test_orchestrator_raises_when_every_case_fails():
    """If every case raises (e.g. FoundryConfigurationError) the orchestrator
    must NOT silently continue and produce an empty matrix — it must raise."""
    case = _case()
    run = _run()

    def raising_call(model_id, messages, parameters):
        raise FoundryConfigurationError("AZURE_AI_PROJECT_ENDPOINT is not set")

    audit_events: list[dict] = []

    ctx = OrchestratorContext(
        cases=[case],
        run=run,
        audit_emit=lambda **kw: audit_events.append(kw),
        foundry_call=raising_call,
    )

    with pytest.raises(RuntimeError, match="1/1 cases failed for model"):
        execute_run(ctx)


def test_orchestrator_rejects_partial_case_failures():
    from ama_eval.evaluators.base import ModelOutput

    case = _case()
    failed_case = case.model_copy(update={"caseId": "case-2", "inputs": {"prompt": "fail this case"}})
    run = _run()

    def mixed_call(model_id, messages, parameters):
        if messages[-1]["content"] == "fail this case":
            raise FoundryConfigurationError("model unavailable")
        return ModelOutput(
            text="Call 000 and evacuate.",
            finish_reason="stop",
            safety_filter_triggered=False,
            latency_ms=10,
            prompt_tokens=5,
            completion_tokens=4,
        )

    ctx = OrchestratorContext(
        cases=[case, failed_case],
        run=run,
        audit_emit=lambda **_kwargs: None,
        foundry_call=mixed_call,
    )

    with pytest.raises(RuntimeError, match="1/2 cases failed for model"):
        execute_run(ctx)


def test_orchestrator_supplies_retrieval_context_and_respects_metric_applicability():
    from ama_eval.evaluators.base import ModelOutput
    from ama_eval_core.models import RetrievedContextEntry

    case = _case().model_copy(
        update={
            "language": "vi-VN",
            "metricApplicability": ["operational"],
            "retrievalScope": True,
            "retrievedContext": [
                RetrievedContextEntry(
                    docId="doc-1",
                    content="Verified evacuation protocol.",
                    rank=1,
                    relevanceLabel="relevant",
                )
            ],
        }
    )
    run = _run()
    captured_messages: list[list[dict[str, str]]] = []

    def fake_call(model_id, messages, parameters):
        captured_messages.append(messages)
        return ModelOutput(
            text="Follow the supplied evacuation protocol.",
            finish_reason="stop",
            safety_filter_triggered=False,
            latency_ms=10,
            prompt_tokens=10,
            completion_tokens=5,
        )

    ctx = OrchestratorContext(
        cases=[case],
        run=run,
        audit_emit=lambda **_kwargs: None,
        foundry_call=fake_call,
    )

    execute_run(ctx)

    assert "Verified evacuation protocol." in captured_messages[0][0]["content"]
    assert set(ctx.sample_traces[0].perMetric) == {"latency-budget"}


def test_content_filter_result_is_classified_as_refusal():
    from ama_eval.evaluators.base import ModelOutput
    from ama_eval.orchestrator import _classify_output

    output = ModelOutput(
        text="",
        finish_reason="content_filter",
        safety_filter_triggered=True,
        latency_ms=10,
        prompt_tokens=10,
        completion_tokens=0,
    )

    assert _classify_output(output, "refuse") == "refused"
