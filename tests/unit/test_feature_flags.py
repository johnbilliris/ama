"""Unit tests for the feature_flags module (T015)."""

from __future__ import annotations

import pytest

from apps.agents.maf_runtime.feature_flags import (
    DEFAULT_RETRY_ATTEMPTS,
    DEFAULT_RETRY_TOTAL_SECONDS,
    KNOWN_AGENTS,
    get_agent_mode,
    get_retry_attempts,
    get_retry_total_seconds,
)


@pytest.mark.parametrize("agent", KNOWN_AGENTS)
def test_default_mode_is_legacy_for_every_agent(monkeypatch: pytest.MonkeyPatch, agent: str) -> None:
    monkeypatch.delenv(f"FEATURE_MAF_RUNTIME_{agent.upper()}", raising=False)
    assert get_agent_mode(agent) == "legacy"


@pytest.mark.parametrize("mode", ["legacy", "maf", "shadow"])
def test_valid_modes_accepted(monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_MONITORING", mode)
    assert get_agent_mode("monitoring") == mode


def test_invalid_mode_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_EVACUATION", "BIG_BANG")
    with pytest.raises(ValueError):
        get_agent_mode("evacuation")


def test_retry_attempts_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FEATURE_MAF_RUNTIME_RETRY_ATTEMPTS", raising=False)
    assert get_retry_attempts() == DEFAULT_RETRY_ATTEMPTS


def test_retry_attempts_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_RETRY_ATTEMPTS", "5")
    assert get_retry_attempts() == 5


def test_retry_attempts_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_RETRY_ATTEMPTS", "0")
    with pytest.raises(ValueError):
        get_retry_attempts()


def test_retry_total_seconds_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FEATURE_MAF_RUNTIME_RETRY_TOTAL_SECONDS", raising=False)
    assert get_retry_total_seconds() == DEFAULT_RETRY_TOTAL_SECONDS


def test_retry_total_seconds_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FEATURE_MAF_RUNTIME_RETRY_TOTAL_SECONDS", "60")
    assert get_retry_total_seconds() == 60.0
