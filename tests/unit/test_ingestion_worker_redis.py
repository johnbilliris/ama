from unittest.mock import Mock

import pytest
import redis
from app.services.ingestion.pipeline_status_store import PipelineStatusStore

from apps.ingestion.worker import _build_dedup_redis_client


def test_local_redis_url_connects_without_azure_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    redis_client = Mock()
    from_url = Mock(return_value=redis_client)
    monkeypatch.setattr(redis.Redis, "from_url", from_url)
    monkeypatch.setenv("AMA_ENVIRONMENT", "dev")
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/0")
    monkeypatch.delenv("REDIS_HOST", raising=False)

    result = _build_dedup_redis_client()

    assert result is redis_client
    from_url.assert_called_once_with(
        "redis://redis:6379/0",
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5,
    )
    redis_client.ping.assert_called_once_with()


def test_local_redis_url_is_rejected_outside_development(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMA_ENVIRONMENT", "production")
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/0")

    with pytest.raises(RuntimeError, match="only supported in local development"):
        _build_dedup_redis_client()


@pytest.mark.parametrize(
    "redis_url",
    [
        "rediss://redis:6379/0",
        "redis://cache.example.com:6379/0",
        "redis://user:password@redis:6379/0",
        "redis://redis:6380/0",
    ],
)
def test_local_redis_url_rejects_nonlocal_connections(
    monkeypatch: pytest.MonkeyPatch,
    redis_url: str,
) -> None:
    monkeypatch.setenv("AMA_ENVIRONMENT", "dev")
    monkeypatch.setenv("REDIS_URL", redis_url)

    with pytest.raises(ValueError, match="Local REDIS_URL"):
        _build_dedup_redis_client()


def test_status_store_uses_refreshing_managed_identity_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    import redis_entraid.cred_provider
    from redis_entraid.identity_provider import ManagedIdentityType

    provider = Mock()
    create = Mock(return_value=provider)
    client = Mock()
    constructor = Mock(return_value=client)
    monkeypatch.setattr(redis_entraid.cred_provider, "create_from_managed_identity", create)
    monkeypatch.setattr(redis, "Redis", constructor)
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("REDIS_HOST", "cache.australiaeast.redis.azure.net")
    monkeypatch.setenv("REDIS_PORT", "10000")
    monkeypatch.setenv("REDIS_SSL", "1")

    store = PipelineStatusStore()

    assert store._redis is client
    create.assert_called_once_with(
        identity_type=ManagedIdentityType.SYSTEM_ASSIGNED, resource="https://redis.azure.com"
    )
    constructor.assert_called_once_with(
        host="cache.australiaeast.redis.azure.net",
        port=10000,
        ssl=True,
        credential_provider=provider,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5,
    )


def test_status_store_preserves_local_host_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    constructor = Mock()
    monkeypatch.setattr(redis, "Redis", constructor)
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("AMA_ENVIRONMENT", "test")
    monkeypatch.setenv("REDIS_HOST", "localhost")
    monkeypatch.setenv("REDIS_PORT", "6379")
    monkeypatch.setenv("REDIS_SSL", "0")
    PipelineStatusStore()
    assert constructor.call_args.kwargs["ssl"] is False
    assert "credential_provider" not in constructor.call_args.kwargs


def test_cloud_redis_rejects_disabled_tls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("REDIS_HOST", "cache.australiaeast.redis.azure.net")
    monkeypatch.setenv("REDIS_SSL", "0")
    with pytest.raises(RuntimeError, match="requires TLS"):
        PipelineStatusStore()


def test_status_store_reports_redis_auth_failure_without_credentials(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    client = Mock()
    client.hgetall.side_effect = redis.exceptions.AuthenticationError("sensitive diagnostic")
    monkeypatch.setattr(PipelineStatusStore, "_build_redis_client", staticmethod(lambda: client))
    store = PipelineStatusStore()
    assert store.list_pipeline_statuses() == []
    assert "AuthenticationError" in caplog.text
    assert "sensitive diagnostic" not in caplog.text
