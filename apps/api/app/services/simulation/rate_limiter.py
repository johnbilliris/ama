"""Simple in-memory token-bucket rate limiter for the Simulation Controller."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class _Bucket:
    tokens: float
    last_refill_ts: float


@dataclass
class RateLimiter:
    per_user_per_min: int = 30
    per_tenant_per_min: int = 120
    _user_buckets: dict[tuple[str, str], _Bucket] = field(default_factory=dict)
    _tenant_buckets: dict[str, _Bucket] = field(default_factory=dict)

    def check_and_consume(self, *, tenant_id: str, user_oid: str, cost: int = 1) -> bool:
        now = time.monotonic()
        u_key = (tenant_id, user_oid)
        user_b = self._user_buckets.get(u_key)
        if user_b is None:
            user_b = _Bucket(tokens=self.per_user_per_min, last_refill_ts=now)
            self._user_buckets[u_key] = user_b
        self._refill(user_b, now, self.per_user_per_min)
        tenant_b = self._tenant_buckets.get(tenant_id)
        if tenant_b is None:
            tenant_b = _Bucket(tokens=self.per_tenant_per_min, last_refill_ts=now)
            self._tenant_buckets[tenant_id] = tenant_b
        self._refill(tenant_b, now, self.per_tenant_per_min)
        if user_b.tokens < cost or tenant_b.tokens < cost:
            return False
        user_b.tokens -= cost
        tenant_b.tokens -= cost
        return True

    # T-C08 / FR-009 — success-only counting:
    def can_attempt(self, *, tenant_id: str, user_oid: str, cost: int = 1) -> bool:
        """Probe whether a parse-attempt is allowed WITHOUT consuming a token.

        Failed parse attempts (which the parse-attempt circuit breaker
        already tracks) MUST NOT increment the user-facing rate-limit
        counters. Use :meth:`record_success` after a successful injection.
        """
        now = time.monotonic()
        u_key = (tenant_id, user_oid)
        user_b = self._user_buckets.get(u_key)
        if user_b is None:
            user_b = _Bucket(tokens=self.per_user_per_min, last_refill_ts=now)
            self._user_buckets[u_key] = user_b
        self._refill(user_b, now, self.per_user_per_min)
        tenant_b = self._tenant_buckets.get(tenant_id)
        if tenant_b is None:
            tenant_b = _Bucket(tokens=self.per_tenant_per_min, last_refill_ts=now)
            self._tenant_buckets[tenant_id] = tenant_b
        self._refill(tenant_b, now, self.per_tenant_per_min)
        return user_b.tokens >= cost and tenant_b.tokens >= cost

    def record_success(self, *, tenant_id: str, user_oid: str, cost: int = 1) -> bool:
        """Consume *cost* tokens after a successful injection (T-C08 / FR-009)."""
        return self.check_and_consume(tenant_id=tenant_id, user_oid=user_oid, cost=cost)

    @staticmethod
    def _refill(bucket: _Bucket, now: float, per_min: int) -> None:
        elapsed = now - bucket.last_refill_ts
        refill = elapsed * (per_min / 60.0)
        bucket.tokens = min(float(per_min), bucket.tokens + refill)
        bucket.last_refill_ts = now


_default: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _default
    if _default is None:
        _default = RateLimiter()
    return _default


def reset_default_for_tests() -> None:
    global _default
    _default = None
