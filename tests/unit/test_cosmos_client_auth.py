from __future__ import annotations

import pytest

from apps.api.app.core.cosmos import _resolve_cosmos_credential


def test_key_auth_uses_configured_local_key_and_overrides_aad_credential(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COSMOS_AUTH_MODE", "key")
    monkeypatch.setenv("COSMOS_KEY", "local-emulator-key")
    aad_credential = object()

    assert _resolve_cosmos_credential(aad_credential) == "local-emulator-key"


def test_key_auth_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COSMOS_AUTH_MODE", "key")
    monkeypatch.delenv("COSMOS_KEY", raising=False)

    with pytest.raises(RuntimeError, match="COSMOS_KEY is required"):
        _resolve_cosmos_credential()


def test_aad_auth_preserves_existing_credential(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COSMOS_AUTH_MODE", "aad")
    monkeypatch.delenv("COSMOS_KEY", raising=False)
    credential = object()

    assert _resolve_cosmos_credential(credential) is credential


def test_unknown_auth_mode_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COSMOS_AUTH_MODE", "unsupported")

    with pytest.raises(ValueError, match="Unsupported COSMOS_AUTH_MODE"):
        _resolve_cosmos_credential()
