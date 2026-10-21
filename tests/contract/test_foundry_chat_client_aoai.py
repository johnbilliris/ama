"""Regression guard for ``LiveFoundryChatClient`` AOAI endpoint handling.

Why this test exists
--------------------
The ``azure-ai-inference`` SDK's ``ChatCompletionsClient`` POSTs to
``{endpoint}/chat/completions``. That URL pattern is correct for native
Foundry project endpoints (``*.services.ai.azure.com``,
``*.inference.ml.azure.com``) but **404s** against Azure-OpenAI-kind
cognitive-services accounts, which require ``/openai/deployments/<name>``
in the URL. The pre-fix client was constructing one shared client bound
to the bare endpoint, so every call from production agents (where
``AZURE_AI_PROJECT_ENDPOINT`` is the cognitive-services endpoint) failed
with ``Foundry deployment '<name>' returned 404``.

This test pins:

* ``_is_aoai_endpoint`` correctly classifies cognitive-services and
  openai.azure.com hosts as AOAI.
* ``_endpoint_for(deployment)`` appends ``/openai/deployments/<name>`` to
  AOAI endpoints and leaves Foundry project endpoints untouched.
* ``_resolve`` honours ``AZURE_AI_<TIER>_DEPLOYMENT`` overrides for the
  recognised tier aliases (the workaround for the CSV-key collision when
  multiple tiers share a model key).
* ``_parse_deployment_map`` rejects conflicting duplicates with an actionable
  diagnostic; identical repeats preserve the independent embedding mapping.
"""

from __future__ import annotations

import pytest
from common.foundry_chat_client import (
    FoundryConfigurationError,
    LiveFoundryChatClient,
    _parse_deployment_map,
)

# ---------------------------------------------------------------- AOAI shape


@pytest.mark.parametrize(
    "endpoint,expected",
    [
        ("https://ama-aif-zo6bb5.cognitiveservices.azure.com/", True),
        ("https://my-resource.openai.azure.com/", True),
        ("https://my-project.services.ai.azure.com/", False),
        ("https://my-project.inference.ml.azure.com/", False),
    ],
)
def test_is_aoai_endpoint_classifies_known_hosts(endpoint: str, expected: bool) -> None:
    assert LiveFoundryChatClient._is_aoai_endpoint(endpoint) is expected


def test_endpoint_for_appends_openai_deployments_path_on_aoai() -> None:
    client = LiveFoundryChatClient(
        endpoint="https://ama-aif-zo6bb5.cognitiveservices.azure.com/",
        deployments={},
    )
    assert client._endpoint_for("gpt-5.6-sim-ama") == (
        "https://ama-aif-zo6bb5.cognitiveservices.azure.com/openai/deployments/gpt-5.6-sim-ama"
    )


def test_endpoint_for_leaves_foundry_project_endpoint_unchanged() -> None:
    client = LiveFoundryChatClient(
        endpoint="https://my-project.services.ai.azure.com/",
        deployments={},
    )
    assert client._endpoint_for("any") == "https://my-project.services.ai.azure.com"


def test_endpoint_for_does_not_double_append_when_already_per_deployment() -> None:
    client = LiveFoundryChatClient(
        endpoint="https://ama-aif-zo6bb5.cognitiveservices.azure.com/openai/deployments/gpt-5.6-sim-ama",
        deployments={},
    )
    assert client._endpoint_for("gpt-5.6-sim-ama") == (
        "https://ama-aif-zo6bb5.cognitiveservices.azure.com/openai/deployments/gpt-5.6-sim-ama"
    )


# ---------------------------------------------------------------- Tier env vars


def test_resolve_honours_simulation_tier_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AZURE_AI_SIMULATION_DEPLOYMENT", "gpt-5.6-sim-ama")
    monkeypatch.setenv("AZURE_AI_REASONING_DEPLOYMENT", "gpt-5.6-ama")
    monkeypatch.setenv("AZURE_AI_DRAFTING_DEPLOYMENT", "gpt-5.6-mini-ama")
    monkeypatch.setenv("AZURE_AI_PROJECT_REGION", "australiaeast")
    client = LiveFoundryChatClient(
        endpoint="https://ama-aif-zo6bb5.cognitiveservices.azure.com/",
        deployments={"gpt-5.6@2026-03-05": "gpt-5.6-ama"},
    )
    assert client._resolve("simulation") == "gpt-5.6-sim-ama"


def test_resolve_falls_back_to_csv_when_tier_env_var_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AZURE_AI_REASONING_DEPLOYMENT", raising=False)
    monkeypatch.setenv("AZURE_AI_PROJECT_REGION", "australiaeast")
    client = LiveFoundryChatClient(
        endpoint="https://ama-aif-zo6bb5.cognitiveservices.azure.com/",
        deployments={"gpt-5.6@2026-03-05": "gpt-5.6-ama"},
    )
    assert client._resolve("gpt-5.6@2026-03-05") == "gpt-5.6-ama"


# ---------------------------------------------------------------- CSV parser


@pytest.mark.parametrize("destinations", [("live-a", "simulation-b"), ("simulation-b", "live-a")])
def test_parse_deployment_map_rejects_conflicts_in_either_order(destinations: tuple[str, str]) -> None:
    first, second = destinations
    with pytest.raises(FoundryConfigurationError) as error:
        _parse_deployment_map(f"model@opaque={first},model@opaque={second}")
    assert "model@opaque" in str(error.value)
    assert first in str(error.value)
    assert second in str(error.value)
    assert "AZURE_AI_PROJECT_DEPLOYMENTS" in str(error.value)


def test_parse_deployment_map_preserves_identical_duplicates_and_embedding() -> None:
    parsed = _parse_deployment_map(
        "model@opaque=live-a,model@opaque=live-a,text-embedding-3-large@1=text-embedding-3-large-ama"
    )
    assert parsed["model@opaque"] == "live-a"
    assert parsed["text-embedding-3-large@1"] == "text-embedding-3-large-ama"
