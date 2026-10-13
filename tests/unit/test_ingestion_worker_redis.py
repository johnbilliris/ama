from unittest.mock import Mock

import pytest
import redis

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
