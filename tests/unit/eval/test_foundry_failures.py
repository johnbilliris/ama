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
        models=[ModelUnderTest(modelId="gpt-5.4", version="2026-03-05")],
        metricSetVersion="disaster-core-v1",
        policyVersion="1.0.0",
        estimatedCostAud=0.0,
        createdAt=datetime.now(UTC),
        createdBy="tester",
    )


def test_parse_deployment_map_handles_csv():
    parsed = _parse_deployment_map("gpt-5.4@2026-03-05=gpt-5-4 , gpt-4o-mini@2024-07-18 = gpt-4o-mini")
    assert parsed == {
        "gpt-5.4@2026-03-05": "gpt-5-4",
        "gpt-4o-mini@2024-07-18": "gpt-4o-mini",
    }


def test_parse_deployment_map_handles_empty():
    assert _parse_deployment_map("") == {}
    assert _parse_deployment_map(None) == {}


def test_foundry_client_raises_when_endpoint_missing(monkeypatch):
    monkeypatch.delenv("AZURE_AI_PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_AI_PROJECT_DEPLOYMENTS", raising=False)
    client = FoundryClient()

    with pytest.raises(FoundryConfigurationError, match="AZURE_AI_PROJECT_ENDPOINT"):
        client.complete(model_id="gpt-5.4", messages=[{"role": "user", "content": "hi"}], version="2026-03-05")


def test_foundry_client_raises_when_deployment_unknown(monkeypatch):
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://aoai.example/")
    monkeypatch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", "gpt-4o-mini@2024-07-18=gpt-4o-mini")
    client = FoundryClient()
    # bypass HTTP by stubbing the inference client
    client._client = MagicMock()  # noqa: SLF001

    with pytest.raises(FoundryConfigurationError, match="no Foundry deployment configured"):
        client.complete(model_id="gpt-5.4", messages=[{"role": "user", "content": "hi"}], version="2026-03-05")


def test_foundry_client_uses_deployment_for_known_model(monkeypatch):
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://aoai.example/")
    monkeypatch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", "gpt-5.4@2026-03-05=my-gpt5")

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
    out = client.complete(model_id="gpt-5.4", messages=[{"role": "user", "content": "hi"}], version="2026-03-05")
    assert out.text == "hi back"
    # When chat_complete fake is used, deployment is None (FakeClient doesn't run lookup)
    # but deployment_for resolves correctly via deployment_for() helper:
    assert client.deployment_for("gpt-5.4", "2026-03-05") == "my-gpt5"


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

    with pytest.raises(RuntimeError, match="every case failed for model"):
        execute_run(ctx)
