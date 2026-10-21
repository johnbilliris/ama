from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlsplit

_LOCAL_ENVIRONMENTS = frozenset({"dev", "development", "local", "test"})
_LOCAL_HOSTS = frozenset({"redis", "localhost", "127.0.0.1", "::1", "ama-local-redis-1"})


def build_redis_client() -> Any | None:
    import redis

    environment = (os.environ.get("AMA_ENVIRONMENT") or os.environ.get("ENVIRONMENT") or "").lower()
    redis_url = os.environ.get("REDIS_URL", "").strip()
    if redis_url:
        if environment not in _LOCAL_ENVIRONMENTS:
            raise RuntimeError("REDIS_URL is only supported in local development environments")
        parsed = urlsplit(redis_url)
        try:
            port = parsed.port
        except ValueError as exc:
            raise ValueError("Local REDIS_URL must use redis://<local-host>:6379/<db>") from exc
        if (
            parsed.scheme != "redis"
            or parsed.hostname not in _LOCAL_HOSTS
            or port not in (None, 6379)
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ValueError("Local REDIS_URL must use redis://<local-host>:6379/<db> without credentials")
        return redis.Redis.from_url(redis_url, decode_responses=True, socket_timeout=5, socket_connect_timeout=5)

    host = os.environ.get("REDIS_HOST", "").strip()
    if not host:
        return None
    if host in _LOCAL_HOSTS and environment in _LOCAL_ENVIRONMENTS:
        return redis.Redis(
            host=host,
            port=int(os.environ.get("REDIS_PORT", "6380")),
            ssl=os.environ.get("REDIS_SSL", "1").strip() != "0",
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
        )
    if os.environ.get("REDIS_SSL", "1").strip() == "0":
        raise RuntimeError("Azure Redis requires TLS")

    from redis_entraid.cred_provider import create_from_managed_identity
    from redis_entraid.identity_provider import ManagedIdentityType

    provider = create_from_managed_identity(
        identity_type=ManagedIdentityType.SYSTEM_ASSIGNED,
        resource="https://redis.azure.com",
    )
    return redis.Redis(
        host=host,
        port=int(os.environ.get("REDIS_PORT", "10000")),
        ssl=True,
        credential_provider=provider,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5,
    )
