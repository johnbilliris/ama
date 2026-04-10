import logging
import time
from typing import Any

from app.core.settings import get_settings
from app.repositories.simulation_repository import SimulationRepository

logger = logging.getLogger(__name__)


class TokenBucket:
    """Simple token bucket rate limiter for simulation writes."""

    def __init__(self, rate: float, capacity: int):
        self._rate = rate
        self._capacity = capacity
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()

    def consume(self, tokens: int = 1) -> bool:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
        self._last_refill = now
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False


class ResourceGovernor:
    """Monitors shared resource utilisation and throttles simulation writes."""

    def __init__(
        self,
        simulation_repository: SimulationRepository,
        redis_client: Any = None,
    ):
        self._repo = simulation_repository
        self._redis = redis_client
        self._settings = get_settings()
        self._bucket = TokenBucket(rate=100.0, capacity=1000)
        self._incident_active = False

    async def check_write_allowed(self, tenant_id: str) -> bool:
        if not tenant_id.startswith("sim-"):
            return True

        tenant = await self._repo.get_by_tenant_id(tenant_id)
        if tenant is None:
            return False

        if tenant.throttle_mode == "incident-throttled":
            if not self._bucket.consume(5):
                logger.info("write_throttled_incident tenant_id=%s", tenant_id)
                return False

        if tenant.throttle_mode == "throttled":
            if not self._bucket.consume(2):
                logger.info("write_throttled tenant_id=%s", tenant_id)
                return False

        return self._bucket.consume(1)

    async def evaluate_utilisation(self) -> str:
        """Check global utilisation and return current mode."""
        if self._incident_active:
            return "incident-throttled"

        utilisation_pct = await self._get_utilisation_pct()
        if utilisation_pct >= self._settings.throttle_threshold_pct:
            return "throttled"
        return "normal"

    async def declare_incident(self) -> int:
        """Set all active simulations to incident-throttled mode. Returns count affected."""
        self._incident_active = True
        active_tenants, _ = await self._repo.list_by_status(status="active", limit=100)
        paused_tenants, _ = await self._repo.list_by_status(status="paused", limit=100)
        all_tenants = active_tenants + paused_tenants

        affected = 0
        quota = self._settings.incident_throttle_quota_pct
        for tenant in all_tenants:
            updated = tenant.model_copy(
                update={"throttle_mode": "incident-throttled", "throttle_quota_pct": quota}
            )
            await self._repo.update(updated)
            affected += 1

        logger.info("incident_declared simulations_throttled=%d quota=%d%%", affected, quota)
        return affected

    async def resolve_incident(self) -> int:
        """Restore all simulations to normal throttle mode. Returns count restored."""
        self._incident_active = False
        active_tenants, _ = await self._repo.list_by_status(status="active", limit=100)
        paused_tenants, _ = await self._repo.list_by_status(status="paused", limit=100)
        all_tenants = active_tenants + paused_tenants

        restored = 0
        for tenant in all_tenants:
            if tenant.throttle_mode == "incident-throttled":
                updated = tenant.model_copy(
                    update={"throttle_mode": "normal", "throttle_quota_pct": 100}
                )
                await self._repo.update(updated)
                restored += 1

        logger.info("incident_resolved simulations_restored=%d", restored)
        return restored

    async def _get_utilisation_pct(self) -> float:
        if self._redis:
            try:
                info = await self._redis.info("memory")
                used = info.get("used_memory", 0)
                max_mem = info.get("maxmemory", 1) or 1
                return (used / max_mem) * 100
            except Exception:
                logger.warning("redis_utilisation_check_failed", exc_info=True)
        return 0.0
