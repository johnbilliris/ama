from __future__ import annotations

from unittest.mock import Mock

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


@pytest.mark.parametrize("async_client", [False, True])
@pytest.mark.parametrize("auth_mode", [None, "aad"])
def test_default_credential_matches_client_type(
    monkeypatch: pytest.MonkeyPatch, async_client: bool, auth_mode: str | None
) -> None:
    monkeypatch.delenv("COSMOS_AUTH_MODE", raising=False)
    if auth_mode is not None:
        monkeypatch.setenv("COSMOS_AUTH_MODE", auth_mode)
    sync_credential = object()
    async_credential = object()
    sync_factory = Mock(return_value=sync_credential)
    async_factory = Mock(return_value=async_credential)
    monkeypatch.setattr("azure.identity.DefaultAzureCredential", sync_factory)
    monkeypatch.setattr("azure.identity.aio.DefaultAzureCredential", async_factory)

    result = _resolve_cosmos_credential(async_client=async_client)

    if async_client:
        assert result is async_credential
        async_factory.assert_called_once_with()
        sync_factory.assert_not_called()
    else:
        assert result is sync_credential
        sync_factory.assert_called_once_with()
        async_factory.assert_not_called()
