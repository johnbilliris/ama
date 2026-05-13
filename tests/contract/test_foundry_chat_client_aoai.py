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
* ``_parse_deployment_map`` is first-write-wins (so the CSV order is
  deterministic — the simulation Controller and the inference seam see
  the same lookup result).
"""

from __future__ import annotations

import pytest

from common.foundry_chat_client import (
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
    assert client._endpoint_for("gpt-5.4-sim-ama") == (
        "https://ama-aif-zo6bb5.cognitiveservices.azure.com/openai/deployments/gpt-5.4-sim-ama"
    )


def test_endpoint_for_leaves_foundry_project_endpoint_unchanged() -> None:
    client = LiveFoundryChatClient(
        endpoint="https://my-project.services.ai.azure.com/",
        deployments={},
    )
    assert client._endpoint_for("any") == "https://my-project.services.ai.azure.com"


def test_endpoint_for_does_not_double_append_when_already_per_deployment() -> None:
    client = LiveFoundryChatClient(
        endpoint="https://ama-aif-zo6bb5.cognitiveservices.azure.com/openai/deployments/gpt-5.4-sim-ama",
        deployments={},
    )
    assert client._endpoint_for("gpt-5.4-sim-ama") == (
        "https://ama-aif-zo6bb5.cognitiveservices.azure.com/openai/deployments/gpt-5.4-sim-ama"
    )


# ---------------------------------------------------------------- Tier env vars

def test_resolve_honours_simulation_tier_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AZURE_AI_SIMULATION_DEPLOYMENT", "gpt-5.4-sim-ama")
    client = LiveFoundryChatClient(
        endpoint="https://ama-aif-zo6bb5.cognitiveservices.azure.com/",
        deployments={"gpt-5.4@2026-03-05": "gpt-5.4-ama"},
    )
    assert client._resolve("simulation") == "gpt-5.4-sim-ama"


def test_resolve_falls_back_to_csv_when_tier_env_var_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AZURE_AI_REASONING_DEPLOYMENT", raising=False)
    client = LiveFoundryChatClient(
        endpoint="https://ama-aif-zo6bb5.cognitiveservices.azure.com/",
        deployments={"gpt-5.4@2026-03-05": "gpt-5.4-ama"},
    )
    assert client._resolve("gpt-5.4@2026-03-05") == "gpt-5.4-ama"


# ---------------------------------------------------------------- CSV parser

def test_parse_deployment_map_first_write_wins() -> None:
    """Three tiers may share a key; the first entry MUST win, deterministically."""
    csv = (
        "gpt-5.4@2026-03-05=gpt-5.4-ama,"
        "gpt-5.4@2026-03-05=gpt-5.4-mini-ama,"
        "gpt-5.4@2026-03-05=gpt-5.4-sim-ama,"
        "text-embedding-3-large@1=text-embedding-3-large-ama"
    )
    parsed = _parse_deployment_map(csv)
    assert parsed["gpt-5.4@2026-03-05"] == "gpt-5.4-ama"
    assert parsed["text-embedding-3-large@1"] == "text-embedding-3-large-ama"
