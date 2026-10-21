from __future__ import annotations

import pytest

from tests.simulation import test_quickstart_live_llm_rehearsal as live_gate


def test_live_gate_reports_missing_prerequisites_when_opted_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_LIVE_REHEARSAL", "1")
    monkeypatch.delenv("AZURE_AI_PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_AI_PROJECT_DEPLOYMENTS", raising=False)
    monkeypatch.delenv("AZURE_AI_REASONING_DEPLOYMENT", raising=False)
    monkeypatch.delenv("AZURE_AI_DRAFTING_DEPLOYMENT", raising=False)

    missing = live_gate._missing_live_prerequisites()

    assert "AZURE_AI_PROJECT_ENDPOINT" in missing
    assert "AZURE_AI_PROJECT_DEPLOYMENTS" in missing
    assert "AZURE_AI_REASONING_DEPLOYMENT" in missing
    assert "AZURE_AI_DRAFTING_DEPLOYMENT" in missing


def test_live_gate_allows_skip_when_not_opted_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_LIVE_REHEARSAL", "0")

    with pytest.raises(pytest.skip.Exception):
        live_gate._require_live_gate()


def test_live_gate_passes_when_opted_in_and_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_LIVE_REHEARSAL", "1")
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://project.services.ai.azure.com")
    monkeypatch.setenv("AZURE_AI_PROJECT_DEPLOYMENTS", "gpt-4o@2024-01-01=reasoning-deployment")
    monkeypatch.setenv("AZURE_AI_REASONING_DEPLOYMENT", "reasoning-deployment")
    monkeypatch.setenv("AZURE_AI_DRAFTING_DEPLOYMENT", "drafting-deployment")

    live_gate._require_live_gate()
